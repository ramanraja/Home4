// otaHelper.h
// OTA files on S3 are of the form:
// https://my-bucket.s3.us-east-2.amazonaws.com/my-folder/my-file.jpg

#ifndef OTAHELPER_H
#define OTAHELPER_H

// enable the following line to receive MQTT status during FW update; comment out to disable messages
#define MQTT_ENABLED

#include "Zib_common.h"
#include "Zib_config.h"
#include <ESP8266HTTPClient.h>
#include <ESP8266httpUpdate.h>

#ifdef MQTT_ENABLED
  #include "Zib_mqttLite.h"
#endif

class OtaHelper {
 public:
    OtaHelper();
    void init(Config *configptr);    
#ifdef MQTT_ENABLED
    //void init(Config *configptr, PubSubClient *mqttptr);
    void init(Config *configptr, MqttLite *mqttptr);
    void publish_msg ();
#endif
    int check_and_update();
    int check_version();    
    int update_firmware();  
 private:
     Config *pC;
     /////bool use_backup_urls = false; // this is a global flag used throughout this class
#ifdef MQTT_ENABLED     
     //PubSubClient *pM;
     MqttLite *pM;
     char reusable_str[MAX_MSG_LENGTH]; // Reusable Tx message buffer.  TODO: revisit this length  
#endif     
};

#endif 
