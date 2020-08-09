// utilities.h
#ifndef UTILITIES_H
#define UTILITIES_H

#include "common.h"

extern bool safe_strncpy (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH); 
extern bool safe_strncat (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH);
extern bool safe_strncpy_remove_slash (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH); 
extern bool safe_strncpy_add_slash (char *dest, const char *src, int length=MAX_LONG_STRING_LENGTH); 
extern bool print_heap(); 

#endif
