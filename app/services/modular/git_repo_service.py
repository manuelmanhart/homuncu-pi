import subprocess

from app.services.abstract_modular_base_service import AbstractModularBaseService
from app.services.modular.readonly_service import ReadOnlyService


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

                    readonly = self.getService(ReadOnlyService)
                    was_readonly = readonly.ensure_readwrite()

                    workdir = r.get("path")
                    try:
                        result = subprocess.run(
                            ["git", "pull"],
                            cwd=workdir,
                            capture_output=True,
                            text=True
                        )
                        self.getLoggingService().info(self.name, f"result: {result}")
                    finally:
                        readonly.restore_readonly(was_readonly)
                    return
