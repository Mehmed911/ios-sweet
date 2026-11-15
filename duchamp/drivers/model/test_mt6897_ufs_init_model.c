#include "mt6897_ufs_init_model.h"

#ifdef MT6897_MODEL_FREESTANDING
extern void model_assert_fail(const char *, unsigned);
extern int printf(const char *, ...);
#define CHECK(expr) do { if (!(expr)) model_assert_fail(#expr, __LINE__); } while (0)
#else
#include <assert.h>
#include <stdio.h>
#define CHECK(expr) assert(expr)
#endif

#define BOOT UINT64_C(0x202611150002)
#define NO_STEP (MUI_STEP_COUNT + 1)

struct fixture {
    struct mui_model model;
    struct mt6897_ufs_gate gate;
    struct mt6897_ufs_gate_lease lease;
    struct mui_ops ops;
    enum mui_step next, fail_at, pending_at, revoke_at, revoke_check_at;
    uint64_t now, time_step;
    uint32_t contract_flags;
    unsigned calls, clock_calls, contract_calls, verifier_calls, route;
    unsigned bad_progress, reenter, wait_once, jump_time, regress_time, late_deny;
};
static unsigned cases;

static enum mt6897_ufs_gate_verdict
approve(void *context, const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    struct fixture *f = context;
    f->verifier_calls++;
    CHECK(request->evidence.boot_generation == BOOT && request->route == f->route);
    *lease = (struct mt6897_ufs_gate_lease){
        .version = MT6897_UFS_GATE_LEASE_VERSION,
        .flags = MT6897_UFS_LEASE_REQUIRED_FLAGS,
        .boot_generation = BOOT,
        .evidence_fingerprint = request->evidence_fingerprint,
        .lease_id = 1, .provider_epoch = 2, .controller_owner_id = 3,
        .phy_owner_id = 4, .dma_owner_id = 5, .cache_owner_id = 6,
        .firmware_owner_id = 7
    };
    return MT6897_UFS_GATE_VERIFY_APPROVE;
}

static struct mt6897_ufs_gate_evidence
synthetic_evidence(unsigned route)
{
    struct mt6897_ufs_gate_evidence e = mt6897_ufs_gate_duchamp_known_evidence(BOOT);
    e.route = route;
    e.asserted = MT6897_UFS_E_COMMON_REQUIRED | MT6897_UFS_E_NONCOHERENT_DEVICE;
    if (route == MT6897_UFS_GATE_ROUTE_DIRECT_DMA) {
        e.asserted |= MT6897_UFS_E_DIRECT_BASE_REQUIRED | MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    } else {
        e.asserted |= MT6897_UFS_E_IOMMU_REQUIRED;
        e.iommu_stream_id = 8; e.iommu_domain_id = 9;
        e.iommu_table_id = 10; e.iommu_mapping_epoch = 11;
    }
    e.known = e.asserted;
    return e;
}

static void
fault(struct fixture *f)
{
    uint64_t blockers;
    CHECK(mt6897_ufs_gate_fault(&f->gate, MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
        &blockers) == MT6897_UFS_GATE_FAULT);
}

static uint32_t
contract(void *context, const struct mt6897_ufs_gate_lease *lease, enum mui_step step)
{
    struct fixture *f = context;
    f->contract_calls++;
    CHECK(step == f->next && lease->lease_id == 1 && lease->boot_generation == BOOT &&
        lease->provider_epoch == 2 && lease->controller_owner_id == 3 &&
        lease->phy_owner_id == 4 && lease->dma_owner_id == 5 &&
        lease->cache_owner_id == 6 && lease->firmware_owner_id == 7);
    if (step == f->revoke_check_at)
        fault(f);
    return f->late_deny && step == MUI_STEP_COUNT ? 0 : f->contract_flags;
}

static uint64_t
milliseconds(void *context)
{
    struct fixture *f = context;
    f->clock_calls++;
    uint64_t now = f->now;
    f->now += f->time_step;
    return now;
}

static int
dispatch(void *context, const struct mt6897_ufs_provider_request *req, uint64_t *progress)
{
    struct fixture *f = context;
    enum mui_step step = f->next;
    CHECK(step < MUI_STEP_COUNT && req->version == MT6897_UFS_PROVIDER_REQUEST_VERSION);
    CHECK(req->argument[0] == MUI_MODEL_TAG && req->argument[1] == step);
    CHECK(req->argument[2] == 0 && req->argument[3] == 0);
    CHECK(req->operation < MT6897_UFS_PROVIDER_OPERATION_COUNT &&
        req->operation != MT6897_UFS_PROVIDER_COMMAND);

    if (step == MUI_DMA) CHECK(req->operation == MT6897_UFS_PROVIDER_DMA);
    if (step == MUI_BUS_CLOCKS) CHECK(req->operation == MT6897_UFS_PROVIDER_CLOCK);
    if (step == MUI_HOST_RESET || step == MUI_UIC_LINK)
        CHECK(req->operation == MT6897_UFS_PROVIDER_MMIO);
    f->calls++;
    if (f->reenter) {
        CHECK(mui_run(&f->model, &f->gate, &f->lease, &f->ops) == MUI_ALREADY_USED);
        f->reenter = 0;
    }
    if (step == f->revoke_at) fault(f);
    if (step == f->fail_at) return -1;
    if (f->jump_time) f->now += f->ops.timeout_ms;
    if (f->regress_time) f->now = 0;
    if (f->bad_progress) {
        *progress = 2;
        return 0;
    }
    if (step == f->pending_at || f->wait_once) {
        *progress = MUI_PENDING;
        f->wait_once = 0;
        return 0;
    }
    f->next++;
    *progress = MUI_COMPLETE;
    return 0;
}

static void
setup(struct fixture *f, unsigned route, uint64_t missing)
{
    uint64_t blockers = 0;
    *f = (struct fixture){0};
    f->route = route;
    f->contract_flags = MUI_REQUIRED;
    f->fail_at = f->pending_at = f->revoke_at = f->revoke_check_at = NO_STEP;
    f->now = 1;
    f->ops = (struct mui_ops){
        .backend = { f, dispatch }, .contract = contract, .milliseconds = milliseconds,
        .timeout_ms = 8, .poll_limit = 3
    };
    struct mt6897_ufs_gate_evidence e = synthetic_evidence(route);
    if (missing) e.asserted &= ~missing;
    CHECK(mt6897_ufs_gate_init(&f->gate, BOOT) == MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&f->gate, &e, approve, f, &f->lease, &blockers) ==
        (missing ? MT6897_UFS_GATE_DENIED : MT6897_UFS_GATE_LEASED));
    CHECK(f->verifier_calls == !missing);
    if (missing) CHECK((blockers & missing) == missing);
}

static void
run(struct fixture *f, enum mui_result expected, unsigned completed, unsigned calls,
    unsigned recovery)
{
    CHECK(mui_run(&f->model, &f->gate, &f->lease, &f->ops) == expected);
    CHECK(f->model.result == expected && f->model.completed_steps == completed);
    CHECK(f->calls == calls && f->model.recovery_required == recovery);
    CHECK(f->model.state == (expected ? MUI_STOPPED : MUI_READY));
    CHECK(mui_run(&f->model, &f->gate, &f->lease, &f->ops) == MUI_ALREADY_USED);
    CHECK(f->calls == calls);
    uint64_t blockers;
    CHECK((mt6897_ufs_gate_lease_check(&f->gate, &f->lease, &blockers) ==
        MT6897_UFS_GATE_LEASED) == !expected);
    printf("UFS INIT case=%u result=%u steps=%u dispatches=%u quarantine=%u\n",
        ++cases, (unsigned)expected, completed, calls, recovery);
}

int
main(void)
{
    struct fixture f;
    const unsigned direct = MT6897_UFS_GATE_ROUTE_DIRECT_DMA;
    const unsigned iommu = MT6897_UFS_GATE_ROUTE_IOMMU;
    setup(&f, direct, 0); run(&f, MUI_OK, MUI_STEP_COUNT, MUI_STEP_COUNT, 0);
    setup(&f, iommu, 0); f.wait_once = f.reenter = 1;
    run(&f, MUI_OK, MUI_STEP_COUNT, MUI_STEP_COUNT + 1, 0);

    setup(&f, direct, 0); f.lease.boot_generation++;
    run(&f, MUI_LEASE_INVALID, 0, 0, 0);
    CHECK(!f.contract_calls && !f.clock_calls);

    setup(&f, direct, MT6897_UFS_E_DIRECT_ADDRESS_TRANSLATION);
    run(&f, MUI_LEASE_INVALID, 0, 0, 0);
    setup(&f, iommu, MT6897_UFS_E_IOMMU_MAPPING_OWNERSHIP);
    run(&f, MUI_LEASE_INVALID, 0, 0, 0);
    setup(&f, direct, MT6897_UFS_E_CACHE_MAINTENANCE_OWNERSHIP);
    run(&f, MUI_LEASE_INVALID, 0, 0, 0);

    for (unsigned bit = 0; bit < 6; bit++) {
        setup(&f, direct, 0); f.contract_flags &= ~(1u << bit);
        run(&f, MUI_CONTRACT_MISSING, 0, 0, 0);
    }
    setup(&f, direct, 0); f.contract_flags |= 0x40;
    run(&f, MUI_CONTRACT_MISSING, 0, 0, 0);

    for (enum mui_step step = MUI_RESOURCES; step < MUI_STEP_COUNT; step++) {
        setup(&f, direct, 0); f.fail_at = step;
        run(&f, MUI_BACKEND_FAILED, step, step + 1, step >= MUI_POWER);
        setup(&f, direct, 0); f.pending_at = step;
        run(&f, MUI_TIMEOUT, step, step + f.ops.poll_limit, step >= MUI_POWER);
        setup(&f, direct, 0); f.revoke_at = step;
        run(&f, MUI_LEASE_INVALID, step, step + 1, step >= MUI_POWER);
        setup(&f, direct, 0); f.revoke_check_at = step;
        run(&f, MUI_LEASE_INVALID, step, step, step > MUI_POWER);
    }

    setup(&f, direct, 0); f.now = 3; f.time_step = f.ops.timeout_ms;
    run(&f, MUI_TIMEOUT, 0, 0, 0);
    setup(&f, direct, 0); f.jump_time = 1;
    run(&f, MUI_TIMEOUT, 0, 1, 0);
    setup(&f, direct, 0); f.regress_time = 1;
    run(&f, MUI_CLOCK_FAULT, 0, 1, 0);
    setup(&f, direct, 0); f.bad_progress = 1;
    run(&f, MUI_BAD_PROGRESS, 0, 1, 0);
    setup(&f, direct, 0); f.late_deny = 1;
    run(&f, MUI_CONTRACT_MISSING, MUI_STEP_COUNT, MUI_STEP_COUNT, 1);
    setup(&f, direct, 0); f.revoke_check_at = MUI_STEP_COUNT;
    run(&f, MUI_LEASE_INVALID, MUI_STEP_COUNT, MUI_STEP_COUNT, 1);
    setup(&f, direct, 0); f.ops.poll_limit = MUI_POLL_MAX + 1;
    CHECK(mui_run(&f.model, &f.gate, &f.lease, &f.ops) == MUI_BAD_ARGUMENT);
    CHECK(f.model.state == MUI_NEW && !f.calls && !f.contract_calls);

    printf("MT6897 UFS INIT MODEL PASS cases=%u\n", cases);
    return 0;
}
