# unit test cases for Maria DB wrapper class

from MariaWrapper import *

TEST_MAC1 = '10A578C3D188'
TEST_MAC2 = '20B17809C62F'
TEST_MAC3 = '30AB60C3F0E5'

def print_time():
    print(maria.getTimeStamp())

def print_tables():
    print('Tables:')
    tabs = maria.listTables()
    print(tabs)
    print()
        
def drop_tables():
    maria.dropTables()
    print ('Tables dropped.')
        
def create_tables():
    maria.createTables()
    print ('Tables created.')
        
def get_dev_types():
    print('Device types:')
    dts = maria.getDeviceTypes()
    print (dts)
    print ()
    
def get_room_types():
    print('Room types:')
    rts = maria.getRoomTypes()
    print (rts)
    print ()
    
def insert_dev_types():
    print('Updating device types..')
    dt = {  'device_types': 
        ['Smoke detector',  'Pump', 'Bulb', 'CO2 alarm', 'Others']
    }
    res = maria.insertDeviceTypes(dt)
    print (res)
    print()
            
def insert_room_types():
    print('Updating room types..')
    rt = {  'room_types': 
         ['Drawing room',  'Mini Hall', 'Kitchen', 'Pooja room', 'Others']    }
    res = maria.insertRoomTypes(rt)
    print (res)
    print()
                
def insert_app_config():
    print ('inserting app config items..')
    conf1 = {'config_id':'ckey1', 'config_item':'{"name":"Raja", "age":43}'}
    raw_conf = { 
        "user_id" : "myselfd@intof.in",
        "app_id" :  "A8B4CD78C09-89ASF0",
        "hub_id" : "Hub-123A.4",
        "version" : "1.2"
        }
    conf2 = {'config_id':'ckey2', 'config_item':raw_conf}
    maria.insertAppConfig (conf1)
    maria.insertAppConfig (conf2)
    print()
    
def get_app_config():  
    print ('fetching app config items..')
    conf = maria.getAppConfig ({'config_id':'ckey1'})
    print (conf)
    conf = maria.getAppConfig ({'config_id':'non_existent_id'})
    print (conf)  
    conf = maria.getAppConfig ({'config_id':'ckey2'})
    print (conf)
    print() 
    
def register_device():
    print ('New devices: self-registering...')
    new_min_dev1 = {'device_id':TEST_MAC1, 'hardware_type':'REL4.1-PIR-RAD', 'num_relays':4}
    new_min_dev2 = {'device_id':TEST_MAC2, 'hardware_type':'REL2.0', 'num_relays':2}
    maria.registerDevice (new_min_dev1)
    maria.registerDevice (new_min_dev2)
        
def direct_insert_device():  
    print ('Directly provisioning device from back end...')
    jhw_conf = {'group_id':'G0', 'primary_relay':1, 'active_low':0, 
        'auto_off_min':2.5, 'status_freq':5}
    full_dev = {'device_id':TEST_MAC3, 'hardware_type':'REL4.3-TEM', 'num_relays':4,
        'room_name':'Grandma\'s room', 'room_type' : 'Bed Room',
        'enabled':1, 'hardware_config': json.dumps(jhw_conf)}
    maria.directInsertDevice (full_dev)  
    
def discover_devices():
    print('New devices:')
    new_devs = maria.getNewDevices()  
    print(new_devs)
    print()  
    
def list_hardware_types():    
    print ('Hardware types:')
    hw_types = maria.getHardwareTypes()
    print(hw_types)
    print()  
        
def provision_devices():  # this is actually onboarding the device
    print ('Provisioning non existent device..')
    provision_params1 = {
        'device_id' : 'ABCDEFG0000',
        'room_name' : 'Bust room',
        'room_type' : 'Unknown room type'
    }
    res = maria.provisionDevice (provision_params1)    
    print(res)
    print ('Provisioning real device..')
    provision_params2 = {
        'device_id' : TEST_MAC1,
        'room_name' : 'Kutty\'s bed room',
        'room_type' : 'Bed room'
    }
    res = maria.provisionDevice (provision_params2) 
    print(res)
    print()
    
def get_active_devices():
    print('Active devices:')      
    act_devs = maria.getActiveDevices()
    print (act_devs)
    print()
    
def set_status():
    print ('Setting device status..')
    dev_status = {'device_id':TEST_MAC1, 'relay_status':'0101'} 
    maria.insertDeviceStatus (dev_status)   
    
def get_status():
    print ('Device status:')
    dev_status = maria.getDeviceStatus ({'device_id':TEST_MAC1})
    print (dev_status)
    print()
    
def set_data():
    print ('Setting device data..')
    simul_data = {"LIGHT":456, "TEMP":23, "HUMI":76}
    dev_data = {'device_id':TEST_MAC2, 'relay_status':'0101', 'data':simul_data} 
    maria.insertDeviceData (dev_data)   
    print ()
    
def get_data():
    print ('Device data:')
    dev_data = maria.getDeviceData ({'device_id':TEST_MAC1})
    print (dev_data)
    dev_data = maria.getDeviceData ({'device_id':TEST_MAC2})
    print (dev_data)
    print ()
        
def set_event():
    print ('Adding event..')
    eve_body = {'update':'failed', 'reason':'HTTP', 'code':400}
    dev_event = {'device_id':TEST_MAC1, 'event_type':'FW_UPDATE', 'event_body':eve_body}
    dev_status = maria.insertDeviceEvent (dev_event)
    print ()
    
def get_event():
    print ('Device event:')
    event = maria.getDeviceEvent({'device_id':TEST_MAC1})
    print(event)    
    event = maria.getDeviceEvent({'device_id':TEST_MAC2})
    print(event)
    print()
    
def get_dev_config():
    print ('Device config:')
    dc = maria.getDeviceConfig ({'device_id':TEST_MAC1})
    print(dc)
    print()
    dc = maria.getDeviceConfig ({'device_id':'non-existant'})
    print(dc)
    print()    
    dc = maria.getDeviceConfig ({'device_id':TEST_MAC3})
    print(dc)    
    print()
    
def set_dev_config():
    print ('Inserting device config..')
    dc1 = {'name':'Hall light',     'type' : 'Light', 'schedule':[18,30,6,0]}
    dc2 = {'name':'Bed room A/C',   'type' : 'A/C',   'schedule':[20,0,5,40]}
    dc3 = {'name':'Hall fan',       'type' : 'Fan',   'schedule':[]}
    dc4 = {'name':'Portico light',  'type' : 'Light', 'schedule':[14,30,7,10]}
    dev_con = {
        'device_id':TEST_MAC1,   # TEST_MAC2 here should raise an exception
        'room_name' : 'Basement',
        'room_type' : 'Garage',
        'device_config' : [dc1, dc2, dc3, dc4]
    }
    maria.insertDeviceConfig (dev_con)
    print()          
    
def dev_exits(): 
    print ('Device existence:')
    devex = maria.deviceExists (TEST_MAC1)  
    print(devex)   
    devex = maria.deviceExists ('no-such-dev') 
    print(devex)      
    devex = maria.deviceExists (TEST_MAC2) 
    print(devex)      
    print()
    
def delete_dev():
    print('Deleting device..')
    maria.deleteDevice  ({'device_id':TEST_MAC1})   
    print()
    
#-------------------------------------------------------------------------------
# MAIN 
#-------------------------------------------------------------------------------
    
maria = MariaWrapper(debug=True)
print()
maria.connect (db=PasswordStore.db_name, host=PasswordStore.db_host, port=PasswordStore.db_port)
print ('Connected to DB.')

print_time()
print()

print_tables()
drop_tables()
print_tables()
create_tables()
print_tables()

get_dev_types()
get_room_types()
insert_dev_types()
insert_room_types()
get_dev_types()
get_room_types()

insert_app_config()
get_app_config()

discover_devices()

register_device()
list_hardware_types()
direct_insert_device() 
list_hardware_types()

discover_devices()
get_active_devices()

provision_devices()

discover_devices()
get_active_devices()

get_dev_config()
set_dev_config()
get_dev_config()

get_data()
set_data()
get_data()

get_status()
set_status()
get_status()

set_event()
get_event()   

dev_exits()
#delete_dev()
#dev_exits()

maria.close()
print('Done!')

