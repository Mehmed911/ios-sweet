#ifndef DUCHAMP_MT6897_HANDOFF_H
#define DUCHAMP_MT6897_HANDOFF_H

#include "mt6897_loader.h"

enum duchamp_mt6897_handoff_result {
	DUCHAMP_HANDOFF_OK = 0,
	DUCHAMP_HANDOFF_ARGUMENT = 1,
	DUCHAMP_HANDOFF_ALIGNMENT = 2,
	DUCHAMP_HANDOFF_RANGE = 3,
	DUCHAMP_HANDOFF_SEQUENCE = 4,
	DUCHAMP_HANDOFF_PLATFORM = 5,
};

struct duchamp_mt6897_handoff_ops {
	unsigned (*disable_mmu)(void *context);
	unsigned (*clean_kernel_cache)(void *context, uint64_t base, uint64_t size);
	unsigned (*invalidate_instruction_cache)(void *context);
	unsigned (*install_translation)(void *context, uint64_t base, uint64_t size);
	unsigned (*enter_xnu)(void *context, uint64_t entry, uint64_t boot_args);
};

/*
 * Execute the platform-independent handoff order through platform callbacks.
 * A real MT6897 backend must provide the callbacks after its register and
 * exception-level contract has been verified; NULL callbacks are rejected.
 */
unsigned duchamp_mt6897_handoff_run(
	const struct duchamp_mt6897_handoff *handoff,
	const struct duchamp_mt6897_handoff_ops *ops,
	void *context);

#endif
