#ifndef DUCHAMP_BOOTSHIM_HANDOFF_READY_H
#define DUCHAMP_BOOTSHIM_HANDOFF_READY_H

#include <stdint.h>

enum duchamp_handoff_ready_result {
	DUCHAMP_READY_OK = 0,
	DUCHAMP_READY_ARGUMENT = 1,
	DUCHAMP_READY_EXCEPTION_LEVEL = 2,
	DUCHAMP_READY_TRANSLATION_STATE = 3,
	DUCHAMP_READY_RANGE = 4,
	DUCHAMP_READY_ALIGNMENT = 5,
};

struct duchamp_handoff_ready {
	uint32_t result;
	uint32_t reserved;
	uint64_t current_el;
	uint64_t sctlr;
	uint64_t entry;
	uint64_t boot_args;
};

unsigned duchamp_handoff_ready_check(uint64_t current_el, uint64_t sctlr,
	uint64_t window_base, uint64_t window_size, uint64_t entry,
	uint64_t boot_args, struct duchamp_handoff_ready *report);
void duchamp_handoff_barrier(void);

#endif
