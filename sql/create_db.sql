CREATE TABLE DEVICE (
	ID INTEGER PRIMARY KEY,
	Parent INTEGER,

	FOREIGN KEY(Parent) REFERENCES DEVICE(ID)
);

CREATE TABLE DEVICE_STATUS_LOG (
	ID INTEGER PRIMARY KEY,
	Device INTEGER NOT NULL,
	Date DATETIME DEFAULT(STRFTIME('%Y-%m-%dT%H:%M:%f', 'NOW')),
	Online BOOLEAN NOT NULL DEFAULT(1),
	Error BOOLEAN NOT NULL DEFAULT(0),

	FOREIGN KEY(Device) REFERENCES DEVICE(ID)
);

CREATE TABLE DISPLAYABLE_TYPE (
	ID INTEGER PRIMARY KEY,
	Name TEXT NOT NULL
);
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Lamp');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Wall Socket');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Multiple Socket');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Coffee Machine');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Oven');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Thermometer');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Plant');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Window');
INSERT INTO DISPLAYABLE_TYPE(Name) VALUES('Scale');

CREATE TABLE DISPLAYABLE (
	ID INTEGER PRIMARY KEY,
	Device INTEGER NOT NULL,
	Name TEXT NOT NULL,
	Type INTEGER,

	FOREIGN KEY(Device) REFERENCES DEVICE(ID),
	FOREIGN KEY(Type) REFERENCES DISPLAYABLE_TYPE(ID)
);

CREATE TABLE SWITCHABLE (
	ID INTEGER PRIMARY KEY,
	Device INTEGER NOT NULL,
	FutureOn INTEGER,

	FOREIGN KEY(Device) REFERENCES DEVICE(ID)
);

CREATE TABLE SWITCHABLE_LOG (
	ID INTEGER PRIMARY KEY,
	Switchable INTEGER NOT NULL,
	Date DATETIME NOT NULL DEFAULT(STRFTIME('%Y-%m-%dT%H:%M:%f', 'NOW')),
	Value BOOLEAN NOT NULL,

	FOREIGN KEY(Switchable) REFERENCES SWITCHABLE(ID)
);

CREATE TABLE UNIT (
	ID INTEGER PRIMARY KEY,
	Name TEXT NOT NULL,
	Fundamental INTEGER,

	FOREIGN KEY(Fundamental) REFERENCES UNIT(ID)
);

INSERT INTO UNIT(Name)              VALUES('Degree C');
INSERT INTO UNIT(Name, Fundamental) SELECT 'Degree F', ID FROM UNIT WHERE Name = 'Degree C';
INSERT INTO UNIT(Name)              VALUES('H2O ppm');
INSERT INTO UNIT(Name)              VALUES('CO2 ppm');
INSERT INTO UNIT(Name)              VALUES('CO ppm');
INSERT INTO UNIT(Name)              VALUES('NOX ppm');
INSERT INTO UNIT(Name)              VALUES('Small particles ppm');
INSERT INTO UNIT(Name)              VALUES('Gram');
INSERT INTO UNIT(Name)              VALUES('Watt');
INSERT INTO UNIT(Name)              VALUES('WattHour');

CREATE TABLE UNIT_CONVERSION (
	ID INTEGER PRIMARY KEY,
	UnitFrom INTEGER NOT NULL,
	UnitTo INTEGER NOT NULL,
	Offset FLOAT NOT NULL,
	Scale FLOAT NOT NULL,

	FOREIGN KEY(UnitFrom) REFERENCES UNIT(ID),
	FOREIGN KEY(UnitTo) REFERENCES UNIT(ID)
);
INSERT INTO UNIT_CONVERSION(UnitFrom, UnitTo, Offset, Scale) SELECT DC.ID, DF.ID, 32, 1.8 FROM UNIT DC, UNIT DF WHERE DC.Name = 'Degree C' AND DF.Name = 'Degree F';

CREATE TABLE SENSOR (
	ID INTEGER PRIMARY KEY,
	Device INTEGER NOT NULL,
	Exponent INTEGER NOT NULL,
	Unit INTEGER NOT NULL,

	FOREIGN KEY(Device) REFERENCES DEVICE(ID),
	FOREIGN KEY(Unit) REFERENCES UNIT(ID)
);

CREATE TABLE SENSOR_LOG (
	ID INTEGER PRIMARY KEY,
	Sensor INTEGER NOT NULL,
	Date DATE NOT NULL,
	Value INTEGER NOT NULL,

	FOREIGN KEY(Sensor) REFERENCES SENSOR(ID)
);

CREATE TABLE DRIVER_BLE (
	ID INTEGER PRIMARY KEY,
	Device INTEGER NOT NULL,
	Mac TEXT NOT NULL,

	FOREIGN KEY(Device) REFERENCES DEVICE(ID)
);

PRAGMA USER_VERSION = 1;
