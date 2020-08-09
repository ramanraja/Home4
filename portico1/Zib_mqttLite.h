//mqttLite.h
// HiveMQ: http://www.hivemq.com/demos/websocket-client/

#ifndef MQTTLITE_H
#define MQTTLITE_H

#include "Zib_config.h"
#include "Zib_common.h"
#include "Zib_myfi.h"
#include <ESP8266WiFi.h>
#include <PubSubClient.h>   // https://github.com/knolleary/pubsubclient 

class MqttLite {
  public:
    MqttLite();
    bool init(Config* config, MyFi*  pW);
    void update ();
    bool reconnect ();
    void generateClientID ();
    bool subscribe ();
    bool publish (const char *msg);  // send to a pre-configured topic
    bool publish (const char *topic, const char *msg);    
    //static void callback(char* topic, byte* payload, unsigned int length);   
    int QOS=1; 
  private:
    Config *pC;  
    MyFi*  pW;
    char mqtt_client_id [MAX_CLIENT_ID_LENGTH];   
};


#endif
