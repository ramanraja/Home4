// myfi.h

#ifndef MYFI_H
#define MYFI_H

#include "Zib_common.h"
#include "Zib_config.h"
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>

class MyFi {
public:
    MyFi();
    bool init(Config* configptr);
    ////void update(); // call this periodically, say once in a few seconds
    ////bool checkWifi();
    void disable();
    bool isConnected();
    bool reconnect();
    bool update();
    void dump();
private:
    Config *pC;
    ESP8266WiFiMulti wifi_multi_client;
    bool wifi_connected;
};

#endif 
