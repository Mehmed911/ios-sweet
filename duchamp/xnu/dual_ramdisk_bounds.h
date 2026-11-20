/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_DUAL_RAMDISK_BOUNDS_H
#define DUCHAMP_DUAL_RAMDISK_BOUNDS_H

#include <stdint.h>

#define DUCHAMP_RAMDISK_ALIGN UINT64_C(16384)
#define DUCHAMP_RAMDISK_MIN   UINT64_C(1048576)
#define DUCHAMP_RAMDISK_MAX   UINT64_C(67108864)

struct duchamp_ramdisk_range {
    uint64_t base;
    uint64_t size;
};

enum duchamp_ramdisk_check {
    DUCHAMP_RAMDISK_OK,
    DUCHAMP_RAMDISK_BOOT_WINDOW,
    DUCHAMP_RAMDISK_SIZE,
    DUCHAMP_RAMDISK_ALIGNMENT,
    DUCHAMP_RAMDISK_OUTSIDE,
    DUCHAMP_RAMDISK_LAYOUT,
};

static inline enum duchamp_ramdisk_check
duchamp_ramdisk_check_ranges(uint64_t phys, uint64_t memory, uint64_t kernel_end,
    uint64_t adt, uint64_t adt_size, uint64_t boot_args, uint64_t reserved_end,
    struct duchamp_ramdisk_range root, struct duchamp_ramdisk_range var)
{
    const uint64_t mask = DUCHAMP_RAMDISK_ALIGN - 1;
    if (!memory || memory > UINT64_MAX - phys || reserved_end > phys + memory ||
        kernel_end < phys || kernel_end > adt || adt > boot_args ||
        !adt_size || adt_size > boot_args - adt ||
        boot_args > reserved_end || reserved_end - boot_args != DUCHAMP_RAMDISK_ALIGN ||
        ((phys | kernel_end | adt | boot_args | reserved_end) & mask)) {
        return DUCHAMP_RAMDISK_BOOT_WINDOW;
    }
    if (root.size < DUCHAMP_RAMDISK_MIN || root.size > DUCHAMP_RAMDISK_MAX ||
        var.size < DUCHAMP_RAMDISK_MIN || var.size > DUCHAMP_RAMDISK_MAX) {
        return DUCHAMP_RAMDISK_SIZE;
    }
    if ((root.base | root.size | var.base | var.size) & mask) {
        return DUCHAMP_RAMDISK_ALIGNMENT;
    }
    if (root.base < kernel_end || root.base > adt || root.size > adt - root.base ||
        var.base < kernel_end || var.base > adt || var.size > adt - var.base) {
        return DUCHAMP_RAMDISK_OUTSIDE;
    }
    if (root.base + root.size != var.base || var.base + var.size != adt) {
        return DUCHAMP_RAMDISK_LAYOUT;
    }
    return DUCHAMP_RAMDISK_OK;
}
#endif
