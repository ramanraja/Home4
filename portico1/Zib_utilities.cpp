// utilities.cpp

#include "Zib_common.h"

// http://www.cplusplus.com/reference/cstring/strncpy/ 
// http://www.cplusplus.com/reference/cstring/strncat/

// TODO: develop this into a comprehensive utility class
// utility methods for string copying with bounds check
// It just truncates source strings that are too long **

// Need for this file: if the destination string is not large enough to hold the contents,
// then the behaviour is undefined in the case of plain vanilla strncpy and strncat.
// Also, if strncpy has to truncate the source, then there is no space for the null
// character, so it is left unterminated !

bool safe_strncpy (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH) 
{
    bool truncated = false;
    if (strlen(src) > (length-1)) {
        SERIAL_PRINTLN(F("***** String length is too long to copy !! TRUNCATING.... ******"));
        truncated = true;
    }
    strncpy (dest, src, length-1);  // this copies exactly length-1 characters. You need one more for null
    dest[length-1] = '\0';  // if it overflows, destination string becomes unterminated ! 
    #ifdef VERBOSE_MODE
        SERIAL_PRINT(F("string copied: "));
        SERIAL_PRINTLN (dest);
    #endif
    return truncated;
}

// if a string ends in a slash, remove that character
bool safe_strncpy_remove_slash (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH) 
{
    bool truncated = safe_strncpy (dest, src, length);  
    int len = strlen(dest);
    if (dest[len-1] == '/')  // remove any trailing slash
        dest[len-1] = '\0';
    dest[length-1] = '\0';  // extra layer of safety
    #ifdef VERBOSE_MODE
        SERIAL_PRINT(F("string copied: "));
        SERIAL_PRINTLN (dest);
    #endif
    return truncated;    
}

// copies a string without causing overflow; if the source does not end in a slash (/), adds it.
bool safe_strncpy_add_slash (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH) 
{
    bool truncated = false;
    if (strlen(src) > (length-2)) { // leave one for slash, one for null 
        SERIAL_PRINTLN(F("***** String length is too long to copy !! TRUNCATING.... ******"));
        truncated = true;
    }
    strncpy (dest, src, length-2);  // strncpy copies exactly n characters; we add 2 for slash and null
    int actual_length = min((int)strlen(src), length-2); // NOTE: strlen() excludes the null: strlen("abcd")=4
    SERIAL_PRINTLN(actual_length);
    if (dest [actual_length-1] != '/') {
        dest [actual_length] = '/';          // this overwrites the null that was at str[strlen]
        dest [actual_length+1] = '\0';       // NOTE: we are expanding by one character
    }
    dest[length-1] = '\0';  // for double safety:
                            // if it overflows, destination string becomes unterminated ! 
    #ifdef VERBOSE_MODE
        SERIAL_PRINT(F("copied: "));
        SERIAL_PRINTLN (dest);
    #endif
    return truncated;
}
 
bool safe_strncat (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH) 
{
    bool truncated = false;
    int slen = strlen(src); 
    int dlen = strlen(dest);
    #ifdef VERBOSE_MODE
      SERIAL_PRINT(F("Src: ")); SERIAL_PRINT(slen); 
      SERIAL_PRINT(F(" Dest: ")); SERIAL_PRINTLN(dlen);
    #endif
    if ((slen+dlen) > (length-1)) {
        SERIAL_PRINTLN(F("***** String lengths are too long to concatenate !! TRUNCATING.... ******"));
        truncated =true;
    }
    strncat (dest, src, length-dlen-1);   // strncat copies exactly n characters, plus adds a null
    dest[length-1] = '\0';  // if it overflows, destination string becomes unterminated ! 
    #ifdef VERBOSE_MODE
        SERIAL_PRINT(F("copied: "));
        SERIAL_PRINTLN (dest);
    #endif
    return truncated;
}

void print_heap() {
    SERIAL_PRINT(F("Free Heap: ")); 
    SERIAL_PRINTLN(ESP.getFreeHeap()); //Low heap can cause problems  
}
