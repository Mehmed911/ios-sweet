/* Separate static Mach-O. "once" exits 42 after two heartbeats; "stay"
 * continues so PID 1 can demonstrate both reaping and persistent service. */
#define SYS_exit    1
#define SYS_write   4
#define SYS_open    5
#define SYS_getpid 20
#define SYS_select 93

	.macro PRINT name
	adr x1, \name
	adr x2, \name\()_end
	sub x2, x2, x1
	bl write_console
	.endmacro
	.text
	.globl _start
	.p2align 2
_start:
	/* Read argc/argv before aligning the kernel-provided stack. */
	mov x8, sp
	ldr x9, [x8]
	cmp x9, #2
	b.ne hang
	ldr x9, [x8, #16]
	ldrb w20, [x9]
	mov x9, sp
	and x9, x9, #~15
	mov sp, x9
	adr x0, console_path
	mov x1, #2
	mov x2, #0
	mov x16, #SYS_open
	svc #0x80
	b.cs hang
	mov x19, x0
	mov x16, #SYS_getpid
	svc #0x80
	b.cs hang
	cmp x0, #1
	b.ls hang
	PRINT started
	mov x21, #0
loop:
	mov x0, #0
	mov x1, #0
	mov x2, #0
	mov x3, #0
	adr x4, five_sec
	mov x16, #SYS_select
	svc #0x80
	b.cs hang
	PRINT heartbeat
	add x21, x21, #1
	cmp w20, #'o'
	b.ne loop
	cmp x21, #2
	b.lo loop
	PRINT exiting
	mov x0, #42
	mov x16, #SYS_exit
	svc #0x80
hang:
	b hang
write_console:
	mov x0, x19
	mov x16, #SYS_write
	svc #0x80
	ret
	.p2align 3
five_sec:
	.quad 5, 0
console_path:
	.asciz "/dev/console"
started:
	.ascii "SWEET worker: exec successful, child PID verified\n"
started_end:
heartbeat:
	.ascii "SWEET worker: still alive\n"
heartbeat_end:
exiting:
	.ascii "SWEET worker: intentional exit 42\n"
exiting_end:
