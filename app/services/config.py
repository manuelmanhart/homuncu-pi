import os
import yaml
import socket
from app.env_var_resolver import resolveVariable

class ConfigService():
    def __init__(self):
        self.loadConfig()

    def readState(self):
        return True

    def activate(self) -> bool:
        return True

    def deactivate(self) -> bool:
        return True

    def configure(self, config: dict) -> bool:
        return True

    def _expand(self, obj):
        """Rekursiv über dict/list/str ersetzen."""
        if isinstance(obj, dict):
            return {k: self._expand(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._expand(v) for v in obj]
        if isinstance(obj, str):
            return resolveVariable(obj)
        return obj

    def loadConfig(self):
        base_dir = os.path.join(os.path.dirname( __file__ ), '..', '..')

        user_cfg = os.path.join(base_dir, "config.yaml")
        default_cfg = os.path.join(base_dir, "default_config.yaml")

        path = user_cfg if os.path.exists(user_cfg) else default_cfg
        if not os.path.exists(path):
            raise FileNotFoundError("Weder config.yaml noch default_config.yaml gefunden")

        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        # Expand environment placeholders recursively
        cfg = self._expand(raw or {})
        return cfg
