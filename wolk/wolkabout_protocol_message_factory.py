"""Serialize mesasges in WolkAbout Protocol format."""
#   Copyright 2018 WolkAbout Technology s.r.o.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import json

from wolkabout.iot.wolk.interface import message_factory
from wolkabout.iot.wolk.model import message


class WolkAboutProtocolMessageFactory(message_factory.MessageFactory):
    """Serialize device data to be sent to the Platform."""

    DEVICE_PATH_PREFIX = "d/"
    REFERENCE_PATH_PREFIX = "r/"
    TOPIC_DELIMITER = "/"
    LAST_WILL = "lastwill/"
    SENSOR_READING = "d2p/sensor_reading/"
    ALARM = "d2p/events/"
    ACTUATOR_STATUS = "d2p/actuator_status/"
    CONFIGURATION_STATUS = "d2p/configuration_get/"
    KEEP_ALIVE = "ping/"

    def __init__(self, device_key):
        """
        Create a factory for serializing mesasges.

        :param device_key: Device key to use when serializing messages
        :type device_key: str
        """
        self.device_key = device_key

    def make_from_sensor_reading(self, reading):
        """
        Serialize a sensor reading to be sent to the Platform.

        :param reading: Sensor reading to serialize
        :type reading: SensorReading
        :return: serialized message
        :rtype: message.Message
        """
        topic = (
            self.SENSOR_READING
            + self.DEVICE_PATH_PREFIX
            + self.device_key
            + self.TOPIC_DELIMITER
            + self.REFERENCE_PATH_PREFIX
            + reading.reference
        )
        payload = {}

        if reading.timestamp is not None:
            payload["utc"] = reading.timestamp

        if type(reading.value) == 10:  # PTUPLE
            delimiter = ","

            values_list = []

            for single_value in reading.value:
                if single_value is True:
                    single_value = "true"
                elif single_value is False:
                    single_value = "false"
                if "\n" in str(single_value):
                    single_value = single_value.replace("\n", "\\n")
                    single_value = single_value.replace("\\\\n", "\\n")
                    single_value = single_value.replace("\r", "")
                if '"' in str(single_value):
                    single_value = single_value.replace('"', '\\"')
                    single_value = single_value.replace('\\\\"', '\\"')
                values_list.append(single_value)

            string_values = str()

            for tuple_value in values_list:
                string_values += str(tuple_value)
                string_values += delimiter

            string_values = string_values[:-1]
            reading.value = string_values

        if reading.value is True:
            reading.value = "true"
        elif reading.value is False:
            reading.value = "false"

        if "\n" in str(reading.value):
            reading.value = reading.value.replace("\n", "\\n")
            reading.value = reading.value.replace("\r", "")
        if '"' in str(reading.value):
            reading.value = reading.value.replace('"', '\\"')

        payload["data"] = str(reading.value)

        return message.Message(topic, json.dumps(payload))

    def make_from_alarm(self, alarm):
        """
        Serialize the alarm to be sent to WolkAbout IoT Platform.

        :param alarm: Alarm event to be serialized
        :type alarm: Alarm
        :returns: message
        :rtype: Message
        """
        topic = (
            self.ALARM
            + self.DEVICE_PATH_PREFIX
            + self.device_key
            + self.TOPIC_DELIMITER
            + self.REFERENCE_PATH_PREFIX
            + alarm.reference
        )
        payload = {}

        if alarm.timestamp is not None:
            payload["utc"] = alarm.timestamp

        if alarm.active is True:
            alarm.active = "true"
        elif alarm.active is False:
            alarm.active = "false"

        payload["data"] = alarm.active

        return message.Message(topic, json.dumps(payload))

    def make_from_actuator_status(self, actuator):
        """
        Serialize the actuator status to be sent to WolkAbout IoT Platform.

        :param actuator: Actuator status to be serialized
        :type actuator: ActuatorStatus
        :returns: message
        :rtype: Message
        """
        topic = (
            self.ACTUATOR_STATUS
            + self.DEVICE_PATH_PREFIX
            + self.device_key
            + self.TOPIC_DELIMITER
            + self.REFERENCE_PATH_PREFIX
            + actuator.reference
        )
        payload = {"status": actuator.state}

        if actuator.value is True:
            actuator.value = "true"
        elif actuator.value is False:
            actuator.value = "false"
        if "\n" in str(actuator.value):
            actuator.value = actuator.value.replace("\n", "\\n")
            actuator.value = actuator.value.replace("\r", "")
            actuator.value = actuator.value.replace("\\\\n", "\\n")
        if '"' in str(actuator.value):
            actuator.value = actuator.value.replace('"', '\\"')
            actuator.value = actuator.value.replace('\\\\"', '\\"')

        payload["value"] = str(actuator.value)

        return message.Message(topic, json.dumps(payload))

    def make_from_configuration(self, configuration):
        """
        Serialize device's configuration to WolkAbout IoT Platform.

        :param configuration: Device's current configuration
        :type configuration: dict
        :returns: message
        :rtype: Message
        """
        topic = self.CONFIGURATION_STATUS + self.DEVICE_PATH_PREFIX + self.device_key

        for reference, value in configuration.items():
            if "\n" in str(value):
                configuration[reference] = value.replace("\n", "\\n")
                configuration[reference] = value.replace("\\\\n", "\\n")
                configuration[reference] = value.replace("\r", "")
            if '"' in str(value):
                configuration[reference] = value.replace('"', '\\"')
                configuration[reference] = value.replace('\\\\"', '\\"')
            if value is True:
                configuration[reference] = "true"
            elif value is False:
                configuration[reference] = "false"

            configuration[reference] = str(value)

        payload = {"values": configuration}

        return message.Message(topic, json.dumps(payload))

    def make_from_ping_keep_alive_message(self):
        """
        Serialize a ping keep alive message.

        :returns: message
        :rtype: Message
        """
        return message.Message(self.KEEP_ALIVE + self.device_key, None)
