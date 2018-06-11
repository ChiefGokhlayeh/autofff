import utils

from abc import ABCMeta, abstractmethod
import logging
import os.path
import subprocess
import sys

from overrides import overrides

import pycparser
from pycparser import parse_file

GCC_PATH = 'gcc'
LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
	LOGGER.error("Module is not inteded to run as '__main__'!")
	sys.exit(1)

class ScannerException(Exception):
	def __init__(self, message:str, details:str):
		self.details = details
		super().__init__(message)

class ScannerResult():
	def __init__(self, declarations:tuple, definitions:tuple):
		self.declarations = declarations
		self.definitions = definitions

class Scanner(metaclass=ABCMeta):
	@classmethod
	def __init__(self, targetHeader:str, fakes:str, includes:list=None, defines:list=None):
		self.targetHeader = targetHeader
		self.fakes = fakes
		self.includes = includes
		self.defines = defines

	@classmethod
	def scan(self):
		includedHeaders = self._scan_included_headers()
		incFuncDecl = {}
		incFuncDef = {}
		for includedHeader in includedHeaders.values():
			LOGGER.info(f"Looking for included function declarations in {includedHeader}...")
			ast = self._call_parse(includedHeader)
			incFuncDecl = {**self._mine_function_declarations(ast, incFuncDecl), **incFuncDecl }
			if len(incFuncDecl) > 0:
				LOGGER.info(f"Found '{len(incFuncDecl)}' included function declarations in {os.path.basename(includedHeader)}: {', '.join(incFuncDecl)}.")
			else:
				LOGGER.info(f"No included function declarations found.")
			incFuncDef = {**self._mine_function_definitions(ast, incFuncDef), **incFuncDef }
			if len(incFuncDef) > 0:
				LOGGER.info(f"Found '{len(incFuncDef)}' included function definitions in {os.path.basename(includedHeader)}: {', '.join(incFuncDef)}.")
			else:
				LOGGER.info(f"No included function definitions found.")

		ast = self._call_parse(self.targetHeader)
		return ScannerResult(tuple(self._mine_function_declarations(ast, incFuncDecl).values()), tuple(self._mine_function_definitions(ast, incFuncDef).values()))

	@abstractmethod
	def _scan_included_headers(self):
		pass

	@classmethod
	def _mine_function_declarations(self, ast:pycparser.c_ast.FileAST, knownFunctions:dict=dict()):
		foundFunctions = {}

		for elem in ast.ext:
			if isinstance(elem, pycparser.c_ast.Decl) and isinstance(elem.type, pycparser.c_ast.FuncDecl):
				funcName = elem.name
				if funcName not in knownFunctions:
					funcDecl = elem.type
					foundFunctions[funcName] = elem
					LOGGER.debug(f"[{len(foundFunctions)}] Function Delaration: {funcName}")
					LOGGER.debug(f"\tReturn type: {utils.get_type_name(funcDecl)}")
					paramList = funcDecl.args.params
					for param in paramList:
						paramName = param.name
						paramType = utils.get_type_name(param)
						LOGGER.debug(f"\tParameter: {paramName} of Type: {paramType}")
		return foundFunctions

	@classmethod
	def _mine_function_definitions(self, ast:pycparser.c_ast.FileAST, knownFunctions:dict=dict()):
		foundFunctions = {}

		for elem in ast.ext:
			if isinstance(elem, pycparser.c_ast.FuncDef):
				funcName = elem.decl.name
				if funcName not in knownFunctions:
					funcDecl = elem.decl.type
					foundFunctions[funcName] = elem
					LOGGER.debug(f"[{len(foundFunctions)}] Function Definition: {funcName}")
					LOGGER.debug(f"\tReturn type: {utils.get_type_name(funcDecl)}")
					paramList = funcDecl.args.params
					for param in paramList:
						paramName = param.name
						paramType = utils.get_type_name(param)
						LOGGER.debug(f"\tParameter: {paramName} of Type: {paramType}")
		return foundFunctions

	@abstractmethod
	def _call_parse(self, pathToHeader:str):
		pass

class GCCScanner(Scanner):
	@classmethod
	def __init__(self, targetHeader:str, fakes:str, includes:list=None, defines:list=None):
		super().__init__(targetHeader, fakes, includes, defines)

	@classmethod
	@overrides
	def _scan_included_headers(self):
		with subprocess.Popen(
			[
				GCC_PATH,
				'-M',
				self.targetHeader,
			]
			+ utils.format_as_includes(self.fakes)
			+ utils.format_as_includes(self.includes)
			+ utils.format_as_defines(self.defines), stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
			stdout = proc.stdout.read().decode('UTF-8')
			proc.wait()
			result = proc.poll()
			if result != 0:
				ex = ScannerException(f"Header scan '{' '.join(proc.args)}' returned with exit code {result}.", proc.stderr.read().decode('UTF-8'))
				LOGGER.error(f"Scan error: {ex.details}")
				LOGGER.exception(ex)
				raise ex
		lines = stdout.split(' \\\r\n')
		includedHeaders = {}
		paths = lines[0].split(' ')[2:]
		includedHeaders.update(zip([ os.path.basename(x) for x in paths ], paths))
		for line in lines[1:]:
			paths = [ os.path.normcase(os.path.normpath(pathStr)) for pathStr in line.strip().split(' ') ]
			for key, val in zip([ os.path.basename(x) for x in paths ], paths):
				if key not in includedHeaders:
					includedHeaders[key] = val
		LOGGER.debug(f"Included headers: {includedHeaders}")
		return includedHeaders

	@classmethod
	@overrides
	def _call_parse(self, pathToHeader:str):
		cppArgs = (['-E', '-D__attribute__(x)=' ] +
			utils.format_as_includes(self.fakes) +
			utils.format_as_includes(self.includes) +
			utils.format_as_defines(self.defines))

		LOGGER.debug(f"GCC args for parsing: {', '.join(cppArgs)}")
		return parse_file(pathToHeader, use_cpp=True, cpp_path=GCC_PATH, cpp_args=cppArgs)