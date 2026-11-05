# MT6897/LK RAM transport provider

This provider connects the one-shot resident loader state machine to bytes
that LK has already loaded as part of a temporary Android boot image.  It is a
RAM-only source: it performs no USB, storage, partition, MMIO, SMC, clock,
reset, PHY or DMA operation.

## Documented boundary

The arm64 Linux boot contract used by the stock MT6897 LK loads an Image and
enters it with the FDT pointer in `x0`.  The saved Duchamp LK image contains
Fastboot, UDC and MTU3 strings, but neither those strings nor raw function
offsets define a callable ABI after LK transfers control.  The exact saved LK
sample currently recorded by the project is:

```text
SHA-256 f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a
```

HakiOS's published MediaTek MT6768 port uses the same safe shape: its
`chainboot.py` puts a bare-metal loader and a payload in the kernel bytes LK
loads, and the loader receives the FDT in `x0`.  It does not call back into
LK's USB implementation.  HakiOS's newer live Fastboot loader is instead a
Qualcomm UEFI/U-Boot implementation and exposes
`EFI_USB_DEVICE_PROTOCOL`; that controller contract is not portable to
MT6897/MTU3.

Accordingly, this milestone documents and implements only the inherited-RAM
contract.  Direct LK USB calls remain unavailable by design until a stable
runtime base, calling convention, ownership/lifetime rules and controller
state contract are all recovered and independently verified.

## Capsule

`tools/mk-duchamp-lk-capsule.py` produces a strict little-endian capsule:

| Offset | Size | Meaning |
| ---: | ---: | --- |
| `0x00` | 8 | `DUCHLKR1` |
| `0x08` | 4 | version, exactly 1 |
| `0x0c` | 4 | header size, exactly 64 |
| `0x10` | 8 | exact capsule size |
| `0x18` | 8 | nonzero loader generation |
| `0x20` | 8 | payload offset, exactly 64 |
| `0x28` | 8 | payload size |
| `0x30` | 8 | mutation receipt |
| `0x38` | 8 | immutable flag, exactly 1 |

The receipt detects accidental mutation but is not authentication.  AVB or a
separate signature policy must authenticate any image before this code sees
it.

The provider rejects unknown versions or flags, stale generations, truncated
or trailing bytes, invalid sizes, non-sequential reads and a changed receipt.
The transport copies through a disjoint bounded scratch area, feeds only
sequential chunks into `resident_protocol`, recomputes the receipt after the
complete transfer, and then invokes the existing prepare/enter callbacks.
The capsule backing range must also be disjoint from staging, result and
scratch memory, so a provider cannot overwrite its own input while copying.
Any failure terminally closes that transport instance; using it again requires
a fresh RAM boot.

## Local verification

From WSL, with a new output directory:

```sh
sh duchamp/loader/test_mt6897_lk_transport.sh /tmp/duchamp-lk-transport \
  work/phone-fdt.bin work/payload.bin
```

The suite runs native ASan/UBSan negative tests, tests the capsule packer,
links the provider as a freestanding AArch64 object with no unresolved
imports, materializes a real XNU payload through the capsule provider when the
optional FDT and payload are supplied, and executes the complete
capsule-to-resident flow as AArch64 code under QEMU GICv3.  It does not touch a
phone.
