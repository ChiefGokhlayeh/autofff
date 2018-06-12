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

def get_type_name(decl:pycparser.c_ast.Decl, prefix='', postfix=''):
	if isinstance(decl.type, pycparser.c_ast.TypeDecl):
		if len(decl.type.quals) > 0:
			quals = ' '.join(decl.type.quals) + ' '
		else:
			quals = ''
		names = ' '.join(decl.type.type.names)
		return f'{quals}{prefix}{names}{postfix}'
	elif isinstance(decl.type, pycparser.c_ast.PtrDecl):
		if is_function_pointer_type(decl):
			if decl.type.type.args is not None:
				params = ', '.join([ get_type_name(param) for param in decl.type.type.args.params ])
			else:
				params = ''
			return f'{get_type_name(decl.type)} (*{prefix}{decl.name}{postfix})({params})'
		else:
			if len(decl.type.quals) > 0:
				quals = ' ' + ' '.join(decl.type.quals)
			else:
				quals = ''
			return f'{prefix}{get_type_name(decl.type)}{postfix}*{quals}'
	elif isinstance(decl.type, pycparser.c_ast.FuncDecl):
		return get_type_name(decl.type)
	else:
		raise ValueError(f"Unknown type {type(decl.type)}")

def is_function_pointer_type(decl:pycparser.c_ast.Decl):
	return isinstance(decl.type.type, pycparser.c_ast.FuncDecl)

def create_typedef_name_for_fnc_ptr(decl:pycparser.c_ast.Decl, param:pycparser.c_ast.Decl):
	index = decl.type.args.params.index(param)
	return f"fff_{decl.name}_param{index}"