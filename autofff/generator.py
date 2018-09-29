import autofff.utils as utils
import autofff.scanner as scanner

from abc import ABC, abstractmethod
import io
import logging
import os.path
import sys
import re

from overrides import overrides

import pycparser
import pycparser.c_generator
from pycparser.c_ast import *

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
	LOGGER.error("Module is not intended to run as '__main__'!")
	sys.exit(1)

class FakeGenerator(ABC):
	def __init__(self):
		self.cGen = pycparser.c_generator.CGenerator()

	@abstractmethod
	def generate(self, result:scanner.ScannerResult, output:io.IOBase):
		pass

class TemplatedFakeGenerator(FakeGenerator):
	pass

class BareFakeGenerator(FakeGenerator):
	def __init__(self):
		super().__init__()

	def _generateTypeDefForDecl(self, decl:Decl):
		typedefs = ''
		for param in filter(
			lambda p: utils.is_function_pointer_type(p.type),
			decl.type.args.params):
			name = utils.create_typedef_name_for_fnc_ptr(decl, param)

			param.type.type.type.declname = name
			typedef = Typedef(name, param.quals, ['typedef'], param.type)

			param.type = TypeDecl(param.name, param.type.quals, IdentifierType([name]))
			typedefs += f"{self.cGen.visit_Typedef(typedef)};\n"
		return typedefs

	def _generateBypassForFuncDef(self, funcDef:FuncDef):
		funcName = funcDef.decl.name
		bypass = f"#define {funcName} {funcName}_fff\n"
		bypass += f"#define {funcName}_fake {funcName}_fff_fake\n"
		bypass += f"#define {funcName}_reset {funcName}_fff_reset\n"
		return bypass

	def _generateFakeForDecl(self, decl:Decl):
		funcName = decl.name
		returnType = utils.get_type_name(decl.type)
		if any(map(lambda p: isinstance(p, EllipsisParam), decl.type.args.params)):
			vararg = '_VARARG'
		else:
			vararg = ''
		if returnType == 'void':
			fake = f'FAKE_VOID_FUNC{vararg}({funcName}'
		else:
			fake = f'FAKE_VALUE_FUNC{vararg}({returnType}, {funcName}'
		if len(decl.type.args.params) > 1 or (
			not isinstance(decl.type.args.params[0], EllipsisParam) and
				utils.get_type_name(decl.type.args.params[0]) != 'void'):
			for param in decl.type.args.params:
				if isinstance(param, EllipsisParam):
					fake += ', ...'
				else:
					fake += f', {utils.get_type_name(param)}'
		LOGGER.debug(f"Creating fake {fake});...")
		fake += ');\n'
		return fake

	@overrides
	def generate(self, result:scanner.ScannerResult, output:io.IOBase):
		for decl in filter(
				lambda decl: decl.type.args is not None and any(map(
					lambda param: (not isinstance(param, EllipsisParam) and
						utils.is_function_pointer_type(param.type)),
					decl.type.args.params
				)),
				result.declarations):
			output.write(self._generateTypeDefForDecl(decl))
		for defin in filter(
				lambda defin: defin.decl.type.args is not None and any(map(
					lambda param: (not isinstance(param, EllipsisParam) and
						utils.is_function_pointer_type(param.type)),
					defin.decl.type.args.params
				)),
				result.definitions):
			output.write(self._generateTypeDefForDecl(defin.decl))

		for decl in result.declarations:
			output.write(self._generateFakeForDecl(decl))

		for definition in result.definitions:
			output.write(self._generateBypassForFuncDef(definition))
			output.write(self._generateFakeForDecl(definition.decl))

class SimpleFakeGenerator(BareFakeGenerator):
	def __init__(self, fakeName:str, originalHeader:str, includeFiles:list=None, generateIncludeGuard:bool=True):
		super().__init__()
		self.fakeName = fakeName
		self.originalHeader = originalHeader
		self.includeFiles = includeFiles
		self.generateIncludeGuard = generateIncludeGuard

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
			f'#include "fff.h"\n'
		]
		if self.includeFiles is not None:
			incGuardBeginning += [ f'#include "{os.path.basename(f)}"\n' for f in self.includeFiles ]
		incGuardBeginning += f'#include "{os.path.basename(self.originalHeader)}"\n\n'
		incGuardEnd = [
			f"\n#endif /* {incGuard} */\n"
		]
		output.writelines(incGuardBeginning)

		for decl in filter(
				lambda decl: decl.type.args is not None and any(map(
					lambda param: (not isinstance(param, EllipsisParam) and
						utils.is_function_pointer_type(param.type)),
					decl.type.args.params
				)),
				result.declarations):
			output.write(self._generateTypeDefForDecl(decl))
		for defin in filter(
				lambda defin: defin.decl.type.args is not None and any(map(
					lambda param: (not isinstance(param, EllipsisParam) and
						utils.is_function_pointer_type(param.type)),
					defin.decl.type.args.params
				)),
				result.definitions):
			output.write(self._generateTypeDefForDecl(defin.decl))

		output.write("\n")
		for decl in result.declarations:
			output.write(self._generateFakeForDecl(decl))

		output.write("\n")
		for definition in result.definitions:
			output.write(self._generateBypassForFuncDef(definition))
			output.write(self._generateFakeForDecl(definition.decl))

		output.writelines(incGuardEnd)