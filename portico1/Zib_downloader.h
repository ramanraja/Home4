//Downloader.h
// Downloads a file from the internet and saves it on the SPIFF of 8266
#ifndef DOWNLOADER_H
#define DOWNLOADER_H

#include "Zib_common.h"
#include "Zib_config.h"
#include <FS.h>
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266HTTPClient.h>
//#include <WiFiClientSecureBearSSL.h>  // part of Arduino 8266 library
 
class Config;  // forward declaration is needed, since Config creates the Downloader object
 
class Downloader {
public:
    void init(Config* configptr);
    int download_file(); // this downloads only the config file
private:
    Config* pC;
    // lesson earnt: never reuse the same HTTPClient object for a different web server!
    int save_config_file ();
    void list_files(); 
    void print_file (); // only for text files    
    int write_to_spiff (HTTPClient& http);  
};
 
#endif
