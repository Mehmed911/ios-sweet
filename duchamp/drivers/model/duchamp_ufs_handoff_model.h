#ifndef DUCHAMP_UFS_HANDOFF_MODEL_H
#define DUCHAMP_UFS_HANDOFF_MODEL_H

#include <stddef.h>
#include <stdint.h>
#include "mt6897_ufs_gate.h"

#define UHF_VERSION 1u
#define UHF_BYTES 448u
#define UHF_SIGNED_BYTES 384u
#define UHF_DIGEST_BYTES 32u
#define UHF_BOARD_DUCHAMP_MT6897 0x6897u
#define UHF_SLOT_B 2u
#define UHF_STAGE_FINAL_BL31 1u

enum uhf_ownership {
    UHF_OWN_HCI = 1u << 0, UHF_OWN_CLOCKS = 1u << 1,
    UHF_OWN_POWER = 1u << 2, UHF_OWN_PHY = 1u << 3,
    UHF_OWN_RESETS = 1u << 4, UHF_OWN_IRQ = 1u << 5,
    UHF_OWN_DMA = 1u << 6, UHF_OWN_CACHE = 1u << 7,
    UHF_OWN_FIRMWARE = 1u << 8, UHF_OWN_REQUIRED = 0x1ff
};
enum uhf_prerequisite {
    UHF_RAILS_PINNED = 1u << 0, UHF_DOMAIN_ON = 1u << 1,
    UHF_BUS_CLOCKS_PINNED = 1u << 2, UHF_REFCLK_PINNED = 1u << 3,
    UHF_PHY_READY = 1u << 4, UHF_RESET_DEASSERTED = 1u << 5,
    UHF_HCE_OFF_OBSERVED = 1u << 6, UHF_NS_ACCESS_GRANTED = 1u << 7,
    UHF_LIFETIME_PINNED = 1u << 8, UHF_COLD_INIT_GRANTED = 1u << 9,
    UHF_READONLY_POLICY = 1u << 10, UHF_PREREQ_REQUIRED = 0x7ff
};
enum uhf_dma {
    UHF_DRAIN_COMPLETE = 1u << 0, UHF_QUEUE_SNAPSHOT_COMPLETE = 1u << 1,
    UHF_OLD_SUBMISSIONS_FENCED = 1u << 2, UHF_OLD_DESCRIPTORS_QUARANTINED = 1u << 3,
    UHF_XNU_MEMORY_ISOLATED = 1u << 4, UHF_DMA_CACHE_SYNCHRONIZED = 1u << 5,
    UHF_DMA_COMMON = 0x3f,
    UHF_DIRECT_FILTER_PROVEN = 1u << 6,
    UHF_SMMU_STREAM_BLOCKED = 1u << 7, UHF_IOTLB_INVALIDATED_SYNCED = 1u << 8,
    UHF_DEVICE_TRANSLATIONS_ACCOUNTED = 1u << 9,
    UHF_DMA_DIRECT_REQUIRED = UHF_DMA_COMMON | UHF_DIRECT_FILTER_PROVEN,
    UHF_DMA_IOMMU_REQUIRED = UHF_DMA_COMMON | UHF_SMMU_STREAM_BLOCKED |
        UHF_IOTLB_INVALIDATED_SYNCED | UHF_DEVICE_TRANSLATIONS_ACCOUNTED
};
enum uhf_queue_mode { UHF_LEGACY = 1, UHF_MCQ = 2 };

/* Host-endian decoded view. Never cast the wire buffer to this type. */
struct uhf_record {
    uint32_t board, slot, stage, route, ownership, prerequisites, dma;
    uint32_t queue_mode, queue_count, busy_queues, outstanding_dma, stream_id;
    uint64_t boot_id, sequence, issued_ms, expires_ms, hci_base, hci_bytes;
    uint64_t lease_id, evidence_fingerprint, provider_epoch, authority_id;
    uint64_t controller_owner, phy_owner, firmware_owner, dma_owner, cache_owner;
    uint64_t clock_owner, power_owner, reset_owner, irq_owner;
    uint64_t isolation_epoch, iommu_domain, queue_snapshot_id, fabric_fence_id;
    uint64_t descriptor_pool_id, cache_receipt_id, isolation_receipt_id;
    uint64_t protected_pa, protected_bytes;
    uint8_t kernel_digest[UHF_DIGEST_BYTES], firmware_digest[UHF_DIGEST_BYTES];
    uint8_t fdt_digest[UHF_DIGEST_BYTES];
};

/* Independent CPU-only observations from the policy owner, never populated
 * from the candidate record. Time uses the authenticated boot's shared
 * monotonic clock domain. Stream 0 is legal with a verified SMMU domain.
 */
struct uhf_current {
    uint32_t slot, route, stream_id;
    uint64_t boot_id, sequence, now_ms, max_age_ms, authority_id;
    uint64_t isolation_epoch, iommu_domain, protected_pa, protected_bytes;
    uint8_t kernel_digest[UHF_DIGEST_BYTES], firmware_digest[UHF_DIGEST_BYTES];
    uint8_t fdt_digest[UHF_DIGEST_BYTES];
};

struct uhf_ops {
    void *context;
    /* Verify the authority, the exact signed prefix, and the underlying
     * receipt scopes/lifetimes, including that they are still unrevoked.
     * The 64-byte proof starts at UHF_SIGNED_BYTES. Exactly 1 means success.
     * The callback cannot use MMIO, initiate DMA or grant resources.
     */
    int (*verify_provenance)(void *, const uint8_t *, size_t);
    int (*sample_current)(void *, struct uhf_current *);
};
enum uhf_result {
    UHF_OK, UHF_ARGUMENT, UHF_FORMAT, UHF_IDENTITY, UHF_FRESHNESS,
    UHF_RESOURCE, UHF_DMA_UNSAFE, UHF_PROVENANCE, UHF_LEASE, UHF_STATE, UHF_REVOKED
};
enum uhf_state {
    UHF_NEW, UHF_CHECKING, UHF_VALIDATED, UHF_CLAIMED, UHF_FAULTED
};

struct uhf_session {
    uint32_t state;
    struct mt6897_ufs_gate *gate;
    struct mt6897_ufs_gate_lease lease;
    struct uhf_ops ops;
    uint64_t last_now;
    uint8_t wire[UHF_BYTES];
};

/* Parse only. The output remains untouched on a malformed wire header. */
enum uhf_result uhf_parse(const void *, size_t, struct uhf_record *);
/* Start from zero. Accept takes one private copy from stable caller RAM.
 * Borrowed gate/context must outlive the session. No operation grants access
 * or publishes a replacement lease. Concurrent or reentrant operations are
 * refused, and revocation is terminal. Use separate sessions only in tests.
 */
enum uhf_result uhf_accept(struct uhf_session *, const void *, size_t,
    struct mt6897_ufs_gate *, const struct mt6897_ufs_gate_lease *,
    const struct uhf_ops *);
enum uhf_result uhf_claim(struct uhf_session *);
enum uhf_result uhf_check(struct uhf_session *);
void uhf_revoke(struct uhf_session *);

#endif
