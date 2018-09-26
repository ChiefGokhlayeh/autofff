import logging
import sys

import pycparser
from pycparser.c_generator import CGenerator
from pycparser.c_ast import *

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
	LOGGER.error("Module is not intended to run as '__main__'!")
	sys.exit(1)

def format_as_includes(includes:list):
	if includes is None:
		return list()
	else:
		return [format_as_include(element) for element in includes]

def format_as_include_files(fileInclude:list):
	if fileInclude is None:
		return list()
	else:
		return [format_as_include_file(element) for element in fileInclude]

def format_as_include(include:str):
	return f"-I{include.strip()}"

def format_as_include_file(fileInclude:str):
	return f"-include{fileInclude.strip()}"

def format_as_defines(defines:list):
	if defines is None:
		return list()
	else:
		return [format_as_define(element) for element in defines]

def format_as_define(define:str):
	return f"-D{define.strip()}"

def _get_type_name_struct(struct:Struct):
	return CGenerator().visit_Struct(struct).replace('\n', '')

def _get_type_name_union(union:Union):
	return CGenerator().visit_Union(union).replace('\n', '')

def _get_type_name_enum(enum:Enum):
	return CGenerator().visit_Enum(enum)

def _get_type_name_identifiertype(identifiertype:IdentifierType):
	return CGenerator().visit_IdentifierType(identifiertype)

def _get_type_name_typedecl(typedecl:TypeDecl, omitConst:bool=False):
	quals = list(filter(lambda q: not omitConst or q != 'const', typedecl.quals))
	if len(quals) > 0:
		quals = ' '.join(quals) + ' '
	else:
		quals = ''
	if isinstance(typedecl.type, IdentifierType):
		names = _get_type_name_identifiertype(typedecl.type)
	elif isinstance(typedecl.type, Struct):
		names = _get_type_name_struct(typedecl.type)
	elif isinstance(typedecl.type, Union):
		names = _get_type_name_union(typedecl.type)
	elif isinstance(typedecl.type, Enum):
		names = _get_type_name_enum(typedecl.type)
	else:
		raise ValueError(f"Unknown type {type(typedecl.type)}")
	return f'{quals}{names}'

def _get_type_name_ptrdecl(ptrdecl:PtrDecl, omitConst:bool=False):
	if is_function_pointer_type(ptrdecl):
		if ptrdecl.type.args is not None:
			params = ', '.join(
				[ get_type_name(param, omitConst=False) for param in ptrdecl.type.args.params ])
		else:
			params = ''
		return f'{_get_type_name_funcdecl(ptrdecl.type)} (*)({params})'
	else:
		if len(ptrdecl.quals) > 0 and not omitConst:
			quals = ' ' + ' '.join(ptrdecl.quals)
		else:
			quals = ''
		if isinstance(ptrdecl.type, PtrDecl):
			name = _get_type_name_ptrdecl(ptrdecl.type)
		elif isinstance(ptrdecl.type, TypeDecl):
			name = _get_type_name_typedecl(ptrdecl.type)
		else:
			raise ValueError(f"Unknown type {type(ptrdecl.type)}")
		return f'{name}*{quals}'

def _get_type_name_funcdecl(funcDecl:FuncDecl):
	if isinstance(funcDecl.type, PtrDecl):
		return _get_type_name_ptrdecl(funcDecl.type)
	elif isinstance(funcDecl.type, TypeDecl):
		return _get_type_name_typedecl(funcDecl.type, omitConst=True)
	else:
		raise ValueError(f"Unknown type {type(funcDecl.type)}")

def _get_type_name_arraydecl(arraydecl:ArrayDecl):
	if isinstance(arraydecl.type, PtrDecl):
		name = _get_type_name_ptrdecl(arraydecl.type)
	elif isinstance(arraydecl.type, TypeDecl):
		name = _get_type_name_typedecl(arraydecl.type)
	else:
		raise ValueError(f"Unknown type {type(arraydecl.type)}")
	return f'{name}*'

def get_type_name(decl:Decl, omitConst:bool=True):
	if isinstance(decl.type, TypeDecl):
		return _get_type_name_typedecl(decl.type, omitConst=omitConst)
	elif isinstance(decl.type, PtrDecl):
		return _get_type_name_ptrdecl(decl.type, omitConst=omitConst)
	elif isinstance(decl.type, FuncDecl):
		return _get_type_name_funcdecl(decl.type)
	elif isinstance(decl.type, ArrayDecl):
		return _get_type_name_arraydecl(decl.type)
	else:
		raise ValueError(f"Unknown type {type(decl.type)}")

def is_function_pointer_type(ptrdecl:PtrDecl):
	return isinstance(ptrdecl.type, FuncDecl)

def create_typedef_name_for_fnc_ptr(decl:Decl, param:Decl):
	index = decl.type.args.params.index(param)
	return f"fff_{decl.name}_param{index}"