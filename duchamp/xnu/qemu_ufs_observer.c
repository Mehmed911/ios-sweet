/* QEMU-only integration test of the real read-only XNU mapping adapter.
 * The MT6897-shaped aperture below is ivshmem RAM, NOT physical hardware.
 * This synthetic authority is never a platform handoff/firmware producer.
 */
#if defined(ARM64_BOARD_CONFIG_SWEET)
#include <sys/param.h>
#include <sys/systm.h>
#include <sys/errno.h>
#include <machine/machine_routines.h>
#include <pexpert/pexpert.h>
#include <pexpert/device_tree.h>
#include "mt6897_ufs_observer_xnu.h"

int duchamp_qemu_ufs_observer_test(void);
extern uint64_t duchamp_qemu_ufs_snapshot_boot_id(void);
/* Private ARM64 mapper; BSD's exported header omits its declaration. */
extern vm_offset_t ml_io_map(vm_offset_t, vm_size_t);
static struct mt6897_ufs_xnu_observer observer;
static unsigned attempted, scenario, checks;

static int fixture(void)
{
    uint64_t midr;
    __asm__ volatile("mrs %0,midr_el1" : "=r"(midr));
    if ((midr >> 24) != 0x41 || ((midr >> 4) & 0xfff) != 0xd0b) return ENXIO;
    DTEntry n; const void *v; unsigned size;
    static const char firmware[] = "duchamp-qemu-ufs-fixture-v1";
    static const char compatible[] = "qemu,mt6897-register-bank-v1";
    if (SecureDTLookupEntry(NULL,"/chosen",&n) != kSuccess ||
        SecureDTGetProperty(n,"firmware-version",&v,&size) != kSuccess ||
        size != sizeof(firmware) || memcmp(v,firmware,size) ||
        SecureDTLookupEntry(NULL,"/duchamp-qemu-observer",&n) != kSuccess ||
        SecureDTGetProperty(n,"compatible",&v,&size) != kSuccess ||
        size != sizeof(compatible) || memcmp(v,compatible,size)) return ENXIO;
    return 0;
}
static int virtual_bank(void)
{
    /* Explicit emulator-only PCI device 05.0; no bus mastering or IRQs.
     * BAR2 is a 16 KiB ivshmem RAM bank. Only PCI config is written here;
     * the observer itself has no write callback, including to this RAM bank.
     */
    volatile uint32_t *pci = (void *)ml_io_map(0x3f028000,0x1000);
    if (!pci || pci[0] != 0x11101af4 || (pci[1] & 7) || pci[6] != 0xc || pci[7])
        return ENXIO;
    pci[6] = UINT32_MAX; pci[7] = UINT32_MAX;
    __asm__ volatile("dsb sy" ::: "memory");
    if (pci[6] != 0xffffc00c || pci[7] != UINT32_MAX) return ENXIO;
    pci[6] = DUFS_MTK_HCI_BASE; pci[7] = 0; pci[1] = 2;
    __asm__ volatile("dsb sy" ::: "memory");
    return pci[6] != (DUFS_MTK_HCI_BASE | 0xc) || pci[7] || (pci[1] & 7) != 2 ? EIO : 0;
}
static int verify(void *context, uint64_t boot, struct mt6897_ufs_read_grant *g)
{
    (void)context;
    *g = (struct mt6897_ufs_read_grant){ .version=MUO_GRANT_VERSION,
        .rights=MUO_REQUIRED, .boot_id=boot, .grant_id=1, .owner_id=2,
        .resource_epoch=3, .base=DUFS_MTK_HCI_BASE, .bytes=DUFS_MTK_HCI_BYTES };
    if (scenario == 3) g->boot_id ^= 1;
    if (scenario == 4) g->rights &= ~MUO_POWER_PINNED;
    if (scenario == 5) g->rights &= ~MUO_BUS_CLOCKS_PINNED;
    return 0;
}
static int check(void *context, const struct mt6897_ufs_read_grant *g)
{
    (void)context; (void)g;
    unsigned position = scenario == 6 ? 1 : scenario == 7 ? 100 : scenario == 8 ? 318 : 0;
    if (++checks == position) {
        mt6897_ufs_observer_revoke(&observer.provider);
        return -1;
    }
    return 0;
}
static int mapping_protection(uint64_t *read_par, uint64_t *write_par)
{
    uint64_t daif, saved;
    /* AT checks permissions without attempting any store. Keep PAR_EL1 local
     * to this small critical section and restore its previous value.
     */
    __asm__ volatile("mrs %0,daif\nmsr daifset,#3\nmrs %1,par_el1"
        : "=r"(daif), "=r"(saved) :: "memory");
    __asm__ volatile("at s1e1r,%1\nisb\nmrs %0,par_el1"
        : "=r"(*read_par) : "r"(observer.mapping) : "memory");
    __asm__ volatile("at s1e1w,%1\nisb\nmrs %0,par_el1"
        : "=r"(*write_par) : "r"(observer.mapping) : "memory");
    __asm__ volatile("msr par_el1,%0\nmsr daif,%1" :: "r"(saved), "r"(daif) : "memory");
    return (*read_par & 1) || !(*write_par & 1) ||
        (*read_par & UINT64_C(0x0000fffffffff000)) != DUFS_MTK_HCI_BASE;
}
int duchamp_qemu_ufs_observer_test(void)
{
    if (!PE_parse_boot_argn("sweet-qemu-ufs-observer-test",&scenario,sizeof(scenario)) ||
        !scenario) return 0;
    if (scenario > 9 || fixture() || !duchamp_qemu_ufs_snapshot_boot_id()) return ENXIO;
    if (attempted++) return EIO;
    if (virtual_bank()) return ENXIO;
    struct dufs_register_snapshot output, original;
    memset(&output,0xa5,sizeof(output)); original=output;
    const struct mt6897_ufs_read_authority authority = { NULL, verify, check };
    uint64_t boot = duchamp_qemu_ufs_snapshot_boot_id();
    int status = 0;
    if (scenario != 2) status = mt6897_ufs_xnu_observer_bind(&observer,boot,&authority);
    if (status) return EIO;
    status = mt6897_ufs_observer_capture(&observer.provider,&output);
    uint64_t read_par=0, write_par=0;
    int protection = observer.mapping ? mapping_protection(&read_par,&write_par) : 0;
    unsigned unchanged = !memcmp(&output,&original,sizeof(output));
    int expected = scenario == 2 ? MUO_DISABLED : scenario <= 5 && scenario >= 3 ? MUO_DENIED :
        scenario >= 6 && scenario <= 8 ? MUO_REVOKED : MUO_OK;
    unsigned maps = scenario == 1 || scenario >= 7 ? 1 : 0;
    unsigned reads = scenario == 1 || scenario == 8 || scenario == 9 ? 316 : scenario == 7 ? 98 : 0;
    unsigned flags = scenario == 9 ? 0x39 : 0;
    int passed = status == expected && observer.map_calls == maps && observer.read_calls == reads &&
        !protection && (status ? unchanged : !unchanged && output.boot_id == boot &&
        output.profile == DUFS_SNAPSHOT_MT6897 && output.reads == reads && output.blockers == flags);
    printf("SWEET OBSERVER case=%u status=%d maps=%u reads=%llu checks=%u unchanged=%u flags=%x boot=%016llx pass=%d\n",
        scenario,status,observer.map_calls,observer.read_calls,checks,unchanged,
        status ? 0 : output.blockers,boot,passed);
    if (observer.mapping) printf("SWEET OBSERVER RO read=%016llx write=%016llx pass=%d\n",read_par,write_par,!protection);
    if (!status) {
        for (unsigned i=0;i<output.last.queues;i++) {
            const struct dufs_queue_snapshot *q=&output.last.queue[i];
            printf("SWEET OBSERVER q=%u sq=%x/%x cq=%x/%x\n",i,q->sq_head,q->sq_tail,q->cq_head,q->cq_tail);
        }
    }
    if (!passed) return EIO;
    /* Only the cold positive fixture may continue to the separate QEMU UFS
     * GPT disk. All denial/inherited-state tests stop before its first access.
     */
    return scenario == 1 ? 0 : EPERM;
}
#endif
