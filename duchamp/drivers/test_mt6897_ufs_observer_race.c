#include "mt6897_ufs_observer.h"
#include <assert.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>

enum { BEFORE_MAP = 1, IN_MAP, IN_READ, BEFORE_PUBLISH };
struct race {
    pthread_mutex_t lock;
    pthread_cond_t changed;
    unsigned phase, blocked, release, verifies, checks, maps, reads;
    struct mt6897_ufs_observer provider;
    struct dufs_register_snapshot output, before;
    uint32_t reg[DUFS_MTK_HCI_BYTES / 4];
    int result;
};
static void pause_at(struct race *r, unsigned phase)
{
    if (r->phase != phase) return;
    assert(!pthread_mutex_lock(&r->lock));
    r->blocked = 1;
    assert(!pthread_cond_broadcast(&r->changed));
    while (!r->release) assert(!pthread_cond_wait(&r->changed, &r->lock));
    assert(!pthread_mutex_unlock(&r->lock));
}
static int verify(void *context, uint64_t boot, struct mt6897_ufs_read_grant *grant)
{
    struct race *r = context;
    ++r->verifies;
    *grant = (struct mt6897_ufs_read_grant){ .version = 1, .rights = MUO_REQUIRED,
        .boot_id = boot, .grant_id = 1, .owner_id = 2, .resource_epoch = 3,
        .base = DUFS_MTK_HCI_BASE, .bytes = DUFS_MTK_HCI_BYTES };
    return 0;
}
static int check(void *context, const struct mt6897_ufs_read_grant *grant)
{
    struct race *r = context;
    assert(grant->boot_id == 0x1234);
    ++r->checks;
    if (r->checks == 1) pause_at(r, BEFORE_MAP);
    if (r->checks == 318) pause_at(r, BEFORE_PUBLISH);
    return 0;
}
static uintptr_t map(void *context, uint64_t base, uint32_t bytes)
{
    struct race *r = context;
    assert(base == DUFS_MTK_HCI_BASE && bytes == DUFS_MTK_HCI_BYTES);
    ++r->maps;
    pause_at(r, IN_MAP);
    return (uintptr_t)r->reg;
}
static int read32(void *context, uintptr_t mapping, uint32_t offset, uint32_t *value)
{
    struct race *r = context;
    assert(mapping == (uintptr_t)r->reg);
    ++r->reads;
    pause_at(r, IN_READ);
    *value = r->reg[offset / 4];
    return 0;
}
static void *worker(void *context)
{
    struct race *r = context;
    r->result = mt6897_ufs_observer_capture(&r->provider, &r->output);
    return 0;
}
static void run(unsigned phase, unsigned expected_maps, unsigned expected_reads)
{
    struct race r = { .phase = phase };
    assert(!pthread_mutex_init(&r.lock, 0));
    assert(!pthread_cond_init(&r.changed, 0));
    r.reg[0] = 1u << 30; r.reg[1] = 0x20007; r.reg[2] = 0x400;
    memset(&r.output, 0xa5, sizeof(r.output)); r.before = r.output;
    const struct mt6897_ufs_read_authority authority = { &r, verify, check };
    const struct mt6897_ufs_observer_bus bus = { &r, map, read32 };
    assert(mt6897_ufs_observer_bind(&r.provider, 0x1234, &authority, &bus) == 0);
    pthread_t thread;
    assert(!pthread_create(&thread, 0, worker, &r));
    assert(!pthread_mutex_lock(&r.lock));
    while (!r.blocked) assert(!pthread_cond_wait(&r.changed, &r.lock));
    assert(!pthread_mutex_unlock(&r.lock));
    struct dufs_register_snapshot second = { 0 };
    assert(mt6897_ufs_observer_capture(&r.provider, &second) == MUO_STATE);
    mt6897_ufs_observer_revoke(&r.provider);
    assert(!pthread_mutex_lock(&r.lock));
    r.release = 1;
    assert(!pthread_cond_broadcast(&r.changed));
    assert(!pthread_mutex_unlock(&r.lock));
    assert(!pthread_join(thread, 0));
    assert(r.result == MUO_REVOKED && r.verifies == 1 && r.maps == expected_maps && r.reads == expected_reads);
    assert(!memcmp(&r.output, &r.before, sizeof(r.output)));
    assert(mt6897_ufs_observer_capture(&r.provider, &second) == MUO_REVOKED);
    assert(!pthread_cond_destroy(&r.changed));
    assert(!pthread_mutex_destroy(&r.lock));
    printf("UFS OBSERVER RACE phase=%u maps=%u reads=%u output_unchanged=1\n", phase, r.maps, r.reads);
}
int main(void)
{
    run(BEFORE_MAP, 0, 0);
    run(IN_MAP, 1, 0);
    run(IN_READ, 1, 1);
    run(BEFORE_PUBLISH, 1, 316);
    puts("UFS OBSERVER RACE PASS cases=4");
    return 0;
}
