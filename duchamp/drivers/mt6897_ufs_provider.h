#ifndef MT6897_UFS_PROVIDER_H
#define MT6897_UFS_PROVIDER_H

#include <stdint.h>

#include "mt6897_ufs_gate.h"

/*
 * Lease-guarded MT6897 UFS dispatch shell.
 *
 * This module contains no physical MMIO, SMC, cache, DMA, PHY or UFS command
 * implementation.  A zero-initialized provider is disabled.  The sole
 * dispatch callback is reachable only after a valid gate lease has been bound
 * and revalidated immediately before the operation.
 *
 * Provider calls and mt6897_ufs_provider_fault() may be concurrent.  The
 * transition from CHECKING to DISPATCHING is the authorization point: a fault
 * which wins before that transition prevents the callback.  A fault after the
 * transition revokes all subsequent operations; the current callback may
 * already have started and must itself obey the provider's platform locking.
 */

#define MT6897_UFS_PROVIDER_REQUEST_VERSION UINT32_C(1)

enum mt6897_ufs_provider_result {
    MT6897_UFS_PROVIDER_OK = 0,
    MT6897_UFS_PROVIDER_ARGUMENT = -1,
    MT6897_UFS_PROVIDER_DISABLED = -2,
    MT6897_UFS_PROVIDER_LEASE = -3,
    MT6897_UFS_PROVIDER_STATE = -4,
    MT6897_UFS_PROVIDER_CALLBACK = -5,
    MT6897_UFS_PROVIDER_FAULTED = -6
};

enum mt6897_ufs_provider_state {
    MT6897_UFS_PROVIDER_STATE_DISABLED = 0,
    MT6897_UFS_PROVIDER_STATE_ACTIVE = 1,
    MT6897_UFS_PROVIDER_STATE_CHECKING = 2,
    MT6897_UFS_PROVIDER_STATE_DISPATCHING = 3,
    MT6897_UFS_PROVIDER_STATE_FAULTED = 4
};

enum mt6897_ufs_provider_operation {
    MT6897_UFS_PROVIDER_POWER = 0,
    MT6897_UFS_PROVIDER_CLOCK = 1,
    MT6897_UFS_PROVIDER_PHY = 2,
    MT6897_UFS_PROVIDER_MMIO = 3,
    MT6897_UFS_PROVIDER_DMA = 4,
    MT6897_UFS_PROVIDER_COMMAND = 5,
    MT6897_UFS_PROVIDER_OPERATION_COUNT = 6
};

struct mt6897_ufs_provider_request {
    uint32_t version;
    uint32_t operation;
    uint64_t argument[4];
};

typedef int
(*mt6897_ufs_provider_dispatch_fn)(
    void *context,
    const struct mt6897_ufs_provider_request *request,
    uint64_t *result_out);

struct mt6897_ufs_provider_ops {
    void *context;
    mt6897_ufs_provider_dispatch_fn dispatch;
};

struct mt6897_ufs_provider {
    struct mt6897_ufs_gate *gate;
    struct mt6897_ufs_gate_lease lease;
    struct mt6897_ufs_provider_ops ops;
    uint32_t state;
    uint32_t fault_pending;
    uint64_t dispatches;
};

/* Bind once from an all-zero provider.  Failure never invokes dispatch. */
enum mt6897_ufs_provider_result
mt6897_ufs_provider_bind(
    struct mt6897_ufs_provider *provider,
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease,
    const struct mt6897_ufs_provider_ops *ops,
    uint64_t *blockers_out);

enum mt6897_ufs_provider_result
mt6897_ufs_provider_call(
    struct mt6897_ufs_provider *provider,
    enum mt6897_ufs_provider_operation operation,
    const uint64_t argument[4],
    uint64_t *result_out,
    uint64_t *blockers_out);

enum mt6897_ufs_provider_result
mt6897_ufs_provider_fault(
    struct mt6897_ufs_provider *provider,
    uint64_t blocker,
    uint64_t *blockers_out);

enum mt6897_ufs_provider_result
mt6897_ufs_provider_power(struct mt6897_ufs_provider *, uint64_t,
    uint64_t *, uint64_t *);
enum mt6897_ufs_provider_result
mt6897_ufs_provider_clock(struct mt6897_ufs_provider *, uint64_t, uint64_t,
    uint64_t, uint64_t *, uint64_t *);
enum mt6897_ufs_provider_result
mt6897_ufs_provider_phy(struct mt6897_ufs_provider *, uint64_t,
    uint64_t *, uint64_t *);
enum mt6897_ufs_provider_result
mt6897_ufs_provider_mmio(struct mt6897_ufs_provider *, uint64_t, uint64_t,
    uint64_t, uint64_t *, uint64_t *);
enum mt6897_ufs_provider_result
mt6897_ufs_provider_dma(struct mt6897_ufs_provider *, uint64_t, uint64_t,
    uint64_t, uint64_t *, uint64_t *);
enum mt6897_ufs_provider_result
mt6897_ufs_provider_command(struct mt6897_ufs_provider *, uint64_t, uint64_t,
    uint64_t, uint64_t, uint64_t *, uint64_t *);

#endif
