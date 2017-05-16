-- Remove the column FutureOn from SWITCHABLE
-- Because SQLite does not fully implements ALTER TABLE,
-- we have to create a backup table, copy all data to it,
-- then rename it to replace the old one.
--
-- see: http://stackoverflow.com/questions/5938048/delete-column-from-sqlite-table/5987838#5987838
CREATE TABLE SWITCHABLE_NEW (
	ID INTEGER PRIMARY KEY,
	Device INTEGER NOT NULL,

	FOREIGN KEY(Device) REFERENCES DEVICE(ID)
);

INSERT INTO SWITCHABLE_NEW
SELECT ID, Device
FROM SWITCHABLE;

DROP TABLE SWITCHABLE;

CREATE TABLE SWITCHABLE (
	ID INTEGER PRIMARY KEY,
	Device INTEGER NOT NULL,

	FOREIGN KEY(Device) REFERENCES DEVICE(ID)
);

INSERT INTO SWITCHABLE
SELECT ID, Device
FROM SWITCHABLE_NEW;

DROP TABLE SWITCHABLE_NEW;
