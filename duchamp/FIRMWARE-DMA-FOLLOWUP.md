# MT6897 firmware returns and UFS DMA limits — 2026-10-31

This follow-up checks saved UFS client code against pinned public sources,
executes a comparison firmware handler, and fixes separate descriptor/payload
limits in the production read-only UFS transport. No phone, USB, ADB, fastboot,
physical UFS or partition operation is involved. The installed monitor's effect
contract and the phone's active DMA route remain unverified; physical providers
stay closed.

## Separate address limits in the transport

The saved `ufshcd_memory_alloc()` contains three relocations to
`dmam_alloc_attrs`, with attributes zero, and alignment checks for 128, 1024
and 1024 bytes. They correspond to command, transfer and task-management
descriptors in the pinned source. The earlier mask audit established that
the saved client can ignore a failed coherent-mask setter after successful
streaming-mask setup. A successful streaming request therefore cannot supply
both effective limits.

`dufs_config` now requires `descriptor_address_bits` and `data_address_bits`
from the provider. The former bounds the list and command allocations; the
latter bounds the payload mapping. Zero or values above 64 are refused before
I/O. Complete allocation extents, including their final byte, must fit the
selected limit, remain inside the bus aperture, and not overlap.

The controller's CAP64 remains an independent ceiling checked at startup.
This check now uses each allocated extent rather than the end of a possibly
larger declared bus window. A low pool can fit a CAP32 controller even when
its declared bus aperture spans 64 GiB. This does not infer bypass, a DMA
domain, coherency, ownership, or effective masks from a DT window.

The QEMU-only XNU adapter explicitly supplies 64/64 for its private virtual
DMA pool. No such values are supplied to a physical MT6897 provider. Callers
must rebuild and fill both fields; omitted initializers are deliberately
rejected. Cached control-memory allocation and payload cache synchronization
remain provider responsibilities.

## New saved-client evidence

The selected saved module remains pinned to SHA-256
`7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493`.
All offsets below are `.text` offsets in that ET_REL file, not runtime
addresses. The auditor does not load the module for execution.

| Selected path | Confirmed instructions/relocations |
| --- | --- |
| MCQ query at call offset `0x1e80` | x0=`0xc2000276`, x1=`1024`, x2–x7 zero; relocation to `__arm_smccc_smc`. |
| Selected query continuation | Reads result a1 at stack-result offset +8. Zero sets the disable-MCQ capability bit `0x100`; this selected continuation does not inspect a0. |
| Allocation function `0x13198`, size `0x154` | Three calls to `dmam_alloc_attrs` at `0x131d4`, `0x13208`, `0x13248`, attrs=0; checks descriptor alignment at 128/1024/1024 bytes. |

`audit-duchamp-firmware-client.py` validates the complete query-fragment hash,
key instruction encodings, allocation symbol bounds, call relocation targets,
zero attributes, and alignment checks. It verifies the same 13 source Git blobs
and saved-audit provenance as [SAVED-UFS-CONTRACT.md](SAVED-UFS-CONTRACT.md).
It emits selected observations and hashes, not module bytes or private bootargs.

## What the comparison firmware proves

The comparison is the public MediaTek
[ufs_ctrl.c at f3083e2](https://chromium.googlesource.com/chromiumos/third_party/arm-trusted-firmware/+/f3083e2e6c508d58f9bce1b2fce5eeb0903a4c6d/plat/mediatek/drivers/ufs/ufs_ctrl.c),
Git blob `5cb9eb7f5f683a9d3c8f99be6dc209f27b7af266`, SHA-256
`6ff9b14399dfa9e8ac8ee822a09845b97fdae2872b355b2b2194a6e8e0c694e3`.
It is not identified as the installed MT6897 monitor.

The test extracts its unchanged `ufs_knl_ctrl()` and selector definitions,
then builds with MTCMOS absent and present. Both return zero for MTCMOS;
the absent build never calls the power hook. The reference also lacks the
vendor client's selector 1024. These observations prevent treating this
source as a complete installed-firmware contract.

Dependencies are explicit fixture hooks. The ARM64 test crosses EL1/EL3 through
the production raw conduit and a purpose-built monitor adapter. This tests
register transport and the selected reference C dispatch; it does not run the
phone's BL31, implement MediaTek power effects or establish its return ABI.
For both builds, the production firmware gate refuses unverified zero replies,
preserves caller output, and refuses a second call after the failure.

## Actual local results

Evidence stays under ignored `research/mt6897-routing/`:

| Test | Result | Scope |
| --- | --- | --- |
| `poll-v1` | 79 native ASan/UBSan and 79 ARM64 checks | Independent limits, unknown/invalid widths, exact/crossing 4-GiB ends, model CAP32 with wide aperture, existing bounded waits. |
| `transport-v1` | 242 checks and 78 native sanitizer guards | Actual emulated UFS DMA, six read-only cases including control32/data64 and control64/data32, plus framebuffer guards. |
| `firmware-check-v1` | 45 native +45 ARM64 per build, two builds; 28 actual fixture SMC calls | Unchanged comparison handler, conditional hook dispatch, unsupported requests and refused unverified replies. |
| `client-guards-v1.log` | Nine tests pass | Wrong selector/result instruction, allocation attributes/alignment, relocation, provenance/reference changes and existing-output preservation. |
| `compile-v1` | Both changed C translation units compile | Real generated XNU headers; full guest execution is separate. |

High-frequency qtest traffic and its images run on a Linux-native workspace,
copied through Windows UNC. Host images, saved inputs and sources are preserved.
Firmware test images use only small fixture logs. None of these tests measures
MT6897 timing, physical DMA or cache coherency.

Kernel source `8bdc163` built successfully in
[CI 41156122045](https://github.com/Mehmed911/ios-sweet/actions/runs/41156122045).
Artifact `13025606915` archive SHA-256 is
`83d290efcbdad3363ab4bf2abc576ad66eb0ba2dc56d0a9499d77a733f7216ae`;
kernel SHA-256 is
`8d47bba9d1f097cba15a4d4747ed28cc7f4026a7b65d87ad472eb6f8a83d731a`.
The API digest and packaged checksum manifest both match. Two new strict
guest replays with that kernel pass:

| Replay | Actual result |
| --- | --- |
| `guest-backends-v1` | 24/24, 36.569 host seconds; virtual UFS/HFS+ root, diagnostic PID1, read/EROFS/error paths and backend/table RAM checks. |
| `guest-baseline-v1` | 20/20, 36.376 host seconds; same read-only transport without the backend/table selftest. |

Both use the ARM QEMU profile from the previous bootstrap milestone, default
clock and 17 framebuffer samples, with zero undecodable glyphs and no panic
observed through the success heartbeat. Source, image and kernel hashes stay
unchanged. The backend receipt remains `fw_verified=0 physical=0`.
`final-verification.json` checks the source closures, saved module/public
references and all five original saved phone-input hashes. User changes are
preserved, and no QEMU process remains. These short guest tests establish no
physical DMA, long-term stability, installed-monitor effects or complete iOS.

## Reproduce without a phone

Use new output directories, keeping the saved artifacts and public source cache
outside Git:

```sh
python3 tools/fetch-duchamp-firmware-reference.py research/firmware-ref-new
python3 tools/test-duchamp-firmware-return.py research/firmware-return-new \
  --source research/firmware-ref-new
python3 tools/audit-duchamp-firmware-client.py research/firmware-client-new \
  --saved-audit research/mt6897-contract/audit-v3 \
  --sources research/mt6897-contract/replay-sources \
  --reference research/firmware-ref-new
python3 tools/test-duchamp-firmware-client-audit.py \
  --saved-audit research/mt6897-contract/audit-v3 \
  --reference research/firmware-ref-new
```

Run qtest on Linux-native storage to avoid high-frequency WSL `/mnt/c` I/O.
The new production core is tested with `tools/test-duchamp-driver-core.py`
and `tools/test-duchamp-ufs-poll.py`. The native Windows guest launcher from
[MT6897-BOOT-PLATFORM.md](MT6897-BOOT-PLATFORM.md) accepts the new kernel pin
above with `-Head 8bdc1633f1180b77a732def92be54501b9251eef -Run 41156122045`.
Use `research/mt6897-boot/ufs-profile-v4` with `-Backends`, or the locally
generated `research/mt6897-routing/baseline-fixture-v1` without that switch;
choose a fresh output. Neither launcher contacts the phone.

The remaining physical evidence is a matched monitor/build configuration,
per-service effects and secure ownership, runtime DMA ops/fwspec/domain and
both effective masks, HCCAP, and cache ownership. Passing these fixtures
does not supply that evidence or authorize a phone experiment.
