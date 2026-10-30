/* Standalone QEMU virt model tests, MMU/cache off, interrupts masked. */
.section .text.boot,"ax"
.global _start
_start:
    msr daifset, #15
    ldr x0, =_stack_top
    mov sp, x0
    adr x0, model_vectors
    msr vbar_el1, x0
    isb
    ldr x0, =_bss_start
    ldr x1, =_bss_end
1:
    cmp x0, x1
    b.hs 2f
    str xzr, [x0], #8
    b 1b
2:
    bl model_entry
3:
    wfe
    b 3b
.balign 2048
model_vectors:
.rept 16
    b model_trap
    .space 124
.endr
model_trap:
    mrs x0, esr_el1
    mrs x1, elr_el1
    mrs x2, far_el1
    bl model_exception
    b 3b
