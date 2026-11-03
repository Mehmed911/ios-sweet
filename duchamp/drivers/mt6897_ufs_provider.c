#include "mt6897_ufs_provider.h"

#ifdef MT6897_UFS_PROVIDER_TEST_HOOKS
extern void mt6897_ufs_provider_test_after_lease_check(void);
#endif

static void
provider_state_store(struct mt6897_ufs_provider *provider,
    enum mt6897_ufs_provider_state state)
{
    __atomic_store_n(&provider->state, (uint32_t)state, __ATOMIC_RELEASE);
}

static int
provider_state_claim(struct mt6897_ufs_provider *provider, uint32_t *expected,
    enum mt6897_ufs_provider_state desired)
{
    return __atomic_compare_exchange_n(&provider->state, expected,
        (uint32_t)desired, 0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE);
}

static uint32_t
provider_fault_load(const struct mt6897_ufs_provider *provider)
{
    return __atomic_load_n(&provider->fault_pending, __ATOMIC_ACQUIRE);
}

static void
provider_fault_store(struct mt6897_ufs_provider *provider)
{
    __atomic_store_n(&provider->fault_pending, 1, __ATOMIC_RELEASE);
}

static int
provider_zero(const struct mt6897_ufs_provider *provider)
{
    const struct mt6897_ufs_gate_lease *lease;

    if (provider == 0) {
        return 0;
    }
    lease = &provider->lease;
    return provider->gate == 0 && provider->ops.context == 0 &&
        provider->ops.dispatch == 0 && provider->state == 0 &&
        provider->fault_pending == 0 && provider->dispatches == 0 &&
        lease->version == 0 && lease->flags == 0 &&
        lease->boot_generation == 0 && lease->evidence_fingerprint == 0 &&
        lease->lease_id == 0 && lease->provider_epoch == 0 &&
        lease->controller_owner_id == 0 && lease->phy_owner_id == 0 &&
        lease->dma_owner_id == 0 && lease->cache_owner_id == 0 &&
        lease->firmware_owner_id == 0;
}

static void
copy_lease(struct mt6897_ufs_gate_lease *destination,
    const struct mt6897_ufs_gate_lease *source)
{
    destination->version = source->version;
    destination->flags = source->flags;
    destination->boot_generation = source->boot_generation;
    destination->evidence_fingerprint = source->evidence_fingerprint;
    destination->lease_id = source->lease_id;
    destination->provider_epoch = source->provider_epoch;
    destination->controller_owner_id = source->controller_owner_id;
    destination->phy_owner_id = source->phy_owner_id;
    destination->dma_owner_id = source->dma_owner_id;
    destination->cache_owner_id = source->cache_owner_id;
    destination->firmware_owner_id = source->firmware_owner_id;
}

static enum mt6897_ufs_provider_result
provider_gate_fault(struct mt6897_ufs_provider *provider, uint64_t blocker,
    uint64_t *blockers_out)
{
    uint64_t ignored = 0;

    provider_fault_store(provider);
    provider_state_store(provider, MT6897_UFS_PROVIDER_STATE_FAULTED);
    if (provider->gate != 0) {
        (void)mt6897_ufs_gate_fault(provider->gate, blocker,
            blockers_out != 0 ? blockers_out : &ignored);
    } else if (blockers_out != 0) {
        *blockers_out = blocker != 0 ? blocker :
            MT6897_UFS_BLOCK_PROVIDER_RUNTIME;
    }
    return MT6897_UFS_PROVIDER_FAULTED;
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_bind(struct mt6897_ufs_provider *provider,
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease,
    const struct mt6897_ufs_provider_ops *ops, uint64_t *blockers_out)
{
    enum mt6897_ufs_gate_result result;

    if (provider == 0 || gate == 0 || lease == 0 || ops == 0 ||
        ops->dispatch == 0 || blockers_out == 0) {
        return MT6897_UFS_PROVIDER_ARGUMENT;
    }
    if (!provider_zero(provider)) {
        return MT6897_UFS_PROVIDER_STATE;
    }
    result = mt6897_ufs_gate_lease_check(gate, lease, blockers_out);
    if (result != MT6897_UFS_GATE_LEASED) {
        provider_state_store(provider, MT6897_UFS_PROVIDER_STATE_FAULTED);
        return MT6897_UFS_PROVIDER_LEASE;
    }
    provider->gate = gate;
    copy_lease(&provider->lease, lease);
    provider->ops = *ops;
    provider->dispatches = 0;
    provider_state_store(provider, MT6897_UFS_PROVIDER_STATE_ACTIVE);
    *blockers_out = 0;
    return MT6897_UFS_PROVIDER_OK;
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_call(struct mt6897_ufs_provider *provider,
    enum mt6897_ufs_provider_operation operation, const uint64_t argument[4],
    uint64_t *result_out, uint64_t *blockers_out)
{
    struct mt6897_ufs_provider_request request;
    enum mt6897_ufs_gate_result lease_result;
    uint32_t expected;
    int callback_result;

    if (provider == 0 || argument == 0 || result_out == 0 ||
        blockers_out == 0 || operation < MT6897_UFS_PROVIDER_POWER ||
        operation >= MT6897_UFS_PROVIDER_OPERATION_COUNT) {
        return MT6897_UFS_PROVIDER_ARGUMENT;
    }
    *result_out = 0;
    *blockers_out = 0;
    expected = (uint32_t)MT6897_UFS_PROVIDER_STATE_ACTIVE;
    if (!provider_state_claim(provider, &expected,
        MT6897_UFS_PROVIDER_STATE_CHECKING)) {
        if (expected == (uint32_t)MT6897_UFS_PROVIDER_STATE_DISABLED) {
            return MT6897_UFS_PROVIDER_DISABLED;
        }
        if (expected == (uint32_t)MT6897_UFS_PROVIDER_STATE_FAULTED ||
            provider_fault_load(provider) != 0) {
            return MT6897_UFS_PROVIDER_FAULTED;
        }
        return MT6897_UFS_PROVIDER_STATE;
    }
    if (provider_fault_load(provider) != 0 || provider->gate == 0 ||
        provider->ops.dispatch == 0) {
        return provider_gate_fault(provider, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    lease_result = mt6897_ufs_gate_lease_check(provider->gate,
        &provider->lease, blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED) {
        provider_state_store(provider, MT6897_UFS_PROVIDER_STATE_FAULTED);
        return MT6897_UFS_PROVIDER_LEASE;
    }
#ifdef MT6897_UFS_PROVIDER_TEST_HOOKS
    mt6897_ufs_provider_test_after_lease_check();
#endif
    if (provider_fault_load(provider) != 0) {
        return provider_gate_fault(provider, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
    }
    expected = (uint32_t)MT6897_UFS_PROVIDER_STATE_CHECKING;
    if (!provider_state_claim(provider, &expected,
        MT6897_UFS_PROVIDER_STATE_DISPATCHING)) {
        return provider_gate_fault(provider, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    request.version = MT6897_UFS_PROVIDER_REQUEST_VERSION;
    request.operation = (uint32_t)operation;
    request.argument[0] = argument[0];
    request.argument[1] = argument[1];
    request.argument[2] = argument[2];
    request.argument[3] = argument[3];
    callback_result = provider->ops.dispatch(provider->ops.context, &request,
        result_out);
    __atomic_fetch_add(&provider->dispatches, UINT64_C(1), __ATOMIC_RELAXED);
    if (callback_result != 0) {
        (void)provider_gate_fault(provider,
            MT6897_UFS_BLOCK_PROVIDER_RUNTIME, blockers_out);
        return MT6897_UFS_PROVIDER_CALLBACK;
    }
    lease_result = mt6897_ufs_gate_lease_check(provider->gate,
        &provider->lease, blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED ||
        provider_fault_load(provider) != 0) {
        provider_state_store(provider, MT6897_UFS_PROVIDER_STATE_FAULTED);
        return MT6897_UFS_PROVIDER_LEASE;
    }
    expected = (uint32_t)MT6897_UFS_PROVIDER_STATE_DISPATCHING;
    if (!provider_state_claim(provider, &expected,
        MT6897_UFS_PROVIDER_STATE_ACTIVE)) {
        return provider_gate_fault(provider, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    *blockers_out = 0;
    return MT6897_UFS_PROVIDER_OK;
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_fault(struct mt6897_ufs_provider *provider,
    uint64_t blocker, uint64_t *blockers_out)
{
    if (provider == 0 || blockers_out == 0) {
        return MT6897_UFS_PROVIDER_ARGUMENT;
    }
    return provider_gate_fault(provider, blocker, blockers_out);
}

static enum mt6897_ufs_provider_result
provider_simple_call(struct mt6897_ufs_provider *provider,
    enum mt6897_ufs_provider_operation operation, uint64_t a0, uint64_t a1,
    uint64_t a2, uint64_t a3, uint64_t *result_out, uint64_t *blockers_out)
{
    const uint64_t argument[4] = { a0, a1, a2, a3 };

    return mt6897_ufs_provider_call(provider, operation, argument, result_out,
        blockers_out);
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_power(struct mt6897_ufs_provider *provider, uint64_t action,
    uint64_t *result_out, uint64_t *blockers_out)
{
    return provider_simple_call(provider, MT6897_UFS_PROVIDER_POWER, action,
        0, 0, 0, result_out, blockers_out);
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_clock(struct mt6897_ufs_provider *provider, uint64_t bank,
    uint64_t clock, uint64_t action, uint64_t *result_out,
    uint64_t *blockers_out)
{
    return provider_simple_call(provider, MT6897_UFS_PROVIDER_CLOCK, bank,
        clock, action, 0, result_out, blockers_out);
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_phy(struct mt6897_ufs_provider *provider, uint64_t action,
    uint64_t *result_out, uint64_t *blockers_out)
{
    return provider_simple_call(provider, MT6897_UFS_PROVIDER_PHY, action,
        0, 0, 0, result_out, blockers_out);
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_mmio(struct mt6897_ufs_provider *provider, uint64_t action,
    uint64_t offset, uint64_t value, uint64_t *result_out,
    uint64_t *blockers_out)
{
    return provider_simple_call(provider, MT6897_UFS_PROVIDER_MMIO, action,
        offset, value, 0, result_out, blockers_out);
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_dma(struct mt6897_ufs_provider *provider, uint64_t action,
    uint64_t address, uint64_t bytes, uint64_t *result_out,
    uint64_t *blockers_out)
{
    return provider_simple_call(provider, MT6897_UFS_PROVIDER_DMA, action,
        address, bytes, 0, result_out, blockers_out);
}

enum mt6897_ufs_provider_result
mt6897_ufs_provider_command(struct mt6897_ufs_provider *provider,
    uint64_t opcode, uint64_t lun, uint64_t lba, uint64_t blocks,
    uint64_t *result_out, uint64_t *blockers_out)
{
    return provider_simple_call(provider, MT6897_UFS_PROVIDER_COMMAND,
        opcode, lun, lba, blocks, result_out, blockers_out);
}
