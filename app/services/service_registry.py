import time

# ServiceRegistry
# ------
# Holds references to all instantiated services and provides lookup helpers.
# Config: None (services are registered at runtime).
# MQTT: No direct MQTT usage – services retrieve MqttService via getService().
class ServiceRegistry:

    def __init__(self):
        self._services_by_name = {}
        self._services_by_class = {}
        self.running = False

    def register(self, instance):
        name = instance.name
        cls = instance.__class__

        if name in self._services_by_name:
            raise RuntimeError(f"Service '{name}' already registered")
        #else:
            #print(f"registering service {name} with class {cls}")
        self._services_by_name[name] = instance
        self._services_by_class[cls] = instance

    def getByName(self, name: str):
        #print(f"getByName({name}): {self._services_by_name.get(name)}")
        return self._services_by_name.get(name)

    def get(self, cls):
        #print(f"getByClass({cls}): {self._services_by_class.get(cls)}")
        return self._services_by_class.get(cls)

    def all(self):
        return self._services_by_name.values()

    def handleShutdownServices(self):
        self.running = False
        for service in self.all():
            service.handleShutdownService()

    def readyServices(self):
        for service in self.all():
            service.onReady()

    def loopReadingServices(self):
        self.running = True
        while self.running:
            for service in self.all():
                try:
                    service.getState()
                except Exception as e:
                    print(f"[ERROR] {service.name} status failed: {e}")
            time.sleep(10)
