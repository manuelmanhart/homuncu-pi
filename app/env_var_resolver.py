import os
import socket
import re

ENV_VAR_RE = re.compile(r'\$\{([^}:]+)(?::([^}]+))?\}')

def resolveVariable(s: str) -> str:
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

        val = os.getenv(var)
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
