#include "gtest.h"
#include "fff.h"

extern "C"
{
#include "driver_th.h"

#include "app.c"
}

DEFINE_FFF_GLOBALS

class TS_Driver_SmokeTest: public testing::Test
{
public:
    void SetUp()
    {
        FFF_RESET_HISTORY();
    }
};

TEST_F(TS_Driver_SmokeTest, Success)
{
    ASSERT_TRUE(1);
}