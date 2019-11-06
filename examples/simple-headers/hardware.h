#ifndef HARDWARE_H_
#define HARDWARE_H_

#include <string.h>

typedef void *Hardware;

/* Showcasing the skipping of headers that are included by the original */
const char *Hardware_GetDescription(const Hardware *hw);

#endif
