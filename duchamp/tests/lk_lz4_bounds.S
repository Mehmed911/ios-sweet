/* Standalone QEMU-only regression entry. Never a phone boot target. */
.section .text.entry,"ax"
.global _start
_start:
    msr daifset, #15
    ldr x0, =0x41000000
    mov sp, x0
    adr x0, vectors
    msr vbar_el1, x0
    isb
    bl test_mmu_setup
    bl test_main
1:  wfe
    b 1b

.balign 2048
vectors:
.rept 16
    b test_fault_entry
    .balign 128
.endr

test_fault_entry:
    sub sp, sp, #256
    stp x0, x1, [sp]
    stp x2, x3, [sp, #16]
    stp x4, x5, [sp, #32]
    stp x6, x7, [sp, #48]
    stp x8, x9, [sp, #64]
    stp x10, x11, [sp, #80]
    stp x12, x13, [sp, #96]
    stp x14, x15, [sp, #112]
    stp x16, x17, [sp, #128]
    stp x18, x19, [sp, #144]
    stp x20, x21, [sp, #160]
    stp x22, x23, [sp, #176]
    stp x24, x25, [sp, #192]
    stp x26, x27, [sp, #208]
    stp x28, x29, [sp, #224]
    stp x30, xzr, [sp, #240]
    mov x0, sp
    bl test_fault
    b 1b

/* Bytes copied only into the isolated test ELF by the host runner. */
.section .lk,"ax"
.incbin "lk-code.bin"
