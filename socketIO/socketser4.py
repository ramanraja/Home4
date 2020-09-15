# Example of how to send server generated events to clients:
# Flask socket IO emit an event periodically from a background thread

# https://github.com/miguelgrinberg/Flask-SocketIO/blob/master/example/app.py
# https://github.com/miguelgrinberg/Flask-SocketIO/issues/117
# https://github.com/miguelgrinberg/python-socketio/issues/16
# Test it using socketcli4.py

#import eventlet
#eventlet.monkey_patch()

from threading import Lock
from flask_socketio import SocketIO, emit, send
from flask import Flask  
from flask_socketio import SocketIO, emit, disconnect 

PORT = 5000
TERMINATE = False

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
sio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
        
@app.route('/',  methods=['GET'])
def index():
    ##return render_template('index.html', async_mode=socketio.async_mode)
    return ("This is socketIO server @ localhost:", PORT)

'''
@sio.on ('connect')
def on_connect ():
    print ('\nclient connected.\n')
    emit('server-event', 'Welcome, client!')
'''

@sio.on ('disconnect')
def on_disconnect ():
    print ('\nclient disconnected.\n')
    

@sio.on_error()        # for the default namespace
def error_handler (e):
    print ("Error: ", e)
    

@sio.on ('client-event')
def on_client_event (payload):
    print ('\nReceived client event: ', payload)


@sio.on('connect')
def on_connect():
    global thread
    print ('\nclient connected.\n')
    print ('About to start background thread...')
    with thread_lock:
        if thread is None:
            thread = sio.start_background_task (bgthread)
    emit('server-event', 'Welcome, dear client!')
        
            
def bgthread():
    count = 0
    print ('Entering backgrount thread...')
    while not TERMINATE:
        sio.sleep(10)
        count += 1
        print ('Emitting: ', count)
        sio.emit ('server-event', {'count' : count}) # payload must be JSON
    print ('Background thread finished.')         
       
#----------------------------------------------------------------
# MAIN
#----------------------------------------------------------------
if __name__ == '__main__':

    '''----------------- this does not work- why?-----------------
        print ('About to start background thread...')
        with thread_lock:
            if thread is None:
                thread = sio.start_background_task (bgthread)
    ------------------------------------------------------------'''
    
    print ('Entering main loop...')
    ###app.run(debug=True) 
    sio.run (app, debug=True, port=PORT)
    
    print ('Shutting down..')    
    TERMINATE = True
    sio.sleep (2)
    print ('Bye!')
