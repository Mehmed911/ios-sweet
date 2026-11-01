# MT6897 pre-GIC architected-counter probe

This diagnostic closes only the next narrow timer question. It is opt-in via
`duchamp_counter_probe=1` and runs immediately after
`cpu_machine_idle_init(TRUE)`, before `PE_init_platform(TRUE)`, GIC setup and
`cpu_timebase_init(TRUE)`.

The probe:

- reads `CNTFRQ_EL0` and requires the ADT-derived frequency;
- reads `CNTVCT_EL0` until it advances or one million polls are exhausted;
- prints PASS or FAIL to the already proven framebuffer console;
- stops in both cases before any GIC, timer-register write, SMC or device MMIO.

Without the exact boot argument, the probe performs no register read and the
normal XNU path is unchanged. The pure validation helper is tested natively
under ASan/UBSan. A freestanding AArch64 test executes real `CNTFRQ_EL0` and
`CNTVCT_EL0` reads on QEMU and expects QEMU virt's 62.5 MHz counter. This QEMU
result does not prove the 13 MHz MT6897 counter on the phone.

No phone image has been executed for this probe. A future phone test must be a
separately approved RAM-only `fastboot boot` attempt. If the bootloader rejects
RAM-only boot, stop; do not fall back to flashing or modifying a boot slot.
Even a phone PASS would prove only counter readability and progress under XNU.
It would not prove GIC ownership, PPI 27 delivery, `rtclock_intr()`, scheduler
timing, firmware effects or UFS ownership.
