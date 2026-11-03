#include "mt6897_ufs_cache.h"

#include <stddef.h>

#ifdef MT6897_MODEL_FREESTANDING
extern void model_assert_fail(const char *, unsigned);
extern int printf(const char *, ...);
#define TEST_FAIL(expression, line) model_assert_fail((expression), (line))
#else
#include <stdio.h>
#include <stdlib.h>
static void
native_fail(const char *expression, unsigned line)
{
    (void)fprintf(stderr, "line %u: check failed: %s\n", line, expression);
    abort();
}
#define TEST_FAIL(expression, line) native_fail((expression), (line))
#endif

static unsigned checks;
#define CHECK(expression) do { \
    ++checks; \
    if (!(expression)) { \
        TEST_FAIL(#expression, __LINE__); \
    } \
} while (0)

#define BOOT_GENERATION UINT64_C(0x202611030201)

enum event_kind {
    EVENT_VERIFY = 1,
    EVENT_CLEAN = 2,
    EVENT_FLUSH = 3,
    EVENT_BARRIER_TO_DEVICE = 4,
    EVENT_BARRIER_BEFORE_CPU = 5,
    EVENT_BARRIER_AFTER_CPU = 6
};

struct cache_event {
    unsigned kind;
    unsigned direction;
    uint64_t cpu;
    uint64_t physical;
    uint64_t bytes;
};

struct cache_model {
    struct cache_event events[64];
    unsigned count;
    unsigned fail_kind;
    unsigned char device[256];
};

_Alignas(64) static unsigned char cpu_buffer[256];

static void
record_event(struct cache_model *model, unsigned kind,
    enum mt6897_ufs_cache_direction direction, uint64_t cpu,
    uint64_t physical, uint64_t bytes)
{
    CHECK(model->count < 64);
    model->events[model->count].kind = kind;
    model->events[model->count].direction = (unsigned)direction;
    model->events[model->count].cpu = cpu;
    model->events[model->count].physical = physical;
    model->events[model->count].bytes = bytes;
    ++model->count;
}

static void
make_valid_lease(const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    lease->version = MT6897_UFS_GATE_LEASE_VERSION;
    lease->flags = MT6897_UFS_LEASE_REQUIRED_FLAGS;
    lease->boot_generation = request->evidence.boot_generation;
    lease->evidence_fingerprint = request->evidence_fingerprint;
    lease->lease_id = UINT64_C(0x1101);
    lease->provider_epoch = UINT64_C(0x2202);
    lease->controller_owner_id = UINT64_C(0x3303);
    lease->phy_owner_id = UINT64_C(0x4404);
    lease->dma_owner_id = UINT64_C(0x5505);
    lease->cache_owner_id = UINT64_C(0x6606);
    lease->firmware_owner_id = UINT64_C(0x7707);
}

static enum mt6897_ufs_gate_verdict
approve_lease(void *context,
    const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    unsigned *calls = (unsigned *)context;

    ++*calls;
    make_valid_lease(request, lease);
    return MT6897_UFS_GATE_VERIFY_APPROVE;
}

static enum mt6897_ufs_gate_verdict
unreachable_lease(void *context,
    const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    unsigned *calls = (unsigned *)context;

    (void)request;
    (void)lease;
    ++*calls;
    return MT6897_UFS_GATE_VERIFY_FAULT;
}

static struct mt6897_ufs_gate_evidence
complete_evidence(void)
{
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);

    evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED |
        MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    evidence.known = evidence.asserted;
    return evidence;
}

static struct mt6897_ufs_cache_receipt
valid_receipt(const struct mt6897_ufs_gate_lease *lease)
{
    struct mt6897_ufs_cache_receipt receipt = { 0 };

    receipt.version = MT6897_UFS_CACHE_CONTRACT_VERSION;
    receipt.flags = MT6897_UFS_CACHE_REQUIRED_FLAGS;
    receipt.boot_generation = lease->boot_generation;
    receipt.cache_owner_id = lease->cache_owner_id;
    receipt.range_owner_id = UINT64_C(0x8808);
    receipt.cpu_address = (uint64_t)(uintptr_t)cpu_buffer;
    receipt.physical_address = UINT64_C(0x100000000);
    receipt.bytes = sizeof(cpu_buffer);
    receipt.cache_line_size = 64;
    receipt.clean_implementation_id = UINT64_C(0xc1ea0001);
    receipt.flush_implementation_id = UINT64_C(0xf1050002);
    receipt.barrier_implementation_id = UINT64_C(0xba220003);
    return receipt;
}

static int
cache_verify(void *context, const struct mt6897_ufs_cache_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease)
{
    struct cache_model *model = (struct cache_model *)context;

    CHECK(receipt->version == MT6897_UFS_CACHE_CONTRACT_VERSION);
    CHECK(receipt->flags == MT6897_UFS_CACHE_REQUIRED_FLAGS);
    CHECK(receipt->boot_generation == lease->boot_generation);
    CHECK(receipt->cache_owner_id == lease->cache_owner_id);
    record_event(model, EVENT_VERIFY, MT6897_UFS_CACHE_TO_DEVICE,
        receipt->cpu_address, receipt->physical_address, receipt->bytes);
    return model->fail_kind == EVENT_VERIFY ? -1 : 0;
}

static int
cache_clean(void *context, uint64_t cpu, uint64_t physical, uint64_t bytes,
    enum mt6897_ufs_cache_direction direction)
{
    struct cache_model *model = (struct cache_model *)context;
    unsigned index;

    CHECK(cpu == (uint64_t)(uintptr_t)cpu_buffer);
    CHECK(physical == UINT64_C(0x100000000));
    CHECK(bytes == sizeof(cpu_buffer));
    record_event(model, EVENT_CLEAN, direction, cpu, physical, bytes);
    if (model->fail_kind == EVENT_CLEAN) {
        return -1;
    }
    for (index = 0; index < sizeof(cpu_buffer); ++index) {
        model->device[index] = cpu_buffer[index];
    }
    return 0;
}

static int
cache_flush(void *context, uint64_t cpu, uint64_t physical, uint64_t bytes,
    enum mt6897_ufs_cache_direction direction)
{
    struct cache_model *model = (struct cache_model *)context;
    unsigned index;

    CHECK(cpu == (uint64_t)(uintptr_t)cpu_buffer);
    CHECK(physical == UINT64_C(0x100000000));
    CHECK(bytes == sizeof(cpu_buffer));
    record_event(model, EVENT_FLUSH, direction, cpu, physical, bytes);
    if (model->fail_kind == EVENT_FLUSH) {
        return -1;
    }
    for (index = 0; index < sizeof(cpu_buffer); ++index) {
        cpu_buffer[index] = model->device[index];
    }
    return 0;
}

static int
cache_barrier(void *context, enum mt6897_ufs_cache_barrier_phase phase,
    enum mt6897_ufs_cache_direction direction)
{
    struct cache_model *model = (struct cache_model *)context;
    unsigned event;

    if (phase == MT6897_UFS_CACHE_BARRIER_TO_DEVICE) {
        event = EVENT_BARRIER_TO_DEVICE;
    } else if (phase == MT6897_UFS_CACHE_BARRIER_BEFORE_CPU) {
        event = EVENT_BARRIER_BEFORE_CPU;
    } else {
        CHECK(phase == MT6897_UFS_CACHE_BARRIER_AFTER_CPU);
        event = EVENT_BARRIER_AFTER_CPU;
    }
    record_event(model, event, direction, 0, 0, 0);
    return model->fail_kind == event ? -1 : 0;
}

static struct mt6897_ufs_cache_ops
cache_ops(struct cache_model *model)
{
    struct mt6897_ufs_cache_ops ops = {
        model, cache_verify, cache_clean, cache_flush, cache_barrier
    };

    return ops;
}

static void
authorize_gate(struct mt6897_ufs_gate *gate,
    struct mt6897_ufs_gate_lease *lease)
{
    struct mt6897_ufs_gate_evidence evidence = complete_evidence();
    uint64_t blockers = UINT64_MAX;
    unsigned verifier_calls = 0;

    CHECK(mt6897_ufs_gate_init(gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(gate, &evidence, approve_lease,
        &verifier_calls, lease, &blockers) == MT6897_UFS_GATE_LEASED);
    CHECK(verifier_calls == 1);
    CHECK(blockers == 0);
}

static void
bind_cache(struct mt6897_ufs_gate *gate,
    struct mt6897_ufs_gate_lease *lease, struct mt6897_ufs_cache *cache,
    struct cache_model *model)
{
    struct mt6897_ufs_cache_receipt receipt;
    struct mt6897_ufs_cache_ops ops = cache_ops(model);
    uint64_t blockers = UINT64_MAX;

    authorize_gate(gate, lease);
    receipt = valid_receipt(lease);
    CHECK(mt6897_ufs_cache_bind(cache, gate, lease, &receipt, &ops,
        &blockers) == MT6897_UFS_CACHE_OK);
    CHECK(cache->state == MT6897_UFS_CACHE_STATE_CPU_OWNED);
    CHECK(cache->transitions == 0);
    CHECK(blockers == 0);
}

static void
test_default_closed(unsigned *current_callbacks)
{
    struct mt6897_ufs_cache zero = { 0 };
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct mt6897_ufs_cache cache = { 0 };
    struct mt6897_ufs_cache_receipt receipt = { 0 };
    struct cache_model model = { 0 };
    struct mt6897_ufs_cache_ops ops = cache_ops(&model);
    uint64_t blockers = 0;
    unsigned verifier_calls = 0;

    CHECK(mt6897_ufs_cache_for_device(&zero,
        MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
        MT6897_UFS_CACHE_DISABLED);
    CHECK(mt6897_ufs_cache_for_cpu(&zero,
        MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
        MT6897_UFS_CACHE_DISABLED);
    CHECK(model.count == 0);

    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, unreachable_lease,
        &verifier_calls, &lease, &blockers) == MT6897_UFS_GATE_DENIED);
    CHECK(blockers == MT6897_UFS_CURRENT_DUCHAMP_BLOCKERS);
    CHECK(verifier_calls == 0);
    receipt = valid_receipt(&lease);
    CHECK(mt6897_ufs_cache_bind(&cache, &gate, &lease, &receipt, &ops,
        &blockers) == MT6897_UFS_CACHE_LEASE);
    CHECK(cache.state == MT6897_UFS_CACHE_STATE_FAULTED);
    CHECK(model.count == 0);
    CHECK(mt6897_ufs_cache_for_device(&cache,
        MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
        MT6897_UFS_CACHE_FAULTED);
    CHECK(model.count == 0);
    *current_callbacks = model.count;
}

static void
test_successful_directions(unsigned *model_handoffs)
{
    unsigned direction;

    for (direction = MT6897_UFS_CACHE_TO_DEVICE;
         direction <= MT6897_UFS_CACHE_BIDIRECTIONAL; ++direction) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_cache cache = { 0 };
        struct cache_model model = { 0 };
        uint64_t blockers = UINT64_MAX;
        unsigned before;
        unsigned index;

        for (index = 0; index < sizeof(cpu_buffer); ++index) {
            cpu_buffer[index] = (unsigned char)(index ^ direction);
        }
        bind_cache(&gate, &lease, &cache, &model);
        CHECK(model.count == 1 && model.events[0].kind == EVENT_VERIFY);
        CHECK(mt6897_ufs_cache_for_device(&cache,
            (enum mt6897_ufs_cache_direction)direction, &blockers) ==
            MT6897_UFS_CACHE_OK);
        ++*model_handoffs;
        CHECK(cache.state == MT6897_UFS_CACHE_STATE_DEVICE_OWNED);
        CHECK(cache.transitions == 1);
        CHECK(model.count == 4);
        CHECK(model.events[1].kind == EVENT_VERIFY);
        CHECK(model.events[2].kind == EVENT_CLEAN);
        CHECK(model.events[3].kind == EVENT_BARRIER_TO_DEVICE);
        before = model.count;
        CHECK(mt6897_ufs_cache_for_device(&cache,
            (enum mt6897_ufs_cache_direction)direction, &blockers) ==
            MT6897_UFS_CACHE_STATE);
        CHECK(model.count == before);

        model.device[17] = (unsigned char)(0xa0 + direction);
        CHECK(mt6897_ufs_cache_for_cpu(&cache,
            (enum mt6897_ufs_cache_direction)direction, &blockers) ==
            MT6897_UFS_CACHE_OK);
        ++*model_handoffs;
        CHECK(cache.state == MT6897_UFS_CACHE_STATE_CPU_OWNED);
        CHECK(cache.transitions == 2);
        CHECK(model.events[4].kind == EVENT_VERIFY);
        CHECK(model.events[5].kind == EVENT_BARRIER_BEFORE_CPU);
        if (direction == MT6897_UFS_CACHE_TO_DEVICE) {
            CHECK(model.count == 7);
            CHECK(model.events[6].kind == EVENT_BARRIER_AFTER_CPU);
            CHECK(cpu_buffer[17] == (unsigned char)(17 ^ direction));
        } else {
            CHECK(model.count == 8);
            CHECK(model.events[6].kind == EVENT_FLUSH);
            CHECK(model.events[7].kind == EVENT_BARRIER_AFTER_CPU);
            CHECK(cpu_buffer[17] == (unsigned char)(0xa0 + direction));
        }
        before = model.count;
        CHECK(mt6897_ufs_cache_for_cpu(&cache,
            (enum mt6897_ufs_cache_direction)direction, &blockers) ==
            MT6897_UFS_CACHE_STATE);
        CHECK(model.count == before);
        CHECK(mt6897_ufs_cache_bind(&cache, &gate, &lease,
            &cache.receipt, &cache.ops, &blockers) ==
            MT6897_UFS_CACHE_STATE);
    }
}

static void
damage_receipt(struct mt6897_ufs_cache_receipt *receipt, unsigned mode)
{
    switch (mode) {
    case 0: ++receipt->version; break;
    case 1: receipt->flags &= ~MT6897_UFS_CACHE_NO_CPU_ALIASES; break;
    case 2: receipt->flags |= UINT32_C(0x80000000); break;
    case 3: ++receipt->boot_generation; break;
    case 4: ++receipt->cache_owner_id; break;
    case 5: receipt->range_owner_id = 0; break;
    case 6: ++receipt->cpu_address; break;
    case 7: ++receipt->physical_address; break;
    case 8: receipt->bytes = 0; break;
    case 9: --receipt->bytes; break;
    case 10: receipt->cache_line_size = 63; break;
    case 11: receipt->reserved0 = 1; break;
    case 12: receipt->clean_implementation_id = 0; break;
    case 13: receipt->flush_implementation_id = 0; break;
    case 14: receipt->barrier_implementation_id = 0; break;
    case 15:
        receipt->cpu_address = UINT64_MAX - 63;
        receipt->bytes = 128;
        break;
    case 16:
        receipt->physical_address = UINT64_MAX - 63;
        receipt->bytes = 128;
        break;
    default: receipt->cache_line_size = 8; break;
    }
}

static void
test_receipt_rejection(void)
{
    unsigned mode;

    for (mode = 0; mode < 18; ++mode) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_cache cache = { 0 };
        struct cache_model model = { 0 };
        struct mt6897_ufs_cache_ops ops = cache_ops(&model);
        struct mt6897_ufs_cache_receipt receipt;
        uint64_t blockers = 0;

        authorize_gate(&gate, &lease);
        receipt = valid_receipt(&lease);
        damage_receipt(&receipt, mode);
        CHECK(mt6897_ufs_cache_bind(&cache, &gate, &lease, &receipt,
            &ops, &blockers) == MT6897_UFS_CACHE_CONTRACT);
        CHECK(cache.state == MT6897_UFS_CACHE_STATE_FAULTED);
        CHECK(model.count == 0);
        CHECK((blockers & MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT) != 0);
    }
}

static void
test_stale_and_mutated_contract(void)
{
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_cache cache = { 0 };
        struct cache_model model = { 0 };
        uint64_t blockers = 0;
        unsigned before;

        bind_cache(&gate, &lease, &cache, &model);
        before = model.count;
        ++cache.lease.lease_id;
        CHECK(mt6897_ufs_cache_for_device(&cache,
            MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
            MT6897_UFS_CACHE_LEASE);
        CHECK(cache.state == MT6897_UFS_CACHE_STATE_FAULTED);
        CHECK(model.count == before);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_cache cache = { 0 };
        struct cache_model model = { 0 };
        uint64_t blockers = 0;
        unsigned before;

        bind_cache(&gate, &lease, &cache, &model);
        before = model.count;
        cache.receipt.physical_address += cache.receipt.cache_line_size;
        CHECK(mt6897_ufs_cache_for_device(&cache,
            MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
            MT6897_UFS_CACHE_FAULTED);
        CHECK(cache.state == MT6897_UFS_CACHE_STATE_FAULTED);
        CHECK(model.count == before);
    }
}

static void
test_callback_failures(void)
{
    unsigned failure;

    for (failure = EVENT_VERIFY; failure <= EVENT_BARRIER_AFTER_CPU;
         ++failure) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_cache cache = { 0 };
        struct cache_model model = { 0 };
        uint64_t blockers = 0;
        unsigned before;

        bind_cache(&gate, &lease, &cache, &model);
        if (failure == EVENT_BARRIER_BEFORE_CPU || failure == EVENT_FLUSH ||
            failure == EVENT_BARRIER_AFTER_CPU) {
            CHECK(mt6897_ufs_cache_for_device(&cache,
                MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
                MT6897_UFS_CACHE_OK);
        }
        model.fail_kind = failure;
        if (failure == EVENT_VERIFY || failure == EVENT_CLEAN ||
            failure == EVENT_BARRIER_TO_DEVICE) {
            CHECK(mt6897_ufs_cache_for_device(&cache,
                MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
                MT6897_UFS_CACHE_CALLBACK);
        } else {
            CHECK(mt6897_ufs_cache_for_cpu(&cache,
                MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
                MT6897_UFS_CACHE_CALLBACK);
        }
        CHECK(cache.state == MT6897_UFS_CACHE_STATE_FAULTED);
        before = model.count;
        CHECK(mt6897_ufs_cache_for_device(&cache,
            MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
            MT6897_UFS_CACHE_FAULTED);
        CHECK(model.count == before);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_cache cache = { 0 };
        struct cache_model model = { 0 };
        struct mt6897_ufs_cache_ops ops = cache_ops(&model);
        struct mt6897_ufs_cache_receipt receipt;
        uint64_t blockers = 0;

        authorize_gate(&gate, &lease);
        receipt = valid_receipt(&lease);
        model.fail_kind = EVENT_VERIFY;
        CHECK(mt6897_ufs_cache_bind(&cache, &gate, &lease, &receipt,
            &ops, &blockers) == MT6897_UFS_CACHE_CALLBACK);
        CHECK(cache.state == MT6897_UFS_CACHE_STATE_FAULTED);
        CHECK(model.count == 1);
        CHECK(model.events[0].kind == EVENT_VERIFY);
    }
}

static void
test_arguments(void)
{
    struct mt6897_ufs_cache cache = { 0 };
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct mt6897_ufs_cache_receipt receipt = { 0 };
    struct mt6897_ufs_cache_ops ops = { 0 };
    uint64_t blockers = 0;

    CHECK(mt6897_ufs_cache_bind(0, &gate, &lease, &receipt, &ops,
        &blockers) == MT6897_UFS_CACHE_ARGUMENT);
    CHECK(mt6897_ufs_cache_bind(&cache, &gate, &lease, &receipt, &ops,
        &blockers) == MT6897_UFS_CACHE_ARGUMENT);
    CHECK(mt6897_ufs_cache_for_device(0,
        MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
        MT6897_UFS_CACHE_ARGUMENT);
    CHECK(mt6897_ufs_cache_for_device(&cache,
        (enum mt6897_ufs_cache_direction)0, &blockers) ==
        MT6897_UFS_CACHE_ARGUMENT);
    CHECK(mt6897_ufs_cache_for_cpu(&cache,
        (enum mt6897_ufs_cache_direction)4, &blockers) ==
        MT6897_UFS_CACHE_ARGUMENT);
    CHECK(mt6897_ufs_cache_fault(0, 0, &blockers) ==
        MT6897_UFS_CACHE_ARGUMENT);
}

int
main(void)
{
    unsigned current_callbacks = UINT32_MAX;
    unsigned model_handoffs = 0;

    test_default_closed(&current_callbacks);
    test_successful_directions(&model_handoffs);
    test_receipt_rejection();
    test_stale_and_mutated_contract();
    test_callback_failures();
    test_arguments();
    (void)printf("%u MT6897 UFS noncoherent-cache checks passed; "
        "current_callbacks=%u model_handoffs=%u\n", checks,
        current_callbacks, model_handoffs);
    return 0;
}
