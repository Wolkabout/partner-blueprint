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

import streams
from wolkabout.iot import iot
from wireless import wifi

# uncomment one of the following lines depending on used board(e.g. Particle Photon, esp8266 or esp32 based board)
# from broadcom.bcm43362 import bcm43362 as wifi_driver
# from espressif.esp32net import esp32wifi as wifi_driver
# from espressif.esp8266wifi import esp8266wifi as wifi_driver
from stm.spwf01sa import spwf01sa as wifi_driver


# Insert your WiFi credentials
network_SSID = "INSERT_YOUR_WIFI_SSID"
network_SECURITY = wifi.WIFI_WPA2  # wifi.WIFI_OPEN , wifi.WIFI_WEP, wifi.WIFI_WPA, wifi.WIFI_WPA2
network_password = "INSERT_YOUR_WIFI_PASSWORD"

# Insert the device credentials received from WolkAbout IoT Platform when creating the device
device_key = "device_key"
device_password = "some_password"
actuator_references = ["SW", "SL"]

publish_period_milliseconds = 5000
streams.serial()


class ActuatorSimulator:
    def __init__(self, value):
        self.value = value


switch_simulator = ActuatorSimulator(False)
slider_simulator = ActuatorSimulator(0)


def get_actuator_status(reference):
    """
    Provide means of reading current actuator state.

    Possible states are:
    iot.ACTUATOR_STATE_READY,
    iot.ACTUATOR_STATE_BUSY,
    iot.ACTUATOR_STATE_ERROR

    :param reference: Actuator for which to get state
    :type reference: str
    :return: (state, value)
    :rtype: (str, bool or int or float or str)
    """
    if reference == "SW":
        return iot.ACTUATOR_STATE_READY, switch_simulator.value
    if reference == "SL":
        return iot.ACTUATOR_STATE_READY, slider_simulator.value


def handle_actuation(reference, value):
    """
    Handle incoming actuation command.

    :param reference: Actuator to set value for
    :type reference: str
    :param value: Value to set to
    :type value: bool or int or float or str
    """
    if reference == "SL":
        slider_simulator.value = value
    if reference == "SW":
        switch_simulator.value = value


class ConfigurationSimulator:
    def __init__(self, value):
        self.value = value


log_level = ConfigurationSimulator("INFO")
heart_beat = ConfigurationSimulator(publish_period_milliseconds / 1000)
enabled_feeds = ConfigurationSimulator("T,P,H,ACL")


def get_configuration():
    """
    Return current device configuration option's values.

    :return: configurations
    :rtype: dict
    """
    configurations = {}
    configurations["LL"] = log_level.value
    configurations["HB"] = int(heart_beat.value)
    configurations["EF"] = enabled_feeds.value
    return configurations


def handle_configuration(configuration):
    """
    Handle incoming configuration command.

    :param configuration: received configuration values
    :type configuration: dict
    """
    for config_reference, config_value in configuration.items():
        if config_reference == "LL":
            log_level.value = config_value
        if config_reference == "HB":
            heart_beat.value = config_value
        if config_reference == "EF":
            enabled_feeds.value = config_value


# Connect to WiFi network
try:
    print("Initializing WiFi driver..")
    # This setup refers to spwf01sa wi-fi chip mounted on flip n click device slot A
    # For other wi-fi chips auto_init method is available, wifi_driver.auto_init()
    wifi_driver.init(SERIAL1, D16)

    print("Establishing connection with WiFi network...")
    wifi.link(network_SSID, network_SECURITY, network_password)
    print("Done")
except Exception as e:
    print("Something went wrong while linking to WiFi network: ", e)

try:
    device = iot.Device(device_key, device_password, actuator_references)
except Exception as e:
    print("Something went wrong while creating the device: ", e)

try:
    wolk = iot.Wolk(
        device,
        host="api-demo.wolkabout.com",
        port=1883,
        actuation_handler=handle_actuation,
        actuator_status_provider=get_actuator_status,
        configuration_handler=handle_configuration,
        configuration_provider=get_configuration,
    )
except Exception as e:
    print("Something went wrong while creating the Wolk instance: ", e)

try:
    print("Connecting to WolkAbout IoT Platform")
    wolk.connect()
    print("Done")
except Exception as e:
    print("Something went wrong while connecting to the platform: ", e)

# Initial state of actuators and configuration must be delivered to the platform
# in order to be able to change their values from the platform
wolk.publish_actuator_status("SW")
wolk.publish_actuator_status("SL")

wolk.publish_configuration()

try:
    while True:
        print("Publishing readings:")
        if "T" in enabled_feeds.value.split(","):
            temperature = random(15, 40)
            print("\tTemperature: ", temperature)
            wolk.add_sensor_reading("T", temperature)
        if "P" in enabled_feeds.value.split(","):
            pressure = random(980, 1020)
            print("\tPressure: ", pressure)
            wolk.add_sensor_reading("P", pressure)
        if "H" in enabled_feeds.value.split(","):
            humidity = random(20, 70)
            print("\tHumidity: ", humidity)
            wolk.add_sensor_reading("T", temperature)
            if humidity >= 60:
                wolk.add_alarm("HH", True)
            else:
                wolk.add_alarm("HH", False)
        if "ACL" in enabled_feeds.value.split(","):
            acceleration = (random(0, 10), random(0, 10), random(0, 10))
            print("\tAcceleration: ", acceleration)
            wolk.add_sensor_reading("ACL", acceleration)

        # Publishes all stored sensor readings and alarms
        # from the queue to WolkAbout IoT Platform
        wolk.publish()
        sleep(int(heart_beat.value * 1000))
except Exception as e:
    print("Something went wrong: ", e)
