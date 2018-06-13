# AutoFFF
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

## Usage
### As a Standalone Script
To run the example:
```shell
$ py -3.6 autofff.py
    ./examples/driver.h
    -O ./output/driver_th.h
    -I ./examples
    -F ./dependencies/pycparser/utils/fake_libc_include
```
### Running the Make Example
```shell
$ make -f examples/generate_fakes.mk CRAWL_PATHS=examples
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