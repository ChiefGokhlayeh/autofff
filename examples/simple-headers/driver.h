#ifndef DRIVER_H_
#define DRIVER_H_

#include "hardware.h"

#include <stdlib.h>
#include <stdint.h>

/* Dummy driver events for demonstrative purposes */
enum Driver_Event
{
    DRIVER_EVENT_POWER_UP_COMPLETE,
    DRIVER_EVENT_POWER_DOWN_COMPLETE,
    DRIVER_EVENT_DATA_AVAILABLE,

    DRIVER_EVENT_MAX
};

typedef void (*Driver_EventCallback)(enum Driver_Event);
typedef void *Config;

/* Showcasing complex pointer qualifiers in parameter list */
void Driver_Initialize(volatile const Hardware *const hardware, Driver_EventCallback callback);

/* Showcasing complex pointer qualifiers in return value */
volatile const Hardware *Driver_GetHardware(void);

/* Showcasing pointers */
size_t Driver_Write(const uint8_t *buffer, const size_t size);

/* Showcasing out-parameter pointers */
void Driver_GrabBuffer(const uint8_t **buffer, size_t *size);

/* Showcasing in-line function pointer parameters */
void Driver_PowerUp(Config (*config_cb)(void *arg));

void Driver_PowerDown(void);

/* Showcasing in-line function pointer parameters that return pointer */
void Driver_Register_Callback(void *(*cb)(void *arg));

int Driver_Deinitialize(void);

/* Showcasing inline definition workaround */
uint16_t Driver_GetRevision(void)
{
    return 120;
}

/* Showcasing vararg/ellipsis parameters */
void debug_print(const char *format, ...);

#endif
