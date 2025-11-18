from app.services.di_helper import registerService
from datetime import datetime

# Logging Service cannot inherit any of the service classes as this would result in a circular dependency
# because AbstractBaseService imports the LoggingService
class LoggingService():
    """
    Logging service
    """
    def __init__(self):
        return

    def debug(self, message: str):
        self.log("DEBUG", message)

    def info(self, message: str):
        self.log("INFO", message)

    def warn(self, message: str):
        self.log("WARN", message)

    def error(self, message: str):
        self.log("ERROR", message)

    def log(self, logLevel: str, message: str):
        now = datetime.now().isoformat()
        print(f"{now} [{logLevel}] {message}")

    # TODO setting log level for future use / implementation (to change on mqtt message)
    def setLogLevel():
        return
# Service in di registrieren
registerService(LoggingService, LoggingService())