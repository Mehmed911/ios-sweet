#include "mt6897_ufs_dma_route.h"

#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BOOT_GENERATION UINT64_C(0x202611040302)

static _Atomic unsigned checks;
#define CHECK(expression) do { \
    (void)atomic_fetch_add_explicit(&checks, 1, memory_order_relaxed); \
    if (!(expression)) { \
        (void)fprintf(stderr, "line %u: check failed: %s\n", \
            __LINE__, #expression); \
        abort(); \
    } \
} while (0)

struct route_race {
    pthread_mutex_t mutex;
    pthread_cond_t condition;
    int hook_entered;
    int hook_release;
    unsigned lease_verifier_calls;
    unsigned receipt_verifier_calls;
    unsigned copy_to_calls;
    unsigned copy_from_calls;
    struct mt6897_ufs_gate gate;
    struct mt6897_ufs_gate_lease lease;
    struct mt6897_ufs_dma_route route;
    struct mt6897_ufs_dma_route_request request;
    struct mt6897_ufs_dma_route_mapping mapping;
    enum mt6897_ufs_dma_route_result result;
    uint64_t blockers;
};

static struct route_race *active_race;
_Alignas(64) static unsigned char source_buffer[256];
_Alignas(64) static unsigned char bounce_buffer[256];

void
mt6897_ufs_dma_route_test_after_lease_check(void)
{
    struct route_race *race = active_race;

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
    struct route_race *race = (struct route_race *)context;

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
    const struct mt6897_ufs_dma_route_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease)
{
    struct route_race *race = (struct route_race *)context;

    CHECK(receipt->dma_owner_id == lease->dma_owner_id);
    CHECK(receipt->cache_owner_id == lease->cache_owner_id);
    ++race->receipt_verifier_calls;
    return 0;
}

static int
copy_to(void *context, uint64_t destination, uint64_t source, uint64_t bytes)
{
    struct route_race *race = (struct route_race *)context;

    (void)destination;
    (void)source;
    (void)bytes;
    ++race->copy_to_calls;
    return 0;
}

static int
copy_from(void *context, uint64_t destination, uint64_t source,
    uint64_t bytes)
{
    struct route_race *race = (struct route_race *)context;

    (void)destination;
    (void)source;
    (void)bytes;
    ++race->copy_from_calls;
    return 0;
}

static void *
handoff_thread(void *context)
{
    struct route_race *race = (struct route_race *)context;

    race->result = mt6897_ufs_dma_route_for_device(&race->route,
        &race->request, &race->mapping, &race->blockers);
    return 0;
}

int
main(void)
{
    struct route_race race = { 0 };
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    struct mt6897_ufs_dma_route_receipt receipt = { 0 };
    const struct mt6897_ufs_dma_route_ops ops = {
        &race, verify_receipt, copy_to, copy_from
    };
    pthread_t thread;
    uint64_t blockers = 0;

    evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED |
        MT6897_UFS_E_BOUNCE_REQUIRED |
        MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP;
    evidence.known = evidence.asserted;
    evidence.bounce_start = UINT64_C(0x400000000);
    evidence.bounce_size = sizeof(bounce_buffer);
    evidence.bounce_owner_id = UINT64_C(0x9909);
    CHECK(pthread_mutex_init(&race.mutex, 0) == 0);
    CHECK(pthread_cond_init(&race.condition, 0) == 0);
    CHECK(mt6897_ufs_gate_init(&race.gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&race.gate, &evidence, approve_lease,
        &race, &race.lease, &blockers) == MT6897_UFS_GATE_LEASED);
    CHECK(race.lease_verifier_calls == 1);

    receipt.version = MT6897_UFS_DMA_ROUTE_CONTRACT_VERSION;
    receipt.flags = MT6897_UFS_DMA_BOUNCE_FLAGS;
    receipt.route = MT6897_UFS_DMA_ROUTE_BOUNCE_POOL;
    receipt.bounce_disposition = MT6897_UFS_DMA_BOUNCE_REQUIRED;
    receipt.boot_generation = race.lease.boot_generation;
    receipt.dma_owner_id = race.lease.dma_owner_id;
    receipt.cache_owner_id = race.lease.cache_owner_id;
    receipt.controller_owner_id = race.lease.controller_owner_id;
    receipt.firmware_owner_id = race.lease.firmware_owner_id;
    receipt.source_owner_id = UINT64_C(0x8808);
    receipt.source_cpu_begin = (uint64_t)(uintptr_t)source_buffer;
    receipt.source_pa_begin = UINT64_C(0x100000000);
    receipt.source_bytes = sizeof(source_buffer);
    receipt.dma_limit = MT6897_UFS_DUCHAMP_DMA_LIMIT;
    receipt.dma_address_bits = MT6897_UFS_DUCHAMP_DMA_BITS;
    receipt.alignment = 64;
    receipt.translation_implementation_id = UINT64_C(0xd0010001);
    receipt.firewall_receipt_id = UINT64_C(0xf0010002);
    receipt.cache_contract_id = UINT64_C(0xca000003);
    receipt.bounce_owner_id = UINT64_C(0x9909);
    receipt.bounce_cpu_begin = (uint64_t)(uintptr_t)bounce_buffer;
    receipt.bounce_pa_begin = UINT64_C(0x300000000);
    receipt.bounce_dma_begin = UINT64_C(0x400000000);
    receipt.bounce_bytes = sizeof(bounce_buffer);
    receipt.copy_to_implementation_id = UINT64_C(0xc0700004);
    receipt.copy_from_implementation_id = UINT64_C(0xc0f00005);
    CHECK(mt6897_ufs_dma_route_bind(&race.route, &race.gate, &race.lease,
        &receipt, &ops, &blockers) == MT6897_UFS_DMA_ROUTE_OK);
    CHECK(race.receipt_verifier_calls == 1);
    CHECK(race.copy_to_calls == 0 && race.copy_from_calls == 0);

    race.request.cpu_address = (uint64_t)(uintptr_t)source_buffer;
    race.request.physical_address = UINT64_C(0x100000000);
    race.request.bytes = sizeof(source_buffer);
    race.request.direction = MT6897_UFS_DMA_BIDIRECTIONAL;
    active_race = &race;
    CHECK(pthread_create(&thread, 0, handoff_thread, &race) == 0);
    CHECK(pthread_mutex_lock(&race.mutex) == 0);
    while (!race.hook_entered) {
        CHECK(pthread_cond_wait(&race.condition, &race.mutex) == 0);
    }
    CHECK(pthread_mutex_unlock(&race.mutex) == 0);

    CHECK(mt6897_ufs_dma_route_fault(&race.route,
        MT6897_UFS_BLOCK_PROVIDER_RUNTIME, &blockers) ==
        MT6897_UFS_DMA_ROUTE_FAULTED);
    CHECK(race.receipt_verifier_calls == 1);
    CHECK(race.copy_to_calls == 0 && race.copy_from_calls == 0);

    CHECK(pthread_mutex_lock(&race.mutex) == 0);
    race.hook_release = 1;
    CHECK(pthread_cond_broadcast(&race.condition) == 0);
    CHECK(pthread_mutex_unlock(&race.mutex) == 0);
    CHECK(pthread_join(thread, 0) == 0);
    active_race = 0;

    CHECK(race.result == MT6897_UFS_DMA_ROUTE_FAULTED);
    CHECK(race.route.state == MT6897_UFS_DMA_ROUTE_STATE_FAULTED);
    CHECK(race.route.transitions == 0);
    CHECK(race.mapping.cookie == 0);
    CHECK(race.receipt_verifier_calls == 1);
    CHECK(race.copy_to_calls == 0 && race.copy_from_calls == 0);
    CHECK((race.blockers & MT6897_UFS_BLOCK_PROVIDER_RUNTIME) != 0);
    CHECK(mt6897_ufs_dma_route_for_device(&race.route, &race.request,
        &race.mapping, &blockers) == MT6897_UFS_DMA_ROUTE_FAULTED);
    CHECK(mt6897_ufs_dma_route_for_cpu(&race.route, &race.mapping,
        &blockers) == MT6897_UFS_DMA_ROUTE_FAULTED);
    CHECK(race.copy_to_calls == 0 && race.copy_from_calls == 0);

    CHECK(pthread_cond_destroy(&race.condition) == 0);
    CHECK(pthread_mutex_destroy(&race.mutex) == 0);
    (void)printf("%u MT6897 UFS concurrent DMA-route checks passed; "
        "fault_before_route_callback=1 copy_callbacks=0\n",
        atomic_load_explicit(&checks, memory_order_relaxed));
    return 0;
}
