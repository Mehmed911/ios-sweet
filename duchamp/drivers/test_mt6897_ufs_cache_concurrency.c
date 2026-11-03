#include "mt6897_ufs_cache.h"

#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BOOT_GENERATION UINT64_C(0x202611030202)

static _Atomic unsigned checks;
#define CHECK(expression) do { \
    (void)atomic_fetch_add_explicit(&checks, 1, memory_order_relaxed); \
    if (!(expression)) { \
        (void)fprintf(stderr, "line %u: check failed: %s\n", \
            __LINE__, #expression); \
        abort(); \
    } \
} while (0)

struct cache_race {
    pthread_mutex_t mutex;
    pthread_cond_t condition;
    int hook_entered;
    int hook_release;
    unsigned lease_verifier_calls;
    unsigned receipt_verifier_calls;
    unsigned range_calls;
    unsigned barrier_calls;
    struct mt6897_ufs_gate gate;
    struct mt6897_ufs_gate_lease lease;
    struct mt6897_ufs_cache cache;
    enum mt6897_ufs_cache_result result;
    uint64_t blockers;
};

static struct cache_race *active_race;
_Alignas(64) static unsigned char cache_range[256];

void
mt6897_ufs_cache_test_after_lease_check(void)
{
    struct cache_race *race = active_race;

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
    struct cache_race *race = (struct cache_race *)context;

    ++race->lease_verifier_calls;
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
    return MT6897_UFS_GATE_VERIFY_APPROVE;
}

static int
verify_receipt(void *context,
    const struct mt6897_ufs_cache_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease)
{
    struct cache_race *race = (struct cache_race *)context;

    CHECK(receipt->cache_owner_id == lease->cache_owner_id);
    ++race->receipt_verifier_calls;
    return 0;
}

static int
range_callback(void *context, uint64_t cpu, uint64_t physical,
    uint64_t bytes, enum mt6897_ufs_cache_direction direction)
{
    struct cache_race *race = (struct cache_race *)context;

    (void)cpu;
    (void)physical;
    (void)bytes;
    (void)direction;
    ++race->range_calls;
    return 0;
}

static int
barrier_callback(void *context,
    enum mt6897_ufs_cache_barrier_phase phase,
    enum mt6897_ufs_cache_direction direction)
{
    struct cache_race *race = (struct cache_race *)context;

    (void)phase;
    (void)direction;
    ++race->barrier_calls;
    return 0;
}

static void *
handoff_thread(void *context)
{
    struct cache_race *race = (struct cache_race *)context;

    race->result = mt6897_ufs_cache_for_device(&race->cache,
        MT6897_UFS_CACHE_BIDIRECTIONAL, &race->blockers);
    return 0;
}

int
main(void)
{
    struct cache_race race = { 0 };
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    struct mt6897_ufs_cache_receipt receipt = { 0 };
    const struct mt6897_ufs_cache_ops ops = {
        &race, verify_receipt, range_callback, range_callback,
        barrier_callback
    };
    pthread_t thread;
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
    CHECK(race.lease_verifier_calls == 1);

    receipt.version = MT6897_UFS_CACHE_CONTRACT_VERSION;
    receipt.flags = MT6897_UFS_CACHE_REQUIRED_FLAGS;
    receipt.boot_generation = race.lease.boot_generation;
    receipt.cache_owner_id = race.lease.cache_owner_id;
    receipt.range_owner_id = UINT64_C(0x8808);
    receipt.cpu_address = (uint64_t)(uintptr_t)cache_range;
    receipt.physical_address = UINT64_C(0x100000000);
    receipt.bytes = sizeof(cache_range);
    receipt.cache_line_size = 64;
    receipt.clean_implementation_id = UINT64_C(0xc1ea0001);
    receipt.flush_implementation_id = UINT64_C(0xf1050002);
    receipt.barrier_implementation_id = UINT64_C(0xba220003);
    CHECK(mt6897_ufs_cache_bind(&race.cache, &race.gate, &race.lease,
        &receipt, &ops, &blockers) == MT6897_UFS_CACHE_OK);
    CHECK(race.receipt_verifier_calls == 1);
    CHECK(race.range_calls == 0 && race.barrier_calls == 0);

    active_race = &race;
    CHECK(pthread_create(&thread, 0, handoff_thread, &race) == 0);
    CHECK(pthread_mutex_lock(&race.mutex) == 0);
    while (!race.hook_entered) {
        CHECK(pthread_cond_wait(&race.condition, &race.mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&race.mutex) == 0);

    CHECK(mt6897_ufs_cache_fault(&race.cache,
        MT6897_UFS_BLOCK_PROVIDER_RUNTIME, &blockers) ==
        MT6897_UFS_CACHE_FAULTED);
    CHECK(race.receipt_verifier_calls == 1);
    CHECK(race.range_calls == 0 && race.barrier_calls == 0);

    CHECK(pthread_mutex_lock(&race.mutex) == 0);
    race.hook_release = 1;
    CHECK(pthread_cond_broadcast(&race.condition) == 0);
    CHECK(pthread_mutex_unlock(&race.mutex) == 0);
    CHECK(pthread_join(thread, 0) == 0);
    active_race = 0;

    CHECK(race.result == MT6897_UFS_CACHE_FAULTED);
    CHECK(race.cache.state == MT6897_UFS_CACHE_STATE_FAULTED);
    CHECK(race.cache.transitions == 0);
    CHECK(race.receipt_verifier_calls == 1);
    CHECK(race.range_calls == 0 && race.barrier_calls == 0);
    CHECK((race.blockers & MT6897_UFS_BLOCK_PROVIDER_RUNTIME) != 0);
    CHECK(mt6897_ufs_cache_for_device(&race.cache,
        MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
        MT6897_UFS_CACHE_FAULTED);
    CHECK(mt6897_ufs_cache_for_cpu(&race.cache,
        MT6897_UFS_CACHE_BIDIRECTIONAL, &blockers) ==
        MT6897_UFS_CACHE_FAULTED);
    CHECK(race.range_calls == 0 && race.barrier_calls == 0);

    CHECK(pthread_cond_destroy(&race.condition) == 0);
    CHECK(pthread_mutex_destroy(&race.mutex) == 0);
    (void)printf("%u MT6897 UFS concurrent cache checks passed; "
        "fault_before_cache_callback=1 range_callbacks=0\n",
        atomic_load_explicit(&checks, memory_order_relaxed));
    return 0;
}
