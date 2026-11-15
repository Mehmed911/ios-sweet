#ifndef MT6897_UFS_INIT_MODEL_TEST
#error "MT6897 UFS initialization model is restricted to offline tests"
#endif

#include "mt6897_ufs_init_model.h"

static const enum mt6897_ufs_provider_operation operation[MUI_STEP_COUNT] = {
    [MUI_RESOURCES] = MT6897_UFS_PROVIDER_POWER,
    [MUI_POWER] = MT6897_UFS_PROVIDER_POWER,
    [MUI_BUS_CLOCKS] = MT6897_UFS_PROVIDER_CLOCK,
    [MUI_PHY_REFCLK] = MT6897_UFS_PROVIDER_PHY,
    [MUI_VERIFY_QUIESCENT] = MT6897_UFS_PROVIDER_MMIO,
    [MUI_HOST_RESET] = MT6897_UFS_PROVIDER_MMIO,
    [MUI_RECHECK_PHY_REFCLK] = MT6897_UFS_PROVIDER_PHY,
    [MUI_DMA] = MT6897_UFS_PROVIDER_DMA,
    [MUI_POLLING_IRQ] = MT6897_UFS_PROVIDER_MMIO,
    [MUI_HCE] = MT6897_UFS_PROVIDER_MMIO,
    [MUI_UIC_LINK] = MT6897_UFS_PROVIDER_MMIO,
    [MUI_VALIDATE_READONLY] = MT6897_UFS_PROVIDER_MMIO,
};

static enum mui_result
verify(struct mui_model *model, struct mt6897_ufs_provider *provider,
    const struct mui_ops *ops, enum mui_step step)
{
    if (mt6897_ufs_gate_lease_check(provider->gate, &provider->lease,
        &model->blockers) != MT6897_UFS_GATE_LEASED)
        return MUI_LEASE_INVALID;
    if (ops->contract(ops->backend.context, &provider->lease, step) != MUI_REQUIRED)
        return MUI_CONTRACT_MISSING;
    return mt6897_ufs_gate_lease_check(provider->gate, &provider->lease,
        &model->blockers) == MT6897_UFS_GATE_LEASED ? MUI_OK : MUI_LEASE_INVALID;
}

static enum mui_result
advance(struct mui_model *model, struct mt6897_ufs_provider *provider,
    const struct mui_ops *ops, enum mui_step step, uint64_t *last_time)
{
    const uint64_t start = *last_time;
    const uint64_t args[4] = { MUI_MODEL_TAG, step, 0, 0 };

    for (uint32_t poll = 0; poll < ops->poll_limit; poll++) {
        enum mui_result status = verify(model, provider, ops, step);
        if (status)
            return status;
        uint64_t now = ops->milliseconds(ops->backend.context);
        if (now < *last_time)
            return MUI_CLOCK_FAULT;
        if (now - start >= ops->timeout_ms)
            return MUI_TIMEOUT;
        *last_time = now;
        /* The first mutable stage is POWER. Quarantine conservatively if
         * an authorized operation may have executed before a failure. */
        if (step >= MUI_POWER)
            model->recovery_required = 1;
        uint64_t progress = 0;
        enum mt6897_ufs_provider_result rc = mt6897_ufs_provider_call(provider,
            operation[step], args, &progress, &model->blockers);
        if (rc != MT6897_UFS_PROVIDER_OK)
            return rc == MT6897_UFS_PROVIDER_CALLBACK ? MUI_BACKEND_FAILED :
                MUI_LEASE_INVALID;
        now = ops->milliseconds(ops->backend.context);
        if (now < *last_time)
            return MUI_CLOCK_FAULT;
        if (now - start >= ops->timeout_ms)
            return MUI_TIMEOUT;
        *last_time = now;
        if (progress == MUI_COMPLETE)
            return MUI_OK;
        if (progress != MUI_PENDING)
            return MUI_BAD_PROGRESS;
    }
    return MUI_TIMEOUT;
}

enum mui_result
mui_run(struct mui_model *model, struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease, const struct mui_ops *ops)
{
    if (!model || !gate || !lease || !ops || !ops->backend.dispatch ||
        !ops->contract || !ops->milliseconds || !ops->timeout_ms ||
        ops->timeout_ms > MUI_STAGE_MS_MAX || !ops->poll_limit ||
        ops->poll_limit > MUI_POLL_MAX)
        return MUI_BAD_ARGUMENT;
    uint32_t state = MUI_NEW;
    if (!__atomic_compare_exchange_n(&model->state, &state, MUI_RUNNING, 0,
        __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE))
        return MUI_ALREADY_USED;

    struct mt6897_ufs_provider provider = {0};
    if (mt6897_ufs_provider_bind(&provider, gate, lease, &ops->backend,
        &model->blockers) != MT6897_UFS_PROVIDER_OK) {
        model->result = MUI_LEASE_INVALID;
    } else {
        uint64_t time = ops->milliseconds(ops->backend.context);
        for (enum mui_step step = MUI_RESOURCES; step < MUI_STEP_COUNT; step++) {
            model->result = advance(model, &provider, ops, step, &time);
            if (model->result)
                break;
            model->completed_steps++;
        }
        if (!model->result)
            model->result = verify(model, &provider, ops, MUI_STEP_COUNT);
        if (model->result)
            (void)mt6897_ufs_provider_fault(&provider,
                MT6897_UFS_BLOCK_PROVIDER_RUNTIME, &model->blockers);
    }
    if (!model->result)
        model->recovery_required = 0;
    __atomic_store_n(&model->state, model->result ? MUI_STOPPED : MUI_READY,
        __ATOMIC_RELEASE);
    return model->result;
}
