/* SPDX-License-Identifier: 0BSD */
#include "dual_ramdisk_bounds.h"

static unsigned int
test_ranges(void)
{
    const uint64_t phys = UINT64_C(0x1c0000000);
    const uint64_t page = DUCHAMP_RAMDISK_ALIGN;
    const uint64_t memory = 512 * DUCHAMP_RAMDISK_MIN;
    const uint64_t kernel_end = phys + 37 * DUCHAMP_RAMDISK_MIN;
    const struct duchamp_ramdisk_range root = {kernel_end, 32 * DUCHAMP_RAMDISK_MIN};
    const struct duchamp_ramdisk_range var = {root.base + root.size, root.size};
    const uint64_t adt = var.base + var.size, args = adt + page;

    const struct {
        uint64_t k_end, adt_bytes, args_end, ram_size;
        struct duchamp_ramdisk_range root, var;
        enum duchamp_ramdisk_check expected;
    } cases[] = {
        {kernel_end, 1024, args + page, memory, root, var, DUCHAMP_RAMDISK_OK},
        {kernel_end + page, 1024, args + page, memory, root, var, DUCHAMP_RAMDISK_OUTSIDE},
        {kernel_end, 0, args + page, memory, root, var, DUCHAMP_RAMDISK_BOOT_WINDOW},
        {kernel_end, page + 1, args + page, memory, root, var, DUCHAMP_RAMDISK_BOOT_WINDOW},
        {kernel_end, 1024, args, memory, root, var, DUCHAMP_RAMDISK_BOOT_WINDOW},
        {kernel_end, 1024, args + page, args + page - phys - 1, root, var, DUCHAMP_RAMDISK_BOOT_WINDOW},
        {kernel_end, 1024, args + page, UINT64_MAX, root, var, DUCHAMP_RAMDISK_BOOT_WINDOW},
        {kernel_end, 1024, args + page, memory, root, {0, 0}, DUCHAMP_RAMDISK_SIZE},
        {kernel_end, 1024, args + page, memory, root, {var.base, UINT64_MAX}, DUCHAMP_RAMDISK_SIZE},
        {kernel_end, 1024, args + page, memory, {root.base, root.size - 1}, var, DUCHAMP_RAMDISK_ALIGNMENT},
        {kernel_end, 1024, args + page, memory, root, {var.base + 1, var.size}, DUCHAMP_RAMDISK_ALIGNMENT},
        {kernel_end, 1024, args + page, memory, root, {adt, var.size}, DUCHAMP_RAMDISK_OUTSIDE},
        {kernel_end, 1024, args + page, memory, root, {var.base - page, var.size}, DUCHAMP_RAMDISK_LAYOUT},
        {kernel_end, 1024, args + page, memory, root, {var.base + page, var.size - page}, DUCHAMP_RAMDISK_LAYOUT},
        {kernel_end, 1024, args + page, memory, var, root, DUCHAMP_RAMDISK_LAYOUT},
    };
    for (unsigned int i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (duchamp_ramdisk_check_ranges(phys, cases[i].ram_size, cases[i].k_end,
            adt, cases[i].adt_bytes, args, cases[i].args_end,
            cases[i].root, cases[i].var) != cases[i].expected) {
            return i + 1;
        }
    }

    const uint64_t shift = UINT64_C(0x40000000);
    if (duchamp_ramdisk_check_ranges(phys + shift, memory, kernel_end + shift,
        adt + shift, 1024, args + shift, args + page + shift,
        (struct duchamp_ramdisk_range){root.base + shift, root.size},
        (struct duchamp_ramdisk_range){var.base + shift, var.size}) != DUCHAMP_RAMDISK_OK) {
        return 16;
    }
    return 0;
}

#ifdef DUCHAMP_QEMU_SEMIHOST
__attribute__((used, noreturn)) static void run_qemu(void)
{
    const uint64_t result[] = {0x20026, test_ranges()};
    register uint64_t operation __asm__("x0") = 0x20;
    register const uint64_t *parameters __asm__("x1") = result;
    __asm__ volatile("hlt #0xf000" : "+r"(operation) : "r"(parameters) : "memory");
    for (;;) {
        __asm__ volatile("wfe");
    }
}

__attribute__((naked)) void _start(void)
{
    __asm__ volatile("mov x0, #0x48000000\nmov sp, x0\nb run_qemu");
}
#else
#include <stdio.h>

int main(void)
{
    unsigned int failure = test_ranges();
    if (failure) {
        fprintf(stderr, "dual RAMDisk bounds case %u failed\n", failure);
        return 1;
    }
    puts("dual RAMDisk bounds: 16 cases passed");
    return 0;
}
#endif
