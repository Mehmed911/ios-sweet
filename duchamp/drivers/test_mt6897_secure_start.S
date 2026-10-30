/* QEMU-only monitor fixture. This is NOT MT6897 firmware. */
.section .text.boot,"ax"
.global _start
_start:
    msr daifset, #15
    ldr x0, =_stack_top
    mov sp, x0
    ldr x0, =_bss_start
    ldr x1, =_bss_end
1:
    cmp x0, x1
    b.hs 2f
    str xzr, [x0], #8
    b 1b
2:
    mrs x0, CurrentEL
    cmp x0, #12
    b.ne bad_start
    adr x0, secure_vectors
    msr vbar_el3, x0
    ldr x0, =0x401
    msr scr_el3, x0
    ldr x0, =0x80000000
    msr hcr_el2, x0
    ldr x0, =_stack_top
    sub x0, x0, #0x10000
    msr sp_el1, x0
    mov x0, #0x3c5
    msr spsr_el3, x0
    adr x0, nonsecure_entry
    msr elr_el3, x0
    isb
    eret
bad_start:
    mov x0, #0xbad
    mov x1, #0
    mov x2, #0
    bl model_exception
nonsecure_entry:
    adr x0, nonsecure_vectors
    msr vbar_el1, x0
    isb
    bl model_entry
3:
    wfe
    b 3b
.balign 2048
secure_vectors:
.rept 16
    b secure_trap
    .space 124
.endr
secure_trap:
    mrs x9, esr_el3
    lsr x9, x9, #26
    cmp x9, #0x17
    b.ne secure_fault
    ldr x9, =test_smc_seen
    stp x0, x1, [x9]
    stp x2, x3, [x9, #16]
    stp x4, x5, [x9, #32]
    stp x6, x7, [x9, #48]
    ldr x9, =test_smc_count
    ldr w10, [x9]
    add w10, w10, #1
    str w10, [x9]
    mov x0, #0
    mov x1, x7
    add x2, x2, #13
    ldr x3, =0x1122334455667788
    eret
secure_fault:
    mrs x0, esr_el3
    mrs x1, elr_el3
    mrs x2, far_el3
    bl model_exception
    b 3b
.balign 2048
nonsecure_vectors:
.rept 16
    b nonsecure_fault
    .space 124
.endr
nonsecure_fault:
    mrs x0, esr_el1
    mrs x1, elr_el1
    mrs x2, far_el1
    bl model_exception
    b 3b
