# DBus naming

The bus `org.coiot` is used by the coiotd to allow manupilation of the COIoT devices.

# Object hierarchy

It contains a hierarchy of objects, starting from `/org/coiot`, the objects are each contained under that
with a name that is chosen by the daemon to guarantee never to change during the life of the product.
A device can have a sub-device if they are both 

For example, a device that is a smart power plug with a power-usage sensor must be described as
```
/org/coiot/<id>
               /1 -> .Switchable1
               /2 -> .Sensor1
```

Some special rules apply in a hierarchy of devices: if a devices is missing a property, then it should be
read as the parent's property. A parent can miss some properties if every one of its children include the
same interface.

This allows for a simple modelisation of complex setups.

For example, a multiple socket that has two lamps plugged-in but a single switch to control them both:
```
/org/coiot/<id> -> .Displayable1(type=Multiple socket) .Switchable1(w/ on)
                /1 -> .Displayable1(type=Lamp) .Switchable1(w/o on)
                /2 -> .Displayable1(type=Lamp) .Switchable1(w/o on)
```

Other example, a temperature sensor hub with 3 slave sensors in the room:
```
/org/coiot/<id> -> .Displayable1(type=Thermometer) .Sensor1(w/o any property)
                /1 -> .Displayable1 .Sensor1
                /2 -> .Displayable1 .Sensor1
                /3 -> .Displayable1 .Sensor1
```

A temperature and humidity sensor for a potted plant, to be displayed together:
```
/org/coiot/<id> -> .Displayable1(type=Plant) .Sensor1(w/o any property)
                /1 -> .Sensor1(unit=H20 ppm, exponent=4)
                /2 -> .Sensor1(unit=degrees C, exponent=-1)
```

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

This interface must have one of the following types:
- Lamp: That is a special case, as turning the device on will produce light
- Wall Socket
- Multiple Socket
- Coffee Machine
- Oven

# org.coiot.Sensor1
A device with sensing capability

- **Value**: raw sensor value
- **Exponent**: an exponent of 10, 3 being 10^3=kilos
- **Unit**

The units can be the following:
- degrees C
- degrees F
- H2O ppm
- CO2 ppm
- CO ppm
- NOX ppm
- Small particules ppm

The type must be one of the following:
- Thermometer
- Plant
- Window
