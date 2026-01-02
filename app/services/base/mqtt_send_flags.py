from enum import Flag, auto

class MqttSendFlags(Flag):
    NONE = 0
    ADD_BASE_TOPIC = auto()
    ADD_HOSTNAME = auto()
    ADD_TIMESTAMP = auto()

    @staticmethod
    def parse(value: str | None) -> "MqttSendFlags":
        if not value:
            return MqttSendFlags.NONE

        value = value.strip()

        if value.upper() == "NONE":
            return MqttSendFlags.NONE

        flags = MqttSendFlags.NONE

        # Unterstützte Separatoren
        for part in value.replace("|", ",").split(","):
            name = part.strip().upper()
            try:
                flags |= MqttSendFlags[name]
            except KeyError:
                raise ValueError(f"Unknown MQTT flag: {name}")

        return flags
