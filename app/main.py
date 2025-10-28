import importlib.util
import importlib
import pkgutil
import inspect
import os
import sys

from fastapi import FastAPI, HTTPException
from app.services.abstract_base_service import AbstractBaseService
from app.services.abstract_sensor_service import AbstractSensorService
import app.services # unser Service-Package

# Dictionary aller geladenen Services
services = {}

SERVICES_DIR = os.path.join(os.path.dirname(__file__), "services")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
PROJECT_ROOT = os.path.dirname(BASE_DIR)              # raspi-controller/
sys.path.insert(0, PROJECT_ROOT)

def discover_services():
    print(f"[DEBUG] Scanne Services-Verzeichnis: {SERVICES_DIR}")
    if not os.path.exists(SERVICES_DIR):
        print(f"[ERROR] Verzeichnis existiert nicht!")
        return services

    for filename in os.listdir(SERVICES_DIR):
        if filename.endswith("service.py") and not filename.startswith("__") and not filename.startswith("abstract"):
            module_path = os.path.join(SERVICES_DIR, filename)
            module_name = filename[:-3]  # ohne .py
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Suche Service-Klassen
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, AbstractBaseService) and obj is not AbstractBaseService and obj is not AbstractSensorService:
                    print(f"[DEBUG] initializing service {obj}")
                    instance = obj()
                    services[instance.name] = instance
                    print(f"[DEBUG] Service geladen: {instance.name}")

    print(f"[DEBUG] Insgesamt {len(services)} Service(s) geladen")


discover_services()

app = FastAPI(title="Pi Controller API", version="0.4")

# -------- API Endpoints --------

@app.get("/")
def root():
    return {
        "name": app.title,
        "version": app.version,
        "services": listServicesWithState()
    }

@app.get("/services")
def listServicesWithState():
    """
    Gibt alle Services mit Name und Status zurück.
    """
    result = []
    for name, service in services.items():
        try:
            status = service.status()
        except Exception as e:
            status = {"active": False, "error": str(e)}

        result.append({
            "name": name,
            "status": status
        })
    return result

@app.get("/services")
def list_services():
    return list(services.keys())

@app.get("/services/{name}")
@app.get("/services/{name}/status")
def service_status(name: str):
    service = services.get(name)
    if not service:
        raise HTTPException(404, f"Service {name} not found")
    return service.updateState()

@app.post("/services/{name}/install")
def service_install(name: str):
    service = services.get(name)
    if not service:
        raise HTTPException(404, f"Service {name} not found")
    return {"success": service.doInstall()}

@app.post("/services/{name}/uninstall")
def service_uninstall(name: str):
    service = services.get(name)
    if not service:
        raise HTTPException(404, f"Service {name} not found")
    return {"success": service.doUninstall()}


@app.post("/services/{name}/activate")
def service_activate(name: str):
    service = services.get(name)
    if not service:
        raise HTTPException(404, f"Service {name} not found")
    return {"success": service.doActivate()}

@app.post("/services/{name}/deactivate")
def service_deactivate(name: str):
    service = services.get(name)
    if not service:
        raise HTTPException(404, f"Service {name} not found")
    return {"success": service.doDeactivate()}

@app.post("/services/{name}/configure")
def service_configure(name: str, config: dict):
    service = services.get(name)
    if not service:
        raise HTTPException(404, f"Service {name} not found")
    return {"success": service.doconfigure(config), "config": service.doconfig}
