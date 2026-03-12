from app.services.abstract_sensor_service import AbstractSensorService
import socket

# TODO check
class IpAddressService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("ipaddress", registry, 60 * 5, 0)

    def onReady(self):
        self.ipToConnectTo = self.getServiceConfig().get("ipToConnectTo", "8.8.8.8")
        self.portToConnectTo = self.getServiceConfig().get("portToConnectTo", 80)
        super().onReady()

    def readState(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.ipToConnectTo, self.portToConnectTo))
        #self.getLoggingService().debug(self.name, f"networking info: {s.getsockname()}")
        ipAddress = (s.getsockname()[0])
        self.getLoggingService().debug(self.name, f"current ip address {ipAddress}")
        s.close()
        return {
            "name": self.getGlobalConfig().get("hostname", ""),
            "ip": ipAddress,
        }

    def hasSignificantChange(self, oldState, newState) -> bool:
        self.getLoggingService().debug(self.name, f" hasSignificantChange {oldState} - {newState} -> results in {oldState != newState}")
        hasChanged = (oldState != newState)
        if hasChanged:
            self.getServiceByName("mqtt").setIpAddress(newState)
        return hasChanged
