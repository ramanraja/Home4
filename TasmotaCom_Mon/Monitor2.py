# MQTT Tasmota device moniter
# pip install paho-mqtt

import paho.mqtt.client as mqtt
from datetime import datetime 
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
sub_topic = "stat/#"
sub_topic_prefix = "stat"  

pub_topic_prefix = "cmnd"
pub_topic_suffix = 'POWER'  # this may be overriden
#------------------------------ callbacks ---------------------------- 

def on_connect(client, userdata, flags, rc):
    print('Connected to MQTT server: ' +server)
    client.subscribe (sub_topic, qos=0)  # on reconnection, automatically renew
 
def on_publish(client, userdata, mid):
    print("Published msg id: "+str(mid))

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed to {}; mid={}; granted QOS={}".format (sub_topic,mid,granted_qos))
    
def on_unsubscribe (client, userdata, mid):
    print("Unsubscribing from {}; mid={}".format (sub_topic,mid))
        
def on_message(client, userdata, msg):
    ts = datetime.now() 
    print ('{}  {} => {}'.format (ts.strftime("%H:%M:%S"), msg.topic, msg.payload.decode())) 
    
#---------------------------- main -----------------------------------

import sys
terminate = False
print ('Tasmota device monitor. \nUsage: python monitor  <device_name>')
if len(sys.argv) > 1:
    sub_topic = '{}/{}/#'.format (sub_topic_prefix, sys.argv[1])
print ('sub topic: {}'.format(sub_topic))
         
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
print ('Press ^C to quit...')
try:
    while (True):
        time.sleep(2)
except KeyboardInterrupt:
    print ('^C received.')
      
client.loop_stop()   # kill the background thread   
client.disconnect()
time.sleep(1)   
print ('Main thread quits.')   



    