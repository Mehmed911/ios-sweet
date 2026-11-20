/* SPDX-License-Identifier: 0BSD */
/* Run as a static LC_UNIXTHREAD child. Inherit the dynamic parent's stdout. */
	.text
	.globl _start
	.p2align 2
_start:
	mov	x0, #1
	adr	x1, message
	adr	x2, message_end
	sub	x2, x2, x1
	mov	x19, x2
	mov	x16, #4		/* write */
	svc	#0x80
	b.cs	failed
	cmp	x0, x19
	b.ne	failed
	mov	x0, #42
	b	exit
failed:
	mov	x0, #43
exit:
	mov	x16, #1		/* exit */
	svc	#0x80
	brk	#0
message:
	.ascii	"RAMROOT STATIC: entered LC_UNIXTHREAD child\n"
message_end:
