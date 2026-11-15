#ifndef MT6897_UFS_INIT_MODEL_H
#define MT6897_UFS_INIT_MODEL_H

#include "mt6897_ufs_provider.h"

/* Offline model protocol. Requests are not physical-provider operations. */
#define MUI_MODEL_TAG UINT64_C(0x4d55494d4f44454c)
#define MUI_POLL_MAX 4096u
#define MUI_STAGE_MS_MAX 60000u

enum mui_step {
    MUI_RESOURCES, MUI_POWER, MUI_BUS_CLOCKS, MUI_PHY_REFCLK,
    MUI_VERIFY_QUIESCENT, MUI_HOST_RESET, MUI_RECHECK_PHY_REFCLK,
    MUI_DMA, MUI_POLLING_IRQ, MUI_HCE, MUI_UIC_LINK, MUI_VALIDATE_READONLY,
    MUI_STEP_COUNT
};

enum mui_contract {
    MUI_SLOT_B = 1u << 0,
    MUI_COLD_INIT_ALLOWED = 1u << 1,
    MUI_EXCLUSIVE_RESOURCES = 1u << 2,
    MUI_REGISTER_ACCESS = 1u << 3,
    MUI_INHERITED_DMA_SAFE = 1u << 4,
    MUI_READONLY_POLICY = 1u << 5,
    MUI_REQUIRED = 0x3fu
};
enum mui_progress { MUI_PENDING = 0, MUI_COMPLETE = 1 };
enum mui_state { MUI_NEW, MUI_RUNNING, MUI_READY, MUI_STOPPED };
enum mui_result {
    MUI_OK, MUI_BAD_ARGUMENT, MUI_ALREADY_USED, MUI_LEASE_INVALID,
    MUI_CONTRACT_MISSING, MUI_BACKEND_FAILED, MUI_TIMEOUT,
    MUI_CLOCK_FAULT, MUI_BAD_PROGRESS
};

struct mui_ops {
    struct mt6897_ufs_provider_ops backend;
    /* CPU-only checks. The contract is validated against the verified lease
     * and includes ongoing guarantees for any resources already acquired.
     * Neither callback may activate a resource, probe MMIO or run commands.
     */
    uint32_t (*contract)(void *, const struct mt6897_ufs_gate_lease *, enum mui_step);
    uint64_t (*milliseconds)(void *);
    uint32_t timeout_ms;
    uint32_t poll_limit;
};

struct mui_model {
    uint32_t state;
    uint32_t completed_steps;
    enum mui_result result;
    uint64_t blockers;
    /* A dispatched operation might have changed state. Hold all acquired
     * resources and DMA memory until independent evidence proves quiescence.
     */
    uint32_t recovery_required;
};

/* Start from zero once. Publish the resulting report after run has returned.
 * All poll and time callbacks must return. A pending stage may be advanced
 * again but its initiating side effect must not be repeated by the backend.
 * No teardown, retry, I/O submission or physical provider lives here.
 */
enum mui_result mui_run(struct mui_model *, struct mt6897_ufs_gate *,
    const struct mt6897_ufs_gate_lease *, const struct mui_ops *);

#endif
