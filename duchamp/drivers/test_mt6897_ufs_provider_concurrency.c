#include "mt6897_ufs_provider.h"

#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BOOT_GENERATION UINT64_C(0x202611030102)

static _Atomic unsigned checks;
#define CHECK(expression) do { \
    (void)atomic_fetch_add_explicit(&checks, 1, memory_order_relaxed); \
    if (!(expression)) { \
        (void)fprintf(stderr, "line %u: check failed: %s\n", \
            __LINE__, #expression); \
        abort(); \
    } \
} while (0)

struct provider_race {
    pthread_mutex_t mutex;
    pthread_cond_t condition;
    int hook_entered;
    int hook_release;
    unsigned verifier_calls;
    unsigned dispatch_calls;
    struct mt6897_ufs_gate gate;
    struct mt6897_ufs_gate_lease lease;
    struct mt6897_ufs_provider provider;
    enum mt6897_ufs_provider_result result;
    uint64_t result_value;
    uint64_t blockers;
};

static struct provider_race *active_race;

void
mt6897_ufs_provider_test_after_lease_check(void)
{
    struct provider_race *race = active_race;

    if (race == 0) {
        return;
    }
    CHECK(pthread_mutex_lock(&race->mutex) == 0);
    race->hook_entered = 1;
    CHECK(pthread_cond_broadcast(&race->condition) == 0);
    while (!race->hook_release) {
        CHECK(pthread_cond_wait(&race->condition, &race->mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&race->mutex) == 0);
}

static enum mt6897_ufs_gate_verdict
approve_lease(void *context,
    const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    struct provider_race *race = (struct provider_race *)context;

    ++race->verifier_calls;
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
dispatch(void *context, const struct mt6897_ufs_provider_request *request,
    uint64_t *result_out)
{
    struct provider_race *race = (struct provider_race *)context;

    (void)request;
    ++race->dispatch_calls;
    *result_out = 1;
    return 0;
}

static void *
command_thread(void *context)
{
    struct provider_race *race = (struct provider_race *)context;

    race->result = mt6897_ufs_provider_command(&race->provider, 0x28, 0,
        0, 1, &race->result_value, &race->blockers);
    return 0;
}

int
main(void)
{
    struct provider_race race = { 0 };
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    const struct mt6897_ufs_provider_ops ops = {
        .context = &race,
        .dispatch = dispatch
    };
    pthread_t thread;
    uint64_t result = 0;
    uint64_t blockers = 0;

    evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED |
        MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    evidence.known = evidence.asserted;
    CHECK(pthread_mutex_init(&race.mutex, 0) == 0);
    CHECK(pthread_cond_init(&race.condition, 0) == 0);
    CHECK(mt6897_ufs_gate_init(&race.gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&race.gate, &evidence, approve_lease,
        &race, &race.lease, &blockers) == MT6897_UFS_GATE_LEASED);
    CHECK(race.verifier_calls == 1);
    CHECK(mt6897_ufs_provider_bind(&race.provider, &race.gate, &race.lease,
        &ops, &blockers) == MT6897_UFS_PROVIDER_OK);

    active_race = &race;
    CHECK(pthread_create(&thread, 0, command_thread, &race) == 0);
    CHECK(pthread_mutex_lock(&race.mutex) == 0);
    while (!race.hook_entered) {
        CHECK(pthread_cond_wait(&race.condition, &race.mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&race.mutex) == 0);

    CHECK(mt6897_ufs_provider_fault(&race.provider,
        MT6897_UFS_BLOCK_PROVIDER_RUNTIME, &blockers) ==
        MT6897_UFS_PROVIDER_FAULTED);
    CHECK(race.dispatch_calls == 0);

    CHECK(pthread_mutex_lock(&race.mutex) == 0);
    race.hook_release = 1;
    CHECK(pthread_cond_broadcast(&race.condition) == 0);
    CHECK(pthread_mutex_unlock(&race.mutex) == 0);
    CHECK(pthread_join(thread, 0) == 0);
    active_race = 0;

    CHECK(race.result == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(race.provider.state == MT6897_UFS_PROVIDER_STATE_FAULTED);
    CHECK(race.provider.dispatches == 0);
    CHECK(race.dispatch_calls == 0);
    CHECK((race.blockers & MT6897_UFS_BLOCK_PROVIDER_RUNTIME) != 0);
    CHECK(mt6897_ufs_provider_power(&race.provider, 1, &result,
        &blockers) == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(mt6897_ufs_provider_clock(&race.provider, 0, 0, 1, &result,
        &blockers) == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(mt6897_ufs_provider_phy(&race.provider, 1, &result,
        &blockers) == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(mt6897_ufs_provider_mmio(&race.provider, 1, 0, 0, &result,
        &blockers) == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(mt6897_ufs_provider_dma(&race.provider, 1, 0, 4096, &result,
        &blockers) == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(mt6897_ufs_provider_command(&race.provider, 0, 0, 0, 0,
        &result, &blockers) == MT6897_UFS_PROVIDER_FAULTED);
    CHECK(race.dispatch_calls == 0);
    CHECK(race.provider.dispatches == 0);

    CHECK(pthread_cond_destroy(&race.condition) == 0);
    CHECK(pthread_mutex_destroy(&race.mutex) == 0);
    (void)printf("%u MT6897 UFS concurrent provider checks passed; "
        "fault_before_dispatch=1 dispatches=0\n",
        atomic_load_explicit(&checks, memory_order_relaxed));
    return 0;
}
