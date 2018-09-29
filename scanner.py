import utils

from abc import ABCMeta, abstractmethod
import logging
import os.path
import subprocess
import sys
import re

from overrides import overrides

import pycparser
from pycparser import parse_file

GCC_PATH = 'gcc'
GCC_SPECIFIC_MACROS = [
	r'-D__attribute__(x)=',
	r'-D__asm__(x)=',
	r'-D__const=',
	r'-D__const__=',
	r'-D__restrict=',
	r'-D__restrict__=',
	r'-D__extension__=',
	r'-D__inline=',
	r'-D__forcedinline=',
	r'-D__inline__=',
]
GCC_SPECIFIC_IGNORE_PATTERN = r"([\s\n]*(__asm|asm)[\s\n]*(volatile|[\s\n]*)(goto|[\s\n]*)(.|\n|;)*?;)"
ERROR_CONTEXT_PREV_LINE_COUNT = 5
ERROR_CONTEXT_POST_LINE_COUNT = 5
LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
	LOGGER.error("Module is not intended to run as '__main__'!")
	sys.exit(1)

class ScannerException(Exception):
	def __init__(self, message:str, details:str)->None:
		self.details = details
		super().__init__(message)

class ScannerResult():
	def __init__(self, declarations:tuple, definitions:tuple)->None:
		self.declarations = declarations
		self.definitions = definitions

class Scanner(metaclass=ABCMeta):
	def __init__(self, targetHeader:str, fakes:str, includes:list=None, includeFiles:list=None, defines:list=None, ignorePattern:str=None)->None:
		self.targetHeader = targetHeader
		self.fakes = fakes
		self.includes = includes
		self.includeFiles = includeFiles
		self.defines = defines
		if isinstance(ignorePattern, str):
			self.ignorePattern = re.compile(ignorePattern)
		else:
			self.ignorePattern = ignorePattern

	def scan(self)->ScannerResult:
		ast = self._call_parse(self.targetHeader)
		return ScannerResult(tuple(self._mine_function_declarations(ast)), tuple(self._mine_function_definitions(ast)))

	def _mine_function_declarations(self, ast:pycparser.c_ast.FileAST)->list:
		foundFunctions = []

		for elem in ast.ext:
			if isinstance(elem, pycparser.c_ast.Decl) and isinstance(elem.type, pycparser.c_ast.FuncDecl):
				funcName = elem.name
				header = elem.coord.file
				if os.path.normpath(header) == os.path.normpath(self.targetHeader):
					funcDecl = elem.type
					foundFunctions.append(elem)
					LOGGER.debug(f"[{len(foundFunctions)}] Function Declaration: {funcName}")
					LOGGER.debug(f"\tReturn type: {utils.get_type_name(elem)}")
					paramList = funcDecl.args.params
					for param in paramList:
						if isinstance(param, pycparser.c_ast.EllipsisParam):
							paramName = '...'
						else:
							paramName = param.name
							paramType = utils.get_type_name(param)
						LOGGER.debug(f"\tParameter: {paramName} of Type: {paramType}")
		return foundFunctions

	def _mine_function_definitions(self, ast:pycparser.c_ast.FileAST)->list:
		foundFunctions = []

		for elem in ast.ext:
			if isinstance(elem, pycparser.c_ast.FuncDef):
				decl = elem.decl
				funcName = decl.name
				header = decl.coord.file
				if os.path.normpath(header) == os.path.normpath(self.targetHeader):
					funcDecl = decl.type
					foundFunctions.append(elem)
					LOGGER.debug(f"[{len(foundFunctions)}] Function Definition: {funcName}")
					LOGGER.debug(f"\tReturn type: {utils.get_type_name(decl)}")
					paramList = funcDecl.args.params
					for param in paramList:
						paramName = param.name
						paramType = utils.get_type_name(param)
						LOGGER.debug(f"\tParameter: {paramName} of Type: {paramType}")
		return foundFunctions

	@abstractmethod
	def _call_parse(self, pathToHeader:str)->pycparser.c_ast.FileAST:
		pass

class GCCScanner(Scanner):
	def __init__(self, targetHeader:str, fakes:str, includes:list=None, includeFiles:list=None, defines:list=None)->None:
		super().__init__(targetHeader, fakes, includes, includeFiles, defines, GCC_SPECIFIC_IGNORE_PATTERN)

	@overrides
	def _call_parse(self, pathToHeader:str)->pycparser.c_ast.FileAST:
		cppArgs = (['-E'] + GCC_SPECIFIC_MACROS +
			utils.format_as_includes(self.fakes) +
			utils.format_as_includes(self.includes) +
			utils.format_as_include_files(self.includeFiles) +
			utils.format_as_defines(self.defines))

		LOGGER.debug(f"GCC args for parsing: {', '.join(cppArgs)}")
		return self._parse_file(pathToHeader, use_cpp=True, cpp_path=GCC_PATH, cpp_args=cppArgs)

	def _preprocess_file(self, filename:str, cpp_path:str='cpp', cpp_args:str='')->str:
		path_list = [cpp_path]
		if isinstance(cpp_args, list):
			path_list += cpp_args
		elif cpp_args != '':
			path_list += [cpp_args]
		path_list += [filename]

		try:
			# Note the use of universal_newlines to treat all newlines
			# as \n for Python's purpose
			#
			pipe = subprocess.Popen(path_list,
							stdout=subprocess.PIPE,
							universal_newlines=True)
			text = pipe.communicate()[0]
		except OSError as e:
			raise RuntimeError("Unable to invoke 'cpp'.  " +
				'Make sure its path was passed correctly\n' +
				('Original error: %s' % e))

		filteredText = self.ignorePattern.sub('', text)

		return filteredText

	def _parse_file(self, filename:str, use_cpp:bool=False, cpp_path:str='cpp', cpp_args:str='', parser:pycparser.CParser=None)->pycparser.c_ast.FileAST:
		if use_cpp:
			text = self._preprocess_file(filename, cpp_path, cpp_args)
		else:
			with open(filename, 'rU') as f:
				text = f.read()

		if parser is None:
			parser = pycparser.CParser()
		try:
			return parser.parse(text, filename)
		except pycparser.c_parser.ParseError as error:
			if isinstance(error, pycparser.c_parser.ParseError):
				context = self._parse_error_context(text, error)
			else:
				context = ""
			LOGGER.error(f"Parsing of {filename} failed. Details:\t{str(error)}\n{context}")
			raise error

	def _parse_error_context(self, text:str, error:pycparser.c_parser.ParseError)->str:
		match = re.match(r"\s*(.*?)\s*:\s*([0-9]*?)\s*:\s*([0-9]*?)\s*:\s*(.*)", str(error))
		filename = match.group(1)
		row = int(match.group(2)) - 1
		column = int(match.group(3)) - 1

		context = f">Caused in file: {filename}\n"
		prevRowStart = max(row - ERROR_CONTEXT_PREV_LINE_COUNT, 0)
		postRowStart = row + ERROR_CONTEXT_POST_LINE_COUNT
		with open(filename) as fp:
			for i, line in enumerate(fp):
				if i == row:
					context += f">{line[:-1]}\n"
					context += f"{'-' * (column + 1)}^{'-' * (len(line) - column - 2)}\n"
				elif i >= prevRowStart and i <= postRowStart:
					context += f"{line[:-1]}\n"
		return context