import importlib
import importlib.util
import inspect
import os
import sys

from pathlib import Path
from fastapi import FastAPI, HTTPException
from app.services.abstract_base_service import AbstractBaseService
from app.services.abstract_sensor_service import AbstractSensorService
from app.services.base import ConfigService
from app.services.base import MqttService
#import app.services.modular # unser Service-Package
from app.env_var_resolver import resolveVariable
import asyncio

# Dictionary aller geladenen Services
services = {}
SERVICES_DIR = os.path.join(os.path.dirname(__file__), "services", "modular")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
PROJECT_ROOT = os.path.dirname(BASE_DIR)               # raspi-controller/
sys.path.insert(0, PROJECT_ROOT)

def isService(filename):
    return filename.endswith("service.py") \
        and not filename.startswith("__") \
        and not filename.startswith("abstract") \
        and not filename.endswith("helper.py")

def discover_services():
    print(f"[DEBUG] Scanne Services-Verzeichnis: {SERVICES_DIR}")
    if not os.path.exists(SERVICES_DIR):
        print(f"[ERROR] Verzeichnis existiert nicht!")
        return services

    for filename in os.listdir(SERVICES_DIR):
        if isService(filename):
            module_path = os.path.join(SERVICES_DIR, filename)
            module_name = filename[:-3]  # ohne .py
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Suche Service-Klassen
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, AbstractBaseService):
                    print(f"[DEBUG] initializing service {obj}")
                    instance = obj()
                    services[instance.name] = instance
                    print(f"[DEBUG] Service geladen: {instance.name}")

    print(f"[DEBUG] Insgesamt {len(services)} Service(s) geladen")

# set hostname for full state
hostname = resolveVariable("${HOSTNAME}")

# read version from file VERSION in project root
base_dir = os.path.join(os.path.dirname( __file__ ), '..')
versionFileFullPath = os.path.join(base_dir, "VERSION")
versionFile = Path(versionFileFullPath)
if versionFile.exists():
    version = versionFile.read_text().strip()
else:
    version = "0.0.0-dev"

app = FastAPI(title="Raspi Controller API", version=version)

# -------- API Endpoints --------

async def start_services():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, discover_services)
#    discover_services()
    print(f"config: {CONFIG.loadConfig()}")

start_services()