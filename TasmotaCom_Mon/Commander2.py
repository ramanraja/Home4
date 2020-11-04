# MQTT Tasmota device controller
# pip install paho-mqtt

import paho.mqtt.client as mqtt
from random import randint
import threading
import json
import time
import sys

#------------------------------ globals ------------------------------
# server = 'broker.mqtt-dashboard.com'  # http://www.hivemq.com/demos/websocket-client/
# server = 'm2m.eclipse.org'
# server = 'test.mosquitto.org'
# server = 'localhost'                  # mosquitto -v
# port = 8000

server = 'localhost'    
port = 1883
client = None

device_name = 'simulator'
sub_topic_prefix = "stat"
sub_topic = "stat/#"
pub_topic_prefix = "cmnd"
pub_topic_suffix = 'POWER'  # this will be overriden
#------------------------------ callbacks ---------------------------- 

def on_connect(client, userdata, flags, rc):
    print('Connected to MQTT server  {}:{}'.format(server, port))
    client.subscribe (sub_topic, qos=0)  # on reconnection, it will automatically renew subscription
 
def on_publish(client, userdata, mid):
    print("Published msg id: {}".format(mid))

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed to {}; mid={}; granted QOS={}".format (sub_topic,mid,granted_qos))
    
def on_unsubscribe (client, userdata, mid):
    print("Unsubscribing from {}; mid={}".format (sub_topic,mid))

def on_message(client, userdata, msg):
    print ("{} => {}". format (msg.topic,msg.payload.decode()))
    
#---------------------------- main -----------------------------------

import sys
terminate = False

print ('Tasmota batch Commander. \nUsage: python commander  <commands_file_name>')
    
# note: if client ID is constant and clean_session=False, earlier subscriptions will still linger *     
client = mqtt.Client("myclient", clean_session=True) # if you make clean_session False, you will get weird messages!

# client.username_pw_set("User", "password")     

client.on_connect = on_connect
client.on_publish = on_publish
client.on_subscribe = on_subscribe
client.on_unsubscribe = on_unsubscribe
client.on_message = on_message

client.connect(server, port, keepalive=60)    # blocking call
#client.connect_async(server, port, keepalive=60)  # non blocking

# blocking call - reconnects automatically (useful esp. for mqtt listeners)
#client.loop_forever()    # blocking call

client.loop_start()       # start a background thread (useful if you are also an mqtt sender)
time.sleep(1)

cmd_file = 'commands.txt'
if len(sys.argv) > 1:
    cmd_file = sys.argv[1]
f = open(cmd_file, 'r') 
lines = f.readlines() 

print ('Executing commands. Press ^C to quit...')
try:
    for L in lines: 
        line = L.strip()
        if (len(line) == 0):
            continue
        sp = line.split(' ')
        print (sp)
        if (sp[0]=='device'):
            device_name = sp[1]
            client.unsubscribe (sub_topic)
            time.sleep(4)
            sub_topic = "{}/{}/#".format (sub_topic_prefix, device_name)
            client.subscribe (sub_topic, qos=0)
            time.sleep(4)
        else:
            pub_topic_suffix = sp[0]
            topic = '{}/{}/{}'.format (pub_topic_prefix, device_name, pub_topic_suffix)
            msg = ''
            if (len(sp) > 1):
                msg = sp[1]
            print (topic)
            print (msg)
            client.publish (topic, payload=msg, qos=0, retain=False)        
            time.sleep(3)        
            print()
except KeyboardInterrupt:
    print ('^C received.')
            
client.loop_stop()   # kill the background thread
client.disconnect()
time.sleep(1)   
print ('Main thread quits.')  



    