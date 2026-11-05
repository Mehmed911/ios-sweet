#include "payload_preflight.h"

#include "../loader/guard.h"

static uint32_t
le32(const unsigned char *p)
{
	return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
	    (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint64_t
le64(const unsigned char *p)
{
	return (uint64_t)le32(p) | (uint64_t)le32(p + 4) << 32;
}

static void
clear_preflight(struct duchamp_payload_preflight *p)
{
	p->result = DUCHAMP_GUARD_ARGUMENT;
	p->segment_count = 0;
	p->phys_base = 0;
	p->memory_size = 0;
	p->entry = 0;
	p->adt = 0;
	p->boot_args = 0;
	p->top = 0;
}

unsigned
duchamp_bootshim_payload_preflight(const void *fdt, size_t fdt_size,
	const void *payload_pointer, size_t payload_size,
	struct duchamp_payload_preflight *preflight)
{
	const unsigned char *payload = payload_pointer;
	struct duchamp_payload_plan plan;
	unsigned result;

	if (preflight == 0) {
		return DUCHAMP_GUARD_ARGUMENT;
	}
	clear_preflight(preflight);
	result = duchamp_loader_plan_check(fdt, fdt_size, payload, payload_size,
	    0, 0, &plan);
	preflight->result = result;
	if (result != DUCHAMP_GUARD_OK) {
		return result;
	}
	preflight->segment_count = le32(payload + 12);
	preflight->phys_base = le64(payload + 0x38);
	preflight->memory_size = le64(payload + 0x40);
	preflight->entry = plan.entry;
	preflight->adt = plan.adt;
	preflight->boot_args = plan.boot_args;
	preflight->top = plan.top;
	if (preflight->phys_base != DUCHAMP_PAYLOAD_EXPECTED_BASE ||
	    preflight->memory_size != DUCHAMP_PAYLOAD_EXPECTED_SIZE ||
	    preflight->segment_count == 0 || preflight->segment_count > 32 ||
	    preflight->entry < preflight->phys_base ||
	    preflight->entry >= preflight->phys_base + preflight->memory_size ||
	    preflight->top > preflight->phys_base + preflight->memory_size) {
		preflight->result = DUCHAMP_GUARD_PLATFORM;
		return DUCHAMP_GUARD_PLATFORM;
	}
	return DUCHAMP_GUARD_OK;
}
