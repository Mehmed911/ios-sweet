#include "mt6897_ufs_dma_route.h"

#include <stddef.h>

#ifdef MT6897_UFS_DMA_ROUTE_TEST_HOOKS
extern void mt6897_ufs_dma_route_test_after_lease_check(void);
extern void mt6897_ufs_dma_route_test_before_cpu_owned_publish(void);
#endif

#define DMA_ROUTE_FNV_OFFSET UINT64_C(1469598103934665603)
#define DMA_ROUTE_FNV_PRIME UINT64_C(1099511628211)

/* Monotonic for this kernel boot; zero and UINT64_MAX are terminal. */
static uint64_t dma_route_instance_counter = 1;

static uint64_t
hash_u64(uint64_t hash, uint64_t value)
{
    unsigned index;

    for (index = 0; index < 8; ++index) {
        hash ^= (uint8_t)(value >> (index * 8));
        hash *= DMA_ROUTE_FNV_PRIME;
    }
    return hash;
}

static uint64_t
receipt_fingerprint(const struct mt6897_ufs_dma_route_receipt *receipt)
{
    uint64_t hash = DMA_ROUTE_FNV_OFFSET;

#define HASH_RECEIPT(field) hash = hash_u64(hash, receipt->field)
    HASH_RECEIPT(version);
    HASH_RECEIPT(flags);
    HASH_RECEIPT(route);
    HASH_RECEIPT(bounce_disposition);
    HASH_RECEIPT(boot_generation);
    HASH_RECEIPT(dma_owner_id);
    HASH_RECEIPT(cache_owner_id);
    HASH_RECEIPT(controller_owner_id);
    HASH_RECEIPT(firmware_owner_id);
    HASH_RECEIPT(source_owner_id);
    HASH_RECEIPT(source_cpu_begin);
    HASH_RECEIPT(source_pa_begin);
    HASH_RECEIPT(source_bytes);
    HASH_RECEIPT(device_begin);
    HASH_RECEIPT(device_bytes);
    HASH_RECEIPT(dma_limit);
    HASH_RECEIPT(dma_address_bits);
    HASH_RECEIPT(alignment);
    HASH_RECEIPT(translation_implementation_id);
    HASH_RECEIPT(firewall_receipt_id);
    HASH_RECEIPT(cache_contract_id);
    HASH_RECEIPT(bounce_owner_id);
    HASH_RECEIPT(bounce_cpu_begin);
    HASH_RECEIPT(bounce_pa_begin);
    HASH_RECEIPT(bounce_dma_begin);
    HASH_RECEIPT(bounce_bytes);
    HASH_RECEIPT(copy_to_implementation_id);
    HASH_RECEIPT(copy_from_implementation_id);
#undef HASH_RECEIPT
    return hash;
}

static uint64_t
mapping_fingerprint(const struct mt6897_ufs_dma_route_mapping *mapping,
    uint64_t receipt_hash)
{
    uint64_t hash = hash_u64(DMA_ROUTE_FNV_OFFSET, receipt_hash);

#define HASH_MAPPING(field) hash = hash_u64(hash, mapping->field)
    HASH_MAPPING(source_cpu_address);
    HASH_MAPPING(source_physical_address);
    HASH_MAPPING(dma_cpu_address);
    HASH_MAPPING(dma_physical_address);
    HASH_MAPPING(device_address);
    HASH_MAPPING(bytes);
    HASH_MAPPING(route_instance_id);
    HASH_MAPPING(operation_id);
    HASH_MAPPING(direction);
    HASH_MAPPING(bounced);
#undef HASH_MAPPING
    return hash;
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
copy_receipt(struct mt6897_ufs_dma_route_receipt *destination,
    const struct mt6897_ufs_dma_route_receipt *source)
{
#define COPY_RECEIPT(field) destination->field = source->field
    COPY_RECEIPT(version);
    COPY_RECEIPT(flags);
    COPY_RECEIPT(route);
    COPY_RECEIPT(bounce_disposition);
    COPY_RECEIPT(boot_generation);
    COPY_RECEIPT(dma_owner_id);
    COPY_RECEIPT(cache_owner_id);
    COPY_RECEIPT(controller_owner_id);
    COPY_RECEIPT(firmware_owner_id);
    COPY_RECEIPT(source_owner_id);
    COPY_RECEIPT(source_cpu_begin);
    COPY_RECEIPT(source_pa_begin);
    COPY_RECEIPT(source_bytes);
    COPY_RECEIPT(device_begin);
    COPY_RECEIPT(device_bytes);
    COPY_RECEIPT(dma_limit);
    COPY_RECEIPT(dma_address_bits);
    COPY_RECEIPT(alignment);
    COPY_RECEIPT(translation_implementation_id);
    COPY_RECEIPT(firewall_receipt_id);
    COPY_RECEIPT(cache_contract_id);
    COPY_RECEIPT(bounce_owner_id);
    COPY_RECEIPT(bounce_cpu_begin);
    COPY_RECEIPT(bounce_pa_begin);
    COPY_RECEIPT(bounce_dma_begin);
    COPY_RECEIPT(bounce_bytes);
    COPY_RECEIPT(copy_to_implementation_id);
    COPY_RECEIPT(copy_from_implementation_id);
#undef COPY_RECEIPT
}

static void
copy_ops(struct mt6897_ufs_dma_route_ops *destination,
    const struct mt6897_ufs_dma_route_ops *source)
{
    destination->context = source->context;
    destination->verify = source->verify;
    destination->copy_to_bounce = source->copy_to_bounce;
    destination->copy_from_bounce = source->copy_from_bounce;
}

static void
copy_mapping(struct mt6897_ufs_dma_route_mapping *destination,
    const struct mt6897_ufs_dma_route_mapping *source)
{
    destination->source_cpu_address = source->source_cpu_address;
    destination->source_physical_address = source->source_physical_address;
    destination->dma_cpu_address = source->dma_cpu_address;
    destination->dma_physical_address = source->dma_physical_address;
    destination->device_address = source->device_address;
    destination->bytes = source->bytes;
    destination->route_instance_id = source->route_instance_id;
    destination->operation_id = source->operation_id;
    destination->cookie = source->cookie;
    destination->direction = source->direction;
    destination->bounced = source->bounced;
}

static int
power_of_two(uint64_t value)
{
    return value != 0 && (value & (value - 1)) == 0;
}

static int
allocate_route_instance_id(uint64_t *instance_id)
{
    uint64_t current = __atomic_load_n(&dma_route_instance_counter,
        __ATOMIC_ACQUIRE);

    while (current != 0 && current != UINT64_MAX) {
        uint64_t next = current + 1;

        if (__atomic_compare_exchange_n(&dma_route_instance_counter,
            &current, next, 0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) {
            *instance_id = current;
            return 1;
        }
    }
    *instance_id = 0;
    return 0;
}

static int
range_valid(uint64_t begin, uint64_t bytes)
{
    return bytes != 0 && begin <= UINT64_MAX - (bytes - 1);
}

static int
range_contains(uint64_t outer_begin, uint64_t outer_bytes,
    uint64_t inner_begin, uint64_t inner_bytes)
{
    uint64_t offset;

    if (!range_valid(outer_begin, outer_bytes) ||
        !range_valid(inner_begin, inner_bytes) || inner_begin < outer_begin) {
        return 0;
    }
    offset = inner_begin - outer_begin;
    return offset < outer_bytes && inner_bytes <= outer_bytes - offset;
}

static int
ranges_disjoint(uint64_t left_begin, uint64_t left_bytes,
    uint64_t right_begin, uint64_t right_bytes)
{
    uint64_t left_end;
    uint64_t right_end;

    if (!range_valid(left_begin, left_bytes) ||
        !range_valid(right_begin, right_bytes)) {
        return 0;
    }
    left_end = left_begin + left_bytes - 1;
    right_end = right_begin + right_bytes - 1;
    return left_end < right_begin || right_end < left_begin;
}

static int
address_fits(uint64_t begin, uint64_t bytes, uint64_t limit, uint32_t bits)
{
    uint64_t end;

    if (!range_valid(begin, bytes)) {
        return 0;
    }
    end = begin + bytes - 1;
    if (end > limit || bits == 0 || bits > 64) {
        return 0;
    }
    return bits == 64 || (end >> bits) == 0;
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
receipt_zero(const struct mt6897_ufs_dma_route_receipt *receipt)
{
    return receipt->version == 0 && receipt->flags == 0 &&
        receipt->route == 0 && receipt->bounce_disposition == 0 &&
        receipt->boot_generation == 0 && receipt->dma_owner_id == 0 &&
        receipt->cache_owner_id == 0 && receipt->controller_owner_id == 0 &&
        receipt->firmware_owner_id == 0 && receipt->source_owner_id == 0 &&
        receipt->source_cpu_begin == 0 && receipt->source_pa_begin == 0 &&
        receipt->source_bytes == 0 && receipt->device_begin == 0 &&
        receipt->device_bytes == 0 && receipt->dma_limit == 0 &&
        receipt->dma_address_bits == 0 && receipt->alignment == 0 &&
        receipt->translation_implementation_id == 0 &&
        receipt->firewall_receipt_id == 0 &&
        receipt->cache_contract_id == 0 && receipt->bounce_owner_id == 0 &&
        receipt->bounce_cpu_begin == 0 && receipt->bounce_pa_begin == 0 &&
        receipt->bounce_dma_begin == 0 && receipt->bounce_bytes == 0 &&
        receipt->copy_to_implementation_id == 0 &&
        receipt->copy_from_implementation_id == 0;
}

static int
mapping_zero(const struct mt6897_ufs_dma_route_mapping *mapping)
{
    return mapping->source_cpu_address == 0 &&
        mapping->source_physical_address == 0 &&
        mapping->dma_cpu_address == 0 &&
        mapping->dma_physical_address == 0 &&
        mapping->device_address == 0 && mapping->bytes == 0 &&
        mapping->route_instance_id == 0 && mapping->operation_id == 0 &&
        mapping->cookie == 0 &&
        mapping->direction == 0 &&
        mapping->bounced == 0;
}

static void
mapping_clear(struct mt6897_ufs_dma_route_mapping *mapping)
{
    mapping->source_cpu_address = 0;
    mapping->source_physical_address = 0;
    mapping->dma_cpu_address = 0;
    mapping->dma_physical_address = 0;
    mapping->device_address = 0;
    mapping->bytes = 0;
    mapping->route_instance_id = 0;
    mapping->operation_id = 0;
    mapping->cookie = 0;
    mapping->direction = 0;
    mapping->bounced = 0;
}

static int
route_zero(const struct mt6897_ufs_dma_route *route)
{
    return route != 0 && route->gate == 0 && lease_zero(&route->lease) &&
        receipt_zero(&route->receipt) && route->ops.context == 0 &&
        route->ops.verify == 0 && route->ops.copy_to_bounce == 0 &&
        route->ops.copy_from_bounce == 0 && mapping_zero(&route->active) &&
        route->receipt_fingerprint == 0 && route->route_instance_id == 0 &&
        route->next_operation_id == 0 && route->transitions == 0 &&
        route->state == 0 && route->fault_pending == 0;
}

static int
receipt_valid(const struct mt6897_ufs_dma_route_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease)
{
    uint64_t alignment;

    if (receipt->version != MT6897_UFS_DMA_ROUTE_CONTRACT_VERSION ||
        receipt->boot_generation == 0 ||
        receipt->boot_generation != lease->boot_generation ||
        receipt->dma_owner_id == 0 ||
        receipt->dma_owner_id != lease->dma_owner_id ||
        receipt->cache_owner_id == 0 ||
        receipt->cache_owner_id != lease->cache_owner_id ||
        receipt->controller_owner_id == 0 ||
        receipt->controller_owner_id != lease->controller_owner_id ||
        receipt->firmware_owner_id == 0 ||
        receipt->firmware_owner_id != lease->firmware_owner_id ||
        receipt->source_owner_id == 0 || receipt->source_cpu_begin == 0 ||
        !range_valid(receipt->source_cpu_begin, receipt->source_bytes) ||
        !range_valid(receipt->source_pa_begin, receipt->source_bytes) ||
        receipt->translation_implementation_id == 0 ||
        receipt->firewall_receipt_id == 0 ||
        receipt->cache_contract_id == 0 ||
        receipt->dma_address_bits == 0 ||
        receipt->dma_address_bits > 64) {
        return 0;
    }
    alignment = receipt->alignment;
    if (alignment < 4 || !power_of_two(alignment) ||
        (receipt->source_cpu_begin & (alignment - 1)) != 0 ||
        (receipt->source_pa_begin & (alignment - 1)) != 0 ||
        (receipt->source_bytes & (alignment - 1)) != 0) {
        return 0;
    }
    if (receipt->route == MT6897_UFS_DMA_ROUTE_DIRECT_AFFINE) {
        return receipt->flags == MT6897_UFS_DMA_DIRECT_FLAGS &&
            receipt->bounce_disposition ==
                MT6897_UFS_DMA_BOUNCE_NOT_REQUIRED &&
            receipt->device_bytes == receipt->source_bytes &&
            (receipt->device_begin & (alignment - 1)) == 0 &&
            address_fits(receipt->device_begin, receipt->device_bytes,
                receipt->dma_limit, receipt->dma_address_bits) &&
            receipt->bounce_owner_id == 0 &&
            receipt->bounce_cpu_begin == 0 &&
            receipt->bounce_pa_begin == 0 &&
            receipt->bounce_dma_begin == 0 &&
            receipt->bounce_bytes == 0 &&
            receipt->copy_to_implementation_id == 0 &&
            receipt->copy_from_implementation_id == 0;
    }
    if (receipt->route == MT6897_UFS_DMA_ROUTE_BOUNCE_POOL) {
        return receipt->flags == MT6897_UFS_DMA_BOUNCE_FLAGS &&
            receipt->bounce_disposition == MT6897_UFS_DMA_BOUNCE_REQUIRED &&
            receipt->device_begin == 0 && receipt->device_bytes == 0 &&
            receipt->bounce_owner_id != 0 &&
            receipt->bounce_owner_id != receipt->source_owner_id &&
            receipt->bounce_cpu_begin != 0 &&
            receipt->bounce_bytes >= receipt->source_bytes &&
            range_valid(receipt->bounce_cpu_begin, receipt->bounce_bytes) &&
            range_valid(receipt->bounce_pa_begin, receipt->bounce_bytes) &&
            ranges_disjoint(receipt->source_cpu_begin,
                receipt->source_bytes, receipt->bounce_cpu_begin,
                receipt->bounce_bytes) &&
            ranges_disjoint(receipt->source_pa_begin,
                receipt->source_bytes, receipt->bounce_pa_begin,
                receipt->bounce_bytes) &&
            (receipt->bounce_cpu_begin & (alignment - 1)) == 0 &&
            (receipt->bounce_pa_begin & (alignment - 1)) == 0 &&
            (receipt->bounce_dma_begin & (alignment - 1)) == 0 &&
            (receipt->bounce_bytes & (alignment - 1)) == 0 &&
            address_fits(receipt->bounce_dma_begin, receipt->bounce_bytes,
                receipt->dma_limit, receipt->dma_address_bits) &&
            receipt->copy_to_implementation_id != 0 &&
            receipt->copy_from_implementation_id != 0;
    }
    return 0;
}

static int
direction_valid(uint32_t direction)
{
    return direction == MT6897_UFS_DMA_TO_DEVICE ||
        direction == MT6897_UFS_DMA_FROM_DEVICE ||
        direction == MT6897_UFS_DMA_BIDIRECTIONAL;
}

static int
request_valid(const struct mt6897_ufs_dma_route_receipt *receipt,
    const struct mt6897_ufs_dma_route_request *request)
{
    uint64_t cpu_offset;
    uint64_t pa_offset;
    uint64_t mask = receipt->alignment - 1;

    if (!direction_valid(request->direction) || request->reserved0 != 0 ||
        !range_contains(receipt->source_cpu_begin, receipt->source_bytes,
            request->cpu_address, request->bytes) ||
        !range_contains(receipt->source_pa_begin, receipt->source_bytes,
            request->physical_address, request->bytes) ||
        ((request->cpu_address | request->physical_address |
            request->bytes) & mask) != 0) {
        return 0;
    }
    cpu_offset = request->cpu_address - receipt->source_cpu_begin;
    pa_offset = request->physical_address - receipt->source_pa_begin;
    return cpu_offset == pa_offset &&
        (receipt->route != MT6897_UFS_DMA_ROUTE_BOUNCE_POOL ||
         request->bytes <= receipt->bounce_bytes);
}

static void
make_mapping(const struct mt6897_ufs_dma_route *route,
    const struct mt6897_ufs_dma_route_request *request,
    uint64_t operation_id, struct mt6897_ufs_dma_route_mapping *mapping)
{
    uint64_t offset = request->physical_address -
        route->receipt.source_pa_begin;

    mapping_clear(mapping);
    mapping->source_cpu_address = request->cpu_address;
    mapping->source_physical_address = request->physical_address;
    mapping->bytes = request->bytes;
    mapping->route_instance_id = route->route_instance_id;
    mapping->operation_id = operation_id;
    mapping->direction = request->direction;
    if (route->receipt.route == MT6897_UFS_DMA_ROUTE_DIRECT_AFFINE) {
        mapping->dma_cpu_address = request->cpu_address;
        mapping->dma_physical_address = request->physical_address;
        mapping->device_address = route->receipt.device_begin + offset;
        mapping->bounced = 0;
    } else {
        mapping->dma_cpu_address = route->receipt.bounce_cpu_begin;
        mapping->dma_physical_address = route->receipt.bounce_pa_begin;
        mapping->device_address = route->receipt.bounce_dma_begin;
        mapping->bounced = 1;
    }
    mapping->cookie = mapping_fingerprint(mapping,
        route->receipt_fingerprint);
}

static int
mapping_equal(const struct mt6897_ufs_dma_route_mapping *left,
    const struct mt6897_ufs_dma_route_mapping *right)
{
    return left->source_cpu_address == right->source_cpu_address &&
        left->source_physical_address == right->source_physical_address &&
        left->dma_cpu_address == right->dma_cpu_address &&
        left->dma_physical_address == right->dma_physical_address &&
        left->device_address == right->device_address &&
        left->bytes == right->bytes &&
        left->route_instance_id == right->route_instance_id &&
        left->operation_id == right->operation_id &&
        left->cookie == right->cookie &&
        left->direction == right->direction &&
        left->bounced == right->bounced && left->cookie != 0;
}

static void
state_store(struct mt6897_ufs_dma_route *route,
    enum mt6897_ufs_dma_route_state state)
{
    __atomic_store_n(&route->state, (uint32_t)state, __ATOMIC_RELEASE);
}

static int
state_claim(struct mt6897_ufs_dma_route *route, uint32_t *expected,
    enum mt6897_ufs_dma_route_state desired)
{
    return __atomic_compare_exchange_n(&route->state, expected,
        (uint32_t)desired, 0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE);
}

static uint32_t
fault_load(const struct mt6897_ufs_dma_route *route)
{
    return __atomic_load_n(&route->fault_pending, __ATOMIC_ACQUIRE);
}

static void
fault_store(struct mt6897_ufs_dma_route *route)
{
    __atomic_store_n(&route->fault_pending, 1, __ATOMIC_RELEASE);
}

static enum mt6897_ufs_dma_route_result
route_gate_fault(struct mt6897_ufs_dma_route *route, uint64_t blocker,
    uint64_t *blockers_out)
{
    uint64_t ignored = 0;

    fault_store(route);
    state_store(route, MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
    if (route->gate != 0) {
        (void)mt6897_ufs_gate_fault(route->gate, blocker,
            blockers_out != 0 ? blockers_out : &ignored);
    } else if (blockers_out != 0) {
        *blockers_out = blocker != 0 ? blocker :
            MT6897_UFS_BLOCK_PROVIDER_RUNTIME;
    }
    return MT6897_UFS_DMA_ROUTE_FAULTED;
}

static enum mt6897_ufs_dma_route_result
preflight(struct mt6897_ufs_dma_route *route, uint64_t *blockers_out)
{
    enum mt6897_ufs_gate_result lease_result;

    if (fault_load(route) != 0 || route->gate == 0 ||
        route->ops.verify == 0) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    if (!receipt_valid(&route->receipt, &route->lease) ||
        route->receipt_fingerprint == 0 ||
        receipt_fingerprint(&route->receipt) !=
            route->receipt_fingerprint) {
        return route_gate_fault(route,
            MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT, blockers_out);
    }
    lease_result = mt6897_ufs_gate_lease_check(route->gate, &route->lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED) {
        state_store(route, MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        return MT6897_UFS_DMA_ROUTE_LEASE;
    }
#ifdef MT6897_UFS_DMA_ROUTE_TEST_HOOKS
    mt6897_ufs_dma_route_test_after_lease_check();
#endif
    if (fault_load(route) != 0) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
    }
    if (route->ops.verify(route->ops.context, &route->receipt,
        &route->lease) != 0) {
        (void)route_gate_fault(route, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_DMA_ROUTE_CALLBACK;
    }
    if (!receipt_valid(&route->receipt, &route->lease) ||
        receipt_fingerprint(&route->receipt) !=
            route->receipt_fingerprint) {
        return route_gate_fault(route,
            MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT, blockers_out);
    }
    lease_result = mt6897_ufs_gate_lease_check(route->gate, &route->lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED || fault_load(route) != 0) {
        state_store(route, MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        return MT6897_UFS_DMA_ROUTE_LEASE;
    }
    return MT6897_UFS_DMA_ROUTE_OK;
}

static enum mt6897_ufs_dma_route_result
claim_transition(struct mt6897_ufs_dma_route *route,
    enum mt6897_ufs_dma_route_state expected_state,
    enum mt6897_ufs_dma_route_state transition_state)
{
    uint32_t expected = (uint32_t)expected_state;

    if (!state_claim(route, &expected, transition_state)) {
        if (expected == MT6897_UFS_DMA_ROUTE_STATE_DISABLED) {
            return MT6897_UFS_DMA_ROUTE_DISABLED;
        }
        if (expected == MT6897_UFS_DMA_ROUTE_STATE_FAULTED ||
            fault_load(route) != 0) {
            return MT6897_UFS_DMA_ROUTE_FAULTED;
        }
        return MT6897_UFS_DMA_ROUTE_STATE;
    }
    return MT6897_UFS_DMA_ROUTE_OK;
}

static enum mt6897_ufs_dma_route_result
authorize_callbacks(struct mt6897_ufs_dma_route *route,
    enum mt6897_ufs_dma_route_state checking_state,
    enum mt6897_ufs_dma_route_state dispatch_state, uint64_t *blockers_out)
{
    uint32_t expected;

    if (fault_load(route) != 0) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
    }
    expected = (uint32_t)checking_state;
    if (!state_claim(route, &expected, dispatch_state)) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    return MT6897_UFS_DMA_ROUTE_OK;
}

static enum mt6897_ufs_dma_route_result
finish_transition(struct mt6897_ufs_dma_route *route,
    enum mt6897_ufs_dma_route_state transition_state,
    enum mt6897_ufs_dma_route_state final_state, uint64_t *blockers_out)
{
    enum mt6897_ufs_gate_result lease_result;
    uint32_t expected;

    lease_result = mt6897_ufs_gate_lease_check(route->gate, &route->lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED || fault_load(route) != 0) {
        state_store(route, MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        return MT6897_UFS_DMA_ROUTE_LEASE;
    }
    expected = (uint32_t)transition_state;
    if (!state_claim(route, &expected, final_state)) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    (void)__atomic_fetch_add(&route->transitions, UINT64_C(1),
        __ATOMIC_RELAXED);
    *blockers_out = 0;
    return MT6897_UFS_DMA_ROUTE_OK;
}

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_bind(struct mt6897_ufs_dma_route *route,
    struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease,
    const struct mt6897_ufs_dma_route_receipt *receipt,
    const struct mt6897_ufs_dma_route_ops *ops, uint64_t *blockers_out)
{
    struct mt6897_ufs_gate_lease saved_lease;
    struct mt6897_ufs_dma_route_receipt saved_receipt;
    struct mt6897_ufs_dma_route_ops saved_ops;
    enum mt6897_ufs_gate_result lease_result;
    uint64_t fingerprint;
    uint64_t route_instance_id;

    if (route == 0 || gate == 0 || lease == 0 || receipt == 0 || ops == 0 ||
        ops->verify == 0 || blockers_out == 0) {
        return MT6897_UFS_DMA_ROUTE_ARGUMENT;
    }
    if (!route_zero(route)) {
        return MT6897_UFS_DMA_ROUTE_STATE;
    }
    copy_lease(&saved_lease, lease);
    copy_receipt(&saved_receipt, receipt);
    copy_ops(&saved_ops, ops);
    route->gate = gate;
    copy_lease(&route->lease, &saved_lease);
    lease_result = mt6897_ufs_gate_lease_check(gate, &saved_lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED) {
        state_store(route, MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        return MT6897_UFS_DMA_ROUTE_LEASE;
    }
    if (!receipt_valid(&saved_receipt, &saved_lease) ||
        (saved_receipt.route == MT6897_UFS_DMA_ROUTE_BOUNCE_POOL &&
         (saved_ops.copy_to_bounce == 0 ||
          saved_ops.copy_from_bounce == 0))) {
        (void)route_gate_fault(route,
            MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT, blockers_out);
        return MT6897_UFS_DMA_ROUTE_CONTRACT;
    }
    fingerprint = receipt_fingerprint(&saved_receipt);
    if (fingerprint == 0 || saved_ops.verify(saved_ops.context,
        &saved_receipt, &saved_lease) != 0) {
        (void)route_gate_fault(route, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_DMA_ROUTE_CALLBACK;
    }
    if (!receipt_valid(&saved_receipt, &saved_lease) ||
        receipt_fingerprint(&saved_receipt) != fingerprint) {
        (void)route_gate_fault(route,
            MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT, blockers_out);
        return MT6897_UFS_DMA_ROUTE_CONTRACT;
    }
    lease_result = mt6897_ufs_gate_lease_check(gate, &saved_lease,
        blockers_out);
    if (lease_result != MT6897_UFS_GATE_LEASED) {
        state_store(route, MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        return MT6897_UFS_DMA_ROUTE_LEASE;
    }
    if (!allocate_route_instance_id(&route_instance_id)) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    copy_receipt(&route->receipt, &saved_receipt);
    copy_ops(&route->ops, &saved_ops);
    mapping_clear(&route->active);
    route->receipt_fingerprint = fingerprint;
    route->route_instance_id = route_instance_id;
    route->next_operation_id = 1;
    route->transitions = 0;
    state_store(route, MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED);
    *blockers_out = 0;
    return MT6897_UFS_DMA_ROUTE_OK;
}

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_for_device(struct mt6897_ufs_dma_route *route,
    const struct mt6897_ufs_dma_route_request *request,
    struct mt6897_ufs_dma_route_mapping *mapping_out,
    uint64_t *blockers_out)
{
    struct mt6897_ufs_dma_route_mapping mapping;
    enum mt6897_ufs_dma_route_result result;
    uint64_t operation_id;

    if (route == 0 || request == 0 || mapping_out == 0 ||
        blockers_out == 0) {
        return MT6897_UFS_DMA_ROUTE_ARGUMENT;
    }
    mapping_clear(mapping_out);
    *blockers_out = 0;
    result = claim_transition(route, MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED,
        MT6897_UFS_DMA_ROUTE_STATE_CHECKING_DEVICE);
    if (result != MT6897_UFS_DMA_ROUTE_OK) {
        return result;
    }
    if (!receipt_valid(&route->receipt, &route->lease) ||
        receipt_fingerprint(&route->receipt) !=
            route->receipt_fingerprint) {
        return route_gate_fault(route,
            MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT, blockers_out);
    }
    if (!request_valid(&route->receipt, request)) {
        uint32_t expected = MT6897_UFS_DMA_ROUTE_STATE_CHECKING_DEVICE;
        if (!state_claim(route, &expected,
            MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED)) {
            return route_gate_fault(route, MT6897_UFS_BLOCK_BAD_STATE,
                blockers_out);
        }
        return MT6897_UFS_DMA_ROUTE_RANGE;
    }
    result = preflight(route, blockers_out);
    if (result != MT6897_UFS_DMA_ROUTE_OK) {
        return result;
    }
    result = authorize_callbacks(route,
        MT6897_UFS_DMA_ROUTE_STATE_CHECKING_DEVICE,
        MT6897_UFS_DMA_ROUTE_STATE_TO_DEVICE, blockers_out);
    if (result != MT6897_UFS_DMA_ROUTE_OK) {
        return result;
    }
    operation_id = route->next_operation_id;
    if (operation_id == 0) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    route->next_operation_id = operation_id + 1;
    make_mapping(route, request, operation_id, &mapping);
    if (mapping.cookie == 0) {
        return route_gate_fault(route,
            MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT, blockers_out);
    }
    if (mapping.bounced != 0 &&
        request->direction != MT6897_UFS_DMA_FROM_DEVICE &&
        route->ops.copy_to_bounce(route->ops.context,
            mapping.dma_cpu_address, mapping.source_cpu_address,
            mapping.bytes) != 0) {
        (void)route_gate_fault(route, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_DMA_ROUTE_CALLBACK;
    }
    copy_mapping(&route->active, &mapping);
    result = finish_transition(route, MT6897_UFS_DMA_ROUTE_STATE_TO_DEVICE,
        MT6897_UFS_DMA_ROUTE_STATE_DEVICE_OWNED, blockers_out);
    if (result == MT6897_UFS_DMA_ROUTE_OK) {
        copy_mapping(mapping_out, &mapping);
    }
    return result;
}

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_for_cpu(struct mt6897_ufs_dma_route *route,
    const struct mt6897_ufs_dma_route_mapping *mapping,
    uint64_t *blockers_out)
{
    enum mt6897_ufs_dma_route_result result;

    if (route == 0 || mapping == 0 || blockers_out == 0) {
        return MT6897_UFS_DMA_ROUTE_ARGUMENT;
    }
    *blockers_out = 0;
    result = claim_transition(route, MT6897_UFS_DMA_ROUTE_STATE_DEVICE_OWNED,
        MT6897_UFS_DMA_ROUTE_STATE_CHECKING_CPU);
    if (result != MT6897_UFS_DMA_ROUTE_OK) {
        return result;
    }
    if (!mapping_equal(mapping, &route->active) ||
        mapping->cookie != mapping_fingerprint(mapping,
            route->receipt_fingerprint)) {
        return route_gate_fault(route, MT6897_UFS_BLOCK_BAD_ARGUMENT,
            blockers_out);
    }
    result = preflight(route, blockers_out);
    if (result != MT6897_UFS_DMA_ROUTE_OK) {
        return result;
    }
    result = authorize_callbacks(route,
        MT6897_UFS_DMA_ROUTE_STATE_CHECKING_CPU,
        MT6897_UFS_DMA_ROUTE_STATE_TO_CPU, blockers_out);
    if (result != MT6897_UFS_DMA_ROUTE_OK) {
        return result;
    }
    if (mapping->bounced != 0 &&
        mapping->direction != MT6897_UFS_DMA_TO_DEVICE &&
        route->ops.copy_from_bounce(route->ops.context,
            mapping->source_cpu_address, mapping->dma_cpu_address,
            mapping->bytes) != 0) {
        (void)route_gate_fault(route, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
            blockers_out);
        return MT6897_UFS_DMA_ROUTE_CALLBACK;
    }
    /*
     * Retire the active mapping while TO_CPU still excludes a new device
     * handoff.  Publishing CPU_OWNED first would allow a new operation to
     * install its mapping before this clear, losing the new mapping.
     */
    mapping_clear(&route->active);
#ifdef MT6897_UFS_DMA_ROUTE_TEST_HOOKS
    mt6897_ufs_dma_route_test_before_cpu_owned_publish();
#endif
    result = finish_transition(route, MT6897_UFS_DMA_ROUTE_STATE_TO_CPU,
        MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED, blockers_out);
    return result;
}

enum mt6897_ufs_dma_route_result
mt6897_ufs_dma_route_fault(struct mt6897_ufs_dma_route *route,
    uint64_t blocker, uint64_t *blockers_out)
{
    if (route == 0 || blockers_out == 0) {
        return MT6897_UFS_DMA_ROUTE_ARGUMENT;
    }
    return route_gate_fault(route, blocker, blockers_out);
}
