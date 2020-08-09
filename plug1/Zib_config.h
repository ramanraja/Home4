//config.h
#ifndef CONFIG_H
#define CONFIG_H
 
// Takes default values from keys.h (for sensitive data) and settings.h (for others)
// Then reads config.h file from the Flash and overwrites the defaults
#include "settings.h" 
#include "Zib_common.h"
#include "Zib_downloader.h"
#include "Zib_utilities.h"
#include "Zib_keys.h"
#include <FS.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>     // https://github.com/bblanchon/ArduinoJson



class Config {
public :
// constants from settings.h
/////////short  current_firmware_version =  FIRMWARE_VERSION;  

/////const char * app_name = APP_NAME;  // this is only for display on startup message
bool version_check_enabled = true;

// holds .bin and .txt file names etc, one at a time. it is REUSED ! Consume as soon as you generate it.
char  reusable_string [MAX_LONG_STRING_LENGTH];   

char  mac_address[MAC_ADDRESS_LENGTH];  // 12+1 bytes needed to hold 6 bytes in HEX 

// the following have defaults in settings.h and then overwritten from config.txt on SPIFF
char  app_id [MAX_TINY_STRING_LENGTH];
char  org_id [MAX_TINY_STRING_LENGTH];     
char  group_id [MAX_TINY_STRING_LENGTH];  
char  hub_id [MAX_TINY_STRING_LENGTH];
char  config_file_name [MAX_TINY_STRING_LENGTH];

// these have defaults in keys.h and overriden by config.txt on SPIFF
char  wifi_ssid1 [MAX_TINY_STRING_LENGTH];
char  wifi_passwd1 [MAX_TINY_STRING_LENGTH];
char  ota_server_prefix [MAX_LONG_STRING_LENGTH];  // can be a cloud URL, so a long string is reserved

// these two sets are hard coded values in keys.h
const char* wifi_ssid2 = AP_SSID2;  
const char* wifi_passwd2 = AP_PASSWD2;
const char* wifi_ssid3 = AP_SSID3;  
const char* wifi_passwd3 = AP_PASSWD3;

// MQTT 
bool  generate_random_client_id = false;   // client id MUST be unique to avoid 'repeated 8266 restart' issue !
// .. but this is now solved by appending the MAC ID as part of the client id
char  mqtt_pub_topic[MAX_SHORT_STRING_LENGTH];   // save oly the pub topic because we use it frequently

bool active_low = RELAY_ACTIVE_LOW;  // default defined in settings.h
short  primary_relay = PRIMARY_RELAY;   // the autonomous relay, which is triggered by movement, time of the day etc.

bool ON  = !active_low;  
bool OFF = active_low;

bool   auto_dawn_dusk_mode = AUTO_DAWN_DUSK_MODE;  // whether the primary light should automatically on/off during night/day 
short  night_start_hour = NIGHT_START_HOUR;   // time based automatic lights; hour and minute in 24 hour format          
short  night_start_minute = NIGHT_START_MINUTE;   
short  night_end_hour = NIGHT_END_HOUR;              
short  night_end_minute = NIGHT_END_MINUTE;       
int    day_light_threshold = DAY_LIGHT_THRESHOLD;
int    night_light_threshold = NIGHT_LIGHT_THRESHOLD;
int    light_correction = PRIMARY_LIGHT_CORRECTION;
float  auto_off_minutes = AUTO_OFF_TIME_MIN;  // the autonomous relay switches off after this time (can be fractional)

short  current_hour = 0;  // default start is at midnight
short  current_minute = 0;
bool   time_never_synced = true; // was time synced at least once? ever?
long   tick_interval = 100;  // millisec; less than ~50 will starve the network stack of CPU cycles
long   check_interval = 10000;  // check status once in 10 sec  (for leaky bucket)
short  status_report_frequency = STATUS_FREQUENCEY;  // in minutes; usually 5 minutes

Config();
bool  init();
void  dump();
int   load_config();
int   download_config();  // this is called from command handler through MQTT
const char* get_error_message (int error_code);

void make_derived_params();
int get_auto_off_ticks(); // number of 10-sec blocks after which the autonomous light will go off

// the following are internal methods that actually form the respective strings by splicing
const char* get_ota_url();
const char* get_version_url();
const char* get_config_url();
const char* get_config_file_name();
const char* get_sub_topic();
const char* get_broadcast_topic(); 
const char* get_night_hours_string();

// this method is to send it to the client that requests the parameter
const char* get_param (const char* param); 
/***
// this method temporarily sets the parameter to the indicated value; this does NOT survive a reboot
bool set_param (const char* param, const char* value); // to etch it permanenly, upload a new config.txt file
***/

void  set_time (short hour, short minute);
const char* get_time();
short is_night_time();  // The output is ternary: day,night,unknown
void  increment_clock();
};  
#endif 
 
