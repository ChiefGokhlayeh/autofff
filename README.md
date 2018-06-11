# AutoFFF
Auto-generate [FFF](https://github.com/meekrosoft/fff) fake definitions for C API header files.

Incorporate the script into your normal build environment (like _make_) and automatically generate test-headers with faked function definitions ready-to-use with [FFF](https://github.com/meekrosoft/fff)'s own _gtest_ or some other unit-testing-framework.

## Usage
### As a Standalone Script
To run the example:
```shell
$ py -3.6 autofff.py 
    ./examples/example.h
    -o ./output/example_th.h
    -i ./examples
    -f ./dependencies/pycparser/utils/fake_libc_include
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