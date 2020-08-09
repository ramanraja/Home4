// Downloader.cpp
// Downloads config file from cloud or a local server and saves it on the SPIFF of 8266

#include "Zib_downloader.h"

void Downloader::init (Config* configptr) {
    this->pC = configptr;
}

int Downloader::download_file() {
    SERIAL_PRINTLN(F("Downloading file..."));
    if (WiFi.status() != WL_CONNECTED) {
        SERIAL_PRINTLN(F("\n---- Cannot download: No WiFi ---"));
        return NO_WIFI;   
    }
    if (!SPIFFS.begin()) {
        Serial.println("--- Failed to mount file system. ---");
        return SPIFF_FAILED; 
    }
    list_files(); // before
    
    int result = save_config_file ();   
    SERIAL_PRINT(F("File download result code: "));
    SERIAL_PRINTLN(pC->get_error_message(result));

    list_files();  // after
    if (result==CODE_OK) {   
        SERIAL_PRINTLN(F("Config file contents: ")); 
        print_file();  
    }
    SPIFFS.end();  
    return result;   
}

// This function is versatile, but at the moment, it only downloads the config file
int Downloader::save_config_file () {
    // lesson learnt: never reuse the same HTTPClient object for a different web server!
    // you can reuse HTTP client for multiple file downloads, provided they are on the same server *
    WiFiClient wifi_client; 
    HTTPClient http;
    char* url = (char*)pC->get_config_url(); // hard coded; but it can download any file from the web
    if (!http.begin(wifi_client, url)) {   
        SERIAL_PRINTLN(F("--- Malformed URL ---"));
        // begin() failed, so no end() is not required?
        return BAD_URL;   
    }
    SERIAL_PRINT(F("Downloading: "));
    SERIAL_PRINTLN (url);
    int response_code = http.GET();
    SERIAL_PRINT(F("HTTP response code: "));
    SERIAL_PRINTLN (response_code);
    if (response_code <= 0) {
        SERIAL_PRINT(F("HTTP GET failed: "));
        SERIAL_PRINTLN(http.errorToString(response_code).c_str()); // the strings are defined only for negative codes
        http.end();
        return HTTP_FAILED;   
    }
    // file found at server: (or the library automatically redirected to new location?)
    //// if(response_code >= 200 && response_code <= 308) { // code 304 = content unmodified (TODO: revisit)
    if (response_code == HTTP_CODE_OK) {
        int spiff_result = write_to_spiff (http); // the http client object is passed to the SPIFF stream
        http.end();
        return spiff_result;        
    }    
    SERIAL_PRINTLN(F("--- HTTP GET failed. ---"));
    http.end();
    return NO_ACCESS;   //   todo: revisit
}

int Downloader::write_to_spiff (HTTPClient& http) {
    File f = SPIFFS.open((const char*)pC->config_file_name, "w");
    if (!f.isFile()) {
        SERIAL_PRINTLN(F("Failed to open file for writing."));
        return FILE_OPEN_ERROR;  
    }
    // the following call returns bytes written (negative values are error codes)
    int writer_result = http.writeToStream(&f);
    if (writer_result > 0) {
        SERIAL_PRINT(F("Bytes written to SPIFF: "));
        SERIAL_PRINTLN (writer_result);
        f.flush(); // TODO: revisit
        f.close();
        return CODE_OK;
    }
    f.close();
    SERIAL_PRINT(F("Failed to write to file stream. Code: "));
    SERIAL_PRINTLN (writer_result);
    return FILE_WRITE_ERROR;       
}

void Downloader::list_files() {
    /////SPIFFS.begin();  // this is done centrally
    SERIAL_PRINTLN(F("Listing files, sizes in your root folder.."));
    Dir dir = SPIFFS.openDir("/");
    while (dir.next()) {
        SERIAL_PRINT(dir.fileName());
        SERIAL_PRINT(F("    "));
        File f = dir.openFile("r");
        SERIAL_PRINTLN(f.size());
        f.close();  // this is important
    }
    //dir.close(); // this call does not exist. 
    //////SPIFFS.end();  
}

void Downloader::print_file () {
    SERIAL_PRINT(F("Opening config file for reading: "));
    SERIAL_PRINTLN (pC->config_file_name);    
    if (!SPIFFS.exists((const char*)pC->config_file_name)) {
        SERIAL_PRINT(F("\n--- Config file is missing---\n"));
        return;
    }
    File f = SPIFFS.open((const char*)pC->config_file_name, "r");
    if (!f.isFile()) {
      SERIAL_PRINTLN(F("Failed to open file for reading."));
      return;
    }
    SERIAL_PRINTLN(F("File opened. Contents:\n"));
    while(f.available()) {
      String line = f.readStringUntil('\n');
      SERIAL_PRINTLN(line);
    }    
    f.close();
}
 
