import subprocess

from app.services.abstract_modular_base_service import AbstractModularBaseService

# GitRepoService
# ------
# Provides a simple interface to pull a configured git repository via MQTT commands.
# Config keys (under services.git):
#   repos: list of repo definitions, each with:
#       name (str) – identifier used in incoming MQTT messages.
#       path (str) – filesystem path of the repository.
# MQTT: Listens for messages containing a JSON object with a "repo" field. On match, runs `git pull` in the configured path and logs the result.
class GitRepoService(AbstractModularBaseService):
    def __init__(self, registry):
        super().__init__("git", registry)

    def readState(self):
        return {
            "active": self.active
        }

    def onMqttMessage(self, message):
        self.getLoggingService().info(self.name, f"got message {message}")
        config = self.getServiceConfig()

        self.getLoggingService().debug(self.name, f" serviceConfig: {config}")

        if not message.get("repo"):
            self.getLoggingService().warn(self.name, "Please add a repository name in your message like: {\"repo\": \"myRepository1\"}")
        else:
            for r in config.get("repos", []):
                if message.get("repo") == r.get("name"):
                    self.getLoggingService().info(self.name, f"updating repository {r.get("name")} now")
                    workdir = r.get("path")
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=workdir,
                        capture_output=True,
                        text=True
                    )
                    self.getLoggingService().info(self.name, f"result: {result}")
                    return
