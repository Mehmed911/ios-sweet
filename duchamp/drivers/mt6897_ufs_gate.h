#ifndef MT6897_UFS_GATE_H
#define MT6897_UFS_GATE_H

#include <stdint.h>

/*
 * Fail-closed MT6897 UFS activation policy.
 *
 * This module owns no MMIO addresses, SMC executor, DMA buffer or UFS
 * command callback. A successful decision is not a boolean: the external
 * verifier must return a boot-generation-bound lease which pins the exact
 * controller, PHY, firmware, cache and translation owners until boot end.
 * The caller must validate that lease before every later operation.
 *
 * A gate is one-shot. It may be initialized only from an all-zero object,
 * may call the verifier at most once, and has no reset/release/rearm API.
 * Clearing or copying its storage behind this interface is caller corruption,
 * not a supported state transition.
 */

#define MT6897_UFS_GATE_EVIDENCE_VERSION UINT32_C(2)
#define MT6897_UFS_GATE_LEASE_VERSION UINT32_C(1)

#define MT6897_UFS_DUCHAMP_HCI_BASE UINT64_C(0x112b0000)
#define MT6897_UFS_DUCHAMP_HCI_SIZE UINT64_C(0x3000)
#define MT6897_UFS_DUCHAMP_PHY_BASE UINT64_C(0x112a0000)
#define MT6897_UFS_DUCHAMP_PHY_SIZE UINT64_C(0x10000)
#define MT6897_UFS_DUCHAMP_DMA_SIZE UINT64_C(0x1000000000)
#define MT6897_UFS_DUCHAMP_DMA_LIMIT UINT64_C(0x0fffffffff)
#define MT6897_UFS_DUCHAMP_DMA_BITS UINT32_C(36)
#define MT6897_UFS_DUCHAMP_SIP_UFS64 UINT32_C(0xc2000276)

enum mt6897_ufs_gate_route {
    MT6897_UFS_GATE_ROUTE_NONE = 0,
    MT6897_UFS_GATE_ROUTE_DIRECT_DMA = 1,
    MT6897_UFS_GATE_ROUTE_IOMMU = 2
};

/* Positive facts. A fact is usable only when it is both known and asserted.
 * Static selector discovery is not FIRMWARE_EFFECT_CONTRACT. Linux resource
 * reservation is not RESOURCE_OWNERSHIP. A non-coherent observation is not
 * CACHE_MAINTENANCE_OWNERSHIP. */
#define MT6897_UFS_E_PLATFORM_MATCH (UINT64_C(1) << 0)
#define MT6897_UFS_E_FIRMWARE_EFFECT_CONTRACT (UINT64_C(1) << 1)
#define MT6897_UFS_E_RESOURCE_OWNERSHIP (UINT64_C(1) << 2)
#define MT6897_UFS_E_CACHE_MAINTENANCE_OWNERSHIP (UINT64_C(1) << 3)

#define MT6897_UFS_E_DIRECT_DMA_SELECTED (UINT64_C(1) << 8)
#define MT6897_UFS_E_DIRECT_DMA_APERTURE (UINT64_C(1) << 9)
#define MT6897_UFS_E_DIRECT_ADDRESS_TRANSLATION (UINT64_C(1) << 10)
#define MT6897_UFS_E_IOMMU_ABSENT (UINT64_C(1) << 11)
#define MT6897_UFS_E_BOUNCE_REQUIRED (UINT64_C(1) << 12)
#define MT6897_UFS_E_BOUNCE_NOT_REQUIRED (UINT64_C(1) << 13)
#define MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP (UINT64_C(1) << 14)

#define MT6897_UFS_E_IOMMU_ATTACHED (UINT64_C(1) << 24)
#define MT6897_UFS_E_IOMMU_DOMAIN_OWNERSHIP (UINT64_C(1) << 25)
#define MT6897_UFS_E_IOMMU_STREAM_ID (UINT64_C(1) << 26)
#define MT6897_UFS_E_IOMMU_TABLE_OWNERSHIP (UINT64_C(1) << 27)
#define MT6897_UFS_E_IOMMU_MAPPING_OWNERSHIP (UINT64_C(1) << 28)

/* Recognized observations; neither one authorizes activation. */
#define MT6897_UFS_E_NONCOHERENT_DEVICE (UINT64_C(1) << 32)
#define MT6897_UFS_E_SWIOTLB_POOL_PRESENT (UINT64_C(1) << 33)

#define MT6897_UFS_E_COMMON_REQUIRED \
    (MT6897_UFS_E_PLATFORM_MATCH | \
     MT6897_UFS_E_FIRMWARE_EFFECT_CONTRACT | \
     MT6897_UFS_E_RESOURCE_OWNERSHIP | \
     MT6897_UFS_E_CACHE_MAINTENANCE_OWNERSHIP)

#define MT6897_UFS_E_DIRECT_BASE_REQUIRED \
    (MT6897_UFS_E_DIRECT_DMA_SELECTED | \
     MT6897_UFS_E_DIRECT_DMA_APERTURE | \
     MT6897_UFS_E_DIRECT_ADDRESS_TRANSLATION | \
     MT6897_UFS_E_IOMMU_ABSENT)

#define MT6897_UFS_E_IOMMU_REQUIRED \
    (MT6897_UFS_E_IOMMU_ATTACHED | \
     MT6897_UFS_E_IOMMU_DOMAIN_OWNERSHIP | \
     MT6897_UFS_E_IOMMU_STREAM_ID | \
     MT6897_UFS_E_IOMMU_TABLE_OWNERSHIP | \
     MT6897_UFS_E_IOMMU_MAPPING_OWNERSHIP)

#define MT6897_UFS_E_ALL \
    (MT6897_UFS_E_COMMON_REQUIRED | MT6897_UFS_E_DIRECT_BASE_REQUIRED | \
     MT6897_UFS_E_BOUNCE_REQUIRED | MT6897_UFS_E_BOUNCE_NOT_REQUIRED | \
     MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP | MT6897_UFS_E_IOMMU_REQUIRED | \
     MT6897_UFS_E_NONCOHERENT_DEVICE | MT6897_UFS_E_SWIOTLB_POOL_PRESENT)

/* Missing evidence uses its MT6897_UFS_E_* bit. High bits are policy or
 * protocol blockers rather than an individual missing positive fact. */
#define MT6897_UFS_BLOCK_BOUNCE_DISPOSITION (UINT64_C(1) << 48)
#define MT6897_UFS_BLOCK_VERIFIER_MISSING (UINT64_C(1) << 49)
#define MT6897_UFS_BLOCK_VERIFIER_DENIED (UINT64_C(1) << 50)
#define MT6897_UFS_BLOCK_VERIFIER_FAULT (UINT64_C(1) << 51)
#define MT6897_UFS_BLOCK_VERIFIER_PROTOCOL (UINT64_C(1) << 52)
#define MT6897_UFS_BLOCK_BAD_STATE (UINT64_C(1) << 53)
#define MT6897_UFS_BLOCK_BAD_ARGUMENT (UINT64_C(1) << 54)
#define MT6897_UFS_BLOCK_BAD_VERSION (UINT64_C(1) << 55)
#define MT6897_UFS_BLOCK_UNKNOWN_ROUTE (UINT64_C(1) << 56)
#define MT6897_UFS_BLOCK_UNKNOWN_EVIDENCE (UINT64_C(1) << 57)
#define MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE (UINT64_C(1) << 58)
#define MT6897_UFS_BLOCK_BOOT_GENERATION (UINT64_C(1) << 59)
#define MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT (UINT64_C(1) << 60)
#define MT6897_UFS_BLOCK_BAD_LEASE (UINT64_C(1) << 61)
#define MT6897_UFS_BLOCK_PROVIDER_RUNTIME (UINT64_C(1) << 62)

#define MT6897_UFS_BLOCK_CONTROL_MASK \
    (MT6897_UFS_BLOCK_BOUNCE_DISPOSITION | \
     MT6897_UFS_BLOCK_VERIFIER_MISSING | MT6897_UFS_BLOCK_VERIFIER_DENIED | \
     MT6897_UFS_BLOCK_VERIFIER_FAULT | MT6897_UFS_BLOCK_VERIFIER_PROTOCOL | \
     MT6897_UFS_BLOCK_BAD_STATE | MT6897_UFS_BLOCK_BAD_ARGUMENT | \
     MT6897_UFS_BLOCK_BAD_VERSION | MT6897_UFS_BLOCK_UNKNOWN_ROUTE | \
     MT6897_UFS_BLOCK_UNKNOWN_EVIDENCE | \
     MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE | \
     MT6897_UFS_BLOCK_BOOT_GENERATION | \
     MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT | MT6897_UFS_BLOCK_BAD_LEASE | \
     MT6897_UFS_BLOCK_PROVIDER_RUNTIME)

#define MT6897_UFS_CURRENT_DUCHAMP_BLOCKERS \
    (MT6897_UFS_E_FIRMWARE_EFFECT_CONTRACT | \
     MT6897_UFS_E_RESOURCE_OWNERSHIP | \
     MT6897_UFS_E_CACHE_MAINTENANCE_OWNERSHIP | \
     MT6897_UFS_E_DIRECT_ADDRESS_TRANSLATION | \
     MT6897_UFS_BLOCK_BOUNCE_DISPOSITION)

#define MT6897_UFS_LEASE_NONREVOKABLE_UNTIL_BOOT_END (UINT32_C(1) << 0)
#define MT6897_UFS_LEASE_EXACT_RESOURCES_PINNED (UINT32_C(1) << 1)
#define MT6897_UFS_LEASE_FIRMWARE_OWNER_PINNED (UINT32_C(1) << 2)
#define MT6897_UFS_LEASE_CACHE_OWNER_PINNED (UINT32_C(1) << 3)
#define MT6897_UFS_LEASE_TRANSLATION_OWNER_PINNED (UINT32_C(1) << 4)
#define MT6897_UFS_LEASE_REQUIRED_FLAGS \
    (MT6897_UFS_LEASE_NONREVOKABLE_UNTIL_BOOT_END | \
     MT6897_UFS_LEASE_EXACT_RESOURCES_PINNED | \
     MT6897_UFS_LEASE_FIRMWARE_OWNER_PINNED | \
     MT6897_UFS_LEASE_CACHE_OWNER_PINNED | \
     MT6897_UFS_LEASE_TRANSLATION_OWNER_PINNED)

struct mt6897_ufs_gate_evidence {
    uint32_t version;
    uint32_t route;
    uint64_t boot_generation;
    uint64_t known;
    uint64_t asserted;
    uint8_t fdt_sha256[32];
    uint8_t firmware_sha256[32];
    uint8_t firmware_audit_sha256[32];
    uint8_t runtime_dma_report_sha256[32];
    uint8_t prdt_report_sha256[32];
    uint64_t ufs_hci_base;
    uint64_t ufs_hci_size;
    uint64_t ufs_phy_base;
    uint64_t ufs_phy_size;
    uint32_t firmware_service_id;
    uint32_t firmware_refclk_selector;
    uint32_t firmware_mtcmos_selector;
    uint32_t firmware_mcq_selector;
    uint64_t dma_cpu_start;
    uint64_t dma_device_start;
    uint64_t dma_size;
    uint64_t dma_limit;
    uint32_t dma_address_bits;
    uint32_t cache_line_size;
    uint64_t bounce_start;
    uint64_t bounce_size;
    uint64_t bounce_owner_id;
    uint32_t iommu_stream_id;
    uint32_t reserved0;
    uint64_t iommu_domain_id;
    uint64_t iommu_table_id;
    uint64_t iommu_mapping_epoch;
};

struct mt6897_ufs_gate_verifier_request {
    uint32_t version;
    uint32_t route;
    uint64_t required;
    uint64_t evidence_fingerprint;
    struct mt6897_ufs_gate_evidence evidence;
};

struct mt6897_ufs_gate_lease {
    uint32_t version;
    uint32_t flags;
    uint64_t boot_generation;
    uint64_t evidence_fingerprint;
    uint64_t lease_id;
    uint64_t provider_epoch;
    uint64_t controller_owner_id;
    uint64_t phy_owner_id;
    uint64_t dma_owner_id;
    uint64_t cache_owner_id;
    uint64_t firmware_owner_id;
};

enum mt6897_ufs_gate_verdict {
    MT6897_UFS_GATE_VERIFY_FAULT = -1,
    MT6897_UFS_GATE_VERIFY_DENY = 0,
    MT6897_UFS_GATE_VERIFY_APPROVE = 1
};

typedef enum mt6897_ufs_gate_verdict
(*mt6897_ufs_gate_verifier_fn)(
    void *context,
    const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease_out);

enum mt6897_ufs_gate_init_result {
    MT6897_UFS_GATE_INIT_OK = 0,
    MT6897_UFS_GATE_INIT_ARGUMENT = -1,
    MT6897_UFS_GATE_INIT_NOT_ZERO = -2,
    MT6897_UFS_GATE_INIT_GENERATION = -3
};

enum mt6897_ufs_gate_result {
    MT6897_UFS_GATE_LEASED = 0,
    MT6897_UFS_GATE_DENIED = -1,
    MT6897_UFS_GATE_FAULT = -2,
    MT6897_UFS_GATE_ARGUMENT = -3
};

enum mt6897_ufs_gate_state {
    MT6897_UFS_GATE_STATE_UNINITIALIZED = 0,
    MT6897_UFS_GATE_STATE_ARMED = 1,
    MT6897_UFS_GATE_STATE_VERIFYING = 2,
    MT6897_UFS_GATE_STATE_LEASED = 3,
    MT6897_UFS_GATE_STATE_DENIED = 4,
    MT6897_UFS_GATE_STATE_FAULT = 5,
    MT6897_UFS_GATE_STATE_CONTENDED = 6,
    MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE = 7,
    MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED = 8
};

struct mt6897_ufs_gate {
    uint64_t cookie;
    uint64_t boot_generation;
    uint64_t evidence_fingerprint;
    uint64_t blockers;
    uint32_t state;
    uint32_t contention;
    int32_t result;
    uint32_t reserved_state;
    struct mt6897_ufs_gate_lease lease;
};

enum mt6897_ufs_gate_init_result
mt6897_ufs_gate_init(struct mt6897_ufs_gate *gate, uint64_t boot_generation);

/* One-shot authorization. Incomplete local evidence is denied before the
 * verifier is called. On success, lease_out must be checked before each use. */
enum mt6897_ufs_gate_result
mt6897_ufs_gate_authorize(
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_evidence *evidence,
    mt6897_ufs_gate_verifier_fn verifier,
    void *verifier_context,
    struct mt6897_ufs_gate_lease *lease_out,
    uint64_t *blockers_out);

enum mt6897_ufs_gate_result
mt6897_ufs_gate_lease_check(
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease,
    uint64_t *blockers_out);

enum mt6897_ufs_gate_result
mt6897_ufs_gate_fault(
    struct mt6897_ufs_gate *gate,
    uint64_t provider_blocker,
    uint64_t *blockers_out);

uint64_t
mt6897_ufs_gate_evidence_fingerprint(
    const struct mt6897_ufs_gate_evidence *evidence);

struct mt6897_ufs_gate_evidence
mt6897_ufs_gate_duchamp_known_evidence(uint64_t boot_generation);

#endif
