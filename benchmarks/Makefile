# Builds every calibration kernel with identical flags so measurements are
# comparable. -g and frame pointers so perf report and Ghidra can map
# addresses to functions; -O2 so the compiler has already done its part.
CC      ?= gcc
CFLAGS  ?= -O2 -g -fno-omit-frame-pointer -Wall -Wextra -std=c11
LDFLAGS ?=
KERNELS := branch_mispredict pointer_chase cache_aos dep_chain
BINS    := $(foreach k,$(KERNELS),$(k)/bin/$(k))

all: $(BINS)

# One rule per kernel (a pattern target may only contain a single %).
define KERNEL_RULE
$(1)/bin/$(1): $(1)/main.c common/harness.h
	@mkdir -p $$(dir $$@)
	$$(CC) $$(CFLAGS) -I common -o $$@ $$< $$(LDFLAGS)
endef
$(foreach k,$(KERNELS),$(eval $(call KERNEL_RULE,$(k))))

# Stripped copies for Phase B (source-less) runs.
strip: all
	@for k in $(KERNELS); do cp $$k/bin/$$k $$k/bin/$$k.stripped && strip $$k/bin/$$k.stripped; done
	@echo "stripped binaries written next to the originals"

run: all
	@for k in $(KERNELS); do echo "== $$k"; ./$$k/bin/$$k; done

clean:
	rm -rf $(foreach k,$(KERNELS),$(k)/bin)

.PHONY: all strip run clean
