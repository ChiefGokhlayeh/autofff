#include "gtest.h"
#include "fff.h"

extern "C"
{
#include "driver_th.h"

#include "app.c"
}

DEFINE_FFF_GLOBALS

#include "app_tests.cc"
