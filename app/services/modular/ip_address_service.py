from app.services.abstract_sensor_service import AbstractSensorService
import socket

# TODO check
class IpAddressService(AbstractSensorService):
    def __init__(self):
        super().__init__("ipaddress", 60 * 5, 0)
        self.ipToConnectTo = self.getServiceConfig().get("ipToConnectTo", "8.8.8.8")
        self.portToConnectTo = self.getServiceConfig().get("portToConnectTo", 80)

    def readState(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((self.ipToConnectTo, self.portToConnectTo))
        #self.getLoggingService().debug(self.name, f"networking info: {s.getsockname()}")
        ipAddress = (s.getsockname()[0])
        self.getLoggingService().debug(self.name, f"current ip address {ipAddress}")
        s.close()
        return {
            "name": self.getGlobalConfig().get("hostname", ""),
            "ipaddress": ipAddress,
        }

    def hasSignificantChange(self, oldState, newState) -> bool:
        self.getLoggingService().debug(self.name, f" hasSignificantChange {oldState} - {newState} -> results in {oldState != newState}")
        return oldState != newState
