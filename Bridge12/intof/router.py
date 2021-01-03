# MQTT-Web socket bridge
# TODO: have a background thread to ping devices, look for new devices and build initial inventory
# Fixed: if the Hub app is not running while building the in_mem_devices, the client connection crashes and
#   re-establishes in an infinite loop !

from flask import current_app as app  # this is the way to import the app object
from intof import  mqtt, socketio
from flask import render_template, redirect
from flask import request
import requests
import json
from threading import Lock

# MQTT
subscribed = False       
SUB_TOPIC = 'stat/#'         
PUB_PREFIX = 'cmnd'
PUB_SUFFIX = 'POWER'
EMPTY_PAYLOAD = ''
BROADCAST_DEVICE = 'tasmotas'  # this is case sensitive **
BROADCAST_RELSEN = 'POWER0'    # get relay status of all the relays in a device 

# socket
client_count = 0         
CLIENT_EVENT = 'client-event'   # there is trouble with storing these in app.config
SERVER_EVENT = 'server-event'   # 'out of app-context' error is raised when retrieving
ACK_EVENT = 'ACK'  

# external database service
HUB_URL = 'http://localhost:5000/'
LIST_DEVICES = 'get/devices'
ACTIVE_DEVICE_SPEC_TREE = '/dump/active/device/spec/tree'
ACTIVE_RELSEN_TREE = '/get/active/relsen/tree'
RANDOM_TEST = 'random'

# thread
TERMINATE = False
PING_INTERVAL = 30
OFFLINE = 'offline'

in_mem_devices = None
in_mem_relsens = None
in_mem_status = None
is_online = None
new_devices = None

bgthread = None
thread_lock = Lock()
DEBUG_ENABLED = True

#--------------------------------------------------------------------------------------------
# daemon
#--------------------------------------------------------------------------------------------

def bgtask():
    dprint ('Entering backgrount thread...')
    while not TERMINATE:
        socketio.sleep (PING_INTERVAL)
        print ('\nWaking !...')
        for devid in is_online:
            if (not is_online[devid]):  # TODO: Make 3 attempts before declaring it offline
                send_offline_notification (devid)
        for devid in is_online:
            is_online[devid] = False    # reset for next round of checking   
        ping_mqtt()  # rebuild fresh status
    print ('Background thread terminates.')  
    
    
def start_daemon():    
    global bgthread
    print ('\nChecking daemon...')
    with thread_lock:
        if bgthread is None:  # as this should run only once
            print ('\nStarting background thread...\n')
            bgthread = socketio.start_background_task (bgtask)    
            
#--------------------------------------------------------------------------------------------
# Helpers
#--------------------------------------------------------------------------------------------
def dprint (*args):
    if DEBUG_ENABLED:
        print (*args)
        
        
def initialize_all():
    print ('\n+++++ this is the application initialization stub ! ++++++\n')
    subscribe_mqtt() # subscribing here is a safety net
    build_device_inventory()
    build_initial_status()  # to correctly light the buttons initially
    start_daemon()
        
    
def subscribe_mqtt():  
    global subscribed
    sub_topic = app.config['SUB_TOPIC']  # TODO: additional subscriptions like TELE
    print ('Subscribing to MQTT: %s' %(sub_topic))
    # do not check the 'subscribed' flag here: this may be a reconnect event!    
    mqtt.subscribe (sub_topic)     # duplicate subscriptions are OK
    subscribed = True  # tell socketIO not to subscribe again
    

# when a device responds:  
# if it is in the database and is enabled, add/update its status in the cache called in_mem_status
# if not, add/update it in the dormant cache called new_devices
# also mark the device as being online in the cache called is_online
def extract_status (message):
    global in_mem_status, is_online, new_devices
    sp = message.topic.split('/')
    #print ("Parsed: ", sp)
    if (not sp[2].startswith('POWER')):  # TODO: handle other messages also
        return None
    devid =sp[1] 
    rsid = sp[2]
    st = message.payload.decode()
    jstatus = {"device_id" : devid, "relsen_id" : rsid, "status" : st}
    print ('JSTATUS:', jstatus)
    if not devid in in_mem_devices:  # unregistered/ disabled device found; cache them in a separate structure
        if not devid in new_devices:
            new_devices[devid] = []
        if (not rsid in new_devices[devid]): # avoid duplicate relsens!
            new_devices[devid].append(rsid)
        return None  # do not process unregistered devices any further
        
    # device is in the database, is enabled, but not in the in_mem_status cache yet:
    if not devid in in_mem_status:   # this acts as device discovery
        in_mem_status[devid] = {}    # add the newly discovered device as the key
    in_mem_status[devid][rsid] = st  
    is_online[devid] = True # this creates the key, if not already existing
    return jstatus


# Ping:= just see which of your devices are responding
# only get the first relay's status of all devices that are online;
# (they may be in the database or not, enabled or not)  
def ping_mqtt():
    print ('\nPinging MQTT...')
    topic = '{}/{}/{}'.format (PUB_PREFIX, BROADCAST_DEVICE, PUB_SUFFIX) # POWER
    print (topic, ' (blank)')
    mqtt.publish (topic, '')   # empty payload
               
               
# trace the status of ALL relays in all devices that are online; 
# (they may be in the database or not, enabled or not)                       
def send_tracer_broadcast():  
    topic = '{}/{}/{}'.format (PUB_PREFIX, BROADCAST_DEVICE, BROADCAST_RELSEN) # POWER0
    print ('Sending probe to: ',topic)
    mqtt.publish (topic, EMPTY_PAYLOAD)  # empty payload gets the relay status


def send_offline_notification (devid):
    print ('sending offline notification for: ', devid)
    for rs in in_mem_relsens[devid]:
        msg = {'device_id':devid, 'relsen_id':rs, 'status' : OFFLINE}
        socketio.emit (SERVER_EVENT, msg)
    
#--------------------------------------------------------------------------------------------
# Build in-memory structures
#--------------------------------------------------------------------------------------------

# download the device configs and relsen list of enabled devices in the database and cache them
def build_device_inventory():  
    global in_mem_relsens, in_mem_devices, new_devices
    try:
        print ('\nbuilding [enabled] in-memory devices..')
        new_devices = {}
        resp = requests.get (HUB_URL + ACTIVE_DEVICE_SPEC_TREE)
        if (resp): 
            in_mem_devices = resp.json()
            print ("in-memory devices:")
            print (in_mem_devices)
            print ('-'*30)
        else:
            print ('Error: Could not build in-memory devices')
            return False
        print ('\nbuilding [enabled] in-memory relsens..')
        resp = requests.get (HUB_URL + ACTIVE_RELSEN_TREE)
        if (resp):
            in_mem_relsens = resp.json()   
            print ("in-memory relsens:")
            print (in_mem_relsens)
            print ('-'*30)
            return True
        else:
            print ('Error: Could not build in-memory relsons')
            return False
    except Exception as e:
        print ('* EXCEPTION 1: ',str(e))            
    return False


def build_initial_status():   
    # TODO: get the initial sensor readings also 
    global in_mem_status, is_online
    is_online = {}       # global
    in_mem_status = {}   # global
    try:
        if (in_mem_devices is None or in_mem_relsens is None): # safety check
            res = build_device_inventory()
            if (not res):
                return False
        for devid in in_mem_devices:
            is_online[devid] = False  
        for devid in in_mem_relsens:  # devid is the JSON key  
            in_mem_status[devid] = {}
            for rsid in in_mem_relsens[devid]:  # iterate the list 
                in_mem_status[devid][rsid] = OFFLINE  # this value is always a string (even for sensor data)
        print ('initial in-memory status:')
        print (in_mem_status)
        send_tracer_broadcast() # priming read of status of all online devices (in the database or not)
        return True
    except Exception as e:
        print ('* EXCEPTION 2: ',str(e))
    return False


#--------------------------------------------------------------------------------------------
# MQTT
#--------------------------------------------------------------------------------------------
###mqtt._connect_handler = on_mqtt_connect

# There is trouble with this callback!
@mqtt.on_connect()  
def on_mqtt_connect (client, userdata, flags, rc):
    print ('\n***** Connected to MQTT broker. *****\n')
    subscribe_mqtt()

@mqtt.on_message()
def on_mqtt_message (client, userdata, message):
    #print ("MQTT msg: ", message.payload.decode())
    jstatus = extract_status (message)
    if (jstatus):
        try:
            #print ('Sending to socket: ', jstatus)
            socketio.emit (SERVER_EVENT, jstatus)
        except Exception as e:
            print ('* EXCEPTION 3: ', str(e))
            
#--------------------------------------------------------------------------------------------
# Socket IO
#--------------------------------------------------------------------------------------------
    
@socketio.on('connect')
def on_socket_connect ():
    global client_count
    client_count = client_count +1
    msg = 'A socket client connected. Client count: {}'.format(client_count) 
    print ('\n **', msg)    
    ### my_startup_function() # TODO: will this be called even if the socket alone connects (without a HTTP page request)?
    try:
        socketio.send (msg)
        send_tracer_broadcast()  # get initial button status for display
    except Exception as e:
        print ('* EXCEPTION 4: ', str(e))
    
    
@socketio.on('disconnect')
def on_socket_disconnect():
    global client_count
    if (client_count > 0):
        client_count = client_count-1
    else:
        print ('\n******** Oops! Client count is negative! *********\n')
    print ('A client disconnected. Active count= {}'.format(client_count))
 

@socketio.on (CLIENT_EVENT)   
def on_socket_event (payload):
    print ('command: ', payload)
    jcmd = json.loads (payload)
    topic = '{}/{}/{}'.format (PUB_PREFIX, jcmd['device_id'], jcmd['relsen_id'])
    #print (topic, jcmd['action'])
    try:
        mqtt.publish (topic, jcmd['action'])
        socketio.emit (ACK_EVENT, jcmd)  # must be a json object, to avoid messy client side escape characters 
    except Exception as e:
        print ('* EXCEPTION 5: ', str(e))


# bridge: send any arbitrary MQTT message to any arbitrary topic
@socketio.on('message')
def on_socket_message (message):
    print ('pass-through message: ', message)
    jcmd = json.loads (message)
    try:
        mqtt.publish (jcmd.get('topic'), jcmd.get('payload'))
        socketio.emit (ACK_EVENT, jcmd)  # must be a json object, to avoid messy client side escape characters   
    except Exception as e:
        print ('* EXCEPTION 6: ', str(e))

#--------------------------------------------------------------------------------------------
# Flask
#--------------------------------------------------------------------------------------------
# a series of backup measures, in case the startup initialization fails
@app.before_first_request 
def my_startup_function(): # TODO: will this be called even if the socket connects without a HTTP page request?
    print ("\n* I am invoked before the first HTTP client call..*\n")
    if (not subscribed):  
        subscribe_mqtt() # subscribing here is a safety net
    if (in_mem_devices is None or in_mem_relsens is None):
        build_device_inventory()
    if in_mem_status is None or is_online is None:
        build_initial_status()  
    if bgthread is None: 
        start_daemon()
            
@app.route('/random', methods=['GET'])
def cross_site_test():
    print ('\ntesting the Hub app...')
    resp = requests.get (HUB_URL + RANDOM_TEST)
    return resp.json()  # resp.text   
                
# buttons to control a real device            
@app.route('/')
@app.route('/index')
def rooot():
    return render_template ('controller.html') 
   
# unit tests and API documentation
@app.route('/menu')
def menu():
    return render_template ('menu.html') 
        
# socket to MQTT bridge; you can send an arbitrary MQTT payload to any topic      
# CAUTION: This is a remote trap door from the Internet to your local MQTT server!
@app.route('/bridge')
def bridge():
    return render_template ('bridge.html') 
            
@app.route('/ping/socket', methods=['GET'])
def ping_socket():
    print ('\nPinging socket...')
    socketio.send ('Ping!')  # broadcast=True is implied
    #return render_template('toggle.html')   
    return ({'result' : 'Ping sent to socket client'})
                
# Ping: just see which of your devices are responding
# only get the first relay status of all devices online, enabled or not          
@app.route('/ping/mqtt', methods=['GET'])  
def ping_mqtt_devices():
    ping_mqtt()
    return ({'result' : 'MQTT Ping sent to all online devices'})

# get the status of ALL relays of all devices online, enabled or not        
@app.route('/send/tracer', methods=['GET']) # send a broadcast to syncup all devices
def send_tracer():
    print('\nsending tracer broadcast..')    
    send_tracer_broadcast()
    return ({'result' : 'tracer broadcast sent'})  
    
# all device ids from your database, enabled or not; online or offline    
@app.route('/get/device/ids', methods=['GET'])
def get_device_id_list():
    print ('\ngetting registered device ids from  your database...')
    resp = requests.get (HUB_URL + LIST_DEVICES) 
    return resp.json()  # resp.text  
  
# download the device config and relsen list (only enabled devices) from the database and rebuild the cache
@app.route('/build/device/inventory', methods=['GET'])
def build_active_device_inventory():
    print ('\nbuilding active device inventory...')
    res = build_device_inventory()
    if res:
        return ({'result':'successfully created in-memory devices'})
    return ({'error' : 'could not build device inventory'})
    
# just return the cached in-memory device configs (only enabled devices, and in the database)    
@app.route('/get/mem/devices', methods=['GET'])
def get_devices():
    print('\nReturning in-memory devices..')
    if not in_mem_devices:
        return {'error' : 'in-memory devices are not available'}
    return in_mem_devices 
    
# just return the cached in-memory relsen list (only from enabled devices, found in the database)        
@app.route('/get/mem/relsens', methods=['GET'])
def get_relsens():
    print('\nReturning in-memory relsens..')
    if not in_mem_relsens:
        return {'error' : 'in-memory relsens are not available'}
    return in_mem_relsens 
    
# return the last known status (ON/OFF/offline) of devices that are in the database and are enabled
@app.route('/get/status', methods=['GET'])
def get_status():
    print('\nReturning in-memory status of registered and active devices..')
    if in_mem_status is None:
        send_tracer_broadcast()  # to build the status
        return {'error' : 'in-memory status is not available; please try again'}
    return in_mem_status 

# return the last known online status [True/False] of devices that are in the database and are enabled 
@app.route('/get/online/status', methods=['GET'])
def get_online_status():
    print('\nReturning online status of registered and active devices..')
    if is_online is None:
        send_tracer_broadcast()  # to build the online status
        return {'error' : 'online status is not available; please try again'}
    return is_online 
    
# return the list of devices that are online, found in the database and are enabled     
@app.route('/get/online/devices', methods=['GET'])   
def get_online_devices():
    print('\nReturning online devices..')
    if not is_online:
        ping_mqtt()
        return {'error' : 'online status is not available; please try again'}
    online = {'online_devices' : []}
    for devid in in_mem_status:   
        if is_online[devid]:
            online['online_devices'].append (devid)
    return online 
        
# return the list of devices that are offline, found in the database and are enabled             
@app.route('/get/offline/devices', methods=['GET'])  
def get_offline_devices():
    print('\nReturning online devices..')
    if is_online is None:  # the list is not yet created
        ping_mqtt()
        return {'error' : 'online status is not available; please try again'}
    offline = {'offline_devices' : []}
    for devid in in_mem_status:   
        if not is_online[devid]:
            offline['offline_devices'].append (devid)    
    return offline 
                
# get the device ids & relsen list of unregistered or disabled devices, that are sending data                
@app.route('/discover/devices', methods=['GET'])
def discover_devices():
    print('\nReturning relsen list of new (unregistered/ disabled) devices..')
    if not new_devices:
        return {'error' : 'new device list is not available; please try again'}
    return new_devices             

# get the device ids of unregistered or disabled devices, that are sending data                
@app.route('/get/new/devices', methods=['GET'])  
def get_new_devices():
    print('\nReturning the ids of new (unregistered/ disabled) devices..')
    if not new_devices:
        return {'error' : 'new device list is not available; please try again'}
    newdev = []
    for k in new_devices.keys():
        newdev.append(k)    
    return {'new_devices' : newdev}