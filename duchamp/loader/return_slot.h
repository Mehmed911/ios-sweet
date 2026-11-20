#ifndef DUCHAMP_LOADER_RETURN_SLOT_H
#define DUCHAMP_LOADER_RETURN_SLOT_H

#include <stddef.h>
#include <stdint.h>

#include "plan.h"

#define DUCHAMP_RETURN_SLOT_MAGIC UINT64_C(0x545352444c554e58)

enum duchamp_return_slot_result {
	DUCHAMP_RETURN_SLOT_OK = 0,
	DUCHAMP_RETURN_SLOT_ARGUMENT = 1,
	DUCHAMP_RETURN_SLOT_RANGE = 2,
	DUCHAMP_RETURN_SLOT_NOT_FOUND = 3,
	DUCHAMP_RETURN_SLOT_MULTIPLE = 4,
	DUCHAMP_RETURN_SLOT_ALIGNMENT = 5,
};

struct duchamp_return_slot_report {
	uint32_t result;
	uint32_t matches;
	uint64_t slot_pa;
	uint64_t return_stub_pa;
	uint64_t checkpoint;
	uint64_t phys_minus_virt;
};

unsigned duchamp_loader_patch_return_slot(void *window, size_t window_size,
	const struct duchamp_dry_run_plan *plan, uint64_t return_stub_pa,
	uint64_t checkpoint, struct duchamp_return_slot_report *report);

#endif
