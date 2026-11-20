ENTRY(_start)
SECTIONS {
    . = 0x40200000;
    .text : { *(.text.entry) *(.text*) }
    .rodata : { *(.rodata*) }
    .data : { *(.data*) }
    .bss : { *(.bss*) *(COMMON) }
    . = 0x50700000;
    .lk : { *(.lk) }
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
