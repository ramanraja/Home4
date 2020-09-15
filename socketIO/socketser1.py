# Flask socket IO server test 
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates
# Test it using socketcli1.py

from flask_socketio import SocketIO, emit, send
from flask import Flask, render_template

app = Flask (__name__)
socketio = SocketIO(app)
gcount = 1

@app.route('/',  methods=['GET'])
def index():
    return ("This is socketIO server. <br/>Hit localhost:5000/trigger")
      
# this is used to simulate an external trigger: Note that this is an ordinary
# Flask method; invoke it from a browser. It will send a message on the socket side.      
@app.route('/trigger',  methods=['GET'])
def trigg():
    global gcount
    gcount += 1
    retval = {'count':gcount}
    print (retval)
    socketio.emit ('update-count', retval, broadcast=True)
    return (retval)

print ('socket server starting on port 5000...')
# NOTE: Flask should not run the loop; hannd it over to SocketIO
# if not, the socket clients can connect, but will not receive any notifications
###app.run(debug=True)  

socketio.run(app, debug=True) #, use_reloader=False)
print ('Bye!')