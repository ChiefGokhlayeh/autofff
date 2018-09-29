# Paths
ROOT_DIR = $(CURDIR)
AUTOFFF_DIR = $(ROOT_DIR)/autofff
TEST_DIR = $(ROOT_DIR)/test
EXAMPLES_DIR = $(ROOT_DIR)/examples
OUTPUT_DIR = $(ROOT_DIR)/output
DEPENDENCIES_DIR = $(ROOT_DIR)/dependencies
FFF_DIR ?= $(DEPENDENCIES_DIR)/fff

# Build settings
GTEST_OBJS ?= $(wildcard $(FFF_DIR)/build/gtest-*.o)
TEST_SOURCES = $(wildcard $(TEST_DIR)/*_unittest.cc)
TEST_EXES = $(patsubst $(TEST_DIR)/%,$(OUTPUT_DIR)/%,$(TEST_SOURCES:%.cc=%.exe))
TEST_INCLUDES = \
	-I$(TEST_DIR) \
	-I$(EXAMPLES_DIR) \
	-I$(OUTPUT_DIR) \
	-I$(FFF_DIR) \
	-I$(FFF_DIR)/gtest
TEST_HEADERS = $(wildcard $(EXAMPLES_DIR)/*.h)
TEST_FAKES = $(patsubst $(EXAMPLES_DIR)/%,$(OUTPUT_DIR)/%,$(TEST_HEADERS:%.h=%_th.h))

# Prevent make from deleting fakes as 'intermediate' files
.PRECIOUS: $(TEST_FAKES)

all: install_autofff run_tests
run_tests: build_tests
build_tests: build_gtest_lib $(TEST_EXES)

.PHONY: install_autofff
install_autofff:
	python3 -m pip install $(ROOT_DIR)
	@echo

.PHONY: gtest_lib
build_gtest_lib:
	mkdir -p $(FFF_DIR)/build
	$(MAKE) -C $(FFF_DIR)/gtest all
	@echo

.PHONY: clean_autofff
clean_autofff:
	$(RM) $(TEST_FAKES)
	@echo

.PHONY: clean_gtest
clean_gtest:
	$(MAKE) -C $(FFF_DIR)/gtest clean
	@echo

.PHONY: clean_unittest
clean_unittest:
	$(RM) $(TEST_EXES)
	@echo

.PHONY: uninstall_autofff
uninstall_autofff:
	python -m pip uninstall $(ROOT_DIR)
	@echo

.PHONY: clean
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

$(OUTPUT_DIR)/%_th.h: $(EXAMPLES_DIR)/%.h install_autofff
	@echo "Generating test-header: $<"
	python3 -m autofff -O $(abspath $@) $(TEST_INCLUDES) -F $(DEPENDENCIES_DIR)/pycparser/utils/fake_libc_include $<
	@echo