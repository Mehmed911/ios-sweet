# Duchamp firmware evidence

These observations come from read-only ADB pulls of the active slot. No
partition was written.

| Image | Size | SHA-256 |
|---|---:|---|
| `lk_a` | 16 MiB | `F85373D3B4CDF3C959E38BBBFE198A2857E03A5266C6F2A40C319549A5BA957A` |
| `preloader_raw_a` | 4,190,208 bytes | `6E9B62813D4466B8143F6DDD2064E3C9CC177AB8A897AA0A586D636C3C526C99` |

## Confirmed strings

The MT6897 preloader contains platform source paths under
`platform/mt6897`, DRAM initialization and training routines, memory-layout
and DRAM-size reporting, and the LK handoff path. This confirms that DRAM is
owned and initialized before LK; the XNU loader must not attempt to retrain or
reconfigure it.

The device LK contains MT6897-specific GIC, MMU, framebuffer, display, FDT,
`boot_linux_from_storage`, `target_atag_videolfb`, and `hwid.project_name=duchamp`
symbols/strings. It also contains MediaTek SMC call sites. These are evidence
of the vendor boot flow, not yet a recovered callable ABI.

## Raw AArch64 instruction scan

Capstone found MMU/cache instructions in the raw LK image at these file
offsets: `SCTLR_EL1` reads/writes near `0x214` and `0x48c`, `MAIR_EL1` at
`0x45c`, `TCR_EL1` at `0x46c`, `TTBR0_EL1`/`TTBR1_EL1` at `0x474`/`0x478`,
TLBI near `0x44c` and `0x4a4`, and cache maintenance sequences near `0x58ac`
through `0x5af0`. These are raw-file offsets, not callable runtime addresses;
relocation and the LK load base still have to be recovered.

The surrounding routine at raw offset `0x200` performs the following observed
sequence: reads `CurrentEL`, builds page-table entries, invalidates the EL1
translation cache, writes `MAIR_EL1`, writes `TCR_EL1`, installs `TTBR1_EL1`,
sets `VBAR_EL1`, enables `SCTLR_EL1.M`, and invalidates again. The literal used
for `TCR_EL1` is `0x00ff0400`; its granule fields indicate the vendor LK is
using a different translation setup from the XNU 16 KiB payload. This routine
must not be copied into the XNU handoff without reconstructing its load base,
table layout, memory attributes, and exception-level assumptions.

## Consequence for the backend

The next implementation target is an LK-compatible handoff adapter that
preserves the vendor MMU, GIC, DRAM, and display state and consumes the live
FDT. It must not copy Qualcomm constants or retrain DRAM. Before any RAM-only
test, the adapter still needs a controlled entry point and register contract
from disassembly or a documented LK interface.
