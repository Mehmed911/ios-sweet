#include "mt6897_entry.h"

#define CURRENT_EL_EL1 UINT64_C(0x4)
#define SCTLR_M UINT64_C(1)
#define SCTLR_C (UINT64_C(1) << 2)
#define SCTLR_I (UINT64_C(1) << 12)

static int
range_contains(uint64_t base, uint64_t size, uint64_t address, uint64_t bytes)
{
	return size != 0 && address >= base && address - base <= size &&
	       bytes <= size - (address - base);
}

unsigned
duchamp_mt6897_entry_check(const struct duchamp_mt6897_entry_state *state,
	uint64_t fdt_range_base, uint64_t fdt_range_size)
{
	if (state == 0) {
		return DUCHAMP_ENTRY_ARGUMENT;
	}
	if (state->current_el != CURRENT_EL_EL1) {
		return DUCHAMP_ENTRY_EXCEPTION_LEVEL;
	}
	if ((state->sctlr_el1 & (SCTLR_M | SCTLR_C | SCTLR_I)) != 0) {
		return DUCHAMP_ENTRY_TRANSLATION_STATE;
	}
	if ((state->entry_x0 & 7) != 0 ||
	    !range_contains(fdt_range_base, fdt_range_size, state->entry_x0, 40)) {
		return DUCHAMP_ENTRY_FDT;
	}
	return DUCHAMP_ENTRY_OK;
}
