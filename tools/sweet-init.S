/*
 * QEMU diagnostic PID 1 for a writable HFS RAM root. Installs an independent,
 * ad-hoc signed Mach-O worker, forks/execs it, checks its intentional first
 * exit with wait4, tests stop/continue/terminate on its replacement, then
 * restarts a final worker in persistent heartbeat mode.
 *
 * Build with tools/build-sweet-userland.sh. All references are PC-relative;
 * mutable state lives in registers/stack. XNU arm64 syscalls use x16 and
 * svc #0x80, with carry set on error. PID 1 never exits.
 */
#define SYS_exit    1
#define SYS_fork    2
#define SYS_read    3
#define SYS_write   4
#define SYS_open    5
#define SYS_close   6
#define SYS_wait4   7
#define SYS_getpid 20
#define SYS_kill   37
#define SYS_pipe   42
#define SYS_execve 59
#define SYS_dup2   90
#define SYS_select 93
#define O_RDWR     2
#define O_CREATE   0x601
#define MODE_0755  0755
#define SIGTERM   15
#define SIGSTOP   17
#define SIGCONT   19

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
	mov x9, sp
	and x9, x9, #~15
	mov sp, x9
	sub sp, sp, #64
	adr x0, console_path
	mov x1, #O_RDWR
	mov x2, #0
	mov x16, #SYS_open
	svc #0x80
	b.cs hang
	mov x19, x0
	mov x16, #SYS_getpid
	svc #0x80
	b.cs failed
	cmp x0, #1
	b.ne failed
	PRINT hello

	adr x0, worker_path
	mov x1, #O_CREATE
	mov x2, #MODE_0755
	mov x16, #SYS_open
	svc #0x80
	b.cs failed
	mov x23, x0
	adr x24, worker_head
	mov x25, #4096
	bl write_all
	/* Reproduce the standard 16K Mach-O layout without embedding 12K of
	 * repeated zero padding in init. The build checks the skipped bytes. */
	mov x26, #3
padding:
	adr x24, zero_page
	mov x25, #4096
	bl write_all
	subs x26, x26, #1
	b.ne padding
	adr x24, worker_signature
	adr x25, worker_signature_end
	sub x25, x25, x24
	bl write_all
	mov x0, x23
	mov x16, #SYS_close
	svc #0x80
	b.cs failed
	PRINT installed
	mov x27, #0
spawn_worker:
	/* pipe returns the read descriptor in x0 and write descriptor in x1. */
	mov x16, #SYS_pipe
	svc #0x80
	b.cs failed
	mov x20, x0
	mov x21, x1
	mov x16, #SYS_fork
	svc #0x80
	b.cs failed
	/* XNU returns x1=1 in the child, x1=0 in the parent. */
	cbnz x1, child
	mov x22, x0
	PRINT spawned
	mov x0, x21
	mov x16, #SYS_close
	svc #0x80
	b.cs failed
	/* Require the exec'd worker's exact READYv1 message and writer EOF. */
	mov x23, x20
	mov x24, sp
	mov x25, #8
	bl read_all
	ldr x9, [sp]
	adr x10, ipc_payload
	ldr x10, [x10]
	cmp x9, x10
	b.ne failed
	mov x0, x20
	mov x1, sp
	mov x2, #1
	mov x16, #SYS_read
	svc #0x80
	b.cs failed
	cbnz x0, failed
	mov x0, x20
	mov x16, #SYS_close
	svc #0x80
	b.cs failed
	PRINT ipc_ok
	b tick
child:
	/* Close the read endpoint and inherit the writer as fd 3 across exec. */
	mov x0, x20
	mov x16, #SYS_close
	svc #0x80
	b.cs child_failed
	mov x0, x21
	mov x1, #3
	mov x16, #SYS_dup2
	svc #0x80
	b.cs child_failed
	cmp x21, #3
	b.eq child_exec
	mov x0, x21
	mov x16, #SYS_close
	svc #0x80
	b.cs child_failed
child_exec:
	adr x0, worker_path
	str x0, [sp]
	adr x9, once_arg
	adr x10, stay_arg
	cmp x27, #0
	csel x9, x9, x10, eq
	str x9, [sp, #8]
	str xzr, [sp, #16]
	mov x1, sp
	mov x2, #0
	mov x16, #SYS_execve
	svc #0x80
child_failed:
	PRINT exec_failed
	mov x0, #127
	mov x16, #SYS_exit
	svc #0x80
	b hang
tick:
	bl sleep_five
	PRINT alive
	mov x0, x22
	mov x1, sp
	mov x2, #1                    /* WNOHANG */
	mov x3, #0
	mov x16, #SYS_wait4
	svc #0x80
	b.cs failed
	cbz x0, running_worker
	cmp x0, x22
	b.ne failed
	ldr w28, [sp]
	PRINT reaped
	mov w0, w28
	bl print_hex
	/* First worker deliberately exits 42. Require exactly that status;
	 * an unexpected crash/exec failure must not become a restart loop. */
	cmp x27, #0
	b.ne failed
	mov w9, #0x2a00
	cmp w28, w9
	b.ne failed
	PRINT restart
	mov x27, #1
	b spawn_worker
running_worker:
	cmp x27, #1
	b.ne tick
	/* Operate only on our positive child PID, never on a process group. */
	PRINT stop_sending
	mov x1, #SIGSTOP
	bl signal_worker
	mov w24, #0x117f             /* W_STOPCODE(SIGSTOP) */
	mov w25, #3                  /* WNOHANG | WUNTRACED */
	bl wait_event
	PRINT stop_verified
	mov w0, w28
	bl print_hex
	bl sleep_five
	PRINT stopped_hold
	PRINT cont_sending
	mov x1, #SIGCONT
	bl signal_worker
	mov w24, #0x137f             /* W_STOPCODE(SIGCONT) */
	mov w25, #17                 /* WNOHANG | WCONTINUED */
	bl wait_event
	PRINT cont_verified
	mov w0, w28
	bl print_hex
	/* Leave time for fresh worker output after continuation. */
	bl sleep_five
	bl sleep_five
	PRINT resumed_window
	PRINT term_sending
	mov x1, #SIGTERM
	bl signal_worker
	mov w24, #15                 /* WTERMSIG == SIGTERM, no core flag */
	mov w25, #1                  /* WNOHANG */
	bl wait_event
	PRINT term_verified
	mov w0, w28
	bl print_hex
	/* After wait4 reaps it, kill(pid, 0) must fail with ESRCH (3). */
	mov x0, x22
	mov x1, #0
	mov x2, #1
	mov x16, #SYS_kill
	svc #0x80
	b.cc failed
	cmp x0, #3
	b.ne failed
	PRINT absent_verified
	PRINT signal_restart
	mov x27, #2
	b spawn_worker
signal_worker:
	cmp x22, #1
	b.ls failed
	mov x0, x22
	mov x2, #1                  /* POSIX kill, one positive PID */
	mov x16, #SYS_kill
	svc #0x80
	b.cs failed
	ret
wait_event:
	/* Poll for one specific wait4 event, at most 50 times with 100ms sleeps. */
	mov x26, #50
wait_poll:
	mov x0, x22
	mov x1, sp
	mov x2, x25
	mov x3, #0
	mov x16, #SYS_wait4
	svc #0x80
	b.cs failed
	cbz x0, wait_pause
	cmp x0, x22
	b.ne failed
	ldr w28, [sp]
	cmp w28, w24
	b.ne failed
	ret
wait_pause:
	subs x26, x26, #1
	b.eq failed
	mov x0, #0
	mov x1, #0
	mov x2, #0
	mov x3, #0
	adr x4, short_pause
	mov x16, #SYS_select
	svc #0x80
	b.cc wait_poll
	cmp x0, #4                  /* EINTR: recheck the event */
	b.eq wait_poll
	b failed
sleep_five:
	mov x0, #0
	mov x1, #0
	mov x2, #0
	mov x3, #0
	adr x4, five_sec
	mov x16, #SYS_select
	svc #0x80
	b.cc sleep_done
	cmp x0, #4                  /* EINTR */
	b.eq sleep_five
	b failed
sleep_done:
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
write_console:
	mov x0, x19
	mov x16, #SYS_write
	svc #0x80
	ret
print_hex:
	/* One complete hex status line; preserve the caller's LR. */
	stp x29, x30, [sp, #-32]!
	mov w10, w0
	adr x11, digits
	add x12, sp, #16
	mov x13, #8
hex_loop:
	lsr w14, w10, #28
	ldrb w14, [x11, x14]
	strb w14, [x12], #1
	lsl w10, w10, #4
	subs x13, x13, #1
	b.ne hex_loop
	mov w14, #10
	strb w14, [x12]
	add x1, sp, #16
	mov x2, #9
	bl write_console
	ldp x29, x30, [sp], #32
	ret
failed:
	PRINT failure
hang:
	b hang
	.p2align 3
five_sec:
	.quad 5, 0
short_pause:
	.quad 0, 100000
console_path:
	.asciz "/dev/console"
worker_path:
	.asciz "/sbin/worker"
once_arg:
	.asciz "once"
stay_arg:
	.asciz "stay"
digits:
	.ascii "0123456789abcdef"
ipc_payload:
	.ascii "READYv1\n"
hello:
	.ascii "\n*** SWEET userspace: init running as PID 1 ***\n"
hello_end:
installed:
	.ascii "SWEET init: worker file installed\n"
installed_end:
spawned:
	.ascii "SWEET init: worker forked\n"
spawned_end:
ipc_ok:
	.ascii "SWEET init: IPC READYv1 and EOF verified\n"
ipc_ok_end:
alive:
	.ascii "SWEET init: still alive\n"
alive_end:
reaped:
	.ascii "SWEET init: wait4 reaped worker, status hex:\n"
reaped_end:
restart:
	.ascii "SWEET init: restarting worker in stay mode\n"
restart_end:
stop_sending:
	.ascii "SWEET init: SIGSTOP sending\n"
stop_sending_end:
stop_verified:
	.ascii "SWEET init: SIGSTOP wait4 verified\n"
stop_verified_end:
stopped_hold:
	.ascii "SWEET init: stopped hold complete\n"
stopped_hold_end:
cont_sending:
	.ascii "SWEET init: SIGCONT sending\n"
cont_sending_end:
cont_verified:
	.ascii "SWEET init: SIGCONT wait4 verified\n"
cont_verified_end:
resumed_window:
	.ascii "SWEET init: resumed heartbeat window complete\n"
resumed_window_end:
term_sending:
	.ascii "SWEET init: SIGTERM sending\n"
term_sending_end:
term_verified:
	.ascii "SWEET init: SIGTERM wait4 verified\n"
term_verified_end:
absent_verified:
	.ascii "SWEET init: terminated worker ESRCH verified\n"
absent_verified_end:
signal_restart:
	.ascii "SWEET init: restarting after SIGTERM\n"
signal_restart_end:
exec_failed:
	.ascii "SWEET child: execve failed\n"
exec_failed_end:
failure:
	.ascii "SWEET init: TEST FAILED\n"
failure_end:
	.p2align 3
worker_head:
	.incbin "sweet-worker.macho", 0, 4096
worker_signature:
	.incbin "sweet-worker.macho", 16384
worker_signature_end:
zero_page:
	.space 4096
