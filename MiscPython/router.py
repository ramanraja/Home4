# MQTT-Web socket bridge
# TODO: have a background thread to ping devices, look for new devices and build initial inventory
# TODO: make the device_id as the key, and a json containing relsen_id and status as its value.
# TODO: if the Hub app is not running while building the in_mem_devices, the client connection crashes and
#   re-establishes in an infinite loop !

####from intof import app  -> does not work
from intof import  mqtt, socketio
from flask import current_app as app  # this is the trick to import the app object ! ***
from flask import render_template, redirect
from flask import request
import requests
import json

#NUM_RELAYS = 4           # TODO: revisit in the full version of Hub
#device_id = 'simulator'  # initial place holder

# MQTT
subscribed = False       
SUB_TOPIC = 'stat/#'         
PUB_PREFIX = 'cmnd'
PUB_SUFFIX = 'POWER'
PUB_PAYLOAD = ''

# socket
client_count = 0         
CLIENT_EVENT = 'client-event'   # there is trouble with storing these in app.config
SERVER_EVENT = 'server-event'   # 'out of app-context' error is raised when retrieving
ACK_EVENT = 'ACK'  

HUB_URL = 'http://localhost:5000/'
in_mem_devices = None
in_mem_relsens = None
in_mem_status = None

#--------------------------------------------------------------------------------------------
# Helpers
#--------------------------------------------------------------------------------------------

def build_device_inventory():  # TODO: do this in a background thread, not in an event handler
    global in_mem_relsens, in_mem_devices
    try:
        print ('building in-memory devices..')    
        resp = requests.get (HUB_URL +'/dump/active/device/spec/tree')
        if (resp): 
            in_mem_devices = resp.json()
            print ("in-memory devices:")
            print (in_mem_devices)
            print ('-'*30)
        else:
            print ('Error: Could not build in-memory devices')
            return False
        print ('building in-memory relsens..')
        resp = requests.get (HUB_URL +'/get/active/relsen/tree')
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


def build_initial_status():  # TODO: do this in a background thread, not in an event handler
    # TODO: get the initial sensor readings also 
    global in_mem_status
    try:
        if (in_mem_devices is None or in_mem_relsens is None):
            res = build_device_inventory()
            if (not res):
                return False
        in_mem_status = {}   # global
        for devid in in_mem_relsens:  # devid is the JSON key   
            in_mem_status[devid] = {}
            for rsid in in_mem_relsens[devid]:  # iterate the list 
                in_mem_status[devid][rsid] = 'offline'  # this value is always a string (even for sensor data)
        print ('in-memory status:')
        print (in_mem_status)
        for devid in in_mem_status:  # devid is the JSON key
            for rsid in in_mem_status[devid]:  # rsid is the JSON key
                topic = '{}/{}/{}'.format (PUB_PREFIX, devid, rsid)   
                print ('Sending probe to: ',topic)
                mqtt.publish (topic, '')  # empty payload gets the relay status
        return True
    except Exception as e:
        print ('* EXCEPTION 2: ',str(e))
    return False


def extract_status (message):
    global device_id, relsen_id, in_mem_status
    sp = message.topic.split('/')
    print ("Parsed: ", sp)
    if (not sp[2].startswith('POWER')):
        return None
    devid =sp[1] 
    rsid = sp[2]
    st = message.payload.decode()
    jstatus = {"device_id" : devid, "relsen_id" : rsid, "status" : st}
    print ('JSTATUS: ', jstatus)
    print ('saving it in-memory..')
    if not devid in in_mem_status:
        in_mem_status[devid] = {}
    in_mem_status[devid][rsid] = st  
    print ('saved: ', in_mem_status[devid])
    return jstatus
    
#--------------------------------------------------------------------------------------------
# MQTT
#--------------------------------------------------------------------------------------------
###mqtt._connect_handler = on_mqtt_connect

# There is trouble with this callback!
@mqtt.on_connect()  
def on_mqtt_connect (client, userdata, flags, rc):
    global  subscribed
    print ('\n***** Connected to MQTT broker. *****\n')
    sub_topic = app.config['SUB_TOPIC']
    print ('Subscribing to %s' %(sub_topic))
    # do not check the 'subscribed' flag here: this may be a reconnect!    
    mqtt.subscribe (sub_topic)     # duplicate subscriptions are OK
    subscribed = True  # tell socketIO not to subscribe again
    topic = '{}/{}/{}'.format (PUB_PREFIX, device_id, PUB_SUFFIX)
    print (topic, ' (blank)')
    mqtt.publish (topic, ' ')   # probe if the device is alive


@mqtt.on_message()
def on_mqtt_message (client, userdata, message):
    print ("MQTT msg: ", message.payload.decode())
    jstatus = extract_status (message)
    if (jstatus):
        try:
            print ('Sending to socket: ', jstatus)
            socketio.emit (SERVER_EVENT, jstatus)
        except Exception as e:
            print ('* EXCEPTION 3: ', str(e))
            
#--------------------------------------------------------------------------------------------
# Socket IO
#--------------------------------------------------------------------------------------------
    
@socketio.on('connect')
def on_socket_connect ():
    global subscribed, client_count
    print ('\n***** A client onnected to socket. *****\n')
    client_count = client_count +1
    if (in_mem_devices is None or in_mem_relsens is None):
        build_device_inventory()
    if (not subscribed):  
        sub_topic = app.config['SUB_TOPIC']
        print ('Subscribing to MQTT: %s' %(sub_topic)) # subscribing here is a safety net
        mqtt.subscribe(sub_topic)    # duplicate subscriptions are OK
        subscribed = True
    msg = 'Socket connected. Client count: {}'.format(client_count) 
    print (msg)    
    try:
        socketio.send (msg)      
        build_initial_status()  # to correctly light the buttons initially
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
    global device_id
    print ('command: ', payload)
    jcmd = json.loads (payload)
    device_id = jcmd['device_id']
    topic = '{}/{}/{}'.format (PUB_PREFIX, jcmd['device_id'], jcmd['relsen_id'])
    print (topic, jcmd['action'])
    try:
        mqtt.publish (topic, jcmd['action'])
        socketio.emit (ACK_EVENT, jcmd)  # must be a json object, to avoid messy client side escape characters 
    except Exception as e:
        print ('* EXCEPTION 5: ', str(e))


# bridge: send any arbitrary message to any arbitrary topic
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
@app.route('/')
def index():
    return render_template('toggle.html')

@app.route('/ping/mqtt', methods=['GET'])
def ping_mqtt():
    print ('Pinging MQTT...')
    topic = '{}/{}/{}'.format (PUB_PREFIX, device_id, PUB_SUFFIX)
    print (topic, ' (blank)')
    mqtt.publish (topic, ' ')   # probe if the device is alive
    return render_template('toggle.html')        

@app.route('/ping/socket', methods=['GET'])
def ping_socket():
    print ('Pinging socket...')
    socketio.send ('Ping!')  # broadcast=True is implied
    return render_template('toggle.html')   
    
@app.route('/test', methods=['GET'])
def cross_site_test():
    print ('testing the Hub app...')
    resp = requests.get (HUB_URL +'test')
    return resp.json()  # resp.text   
    
@app.route('/get/device/ids', methods=['GET'])
def get_device_id_list():
    print ('getting device ids...')
    resp = requests.get (HUB_URL +'list/devices')
    return resp.json()  # resp.text  
    
@app.route('/build/device/inventory', methods=['GET'])
def build_active_device_inventory():
    print ('building active device inventory...')
    res = build_device_inventory()
    if res:
        return ({'result':'successfully created in-memory devices'})
    return ({'error' : 'could not get device inventory'})
    
@app.route('/get/devices', methods=['GET'])
def get_devices():
    print('Returning in-memory devices..')
    if not in_mem_devices:
        return {'error' : 'in-memory devices are not available'}
    return in_mem_devices 
    
@app.route('/get/relsens', methods=['GET'])
def get_relsens():
    print('Returning in-memory relsens..')
    if not in_mem_relsens:
        return {'error' : 'in-memory relsens are not available'}
    return in_mem_relsens 
    
@app.route('/get/status', methods=['GET'])
def get_status():
    print('Returning in-memory status..')
    if not in_mem_status:
        return {'error' : 'in-memory status is not available'}
    return in_mem_status 
        