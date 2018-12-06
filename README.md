# WolkConnect-Python-Zerynth
----
WolkAbout Python Connector library for connecting Zerynth enabled devices to [WolkAbout IoT Platform](https://demo.wolkabout.com/#/login).

Supported protocol(s):
* JsonSingleReferenceProtocol

## Example Usage
----

### Establishing connection with WolkAbout IoT platform

Create a device on WolkAbout IoT platform by importing [manifest.json](https://github.com/Wolkabout/wolkabout-iot/blob/master/examples/Controlled_publish_period/manifest.json).
This manifest fits [Controlled_publish_period](https://github.com/Wolkabout/wolkabout-iot/blob/master/examples/Controlled_publish_period/main.py) example and demonstrates the periodic sending of a temperature sensor reading.

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
wolk = iot.Wolk(device, host="api-demo.wolkabout.com", port=1883)
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

### Debugging

Display send and received messages with `iot.debug_mode` :

```python
# Enable debug printing by setting flag to True
iot.debug_mode = False
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

Additionally, an implementation of `iot.ActuatorStatusProvider` and `iot.ActuationHandler` must be provided to `iot.Wolk`.
An example implementation would look something like this:

```python
class ActuatorStatusProviderImpl(iot.ActuatorStatusProvider):
    def get_actuator_status(self, reference):
        if reference == "ACTUATOR_REFERENCE_ONE":
            value = digitalRead(LED1)
            if value == 1:
                return iot.ACTUATOR_STATE_READY, True
            else:
                return iot.ACTUATOR_STATE_READY, False


class ActuationHandlerImpl(iot.ActuationHandler):
    def handle_actuation(self, reference, value):
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
    actuation_handler=ActuationHandlerImpl(),
    actuator_status_provider=ActuatorStatusProviderImpl()
)
```

Actuator statuses can be published explicitly by calling:

```python
wolk.publish_actuator_status("ACTUATOR_REFERENCE_ONE")
```

### Publishing configuration

Similarly to actuators, configuration options require a provider and a handler.
See `iot.ConfigurationProvider` and `iot.ConfigurationHandler` for implementation details.

Pass these implementations to `iot.Wolk` like so:

```python
wolk = iot.Wolk(
    device,
    configuration_handler=ConfigurationHandlerImpl(),
    configuration_provider=ConfigurationProviderImpl(),
)
```

All present configuration options are published by calling:

```python
wolk_device.publish_configuration()
```

### Data persistence

WolkAbout Python Connector provides a mechanism for persisting data in situations where readings can not be sent to WolkAbout IoT platform.

Persisted readings are sent to WolkAbout IoT platform once connection is established.
Data persistence mechanism used **by default** stores data in-memory.

The number of messages stored in memory by default is 100. This number can be changed like so:

```python
wolk = iot.Wolk(device, outbound_message_queue=iot.ZerynthOutboundMessageQueue(message_count))
wolk.connect()
```

In cases when provided in-memory persistence is suboptimal, one can use custom persistence by implementing `iot.OutboundMessageQueue`,
and forwarding it to the constructor in the following manner:

```python
wolk = iot.Wolk(device, outbound_message_queue=custom_queue)
wolk.connect()
```
For more info on persistence mechanism see `iot.OutboundMessageQueue` class

### Keep alive mechanism

The library by default uses a Keep Alive mechanism to notify WolkAbout IoT Platform that device is still connected. A keep alive message is sent to WolkAbout IoT Platform every 30 seconds.

To reduce network usage Keep Alive mechanism can be disabled in following manner:

```python
wolk = iot.Wolk(device, keep_alive_enabled=False)
wolk.connect()
```