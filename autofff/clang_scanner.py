import autofff.config as c
from autofff.config import CONFIG

import logging
import sys
import os.path

LOGGER = logging.getLogger(__name__)

try:
    import clang.cindex as cidx
except ModuleNotFoundError:
    path = os.path.dirname(sys.modules[__name__].__file__)
    path = os.path.abspath(os.path.join(
        path, '../dependencies/llvm-project/clang/bindings/python'))
    sys.path.insert(0, path)
    import clang.cindex as cidx
    LOGGER.debug(f"Using clang python bindings from {path}")

if __name__ == "__main__":
    LOGGER.error("Module is not intended to run as '__main__'!")
    sys.exit(1)


class ClangScanner():
    def __init__(self, inputFile: str, includes: list = None, includeFiles: list = None, defines: list = None, **kwargs):
        if kwargs:
            self._index = cidx.Index.create(kwargs)
        else:
            self._index = cidx.Index.create()
        self._inputFile = inputFile
        self._includes = includes
        self._includeFiles = includeFiles
        self._defines = defines

    @property
    def index(self) -> cidx.Index:
        return self._index

    @property
    def inputFile(self) -> str:
        return self._inputFile

    @property
    def includes(self) -> list:
        return self._includes

    @property
    def includeFiles(self) -> list:
        return self._includeFiles

    @property
    def defines(self) -> list:
        return self._defines

    def scan(self) -> None:
        args = []
        if self.includes:
            args += [f'--include-directory="{incl}"' for incl in self.includes]
        if self.includeFiles:
            args += [f'--include="{inclf}"' for inclf in self.includeFiles]
        if self.defines:
            args += [f'--define-macro="{d}"' for d in self.defines]
        tu = self.index.parse(self.inputFile, args=args,
                              options=cidx.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
        return None


cidx.Config.set_library_path(
    CONFIG[c.AUTOFFF_SECTION][c.CLANG_SCANNER_SECTION][c.CLANG_SCANNER_LIBCLANG_PATH])
cidx.Config.set_library_file(
    CONFIG[c.AUTOFFF_SECTION][c.CLANG_SCANNER_SECTION][c.CLANG_SCANNER_LIBCLANG_FILE])
