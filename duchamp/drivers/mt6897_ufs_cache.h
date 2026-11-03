#ifndef MT6897_UFS_CACHE_H
#define MT6897_UFS_CACHE_H

#include <stdint.h>

#include "mt6897_ufs_gate.h"

/*
 * Lease-bound cache ownership contract for a non-coherent MT6897 UFS path.
 *
 * This module contains no cache instruction, MMIO access, DMA mapping or UFS
 * command implementation.  A zero-initialized object is disabled.  Binding
 * and every ownership transition revalidate the exact UFS activation lease.
 * Physical cache callbacks are reachable only after a complete receipt has
 * pinned an exclusive, whole-cache-line range and the clean/flush/barrier
 * implementations responsible for it.
 *
 * The contract deliberately uses clean-to-PoC before every device handoff.
 * On return to the CPU, TO_DEVICE requires ordering only; FROM_DEVICE and
 * BIDIRECTIONAL require clean+invalidate-to-PoC ("flush" in XNU terminology).
 * This is safe only because the receipt requires exclusive serialized
 * ownership and forbids CPU aliases.
 *
 * Handoffs and mt6897_ufs_cache_fault() may be concurrent.  The transition
 * from CHECKING_* to TO_* is the authorization point: a fault which wins
 * before that transition prevents every cache callback.  A fault after the
 * transition revokes all subsequent handoffs; a callback from the current
 * handoff may already have started and must obey the platform's own locking.
 */

#define MT6897_UFS_CACHE_CONTRACT_VERSION UINT32_C(1)

#define MT6897_UFS_CACHE_NONCOHERENT_DEVICE (UINT32_C(1) << 0)
#define MT6897_UFS_CACHE_EXCLUSIVE_WHOLE_LINES (UINT32_C(1) << 1)
#define MT6897_UFS_CACHE_NO_CPU_ALIASES (UINT32_C(1) << 2)
#define MT6897_UFS_CACHE_SERIALIZED_OWNERSHIP (UINT32_C(1) << 3)
#define MT6897_UFS_CACHE_CLEAN_TO_POC_PINNED (UINT32_C(1) << 4)
#define MT6897_UFS_CACHE_FLUSH_TO_POC_PINNED (UINT32_C(1) << 5)
#define MT6897_UFS_CACHE_BARRIERS_PINNED (UINT32_C(1) << 6)

#define MT6897_UFS_CACHE_REQUIRED_FLAGS \
    (MT6897_UFS_CACHE_NONCOHERENT_DEVICE | \
     MT6897_UFS_CACHE_EXCLUSIVE_WHOLE_LINES | \
     MT6897_UFS_CACHE_NO_CPU_ALIASES | \
     MT6897_UFS_CACHE_SERIALIZED_OWNERSHIP | \
     MT6897_UFS_CACHE_CLEAN_TO_POC_PINNED | \
     MT6897_UFS_CACHE_FLUSH_TO_POC_PINNED | \
     MT6897_UFS_CACHE_BARRIERS_PINNED)

enum mt6897_ufs_cache_result {
    MT6897_UFS_CACHE_OK = 0,
    MT6897_UFS_CACHE_ARGUMENT = -1,
    MT6897_UFS_CACHE_DISABLED = -2,
    MT6897_UFS_CACHE_LEASE = -3,
    MT6897_UFS_CACHE_CONTRACT = -4,
    MT6897_UFS_CACHE_STATE = -5,
    MT6897_UFS_CACHE_CALLBACK = -6,
    MT6897_UFS_CACHE_FAULTED = -7
};

enum mt6897_ufs_cache_direction {
    MT6897_UFS_CACHE_TO_DEVICE = 1,
    MT6897_UFS_CACHE_FROM_DEVICE = 2,
    MT6897_UFS_CACHE_BIDIRECTIONAL = 3
};

enum mt6897_ufs_cache_barrier_phase {
    MT6897_UFS_CACHE_BARRIER_TO_DEVICE = 1,
    MT6897_UFS_CACHE_BARRIER_BEFORE_CPU = 2,
    MT6897_UFS_CACHE_BARRIER_AFTER_CPU = 3
};

enum mt6897_ufs_cache_state {
    MT6897_UFS_CACHE_STATE_DISABLED = 0,
    MT6897_UFS_CACHE_STATE_CPU_OWNED = 1,
    MT6897_UFS_CACHE_STATE_CHECKING_DEVICE = 2,
    MT6897_UFS_CACHE_STATE_TO_DEVICE = 3,
    MT6897_UFS_CACHE_STATE_DEVICE_OWNED = 4,
    MT6897_UFS_CACHE_STATE_CHECKING_CPU = 5,
    MT6897_UFS_CACHE_STATE_TO_CPU = 6,
    MT6897_UFS_CACHE_STATE_FAULTED = 7
};

struct mt6897_ufs_cache_receipt {
    uint32_t version;
    uint32_t flags;
    uint64_t boot_generation;
    uint64_t cache_owner_id;
    uint64_t range_owner_id;
    uint64_t cpu_address;
    uint64_t physical_address;
    uint64_t bytes;
    uint32_t cache_line_size;
    uint32_t reserved0;
    uint64_t clean_implementation_id;
    uint64_t flush_implementation_id;
    uint64_t barrier_implementation_id;
};

typedef int
(*mt6897_ufs_cache_verify_fn)(
    void *context,
    const struct mt6897_ufs_cache_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease);

typedef int
(*mt6897_ufs_cache_range_fn)(
    void *context,
    uint64_t cpu_address,
    uint64_t physical_address,
    uint64_t bytes,
    enum mt6897_ufs_cache_direction direction);

typedef int
(*mt6897_ufs_cache_barrier_fn)(
    void *context,
    enum mt6897_ufs_cache_barrier_phase phase,
    enum mt6897_ufs_cache_direction direction);

struct mt6897_ufs_cache_ops {
    void *context;
    mt6897_ufs_cache_verify_fn verify;
    mt6897_ufs_cache_range_fn clean_to_poc;
    mt6897_ufs_cache_range_fn flush_to_poc;
    mt6897_ufs_cache_barrier_fn barrier;
};

struct mt6897_ufs_cache {
    struct mt6897_ufs_gate *gate;
    struct mt6897_ufs_gate_lease lease;
    struct mt6897_ufs_cache_receipt receipt;
    struct mt6897_ufs_cache_ops ops;
    uint64_t receipt_fingerprint;
    uint64_t transitions;
    uint32_t state;
    uint32_t fault_pending;
};

/* Bind once from an all-zero object.  Failure never executes a cache range
 * callback.  The verify callback is also unreachable when the lease is not
 * valid or the receipt is structurally incomplete. */
enum mt6897_ufs_cache_result
mt6897_ufs_cache_bind(
    struct mt6897_ufs_cache *cache,
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease,
    const struct mt6897_ufs_cache_receipt *receipt,
    const struct mt6897_ufs_cache_ops *ops,
    uint64_t *blockers_out);

enum mt6897_ufs_cache_result
mt6897_ufs_cache_for_device(
    struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_direction direction,
    uint64_t *blockers_out);

enum mt6897_ufs_cache_result
mt6897_ufs_cache_for_cpu(
    struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_direction direction,
    uint64_t *blockers_out);

enum mt6897_ufs_cache_result
mt6897_ufs_cache_fault(
    struct mt6897_ufs_cache *cache,
    uint64_t blocker,
    uint64_t *blockers_out);

#endif
