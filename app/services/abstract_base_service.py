from abc import ABC, abstractmethod
from app.services.base.stdout_logging_service import StdoutLoggingService
from app.services.service_registry import ServiceRegistry
import time

class AbstractBaseService(ABC):
    """
    Abstrakte Basisklasse für alle Services
    """
    def __init__(self, name: str, registry, cacheTTL = 10):
        # initbase variables
        self.registry = registry
        self.state = None
        self.lastReadTime = 0
        self.name = name
        self.active = False
        # init variables based on state or config
        self.cacheTTL = cacheTTL

    def onReady(self):
        self.getLoggingService().debug(self.name, f"Service {self.name} init was successful, active: {self.active}")
        return

    def getService(self, serviceClass):
        #print(f"registry: {self.registry} - {self.registry.__class__}")
        return self.registry.get(serviceClass)

    def getServiceByName(self, serviceName):
        #print(f"registry: {self.registry} - {self.registry.__class__}")
        return self.registry.getByName(serviceName)

    def getLoggingService(self):
        return self.getService(StdoutLoggingService)

    def getState(self) -> dict:
        if (not self.isCacheValid()):
            self.lastReadTime = time.time()
            self.state = self.readState()
            self.getLoggingService().debug(self.name, f"cache was Invalid, current state {self.state}")

        return self.state

    def isCacheValid(self) -> bool:
        cacheTime = time.time() - self.lastReadTime
        return cacheTime <= self.cacheTTL

    # override if connections, etc. has to be closed for a clean shutdown
    def handleShutdownService(self):
        return
    
    def readState(self):
        return False