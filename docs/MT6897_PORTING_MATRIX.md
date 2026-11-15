# MT6897 porting matrix

| Area | Existing implementation kept | Reference adaptation | Status / remaining dependency |
| --- | --- | --- | --- |
| Configuration | SWEET branch and source build untouched | Native HakiOS device + carried SoC schemas; no empty driver trees | TESTED_OFFLINE with original upstream checker |
| Hardware map | Existing platform/FDT parser | Pinned FDT declarations/providers/reservations generated with UNKNOWN ownership | TESTED_OFFLINE; not runtime grants |
| UFS observation | Atomic one-shot observer and XNU RO mapper | Reject community success-without-data behavior | Prior full-kernel TESTED_OFFLINE; physical access BLOCKED |
| SCSI discovery | Actual UTRD/UPIU/DMA legacy core and MCQ bridge | Add fixed non-EVPD INQUIRY with validated response and bounded retry | TESTED_OFFLINE through complete XNU in legacy and MCQ mode |
| Partition/block root | Existing GPT/HFS+ qufs read-only adapter | No fabricated xnusys geometry; no GPT edits | Prior TESTED_OFFLINE; physical root BLOCKED |
| PHY/power/clocks/reset | Existing gated MT6897 cores | Linux/Xiaomi ordering analyzed; no copied initialization | BLOCKED at real ownership/firmware contract |
| DMA/IOMMU/cache | Existing separate route/cache/lease contracts | Preserve explicit noncoherent handling and bounded lifetimes | Offline models; physical authority remains BLOCKED |
| Loader entry/payload | Existing ARM64/SWEETXNU code | Adapt script organization, not Infinix addresses or XNUP | Existing path preserved; emulator packaging only |
| One-session policy | Existing menu/reset paths preserved | Strict pmsg RAM parser and Android-default policy | TESTED_OFFLINE with actual XNU entry and modeled return; physical binding BLOCKED |
| Recovery | Existing verified backup history | No automatic flashing or slot selection copied | Phone chainboot/reset retention UNKNOWN |
| GPU/display/touch | Existing console, FocalTech probes and models | Reject G52/G57 register reuse; G615/SPI2 actual declarations only | Deferred pending storage/loader prerequisites |
| Radio/audio/power/userland | Existing tests kept | No community stub promoted to physical support | Deferred; no new GUI or radio success claim |

BLOCKED physical dependencies do not prevent the independent configuration,
protocol-policy and QEMU tests. They do prevent automatic deployment, physical
resource initialization or claiming the native port finished.
