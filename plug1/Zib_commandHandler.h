// commandHandler.h
 
#ifndef COMMAND_HANDLER_H
#define COMMAND_HANDLER_H

#include "Zib_common.h"
#include "Zib_utilities.h"
#include "Zib_config.h"
#include "Zib_mqttLite.h"

#include "settings.h"

class Hardware;  // forward declaration is required

class CommandHandler  {
public:
    // manual_override is public because it is accessed frequently in main .ino 
    bool manual_override = false; // for remote commands, set this to true
    CommandHandler();
    void init (Config *pC, MqttLite *pClient, Hardware *phardware);
    void handle_command(const char* command_string);    
    void publish_message ();
    void send_not_implemented ();
    void send_booting_msg();
    void send_status ();
    void send_data ();
    void send_version();
    void send_is_night();
    void send_is_occupied();
    void send_active_onoff();
    void send_mac_address();   
    void send_signal_strength();
    void send_current_time();
    void send_heap();
    void send_org();
    void send_group();
    void reboot();
    void auto_mode ();
    void manual_mode ();
    void send_mode();
    void download_config();
    void send_paused_msg();
    void send_error();
    void get_param(const char *param);
    // TODO: set_param()
    void request_time(); 
    void update_time(); 
private:
    char status_msg[MAX_MSG_LENGTH];   // Reusable Tx message buffer
    int num_relays = NUM_RELAYS;
    bool data_paused = false;
    Config *pC;
    MqttLite *pClient;
    Hardware *pHard;    
};

#endif 
