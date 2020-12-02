####from intof import app
from intof import  mqtt, socketio
from flask import current_app as app  # this is the trick to import ! *
from flask import request
from flask import render_template, redirect
import json

NUM_RELAYS = 4           # TODO: revisit in the full version of Hub
device_id = 'simulator'  # initial place holder

# MQTT
subscribed = False       
SUB_TOPIC = 'stat/#'         
PUB_PREFIX = 'cmnd'
PUB_SUFFIX = 'POWER'       

# socket
client_count = 0         
CLIENT_EVENT = 'client-event'   # there is trouble with storing these in app.config
SERVER_EVENT = 'server-event'   # 'out of app-context' error is raised when retrieving
ACK_EVENT = 'ACK'  

#--------------------------------------------------------------------------------------------
# Helpers
#--------------------------------------------------------------------------------------------

def get_initial_status():
    # TODO: get the initial  device id from the client
    for rel in range(1, NUM_RELAYS+1):
        topic = '{}/{}/{}{}'.format (PUB_PREFIX, device_id, PUB_SUFFIX, rel)   
        mqtt.publish (topic, '')  # empty payload to get the initial relay status


def extract_status (message):
    global device_id
    sp = message.topic.split('/')
    print ("Parsed: ", sp)
    if (sp[1] != device_id):
        return None
    if (not sp[2].startswith('POWER')):
        return None
    relay_num_char = sp[2][-1]
    relay_num = 1    
    # ASSUMPTION: there can be no more than 9 relays per device **
    if (relay_num_char >= '1' and relay_num_char <= '9'): 
        relay_num = int(relay_num_char)
    device_id = sp[1]  # TODO: revisit this
    jstatus = {"device_id" : device_id, "relay" : relay_num, "status" : message.payload.decode()}
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
            #socketio.emit ('server-event', jstatus)
        except Exception as e:
            print ('* EXCEPTION: ', str(e))
            
#--------------------------------------------------------------------------------------------
# Socket IO
#--------------------------------------------------------------------------------------------
    
@socketio.on('connect')
def on_socket_connect ():
    global  subscribed, client_count
    print ('\n***** A client onnected to socket. *****\n')
    client_count = client_count +1
    if (not subscribed):
        sub_topic = app.config['SUB_TOPIC']
        print ('Subscribing to MQTT: %s' %(sub_topic))
        mqtt.subscribe(sub_topic)    # duplicate subscriptions are OK
        subscribed = True
    msg = 'Socket connected. Client count: {}'.format(client_count) 
    print (msg)    
    try:
        socketio.send (msg)      
        get_initial_status()
    except Exception as e:
        print ('* EXCEPTION: ', str(e))
    
    
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
    relay_number = '1'
    if (jcmd['relay']):
        relay_number = str(jcmd['relay'])
    device_id = jcmd['device_id']  # save it for future filtering of messages
    topic = '{}/{}/{}{}'.format (PUB_PREFIX, device_id, PUB_SUFFIX, relay_number)
    print (topic, jcmd['action'])
    try:
        mqtt.publish (topic, jcmd['action'])
        socketio.emit (ACK_EVENT, jcmd)  # must be a json object, to avoid messy client side escape characters 
    except Exception as e:
        print ('* EXCEPTION: ', str(e))


# bridge: send any arbitrary message to any arbitrary topic
@socketio.on('message')
def on_socket_message (message):
    print ('pass-through message: ', message)
    jcmd = json.loads (message)
    try:
        mqtt.publish (jcmd.get('topic'), jcmd.get('payload'))
        socketio.emit (ACK_EVENT, jcmd)  # must be a json object, to avoid messy client side escape characters   
    except Exception as e:
        print ('* EXCEPTION: ', str(e))

        
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
    