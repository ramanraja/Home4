# Flask socket IO server test 
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates
# Test it using socketcli2.py

from flask_socketio import SocketIO, emit, send
from flask import Flask, render_template, request

app = Flask (__name__)
sio = SocketIO(app)
gcount = 1
PORT = 5000  # default is 5000

@app.route('/',  methods=['GET'])
def index():
    return ("This is socketIO server. <br/>Options= localhost:5000/trigger<br/>localhost:5000/ping")

      
# this is used to simulate an external trigger: Note that this is an ordinary
# Flask method; invoke it from a browser. It will send a message on the socket side.      
@app.route('/trigger',  methods=['GET'])
def trigg():
    global gcount
    gcount += 1
    retval = {'count':gcount}
    print ('\n', retval, '\n')
    sio.emit ('update-count', retval, broadcast=True)
    return (retval)


@app.route('/ping',  methods=['GET'])
def ping():
    sio.send ('Ping pong!')
    return ("Sent.<br/>Options= localhost:5000/trigger<br/>localhost:5000/ping")
    
    
@sio.on ('connect')
def on_connect ():
    print ('\nclient connected: ', request.sid)
    emit('server-event', 'Welcome, client!')


@sio.on ('disconnect')
def on_disconnect ():
    print ('\nclient disconnected: ', request.sid)
    

@sio.on_error()        # for the default namespace
def error_handler (e):
    print ("Error: ", e)
    

@sio.on ('client-event')
def on_client_event (payload):
    print ('\nReceived client event: ', payload)
    emit('server-event', 'OK, thanks.')
    
#--------------------------------------------------------------------    
# main
#--------------------------------------------------------------------
print ('Socket server2 starting..')
# NOTE: Flask should not run the loop; hannd it over to SocketIO
# if not, the socket clients can connect, but will not receive any notifications
###app.run(debug=True)  

sio.run(app, debug=True, port=PORT)

print ('Bye!')