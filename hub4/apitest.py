'''
TODO: http://192.168.1.10/get/device/status  fetches the last known status from the
   database; This is only for forensic audit. Contact the device to get real time status.
'''
import json
import random
import requests
from time import sleep
'''
http://127.0.0.1:5000/
http://127.0.0.1:5000/get/time
http://127.0.0.1:5000/echo

http://127.0.0.1:5000/delete/tables
http://127.0.0.1:5000/create/tables
http://127.0.0.1:5000/list/tables

http://127.0.0.1:5000/register/mobile
http://127.0.0.1:5000/insert/app/config
http://127.0.0.1:5000/get/app/config

http://127.0.0.1:5000/update/device/types
http://127.0.0.1:5000/update/room/types

http://127.0.0.1:5000/list/hardware/types
http://127.0.0.1:5000/list/device/types
http://127.0.0.1:5000/list/room/types

http://127.0.0.1:5000/self/register/device
http://127.0.0.1:5000/insert/device

http://127.0.0.1:5000/discover/devices
http://127.0.0.1:5000/list/active/devices
http://127.0.0.1:5000/list/inactive/devices    

http://127.0.0.1:5000/provision/device
http://127.0.0.1:5000/get/device/config
http://127.0.0.1:5000/update/device/config
http://127.0.0.1:5000/device/exists
http://127.0.0.1:5000/delete/device

http://127.0.0.1:5000/insert/device/data
http://127.0.0.1:5000/get/device/data
http://127.0.0.1:5000/insert/device/status
http://127.0.0.1:5000/get/device/status
http://127.0.0.1:5000/insert/device/event
http://127.0.0.1:5000/get/device/event 
'''

HTTP_OK = requests.codes.ok
APP_CONFIG_ID = None
RAND_MAC = None
TEST_MAC1 = 'AA1090C0810E'
TEST_MAC2 = 'BB2089F4021C'
TEST_MAC3 = 'CC3045F40211'
NON_EXIST_MAC = "FFFFF0EEEE"

def get_it (url, payload=None):
    print ('GET ', url)
    res = requests.get(url, params=payload)  #,headers=headers
    print ('HTTP: ', res.status_code)
    if (res.status_code != HTTP_OK):
        print ("HTTP error: {}".format (res.status_code)) 
        res.raise_for_status() 
    else:
        print (res.json())
    print()

def post_it (url, payload):
    print ('POST ', url)
    jheader = {"content-type" : "application/json"}
    res = requests.post(url, json=payload, headers=jheader)
    print ('HTTP: ', res.status_code)
    if (res.status_code != HTTP_OK):
        print ("HTTP error: {}".format (res.status_code))  
    else:
        print (res.json())
    print()
    
'''            
def get_it_cookie (url, payload=None, cookie=None):
    coo = {'my_cookie_name' : 'this is my cookie'}
    res = requests.get(url, params=payload, cookies=coo)  #,headers=headers
    print ('HTTP: ', res.status_code)
    if (res.status_code != HTTP_OK):
        print ("HTTP error: {}".format (res.status_code)) 
        res.raise_for_status() 
    else:
        print (res.json())
        if res.cookies.get ('my_cookie_name'):
            print ('got a cookie: ', res.cookies['my_cookie_name'])
    print()
'''    
#---------------------------------------------------------------------------------

def get_root():
    print('\nget root:')
    url = 'http://127.0.0.1:5000/'
    get_it (url)  
    
def get_time():
    print('\nget time:')
    url = 'http://127.0.0.1:5000/get/time'
    get_it (url)    
        
def echo_test():
    print('\necho_test:')
    url = 'http://127.0.0.1:5000/echo'  
    payload = {'Testing':'echo', 'Name':'Raja', 'Age':45, 'Nums':[20,10,70]}
    post_it (url, payload)  
            
def delete_create_list_tables():
    print('\ndelete_create_list_tables:')
    url = 'http://127.0.0.1:5000/delete/tables' 
    get_it (url)    
    url = 'http://127.0.0.1:5000/create/tables' 
    get_it (url)    
    url = 'http://127.0.0.1:5000/list/tables' 
    get_it (url)    
#------------------------------------------------------------------------------------

def register_mobile():
    print('\nregister_mobile:')
    url = 'http://127.0.0.1:5000/register/mobile'
    payload = {
        'user_id' : 'ajax@coriolis.com',
        'app_id' : 'intof_home_app',
        'version' : '1.0'
    }
    post_it (url, payload)  

def insert_app_config ():
    global APP_CONFIG_ID
    print ('\ninsert_app_config..')
    url = 'http://127.0.0.1:5000/insert/app/config'
    APP_CONFIG_ID = 'confid_{}'.format (random.randint(0,1000))
    payload = { 
                  "config_id" : APP_CONFIG_ID, 
                  "config_item" : {
                        "org_id" : "myorg",
                        "hub_name"  : "HUB1",
                        "hub_ap"    : "HUB1_AP",
                        "hub_ap_passwd" : "hubpassword",
                        "wifi_ap" : "wifiap",
                        "wifi_ap_passwd" : "wifipasswd",
                        "user_name" : "abc@gmail.com",
                        "user_pwd"  : "userpasswd",
                        "email"     : "def@gmail.com",
                        "mobile"    : "9898989898",
                        "location"  : "myhome",
                        "ota_server" : "http://192.168.4.100:8000/ota",
                        "web_server" : "http://192.168.4.100:7000/"
                   }
               }
    post_it (url, payload)  
    
def get_app_config_GET():  
    print ('\nget_app_config [GET]..')
    url = 'http://127.0.0.1:5000/get/app/config' 
    payload = {'config_id' :  APP_CONFIG_ID}  # NOTE: this can also be sent as a URL parameter
    get_it (url, payload)
    payload = {'config_id' :  'NON_EXISTING'}  # NOTE: this can also be sent as a URL parameter
    get_it (url, payload)
        
def get_app_config_POST():
    print ('\nget_app_config [POST]..')
    url = 'http://127.0.0.1:5000/get/app/config'
    payload = {'config_id' :  APP_CONFIG_ID}
    post_it (url, payload)

#--------------------------------------------------------------

def insert_device_types():
    update_device_types()
    
def update_device_types():
    print('\nupdating device types..')
    payload = {  'device_types': 
        ['Smoke detector',  'Pump', 'Bulb', 'CO2 alarm', 'Others']
    }
    url = 'http://127.0.0.1:5000/update/device/types'
    post_it (url, payload)

            
def list_device_types():
    print('\nlist device types:')
    url = 'http://127.0.0.1:5000/list/device/types'
    get_it (url)
        
    
def insert_room_types():
    update_room_types()  # they are the same

def update_room_types():
    print('\nupdating room types..')
    payload = {  'room_types': 
         ['Drawing room',  'Mini Hall', 'Kitchen', 'Pooja room', 'Others']    }
    url = 'http://127.0.0.1:5000/update/room/types'
    post_it (url, payload)
    
        
def list_room_types():
    print('\nlist room types:')
    url = 'http://127.0.0.1:5000/list/room/types'
    get_it (url)
        
    
# this is collected only from the devices table, so no insert/update    
def list_hardware_types():    
    print ('\nlist hardware types:')
    url = 'http://127.0.0.1:5000/list/hardware/types'
    get_it (url)
          
#--------------------------------------------------------------
    
def self_register_device(): # called only from the device, never from UI
    print ('devices: self-registering ...')
    url = 'http://127.0.0.1:5000/self/register/device'    
    new_min_dev1 = {'device_id':TEST_MAC1, 'hardware_type':'REL4.1-PIR-RAD', 'num_relays':4}
    new_min_dev2 = {'device_id':TEST_MAC2, 'hardware_type':'REL2.0', 'num_relays':2}
    post_it (url, new_min_dev1)
    post_it (url, new_min_dev2)
        
def direct_insert_device(): # only from back end
    global RAND_MAC
    print ('\ndirectly provisioning new device...')
    RAND_MAC = ''.join(random.choice('0123456789ABCDEF') for n in range(10))
    jhardware_conf = {'group_id':'G0', 'primary_relay':1, 'active_low':0, 
        'auto_off_min':2.5, 'status_freq':5}
    payload = {'device_id':RAND_MAC, 'hardware_type':'REL4.3-TEM', 'num_relays':4,
        'room_name':'Grandma\'s room', 'room_type' : 'Bed Room',
        'enabled':1, 'hardware_config': json.dumps (jhardware_conf)}    
    print (payload)
    url = 'http://127.0.0.1:5000/insert/device'
    post_it (url, payload)
    
def discover_new_devices():
    print ('\ndiscovering new_devices..')
    url = 'http://127.0.0.1:5000/discover/devices'
    get_it (url)
    
def  list_active_devices(): 
    print ('\nactive_devices:')
    url = 'http://127.0.0.1:5000/list/active/devices'
    get_it (url)
    
def  list_inactive_devices(): 
    print ('\ninactive_devices:')
    url = 'http://127.0.0.1:5000/list/inactive/devices'
    get_it (url)
#------------------------------------------------------------

def provision_device():  # this is the process of onboarding the device
    print ('\nprovisioning non existent device..')
    url = 'http://127.0.0.1:5000/provision/device'
    payload = {
        'device_id' : NON_EXIST_MAC,
        'room_name' : 'Bust room',
        'room_type' : 'Unknown room type'
    }
    post_it (url, payload)
    
    print ('\nprovisioning real device..')
    payload = {
        'device_id' : TEST_MAC1,
        'room_name' : 'Kutty\'s bed room',
        'room_type' : 'Bed room'
    }
    post_it (url, payload)
    
    
def get_device_config():
    print ('\nget device config (non-existant):')
    url = 'http://127.0.0.1:5000/get/device/config'
    payload = {'device_id' : NON_EXIST_MAC}
    get_it (url, payload)
    
    print ('\nget device config (real):')
    payload = {'device_id':TEST_MAC1}
    get_it (url, payload)
    
    
def update_device_config():
    print ('\nInserting device config:')
    url = 'http://127.0.0.1:5000/update/device/config'
    dc1 = {'name':'Hall light',     'type' : 'Light', 'schedule':[18,30,6,0]}
    dc2 = {'name':'Bed room A/C',   'type' : 'A/C',   'schedule':[20,0,5,40]}
    dc3 = {'name':'Hall fan',       'type' : 'Fan',   'schedule':[]}
    dc4 = {'name':'Portico light',  'type' : 'Light', 'schedule':[14,30,7,10]}
    payload = {
        'device_id':TEST_MAC1,   
        'room_name' : 'Basement',
        'room_type' : 'Garage',
        'device_config' : [dc1, dc2, dc3, dc4]
    }
    post_it (url, payload)
    # TEST_MAC3 is not provisioned, so it should raise an exception
    print ('\nInserting device config [non-existant]:')
    payload = {
        'device_id':TEST_MAC3,   
        'room_name' : 'test-room',
        'room_type' : 'test-type',
        'device_config' : [dc1, dc2, dc3, dc4]
    }
    post_it (url, payload)
        
def device_exits(): 
    print ('\ndevice exists?:')
    url = 'http://127.0.0.1:5000/device/exists'
    get_it (url, {'device_id':TEST_MAC1})
    print()       
    get_it (url, {'device_id':NON_EXIST_MAC})
    print()      
    get_it (url, {'device_id':TEST_MAC2})
 
        
def delete_device():
    print('\ndeleting device..')
    url = 'http://127.0.0.1:5000/delete/device'
    get_it (url, {'device_id':NON_EXIST_MAC})
    
#------------------------------------------------------

def set_device_data():
    print ('\nsetting device data..')
    url = 'http://127.0.0.1:5000/insert/device/data'
    simul_data = {"LIGHT":456, "TEMP":23, "HUMI":76}
    payload = {'device_id':TEST_MAC1, 'relay_status':'0101', 'data':simul_data} 
    post_it (url, payload)
    print()    
    payload = {'device_id':NON_EXIST_MAC, 'relay_status':'0101', 'data':simul_data} 
    post_it (url, payload)
  
def get_device_data():
    print ('\ngetting device data:')
    url = 'http://127.0.0.1:5000/get/device/data'
    get_it (url, {'device_id':TEST_MAC1})
    print() 
    get_it (url, {'device_id':NON_EXIST_MAC})
        
def set_device_status():        
    print ('\nsetting device status:')
    url = 'http://127.0.0.1:5000/insert/device/status'
    payload ={'device_id':TEST_MAC2, 'relay_status':'0101'}
    post_it (url, payload)
    

def get_device_status(): # TODO: add a method get_device_staus_real_time()
    print ('\ngetting device status:')
    url = 'http://127.0.0.1:5000/get/device/status'
    get_it (url, {'device_id':'TEST_MAC2'})
    
def set_device_event():
    print ('\ninserting device event..')
    url = 'http://127.0.0.1:5000/insert/device/event'
    eve_body = {'update':'failed', 'reason':'HTTP', 'code':400}
    payload = {'device_id':TEST_MAC1, 'event_type':'FW_UPDATE', 'event_body':eve_body}
    post_it (url, payload)
    
def get_device_event():
    print ('\ngetting device event:')
    url = 'http://127.0.0.1:5000/get/device/event'
    payload = {'device_id':TEST_MAC1}
    get_it (url, payload)
   
#-----------------------------------------------
# MAIN
#------------------------------------------------

print('\nAPI tester starting..')
get_root()
get_time()

echo_test()
delete_create_list_tables()

register_mobile()

insert_app_config()
get_app_config_GET()
get_app_config_POST()

list_hardware_types()
list_device_types()
list_room_types()

insert_device_types()
insert_room_types()

list_device_types()
list_room_types()
 
self_register_device() 
direct_insert_device() 
discover_new_devices()

provision_device()
list_hardware_types()

update_device_config()
get_device_config()

get_device_data()
set_device_data()
get_device_data()

get_device_status()
set_device_status()
get_device_status()

set_device_event()
get_device_event()   

list_active_devices() 
delete_device()
list_active_devices()  


print('\nBye!')



