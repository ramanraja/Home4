// This is thehydroponics controller :  intof/hydro/status/G0/mac_id
// code is cloned from IoTRelay2.ino
// TODO: study repair_comm thoroughly and test various scenarios
// TODO: self-learn light thresholds based on time of the day; automatically adjust for
//   primary light falling on the LDR (light correction). Auto-learn for seasonal variations
//   in light intensity.
// TODO:
//   Try web sockets instead of MQTT/ MQTT over web sockets.
//   Send a command to SET MQTT SERVER = hive server and OTA URL = AWS cloud URL
//     This will even survive a reboot.
//     This can be done either from the mobile app or sending am MQTT messgae to the Hub, or by the customer pushing a button on the device.
//     This will enable you monitor the customer premises device remotely, diagnose and push FW upgrade if needed.
//     To revert back, SET MQTT SERVER = local host and OTA URL = local host throgh a remote mqtt command.
/*
// TODO:
// Test LED blinking for wifi failuare,MQTT failure
// implement comm_status and repair_comm()
// when there is comm_failure, keep blinking the LED (with siren-like PWM -feasible?)
// read light level (unblock the LDRs physically)
// Connect an external LED for Rhydo-Labz boards
// check all PubSubClient error messages and print the return code
// test it with 2 relays or 8 relays (check panic if 9th relay is added)
// implement set param command 
// implement reset_wifi_password
// if wifi or hub/mqtt broker fails: implement retry logic
// Make night start/end times more flexible; remove the constraint that end_time > start_time 
// TODO: ability to add multiple on/off schedules in a day
// A button on hub and a button on the device, to register (when pressed almost simultaneously)
// make use of persistent messages, QOS=1, sticky subscriptions and longer socket time out (existing: 15 sec)
*/
/***************************************************************************************
check list:
compiled for the correct hardware flash configuration? if this is not right, it will never
   recover from a FW update!
connecting the the right broker? *
FW updates: is the version in home.txt correct?

This is the new hydroponics and fish tank controller using Rhydolabs dual relay board
Operates 2 IoT relays through an MQTT broker on the local wifi/internet.
 
Changes for this particular board:
Flash: Generic 8266/ 1 MB/ 64KB/  470KB

settings.h : 
#define  AUTO_DAWN_DUSK_MODE    0 
#define  RELAY_ACTIVE_LOW  0       
#define  PRIMARY_RELAY     0    
#define  APP_ID            "home"  
#define  APP_NAME          "Hydroponics"  
 

conf_hydro.txt: 
"ACTIVE_LOW":0,
"PRIMARY_REL":0,

pins.h : 
#define HARDWARE_TYPE   "RHYD-REL2-LDR.1"
#define LDR_PRESENT
#define NUM_RELAYS    2
#define RELAY1        13       // for the 2-relay module
#define RELAY2        12  
#define LED           2
*******************************************************************************************/

#include "Zib_main.h"

// helper classes
Timer T;
Config C;
MyFi W;
Hardware hard;
MqttLite mqtt;
CommandHandler cmd;
OtaHelper ota; // TODO: create this only when needed ?

void setup() {
    hard.init_serial(); // this is almost like a static method, so OK to call before hard.init()
    C.init();  
    C.dump(); // this needs init_serial
    hard.init(&C, &T, &cmd); // this needs properly initialized C.active_low
    // buy some time blinking the LED; the wifi can connect during that time.
    hard.blink0();
    bool wifi_ok = W.init (&C);
    bool mqtt_ok = mqtt.init (&C, &W);
    cmd.init (&C, &mqtt, &hard);
    ota.init (&C, &mqtt);
    if (!wifi_ok)  // total communication failure
          hard.blink3();  // rapid blinks
    else {
          if (!mqtt_ok) // MQTT failed, but wifi is OK
               hard.blink2();  // fast blinks   
          else  // all is well
               hard.blink1();  // slow blinks
    }
    cmd.send_booting_msg();
    delay(1000);
    cmd.request_time(); // priming read
    delay(1000);
    yield();
    SERIAL_PRINTLN(F("Priming:Check day or night.."));
    check_day_or_night();  // this sets is_night flag
    operate_relays();   // this uses is_night flag
    SERIAL_PRINTLN(F("Setting up timers.."));
    //T.every(C.tick_interval, tick); // TODO: implement this, if neessary
    T.every(60000, one_minute_logic);  // This is hard coded because dead reckoning needs exactly 1 minute increments
}

void loop() {
    T.update();
    if (W.update())
        mqtt.update();
}

// one_minute_logic() is called every 1 minute by the Timer
// Counts upto,say, 5 and then triggers five_minute_logic()
short minute_count = 0;   // counts from 0 to 5 and resets
void one_minute_logic() {  
    //print_heap();
    C.increment_clock(); // dead reckoning
    check_day_or_night(); // this merely sets the global variable is_night 
    hard.read_sensors();
    minute_count++;
    if (minute_count < C.status_report_frequency) // usually 5 minutes
        return;
    minute_count = 0;    
    five_minute_logic();
}

void five_minute_logic() {   // ie,usually 5 minutes!
    cmd.request_time();
    if (C.auto_dawn_dusk_mode && !cmd.manual_override)
        operate_relays();         // if is_night==true, operate the primary relay & vice-versa
    hard.prepare_status_data();   // compute the average readings
    cmd.send_data();  
    repair_comm(); 
    print_heap();
}

short is_night = TIME_UNKNOWN;
short was_night = TIME_UNKNOWN;   // the previous state

void check_day_or_night () {       // updates the global variable is_night
    is_night = C.is_night_time();   
    if (is_night == TIME_UNKNOWN)   // get a second opinion
        is_night = hard.is_night_time();  // this can also be TIME_UNKNOWN
    if (is_night == TIME_NIGHT && was_night == TIME_DAY)
        handle_dusk_transition();  // day->night
    else
    if (is_night == TIME_DAY && was_night == TIME_NIGHT)
        handle_dawn_transition();  // night->day
    was_night = is_night;
}

// you must have called check_day_or_night() once before this
short is_night_time() {   // respond to query from remote
    return (is_night);
}

// you must call check_day_or_night() before this
void operate_relays() {
    if (is_night == TIME_NIGHT)
        hard.primary_light_on();
    else if (is_night == TIME_DAY)
        hard.primary_light_off();
    // otherwise (TIME_UNKNOWN), maintain status quo
}

void handle_dawn_transition() {
    SERIAL_PRINTLN (F("Good Morning!"));   
    /***
    if (occupied && !cmd.manual_override) {  
        occupied = false;
        hard.primary_light_off();
    }    
    ***/
    if (!cmd.manual_override) {
        hard.primary_light_off();
        cmd.send_status();
    }
}

void handle_dusk_transition() {
    SERIAL_PRINTLN (F("Good Night!"));    
    if (!cmd.manual_override) {
        hard.primary_light_on();
        cmd.send_status();
    }
}

bool repair_comm() {
  SERIAL_PRINTLN (F("\nREPAIR COMM STUB\n"));   // TODO: implement this
}

// MQTT subscribed message arrived
// NOTE: the incoming command from the hub is a simple text command; it is not Json formatted.
// Leading special characters like +,- and # are used when the command needs parsing
char time_str[3];
short hour, minute;
void  app_callback (const char* command_string) {
    SERIAL_PRINTLN (command_string); 
    if (command_string[0] == '-') {
        SERIAL_PRINT (F("GET PARAM request: "));
        SERIAL_PRINTLN ((char*)(command_string+1));
        cmd.get_param ((char*)(command_string+1)); // TODO: this runs on the MQTT thread; move this to the main loop 
    }
    else if (command_string[0] == '+') {
        SERIAL_PRINT (F("SET PARAM request: "));
        SERIAL_PRINTLN ((char*)(command_string+1)); // TODO: split it into name,value pair using space as delimiter
        SERIAL_PRINTLN (F("\n<<<--- THIS IS set-param STUB --->>>\n"));   // TODO: implement all params
        set_param ("par", "val");
    }   
    else if (command_string[0] == '#') {  // TODO: move it to +TIM
        SERIAL_PRINT (F("Time server notice: "));
        SERIAL_PRINTLN ((char*)(command_string+1)); 
        // The command string format is "#06:20"
        // TODO: make this more mature!
        if ((char)(command_string[3]) != ':') {
            SERIAL_PRINT (F("\n--- INVALID TIME ---\n"));
            return;
        }        
        time_str[0] = (char)(command_string[1]);
        time_str[1] = (char)(command_string[2]);
        time_str[2] = '\0';
        hour = atoi(time_str);
        time_str[0] = (char)(command_string[4]);
        time_str[1] = (char)(command_string[5]);
        time_str[2] = '\0';
        minute = atoi(time_str);
        if (hour < 0 || hour > 23 || minute < 0 || minute > 59) {
            SERIAL_PRINT (F("\n--- INVALID TIME ---\n"));
            cmd.send_error(); 
            return;
        }
        C.set_time (hour, minute);  
        cmd.send_current_time();
    }      
    else
        cmd.handle_command (command_string); // TODO: this runs on the MQTT thread; move this to the main loop
}

void check_for_updates() {
    SERIAL_PRINTLN(F("---Firmware update command received---"));
    ota.check_and_update();
    SERIAL_PRINTLN(F("Reached after OTA-check for updates.")); // reached if the update fails
}


void set_param (const char* param, const char *value) {  // TODO: implement this
    SERIAL_PRINTLN (F("\n<<<--- Set Param: This is a stub \n--->>>"));
   /***
    bool result = C.set_param(param, value); // this returns true if there was an error
    if (result) {
        SERIAL_PRINTLN (F("--- SET Failed ---"));
        pClient->publish(C.mqtt_pub_topic, "{\"I\":\"SET-ERROR\"}");
    }
    else {
        SERIAL_PRINTLN (F("SET: OK"));
        pClient->publish(C.mqtt_pub_topic, "{\"C\":\"SET-OK\"}");    
    }
    ***/
   cmd.send_not_implemented();
}

void reset_wifi() {
    SERIAL_PRINTLN (F("\n<<<--- Erase Wifi: This is a stub \n--->>>"));
    /**
    SERIAL_PRINTLN(F("\n*** ERASING ALL WI-FI CREDENTIALS ! ***"));   
    SERIAL_PRINTLN(F("You must configure WiFi after restarting"));
    pClient->publish(C.mqtt_pub_topic, "{\"I\":\"Erasing all WiFi credentials !\"}");
    delay(500);
    pClient->publish(C.mqtt_pub_topic, "{\"C\":\"Configure WiFi after restarting\"}");  
    myfi.erase_wifi_credentials(true); // true = reboot ESP
    ***/
   cmd.send_not_implemented();    
}
