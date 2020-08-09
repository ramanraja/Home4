// otaHelper.cpp
// https://github.com/esp8266/Arduino/blob/master/libraries/ESP8266httpUpdate/examples/httpUpdate/httpUpdate.ino

#include "Zib_otaHelper.h"

// life cycle methods
#ifdef ENABLE_DEBUG
void update_started() {
    SERIAL_PRINTLN(F("[CallBack] OTA update started."));
}
void update_finished() {
    SERIAL_PRINTLN(F("[CallBack] OTA update finished!"));
}
void update_progress(int cur, int total) {
    SERIAL_PRINT(F("[CallBack] OTA update progress (bytes): "));
    SERIAL_PRINT (cur);
    SERIAL_PRINT(F(" of "));
    SERIAL_PRINTLN (total);
}
void update_error(int err) {
    SERIAL_PRINT(F("[CallBack] OTA update failed. error code: "));
    SERIAL_PRINTLN (err);
}
#endif
//---------------------------------------------------------------------------------

OtaHelper::OtaHelper() {
}

#ifdef MQTT_ENABLED
/*
void OtaHelper::init (Config *configptr,  PubSubClient *mqttptr) {
    this->pC = configptr;
    this->pM = mqttptr;    
    SERIAL_PRINTLN(F("OtaHelper:  MQTT PubSub version"));
}
*/
void OtaHelper::init (Config *configptr,  MqttLite *mqttptr) {
    this->pC = configptr;
    this->pM = mqttptr;    
    SERIAL_PRINTLN(F("OtaHelper:  MQTT Lite version"));
}
#else
void OtaHelper::init(Config *configptr) {
    this->pC = configptr;
    SERIAL_PRINTLN(F("OtaHelper:  Non-MQTT version"));
}
#endif

void OtaHelper::publish_msg () {
    reusable_str[MAX_MSG_LENGTH-1] = '\0';  // for safety, in case our snprintf() overflowed
    SERIAL_PRINTLN (reusable_str);        
#ifdef MQTT_ENABLED
    pM->publish (reusable_str);  
#endif
}

int OtaHelper::check_and_update() { 
   if (WiFi.status() != WL_CONNECTED) {
        SERIAL_PRINTLN(F("OtaHelper: No wifi connection !"));  // TODO: move this to get_error_string() at the caller
        return NO_WIFI;   
    }  
    SERIAL_PRINTLN(F("Checking for new firmware..."));
    snprintf (reusable_str, MAX_MSG_LENGTH-1, "{\"O\":\"Current firmware version: %d\"}", FIRMWARE_VERSION);
    publish_msg();
    
    int result = check_version();
    if (result != PROCEED_TO_UPDATE) {
      SERIAL_PRINTLN(F("Version check failed."));          
      return (VERSION_CHECK_FAILED);       
    }
    result = update_firmware();  
    return(result); 
}


// Version check: Have a text file at the version_check_url, containing just a single number. 
// The number is the version of the firmware ready to be downloaded.
int OtaHelper::check_version() {
    if (!pC->version_check_enabled) {
        SERIAL_PRINTLN(F("Version checking not enabled. Proceeding to update firmware.."));
        return (PROCEED_TO_UPDATE);
    }
    char* url = (char *)pC->get_version_url();
    SERIAL_PRINTLN(F("Downloading firmware version check file: "));
    SERIAL_PRINTLN(url);
    
    HTTPClient client;
    if (!client.begin(url)) {
        SERIAL_PRINTLN(F("--- Malformed version check URL ---")); // TODO: move this to get_error_string() at the caller
        return (BAD_URL);
    }
    int httpCode = client.GET();
    SERIAL_PRINT(F("HTTP GET result: "));
    SERIAL_PRINTLN (httpCode);
    if(httpCode == 200 ) { // TODO: there may be other codes; handle them
        String str_version = client.getString();
        SERIAL_PRINT(F("Current firmware version: "));
        SERIAL_PRINTLN(FIRMWARE_VERSION);
        SERIAL_PRINT(F("Available firmware version: "));
        SERIAL_PRINTLN(str_version);
        int newVersion = str_version.toInt();
        if(newVersion > FIRMWARE_VERSION) {
            SERIAL_PRINTLN(F("A new FW version is available"));         
            snprintf (reusable_str, MAX_MSG_LENGTH-1, "{\"O\":\"New FW Version %d found\"}", newVersion); 
            publish_msg();          
            client.end();
            return (PROCEED_TO_UPDATE);
        } // if version number is larger than current
        SERIAL_PRINTLN(F("This device already has the latest version."));          
        snprintf (reusable_str, MAX_MSG_LENGTH-1, "{\"O\":\"No new FW updates\"}"); 
        publish_msg();            
        client.end();
        return (NO_UPDATES);       
    } // if code==200  

    int result = VERSION_CHECK_FAILED;  
    if(httpCode > 200 && httpCode <= 308) { // code 304 = content unmodified; TODO: revisit!
        SERIAL_PRINTLN(F("Cannot  check version: content possibly moved."));
        result = VERSION_CHECK_FAILED;
    } else {  // HTTP response is 400s or 500s
        SERIAL_PRINT( "Cannot check firmware version. HTTP error: " );
        SERIAL_PRINTLN (httpCode );      
        result = HTTP_FAILED;
    }      
    snprintf (reusable_str, MAX_MSG_LENGTH-1, "{\"O\":\"Version check failed: HTTP error %d\"}", httpCode); 
    publish_msg();                
    client.end();
    return (result);
}    

int OtaHelper::update_firmware() {
    SERIAL_PRINTLN(F("Updating firmware.."));   
    snprintf (reusable_str, MAX_MSG_LENGTH-1, "{\"O\":\"Updating firmware..\"}"); 
    publish_msg();             
    char* url = (char*)pC->get_ota_url();
    SERIAL_PRINT(F("Looking for FW image file: "));
    SERIAL_PRINTLN(url);
    
#ifdef ENABLE_DEBUG    
    ESPhttpUpdate.onStart(update_started);
    ESPhttpUpdate.onEnd(update_finished);
    ESPhttpUpdate.onProgress(update_progress);
    ESPhttpUpdate.onError(update_error);
#endif
    
    ESPhttpUpdate.rebootOnUpdate(1);   // reboot if the update succeeds    
    ESPhttpUpdate.setLedPin(LED_BUILTIN, LOW); // blink for every chunk
            
    t_httpUpdate_return result_code = ESPhttpUpdate.update(url); // TODO: there is also an HTTPS version of this class
    
    // ----------- Now the ESP8266 will reboot ------------------
    
    // >>> will not reach here if the update succeeds <<<<
    SERIAL_PRINT(F("Response code from FW server: "));
    SERIAL_PRINTLN(result_code);
    int error_msg_code = 0; // 0 means no error
    int return_code = UPDATE_FAILED;    // this is the most likely case, unless rebootOnUpdate is set to 0
    switch (result_code) {
        case HTTP_UPDATE_OK: // will never reach this case, since we set rebootOnUpdate=1
            SERIAL_PRINTLN(F("HTTP update success !"));
            return_code = UPDATE_OK;
            break;
        case HTTP_UPDATE_FAILED:
            error_msg_code = ESPhttpUpdate.getLastError();
            SERIAL_PRINT(F("HTTP update FAILED. Error msg code = "));
            SERIAL_PRINTLN (error_msg_code); 
            SERIAL_PRINTLN (ESPhttpUpdate.getLastErrorString().c_str());
            return_code = UPDATE_FAILED;
            break;
        case HTTP_UPDATE_NO_UPDATES:  // this will arise only if you set the version number in the update() API call above
            SERIAL_PRINTLN(F("NO updates available"));
            return_code = NO_UPDATES; 
            break;
    }    
    snprintf (reusable_str, MAX_MSG_LENGTH-1, "{\"O\":\"FW update failed. result:%d, HTTP: %s, Error: %d\"}", 
             result_code, ESPhttpUpdate.getLastErrorString().c_str(), error_msg_code); 
    publish_msg();            
    return (return_code);
}
