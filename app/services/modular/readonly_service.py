import os
import subprocess
import threading
from contextlib import contextmanager

from app.services.abstract_modular_base_service import AbstractModularBaseService

CMD_TIMEOUT = 20  # s

# ReadOnlyService
# ------
# Config keys (under services.readonly):
#   enableOnBoot (bool) - nach dem Start des Services read-only schalten (default False).
#                         Besser: "ro" in /etc/fstab, dann ist das System schon ab Boot read-only.
#   manageTmpfs (bool)  - tmpfs-Mounts (/tmp, /var/log, ...) zur Laufzeit selbst anlegen (default True).
#                         Auf False setzen, wenn die tmpfs-Mounts in /etc/fstab stehen.
#
# Für Schreibzugriffe aus anderen Services:
#     with readonlyService.readwrite():
#         ...  # schreiben
# Verschachtelte / parallele Aufrufe sind erlaubt: erst der letzte schaltet wieder auf read-only.
#
# Benötigt sudoers-Einträge (NOPASSWD) für: mount, test, mv, ln, rm, systemctl try-restart rsyslog
class ReadOnlyService(AbstractModularBaseService):
    # (Pfad, size, mode)
    TMPFS_PATHS = [
        ("/tmp", "64m", "1777"),
        ("/var/tmp", "16m", "1777"),
        ("/var/log", "50m", "0755"),
        ("/var/spool/mail", "5m", "0755"),
        ("/var/spool/rsyslog", "25m", "0755"),
        ("/var/lib/logrotate", "1m", "0755"),
        ("/var/lib/sudo", "1m", "0700"),
    ]
    CRITICAL = ("/tmp", "/var/log")
    BOOT_MOUNTS = ("/boot/firmware", "/boot")

    def __init__(self, registry):
        super().__init__("readonly", registry)
        self._lock = threading.RLock()
        self._rw_holds = 0
        self.manageTmpfs = True

    def onReady(self):
        config = self.getServiceConfig()
        self.manageTmpfs = config.get("manageTmpfs", True)
        if config.get("enableOnBoot", False) and not self._is_readonly():
            self.getLoggingService().info(
                self.name, "enableOnBoot is set – enabling read-only mode"
            )
            self.enableReadonly()
        super().onReady()

    def readState(self) -> dict:
        # immer live aus dem System lesen, nicht aus einem Cache
        return {
            "readonly": self._is_readonly(),
            "tmpfs_mounts": self._configured_tmpfs_mounts(),
        }

    # ---------- Zugriff für andere Services ----------

    @contextmanager
    def readwrite(self):
        was = self.ensure_readwrite()
        try:
            yield
        finally:
            self.restore_readonly(was)

    def ensure_readwrite(self) -> bool:
        """True = Aufrufer hält jetzt eine rw-Sperre und muss restore_readonly(True) aufrufen."""
        with self._lock:
            if self._rw_holds > 0:
                self._rw_holds += 1
                return True
            if not self._is_readonly():
                return False
            self.getLoggingService().info(
                self.name, "Temporarily switching to read-write mode"
            )
            if not self.disableReadonly():
                return False
            self._rw_holds = 1
            return True

    def restore_readonly(self, was_readonly: bool):
        if not was_readonly:
            return
        with self._lock:
            if self._rw_holds == 0:
                return
            self._rw_holds -= 1
            if self._rw_holds == 0:
                if self.enableReadonly():
                    self.getLoggingService().info(self.name, "Restored read-only mode")

    # ---------- Hilfsfunktionen ----------

    def _sudo(self, *args):
        try:
            r = subprocess.run(
                ["sudo", "-n", *args],
                capture_output=True, text=True, timeout=CMD_TIMEOUT,
            )
            return r.returncode, (r.stderr or "").strip()
        except Exception as e:
            return -1, str(e)

    def _read_mounts(self) -> dict:
        mounts = {}
        try:
            with open("/proc/mounts") as f:
                for line in f:
                    p = line.split()
                    if len(p) >= 4:
                        # bei mehreren Einträgen zählt der letzte (= oberster Mount)
                        mounts[p[1].replace("\\040", " ")] = (p[2], p[3].split(","))
        except OSError:
            pass
        return mounts

    def _is_readonly(self) -> bool:
        try:
            return bool(os.statvfs("/").f_flag & os.ST_RDONLY)
        except OSError:
            return False

    def _is_mounted(self, path: str) -> bool:
        # realpath: /var/spool/mail ist unter Debian ein Symlink auf /var/mail,
        # /proc/mounts zeigt den aufgelösten Pfad
        return os.path.realpath(path) in self._read_mounts()

    def _configured_tmpfs_mounts(self) -> list:
        mounts = self._read_mounts()
        result = []
        for path, _, _ in self.TMPFS_PATHS:
            m = mounts.get(os.path.realpath(path))
            if m and m[0] == "tmpfs":
                result.append(path)
        return result

    def _mount_tmpfs(self, path: str, size: str, mode: str) -> bool:
        real = os.path.realpath(path)
        if self._is_mounted(real):
            self.getLoggingService().debug(self.name, f"{path} already mounted")
            return True

        opts = f"nosuid,nodev,size={size},mode={mode}"
        rc, err = self._sudo("mount", "-t", "tmpfs", "-o", opts, "tmpfs", real)
        if rc != 0:
            self.getLoggingService().error(
                self.name, f"Failed to mount tmpfs on {path}: {err}"
            )
            return False
        self.getLoggingService().debug(self.name, f"Mounted tmpfs on {path}")
        return True

    def _setup_random_seed(self) -> bool:
        seed = "/var/lib/systemd/random-seed"
        target = "/tmp/systemd-random-seed"
        if os.path.islink(seed):
            return True  # schon umgebogen (Link bleibt auch über Reboots bestehen)

        if self._sudo("test", "-f", seed)[0] != 0:
            return True  # keine Seed-Datei vorhanden

        if self._sudo("test", "-e", target)[0] == 0:
            rc, err = self._sudo("rm", "-f", seed)
        else:
            rc, err = self._sudo("mv", seed, target)
        if rc == 0:
            rc, err = self._sudo("ln", "-sf", target, seed)
        if rc != 0:
            self.getLoggingService().error(self.name, f"Failed to setup random-seed: {err}")
            return False
        self.getLoggingService().debug(self.name, "Symlinked random-seed to /tmp")
        return True

    def _remount_boot(self, mode: str):
        for boot in self.BOOT_MOUNTS:
            if self._is_mounted(boot):
                rc, err = self._sudo("mount", "-o", f"remount,{mode}", boot)
                if rc != 0:
                    self.getLoggingService().warn(
                        self.name, f"Remount {boot} {mode} failed: {err}"
                    )

    # ---------- Umschalten ----------

    def enableReadonly(self) -> bool:
        with self._lock:
            if self._is_readonly():
                return True
            if self._rw_holds > 0:
                self.getLoggingService().warn(
                    self.name, "Not switching to read-only: read-write is currently in use"
                )
                return False

            if self.manageTmpfs:
                logs_were_mounted = self._is_mounted("/var/log")
                for path, size, mode in self.TMPFS_PATHS:
                    critical = path in self.CRITICAL
                    if not critical and not os.path.isdir(path):
                        continue  # Dienst nicht installiert
                    if not self._mount_tmpfs(path, size, mode) and critical:
                        self.getLoggingService().error(
                            self.name, "Critical tmpfs mount failed - staying read-write"
                        )
                        return False
                if not logs_were_mounted:
                    # rsyslog hält sonst noch Dateien auf der (jetzt verdeckten) SD-Karte offen
                    self._sudo("systemctl", "try-restart", "rsyslog")
                if not self._setup_random_seed():
                    self.getLoggingService().warn(self.name, "random-seed setup failed, continuing")

            os.sync()
            rc, err = self._sudo("mount", "-o", "remount,ro", "/")
            if rc != 0:
                self.getLoggingService().error(
                    self.name,
                    f"Failed to remount / as read-only: {err} "
                    "(meist: Datei zum Schreiben offen; prüfen mit: "
                    "sudo lsof -nP -- / | awk '$4 ~ /[0-9][wu]/')",
                )
                return False

            self._remount_boot("ro")

            ro = self._is_readonly()
            if ro:
                self.getLoggingService().info(self.name, "System switched to read-only mode")
            return ro

    def disableReadonly(self) -> bool:
        with self._lock:
            if not self._is_readonly():
                return True

            rc, err = self._sudo("mount", "-o", "remount,rw", "/")
            if rc != 0:
                self.getLoggingService().error(
                    self.name, f"Failed to remount / as read-write: {err}"
                )
                return False

            self._remount_boot("rw")

            rw = not self._is_readonly()
            if rw:
                self.getLoggingService().info(self.name, "System switched to read-write mode")
            return rw

    def onMqttMessage(self, message):
        if not self.active:
            return

        action = message.get("action")
        try:
            if action == "enable":
                self.getLoggingService().info(self.name, "enable readonly via mqtt")
                self.enableReadonly()
            elif action == "disable":
                self.getLoggingService().info(self.name, "disable readonly via mqtt")
                self.disableReadonly()
        except Exception as e:
            self.getLoggingService().error(self.name, f"mqtt action '{action}' failed: {e}")
