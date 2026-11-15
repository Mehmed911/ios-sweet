# Duchamp MT6897 UFS initialization design

## Decision

Prefer independent, exclusive, cold initialization from XNU as the design
target. That approach establishes readiness through supported platform
operations and readbacks. It still needs a verified delegation from the
firmware and a safe initial DMA state. Physical initialization and queue
inspection are disabled today. The model added here exercises the
sequence and refusal rules without registering a kernel backend.
[LK shutdown analysis](DUCHAMP_UFS_LK_SHUTDOWN_ANALYSIS.md)

| Approach | What it would need | Main risk and disposition |
| --- | --- | --- |
| A. Preserve resources across LK/BL31 handoff | A supported post-cleanup, same-boot record with matching firmware, Slot B, boot ID and XNU entry. It must prove HCE/link state, inherited queue and DMA drain, resource ownership, access rights and the lifetime of clocks, rails and PHY. Reconfigure XNU to use only resources covered by the contract. | The sampled LK actively shuts down the controller, and later BL31 behavior is incomplete. Reusing a retained list or guessing a power/clock state could let inherited DMA run. Leave A unavailable absent such a contract. |
| B. Initialize independently | A trusted cold-init grant for the exact MT6897 resources and effective MMIO access, a verified drain or isolation at entry, supported power/clock/reset/PHY operations, authorized direct DMA or IOMMU and cache ownership, and an interrupt policy. Add a board-specific XNU provider after those prerequisites are verified. | Reset, power transitions and incorrect DMA routing can affect shared hardware or memory. Use a clean, exclusive baseline, bounded acknowledgments and fail-closed recovery. This is the preferred design, with physical support still blocked. |

## Source comparison

The captured Duchamp FDT fixes the HCI at `0x112b0000` / `0x3000` and
the M-PHY at `0x112a0000` / `0x10000`. The UFS node declares
`mediatek,ufs-rtff-mtcmos`, `vcc`, `vccq`, `dvfsrc-vcore`,
12 clocks and `unipro_rst`, `crypto_rst`, `hci_rst`. It lacks
`power-domains` at the HCI node. The saved M-PHY version is 1.
The topology and Android state describe this board and capture.
A live grant for XNU at entry has to come from a verified provider.
[Duchamp inventory](../devices/duchamp/hardware.json)

| Layer | Pinned Linux behavior and XNU requirement |
| --- | --- |
| Platform and HCI initialization | `ufs_mtk_probe` calls the common `ufshcd_pltfrm_init`, which maps the resource, gets IRQ 0 and parses clock/regulator dependencies. `ufshcd_init` calls `ufshcd_hba_init` ahead of capability reads, DMA allocation and interrupt setup. Obtain explicit access for each range and verify resources before access. [MiCode probe](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L3106-L3152), [common platform probe](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/host/ufshcd-pltfrm.c#L337-L393), [common host setup](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/core/ufshcd.c#L10376-L10447) |
| Power, firmware and clocks | Common `ufshcd_hba_init` enables regulators and clocks before variant initialization. MediaTek `ufs_mtk_init` binds its dependencies, requests PHY power, invokes RTFF restore and MTCMOS-on, then applies its clock setup. `ufs_mtk_setup_ref_clk` has pre/post firmware notifications and a request/ACK path. The MT6897 TOPCKGEN muxes and UFS AO/PDN gate providers are separate resources, and the PHY/reference clocks have their own contract. [Common HBA init](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/core/ufshcd.c#L9311-L9364), [MediaTek power sequence](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L1524-L1627), [ref-clock handshake](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L416-L470), [MT6897 muxes](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/clk/mediatek/clk-mt6897.c#L2457-L2477), [AO/PDN gates](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/clk/mediatek/clk-mt6897-peri.c#L274-L327) |
| M-PHY and host/device reset | Generic PHY power callbacks return early for nonzero `mphy-ver`, leaving the legacy direct register sequence for version 0. Verify version 1 PHY readiness from the supported provider. `ufs_mtk_hce_enable_notify` can assert HCI/crypto/UniPro, delay and deassert in reverse order. Its M-PHY reset handle is commented out in the init path. The separate device reset hook controls the device reset line and stops HBA. Require checked reset results and validate reference/PHY readiness after the host reset. [M-PHY driver](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/phy/mediatek/phy-mtk-ufs.c#L152-L179), [host reset and HCE hook](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L276-L350), [device reset](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L1935-L1958) |
| DMA, IOMMU and cache | The Linux core negotiates streaming/coherent limits and allocates descriptor memory through the DMA API. DT setup resolves DMA ranges and calls `of_iommu_configure`; ARM64 installs IOMMU ops if a translated route applies and sets coherency. The saved FDT declares an identity `/soc/dma-ranges` over 36 bits and no HCI `iommus` property. The Android direct-DMA observations are useful leads. XNU must verify its effective PA-to-device-DMA path, address limits for descriptors and buffers, any bounce policy, firewall and cache maintenance. An IOMMU route needs verified attachment and ownership of its stream, domain, tables and mapping lifetime. [DMA mask and allocation](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/core/ufshcd.c#L10299-L10336), [DT DMA setup](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/of/device.c#L114-L218), [OF IOMMU](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/iommu/of_iommu.c#L111-L151), [ARM64 DMA setup](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/arch/arm64/mm/dma-mapping.c#L65-L82), [saved DMA evidence](../duchamp/MT6897-DMA-IOMMU-FIRMWARE-EVIDENCE.md) |
| HCE and UIC Link Startup | The core waits for HCE, invokes MediaTek pre/post link hooks around `DME_LINK_STARTUP`, checks device presence and starts the HBA's own configured lists. XNU needs bounded confirmation of controller/reset state, UIC readiness, completion/result, and device presence. Its read-only transport must use verified queue mode and its own buffers. [HCE and link startup](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/core/ufshcd.c#L4757-L5014), [MediaTek link hooks](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L1864-L1933) |
| Interrupts | The core clears pending interrupt status, masks the controller interrupts and registers the shared IRQ. The MediaTek driver also parses and configures separate MCQ IRQs. The first XNU design uses bounded polling only if IRQ ownership and quiet state are proved, including MCQ sources. Validate queue mode before attempting any enable. [Common IRQ setup](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/core/ufshcd.c#L10469-L10495), [MediaTek MCQ IRQs](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L2949-L3016) |

The MiCode device-module source is pinned at
`3c4ccd07d5624879555ec710c11bb8818e5cb5c6`, and the AOSP common source at
`cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`. The latter is release-stamp
correlation to the archived Android evidence. The implementation uses
the verified Duchamp addresses and defines no new physical register
addresses. The MT6833 and MT6768 ports supplied no configuration.

## Offline implementation

The test-only model reuses `mt6897_ufs_gate_lease_check()` and
`mt6897_ufs_provider_call()`. The provider is bound to the existing gate
before stage dispatch. The independent CPU-only contract callback must
confirm the actual boot slot, cold-init permission, exclusive resources,
register access, inherited-DMA safety and read-only policy against that
lease. It runs before every attempted stage and once more before the
terminal result. The provider checks the lease at dispatch and after the
callback. A runtime provider must validate guarantees for any resources
already acquired and serialize ownership for one controller per boot.
[Gate](../duchamp/drivers/mt6897_ufs_gate.c),
[provider](../duchamp/drivers/mt6897_ufs_provider.c),
[initialization model](../duchamp/drivers/model/mt6897_ufs_init_model.c)

1. Confirm resources, then establish power, bus clocks and version-specific
   PHY/reference readiness. The initial resource stage reads model metadata.
2. Confirm inherited activity is safe before reset. Apply a host reset
   under verified ownership, then recheck PHY/reference readiness.
3. Prepare DMA using the verified direct or IOMMU route. Establish and
   verify the polling IRQ policy. Enable HCE and run UIC Link Startup.
4. Verify the read-only policy in the mock and publish readiness as a
   status. The model issues no storage command and has no block I/O API.
   A future integration must assign HCE/link startup to one owner.
   The legacy `dufs_start()` already performs HCE/link startup and must
   never be invoked as a second initializer after a successful handoff.

The stage ordering encodes dependencies for a future provider. Hardware
timing remains a separate validation item. Each stage has independent elapsed-time
and poll budgets. A stuck clock still hits the poll bound. A regressing
clock or a result returned past its deadline fails. A backend poll must
return promptly and must not repeat an already initiated side effect.
On error the instance stops, latches the result and faults the lease. If a
mutable phase could have executed, the outcome requires retaining all
acquired resources and DMA memory pending verified quiescence. There is no
automatic retry, reset or power-off. This policy protects buffers in a
future integration. The offline callbacks allocate no hardware resources.

## Verification

- The new suite ran **67/67 cases** in both native ASan/UBSan and ARM64
  QEMU with identical results. It tests successful mock direct-DMA and
  IOMMU routes, missing proof, wrong-slot and stale-lease evidence, all
  12 stage failures and poll exhaustion, and revocation before or during
  each stage and at publication. Timer regression, late completion and
  duplicate entry are also covered.
- The initialization model's production-build guard rejected compilation
  without its explicit test macro. The standalone QEMU run attached a
  separate virtual UFS controller and recorded zero MMIO and SCSI events.
- The model resides under the test-only driver subdirectory, outside the
  production XNU staging globs. The
  read-only observer and existing transport remain the separate,
  previously implemented layers.

- Fresh full-XNU QEMU regression passed **11/11 cases** using the pinned
  CI 43631086106 kernel. Cold and default-off reached read-only GPT/HFS+
  diagnostic PID 1 in 33.992 s and 33.914 s. All nine stopped cases
  recorded zero virtual UFS events. The inherited pending MCQ fixture
  reported flags `0x39`. This run booted the existing kernel.
- The saved-evidence gate and provider passed 708 and 107 checks per
  environment. Current Duchamp evidence still denies authorization
  with zero callouts. The observer passed 28 cases, the snapshot model
  30, and the synthetic handoff denied 20 cases before its one positive
  virtual read. The eight bootshim metadata cases and the auxiliary
  platform, clock/reset, DMA, cache, poll and staging tests also passed.
  The staging coverage confirms the model is excluded from production.

The verification receipt, source digests and test logs are under
`outputs/duchamp-mt6897-ufs-init-20261115` in the outer workspace.

Reproduce the new suite in a fresh output directory with Clang and
QEMU ARM64.

```sh
python3 -B tools/test-mt6897-ufs-init-model.py /path/to/new-output
```

## Remaining hardware blockers

Obtain a supported manufacturer or platform contract for the exact
Slot B boot, with non-secure HCI, UFS clock/reset/PHY and IRQ ownership,
known firmware power/PHY/ref-clock semantics and effective DMA isolation.
Before a physical reset, independently establish that inherited producers
cannot resume and that quarantined memory will remain reserved. Validate
reset assert/deassert semantics and a documented readiness indication,
including external device reset timing if needed. Verify the XNU buffer
translation and cache path before any descriptor or read. Preserve the
existing passive observer gate and the Android Slot A recovery path.

A later approved validation should begin with a correlated metadata-only
capture from the actual Slot B entry. Only after the separate rights and
lifetime checks pass can it read a bounded register sample. Physical
initialization, polling, UIC and a read-only storage trial remain
separate authorization steps. No phone operation occurred in this stage.
