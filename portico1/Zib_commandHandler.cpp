// CommandHandler.cpp

#include "hardware.h"
#include "Zib_commandHandler.h" 

// external callback functions defined in main .ino file 
void reset_wifi();
void check_for_updates();
bool is_night_time(); // this gets the cached value in main .ino

/**
#ifndef PORTICO_VERSION 
  bool is_occupied();
#endif
**/

CommandHandler::CommandHandler() {
}
 
void CommandHandler::init(Config *pconfig, MqttLite *pclient, Hardware *phardware) {
    pC = pconfig;
    pClient = pclient;
    pHard = phardware;
}
 
// Takes the global status message and publishes it
// NOTE: You MUST set up the status_message before calling this !
void CommandHandler::publish_message () {
    status_msg[MAX_MSG_LENGTH-1] = '\0';  // for safety, in case our snprintf() overflowed
    //SERIAL_PRINT(F("Publishing: "));
    //SERIAL_PRINTLN(status_msg);
    pClient->publish(status_msg);
}

void CommandHandler::send_not_implemented () {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"LOG\":\"NOT_IMPLEMENTED\"}");
    publish_message();
}    

void CommandHandler::send_booting_msg() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"BOOT\":{\"APP\":\"%s\",\"MAC\":\"%s\",\"HW\":\"%s\",\"RELS\":\"%d\",\"FW\":\"%d\"}}", 
              APP_NAME, pC->mac_address, HARDWARE_TYPE, NUM_RELAYS, FIRMWARE_VERSION); 
    publish_message();
}     
         
void CommandHandler::send_status () {  
    // this is pull model; in response to an MQTT command
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"STA\":\"%s\"}", pHard->get_relay_status());    
    publish_message();
}

// Sends an outgoing message to Hub to get the time; this is asynchronous request.
// The hub is expected to respond with a message like '+TIM 12 20' 
void CommandHandler::request_time() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"REQ\":\"TIME\"}");    
    publish_message();
}

void CommandHandler::send_data () { //TODO: replace with hardware->get_data()
    if (data_paused) {
        send_paused_msg();
        return; 
    }
    // this is pull model; in response to an MQTT command; gets the last known values (not current)
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"STA\":\"%s\",\"DAT\":{\"LIGHT\":%d,\"RSSI\":%d,\"HEAP\":%ld}}", 
              pHard->get_relay_status(), pHard->get_light_level(), pHard->get_RSSI(), ESP.getFreeHeap());    
    publish_message();
}

void CommandHandler::get_param(const char* param) {
     snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"%s\":\"%s\"}", param, pC->get_param(param)); 
     publish_message();
}

void CommandHandler::send_paused_msg() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"INFO\":\"DATA_PAUSED\"}");    
    publish_message();  
}

void CommandHandler::send_version() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"VER\":\"%d\"}", FIRMWARE_VERSION);    
    publish_message();
}

// Send MAC address - This is useful for polling the devices on the broadcast topic
void CommandHandler::send_mac_address() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"MAC\":\"%s\"}", pC->mac_address);    
    publish_message();
}

void CommandHandler::send_signal_strength() {  // TODO: the single letter id keys are unviable!
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"RSSI\":%d}", pHard->get_RSSI());    
    publish_message();     
}

void CommandHandler::send_heap() {
    long heap = ESP.getFreeHeap();
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"HEAP\":%ld}", heap);    
    publish_message();
}

void CommandHandler::send_org() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"ORG\":\"%s\"}", pC->org_id);    
    publish_message();
}

void CommandHandler::send_group() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"GRP\":\"%s\"}", pC->group_id);    
    publish_message();
}

// a command was received to put the device in auto mode
void CommandHandler::auto_mode () {
    manual_override = false;  // this puts the device in auto mode
    send_mode();
}

// a command was received to put the device in manual mode
// "A" tag stands for both auto/manual mode
void CommandHandler::manual_mode () {
    manual_override = true;  // this puts the device in manual mode
    send_mode();
}

// Logging values ("L") are responses to queries received
// To check whether we are following active low or active high
void CommandHandler::send_active_onoff() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"LEVEL\":\"ON=%d, OFF=%d\"}", pC->ON,pC->OFF);    
    publish_message();
}

void CommandHandler::send_current_time() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"TIME\":\"%s\"}",  pC->get_time());
    publish_message();
}

void CommandHandler::send_is_night() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"IS_NIGHT\":%d\,\"TIME_IN_SYNC\":\"%s\"}", is_night_time(), pC->time_never_synced? "N" : "Y");    
    publish_message();
}

// invalid command
void CommandHandler::send_error() { 
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"ERR\":\"CMD_ERROR\"}");    
    publish_message();
}

// send the current mode
void CommandHandler::send_mode() {
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"MODE\":\"%s\"}", manual_override? "MANUAL":"AUTO");    
    publish_message();
}

void CommandHandler::send_is_occupied() {  // TODO: decide how to use this
    SERIAL_PRINTLN(F("is_occupied flag is not valid for Relay Controller"));  
    send_not_implemented(); 
}
 
// This rebooting happens in response to a remote MQTT command to restart.
// (Autonomous rebooting will go under "BOOT" tag).
void CommandHandler::reboot() {
    print_heap();  
    snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"LOG\":\"Device is rebooting!\"}");    
    publish_message();
    SERIAL_PRINTLN(F("Restarting ESP..."));
    //yield();
    delay(100);    
    pHard->reboot_esp();
}

// Downloads config.txt file. If successful, restarts the device
void CommandHandler::download_config(){
    print_heap();
    int result = pC->download_config();
    print_heap();
    if (result==CODE_OK) {
        snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"LOG\":\"Config updated; restarting\"}");  
        publish_message();
        SERIAL_PRINTLN(F("Restarting ESP..."));
        //yield();
        delay(100);
        pHard->reboot_esp();
    } else {
        snprintf (status_msg, MAX_MSG_LENGTH-1, "{\"ERR\":\"Failed to download config-%s\"}", pC->get_error_message(result));  
        publish_message();      
    }
} 
//--------------------------------------------------------------------------------------
// TODO: move most of these to Config get() method, using -PARAM commands
#define  NUM_COMMANDS    23  // excluding on and off commands; index runs from 0 to NUM_COMMANDS-1
// NOTE: If you change the order of the following strings, you must change the switch cases also !
const char* commands[] = { "STA", "VER", "MAC", "GRO", "ORG", "HEA", "REB", "DEL", "UPD", "AUT", "MAN", 
                           "MOD", "BL0", "BL1", "DAT", "CON", "LOJ", "ISN", "OCC", "PAU", "RES", "SIG", "TIM"};

// TODO: remove all get() kind of commands and move them to Config using '-PARAM' syntax
void CommandHandler::handle_command(const char* command_string) {
    if (strlen (command_string) < 3) {
        SERIAL_PRINTLN(F("Command can be: STA,UPD,VER,MAC,HEA,DEL,GRO,ORG,RES,ONx,OFx etc"));
        return;
    }
    // ON commands: ON0, ON1 etc
    if (command_string[0]=='O' && command_string[1]=='N') { 
        if (command_string[2] < '0' ||  command_string[2] >= NUM_RELAYS+'0') 
            SERIAL_PRINTLN(F("-- Error: Invalid relay number --"));
        else
            pHard->relay_on(command_string[2] - '0'); // this sends the status also 
        print_heap();
        return;
    }
    // OFF commands: OF0, OF1 etc.
    if (command_string[0]=='O' && command_string[1]=='F') { 
        if (command_string[2] < '0' ||  command_string[2] >= NUM_RELAYS+'0') 
            SERIAL_PRINTLN(F("-- Error: Invalid relay number --"));
        else
            pHard->relay_off(command_string[2] - '0'); // this sends the status also 
        print_heap();
        return;
    }
    int command_index = -1;
    for (int i=0; i<NUM_COMMANDS; i++) {
        if (strcmp(command_string, commands[i]) == 0) {
            command_index = i;
            break;
        }
    }
    if (command_index < 0) { // received cmd is out of syllabus
       SERIAL_PRINTLN(F("-- Error: Invalid command --"));
       send_error();
       print_heap();
       return;
    }
    switch (command_index) {
        case 0: // STA
            send_status();
            break;
        case 1: // VER
            send_version();
            break;
        case 2: // MAC
            send_mac_address();
            break;     
        case 3:  // GRO
            send_group();
            break;
        case 4: // ORG
            send_org();
            break;
        case 5:  // HEA
            send_heap();
            break;   
        case 6:  // REB
            reboot();
            break;
        case 7:  // DEL
            reset_wifi();  // TODO: decide how to use this
            break;
        case 8:  // UPD
            check_for_updates();
            break;     
        case 9:  // AUT
            auto_mode();
            break;
        case 10: // MAN
            manual_mode();
            break;                
        case 11: // MOD
            send_mode();
            break;               
        case 12: // BL0
            pHard->blink_led(BLINK_COUNT1);
            break;                
        case 13: // BL1
            pHard->blink_led(BLINK_COUNT2);
            break;       
        case 14: // DAT
            send_data(); // on-demand data
            break;            
        case 15: // CON
            download_config(); // download config.txt file in SPIFF
            break;                        
        case 16: // LOJ = on/off logic levels
            send_active_onoff();
            break;
        case 17: // ISN
            send_is_night();
            break;
        case 18: // OCC
            send_is_occupied(); // TODO: this is redundant 
            break;
        case 19: // PAU        
            SERIAL_PRINTLN(F("Data paused"));    
            data_paused = true;
            break;
        case 20: // RES           
            SERIAL_PRINTLN(F("Resuming data")); 
            data_paused = false;
            break;
        case 21: // SIG           
            send_signal_strength(); // send the RSSI value
            break;  
        case 22: // TIM           
            send_current_time();  
            break;              
        default :
            SERIAL_PRINTLN(F("-- Error: Invalid command index --")); // signals an implementation bug
            send_error();
            break;                              
    }
    print_heap();
}





 
