// settings.h
#ifndef SETTINGS_H
#define SETTINGS_H

#include "pins.h"

#define  FIRMWARE_VERSION        3            // increment the firmware version for every revision
#define  BAUD_RATE               115200       // serial port

#define  RELAY_ACTIVE_LOW        1            // 1 if relays are active low; 0 for active high 
#define  PRIMARY_RELAY           1            // the main light for automatic control is 0,1,2... NUM_RELAYS
#define  BLINK_COUNT1            4            // device identifier (IFF) blinking
#define  BLINK_COUNT2            8            // device identifier (IFF) blinking

#define  UNIVERSAL_GROUP_ID      "0"          // TODO: use this to listen for pan-group messages
#define  UNIVERSAL_DEVICE_ID     "0"          // all devices in a group listen on this channel

#define  APP_NAME                "Portico"   // this is only for display
#define  APP_ID                  "home"       //  max: MAX_TINY_STRING_LENGTH 
#define  ORG_ID                  "intof"      //  max: MAX_TINY_STRING_LENGTH 
#define  GROUP_ID                "G0"         // test group; to be overriden by config.txt file in Flash 
#define  HUB_ID                  "HUB1"       // max: MAX_TINY_STRING_LENGTH 
#define  CONFIG_FILE_SIZE        500             // bytes; the raw text file on the flash
#define  JSON_CONFIG_FILE_SIZE   700             // bytes; including json overhead: https://arduinojson.org/v6/assistant/

#define  AUTO_DAWN_DUSK_MODE     1 
#define  NIGHT_START_HOUR        18             // all zeros: disable automatic light on/off feature (dawn_dusk_mode = false)
#define  NIGHT_END_HOUR          0
#define  NIGHT_START_MINUTE      6      
#define  NIGHT_END_MINUTE        15

#define  DAY_LIGHT_THRESHOLD         150
#define  NIGHT_LIGHT_THRESHOLD       90
#define  PRIMARY_LIGHT_CORRECTION    620   // when primary light is ON, it contributes this much light to the LDR

#define  STATUS_FREQUENCEY       5            // in minutes
#define  AUTO_OFF_TIME_MIN       1.5          // in minutes 

#endif
