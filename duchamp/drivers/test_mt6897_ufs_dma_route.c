#include "mt6897_ufs_dma_route.h"

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

#define BOOT_GENERATION UINT64_C(0x202611040301)
#define SOURCE_PA UINT64_C(0x100000000)
#define DIRECT_DMA UINT64_C(0x200000000)
#define BOUNCE_PA UINT64_C(0x300000000)
#define BOUNCE_DMA UINT64_C(0x400000000)

_Alignas(64) static unsigned char source_buffer[512];
_Alignas(64) static unsigned char bounce_buffer[512];

struct route_model {
    unsigned verify_calls;
    unsigned copy_to_calls;
    unsigned copy_from_calls;
    unsigned fail_verify;
    unsigned fail_copy_to;
    unsigned fail_copy_from;
    unsigned mutate_receipt;
};

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
complete_evidence(int bounced)
{
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);

    evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED;
    if (bounced) {
        evidence.asserted |= MT6897_UFS_E_BOUNCE_REQUIRED |
            MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP;
        evidence.bounce_start = BOUNCE_DMA;
        evidence.bounce_size = sizeof(bounce_buffer);
        evidence.bounce_owner_id = UINT64_C(0x9909);
    } else {
        evidence.asserted |= MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    }
    evidence.known = evidence.asserted;
    return evidence;
}

static void
authorize_gate(struct mt6897_ufs_gate *gate,
    struct mt6897_ufs_gate_lease *lease, int bounced)
{
    struct mt6897_ufs_gate_evidence evidence = complete_evidence(bounced);
    uint64_t blockers = UINT64_MAX;
    unsigned verifier_calls = 0;

    CHECK(mt6897_ufs_gate_init(gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(gate, &evidence, approve_lease,
        &verifier_calls, lease, &blockers) == MT6897_UFS_GATE_LEASED);
    CHECK(verifier_calls == 1);
    CHECK(blockers == 0);
}

static struct mt6897_ufs_dma_route_receipt
valid_receipt(const struct mt6897_ufs_gate_lease *lease, int bounced)
{
    struct mt6897_ufs_dma_route_receipt receipt = { 0 };

    receipt.version = MT6897_UFS_DMA_ROUTE_CONTRACT_VERSION;
    receipt.flags = bounced ? MT6897_UFS_DMA_BOUNCE_FLAGS :
        MT6897_UFS_DMA_DIRECT_FLAGS;
    receipt.route = bounced ? MT6897_UFS_DMA_ROUTE_BOUNCE_POOL :
        MT6897_UFS_DMA_ROUTE_DIRECT_AFFINE;
    receipt.bounce_disposition = bounced ?
        MT6897_UFS_DMA_BOUNCE_REQUIRED :
        MT6897_UFS_DMA_BOUNCE_NOT_REQUIRED;
    receipt.boot_generation = lease->boot_generation;
    receipt.dma_owner_id = lease->dma_owner_id;
    receipt.cache_owner_id = lease->cache_owner_id;
    receipt.controller_owner_id = lease->controller_owner_id;
    receipt.firmware_owner_id = lease->firmware_owner_id;
    receipt.source_owner_id = UINT64_C(0x8808);
    receipt.source_cpu_begin = (uint64_t)(uintptr_t)source_buffer;
    receipt.source_pa_begin = SOURCE_PA;
    receipt.source_bytes = sizeof(source_buffer);
    receipt.dma_limit = MT6897_UFS_DUCHAMP_DMA_LIMIT;
    receipt.dma_address_bits = MT6897_UFS_DUCHAMP_DMA_BITS;
    receipt.alignment = 64;
    receipt.translation_implementation_id = UINT64_C(0xd0010001);
    receipt.firewall_receipt_id = UINT64_C(0xf0010002);
    receipt.cache_contract_id = UINT64_C(0xca000003);
    if (bounced) {
        receipt.bounce_owner_id = UINT64_C(0x9909);
        receipt.bounce_cpu_begin = (uint64_t)(uintptr_t)bounce_buffer;
        receipt.bounce_pa_begin = BOUNCE_PA;
        receipt.bounce_dma_begin = BOUNCE_DMA;
        receipt.bounce_bytes = sizeof(bounce_buffer);
        receipt.copy_to_implementation_id = UINT64_C(0xc0700004);
        receipt.copy_from_implementation_id = UINT64_C(0xc0f00005);
    } else {
        receipt.device_begin = DIRECT_DMA;
        receipt.device_bytes = sizeof(source_buffer);
    }
    return receipt;
}

static int
verify_receipt(void *context,
    const struct mt6897_ufs_dma_route_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease)
{
    struct route_model *model = (struct route_model *)context;

    CHECK(receipt->version == MT6897_UFS_DMA_ROUTE_CONTRACT_VERSION);
    CHECK(receipt->boot_generation == lease->boot_generation);
    CHECK(receipt->dma_owner_id == lease->dma_owner_id);
    CHECK(receipt->cache_owner_id == lease->cache_owner_id);
    CHECK(receipt->controller_owner_id == lease->controller_owner_id);
    CHECK(receipt->firmware_owner_id == lease->firmware_owner_id);
    ++model->verify_calls;
    if (model->mutate_receipt) {
        ((struct mt6897_ufs_dma_route_receipt *)(uintptr_t)receipt)->
            source_owner_id ^= UINT64_C(1);
    }
    return model->fail_verify ? -1 : 0;
}

static int
copy_to_bounce(void *context, uint64_t destination, uint64_t source,
    uint64_t bytes)
{
    struct route_model *model = (struct route_model *)context;
    unsigned char *destination_bytes = (unsigned char *)(uintptr_t)destination;
    const unsigned char *source_bytes =
        (const unsigned char *)(uintptr_t)source;
    uint64_t index;

    CHECK(destination == (uint64_t)(uintptr_t)bounce_buffer);
    CHECK(source >= (uint64_t)(uintptr_t)source_buffer);
    CHECK(bytes <= sizeof(bounce_buffer));
    ++model->copy_to_calls;
    if (model->fail_copy_to) {
        return -1;
    }
    for (index = 0; index < bytes; ++index) {
        destination_bytes[index] = source_bytes[index];
    }
    return 0;
}

static int
copy_from_bounce(void *context, uint64_t destination, uint64_t source,
    uint64_t bytes)
{
    struct route_model *model = (struct route_model *)context;
    unsigned char *destination_bytes = (unsigned char *)(uintptr_t)destination;
    const unsigned char *source_bytes =
        (const unsigned char *)(uintptr_t)source;
    uint64_t index;

    CHECK(source == (uint64_t)(uintptr_t)bounce_buffer);
    CHECK(destination >= (uint64_t)(uintptr_t)source_buffer);
    CHECK(bytes <= sizeof(bounce_buffer));
    ++model->copy_from_calls;
    if (model->fail_copy_from) {
        return -1;
    }
    for (index = 0; index < bytes; ++index) {
        destination_bytes[index] = source_bytes[index];
    }
    return 0;
}

static struct mt6897_ufs_dma_route_ops
route_ops(struct route_model *model)
{
    struct mt6897_ufs_dma_route_ops ops = {
        model, verify_receipt, copy_to_bounce, copy_from_bounce
    };

    return ops;
}

static struct mt6897_ufs_dma_route_request
valid_request(uint32_t direction)
{
    struct mt6897_ufs_dma_route_request request = { 0 };

    request.cpu_address = (uint64_t)(uintptr_t)(source_buffer + 64);
    request.physical_address = SOURCE_PA + 64;
    request.bytes = 128;
    request.direction = direction;
    return request;
}

static void
bind_route(struct mt6897_ufs_gate *gate,
    struct mt6897_ufs_gate_lease *lease,
    struct mt6897_ufs_dma_route *route, struct route_model *model,
    int bounced)
{
    struct mt6897_ufs_dma_route_receipt receipt;
    struct mt6897_ufs_dma_route_ops ops = route_ops(model);
    uint64_t blockers = UINT64_MAX;

    authorize_gate(gate, lease, bounced);
    receipt = valid_receipt(lease, bounced);
    CHECK(mt6897_ufs_dma_route_bind(route, gate, lease, &receipt, &ops,
        &blockers) == MT6897_UFS_DMA_ROUTE_OK);
    CHECK(route->state == MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED);
    CHECK(route->transitions == 0);
    CHECK(model->verify_calls == 1);
    CHECK(blockers == 0);
}

static void
test_default_closed(unsigned *current_callbacks)
{
    struct mt6897_ufs_dma_route zero = { 0 };
    struct mt6897_ufs_dma_route_request request =
        valid_request(MT6897_UFS_DMA_BIDIRECTIONAL);
    struct mt6897_ufs_dma_route_mapping mapping = { 0 };
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct mt6897_ufs_dma_route route = { 0 };
    struct mt6897_ufs_dma_route_receipt receipt;
    struct route_model model = { 0 };
    struct mt6897_ufs_dma_route_ops ops = route_ops(&model);
    uint64_t blockers = 0;
    unsigned verifier_calls = 0;

    CHECK(mt6897_ufs_dma_route_for_device(&zero, &request, &mapping,
        &blockers) == MT6897_UFS_DMA_ROUTE_DISABLED);
    CHECK(mt6897_ufs_dma_route_for_cpu(&zero, &mapping, &blockers) ==
        MT6897_UFS_DMA_ROUTE_DISABLED);
    CHECK(model.verify_calls == 0 && model.copy_to_calls == 0 &&
        model.copy_from_calls == 0);

    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, unreachable_lease,
        &verifier_calls, &lease, &blockers) == MT6897_UFS_GATE_DENIED);
    CHECK(blockers == MT6897_UFS_CURRENT_DUCHAMP_BLOCKERS);
    CHECK(verifier_calls == 0);
    receipt = valid_receipt(&lease, 0);
    CHECK(mt6897_ufs_dma_route_bind(&route, &gate, &lease, &receipt, &ops,
        &blockers) == MT6897_UFS_DMA_ROUTE_LEASE);
    CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
    CHECK(mt6897_ufs_dma_route_for_device(&route, &request, &mapping,
        &blockers) == MT6897_UFS_DMA_ROUTE_FAULTED);
    CHECK(model.verify_calls == 0 && model.copy_to_calls == 0 &&
        model.copy_from_calls == 0);
    *current_callbacks = model.verify_calls + model.copy_to_calls +
        model.copy_from_calls;
}

static void
test_successful_routes(unsigned *direct_mappings, unsigned *bounce_mappings)
{
    uint32_t direction;

    for (direction = MT6897_UFS_DMA_TO_DEVICE;
         direction <= MT6897_UFS_DMA_BIDIRECTIONAL; ++direction) {
        int bounced;

        for (bounced = 0; bounced <= 1; ++bounced) {
            struct mt6897_ufs_gate gate = { 0 };
            struct mt6897_ufs_gate_lease lease = { 0 };
            struct mt6897_ufs_dma_route route = { 0 };
            struct route_model model = { 0 };
            struct mt6897_ufs_dma_route_request request =
                valid_request(direction);
            struct mt6897_ufs_dma_route_mapping mapping = { 0 };
            unsigned index;
            unsigned expected_copy_to;
            unsigned expected_copy_from;
            uint64_t blockers = UINT64_MAX;

            for (index = 0; index < sizeof(source_buffer); ++index) {
                source_buffer[index] = (unsigned char)(index ^ direction);
                bounce_buffer[index] = 0;
            }
            bind_route(&gate, &lease, &route, &model, bounced);
            CHECK(mt6897_ufs_dma_route_for_device(&route, &request,
                &mapping, &blockers) == MT6897_UFS_DMA_ROUTE_OK);
            CHECK(blockers == 0);
            CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_DEVICE_OWNED);
            CHECK(route.transitions == 1);
            CHECK(mapping.source_cpu_address == request.cpu_address);
            CHECK(mapping.source_physical_address ==
                request.physical_address);
            CHECK(mapping.bytes == request.bytes);
            CHECK(mapping.direction == direction);
            if (bounced) {
                ++*bounce_mappings;
                CHECK(mapping.bounced == 1);
                CHECK(mapping.dma_cpu_address ==
                    (uint64_t)(uintptr_t)bounce_buffer);
                CHECK(mapping.dma_physical_address == BOUNCE_PA);
                CHECK(mapping.device_address == BOUNCE_DMA);
            } else {
                ++*direct_mappings;
                CHECK(mapping.bounced == 0);
                CHECK(mapping.dma_cpu_address == request.cpu_address);
                CHECK(mapping.dma_physical_address ==
                    request.physical_address);
                CHECK(mapping.device_address == DIRECT_DMA + 64);
            }
            expected_copy_to = bounced &&
                direction != MT6897_UFS_DMA_FROM_DEVICE;
            CHECK(model.copy_to_calls == expected_copy_to);
            if (bounced && direction != MT6897_UFS_DMA_TO_DEVICE) {
                bounce_buffer[17] = (unsigned char)(0xa0 + direction);
            }
            CHECK(mt6897_ufs_dma_route_for_cpu(&route, &mapping,
                &blockers) == MT6897_UFS_DMA_ROUTE_OK);
            CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED);
            CHECK(route.transitions == 2);
            expected_copy_from = bounced &&
                direction != MT6897_UFS_DMA_TO_DEVICE;
            CHECK(model.copy_from_calls == expected_copy_from);
            if (expected_copy_from) {
                CHECK(source_buffer[64 + 17] ==
                    (unsigned char)(0xa0 + direction));
            }
            CHECK(model.verify_calls == 3);
            CHECK(mt6897_ufs_dma_route_for_cpu(&route, &mapping,
                &blockers) == MT6897_UFS_DMA_ROUTE_STATE);
        }
    }
}

static void
test_range_rejection(void)
{
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct mt6897_ufs_dma_route route = { 0 };
    struct route_model model = { 0 };
    struct mt6897_ufs_dma_route_request requests[6];
    struct mt6897_ufs_dma_route_mapping mapping;
    uint64_t blockers = 0;
    unsigned index;

    bind_route(&gate, &lease, &route, &model, 0);
    for (index = 0; index < 6; ++index) {
        requests[index] = valid_request(MT6897_UFS_DMA_BIDIRECTIONAL);
    }
    ++requests[0].cpu_address;
    requests[1].physical_address += 64;
    requests[2].bytes = 0;
    requests[3].bytes = sizeof(source_buffer);
    requests[4].direction = 0;
    requests[5].reserved0 = 1;
    for (index = 0; index < 6; ++index) {
        CHECK(mt6897_ufs_dma_route_for_device(&route, &requests[index],
            &mapping, &blockers) == MT6897_UFS_DMA_ROUTE_RANGE);
        CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_CPU_OWNED);
        CHECK(route.transitions == 0);
        CHECK(mapping.cookie == 0);
        CHECK(model.verify_calls == 1);
        CHECK(model.copy_to_calls == 0 && model.copy_from_calls == 0);
    }
}

static void
damage_receipt(struct mt6897_ufs_dma_route_receipt *receipt, unsigned mode)
{
    switch (mode) {
    case 0: ++receipt->version; break;
    case 1: receipt->flags ^= MT6897_UFS_DMA_PRIVATE_SOURCE; break;
    case 2: receipt->route = MT6897_UFS_DMA_ROUTE_NONE; break;
    case 3: receipt->bounce_disposition = MT6897_UFS_DMA_BOUNCE_UNKNOWN; break;
    case 4: ++receipt->boot_generation; break;
    case 5: ++receipt->dma_owner_id; break;
    case 6: ++receipt->cache_owner_id; break;
    case 7: ++receipt->controller_owner_id; break;
    case 8: ++receipt->firmware_owner_id; break;
    case 9: receipt->source_owner_id = 0; break;
    case 10: ++receipt->source_cpu_begin; break;
    case 11: --receipt->source_bytes; break;
    case 12: receipt->device_bytes -= 64; break;
    case 13: receipt->dma_limit = receipt->device_begin; break;
    case 14: receipt->dma_address_bits = 1; break;
    case 15: receipt->alignment = 3; break;
    case 16: receipt->translation_implementation_id = 0; break;
    case 17: receipt->firewall_receipt_id = 0; break;
    case 18: receipt->cache_contract_id = 0; break;
    case 19: receipt->bounce_owner_id = 1; break;
    default: receipt->copy_to_implementation_id = 1; break;
    }
}

static void
test_bad_receipts(void)
{
    unsigned mode;

    for (mode = 0; mode < 21; ++mode) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_dma_route route = { 0 };
        struct route_model model = { 0 };
        struct mt6897_ufs_dma_route_receipt receipt;
        struct mt6897_ufs_dma_route_ops ops = route_ops(&model);
        uint64_t blockers = 0;

        authorize_gate(&gate, &lease, 0);
        receipt = valid_receipt(&lease, 0);
        damage_receipt(&receipt, mode);
        CHECK(mt6897_ufs_dma_route_bind(&route, &gate, &lease, &receipt,
            &ops, &blockers) == MT6897_UFS_DMA_ROUTE_CONTRACT);
        CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        CHECK(model.verify_calls == 0 && model.copy_to_calls == 0 &&
            model.copy_from_calls == 0);
        CHECK((blockers & MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT) != 0);
    }
}

static void
test_tampering_and_callbacks(void)
{
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_dma_route route = { 0 };
        struct route_model model = { 0 };
        struct mt6897_ufs_dma_route_request request =
            valid_request(MT6897_UFS_DMA_BIDIRECTIONAL);
        struct mt6897_ufs_dma_route_mapping mapping;
        uint64_t blockers = 0;

        bind_route(&gate, &lease, &route, &model, 0);
        route.receipt.device_begin += 64;
        CHECK(mt6897_ufs_dma_route_for_device(&route, &request, &mapping,
            &blockers) == MT6897_UFS_DMA_ROUTE_FAULTED);
        CHECK(model.verify_calls == 1);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_dma_route route = { 0 };
        struct route_model model = { 0 };
        struct mt6897_ufs_dma_route_request request =
            valid_request(MT6897_UFS_DMA_BIDIRECTIONAL);
        struct mt6897_ufs_dma_route_mapping mapping;
        uint64_t blockers = 0;

        bind_route(&gate, &lease, &route, &model, 0);
        CHECK(mt6897_ufs_dma_route_for_device(&route, &request, &mapping,
            &blockers) == MT6897_UFS_DMA_ROUTE_OK);
        ++mapping.cookie;
        CHECK(mt6897_ufs_dma_route_for_cpu(&route, &mapping, &blockers) ==
            MT6897_UFS_DMA_ROUTE_FAULTED);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_dma_route route = { 0 };
        struct route_model model = { 0 };
        struct mt6897_ufs_dma_route_receipt receipt;
        struct mt6897_ufs_dma_route_ops ops = route_ops(&model);
        uint64_t blockers = 0;

        authorize_gate(&gate, &lease, 0);
        receipt = valid_receipt(&lease, 0);
        model.fail_verify = 1;
        CHECK(mt6897_ufs_dma_route_bind(&route, &gate, &lease, &receipt,
            &ops, &blockers) == MT6897_UFS_DMA_ROUTE_CALLBACK);
        CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_dma_route route = { 0 };
        struct route_model model = { 0 };
        struct mt6897_ufs_dma_route_receipt receipt;
        struct mt6897_ufs_dma_route_ops ops = route_ops(&model);
        uint64_t blockers = 0;

        authorize_gate(&gate, &lease, 0);
        receipt = valid_receipt(&lease, 0);
        model.mutate_receipt = 1;
        CHECK(mt6897_ufs_dma_route_bind(&route, &gate, &lease, &receipt,
            &ops, &blockers) == MT6897_UFS_DMA_ROUTE_CONTRACT);
        CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        CHECK(model.verify_calls == 1);
        CHECK(receipt.source_owner_id == UINT64_C(0x8808));
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_dma_route route = { 0 };
        struct route_model model = { 0 };
        struct mt6897_ufs_dma_route_request request =
            valid_request(MT6897_UFS_DMA_BIDIRECTIONAL);
        struct mt6897_ufs_dma_route_mapping mapping;
        uint64_t blockers = 0;

        bind_route(&gate, &lease, &route, &model, 1);
        model.fail_copy_to = 1;
        CHECK(mt6897_ufs_dma_route_for_device(&route, &request, &mapping,
            &blockers) == MT6897_UFS_DMA_ROUTE_CALLBACK);
        CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        CHECK(model.copy_to_calls == 1);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_dma_route route = { 0 };
        struct route_model model = { 0 };
        struct mt6897_ufs_dma_route_request request =
            valid_request(MT6897_UFS_DMA_FROM_DEVICE);
        struct mt6897_ufs_dma_route_mapping mapping;
        uint64_t blockers = 0;

        bind_route(&gate, &lease, &route, &model, 1);
        CHECK(mt6897_ufs_dma_route_for_device(&route, &request, &mapping,
            &blockers) == MT6897_UFS_DMA_ROUTE_OK);
        model.fail_copy_from = 1;
        CHECK(mt6897_ufs_dma_route_for_cpu(&route, &mapping, &blockers) ==
            MT6897_UFS_DMA_ROUTE_CALLBACK);
        CHECK(route.state == MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
        CHECK(model.copy_from_calls == 1);
    }
}

static void
test_arguments(void)
{
    struct mt6897_ufs_dma_route route = { 0 };
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct mt6897_ufs_dma_route_receipt receipt = { 0 };
    struct mt6897_ufs_dma_route_ops ops = { 0 };
    struct mt6897_ufs_dma_route_request request = { 0 };
    struct mt6897_ufs_dma_route_mapping mapping = { 0 };
    uint64_t blockers = 0;

    CHECK(mt6897_ufs_dma_route_bind(0, &gate, &lease, &receipt, &ops,
        &blockers) == MT6897_UFS_DMA_ROUTE_ARGUMENT);
    CHECK(mt6897_ufs_dma_route_bind(&route, &gate, &lease, &receipt, &ops,
        &blockers) == MT6897_UFS_DMA_ROUTE_ARGUMENT);
    CHECK(mt6897_ufs_dma_route_for_device(0, &request, &mapping,
        &blockers) == MT6897_UFS_DMA_ROUTE_ARGUMENT);
    CHECK(mt6897_ufs_dma_route_for_device(&route, 0, &mapping,
        &blockers) == MT6897_UFS_DMA_ROUTE_ARGUMENT);
    CHECK(mt6897_ufs_dma_route_for_cpu(0, &mapping, &blockers) ==
        MT6897_UFS_DMA_ROUTE_ARGUMENT);
    CHECK(mt6897_ufs_dma_route_fault(0, 0, &blockers) ==
        MT6897_UFS_DMA_ROUTE_ARGUMENT);
}

int
main(void)
{
    unsigned current_callbacks = UINT32_MAX;
    unsigned direct_mappings = 0;
    unsigned bounce_mappings = 0;

    test_default_closed(&current_callbacks);
    test_successful_routes(&direct_mappings, &bounce_mappings);
    test_range_rejection();
    test_bad_receipts();
    test_tampering_and_callbacks();
    test_arguments();
    CHECK(current_callbacks == 0);
    CHECK(direct_mappings == 3);
    CHECK(bounce_mappings == 3);
    (void)printf("%u MT6897 UFS DMA-route checks passed; "
        "current_callbacks=%u direct_mappings=%u bounce_mappings=%u\n",
        checks, current_callbacks, direct_mappings, bounce_mappings);
    return 0;
}
