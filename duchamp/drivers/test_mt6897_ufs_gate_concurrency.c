#include "mt6897_ufs_gate.h"

#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BOOT_GENERATION UINT64_C(0x202611030001)

static _Atomic unsigned checks;

#define CHECK(expression) do { \
    (void)atomic_fetch_add_explicit(&checks, 1, memory_order_relaxed); \
    if (!(expression)) { \
        (void)fprintf(stderr, "line %u: check failed: %s\n", \
            __LINE__, #expression); \
        abort(); \
    } \
} while (0)

struct concurrency_test {
    pthread_mutex_t mutex;
    pthread_cond_t condition;
    int verifier_entered;
    int verifier_release;
    int claim_hook_enabled;
    int claim_entered;
    int claim_release;
    int latch_hook_enabled;
    int latch_entered;
    int latch_release;
    int lease_publish_hook_enabled;
    int lease_publish_entered;
    int lease_publish_release;
    unsigned verifier_calls;
    struct mt6897_ufs_gate gate;
    struct mt6897_ufs_gate_evidence evidence;
    struct mt6897_ufs_gate_lease lease;
    enum mt6897_ufs_gate_result result;
    uint64_t blockers;
};

static struct concurrency_test *claim_hook_test;
static struct concurrency_test *latch_hook_test;
static struct concurrency_test *lease_publish_hook_test;

void
mt6897_ufs_gate_test_after_claim(void)
{
    struct concurrency_test *test = claim_hook_test;

    if (test == 0 || !test->claim_hook_enabled) {
        return;
    }
    CHECK(pthread_mutex_lock(&test->mutex) == 0);
    test->claim_entered = 1;
    CHECK(pthread_cond_broadcast(&test->condition) == 0);
    while (!test->claim_release) {
        CHECK(pthread_cond_wait(&test->condition, &test->mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&test->mutex) == 0);
}

void
mt6897_ufs_gate_test_before_authorize_latch_publish(void)
{
    struct concurrency_test *test = latch_hook_test;

    if (test == 0 || !test->latch_hook_enabled) {
        return;
    }
    CHECK(pthread_mutex_lock(&test->mutex) == 0);
    test->latch_entered = 1;
    CHECK(pthread_cond_broadcast(&test->condition) == 0);
    while (!test->latch_release) {
        CHECK(pthread_cond_wait(&test->condition, &test->mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&test->mutex) == 0);
}

void
mt6897_ufs_gate_test_before_lease_publish(void)
{
    struct concurrency_test *test = lease_publish_hook_test;

    if (test == 0 || !test->lease_publish_hook_enabled) {
        return;
    }
    CHECK(pthread_mutex_lock(&test->mutex) == 0);
    test->lease_publish_entered = 1;
    CHECK(pthread_cond_broadcast(&test->condition) == 0);
    while (!test->lease_publish_release) {
        CHECK(pthread_cond_wait(&test->condition, &test->mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&test->mutex) == 0);
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

static void
make_valid_lease(const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
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
}

static enum mt6897_ufs_gate_verdict
blocking_verifier(void *opaque,
    const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    struct concurrency_test *test = (struct concurrency_test *)opaque;

    CHECK(pthread_mutex_lock(&test->mutex) == 0);
    ++test->verifier_calls;
    test->verifier_entered = 1;
    CHECK(pthread_cond_broadcast(&test->condition) == 0);
    while (!test->verifier_release) {
        CHECK(pthread_cond_wait(&test->condition, &test->mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&test->mutex) == 0);
    make_valid_lease(request, lease);
    return MT6897_UFS_GATE_VERIFY_APPROVE;
}

static void *
authorize_thread(void *opaque)
{
    struct concurrency_test *test = (struct concurrency_test *)opaque;

    test->result = mt6897_ufs_gate_authorize(&test->gate, &test->evidence,
        blocking_verifier, test, &test->lease, &test->blockers);
    return 0;
}

int
main(void)
{
    struct concurrency_test test = { 0 };
    struct concurrency_test late = { 0 };
    struct concurrency_test incomplete = { 0 };
    struct concurrency_test late_denial = { 0 };
    struct concurrency_test runtime_fault = { 0 };
    struct mt6897_ufs_gate_lease competing_lease = { 0 };
    struct mt6897_ufs_gate_lease late_competing_lease = { 0 };
    enum mt6897_ufs_gate_result competing_result;
    enum mt6897_ufs_gate_result late_competing_result;
    uint64_t competing_blockers = 0;
    uint64_t late_competing_blockers = 0;
    uint64_t late_check_blockers = 0;
    struct mt6897_ufs_gate_lease incomplete_competing_lease = { 0 };
    enum mt6897_ufs_gate_result incomplete_competing_result;
    uint64_t incomplete_competing_blockers = 0;
    struct mt6897_ufs_gate_lease late_denial_competing_lease = { 0 };
    enum mt6897_ufs_gate_result late_denial_competing_result;
    uint64_t late_denial_competing_blockers = 0;
    uint64_t runtime_fault_blockers = 0;
    uint64_t runtime_check_blockers = 0;
    pthread_t thread;

    CHECK(pthread_mutex_init(&test.mutex, 0) == 0);
    CHECK(pthread_cond_init(&test.condition, 0) == 0);
    test.evidence = mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    test.evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED |
        MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    test.evidence.known = test.evidence.asserted;
    CHECK(mt6897_ufs_gate_init(&test.gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(pthread_create(&thread, 0, authorize_thread, &test) == 0);

    CHECK(pthread_mutex_lock(&test.mutex) == 0);
    while (!test.verifier_entered) {
        CHECK(pthread_cond_wait(&test.condition, &test.mutex) == 0);
    }
    CHECK(test.verifier_calls == 1);
    CHECK(pthread_mutex_unlock(&test.mutex) == 0);

    competing_result = mt6897_ufs_gate_authorize(&test.gate,
        &test.evidence, blocking_verifier, &test, &competing_lease,
        &competing_blockers);
    CHECK(competing_result == MT6897_UFS_GATE_FAULT);
    CHECK(competing_blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&competing_lease));

    CHECK(pthread_mutex_lock(&test.mutex) == 0);
    CHECK(test.verifier_calls == 1);
    test.verifier_release = 1;
    CHECK(pthread_cond_broadcast(&test.condition) == 0);
    CHECK(pthread_mutex_unlock(&test.mutex) == 0);
    CHECK(pthread_join(thread, 0) == 0);

    CHECK(test.verifier_calls == 1);
    CHECK(test.result == MT6897_UFS_GATE_FAULT);
    CHECK(test.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&test.lease));
    CHECK(test.gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(test.gate.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(pthread_cond_destroy(&test.condition) == 0);
    CHECK(pthread_mutex_destroy(&test.mutex) == 0);

    /* Race a contender with the winner's final VERIFYING -> LEASED claim. */
    CHECK(pthread_mutex_init(&late.mutex, 0) == 0);
    CHECK(pthread_cond_init(&late.condition, 0) == 0);
    late.evidence = mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    late.evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED |
        MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    late.evidence.known = late.evidence.asserted;
    CHECK(mt6897_ufs_gate_init(&late.gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(pthread_create(&thread, 0, authorize_thread, &late) == 0);
    CHECK(pthread_mutex_lock(&late.mutex) == 0);
    while (!late.verifier_entered) {
        CHECK(pthread_cond_wait(&late.condition, &late.mutex) == 0);
    }
    CHECK(late.verifier_calls == 1);
    late.verifier_release = 1;
    CHECK(pthread_cond_broadcast(&late.condition) == 0);
    CHECK(pthread_mutex_unlock(&late.mutex) == 0);

    late_competing_result = mt6897_ufs_gate_authorize(&late.gate,
        &late.evidence, blocking_verifier, &late, &late_competing_lease,
        &late_competing_blockers);
    CHECK(late_competing_result == MT6897_UFS_GATE_FAULT);
    CHECK(late_competing_blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&late_competing_lease));
    CHECK(pthread_join(thread, 0) == 0);
    CHECK(late.verifier_calls == 1);
    CHECK(late.result == MT6897_UFS_GATE_LEASED ||
        late.result == MT6897_UFS_GATE_FAULT);
    if (late.result == MT6897_UFS_GATE_FAULT) {
        CHECK(late.blockers == MT6897_UFS_BLOCK_BAD_STATE);
        CHECK(lease_zero(&late.lease));
    }
    CHECK(late.gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(late.gate.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(mt6897_ufs_gate_lease_check(&late.gate, &late.lease,
        &late_check_blockers) == MT6897_UFS_GATE_FAULT);
    CHECK(late_check_blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(pthread_cond_destroy(&late.condition) == 0);
    CHECK(pthread_mutex_destroy(&late.mutex) == 0);

    /* A contender must win over an owner's incomplete-evidence denial. */
    CHECK(pthread_mutex_init(&incomplete.mutex, 0) == 0);
    CHECK(pthread_cond_init(&incomplete.condition, 0) == 0);
    incomplete.evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    incomplete.claim_hook_enabled = 1;
    claim_hook_test = &incomplete;
    CHECK(mt6897_ufs_gate_init(&incomplete.gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(pthread_create(&thread, 0, authorize_thread, &incomplete) == 0);
    CHECK(pthread_mutex_lock(&incomplete.mutex) == 0);
    while (!incomplete.claim_entered) {
        CHECK(pthread_cond_wait(&incomplete.condition,
            &incomplete.mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&incomplete.mutex) == 0);

    incomplete_competing_result = mt6897_ufs_gate_authorize(
        &incomplete.gate, &incomplete.evidence, blocking_verifier,
        &incomplete, &incomplete_competing_lease,
        &incomplete_competing_blockers);
    CHECK(incomplete_competing_result == MT6897_UFS_GATE_FAULT);
    CHECK(incomplete_competing_blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&incomplete_competing_lease));
    CHECK(pthread_mutex_lock(&incomplete.mutex) == 0);
    incomplete.claim_release = 1;
    CHECK(pthread_cond_broadcast(&incomplete.condition) == 0);
    CHECK(pthread_mutex_unlock(&incomplete.mutex) == 0);
    CHECK(pthread_join(thread, 0) == 0);
    claim_hook_test = 0;
    CHECK(incomplete.verifier_calls == 0);
    CHECK(incomplete.result == MT6897_UFS_GATE_FAULT);
    CHECK(incomplete.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(incomplete.gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(incomplete.gate.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&incomplete.lease));
    CHECK(pthread_cond_destroy(&incomplete.condition) == 0);
    CHECK(pthread_mutex_destroy(&incomplete.mutex) == 0);

    /* A contender after the owner's latch claim must override DENIED. */
    CHECK(pthread_mutex_init(&late_denial.mutex, 0) == 0);
    CHECK(pthread_cond_init(&late_denial.condition, 0) == 0);
    late_denial.evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    late_denial.latch_hook_enabled = 1;
    latch_hook_test = &late_denial;
    CHECK(mt6897_ufs_gate_init(&late_denial.gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(pthread_create(&thread, 0, authorize_thread, &late_denial) == 0);
    CHECK(pthread_mutex_lock(&late_denial.mutex) == 0);
    while (!late_denial.latch_entered) {
        CHECK(pthread_cond_wait(&late_denial.condition,
            &late_denial.mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&late_denial.mutex) == 0);
    late_denial_competing_result = mt6897_ufs_gate_authorize(
        &late_denial.gate, &late_denial.evidence, blocking_verifier,
        &late_denial, &late_denial_competing_lease,
        &late_denial_competing_blockers);
    CHECK(late_denial_competing_result == MT6897_UFS_GATE_FAULT);
    CHECK(late_denial_competing_blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&late_denial_competing_lease));
    CHECK(pthread_mutex_lock(&late_denial.mutex) == 0);
    late_denial.latch_release = 1;
    CHECK(pthread_cond_broadcast(&late_denial.condition) == 0);
    CHECK(pthread_mutex_unlock(&late_denial.mutex) == 0);
    CHECK(pthread_join(thread, 0) == 0);
    latch_hook_test = 0;
    CHECK(late_denial.verifier_calls == 0);
    CHECK(late_denial.result == MT6897_UFS_GATE_FAULT);
    CHECK(late_denial.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(late_denial.gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(late_denial.gate.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&late_denial.lease));
    CHECK(pthread_cond_destroy(&late_denial.condition) == 0);
    CHECK(pthread_mutex_destroy(&late_denial.mutex) == 0);

    /* A provider fault while the lease is publishing must remain terminal. */
    CHECK(pthread_mutex_init(&runtime_fault.mutex, 0) == 0);
    CHECK(pthread_cond_init(&runtime_fault.condition, 0) == 0);
    runtime_fault.evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    runtime_fault.evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED |
        MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    runtime_fault.evidence.known = runtime_fault.evidence.asserted;
    runtime_fault.lease_publish_hook_enabled = 1;
    lease_publish_hook_test = &runtime_fault;
    CHECK(mt6897_ufs_gate_init(&runtime_fault.gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(pthread_create(&thread, 0, authorize_thread, &runtime_fault) == 0);
    CHECK(pthread_mutex_lock(&runtime_fault.mutex) == 0);
    while (!runtime_fault.verifier_entered) {
        CHECK(pthread_cond_wait(&runtime_fault.condition,
            &runtime_fault.mutex) == 0);
    }
    runtime_fault.verifier_release = 1;
    CHECK(pthread_cond_broadcast(&runtime_fault.condition) == 0);
    while (!runtime_fault.lease_publish_entered) {
        CHECK(pthread_cond_wait(&runtime_fault.condition,
            &runtime_fault.mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&runtime_fault.mutex) == 0);
    CHECK(mt6897_ufs_gate_fault(&runtime_fault.gate,
        MT6897_UFS_BLOCK_PROVIDER_RUNTIME, &runtime_fault_blockers) ==
        MT6897_UFS_GATE_FAULT);
    CHECK(runtime_fault_blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(pthread_mutex_lock(&runtime_fault.mutex) == 0);
    runtime_fault.lease_publish_release = 1;
    CHECK(pthread_cond_broadcast(&runtime_fault.condition) == 0);
    CHECK(pthread_mutex_unlock(&runtime_fault.mutex) == 0);
    CHECK(pthread_join(thread, 0) == 0);
    lease_publish_hook_test = 0;
    CHECK(runtime_fault.verifier_calls == 1);
    CHECK(runtime_fault.result == MT6897_UFS_GATE_FAULT);
    CHECK(runtime_fault.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(runtime_fault.gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(runtime_fault.gate.blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(lease_zero(&runtime_fault.lease));
    CHECK(mt6897_ufs_gate_lease_check(&runtime_fault.gate,
        &runtime_fault.lease, &runtime_check_blockers) ==
        MT6897_UFS_GATE_FAULT);
    CHECK(runtime_check_blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(pthread_cond_destroy(&runtime_fault.condition) == 0);
    CHECK(pthread_mutex_destroy(&runtime_fault.mutex) == 0);

    (void)printf("%u MT6897 UFS concurrent authorization checks passed; "
        "verifier_calls=1 no MMIO/SMC/DMA calls\n",
        atomic_load_explicit(&checks, memory_order_relaxed));
    return 0;
}
