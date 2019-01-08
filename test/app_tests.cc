/* Intendet to be included by _unittest.cc file. Only contains the test suites and fixtures. */

class TS_App_SmokeTest: public testing::Test
{
public:
    void SetUp()
    {
        FFF_RESET_HISTORY();
    }
};

TEST_F(TS_App_SmokeTest, Success)
{
    ASSERT_TRUE(1);
}

class TS_App_DoDriverInit: public testing::Test
{
public:
    void SetUp()
    {
        FFF_RESET_HISTORY();

        RESET_FAKE(Driver_Initialize);
    }
};

TEST_F(TS_App_DoDriverInit, Success)
{
    App_DoDriverInit();

    ASSERT_EQ(1U, Driver_Initialize_fake.call_count);
    ASSERT_EQ(&HardwareHandle, Driver_Initialize_fake.arg0_val);
    ASSERT_EQ((void*) HandleDriverCallback, (void*) Driver_Initialize_fake.arg1_val);
}
