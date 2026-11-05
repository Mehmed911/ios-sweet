#ifndef DUCHAMP_MT6897_RAM_PROVIDER_H
#define DUCHAMP_MT6897_RAM_PROVIDER_H

#include <stddef.h>
#include <stdint.h>

#define DUCHAMP_MT6897_RAM_PROVIDER_MAGIC UINT64_C(0x3152504c48435544)
#define DUCHAMP_MT6897_RAM_PROVIDER_VERSION 1u

#define DUCHAMP_MT6897_RAM_PROVIDER_RAM_ONLY (UINT32_C(1) << 0)
#define DUCHAMP_MT6897_RAM_PROVIDER_ENTRY_PC_OBSERVED (UINT32_C(1) << 1)
#define DUCHAMP_MT6897_RAM_PROVIDER_ENTRY_X0_OBSERVED (UINT32_C(1) << 2)
#define DUCHAMP_MT6897_RAM_PROVIDER_FDT_IN_RAM (UINT32_C(1) << 3)
#define DUCHAMP_MT6897_RAM_PROVIDER_CAPSULE_IMMUTABLE (UINT32_C(1) << 4)
#define DUCHAMP_MT6897_RAM_PROVIDER_NO_STORAGE_WRITE (UINT32_C(1) << 5)
#define DUCHAMP_MT6897_RAM_PROVIDER_CAPSULE_IN_IMAGE (UINT32_C(1) << 6)

#define DUCHAMP_MT6897_RAM_PROVIDER_REQUIRED_FLAGS \
	(DUCHAMP_MT6897_RAM_PROVIDER_RAM_ONLY | \
	 DUCHAMP_MT6897_RAM_PROVIDER_ENTRY_PC_OBSERVED | \
	 DUCHAMP_MT6897_RAM_PROVIDER_ENTRY_X0_OBSERVED | \
	 DUCHAMP_MT6897_RAM_PROVIDER_FDT_IN_RAM | \
	 DUCHAMP_MT6897_RAM_PROVIDER_CAPSULE_IMMUTABLE | \
	 DUCHAMP_MT6897_RAM_PROVIDER_NO_STORAGE_WRITE)
#define DUCHAMP_MT6897_RAM_PROVIDER_ALL_FLAGS \
	(DUCHAMP_MT6897_RAM_PROVIDER_REQUIRED_FLAGS | \
	 DUCHAMP_MT6897_RAM_PROVIDER_CAPSULE_IN_IMAGE)

enum duchamp_mt6897_ram_provider_kind {
	DUCHAMP_MT6897_RAM_PROVIDER_NONE = 0,
	DUCHAMP_MT6897_RAM_PROVIDER_LK = 1,
	DUCHAMP_MT6897_RAM_PROVIDER_UEFI = 2,
	DUCHAMP_MT6897_RAM_PROVIDER_QEMU_REHEARSAL = 3,
};

enum duchamp_mt6897_ram_provider_result {
	DUCHAMP_MT6897_RAM_PROVIDER_OK = 0,
	DUCHAMP_MT6897_RAM_PROVIDER_ARGUMENT = 1,
	DUCHAMP_MT6897_RAM_PROVIDER_BAD_VERSION = 2,
	DUCHAMP_MT6897_RAM_PROVIDER_KIND = 3,
	DUCHAMP_MT6897_RAM_PROVIDER_EVIDENCE = 4,
	DUCHAMP_MT6897_RAM_PROVIDER_ENTRY = 5,
	DUCHAMP_MT6897_RAM_PROVIDER_FDT = 6,
	DUCHAMP_MT6897_RAM_PROVIDER_RANGE = 7,
	DUCHAMP_MT6897_RAM_PROVIDER_OVERLAP = 8,
	DUCHAMP_MT6897_RAM_PROVIDER_RECEIPT = 9,
};

struct duchamp_mt6897_ram_region {
	uint64_t base;
	uint64_t size;
};

struct duchamp_mt6897_ram_provider_contract {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint32_t kind;
	uint32_t flags;
	uint64_t current_el;
	uint64_t sctlr_el1;
	uint64_t entry_pc;
	uint64_t entry_x0;
	struct duchamp_mt6897_ram_region image;
	struct duchamp_mt6897_ram_region fdt;
	struct duchamp_mt6897_ram_region capsule;
	struct duchamp_mt6897_ram_region staging;
	struct duchamp_mt6897_ram_region xnu;
	uint64_t expected_fdt_receipt;
};

struct duchamp_mt6897_ram_provider_report {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint32_t result;
	uint32_t detail;
	uint32_t kind;
	uint32_t flags;
	uint32_t transport_allowed;
	uint32_t xnu_jump_allowed;
	uint64_t entry_pc;
	uint64_t entry_x0;
	uint64_t fdt_pa;
	uint64_t fdt_size;
	uint64_t fdt_receipt;
	uint64_t image_base;
	uint64_t image_size;
	uint64_t capsule_base;
	uint64_t capsule_size;
	uint64_t staging_base;
	uint64_t staging_size;
	uint64_t xnu_base;
	uint64_t xnu_size;
	uint64_t checksum;
};

_Static_assert(sizeof(struct duchamp_mt6897_ram_provider_report) == 152,
    "RAM provider report size");

uint64_t duchamp_mt6897_ram_provider_checksum(
	const struct duchamp_mt6897_ram_provider_report *report);

unsigned duchamp_mt6897_ram_provider_validate(
	const struct duchamp_mt6897_ram_provider_contract *contract,
	const void *fdt_bytes, size_t fdt_available,
	unsigned allow_qemu_rehearsal,
	struct duchamp_mt6897_ram_provider_report *report);

#endif
