/* QEMU-only, read-only disk PID1. Fork and exec the dynamic probe as a child.
 * Only raw Darwin syscalls run before the original dyld starts.
 */
    .text
    .global _start
    .p2align 2
_start:
    mov x9,sp
    and x9,x9,#~15
    mov sp,x9
    sub sp,sp,#256
    adr x0,console
    mov x1,#2
    mov x2,#0
    mov x16,#5
    svc #0x80
    b.cs hang
    mov x19,x0
    mov x20,#0
dup_loop:
    mov x0,x19
    mov x1,x20
    mov x16,#90
    svc #0x80
    b.cs failed
    add x20,x20,#1
    cmp x20,#3
    b.ne dup_loop
    mov x0,#1
    adr x1,entered
    adr x2,entered_end
    sub x2,x2,x1
    mov x16,#4
    svc #0x80
    mov x16,#2
    svc #0x80
    b.cs failed
    /* Raw Darwin fork returns x1=1 to the child, x1=0 to the parent. */
    cbnz x1,child_exec
    mov x20,x0
wait_child:
    mov x0,x20
    add x1,sp,#32
    mov x2,#0
    mov x3,#0
    mov x16,#7                 /* wait4: block, do not spin on syscalls. */
    svc #0x80
    b.cc child_exited
    cmp x0,#4                  /* EINTR */
    b.eq wait_child
    b failed
child_exec:
    adr x0,program
    str x0,[sp]
    str xzr,[sp,#8]
    adr x9,environment
    str x9,[sp,#16]
    str xzr,[sp,#24]
    mov x1,sp
    add x2,sp,#16
    mov x16,#59
    svc #0x80
failed:
    mov x0,#1
    adr x1,failure
    adr x2,failure_end
    sub x2,x2,x1
    mov x16,#4
    svc #0x80
    b hang
child_exited:
    mov x0,#1
    adr x1,child_failure
    adr x2,child_failure_end
    sub x2,x2,x1
    mov x16,#4
    svc #0x80
hang:
    /* Darwin select(0,NULL,NULL,NULL,&timeval), matching the established
     * static UFS fixture ABI. The timeout is two 64-bit user fields.
     */
    mov x9,#60
    stp x9,xzr,[sp,#64]
    mov x0,#0
    mov x1,#0
    mov x2,#0
    mov x3,#0
    add x4,sp,#64
    mov x16,#93
    svc #0x80
    b hang
console: .asciz "/dev/console"
program: .asciz "/sbin/sweet-shared-cache-probe"
environment: .asciz "DYLD_PRINT_TO_STDERR=1"
entered: .ascii "SWEET SHARED CACHE: STATIC PID1 FORK EXEC\n"
entered_end:
failure: .ascii "SWEET SHARED CACHE: EXEC FAILED\n"
failure_end:
child_failure: .ascii "SWEET SHARED CACHE: CHILD EXITED\n"
child_failure_end:
