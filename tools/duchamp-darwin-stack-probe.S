/* SPDX-License-Identifier: 0BSD */
/*
 * Diagnostic link support for ARM64 Darwin objects built with stack probing.
 * The reference SWEET caller puts the byte count in x9. Probe in 4 KiB steps
 * down from the unchanged SP, then read the final byte. Only x9 and x10 are
 * scratch. The volatile loads must still fault when a guard page is crossed.
 */
#ifndef __aarch64__
#error This stack probe requires AArch64
#endif

    .text
    .p2align 2
    .globl ___chkstk_darwin
___chkstk_darwin:
    b Lprobe

Lprobe:
    cmp x9, #4096
    mov x10, sp
    b.lo Llast
Lmore:
    sub x10, x10, #4096
    ldrb wzr, [x10]
    sub x9, x9, #4096
    cmp x9, #4096
    b.hi Lmore
Llast:
    sub x10, x10, x9
    ldrb wzr, [x10]
    ret
