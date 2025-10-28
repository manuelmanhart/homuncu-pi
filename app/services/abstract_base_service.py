from abc import ABC, abstractmethod
import logging
from app.config_loader import CONFIG

class AbstractBaseService(ABC):
    """
    Abstrakte Basisklasse für alle Services
    """
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug(f"[{self.name}] Service init...")
        self.installed = False
        self.active = False
        self.state = ""
        self.configFile = f'{name}.config.json'
        self.config = {}
        self.initStatus()

    def status(self) -> dict:
        return {
            "service": self.name,
            "installed": self.installed,
            "active": self.active,
            "state": self.state
        }

    def doInstall(self) -> dict:
        if self.installed:
            return self.status()
        self.installed = self.install()
        return self.status()

    def doUninstall(self) -> dict:
        if not self.installed:
            return self.status()
        self.installed = self.uninstall()
        return self.status()

    def doActivate(self) -> dict:
        if self.active:
            return self.status()
        self.active = self.activate()
        return self.status()

    def doDeactivate(self) -> dict:
        if not self.active:
            return self.status()
        self.active = self.deactivate()
        return self.status()

    def doConfigure(self, config: dict) -> bool:
        return self.configure()

    def saveConfig(self):
        """Speichert self.config als JSON-Datei"""
        try:
            with open(self.configFile, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Konfiguration speichern fehlgeschlagen: {e}")

    def loadConfig(self):
        """Lädt JSON-Datei in self.config, falls vorhanden"""
        if os.path.exists(self.configFile):
            try:
                with open(self.configFile, "r") as f:
                    cfg = json.load(f)
                    self.config.update(cfg)
            except Exception as e:
                print(f"[ERROR] Konfiguration laden fehlgeschlagen: {e}")

    #@abstractmethod
    def initStatus(self) -> bool:
        return NotImplementedError

    def install(self) -> bool:
        return True

    def uninstall(self) -> bool:
        return True

    @abstractmethod
    def activate(self) -> bool:
        return True

    @abstractmethod
    def deactivate(self) -> bool:
        return True

    @abstractmethod
    def configure(self, config: dict) -> bool:
        return True

    def updateState(self) -> bool:
        return True

    def getServiceConfig(self) -> dict:
        return CONFIG.get("services", {}).get(self.name, {})

    def getGlobalConfig(self, scope) -> dict:
        return CONFIG.get(scope, {})
