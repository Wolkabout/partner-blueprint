"""Serialize messages to be sent to the Platform."""
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


class MessageFactory:
    """Message Factory Interface."""

    def make_from_sensor_reading(self, reading):
        """
        Serialize a sensor reading to be sent to the Platform.

        :param reading: The reading to be serialized
        :type reading: SensorReading
        :returns: message
        :rtype: Message
        """
        pass

    def make_from_alarm(self, alarm):
        """
        Serialize an alarm event to be sent to the Platform.

        :param alarm: The alarm to be serialized
        :type alarm: Alarm
        :returns: message
        :rtype: Message
        """
        pass

    def make_from_actuator_status(self, actuator):
        """
        Serialize an actuator status to be sent to the Platform.

        :param actuator: The actuator status to be serialized
        :type actuator: ActuatorStatus
        :returns: message
        :rtype: Message
        """
        pass

    def make_from_ping_keep_alive_message(self):
        """
        Serialize a keep alive message.

        :returns: message
        :rtype: Message
        """
        pass

    def make_from_configuration(self, configuration):
        """
        Serialize the device's configuration to be sent to the Platform.

        :param configuration: The device's current configuration
        :type configuration: dict
        :returns: message
        :rtype: Message
        """
        pass
