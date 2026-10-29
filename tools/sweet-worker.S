/* Separate static Mach-O. "once" exits 42 after two heartbeats; "stay"
 * continues so PID 1 can demonstrate both reaping and persistent service. */
#define SYS_exit    1
#define SYS_read    3
#define SYS_write   4
#define SYS_open    5
#define SYS_close   6
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
	sub sp, sp, #64
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
	/* Write, close, reopen, read, compare all bytes, then require EOF. */
	adr x0, data_path
	mov x1, #0x601
	mov x2, #0600
	mov x16, #SYS_open
	svc #0x80
	b.cs failed
	mov x22, x0
	mov x23, x0
	adr x24, file_payload
	mov x25, #18
	bl write_all
	mov x0, x22
	mov x16, #SYS_close
	svc #0x80
	b.cs failed
	adr x0, data_path
	mov x1, #0
	mov x2, #0
	mov x16, #SYS_open
	svc #0x80
	b.cs failed
	mov x22, x0
	mov x23, x0
	mov x24, sp
	mov x25, #18
	bl read_all
	mov x9, sp
	adr x10, file_payload
	mov x11, #18
compare_file:
	ldrb w12, [x9], #1
	ldrb w13, [x10], #1
	cmp w12, w13
	b.ne failed
	subs x11, x11, #1
	b.ne compare_file
	mov x0, x22
	add x1, sp, #32
	mov x2, #1
	mov x16, #SYS_read
	svc #0x80
	b.cs failed
	cbnz x0, failed
	mov x0, x22
	mov x16, #SYS_close
	svc #0x80
	b.cs failed
	PRINT file_ok
	/* fd 3 was installed by PID 1 before exec; close it to signal EOF. */
	mov x23, #3
	adr x24, ipc_payload
	mov x25, #8
	bl write_all
	mov x0, #3
	mov x16, #SYS_close
	svc #0x80
	b.cs failed
	PRINT ipc_sent
	mov x21, #0
loop:
	mov x0, #0
	mov x1, #0
	mov x2, #0
	mov x3, #0
	adr x4, five_sec
	mov x16, #SYS_select
	svc #0x80
	b.cs failed
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
failed:
	PRINT failure
	mov x0, #99
	mov x16, #SYS_exit
	svc #0x80
	b hang
write_all:
	mov x0, x23
	mov x1, x24
	mov x2, x25
	mov x16, #SYS_write
	svc #0x80
	b.cs failed
	cbz x0, failed
	add x24, x24, x0
	subs x25, x25, x0
	b.ne write_all
	ret
read_all:
	mov x0, x23
	mov x1, x24
	mov x2, x25
	mov x16, #SYS_read
	svc #0x80
	b.cs failed
	cbz x0, failed
	add x24, x24, x0
	subs x25, x25, x0
	b.ne read_all
	ret
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
data_path:
	.asciz "/sbin/worker-data"
file_payload:
	.ascii "SWEET RAM FILE OK\n"
ipc_payload:
	.ascii "READYv1\n"
started:
	.ascii "SWEET worker: exec successful, child PID verified\n"
started_end:
file_ok:
	.ascii "SWEET worker: RAM file bytes and EOF verified\n"
file_ok_end:
ipc_sent:
	.ascii "SWEET worker: IPC READYv1 sent and closed\n"
ipc_sent_end:
heartbeat:
	.ascii "SWEET worker: still alive\n"
heartbeat_end:
exiting:
	.ascii "SWEET worker: intentional exit 42\n"
exiting_end:
failure:
	.ascii "SWEET worker: TEST FAILED\n"
failure_end:
