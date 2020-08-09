//common.h
#ifndef COMMON_H
#define COMMON_H

#include <Arduino.h>
extern "C" {
  #include "user_interface.h"
}


#define  MAX_COMMAND_LENGTH          8         // the raw command string, without json formatting & keys (usually 3 chars)
#define  MAC_ADDRESS_LENGTH          14        // 12+1 needed to hold 6 hyte HEX address
#define  MAX_LONG_STRING_LENGTH      128       // URLs, messages etc (mqtt message body + json parser overhead)
#define  MAX_SHORT_STRING_LENGTH     64        // topic names, keys-values, web-app server prefix etc
#define  MAX_TINY_STRING_LENGTH      16        // wifi ssid, password, org id, app id, group id etc
#define  MAX_CLIENT_ID_LENGTH        22        // * MQTT standard allows max 23 characters for client id *  

// keep MQTT Rx messages short (~100 bytes); PubSubClient silently drops longer messages !
#define  MAX_MSG_LENGTH              96        // MQTT message body -usully a json.dumps() string, excluding parser overhead
// The following constants override those in PubSubClient
#define  MQTT_KEEPALIVE              60        // 120   override for PubSubClient keep alive, in seconds
////#define  MQTT_MAX_PACKET_SIZE    128       // 256   PubSubClient default is 128, including headers

// The maximum number of relays a board can theoretically have is limited to 8
// The actually present number can be 1 to 8, which is given by NUM_RELAYS in pins.h
// Assumption: there will not be more than 8 relays
// Command handler can only handle commands like ON0 to ON9, so the relay count has to be single digit ***
// This is OK, since 8266 has only a limited number of I/O pins

#define  MAX_RELAYS     8 

// comment out this line to disable some informative messages
///#define  VERBOSE_MODE 

// comment out this line to disable all serial messages
#define ENABLE_DEBUG

#ifdef ENABLE_DEBUG
  #define  SERIAL_PRINT(x)       Serial.print(x)
  #define  SERIAL_PRINTLN(x)     Serial.println(x)
  #define  SERIAL_PRINTLNF(x,y)  Serial.println(x,y)   
  #define  SERIAL_PRINTF(x,y)    Serial.printf(x,y) 
#else
  #define  SERIAL_PRINT(x)
  #define  SERIAL_PRINTLN(x)
  #define  SERIAL_PRINTLNF(x,y)
  #define  SERIAL_PRINTF(x,y)
#endif

#define  TIME_DAY       0
#define  TIME_NIGHT     1
#define  TIME_UNKNOWN   2
 
enum connection_result {
    CODE_OK = 0,
    PROCEED_TO_UPDATE,
    UPDATE_OK,
    MQTT_CONNECT_SUCCESS,
    
    MQTT_CONNECT_FAILED,
    TIME_SERVER_FAILED,
    
    NO_WIFI,
    BAD_URL,
    HTTP_FAILED,
    URI_NOT_FOUND,
    NO_ACCESS,
    VERSION_CHECK_FAILED,
    UPDATE_FAILED,
    NO_UPDATES,
    
    SPIFF_FAILED,
    FILE_OPEN_ERROR,
    FILE_WRITE_ERROR,
    FILE_TOO_LARGE,
    JSON_PARSE_ERROR
} ;

#endif
