from pycparser.c_ast import (
    Decl,
    EllipsisParam,
    FuncDef,
    IdentifierType,
    TypeDecl,
    Typedef,
)
import autofff.utils as utils
import autofff.scanner as scanner
import autofff.config as c
from autofff.config import CONFIG

from abc import ABC, abstractmethod
import io
import logging
import os.path
import sys
import re

from overrides import overrides

import pycparser
import pycparser.c_generator

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    LOGGER.error("Module is not intended to run as '__main__'!")
    sys.exit(1)


class FakeGenerator(ABC):
    def __init__(self) -> None:
        self.cGen = pycparser.c_generator.CGenerator()

    @abstractmethod
    def generate(self, result: scanner.ScannerResult, output: io.IOBase) -> None:
        pass


class TemplatedFakeGenerator(FakeGenerator):
    pass


class BareFakeGenerator(FakeGenerator):
    def __init__(self) -> None:
        super().__init__()

    def _generateTypeDefForDecl(self, decl: Decl) -> str:
        typedefs = ""
        for param in filter(
            lambda p: utils.is_function_pointer_type(p.type), decl.type.args.params
        ):
            name = utils.create_typedef_name_for_fnc_ptr(decl, param)

            type = param.type.type.type
            while not hasattr(type, "declname"):
                type = type.type
            type.declname = name
            typedef = Typedef(name, param.quals, ["typedef"], param.type)

            param.type = TypeDecl(
                param.name, param.type.quals, None, IdentifierType([name])
            )
            typedefs += f"{self.cGen.visit_Typedef(typedef)};\n"
        return typedefs

    def _generateBypassForFuncDef(self, funcDef: FuncDef) -> str:
        funcName = funcDef.decl.name
        bypass = f"#define {funcName} {funcName}_fff\n"
        bypass += f"#define {funcName}_fake {funcName}_fff_fake\n"
        bypass += f"#define {funcName}_reset {funcName}_fff_reset\n"
        return bypass

    def _generateFakeForDecl(self, decl: Decl) -> str:
        funcName = decl.name
        returnType = utils.get_type_name(decl.type)
        if decl.type.args is not None and any(
            map(lambda p: isinstance(p, EllipsisParam), decl.type.args.params)
        ):
            vararg = "_VARARG"
        else:
            vararg = ""
        if returnType == "void":
            fake = f"FAKE_VOID_FUNC{vararg}({funcName}"
        else:
            fake = f"FAKE_VALUE_FUNC{vararg}({returnType}, {funcName}"
        if decl.type.args is None:
            pass
        elif len(decl.type.args.params) > 1 or (
            not isinstance(decl.type.args.params[0], EllipsisParam)
            and utils.get_type_name(decl.type.args.params[0]) != "void"
        ):
            for param in decl.type.args.params:
                if isinstance(param, EllipsisParam):
                    fake += ", ..."
                else:
                    fake += f", {utils.get_type_name(param)}"
        LOGGER.debug(f"Creating fake {fake});...")
        fake += ");\n"
        return fake

    @overrides
    def generate(self, result: scanner.ScannerResult, output: io.IOBase) -> None:
        for decl in filter(
            lambda decl: decl.type.args is not None
            and any(
                map(
                    lambda param: (
                        not isinstance(param, EllipsisParam)
                        and utils.is_function_pointer_type(param.type)
                    ),
                    decl.type.args.params,
                )
            ),
            result.declarations,
        ):
            output.write(self._generateTypeDefForDecl(decl))
        for defin in filter(
            lambda defin: defin.decl.type.args is not None
            and any(
                map(
                    lambda param: (
                        not isinstance(param, EllipsisParam)
                        and utils.is_function_pointer_type(param.type)
                    ),
                    defin.decl.type.args.params,
                )
            ),
            result.definitions,
        ):
            output.write(self._generateTypeDefForDecl(defin.decl))

        for decl in result.declarations:
            output.write(self._generateFakeForDecl(decl))

        for definition in result.definitions:
            output.write(self._generateBypassForFuncDef(definition))
            output.write(self._generateFakeForDecl(definition.decl))


class SimpleFakeGenerator(BareFakeGenerator):
    def __init__(
        self,
        fakeName: str,
        originalHeader: str,
        includeFiles: list = None,
        generateIncludeGuard: bool = None,
    ) -> None:
        super().__init__()
        self.fakeName = fakeName
        self.originalHeader = originalHeader
        self.includeFiles = includeFiles
        if generateIncludeGuard is None:
            self.generateIncludeGuard = CONFIG[c.AUTOFFF_SECTION][
                c.SIMPLE_GENERATOR_SECTION
            ][c.SIMPLE_GENERATOR_GENERATE_INCLUDE_GUARD]
        else:
            self.generateIncludeGuard = generateIncludeGuard

    @overrides
    def generate(self, result: scanner.ScannerResult, output: io.IOBase) -> None:
        if self.generateIncludeGuard:
            incGuard = os.path.splitext(os.path.basename(self.fakeName.upper()))[0]
            if incGuard[0].isdigit():
                incGuard = "_" + incGuard

            fffHeader = os.path.expandvars(
                CONFIG[c.AUTOFFF_SECTION][c.SIMPLE_GENERATOR_SECTION][
                    c.SIMPLE_GENERATOR_FFF_PATH
                ]
            )
            incGuard = f"{re.sub('([^A-Z0-9_]*)', '', incGuard)}_H_"
            LOGGER.debug(f"Generated include guard macro: '{incGuard}'.")
            incGuardBeginning = [
                f"#ifndef {incGuard}\n",
                f"#define {incGuard}\n\n",
                f'#include "{fffHeader}"\n',
            ]
            if self.includeFiles is not None:
                incGuardBeginning += [
                    f'#include "{os.path.basename(f)}"\n' for f in self.includeFiles
                ]
            incGuardBeginning += (
                f'#include "{os.path.basename(self.originalHeader)}"\n\n'
            )
            incGuardBeginning += '#ifdef __cplusplus\nextern "C" { \n #endif\n'
            incGuardEnd = [
                "#ifdef __cplusplus\n}\n#endif\n",
                f"\n#endif /* {incGuard} */\n",
            ]
            output.writelines(incGuardBeginning)

        for decl in filter(
            lambda decl: decl.type.args is not None
            and any(
                map(
                    lambda param: (
                        not isinstance(param, EllipsisParam)
                        and utils.is_function_pointer_type(param.type)
                    ),
                    decl.type.args.params,
                )
            ),
            result.declarations,
        ):
            output.write(self._generateTypeDefForDecl(decl))
        for defin in filter(
            lambda defin: defin.decl.type.args is not None
            and any(
                map(
                    lambda param: (
                        not isinstance(param, EllipsisParam)
                        and utils.is_function_pointer_type(param.type)
                    ),
                    defin.decl.type.args.params,
                )
            ),
            result.definitions,
        ):
            output.write(self._generateTypeDefForDecl(defin.decl))

        output.write("\n")
        for decl in result.declarations:
            output.write(self._generateFakeForDecl(decl))

        output.write("\n")
        for definition in result.definitions:
            output.write(self._generateBypassForFuncDef(definition))
            output.write(self._generateFakeForDecl(definition.decl))

        if self.generateIncludeGuard:
            output.writelines(incGuardEnd)
