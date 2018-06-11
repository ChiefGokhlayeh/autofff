import logging
import sys

import pycparser

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

def get_type_name(decl:pycparser.c_ast.Decl):
	if isinstance(decl.type, pycparser.c_ast.TypeDecl):
		return decl.type.type.names[0]
	elif isinstance(decl.type, pycparser.c_ast.PtrDecl):
		ptrDecl = decl.type
		depth = 1
		while True:
			if isinstance(ptrDecl.type, pycparser.c_ast.PtrDecl):
				ptrDecl = ptrDecl.type
				depth += 1
			else:
				break
		dummy = ''.join(['*'] * depth)
		return f'{ptrDecl.type.type.names[0]}{dummy}'
	else:
		raise ValueError(f"Unknown type {type(decl)}")