#if defined(ARM64_BOARD_CONFIG_SWEET) || defined(MT6897_UFS_OBSERVER_XNU_TEST)
#include "mt6897_ufs_observer_xnu.h"
#include <stddef.h>

#if defined(MT6897_UFS_OBSERVER_XNU_TEST)
/* Test links a RAM-backed mapping shim. These are not physical MMIO probes. */
extern uintptr_t ml_io_map_with_prot(uintptr_t, size_t, int);
#define OBSERVER_PROT_READ 1
#else
#include <machine/machine_routines.h>
#include <mach/vm_prot.h>
/* BSD's exported header omits this private prototype. Match the ARM64
 * definition in osfmk/arm64/machine_routines.c and the full source header.
 */
extern vm_offset_t ml_io_map_with_prot(vm_offset_t, vm_size_t, vm_prot_t);
#define OBSERVER_PROT_READ VM_PROT_READ
#endif

static uintptr_t map_readonly(void *context, uint64_t base, uint32_t bytes)
{
    struct mt6897_ufs_xnu_observer *x = context;
    if (x->map_calls || x->mapping || base != DUFS_MTK_HCI_BASE || bytes != DUFS_MTK_HCI_BYTES)
        return 0;
    ++x->map_calls;
    /* XNU maps this as Device memory with VM_PROT_READ. It is intentionally
     * permanent, including on failure: platform power/access pins last until
     * reset. This creates no power/clock/firewall permission by itself.
     */
    x->mapping = ml_io_map_with_prot((uintptr_t)base, bytes, OBSERVER_PROT_READ);
    return x->mapping;
}
static int read32(void *context, uintptr_t mapping, uint32_t offset, uint32_t *value)
{
    struct mt6897_ufs_xnu_observer *x = context;
    if (!value || !mapping || mapping != x->mapping || (offset & 3) ||
        offset > DUFS_MTK_HCI_BYTES - 4) return -1;
    ++x->read_calls;
    *value = *(const volatile uint32_t *)(mapping + offset);
#if defined(__aarch64__) || defined(__arm64__)
    __asm__ volatile("dsb ld" ::: "memory");
#else
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
#endif
    return 0;
}
int mt6897_ufs_xnu_observer_bind(struct mt6897_ufs_xnu_observer *x, uint64_t boot,
    const struct mt6897_ufs_read_authority *authority)
{
    if (!x) return MUO_ARGUMENT;
    if (x->mapping || x->map_calls || x->read_calls) return MUO_STATE;
    const struct mt6897_ufs_observer_bus bus = { x, map_readonly, read32 };
    return mt6897_ufs_observer_bind(&x->provider, boot, authority, &bus);
}
#endif
