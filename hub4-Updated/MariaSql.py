# Centralized place to keep all SQLs
# TODO: partition deviceData/deviceEvent table by mac id, sort by time stamp DESC, and return 
# the first few records for the UI.  see:  https://mariadb.com/kb/en/row_number/    

#SQL_CREATE_DATABASE = 'CREATE DATABASE IF NOT EXISTS intof;'     # for local MariaDB
SQL_CREATE_DATABASE = 'CREATE DATABASE IF NOT EXISTS intof_hub;'  # for AWS MySQL

SQL_GET_TIMESTAMP = 'SELECT NOW();'

SQL_LIST_TABLES = 'SHOW TABLES;'

SQL_CREATETAB_APP_CONFIG = '''CREATE TABLE IF NOT EXISTS appConfig 
    (config_id VARCHAR(20) NOT NULL UNIQUE, config_item VARCHAR(1024), 
    PRIMARY KEY (config_id));'''
    
SQL_DROPTAB_APP_CONFIG = 'DROP TABLE IF EXISTS appConfig'

SQL_INSERT_APP_CONFIG = '''INSERT INTO appConfig 
    (config_id, config_item) 
    VALUES 
    (%(config_id)s, %(config_item)s);'''
    
SQL_GET_APP_CONFIG = '''SELECT * FROM appConfig
    WHERE config_id = %(config_id)s;'''
    
#--------------------------------------------------------------------------------------------

SQL_CREATETAB_DEVICE = '''CREATE TABLE IF NOT EXISTS device
    (device_id VARCHAR(16) NOT NULL UNIQUE, 
    hardware_type VARCHAR(24), num_relays SMALLINT DEFAULT 1,
    room_name VARCHAR(32) DEFAULT '(Room name)',
    room_type VARCHAR(32) DEFAULT '(Room type)',
    enabled BOOLEAN DEFAULT 0,
    hardware_config JSON,   #  DEFAULT "{}", 
    CHECK (JSON_VALID(hardware_config)), 
    PRIMARY KEY (device_id));'''

SQL_DROPTAB_DEVICE = 'DROP TABLE IF EXISTS device'

SQL_NEW_DEVICE = '''INSERT INTO device
    (device_id, hardware_type, num_relays, enabled)
    VALUES
    (%(device_id)s, %(hardware_type)s, %(num_relays)s, 0);'''    # num_relays is read-only. It comes from the device (hard coded).
    
SQL_INSERT_DEVICE = '''INSERT INTO device
    (device_id, hardware_type, num_relays, 
    room_name, room_type,
    enabled, hardware_config)
    VALUES
    (%(device_id)s, %(hardware_type)s, %(num_relays)s,
    %(room_name)s, %(room_type)s,
    %(enabled)s, %(hardware_config)s);'''   # bulk provisioning by admin

SQL_UPDATE_DEVICE = '''UPDATE device SET
    room_name = %(room_name)s,
    room_type = %(room_type)s,
    enabled = %(enabled)s, 
    hardware_config = %(hardware_config)s
    WHERE
    device_id = %(device_id)s;'''  # TODO: implement
    
SQL_PROVISION_DEVICE = '''UPDATE device SET
    room_name = %(room_name)s,
    room_type = %(room_type)s,
    enabled = 1
    WHERE
    device_id = %(device_id)s;'''
        
SQL_UPDATE_LOCATION = '''UPDATE device SET
    room_name = %(room_name)s,
    room_type = %(room_type)s   
    WHERE
    device_id = %(device_id)s;'''   
        
SQL_ENABLE_DEVICE = '''UPDATE device SET
    enabled = 1
    WHERE
    device_id = %(device_id)s;'''  # TODO: implement
           
SQL_DISABLE_DEVICE = '''UPDATE device SET
    enabled = 0
    WHERE
    device_id = %(device_id)s;'''  # TODO: implement
               
SQL_DEVICE_EXISTS = 'SELECT device_id FROM device WHERE device_id = %(device_id)s;'      

SQL_GET_NUM_RELAYS = 'SELECT num_relays from device WHERE device_id = %(device_id)s;'

SQL_GET_HARDWARE_TYPES = 'SELECT DISTINCT hardware_type FROM device;'
               
SQL_GET_STATUS_FREQS = "SELECT device_id, JSON_VALUE(hardware_config, '$.status_freq_mins') as status_freq FROM device;"   # TODO: implement

SQL_GET_ALL_DEVICES = '''SELECT device_id, hardware_type, num_relays, room_name, room_type 
    FROM device;'''     # TODO: implement
                   
SQL_GET_ACTIVE_DEVICES = '''SELECT device_id, hardware_type, num_relays, room_name, room_type
    FROM device WHERE
    enabled = 1;'''    
               
SQL_GET_NEW_DEVICES =  '''SELECT device_id, hardware_type, num_relays, room_name, room_type 
    FROM device WHERE
    enabled = 0;'''     # newly discovered devices, waiting to be provisioned
   
SQL_GET_INACTIVE_DEVICES = SQL_GET_NEW_DEVICES    # this is ony an alias: already provisioned, but deactivated temporarily for maintenence  
        
SQL_DELETE_hardware_type = '''DELETE FROM deviceType
    WHERE
    device_id = %(device_id)s;'''  # when you delete a device, do not delete its type; there may be other devices of this type  
    
SQL_DELETE_DEVICE = '''DELETE FROM device
    WHERE
    device_id = %(device_id)s;'''      
#--------------------------------------------------------------------------------------------

# Each row in this table represents one relay in a particular device
# This is a table without a unique key; duplicate mac ids are possible
# To modify a device's records, make a copy, delete all of its rows and reinsert the data

SQL_CREATETAB_DEVICE_CONFIG = '''CREATE TABLE IF NOT EXISTS deviceConfig
    (device_id VARCHAR(16) NOT NULL, 
    name VARCHAR(32) DEFAULT '(Name)', 
    type VARCHAR(32) DEFAULT '(Type)',
    schedule VARCHAR(16), light VARCHAR (16),
    FOREIGN KEY (device_id) REFERENCES device(device_id));'''

SQL_DROPTAB_DEVICE_CONFIG = 'DROP TABLE IF EXISTS deviceConfig' 

SQL_INSERT_DEVICE_CONFIG = '''INSERT INTO deviceConfig
    (device_id, name, type, schedule, light)
    VALUES
    (%(device_id)s, %(name)s, %(type)s, %(schedule)s, %(light)s);'''   # TODO: implement this!

SQL_INSERT_DEVICE_CONFIG2 = '''INSERT INTO deviceConfig
    (device_id, name, type, schedule)
    VALUES
    (%(device_id)s, %(name)s, %(type)s, %(schedule)s);''' 
    
SQL_GET_DEVICE_CONFIG = '''SELECT * FROM deviceConfig
    WHERE
    device_id = %(device_id)s;'''   # TODO: implement
   
SQL_GET_DEVICE_CONFIG2 = '''SELECT device_id, name, type, schedule FROM deviceConfig
    WHERE
    device_id = %(device_id)s;'''    # TODO: implement
    
SQL_GET_DEVICE_CONFIG3 = '''SELECT d.device_id, d.hardware_type, d.num_relays,
    d.room_name, d.room_type,
    c.name, c.type, c.schedule FROM deviceConfig c 
    INNER JOIN device d ON c.device_id=d.device_id 
    WHERE d.device_id=%(device_id)s;''' 
     
SQL_DELETE_DEVICE_CONFIG = '''DELETE FROM deviceConfig
    WHERE
    device_id = %(device_id)s;'''     
#--------------------------------------------------------------------------------------------

SQL_CREATETAB_DEVICE_DATA = '''CREATE TABLE IF NOT EXISTS deviceData
    (device_id VARCHAR(16) NOT NULL, time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
    relay_status VARCHAR(10), data JSON,  # DEFAULT "{}", 
    CHECK (JSON_VALID(data)),
    FOREIGN KEY (device_id) REFERENCES device(device_id));'''
       
SQL_DROPTAB_DEVICE_DATA = 'DROP TABLE IF EXISTS deviceData'       

SQL_INSERT_DEVICE_DATA = '''INSERT INTO deviceData
    (device_id, relay_status, data)
    VALUES
    (%(device_id)s, %(relay_status)s, %(data)s);'''   # timestamp will be auto populated 
    
SQL_INSERT_DEVICE_STATUS = '''INSERT INTO deviceData
    (device_id, relay_status)
    VALUES
    (%(device_id)s, %(relay_status)s);'''   # timestamp will be auto populated    
    
SQL_GET_DEVICE_STATUS = '''SELECT device_id, time_stamp, relay_status FROM deviceData 
    WHERE
    device_id = %(device_id)s
    ORDER BY time_stamp DESC
    LIMIT 1;'''
           
SQL_GET_DEVICE_DATA = '''SELECT * FROM deviceData 
    WHERE
    device_id = %(device_id)s    
    ORDER BY time_stamp DESC
    LIMIT 1;'''
        
SQL_DELETE_DEVICE_DATA = '''DELETE FROM deviceData
    WHERE
    device_id = %(device_id)s;'''    
#--------------------------------------------------------------------------------------------
    
SQL_CREATETAB_DEVICE_EVENT = '''CREATE TABLE IF NOT EXISTS deviceEvent
    (device_id VARCHAR(16) NOT NULL, time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
    event_type VARCHAR(12), event_body JSON,  # DEFAULT "{}", 
    CHECK (JSON_VALID(event_body)),
    FOREIGN KEY (device_id) REFERENCES device(device_id));'''
       
SQL_DROPTAB_DEVICE_EVENT = 'DROP TABLE IF EXISTS deviceEvent'       

SQL_INSERT_DEVICE_EVENT = '''INSERT INTO deviceEvent
    (device_id, event_type, event_body)
    VALUES
    (%(device_id)s, %(event_type)s, %(event_body)s);'''   # timestamp will be auto populated    
    
SQL_GET_DEVICE_EVENT =  '''SELECT * FROM deviceEvent 
    WHERE
    device_id = %(device_id)s    
    ORDER BY time_stamp DESC
    LIMIT 1;''' 
    
SQL_DELETE_DEVICE_EVENT = '''DELETE FROM deviceEvent
    WHERE
    device_id = %(device_id)s;'''      
#--------------------------------------------------------------------------------------------

SQL_CREATETAB_DEVICE_TYPES = ''' CREATE TABLE deviceTypes
    (device_type VARCHAR(36) NOT NULL);'''
    
SQL_DROPTAB_DEVICE_TYPES = 'DROP TABLE IF EXISTS deviceTypes' 
    
SQL_INSERT_DEVICE_TYPE = '''INSERT INTO deviceTypes 
    (device_type)
    VALUES
    (%s);'''
    
SQL_GET_DEVICE_TYPES = 'SELECT * FROM deviceTypes;'

SQL_DELETE_DEVICE_TYPES = 'DELETE FROM deviceTypes WHERE 1=1;'
#--------------------------------------------------------------------------------------------

SQL_CREATETAB_ROOM_TYPES = ''' CREATE TABLE roomTypes
    (room_type VARCHAR(36) NOT NULL);'''
    
SQL_DROPTAB_ROOM_TYPES = 'DROP TABLE IF EXISTS roomTypes' 
    
SQL_INSERT_ROOM_TYPE = '''INSERT INTO roomTypes 
    (room_type)
    VALUES
    (%s);'''

SQL_GET_ROOM_TYPES = 'SELECT * FROM roomTypes;'
        
SQL_DELETE_ROOM_TYPES = 'DELETE FROM roomTypes WHERE 1=1;'
#--------------------------------------------------------------------------------------------

        
CREATE_TABLES = [
    SQL_CREATETAB_APP_CONFIG,
    SQL_CREATETAB_ROOM_TYPES,
    SQL_CREATETAB_DEVICE,
    SQL_CREATETAB_DEVICE_TYPES,
    SQL_CREATETAB_DEVICE_CONFIG,
    SQL_CREATETAB_DEVICE_DATA,
    SQL_CREATETAB_DEVICE_EVENT
]

# dependent tables should be deleted before the 'device' table
DROP_TABLES = [
    SQL_DROPTAB_APP_CONFIG,
    SQL_DROPTAB_DEVICE_CONFIG,
    SQL_DROPTAB_DEVICE_DATA,  
    SQL_DROPTAB_DEVICE_EVENT,
    SQL_DROPTAB_DEVICE,
    SQL_DROPTAB_DEVICE_TYPES,
    SQL_DROPTAB_ROOM_TYPES
]    

DEVICE_TYPE_SEED = {
    'device_types': 
    ['Light', 'Fan', 'A/C', 'Heater', 'Fire alarm', 'Others']
}

ROOM_TYPE_SEED = {
    'room_types': 
    ['Bed room', 'Living room', 'Hall', 'Bath room', 'Portico', 'Garden', 'Others']
}
