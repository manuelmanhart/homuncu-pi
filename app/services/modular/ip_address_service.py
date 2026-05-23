from app.services.abstract_sensor_service import AbstractSensorService
import socket

# IpAddressService
# ------
# Determines the local IP address used to reach a configurable remote host/port.
# Config keys (under services.ipaddress):
#   ipToConnectTo (str) – remote IP to connect to (default "8.8.8.8").
#   portToConnectTo (int) – remote port (default 80).
# MQTT: Publishes its own IP via the MqttService; also updates the MQTT service's `ipAddress` filter when the address changes.
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
