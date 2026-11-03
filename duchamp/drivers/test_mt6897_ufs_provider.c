#include "mt6897_ufs_provider.h"

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

#define BOOT_GENERATION UINT64_C(0x202611030101)

struct dispatch_model {
    unsigned calls[MT6897_UFS_PROVIDER_OPERATION_COUNT];
    unsigned total;
    int fail_operation;
};

static struct mt6897_ufs_gate_evidence
valid_evidence(void)
{
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);

    evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED |
        MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    evidence.known = evidence.asserted;
    return evidence;
}

static enum mt6897_ufs_gate_verdict
approve_lease(void *context,
    const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    unsigned *calls = (unsigned *)context;

    ++*calls;
    lease->version = MT6897_UFS_GATE_LEASE_VERSION;
    lease->flags = MT6897_UFS_LEASE_REQUIRED_FLAGS;
    lease->boot_generation = request->evidence.boot_generation;
    lease->evidence_fingerprint = request->evidence_fingerprint;
    lease->lease_id = UINT64_C(0x1001);
    lease->provider_epoch = UINT64_C(0x2002);
    lease->controller_owner_id = UINT64_C(0x3003);
    lease->phy_owner_id = UINT64_C(0x4004);
    lease->dma_owner_id = UINT64_C(0x5005);
    lease->cache_owner_id = UINT64_C(0x6006);
    lease->firmware_owner_id = UINT64_C(0x7007);
    return MT6897_UFS_GATE_VERIFY_APPROVE;
}

static int
model_dispatch(void *context,
    const struct mt6897_ufs_provider_request *request, uint64_t *result_out)
{
    struct dispatch_model *model = (struct dispatch_model *)context;

    CHECK(request != 0);
    CHECK(result_out != 0);
    CHECK(request->version == MT6897_UFS_PROVIDER_REQUEST_VERSION);
    CHECK(request->operation < MT6897_UFS_PROVIDER_OPERATION_COUNT);
    ++model->calls[request->operation];
    ++model->total;
    *result_out = UINT64_C(0x9000) + request->operation;
    if (model->fail_operation == (int)request->operation) {
        return -1;
    }
    return 0;
}

static void
authorize_gate(struct mt6897_ufs_gate *gate,
    struct mt6897_ufs_gate_lease *lease)
{
    struct mt6897_ufs_gate_evidence evidence = valid_evidence();
    unsigned verifier_calls = 0;
    uint64_t blockers = 0;

    CHECK(mt6897_ufs_gate_init(gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(gate, &evidence, approve_lease,
        &verifier_calls, lease, &blockers) == MT6897_UFS_GATE_LEASED);
    CHECK(verifier_calls == 1);
    CHECK(blockers == 0);
}

static void
bind_provider(struct mt6897_ufs_provider *provider,
    struct mt6897_ufs_gate *gate, struct mt6897_ufs_gate_lease *lease,
    struct dispatch_model *model)
{
    const struct mt6897_ufs_provider_ops ops = {
        .context = model,
        .dispatch = model_dispatch
    };
    uint64_t blockers = 0;

    authorize_gate(gate, lease);
    CHECK(mt6897_ufs_provider_bind(provider, gate, lease, &ops,
        &blockers) == MT6897_UFS_PROVIDER_OK);
    CHECK(blockers == 0);
    CHECK(provider->state == MT6897_UFS_PROVIDER_STATE_ACTIVE);
    CHECK(provider->dispatches == 0);
}

static void
call_all_denied(struct mt6897_ufs_provider *provider,
    enum mt6897_ufs_provider_result expected)
{
    uint64_t result = UINT64_C(0xffff);
    uint64_t blockers = UINT64_C(0xffff);

    CHECK(mt6897_ufs_provider_power(provider, 1, &result, &blockers) ==
        expected);
    CHECK(mt6897_ufs_provider_clock(provider, 0, 1, 1, &result,
        &blockers) == expected);
    CHECK(mt6897_ufs_provider_phy(provider, 1, &result, &blockers) ==
        expected);
    CHECK(mt6897_ufs_provider_mmio(provider, 1, 0x100, 0x55, &result,
        &blockers) == expected);
    CHECK(mt6897_ufs_provider_dma(provider, 1, 0x80000000, 4096,
        &result, &blockers) == expected);
    CHECK(mt6897_ufs_provider_command(provider, 0x28, 0, 0, 1,
        &result, &blockers) == expected);
}

static void
test_disabled_and_bad_arguments(void)
{
    struct mt6897_ufs_provider provider = { 0 };
    uint64_t argument[4] = { 0 };
    uint64_t result = 0;
    uint64_t blockers = 0;

    call_all_denied(&provider, MT6897_UFS_PROVIDER_DISABLED);
    CHECK(provider.dispatches == 0);
    CHECK(provider.state == MT6897_UFS_PROVIDER_STATE_DISABLED);
    CHECK(mt6897_ufs_provider_call(0, MT6897_UFS_PROVIDER_POWER,
        argument, &result, &blockers) == MT6897_UFS_PROVIDER_ARGUMENT);
    CHECK(mt6897_ufs_provider_call(&provider,
        MT6897_UFS_PROVIDER_OPERATION_COUNT, argument, &result,
        &blockers) == MT6897_UFS_PROVIDER_ARGUMENT);
}

static void
test_missing_and_stale_lease(void)
{
    struct dispatch_model missing_model = { .fail_operation = -1 };
    struct dispatch_model stale_model = { .fail_operation = -1 };
    struct mt6897_ufs_provider missing = { 0 };
    struct mt6897_ufs_provider stale = { 0 };
    struct mt6897_ufs_gate missing_gate = { 0 };
    struct mt6897_ufs_gate stale_gate = { 0 };
    struct mt6897_ufs_gate_lease missing_lease = { 0 };
    struct mt6897_ufs_gate_lease stale_lease = { 0 };
    const struct mt6897_ufs_provider_ops missing_ops = {
        .context = &missing_model, .dispatch = model_dispatch
    };
    const struct mt6897_ufs_provider_ops stale_ops = {
        .context = &stale_model, .dispatch = model_dispatch
    };
    uint64_t blockers = 0;

    CHECK(mt6897_ufs_gate_init(&missing_gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_provider_bind(&missing, &missing_gate, &missing_lease,
        &missing_ops, &blockers) == MT6897_UFS_PROVIDER_LEASE);
    CHECK(missing.state == MT6897_UFS_PROVIDER_STATE_FAULTED);
    call_all_denied(&missing, MT6897_UFS_PROVIDER_FAULTED);
    CHECK(missing_model.total == 0);
    CHECK(missing.dispatches == 0);

    authorize_gate(&stale_gate, &stale_lease);
    ++stale_lease.lease_id;
    blockers = 0;
    CHECK(mt6897_ufs_provider_bind(&stale, &stale_gate, &stale_lease,
        &stale_ops, &blockers) == MT6897_UFS_PROVIDER_LEASE);
    CHECK(stale.state == MT6897_UFS_PROVIDER_STATE_FAULTED);
    call_all_denied(&stale, MT6897_UFS_PROVIDER_FAULTED);
    CHECK(stale_model.total == 0);
    CHECK(stale.dispatches == 0);
}

static void
test_valid_model_dispatch(void)
{
    struct mt6897_ufs_provider provider = { 0 };
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct dispatch_model model = { .fail_operation = -1 };
    uint64_t result = 0;
    uint64_t blockers = 0;

    bind_provider(&provider, &gate, &lease, &model);
    CHECK(mt6897_ufs_provider_power(&provider, 1, &result, &blockers) ==
        MT6897_UFS_PROVIDER_OK);
    CHECK(mt6897_ufs_provider_clock(&provider, 0, 1, 1, &result,
        &blockers) == MT6897_UFS_PROVIDER_OK);
    CHECK(mt6897_ufs_provider_phy(&provider, 1, &result, &blockers) ==
        MT6897_UFS_PROVIDER_OK);
    CHECK(mt6897_ufs_provider_mmio(&provider, 1, 0x100, 0x55, &result,
        &blockers) == MT6897_UFS_PROVIDER_OK);
    CHECK(mt6897_ufs_provider_dma(&provider, 1, 0x80000000, 4096,
        &result, &blockers) == MT6897_UFS_PROVIDER_OK);
    CHECK(mt6897_ufs_provider_command(&provider, 0x28, 0, 0, 1,
        &result, &blockers) == MT6897_UFS_PROVIDER_OK);
    for (unsigned operation = 0;
        operation < MT6897_UFS_PROVIDER_OPERATION_COUNT; ++operation) {
        CHECK(model.calls[operation] == 1);
    }
    CHECK(model.total == MT6897_UFS_PROVIDER_OPERATION_COUNT);
    CHECK(provider.dispatches == MT6897_UFS_PROVIDER_OPERATION_COUNT);
    CHECK(provider.state == MT6897_UFS_PROVIDER_STATE_ACTIVE);

    CHECK(mt6897_ufs_gate_fault(&gate, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
        &blockers) == MT6897_UFS_GATE_FAULT);
    CHECK(mt6897_ufs_provider_command(&provider, 0x28, 0, 1, 1,
        &result, &blockers) == MT6897_UFS_PROVIDER_LEASE);
    CHECK(model.total == MT6897_UFS_PROVIDER_OPERATION_COUNT);
    CHECK(provider.dispatches == MT6897_UFS_PROVIDER_OPERATION_COUNT);
    CHECK(provider.state == MT6897_UFS_PROVIDER_STATE_FAULTED);
}

static void
test_callback_failure_is_terminal(void)
{
    struct mt6897_ufs_provider provider = { 0 };
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct dispatch_model model = {
        .fail_operation = MT6897_UFS_PROVIDER_MMIO
    };
    uint64_t result = 0;
    uint64_t blockers = 0;

    bind_provider(&provider, &gate, &lease, &model);
    CHECK(mt6897_ufs_provider_mmio(&provider, 1, 0, 0, &result,
        &blockers) == MT6897_UFS_PROVIDER_CALLBACK);
    CHECK(model.total == 1);
    CHECK(provider.dispatches == 1);
    CHECK(provider.state == MT6897_UFS_PROVIDER_STATE_FAULTED);
    CHECK((blockers & MT6897_UFS_BLOCK_PROVIDER_RUNTIME) != 0);
    CHECK(mt6897_ufs_provider_command(&provider, 0, 0, 0, 0, &result,
        &blockers) == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(model.total == 1);
    CHECK(provider.dispatches == 1);
}

int
main(void)
{
    test_disabled_and_bad_arguments();
    test_missing_and_stale_lease();
    test_valid_model_dispatch();
    test_callback_failure_is_terminal();
    (void)printf("%u MT6897 UFS lease-provider checks passed; "
        "model_dispatches=%u denied_dispatches=0\n", checks,
        (unsigned)MT6897_UFS_PROVIDER_OPERATION_COUNT);
    return 0;
}
