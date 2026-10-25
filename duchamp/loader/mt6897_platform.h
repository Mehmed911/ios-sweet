#ifndef DUCHAMP_MT6897_PLATFORM_H
#define DUCHAMP_MT6897_PLATFORM_H

#include <stdint.h>

struct duchamp_mt6897_platform {
	uint64_t gicd_base;
	uint64_t gicr_base;
	uint64_t gicr_size;
	uint64_t timer_frequency;
	uint64_t framebuffer_base;
	uint64_t framebuffer_stride;
	uint32_t framebuffer_width;
	uint32_t framebuffer_height;
	uint32_t framebuffer_depth;
};

/* Values captured from the live Duchamp FDT; no MMIO is performed. */
void duchamp_mt6897_platform_profile(struct duchamp_mt6897_platform *platform);

#endif
