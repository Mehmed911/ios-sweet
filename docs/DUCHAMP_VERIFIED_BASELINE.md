# Duchamp preserved baseline

The baseline is commit `60ae971`, not a fresh rewrite. Uncommitted source,
documentation, loader experiments and qemu-sweet.py changes remain user-owned.

| Component | Actual path | Evidence/scope |
| --- | --- | --- |
| ARM64 entry and ELF layout | duchamp/bootshim/start.S, shim.ld | Existing entry/FDT/EL guards preserved |
| Payload | tools/mkpayload.py | SWEETXNU v1; Mach-O fixups, flat segments, ADT, 608-byte argument area |
| Copy and handoff validation | duchamp/loader/plan.c, materialize.c; duchamp/bootshim/handoff_ready.c | Bounds/reservations checked before transfer |
| Image packer | duchamp/bootshim/pack_boot.py | Existing v4/LZ4 path retained; no MT6768 v2 packer substituted |
| MT6897 platform | duchamp/loader/mt6897_platform.c | Existing GIC, timer and inherited framebuffer facts |
| Device-tree handling | tools/inspect-duchamp-hardware.py, adt.py, qemu_ufs.py | Saved FDT and separately marked emulator ADT |
| Storage core | duchamp/drivers/ufs_readonly.c, ufs_gpt.c, ufs_register_snapshot.c | Real bounded command transport/GPT; physical backend disabled |
| Kernel storage adapter | duchamp/xnu/qemu_ufs.c, qemu_ufs_mcq.c, mt6897_ufs_observer_xnu.c | QEMU PCI and MT6897 read-only observation are separate |
| Physical historical evidence | duchamp/PHONE-PC-X0-FLASH-TRIAL.md; diagnostics/ | Historical logs only; no new phone trial authorized here |
| Recovery/menu models | duchamp/bootshim/test_boot_once_qemu.py, test_recovery_chain_qemu.py | Simulated slot/retention/return; not proof of LK choosing A |
| Userspace fixtures | tools/sweet-launchd-bootstrap.S, sweet-launchd-service.c, build-launchd-root.py | Separate diagnostic programs and supplied Darwin binaries; PID 1 alone does not prove iOS GUI |

Prior full-kernel CI `43631086106` built source
`7726168b844c7e00e24039cd93b8d0f4ed9a5e2d`. Its complete kernel SHA-256 is
`c6ebb7330ad393f19637f759b2ee35b0e4b2e66ae4f22b7cfde90c3f64ade4f3`.
Eleven full-XNU/QEMU cases passed; read-only GPT/HFS+ reached diagnostic PID 1
in 34.122 host seconds. Nine rejected cases left the virtual-UFS trace empty.
Those are prior results, not new physical-device measurements.

This port adds an opt-in standard INQUIRY and new metadata/policy adapters.
Fresh tests and complete-kernel build provenance are recorded in
[DUCHAMP_PORT_STATUS.md](DUCHAMP_PORT_STATUS.md). No existing image is overwritten.
