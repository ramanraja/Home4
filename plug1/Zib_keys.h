// keys.h
// Keep this file secret: NEVER upload it to any code repository like Github !

#ifndef KEYS_H
#define KEYS_H

#define  AP_SSID1       "xxxxx"     
#define  AP_PASSWD1     "xxxxx" 
#define  AP_SSID2       "xxxxx"
#define  AP_PASSWD2     "xxxxx"
#define  AP_SSID3       "xxxxx"
#define  AP_PASSWD3     "xxxxx"

//"INTOF_MOBILE"
//"!ntof4321"

// OTA binary file:  http://web_server_prefix/app_id.bin  
// OTA version check file:  http://web_server_prefix/app_id.txt
// Config file: http://web_server_prefix/config.txt

#define  OTA_SERVER_PREFIX      "http://192.168.1.2:1000/ota"
 
// MQTT subscribe topic is of the form : intof/AppID/cmd/groupID/MAC
// MQTT publish topic is of the form   : intof/AppID/status/groupID/MAC

// using mosquitto broker on the local network

#define  MQTT_SERVER           "192.168.1.10"
#define  MQTT_PORT             1883
#define  SUB_TOPIC_PREFIX      "cmd"
#define  PUB_TOPIC_PREFIX      "status"

#endif 
