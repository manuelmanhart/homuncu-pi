import os
import yaml
from copy import deepcopy
from app.env_var_resolver import resolveVariable
from app.services.abstract_base_service import AbstractBaseService

def _deep_merge(base, override):
    """Merge `override` into `base` recursively. Returns a new dict."""
    result = deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = deepcopy(val)
    return result

# ConfigService
# ------
# Loads default_config.yaml as base and overlays config.yaml on top.
# This way config.yaml only needs values that differ from the defaults.
# Environment variables are expanded after merging.
# Config structure:
#   global: {...} – global settings (e.g. hostname, cacheTTL).
#   services: { <service_name>: { … } } – per‑service configuration used by AbstractConfigurableService.
# MQTT: No direct MQTT usage.
class ConfigService(AbstractBaseService):
    def __init__(self, registry):
        print(f"registry {registry}")
        super().__init__("config", registry)

    def _expand(self, obj):
        """Rekursiv über dict/list/str ersetzen."""
        if isinstance(obj, dict):
            return {k: self._expand(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._expand(v) for v in obj]
        if isinstance(obj, str):
            return resolveVariable(obj)
        return obj

    def _load_yaml(self, path):
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
            self.getLoggingService().debug(self.name, f" loaded {path}: {raw}")
            return raw or {}

     def readState(self):
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
        defaultConfigFile = os.path.join(base_dir, "default_config.yaml")
        defaults = self._load_yaml(defaultConfigFile) 
        if not os.path.exists(defaultConfigFile):
            raise FileNotFoundError("default_config.yaml nicht gefunden")

        customConfigFile = os.path.join(base_dir, "config.yaml")
        if os.path.exists(customConfigFile):
            overrides = self._load_yaml(customConfigFile)
            merged = _deep_merge(defaults, overrides)
            self.getLoggingService().debug(self.name, f" merged with config.yaml")
        else:
            merged = defaults

        cfg = self._expand(merged)
        return cfg

    def getScopedConfig(self, scope) -> dict:
        config = self.getState()
        return config.get(scope, {})
