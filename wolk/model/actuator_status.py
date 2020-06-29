"""Contains the status of the Actuator."""
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


class ActuatorStatus:
    """Actuator Status class."""

    def __init__(self, reference, state, value):
        """
        State of a device actuator.

        :param reference: The reference of the actuator
        :type reference: str
        :param state: The actuators current state
        :type state: ActuatorState
        :param value: The actuators current value
        :type value: bool or int or float or string
        """
        self.reference = reference
        self.state = state
        self.value = value
