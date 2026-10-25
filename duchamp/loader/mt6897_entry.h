#ifndef DUCHAMP_MT6897_ENTRY_H
#define DUCHAMP_MT6897_ENTRY_H

#include <stdint.h>

enum duchamp_mt6897_entry_result {
	DUCHAMP_ENTRY_OK = 0,
	DUCHAMP_ENTRY_ARGUMENT = 1,
	DUCHAMP_ENTRY_EXCEPTION_LEVEL = 2,
	DUCHAMP_ENTRY_TRANSLATION_STATE = 3,
	DUCHAMP_ENTRY_FDT = 4,
};

struct duchamp_mt6897_entry_state {
	uint64_t current_el;
	uint64_t sctlr_el1;
	uint64_t entry_x0;
	uint64_t entry_x1;
	uint64_t entry_x2;
	uint64_t entry_x3;
	uint64_t entry_sp;
};

unsigned duchamp_mt6897_entry_check(
	const struct duchamp_mt6897_entry_state *state,
	uint64_t fdt_range_base, uint64_t fdt_range_size);

#endif
