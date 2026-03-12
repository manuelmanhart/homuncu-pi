from app.services.abstract_base_service import AbstractBaseService
import time
from app.services.base.config_service import ConfigService

class AbstractConfigurableService(AbstractBaseService):
    """
    Abstrakte Basisklasse für alle Services, welche die Konfiguration auslesen oder speichern
    """
    def __init__(self, name: str, registry):
        # initbase variables
        super().__init__(name, registry)

    def onReady(self):
        self.cacheTTL = self.getGlobalConfig().get("cacheTTL", self.cacheTTL)
        super().onReady()

    def _getConfigService(self):
        return self.getService(ConfigService)

    def getServiceConfig(self) -> dict:
        if not self.name or self.name == None:
            self.getLoggingService().error(self.name, "Cannot access service config yet, must be after init method has been completed!")
            return {}; # TBD do some useful error handling
        else:
            return self._getConfigService().getScopedConfig("services").get(self.name)

    def getGlobalConfig(self) -> dict:
        return self._getConfigService().getScopedConfig("global")
