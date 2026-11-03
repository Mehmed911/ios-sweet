#ifndef MT6897_UFS_DMA_ROUTE_H
#define MT6897_UFS_DMA_ROUTE_H

#include <stdint.h>

#include "mt6897_ufs_gate.h"

/*
 * Lease-bound PA-to-DMA/bounce contract for the MT6897 UFS path.
 *
 * This module performs no MMIO, cache maintenance, DMA or UFS command.  It
 * accepts either a pinned affine PA-to-DMA window or a dedicated bounce pool.
 * A zero-initialized object is disabled.  Binding and every ownership
 * transition revalidate the exact activation lease and an immutable receipt.
 *
 * The cache implementation is deliberately separate.  The receipt pins its
 * owner and implementation identifier (the source range for direct routing,
 * the bounce range for bounce routing), but callers must complete the cache
 * ownership handoff before dispatching a DMA command.  The controller and
 * firmware owners are pinned as well so a firewall receipt cannot float
 * between leases.  The contract therefore proves routing and bounce
 * disposition; it does not claim that physical UFS is ready.
 */

#define MT6897_UFS_DMA_ROUTE_CONTRACT_VERSION UINT32_C(1)

#define MT6897_UFS_DMA_PRIVATE_SOURCE          (UINT32_C(1) << 0)
#define MT6897_UFS_DMA_CONTIGUOUS_SOURCE       (UINT32_C(1) << 1)
#define MT6897_UFS_DMA_TRANSLATION_PINNED      (UINT32_C(1) << 2)
#define MT6897_UFS_DMA_ADDRESS_LIMIT_PINNED    (UINT32_C(1) << 3)
#define MT6897_UFS_DMA_FIREWALL_RECEIPT_PINNED (UINT32_C(1) << 4)
#define MT6897_UFS_DMA_CACHE_CONTRACT_PINNED   (UINT32_C(1) << 5)
#define MT6897_UFS_DMA_SERIALIZED_OWNERSHIP    (UINT32_C(1) << 6)
#define MT6897_UFS_DMA_DIRECT_WINDOW_PINNED    (UINT32_C(1) << 7)
#define MT6897_UFS_DMA_BOUNCE_POOL_PINNED      (UINT32_C(1) << 8)
#define MT6897_UFS_DMA_BOUNCE_COPY_PINNED      (UINT32_C(1) << 9)

#define MT6897_UFS_DMA_COMMON_FLAGS \
    (MT6897_UFS_DMA_PRIVATE_SOURCE | \
     MT6897_UFS_DMA_CONTIGUOUS_SOURCE | \
     MT6897_UFS_DMA_TRANSLATION_PINNED | \
     MT6897_UFS_DMA_ADDRESS_LIMIT_PINNED | \
     MT6897_UFS_DMA_FIREWALL_RECEIPT_PINNED | \
     MT6897_UFS_DMA_CACHE_CONTRACT_PINNED | \
     MT6897_UFS_DMA_SERIALIZED_OWNERSHIP)

#define MT6897_UFS_DMA_DIRECT_FLAGS \
    (MT6897_UFS_DMA_COMMON_FLAGS | MT6897_UFS_DMA_DIRECT_WINDOW_PINNED)

#define MT6897_UFS_DMA_BOUNCE_FLAGS \
    (MT6897_UFS_DMA_COMMON_FLAGS | MT6897_UFS_DMA_BOUNCE_POOL_PINNED | \
     MT6897_UFS_DMA_BOUNCE_COPY_PINNED)

enum mt6897_ufs_dma_route_result {
    MT6897_UFS_DMA_ROUTE_OK = 0,
    MT6897_UFS_DMA_ROUTE_ARGUMENT = -1,
    MT6897_UFS_DMA_ROUTE_DISABLED = -2,
    MT6897_UFS_DMA_ROUTE_LEASE = -3,
    MT6897_UFS_DMA_ROUTE_CONTRACT = -4,
    MT6897_UFS_DMA_ROUTE_STATE = -5,
    MT6897_UFS_DMA_ROUTE_RANGE = -6,
    MT6897_UFS_DMA_ROUTE_CALLBACK = -7,
    MT6897_UFS_DMA_ROUTE_FAULTED = -8
};

enum mt6897_ufs_dma_route_kind {
    MT6897_UFS_DMA_ROUTE_NONE = 0,
    MT6897_UFS_DMA_ROUTE_DIRECT_AFFINE = 1,
    MT6897_UFS_DMA_ROUTE_BOUNCE_POOL = 2
};

enum mt6897_ufs_dma_bounce_disposition {
    MT6897_UFS_DMA_BOUNCE_UNKNOWN = 0,
    MT6897_UFS_DMA_BOUNCE_NOT_REQUIRED = 1,
    MT6897_UFS_DMA_BOUNCE_REQUIRED = 2
};

enum mt6897_ufs_dma_direction {
    MT6897_UFS_DMA_TO_DEVICE = 1,
    MT6897_UFS_DMA_FROM_DEVICE = 2,
    MT6897_UFS_DMA_BIDIRECTIONAL = 3
};

enum mt6897_ufs_dma_route_state {
    MT6897_UFS_DMA_ROUTE_STATE_DISABLED = 0,
    MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED = 1,
    MT6897_UFS_DMA_ROUTE_STATE_CHECKING_DEVICE = 2,
    MT6897_UFS_DMA_ROUTE_STATE_TO_DEVICE = 3,
    MT6897_UFS_DMA_ROUTE_STATE_DEVICE_OWNED = 4,
    MT6897_UFS_DMA_ROUTE_STATE_CHECKING_CPU = 5,
    MT6897_UFS_DMA_ROUTE_STATE_TO_CPU = 6,
    MT6897_UFS_DMA_ROUTE_STATE_FAULTED = 7
};

struct mt6897_ufs_dma_route_receipt {
    uint32_t version;
    uint32_t flags;
    uint32_t route;
    uint32_t bounce_disposition;
    uint64_t boot_generation;
    uint64_t dma_owner_id;
    uint64_t cache_owner_id;
    uint64_t controller_owner_id;
    uint64_t firmware_owner_id;
    uint64_t source_owner_id;
    uint64_t source_cpu_begin;
    uint64_t source_pa_begin;
    uint64_t source_bytes;
    uint64_t device_begin;
    uint64_t device_bytes;
    uint64_t dma_limit;
    uint32_t dma_address_bits;
    uint32_t alignment;
    uint64_t translation_implementation_id;
    uint64_t firewall_receipt_id;
    uint64_t cache_contract_id;
    uint64_t bounce_owner_id;
    uint64_t bounce_cpu_begin;
    uint64_t bounce_pa_begin;
    uint64_t bounce_dma_begin;
    uint64_t bounce_bytes;
    uint64_t copy_to_implementation_id;
    uint64_t copy_from_implementation_id;
};

struct mt6897_ufs_dma_route_request {
    uint64_t cpu_address;
    uint64_t physical_address;
    uint64_t bytes;
    uint32_t direction;
    uint32_t reserved0;
};

struct mt6897_ufs_dma_route_mapping {
    uint64_t source_cpu_address;
    uint64_t source_physical_address;
    uint64_t dma_cpu_address;
    uint64_t dma_physical_address;
    uint64_t device_address;
    uint64_t bytes;
    uint64_t route_instance_id;
    uint64_t operation_id;
    uint64_t cookie;
    uint32_t direction;
    uint32_t bounced;
};

typedef int
(*mt6897_ufs_dma_route_verify_fn)(
    void *context,
    const struct mt6897_ufs_dma_route_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease);

typedef int
(*mt6897_ufs_dma_route_copy_fn)(
    void *context,
    uint64_t destination_cpu_address,
    uint64_t source_cpu_address,
    uint64_t bytes);

struct mt6897_ufs_dma_route_ops {
    void *context;
    mt6897_ufs_dma_route_verify_fn verify;
    mt6897_ufs_dma_route_copy_fn copy_to_bounce;
    mt6897_ufs_dma_route_copy_fn copy_from_bounce;
};

struct mt6897_ufs_dma_route {
    struct mt6897_ufs_gate *gate;
    struct mt6897_ufs_gate_lease lease;
    struct mt6897_ufs_dma_route_receipt receipt;
    struct mt6897_ufs_dma_route_ops ops;
    struct mt6897_ufs_dma_route_mapping active;
    uint64_t receipt_fingerprint;
    uint64_t route_instance_id;
    uint64_t next_operation_id;
    uint64_t transitions;
    uint32_t state;
    uint32_t fault_pending;
};

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_bind(
    struct mt6897_ufs_dma_route *route,
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease,
    const struct mt6897_ufs_dma_route_receipt *receipt,
    const struct mt6897_ufs_dma_route_ops *ops,
    uint64_t *blockers_out);

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_for_device(
    struct mt6897_ufs_dma_route *route,
    const struct mt6897_ufs_dma_route_request *request,
    struct mt6897_ufs_dma_route_mapping *mapping_out,
    uint64_t *blockers_out);

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_for_cpu(
    struct mt6897_ufs_dma_route *route,
    const struct mt6897_ufs_dma_route_mapping *mapping,
    uint64_t *blockers_out);

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_fault(
    struct mt6897_ufs_dma_route *route,
    uint64_t blocker,
    uint64_t *blockers_out);

#endif
