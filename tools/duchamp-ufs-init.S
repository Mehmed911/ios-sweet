/* Static read-only-root PID 1: raw BSD read, HFS file read and write-open rejection. */
    .macro PRINT name
    mov x0,x19
    adr x1,\name
    adr x2,\name\()_end
    sub x2,x2,x1
    mov x16,#4
    svc #0x80
    .endmacro
    .text
    .global _start
    .p2align 2
_start:
    mov x9,sp
    and x9,x9,#~15
    mov sp,x9
    sub sp,sp,#8192
    adr x0,console
    mov x1,#2
    mov x2,#0
    mov x16,#5
    svc #0x80
    b.cs hang
    mov x19,x0
    mov x16,#20
    svc #0x80
    b.cs failed
    cmp x0,#1
    b.ne failed
    PRINT entered
    /* syscalls.master: stat64=338. user64_stat64 has st_dev at 0 and
     * st_rdev at 24 (bsd/sys/stat.h). Compare the mounted root's device
     * with the actual block node, rather than relying on early IOLog text.
     */
    adr x0,rootpath
    mov x1,sp
    mov x16,#338
    svc #0x80
    b.cs failed
    ldr w21,[sp]
    ldrh w9,[sp,#4]
    and w9,w9,#0xf000
    cmp w9,#0x4000
    b.ne failed
    adr x0,blockdisk
    mov x1,sp
    mov x16,#338
    svc #0x80
    b.cs failed
    ldr w9,[sp,#24]
    cmp w21,w9
    b.ne failed
    ldrh w9,[sp,#4]
    and w9,w9,#0xf000
    cmp w9,#0x6000
    b.ne failed
    PRINT rootpass
    adr x0,rawdisk
    mov x1,#0
    mov x2,#0
    mov x16,#5
    svc #0x80
    b.cs failed
    mov x20,x0
    mov x1,sp
    mov x2,#4096
    mov x16,#3
    svc #0x80
    b.cs failed
    cmp x0,#4096
    b.ne failed
    add x9,sp,#1024
    ldrh w10,[x9]
    mov w11,#0x2b48
    cmp w10,w11
    b.ne failed
    /* Byte-offset reads exercise the uiomove adapter rather than physio's
     * sector-aligned user-buffer convention. HFS+ header is 512 bytes into
     * the requested window when the device offset is 512.
     */
    mov x0,x20
    mov x1,#512
    mov x2,#0
    mov x16,#199
    svc #0x80
    b.cs failed
    cmp x0,#512
    b.ne failed
    mov x0,x20
    mov x1,sp
    mov x2,#1024
    mov x16,#3
    svc #0x80
    b.cs failed
    cmp x0,#1024
    b.ne failed
    add x9,sp,#512
    ldrh w10,[x9]
    mov w11,#0x2b48
    cmp w10,w11
    b.ne failed
    PRINT offsetpass
    /* Bad user memory must return EFAULT while leaving the kernel/transport
     * alive. The later HFS file read must still succeed.
     */
    mov x0,x20
    mov x1,#0
    mov x2,#4096
    mov x16,#3
    svc #0x80
    b.cc failed
    cmp x0,#14
    b.ne failed
    PRINT faultpass
    mov x0,x20
    mov x16,#6
    svc #0x80
    b.cs failed
    PRINT rawpass
    adr x0,rawdisk
    mov x1,#2
    mov x2,#0
    mov x16,#5
    svc #0x80
    b.cc failed
    cmp x0,#30
    b.ne failed
    PRINT readonlypass
    adr x0,fixture
    mov x1,#0
    mov x2,#0
    mov x16,#5
    svc #0x80
    b.cs failed
    mov x20,x0
    mov x1,sp
    mov x2,#1024
    mov x16,#3
    svc #0x80
    b.cs failed
    cmp x0,#1024
    b.ne failed
    adr x9,expected
    mov x10,sp
    mov x11,#1024
compare:
    ldrb w12,[x9],#1
    ldrb w13,[x10],#1
    cmp w12,w13
    b.ne failed
    subs x11,x11,#1
    b.ne compare
    mov x0,x20
    mov x16,#6
    svc #0x80
    b.cs failed
    PRINT filepass
    PRINT passed
heartbeat:
    mov x9,#2
    stp x9,xzr,[sp]
    mov x0,#0
    mov x1,#0
    mov x2,#0
    mov x3,#0
    mov x4,sp
    mov x16,#93
    svc #0x80
    b.cs failed
    PRINT beat
    b heartbeat
failed:
    PRINT failure
hang:
    b hang
    .p2align 2
console: .asciz "/dev/console"
rootpath: .asciz "/"
blockdisk: .asciz "/dev/qufs0"
rawdisk: .asciz "/dev/rqufs0"
fixture: .asciz "/ufs-test.bin"
entered: .ascii "DUCHAMP UFS PID1 ENTERED\n"
entered_end:
rootpass: .ascii "DUCHAMP UFS ROOT DEVICE MATCH\n"
rootpass_end:
rawpass: .ascii "DUCHAMP UFS RAW HEADER READ PASS\n"
rawpass_end:
offsetpass: .ascii "DUCHAMP UFS OFFSET READ PASS\n"
offsetpass_end:
faultpass: .ascii "DUCHAMP UFS USER COPY FAULT HANDLED\n"
faultpass_end:
readonlypass: .ascii "DUCHAMP UFS WRITE OPEN REFUSED EROFS\n"
readonlypass_end:
filepass: .ascii "DUCHAMP UFS HFS FILE BYTES MATCH\n"
filepass_end:
passed: .ascii "DUCHAMP UFS PID1 READ PASS\n"
passed_end:
beat: .ascii "DUCHAMP UFS PID1 heartbeat\n"
beat_end:
failure: .ascii "DUCHAMP UFS PID1 FAIL\n"
failure_end:
    .p2align 3
expected:
    .incbin "ufs-expected.bin"
