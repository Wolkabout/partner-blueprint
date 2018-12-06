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

publish_period_milliseconds = 5000
streams.serial()

# Enable debug printing by setting flag to True
iot.debug_mode = False


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
    device = iot.Device(device_key, device_password)
except Exception as e:
    print("Something went wrong while creating the device: ", e)

try:
    wolk = iot.Wolk(device)
except Exception as e:
    print("Something went wrong while creating the Wolk instance: ", e)

try:
    print("Connecting to WolkAbout IoT Platform")
    wolk.connect()
    print("Done")
except Exception as e:
    print("Something went wrong while connecting to the platform: ", e)


try:
    while True:
        temperature = random(15, 40)
        print("Publishing sensor reading T: " + str(temperature) + " C")

        # Adds a sensor reading to the queue
        wolk.add_sensor_reading("T", temperature)

        # Publishes all stored sensor readings from the queue to the WolkAbout IoT Platform
        wolk.publish()
        sleep(publish_period_milliseconds)
except Exception as e:
    print("Something went wrong: ", e)
