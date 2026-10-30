.section .text.entry,"ax"
.global _start
_start:
    msr daifset, #15
    ldr x0, =__stack_top
    mov sp, x0
    bl test_framebuffer_arm
1:  wfe
    b 1b
