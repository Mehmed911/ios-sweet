#ifndef DUCHAMP_BOOTSHIM_PHONE_CAPTURE_H
#define DUCHAMP_BOOTSHIM_PHONE_CAPTURE_H

#include <stddef.h>
#include <stdint.h>

#define DUCHAMP_PHONE_CAPTURE_MAGIC UINT64_C(0x3130435048435544)
#define DUCHAMP_PHONE_CAPTURE_VERSION UINT32_C(1)

enum duchamp_phone_capture_state {
	DUCHAMP_PHONE_CAPTURE_NOT_RENDERED = 0,
	DUCHAMP_PHONE_CAPTURE_RENDERING = 1,
	DUCHAMP_PHONE_CAPTURE_COMPLETE = 2,
};

enum duchamp_phone_capture_result {
	DUCHAMP_PHONE_CAPTURE_OK = 0,
	DUCHAMP_PHONE_CAPTURE_UNSAFE_ENTRY = 1,
	DUCHAMP_PHONE_CAPTURE_BAD_FRAMEBUFFER = 2,
};

struct duchamp_phone_capture_record {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint64_t entry_pc;
	uint64_t entry_x0;
	uint64_t current_el;
	uint64_t sctlr;
	uint32_t entry_result;
	uint32_t render_state;
	uint64_t checksum;
};

uint64_t duchamp_phone_capture_checksum(
	const struct duchamp_phone_capture_record *record);
unsigned duchamp_phone_capture_run(volatile void *framebuffer,
	size_t stride, size_t width, size_t height, uint64_t entry_pc,
	uint64_t entry_x0, uint64_t current_el, uint64_t sctlr,
	unsigned entry_result, struct duchamp_phone_capture_record *record);

#endif
