#include "driver.h"

volatile Hardware HardwareHandle = NULL;

static void HandleDriverCallback(enum Driver_Event event)
{
    switch (event)
    {
    case DRIVER_EVENT_POWER_UP_COMPLETE:
        break;
    case DRIVER_EVENT_POWER_DOWN_COMPLETE:
        break;
    case DRIVER_EVENT_DATA_AVAILABLE:
        break;
    case DRIVER_EVENT_MAX:
    default:
        break;
    }
}

void App_DoDriverInit()
{
    Driver_Initialize(&HardwareHandle, HandleDriverCallback);
}
