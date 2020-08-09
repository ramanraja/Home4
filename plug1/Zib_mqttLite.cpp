// mqttLite.cpp

#include "Zib_mqttLite.h"

WiFiClient   wifi_client;
PubSubClient pubsub_client(wifi_client);  // this cannot go inside the class because of the external static callback.

extern void  app_callback (const char* command_string);

//------------------------------------------------------------------------------------------------
// TODO: create a byte_to_char(char* dest, byte* src, int length, int max_length) function in utils.cpp

// static callback to handle mqtt command messages
char rx_payload_string [MAX_MSG_LENGTH];   // we need to make a copy and release the PubSubClient buffer

void mqtt_callback (char* topic, byte* payload, unsigned int length) {
    SERIAL_PRINT (F("Message received @ "));
    SERIAL_PRINTLN (topic);
    if (length >= MAX_MSG_LENGTH) {
        SERIAL_PRINTLN (F("\n\n**** PANIC: Mqtt Rx message is too long ! ******\n\n"));
        return;  // incoming message is discarded
    }
    char *ptr = rx_payload_string;
    for (int i = 0; i < length; i++) {     // Ugly, but needed: payload is in bytes, but target is char
         *ptr++ = (char)payload[i];        // TODO: find another way; strncpy() ?          
    }                                      // what if sizeof(char) is not equal to sizeof(byte) ?
    *ptr= '\0';
    //SERIAL_PRINTLN(rx_payload_string);  
    app_callback ((const char*)rx_payload_string);  
    
    //NOTE: SERIAL_PRINTLN ((char *)payload); // This prints a corrupted string ! because it is a
                                              // byte array, not a char string with null terminator. Conversely,
                                              // there can be even NULLs embedded in the middle of the byte array   

}
//------------------------------------------------------------------------------------------------
// class methods

MqttLite::MqttLite() {
}

bool MqttLite::init (Config* configptr, MyFi*  wifiptr) {
    this->pC = configptr;  
    this->pW = wifiptr;
    pubsub_client.setKeepAlive(MQTT_KEEPALIVE);
    generateClientID();
    SERIAL_PRINT (F("MqttLite client id: "));
    SERIAL_PRINTLN(mqtt_client_id);  
    if (!reconnect ())  // initial connection
        return false;
    subscribe ();  // TODO: is there sticky subscription in 8266?
        return true;
} 

// you must periodically call this function; othewise the MQTT pump will starve
void MqttLite::update () {
    if (pubsub_client.connected ())      
        pubsub_client.loop ();       // keep mqtt pump running
    else {    
        if (reconnect ())
            subscribe ();      
    }
}

//connects to mqtt layer
bool MqttLite::reconnect () {
    if (!pW->isConnected()) {
        SERIAL_PRINTLN (F("MqttLite: No WiFi connection."));
        pW->reconnect();
        return false;
    }
    SERIAL_PRINT (F("Connecting to MQTT broker: "));
    SERIAL_PRINTLN (MQTT_SERVER);
    if (pubsub_client.connected())  
        pubsub_client.disconnect ();  // to avoid leakage ?

    if (pC-> generate_random_client_id) {
        generateClientID ();                   // this not needed if we are using MAC address as a
        SERIAL_PRINT (F("MQTT client id: ")); //  part of the MQTT client ID
        SERIAL_PRINTLN(mqtt_client_id);  
    }
    pubsub_client.setServer(MQTT_SERVER, MQTT_PORT);
    WiFi.mode(WIFI_STA);  // see https://github.com/knolleary/pubsubclient/issues/138 
    
    if (pubsub_client.connect(mqtt_client_id)) {
        SERIAL_PRINTLN (F("Connected to broker."));     
        return true;
    } else {
        SERIAL_PRINT(F("MQTT connection failed, rc="));
        SERIAL_PRINTLN(pubsub_client.state());
        return false;
    }
}
 
// Generate random mqtt clientID or a unique ID based on MAC address
// A unique ID is essential to avoid "device restarting problem" due to clash in client IDs
// A repeatable ID based on MAC address helps in session persistance (TODO: investigate this)
void MqttLite::generateClientID () {
    //snprintf (mqtt_client_id, MAX_CLIENT_ID_LENGTH, "%s_%x%x",  pC->org_id, random(0xffff), random(0xffff));  
    snprintf (mqtt_client_id, MAX_CLIENT_ID_LENGTH, "%s_%s",  pC->org_id, pC->mac_address);  
}

//subscribe to the mqtt command topic
bool MqttLite::subscribe () {
    pubsub_client.setCallback(mqtt_callback); // static function outside the class  
    const char* sub_topic = pC->get_sub_topic();
    SERIAL_PRINT(F("Subscribing to topic: "));
    SERIAL_PRINTLN(sub_topic);      
    if (strlen(sub_topic) < 1) {   // it can be blank some times
        SERIAL_PRINT(F("--- Invalid topic ---"));
        return false;
    }
    bool result1 = pubsub_client.subscribe(sub_topic, QOS);  
    if (result1) 
        SERIAL_PRINTLN (F("Subscribed."));    
    else
        SERIAL_PRINTLN (F("Subscribing failed."));

    const char* bcast_topic = pC->get_broadcast_topic();
    SERIAL_PRINT(F("Subscribing to broadcst topic: "));
    SERIAL_PRINTLN(bcast_topic);      
    if (strlen(bcast_topic) < 1) {   // it can be blank some times
        SERIAL_PRINT(F("--- Invalid topic ---"));
        return false;
    }
    bool result2 = pubsub_client.subscribe(bcast_topic, QOS);  
    if (result2) 
        SERIAL_PRINTLN (F("Subscribed."));    
    else
        SERIAL_PRINTLN (F("Subscribing failed."));        
    return(result1 && result2);
}

//send a message to a pre-configured topic
bool MqttLite::publish (const char *msg) {
    return (publish(pC->mqtt_pub_topic, msg));
}

//send a message to an arbitrary topic
bool MqttLite::publish (const char *topic, const char *msg) {
    if (!pW->isConnected()) {
        SERIAL_PRINTLN (F("MqttLite.publish: No WiFi"));
        return false;
    }
    if (!pubsub_client.connected()) { 
        SERIAL_PRINTLN (F("MqttLite.publish: No Broker"));
        return false;
    }    
    SERIAL_PRINT (F("Publishing to topic: "));    
    SERIAL_PRINTLN (topic);
    SERIAL_PRINT (F("Message: "));    
    SERIAL_PRINTLN (msg);
    int result = pubsub_client.publish(topic, msg);
    if (!result) 
        SERIAL_PRINTLN (F("Publishing failed."));    
    return((bool)result);  // true: success, false:failed to publish
}
 
