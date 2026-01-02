from datetime import datetime

from app.services.di_helper import registerService

# StdoutLoggingService cannot inherit any of the service classes as this would result in a circular dependency
# because AbstractBaseService imports the StdoutLoggingService
class StdoutLoggingService():
    """
    writes the log to stdout
    """
    LOG_LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARN": 30,
        "ERROR": 40
    }

    def __init__(self):
        self.config = {}
        return

    def debug(self, className, message: str):
        self.log(className, "DEBUG", message)

    def info(self, className, message: str):
        self.log(className, "INFO", message)

    def warn(self, className, message: str):
        self.log(className, "WARN", message)

    def error(self, className, message: str):
        self.log(className, "ERROR", message)

    def log(self, className:str, messageLevel: str, message: str):
        if (self.shouldBeLogged(messageLevel, className)):
            now = datetime.now().isoformat()
            print(f"{now} [{messageLevel}] [{className}] {message}")

    def shouldBeLogged(self, messageLevel: str, className: str) -> bool:
        now = datetime.now().isoformat()
        defaultLevel = self.translate(self.config.get("default", "INFO"))
#        print(f"{now} [DEBUG] [LOGGER] shouldBeLogged: defaultLevel: {defaultLevel} - messageLevel: {messageLevel} - classNmae: {className}")

        classLevelName = self.config.get(className)
        if classLevelName:
            configuredLevel = self.translate(classLevelName)
        else:
            configuredLevel = defaultLevel

#        print(f"{now} [DEBUG] [LOGGER] shouldBeLogged: {self.translate(messageLevel)} >= {configuredLevel}")
        return self.translate(messageLevel) >= configuredLevel

    def translate(self, level: str) -> int:
        return self.LOG_LEVELS.get(level.upper(), 20)

    def setConfig(self, config: dict):
        self.config = config

# Service in di registrieren
registerService(StdoutLoggingService, StdoutLoggingService())
