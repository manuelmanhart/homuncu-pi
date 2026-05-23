# Homuncu PI Main Entrypoint
# --------------------------
# Starts the service registry, discovers base and modular services, and enters the main loop.
# Config: Global config (via ConfigService) provides `projectName`, `projectVersion`, and other global settings.
# MQTT: Services may publish/subscribe via MqttService; the main loop only coordinates service readiness and shutdown.

import importlib
import importlib.util
import inspect
import os
import signal

from app.services.abstract_modular_base_service import AbstractModularBaseService
from app.services.abstract_sensor_service import AbstractSensorService
from app.services.service_registry import ServiceRegistry

def discoverBaseServices():
    discoverServicesInPackage("base")

def discoverModularServices():
    discoverServicesInPackage("modular")

def discoverServicesInPackage(package: str):
    print(f"[INFO] discovering {package} services")
    SERVICES_DIR = os.path.join(os.path.dirname(__file__), "services", package)

    for filename in os.listdir(SERVICES_DIR):
        if isService(filename):
            module_name = f"app.services.{package}.{filename[:-3]}"
            module = importlib.import_module(module_name)

            # Suche Service-Klassen
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module.__name__ or inspect.isabstract(obj):
                    continue
                #if issubclass(obj, AbstractModularBaseService) and obj is not AbstractModularBaseService and obj is not AbstractSensorService:
                print(f"[INFO] {name} - {filename} init service...")
                instance = obj(registry)
                registry.register(instance)

def isService(filename):
    return filename.endswith("service.py") \
        and not filename.startswith("__") \
        and not filename.startswith("abstract")

def handleShutdown(sig, frame):
    global running
    print("[INFO] Shutting down...")
    running = False
    registry.handleShutdownServices()

signal.signal(signal.SIGINT, handleShutdown)
signal.signal(signal.SIGTERM, handleShutdown)

def _get_project_version() -> str:
    version_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VERSION"
    )
    try:
        with open(version_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"

if __name__ == "__main__":
    projectName = "Homuncu PI"
    projectVersion = _get_project_version()
    print(f"[INFO] Starting {projectName} v{projectVersion}")

    registry = ServiceRegistry()
    discoverBaseServices()
    discoverModularServices()
    registry.readyServices()
    print("[INFO] Start reading loop")
    registry.loopReadingServices()
