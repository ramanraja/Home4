


    
#--------------------------------------------------------------

# Flask web server running on the hub to interact with mobile app
# POST a json payload to http://127.0.0.1:5000/xxx
# TODO:
#  Integrate Flask-MQTT ? OR/AND..
#  ...study web sockets **
#  Test thie on MySql
#  Verify the token in coockie and raise error on expiry date
#  Decorator @require_login and @require_admin for the admin functions like create_tables()
#  button press to trigger register_device mode for 60 seconds
#  Add @require_login to check validity of token
#  get_device_schedule(mac_id),  set_device_schedule(), get_all_schedules()
#  Maintain a schedule for every relay. There will be a flag 'daily'=yes (or no for one time event)
#  MQTT client calls get_schedules() at every hour and fires on/off events  accordingly
#  Maintain a list of devices that are online (use python 'Set' data type) ; this is culled from the
#     events and data packets; some of them may be new devices waiting to be configured
#  Add a /list/devices/debug method. This will return additional information like
#     hardware and firmware version for the devices
'''
@app.route('/todo/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = [t for t in task_list1 if t['id'] == task_id]
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})
'''

# pip uninstall jwt   # this is the wrong package ! UNINSTALL it, if present
# pip install pyjwt   # install this package

import jwt
from flask import Flask,abort
from flask import request, make_response
from datetime import datetime, timedelta
import PasswordStore
import MariaWrapper  

app = Flask("Intof Hub")

def dprint (*args):
    if debug:
        print (*args)
        
@app.route('/', methods=['GET'])
def get_root():
    dprint ('\nRequest: ', request)
    retval = {'message' : 'Welcome to Intof Hub', 'version' : '1.0'} 
    return (retval)


@app.route('/get/time', methods=['GET'])
def get_time():
    dprint ('\nRequest: ', request)
    time = db.getTimeStamp()
    retval = {'local_time' : time}
    dprint (retval)
    return (retval)
    
    
@app.route('/echo', methods=['GET','POST'])
def echo_input():
    dprint ('\nRequest: ', request)
    if request.json is None:
        retval = {'input' : 'NULL'}
    else:
        retval = request.json
    dprint (retval)
    return (retval)

        
# TODO: the following calls need admin access decorator    
@app.route('/create/tables', methods=['GET'])
def create_all_tables ():
    dprint ('\nRequest: ', request)
    retval = {'result' : 'tables created'}
    try:
        db.createTables()                 
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)
        
        
@app.route('/delete/tables', methods=['GET'])        
def drop_all_tables():
    dprint ('\nRequest: ', request)
    retval = {'result' : 'tables removed'}
    try:
        db.dropTables()            
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)
                
    
@app.route('/list/tables', methods=['GET'])        
def list_tables():
    dprint ('\nRequest: ', request)
    try:
        retval = db.listTables()
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)    
#-------------------------------------------------------------------------------------------------------    
    
@app.route('/register/mobile', methods=['GET','POST'])
def register_mobile(): 
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'input json is NULL'})
    jtoken = {}
    jtoken['code'] = 200    
    payload = {}
    if 'user_id' in request.json:
        payload['user_id'] = request.json['user_id']
    else:
        jtoken ['registration'] = 'failure'
        jtoken ['error'] = 'user id is required'
        return  (jtoken)    
    if 'app_id' in request.json:
        payload['app_id'] = request.json['app_id']
    else:
        jtoken ['registration'] = 'failure'
        jtoken ['error'] = 'app id is required'
        return  (jtoken)     
    if 'version' in request.json:
        payload['version'] = request.json['version']
    else:
        payload['version'] = '1.0'
    try :
        payload['hub_id'] = PasswordStore.hub_id
        expiry_date = datetime.now() + timedelta(days=PasswordStore.jwt_life_time)
        payload ['exp'] = expiry_date
        token = jwt.encode (payload, PasswordStore.jwt_secret, PasswordStore.jwt_algorithm)
        token = token.decode('utf-8')
        print (token)
        jtoken ['registration'] = "success"
        jtoken ['token'] = token
        jtoken['expiry'] = expiry_date
        return  (jtoken)
    except Exception as e:
        jtoken ['registration'] = 'failure'
        jtoken ['error'] = str(e)
        return  (jtoken)
    
#-------------------------------------------------------------------------------------------------------    
        
@app.route('/insert/app/config', methods=['GET','POST'])
def insert_config_item():
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'config object is NULL'})
    dprint (request.json)
    try:
        retval = db.insertAppConfig (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)          
# NOTE: there is no update/app/config. You have to delete the item from the
# back end and insert a new one.    
    
    
@app.route('/get/app/config', methods=['GET','POST'])
def get_config_item():
    dprint ('\nRequest: ', request)
    try:    
        if request.json is not None:
            reqj = request.json
        else:
            if (len(request.args) ==0):
                raise Exception ('config_id is required')
            dprint (request.args)
            reqj = {'config_id' : request.args['config_id']} # convert the GET parameter to valid json
        dprint (reqj)
        retval = db.getAppConfig (reqj)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval) 
    
#----------------------------------------------------------------------- 


@app.route('/self/register/device', methods=['GET','POST'])
def self_register_device():
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'device is NULL'})
    dprint (request.json)
    try:
        retval = db.registerDevice (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
     

@app.route('/insert/device', methods=['GET','POST'])
def direct_insert_device(): # called from back end for bulk provisioning
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'device is NULL'})
    dprint (request.json)
    try:
        retval = db.directInsertDevice (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
    
    
@app.route('/provision/device', methods=['GET','POST'])
def provision_device():  # this is for onboarding the device
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'device is NULL'})
    try:
        retval = db.provisionDevice (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
    
       
@app.route('/discover/devices', methods=['GET']) 
def discover_new_devices():
    dprint ('\nRequest: ', request)
    try:
        retval = db.getNewDevices ()
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
    
   
@app.route('/list/active/devices', methods=['GET'])      
def list_active_devices():    
    dprint ('\nRequest: ', request)
    try:
        retval = db.getActiveDevices ()
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  


@app.route('/list/inactive/devices', methods=['GET'])      
def list_inactive_devices():    
    dprint ('\nRequest: ', request)
    try:
        retval = db.getInactiveDevices ()
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval) 
    
#-------------------------------------------------------------------------------

@app.route('/device/exists', methods=['GET']) 
def does_device_exit(): 
    dprint ('\nRequest: ', request)
    try:    
        if request.json is not None:
            reqj = request.json
        else:
            if (len(request.args)==0):
                raise Exception ('device_id is required')
            dprint (request.args)
            reqj = {'device_id' : request.args['device_id']} # convert the GET parameter to valid json
        dprint (reqj)
        retval = db.deviceExists (reqj)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
  
    
@app.route('/delete/device', methods=['GET']) 
def delete_device():
    dprint ('\nRequest: ', request)
    try:    
        if request.json is not None:
            reqj = request.json
        else:
            if (len(request.args)==0):
                raise Exception ('device_id is required')
            dprint (request.args)
            reqj = {'device_id' : request.args['device_id']} # convert the GET parameter to valid json
        dprint (reqj)
        retval = db.deleteDevice (reqj)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  

 
@app.route('/get/device/config', methods=['GET']) 
def get_device_config():
    dprint ('\nRequest: ', request)
    try:    
        if request.json is not None:
            reqj = request.json
        else:
            if (len(request.args)==0):
                raise Exception ('device_id is required')
            dprint (request.args)
            reqj = {'device_id' : request.args['device_id']} # convert the GET parameter to valid json
        dprint (reqj)
        retval = db.getDeviceConfig (reqj)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
     

@app.route('/update/device/config', methods=['GET', 'POST']) 
def update_device_config(): 
    dprint ('\nRequest: ', request)
    if request.json is None:
        return  ({'error' : 'device type list is NULL'})
    dprint (request.json)
    try:
        retval = db.insertDeviceConfig (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  

#---------------------------------------------------------------------------------            

@app.route('/update/device/types', methods=['GET','POST'])
def insert_device_types():
    dprint ('\nRequest: ', request)
    if request.json is None:
        return  ({'error' : 'device type list is NULL'})
    dprint (request.json)
    try:
        retval = db.insertDeviceTypes (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
        
        
@app.route('/list/device/types', methods=['GET'])
def list_device_types():
    dprint ('\nRequest: ', request)
    try:
        retval = db.getDeviceTypes ()
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
    
        
@app.route('/update/room/types', methods=['GET','POST'])
def insert_room_types():
    dprint ('\nRequest: ', request)
    try:
        if request.json is None:
            return  ({'error' : 'room type list is NULL'})
        dprint (request.json)
        retval = db.insertRoomTypes (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
    
    
@app.route('/list/room/types', methods=['GET'])
def list_room_types():
    dprint ('\nRequest: ', request)
    try:
        retval = db.getRoomTypes ()
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)              
    
    
@app.route('/list/hardware/types', methods=['GET'])
def list_hardware_types():
    dprint ('\nRequest: ', request)
    try:
        retval = db.getHardwareTypes ()
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)          

#-----------------------------------------------------------------------------
    
@app.route('/insert/device/data', methods=['GET','POST'])
def insert_device_data():
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'device data is NULL'})
    dprint (request.json)
    try:
        retval = db.insertDeviceData (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)        


@app.route('/get/device/data', methods=['GET','POST'])
def get_device_data():
    dprint ('\nRequest: ', request)
    try:    
        if request.json is not None:
            reqj = request.json
        else:
            if (len(request.args)==0):
                raise Exception ('device_id is required')
            dprint (request.args)
            reqj = {'device_id' : request.args['device_id']} # convert the GET parameter to valid json
        dprint (reqj)
        retval = db.getDeviceData (reqj)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)  
    
 
@app.route('/insert/device/status', methods=['GET','POST']) 
def insert_device_status():
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'device data is NULL'})
    dprint (request.json)
    try:
        retval = db.insertDeviceStatus (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval) 
    
    
@app.route('/get/device/status', methods=['GET','POST'])    
def get_device_status():
    dprint ('\nRequest: ', request)
    try:    
        if request.json is not None:
            reqj = request.json
        else:
            if (len(request.args)==0):
                raise Exception ('device_id is required')
            dprint (request.args)
            reqj = {'device_id' : request.args['device_id']} # convert the GET parameter to valid json
        dprint (reqj)
        retval = db.getDeviceStatus (reqj)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)                
    
    
@app.route('/insert/device/event', methods=['GET','POST'])
def insert_device_event():
    dprint ('\nRequest: ', request)
    if request.json is None:
        return ({'error' : 'device event is NULL'})
    dprint (request.json)
    try:
        retval = db.insertDeviceEvent (request.json)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)     
    
    
@app.route('/get/device/event', methods=['GET','POST'])    
def get_device_event():
    dprint ('\nRequest: ', request)
    try:    
        if request.json is not None:
            reqj = request.json
        else:
            if (len(request.args)==0):
                raise Exception ('device_id is required')
            dprint (request.args)
            reqj = {'device_id' : request.args['device_id']} # convert the GET parameter to valid json
        dprint (reqj)
        retval = db.getDeviceEvent (reqj)
    except Exception as e:
        retval = {'error' : str(e)} 
    dprint (retval)
    return (retval)     
    
#-----------------------------------------------------------------
# MAIN
#-----------------------------------------------------------------

debug = True
db = MariaWrapper.MariaWrapper (debug=True)
if not db.connect ():
    print ('\n** Failed to connect to MariaDB database **') 
    print ('\n* Cannot start Web Server. *')
else:
    print("local time:")
    print(db.getTimeStamp ())    
    app.run(host="0.0.0.0", port=5000, debug=True)
print ('Bye!')    
    
'''-----------------------------------------------------------------
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
-----------------------------------------------------------------'''    

 