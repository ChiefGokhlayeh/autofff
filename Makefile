.PHONY: \
	all \
	build_tests \
	clean \
	clean_autofff \
	clean_gtest \
	clean_unittest \
	doctest \
	gtest_lib \
	install_autofff \
	patch_fff \
	run_tests \
	uninstall_autofff \
	unpatch_fff

# Paths
ROOT_DIR = $(CURDIR)
AUTOFFF_DIR = $(ROOT_DIR)/autofff
TEST_DIR = $(ROOT_DIR)/test
EXAMPLES_DIR = $(ROOT_DIR)/examples/simple-headers
OUTPUT_DIR = $(ROOT_DIR)/output
DEPENDENCIES_DIR = $(ROOT_DIR)/dependencies
FFF_DIR ?= $(DEPENDENCIES_DIR)/fff
FFF_PATCH_HINT = $(DEPENDENCIES_DIR)/fff/patched_by_autofff

# Build settings
GTEST_OBJS ?= \
	$(FFF_DIR)/build/lib/libgtest_main.a \
	$(FFF_DIR)/build/lib/libgtest.a
TEST_SOURCES = $(wildcard $(TEST_DIR)/*_unittest.cc)
TEST_EXES = $(patsubst $(TEST_DIR)/%,$(OUTPUT_DIR)/%,$(TEST_SOURCES:%.cc=%.exe))
TEST_INCLUDES = \
	-I$(TEST_DIR) \
	-I$(EXAMPLES_DIR) \
	-I$(OUTPUT_DIR) \
	-I$(FFF_DIR) \
	-I$(FFF_DIR)/build/_deps/googletest-src/googletest/include \
	-I$(FFF_DIR)/build/_deps/googletest-src/googletest/include/gtest
TEST_HEADERS = $(wildcard $(EXAMPLES_DIR)/*.h)
TEST_FAKES = $(patsubst $(EXAMPLES_DIR)/%,$(OUTPUT_DIR)/%,$(TEST_HEADERS:%.h=%_th.h))

AUTOFFF_CONFIG ?=
ifeq ($(AUTOFFF_CONFIG),)
AUTOFFF_CONFIG_FLAG =
else
AUTOFFF_CONFIG_FLAG = -c $(AUTOFFF_CONFIG)
endif

CMAKE?=cmake

# Prevent make from deleting fakes as 'intermediate' files
.PRECIOUS: $(TEST_FAKES)

all: install_autofff run_tests
run_tests: build_tests doctests
build_tests: build_gtest_lib $(TEST_EXES)
patch_fff: $(FFF_PATCH_HINT)

install_autofff:
	poetry install
	@echo

$(FFF_PATCH_HINT):
	cd $(FFF_DIR) && patch -p1 < ../fff.patch
	touch $(FFF_PATCH_HINT)

build_gtest_lib: patch_fff
	$(CMAKE) -B $(FFF_DIR)/build $(FFF_DIR) -DFFF_UNIT_TESTING=ON
	$(CMAKE) --build $(FFF_DIR)/build
	@echo

unpatch_fff:
	cd $(FFF_DIR) && patch -R -p1 < ../fff.patch
	$(RM) $(FFF_PATCH_HINT)

clean_autofff:
	$(RM) $(TEST_FAKES)
	@echo

clean_gtest:
	$(RM) -rf $(FFF_DIR)/build
	@echo

clean_unittest:
	$(RM) $(TEST_EXES)
	@echo

uninstall_autofff:
	poetry run pip uninstall -y autofff
	@echo

clean: clean_autofff clean_gtest clean_unittest uninstall_autofff

$(OUTPUT_DIR)/%.exe: $(TEST_DIR)/%.cc $(TEST_FAKES)
	@echo "Building file: $<"
	@echo "Invoking GCC C++ Suite"
	g++ -pthread $(TEST_INCLUDES) $(GTEST_OBJS) $< -o $@
	@echo "Finished building: $<"
	@echo

run_tests:
	@$(foreach exe,$(TEST_EXES),\
		echo "Executing Test: $(exe)"; \
		$(exe); \
		echo "Finished executing: $(exe)"; \
		echo \
	)

doctests:
	poetry run python -m phmutest README.md

$(OUTPUT_DIR)/%_th.h: $(EXAMPLES_DIR)/%.h install_autofff
	@echo "Generating test-header: $<"
	poetry run python -m autofff -O $(abspath $@) $(TEST_INCLUDES) -F $(DEPENDENCIES_DIR)/pycparser/utils/fake_libc_include $(AUTOFFF_CONFIG_FLAG) $<
	@echo
