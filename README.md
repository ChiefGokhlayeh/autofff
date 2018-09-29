# AutoFFF [![Build Status](https://travis-ci.org/FreeGeronimo/autofff.svg?branch=master)](https://travis-ci.org/FreeGeronimo/autofff)

Auto-generate [FFF](https://github.com/meekrosoft/fff) fake definitions for C API header files.

Incorporate the script into your normal build environment (like _make_) and automatically generate test-headers with faked function definitions ready-to-use with [FFF](https://github.com/meekrosoft/fff)'s own _gtest_ or some other unit-testing-framework.

## The Idea Behind Faking

Especially in the embedded world, running your (unit-)tests against the actual target platform often isn't feasible, as the architecture you're executing the test on and your target platform you're writing the code for are generally not the same.

This is where faking a specific platform API might help you. Instead of calling the actual target platform API, you link your code-under-test (CuT) against a faked version of said API. Now whenever your CuT tries to access the platform API it is instead calling the fake-implementation which you can easily configure in your test-cases' setup phase.

[FFF](https://github.com/meekrosoft/fff) (fake-functions-framework) is a framework designed to easily create faked definitions of your API function-declarations, allowing you to configure return values and inspect call and argument histories that were called during the tests' runtime.

The problem with faking an API in embedded C is usually the infeasibility of using dynamic linking and C's lack of techniques like 'reflection' to manipulate your CuT during runtime. This makes the process of writing fake definitions a tedious, labor intensive and error prone matter.

Introducing [*AutoFFF*](https://github.com/FreeGeronimo/autofff), an attempt at automating the process of writing so called test-headers (headers which include the faked definitions).

### Two Philosophies of Faking

When writing fakes you will notice that there are two approaches of laying out your fake.

1. **Banning** the original API header\
    This strategy *bans* the original header by defining the API headers include guard, making it impossible to include the original function, variable and type declarations. This gives you ultimate freedom in the test-header, but also means that you will have to manually declare any types, functions and variables the API-user might expect. It also allows you to control the include hierarchy and maybe skip some headers which aren't compatible with your test-runner's architecture. In general this approach usually involves a lot of copy&pasting and is therefore more prone to *"code rot"*. Not the optimal strategy if you're looking for an easy-to-maintain way of managing test-headers.
1. **Wrapping** the original API header\
    Conversely to the banning method the *wrapping* strategy directly includes the original API header, and thereby imports any type, variable and function declarations. Also the include hierarchy is taken over from the original. The only thing to add into the test-header are the fake definitions. This method evidently grants you less freedom in the test-header, but usually is much shorter and slightly less prone to *"rot"* over time.

It should become obvious which method is better suited for automation. Therefore *AutoFFF* follows the *wrapping* approach of writing test-headers, which for most cases should be good enough.

Finally it must be stated, that these two philosophies seldomly mix well.

## Installation

Use `pip` to download and install *AutoFFF* from the [PyPi](https://pypi.org/project/autofff/) repositories:

```shell
py -3.6 -m pip install autofff
```

Or install from source:

```shell
py -3.6 -m pip install .
```

## Usage

### As a Module

```shell
py -3.6 -m autofff \
    ./examples/driver.h \
    -O ./output/driver_th.h \
    -I ./examples \
    -F ./dependencies/pycparser/utils/fake_libc_include
```

### Using the provided Makefile

To run build and run the tests, simply execute:

```shell
make run_tests
```

You can also let the makefile do the installation of *AutoFFF* for you.

```shell
make install_autofff
```

### Running the 'Generate Fakes' Example

```shell
make -f examples/generate_fakes.mk CRAWL_PATHS=examples
```

### As a Python Package

```python
import autofff

import os.path

targetHeader = input("Enter the path of the header you would like to scan: ")
outputHeader = input("Enter the path of the target header file which shall be generated: ")
fakes = './autofff/dependencies/pycparser/utils/fake_libc_include'

scanner = autofff.scanner.GCCScanner(targetHeader, fakes) # Create GCC code scanner
result = scanner.scan() # Scan for function declarations and definitions

generator = autofff.generator.SimpleFakeGenerator(os.path.splitext(os.path.basename(outputHeader))[0], targetHeader) # Create new generator with name output-header and path to target-header

if not os.path.exists(os.path.dirname(outputHeader)):
    dirname = os.path.dirname(outputHeader)
    os.makedirs(dirname)

with open(outputHeader, "w") as fs:
    generator.generate(result, fs) # Generate fff-fakes from scanner-result
```

## How Fakes Are Generated

The format of the generated test-header obviously depends on the specifics of the `FakeGenerator` being used.

1. The `BareFakeGenerator` will only generate the `FAKE_VALUE_`- and `FAKE_VOID_FUNC` macros without any decorations, like include guards or header includes. Use this generator if you want to add your own file (shell-based) processing on top.
2. The `SimpleFakeGenerator` will generate a "minimum viable test header", meaning the result should be compilable without too much effort.

### In-Header Defined Functions

In some API headers functions may be defined within the header. This will cause issues when trying to fake this function, because by including the header the function definition is copied into each translation unit. If we try to apply a fake definition the usual way, we will end up with a _"redefinition of function *x*"_ error.

*AutoFFF* implements a workaround to avoid this redefinition error and allowing to fake the original function. This workaround simply consists of some defines which will re-route any call to the original in-header definition to our faked one. For this to work it is required that the test-header is included (and thereby pre-processed) _before_ any function call to the function under consideration is instructed, i.e. the test-header must be included _before_ the CuT. Any function call that is processed before the workaround is being pre-processed will leave this function call targeted towards the original in-header definition.

In practice the workaround looks like this:

```c
/* api.h */
#ifndef API_HEADER_H_
#define API_HEADER_H_

const char* foo(void)
{
    return "Definitions inside headers are great!";
}

#endif
```

```c
/* api_th.h */
#ifndef TEST_HEADER_H_
#define TEST_HEADER_H_

#include "fff.h"
#include "api.h"

/* Re-route any call to 'foo' to 'foo_fff' (our fake definition). */
#define foo foo_fff
/* By re-routing the '_fake' and '_reset' type and function the workaround becomes invisible in the test-case. */
#define foo_fake Foo_fff_fake
#define foo_reset Foo_fff_reset
/* Create the fake definition using the now re-routed 'foo'-symbol. */
FAKE_VOID_FUNC(foo);

#endif
```

```c
/* cut.c - code-under-test */
#include "api.h"
#include <stdio.h>

const char* bar(void)
{
    const char* str = foo();
    return str;
}
```

```c
/* test.c */
#include "fff.h"
#include "api_th.h" /* fakes + workaround */
#include "cut.c"

setup(void)
{
    RESET_FAKE(foo);
}

TEST_F(foo, ReturnBar_Success)
{
    const char* expected_retval = "Definitions inside headers make faking difficult!";
    foo_fake.return_val = expected_retval

    const char* str = bar();

    ASSERT_STREQ(expected_retval, str);
}
```