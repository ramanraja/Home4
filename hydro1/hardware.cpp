// hardware.cpp

#include "hardware.h"
#include "Zib_commandHandler.h"  //forward declaration in hardware.h: class CommandHandler; 

Hardware::Hardware () {
}

void Hardware::print_configuration() {
#ifdef ENABLE_DEBUG  
  #ifdef LDR_PRESENT
    SERIAL_PRINTLN (F("LDR present"));
  #else
    SERIAL_PRINTLN (F("No LDR"));
  #endif
  SERIAL_PRINT(F("Number of relays: "));
  SERIAL_PRINTLN (NUM_RELAYS);
  // command handler can only handle commands like ON0 to ON9, so the relay count has to be single digit ***
  // This is OK since 8266 has only a limited number of I/O pins
  if (NUM_RELAYS > MAX_RELAYS || MAX_RELAYS > 8)
        SERIAL_PRINT(F("\n\n\n ************  PANIC: TOO MANY RELAYS ! CANNOT CONTINUE !!   **************\n\n\n"));
#endif  
}

void Hardware::init (Config *configptr, Timer *timerptr, CommandHandler* cmdptr) {
  this->pC = configptr;
  this->pT = timerptr;
  this->pCmd = cmdptr;
  add_relays();
  ////init_serial(); // this is already called from main.ino
  print_configuration(); // this needs serial port
  init_hardware();
}

void Hardware::add_relays() {
  if (NUM_RELAYS > 0)relay_pin[0] = RELAY1;  
  if (NUM_RELAYS > 1)relay_pin[1] = RELAY2;
  if (NUM_RELAYS > 2)relay_pin[2] = RELAY3;
  if (NUM_RELAYS > 3)relay_pin[3] = RELAY4;    
  if (NUM_RELAYS > 4)relay_pin[4] = RELAY5;  
  if (NUM_RELAYS > 5)relay_pin[5] = RELAY6;
  if (NUM_RELAYS > 6)relay_pin[6] = RELAY7;
  if (NUM_RELAYS > 7)relay_pin[7] = RELAY8;     
}

// Tells if it is day or night based on LDR reading
// The output is ternary: day,night,unknown
short Hardware::is_night_time() {
#ifdef LDR_PRESENT  
    int lite = 0;
    for (int i=0; i<5; i++) {
        lite += analogRead(LDR);
        delay(5);  // Do not call this from the main loop
    } 
    lite = (int) (lite/5);  
    lite = MAX_LIGHT - lite;  // invert it - more light, bigger the number
    if (relay_status[pC->primary_relay] == 1)
        lite = max (lite - pC->light_correction, 0);
    SERIAL_PRINT(F("Light level: "));
    SERIAL_PRINTLN(lite);
    //if (lite > (MAX_LIGHT-NOISE_THRESHOLD)) // light sensor failure threshold=10
    //    return TIME_UNKNOWN;      // commented out because the LDR voltage can actually max out during night!
    if (lite < pC->night_light_threshold)    
        return TIME_NIGHT;
    if (lite > pC->day_light_threshold)         
        return TIME_DAY;
    return TIME_UNKNOWN;  // in the forbidden zone
#else       
    return TIME_UNKNOWN;   // in the buffer zone for Schmidt trigger
#endif 
}

const char* Hardware::get_relay_status() {
    for (int i=0; i<NUM_RELAYS; i++)  // relay[0] is represented on the right at LSB
        relay_status_str[i] = relay_status[NUM_RELAYS-1-i] ? '1' : '0';
    relay_status_str[NUM_RELAYS] = '\0';
    return ((const char *)relay_status_str);
}

const char* Hardware::get_data () {
  // TODO: implement this !
  //snprintf (data_reusable_str, MAX_MSG_LENGTH-1, "{\"STA\":\"%s\",\"DAT\":{\"LIGHT\":%d,\"RSSI\":%d,\"HEAP\":%ld}}", 
  //            get_relay_status(), get_light_level(), get_RSSI(), ESP.getFreeHeap());  
}

int Hardware::get_light_level() {
    return (light_level);
}

 // get the received WiFi signal strength at the device
int Hardware::get_RSSI() {
  return (WiFi.RSSI());
}

void Hardware::read_sensors() {
#ifdef LDR_PRESENT
     analog_reading += analogRead(LDR); // assumption: light was read correctly all the times
#endif  
     sensor_reading_count++;  // count only successful reads - some times the DHT may return null, do do not count them
}

void Hardware::prepare_status_data () {
#ifdef LDR_PRESENT
    if (sensor_reading_count > 0)  // only for safety; it is always equal to status_report_frequency
        light_level = (int) (analog_reading/sensor_reading_count);   
    light_level = MAX_LIGHT-light_level;  // invert it, as the LDR is connected from A0 to ground 
    if (relay_status[pC->primary_relay] == 1)
        light_level = max (light_level - pC->light_correction, 0);    
#else
    light_level = 0;
#endif
    analog_reading = 0;   // reset for next reading
    sensor_reading_count = 0;
}

// NOTE: Check if the serial Rx line has been taken away for I/O in your hardware.
// This is almost like a static method, so it can be called before init(&C)
void Hardware::init_serial() {
  #ifdef ENABLE_DEBUG
      Serial.begin(BAUD_RATE); 
      #ifdef VERBOSE_MODE
        Serial.setDebugOutput(true);
      #endif
      Serial.setTimeout(250);
  #endif    
  SERIAL_PRINTLN(F("\n\n ***************** Intof IoT device starting.. ******************\n"));  
  SERIAL_PRINT(F("FW version: "));
  SERIAL_PRINTLN(FIRMWARE_VERSION);
}

// internal function
void Hardware::init_hardware() {
    for (int i=0; i<NUM_RELAYS; i++) {
    pinMode(relay_pin[i], OUTPUT);
    digitalWrite(relay_pin[i],pC->OFF);  // assumes pC->OFF has been configured after reading settings file 
  }  
  pinMode(led, OUTPUT);
  ///blink1();  // this is done from main
}

// use these sparingly, if at all!
void Hardware::operate_all_relays() {
    for (int i=0; i<NUM_RELAYS; i++) {
        digitalWrite(relay_pin[i],pC->ON);   
        delay(50);  // to avoid surge currents
    }
} 

void Hardware::release_all_relays() {
    for (int i=0; i<NUM_RELAYS; i++) {
        digitalWrite(relay_pin[i],pC->OFF);   
        delay(10);  // to avoid surge voltage spikes?
    }
} 
  
// these two are invoked by algorithm based on light level or time of the day or movement
void Hardware::primary_light_on() {
  digitalWrite (relay_pin[pC->primary_relay], pC->ON);
  relay_status[pC->primary_relay] = 1;
}

void Hardware::primary_light_off() {
  digitalWrite (relay_pin[pC->primary_relay], pC->OFF);
  relay_status[pC->primary_relay] = 0;
}       
        
// these two are invoked by remote MQTT command
// either of the two relays can be operated
void Hardware::relay_on (short relay_number) {
  SERIAL_PRINT(F("Remote command: ON; Relay : "));
  SERIAL_PRINTLN (relay_number);  
  digitalWrite (relay_pin[relay_number], pC->ON);
  relay_status[relay_number] = 1;
  pCmd->send_status();  // TODO: send the status as an argument? NO. even the main .ino can send data
}

void Hardware::relay_off (short relay_number) {
  SERIAL_PRINT(F("Remote command: OFF; Relay : "));
  SERIAL_PRINTLN (relay_number);    
  digitalWrite (relay_pin[relay_number], pC->OFF);
  relay_status[relay_number] = 0;
  pCmd->send_status();  // TODO: send the status as an argument? NO. even the main .ino can send data
}

void Hardware::blink0() {
  for (int i=0; i<3; i++) {
      digitalWrite (led, LED_ON);   
      delay(500);
      digitalWrite (led, LED_OFF);   
      delay(100);               
  }
}

void Hardware::blink1() {
  for (int i=0; i<4; i++) {
      digitalWrite (led, LED_ON);   
      delay(250);
      digitalWrite (led, LED_OFF);   
      delay(250);               
  }
}

void Hardware::blink2() {
  for (int i=0; i<6; i++) {
      digitalWrite (led, LED_ON);  
      delay(100);
      digitalWrite (led, LED_OFF);   
      delay(100);               
  }
}

void Hardware::blink3() {
  for (int i=0; i<10; i++) {
      digitalWrite (led, LED_ON);    
      delay(50);
      digitalWrite (led, LED_OFF);    
      delay(50);               
  }
}

void Hardware::led_on () {
    digitalWrite(led, LED_ON);  
}

void Hardware::led_off () {
    digitalWrite(led, LED_OFF);   
}

void Hardware::set_led (bool is_on) {
    digitalWrite(led, is_on ? LED_ON : LED_OFF);   
}

void Hardware::blink_led (byte times) {
    pT->oscillate(led, 200, LED_OFF, times);      
}

void Hardware::reboot_esp() {
    SERIAL_PRINTLN(F("\n *** Intof IoT Device will reboot now... ***"));
    delay(2000);
    ESP.restart();    
}

//  This is an infinite loop ***
void Hardware::infinite_loop() {
    static bool temp = 0;
    while (true)  {  // NOTE: infinite loop outside main loop *
      digitalWrite(led, temp);   
      delay(300);
      temp = !temp;
      digitalWrite(led, temp);   
      delay(300);
    }
}
