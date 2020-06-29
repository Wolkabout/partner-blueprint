"""Message format used for communication with the Platform."""
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


class Message:
    """MQTT Message model."""

    def __init__(self, topic, payload):
        """
        MQTT Message identified by topic and payload.

        :param topic: Topic where the message will be published to
        :type topic: str
        :param payload: Payload of the message that will be published
        :type payload: str
        """
        self.topic = topic
        self.payload = payload
