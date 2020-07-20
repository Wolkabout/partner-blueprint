"""Provide means of reading device's current actuator state."""
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


def get_actuator_status(reference):
    """
    Read the status of actuator from the device.

    Possible states are:
    iot.ACTUATOR_STATE_READY,
    iot.ACTUATOR_STATE_BUSY,
    iot.ACTUATOR_STATE_ERROR

    Returns it as a tuple containing the state and current value.
    Must be implemented as non blocking.
    Must be implemented as thread safe.

    :param reference: The actuator reference
    :type reference: str
    :returns: (state, value)
    :rtype: (state, bool or float or int or str)
    """
    pass
