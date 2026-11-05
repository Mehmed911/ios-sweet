ENTRY(_head)
SECTIONS
{
	. = DEFINED(DUCHAMP_IMAGE_BASE) ? DUCHAMP_IMAGE_BASE : 0;
	.text : { *(.text.head) *(.text*) }
	.rodata : { *(.rodata*) }
	.data : { *(.data*) }
	. = ALIGN(16);
	_bss_start = .;
	.bss : { *(.bss*) *(COMMON) }
	. = ALIGN(16);
	_bss_end = .;
	. += 0x8000;
	. = ALIGN(16);
	_stack_top = .;
	.payload : { KEEP(*(.payload)) }
	. = ALIGN(16);
	.lkram : {
		duchamp_lk_ram_capsule_start = .;
		KEEP(*(.lkram))
		duchamp_lk_ram_capsule_end = .;
	}
	_end = .;
	/DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
