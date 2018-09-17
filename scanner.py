import utils

from abc import ABCMeta, abstractmethod
import logging
import os.path
import re
import subprocess
import sys
import tempfile

from overrides import overrides

import pycparser

GCC_PATH = 'gcc'
GCC_SPECIFIC_MACROS = [
	r'-D__attribute__(x)=',
	r'-D__asm__(x)=',
	r'-D__const=',
	r'-D__const__=',
	r'-D__restrict=',
	r'-D__restrict__=',
	r'-D__extension__=',
	r'-D__inline__=',
]
GCC_SPECIFIC_IGNORE_PATTERN = r"([\s\n]*(__asm|asm)[\s\n]*(volatile|[\s\n]*)(goto|[\s\n]*)(.|\n|;)*?;)"
LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
	LOGGER.error("Module is not intended to run as '__main__'!")
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
	def __init__(self, targetHeader:str, fakes:str, includes:list=None, includeFiles:list=None, defines:list=None, ignorePattern:str=None):
		self.targetHeader = targetHeader
		self.fakes = fakes
		self.includes = includes
		self.includeFiles = includeFiles
		self.defines = defines
		if isinstance(ignorePattern, str):
			self.ignorePattern = re.compile(ignorePattern)
		else:
			self.ignorePattern = ignorePattern

	def scan(self):
		includedHeaders = self._scan_included_headers()
		incFuncDecl = {}
		incFuncDef = {}
		for includedHeader in includedHeaders.values():
			LOGGER.info(f"Looking for included function declarations in {includedHeader.path}...")
			otherHeaders = filter(lambda i: i.path != includedHeader.path, includedHeaders.values())
			ast = self._call_parse(includedHeader.path, [ x.path for x in sorted(otherHeaders, key=lambda entry: entry.ordinal) ])
			incFuncDecl = {**self._mine_function_declarations(ast, incFuncDecl), **incFuncDecl }
			if len(incFuncDecl) > 0:
				LOGGER.info(f"Found '{len(incFuncDecl)}' included function declarations in {os.path.basename(includedHeader.path)}: {', '.join(incFuncDecl)}.")
			else:
				LOGGER.info(f"No included function declarations found.")
			incFuncDef = {**self._mine_function_definitions(ast, incFuncDef), **incFuncDef }
			if len(incFuncDef) > 0:
				LOGGER.info(f"Found '{len(incFuncDef)}' included function definitions in {os.path.basename(includedHeader.path)}: {', '.join(incFuncDef)}.")
			else:
				LOGGER.info(f"No included function definitions found.")

		ast = self._call_parse(self.targetHeader)
		return ScannerResult(tuple(self._mine_function_declarations(ast, incFuncDecl).values()), tuple(self._mine_function_definitions(ast, incFuncDef).values()))

	@abstractmethod
	def _scan_included_headers(self):
		pass

	def _mine_function_declarations(self, ast:pycparser.c_ast.FileAST, knownFunctions:dict=dict()):
		foundFunctions = {}

		for elem in ast.ext:
			if isinstance(elem, pycparser.c_ast.Decl) and isinstance(elem.type, pycparser.c_ast.FuncDecl):
				funcName = elem.name
				if funcName not in knownFunctions:
					funcDecl = elem.type
					foundFunctions[funcName] = elem
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

	def _mine_function_definitions(self, ast:pycparser.c_ast.FileAST, knownFunctions:dict=dict()):
		foundFunctions = {}

		for elem in ast.ext:
			if isinstance(elem, pycparser.c_ast.FuncDef):
				decl = elem.decl
				funcName = decl.name
				if funcName not in knownFunctions:
					funcDecl = decl.type
					foundFunctions[funcName] = elem
					LOGGER.debug(f"[{len(foundFunctions)}] Function Definition: {funcName}")
					LOGGER.debug(f"\tReturn type: {utils.get_type_name(decl)}")
					paramList = funcDecl.args.params
					for param in paramList:
						paramName = param.name
						paramType = utils.get_type_name(param)
						LOGGER.debug(f"\tParameter: {paramName} of Type: {paramType}")
		return foundFunctions

	@abstractmethod
	def _call_parse(self, pathToHeader:str, includeFiles:list=None):
		pass

class GCCScanner(Scanner):
	def __init__(self, targetHeader:str, fakes:str, includes:list=None, includeFiles:list=None, defines:list=None):
		super().__init__(targetHeader, fakes, includes, includeFiles, defines, GCC_SPECIFIC_IGNORE_PATTERN)

	@overrides
	def _scan_included_headers(self):
		with subprocess.Popen(([
				GCC_PATH,
				'-M',
				self.targetHeader,
			]
			+ GCC_SPECIFIC_MACROS
			+ utils.format_as_includes(self.fakes)
			+ utils.format_as_includes(self.includes)
			+ utils.format_as_include_files(self.includeFiles)
			+ utils.format_as_defines(self.defines)),
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE) as proc:
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
		paths = list(filter(lambda path: path != '\\\n', lines[0].split(' ')[2:]))
		includedHeaders.update(zip([ os.path.basename(x) for x in paths ], [ OrderedIncludeHeader(path, i) for i, path in enumerate(paths) ]))
		for line in lines[1:]:
			paths = [ os.path.normcase(os.path.normpath(pathStr)) for pathStr in
				filter(
					lambda p: os.path.normpath(p.strip()) != os.path.normpath(self.targetHeader.strip()),
					line.strip().split(' ')) ]
			for key, val in zip([ os.path.basename(x) for x in paths ], paths):
				if key not in includedHeaders:
					includedHeaders[key] = val
		LOGGER.debug(f"Included headers: {includedHeaders}")
		return includedHeaders

	@overrides
	def _call_parse(self, pathToHeader:str, includeFiles:list=None):
		cppArgs = (['-E'] + GCC_SPECIFIC_MACROS +
			utils.format_as_includes(self.fakes) +
			utils.format_as_includes(self.includes) +
			utils.format_as_include_files(self.includeFiles) +
			utils.format_as_include_files(includeFiles) +
			utils.format_as_defines(self.defines))

		LOGGER.debug(f"GCC args for parsing: {', '.join(cppArgs)}")
		return self._parse_file(pathToHeader, use_cpp=True, cpp_path=GCC_PATH, cpp_args=cppArgs)

	def _preprocess_file(self, filename:str, cpp_path:str='cpp', cpp_args:str=''):
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

	def _parse_file(self, filename:str, use_cpp:bool=False, cpp_path:str='cpp', cpp_args:str='', parser:pycparser.CParser=None):
		if use_cpp:
			text = self._preprocess_file(filename, cpp_path, cpp_args)
		else:
			with open(filename, 'rU') as f:
				text = f.read()

		if parser is None:
			parser = pycparser.CParser()
		return parser.parse(text, filename)

class OrderedIncludeHeader(object):
	def __init__(self, path:str, ordinal:int):
		self.path = path
		self.ordinal = ordinal

	def __str__(self):
		return f"[{self.ordinal}] {self.path}"

	def __repr__(self):
		return self.__str__()