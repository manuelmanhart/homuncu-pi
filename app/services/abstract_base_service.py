from abc import ABC, abstractmethod
import logging
#from app.config_loader import CONFIG
from app.services import CONFIG_SERVICE
import time

class AbstractBaseService(ABC):
    """
    Abstrakte Basisklasse für alle Services
    """
    def __init__(self, name: str):
        # initbase variables
        self.name = name
        self.state = None
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug(f"[{self.name}] Service init...")
        # init config
        self.config = self.getServiceConfig()
        # init variables based on state or config
        self.installed = False
        self.lastReadTime = 0
        self.active = self.config.get("active", False)
        self.cacheTTL = self.config.get("cacheTimeout", 10)

    def status(self) -> dict:
        if (not self.isCacheValid()):
            print(f"cache is invalid reading current state...")
            self.lastReadTime = time.time()
            self.state = self.readState()

        return {
            "service": self.name,
            "installed": self.installed,
            "active": self.active,
            "state": self.state
        }

    def isCacheValid(self) -> bool:
        cacheTime = time.time() - self.lastReadTime
        return cacheTime <= self.cacheTTL

    @abstractmethod
    def readState(self):
        """Implement me in subclasses"""
        raise NotImplementedError

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

    def configure(self, config: dict) -> bool:
        return True

    def getServiceConfig(self) -> dict:
        return CONFIG_SERVICE.loadConfig().get("services", {}).get(self.name, {})

    def getGlobalConfig(self, scope) -> dict:
        return CONFIG_SERVICE.loadConfig().get(scope, {})
