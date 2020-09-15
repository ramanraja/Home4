# Python socket IO client 
# Test it with socketser2.py
# https://python-socketio.readthedocs.io/en/latest/client.html

# sync client:   pip install "python-socketio[client]"             
# Async client:  pip install "python-socketio[asyncio_client]"

import sys
import socketio
##from time import sleep

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
def message(data):      # built in event
    print('Received message:')
    print (data)

@sio.on('update-count') # custom event
def on_message(data):
    print('Received update-count event:')
    print (data)    


#-----------------------------------
# main
#-----------------------------------
 
connected = False 
print ('Trying to connect to socket server..')
 
while True: 
    try: 
        sio.connect('http://localhost:5000')
        connected = True
        print('Connected. SID= ', sio.sid)
        break;
    except KeyboardInterrupt:
        break
    except Exception:
        pass
                    
if not connected:
    print ('Connection failed.')
    sys.exit(0)
                       
print ('Waiting for server events..[^C to quit]')

while True:
    try:    
        sio.sleep(0.5)
    except KeyboardInterrupt:
        break

# aliter:
#sio.wait()

sio.disconnect()
print ('Bye!')    
