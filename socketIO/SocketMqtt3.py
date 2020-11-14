# Flask socketIO server with classical Paho MQTT  [not Flask-mqtt]
# Unlike the Flash-MQTT version when SocketIO is the server, this correctly calls MQTT on_connect()
# Test it by pointing your broswer to localhost:5000; this displays a socket client.
# https://stackoverflow.com/questions/43205568/python-flask-server-with-mqtt-subscription
# pip install paho-mqtt

import time
from flask import Flask, render_template
import paho.mqtt.client as mqtt
from flask_socketio import SocketIO

topic1 = 'cmnd/raja'
topic2 = 'stat/raja'
server = 'localhost'
MQTTport = 1883
HTTPport = 5000
client = None

app = Flask(__name__)
socketio = SocketIO (app, async_mode='gevent', cors_allowed_origins="*") 

# --------- SocketIO ---------------------------------------------------------

@socketio.on('connect')
def on_connect ():
    print ('Socket client connected.')
    socketio.send ('Welcome client!')

@socketio.on('disconnect')
def on_disconnect():
    print ('Client disconnected.')

@socketio.on ('message')   # ('client-event')  
def on_publish (payload):
    print ('publishing: ', payload)
    client.publish (topic2, payload)
    #socketio.send ('Published: ' +payload)
    
# --------- MQTT -------------------------------------------------------------
   
def on_connect (client, userdata, flags, rc):
    print('\n\n********* Connected to MQTT broker: ' +server +' **************\n\n')
    client.subscribe (topic1, qos=0)  # on reconnection, automatically renew
    print ('Subscribed to: ' +topic1)
    client.publish (topic2, 'Hello client(s)...! I am online')

def on_message (client, userdata, msg):
    strmsg = msg.payload.decode()
    print (msg.topic+"  <-- " + strmsg)  
    socketio.send (strmsg)
    client.publish (topic2, 'Pushed: ' +strmsg)

# --------- web server ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('socketclient1.html')
    
@app.route('/ping')
def ping():
    client.publish(topic2, "Ping !")
    print ('pinging client..')
    return 'sent a PinG!'
#--------------------------------------------------------------------------------    
# MAIN    
#--------------------------------------------------------------------------------

# note: if client ID is constant, earlier subscriptions will still linger *     
client = mqtt.Client("raman_rajas_Flak_client1", clean_session=True)  # False
#client.username_pw_set (username, password)

client.on_connect = on_connect
client.on_message = on_message

print ('Trying to connect to the broker...')
client.connect(server, MQTTport, keepalive=60)    # blocking call    

print ('Starting the MQ loop...')
client.loop_start()  # this is important: listen to the mqtt port

'''----------------------------------------------
# to run stand-alone MQTT without the socket server:
terminate = False
try:
    while (not terminate):
        time.sleep(1)
except KeyboardInterrupt:
    terminate = True
----------------------------------------------'''

print ('Starting the socket server on port 5000...')    
# without use_reloader=False, it goes into an infinite loop of initialization code ! ****
socketio.run (app, host='0.0.0.0', port=5000, use_reloader=False, debug=True)
    
client.loop_stop()   # kill the background thread     
print ('Bye!')    

#===============================================================================================
socketclient2.html

"""
<!DOCTYPE html>
<html lang="en">
<head>
	<title>Flask websocket client</title>
</head>
<body>
    <h3>Socket message:<br/>
    <p id="msg_panel"></p></h3>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/1.7.3/socket.io.min.js"></script>
    <script type="text/javascript">
     var socket = io.connect('http://localhost:5000');

     socket.on('connect', function()
     {  
        var msg = 'Connected to socket server.';
     	console.log (msg);
     	socket.send (msg);
     });

     socket.on('message', function(msg)
     {  
        console.log (msg);  /* JSON.stringify(msg); */
        document.getElementById ("msg_panel").innerHTML = msg;  
        socket.send ('socket gratefully ACKs!')
     });
 </script>
</body>
</html>
"""
