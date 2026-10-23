#ifndef DUCHAMP_LOADER_GUARD_H
#define DUCHAMP_LOADER_GUARD_H

#include <stddef.h>
#include <stdint.h>

struct duchamp_range {
	uint64_t start;
	uint64_t size;
};

struct duchamp_payload_plan {
	uint64_t entry;
	uint64_t adt;
	uint64_t boot_args;
	uint64_t top;
};

enum duchamp_guard_result {
	DUCHAMP_GUARD_OK = 0,
	DUCHAMP_GUARD_ARGUMENT = 1,
	DUCHAMP_GUARD_PAYLOAD_HEADER = 2,
	DUCHAMP_GUARD_PAYLOAD_LAYOUT = 3,
	DUCHAMP_GUARD_PLATFORM = 4,
	DUCHAMP_GUARD_FDT_HEADER = 20,
	DUCHAMP_GUARD_FDT_STRUCTURE = 21,
	DUCHAMP_GUARD_FDT_BOARD = 22,
	DUCHAMP_GUARD_FDT_MEMORY = 23,
	DUCHAMP_GUARD_FDT_RESERVED = 24,
	DUCHAMP_GUARD_OCCUPIED = 25,
};

unsigned duchamp_payload_plan_check(const void *payload, size_t payload_size,
    struct duchamp_payload_plan *plan);
unsigned duchamp_fdt_window_check(const void *fdt, size_t fdt_size,
    uint64_t window_start, uint64_t window_size,
    const struct duchamp_range *occupied, unsigned occupied_count);
unsigned duchamp_loader_plan_check(const void *fdt, size_t fdt_size,
    const void *payload, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    struct duchamp_payload_plan *plan);

#endif
