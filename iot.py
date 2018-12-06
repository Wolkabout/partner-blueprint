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

"""
.. module:: iot

******************************
WolkAbout IoT Platform Library
******************************

WolkAbout Python Connector library for connecting Zerynth devices to `WolkAbout IoT Platform <https://wolkabout.com/>`_.
The `Wolk` class depends upon interfaces, making it possible to provide different implementations.
The section `Dependencies` contains the documentation of the default implementations, followed by the `Wolk` section that
contains everything necessary to connect and publish data to the WolkAbout IoT Platform.
    

"""

from mqtt import mqtt
import json
import queue
import timers

from wolkabout.iot.WolkCore import ActuatorCommand
from wolkabout.iot.WolkCore import ActuatorCommandType
from wolkabout.iot.WolkCore import ActuatorState
from wolkabout.iot.WolkCore import ConfigurationCommand
from wolkabout.iot.WolkCore import ConfigurationCommandType
from wolkabout.iot.WolkCore import ConnectivityService
from wolkabout.iot.WolkCore import FirmwareErrorType
from wolkabout.iot.WolkCore import FirmwareStatusType
from wolkabout.iot.WolkCore import InboundMessage
from wolkabout.iot.WolkCore import InboundMessageDeserializer
from wolkabout.iot.WolkCore import KeepAliveService
from wolkabout.iot.WolkCore import OutboundMessage
from wolkabout.iot.WolkCore import OutboundMessageFactory
from wolkabout.iot.WolkCore import OutboundMessageQueue
from wolkabout.iot.WolkCore import WolkCore


new_exception(InterfaceNotProvided, Exception)


@c_native("_totuple", ["csrc/tuple_ifc.c"], [])
def tuple(mlist):
    pass


debug_mode = False


def print_d(*args):
    if debug_mode:
        print(*args)


class ZerynthMQTTConnectivityService(ConnectivityService.ConnectivityService):
    """

============
Dependencies
============

The following classes are implementations of interfaces on which the Wolk class depends

-------------------------
MQTT Connectivity Service
-------------------------


.. class:: ZerynthMQTTConnectivityService(ConnectivityService.ConnectivityService)

This class provides the connection to the WolkAbout IoT Platform by implementing the :samp:`ConnectivityService` interface

* :samp:`device`: Contains device key, device password and actuator references
* :samp:`host`: Address of the WolkAbout IoT Platform instance
* :samp:`port`: Port of WolkAbout IoT Platform instance
* :samp:`qos`: Quality of Service for MQTT connection (0,1,2), defaults to 0

    """

    def __init__(self, device, host, port, qos=0):
        print_d("[D] Connectivity details:")
        print_d("[D] Device key - " + str(device.key))
        print_d("[D] Device password - " + str(device.password))
        print_d("[D] Host - " + str(host))
        print_d("[D] Port - " + str(port))
        print_d("[D] Quality of Service - " + str(qos))
        self.device = device
        self.qos = qos
        self.host = host
        self.port = port
        self.connected = False
        self.inbound_message_listener = None
        self.client = None

    def set_inbound_message_listener(self, on_inbound_message):
        """
.. method:: set_inbound_message_listener(on_inbound_message)

Sets the callback method to handle inbound messages

* :samp:`on_inbound_message`:  The method that handles inbound messages
        """
        self.inbound_message_listener = on_inbound_message

    def on_mqtt_message(self, client, data):
        """
.. method:: on_mqtt_message(client, data)

Method that serializes inbound messages and passes them to the inbound message listener

* :samp:`client`:  The client that received the message
* :samp:`data`: The message received
        """
        if "message" in data:
            channel = data["message"].topic
            payload = data["message"].payload
            print_d(
                "[D] Received message - Channel: " + channel + " Payload: " + payload
            )
            message = InboundMessage.InboundMessage(channel, payload)
            self.inbound_message_listener(message)

    def connect(self):
        """
.. method:: connect()

This method establishes the connection to the WolkAbout IoT platform.
If there are actuators it will subscribe to topics that will contain actuator commands and also starts a loop to handle inbound messages.
Raises an exception if the connection failed.

        """
        if self.connected:
            return

        self.client = mqtt.Client(client_id=self.device.key, clean_session=True)
        self.client.set_username_pw(self.device.key, self.device.password)
        self.client.set_will("lastwill/" + self.device.key, "Gone offline", 2, False)

        try:
            self.client.connect(self.host, keepalive=60, port=self.port)
            self.topics = []
            self.topics.append(["service/commands/firmware/" + self.device.key, 0])
            self.topics.append(["service/commands/file/" + self.device.key, 0])
            self.topics.append(["service/commands/url/" + self.device.key, 0])
            self.topics.append(["service/binary/" + self.device.key, 0])
            self.topics.append(["pong/" + self.device.key, 0])
            self.topics.append(["configurations/commands/" + self.device.key, 0])
            if self.device.actuator_references:
                for actuator_reference in self.device.actuator_references:
                    topic = [
                        "actuators/commands/"
                        + self.device.key
                        + "/"
                        + actuator_reference,
                        self.qos,
                    ]
                    self.topics.append(topic)
            self.client.subscribe(self.topics)
            self.client.on(mqtt.PUBLISH, self.on_mqtt_message)
            self.client.loop()
            self.connected = True
        except Exception as e:
            raise e

    def disconnect(self):
        """
.. method:: disconnect()

Disconnects the device from the WolkAbout IoT Platform

        """
        self.connected = False
        self.client.disconnect()

    def connected(self):
        """
.. method:: connected()

Returns the current status of the connection

        """
        return self.connected

    def publish(self, outbound_message):
        """
.. method:: publish(outbound_message)

Publishes the :samp:`outbound_message` to the WolkAbout IoT Platform

        """
        print_d(
            "[D] Publishing message - Channel: "
            + outbound_message.channel
            + " Payload: "
            + str(outbound_message.payload)
        )
        self.client.publish(
            outbound_message.channel, outbound_message.payload, self.qos
        )
        return True


class ZerynthOutboundMessageQueue(OutboundMessageQueue.OutboundMessageQueue):
    """

----------------------
Outbound Message Queue
----------------------


.. class:: ZerynthOutboundMessageQueue(OutboundMessageQueue.OutboundMessageQueue)

This class provides the means of storing messages before they are sent to the WolkAbout IoT Platform.

* :samp:`maxsize`: Int - The maximum size of the queue, effectively limiting the number of messages to persist in memory

    """

    def __init__(self, maxsize):
        print_d("[D] Initialized queue with max size of " + str(maxsize))
        self.queue = queue.Queue(maxsize=maxsize)

    def put(self, message):
        """
.. method:: put(message)

Adds the :samp:`message` to :samp:`self.queue`

        """
        if self.queue.full():
            return

        self.queue.put(message)

    def get(self):
        """
.. method:: get()

Takes the first :samp:`message` from :samp:`self.queue`

        """
        if self.queue.empty():
            return None

        return self.queue.get()

    def peek(self):
        """
.. method:: peek()

Returns the first :samp:`message` from :samp:`self.queue` without removing it from the queue

        """
        if self.queue.empty():
            return None

        return self.queue.peek()


class ZerynthOutboundMessageFactory(OutboundMessageFactory.OutboundMessageFactory):
    """

------------------------
Outbound Message Factory
------------------------

.. class:: ZerynthOutboundMessageFactory(OutboundMessageFactory.OutboundMessageFactory)

This class serializes sensor readings, alarms and actuator statuses so that they can be properly sent to the WolkAbout IoT Platform

* :samp:`device_key` - The key used to serialize messages
    """

    def __init__(self, device_key):
        self.device_key = device_key

    def make_from_sensor_reading(self, reading):
        """
.. method:: make_from_sensor_reading(reading)

Serializes the :samp:`reading` to be sent to the WolkAbout IoT Platform

* :samp:`reading`: Sensor reading to be serialized
        """
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

        if reading.timestamp is None:
            return OutboundMessage.OutboundMessage(
                "readings/" + self.device_key + "/" + reading.reference,
                '{ "data" : "' + str(reading.value) + '" }',
            )
        else:
            return OutboundMessage.OutboundMessage(
                "readings/" + self.device_key + "/" + reading.reference,
                '{ "utc" : "'
                + str(reading.timestamp)
                + '", "data" : "'
                + str(reading.value)
                + '" }',
            )

    def make_from_alarm(self, alarm):
        """
.. method:: make_from_alarm(alarm)

Serializes the :samp:`alarm` to be sent to the WolkAbout IoT Platform

* :samp:`alarm`: Alarm event to be serialized
        """
        if alarm.active is True:
            alarm.active = "true"
        elif alarm.active is False:
            alarm.active = "false"
        if alarm.timestamp is None:
            return OutboundMessage.OutboundMessage(
                "events/" + self.device_key + "/" + alarm.reference,
                '{ "data" : "' + str(alarm.active) + '" }',
            )
        else:
            return OutboundMessage.OutboundMessage(
                "events/" + self.device_key + "/" + alarm.reference,
                '{ "utc" : "'
                + str(alarm.timestamp)
                + '", "data" : "'
                + str(alarm.active)
                + '" }',
            )

    def make_from_actuator_status(self, actuator):
        """
.. method:: make_from_actuator_status(actuator)

Serializes the :samp:`actuator` to be sent to the WolkAbout IoT Platform

* :samp:`actuator`: Actuator status to be serialized
        """
        if actuator.state == ActuatorState.ACTUATOR_STATE_READY:
            actuator.state = "READY"
        elif actuator.state == ActuatorState.ACTUATOR_STATE_BUSY:
            actuator.state = "BUSY"
        elif actuator.state == ActuatorState.ACTUATOR_STATE_ERROR:
            actuator.state = "ERROR"

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

        return OutboundMessage.OutboundMessage(
            "actuators/status/" + self.device_key + "/" + actuator.reference,
            '{ "status" : "'
            + actuator.state
            + '" , "value" : "'
            + str(actuator.value)
            + '" }',
        )

    def make_from_firmware_status(self, firmware_status):
        """
.. method:: make_from_firmware_status(self, firmware_status)

Serializes the current :samp:`firmware_status` to be sent to the WolkAbout IoT Platform

* :samp:`firmware_status`: Firmware status to be serialized

        """
        if firmware_status.status == FirmwareStatusType.FIRMWARE_STATUS_FILE_TRANSFER:
            firmware_status.status = "FILE_TRANSFER"

        elif firmware_status.status == FirmwareStatusType.FIRMWARE_STATUS_FILE_READY:
            firmware_status.status = "FILE_READY"

        elif firmware_status.status == FirmwareStatusType.FIRMWARE_STATUS_INSTALLATION:
            firmware_status.status = "INSTALLATION"

        elif firmware_status.status == FirmwareStatusType.FIRMWARE_STATUS_COMPLETED:
            firmware_status.status = "COMPLETED"

        elif firmware_status.status == FirmwareStatusType.FIRMWARE_STATUS_ABORTED:
            firmware_status.status = "ABORTED"

        elif firmware_status.status == FirmwareStatusType.FIRMWARE_STATUS_ERROR:
            firmware_status.status = "ERROR"

        if firmware_status.status == "ERROR":

            if (
                firmware_status.error
                == FirmwareErrorType.FIRMWARE_ERROR_UNSPECIFIED_ERROR
            ):
                firmware_status.error = "0"

            elif (
                firmware_status.error
                == FirmwareErrorType.FIRMWARE_ERROR_FILE_UPLOAD_DISABLED
            ):
                firmware_status.error = "1"

            elif (
                firmware_status.error
                == FirmwareErrorType.FIRMWARE_ERROR_UNSUPPORTED_FILE_SIZE
            ):
                firmware_status.error = "2"

            elif (
                firmware_status.error
                == FirmwareErrorType.FIRMWARE_ERROR_INSTALLATION_FAILED
            ):
                firmware_status.error = "3"

            elif (
                firmware_status.error == FirmwareErrorType.FIRMWARE_ERROR_MALFORMED_URL
            ):
                firmware_status.error = "4"

            elif (
                firmware_status.error
                == FirmwareErrorType.FIRMWARE_ERROR_FILE_SYSTEM_ERROR
            ):
                firmware_status.error = "5"

            elif (
                firmware_status.error
                == FirmwareErrorType.FIRMWARE_ERROR_RETRY_COUNT_EXCEEDED
            ):
                firmware_status.error = "10"

        if firmware_status.error:

            message = OutboundMessage.OutboundMessage(
                "service/status/firmware/" + self.device_key,
                '{"status" : "'
                + firmware_status.status
                + '", "error" : '
                + firmware_status.error
                + "}",
            )
            return message
        else:

            message = OutboundMessage.OutboundMessage(
                "service/status/firmware/" + self.device_key,
                '{"status" : "' + firmware_status.status + '"}',
            )
            return message

    def make_from_keep_alive_message(self):
        """
.. method:: make_from_keep_alive_message()

Pings the platform to keep the device connected
        """
        return OutboundMessage.OutboundMessage("ping/" + self.device_key, None)

    def make_from_configuration(self, configuration):
        """
.. method:: make_from_configuration(self, configuration)

Serializes the device's configuration to be sent to the platform

* :samp:`configuration`: Configuration to be serialized
        """
        values = str()

        for reference, value in configuration.items():

            if type(value) == 10:  # PTUPLE
                delimiter = ","

                values_list = []

                for single_value in value:
                    if single_value is True:
                        single_value = "true"
                    elif single_value is False:
                        single_value = "false"
                    if "\n" in str(single_value):
                        single_value = single_value.replace("\n", "\\n")
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
                value = string_values

            else:

                if "\n" in str(value):
                    value = value.replace("\n", "\\n")
                    value = value.replace("\\\\n", "\\n")
                    value = value.replace("\r", "")
                if '"' in str(value):
                    value = value.replace('"', '\\"')
                    value = value.replace('\\\\"', '\\"')
                if value is True:
                    value = "true"
                elif value is False:
                    value = "false"

            values += '"' + reference + '":"' + str(value) + '",'

        values = values[:-1]

        message = OutboundMessage.OutboundMessage(
            "configurations/current/" + self.device_key, '{"values":{' + values + "}}"
        )
        return message


class ZerynthInboundMessageDeserializer(
    InboundMessageDeserializer.InboundMessageDeserializer
):
    """

-----------------------
Inbound Message Factory
-----------------------

.. class:: ZerynthInboundMessageDeserializer(InboundMessageDeserializer.InboundMessageDeserializer)

This class deserializes messages that the device receives from the WolkAbout IoT Platform from the topics it is subscribed to.

    """

    def deserialize_actuator_command(self, message):
        """
.. method:: deserialize_actuator_command(message)

Deserializes the :samp:`message` that was received from the WolkAbout IoT Platform

* :samp:`message`: The message to be deserialized
        """
        reference = message.channel.split("/")[-1]
        bytearray_payload = bytearray(message.payload)
        payload = json.loads(bytearray_payload)
        command = payload.get("command")
        if str(command) == "SET":
            command_type = ActuatorCommandType.ACTUATOR_COMMAND_TYPE_SET
            value = payload.get("value")
            if "\\n" in str(value):
                value = value.replace("\\n", "\n")
                value = value.replace("\r", "")
            if '\\"' in str(value):
                value = value.replace('\\"', '"')
            if value == "true":
                value = True
            elif value == "false":
                value = False
            actuation = ActuatorCommand.ActuatorCommand(reference, command_type, value)
            return actuation
        elif str(command) == "STATUS":
            command_type = ActuatorCommandType.ACTUATOR_COMMAND_TYPE_STATUS
            actuation = ActuatorCommand.ActuatorCommand(reference, command_type)
            return actuation
        else:
            command_type = ActuatorCommandType.ACTUATOR_COMMAND_TYPE_UNKNOWN
            actuation = ActuatorCommand.ActuatorCommand(reference, command_type)
            return actuation

    def deserialize_configuration_command(self, message):
        """
.. method:: deserialize_configuration_command(message)

Deserializes the :samp:`message` that was received from the WolkAbout IoT Platform

* :samp:`message` The message to be deserialized
        """
        bytearray_payload = bytearray(message.payload)
        payload = json.loads(bytearray_payload)
        command = payload.get("command")

        if command == "SET":

            command = ConfigurationCommandType.CONFIGURATION_COMMAND_TYPE_SET

            configuration = ConfigurationCommand.ConfigurationCommand(
                command, payload.get("values")
            )

            temp_dict = dict()

            for (received_reference, received_value) in configuration.values.items():
                try:
                    if "." in received_value:
                        temp_value = float(received_value)
                    else:
                        temp_value = int(received_value)
                except ValueError:
                    pass

                if type(received_value) == 4:  # PSTRING
                    if "," in str(received_value):
                        values_list = received_value.split(",")
                        for value in values_list:
                            if "\\n" in str(value):
                                value = value.replace("\\n", "\n")
                                value = value.replace("\r", "")
                            if '\\"' in str(value):
                                value = value.replace('\\"', '"')
                            if value == "true":
                                value = True
                            elif value == "false":
                                value = False
                            try:
                                if "." in value:
                                    value = float(value)
                                else:
                                    value = int(value)
                            except ValueError:
                                pass
                        temp_value = tuple(values_list)
                    else:
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

            configuration.values = temp_dict
            return configuration

        elif command == "CURRENT":

            command = ConfigurationCommandType.CONFIGURATION_COMMAND_TYPE_CURRENT

            configuration = ConfigurationCommand.ConfigurationCommand(command)
            return configuration

        else:

            command = ConfigurationCommandType.CONFIGURATION_COMMAND_TYPE_UNKNOWN

            configuration = ConfigurationCommand.ConfigurationCommand(command)
            return configuration


class ZerynthKeepAliveService(KeepAliveService.KeepAliveService):
    """

------------------
Keep Alive Service
------------------

.. class:: ZerynthKeepAliveService(KeepAliveService.KeepAliveService)

This class will send messages to the platform in regular intervals to keep the device connected
in cases where no data is being sent by the device for over 30 minutes.

* :samp:`connectivity_service`: Connectivity service used to publish keep alive messages
* :samp:`outbound_message_factory`: Outbound message factory used to create keep alive messages
* :samp:`interval`:  The number of milliseconds between each keep alive message
    """

    def __init__(self, connectivity_service, outbound_message_factory, interval):
        self.connectivity_service = connectivity_service
        self.outbound_message_factory = outbound_message_factory
        self.interval = interval
        self.timer = None

    def handle_pong(self):
        """
.. method:: handle_pong()

Handles the keep alive response message received from the platform
        """
        pass

    def start(self):
        """
.. method:: start()

Sends a keep alive message as soon as the device is connected to the platform
and starts a repeating timer to send subsequent keep alive messages every `self.interval` milliseconds
        """
        print_d(
            "[D] Initialized keep alive service with interval of "
            + str(self.interval)
            + " milliseconds"
        )
        self.timer = timers.timer()
        self.timer.interval(self.interval, self.send_keep_alive)
        self.timer.start()

    def stop(self):
        """
.. method:: stop()

Stops the repeating timer
        """
        self.timer.destroy()

    def send_keep_alive(self):
        """
.. method:: send_keep_alive()

Creates a keep alive message from the outbound message factory and publishes it using the connectivity service
        """
        message = self.outbound_message_factory.make_from_keep_alive_message()
        self.connectivity_service.publish(message)


class Wolk:
    """
==========
Wolk class
==========

.. class:: Wolk

This class is a wrapper for the WolkCore class that passes the Zerynth compatible implementation of interfaces to the constructor

* :samp:`device`: Contains device key and password, and actuator references
* :samp:`host`: The address of the WolkAbout IoT Platform, defaults to the Demo instance
* :samp:`port`: The port to which to send messages, defaults to 1883
* :samp:`actuation_handler`: Implementation of the :samp:`ActuationHandler` interface
* :samp:`actuator_status_provider`: Implementation of the :samp:`ActuatorStatusProvider` interface
* :samp:`outbound_message_queue`: Implementation of the :samp:`OutboundMessageQueue` interface
* :samp:`configuration_handler`: Implementation of the :samp:`ConfigurationHandler` interface
* :samp:`configuration_provider`: Implementation of the :samp:`ConfigurationProvider` interface
* :samp:`keep_alive_enabled`: Service that sends ping message to platform

    """

    def __init__(
        self,
        device,
        host="api-demo.wolkabout.com",
        port=1883,
        actuation_handler=None,
        actuator_status_provider=None,
        outbound_message_queue=ZerynthOutboundMessageQueue(100),
        configuration_handler=None,
        configuration_provider=None,
        keep_alive_enabled=True,
    ):
        self.device = device
        self.outbound_message_factory = ZerynthOutboundMessageFactory(device.key)
        self.outbound_message_queue = outbound_message_queue
        self.connectivity_service = ZerynthMQTTConnectivityService(device, host, port)
        self.deserializer = ZerynthInboundMessageDeserializer()
        if device.actuator_references and (
            actuation_handler is None or actuator_status_provider is None
        ):
            raise InterfaceNotProvided

        self.keep_alive_service = None
        if keep_alive_enabled:
            keep_alive_interval_milliseconds = 30000
            self.keep_alive_service = ZerynthKeepAliveService(
                self.connectivity_service,
                self.outbound_message_factory,
                keep_alive_interval_milliseconds,
            )

        try:
            self._wolk = WolkCore.WolkCore(
                self.outbound_message_factory,
                self.outbound_message_queue,
                self.connectivity_service,
                actuation_handler,
                actuator_status_provider,
                self.deserializer,
                configuration_handler,
                configuration_provider,
                self.keep_alive_service,
                None,
            )
        except Exception as e:
            raise e

    def connect(self):
        """
.. method:: connect()

Connects the device to the WolkAbout IoT Platform by calling the provided connectivity_service's :samp:`connect` method

        """
        try:
            self._wolk.connect()
        except Exception as e:
            raise e

    def disconnect(self):
        """
.. method:: disconnect()

Disconnects the device from the WolkAbout IoT Platform by calling the provided connectivity_service's :samp:`disconnect` method

        """
        self._wolk.disconnect()

    def add_sensor_reading(self, reference, value, timestamp=None):
        """
.. method:: add_sensor_reading(reference, value, timestamp=None)

Publish a sensor reading to the platform

* :samp:`reference`: String - The reference of the sensor
* :samp:`value`: Int, Float - The value of the sensor reading
* :samp:`timestamp`: (optional) Unix timestamp - if not provided, platform will assign one upon reception
        """
        self._wolk.add_sensor_reading(reference, value, timestamp)

    def add_alarm(self, reference, active, timestamp=None):
        """
.. method:: add_alarm(reference, active, timestamp=None)

Publish an alarm to the platform

* :samp:`reference`: String - The reference of the alarm
* :samp:`active`: Bool - Current state of the alarm
* :samp:`timestamp`: (optional) Unix timestamp - if not provided, platform will assign one upon reception
        """
        self._wolk.add_alarm(reference, active, timestamp)

    def publish(self):
        """
.. method:: publish()

Publishes all currently stored messages and current actuator statuses to the platform
        """
        self._wolk.publish()

    def publish_actuator_status(self, reference):
        """
.. method:: publish_actuator_status(reference)

Publish the current actuator status to the platform

* :samp:`reference`: String - The reference of the actuator
        """
        self._wolk.publish_actuator_status(reference)

    def _on_inbound_message(self, message):
        """
.. method:: _on_inbound_message(message)

Callback method to handle inbound messages

.. note:: Pass this method to the implementation of :samp:`ConnectivityService` interface

* :samp:`message`: The message received from the platform
        """
        self._wolk._on_inbound_message(message)

    def publish_configuration(self):
        """
.. method:: publish_configuration()

Publishes the current device configuration to the platform

        """
        self._wolk.publish_configuration()


class Device:
    """

------
Device
------


.. class:: Device

    The :samp:`Device` class contains all the required information for connecting to the WolkAbout IoT Platform.

    * :samp:`key` - The device key obtained when creating the device on WolkAbout IoT platform
    * :samp:`password` - The device password obtained when creating the device on WolkAbout IoT platform
    * :samp:`actuator_references` - A list of actuator references defined on in the device manifest on WolkAbout IoT Platform

    """

    def __init__(self, key, password, actuator_references=None):
        self.key = key
        self.password = password
        self.actuator_references = actuator_references


class ActuationHandler:
    """

-----------------
Actuation Handler
-----------------

.. class:: ActuationHandler

    This interface must be implemented in order to execute actuation commands issued from WolkAbout IoT Platform.

.. method:: handle_actuation(reference, value)

    This method will try to set the actuator, identified by :samp:`reference`, to the :samp:`value` specified by WolkAbout IoT Platform

    """

    def handle_actuation(self, reference, value):
        pass


class ActuatorStatusProvider:
    """

------------------------
Actuator Status Provider
------------------------

.. class:: ActuatorStatusProvider


    This interface must be implemented in order to provide information about the current status of the actuator to the WolkAbout IoT Platform


.. method:: get_actuator_status(reference)


    This method will return the current actuator :samp:`state` and :samp:`value`, identified by :samp:`reference`, to the WolkAbout IoT Platform.
    The possible `states` are::

        iot.ACTUATOR_STATE_READY
        iot.ACTUATOR_STATE_BUSY
        iot.ACTUATOR_STATE_ERROR

    The method should return something like this::

        return (iot.ACTUATOR_STATE_READY, value)

    """

    def get_actuator_status(self, reference):
        pass


class ConfigurationHandler:
    """

---------------------
Configuration Handler
---------------------

.. class:: ConfigurationHandler

    This interface must be implemented in order to handle configuration commands issued from WolkAbout IoT Platform

.. method:: handle_configuration(configuration)

    This method should update device configuration with received configuration values.

     * :samp:`configuration` - Dictionary that containes reference:value pairs

    """

    def handle_configuration(self, configuration):
        pass


class ConfigurationProvider:
    """

----------------------
Configuration Provider
----------------------

.. class:: ConfigurationProvider

    This interface must be implemented to provide information about the current configuration settings to the WolkAbout IoT Platform

.. method:: get_configuration()

    Reads current device configuration and returns it as a dictionary with device configuration reference as the key, and device configuration value as the value.
    """

    def get_configuration(self):
        pass


# "Enum" of actuator states
ACTUATOR_STATE_READY = 0
ACTUATOR_STATE_BUSY = 1
ACTUATOR_STATE_ERROR = 2

# "Enum" of version number
VERSION_MAJOR = 1
VERSION_MINOR = 1
VERSION_PATCH = 0
