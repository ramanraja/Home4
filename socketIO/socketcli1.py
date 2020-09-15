# Python socket IO client 
# Test it with socketser1.py
# https://python-socketio.readthedocs.io/en/latest/client.html

# sync client:   pip install "python-socketio[client]"             
# Async client:  pip install "python-socketio[asyncio_client]"

import sys
import socketio
from time import sleep

sio = socketio.Client()   

@sio.event
def connect():
    print("Socket connected.")

@sio.event
def connect_error (info):
    print("Connection failed:")
    print (info)

@sio.event
def disconnect():
    print("Socket disconnected.")
    
@sio.event
def message(data):     # built in event
    print('Received message:')
    print (data)

@sio.on('update-count')
def on_message(data):  # custom event
    print('Received update-count event:')
    print (data)    


#-----------------------------------
# main
#-----------------------------------
 
print ('Trying to connect to socket server..') 
sio.connect('http://localhost:5000')
print('Connected. SID= ', sio.sid)
   
print ('Waiting for server events..')

while True:
    try:    
        sleep(0.5)
    except KeyboardInterrupt:
        break

# aliter:
#sio.wait()

sio.disconnect()
print ('Bye!')    