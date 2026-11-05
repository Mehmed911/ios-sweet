#ifndef DUCHAMP_BOOTSHIM_PAYLOAD_PREFLIGHT_H
#define DUCHAMP_BOOTSHIM_PAYLOAD_PREFLIGHT_H

#include <stddef.h>
#include <stdint.h>

#define DUCHAMP_PAYLOAD_EXPECTED_BASE UINT64_C(0x1c0000000)
#define DUCHAMP_PAYLOAD_EXPECTED_SIZE UINT64_C(0x20000000)

struct duchamp_payload_preflight {
	uint32_t result;
	uint32_t segment_count;
	uint64_t phys_base;
	uint64_t memory_size;
	uint64_t entry;
	uint64_t adt;
	uint64_t boot_args;
	uint64_t top;
};

unsigned duchamp_bootshim_payload_preflight(const void *fdt, size_t fdt_size,
	const void *payload, size_t payload_size,
	struct duchamp_payload_preflight *preflight);

#endif
