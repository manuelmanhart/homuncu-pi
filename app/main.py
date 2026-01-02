import time
import signal
import threading
import importlib.util
import inspect
import os
from app.services.abstract_modular_base_service import AbstractModularBaseService
from app.services.abstract_sensor_service import AbstractSensorService

services = {}
running = True

def discoverBaseServices():
    discoverServicesInPackage("base")

def discoverModularServices():
    discoverServicesInPackage("modular")

def discoverServicesInPackage(package: str):
    print(f"[INFO] discovering {package} services")
    SERVICES_DIR = os.path.join(os.path.dirname(__file__), "services", package)

    for filename in os.listdir(SERVICES_DIR):
        if isService(filename):
            module_path = os.path.join(SERVICES_DIR, filename)
            module_name = filename[:-3]  # ohne .py
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Suche Service-Klassen
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, AbstractModularBaseService) and obj is not AbstractModularBaseService and obj is not AbstractSensorService:
                    print(f"[INFO] {name} init service...")
                    instance = obj()
                    services[instance.name] = instance
                    print(f"[INFO] {name} init successfully - active: {instance.active} ")

def isService(filename):
    return filename.endswith("service.py") \
        and not filename.startswith("__") \
        and not filename.startswith("abstract") \
        and not filename.endswith("helper.py")

def loopReadingServices():
    while running:
        for name, service in services.items():
            try:
                state = service.getState()
            except Exception as e:
                print(f"[ERROR] {name} status failed: {e}")
        time.sleep(10)

def handleShutdownServices(sig, frame):
    global running
    print("[INFO] Shutting down...")
    running = False
    for name, service in services.items():
        service.handleShutdownService()

signal.signal(signal.SIGINT, handleShutdownServices)
signal.signal(signal.SIGTERM, handleShutdownServices)

if __name__ == "__main__":
    # TODO read projectName and projectVersion dynamically
    projectName="RaspiController"
    projectVersion="1.0.0-beta"
    print(f"[INFO] Starting {projectName} v{projectVersion}")

    discoverBaseServices()
    discoverModularServices()

    print("[INFO] Start reading loop")
    threading.Thread(target=loopReadingServices, daemon=True).start()

    while running:
        time.sleep(1)
