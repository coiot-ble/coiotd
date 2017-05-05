# DBus naming

The bus `org.coiot` is used by the coiotd to allow manipulation of the COIoT devices.

See files in `dbus-1/interfaces/` for the "real" specification of the interfaces.

# Object hierarchy

The bus exposes a hierarchy of objects, starting from `/org/coiot`, the objects have a unique name
that is chosen by the daemon to guarantee never to change during the life of the product.
Any COIoT interface of a subdevice must be present in the parent device.

For example, a device that is a smart power plug with a power-usage sensor must be described as
```
/org/coiot/<id>
               /1 -> .Switchable1
               /2 -> .Sensor1
```

Some special rules apply in a hierarchy of devices: a parent can miss some mandatory properties of an interface if at least one of its children has them. In that case it means the parent must be understood as "a collection of [the interface]".
This allows for a simple modelisation of complex setups.

For example, a multiple socket that has two lamps plugged-in but a single switch to control them both:
```
/org/coiot/<id> -> .Displayable1(type=Multiple socket) .Switchable1(with On)
                /1 -> .Displayable1(type=Lamp) .Switchable1(without On)
                /2 -> .Displayable1(type=Lamp) .Switchable1(without On)
```

Other example, a temperature sensor hub with 3 slave sensors in the room:
```
/org/coiot/<id> -> .Displayable1(type=Thermometer) .Sensor1(without any property)
                /1 -> .Displayable1 .Sensor1
                /2 -> .Displayable1 .Sensor1
                /3 -> .Displayable1 .Sensor1
```

A temperature and humidity sensor for a potted plant, to be displayed together:
```
/org/coiot/<id> -> .Displayable1(type=Plant) .Sensor1(without any property)
                /1 -> .Sensor1(unit=H2O ppm, exponent=4)
                /2 -> .Sensor1(unit=degrees C, exponent=-1)
```

## COIoT data types

- Dates are 64 bits unsigned (t) representing a time in millisecond in UTC since the epoch

# org.coiot.Reachable1

This interface represent the current reachability state of a device. It is implemented by every COIoT device.

- **Online**: Indicates if the device can be reached.
- **LastOnline**: Date at which the device has been online (connected, accessed, seen) for the last time.
- **Error**: Error flag, a device with that flag set is malfunctionning and requires human intervention.

Any client should probably poll this interface as if set to false, it will mean writes won't happen and
values read will be outdated.

# org.coiot.Displayable1
A device with that interface can appear in a UI.

- **Name**: User-friendly name of the device
- **Type**: optional COIoT object type

## Object type
A COIoT object representation can be deducted from two infos: the device type and its state.
While the state can be directly gathered from the DBus interface, the type must be specified to
know which kind of icons or services to display.

We could also say that the type acts as disambiguation.

A COIoT device can have at most one type, if it must have several types, it means that it should be
represented by multiples COIoT devices.

# org.coiot.Switchable1
A device with that interface can be turned on/off either by code or eventually by
manual user intervention. For many object, "on" can be defined as the state where it is active and
consumes current.

- **On**: indicates whether the device is "on" (True) or "off" (False).
- **SwitchableLog(from, to)** returns a list of tuples `(date, on)` measured between the two dates, with `from`, `to` and `date` as UTC timestamps

This interface must have one of the following types:
- Lamp: That is a special case, as turning the device on will produce light
- Wall Socket
- Multiple Socket
- Coffee Machine
- Oven

# org.coiot.Sensor1
A device with sensing capability

- **Value**: converted sensor value
- **Exponent**: an exponent of 10, 3 being 10^3=kilos. Changing exponent impacts both Value and SensorLog()
- **Unit**
- **MeasureDate**
- **SensorLog(from, to)** returns a list of tuples `(date, value)` measured between the two dates

The units can be the following:
- degree C
- degree F
- H2O ppm
- CO2 ppm
- CO ppm
- NOX ppm
- Small particles ppm
- Gram
- Watt
- WattHour

The type must be one of the following:
- Thermometer
- Plant
- Window
- Scale

# Caching of data, accessing devices
Due to the long time it takes to set and retrieve data, accessing a property is an
asynchronous operation; that is reading a property means getting its latest known value
and setting it means setting-up the device's real property **target** value.

Performance-wise this means that clients have to be careful of several things:
- A succesful read does not mean the device has been physically accessed, as the cache
is the one being read; so a device can appear online for some time after being powered-up.
Some mitigations techniques should be implemented for devices that require to be always
available (security systems...).
- A succesful write does not mean the device has been physically accessed either. When
the call returns, it means the **target** value has been updated and the system will try
to set it as fast as possible. Registering for the `PropertiesChanged` DBus signal is the
way to know that the property has been physically set and to which value.
- Two concurrent writes will overwrite one another using last-arrived-first-served priority.
That mean a write may never happen if another client is concurrently accessing the same device.

## Target device

In order to check what is the target state of a device, the future device can be used. For a
device of path `/org/coiot/a/b/c`, its target device is `/org/coiot/target/a/b/c`.

The target device has exactly the same properties as the actual device, except that their value
is not the actual one but the target one.

A target device can have its properties set, it will act as it the origin device had its properties set. 

# Unreachable states
Unreachable devices are devices that the daemon cannot or will not talk to, such devices stay
installed and keep their properties but they won't be physically accessed until some special
condition is reached.

In case the device is not reachable, its property `org.coiot.Reachable1.Online` is set to false.

A device that is unreachable can have its properties set normally, except that they won't be
actually set until it becomes reachable again.

If a device cannot be detected or connected to after a certain time, it will be set into a
"Offline" state. The daemon checks regularly for offline devices to see if they came back online.

If a device returns too many errors in a row, it will be set into an "Error" state. A device on this
state will have its property `org.coiot.Reachable1.Error` set to true.

Setting back the `org.coiot.Reachable1.Error` of a device to false does not automatically make it
reachable, the daemon has to check first that the device is still online.
