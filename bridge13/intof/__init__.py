# Factory pattern: https://hackersandslackers.com/flask-application-factory/    

from config import Config
from flask import Flask
from flask_socketio import SocketIO 
from flask_mqtt import Mqtt
from flask_cors import CORS
from time import sleep

print ('At the top level..')
Config.dump()
socketio = SocketIO () 
print ('socket object created.')
mqtt = Mqtt()
print ('mqtt object created.')

def create_my_app ():
    app = Flask (__name__)
    with app.app_context():
        app.config.from_object (Config)
        CORS (app)
        socketio.init_app (app, async_mode='gevent', cors_allowed_origins="*")
        print ('socket object initialized.')
        abort = False
        while (not abort):
            try:
                mqtt.init_app (app)
                print ('mqtt object initialized.')
                break
            except Exception as e:
                print ('* EXCEPTION: ', str(e))
                sleep(5)        
        from . import router     # imported within the app context
        router.initialize_all()  # NOTE: this is how to run app level initialization code 
        return (app)
    
# NOTE: router is imported within the app context ***
