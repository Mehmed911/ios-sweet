#include "mt6897_handoff.h"

static int
aligned(uint64_t value, uint64_t alignment)
{
	return (value & (alignment - 1u)) == 0;
}

unsigned
duchamp_mt6897_handoff_run(
	const struct duchamp_mt6897_handoff *handoff,
	const struct duchamp_mt6897_handoff_ops *ops,
	void *context)
{
	uint64_t window_end;
	unsigned result;

	if (handoff == NULL || ops == NULL || context == NULL ||
	    ops->disable_mmu == NULL || ops->clean_kernel_cache == NULL ||
	    ops->invalidate_instruction_cache == NULL ||
	    ops->install_translation == NULL || ops->enter_xnu == NULL) {
		return DUCHAMP_HANDOFF_ARGUMENT;
	}
	if (handoff->window_size > UINT64_MAX - handoff->window_base) {
		return DUCHAMP_HANDOFF_RANGE;
	}
	window_end = handoff->window_base + handoff->window_size;
	if (!aligned(handoff->window_base, 0x4000) ||
	    !aligned(handoff->entry, 4) || !aligned(handoff->boot_args, 0x4000) ||
	    handoff->window_size == 0 || handoff->entry < handoff->window_base ||
	    handoff->entry >= window_end ||
	    handoff->boot_args < handoff->window_base ||
	    handoff->boot_args > window_end ||
	    window_end - handoff->boot_args < 0x4000) {
		return DUCHAMP_HANDOFF_ALIGNMENT;
	}
	result = ops->disable_mmu(context);
	if (result != 0) return DUCHAMP_HANDOFF_SEQUENCE;
	result = ops->clean_kernel_cache(context, handoff->window_base,
	    handoff->window_size);
	if (result != 0) return DUCHAMP_HANDOFF_SEQUENCE;
	result = ops->install_translation(context, handoff->window_base,
	    handoff->window_size);
	if (result != 0) return DUCHAMP_HANDOFF_PLATFORM;
	result = ops->invalidate_instruction_cache(context);
	if (result != 0) return DUCHAMP_HANDOFF_SEQUENCE;
	result = ops->enter_xnu(context, handoff->entry, handoff->boot_args);
	return result == 0 ? DUCHAMP_HANDOFF_OK : DUCHAMP_HANDOFF_PLATFORM;
}
