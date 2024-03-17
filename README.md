# AutoFFF

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ChiefGokhlayeh/autofff/master.svg)](https://results.pre-commit.ci/latest/github/ChiefGokhlayeh/autofff/master)
[![build](https://github.com/ChiefGokhlayeh/autofff/actions/workflows/build.yml/badge.svg)](https://github.com/ChiefGokhlayeh/autofff/actions/workflows/build.yml)
[![PyPI version](https://badge.fury.io/py/autofff.svg)](https://badge.fury.io/py/autofff)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Auto-generate [FFF](https://github.com/meekrosoft/fff) fake definitions for C API header files.

Incorporate this script into your normal build environment (like _make_) and automatically generate test-headers with faked function definitions ready-to-use with [FFF](https://github.com/meekrosoft/fff)'s own _gtest_ or some other unit-testing-framework.

## The Idea Behind Faking

Especially in the embedded world, compiling your (unit-)tests against the actual target platform isn't feasible, as the architecture you're executing the test on and your target platform you're writing the code for are generally not the same.

This is where faking a specific platform API might help you. Instead of calling the actual target platform API, you link your code-under-test (CuT) against a faked version of said API. Now, whenever your CuT tries to access the platform API,it is instead calling the fake-implementation which you can easily configure in your test-cases' setup phase.

[FFF](https://github.com/meekrosoft/fff) (fake-functions-framework) is a framework designed to easily create faked definitions of your API function-declarations, allowing you to configure return values and inspect call and argument histories that were called during the tests' runtime. Check out their awesome project on [Github](https://github.com/meekrosoft/fff). AutoFFF utilizes the ability to easily create fake definitions provided by FFF, but could also be adapted to other mocking frameworks.

The problem with faking an API in embedded C is usually the infeasibility of using dynamic linking and C's lack of techniques like 'reflection' to manipulate your CuT during runtime. This makes the process of writing fake definitions a tedious, labor intensive and error prone matter.

Introducing [_AutoFFF_](https://github.com/ChiefGokhlayeh/autofff), an attempt at automating the process of writing so called test-headers (headers which include the faked definitions).

### Two Philosophies of Faking

When writing fakes you will notice that there are two approaches of laying out your fake.

1. **Banning** the original API header\
   This strategy _bans_ the original header by defining the API headers include guard, making it impossible to include the original function, variable and type declarations. This gives you ultimate freedom in the test-header, but also means that you will have to manually declare any types, functions and variables the API-user might expect. It also allows you to control the include hierarchy and maybe skip some headers which aren't compatible with your test-runner's architecture. In general this approach usually involves a lot of copy&pasting and is therefore more prone to _"code rot"_. You also need to deep-dive any header you want to fake, understand its structure and inspect all the declarations and defines very closely. Not the optimal strategy if you're looking for an easy-to-maintain way of managing test-headers.
1. **Wrapping** the original API header\
   Conversely to the banning method, the _wrapping_ strategy directly includes the original API header, and thereby imports any type, variable and function declarations. Also the include hierarchy is taken over from the original. The only thing to add into the test-header are the fake definitions. This method evidently grants you less freedom in the test-header, but is usually much shorter and slightly less prone to _"rot"_ over time.

It should become obvious which method is better suited for automation. _AutoFFF_ follows the _wrapping_ approach of writing test-headers, which for most cases should be good enough.

Finally it must be stated, that these two philosophies seldomly mix well!

## Installation

Use `pip` to download and install _AutoFFF_ from the [PyPi](https://pypi.org/project/autofff/) repositories:

```shell
py -3.6 -m pip install autofff
```

Or install from source:

```shell
py -3.6 -m pip install .
```

Note that you'll most likely require the pycparser `fake_libc_include`s header collection for AutoFFF to work. The `pip` package does **not** ship with this external code. You may download the faked libc headers from [`pycparser`s Github](https://github.com/eliben/pycparser), or check out the project as a submodule (when installing from source run `git submodule update --init`).

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

You can also let the makefile do the installation of _AutoFFF_ for you.

```shell
make install_autofff
```

### Running the 'Generate Fakes' Example

```shell
make -f examples/generate-via-makefile/generate_fakes.mk CRAWL_PATHS=examples
```

### As a Python Package

```python
import autofff

import os.path

targetHeader = "examples/simple-headers/driver.h"
outputHeader = "output/driver_th.h"
fakes = './autofff/dependencies/pycparser/utils/fake_libc_include'

scnr = autofff.scanner.GCCScanner(targetHeader, fakes) # Create GCC code scanner
result = scnr.scan() # Scan for function declarations and definitions

gen = autofff.generator.SimpleFakeGenerator(os.path.splitext(os.path.basename(outputHeader))[0], targetHeader) # Create new generator with name output-header and path to target-header

if not os.path.exists(os.path.dirname(outputHeader)):
    dirname = os.path.dirname(outputHeader)
    os.makedirs(dirname)

with open(outputHeader, "w") as fs:
    gen.generate(result, fs) # Generate fff-fakes from scanner-result
```

## How Fakes Are Generated

The format of the generated test-header obviously depends on the specifics of the `FakeGenerator` being used.

1. The `BareFakeGenerator` will only generate the `FAKE_VALUE_`- and `FAKE_VOID_FUNC` macros without any decorations, like include guards or header includes. Use this generator if you want to add your own (shell-based-)processing on top.
2. The `SimpleFakeGenerator` will generate a "minimum viable test header", meaning the result should be compilable without too much effort.

### In-Header Defined Functions

In some API headers functions may be defined within the header. This will cause issues when trying to fake this function, because by including the header the function definition is copied into each translation unit. If we try to apply a fake definition the usual way, we will end up with a _"redefinition of function **x**"_ error.

_AutoFFF_ implements a workaround to avoid this redefinition error and allowing to fake the original function. This workaround simply consists of some defines which will re-route any call to the original in-header definition to our faked one. For this to work it is required that the test-header is included (and thereby pre-processed) _before_ any function call to the function under consideration is instructed, i.e. the test-header must be included _before_ the CuT. Any function call that is processed before the workaround is being pre-processed will leave this function call targeted towards the original in-header definition.

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
FAKE_VALUE_FUNC(const char *, foo);

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

### Working with _obscure_ include policies

Some libraries like FreeRTOS or CMSIS require you to include their API headers in a very specific way. AutoFFF can't guess these policies (yet! ;P) from source-code alone. For cases where the include policy of your vendor lib does not allow each header to be preprocessed individually check out the `-D` (`--define`) and `-i` (`--includefile`) command line options. They may allow you to fix/trick the broken include chain.
As an example, for FreeRTOS' `list.h` run:

```shell
py -3.6 -m autofff
    [...]/include/list.h
    -o [...]
    -i [...]/include/FreeRTOS.h <<< inject FreeRTOS.h before preprocessing list.h
    -F [...]
```
