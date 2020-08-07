# WolkConnect-Python-Zerynth
----
WolkAbout Python Connector library for connecting Zerynth enabled devices to [WolkAbout IoT Platform](https://demo.wolkabout.com/#/login).

Supported protocol(s):
* WolkAbout Protocol

## Example Usage
----

### Establishing connection with WolkAbout IoT platform

Create a device on WolkAbout IoT platform by using the provided *Simple example* device type.
This template fits [Controlled_publish_period](https://github.com/Wolkabout/wolkabout-iot/blob/master/examples/Controlled_publish_period/main.py) example and demonstrates the periodic sending of a temperature sensor reading.

```python
from wolkabout.iot import iot

# Setup credentials received upon device creation on the platform
device_key = "device_key"
device_password = "some_password"

device = iot.Device(device_key, device_password)
wolk = iot.Wolk(device)
wolk.connect()
```

Connecting to a different WolkAbout IoT platform instance is achieved in the following manner:

```python
wolk = iot.Wolk(device, host="api-demo.wolkabout.com", port=2883)
wolk.connect()
```

### Adding sensor readings

```python
wolk.add_sensor_reading("T", 26.93)
```

### Adding events

```python
wolk.add_alarm("ALARM_REFERENCE", True)
```

### Data publish strategy

Stored sensor readings and alarms, as well as current actuator statuses are pushed to WolkAbout IoT platform on demand by calling:

```python
wolk.publish()
```

### Disconnecting from the platform

```python
wolk.disconnect()
```

----

## Advanced features

### Publishing actuator statuses

In order to be able to send actuator statuses and receive actuation commands, a list of actuator references must be provided to `iot.Device`.
```python
device_key = "device_key"
device_password = "some_password"
actuator_references = ["ACTUATOR_REFERENCE_ONE", "ACTUATOR_REFERENCE_TWO"]
device = iot.Device(device_key, device_password, actuator_references)
```

Additionally, an implementation of [actuator_status_provider](./wolk/interface/actuator_status_provider.py) and [actuation_handler](./wolk/interface/actuation_handler.py) must be provided to `iot.Wolk`.
An example implementation would look something like this:

```python
def get_actuator_status(reference):
    if reference == "ACTUATOR_REFERENCE_ONE":
        return iot.ACTUATOR_STATE_READY, switch_simulator.value


def handle_actuation(reference, value):
    if reference == "ACTUATOR_REFERENCE_ONE":
        print("Setting actuator " + reference + " to value: " + str(value))
        current_state = digitalRead(LED1)
        if current_state == 1:
            if value is False:
                digitalWrite(LED1, LOW)
        else:
            if value is True:
                digitalWrite(LED1, HIGH)


wolk = iot.Wolk(
    device,
    actuation_handler=handle_actuation,
    actuator_status_provider=get_actuator_status
)
```

Actuator statuses can be published explicitly by calling:

```python
wolk.publish_actuator_status("ACTUATOR_REFERENCE_ONE")
```

### Publishing configuration

Similarly to actuators, configuration options require a provider and a handler.
See [configuration_provider](./wolk/interface/configuration_provider.py) and [configuration_handler](./wolk/interface/configuration_handler.py) for implementation details.

Pass these implementations to `iot.Wolk` like so:

```python
wolk = iot.Wolk(
    device,
    configuration_handler=handle_configuration,
    configuration_provider=get_configuration,
)
```

All present configuration options are published by calling:

```python
wolk_device.publish_configuration()
```

### Data persistence

WolkAbout Python Connector provides a mechanism for persisting data in situations where readings can not be sent to WolkAbout IoT platform.

Persisted readings are sent to WolkAbout IoT platform once connection is established.
Data persistence mechanism used by default stores data in-memory.

The number of messages stored in memory by default is 100. This number can be changed like so:

```python
wolk = iot.Wolk(device, message_queue_size=100)
wolk.connect()
```
