# --------------------------------------------------------------------------- #
# Demonstration of auto-generating fake headers for your API headers
# using 'make'
# --------------------------------------------------------------------------- #
# Usage:
#	make -f generate_fakes.mk CRAWL_PATHS="path/to/include1 path/to/include2"
ifndef CRAWL_PATHS
$(error 'CRAWL_PATHS' is undefined! Please pass it as a cmd-line arg or \
	define it in another makefile)
endif

# Optional parameters:
OUTPUT_PATH?=./output
INCLUDE_PATHS?=
INCLUDE_FILE_PATHS?=
FAKE_INCLUDE_PATHS?=./dependencies/pycparser/utils/fake_libc_include
PYTHON?=py -3.6
VERBOSE?=0

# Configure suppressing of commands depending on $(VERBOSE) value
ifneq ($(VERBOSE),0)
V=
else
V=@
endif

define discover_headers
$(foreach dir,$(1),$(shell find $(1) -name *.h))
endef

HEADER_PATHS=$(call discover_headers,$(CRAWL_PATHS))
OUTPUT_FILE_PATHS=$(patsubst %.h,$(OUTPUT_PATH)/%_th.h,$(HEADER_PATHS))

.PHONY: all
all: $(OUTPUT_FILE_PATHS)

$(OUTPUT_PATH)/%_th.h: %.h
	$(V)echo Generating fakes for: $<
	$(V)PYTHON autofff.py \
		-O$@ \
		$(addprefix -I,$(INCLUDE_PATHS)) \
		$(addprefix -F,$(FAKE_INCLUDE_PATHS)) \
		$(addprefix -i,$(INCLUDE_FILE_PATHS)) \
		$<