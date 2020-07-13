"""Deserialize messages according to WolkAbout Protocol."""
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

from wolkabout.iot.wolk.interface import message_deserializer
from wolkabout.iot.wolk.model import actuator_command


class WolkAboutProtocolMessageDeserializer(message_deserializer.MessageDeserializer):
    """Deserialize messages received from the WolkAbout IoT Platform."""

    DEVICE_PATH_DELIMITER = "d/"
    REFERENCE_PATH_PREFIX = "r/"
    TOPIC_DELIMITER = "/"
    KEEP_ALIVE_RESPONSE = "pong/"
    ACTUATOR_SET = "p2d/actuator_set/"
    CONFIGURATION_SET = "p2d/configuration_set/"

    def __init__(self, device):
        """
        Create message deserializer and list of inbound topics.

        :param device: Device key and actuator references for inbound topics
        :type device: Device
        """
        self.inbound_topics = [
            self.KEEP_ALIVE_RESPONSE + device.key,
            self.CONFIGURATION_SET + self.DEVICE_PATH_DELIMITER + device.key,
        ]

        for reference in device.actuator_references:
            self.inbound_topics.append(
                self.ACTUATOR_SET
                + self.DEVICE_PATH_DELIMITER
                + device.key
                + self.TOPIC_DELIMITER
                + self.REFERENCE_PATH_PREFIX
                + reference
            )

    def get_inbound_topics(self):
        """
        Return list of inbound topics for device.

        :return: List of topics to subscribe to
        :rtype: List[str]
        """
        return self.inbound_topics

    def is_keep_alive_response(self, message):
        """
        Check if message is keep alive response.

        :param message: The message received
        :type message: Message
        :returns: keep_alive_response
        :rtype: bool
        """
        keep_alive_response = message.topic.startswith(self.KEEP_ALIVE_RESPONSE)

        return keep_alive_response

    def is_actuation_command(self, message):
        """
        Check if message is actuation command.

        :param message: The message received
        :type message: Message
        :returns: actuation_command
        :rtype: bool
        """
        actuation_command = message.topic.startswith(self.ACTUATOR_SET)

        return actuation_command

    def is_configuration_command(self, message):
        """
        Check if message is configuration command.

        :param message: The message received
        :type message: Message
        :returns: configuration
        :rtype: bool
        """
        configuration = message.topic.startswith(self.CONFIGURATION_SET)
        return configuration

    def parse_actuator_command(self, message):
        """
        Parse the message into an actuation command.

        :param message: Message to be deserialized
        :type message: Message
        :returns: actuation
        :rtype: ActuatorCommand
        """
        reference = message.topic.split("/")[-1]
        bytearray_payload = bytearray(message.payload)
        payload = json.loads(bytearray_payload)

        value = payload.get("value")
        try:
            value = float(value)
        except Exception:
            try:
                value = int(value)
            except Exception:
                pass
        if "\\n" in str(value):
            value = value.replace("\\n", "\n")
            value = value.replace("\r", "")
        if '\\"' in str(value):
            value = value.replace('\\"', '"')

        if value == "true":
            value = True
        elif value == "false":
            value = False
        actuation = actuator_command.ActuatorCommand(reference, value)
        return actuation

    def parse_configuration_command(self, message):
        """
        Deserialize the message into configurations.

        :param message: The message received
        :type message: Message
        :returns: configurations
        :rtype: dict
        """
        bytearray_payload = bytearray(message.payload)
        configurations = json.loads(bytearray_payload)

        temp_dict = {}

        for received_reference, received_value in configurations.items():
            try:
                if "." in received_value:
                    temp_value = float(received_value)
                else:
                    temp_value = int(received_value)
            except ValueError:
                pass

            if type(received_value) == 4:  # PSTRING
                if "\n" in str(received_value):
                    temp_value = received_value.replace("\\n", "\n")
                    temp_value = received_value.replace("\r", "")
                elif '"' in str(received_value):
                    temp_value = received_value.replace('\\"', '"')
                else:
                    temp_value = received_value

            if received_value == "true":
                temp_value = True
            elif received_value == "false":
                temp_value = False

            temp_dict[received_reference] = temp_value

        configurations = temp_dict
        return configurations

    def parse_keep_alive_response(self, message):
        """
        Deserializes the message into a UTC timestamp.

        :param message: The message received
        :type message: Message
        :returns: UTC timestamp in milliseconds
        :rtype: int
        """
        bytearray_payload = bytearray(message.payload)
        payload = json.loads(bytearray_payload)
        timestamp = payload.get("value")
        return timestamp
