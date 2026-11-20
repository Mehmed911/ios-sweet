# Publication and generated-output cleanup — 2026-11-20

## Publication

The existing `duchamp-bootstrap` history and current source changes were pushed
without force to `Mehmed911/ios-sweet`. The first publication commit was
`b076c35d2505e8fe3f5c224b2bd885f3288e02ca`; its remote hash was independently
checked before any deletion. This follow-up records cleanup only.

Source, patches, test programs, reports and the authored20F66 field map were
published. Device images, Apple binaries, generated native test executables and
build/output directories were excluded. A focused current-source and pending
history scan found no matches for the checked token/private-key/device-serial
patterns; this is a scoped check, not a universal secret-free guarantee.

A verified Git bundle was retained locally, SHA-256
`f68fd81bafac100919ad717995989f6ff5efaa9bf4e74aa1c4fa176e86c588f5`.
Local audit directory:
`C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/publish-cleanup-20261120`.

## Removed generated artifacts

| Location | Removed | Scope |
| --- | --- | --- |
| Windows outputs | 463 closed reproducible files,20.34GiB logical | Old `payload.bin`, `payload.rebuild.bin`, `root.hfs`, `ramdisk-final.hfs` copies; compressed storage was smaller than logical size |
| Ubuntu `/var/tmp` | 28 virtual RAM/test-root files | Nine obsolete graphics/service VM directories, plus the latest closed VM's transient RAM file |

Ubuntu removals accounted for99,653,386,240 allocated bytes (92.81GiB) and
165,356,240,896 logical bytes. This difference matters for sparse virtual RAM.
No source directories, test sources, evidence logs, firmware images or recovery
files were removed. There were no active QEMU processes at deletion time.

Every Windows target was constrained to the workspace outputs directory and
screened against protected files and current output directories. A bulk loop
was rejected by automatic review before execution; deletion was completed with
smaller batches of explicitly named native PowerShell literal paths, without
recursive deletion or `Force`. All463 final paths were checked absent.
The28 Linux targets were independently checked as regular, non-symlink files
inside the selected `/var/tmp` test directories before removal. File-level
plans/results are retained in the audit directory.

## Physical capacity recovery

Removing files from ext4 did not immediately recover C capacity. Ubuntu was
already stopped, so no user sessions were terminated. After an ext4 trim, the
documented Windows [CompactVirtualDisk API](https://learn.microsoft.com/en-us/windows/win32/api/virtdisk/nf-virtdisk-compactvirtualdisk)
was used on the detached Ubuntu VHDX under the current user's security context.
Open and compact both returned0. No disk partition or filesystem was resized.

The VHDX file changed from343,970,676,736 to254,507,220,992bytes. Immediately
after compaction C had105,907,150,848bytes free (98.63GiB). The final measurement
after verification was99,913,547,776bytes (93.05GiB); free space can change during
normal host/WSL activity. These are measured host values, not the trim command's
much larger logical-discard count.

The audit retains `compact-ubuntu.ps1`, API error codes, before/after lengths,
disk observations and all cleanup results. No sparse-mode or firmware/security
settings were changed, and no administrator privilege was bypassed.

## Retained and verified

- All25 frozen native/recovery artifacts retained their exact hashes.
- The exact current source-built XNU kernel and all1127 source-link inputs
  verified again after VHD compaction.
- The staged original-service root and original pinned fixture both matched
  their pre-cleanup SHA-256 values.
- The latest final HFS+ root remains at
  `/var/tmp/duchamp-abi-repaired-d9oo6amx/run/ramdisk-final.hfs`.
- Its source input remains `/var/tmp/duchamp-abi-dzdv45q6/root.hfs`.
- The latest original-service logs, passive traces and all reports remain in
  `outputs/duchamp-abi-repair-20261120`; the preceding accepted kernel/guest
  binaries remain in `outputs/duchamp-ioacceleratores-20261119`.
- The new offline ABI suite passed36/36 again after cleanup, exit0. No full VM
  was rerun solely to validate deletion of obsolete generated files.

Historical reports describing retention reflect their creation time. The
obsolete VM RAM/root copies listed in this audit are now intentionally absent;
do not expect an old execution directory to retain a complete memory snapshot.
Use the retained latest fixtures and source-build receipt for the next run.

Graphics status remains **BLOCKED_BY_UNKNOWN_ABI**; physical status remains
**BLOCKED_BY_MEMORY_EVIDENCE**. No phone flashing, reboot, slot change, physical
UFS access or firmware modification occurred during publication or cleanup.
