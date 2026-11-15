#ifndef DUCHAMP_UFS_HANDOFF_EVIDENCE_H
#define DUCHAMP_UFS_HANDOFF_EVIDENCE_H

#include <stddef.h>
#include <stdint.h>

#define DUCHAMP_UFS_HANDOFF_MAGIC UINT64_C(0x3153465548435544)
#define DUCHAMP_UFS_HANDOFF_VERSION 2u
#define DUCHAMP_UFS_HANDOFF_FDT_MAX (2u * 1024u * 1024u)

enum duchamp_ufs_slot_hint {
	DUCHAMP_UFS_SLOT_UNKNOWN,
	DUCHAMP_UFS_SLOT_A,
	DUCHAMP_UFS_SLOT_B,
	DUCHAMP_UFS_SLOT_INVALID,
};

enum duchamp_ufs_fdt_declaration {
	DUCHAMP_UFS_DECL_HCI_REG = 1u << 0,
	DUCHAMP_UFS_DECL_CLOCKS = 1u << 1,
	DUCHAMP_UFS_DECL_PHY = 1u << 2,
	DUCHAMP_UFS_DECL_POWER_DOMAIN = 1u << 3,
	DUCHAMP_UFS_DECL_RTFF_MTCMOS = 1u << 4,
	DUCHAMP_UFS_DECL_RESETS = 1u << 5,
	DUCHAMP_UFS_DECL_VCC = 1u << 6,
	DUCHAMP_UFS_DECL_VCCQ = 1u << 7,
};

enum duchamp_ufs_handoff_blocker {
	DUCHAMP_UFS_NO_TRACE = 1u << 0,
	DUCHAMP_UFS_HCE_UNKNOWN = 1u << 1,
	DUCHAMP_UFS_QUEUES_UNKNOWN = 1u << 2,
	DUCHAMP_UFS_DMA_UNVERIFIED = 1u << 3,
	DUCHAMP_UFS_FDT_INVALID = 1u << 4,
	DUCHAMP_UFS_SLOT_UNVERIFIED = 1u << 5,
	DUCHAMP_UFS_OWNER_UNVERIFIED = 1u << 6,
	DUCHAMP_UFS_POWER_UNVERIFIED = 1u << 7,
	DUCHAMP_UFS_CLOCKS_UNVERIFIED = 1u << 8,
	DUCHAMP_UFS_MMIO_UNVERIFIED = 1u << 9,
	DUCHAMP_UFS_PHY_UNVERIFIED = 1u << 10,
};

struct duchamp_ufs_handoff_record {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint64_t fdt_fingerprint;
	uint32_t fdt_bytes;
	uint32_t blockers;
	uint32_t slot_hint;
	uint32_t declarations;
};

/* Only reads the caller's bounded FDT in RAM. Slot hints and declarations
 * describe that blob. They cannot establish boot provenance or authority.
 * NULL FDT publishes the initial blocked state without reading any bytes.
 */
void duchamp_ufs_handoff_collect(struct duchamp_ufs_handoff_record *,
	const volatile unsigned char *fdt, size_t available);

#endif
