"""Means of storing messages into memory before publishing to Platform."""
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

import queue

from wolkabout.iot.wolk.interface import message_queue


class ZerynthMessageQueue(message_queue.MessageQueue):
    """Store messages before they are sent to WolkAbout IoT Platform."""

    def __init__(self, max_size):
        """
        Initialize a queue and set its maximum capacity.

        :param max_size: Number of messages to store
        :type max_size: int
        """
        self.queue = queue.Queue(maxsize=max_size)

    def put(self, message):
        """
        Add a message to the queue.

        :param mesasge: Message to store
        :type message: Message
        """
        if self.queue.full():
            return

        self.queue.put(message)

    def get(self):
        """
        Get the first message from the queue.

        :return: message
        :rtype: Message or None
        """
        if self.queue.empty():
            return None

        return self.queue.get()

    def peek(self):
        """
        Return the first message from queue without removing it from the queue.

        :return: message
        :rtype: Message or None
        """
        if self.queue.empty():
            return None

        return self.queue.peek()
