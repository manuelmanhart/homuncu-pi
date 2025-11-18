from app.services.abstract_base_service import AbstractBaseService
import time
from app.services.base.config_service import ConfigService
from app.services.di_helper import getService

class AbstractConfigurableService(AbstractBaseService):
    """
    Abstrakte Basisklasse für alle Services, welche die Konfiguration auslesen oder speichern
    """
    def __init__(self, name: str):
        # initbase variables
        super().__init__(name)
        self.cacheTTL = self.getGlobalConfig().get("cacheTTL", 10)

    def _getConfigService(self):
        return getService(ConfigService)

    def getServiceConfig(self) -> dict:
        if not self.name or self.name == None:
            self.getLoggingService().error(f"[{self.name}] Cannot access service config yet, must be after init method has been completed!")
            return {}; # TBD do some useful error handling
        else:
            return self._getConfigService().getScopedConfig("services").get(self.name);

    def getGlobalConfig(self) -> dict:
        return self._getConfigService().getScopedConfig("global")
