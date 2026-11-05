#ifndef DUCHAMP_BOOTSHIM_LK_RAM_BOOT_H
#define DUCHAMP_BOOTSHIM_LK_RAM_BOOT_H

#include <stddef.h>
#include <stdint.h>

#define DUCHAMP_LK_RAM_BOOT_REPORT_MAGIC UINT64_C(0x5450524b4c435544)
#define DUCHAMP_LK_RAM_BOOT_REPORT_VERSION 1u
#define DUCHAMP_LK_RAM_BOOT_STAGING_BASE UINT64_C(0x90000000)
#define DUCHAMP_LK_RAM_BOOT_STAGING_CAPACITY UINT64_C(0x20000000)
#define DUCHAMP_LK_RAM_BOOT_XNU_WINDOW_BASE UINT64_C(0x1c0000000)
#define DUCHAMP_LK_RAM_BOOT_XNU_WINDOW_SIZE UINT64_C(0x20000000)

struct duchamp_lk_ram_boot_report {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint32_t result;
	uint32_t transport_state;
	uint32_t transport_error;
	uint32_t transport_detail;
	uint32_t prepare_result;
	uint32_t reserved;
	uint64_t generation;
	uint64_t bytes_read;
	uint64_t source_reads;
	uint64_t entry;
	uint64_t boot_args;
	uint64_t segment_count;
	uint64_t checksum;
};

_Static_assert(sizeof(struct duchamp_lk_ram_boot_report) == 96,
    "LK RAM report size");

extern struct duchamp_lk_ram_boot_report duchamp_lk_ram_boot_report;

unsigned duchamp_lk_ram_boot_run(const void *fdt, size_t fdt_size,
	const void *capsule, size_t capsule_size);

#endif
