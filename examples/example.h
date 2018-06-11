#ifndef EXAMPLE_H_
#define EXAMPLE_H_

#include <stdint.h>
#include <stdbool.h>

#include "included_header.h"

void SomeFunction1(void);
uint32_t SomeFunction2(void);
uint32_t SomeFunction3(uint32_t* param1);
uint32_t SomeFunction4(uint32_t param1, bool param2);
void* SomeFunction5(uint32_t param1, bool* param2)
{
}

#endif