.. module:: iot

******************************
WolkAbout IoT Platform Library
******************************

WolkAbout Python Connector library for connecting Zerynth devices to `WolkAbout IoT Platform <https://wolkabout.com/>`_.
The `Wolk` class depends upon interfaces, making it possible to provide different implementations.
The section `Dependencies` contains the documentation of the default implementations, followed by the `Wolk` section that
contains everything necessary to connect and publish data to the WolkAbout IoT Platform.
============
Dependencies
============

The following classes are implementations of interfaces on which the Wolk class depends.

-------------------------
MQTT Connectivity Service
-------------------------


.. class:: MQTTConnectivityService(ConnectivityService)

Provide connection to WolkAbout IoT Platform via MQTT.

* :samp:`device`: Contains device key, device password and actuator references
* :samp:`host`: Address of the WolkAbout IoT Platform instance
* :samp:`port`: Port of WolkAbout IoT Platform instance
* :samp:`qos`: Quality of Service for MQTT connection (0,1,2), defaults to 0
.. method:: set_inbound_message_listener(on_inbound_message)

Set the callback method to handle inbound messages.

* :samp:`on_inbound_message`:  The method that handles inbound messages
.. method:: on_mqtt_message(client, data)

Method that serializes inbound messages and passes them to the inbound message listener

* :samp:`client`:  The client that received the message
* :samp:`data`: The message received
.. method:: connect()

This method establishes the connection to the WolkAbout IoT platform.
If there are actuators it will subscribe to topics
that will contain actuator commands and also
starts a loop to handle inbound messages.
Raises an exception if the connection failed.
.. method:: disconnect()

Disconnects the device from the WolkAbout IoT Platform

        
.. method:: connected()

Returns the current status of the connection

        
.. method:: publish(outbound_message)

Publishes the :samp:`outbound_message` to the WolkAbout IoT Platform

        
----------------------
Outbound Message Queue
----------------------


.. class:: ZerynthOutboundMessageQueue(OutboundMessageQueue.OutboundMessageQueue)

This class provides the means of storing messages before they are sent to the WolkAbout IoT Platform.

* :samp:`maxsize`: Int - The maximum size of the queue, effectively limiting the number of messages to persist in memory

    
.. method:: put(message)

Adds the :samp:`message` to :samp:`self.queue`

        
.. method:: get()

Takes the first :samp:`message` from :samp:`self.queue`

        
.. method:: peek()

Returns the first :samp:`message` from :samp:`self.queue` without removing it from the queue

        
------------------------
Outbound Message Factory
------------------------

.. class:: ZerynthOutboundMessageFactory(OutboundMessageFactory.OutboundMessageFactory)

This class serializes sensor readings, alarms and actuator statuses so that they can be properly sent to the WolkAbout IoT Platform

* :samp:`device_key` - The key used to serialize messages
    
.. method:: make_from_sensor_reading(reading)

Serializes the :samp:`reading` to be sent to the WolkAbout IoT Platform

* :samp:`reading`: Sensor reading to be serialized
        
.. method:: make_from_alarm(alarm)

Serializes the :samp:`alarm` to be sent to the WolkAbout IoT Platform

* :samp:`alarm`: Alarm event to be serialized
        
.. method:: make_from_actuator_status(actuator)

Serializes the :samp:`actuator` to be sent to the WolkAbout IoT Platform

* :samp:`actuator`: Actuator status to be serialized
        
.. method:: make_from_configuration(self, configuration)

Serializes the device's configuration to be sent to the platform

* :samp:`configuration`: Configuration to be serialized
        
-----------------------
Inbound Message Factory
-----------------------

.. class:: ZerynthInboundMessageDeserializer(InboundMessageDeserializer.InboundMessageDeserializer)

This class deserializes messages that the device receives from the WolkAbout IoT Platform from the topics it is subscribed to.

    
.. method:: deserialize_actuator_command(message)

Deserializes the :samp:`message` that was received from the WolkAbout IoT Platform

* :samp:`message`: The message to be deserialized
        
.. method:: deserialize_configuration_command(message)

Deserializes the :samp:`message` that was received from the WolkAbout IoT Platform

* :samp:`message` The message to be deserialized
        
==========
Wolk class
==========

.. class:: Wolk

This class is a wrapper for the WolkCore class that passes the Zerynth compatible implementation of interfaces to the constructor

* :samp:`device`: Contains device key and password, and actuator references
* :samp:`host`: The address of the WolkAbout IoT Platform, defaults to the Demo instance
* :samp:`port`: The port to which to send messages, defaults to 1883
* :samp:`actuation_handler`: Implementation of the :samp:`ActuationHandler` interface
* :samp:`actuator_status_provider`: Implementation of the :samp:`ActuatorStatusProvider` interface
* :samp:`outbound_message_queue`: Implementation of the :samp:`OutboundMessageQueue` interface
* :samp:`configuration_handler`: Implementation of the :samp:`ConfigurationHandler` interface
* :samp:`configuration_provider`: Implementation of the :samp:`ConfigurationProvider` interface

    
.. method:: connect()

Connects the device to the WolkAbout IoT Platform by calling the provided connectivity_service's :samp:`connect` method

        
.. method:: disconnect()

Disconnects the device from the WolkAbout IoT Platform by calling the provided connectivity_service's :samp:`disconnect` method

        
.. method:: add_sensor_reading(reference, value, timestamp=None)

Publish a sensor reading to the platform

* :samp:`reference`: String - The reference of the sensor
* :samp:`value`: Int, Float - The value of the sensor reading
* :samp:`timestamp`: (optional) Unix timestamp - if not provided, platform will assign one upon reception
        
.. method:: add_alarm(reference, active, timestamp=None)

Publish an alarm to the platform

* :samp:`reference`: String - The reference of the alarm
* :samp:`active`: Bool - Current state of the alarm
* :samp:`timestamp`: (optional) Unix timestamp - if not provided, platform will assign one upon reception
        
.. method:: publish()

Publishes all currently stored messages and current actuator statuses to the platform
        
.. method:: publish_actuator_status(reference)

Publish the current actuator status to the platform

* :samp:`reference`: String - The reference of the actuator
        
.. method:: _on_inbound_message(message)

Callback method to handle inbound messages

.. note:: Pass this method to the implementation of :samp:`ConnectivityService` interface

* :samp:`message`: The message received from the platform
        
.. method:: publish_configuration()

Publishes the current device configuration to the platform

        
------
Device
------


.. class:: Device

    The :samp:`Device` class contains all the required information for connecting to the WolkAbout IoT Platform.

    * :samp:`key` - The device key obtained when creating the device on WolkAbout IoT platform
    * :samp:`password` - The device password obtained when creating the device on WolkAbout IoT platform
    * :samp:`actuator_references` - A list of actuator references defined in the device template on WolkAbout IoT Platform

    
-----------------
Actuation Handler
-----------------

.. class:: ActuationHandler

    This interface must be implemented in order to execute actuation commands issued from WolkAbout IoT Platform.

.. method:: handle_actuation(reference, value)

    This method will try to set the actuator, identified by :samp:`reference`, to the :samp:`value` specified by WolkAbout IoT Platform

    
------------------------
Actuator Status Provider
------------------------

.. class:: ActuatorStatusProvider


    This interface must be implemented in order to provide information about the current status of the actuator to the WolkAbout IoT Platform


.. method:: get_actuator_status(reference)


    This method will return the current actuator :samp:`state` and :samp:`value`, identified by :samp:`reference`, to the WolkAbout IoT Platform.
    The possible `states` are::

        iot.ACTUATOR_STATE_READY
        iot.ACTUATOR_STATE_BUSY
        iot.ACTUATOR_STATE_ERROR

    The method should return something like this::

        return (iot.ACTUATOR_STATE_READY, value)

    
---------------------
Configuration Handler
---------------------

.. class:: ConfigurationHandler

    This interface must be implemented in order to handle configuration commands issued from WolkAbout IoT Platform

.. method:: handle_configuration(configuration)

    This method should update device configuration with received configuration values.

     * :samp:`configuration` - Dictionary that containes reference:value pairs

    
----------------------
Configuration Provider
----------------------

.. class:: ConfigurationProvider

    This interface must be implemented to provide information about the current configuration settings to the WolkAbout IoT Platform

.. method:: get_configuration()

    Reads current device configuration and returns it as a dictionary with device configuration reference as the key, and device configuration value as the value.
    
