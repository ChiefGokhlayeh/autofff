#ifndef EXAMPLE_H_
#define EXAMPLE_H_

#include <stdint.h>
#include <stdbool.h>

#include "included_header.h"

void SomeFunction1(void);
uint32_t SomeFunction2(void);
uint32_t SomeFunction3(uint32_t* param1);
uint32_t SomeFunction4(uint32_t param1, bool param2);
const volatile uint8_t* const SomeFunction5(const uint8_t** param1, bool param2);
void SomeFunction6(const uint8_t* const* param1, const uint8_t* const param2);
void* SomeFunction7(uint32_t param1, bool* param2)
{
}

#endif