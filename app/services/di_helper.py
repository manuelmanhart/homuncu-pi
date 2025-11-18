# app/di.py
_services = {}

def inject(serviceClass):
    """Decorator für automatische Injektion"""
    def wrapper(*args, **kwargs):
        instance = serviceClass(*args, **kwargs)
        registerService(serviceClass.__name__, instance)
        return instance
    return wrapper

def registerService(serviceClass, instance):
    _services[serviceClass] = instance

def getService(serviceClass):
    return _services.get(serviceClass)
