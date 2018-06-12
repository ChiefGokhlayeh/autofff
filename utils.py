import logging
import sys

import pycparser

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
	LOGGER.error("Module is not intended to run as '__main__'!")
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
		if len(decl.type.quals) > 0:
			quals = ' '.join(decl.type.quals) + ' '
		else:
			quals = ''
		return f'{quals}{decl.type.type.names[0]}'
	elif isinstance(decl.type, pycparser.c_ast.PtrDecl):
		if len(decl.type.quals) > 0:
			quals = ' ' + ' '.join(decl.type.quals)
		else:
			quals = ''
		return f'{get_type_name(decl.type)}*{quals}'


		#ptrDeclStack = [ decl.type ]
		#while True:
		#	if isinstance(ptrDeclStack[-1].type, pycparser.c_ast.PtrDecl):
		#		ptrDeclStack.append(ptrDeclStack[-1].type)
		#	else:
		#		break
		#dummy = ''.join(['*'] * len(ptrDeclStack))
		#return f'{get_type_name(ptrDeclStack[-1])}{dummy}'
	elif isinstance(decl.type, pycparser.c_ast.FuncDecl):
		return get_type_name(decl.type)
	else:
		raise ValueError(f"Unknown type {type(decl.type)}")