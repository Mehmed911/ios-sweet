# Duchamp DMA/IOMMU probe phone tests — 2026-11-01

## Result

The corrected v2 read-only probe loaded successfully, produced two
byte-identical reports, unloaded cleanly and left no staged module or sysfs
attribute behind. It issued no DMA mapping, IOMMU mapping/attachment, storage
command, MMIO access, SMC or partition operation.

The live UFS-device values are:

- streaming DMA mask: `0xffffffffffffffff` (64 bits);
- coherent DMA mask: `0xffffffffffffffff` (64 bits);
- `bus_dma_limit`: `0x0000000fffffffff` (36-bit address ceiling);
- `get_dma_ops(dev)` and `dev->dma_ops`: both `NULL`;
- device SWIOTLB pool pointer: present;
- Linux IOMMU private state, group, fwspec and domain: all absent;
- DMA coherency: false; DMA range map: present.

In the pinned GKI source, null DMA ops select the generic `dma-direct` path.
This does not prove physical firewall bypass, identity DMA addresses, use of
SWIOTLB by a transfer, or correct cache maintenance for XNU.

Machine-readable probe evidence:

- `research/mt6897-dma-ownership/live-probe-20261101-v1/result.json`
- SHA-256:
  `06673dadd8a2d1b91748ae333d773352ae823b8ebc5fb52b0adf2ffa88d3bae6`

## Successful v2 execution

- Kernel: `6.1.57-android14-11-gcf2c2dc91b9e-ab11782407`
- Probe size: 278200 bytes
- Probe SHA-256:
  `96cd9bf422f8924c1c11b33c92d042ec0ea7fb864e756712fe45e5261be27518`
- `insmod` exit: `0`
- Two reads completed and byte-identical: yes
- Kernel taint before/during: `12805` / `12805`
- `rmmod` exit: `0`
- Cleanup: module absent, attribute absent, staged file removed
- Android remained booted; no recovery action was required

## Rejected v1 attempt

### Preflight and artifact

- Device: `duchamp`
- Hardware: `mt6897`
- Kernel: `6.1.57-android14-11-gcf2c2dc91b9e-ab11782407`
- Root context: `u:r:magisk:s0`
- `modules_disabled`: `0`
- Probe and sysfs attribute: absent before the test
- Loaded-file SHA-256:
  `aa8e9c4356c7695cbeeddd3295764fe60cd54ba5f3a8b9ed7cb7e7f5175eac75`

### Failure evidence

- `insmod` exit: `255`
- ADB disconnected immediately.
- Android recovered by rebooting; `ro.boot.bootreason=kernel_panic`.
- Pstore file: `/sys/fs/pstore/console-ramoops-0`
- Pstore SHA-256:
  `c283f57a1d27a5237020eed880542f702e1802caeee727d4dedd2f9738e3256e`
- First fault: level-1 translation fault at `0x00000001b40001d0`.
- PC: `mod_sysfs_setup+0x208/0x418`.
- Process: `insmod`, PID 29891.
- Trace: `mod_sysfs_setup -> load_module -> __arm64_sys_finit_module`.

The trace proves the crash occurred while the kernel registered module sysfs,
before `do_init_module()` and before the probe's init function.

### Root cause

The v1 candidate's `.gnu.linkonce.this_module` section was `0x400` bytes. All
six captured vendor modules use `0x440`. Live kernel BTF independently reports:

- `struct module` size: 1088 (`0x440`)
- `btf_data_size` offset: `0x348`
- `btf_data` offset: `0x350`
- init offset: `0x170`
- exit offset: `0x3d8`
- four Android KABI reserve fields ending at offset `0x400`

The captured config requires `CONFIG_DEBUG_INFO_BTF_MODULES=y` and Pahole 1.23.
Because Pahole was missing during the first local `olddefconfig`, Kconfig
silently disabled the option. That removed `btf_data_size` and `btf_data`,
shifted every later field by 16 bytes and reduced the aligned structure size to
`0x400`. Injecting the captured `module_layout` CRC allowed this incompatible
structure to pass version checking.

### Recovery

After reboot:

- `sys.boot_completed=1`;
- the diagnostic module was absent;
- the diagnostic sysfs attribute was absent;
- the staged `.ko` was absent;
- no partition or boot image had been modified.

The unsafe binary was renamed with `.UNSAFE-DO-NOT-LOAD`. The verifier now
checks section size and init/exit relocation offsets. The corrected `0x440`
candidate is the v2 binary that subsequently passed the successful test above.

This closes the runtime-mask and Linux-IOMMU-state evidence gap. It does not
make physical UFS from XNU safe or make the phone port boot-ready.
