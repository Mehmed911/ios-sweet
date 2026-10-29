/* DEVELOPMENT init entry; exec the unchanged Apple binary without forking. */
    .macro PRINT name
    adr x1, \name
    adr x2, \name\()_end
    sub x2, x2, x1
    bl output
    .endmacro
    .text
    .globl _start
    .p2align 2
_start:
    mov x9, sp
    and x9, x9, #~15
    mov sp, x9
    sub sp, sp, #128
    adr x0, console
    mov x1, #2
    mov x2, #0
    mov x16, #5
    svc #0x80
    b.cs hang
    mov x19, x0
    mov x20, #0
stdio:
    mov x0, x19
    mov x1, x20
    mov x16, #90
    svc #0x80
    b.cs failed
    add x20, x20, #1
    cmp x20, #3
    b.lo stdio
    mov x16, #20
    svc #0x80
    cmp x0, #1
    b.ne failed
    PRINT starting
    adr x0, launchd
    str x0, [sp]
    str xzr, [sp, #8]
    adr x9, no_cache
    str x9, [sp, #16]
    adr x9, path
    str x9, [sp, #24]
    str xzr, [sp, #32]
    mov x1, sp
    add x2, sp, #16
    mov x16, #59
    svc #0x80
    mov x24, x0
    PRINT exec_error
    mov w10, w24
    adr x11, digits
    add x12, sp, #64
    mov x13, #8
hex:
    lsr w14, w10, #28
    ldrb w14, [x11, x14]
    strb w14, [x12], #1
    lsl w10, w10, #4
    subs x13, x13, #1
    b.ne hex
    mov w14, #10
    strb w14, [x12]
    add x1, sp, #64
    mov x2, #9
    bl output
failed:
    PRINT failure
hang:
    b hang
output:
    mov x0, x19
    mov x16, #4
    svc #0x80
    ret
console:
    .asciz "/dev/console"
launchd:
    .asciz "/sbin/launchd"
no_cache:
    .asciz "DYLD_SHARED_REGION=avoid"
path:
    .asciz "PATH=/usr/bin:/bin:/usr/sbin:/sbin"
digits:
    .ascii "0123456789abcdef"
starting:
    .ascii "SWEET launchd bootstrap: PID 1 exec original /sbin/launchd\n"
starting_end:
exec_error:
    .ascii "SWEET launchd bootstrap: exec errno hex:\n"
exec_error_end:
failure:
    .ascii "SWEET launchd bootstrap: TEST FAILED\n"
failure_end:
