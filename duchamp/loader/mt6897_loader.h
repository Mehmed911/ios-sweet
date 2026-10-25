#ifndef DUCHAMP_MT6897_LOADER_H
#define DUCHAMP_MT6897_LOADER_H

#include "materialize.h"

#define DUCHAMP_MT6897_LOADER_VERSION 1u

struct duchamp_mt6897_handoff {
	uint64_t window_base;
	uint64_t window_size;
	uint64_t framebuffer_base;
	uint64_t framebuffer_stride;
	uint64_t framebuffer_width;
	uint64_t framebuffer_height;
	uint64_t framebuffer_depth;
	uint64_t entry;
	uint64_t boot_args;
	unsigned segment_count;
};

unsigned duchamp_mt6897_prepare(const void *fdt, size_t fdt_size,
    const void *payload, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    void *window, size_t window_size,
    const struct duchamp_framebuffer *framebuffer,
    struct duchamp_mt6897_handoff *handoff);

#endif
