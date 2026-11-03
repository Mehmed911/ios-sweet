#include "mt6897_ufs_cache.h"

#include <stddef.h>

#ifdef MT6897_UFS_CACHE_TEST_HOOKS
extern void mt6897_ufs_cache_test_after_lease_check(void);
#endif

#define MT6897_UFS_CACHE_FNV_OFFSET UINT64_C(1469598103934665603)
#define MT6897_UFS_CACHE_FNV_PRIME UINT64_C(1099511628211)

static void
cache_state_store(struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_state state)
{
    __atomic_store_n(&cache->state, (uint32_t)state, __ATOMIC_RELEASE);
}

static int
cache_state_claim(struct mt6897_ufs_cache *cache, uint32_t *expected,
    enum mt6897_ufs_cache_state desired)
{
    return __atomic_compare_exchange_n(&cache->state, expected,
        (uint32_t)desired, 0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE);
}

static uint32_t
cache_fault_load(const struct mt6897_ufs_cache *cache)
{
    return __atomic_load_n(&cache->fault_pending, __ATOMIC_ACQUIRE);
}

static void
cache_fault_store(struct mt6897_ufs_cache *cache)
{
    __atomic_store_n(&cache->fault_pending, 1, __ATOMIC_RELEASE);
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

static void
copy_receipt(struct mt6897_ufs_cache_receipt *destination,
    const struct mt6897_ufs_cache_receipt *source)
{
    destination->version = source->version;
    destination->flags = source->flags;
    destination->boot_generation = source->boot_generation;
    destination->cache_owner_id = source->cache_owner_id;
    destination->range_owner_id = source->range_owner_id;
    destination->cpu_address = source->cpu_address;
    destination->physical_address = source->physical_address;
    destination->bytes = source->bytes;
    destination->cache_line_size = source->cache_line_size;
    destination->reserved0 = source->reserved0;
    destination->clean_implementation_id = source->clean_implementation_id;
    destination->flush_implementation_id = source->flush_implementation_id;
    destination->barrier_implementation_id = source->barrier_implementation_id;
}

static int
lease_zero(const struct mt6897_ufs_gate_lease *lease)
{
    return lease->version == 0 && lease->flags == 0 &&
        lease->boot_generation == 0 && lease->evidence_fingerprint == 0 &&
        lease->lease_id == 0 && lease->provider_epoch == 0 &&
        lease->controller_owner_id == 0 && lease->phy_owner_id == 0 &&
        lease->dma_owner_id == 0 && lease->cache_owner_id == 0 &&
        lease->firmware_owner_id == 0;
}

static int
receipt_zero(const struct mt6897_ufs_cache_receipt *receipt)
{
    return receipt->version == 0 && receipt->flags == 0 &&
        receipt->boot_generation == 0 && receipt->cache_owner_id == 0 &&
        receipt->range_owner_id == 0 && receipt->cpu_address == 0 &&
        receipt->physical_address == 0 && receipt->bytes == 0 &&
        receipt->cache_line_size == 0 && receipt->reserved0 == 0 &&
        receipt->clean_implementation_id == 0 &&
        receipt->flush_implementation_id == 0 &&
        receipt->barrier_implementation_id == 0;
}

static int
cache_zero(const struct mt6897_ufs_cache *cache)
{
    if (cache == 0) {
        return 0;
    }
    return cache->gate == 0 && lease_zero(&cache->lease) &&
        receipt_zero(&cache->receipt) && cache->ops.context == 0 &&
        cache->ops.verify == 0 && cache->ops.clean_to_poc == 0 &&
        cache->ops.flush_to_poc == 0 && cache->ops.barrier == 0 &&
        cache->receipt_fingerprint == 0 && cache->transitions == 0 &&
        cache->state == 0 && cache->fault_pending == 0;
}

static uint64_t
hash_u64(uint64_t hash, uint64_t value)
{
    unsigned index;

    for (index = 0; index < 8; ++index) {
        hash ^= (uint8_t)(value >> (index * 8));
        hash *= MT6897_UFS_CACHE_FNV_PRIME;
    }
    return hash;
}

static uint64_t
receipt_fingerprint(const struct mt6897_ufs_cache_receipt *receipt)
{
    uint64_t hash = MT6897_UFS_CACHE_FNV_OFFSET;

    hash = hash_u64(hash, receipt->version);
    hash = hash_u64(hash, receipt->flags);
    hash = hash_u64(hash, receipt->boot_generation);
    hash = hash_u64(hash, receipt->cache_owner_id);
    hash = hash_u64(hash, receipt->range_owner_id);
    hash = hash_u64(hash, receipt->cpu_address);
    hash = hash_u64(hash, receipt->physical_address);
    hash = hash_u64(hash, receipt->bytes);
    hash = hash_u64(hash, receipt->cache_line_size);
    hash = hash_u64(hash, receipt->reserved0);
    hash = hash_u64(hash, receipt->clean_implementation_id);
    hash = hash_u64(hash, receipt->flush_implementation_id);
    hash = hash_u64(hash, receipt->barrier_implementation_id);
    return hash;
}

static int
receipt_valid(const struct mt6897_ufs_cache_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease)
{
    uint64_t line;

    if (receipt->version != MT6897_UFS_CACHE_CONTRACT_VERSION ||
        receipt->flags != MT6897_UFS_CACHE_REQUIRED_FLAGS ||
        receipt->boot_generation == 0 ||
        receipt->boot_generation != lease->boot_generation ||
        receipt->cache_owner_id == 0 ||
        receipt->cache_owner_id != lease->cache_owner_id ||
        receipt->range_owner_id == 0 || receipt->cpu_address == 0 ||
        receipt->bytes == 0 || receipt->reserved0 != 0 ||
        receipt->clean_implementation_id == 0 ||
        receipt->flush_implementation_id == 0 ||
        receipt->barrier_implementation_id == 0) {
        return 0;
    }
    line = receipt->cache_line_size;
    if (line < 16 || line > 2048 || (line & (line - 1)) != 0 ||
        (receipt->cpu_address & (line - 1)) != 0 ||
        (receipt->physical_address & (line - 1)) != 0 ||
        (receipt->bytes & (line - 1)) != 0 ||
        receipt->cpu_address > UINT64_MAX - (receipt->bytes - 1) ||
        receipt->physical_address > UINT64_MAX - (receipt->bytes - 1)) {
        return 0;
    }
    return 1;
}

static int
direction_valid(enum mt6897_ufs_cache_direction direction)
{
    return direction == MT6897_UFS_CACHE_TO_DEVICE ||
        direction == MT6897_UFS_CACHE_FROM_DEVICE ||
        direction == MT6897_UFS_CACHE_BIDIRECTIONAL;
}

static enum mt6897_ufs_cache_result
cache_gate_fault(struct mt6897_ufs_cache *cache, uint64_t blocker,
    uint64_t *blockers_out)
{
    uint64_t ignored = 0;

    cache_fault_store(cache);
    cache_state_store(cache, MT6897_UFS_CACHE_STATE_FAULTED);
    if (cache->gate != 0) {
        (void)mt6897_ufs_gate_fault(cache->gate, blocker,
            blockers_out != 0 ? blockers_out : &ignored);
    } else if (blockers_out != 0) {
        *blockers_out = blocker != 0 ? blocker :
            MT6897_UFS_BLOCK_PROVIDER_RUNTIME;
    }
    return MT6897_UFS_CACHE_FAULTED;
}

static enum mt6897_ufs_cache_result
cache_preflight(struct mt6897_ufs_cache *cache, uint64_t *blockers_out)
{
    enum mt6897_ufs_gate_result lease_result;

    if (cache_fault_load(cache) != 0 || cache->gate == 0 ||
        cache->ops.verify == 0 || cache->ops.clean_to_poc == 0 ||
        cache->ops.flush_to_poc == 0 || cache->ops.barrier == 0) {
        return cache_gate_fault(cache, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    if (!receipt_valid(&cache->receipt, &cache->lease) ||
        cache->receipt_fingerprint == 0 ||
        receipt_fingerprint(&cache->receipt) != cache->receipt_fingerprint) {
        return cache_gate_fault(cache, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT,
            blockers_out);
    }
    lease_result = mt6897_ufs_gate_lease_check(cache->gate, &cache->lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED) {
        cache_state_store(cache, MT6897_UFS_CACHE_STATE_FAULTED);
        return MT6897_UFS_CACHE_LEASE;
    }
#ifdef MT6897_UFS_CACHE_TEST_HOOKS
    mt6897_ufs_cache_test_after_lease_check();
#endif
    if (cache_fault_load(cache) != 0) {
        return cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
    }
    if (cache->ops.verify(cache->ops.context, &cache->receipt,
        &cache->lease) != 0) {
        (void)cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_CACHE_CALLBACK;
    }
    if (!receipt_valid(&cache->receipt, &cache->lease) ||
        receipt_fingerprint(&cache->receipt) != cache->receipt_fingerprint) {
        return cache_gate_fault(cache, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT,
            blockers_out);
    }
    lease_result = mt6897_ufs_gate_lease_check(cache->gate, &cache->lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED ||
        cache_fault_load(cache) != 0) {
        cache_state_store(cache, MT6897_UFS_CACHE_STATE_FAULTED);
        return MT6897_UFS_CACHE_LEASE;
    }
    return MT6897_UFS_CACHE_OK;
}

static enum mt6897_ufs_cache_result
claim_transition(struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_state expected_state,
    enum mt6897_ufs_cache_state transition_state)
{
    uint32_t expected = (uint32_t)expected_state;

    if (!cache_state_claim(cache, &expected, transition_state)) {
        if (expected == (uint32_t)MT6897_UFS_CACHE_STATE_DISABLED) {
            return MT6897_UFS_CACHE_DISABLED;
        }
        if (expected == (uint32_t)MT6897_UFS_CACHE_STATE_FAULTED ||
            cache_fault_load(cache) != 0) {
            return MT6897_UFS_CACHE_FAULTED;
        }
        return MT6897_UFS_CACHE_STATE;
    }
    return MT6897_UFS_CACHE_OK;
}

static enum mt6897_ufs_cache_result
finish_transition(struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_state transition_state,
    enum mt6897_ufs_cache_state final_state, uint64_t *blockers_out)
{
    enum mt6897_ufs_gate_result lease_result;
    uint32_t expected;

    lease_result = mt6897_ufs_gate_lease_check(cache->gate, &cache->lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED ||
        cache_fault_load(cache) != 0) {
        cache_state_store(cache, MT6897_UFS_CACHE_STATE_FAULTED);
        return MT6897_UFS_CACHE_LEASE;
    }
    expected = (uint32_t)transition_state;
    if (!cache_state_claim(cache, &expected, final_state)) {
        return cache_gate_fault(cache, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    (void)__atomic_fetch_add(&cache->transitions, UINT64_C(1),
        __ATOMIC_RELAXED);
    *blockers_out = 0;
    return MT6897_UFS_CACHE_OK;
}

static enum mt6897_ufs_cache_result
authorize_callbacks(struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_state checking_state,
    enum mt6897_ufs_cache_state dispatch_state, uint64_t *blockers_out)
{
    uint32_t expected;

    if (cache_fault_load(cache) != 0) {
        return cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
    }
    expected = (uint32_t)checking_state;
    if (!cache_state_claim(cache, &expected, dispatch_state)) {
        return cache_gate_fault(cache, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    return MT6897_UFS_CACHE_OK;
}

enum mt6897_ufs_cache_result
mt6897_ufs_cache_bind(struct mt6897_ufs_cache *cache,
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease,
    const struct mt6897_ufs_cache_receipt *receipt,
    const struct mt6897_ufs_cache_ops *ops, uint64_t *blockers_out)
{
    struct mt6897_ufs_gate_lease saved_lease;
    struct mt6897_ufs_cache_receipt saved_receipt;
    enum mt6897_ufs_gate_result lease_result;
    uint64_t fingerprint;

    if (cache == 0 || gate == 0 || lease == 0 || receipt == 0 || ops == 0 ||
        ops->verify == 0 || ops->clean_to_poc == 0 ||
        ops->flush_to_poc == 0 || ops->barrier == 0 || blockers_out == 0) {
        return MT6897_UFS_CACHE_ARGUMENT;
    }
    if (!cache_zero(cache)) {
        return MT6897_UFS_CACHE_STATE;
    }
    copy_lease(&saved_lease, lease);
    copy_receipt(&saved_receipt, receipt);
    cache->gate = gate;
    copy_lease(&cache->lease, &saved_lease);
    lease_result = mt6897_ufs_gate_lease_check(gate, &saved_lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED) {
        cache_state_store(cache, MT6897_UFS_CACHE_STATE_FAULTED);
        return MT6897_UFS_CACHE_LEASE;
    }
    if (!receipt_valid(&saved_receipt, &saved_lease)) {
        (void)cache_gate_fault(cache, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT,
            blockers_out);
        return MT6897_UFS_CACHE_CONTRACT;
    }
    fingerprint = receipt_fingerprint(&saved_receipt);
    if (fingerprint == 0 ||
        ops->verify(ops->context, &saved_receipt, &saved_lease) != 0) {
        (void)cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_CACHE_CALLBACK;
    }
    lease_result = mt6897_ufs_gate_lease_check(gate, &saved_lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED) {
        cache_state_store(cache, MT6897_UFS_CACHE_STATE_FAULTED);
        return MT6897_UFS_CACHE_LEASE;
    }
    copy_receipt(&cache->receipt, &saved_receipt);
    cache->ops = *ops;
    cache->receipt_fingerprint = fingerprint;
    cache->transitions = 0;
    cache_state_store(cache, MT6897_UFS_CACHE_STATE_CPU_OWNED);
    *blockers_out = 0;
    return MT6897_UFS_CACHE_OK;
}

enum mt6897_ufs_cache_result
mt6897_ufs_cache_for_device(struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_direction direction, uint64_t *blockers_out)
{
    enum mt6897_ufs_cache_result result;

    if (cache == 0 || blockers_out == 0 || !direction_valid(direction)) {
        return MT6897_UFS_CACHE_ARGUMENT;
    }
    *blockers_out = 0;
    result = claim_transition(cache, MT6897_UFS_CACHE_STATE_CPU_OWNED,
        MT6897_UFS_CACHE_STATE_CHECKING_DEVICE);
    if (result != MT6897_UFS_CACHE_OK) {
        return result;
    }
    result = cache_preflight(cache, blockers_out);
    if (result != MT6897_UFS_CACHE_OK) {
        return result;
    }
    result = authorize_callbacks(cache,
        MT6897_UFS_CACHE_STATE_CHECKING_DEVICE,
        MT6897_UFS_CACHE_STATE_TO_DEVICE, blockers_out);
    if (result != MT6897_UFS_CACHE_OK) {
        return result;
    }
    if (cache->ops.clean_to_poc(cache->ops.context,
            cache->receipt.cpu_address, cache->receipt.physical_address,
            cache->receipt.bytes, direction) != 0 ||
        cache->ops.barrier(cache->ops.context,
            MT6897_UFS_CACHE_BARRIER_TO_DEVICE, direction) != 0) {
        (void)cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_CACHE_CALLBACK;
    }
    return finish_transition(cache, MT6897_UFS_CACHE_STATE_TO_DEVICE,
        MT6897_UFS_CACHE_STATE_DEVICE_OWNED, blockers_out);
}

enum mt6897_ufs_cache_result
mt6897_ufs_cache_for_cpu(struct mt6897_ufs_cache *cache,
    enum mt6897_ufs_cache_direction direction, uint64_t *blockers_out)
{
    enum mt6897_ufs_cache_result result;

    if (cache == 0 || blockers_out == 0 || !direction_valid(direction)) {
        return MT6897_UFS_CACHE_ARGUMENT;
    }
    *blockers_out = 0;
    result = claim_transition(cache, MT6897_UFS_CACHE_STATE_DEVICE_OWNED,
        MT6897_UFS_CACHE_STATE_CHECKING_CPU);
    if (result != MT6897_UFS_CACHE_OK) {
        return result;
    }
    result = cache_preflight(cache, blockers_out);
    if (result != MT6897_UFS_CACHE_OK) {
        return result;
    }
    result = authorize_callbacks(cache, MT6897_UFS_CACHE_STATE_CHECKING_CPU,
        MT6897_UFS_CACHE_STATE_TO_CPU, blockers_out);
    if (result != MT6897_UFS_CACHE_OK) {
        return result;
    }
    if (cache->ops.barrier(cache->ops.context,
            MT6897_UFS_CACHE_BARRIER_BEFORE_CPU, direction) != 0) {
        (void)cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_CACHE_CALLBACK;
    }
    if (direction != MT6897_UFS_CACHE_TO_DEVICE &&
        cache->ops.flush_to_poc(cache->ops.context,
            cache->receipt.cpu_address, cache->receipt.physical_address,
            cache->receipt.bytes, direction) != 0) {
        (void)cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_CACHE_CALLBACK;
    }
    if (cache->ops.barrier(cache->ops.context,
            MT6897_UFS_CACHE_BARRIER_AFTER_CPU, direction) != 0) {
        (void)cache_gate_fault(cache, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_CACHE_CALLBACK;
    }
    return finish_transition(cache, MT6897_UFS_CACHE_STATE_TO_CPU,
        MT6897_UFS_CACHE_STATE_CPU_OWNED, blockers_out);
}

enum mt6897_ufs_cache_result
mt6897_ufs_cache_fault(struct mt6897_ufs_cache *cache, uint64_t blocker,
    uint64_t *blockers_out)
{
    if (cache == 0 || blockers_out == 0) {
        return MT6897_UFS_CACHE_ARGUMENT;
    }
    return cache_gate_fault(cache, blocker, blockers_out);
}
