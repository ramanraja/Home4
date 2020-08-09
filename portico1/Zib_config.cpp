//config.cpp
#include "Zib_config.h"

/* 
 Example topics:
 publish:   intof/home/status/G1/2CF432173BC0
 subscribe: intof/home/cmd/G1/2CF432173BC0
 subscribe: intof/home/cmd/G1/0
*/

Config::Config(){
}

// returns false if config file could not be loaded; true otherwise
bool Config::init() {
    byte mac[6];
    WiFi.macAddress(mac);
    // do not write %2X, since it will pad with a space if the octet has a single digit
    snprintf (mac_address, MAC_ADDRESS_LENGTH-1, "%02X%02X%02X%02X%02X%02X", mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);
    mac_address[MAC_ADDRESS_LENGTH-1]='\0';   // TODO: create a utility wrapper safe_snprintf()  
        
    // the string variables are to be copied; (other basic types are already initialized in config.h) 
    safe_strncpy (hub_id, HUB_ID, MAX_TINY_STRING_LENGTH);
    safe_strncpy (app_id, APP_ID, MAX_TINY_STRING_LENGTH);
    safe_strncpy (org_id, ORG_ID, MAX_TINY_STRING_LENGTH);
    safe_strncpy (group_id, GROUP_ID, MAX_TINY_STRING_LENGTH);    
    
    // these are user defined strings in keys.h and later in settings.txt
    safe_strncpy (wifi_ssid1, AP_SSID1, MAX_TINY_STRING_LENGTH);    
    safe_strncpy (wifi_passwd1, AP_PASSWD1, MAX_TINY_STRING_LENGTH);    
    
    // The firmware URLs will later be concatenated with an intervening slash; so remove them if present.
    // The Flash file names already have a mandatory slash at the beginning; so remove it too.
    safe_strncpy_remove_slash (ota_server_prefix,  OTA_SERVER_PREFIX,  MAX_SHORT_STRING_LENGTH);
        
    // now that the main parameters are in place, set up the derived parameters:
    make_derived_params();
    SERIAL_PRINTLN (F("Default configuration:"));
    dump();
    
    int result = load_config();  // read overriding params from Flash file    
    SERIAL_PRINT (F("SPIFF configuration load result: "));
    SERIAL_PRINTLN (get_error_message(result));
    return (result==CODE_OK);  
}

// parameters that depend on other parameters initialized earlier
void Config::make_derived_params() {
    ON  = active_low ? 0 : 1;
    OFF = active_low ? 1 : 0;
    int hours_sum = night_start_hour+ night_start_minute+ night_end_hour+night_end_minute;
    auto_dawn_dusk_mode = (hours_sum > 0); 
    snprintf (config_file_name, MAX_TINY_STRING_LENGTH-1, "%s", get_config_file_name());
    snprintf (mqtt_pub_topic, MAX_SHORT_STRING_LENGTH-1, "%s/%s/%s/%s/%s", org_id, app_id, PUB_TOPIC_PREFIX, group_id, mac_address); 
}  

// converts auto_off_minutes into number of 10-second ticks
int Config::get_auto_off_ticks() {
    return (auto_off_minutes * 60 / (check_interval/1000));
}

// NOTE: reusable_string is a scratch pad string; it holds one URL at a time, to save memory!
// So don't call any of these functions while the previous string is still in use 
// add a random parameter to the URL to bypass the server side cache:
// https://stackoverflow.com/questions/50699554/my-esp8266-using-cached-how-to-fix
// NOTE: the following two functions introduce a slash between the prefix and the file name; so this should not
// be added in the prefix string (even if present, it would have been removed)

// To the caller: reusable_string is loaned to you for a short duration only; use it up immediately and release it! Never store the pointer.
// A  dummy random number is added to the URL to prevent stale files being served from cache
const char* Config::get_ota_url() {
    snprintf (reusable_string, MAX_LONG_STRING_LENGTH-1, "%s/%s.bin?X=%d", ota_server_prefix, app_id, random(0,1000));    
    return ((const char*) reusable_string);
}

// To the caller: Never store the returned pointer.
const char* Config::get_version_url() {
    snprintf (reusable_string, MAX_LONG_STRING_LENGTH-1, "%s/%s.txt?X=%d", ota_server_prefix, app_id, random(0,1000));    
    return ((const char*) reusable_string);}

// To the caller: Never store the returned pointer.
// NOTE: config_file_name must start with a leading slash '/' for the SPIFF to work correctly
const char* Config::get_config_file_name() {
    snprintf (reusable_string, MAX_LONG_STRING_LENGTH-1, "/conf_%s.txt", app_id);    // NOTE: leading slash is needed
    return ((const char*) reusable_string);
}

// To the caller: Never store the returned pointer.
// Config file name must be in the form   '/conf_<APPID>.txt'  eg:  '/conf_home.txt'
// NOTE: config_file_name already starts with a leading slash '/', so avoid it in the format string
const char* Config::get_config_url() {
    snprintf (reusable_string, MAX_LONG_STRING_LENGTH-1, "%s%s?X=%d", ota_server_prefix, config_file_name, random(0,1000));    
    return ((const char*) reusable_string);
}

// To the caller: reusable_string is loaned to you for a short duration only; use it up immediately and release it! Never store the pointer.
const char* Config::get_sub_topic() {
    snprintf (reusable_string, MAX_SHORT_STRING_LENGTH-1, "%s/%s/%s/%s/%s", org_id, app_id, SUB_TOPIC_PREFIX, group_id, mac_address);
    return ((const char*) reusable_string);
}    

// To the caller: Never store the returned pointer.
const char* Config::get_broadcast_topic() {  
    snprintf (reusable_string, MAX_SHORT_STRING_LENGTH-1, "%s/%s/%s/%s/%s", org_id, app_id, SUB_TOPIC_PREFIX, group_id, UNIVERSAL_DEVICE_ID);    
    return ((const char*) reusable_string);
} 

// To the caller: Never store the returned pointer.
const char*  Config::get_night_hours_string() {
    snprintf(reusable_string, MAX_SHORT_STRING_LENGTH-1, "%d:%02d - %d:%02d", night_start_hour, night_start_minute, night_end_hour,night_end_minute);
    return ((const char*) reusable_string);
}

// this is triggered by a #HH:MM command from the Hub
// Assumption: the time has already been validated
void Config::set_time (short hour, short minute) {
    current_hour = hour;
    current_minute = minute;
    time_never_synced = false;  // it is enough if time was synced just once; then dead reckoning is good for days to come
  #ifdef  ENABLE_DEBUG       
    snprintf(reusable_string, MAX_SHORT_STRING_LENGTH-1, "SET TIME %02d:%02d", current_hour,current_minute);    
    SERIAL_PRINTLN (reusable_string);  
  #endif    
}

// this is triggered by TIM command
const char* Config::get_time () {
    snprintf(reusable_string, MAX_SHORT_STRING_LENGTH-1, "%02d:%02d", current_hour,current_minute);    
    return ((const char*) reusable_string);  
}

// This is dead reckoning: increment the clock by one minute
void Config::increment_clock() {
    current_minute = (current_minute+1) % 60;
    if (current_minute == 0)
        current_hour = (current_hour+1) % 24;
}

// The output is ternary: day,night,unknown
// this is called every 5 minutes to switch the primary light on schedule
short Config::is_night_time() {  
    if (time_never_synced) {   
      SERIAL_PRINTLN(F("Never heard from Time Server"));
      return TIME_UNKNOWN;
    }
    // Assumption: in 24 hour format, night start time is bigger than end time; 
    // end time is in the next morning
    // NOTE: this makes it impossible to switch on at, say, 6 PM and switch off at 10 PM the same night
    // TODO: make this more flexible, remove the above constraint 
    // TODO: ability to add multiple schedules in a day
    if (current_hour > night_start_hour  || current_hour < night_end_hour) 
        return TIME_NIGHT;
    if (current_hour == night_start_hour && current_minute >= night_start_minute)  
        return TIME_NIGHT;        
    if (current_hour == night_end_hour && current_minute <= night_end_minute)  
        return TIME_NIGHT;
    return TIME_DAY;
}
               
int Config::load_config() {
    SERIAL_PRINTLN(F("Loading config from Flash..."));
    if (!SPIFFS.begin()) {
        SERIAL_PRINTLN(F("--- Failed to mount file system. ---"));
        ///SPIFFS.end();
        return SPIFF_FAILED;
    }
    //SERIAL_PRINTLN(F("Checking Config file..."));
    File configFile = SPIFFS.open (get_config_file_name(), "r");
    if (!configFile) {
        SERIAL_PRINTLN(F("--- Failed to open config file. ---"));
        SPIFFS.end();
        return FILE_OPEN_ERROR;
    }
    size_t size = configFile.size();
    SERIAL_PRINT(F("Config file present. Size: "));
    SERIAL_PRINTLN(size);    
    if (size > CONFIG_FILE_SIZE) {
        SERIAL_PRINTLN(F("--- Config file size is too large. ---"));
        SPIFFS.end();
        return FILE_TOO_LARGE;
    }
    // Allocate a buffer to store file contents ***
    // ArduinoJson library requires the input buffer to be mutable.     
    std::unique_ptr<char[]> buf(new char[size]);
    configFile.readBytes(buf.get(), size);
    
    // Consider this number carefully; ArduinoJson needs extra space for metadata:
    // https://arduinojson.org/v6/assistant/
    StaticJsonDocument<JSON_CONFIG_FILE_SIZE> doc;  // including extra space for Json
    auto error = deserializeJson(doc, buf.get());
    SERIAL_PRINT(F("Deserialization result: "));
    SERIAL_PRINTLN (error.c_str());
    if (error) {
        SERIAL_PRINTLN(F("--- Failed to parse config file. ---"));
        SPIFFS.end();
        return JSON_PARSE_ERROR;
    }
    // string variables
    char *tmp;  // just a pointer, without memory
    tmp = (char *)(doc["OTA_SER"] | OTA_SERVER_PREFIX); 
    safe_strncpy_remove_slash (ota_server_prefix, tmp, MAX_LONG_STRING_LENGTH);
    
    tmp = (char *)(doc["GRP"] | GROUP_ID); 
    safe_strncpy (group_id, tmp, MAX_TINY_STRING_LENGTH);
    tmp = (char *)(doc["ORG"] | ORG_ID); 
    safe_strncpy (org_id, tmp, MAX_TINY_STRING_LENGTH);
    tmp = (char *)(doc["APP"] | APP_ID); 
    safe_strncpy (app_id, tmp, MAX_TINY_STRING_LENGTH); 
    tmp = (char *)(doc["HUB"] | HUB_ID); 
    safe_strncpy (hub_id, tmp, MAX_TINY_STRING_LENGTH); 
    tmp = (char *)(doc["SSID"] | AP_SSID1); 
    safe_strncpy (wifi_ssid1, tmp, MAX_TINY_STRING_LENGTH); 
    tmp = (char *)(doc["PASS"] | AP_PASSWD1); 
    safe_strncpy (wifi_passwd1, tmp, MAX_TINY_STRING_LENGTH);         
        
    // Non-string variables       
    active_low = doc["ACTIVE_LOW"] | RELAY_ACTIVE_LOW; 
    primary_relay = doc["PRIMARY_REL"] | PRIMARY_RELAY; 
    status_report_frequency = doc["STAT_FREQ_MIN"] | STATUS_FREQUENCEY; 
    auto_off_minutes = doc["AUTO_OFF_MIN"] | AUTO_OFF_TIME_MIN;   
    night_start_hour = doc["NIGHT_HRS"][0] | NIGHT_START_HOUR; 
    night_start_minute = doc["NIGHT_HRS"][1] | NIGHT_START_MINUTE; 
    night_end_hour = doc["NIGHT_HRS"][2] | NIGHT_END_HOUR; 
    night_end_minute = doc["NIGHT_HRS"][3] | NIGHT_END_MINUTE; 
    day_light_threshold = doc["DAY_LIGHT"] | DAY_LIGHT_THRESHOLD;
    night_light_threshold = doc["NIGHT_LIGHT"] | NIGHT_LIGHT_THRESHOLD;
    light_correction = doc["LIGHT_CORRECTION"] | PRIMARY_LIGHT_CORRECTION;
     
    // now that the main parameters are in place, set up the derived parameters:
    make_derived_params();
    
    SPIFFS.end();  // unmount file system
    return CODE_OK;
}

void Config::dump() {
#ifdef ENABLE_DEBUG
    SERIAL_PRINTLN(F("\n-----------------------------------------"));
    SERIAL_PRINTLN(F("               configuration             "));
    SERIAL_PRINTLN(F("-----------------------------------------"));    
    print_heap();
    SERIAL_PRINT(F("App name: "));
    SERIAL_PRINTLN (APP_NAME);    
    SERIAL_PRINT(F("Firmware version: "));
    SERIAL_PRINTLN (FIRMWARE_VERSION);         
    SERIAL_PRINT(F("OTA URL: "));
    SERIAL_PRINTLN (get_ota_url());   
    SERIAL_PRINT(F("FW version file URL: "));
    SERIAL_PRINTLN (get_version_url());   
    SERIAL_PRINT(F("Config file name: "));   
    SERIAL_PRINTLN(get_config_file_name());
    SERIAL_PRINT(F("Config file URL: ")); 
    SERIAL_PRINTLN (get_config_url());        
    SERIAL_PRINTLN();
    
    SERIAL_PRINT(F("Org id: "));
    SERIAL_PRINTLN (org_id);   
    SERIAL_PRINT(F("App id: "));
    SERIAL_PRINTLN (app_id);      
    SERIAL_PRINT(F("Group id: "));
    SERIAL_PRINTLN (group_id);       
    SERIAL_PRINT(F("MAC address: "));    
    SERIAL_PRINTLN (mac_address);    
    SERIAL_PRINT(F("Hub id: "));
    SERIAL_PRINTLN (hub_id);      
    SERIAL_PRINT(F("Wifi SSID: "));
    SERIAL_PRINTLN (wifi_ssid1);  
    SERIAL_PRINT(F("Wifi password: "));
    SERIAL_PRINTLN (wifi_passwd1);      
    SERIAL_PRINTLN();
    
    SERIAL_PRINT(F("MQTT server: "));
    SERIAL_PRINTLN(MQTT_SERVER); 
    SERIAL_PRINT(F("MQTT Port: "));
    SERIAL_PRINTLN(MQTT_PORT);     
    SERIAL_PRINT(F("Publish topic: "));
    SERIAL_PRINTLN (mqtt_pub_topic); 
    SERIAL_PRINT(F("Subscribe topic: "));
    SERIAL_PRINTLN (get_sub_topic()); 
    SERIAL_PRINT(F("Broadcast topic (sub): "));
    SERIAL_PRINTLN (get_broadcast_topic());  
    SERIAL_PRINTLN();
    
    // the autonomous relay, which is triggered by movement/ time of the day etc.
    SERIAL_PRINT(F("Primary (autonomous) realy number: "));
    SERIAL_PRINTLN (primary_relay);   
    // some relay modules need active LOW signals, ie, logic 0 operates the relay and 1 releases it
    SERIAL_PRINT(F("Active LOW relays? : "));
    SERIAL_PRINTLN (active_low? "Yes":"No");          
    // time based automatic lights; hour and minute in 24 hour format 
    SERIAL_PRINT(F("Night hours: "));
    SERIAL_PRINTLN (get_night_hours_string()); 
    SERIAL_PRINT(F("Day/Night Light threshold: "));
    SERIAL_PRINT (day_light_threshold);
    SERIAL_PRINT(F(" / "));
    SERIAL_PRINTLN(night_light_threshold); 
    SERIAL_PRINT (F("Primary light correction: "));
    SERIAL_PRINTLN (light_correction);
    SERIAL_PRINT(F("Automatic dawn/dusk light? : "));
    SERIAL_PRINTLN (auto_dawn_dusk_mode? "Yes":"No");  
    SERIAL_PRINT(F("Status report frequency (minutes): "));
    SERIAL_PRINTLN (status_report_frequency);        
    SERIAL_PRINT(F("Auto off minutes: "));
    SERIAL_PRINTLN (auto_off_minutes);      
    SERIAL_PRINT(F("Auto off ticks: "));
    SERIAL_PRINTLN (get_auto_off_ticks());             
    yield();
    delay(1000);  // stabilize heap ?     
    print_heap();           
    SERIAL_PRINTLN(F("-----------------------------------------\n"));
#endif    
}
     
// This is called from command handler through MQTT
// If the download succeeds, the command handler may restart the ESP
int Config::download_config() {
    SERIAL_PRINTLN(F("[Config] Downloading configuration file.."));  
    print_heap();
    Downloader D;
    D.init(this);
    int result = D.download_file();
    SERIAL_PRINT(F("[Config] download result: "));
    SERIAL_PRINTLN(get_error_message(result));
    print_heap();
    return (result);
}

const char* Config::get_error_message (int error_code) {
  switch (error_code) {
    case CODE_OK:
        return ("CODE_OK"); break;
    case PROCEED_TO_UPDATE:
        return ("PROCEED_TO_UPDATE"); break;
    case UPDATE_OK:
        return ("UPDATE_OK"); break;
    case MQTT_CONNECT_SUCCESS:
        return ("MQTT_CONNECT_SUCCESS"); break;
        
    case MQTT_CONNECT_FAILED:
        return ("MQTT_CONNECT_FAILED"); break;
    case TIME_SERVER_FAILED:
        return ("TIME_SERVER_FAILED"); break;  
                
    case NO_WIFI:
        return ("NO_WIFI"); break;                
    case BAD_URL:
        return ("BAD_URL"); break;
    case HTTP_FAILED:
        return ("HTTP_FAILED"); break;
    case URI_NOT_FOUND:
        return ("URI_NOT_FOUND"); break;
    case NO_ACCESS:
        return ("NO_ACCESS"); break;
    case VERSION_CHECK_FAILED:
        return ("VERSION_CHECK_FAILED"); break;
    case UPDATE_FAILED:
        return ("UPDATE_FAILED"); break;
    case NO_UPDATES:
        return ("NO_UPDATES"); break;
        
    case SPIFF_FAILED:
        return ("SPIFF_FAILED"); break;
    case FILE_OPEN_ERROR:
        return ("FILE_OPEN_ERROR"); break;
    case FILE_WRITE_ERROR:
        return ("FILE_WRITE_ERROR"); break;   
    case FILE_TOO_LARGE:
        return ("FILE_TOO_LARGE"); break;      
    case JSON_PARSE_ERROR:
        return ("JSON_PARSE_ERROR"); break;                               
    default:
        return("UNCONFIGURED ERROR !"); break;
  }
}

// Get commands are in the form {"-param"}
// TODO: convert this into a switch statement
const char* Config::get_param (const char* param) {
    SERIAL_PRINT(F("[Config] Get: "));
    SERIAL_PRINTLN(param);
    // the following calls return the full URL, not just the prefix 
    if (strcmp(param, "OTA") == 0)
        return (get_ota_url());
    if (strcmp(param, "OTAV") == 0)
        return (get_version_url());
    if (strcmp(param, "OTAC") == 0)
        return (get_config_url()); 
         
    if (strcmp(param, "MAC") == 0)          // this is just for completeness:
        return ((const char*)mac_address);  // it is availabe through {"C":"MAC"} also
    if (strcmp(param, "ORG") == 0)
        return ((const char*)org_id);
    if (strcmp(param, "GRO") == 0)
        return ((const char*)group_id);  
    if (strcmp(param, "APP") == 0)
        return ((const char*)app_id); 
    if (strcmp(param, "APPN") == 0)
        return (APP_NAME); 
    if (strcmp(param, "HWT") == 0)
        return (HARDWARE_TYPE);
    if (strcmp(param, "HUB") == 0)
        return ((const char*)hub_id); 
                
    if (strcmp(param, "ACTL") == 0)
        return (active_low? "1" : "0");             
    if (strcmp(param, "PRIREL") == 0) {
        itoa (primary_relay, reusable_string, 10);  // 10 is the base
        return ((const char*)reusable_string);
    } 
    if (strcmp(param, "AUTODD") == 0)  // auto dawn-dusk mode
        return (auto_dawn_dusk_mode? "1" : "0");     
         
    if (strcmp(param, "STATF") == 0) {
        itoa (status_report_frequency, reusable_string, 10);
        return ((const char*)reusable_string);
    }
    if (strcmp(param, "AOFF") == 0) {
        itoa (auto_off_minutes, reusable_string, 10);
        return ((const char*)reusable_string);
    }
    if (strcmp(param, "LTH") == 0) {
        snprintf(reusable_string, MAX_SHORT_STRING_LENGTH, "DT:%d,NT:%d,CORR:%d", day_light_threshold, night_light_threshold, light_correction);
        return ((const char*)reusable_string);         
    } 
    if (strcmp(param, "NHRS") == 0) 
        return (get_night_hours_string());  // this in turn uses reusable_string *
    if (strcmp(param, "TIME") == 0)
        return (get_time());  // this in turn uses reusable_string *
   // if (strcmp(param, "IP") == 0)  // TODO: implement this !
    //    return (get_IP());  // this in turn uses reusable_string *        
    SERIAL_PRINTLN (F("--- ERROR: Unknown parameter ---"));   
    return ("ERROR");
}

/****
// SET commands are in the form {"S":{"P":"param", "V":"value"}}
// To see the effect of a SET, issue a GET command subsequently
//  returns true if there was an error, false otherwise **
bool Config::set_param (const char* param, const char* value) {
    SERIAL_PRINT(F("Set: "));
    SERIAL_PRINTLN(param);
    SERIAL_PRINT(F("Value: ")); 
    SERIAL_PRINTLN(value);   
    bool truncated = false;
    // MAC address spoofing - use it only for testing purposes ! MAC is used in MQTT client ID
    // Warning: any duplicate MQTT client IDs will result in malfunctioning, rebooting etc
    if (strcmp(param, "MAC") == 0) {
        truncated = safe_strncpy (mac_address, value, MAC_ADDRESS_LENGTH-1);
        if (!truncated)
            make_derived_params();
        return truncated;
    }    
    // the following calls only set the prefix, not the full URL
    if (strcmp(param, "OTAP") == 0) {
        truncated = safe_strncpy_remove_slash (firmware_primary_prefix, value, MAX_LONG_STRING_LENGTH);
        return truncated;
    }
    if (strcmp(param, "OTAS") == 0) {
        truncated = safe_strncpy_remove_slash (firmware_secondary_prefix, value, MAX_LONG_STRING_LENGTH);
        return truncated;
    }
    if (strcmp(param, "CERTP") == 0) {
        truncated = safe_strncpy_remove_slash (certificate_primary_prefix, value, MAX_LONG_STRING_LENGTH);
        return truncated;
    }
    if (strcmp(param, "CERTS") == 0) {
        safe_strncpy_remove_slash (certificate_secondary_prefix, value, MAX_LONG_STRING_LENGTH);
        return truncated;
    }
    if (strcmp(param, "GRP") == 0) {     
        safe_strncpy (group_id, value, MAX_TINY_STRING_LENGTH);
        if (!truncated) {
            make_derived_params(); 
            // TODO: resubscribe to the new topic
        }
        return truncated;
    } 
       
    //if (strcmp(param, "ORG") == 0) {         
    //    safe_strncpy (org_id, value, MAX_TINY_STRING_LENGTH);
   //     if (!truncated)
    //        make_derived_params(); // TODO: resubscribe to the new topic
   //     return truncated;
   // } 
   // if (strcmp(param, "APP") == 0) {         
   //     safe_strncpy (app_id, value, MAX_TINY_STRING_LENGTH); 
   //     if (!truncated)
   //         make_derived_params(); // TODO: resubscribe to the new topic
   //     return truncated;
   // }    
     
    if (strcmp(param, "PRIREL") == 0) {         
        int rel = atoi(value); // returns zero if the integer string is invalid
        if (rel > 0 && rel < NUM_RELAYS) { 
            primary_relay = rel; 
            return false;  // false: all is OK
        }
        SERIAL_PRINTLN("\n*** Invalid relay number ****");
        return true; // true: ERROR
    }      
    if (strcmp(param, "ACTL") == 0) {
        if (value[0]=='1')      
            active_low = true;
        else 
            if (value[0]=='0')      
                active_low = false;  
            else 
                return true;  // ERROR 
        make_derived_params();
        return false;  // OK
    }     
    if (strcmp(param, "RTRIG") == 0) {         
        if (value[0]=='1')      
            radar_triggers = true;
        else 
            if (value[0]=='0')      
                radar_triggers = false;  
            else 
                return true;  // ERROR 
        return false;  // OK
    }          
    SERIAL_PRINTLN (F("--- ERROR: Unknown parameter ---"));     
    return true; // ERROR
}
****/
