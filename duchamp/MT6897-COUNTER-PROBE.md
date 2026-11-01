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

## Full-XNU QEMU result

GitHub Actions run `41328290431` built commit
`9c415f586d2e49fa94dcc7653059e802c3db3269` successfully. The downloaded
`kernel.development.sweet` is a 64-bit ARM64 Mach-O with SHA-256
`1363b519447822791ad8c9fb0e3a6af993cc2b321cba5148584e27bef96b88d8`.
Its artifact ZIP digest exactly matched GitHub's recorded digest.

The kernel was packed with the pinned QEMU ADT
`be512dce04bf581d188440246b4e3402de057a43f4c178da7984a68ccbb9ba2f`
and `duchamp_counter_probe=1`. With the Duchamp framebuffer geometry, full XNU
reached `SWEET EARLY 23: DUCHAMP COUNTER PROBE PASS` after 6.39 host seconds.
The final screen contained three undecodable cells from the colored marker, so
the generic screen decoder reported `incomplete_decode`; the explicit PASS
stop marker and absence of FAIL/panic are the authoritative result for this
diagnostic. `tools/verify-duchamp-counter-probe-xnu.py` verifies those facts
and pins the kernel, payload and ADT hashes.

An initial negative run deliberately using the old `sweet` framebuffer
geometry stopped earlier in `pmap_map_bd`. Re-running the identical payload
with the current Duchamp `1220x2712` geometry reached the counter PASS marker.
Neither run accessed a phone, executed an SMC, or modified a partition.
