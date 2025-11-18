from abc import ABC, abstractmethod
from app.services.base.logging_service import LoggingService
from app.services.di_helper import getService
import time

class AbstractBaseService(ABC):
    """
    Abstrakte Basisklasse für alle Services
    """
    def __init__(self, name: str, cacheTTL = 10):
        # initbase variables
        self.state = None
        self.lastReadTime = 0
        self.name = name
        # init variables based on state or config
        self.cacheTTL = cacheTTL

    def init(self):
        self.getLoggingService().debug(f"Service [{self.name}] init was successful")

    def getDIService(self, className):
        return getService(className)

    def getLoggingService(self):
        return getService(LoggingService)

    def getState(self) -> dict:
        if (not self.isCacheValid()):
            self.lastReadTime = time.time()
            self.state = self.readState()
            self.getLoggingService().debug(f"[{self.name}] cache was Invalid, current state {self.state}")

        return self.state

    def isCacheValid(self) -> bool:
        cacheTime = time.time() - self.lastReadTime
        return cacheTime <= self.cacheTTL

    # override if connections, etc. has to be closed for a clean shutdown
    def handleShutdownService(self):
        return
    
    def readState(self):
        return False