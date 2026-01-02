import paho.mqtt.client as mqtt
from datetime import datetime
import json

from app.services.abstract_configurable_service import AbstractConfigurableService
from app.services.di_helper import registerService
from app.services.base.mqtt_send_flags import MqttSendFlags

class MqttService(AbstractConfigurableService):
    """
    MQTT service
    """
    def __init__(self):
        super().__init__("mqtt")
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.inTopic = self.getServiceConfig().get("inTopic", "")
        self.baseOutTopic = self.getServiceConfig().get("baseOutTopic", "")
        self.hostname = self.getGlobalConfig().get("hostname", "")

        # Set the will message, when the Raspberry Pi is powered off, or the network is interrupted abnormally, it will send the will message to other clients
        self.client.will_set(f"{self.baseOutTopic}/logging", b'{"status": "Off"}')

        # Create connection, the three parameters are broker address, broker port number, and keep-alive time respectively
        mqttHost = self.getServiceConfig().get("host", "")
        mqttPort = self.getServiceConfig().get("port", "")
        if (mqttHost == "" or mqttPort == ""):
            self.getLoggingService().error(self.name, f"please provide full config to mqtt server - host: {mqttHost} port: {mqttPort}")
        else:
            self.client.connect(mqttHost, mqttPort, 60)
            # Start the network loop
            self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        self.getLoggingService().debug(self.name, f" connected with result code {rc}")
        # Subscribe, which need to put into on_connect
        # If reconnect after losing the connection with the broker, it will continue to subscribe to the raspberry/topic topic
        self.client.subscribe(self.inTopic)

    # The callback function, it will be triggered when receiving messages
    def on_message(self, client, userdata, msg):
        # TBD refactor so the service sends an internal event / message to all services
        # only if the hostname is either not set or set to this rpi hostname
        # send log to the logging topic
        # TODO send logging event (see https://stackoverflow.com/questions/1092531/which-python-packages-offer-a-stand-alone-event-system/16192256#16192256)
        self.sendMessage("logging", f"I got your message {msg}")
        self.getLoggingService().debug(self.name, f" Got mqtt message with topic {msg.topic} and payload {msg.payload}")

    def sendMessage(self, topic: str, payload: str, flags: MqttSendFlags = MqttSendFlags.NONE):
        self.getLoggingService().debug(self.name, f"MQTT flags given: {flags}")

        if MqttSendFlags.ADD_HOSTNAME in flags and self.hostname != "":
            topic = f"{self.hostname}/{topic}"

        if MqttSendFlags.ADD_BASE_TOPIC in flags and self.baseOutTopic != "":
            topic = f"{self.baseOutTopic}/{topic}"

        if MqttSendFlags.ADD_TIMESTAMP in flags:
            payload = json.dumps({
                "state": payload,
                "timestamp": datetime.now().isoformat()
            })

        self.getLoggingService().debug(self.name, f" sending mqtt message to topic {topic} with payload {payload}")
        self.client.publish(f"{topic}", payload)

    def handleShutdownService(self):
        self.getLoggingService().debug(self.name, f" disconnecting mqtt")
        self.client.disconnect()

# Service in di registrieren
registerService(MqttService, MqttService())