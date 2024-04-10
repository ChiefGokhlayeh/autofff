import logging
import sys

from configobj import ConfigObj
from validate import Validator

LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":
    LOGGER.error("Module is not intended to run as '__main__'!")
    sys.exit(1)

AUTOFFF_SECTION = "autofff"

SCANNER_TYPE = "scanner_type"
GCC_HEADER_SCANNER_TYPE = "gcc_header"
GCC_OBJECT_SCANNER_TYPE = "gcc_object"
SCANNER_TYPE_DEF = GCC_HEADER_SCANNER_TYPE

GENERATOR_TYPE = "generator_type"
BARE_GENERATOR_TYPE = "bare"
SIMPLE_GENERATOR_TYPE = "simple"
GENERATOR_TYPE_DEF = SIMPLE_GENERATOR_TYPE

GCC_SCANNER_SECTION = "gcc.scanner"

GCC_SCANNER_CPP_PATH = "cpp_path"
GCC_SCANNER_CPP_PATH_DEF = "cpp"

GCC_SCANNER_CPP_ARGS = "cpp_args"
GCC_SCANNER_CPP_ARGS_DEF = (
    "list("
    + ", ".join(
        [
            r"'-D__attribute__(x)='",
            r"'-D__asm__(x)='",
            r"'-D__const='",
            r"'-D__const__='",
            r"'-D__restrict='",
            r"'-D__restrict__='",
            r"'-D__extension__='",
            r"'-D__inline='",
            r"'-D__forcedinline='",
            r"'-D__inline__='",
        ]
    )
    + ")"
)

GCC_SCANNER_CPP_INCLUDE_DIR_PREFIX = "cpp_include_dir_prefix"
GCC_SCANNER_CPP_INCLUDE_DIR_PREFIX_DEF = "-I"

GCC_SCANNER_CPP_INCLUDE_FILE_PREFIX = "cpp_include_file_prefix"
GCC_SCANNER_CPP_INCLUDE_FILE_PREFIX_DEF = "-include"

GCC_SCANNER_CPP_DEFINE_PREFIX = "cpp_define_prefix"
GCC_SCANNER_CPP_DEFINE_PREFIX_DEF = "-D"

GCC_SCANNER_NON_STANDARD_IGNORE_PATTERN = "non_standard_ignore_pattern"
GCC_SCANNER_NON_STANDARD_IGNORE_PATTERN_DEF = r"([\s\n]*(\W(__asm|asm|__asm__)\W)[\s\n]*(volatile|[\s\n]*)(goto|[\s\n]*)(.|\n|;)*?;)"

GCC_SCANNER_ERROR_CONTEXT_PREV_LINES = "error_context_prev_lines"
GCC_SCANNER_ERROR_CONTEXT_PREV_LINES_MIN = 0
GCC_SCANNER_ERROR_CONTEXT_PREV_LINES_DEF = 5
GCC_SCANNER_ERROR_CONTEXT_POST_LINES = "error_context_post_lines"
GCC_SCANNER_ERROR_CONTEXT_POST_LINES_MIN = 0
GCC_SCANNER_ERROR_CONTEXT_POST_LINES_DEF = 5

GCC_SCANNER_IGNORE_ANNOTATION = "ignore_annotation"
GCC_SCANNER_IGNORE_ANNOTATION_DEF = "AUTOFFF_SCAN_IGNORE"

SIMPLE_GENERATOR_SECTION = "simple.generator"

SIMPLE_GENERATOR_GENERATE_INCLUDE_GUARD = "generate_include_guard"
SIMPLE_GENERATOR_GENERATE_INCLUDE_GUARD_DEF = True

SIMPLE_GENERATOR_FFF_PATH = "fff_path"
SIMPLE_GENERATOR_FFF_PATH_DEF = "fff.h"

BARE_GENERATOR_SECTION = "bare.generator"

VALIDATOR = Validator()
CONFIG_SPEC = [
    f"[{AUTOFFF_SECTION}]",
    f"{SCANNER_TYPE} = option('{GCC_HEADER_SCANNER_TYPE}', '{GCC_OBJECT_SCANNER_TYPE}', default='{SCANNER_TYPE_DEF}')",
    f"{GENERATOR_TYPE} = option('{BARE_GENERATOR_TYPE}', '{SIMPLE_GENERATOR_TYPE}', default='{GENERATOR_TYPE_DEF}')",
    f"[[{GCC_SCANNER_SECTION}]]",
    f"{GCC_SCANNER_CPP_PATH} = string(default='{GCC_SCANNER_CPP_PATH_DEF}')",
    f"{GCC_SCANNER_CPP_ARGS} = string_list(default={GCC_SCANNER_CPP_ARGS_DEF})",
    f"{GCC_SCANNER_CPP_INCLUDE_DIR_PREFIX} = string(default='{GCC_SCANNER_CPP_INCLUDE_DIR_PREFIX_DEF}')",
    f"{GCC_SCANNER_CPP_INCLUDE_FILE_PREFIX} = string(default='{GCC_SCANNER_CPP_INCLUDE_FILE_PREFIX_DEF}')",
    f"{GCC_SCANNER_CPP_DEFINE_PREFIX} = string(default='{GCC_SCANNER_CPP_DEFINE_PREFIX_DEF}')",
    f"{GCC_SCANNER_NON_STANDARD_IGNORE_PATTERN} = string(default={GCC_SCANNER_NON_STANDARD_IGNORE_PATTERN_DEF})",
    f"{GCC_SCANNER_ERROR_CONTEXT_PREV_LINES} = integer(min={GCC_SCANNER_ERROR_CONTEXT_PREV_LINES_MIN}, default={GCC_SCANNER_ERROR_CONTEXT_PREV_LINES_DEF})",
    f"{GCC_SCANNER_ERROR_CONTEXT_POST_LINES} = integer(min={GCC_SCANNER_ERROR_CONTEXT_POST_LINES_MIN}, default={GCC_SCANNER_ERROR_CONTEXT_POST_LINES_DEF})",
    f"{GCC_SCANNER_IGNORE_ANNOTATION} = string(default={GCC_SCANNER_IGNORE_ANNOTATION_DEF})",
    f"[[{SIMPLE_GENERATOR_SECTION}]]",
    f"{SIMPLE_GENERATOR_GENERATE_INCLUDE_GUARD} = boolean(default={SIMPLE_GENERATOR_GENERATE_INCLUDE_GUARD_DEF})",
    f"{SIMPLE_GENERATOR_FFF_PATH} = string(default={SIMPLE_GENERATOR_FFF_PATH_DEF})",
    f"[[{BARE_GENERATOR_SECTION}]]",
]
CONFIG = ConfigObj(configspec=CONFIG_SPEC, raise_errors=True)
CONFIG.validate(VALIDATOR)  # Invoke validator once to get basic structure


def load(filename: str):
    global CONFIG, VALIDATOR
    CONFIG.filename = filename
    CONFIG.reload()
    CONFIG.validate(VALIDATOR)
