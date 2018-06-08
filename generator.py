import scanner

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
	def generate(self, result:scanner.ScannerResult, output:io.IOBase):
		pass

class TemplatedFakeGenerator(FakeGenerator):
	pass

class SimpleFakeGenerator(FakeGenerator):
	def __init__(self, fakeName:str, originalHeader:str, generateIncludeGuard:bool=True):
		super().__init__(fakeName)
		self.originalHeader = originalHeader
		self.generateIncludeGuard = generateIncludeGuard

	def _generateBypassForFuncDef(self, funcDef:pycparser.c_ast.FuncDef):
		funcName = funcDef.decl.name
		bypass = f"#define {funcName} {funcName}_fff\n"
		bypass += f"#define {funcName}_fake {funcName}_fff_fake\n"
		bypass += f"#define {funcName}_reset {funcName}_fff_reset\n"
		return bypass

	def _generateFakeForDecl(self, decl:pycparser.c_ast.Decl):
		funcName = decl.name
		returnType = decl.type.type.type.names[0]
		if returnType == 'void':
			fake = f'FAKE_VOID_FUNC({funcName}'
		else:
			fake = f'FAKE_VALUE_FUNC({returnType}, {funcName}'
		params = filter(lambda param: param.type.type.names[0] != 'void', decl.type.args.params)
		for param in params:
			fake += f', {param.type.type.names[0]}'
		LOGGER.debug(f"Creating fake {fake});...")
		fake += ');\n'
		return fake

	@overrides
	def generate(self, result:scanner.ScannerResult, output:io.IOBase):
		incGuard = os.path.splitext(os.path.basename(self.fakeName.upper()))[0]
		if incGuard[0].isdigit():
			incGuard = '_' + incGuard

		incGuard = f"{re.sub('([^A-Z0-9_]*)', '', incGuard)}_H_"
		LOGGER.debug(f"Generated include guard macro: '{incGuard}'.")
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

		for decl in result.declarations:
			output.write(self._generateFakeForDecl(decl))

		output.write("\n")
		for definition in result.definitions:
			output.write(self._generateBypassForFuncDef(definition))
			output.write(self._generateFakeForDecl(definition.decl))

		output.writelines(incGuardEnd)