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

def format_as_includes(includes:list):
	if includes is None:
		return list()
	else:
		return [format_as_include(element) for element in includes]

def format_as_include(include:str):
	return f"-I{include.strip()}"

def format_as_defines(defines:list):
	if defines is None:
		return list()
	else:
		return [format_as_define(element) for element in defines]

def format_as_define(define:str):
	return f"-D{define.strip()}"

class ScannerException(Exception):
	def __init__(self, message:str, details:str):
		self.details = details
		super().__init__(message)

class Scanner(metaclass=ABCMeta):
	@classmethod
	def __init__(self, targetHeader:str, fakes:str, includes:list=None, defines:list=None):
		self.targetHeader = targetHeader
		self.fakes = fakes
		self.includes = includes
		self.includedHeaders = dict()
		self.defines = defines

	@classmethod
	def scan_function_declarations(self):
		includedFunctions = {}
		for includedHeader in self.includedHeaders.values():
			LOGGER.info(f"Looking for included function declarations in {includedHeader}")
			includedFunctions = {**self._mine_function_declarations(includedHeader, includedFunctions), **includedFunctions }
			if len(includedFunctions) > 0:
				LOGGER.info(f"Included function declarations in {os.path.basename(includedHeader)}: {', '.join(includedFunctions)}")
			else:
				LOGGER.info(f"No included function declarations found")
		return self._mine_function_declarations(self.targetHeader, includedFunctions).values()

	@abstractmethod
	def scan_included_headers(self):
		pass

	@classmethod
	def _mine_function_declarations(self, pathToHeader:str, knownFunctions:dict=dict()):
		ast = self._call_parse(pathToHeader)
		foundFunctions = {}

		for elem in ast.ext:
			if isinstance(elem, pycparser.c_ast.Decl) and isinstance(elem.type, pycparser.c_ast.FuncDecl):
				funcName = elem.name
				if funcName not in knownFunctions:
					funcDecl = elem.type
					foundFunctions[elem.name] = elem
					funcType = funcDecl.type.type.names
					LOGGER.debug(f"[{len(foundFunctions)}] Function Delaration: {funcName}")
					LOGGER.debug(f"\tReturn type: {funcType}")
					paramList = funcDecl.args.params
					for param in paramList:
						paramType = param.type.type.names
						paramName = param.type.declname
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
	def scan_included_headers(self):
		with subprocess.Popen(
			[
				GCC_PATH,
				'-M',
				self.targetHeader,
			]
			+ format_as_includes(self.fakes)
			+ format_as_includes(self.includes)
			+ format_as_defines(self.defines), stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
			stdout = proc.stdout.read().decode('UTF-8')
			proc.wait()
			result = proc.poll()
			if result != 0:
				ex = ScannerException(f"Header scan '{' '.join(proc.args)}' returned with exit code {result}.", proc.stderr.read().decode('UTF-8'))
				LOGGER.exception(ex)
				raise ex
		lines = stdout.split(' \\\r\n')
		self.includedHeaders.clear()
		paths = lines[0].split(' ')[2:]
		self.includedHeaders.update(zip([ os.path.basename(x) for x in paths ], paths))
		for line in lines[1:]:
			paths = [ os.path.normcase(os.path.normpath(pathStr)) for pathStr in line.strip().split(' ') ]
			for key, val in zip([ os.path.basename(x) for x in paths ], paths):
				if key not in self.includedHeaders:
					self.includedHeaders[key] = val
		LOGGER.debug(f"Included headers: {self.includedHeaders}")

	@classmethod
	@overrides
	def _call_parse(self, pathToHeader:str):
		cppArgs = ['-E', '-D__attribute__(x)=' ] + format_as_includes(self.fakes) + format_as_includes(self.includes) + format_as_defines(self.defines)

		LOGGER.debug(f"GCC args for parsing: {', '.join(cppArgs)}")
		return parse_file(pathToHeader, use_cpp=True, cpp_path=GCC_PATH, cpp_args=cppArgs)