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

from wolkabout.iot.WolkCore import SensorReading
from wolkabout.iot.WolkCore import Alarm
from wolkabout.iot.WolkCore import ActuatorCommandType
from wolkabout.iot.WolkCore import ActuatorStatus
from wolkabout.iot.WolkCore import ConfigurationCommandType
from wolkabout.iot.WolkCore import FirmwareCommandType
from wolkabout.iot.WolkCore import FirmwareStatus
from wolkabout.iot.WolkCore import FirmwareStatusType
from wolkabout.iot.WolkCore import FirmwareErrorType

"""
    WolkCore Class
"""


class WolkCore:
    """
        WolkCore Class
    """

    def __init__(
        self,
        outbound_message_factory,
        outbound_message_queue,
        connectivity_service,
        actuation_handler,
        actuator_status_provider,
        inbound_message_deserializer,
        configuration_handler,
        configuration_provider,
        keep_alive_service=None,
        firmware_update=None,
    ):
        """
        :param outbound_message_factory: Implementation of the OutboundMessageFactory interface
        :type outbound_message_factory: OutboundMessageFactory
        :param outbound_message_queue: Implementation of the OutboundMessageQueue interface
        :type outbound_message_queue: OutboundMessageQueue
        :param connectivity_service: Implementation of the ConnectivityService interface
        :type connectivity_service: ConnectivityService
        :param actuation_handler: Implementation of the ActuationHandler interface
        :type actuation_handler: ActuationHandler
        :param actuator_status_provider: Implementation of the ActuatorStatusProvider interface
        :type actuator_status_provider: ActuatorStatusProvider
        :param inbound_message_deserializer: Implementation of the InboundMessageDeserializer interface
        :type inbound_message_deserializer: InboundMessageDeserializer
        :param configuration_handler: Implementation of the ConfigurationHandler interface
        :type configuration_handler: ConfigurationHandler
        :param configuration_provider: Implementation of the ConfigurationProvider interface
        :type configuration_provider: ConfigurationProvider
        :param keep_alive_service: Implementation of the KeepAliveService interface
        :type keep_alive_service: KeepAliveService
        :param firmware_update: Implementation of the FirmwareUpdate interface
        :type firmware_update: FirmwareUpdate
        """

        self.outbound_message_factory = outbound_message_factory
        self.outbound_message_queue = outbound_message_queue
        self.connectivity_service = connectivity_service
        self.inbound_message_deserializer = inbound_message_deserializer
        self.actuation_handler = actuation_handler
        self.actuator_status_provider = actuator_status_provider
        self.configuration_handler = configuration_handler
        self.configuration_provider = configuration_provider
        self.connectivity_service.set_inbound_message_listener(self._on_inbound_message)

        self.keep_alive_service = None

        if keep_alive_service:
            self.keep_alive_service = keep_alive_service

        self.firmware_update = firmware_update

        if self.firmware_update:

            self.firmware_update.set_on_file_packet_request_callback(
                self._on_packet_request
            )
            self.firmware_update.set_on_status_callback(self._on_status)

    def connect(self):
        """
        Connects to the platform and starts the keep alive service if it is enabled
        """
        self.connectivity_service.connect()
        if self.keep_alive_service:
            self.keep_alive_service.start()

    def disconnect(self):
        """
        Disconnects from the platform and stops the keep alive service if it is enabled
        """
        self.connectivity_service.disconnect()
        if self.keep_alive_service:
            self.keep_alive_service.stop()

    def add_sensor_reading(self, reference, value, timestamp=None):
        """
        Publish a sensor reading to the platform
        :param reference: The reference of the sensor
        :type reference: str
        :param value: The value of the sensor reading
        :type value: int, float, str
        :param timestamp: (optional) Unix timestamp - if not provided, platform will assign one upon reception
        :type timestamp: int
        """
        reading = SensorReading.SensorReading(reference, value, timestamp)
        outbound_message = self.outbound_message_factory.make_from_sensor_reading(
            reading
        )
        self.outbound_message_queue.put(outbound_message)

    def add_alarm(self, reference, active, timestamp=None):
        """
        Publish an alarm to the platform
        :param reference: The reference of the alarm
        :type reference: str
        :param active: Current state of the alarm
        :type active: bool
        :param timestamp: (optional) Unix timestamp - if not provided, platform will assign one upon reception
        :type timestamp: int
        """
        alarm = Alarm.Alarm(reference, active, timestamp)
        outbound_message = self.outbound_message_factory.make_from_alarm(alarm)
        self.outbound_message_queue.put(outbound_message)

    def publish(self):
        """
        Publishes all currently stored messages to the platform
        """
        while True:
            outbound_message = self.outbound_message_queue.peek()

            if outbound_message is None:

                break

            if self.connectivity_service.publish(outbound_message) is True:

                self.outbound_message_queue.get()

            else:

                break

    def publish_actuator_status(self, reference):
        """
        Publish the current actuator status to the platform
        :param reference: The reference of the actuator
        :type reference: str
        """
        state, value = self.actuator_status_provider.get_actuator_status(reference)
        actuator_status = ActuatorStatus.ActuatorStatus(reference, state, value)
        outbound_message = self.outbound_message_factory.make_from_actuator_status(
            actuator_status
        )

        if not self.connectivity_service.publish(outbound_message):
            self.outbound_message_queue.put(outbound_message)

    def publish_configuration(self):
        """
        Publish the current device configuration to the platform
        """
        configuration = self.configuration_provider.get_configuration()
        outbound_message = self.outbound_message_factory.make_from_configuration(
            configuration
        )

        if not self.connectivity_service.publish(outbound_message):
            self.outbound_message_queue.put(outbound_message)

    def _on_inbound_message(self, message):
        """
        Callback function to handle inbound messages
        .. note:: Pass this function to the implementation of ConnectivityService
        :param message:  The message received from the platform
        :type message: InboundMessage
        """
        if message.channel.startswith("p2d/actuator"):

            if not self.actuation_handler or not self.actuator_status_provider:
                return

            actuation = self.inbound_message_deserializer.deserialize_actuator_command(
                message
            )

            if actuation.command == ActuatorCommandType.ACTUATOR_COMMAND_TYPE_SET:

                self.actuation_handler.handle_actuation(
                    actuation.reference, actuation.value
                )

                self.publish_actuator_status(actuation.reference)

            elif actuation.command == ActuatorCommandType.ACTUATOR_COMMAND_TYPE_STATUS:

                self.publish_actuator_status(actuation.reference)

        elif message.channel.startswith("p2d/configuration"):

            if not self.configuration_provider or not self.configuration_handler:
                return

            configuration = self.inbound_message_deserializer.deserialize_configuration_command(
                message
            )

            if (
                configuration.command
                == ConfigurationCommandType.CONFIGURATION_COMMAND_TYPE_SET
            ):
                self.configuration_handler.handle_configuration(configuration.values)
                self.publish_configuration()

            elif (
                configuration.command
                == ConfigurationCommandType.CONFIGURATION_COMMAND_TYPE_CURRENT
            ):
                self.publish_configuration()

        elif message.channel.startswith("service/commands/firmware/"):

            if not self.firmware_update:
                # Firmware update disabled
                firmware_status = FirmwareStatus.FirmwareStatus(
                    FirmwareStatusType.FIRMWARE_STATUS_ERROR,
                    FirmwareErrorType.FIRMWARE_ERROR_FILE_UPLOAD_DISABLED,
                )
                outbound_message = self.outbound_message_factory.make_from_firmware_status(
                    firmware_status
                )
                if not self.connectivity_service.publish(outbound_message):
                    self.outbound_message_queue.put(outbound_message)
                return

            firmware_command = self.inbound_message_deserializer.deserialize_firmware_command(
                message
            )

            if (
                firmware_command.command
                == FirmwareCommandType.FIRMWARE_COMMAND_TYPE_FILE_UPLOAD
            ):

                self.firmware_update.handle_file_upload(firmware_command)

            elif (
                firmware_command.command
                == FirmwareCommandType.FIRMWARE_COMMAND_TYPE_URL_DOWNLOAD
            ):

                self.firmware_update.handle_url_download(firmware_command)

            elif (
                firmware_command.command
                == FirmwareCommandType.FIRMWARE_COMMAND_TYPE_INSTALL
            ):

                self.firmware_update.handle_install()

            elif (
                firmware_command.command
                == FirmwareCommandType.FIRMWARE_COMMAND_TYPE_ABORT
            ):

                self.firmware_update.handle_abort()

            elif (
                firmware_command.command
                == FirmwareCommandType.FIRMWARE_COMMAND_TYPE_UNKNOWN
            ):
                pass

        elif message.channel.startswith("service/binary/"):

            if not self.firmware_update:
                # Firmware update disabled
                firmware_status = FirmwareStatus.FirmwareStatus(
                    FirmwareStatusType.FIRMWARE_STATUS_ERROR,
                    FirmwareErrorType.FIRMWARE_ERROR_FILE_UPLOAD_DISABLED,
                )
                outbound_message = self.outbound_message_factory.make_from_firmware_status(
                    firmware_status
                )
                if not self.connectivity_service.publish(outbound_message):
                    self.outbound_message_queue.put(outbound_message)
                return

            packet = self.inbound_message_deserializer.deserialize_firmware_chunk(
                message
            )
            self.firmware_update.handle_packet(packet)

    def _on_packet_request(self, file_name, chunk_index, chunk_size):
        """
        """
        message = self.outbound_message_factory.make_from_chunk_request(
            file_name, chunk_index, chunk_size
        )
        if not self.connectivity_service.publish(message):
            self.outbound_message_queue.put(message)

    def _on_status(self, status):
        """
        """
        message = self.outbound_message_factory.make_from_firmware_status(status)
        if not self.connectivity_service.publish(message):
            self.outbound_message_queue.put(message)
