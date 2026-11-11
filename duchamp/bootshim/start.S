#if defined(DUCHAMP_PHONE_LAYOUT_ONLY) && defined(DUCHAMP_QEMU_ONLY)
#error "phone-layout and QEMU-only guards are mutually exclusive"
#endif
#if defined(DUCHAMP_PHONE_CAPTURE) && (defined(DUCHAMP_PHONE_LAYOUT_ONLY) || defined(DUCHAMP_QEMU_ONLY))
#error "phone capture is separate from fixed-layout and QEMU-only guards"
#endif
#if defined(DUCHAMP_QEMU_RECOVERY_CHAIN) && !defined(DUCHAMP_QEMU_ONLY)
#error "the Linux recovery chain requires QEMU virt"
#endif

	.section .text.head, "ax"
	.globl _head
_head:
	b	_start
	.long	0
	.quad	0
	.quad	_end - _head
	.quad	0xa
	.quad	0, 0, 0
	.ascii	"ARM\x64"
	.long	0

	.text
	.globl _start
_start:
	msr	daifset, #0xf
	mov	x19, x0
	mov	x20, x1
	mov	x21, x2
	mov	x22, x3
	mov	x23, sp
#if defined(DUCHAMP_PHONE_LAYOUT_ONLY)
	.globl duchamp_phone_layout_guard
duchamp_phone_layout_guard:
	adr	x11, _head
	movz	x9, #0x4000, lsl #16
	cmp	x11, x9
	b.ne	halt
	movz	x10, #0x47c8, lsl #16
	cmp	x19, x10
	b.ne	halt
	.globl duchamp_phone_layout_stop
duchamp_phone_layout_stop:
	b	halt
#endif
#if defined(DUCHAMP_QEMU_ONLY)
	adr	x11, _head
	movz	x9, #0x4020, lsl #16
	cmp	x11, x9
	b.ne	halt
	movz	x10, #0x4800, lsl #16
	cmp	x19, x10
	b.ne	halt
#endif
	mrs	x24, CurrentEL
	cmp	x24, #8
	b.eq	entry_el2
	cmp	x24, #4
	b.ne	halt
	mrs	x25, sctlr_el1
	msr	spsel, #1
	adr	x0, _stack_top
	mov	sp, x0
	adr	x0, vectors
	msr	vbar_el1, x0
	b	entry_common
entry_el2:
	mrs	x25, sctlr_el2
	msr	spsel, #1
	adr	x0, _stack_top
	mov	sp, x0
	adr	x0, vectors
	msr	vbar_el2, x0
entry_common:
	isb
	adr	x0, _bss_start
	adr	x1, _bss_end
1:	cmp	x0, x1
	b.hs	2f
	str	xzr, [x0], #8
	b	1b
2:	adr	x0, duchamp_bootshim_entry_state
	stp	x24, x25, [x0]
	stp	x19, x20, [x0, #16]
	stp	x21, x22, [x0, #32]
	str	x23, [x0, #48]
#if defined(DUCHAMP_PHONE_CAPTURE)
	.globl duchamp_phone_capture_store_entry_pc
duchamp_phone_capture_store_entry_pc:
	adr	x1, _head
	adr	x2, duchamp_bootshim_runtime_head
	str	x1, [x2]
#endif
	bl	duchamp_bootshim_main
halt:
	wfe
	b	halt

	.balign 2048
vectors:
	.rept 4
	.balign 128
	b	exception_sync
	.balign 128
	b	exception_irq
	.balign 128
	b	exception_fiq
	.balign 128
	b	exception_serror
	.endr

exception_sync:
	mov	x0, #1
	b	exception_capture
exception_irq:
	mov	x0, #2
	b	exception_capture
exception_fiq:
	mov	x0, #3
	b	exception_capture
exception_serror:
	mov	x0, #4
exception_capture:
	mrs	x5, CurrentEL
	cmp	x5, #8
	b.eq	exception_capture_el2
	mrs	x1, esr_el1
	mrs	x2, elr_el1
	mrs	x3, far_el1
	b	exception_call
exception_capture_el2:
	mrs	x1, esr_el2
	mrs	x2, elr_el2
	mrs	x3, far_el2
exception_call:
	mov	x4, sp
	bl	duchamp_bootshim_exception
	b	halt

#if defined(DUCHAMP_QEMU_RECOVERY_CHAIN)
	.globl duchamp_qemu_enter_linux
duchamp_qemu_enter_linux:
	msr	daifset, #0xf
	dsb	sy
	ic	iallu
	dsb	sy
	isb
	mov	x16, x0
	mov	x0, x1
	mov	x1, xzr
	mov	x2, xzr
	mov	x3, xzr
	br	x16
#endif

#if defined(DUCHAMP_XNU_JUMP)
	.globl duchamp_enter_xnu
duchamp_enter_xnu:
	msr	daifset, #0xf
	dsb	sy
	ic	iallu
	dsb	sy
	isb
	mov	x16, x0
	mov	x0, x1
	br	x16
#endif

#if defined(DUCHAMP_XNU_RETURN)
	.globl duchamp_xnu_return_stub
duchamp_xnu_return_stub:
	msr	daifset, #0xf
	adr	x6, _stack_top
	mov	sp, x6
	bl	duchamp_bootshim_xnu_return
1:	wfe
	b	1b
#endif
