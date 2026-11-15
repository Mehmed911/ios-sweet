#include "mt6897_ufs_observer_xnu.h"
#include <stddef.h>
#ifdef MT6897_MODEL_FREESTANDING
extern void model_assert_fail(const char *, unsigned);
extern int printf(const char *, ...);
extern void *memset(void *, int, size_t);
extern int memcmp(const void *, const void *, size_t);
#define CHECK(e) do { if (!(e)) model_assert_fail(#e, __LINE__); } while (0)
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define CHECK(e) assert(e)
#endif

enum { BOOT = 0x1234, SLOT_A = 1, SLOT_B = 2 };
static struct fixture {
    struct mt6897_ufs_xnu_observer x;
    struct mt6897_ufs_read_grant grant;
    unsigned entry_slot, evidence_slot;
    uint64_t current_epoch;
    unsigned verifies, checks, maps, deny_verify, deny_at, revoke_at;
    unsigned revoke_verify, revoke_map, map_fail, map_alignment, map_overflow, reentrant;
    _Alignas(16) uint32_t reg[DUFS_MTK_HCI_BYTES / 4];
} f;
static unsigned cases;

static int verify(void *context, uint64_t boot, struct mt6897_ufs_read_grant *grant)
{
    CHECK(context == &f && boot == BOOT);
    ++f.verifies;
    if (f.revoke_verify) mt6897_ufs_observer_revoke(&f.x.provider);
    /* Test fixture only. The observed slot is independent of the record's
     * claim. The physical bootshim's FDT hint is not a source of authority. */
    if (f.deny_verify || f.entry_slot != SLOT_B || f.evidence_slot != f.entry_slot)
        return -1;
    *grant = f.grant;
    return 0;
}
static int check(void *context, const struct mt6897_ufs_read_grant *grant)
{
    CHECK(context == &f && grant->grant_id == 1);
    ++f.checks;
    if (f.reentrant) {
        struct dufs_register_snapshot other = { 0 };
        CHECK(mt6897_ufs_observer_capture(&f.x.provider, &other) == MUO_STATE);
    }
    if (f.checks == f.revoke_at) mt6897_ufs_observer_revoke(&f.x.provider);
    return grant->resource_epoch != f.current_epoch || f.checks == f.deny_at ? -1 : 0;
}
uintptr_t ml_io_map_with_prot(uintptr_t base, size_t bytes, int protection)
{
    CHECK(base == DUFS_MTK_HCI_BASE && bytes == DUFS_MTK_HCI_BYTES && protection == 1);
    CHECK(f.verifies == 1 && f.checks == 1 && f.x.read_calls == 0);
    ++f.maps;
    if (f.revoke_map) mt6897_ufs_observer_revoke(&f.x.provider);
    if (f.map_fail) return 0;
    if (f.map_alignment) return (uintptr_t)f.reg + 1;
    if (f.map_overflow) return UINTPTR_MAX & ~(uintptr_t)3;
    return (uintptr_t)f.reg; /* Synthetic MT6897 register bank, not physical MMIO. */
}
static void reset(void)
{
    memset(&f, 0, sizeof(f));
    f.entry_slot = f.evidence_slot = SLOT_B;
    f.current_epoch = 3;
    f.grant = (struct mt6897_ufs_read_grant){ .version = MUO_GRANT_VERSION, .rights = MUO_REQUIRED,
        .boot_id = BOOT, .grant_id = 1, .owner_id = 2, .resource_epoch = 3,
        .base = DUFS_MTK_HCI_BASE, .bytes = DUFS_MTK_HCI_BYTES };
    f.reg[0] = 0x55c7051f; f.reg[1] = 0x20007; f.reg[2] = 0x400;
    const struct mt6897_ufs_read_authority authority = { &f, verify, check };
    CHECK(mt6897_ufs_xnu_observer_bind(&f.x, BOOT, &authority) == 0);
    CHECK(!f.verifies && !f.checks && !f.maps && !f.x.read_calls);
}
static void run(int expected, unsigned maps, unsigned reads, uint32_t blockers)
{
    struct dufs_register_snapshot out, before;
    memset(&out, 0xa5, sizeof(out)); before = out;
    int result = mt6897_ufs_observer_capture(&f.x.provider, &out);
    CHECK(result == expected && f.maps == maps && f.x.read_calls == reads);
    if (result) CHECK(memcmp(&out, &before, sizeof(out)) == 0);
    else {
        CHECK(out.blockers == blockers && out.boot_id == BOOT && out.reads == reads);
        CHECK(out.profile == DUFS_SNAPSHOT_MT6897 && out.physical_base == DUFS_MTK_HCI_BASE);
        CHECK(out.first.queues == 8 && out.last.queues == 8);
    }
    printf("UFS OBSERVER case=%u status=%u maps=%u reads=%u checks=%u\n",
        ++cases, (unsigned)-result, f.maps, (unsigned)f.x.read_calls, f.checks);
}
int main(void)
{
    struct mt6897_ufs_xnu_observer disabled = { 0 };
    struct dufs_register_snapshot out = { 0 };
    CHECK(mt6897_ufs_observer_capture(&disabled.provider, &out) == MUO_DISABLED);
    CHECK(!disabled.mapping && !disabled.map_calls && !disabled.read_calls);
    CHECK(mt6897_ufs_xnu_observer_bind(&disabled, BOOT, 0) == MUO_ARGUMENT);
    CHECK(mt6897_ufs_observer_capture(&disabled.provider, &out) == MUO_DISABLED);
    disabled.provider.state = MUO_BOUND; /* Corrupt state must not call NULL. */
    CHECK(mt6897_ufs_observer_capture(&disabled.provider, &out) == MUO_ARGUMENT);
    reset(); run(0, 1, 316, 0); CHECK(f.checks == 318);
    CHECK(mt6897_ufs_observer_capture(&f.x.provider, &out) == MUO_STATE);
    const struct mt6897_ufs_read_authority authority = { &f, verify, check };
    CHECK(mt6897_ufs_xnu_observer_bind(&f.x, BOOT, &authority) == MUO_STATE);
    struct mt6897_ufs_xnu_observer stale = { 0 };
    stale.provider.grant.version = 1;
    CHECK(mt6897_ufs_xnu_observer_bind(&stale, BOOT, &authority) == MUO_STATE);
    reset(); f.reg[0x34 / 4] = 1; f.reg[0x300 / 4] = 1;
    f.reg[0x400 / 4] = f.reg[0x420 / 4] = 0x8000001f;
    f.reg[0x404 / 4] = 0x60002000; f.reg[0x424 / 4] = 0x60003000;
    run(0, 1, 316, DUFS_SNAPSHOT_HCE_ACTIVE | DUFS_SNAPSHOT_MCQ_ENABLED | DUFS_SNAPSHOT_LISTS_CONFIGURED);
    reset(); f.reentrant = 1; run(0, 1, 316, 0); CHECK(f.verifies == 1 && f.maps == 1);
    reset(); f.deny_verify = 1; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.boot_id++; run(MUO_DENIED, 0, 0, 0); CHECK(f.checks == 0);
    reset(); f.entry_slot = SLOT_A; run(MUO_DENIED, 0, 0, 0); CHECK(f.checks == 0);
    reset(); f.evidence_slot = SLOT_A; run(MUO_DENIED, 0, 0, 0); CHECK(f.checks == 0);
    reset(); f.current_epoch++; run(MUO_DENIED, 0, 0, 0); CHECK(f.checks == 1);
    for (unsigned bit = 0; bit < 6; ++bit) {
        reset(); f.grant.rights &= ~(1u << bit); run(MUO_DENIED, 0, 0, 0);
    }
    reset(); f.grant.rights |= 0x40; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.version++; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.base += 4; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.bytes -= 4; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.owner_id = 0; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.grant_id = 0; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.resource_epoch = 0; run(MUO_DENIED, 0, 0, 0);
    reset(); f.grant.reserved = 1; run(MUO_DENIED, 0, 0, 0);
    reset(); f.revoke_verify = 1; run(MUO_REVOKED, 0, 0, 0);
    reset(); f.revoke_map = 1; run(MUO_REVOKED, 1, 0, 0);
    reset(); f.map_fail = 1; run(MUO_MAP, 1, 0, 0);
    reset(); f.map_alignment = 1; run(MUO_MAP, 1, 0, 0);
    reset(); f.map_overflow = 1; run(MUO_MAP, 1, 0, 0);
    reset(); f.reg[2] = 0; run(MUO_LAYOUT, 1, 2, 0);
    for (unsigned i = 1; i <= 318; ++i) {
        reset(); f.deny_at = i;
        struct dufs_register_snapshot sample, before;
        memset(&sample, 0xa5, sizeof(sample)); before = sample;
        CHECK(mt6897_ufs_observer_capture(&f.x.provider, &sample) == MUO_DENIED);
        CHECK(f.maps == (i > 1) && f.x.read_calls == (i > 1 ? i - 2 : 0) && f.checks == i);
        CHECK(memcmp(&sample, &before, sizeof(sample)) == 0);
        reset(); f.revoke_at = i;
        memset(&sample, 0xa5, sizeof(sample)); before = sample;
        CHECK(mt6897_ufs_observer_capture(&f.x.provider, &sample) == MUO_REVOKED);
        CHECK(f.maps == (i > 1) && f.x.read_calls == (i > 1 ? i - 2 : 0) && f.checks == i);
        CHECK(memcmp(&sample, &before, sizeof(sample)) == 0);
    }
    printf("UFS OBSERVER authority_failures=%u revocations=%u no_later_read=1\n", 318u, 318u);
    printf("UFS OBSERVER PASS cases=%u physical_access=0\n", cases);
    return 0;
}
