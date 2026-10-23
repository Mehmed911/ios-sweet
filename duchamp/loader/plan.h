#ifndef DUCHAMP_LOADER_PLAN_H
#define DUCHAMP_LOADER_PLAN_H

#include "guard.h"

#define DUCHAMP_MAX_SEGMENTS 32u

struct duchamp_framebuffer {
	uint64_t base;
	uint64_t stride;
	uint64_t width;
	uint64_t height;
	uint64_t depth;
};

struct duchamp_copy_plan {
	uint64_t source_offset;
	uint64_t destination;
	uint64_t copy_size;
	uint64_t zero_size;
};

struct duchamp_boot_args_plan {
	uint64_t destination;
	uint64_t virt_base;
	uint64_t phys_base;
	uint64_t memory_size;
	uint64_t top_of_kernel_data;
	uint64_t device_tree_virtual;
	uint64_t device_tree_size;
	struct duchamp_framebuffer video;
};

struct duchamp_dry_run_plan {
	uint64_t entry;
	unsigned segment_count;
	struct duchamp_copy_plan segments[DUCHAMP_MAX_SEGMENTS];
	struct duchamp_copy_plan adt;
	struct duchamp_boot_args_plan boot_args;
};

unsigned duchamp_loader_dry_run(const void *fdt, size_t fdt_size,
    const void *payload, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    const struct duchamp_framebuffer *framebuffer,
    struct duchamp_dry_run_plan *dry_run);

#endif
