"""Deserialize the messages received from the Platform."""
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


class MessageDeserializer:
    """Message Deserializer Interface."""

    def get_inbound_topics(self):
        """
        Return list of inbound topics for device.

        :return: List of topics to subscribe to
        :rtype: List[str]
        """
        pass

    def is_keep_alive_response(self, message):
        """
        Check if message is keep alive response.

        :param message: The message received
        :type message: Message
        :returns: keep_alive_response
        :rtype: bool
        """
        pass

    def is_actuation_command(self, message):
        """
        Check if message is actuation command.

        :param message: The message received
        :type message: Message
        :returns: actuation_command
        :rtype: bool
        """
        pass

    def is_configuration_command(self, message):
        """
        Check if message is configuration command.

        :param message: The message received
        :type message: Message
        :returns: configuration
        :rtype: bool
        """
        pass

    def parse_actuator_command(self, message):
        """
        Deserialize the message into an ActuatorCommand.

        :param message: The message received
        :type message: Message
        :returns: actuation
        :rtype: ActuatorCommand
        """
        pass

    def parse_configuration_command(self, message):
        """
        Deserialize the message into configurations.

        :param message: The message received
        :type message: Message
        :returns: configurations
        :rtype: dict
        """
        pass

    def parse_keep_alive_response(self, message):
        """
        Deserializes the message into a UTC timestamp.

        :param message: The message received
        :type message: Message
        :returns: UTC timestamp in milliseconds
        :rtype: int
        """
        pass
