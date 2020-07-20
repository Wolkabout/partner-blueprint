"""Enables connection to WolkAbout IoT Plaftorm."""
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


class ConnectivityService:
    """Connectivity Service Interface."""

    def connect(self):
        """Attempt to establish connection to the Platform."""
        pass

    def disconnect(self):
        """Terminate connection with the Platform."""
        pass

    def connected(self):
        """
        Return current state of the connection to the Platform.

        :returns: state
        :rtype: bool
        """
        pass

    def publish(self, outbound_message):
        """
        Publish message to the Platform.

        Returns true on success, false otherwise.

        :param outbound_message: Message to send
        :type outbound_message: OutboundMessage
        :returns: success
        :rtype: bool
        """
        pass

    def set_inbound_message_listener(self, listener):
        """
        Set a callback to Wolk._on_inbound_message method.

        This callback function needs to pass back an InboundMessage object
        :param listener: inbound message listener function
        :type listener: Callable
        """
        pass
