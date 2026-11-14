/* Register-array cases run identically under sanitizers and ARM64 QEMU.
 * DUCHAMP_SNAPSHOT_QEMU_DEVICE also reads the real QEMU PCI UFS device.
 */
#include "ufs_register_snapshot.h"
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

static struct fixture {
    uint32_t reg[DUFS_MTK_HCI_BYTES / 4];
    unsigned reads, permits, deny_after, fail_at, cap_reads, mutate;
    uint32_t runtime, config;
} f;
static unsigned cases;
static int permit(void *context, uint64_t boot, uint64_t base, uint32_t size)
{
    struct fixture *v = context;
    CHECK(boot == 0x1234 && base == DUFS_MTK_HCI_BASE && size == DUFS_MTK_HCI_BYTES);
    ++v->permits;
    return v->permits >= v->deny_after ? -1 : 0;
}
static int read32(void *context, uint32_t offset, uint32_t *value)
{
    struct fixture *v = context;
    CHECK(!(offset & 3) && offset < sizeof(v->reg));
    if (++v->reads == v->fail_at) return -1;
    if (offset == 0 && ++v->cap_reads == 2 && v->mutate)
        v->reg[0x34 / 4] = 1;
    *value = v->reg[offset / 4];
    return 0;
}
static struct dufs_snapshot_source reset(void)
{
    memset(&f, 0, sizeof(f));
    f.deny_after = UINT32_MAX;
    f.runtime = DUFS_MTK_MCQ_RUNTIME;
    f.config = 0x400;
    f.reg[0] = 1u << 30;
    f.reg[1] = 0x20007;
    f.reg[2] = 0x400;
    for (unsigned i = 0; i < 8; ++i) {
        uint32_t c = f.config + i * DUFS_MCQ_CONFIG_STRIDE;
        uint32_t o = f.runtime + i * DUFS_MCQ_STRIDE;
        f.reg[(c + 0xc) / 4] = o;
        f.reg[(c + 0x10) / 4] = o + DUFS_MCQ_SQ_IS;
        f.reg[(c + 0x2c) / 4] = o + DUFS_MCQ_CQ_HEAD;
        f.reg[(c + 0x30) / 4] = o + DUFS_MCQ_CQ_IS;
    }
    return (struct dufs_snapshot_source) { .context = &f, .allow_read = permit,
        .read32 = read32, .boot_id = 0x1234, .physical_base = DUFS_MTK_HCI_BASE,
        .bytes = DUFS_MTK_HCI_BYTES, .profile = DUFS_SNAPSHOT_MT6897 };
}
static void check_case(struct dufs_snapshot_source *source, int expected,
    uint32_t expected_blockers)
{
    struct dufs_register_snapshot output, before;
    memset(&output, 0xa5, sizeof(output)); before = output;
    int result = dufs_snapshot_registers(source, &output);
    CHECK(result == expected);
    if (result) CHECK(memcmp(&output, &before, sizeof(output)) == 0);
    else {
        CHECK(output.blockers == expected_blockers);
        CHECK(output.boot_id == source->boot_id && output.reads == f.reads);
        CHECK(output.first.queues <= 8 && output.last.queues <= 8);
    }
    printf("UFS SNAPSHOT case=%u status=%u blockers=%u reads=%u\n",
        ++cases, (unsigned)-result, expected_blockers, f.reads);
}
static void enabled_queue(unsigned i)
{
    unsigned c = f.config + i * DUFS_MCQ_CONFIG_STRIDE;
    f.reg[c / 4] = f.reg[(c + 0x20) / 4] = 0x8000001f;
    f.reg[(c + 4) / 4] = 0x60000000;
    f.reg[(c + 0x24) / 4] = 0x60001000;
}
static void model_cases(void)
{
    struct dufs_snapshot_source s = reset(); check_case(&s, 0, 0);
    unsigned full_reads = f.reads;
    s = reset(); f.reg[0] = 0; check_case(&s, 0, 0); CHECK(f.reads == 24);
    s = reset(); f.reg[0x34 / 4] = 3; check_case(&s, 0, DUFS_SNAPSHOT_HCE_ACTIVE);
    s = reset(); f.reg[0x60 / 4] = 1; check_case(&s, 0, DUFS_SNAPSHOT_LEGACY_RUNNING);
    s = reset(); f.reg[0x58 / 4] = 1; check_case(&s, 0, DUFS_SNAPSHOT_LEGACY_PENDING);
    s = reset(); f.reg[0x78 / 4] = 1; check_case(&s, 0, DUFS_SNAPSHOT_LEGACY_PENDING);
    s = reset(); f.reg[0x50 / 4] = 0x60000000; check_case(&s, 0, DUFS_SNAPSHOT_LISTS_CONFIGURED);
    s = reset(); f.reg[0x300 / 4] = 1; check_case(&s, 0, DUFS_SNAPSHOT_MCQ_ENABLED);
    s = reset(); enabled_queue(0);
    check_case(&s, 0, DUFS_SNAPSHOT_MCQ_ENABLED | DUFS_SNAPSHOT_LISTS_CONFIGURED);
    s = reset(); enabled_queue(0); f.reg[(f.runtime + 4) / 4] = 32;
    check_case(&s, 0, DUFS_SNAPSHOT_MCQ_ENABLED | DUFS_SNAPSHOT_LISTS_CONFIGURED | DUFS_SNAPSHOT_MCQ_PENDING);
    s = reset(); enabled_queue(0); f.reg[(f.runtime + 0x20) / 4] = 32;
    check_case(&s, 0, DUFS_SNAPSHOT_MCQ_ENABLED | DUFS_SNAPSHOT_LISTS_CONFIGURED | DUFS_SNAPSHOT_MCQ_PENDING);
    s = reset(); f.reg[(f.runtime + 0x24) / 4] = 1; check_case(&s, 0, DUFS_SNAPSHOT_MCQ_PENDING);
    s = reset(); enabled_queue(7); f.reg[(f.runtime + 7 * 0x30 + 4) / 4] = 32;
    check_case(&s, 0, DUFS_SNAPSHOT_MCQ_ENABLED | DUFS_SNAPSHOT_LISTS_CONFIGURED | DUFS_SNAPSHOT_MCQ_PENDING);
    s = reset(); enabled_queue(0); f.reg[f.runtime / 4] = 3;
    check_case(&s, 0, DUFS_SNAPSHOT_MCQ_ENABLED | DUFS_SNAPSHOT_LISTS_CONFIGURED |
        DUFS_SNAPSHOT_MCQ_PENDING | DUFS_SNAPSHOT_BAD_POINTER);
    s = reset(); enabled_queue(0); f.reg[f.runtime / 4] = f.reg[(f.runtime + 4) / 4] = 128;
    check_case(&s, 0, DUFS_SNAPSHOT_MCQ_ENABLED | DUFS_SNAPSHOT_LISTS_CONFIGURED | DUFS_SNAPSHOT_BAD_POINTER);
    s = reset(); f.reg[f.runtime / 4] = f.reg[(f.runtime + 4) / 4] = 32;
    check_case(&s, 0, DUFS_SNAPSHOT_BAD_POINTER);
    s = reset(); f.reg[1] = 0x40007; check_case(&s, 0, 0);
    s = reset(); f.reg[1] = 0xff0007; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0);
    s = reset(); f.reg[1] = 7; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0);
    s = reset(); f.reg[0] = UINT32_MAX; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0);
    s = reset(); f.reg[2] = 0; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0);
    s = reset(); f.reg[1] = 0x20008; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0);
    s = reset(); s.physical_base += 4; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0); CHECK(!f.reads);
    s = reset(); s.bytes -= 4; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0); CHECK(!f.reads);
    s = reset(); s.profile = 0; check_case(&s, DUFS_SNAPSHOT_LAYOUT, 0); CHECK(!f.reads);
    s = reset(); s.boot_id = 0; check_case(&s, DUFS_SNAPSHOT_ARGUMENT, 0); CHECK(!f.reads);
    s = reset(); s.allow_read = 0; check_case(&s, DUFS_SNAPSHOT_ARGUMENT, 0); CHECK(!f.reads);
    s = reset(); f.deny_after = 1; check_case(&s, DUFS_SNAPSHOT_DENIED, 0); CHECK(!f.reads);
    s = reset(); f.deny_after = 100; check_case(&s, DUFS_SNAPSHOT_DENIED, 0); CHECK(f.reads == 99);
    s = reset(); f.mutate = 1; check_case(&s, 0, DUFS_SNAPSHOT_HCE_ACTIVE | DUFS_SNAPSHOT_CHANGED);
    for (unsigned i = 1; i <= full_reads; ++i) {
        s = reset(); f.fail_at = i;
        struct dufs_register_snapshot out, before;
        memset(&out, 0xa5, sizeof(out)); before = out;
        CHECK(dufs_snapshot_registers(&s, &out) == DUFS_SNAPSHOT_IO);
        CHECK(f.reads == i && memcmp(&out, &before, sizeof(out)) == 0);
    }
    printf("UFS SNAPSHOT failures=%u output_unchanged=1\n", full_reads);
    for (unsigned i = 1; i <= full_reads; ++i) {
        s = reset(); f.deny_after = i;
        struct dufs_register_snapshot out, before;
        memset(&out, 0xa5, sizeof(out)); before = out;
        CHECK(dufs_snapshot_registers(&s, &out) == DUFS_SNAPSHOT_DENIED);
        CHECK(f.reads == i - 1 && f.permits == i && memcmp(&out, &before, sizeof(out)) == 0);
    }
    printf("UFS SNAPSHOT revocations=%u no_later_read=1\n", full_reads);
}

#ifdef DUCHAMP_SNAPSHOT_QEMU_DEVICE
#define PCI UINT64_C(0x3f020000)
#define BAR UINT64_C(0x10000000)
static unsigned real_reads;
static int real_permit(void *context, uint64_t boot, uint64_t base, uint32_t size)
{
    (void)context;
    return boot != 0x5678 || base != BAR || size != 0x2000;
}
static int real_read(void *context, uint32_t offset, uint32_t *value)
{
    (void)context; ++real_reads;
    *value = *(volatile uint32_t *)(uintptr_t)(BAR + offset);
    __asm__ volatile("dsb ld" ::: "memory");
    return 0;
}
/* Fixture setup is deliberately outside the observer's read-only API. */
static void firmware_write(uint32_t offset, uint32_t value)
{
    *(volatile uint32_t *)(uintptr_t)(BAR + offset) = value;
    __asm__ volatile("dsb sy" ::: "memory");
}
static void qemu_device_cases(void)
{
    volatile uint32_t *pci = (void *)PCI;
    CHECK(pci[0] == 0x00131b36);
    CHECK(!(pci[1] & 7));
    unsigned type = pci[4] & 15;
    CHECK(type == 0 || type == 4);
    pci[4] = BAR;
    if (type == 4) pci[5] = 0;
    /* Enable memory decode only. Bus mastering remains off. */
    *(volatile uint16_t *)(PCI + 4) = 2;
    __asm__ volatile("dsb sy" ::: "memory");
    struct dufs_snapshot_source s = { .allow_read = real_permit, .read32 = real_read,
        .boot_id = 0x5678, .physical_base = BAR, .bytes = 0x2000, .profile = DUFS_SNAPSHOT_QEMU };
    struct dufs_register_snapshot out;
    CHECK(dufs_snapshot_registers(&s, &out) == 0 && !out.blockers);
    CHECK(out.first.queues == 8 && out.first.queue_config_base == 0x400);
    CHECK(real_reads == out.reads);
    printf("UFS DEVICE cold blockers=%u reads=%u\n", out.blockers, real_reads);
    firmware_write(0x34, 1); firmware_write(0x300, 1);
    firmware_write(0x424, 0x43001000); firmware_write(0x428, 0);
    firmware_write(0x420, 0x8000001f);
    firmware_write(0x404, 0x43000000); firmware_write(0x408, 0);
    firmware_write(0x400, 0x8000001f);
    real_reads = 0;
    CHECK(dufs_snapshot_registers(&s, &out) == 0);
    CHECK(out.blockers == (DUFS_SNAPSHOT_HCE_ACTIVE | DUFS_SNAPSHOT_MCQ_ENABLED |
        DUFS_SNAPSHOT_LISTS_CONFIGURED));
    CHECK(real_reads == out.reads && out.first.queue[0].sq_base_lo == 0x43000000);
    printf("UFS DEVICE inherited blockers=%u reads=%u\n", out.blockers, real_reads);
    real_reads = 0; s.boot_id = 0x5679;
    CHECK(dufs_snapshot_registers(&s, &out) == DUFS_SNAPSHOT_DENIED && !real_reads);
    printf("UFS DEVICE different_boot denied=1 reads=%u\n", real_reads);
}
#endif
int main(void)
{
    model_cases();
#ifdef DUCHAMP_SNAPSHOT_QEMU_DEVICE
    qemu_device_cases();
#endif
    printf("UFS SNAPSHOT PASS cases=%u\n", cases);
    return 0;
}
