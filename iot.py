"""
.. module:: iot

WolkAbout IoT Platform Library
******************************

WolkAbout IoT Platform is an IoT application enablement platform that
allows users to easily and securely connect, manage, monitor and control
disparate devices, transform real-time readings into meaningful data and
combine different devices and services into
a complete IoT solution: `WolkAbout IoT Platform <https://wolkabout.com/>`_
  

"""
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
import timers

from wolkabout.iot.wolk import wolkabout_protocol_message_factory as wapmf
from wolkabout.iot.wolk import wolkabout_protocol_message_deserializer as wapmd
from wolkabout.iot.wolk import zerynth_message_queue as zmq
from wolkabout.iot.wolk import mqtt_connectivity_service as mcs
from wolkabout.iot.wolk.model import sensor_reading
from wolkabout.iot.wolk.model import alarm
from wolkabout.iot.wolk.model import actuator_status

new_exception(InterfaceNotProvided, Exception)  # noqa


@c_native("_totuple", ["csrc/tuple_ifc.c"], [])  # noqa
def tuple(mlist):  # noqa
    pass


class Device:

    def __init__(self, key, password, actuator_references=None):
        """
Device
------

The :samp:`Device` class contains all the required information for connecting
to the WolkAbout IoT Platform.

.. method:: Device(key, password, actuator_references=None)

* :samp:`key` - The device key obtained when creating the device on WolkAbout IoT platform
* :samp:`password` - The device password obtained when creating the device on WolkAbout IoT platform
* :samp:`actuator_references` - A list of actuator references defined in the device type on WolkAbout IoT Platform
        """
        self.key = key
        self.password = password
        self.actuator_references = actuator_references


# "Enum" of actuator states
ACTUATOR_STATE_READY = "READY"
ACTUATOR_STATE_BUSY = "BUSY"
ACTUATOR_STATE_ERROR = "ERROR"


class Wolk:

    def __init__(
        self,
        device,
        host="api-demo.wolkabout.com",
        port=1883,
        actuation_handler=None,
        actuator_status_provider=None,
        configuration_handler=None,
        configuration_provider=None,
        message_queue_size=100,
        keep_alive_enabled=True,
    ):
        """

Wolk
----

The :samp:`Wolk` class wraps all the functionality of the library.

.. method:: Wolk(device, host="api-demo.wolkabout.com", port=1883, actuation_handler=None, actuator_status_provider=None, configuration_handler=None, configuration_provider=None, message_queue_size=100, keep_alive_enabled=True)

* :samp:`device`: Device containing key, password and actuator references
* :samp:`host`: Address of the MQTT broker of the Platform - defaults to demo instance
* :samp:`port`: Port of the MQTT broker - defaults to demo instance's port
* :samp:`actuation_handler`: Actuation handler function, optional

    .. method:: actuation_handler(reference, value)

    Implement this function in order to execute actuation commands issued from the Platform.

    This function will try to set the actuator, identified by :samp:`reference`, to the :samp:`value` specified by the Platform.

* :samp:`actuator_status_provider`: Actuator status provider function, optional

    .. method:: actuator_status_provider(reference)

    Implement this function in order to provide information about the current status of the actuator to the Platform.

    This function will return the current actuator :samp:`state` and :samp:`value`, identified by :samp:`reference`, to the Platform.

    The possible `states` are::

        iot.ACTUATOR_STATE_READY
        iot.ACTUATOR_STATE_BUSY
        iot.ACTUATOR_STATE_ERROR

    The method should return something like this::

        return (iot.ACTUATOR_STATE_READY, value)

* :samp:`configuration_handler`: Configuration handler function, optional

    .. method:: configuration_handler(configuration)

    Implement this function in order to handle configuration commands issued from the Platform.

    This function should update device configuration with received configuration values.

        * :samp:`configuration` - Dictionary that contains reference:value pairs

* :samp:`configuration_provider`: Configuration provider function, optional

    .. method:: configuration_provider()

    Implement this function to provide information about the current configuration settings to the Platform.

    Reads current device configuration and returns it as a dictionary with device configuration reference as the key, and device configuration value as the value.

* :samp:`message_queue_size`: Number of reading to store in memory, defaults to 100
* :samp:`keep_alive_enabled`: Periodically publish keep alive message, default True

  
        """
        self.device = device
        self.message_factory = wapmf.WolkAboutProtocolMessageFactory(device.key)
        self.message_deserializer = wapmd.WolkAboutProtocolMessageDeserializer(device)
        self.message_queue = zmq.ZerynthMessageQueue(message_queue_size)
        self.connectivity_service = mcs.MQTTConnectivityService(
            device, self.message_deserializer.get_inbound_topics(), host, port
        )
        self.connectivity_service.set_inbound_message_listener(self._on_inbound_message)
        self.actuation_handler = actuation_handler
        self.actuator_status_provider = actuator_status_provider
        self.configuration_handler = configuration_handler
        self.configuration_provider = configuration_provider
        self.keep_alive_enabled = keep_alive_enabled
        self.keep_alive_service = None
        self.last_platform_timestamp = None

        if device.actuator_references and (
            actuation_handler is None or actuator_status_provider is None
        ):
            raise InterfaceNotProvided

    def connect(self):
        """
.. method:: Wolk.connect()
Connect to the Platform.


        """
        self.connectivity_service.connect()
        if self.keep_alive_enabled:
            self.keep_alive_service = timers.timer()
            self.keep_alive_service.interval(60000, self._send_keep_alive)
            self.keep_alive_service.start()

    def disconnect(self):
        """
.. method:: Wolk.disconnect()
Disconnect from the Platform.


        """
        self.connectivity_service.disconnect()
        if self.keep_alive_enabled:
            self.keep_alive_service.stop()

    def _send_keep_alive(self):
        message = self.message_factory.make_from_ping_keep_alive_message()
        self.connectivity_service.publish(message)

    def add_sensor_reading(self, reference, value, timestamp=None):
        """
.. method:: Wolk.add_sensor_reading(reference, value, timestamp=None)
Add a sensor reading into storage.

* :samp:`reference`: The reference of the sensor
* :samp:`value`: The value of the sensor reading
* :samp:`timestamp`: (optional) Unix timestamp - if not provided, Platform will assign one


        """
        reading = sensor_reading.SensorReading(reference, value, timestamp)
        message = self.message_factory.make_from_sensor_reading(reading)
        self.message_queue.put(message)

    def add_alarm(self, reference, active, timestamp=None):
        """
.. method:: Wolk.add_alarm(reference, active, timestamp=None)
Add an alarm event into storage.

* :samp:`reference`: The reference of the alarm
* :samp:`active`: Current state of the alarm
* :samp:`timestamp`: (optional) Unix timestamp - if not provided, Platform will assign one


        """
        alarm_event = alarm.Alarm(reference, active, timestamp)
        message = self.message_factory.make_from_alarm(alarm_event)
        self.message_queue.put(message)

    def publish(self):
        """
.. method:: Wolk.publish()
Publish all currently stored messages to the Platform.


        """
        while True:
            message = self.message_queue.peek()
            if message is None:
                break
            if self.connectivity_service.publish(message) is True:
                self.message_queue.get()

    def publish_actuator_status(self, reference):
        """
.. method:: Wolk.publish_actuator_status(reference)
Publish the current actuator status to the Platform.

* :samp:`reference` The reference of the actuator


        """
        if self.actuator_status_provider is None:
            return

        state, value = self.actuator_status_provider(reference)
        status = actuator_status.ActuatorStatus(reference, state, value)
        message = self.message_factory.make_from_actuator_status(status)

        if not self.connectivity_service.publish(message):
            self.message_queue.put(message)

    def publish_configuration(self):
        """
.. method:: Wolk.publish_configuration()
Publish the current device configuration to the Platform.


        """
        if self.configuration_handler is None:
            return

        configuration = self.configuration_provider()
        message = self.message_factory.make_from_configuration(configuration)
        if not self.connectivity_service.publish(message):
            self.message_queue.put(message)

    def request_timestamp(self):
        """
.. method:: Wolk.request_timestamp()
Return last received Platform timestamp.

If keep alive service is not enabled, this will always be None.

:return: UTC timestamp in milliseconds or None
:rtype: int, None
        """
        return self.last_platform_timestamp

    def _on_inbound_message(self, message):
        if self.message_deserializer.is_actuation_command(message):

            if not self.actuation_handler or not self.actuator_status_provider:
                return

            actuation = self.message_deserializer.parse_actuator_command(message)
            self.actuation_handler(actuation.reference, actuation.value)
            self.publish_actuator_status(actuation.reference)
            return

        if self.message_deserializer.is_configuration_command(message):

            if not self.configuration_provider or not self.configuration_handler:
                return

            configuration = self.message_deserializer.parse_configuration_command(
                message
            )
            self.configuration_handler(configuration)
            self.publish_configuration()
            return

        if self.message_deserializer.is_keep_alive_response(message):
            self.last_platform_timestamp = self.message_deserializer.parse_keep_alive_response(
                message
            )


# "Enum" of version number
VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_PATCH = 0
