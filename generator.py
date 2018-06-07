from abc import ABC, abstractmethod
import io
import logging
import os.path
import sys
import re

from overrides import overrides

import pycparser

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
	LOGGER.error("Module is not inteded to run as '__main__'!")
	sys.exit(1)

class FakeGenerator(ABC):
	def __init__(self, fakeName:str):
		self.fakeName = fakeName

	@abstractmethod
	def generate(self, declarations:list, output:io.IOBase):
		pass

class TemplatedFakeGenerator(FakeGenerator):
	pass

class SimpleFakeGenerator(FakeGenerator):
	def __init__(self, fakeName:str, originalHeader:str, generateIncludeGuard:bool=True):
		super().__init__(fakeName)
		self.originalHeader = originalHeader
		self.generateIncludeGuard = generateIncludeGuard

	@overrides
	def generate(self, declarations:list, output:io.IOBase):
		incGuard = os.path.splitext(os.path.basename(self.fakeName.upper()))[0]
		if incGuard[0].isdigit():
			incGuard = '_' + incGuard

		incGuard = f"{re.sub('([^A-Z0-9_]*)', '', incGuard)}_H_"
		LOGGER.info(f"Generated include guard macro: '{incGuard}'.")
		incGuardBeginning = [
			f'#ifndef {incGuard}\n',
			f'#define {incGuard}\n\n',
			f'#include "fff.h"\n',
			f'#include "{os.path.basename(self.originalHeader)}"\n\n'
		]
		incGuardEnd = [
			f"\n#endif /* {incGuard} */\n"
		]
		output.writelines(incGuardBeginning)

		for decl in declarations:
			funcName = decl.name
			returnType = decl.type.type.type.names[0]
			if returnType == 'void':
				fake = f'FAKE_VOID_FUNC({funcName}'
			else:
				fake = f'FAKE_VALUE_FUNC({returnType}, {funcName}'
			params = filter(lambda param: param.type.type.names[0] != 'void', decl.type.args.params)
			for param in params:
				fake += f', {param.type.type.names[0]}'
			fake += ');\n'
			output.write(fake)

		output.writelines(incGuardEnd)