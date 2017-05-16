# Database schema

The COIoT database is normalized and formally defined to allow a good backward and forward compatibily.

## General rules

The SQLite pragma USER_VERSION is used to store the schema version.

The database is in UTF-8.

Please see DBus interface for clarification on the fields values and meanings.

In order to manage delays in setting data, use transactions; eg set a Switch to ON and commit when
the BLE write command successfully returns.

All foreign key references are made using the ID of the table. ID have no meaning apart from
being unique for each entry and never reused.

# DEVICE
* ID
* Parent: foreign key to DEVICE. eg if foo is child of device bar, its Parent field will be set to bar

# DEVICE_STATUS_LOG
* ID
* Device: foreign key to DEVICE
* Date
* Online
* Error

# DISPLAYABLE_TYPE
* ID
* Name

# DISPLAYABLE
* ID
* Device: foreign key to DEVICE
* Name
* Type: foreign key to DISPLAYABLE_TYPE

# SWITCHABLE
* ID
* Device: foreign key to DEVICE

# SWITCHABLE_LOG
* ID
* Switchable: foreign key to switchable
* Date
* Value

# UNIT
* ID
* Name
* Fundamental: foreign key to UNIT
Important: values are stored in the fundamental unit, not the sensor or user unit; so that if there
is two thermometers, one in Farenheit and one in Celsius, they are all stored in Celsius and
displayed in the unit the user wants.

# UNIT_CONVERSION
* ID
* UnitFrom: foreign key to UNIT
* UnitTo: foreign key to UNIT
* Offset
* Scale

UnitTo = Offset + Scale * UnitFrom
UnitFrom = (UnitTo - Offset) / Scale

# SENSOR
* ID
* Device: foreign key to DEVICE
* Exponent
* Unit: foreign key to UNIT

# SENSOR_LOG
* ID
* Sensor: foreign key to SENSOR
* Date
* Value

# Private tables

Following tables are used for storing some informations, like drivers data. They are not exported
through DBus.

# DRIVER_BLE
* ID
* Device: foreign key to DEVICE
* Mac: BLE device MAC address
* Idx: COIoT device Index for BLE devices with array characteristics (eg: Automation IO)

# DRIVER_SONOS
* ID
* Device: foreign key to DEVICE
* Zone: name of the SONOS player
