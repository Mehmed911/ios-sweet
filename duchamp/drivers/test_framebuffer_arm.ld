ENTRY(_start)
SECTIONS {
    /* Leave QEMU virt's default 1 MiB DTB reservation untouched. */
    . = 0x40200000;
    .text : { KEEP(*(.text.entry)) *(.text*) }
    .rodata : { *(.rodata*) }
    .data : { *(.data*) }
    .bss : { *(.bss*) *(COMMON) }
    . = ALIGN(16);
    . += 0x10000;
    __stack_top = .;
    /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
