import os
import re
import yaml
import socket

ENV_VAR_RE = re.compile(r'\$\{([^}:]+)(?::([^}]+))?\}')

def _replace_env_vars_in_string(s: str) -> str:
    """
    Ersetzt ${VAR} oder ${VAR:default} in einem String.
    - Zuerst wird os.environ geprüft.
    - Falls VAR == 'HOSTNAME' und keine Umgebungsvariable vorhanden ist, wird socket.gethostname() genutzt.
    - Falls ein Default angegeben ist, wird dieser verwendet wenn die Var nicht gesetzt ist.
    - Falls nichts gefunden wird, wird der Platzhalter durch einen leeren String ersetzt.
    """
    def repl(match):
        var = match.group(1)
        default = match.group(2)

        val = os.environ.get(var)
        if val is not None:
            return val

        # Spezial-Fallback für HOSTNAME
        if var == "HOSTNAME":
            return socket.gethostname()

        if default is not None:
            return default

        # Fallback leer (oder du könntest hier raise)
        return ""

    return ENV_VAR_RE.sub(repl, s)

def _expand(obj):
    """Rekursiv über dict/list/str ersetzen."""
    if isinstance(obj, dict):
        return {k: _expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand(v) for v in obj]
    if isinstance(obj, str):
        return _replace_env_vars_in_string(obj)
    return obj

def load_config():
    base_dir = os.path.dirname(__file__)
    user_cfg = os.path.join(base_dir, "config.yaml")
    default_cfg = os.path.join(base_dir, "default_config.yaml")

    path = user_cfg if os.path.exists(user_cfg) else default_cfg
    if not os.path.exists(path):
        raise FileNotFoundError("Weder config.yaml noch default_config.yaml gefunden")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    # Expand environment placeholders recursively
    cfg = _expand(raw or {})
    return cfg

CONFIG = load_config()
