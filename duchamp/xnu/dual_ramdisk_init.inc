/* SPDX-License-Identifier: 0BSD */
/* Included in memdev.c after its private registration and state helpers. */
#if defined(ARM64_BOARD_CONFIG_SWEET)
#include <arm/machine_routines.h>
#include <pexpert/arm64/boot.h>
#include <pexpert/device_tree.h>
#include "duchamp_dual_ramdisk_bounds.h"

int duchamp_dual_ramdisk_init(const char *root_name);
extern vm_offset_t arm_vm_kernelcache_phys_end;
extern vm_offset_t duchamp_loader_boot_args_pa;

static int
duchamp_ramdisk_read_range(DTEntry node, const char *name, struct duchamp_ramdisk_range *range)
{
    const void *data;
    unsigned int bytes;
    if (SecureDTGetProperty(node, name, &data, &bytes) != kSuccess) {
        return 0;
    }
    if (bytes != sizeof(*range)) {
        panic("DUCHAMP DUAL RAMDISK malformed property %s", name);
    }
    memcpy(range, data, sizeof(*range));
    return 1;
}

int
duchamp_dual_ramdisk_init(const char *root_name)
{
    DTEntry node;
    unsigned int version = 0, rootrw = 0;
    int requested = PE_parse_boot_argn("duchamp_dual_ramdisk", &version, sizeof(version));
    int has_map = SecureDTLookupEntry(NULL, "/chosen/memory-map", &node) == kSuccess;
    struct duchamp_ramdisk_range root, var;
    int has_var = has_map && duchamp_ramdisk_read_range(node, "DuchampDataRAMDisk", &var);

    if (!requested && !has_var) {
        return 0;
    }
    if (!requested || version != 1 || strcmp(root_name, "md0") ||
        (PE_parse_boot_argn("rootrw", &rootrw, sizeof(rootrw)) && rootrw)) {
        panic("DUCHAMP DUAL RAMDISK invalid boot profile");
    }
    if (!has_var || !duchamp_ramdisk_read_range(node, "RAMDisk", &root)) {
        panic("DUCHAMP DUAL RAMDISK missing RAMDisk or DuchampDataRAMDisk");
    }

    const boot_args *args = PE_state.bootArgs;
    if (!args || !PE_state.deviceTreeHead || !duchamp_loader_boot_args_pa) {
        panic("DUCHAMP DUAL RAMDISK missing boot reservation");
    }
    enum duchamp_ramdisk_check bounds = duchamp_ramdisk_check_ranges(args->physBase,
        args->memSize, arm_vm_kernelcache_phys_end,
        ml_static_vtop((vm_offset_t)PE_state.deviceTreeHead),
        args->deviceTreeLength, duchamp_loader_boot_args_pa,
        args->topOfKernelData, root, var);
    if (bounds != DUCHAMP_RAMDISK_OK || mdevlookup(0) != -1 || mdevlookup(1) != -1) {
        panic("DUCHAMP DUAL RAMDISK invalid reservation or occupied slot (%d)", bounds);
    }

    if (mdevadd_with_flags(0, ml_static_ptovirt(root.base) >> 12,
        (unsigned int)(root.size >> 12), mdRO) == -1 ||
        mdevadd_with_flags(1, ml_static_ptovirt(var.base) >> 12,
        (unsigned int)(var.size >> 12), 0) == -1) {
        panic("DUCHAMP DUAL RAMDISK device registration failed");
    }
    printf("DUCHAMP DUAL RAMDISK md0 read-only md1 writable\n");
    return 1;
}
#endif
