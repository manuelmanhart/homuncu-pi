import os
import yaml
from app.env_var_resolver import resolveVariable
from app.services.di_helper import registerService
from app.services.abstract_base_service import AbstractBaseService

class ConfigService(AbstractBaseService):
    def __init__(self):
        super().__init__("config")

    def _expand(self, obj):
        """Rekursiv über dict/list/str ersetzen."""
        if isinstance(obj, dict):
            return {k: self._expand(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._expand(v) for v in obj]
        if isinstance(obj, str):
            return resolveVariable(obj)
        return obj

    def readState(self):
        base_dir = os.path.join(os.path.dirname( __file__ ), '..', '..', '..')

        customConfigFile = os.path.join(base_dir, "config.yaml")
        defaultConfigFile = os.path.join(base_dir, "default_config.yaml")

        path = customConfigFile if os.path.exists(customConfigFile) else defaultConfigFile
        if not os.path.exists(path):
            raise FileNotFoundError("Weder config.yaml noch default_config.yaml gefunden")

        with open(path, "r") as f:
            self.getLoggingService().debug(f"[{self.name}] loading config file {path}")
            raw = yaml.safe_load(f)
            self.getLoggingService().debug(f"[{self.name}] config {raw}")

        # Expand environment placeholders recursively
        cfg = self._expand(raw or {})
        return cfg

    def getScopedConfig(self, scope) -> dict:
        config = self.getState()
        #self.getLoggingService().debug(f"[{self.name}] reading {scope} from config {config}")
        return config.get(scope, {})

# TODO implement update config functions which saves to config.yaml file
# TODO implement merging of the two yamls so we just override what we need from default_config.yaml

# Service in di registrieren
registerService(ConfigService, ConfigService())