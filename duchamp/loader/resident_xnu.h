#ifndef DUCHAMP_RESIDENT_XNU_H
#define DUCHAMP_RESIDENT_XNU_H

#include "materialize.h"
#include "resident_protocol.h"

#define DUCHAMP_RESIDENT_MAX_OCCUPIED 32u

struct duchamp_resident_xnu_context {
	const void *fdt;
	size_t fdt_size;
	uint64_t fdt_physical;
	const void *staging;
	size_t staging_capacity;
	uint64_t staging_physical;
	const struct duchamp_range *occupied;
	unsigned occupied_count;
	struct duchamp_framebuffer framebuffer;
	void *window;
	size_t window_size;
	struct duchamp_dry_run_plan completed_plan;
	unsigned prepare_result;
};

unsigned duchamp_resident_xnu_prepare(void *context, const void *payload,
	size_t payload_size, struct duchamp_resident_target *target);

#endif
