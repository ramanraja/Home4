import os
        
class Config (object):
    APP_PORT = os.environ.get ('APP_PORT') or 5000
    TEMPLATES_AUTO_RELOAD = True    
    SECRET_KEY = os.environ.get ('SECRET_KEY') or 'the-secret-key'
    MQTT_BROKER_URL = 'localhost'      
    MQTT_BROKER_PORT = 1883
    MQTT_KEEPALIVE = 60  # sec
    MQTT_TLS_ENABLED = False  
    
    # the following are not used; they are again defined in router.py
    SUB_TOPIC = 'stat/#'         
    PUB_PREFIX = 'cmnd'
    PUB_SUFFIX = 'POWER'       
    CLIENT_EVENT = 'client-event'
    SERVER_EVENT = 'server-event'
    ACK_EVENT = 'ACK'    

    def dump ():   # satic method
        print ('\nConfig:') 
        print ('APP_PORT: %d [%s]' %(Config.APP_PORT, type(Config.APP_PORT)))
        print ('SECRET_KEY: %s' %'*****')  # Config.SECRET_KEY)
        print ('MQTT_BROKER_URL: %s' % Config.MQTT_BROKER_URL)         
        print ('MQTT_BROKER_PORT: %s' % Config.MQTT_BROKER_PORT)         
        print ('MQTT_KEEPALIVE: %d' % Config.MQTT_KEEPALIVE)   
        print ('\nFor info only:')      
        print ('SUB_TOPIC: %s' % Config.SUB_TOPIC)  
        print ('PUB_PREFIX: %s' % Config.PUB_PREFIX)         
        print ('PUB_SUFFIX: %s' % Config.PUB_SUFFIX) 
        print ('CLIENT_EVENT: %s' % Config.CLIENT_EVENT)          
        print ('SERVER_EVENT: %s' % Config.SERVER_EVENT)          
        print ('ACK_EVENT: %s' % Config.ACK_EVENT)          
        print()        