#ifndef DUCHAMP_BOOTSHIM_DIAGNOSTIC_H
#define DUCHAMP_BOOTSHIM_DIAGNOSTIC_H

#include <stdint.h>

#include "../loader/mt6897_entry.h"

#define DUCHAMP_DIAGNOSTIC_MAGIC UINT64_C(0x4455434844494147)
#define DUCHAMP_DIAGNOSTIC_VERSION UINT32_C(1)

enum duchamp_diagnostic_marker {
	DUCHAMP_MARKER_NONE = 0,
	DUCHAMP_MARKER_FAILURE = 1,
	DUCHAMP_MARKER_SUCCESS = 2,
};

struct duchamp_bootshim_diagnostic {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint32_t entry_result;
	uint32_t marker;
	uint32_t fdt_magic;
	uint32_t fdt_size;
	uint32_t watchdog_mode_before;
	uint32_t watchdog_mode_after;
	struct duchamp_mt6897_entry_state entry;
	uint64_t checksum;
};

extern struct duchamp_bootshim_diagnostic duchamp_bootshim_diagnostic;

#endif
