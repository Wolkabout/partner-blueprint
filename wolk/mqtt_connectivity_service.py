"""Connectivity service based on MQTT protocol."""
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
from mqtt import mqtt

from wolkabout.iot.wolk.interface import connectivity_service
from wolkabout.iot.wolk.model import message


class MQTTConnectivityService(connectivity_service.ConnectivityService):
    """Provide connection to WolkAbout IoT Platform via MQTT."""

    def __init__(self, device, topics, host, port, qos=0):
        """
        Credentials and configuration for MQTT connection.

        :param device: Contains device key, device password and actuator references
        :type device: Device
        :param topics: List of topics to which to subscribe
        :type topics: List[str]
        :param host: Address of the WolkAbout IoT Platform instance
        :type host: str
        :param port: Port of WolkAbout IoT Platform instance
        :type port: int
        :param qos: Quality of Service for MQTT connection (0,1,2), defaults to 0
        :type qos: int
        """
        self.device = device
        self.topics = topics
        self.qos = qos
        self.host = host
        self.port = port
        self._connected = False
        self._inbound_message_listener = None
        self._client = None

    def set_inbound_message_listener(self, on_inbound_message):
        """
        Set the callback method to handle inbound messages.

        :param on_inbound_message: Method that handles inbound messages
        :type on_inbound_message: Callable[[Message], None]
        """
        self._inbound_message_listener = on_inbound_message

    def on_mqtt_message(self, client, data):
        """
        Serialize inbound messages and pass them to inbound message listener.

        :param client:  The client that received the message
        :type client:  mqtt.Client
        :param data: The message received
        :type data: dict
        """
        if "message" in data:
            topic = data["message"].topic
            payload = data["message"].payload
            received_message = message.Message(topic, payload)
            self._inbound_message_listener(received_message)

    def connect(self):
        """
        Establish connection with WolkAbout IoT platform.

        If there are actuators it will subscribe to topics that will contain
        actuator commands and also starts a loop to handle inbound messages.

        Raises an exception if the connection failed.
        """
        if self._connected:
            return

        self._client = mqtt.Client(client_id=self.device.key, clean_session=True)
        self._client.set_username_pw(self.device.key, self.device.password)
        self._client.set_will("lastwill/" + self.device.key, "Gone offline", 2, False)

        try:
            self._client.connect(self.host, keepalive=60, port=self.port)
            topics = []
            for topic in self.topics:
                topics.append([topic, 2])
            self._client.subscribe(topics)
            self._client.on(mqtt.PUBLISH, self.on_mqtt_message)
            self._client.loop()
            self._connected = True
        except Exception as e:
            raise e

    def disconnect(self):
        """Disconnect the device from the Platform."""
        if self._connected:
            self.publish(message.Message("lastwill/" + self.device.key, None))
        self._connected = False
        self._client.disconnect()

    def connected(self):
        """
        Return the current status of the connection.

        :return: current connection state
        :rtype: bool
        """
        return self._connected

    def publish(self, message):
        """
        Publish the message to WolkAbout IoT Platform.

        :param message: Message to be published
        :type message: Message
        :return: True on success, False otherwise
        :rtype: bool

        """
        self._client.publish(message.topic, message.payload, self.qos)
        return True
