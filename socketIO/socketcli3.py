# Python socket IO client through Nginx
# Test it with socketser3.py
# https://python-socketio.readthedocs.io/en/latest/client.html

# sync client:   pip install "python-socketio[client]"             
# Async client:  pip install "python-socketio[asyncio_client]"

import sys
import socketio
##from time import sleep

sio = socketio.Client()   

@sio.event
def connect():
    print ("Socket connected.")


@sio.event
def connect_error (payload):
    print ("Connection failed:")
    print (payload)


@sio.event
def disconnect():
    print ("Socket disconnected.")
    
    
@sio.event
def message (payload):      # built in event
    print ('Received message:')
    print (payload)
    sio.emit ('client-event', 'Got it!')


@sio.on ('update-count') # custom event
def on_counter (payload):
    print ('Received update-count event:')
    print (payload)    


@sio.on ('server-event') # custom event
def on_server_event (payload):
    print ('Received server-event:')
    print (payload)

#-----------------------------------
# main
#-----------------------------------
 
connected = False 

PORT = 8000    # NOTE: this works through Nginx
#PORT = 5000   # direct port

url =  'http://localhost:{}'.format(PORT)
print ('server URL: ', url)
print ('Trying to connect to socket server..')

while True: 
    try: 
        sio.connect (url)
        connected = True
        print ('Connected. SID= ', sio.sid)
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
        sio.sleep (0.5)
    except KeyboardInterrupt:
        break

# aliter:
#sio.wait()

sio.disconnect()
print ('Bye!')    
