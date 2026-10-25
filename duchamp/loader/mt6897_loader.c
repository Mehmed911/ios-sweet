#include "mt6897_loader.h"

unsigned
duchamp_mt6897_prepare(const void *fdt, size_t fdt_size,
    const void *payload, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    void *window, size_t window_size,
    const struct duchamp_framebuffer *framebuffer,
    struct duchamp_mt6897_handoff *handoff)
{
	struct duchamp_dry_run_plan plan;
	unsigned result;

	if (handoff == NULL || framebuffer == NULL) {
		return DUCHAMP_GUARD_ARGUMENT;
	}
	result = duchamp_loader_materialize(fdt, fdt_size, payload, payload_size,
	    occupied, occupied_count, framebuffer, window, window_size, &plan);
	if (result != DUCHAMP_GUARD_OK) {
		return result;
	}
	handoff->window_base = plan.boot_args.phys_base;
	handoff->window_size = plan.boot_args.memory_size;
	handoff->framebuffer_base = framebuffer->base;
	handoff->framebuffer_stride = framebuffer->stride;
	handoff->framebuffer_width = framebuffer->width;
	handoff->framebuffer_height = framebuffer->height;
	handoff->framebuffer_depth = framebuffer->depth;
	handoff->entry = plan.entry;
	handoff->boot_args = plan.boot_args.destination;
	handoff->segment_count = plan.segment_count;
	return DUCHAMP_GUARD_OK;
}
