/* Static PID 1 harness for the separate dynamically linked C executable. */
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
	sub sp, sp, #96
	adr x0, console
	mov x1, #2
	mov x2, #0
	mov x16, #5
	svc #0x80
	b.cs hang
	mov x19, x0
	/* Give dyld and libc real stdin/stdout/stderr descriptors. */
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
	PRINT started
	mov x16, #2
	svc #0x80
	b.cs failed
	cbnz x1, child
	mov x22, x0
	mov x23, #60
poll:
	mov x0, x22
	mov x1, sp
	mov x2, #1
	mov x3, #0
	mov x16, #7
	svc #0x80
	b.cs failed
	cbz x0, pause
	cmp x0, x22
	b.ne failed
	ldr w0, [sp]
	cbnz w0, bad_status
	PRINT passed
alive:
	bl sleep_one
	bl sleep_one
	bl sleep_one
	bl sleep_one
	bl sleep_one
	PRINT heartbeat
	b alive
pause:
	subs x23, x23, #1
	b.eq failed
	bl sleep_one
	b poll
child:
	adr x0, program
	str x0, [sp]
	str xzr, [sp, #8]
	adr x9, no_cache
	str x9, [sp, #16]
	str xzr, [sp, #24]
	mov x1, sp
	add x2, sp, #16
	mov x16, #59
	svc #0x80
	PRINT exec_error
	/* Exit 127 distinguishes an exec return from a running C program. */
	mov x0, #127
	mov x16, #1
	svc #0x80
	b hang
bad_status:
	mov w24, w0
	PRINT exited
	mov w10, w24
	adr x11, digits
	add x12, sp, #32
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
	add x1, sp, #32
	mov x2, #9
	bl output
failed:
	PRINT failure
hang:
	b hang
sleep_one:
	mov x0, #0
	mov x1, #0
	mov x2, #0
	mov x3, #0
	adr x4, one_sec
	mov x16, #93
	svc #0x80
	b.cc sleep_done
	cmp x0, #4
	b.eq sleep_one
	b failed
sleep_done:
	ret
output:
	mov x0, x19
	mov x16, #4
	svc #0x80
	ret
	.p2align 3
one_sec:
	.quad 1, 0
console:
	.asciz "/dev/console"
program:
	.asciz "/sbin/c-runtime-test"
no_cache:
	.asciz "DYLD_SHARED_REGION=avoid"
digits:
	.ascii "0123456789abcdef"
started:
	.ascii "SWEET dynamic init: starting C program via execve\n"
started_end:
passed:
	.ascii "SWEET dynamic init: C child exit 0 verified\n"
passed_end:
heartbeat:
	.ascii "SWEET dynamic init: still alive\n"
heartbeat_end:
exec_error:
	.ascii "SWEET dynamic init: execve failed\n"
exec_error_end:
exited:
	.ascii "SWEET dynamic init: bad C child wait status hex:\n"
exited_end:
failure:
	.ascii "SWEET dynamic init: TEST FAILED\n"
failure_end:
