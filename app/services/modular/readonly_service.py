import os
import subprocess

from app.services.abstract_modular_base_service import AbstractModularBaseService


class ReadOnlyService(AbstractModularBaseService):
    def __init__(self, registry):
        super().__init__("readonly", registry)
        self._readonly = False
        self._tmpfs_mounts = []

    def onReady(self):
        config = self.getServiceConfig()
        self._readonly = self._is_readonly()
        enable_on_boot = config.get("enableOnBoot", False)
        if enable_on_boot and not self._readonly:
            self.getLoggingService().info(
                self.name, "enableOnBoot is set – enabling read-only mode"
            )
            self.enableReadonly()
        super().onReady()

    def readState(self) -> dict:
        return {
            "readonly": self._readonly,
            "tmpfs_mounts": self._tmpfs_mounts,
        }

    def ensure_readwrite(self) -> bool:
        if self._readonly:
            self.getLoggingService().info(
                self.name, "Temporarily switching to read-write mode"
            )
            self.disableReadonly()
            return True
        return False

    def restore_readonly(self, was_readonly: bool):
        if was_readonly:
            self.enableReadonly()
            self.getLoggingService().info(
                self.name, "Restored read-only mode"
            )

    def _is_readonly(self) -> bool:
        try:
            with open("/proc/mounts") as f:
                for line in f:
                    parts = line.split()
                    if parts[1] == "/":
                        return "ro" in parts[3].split(",")
        except Exception:
            pass
        return False

    def _is_mounted(self, path: str) -> bool:
        try:
            with open("/proc/mounts") as f:
                for line in f:
                    parts = line.split()
                    if parts[1] == path:
                        return True
        except Exception:
            pass
        return False

    def _mount_tmpfs(self, path: str, size: str = None, mode: str = None) -> bool:
        if self._is_mounted(path):
            self.getLoggingService().debug(self.name, f"{path} already mounted")
            return True

        os.makedirs(path, exist_ok=True)

        cmd = ["sudo", "mount", "-t", "tmpfs", "tmpfs", path]
        if size or mode:
            opts = []
            if size:
                opts.append(f"size={size}")
            if mode:
                opts.append(f"mode={mode}")
            cmd.extend(["-o", ",".join(opts)])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            self.getLoggingService().error(
                self.name, f"Failed to mount tmpfs on {path}: {result.stderr}"
            )
            return False

        self._tmpfs_mounts.append(path)
        self.getLoggingService().debug(self.name, f"Mounted tmpfs on {path}")
        return True

    def _setup_random_seed(self) -> bool:
        check = subprocess.run(
            ["sudo", "test", "-f", "/var/lib/systemd/random-seed"],
            capture_output=True,
        )
        if check.returncode != 0:
            return True

        target_exists = subprocess.run(
            ["sudo", "test", "-e", "/tmp/systemd-random-seed"],
            capture_output=True,
        )
        try:
            if target_exists.returncode == 0:
                subprocess.run(
                    ["sudo", "rm", "-f", "/var/lib/systemd/random-seed"],
                    check=True, capture_output=True,
                )
            else:
                subprocess.run(
                    ["sudo", "mv", "/var/lib/systemd/random-seed", "/tmp/systemd-random-seed"],
                    check=True, capture_output=True,
                )
            subprocess.run(
                ["sudo", "ln", "-s", "/tmp/systemd-random-seed", "/var/lib/systemd/random-seed"],
                check=True, capture_output=True,
            )
            self.getLoggingService().debug(self.name, "Symlinked random-seed to /tmp")
            return True
        except subprocess.CalledProcessError as e:
            self.getLoggingService().error(
                self.name, f"Failed to setup random-seed: {e}"
            )
            return False

    def enableReadonly(self) -> bool:
        if self._readonly:
            return True

        result = True

        tmpfs_paths = [
            ("/tmp", None, None),
            ("/var/tmp", None, None),
            ("/var/log", "50m", None),
            ("/var/spool/mail", "25m", None),
            ("/var/spool/rsyslog", "25m", None),
            ("/var/lib/logrotate", "1m", "0755"),
            ("/var/lib/sudo", "1m", "0700"),
        ]

        for path, size, mode in tmpfs_paths:
            if not self._mount_tmpfs(path, size, mode):
                result = False

        if not self._setup_random_seed():
            result = False

        for boot_mount in ["/boot/firmware", "/boot"]:
            if self._is_mounted(boot_mount):
                subprocess.run(
                    ["sudo", "mount", "-o", "remount,ro", boot_mount],
                    capture_output=True, text=True,
                )

        ro_result = subprocess.run(
            ["sudo", "mount", "-o", "remount,ro", "/"],
            capture_output=True, text=True,
        )
        if ro_result.returncode != 0:
            self.getLoggingService().error(
                self.name, f"Failed to remount / as read-only: {ro_result.stderr}"
            )
            result = False

        self._readonly = self._is_readonly()
        if self._readonly:
            self.getLoggingService().info(self.name, "System switched to read-only mode")
        return result

    def disableReadonly(self) -> bool:
        if not self._readonly:
            return True

        for boot_mount in ["/boot/firmware", "/boot"]:
            if self._is_mounted(boot_mount):
                subprocess.run(
                    ["sudo", "mount", "-o", "remount,rw", boot_mount],
                    capture_output=True, text=True,
                )

        rw_result = subprocess.run(
            ["sudo", "mount", "-o", "remount,rw", "/"],
            capture_output=True, text=True,
        )
        if rw_result.returncode != 0:
            self.getLoggingService().error(
                self.name, f"Failed to remount / as read-write: {rw_result.stderr}"
            )
            return False

        self._readonly = self._is_readonly()
        if not self._readonly:
            self.getLoggingService().info(self.name, "System switched to read-write mode")
        return True

    def onMqttMessage(self, message):
        if not self.active:
            return

        action = message.get("action")
        if action == "enable":
            self.getLoggingService().info(self.name, "enable readonly via mqtt")
            self.enableReadonly()
        elif action == "disable":
            self.getLoggingService().info(self.name, "disable readonly via mqtt")
            self.disableReadonly()
