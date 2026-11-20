ACTIVE HANDOFF - published to GitHub; obsolete VM outputs cleaned and Ubuntu VHD compacted (2026-11-20)

- User explicitly authorized commit/push and cleanup, superseding the preceding no-commit/no-deletion restriction. Branch duchamp-bootstrap first pushed at b076c35d2505e8fe3f5c224b2bd885f3288e02ca; remote SHA verified before deletion. Source/history/tests/docs published without force; Apple binaries, device images and generated build assets excluded. Local verified Git bundle and audit: outputs/publish-cleanup-20261120.
- Deleted463 old Windows output copies (20.34GiB logical) and28 obsolete Ubuntu VM RAM/root files (92.81GiB allocated). All logs and source retained. Current /var/tmp/duchamp-abi-repaired-d9oo6amx/run/ramdisk-final.hfs and /var/tmp/duchamp-abi-dzdv45q6/root.hfs retained; latest guest-ram.bin intentionally removed. Older first-frame/Metal/provider test RAM/root copies are gone; historical reports do not imply they still exist.
- Ubuntu was already stopped; documented OpenVirtualDisk(METAOPS)/CompactVirtualDisk(NONE) returned0/0 without terminating sessions or resizing filesystems. VHD343,970,676,736->254,507,220,992bytes. C briefly98.63GiB free, final post-verification93.05GiB measured. All25 protected hashes, exact4ae22e3d... kernel/1127 link inputs, staged root and original fixture reverified; offline ABI36/36 pass after cleanup. No phone/slot/flash/physicalUFS/firmware operation. BLOCKED_BY_UNKNOWN_ABI and BLOCKED_BY_MEMORY_EVIDENCE unchanged.
- Read docs/DUCHAMP_PUBLICATION_CLEANUP_20261120.md for retained paths and actual cleanup scope. Continue producer-side20F66 allocation/mapping/ownership/fence ABI recovery; do not publish an accelerator stub or count diagnostic pixels as a SpringBoard frame.

ACTIVE HANDOFF - original-service regression restored; IOAcceleratorES ABI V2 still BLOCKED_BY_UNKNOWN_ABI (2026-11-20)

- Branch duchamp-bootstrap / HEAD d91562d plus preserved dirty tree; no commit/push. Before this task's NOTES update the Windows-Git binary diff exactly matched the saved baseline (SHA256 3fa0785ab5d4d5de5ae52294ceea300328fee74a9af4959ed491d3ed29c3f048). All25 frozen native/recovery hashes unchanged. No phone/ADB/Fastboot/reboot/slot/UFS/firmware operation. Physical BLOCKED_BY_MEMORY_EVIDENCE unchanged.
- Disk restored WITHOUT DELETE/relocation: lossless NTFS compression on one pilot plus483 closed reproducible output copies, every pre/post SHA identical, native/recovery excluded. Batch free19.83->38.29GiB; after new large VM retained outputs35.54GiB. Compression per-file22,742,829,848 logical bytes ->5,252,366,336 reported stored bytes. Other host allocation changes not attributed solely to compression. C only usable attached volume; VHD untouched. Records in outputs/duchamp-abi-repair-20261120/{compression-results,disk-final-assessment}.json.
- Fresh original20F66 run COMPLETE on exact source kernel4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd /1127 source inputs:22/22services,24/24IOSurface,26/26IOKit,296/296installed hashes, guest probe exits0, completionstatus0, no observedpanic,213.897s. launchdPID1; originalBackBoard25/birth90,SpringBoard34/birth119 UID501. Current native VM /var/tmp/duchamp-abi-repaired-d9oo6amx/run, allRAM/root/extraction files retained. Prior SIGBUS/cancelled runs remain failures.
- Fresh original matching IOAcceleratorES returnskr0/iterator0 thenservice0; no error-to-success conversion proven. Originalswap1 surfaces[0,0,0,0]/zero rects. No genuine SpringBoard frame. Diagnostic IOSurface task-bound method calls have expected errors; never equate them with GPU compatibility. Bounded observer evidence is not a claim about all later calls.
- New static evidence rebind15code intervals/29anchors to actual20F66 cache.600byte selector2 reply+0x18 is dlsym name input (x0=-3), resolved actual_dlsym0x1a6c2cc88; text extent UNKNOWN. Count1 usesbase directly; count>=2 consumesu32offsets+0x58/+0x5c.64byte query lives at wrapper+0x270, NOT within600reply. Type2SharedCreateDeviceShmem selector5 one scalar/16structure output,Destroy selector6 one scalar/nooutput, producer ownership/mapping/syncUNKNOWN. No successful actualGPU reply captured.
- New offline-only tools duchamp_ioaccel_abi.py, test-duchamp-ioaccel-abi.py (36/36 including1000deterministic random captures), verify-duchamp-ioaccel-static.py. No IOKit provider/noGPUcommands/no pointerdereference. Positive self-reported memory claims never establish ownership. New machine map research/graphics-abi-20F66/selector2-field-map.json is an analysis partition, NOT a Cstruct. Additional fresh native tests: discovery20,observer22,RAMbounds6,actuallognegative8. Initial logtest omitted requiredargument(exit2), preserved; corrected actual-log testpasses. Prior apps35/compositor25/windows22/mouse18/MachO17/FS11/service74 receipts preserved and hashes revalidated, not rerun for offline-only code.
- Reports docs/DUCHAMP_IOACCELERATORES_ABI_V2.md, DUCHAMP_GRAPHICS_ABI_FIELD_MAP.md, DUCHAMP_QEMU_DISK_SPACE_RECOVERY.md. Pinned MITUniXNU iOS17/customwire and AppleAPSLIOFramebuffer source reviewed only; no unrelated selectors/Adreno/Mali code copied. NEXT: recover matching20F66 producer dispatch and mappedmemory allocation/unmap/owner/fence/completion contract; no service publication until real operations established. Keep native32+4MiB candidate frozen.

ACTIVE HANDOFF - 20F66 IOAccelerator ABI prefix decoded; provider BLOCKED_BY_UNKNOWN_ABI (2026-11-20)

- Branchduchamp-bootstrap/HEADd91562d, all prior changes preserved. No phone/flash/reboot/slot/physicalUFS/firmware/commit/push. Exact source-built kernel4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd and1127 source inputs unchanged. Physical BLOCKED_BY_MEMORY_EVIDENCE unchanged. No IOAcceleratorES/Metal provider published; no authentic SpringBoard frame.
- NEW actual20F66 binary evidence: cache includesAGXMetalA11 UUIDA1D04B73-670F-33D5-BE50-89366A4BEA14. IOAccelDeviceCreateWithAPIProperty opens type1; conditional APIlabel selector7/16inputbytes, mandatory selector2/600outputbytes, mandatory selector0/64outputbytes, optional selector5/24outputbytes. IOAccelSharedCreate opens type2 and query7/16outputbytes; queue opens type4, submit selector1 framing8+24*N (count at+4). These are STATIC callsite facts, NOT live successful GPU requests. Consumer of600byte reply uses mapped base/count/offsets; producer ownership, synchronization, entry semantics and command execution still UNKNOWN. No zero-descriptor/Cstruct guess implemented.
- Original matching Apple-hosted20F66 iPhone10b kernelcache downloaded18,183,395B (f753edf0...), ZIPCRCverified; decompressed50,888,704B(e6fa7559...), xnu8796.122.4 ARM64_T8015. KEXTmetadata confirms IOGPUFamily65.40.15 and AGXG10P_B0 personality MetalPluginNameAGXMetalA11, parentAppleARMIODevice, gpu,t8015, matchcategoryIOAcceleratorES. This is NOT a QEMU/MTK provider. Pinnedipsw cannotextract nonMH_FILESET kext; target class symbols absent from5868 defined kernel symbols. Original image retained for future typed producer-ABI work, never executed/installed; CRC/SHA not signature attestation.
- UniXNUrefgit clean/pinnedAdrenoMetalcc0a4e8... andAdreno740be70fb1... MIT,12source/license receipts. iOS17 OriginalAcceleratorABI not20F66proof. Own offline wire IDs notApple ABI. HostMetal backend needs actualhostMetal; macOS IOGPUMetalDeviceShim autozero stubs explicitly NOT reused. Existing CPU compositor remains independent Mach protocol.
- Fresh completed SAMEkernel regressions:apps35,compositor25+graphics10,GUI22,mouse18(+host10),MachO17,nestedFS11/services74 allpass5commands exit0. NativeASan/UBSan14+14,discovery20,observer22,profile7,largeRAM6 pass. Existing negative ownership/rect/replay/null/dead/buffer cases retained. Only safe code change: verifier follows explicit build/config/guest-receipt paths and canonical config receipt binding;5labelled historical-log replay tests(default/explicit accepted,wrongkernel/nonpassive/missing rejected) pass. Replay is NOT new guest execution.
- Fresh original22/IOSurface24/IOKit26 run FAILEDhostSIGBUS135 before diagnostic completion. C measured0.89GiB; WSLinstance startup transientfailure. Logs/partialtrace archived. Retryreusedsameinputroot, stopped ONLYconfirmedownQEMU/debugger/runner whenfree<768MiB, alsoINCOMPLETE. Do NOT report fresh22/24/26 success. Last accepted baseline remains2026-11-19. Current-run duplicatedrebuildpayloadremoved withrecordedhash,9reproduciblepayloadcopies ZIParchived+independentlyhashverifiedbefore removal; failed virtualRAMfilesremoved afterlogs retained. fstrim reported675GiB discard but NOT actualWindowsreclaimedspace; no WSLshutdown/restart issued. C about2.16GiB free after scopedcleanup; more headroom needed before large VM. No old user/source/recovery/working files deleted.
- Newreports docs/DUCHAMP_IOACCELERATORES_ABI.md, docs/DUCHAMP_SOFTWARE_GRAPHICS_PROVIDER.md, docs/DUCHAMP_SPRINGBOARD_RENDER_PROGRESS.md. Evidence outputs/duchamp-ioacceleratores-abi-20261120, static-abi-summary.json, bounded-functions.json, resolved-static-calls.json, reference-source-receipts.json, apple-kernelcache-receipt.json, regression-commands.json, receipt-path-tests.json, host-storage-failure.json, retry-storage-cancelled.json, final-manifest.json. Next: qualify exact600byte mapped descriptor, sharedresource/24bytequeue-record ownership and completion protocol, plus real20F66 software runtime/backend; do not publish partial/fake accelerator to hide this boundary.

ACTIVE HANDOFF - IOAcceleratorES boundary confirmed; honest IOSurface errors/source kernel VERIFIED (2026-11-19)

- Outcome BLOCKED_BY_UNIMPLEMENTED_GRAPHICS_API; first authentic SpringBoard frame still false. Original BackBoardPID25/birth90 MTLRegisterDevices: dictionary IOProviderClass=IOAcceleratorES, matching kr0/iterator0/service0, before plugin/GPU userclient. This is valid empty matching, not an observed error-code conversion. Actual20F66 plugin stubs/properties resolved (MetalPluginName, MetalPluginClassName, bundleWithPath:, principalClass/classNamed:, initWithAcceleratorPort:); qualified compatible execution backend still missing. No dummy accelerator, Metal plugin, feature advertisement or fake success introduced.
- Fixed real preexisting bug: xnu/patches/0218-duchamp-iosurface-unsupported.patch makes default IOSurface external selector return kIOReturnUnsupported, replacing accept-and-ignore success. Separate source-compiled SweetSurface.cpo fully relinked with all1127 verified inputs: outputs/duchamp-ioacceleratores-20261119/kernel/kernel.development.sweet SHA2564ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd. Source/build receipts preserved; no prebuilt-kernel binary patch. Prior97adb397 kernel/receipts unchanged.
- New0BSD original-IOKit guest contract probe passed26/26/exit0 as PID38 UID501; matched real IOCoreSurfaceRoot registry4294967577 and opened actual connection0x1d0b. Implemented limits0, short buffer0xe00002db, unimplemented selector0xffffffff->0xe00002c7, null surface capability0xe00002bf, invalid mapping type0xe00002c2. Four passive kernel entry/return pairs independently confirm ownertask/results. Original IOSurface24/24/PID37 and original services22/22 pass;296 installed hashes verified. Same-process surface alias is not full sandbox/ownership qualification.
- Guarded existing compositor IOKit transport against null/dead handles, null buffers with positive counts and oversized requests before IPC/copies. New native ASan/UBSan14+14, false-success log8, discovery20, observer22, sourceprofile7, largeRAM6 pass. Wrong initial observer filename/missing profile argument exits2 retained and corrected separately; host stdio/guest fflush prototype compile conflict fixed by dropping unnecessary host stdio include. No failed test relabelled.
- Fresh exact-new-kernel regressions passed apps/multitouch35, compositor25+graphics10, GUI22, live virtualmouse18+host10, nestedFS11/services74, dynamic/staticMachO17. Default opt-in-disabled controller remains byte-identical451625b8.... Single original BackBoardSwap1 IDs[0,0,0,0], no original surface-create/present event. Diagnostic Surface2 and custom compositor frames are NOT authentic SpringBoard. Generic observer caps remain explicit limitations.
- Reports docs/DUCHAMP_IOACCELERATORES_PROVIDER.md, docs/DUCHAMP_METAL_SOFTWARE_BACKEND.md, docs/DUCHAMP_SPRINGBOARD_FRAME_STATUS.md. Evidence outputs/duchamp-ioacceleratores-20261119 with correlated-verification.json, full trace, full source link receipt, exact commands/hashes and final-manifest.json.25 frozen native/recovery files unchanged. Physical BLOCKED_BY_MEMORY_EVIDENCE unchanged; no phone/ADB/Fastboot/flash/reboot/slot/physicalUFS/firmware/commit/push. All test VMs ended. Next: qualify genuine20F66 plugin/runtime plus an actual execution backend; do not relabel IOCoreSurfaceRoot/custom CPU compositor as IOAcceleratorES.

ACTIVE HANDOFF - original 20F66 Metal discovery isolated; IOSurface24/24 VERIFIED (2026-11-19)

- Completed QEMU/offline only. No phone/ADB/Fastboot/UFS/firmware/slot/flash/reboot/commit/push. Physical BLOCKED_BY_MEMORY_EVIDENCE unchanged; exact source kernel97adb397.../1127 link inputs and25 frozen native/recovery files preserved. Baseline diff/status/NOTES/controller/observer copies in outputs/duchamp-metal-iosurface-20261119/baseline.
- Actual BackBoardPID25/birth90 first missing resource: MTLRegisterDevices calls IOMasterPort kr0, IOServiceMatching(IOAcceleratorES) nonnull, IOServiceGetMatchingServices kr0 BUT iterator0, then IOIteratorNext0. Fixed opcode-bound sites, real cached framework UUID and thread/process identity correlate sequences [526, 528, 529, 530, 531]. No provider is returned in this query; this is before plugin creation, GPU IOServiceOpen, feature validation or command submission. Those downstream contracts are NOT proven; no fake Metal/GPU class/device/reply added.
- Accepted trial4: original launchdPID1/BackBoard25/SpringBoard34,22/22 original service checks,295 installed-file hash comparisons pass. New original-public-IOSurface clientPID37/birth128/UID501 passed24/24: BGRA64x32,row256,allocation16384,Surface2,realMachport0xb03,same-process alias/shared-byte/retained-alias/release checks,invalidID/nullport/over-width rejection. Kernel traces link creator task, scalarID, returnedport and lookupSID. Diagnostic pixels are NOT SpringBoard; cross-process transfer and full leak/isolation audit remain unverified.
- Source branch uncommitted d91562d. Permanent additions: bounded cache/site preparation, passive Metal/IOKit return probes, classifier/20tests, original-IOSurface MachO client and opt-in post-health hook. Normal controller object remains byte-identical451625b8... with opt-in disabled. Idle return probes disable when unused; hot genericIOKit80/Metal40 caps explicitly recorded. Later absence at globally capped Metal sites does NOT prove no SpringBoard Metal call. CA/kernel-surface hooks remain enabled.
- First prep rejected separate .symbols synthetic mapping (explicitly excluded from runtime return allowlist); trial1 did not launch. Trial2 original-service query timed out before SB under excess observer load; preserved as failure, fixed observer overhead without changing timeout/assertions. Trial3 original22 passed but IOSurface23/24 failed an unsupported zero-width rejection assumption. Source permits zero-width+explicitallocation; trial4 records that as an observation and tests actual maxdim16384 instead. No kernel gate or failed result was relabelled successful.
- Fresh regressions allpass: apps35+host14,compositor25+graphics10,GUI22,mouse18+host10,FS11,services74,MachO17. Final targeted20 discovery/bounds,22 observer,7 source gates,6 largeRAM pass. Original SB surface creations0 and context commits0; BackBoardSwap1 surfaces[0,0,0,0]. No authentic frame or screenshot, graphics stays BLOCKED_BY_GRAPHICS_DEPENDENCY.
- UniXNU requested aliases resolved to AdrenoMetal cc0a4e8e57d20f4a4698753c2530875f2b10c0ca and Adreno740 be70fb13ed19d5fdf139d27977da6f54078cf50a (both MIT).17 audited source/license receipts pinned. No Adreno registers/firmware/shaders/memory or sandbox alternatives copied to Mali. Current offline broker requires native4KiB context and host-Metal server needs real host Metal; neither is a drop-in for this16KiB/Linux guest.
- Reports: docs/DUCHAMP_METAL_DISCOVERY.md,docs/DUCHAMP_IOSURFACE_COMPATIBILITY.md,docs/DUCHAMP_SPRINGBOARD_RENDER_BLOCKER.md. Fullreceipts/traces/commands/failedattempts/console-only rawfb under outputs/duchamp-metal-iosurface-20261119. NEXT: qualify cross-process IOSurface rights/crash cleanup and a real20F66 renderer/provider/shader/queue contract; independently resolve SB startup waits before publishing any accelerator. Do not fake publication, force PC/registers or attribute diagnostic surfaces to SB.

ACTIVE HANDOFF - original 20F66 first-frame trace BLOCKED_BY_GRAPHICS_DEPENDENCY (2026-11-19)

- Completed QEMU/offline only. No phone/ADB/Fastboot, physical UFS, firmware, slots, flash, reboot, commit or push. Physical BLOCKED_BY_MEMORY_EVIDENCE unchanged. All25 frozen native/recovery files and source kernel97adb397.../1127 link objects unchanged; baseline diff/status/NOTES preserved in outputs/duchamp-springboard-first-frame-20261119/baseline.
- Fixed passive hardware-breakpoint observer derives10 layouts from actual linked DWARF; binds8 kernel sites/15 original cache sites, actual task/PID/birth, executable/cache UUIDs and source receipt. No guest register/memory rewrite, forced software renderer or custom GUI substitution. Added QEMU source-profile hook, conservative pixel prerequisites and negative tests; no kernel or Apple binary changes.
- Accepted trial4: original BackBoardPID25/birth90 and SpringBoardPID34/birth119, original launchdPID1,22/22 native-job checks and294 installed-file hashes pass. 3 BackBoard CA context commits; ZERO observed SpringBoard context commits. Direct MTLCreateSystemDefaultDevice-return site captured40 samples, allnil. Actual bounded QuartzCore/stub decode establishes the function; legacy metal_device_result label is wrapper RET, not direct device result.
- Swap1 contains[0,0,0,0], zero rects, mask0x80000007, method return0. Empty presentation completions=0; no original content surface or attributed frame. Raw final framebuffer13,538,304B SHAc77db9d4f048dd7f7578d517affbd7a31e31233ebe768ecdabfbeb42c8599809, retained as diagnostic console only; NO authentic screenshot. Missing bootstrap services and incomplete SpringBoard init remain additional unresolved dependencies, not assumed solved by Metal alone.
- Observer/DWARF/pixel prerequisite22, source-profile denials7, largeRAMlayout6 pass. Fresh exact-kernel regressions: apps35+host14, compositor25+graphics10, GUI22, mouse18+host10, FS11+services74, real MachO17; command/exit/log hashes saved. Trials1/2 observer page-residency failures retained; trial3 partialtrace retained. Trial4 corrects kernel-thread/no-BSD-process observation without fabricating userspace ownership. Optional ipsw ObjC disassembler allocation failure replaced by bounded LLVM decode.
- Reports docs/DUCHAMP_SPRINGBOARD_FIRST_FRAME.md and docs/DUCHAMP_IOS_GRAPHICS_RENDER_PATH.md. Receipts/raw traces/filtered events/console-onlyfb/manifest in outputs/duchamp-springboard-first-frame-20261119. NEXT: establish a real renderer/provider contract or verified original CPU-renderer configuration, independently resolve SpringBoard startup waits, then require a nonzero original surface + matching presentation/framebuffer chain. Do not force PC/registers, fake Metal success or treat custom shell/empty swap as SpringBoard proof.

ACTIVE HANDOFF - intact 20F66 cache and original graphical-service STARTUP VERIFIED (2026-11-19)

- Completed QEMU/offline only; no phone/ADB/Fastboot, physical UFS, firmware, slots, flash, reboot, commit or push. BLOCKED_BY_MEMORY_EVIDENCE remains unchanged. All25 frozen native/recovery-file hashes and exact source kernel97adb397.../1127 link objects revalidated. Baseline patch/status/NOTES preserved outside source at outputs/duchamp-ios20f66-integration-20261118/baseline.
- Rehashed all43 intact runtime cache components,2722512896B;2710 actual MachO records; UUID E5420DB3-30D0-33AA-8B7E-05B5038BB46D. StudyLog and SpringBoard.framework exist. Recursive strong closures267/1005 nodes,2381/16150 edges (including standalone dyld)(including weak),no missingstrongpaths; allplainARM64/iOSmin<=16.5. Metadata is not full ABI proof; signatures/provenance limits recorded.
- runtime-1 direct admission12/12 diagnostic checks passed with realcachebase0x19ccdc000,bytes2850996224,original launchdPID1,parentprobePID3; originalbackboarddPID8/SpringBoardPID9 acceptedexec thenSIGTRAP5,notnormalexit0,no timeout. Those failed startup observations remain historical, not relabelled working.
- native-jobs-1 original provider/resource/jobs fixture PASSED18/18 general+4/4UIcriteria on exact source kernel97adb397...,no instruction/debugger patch. Original mobile backboarddPID25 and SpringBoardPID34 PPID1/UID501, six5shealthchecks each; logdPID7/rootMCM5/installd13/lsd17/runningboard22. FirstlogdPID3SIGTRAP preserved. Original BKS native display handler replied twice kr0,1125x2436; LS native rebuild/installedSpringBoardrecord verified. FullGUI/rendering remainsFALSE/unverified; launchdinitialized=1 and activeendpoint flags are not completeUIinitialization. Multipleprovider/context changes mean directSIGTRAPcause not uniquely isolated.
- Isolated3GiB writable HFSmd0 QEMU-only profile; hostRAMsparse10GiB,guestwindow4GiB. No blockdevice. Existing smallread-onlymd0+writablemd1 and frozenphone32+4MiB layout unchanged. 294additionalnative-job files roundtripped/hashverified. Native root SHA f369d7a1d9c4df9df5efe70ce13251e02a342c3e8fecb230ea7f21f06997d265. Native root filesystemheader free343928832B; oldHFSCLI signedused-byte print wrapsabove2GiB,notcapacitycorruption.
- New strict cacheclosuretool/tests13,source-profile denial4,large-layout6,job-verdict4,preflight21,heartbeat9,waitstatus7,dualpackaging12passed. Firstpackaginginvocation omittedrequiredpayload(exit2);correctedloggedinvocationpassed. Fresh regressions applications35+realdevicehost14,compositor25,graphics10,GUI22,mouse18+host10,FS11,services74,MachO17 allpassed. No archivedCIkernelresults counted; overlappingnestedchecks notsummed.
- Docs: DUCHAMP_IOS_20F66_SHARED_CACHE.md,DUCHAMP_BACKBOARDD_RUNTIME_STATUS.md,DUCHAMP_SPRINGBOARD_RUNTIME_STATUS.md. Evidence outputs/duchamp-ios20f66-integration-20261118 includes finalmanifest, rawcache/macho metadata, signatures/entitlements, closures, directexec logs, native-primary compact logs, native-jobs-1 private images, all regressioncommands/logs.
- Next: attribute originalSpringBoard/QuartzCore IOSurface->SwapEnd->framebufferpixels. ActualBKS1125x2436 differsQEMU1220x2712;renderingimpactunknown. 44observedmissingruntimeendpoints(mobilegestalt/iconservices/etc)mayincludeoptionalservices;no uniquefirst-framecauseproven. Childper-imageDYLDprinttraceswereunavailable;parentlivecacheandstaticmappingtablesareexplicitlyseparate. CurrentcustomVirtIOshellinputdoesnotproveBackBoardHID. No SpringBoardUI/Setup/Metal/Mali/physicalcompatibility claim.

ACTIVE WORK - iOS20F66 intact-cache integration (2026-11-18)

- Baseline preserved outside source at outputs/duchamp-ios20f66-integration-20261118/baseline. No phone/physical UFS/commit/push operations. Exact source kernel97adb397... unchanged. Native32+4MiB candidate/recovery unchanged.
- All43 runtime cache component hashes verified,2710 Mach-O records inspected. Required strong closures contain266 nodes/2380 edges(backboardd),1004/16149(SpringBoard), all plainARM64/iOS minimum<=16.5 and all strong paths present. Metadata availability is not runtime ABI success. Separate3GiB writable QEMU-only RAM-root fixture under preparation; small read-only dual profile unchanged.

ACTIVE HANDOFF - iOS graphical userland compatibility AUDITED; actual loader blockers verified (2026-11-18)

- Scope was QEMU/offline only. No phone/ADB/Fastboot, reboot, flash, slot change, physical UFS, firmware operation, commit or push. Physical BLOCKED_BY_MEMORY_EVIDENCE is unchanged. All prior uncommitted work and the frozen native candidate/recovery files are preserved. Baseline diff/status/source copies: outputs/duchamp-ios-graphics-audit-20261118/baseline.
- Exact kernel remains 97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001 (19543912B,1127 source-link inputs). All10 inspected XNU source hashes match their actual link-input source receipts: kernel-interface-sources.json. No kernel, compositor, WM, GUI, input or application-manager implementation changed.
- Actual original20F66 admission-2 diagnostic PASSED15/15: probePID4/PPID1,37dyldimages,cache_present=0; matched existing five surface/display/test-HID providers, not queried IOHIDSystem/IOAccelerator. Surface-limit ABI1,rowmask63,display1220x2712. Original backboarddPID9 and SpringBoardPID10 were accepted by exec with UID/GID501 requested via successful setgid/setuid, then original dyld reported missing StudyLog.framework and SpringBoard.framework respectively; both SIGABRT6, no timeout, no normal exit status, neither service initialized. UUIDs match original files. Native program independently recompiled/relinked byte-identically (native-reproduction/verification.json). No Apple binary patched/re-signed.
- backboardd1182960B SHA686f26a6a7b749fd0ae30acca704022da8cb6f85b5c39a0e0e09e25ffd00d273:45strong+1weakdirectimports,42missingstrongguestpaths. SpringBoard112048B SHA7926a1ba0b115cf45102b2c3d8e4eb7bc9c84bcf70b573d2a798690d9148059c:4strongimports,SpringBoard.framework/Foundationmissing. Host2710-image20F66cacheinventory does not satisfy guest dependencies or prove cache mapping. Original jobs declare18/33Machservices, mobile credentials and policy; no fake endpoints registered. Direct exec admission is not full original-job bootstrap.
- Linked SweetSurface CPU allocation/lookup/ports coexist with no-op values/notifications/accelerators/shared events/use-count paths. SweetFramebuffer implements CPU scanout/selectedmethods, not full graphics ABI. Current VirtIO multitouch feeds custom DT/GW shell/WM; original BackBoard digitizer delivery is missing for this profile. Historical large-root UI observations use different kernel/runtime conditions and are not current-kernel proof.
- Implemented0BSD strict Mach-O preflight/closure tool (duchamp_macho_preflight.py), read-only HFS guest dependency/job audit (audit-duchamp-ios-graphics.py), native capability/direct-exec probe and runner. No production GUI replacement or private API fabrication. New tests:MachO21/21,heartbeat9/9,terminalwait7/7; final-targeted commands/logs recorded. Cache-only files and unknown required commands fail closed; unresolved runpaths remain unknown; weak imports do not masquerade as required dependencies.
- Fresh regressions PASSED: applications35/35 +actualtouch14/14,compositor25/25,graphics10/10,GUI22/22,mouse18/18,MachO17/17,FS11/11,services74/74. Normalbrowser18/18 and nativepostflight15/15 passed. Kernel and native candidate unchanged. Outputs: regression-applications-2, regression-compositor, regression-gui, regression-mouse, regression-macho-2, browser-regression.
- Failure history preserved: admission-1 expired180s without nativeprobe trace (UNKNOWN); longer-budget admission-2 produced real loader evidence. Firstappregression had18healthyheartbeats but oldvalidator demanded exactly2; criterion now requires first1/2 plus all extra samples contiguous/healthy and rejects gaps/replay/wrongPID/unhealthy. Freshapp-2passed. Initialmacho wrapper substituted wrongargument and failedexistingmkdir; correctedmacho-2passed. Rawwait high-byte exit=0 duringSIGABRT is not normalexit0: originalrawreport retained, verification-normalized.json records exit_status=null.
- Docs completed: DUCHAMP_IOS_GRAPHICS_COMPATIBILITY.md, DUCHAMP_BACKBOARDD_DEPENDENCIES.md, DUCHAMP_SPRINGBOARD_DEPENDENCIES.md. Final audit manifest/postflight verifies receipts, new sources, original files and frozen25filehashes. No claim of authentic graphical-service startup.
- Next justified implementation is a separate large QEMU runtime fixture with intact matching cache/resources and fresh cache mapping/UUID/slide evidence, then original mobile/session job policy and actual BackBoard/QuartzCore/HID responses. Do not modify frozen32+4MiB native image or infer physical safety.

ACTIVE HANDOFF - Darwin application lifecycle + real VirtIO multitouch VERIFIED (2026-11-18)

- Scope QEMU/offline only. No phone commands, flash/reboot/slots/UFS/firmware/commit/push. BLOCKED_BY_MEMORY_EVIDENCE unchanged. Original native candidate/recovery files preserved. Baseline diff/status/source copies at outputs/duchamp-app-multitouch-20261118/baseline.
- Source-linked kernel-2 SHA256 97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001,19543912B,1127 verified source inputs. Native final attempt-7 PASSED35/35, host14/14,twelve full framebuffer byte comparisons. QMP actual2-contact drag+resize, native input-service restart cancellation, stale PID/birth denials, actual launchd child exit0 and abort6, focus restore/restart tested. GUI-final22/22, mouse-final18/18, browser-mouse16/16, compositor25/25, graphics10/10, FS11/11, services74/74, MachO17/17 passed on exact new kernel.
- Final normal browser-5 PASSED18/18 with native-postflight15/15, no test observer. Actual guest redPID32/birth76; bluePID34/81,37/88,40/95 acrossclose/relaunch/restart; allPPID1. Twelve browser crops byte-exact. Rootbyte-identical,varwritable,EROFS/ENOSPCverified. Finalmanifest records commands/logs/hashes; do notsum overlappingchecks.
- Separate applications service fixed catalog2 ARM64MachO paths, auditedMachRPC, PID+birthownership. Asyncfork/exec launchctl acknowledgesPENDING/STOPPING;READYonlyafterrealWMowner. Fixes prior4secondtimeoutwhilelaunchdthrottled; inputno longerwaitsforspawn. BackgroundkeepsPID,hideswindow,cancelscaptures,restoresfocus. ExitdeadnamesremoveWindowsanddetachcontacts;staleupneverretargetsrestart.
- Real QEMU10.2.1 multitouch device0xa003c00, tablet0xa003e00;slots/IDs0..10 inclusive,208Broot-onlyexclusivereadABI. ActualQMP/browser->device->XNU->nativeMachinput->WM/compositor. Rawend/cancelindistinguishable; genuinecancelverifiedthroughinputservicedeath. Bus hot-unplugunsupported. No physicaltouch/BackBoard/SpringBoardclaim;end-to-end2contacts,not11.
- QEMU dropsreportsonqueueshortagewithoutSYN_DROPPED. FinalhostguardusesobservedQOMx-query-virtio-queue-status, validates64queueandRAMavailaddress, waitsboundedactualcapacity andcountsrawSLOT+TRACKING+XY+SYN(two downs9descriptors). Nopartialsend;failedcancelneverclaimsreleasedandblocksreconnect. Host15/15+old9/9,touchprofile11/11,pointerprofile10/10,observer13/13,defaultpackaging12/12passed; nativeASan/UBSan71touch,42capture,old53window,33pointer.
- Failurehistorypreserved:attempt1preflight8-frame/defaultprofile;2observercontacttiming;3transientcapture;browser2syncspawnnativepostflight;attempt6/browser4write-onlyqueueaddressregisterread. Corrected queueguardviaactualsupportedQMPintrospection,notguessedMMIOaddresses. Incorrectpackagingpath/profilecommandfailuresretainedseparately;finaldefaultpayloadnegative12passed. No failedrunrelabeled.
- Docs completed: docs/DUCHAMP_DARWIN_APP_LIFECYCLE.md and docs/DUCHAMP_QEMU_MULTITOUCH.md. Normal launcher tools/run-duchamp-live-input.py --applications --artifacts outputs/.../attempt-7 --kernel-manifest outputs/.../kernel-2/build-manifest.json --mkfs preservedformatter;prints localURL. Tests use WSLChromiumautomation,not humanphysicalinput. Final postflight PASSED: source-linked kernel and all1127 object hashes, current driver/header sources,25 frozen native/recovery/candidate hashes, previousmousekernel, actualqueuebudgets, strictpayload/UFSdenial, rootunchanged/writablevar, Python syntax and scoped whitespace checks. outputs/duchamp-app-multitouch-20261118/final-manifest.json records exact receipts/source/artifact hashes. All test QEMU/browser processes ended. No commits.

ACTIVE HANDOFF - QEMU LIVE MOUSE VERIFIED through actual VirtIO/XNU and normal browser GUI (2026-11-18)

- Current scope QEMU/offline only. No phone operations, no commit/push. Physical status stays BLOCKED_BY_MEMORY_EVIDENCE. Previous native candidate, source-built baseline, recovery images and all uncommitted work preserved; evidence snapshot outputs/duchamp-live-input-20261118/baseline.
- New real virtio-tablet-device transport, fixed observed QEMU MMIO0xa003e00, modern queue64. Source XNU cdev /dev/duchamp-pointer0600 read-only opens exclusive; input process sends audited Mach reports to existing live shell/WM. Polling5ms, QEMU coherent memory only. No physical MT6897 DMA/cache claim. Native driver service reset/reopen generation2 tested; VirtIO-MMIO bus itself rejects hot-unplug, documented limitation.
- New kernel compiled/relinked from verified source objects (1127 inputs), no prebuilt binary patch. outputs/duchamp-live-input-20261118/kernel-2/kernel.development.sweet SHA256 cf0b0f80e83580bfe0b00529f148b8ad5705ea565ee3c1e683494948d9752e0d. Original kernel e7b51ecb... unchanged. Build recipe tools/build-duchamp-qemu-pointer-kernel.py and manifest preserve exact commands/hashes.
- Accepted attempt-1:18/18 real virtual-device input checks,7/7 full framebuffer crops,11/11 filesystems,74/74 services. Native ASan/UBSan pointer33 and window53 assertions. New-kernel GUI regression22/22, original compositor25/25, graphics10/10, native compositor48, services74, filesystems11 and Mach-O17/17 passed. Targeted host9/profile10/observer12/package12 pass; initial packaging command had nonexistent path and was corrected with separate receipt, not relabelled success.
- Normal interactive launcher tools/run-duchamp-live-input.py uses six launchd jobs, no observer/self-test. Localhost viewer maps RAM read-only; browser pointer -> QMP -> VirtIO -> XNU -> input Mach service -> shell -> WM. Browser automated via isolated Linux Chromium/Playwright; Windows UI tool unavailable (kernel assets path error), no human mouse claim. Browser tests1 lost early clicks,2/3 timed out30s before ~56s guest readiness. Fixed readiness handshake/retry and explicit120s startup timeout; fixed motion coalescing to preserve button-edge positions. Browser-test-4 PASSED16/16 with10 exact pixel crops and28 browser-origin pointer events; actual browser launch/focus/drag/resize/outside-release/reconnect verified. Normal240-second session exited0/no panic observed. Deliberate network backpressure tests initial press coordinate retention. No GW pointer synthetic injection in browser run.
- COMPLETED docs/DUCHAMP_QEMU_LIVE_INPUT.md and outputs/duchamp-live-input-20261118/final-manifest.json. Offline postflight27/27 checks passed,1127 object hashes verified,25 frozen-file hashes unchanged. Normal md0 byte-identical, md1 changed, EROFS/ENOSPC/devfs witness verified. Native/browser logs extracted in extracted-input and normal-session-evidence. Normal launcher tools/run-duchamp-live-input.py uses --artifacts accepted attempt-1 and --kernel-manifest kernel-2/build-manifest.json, prints local URL. Tests ended; no VM/browser session left running. Windows UI helper unavailable; browser automation used isolated WSL Chromium159.0.8154.6, not human input. No true device hotplug claim. No commit/push or phone operation.
- test-duchamp-readonly-var.py now reports actual transformed pointer payload hash/size/ADT plus base payload hash separately; metadata-preflight confirmed exact bytes. Existing receipt preserved, actual-run-payloads.json identifies real attempt-1 guest/payload.bin57298732B SHA25631fcf39de95c82892e6fdcaadb34303dca57b60aad3362e927e72245db9a9fdc. Repack same seeds remains byte-identical; independent HFS generation timestamps may differ.

ACTIVE HANDOFF - Darwin GUI shell/window manager verified in QEMU; no phone operation (2026-11-18)

- Current request supersedes the earlier phone/root work: QEMU/offline only. No ADB/Fastboot access, reboot, flash, slot change, physical UFS, firmware modification, commit or push in this GUI task. Physical readiness remains BLOCKED_BY_MEMORY_EVIDENCE. Preserve all prior uncommitted work and native candidate.
- Baseline branch duchamp-bootstrap, HEAD d91562d9c2bd3bc33d52550c101de1009bb41dc0. Before edits saved tracked diff/status and relevant source copies/hashes outside repo at outputs/duchamp-darwin-gui-20261118/baseline. Final docs: docs/DUCHAMP_DARWIN_GUI_SHELL.md. All changes remain uncommitted.
- New 0BSD tools/duchamp-window-core.[ch], duchamp-gui-wire.h, duchamp-darwin-gui.c, duchamp-gui-control.h, test-duchamp-window-core.c, duchamp_gui_expectations.py, test-duchamp-darwin-gui.py. Existing compositor engine extended compatibly with optional160x96 canvas, capacity-aware viewport move/resize and owner-checked single-layer removal. GUI service reuses DC registration/dirty/Z wire plus VIEW. Original64x32 service remains tested.
- Accepted source-built-XNU QEMU run outputs/duchamp-darwin-gui-20261118/attempt-4 passed22/22 GUI checks,7/7 full160x96 RAM framebuffer byte comparisons,11/11 md0RO/md1writable tests,74/74 original launchd/syslogd/notifyd checks. GUI compositorPID18, WM20->31 after real launchctl restart, shell24, red26, blue28, all PPID1. Red received8 genuinely delivered sequenced Mach input events, including down/up, drag and resize. Actual client termination/dead-name cleanup and persistent app reconnect verified. Native ASan/UBSan53 new assertions passed.
- Legacy regression rerun outputs/duchamp-darwin-gui-20261118/legacy-regression-2 passed25/25 compositor,10/10 graphics,48 native assertions,11/11 filesystem,74/74 service. Original compositor self-test now holds restored phase8sec before input; initial rerun missed that transient phase. Ordinary daemon behavior unchanged. Separate macho-regression passed17/17 dynamicPID2/exit0,staticPID3/exit42. Memory16+19,observer12,packaging12,accepted-payload profile7 passed.25/25 preserved local native/bootshim/FDT/recovery-file hashes unchanged, not new physical evidence.
- Exact kernel unchanged SHA256 e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457. GUI Mach-O87152B SHA256 e0bbf130cd42a76f6137d7ad73be20ec69b621b8e57e2aa347d823f86f0675e3; independent recompile/relink bit-identical. build-manifest.json records all source/output hashes, compiler/linker21.1.8/QEMU10.2.1 and commands. GUI payload57296096B SHA2564880d43a759106c33aa5edf0c949ae0926472749fa7a60dfd2f56ba4ece0dee0, QEMU-only, never a phone replacement.
- Actual screenshot attempt-4/guest/run/sequence-resize.png; sequence-*.raw and frame-sequence.json are independent observed pixels. Attempt1 window processes worked but console overpaint prevented frame capture; periodic re-presentation fixed it. Attempts2/3 captured7 frames but running verifier lacked opt-in GUI command list, so not accepted. --gui verifier fixed exact expected sequence; final4 all passed, no assertions/pixels relaxed. Initial packaging command missing payload exited2; corrected run passed12.
- Scope: primitive Darwin test shell with two app windows/status/launcher/pointer feedback. Virtual pointer currently originates in explicit shell --selftest over audited Mach IPC, NOT host mouse/IOHID touch/BackBoard. Ordinary shell shows desktop; external pointer adapter + normal interactive launcher loop are NEXT work. No SpringBoard/iOS/Mali/physical-input compatibility claim. Explicit GW_DESTROY RPC exists but QEMU exercised process-death cleanup; destroy core tested natively. No physical evidence gate changed.

ACTIVE HANDOFF - Magisk31.1 ROOT VERIFIED on Slot A; only init_boot_a changed; B unchanged (2026-11-18)

- COMPLETED: actual Android sys.boot_completed1 on _a after flash, magisk31.1:MAGISK:R, successful su -c id -> uid0/root contextmagisk and exit0, SELinux stillEnforcing, identical kernel release. Official manager Superuser UI explicitly granted only Shell/com.android.shell; no policy-database manipulation. Root readback of14 A/B boot-image partitions proves ONLY init_boot_a changed to expected7666d290...; all13 other hashes (including B's7) unchanged. No data wipe, super/vbmeta/kernel/recovery/firmware image writes. verification.json, root-runtime-proof.log, boot-image-comparison.json and ROOT-REPORT.md in current run record actual results. Phone left running Android with Magisk home page, no further reboot needed.

- User explicitly requested kernel audit and suitable root installation on Slot A without data wipe or Slot B changes. Actual Android ADB now works: sys.boot_completed1, slot _a, MT6897/duchamp SKU, ARM64, Android16/SDK36, RMX5030_16.0.5.700(EX01), kernel6.1.138-android14-11-g23d7c6efa1683-ab10003285-4k, SELinux Enforcing. CONFIG_MODULES/KALLSYMS/KALLSYMS_ALL/CFI_CLANG enabled. KernelSU LKM/APatch prerequisites partially present but their exact compatibility not established; selected Magisk to patch the separate init ramdisk while preserving the tested kernel/recovery.
- Run outputs/duchamp-magisk-a-20261118-072626. Official stable Magisk v31.1 APK downloaded from topjohnwu release; SHA25689cefac0a318afa39fb3880c45c87b036c05bc1ebf02a7a715b7f8d7c26ac6e7 matches GitHub asset digest. Manager installed, patched original image on THIS phone using actual app GUI. Original init_boot_a8MiB SHA25613ee7f0438bf7d917e0a06116a6805e7eaaf90ab0faa4594a1f760b589471650; patched8MiB SHA2567666d29066728411459c5dd5cafcaf7c6a83071ae5ae8942642b15ec6c96b60b. Both v4, kernel_size0; headers unchanged except ramdisk size, CPIO test original0/patched1; config preserves verity/encryption, recovery/vendorboot false, sourceSHA1 matches. Patch log, images and validation JSON saved.
- Rebooted to known OrangeFox on A and verified actual original init_boot_a hash against patch source; captured14 A/B boot-image hashes, no full backup. Fastboot ACTUAL productduchamp/current-slota/unlockedyes confirmed (Android ro.boot.flash.locked1 was inconsistent with actual unlocked state). Fastboot partition-size bare hex800000 =8MiB. Flashed exactly init_boot_a once: Sending/Writing OKAY, exit0; A unbootable=no; rebootOKAY. No B/super/vbmeta/kernel/recovery/firmware image writes or data format in this root task.
- Root boot monitor45356 completed successfully. Magisk31.1 removed reactive prompts; Shell grant was configured through the official Superuser UI and then su succeeded. Never select inactive-slot install for this A-only task. USB stay-awake restored to original0, verified in temporary-settings-restored.json; manager notifications allowed. Android UI helper uses observed uiautomator bounds. Final manager screenshot saved; Zygisk/modules not enabled. No commit/push.

ACTIVE HANDOFF - RealmeUI reached Android Setup on Slot A, confirmed by user; phone left running (2026-11-18)

- Actual installation reached all ten super pieces, but V1 postflight correctly aborted on an apparent super readback mismatch. Root cause VERIFIED on actual OrangeFox shell: arithmetic 9126805504/4096 returns131072 (32-bit overflow), reading only512MiB instead of2,228,224 blocks/8.5GiB. Original mock used 64-bit dash and missed this host-shell difference. Do NOT treat V1's previous 13/13 local results as proving this recovery-shell behavior correct. OrangeFox CLI returned0 even though native installer aborted with1; actual recovery log was checked rather than trusting frontend exit0.
- Independent physical head -c9126805504 super hash EXACTLY matches original expected 888e22c039ee36fc0f9ec07e0bacc52b99559e786a04d2d503ce70604522675c. No expected hash was changed. Corrected postflight uses awk division, executed through a real pipe for its UI FD, verified ALL8 written ranges, exited0 and successfully activated A. B's seven boot-image hashes unchanged (normalized SHA records, not CRLF-vs-LF string comparison). install-verification.json and corrected-postflight.log record this; V1 native run itself still historically aborted1, not silently recast as success.
- Already-authorized system reboot through twrp reboot reached Android Setup: user explicitly answered 'ظهرت شاشة الإعداد'. This is user-observed UI evidence; ADB sys.boot_completed was NOT measured because Android ADB remained unavailable. boot-outcome.json records ANDROID_SETUP_REACHED_USER_CONFIRMED, and install-verification.json specifies this evidence source. Host-only monitor46586 was terminated intentionally after confirmation (143); phone left running Setup, no additional reboot, flash or format. Do not interrupt Setup merely to obtain ADB logs.
- Permanent builder postflight fixed. Desktop V2 ZIP 7,387,905,597 bytes SHA256 765385c3099866b4bcd846271df4073a1563245440322821332b0b069412c3f6 changes only postflight, its manifest hash and README; firmware payloads identical to physically verified images. v2-package.json records exact scope. V2 archive-manifest check PASSED22/22 SHA256/size checks; all25 archive entries CRC-checked, exit0, v2-verification.json. The entire V2 installer has NOT been re-flashed/re-executed; corrected postflight ran on phone and passed. V1 remains historical with a Desktop warning README; use V2 for future installs. No commit/push.

- User now requested installing the repaired ZIP through OrangeFox on Slot A, reviewing installation logs and then attempting Android boot. This authorizes the previously disclosed A boot-image families + shared super and A boot-control activation, not a data wipe, firmware/bootloader rewrite or B boot-image write. Do not ask for the same flash permission again.
- Pre-install observations: duchamp, OrangeFox R12.0 on _a, unlocked, snapshot merge none, host/staged V1 SHA256 820bbdd138b1fbb30edb87aea348ffc462a18724b46e13c5ccb9475e34cb0e3a. Working bootctl HAL. /data was mounted/decrypted with ~479GiB free; staged ZIP in a new /data/rom-repair-install-20261117-225337 directory, no existing file overwrite or data wipe. Backup was stopped at the user's explicit request as recorded below.
- Current run: outputs/duchamp-repaired-install-20261117-225337. User said no backup needed. Stopped ONLY in-progress read-only super cat PID5989; kept eight completed A/misc snapshots. Incomplete super and invalid first dd image (82 appended statistics bytes, rejected before writes) were explicitly marked non-restorable, then ONLY those two generated invalid/incomplete files deleted in final cleanup. invalid-temporary-copy-cleanup.json records sizes; valid snapshots, original ROM and user backups remain. No complete super rollback image exists from this run.
- Supported twrp install invoked ONCE by perform_install.py; session52299 ended after the correctly detected V1 verification failure above. install-intent.json prevents automatic retry. No reflash was needed: corrected-postflight.log plus independent-super-readback.json verify the actual written images, and install-verification.json records successful corrected verification/A activation. Full original recovery log and installation-delta.log preserve the initial native error. Do not format data or flash B. No commit/push.

ACTIVE HANDOFF - RealmeUI local installer repair VERIFIED; final ZIP on Desktop; NOT flashed (2026-11-18)

- User asked to repair the ROM. Original Desktop ZIP remains unchanged, SHA256 e0c9c1cc0b1ec02a5c9ee28c03051fb3945aafe1f067f2eace1b25cf97d106eb. Repair work, exact source receipts and scripts are in outputs/duchamp-realmeui-repair-20261118. Final C:/Users/Mehmedamir/Desktop/RealmeUI_7.0_DUCHAMP_REPAIRED_A_ONLY.zip is 7,387,905,486 bytes, SHA256 820bbdd138b1fbb30edb87aea348ffc462a18724b46e13c5ccb9475e34cb0e3a; adjacent SHA256 and Arabic README saved. This is a locally repaired recovery installer, not verified Android boot. No flash without a separate reviewed decision.
- Fixed missing archive paths and unchecked native installer returns. Added matching OS3.0.5.0.WNLCNXM stock primary vbmeta plus vendor_boot assembled from that exact platform/DTB, port vendor fstab and unchanged verified OrangeFox recovery CPIO. Gzip support confirmed read-only in running matching recovery kernel. Stock primary vbmeta flags remain0; custom vendor_boot leaf uses algorithm NONE, not an OEM signature. Full modified AVB-chain/physical bootloader acceptance remains unverified.
- Candidate writes only A boot-image families plus SHARED super, so it is NOT a dual-OS installer. No preloader/LK/TEE/modem/B boot-image/FRP/userdata/metadata-partition writes, wipe or automatic reboot; bootctl does update active-slot control metadata after readback. Payload SHA256 preflight precedes writes; native writes asserted; full target readback hashes precede bootctl activation. Required installed firmware prefixes match read-only phone capture. Actual results: 13/13 installer cases, including FULL 7.39GB candidate (exit0, 666.874s, all eight target hashes matched); 28/28 independent package checks; product/system/vendor EROFS decode validations exit0 each. Full installer is actual ARM64 updater/OrangeFox ziptool in user-mode QEMU on generated loop blocks, mocked getprop/bootctl and buffered actual-byte prefix reader, NOT full Android emulation or physical boot.
- Current phone is still OrangeFox recovery on A, unlocked; only read-only ADB configuration/tool queries in this repair turn. Existing Android bootability is NOT established, neither slot is a verified Android fallback. Reports: verification.json, REPAIR-REPORT.md, installer-tests/results.json, test-environment.json and full_candidate UI/native logs in repair output folder. All owned test loop devices detached and independently checked absent. Removed only 12 generated test/extracted-image files (15.29 GiB logical); C now ~130GiB free. Original ROM, source inputs, candidate, logs, user backups and all preexisting XNU work preserved. No commit/push.

ACTIVE HANDOFF - Actual latest OrangeFox installer log captured: false success, missing ZIP payload (2026-11-18)

- User requested current flashing log. ADB recovery transport20, fox_duchamp on A. Captured /tmp/recovery.log after user installed /usb_otg/RealmeUI_7.0_DUCHAMP.zip. Actual installer printed ColorOS16 /16.0.5.700 /Davv98 and20 missing-file errors covering15 unique paths: fw/preloader_duchamp.bin, fw/vbmeta.img, images/boot.img, images/init_boot.img, images/vendor_boot.img and ten images/super.img.* entries. This directly confirms the earlier static preflight defects.
- Installer nevertheless printed script succeeded/result0, process ended with no errors, installer code0, flash_done, and took5 seconds. This is a FALSE SUCCESS for intended ROM installation: errors were not propagated. Do not describe it as a complete RealmeUI installation. compatibility.zip/file_contexts notices and later failed mounts are separate; missing payload is the confirmed installation defect. USB exFAT was mounted using exfat-fuse; warning was unclean prior unmount, not demonstrated archive corruption.
- Read-only SHA256 of20 current boot-chain partitions (both LK, TEE, GZ, boot, init_boot, vendor_boot, DTBO and vbmeta families) exactly matches the pre-sideload backup snapshot. This proves current bytes match, NOT that no write attempts occurred. No whole-super before/after hash exists. No reboot, slot change, flash, wipe or automatic retry in this log review. Phone left in OrangeFox.
- Evidence: outputs/duchamp-current-flash-log-20261118-215923/recovery.log SHA256 a734a12ecf3a9599360050c509cfb335646e92b5ad55c49c2d79e30ae1cd900f; installer-missing-files.txt includes exact line numbers; current-bootchain.sha256, bootchain-comparison.json and analysis.json. Path pointer outputs/current-flash-log-path.txt. Original archives/backups retained. Recovery image itself was just re-flashed and verified as described below; normal Android/RealmeUI boot still unverified. No commit/push.

ACTIVE HANDOFF - OrangeFox re-flashed and actually booted on A after RealmeUI failure (2026-11-18)

- User explicitly requested 'flash Orange'. Verified current product duchamp, unlocked and active A; rechecked original Dip184 R12.0 image64MiB SHA256 501ec32cb585c60c4db9245266c16469eb42b31f7b4fb37b8f8f6d1c7d45d9c9. Flashed ONLY vendor_boot_a; sending/writing OKAY, exit0. fastboot reboot recovery OKAY. No other partition flash, wipe, or B selection.
- Actual ADB recovery returned fox_duchamp, device duchamp, slot _a, crash_counter0, recovery PID371 alive. Physical vendor_boot_a SHA256 readback matches image. Recovery log and verification.json under outputs/duchamp-orangefox-reflash-20261118. Phone left running OrangeFox. Normal Android boot and RealmeUI installation are NOT verified or repaired by this recovery reflash. Prior both-slots-unbootable flags were not rechecked from Fastboot because recovery was kept open.
- Prior RealmeUI archive defects and pre-install21 valid backup images remain unchanged. No commit/push. Capture any next installer result/log before rebooting; do not infer installer success from host adb exit0.

ACTIVE HANDOFF - Current RealmeUI failure: BOTH slots marked unbootable, Fastboot only observed (2026-11-18)

- Latest user requested return to Slot A. Verified product duchamp and executed fastboot set_active a: OKAY, current-slot=a. Readback STILL reports slot-unbootable:a=yes and retries:a=0. Do not describe this selection as repairing bootability or resetting retries. No reboot, flash, partition-image write, or B selection during this instruction. Receipt: outputs/duchamp-realmeui-failure-20261118/set-active-a-user-request.log. Phone left in Fastboot.
- User now reports installing ZIP from within OrangeFox after earlier sideload and asks why it did not run. Read-only Fastboot confirms duchamp, unlocked=yes, current-slot=a, slot-successful A/B=no, slot-unbootable A/B=yes, retries A/B=0. Version duchamp_45cb0fdfa_202602051447. Do not assume Android A currently boots or either slot is a known-good fallback. Flags are boot metadata, not proof of physically corrupted partitions. No reboot/slot change/flash/write in this diagnosis turn.
- User's ROM ZIP is again on Desktop; SHA256 freshly matches e0c9c1cc0b1ec02a5c9ee28c03051fb3945aafe1f067f2eace1b25cf97d106eb. Existing extracted Desktop/RealmeUI_7.0_DUCHAMP/fw/ has no vendor_boot.img or vbmeta.img. The previously verified15 missing updater-script references remain applicable. These defects prevent complete installation via this ZIP; actual writes after user's recovery install remain unknown because final recovery log was never captured. Do not equate host sideload exit0 with install success or infer Chinese-region mismatch as proven cause.
- Maintainer guide https://telegra.ph/Install-guide-05-24 linked from wectazz's RealmeUI release documents both Recovery and Fastboot methods. Thus Recovery itself is not established as unsupported; guide does not prove this local archive complete. It mentions clean-data/format steps; do not execute wipes merely to troubleshoot without specific authorization.
- Evidence and diagnosis: outputs/duchamp-realmeui-failure-20261118/fastboot-readonly.log and diagnosis.json. Next useful observation is current recovery installer log/current boot-chain identity; any reboot/slot repair/reflash must be scoped to the user's next instruction. Current21 usable pre-install block snapshots remain under outputs/duchamp-realmeui-sideload-20261117/before-flash; preloader67-byte files are unusable. Historical Android14 baseline is not a valid substitute for user's updated firmware. No commit/push.

ACTIVE HANDOFF - D USB formatted exFAT and original RealmeUI ZIP moved with readback verification (2026-11-18)

- User requested repairing D and moving the ROM onto it. Read-only CHKDSK found no filesystem errors; limitation was FAT32 maximum single-file size, not filesystem corruption. USB D is approximately32GB (31,457,280,000-byte disk). Only two Windows indexing files (88 bytes total) existed; both backed up and hash-verified outside D.
- User explicitly approved formatting D only to exFAT and moving the ROM. Guarded elevated script matched USB disk identity/serial/path/size and partition boundaries before format. First attempt stopped without formatting due PowerShell5.1 JSON array enumeration; corrected read-only guards tested on5.1, second attempt exited0 and produced exFAT label ROMS.
- ROM CURRENT PATH: D:/RealmeUI_7.0_DUCHAMP.zip, 7,395,734,552 bytes. SHA256 e0c9c1cc0b1ec02a5c9ee28c03051fb3945aafe1f067f2eace1b25cf97d106eb. Copied to .partial while hashing locked source, flushed, read back and hashed all destination bytes; both hashes match. Renamed verified destination, then removed only the original C:/Users/Mehmedamir/Desktop/RealmeUI_7.0_DUCHAMP.zip. OriginalRemoved=true, no partial remains. File bytes were not repaired or modified; earlier package-installer defects still apply.
- Final CHKDSK D exited0, reports no filesystem problems; D Healthy, exFAT, size31,450,988,544, free24,054,956,032. C free155,952,287,744 at final observation. No physical phone action, flash, slot change or reboot in this USB task. Earlier sideload outcome remains unverified pending recovery screen/log.
- Exact scripts, drive-identity snapshot, pre-format88-byte backups, two format-attempt logs, transfer-result.json, final CHKDSK and verification.json are under outputs/duchamp-usb-rom-transfer-20261118. No automatic commit/push. Use D path for any future package inspection; old Desktop ROM path no longer exists.

ACTIVE HANDOFF - RealmeUI original ZIP sideload attempted on user's renewed explicit instruction (2026-11-17)

- After missing-file/dual-slot write findings were disclosed, user instructed 'just flash'. Preserved original ZIP without edits and executed actual adb sideload of C:/Users/Mehmedamir/Desktop/RealmeUI_7.0_DUCHAMP.zip. Entered sideload with documented OrangeFox `twrp sideload`; shell disconnected as expected. Host sideload command returned exit0 after about7.65s, reporting total transfer0.01x. THIS IS NOT INSTALLATION SUCCESS EVIDENCE. Phone remained in sideload and user reported installation still running. Waiting for actual recovery outcome; do not reboot or retry automatically.
- Three-minute read-only watcher completed with timeout; state remained sideload. /tmp/recovery.log pull failed 'connect failed: closed', because normal recovery shell is unavailable during sideload. User was asked for the last screen line/status. Host exit0 and0.01x transfer DO NOT prove ROM installation succeeded. Await the screen result/normal recovery ADB, then pull the log and assess actual writes before any reboot, retry or rollback.
- Saved 21 valid-sized current block images (~475MB total, including both boot, init_boot, vendor_boot, LK, TEE, GZ, DTBO, vbmeta families and misc) to outputs/duchamp-realmeui-sideload-20261117/before-flash/. Two extra preloader_raw_a/b files contain only67-byte cat errors (those paths absent); explicitly marked UNUSABLE in manifest. Do not flash these error strings. Actual current LK differs from old project archives; boot_a/b now identical updated Linux images, not prior XNU B fixture. Current vendor_boot_a is installed OrangeFox; B still previous stock vendor_boot at snapshot time. Do not restore historical Android14 files blindly.
- Logs: adb-sideload.log, adb-sideload.exit-code.txt, enter-sideload.log, recovery-before-sideload.log, before-flash-manifest.json and sideload-attempt.json under outputs/duchamp-realmeui-sideload-20261117. Preflight findings below remain valid. No manual partition writes, wipe, package changes or reboot in this sideload attempt; package installer may itself have written firmware. Need recovery log to determine actual effects. No commit/push.

ACTIVE HANDOFF - RealmeUI ZIP sideload preflight blocked by missing payload files (2026-11-17)

- User explicitly requested adb sideload of C:/Users/Mehmedamir/Desktop/RealmeUI_7.0_DUCHAMP.zip. Device was already in OrangeFox sideload, product fox_duchamp. NO sideload was sent, no new phone reboot/slot action/partition write/wipe in this request.
- Archive 7,395,734,552 bytes, SHA256 e0c9c1cc0b1ec02a5c9ee28c03051fb3945aafe1f067f2eace1b25cf97d106eb, 59 ZIP entries. Statically inspected original installer and scripts, did not execute package binaries or scripts. Installer references FIFTEEN nonexistent source paths: fw/preloader_duchamp.bin, fw/vbmeta.img, images/boot.img, images/init_boot.img, images/vendor_boot.img, and images/super.img.0 through .9. The existing image files use fw/; fw/vendor_boot.img and fw/vbmeta.img are absent entirely. Renaming paths alone cannot repair this package.
- Recovery updater-script prints ColorOS16 /16.0.5.700 /Davv98 while Windows scripts print RealmeUI7/wectazz. Metadata describes donor HyperOS OS3.0.5.0.WNLCNXM and references absent payload.bin. These identities do not establish payload provenance. Updater has 59 distinct block targets including both LK/preloader/TEE/boot-chain slots and shared super; partial installation could destroy the current fallback and overwrite XNU B. Bundled Fastboot scripts also reference missing fw/vendor_boot.img and fw/vbmeta.img. Do not switch to these scripts or run the format script (it also erases frp/metadata/userdata).
- Offline inventory, original installer, metadata and decision saved in outputs/duchamp-realmeui-sideload-20261117/preflight.json and zip-inventory.json. Need a complete maintainer-provided package and installation instructions before proceeding. Do not silently rebuild or substitute firmware, do not claim sideload succeeded. Source-built XNU, prior artifacts and user ZIP remain unchanged. No commit or push.

ACTIVE HANDOFF - OrangeFox recovery installed and booted on physical Duchamp A (2026-11-17)

- User explicitly requested finding/flashing OrangeFox in Fastboot, then confirmed a system update and instructed proceeding with the recovery image. Initial Fastboot identified duchamp, unlocked, active B. Selected A and attempted Android boot before flashing: returned automatically to Fastboot, as confirmed by user. Stock A recovery later exposed ADB. Historical recovery properties showed Android14, while OrangeFox subsequently detected installed OS3.0.5.0.WNLCNXM / SDK36. Do not mistake recovery build properties for installed-system identity.
- Existing OrangeFox community image and ZIP now verified against upstream Dip184 Custom_Recovery_v1.1 GitHub release digests. Image 67,108,864 bytes, SHA256 501ec32cb585c60c4db9245266c16469eb42b31f7b4fb37b8f8f6d1c7d45d9c9; ZIP 0d9e94518e27d8bacbc36d1dc6269beccda7e05e4fe3999fab8df86d34cd6ac8. Vendor_boot v4 recovery, not a standalone kernel. Bundled flash-whole-image script specifies vendor_boot. Firmware-specific blobs are documented by maintainer; do not claim universal compatibility or verified decryption.
- Actual command flashed vendor_boot_a only: send/write both OKAY, exit0, followed by fastboot reboot recovery OKAY. ADB returned fox_duchamp, slot _a, uid0; recovery log confirms OrangeFox R12.0 startup and GUI package loading; process recovery PID381 running, crash_counter0. Physical vendor_boot_a SHA256 readback exactly matches release. No other partition flashed, no format/wipe, no commit or push. B boot/vendor_boot/init_boot were not flashed. Android normal boot and userdata decryption were not verified after recovery installation. Leave phone in OrangeFox for user.
- Bootloader Fastboot fetch is unsupported; attempted vendor_boot_a.before.img is ZERO BYTES, NOT a backup. Existing Android images are historical and predate the user's update: do not restore them blindly to OS3. A/B metadata is now active A. Exact read-only queries, flash logs, release identity, readback, recovery properties/log and flash-result.json are in outputs/duchamp-orangefox-install-14480607-231224 (PowerShell local calendar generated this directory name).
- Prior source-built XNU, frozen candidate and Darwin compositor files preserved. Native XNU memory-evidence blocker remains unchanged; recovery success does not establish XNU/UFS or DMA support.

ACTIVE HANDOFF - Darwin compositor stage 2, actual QEMU clients and lifecycle (2026-11-17)

- Accepted final run: outputs/duchamp-darwin-compositor-20261117/attempt-4, 25/25 checks, exit 0. Same source-built XNU e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457, unmodified. Native boot stays BLOCKED_BY_MEMORY_EVIDENCE; historical export stays EXPORT_INTERFACE_UNAVAILABLE. No phone/firmware/UFS operation, reboot, slot change, commit or push.
- Implemented real launchd-managed custom Mach service org.duchamp.qemu.compositor with capability-backed IOSurface import and kernel-appended audit PID/PID-version ownership. Bounded 64x32 CPU compositor: Z-order, straight-alpha, private snapshots and dirty rectangles, two CPU/output buffers, focus/press capture and dead-name-triggered IOKit cleanup. No new Apple private class, proprietary compositor protocol, GPU or SpringBoard claim.
- Self-test daemon PID12, clients14/16, owners audit versions35/40, client surfaces4/5, output surfaces2/3. All six framebuffer RAM crops byte-match independent oracle in order: blend, dirty8x8, raised Z, restore, overlay cleanup, all cleanup. 8192 bytes per frame at 320,1664. Press/release went to overlay despite focus change mid-press; SIGKILL after release ACK generated kernel death notification. Old surface lookup denied after close. Remaining red client got next pair and exited0; its surface was reclaimed too.
- Ordinary daemon mode is separate from --selftest; no scripted transitions or client kill in normal mode. Second daemon PID28 survived early clients30/32 with zero events/ACKs, closed both mappings and rejected old-ID lookups. Both daemons were removed with launchctl bootout and confirmed gone. --selftest jobs are explicit copied-QEMU fixtures only.
- Tests: compositor25/25; original graphics10/10, dual filesystem11/11, services74/74; separate real dynamic/static Mach-O17/17 (PID2 exit0, PID3 exit42); native core/audit parser48 assertions under ASan/UBSan; observer12/12; default packaging12/12 and accepted payload restrictions7/7. Guest117.177 host seconds, no observed panic, zero unknown glyphs. md0 byte-identical SHA a4dd47519657fc6cfedcaa29895d52bbb52c2c9b53b8e1e856652c23d0564de5, md1 writable, EROFS/raw-root denial/ENOSPC/var alias/console preserved. 25 frozen local native/recovery hashes unchanged.
- Shared IOKit implementation extracted from stage1 into tools/duchamp-darwin-iokit.h; stage1 reran successfully. New engine/wire/service/runner/oracle/control files use duchamp-compositor-* and duchamp-darwin-compositor* names. Explicit compositor options added to existing QEMU/graphics/var/service runners; default five system jobs remain unchanged. Exact commands/logs/binary hashes and failed attempts retained outside repo.
- Early attempt1 exposed VM-page-rounded surface allocations (16KiB vs logical8KiB); actual XNU layout source justified a bounded64KiB mapping cap plus unchanged logical bounds. Attempt2 passed initial22 checks. Attempt3 was superseded during harness extension and is not accepted evidence. Attempt4 built and tested consistent final sources, including explicit owner-checked FOCUS RPC and normal-mode early cleanup.
- Report docs/DUCHAMP_DARWIN_COMPOSITOR.md includes API, ownership/lifetime, bounds, six frame hashes, source paths, exact reproduction and limitations. Next independent milestone: interactive open-source client, digitizer/pointer, resize and broader fault/lifetime stress. Keep native candidate frozen; QEMU surface ownership does not establish physical MT6897 memory/DMA ownership.

ACTIVE HANDOFF - firmware evidence frozen; real Darwin IOKit graphics/input in QEMU (2026-11-17)

- Native status stays BLOCKED_BY_MEMORY_EVIDENCE and historical Blackbox export stays EXPORT_INTERFACE_UNAVAILABLE. No supported new historical exporter was established. Official Xiaomi Services & feedback instructions describe active issue capture, not Blackbox generation selection or authenticated final BL31 state. No new Blackbox parser or simulated authorization model was added. No phone operation, flash, reboot, slot action, physical UFS/modem access, firmware change, commit or push.
- Exact source-built kernel e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457, native 32+4 MiB candidate, bootshim, FDT and memory validators preserved. 25 local input hashes (including nine saved recovery/boot-chain images) still match. These are preservation checks, not a new recovery-UI or physical-device validation.
- Reused graphics and HID providers already compiled into this kernel. New 0BSD dynamic tools/duchamp-darwin-graphics.c runs under original launchd as PID 10, PPID 1, with 37 dyld images. Matched AppleCLCD, IOCoreSurfaceRoot, SweetHIDButtons and SweetHIDTouch; nonexistent provider rejected. Real shared HID queue delivered Menu down/up, ordered sender/timestamps and two Mach notifications.
- Real surface 2, SwapEnd/SwapBegin ID 1, rectangle 160,1600,64,32. QEMU framebuffer RAM crop exactly matches all 8192 expected BGRA bytes, SHA-256 1af2135a15afd0e0b13b696ce529cf84a0e17341fdfee3b6416a30317a683521. Screenshot is a diagnostic gradient, not iOS UI or physical GPU/input evidence. No BackBoard/SpringBoard execution in this phase.
- Correct probe ABI uses supported matching_service_bin ID2880, open2862, map2863, method2865, notify2818; mach_msg2 kernel-object flag; LP64 OOL descriptor type@11/size@12. Legacy string matching explicitly returns unsupported. Existing HID entitlement check rejected unentitled v10. Successful v11 has only the required HID entitlement in its own verified ad-hoc test signature; no kernel check was weakened.
- Successful accepted run outputs/duchamp-darwin-next-stage-20261117/graphics-v11: graphics integration 10/10, dual-RAMDisk 11/11, original services 74/74, zero unknown console glyphs, no observed panic, 71.424 host seconds. Read-only root unchanged, writable md1/var alias, EROFS, raw-root denial, ENOSPC/recovery and console all pass. Native parser ASan/UBSan 10/10, observer 8/8, packaging 12/12, exact HID/storage profile rejection 7/7. Separate source-kernel Mach-O regression 17/17: dynamic PID2 exit0 and static PID3 exit42, real Mach IPC. Default packaging/services behavior preserved.
- New tools: duchamp-iokit-wire.h, duchamp-darwin-graphics.c, qemu_frame_witness.py and three targeted tests plus test-duchamp-darwin-graphics.py. Opt-in integration only in qemu-sweet.py, qemu_ramroot_var.py, test-duchamp-readonly-var.py, sweet-launchctl-control.c and verify-sweet-syslogd.py. Artifact manifests record exact commands/log hashes and frozen inputs; prior failures v1-v10 retained, v11 alone accepted. Preexisting tracked diff and edited-file copies saved outside repo before changes.
- Reports: docs/DUCHAMP_FIRMWARE_EVIDENCE_BLOCKER.md, docs/DUCHAMP_GRAPHICS_BRINGUP_PLAN.md, docs/DUCHAMP_DARWIN_NEXT_STAGE.md. Next independent milestone: open-source input-driven UI loop, digitizer/contact/cancellation and cleanup tests. Native work requires new final-boot ownership/DMA evidence; do not resume repeated history searches or move the frozen candidate without it.

ACTIVE HANDOFF - LK Blackbox historical export investigation (2026-11-17)

- Historical result EXPORT_INTERFACE_UNAVAILABLE within the reviewed/currently permitted interfaces; physical readiness remains BLOCKED_BY_MEMORY_EVIDENCE. No historical B record was recovered and no new phone command was executed. No reboot, slot action, physical UFS access, storage write, firmware change, commit or push. Exact 32+4 MiB candidate/kernel/bootshim and earlier 50-test baseline are preserved.
- Actual pinned LK writer is file+0x51a24, normal caller 0x10050 before secure handoff. Resolves storage label blackbox, uses block read/write dispatch 0x65758/0x657c8. Archived Fastboot device list names that label, 165,670,912 bytes. No physical partition was read this phase. Matching full LK C source is unavailable; another SoC's decompilation is not authority.
- Correction: dump_count=4 in the A banner is an old CURSOR, not four-slot capacity. Pinned instructions 0x51d08..0x51d34 implement five cyclic positions: 5 -> 1, else old+1; record start (cursor-1)*stride+first_offset. Generation banner prints before 32-bit increment. Captured 794/cursor4 implies intended stored generation795/position5, not an actually recovered record795. Header writes precede PL/LK bytes, so fresh metadata does not establish complete payload or atomic write. Survival of a particular old B record is unknown.
- Official MiCode 3c4ccd07 source was fetched and Git-blob verified. log_store.c is byte-identical to the old saved community source. Its proc reader copies the current mapped DRAM log, with no history selector. Separate proc write changes boot/log state and was not used. Reviewed AEE current exception/reboot-reason exports and actual Fastboot current-log handling do not establish historical Blackbox export. Private OEM tooling remains unknown. No invented command, raw-memory scan or raw storage operation.
- Added tools/audit-duchamp-lk-blackbox.py: 28/28 static instruction assertions pass. Hardened existing current-log observation parser/tests: 16/16 pass, covering Blackbox printed metadata corruption/geometry/generation plus existing acquisition/slot/allocation checks. It is NOT a historical binary record parser. Freshness/origin/history recovery and all hardware authorization remain false, even for internally consistent older text. Phase 3 historical parser deferred because no supported export is established. Prior 13/13 original-decoder tests unchanged, not rerun.
- New reports docs/DUCHAMP_LK_BLACKBOX_HISTORY.md and docs/DUCHAMP_SLOT_B_HISTORICAL_EVIDENCE.md; prior memory/trace reports corrected. Exact source references, commands, logs, hashes and before-change copies are in outputs/duchamp-lk-blackbox-history-20261117. Next external requirement: supported read-only OEM historical export with generation/slot/image/origin/completeness contract. Even such LK history cannot establish final BL31 effects, XNU entry or DMA isolation. Do not advance dependent hardware work.

ACTIVE HANDOFF - Actual LK allocator channel and LZ4 guard boundaries (2026-11-17)

- Decision remains BLOCKED_BY_MEMORY_EVIDENCE at d91562d, duchamp-bootstrap. Exact native 32+4 MiB Image/envelope, source-built kernel, saved FDT and all 12 previous baseline entries remain byte-identical. Existing 50-test sources/manifest were checked, not rerun. No guest/kernel/bootshim/candidate/access-gate changes, commit or push. Copies of the previous two reports and NOTES are outside the repo in outputs/duchamp-actual-lk-memory-20261117/before-document-update.
- New REAL read-only ADB evidence: connected duchamp/mt6897, Android Global V816.0.17.0.UNLMIXM, slot A; existing Magisk root works. No root installation. Saved 257,652-byte /proc/pl_lk raw buffer SHA-256 5731b1ad6f2cf36194cff78e0dcfeaa7ed50f3f3ff4332313174554b0d61643b. Android boot-ID digest was unchanged during capture. Raw log line 4664 reports mb_avb [0x334a00000,0x33d600000), 140 MiB; line 4990 reports free after decompress_kernel. This is A, never B/XNU authority. Mapping, loaded-data pointer and release success returns are absent. Ordinary shell was denied; its error output is preserved. Root receipt's initial broad substring heuristic marked the real log false because it contains legitimate "not found" text; extraction validates raw hash/structure instead, without rewriting the original receipt.
- Actual A log also shows modem start, PGD-clean/protection call messages and later LK frees. It prints OEM blackbox boot index 0x31a = 794, cursor4, 8 MiB stride and PL/LK logstore copy. The later source audit above corrects the initial four-slot interpretation to five positions. This is a concrete retention lead, NOT proof a B record survives or contains post-BL31 policy/XNU entry. No blackbox partition was read/written. No invented vendor command, guessed physical address or firmware patch.
- Reviewed pinned MiCode log_store.c already saved in outputs/duchamp-diagnostic-channels-20261111: pl_lk_log_show lines 213-233 copies mapped DRAM, no UFS operation; no historical selector. Separate proc write handler calls boot-phase/log-state changes, not retrieval, and was not used. Repeating current A reads cannot recover overwritten B bytes. Installed binary equivalence is not inferred from a build property alone.
- Exact LK allocator request is size 0x8c00000, alignment 0x1000, lower bound 0, limit UINT64_MAX, no fixed start, map0. Core coalesces free entries, keeps last eligible list entry and aligns down within it; no unproved global highest-address or DMA-security assumption. AVB pool release/unmap may fail and does not clear all globals or establish DMA drain. Actual B pool/input PA, allocator lifetime and final modem/peripheral exclusion remain missing.
- Added unchanged-LK-decoder guard test sources duchamp/tests/lk_lz4_bounds.{S,c,ld} and tools/test-duchamp-lk-lz4-bounds.py. Final isolated ARM64 QEMU regression passes 13/13, compiler/QEMU exits 0. Seven logical outputs match Image; exact capacity succeeds; insufficient/zero/truncated cases return errors. Deliberate lying-capacity fixture traps original file+0x5931c str x21,[x6], an 8-byte store beginning logical_end-4 and crossing four bytes. Normal greater-capacity case verifies exactly four zero tail bytes. This is optimized match-copy tail within advertised capacity, not returned semantic output. It does not establish physical allocation safety. Copied firmware bytes are verified unchanged.
- New tools/inspect-duchamp-lk-allocation-log.py extracts actual observation lines, acquisition/slot consistency, pool bounds/order and producer index. It always leaves firmware origin unauthenticated, complete B handoff false and physical access false. Nine real-capture-derived consistency tests pass; it is not connected to authorization. Exact commands, binary/log hashes, disassemblies and test receipts are in outputs/duchamp-actual-lk-memory-20261117, notably lz4-guards-final/verification.json and observation-checks-final.json.
- Updated docs/DUCHAMP_SLOT_B_MEMORY_UNBLOCK.md and docs/DUCHAMP_RUNTIME_ALLOCATION_TRACE_PLAN.md. No same-B input/mapping addresses, post-BL31 lifetime, effective master/domain/drain/cache contract or XNU-entry correlation exists. Preserve unknowns and stop dependent hardware work. This turn read existing Android metadata and memory-backed proc logs only; no reboot, slot switch, flash, physical UFS MMIO/DMA, partition write or firmware change.

ACTIVE HANDOFF - Slot B decompression and runtime trace unblock (2026-11-17)

- Decision remains BLOCKED_BY_MEMORY_EVIDENCE at d91562d. Candidate 32+4 MiB, source-built kernel and existing 50-test source/manifest hashes are preserved. No guest, bootshim, payload, image, authorization gate or recovery changes. No phone access, reboot, slot action, physical UFS, commit or push.
- New source evidence closes normal input provenance: normal dispatcher 0x10d3c -> load 0x52abc -> loaded-partition consumer 0x52f40 -> setter 0xd680 -> getter 0xcd50. This refines the earlier report's unresolved setter path. Full-partition fallback at 0x9fbfc allocates through 0xa0398/0x9fe48; source requests a dynamic 140 MiB mb_avb pool and vm_avb mapping at 0xa4504. Actual normal-B pool/input PA, mapping and cursor are still unavailable. AVB pool release follows decompression at 0xfdb8.
- Closed LZ4 block/memmove call graph has no heap calls, decoder frame 48 bytes, wrapper frame 192 bytes and outer boot_linux_fdt frame 160 bytes. These 400 identified bytes are not the whole LK stack peak. New isolated ARM64 QEMU replay executed unchanged saved decoder/memmove, matched all seven blocks to the 57,417,168-byte Image and found FOUR changed bytes past the logical Image end, [0x436c1dd0,0x436c1dd4) at the historical output PA. This is within the supplied 8 MiB block capacity. Account conservatively for the 56 MiB capacity envelope through 0x43800000, not just logical file length. It fits historical mb_kernel but does not establish runtime ownership.
- Replay final exit 0; 28 binary instruction assertions exit 0. ELF copied firmware payload matched all 990,320 bytes. Initial harness attempts (wrong host linker, MMU-off alignment fault, strict logical-end canary failure) are retained and explained. Existing 50 tests and full-XNU boots were not repeated; only the newly analyzed decoder pair was replayed. Artifacts, exact commands, logs and manifest are in outputs/duchamp-memory-unblock-20261117.
- Newly targeted search found no mb_avb/normal-decompress event in existing Fastboot PL/LK or lkmsg/lpmsg raw archives. The previous Android A observer saved hashes/markers but discarded raw pl_lk bytes, so those cannot be searched retroactively. No same-boot final BL31 isolation record exists in reviewed captures. Need supported normal-B allocation/mapping telemetry, complete stack/lifetimes and final master/domain/drain/protection evidence with actual XNU entry correlation. Keep dependent hardware work stopped.
- Deliverables: docs/DUCHAMP_SLOT_B_MEMORY_UNBLOCK.md and docs/DUCHAMP_RUNTIME_ALLOCATION_TRACE_PLAN.md. Blockers are classified by source, existing-runtime trace, supported firmware instrumentation, hardware validation or unsupported current path. No independently safe relocation exists. Next external action is obtaining supported raw normal-boot allocation records and final isolation telemetry, not another simulated grant.

ACTIVE HANDOFF - LK memory ownership audit (2026-11-17)

- Decision BLOCKED_BY_MEMORY_EVIDENCE at d91562d on duchamp-bootstrap. Preserved the exact native 32+4 MiB reference, source-built kernel, Image, unsigned envelope and embedded HFS+ hashes. Full tracked diff was saved outside the repo as outputs/duchamp-memory-ownership-20261117/baseline.patch. Existing untracked work remains in place. No commit or push.
- New evidence: retained LK Fastboot allocation log explicitly reserves mb_kernel [0x40000000,0x47c80000), which contains the 57,417,168-byte reference Image. Audited LK queries that reservation, passes output extent to the decompressor, then attempts to release BL33/kernel/DTB before exporting mblock_info. Release completion and subsequent ownership are unproved. The retained log is Fastboot, not a correlated XNU boot.
- Added a bounded decoder for the archived LK v2 mblock layout. Saved FDT has 29 active free-pool entries and 52 reservations, with holes through slot 57 and stale free slots after the count. All 52 active reservations match fixed FDT nodes including mapping flags. Historical free pools cover both low Image and high 512 MiB XNU window. Dynamic Linux DPMAIF alloc-ranges are potential policy conflicts, not proof LK overwrote the candidate with modem buffers. Earlier memory reports must be read with this refinement.
- Added host-only lifetime/overlap analysis and pinned LK/FDT/log audit. Final tests pass 16 interval + 19 lifetime + 15 parser cases, 50/50 total. Real archive cross-check matched 52/52 reservations and 11 LK instruction assertions. Syntax and whitespace checks passed. No kernel/bootshim/payload/configuration changes, so QEMU was not rerun. Receipts, exact commands, exit codes, hashes and all intervals are in outputs/duchamp-memory-ownership-20261117/verification.json and corroborated/memory-ownership-audit.json.
- Remaining: actual normal-boot compressed-input/scratch addresses and peak, reservation lifetimes after LK release/final BL31 callbacks, same-boot ownership of the full XNU window, firmware/modem writer exclusion and effective DMA/IOMMU/fabric permissions. Alternative high bases clear historical fixed geometry but current native preflight rejects relocation. No physical ownership established by moving or compressing the image.
- Reports: docs/DUCHAMP_LK_MEMORY_ALLOCATION_AUDIT.md, docs/DUCHAMP_SLOT_B_MEMORY_EVIDENCE.md, docs/DUCHAMP_SAFE_PLACEMENT_DECISION.md. Next external requirement is supported final allocator/isolation telemetry or the matching LK/BL31 source and an approved instrumentation path, correlated with actual XNU entry. No phone transport, reboot, slot change, flash, MMIO, DMA or modem modification was performed.

ACTIVE HANDOFF - QEMU disk cleanup (2026-11-17)

- User authorized cleanup of old tests and unrelated temporary files. Removed 177 ended QEMU runtime outputs under /home/mehmedamir/.cache/duchamp-qemu-tests, accounting for 140.4277458190918 GiB of allocated blocks. These include guest RAM snapshots and final runtime volume dumps. Archived logs, scripts, image seeds, source-built kernel, native candidates and build toolchains were retained.
- Cleaned apt package archives, ran fstrim, stopped idle Ubuntu and completed built-in Windows DiskPart compaction with exit 0. Ubuntu restarted successfully and isolated Clang 24 is available. The source-built kernel digest and nine archived A/B boot-chain images were reverified. Existing desktop Setup and the latest compact/GPT root dependencies exist.
- C free space rose from about 15 GiB to about 157 GiB during cleanup. The Ubuntu VHDX file shrank from about 350 GiB to about 221 GiB. See outputs/duchamp-disk-cleanup-20261117/cleanup-result.json and the exact deletion manifest.
- Windows temporary-file removal was rejected by automatic approval review with only a generic policy reason. The first generated compaction script was blocked by Windows protection. The supported DiskPart tool completed the actual VHD compaction directly after Ubuntu stopped. No Windows temporary deletion is claimed.
- Project work remains uncommitted. The memory-placement decision remains BLOCKED_BY_MEMORY_EVIDENCE as documented below.

ACTIVE HANDOFF - Duchamp MT6897 safe memory placement (2026-11-17)

- Decision BLOCKED_BY_MEMORY_EVIDENCE on duchamp-bootstrap at d91562d. Offline unsigned lab envelopes for md0+md1 32+8 MiB and 32+4 MiB are 14,905,344 and 14,888,960 bytes. Raw Images are 61,611,472 and 57,417,168 bytes. Both passed preflight and LZ4 round trip.
- Same source-built kernel e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457 passed independent 4 MiB and 8 MiB QEMU tests (11/11 integration and 74/74 services each), five 4 MiB failure profiles, 17/17 Mach-O checks and both bootshim twins. Native and ARM64 bounds passed 16 cases each, the map checker passed 15 tests, and four injected reservations were denied by the bootshim guard.
- The historical FDT has 52 fixed reservations and four dynamic requests. Both Images intersect the possible DPMAIF and MKP allocations. The expanded bytes beyond the archived B Image lie in both DPMAIF candidate ranges. The saved 512 MiB high XNU window clears declared reservations. Neither stage has proven same-boot ownership or DMA exclusion, and no new native LK decompression limit or AVB outcome was established.
- Reports are docs/DUCHAMP_MT6897_MEMORY_MAP.md, docs/DUCHAMP_MODEM_MEMORY_ANALYSIS.md, docs/DUCHAMP_BOOT_IMAGE_COMPATIBILITY.md and docs/DUCHAMP_SAFE_PAYLOAD_LAYOUT.md. See outputs/duchamp-mt6897-safe-placement-20261117/offline-evidence.json for reproducible command records and the map. Keep work local and stop before physical tests.

ACTIVE HANDOFF - Native preparation for the source-built Duchamp kernel (2026-11-17)

- Decision BLOCKED. Source-built kernel e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457 passed a fresh offline QEMU replay. Dual 32+32 MiB 11/11, launchd/services 74/74, Darwin Mach-O 17/17, and five error profiles passed. The 32+8 MiB profile also passed 11/11 and 74/74 with ENOSPC and cleanup.
- Compared the exact previously booted Slot B image with the new Mach-O and physical ADT. Both native payloads materialize against the archived FDT. Both injected md1 reservation collisions were rejected. The compact QEMU bootshim twin reached XNU and verified return-slot contents.
- Existing packer rejects the 86,777,296-byte 32+32 MiB raw Image. Compact 32+8 MiB payload hashes to 4f4ea161e1657999f653d856c65ec927b9e64fa2e0a50512405ecd5f92deb07e. Its unsigned 14,905,344-byte Android v4 lab envelope rebuilt byte-identically and fits before the archived stock boundary.
- The saved high window clears all reservations. The expanded low Image crosses possible modem DMA allocation ranges. Establish actual handoff occupancy and DMA exclusion, the supported policy for the unsigned candidate and current recovery reachability before a later review. Nine archived A/B files rehashed against prior live receipts. No phone or physical UFS operation, commit or push.
- See docs/DUCHAMP_NEW_XNU_HARDWARE_READINESS.md and outputs/duchamp-xnu-hardware-readiness-20261117/build-manifest.json.

ACTIVE HANDOFF - Source-built XNU and dual RAMDisk in QEMU (2026-11-17)

- Built isolated UniXNU-patched Clang 24.0.0git in Ubuntu WSL. The builtin and real-header checks passed. Compiled IOKitBSDInit.cpp and memdev.c, then 1126/1126 source objects with no archived kernel objects in the link.
- Fixed C++ typed-pointer checks, Clang 24 NFS buffer and SHA assembly compatibility, SWEET CPU selection and the original loader boot-argument reservation. Linux ld64 compiled/link receipts include the kernel destructor-lowering option for bootstrap.cpp.
- Final 19,541,944-byte kernel SHA-256 e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457. ARM64 LC_UNIXTHREAD entry 0xfffffe00074aa488 and md0/md1 registration 0xfffffe0007506b60. Zero unresolved symbols.
- Exact kernel passed QEMU dual-RAMDisk 11/11, original launchd/syslogd/notifyd 74/74, Darwin Mach-O 17/17 and error-path cases 5/5. Original launchd ran as PID 1. md0 remained byte-identical and returned EROFS. md1 mounted at /private/var, returned ENOSPC at the limit and recovered capacity. Dynamic PID 2 exited 0 and static PID 3 exited 42.
- See docs/DUCHAMP_PATCHED_CLANG_BUILD.md, docs/DUCHAMP_NEW_XNU_QEMU_BOOT.md and outputs/duchamp-patched-clang-20261117/verification.json. Result is QEMU-only. Physical UFS remains disabled. Changes are local and uncommitted.

ACTIVE HANDOFF - Linux Firehose and XNU reference relink (2026-11-17)

- Built libfirehose_kernel.a on WSL from Apple libdispatch-1415.140.2 matched to xnu-8796.141.3. The 34,392-byte plain ARM64 archive reproduced SHA-256 9452c8d39826db46ff2e40c0ad6ed128f95ec78557378a607d0a1e52eb7f9d7f. Built the real LLVM 15.0.7 kernel profiling archive after verifying the historical caller ABI. LLVM 21.1.8 has an incompatible profile buffer argument list.
- Added a diagnostic ARM64 Darwin stack probe with real page reads. Its 48 instruction bytes match the reference helper. Ten ARM64 QEMU user-mode cases passed, including preserved SP and expected guard faults. The helper is outside the default kernel build.
- Linux ld64-951.9 relinked the archived XNU object set using these source-built dependencies, exit 0. The explicit SDK 15.5 reference passed layout inspection, entry 0xfffffe0007480488, SHA-256 2c3ab344f9f325d172719eb14785b2080263b6670d7492b989d8f8b14035d594. It lacks dual RAMDisk registration and was rejected for packaging. Host payload regression passed 12/12.
- Fresh staged memdev.c compiles without stand-ins. IOKitBSDInit.cpp fails with stock Clang lacking the XNU typed allocation builtins. Next verify the real UniXNU patched compiler against both files and build the complete SWEET source snapshot. The prepared Xcode fallback inventory reverified 858 inputs. No modified-kernel payload or full guest boot, no phone operations, commit or push.
- See docs/DUCHAMP_LIBFIREHOSE_BUILD.md, docs/DUCHAMP_LINUX_XNU_LINK_STATUS.md, docs/DUCHAMP_FULL_KERNEL_QEMU_RESULT.md and outputs/duchamp-linux-firehose-20261117/verification.json.

ACTIVE HANDOFF - Duchamp full XNU source link diagnosis (2026-11-17)

- Captured complete link-probe argv and compared CI 41543710742 ARM64 layout, thread-state entry, symbols and Apple ld 955.13. WSL LLD 21.1.8 ignores kernel-static, image-base and segment-order flags. The tested Linux ld64-951.9 port honored those settings on a minimal Mach-O. The archive diagnostic is blocked by missing libfirehose_kernel. The complete fresh toolchain/object build is unavailable locally.
- Added the kernel layout validator to normal dual-RAMDisk packaging and the macOS workflow. Prepared and hashed the current source with the exact local IIG ZIP. Local dxb staging at 663906528d1cd5ea8fde7de6f16de73db9511549 succeeded. The portable source workspace is under outputs/duchamp-full-xnu-source-build-20261117/source-ready.
- Format checks 11/11, dual-payload 12/12, single-RAMDisk 2/2, prior preflight 10/10, bounds 16/16 on native sanitizers and ARM64 QEMU. Reference kernel replays passed Mach-O 17/17 and services 74/74. Boot-image regression 13/13 matched the saved 64 MiB image.
- No new linked kernel or modified-kernel QEMU boot. Run the prepared source on Xcode 16.4 with SDK 15.5 and the pinned dxb/KDK environment, then test the exact output hash. See docs/DUCHAMP_XNU_LINKER_ANALYSIS.md and docs/DUCHAMP_FULL_XNU_SOURCE_BUILD.md. No physical device, UFS, commit or push.

ACTIVE HANDOFF - Darwin read-only root plus writable /private/var (2026-11-16)

- QEMU-only dual-HFS profile reuses the BSD memory-device and HFS+ code. md0 is the readonly 32 MiB root. md1 is a fresh writable 32 MiB HFS+ volume mounted at /private/var by a checked PID 1 preflight. /var resolves to it and devfs exposes the console. A pinned private kernel overlay registers md1, with no production staging or phone packaging.
- The final full XNU guest passed 10/10 integration and 74/74 original service checks in 71.486 s. Same-boot md1 witness records EROFS=30, ENOSPC=28 after 32,702,464 bytes and recovered capacity. It then created logs while the root dump remained byte-identical. Original launchd PID 1 ran notifyd PID 8 and syslogd PID 5. The two clients exited 0 and six ASL records were verified.
- All four full-XNU bad cases stopped before launchd. Fresh baseline boots passed 17/17 Mach-O and 74/74 services. 7/7 new payload, 10/10 historical packaging, 9/9 native evidence, staging, archive digests and same-seed restart checks passed.
- See docs/DUCHAMP_READONLY_ROOT_WRITABLE_VAR.md and outputs/duchamp-readonly-var-20261116/verification.json. The baseline Git patch, test manifest and untracked source archive are outside the repo. No hardware access, UFS, commit or push.

ACTIVE HANDOFF - Read-only 32 MiB HFS+ Darwin userspace in QEMU (2026-11-16)

- The first full-XNU boot mounted HFS+ but failed devfs/console because the base lacks /dev. The offline builder now pre-creates /dev in the copied readonly fixture and verifies the files placed in it. The existing kernel and bootshim stayed unchanged.
- The 0BSD dynamic C probe executed via the 20F66 restore dyld/libSystem as PID 2 with 37 images, verified readonly HFS+ statfs and directory/file/EOF, private mmap, errno and a real Mach loopback, then execed the 0BSD static LC_UNIXTHREAD child (PID 3, verified exit 42). The static PID 1 harness reaped the C child with exit 0. Full guest checks 17/17 in 93.376 s, same RAM disk bytes pre/post boot, identical repeat packaging.
- Original launchd/notifyd/syslogd service regression on the separate writable fixture passed 74/74 in 71.438 s. Native evidence checks 9/9, preserved packaging 10/10, legacy builder 39 files re-extracted, and UFS handoff 98/98 per native ASan/UBSan and ARM64 QEMU. Archived phone image still matches SHA-256 545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8.
- Read docs/DUCHAMP_DARWIN_USERLAND_STATUS.md and docs/DUCHAMP_HFS_RAMROOT_EXECUTION.md. Receipts are in outputs/duchamp-darwin-ramroot-20261116. Next integration is the original service lifecycle with readonly boot root plus volatile writable /private/var, then existing large-cache and IOKit/compositor tests. Physical UFS remains BLOCKED_BY_FIRMWARE. No phone access, commit or push.

ACTIVE HANDOFF - MT6897 firmware interface audit and verified RAM-root package (2026-11-16)

- The saved DTB and Android archive confirm the MediaTek SCMI tinysys endpoint. Its sole declared DT protocol is vendor 0x80. UFS references separate clock and reset providers. The saved UFS SiP dispatch and PSCI support establish no Slot B UFS ownership, DMA drain, cache contract or proven physical effects for XNU.
- HakiOS MT6768 relies on LK-ready eMMC PIO. HakiOS Qualcomm UFS relies on UFSDxe and a cooperating loader. Xiaomi Linux documents the platform dependencies. Physical UFS remains BLOCKED_BY_FIRMWARE. Cold initialization stays offline, while the 32 MiB services HFS+ root can boot with rd=md0.
- The services packager now checks the embedded HFS+ bytes against the QEMU proof and requires the ADT RAMDisk to address exactly that segment. 74 guest, 10 payload and 13 package checks passed. The local 64 MiB image equals the archived candidate byte for byte. 67 cold-init and 98 handoff cases passed in each environment. The current UFS gate denied access without callouts.
- See docs/DUCHAMP_FIRMWARE_UFS_OPTIONS.md, docs/DUCHAMP_UFS_RESOURCE_CONTROL_MATRIX.md and outputs/duchamp-firmware-ufs-options-20261116. No phone access or changes. Work left uncommitted.

ACTIVE HANDOFF - Android A recovery reconciled, hardware trace still blocked (2026-11-16)

- Read-only ADB confirmed completed Android A on Duchamp/MT6897 Global V816.0.17.0.UNLMIXM with Magisk 30.7. All six A boot-chain hashes and sizes match the archived working baseline. Live init_boot_a is exactly magisk_patched-30700-duchamp-correct.img. All three installed B service images match the previously booted triplet.
- Offline Magisk v30.7 unpack/restore/repack reproduces the stock-labeled init_boot_a file byte for byte from either same-origin historical patch. It has matching stock CPIO contents but fails the live signed init-boot descriptor. The saved Xiaomi Global OTA init boot matches that signed descriptor and the recorded Magisk original SHA-1. Live vendor_boot_a and its type-2 recovery fragment match the archive. No recovery-mode boot was attempted.
- Live tee_a and tee_b have different container sizes but the exact same stored audited atf component. Android A ATF, PL/LK, bootprof and pstore read-only captures did not supply an authenticated final BL31 and XNU pair from B. Kernel CoreSight is disabled and a supported external secure/entry trace is unverified. No new authorization model or physical candidate was prepared.
- BLOCKED_BY_FIRMWARE. Cold init remains offline until resource ownership, DMA isolation and cache authority are verified. Existing 67 cold-init, 98 handoff and 12 passive cases each pass in ASan/UBSan and ARM64 QEMU, and 11/11 full-XNU QEMU cases pass with nine empty denial traces. See docs/DUCHAMP_ANDROID_A_RECOVERY_VERIFICATION.md and outputs/duchamp-hardware-unblock-20261116. No device writes or boot changes. Work left uncommitted.

ACTIVE HANDOFF - Final BL31/XNU capture correlation and one-boot procedure prepared (2026-11-16)

- Reverified LK/BL31 shutdown and reset instructions, including the first-entry BL31 group-5 callbacks and subsequent helper. Archived Android ATF, Fastboot PL/LK, and pstore exports provide no authenticated same-boot Slot B XNU handoff. Generic TF-A instrumentation and CoreSight supply no evidence of supported trace on this handset.
- Added an offline verifier for independent final-exit and actual XNU-entry witnesses. It checks pinned Ed25519 keys, attempt and image identity, final FDT and entry ADT, ordering, entry coordinates and observation receipts. 44 mock cases pass, including synthetic-scope rejection by the physical-input CLI. The verifier grants no physical access.
- The exact November 11 Slot B services triplet and three historical B rollback files rehashed correctly. The exact decompressed B image reached the XNU marker in 7 GiB QEMU and its 11-segment payload passed preflight. The archived stock A init_boot file does not match the recorded A baseline. Confirm the matching A recovery set and the currently installed B digest set before any future physical attempt.
- 12 passive entry and 98 handoff model tests each pass on native sanitizers and ARM64 QEMU. Existing CI 43631086106 passes 11/11 fresh full-XNU regressions with nine blocked cases and zero virtual UFS events in each. See docs/DUCHAMP_FINAL_BL31_XNU_HANDOFF.md and outputs/duchamp-final-bl31-xnu-20261116. No phone operations performed. Physical UFS remains disabled.

ACTIVE HANDOFF - Duchamp trusted boot evidence boundaries and passive capture (2026-11-16)

- Reverified the saved LK/BL31 cleanup and reset path. LK is the last identified HCI writer in the static trace, attempts PowerDown and writes HCE zero without post-store queue confirmation. BL31's active-low device-reset helper is conditional. No same-boot reset, clock/power, resource, DMA drain, IOMMU or cache evidence was obtained.
- The isolated PHONE_CAPTURE/UFS_HANDOFF_PROBE v3 records PC, x0 and SHA-256 of the bounded incoming FDT and shows all 64 digest digits. A valid capture leaves blockers at 0xffef. DT declarations, a B hint and boot identity-like fields confer no grant. The offline DUCHUFS1 model now independently rechecks resource prerequisites and cache ownership against the authenticated receipt and existing lease.
- 12 passive diagnostic and 98 handoff format cases each pass in native ASan/UBSan and ARM64 QEMU. The 28 observer cases, 318 denials and revocations, four native races, bootshim host/payload/QEMU, static audit and staging checks pass. The existing CI 43631086106 kernel passed 11/11 fresh XNU QEMU runs, with nine blocked cases recording zero virtual UFS events.
- See docs/DUCHAMP_SLOT_B_TRUSTED_HANDOFF.md and docs/DUCHAMP_UFS_HARDWARE_VALIDATION_PLAN.md. Receipts and logs are in outputs/duchamp-trusted-boot-handoff-20261116. The proposed hardware experiment requires an authenticated or independently witnessed final BL31 and XNU entry from one actual Slot B boot and an independently verifiable resource authority. No phone access or physical changes occurred.

ACTIVE HANDOFF - MT6897 UFS handoff bound to the existing lease scope (2026-11-16)

- Extended the test-only DUCHUFS1 model to bind the candidate BL31/FDT digests and DMA route to the retained evidence for the existing gate lease. IOMMU receipts must also match the approved stream, domain and mapping epoch. A provenance callback that revokes the session skips the current-context sampler. The production gate and XNU staging are unchanged.
- 89 cases pass in each of native ASan/UBSan and ARM64 QEMU, with all 448 shorter lengths refused and a zero-event virtual UFS trace. Independent cross-route, IOMMU scope, evidence fingerprint and digest mismatch cases are covered. Existing bootshim host/payload/QEMU and gate/provider, DMA route, cache, snapshot, cold-init, handoff and staging suites pass.
- Fresh full-XNU QEMU passed 11/11 on the existing CI 43631086106 kernel. Read-only GPT/HFS+ boots reached diagnostic PID 1. The nine stopped cases had zero virtual UFS events. Commands, logs, traces and the repeated static reset-selector audit are in outputs/duchamp-ufs-ownership-dma-20261116.
- The reset-level role is established for the saved BL31 code. Same-boot Slot B ownership, resource continuity and fabric DMA drain remain unproven. There was no phone access, reboot, slot change, flashing, MMIO, DMA or partition write.

ACTIVE HANDOFF - MT6897 UFS ownership and DMA handoff validated offline (2026-11-15)

- Audited the pinned LK and BL31 again. In the saved BL31, both device-reset dispatch paths resolve to helper 0x44f84. The pinned Xiaomi client identifies 0x112b8090 bit 0 as device reset-level control, active low. The companion read is the HCI IP version register. No same-boot evidence of the electrical reset state, clocks, PHY, power or DMA drain was found.
- Added a test-only DUCHUFS1 parser and session validator under duchamp/drivers/model. Its fixed-size record requires independently authenticated provenance and live boot/sequence/lease/ownership scope. It checks separate queue, fabric drain, no-resume, DMA isolation, descriptor/cache and range evidence. Direct and IOMMU rules are distinct. Failure or revocation is terminal. It creates no grant and dispatches no I/O.
- 80 format cases pass in each of native ASan/UBSan and ARM64 QEMU, with all 448 shorter lengths rejected and zero virtual UFS events. The existing bootloader host/payload and eight QEMU entry cases, exact firmware audit, gate, route, cache, snapshot, staging and init regressions pass. Fresh full-XNU QEMU passes 11/11 on existing CI 43631086106, with nine stopped cases emitting zero UFS events.
- See docs/DUCHAMP_UFS_OWNERSHIP.md, docs/DUCHAMP_UFS_DMA_SAFETY.md and docs/DUCHAMP_UFS_HANDOFF_FORMAT.md. Commands, exit codes, logs and verified reset trace are in outputs/duchamp-ufs-ownership-dma-20261115. Physical UFS stays disabled. No phone access, flash, reboot, slot change, MMIO, DMA or partition writes occurred.

ACTIVE HANDOFF - MT6897 cold UFS initialization modeled offline (2026-11-15)

- Reverified pinned LK/BL31. LK writes AHIT/HCE zero and attempts device PowerDown with no final HCE/queue readback. The saved BL31 bootloader UFS service conditionally changes one AO syscon bit, distinct from published clock gates. No same-boot continuity, reset, PHY, DMA or MMIO grant follows.
- Prefer independent, exclusive cold initialization under a supported firmware/resource contract. Added a test-only state machine under duchamp/drivers/model using the existing gate and provider. It covers resources, power/clocks, PHY, quiescence, reset, DMA, IRQ, HCE and UIC readiness. Failures stop and quarantine after any potentially mutable step. No storage write or physical backend is exposed.
- All 67 model cases pass in native ASan/UBSan and ARM64 QEMU with identical output and zero virtual UFS events. The gate/provider, passive diagnostic, register snapshot, cache, DMA and staging regressions pass. Existing CI 43631086106 kernel passes 11 fresh QEMU cases. Two read-only boots reach PID 1 at 33.992 s and 33.914 s and nine stopped cases issue zero virtual UFS events. No new kernel was built.
- See docs/DUCHAMP_MT6897_UFS_INIT_DESIGN.md, docs/DUCHAMP_UFS_LK_SHUTDOWN_ANALYSIS.md and outputs/duchamp-mt6897-ufs-init-20261115. Physical UFS remains disabled pending a verified cold-init resource grant and safe DMA baseline. No phone access, slot switch, reboot, flash or partition write.

ACTIVE HANDOFF - Passive Slot B UFS handoff evidence audited and tested (2026-11-15)

- Re-ran pinned LK/BL31 analysis and verified the retained Fastboot log reports UFS/M-PHY initialization during firmware startup. It is distinct from the archived XNU Slot B boot. LK attempts shutdown before the BL31 callbacks. No record proves final power, clocks, PHY, ownership or non-secure read permission at XNU entry.
- Extended the isolated PHONE_CAPTURE/UFS_HANDOFF_PROBE with a version 2 RAM-only FDT record. It reports the slot hint, declared UFS dependencies and unproven rights. The saved Duchamp FDT shows no slot hint. All valid metadata captures leave blockers at 0x7ef. No physical grant producer or XNU mapping caller was added.
- Eight metadata cases each pass in native ASan/UBSan and bootshim QEMU. The observer passes 28 cases each in host/ARM64 QEMU, including wrong slots and stale epoch, 318 denial positions, 318 revocations and four native races. In four fresh regressions of the existing CI 43631086106 kernel, cold QEMU reaches read-only GPT/HFS+ PID 1 in 33.953 s and all three denials have zero maps, reads and virtual UFS events. No new full kernel was built.
- Details and next hardware procedure are in docs/DUCHAMP_SLOT_B_UFS_HANDOFF.md. Receipts and logs are in outputs/duchamp-slot-b-ufs-handoff-passive-20261115. Physical capture stays gated pending a trusted same-boot read and power/clock lifetime grant. No phone commands, reboot, flash, slot change, partition write or physical MMIO.

ACTIVE HANDOFF - Slot B UFS read authority unproven after live ADB check (2026-11-15)

- Verified Duchamp / MT6897 fully booted from Android A, with a matching hashed boot ID before and after capture. The Android UFS host and PHY drivers reported runtime-active.
- Read 128 KiB of the ATF runtime snapshot, a bounded 2 MiB raw ATF export, PL/LK and both pstore entries without a reboot or slot change. BL31 reported lts-v2.8.6(release):2fbca47. PL/LK had 142 UFS mentions. The scanned exports included no correlated Slot B XNU entry, non-secure read grant or power/bus-clock pin evidence. The archived LK shutdown attempt lacks HCE readback. Physical register read permission and duration of stable resources remain unproven.
- Re-ran 25 observer cases on native ASan/UBSan and standalone ARM64 QEMU, with 318 authority denials and 318 revocations apiece, four native races and an empty virtual UFS trace. No full XNU rebuild made in this pass. The prior full XNU/QEMU integration result supplies only synthetic authority.
- See duchamp/MT6897-UFS-OBSERVER-BINDING.md and outputs/duchamp-slot-b-ufs-read-authority-20261115/verification.json. The physical provider remains disabled. Before any physical queue capture, obtain a trusted same-boot grant for non-destructive reads and stable power/bus clocks until reset, or verified initialization that establishes the same contract. This run used ADB log/status reads only, with no physical MMIO, storage commands, flashing or partition change.

ACTIVE HANDOFF - HakiOS reference port and one-session XNU boot verified in QEMU (2026-11-15)

- Audited MT6768 ad65e1f4b3ba479e9d7ada98f17398b83cc6f285 and community MT6833 c24467f3074d9bfbd7cb92e2d20beacd91e468b5. Mapped all 770 device-reference files. The extracted MT6833 reader returned success with 0 bytes transferred. No hardware implementation was copied.
- Added devices/duchamp metadata checked by HakiOS main 63fc2b4633bac3af8e57dadab9f5a8d4cb940438, with unported drivers and runtime options off. The reproducible saved-DTB map documents reserved RAM and UNKNOWN ownership. The MT6768 XNU base overlaps Duchamp's TEE reservation.
- CI 43753027593 built complete XNU from isolated eb6cb0b61cb7030caff7958bf2e619c409f9249d with 324 pinned inputs. Kernel SHA-256 4176a10872a39839291f4783ccb0ae738e043a9da5db2c258412bc9f297af590. Native disassembly verifies dufs_inquiry binding. Seven MCQ cases pass. Standard INQUIRY identifies QEMU HARDDISK and read-only GPT/HFS+ reaches diagnostic PID 1 in 34.224 seconds with 34 completions and 28 READ(16)s. Legacy INQUIRY passes (33.847 s) and default-off MCQ reaches PID 1 (33.876 s). Missing handoff/DMA/cache and inherited queues remain blocked.
- Native ASan/UBSan and ARM64 QEMU each pass 131 UFS and 251 request-policy checks. Six menu cases and 13 one-shot cases pass. The QEMU shim calls the same bounded parser, consumes a wrapped request, verifies simulated A readback and enters real XNU once. Explicit host reset retains the consumed bytes and the B replay is refused. Wrong or missing readback blocks dispatch. A reentry is a model, so actual Android boot/automatic return remains unproven.
- QEMU-only review container: out/duchamp/hakios-port-final-20261115/duchamp-qemu-review-elf-verified.img, 8581120 bytes, SHA-256 5d7383baee906669d9c3b399875dff17aab236b5dbbb260937f024e096e82d3a. Raw/ELF equality and v4/LZ4 round trip verify. Modified loader rejected before generation.
- See docs/DUCHAMP_PORT_STATUS.md and outputs/duchamp-hakios-port-20261115 for 145 hashed files and receipts. No phone access, slot change, flashing or partition write. Before physical UFS capture, prove same-boot readable MMIO and stable power/clocks. Before commands, prove exclusive ownership, DMA and cache. Before binding physical boot selection, prove retained RAM, cache publication and the Android fallback.

ACTIVE HANDOFF - Read-only MT6897 observer verified inside complete XNU/QEMU (2026-11-14)

- Added a guarded QEMU-only caller of the real MT6897 read-only XNU adapter. It maps an ivshmem RAM bank carrying pinned MT6897 register offsets, then checks EL1 read/write translation without a store. This is not physical firmware authority or MT6897 device emulation. Physical capture stays disabled.
- Both affected Apple ARM64 objects compile with real XNU BSD headers. Ten backend-stage, nine UFS-stage and 29 profile tests pass. Staging now owns 33 files and includes the guarded emulator test. Main workflow compares the new staged module.
- CI 43631086106 succeeded from isolated source 7726168b844c7e00e24039cd93b8d0f4ed9a5e2d on codex/xnu-ufs-observer-full-20261114, with 324 pinned inputs, based on the previous successful full snapshot build. The full 16781120-byte kernel SHA-256 is c6ebb7330ad393f19637f759b2ee35b0e4b2e66ae4f22b7cfde90c3f64ade4f3. Artifact source/manifest/checksums and six native call edges through the actual adapter/mapper verify; no replay hooks.
- All 11 complete-kernel cases pass. Cold capture performs 316 loads/318 authority checks, then read-only GPT/HFS+ reaches diagnostic PID 1 in 34.122 host seconds. Default-off also reaches PID 1 in 34.161 seconds. Both verify file bytes and EROFS. Nine denied/inherited/profile cases leave the separate virtual-UFS trace entirely empty. Revocation during reads stops at 98 loads; revocation after all 316 loads discards output. Queue 7 pending at SQ head/tail 0/32 is reported with flags 0x39. All RAM banks and the GPT disk remain unchanged.
- The four mapped cases use the real ml_io_map_with_prot(..., VM_PROT_READ), not the standalone mapping shim. AT S1E1R resolves to model PA 0x112b0000 (PAR 0x112b0b00); AT S1E1W faults (PAR 0x81f), without attempting a store. This is virtual page-protection proof, not MT6897 power/firewall/DMA/cache proof.
- Fixed a host-checker assertion requiring an early framebuffer-only ID mark that had scrolled away before denial. The observer kernel-log ID instead comes from the accepted same-boot handoff getter. Rechecking saved runs validates exact payload/ADT/mailbox/model bytes without changing guests. Fresh end-to-end cold/disabled reruns also pass after the correction (PID 1 in 34.084 seconds). The initial checker failure is retained with the evidence; no kernel fix was needed.
- The 151 hashed evidence files and archive.json are in outputs/duchamp-ufs-observer-xnu-full-20261114. Native disassembly, CI receipts, all logs/traces, RAM banks and pid1.png are included. Preparation/download/reproduction helpers and the selected kernel remain in work/ci-xnu-ufs-observer-full-20261114. Contract/results are in duchamp/MT6897-UFS-OBSERVER-BINDING.md.
- No phone commands, reboot, slot switch, flashing or partition modifications. Physical capture still needs a trusted same-boot read-access and power/bus-clock-pinned authority from verified initialization or a documented handoff. No physical producer was added; physical UFS/DMA/cache remain unproven. Preserve the user's existing changes, particularly the long unrelated NOTES diff, qemu-sweet.py and mt6897_firmware.c.

ACTIVE HANDOFF - MT6897 read-only observer binding tested, physical authority missing (2026-11-14)

- Added `duchamp/drivers/mt6897_ufs_observer.c/h` and `duchamp/xnu/mt6897_ufs_observer_xnu.c/h`. This one-shot sidecar binds the snapshot to the MT6897 HCI window without requiring or creating a DMA/cache/storage activation lease. A trusted internal authority must prove exact-boot read access, power/bus-clock stability, non-secure access, non-destructive reads and pins until reset. No producer, ADT parser, boot-arg enable or automatic physical caller was installed.
- The XNU adapter requests a permanent Device mapping with `ml_io_map_with_prot(..., VM_PROT_READ)` and uses bounded 32-bit volatile loads plus `dsb ld`. It imports no SMC, DMA/cache or storage executor. The private mapper prototype is omitted from BSD exports; its explicit declaration matches the full ARM64 source/header, and the symbol exists in the prior complete kernel. `ml_probe_read` panics and `ml_nofault_copy` does not provide MMIO fault recovery, so neither is used.
- Atomic transitions authorize each mapping/load and final publication. Failed or revoked capture leaves output unchanged and latches a fault. Rebinding/concurrent capture are refused. Already authorized callbacks may finish under the boot-lifetime pins; revocation before publication discards their data. The mapping is deliberately retained until reset. This is a diagnostic lifecycle, not production power management or a storage transport.
- All 25 cases, 318 authority-denial positions and 318 revocation positions passed under host ASan/UBSan and standalone ARM64 QEMU. Four deterministic native pthread races passed, including one already authorized load and a full capture revoked before publication. The tests use synthetic grants and a RAM mapping shim; VM_PROT_READ requests are checked, not physical MMU protection. The unrelated QEMU UFS trace is empty. Two Apple ARM64 objects compiled with real XNU BSD headers/commands. No full kernel was rebuilt or booted for this binding.
- Backend staging now includes 32 files. All 10 backend-stage, 9 UFS-stage and 29 profile checks pass. The new observer source/header is protected against overwriting pre-existing or modified staged files. The workflow compares the staged XNU adapter. No unrelated files or the previous complete kernel were changed.
- `outputs/duchamp-ufs-observer-binding-20261114/verification.json` records source/binary/log hashes, cases, imports and the saved-evidence audit. Reproduction and contract details are in `duchamp/MT6897-UFS-OBSERVER-BINDING.md`. The saved resource capture is Android A data from November 12, with XNU delegation unproven; it supplies no read-access/power pin at XNU entry. `xnu_read_grant_proven=false`, `physical_capture_allowed=false`.
- No phone command, physical register access, reboot, slot change, SMC, DMA/storage command, flashing or partition modification. Actual queue capture remains pending a trusted same-boot access/power-pinned authority from verified platform initialization or a documented handoff. Do not infer it from Linux active state or model success. Before phone use, validate the producer and complete the new kernel integration test. Preserve all prior user changes.

ACTIVE HANDOFF - Passive UFS observer verified in full XNU/QEMU (CI 2026-11-12)

- Implemented `duchamp/drivers/ufs_register_snapshot.c/h`, with separately pinned MT6897 and QEMU runtime layouts. It reads two bounded snapshots, rechecks boot-scoped read permission before each read, flags inherited/pending/changed queues and never follows inherited DMA pointers. It has no controller-write, DMA or command interface and supplies no ownership/cache grant.
- All 30 register-array cases, 316 injected read failures and 316 permission-revocation positions passed under native ASan/UBSan and standalone ARM64 QEMU. A separate real QEMU PCI UFS capture records 632 reads and zero observer writes/SCSI commands. Exactly eight intervening fixture writes enable inherited MCQ queues, which the observer identifies. Different-boot permission denies before any read. Reports are in `outputs/duchamp-ufs-passive-snapshot-20261112`.
- Staged the observer in the XNU BSD build list and added opt-in `sweet-qemu-ufs-snapshot=1` to the virtual root adapter. It captures before DMA allocation and PCI bus-master enable, then refuses if capture fails or flags are nonzero. Its permission callback uses the existing synthetic handoff's boot ID without logging per-read. The physical root selector remains disabled; no phone mapping or reader was added. Reviewed XNU `ml_probe_read[_64]` is an unconditional panic and cannot be used as a protected physical probe.
- All four affected C sources compile with the real XNU command-line/header configuration. UFS staging has 9 passing tests, backend staging 8 and profile tests 29. The transport-only MCQ replay remains byte-identical at SHA-256 `5ed792c0052a6d791eb24dda3d87fd33c37bde4b98d41a3c480678658eb57a42`.
- Full-source macOS Actions run **43301119194** succeeded from isolated ref `codex/xnu-ufs-snapshot-20261112`, source **2d554f207c46f248da26b6d23bad97e3f74a8676**, with 319 pinned inputs. The 16780440-byte kernel SHA-256 is **16616409bcca4ba4ea478f781e82267768f5ef457ffaebe886ae80f875014f50**. Native disassembly confirms `qu_prepare -> qu_snapshot -> dufs_snapshot_registers`. All seven MCQ cases pass without replay hooks. The read-only GPT/HFS+ root reaches diagnostic PID 1 in 34.035 host seconds, with 316 initial passive reads, 33 MCQ completions and 28 READ(16) commands. Default mode also reaches PID 1 in 33.838 seconds.
- The independent full-XNU test enables empty MCQ queues with QTest while its synthetic handoff claims cold queues. XNU detects flags `0x29`, refuses preparation after 316 reads, emits zero HCI writes/SCSI commands and leaves the output block zero. A host read after rejection confirms PCI command 2, with bus mastering off. Missing grants/inherited-mode records yield empty HCI traces; invalid pool DMA and missing SQ synchronization refuse submission; the device-side DMA fault times out after one submission/no SCSI. Cache grants and BL31 are synthetic, not physical proof.
- Framebuffer scrolling hid the new marker, so `tools/qemu_kernel_log.py` captures the stopped guest's circular log using QMP virtual-memory `memsave`. It never patches the guest or changes the user's existing runner/session. The main `tools/qemu-sweet.py` edits were preserved. An initial selected factory B backup was all zero; tests instead use a separately recorded, hash-verified previous QEMU-only v4 container padded as a header fixture. It is not an installed B backup or flashable phone image.
- The 95 hashed evidence files and `archive.json` are in `outputs/duchamp-ufs-snapshot-xnu-full-20261112`; the million-event injected DMA-fault trace is compressed with its original digest recorded. CI inputs, native objects, selected kernel, reproduction helpers and scratch location are in `work/ci-xnu-ufs-snapshot-20261112`. Complete details are in `duchamp/UFS-PASSIVE-SNAPSHOT.md`.
- No phone commands, reboot, slot change, firmware calls, flashing or partition writes. Physical UFS remains unproven. Next implement a physical MT6897 read-only binding only after documenting accessible/powered MMIO at XNU entry, then capture real queue state. Storage commands additionally require exclusive resources, PA-to-DMA and cache ownership; a documented initialization contract or verified handoff can supply evidence. Preserve all unrelated user modifications.

ACTIVE HANDOFF - Live Android UFS reference verified, physical XNU adapter pending (2026-11-12)

- Read-only ADB found rooted Duchamp/MT6897 on Android Slot A with the same boot-ID hash as the earlier Android capture. Three O_DIRECT reads of 4096 bytes passed: LUN 2 / LBA 276480, the corresponding vendor_boot_a partition header, then the LUN read again. All returned SHA-256 `065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6`. Raw block bytes were discarded.
- The current Android host reports HCCAP `0x55c7051f`, eight MCQ queues and the expected UFS IRQ mapping. Three UFS interrupts occurred between the direct-read snapshots. Background Android activity prevents an exclusive workload-causality claim. Provider bindings and supplies were captured through Linux interfaces without direct MMIO.
- Rehashed both installed LK slots to the saved `f85373d3...5ba957a` audit input. The reviewed registry has no fastboot RAM-launch command. Live CONFIG_KEXEC and CONFIG_KEXEC_FILE are disabled. Android stayed on A throughout, with no reboot or slot change.
- Source review identifies an implementation gap beyond firmware logging. The current MCQ adapter targets QEMU PCI/Cortex-A76, and the physical `mt6897` root selector still returns `kIOReturnUnsupported`. The physical provider exposes a guarded dispatch interface without hardware operations. Implementing that adapter and establishing its same-boot controller/queue, DMA/cache and resource contract remain required. Acceptable evidence can use a documented initialization contract, verified XNU-side observation, or a vendor BL31 record.
- Corrected the resource-binding collector's requirement that UFS/PHY always stay active. It now records valid runtime-PM transitions while retaining false XNU grants. All six collector tests passed, and the live capture succeeded. Revalidated the saved November 4 PRDT observations offline without loading a module. Those historical DMA observations are not a fresh XNU contract.
- The evidence archive is `outputs/duchamp-physical-ufs-20261112-v2`. Reproduction scripts and raw read-only runtime captures are in `work/duchamp-physical-ufs-20261112-v2`. Physical UFS reads in this session were issued by Android's driver. No XNU UFS read, module loading, explicit firmware call, direct MMIO, flashing or partition write was performed.

ACTIVE HANDOFF - Full-source XNU MCQ passed GPT boot and fault isolation (2026-11-12)

- Integrated `duchamp/xnu/qemu_ufs_mcq.c` with the virtual root driver and the XNU BSD staging list. The module uses the established SWEET board guard, and the adapter explicitly maps the MCQ runtime register extent. The default legacy path remains selectable by omitting the MCQ boot argument.
- macOS Actions run 43290848980 succeeded at isolated source `3879b4b380112de3fab4987cb216c139423e17d2` on ref `codex/xnu-ufs-mcq-20261112`, derived from successful CI 43115466836. The artifact matches all 317 source-input hashes and the pinned IIG archive. Its complete 16780176-byte Mach-O SHA-256 is `6f471df61fceb79fade40d7d5248621837d5484ded3c7690e2061f11069e10c8`. Native disassembly confirms the normal root driver's call to `dufs_mcq_bind()`. No replay hooks were applied.
- All seven full-kernel MCQ cases passed. The read-only GPT/HFS+ root reached diagnostic PID 1 in 33.936 host seconds with 33 SQ submissions/CQ completions and 28 READ(16) commands. An independent check matched eight ring wraps. PID 1 verified file bytes and EROFS write-open rejection. The same kernel also reached PID 1 in legacy mode in 33.887 seconds. The source GPT and archived Slot B image remained byte-identical.
- Invalid DMA and missing SQ sync were refused before submission. The device-side UCD fault produced one SQ submission, one QEMU DMA error, zero SCSI commands and a bounded timeout. Missing DMA/cache grants and inherited MCQ each left the UFS trace empty. These expected negative-root cases end in a root-unavailable panic. BL31 records and non-coherent cache visibility remain simulated. Physical MT6897 resource/cache ownership is unverified.
- All 7 UFS staging tests, 8 backend staging tests and 29 profile tests pass. Corrected two outdated backend-test expectations for the probe source count and separately staged SPI2 sources. Apple ARM64 compilation passes, and the retained replay still produces its previous verified binary. The full-build verifier rejects a wrong hash or an older kernel without MCQ.
- CI inputs, the selected full kernel and preparation scripts are in `work/ci-xnu-ufs-mcq-20261112`. The 83-file evidence archive is `outputs/duchamp-xnu-mcq-full-20261112`, including native binding, the seven traces, legacy regression and `pid1.png`. No phone access or partition changes.

ACTIVE HANDOFF - QEMU MCQ boots the GPT root and rejects DMA/cache faults (2026-11-12)

- Added the isolated MCQ transport in `duchamp/xnu/qemu_ufs_mcq_replay.c` and `tools/test-duchamp-ufs-mcq-xnu.py`. The source-checked MT6897 model supplies the eight-queue capacity and synthetic cold handoff. QEMU executes a four-entry SQ/CQ pair on queue 0 using its own register layout. The default virtual UFS profile retains legacy mode.
- All seven XNU/QEMU cases passed. The GPT/HFS+ root reached diagnostic PID 1 in 33.890 host seconds with 33 MCQ submissions/completions and 28 READ(16) commands. SQ/CQ offsets matched through eight wraps. PID 1 verified the file bytes and EROFS write-open rejection. The GPT disk SHA-256 stayed `9a74c16529b51a06bcc843e73184ae669a5670808a4e85db7c532db578be74e1`.
- Invalid owned-pool DMA and missing SQ sync each produced zero SQ submissions/SCSI commands. An explicit device-side UCD fault produced one SQ submission, one QEMU DMA-read error, no completions/SCSI commands and a bounded XNU timeout. Missing DMA/cache grants and inherited MCQ each left the entire UFS trace empty. Negative root selection ends in an expected root-unavailable panic. The legacy regression also reached PID 1, and all 29 host profile checks passed.
- This uses a 1632-byte locally compiled transport linked into checked gaps of the CI 43115466836 kernel, with one checked root-driver call-site hook. Replay SHA-256 is `5ed792c0052a6d791eb24dda3d87fd33c37bde4b98d41a3c480678658eb57a42`. A full source rebuild with MCQ is the next verification. The cache omission is an injected contract failure under coherent QEMU TCG. Physical MT6897 cache/resource ownership remains unverified.
- Reports, traces, local images and `pid1.png` are in `outputs/duchamp-mt6897-ufs-mcq-20261112/verified`. The source/command details are in `duchamp/QEMU-UFS-XNU.md`. No phone access or partition changes.

ACTIVE HANDOFF - MT6897 UFS model supplies the Slot B GPT test (2026-11-12)

- Added `tools/mt6897_ufs_model.py`. The pinned Duchamp DTB provides the UFS HCI, IRQs and identity DMA aperture, and the pinned Xiaomi UFS source provides MCQ register offsets, stride and permission policy. The model runs legacy and MCQ queue drain checks and verifies that the PRDT and data stay stale until the appropriate sync. An out-of-window DMA address is rejected.
- With `--mt6897-sources`, the Slot B verifier passes modeled handoffs to full XNU from CI 43115466836. The legacy case mounts the read-only GPT/HFS+ root and reaches diagnostic PID 1. The eight denials leave the virtual UFS trace empty, including an outstanding task and a drained MCQ state. Reports and image are under `outputs/duchamp-mt6897-ufs-model-20261112`.
- The 27 host UFS profile checks, 560 native/ARM64 cache checks and 791 native/ARM64 DMA-route checks passed. QEMU uses its legacy PCI UFS device. The new software model does not establish physical MT6897 resource or cache ownership. No phone access or partition changes.

ACTIVE HANDOFF - HakiOS storage split verified from a Slot B image to PID 1 in QEMU (2026-11-12)

- Reviewed HakiOS Infinix Hot 20 at `ad65e1f4`. Its LK chainloader and BSD block device use MSDC/eMMC PIO and read the GPT system partition on demand. The MT6833 example at `c24467f3` shows QEMU/rd=md0, and its sector routine does not return data. The comparison and pinned source links are in `duchamp/QEMU-UFS-XNU.md`.
- Added `--gpt-fixture` to the existing Slot B image verifier. Full XNU from CI 43115466836 booted from the image's extracted ARM64 bootshim with a runtime synthetic handoff, mounted the HFS+ GPT slice via qufs0 without a RAM root, read a known file in diagnostic PID 1, refused write-open with EROFS and reached the heartbeat. Six rejected records left the UFS trace empty. The image and receipts are under `outputs/duchamp-slot-b-gpt-root-20261112`.
- All 27 host UFS profile checks passed. No device access or partition writes. Physical MT6897 UFS remains gated by the separate resource, DMA and cache handoff evidence.

ACTIVE HANDOFF - Public Duchamp BL31 channels reviewed against the Slot B receiver (2026-11-12)

- Verified MiCode `3c4ccd07` and the pinned Android FDT. The four-byte `atag,ufs` describes RPMB key state. `GET_MCQ_EN` supplies MCQ policy. `/proc/ufs_debug` traces the Android UFS host after its initialization. The ATF snapshot copies an existing ring, and the SLC parity interface provides no UFS cache grant.
- Re-ran the saved LK and BL31 binary audit and passed all 22 LK, BL31 identity and resource-ownership checks. A vendor-published final-exit record must bind the XNU digest and fresh Slot B boot ID to drained queues, effective DMA delegation and the system-cache maintenance owner. Documented the existing `x0` FDT as a possible carrier for a separate vendor-defined reserved RAM record in `duchamp/MT6897-LK-HANDOFF-CONTRACT.md`.
- The audit is in `outputs/duchamp-bl31-vendor-channel-20261112`. No vendor ABI or same-boot sample was found for the installed firmware. The physical UFS gate remains closed. No device commands, reboot, slot change, flash or partition writes.

ACTIVE HANDOFF - Slot B image receives a BL31 handoff in QEMU (2026-11-12)

- The isolated QEMU_BL31_RECEIVER profile boots an ARM64 Image extracted from a separately repacked Android v4/LZ4 Slot B container. The shim reads the synthetic mailbox at 0x49000000 and injects the independent boot-entry ID and 64-byte record into the materialized boot args and /chosen ADT property. The archived boot_b.img is hash-checked before and after. The repack has no AVB footer and the shim requires the emulator addresses and Cortex-A76 MIDR.
- The full XNU kernel from CI 43115466836 logged both IDs. One accepted case read 4096 bytes via READ(16) on virtual LUN 2 / LBA 276480 and matched Android SHA-256 065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6. Six cases produced no UFS MMIO or SCSI events: a different ID, missing record, missing queue evidence, a pending queue, missing DMA grant and missing cache evidence. The 27 host UFS profile tests passed.
- Build and per-case evidence are in outputs/duchamp-slot-b-bl31-receiver-20261112. tools/test-duchamp-slot-b-handoff.py recreates the container and runs the matrix. The existing explicit framebuffer-field copy in loader/plan.c is required by the freestanding link to avoid an unresolved memcpy. The phone was not accessed. Physical UFS still needs a documented producer of the final-exit record on the same Slot B boot.

ACTIVE HANDOFF - Firmware and XNU UFS block digests match in one QEMU boot (2026-11-12)

- Added a HakiOS-style comparison to tools/test-duchamp-ufs-probe-xnu.py. Before starting XNU, QTest acts as the firmware and sends one READ(16) for LUN 2 / LBA 276480 on the same read-only virtual UFS device. It verifies completion and hashes the 4096 bytes returned into guest RAM by UFS DMA.
- Boot ID 0x7a25e7ed54de4d82 appears in the QTest receipt and both XNU entry fields. At handoff HCE, UTRLDBR, UTRLRSR, UTMRLDBR and UTMRLRSR all read zero. The measured legacy queue state matches the synthetic ADT record.
- XNU from CI 43115466836 sends its own READ(16) for the same block. Both SHA-256 digests match the saved Android reference. All twelve XNU/QEMU cases and 27 host profile tests passed. The separately captured firmware and XNU traces are in outputs/duchamp-ufs-firmware-xnu-compare-20261112. No phone access or partition writes.

ACTIVE HANDOFF - Physical Slot B UFS prerequisites rechecked (2026-11-12)

- Read-only ADB found the same Duchamp Android A boot before and after capture. The ATF raw and snapshot, PL/LK and bootprof hashes all match the previous Android A capture, and pstore is empty. Reverified the archived Slot B photo and LK/pstore hashes. That XNU image boots md0 and has no handoff receiver. No available record binds the observed firmware to that XNU entry or establishes queue drain, DMA delegation or the cache maintenance owner.
- Reverified the saved Android backup and its 4096-byte reference for LUN 2 / LBA 276480 against the matching QEMU result. The physical read remains gated. The new receipt is outputs/duchamp-slot-b-ufs-conditions-20261112/verification.json. No reboot, slot switch, flash or partition write.
- After the firmware/XNU QEMU comparison, a fresh ADB check matched the same Android A boot and identical ATF export hashes. Pstore was empty. The archived B image still lacks the handoff receiver. The physical comparison did not start. See outputs/duchamp-slot-b-physical-compare-20261112/verification.json.

ACTIVE HANDOFF - XNU rejects a pending inherited UFS request in QEMU (2026-11-12)

- QTest configured a live legacy UFS list on the read-only LUN, consumed power-on UNIT ATTENTION with TEST UNIT READY and submitted one firmware READ(16) to LUN 2 / LBA 276480. QEMU blkdebug held the real request across guest boot.
- The pinned XNU from CI 43115466836 admitted the synthetic handoff and rejected initialization with provider status -5. At the XNU stop loop, QTest read UTRLDBR=1 and OCS=0xf. The guest-only trace contains one HCI read (HCE=1), zero HCI writes and zero new SCSI commands. PCI mapping writes occur separately.
- The host resumed the original request after recording the refusal and confirmed UTRLDBR=0 and OCS=0. All eleven XNU/QEMU cases and 27 host profile tests passed. The full trace separates firmware submission, XNU and the host's final readback. Evidence is in outputs/duchamp-ufs-inherited-pending-20261112. No phone access or partition writes.

ACTIVE HANDOFF - XNU rejects a running inherited UFS list in QEMU (2026-11-12)

- Added a QTest fixture to tools/test-duchamp-ufs-probe-xnu.py. While the ARM64 guest is paused, it starts the emulated legacy HCI and configures a running transfer list with no pending request. Readback shows HCE=1, UTRLRSR=1, UTRLBA=0x60000000 and UTRLDBR=0.
- The full XNU artifact from CI 43115466836 admitted the synthetic handoff, mapped the PCI BAR and rejected initialization with provider status -5. After the separately verified fixture trace, XNU made exactly one HCI read (HCE=1), zero HCI writes and zero SCSI commands. The output buffer stayed zero.
- All ten XNU/QEMU cases and 27 host profile tests passed. The cold control still read 4096 bytes and matched the Android reference. The experiment used a read-only virtual disk and did not access the phone or its partitions. Results and traces are in outputs/duchamp-ufs-inherited-controller-20261112.

ACTIVE HANDOFF - QEMU UFS replay and live BL31 correlation recheck (2026-11-12)

- Replayed all nine QEMU cases with the SHA-256-pinned full XNU artifact from CI 43115466836. The matching synthetic handoff issued one READ(16) for LUN 2 / LBA 276480, read 4096 bytes and matched the Android reference. A one-byte alteration changed the digest. All seven denials had zero controller events.
- Read-only ADB confirmed the same Android A boot before and after the capture. ATF raw (2097152 bytes), runtime snapshot (131072 bytes), PL/LK and bootprof all matched their prior Android A hashes. Parsed the vendor buffer headers and verified that the runtime snapshot is byte-for-byte the RUNTIME_LOG body of the raw export. Pstore was empty and last_kmsg was unavailable.
- Rechecked the archived Slot B trial, PL/LK log and pstore slices. The LK reference to boot_b is a partition listing. The trial image lacks the handoff receiver, and the available records have no correlated BL31-to-XNU entry, queue drain, DMA grant or cache owner. A vendor-supported final-exit record with a matching XNU boot identifier remains the physical UFS prerequisite.
- Reports and the matching QEMU traces are in outputs/duchamp-bringup-recheck-20261112. No reboot, slot change, flash, partition write, direct MMIO or physical UFS read.

ACTIVE HANDOFF - Live Android A ATF logs checked for Slot B XNU (2026-11-12)

- ADB identified Duchamp running Android V816.0.17.0.UNLMIXM on A. The Android boot ID hash and slot agreed before and after the read-only capture. ATF raw returned 2097152 bytes and runtime_snapshot returned 131072. Both showed BL31 lts-v2.8.6(release):2fbca47. PL/LK and bootprof also read successfully. Pstore was empty and last_kmsg was unreadable.
- No captured log contained an XNU entry, a correlatable Slot B boot ID or evidence of queue drain and DMA/cache delegation. The report is under outputs/duchamp-slot-b-live-adb-20261112. Raw log contents were not retained. No reboot, slot switch, flash, partition write or physical UFS probe.

ACTIVE HANDOFF - Slot B BL31 capture attempt (2026-11-12)

- Windows reported no ADB or Fastboot devices, no matching Xiaomi/MediaTek/Android USB interface and no present serial ports. No capture could be acquired from the phone. The saved Slot B launchd receipt has no boot identifier for BL31 correlation. The audited Slot B image uses md0 and has no handoff receiver.
- The saved 2 MiB ATF export came from Android Slot A and contains no Slot B/XNU or UFS queue/cache handoff markers. Rechecked the public runtime_snapshot reader, which copies the existing runtime buffer. A documented firmware trace and matching XNU entry from one Slot B boot are still needed to establish queue drain, DMA delegation and cache ownership. No physical UFS command, reboot, flash or partition write occurred.

ACTIVE HANDOFF - Full XNU verifies the MT6897 one-block probe in QEMU (2026-11-12)

- macOS CI run 43115466836 built DEVELOPMENT SWEET at 9db1c1580e41173aa37229ad358797f8b75efc9e from 059b84b plus the opt-in QEMU call site and same-boot synthetic lease bridge. The unchanged artifact SHA-256 is 57ba8b32dd1b7a5ed7c70ed65d7a4aec107d12b85147f236c439cd309672fda0.
- The matching proof issued one READ(16), LUN 2 LBA 276480, length 4096. The XNU BSD log and independent hash of its guest RAM buffer both matched the saved Android digest 065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6. A one-byte change produced a different digest.
- Seven denials had no controller MMIO or SCSI events and left the output zeroed. The same kernel booted the normal read-only qufs0 GPT root to PID 1. All 27 host profile tests passed. Evidence is under outputs/duchamp-ufs-probe-full-xnu-20261112. The handoff is synthetic. No phone commands or partition changes.

ACTIVE HANDOFF - MT6897 one-block UFS probe wired through the provider (2026-11-12)

- Added the one-shot read-only adapter in duchamp/drivers/mt6897_ufs_probe.c. The provider validates its lease before the prepare callback, then the adapter uses the existing UFS core to read exactly 4096 bytes from LUN 2 LBA 276480. Failed authorization leaves the destination untouched. Included the adapter in XNU source staging and compiled the staged ARM64 Mach-O object.
- ARM64 QEMU confirmed one SCSI READ(16) on the read-only virtual device with synthetic handoff evidence. All 20 refusals had zero PCI, MMIO, DMA or read callbacks, including a lease revoked after bind. The UFS polling model passed 79 checks each natively and in ARM64 QEMU. Separate QEMU qtest with the saved vendor_boot_a backup passed 27 checks and matched the Android digest. A one-byte change was detected.
- Logs are under outputs/duchamp-mt6897-ufs-probe-20261112-verified. The same-boot Slot B queue, DMA and cache evidence is still absent. The adapter requires a verified platform transport. No new full XNU build or phone access, flash or partition changes.

ACTIVE HANDOFF - Duchamp vendor UFS handoff diagnostics (2026-11-12)

- Reviewed the published MiCode tfa_debug driver. runtime_snapshot reads a subrange of raw_dump_all and does not take a controller sample. Found no public final-exit UFS trace producer for the observed BL31 lts-v2.8.6(release):2fbca47 on the audited V816.0.17.0.UNLMIXM release.
- Prepared a request for Xiaomi firmware engineering for a supported read-only trace with the shared Slot B boot identifier, drained queues and DMA/cache ownership. Xiaomi Global Support is the public intake and MediaTek Online directs technical questions through the company representative. No request was sent and no phone commands were issued.

ACTIVE HANDOFF - Full XNU build passes all seven QEMU UFS handoff cases (2026-11-12)

- Built XNU DEVELOPMENT SWEET on macOS CI run 43105108152, isolated commit 99513047545793c352596c5807ab774f0efa8690. The 314 pinned build inputs match duchamp-bootstrap 3bf3e12. Replaced the expired IIG artifact with retained 13714817484 after matching all 39 input and 34 generated-output hashes.
- Booted the verified Mach-O SHA-256 0b2397db58d8fd59a406ee00efcef572c0fee62f1be3d248b039c2e7427c35f1 directly, without replay hooks. GDB paused arm_init on return from the compiled handoff call and captured both boot IDs and the verdict from the stage-2 framebuffer in each of seven separate entry checks.
- The matching boot reached PID 1 and verified reads through qufs0 on unchanged read-only GPT media. Each of six denials stopped with EPERM before virtual UFS access. Different boot, missing BL31, missing queues, busy queue, missing DMA and missing cache produced zero controller MMIO/SCSI events. Logs are under outputs/duchamp-ufs-handoff-full-build-20261112.
- Physical UFS still requires a documented BL31 final-exit record from the same Slot B boot as XNU, with queue drain and explicit DMA/cache ownership. All records used here were synthetic. No phone access or partition changes.

ACTIVE HANDOFF - Actual XNU entry correlates the virtual UFS handoff (2026-11-12)

- Added the opt-in sweet-qemu-ufs-handoff profile. arm_init captures its independent boot ID after early PE initialization and compares it with the synthetic BL31 ADT record. XNU logs both IDs at entry and reprints the saved decision before qufs0. The gate requires observed legacy queue drain and DMA/cache grants before the adapter reaches PCI mapping.
- Full CI XNU from run 42707402072 was reused as the pinned base. The local replay linked the new source into a separate kernel copy through two checked ARM64 hooks. All three staged production translation units compiled to arm64 Mach-O objects and the full kernel was not rebuilt. QEMU/GDB captured the XNU stage-2 line at the return from the entry hook.
- All seven QEMU boots passed. The matching pair reached PID 1 and verified reads from the unchanged read-only GPT disk. Different boot ID, missing BL31, missing queue evidence, busy queue, missing DMA, and missing cache each stopped at the expected EPERM root failure with an empty UFS MMIO/SCSI trace. The existing QEMU UFS profile without the opt-in also passed. Evidence is under outputs/duchamp-ufs-handoff-xnu-20261112. No phone access or physical authorization.

ACTIVE HANDOFF - Same-boot BL31/XNU correlation blocks UFS reads in QEMU (2026-11-11)

- Added tools/test-duchamp-ufs-handoff-qemu.py and a standalone AArch64 test linked to the existing MT6897 UFS gate/provider and read-only transport. Synthetic BL31 and XNU records are checked against the current boot generation and image identity, final-exit and controller samples, legacy or complete MCQ drain evidence, and explicit resource, DMA and cache grants. No production firmware or phone image was changed.
- All 19 negative cases denied the lease. In each case all six provider operations were blocked and the PCI, MMIO, DMA and read counters stayed at zero. The matching control issued one READ(16) for LUN 2 LBA 276480 against a read-only synthetic image on QEMU virt, matched all 4096 bytes, and left the image hash unchanged. The QEMU controller trace confirmed the opcode, LUN and LBA. Native and ARM64 gate regressions passed 708 checks each and the ARM64 provider passed 107. The physical gate still denied access.
- Evidence is under outputs/duchamp-ufs-handoff-qemu-20261111. The test uses synthetic records and media. The BL31 producer and correlated XNU entry on physical Slot B remain unverified. No phone access, flash or partition changes.

ACTIVE HANDOFF - Installed Slot B image audited for same-boot UFS evidence (2026-11-11)

- Read-only ADB on Android A rehashed boot_b, vendor_boot_b, init_boot_b and lk_b. They match the archived service image and supporting firmware. Unwrapping the matching boot_b yielded the pinned XNU image with rd=md0, a 32 MiB embedded root and no UFS node or handoff receiver. The exact unmodified image reached the XNU framebuffer marker in QEMU with 7 GiB.
- The exact installed LK's 35-entry Fastboot registry offers no documented RAM launch. Android reports both kexec options disabled. The standalone UFS receiver rebuilt to the archived SHA-256 and recorded blockers=0xf on both QEMU-generated and saved Duchamp FDTs. Twenty-five local audit and ownership tests passed. The last live ATF export is from Android A and supplies no evidence tied to a B/XNU boot.
- A vendor-supported record after final BL31 platform work and a correlated XNU entry record are still missing. Physical read of LUN 2 LBA 276480 remains pending. Phone stayed on Android A with no reboot, slot switch, flash, partition write, direct MMIO or firmware calls. Evidence is under outputs/duchamp-slot-b-handoff-audit-20261111.

ACTIVE HANDOFF - Live Duchamp UFS GPT has no dedicated Setup space (2026-11-11)

- Verified from stock Android V816.0.17.0.UNLMIXM on A via read-only ADB. The 4 KiB primary and backup GPT headers and entry tables on LUN 2 passed CRC and matched each other and all 90 sysfs partition geometries. The entries cover every usable LBA from 8 through 129155063. LUNs 0 and 1 expose 4 MiB each. Only Android super and shared userdata fit the 3.125 GiB Setup image. Both GPT headers have a zero disk GUID, while all 90 partition GUIDs are nonzero. The current QEMU UFS parser rejected a synthetic 4 KiB GPT with this single variation after recomputing CRCs. All 85 control and rejection checks passed.
- Re-read 4 KiB from vendor_boot_a via the partition node and LUN 2 LBA 276480. Both matched the saved Android digest 065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6. The isolated QEMU known-block test passed 27 checks. The captured bytes serve only as a reference and were not retained.
- The installed atf_logger module registers /proc/atf_log/raw_dump_all with raw_open/raw_read/raw_release. The live export returned 2 MiB and contained BL31 banners but no matching XNU/Slot B, UFS, queue, or cache ownership markers. Current Android boot identity stayed the same throughout the capture. Same-boot queue state and UFS resource, DMA and system-cache delegation to XNU remain unproved. The local physical gate still denied access with zero hardware, MMIO, DMA and SMC dispatches. No reboot, slot change, partition write or physical UFS command from XNU. Reports and replay scripts are under outputs/duchamp-ufs-layout-20261111.

ACTIVE HANDOFF - Read-only Setup root verified on 4 KiB GPT through QEMU UFS (2026-11-11)

- Booted the pinned 20F66 HFS+ root, 3,355,443,200 bytes, from a dedicated GPT partition at LBA 256 through qufs0 on emulated UFS. The GPT and emulated controller both used 4,096-byte sectors. XNU CI 42707402072 mounted the root read-only and used a separate 64 MiB md0 for /private/var. The guest process list confirmed launchd PID 1. Setup PID 63 connected to BackBoard. Hello and the language list both passed six framebuffer checks with IOSurface 5 at SwapEnd 157 and 368 respectively. Stopped after 306.195 host seconds without a kernel panic.
- The entire disk and the adjacent synthetic non-HFS partition retained their SHA-256 hashes. The portable controller checks passed 45/45 against the same image and rejected a read crossing into the next partition before transport. QEMU profile and resource ownership tests passed 26/26 and 9/9. The pinned MT6897 gate denied physical access with zero hardware, MMIO, SMC and DMA calls.
- Replay, logs and screenshots are in outputs/duchamp-setup-ufs-gpt4k-20261111. The large local test disk remains in WSL, outside Git. Physical access requires evidence of queue state and delegation at LK/BL31 handoff, including the DMA and system cache contract. The saved Android reference block is from vendor_boot_a and serves only as a one-block comparison. A dedicated physical Setup volume is unverified. No phone access, flash, reboot, or partition changes.

ACTIVE HANDOFF - Duchamp B-to-OrangeFox Linux chain and simulated A return verified in QEMU (2026-11-11)

- Added RECOVERY_CHAIN=1 to the QEMU-only boot menu build. On a simulated B recovery request, the ARM64 shim passed a QEMU virt DTB and OrangeFox recovery ramdisk to the stock Duchamp Android 6.1.57 kernel from boot_a. Android init and the packaged recovery process ran. The full phone ramdisk combination hit a vendor aee_hangdet fault in virt, so the passing chain used the recovery ramdisk alone. Logs and results are under outputs/duchamp-orangefox-qemu-20261111/run.1JxF7B.
- A separate Linux PID 1 probe requested A, checked simulated readback, caused a real guest reset and reached stock Android kernel and diagnostic PID 1 with slot _a. Wrong readback blocked reset. Five recovery-chain checks and all ten previous ramoops checks passed. Final shim and probe rebuilds matched tested binaries. Full Android userspace, OrangeFox UI and native Boot Control return are unverified. An isolated virtual UFS follow-up detected PCI 1b36:0013, but bootctl reads timed out and the MTK service reported missing /dev/block/by-name/misc. No phone commands, flash or partition changes.

ACTIVE HANDOFF - OrangeFox Duchamp recovery and Slot B reviewed offline (2026-11-11)

- Audited the SourceForge community OrangeFox R12.0 Duchamp ZIP, SHA-256 0d9e94518e27d8bacbc36d1dc6269beccda7e05e4fe3999fab8df86d34cd6ac8. ZIP CRC, standalone image header/table ranges and the embedded recovery ramdisk agree. The ZIP contains a vendor_boot v4 image, not a standalone kernel. Its recovery ramdisk includes the Reboot menu A/B switch, bootctl, the Android boot-control service and the MTK recovery service. No installer or recovery executable was run.
- Last verified boot_b matches the XNU service fixture and last verified vendor_boot_b matches the stock Android vendor_boot_a. The exact LK audit finds no fastboot boot command and all seven audit tests passed. No reviewed no-write path starts this OrangeFox build while B contains XNU, and on-device B to A via recovery remains unverified. The known return to Android A used LK Fastboot. Evidence is under outputs/duchamp-orangefox-offline-20261111. No phone commands, slot changes or partition writes.

ACTIVE HANDOFF - Duchamp one-shot pmsg request verified through QEMU warm resets (2026-11-11)

- Added the BOOT_ONCE=1 QEMU menu preview. The saved FDT and earlier live Android parameters place the no-ECC pmsg ring at 0x48160000, size 0x10000. The simulated Android A writer publishes the test ring in QEMU RAM. A guest PSCI reset preserves it, and the ARM64 bootshim on simulated B consumes complete requests only inside the valid ring. It preserves headers, other log bytes and adjacent RAM. A replay after reset does not dispatch XNU a second time.
- Ten QEMU cases passed, including wrap, duplicate requests, later logs, stale data, truncation, an invalid header and blocked return on wrong or absent A readback. The existing menu passed six regression cases. QMP observed guest reset and reentry as simulated A after verified readback. Evidence is under outputs/duchamp-ramoops-boot-once-20261111.Mq2otw. Android, XNU dispatch and firmware slot selection were simulated in this test. Physical retention and slot selection remain unverified. No phone commands or partition changes.

ACTIVE HANDOFF - HakiOS MT6768 one-shot boot comparison (2026-11-11)

- Reviewed upstream oosexgang/hakios-mt6768 ad65e1f4b3ba479e9d7ada98f17398b83cc6f285. Its mtkloader and Android kernel share boot_a. The standard build consumes a one-shot Android /dev/pmsg0 request in ramoops to choose XNU, and chains to Android by default. Its XNU key driver reads both volume keys from KPD and power from MT6358 TOPSTATUS through PWRAP WACS2. This hardware path supplies no MT6897 SWINF2 delegation evidence.
- The saved Duchamp FDT describes mediatek,pstore at 0x48090000, size 0xe0000, with no pmsg-size property on that node. The existing Fastboot lpmsg export proves a retained pmsg slice is readable there. An Android-to-B reboot marker and its consumption at bootshim entry remain unverified. A marker-based one-shot design would also need a verified stock Slot A selection or return mechanism, because Duchamp keeps Android and XNU on separate slots. Source and FDT review only. No QEMU, phone or partition operation.

ACTIVE HANDOFF - Archived Slot B logs do not establish SWINF2 delegation (2026-11-11)

- Rechecked the retained PL/LK log, both pstore exports, the identity-matched Android BL31 log and five archived ATF probe outputs. Four primary capture hashes match their receipts. The PL/LK log reports SPMI initialization, a pre-reboot PMIF command list containing only channel 0 entries, BL31 load and Fastboot entry. No saved log supplies a SWINF2 grant tied to the XNU Slot B entry. Xiaomi's public ATF reader exposes the reserved log buffer on Android, and the published source reviewed contains no matching LK/BL31 channel grant. Coverage report is under outputs/duchamp-swinf2-handoff-audit-20261111/slot-b-log-coverage.json.
- Keep the TOPSTATUS experiment gated on a matching firmware contract or same-boot trace that identifies SWINF2 ownership and serialization after LK exit. No new QEMU run, phone access or partition change. Last verified state remains Android on A after restoring B.

ACTIVE HANDOFF - Duchamp SWINF2 delegation remains unverified (2026-11-11)

- The saved Duchamp DTB and Xiaomi Android driver identify SWINF2 and SID 4. The Android driver serializes its own transactions. The prior Slot B capture proves INIT_DONE=1 and FSM=0 at the sampled instant. A TOPSTATUS read through this channel requires issuing a PMIF command and acknowledging valid data.
- The offline audit reproduced the LK handoff layout and found PMIF initialization references in the archived firmware. The retained LK log does not capture the target handoff, and the reviewed inputs establish no SWINF2 grant or cross-firmware serialization contract. Nine LK audit and four BL31 identity tests passed. Evidence is under outputs/duchamp-swinf2-handoff-audit-20261111. The user gated the new QEMU run and Slot B trial on proof of delegation, so neither ran. No phone access or partition changes. Last verified phone state was Android on A with B restored.

ACTIVE HANDOFF - Duchamp MT6363 TOPSTATUS key bits verified through stock Android (2026-11-11)

- Read only register 0x001e of SID 4 through the live MT6363 regmap in a temporary private read-only debugfs mount. Matched 1,000 samples to the stock PMIC input device. Two volume-down cycles changed 0x1e → 0x16 → 0x1e (active-low bit 3). One power cycle changed 0x1e → 0x1c → 0x1e (active-low bit 1). The ARM64 QEMU backend replayed the measured values and passed 122 PMIF checks.
- The vendor driver uses SWINF2 and serializes its own transfers. PL/LK shows SPMI initialization and the earlier B capture shows INIT_DONE=1 and FSM idle. These establish routing and readiness at the sampled instant. No reviewed firmware record establishes exclusive bootshim ownership of SWINF2, so no bootshim transaction was issued. Android A remained booted and debugfs was absent from the parent namespace after the capture. No reboot, flash or partition changes. Evidence is under outputs/duchamp-mt6363-topstatus-20261111.

ACTIVE HANDOFF - PMIF SWINF2 is initialized and idle at a measured Slot B entry (2026-11-11)

- The Duchamp DTB and MiCode driver match PMIF bank 0, SWINF2 and MT6363 SID 4. The stock Android read selector measured INIT_DONE=1 and SWINF2_STA=0x8441. The isolated read-only bootshim reproduced both values on B (photo D0=4, D1=0x0000000100008441), with FSM=0 at the sampled instant.
- Six ARM64 QEMU snapshot cases and 110 PMIF backend model checks passed. The one-byte TOPSTATUS read from SID 4 at 0x001e passed in the model with the expected read command and acknowledgement. The phone diagnostic issued no SPMI transaction. Physical TOPSTATUS, its key bit mapping and exclusive channel ownership remain unverified.
- Only boot_b received image writes. The original boot_b was restored and Android completed boot from A with seven matching partition hashes. Evidence is under outputs/duchamp-pmif-keys-20261111.

ACTIVE HANDOFF - Slot B captured both physical volume-up edges (2026-11-11)

- Kept the 12-second press window and started a separate five-second release window on confirmed press. D3 records the latest raw KP_MEM1 and is refreshed at timeout. Nine QEMU cases passed, including release beyond the original press deadline and a timeout where the raw and confirmed readings differ. The baseline PC/x0 image remains byte-identical.
- Installed only boot_b for one diagnostic boot. The photo shows D0=8, D1=0x0001ffff, D2=0x0000fffffdfeffff, and D3=0xffff. The hardware sequence was 0xffff → 0xfdfe → 0xffff. Both press and release are confirmed. Restored the previous boot_b and verified Android completed boot on A and all seven partition hashes matched preflight. Evidence is under outputs/duchamp-kpd-release-20261111. PMIC access and slot selection from the menu remain unverified.

ACTIVE HANDOFF - Slot B captured a physical volume-up press (2026-11-11)

- The trial photo shows PC=0x40000000, x0=0x47c80000, D0=0xa, D1=0x0001fdfe, and D2=0x0000fffffdfe0000. KP_EN was 1. The initial MEM1 was 0xffff and the accepted press was 0xfdfe. The deadline expired without a confirmed release. D1 is the last confirmed sample, so the display cannot establish the physical button state at the deadline or the cause of the missing release.
- Archived the photo and decoded values alongside the existing verified restoration in outputs/duchamp-kpd-window-20261111.TryCSB/hardware-trial. Android A booted and all seven checked hashes matched preflight. For the next diagnostic, start a bounded release window when the press is confirmed and record the last raw MEM1 separately from the last confirmed sample.

ACTIVE HANDOFF - Duchamp volume-up capture window tested and B restored (2026-11-11)

- The isolated bootshim shows D0=6 and then samples KP_MEM1 for 12 seconds. It latches a fresh press and release, with two samples per edge and an initial held-key guard. D2 records the three raw snapshots. Eight QEMU cases passed, including real-time fixture register changes, two timeout modes and a key held at entry. The old PC/x0 image remained byte-identical.
- Packed and verified the exact tested Image, backed up the live boot_b, wrote the diagnostic only to boot_b and requested one diagnostic boot on B. Fastboot then restored the original boot_b and selected A. Android completed boot on A with all seven partition SHA-256 values matching preflight. Phone display evidence is pending. Logs and backup are in outputs/duchamp-kpd-window-20261111.TryCSB.

ACTIVE HANDOFF - Slot B physically read the Duchamp volume-up release state (2026-11-11)

- With the user present, verified a fresh boot_b backup and installed the isolated keypad diagnostic to boot_b only. Stock LK accepted Slot B. The user's photo shows PC=0x40000000, x0=0x47c80000, D0=4 and D1=0x0001ffff. The handoff matched and the bootshim physically read KP_EN=1 and KP_MEM1=0xffff, with volume up released. A physical press transition and PMIC access were not measured.
- After the user returned to Fastboot, selected and verified A, restored the original boot_b, and confirmed Android V816.0.17.0.UNLMIXM completed boot on A. All seven checked partition hashes match the pretrial values. Only boot_b received image writes. Evidence, photo and fresh B backup are under outputs/duchamp-kpd-hardware-trial-20261111. A future bounded read window after the diagnostic appears can capture a physical press and release in one boot.

ACTIVE HANDOFF - Isolated Duchamp volume-up probe staged for Slot B (2026-11-11)

- The pinned FDT maps volume up to KP_MEM1 bit 0. The archived LK log reports KP_EN=1 before Fastboot. The new PC/x0 capture profile checks the recorded handset entry addresses and inherited CPU state, then attempts one 16-bit KP_EN read and one KP_MEM1 read if enabled. Screen stages bracket the reads. PMIC and slot selection remain unavailable.
- Five QEMU cases passed, including the hardware image rejecting the QEMU handoff and four simulated keypad register states. Host and existing PC/x0 and UFS receiver checks passed. The standard PC/x0 binary is byte-identical. The 64 MiB local B diagnostic passed boot header and AVB hash checks and unwrapped to the tested Image. Previous B backup SHA-256 still matches the prior installed image. Results and image are under outputs/duchamp-kpd-entry-20261111.cSLzHv.
- No flash, slot change or reboot. ADB confirmed Android completed boot on A. Physical KP_EN/KP_MEM1 access and the separate early PMIC path still need verification. The diagnostic has no storage, PMIC, reset, or XNU jump path.

ACTIVE HANDOFF - Physical Duchamp buttons verified under Android on Slot A (2026-11-11)

- Captured real press/release pairs for volume up through mtk-kpd and for volume down and power through mtk-pmic-keys. Android completed boot on A and stayed on A. All three A boot image hashes matched the saved pre-trial baseline. All three B hashes matched the previously tested XNU trial images.
- The installed B image does not contain the QEMU menu. Physical button sampling at bootshim entry and the menu's return to A remain unverified. No reboot, flash, slot change or partition write was issued. Read-only evidence: outputs/duchamp-phone-buttons-android-20261111/verification.json.

ACTIVE HANDOFF - Duchamp menu entry samples verified in QEMU (2026-11-11)

- Added a QEMU-only preview that consumes an injected keypad and PMIC sample at menu entry, before drawing or reading UART. All seven entry cases passed: neutral, each key held, incomplete, invalid PMIC and missing. After release, fresh volume up/down and power selected B, A and confirmed A. All seven menu regressions passed, including simulated A readback followed by a QMP guest reset and B dispatch to XNU. Three incompatible build configurations were rejected. Host checks passed and the phone PC/x0 diagnostic remains byte-identical.
- Stock LK Fastboot is the verified route to A. The reviewed LK Linux handoff exposes no documented next-slot operation callable from the shim. HakiOS's redwood menu changes its own slot bootability and relies on Qualcomm ABL to choose Android. A documented Duchamp slot provider and physical early key reads remain open. This run issued no phone commands. Results: outputs/duchamp-boot-menu-entry-20261111.ehCBiY/verified/verification.json.

ACTIVE HANDOFF - Duchamp keypad and PMIC button samples feed the boot menu (2026-11-11)

- Added the menu's button decoder. The saved Duchamp FDT maps volume up to active-low KPD MEM1 bit 0. The decoder accepts normalized PMIC levels for volume down and power. QEMU replays held-on-entry power, repeated samples, a chord, an invalid PMIC sample and fresh individual presses. Seven QEMU cases pass, including Slot A reset after a simulated readback and real XNU dispatch after a volume-down and power replay. Host and PC/x0 regressions pass.
- The running Android A exposes android.hardware.boot.IBootControl/default. The stock LK Linux handoff still has no documented next-slot provider for this bootshim. Real button sampling at shim entry and selection of A from that entry remain unverified. No phone reboot, slot change, flash or partition write. Report under outputs/duchamp-boot-menu-keys-20261111.

ACTIVE HANDOFF - Android menu return rehearsed with verified QEMU reset (2026-11-11)

- Read-only Android A identifies volume up through mtk-kpd and volume down/power through mtk-pmic-keys. The saved Duchamp DT and pinned Xiaomi driver sources agree. The archived LK trace observes keypad initialization, a power-key status read and a PMIC home/volume-down press on the way to Fastboot. All three button edges at bootshim entry remain unverified.
- Menu A or timeout now sends the next-slot request. The QEMU provider requires a fresh readback of A before PSCI reset and blocks a wrong slot, missing reply and pre-buffered reply. QMP observed a guest-reset after simulated A. Six cases pass, including real XNU kernel dispatch on B inside QEMU. Android boot from this menu and a documented phone-side next-slot provider remain pending.
- Android is still running on A. No phone reset, slot change, partition write or flash. Reports are under outputs/duchamp-boot-menu-return-20261111.

ACTIVE HANDOFF - Duchamp dual-boot menu verified in QEMU (2026-11-11)

- Built the opt-in QEMU menu on the existing framebuffer and used emulated serial keys for navigation and confirmation. A is the default after 10 seconds, including if B was highlighted without confirmation. Four QEMU cases passed, including confirmed B entering the XNU kernel through the existing payload guard. Confirmed A and timeout remain shim decisions, with no Android dispatch in this profile.
- Verified the build from a clean source snapshot. Existing PC/x0 capture is byte-identical and host regression tests pass. The saved FDT has an enabled MediaTek keypad node, but early key availability and a supported A-select-and-reset backend remain unverified. Android A and XNU B were untouched. Screenshots and results are in outputs/duchamp-boot-menu-qemu-20261111/verified-clean.

ACTIVE HANDOFF - Android boot verified on Duchamp Slot A (2026-11-11)

- With user approval, refreshed the bootloader after the earlier accepted A selection. Fresh LK Fastboot reported current-slot a and slot-unbootable:a no. Normal reboot then returned OKAY. ADB confirmed duchamp, ro.boot.slot_suffix=_a, sys.boot_completed=1, Android 14 and build V816.0.17.0.UNLMIXM.
- Left Android running on A. This verification issued no new slot-selection command, flash, manual partition write or data wipe.

ACTIVE HANDOFF - Duchamp accepted Slot A selection in Fastboot (2026-11-11)

- The user requested Slot A. Confirmed the connected Duchamp in LK Fastboot with B reported, and A marked successful and bootable. Sent set_active a once and Fastboot returned OKAY. Two immediate getvar queries still report B in the existing LK session. The earlier B selection showed the same stale readback until a new bootloader session. Slot A readback and Android boot remain unverified.
- Left the device in Fastboot with no reboot, no second slot command and no image flash.

ACTIVE HANDOFF - Slot B pstore exports contain no attributable XNU log (2026-11-11)

- Read lkmsg (262144 bytes) and lpmsg (65536 bytes) through live LK Fastboot USB on Duchamp with B selected. Both returned DATA and terminal OKAY. Excluding send-buffer tails, the two payloads have no readable XNU lines, same-boot identifier, or UFS handoff markers in ASCII or UTF-16. These exports cover console/pmsg slices only and omit LK-stripped header bytes. ATF and other pstore zones were not read.
- B remained selected with zero retries before and after. No reboot, slot switch, partition access or writes. UFS controller/queue state and DMA/cache delegation remain unproven. Private captures and verification are under outputs/duchamp-slot-b-pstore-20261111.

ACTIVE HANDOFF - Current Slot B Fastboot cannot export raw ATF through the reviewed paths (2026-11-11)

- Live Duchamp LK Fastboot identified B, version duchamp_cc6aa9311_202412180714, with zero B retries before and after. The standard get_staged request returned unknown command and zero bytes. max-fetch-size was empty. No reboot, slot change or partition access.
- Audited all 35 registrations in the archived matching LK. No upload/fetch handler. dump_pllk_log shares uefilog's retained PL/LK buffer. lkmsg/lpmsg map the separate pstore region. expdb exports crash storage and was not run. The official ATF raw reader is an Android driver. No raw ATF or boot ID links the current session to the XNU handoff. Physical UFS stays blocked. Seven LK audit tests passed. Report under outputs/duchamp-slot-b-atf-fastboot-audit-20261111.

ACTIVE HANDOFF - Live Slot B Fastboot PL/LK export verified (2026-11-11)

- Confirmed Duchamp in LK Fastboot, current-slot B. The verified retained-log command returned 197219 bytes and terminal OKAY using the installed Android USB DLL and a bounded host receiver. The log confirms BL31 image load followed by entering Fastboot, with no XNU handoff, HCE, queue, DMA/cache or ownership markers. USB capture works for PL/LK. A same-boot BL31-to-XNU firmware trace is still missing.
- B remains selected. After capture Fastboot reported zero retries, successful=no and unbootable=no. No reboot, slot change, firmware replacement, direct MMIO, partition write or physical UFS block read. Seven LK audit and nine ownership regressions passed. Keep the private capture out of git. Report and capture are under outputs/duchamp-slot-b-live-lk-log-20261111.

ACTIVE HANDOFF - Slot B firmware trace remains missing (2026-11-11)

- Rechecked the Slot B photograph and Fastboot receipt. They establish the diagnostic RAM-root launchd and services, with no firmware queue state or same-boot ownership record. Two host checks found no ADB or Fastboot device. No reboot, partition write, physical UFS read or mount.
- The official Duchamp ATF and PL/LK source blobs match the locally archived copies. The saved Android FDT declares a 2 MiB ATF buffer. The Android raw interface only copies that existing buffer, with no verified cross-boot retention or correlation to Slot B. The current trace still needs an actual BL31-boundary sample and firmware delegation for XNU. All 22 local identity, handoff and ownership checks passed.
- Rechecked the prior QEMU Hello and language image hashes. Its read-only qufs0 GPT root and RAM-backed /private/var are verified in that receipt. A separate physical root location has not been established. Report is under outputs/duchamp-slot-b-firmware-trace-20261111.

ACTIVE HANDOFF - Slot B UFS handoff receiver and known-block replay (2026-11-11)

- Built an opt-in PC/x0 receiver that correlates the FDT from RAM and reports missing same-boot firmware trace, unknown controller and queue state, and unverified DMA in D1=0xf. Both QEMU runs verified the fingerprint and framebuffer output. The original PC/x0 capture still builds byte-for-byte. No UFS MMIO, SMC, DMA, storage command or XNU jump in this receiver.
- The emulated UFS qtest passed 27/27, including one 4096-byte READ(16) on LUN 2 / LBA 276480 matching the retained Android digest, one-byte mismatch rejection, and zero backend access for absent authorization or busy queues. The resource gate passed 9/9.
- LK requests HCE=0 without readback. Actual HCE, legacy/MCQ queue state, firmware resource delegation and the XNU DMA/cache contract are unproven at handoff. Physical read and Setup mount remain pending. Keep the verified Slot B image and leave A and shared userdata alone. Local report and raw receiver are under outputs/duchamp-slot-b-ufs-diagnostic-20261111.

ACTIVE HANDOFF - Photograph verifies Apple launchd and diagnostic services on Slot B (2026-11-11)

- Matched the user-supplied Slot B photo to the pinned services fixture. It shows NOTIFYD CONTROL PASS (notifyd PID 7), SYSLOGD CONTROL PASS (syslogd PID 4, six ASL messages, clients 5 and 6) and heartbeat 8 with probes stopped. The controller enters the lifecycle only after checking getppid() == 1 and proc_pidpath(1) == /sbin/launchd. Together with the preceding Fastboot Slot B selection this establishes native launchd as PID 1 on B.
- Archived the photo and updated the trial receipt under outputs/duchamp-slot-b-trial-20261111. Setup and physical UFS are still unverified on B. Retain the known-good B image as a fallback. The next hardware diagnostic needs to prove the MT6897 storage handoff before issuing a bounded read-only 4 KiB comparison against Android. Keep any future iOS root separate from shared userdata. No phone access, reboot, slot switch or partition writes during this photo review.

ACTIVE HANDOFF - Duchamp Slot B accepted the XNU trial and the user saw XNU logs (2026-11-11)

- The user authorized exactly vendor_boot_b, init_boot_b and boot_b, preserving A, recovery and userdata, with return to A if XNU failed. Verified A boot, unlock, 90 percent battery, all image pins and matching live backups of the three B partitions before flashing. Fastboot returned OKAY for all three writes. No write command targeted A, recovery, userdata, vbmeta, dtbo or LK.
- After set_active b, the running Fastboot session continued reporting A and stale B state. Refreshed with reboot-bootloader, without a second set_active or flash. Fresh LK Fastboot reported current-slot b, slot-unbootable:b no and six tries. Normal reboot was accepted. The user then reported XNU logs visible. No picture or serial log was available when recording this checkpoint. The exact last XNU stage, launchd on B and Setup were not independently established.
- Left B selected after the reported XNU entry. A was confirmed booted and its hashes captured before the trial. Post-trial Android/recovery verification was not performed because B remained running. No rollback requested. Trial log, backups, and result are under outputs/duchamp-slot-b-trial-20261111.

ACTIVE HANDOFF - Staged verified Duchamp Slot B XNU and vendor boot images locally (2026-11-11)

- Staged boot_b.img and vendor_boot_b.img, 64 MiB each, under outputs/duchamp-slot-b-candidate-20261111. boot_b is byte-identical to the phone-tested service image 54511250...8f6a8, with diagnostic HFS+ md0 and physical UFS disabled. The staged kernel round-trips via legacy LZ4 to the pinned shim Image. A fresh test of that exact unwrapped image with the saved final FDT reached XNU in QEMU. A separate fresh replay of the same services and payload passed all 74 checks.
- vendor_boot_b is byte-identical to the known-good V816.0.17.0.UNLMIXM vendor_boot_a. Its AVB content hash matches the signed descriptor in the exact saved vbmeta_b. The vendor boot v4 load layout matches the measured kernel and FDT addresses, and the embedded DT table entry matches the saved DTB. The unsigned XNU boot footer verifies for integrity and does not satisfy the Xiaomi signed boot chain in vbmeta_b. Unlocked LK acceptance was previously observed on A and remains untested on B.
- Live init_boot_b differs from the signed expected content digest, as does the older local init_boot_a archive. Extracted a clean 8 MiB init_boot reference from the official matching Xiaomi OTA using bounded HTTP ranges. OTA manifest and the current signed vbmeta_b digest both match it. Kept it separate as a reference, with no device write.
- Read-only follow-up confirmed Android booted on A, both A boot images match stock, B boot images are still blank, and vbmeta_b is unchanged. No flash, slot switch, reboot, recovery boot or physical UFS access. Slot B hardware acceptance and storage-backed Setup remain unverified.

ACTIVE HANDOFF - Live Duchamp slot B has blank boot and vendor_boot (2026-11-11)

- Read-only ADB reconfirmed Android V816.0.17.0.UNLMIXM on slot A, completed boot, and Virtual A/B. AOSP-format metadata at misc offset 2048 matched magic, version, count, and CRC. A reports successful with priority 7. B has priority 0, tries 0, and is not successful. The metadata prefix did not contain a recognized ASCII slot suffix. The running slot comes from Android boot properties.
- Full live partition hashes confirm boot_b and vendor_boot_b are each 64 MiB of zeros. lk_b, dtbo_b and vbmeta_b match their A counterparts byte-for-byte. init_boot_b is present and matches its archived copy. boot_a and vendor_boot_a match the verified stock backups. init_boot_a differs from its saved stock copy and must be preserved as currently installed. There is one named userdata and no separate recovery partition. A's saved and live-identical vendor_boot has the recovery fragment. Recovery was not booted, and OrangeFox operation is unverified.
- Report and reader are in outputs/duchamp-slot-inventory-20261111. Slot B requires a compatible vendor_boot and XNU boot image before a trial. The separate iOS root location and MT6897 storage path remain unresolved. No reboot, slot switch, flash or device write.

ACTIVE HANDOFF - Duchamp Slot A stays Android; Slot B is the XNU boot target (2026-11-11)

- User clarified the intended dual-boot layout. Preserve Android and its working recovery on A. Scope the future XNU loader image to boot_b and load the iOS root from separate storage that does not overwrite Android data. The root location and physical UFS path are still unresolved.
- ADB and Fastboot both reported zero devices in this check. Saved boot_b and vendor_boot_b captures are zero-filled and cannot establish the current state. Verify live slot metadata, B's supporting boot images and slot-specific firmware requirements, and the known-good A recovery and return path before deploying anything. Check retry behavior separately from an XNU boot success. No slot switch, reboot or device write occurred.

ACTIVE HANDOFF - Duchamp storage boot is the target and Android recovery must remain usable (2026-11-11)

- User selected storage-backed iOS boot and asked to preserve a useful Android recovery such as OrangeFox. Standalone RAM-only entry is no longer a prerequisite. Reuse the existing boot-v4 Duchamp entry evidence and QEMU GPT-backed read-only Setup proof. Keep the storage location unassigned on the phone. Do not repurpose userdata or change GPT without specific approval. The physical UFS path remains fail-closed pending MT6897 ownership, queue, DMA and cache evidence.
- Rehashed saved boot_a and vendor_boot_a against the trial pins. The stock boot_a contains the Linux kernel and no generic ramdisk. The vendor_boot_a v4 table has a 13,565,240-byte fragment named recovery, type 2. Retaining the vendor fragment alone does not demonstrate a usable recovery after the Android kernel is replaced. The previously verified fallback is Fastboot restoration of stock boot_a followed by Android boot. Verify the current recovery path and preserve a known-good Android boot path before a storage-backed phone trial.
- Saved boot_b and vendor_boot_b images are both all-zero. This is archive evidence, not a fresh slot inventory. Do not assume slot B is an available Android fallback. OrangeFox identity and operation on the live phone were not verified. The recovery and storage audit is in outputs/duchamp-storage-recovery-20261111. Nine resource ownership and 26 QEMU profile tests passed. No phone access, reboot, flash or partition modification.

ACTIVE HANDOFF - Compact 20F66 HFS+ RAM root reached Setup Hello on QEMU (2026-11-11)

- Cloned the pinned 3 GiB RAM Setup root and removed 59 non-English CoreEmoji localizations from the new copy. The compact HFS+ volume is 3,019,898,880 bytes (2,880 MiB), 192 MiB smaller, with 81,580,032 bytes free at build time. fsck.hfsplus -fn passed. Compared every retained data file with the original: 1,333 matched, including all 43 dyld cache files. Source root stayed byte-identical. Compact SHA-256 475ac6e417412562bad1b7330fdc99eae232b86ecd7090da92fd68d6f900ea0e.
- Both the first compact run and a parallel original-root control tripped the guest interrupt-processing timeout in QEMU. The successful compact retry used the same image and CI 41543710742 kernel with the QEMU-only ml-timeout-interrupt-masked-scale changed from 4 to 32, and reused the established iOSUser and software scanout hooks. XNU mounted SweetRAMRoot from md0. Setup PID 37 received BackBoard status 0. The Hello framebuffer passed 6/6 checks at SwapEnd 186, IOSurface 5, layer 0, in 273.713 host seconds. All active pixels matched the software scanout. No kernel panic was seen in the successful run.
- Result, Hello PNG, logs, and local replay tools are in outputs/duchamp-setup-compact-ram-20261111. The private compact root is at ~/.cache/duchamp-qemu-tests/setup-compact-ram-20261111-v3/root.hfs in Ubuntu WSL. Only Hello was tested. QEMU attached no guest disk or UFS device. No phone access, partition changes, or physical UFS.

ACTIVE HANDOFF - Xiaomi OTA comparison finds no additional Duchamp RAM entry (2026-11-11)

- ADB read-only on V816.0.17.0.UNLMIXM, slot _a, confirmed the saved lk_a SHA-256 and disabled CONFIG_KEXEC and CONFIG_KEXEC_FILE. No reboot or write to the phone.
- Reconstructed LK offline from Xiaomi full OTA range reads for OS3.0.10.0.WNLMIXM, OS3.0.307.0.WNLEUXM and OS3.0.305.0.WNLCNXM. Metadata, compressed operation and LK hashes matched their OTA records. The Global and China registries match the installed 35 names. EEA has 33 names, removing two OEM commands. All three lack a registered RAM execute command. The installed and Global continue callbacks were traced to storage boot.
- AOSP Android 14 fastbootd lacks boot in its command map. The exact Xiaomi recovery binary was not tested. The provider remains unproven. Seven audit tests passed. The exact registries, source receipts and replay scripts are in outputs/duchamp-ram-entry-refresh-20261111.

ACTIVE HANDOFF - UniXNU and HakiOS review finds a reusable ramoops output, with Duchamp RAM entry unresolved (2026-11-11)

- Reviewed the current UniXNU catalog and pinned MediaTek sources and documentation. Lenovo TB375FC is its only MT6897 entry and uses board-specific UEFI with boot_a/misc restoration and UFS mrdump logging. Dandelion uses a boot image write and eMMC logging; Merlinx writes its boot partition and uses a downstream MUSB diagnostic endpoint. Dali documents ramoops and a boot_b restore cycle. HakiOS MT6768 boots its loader from boot_a. The fresh Duchamp LK audit still exits 1 with --require-provider.
- Ramoops is the useful receiving-side channel. The saved Duchamp FDT and read-only live Android parameters agree on the reserved region and sizes. The pinned GKI zone layout gives console 0x4811f000 + 0x40000, ECC zero. Android previously recovered its own console-ramoops-0 after a panic.
- Compiled only the HakiOS console-ring writer for an isolated QEMU AArch64 guest. The first link placement overlapped the virt DTB, so it was moved to 0x40200000. Both the short and wrapped test payloads were recovered byte-for-byte from private RAM after QMP reset. The host decoder follows the GKI header/ring order, rejected an oversized header, and verified neighboring bytes. No Android guest was booted and this is not proof of XNU-written record retention on the phone.
- Pinned source receipts, replay script, test reports and read-only parameter receipt are in outputs/duchamp-mediatek-upstream-20261111. No phone reboot, ramoops write, flash or partition change. Ramoops can carry a log after entry. A supported Duchamp caller and authoritative BL31 UFS state and delegation remain unresolved.

ACTIVE HANDOFF - Diagnostic-channel search narrows uefilog to retained PL/LK data (2026-11-11)

- Added --diagnostic-channels to the pinned LK RAM-launch audit. It verifies the registered oem uefilog handler's buffer getters, copy/send path and PL/LK label. This sender returns retained PL/LK bytes. It supplies no proved fresh UFS handoff measurement, ownership grant or RAM entry. Runtime execution of that OEM command remains unverified.
- Inspected the pinned MediaTek kernel reference log consumers and official Xiaomi source inventories. The ATF ordinary read advances the shared ring cursor. Correction to the initial source-reading update: the ordinary open has no SMC. TIME_SYNC runs at driver probe/resume; the write path has a separate debug SMC. These references were not equated to the live logger binary. Upstream TF-A DebugFS is build-selectable and MediaTek UART guidance targets Genio EVKs. Neither establishes a Duchamp diagnostic channel. A separate complete Xiaomi drivers-subtree query resolved the initially truncated source inventory for the relevant filenames.
- All 25 focused tests passed. The extended audit on the actual LK identifies the retained sender, --require-provider correctly returns 1, and the default report is byte-identical to the archive. Derived evidence and pinned source receipts are in outputs/duchamp-diagnostic-channels-20261111. No phone access, OEM command, SMC/MMIO execution, reboot, flash, partition write or physical UFS read.
- A qualified vendor-supported Duchamp trace or documented RAM diagnostic interface covering the final BL31-to-XNU boundary remains missing. The conditional hardware snapshot was not acquired.

ACTIVE HANDOFF - Locate the Duchamp UFS observation boundary after BL31 boot callbacks (2026-11-11)

- The optional --atf audit pins the saved 953,976-byte BL31 capture and follows the LK kernel-boot service descriptor. Its first-entry handler selects callback group 5. The table contains sip_emi_set_nsr_permission then spm_smpu_hre_first_bk before the final handler helper. A sample on the LK side would miss this secure-side work. This is static captured BL31 evidence, not a runtime trace or proof that the running image is byte-identical.
- Documented the two correlated hardware records in duchamp/MT6897-LK-HANDOFF-CONTRACT.md. Obtain a firmware-side record after the last platform work, correlated to first entry of the XNU boot path in the same boot. Record HCE and legacy/MCQ drain, the authoritative resource grant, and the DMA and system-cache contract. The existing PC/x0 capture supplies only CPU entry state. The exact LK RAM launch audit still rejects the no-write provider requirement. No documented vendor trace carrying these observations has been verified.
- The saved-image audit passed, its default output stayed byte-identical to the archive, and 23 focused audit, layout and ownership tests passed. The existing bootshim recorded PC/x0/EL and passed the framebuffer check in QEMU with the extended report. Reports are in outputs/duchamp-ufs-capture-point-20261111. No physical handoff snapshot, phone access, flash, partition write, MMIO/SMC execution or physical UFS read.

ACTIVE HANDOFF - Duchamp LK requests UFS shutdown after blackbox, with no handoff state proof (2026-11-11)

- Followed the matching lk_a.bin call path beyond the blackbox routine. The call at file offset 0x10070 enters the final wrapper, which calls platform cleanup at 0x196e8. Cleanup calls UFS shutdown at 0x3b14. The same host structure resolves to the UFSHCI base in the saved DTB. Shutdown clears AHIT, calls ufs_poweroff_notify, discards its status, requests HCE=0 at 0x79e48, and returns without reading HCE back. The notify path submits a legacy command. Neither the static shutdown sequence nor the architected EL1 cache operations establishes a queue drain or an XNU resource grant.
- Read existing Android PL/LK and ATF logs over ADB on V816.0.17.0.UNLMIXM, slot _a. PL/LK matches the earlier archived hash. The late LK lines and the available BL31 2fbca47 log contain no state snapshot of the transfer/task queues or MCQ, controller/clock/PHY delegation, or the XNU DMA and system-cache contract. The stock Android boot logs do not describe XNU entry.
- All 23 evidence tests and 27 fresh QEMU one-block qtest checks passed. The fixture for LUN 2 / LBA 276480 matches the saved Android SHA-256 065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6, and a one-byte change fails the digest comparison. The offline ownership gate remains denied with all hardware callbacks at zero. No physical UFS read from XNU, direct MMIO/SMC, reboot, flash or partition write.
- Derived reports are in outputs/duchamp-ufs-handoff-boundary-20261111. The next required evidence is a documented snapshot at the actual XNU handoff showing HCE and quiescent legacy transfer/task state or MCQ state as applicable, plus firmware delegation of controller, clocks, PHY, DMA and system-cache responsibility for the XNU buffer.

ACTIVE HANDOFF - One-block Duchamp UFS digest verified on the emulated controller (2026-11-11)

- Added the offline --known-block mode to tools/test-duchamp-driver-core.py. It validates the saved Android receipt and the full vendor_boot_a backup hash, embeds only the reference block in a temporary read-only QEMU LUN 2 at LBA 276480, and issues exactly one SCSI READ(16) per case through the portable driver. The returned 4096 bytes match Android SHA-256 065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6. A one-byte mutation is detected. The harness persists no raw block or qtest packet trace in this mode.
- The cold legacy UFS start guard now also rejects pending/running task-management queues. Simulated transfer and task queue states were refused before any register write or DMA callback. Missing platform readiness refused all transport callbacks. The real Duchamp assessment still denies the physical provider with zero MMIO, SMC, DMA and UFS callbacks. QEMU is not hardware handoff evidence. Keep phone execution blocked pending independent proof of queue state, including MCQ where applicable, and the firmware/resource/DMA/cache grant.
- All 27 focused checks, 694 QEMU/host regression checks, 78 native ASan/UBSan guards, 79 polling checks each on native and ARM64 QEMU, and 9 ownership checks passed. Tampered LBA and changed backup failed before QEMU. Reports are under outputs/duchamp-ufs-one-block-20261111, with qtest-final/result.json and ownership.json. No XNU guest, phone command, flash, partition write or physical read occurred.
- Reproduce from the repository root with: python3 tools/test-duchamp-driver-core.py work/ufs-one-block-NEW --known-block ../../outputs/duchamp-ufs-known-block-20261110/android-reference.json ../phone-boot/vendor_boot_a.img

ACTIVE HANDOFF - Lenovo MT6897 reference narrowed the Duchamp UFS comparison (2026-11-11)

- Rehashed the actual 64 MiB combined-services image and the phone photo. Both match the pinned Duchamp hardware trial in PHONE-SERVICES-BATCH.md. That trial used boot_a and restored stock Android. The verified RAM-root services are a reusable XNU baseline. The standalone RAM-only entry and full Setup root remain separate requirements.
- Reviewed public UniXNU-tb375fc at cc4da0eabe4a27825253e6332f33ca4760ebb359. Its README records physical XNU and a 232 MiB APFS recovery fixture through a Lenovo-specific UEFI chain. The reported trials restored boot_a/misc. Decoded the saved Duchamp DTB using /soc address/size cell widths and confirmed its UFSHCI base and size match Lenovo's 0x112b0000 / 0x3000. The source checks inherited controller readiness and empty transfer/task doorbells and uses explicit cache maintenance on private aligned DMA buffers. Its diagnostic write path and board-specific ownership assumptions are outside the Duchamp read-only scope.
- All 12 existing resource/ownership checks passed. Next compare the inherited controller, DMA and cache assumptions against Duchamp handoff evidence and validate a bounded one-block read design against the existing fail-closed gate. This source comparison establishes no Duchamp UFS grant or new RAM boot provider. No phone operation or driver changes.

ACTIVE HANDOFF - Live PL/LK log separates early UFS deinit from the final LK handoff (2026-11-10)

- Read the existing Android /proc/pl_lk and /proc/bootprof views over ADB on V816.0.17.0.UNLMIXM, slot _a. The PL/LK log was 254,454 bytes with separate PL and LK sections. PL reports UFS power-off notification and boot_device_deinit. LK logs its Linux jump announcement before blackbox log persistence and a later UFS sense warning. The pinned LK instructions place the blackbox call between the announcement and the secure handoff call.
- The bootprof snapshot adds no UFS handoff markers. The PL milestone does not establish final DMA queue drain, clock/PHY delegation, or cache ownership. The next evidence target is the UFS state after blackbox returns and before LK/BL31 enters the kernel. Nineteen local layout and ownership checks passed. Only derived evidence is in outputs/duchamp-ufs-pllk-20261110/verification.json. No physical XNU UFS read, MMIO/SMC probe, reboot, flash or partition write.

ACTIVE HANDOFF - LK UFS boot metadata confirmed, XNU delegation still unproven (2026-11-10)

- Replayed the pinned LK, Android Image and FDT layout audit. The captured LK writes a four-byte /chosen/atag,ufs property. The live Android FDT matched the saved property and bootmode phandle. The matched vendor module reads it through ufs_mtk_init. The pinned reference source defines the field as RPMB Region 2 key state. The FDT also identifies 12 clocks and the PHY, with no ownership grant established.
- Read-only Android ADB returned 327 lines from the available ATF boot log on Duchamp V816.0.17.0.UNLMIXM. The phone reports BL31 2fbca47 and common_2.6.1(6897-1.2). Public TF-A lts-v2.8.6 points to ff0bd5f. The available log contains no UFS handoff, resource ownership or DMA-cache marker. The matching BL31 source remains unverified.
- All 14 local LK-layout, BL31 identity and resource-binding tests passed. UFS controller quiescence and delegation, clock and PHY ownership, and the DMA buffer/system-cache contract for XNU remain unproven. Evidence is in outputs/duchamp-ufs-handoff-audit-20261110/verification.json. No phone reboot, flash, partition write, MMIO/SMC probe or physical XNU UFS read.

ACTIVE HANDOFF - Matched Duchamp firmware and DMA evidence keep physical XNU UFS closed (2026-11-10)

- Read-only Android recheck matched the complete active-slot tee_a hash and installed ufs_mediatek_mod build-ID note to the saved captures. Re-extracted the saved BL31 UFS dispatch evidence and matched its pinned audit after line-ending normalization. The saved client ABI verifier reproduced its pinned report byte-for-byte. A common zero return does not prove a successful effect or authorize XNU.
- The newer passive PRDT v3 receipt proves raw DMA equals PA for the observed Android route. No SWIOTLB transfer appeared in 34,162 sampled segments. That receipt does not establish XNU firewall/delegation or the bounce disposition for its allocation. The saved XNU QEMU run confirms clean/flush-to-PoC and barriers in QEMU, with the MT6897 system cache path and owner unproven.
- All 23 evidence tests passed. Resource ownership remains blocked with zero MMIO, SMC, DMA or UFS dispatch. No physical XNU read of LUN 2 / LBA 276480 was performed, and Setup was not mounted. No reboot, flash or partition write. The scoped decision, reports and exact reference digest are under outputs/duchamp-ufs-xnu-ownership-20261110.

ACTIVE HANDOFF - Duchamp physical UFS block reference captured under Android (2026-11-10)

- Read-only ADB on Duchamp/MT6897, Android V816.0.17.0.UNLMIXM, active slot _a. First 4 KiB of vendor_boot_a matched two independent reads from Linux SCSI LUN 2, LBA 276480, and the exact saved partition backup. Reference SHA-256 065f2cf024655ce86cd67efd58901ded708c34cf2e721778b6b3de67f5382fd6. Only the digest and geometry were retained.
- The active-slot tee_a hash matches the saved partition byte-for-byte. Linux bound ufshcd-mtk, reports 13 supplier links, and has no iommu_group link for that controller. These observations do not establish XNU firmware effects, resource/cache ownership, direct PA-to-DMA translation, or bounce disposition. The pinned gate still denies current evidence, mask 0x000100000000040e, with zero hardware/provider dispatches.
- Native and ARM64 model checks passed for the gate, DMA routing and cache backend. The full XNU replay passed 23/23 checks in 76.25 host seconds with virtual GPT/qufs0, diagnostic PID 1 and EROFS on write-open. That replay used a separate synthetic HFS+ fixture. Physical XNU read and Setup mount remain pending. No phone reboot, flash, partition write, MMIO diagnostic, or SMC. Evidence is in outputs/duchamp-ufs-known-block-20261110.

ACTIVE HANDOFF - Duchamp Setup root needs a separate transport (2026-11-10)

- Rechecked the actual 3,355,443,200-byte HFS+ root from the verified QEMU Wi-Fi picker with the phone ADT extracted from the known boot_a service candidate. The current CI kernel, root and boot data require 3,394,748,416 bytes. The payload builder rejected them against the 536,870,912-byte phone window before loading the root or creating an image. The saved phone FDT describes 12 GiB total, which does not establish a safe larger XNU window.
- Using the phone packer's LZ4 legacy format, a streamed prefix of the root alone exceeded the saved 67,108,864-byte boot_a container. The root hash matched before and after. Increasing the XNU window alone cannot make this root fit the existing boot_a transport.
- All 48 phone readiness, layout, and virtual UFS profile tests passed. The large root needs a separate transport. The existing virtual qufs0 backend cannot provide it on MT6897, and physical UFS stays gated pending firmware/resource and DMA/cache proof. Receipt is outputs/duchamp-phone-setup-preflight-20261110/verification.json. No phone access, partition write, or new boot image.

ACTIVE HANDOFF — QEMU Setup read synthetic SIM presence before scene creation (2026-11-10)

- Retested original 20F66 Setup without the prior cellular dylib or control job. The original fixture rejected getSubscriptionInfo, getConnectionAvailability and usingBootstrapDataService. The updated QEMU-only fixture returns native CTXPCServiceSubscriptionInfo and CTDataConnectionAvailabilityStatus objects and a typed BOOL bootstrap response. Its synthetic slot is 1, availability is false, and bootstrap data service is false.
- Fixed two reproducible QEMU startup stalls. The repeated LaunchServices launchctl command now has 120 seconds. The test opted into reusing a completed registry only after verifying native installed records and exact paths for both SpringBoard and Setup. The display check also passed. A later SIGBUS came with the virtual UFS core in failed state 3, deadline reason 1 and 5,911 successful reads. Raised only the QEMU adapter deadline from 3,000 to 30,000 ms, preserving the poll cap and fail-closed behavior. This runtime used a one-instruction QEMU-only overlay on CI 42707402072 with the original kernel preserved. A fresh CI build of the source change has not run.
- The retry reached original Setup PID 70 in user/501 and BackBoard returned status 0. Before Continue, native Setup requested subscription information and called isSimPresent twice on the returned subscription type. The CommCenter service logged slot 1 present/good and answered the availability and bootstrap queries from the same PID. No getSIMStatus or registration query came from Setup. SpringBoard PID 59 independently requested getSIMStatus and received Ready. Setup's separate copyMobileCountryCode request was rejected.
- Setup exceeded the 1,220-second scene-create watchdog while in CoreText shaping, before the network picker. The watchdog reported 7.846 CPU seconds attributed to the application during that interval. No network-screen or automatic registration result was established. Virtual UFS remained active with zero timeout reason after 6,071 successful reads. 26 virtual UFS profile checks and 79 each native and ARM64 model checks passed. The test used -nic none, qufs0 read-only and /private/var on md0. No phone or operator access. Local evidence is under outputs/duchamp-qemu-cellular-native-20261110 and the final replay under work/qufs-gpt-cellular-native-20261110-v5.

ACTIVE HANDOFF — Setup read synthetic SIM and network registration through CommCenter (2026-11-10)

- Built a read-only CommCenter fixture and native CoreTelephony probe against the verified 20F66 protocol. The service exposes the two state queries, one synthetic subscription context and the handshake needed by native clients. Its standalone entry requires SWEET_QEMU_CELLULAR_FIXTURE=1. The Setup probe runs only when the QEMU debugger explicitly loads it into the original Setup process.
- The first clone placed the jobs only in LaunchDaemons and this boot profile did not load them. Added the jobs to the private copy of the embedded launchd job list. The next run reached the listener but crashed while Foundation retained the exported object. A runtime-allocated Objective-C class resolved that crash. The following native client rejected CTXPCServiceSubscriptionContext inside CTXPCContexts because its decoder requires CTXPCContextInfo. Used the native context type and kept all of the client decoder checks enabled.
- Final result passed. CoreTelephony in control PID 25 and original Setup PID 65 each read slot 1, kCTSIMSupportSIMStatusReady and kCTRegistrationStatusNotRegistered, with zero errors. Matched both request PIDs and both values to the service log. The debugger independently recorded Setup entering the native getSIMStatus:error: and copyRegistrationStatus:error: methods. These calls were initiated by the diagnostic worker inside Setup. SpringBoard PID 60 independently subscribed to notifications. No modem, carrier registration, or Setup screen progression was tested.
- Used CI 42707402072 kernel and the separate GPT fixture. QEMU used -nic none, qufs0 read-only and /private/var on md0. Stopped after 221.639 host seconds with no observed kernel panic and unchanged candidate GPT, original RAM seed and kernel hashes. The builder independently checked the parent disk hashes and GPT metadata. Evidence is in outputs/duchamp-qemu-cellular-20261110, and the private reproduction is under work/qufs-gpt-cellular-20261110-v1. No phone or operator was contacted.

ACTIVE HANDOFF — Cellular service boundary verified from the saved QEMU run (2026-11-10)

- Rechecked the saved 20F66 run from a9a049a. Setup made 29 failed lookups for com.apple.commcenter.coretelephony.xpc across PIDs 63 and 65. SpringBoard made four failed lookups for that endpoint and 219 for com.apple.commcenter.xpc. Launchd returned error 3. The same root has no CommCenter job in its 15 embedded launchd jobs or its LaunchDaemons directory.
- The run configured restricted VirtIO Ethernet. The saved XNU interface inventory contains only lo0, gif0 and stf0. No cellular interface or modem is present in the guest. The saved 20F66 CoreTelephony metadata provides separate read-only SIM and registration queries that could be used to test a future isolated service implementation.
- Reparsed the saved stock Duchamp DTB with SHA-256 9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29. It identifies /soc/ccifdriver@10209000 as mediatek,ccci_ccif and /soc/dpmaif@10014000 as mediatek,dpmaif. All 22 hardware-inspector tests passed. This was an offline audit of saved files. No new QEMU boot, phone access, SIM registration, call, or cellular data session was performed.

ACTIVE HANDOFF — QEMU Setup Wi-Fi scan boundary and synthetic SSID verified (2026-11-10)

- Replayed Setup in the isolated QEMU 10.2.1 guest with the same CI 42707402072 kernel, read-only GPT qufs0 and RAM-backed /private/var on md0. The native picker showed zero SSIDs. Matched the empty framebuffer to IOSurface 5 at SwapEnd 6566.
- Setup PID 63 and its relaunched PID 65 could not resolve com.apple.private.corewifi.internal-xpc in launchd. The matching 20F66 wifid job advertises that Mach service and limits loading to wlan or marconi-wifi device-tree nodes. The test GPT root lacks both wifid and its launchd plist. The QEMU PCI network device was restricted VirtIO Ethernet, and XNU enumerated only lo0, gif0 and stf0.
- Recorded WiFiManagerClientCopyDevices returning null and WFNetworkListController taking _setupWithoutInterface. At startScanning, both interface and scanManager were null, and the scan manager start message had a null receiver. The instrumented CoreWiFi scan methods and MobileWiFi async scan entry had zero hits.
- The first synthetic injection called the unavailable WFNetworkScanRecord init and Setup restarted. Retried in the same VM with WiFiNetworkCreateWithSsid and initWithNetworkRef. The resulting one-record CFSet reached native setNetworks and cellForNetworkRecord, with the record's SSID independently read from the row object. Setup rendered Duchamp-Lab-QEMU at SwapEnd 14376 on IOSurface 5. All 3308640 active pixels matched. XNU still had zero Wi-Fi interfaces. The injection tested WiFiKitUI result display at the setNetworks boundary. Radio scanning, association and connectivity remain untested.
- Stopped the dedicated guest after 1831.818 host seconds with no observed kernel panic. The kernel, original RAM seed and GPT image kept their SHA-256 hashes. Evidence is under outputs/duchamp-qemu-wifi-scan-20261110 in the workspace, with the private harness under work/qufs-gpt-wifi-scan-20261110-v1. No physical device was used.

ACTIVE HANDOFF — Native Setup rendered the Wi-Fi picker on read-only GPT (2026-11-10)

- A cold diagnostic replay hit the 420-second scene-create watchdog while sampling CoreText glyph shaping. A saved live RAM volume was dirty and could not remount. Cloned the original clean RAM seed, copied the verified English/Algeria preferences, and changed only the Setup watchdog allowance from 400 to 1200 seconds. The replay mounted the new seed as `md0` and advanced beyond the font startup. Fixed the QEMU input harness so its timer survives the language wait and its interactive swipe counter is initialized.
- The instrumented unmodified GPT replay reproduced the post-Continue SIGABRT. UIKitCore's `UIKeyboardLocalizedSWLayoutName` tried to insert a nil value for `en_US` after looking up `KeyboardLayouts` in the missing `KeyboardSettings.bundle`. The 20F66 Info.plist and KeyboardLayouts.loctable restored the native QWERTY lookups for `en_US` and `en_GB`. This first repair exposed a separate exception in WiFiKitUI. The full guest error named `WFAdditionalSetupTableViewCell.nib`, which was missing with the rest of the framework resources.
- Installed the two keyboard files and 14 matching 20F66 WiFiKitUI resource files in a separate GPT clone, SHA-256 `12c0af3c89172abad7700ab9805b5160162ec2b4342c186190fd7a5025f104eb`. Round-tripped every installed file and verified unchanged GPT metadata and the original disk. Booted the same CI 42707402072 kernel. The guest mounted `qufs0` read-only and `/private/var` from `md0`. Setup PID 63 returned from Continue and completed WFBuddyViewController viewDidAppear. No Setup exception or kernel panic was observed in the successful run.
- Captured the native Choose a Wi-Fi Network picker at SwapEnd 3648, IOSurface 5. All 3308640 active pixels matched. Over 52 host seconds the frame remained identical and showed only Connect to Mac or PC with zero SSIDs. XNU had only `lo0`, `gif0` and `stf0` at both readings. The only QEMU network device was the restricted VirtIO Ethernet control. The test stopped after 740.616 host seconds with matching before/after kernel, GPT and RAM seed hashes. Evidence is under `duchamp-qemu-keyboard-wifi-20261110` in the workspace outputs, with the private replay under `work/qufs-gpt-wifi-ui-20261110-v1`. No physical device was used.

ACTIVE HANDOFF — Wi-Fi was unavailable in the GPT QEMU Setup guest (2026-11-10)

- Booted the same CI 42707402072 kernel and GPT disk in QEMU 10.2.1. The guest selected the same HFS+ slice, verified `qufs0` read-only and mounted `DuchampVar` on `md0`. Added an isolated VirtIO Ethernet control with QEMU user networking restricted. QMP reported it on PCI, but the XNU interface list contained only `lo0`, `gif0` and `stf0` before and after the Setup test. The local QEMU device list had no 802.11 adapter.
- Selected English and Algeria, reached Quick Start, chose Set Up Manually and reached Written and Spoken Languages. Setup PID 63 aborted with SIGABRT about 5.6 guest seconds after Continue and was relaunched. The stack reaches Objective-C/C++ termination on the main dispatch queue. The exception reason remains unknown. No Wi-Fi picker or network connection was observed.
- Stopped the isolated guest after collecting evidence, with no observed kernel panic. The GPT image, RAM seed and kernel hashes matched before and after. Logs and frame are under `duchamp-qemu-wifi-20261110` in the workspace outputs directory, with the private replay under `work/qufs-gpt-wifi-20261110-v1`. All execution was in QEMU.

ACTIVE HANDOFF — Setup reached Hello and language selection on the same GPT root (2026-11-10)

- Reused the exact CI 42707402072 kernel and whole GPT fixture from the native PID 1 proof. The guest selected block 256, verified `qufs0` read-only, and mounted `DuchampVar` on `md0`. The pinned root's fstab mounts `/dev/qufs0 / hfs ro` and `/dev/md0 /private/var hfs rw`. Data changed inside guest RAM, while the host GPT image, original RAM seed, and kernel retained their hashes.
- Rebased the verified QEMU-only software scanout and SPI2 swipe instrumentation to the CI kernel. Setup PID 63 connected to BackBoard successfully. Captured Hello at swap 193 before arming the synthetic swipe. All ten ordered digitizer events were enqueued in BackBoard PID 47. Captured the language picker, including العربية, at swap 605. Both captures passed the full pixel and IOSurface 5 checks. The run stopped at the language picker after 324.671 host seconds with no observed panic.
- Verification and both PNGs are in the workspace outputs directory `duchamp-gpt-setup-20261110`. The local replay and guest evidence are under `work/qufs-gpt-setup-20261110-v1`. The language capture is dark as rendered. All execution was inside QEMU.

ACTIVE HANDOFF — XNU mounted a GPT root on qufs0 and ran Apple launchd as PID 1 (2026-11-10)

- Wired the portable selector into the virtual BSD adapter. The QEMU ADT opts in with both `gpt-sector-size` and `gpt-root-guid`. The adapter resolves the slice before exposing `qufs0`, uses its bounds for geometry and raw/block reads, and reports selection failures without exposing the whole LUN. An ADT without those properties keeps the existing read-only whole-LUN behavior. `build-duchamp-ufs-fixture.py --gpt` produces a complete GPT test disk and matching ADT. Use a QEMU base ADT with the current GIC capability. The older multiprocess ADT stopped before storage, and the corrected control with the previous kernel reached `QEMU RAM ROOT MOUNT FAILED` on the same GPT disk.
- Full macOS XNU CI run 42707402072 at c17a595f69a184e5af35c49ee38d6d858d62d851 verified 313 build inputs. Artifact kernel SHA-256 `9ea1ed93bb392753bbb11dda532eadfbdf766118508c8cb52f4af222167fbca0`. The selected artifact source commit and manifest matched the build ref. The QEMU profile suite passed 26/26, the changed C translation units passed the saved XNU compile flags, and `sgdisk --pretend --verify` found no problems in the whole GPT fixtures.
- In QEMU 10.2.1 the new kernel selected 819200 UFS blocks at block 256 (1 MiB), registered `qufs0` as device b(2,0), and mounted HFS+ on that device. The byte-verified original `/sbin/launchd` completed early boot. Read-only GDB inspection of the running kernel's `initproc` returned `pid=1 comm=launchd` at 41.857 host seconds. `/private/var` used separate `md0` RAM. The disk, source HFS+, RAM seed, and exact kernel hashes were unchanged. Evidence and private reproducer are under `work/qufs-gpt-xnu-20261110-v1`, especially `native-verification.json`, `native-guest-msgbuf.txt`, and `native-proc-check.txt`. No physical device was used.
- The same kernel also passed the diagnostic GPT and flat-root guests with 23/23 and 22/22 checks respectively. Both matched the root device to `/dev/qufs0`, read the HFS header and test bytes, returned EROFS for write-open and reached the PID 1 heartbeat without a RAM disk or observed panic. Reports are `gpt-guest-v2/verification.json` and `flat-guest-v2/verification.json`. Early QUFS selection lines were verified from the native guest message buffer.

ACTIVE HANDOFF — Ruby-style read-only GPT root selection exercised through virtual UFS (2026-11-10)

- Continuing the Ruby-style path from the already proven Duchamp `boot_a` RAM-root service checkpoint. The virtual `qufs0` adapter currently expects HFS+ at LUN offset zero. Added a separate portable selector that checks the protective MBR, GPT header and entry CRCs, exact primary/backup table agreement, a pinned HFS partition GUID, alignment, bounds, and the HFS+/HFSX signature. Reads relative to the selected extent reject any crossing before issuing a UFS command. The selector uses the existing read-only transport and adds no physical callbacks or GPT writer.
- QEMU 10.2.1 exercised the actual virtual UFS controller via qtest, including 512- and 4096-byte GPT sectors over 4096-byte UFS blocks and a 32 MiB existing HFS+ root wrapped in a fresh 512-byte GPT fixture. The 41 GPT checks and all 777 total harness checks passed, plus 78 existing native ASan/UBSan guard checks and an ARM64 freestanding compile. QEMU returned exact first and last partition blocks. All 19 inputs remained byte-identical, and independent `sgdisk --pretend --verify` found no problems in the HFS fixture. Invalid and conflicting metadata, duplicate identifiers, overlaps, wrong type, wrong signature and out-of-range reads were rejected.
- Reproduce in WSL with `python3 tools/test-duchamp-driver-core.py work/NEW --gpt --root-image work/qemu-rootvnode-98/root-with-launchd.hfs`. The final evidence is `work/ruby-route-gpt-20261110-v3/result.json`, SHA-256 `5e00e881456d59adb9fd1b728593c67ba48eeebf2b289282ddc82661afe00d80`, plus `sgdisk-verify.txt` in the same directory. qtest ran the controller but no guest OS. Next integrate an opt-in GPT-backed root into XNU's virtual UFS adapter and boot that fixture to PID 1. Physical MT6897 UFS still needs its resource and DMA ownership contract. No phone connection or partition writes occurred.

ACTIVE HANDOFF — MediaTek V6 DA1 digest gate verified in QEMU (2026-11-10)

- The published DA_DUCHAMP_OS1.0.12.0.bin candidate SHA-256 b37df080...33969 has hardware code 0x1203, subcode 0x8a00 and hardware version 0xca00. This identifies its target family. Admission on the user's installed firmware was not tested.
- The BOOT-TO handler computes a 32-byte digest and takes its error path if it differs from the digest embedded in the exact DA1. The embedded value matches the bundled DA2 body without its signature tail (SHA-256 307a866b...bfa2). The PC/x0 diagnostic digest 2a7dff64...d20ea differs.
- Tested the exact 52 comparison bytes in an isolated ARM64 QEMU harness with host-computed digests. The first run hit a harness alignment exception. After aligning the inputs, all three cases passed. The original DA2 matched, the diagnostic mismatched and a one-byte DA2 mutation mismatched. The comparison test did not emulate the full USB command, firmware admission or handoff, and no phone commands or writes were issued. The RAM-only gate remains closed for this candidate. Evidence and replay-da1-compare.py are under work/ram-provider-sources-20261109-v1.

ACTIVE HANDOFF — Active Duchamp LK matched the offline RAM-entry audit (2026-11-09)

- Read-only ADB verified Duchamp/MT6897, boot complete, slot _a and kernel 6.1.57-android14-11-gcf2c2dc91b9e-ab11782407. The active lk_a SHA-256 matched f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a. Both CONFIG_KEXEC and CONFIG_KEXEC_FILE were unset in the running kernel. No reboot, upload, flash or partition write occurred.
- The pinned binary exposes 35 registered Fastboot commands without a RAM execution command. Resolved the separate download and continue callbacks. The latter acknowledges, sets STATE_RETURN and signals the normal boot event. The waiter uses that same event and calls boot_linux_from_storage. The auditor now checks those control-flow edges and the storage routine label against the exact image.
- Reviewed AOSP Fastboot/fastbootd and pinned MTKClient V6 (118a000a83ea31c4f427fe5225abfe964546e05e). MTKClient boot_to is reached after an accepted DA1 in its DA2 load path. A Duchamp RAM handoff provider for the diagnostic is still unproved. The provider gate remains closed.
- Both audit suites passed 12 unit tests total, and three local route mutations were rejected. Rebuilt the unchanged PC/x0 diagnostic and passed the QEMU RAM record and framebuffer checks at PC 0x40200000, x0 0x48000000 and EL1. The capture Image SHA-256 matched the prior 2a7dff64...d20ea. Evidence is under work/ram-entry-20261109-v1. No phone payload was produced or executed this turn.

ACTIVE HANDOFF — Duchamp SPI2 one-shot DMA diagnostic verified in QEMU (2026-11-09)

- The saved SPI2 DT node has no dma-coherent or iommus property. /soc/dma-ranges declares a 64 GiB identity window and the pinned MediaTek driver requests a 36-bit DMA mask. Android's 14 observed touch frames used DMA. These inputs do not establish runtime PA-to-DMA mapping, bounce use or resource/cache ownership under XNU. A read-only ADB config check showed CONFIG_SWIOTLB=y and both kexec options disabled.
- Added a single-attempt diagnostic with a trusted, boot-generation-bound resource grant and two disjoint cache-aligned 128-byte buffers. It waits for GPIO9, exchanges only the 100-byte FT3683G report and checks CRC, format and coordinates. It quarantines mappings after uncertain DMA completion. The only wired provider is a QEMU RAM simulation. The code adds no physical controller, IRQ, clock, pin or regulator implementation.
- Each of the synthetic and captured-fixture suites passed 31 scenarios under native ASan/UBSan and ARM64 QEMU. All four C units passed the saved XNU compile flags, staging was idempotent and QuFS passed 24 regression checks.
- Two CI attempts stopped before compilation because hdiutil rejected the downloaded KDK. The isolated retry installed the exact 22G74 asset after length and SHA-256 verification and checked 311 build inputs. Full XNU CI run 42580497062 head 2a52d10bac7d5a631a0d1bff891502f9b530daa0 produced kernel SHA-256 9c73b61b4aeb5fed6a1b1c61938f8fd9f86d1cbd92b8290011a88696437ad703. The full linked kernel in QEMU rejected the incomplete grant, completed six cache/barrier phases and one simulated transfer of the exact captured report, mounted the RAM /private/var and reached launchd early boot with no panic. The read-only QuFS root, seed and kernel hashes were unchanged. The corrected local QEMU overlay passed the same check, with the first overlay's printf ABI mismatch excluded from the result.
- Local evidence and reproducer are under work/spi2-dma-20261109-v1. The exact saved LK audit again found no registered RAM execution command. A physical run still needs a non-persistent entry and documented SPI2 grant, address and cache ownership. No phone image was deployed, no flash command was run and no phone partitions were modified.

ACTIVE HANDOFF — Stock Duchamp touch reports consumed by BackBoard in QEMU (2026-11-09)

- Matched the stock FocalTech and MediaTek SPI module build IDs to the saved ELF files. Calibrated the temporary trace with a ten-byte A6 read at 0x29 on the FIFO path. A 32 KiB trace lost the start of the first swipe. Repeated with a 256 KiB trace and stopped on first UP. The second capture retained 84/84 events over one 52.095 ms gesture.
- Each of the 14 physical SPI2 CS0 replies followed GPIO9 (Linux IRQ 56), a 100-byte transaction for register 0x01, the MediaTek DMA branch and SPI2 completion (Linux IRQ 462). The full RX buffer was traced after the transfer returned. Independently checked all 14 CRC-16 values and decoded the original bytes with the same FT3683G C parser. The result was one DOWN, 12 MOVE and one UP for a single contact.
- Replayed all 1,400 captured RX bytes through the linked XNU fixture, with only the fixture chip ID replies synthesized (0x1234). Used the unchanged Mach-O from macOS CI 42522493233, SHA-256 42bdd37f4f52637f1573628add1deb570a78535e71152a3a1f04e13c1b7761d2, built from 491ff8b inputs. A debugger held the test timer until backboardd mapped its HID queue. It verified the emitted contact values and that the BackBoard process advanced its queue head after every event. The first run verified all 14 events before a debugger shutdown exception. The clean repeat verified all 14 in order, exited GDB with status 0, and recorded no panic. qufs0 was read-only and /private/var used RAM. The kernel, root and seed hashes were unchanged.
- Local capture and replay evidence is under work/duchamp-touch-20261109-v1. Start with android-verified.json, qemu-verified.json and backboard-events.jsonl. The stock trace establishes the DMA path in Android. The remaining phone boundary is a documented MT6897 SPI2 DMA, IRQ, cache and resource ownership contract under XNU. Temporary tracing was removed from Android. No flash or phone partition write was performed.

ACTIVE HANDOFF — Duchamp FT3683G ID and SPI2 resources measured on stock Android (2026-11-09)

- ADB detected one authorized Android device. Root confirmed duchamp/mt6897, matched all 19 DT properties and both pinned loaded module notes, and resolved focaltech_ts at spi2.0 to mtk-spi at 11012000.spi2. Fixed the probe's stock driver name and skipped the unbound SPI master ancestor which shares the controller OF node.
- The fts_boot_mode attribute reflects the software debug flag, which was false on the working device. The stock read-only A6 firmware version returned 0x29. The saved ELF and the running handler rejected the short register syntax, even as a single write. The corrected probe uses the read-prefix/one-byte-length form, 1A301 LF and 19F01 LF, buffered into one write per request. No controller register writes, reset, update, or module load was performed by the probe.
- Fresh stock-driver reads returned A3=56 and 9F=72, confirming application-mode ID 0x5672. A temporary filtered tracefs instance recorded all three 10-byte transfers. Independently validated RX status and CRC for A6, A3 and 9F, and matched enable/disable events for univpll_d6_d2, spi2_sel and peraop_spi2_bclk around each transfer. SPI2 runtime PM was suspended at idle before and after. The driver reports a 15 MHz ceiling; no physical SCLK rate was measured.
- Vendor pinctrl reported GPIO11–14 in mode 1, GPIO60 reset and GPIO73 AVDD enable as high outputs, and GPIO9 as an input mapped to Linux IRQ 56. Regulator sysfs reported mt6368_vtp enabled at 1,800,000 uV with one user. The trace instance was removed and debugfs remained unmounted. No reboot, flash or partition write occurred. Stock Android evidence does not establish clock or power ownership under XNU.
- Evidence hardware-confirmed.txt and hardware-verified.json is under work/spi2-live-14480529-100451-359. The final tool preflight succeeded on Android and 17 local mock cases passed. The standalone RAM boot gate and physical 100-byte touch report path remain separate.

ACTIVE HANDOFF — MT6897 SPI2 resources verified and stock Android FocalTech ID probe prepared (2026-11-09)

- Re-read the saved Duchamp DTB 9c49589f...1d29 and checked 19 exact properties, including SPI2 at 0x11012000/0x100, CS0, topckgen parent/mux IDs 140/72, pericfg_ao gate 14, pinmux mode 1 on GPIO11–14, GPIO60 reset, GPIO9 IRQ and MT6368 VTP at 1.8 V. The separate analog enable is GPIO73 active high, consumed through goodix,avdd-gpio by the stock FocalTech driver. The checked DTB and pinned vendor source describe the wiring and the stock Linux clock/resource path. Actual clock enable state, physical rail voltage and post-handoff ownership are unmeasured.
- The saved focaltech_touch.ko build ID ee808717...2a85 reads application registers A3 and 9F and checks 0x56/0x72. Boot-mode ID 0x36B3 is a separate signature; the cached model ID is insufficient proof of live register reads. The saved MediaTek SPI module build ID is 0e21c143...2783. The pinned drivers use mode 0, eight bits and a 15 MHz DT ceiling. Each ID frame is ten bytes and fits the 32-byte FIFO, independent of the 100-byte touch report path.
- Added tools/probe-duchamp-spi2-id.py and duchamp/MT6897-SPI2-ID-PROBE.md. The host streams the check into already running rooted Android, verifies the exact DT binding, loaded module IDs and bound fts_ts/mtk-spi owners, and prints available read-only resource snapshots. Explicit --read-id additionally checks the firmware mode and awake state, then sends only A3 LF and 9F LF to the stock driver's volatile sysfs read-command path. No new module, partition, power, reset or firmware operation is performed by the diagnostic.
- Local test results were 14/14 mock probe cases and 22/22 existing DT inspector tests. Running the default ADB preflight returned no devices/emulators found, so no hardware ID or live resource state was measured. The exact saved LK audit again closed the standalone RAM-launch gate with no registered fastboot boot or memory execution command. No phone image was created or flashed. Logs and pinned source extracts are under work/spi2-hardware-20261109-v1.

ACTIVE HANDOFF — Full XNU build from 491ff8b inputs passed FocalTech SPI2 QEMU replay (2026-11-09)

- GitHub Actions XNU run 42522493233 completed successfully on macOS. Used the isolated CI ref codex/xnu-spi2-491ff8b at a2291b6 over the previously published base. The helper ref contains the build inputs from 491ff8b and CI-only metadata. All 308 build input files were verified byte-for-byte against 491ff8b; unrelated local commits and uncommitted files were left out of the CI ref. The expired IIG archive 13098010906 was replaced for this run by 13282566232. Verified 39 IIG inputs and 34 generated files byte-for-byte against the saved original, and pinned the replacement archive digest.
- Kernel artifact 13634715679, SHA-256 42bdd37f4f52637f1573628add1deb570a78535e71152a3a1f04e13c1b7761d2. Verified normal linked calls from SweetHIDButtons::testFired to the compiled adapter, from the adapter to both FocalTech protocol entry points, and from the adapter to SweetHID. Booted the extracted Mach-O in QEMU using the standard payload builder, with no injected code or binary overlay. The debugger deferred the test timer until the first Setup frame. The driver read the synthetic wire replies and emitted the gesture from its linked code. qufs0 was read-only and /private/var was mounted on the RAM disk.
- The first QEMU run stopped at a stale debugger guard for the relocated memmove call. Verified the new call target and corrected the debugger guard for the second run while keeping the kernel artifact unchanged.
- The full kernel read synthetic ID 0x1234, rejected one corrupt CRC, and matched 10/10 ordered HID dispatches to BackBoard (PID 47) enqueues. The native Setup language list appeared after the gesture. SwapSetLayer and SwapEnd 647 agreed on IOSurface 5, with the 1220x2712 framebuffer matching the software source. Runtime 298.258 host seconds. The kernel, root image and RAM seed retained their input hashes, and no kernel panic was seen.
- Reproduction scripts, build input verification, validated trace and the Setup framebuffer PNG are under work/spi2-full-491ff8b-v1. The actual chip ID and physical SPI2 transport still require hardware validation. This turn did not contact the phone or write any phone partitions.

ACTIVE HANDOFF — Duchamp FocalTech SPI2 replay reached BackBoard in QEMU (2026-11-08)

- Wired the portable FT3683G protocol into the existing XNU SweetHID timer and touch service. The replay is opt-in with `sweet-qemu-spi2=1`, `sweethidtest=15`, a Cortex-A76 QEMU CPU and the synthetic ADT node generated by `tools/duchamp-qemu-spi2.py`. The generator accepts only the virtual split-root profile, rejects duplicate fixtures, and preserves existing output files. The provider returns raw synthetic wire replies; the driver performs ID register reads, status and CRC validation, high-resolution decoding and coordinate conversion before calling SweetHID.
- Repeated staging against the saved XNU build tree; it made no additional changes. Both C sources and the modified SweetHID.cpp compiled individually for the ARM64 kernel, using the repository's Apple-builtin fallbacks for the local C++ check. The FocalTech core passed 131 checks each on the host and in ARM64 QEMU, and the existing QEMU UFS profile passed 24 checks. No full macOS CI build was run for this change.
- For the executable QEMU test, linked the two C sources into an overlay on pinned kernel CI 41543710742 (base e465723a...182b, overlay 646f9f50...b93c). The first run passed ID and CRC checks but consumed the gesture before BackBoard was ready. In the second run, GDB parked the original timer before its first callback and armed the fixture once after the Hello capture. GDB supplied timing only; the kernel driver generated the touch events from the ADT wire replies. QuFS qufs0 was read-only and /private/var was on md0 in RAM. Both input images retained their hashes.
- The second run read synthetic ID 0x1234, dropped the one CRC-corrupted report, and matched 10/10 ordered HID dispatches with enqueues to BackBoard (PID 47). Setup (PID 63) moved from Hello to the language list. SwapSetLayer and SwapEnd 625 agreed on IOSurface 5, and all 3,308,640 active pixels matched the software output for that swap. The run stopped after 313.333 host seconds with no kernel panic. Replay scripts, trace, validated framebuffer PNG and spi2-validation.json are under work/qemu-spi2-touch-20261108-v1.
- Real SPI2 remains to be verified. The next hardware boundary is documented clock/pin/reset/supply ownership and a bounded 10-byte ID transaction. The 100-byte report additionally needs verified DMA ownership or a demonstrated PIO sequence preserving chip select across the 32-byte FIFO. This turn did not access the phone, flash, write partitions, or issue phone MMIO.

ACTIVE HANDOFF — Duchamp touchscreen wire protocol and peripheral DT dependencies (2026-11-08):

- The saved Duchamp FDT 9c49589f...1d29 identifies focaltech,n11a-3683g-spi under SPI2 at 0x11012000, chip select 0, up to 15 MHz, ten contacts and a coordinate resolution factor of 16. GPIO 60 is reset, GPIO 9 is the touch interrupt, and IOVDD resolves to the VTP regulator. The pinned vendor_boot d1d1887e...3e49 contains focaltech_touch.ko bff6726d...7e3f (GNU build ID ee8087174b06587905ce285014b589105a892a85) and spi-mt65xx.ko 78207312...62f6. This is saved-image evidence. The focaltech module was present but absent from the archived modules.load list. No installed runtime touch chip ID was measured.
- Added duchamp_ft3683g.c/.h with the pinned module's read-only SPI envelope. The IRQ path at 0x41c4–0x41e0 reads 91 bytes from 0x01. fts_read at 0x23b84–0x23ce0 supplies the 0xa0 command, three dummy bytes, payload at byte 7, status mask 0xa0 and reflected CRC-16 0x8408 with a 0xffff seed. The dispatch at 0x4818 selects standard six-byte and extended eight-byte point records. The DT factor 16 excludes the separate factor-10 branch. The portable core also reads the two chip-ID registers 0xa3 and 0x9f using two ten-byte transfers, with no firmware bootloader entry. It keeps native units and rejects corrupt reports before changing the caller's output.
- Added --peripherals to the existing offline hardware inspector. The optional report resolves the touch SPI clocks/pins/IRQ/supply, two DSI panel candidates, MTU3/xHCI PHYs, Wi-Fi/BT/conninfra, audio and MT6368 codec, four camera sensors and I2C controllers, and modem data/control nodes. Bus endpoint addresses are separate from controller MMIO ranges. The original UFS/GPU report stayed byte-identical for the saved DTB. These declarations do not assert ownership or provide peripheral drivers.
- Native ASan/UBSan and ARM64 QEMU each passed 131 FocalTech checks with a synthetic SPI peer, covering chip-ID reads and CRC errors, standard/extended reports, ten contact slots, malformed input and unchanged outputs on failures. The inspector passed 22 tests and the actual saved DTB passed 17 follow-up assertions. Existing QEMU UFS profile checks passed 24/24 and UFS ownership checks 9/9. The physical UFS gate still denies the current evidence. No phone, flash, device MMIO, CI build or partition access.
- Replay, pinned module metadata, local disassembly, hardware-with-peripherals-v2.json and ft3683g-test-v2/result.json are under work/duchamp-peripherals-20261108-v1. Keep extracted modules and the DTB outside Git. Next touch boundary: provide the actual MT6897 SPI2 clock/pin/GPIO/power path for a ten-byte ID read. The pinned MediaTek SPI driver selects DMA for aligned transfers above its 32-byte FIFO, so the 100-byte report path still needs verified DMA ownership or a demonstrated PIO chip-select sequence. The decoder is not connected to XNU's HID path yet.

ACTIVE HANDOFF — QEMU split-root Setup reached Quick Start (2026-11-08):

- Reproduced dmd PID 25 SIGABRT at guest 41.407209 seconds. The read-only GDB trace caught NSInvalidArgumentException with `CoreData: Cannot load NSManagedObjectModel.  nil is an illegal URL parameter`. The caller at native dmd image base + 0x573a0 is DMDPolicyPersistence, which looks up DMDEffectivePolicies.momd before passing the resulting URL to initWithContentsOfURL:. Installed 11 original 20F66 DeviceManagement.framework resource files, including that model and DMDConfigurationDatabaseModel.momd, into a fresh qufs0 clone. Verified HFS byte readback and kept the executable unchanged. An isolated forced-start probe stopped after a separate store-URL exception without a recorded abort. The normal on-demand replay below is the end-to-end result.
- With the original 120-second Setup watchdog, dmd stayed up through Setup relaunches, but Setup hit the scene-create and process-launch timeouts before a captured screen. In a separate 64 MiB RAM seed changed only the app-specific FBLaunchWatchdogExceptions entry for com.apple.purplebuddy from 100 to 400. Reused the pinned CI 41543710742 kernel, 2 GiB guest window, QEMU-only user/501 session correction and software scanout. The QEMU block root logged readonly=1 and md0 mounted DuchampVar. Both input hashes matched at shutdown.
- The extended replay ran native dmd PID 62 on demand in user/501. It created the configuration and policy databases on RAM and exited normally with status 0. Setup PID 63 received a successful BackBoard display reply. Fourteen virtual digitizer samples reproduced Hello, English, and Algeria. The final RAM image contains AppleLocale=en_DZ and AppleLanguages=[en-DZ].
- Native Setup rendered Quick Start after selection. Captured the 1220x2712 frame from guest RAM. BackBoard SwapSetLayer used layer 0 / IOSurface 5, SwapEnd 1137 presented surface 5, and the hash of all 3308640 active pixels matched the software scanout output recorded for that swap. The run stopped after 484.713 host seconds without kernel panic. All 24 virtual UFS profile tests passed. No phone access or partition changes.
- Evidence and replay inputs are under `work/setup-qufs-dmd-20261108-v1`. The Quick Start image is `extended/live-swap-1137.png` with `extended/live-swap-1137.json`, and the final data RAM and exact raw frame are in the private Ubuntu run directory recorded in `staging-path.txt`. The run stopped on Quick Start before Set Up Manually.

ACTIVE HANDOFF — QEMU split-root Setup selected English and Algeria (2026-11-08):

- Cloned the known Hello qufs0 image 7f842de8, added and byte-verified 30 pinned 20F66 fallback fonts and the original three-file HID event service plugin, then attached the 3.125 GiB clone read-only. The original root and the 64 MiB md0 seed stayed byte-identical. Both QEMU runs used the 2 GiB XNU window, writable /private/var on RAM, and CI 41543710742.
- The first run delivered all 14 digitizer events to BackBoard. Ten samples swiped from Hello to the language list. The next two selected English, then a two-sample tap selected Algeria. The stopped data RAM contains AppleLocale=en_DZ and AppleLanguages=[en-DZ]. Frame verification passed for Hello 220, language 1075, country 1246, and Algeria selected 1255. All four use IOSurface 5 and match five sampled rows and all 3308640 active pixels. The last visible screen is still the country picker with Algeria highlighted.
- Setup PID 62 was sampled in BFFFlowStarter controllerNeedsToRunForClass: and repeatedly looked up com.apple.dmd without a provider. A separate read-only clone added the original signed 20F66 dmd binary, job, and DeviceManagement framework metadata, with all 45 direct dependency names present in the shared cache. Native dmd execed in user/501 but at least three instances exited on SIGABRT. Setup PID 64 connected to BackBoard and hit the existing 120-second scene-create watchdog before an eligible frame in that retry. The exact dmd abort cause and the next Setup screen remain unverified.
- The first run stopped after 638.138 host seconds and the second after 370.216. No kernel panic was seen and the input images and seeds retained their hashes. All 24 virtual UFS profile tests pass. The capture, reports and logs are under `work/setup-qufs-country-20261108-v1`. No phone access or partition changes.

ACTIVE HANDOFF — Setup Hello on QEMU read-only qufs0 with RAM data (2026-11-08):

- Replayed CI 41543710742 kernel e465723a on QEMU Cortex-A76 with a 2 GiB guest memory window, read-only 3 GiB qufs0 and writable 64 MiB HFS+ md0 mounted at /private/var. The wide direct-launch control still showed a native LaunchServices containerized scan blocked in a semaphore wait. In the gated control, native lsd received the probe request but waited for the database to finish seeding. Launchd tried com.apple.MobileInstallationHelperService and reported the executable missing with ENOENT/exit 78.
- Installed four matching 20F66 MobileInstallation framework/XPC bundle files into a fresh copy of the gated root and byte-verified the HFS readback. The successful pair used the same seed, including the genuine migration plist from the previous successful datamigrator. The 192864-byte native helper SHA-256 is a0e27596d2600b13c5d51024ab1ed38194ffe0a9c621291ed82b2cf6b862dc7b. All 16 direct library install names are in the pinned shared cache. The same launchd job now execed helper PID 42. Native lsd replied with status 256 and completed registry rebuild. The mobile client verified the installed SpringBoard record and two successful BackBoard queries before starting SpringBoard.
- Original cfprefsd PID 36 was running. SpringBoard PID 58 reached its main run loop and Setup transition, with new preferences visible on md0. Native Setup PID 62 ran in user/501 and connected to BackBoard PID 47 with status 0. The first verified Hello framebuffer was captured at SwapEnd 218, IOSurface 5, layer 0, after 246.631 host seconds. Five sampled rows and all 3308640 active BGRA pixels matched the scaled native software source. The saved 1220x2712 PNG SHA-256 is e683ae34fd32a762a8619ec032d2dec0cba10698eb5d16ac33f017a549f1843c.
- Results, replay script, local staging path, verification report and PNG are in `work/setup-qufs-cfprefs-20261108-v1`. The replay reused the QEMU-only session correction, manual Setup and software scanout hooks and the scoped development launchd cache. The physical XNU kernel and phone configuration were not changed. The root and RAM seed hashes matched before and after. All 24 existing virtual UFS profile tests pass. No phone access or partition changes.

ACTIVE HANDOFF — QEMU split root UI replay result (2026-11-08):

- Final 20F66 replay mounted qufs0 read-only and a 64 MiB writable HFS+ md0 at /private/var. Native SpringBoard PID 26 and backboardd PID 27 both ran as UID 501. BackBoard produced three QuartzCore context commits. Adding the original DataMigration XPC bundle and wrapper resolved the prior xpcproxy ENOENT. The native datamigrator executed as PID 35 and exited with status 0.
- At 1235.097 host seconds the test timed out with no panic observed. There was no Setup exec or matching framebuffer presentation. The captured SpringBoard stack shows a synchronous wait for user cfprefsd in MediaAccessibility. A separate FrontBoard thread was waiting while LaunchServices was reseeding its database. A late failed profiled.public lookup is also logged. The trace does not prove which dependency prevents Setup from starting. GDB reported a detach error during shutdown after recording the trace.
- Source, test root and data seed hashes stayed unchanged. New guest data was captured from RAM only. The scoped UI configuration and development cache mode are local QEMU test settings. See `work/setup-qufs-var-ram-20261108-v1/verification.json` and the migration replay evidence. No phone access or partition changes.

ACTIVE HANDOFF — Writable QEMU /private/var with read-only qufs0 (2026-11-08):

- Commit e925867 adds explicit `--ufs-var-ramdisk` for a bounded HFS+ data-only payload, with the strict read-only qufs0 gate retained. All 24 profile tests pass. The pre-existing framebuffer result edit in qemu-sweet.py remains unstaged.
- Cloned the pinned 20F66 root and formatted a 64 MiB HFS+ data seed with the fixture's /private/var ownership and contents. The local fstab mounts qufs0 read-only at / and md0 read-write at /private/var. QEMU and XNU both verified the split. A stopped RAM snapshot contains the newly created syslog socket and launchd logs. Root copies and data seed hashes match their pre-run values.
- The first UI harness stopped on missing scan directories on the read-only root. An independent clone precreated them and proved logd, containermanagerd, installd and native lsd identities. The optional readiness client waited for a native Mach reply beyond the controller deadline. A direct fixture cache replay started SpringBoard PID 26 and backboardd PID 27 as mobile. BackBoard posted DisplayChanged and produced three native QuartzCore context commits. No Setup frame was seen in that replay. Native xpcproxy reported datamigrator ENOENT and exited 78.
- Added the matching native DataMigration service and wrapper to another independent read-only root for the next QEMU replay. The local 20F66 development cache option and scoped UI launch configuration are test-only. Verification and local receipts are under `work/setup-qufs-var-ram-20261108-v1`. No phone access or partition changes.

ACTIVE HANDOFF — Native launchd early boot complete on QEMU qufs0 (2026-11-08):

- The unchanged mount fixture completed mount-phase-2 and started the init-with-data-volume task. Native launchd then panicked at missing required /usr/libexec/cc_fips_test after 174.553 host seconds.
- In a fresh 3 GiB read-only HFS+ copy, installed hash-verified 20F66 cc_fips_test and dirs_cleaner, with their libSystem dependency in the existing dyld cache. Corecrypto POST returned true and all tests passed. Launchd advanced beyond dirs_cleaner despite its read-only temp-directory warning, then panicked at missing launchd_cache_loader after 198.435 host seconds.
- In another fresh copy, installed hash-verified original launchd_cache_loader, /System/Library/xpc/launchd.plist and its detached signature. For the QEMU development replay only, the payload used native launchd_unsecure_cache=1, so normal AMFI cache verification was outside the test. No native executable, cache file, kernel, ADT or filesystem policy was patched.
- The final run logged Early boot complete at 00:02:12.341834 guest time, created user/501 and began bootstrapping and importing native service jobs. It reached the 330-second runner budget with no panic observed in framebuffer samples (332.737 seconds reported). BackBoard, SpringBoard and a Setup display were not verified. The logger socket and writes under /private/var returned EROFS. Give the QEMU guest writable data in a separate fixture before retesting the UI. Physical MT6897 root delivery remains unresolved.
- All three runs used qufs0 read-only with no RAM disk. Every test image kept its pre-run SHA-256 and all 20 existing virtual UFS profile tests passed. No phone access or partition changes. Evidence is in `work/setup-qufs-after-mount-20261108-v1/verification.json`, with per-run console captures and input receipts. Keep the local Apple artifacts out of git.

ACTIVE HANDOFF — Native mount-phase-1 on the separate QEMU Setup root (2026-11-08):

- Extracted original 20F66 `/sbin/mount` and `mount_hfs` from the pinned complete restore DMG. Installed and hash-verified them in a new 3 GiB HFS+ copy of the successful fsck fixture. `/sbin/mount_hfs` is a byte-identical regular copy of its original symlink target. All direct Mach-O libraries, including MediaKit and libutil, are in the existing 20F66 dyld cache.
- Control with unchanged CI 41543710742 kernel and ignition-level-1 payload ran stock `mount -P 1` through launchd. The fixture had no fstab. Native mount_hfs attempted a writable root update, returned EROFS, and mount exited with status 1 at 151.761 host seconds.
- A second independent copy added only `/private/etc/fstab` with `/dev/qufs0 / hfs ro 0 1`. The original mount, launchd, fsck and Setup executable stayed byte-identical. Native mount reported `/dev/qufs0 on / (hfs, local, read-only, noatime)`. Launchd accepted the required phase-1 task, ran subsequent tasks, and started mount-phase-2 at 00:01:22.908288 guest time. The QEMU harness stopped at that marker after 150.983 host seconds with no panic observed. Phase 2 completion and Setup UI were not tested.
- Both replays used read-only virtual UFS without a RAM disk. The source and both test image hashes were unchanged by QEMU. All 20 existing virtual UFS profile tests passed. No phone access or partition changes.
- Evidence is under `work/setup-qufs-mount-20261108-v1/verification.json`, `run/fb.txt` and `fstab-readonly/run/fb.txt`. The passing image is `/home/mehmedamir/.cache/duchamp-qemu-tests/setup-mount-20F66-3fVzRQ/root-mount-fstab-ro.hfs` in Ubuntu WSL. Keep the original Setup root and the Apple binaries out of the index.

ACTIVE HANDOFF — Native fsck on the separate QEMU Setup root (2026-11-08):

- Extracted native `/sbin/fsck`, the original HFS checker and its bundle Info.plist from the complete 20F66 restore DMG. Installed and hash-verified them in a separate 3 GiB HFS+ copy. The local HFS editor cannot create symlinks, so `/sbin/fsck_hfs` is a byte-identical regular copy of its original target. All direct Mach-O libraries are present in the existing 20F66 dyld cache. Setup, launchd and the main cache file matched the original fixture.
- Replayed CI 41543710742 with the same ignition-level-1 payload, no RAM disk and read-only virtual UFS `qufs0`. Native launchd ran the required `/sbin/fsck -qL`. The tool printed `failed to get filesystem info` and then reported skipping the OS container check in this boot environment. Launchd advanced to the next required task, proving it accepted fsck completion. The fsck exit code was not independently captured and this did not exercise a full disk check.
- The run stopped after 156.859 host seconds at `mount-phase-1` because its native executable `/sbin/mount` is missing. The embedded launchd config invokes `mount -P 1`. Setup UI was not reached. All 20 existing virtual UFS profile tests passed. Both disk images had unchanged SHA-256 hashes after the run. No phone access or partition changes.
- Evidence and input hashes are in `work/setup-qufs-fsck-20261108-v1/verification.json` and `run/fb.txt`. The disposable image is `/home/mehmedamir/.cache/duchamp-qemu-tests/setup-fsck-full-20F66-Py1Fb3/root-fsck.hfs` in Ubuntu WSL. Keep the original Setup root and all Apple artifacts out of the index.

ACTIVE HANDOFF — Setup root on separate QEMU storage (2026-11-08):

- Mounted the exact 3 GiB 20F66 Setup HFS+ fixture as read-only virtual UFS `qufs0`, without md0. XNU retained the 512 MiB high-RAM window at 0x1c0000000 and its payload measured 16,715,616 bytes. The 3.04 GiB from the previous turn included boot data for the embedded layout. Only QEMU storage was used.
- Diagnostic run PASS 6/6 in 135.175 host seconds. A static fork/exec parent in a disposable disk copy started a native dyld child. The child read all 2,091,200 bytes of the original Setup executable and verified the expected SHA-256, mapped the exact 20F66 cache UUID E5420DB3-30D0-33AA-8B7E-05B5038BB46D, and loaded the original framework/ObjC probes. A creation attempt returned EROFS. Source and diagnostic disks stayed byte-identical to their pre-run hashes. All 20 existing QEMU UFS profile tests pass.
- The unchanged original-root trial did exec native launchd as PID 1 but reported preboot error 25 and later a required fsck boot-task panic. The `ignition_level=1` replay opened the shared cache directory and completed ignition, then also hit missing `/sbin/fsck`. The exact boot task is `fsck -qL` with RequireRun and RequireSuccess in the native launchd config. No native Setup UI launched. An extra legacy shared-cache fixture control reached its 85-second budget without its PASS marker. The actual Setup-root diagnostic completed independently.
- Evidence and reproduction inputs are under `work/setup-disk-root-20261108-v1`. See combined `verification.json`, `diagnostic/verification.json` and both native framebuffer logs. Physical phone UFS, resource ownership, and any writable state integration remain outside this result. No phone access or partition changes.

ACTIVE HANDOFF — Duchamp phone boot resumed (2026-11-08):

- The last physical milestone remains the photographed combined launchctl/syslogd/notifyd PASS on the 32 MiB RAM root, followed by verified Android restoration. Read-only ADB and Fastboot enumeration detected no device in this turn. The two saved stock boot_a copies still hash to 1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12 and the tested service image to 545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8.
- mkpayload now checks the aligned md0 placement, updated ADT and boot-args page before reading the RAM disk. Both boundary tests passed. The real 3 GiB Setup HFS root requires 3,260,481,536 bytes including boot data and was rejected against the 536,870,912-byte phone ADT window before any output file. This is a limit of the current profile, not a measurement of total phone RAM.
- Fresh local evidence in `work/phone-return-local-20261108-v1`. Packaging passed 12/12 including bootshim-to-XNU QEMU entry, byte comparison, LZ4 and AVB checks. The generated service boot image is byte-identical to the November 6 trial. A separate fresh QEMU service replay passed 74/74 in 71.346 host seconds. All 17 existing offline phone-readiness tests pass. Physical UFS/firmware ownership stays gated. The GUI needs a verified way to supply its larger root; no phone boot or write in this turn.

ACTIVE HANDOFF — QEMU one-vs-two vCPU Setup replay (2026-11-08):

- Ran sequential isolated Ubuntu QEMU TCG tests with the same pinned CI 41543710742 XNU, HFS 20F66 root and 120 Hz display setting. Only the test payload accepts QEMU Aff0=1 and starts CPU 1 by PSCI HVC. The first two baseline attempts hit XNU interrupt-hygiene panics. The final pair used the same QEMU-only trace mode, verified in guest RAM. The benchmark had a 2304 MiB cgroup limit. Its memory pressure threshold changed during boot, so these are not matched boot-speed measurements.
- The 1-vCPU kernel verified 1/1 CPUs and SGI1. Setup PID 38 connected to BackBoard with status 0 in user/501. The kernel message buffer records the app's 120-second process-launch watchdog exit, reason 0x8BADF00D, before a country frame. The 2-vCPU kernel verified 2/2 CPUs and SGI1, started SpringBoard, and hit a ticket spinlock timeout with CPU 1 as owner. The lock is `pset0.sched_lock`, verified by the pinned Mach-O symbol and the `pset_init` call to `lck_ticket_init` at offset 0x100. The underlying cause of the lock stall is not determined.
- Neither disposable session reached the comparable touch gate. Zero drag samples and no touch-speed conclusion. JSON evidence is in `work/duchamp-qemu/setup-touch-smp-comparison-20261108.json` beside the checkout. Full logs are in `/home/mehmedamir/.cache/duchamp-qemu-tests/smp-touch-pair-gicudhpe` inside Ubuntu. No tracked kernel change. The original Windows QEMU 2540 and the two already-open Setup processes (Windows 9276 and Ubuntu 733) kept their start times. The existing viewer on port 18291 still returned input-ready. No input was sent to the open sessions.

ACTIVE HANDOFF — QEMU test storage cleanup (2026-11-08):

- Removed 27 generated root and final RAM-disk images from superseded Windows QEMU runs in the platform-services, shared-cache and UI-readiness families. Each removal had a completed run report and a tracked-file check. The immediate measured C: gain was 41.12 GiB. Newest versions and run logs remain.
- Removed 49 generated images and RAM backing files from explicit completed Ubuntu QEMU runs, totaling 161.07 GiB in Linux allocations. Retained the pinned 20F66 watchdog root, Setup v6, font/HID/HFS launcher inputs, latest successful platform and compositor runs, and the recent SMP probes. After Ubuntu became idle and stopped on its own, the built-in WSL compactor completed and reduced the VHDX from 295.25 to 148.55 GiB. Ubuntu restarted normally and the retained Setup root still reads as HFS Plus. C: later measured about 258 GiB free, including free-space changes beyond the 41.12 GiB Windows cleanup and 146.70 GiB VHDX reduction.
- Native Windows QEMU PID 2540 kept its original start time. The old viewer/mouse relay was already absent before cleanup and is still unavailable. No QEMU or phone restart. Device backup directories were outside the deletion allowlists. Verified the separate local boot_a, boot_b and lk_a files still exist. The full DFTPRO Duchamp archive seen during the earlier disk inventory was absent at post-cleanup verification and was not found by name in readable local locations. Its path was outside this cleanup; its current location is unknown.

ACTIVE HANDOFF — QEMU SMP touch comparison (2026-11-08):

- The original native Windows QEMU process 2540 stayed running with `-smp 1` throughout the separate tests. The full Setup staging test exhausted host disk space and Ubuntu WSL stopped, taking the original loopback viewer, input bridge and debugger endpoints with it. Ubuntu starts again after host space recovered. The previous tmpfs session directory and its connections are gone. No restart was issued to QEMU 2540. A read-only capture from its BackBoard software surface shows the Arabic country picker and the language settings loading overlay. See `work/duchamp-qemu/setup-original-2540-retained-20261108.png` beside the checkout. The capture is static and the mouse connection is unavailable.
- Tested pinned XNU CI 41543710742 on QEMU 10.2.1 with a separate RAM-only boot fixture. Baseline `-smp 1` reached BSD with one active CPU. The unmodified `-smp 2` kernel rejected CPU 1's QEMU MPIDR `0x1` at SweetCPU.cpp:108, leaving one active CPU and IOKit CPUs-running unset. This is a topology check in XNU.
- A local, byte-checked QEMU-only binary prototype accepted CPU 1's affinity and invoked PSCI CPU_ON via HVC for that CPU. It reached BSD. Saved guest RAM independently shows `real_ncpus=2`, `gCPUsRunning=1` and registered per-CPU data with signaling enabled for both CPUs. The comparable one-CPU and prototype two-CPU diagnostic boots both stopped at the legacy 32 MiB HFS root mount failure. The prototype is an experiment, with no tracked kernel or phone-path edits.
- The 20F66 Setup test failed before starting its QEMU process while copying the large RAM-root to a disk-backed image (`OSError [Errno 5] Input/output error`). Host C: was nearly full. The partial 10 GiB sparse staging file was deleted after WSL returned. There is no valid one-vs-two-vCPU touch timing result. Keep the original process intact. Retry the UI benchmark only with adequate host disk and memory headroom or a proven lower-footprint staging path. Use identical root and input for both counts. Test artifacts are in `/home/mehmedamir/.cache/duchamp-qemu-tests/smp-touch-9i8x08ci` under Ubuntu WSL.

ACTIVE HANDOFF — live CPU and interrupt verification (2026-11-08):

- Native QEMU PID 2540 is still the original Windows Setup session. The active command uses Cortex-A76, one vCPU and GICv3. XNU machine_info and real_ncpus independently report one CPU. Verified the registered SweetCPU object's vtable, IOKit cpusRunning and the CPU0 SGI signal flag in guest RAM. The timer IRQ witness is set for INTID 27 and the configured guest timebase is 62.5 MHz.
- The active GUI fixture still carries qcom,kryo470 in its legacy ADT. The pinned XNU binary matches that name and arm,cortex-a76/arm,cortex-a510/arm,cortex-a715 to the same SweetCPU class. The separate boot-profile generator emits matching Cortex identifiers. Its 24 tests and the six QEMU RAM loader tests passed.
- The saved phone FDT hash matches the pinned capture. Its eight CPU reg values identify four Cortex-A510 and four Cortex-A715 cores, and its PSCI method is smc. This check was read-only, and did not test secondary CPU startup on hardware.

ACTIVE HANDOFF — live Windows Setup navigation recovered (2026-11-08):

- Preserved native QEMU PID 2540 and Setup PID 37 in run `setup-run-desktop-20261107-221715-3744`. The frozen source buffer matched SwapEnd 908. The first 42 HID submissions reached the BackBoard client with zero drops and an empty ring.
- Setup's main thread was blocked in dispatch_sync while the skip-keys block waited indefinitely for the missing com.apple.dmd service. The first one-shot signal exposed a second wait at the same call site. In guest RAM only, used the 20F66 CoreFoundation empty NSArray for BuddyDeviceManagementSupport._skipKeys, balanced the matching libdispatch counter and signaled the verified XNU semaphore. Restored and read back the original HID callback. Set the existing console mute flag so diagnostic text no longer paints over the GUI.
- IOSurface 5 resumed scanout at SwapEnd 935 with changed pixels and matching row samples. A diagnostic mouse drag at steps 47–53 reached BackBoard while the country rows remained fixed. Setup later applied the user's earlier mouse selection. Verified BuddyProximitySetupController owned the active view and saw Quick Start in live scanout. Subsequent user clicks reached Written and Spoken Languages in the same session. Left the user's navigation intact, so country-list scrolling after recovery was not verified.
- The live repair was scoped to this disposable RAM guest. A reproducible fix for future boots is still pending. No QEMU restart or phone access.

ACTIVE HANDOFF — touch queue verified in the running Windows Setup session (2026-11-08):

- In native QEMU PID 2540, BackBoard opened the HID service with the verified 20F66 IOHIDEventServicePlugin. The desktop viewer input path sent a controlled down, six moves, and up at steps 19–26. Every sample reached the dispatch and enqueue trace sites with one attached client.
- Confirmed the live guest queue counters with read-only Windows process memory and the pinned XNU page tables and object layouts. The digitizer client had 26 enqueue attempts, zero drops, and matching queue head and tail of 6240 in a 16,384-byte ring. The consumer drained the queue.
- The controlled drag did not change the visible country list or cause a new Setup presentation. The cached viewer frame stayed at generation 1794090289222650965 while the actual scanout contained console text. Some earlier desktop taps were followed by presentation; the cause after queue consumption is still open. The live guest was preserved.


ACTIVE HANDOFF — 120 Hz applied in the Windows Setup session (2026-11-08):

- With the user's approval, stopped the previous 60 Hz test and relaunched native QEMU from e618302. PID 2540 loaded both 8,333-microsecond AppleCLCD timer instructions, independently verified by reading their bytes from the running process. The run is setup-run-desktop-20261107-221715-3744.
- Setup connected to BackBoard on port 5635 with status 0. The country picker was visible in the live framebuffer at SwapEnd 840 and input-ready was set. Desktop press and release reached the guest queue at steps 13 and 14. The window was left open. Presented FPS was not measured.


ACTIVE HANDOFF — 120 Hz guest display timer for fresh Windows QEMU sessions (2026-11-08):

- The pinned AppleCLCD kernel used 16,667 microseconds at both its first timer arm and its recurring arm. The native Windows Setup loader now verifies both MOV/BLR sequences and patches a fresh RAM payload to 8,333 microseconds. The source kernel and non-opt-in Linux tests keep their original timing.
- Separate QEMU kernel probes captured twelve rearm calls at 16,667 and 8,333 microseconds. At a 62.5 MHz guest counter, median observed callback gaps were 18.525 ms and 10.070 ms under the breakpoint probe. This verifies timer configuration and faster guest callbacks, not 120 displayed frames per second. Also verified both instruction bytes in the exact Windows Setup payload preparation path.
- The user's existing Windows PID 20704 session still had working input and prior interactions. Its loaded 60 Hz kernel was left in place to preserve Setup progress.


ACTIVE HANDOFF — Duchamp Setup on native Windows QEMU (2026-11-08):

- Launched the pinned 20F66 RAM-root replay in C:\Program Files\qemu\qemu-system-aarch64.exe 10.2.50. Windows QEMU PID 20704 was live at handoff. Ubuntu WSL prepared the verified font/HID overlay and ran the existing GDB helpers. The earlier WSL emulator session was not restarted.
- The first native RAM layout missed the independent early text console at 0x9c000000. The pinned ADT and fbcon_init data-abort trace identified the missing bank. A compact inert ROM now enables the native DIMM map. The private WSL NAT debugger route reduced an 80–100 exchange localhost relay probe with split RSP-like replies from 44.356 ms to 0.167 ms per exchange.
- Run setup-run-desktop-20261107-214658-16008 reached the country picker. Setup PID 37 connected to BackBoard with status 0 on port 4867. The viewer reported HTTP 200 and input ready at SwapEnd 651. Desktop pointer down and up reached the guest queue at steps 13 and 14. The native viewer and emulator were left running. Windows C: had about 250 MiB free after the test.


ACTIVE HANDOFF — Windows desktop QEMU launcher (2026-11-08):

- The Duchamp QEMU desktop shortcut opens the existing Ubuntu replay in a dedicated Windows window. It reuses a live session and starts a fresh RAM-backed test otherwise. The local Ubuntu fixtures stay outside Git.
- The first shortcut launch reached the native Setup country screen at SwapEnd 497 and 570. The loopback viewer reported input ready. The guest digitizer reached 111 checks in 4.001 host seconds while idle. The trace later recorded desktop input reaching BackBoard. No phone access.
- Native Windows QEMU 10.2.50 was already installed. Added its directory to the Windows user PATH and verified a separate ARM64 virt smoke test reached QMP prelaunch and exited cleanly. The Duchamp replay uses its existing Ubuntu toolchain.


ACTIVE HANDOFF — guest touchscreen timer tuning prepared (2026-11-07):

- The prior live-v1 QEMU session had already ended when the user requested faster guest touch without a restart. Its runner returned successfully after 866.719 host seconds, and neither the VM nor its tmpfs RAM remained. The shutdown reason could not be recovered. The existing session was not relaunched.
- The interactive QEMU debugger now requests 16 ms idle and 8 ms pressed timer periods, down from 60 and 25. It validates each pinned instruction once and supports live adjustment via an atomic live-touch-period.json update. The helper passed tests for defaults, live updates, invalid settings, reset and opcode guards. The six RAM loader and seven UI readiness tests passed. No guest timing or live responsiveness was measured with this revision.


ACTIVE HANDOFF — responsive desktop viewer attached to live QEMU (2026-11-07):

- The existing live-v1 VM stayed up while the user reported sluggish touch. The original viewer polled after 180 ms and rebuilt unchanged JPEGs. Idle guest input also measured 53 timer stops in 4 seconds. The debugger and guest timer were left running as loaded.
- Added the loopback attach mode, cached unchanged frames, waited on a new scanout generation, and bounded queued pointer moves while preserving down, final position and release. The alternate viewer is open as Duchamp QEMU Fast on port 18291 on the same VM. Windows warm GET samples dropped from roughly 39–43 ms to 4–7 ms. This measures the viewer, not guest touch-to-render latency.
- Local HTTP tests passed for replacement frames, origin and coordinate checks, and move coalescing. The original VM and the user's current Setup state were preserved.


ACTIVE HANDOFF — interactive Duchamp QEMU desktop window (2026-11-07):

- Opened a dedicated Duchamp QEMU desktop window on Windows loopback port 18290. The local viewer served the guest framebuffer and switched to the complete physical scanout at present. Its mouse input goes through SweetHIDTouch and BackBoard. The same pinned 20F66 region replay automatically reached the country screen before enabling desktop input.
- The live-v1 run captured the country scene at SwapEnd 774 and 832, IOSurface 5. Windows returned HTTP 200 and guest input ready. At handoff the QEMU event log had 52 desktop touch samples and 64 total BackBoard queue submissions including the 12 startup samples. QEMU and its display server were left running for the user.
- Local replay launcher is `work/launch-setup-live.sh`. The viewer is `tools/duchamp-qemu-display.py`. The stop button ends the VM. The active run was bounded to 3600 seconds from launch. The disposable QEMU RAM root used the existing 20F66 font and HID overlay. No phone access.


ACTIVE HANDOFF — 20F66 Setup fonts and country selection in QEMU (2026-11-07):

- The previous RAM root was missing the original script fallback fonts. Extracted 30 original 20F66 font files (136767248 bytes), checked representative autonym codepoints against their Unicode cmap tables, and pinned manifest cc4979a574aad865c70407cc2a8a30cfdc3ae35c47ecd9f6768e446f69336d46. The private runner grew only the temporary HFS RAM copy by 128 MiB and verified both volume headers and byte-for-byte file readback. The base image hash was unchanged.
- Region-v1 used the existing CI 41543710742 kernel, original 20F66 cache, QEMU software scanout and HID bundle. Setup PID 37 in user/501 received a successful display reply on port 6403. BackBoard received ten swipe events and two tap events. Native Setup selected row 0, visibly English in the language capture, then ran BuddyLocaleController viewWillAppear: and built country rows.
- The 352.966-second run ended without an observed XNU panic and recorded 16 refreshes. SwapEnd 631 shows the previously missing labels in Chinese, Japanese, Korean, Arabic and Thai. SwapEnd 793 shows Select Your Country or Region. Both use IOSurface 5, layer 0, and independently match all 3,308,640 active BGRA pixels and five sampled rows. The other two saved frames also pass the frame verifier.
- Proof: `work/quartzcore-setup-qemu-20261107/region-v1/verification.json` SHA-256 60cf77038bbadd985b6aca71caaaef9958a9382606fc2f7fe9d5b13046343475. Language PNG `native-frame-00000277.png` SHA-256 b26db29541857e65cf76a8693255ce994b620374d4d82175e6b7b4adfd857665. Country PNG `native-frame-00000319.png` SHA-256 a13f3ec74654e6ead622c08c1050021f3db2fb7c53031ead2b2a209d8bd67c39. The directory retains both raw inputs compressed and the event trace. Test scope QEMU only.


ACTIVE HANDOFF — native 20F66 Setup language picker after a QEMU swipe (2026-11-07):

- Added opt-in continuous QuartzCore software scanout and a bounded bottom-edge swipe through the existing SweetHIDTouch path. The same CI 41543710742 kernel, manual Setup mode, and user/501 session were used. The original arm64 20F66 IOHIDEventServicePlugin bundle was installed and byte-verified in the temporary QEMU RAM volume. The original root hash was unchanged.
- BackBoard PID 25 opened the touch service and enqueued all ten digitizer events. Kernel timestamps put the swipe at 246.959 ms, from (540,2380) to (540,1180). Setup PID 37 received BackBoard display port 6147 with status 0. After release, the native BuddyLanguageController ran viewWillAppear: and tableView:numberOfRowsInSection:.
- The 328.636-second gesture-v4 run completed without an observed kernel panic. It recorded 17 scanout refreshes and five frame samples. The final 1220×2712 PNG visibly shows the language list. Several labels render as missing glyphs and the captured frame is dim. SwapEnd 1047 selects IOSurface 5 in layer 0. All five sampled rows and all 3,308,640 active BGRA pixels matched. SwapEnd 1013 also matched the source pixels but did not demonstrate a change in the sampled rows.
- Private proof: `work/quartzcore-setup-qemu-20261107/gesture-v4/verification.json` SHA-256 6b73e3203e875b8cbc304fb2c8555efd04b6c2a871cbefa9b4e06d275c715583. Screenshot `native-frame-00000417.png` SHA-256 3bee572e48ff2dc7df8edad0c41c88c46049b7fca9892343b3803f3ed4132d7f. The same folder contains the compressed raw inputs, event trace and kernel log. See `duchamp/QUARTZCORE-QEMU.md`. No phone access.
- Reclaimed host space with in-place compression of two existing QEMU logs and two existing diagnostic HFS images. Each file's original SHA-256 was preserved.


ACTIVE HANDOFF — visible 20F66 Setup Hello in QEMU (2026-11-07):

- SpringBoard PID 34 launched Setup PID 37 in user/501 with the QEMU-only iOSUser session correction. Setup received BackBoard display port 5891 and a successful native screen reply. The app-specific watchdog allowance was measured at 120 seconds in the prior replay.
- The manual replay answered the proximity resume check with false. Setup then committed three contexts. QuartzCore drew the native Hello screen in a 1125×2436 software buffer. The original 1220×2712 output IOSurface remained black until the one-frame diagnostic copied the scaled native pixels to it.
- Verified SwapSetLayer and SwapEnd 215 select IOSurface 5, layer 0. All five sampled rows and all 3,308,640 active BGRA pixels match the native software source after scaling. The physical framebuffer PNG shows Hello. The test was a one-frame software scanout in QEMU.
- Evidence: `work/quartzcore-setup-qemu-20261107/physical-hello/verification.json` SHA-256 d87d314412d2ca9f8e13bd668e0fa7f4bc26def58abf421cb8e77e040c57f104. See `duchamp/QUARTZCORE-QEMU.md`.

ACTIVE HANDOFF — 20F66 Setup launch in QEMU (2026-11-07):

- Added 645 pinned original Setup.app and framework files and 82 native RunningBoard/FrontBoard policy files to a separate HFS RAM root. Each file passed a byte-for-byte readback. Setup's 95 linked install names are present in the matching dyld cache.
- The system-lsd replay retained the native binary and mobile credentials. UID 501 still received the native LaunchServices reply. With the QEMU-only interrupt timeout scale set to 4, the last run reached Setup activation from SpringBoard PID 34 after booting the CI 41543710742 kernel. The 460.256-second run recorded no XNU panic.
- RunningBoard returned code 5. Native launchd rejected UIKitApplication:com.apple.purplebuddy in system with error 134. The serialized request recovered from PID 1 selects /Applications/Setup.app/Setup and mobile with no LimitLoadToSessionType. The system session name is System and the existing user session is iOSUser. SpringBoard then aborted at its app-layout assertion.
- No Setup exec, Setup context commit, or eligible Setup frame was observed. Next validate the launchd session for this specific job, then capture Setup pixels and verify their SwapEnd surface. All runs used QEMU.
- Evidence: `work/quartzcore-setup-qemu-20261107/session-rejection/verification.json` SHA-256 ce54177a7b146348514f5142a8c79c1a17b247666088807313ff6a816eb0ab6e. See `duchamp/QUARTZCORE-QEMU.md`.

ACTIVE HANDOFF — verified native compositor scanout in QEMU (2026-11-07):

- Reclaimed host space by compressing seven prior QEMU RAM-root dumps in place. All seven SHA-256 values stayed identical. Rehashed the 20F66 image (64354ba3475d3c34d6fc531f75585a7b24af0fdb7a3a8a2bdf95c7f351a3f290), installed and round-tripped 557 CoreEmoji resources in a separate root (ae2c474570e5be596ecdae81a153d7f608611ec176d5696cbe0e4f09f162ed63).
- 315.202-second replay with CI 41543710742 kernel and unmodified native 20F66 cache. SpringBoard PID 34 was alive at stop with four traced context commits. BackBoard PID 25 submitted layer 0 IOSurface 5 in SwapEnd 17. The ID and five rows matched AppleCLCD's physical scanout at 0xfcc2f000. Four rows changed from the prior scanout.
- Native transfer passes. All active RGB pixels of the first native frame were black. The final QMP frame only showed launchd console text. The separate synthetic control matched 2048/2048 pixels and five traced rows. No physical device was tested.
- Evidence: `work/quartzcore-emoji-qemu-20261107/verification.json` SHA-256 4602731ada509574f3e94ec70076a874fb7ff3380c1f5d42077953ab35ba23ec. See `duchamp/QUARTZCORE-QEMU.md` and `tools/verify-duchamp-native-frame.py`.
- Next gate: a visible native SpringBoard/Setup frame. The staged QEMU root lacks `/Applications/Setup.app`. Its absence is an observation; the reason the compositor emits black has not been proved.

ACTIVE HANDOFF — native SpringBoard IOSurface creation in QEMU (2026-11-07):

- Branch `duchamp-bootstrap`, QEMU only. Same CI 41543710742 kernel and original 20F66 shared cache. The native baseline calls `set_all_layers_to_null(true)` from `set_enabled_(false)`, sends NULL through SwapSetLayer, and powers off. AppleCLCD previously verified the independent synthetic 2048-pixel fixture.
- QEMU replay omitted the blocked `com.apple.AttentionAwareness` service from the guest BackBoard job and used verified original UIKit collation, CoreNLP/langid, UIKit Artwork/CoverSheet and AddressBookLegacy resources. The chained boots successively advanced through a synchronous IPC wait and collation, language-model, luminance-map and address-book startup failures.
- Contacts replay (270.293 s) captured one QuartzCore context commit from SpringBoard PID 34 and two native IOSurfaces, ID 2 (184x124 BGRA) and ID 3 (230x186, 0x4c413038). SpringBoard then aborted in CoreEmoji's bundle creation. The last backboardd SwapEnd carried [0,0,0,0], AppleCLCD counted two swaps and zero eligible layers, and physical scanout was blank. First native frame remains pending.
- `duchamp/QUARTZCORE-QEMU.md` has the replay instructions and exact throw sites. Private evidence is `work/quartzcore-qemu-20261107/verification.json` (SHA-256 e8531fe811d774375f08827ac65272920dcffb50d7c8d05c54949807deb077b0). `contacts/msgbuf.txt` records the surface IDs and `contacts/quartzcore-events.jsonl` the native calls. The workspace's pre-existing changes were kept separate.
- Next QEMU trial: restore matching CoreEmoji resources, then correlate a non-null SwapSetLayer, surface ID, SwapEnd and actual scanout bytes. Extraction stopped on host I/O while C: was full. Reclaim space before another large VM. No phone or physical storage work occurred.

ACTIVE HANDOFF — native compositor traced and synthetic framebuffer PASS (2026-11-07):
Read duchamp/COMPOSITOR-QEMU.md. Private evidence in work/compositor-qemu-20261107.
Verification SHA256 30d16a4391704a782e89183f0ef0893d132082514fd3d4a4bebd2e824cb0a725.
Six observation checks passed. Native V3 reached the original service marker
in 192.520 host seconds. Hardware trace on the unchanged e465723a kernel
and 8029fb33 V6 root showed backboardd PID25 power 1, SwapEnd ID1 while on
with four zero IOSurface IDs and zero rects, then power 0 at the same vsync.
RAM confirmed one swap, zero layer logs, display off, dirty pending, active
vsync and byte-for-byte match at framebuffer PA 0xfcc2f000.
A sweethidtest=7 run reached the same marker in 191.264s with the same empty
swap and off state. End-to-end Home delivery was not checked. V1 debugger
signed address error fixed. V2 ran past the readiness marker and had an IRQ
latency panic. Corrected V3 stopped cleanly at the intended marker.
Synthetic isolated scanout PASS in 75.246s: original IOSurface/IOKit,
selector 5 submitted ID2, 2048/2048 BGRA pixels at (521,1801), one layer
consumed, dirty false. This proves CPU copy in QEMU. Native GUI unverified.
No kernel or shared-runner changes. No CI, phone, flash, UFS or Mali access.
Next trace QuartzCore render_display to IOMobileFramebufferSwapSetLayer.
Verify nonzero native surface ID, subsequent SwapEnd and captured pixels.
The 1125x2436 BackBoard geometry vs 1220x2712 AppleCLCD geometry remains
an unisolated difference for the native path.

ACTIVE HANDOFF — native readiness and SpringBoard process PASS (2026-11-07):
Implementation/docs commit: eeec2a18e44e55f6b52097795ad70cfd869fcd6e.
Completed the authorized QEMU batch:22/22 checks PASS (18 core/order/process,
4 UI-provider),187.382 host seconds. Final report
work/ui-readiness-qemu-v6/evidence/verification.json SHA256
7d91e37d0e651b62ec251935ade0875a3a1a7fa8beb1f858bcf68871570c5dfe.
Inputs f2dc87ed1dec48e387b7613cfcda538b3d44275724964c41dfc55cd4fe879d56;
root 8029fb33aa7805e773e10848f05af0f85349a1e1c9fe1e3dcea35890f3f9c171.
All294 installed-file roundtrips match; base/source root/13 tested source pins
unchanged. Original e465723a...9182b kernel unchanged; no new CI build.
No phone/ADB/flash/partition write, physical UFS or GPU access.

Original launchd PID1; logd7, MCM5, installd13 UID/GID33, lsd17 mobile,
runningboardd22 root and backboardd25 mobile. Original SpringBoard PID34 mobile,
launchd parent/exactpath verified; all six five-second health samples PASS.
LS native read/rebuild callbacks witnessed; status256/0x100 means seeded AND
seeding_complete. Original SpringBoard record installed1/nonplaceholder with
exact bundle path verified. Full stock-app inventory remains unverified.
Two native BackBoard display MIG replies kr0,values1125,2436,1,0 /flags0,0;
opaque slots are not physical-panel-discovery or rendering proof.
SpringBoard plist kept outside LaunchDaemons; bootstrap ordering after all
native readiness/record gates verified. RunAtLoadFalse alone allowed an early
EmbeddedHomeScreen launch in V4; no longer relied on as an ordering gate.

V1 FAILED121.648s: actual native rebuild -54; display checker wrongly rejected
zero fourth scalar. V2 FAILED138.168s: exact single rebuild entitlement on OUR
ad-hoc client fixed authorization, display replies PASS, LS still0x300.
V3 PASS142.138s,19 checks: original installd/home + minimal bundle resources
made LS0x100. Additions tested together, not an isolated per-file causal proof.
V4 FAILED162.624s: full38-file/2202072-byte original bundle and native app record
PASS, but missing original libobjc-trampolines.dylib killed SpringBoard.
V5 FAILED176.208s: recovered module + deferred bootstrap/native identity PASS;
health1/2 alive,3 dead. Actual nil-dictionary exception in ISImageBagIcon
_generateImageWithDescriptor:+328; matched live slide44630000 and actual stack.
Quiet disassembly/call-stub lookup traces nil slot to default app/App Clip
asset bag; global ipsw ObjC analysis hit its own host OOM, not a guest failure.
V6 adds115 original IconServices/MobileIcons/font files (9788380bytes); prior
nil exception absent in this short window. Exact individual resource not isolated.
Seven parser + four overall-verdict regressions PASS; runtime C/ObjC and decoder
C++ compile with Werror PASS. All failed/successful trials remain private.

Original68080-byte trampoline decoded by pinned read-only apfs-fuse algorithm14,
exact usr/lib path/inode3136/size. Existing-output/unsupported/invalid-image
negative checks PASS. SystemOS image freshly SHA-verified2279bf44...fdd3;
module a5410b215468c275e1f861c7e605f58401e332f7f23765a6e1fbe7391d4f05df.
Other resource extractions inherit prior full-OS hash after exact size/mtime
checks and verify each file hash; they do not freshly hash that large image.

IMPORTANT: final PNG visually inspected: diagnostic console only, no observed
lock/home screen. full_gui_ready=false, rendering_verified=false stay set.
SpringBoard stderr retains PLClientLogging unknown permission type2. Missing
native lookups include mobilegestalt/iconservices/searchd/sessionservices/DND;
these are leads, not an attributed cause of absent graphical output.
NEXT: inspect native compositor/window-server state and actual presentation;
isolate which missing service requests block that path. Process liveness is
not GUI success. Physical MT6897 UFS/DMA/IOMMU/cache/resource ownership/Mali
remain separate unproven work; large QEMU md0 layout is NOT a phone candidate.
Native final dir /home/mehmedamir/.cache/duchamp-qemu-tests/platform-services-a7tsocao;
exports retain evidence and omit native guest-ram.bin only. See
 duchamp/UI-READINESS-QEMU.md. No VM/GDB/APFS helper remains active.

ACTIVE HANDOFF — original platform services and UI daemon health PASS (2026-11-07):
Implementation/docs commit: 7376d79677fbf5e2a4a1112f7dc04a6565e89925.
Completed the authorized local batch; no phone/ADB, flash, partition write,
physical UFS or GPU access. Original kernel e465723a...9182b unchanged. No CI.
V9 work/platform-services-qemu-v9/evidence/verification.json: PASS 13 core
plus 4 requested UI checks, 117.640 host seconds; report SHA256
2fa5bf57b43f00258dd7dab6c9d31bd1b63457ec2b0a528305447e2210067ab2.
Inputs 010c5ee20955ea026ff0dc366e9cc192a66490f1f57cf9198d7c63d0c458ba7b;
root da5a0c9ef7d9a9002c642f01f731a5c4b8b37d4dc74a342104e4aa00a930dc6f.
134 installed-file roundtrips matched; source root/base/test-source pins unchanged.

Original launchd PID1, intact 20F66 shared cache; verified logd PID7 UID/GID272,
containermanagerd PID5 root, lsd PID13 mobile, runningboardd PID19 root and
backboardd PID22 mobile. All five retained identities across six five-second
health samples. Separate native mobile clients PID16/PID25 received real
LaunchServices completion callbacks before/after UI, error=0; original wrapper
agreed. Status768/0x300 is a BITFIELD: seeded=true, seeding_complete=false,
NOT OSStatus and NOT application-registry-ready. No GUI/SpringBoard proof.

Root cause: hardware breakpoint at actual EL0 fault captured FAR8/x0=0 and
user frames through CFDateFormatterCreateISO8601Formatter -> MCM formatter.
Missing original ICU data caused the repeated MCM segfault. Matching ICU data
fixes it; independent native ISO8601 epoch formatting PASS. SystemVersion alone
did not fix it. Correct root/System MCM and mobile LS bootstrap contexts retained.
V8's longer check caught delayed backboard SIGABRT from missing original
EventProcessorConfiguration.plist; V9 installs exact 1313-byte source resource,
then passes all health/reply gates. No original executable/kernel was patched.
Initial logd SIGTRAP before controlled kickstart and duplicate BK class warning
remain diagnostic limitations. Liveness is not proof of every daemon RPC.

New qemu-service-ram.py uses native-Linux shared sparse 10GiB RAM backend,
4GiB kernel window, 3GiB writable md0; source images unchanged. Separate QEMU
layout, NOT a phone candidate or modification of phone ADT/512MiB payload.
Small-root original-launchd baseline PASS heartbeat3 in45.089s. Unit checks:
6 layout + 6 LS-status + 4 verdict regressions PASS; C/ObjC compile Werror PASS.
V1-v8 failed/shorter trials and null-fault trace are preserved privately.
V7 caught fresh-query file ownership bug, fixed 501:501; UI failure cannot pass.
WSL gdb-multiarch17.1 installed (8packages/52.1MB); no phone service installed.

Final native dir /home/mehmedamir/.cache/duchamp-qemu-tests/platform-services-jxtpwpjq;
exports omit the retained native guest-ram.bin. No VM/GDB/HFS helper remains.
See duchamp/PLATFORM-SERVICES-QEMU.md for replay, exact receipts and limitations.
NEXT: complete/verify LS application registry, then native display-service
requests before an audited SpringBoard trial in QEMU. Physical MT6897
UFS/DMA/IOMMU/cache/resource ownership and Mali remain separate unproven work.

ACTIVE HANDOFF — intact shared cache executed in QEMU; 13/13 PASS (2026-11-06):
Continued the user's approved next-stage plan locally. Original20F66 dyld
loaded untouched runtimecache UUIDE5420DB3-30D0-33AA-8B7E-05B5038BB46D.
Static diagnosticPID1 forks; dynamicchildPID2/ppid1 reports livecache range,
dlopen(RTLD_NOW) success for original ContainerManagerCommon andCacheDelete,
bothloadedheaders inrange withMH_DYLIB_IN_CACHE andobjcclass namesMCMError /
CDRecentInfo. No derived standaloneexports wereused; theirgate remainsclosed.

V4 FINALsource result work/shared-cache-qemu-v4/evidence/verification.json:
13/13PASS,32.843hostseconds,SHA256
1aa834e63097cb1a07d5640177da6d2500b2322afdc3cba231f04874fcc8fb54.
V4root3e23c283d5847ccf9e556f2300df8050d30ad8487e759e92689dd2765a9f71bf;
inputs1b7e4c71739f50029b8e485367663d1659802c66889afb4461173aebb44c3723.
V3 alsoPASS13/13,49.343s,report3da48e77694343e15a0e4386d1e4d4199f3af7cc8ec3cfb127795843ac532969.
V4corrects diagnosticparent busyrecvfrom to blockingwait4/select; rerunpassed.
Timingsarelocaltrials,notcontrolledperformanceorhardwaretimingproof.

43runtimecomponents/2722512896bytes (symbols omitted) installed into NEW3GiB
HFSdisk; each sourcepin + HFSroundtripchecked. Strict read-onlyQEMU UFS serves
cacheoutside unchanged512MiBkernelwindow. Payload16715616bytes,SHA
5aba40f16dd814bc2c2a1126677bcfca222c87fa61c650eb7756364f8eb7a465.
Kernel e465723a...9182b unchanged; baseQEMUADT a881410d...417d8 unchanged.
Disk/base/sourcehashesunchanged afterrun. Originaldyldroundtripmatchesmatching
source. NoRAMDisk fallback. Inheritedearly 'QEMU RAM ROOT MOUNTED' text is
generic: thisfixtureusesqufs0,notmd0. Native3GiBimagesuseWSLdisknot/tmpfs;
allprivateinputs/frozensources/results exported. NoVM/helper remainsactive.

V1FAILED beforedyld: missing/dev onreadonlyroot,consoleopenfailed; manually
stopped89.533s. V2FAILED180.250stimeout: directexecasPID1 lastshowedlibignition
configuration; noCmain. Exactinternalwaitnotattributed. Independentchildisolates
cacheloading; itdoesNOTsolveoriginalPID1diskrootstartup. V1-v4allpreserved.
qemu_ufs.py nowstreamshash/headerchecksinsteadwhole3GiBreads;20profiletests
PASSincludingwholefilereadguard. Newtools:test-duchamp-shared-cache.py,
duchamp-shared-cache-init.S,sweet-shared-cache-probe.c. RuntimeAPIdeclsverified
againstApple dyld1066.8headerandmatchinglocalexports.

NEXT: writable service state separatelyfromcache disk; integrateoriginalMCM/
logdpolicies and require realnativelsdrequest/reply. OriginalApplelaunchd with
thisdiskfixture,GUI/backboardd/SpringBoard NOTtested. PhysicalMT6897UFS/DMA/
IOMMU/Maliremainseparateunprovenwork. Nophoneaccess/flash/partitionwrite;
Androidlastverifiedrestoredasbefore. See duchamp/SHARED-CACHE-QEMU.md.
Preserve unrelateduseredits(including1960earlierunstagedNOTESlines).

ACTIVE HANDOFF — complete SystemOS/cache acquired; strong paths resolved; loader blocked (2026-11-06):
The user challenged progress toward a usable phone system. Continued actual
local source work, without phone/partition access or a new kernel build.
Official Apple20F66 SystemOS member096-04666-078.dmg was downloaded into NEW
work/20F66-systemos-v1,2726297600 bytes, liveZIP tuple/manifest matched and
finalsize/CRC passed. SHA256
2279bf443856fcb6a3f00b1fa06a32ba02a66fdf6ab6b12019462c7498aafdd3.
Priorpartialfiles preserved. Signature authentication is NOT claimed.

7z could not decode3 ZBM-rsrc cache components. Built upstream read-only
apfs-fuse library commit66b86bd525e8cb90f9012543be89b1f092b75cf3 withLZFSE
e634ca58b4821d9f3d560cdc6df5dec02ffc93fd (WSLcmake/bz2/fuse3depsinstalled).
New GPL2+ tools/read-systemos-zbm.cpp uses only read-only image APIs, no
filesystem mount, strict path/inode/algorithm14/size and exclusive output.
All3 decodes passed: .42linkedit333955072; .28linkedit19906560; symbols591855616.
Unknowncomponent,existing-output and invalid-image rejection checks passed;
existing bytes unchanged. See work/cache-zbm-recovery-v2/receipt.json and
negative-checks.json. No upstream APFS tool was installed globally and no
filesystem mount occurred; WSL build dependencies were installed as noted.

Selected complete cache work/20F66-cache-v3 has44 primary components,
3314368512 bytes, UUIDE5420DB3-30D0-33AA-8B7E-05B5038BB46D. Pinnedipsw
parsed2710 indexedlibraryrecords. Source/partialcachev1/v2 artifacts preserved.
Eight selected --slide exports matched original imageUUIDs. Complete strong
source closures: MCM87 binaries/102555520bytes; systemMCM87/102555536;
logd93/109247128; zero missing/invalid. Audit:
work/20F66-framework-audit-v3/summary.json SHA256
f7d67dd36cf0792b2de6d313b9903a0d21866750c194bc30e25d5eb0796cc150.

CRITICAL SCOPE: these are derived analysis exports, not unchanged standalone
dylibs. Common,CacheDelete,RBS,UserManagement retain sampled externalcache
addresses without declared bind/rebase metadata. Four originalframeworks
lack DYLD_INFO/CHAINED_FIXUPS/CODE_SIGNATURE commands and sectionrelocations.
New audit keeps standalone_payload_allowed=false; six loader-gate unit tests
passed. No derived export was executed in QEMU or placed into a phone image.
Previous lsd failure verdict remains; no native RPC/GUI success is claimed.
Review findings fixed: failed closure status is propagated; ordinary cache
reuse requires source-bound per-file SHA validation before copying. Fresh41
source extractions under work/20F66-cache-source-regular-v1 made the manifest;
v4 assembly uses it plus strict3-component ZBM receipt. Negative tests reject
same-size corruption and ensure failedclosure reports do not imply exitzero.
V4 actual parserPASS,all44 hashes byte-identical tov3. Activev4receiptSHA256
30eb89efbe8fb1c63b6599a9ecffad13b6b956f644e9ef91cf351b61b97f1fab;
comparison6ff1fe70483fa480a70d972f76e9a52ae563ee0cf359f68f3e7f17a6f64f9c2b;
manifest0ebc803c65cd8834b9fac4ff57e7b798bbc3bcec3ab79b06251180b1f8e1eeb0.
This strengthensv3sourceprovenance without rewritingits historicalreceipt.

Parallel original policy/account audit: work/container-policy-v1/results.json
26a69fb2b2f133b79aff240e52242cfdb880935f1d7807317a9b965c682b05f3.
user_system_split absent/defaultfalse is statically supported without overrides,
not a liveflag proof. mobile501:501,_installd33:33,_logd272:272 preserved across
original/restore/savedRAM accounts; no UID/GID fix indicated. Kernelupcall25,
credentials,privilege/sandbox contracts remain unproven.

NEXT: choose/validate runnable cache loading in QEMU (intactcache storage/map
or reconstructed standalone binds/ObjC references). 3.3GBcache does NOT fit
the existing512MiBphone payloadwindow; no blind insertion. Then integrate real
MCM/logd policies and obtain native lsd reply evidence. Original Android is
still lastverifiedrestored; physicalUFS/Mali/fullGUI unproven. See
duchamp/SYSTEMOS-CACHE-RECOVERY.md for receipts/reproduction boundaries.
Preserve unrelated user edits and keep Apple/private artifacts outside git.

ACTIVE LOCAL HANDOFF — lsd runtime blocked by support services/framework gaps (2026-11-06):
The user asked the fastest next step; ran original lsd in QEMU on the unchanged
e465723a...9182b kernel/a881410d...417d8 QEMU ADT. No phone/network access or
kernel build. Original Android remains last verified restored below.
tools/test-duchamp-lsd.py and sweet-lsd-probe.c create a fresh128MiB HFS root,
preserve original lsd/mobile job/13MachServices and add proven notifyd/cfprefsd
support. All106 installed files plus original launchd/xpcproxy hashes matched.

ACTUAL RESULT: work/lsd-qemu-v1 failed,76.501 host seconds. Root controllerPID3
kickstarted real lsdPID6; first CLI print showed running,execs=1,initialized=1
in user/501. launchd then reported lsd self-SIGABRT. Last print not running,
Abort trap6. Failed lookups for com.apple.logd and com.apple.containermanagerd
were visible. Exact fatal branch is NOT attributed by temporal lookup logs.
Native UID/GID/stability/endpoint checks did not pass; no native app RPC ran.
QEMU report3ec19b4e1ad47d2c8efa4bc5535e8e7f284909c9c4477e485d6630a3a3b7ec1e;
payload377256b9155a125688797e7cb39e5a0a3d01d69fec777022bd13938975bce494;
root392a97d4f84f0c3399f2a4b7821dd4d71832b2d91350989196567fede0a8229c.

Safe alternative follow-up extracted6 original container/log binary/job files
into work/lsd-support-audit-v1. Source size/mtime match prior SHA-verified4.7GB
image receipt; hash inherited,not recomputed. Both container daemons lack
ContainerManagerCommon/System/User; logd lacks CacheDelete. These are exposed
strong-path gaps,not a complete transitive count. Incomplete providers not run.
Support audit4423b5df9d88942bfa9cce2371865bc07245c3fb30cf0f678b4e26bdbf537966.
Original conditional modes/ownership/hostspecial25/crash policies are recorded.

Static CoreServices inspection identified a native status query, but wrapper
zero alone is not server-reply evidence and an internal helper symbol is not
registered ObjC method metadata. No speculative native wire request was sent.
The final observer uses verified bootstrap_look_up_per_user(...501...), since
launchd relocates this job to user/501; native branch was never reached in v1.
This correction and bounded CLI cleanup compile/link successfully under
work/lsd-probe-final-build-v1; corrected endpoint branch remains unexecuted.
Frozen v1 source/evidence preserved. See duchamp/LSD-QEMU-DIAGNOSTICS.md.

NEXT CONCRETE WORK: acquire/audit matching four support frameworks and their
imports from complete verified20F66 SystemOS/Cryptex, integrate real support
providers with resolved policies/resources and run a native reply witness.
Do not retry the unchanged incomplete fixture expecting success, substitute
stub services, or claim full GUI/UFS/Mali. Prior IOSurface14/14 remains a CPU
sharing result. Private Apple files/logs stay local; preserve unrelated edits.

ACTIVE LOCAL HANDOFF — UI dependency audit and IOSurface QEMU PASS (2026-11-06):
The user requested UI-service dependency inspection inside QEMU. No phone was
accessed or flashed; original Android remains last verified restored below.
Twelve actual GUI executable/job files were selectively extracted from the
existing complete 20F66 OS member into work/ui-daemon-scan-v1/apple-extracted.
Source image SHA256
64354ba3475d3c34d6fc531f75585a7b24af0fdb7a3a8a2bdf95c7f351a3f290,
4728546953 bytes, CRC32 028fc181, matching the saved IPSW index. All six
executables are plain arm64/iOS16.5. Exposed missing strong paths: SpringBoard
1 (its main framework), backboardd29, runningboardd2, mediaserverd6,
splashboardd8. lsd is complete:88 binaries/106575136 bytes, not yet run here.
Unknown dependencies of absent frameworks cannot yet be traversed. Weak/
dynamic imports, services and hardware compatibility are not established by
the static closure. Original mobile identities/Mach endpoints are recorded.

Available original IOSurface/IOMobileFramebuffer/MiniDisplay have a combined
81-binary strong closure. New tools/audit-duchamp-ui-runtime.py records this
with conflict/unsafe/unresolved-path failure gates; its six negative/scope
unit tests passed. New tools/sweet-ui-surface.m and test-duchamp-ui-surface.py
use the same e465723a...9182b kernel and a881410d...417d8 QEMU ADT, a copied
128 MiB HFS root, original launchd PID1 and no kernel/phone image changes.

work/ui-surface-qemu-v3 passed14/14 in35.806 host seconds. Root parent PID3
created IOSurface ID2,64x32,stride256,allocation16384; independent exec child
PID4 verified/rewrote2048 pixels; parent verified complete writeback after
normal child exit. Saved logs/result/heartbeats and all90 installed files plus
original launchd/xpcproxy hashes match. Source snapshot matches current code.
QEMU report SHA256
3b1ae8542e0f84beb341ec25d5ad2634a99bcdc767d9044b21bfcdace81ccdb9;
payload1d0f3987c54d40309c8ac976ed3564091729cac321f727a63abef3a979340087;
root10ed2fc8043e5c8d0515e2544bb741b82fd49ab6357c7589ac5d14f943f1d524.
No display swap, GPU/Mali acceleration, full GUI or physical DMA/cache claim.
v1 HFS catalog deletion failure and v2 missing saved HFS log/result evidence
remain preserved. v3 replaces the existing copied job and syncs before the
console stop marker; full saved-evidence verification now passes. Independent
read-only review found no material issue. See duchamp/UI-DEPENDENCIES-QEMU.md.

NEXT: original lsd runtime test in QEMU with its native mobile job/endpoints,
bounded startup/client checks and dynamic-dependency diagnostics. The matching
GUI frameworks/Cryptex cache still need availability/auditing before higher UI
jobs; no extra download was made this turn. Physical UFS remains closed and
phone state unchanged. Private Apple files and detailed evidence stay in work/
and research/, outside git. Preserve pre-existing unrelated user edits.

LATEST HARDWARE RESULT — combined services PASS; Android restored (2026-11-06):
The user approved combined launchctl/syslogd/notifyd boot_a image SHA256
545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8
with original Android restoration. Fresh read-only preflight established
Duchamp/MT6897, active _a, unlocked/rooted original Android and 85% charging
battery. Original boot_a/vendor_boot_a/lk_a live hashes match. A fresh 64 MiB
binary-safe boot_a backup is saved at
work/phone-services-flash-trial-v1/boot_a-before-trial.img, SHA256
1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12.
Fastboot rechecked identity/slot/unlock/size, wrote only boot_a successfully
(1.766s) and accepted reboot. Original Android has since been restored below.

The user's physical-phone photo shows NOTIFYD CONTROL PASS server=7,
syslogd=4 clients=5,6; SYSLOGD CONTROL PASS messages=6; heartbeats 1 through 3
with server still running and probes stopped; both clients exit status 0.
Photo: work/phone-services-flash-trial-v1/phone-services-observation-01.jpg,
SHA256 652315d665cae36a5e2b957d2c645f7be18bfa4bd3aa5c3188a2b06efb956dda.
Shared-region address warnings are visible but these observed CLI calls
returned status zero. This is physical combined-services evidence, not a
claim that all 74 saved-guest checks were extracted from the phone.

CURRENT STATE: ORIGINAL ANDROID RESTORED. The private helper wrote original
boot_a successfully (1.819s), rebooted, verified Android/root/live boot_a and
exited zero at 04:16:17 local time. Exec session 82953 ended. A transient ADB
device-not-found during the sys.boot_completed observation was logged and
tolerated by the bounded read-only loop; no flash was repeated. Independent
read-only follow-up reconfirmed boot_completed=1, Duchamp/MT6897, active _a,
original V816.0.17.0.UNLMIXM fingerprint, Magisk uid=0 and original boot_a hash.
Private android-recovery-followup.json SHA256
4040e55a2f0a9a653750c92f69df67360015a1796f7f71bcf0919319115ccd54.
No restoration remains pending. Logs/plan/private scripts are under
work/phone-services-flash-trial-v1. Physical UFS remains closed; GUI/Mali/full
iOS are not established. Next work is local dependency/provenance review for
a larger RAM userland; any materially different hardware trial needs its own
concrete review/approval. See duchamp/PHONE-SERVICES-BATCH.md.
Preserve all pre-existing unrelated user edits.

ACTIVE HANDOFF — combined services candidate locally PASS; phone trial pending (2026-11-06):
The user requested the fastest useful next boot checkpoint. Reused the exact
phone-proven kernel e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b
with the existing 32 MiB notifyd/syslogd/Procursus-launchctl RAM-root fixture.
Fresh QEMU replay passed all 74 guest checks in 71.368 host seconds: five
distinct processes, six ASL records, notifications/cancellation and two server
heartbeats. Evidence: work/phone-services-batch-v2/qemu-proof/run/verification.json,
SHA256 772c3971d0b455a9013b9d933e7147ef1b97b9e7e7a7d3b22464a3336eab191d.

Selected image work/phone-services-candidate-v3/duchamp-services-batch-avb-none-lz4.img
is 67108864 bytes, SHA256
545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8.
The packager passed 12/12 checks including reconstructed guest payload, native
handoff/materialization, real bootshim->XNU QEMU entry, boot-v4/AVB-NONE and
LZ4 roundtrip. Report SHA256
0b15c708455f7d8c23625e24dc476dd039532286f5d43ed4f8399bbfd695e63f.
The new replay and package tools refuse existing outputs; a failed prior
74-check proof was rejected without creating a candidate. Syntax checks pass.

Packaging found an undefined DUCHAMP_IMAGE_BASE sentinel in legacy ELFs.
build.sh now explicitly defines default base zero; capture/layout/QEMU-LK
overrides were independently checked at 0/0x40000000/0x40200000 without
undefined symbols or relocations. shim.ld is unchanged. Failed/intermediate
outputs are preserved. Source receipts capture existing local loader edits;
do not stage or overwrite those unrelated changes. Private fixtures stay local.

No phone access or writes occurred this turn. Original Android was last
verified restored after the preceding hardware trial (including independent
ADB follow-up after the helper's post-reboot observation error; details below).
The new combined batch is NOT yet phone-proven. Next: the user's concrete
approval for this different boot_a image with restoration, fresh device/slot/
backup checks, and bounded read-only recovery observation retries with exact
command diagnostics. Never retry a flash automatically. No physical UFS,
DMA/IOMMU/resource ownership, GUI or complete iOS claim follows from this work.
See duchamp/PHONE-SERVICES-BATCH.md. Preserve all pre-existing user changes.

LATEST HARDWARE RESULT — Apple launchd + C service PASS; Android restored (2026-11-06):
The user explicitly approved the concrete Apple-launchd boot_a trial with stock
restoration. The exact image SHA256 is
e36b7632ff402d39db162081c2c5bb401540651ba87a38d9fdd21afd6ca80686,
64 MiB, original launchd/dyld/xpcproxy plus one diagnostic C service on a
32 MiB HFS RAM root, cpus=1 and rd=md0. Physical UFS remains closed. Fresh
offline revalidation had passed 17/17 in the preceding turn.

Android preflight reconfirmed Duchamp/MT6897, original fingerprint, slot _a,
unlocked state, completed boot, 80% charging battery and matching live boot_a,
vendor_boot_a and lk_a hashes. A fresh binary-safe boot_a backup has SHA256
1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12.
Fastboot reconfirmed device/slot/unlock/size, wrote only boot_a successfully
(1.770s) and accepted reboot. Original files and other user edits preserved.

The user's clear physical-phone photo shows xpcproxy spawning service PID 3,
launchd service state running, main pid=3 ppid=1, uid=0 euid=0,
parent_path=/sbin/launchd, RAM file verified and heartbeats 1 through 11 with
stable PID/PPID. Photo SHA256
8e2d5566818cd8eb9a94793c60398a67e345d42af61db97256eaf58e09ce3243,
saved as work/phone-apple-launchd-flash-trial-v1/phone-launchd-service-observation-01.jpg.
This establishes original Apple launchd PID 1 and its root C service on the
physical Duchamp RAM root, in addition to the earlier QEMU evidence. Persona
lookup warnings are visible but did not prevent service startup/heartbeats.

CURRENT STATE: ORIGINAL ANDROID RESTORED. The helper successfully wrote original
boot_a (1.838s) and rebooted, then exited on an empty nonzero ADB verification
error. Do not call the helper a clean PASS. Independent read-only follow-up
verified boot_completed=1, Duchamp/MT6897, slot _a, original build fingerprint,
Magisk uid=0 and live boot_a SHA256 matching the original backup. No extra flash
was needed. Helper exec session 56751 ended; no restoration remains pending.
Exact failed ADB invocation was not logged; future helpers should record it
and tolerate bounded transport errors only during read-only boot observation,
never repeat a flash automatically. Logs, fresh backup and plan are under
work/phone-apple-launchd-flash-trial-v1.
Scope: original launchd + one C service from RAM is proven on the phone.
Physical UFS/DMA/IOMMU/firmware ownership, persistent root, Mali, SpringBoard
and other peripherals remain unproven. See duchamp/PHONE-LAUNCHD-TRIAL-PLAN.md.
Preserve pre-existing user changes.

Next reviewable checkpoint — Apple launchd RAM root (2026-11-06):
The user asked what to do after PC/x0 capture. The next useful phone checkpoint
is the existing Apple-launchd + xpcproxy + one C service candidate, rather than
repeating the already proven diagnostic PID 1 milestones. Fresh independent
offline revalidation in work/phone-launchd-recheck-20261106-v1 PASSed 17/17,
including payload reconstruction, ELF/embedded payload checks, native loader
tests, actual bootshim->XNU QEMU entry, LZ4 and AVB-NONE. The pinned earlier
15-check original-launchd service report was validated, not freshly rerun.
Candidate SHA256 e36b7632ff402d39db162081c2c5bb401540651ba87a38d9fdd21afd6ca80686;
report SHA256 e3e7faeb50977552385ee8c304bc54035f7ad6887492df1f844cd350f33287a6.
Original candidate files were preserved. No phone operation occurred this turn.
Android/root remain restored from the preceding capture trial. The last
explicit reflash authorization applied to the isolated PC/x0 image; this
different launchd trial awaits the user's hardware-test decision. Physical
UFS/DMA/IOMMU/resource ownership remain closed. Concrete image, validation and
recovery scope: duchamp/PHONE-LAUNCHD-TRIAL-PLAN.md. Preserve user edits.

Active handoff — runtime Image PC/x0 CAPTURED; STOCK RESTORED (2026-11-06):
The user explicitly requested repeating the isolated capture flash to read the
numbers. Same verified boot-v4/LZ4/AVB-NONE image SHA256
d4d39727f226cd1551df1f5bc11775c1cd05654fa661b1f65ae6d308902e023c;
fresh original 64 MiB boot_a backup SHA256
1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12.
Device/slot/unlock/battery preflight passed, and only boot_a was flashed
(1.768s). The new legible user photo shows:
PC=0X0000000040000000
X0=0X0000000047C80000
The capture computes runtime Android Image _head with ADR and preserves entry
x0 before C. These are observed phone values, matching the earlier static
Image/FDT address evidence. The photo SHA256 is
b4386baa506cf2db710959a9d3dfbb398ad0119d0b25120526337b6ca9b1c604,
stored privately in work/phone-pc-x0-flash-trial-v2/phone-pc-x0-observation-02.jpg.

The guarded helper restored original boot_a (1.828s), rebooted Android and
verified boot_completed=1, Duchamp/MT6897, slot _a and the live partition hash.
It exited successfully at 03:09:15 local time. Independent ADB reconfirmed the
original V816.0.17.0.UNLMIXM build fingerprint and Magisk uid=0. No restore
helper remains pending. No other partition or slot selection was changed.

Scope: Image _head and incoming x0 are now numerically observed. This photo
does not display CurrentEL/SCTLR, dereference FDT contents, transport a capsule,
or enter XNU. LK's own internal PC, capsule lifetime/ownership, dynamic reserved
allocations and UFS/DMA/IOMMU/resource ownership remain separate unknowns.
The saved static audit JSON stays immutable; its capture=false fields describe
that older offline artifact, not the newer photo. An approved boot_a route is
available for controlled trials; no no-write RAM provider was discovered.
See duchamp/PHONE-PC-X0-FLASH-TRIAL.md and MT6897-LK-HANDOFF-CONTRACT.md.
Preserve pre-existing user edits. End of latest active handoff.

Active handoff — approved PC/x0 phone flash trial (2026-11-06):
The user explicitly accepted flashing. Read-only ADB preflight confirmed
Duchamp/MT6897, unlocked bootloader, slot _a, completed Android boot, Magisk
root and 81% charging battery. A fresh 64 MiB boot_a backup was copied to the
host and verified against the live partition and original saved hash
1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12.
Live vendor_boot_a and lk_a also matched the pinned handoff evidence.

The isolated PHONE_CAPTURE Image (40,912 bytes, SHA256
2a7dff64f5e28afa5e7eef74e99ea2d3a273df367f341047891ba3a4ea6d20ea)
passed the complete native/post-link/QEMU capture suite. Its 64 MiB
boot-v4/LZ4/AVB-NONE wrapper SHA256 is
d4d39727f226cd1551df1f5bc11775c1cd05654fa661b1f65ae6d308902e023c.
The footer/hash and LZ4 byte roundtrip passed. Fastboot verified product,
slot a, unlocked state and partition size, then successfully wrote only
boot_a (1.771 seconds) and accepted reboot. This image records runtime PC/x0
and writes only the measured framebuffer after entry; it has no XNU payload,
FDT dereference, storage command or watchdog access.

Photo observation: two bright text rows are visible, consistent with the
capture renderer, but the hexadecimal digits are overexposed/blurred. Numeric
hardware PC/x0 remain unverified. Private photo SHA256 is
1f3931fd8ea8db9ca585d5698b146452d869fc3f50cc72a5694374dc12323667,
saved as work/phone-pc-x0-flash-trial-v1/phone-pc-x0-observation-01.jpg.

CURRENT STATE: STOCK RESTORED. After the user's return to Fastboot, the
guarded helper restored only the original boot_a (send/write OKAY, 1.834s),
rebooted Android and verified boot_completed=1, Duchamp/MT6897, slot _a and
the live boot_a hash against the backup. Recovery completed at 02:57:20 local
time; the helper exited successfully. Separate ADB checks reconfirmed the
original V816.0.17.0.UNLMIXM fingerprint and Magisk uid=0. The transcript is
work/phone-pc-x0-flash-trial-v1/restore-transcript.txt. Numeric physical PC/x0
remain unverified due to the unreadable photo. Do not substitute QEMU or static
addresses. No other partition, slot selection or userdata was changed.
See duchamp/PHONE-PC-X0-FLASH-TRIAL.md and the ignored trial directory.

Immediately preceding offline commits: cdab54f audits pinned UniXNU/Ruby/
Merlinx source reuse; 8bd7a53 adds the common LK/UEFI RAM contract validator
and QEMU-only integration (16 native checks plus real capsule/QEMU proof).
That contract does not supply a phone entry caller or authorize an XNU jump.
Preserve all other pre-existing user changes.
End of active handoff.

QEMU-only LK RAM bootshim integration — verified offline (2026-11-06):
Commits 818d553 and da1a463 on duchamp-bootstrap add the previously untracked
diagnostic bootshim source and connect the versioned MT6897 LK RAM provider to
the resident guard -> plan -> materialize path behind the mandatory
LK_RAM_TRANSPORT=1/QEMU_ONLY=1 build gate. The image is fixed-linked at QEMU
virt's 0x40200000 so callback tables contain correct runtime addresses. Its
first assembly instructions also require runtime _head=0x40200000 and
x0=0x48000000 before clearing BSS or touching other memory. JUMP/READY/RETURN
combinations are rejected and the QEMU-only ELF contains no
duchamp_enter_xnu branch helper. The resident XNU context now binds the
payload's declared physical window exactly to the backing output window before
any materialization write.

The complete 50,269,904-byte SWEETXNU payload was packed into a 50,269,968-byte
DUCHLKR1 capsule and streamed in 768 bounded reads. The actual freestanding
AArch64 Image ran under QEMU/GICv3 and returned a valid checksummed completion
report: 11 segments, entry 0x1c1480488, boot_args 0x1c456c000, and a clear
exception record. The full loader guard checked 52 fixed and 4 dynamic FDT
reservations without copy or jump. The 50,393,088-byte Image SHA256 is
161709c60ba0b785488021f557dac1df47ba201f701104e42be47a34e00daa1f.
The offline 64 MiB LZ4 legacy boot-v4 layout wrapper SHA256 is
3af5ebb5fb75b76567f3631bb172c729f9a7a5037e594c778e45cd5a6e625f22;
it deliberately preserves a mismatching stock AVB descriptor and is explicitly
named qemu-only-layout-not-for-phone.img. Layout JSON SHA256 is
26f4ef44192aeb7f85ad4ae5949d9c65f5000274af12fe7a832543f49042c658.

Native resident tests PASSed 806 checks, the provider suite PASSed 41 transport
checks plus 9 real-XNU checks, and both AArch64 QEMU suites PASSed. The current
150,968,880-byte payload was also tested as a negative case and was correctly
rejected because its complete image overlaps QEMU's DTB reservation at
0x48000000. Evidence is under work/validation-lk-ram-bootshim-v7; the negative
result is work/validation-lk-ram-oversize-reject-v2-reject.log. No phone, ADB,
Fastboot, partition, physical MMIO, SMC, DMA, IOMMU or UFS operation occurred.
Next: keep the hardware path closed until the stock LK image-load/FDT/reserved
RAM contract is documented independently; do not reuse this fixed QEMU image
on the phone.
End of QEMU-only LK RAM bootshim integration.

MT6897/LK inherited-RAM transport provider — verified offline (2026-11-05):
Commit 97c060e on duchamp-bootstrap adds a fail-closed provider that consumes
an immutable capsule already loaded in RAM by LK and feeds the resident loader
through bounded sequential chunks. It binds source and loader generations,
checks exact capsule/header/size/flag fields, verifies a mutation receipt both
before and after transfer, requires capsule/staging/result/scratch ranges to be
disjoint, and terminally closes the transport on every error. The capsule
packer refuses overwrite. Direct calls into LK USB/MTU3 remain intentionally
unimplemented: the saved 16 MiB lk_a sample SHA256 is
f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a,
but its strings and raw offsets do not establish a callable post-handoff ABI.
The published HakiOS MT6768 chainboot path likewise receives FDT in x0 and
uses payload bytes preloaded with the kernel image; its Qualcomm live USB path
uses a different UEFI/U-Boot protocol and is not reused.
Native ASan/UBSan provider tests PASSed 40 checks and the packer PASSed 4.
The real 150,968,880-byte payload was packed into a 150,968,944-byte capsule
(SHA256 e60228019f80da25d0b1e6e38b066ba2d6691328efbda1142ae581ae1e46fa45),
read in 2,304 chunks, materialized as 11 segments and reached prepared entry
0x1c1480488. The freestanding AArch64 object has no undefined imports
(SHA256 a909d35567611619662b8f8ccd2c68e40c369564d9933d07bb1397222df1e4b5),
and the complete provider ran as AArch64 on QEMU/GICv3 with all 12 visual rows
PASS (Image SHA256 782ef23d397813213832b2e0cb522630a4c0f1b8c9fa702c26144ccbcae93b75).
The original resident suite also regressed cleanly: 28 protocol, 2,341 real
materialization and 12 QEMU visual checks PASSed. Artifacts are under
work/validation-mt6897-lk-transport-v2 and
work/validation-resident-regression-v2. No phone, ADB, Fastboot, partition,
MMIO, SMC, DMA, IOMMU or UFS operation occurred. Next: integrate the capsule
provider into a bootshim build behind an explicit QEMU-only switch, then prove
the complete LK-image layout offline before considering any hardware trial.
End of MT6897/LK inherited-RAM transport provider.

Resident RAM-loader protocol core — verified offline (2026-11-05):
Commit 3edfdec on duchamp-bootstrap adds a transport-independent one-shot
EMPTY -> RECEIVING -> READY -> RUNNING -> RETURNED/FAILED state machine and a
bridge to the existing guard -> plan -> materialize path. Sequential bounded
transfer, mutation receipt, disjoint buffers, state-capacity revalidation,
single execution and a bounded result channel are enforced; terminal states
require a fresh loader instance. The bridge adds the live FDT and staging
physical ranges to the occupied set and never branches to XNU itself.
Native ASan/UBSan protocol tests PASSed 28 checks. The real 50,269,904-byte
Apple-launchd candidate payload PASSed 805 materialization checks with 11
segments and entry 0x1c1480488. The freestanding AArch64 object has no undefined
imports, and the actual QEMU Image PASSed all 12 visual receipt rows. A fresh
bootshim built from the hardened guard reached the XNU stage-0 marker in QEMU
with 95,500 white pixels; the immutable candidate verifier also PASSed 17/17.
The review additionally fixed overflow-safe FDT structure/string/reservation
bounds and an uninitialized-token edge case, covered by four malformed-FDT
tests. Final suite artifacts are under work/resident-loader-test-v6; the
current-guard XNU-entry replay is under work/resident-guard-bootshim-v1.
This milestone has no USB/Fastboot transport and performed no phone, ADB,
partition, physical MMIO, SMC, DMA, IOMMU or UFS operation. The next safe step
is a documented MT6897/LK transport provider that remains separate from the
protocol core; physical storage remains fail-closed.
Preserve all user edits.
End of resident RAM-loader protocol core.

MT6897 PA-to-DMA/bounce route contract/XNU replay — verified (2026-11-04):
Commits 06c27a97a996cb6fbe2eb8a3540d28c33f99222c and
2d65b02ffda3c442bcdf6c52a4c34490ee5b222c on duchamp-bootstrap add and
harden a disabled-by-default route contract. It permits only a pinned affine
PA-to-DMA window or a dedicated owned bounce pool, rechecks the exact lease and
immutable receipt on every handoff, and performs no physical MMIO, DMA, cache
instruction or UFS command. Boot-local route identities and per-route operation
identities reject stale and cross-route mapping replay. The active mapping is
cleared while state remains TO_CPU, before CPU_OWNED is published, closing the
new-operation race found during independent review.
Native ASan/UBSan and actual ARM64 QEMU models each PASSed 791 checks; the
deterministic concurrency suite PASSed 80 checks and its binary replayed
200/200 times. Current Duchamp evidence reached zero callbacks. The final
19-component saved-DTB gate PASSed in 35.137s. Route-result SHA256 is
a011df2bf04f8537725027ee9019ab34e09d09953a423958aefcf74951a88b34;
combined-result SHA256 is
693caecd777da46c3edd26cd88d63c3196e7689770307a9e090aefec856363c7.
GitHub Actions run 41731254174 PASSed all build/package/collect steps. Artifact
13276494290 archive SHA256 is
87a8bf0341eb9ef9767378d9677e92e8c46ccf33f7d986882f5597593d6dc1f6;
kernel.development.sweet SHA256 is
6fcab2806164848b031ac98dd348f14f2180f359a7fbd9edbb8e3770344e2778.
The full read-only HFS+ QEMU replay PASSed 32/32 checks in 81.108s with 16
frames, no undecodable glyphs or observed panic, PID 1 heartbeat, unchanged
host image, and 512/512 virtual timer IRQ pixels. It emitted the mandatory
QEMU XNU UFS DMA ROUTE DEFAULT CLOSED marker. Verification JSON SHA256 is
8036b9834c15fca9417e25747c25e269309bddb3f03957b9ae95214b10d7fd67;
payload SHA256 is
9cfc459f9e53f233c948612858acf75f8442e43ee7139b1fc28b80046f646e17.
This proves only the local fail-closed policy and virtual XNU path. Raw
PA-to-DMA translation, the physical SWIOTLB/bounce disposition, real cache
callbacks and firmware/resource ownership remain unproven, so physical UFS
stays disabled. No phone, USB, ADB, fastboot, partition, physical MMIO, SMC,
DMA, IOMMU or UFS command was used. See duchamp/MT6897-UFS-FAIL-CLOSED.md and
work/ci-41731254174-ufs-dma-route/qemu-backends-dma-route-v1/verification.json.
Preserve all user edits.
End of MT6897 PA-to-DMA/bounce route contract/XNU replay.

MT6897 non-coherent UFS cache contract/XNU replay — verified (2026-11-04):
Commit f3e24e3c087ce3ad1ddbc3e7bc7423e446506437 on duchamp-bootstrap adds a
lease-bound, disabled-by-default cache ownership state machine. It requires an
exact boot lease and immutable receipt, exclusive whole-cache-line ownership,
no CPU aliases, serialized handoffs, and identified clean-to-PoC,
clean+invalidate-to-PoC and barrier implementations. The contract contains no
cache instructions. Missing/stale evidence, changed receipts, wrong ownership,
callback failure or a fault before dispatch permanently denies access. Native
sanitizer and actual ARM64 QEMU models each PASSed 560 checks; the deterministic
race test PASSed 35 checks with fault-before-callback and zero range callbacks.
The six successful handoffs use only a synthetic lease and private RAM. Current
Duchamp evidence executes zero cache callbacks. The 18-component combined
offline gate PASSed in 37.919s. Result SHA256 values are
609dddf2bec639cacff52c76953cf2b45cfd750bc3394fa68b5612155b034283
(combined gate) and
c4a8448b95e4be7942a557654c6e8abf2895e4d5729bb54e096b180ffa66c9cb
(cache runner).
GitHub Actions run 41716783413 PASSed all build/package/collect steps. Artifact
13270913854 archive SHA256 is
45e93099403b3794da1e40ac57f4ed4b40864047b484ac5ba89d9f3f89efed33;
kernel.development.sweet SHA256 is
d29620071fb48f7d36b7b613bea83888ee1fc1aaf61e2ddae064c2ad685b535f.
The full read-only HFS+ QEMU replay PASSed 31/31 checks in 76.265s with 16
frames, no undecodable glyphs or observed panic, PID 1 heartbeat, unchanged
host image, and 512/512 virtual timer IRQ pixels. It emitted the mandatory
QEMU XNU UFS CACHE CONTRACT DEFAULT CLOSED marker. Verification JSON SHA256 is
66fa005d8cacd0e966fc2a8512a118773defc3ea8982ca71deff93a29e6e546d;
payload SHA256 is
b94c3e990eb012326f06d16d3d21d0f22947a6333c9e055716263fa53bebaf7e.
This proves the local fail-closed policy and virtual XNU path only. PA-to-DMA
translation, bounce/SWIOTLB disposition, physical cache implementation and
firmware/resource ownership remain unresolved; physical UFS stays disabled.
No phone, USB, ADB, fastboot, partition, physical MMIO, SMC, DMA, IOMMU or UFS
command was used. See duchamp/MT6897-UFS-FAIL-CLOSED.md and
work/ci-41716783413-ufs-cache-contract/qemu-backends-cache-contract-v1/verification.json.
Preserve all user edits.
End of MT6897 non-coherent UFS cache contract/XNU replay.

MT6897 direct-DMA/IOMMU evidence replay — verified limited result (2026-11-03):
The saved-evidence audit was rerun offline from the pinned FDT, runtime probe,
UFS client, GKI source, BL31 audit and iomem receipts. The generated report is
byte-identical to the canonical report: SHA256
71236c08c0354ff0733d44a64e505d117dfd4594e370bedd81fad3ec93d1bf4d.
All 14 mutation/polarity tests PASS. Evidence proves that Linux selected its
generic dma-direct API path at observation, no Linux UFS IOMMU group/fwspec/
domain was attached, both live masks were 64-bit and bus_dma_limit imposed a
36-bit ceiling. It does not prove physical PA-to-DMA identity, firewall or
secure-world bypass, whether a transfer used the observed SWIOTLB pool, or
cache-maintenance ownership/correctness for the non-coherent device. Therefore
DIRECT_ADDRESS_TRANSLATION, BOUNCE_DISPOSITION and CACHE_MAINTENANCE_OWNERSHIP
remain blockers and the physical provider remains unable to obtain a lease.
This replay used local files only and performed no phone, ADB, MMIO, SMC, DMA,
storage-command or partition access. See
work/dma-iommu-ownership-replay-20261103-v1/result.json. Preserve user edits.
End of MT6897 direct-DMA/IOMMU evidence replay.

MT6897 UFS lease-provider/XNU integration replay — verified (2026-11-03):
Commit 9e567ec6ac0bf7da487face7f54560e2b4dbcc56 on duchamp-bootstrap.
GitHub Actions XNU run 41707709521 PASSed all build/package/collect steps.
The xnu-kernel artifact is id 13265849833; archive SHA256 is
06b191da9897d932403070a7fb6b535d35e82c1ecbe09f7baafb615286726b46.
The extracted kernel.development.sweet SHA256 is
cba64bd6139b1bb8f8b95da3202ab8c6b1d889f1fc7cc1368eb3ffb809020cdb;
the compiled image exports the lease-provider bind/command symbols and embeds
the mandatory QEMU XNU UFS LEASE PROVIDER DEFAULT CLOSED marker. The pinned
read-only HFS+ backend replay PASSed all 30 checks in 85.912 host seconds with
16 sampled frames, zero undecodable glyphs and no observed panic. XNU mounted
the RAM root, verified root vnode and read-only UFS semantics, entered PID 1
and stopped at its heartbeat. The virtual timer IRQ witness PASSed 512/512
pixels. The in-kernel selftest reported firmware unverified, physical=0,
physical providers default closed and the lease provider default closed; it
therefore proves dispatch denial, not physical MT6897 UFS readiness. A separate
native concurrency stress replay PASSed 200/200 runs with fault-before-dispatch
and zero callbacks. Verification JSON SHA256 is
06c13a7567bfb411dd4b500fe588718471eff1d2745f1d71117bea5346fc5a96;
payload SHA256 is
4d372bf71645d7d9c7793c78f763ef7bfbdc9e46f7cc9f008ce4e11aac23d770.
All execution was local/Actions/QEMU only: no phone, USB, ADB, fastboot,
partition, physical MMIO, SMC or DMA access. The next evidence milestone is
documented direct-DMA versus IOMMU routing and cache/firmware ownership before
any physical provider can obtain a lease. See
work/ci-41707709521-ufs-lease-provider/qemu-backends/verification.json.
Preserve all user edits.
End of MT6897 UFS lease-provider/XNU integration replay.

MT6897 UFS lease-provider/XNU dispatch milestone — local verification (2026-11-03):
Baseline ee9e771, duchamp-bootstrap. Local saved files/WSL/QEMU only: no phone,
USB, ADB, fastboot, partition, physical MMIO, SMC or DMA access. Added
drivers/mt6897_ufs_provider.[ch], a disabled-by-default dispatch shell for six
operation classes: power, clock, PHY, MMIO, DMA and UFS command. Binding and
every operation require the exact activation lease. Missing/stale leases and
runtime callback failures latch a terminal fault. A fault racing before the
CHECKING->DISPATCHING authorization point prevents dispatch; future physical
callbacks still require platform locking once dispatch has begun. The opt-in
XNU QEMU backend selftest now presents the pinned incomplete Duchamp evidence,
proves the verifier is unreachable, attempts all six operations through both a
zero provider and denied binding, and requires access/dispatch counters to stay
zero. The XNU staging list now includes the provider C/H; full XNU CI compile
and guest replay are still pending and must not be inferred from local models.
The standalone v8 gate PASSed 708 native + 708 ARM64 lease checks, 140 gate
concurrency checks, 107 native + 107 ARM64 provider checks and 35 deterministic
provider concurrency checks. All denied dispatches were zero; the synthetic
valid-lease RAM model covered all six operation classes. Result SHA256 is
6e5dc0fc131bd90066e478ac2fd375d5e6a92e9738dcf31be5b15e6fe07c767f.
The source-staging suite PASSed 8/8. The combined saved-DTB gate PASSed all 17
components in 36.000s and records the lease provider as implemented fail-closed
with no physical lease. Combined result SHA256 is
8fbbcf07dffcd3222ab5dad81fa9a61c694a6b1d451244b255ea21839c33d967.
Physical UFS remains disabled. Firmware effects, resource/cache ownership,
direct address translation and bounce disposition remain unresolved. See
duchamp/MT6897-UFS-FAIL-CLOSED.md and work/offline-gate-ufs-20261103-v8.
Preserve all user edits.
End of MT6897 UFS lease-provider/XNU dispatch local milestone.

MT6897 UFS activation lease gate — local fail-closed milestone (2026-11-03):
Baseline 8d8f4164ddc738734d100ad1c0e1cc658c2faa40, duchamp-bootstrap.
Local saved files/WSL/QEMU only: no phone, USB, ADB, fastboot, partition,
physical MMIO, SMC or DMA access. Added a one-shot UFS activation gate whose
success is a boot-generation/evidence-bound, non-revocable resource lease, not
a persistent boolean. The gate has no reset/rearm API, atomically claims its
verifier at most once, validates the exact DTB/ATF/runtime/PRDT receipts and
controller/PHY/DMA route, requires owner tokens for firmware/resources/cache/
translation, and
must be checked before every future operation. Re-entry, stale/mutated leases,
receipt changes and provider failures latch a terminal fault. The saved Duchamp
profile correctly remains DENIED with blocker mask 0x000100000000040e:
firmware runtime effect, resource ownership, cache ownership, direct address
translation and bounce disposition. Its verifier was not called and all
hardware counters remained zero. Native ASan/UBSan and actual ARM64 QEMU model
both PASS the same 708 policy checks; 140 native concurrency checks plus 200
stress repetitions prove a simultaneous second authorization cannot invoke a
second verifier or publish a usable lease; the compiled
receipt extractor matches the saved DTB/ATF/runtime/PRDT inputs; the
freestanding ARM64 object has zero undefined imports. Result SHA256 is
a5b89518c41022181765b03b0e3375238368aac243119a26e42bf2470e3675dc.
UFS leaf-clock polling now has an independent bounded iteration limit when the
time source freezes: 129 sanitizer checks PASS plus ARM64 freestanding compile;
result SHA256 a42056f974cd27468452125d5277144ce0f317817f6c901e7ad7c1a9b7b04cb5.
The source-staging suite PASSes 8/8 and stages the gate C/H with the other XNU
backends. The combined saved-DTB gate PASSes all 17 components in 27.796s,
including 708 native + 708 ARM64 activation checks, 176 power, 199 DMA,
provider, GIC, timer, clock and bounded-UFS suites. Combined result SHA256 is
f82f99cfbe78d0969fb5f9d9de7582a8c8028edad9ec889d01119ab26165b4a1.
Physical UFS remains disabled: no physical lease provider exists and the five
blockers above are unresolved. Passing this milestone is not phone-test or
full-system-boot authorization. See duchamp/MT6897-UFS-FAIL-CLOSED.md and
work/offline-gate-ufs-20261103-v7/result.json. Preserve all user edits.
End of MT6897 UFS activation lease-gate milestone.

Latest XNU timer + Apple-service combined QEMU milestone (2026-11-01):
Local/WSL/QEMU only; no phone, USB, ADB, fastboot, physical MMIO or partition
access. Kernel fa23d6319ab2af1b669146bd4a17d66f6726703bee0ced8d1e607e1bc0db81d9
is the pinned artifact from successful CI 41236137474 at acb75a16cc445d86f6d60fd5345058c6a13146b7.
The first combined replay retained its failure evidence: the legacy ADT failed
the bounded GICR scan. A second replay proved qemu-profile-v4 has the correct
GIC/timer resources but predates the mandatory QEMU-only
duchamp,gic-mmio-auth-v1 capability; XNU refused MMIO with DGIC_UNVERIFIED (-8)
before any timer IRQ. The authorized ADT is pinned at
f4a27f597bce0b633733e5d479b4b43c3dfad53eaf8d5a67f52d91a9b8ac33cf;
the existing polarity test proves removing exactly that property fails closed.
system-timer-ramroot-acb75a-v4 PASS: all72 original Apple-service checks and
all8 wrapper checks in86.788 host seconds on the default QEMU clock,17 sampled
frames,zero undecodable glyphs and no observed panic. The real XNU virtual
timer-IRQ framebuffer witness is512/512 cyan pixels; the128MiB HFS+ RAM root,
PID1,launchd,notifyd,cfprefsd,four client instances,restart/recovery and saved
typed preferences all passed. Verification SHA256 is
bcc7c16d28934a8e8e7722121afebce82befe44f4ca65277e65bfe9b4beeb865;
payload SHA256 is be1be56936b7b1d8fe650969d2be41396836f4a50958cd156ec37692da4468f7.
Local commit951a869 contains only the two system-harness changes. The system
harness now accepts a deliberate ADT override only with an exact
explicit SHA256, records reference/selected provenance and rejects both a wrong
pin and an unpinned override before creating output. Witness verifier tests
PASS6/6; Python/PowerShell parsers and diff checks pass; no QEMU process remains.
The parallel saved-DTB offline gate also PASSed all12 components in17.361s:
21 boot-profile tests,138 native+138 ARM64 GIC checks plus4 actual QEMU GICR
checks,47+47 PSCI,15+15 timer-frequency,176 power,199 DMA,provider/PMIC/
firmware/IOMMU suites,146 UFS topckgen and79+79 bounded UFS polling checks.
Its result SHA256 is 363a22313a98c04b1be85be7b57788590a9228552f94cf6722a6a85fba169e82.
This proves the combined QEMU path, not phone readiness. Physical timer/IRQ
delivery, firmware/GIC ownership, the installed firmware contract, secondary
CPU power and the real UFS DMA/IOMMU route remain unverified; physical UFS and
Mali stay disabled. Preserve all existing user edits.
End of latest combined QEMU timer/service milestone.

MT6897 UFS DMA/IOMMU live contract — verified milestone (2026-11-01):
Approved read-only v2 module SHA96cd9bf422f8924c1c11b33c92d042ec0ea7fb864e756712fe45e5261be27518
loaded on duchamp/mt6897 kernel6.1.57-ab11782407, produced two byte-identical
reports, unloaded with rmmod=0, removed its staged file/sysfs attribute and left
taint unchanged12805. Exact live masks are streaming64/coherent64, while
bus_dma_limit=0x0000000fffffffff imposes36-bit addressability. get_dma_ops and
dev->dma_ops are NULL; pinned GKI selects generic dma-direct. No Linux IOMMU
private object/group/fwspec/domain was attached. Device SWIOTLB pool pointer is
present; no transfer through it was observed. Device is non-coherent and has a
DMA range map. This does not prove physical identity/firewall bypass, cache
ownership, firmware effects or safe XNU UFS. v1 is unsafe: struct module0x400
versus live0x440 caused pre-init mod_sysfs_setup panic; Android recovered and
the artifact is marked UNSAFE-DO-NOT-LOAD. Ownership audit v2 SHA71236c08...
PASS; readiness v12 SHA7ff95f51... validates the new evidence but remains
blocked/physical UFS disabled. Probe/audit/source/readiness suites PASS47 total
(8+4+4+14+17). Final read-only ADB check: Android booted, probe module/attribute/
staged file absent, vendor UFS module live. No partition, boot image, MMIO, SMC,
DMA mapping, IOMMU attachment or storage command was performed by the probe.
See duchamp/diagnostics/dma-iommu-probe/PHONE-TEST-2026-11-01.md and
duchamp/MT6897-DMA-IOMMU-FIRMWARE-EVIDENCE.md. Preserve existing user edits.
End of MT6897 UFS DMA/IOMMU live contract milestone.

Latest-kernel Duchamp phone bootstrap candidate — local milestone (2026-10-31):
Baseline e81afba, duchamp-bootstrap. No phone/USB/ADB/fastboot/partition access.
Built phone/QEMU twin payloads from kernel8d47bba (CI41156122045/artifact13025606915)
and profile-v4 ADTs. Cmdline is single CPU, framebuffer console, rootrw=0, no
root-device and no QEMU/physical UFS enable. Phone payload SHA82dd86fd; QEMU
payload SHA957997e0. Source reconstruction and embedded byte comparisons PASS.
Updated the local untracked bootshim preflight test to derive ADT/boot-args
placement from the pinned payload instead of stale smaller-kernel addresses.
Guard/materializer PASS:10 segments, entry0x1c1480488, ADT0x1c2568000,
boot_args0x1c256c000, top0x1c2570000; corrupt input performs no write.
QEMU captured-phone-FDT/8GiB jump PASS after20s with356280 white XNU pixels.
Phone jump ELF has no relocations/unresolved imports and one final indirect br.
Offline boot-v4/legacy-LZ4/AVB-NONE image64MiB verifies footer/vbmeta/boot hash;
compressed8528087 bytes expands byte-equal to shim Image. Candidate SHA256
288672ec987ef878bc457598f8f7c760855c1bc7975ada3dc7db3f754e8abc85 under
research/mt6897-phone-boot-v1. It was not deployed and is not phone-ready iOS.
Physical UFS/firmware/DMA providers remain closed. See
duchamp/MT6897-PHONE-BOOT-CANDIDATE.md. Preserve all existing user edits.
End of latest-kernel phone-bootstrap candidate.

MT6897 firmware/DMA follow-up — active work (2026-10-31):
Baseline31c15ab,duchamp-bootstrap; local saved files/WSL/QEMU only. No phone,
USB,ADB,fastboot,physical UFS or partition action. Preserve existing user edits.
Production UFS transport now requires separate provider-established descriptor
and payload DMA address limits; unknown/invalid limits fail before any I/O.
Each allocation's full extent is checked, including crossing4GiB; CAP64 is
a separate controller ceiling. Large bus aperture alone no longer rejects
an otherwise valid low32-bit pool. QEMU-only adapter supplies64/64 explicitly.
research/mt6897-routing/poll-v1 PASS:79 native ASan/UBSan +79 ARM64 model checks.
transport-v1 PASS:242 qtest/core checks,78 sanitizer guards;6 cases on read-only
images,including control32/data64 and control64/data32 with actual
emulated DMA below/above4GiB. Model CAP32/aperture and extent bounds also pass.
compile-v1:both UFS core and XNU adapter compile against generated XNU headers.
Full XNU CI41156122045 SUCCESS at8bdc1633f1180b77a732def92be54501b9251eef.
Artifact13025606915 archive SHA83d290efcbdad3363ab4bf2abc576ad66eb0ba2dc56d0a9499d77a733f7216ae;
kernel SHA8d47bba9d1f097cba15a4d4747ed28cc7f4026a7b65d87ad472eb6f8a83d731a.
API digest/internal SHA256SUMS verified. Both strict guest replays PASS:
guest-backends-v1 24/24,36.569hostsec;guest-baseline-v1 20/20,36.376hostsec.
Both17frames,defaultclock,zero unknown glyphs,no observed panic;HFS+ root,
PID1,read/error/EROFS checks;image/kernel/harness pins unchanged. First guest
also passes backend/table RAM receipt fw_verified=0 physical=0. No phone claim.
firmware-check-v1 PASS:90 native ASan/UBSan +90 ARM64 checks,28 actual SMCs
to a QEMU fixture monitor; unchanged comparison ufs_knl_ctrl() compiled twice.
MTCMOS-disabled reference returns0 without a hook call; no installed effect proof.
Comparison firmware f3083e2 blob5cb9eb7 is not identified as installed BL31.
client-audit-v1 validates13 existing source pins and saved module7043e110.
Saved query at.text0x1e80 passes selector1024 and consumes a1; comparison
handler does not implement that selector. This is a coverage gap, not proof
of the installed firmware's behavior. Saved allocation function has3
dmam_alloc_attrs calls,attrs0,alignment128/1024/1024. No module was loaded.
client-guards-v1:9 mutation/provenance/output-preservation tests PASS.
research/mt6897-routing/final-verification.json PASS:all test/source/module
pins,5 saved phone input hashes,user changes preserved;no QEMU remains.
See duchamp/FIRMWARE-DMA-FOLLOWUP.md for source offsets,pins,reproduction
and unresolved physical prerequisites. No new physical provider is installed.
Installed monitor effects/ownership and physical DMA route remain unverified;
the physical backend stays disabled. Do not infer UFS uses display/MDP IOMMU.
End of MT6897 firmware/DMA follow-up.

MT6897 boot platform — active source integration (2026-10-31):
Baseline5834326, duchamp-bootstrap. No phone/USB/ADB/fastboot/partition access.
Captured FDT timer13MHz, virtual PPI11=>INTID27, GIC four-cell interrupt
specifiers; GICD0x0c400000/0x40000, GICR0x0c440000/0x200000.
CPU reg IDs0x000..0x700,4 Cortex-A510 +4 Cortex-A715; use reg, not node names.
PSCI method smc is a saved declaration, not firmware authorization.
New duchamp_gic_boot.h fixes full MPIDR Aff3:Aff0 matching, VLPIS-aware
128/256-KiB redistributor scan, full extent/overlap validation and bounded wake.
One ProcessorSleep clear preserves other bits, then requires both sleep bits
clear; frozen timer/ignored write/failed callbacks cannot loop indefinitely.
No Distributor or ICC ownership policy changes; no SMC or physical provider.
stage-duchamp-gic-boot.py patches only DUCHAMP branch of existing pe_fiq.c,
retains non-Duchamp bodies, rejects changed/partial staging via source receipt.
Mandatory final dxb staging and CI header comparison added.
bb15237 CI41152464883 SUCCESS (intermediate scan/wake version only).
Latest check-v2 PASS:128 native ASan/UBSan and128 ARM64 model checks,
plus4 actual QEMU GICR checks; added PIDR2 validation before TYPER scan.
ELF SHA d83344e72f0180ccc7c9d05e77dce7318171149d275dc4a2e8572e4ccd71f06e.
11 staging guards and18 saved-FDT/profile tests PASS. pe_fiq.c cross-compiles
against real generated XNU headers. Local C++ compile-v2 is BLOCKED by Linux
clang lacking Apple's __builtin_xnu_type_summary/signature, not a compile pass;
Full Apple-toolchain CI41154098870 now SUCCESS at ff841ef7728a717262c00cee96fc163e12aedf8e.
New separate phone/QEMU ADTs derive saved-FDT GIC/timer/CPU facts, preserve
template software identities, omit unknown phone clocks and enable one CPU only.
Public GIC/timer source blobs pinned at kernel_common cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6.
New QEMU-profile baseline FAILED on old f6dfc1e kernel (no BSD/root/PID1);
SweetCPU only matched qcom,kryo470. Added DUCHAMP-only ARM A510/A715/A76
bindings and neutral CPU name; final new-kernel guest tests PASS below.
Clock consumer audit found undefined division with missing bus-frequency.
DUCHAMP-only ratio guards retain unknown clocks as zero and use nonzero
ratio denominators. clock-consumer-v1 executes the real transformed function:
baseline UBSan division-by-zero reproduced; unknown/zero and legacy known
clock cases PASS after change. compile-v3 cross-compiles both pe_fiq.c and
pe_identify_machine.c against generated XNU headers. No synthetic clock added.
654a3c9 CI41153721164 cancelled after superseding it with the clock fix.
Final kernel artifact13024424002 archive SHA d527cafd07e02fcebefcfdb0306cdce7f936fc4a4f432cc1e611e57064375c85;
kernel SHA a26248fa69047a6c2110f7998022d0625e8c617dd900050f098d39ed49a79232.
Verified API archive digest and internal SHA256SUMS; final kernel has ARM
CPU binding/name and bounded-GIC scan/wake markers.
guest-profile-final-v1 reached root/PID1 but FAILED strict decoding:2 glyphs
overlapped the last32-pixel diagnostic band. Corrected ADT sweet-fbcon text
viewport to2680px/83rows, retaining actual1220x2712 canvas/full mapping.
guest-profile-final-v2 PASS:24/24,33.539hostsec,15frames,0unknown glyphs,
defaultclock; HFS+ root,PID1,readonly/error paths,backend/table RAM checks.
Uses qemu-profile-v4 (ARM A76,unknown core/bus/DDR clocks omitted), not phone MMIO.
system-final-v1 PASS:72/72 original Apple service checks+6 wrapper checks,
113 installed hashes,86.640hostsec,defaultclock;unchanged legacy ADT/root.
Final profiles phone SHA efa8ca6254a0534ebe79c0c9a38b12d07b9a468a7bf32ed30c348511553e6101;
QEMU SHA 5ddf0057a50d97be8fc2a08ad88e443ab3460290f6fc532f5f4dbc063562eebe.
tools/test-duchamp-ufs-native.ps1 reproduces strict24 checks on Linux ext4
via Windows UNC, verifies source/fixture/kernel preservation; no /mnt/c VM trace.
research/mt6897-boot/final-verification.json PASS:all report/source/profile
pins,5 saved phone input hashes,user edits unchanged;no remaining QEMU process.
See duchamp/MT6897-BOOT-PLATFORM.md for reproduction and limitations.
VLPIS behavior on the actual phone is not captured or asserted by these tests.
Physical GIC/timer/scheduler/firmware readiness still unverified; no phone image
or test was deployed. Preserve1689 old notes,7 qemu classifier lines and loader edits.
End of MT6897 boot-platform handoff.

Fast system bootstrap — verified local milestone (2026-10-31):
Baseline1dae03f, duchamp-bootstrap. Host/QEMU/RAM only; no phone/USB/partitions.
New tools/test-duchamp-system-boot.py reuses the unchanged proven RAM fixture
with an explicit kernel pin; Windows test-duchamp-system-native.ps1 copies via
UNC and performs all high-frequency VM trace/snapshot/HFS work on Linux ext4.
No Apple executables/libraries modified or added to Git; copied evidence retained.
Kernel remains f6dfc1e CI41147308270, SHA
f86bd430b9fdb58d93c0f38d2009b71a7d1b5f15107ea9656c045c5a2eea99ca.
Reference RAM root89388d378c8d2fc66cf942d3c60647ad0579ebb29df629903a7bad0c44469a21.
research/fast-boot/system-native-unc-v1:72/72 actual service checks+6 wrapper
checks PASS;113 installed hashes;86.819hostsec,17frames,default QEMU clock.
Original launchd PID1/notifyd/cfprefsd/Foundation clients;4 ordered phases,
10 native launchctl calls and daemon/reader restart recovery observed.
Kernel/root/reference/sources unchanged; no complete iOS or physical device claim.
Prior same-root/probe run1691.019s used old kernel/different host workload;
about19.5x historical comparison, not controlled hardware timing/speed guarantee.
Short UFS diagnostics:default20/20 at77.515s;icount0 same fixture20/20 at32.237s;
icount4 backend fixture24/24 at39.414s. Clock selection optional/default unchanged.
Broader /mnt/c experiments interrupted during p9_client_rpc stalls, NOT passes.
User explicitly approved Ubuntu/WSL restart; shutdown/start completed, no old
QEMU processes remain and repo filesystem access recovered. Saved evidence intact.
All4 Python execution/preservation guards+2 native launcher guards/parser PASS.
Linux Python --native-workspace replay after restart:system-native-python-v2
72/72 service checks+6 wrapper checks,113 hashes,86.674sec,default clock PASS.
research/fast-boot/final-verification.json PASS:all5 positive reports/current
source closures,5 saved boot/FDT/firmware hashes,user1689+7 edits preserved;
no QEMU process left. Interrupted experiments retained, not counted as passes.
Docs duchamp/FAST-SYSTEM-BOOT.md; physical GIC/timer/scheduler, firmware/DMA/UFS,
Mali/input and SpringBoard still require separate actual validation/development.
Keep prior1689-line notes tail,7-line qemu classifier edit and loader/user files.
End of fast-system boot handoff.

Bounded UFS waits / saved boot policy — verified milestone (2026-10-31):
Baseline 50f15c39241565cdb4a87921b0fe949af2f8f4d7, duchamp-bootstrap.
No phone/USB/ADB/fastboot/partition access. Existing user changes preserved.
Fixed unbounded frozen-clock UFS waits with a mandatory finite, operation-wide
poll budget. Timeout poisons the host without reset/rebind or DMA reclamation;
deadline versus budget exhaustion is exposed to XNU diagnostics.
research/mt6897-policy/poll-v1/result.json PASS:67 native ASan/UBSan checks
and the same67 on ARM64 in QEMU (register/DMA fixture model).
transport-v1/result.json PASS:142 actual QEMU UFS/qtest host-core checks,
including a frozen timer above4GiB;78 native sanitizer guards also pass.
compile-v1/result.json:both changed C TUs compile with real XNU generated
headers, new timeout-cause core definition resolves the adapter import.
Production core commit f6dfc1e077bd196288d99d2250adfbd0b313e7b0 pushed.
Full XNU CI41147308270 SUCCESS at f6dfc1e; artifact13022331159, archive SHA
e980cee5e4e240e8595320757b6799a5be72375b6512ecf0110ccac431606c91.
Kernel SHA f86bd430b9fdb58d93c0f38d2009b71a7d1b5f15107ea9656c045c5a2eea99ca.
NEW guest-backends-v1/verification.json24/24 and guest-baseline-v1/verification.json
20/20 PASS with this exact kernel; both exit0,81.805/81.815sec,16frames each.
Actual virtual UFS/HFS+ root -> diagnostic PID1 reads/EROFS/heartbeat observed;
no sampled panic,0 unknown glyphs. No RAMDisk; both root images unchanged.
In-kernel backend/table selftest remains RAM models with fw_verified=0/physical=0.
Stopped rootPA0x1c2820000 aligned64KiB and below35bits; pool0x1c2830000/data0x1c2834000.
final-verification.json passes source closures,7 fresh public blobs and5 original
saved image hashes. All user pre-existing1689-line notes/loader/QEMU changes preserved.
Boot-policy tools/docs committed01aa3148328119598bcc6f6ba929469fbadb1b92.
New boot-policy auditor pins7 public files to the saved GKI stamp. audit-v2
finds swiotlb=noforce disables DEFAULT SWIOTLB init, disable_dma32=on disables
that zone, ufshcd_core_init is requested blacklisted. Built-in protected KVM
is only a request, not runtime proof. EXTEND command line needs951/2048 bytes;
saved vendor-boot bootconfig section is empty, bootloader-generated one unknown.
check-v2 PASS:50 native ASan/UBSan +50 ARM64 QEMU checks of3 unchanged Linux
parameter bodies with fixture capabilities; no Linux/pKVM/SWIOTLB initialization.
All9 auditor guards pass (one initial boundary-test expectation corrected).
Fresh public fetch verifies all7 exact Git blobs. Full bootargs never exported.
This refines previous default-bounce assumptions; vendor overrides remain open.
See duchamp/UFS-BOUNDS-POLICY.md. These Linux policies do not authorize XNU DMA.
Physical firmware identity/effects, DMA ownership and effective masks remain
unverified. No physical MT6897 backend enabled by these local tests.
Next: close those actual firmware/DMA evidence gaps before physical UFS use;
do not infer them from Linux policy, source replay, QEMU or a successful CI.
End of bounded-UFS handoff.

Saved-UFS firmware/DMA contract — verified local milestone (2026-10-31):
Baseline cb57481f071b3d94f0a21433e0f56dbc243638d2, duchamp-bootstrap.
No phone, USB, ADB, fastboot, module loading or partition action. Inputs preserved.
New tools audit-duchamp-saved-ufs.py / duchamp_saved_ufs.py verify saved boot-v4,
vendor-boot-v4, captured FDT, LK/preloader and 13 exact public source blobs.
Public fetch-duchamp-contract-sources.py reproduces downloads without replacing
differing files; extracted modules/fragments/images stay outside Git.
boot_a SHA1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12;
vendor_boot_a SHAd1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49.
Captured release6.1.57-android14-11-gcf2c2dc91b9e-ab11782407 resolves to public
GKI cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6. Stamp correlation only, not
byte-identical rebuild/current running state. Modules say maybe-dirty, no srcversion.
Saved IKCONFIG: IOMMU_DMA/default DMA strict=y, passthrough=n, SWIOTLB=y,
XEN=n, standard ARM_SMMU/ARM_SMMU_V3=n, ARM64 4K/PA48. modules.load requests
all six inspected UFS/PHY/IOMMU modules; load intent is not runtime evidence.
UFS module SHA7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493.
Binary ufshcd_init has 64->32 streaming-mask fallback; coherent setter's return
is ignored. Captured live HCCAP/effective post-quirk caps/masks are still absent.
No UFS iommus/iommu-map on saved ancestry; /soc DMA window remains64GiB.
Candidate: direct DMA, possibly SWIOTLB; inherited dma_ops/fwspec/vendor/secure
overrides still need proof. NULL IOMMU does not clear inherited dma_ops.
ARM_V7S display-table OAS35 is NOT the UFS mask or its IOMMU route.
Saved SMC fragments confirm client x0=c2000276, selector512(op0/1), selector8
(off/on,PRE/POST). Actual BL31 effects/return semantics remain unverified.
LK/preloader have BL31 loader/reservation strings; these are not monitor identity.
research/mt6897-contract/audit-v3/result.json: audit complete, all physical flags false.
check-v4/result.json PASS, exit0:216 source ASan/UBSan checks; same216 on ARM64;
244 saved DMA instruction checks +96 saved SMC instruction/policy checks.
12 actual SMC calls to a QEMU-only EL3 monitor, not installed MT6897 firmware.
Fifteen unchanged source function bodies; allocations/kernel DMA/SWIOTLB/cache
callbacks are fixture models. Saved .text fragments have relocated external
calls/exit branches and synthetic frames. Original MMIO/registration is not run.
guards-v2.log:8 guard tests PASS. Final ELF SHA256
7663c6219f988f3af04fbcf0d70df81cbc6385a6e93c0c170e6aa04d7146d1ea.
QEMU10.2.1 Debian1:10.2.1+ds-1ubuntu3.3. Sources/module hashes unchanged.
No production XNU backend modified; no new full-kernel CI/boot in this milestone.
Earlier XNU24/20 results belong to the previous d51e7db kernel, not this fixture.
See duchamp/SAVED-UFS-CONTRACT.md for exact scope, pins, replays and remaining gaps.
Next physical authorization needs matched monitor/build/effect and secure ownership
plus runtime ops/fwspec/domain/SWIOTLB, HCCAP and both effective masks. None can
be inferred from the saved files/QEMU results, so physical providers stay closed.
End of saved-UFS contract handoff.

XNU backend/table integration — active work (2026-10-31):
Baseline 116fef581bb1d756d82604029309580f56ab4b8b, duchamp-bootstrap.
No phone/USB/ADB/fastboot/partition commands. Preserve all existing files.
New offline 4-KiB ARM_V7S table builder: IAS34/OAS35, NS/NO_PERMS/MTK_EXT/
MTK_TTBR_EXT, finite caller-owned L2 pool, whole-operation preflight,
nonidentity CPU/physical addresses, sealed immutable tables and cache-sync
failure poisoning. No live unmap or UFS stream-routing assumption.
Pinned Android source commit 498f91c17b0822a09aede17d26a63bf8c6813725,
drivers/iommu/io-pgtable-arm-v7s.c blob08ec39111e608f6405a5777889d6ac2eda561506.
research/mt6897-xnu/tables-v2/result.json PASS:11476 ASan/UBSan checks
against six unchanged upstream encoding/decode/install function bodies,
with allocator/cache/atomic fixture helpers; no hardware table walk.
tables-v1 extractor regex failed before any C test; failure retained.
research/mt6897-xnu/compile-v3:9 C TUs compiled against real generated XNU
headers; staging-v1 has6 checks, idempotence/change rejection and all imports
resolved against the prior kernel plus the new objects. All8 staging unit
tests pass, including changed-file/partial-stage rejection and ownership.

tools/stage-duchamp-qemu-backends.py stages eight cores and one XNU adapter.
Only rd=qufs0 calls the new adapter; boot argument sweet-qemu-backends=1 and
exact QEMU firmware/ADT+Cortex-A76 gate required. No flag returns without work.
The opt-in kernel selftest uses real XNU contiguous allocation, PA validation,
cache cleaning, clocks, mutexes and read-only /dev/mbtest diagnostic output.
Peripheral callbacks are private RAM models only. Actual UFS remains QEMU PCI
read-only through the established driver. Unknown firmware contract and UFS
IOMMU selection are required to fail closed. No physical SMC is wired.
Integration 0a947b6: run41140465715 built successfully, artifact13019651368,
ZIP SHA d82a04411baafd27230be3fabc45f15726271da2449e2cd32fea401ddebc811b;
kernel fd75b80bfcef016eb37cd52b285be3b577bbff018911b517f2fb928883baf2f3.
guest-ci107-v1 FAILED before tables marker, EIO5. Read-only monitor replay
guest-ci107-diagnostic confirmed root VA0xfffffe78672a0000, physical
PA0x1c281c000 (low16bits0xc000), while table context remained fresh.
Source review found kmem_alloc_contig's VA mask does not constrain physical
alignment. Follow-up explicitly supplies a page-number mask and a 35-bit PA
limit, with PA alignment/range readback checks. Compile-v3 PASS for all9 TUs.
Fix d51e7db compiled all9 TUs locally. Parallel CI41142122133 on temporary
branch codex/mt6897-xnu-tables-d51e7db SUCCEEDED (avoided cancelling CI107).
Active branch remains duchamp-bootstrap; corrected guest results follow.
Artifact13019712695 ZIP SHA256
4dfb5b7194e18c3e2f4185e91ed5457a44c071cf09ede0eaf53c609367a8ac80 verified.
Extracted kernel matches SHA256SUMS:
fdbbca3def13fddcbef77d01504aeaabe41bfb3a7b7df94b4d7fd03fd015b92d.
guest-backends-v1/verification.json PASS24/24, exit0, 81.580s,16frames.
guest-baseline-v1/verification.json PASS20/20, exit0, 81.570s,16frames.
All backend checkpoint groups observed. PID1 exact /dev/mbtest receipt, EOF,
EROFS, root identity, raw UFS/offset/EFAULT/HFS bytes and heartbeat passed.
Read-only stopped-guest physical monitor confirmed root PA0x1c2830000,
pool PA0x1c2840000, data PA0x1c2844000; root64KiB alignment/range PASS.
Both runs zero unknown glyphs/no observed panic/unchanged images and sources,
read-only/no RAMDisk. Sampling limits and existing local runner classifier
are recorded in duchamp/XNU-TABLES-QEMU.md. All old failures retained.
Offline contract-v2 audit matched three exact GKI Git blobs, captured DTB and
saved LK/preloader hashes. UFS direct/bus-window DMA is a conditional source
candidate only; no installed BL31 contract or actual DMA route verified.
Three deliberately mutated source copies were refused by exact blob pins.
Next: resolve matching installed GKI/runtime fwspec/vendor overrides, actual
controller DMA mask/cache/ownership and matched BL31 effect semantics before
binding physical providers. No display/MDP IOMMU assignment to UFS.
End of active XNU-table handoff.

MT6897 PMIF/PMIC, SMC and partial IOMMU register backends — local milestone (2026-10-31):
Baseline f323908cbe1173c6241cf6b3ff47761d96327559; branch duchamp-bootstrap.
No phone/USB/ADB/fastboot/partition command. All previous files preserved.
New code is NOT linked into XNU or bound to phone MMIO; physical UFS remains
disabled. No installed firmware compatibility or physical regulator/IOMMU test.

duchamp/drivers/mt6897_pmif.c: matched mt6xxx SWINF2 command/data programmer,
1-4 bytes, SIDs4/8 only, 16-bit register bounds, explicit little endian,
initialized controller and route mask0 guard, finite idle/valid polling,
no stolen inherited reply, no auto retry after a transport fault.
PMIF idle is NOT PMIC ACK/NACK proof; physical error IRQ handling is absent.
mt6897_pmic.c: VEMC SID4 exact voltage table/trap-selected nibble, TMA
unlock/write/relock, factory trim preserved, enable bit only/680us delay;
SID8 vbuck3 uses matched mt6315_8-regulator ABI, selector and SET enable,
256us delay. No disable/global shutdown/mode/guessed voltage target.
Matched n_voltages=0xbf means selector191/1193750uV refused, even though
DTB and linear endpoint include it; max accepted selector190/1187500uV.
Relock is attempted even after a partial failure. Poisoned bus may prevent
it: failure remains latched, not claimed recovered. Readback is programmed
bits only, not actual measured rail voltage or PHY readiness.

mt6897_smc.S: raw SMCCC SMC#0, x0-x7 input/x0-x3 output, no default binding.
mt6897_firmware.c: whitelisted UFS requests, per-call authorization and
mandatory matched-firmware reply verification; unknown zero results refused.
Separate reference ATF f3083e2e6c508d58f9bce1b2fce5eeb0903a4c6d UFS handler
returns zero when CONFIG_MTK_MTCMOS handling is compiled out. This is NOT
installed MT6897 firmware identity. Existing LK evidence also does not prove
the installed UFS SiP effect/return contract.

mt6897_iommu.c: actual TTBR write/readback and GEN2 full/range TLB register
programming for source-defined display/MDP banks, 34-bit address encoding,
fresh-status and TLB_SYNC guards, finite CPE wait, failures pin state/tables.
Requires a preconfigured powered exclusive domain and externally built/
synchronized encoded ARM_V7S/MTK_TTBR_EXT tables. Table allocation/encoding,
SMI/stream routing, shared-domain coordination and full HW init are NOT done.
UFS client unconditionally refused before any authorization or register I/O.
No documented UFS-to-IOMMU route was found in source/inspected DTB ancestry.

research/mt6897-backends/check-v2/result.json: PASS, exit0:
105 PMIF +193 PMIC +39 firmware +87 IOMMU =424 native ASan/UBSan model checks.
SAME424 checks passed during actual ARM64 CPU execution of models in QEMU.
12 additional checks of TWO actual SMC calls from NS EL1 into a QEMU EL3 test
monitor passed, then MT6897 ARM64 MODEL PASS and semihost exit0.
This is no MT6897 peripheral/secure-firmware or XNU execution.
Freestanding ARM64 compilation of four C backends +raw SMC object passed;
all five normal-RAM objects have no undefined imports. Secure fixture uses
strict alignment, explicit byte-wise runtime, MMU/cache off.
ELF SHA256 8dba37ef2d3ca4c44c559623fe86be0346b6e79b048e36ffca28fea763fd607d.
Seven source files matched exact vendor Git blobs at commit
a805f95d61dbf0b2959c9262acc626893114321d; source catalog
duchamp/drivers/mt6897-backend-sources.json. Sources stay ignored.
Saved DTB SHA256 9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29
matched before resolving rails/PMIC IDs/SPMI offsets/IOMMU nodes.
All11 selected production/test input hashes unchanged during run and staging.
QEMU10.2.1 Debian1:10.2.1+ds-1ubuntu3.3; version log and exact commands local.
check-v1 is an earlier passing subset; check-v2 adds protected-write
enforcement and every fallible PMIF-write/PMIC transaction point.
No new XNU kernel/CI or phone image was built in this milestone.
Reference/replay: duchamp/MT6897-BACKENDS.md, tools/test-mt6897-backends.py.

Next: match installed firmware identity/SiP semantics/effects and delegated PHY
ownership; supply trusted XNU MMIO/cache/locking and regulator-vote/resource
adapters, PMIF error IRQ handling and controller quiescence/recovery.
A full IOMMU driver still needs matching table builder and actual client
routing; do not wire UFS to display/MDP/APU IOMMU based on guessed stream IDs.
End of MT6897 backend handoff.

MT6897 power/PHY policy and DMA ownership — verified local milestone (2026-10-31):
Baseline a15c2e59f212e530c600201034db6450eaa5a336; branch duchamp-bootstrap.
Source-pinned subset: duchamp/drivers/mt6897_ufs_platform.c/.h and
mt6897_ufs_dma.c/.h. Neither linked into XNU nor bound to physical callbacks.
No phone/USB/ADB/fastboot/boot-partition commands; old files preserved.
Captured DTB SHA256 9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29.
The PHY has mphy-ver=1: vendor phy_power_on/off returns without old ver=0
register programming. The new subset deliberately has no PHY MMIO callbacks.
Captured policy: RTFF enabled, no VA09 flag, IDs UniPro0/crypto1/HCI2.
Implements guarded SiP request encoding (no SMC instruction/provider),
RTFF restore/on, reference-clock PRE/request/ACK/32us/POST, bounded 3000us
and 32-poll timeout, explicit source-defined timeout notification, host-reset
order with 100us delay and captured masked-register descriptors.
Prerequisites require exclusive ownership, stable rails and all correct
parent/leaf clocks, matched SiP/PHY firmware, link off and DMA quiescence.
These are caller attestations, NOT firmware verification or physical readiness.
DMA API separates CPU VA/PA/device IOVA, refuses unknown routing, validates
alignment/aperture/overflow/mask, synchronizes private full-pool ownership
through callbacks, refuses completion/unmap while active and pins poisoned
allocations. No IOMMU table/stream-ID or bypass/coherency guess.
Saved /soc dma-ranges declares a zero-to-zero 64-GiB window; no inspected
UFS ancestor iommus/iommu-map/dma-coherent. Actual route/mask stays unknown.

research/mt6897-platform/check-v6/result.json: PASS, exit 0.
176 power-sequence + 149 DMA-ownership checks under native ASan/UBSan.
SAME 325 checks passed during actual ARM64 QEMU CPU execution of models;
MT6897 ARM64 MODEL PASS + semihost exit 0. No MediaTek peripheral or XNU run.
ARM model MMU/cache off, strict-alignment build, explicit byte-wise runtime.
Normal-RAM production objects compiled freestanding ARM64, general registers
only, no undefined imports. They use default alignment flags separately.
ARM model ELF SHA256 3788be0f0ab3f952abf38de62f00bfbb75714a5a9b262f37518a146bead8d378.
Six downloaded vendor files verified against exact upstream Git blob IDs.
Pinned vendor a805f95d61dbf0b2959c9262acc626893114321d; Linux v6.1 commit
830b3c68c1fb1e9176028d02ef86f3cf76aa2476. Source catalog in
duchamp/drivers/mt6897-platform-sources.json; sources/dumps stay ignored.
Report includes source/object hashes, selected DTB facts and upstream receipts.
Test sources still match report hashes at staging time.

Preserved failures: check-v3 timeout; check-v4 diagnosed unaligned model
pbarrier trace-store (ESR 0x96000061, ELR 0x4020486c, FAR 0x40246fcc) with
MMU-off memory attributes. Fixture now compiles strict-alignment code.
check-v5 exposed memcpy lowering with strict-alignment code; final harness
checks normal-RAM standalone objects separately and supplies an explicit
runtime for its ARM fixture. These failures are not counted as passes.
Reference/replay: duchamp/MT6897-PLATFORM.md, tools/test-mt6897-platform.py.
No new full XNU CI/kernel/phone image was required or built in this milestone.
Physical PMIC/topckgen/masked-reset providers, matched SiP return/authorization,
delegated PHY ownership, effective DMA mask/domain/stream/cache and hardware
quiescence/recovery remain unimplemented/unverified. MT6897 root stays disabled.
Next: establish those provider contracts before physical transport integration;
GPU/Mali/CSF remains separate. Do not turn model success into a phone-ready claim.
End of MT6897 platform handoff.

# DUCHAMP update — 2026-10-22

QEMU UFS / XNU integration — verified milestone (2026-10-31):
Baseline HEAD 62c91492b0bda5a764f202349b5e2141a5ee48ec.
Source adapter duchamp/xnu/qemu_ufs.c stages with the unchanged portable core
via tools/stage-duchamp-qemu-ufs.py after the existing BSD checkpoints.
Opt-in root qufs0; separate virtual firmware/ADT profile, Cortex-A76 gate,
PCI ECAM 0x3f000000/slot4, BAR 0x10000000; physical MT6897 remains unsupported.
BSD strategy has bounds, read-only policy, serialized bounce reads, residuals
and biodone completion. DMA allocation is permanent; callbacks clean/flush
physical cache lines and preserve poisoned/in-flight memory ownership.
Local Actions-104-generated-header compilation passed for both C TUs;
all their imports resolve against the baseline kernel/each other.
Local IOKit C++ compile cannot validate Apple XNU compiler builtins on Linux;
its failure is retained in research/xnu-ufs/compile/IOKitBSDInit.log.
First full Xcode CI succeeded, but guest-v1 is a FAILED runtime test: UFS
root mounted and PID1 entered, then raw character read panicked at memmove
+0x48 / qu_strategy+0x1c0, FAR=user stack. physio/buf_map returned a user VA
that plain memcpy cannot access with PAN enabled. Its failed outputs remain.
Fix now uses uiomove from a private CPU buffer outside the controller lock;
B_PHYS strategy requests are rejected. Both C TUs recompiled successfully.
Full Xcode fix CI succeeded; exact new kernel passed both guest tests below.
CI source commit 51bd2ca39c97d441df912a9a12e31cf24ea7a601; run 41131664525.
PAN fix commit 9a10068375fa1320d802e3d30fe951f8b1a07f4f; run 41133993461.
Kernel artifact ID 13015622163, ZIP SHA256
cb11ed54942844c14f12346a1c3c8121d90777a9038896442e4c1be5181c668f,
matched GitHub digest. research/xnu-ufs/kernel-fix-ci/kernel.development.sweet
SHA256 c40bebddeaea04c11ca8f4812de8160490ba8933ee68bc63a9481ed257d82109,
matched artifact SHA256SUMS. No kernel stubs/rebuild after download.
research/xnu-ufs/guest-v2/verification.json: PASS 20/20, exit 0,
80.493 host seconds, 16 sampled frames. Real XNU HFS+ mount/rootvnode via
qufs0 (no ADT RAMDisk), PID1, root st_dev matches qufs0 st_rdev with valid
inode types, raw header and offset reads, invalid user pointer returns
EFAULT without panic, write-open returns EROFS, exact 1024 file bytes,
and later heartbeat. Zero unknown glyphs/no observed panic. Read-only host
image unchanged, kernel pin and all five test-source hashes preserved.
Early QUFS printf/IOLog is not framebuffer-visible; stat64 device identity
and no-RAMDisk gates establish the root source. The legacy marker
QEMU RAM ROOT MOUNTED alone does not establish its source.
Fixture research/xnu-ufs/fixture-v4 root SHA256
5f4f6b5c5a7947dcab9e2c56f668b719053b89a5f07dc256f255e11fdbec3440.
research/xnu-ufs/md0-regression-v1/verification.json: PASS 10/10, exit 0,
89.932 host seconds, 18 sampled frames. SAME new kernel, old RAM root/static
PID1 and later heartbeat, no UFS-image option, zero unknown glyphs/no observed
panic, kernel/root unchanged. Base HFS+ SHA256
e5b5c1b68c00db65ae31d8d29baef6ab88c8131e29940d8ce7b810536726414a.
These sampled short boots are not long-term stress or phone tests.
The existing 7-line uncommitted qemu-sweet MEMORY READY diagnostic remains;
its classification branch was not exercised. Exact working hashes are in report.
The new qu_read/qu_error bodies passed 18 ASan/UBSan control-flow model checks
in research/xnu-ufs/uio-model-v1. This is not XNU VM/PAN execution proof.
Virtual-UFS fixture prepared with no fallback ADT RAMDisk;
tools/test-qemu-ufs-profile.py passed 19 rejection tests.
Six MT6897 AO/PDN clock leaves implemented separately, not linked to a phone
backend; 123 ASan/UBSan model checks and ARM64 compile passed in
research/xnu-ufs/clocks-v2, including captured-FDT ID/provider matching.
Baseline tree ZIP SHA256 b2cf5bc24205c978858eb8667d7a9c65dfe66a87d1d56399efda9c34c76da333.
Native WSL build cache path is in research/xnu-ufs/base104-tree-path.txt.
No phone/USB/UFS hardware/boot-partition command. Preserve all previous files.
Reference/replay: duchamp/QEMU-UFS-XNU.md; scripts refuse output overwrite.
No complete physical power/PHY/reset/SiP, topckgen mux, DMA/IOMMU backend or
Mali CSF acceleration. Six model-tested clock leaves do not power on UFS.
Next: match firmware ownership/SiP/PHY/reset and DMA mapping/cache contracts
before connecting physical MT6897 transport; identify selected Mali DDK/CSF
firmware and design MMU/queue/fence/power backend independently of Adreno.
End of active XNU-UFS handoff.

Portable storage/software-graphics cores (2026-10-31; this commit):
Baseline HEAD 6b93481421300eeebc124813a2998bed140fda5f; branch duchamp-bootstrap.
No phone/USB/UFS hardware or boot-partition command. No new XNU build or CI.

Implemented independent portable C UFSHCI read transport and raw 32-bit
software framebuffer fill/blit, with offline hardware-dependency extraction.
These cores are NOT yet linked into XNU. MT6897 root selection stays
kIOReturnUnsupported; there is no physical MediaTek power/DMA/MMIO backend.
No complete iOS, accelerated GPU, DSI scanout or phone-UFS claim.

Actual tests: research/mt6897-drivers/core-v6/result.json, exit 0,
108/108 checks. Real QEMU UFS emulation/DMA via qtest, guest CPU stopped.
Three cases: generated 16-MiB read-only disk at DMA 0x100000 and
0x100100000, then existing 32-MiB HFS+ root at above-4GB DMA. Five exact
byte-comparison reads per case, including 256 KiB and the last block.
All images unchanged; HFS+ source SHA256
491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f.
This is transport evidence, not an XNU UFS mount. Controller version 0x400.
Injected task-tag and completion-mask faults are separately identified.
No arbitrary CDB/SCSI WRITE API; only NOP, fDeviceInit queries and SCSI reads.
Cold-device UNIT ATTENTION retry is bounded to three valid sense responses.
Timeout/error poisons the host; API blocks rebind/resubmit. DMA storage stays
reserved until a real platform proves quiescence; no automatic reset/abort.
Readiness flag is a caller precondition, not proof of firmware compatibility.

Same run: 78 native guard checks under ASan/UBSan, exit 0; freestanding
AArch64 compile of both C cores passed, llvm-nm undefined imports empty.
research/mt6897-drivers/framebuffer-arm-v2/result.json: 3/3 checks, exit 0.
Actual ARM64 raster code ran at EL1, MMU/cache off, in ordinary guest RAM
at Duchamp framebuffer address/geometry (1220x2712, stride 4992).
Every pixel, row padding and outside guard matched; capture SHA256
2be9fd76292a0edafb0fc52d54f2d3bf029911cfb6674554659d9a55df3ec3ac.
No hardware GPU, framebuffer mapping/cache-on, vsync or scanout test.
tools/test-inspect-duchamp-hardware.py: 20 tests, exit 0; actual phone DTB
inspection succeeded; captured DTB SHA256
9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29.

DTB facts: UFS 0x112b0000+0x3000, compatible mediatek,mt8183-ufshci;
PHY 0x112a0000+0x10000; 12 named clocks, 3 resets, 9 four-cell IRQ tuples;
Mali 0x13000000+0x480000, five named IRQs and memory-provider references.
Absent iommus/dma-coherent is NOT proof of bypass/coherency. The inspector
resolves variable provider cells and bus translations without bootargs/serials.
Selected report research/mt6897-drivers/hardware-v1.json remains local.

Read pinned MediaTek device modules a805f95d61dbf0b2959c9262acc626893114321d
and vendor modules 6bceb1b8e3444dd6caf80ad7470c9e57bbdcd1ab. UFS variant
needs PHY, clock/reset, power and SiP/RTFF-MTCMOS sequencing. GPU source
has CSF/firmware/MMU requirements; installed phone DDK/firmware ABI remains
unidentified. Independent implementations only; external sources stay ignored.
QEMU reference source 7f36b1fbeb1f6f070cd5f8eddb3edbcafac15440 differs
from tested installed QEMU 10.2.1; no firmware behavior equivalence claim.

Failures retained: core-v1 wrong test PCI BAR-width assumption; core-v2
unhandled cold UNIT ATTENTION. ARM-v1 overlapped the default QEMU DTB;
ARM-v2 relocates its ELF. Later passing runs have exact input/object hashes.
Replay/scope/pinned source links: duchamp/DRIVER-CORES.md.
Next concrete work: XNU read/completion adapter in separate QEMU storage
configuration while retaining md0; separately derive the MT6897 PHY/clock/
reset/SiP and DMA/cache ownership sequence from matching firmware evidence.
Physical backend stays disabled; Mali needs its own CSF/MMU/fence/power ABI.
All pre-existing edits, untracked trees and 1689 old NOTES additions preserved.

Grouped live-preferences/restart milestone (2026-10-30; this commit):
Baseline HEAD 8e7565855a862b5018c337d032f28dddedcd2e90. QEMU/RAM only.
No phone, USB, UFS or boot-partition command; no new kernel build or CI run.

Successful run: work/launchctl-cfprefs-batch-v2, exit 0, 72/72 checks.
All 113 file hashes matched; unchanged Actions 104 kernel and original
Apple launchd/xpcproxy/cfprefsd/notifyd/frameworks. Runtime audit: 92 binaries.
1691.019 host seconds, 70 sampled frames, no visible panic,
zero unknown glyphs, stopped on the second-heartbeat text (>=2 beats).
Writer PID 7, first reader1 PID 5, new reader1 PID 16,
reader2 PID 6. Original cfprefsd changed from PID 9 to 13,
runs=2. Original notifyd stayed PID 8, runs=1.
All ten real CLI calls exited 0. Writer and reader2 runs=1, reader1 runs=2,
all normal exits=0 and reaped; old daemon was forcibly restarted, not graceful.

Four ordered phases: set/read generation 1; live update to generation 2;
after daemon restart plus orderly stop/restart of reader1, read generation 2
without setters; then write/read generation 3 through the existing writer.
Reader2 remained alive across all four phases. Both clients acknowledged
every applicable phase. All four probe instances entered an empty chroot
after independent-domain warmup; direct preference paths stayed ENOENT.
Saved final plist exactly device=DUCHAMP-RECOVERED, integer soc=6897,
boolean enabled=true, integer generation=3. Chroot directory stayed empty.
Signals were explicit program posts through native notifyd after synchronize;
notification state/control files carried only step numbers, never values.
No automatic NSUserDefaultsDidChangeNotification or FSEvents delivery claim.

First attempt work/launchctl-cfprefs-batch remains a failure: two live-update
phases passed, then the test checked PID 13 while it was still xpcproxy.
Bounded executable-transition waiting fixes this harness race. Its 113 file
hashes matched; intermediate phase2.json proves actual saved false/generation 2.
Sources/headers are frozen in each run's test-sources/ with input hashes.
Basic writer, reader and controller rebuilt byte-identically to v5 in
work/cfprefs-basic-build-check-v2/comparison.json; no baseline VM rerun.

Parallel review: hakios-metal commit 54a46fadec5bd9684ebd77f3a0834c84b5eb01a6.
make test CXX=clang++ passed 21 tests, 0 failed checks on Linux FakeGpu.
Checkout clean, MIT, no iOS build or device GPU run. Parser/state semantics
are useful references; actual transport/PM4 are Adreno-specific and the
repo's shader pipeline is unfinished. See HAKIOS-METAL-REUSE.md.

Initial root SHA256 89388d378c8d2fc66cf942d3c60647ad0579ebb29df629903a7bad0c44469a21.
Payload 8c1c249fd0940b03bfca7ac7781d721e328230a680bb59427e93545177b08635.
Saved root 03532c1d4e832f36ca6d3f992e1df619239afb364aa4b3ff5c9af9723658ed58.
Full report: work/launchctl-cfprefs-batch-v2/run/verification.json; guest/ logs.
Docs: duchamp/CFPREFS-BATCH-QEMU.md and HAKIOS-METAL-REUSE.md.
Remaining: MediaTek platform/storage/graphics contracts and device tests.
MT6897 root selection still returns kIOReturnUnsupported; RAM tests prove
no UFS driver compatibility, phone full-boot or complete iOS readiness.
All earlier local edits and 1689 old NOTES lines remain unstaged.

Original cfprefsd / isolated NSUserDefaults milestone (2026-10-30; this commit):
QEMU/RAM only. Baseline HEAD bea1e346cbd0ec005a5fc63dbd05cb504d90916e.
No phone, USB, UFS, fastboot or boot partition command was run.
No new kernel build or Actions run. The Actions 104 kernel is unchanged.

Successful run: work/launchctl-cfprefs-v5, exit 0, 49/49 checks passed.
112 file hashes matched: 110 installed files plus original launchd/xpcproxy.
978.85 host seconds, 75 sampled frames, zero unknown glyphs, no visible panic;
stopped on the second success heartbeat before the 1500-second limit.
Observer PID 3; writer PID 5; separate reader runs PIDs 12 and 15.
Original regular cfprefsd PID 7 stayed running, runs=1, same PID before/after.
The separate system-session job stayed unstarted, runs=0; not exercised.
Ten real Procursus launchctl invocations exited 0. All three probes exited 0,
were reaped and stayed stopped for two heartbeats. Daemon shutdown not tested.

Every probe warms only org.sweet.qemu.runtime-warmup (unset key, no setters),
then enters an empty chroot and changes cwd to /. The actual fixture suite
org.sweet.qemu.preferences is first accessed after isolation. Direct creation
and later direct reading at all three standard preferences paths return ENOENT.
Writer sets device=DUCHAMP, integer soc=6897, boolean enabled=true. Both fresh
isolated readers obtain all three values without setters. The saved real-root
plist contains exactly those values/types. The saved chroot directory is empty.
Regular outside descriptors carry only console/log/PID/release data, not values.
No injected library, fabricated XPC reply or per-message trace is claimed.

Pinned original cfprefsd: 05e6c217284c2e4f669243fe24296f3ba9abb53a750c9d3860348b0b43c978e2.
Runtime: research/cfprefs-runtime-20F66-v2/runtime-root, 92 audited binaries,
107016192 bytes plus seven existing Foundation resources. Apple files local only.
The first 85-file image crashed: CF dlopen of MobileCoreServices was missing.
Debug PC=0/LR=0x100e22fd0 matched CF file offset 0xfafd0 (FSEventStreamCreate
indirect call). Adding the original MobileCoreServices/CoreServices closure
fixed this daemon crash. See duchamp/CFPREFS-QEMU.md for pins and exact replay.
Attempts v1-v4 remain preserved and are failures, not successes. Interpose
hooks never ran; that method was removed. Chroot-before-runtime-init also
crashed; independent-domain warmup before chroot is verified in v5.
The later chroot failure was FAR=8/nonzero ELR; its exact function is unknown.
The periodic-frame debug observer caught a normal pause, not a null fault.

Root SHA256: 14dde88259e13d1f5c352d7eee4ec1c7c02afd74305180626db54e119f86abba.
Payload: 33579779ba49f0fb307bf9a0e7e5eee47c6f0fc7f70aec58f58234be1f399f68.
Saved root: a648ed135606d03c51dcc1f838ce0310d936ea95b5c72ab78eabdac1bc2173f7.
Full report: work/launchctl-cfprefs-v5/run/verification.json; guest logs in guest/.
Next: live preference updates/notification invalidation between clients.
FSEvents change delivery, reboot persistence, sandboxed app domains, UI and
MT6897 hardware support are outside this test. No complete iOS claim.
Pre-existing unrelated local edits and 1689 added NOTES lines stay unstaged.

Original notifyd integration milestone (2026-10-30, QEMU/RAM only; this commit):
Original iOS notifyd now runs beside original syslogd, with two-process
notification state/post/cancel and notifyd-controlled ASL remote filters.
Baseline HEAD: 263e74fdd5d061528c2d5d9e75bf1799f9dd89c4.
No phone, USB, UFS or boot partition command was run.

Successful run: work/launchctl-notifyd-v3, exit 0, 74/74 checks passed.
51 installed file hashes and original launchd/xpcproxy/syslogd/notifyd
hashes matched. 536.613 host seconds, 42 sampled frames, zero unknown
glyphs, no visible panic. Stopped on second heartbeat before 1500 sec.
Observer PID 3, syslogd PID 4, probes PIDs 5/6, notifyd PID 7.
All six real CLI print processes exited 0. Both daemon before/after
prints matched: same PID, running, runs=1. Both probes returned 0,
were reaped, runs=1, no restart through two heartbeats. Both daemons
were alive at the stopped guest snapshot; graceful shutdown not tested.

Both probes registered plain IPC tokens for the same non-self name.
Initial state=0, initial changed=1 then quiet=0 were proven. Probe 1 set
and posted 0x1020304050607001; both probes received the exact state.
Probe 1 cancelled its check token (valid=0/check status=2), then set
and posted 0x1020304050607002. Only probe 2 received it; the cancelled
token stayed invalid. Remaining tokens were cancelled. The synchronization
files carried only done tokens, not notification state. Daemon debug
confirmed the name and cancellation calls; the real resolved name_id
was 1, distinct from the internal IPC-version name.

The observer set com.apple.system.syslog.master to 0x300ff, read it back,
then posted com.apple.asl.remote. ASL probes used options 0x20000000
(NO_REMOTE clear, SHIM_NO_TRACE retained). All six runtime evaluations
were 0x00230005 with TUNNEL set, and six exact raw records reached the
original syslogd file with expected root sender identities. The master
state was restored to zero and its token cancelled. Modern os_log/logd
and arbitrary credential-forgery behavior were not tested.

Native source: research/notifyd-20F66/apple-extracted, selected from
20F66 system-image member 096-04088-077.dmg with existing APFS range-cache
helper/7z. Extraction exit 0: 2 files / 129501 bytes. notifyd is 128704
bytes, plain arm64, iOS 16.5, libSystem/libbsm, dyld. Original job 797 bytes,
MachServices com.apple.system.notification_center and PublishesEvents
com.apple.notifyd.matching retained in the copied job. Test adds root/
System, RunAtLoad=true/KeepAlive=false and -d/-log_file/-shm_pages 0.
Original executable/library bytes are unchanged. Partial APFS cache is
not a complete-image digest or independent Apple signature verification.

Actual binary LC_SOURCE_VERSION/library PROJECT string identify 312.
Matched Apple Libnotify-312 source commit:
885677be0379101ccf37b46f8da81dbc17d6d301 (not exact build equivalence).
The first two attempts, work/launchctl-notifyd and -v2, FAILED after
298.05 and 297.615 sec. First combined assertion hid the native result;
the second separately logged registration 0/token 2 and get_state 0 with
0x0000000700000003. Server log showed get_state_2 name_id=0.
Matched 312 source explains zero-page register_check delegates to plain
without filling name_id, leaving zero; the client then reads IPC version
(PID<<32|3). Final fixture uses notify_register_plain/NID_UNSET, preserving
the exact-state assertions. No binary patch and no claim register_check/
get_state works with zero shared pages. Failure diagnostics sync before
FAIL to preserve newly created HFS entries; first attempt had missing
new log entries despite visible console execution. All attempts retained.

Runtime: research/notifyd-runtime-20F66-v2/runtime-root.
42 binaries / 11006176 bytes, no missing strong dependencies.
Replay: tools/test-sweet-launchctl.sh with original Actions 104 kernel,
qemu-multiproc.adt, launchd-final/root.hfs, new runtime, HFS tool, fresh
output, 1500 and notifyd. Details: duchamp/NOTIFYD-QEMU.md.
Report: work/launchctl-notifyd-v3/run/verification.json; raw files in guest/.
Old syslogd saved guest recheck passed 43/43 with final verifier:
work/syslogd-notify-final-recheck.json; original report preserved.
10 observer modes/probe compile checks, Python/shell checks passed.
No kernel change or new CI. Pre-existing dirty files/NOTES edits preserved.

SHA-256:
notifyd 819c8ec6b3bee5cd2f1dcbe0b2b698418c411b4c126f2f97cbdae932c1972907
notifyd original plist 627b24feb59a493a50f488bc62ec9e878c333757d4ddb7786a977650ed9b1a05
probe1 d75e313663319e78e301954ece5698e8fc2c4f7527b8324494a9c82ff0003267
probe2 4c75ae7555275a5cc7a906c408cb6944451979aafab3bdd56f62f0ef38555f7f
observer f364f0dee8bef980589bdff407e35d7bb77e134248234967f9c7519513d23b28
input root 3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf
payload eacdc56581aa13cc14c0fd36feb8041a1e71b0aacb14715793d4ece58e8a676e
exported root e942200c5f595f8918aa7e39935d2e39bc4aea0999af57eac19d7f442e5b9583
raw ASL log f41a71dafad74ffd53ecc98175fcf71957487dc4423cbe4010140f77f3c17bce
Rehashed unchanged kernel/base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Coverage: plain/check polling over IPC, state and cancellation, and ASL
remote-filter integration. Shared memory, dispatch callbacks, daemon
restart recovery, UIKit, SpringBoard/full iOS and MT6897 drivers remain
unproven. No VM is left running for this completed fixture.

Original syslogd milestone (2026-10-30, QEMU/RAM only; this commit):
Unmodified Apple iOS 16.5 restore syslogd now receives legacy ASL messages
from two C programs and writes six real raw records to its own log file.
Baseline commit: 9f101800fbbcf958c511ab7350d3853cd99aa374.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-syslogd, exit 0, 43/43 checks passed,
49 installed file hashes and original launchd/xpcproxy/syslogd hashes
matched. 397.172 host seconds, 31 sampled frames, zero unknown glyphs,
no visible panic; stopped on second observer heartbeat before 1200 sec.
Observer PID 3; original syslogd PID 4; probe PIDs 5 and 6, root children
of original launchd PID 1. All four CLI print processes exited 0.
Server before/after prints were identical: running, PID 4, runs=1.
Both probes sent three messages, returned 0, were reaped and stayed
stopped. The original daemon remained alive through final heartbeats;
the fixture does not test its graceful shutdown.

Inspection: original syslogd is plain arm64, iOS 16.5, 166848 bytes,
direct imports libbsm.0.dylib and libSystem.B.dylib; dyld /usr/lib/dyld.
Original 347-byte job is Disabled=true, KeepAlive=true, MachServices
com.apple.system.logger, daemon environment ASL_DISABLE=1.
The RAM copy enables the job, disables KeepAlive, adds root/System
identity, diagnostics and module flags; executable bytes are unchanged.
Daemon ASL_DISABLE=1 is retained to avoid self-logging. Probe jobs set
ASL_DISABLE=0 and open ASL with NO_REMOTE|SHIM_NO_TRACE=0x20000004.
Actual runtime eval for all six messages: 0x00030005, SEND_ASL set,
TRACE/local-file bits clear. No probe opens the daemon output path.

Native daemon debug receipts contain all six tokens at
__asl_server_message. Independent host parsing of sweet-asl.log verified
exactly six records with expected Message/Sender/Facility/Level/custom
fields and matching PID/UID/GID. This verifies expected root senders;
forged credential fields and unprivileged senders were not tested.
Readiness, begin/exit gates and actual job exit/PID files were checked.
launchd still logged persona lookup and legacy launch(3) activation
warnings; they did not prevent the observed legacy ASL path.

Local runtime: research/syslogd-runtime-20F66/runtime-root.
Preparer: tools/prepare-syslogd-runtime.py; 41 binaries / 10877472 bytes,
no missing strong dependencies. Original extraction:
research/syslogd-20F66/apple-extracted, from the pinned restore.apfs.
Reference Apple syslog source commit 69d8586e9a599c304e1b702a9c2830e2f78126d5
was read for flags/config/ABI, not claimed to exactly match this build.
Required exports were separately checked in the real pinned library.
Nine observer modes and the C probe passed arm64 checks with -Werror;
shell/Python checks passed. One VM run, no kernel change or new CI.

Replay: tools/test-sweet-launchctl.sh with Actions 104 kernel, existing
qemu-multiproc.adt, original launchd-final/root.hfs, the new runtime,
HFS tool, fresh output path, 1200 and syslogd.
Details/replay: duchamp/SYSLOGD-QEMU.md.
Report: work/launchctl-syslogd/run/verification.json.
Raw log, daemon debug, CLI and extracted files: its guest/ directory.

SHA-256:
syslogd 86838d9149bb898e3d39266fea884c6c92eeac1e6486c072b135a879c9eeaabe
original plist 86ce6512803e6a20c04834f155a38e1b1a24ff66c9452a57850f65bf2056d5fe
probe1 81d467a90d7b76a5427b3c62832ec9589c9b6d8fa16e84a80726310ef813f6b8
probe2 6b4b55dce920698153bbf6e56b09cff5c95890ae05a064c4f5d7b02279adf305
observer b8731a57adffe79f10ddea2cffbb321635da1d3844659ba3e697d4ea1571ae26
input root 24a366af70ac1e3d30cda31e6cad4708c80f47bb899f8278cd194f3df159cc7d
payload 16c324fe03a318c8b2031e89c4f2407be0f2787ed64dab7eab7b1244b4b2bfee
exported root bdf674d4e60e53d321aa98e38c39306846d323f2500cf67d7604c35d4ed056eb
raw ASL log 1e4be882410f11880afc0e9821d7e55c51ce35eb1ecdd8ba0ded54103ffdb65a
Rehashed unchanged kernel/base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Coverage is the original daemon's legacy ASL receive/file path. Modern
os_log/logd, notifyd, rotation, arbitrary input, UIKit, SpringBoard,
full iOS and MT6897 hardware compatibility remain unproven.

Foundation/XPC batch milestone (2026-10-30, QEMU/RAM only; this commit):
Two live clients now exercise two on-demand server generations and six
representative malformed-request cases in one grouped QEMU boot.
Baseline commit: a4b9d8956aed9683fad4ea01d987b56ee1bb6af9.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-foundation-xpc-batch, exit 0, 83/83 checks
passed. All 96 installed file hashes and the original launchd/xpcproxy
hashes matched. 916.589 host seconds, 69 sampled frames, zero unknown
glyphs, no visible panic; stopped on the second observer heartbeat,
before the 1500-second limit. The user interrupted the conversation
during the boot; the existing run finished in the background. Its
completed report and raw logs were reviewed on resume; no second boot.

Observer PID 3 and client PIDs 4/5 were root children of original launchd.
Server PID 7 initially activated from native traffic, returned 0 after
SIGTERM and was reaped. Clients stayed alive and reopened connections;
native traffic activated server PID 11. Prints showed runs=0 initially,
runs=1 after first activation/exit and runs=2 after the second.
All nine real CLI processes exited 0. The observer issued print and kill
only, with no kickstart/bootstrap/start. Both server instances and both
client jobs finished with last exit code=0 and stayed stopped through
two heartbeats. The MachServices name remained registered.

Each server held two live connections; every one of the 36 data replies
reported active=2. Per-peer handlers share one private serial dispatch
queue, so this is concurrent live clients with serialized processing,
not proof of parallel Foundation callbacks. Four hellos and four closes
were recorded. Each client/generation sent three valid JSON requests
and six rejected cases: syntax, wrong XPC type, missing data, 4097-byte
payload, wrong JSON field type, and an envelope PID differing from the
actual XPC peer. Exact statuses 1..6 were returned on the same connection.
Valid requests after errors succeeded; totals: 12 accepted, 24 rejected.
All 36 saved JSON files independently decoded correctly; all 12
server/client reply pairs were byte-identical. Valid per-operation pool
drains appeared in order. No runtime exception or diagnostic failure.

Replay: tools/test-sweet-launchctl.sh with the previous kernel/ADT/base,
research/foundation-runtime-20F66-v2/runtime-root and HFS tool, a fresh
output directory, 1500 and foundation-xpc-batch.
Details: duchamp/XPC-BATCH-QEMU.md.
Report: work/launchctl-foundation-xpc-batch/run/verification.json.
Raw CLI outputs, logs, JSON and extracted installed files: its guest/.
Eight observer modes and the two new Objective-C peers passed arm64
syntax checks with -Werror; shell/Python checks passed. Required new
XPC/dispatch exports were verified in the pinned runtime before boot.
An initial Objective-C identifier conflict was corrected before boot;
there was only one VM run. Earlier scenarios/images remain preserved.

SHA-256:
server 90894c0b02d38a112c4976cb6d6142859fc5f37e937a81f20873d6a108b61e22
client 1543a5c511277b84f5f9daea8d3b898a2b246b5594edc17c70c4169bd4b749bd
observer 44ca3b85ed2605305ee9bf277dd497333fb12119f6a75f6157ba7651a22d9458
input root 62671e29f50f6fd4d97df7a05b2f0d0cbc0d92cca133e011598f9043e41815cd
payload ca55c15c2f94de7a0b25dedfbf29d6c583522abe0d9a3f7e03f0e7c83b9d531e
exported root 125024bf1c51cd7bf03d262cecb06eeacf8f77c3da33826c55e7e771502d8206
Rehashed unchanged kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

This is a bounded fixture, not a fuzzer or a production IPC server.
Arbitrary malformed traffic, stress, NSXPCConnection, UIKit, SpringBoard,
full iOS and MT6897 storage/drivers remain unproven.
Next useful system step: inspect an original system daemon and its
runtime/job dependencies before adding a QEMU-only service test.

Foundation/XPC integration milestone (2026-10-30, QEMU/RAM only; this commit):
Original Apple Foundation now processes JSON in both native libxpc peers,
with on-demand launchd MachServices activation and orderly exits.
Baseline commit: 97d940bb47a0a3ce62fa62fc3aaea615eee3d3d7.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-foundation-xpc, exit 0, 56/56 checks passed,
95 installed file hashes plus original launchd/xpcproxy checks passed.
531.312 host seconds, 40 sampled frames, zero unknown glyphs, no visible
panic; stopped on second observer heartbeat before the 900-second limit.
Observer PID 3, client PID 4, server PID 6, root children of launchd PID 1.
Initial server print had runs=0 and no PID with its Mach name registered.
Only after that print did the observer release the client; native XPC
traffic activated the server without any manual start command.

Both peers are Objective-C/MRC with blocks and exceptions. Three JSON
requests passed through NSDictionary/NSJSONSerialization/NSData into
native XPC data. Server checked received classes/fields against the
integer envelope, uppercased duchamp to DUCHAMP, added fixture soc=6897
and XOR-transformed values. Client parsed and validated every reply.
Each request was 46 bytes, each reply 58 bytes. Nine atomically saved
JSON files independently decoded correctly on the host; all three
server/client reply pairs were byte-identical. All nine per-operation
autorelease-pool drains appeared in order, including worker callbacks.

Six launchctl commands exited 0. Client cancelled its connection and
returned 0; server saw connection invalidation, handled SIGTERM,
cancelled peer/listener and returned 0. Final prints: not running,
runs=1, last exit code=0. Both PIDs reaped and stayed stopped through
two heartbeats. The MachServices entry remained registered.
Original Apple libraries, launchd and xpcproxy remained byte-identical.
CLI remains pinned Procursus FOSS launchctl 1:1.1.1, not Apple's CLI.

Replay: tools/test-sweet-launchctl.sh with the prior six inputs,
research/foundation-runtime-20F66-v2/runtime-root, fresh output directory,
900 and foundation-xpc. The copied HFS root is 128 MiB in RAM.
Details/replay: duchamp/FOUNDATION-XPC-QEMU.md.
Report: work/launchctl-foundation-xpc/run/verification.json.
Raw logs, nine JSON files and file extractions are under its guest/.
Earlier native-XPC saved guest recheck passed using a separate report
work/xpc-integration-tools-recheck.json; original report preserved.
Seven controller modes, both integrated Objective-C peers, old C XPC
peers and standalone Foundation compile checks passed with -Werror.
Python/shell checks passed. No kernel change or new Actions build.

SHA-256:
server 2a72fb59c4baa0228cd578639aedb851f131d05dccf057b2f6f1036200749926
client ef5647df2d8ae691da4158ee99e6880fa7a65a5f5cec7fbcf031dab3bcb56870
observer 3085749319a68c6865efc78da4fb9683808284776300a2d696eae38f37cfb694
input root 236b7ff7bf6d753f9d70fd97c98f530198035b92da6f47d477ee7ac484ebd628
payload a04f5a411feb1fc09183f9c315f0d6c89396d62b9c0892a097b4f5ab9d66c5b0
exported root e44eddb4efe8a04e0bd9bfd1d91aa67fd8a7997251e6c503842c369d598d8032
Rehashed unchanged kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Coverage: one activation, one client, three valid Foundation JSON
exchanges and graceful exits. This uses C libxpc data, not high-level
NSXPCConnection. Malformed inputs, concurrent clients and repeated
activation remain useful next grouped tests. UIKit, SpringBoard,
full iOS and MT6897 storage/driver work remain unproven.

Foundation milestone (2026-10-30, QEMU/RAM only; this commit):
An Objective-C program now executes selected APIs in the original Apple
iOS 16.5 Foundation/CoreFoundation and matching libobjc/Swift closure.
Baseline commit: 2409971aaf221e6a2984392b0836d9c9ced9e9b2.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-foundation, exit 0, 26/26 checks passed,
94 installed/original file byte checks passed, 315.692 host seconds,
23 sampled frames, zero unknown glyphs, no visible panic. Stopped on
second observer heartbeat before the 900-second limit.
Program PID 4, observer PID 3; root children of original launchd PID 1.
Ordered proof: NSAutoreleasePool creation; uppercase DUCHAMP; Arabic
UTF-8 round trip with five UTF-16 units; NSDictionary/NSNumber with
device and soc; JSON encode/decode; atomic NSData write/read; named
SweetProbe NSException throw/catch; pool drain; readiness; normal exit.
The saved 31-byte JSON independently decoded as device=DUCHAMP,soc=6897.
Both launchctl commands exited 0. Final print: not running, runs=1,
last exit code=0. PID 4 reaped; later heartbeats confirmed no restart.
The observer sent no signal or start command to the target.

Runtime preparation: tools/prepare-foundation-runtime.py.
Successful output: research/foundation-runtime-20F66-v2/runtime-root.
82 plain-arm64 binaries / 100,424,416 bytes, seven framework resources,
no missing strong dependencies. Source APFS hash and all file/resource
hashes recorded in its parent source.json. The first preparation output
was retained after rewriting identical read-only base files failed;
the preparer now skips matching existing bytes. Broad 7z extraction
rejected one unneeded libextension symlink; it was not reconstructed.
Replay can exclude it with -xr!libextension.dylib (list exclusion checked).

Replay tools/test-sweet-launchctl.sh with the prior six inputs, replacing
the runtime with the new one, then 900 and foundation. Objective-C uses manual reference counting
and exceptions; observer uses SWEET_FOUNDATION_TEST=1.
Builder copies/grows only the new RAM root from 32 to 128 MiB, verifies
its HFS header/length, creates only missing framework directories and
re-extracts every installed file. Target plist stays unchanged.
RAMDisk: 0x1c24d8000 + 0x08000000, inside the 512 MiB payload window.
Details/replay: duchamp/FOUNDATION-QEMU.md.
Report: work/launchctl-foundation/run/verification.json.
Raw logs, JSON and file extractions: work/launchctl-foundation/guest/.

SHA-256:
program eb121f6730f9bd198b1631bea0ebffaa349893379d3927c894ed88724ba7f1a6
observer 88424f24048eb5334b14c8beaa8e8b88ca74fb7985c3028f19068adf0b2890c8
input root ee2c72087cec9fe87500253c0c583ca7f55aa4d78d5e4cc097bc29bd3df5c040
payload 1ecf5feaf7f16ef85392c0abf9a9a29bb3c7c58e3e0c68a0799db7a86736b81e
exported root 096c443f4ab67987ad55f287b256cc88e662aa5c204db204c681bf798f84b271
Foundation 182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2
CoreFoundation 1bc84069d4292467b750c7aafb4c3114092cb9b5fa906d9c40e61504dc883878
Rehashed unchanged Actions 104 kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

All six controller modes and the Objective-C program pass arm64 checks
with warnings as errors; shell/Python checks pass. No kernel change or
new CI build. Earlier images/results and Apple sources remain local.
Coverage is selected Foundation APIs, not Foundation/XPC integration,
network services, UIKit, SpringBoard, full iOS or MT6897 UFS.

Native XPC milestone (2026-10-30, QEMU/RAM only; this commit):
One combined fixture now proves launchd MachServices registration,
on-demand server activation, native Apple libxpc dictionary request/reply,
and orderly exits. Original Apple launchd/xpcproxy/libxpc are unchanged;
observer CLI remains pinned Procursus FOSS launchctl 1:1.1.1.
Baseline commit: 8c6172eeb6b159bb0f64724bfece43f771d10dc8.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-xpc, exit 0, 43/43 checks passed,
449.402 host seconds, 35 sampled frames, zero unknown glyphs, no visible
panic. Stopped on second observer heartbeat before 720 seconds.
Observer PID 3, client PID 4, server PID 6; all root children of PID 1.
The initial server print had no PID, runs=0 and its registered Mach name.
Only after that print did the observer release the client's begin gate.
Native XPC traffic caused launchd to start PID 6 without a start command.
Both endpoints verified xpc_connection_get_pid and executable paths.
Three independent dictionary exchanges matched the expected payloads:
0x10203001 -> 0x4a7a6a5b, 0x10203002 -> 0x4a7a6a58,
0x10203003 -> 0x4a7a6a59. All eight integer fields are compared.
Client cancelled its connection and returned 0; server recorded native
XPC connection invalidation, handled SIGTERM, cancelled listener/peer
and returned 0. Final prints: not running, runs=1, last exit code=0.
Both PIDs reaped; Mach service registration remained in the final print.
All six CLI processes exited 0; final heartbeats confirmed stopped state.

Replay tools/test-sweet-launchctl.sh with prior six inputs, 720, then xpc.
Server plist: RunAtLoad=false, KeepAlive=false, MachServices containing
org.sweet.qemu.mach-service. Client/observer: RunAtLoad=true, no service.
Native programs use -fblocks; observer selects SWEET_XPC_TEST=1.
The same 39-file / 10,551,232-byte runtime suffices; no new kernel CI.
Public libxpc prototypes/ownership/queue rules checked in Apple docs;
listener flag bit 0 also checked in the pinned libxpc disassembly.
Sync replies occur on client main, outside its event-handler queue.
The API has no per-request timeout here; whole-VM limit bounds the run.
Details/replay: duchamp/XPC-QEMU.md.
Report: work/launchctl-xpc/run/verification.json.
Raw peer logs, CLI files and listings: work/launchctl-xpc/guest/.

SHA-256:
server bfb60c484b8878d658cad3182256d0b768e5273240dd7dfd4fd11b379a1c936a
client e321ce84071a0c6c5d01188fca0782c5435d811e753cf65506cf55543a6bec55
observer 0ac3063243d8d2a62928e12d31ebcdff3dfa8d5de53f798827afc431f3a45170
input root 7dba76a3799e87d7b8443f23d6eaf391ab23cb51c31246aa24641f219077dbe3
payload 28c415f14ee8ab3c2ab7927e95cdd3197fe63f465418dd3c29d96ac9b9d465cb
exported root a90255ffc4b32bfa2fbbc6dc7798c949145537610223b0d6026356ded7aa7af1
server plist e32f6c8940f7005aa3347ec2f2663dbf5c4a86c9405d4b9c7be6dad7f8f81275
Rehashed unchanged Actions 104 kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Five controller modes and both XPC programs passed arm64 -Wall -Wextra
-Werror checks; shell/Python checks passed. Old Unix guest recheck passed
39 checks with the split launch-policy validation. Its original 38-check
report was saved/restored; verification-xpc-tools-recheck.json records
the recheck. Prior images and results remain intact.

Coverage is one native XPC connection, three replies and one on-demand
activation. Repeated activation, concurrent clients, Foundation/system
services, full iOS and MT6897 UFS remain unproven and separate work.

Two-service IPC milestone (2026-10-30, QEMU/RAM only; this commit):
A separate Unix-domain socket server and client now exchange validated
messages as root children of unchanged Apple launchd PID 1. A third
observer uses pinned Procursus FOSS launchctl 1:1.1.1 for state/stop checks.
Baseline commit: de31099d57f8b4dfa162ada21049fbbeec504206.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-ipc, exit 0, 38/38 checks passed,
428.675 host seconds, 33 sampled frames, zero unknown glyphs, no visible
panic. Stopped on SWEET launchctl: heartbeat=2 before 720-second limit.
Observer PID 3, server PID 4, client PID 5; all root children of PID 1.
Both socket endpoints verified LOCAL_PEERPID and the peer executable path.
Three 32-byte request/reply frames carried matching PIDs, sequence,
version, payload and XOR checksum. Both independent saved logs matched:
seq 1: 0x10203001 -> 0x4a7a6a5b
seq 2: 0x10203002 -> 0x4a7a6a58
seq 3: 0x10203003 -> 0x4a7a6a59
The client closed its socket; the server observed EOF.
The observer released the client via a RAM file; its main returned 0.
It sent SIGTERM to the idle server; the handler only set a flag, then
normal execution closed the listener, unlinked the socket and returned 0.
Both PIDs were reaped. Final launchctl prints: not running, runs=1,
last exit code=0. No signal death. Socket absent from saved RAM root.
All five CLI children exited 0; later observer heartbeats confirmed
both services stayed stopped. No kickstart/bootstrap/direct service exec.

Replay tools/test-sweet-launchctl.sh with the prior six inputs, 720,
then ipc. It builds sweet-ipc-server.c at the existing C-service path,
adds sweet-ipc-client and its job, and selects SWEET_IPC_TEST=1 for the
observer. All three jobs RunAtLoad=true / KeepAlive=false. The server
job's plist stays byte-identical to the base. Fixture executables are
new in this scenario; prior scenarios retain their original C target.
ABI declarations checked against local XNU 22.6 CI source headers and
uipc_usrreq.c. This is AF_UNIX SOCK_STREAM, not an XPC/Mach service test.
Details/replay: duchamp/IPC-QEMU.md.
Report: work/launchctl-ipc/run/verification.json.
Raw peer logs, CLI stdout/stderr and listings: work/launchctl-ipc/guest/.

SHA-256:
server f89ef4d320f554bf13f5e284efb6f4ba4d61235c6d6cf5140fe91edc04f88972
client fc9b79e2d48729ff45b6abe6909325b69a499e7660aabe821af5d1e605cf866f
observer 2bc3845ccdfa148c36411c271046816ded93a732c1ae3b0844308dae41fc30f2
input root aa4e450a621daa745ed915bc97fe3ce3dd605b7e25e5f4fa2bf9d3bbec8c53f0
payload 55a093b2d3b86c5850bdad77a1d28d8eb0e024d326687d6ce409d7b493a034bf
exported root 47800e98c2f14a64e2c8b5ee7a28164b370d5fc1afc4cb8575458e10237de9f7
Original Apple launchd/xpcproxy and pinned CLI hashes passed.
Rehashed unchanged Actions 104 kernel and initial base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base root 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f
No new kernel CI build. Server/client and all four controller modes
passed arm64 C checks with warnings as errors; shell/Python checks pass.
The prior saved KeepAlive run still passes its 33 checks.

Coverage: one connection and three request/reply pairs; normal client
exit; SIGTERM cleanup of an idle server after peer EOF. Active-request
cancellation, concurrent clients and XPC remain separate coverage.
Full iOS and MT6897 UFS are not proven. Preserve all prior roots/results.

KeepAlive milestone (2026-10-30, QEMU/RAM only; this commit):
Unchanged Apple launchd/xpcproxy automatically restarted the diagnostic
C service twice with KeepAlive=true, using pinned Procursus FOSS
launchctl 1:1.1.1 only to print and send SIGTERM / SIGKILL.
Baseline commit: 9653af572059e49531a7eb43638aa2e02c5daef2.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-keepalive, exit 0, 33/33 checks passed,
450.716 host seconds, 35 sampled frames, zero unknown glyphs, no visible
panic. Stopped on SWEET launchctl: heartbeat=2 before the 720-second limit.
Controller PID 3 is a root child of original PID 1 /sbin/launchd.
All five CLI processes exited 0:
print-before: PID 4 running, runs=1.
kill SIGTERM: PID 4 reaped / ESRCH; launchd respawned PID 7 automatically.
print-auto-1: PID 7 running, runs=2, last terminating signal=15.
kill SIGKILL: PID 7 reaped / ESRCH; launchd respawned PID 10 automatically.
print-after: PID 10 running, runs=3, last terminating signal=9.
No kickstart/bootstrap/direct exec of the target was used by the controller.
All three target instances passed readiness checks; PID 10 and controller
continued heartbeats. The saved readiness file contained 10.

Replay tools/test-sweet-launchctl.sh with the prior six inputs, 720, and
keepalive as eighth argument. Only controller gets SWEET_KEEPALIVE_TEST=1.
The copied target plist changes only KeepAlive false -> true; base stays
unchanged and controller KeepAlive stays false. The target C binary is
byte-identical to the prior tests. Builder records base/installed plist
hashes and base properties. Verifier checks three distinct PIDs, ordered
autorestarts, run count 1/2/3, signals, raw CLI files and final heartbeats.
Details/replay: duchamp/KEEPALIVE-QEMU.md.
Report: work/launchctl-keepalive/run/verification.json.
Raw trace and CLI outputs: work/launchctl-keepalive/guest/.

SHA-256:
target 465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f
controller ca5fcabfe9da5ab23768841986ab9e0eada43674c2a32524ef0b7fc05cf30bb8
input root 9ef39b5556b5d4416a89aa58e21eafd0bd0038c9f468359ba61cb6a33720a03f
payload d7b6d4d88ee53ec67473bf21ebea8e2fdde545b172b5a7665e3ce16aabfbaba6
exported root 85b2e3958900f668387963f0fea647bc1a20f88aa83b58f30aec72a0d104de30
KeepAlive plist 7e33d9a92afeca768a5aacd4fb95ff171355444bee1c24099a6dfa136cc8f808
base plist 004e41dbd0bc0d0f1ef88a7ee73c6ae228c55a5e7d8728704289dc244380083c
Rehashed unchanged Actions 104 kernel and initial base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base root 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f
No new kernel CI build. Original launchd/xpcproxy/CLI hashes passed.
Three C controller modes passed arm64 -Wall -Wextra -Werror checks;
shell syntax and Python compile checks passed. Updated verifier still
accepts prior saved guests: 22 stop/restart and 27 bootout/bootstrap checks.

This tests unconditional KeepAlive after signal termination in QEMU.
Normal exit, conditional KeepAlive dictionaries and custom shutdown
handlers remain separate coverage. Full iOS and MT6897 UFS are not proven.
Keep all successful roots and prior failed probes for comparison.

bootout/bootstrap milestone (2026-10-30, QEMU/RAM only; this commit):
The pinned Procursus FOSS launchctl 1:1.1.1 successfully removed and
reloaded org.sweet.qemu.c-service under unchanged Apple launchd/xpcproxy.
Prior lifecycle commit: 5343d416b2d83ad71f37357d7321065172aa62d8.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-bootstrap, exit 0, 27/27 checks passed,
399.932 host seconds, 31 sampled frames, zero unknown glyphs, no visible
panic. Stop marker: SWEET launchctl: heartbeat=2 .
Controller PID 3 is a root child of PID 1 /sbin/launchd.
print-before: exit 0, target PID 4 running.
bootout system/org.sweet.qemu.c-service: exit 0, PID 4 reaped / ESRCH.
After five seconds, print returned ENOSERVICE=113 (wait status 0x7100):
Could not find service "org.sweet.qemu.c-service" in domain for system
The plist remained readable and byte-identical to the base image.
bootstrap system /System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist:
exit 0; readiness file became 9; print-after: exit 0, PID 9 running.
Both target and controller continued heartbeats. This proves removal of
registration and reloading, beyond the earlier stopped-but-registered test.

Replay tools/test-sweet-launchctl.sh with the same six inputs, 720, then
bootout-bootstrap as its eighth argument. Omitting the mode retains the
SIGTERM/kickstart scenario. Only the controller gets SWEET_BOOTSTRAP_TEST=1.
Verifier requires the exact missing-service status/text and checks the
saved guest plist, original executables, PID transition and heartbeats.
Details and replay: duchamp/BOOTSTRAP-QEMU.md.
Raw trace/CLI files: work/launchctl-bootstrap/guest/.
Report: work/launchctl-bootstrap/run/verification.json.

SHA-256:
target 465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f
controller ef31d135fdf0120e930b77f7c34724a5cb44589ce8bed7b75d8194ee2f3c0bd8
input root 949814247b6e88a4d466518d0dc88bdce01cd13066e9fb7120590afc87585b58
payload fe12ca6fd72cf90be45a82a9f807bc4147c46115e9a996ccaa761b9bb575d38b
exported root d2bbb6a6910f100fac9bff93a7c1f646f27fe0c63451ba8fa3d2a8cd951b51e4
target plist 004e41dbd0bc0d0f1ef88a7ee73c6ae228c55a5e7d8728704289dc244380083c
The unchanged Actions 104 kernel and initial base root were rehashed:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f
No new kernel CI build. Both controller modes pass arm64 C checks with
-Wall -Wextra -Werror; Python compile and shell syntax checks pass.
The updated verifier accepts the prior lifecycle run (22 checks) and
rejects the earlier SIGTERM-ignored run despite its no-panic result.

This milestone covers one diagnostic service in QEMU's development
kernel. It does not establish full iOS or a working MT6897 storage backend.
Keep the existing successful roots and failed probes. Further work should
select a separately scoped userland test; phone storage remains outside it.

launchctl lifecycle milestone (2026-10-30, QEMU/RAM only; this commit):
Apple's unchanged launchd/xpcproxy now successfully serve print, SIGTERM
stop, stopped-state print, kickstart -p, and running-state print through
pinned Procursus FOSS launchctl 1:1.1.1. This is not an Apple-supplied
launchctl binary. Restore/update/system image file lists contained none.
The CLI SHA-256 is
11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d;
libiosexec.1.dylib is
9d8f0b10be02f9829854e11dc4a86f70dbfd0f0322f3a3a996716e4d38214391.
prepare-launchctl-runtime.py pins official package URLs/SHA-256 values and
copies the existing restore runtime. LC_RPATH resolution was added to the
dependency audit; the closure is 39 files / 10,551,232 bytes. No global
package installation, Apple binary patch, or kernel modification was used.

Final complete wrapper run: work/launchctl-signals, exit 0, 22/22 checks
passed, 412.973 host seconds, 32 sampled frames, zero unknown glyphs, and
no visible panic. The 720-second maximum was cut short by the second
controller heartbeat after CONTROL PASS. The root/System controller PID 3
is a child of original /sbin/launchd PID 1. Target PID 4 was running,
terminated by SIGTERM, reaped (ESRCH), and remained absent during the
stopped check after at least five seconds. kickstart printed 9; the new
target published PID 9 and print-after showed it running. All five CLIs
exited 0. Both target and controller continued heartbeats.

The target now publishes a PID readiness file after its identity/file checks
and explicitly sets/read-backs SIGTERM=SIG_DFL with an empty mask. Both
instances logged inherited SIGTERM=ignored, mask=0. Before that fix the
CLI request succeeded and launchd logged signal 0xf, but the target kept
running; work/launchctl-final correctly failed after 60 reap polls.
The first probe (work/launchctl-probe-1) failed from O_WRONLY capture
readback / EBADF; O_RDWR fixed the controller. That failed VM was stopped
early with its RAM root exported. All attempts and raw outputs are kept.
The strict verifier rejects the earlier no-panic / successful-CLI failure.
This tests default SIGTERM termination, not custom signal-handler cleanup.

--save-ramdisk validates the ADT RAMDisk physical range and exports it after
stopping the VM. The verifier extracts all five actual stdout/stderr files,
the controller trace, readiness PID, and original executable bytes from the
saved HFS image. It checks ordered CLI statuses, old/new process state,
signal normalization, both target instances and continuing heartbeats.
Evidence: work/launchctl-signals/guest/ and run/verification.json.

Final target SHA-256
465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f;
controller 2425fbdf5d19ce32eaf90bf6b3bc967afec5bcd57aa7fed011e8c508958b3001;
input root 6304a5a91fd1b6cf223912f710139df443d2de3bb1fc5934ad926a301d419e3d;
payload e4ac257dacec131822e5d864dc232046028f52ba0b25f73d6075d573c916def6;
exported root 072372b543a717b9c06ca0e4bdee7ed634a9a87f43efa53be92e6e64bba08071.
Actions 104 / 40939563499 kernel is unchanged:
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.
The previous launchd input root remains
491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f.
The full public system DMG was also fetched during asset investigation:
research/launchctl-20F66/096-04088-077.dmg, ZIP CRC32 028fc181 verified.
It is not needed to replay this test. Apple/third-party files stay ignored.
No helper/QEMU download processes remained after completion.

Next QEMU step: bootstrap/bootout of the target job and verify removal and
re-registration. Full iOS, SpringBoard, production signing, and MT6897 UFS/
hardware remain unfinished. Phone/USB/boot partitions were not accessed.
Previous commit: b52fd2a. Reproduction: duchamp/LAUNCHCTL-QEMU.md.

Original launchd milestone (2026-10-30, QEMU/RAM only; this commit):
Original, unmodified iOS 16.5 restore launchd now runs as PID 1 and launches
one persistent dynamically linked C system service via original xpcproxy.
The static /usr/appleinternal/sbin/launchd.sweet entry is selected with the
existing DEVELOPMENT launchdsuffix=sweet path, checks PID 1, opens console
fds and execs /sbin/launchd without forking or starting the service itself.
The C service reports PID 3, PPID 1, real/effective UID 0, and verifies that
proc_pidpath(1) is /sbin/launchd. Its RAM-file roundtrip and continuing
numbered heartbeats passed. Only one process identity was observed.
Job: org.sweet.qemu.c-service, UserName=root, GroupName=wheel,
LimitLoadToSessionType=System, RunAtLoad=true, KeepAlive=false.

Final unchanged wrapper run in work/launchd-final completed for 180 host
seconds with exit 0, all 15 checks true, 14 sampled frames, zero unknown
glyphs, and no visible panic. run/verification.json records hashes/checks;
run/frames and run/fb.txt contain sampled circular framebuffer logs.
Original launchd SHA-256
4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06;
xpcproxy 2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f.
Bootstrap fca4093be866f706e4a693f7f79bcfd2239ea144ccdb14dd2bbeb215719f441f;
C service 6adbe9d1fb35a1833b273507aeb2b0e9c75450d73274a3410937aa0c495d24de;
root 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f;
payload 42f784c42bbf31745502f5e11b2727f8cc2b4365f3b42c2cbaf004c7ffa781a8.
Kernel unchanged from Actions 104 / 40939563499, SHA-256
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.

Probe 1 reached Apple launchd but panicked because the root-only fixture
could not resolve mobile (errno 114). The builder now preserves the restore
image's account IDs/groups and locks password fields. Probe 2 panicked in
the interrupt-duration watchdog while a separate observer dumped live RAM.
The new optional QEMU snapshots stop virtual time before pmemsave and
resume afterward; the runner also reaps the VM on capture/decoding errors.
Probe 3 then passed 12 earlier checks and ran the service in user/501.
launchd rejected DYLD_SHARED_REGION in that job. The final job removes that
variable and explicitly selects a root/System service. The strict verifier
also rejects the failed first probe. No watchdog or kernel check was disabled.

prepare-darwin-runtime.py now extracts launchd/xpcproxy and account inputs
alongside the 37-file runtime closure; tested using the pinned restore disk
into research/darwin-launchd-20F66. All Apple inputs stay ignored/local.
Each installed regular file is re-extracted and byte-compared; the HFS job
directory is checked for exactly one job. The original dynamic RAM-root
SHA-256 stays 750fc8ec3e2452a708da00aa078a8f6b65d7f27333c18cba17add0899ea67c91.
launchd retains embedded __TEXT,__config; no binary or global config patch.
Nonfatal logs include missing MRM cache, jetsam EINVAL and persona lookup
failures. This proves one service, not complete launchd/iOS compatibility.
Next concrete QEMU work: original launchctl status and controlled service
stop/restart. GUI, hardware drivers and MT6897 UFS remain unfinished.
Phone/USB/UFS/boot partitions were not accessed. Previous commit: 3a9bc41.
Reproduction: duchamp/LAUNCHD-QEMU.md.

Dynamic C runtime milestone (2026-10-29, QEMU/RAM only; this commit):
Fetched only Apple's 20F66 iPhone X restore disk 096-03566-084.dmg using
remotezip; pinned SHA-256
8223b75c9399dfc8cf0971374527d710b69e29e8ef69722b98a82902199fcff5.
It is an unencrypted IM4P/APFS container, not a decrypted system image.
prepare-darwin-runtime.py was also tested against the local pinned member.
Its real plain-arm64 dyld/libSystem dependency closure has 37 files,
10,401,536 bytes, all kept locally under ignored research/.

A separate C executable links to /usr/lib/dyld and libSystem with LC_MAIN
and explicit ld64.lld -adhoc_codesign. It uses real printf, dyld image
enumeration, file create/write/close/reopen/read/EOF, libc fork, and waitpid.
A static diagnostic PID 1 forks/execs it, requires exit 0, then heartbeats.
The 32 MiB HFS root is a fresh baseline copy; all 39 installed files were
extracted and byte-compared using libdmg-hfsplus at pinned commit
7ac55ec64c96f7800d9818ce64c79670e7f02b67. The baseline SHA-256 remains
e5b5c1b68c00db65ae31d8d29baef6ab88c8131e29940d8ce7b810536726414a.

Final complete wrapper run: work/userland-dynamic-final, 90 seconds, exit 0,
all 15 semantic/metadata checks passed. C main reported PID 2 and 37 images;
child PID 3 exited 42, parent verified waitpid, C exited 0, PID 1 continued.
Zero unknown glyphs and no visible panic. An initial 45-second probe had not
reached C main. The first 90-second binary ran successfully but had no
LC_CODE_SIGNATURE; the validator rejected it. Explicit -adhoc_codesign
fixed that build issue and the final untouched wrapper passed. Signature
command presence/execution under a development policy does not prove
production trust or entitlement enforcement.

Kernel unchanged from Actions 104 / 40939563499, SHA-256
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.
Final init 2c2892d85895afefc8bd62ef620ac7081f81cdc6bbeb22935fdd4759dfd6d663;
C program 8a8427fc901b7d4041079e80e6965253ddb15a031918fcd04d2b5476f6a8953f;
root 750fc8ec3e2452a708da00aa078a8f6b65d7f27333c18cba17add0899ea67c91;
payload 422bd7cb12fd82d502cde09070d06822b417ec4f9e9137d23ed0665d7ddd0e05.
Reports: work/userland-dynamic-final/run/{fb.txt,verification.json}.
Reproduction and launchd inspection: duchamp/DYNAMIC-USERLAND.md.

Original restore launchd and xpcproxy were extracted for metadata/import
inspection only. Both are arm64/iOS and directly require libSystem/libobjc,
already in the tested closure. xpcproxy has a weak cryptex trampoline import.
Their private spawn, Mach/dispatch, host ports, sandbox/csops behavior is not
verified. The five supplied daemon plists include iPhone restore services.
Next: isolated QEMU root with actual launchd as PID 1, xpcproxy, writable
private/var directories, console/null nodes, and one controlled C service;
trace errors before adding more jobs. No original launchd was executed yet.
Full iOS and MT6897 hardware support remain unfinished. Phone/UFS/boot
partitions were not accessed. Previous milestone commit: 053964a.
The runner's long-path QMP socket fix is included: transient socket in /tmp,
removed on completion. Other pending checkpoint/loader changes stay separate.

Signal/service-control milestone (2026-10-29, QEMU/RAM only; this commit):
After the intentional exit-42/restart, PID 1 sends SIGSTOP (17) to the positive
worker PID and polls wait4(WNOHANG|WUNTRACED) for status 0000117f. It holds the
worker stopped for at least five seconds, sends SIGCONT (19), requires
WCONTINUED status 0000137f, and allows ten seconds for renewed heartbeat output.
It then sends SIGTERM (15), requires termination status 0000000f, reaps the
worker, checks kill(pid, 0) returns ESRCH, and starts a third persistent worker.
Each wait event has at most 50 polls with 100ms pauses. Worker SIGTERM is
explicitly SIG_DFL with an empty signal mask; select retries EINTR. This tests
default actions, not a custom signal handler or graceful cleanup routine.

The complete 90-second wrapper run in work/userland-signals-verified exited 0.
All 27 semantic checks passed, including ordered signal events, no worker
heartbeat during the stopped interval, fresh heartbeat after continuation,
termination/reaping, final restart, and all three workers' file/IPC tests.
No visible panic and zero unknown glyphs were observed. The earlier run in
work/userland-signals-final also passed guest checks but its host wrapper
reported a trailing syntax error after its comment was edited mid-execution;
the untouched rerun passed end to end. The verifier rejected an IPC-only
result copied to work/userland-signals-negative. Previous milestone: ef86078.

Kernel unchanged from Actions 104 / 40939563499, SHA-256
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.
Final init 10256d2be047a950c2b920670e69806814089b37ae6ef19ce8c44a2e65df2c1c;
worker 595827b44de924f7316a2befbe6ef641ac897b7a0cd25e14bd68f5fd52dbdcb1;
root ccc0ecc271447f104854eabaea6b5cbdaf9c56e9a5706d93a9282f5bb20c17c1;
payload 19dd823926c2fe1971bcd3dfbeff1c8a3510742d0be60f103d8c96c9bf083df9.
The repeated build produced identical input hashes. Artifacts and report:
work/userland-signals-verified/run/{fb.txt,verification.json}. Documentation:
duchamp/USERLAND-QEMU.md. Phone/UFS/boot partitions were not accessed.
Richer userspace and the MT6897 hardware backend remain unfinished.

IPC and RAM-file milestone (2026-10-29, QEMU only; this commit):
PID 1 now creates a fresh pipe before each fork, closes its writer, and checks
the exec'd worker's exact READYv1 message followed by EOF. The child uses dup2
to inherit the writer on fd 3 and closes unused endpoints. On each exec the
worker creates /sbin/worker-data, writes 18 known bytes, closes and reopens it,
compares every byte, checks EOF, then sends its pipe message and closes fd 3.
Both transfer loops handle short reads/writes and reject premature EOF.

The existing kernel from Actions 104 / 40939563499 was reused. The single
test-sweet-userland.sh run in work/userland-ipc-final completed for 90 seconds
with no_panic_observed, zero unknown glyphs, and all 17 semantic checks true.
The intentional exit 42, wait4 status 00002a00, restart, and continued
heartbeats still passed. Both workers completed the RAM-file and IPC checks.
The updated verifier rejected a copied exec-only result in
work/userland-ipc-negative, proving that old milestones alone do not pass.

Final hashes: init
b519aa9d6c849949ca73c70e99b6ef56dfe5111ca5aa270771fd3f679ad0138d;
worker a5a310483d999a5038da85b08184f2ec3c80ec3b3546d02dae27b5dc439f5abd;
root b1e19227f8f004c41b44a470f79d7750827df376d9f0c30c1c2363d6df067363;
payload 42a402a2c38e030c7d207e83b9f43d08901d0b6630ed7a4c5e7724f509dc6e9b.
See run/verification.json and run/fb.txt under that directory. Previous
exec-only milestone: 039b4a1. No new kernel build or phone access was needed.
Remaining work includes signals/service control, richer userland, and the
separate MT6897 hardware backend. These are RAM-root observations in QEMU.

Diagnostic exec/supervision milestone (2026-10-29, QEMU/RAM only; this
commit): tools/build-sweet-userland.sh builds separate signed arm64 init and
worker executables. PID 1 creates /sbin/worker on the writable RAM HFS root,
forks and execs it with argv once, then uses wait4(WNOHANG) to reap its deliberate
exit 42 (raw status 00002a00). It requires that status before restarting the
worker with argv stay; unexpected exits stop with TEST FAILED. Worker entry
also checks argc and a PID greater than 1. No kernel change was required:
Actions run 104 / 40939563499 at 4ada6fda3a7b6bd6b3c880698b35c0bc30ebbf8e
provided the reused kernel. Final 90-second QEMU run completed with
no_panic_observed and zero unknown glyphs; every semantic check passed,
including two exec entries, wait status, restart, and continued parent/worker
heartbeats. The verifier correctly rejected the earlier failed compact-worker
run despite its no_panic_observed snapshot.

Artifacts: work/userland-exec-final/{launchd,sweet-worker.macho,root.hfs,
payload.bin,run/fb.txt,run/verification.json}. Reproduce with the single command
documented in duchamp/USERLAND-QEMU.md. Kernel SHA-256:
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9;
init cba363ff31a227b0ca4aa410196148f0abcb7146a0a885455e993625a931da73;
worker 2918b89ab249a0f54f2e63a89355e746669dcd3cb6f6b315581838391bd8a64a;
root 0a19b8c12959f48d292bedd8a018a461de832dd043cd9932747677f8766ac34f;
payload 30bfd3b0b46aabb1b673cff58165ba5fa0b84281260d25d07d154c399e54ecde.

Failed experiments retained: the compact worker used an invalid 4K file offset
for this 16K arm64 loader; it has been replaced with the standard Mach-O layout.
An earlier unsuccessful writable hpmount attempt altered work/root-multiproc.hfs;
do not reuse it. All final images use the unchanged original HFS baseline
work/qemu-rootvnode-98/root-with-launchd.hfs (e5b5c1b6...36726414a).
Phone, UFS, and boot partitions were not accessed. Next work can add IPC and
file-service tests in QEMU; a dynamic userland and MT6897 storage remain
separate unfinished work. This milestone is a diagnostic userspace, not iOS.

Grouped pre-BSD checkpoint (2026-10-28, offline/QEMU only): commit
`da2da9b` executes the commpage, security/code-signing, trust/startup-lockdown,
kernel-lockdown, and final platform groups, then stops at stage 154 immediately
before `bsd_init()`. GitHub Actions run `40614756535` succeeded. Payload-source
reconstruction passed. QEMU displayed every grouped stage 145 through 154,
including entry and return markers for each completed group and `DUCHAMP PRE
BSD INIT`; no panic, abort, assertion, fault, guest error, or invalid-value
report was found. The framebuffer decoder reported nine unknown glyphs, but
all required markers decoded exactly. No phone image was created or flashed.

SHA-256: kernel
`027749bee9f33323faefed98d182c46d7aa3c25fba812b3584c62f3c6cc15125`;
payload
`460fba13999b83f0d2dedd709b652a8e6cd0374e285ff75b481e382142ddbcc8`.

Post-initialize_screen / pre-vm_commpage checkpoint (2026-10-28,
offline/QEMU only): commit `f5b1463` releases the stage-141 stop, marks entry
and return from `initialize_screen(NULL, kPEAcquireScreen)`, and stops at
stage 144 immediately before `vm_commpage_init()`. GitHub Actions run
`40613078727` succeeded. The rebuilt payload matched its kernel source. QEMU
displayed stages 142 (`initialize_screen` entering), 143 (returned), and 144
(pre VM commpage), with no panic, abort, assertion, fault, guest error, or
invalid-value report. The framebuffer snapshot contains all three markers;
the text decoder reported nine unknown glyphs but this did not hide or alter
the required markers. No phone image was created or flashed.

SHA-256: kernel
`bf3f20f3f3b9e740fbae61dda3472e3fbff7941d4f57ebf9cd207cc0c935ccf0`;
payload
`cd1c29ee4a02dcd9160070482611db91166826dab66678d9dec9d13fa32829e3`.

Post-spllo / pre-initialize_screen checkpoint (2026-10-28, offline/QEMU
only): commit `b6f0b6b` validates the enabled virtual timer and permits only
spurious, virtual-timer, or IPI pending INTIDs before enabling interrupts.
GitHub Actions run `40610510362` succeeded at
`b6f0b6bc2254d7d9dc71329c05cd179056a978ee`. The rebuilt payload matched its
kernel source. Direct QEMU displayed stages 138 (interrupt state validated),
139 (`spllo()` returned), 140 (interrupts enabled verified), and 141
(immediately before `initialize_screen()`). No panic, abort, assertion, fault,
guest error, or invalid-value report was found. QEMU logged normal handled IRQ
entry/return activity after interrupts were enabled. Embedded-payload byte
comparison passed, and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=357776`). No phone image was created or flashed.

SHA-256: artifact ZIP
`6a20627a716cd0b06e2a1293f0bb8ee8c08d117a1aa14b0ab495f9d22ce886d8`;
kernel
`f9e1baa55e0f87d9b593d85d93f344a9c0cec4c9cedaad0443f43170adbcc6b4`;
ADT `12a3b24830bc96163188bbadf8f709afc2d5a48449f491f859900eb00fb4e55e`;
payload
`d6b5da48a23cf6e3df4809b60f552d9e912c79cd03100eb2788a685a4797b8af`;
bootshim Image
`60e523359dbcba2a23f7dd0233d8c98ce6526247eca9746c31e7451e59a5ce21`.

Pre-spllo early-boot checkpoint (2026-10-28, offline/QEMU only): commit
`2368b05` releases the stage-134 stop, adds grouped stages around
`kernel_startup_initialize_upto(STARTUP_SUB_EARLY_BOOT)`, and stops at stage
137 immediately before `spllo()` enables interrupts. Source inspection found
EARLY_BOOT registrations for the SWEET PRNG, process and ulock tables, pthread
and AMFI providers, kmem crypto state, VM reclamation/pageout support,
personas, telemetry, iotrace, PGZ, optional KCOV, and watchdog scratch
subscription. In the tested ADT `/options` is absent, the watchdog node lacks
`awl-scratch-supported`, and iotrace is disabled by default, so this path adds
no direct hardware MMIO. GitHub Actions run `40608017331` succeeded. Direct
QEMU displayed stage 135 entering the callbacks, stage 136 after all callbacks
returned, and stage 137 before `spllo()`; no panic, exception, abort,
assertion, fault, guest error, or invalid-value report was found. Payload
reconstruction, embedded-payload byte comparison, and the captured-phone-FDT
8 GiB bootshim test passed (`white_pixels=355676`). Interrupts were not
enabled, and no phone image was created or flashed.

SHA-256: artifact ZIP
`940c166389b08dbecb46870934c2f2c4e0fede265da5b74dceeb2a521a54ee90`;
kernel `cb99cb7a297c1837ae4046b181bfbda6d21a711ee72075f03cbe181ae479e1d1`;
ADT `f05f2e7ff1a6b2bbb7ab23554fbc6d5c5c64f1930ba1d07fe82e794064132c65`;
payload `3e9c7b30fb3a9f7ce469a8699e3f91aca0e4ec72277dccdadcdf57ef02ce480f`;
bootshim Image
`ec535f80df9a608fd8c8f471c4e8afd98409656923c0c974c6559be6d830aa44`.

PE-init-I/O-Kit return checkpoint (2026-10-28, offline/QEMU only): commit
`ac1e605` releases the stage-132 stop inside ARM `PE_init_iokit()` and moves
the diagnostic barrier into `kernel_bootstrap_thread()` immediately after
`PE_init_iokit()` returns. Stages 133 and 134 prove control returned to the
main bootstrap thread and stop before the interrupt-state assertion and before
`kernel_startup_initialize_upto(STARTUP_SUB_EARLY_BOOT)`. GitHub Actions run
`40606665314` succeeded. Direct QEMU displayed both stages with no panic,
exception, abort, assertion, fault, guest error, or invalid-value report.
Payload reconstruction, embedded-payload byte comparison, and the
captured-phone-FDT 8 GiB bootshim test passed (`white_pixels=353976`). No phone
image was created or flashed.

SHA-256: artifact ZIP
`313c453663924e792f492b3689f5761be2201d3c5c01bd13d0649f4a5ef68793`;
kernel `6fb6e899b72a03b2e1ad96d2beb7811dab877e08ab5d0822c40512cec06b359f`;
ADT `6ff7c79cbc86940a9b1b74774ce58b3d905fc882bbf0ed2102b8b83518b7ad0a`;
payload `69c4b7a352b63c40d78d45a727dbc47f406a5fbc3296c7984b1d97424a9ec3d5`;
bootshim Image
`cb001eb003f8f791c39a398ff610b7ebad1159391edbd12fd7ff4869ad439d33`.

Post-ConfigureIOKit checkpoint (2026-10-28, offline/QEMU only): commit
`0f327e5` releases the stage-129 stop and brackets `ConfigureIOKit()` with
stages 130--132. Parsing the exact QEMU ADT used for this test proved its root
children are `chosen`, `defaults`, `cpus`, `arm-io`, `sweet-fbcon`, and
`buttons`; `/options` is absent. Consequently `createNVRAM()` returns before
allocating or starting `IODTNVRAM`. General driver matching remains later in
`PE_lockdown_iokit()` and was not reached. GitHub Actions run `40605065946`
succeeded. Direct QEMU displayed `ConfigureIOKit entering`,
`ConfigureIOKit returned`, and `DUCHAMP POST CONFIGURE IOKIT`; no panic,
exception, abort, assertion, fault, guest error, or invalid-value report was
found. Payload reconstruction, embedded-payload byte comparison, and the
captured-phone-FDT 8 GiB bootshim test passed (`white_pixels=352880`). No phone
image was created or flashed.

SHA-256: artifact ZIP
`67a45b48ae04854c4cd8c105d0838d0707fafe5a311411a1faf03dd1cd96c6bb`;
kernel `a5502895037037f460d033523c04a31079e5e4e6fb910372be9fde67833ea454`;
ADT `9f1a120587d91d12cfcff92c4b6ec80c52bebcbfbd46b670bcde6445f6e7c76c`;
payload `e882f9ec98a1f30f63367a1d253c9d5f25b86ac36ab22f05c39e3257b5dc7f8f`;
bootshim Image
`50b33b54d5dc43329ec2383d1c4129299a9f0bdc5f1106ef5e3410f0aff0d128`.

Pre-ConfigureIOKit checkpoint (2026-10-28, offline/QEMU only): commit
`4b8f48b` releases the stage-123 stop and adds grouped markers inside the ARM
`PE_init_iokit()` path. Source inspection established that `PE_init_iokit()`
prepares console/progress state, imports selected Device Tree data, calls
`InitIOKit()` to initialize the IOKit runtime and attach the root nub, and then
calls `ConfigureIOKit()`. The latter can invoke `IODTNVRAM::start()` when an
`/options` node exists; general driver matching starts later through
`PE_lockdown_iokit()`/`StartIOKitMatching()`. The new stage-129 barrier is
therefore immediately before `ConfigureIOKit()`, before the first possible
driver `start()` in this path. GitHub Actions run `40603689394` succeeded.
Direct QEMU displayed stages 124 through 129, including `InitIOKit returned`,
with no panic, exception, abort, assertion, fault, guest error, or invalid-value
report. Payload reconstruction, embedded-payload byte comparison, and the
captured-phone-FDT 8 GiB bootshim test passed (`white_pixels=351312`). No phone
image was created or flashed.

SHA-256: artifact ZIP
`0cdad46936d331da5ed5b8d464eb4cc6af71098d66b9c4533a7d996e9e725edd`;
kernel `b5b2b7d470ce693d8a5dd29c0dcbcaa3364c70d7385c39477f5fd8dd106905ce`;
ADT `7a1a44abaf129a10647bfbf4828df9341b78960a3670a5331161d37725014cdf`;
payload `55d5dcdd1ee36934def2a4a7d79cf477c8f7f2eae16735e20ca1b89a3d9a560b`;
bootshim Image
`a9634d06eea1e02cf9051b70edb6d041f63b3bc9a5094b2330cefb2c79098b7d`.

Address-permutation checkpoint (2026-10-28, offline/QEMU only): commits
`8bb26be` and `8c337e7` release the stage-119 stop, execute the five
`early_random()` calls, validate that all five resulting values are non-zero
and that the three address permutations are odd, and stop at stage 123 before
`PE_init_iokit()`. The first CI artifact exposed that the old stage-119 WFE
barrier was still present; that result was rejected, the barrier was removed,
and GitHub Actions run `40601741780` then succeeded. The corrected kernel
contains the stage-120--123 strings. Direct QEMU displayed all four markers
through `DUCHAMP PRE PE INIT IOKIT`; no panic, exception, abort, assertion,
fault, guest error, or invalid-value report was found. Payload reconstruction,
embedded-payload byte comparison, and the captured-phone-FDT 8 GiB bootshim
test passed (`white_pixels=351016`). No phone image was created or flashed.

SHA-256: artifact ZIP
`88abc1708e77957f872f63a3500af5417672caea32432bf3ef13766166d82e3c`;
kernel `d0fb78b25606e1591d3e1163df81d77950e7fc0e871240fd208b7b1b756e7998`;
ADT `0a94807d462d61d7b083ef16559552995220ce049b04dcd469eb1189206fb3a2`;
payload `3705b05fc0da473dcc272dedb5f900964a29d3a09d1333a052c77d66d148f70e`;
bootshim Image
`fca4e906d6f27b096c4ec0bd71183fa35cfad4d3245967c867b59d0edc7d1546`.

SYSCTL-startup checkpoint (2026-10-28, offline/QEMU only): commit `9fb4f93`
releases the stage-114 stop, adds grouped markers around the internal SYSCTL
callback dispatch, and stops at stage 119 immediately after
`kernel_startup_initialize_upto(STARTUP_SUB_SYSCTL)` returns but before the
first `early_random()` used for `vm_kernel_addrperm`. Source inspection found
that this transition registers SYSCTL OIDs and reads selected Device Tree
properties; it performs no new hardware MMIO initialization. GitHub Actions
run `40598692557` succeeded. Direct QEMU displayed every stage from 115
through 119; no panic, exception, abort, assertion, or fault was found.
Payload reconstruction and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=336880`). No phone image was created or flashed.

SHA-256: artifact ZIP
`e61a16c6b6ebc3bd8e3337e5d64c46d7d7055fbe37f799357f6978ebb8c8422d`;
kernel `7b699acaf8d436ae76ab4eed63e84e4dcbff372501dbbe98ca84aa6d4f22d0d4`;
ADT `579393e952723a794aee92d61ca463fc23e842770760f7f1307180cc230cf426`;
payload `3f92c8a6198fa465a6405498ce3d06a9d725460c6aa080625dc0d5716594b325`;
bootshim Image
`ea63332b0003d1db074b500168a089bf15fe644a4096e4bc1408f70fb19375b0`.

Pre-SYSCTL debug-services checkpoint (2026-10-28, offline/QEMU only): commit
`98e918a` releases the stage-107 stop and records the configured early-service
path before `STARTUP_SUB_SYSCTL`. The SWEET configuration and runtime markers
both prove `ALTERNATE_DEBUGGER=1`, `HYPERVISOR=0`, and
`CONFIG_TELEMETRY=1`. With no alternate-debugger or bootprofile boot arguments,
`alternate_debugger_init()` and `bootprofile_init()` both returned without
allocating their optional permanent buffers or starting a profile timer.
GitHub Actions run `40597098982` succeeded. Direct QEMU displayed stages 108,
109, 112, 113, and the stage-114 stop immediately before
`kernel_startup_initialize_upto(STARTUP_SUB_SYSCTL)`; stages 110 and 111 were
correctly absent. No panic, exception, abort, assertion, or fault was found.
Payload reconstruction and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=314632`). No phone image was created or flashed.

SHA-256: artifact ZIP
`d947e4c60cad90cb8eacc74a789246265ac20f266266bdde63e0567c05d89ff4`;
kernel `acde01e29c96f081d101f497187d37ff8396fcffeddda108b031f4b01fcf06e7`;
ADT `c1227824ab40df09b9b41d7a57016d7aafe67aa93e3d1956e47c88b75d0b7547`;
payload `9923070a2c733995cf6a1316724f53883a228164872dc57b0e625121082812a9`;
bootshim Image
`636ab91b8994df2dd93ec7d1ed54c24d69d85e15b9ef3a739ca4e9c8e678e8eb`.

KDP-initialization checkpoint (2026-10-28, offline/QEMU only): commit
`686ef3b` releases the stage-104 stop, marks entry to and return from
`kdp_init()`, and stops at stage 107 immediately before the next caller-side
service, `alternate_debugger_init()`. Source inspection confirmed that this
path prepares the debugger version string, debug log, KDP timer, packet size,
and crashdump core; with the current boot arguments its optional serial-KDP
path returns without initializing new hardware. GitHub Actions run
`40595234153` succeeded. Direct QEMU displayed stages 105, 106, and 107; no
panic, exception, abort, assertion, or fault was found. Payload reconstruction
and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=291132`). No phone image was created or flashed.

SHA-256: artifact ZIP
`6843aafa41f34c63fbbfc75ec72d0e2a7137c05d91a043c5f951b8e35102b340`;
kernel `6068db99f831ba99c759d2f0fa17c877b77b40eb7bf219ccb62fc6670d4b6e17`;
ADT `fc6afa165cccb2af590239b8c4c619dca5487e85866f4f87e983a7b636c0bfd3`;
payload `5cb938825c649fb431ede0841eface6ad22bb2363072af990ba5b034e6e386be`;
bootshim Image
`039bea2404662801b3f315b0a95734594a51ab9868e1e8897bd103440b924431`.

Physical-carveout checkpoint (2026-10-28, offline/QEMU only): commit
`3229d68` releases the stage-101 stop, verifies at runtime that
`phys_carveout_mb` remains zero, runs `phys_carveout_init()`, and stops at
stage 104 immediately before `kdp_init()`. The zero-value guard would panic
instead of allocating a permanent physical carveout if the boot argument were
unexpectedly enabled. GitHub Actions run `40592448879` succeeded. Direct QEMU
displayed stages 102, 103, and 104; no panic, exception, abort, assertion, or
fault was found. Payload reconstruction and the captured-phone-FDT 8 GiB
bootshim test passed (`white_pixels=278124`). No phone image was created or
flashed.

SHA-256: artifact ZIP
`f015e5ada8a1fc538c855a9a14d00cbfac7ffcc2aafd94ba8cdb60789b83a5dc`;
kernel `d306ab8ca6b0fce929d3f3656924261b513d4f20ee858c8761b6cb4e01c45f30`;
ADT `818f50b642baf6a031859eab7abb98ff2ea0cdadaf8621982a2ceca3b034c625`;
payload `174033736e8059e59655d5fc4f551014d347ab71628f689ce36e910a5e835f3e`;
bootshim Image
`7938712934ddefbe9caf2f30ffbc3cbe2516370a0a2e12998b816e8b5e3efb21`.

Device-IPC-service checkpoint (2026-10-28, offline/QEMU only): commit
`733ca55` releases the stage-98 stop, runs `device_service_create()`, and stops
at stage 101 immediately before `phys_carveout_init()`. Source inspection
confirmed that the function allocates the main device IPC kobject port and
registers it as `HOST_IO_MAIN_PORT`; it does not initialize hardware drivers.
The same commit fixes three-digit stage rendering and wraps the diagnostic
color stripe inside the framebuffer width. GitHub Actions run `40590378357`
succeeded. Direct QEMU displayed stages 99, 100, and 101 correctly. No panic,
exception, abort, assertion, or fault was found. Payload reconstruction and
the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=265792`). No phone image was created or flashed.

SHA-256: artifact ZIP
`c4b4651e7bbb42275eaf9512a9e1778edfd05724ce9dcc1d2bceaaadf6c37870`;
kernel `cf5fa0cec0b69d813df1a4bf11175c73838d847b49639468b92de286173f46c0`;
ADT `291a5aa5c187a1ed86cff8f15c2f3f47b5a6b54c16756b989e42ba08bd791697`;
payload `5bd1bf14c0edb03d6f48c11c12396e1129e6aec315556301aaba4fe8f85f9490`;
bootshim Image
`61afc86d080fc69d779321a6be5f98b02c14dfe63372d914af276cf6cd294ddd`.

Clock-service checkpoint (2026-10-28, offline/QEMU only): commit `20a7c5a`
releases the stage-95 stop, runs `clock_service_create()`, and stops at stage
98 immediately before `device_service_create()`. GitHub Actions run
`40588597145` succeeded. Direct QEMU displayed stages 96 through 98, proving
the clock service returned while the device service remained unexecuted. No
panic, exception, abort, assertion, or fault was found. Payload reconstruction
and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=252724`). No phone image was created or flashed.

SHA-256: artifact ZIP
`c5849dc3a83cf097cac6147993d32fb0b555aab0ff8cdba3071bd6745dc7c98e`;
kernel `6c828f905b80310d323d0b3f62bb8a2c36b692e10338dc2df4b20c39d179a4d5`;
ADT `ebe10db3ed70d504a5903a5c89ec41ec27c0229acf86299d9e7e92383c00a9ad`;
payload `a871a87a905c00c2e29471156b40d70d79de953559d319d8fcc73397c10bbef6`;
bootshim Image
`f18248ae48adef3c3500182e3151682ac70aefd168d386d1e719d07e7e7a567c`.

Thread-binding and mapping checkpoint (2026-10-28, offline/QEMU only): commit
`a6758ef` releases the stage-90 stop, runs `thread_bind(processor)` and
`mapping_adjust()`, and stops at stage 95 immediately before
`clock_service_create()`. GitHub Actions run `40586685767` succeeded. Direct
QEMU displayed stages 91 through 95, proving both requested operations
returned. No panic, exception, abort, assertion, or fault was found. Payload
reconstruction and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=240028`). No phone image was created or flashed.

SHA-256: artifact ZIP
`d5f441dd4b93b8c213800bba030820ed0d35b2de4481948dc6c3ecbc4c6e890f`;
kernel `6b1bda6c2ea30e95f0e69932a7d29049af2ad297f8af3b69c5a317fcbd3563a5`;
ADT `8c4baffa428a7610c0da592497d574af3dcd9a05834016395b06f9d2e1f0d2a7`;
payload `cdf7b3decc03e3bd41e917935b278e4eff85758811e8e44840138857e141db39`;
bootshim Image
`b8c802ec8156efe0ee9b08dbb05b90feb2751e89e2692658a7ecaf96fd71ec9e`.

Early-thread-services checkpoint (2026-10-28, offline/QEMU only): commit
`e5e0712` releases the stage-85 stop, runs `thread_daemon_init()` and the
`STARTUP_SUB_THREAD_CALL` startup phase, and stops at stage 90 before
`thread_bind()`, `mapping_adjust()`, and `clock_service_create()`. GitHub
Actions run `40584664263` succeeded. Direct QEMU displayed stages 86 through
90, proving both requested initialization steps returned. No panic, exception,
abort, assertion, or fault was found. Payload reconstruction and the
captured-phone-FDT 8 GiB bootshim test passed (`white_pixels=219008`). No
phone image was created or flashed.

SHA-256: artifact ZIP
`ff5b48daea6ef075599c89a194aaaea69612277d5bb1f3d317d77da1746b13f1`;
kernel `ff95c58b75f326744b0b2ec9cf6e227abe518c0a0b3b62277227ba4ea712b770`;
ADT `b07a54e7443ae147c1f600900ec0e6822cfb13ef2193215b9da7a412563ce1a4`;
payload `f7867d1886d26c04fd0365ce4d05e55cf6804c0e00231234de079be54d7ca884`;
bootshim Image
`9d93c3dc0d3a806e61fdd8e966dc3aeab99e5fb25255d20a4e7f612b73c4fe7b`.

Scheduler-startup checkpoint (2026-10-28, offline/QEMU only): commit
`3b2e2a7` releases the stage-78 stop, instruments the internal scheduler
startup transitions, and stops at stage 85 after `sched_startup()` returns but
before `thread_daemon_init()`. GitHub Actions run `40583142353` succeeded.
Direct QEMU displayed stages 79 through 85, proving creation of the scheduler
initialization thread, a successful `thread_block()` context switch and
return, creation of the powered-cores update thread, and return from
`sched_startup()`. No panic, exception, abort, assertion, or fault was found.
Payload reconstruction and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=196128`). No phone image was created or flashed.

SHA-256: artifact ZIP
`c2468a11768cf8abcde584086f5b88a190369bdf473e50762babe3cff20405dc`;
kernel `4c7bd28ad9dc93360222f0a808da9ac5afde9bbce8e79a8331ee920850afb45a`;
ADT `51d84604099f02e17478dbbfd2269d98650dacba3c85b3c88a135a22dc8db48d`;
payload `659bba1f36629a238e2f8e1ed07dd7a6860b8ab59b3ee636d828a919eeecb3db`;
bootshim Image
`f92528cf4d3d3f835b13e8e9c2ec2beee07f3199aca16ed68cd6b7c899feecaa`.

Bootstrap-thread pre-scheduler checkpoint (2026-10-27, offline/QEMU only):
commit `e28da41` releases the stage-74 stop, allows `load_context()` to switch
to the first bootstrap thread, records entry into that thread, and stops at
stage 78 immediately before `sched_startup()`. GitHub Actions run
`40581233793` succeeded. Direct QEMU displayed stages 75 through 78, proving
that the context switch completed and `idle_thread_create()` returned. No
panic, exception, abort, assertion, or fault was found. Payload reconstruction
and the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=164648`). No phone image was created or flashed.

SHA-256: artifact ZIP
`30eca85d10c0698977bf5066c655169f5450ec2c8c2cae2af40d36281d8af827`;
kernel `70ece5a043a5949573f5cc7e424abad80b995cd1d55c5d1a4b58b94ad5e9a56c`;
ADT `9512bae994e02d05725d9c6c9d296859c60980fbf612e2c390b60ff896a4e43f`;
payload `7e8a70087027edc777994c30ba029b542476e9710aa4572072f81b2c17845551`;
bootshim Image
`ac3575fa3d0853187a800b82a4a324f4a455dd6ada263df433b02398983c6034`.

Grouped kernel-bootstrap checkpoint (2026-10-27, offline/QEMU only): commit
`e89b099` releases the stage-63 stop, marks the major early
`kernel_bootstrap()` boundaries, creates the first bootstrap thread, and stops
at stage 74 immediately before `load_context(thread)`. GitHub Actions run
`40578492454` succeeded. Direct QEMU displayed every stage from 64 through 74,
including successful returns from `vm_mem_bootstrap()`, OSLOG startup,
`console_init()`, `sched_init()`, Mach IPC startup, `machine_init()`, and
`thread_init()`, followed by successful bootstrap-thread creation. No panic,
exception, abort, assertion, or fault was found. Payload reconstruction and
the captured-phone-FDT 8 GiB bootshim test passed
(`white_pixels=148704`). No phone image was created or flashed.

SHA-256: artifact ZIP
`bbd71334faf2487720bf56acea593c9eca0be90293db8524a3c56d8af53e485b`;
kernel `85028af6d9c383bf6441cbe363983a7fae5f59211260fc4bc58ae20baa27533f`;
ADT `65cbe286a37885df34cd383fb5e70b0a00822509454c0a3f125993ef04c0e495`;
payload `0497a65806ff85200627a4337856790f40da75c4895caa5e60984f2fdf4532e2`;
bootshim Image
`cce3cf98ccd80ba1de72f65c1a02e5a4d610318179bfc11876d3006a51522f07`.

Grouped machine-startup checkpoint (2026-10-27, offline/QEMU only): commits
`f3693e9` and `939ea81` retain stage 59 as a non-blocking marker, enter
`machine_startup()`, mark completion of boot-argument handling and
`machine_conf()`, and stop at stage 63 immediately before
`kernel_bootstrap()`. GitHub Actions run `40576319487` succeeded. Direct QEMU
displayed stages 60, 61, 62, and
`SWEET EARLY 63: DUCHAMP PRE KERNEL BOOTSTRAP`; no panic, exception, abort,
assertion, or fault was found. Payload reconstruction and the captured-phone-
FDT 8 GiB bootshim test passed (`white_pixels=104172`). No phone image was
created or flashed. The earlier run `40574392928` correctly exposed that the
stage-59 stop had not yet been released and was superseded by this result.

SHA-256: artifact ZIP
`b2abf966b60301f50d91346d557f88f50301bd67acdf610cd25582e724d06bab`;
kernel `804653c6e86bef56c55c187770b3def9bd496f162004fc496d6a0479f8534f6a`;
ADT `fb87fcf49ad810697b37de61dcc9b7f8f92c5e33bb06726c3e7b7b348067dd60`;
payload `dfc59bc2cfef7f86c5ce79ab379347c66b81dd69225d76ca7a7ada901c929abc`;
bootshim Image
`1c2a6e93656545e6e7611a29b6be50759cb15d9447611a4ef761b316cc4441e7`.

Pre-machine-startup checkpoint (2026-10-27, offline/QEMU only): commit
`d217d1f444165f7f340557d28c577410ab7dbd45` removes the stage-58 stop,
assigns `gDramBase` and `gDramSize`, initializes and masks
`__stack_chk_guard`, and stops at stage 59 immediately before
`machine_startup(args)`. GitHub Actions run `40570509213` succeeded. Direct
QEMU displayed `SWEET EARLY 59: DUCHAMP PRE MACHINE STARTUP`; no panic,
exception, abort, assertion, or fault was found. Payload source reconstruction
passed. The captured-phone-FDT 8 GiB bootshim test passed with
`white_pixels=85824`. No phone image was created or flashed.

SHA-256: artifact ZIP
`619498ccf55bf411bec2bf99141bb70f411385f218925b8768c0cf6ac9739228`;
kernel `0af722062cebd249c636455f902881be10e4454322eae756b61714ab550b40bd`;
ADT `7f89eb2fda16bd7cb089c21f08e02f85113f0901ff950d75826c15e7ec4e5fe0`;
payload `cf992c6de4ec416d61b077c8887c4bedf168af462d5e37fa9627d1800b3fee68`;
bootshim Image
`091d5cdcec2a39f37003fb10012fb36a64a2b889dfaa0e0dca93ac56e0e416d4`.

DRAM-size-read checkpoint (2026-10-27, offline/QEMU only): commit
`c1d32951be93e81e41f9d6ccff881017b59b142e` lets the
`SecureDTGetProperty()` call read `dram-size`, records the complete 64-bit
value, and places the stage-58 stop before assigning either `gDramBase` or
`gDramSize`. The original panic path is unchanged. Both new patches passed
strict forward and reverse `git apply --check`; GitHub Actions run
`40567636656` succeeded. Direct QEMU displayed
`SWEET EARLY 58: DUCHAMP DRAM_SIZE=0x0000000020000000`, matching the
generated Duchamp-window ADT size (512 MiB); no panic, exception, or abort was
found. The payload source rebuild passed. The captured-phone-FDT, 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=87644`). Artifact ZIP SHA256 is
`0c0c265cd6a7e6d1f5a407a0fd5997af0ccde6730ae075a03d46b5fbb90bd0a5`;
kernel SHA256 is
`e90f2244a5d66b76b62a787a9351fb833f787061d006af6910033c39127c64a8`;
QEMU ADT SHA256 is
`b56ca536eae5854b22f36ae5a412e032269fac456a83e90af764f8fdf08b2ce4`;
payload SHA256 is
`f918432885393cd2cf1aa7e16c5fdf71103b57e0418c8209f10590b11d51ba16`;
and bootshim Image SHA256 is
`638f6d60a46037ad1173e6c3e3f2f74d686cc1957e66bdcd5cae721ef3f75bd5`.
No phone image was prepared or flashed for this checkpoint.

DRAM-base-read checkpoint (2026-10-27, offline/QEMU only): commit
`e8fb66c58047d95c60a9584d386377fcdde89782` lets the first
`SecureDTGetProperty()` read `dram-base`, records the complete 64-bit value,
and places the stage-57 stop before the `dram-size` lookup. The original panic
path is unchanged. Both new patches passed strict forward and reverse
`git apply --check`. Initial Actions run `40561695414` was cancelled without
receiving a macOS runner; replacement run `40564121509` succeeded. Direct QEMU
displayed `SWEET EARLY 57: DUCHAMP DRAM_BASE=0x00000001c0000000`, exactly
matching the generated QEMU ADT value `0x1c0000000`; no panic, exception, or
abort was found. The payload source rebuild passed. The captured-phone-FDT,
8 GiB bootshim path passed its embedded-payload byte comparison and XNU-entry
test (`white_pixels=87604`). Artifact ZIP SHA256 is
`660ff441c4e4645ca15945bfdf74b4b04e426940eb54103f912198fdd24197bb`;
kernel SHA256 is
`f224e874d82fcbc0b0a2acf4f55fd0a74379b32f4b0d0a0d00b0f5a4f9d578cd`;
QEMU ADT SHA256 is
`c226929148431d060bb1b9a6f4fbd2927dc22fcf58685f88e4eb759350019346`;
payload SHA256 is
`c882f6946784275f4f714a51b910d927a5cda35d0f5eb4f331cccd72290e8b33`;
and bootshim Image SHA256 is
`073bc49142a6767470753d34c57fb19ba6d6105396fc4c218c4bb81a3e0a7182`.
No phone image was prepared or flashed for this checkpoint.

Chosen-lookup checkpoint (2026-10-27, offline/QEMU only): commit
`a46c89824be76eea72fd6128299d01d6b8fa07a2` lets
`SecureDTLookupEntry(NULL, "/chosen", &chosen)` execute on the boot-CPU path
and places the stage-56 stop only after a successful lookup, before the first
following `SecureDTGetProperty()` for `dram-base`. The original panic path is
unchanged. Both new patches passed strict forward and reverse
`git apply --check`; GitHub Actions run `40558077806` succeeded. Direct QEMU
displayed `SWEET EARLY 56: DUCHAMP CHOSEN FOUND`; no panic, exception, or
abort was found. The payload source rebuild passed. The captured-phone-FDT,
8 GiB bootshim path passed its embedded-payload byte comparison and XNU-entry
test (`white_pixels=85036`). Artifact ZIP SHA256 is
`b6f675d8c69d37ce473907e553ad4d7dbe6b8284f8ded5d5c43185255d878d33`;
kernel SHA256 is
`4f66829d35276feca329303faaef91641db94e281f4763f7f906e4fcf245f78b`;
QEMU ADT SHA256 is
`9bff98a8d540e8fea55b57c844ebc8f45ccbcdb99168a3ef08dc116c95c2d3fd`;
payload SHA256 is
`47e8c458de12b2523dce187ed7e7206eb2d3dff5a251c4ef8a5db5a61b6859c7`;
and bootshim Image SHA256 is
`568b519a2e01a9f362a85b47b5fb01202a2d5f338eb2fd833c7b7c160fc6671d`.
No phone image was prepared or flashed for this checkpoint.

Hibernation-block checkpoint (2026-10-27, offline/QEMU only): commit
`a1c317bd06a2abf89d904a14a4555380c16ac851` moves the stage-55 stop
after the complete `#if HIBERNATION` block and before the following
`SecureDTLookupEntry(NULL, "/chosen", ...)`. The final DEVELOPMENT kernel
contains `_arm_init` but no `pal_hib_init` symbol, so HIBERNATION is disabled
for this build and the checkpoint proves the disabled block was crossed; it
does not claim that `pal_hib_init()` executed. Both new patches passed strict
forward and reverse `git apply --check`; GitHub Actions run `40553554664`
succeeded. Direct QEMU displayed
`SWEET EARLY 55: DUCHAMP HIB BLOCK PASSED`; no panic, exception, or abort was
found. The payload source rebuild passed. The captured-phone-FDT, 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=85340`). Artifact ZIP SHA256 is
`d3903d3b9ef01a77bb8bc1f2badf679d60cf0a2eadf6023249893c54b72152d9`;
kernel SHA256 is
`564c288a56e962ba3d288b3ec0de8cd7870e1d36614cf6f7d9f31dbc26d0387f`;
QEMU ADT SHA256 is
`7944d61fcf3ed76f819c5e979aba13b60341b260a50e380d8bdd8322193f33fb`;
payload SHA256 is
`a7209a1921c2220d0fac918d217d213724e2338d52a2ebc657cb64d940852101`;
and bootshim Image SHA256 is
`effc944f2d2e1b54e7c99bd9bf9a2612a5dfc3a586101e2d9224cdf842e793a4`.
No phone image was prepared or flashed for this checkpoint.

FIQ-context-return checkpoint (2026-10-27, offline/QEMU only): commit
`a073deca711e124c5caa4c2e8cfdc94c156a376f` lets
`fiq_context_init(TRUE)` execute on the boot-CPU path and places the stage-54
stop immediately after its return, before the `pal_hib_init()` block and all
following initialization. The secondary `arm_init_cpu()` path remains
unchanged. Both new patches passed strict forward and reverse
`git apply --check`; GitHub Actions run `40549741154` succeeded. Direct QEMU
displayed `SWEET EARLY 54: DUCHAMP FIQ CONTEXT RETURNED`; no panic,
exception, or abort was found. The payload source rebuild passed. The
captured-phone-FDT, 8 GiB bootshim path passed its embedded-payload byte
comparison and XNU-entry test (`white_pixels=85908`). Artifact ZIP SHA256 is
`eb9fe80aeebfa68580d01212721faae821a0031c9884f6b9336102b48871d8dd`;
kernel SHA256 is
`9b005f3e1c1bdc286a6b4cc640f297536fca732811dec174bd77df8a9cae22cc`;
QEMU ADT SHA256 is
`2b8a390fd67ec097ff0eec56ffc99f51c7a48ed1b95366738536b427baa9e7b5`;
payload SHA256 is
`d92eaea5f26b34b729989e0966190fd0e026ca1338e70321c3e9d02a12e51dd1`;
and bootshim Image SHA256 is
`c94631c8f998dfcfca2730db9a5a6c55456a6e08ebe966d1a288b56b7b6aa736`.
No phone image was prepared or flashed for this checkpoint.

PE-init-CPU-return checkpoint (2026-10-27, offline/QEMU only): commit
`47951d31a2686ed57451d995472afcd5c7791598` lets `PE_init_cpu()` return
to the boot processor's `arm_init()` and places the stage-53 stop immediately
after that return, before `fiq_context_init(TRUE)`. The secondary
`arm_init_cpu()` path was deliberately left unchanged for this boot-CPU
checkpoint. Both new patches passed strict forward and reverse
`git apply --check`; GitHub Actions run `40480706346` succeeded. Direct QEMU
displayed `SWEET EARLY 53: DUCHAMP PE_INIT_CPU RETURNED`; no panic, exception,
or abort was found. The payload source rebuild passed. The captured-phone-FDT,
8 GiB bootshim path passed its embedded-payload byte comparison and XNU-entry
test (`white_pixels=85788`). Artifact ZIP SHA256 is
`e76b9b5e43e17b5ebf5c4c83d8233b9a221a4543fec7f946905f49d4ac07154a`;
kernel SHA256 is
`433f566d91559a44d980e33d7a57394370ebf1237535eb96daef0350abf3d40e`;
QEMU ADT SHA256 is
`092878a5a1a2627c9421a004b6845602f2832567a9e5bb8e830f5c6bc96ee29c`;
payload SHA256 is
`bc859158de3b40b85b8eea60a62e0f925d3605efea7ab8ee383e42822ab04043`;
and bootshim Image SHA256 is
`705fd01be666a9a166c5cd5ebd5ce20bc3683b93b278e531a5f7c38aca94f7f7`.
No phone image was prepared or flashed for this checkpoint.

GIC-return checkpoint (2026-10-27, offline/QEMU only): commit
`e9e4fb17d7ca3baf7c7fadcfdf7ed5341daadc4a` lets `pe_init_fiq()` return and
places the stage-52 stop in its direct caller, `PE_init_cpu()`, before that
function returns to `arm_init()`. In this XNU ordering, `cpu_timebase_init(TRUE)`
already runs before `PE_init_cpu()`; this checkpoint is therefore specifically
before `fiq_context_init(TRUE)` and later interrupt work, not before the timer.
Both new patches passed strict forward and reverse `git apply --check`; GitHub
Actions run `40471074615` succeeded. Direct QEMU displayed
`SWEET EARLY 52: DUCHAMP GIC RETURNED`; no panic, exception, or abort was
found. The payload source rebuild passed. The captured-phone-FDT, 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=83440`). Artifact ZIP SHA256 is
`6d9afca690eb3fde99850e50c234a9afc56a78bda386e917a57711722fee2586`;
kernel SHA256 is
`96590808362923970ea8cf2b65c9501a120d9cc9551008f727bd9c04d4a12726`;
QEMU ADT SHA256 is
`9fc326a31b0eae4fb40b763e6ea8169d9068bc3fc1b847f120b15bdaaf394fb2`;
payload SHA256 is
`b36a73faa844a8fac482d52f7e35ec172d9fb709c0ea7040ec44bab184751d9f`;
and bootshim Image SHA256 is
`bed4190a92c85861a1c046bc01fc6045a63985cc71f6ca8101822a72925cfc2b`.
No phone image was prepared or flashed for this checkpoint.

ICC-IGRPEN1-ISB checkpoint (2026-10-27, offline/QEMU only): commit
`73d7ae46e84846742ec19b29c353434c006007bd` executes the `ISB`
immediately after the successful `ICC_IGRPEN1_EL1 = 1` write and stops
before returning from `pe_init_fiq()`. The timeout path still stops before
the write. Both new patches passed strict forward and reverse
`git apply --check`; GitHub Actions run `40468936088` succeeded. Direct QEMU
displayed `SWEET EARLY 51: DUCHAMP ICC_IGRPEN1_ISB_DONE`; no panic,
exception, or abort was found. The payload source rebuild passed. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=85724`). Artifact ZIP SHA256 is
`0f8aa93c85d6f50200b99601ad17a7e2d5e53e38e5ba2c577db8fe61500a2ccd`;
kernel SHA256 is
`901e10ff55d1bd52dd61f4b09474e0d99a3510d589a50505fe26f90ebd354b9c`;
QEMU ADT SHA256 is
`f76798d5c605b0db468b1d5a5c3215df5ea14a0d78c84e9b8f2955b883cd261f`;
payload SHA256 is
`82c5e4e6fb8ad70953284407bd45a1132844a23d4776f8dfec8fecd1ebddca3a`;
and bootshim Image SHA256 is
`d1ede2a291b42e323b45ace88bba1b27d02a102cb794977570b0cfbda8e4dd02`.
No phone image was prepared or flashed for this checkpoint.

ICC-IGRPEN1-write checkpoint (2026-10-27, offline/QEMU only): commit
`99bf548c78599748ac69b3caa1c704ce84090725` writes
`ICC_IGRPEN1_EL1 = 1` exactly once after the bounded RWP loop succeeds and
stops before the following `ISB`. A timeout path stops without performing
the write. Both new patches passed strict forward and reverse
`git apply --check`; GitHub Actions run `40436986741` succeeded. Direct QEMU
displayed `SWEET EARLY 50: DUCHAMP ICC_IGRPEN1_WRITE=1`; no panic,
exception, or abort was found. The payload source rebuild passed. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=85528`). Artifact ZIP SHA256 is
`0b08ff4c56ac6f4a9300d4e0e4fcf986ada6f3565b1ceaa72a9212ce650dbb79`;
kernel SHA256 is
`4fdf3d2a0f85f9cd4888fc382742423fb3b6675e11da1805ceafabe6dbdc83d2`;
QEMU ADT SHA256 is
`03b6964b12baff8006de0e89f15758ffc577e4611abe3053d3f2a80b4b6f73af`;
payload SHA256 is
`a254a15f8807ff0a48c784c5a82c2fdb293d01f667936563840d16c350dfec07`;
and bootshim Image SHA256 is
`28fe42a41bb6073cabb1a452e25e2e2f8f25e27ae0711e508c5e3354277d0bb6`.
No phone image was prepared or flashed for this checkpoint.

GICD-RWP-bounded checkpoint (2026-10-27, offline/QEMU only): commit
`a73fcbf248a4291662199ebdfa2c3c4a72b972c6` replaces the Duchamp
unbounded `GICD_CTLR_RWP` wait with a diagnostic loop capped at 100000
iterations and stops after the loop but before `ICC_IGRPEN1_EL1`. Both new
patches passed strict forward and reverse `git apply --check`; GitHub Actions
run `40433794756` succeeded. Direct QEMU displayed
`SWEET EARLY 49: DUCHAMP RWP=0 TO=0 N=00000000`; the first read observed
RWP clear, so the loop completed with zero spins and no timeout. No panic,
exception, or abort was found. The payload source rebuild passed. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=86164`). Artifact ZIP SHA256 is
`8bbc892f97d9cf0e7f1459eccafa9e264e292d08253d53f513069d6b26450e36`;
kernel SHA256 is
`dca3359e9561b23839cbb7fa753ddaca73c9a6e181a6747cb99a7096ffe7adc8`;
QEMU ADT SHA256 is
`6992acd7eee8473d22ce86d3cf0651986e2f5d45d9162a83c2654b15cd86822f`;
payload SHA256 is
`2ea848f0af76cd9489e22d670161df2af774101dfea328c986f1dbb717694b1b`;
and bootshim Image SHA256 is
`d5eb600b2d2d8e2ade2285f6595c38c6d25e396170fedfeb751522834405c933`.
No phone image was prepared or flashed for this checkpoint.

GICD-CTLR-readback checkpoint (2026-10-27, offline/QEMU only): commit
`73e8912196bc72e82ef87bb8586192ee023f6751` reads `GICD_CTLR` exactly
once after the stage-47 write, records both the complete value and its `RWP`
bit, and stops before the polling loop and before `ICC_IGRPEN1_EL1`. Both
new patches passed strict forward and reverse `git apply --check`; GitHub
Actions run `40432649441` succeeded. Direct QEMU displayed
`SWEET EARLY 48: DUCHAMP GICD_AFTER=0x00000053 RWP=0`; no panic,
exception, or abort was found. The payload source rebuild passed. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=86948`). Artifact ZIP SHA256 is
`e5b45a1142b50e765dedc4313883da6c9f627f5a7a170e60e649e2e27fa44985`;
kernel SHA256 is
`180ff0d39c2da09039bcd52b6c52f769deb3f5a17d92e4e671a90c4663065893`;
QEMU ADT SHA256 is
`ad4aed75dbf570269e01aab4884bd34f7467828095136305b769605d44c589f0`;
payload SHA256 is
`6621ed714e6a00b0cde328103d7efa88567a958108ecd3813925cba62f3e69e3`;
and bootshim Image SHA256 is
`d584d009a1b2325d3ff99a89cbfc51cb00fde87c618fce569201bb3edc5bfcfb`.
No phone image was prepared or flashed for this checkpoint.

GICD-CTLR-write checkpoint (2026-10-27, offline/QEMU only): commit
`704b3b96247e8f737f685bf703853cde0c52d468` writes the prepared value
`0x00000053` to `GICD_CTLR` exactly once and stops immediately before the
first `GICD_CTLR_RWP` read and before `ICC_IGRPEN1_EL1`. Both new patches
passed strict forward and reverse `git apply --check`; GitHub Actions run
`40431550650` succeeded. Direct QEMU displayed
`SWEET EARLY 47: DUCHAMP GICD_WRITE=0x00000053`; no panic, exception, or
abort was found. The payload source rebuild passed. The 8 GiB bootshim path
passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=86136`). Artifact ZIP SHA256 is
`c8a879456e477239dd0b0edb250dd3f8ce5b1a64159e2e6b1509ba77efb460ef`;
kernel SHA256 is
`331bcff603c931656c1dd0704b2fc5a81d680a64c69cf688f229a98a466193cf`;
QEMU ADT SHA256 is
`0dd316a4321989e52fdb849d5987bffb2a053c4a758f39c66aba679b48823dd0`;
payload SHA256 is
`22611f37ee1cbd6793ec13c8be00700205720674af4e8201a196c049c0ac1e3d`;
and bootshim Image SHA256 is
`037c06c7d47c017d833f287c885dea3dd37eaa835c50abdbe7a09a3efc41a5c2`.
No phone image was prepared or flashed for this checkpoint.

GICD-CTLR-local-enable checkpoint (2026-10-27, offline/QEMU only): commit
`f9cd916b0828382aa3e2971810b4a4febff23bb1` combines `ARE_NS`,
`ENABLEGRP1A`, and `ENABLEGRP1` into the local `gicd_ctlr` value and stops
before the first `GICD_CTLR` write and before `ICC_IGRPEN1_EL1`. Both new
patches passed strict forward and reverse `git apply --check`; GitHub Actions
run `40430203151` succeeded. Direct QEMU displayed
`SWEET EARLY 46: DUCHAMP GICD_LOCAL=0x00000053`, consistent with the
stage-45 value `0x00000050` plus the requested enable bits. No panic,
exception, or abort was found. The payload source rebuild passed. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=86148`). Artifact ZIP SHA256 is
`60647572baf33d39fab759bf0839aeb697749931e3a3a6755a2b3766eaef6b9a`;
kernel SHA256 is
`9fc2ffb0715e05a42bed6a2f377c9e5515327cf6e6669cb72139ed796f0b4015`;
QEMU ADT SHA256 is
`57870dad78408d77d85fc461f23cea59d3ee666169e9eeab2271c33d29bbd083`;
payload SHA256 is
`97862788703840062e5407f839bc5e745cee8cd6e78582d7d20591bf053709ce`;
and bootshim Image SHA256 is
`4e3936f7c49cb84cb34868612d407ff6017e585b562cdc2c7d4386c4c68a0f7e`.
No phone image was prepared or flashed for this checkpoint.

GICD-CTLR-read checkpoint (2026-10-27, offline/QEMU only): commit
`bad619f7830285b7c5b6acfa5e3e9c04bad8b30b` reads `GICD_CTLR` exactly
once and stops before combining `ARE_NS`, `ENABLEGRP1A`, or `ENABLEGRP1`
into the local value, before any `GICD_CTLR` write, and before
`ICC_IGRPEN1_EL1`. Both new patches passed strict forward and reverse
`git apply --check`; GitHub Actions run `40428601305` succeeded. Direct
QEMU displayed `SWEET EARLY 45: DUCHAMP GICD_CTLR=0x00000050`; no panic,
exception, or abort was found. The payload source rebuild passed. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=86012`). Artifact ZIP SHA256 is
`e9448e94a93b0ee5dd775fd532430ebe107cdf7918be857d67b0cb8c1769a4ee`;
kernel SHA256 is
`69f7cfe78cf68ecc1866d9716c44dcc2a61f1e938d047a771db071b4c54d7731`;
QEMU ADT SHA256 is
`74410f5d7000fb178819e1fa786e398862f4b0b6c6209d6f31980a3cb9b18aeb`;
payload SHA256 is
`33d346ebae72a1877d35db91f0151d0bd5e65a990410545088659fd2f786ad50`;
and bootshim Image SHA256 is
`cef739cb0a970823770fa3c5d569fae5de8833b362fe42a7ad37559ea760b27d`.
No phone image was prepared or flashed for this checkpoint.

ICC-CTLR-write checkpoint (2026-10-27, offline/QEMU only): commit
`e4040e7f971df2dbbf7b8d7e1b555ae27ac6f797` writes the locally prepared
value to `ICC_CTLR_EL1` exactly once and stops before the first
`GICD_CTLR` read and before `ICC_IGRPEN1_EL1`. Both new patches passed
strict forward and reverse `git apply --check`; GitHub Actions run
`40426910967` succeeded. Direct QEMU displayed
`SWEET EARLY 44: DUCHAMP ICC_CTLR_WRITE=0x0000000000008c00`; no panic,
exception, or abort was found. The automatic framebuffer decoder reported
three unknown trailing glyphs, but the saved framebuffer and `fb.txt`
confirm the complete stage-44 marker. The payload source rebuild passed.
The 8 GiB bootshim path passed its embedded-payload byte comparison and
XNU-entry test (`white_pixels=87892`). Artifact ZIP SHA256 is
`a72ebfff2d0c7744f7ef7d170e0562b3e0fa914f69bd953c7d12fb6413eae27a`;
kernel SHA256 is
`557a407c200bbf88fb9ce79d318f401e1e97a4e09d4e42beeeb7a22168ffeb27`;
QEMU ADT SHA256 is
`4680822e6fbb5a40f4071d5282532c07067bf12b3ddf1ecdad90c40f096bc75f`;
payload SHA256 is
`2c37953d2ca987ad669e1c54edc5a78c03c8bd28a06c199a156d32f37301a096`;
and bootshim Image SHA256 is
`f61dca94d05fd940daf9eb191b9722ae5d6f4e1e5ed91a843a9e65729a0e9d06`.
No phone image was prepared or flashed for this checkpoint.

ICC-CTLR-local-EOIMODE checkpoint (2026-10-27, offline/QEMU only): commit
`b8654f28c49816b5288f1b4d2d6559f207d6b05e` clears
`ICC_CTLR_EOIMODE` in the local `icc_ctlr` copy and stops before the first
`ICC_CTLR_EL1` write, before any later GICD access, and before
`ICC_IGRPEN1_EL1`. Both new patches passed strict forward and reverse
`git apply --check`; GitHub Actions run `40425590830` succeeded after Actions
was re-enabled with user approval. Direct QEMU displayed
`SWEET EARLY 43: DUCHAMP ICC_CTLR_EOI=0x0000000000008c00`; the value matches
the stage-42 read because QEMU already reported EOIMODE clear. No panic,
exception, or abort was found. The automatic framebuffer decoder reported
three unknown trailing glyphs, but the saved framebuffer and `fb.txt` confirm
the complete stage-43 marker. The payload source rebuild passed. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=87600`). Artifact ZIP SHA256 is
`df7681d297df991b5e21b02d8137a2a7a07a96373766638aead57784923c7a65`;
kernel SHA256 is
`fca3ed7298e45866fb483f11eb1d208738c5e182a8dafc3e008c1f05ad481caf`;
QEMU ADT SHA256 is
`52fe743dccdf6d6bb593afb3e0fc376cb20be71f7c66774a065274dd6d816630`;
payload SHA256 is
`4c7b950bf5151a9b2d24bcd683fa5afc4eedd8985c6c698834e68cf46fffa253`;
and bootshim Image SHA256 is
`16d1196e3967487ce80921b9243e9fe7c5c27006643a533ed6bc65ab43981295`.
No phone image was prepared or flashed for this checkpoint.

ICC-CTLR-read checkpoint (2026-10-27, offline/QEMU only): commit
`742b0151eb2db4891a77940cfd8b81e1744b6f2e` moves the controlled stop past
one read of `ICC_CTLR_EL1`, but before changing `EOIMODE`, writing
`ICC_CTLR_EL1`, touching the GICD enable path, or writing `ICC_IGRPEN1_EL1`.
Both new patches passed strict forward and reverse `git apply --check`;
GitHub Actions run `40423496961` succeeded. Direct QEMU displayed
`SWEET EARLY 42: DUCHAMP ICC_CTLR_EL1=0x0000000000008c00`; no panic,
exception, or abort was found. The automatic framebuffer decoder reported
three unknown trailing glyphs, but the saved framebuffer and `fb.txt` both
confirm the complete stage-42 marker and value. The payload source rebuild
passed. The 8 GiB bootshim path passed its embedded-payload byte comparison
and XNU-entry test (`white_pixels=87516`). Artifact ZIP SHA256 is
`bd41b214456fc1a35eb641d483af8421e5491c874dabf367ab00c15f2cbd57f2`;
kernel SHA256 is
`977a18507bc7148e8fb62cfba11f054acaf0bb3c7ff3e9528c444a0aebac36f6`;
QEMU ADT SHA256 is
`42e6c984f8026f08ee0e71717b2e32511fbac7ed949eee5c6638100cc0afb751`;
payload SHA256 is
`cbc06e3cd8d04727025834c60260537078bcab4ee2274e8757ef30d6775e53b5`;
and bootshim Image SHA256 is
`64a45a72fca9cc94693126ab97ec7f9f4a990fcaa929a6d6c95c15fe6d9ef7f0`.
No phone image was prepared or flashed for this checkpoint.

ICC-PMR-write checkpoint (2026-10-27, offline/QEMU only): commit
`edf887a57df4416646f3b0e08238ea7ab2c357bd` moves the controlled stop past
one `ICC_PMR_EL1=0xFF` write, but before reading `ICC_CTLR_EL1` and before
writing `ICC_IGRPEN1_EL1`. Both new patches passed strict
`git apply --check`; GitHub Actions run `40422206995` succeeded, and the
built kernel contains `DUCHAMP ICC_PMR WRITE READY`. Direct QEMU displayed
`SWEET EARLY 41: DUCHAMP ICC_PMR WRITE READY`; no panic, exception, or abort
was found. The automatic framebuffer decoder reported three unknown glyphs,
but the saved framebuffer and `fb.txt` both confirm the complete stage-41
marker. The payload source rebuild passed. The 8 GiB bootshim path passed its
embedded-payload byte comparison and XNU-entry test (`white_pixels=85584`).
Artifact ZIP SHA256 is
`4b99be1019bae861d675b2449d8a7bc350534d48a5c284c122aca1dbae9b5998`;
kernel SHA256 is
`fd14831dc90bbf03e32657414e351f1b4fdbc0cfb2d3d6dc92c9daafb6c380a5`;
QEMU ADT SHA256 is
`2c789baca30ef1699f6450ba6fad82279a2a25cfc153e234ad859a4a65b78357`;
payload SHA256 is
`8037d5fbd351ec27ce29640217ea1ae1842bf7a2d2ed23c8cc61f9fc3421f044`;
and bootshim Image SHA256 is
`8f7899428b87cd0fdfbf698e46affe5355b72eec513a545381980a2ee9ccf0f5`.
No phone image was prepared or flashed for this checkpoint.

ICC-BPR1-write checkpoint (2026-10-27, offline/QEMU only): commit
`b5e46132a66f293d4baedd6edfb2950098d6e9af` moves the controlled stop past
one `ICC_BPR1_EL1=0` write, but before `ICC_PMR_EL1`, `ICC_IGRPEN1_EL1`, or
any intervening CPU-interface configuration. Both new patches passed strict
`git apply --check`; GitHub Actions run `40420604838` succeeded, and the built
kernel contains `DUCHAMP ICC_BPR1 WRITE READY` without the stage-39 label.
Direct QEMU displayed `SWEET EARLY 40: DUCHAMP ICC_BPR1 WRITE READY`; no
panic, exception, or abort was found. The 8 GiB bootshim path passed its
embedded-payload byte comparison and XNU-entry test (`white_pixels=85744`).
Artifact ZIP SHA256 is
`49edd9819820bc551a2f02ffd7965a0f78f370150b7bcb11ccb177458070c991`;
kernel SHA256 is
`0c105a5c1fbdb64beb02784f26c13b445a839690129148cc7f30ef27552fb8d4`;
QEMU ADT SHA256 is
`7b4b6a1bc0f234d95c61caf4d06a98c95907b451023fc65fab035f882247c2cd`;
payload SHA256 is
`b4e8f05caab42b96155e78efe616570d486ddb2c92592d04a2541dfadcc5c119`;
and bootshim Image SHA256 is
`49ff624331f8ceef986b962885fcabe2582fdff391294e76797c3fcaf100878f`.
No phone image was prepared or flashed for this checkpoint.

ICC-SRE-ISB checkpoint (2026-10-27, offline/QEMU only): commit
`908fc8143905ce9684bf9aebab0d3692521fc602` moves the controlled stop past
the architectural `ISB` following the `ICC_SRE_EL1=0x7` write, but before the
first `ICC_BPR1_EL1` write or any later GIC CPU-interface access. Both new
patches passed strict `git apply --check`; GitHub Actions run `40419290568`
succeeded, and the built kernel contains the dynamic `DUCHAMP ICC_SRE_ISB`
diagnostic without the stage-38 label. Direct QEMU displayed
`SWEET EARLY 39: DUCHAMP ICC_SRE_ISB=0x0000000000000007`; no panic,
exception, or abort was found. The 8 GiB bootshim path passed its
embedded-payload byte comparison and XNU-entry test (`white_pixels=87584`).
Artifact ZIP SHA256 is
`ec08c3c0f2e8eebd8a8ed45bafd87fe59761c139112c7dba258e49f6809a7121`;
kernel SHA256 is
`4abac0df3eed3d2b02eed95f40f0a4e13a06c7bf0af93035f3b3f7538bd38695`;
QEMU ADT SHA256 is
`9a63e36992d234cca7e28b2cfb878d50b6dc0c2eca55859f6dafdff8ed9566ea`;
payload SHA256 is
`e292f31720724fc224119415599c9d8186a33eed1e9595b9f38bfad502805c19`;
and bootshim Image SHA256 is
`4ca9a8bba8fa776b80bbac65249fc9751a61023ad4bd3a1e9c787d689ed7af32`.
No phone image was prepared or flashed for this checkpoint.

ICC-SRE-write checkpoint (2026-10-27, offline/QEMU only): commit
`878db3d6ddd2eb08bc835f168b46fac0c59d13b5` moves the controlled stop past
one `ICC_SRE_EL1` write of the local value `0x7`, but before the following
architectural `ISB` and before any `ICC_BPR1_EL1` or later CPU-interface
access. The diagnostic stop deliberately uses `DSB` without `ISB` so the
checkpoint preserves that boundary exactly. Both new patches passed strict
`git apply --check`; GitHub Actions run `40418011903` succeeded, and the built
kernel contains the dynamic `DUCHAMP ICC_SRE_WRITE` diagnostic without the
stage-37 label. Direct QEMU displayed
`SWEET EARLY 38: DUCHAMP ICC_SRE_WRITE=0x0000000000000007`; no panic,
exception, or abort was found. The 8 GiB bootshim path passed its
embedded-payload byte comparison and XNU-entry test (`white_pixels=87900`).
Artifact ZIP SHA256 is
`326d5b5bd79f909422e80c637bc001ebec3e760ff7fefcf2d7ccad0472dd097c`;
kernel SHA256 is
`5b913f6b5747edb58d87121d5d227afe3c0300b42e93abed1425fb546f21716b`;
QEMU ADT SHA256 is
`a7dbc7ec43a1c7d35e61b6e2e90af4bba062d3953ee9c31ebb44d813055f0ae8`;
payload SHA256 is
`52422a198714c0c4de9b9cb956d8d249577873ed74607bfda85f1583f5fd4ea2`;
and bootshim Image SHA256 is
`b1beaefdfd0ca1cea4239573a67a0de7f0bbcdb74881b9c95c96515c93a7207a`.
No phone image was prepared or flashed for this checkpoint.

ICC-SRE-local-update checkpoint (2026-10-27, offline/QEMU only): commit
`20c3f31a3e09fba026b63b6ee79de2b37b671c05` moves the controlled stop past
the local `icc_sre |= ICC_SRE_SRE` operation, while keeping the hardware
`ICC_SRE_EL1` write after the stop. Both new patches passed strict
`git apply --check`; GitHub Actions run `40416666146` succeeded, and the built
kernel contains the dynamic `DUCHAMP ICC_SRE_LOCAL` diagnostic without the
stage-36 label. Direct QEMU displayed
`SWEET EARLY 37: DUCHAMP ICC_SRE_LOCAL=0x0000000000000007`, proving that
setting the already-set SRE bit leaves the local value at `0x7`; no panic,
exception, or abort was found. The source barrier remains immediately before
the `ICC_SRE_EL1` write. The 8 GiB bootshim path passed its embedded-payload
byte comparison and XNU-entry test (`white_pixels=87792`). Artifact ZIP
SHA256 is
`58ebefb927059b6b2be0b4fc7c4cb8ceef8aa5cfb5373dedaa93e178891c7a9b`;
kernel SHA256 is
`5ea3b4fe9af6d04842a833f33c52e5a0a9bd0e77dc2b76a92e38a9d995c966bd`;
QEMU ADT SHA256 is
`81c5d35fe9caf936c671b1f5e92b709322d0d6a9247a4c37e42f108cf6f4bb34`;
payload SHA256 is
`cbd72454eec903f3a2170a995cea344eb0a04a924c53d53518c68814dfa1ee7c`;
and bootshim Image SHA256 is
`08c287abe0c2574935f0a38389fdc6976c4dee39606dbd64a7d9d050f43e5f01`.
No phone image was prepared or flashed for this checkpoint.

ICC-SRE-read checkpoint (2026-10-27, offline/QEMU only): commits
`c310861dd40dbdd009f7712603c18aced2e668dd` and diagnostic follow-up
`5a20560669eac50870b68ad21d92653eec9e8dea` move the controlled stop past a
single `ICC_SRE_EL1` read, but before setting `ICC_SRE_SRE` or writing the
register. All new patches passed strict `git apply --check`. GitHub Actions
runs `40412637682` and `40414220687` succeeded. The follow-up was required
because the current QEMU `kprintf` path produces no serial/log output; it
renders the captured value directly through the early framebuffer instead.
Direct QEMU displayed
`SWEET EARLY 36: DUCHAMP ICC_SRE_EL1=0x0000000000000007`, proving the read
returned `0x7`; no panic, exception, or abort was found. The source barrier is
before both `icc_sre |= ICC_SRE_SRE` and the `ICC_SRE_EL1` write. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=87508`). Final artifact ZIP SHA256 is
`bffdee19887658d8b4f3feee9881fdcfc88407bf199b87f0ab44c55f21719b83`;
kernel SHA256 is
`4f317a9c56c5a17687dced0fd54bc6d677994bb6de3b334f870ffa21d741308a`;
QEMU ADT SHA256 is
`f64afcc63e6bc60f6b43a8cc5f22b5045f49fe024dd3eebc9276ec505df016c8`;
payload SHA256 is
`16add4d7f90de7c32157307594edb071f651fa7d95354ede156ff882b626aba2`;
and bootshim Image SHA256 is
`35293cf8c9fa6552620c06e53a1ea0356ecf6ff4c8301f9a3c441b1549d4111c`.
No phone image was prepared or flashed for this checkpoint.

GICR-enable-write checkpoint (2026-10-27, offline/QEMU only): commit
`8d8b5d1fcff860ea723eb1b4b5d5db708ee892f8` moves the controlled stop past
the single `GICR_ISENABLER0` write, but before the first read of `ICC_SRE_EL1`
and all later GIC CPU-interface configuration. Both new patches passed strict
`git apply --check`; GitHub Actions run `40410897889` succeeded, and the built
kernel contains `DUCHAMP GICR ENABLE WRITE READY` without the stage-34 stop.
Direct QEMU displayed `SWEET EARLY 35: DUCHAMP GICR ENABLE WRITE READY`; no
panic, exception, or abort was found. A read-only monitor check reported
`GICR_ISENABLER0=0x08000002`, exactly bits 27 (virtual timer from the QEMU ADT)
and 1 (`SWEET_IPI_SGI`). The first and last priority words remained
`0xA0A0A0A0`. The 8 GiB bootshim path passed its embedded-payload byte
comparison and XNU-entry test (`white_pixels=86220`). Artifact ZIP SHA256 is
`90258a9e32da99ebf4014e31e12d2cea8781631be57e28f91e643ddb725bd072`;
kernel SHA256 is
`4632f75bc095337a9b7892027a4ef9da82d96c28bc0b17fca956008054b51ecb`;
QEMU ADT SHA256 is
`11d950db4caf88fcaf57b6d1477bacfd0370f6d13227408e0a006f7785b03341`;
payload SHA256 is
`a8640790189aece3fa5457fd39ac3323bc9378a1bb5d8a7a22a8052b838dac22`;
and bootshim Image SHA256 is
`ad0ff766a78686792cd07d0ec1d0823289a7b3c103c367d91df66f897dbb3975`.
No phone image was prepared or flashed for this checkpoint.

GICR-all-priorities checkpoint (2026-10-27, offline/QEMU only): commit
`7c2bafb97f44b439ea19a292cbf5a55646703811` moves the controlled stop past
all eight 32-bit `GICR_IPRIORITYR0` writes (offsets 0 through 28), but before
the first `GICR_ISENABLER0` write. Both new patches passed strict
`git apply --check`; GitHub Actions run `40409236556` succeeded, and the built
kernel contains `DUCHAMP GICR PRIORITIES READY` without the stage-33 stop.
Direct QEMU displayed `SWEET EARLY 34: DUCHAMP GICR PRIORITIES READY`; no
panic, exception, or abort was found. Eight separate read-only monitor checks
reported `0xA0A0A0A0` for every priority word, while
`GICR_ISENABLER0=0x00000000`, proving that priority setup completed without
enabling an interrupt. A QEMU HMP bulk `xp /8wx` read misleadingly returned
zeros, so the result was rechecked and confirmed with individual reads. The
8 GiB bootshim path passed its embedded-payload byte comparison and XNU-entry
test (`white_pixels=85900`). Artifact ZIP SHA256 is
`2c637dafa31fc96644d5f05c8cfd7be617d78a5aa97259b2f6521f4d5999ab92`;
kernel SHA256 is
`5d71f6a9862aa9a9bdcc858769fae034cd8b02ac03ee9fe5b56d0706ec09da7c`;
QEMU ADT SHA256 is
`6c65e44a59f01c2a9e6ee353e1832c8d6a341a7c61505d536e25aab2db45c2aa`;
payload SHA256 is
`71799d8bbe63124d2401f212a3e1fb083995d91b5e366188ea5d8decc8217196`;
and bootshim Image SHA256 is
`7377fc3f403786578fda24c8c96fe7c05a08434e5638872f3bd55e0df255080c`.
No phone image was prepared or flashed for this checkpoint.

GICR-first-priority-write checkpoint (2026-10-27, offline/QEMU only): commit
`9af35d7a96d6d3f100ba37fc7edc6d2fdc64fb90` separates the first
`GICR_IPRIORITYR0` write at offset zero from the remaining priority writes,
and stops before offsets 4 through 28 and before `GICR_ISENABLER0`. Both new
patches passed strict `git apply --check`; GitHub Actions run `40407587527`
succeeded, and the built kernel contains `DUCHAMP GICR PRIORITY0 WRITE READY`
without the stage-32 stop. Direct QEMU displayed
`SWEET EARLY 33: DUCHAMP GICR PRIORITY0 WRITE READY`; no panic, exception, or
abort was found. Read-only monitor checks reported the first priority word as
`0xA0A0A0A0`, the next priority word as `0x00000000`, and
`GICR_ISENABLER0=0x00000000`, proving that only the intended priority write
ran. The 8 GiB bootshim path passed its embedded-payload byte comparison and
XNU-entry test (`white_pixels=86536`). Artifact ZIP SHA256 is
`6e650ae2bbebeca019e5f136f9a1f9701e420bd91aed7c231062edd3edea3f11`;
kernel SHA256 is
`3d60ce9b2d22240c02daef774d2f0946bf2120e300e159a77a7c51985833007d`;
QEMU ADT SHA256 is
`817f554db9850b4d7fcd93af355ec3e95fbebe86e47becd75d02e7fb6efb1ea5`;
payload SHA256 is
`b48c4d9beb398cdb83692a2da3bc35facc3c46f19d38e372cfda743e2222dba2`;
and bootshim Image SHA256 is
`6da15cd276b957766d0e008b1cf0a9dce30dc7ba257a3b9e0828ac744597224f`.
No phone image was prepared or flashed for this checkpoint.

GICR-IGROUPR0-write checkpoint (2026-10-27, offline/QEMU only): commit
`dca407e5a9a2747b17f6fcabd0bc5603fe1b1aab` moves the controlled stop past
the first `GICR_IGROUPR0` write (`0xFFFFFFFF`), but before any
`GICR_IPRIORITYR0` or `GICR_ISENABLER0` write. Both new patches passed strict
`git apply --check`; GitHub Actions run `40405673875` succeeded, and the built
kernel contains `DUCHAMP GICR IGROUPR0 WRITE READY` without the stage-31 stop.
Direct QEMU displayed
`SWEET EARLY 32: DUCHAMP GICR IGROUPR0 WRITE READY`; no panic, exception, or
abort was found. Read-only monitor checks reported `GICR_WAKER=0x00000000`
and `GICR_IGROUPR0=0xFFFFFFFF`, confirming the isolated group write. The
8 GiB bootshim path passed its embedded-payload byte comparison and XNU-entry
test (`white_pixels=86516`). Artifact ZIP SHA256 is
`d13725fbe8d0173965d59e37530285d83f23ef6cc7f3f06ef7c115cc681b95b2`;
kernel SHA256 is
`ee1b152f93b467279e71f00792193582a9f2120bafa377d3d47b6b46e58f5f5e`;
QEMU ADT SHA256 is
`04d00515132d8283701edc7e8c99fb22a7d139e9931d9efa30405e7e16005f47`;
payload SHA256 is
`ac8ab4351dcfeb4e79b3447b5b6df6fc17642394cbfed145297557e5b6cdaefb`;
and bootshim Image SHA256 is
`0ed8c980f34f6212badc7b08439f8ebbf0c3c8c08a83bce1f76c46f153716159`.
No phone image was prepared or flashed for this checkpoint.

GICR-awake checkpoint (2026-10-27, offline/QEMU only): commit
`638b0cbf5f2c4e07a95d68ab63a823b3cb05c930` moves the controlled stop past
the complete `CHILDRENASLEEP` polling loop, but before the first write to
`GICR_IGROUPR0`. Both patches passed strict `git apply --check`; GitHub Actions
run `40401666217` succeeded, and the built kernel contains
`DUCHAMP GICR AWAKE READY` without the stage-30 stop. Direct QEMU displayed
`SWEET EARLY 31: DUCHAMP GICR AWAKE READY`; no panic, exception, or abort was
found. A read-only monitor check reported `GICR_WAKER=0x00000000`, confirming
that the polling condition had cleared before the checkpoint. The 8 GiB
bootshim path passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=85376`). Artifact ZIP SHA256 is
`c90a852391a328d4dcbc5e911f3a9e90323951cec96651ad325ed3941a17c295`;
kernel SHA256 is
`8e92a4028e16188d663c41d332ebd244f39fb21eea2038a27ce990a8402f9f75`;
QEMU ADT SHA256 is
`d8041de5b7a13c9ac4599b1cc02334b5f0bae274a89f442afbbd61b84d85467c`;
payload SHA256 is
`393af77c3b31b15f091a1ec5b55df16af667ed32f860c8d09f58078dc8518f6c`;
and bootshim Image SHA256 is
`3f92670d8c3d2b407e6b1f38f7075437090a414ebc764c29d825931d0aa4f1de`.
No phone image was prepared or flashed for this checkpoint.

GICR-WAKER-write checkpoint (2026-10-27, offline/QEMU only): commits
`4de128cb6792d01e0d551558a4ce5095fd4b45b5` and corrective
`08aa0d995c404b206cf2cf9f65ddf3f2dcc956aa` move the controlled stop past
clearing `PROCESSORSLEEP` and the single `GICR_WAKER` write, but before the
first polling read of `CHILDRENASLEEP`. The first CI run exposed that dxb's
strict `git apply` skipped patch 0103 despite the permissive local `patch`
check; the hunk was corrected and verified with `git apply --check`. GitHub
Actions run `40399036931` then succeeded, and its kernel contains the stage-30
strings but not the old stage-29 stop. Direct QEMU displayed
`SWEET EARLY 30: DUCHAMP GICR WAKER WRITE READY`; no panic, exception, or
abort was found. A read-only monitor check after the write reported
`GICR_WAKER=0x00000000` (stage 29 had read `0x00000006`), confirming that QEMU
cleared both sleep bits before any kernel polling read. The 8 GiB bootshim path
passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=86156`). Artifact ZIP SHA256 is
`1a4ea1a8e0342fa741273f7b6e43afde8843e6542c251e56ae0c8fd85d15b371`;
kernel SHA256 is
`2b064c6101ebd729acad9c23481139ecb2b3f4eda8f86b9705c9bb755a046f48`;
QEMU ADT SHA256 is
`b858362249fd07ac98755d51d2926877b04f1e0b37c230d5bbab0f9a38f33b0f`;
payload SHA256 is
`bc5eca9e8179ba9ea6cb55181f2db350530a0ed831c35d6d6cea072fe8b08fbc`;
and bootshim Image SHA256 is
`2b0f070251cbfda619cc3c1f95efbfe037b991aceed5e871fab82ee66721639e`.
No phone image was prepared or flashed for this checkpoint.

GICR-WAKER-read checkpoint (2026-10-26, offline/QEMU only): commit
`2cc8e1084cc5c1a627bba76fdf6eddadd2e168b0` moves the controlled stop past
the first `GICR_WAKER` read and before clearing `PROCESSORSLEEP`, changing the
local value, or writing any GICR register. GitHub Actions run `40393220355`
succeeded. Using the QEMU-only GICv3 ADT with the Duchamp diagnostic RAM
window, direct QEMU displayed
`SWEET EARLY 29: DUCHAMP GICR WAKER READ READY`; no panic, exception, or abort
was found. A read-only QEMU monitor check reported `GICR_WAKER=0x00000006`, so
both `PROCESSORSLEEP` and `CHILDRENASLEEP` were set. The 8 GiB bootshim path
passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=86076`). Artifact ZIP SHA256 is
`60109cc7fd887809e128c131df4918ad413950a6ef932685a57dc52fcd506614`;
kernel SHA256 is
`08d8f164bfb5e3f58badb2d80ee33ff3a6dc3a0bcfa6175aab7cf63803ad63ee`;
QEMU ADT SHA256 is
`d97695cc5eece82a6247e1feb7053a9ba210c09b2c26dae04423774e776a85ed`;
payload SHA256 is
`e3f21cdf6d9124b9933c2e9d1110238de14a9808c841da2d71f28f1594ce655c`;
and bootshim Image SHA256 is
`5b2ffc5c463a7a96e57f7b2944a5d11baaa2d710e86c0451bc862045b81b6842`.
No phone image was prepared or flashed for this checkpoint.

GICR-TYPER checkpoint (2026-10-26, offline/QEMU only): commit
`6c513023e54ed9e785fc3aa4e0ba63bab1acf882` moves the controlled stop past
`find_gicr_pe_base()`, proving that `GICR_TYPER` was read and a redistributor
matching the boot CPU was found, while stopping before the first
`GICR_WAKER` read. GitHub Actions run `40387966765` eventually succeeded.
The first direct test deliberately exposed an ADT/model mismatch: the phone
GICR address caused a data abort at `pe_init_fiq+0x168` in QEMU. A separate
QEMU-only ADT now combines QEMU virt GICv3 addresses (`GICD=0x08000000`,
`GICR=0x080a0000`, virtual timer INTID 27) with the diagnostic bootshim's
measured Duchamp RAM window (`0x1c0000000 + 0x20000000`). The phone/default
ADT values are unchanged. With that ADT, direct QEMU displayed
`SWEET EARLY 28: DUCHAMP GICR TYPER READY` with no panic, exception, or abort.
The 8 GiB bootshim path passed its embedded-payload byte comparison and XNU
entry test (`white_pixels=85304`). Kernel SHA256 is
`3cb141c51eb598fbc07991678edd6b5f824b6b436ad7a7c11ac95367b0abee50`;
QEMU ADT SHA256 is
`fc7e51a61fe7712cac60e8dc26b22a2f564f60d63a302114b3e72cfc675327b4`;
payload SHA256 is
`1c8c8e30b4e7c41e07575f86a200c931f640fa6c820927d9815b4fe6811dd9cd`;
and bootshim Image SHA256 is
`dffcc0288188d09f98e648b3a1b2b9cfe634be5ee28ff0f37bf9a096e3e20e79`.
No phone image was prepared or flashed for this checkpoint.

GIC-map checkpoint (2026-10-26, offline/QEMU only): commit
`689d674f3c320846c4b62ad0bc75a9f999375e5b` moves the controlled stop past
successful `ml_io_map()` calls for both GICD and GICR, but before
`find_gicr_pe_base()` and its first `GICR_TYPER` MMIO read. GitHub Actions run
`40383300486` succeeded. The artifact ZIP SHA256 is
`8c838b80c7177e95fe20df745923a406c2c94a647352b96a4fd33825adbb5460`;
the kernel SHA256 is
`851d471b03bddf24d06317a943ac5edd3fcec0c79eba49357899956ca8745287`;
and the rebuilt payload SHA256 is
`44228caf625e889c4ea91a87519b61d10c22cc098c01f960b5a748d8f9e7a96b`.
Direct QEMU displayed `SWEET EARLY 27: DUCHAMP GIC MAP READY`; no panic,
exception, or abort was found. The captured-phone-FDT, 8 GiB bootshim path
passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=76428`); its Image SHA256 is
`0de62b9d9120abdf2bf9eb01031ff1e5da8432ed0d778cd5aae3c5fd43670783`.
No phone image was prepared or flashed for this checkpoint.

GIC-reg checkpoint (2026-10-26, offline/QEMU only): commit
`416948811d49357667a0accd9b3f495da46fb1be` moves the controlled stop past
the `/arm-io/gic` lookup and validation of its mandatory `reg` cells. It
rejects zero-sized GICD/GICR regions and physical-address addition overflow,
then stops before `ml_io_map()` and therefore before any GICD/GICR MMIO read
or write. GitHub Actions run `40381045575` succeeded. The artifact ZIP SHA256
is `d9d83496cc153e8df79250e196d104564628f677056f6d1879c7bf5f5464c957`;
the kernel SHA256 is
`2e52257a3a44e8c0b1aedea854a65785c6e4f804e1fe0e9d0292858ada9bbf0a`;
and the rebuilt payload SHA256 is
`79883ee6dee7350fded78210b5cdee83b2a25ece1b976d5aa9847efeebdf41e9`.
Direct QEMU displayed `SWEET EARLY 26: DUCHAMP GIC REG READY`; no panic,
exception, or abort was found. The three trailing unknown glyphs are the known
framebuffer-decoder limitation. The captured-phone-FDT, 8 GiB bootshim path
passed its embedded-payload byte comparison and XNU-entry test
(`white_pixels=74924`); its Image SHA256 is
`9327e1d0d2b72d2e01bafca2c4f9850fe40cabf917ecc9fcb037a07a1607e7b6`.
No phone image was prepared or flashed for this checkpoint.

GIC-entry checkpoint (2026-10-26, offline/QEMU only): commit
`b4e35b1f89e82a0c2ff04d7b6afdf9dd0d84fb39` moves the controlled stop to the
entry of `pe_init_fiq()`, before GICD/GICR discovery, mapping, or register
access. This proves that `ml_map_cpu_pio()` and `cpu_timebase_init(TRUE)`
returned and that `PE_init_cpu()` reached the GICv3 initialization boundary.
GitHub Actions run `40378344512` succeeded. The artifact ZIP SHA256 is
`b2708f022ed290772e943cb680671ed24da5e5706df3cd90429a7e27714d4d3a`; the
kernel SHA256 is
`187d189dc59a3b016f2738eaade58acf99f8a075e7327d6020b9e1c5ada96fec`; and the
rebuilt payload SHA256 is
`980f8c56c2a3a8845d974584792950213d34761f0f4254080e3da95ff0be5f38`.
Direct QEMU displayed `SWEET EARLY 25: DUCHAMP GIC ENTRY READY`; no panic,
exception, or abort was found. Its framebuffer decoder reported three unknown
glyphs after the marker, so the wrapper returned nonzero despite the successful
checkpoint. The complete captured-phone-FDT, 8 GiB bootshim path passed its
embedded-payload byte comparison and XNU-entry test (`white_pixels=76680`); its
Image SHA256 is
`387dbba2c8eae3fda1f55c27f36405df9bd20cbd0b7c728187bcd17b90ae9ed6`.
No phone image was prepared or flashed for this checkpoint.

CPU-PIO checkpoint (2026-10-26, offline/QEMU only): commit
`479a6081428f53d5d2f704ad7ef2297ce8b1b8f9` places the controlled stop after
`ml_map_cpu_pio()` and before `cpu_timebase_init(TRUE)`. GitHub Actions run
`40376523768` succeeded. Direct QEMU displayed
`SWEET EARLY 24: DUCHAMP CPU PIO READY` without a visible panic, and the full
captured-phone-FDT, 8 GiB bootshim path passed (`white_pixels=76412`). No phone
image was prepared or flashed for this checkpoint.

PLATFORM checkpoint (2026-10-26, offline/QEMU only): commit
`c8eaa0fc58d8bce01a9e3ce4752b8d81061817ab` moves the controlled stop to
immediately after `PE_init_platform(TRUE, &BootCpuData)` and before
`ml_map_cpu_pio`, GIC, or `cpu_timebase_init`. GitHub Actions run
`40374543035` succeeded. The kernel SHA256 is
`8494ddce333f613aa55170a5c0cad8e860df36a9c6194b57abd4f0310607ebbc`;
the rebuilt payload SHA256 is
`425b7f5882f21174e216b371dcf2c662d05613876d806e7c344e4f9638ff558b`.
Direct QEMU displayed `SWEET EARLY 23: DUCHAMP PLATFORM READY` with no visible
panic. The complete captured-phone-FDT, 8 GiB bootshim/materialize/ready/jump
path also passed (`white_pixels=76760`); its Image SHA256 is
`8d8deef304ea4d33ae750e711411d185d269e915432cf7f7c0c9916206bdb7f9`.
No phone image was prepared or flashed for this checkpoint.

CPU-IDLE checkpoint (2026-10-26, offline/QEMU only): commit
`310935877302bb2aa35a5cbd78293b918e3ef040` adds a controlled stop immediately
after `cpu_machine_idle_init(TRUE)` and before `PE_init_platform(TRUE)`, GIC,
or timer setup. GitHub Actions run `40274811327` succeeded. The kernel SHA256
is `15f939d382fb4e35d4fce21b68124afc49c9182e648f456603e1ad255871f160`;
the rebuilt payload SHA256 is
`57d5380044152b28055181c7e73fb37f24168f922c5dc52deaa70821374729cb`.
Direct QEMU displayed `SWEET EARLY 22: DUCHAMP CPU IDLE READY` with no visible
panic. The full captured-FDT, 8 GiB bootshim/materialize/ready/jump path also
passed (`white_pixels=76496`); its Image SHA256 is
`5f5b8ad9af178812705007876dbf0eed8e0031de87b93ff85ea9a1cc246a409e`.
No phone boot, partition write, or hardware claim was made for this checkpoint.

The offline phone candidate is
`work/duchamp-xnu-cpu-idle-stage22-avb-none-lz4.img`, exactly 64 MiB, SHA256
`70426d5ba8f6f57c0531eef9870720e62163ec087d9af66ee79222a21efee3c7`.
AOSP `avbtool verify_image` verified its NONE vbmeta footer and the SHA-256
`boot` descriptor over the measured 16,318,464-byte payload region. Its LZ4
legacy kernel was decompressed and byte-compared equal to the tested bootshim
Image (`5f5b8ad9af178812705007876dbf0eed8e0031de87b93ff85ea9a1cc246a409e`).
This image is prepared but has not been flashed.

CPU-IDLE hardware checkpoint (2026-10-26): after explicit approval and guarded
preflight, the AVB-NONE/LZ4 candidate was written to `boot_a` only. The POCO
X6 Pro framebuffer showed the complete expected early trace and the controlled
terminal line `SWEET EARLY 22: DUCHAMP CPU IDLE READY`, with no visible panic.
Photo evidence is `work/duchamp-xnu-cpu-idle-hardware-pass.jpg`, SHA256
`80c2d0d3a03ec25202f7d836ea01e8a2b6054426a9cb609088f82bb363e64266`.
The guarded recovery then verified and restored the original 64 MiB `boot_a`
SHA256 `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`.
Android `V816.0.17.0.UNLMIXM` completed boot on slot `_a`; the device again
reported `duchamp`, `mt6897`, and Magisk `uid=0`. No other partition was
written during the test or restoration.

CONSOLE hardware checkpoint (2026-10-25): XNU built from commit
`ef86db3e2168c40992d5d80db265ede3425abf41` reached the controlled
`DUCHAMP CONSOLE READY` stop on the POCO X6 Pro (`duchamp`, MT6897). The
on-device framebuffer showed successful return from `arm_vm_init`,
`serial_init`, kprintf startup, `PE_create_console`, and `PE_init_printf`,
with no visible panic. The tested kernel SHA256 was
`45fe3c67cdf4bb5ad93d76c69aef0761c046701ee3f9ef2cc86e4e0b8b74e9a4`;
the tested boot image SHA256 was
`bff9ddadf09855a9cdfba031c3a36ba481aa54144fead6b3cf0567f263d9848d`.
Photo evidence is `work/duchamp-xnu-console-ready-hardware-pass.jpg` with
SHA256 `4976cf986e56007d38eab7f1aacb94ef3fc8192824da1d2f8966a2b7e29e0705`.
After the test, the verified 64 MiB stock `boot_a` image SHA256
`1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`
was restored. Android `V816.0.17.0.UNLMIXM` completed boot on slot `_a`, and
Magisk root returned `uid=0`. No partition other than `boot_a` was written.

KPRINTF hardware checkpoint (2026-10-25): XNU built from commit
`2db493c27f778c6d14b94366ceb198caf5289e62` reached the controlled
`DUCHAMP KPRINTF READY` stop on the POCO X6 Pro (`duchamp`, MT6897). The
framebuffer showed successful return from `arm_vm_init`, `serial_init`, and
the kprintf startup level, with no visible panic. The tested boot image SHA256
was `21db524362144ee062ae6bf4bc31f4e2c6cdef6a2132967e7ecf7df43477907f`;
photo evidence is `work/duchamp-xnu-kprintf-hardware-pass.jpg` with SHA256
`ef45c6391c621979a786e3950271e64e787ff6e94be18f108a1ef3e19ba7ed04`.
After the test, the verified 64 MiB stock `boot_a` image SHA256
`1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`
was restored. Android `V816.0.17.0.UNLMIXM` completed boot on slot `_a`, and
Magisk root returned `uid=0`. No partition other than `boot_a` was written.

Direct device read (2026-10-24): ADB/root reports Linux
`6.1.57-android14-11` on aarch64 and the expected ARM feature set. Android's
`dmesg` exposes no usable EL or PSCI diagnostic, so the current EL cannot be
confirmed from userspace. Do not add a guessed SMC path; the handoff backend
must remain rejected until EL/firmware entry state is measured or documented.

Live platform contract (2026-10-24): the decompiled live FDT declares
`arm,psci-1.0` with `method = "smc"`, CPU nodes with `enable-method =
"psci"`, `arm,gic-v3`, and an ARMv8 timer plus MediaTek MT6897 system-timer
nodes. This is concrete platform data for the future backend; it does not
prove that an arbitrary loader may invoke PSCI from its current exception
level, so no SMC or hardware handoff was attempted.

DTB memory comparison (2026-10-24): `vendor_boot`'s embedded DTB describes
only `0x40000000`..`0x80000000` (1 GiB), while the live FDT describes RAM up to
`0x300000000` and includes the high range used by the payload at
`0x1c0000000`. The guard accepts the live FDT and rejects the embedded DTB as
`payload window is outside live RAM`. This rejection is now documented as a
required safety property for future loader tests.

Vendor DT table extraction (2026-10-24): `vendor_boot_a` contains an Android
DT table with magic `0xd7b7ab1e`, total size `396071`, one entry, and entry
DTB size `396007` at table offset `64`. The extracted embedded DTB has SHA256
`8aeadd5306b84193384c0f14dea51c1ba23afd7419c7150c1ea1eb2566c49022`, which
differs from the live `/sys/firmware/fdt` SHA256
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
Running the guard against the embedded DTB rejects the current payload as
`payload window is outside live RAM`; the live FDT remains authoritative for
the current boot. This demonstrates that boot-time DT selection/overlay or
memory description changes the handoff contract; no image was modified.

Handoff bounds hardening (2026-10-24): `mt6897_handoff_run` now checks
window-end overflow and requires the complete 0x4000-byte boot-args page to
fit inside the validated window, not merely its starting address. Mock success
and translation-failure tests still pass (`MDTIX` and `MDT`); object size is
372 bytes.

Read-only MT6897 boot-chain observations (2026-10-24): the live device is
`duchamp`, `mt6897`, slot `_a`, with root through Magisk. The by-name links
resolve to `boot_a -> sdc38`, `vendor_boot_a -> sdc39`, and `dtbo_a -> sdc41`.
`/proc/cmdline` identifies the MediaTek Android boot path and `hwid.project_name`
is `duchamp`. `/proc/iomem` reports system RAM beginning at `0x40000000` and a
high range beginning at `0x1c0000000`; it also reports the reserved framebuffer
range `0xfcc2f000-0x100000000`, matching the loader framebuffer base
`0xfcc2f000`. These observations do not prove that XNU can reuse Android's
memory map or that a handoff is safe; no partition was read or written.

MT6897 handoff contract (2026-10-24): added `duchamp/loader/mt6897_handoff.c`
and `.h`. It validates aligned in-window entry/boot-args and enforces the
order disable-MMU, clean data cache, install translation, invalidate I-cache,
then enter-XNU through explicit callbacks. Freestanding Clang compilation
passed; object size is 348 bytes. This is a guarded contract/mock boundary,
not a register-level MT6897 backend: no hardware callback or physical handoff
was executed.

MT6897 local loader wrapper (2026-10-24): added `duchamp/loader/mt6897_loader.c`
and `.h`. The wrapper calls the existing bounded materializer and emits a
small handoff manifest with entry, boot-args, memory window, and Duchamp
framebuffer geometry. WSL Clang build passed; the wrapper object is 161 bytes.
With the extracted phone FDT and verified Duchamp payload, the harness returned
`mt6897_prepare=0`, 10 segments, entry `0x1c1480488`, boot args
`0x1c24dc000`, framebuffer `0xfcc2f000` at `1220x2712`. A `0x1000` window was
rejected with result 4. This remains a local bounded-memory test: no physical
RAM mapping, MediaTek DRAM/MMU/cache setup, exception-level change, or XNU
branch exists, and no phone boot was attempted.

QEMU handoff check (2026-10-23): the C materializer output was compared with
`tools/qemu-sweet.py`'s host image using the same payload and Duchamp profile.
Both images were 38,666,240 bytes with SHA256
`098ba6d9bcc62ec3cd437713a416ef17fd53d145b907c1b0cae035696505b62b` and zero
byte differences; entry `0x1c1480488` and boot_args `0x1c24dc000` also matched.
The subsequent QEMU run was not completed in this Windows environment:
Unix QMP sockets are unavailable, and the TCP fallback is blocked by
`WinError 10013` before QMP can connect. The QEMU command was also made
`-nodefaults` so it does not request unrelated `efi-virtio.rom` firmware. This
is an environment limitation, not evidence of an XNU or payload failure.

QEMU controlled jump completed (2026-10-23): the local QEMU process was
allowed to bind its monitoring endpoint and `qemu-sweet.py --framebuffer
duchamp` ran the verified payload for 10 seconds. The framebuffer decoder showed
every marker from `SWEET EARLY 1` through `SWEET EARLY 15`, followed by
`DUCHAMP XNU MEMORY READY`; no panic text appeared and QEMU produced a register
snapshot. The decoder still reports 3 unknown cells from the intentional bottom
stage band, so the status is `incomplete_decode`/snapshot-only rather than a
clean decode. This is a QEMU `virt` result, not MT6897 hardware validation.

Bounded materialization (2026-10-23): added `duchamp/loader/materialize.c` and
`materialize.h`. This stage applies the validated dry-run plan only to a
caller-provided byte window: it copies 10 payload segments, zero-fills their
tails, places the ADT, and creates revision-2 `boot_args`. It contains no raw
physical-memory access, cache/MMU transition, or XNU branch. Strict bare-AArch64
compilation and execution under Unicorn passed. The first segment and ADT were
byte-identical to the payload, boot args reported revision/version 2/2,
physBase `0x1c0000000`, top `0x1c24e0000`, and the exact Duchamp framebuffer.
Reducing the required `0x24e0000`-byte window by one byte returned
`DUCHAMP_GUARD_PLATFORM`, left the destination marker unchanged, and zeroed the
result plan before any copy.

Dry-run loader plan (2026-10-23): added `duchamp/loader/plan.c` and `plan.h`.
After the guard succeeds, this freestanding layer emits the segment source
offsets, physical destinations, copy/zero lengths, ADT placement, revision-2
boot-args values, entry address, and Duchamp framebuffer contract. It contains
no destination-memory writes and no branch to XNU. Strict bare-AArch64
compilation passed. The actual ARM64 function was executed under Unicorn with
the captured MT6897 FDT and verified payload: it returned 10 segments, entry
`0x1c1480488`, ADT `0x1c24d8000`, boot_args `0x1c24dc000`, framebuffer
`0xfcc2f000`/4992/1220x2712x32, and the expected virtual ADT address. A bad
framebuffer stride returned `DUCHAMP_GUARD_PLATFORM` and a fully zeroed plan.

Freestanding loader guard (2026-10-23): added `duchamp/loader/guard.c` and
`guard.h`. The allocation-free ARM64 core validates SWEETXNU v1 payload bounds,
entry placement, a version-17 MT6897 FDT, live RAM containment, fixed and dynamic
reservations, and caller-supplied occupied ranges. It only returns a placement
plan; it contains no payload copy, cache/MMU transition, exception-level change,
or jump to XNU. It compiled with strict freestanding AArch64 warnings enabled and
was executed under Unicorn against the captured MT6897 FDT and real payload.
The valid case returned physical base `0x1c0000000`, entry `0x1c1480488`, ADT
`0x1c24d8000`, boot_args `0x1c24dc000`, and top `0x1c24e0000`. Negative cases
rejected an occupied-range collision, bad payload magic, and truncated FDT, and
left the output plan zeroed. This is host/emulator validation only.

QEMU framebuffer harness update (2026-10-23): `tools/qemu-sweet.py` now accepts
`--framebuffer duchamp`. It consistently uses base 0xfcc2f000, 1220x2712 and
stride 4992 in XNU boot_args, framebuffer capture, PNG conversion and console
decoding. The old hard-coded Sweet geometry remains the default. This repairs
the host harness mismatch only; it does not validate the MT6897 display path.

Full DUCHAMP kernel/QEMU verification (2026-10-23): GitHub Actions run
`39830616234` completed successfully at `9939a0e`; the downloaded artifact ZIP
matched GitHub SHA256 `5cb02f0323e17679ab47a431e039a07a29143d2de45cb12c22ff57f375195f53`,
and `kernel.development.sweet` matched its included SHA256
`4ce45cc4ec6fb7bd6f7db075fffca90816b586022b1f3e00d937a3dedc9116c6`.
An isolated QEMU `virt` run used the 0x1c0000000 + 512 MiB high-memory window,
the minimal one-CPU QEMU ADT, and the Duchamp framebuffer geometry. The screen
reached `arm_vm_init returned` followed by the intentional
`DUCHAMP XNU MEMORY READY` stop, with no panic. The decoder reported three
unknown glyph cells because its final sampled text row overlaps the deliberate
64x32 Stage-0 color band at the physical bottom of the screen; visual inspection
confirmed the text itself is intact. This proves the compiled early-memory path
in QEMU only, not MT6897 hardware execution or display-controller compatibility.

Loader planning guard (2026-10-23): added `tools/duchamp-loader-guard.py`. It
parses a version-17 MT6897 FDT and SWEETXNU v1 payload, requires 2/2 address
cells and identity-mapped reserved-memory, checks the payload window is inside
live RAM, rejects fixed reservations and every overlapping dynamic
`alloc-ranges`, validates all Mach-O payload segment/file bounds and the entry,
and rejects caller-supplied loader/DTB/stack/source ranges. It emits addresses
only and never copies or jumps. Against the captured FDT and verified kernel it
accepted the high-window plan (`phys_base=0x1c0000000`, entry `0x1c1480488`,
ADT `0x1c24d8000`, boot_args `0x1c24dc000`) after checking 52 fixed, four
dynamic and three occupied ranges. Negative checks rejected an occupied-range
collision, bad magic, bad version and a truncated FDT. This remains an offline
snapshot check; a future loader must invoke equivalent checks on the FDT from
the same boot.

Build dispatched: https://github.com/Mehmed911/ios-sweet/actions/runs/39828208185 at source f22878076d156c246bd0605e173e181b0982ddcc. GitHub currently reports queued (no runner/steps started yet); do not claim a linked kernel or a phone XNU boot. Patch commit: 1cadc81582597a05a49d03d219b23a3c2504f5a5. Expected compile-time stop: DUCHAMP XNU MEMORY READY after arm_vm_init.

The low RAM candidate in the previous handoff is superseded. The captured FDT contains dynamic allocation requests whose allowed ranges overlap low RAM. The revised planner excludes each entire alloc-ranges region as well as 52 fixed reservations and nested iomem exclusions. New hardware candidate: physical 0x1c0000000 + 0x20000000 (512 MiB). It has no fixed or dynamic conflicts in that captured tree. It remains a candidate: a loader must repeat checks on the actual boot FDT and check overlap with its Image, DTB, payload and framebuffer before any writes.

Minimal ADTs for one CPU pass serialization/contract tests and reject Qualcomm UFS, wrong timer/GIC and unsafe memory. Candidate hardware timebase is 13MHz and virtual timer INTID 27. QEMU control tests use QEMU GIC addresses/timebase, not MTK emulation. The earlier reference kernel reached arm_vm_init return at both low RAM and the new high RAM base in QEMU, then hit the expected missing DUCHAMPBOOT platform driver panic later in IOKit. That later panic is NOT a successful boot, and the new compile-time stop precedes it. The geometry/stop-patched kernel still needs successful CI and its own QEMU test.

No phone changes in this phase. The POCO still has restored Android; only the standalone 16KB MMU diagnostic has run on its hardware.

---

# DUCHAMP bootstrap handoff — 2026-10-21

This branch is a POCO X6 Pro (MT6897) early-memory experiment, separate from the Redmi/SWEET results below. Patch 0082 replaces bootstrap framebuffer geometry and forces the SWEET build to define DUCHAMP. It deliberately halts after arm_vm_init, before serial_init, PE_init_platform(TRUE), IOKit and BSD. Expected marker: DUCHAMP XNU MEMORY READY.

Physical POCO evidence so far: standalone diagnostic entered EL1, CNTFRQ=13000000, reported TGran16 support, then passed ten actual 16KB alias read/write checks with MMU enabled and restored it off. Android boot_a was restored and independently hash-verified after that trial. XNU and iOS have NOT executed on this POCO.

Local checks: all four changed XNU source files compile individually for SWEET and DUCHAMP (eight objects); geometry and clean patch application checks pass. A minimal single-CPU ADT candidate uses MT6897 GICD 0x0c400000, GICR 0x0c440000, virtual timer INTID 27, and no Qualcomm storage/input/USB nodes. Candidate RAM 0xa0000000..0xbe000000 comes only from a captured map; a future loader must validate the live FDT and every reserved range before writing it. No device dumps or Apple artifacts are committed.

Kernel CI on this branch is the next validation. Even a successful build is not a phone boot image: it still needs QEMU validation and an MT6897 loader with live memory-range checks. Preserve Android and the original boot image.

---

# iOS 16 on sweet (Redmi Note 10 Pro, SM7150) - working notes

## Agent handoff / active work (2026-10-15, latest)

### >>> UPDATE 2026-10-18 (read first, then the 10-17 handoff below) <<<

**STATE at end of 2026-10-18 (evening):**
- On the phone: userdata = **image v15** (`/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v15.img/.simg`; = v14 + `/private/var/preferences/SystemConfiguration/preferences.plist` with one network service "USB Ethernet": Interface DeviceName ue0 Type Ethernet, IPv4 Manual 192.168.7.2/24 router 192.168.7.1, DNS 1.1.1.1 8.8.8.8, set "Automatic" as CurrentSet). Fallback image v14 (v12/v13 deleted).
- Kernels: **0078** = all 8 cores (`cpus=8`, cpu6/7 = A76, homogeneous SMP; mkadt now emits 8 CPU nodes; ADT `shim/out/sweet-0078hi.adt`); **0079** = display off/on via IOMFB selector 12 kern_RequestPowerChange(state) (fade over 6 vsyncs, then black; verified: power button gives "SWEET FB: display off/on"); **0080** = `SWEET NET: <proc> route add/delete/change ...` and `... add/delete address ...` trace (built, `shim/out/shim-boot-0080s.img`, NOT booted yet).
- **Internet over USB: not working yet.** Host side is ready (temporary iptables: FORWARD accept for 192.168.7.0/24 + MASQUERADE, comment "ios-sweet"; lost on host reboot). With v15 the phone sent no DNS and no outbound traffic (only mDNS/ARP) -> configd probably did not apply the service (or did, without default route/DNS). Next: boot 0080s on v15, watch `SWEET NET` lines (does configd add 192.168.7.2 / default route on ue0?). If configd ignores ue0 (not an IOKit IONetworkInterface; configd 1241.140.6 source in `research/configd-1241`, SCNetworkInterface createInterface needs IONetworkInterface -> controller (IOMACAddress, SelfNamed) -> bus), add IOKit stand-ins and/or rename the ifnet to en*.
- Live log listener (`nc -ukl 5140`) may still be running, writing `logs/live-0078s.txt`.

**LIVE LOG over USB (0077, boot 0077s): no more recovery round-trips.** Boot an image with `sweetusb=2`, run `tools/sweet-usbnet.sh logs/live-NAME.txt` on the PC: it waits for the phone's CDC-ECM interface, sets 192.168.7.1/24 (sudo) and prints/saves the kernel console the phone streams every 100 ms as UDP to 192.168.7.1:5140 (starts with the last 64 KiB). `ping 192.168.7.2` checks the link. Current image: `shim/out/shim-boot-0077s.img` (kernel 0077, ADT sweet-0069hi, cpus=6, sweetfb_noconsole=1, sweetfb_hz=30, sweetusb=2). The recovery pull (`tools/sweet-log-pull.sh`) is still the way after a panic/hang before USB comes up.

**🎉 USB networking works (boot 0076s, 18:24 local): `ping 192.168.7.2` from the PC answers in ~1 ms, 0 % loss (200-packet burst, 1500-byte frames, 512/1024-byte frames).** 0075: CDC-ECM function (bulk 0x81/0x01, interrupt 0x82 NETWORK_CONNECTION; host MAC 02:00:5e:77:ee:01) + kernel ethernet ifnet `ue0` (legacy output, header strip like if_fake) with 192.168.7.2/24 set from the kernel (proto_plumb + SIOCAIFADDR on an in-kernel socket). 0076: received frames into one cluster mbuf (mbuf_allocpacket gave a first mbuf of length 0 -> panic "Failed mbuf validity check: len -14"). Host side (Linux cdc_ether, interface `enp0s20f0u3u1`): `nmcli dev set IF managed no; sudo ip addr add 192.168.7.1/24 dev IF; sudo ip link set IF up`. Boot image `shim/out/shim-boot-0076s.img` (`sweetusb=2`). iOS itself does not see ue0 yet (configd needs an IONetworkInterface in IOKit).

**USB device mode works (boot 0074s, 17:45 local): the host enumerates the phone at high speed as `1209:0001 ios-sweet "Sweet iOS (USB bring-up)"`.** 0072 read-only probe: ABL leaves the USB30_PRIM GDSC and all 7 USB clocks on, DWC3 v3.20a (GSNPSID 0x5533320a) in device mode (GCTL 0x00112000), halted (DCTL RUN_STOP 0, DSTS 0x00d3de04), event buffer still at ABL's 0xfdfc8000, QUSB2 PHY alive. 0073 (`sweetusb=2`): DCTL soft reset, own event buffer (polled, interrupt masked), ep0 DEPSTARTCFG/SETEPCONFIG/SETTRANSFRESOURCE, setup TRB, RUN_STOP; control-transfer state machine as Linux ep0.c; descriptors: vendor class, no data endpoints. It ran but no event came: **0074** forces the VBUS session in the Qualcomm wrapper (QSCRATCH 0xa6f8800: HS_PHY_CTRL |= UTMI_OTG_VBUS_VALID(20)|SW_SESSVLD_SEL(28), SS_PHY_CTRL |= LANE0_PWR_PRESENT(24), as Linux dwc3_qcom_vbus_override_enable) -> connect + enumeration. Image `shim/out/shim-boot-0074s.img`. Black Phone app: main thread waits in -[VMVoicemailManager fetchAccounts] (sync XPC; voicemail needs the modem).

**Navigation works (boot 0071s on v14, log `logs/boot-0071s.txt`):** swipe up from the bottom edge returns to the home screen; app switcher works. Two fixes: **0070** pid_hibernate (syscall 435 was nosys on the macOS config -> SIGSYS killed SpringBoard in -[SBToAppsWorkspaceTransaction _didComplete] when an app left the foreground; the only CONFIG_EMBEDDED-only entry in syscalls.master); **0071** touches starting within 48 px of an edge carry kIOHIDDigitizerEventFromEdgeTip (UIKit `_UIEventHIDTouchEdgeTypeForHIDEvent` reads the digitizer EventMask 0xb0007 bits 0x800/0x1000/0x2000/0x40000). Diagnosed, not fixed: Settings (Preferences) SIGTRAP in PodcastsUI func_1cdc47c58: force-unwrap of `URL.volumeTotalCapacity` (nil on our HFS+ root). Phone/Photos/Messages show black (MobilePhone launches, no crash) - next: stack samples via boot-arg `sweetsample=MobilePhone,MobileSlideShow,MobileSMS,SpringBoard` (image `shim/out/shim-boot-0071s.img`).

**🎉🎉 MILESTONE 2026-10-18 ~15:30 local: iOS 16.7 SPRINGBOARD HOME SCREEN ON THE PHONE** (boot `shim/out/shim-boot-0069s.img` = kernel 0069 + ADT `shim/out/sweet-0069hi.adt`, image **v14**; log `logs/boot-0069s-v14-HOMESCREEN.txt`). Home screen with a few apps, Settings opens, Control Center / lock screen / notification center work, touch + buttons work, 6 A55 cores (`cpus=6`), `sweetfb_noconsole=1 sweetfb_hz=30`. Known issue: cannot leave Settings (home gesture / AssistiveTouch home do nothing) - to investigate.
What it took today (in order): 0058 HID services (Apple IOHIDFamily-1915 user client), 0059 iPhone X identity (hw.product etc.), 0060 SPMI keys + GENI touch, 0061 1125x2436 presented display, 0062 RPMh L11C touch power + IOPMPowerSource battery, 0063 GENI FIFO packing (Goodix GT9896), 0064 PRIV_WORK_INTERVAL grant (SpringBoard "Failed to create work interval"), 0065 SMP via PSCI (6 A55), 0066 crash map regions, 0067 console mute without cons_ops write, 0068 IOSurface lookup of an already-mapped surface returns base -1 (backboardd snapshot crash), 0069 UFS log flush 10 s. Image v13: CommCenter removed from launchd.plist, BKNoWatchdogs. **Image v14** = v13 + Setup skipped (`/var/mobile/Library/Preferences/com.apple.purplebuddy.plist` SetupDone/SetupFinishedAllSteps true, SetupVersion 11, daemonizeNeedsToRun false; purplebuddy.notbackedup mini-buddy flags false; managedconfiguration.notbackedup LockdownActivationIndicatesCloudConfigurationAvailable false; springboard MCForceShowCloudConfigurationUI false) + mobileactivationd data ark seeded (`/private/var/containers/Data/System/D90C94C4-F94E-4FCF-8A28-A93BE3846D8E/Library/internal/data_ark.plist`, -ActivationState Activated etc.) + MediaToolbox D22/D221/Default SubServerConfiguration StartRecorderServer=false (mediaserverd crash loop: portrait-filter prewarm called NULL GL). **Activation:** ADT /chosen certificate-production-status 0, effective-production-status-ap 0, certificate-security-mode 1, effective-security-mode-sep 1 -> mobileactivationd's native Hactivation branch (Codex `codex/activation/report.md`; alternative 4-byte daemon patch documented there). Fallback image v13; v12 deleted.

**🎉 TOUCH WORKS (boot 0063u on image v13, 2026-10-18 ~13:15 local):** tapping (i) on Setup's Hello opens the device-info sheet; swipe-up is recognised (spinner, then back to Hello - under investigation). Chain: RPMh L11C vote (0062, `bsd/dev/sweet_rpmh.c`) -> GT9896 @0x5d on GENI SE7 (0063 fixed FIFO packing: register address went out byte-swapped) -> sweet_hid_touch -> SweetHIDTouch -> backboardd. Battery icon OK (0062 SweetBattery IOPMPowerSource, static 100 %). **Image v13** (= v12 + CommCenter jobs removed from launchd.plist + `BKNoWatchdogs`=true and `FBLaunchWatchdogExceptions{com.apple.purplebuddy:100}` in /var/mobile/Library/Preferences/com.apple.springboard.plist): Setup no longer killed by the scene-create watchdog (it blocked in CoreTelephony getSubscriptionInfo -> CommCenter, Codex `codex/setup/report.md`; that report also lists how to skip Setup: SetupDone/SetupFinishedAllSteps/SetupVersion=11 in com.apple.purplebuddy.plist + activation check). v9 deleted, fallback = v12. Input latency ~1 min with 1 CPU -> Codex task 11 = SMP via PSCI (`codex/smp/`).

**INPUT WORKS (boot 0060u on a freshly flashed v12, log `logs/boot-0060u.txt`):** power, volume up, volume down reach iOS (PMIC -> sweet_keys.c -> SweetHIDButtons -> backboardd). Power locks/unlocks (screen "off" shows the kernel console because the panel never really turns off). **Device identity fixed: iPhone X** (home indicator, Face-ID-style Setup). Earlier test (0059u, `sweethidtest=15` fake Home presses) advanced Setup from Hello to the language list.
- **0058** HID: `iokit/Kernel/arm/hid/`: IOHIDEventServiceUserClient + IOHIDEventServiceQueue + IOHIDEvent compiled UNCHANGED from Apple IOHIDFamily-1915.140.3 (= exact version of the iOS 16.7 IOHIDLib, clone in `research/iohid-1915`) over our minimal IOHIDEventService (SweetHID.cpp: SweetHIDButtons consumer page 0x0C power 0x30 / vol 0xE9/0xEA / menu 0x40; SweetHIDTouch digitizer collections). C hooks `sweet_hid_key(key, down)` (0 power, 1 vol+, 2 vol-, 3 home) and `sweet_hid_touch(finger, down, x, y)`. HID logs go to IOLog. Boot-arg `sweethidtest=N` = fake Home press every N s.
- **0059** identity: hw.machine/hw.model/hw.target/hw.product from the ADT (macOS-config kernel used to answer "iPad8,6"/"Redmi Note 10 Pro"). mkadt: root compatible `D22AP|iPhone10,3|xiaomi,sweet|...`, model iPhone10,3, target-type D22, `/product` copied from the real D22AP device tree (`research/ipsw-x/d22ap.adt`, extracted from the IPSW, NOT in git), `/buttons home-button-type 2`. Codex report `codex/mg/report.md`: MG ProductType = sysctl **hw.product** (unrecognized -> iPod), HWModelStr = hw.target, HomeButtonType = `/buttons/home-button-type`; disk cache `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist` (keyed by build + UUID only -> stale iPod answers survived; reflashed clean v12 to clear it).
- **0060** drivers by Codex (`codex/input/hw-report.md`): `bsd/dev/sweet_keys.c` (SPMI arbiter v5 observer reads, PON 0x810 bits KPDPWR/RESIN SID0, PM6150L GPIO2 SID4 0xc110; works), `bsd/dev/sweet_touch.c` (GENI SE7 I2C @0xa84000, starts 45 s after boot). Touch result: SE7 fw ok (proto 3) but **0x5d and 0x38 both time out -> touch IC unpowered** (L11C LDO needs an RPMh vote). Codex task 8 = RPMh client (`codex/rpmh/`), task 7 = battery (`codex/battery/`).
- **0061** (CI 39117078444): red status bar "rdar:45025538" = UIKit "No status bar visual provider for screen" (360x800 pt is no real iPhone). AppleCLCD now presents **1125x2436** (iPhone X) and shows the centered 1080x2400; touch mapped the same; ADT canvas 1125x2436. `sweetfb_native=1` reverts.
- Images: `shim/out/shim-boot-0060b.img` (0060 + /buttons ADT `sweet-0060hi.adt`). Next: 0061 image with ADT from current mkadt.

### >>> HANDOFF 2026-10-17 late (read this first) <<<

**STATE: iOS 16.7 Setup.app "Hello" screen is ON THE PHONE** (boot `shim/out/shim-boot-0057u.img` on image v12). Photo `/run/media/dipa/android/ios-sweet-work/MILESTONE-setup-hello-2026-10-17.jpg`. SpringBoard + backboardd + Setup run; nothing crashes in the GUI path. Remaining crash/relaunch loops: installcoordinationd (should be fixed by 0057, unverified), mediaserverd (VirtualAudio removed in v12, unverified), mobileactivationd (~100/boot, not analysed), bluetoothd + fairplayd.H2 relaunch constantly (no hardware).

**What is on the phone now:** userdata = image **v12** (`/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v12.img` + `.simg` + `.sha256`; v9 kept as fallback, v8/v10/v11 deleted or superseded). Kernel **0057** (`xnu/out-0057`, CI `39067532732`). ADT **`shim/out/sweet-0057hi.adt`** (QEMU twin `research/q0057-hi.adt`). Boot image **`shim/out/shim-boot-0057u.img`**. Boot args: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1`.

**Build a phone image** (kernel K, ADT A): `python3 tools/mkpayload.py $K $A shim/out/payload-X.bin --cmdline "$B" && (cd shim && ./build.sh ../shim/out/payload-X.bin && cp out/shim-boot.img out/shim-boot-X.img)` then check `python3 tools/unpack_bootv2.py shim/out/shim-boot-X.img shim/out/check-X && cmp shim/out/check-X/ramdisk shim/out/payload-X.bin`. QEMU smoke test: `python3 tools/mkpayload.py $K research/q0057-hi.adt $S/csq/payloadX.bin --ramdisk $S/csq/root-fork.img --cmdline "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0"` + `PATH=~/swift/usr/bin:$PATH python3 tools/qemu-sweet.py ... --secs 40 --kernel $K --fail-on-panic` (S = scratchpad; root-fork.img lives in the session scratchpad csq/ dir and may be gone in a new session).

**Kernel workflow:** edit `research/bt28/xnu/...` (keep the pre-edit copy in `research/preNNNN/`), syntax check `python3 tools/xnu-cc.py research/run28.log research/bt28 <file>`, make `xnu/patches/NNNN-*.patch` with `diff -u pre bt28 | sed` path rewrite, add new/changed files to `research/check-patch-order.py` list, run it (must say applied + MATCH), commit + push -> GitHub Actions `xnu` builds (~8 min) -> `gh run download <id> -R dipa-studio/ios-sweet -n xnu-kernel -D xnu/out-NNNN`. **Repo is PUBLIC since 2026-10-17** (private macOS runner minutes ran out: "recent account payments have failed"); public = free runners. Commit trailer: only `Co-Authored-By: dipa-studio <183933817+dipa-studio@users.noreply.github.com>`.

**Phone workflow (user does buttons, Claude runs commands):**
- Boot test kernel: phone in fastboot -> `fastboot boot shim/out/shim-boot-X.img`. NEVER `fastboot getvar`.
- **Read logs WITHOUT filming:** after a test the user holds Power+VolDown -> fastboot -> `fastboot boot recovery/recovery.img` (OrangeFox, temp) -> wait for `adb shell true` -> `tools/sweet-log-pull.sh /run/media/dipa/android/ios-sweet-work/logs/<name>.txt` (reads the 4 MiB console ring the kernel keeps in the last 1025 blocks of userdata; patch 0047). Then `adb reboot bootloader` brings the phone back to fastboot without the user.
- **Flash a root image:** `fastboot flash -S 512M userdata <img>.simg` (7 min, 25 chunks). After a big flash the Xiaomi ABL fastboot hangs: next `fastboot boot` stalls at "Sending" -> the USER must re-enter fastboot by hand (Power+VolDown). Do not retry commands against the hung ABL. A flash right after `adb reboot bootloader` once failed on chunk 1 (USB protocol error): just retry. User must NOT unplug during flash (once interrupted at 25/25 -> reflash).
- **Edit the phone root without reflashing (same-length only):** find the file's raw offset in the local image (it is one extent; search the image for its first 4 KiB), compare with `adb exec-out dd if=/dev/block/sda34 ...`, then `adb push` changed 4 KiB blocks and `dd of=/dev/block/sda34 seek=... conv=notrunc,fsync`, read back. Recovery kernel has no hfsplus.
- **Pull the whole phone root** (12 min): `adb exec-out "dd if=/dev/block/sda34 bs=1048576 count=16384" > img`; mount ro with udisksctl or `sudo mount -t hfsplus -o loop,ro`. To write into a pulled image: `sudo fsck.hfsplus -fy` first (volume is never cleanly unmounted -> Linux mounts ro even with -o force), then `sudo mount -t hfsplus -o loop,force`.
- Making images: copy latest img with `cp --sparse=always`, mount rw with force, change, `sync; umount`, `sha256sum`, `img2simg`. Keep only the latest image + one fallback on the SSD (/home is ~98% full; big work files live in `/run/media/dipa/android/ios-sweet-work/`, old kernels/images archived in `.../ios-sweet-work/archive/`).

**Diagnostics built into the kernel (all SWEET-only):** persistent console log (0047, boot-arg sweetlog=0 off; flush every ~1 s); `|name| text` copies of /dev/null writes for processes in `sweetnull` (default backboardd,SpringBoard; 0048); `IOK name:` IOKit lookup/open trace for `sweetiolog` (default backboardd,SpringBoard; 0049/0054, 400 lines max); `SWEET Sandbox: proc op N` (0050); `STR ...` heap text dump on SIGABRT/SIGTRAP for `sweetscan` (default backboardd,SpringBoard; 0051/0053) - this is how NSException/BSAssert reasons were found; `SMP name tN pc .. bt ..` user stack sampler for `sweetsample` (default SpringBoard,backboardd; first at 90 s then every 120 s, 40 samples, 16 frames; 0054/0055); `SWEET FB: N swaps` every 1000 swaps; `CRASH name ...` crash reports (0043/0044). Symbolicate cache addresses with `ipsw dyld a2s research/dsc/dyld_shared_cache_arm64 <addr - slide>`; main-binary addresses: addr - mh + 0x100000000.

**Patches added today (0046-0057, all CI-built):** 0046 IOSurface (IOCoreSurfaceRoot) + IOMobileFramebuffer (AppleCLCD on /arm-io/disp0) + arm-io nubs; 0047 persistent log; 0048 /dev/null tee; 0049 IOKit trace; 0050 permissive "Sandbox" MAC policy; 0051/0053 heap text on crash; 0052 RENAME_SWAP via exchangedata on HFS; 0054/0055 sampler, swap counter, AKS selectors 35 (extended device state = 17) and 101; 0056 panel copy from the vsync timer at 10 Hz (sweetfb_hz) instead of every swap; 0057 no config_ext_resolver (ACL group entries resolve without memberd). ADT (tools/mkadt.py): /arm-io/disp0, /chosen/display-scale 3, /chosen/unique-chip-id (synthetic 0x5357454554000001) + chip-id 0x8015 -> IOPlatformUUID A9683613-3704-53F2-95D0-98A8FB574E78. Image v9-v12: /private/var/containers/{Bundle,Data/System,Shared/SystemGroup,Temp}; launchd.plist StandardOut/ErrorPath renamed to ...PatX (pointing jobs at /dev/console stops them launching: EACCES); v12: LastSystemVersion=20H392 in plain /var/mobile/Library/Preferences/com.apple.migration.plist (stops the 1-hour data migration that ran every boot), VirtualAudio.plugin moved to /Library/Audio/Plug-Ins/HAL.disabled/.

**Codex helper** (`codex exec --skip-git-repo-check -m gpt-6.1-sol -c model_reasoning_effort=high -s workspace-write -C /run/media/dipa/android/ios-sweet-work/codex -o OUT "$(cat task.md)" < /dev/null`, run detached with setsid nohup; config already defaults to gpt-6.1-sol high). Reports in `/run/media/dipa/android/ios-sweet-work/codex/`: mediaserverd-report.md, installcoordinationd-report.md (-> 0057), ufs-performance.md (ranked UFS speed plan), **ufs/0058-sweet-ufs-faster.patch** (READY, not yet applied: ufslogsecs default 10 s log flush batching, optional ufscache=1 directional cache ops, optional ufswait=1 spin-then-sleep; syntax-checked, host-stub verified; see ufs/README.md). Apply it as patch 0058 after review.

**Claude safety-classifier note:** several messages about QuartzCore renderer selection / writing an HFS reader tool were cut off by an automatic classifier (false positives, user agrees). Keep those topics short or let them be; they are not blockers now (rendering already works).

**NEXT STEPS (in order):**
1. **Input** (Setup stuck on Hello): touch + power + volume as IOHIDEventService/IOHIDDevice services backboardd matches (log shows backboardd matching IOHIDDevice with DeviceUsagePairs and IOService with HIDServiceSupport=true). Phone hardware: Goodix/Focaltech touch over I2C/SPI (check live DT `dtb/`), buttons via PMIC (pon) and GPIO keys. Start with a fake HID service (e.g. power button via a timer or boot-arg) to learn the ABI, then real drivers.
2. **Device identity**: MobileGestalt reports iPod + Home button. Add /product node / product-type (iPhone10,3, D22AP), device class iPhone, home-button-less (Face ID) properties in mkadt; find exact MG keys (MGIOMFBSupport.c, `IODeviceTree:/product` lookups seen in backboardd trace).
3. **Battery**: AppleSmartBattery/IOPMPowerSource style service (status bar shows empty red battery).
4. Apply Codex 0058 (UFS speed), consider cpus>1, check whether installcoordinationd/mediaserverd loops are gone, analyse mobileactivationd.
5. Hide kernel console over the GUI when not debugging: boot-arg sweetfb_noconsole=1 (but then panics are not on screen).

- **🎉 MILESTONE: iOS GUI ON THE PHONE - Setup.app "Hello" screen (2026-10-17 ~21:30 UTC, boot 0057u on image v12).** Photo: `/run/media/dipa/android/ios-sweet-work/MILESTONE-setup-hello-2026-10-17.jpg` (animated "dobar d(an)" hello lettering, status bar "iPod" + battery icon, bottom "Pritisnite Home za otvaranje" = "Press Home to open" (locale hr), (i) button). Rendered by iOS 16.7 SpringBoard/Setup through CoreAnimation -> backboardd -> kernel IOSurface (IOCoreSurfaceRoot) -> kernel AppleCLCD swaps -> ABL panel memory. What made it: data migration finally skipped (v12: `LastSystemVersion` 20H392 in the plain `/var/mobile/Library/Preferences/com.apple.migration.plist`; ADT `/chosen/unique-chip-id` + `chip-id` for IOPlatformUUID), 0057 (no ext resolver -> ACL containers work), plus everything before (0046 display/IOSurface, 0050 Sandbox policy, display-scale 3, containers dirs, RENAME_SWAP, AKS 35/101, 10 Hz present).
  **Missing (next work, in rough order):**
  - **Input: no touch, no power button, no volume buttons** (no HID drivers; backboardd looks for IOHIDDevice / HIDServiceSupport services). Setup is stuck on "Hello".
  - **Device identity: it thinks it is an iPod with a Home button** (status bar "iPod", "Press Home to open"): MobileGestalt has no product/model identity (no /product node, product-type, etc.) - give it iPhone10,3 / home-button-less (Face ID class) identity.
  - **No battery detection** (no battery/charger/PMIC service; status bar battery shows empty/red).
  - Locale came up Croatian (hr) - harmless.
  - Performance: cpus=1, polled UFS (Codex UFS patch in progress: `codex/ufs/`), backboardd presents at 60 Hz.
- **README refreshed (2026-10-17):** read the full notes and updated the public overview through patch 0045, v7 hardware observations and prepared v8 diagnostics. Documents real Apple userspace, the missing display/IOSurface GUI work, limited security services, highmem, persistent userdata root, current tooling and build examples. Documentation only; no kernel build, tests, flashing or phone boot performed.

- **v11 still migrated (boot 0056u, 20:32 UTC, `logs/boot-0056u-v11.txt`).** On iOS kCFPreferencesCurrentHost lands in the plain plist: all DMEnvironment setters (setLastBuildVersionPref, setUserDataDispositionPref, ...) use CurrentHost and the phone's `/var/mobile/Library/Preferences/com.apple.migration.plist` holds DMUserDataDisposition; datamigrator's XPC service runs with `_RoleAccount: mobile`. **Image v12** = v11 + `LastSystemVersion` = 20H392 added to that plain `com.apple.migration.plist` (keeps DMUserDataDisposition, 501:501 0600) + `/Library/Audio/Plug-Ins/HAL/VirtualAudio.plugin` moved to `/Library/Audio/Plug-Ins/HAL.disabled/` (Codex: stops the mediaserverd SIGSEGV loop; untested). **installcoordinationd loop explained (Codex `codex/installcoordinationd-report.md`):** os_crash "Failed to create data directory" EACCES for `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.installcoordinationd/Library/InstallCoordination`: `Library`/`Library/Caches` in the container are ACL-only (uid/gid 0xfffffffe, mode 0000, ACE for group GUID ...012B = gid 299 systemusers); with `config_ext_resolver` the kernel asks an identity resolver (memberd/opendirectoryd) that iOS does not run -> EWOULDBLOCK -> ACE skipped -> EACCES. **Patch 0057**: drop config_ext_resolver from FILESYS_BASE (compatibility UID/GID<->GUID mapping is used instead), likely fixes other ACL-protected containers too. Codex task 3: UFS driver performance design (`codex/ufs-performance.md`).
- **mediaserverd SIGSEGV loop explained (Codex report `/run/media/dipa/android/ios-sweet-work/codex/mediaserverd-report.md`):** the fault (FAR 0x390) is in the HAL plug-in `/Library/Audio/Plug-Ins/HAL/VirtualAudio.plugin/VirtualAudio` (ApplyBeamFormerPreference <- VirtualAudio_PlugIn::SetPropertyData <- HALS_AHPPlugIn::ObjectSetPropertyData <- AudioObjectSetPropertyData <- MediaExperience vaemVADSerializationListener): the default virtual audio device ('vdef', VirtualAudioDevice_Default) does not exist (no audio hardware/driver, no /product/audio). Proposed workaround for GUI bring-up: move VirtualAudio.plugin out of /Library/Audio/Plug-Ins/HAL/ in the next root image (untested). v11 reflashed OK after an interrupted flash (USB unplugged at chunk 25/25). Codex task 2: installcoordinationd crash loop.
- **ROOT CAUSE of the endless migration: no IOPlatformUUID (2026-10-17).** datamigrator's `-[DMMigrator isMigrationNeededWithBuildVersion:lastBuildVersion:clientPID:]` gets lastBuildVersion from `-[DMEnvironment lastBuildVersionPref]` = `CFPreferencesCopyValue("LastSystemVersion", "com.apple.migration", kCFPreferencesCurrentUser, kCFPreferencesCurrentHost)` -> a ByHost file. The phone had `/var/mobile/Library/Preferences/com.apple.migration.plist` (only DMUserDataDisposition) and NO `Preferences/ByHost` directory at all. On arm XNU publishes IOPlatformUUID (gethostuuid) only from `/chosen/unique-chip-id` (8 bytes) + `/chosen/chip-id` (4 bytes) (IOPlatformExpertDevice::generatePlatformUUID, called from IOPlatformExpert::start); the SWEET ADT had neither, so every CurrentHost preference write failed. Fix: mkadt adds `unique-chip-id` = 0x5357454554000001 (synthetic) and `chip-id` = 0x8015 -> UUID `A9683613-3704-53F2-95D0-98A8FB574E78` (same SHA1 namespace computation as the kernel). ADT `shim/out/sweet-0057hi.adt`, boot image `shim/out/shim-boot-0056u.img` (0056 kernel + 0057hi ADT, QEMU OK). **Image v11** = v10 + `Preferences/ByHost/com.apple.migration.<UUID upper and lower>.plist` {LastSystemVersion: 20H392} (501:501, dir 0755 files 0600). Flashing v11 2026-10-17 ~20:10 UTC. Codex (gpt-6.1-sol high) analysing the mediaserverd SIGSEGV loop in `/run/media/dipa/android/ios-sweet-work/codex/` (report `mediaserverd-report.md`).
- **v10 did NOT stop the migration (boot 0056n on v10, 19:18 UTC, `logs/boot-0056n-v10.txt`):** datamigrator + migrationpluginwrapper ran again, backboardd drew the progress UI (13000+ swaps in ~5 min). So `com.apple.DataMigration.plist`/LastSystemVersion is not the deciding input. What is known about the decision (datamigrator XPC service `DataMigration.framework/XPCServices/com.apple.datamigrator.xpc/com.apple.datamigrator`, strings): `Migration sentinel present. Migration necessary.` (sentinel `/private/var/datamigrator/migrate`, created and removed by datamigrator itself; absent in v10), `System build version changed from %@ to %@. Migration necessary.` / `...unchanged... not necessary`, `Disposition dictionary with build version %@ is out of date relative to current build version %@`, `SyntheticDidUpgrade`, DMUserDataDispositionManager; previous build source not found yet (not in the binary's plain strings; likely in DataMigration.framework's DMUserDataDispositionManager / preferences domain `com.apple.migration`). backboardd calls `DMPerformMigrationIfNeeded` and holds SpringBoard in `checkInAndWaitForDataMigration` until it returns. NEXT: find where the previous build version / disposition dictionary is stored (disassemble DataMigration.framework DMUserDataDispositionManager + datamigrator's isMigrationNeeded path), write it into the image; or get datamigrator's os_log out (OS_ACTIVITY_DT_MODE needs a launchd env change).
- **Data migration never records completion -> skip it (image v10, 2026-10-17).** Boot 0056n (18:16 UTC, `logs/boot-0056n.txt`, 30 min): 10 Hz panel copies, backboardd still presents at ~60 Hz (107k swaps), SpringBoard still in `BKSSystemShellService _checkIn` at sample 14. Every migration run takes 1+ hour on cpus=1 and repeats each boot. DataMigration decides from `/var/mobile/Library/Preferences/com.apple.DataMigration.plist` key `LastSystemVersion` (vs ProductBuildVersion 20H392); the pulled phone root (21:01 local) had NO such file. **v10** = that pulled phone state + fsck.hfsplus -fy (volume was marked not cleanly unmounted -> Linux mounts it read-only even with -o force; fsck found only hard-link counts + minor volume header, repaired) + `com.apple.DataMigration.plist` {LastSystemVersion: 20H392} (501:501 0600). `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v10.img` (+ .sha256, .simg); v8 files deleted, v9 kept as fallback.
- **Repo made PUBLIC (2026-10-17, user request) so GitHub-hosted macOS runners are free:** the 0056 CI run was refused ("recent account payments have failed or your spending limit needs to be increased"). Checked before: no device dumps, serials, IMEI or Apple binaries in the history (.gitignore keeps backup/, dtb/, recovery/, research/ out); commit author emails are public now. 0056 rerun `39056660104` passed -> `xnu/out-0056`, QEMU OK, image `shim/out/shim-boot-0056n.img` booted 18:16 UTC.
- **Boot 0055n (17:16 UTC, ~65 min, `logs/boot-0055n.txt`): migration bar reached 99% in ~30 min (was ~60), then crawled.** Root cause of the slowness: backboardd presents the progress UI at ~58 Hz (**167,000 swaps in ~48 min**) and AppleCLCD copied the full 10 MB frame into the panel on every swap -> ~600 MB/s memcpy on the single CPU (cpus=1), starving everything (polled UFS I/O too). Sampler (16 frames): **SpringBoard waits in `-[BKSSystemShellService _checkIn]`** (synchronous BSXPC call to backboardd, from FBSystemShellInitialize <- SBSystemAppMain) - backboardd holds the system shell check-in until the data migration ends, so the migration is the gate to SpringBoard UI. **Patch 0056**: swap only records the latest swap record; the vsync timer copies it to the panel every 60/sweetfb_hz ticks (default 10 Hz); `SWEET FB: N swaps` every 1000.
- **Boot 0054n (16:53 UTC, ~12 min, `logs/boot-0054n.txt`, patch 0054 sampler):** the data migration runs AGAIN on every boot (it completed once in the 0053s run) - completion is not being recorded. backboardd keeps swapping the progress UI (3700+ swaps in ~10 min, `SWEET FB: N swaps`). Sample during migration: SpringBoard main thread blocked in a synchronous XPC call (`mach_msg2_trap <- dispatch_mach_send_and_wait_for_reply <- xpc_connection_send_message_with_reply_sync <- -[BSXPCServiceConnectionMessage _sendSynchronously:] <- BSXPCServiceConnectionProxy ...`). Unsupported AKS selectors seen: 101 `aks_assert_consume`, 93 `aks_get_internal_info`, 34 `_aks_stash_load` (datamigrator), **35 `aks_get_extended_device_state`** (SpringBoard, chronod, remindd, searchd, symptomsd...). **Patch 0055**: AKS 35 answered like 17 (same DER device state), 101 succeeds; sampler backtraces 16 frames, 40 samples (~80 min).
- **MILESTONE: FIRST iOS PIXELS ON THE PANEL (boot 0053s long run, 15:33 UTC, ~60 min; photos IMG_20261017_183029/183222/183419; log `/run/media/dipa/android/ios-sweet-work/logs/boot-0053s-long.txt`, 407 KB, 1428 flushes).** The iOS data-migration boot screen (Apple logo + progress bar) was shown and the bar advanced to full in ~60 minutes. It is drawn by **backboardd through our kernel display path**: `SWEET SURF: backboardd create id 2/3 1080x2400 fmt 0x42475241 (BGRA) bpe 4 bpr 4352 size 10452992 keys 11`, IOSurface sels 9, 27, 5, 34 and traps 2/3 (lock/unlock), IOMFB SwapBegin (4) / SwapEnd (5, 1132-byte struct) / GetLayerDefaultSurface (3) / 68 / 55, then `SWEET FB: swap N layer 0 surface 2|3 1080x2400 ... a 0,0 1080x2400 b 0,0 1080x2400` alternating (double buffering; only the first 16 swaps are logged). Triggered by `com.apple.datamigrator` (AKS sels 101/93/34 return unsupported) and `com.apple.migrationpluginwrapper`. Probably ProgressUI-style CoreGraphics drawing into IOSurfaces (no GPU used). After the migration: SpringBoard and backboardd stay up (exec once each, no crash), nothing new drawn; crash loops only for mediaserverd, installcoordinationd, mobileactivationd (~108 each in the hour); bluetoothd and fairplayd.H2 relaunch constantly (no hardware). Kernel console text overlays the image (sweetfb_noconsole=1 would hide it).
- **MILESTONE: SpringBoard and backboardd both stay up (boot 0053s on v9, 15:29 UTC, `logs/boot-0053s.txt`).** With /chosen/display-scale = 3: `exec SpringBoard` once, `exec backboardd` once, no CRASH for either; MobileGestaltHelper reads IOMFB size/dot pitch; backboardd opens AppleCLCD (sels 57,15,22,29,33,79,74 as before). No IOSurface creates and no swaps: backboardd keeps polling `IOProviderClass IOAcceleratorES` (-> 0 found) and AGXAccelerator/IOAcceleratorESLegacy - no GPU, so no CoreAnimation renderer yet. Log goes quiet after ~47 s (only 47 flushes): the system idles. NEXT WALL: CoreAnimation rendering without a GPU (CPU path) so the window server produces frames.
- **SpringBoard's invalid mode = scale 0 (boot 0053n, 15:19 UTC, `logs/boot-0053n.txt`, heap scan):** `FBSDisplayMode cannot be configured as requested : <FBSDisplayMode: ...; infxinf@0x (1080x2400/0) 60Hz sRGB SDR>` - pixel size and 60 Hz are fine, scale is 0. libMobileGestalt (MGIOMFBSupport.c, sub_19c560a54) reads `display-scale` (u32, default 0) and `display-rotation` from **IODeviceTree:/chosen**, pixel size via IOMobileFramebufferGetDisplaySize (MobileGestaltHelper sel 8/28 in the log). mkadt now adds `/chosen/display-scale` = 3 (1080x2400 @3x = 360x800 pt). ADT `shim/out/sweet-0054hi.adt` (QEMU `research/q0054-hi.adt`), image `shim/out/shim-boot-0053s.img` = 0053 kernel + 0054hi ADT. Possible catch: MobileGestalt may have cached scale 0 in `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/...`.
- **MILESTONE: backboardd survives and opens the display (boot 0052n on v9, 15:07 UTC, `logs/boot-0052n.txt`).** No `CRASH backboardd`. It walks `IODeviceTree:/arm-io` children, matches IOMobileFramebuffer, `open AppleCLCD type 0 -> 0x0`, calls IOMFB selectors 57, 15, 22, 29, 33, 79 (GetBlock, out 1580/40), 74 (SupportedFrameInfo), 12, 6, 27, 17, 84, 50; opens IOCoreSurfaceRoot (sel 13); looks for AGXAccelerator / IOAcceleratorES / IOAcceleratorESLegacy (none, repeatedly), `IODeviceTree:/product` (none, repeatedly), `/buttons`, aop-smart-cover, IOPMrootDomain. No swaps yet. **SpringBoard now gets past display discovery** and dies (sig 5) in `-[FBSDisplayMode _initWithWidth:height:preferredScale:scaleOverride:refreshRate:gamut:hdr:rotation:virtual:validityCheck:]+580` <- `_initWithCADisplayMode:scale:rotation:` <- `FBSDisplayConfiguration _initWithImmutableDisplay:` <- `FBSDisplaySource initWithDisplay:` <- `FBSDisplayMonitor` (slide 0x14504000): "FBSDisplayMode cannot be configured as requested". Checks: width/height >= 2, preferredScale > 0, scaleOverride >= 0, refreshRate non-zero, valid gamut/HDR/rotation. Suspects: refresh rate 0 (IOMFB timing blocks answered with zeros) and/or scale 0 (MobileGestalt main-screen-scale; no /product node in the ADT). **Patch 0053**: heap text scan also on SIGTRAP and for SpringBoard (default sweetscan list backboardd,SpringBoard) to read the exact mode description.
- **Image v9 (2026-10-17) = v8 + `/private/var/containers/{Bundle,Data/System,Shared/SystemGroup,Temp}` (root:wheel 0755; on iOS these live on the data volume, absent from the rootfs) + launchd.plist with StandardOutPath/StandardErrorPath renamed to ...PatX (the in-place phone fix; daemons' stdout reaches the log via the 0048 /dev/null tee).** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v9.img` SHA256 aa9f9139...6e67, `.simg` 12,145,303,864 bytes; written through `sudo mount -t hfsplus -o loop,force`. **Patch 0052** (`xnu/patches/0052-sweet-hfs-rename-swap.patch`, CI `39042761826` -> `xnu/out-0052`, QEMU OK, image `shim/out/shim-boot-0052n.img`): vn_rename falls back to VNOP_EXCHANGE when VNOP_RENAMEX(RENAME_SWAP) returns ENOTSUP for two regular files on one volume (HFS exchange swaps data and cnode descriptors = swap semantics). Flashing v9 started 2026-10-17 ~15:00 UTC.
- **backboardd EXCEPTION FOUND (boot 0051n, 14:41 UTC, `logs/boot-0051n.txt`, patch 0051 heap scan):** `*** Terminating app due to uncaught exception 'NSInvalidArgumentException', reason: '*** -[NSURL initFileURLWithPath:]: nil string parameter'`. First-throw stack (slide 0x337f0000): `+[NSURL fileURLWithPath:]` <- `-[BSSystemContainerForCurrentProcessPathProvider libraryPath]` <- `cachesPath` <- backboardd main+0x1d858 (StartWindowServer, shader cache path). BaseBoard: libraryPath = `BSSystemSharedResourcesDirectoryForIdentifier` = `BSSystemSharedDirectoryForIdentifier(id)` + "/Library"; that calls `container_system_path_for_identifier` (libsystem_containermanager -> `_container_legacy_lookup` -> containermanagerd XPC), which returned NULL (BaseBoard logs "Error getting shared system container ..."). With 0050 the sandbox denials are gone. containermanagerd.log.0 in the pulled (pre-0050) image: "Did not receive any persona attributes", "Expected to find at least one persona", notify_register_dispatch failed 9; `/private/var/containers` does NOT exist in the root image (on iOS it lives on the data volume). usermanagerd does create kernel personas 99/199/1000, but fails to save `/private/var/keybags/usersession.kb` and `persona.kb`: "Failed to atomically swap writing file: Operation not supported (45)" (HFS has no RENAME_SWAP). NEXT: create `/private/var/containers` (and check what containermanagerd needs for system group containers), fix or emulate RENAME_SWAP on HFS, then re-check backboardd.
- **Disk housekeeping (2026-10-17):** /home was at 4 GiB free. Moved (not deleted) `xnu/out-0010..0044` and old `shim/out/*.img`/`payload-*.bin` (everything before 0046) to `/run/media/dipa/android/ios-sweet-work/archive/{xnu,shim-out}` (6.3 GiB); /home now 8.7 GiB free. Large work files (phone-root.img 16 GiB, logs, tracev3 dumps) live in `/run/media/dipa/android/ios-sweet-work/`. **Patch 0051** (`xnu/patches/0051-sweet-crash-heap-strings.patch`, CI `39041440935`): on SIGABRT of a process in boot-arg `sweetscan` (default backboardd) the crash log prints heap text runs as `STR ...` (to find the NSException reason). Boot 0051n 14:41 UTC.
- **Boot 0049n (14:11 UTC, `logs/boot-0049n.txt`, patch 0049 trace): backboardd's IOKit lookups before it dies** (each run): `IODeviceTree:/arm-io/pearl-sep` -> none, matching ApplePearlSEPDriver -> none, `IOService:/IOResources/AppleKeyStore` open OK, matching IOHIDDevice (DeviceUsagePairs) / `HIDServiceSupport` notifications, `usb-drd,t8027` notification; **never any IOMobileFramebuffer / display lookup** - the exception happens before display detection. launchd (tracev3) shows backboardd's mach lookups denied with `error = 159: Sandbox restriction`: com.apple.mobilegestalt.xpc, com.apple.iohideventsystem, com.apple.system.notification_center, com.apple.logd, containermanagerd, ACCHWComponentAuthService, oscard. libsystem_sandbox uses `__mac_syscall("Sandbox", op, arg)` (ops: 1 init, 2 check, 3 note, 4 container path, 5/6/7/8 extensions, 0x15 check_bulk, ...); with no policy named "Sandbox" every call gets ENOPOLICY. **Patch 0050** (`xnu/patches/0050-sweet-sandbox-policy.patch`): built-in permissive MAC policy "Sandbox" in sweet_amfi.c (mpo_policy_syscall returns 0, container/extension ops ENOENT; logs first use of each op as `SWEET Sandbox: proc op N`).
- **Phone root pulled (16 GiB, 12 min, `adb exec-out dd if=/dev/block/sda34`) to `/run/media/dipa/android/ios-sweet-work/phone-root.img` (loop-mounted ro at /run/media/dipa/iOSRoot).** No .ips crash reports. logd tracev3 (Persist, LZ4 `bv41` blocks, decompressed strings in `ios-sweet-work/tracev3/all.txt`): /private/var/db/uuidtext is EMPTY so only launchd's own messages are readable. Findings: v8 launch failure = `Service could not initialize: posix_spawn(/usr/libexec/backboardd), error 0xd - Permission denied` (xpcproxy exit 78) - /dev/console not openable for the mobile user; backboardd[98] spawned `com.apple.MTLCompilerService` before SIGABRT; **launchd denies many mach lookups with `error = 159: Sandbox restriction`** (mediaserverd -> com.apple.backboard.display.services, remoted, mobiletimerd -> sleepd, identityservicesd -> apsd) and **tccd exits OS_REASON_SANDBOX "profile not found"** - no Sandbox kext/profiles on SWEET; likely cause of many daemon crash loops (next wall after the display). CF's uncaught-exception text never reaches stderr for daemons (no CF handler; libc++abi prints only the type). **Patch 0049** (`xnu/patches/0049-sweet-iokit-trace.patch`): `IOK name: ...` console lines for registry path lookups, child iterators, matching (with result count/class), matching notifications and IOServiceOpen of the processes in boot-arg `sweetiolog` (default backboardd), max 400 lines.
- **CONFIRMED: launchd StandardOut/ErrorPath=/dev/console stops backboardd from launching.** After the in-place rename (boot 0047n-b, log `logs/boot-0047n-b.txt`) backboardd launches again and dies as on v7: sig 6, `___pthread_kill <- abort <- demangling_terminate_handler <- _objc_terminate <- std::terminate <- _dispatch_client_callout <- _dispatch_once_callout <- main+0x9334` (window-server dispatch_once). It never opened AppleCLCD or IOCoreSurfaceRoot (no `SWEET FB/SURF: backboardd` lines) -> throws before/at display detection. **Patch 0048** (`xnu/patches/0048-sweet-devnull-tee.patch`, CI `39037749668` -> `xnu/out-0048`, image `shim/out/shim-boot-0048n.img`): writes to /dev/null by processes named in boot-arg `sweetnull` (default `backboardd,SpringBoard`) are printed as `|name| text`. Boot 0048n (13:48 UTC, log `logs/boot-0048n.txt`): only `|backboardd| libc++abi: terminating due to uncaught exception of type NSException` (CF's reason line goes to os_log, not stderr, despite CFLOG_FORCE_STDERR/OS_ACTIVITY_DT_MODE). Next: pull the whole 16 GiB root from recovery (`adb exec-out dd if=/dev/block/sda34`) to `/run/media/dipa/android/ios-sweet-work/phone-root.img` and read ReportCrash .ips files / logd tracev3 for the exception reason.
- **Persistent log WORKS (boot 0047n on v8, 13:31 UTC; pulled from OrangeFox: 70 KB, 111 flushes, `/run/media/dipa/android/ios-sweet-work/logs/boot-0047n.txt`).** In 3 min **backboardd was never exec'd** (v7 ran it), ~70 bare `exec xpcproxy`, SpringBoard loops on FBSDisplayMonitor (no display), mediaserverd sig 11 loop, locationd, lockdownd sig 5. Suspect the v8 plist (StandardOut/ErrorPath=/dev/console on backboardd). **In-place plist edit from recovery (no reflash):** launchd.plist is one extent at image/partition byte offset 0x1e025f000 (195 blocks; verified bytes identical on phone vs local v8 mount); renamed StandardOutPath->StandardOutPatX and StandardErrorPath->StandardErrorPatX (same length, both jobs) in blocks 68 and 105 via `adb push` + `dd of=/dev/block/sda34 seek=... conv=notrunc,fsync`, read back VERIFIED. Phone now differs from local v8 image in those 2 blocks (files in `/run/media/dipa/android/ios-sweet-work/`). Test boot 0047n 13:38:42 UTC. Recovery kernel has no hfsplus (raw block edits only).
- **Patch 0047: persistent console log (CI `39036478663` -> `xnu/out-0047`, QEMU no panic; phone image `shim/out/shim-boot-0047n.img` = 0047 + sweet-0046hi.adt + 0045n cmdline).** `_cnputs` (all console output: kernel printf + daemons' /dev/console) also appends to a 4 MiB ring in sweet_ufs.c; after the UFS partition is ready and writable (ufsrw=1) a thread writes new ring blocks + header to the LAST 1025 blocks (4 KiB) of userdata every ~1 s and SYNCHRONIZE CACHE (prints `SWEET LOG: console log to the last 4100 KiB ...`). Read: phone to fastboot -> `fastboot boot recovery/recovery.img` (OrangeFox) -> `tools/sweet-log-pull.sh OUT.txt` (adb dd of that area + `tools/sweet-log.py`). Not yet verified on the phone. Panics after the last flush are not in it (screen still shows them). 2x font attempt reverted: XNU's v_scale only scales the progress icon.
- **Boot 0046n on v8 (13:05 UTC, VID_20261017_150522_HSR_120):** phone prints `SWEET SURF: IOCoreSurfaceRoot registered` and `SWEET FB: AppleCLCD 1080x2400 stride 4320 at 0x9c000000, default surface 1` (nubs + match work on hardware). Visible userspace: early boot tasks, launchd_cache_loader, `exec SpringBoard`; no `exec backboardd` / `SWEET FB: backboardd` line seen in the readable frames (video blurry). Frame 00:47: lower half of the screen shows OLDER console text (16:01:12) below newer lines -> unconfirmed hint that a swap copied an old snapshot of the panel (CA reads the default/displayed surface = panel memory). SpringBoard still dies in `-[FBSDisplayMonitor _initWithBookendObserver:transformer:]+1160` (sig 5, slide 0x30960000). **Shim: 2x console font** (`shim/loader.c` Video.v_depth scale field = 1) so phone videos are readable; image `shim/out/shim-boot-0046b.img` = 0046n + 2x font.
- **Patch 0046: built-in IOSurface + IOMobileFramebuffer (2026-10-17, offline, NOT phone-tested).** `xnu/patches/0046-sweet-iosurface-iomfb.patch`: new `iokit/Kernel/arm/SweetSurface.{h,cpp}` (IOCoreSurfaceRoot + IOSurfaceRootUserClient: sel 13/0/4/34/35, traps 0-5, wired buffers mapped into the caller, per-client refs) and `SweetFramebuffer.cpp` (AppleCLCD : IOMobileFramebuffer on /arm-io/disp0: sizes, swap = CPU copy of enabled layers into the ABL panel memory, 60 Hz vsync via sendAsyncResult64WithOptions(CanDrop), panel memory published as the default IOSurface, kernel text console paused on the first swap only with `sweetfb_noconsole=1` (default keeps the console: pausing switches it to serial and would hide panics)); SweetPlatformExpert creates nubs for /arm-io children (not gic) attached to the platform expert (IOPlatformDevice::compareName casts its provider to IOPlatformExpert, so nubs under the arm-io nub never matched - first CI build showed that in QEMU). mkadt: /arm-io/disp0 {device_type display-subsystem, compatible sweet,display, canvas-width 1080, canvas-height 2400}. CI `39021572169` -> `xnu/out-0046`. **QEMU** (`research/q0046-hi.adt`, RAM disk init, msgbuf): `SWEET SURF: IOCoreSurfaceRoot registered`, `SWEET FB: AppleCLCD 1080x2400 stride 4320 at 0x9c000000, default surface 1`, init alive, no panic. Phone image **`shim/out/shim-boot-0046n.img`** (SHA256 9c4d2fe9..., CI `39024108588` with the review fixes: swap bounds check, zeroed 64-bit async ref, port release, 1.5 GiB wired budget, ref leak/race fixes; QEMU re-checked) = 0046 kernel + `shim/out/sweet-0046hi.adt` + the 0045n cmdline; boot it on image v8 (backboardd/SpringBoard log to console) and film. Expected new console lines: `SWEET SURF: <proc> create id ...`, `SWEET FB: backboardd sel N ...`, `SWEET FB: swap ...`. Open question for the next wall: QuartzCore's IOMFB server builds its renderer from Metal first (`CAMetalContextCreate`), GLES only when enabled; how the CPU renderer gets selected on a device without a GPU is not yet established.
- **IOSurface values ABI (offline RE, `/run/media/dipa/android/ios-sweet-work/iosurface-values.md`) - TODO in SweetSurface (0046 only accepts and drops values, so IOSurfaceCopyValue always returns NULL):** sel 9 SetValue in = {u32 id, u32 pad, IOCFSerialize([value, key]) or ([dict] = merge)}, sel 0xb RemoveValue in = {u32 id, u32 pad, key\0} (empty key = remove all); both out 4 bytes = new generation, client accepts only (gen+2)|1. Kernel after each change: gen = (gen+2)|1 (odd, never 0) -> state+0x20, serialized size (>=1) -> state+0x28. sel 0xa in {u32 id, u32 0, u8 0}, out {u32 ?, u32 gen, serialized non-bulk dict}; too small -> 0xe00002db + needed size (client retries x16). sel 0x1b in 0x88: bulk struct 0x70 @0, u64 valid size @0x70, u64 changed mask @0x78, u32 id @0x80 -> copy masked fields into state+0x30 (bit0 32B @0, bit1 16B @0x20, bit2 8B @0x30, bits3-10 1B @0x38..0x3f, bits11-14 24B @0x40/4B @0x58/8B @0x5c/1B @0x64).
- **IOMFB display matching confirmed (offline RE, `/run/media/dipa/android/ios-sweet-work/iomfb-match.md`):** the framework never matches on "AppleCLCD"; any registered IOMobileFramebuffer subclass works. `iomfb_match_callback` reads only `dfr`/`AppleTV`/`external` (CFBoolean, service itself, no parents); internal main display = all absent/false (type 0, name "primary"). Display count = /arm-io children whose device_type starts with "display-subsystem" (count 0 -> CreateDisplayList returns NULL; more nodes than services -> 30 s wait). IOMobileFramebufferOpen fails only on IOServiceOpen failure; canvas-width/height read as 4-byte CFData from the IOService-plane parent (optional). CopyProperty = IORegistryEntrySearchCFProperty on the service only. Patch 0046 (disp0 node, `external`=false, AppleCLCD : IOMobileFramebuffer) fits all of this.
- **IOMobileFramebuffer swap + notification ABI (2026-10-17, offline).** Swap record = fb+0x18, **0x46c bytes**, zeroed by SwapBegin and sent whole by `kern_SwapEnd` = IOConnectCallStructMethod(sel 5, rec, 0x46c, no output). **SwapBegin** = sel 4, no input, 1 scalar out = swap id (stored at rec+0x50). `kern_SwapSetLayer(fb, layer<4, IOSurfaceRef, CGRect a, CGRect b, flags)`: rec+0x54+4*layer = **IOSurface id**; rec+0x104 bit layer = layer enabled (rec+0x108 bit cleared); rect a (int x,y,w,h, scaled) at rec+0x64+16*layer, rect b at rec+0xc4+16*layer; rec+0x114+4*layer = transform from flags&0xf; flag bits 5/31/6/7/8/9 set bytes rec+0x2ca/0x2cc/0x2e3/0x2e5/0x2e6/0x467+layer. A NULL surface only sets the enable bit with zero id. SwapWait = sel 6 scalars [swap id, timeout, 0].
  - **Notifications**: `IOMobileFramebufferScheduleWithDispatchQueue`/`GetRunLoopSource` create an IONotificationPort and `IOConnectSetNotificationPort(conn, type, port, 0)` (kernel `registerNotificationPort`). `kern_EnableNotifications(fb, type, cb, ctx)` = **sel 72 scalars [NotifyCallbackFuncs[type], fb, type, 0]** -> the kernel keeps an async reference {port, func, refcon=fb} per type and fires it with `sendAsyncResult64`. Types: 0 HotPlug, 1 Power, 3 FrameInfo (args[0] = mask of 31-bit keys, args[1] u32, then values), 4 CRC, **5 Vsync**: 6 args, each a 32-bit half in a u64 slot: (ts lo, ts hi), (t2 lo, hi) passed through the time-ingest helper, (t3 lo, hi); the framework then calls the client's vsync callback(fb, ts, t2', t3, ctx). Vsync callbacks are dropped while the notification port has queued messages.

- **IOSurface.framework user-client ABI reversed (2026-10-17, offline, step 2 of the GUI plan).** `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image IOSurface` (selector scan script: scratchpad `selscan.py`).
  - Connect (`_iosConnectInitalize`, pthread_once): `IOServiceGetMatchingService(IOServiceNameMatching("IOCoreSurfaceRoot"))`, retried with sleep(1) up to 241 times (a missing service stalls every client ~4 min, no crash); `IOServiceOpen(type 0)`; then **sel 13** (no inputs, struct out 0x18 bytes = `_ioSurfaceLimits`) and requires u16 at out+0x16 == 1 (ABI version); out+0 = offset/plane-base alignment mask, out+4 = bytes-per-row alignment mask (used as (x+m)&~m), +0..+0x14 also copied into IOSurface remote-method init, otherwise logs and closes the connection.
  - **Create = sel 0**: scalar in [parent id or 0], struct in = `IOCFSerialize(props, kIOCFSerializeToBinary)` (OSUnserializeBinary format; keys IOSurfaceWidth/Height/BytesPerRow/BytesPerElement/PixelFormat/AllocSize/PlaneInfo/CacheMode/IsGlobal/...), struct out **0xa68 bytes** ("lock result"). **Lookup = sel 4**: scalar in [id], same struct out. LookupFromMachPort = sel 0x22 (scalar in [port name]); CreateMachPort = sel 0x23 (scalar in [id, options], scalar out [port name]).
  - Lock result (copied to client+0x68, size 0x68 + planes*0x80, min 0xe8): 0x00 u64 base address **mapped in the caller's task**; 0x08 u64 task VA of a per-surface shared state page (+0 u64 registry id, +8/+0xa u16 bound accel ids, +0xc u32 seed, +0x14 u8 tiled, +0x20 u32 value generation, +0x24 YCbCr matrix, +0x28 u32 non-bulk values size, +0x2d u8 displayable, +0x2e u8 sysmem-only, +0x30 0x70 bytes bulk attachments); 0x10 u64 task VA of timestamp page (4 u64 indexed timestamps, +0x20 detach code); 0x18 u32 surface id; 0x1c u32 alloc size; 0x20 width; 0x24 height; 0x28 bytes per row; 0x2c buffer offset; 0x30 pixel format; 0x34 u32 (dcache flush length); 0x38 plane count; 0x40 u16 bytes/element; 0x42 u8 element width; 0x43 u8 element height; 0x44 cache mode; 0x4c u8 subsampling; 0x4d u8 prohibit-use count; 0x50 parent id; 0x54 slice count; 0x58 u64 trace id; 0x60 u64 protection options; planes[n] at 0x68+n*0x80 (+0 width, +4 height, +8 bytes/row, +0xc offset, +0x14 size, +0x18 u16 bpe, +0x1a/+0x1b u8 element w/h, +0x1c u8 component count, +0x1d address format, +0x54 u8 compression type (non-zero -> no CPU base address)).
  - **Traps** (IOConnectTrapN -> `IOUserClient::getTargetAndTrapForIndex`): 0 IncrementUseCount(id, category), 1 DecrementUseCount(id, category), 2 **Lock**(id, options, &seed_out), 3 **Unlock**(id, options, &seed_out), 4 Release(id), 5 Release after a failed create/lookup setup (id).
  - Other selectors: 5 SetYCbCrMatrix, 6 WrapClientImage, 7 WrapClientMemory, 9 SetValue (serialized), 0xa UpdateNonBulkValueCache (struct in 9), 0xb RemoveValue, 0xc BindAccel, 0x11 SetSurfaceNotify (async), 0x12 RemoveSurfaceNotify, 0x13 Log, 0x14 SetPurgeable, 0x15 SetOwnership, 0x16 SetTiled, 0x18 SetTimestamp, 0x19 GetTileFormat, 0x1a CopyDataValueBytes, 0x1b SetBulkAttachments (struct 0x88), 0x1e/0x2e-0x31 (via outlined helpers), 0x1f SetCompressedTileDataRegionMemoryUsed, 0x20 GetGraphicsCommPageAddress, 0x21 SetIndexedTimestamp, 0x24-0x26/0x2d IOSurfaceAccelerator, 0x27-0x29 shared events, 0x2a SignalEvent, 0x2b Set/InitDetachModeCode, 0x2c SetOwnershipIdentity, 0x32-0x34 data properties.
  - => SWEET kernel service: class/name **IOCoreSurfaceRoot** + IOSurfaceRootUserClient; minimum = sel 13, 0, 4, 9/0xa/0xb (values), traps 0-5, 0x22/0x23 later for cross-process surfaces (CA sends surfaces to backboardd by mach port). Memory: IOBufferMemoryDescriptor per surface, mapped into each task with createMappingInTask; ids from a global table.

- **Image v8: daemon logs on the console.** `tools/patch-launchd-plist.py IN OUT LABEL...` rewrites launchd.plist (binary, plistlib): renames every `_PanicOnCrash` to `_PanicOnCrasX` and gives the listed jobs `StandardOutPath`/`StandardErrorPath` `/dev/console` (devfs console is 0622, writable by mobile) plus `OS_ACTIVITY_DT_MODE=YES` (os_log mirrored to stderr) and `CFLOG_FORCE_STDERR=1`. v8 = v7 + that plist for com.apple.backboardd and com.apple.SpringBoard, written through the mount (796310 bytes, root:80 0644), SHA256 in `ios16-root-20H392-v8.img.sha256`, `.simg` ready; boot with `shim/out/shim-boot-0045n.img`. Goal: see backboardd's uncaught exception text and the window server's display probing. ODDITY (unresolved): the v5 raw-image rename at offset 0x1e025f000 is present in the v5-v7 image bytes, but the plist read through a Linux mount of v7 still had the original `_PanicOnCrash` keys; filefrag shows the file as one extent. Never patch file contents through raw offsets again; write through the mount.
- **IOMobileFramebuffer.framework reversed (step 1 of the GUI plan).** `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image IOMobileFramebuffer`.
  - Display discovery (`IOMobileFramebufferCreateDisplayList` -> `getDisplayListNumber`): iterates children of `IODeviceTree:/arm-io`, counts nodes whose `device_type` is "display-subsystem" or "ext-display-subsystem" (or `compatible` "paravirtualizedgraphics,gpu"); then `iomfb_populate_display_infos` adds an IOServiceAddMatchingNotification(IOServiceFirstMatch, **IOServiceMatching("IOMobileFramebuffer")**) and runs the run loop up to 30 s until that many services matched. `iomfb_match_callback` reads service properties `dfr`, `AppleTV`, `external` (CFBoolean) and names displays (external ones "%s-%d").
  - `IOMobileFramebufferOpen(service, task, type, &fb)`: `__ioMobileFramebufferAlloc` (CFPreferences com.apple.iokit.IOMobileGraphicsFamily: canvas_width/height, override_display_width/height, override_panel_width/height, benchmark, enable_ktrace), `IOServiceOpen(service, task, type)` (GetMainDisplay passes type 0), `getEDTProperty` reads `canvas-width`/`canvas-height` from the service's IODeviceTree parent, then fills a table of `kern_*` function pointers.
  - User client selectors (`kern_*` -> IOConnectCall*): 3 _kern_GetLayerDefaultSurface[ScalarMethod_stub]; 4 _kern_SwapBegin[ScalarMethod_stub]; 5 _kern_SwapEnd[StructMethod_stub]; 6 _kern_SwapWaitWithTimeout[ScalarMethod_stub] _kern_SwapWait[ScalarMethod_stub]; 7 _kern_GetID[ScalarMethod_stub]; 8 _kern_GetDisplaySize[ScalarMethod_stub]; 10 _kern_SetTVOutMode[ScalarMethod_stub]; 11 _kern_SetWSSInfo[ScalarMethod_stub]; 12 _kern_RequestPowerChange[ScalarMethod_stub]; 13 _kern_EnableStatistics[ScalarMethod_stub]; 14 _kern_SetFlags[ScalarMethod_stub]; 15 _kern_SetDebugFlags[ScalarMethod_stub]; 16 _kern_SetTVOutSignalType[ScalarMethod_stub]; 17 _kern_SetGammaTable[StructMethod_stub]; 18 _IOMobileFramebufferIsMainDisplay[ScalarMethod_stub]; 19 _kern_SetWhiteOnBlackMode[ScalarMethod_stub]; 20 _kern_SwapSignal[ScalarMethod_stub]; 22 _kern_SetDisplayDevice[ScalarMethod_stub]; 23 _kern_SetDigitalOutMode[ScalarMethod_stub]; 24 _kern_GetHDCPDownstreamState[StructMethod_stub]; 25 _kern_GetDigitalOutState[ScalarMethod_stub]; 26 _kern_printDisplayRegs[ScalarMethod_stub]; 27 _kern_GetGammaTable[StructMethod_stub]; 28 _kern_GetDotPitch[ScalarMethod_stub]; 29 _kern_GetDisplayArea[StructMethod_stub]; 30 _kern_EnableDisableDithering[ScalarMethod_stub]; 31 _kern_SetUnderrunColor[ScalarMethod_stub]; 33 _kern_EnableDisableVideoPowerSavings[ScalarMethod_stub]; 34 _kern_SetVideoDACGain[ScalarMethod_stub]; 35 _kern_SetLine21Data[ScalarMethod_stub]; 41 _IOMobileFramebufferEnableMirroring[ScalarMethod_stub]; 42 _IOMobileFrameBufferGetMirroringCapability[StructMethod_stub]; 43 _IOMobileFramebufferSetRenderingAngle[StructMethod_stub]; 44 _IOMobileFramebufferSetMirrorContentRegion[StructMethod_stub]; 47 _kern_HDCPSendRequest[ScalarMethod_stub]; 48 _kern_HDCPGetReply[ScalarMethod_stub]; 49 _kern_SurfaceIsReplaceable[ScalarMethod_stub]; 50 _kern_SetBrightnessCorrection[ScalarMethod_stub]; 51 _kern_SetColorRemapMode[ScalarMethod_stub]; 52 _kern_SwapCancel[ScalarMethod_stub]; 53 _IOMobileFramebufferSetCanvasSize[ScalarMethod_stub]; 54 _IOMobileFramebufferGetMatrix[Method_stub]; 55 _IOMobileFramebufferSetMatrix[Method_stub]; 56 _IOMobileFramebufferKernelTests[StructMethod_stub]; 57 _kern_GetColorRemapMode[ScalarMethod_stub]; 66 _kern_SPLCSetBrightness[ScalarMethod_stub]; 67 _kern_SPLCGetBrightness[ScalarMethod_stub]; 68 _kern_SetParameter[Method_stub]; 69 _kern_SwapSetColorMatrix[StructMethod_stub]; 72 _kern_DisableNotifications[ScalarMethod_stub] _kern_EnableNotifications[ScalarMethod_stub]; 73 _kern_ChangeFrameInfo[ScalarMethod_stub]; 74 _kern_SupportedFrameInfo[Method_stub]; 75 _kern_FactoryPortal[StructMethod_stub]; 77 _kern_GetCurrentAbsoluteTime[ScalarMethod_stub]; 78 _kern_SetBlock[Method_stub]; 79 _kern_GetBlock[Method_stub]; 80 _kern_GetLinkQuality[ScalarMethod_stub]; 81 _kern_SwapCancelAll[ScalarMethod_stub]; 82 _kern_GetProtectionOptions[ScalarMethod_stub]; 83 _kern_CopyLayerDisplayedSurface[ScalarMethod_stub]; 84 _kern_SetContrast[StructMethod_stub]; 85 _kern_GetBufBlock[Method_stub]; 86 _IOMFBGainEncoderFinishEncoding[Method_stub]; UNKNOWN {}
  - => Kernel needs: an `/arm-io` child node with device_type "display-subsystem" (+ canvas-width/height) and an IOService of class **IOMobileFramebuffer** (subclass name match) attached under it, opened with type 0, implementing at least GetDisplaySize(8), IsMainDisplay(18), GetID(7), GetLayerDefaultSurface(3), SwapBegin(4)/SwapEnd(5 struct)/SwapWait(6), Enable/DisableNotifications(72), frame info(73/74), CopyLayerDisplayedSurface(83), plus IOSurface for the swapped buffers. NEXT: CoreAnimation's AppleDisplay/IOMFBDisplay usage of these (constructor, first swap, vsync), then IOSurface.framework's IOSurfaceRoot selectors.
- **GUI PLAN (decided 2026-10-16): CPU rendering + kernel IOMobileFramebuffer.** User: CPU rendering is fine for now (goal = prove the GUI runs), may later research an Apple-style GPU driver for the Adreno 618 -> keep display output and renderer separable. QuartzCore findings (symbols from the cache's .symbols subcache: `ipsw dyld symaddr research/dsc/dyld_shared_cache_arm64 --image QuartzCore`; strings: `ipsw dyld macho ... QuartzCore --strings`):
  - Renderers: `sw_new_context` (CA::OGL::SWContext, full CPU renderer incl. blur, images, IOSurface-backed surfaces, make_buffer_current(WindowServer::Surface)), `gles_new_context`, `metal_new_context`, `new_null_context`. Env knobs include CA_ENABLE_OGL, CA_DISPLAY_TYPE, CA_FORCE_LOCAL_SERVER, CA_FORCE_TIMER, CA_CANVAS_WIDTH/HEIGHT, CA_MAIN_DISPLAY_SCALE/ORIENTATION, CA_DISABLE_RENDER, CA_ALWAYS_RENDER (selection logic not traced yet).
  - `-[CAWindowServer _detectDisplays]` (0x1884e3150) iterates static tables `open_funcs`/`count_funcs` = AppleCLCDDisplay, AppleRGBOutDisplay, AppleWirelessDisplay only; each `count()` = `display_count_of_type(IOMFBDisplayType)` over **`IOMobileFramebufferCreateDisplayList()`**, `open(i)` = `create_display_of_type` -> `CA::WindowServer::AppleDisplay(CFString name, ..., IOMFBDisplayType)` (an IOMFBDisplay driven by IOMFBServer: vsync_callback, frame_info_callback, swaps). `CA::WindowServer::VirtualDisplay` exists but is never auto-detected (explicit API only). => the main display MUST come from an IOMobileFramebuffer kernel service.
  - NEXT: reverse IOMobileFramebuffer.framework: IOMobileFramebufferCreateDisplayList / IOMobileFramebufferOpen (service matching, display type property), the user-client selectors used by IOMFBServer (display size/modes, swap begin/set-layer/end with IOSurface ids, vsync notifications), then the IOSurface kernel side (IOSurfaceRoot user client: create/lookup/lock, memory mapping) that both IOMFB swaps and CA surfaces need. Kernel: SWEET IOMobileFramebuffer service that copies the swapped IOSurface to the 1080x2400 framebuffer at 0x9c000000.
- **logd fixed; backboardd = DISPLAY WALL (boot 0045n on v7, 21:08:57 UTC, frames VID_20261016_230850 00:55-01:28, slide 0x4c3ec000, `research/crash-0045n-v7.txt`).** No `CRASH logd` any more; new daemons run (runningboardd, WirelessRadioManagerd, networkserviceproxy, dasd, cloudpaird, magicswitchd, atc, askpermissiond, ManagedSettingsAgent, containermanagerd uses AKS 0/17). New: locationd sig 11 at CFRunLoopAddSource+132 (NULL source) from its main+0x2af138 in a dispatch_once. **backboardd** sig 6: abort <- std::terminate <- _objc_terminate <- dispatch_once <- main+0x9334 = the "start %{public}@..." wrapper (0x100009264) for **"window server"** (block 0x10000a770 -> dispatch_once body 0x10001d7f0 = StartWindowServer): MTLSetShaderCachePath, `[CAWindowServer serverWithOptions:@{kCAWindowServerDisableUpdatesOnMainDisplay: @YES}]`, `setRendererFlags:`, **`mainDisplay`** -> `displayId` -> `[CADisplay displayWithDisplayId:]`, setWindowServerDisplay:, bounds, pointScale, currentMode, preferredScale, nativeOrientation, touchScales... With no display, mainDisplay is nil and it throws. (HID system and GS start fine before it.) SpringBoard dies on the same missing display (FBSDisplayMonitor). QuartzCore display backends (from the cache's .symbols subcache, `ipsw dyld str`): `CA::WindowServer::AppleCLCDDisplay` (IOMobileFramebuffer hardware) and **`CA::WindowServer::VirtualDisplay`** (open(), new_server, clone_update). `CA_DISPLAY_TYPE` and `CA_FORCE_LOCAL_SERVER` strings exist in QuartzCore but have no direct xref (likely read via a table of CA_* env names). NEXT: find how CA::WindowServer::Server enumerates displays (IOMobileFramebuffer services vs VirtualDisplay / CA_DISPLAY_TYPE) and choose: (a) kernel IOMobileFramebuffer service + IOSurface, or (b) a VirtualDisplay rendered by CA's CPU path (CA::OGL::SW) and copied to the framebuffer.
- **watchdogd + CommCenter + identityservicesd fixed (boot 0045n on v6, 20:41:30 UTC, frames VID_20261016_224133 00:39-01:13, slide 0x20fec000).** `SWEET WDT: watchdogd sel 0 in 0/0 out 1/0 -> ok`, no watchdogd/CommCenter/identityservicesd crashes (CommCenter/identityservicesd now call AKS 0/17/7). usermanagerd boot task runs (UMD_INIT creates primary session uid 501 "mobile", personas 99 System and 199 Default registered with the kernel); `Failed to atomically swap writing file /private/var//keybags/usersession.kb: Operation not supported (45)` (HFS lacks the atomic swap rename; non-fatal so far). Remaining: SpringBoard (FBSDisplayMonitor, no display), backboardd (uncaught exception), mediaserverd, lockdownd (crash inside obfuscated code, main+0x4c1b4?), logd. **logd**: main+0x18160 = `BUG IN LIBTRACE: Failed to migrate directory` from 0x10001801c(dir 0): 0x100016538 requires the dir to exist with uid/gid/mode from the table at 0x10002df14 (0: /private/var/db/diagnostics 272:272 0751, 1: /private/var/db/uuidtext 272:272 0755, 2: /private/var/db/diagnostics/timesync 272:272 0755) plus a `.migrated` file, else XPC "operation 6" to a helper and crash. **Image v7** = v6 + those dirs/markers (also in mkiosroot.sh), SHA256 in `ios16-root-20H392-v7.img.sha256`, `.simg` ready. Boot with `shim/out/shim-boot-0045n.img`.
- **Exit-reason text works (boot 0044n, frames VID_20261016_221726 00:32-00:53, slide 0x22d5c000).** CommCenter/identityservicesd: `couldn't dlopen libobjc-trampolines.dylib: dlopen(/usr/lib/libobjc-trampolines.dylib, 0x0106): tried: '/usr/lib/libobjc-trampolines.dylib' (no such file, not in dyld cache)`: the file only exists in the OS cryptex and dyld does not search cryptexes at ignition_level=1. 19 cryptex files have no root counterpart (OS: DriverKit dyld cache + .symbols, VisualTestKit, libffi-trampolines, libobjc-trampolines, libstdc++ 6.0.9 + 2 symlinks; App: SafariSupport.bundle, AuthenticationServicesAgent, com.apple.Safari.History, passwordbreachd, safarifetcherd, webbookmarksd, webinspectord, webpushd) -> hard-linked (symlinks copied: Linux hfsplus cannot hard-link symlinks); `tools/mkiosroot.sh` does it generically. watchdogd still crashed: the `-wdt_no_pmu` / `/arm-io/wdt no-pmu` check (0x10000a01c) only runs when os_variant_has_internal_diagnostics; otherwise 0x100009b18 looks up IOServiceMatching("IOService") + IOPropertyMatch {IOPMUPrimary: 1} (NSConstantDictionary) and crashes if absent, then IORegistryEntrySetCFProperty(boot stage 0xff) (failure only logged). Patch **0045**: IOWatchdog sets IOPMUPrimary = 1 and accepts setProperties; CI `38961814194` -> `xnu/out-0045`. **Image v6** = v5 + the 19 cryptex links, SHA256 7c610c6a...297a, `ios16-root-20H392-v6.simg` (full flash needed). Boot image `shim/out/shim-boot-0045n.img` (0045 + sweet-0044hi.adt). Still open: SpringBoard (no display), backboardd (uncaught exception, reason none), mediaserverd (Fig NULL dict), logd (main+0x18160), lockdownd (main+0x4c1b4).
- **System survives daemon crashes (boot 0043p, video frames VID_20261016_215006 00:25/00:42/00:54).** With the v5 plist patch no panic: launchd keeps launching (runningboardd, powerd, tccd, healthd, peopled, cryptexd, routined, aksd, mediaremoted, familynotificationd, nanoprefsyncd, navd, cloudpaird, passd, amsaccountsd, accessoryupdaterd, wcd ...). Shared cache slide that boot 0x406b4000 (`research/crash-0043p.txt`). watchdogd still crashed at main+0xb82c from the PMU step: `-wdt_no_pmu` is only honored when os_variant_has_internal_diagnostics; customer builds read `no-pmu` from IODeviceTree:/arm-io/wdt (IORegistryEntrySearchCFProperty) -> mkadt adds /arm-io/wdt {no-pmu}. **cryptexd** sig 6: abort_with_payload <- os_crash_fmt <- `__darwin_arm_secure_boot_chip.cold.7` ("panic: failed to get crypto algorithm") <- `_img4_chip_select_personalized_ap`: reads /chosen use-ddi-secure-boot, allow-ecid-mismatch, crypto-hash-method ("sha1" | "sha2-384"), /chosen/asmb lp-smb0/1 -> mkadt adds crypto-hash-method "sha2-384". **identityservicesd** sig 6 = same `_objc_fatal` in imp_implementationWithBlock as CommCenter (block trampolines; message needed). lockdownd sig 5 at main+0x4c1b4. Patch **0044**: crash report adds `CRASH name reason ns N code X: text` (exit reason description = abort_with_payload text). CI `38959096811` -> `xnu/out-0044`, QEMU OK. Image `shim/out/shim-boot-0044n.img` = 0044 + `shim/out/sweet-0044hi.adt` (wdt no-pmu, crypto-hash-method) + cmdline (wdt=-1, no -wdt_no_pmu).
- **First symbolicated daemon crashes (boot 0043u on journaled v4, 19:38:53 UTC; video frame chat image 36; transcribed in `research/crash-0043u.txt`; shared cache slide 0x40d60000 for every process).** (Gemini's video transcription invented values, use frames only.) `tools/sweet-crash.py research/dsc/dyld_shared_cache_arm64 x research/crash-0043u.txt`:
  - **watchdogd** pc main+0xb82c (`_os_crash` trap helper) from 0x100009bb0 = set PMU boot stage via IORegistry (no PMU) -> fix: boot-args `wdt=-1 -wdt_no_pmu` (Apple's own test mode writes "%s wdt=-1 -wdt_no_pmu"; watchdogd logs "skipping setting PMU boot stage because -wdt_no_pmu found in boot-args or no-pmu found in EDT"). Kernel effect of wdt=-1: sched hygiene debug off, zone_exhausted_timeout -1 (harmless).
  - **SpringBoard** sig 5 in `-[FBSDisplayMonitor _initWithBookendObserver:transformer:]+1160` <- `+[FBDisplayManager sharedInstance]` <- `FBSystemShellInitialize` <- `SBSystemAppMain`: no main display. GUI WALL: display service (IOMobileFramebuffer / CoreAnimation display).
  - **backboardd** sig 6: abort <- std::terminate <- _objc_terminate (uncaught exception; message not shown).
  - **CommCenter** sig 6: `_objc_fatal` in `imp_implementationWithBlock` (from `+[_PFRoutines initialize]`, CoreData): objc block trampolines cannot be allocated -> likely kernel gap (trampoline page remap); will hit many processes.
  - **mediaserverd** sig 11: CFDictionaryGetValue(NULL) in FigNotificationListenerStartNotifications (routing session manager).
  - **logd** sig 5 at its main+0x18160 (bt main+0x9dfc); lockdownd sig 5 (not yet symbolicated).
  - Image v5 = v4 + launchd.plist (`/System/Library/xpc/launchd.plist`, contiguous at image offset 0x1e025f000, 1456980 bytes) with the 7 `_PanicOnCrash` keys renamed `_PanicOnCrasX` in place (raw image patch, no metadata change) -> `diff-v4-v5.simg` = 7 blocks; v5 SHA256 78f96974...185a. Boot image `shim/out/shim-boot-0043p.img` = 0043 + `wdt=-1 -wdt_no_pmu`.
- **0043 console crash reports (QEMU verified); image `shim/out/shim-boot-0043u.img`; NEXT: flash v4 + boot 0043u.** Boot 0042u (video photo IMG_20261016_211646): short exec lines work; watchdogd crashes with NO `SWEET WDT:` line (fails before its first IOWatchdog call: lookup or IOServiceOpen, or elsewhere); lockdownd, SpringBoard, mediaserverd, CommCenter, identityservicesd, backboardd, watchdogd all crash repeatedly ("Too many corpses being created" = corpse limit, no crash reports). AKS callers: lockdownd (0, 7), imagent/sleepd (0, 17, 7), backboardd (0, 17), UserEventAgent (0, 7, 102, 103 -> unsupported). Patch **0043**: `sweet_crash_log` (osfmk/kern/exception.c, called from proc_prepareexit for crash exits on the current proc) prints `CRASH name[pid] sig S code (exc<<32|code) sub X slide SR mh MH`, `CRASH name pc lr sp fp far`, `CRASH name bt` (10 fp frames); AKS sel 103 notify_state_is_set -> 0. CI `38954520419` -> `xnu/out-0043`. QEMU test: init forks, child `brk #1`: `CRASH launchd[2] sig 5 code 0x600000001 sub 0x1000004f0 slide 0x0`, pc correct, parent keeps running (pid 1 crashes panic before proc_prepareexit, so test with a child). `tools/sweet-crash.py CACHE ROOT [report]` symbolicates typed-in CRASH lines (`ipsw dyld a2s` with addr - slide; main binary offsets = addr - mh + 0x100000000).
- **v3 reflashed 18:50-18:55 UTC (`research/flash-userdata-v3b.log`, 24/24 OKAY); 0042u booted 19:01:17 UTC on the clean disk (`research/boot0042u-2.log`), SLOW MO VID pending (watchdogd failure reason).** ABL hangs on the first `fastboot boot` after every big flash; user re-enters fastboot. User gave standing approval to reflash/boot without asking (memory standing-flash-approval). Commits now end with `Co-Authored-By: dipa-studio <183933817+dipa-studio@users.noreply.github.com>` (user request; never a Claude trailer).
  - watchdogd flow: connect_to_kext (0x100005408): IOServiceGetMatchingService("IOWatchdog") fails -> "failed to discover" + _os_crash; IOServiceOpen(type 1) fails -> "IOServiceOpen failed with error : 0x%x" + _os_crash. Then sel 0 (out 1 scalar): 0 -> "userspace monitoring disabled", 0x100009bb0, sleep 2, exit(0); nonzero -> "userspace monitoring enabled", normal operation.
  - **Image v4 (JOURNALED):** `tools/mkiosroot.sh` now does `mkfs.hfsplus -J`, mounts with `-o loop,force`, adds the /System/Library/Caches/com.apple.dyld hard links (44) and /private/var/keybags/systembag.kb (0700/0600 root). Built from the IPSW dmgs (OS 087-86698-044, SystemOS 087-86593-047, AppOS 087-86715-047) -> `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v4.img` SHA256 fba4aeae...ec0f9 + `.simg`. Header: attr 0x80002100 (unmounted, journaled), journal info block 129, journal 8 MiB at 532480 flagged need-init. Linux `fsck.hfsplus -n` reports "Volume header needs minor repair" on any fresh journaled volume even after -y (quirk). QEMU: 64 MB journaled test root (`rd=md0 rootrw=1`, 0042 kernel): `hfs: Initializing the journal (joffset 0x3000 sz 0x80000)` -> mounted -> init runs, no panic. NEXT: flash v4 (full), boot 0042u.
- **SPRINGBOARD STARTS (boot 0041u 18:39:53 UTC, photo IMG_20261016_204142).** backboardd, bluetoothd, fairplayd.H2, SpringBoard (pid 111, crashed: "Too many corpses"), xpcproxy run; `SWEET AKS: backboardd sel 0 -> 0`, `sel 17 in 1/0 out 0/4096 -> 0`. Panic: watchdogd[113] exited, namespace 2 subcode 5 (SIGTRAP = its _os_crash): watchdogd crashes on purpose when IOServiceGetMatchingService("IOWatchdog") fails ("connect_to_kext() unexpectedly failed") or IOServiceOpen(type 1) fails ("IOServiceOpen failed with error"); IOWatchdog DOES register (QEMU msgbuf: `SWEET WDT: IOWatchdog registered`), cause not on screen yet -> need video. Note `wdt_test=no_user_checkin` makes watchdogd log "detected testing boot-args to not run, exiting" (path not reached here?). **HFS CORRUPTION:** `hfs_swap_BTNode: offset #0 invalid (0xBC1D) (blockSize 0x2000 numRecords 81)`, `node=19677 fileID=4` (catalog), `hfs_mark_inconsistent` repeated. Likely cause: non-journaled HFS + unclean panics while writing (0038e wrote a 2.7 GB core then panicked; every boot since ends in panic). Plan: reflash v3 (clean), longer term HFS journaling. Patch **0042**: one short `exec NAME` console line instead of the 3-line "Allowing spawn of iOS binary" notice; CI `38949451276` -> `xnu/out-0042`; image `shim/out/shim-boot-0042u.img` (same cmdline as 0041u).
- **LAUNCHD DAEMONS RUN (boot 0039u, 18:29:13 UTC, photo IMG_20261016_203052).** With `launchd_unsecure_cache=1` all boot tasks pass and launchd starts LaunchDaemons (pids > 100: identityservicesd 114 and lockdownd 106 crash, "Too many corpses being created"). Fatal: `watchdogd: ERROR: failed to discover watchdog KEXT service` -> exit (namespace 2 = signal, subcode 5) -> `_PanicOnCrash` panic. watchdogd: IOServiceMatching("IOWatchdog"), IOServiceOpen type 1, IOConnectCallScalarMethod sel 0/1 (check in)/3/4 (disable/enable userspace monitoring)/5, IOConnectCallStructMethod sel 2 (1 KiB in) and 9 (small out); VM path ("detected virtual machine environment and no watchdog KEXT found, exiting...") only when it detects a VM. Console also flooded with `hfs: set hardlink bit on vol=iOSRoot cnid=321318` (Linux-made hard links lack kHFSHasLinkChainBit; repaired only in memory on each lookup). Patches **0040** (`iokit/Kernel/arm/SweetWatchdog.cpp`: IOWatchdog + IOWatchdogUserClient, all selectors succeed with zeroed outputs, each logged once as `SWEET WDT: ...`) and **0041** (sweet_hfs hfs_catalog.c: the three link-repair printfs limited to 8 per boot); CI `38948245372` PASSED -> `xnu/out-0041` (QEMU regression OK). Image `shim/out/shim-boot-0041u.img` (0041 + sweet-0038hi.adt + ufsrw rootrw + launchd_unsecure_cache=1) booted 18:39:53 UTC (`research/boot0041u.log`), photo pending.
- **v3 FLASHED + keybag passes; next wall AMFI (launchd_cache_loader).** User said "flash, nothing to lose": `fastboot -S 512M flash userdata ios16-root-20H392-v3.simg` 17:51:52-17:57:01 UTC, 24/24 chunks OKAY (`research/flash-userdata-v3.log`). userdata = v3 (SHA256 fa84274c...22df) until the next rw boot. ABL fastboot then hung ("Sending" forever, `reboot bootloader` timed out) until the user re-entered fastboot by hand (common Xiaomi ABL crash). Boot 0038e 18:06:15 UTC (`research/boot0038e-3.log`), photos IMG_20261016_200812/200838: keybag OK, then boot tasks tzinit (`Bad zoneinfo link`, resets to system partition, OK), finish-restore, finish-demo-restore, sysstatuscheck, prng_seedctl (`failed to load kernel prng seed`, `failed to load virtual random (-147)`, AllowCrash), auearlyboot, then **launchd_cache_loader: `abort: Unable to find AMFI`** -> 2.7 GB core written to /cores in 91 s -> launchd panic `launchd_cache_loader[22] exited -- exit reason namespace 7 subcode 0x1`. launchd_cache_loader: SecStaticCodeCheckValidity of /System/Library/xpc/launchd.plist with detached .sig, then IOServiceMatching("AppleMobileFileIntegrity") + IOServiceOpen type 0 + IOConnectCallMethod sel 6 (1 scalar = 1, struct in = cdhash) = trust the cdhash, then sends the cache to launchd. Boot-arg `launchd_unsecure_cache=1` skips signature + AMFI ("Using unsecure cache"); the value is parsed with strtoul base 10 (helper 0x100002da8), so a path = 0 = off: boot 0039w (18:17:13 UTC, `=/System/Library/xpc/launchd.plist`, photo IMG_20261016_202008) still aborted `Unable to find AMFI` (core dump now skipped: `Failed to generate core file ... error 14`, so 0039 works). Image `shim/out/shim-boot-0039u.img` uses `launchd_unsecure_cache=1`. Patch **0039**: do_coredump = 0 on SWEET (kern.coredump sysctl still works); CI `38945267341` -> `xnu/out-0039` (_do_coredump now in __common). Image `shim/out/shim-boot-0039w.img` = 0039 + sweet-0038hi.adt + ufsrw rootrw + `launchd_unsecure_cache=/System/Library/xpc/launchd.plist`. TODO later: real AppleMobileFileIntegrity IOService (sel 6 trust cdhash etc.).
- **Image v3 ready, awaiting user "flash".** Boot 0038w 17:38:10 UTC, photo (chat image 30): `SWEET AKS: keybagd sel 0 -> 0x0`, `sel 14 out 1/0 -> 0x0` (x2), `MKB_INIT: mount is with NO CPROTECT ... does not support Data Protection`, `System Keybag loaded`; then keybagd still opens /private/var/keybags/systembag.kb (0x100012d3c, for BackupKeyBagKeys) -> ENOENT, `no-effaceable-storage` not set -> `Can't load the keybag. tears in rain... Time to die` -> `FATAL KEYBAG ERROR: kb_load` -> reboot -> Halt/Restart Timed Out panic. Fix: ADT `/defaults/no-effaceable-storage` (mkadt.py; `shim/out/sweet-0038hi.adt`, `research/q0038-hi.adt`, QEMU OK) + file `/private/var/keybags/systembag.kb` (0600 root, dir 0700; XML plist {KeyBagKeys: data}). **v3 image** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v3.img` = v2 + that file, fsck OK, SHA256 fa84274c...22df; `ios16-root-20H392-v3.simg` (img2simg: zero blocks become FILL chunks, so a full flash overwrites every block the rw boots changed). Flash: `fastboot -S 512M flash userdata ios16-root-20H392-v3.simg`, then boot `shim/out/shim-boot-0038e.img` (0038 + sweet-0038hi.adt + ufsrw=1 rootrw=1).
- **0038 AppleKeyStore (CI 38938744130 PASSED -> `xnu/out-0038`; QEMU msgbuf: `SWEET AKS: AppleKeyStore registered (no passcode, unlocked)`; phone image `shim/out/shim-boot-0038w.img` booted 17:38:10 UTC, `research/boot0038w.log`, photo pending).** QEMU full kernel log trick (fb.txt is only the last screen): `llvm-nm KERNEL | grep _msgbufp` -> `--hmp "x /1gx ADDR"` gives struct msgbuf address (static, 0xfffffe0007b56678 on 0038) -> `--hmp "x /3gx STRUCT"` gives bufc (3rd quad) -> `--hmp "memsave BUFC 0x20000 \"FILE\""` (quote the file name), `tr -d "\0" < FILE`. Same inputs give the same addresses. Boot 0037w 17:08:35 UTC, photo IMG_20261016_191052: bindfs fixed mount; mount-phase-1/2 pass; `cc_fips_test` boot task: all corecrypto FIPS POST tests PASSED in userspace; then keybag boot task `keybagd --init`: `MKB_INIT: FATAL KEYBAG ERROR: failed to load system bag`, `Could not get options entry from the device tree` (x2, IODeviceTree:/options = NVRAM, non-fatal), `REBOOTING INTO RECOVERY MODE` -> reboot -> panic `Halt/Restart Timed Out @IOPlatformExpert.cpp:884` (no restart path on SWEET).
  - keybagd (static libaks): load_devicebag (0x100012c30) calls aks_get_system (sel 14, 0-1 scalar in, 1 out) and loads /private/var/keybags/systembag.kb only if the result is 0xe00002f0 (NotFound); any other error -> fatal; SUCCESS -> skip the file (userspace-reboot path). systembag.kb is a plist {KeyBagKeys}; decrypted with effaceable storage unless IODeviceTree:/defaults has `no-effaceable-storage`. Image has no /private/var/keybags. has_data_protection: statfs of /private/var; no cprotect on our HFS -> device-bag volume mapping skipped.
  - libaks connection: IORegistryEntryFromPath / IOServiceMatching("AppleKeyStore"), IOServiceOpen type 0, then selector 0 (no args) must succeed.
  - **AppleKeyStore selector map (iOS 16.7 AppleKeyStore.framework, via `ipsw dyld disass`):** 0 open, 2 create_bag, 3 save_bag, 4 unload_bag, 5 set_system_with_passcode, 6 load_bag, 7 get_lock_state (1 in, 1 out; bit 2 = unlocked since boot), 9 unlock_device, 10 wrap_key, 11 unwrap_key, 12 unlock_bag/test_stashed_kek, 13 lock_bag, 14 get_system, 15 change_secret_se, 16 internal_state, 17 get_device_state (1 in, struct out <=4K: DER SET of SEQUENCE{UTF8 key, INTEGER}: ss state, sls lock_state (MKBGetDeviceLockState returns it), sb backoff, sbo, sfa failed attempts, sfao, sgs generation, sas assertions, sgpe grace, srcd countdown, sr reserved), 18 recover_with_escrow_bag, 19 obliterate_class_d, 20 drain_backup_keys, 21/22 set/clear_backup_bag, 23 get_bag_uuid, 24 rewrap_key_for_backup, 26/27 assert_hold/drop, 30/31 set/get_configuration, 33-37 stash, 38 auth_token_create, 40 generation, 41 fdr_hmac_data, 42 verify_password, 43 _aks_operation, 44 remote_session, 49/50 signing keys, 51/53/54 stash enable/persist/escrow, 55 unload_session_bags, 57/58 remote peer, 59-62 smartcard, 63 migrate_s_key, 65 set_keybag_for_volume_with_cookie_persona, 66/67 sync bags, 68 copy_volume_cookie_persona, 69-73 se_*, 74-79/84/85/99 fv_* (FileVault/VEK), 80/81 absinthe, 82 make_public_backup_bag, 83 drop_auxiliary_auth, 86 kext get/set options, 87 invalidate_bag, 88-91/94/95/106/107 se_*, 92 lower_iteration_count, 93 get_internal_info, 96-98/117 keybag_persona create/list/delete, 100/101 assert promote/consume, 102/103 notify_state set/is_set, 104 fairplay, 105 change_secret_epilogue, 108 delete_xart_leak, 110-113 backup volume, 114 sealed_hashes_set, 115 prewarm_sps, 118-128 AKSIdentity*/AKSGetLastUser.
  - Patch **0038**: `iokit/Kernel/arm/SweetKeyStore.cpp` (class AppleKeyStore on IOResources, IOUserClientClass AppleKeyStoreUserClient; personality in KernelConfigTables.cpp): 0/4/5/9/12/13/26/27/55/102 success, 14 -> handle 0, 7 -> 0x4, 17 -> DER state (ss 4, sls 0), others kIOReturnUnsupported; logs `SWEET AKS: <proc> sel N arg0 in a/b out c/d -> ret` for every call.
  - Tools: shared cache copied to `research/dsc/` (git-ignored; ipsw needs a writable dir for its .a2s symbol cache); `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image AppleKeyStore|MobileKeyBag`; scratchpad `annot2.py BIN DIS FIXUPS` annotates llvm-objdump output with strings and import names (`ipsw macho info --fixups`).
- **0037 bindfs (phone boot 0037w pending photo).** Boot 0036mw 16:57:47 UTC, photo IMG_20261016_190102: WRITABLE ROOT WORKS: `/dev/ufsroot0 on / (hfs, local, noatime)` after mount_hfs update (GetMasterBlock EBUSY harmless), coredump of mount written to /cores (rw). Then `mount: failed to mount /private/preboot/5CBE3601.../usr/standalone/firmware -> ...: Operation not supported by device (19)` -> exit 74 -> launchd panic `mount[2] exited`. Cause: the macOS-derived config had nullfs but no bindfs (ENODEV = unknown fs type). Caller passes env 0 -> bind not required, ENOENT (missing source dir) tolerated. Patch **0037** adds `bindfs` to FILESYS_BASE in MASTER.arm64.sweet; CI `38936550483` -> `xnu/out-0037` (bindfs_vfsops present; QEMU probe regression OK). Image `shim/out/shim-boot-0037w.img` (0037 + sweet-0036hi.adt + ufsrw=1 rootrw=1) booted 17:08:35 UTC (`research/boot0037w.log`). NOTE: userdata has now been modified by rw boots; it no longer equals the v2 image, so sparsediff with v2 as OLD is not safe any more (full reflash or a new baseline needed).
- **0036 phone: launchd boot tasks run; mount -P 1 needs /chosen/boot-manifest-hash.** Boot 0036hr 16:15:32 UTC, photo IMG_20261016_185236: platform check passes; fsck boot task runs (`fsck: not booting main or diagnostic OS. Skipping fsck on OS container`); mount-phase-1: `failed to get filesystem info` x2 (no IODeviceTree:/filesystems/fstab, non-fatal), `mount: data volume missing, but not required in env: 0`, mount_hfs update of /: `GetMasterBlock: Error 16 opening /dev/ufsroot0` (EBUSY, mounted block dev, non-fatal) then mount() EROFS (read-only boot) -> `mount: / failed with 1`; then `failed to get boot-manifest-hash` -> errx exit 66 -> launchd panic `mount[3] exited`. /sbin/mount: fn 0x100005f90 reads IODeviceTree:/chosen boot-manifest-hash (hex), bindfs-mounts /private/preboot/<HEX>/usr/standalone/firmware (ENOENT tolerated unless required). `tools/mkadt.py` now adds `boot-manifest-hash` = SHA-384("sweet boot manifest") (5CBE3601...5205). ADTs `shim/out/sweet-0036hi.adt`, `research/q0036-hi.adt` (QEMU probe OK, csops 0x26000001). Image `shim/out/shim-boot-0036mw.img` (0036 + new ADT + ufsrw=1 rootrw=1), booted 16:57:47 UTC (`research/boot0036mw.log`): FIRST WRITABLE BOOT of userdata (restore source: v2 image on SSD).
- **0036 CS_SIGNED (phone boot 0036hr pending photo).** Phone boot 0035hr 2026-10-16 15:57:02 UTC (`research/boot0035hr.log`, photo IMG_20261016_180249): highmem works on hardware; shared cache maps (trust-cache warnings only), Apple launchd runs (`Darwin Bootstrapper Version 7.0.0`, `entering ondemand mode`), starts boot task fsck, then userspace panic `boot task is not a platform binary (fsck, /sbin/fsck)`. launchd+0x3fea0: `csops(pid, CS_OPS_STATUS)` must have bit 0x04000000. Cause: nothing set CS_SIGNED (AMFI does it in vnode_check_signature), so csproc_get_blob() returns NULL for every process and csops never reports CS_PLATFORM_BINARY (also breaks per-process cdhash/entitlement queries). QEMU probe init (`csops` status printer, scratchpad csq/) on 0035: `0x02000001`; patch **0036** (`*cs_flags |= CS_SIGNED` in the SWEET AMFI hook), CI `38929635791` -> `xnu/out-0036`: `0x26000001`. Images `shim/out/shim-boot-0036hr.img` / `-0036hw.img` (same cmdlines as 0035). 0036hr booted 16:15:32 UTC (`research/boot0036hr.log`). Next launchd boot tasks (embedded __config plist): fsck -qL and mount -P 1/2 (RequireSuccess); no /etc/fstab on the image.
- **0035 ENTITLEMENTS + PLATFORM BINARIES (QEMU verified).** `xnu/patches/0035-sweet-amfi-entitlements-platform-binaries.patch`: new `iokit/Kernel/arm/SweetEntitlements.cpp` (OSObject subclass: OSDictionary from OSUnserializeXML of the signature's XML entitlements + original XML for CS_OPS_ENTITLEMENTS_BLOB); `bsd/kern/sweet_amfi.c` answers queryEntitlementBoolean/String(+WithProc, string also matches array members), copyEntitlementAsOSObject(+WithProc, retained), asdict (retained), get_xml (kalloc_data copy); built-in MAC policy "SWEET AMFI" (registered from bsd_init before vfs/exec) with mpo_vnode_check_signature: every signed binary on the MNT_ROOTFS mount gets CS_PLATFORM_BINARY (stand-in for AMFI's static trust cache: iOS system binaries are ad-hoc, cd_flags 0x2, platform byte 0), and attaches entitlements ONLY for the writable copy (cs_blob != csb_ro_addr; revalidation passes the RO blob). LESSON: first version attached in adjustContextWithoutMonitor -> QEMU `unable to adjust OSEntitlements context without monitor: 53` because ubc_cs_convert_to_multilevel_hash (4K-page signatures on 16K kernel) sets csb_entitlements_blob = NULL; ALL iOS 16 binaries (launchd, backboardd, SpringBoard) use 4K code pages, so this would have broken launchd on the phone. Boot-arg `sweet_amfi_debug=1` logs `SWEET AMFI: <ident>: N entitlements (test: ...)`. `tools/mkinit.py OBJ OUT [ENTS.plist]` adds an XML entitlements blob (special slot -5; default output byte-identical). QEMU `research/q0035-ent` (RAM disk `research/root-hfs-ent.img`, init with 3 test entitlements, highmem): `org.sweet.init: 3 entitlements (test: bool 1 string 1 array 1)` then init PID 1. MAC policies loaded: 0034 = 1, 0035 = 2 (QMP `mac_policy_list`). CI `38909807230` -> `xnu/out-0035`. Phone images: `shim/out/shim-boot-0035hr.img` (highmem, ro), `-0035hw.img` (highmem, +ufsrw=1 rootrw=1), `-0035r.img` (low mem fallback).
- **PHONE TEST ORDER (updated):** 0035hr -> if instant reset, 0035r -> then 0035hw.

- **HIGHMEM: XNU in the upper DDR bank, ~3.95 GiB (was 1.2 GiB).** Live FDT memory = <0x80000000 2G> + <0x1_00000000 0xfcc00000>; all fixed reserved-memory carve-outs are in the low bank (highest: ramdump_fb 0xaf000000, rmtfs ~0xfde01000), dynamic pools have alloc-ranges <= 0xffffffff, UFS node has no `iommus` (Linux DMAs anywhere). `tools/mkadt.py --highmem` sets /chosen dram-base 0x100000000 dram-size 0xfcc00000; `tools/mkpayload.py` now takes phys_base/mem_size from the ADT (default payloads byte-identical, verified); `tools/qemu-sweet.py` sizes -m from the payload (8G for highmem). Patch **0034** (`0034-sweet-ufs-dma-above-4g.patch`): UFS refuses DMA memory above 4G without UFSHCI CAP.64AS (bit 24), logs `DMA at 0x...`. CI `38905889883` success -> `xnu/out-0034`. **QEMU verified** (`research/q0034-hi`, ADT `research/q0034-hi.adt` --qemu --highmem, HFS RAM disk): phys_base 0x100000000, init PID 1 heartbeat, no panic; `max_mem` = `mem_size` = 0xfcc00000 read via QMP (`research/q0034-hi-mem`). Phone images: `shim/out/shim-boot-0034hr.img` (read-only) / `-0034hw.img` (+ufsrw=1 rootrw=1), ADT `shim/out/sweet-0034hi.adt` (asmb SIP + sweet-ufs + highmem). PHONE RISK: unknown runtime TZ/XPU protection in the upper bank would show as an instant reset; fall back to 0033r/w. Watchdog ruled out for the overnight reset: msm-watchdog bark is 20 s (qcom,bark-time 0x4e20) yet panic screens stay up for many minutes.

- **Offline research 2026-10-16 (user away, phone unavailable). Images rebuilt** `shim/out/shim-boot-0033r.img` / `-0033w.img` now also carry `wdt_test=no_user_checkin`. NEXT ON PHONE: boot 0033r (expect past in6_nigroup), then 0033w (first writes: rw root fixes HFS link-chain bits itself and gives /var for launchd sockets /var/run/syslog, /var/run/lockdown.sock).
- **launchd.plist** (`/System/Library/xpc/launchd.plist`, compiled; 532 daemons, 66 RunAtLoad/KeepAlive, list in scratchpad `early-daemons.txt`). `_PanicOnCrash` daemons: containermanagerd/usermanagerd (InternalOnly), lockdownd/remoted/trustd/remotepairingdeviced (AutomationOnly), **watchdogd unconditional** (KeepAlive SuccessfulExit=false). watchdogd needs IOKit `IOWatchdog` kext service; if absent it exits only when `kern.hv_vmm_present` (ADT `/defaults/vmm-present`, hvg_sysctl.c) or with boot-arg `wdt_test=no_user_checkin` ("detected testing boot-args to not run, exiting"; reads kern.bootargs). Using the boot-arg (vmm-present would change many daemons; keep as an option).
- **GUI path research (QuartzCore in the shared cache, `ipsw dyld str CACHE STR`, ~10 s/search):** CA::WindowServer has IOMFBServer/IOMFBDisplay (Apple DCP/IOMobileFramebuffer), AppleCLCDDisplay, AppleRGBOutDisplay, **VirtualServer/VirtualDisplay** and **MemorySurface**, EAGLServer. Renderers: CA::OGL::MetalContext, GLContext and a **CPU software rasterizer CA::OGL::SW** (samplers/blend modes; "image is too large for software renderer"). Env knobs: `CA_ENABLE_OGL`, `CA_DISPLAY_TYPE`, `CA_FORCE_LOCAL_SERVER` (249 CA_* vars). Hypothesis (unverified): backboardd's render server could run a VirtualServer/MemorySurface with the SW renderer and we copy the surface to the ABL framebuffer -> needs disassembly of CA::WindowServer server creation. Expected other GUI walls: IOSurface (closed-source kext; needs a reimplementation), IOMobileFramebuffer user client, IOHID touch events, AppleKeyStore/keybag (SEP) for lock state, MobileGestalt answers (AppleCLCD etc.).

- **0032r RESULT (boot 05:07:50 UTC, `research/boot0032r.log`, photo IMG_20261016_071200): SHARED CACHE MAPPED, LAUNCHD RUNS.** With SIP relaxed (ADT asmb) the `not in trust cache` lines are only warnings for every subcache (.31 ... .42.dyldlinkedit); no SIP rejection; libSystem loads; launchd configures networking (`skip attaching fsw to lo0 using legacy TX model`) -> kernel data abort far 0x28 in `SHA1Init` (symbolized as sha1_init) from `in6_nigroup` (IPv6 on lo0): g_crypto_funcs NULL. Kernel addresses are unslid: `~/swift/usr/bin/llvm-symbolizer --obj=KERNEL ADDR` works directly.
- **0032** BearSSL SHA-1 (`0032-sweet-bearssl-sha1.patch`), **0033** BearSSL SHA-384/512 (`0033-sweet-bearssl-sha384-sha512.patch`, BearSSL ctx stored in SHA512_CTX, static-asserted to fit; ubc_subr.c uses SHA-384 for code directories). `0020-stage-bearssl.sh` now also stages hash/sha1.c, hash/sha2big.c, codec/{dec,enc}{32,64}be.c. CI `38854909053` success (0032-only run `38854802073` superseded). Kernel `xnu/out-0033` (SHA1Init -> _br_sha1_init verified by disassembly; nm symbols have a leading underscore). Images (ADT sweet-0032): `shim/out/shim-boot-0033r.img` (read-only), `shim-boot-0033w.img` (+ufsrw=1 rootrw=1). Still NULL g_crypto_funcs users: des, chacha20poly1305, rsa, aesxts, rand, flow_divert.
- `research/check-patch-order.py` now skips patches touching CI-staged sweet_hfs sources (0031) instead of stopping.

- **0031r RESULT (boot 05:03:52 UTC 2026-10-16, `research/boot0031r.log`, photo IMG_20261016_070508): SHARED CACHE FOUND.** dyld now opens `dyld_shared_cache_arm64` (v2 image hard links), kernel refuses to map it: `shared_region: ... map(...'dyld_shared_cache_arm64'): not in trust cache` -> `vnode is not SIP-protected` (vm_unix.c: macOS arm64 path needs trust cache, else root-owned + SF_RESTRICTED unless CSR_ALLOW_UNRESTRICTED_FS) -> `dyld cache '(null)' not loaded: syscall to map cache into shared region failed` -> libSystem not loaded -> coredump to /cores fails error 30 (EROFS) -> panic initproc failed -> "MACH Reboot" (spins; screen kept). Lots of `hfs: set hardlink bit on vol=iOSRoot cnid=... linkid=...` spam (Linux-made hard links lack the link-chain bit; read-only mount cannot persist the fix). FIX: ADT `/chosen/asmb` with `lp-sip0`=0x6f (u64; incl. CSR_ALLOW_UNRESTRICTED_FS) and `lp-sip1`=1 (unauthenticated root), `tools/mkadt.py` -> `shim/out/sweet-0032.adt`. Images with kernel 0031: `shim/out/shim-boot-0032r.img` (read-only) and `shim-boot-0032w.img` (+ufsrw=1 rootrw=1).

- **2026-10-16 morning:** userdata now = **v2** image (`diff-v1-v2.simg` flashed 21:06:50 UTC 2026-10-15, OKAY, `research/flash-userdata-diff-v2.log`); future diffs use `ios16-root-20H392-v2.img` as OLD. Booted `shim-boot-0029k.img` (ignition_level=1) right after (`research/boot0029k-v2.log`); **no photo** (user asleep). Next morning the phone was in PixelOS recovery = some hardware reset (ABL then booted Android, which cannot use userdata). OBSERVATION: our kernel cannot reset the SoC itself (`PE_halt_restart` is never set; reboot/halt print "MACH Reboot"/"CPU halted" and spin), so the reset came from outside XNU: Qualcomm watchdog or a TZ/XPU violation. Unknown which; re-boot 0029k and watch/video until the reset. Do NOT tap factory reset/format data in recovery (would wipe the iOS image).
- **0030** (`xnu/patches/0030-sweet-ufs-writes.patch`, CI `38852655542`): UFS WRITE(10) + read-modify-write for partial 4 KiB blocks + SYNCHRONIZE CACHE (DKIOCSYNCHRONIZE), only with boot-arg `ufsrw=1`; `ufs_write_blocks` re-checks partition bounds before every write (only place data goes out).
- **0031** (`xnu/patches/0031-sweet-read-write-root.patch`, CI `38852837176`): boot-arg `rootrw=1` clears MNT_RDONLY before the root mount (no data volume on sweet: /private/var is on the root; image has no /etc/fstab); Apple HFS accepts a dirty non-journaled ROOT read-write on SWEET (logs "mounting dirty non-journaled root read-write"). Later: journaled HFS for crash safety. Kernel `xnu/out-0031` (CI `38852837176` success, 5m31s; 0030 run cancelled by the newer push). Boot images (phone ADT `sweet-0028.adt`, ramdisk byte-matched): `shim/out/shim-boot-0031r.img` = 0029k args (read-only, ignition_level=1) and `shim/out/shim-boot-0031w.img` = same + `ufsrw=1 rootrw=1`. PLAN: boot 0031r first and film until the reset (diagnose overnight reset), then 0031w (first ever writes to userdata; v2 image on the SSD is the restore source). `research/check-patch-order.py` cannot check 0031 (staged sweet_hfs files are not in its index); CI stage scripts run first, so CI is the check.

- **ignition_level=1 result** (boot 21:01:39 UTC, `research/boot0029k.log`, photo IMG_20261015_230308): preboot/cryptex stages skipped (need >= 2/3), `dylib_cache: finding shared cache on system volume: ignition level = 1, search root fd = 4, subpath = System/Library/Caches/com.apple.dyld/` -> not found -> `ignition boot failed: 19` -> no shared cache -> libSystem not loaded. FIX IN PROGRESS: image v2 = copy of the flashed image + `/System/Library/Caches/com.apple.dyld/` with HARD LINKS to the 44 cryptex cache files (no extra space; avoids symlink-following doubts), then `tools/sparsediff.py ios16-root-20H392.img ios16-root-20H392-v2.img diff.simg` and flash only the diff. Boot with `ignition_level=1` (shim-boot-0029k.img).
- **ignition_level=0 result** (boot 20:58:07 UTC, `research/boot0029j.log`, photo IMG_20261015_230037): all stages skipped as "ignition level insufficient" (hello/preboot/cryptex1 sniff >= 2, select os cryptex path/graft >= 3, **dyld_cache >= 1**), `ignition boot failed: 89`, "ignition partially disabled", then same `Library not loaded: /usr/lib/libSystem.B.dylib (no such file, no dyld cache)`. => dyld gets the shared cache directory from ignition's dyld_cache stage. Next: `ignition_level=1` (`shim/out/shim-boot-0029k.img`) to skip preboot/cryptex stages but run dyld_cache; its log "finding shared cache on %s ... subpath = %s" will show where it searches. If it searches rootfs /System/Library/Caches/com.apple.dyld, add a symlink there (image rebuild; consider a diff-only sparse flash tool to avoid rewriting 12 GB).
- **APPLE dyld/launchd RUNNING (libignition) with `unentitled_ios_sim_launch=1`** (boot 20:53:24 UTC, `research/boot0029i.log`, photo IMG_20261015_225617): kernel prints "Allowing spawn of iOS binary ... boot-arg set to true"; `shared_region: ... check_np ... vm_shared_region_start_address() failed` (no region yet, normal); dyld's built-in **libignition** (Darwin Ignition Sequence 1.0.0, libignition-51~1974; prints rd=ufsroot0, hardware target sweet, ignition level 0x5, platform 0x2, boot spec local, 7 stages): `hello from launchd.1` -> `preboot: mounting preboot` -> `failed to lookup preboot: 25` (ENOTTY: looks for a separate Preboot volume by role) -> ignition fails -> dyld `Library not loaded: /usr/lib/libSystem.B.dylib ... (no such file, no dyld cache)` -> launchd exit -> panic initproc failed. dyld boot-args found via strings: `ignition_level`, `ignition_force_dylib_root` (forced rootfs/livefs/cryptex fallback), `ignition_halt_after`, `ignition_live_app_graft`; dyld cache search paths include /System/Cryptexes/OS, /System/Volumes/Preboot/Cryptexes/OS/, /private/preboot/Cryptexes/OS/ (present in our image). Next try `ignition_level=0` (`shim/out/shim-boot-0029j.img`).
- **APPLE launchd EXECUTED FROM UFS (2026-10-15).** Flashed iOS image: `img2simg` -> `ios16-root-20H392.simg` (12.1 GB) then `fastboot -S 512M flash userdata ...simg` (24 chunks, 307 s, `research/flash-userdata-ios16.log`; a raw-image flash was killed by earlyoom at 2.6 GB RSS - always flash the sparse image). ABL fastboot hung on getvar after the flash; power+vol-down fixed it. Boot 0029u 20:49:04 UTC (`research/boot0029u-ios16.log`), photo IMG_20261015_225134: `hfs: mounted iOSRoot` -> load_init_program /sbin/launchd -> panic `unexpected SIGKILL of launchd (CS_KILLED) with reason -- namespace 9 code 0xe` = OS_REASON_EXEC / EXEC_EXIT_REASON_WRONG_PLATFORM: our kernel is XNU_TARGET_OS_OSX, iOS-platform binaries are "alien" and refused unless spawn attr platform set or DEVELOPMENT TUNABLE `unentitled_ios_sim_launch`. Next try: same kernel, cmdline + `unentitled_ios_sim_launch=1` (`shim/out/shim-boot-0029i.img`). LONGER TERM: macOS-config kernel marks iOS maps alien (vm_map_mark_alien) and differs from iOS in many policies; an iPhoneOS-config kernel build may eventually be needed.
- **iOS 16 ROOT IMAGE BUILT:** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392.img` (16 GiB case-sensitive HFS+, label iOSRoot, 12 GB used, fsck OK after `fsck.hfsplus -y` rewrote 32 non-ASCII localized WorkflowKit Shortcut names Linux decomposes differently). Built by `tools/mkiosroot.sh OS.dmg SYSTEMOS.dmg APPOS.dmg OUT.img [SIZE]` (needs sudo; apfs-fuse as root; OS dmg is UDIF -> link must end .dmg). Contents: iPhone X 20H392 OS root + SystemOS cryptex at /private/preboot/Cryptexes/OS (so /System/Cryptexes/OS -> cache, 44 files, dyld_v1 arm64) + AppOS at .../App. /sbin/launchd and /usr/lib/dyld root:wheel 0755. NEXT: (confirm) `fastboot flash userdata ios16-root-20H392.img` (auto-sparse), boot 0029u (rd=ufsroot0) -> Apple launchd attempt.
- **MILESTONE ON HARDWARE: BOOT FROM INTERNAL FLASH.** 0029 CI `38797924912` PASSED, `xnu/out-0029` SHA256 `a68bc847...2a37`. Image `shim/out/shim-boot-0029u.img` (payload-0029u = 0029 kernel + `shim/out/sweet-0028.adt` + `rd=ufsroot0`, NO RAM disk). Boots 20:01:34 and 20:12:37 UTC (`research/boot0029u*.log`), photo IMG_20261015_221403: `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB, read-only` -> `BSD root: ufsroot0, major 1, minor 0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `SWEET: root volume is not authenticated (error 25); continuing unsealed` -> `load_init_program ... /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> heartbeat (ran for minutes unattended). userdata currently holds the 8 MB `research/root-hfs.img`. NEXT: build a multi-GB HFS+ image with the iOS 16 (iPhone X 20H392) userland (OS rootfs + SystemOS cryptex contents incl. dyld shared cache at /System/Library/Caches/com.apple.dyld; preserve modes/owners/symlinks; decompress LZBITMAP via apfs-fuse), flash it to userdata (sparse, needs user OK), then try Apple's dyld/launchd. Driver is read-only (root mounts RDONLY), fine for first launchd attempts.
- **userdata FLASHED with the 8 MB HFS test volume** (user said "flash it", 2026-10-15 19:53:17 UTC, `research/flash-userdata-hfs-test.log`: `fastboot flash userdata research/root-hfs.img` OKAY; pre-checks: one sweet device, partition-size:userdata 0x1AC4BFB000, partition-type f2fs, image fsck OK, SHA256 3626ea69...). Android userdata is now destroyed (expected/approved). Boot 0028u at 19:53:20 (`research/boot0028u-hfs.log`), photo IMG_20261015_215541: `BSD root: ufsroot0` -> **`hfs: mounted SweetRoot on device b(1, 0)` from internal UFS** -> panic `rootvp not authenticated after mounting @bsd_init.c:931` (arm64 macOS-config requires FSIOC_KERNEL_ROOTAUTH sealed root for non-ramdisk roots). Patch **0029** (`dd1c284`): SWEET logs `SWEET: root volume is not authenticated (error N); continuing unsealed` instead of panicking (Apple configs keep the panic; pivot_root still requires auth). CI **`38797924912`** running. Next: download out-0029, phone image with sweet-0028.adt + rd=ufsroot0 (no RAM disk), boot -> expect init from UFS.
- **UFS ROOT DRIVER VERIFIED ON HARDWARE (read-only).** 0028 CI `38796139570` PASSED, `xnu/out-0028` SHA256 `8b981640...9da6`; QEMU HFS RAM-disk regression `research/q0028-hfs` still runs init. Phone boot 2026-10-15 19:50:24 UTC (`research/boot0028u.log`, image `shim/out/shim-boot-0028u.img`, phone ADT `shim/out/sweet-0028.adt` with /sweet-ufs, NO RAM disk, `rd=ufsroot0`), photos IMG_20261015_215151/215220: `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB, read-only` -> `BSD root: ufsroot0, major 1, minor 0` -> `hfs_ValidateHFSPlusVolumeHeader: unknown Volume Signature : f188` (Android-encrypted data, as expected) -> `cannot mount root, errno = 19`, kernel retries mountroot (no panic). Nothing written to flash. NEXT (destructive, needs user confirmation right before): `fastboot flash userdata research/root-hfs.img` (8 MB HFS with test init) then boot rd=ufsroot0 -> expect init from internal flash.
- **PATCH 0028 (`33aceac`): XNU read-only UFS root device**, CI **`38796139570`** running (next artifacts xnu/out-0028, research/bt29, run29.log). `bsd/dev/sweet_ufs.c`: reuses ABL's UFSHCI state (like the shim probe), takes over UTRL at a kmem_alloc_contig region (DMA layout: UTRL 0x0, UCD 0x1000, 1 MiB bounce 0x4000), verifies UTRLBA readback before any doorbell, IE=0 polled, one SCSI cmd at a time on LUN0 (TUR x3, READ(10) via bounce, PRDT 256 KiB chunks), flush_dcache64 by PA around each command (host not dma-coherent per DT), finds GPT partition by name (`ufsroot=` boot-arg, default `userdata`), exposes `/dev/ufsroot0`/`rufsroot0` (512-byte logical sectors, physical 4 KiB, DKIOC* ioctls), refuses writes (EROFS). IOKitBSDInit: `rd=ufsroot0` -> sweet_ufs_rootdev() (lazy init) else panic. ADT: `tools/mkadt.py` adds `/sweet-ufs` reg <0x1d84000 0x3000> for the PHONE only (not --qemu). Local compile OK, imports resolve. Sandbox research/bt28 (pre0028 originals). FIRST PHONE TEST PLAN (non-destructive): boot 0028 with phone ADT + `rd=ufsroot0` and NO RAM disk: expect `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB` + `BSD root: ufsroot0`, then root mount failure (userdata is still Android-encrypted) -> panic. That validates the driver before flashing an HFS image into userdata (needs explicit user confirmation at that time).
- **SUPERSEDES the 64 GiB iosroot GPT plan: user said "u can delete android" (2026-10-15).** Use the existing `userdata` partition (LUN0 sda34, 4K LBA 0x2B8C00, 0x1AC4B MiB ~107 GiB) directly as the iOS root: NO GPT changes. Keep bootloaders, recovery (OrangeFox), modem/persist/fsg/modemst untouched. Write the HFS image later with `fastboot flash userdata` (sparse, auto-split under the 768 MiB limit). Android will no longer boot normally (expected; reinstallable). Order: XNU UFS driver first, read-only against the current GPT; flash only once it can locate userdata. Nothing erased yet.
- **DECIDED (user, 2026-10-15): 64 GiB `iosroot` on LUN0 (sda), taken from userdata (wipes Android user data; Android/super kept).** Planned GPT (4K LBAs): userdata 0x2B8C00..0xD7D6FF (~43 GiB, keep type/unique GUIDs and attributes); iosroot 0xD7D700..0x1D7D6FF (0x1000000 blocks = 64 GiB, 1 MiB aligned); backup GPT area unchanged. Procedure: user backs up phone data -> boot OrangeFox recovery (adb) -> back up GPT (sgdisk --backup + raw dd of LBA 0-5 and last 6 blocks) to research/ -> sgdisk edit -> Format Data -> verify Android boots to setup. NOT EXECUTED YET.
- **INTERNAL UFS WORKS FROM THE SHIM (read-only), user authorized internal-UFS approach incl. flashing (2026-10-15, "i allow everything").** Shim probe `shim/ufs.c` (commit `12ed3ed` + filter): ufshc@1d84000 is UFSHCI 2.1 (ver 0x210, cap 0x1587031F, 32 slots), ABL leaves HCE=1, HCS=0x10F (device present, lists ready, UIC ready); probe takes over UTRL at its own buffer (verifies UTRLBA readback before any doorbell), TEST UNIT READY/READ CAPACITY/READ(10) all succeed. LUN0 = 0x1D7D800 x 4 KiB (~126.6 GB), valid GPT (64 entries at LBA 2). Photos IMG_20261015_212916/213325/213429. Big LUN0 partitions (start in 4K LBAs / MiB): super 0xCA00/0x2200 (8.5 GiB), logdump 0x22CA00/64, minidump 0x230A00/128, rawdump 0x238A00/128, recovery 0x240C00/128, cache 0x248C00/384 ext4, exaid 0x260C00/384, cust 0x278C00/1024 ext4, **userdata 0x2B8C00/0x1AC4B MiB (~107 GiB), fs unreadable = encrypted (metadata encryption)**. cache..cust contiguous = only 1.75 GiB (too small for iOS ~10+ GiB). Plan needing user consent: shrink userdata in GPT (wipes Android data) and add an `iosroot` partition at the end of LUN0. LUNs 1-5 not listed yet (sdb..sdf backed up in backup/lun).
- **fastboot limit measured (2026-10-15, read-only getvar):** `max-download-size: 805306368` (768 MiB); `max-fetch-size` unsupported; `is-userspace: no` (ABL fastboot). A `fastboot boot` image (shim+kernel+RAM disk) must be < 768 MiB, so the 2.5 GiB iOS shared cache cannot ride in the boot RAM disk even if XNU gets all RAM. Real userland needs storage access (UFS driver, or USB host) or a much smaller cache. Unlocking full RAM is still needed later (GUI).
- **iOS 16 USERLAND SOURCE (Claude, 2026-10-15).** Chose **iPhone X (iPhone10,3/10,6, D22/D221AP)** iOS **16.7.16 (20H392)** over iPhone 8: same A11 (no PAC -> plain arm64, runs on Kryo 470/ARMv8.2), last iOS for A11; X userland is home-button-less and tall-screen (1125x2436 vs sweet 1080x2400), better fit for later GUI. Note the X has its OWN SystemOS cryptex (different digest from iPhone 8's). IPSW URL in `research/ipsw-x/URL.txt` (+ BuildManifest). Images on the user's external SSD (NOT in git, do not format that disk: it holds the user's photos): `/run/media/dipa/android/ios-sweet-ipsw/iPhone10,3_16.7.16_20H392/` — `087-86593-047.dmg` = Cryptex1,SystemOS (2,743,074,816 B), `087-86698-044.dmg` = OS rootfs (4,730,814,044 B), both zip CRC-32 verified, plus Firmware/*.root_hash/.trustcache/.mtree. AppOS cryptex is 087-86715-047.dmg (10 MB, same as iPhone 8).
  - Images are raw APFS; files use LZBITMAP (decmpfs type 14). 7z cannot decode. Tools: `ipsw` 3.1.738 (AUR ipsw-bin, user-approved) needs apfs-fuse on Linux; **apfs-fuse** built in user space (system cmake broken: cmake 4.4.4 wants libjsoncpp.so.27, jsoncpp 1.9.6 installed = partial upgrade, NOT fixed) with pip cmake + `-DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_CXX_FLAGS="-include cstdint"`, installed to `~/.local/bin/apfs-fuse` (+apfs-dump-quick). Mount via a comma-free symlink (apfs-fuse splits options on ',' in `iPhone10,3`; exFAT has no symlinks -> put link elsewhere): `apfs-fuse LINK/087-86698-044.dmg MNT` -> `MNT/root/...`; unmount `fusermount3 -u MNT`.
  - Verified from headers: `dyld_shared_cache_arm64` magic `dyld_v1   arm64`; `/sbin/launchd`, `/usr/lib/dyld` = cputype 0x100000c subtype 0 (plain arm64). libSystem exists only inside the cache.
  - **BLOCKER for real userland via RAM disk:** shared cache = 3.10 GiB in 44 files (~2.5 GiB without the 592 MB `.symbols`), but the kernel manages only 1.20 GiB (0xb0000000..0xfd000000). Options: (A) give XNU the phone's full ~6 GB (banks 0x80000000+2G and 0x100000000+0xfcc00000, carve-out holes need pmap support) AND check fastboot max-download-size for a multi-GB boot image; (B) storage driver (Qualcomm UFS) to read a root from flash (no flashing allowed: would need a file/partition strategy); (C) run against individual dylibs extracted from the cache (uncertain).
- **MILESTONE ON HARDWARE: HFS+ ROOT FILESYSTEM -> PID 1.** Boot 2026-10-15 18:22:12 UTC (`research/boot0027b.log`, image `shim/out/shim-boot-0027b.img`), photo `IMG_20261015_202334.jpg`: `BSD root: md0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> repeated `SWEET init: still alive`, no panic. Kernel 0027 (built-in Apple OSS HFS + BearSSL MD5), init with SP alignment fix. NEXT: real iOS 16 userland on the HFS image (dyld, libSystem/dyld shared cache, launchd). Known gaps: entitlements (none granted), SHA-1/SHA-384/512 providers, no storage driver (RAM disk only), root mounted read-only.
- **PHONE HFS ROOT (0027) + SIGBUS ROOT-CAUSED.** Phone boot 2026-10-15 17:49:06 UTC (`research/boot0027.log`, photo `IMG_20261015_200031.jpg`): `hfs: mounted SweetRoot on device b(1, 0)` (HFS works on hardware), init printed its first line, then `pid 1 exited -- exit reason namespace 2 subcode 0xa` = SIGNAL/SIGBUS -> `initproc failed to start` panic. Diagnostic boot 18:08:13 UTC (`research/boot0027d.log`, image `shim/out/shim-boot-0027d.img`, diag init `research/diag-init` from scratch diag-init.S with [a][b][c] markers, `cs_debug=1`; photo `IMG_20261015_201547.jpg`): output `PID [a][b]` then SIGBUS -> fault at first `strb w21,[sp]`; no code-signing messages. Cause: kernel enters a static binary with sp at argc, not necessarily 16-aligned (depends on arg/apple string lengths, differs mockfs vs HFS); EL0 SP alignment check -> EXC_ARM_SP_ALIGN -> SIGBUS (sleh handle_sp_align). QEMU does not enforce SP alignment. NOT a kernel bug: real binaries start in dyld which aligns. Fix `1a8fc15`: sweet-init aligns sp at entry. Rebuilt `research/root-hfs.img`, QEMU `research/q0027-hfs2` OK. Phone image `shim/out/shim-boot-0027b.img` SHA256 `098ba46c...c5c` (payload-0027b, ramdisk match check-0027b) ready, awaiting FASTBOOT. Lesson: Assembly `;` is a comment in Apple arm64 asm (use .macro, not ;-joined #define).
- **HFS ROOT WORKS (QEMU).** 0027 CI `38779441895` PASSED, `xnu/out-0027` SHA256 `a8643886...5f6a`. QEMU `research/q0027-hfs` (RAM disk = `research/root-hfs.img`, rd=md0): `BSD root: md0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` + heartbeat, no panic. Phone image `shim/out/shim-boot-0027.img` (payload-0027 = 0027 kernel + sweet-0021.adt + root-hfs.img + rd=md0, ramdisk byte-match check-0027) ready; awaiting FASTBOOT for phone test.
- **HFS ROOT WORK (Claude), patches 0026-0027.**
  - 0026 (`f0e990c` + link fix `64c96f4`): Apple OSS **hfs-627.100.6** (commit `31d5ec238dfab485e78a9a30b8b92d13e8914f03`, paired with xnu-8796.141.3 in macos-135 release.json) staged by `xnu/patches/0026-stage-hfs.sh` into `bsd/sweet_hfs` (core + hfs_encodings; AppleKeyStore include/key prototypes guarded by CONFIG_PROTECT; SDK TargetConditionals copied). New config option `sweet_hfs` (MASTER + MASTER.arm64.sweet); 40 `optional sweet_hfs` files; Makefile.template foreach adds `_CFLAGS_ADD = -include sweet_hfs_compat.h -I...` (MUST come after kernel -D flags; compat undefs BSD/XNU_KERNEL_PRIVATE and the CONFIG_* HFS tests so kext-config.h decides: macOS profile, no content protection). `sweet_hfs_iokit.c` replaces hfs_iokit.cpp/hfs_encodings_kext.cpp: `sweet_hfs_register()` called in bsd_init after vfsinit (encodings init, vfs_fsadd VFS_TBLCANMOUNTROOT, zones, sysctls); is_ejectable 0, iterate_media none, serial KERN_NOT_SUPPORTED, OSKextGetCurrentLoadTag -> kOSKextInvalidLoadTag (renamed via compat macro). hfs_encodings' own `hfs_allocated` renamed per object (separate kexts on Apple; first CI `38777325964` failed on that duplicate at link). mockfs now validates Mach-O magic (its TODO) so non-Mach-O roots fall through to HFS (new fs entries come AFTER mockfs in vfsconf). CI `38778133720` PASSED, `xnu/out-0026` SHA256 `0b49170c...701a`, prints `SWEET HFS: hfs-627.100.6 registered`.
  - HFS+ image: `research/root-hfs.img` (8 MB, mkfs.hfsplus from AUR hfsprogs installed with user approval; loop-mounted with sudo; /sbin/launchd = research/sweet-init, /dev; fsck.hfsplus OK). QEMU `research/q0026-hfs`: `BSD root: md0` then data abort in MD5Init from hfs_getvoluuid (mount computes volume UUID).
  - 0027 (`14bf2b7`): 0020 stager also copies BearSSL hash/md5.c + codec/dec32le.c/enc32le.c; `corecrypto_md5.c` SWEET branch converts MD5_CTX <-> br_md5_context around br_md5_* calls; wrappers sweet_md5.c/sweet_dec32le.c/sweet_enc32le.c. Host test 40/40 match md5sum. CI **`38779441895`** running.
  - Local tooling: `tools/xnu-cc.py` has `XNU_CC_POST` (flags after logged ones). Sandbox `research/bt28/xnu` = 0025 CI tree + 0026/0027 edits; originals `research/pre0026`, `research/pre0027`. HFS local objects `research/hfs-objs`. Checker entries updated to bt28.
  - SHA-1 / SHA-384/512 still have no provider.
- **MILESTONE ON HARDWARE: USERSPACE PID 1 RUNS ON THE PHONE.** Boot 2026-10-15 17:16:00 UTC (`research/boot0025.log`: send OKAY0.410s, boot OKAY0.135s), image `shim/out/shim-boot-0025.img` SHA256 `9dbfa0b1...89db0`. Photo `IMG_20261015_191733.jpg`: `BSD root: md0` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> repeated `SWEET init: still alive` (5 s heartbeat), no panic. Kernel 0025 + mockfs RAM disk + built-in no-entitlements AMFI. No flashing performed.
- **NEXT (toward real iOS userland):** real root filesystem with real binaries. Options: (a) build Apple OSS `hfs` (macOS 13.5 tag `hfs-627.100.6`) into SWEET like libpthread, then an HFS RAM disk image; (b) iOS 16 dyld + libSystem/dyld shared cache from the IPSW (needs APFS or repacking onto HFS). Expected hurdles: entitlements (sweet_amfi grants none), SHA-1/MD5/SHA-384/512 providers (BearSSL), missing kexts/daemons. Current init is a static test program, not launchd.
- **MILESTONE: USERSPACE RUNS (QEMU).** 0025 CI `38774788048` PASSED, `xnu/out-0025` SHA256 `5496069b...4877`. QEMU `research/q0025-rd` (150 s, no panic): `BSD root: md0` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> `SWEET init: still alive` every 5 s. Exec, ad-hoc SHA-256 code signature, syscalls, devfs /dev/console, select timeouts all work. Phone image prepared: `shim/out/shim-boot-0025.img` 16,515,072 bytes SHA256 `9dbfa0b15140c0bd733a16c4f727f6a7df44a8741f98d8e266d5f2fa4f689db0` (payload-0025 = 0025 kernel + sweet-0021.adt + research/sweet-init + rd=md0; ramdisk byte-match check-0025). Waiting for user to put phone in FASTBOOT.
- **0024 CI `38773277811` PASSED**, `xnu/out-0024` SHA256 `a0ba964b...4348`. QEMU `research/q0024-rd` and **PHONE (boot 2026-10-15 17:05:55 UTC, `research/boot0024.log`, image `shim/out/shim-boot-0024.img` SHA256 `cf3dac86...6964`, 16,510,976 bytes, payload `shim/out/payload-0024.bin` = 0024 kernel + `shim/out/sweet-0021.adt` + RAM disk `research/sweet-init` + rd=md0; ramdisk byte-match `check-0024`)** agree: `Added memory device md0`, `BSD root: md0`, `load_init_program: attempting to load /sbin/launchd`, then data abort in accelerate_entitlement_queries (PC 0x...77d2458, FAR 0x1a0) = NULL AMFI interface. Photo `IMG_20261015_190715.jpg`. RAM disk root is physically verified.
- **0025 (`2518c79`)**: new `bsd/kern/sweet_amfi.c` registers a built-in AMFI interface at EARLY_BOOT/MIDDLE: no entitlements (adjustContextWithoutMonitor succeeds without creating a context, queries KERN_DENIED, copies NULL/KERN_NOT_FOUND, get_xml/transmuted false); WithMonitor KERN_NOT_SUPPORTED; OSEntitlements_query and query_context_to_object panic explicitly (CoreEntitlements closed; no kernel caller); TrustCache version 0 (0015 keys on trust_cache_rt==NULL, img4 absent -> still unavailable); CoreEntitlements table zero (PMAP_CS only). Compiles locally; checker updated (bt27 entries). CI **`38774788048`** running. Next artifacts `xnu/out-0025`, `research/bt29`, `research/run29.log`. Real iOS binaries will need real entitlements later (no OSS CoreEntitlements exists).
- **0021-0024 RAM-disk-root iteration (Claude), QEMU only so far, no new phone boot since 0020.** Each kernel tested with `tools/mkpayload.py KERNEL research/q0021.adt OUT --ramdisk research/sweet-init --cmdline "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0"` then `tools/qemu-sweet.py OUT DIR --secs 150 --kernel KERNEL --fail-on-panic` (PATH needs ~/swift/usr/bin for llvm-nm). Fresh ADTs: `research/q0021.adt` (QEMU), `shim/out/sweet-0021.adt` (phone).
  - 0021 CI `38769532000` PASSED, `xnu/out-0021` SHA256 `2b7500a1...962e`, `research/bt25`/`run25.log`. QEMU `research/q0021-rd`: md0 root, then assert `iomediaClass` in IOService::publishHiddenMedia.
  - 0022 (`20ece9c`, publishHiddenMedia without IOMedia class) CI `38770666158` PASSED, `xnu/out-0022` SHA256 `a4d0e787...30c5`, `research/bt26`/`run26.log`. QEMU `research/q0022-rd`: data abort in SHA256_Init (NULL g_crypto_funcs) from vm_kernel_addrhash_internal.
  - 0023 (`c8089d1`, libkern SHA256_Init/Update/Final use built-in ccsha256_ltc_di + ccdigest_init/update on SWEET; also serves code-signing SHA-256; SHA-1/MD5/SHA-384/512 still have NO provider - BearSSL from 0020 could supply them later) CI `38771876423` PASSED, `xnu/out-0023` SHA256 `d763fed7...1003`, `research/bt27`/`run27.log`. QEMU `research/q0023-rd`: **mockfs mounted md0, `load_init_program: attempting to load /sbin/launchd`**, then panic `mockfs_fsnode_vnode failed to create fictitious pages ... rvalue = 5` (mockfs.c:351).
  - 0024 (`3293c80`): mockfs used memdev mi_base (4K page number of a VIRTUAL kernel address for IOKit RAMDisk, truncated to 32 bits) << PAGE_SHIFT as a physical address. Now zero-copy pager mapping only when mi_phys (with 4K units); virtual md uses pagein/blockmap/strategy -> memdev bcopy. memdev's own mdPhys path assumes 4K ppnums (unsafe on 16K arm64), so do NOT switch the RAMDisk to physical. CI **`38773277811`** running. Next artifacts `xnu/out-0024`, `research/bt28`, `research/run28.log`.
  - Sandboxes: bt25/bt26/bt27 contain the next patch's edited files; pristine copies in `research/pre0022`..`pre0024`.
- **PATCH 0021 (Claude): RAM disk root via mockfs -> first userspace program.** Commits `9c37771` (initial; CI `38768500280` FAILED: mockfs_fsnode.c kfree_type(mockfs_fsnode_t) typed-alloc static assert; local xnu-cc stubs `__builtin_xnu_types_compatible` so it can't catch this) and `193772f` (fix), CI **`38769532000`** running: https://github.com/dipa-studio/ios-sweet/actions/runs/38769532000. Next artifacts: `xnu/out-0021`, `research/bt25`, `research/run25.log`.
  - Kernel: `config/MASTER.arm64.sweet` FILESYS_BASE += `mockfs` (XNU's built-in FS: root device is itself a Mach-O, served as /sbin/launchd, plus /dev for devfs). Upstream mockfs bit-rot fixed: kalloc_type/kfree_type used the POINTER typedef mockfs_fsnode_t (nodes were 8 bytes) -> `struct mockfs_fsnode`. `IOService::setRootMedia` asserted IOBlockStorageDriver class exists (IOStorageFamily absent): SWEET-only, a missing class means root=NULL (same as IOSetImageBoot); Apple path keeps assert. All 21 patches apply (`research/check-patch-order.py`); 5 TUs compile locally with -DMOCKFS (`research/mockfs-objs`), imports resolve vs 0020 kernel. Sandbox `research/bt24/xnu` now holds 0021 versions of those 3 files; pristine 0020 copies in `research/pre0021`.
  - Tools: `tools/mkpayload.py --ramdisk IMAGE` appends IMAGE as an extra payload segment right after the kernel, moves kernel_end past it (shim unchanged: ADT+boot_args follow it, image stays below topOfKernelData), and adds ADT `/chosen/memory-map` `RAMDisk`=<phys,size>. Boot with `rd=md0`. Without --ramdisk output is byte-identical to existing 0020 QEMU and phone payloads (verified). `tools/sweet-init.S` + `tools/mkinit.py`: PIC static init (open /dev/console, print PID, heartbeat every 5 s via select, never exits) wrapped into a static arm64 Mach-O (__PAGEZERO, __TEXT@0x100000000, LC_UNIXTHREAD, ad-hoc SHA-256 CodeDirectory v0x20400, 4K pages). Build: `~/swift/usr/bin/clang -target arm64-apple-ios16.0 -c tools/sweet-init.S -o X.o && tools/mkinit.py X.o research/sweet-init` (ld64.lld cannot link static iOS). Signature not verified by a real codesign; the kernel will tell.
  - QEMU with 0020 kernel + RAM disk (`research/q0020-rd.bin`, rd=md0, 150 s `research/q0020-rd150`): `Added memory device md0`, **`BSD root: md0, major 1, minor 0`** (plumbing works), then the setRootMedia assert (now fixed in 0021). NOTE: QEMU needs >60 s to reach IOFindBSDRoot (60 s run showed nothing after stf0; likely RTC/inittodr wait), so use --secs 150.
  - NEXT: download 0021, QEMU 150 s with ramdisk; expect mockfs mount then init exec -> `*** SWEET userspace: init running as PID 1 ***`. Then phone boot with same payload (phone ADT shim/out/sweet-0020.adt pattern + --ramdisk + rd=md0).
- **0020 PHONE RESULT (user transcription of screen, 2026-10-15): KERNEL INIT COMPLETE, WAITING FOR ROOT.** After Skywalk self-tests PASSED, kminit, ifnet_attach lo0/gif0/stf0, screen prints `BSD`, then `Waiting on <dict><key>IOProviderClass</key><string>IOMedia</string><key>Content</key><string>Apple_HFS</string></dict>` and `Failed to write boot-picker-bringup-reason to NVRAM.` No panic. This is IOFindBSDRoot waiting for a root device (none exists); NVRAM warning is expected (no NVRAM driver). QEMU `cpu_idle` snapshot is presumably the same wait (not GDB-confirmed; milestone GDB run was cancelled by user since phone answered it). Draft `research/check-milestones20.gdb` (hbreaks inittodr/vfs_mountroot/IOFindBSDRoot/bsd_utaskbootstrap) left uncommitted/ignored.
- **NEXT MILESTONE: root filesystem -> launchd.** Plan: (1) RAM disk: shim places an image in RAM, ADT /chosen/memory-map `RAMDisk` entry, boot-arg `rd=md0` (XNU md driver). (2) HFS is a separate kext on Apple; build Apple OSS `hfs` (tag paired with macOS 13.5 in distribution-macOS macos-135 release.json) into SWEET like libpthread 0019. APFS is closed. (3) Minimal HFS image with iOS 16 launchd (later: dyld/shared cache; AMFI/code-signing absent will be a later hurdle). User's end goal is full iOS GUI.
- **0020 (AES) VERIFIED + PHONE BOOTED (Claude took over after Codex usage limit).** Actions `38765422261` (`ab9e23f`) PASSED; kernel `xnu/out-0020/kernel.development.sweet` checksum OK; buildtree `research/bt24`, log `research/run24.log`. Actual-kernel AES checks PASS (`research/check-aes20.gdb` / `.log`, 12 extra CBC cases match OpenSSL). 45s QEMU `research/q0020`: no panic, zero unknown glyphs, past old TCP/AES panic -> Skywalk self-tests PASSED -> bsd_autoconf kminit -> ifnet_attach lo0/gif0/stf0; final snapshot PC in `cpu_idle` (idle or waiting; NOT yet diagnosed, could be root-device wait). Image `shim/out/shim-boot-0020.img` 16,461,824 bytes SHA256 `775200cb02d95fc750981516b79d91dcdc96184bbe67a38f9d57c59b4a391828`, ramdisk byte-matches `payload-0020.bin` (`check-0020`). **Phone temporarily booted 2026-10-15 16:10:00 UTC**: one FASTBOOT product sweet, send OKAY0.407s, boot OKAY0.134s, total0.549s, exit0 (`research/boot0020.log`). Awaiting user photo; do not reboot the phone before it. NEXT: read photo; diagnose what QEMU waits on after stf0 (GDB backtrace of threads / longer run). Codex's STOP request below is complete.
- User requests STOP after completing the current0020 AES iteration (Actions/QEMU/phone), then leave a precise committed handoff for another AI. User says FASTBOOT ready again after0019 photo. Do not start a new blocker fix after this iteration.
- Goal: iOS16-generation XNU on Redmi Note10Pro sweet/SM7150. Always commit, use gh/Actions for kernel builds, keep this handoff current. Temporary fastboot boot only; preserve Android/backups. No userland/root filesystem boot yet.
- **Patch0020 update:** initial `e71098d` / Actions `38765012466` superseded by scalar-only compile flags. Added -mgeneral-regs-only to all six provider/BearSSL TUs and corecrypto_aes.c; object disassembly now confirms no SIMD. Updated implementation `ab9e23f`, Actions `38765422261` queued/running: https://github.com/dipa-studio/ios-sweet/actions/runs/38765422261. Do not launch another run. portable BearSSL AES CBC and legacy one-block ECB wired directly into SWEET corecrypto_aes.c. Genuine bitslice implementation, no CPU AES/SIMD requirement, heap or fake global crypto table. Source fetched by `0020-stage-bearssl.sh` from official BearSSL git at immutable `7bea48e5e850ab4cafbe68d3765cdaba13a86d6f`; MIT license retained, downloaded source stays out of git. Kernel limits include adapter only. All128/192/256-bit keys, CBC encrypt/decrypt, copied contexts, in-place/out-of-place; zero block count and size overflow handled, invalid keys clear context. Seven TUs compile to arm64 objects (`research/aes-objs`), imports resolve, all20 patches apply and sources match (`research/patch0020-check.log`). Sandbox `research/bt23/xnu`, originals `research/pre0020`. NEXT: Actions then actual-kernel NIST/random CBC/ECB checks and >=45s QEMU before another phone boot. Next artifacts out-0020 / bt24 / run24.log. 0020 updated CI pending. Local sources/checks match the scalar-only patch.
- **Latest built kernel0019**, implementation `256d3f0`, patches0001-0019. Actions `38763072907` PASSED (4m5s): https://github.com/dipa-studio/ios-sweet/actions/runs/38763072907. Kernel `xnu/out-0019/kernel.development.sweet`, SHA256 `a27df7568f03fb541cf0e8024c0a594fa178a85054fcf9eba29158cbd4c5ecc0`; checksum verified. Log/source `research/run23.log` / `research/bt23` (no nested .git). Seven pthread source/build/header files and staged adaptations byte-match local compile inputs.
- **0019 hardware photo received** `IMG_20261015_175306.jpg`: pthread registration visible, passes mbinit and DLIL checksum/scheduling, same AES fault as QEMU: PC`0xfffffe00079174e0` (`aes_encrypt_key128`), LR`0xfffffe000767c3a4` (`tcp_init`), FAR0x78, x8=0. Disassembly proves NULL g_crypto_funcs->ccaes_cbc_encrypt. Photo processed; no more0019 observation pending. General crypto table remains absent, other hash/mode operations may still fault after0020. DO NOT bypass TCP or install fake crypto. XNU already contains SHA256/HMAC implementations; AES source there is a dispatch wrapper. Full future provider interface libkern/libkern/crypto/register_crypto.h. Apple/corecrypto default README describes evaluation-only licensing, so no external corecrypto was fetched or staged; BearSSL selected for this portable AES integration.
- **0019 pthread FIXED in QEMU and observed beyond its init on phone**: 45s QEMU `research/q0019`, zero unknown glyphs, then AES panic. Actual-kernel API checks PASS `research/check-pthread19.gdb` / `.log`, guest `research/q0019-api`: function/callback table identity, actual provider pthread_init returns, locks/global hash/threadcall/typed zones initialized, thread_selfid via syscall shim + buffer bounds, process hash init/delete via shims restores NULL. Monitor quit prints expected remote-disconnect after PASS. All fixture guests stopped.
- **0019 provider**: genuine Apple libpthread-514.100.2 commit `a6c70ca0e544347a0377babf748f831577ec24f9`, exact paired release with xnu8796.141.3 in distribution-macOS/macos-135/release.json (`research/macos-135-release.json`). 0019 shell stage runs before patches (workflow copies *.sh); three SWEET wrapper TUs use kext BSD header view, vm_fault_external, renamed provider-side pthread_kern/current_uthread; register real function table at EARLY_BOOT SECOND, real pthread_init later. Stager applies bounded address casts, zero user addresses, proper panic format. SWEET opaque ksyn storage enlarged48->56 for trailing kwe_uth, checked with provider static assertion. Local pre-CI TargetConditionals fixture was syntax-only; artifact bt23 carries actual SDK header and CI is authoritative.
- **Phone0019 temporarily booted** 2026-10-15 15:51:36 UTC: exactly one FASTBOOT/product sweet verified; send OKAY0.406s, boot OKAY0.134s, total0.546s, exit0 (`research/boot0019.log`). Image `shim/out/shim-boot-0019.img`, 16,457,728 bytes, SHA256 `19429a57e486b856880df9e27327ed488e0139345311fdb0350974e72103a9a1`. Phone ADT/payload `shim/out/sweet-0019.adt` / `payload-0019.bin` timer19, unpacked ramdisk byte-match (`check-0019`). EntryPA0xb146b488, kernelendPA0xb2000000, boot_argsPA0xb2004000/top0xb2008000. Last user FASTBOOT+USB reply preceded this boot; do not assume phone is still in FASTBOOT.
- **CPU0018 physically verified** by `IMG_20261015_173951 (2).jpg`: boot CPU0 registered, real SGI1 verified, initialization complete -> BSD/MAC/mbinit -> old pthread-table panic. SweetCPU uses legacy IOCPU, ml_processor_register/processor_start/initCPU, real SGI1 clears SIGPdisabled before max CPUs completion; no forced flags/skipped waits. CPU APIs and two-CPU rejection passed (`research/check-cpu18.gdb`, `q0018-api`, `q0018-smp`). Single core; SMP/suspend unsupported. CURRENT SWEET has NO USE_APPLEARMSMP.
- QEMU next run: generate fresh `tools/mkadt.py research/q0020.adt --qemu` (timer27), mkpayload with `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`, then `tools/qemu-sweet.py PAYLOAD OUT --secs 45 --kernel KERNEL --fail-on-panic`. 12s can miss later panics because IORTC waits30s. Runner snapshot only: panic exit2, blank/incomplete exit3; absence of panic does not mean complete boot. Qualcomm XPU/ABL/panel and phone SMC PSCI require hardware checks.
- Local checker `tools/xnu-cc.py research/run23.log research/bt23 FILTER --per-file`, XNU_CC_OBJDIR for objects. For new BearSSL TUs add XNU_CC_EXTRA with -I bt23/xnu/libkern/crypto/sweet_bearssl/{inc,src}. Patch checker `research/check-patch-order.py` uses temporary upstream index; source fixtures/artifacts ignored under research. GDB mask registers to unsigned64, use function-entry manual-call return traps, discard manipulated guests. No QEMU guest intentionally left running.

## Session log and earlier handoffs (superseded by the active summary above)

### Prior 0019 transition notes (superseded)

- Goal: iOS 16 generation XNU on sweet. Always commit completed work, use gh/Actions for kernel builds, keep this handoff current. Temporary fastboot boot only; preserve Android/backups.
- **0019 build PASSED** Actions `38763072907` (4m5s), implementation `256d3f0`. Kernel `xnu/out-0019/kernel.development.sweet`, SHA256 `a27df7568f03fb541cf0e8024c0a594fa178a85054fcf9eba29158cbd4c5ecc0`; checksum verified. Log/source `research/run23.log` / `research/bt23`; all seven patched files and staged provider adaptations match local compile inputs. Prefer bt23 as the next baseline.
- **0019 pthread FIXED in QEMU**: 45s run `research/q0019` registers provider, passes mbinit, DLIL SUM16 checks and DLIL thread scheduling. Actual-kernel GDB checks `research/check-pthread19.gdb` / `.log` PASS: function/callback table identity, real _pthread_init returns, locks/global hash/cleanup threadcall/typed zones non-NULL, thread_selfid via actual syscall shim with output bounds, process hash init/delete through actual shims restores NULL. Guest stopped after tests; no fixture left running. GDB monitor quit prints expected remote disconnect after PASS.
- **Current next blocker:** QEMU0019 panic data abort FAR0x78 at `aes_encrypt_key128` PC`0xfffffe00079174e0`, called by `tcp_init` LR`0xfffffe000767c3a4`. Disassembly confirms `g_crypto_funcs == NULL`, loading ccaes_cbc_encrypt at+0x78. General crypto registration is still absent; DO NOT bypass TCP or supply fake crypto. Next integrate a genuine compatible crypto implementation/provider (AES first needed here, other digest/mode APIs also used). XNU contains SHA256/HMAC but no AES implementation; its corecrypto_aes.c is a dispatch wrapper. Full crypto table is in libkern/libkern/crypto/register_crypto.h.
- **0019 phone image prepared and verified**, user reports FASTBOOT+USB again; exactly one device/product sweet verified. `shim/out/shim-boot-0019.img`, 16,457,728 bytes, SHA256 `19429a57e486b856880df9e27327ed488e0139345311fdb0350974e72103a9a1`; unpacked ramdisk matches phone payload (`shim/out/check-0019`, `payload-0019.bin`, `sweet-0019.adt`, timer19). EntryPA0xb146b488; kernelendPA0xb2000000; boot_argsPA0xb2004000/top0xb2008000. Usual debug cmdline cpus=1/-noprogress. **Temporarily booted 2026-10-15 15:51:36 UTC**: send OKAY0.406s, boot OKAY0.134s, total0.546s, exit0 (`research/boot0019.log`). User asked for photo after45s. Await the photo; DO NOT reboot again before observation. Bootloader acceptance only; no0019 physical progress observed yet.
- **Hardware photo confirms 0018 progress** (`IMG_20261015_173951 (2).jpg`): real phone prints `SWEET CPU: boot CPU 0 registered, SGI1 verified, initialization complete`, enters BSD/MAC, reaches `mbinit: done`, then the same missing-pthread-function-table panic as QEMU at pthread_shims.c:318. CPU completion/interrupt delivery is now physically observed. The photo was received; no further phone boot performed yet.
- **Patch0019 committed/pushed `256d3f0`; Actions `38763072907` queued/running:** https://github.com/dipa-studio/ios-sweet/actions/runs/38763072907. Do not launch a duplicate. genuine Apple OSS libpthread-514.100.2 provider (immutable commit `a6c70ca0e544347a0377babf748f831577ec24f9`), paired with xnu-8796.141.3 by Apple's `distribution-macOS/macos-135/release.json` (`research/macos-135-release.json`). `0019-stage-libpthread.sh` fetches/stages it before patches; workflow now copies shell scripts too. SWEET-only wrappers compile all three real kernel sources, rename provider-side symbols, use kext header view and vm_fault_external, register the real function table at EARLY_BOOT SECOND. Existing pthread_init then runs the actual provider initialization. No pthread wait/syscall is bypassed. Source staging includes bounded explicit address casts/zero user addresses and panic-format fixes. SWEET kernel opaque ksyn storage enlarged from48 to56 bytes to contain this provider's trailing kwe_uth, with a provider size assertion. Local compile of three provider TUs plus pthread_shims/kern_fork passed; imports resolve and provider exports do not collide with existing kernel symbols. All19 patches apply and changed sources match (`research/patch0019-check.log`). Source sandbox `research/bt22/xnu`, originals `research/pre0019`, objects `research/pthread-objs`. Local TargetConditionals fixture only has target macros for syntax; CI stages the real macOS SDK header and is authoritative. Next Actions artifacts: out-0019 / bt23 / run23.log; run QEMU >=45 seconds. 0019 CI is pending; no 0019 QEMU run yet.
- **Latest kernel implementation `e7d9550`, patches0001-0018; CI `38760004398` PASSED (3m56s)**: https://github.com/dipa-studio/ios-sweet/actions/runs/38760004398. No build is pending. Kernel `xnu/out-0018/kernel.development.sweet`, SHA256 `b3c8d59acc88f93a2c836eb2527a05ed4fbaac7c580a2ea8c3b795137f4aadf1`; checksum verified. Source/log `research/bt22` / `research/run22.log` (baseline for patch0019; no nested .git). New driver/config sources match CI exactly.
- **CPU wait FIXED in QEMU**: SweetCPU uses legacy IOCPU, validates single boot CPU, ml_processor_register -> processor_start -> initCPU real SGI1 -> scheduler/IOKit completion -> ml_set_max_cpus. It does NOT force a flag or skip a wait. CPU APIs passed: Running CPU0, processor_array[0] association, SGI signalling enabled, name, unsupported secondary-start error (`research/check-cpu18.gdb` / `.log`, `research/q0018-api`). Single-core only; SMP and suspend unsupported. Two-CPU topology fails explicitly (`research/q0018-smp`).
- **Next blocker reproduced in 45s QEMU** (`research/q0018-long`, zero unknown glyphs): BSD initialization reaches MAC framework, network mcache and `mbinit: done`, then **`pthread kernel extension not loaded (function table is NULL). @pthread_shims.c:318`**. Do not bypass pthread_init: find/integrate the matching open-source libpthread kernel implementation and register its real function table. A 12s run `research/q0018` looked panic-free before the 30s IORTC wait elapsed; use >=45s or GDB checkpoints for the next iteration. No userland/root filesystem boot yet.
- **Phone 0018 TEMPORARILY BOOTED** 2026-10-15 **15:31:15 UTC**: exactly one FASTBOOT device verified product sweet; send OKAY0.400s, boot OKAY0.134s, total0.539s, exit0. Local log `research/boot0018.log`. This confirms bootloader acceptance only. User was asked for a photo; await it, DO NOT reboot the phone again before their observation. No flashing performed.
- Current hardware image `shim/out/shim-boot-0018.img`, **16,437,248 bytes**, SHA256 **`b7a23595d143a76c72c9fe2cfcc5d77a8f16987b5af1a2703bbffdfa6922908c`**. Phone ADT/payload `shim/out/sweet-0018.adt` / `shim/out/payload-0018.bin` (timer19), unpacked ramdisk exactly matches payload (`shim/out/check-0018`). EntryPA0xb146b488; kernelendPA0xb1ffc000; boot_argsPA0xb2000000/top0xb2004000. Command line `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`.
- QEMU payload/ADT `research/q0018.bin` / `research/q0018.adt` (timer27). Run `python3 tools/qemu-sweet.py research/q0018.bin research/NEW-OUT --secs 45 --kernel xnu/out-0018/kernel.development.sweet --fail-on-panic`; fresh ADT seed for a new payload. Output fb.png/fb.txt/regs.txt/qemu.log/result.json. Visible panic exit2; blank/incomplete decode exit3; no_panic_observed is snapshot-only, not successful boot. -noprogress prevents the graphical indicator corrupting console text. Qualcomm XPU/bootloader/panel and SMC PSCI still need physical validation.
- Patches0014-0017 fixed PRNG registration/direct SHA256, explicit unavailable trust-cache service with rejected loads/no matches, built-in SweetPlatformExpert, and timer PPI from ADT (phone19/default19, QEMU27). All their checks/artifacts are preserved in the history below. CURRENT SWEET has NO USE_APPLEARMSMP; do not assume gCPUIC/gAIC/gPMGR AppleARMSMP globals exist.
- Local single-file checker: tools/xnu-cc.py research/run22.log research/bt22 FILTER --per-file, output via XNU_CC_OBJDIR. Patch checker `research/check-patch-order.py` applies all18 via temporary index, matches sandbox sources. Sandbox for0018 `research/bt21/xnu`, originals `research/pre0018`, objects `research/cpu-objs`. First compiler issues were missing machine/atomic.h and nonexistent getNameSymbol; fixed and both TUs compiled successfully before CI. Fixtures/artifacts under research are local-only/ignored.
- GDB: mask int(register)&((1<<64)-1) for unsigned kernel pointers; use function-entry manual-call return traps, discard manipulated guests. No QEMU fixture is intentionally left running.

### Earlier active handoff snapshot (superseded)


- **0018 milestone:** Actions `38760004398` PASSED (3m56s), checksums passed, new CPU/build files byte-match CI tree. Kernel `xnu/out-0018/kernel.development.sweet`, SHA256 `b3c8d59acc88f93a2c836eb2527a05ed4fbaac7c580a2ea8c3b795137f4aadf1`; log/tree `research/run22.log` / `research/bt22`. QEMU `research/q0018` 12s: boot CPU registered, SGI1 verified, CPU initialization complete, **BSD initialization entered** (copyright, MAC framework, buffer headers), no panic/zero unknown glyphs. Direct CPU API checks PASS (`research/check-cpu18.gdb`, `.log`, `research/q0018-api`): CPU0 Running, processor matches processor_array[0], real SGI enabled, CPU name correct, secondary-start returns KERN_NOT_SUPPORTED. Two-CPU ADT correctly panics before registration (`research/q0018-smp`). Longer 45s run `research/q0018-long` still running; next BSD wait/fault not yet identified.
- **Prepared 0018 phone image:** `shim/out/shim-boot-0018.img`, 16,437,248 bytes, SHA256 `b7a23595d143a76c72c9fe2cfcc5d77a8f16987b5af1a2703bbffdfa6922908c`. Phone ADT/payload `shim/out/sweet-0018.adt` / `shim/out/payload-0018.bin`, usual debug args with cpus=1 and -noprogress. Unpacked ramdisk byte-compared (`shim/out/check-0018`). Entry PA remains 0xb146b488; kernel end PA 0xb1ffc000, boot_args 0xb2000000/top0xb2004000. User reports FASTBOOT+USB ready; read-only check found exactly one product sweet. NEXT: temporary fastboot boot of this verified image, record send/boot results, then await hardware photo without rebooting again.
- Patch 0018 committed/pushed **`e7d9550`**; Actions **`38760004398`** queued/running: https://github.com/dipa-studio/ios-sweet/actions/runs/38760004398. Do not launch a duplicate run.
- Active continuation: patch **0018** implemented in `iokit/Kernel/arm/SweetCPU.cpp` + arm64 source list + exact qcom,kryo470 personality. Keeps legacy IOCPU, accepts ONLY the single boot CPU, fills ml_processor_info from parsed topology with CPU object as cpu_id, calls ml_processor_register and processor_start. initCPU sends SGI1 via ICC_SGI1R_EL1 and waits (1-second deadline) for real cpu_signal_handler to clear SIGPdisabled. Only after successful startup calls ml_cpu_init_completed/cpusRunning and publishes completion/max CPUs. Secondary startup/suspend are explicitly unsupported. Local C++ compile passed for both TUs (`research/cpu-objs`), all imports resolve, object contains dsb ishst / ICC_SGI1R / isb; all18 patches apply in order and match sources. Sandbox `research/bt21/xnu`, originals `research/pre0018`; next CI artifacts should use `xnu/out-0018`, `research/bt22`, `research/run22.log`. User has the phone available; first run QEMU, then prepare/temporarily boot useful hardware progress.
- Goal: iOS 16 generation XNU on Redmi Note 10 Pro / sweet. User wants persistent progress, commits, kernel builds via `gh` Actions, and this handoff kept current across agent switches. Temporary `fastboot boot` only; preserve Android and backups.
- Latest kernel implementation: **`aa3f991`**, patches **0001-0017**. All four new Actions builds PASSED: 0014 `38748543058` (4m0s), 0015 `38749549779` (4m3s), 0016 `38750733996` (4m3s), 0017 **`38751507437` (4m7s)**. Latest: https://github.com/dipa-studio/ios-sweet/actions/runs/38751507437. No build is pending.
- **Current blocker: CPU initialization has no SWEET CPU driver.** QEMU registers SweetPlatformExpert, then kernel_bootstrap_thread waits in **kperf_init_early -> ml_wait_max_cpus**. Confirmed via actual-kernel GDB call stack (`research/locate-cpu-wait2.log` / `.symbols`) and normal-run `max_cpus_initialized == 2` (MAX_CPUS_WAIT). Do not force the flag or remove the wait. Next implement real CPU registration and completion using XNU's CPU/processor interfaces. CURRENT SWEET uses legacy IOCPU (`USE_APPLEARMSMP` is absent); enabling AppleARMSMP is a separate architectural change requiring GIC/PMGR services. No userland/root filesystem boot yet.
- Fixed this session: PC=0 unregistered PRNG callback (0014, built-in HMAC-SHA256 provider + direct entropy/write_random hashing); absent Image4/AMFI trust-cache service (0015, unavailable runtime, loads rejected and queries no-match); missing platform driver (0016, SweetPlatformExpert exact personality); incorrect QEMU timer IRQ (0017, validated ADT PPI property, phone default19/QEMU27).
- **Latest kernel** `xnu/out-0017/kernel.development.sweet`, SHA256 `055a80190ab998b4df9203f1102072dcc78faad1779a537a514e522b682b582f`. Buildtree/log **`research/bt21` / `research/run21.log`**; all nine changed C/C++/header/config files byte-match local checked sources. Checksums passed. Entry PA `0xb146b488`, kernel end PA `0xb1ff4000`. Preferred baseline for patch 0018: `research/bt21/xnu` (no nested .git).
- **QEMU verified**: `research/q0017-noprogress` ran **30 seconds**, no visible panic, **zero unknown glyphs**, IRQ exceptions returned normally (4 IRQs, tickless idle). It still waits for CPU completion, so this is NOT a completed boot. Earlier 15s run `research/q0017` captured 122 IRQs, timer value27, GICR_ISENABLER0 `0x08000002`, and CPU WAIT; graphical progress overlay corrupted 13 glyphs. Add **`-noprogress`** to keep the console readable. New runner classifies incomplete/blank decoding explicitly (exit3 with --fail-on-panic), visible panic exits2. Snapshot-only; use regs/GDB to diagnose stalls.
- Current QEMU payload/ADT: **`research/q0017-noprogress.bin` / `research/q0017.adt`**. Run: `python3 tools/qemu-sweet.py research/q0017-noprogress.bin research/NEW-OUT --secs 30 --kernel xnu/out-0017/kernel.development.sweet --fail-on-panic`. Generate fresh seed with mkadt for a new payload. QEMU virt models generic ARM execution, not Qualcomm XPU/bootloader/panel or the phone's SMC PSCI conduit.
- **Prepared phone image**: **`shim/out/shim-boot-0017.img`**, 16,416,768 bytes, SHA256 `51ff7fe30b4a6668c3452ffe1da922c5ac30cb8de60625c2a652587ecbd0ec92`. Phone ADT/payload `shim/out/sweet-0017.adt` / `shim/out/payload-0017.bin` (timer19). Unpacked ramdisk exactly matches payload (`shim/out/check-0017`). Command line **`debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`**. NOT sent to phone this session: known CPU-driver wait should be addressed in QEMU first. Last actual phone boot remains 0013; user's latest photo `IMG_20261015_160033.jpg` confirmed the old PRNG PC=0 panic.
- Direct QEMU/GDB API checks: PRNG 600-byte chunking, buffer bounds, changing output, zero-length reads/writes, user reseed, contended refresh, generator1 init/output PASS again on latest0017 (`research/check-prng17.gdb` / `.log`, guest `research/q0017-api`). Trust-cache unavailable-service/argument/output cases PASS on0015 (`research/check-trustcache.gdb` / `.log`). Platform registration + target/product normal/truncated/zero/null/bounds PASS on0016 (`research/check-platform.gdb`, `research/check-platform3.log`). Different platform ID correctly retains IOPanicPlatform fallback (`research/q0016-negative`). Timer PPI32 and size2 correctly panic (`research/q0017-badppi`, `research/q0017-badsize`); omitted property selects19 (`research/q0017-default`). These are API/bring-up checks, not crypto certification or SMP scheduling validation.
- Local checker **`research/check-patch-order.py`** verifies all17 patches and changed source equality using a temporary upstream git index. Fixtures/logs/artifacts under research are local-only and ignored. For GDB unsigned kernel pointers, mask `int(register_value) & ((1<<64)-1)`; x30/x29 may be rendered signed. Stop at a function entry for manual-call return traps, and discard each manipulated guest after API tests. All fixture QEMU guests have been stopped.


- User wants persistent progress toward iOS 16, commits for completed changes, builds through `gh` / GitHub Actions.
- Keep this file current at every milestone so another agent can resume immediately, including when usage limits interrupt a session.
- Patch 0017 committed/pushed `aa3f991`, Actions `38751507437` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38751507437. Next artifacts: xnu/out-0017, research/bt21, research/run21.log. Do not duplicate.
- Patch 0016 kernel downloaded/checksum verified: SHA256 `d06336c54baa06e0df6561a8bd7df98a9b9f7502c9381c62d1a44c045cd1ce46`, `xnu/out-0016/kernel.development.sweet`; buildtree/log `research/bt20` / `research/run20.log`. QEMU `research/q0016` (10s) prints platform expert registered, zero unknown glyphs, no panic observed BUT stalls (timer mapping still wrong until 0017). Direct actual-kernel GDB tests passed for registered instance and target/product names, including maxLength=1/0 and NULL, sentinels intact (`research/check-platform.gdb`, `research/check-platform3.log`, `research/q0016-api3`). First two fixture attempts used premature/wrong return breakpoints; discarded, corrected fixture uses start-return observation then a function-entry return trap. No phone boot yet.
- Patch 0016 CI `38750733996` PASSED (4m3s); artifacts not yet downloaded/booted. Patch 0017 prepared to fix QEMU timer fidelity BEFORE interpreting future no-panic/stall runs: actual `qemu-system-aarch64 -M virt,gic-version=3,dumpdtb=research/qemu-virt.dtb ...` timer property has virtual PPI 11 => INTID 27, while phone uses INTID 19. Kernel formerly hardcoded 19. New optional /arm-io/gic virtual-timer-intid property selects the PPI (validate exact u32 and 16..31); missing property retains phone default 19. One RO-late global drives GIC enable and sleh_irq dispatch. tools/mkadt.py emits phone19/QEMU27. Both C TUs compile (`research/timer-objs`), ADT serialize/parse checks confirm values/addresses, all 17 patches apply and match. Sandbox `research/bt19/xnu`, originals `research/pre0017`; initial local sleh compile failed due read-only exported header not updated, fixed export and BOTH recompiled successfully. CI exports normally.
- Architecture correction for next agent: CURRENT SWEET board_config does NOT define USE_APPLEARMSMP; it compiles the legacy IOCPU path, not cpu_boot_thread/IOPMGR AppleARMSMP. Existing roadmap mentions AppleARMSMP as a future approach. Do not look for gCPUIC/gAIC/gPMGR globals in the current kernel: they are absent. Determine the actual CPU-init wait after platform registration before choosing the next driver architecture.
- Patch 0016 committed/pushed as `0dcdf5c`; Actions `38750733996` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38750733996. Next artifacts: `xnu/out-0016`, `research/bt20`, `research/run20.log`.
- Patch 0016 implemented: new `iokit/Kernel/arm/SweetPlatformExpert.cpp`, arm64 source list, built-in personality in KernelConfigTables.cpp guarded by ARM64_BOARD_CONFIG_SWEET. Matches only xiaomi,sweet at score 10000, keeps IOPanicPlatform fallback for other hardware. Uses IODTPlatformExpert base initialization/power domain and createNubs CPU logical-ID annotation; overrides top-level publishing because base requires nonexistent Apple NVRAM /options. Publishes real CPU/top-level nodes, provides bounded target/product names, and registers the platform service. GIC/PMGR and arm-io child-bus drivers remain separate work. Both C++ TUs compile (`research/platform-objs`), all imports resolve against 0015/own objects, all 16 patches apply and sources match. Sandbox `research/bt19/xnu`; originals `research/pre0016`. NEXT: full Actions/QEMU; inspect CPU boot waits after the platform registers, do not equate absence of panic with successful boot.
- Patch 0015 CI `38749549779` PASSED (4m3s), checksum verified. Kernel `xnu/out-0015/kernel.development.sweet`, SHA256 `ca1b424a596c7058550ad1659080a333e7643270f019656401d80bf2b876645f`; buildtree/log `research/bt19` / `research/run19.log`. QEMU `research/q0015` (10s, zero unknown glyphs) passes trust-cache handling and machine lockdown, then panics `Unable to find driver for this platform: "xiaomi,sweet" @IOPlatformExpert.cpp:2319` (IOPanicPlatform fallback). Next concrete work: add a built-in SWEET IODTPlatformExpert personality/class; keep the fallback for mismatched platforms. No phone boot yet.
- Direct trust-cache API checks PASSED in the actual 0015 kernel under QEMU/GDB (`research/check-trustcache.gdb`, `research/check-trustcache.log`, `research/q0015-api`): runtime pointers NULL, hash/UUID queries return NOT_FOUND, typed/untyped/legacy loads return NOT_SUPPORTED, capabilities outputs zero and bounds preserved, invalid-argument cases still reject. Second PRNG check also verifies contended refresh returns immediately (`research/check-prng2.log`, `research/q0014-api2`).
- Patch 0015 committed/pushed `8f851d4`, Actions run `38749549779` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38749549779. Do not duplicate.
- Direct PRNG API checks passed in the REAL 0014 kernel under QEMU/GDB, stopped before trust-cache init (`research/check-prng.gdb`, log `research/check-prng.log`, guest `research/q0014-api`). Invoked read_random for 600 bytes (chunking and buffer sentinel intact), repeated output differed, zero-length read/write succeeded, write_random(64-byte input) succeeded, secondary generator 1 initialized and generated distinct output. QEMU log has no exceptions during these checks; guest was discarded after the tests. This tests API behavior, not a cryptographic certification or SMP scheduling.
- Patch 0015 implemented in `bsd/kern/kern_trustcache.c`: SWEET with missing Image4/AMFI marks both runtime pointers NULL and logs service unavailability. Existing static loader handles NULL. Public load APIs return KERN_NOT_SUPPORTED; hash/UUID queries return KERN_NOT_FOUND; capabilities outputs are zero with KERN_NOT_SUPPORTED. Invalid-input checks remain, and Apple paths/available-provider initialization retain existing behavior. No trust is granted. Local arm64 compile passed (`research/trustcache-objs`), all 15 patches apply and sources match. Sandbox `research/bt18/xnu`, baseline `research/pre0015`. Next: Actions/QEMU and direct unavailable-service API checks using GDB.
- Patch 0014 CI `38748543058` PASSED (4m0s), artifact checksum passed. Kernel `xnu/out-0014/kernel.development.sweet`, SHA256 `741de20c851755d333759d7e668346f3edb4f325efac4cc7c142d80d1f5ff75c`; buildtree/log `research/bt18` / `research/run18.log`. QEMU run `research/q0014` (10s, zero unknown glyphs) prints `SWEET PRNG: HMAC-SHA256 registered`, passes commpage initialization, loads vnguard policy, THEN panics `image4 interface not available @kern_trustcache.c:253`. PC=0 fault FIXED IN QEMU. No new phone boot performed.
- Next work: SWEET currently has neither AppleImage4 nor AMFI. `trust_cache_runtime_init` unconditionally requires both; unlike BCM2837, SWEET enters this startup path. Investigate an explicitly unavailable trust-cache runtime with rejected loads/no query matches while providers are absent; preserve all Apple-platform checks. Merely skipping the startup call would leave later AMFI/IMG4 dereferences unsafe. Existing load_static_trust_cache already handles trust_cache_rt == NULL.
- QEMU runner now supports `--kernel MATCHING_KERNEL --fail-on-panic`: runtime font extraction from the payload produces exact `fb.txt`, plus `result.json`; a visible panic returns 2. Baseline 0013 re-run `research/q0013-text` detects the same NULL callback panic with zero unknown glyphs. Synthetic glyph roundtrip (including literal `?`) and invalid-VA rejection passed. Screen rows remain circular, not a full log; `no_panic_observed` does not prove successful boot. README has the invocation.
- Patch 0014 committed/pushed as `be61f99`; Actions run `38748543058` is running: https://github.com/dipa-studio/ios-sweet/actions/runs/38748543058. Do not start a duplicate build.
- 2026-10-15 active: hardware photo `IMG_20261015_160033.jpg` confirms the same PC=0 instruction-fetch abort as QEMU (LR `0xfffffe0007443fe4` = read_random). Independently reproduced with kernel 0013 in `research/q0013` (8-second run); prior allocator fix works. Latest tooling commit reviewed: `8d66d2d`.
- Patch 0014 implemented: registers a built-in HMAC-SHA256 DRBG provider at EARLY_BOOT/FIRST, before commpage creation. A shared mutex serializes output/reseed across CPUs (correctness first; no per-CPU scaling yet), initgen validates CPU identities, refresh uses try-lock and the existing entropy filter/health tests. SWEET entropy accumulation and write_random now use the built-in SHA256 directly; no incomplete g_crypto_funcs table is registered. The existing bootloader-seed requirement remains enforced.
- Local validation: both PRNG translation units compile to arm64 objects in `research/prng-objs`; no SHA256 wrapper imports remain. All 14 patches apply in CI order and resulting PRNG sources match local inputs. Sandbox `research/bt17/xnu`, originals `research/pre0014`, checker `research/check-patch-order.py`. NEXT: Actions kernel build, download to `xnu/out-0014`, run the QEMU payload before requesting another phone boot. Baseline QEMU ADT/payload are `research/q0013.adt` / `research/q0013.bin`.
- 2026-10-15 08:15 QEMU EMULATION WORKS (`tools/qemu-sweet.py`, see "QEMU emulation" below). Patch 0013 VERIFIED in QEMU: boot passes kmem_crypto_init and ulock_initialize. NEXT BLOCKER (reproduced in QEMU, expected on hardware too): `pmap_create_commpages -> random() -> RandomULong -> read_random -> prng_funcs.refresh == NULL` (instruction fetch abort at pc 0, lr read_random+0x34). Nobody calls `register_and_init_prng` (closed corecrypto kext does it on Apple). Fix = patch 0014: SWEET-registered cckprng_funcs provider (osfmk/prng/prng_random.c); note random_cpu_init also panics while !prng_ready. The 07:26 hardware boot of 0013 will most likely show this same panic.
- Previous hardware boot: patch 0013 (`a3a46e2`) CI `38686345689` PASSED (3m44s), image `shim/out/shim-boot-0013.img` was temporarily booted on 2026-10-15 at 05:26 UTC: send OKAY (0.407s), boot OKAY (0.134s), total 0.546s. Superseded by the hardware/QEMU PC=0 observation and patch 0014 work above.
- Latest kernel implementation commit: `8f851d4`. Latest successful kernel CI: `38749549779` (patch 0015), https://github.com/dipa-studio/ios-sweet/actions/runs/38749549779.
- CURRENT image: `shim/out/shim-boot-0013.img`, 16,412,672 bytes, SHA256 `110d1c46aee4b60253db24b6535e9781c4cf0fd25ca2a70e9016cf81378cea25`. Kernel `xnu/out-0013/kernel.development.sweet`, SHA256 `f0b1d375995316c550ce7014ff234d8271e9b9ac2857795ceff41b76ba2cd740`, plain arm64. CI log confirms 0013 applied; checksums passed. Entry PA `0xb146b488`, kernel end PA `0xb1ff4000`.
- Current log/buildtree: `research/run17.log`, `research/bt17` (extracted, no nested .git; preferred baseline for patch 0014). Payload/ADT: `shim/out/payload-0013.bin`, `shim/out/sweet-0013.adt` (includes /defaults). Unpacked ramdisk byte-compared with payload in `shim/out/check-0013`.
- Patch-0012 original image: `shim/out/shim-boot-0012.img`, 16,412,672 bytes, SHA256 `cf4b8ec4a65a51888d71c17d09cd0831d6b761b90e2531fdb8e575c32f4fd24a`. Kernel `xnu/out-0012/kernel.development.sweet`, SHA256 `69b78f49f6459cc63a0af44e7cf73c1779ef72130ef72b12ae86c88183ffc742`; checksums passed and sweet_early_relocate symbol present. Entry PA remains `0xb146b488`, kernel end PA `0xb1ff4000`.
- Patch-0012 log/tree: `research/run16.log`, `research/bt16` (extracted, no nested .git; preferred baseline for next patch). CI log confirms 0012 applied. Payload `shim/out/payload-0012.bin`, ADT `shim/out/sweet-0012.adt`; packed ramdisk byte-compared with payload in `shim/out/check-0012`.
- Active payload command line: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam`.
- Latest observed photo: `/home/dipa/Downloads/IMG_20261015_071346.jpg` (local only). Stages 9 (kernel framebuffer VA), 10 (TTBR0 off/TLB flush), 11 (physmap table pointers) and 12 (calling pmap_bootstrap) all visible. Persistent diagnostics are VERIFIED ON HARDWARE.
- pmap.c:1987 is the assert after SecureDTLookupEntry(NULL, "/defaults", &entry). The pmap-max-asids property itself is optional; an empty /defaults uses XNU's MAX_ASIDS. Do not bypass the assertion or guess an ASID limit.
- Previous payload-only fix image: `shim/out/shim-boot-0012-defaults.img`, SHA256 `3ff61a268853c6ea7cbf284833f1346a1d791980ca366b6e1a215a86e040512b` (16,412,672 bytes). Same kernel/CI as 0012; ADT 2516 bytes (`shim/out/sweet-0012-defaults.adt`), root /defaults present with no ASID override. Payload `shim/out/payload-0012-defaults.bin`; unpacked ramdisk exactly matches payload (`shim/out/check-0012-defaults`). This boot reached the allocator crypto NULL-pointer fault below.
- Latest hardware photo: `/home/dipa/Downloads/IMG_20261015_071608.jpg` (local only). Normal serial framebuffer console works. VM bootstrap/zone initialization, logging, scheduler, IPC, KDP and ulock_initialize print before the kmem_crypto_init data abort. gPanicBase warnings are expected because PLATFORM_PANIC_LOG_DISABLED is configured, and are not the faulting call.
- Faulting instruction: `ldr x0, [x8, #0x150]` in crypto_random_kmem_ctx_size; x8 = NULL g_crypto_funcs. Source: libkern/crypto/corecrypto_rand.c and osfmk/vm/vm_kern.c:2448. rand.h explicitly permits NON-cryptographic kmem RNGs, but requires no locking in generation and context size <=256. Do not substitute read_random here: the global PRNG provider is also unregistered and kmem generation must remain lock-free. early_random may seed contexts during single-CPU bootstrap; it uses the built-in HMAC-SHA256 DRBG with the host-generated ADT seed.
- Patch 0013 keeps the replacement entirely private to vm_kern.c: SplitMix64 state is 8 bytes per CPU/sizeclass, initialized using early_random. Uniform selection uses rejection sampling to avoid modulo bias. Other platforms retain the original corecrypto calls; SWEET's generic crypto APIs/registration remain untouched. Reference: https://prng.di.unimi.it/splitmix64.c (Sebastiano Vigna, public domain).
- Validation: vm_kern.c compiles to arm64 (`research/kmem-rng-objs`, using `research/run16.log` + `research/bt16`). Undefined symbols include early_random and NO crypto_random_* references. All 13 patches apply in CI order and match the checked source. Original saved as `research/vm_kern.pre0013.c`.
- RNG host checks: extracted actual new helper in `research/kmem-rng-check.c`; 16,384 outputs match the author's downloaded reference (`research/splitmix64-reference.c`), 147,456 bounded outputs satisfy their limits (including 1 and UINT64_MAX), and a forced rejection advances correctly. Full kernel crypto services and the registered kernel PRNG provider remain future work; this patch only supplies the allocator RNG contract.
- Patch-0011 artifacts: kernel `xnu/out-0011/kernel.development.sweet`, log `research/run15.log`, extracted buildtree `research/bt15` (no nested .git). CI log confirms patch 0011 applied; artifact checksums passed. Kernel is plain arm64, entry VA `0xfffffe000746b488` -> PA `0xb146b488`, kernel end PA still `0xb1ff4000`.
- Patch-0011 image: 16,412,672 bytes, SHA256 `29ad5cbfc752473de4af2c471a24a8b34f92da4bff5afec65c614b90cd3ad53a`. Kernel SHA256 `8ac3a956894b09f7bd0d890de8c5de38c65513287feb1e1bcd12db8ca772ee5c`. Payload/ADT in `shim/out/payload-0011.bin`, `shim/out/sweet-0011.adt`. Header unpacked/checked in `shim/out/check-0011`.
- First patch-0011 attempt timed out waiting for FASTBOOT; superseded by the successful send/boot recorded above. Do not repeat the boot before the user reports the current screen.
- Patch-0011 photo: `/home/dipa/Downloads/IMG_20261015_070218.jpg` (local only). Visible stages 1-8 and old red shim text; entry PA B146B488, boot args PA B1FF8000 / top B1FFC000. No evidence yet locating execution after stage 8.
- Patch-0012 sandbox: `research/bt15/xnu` (NO nested .git). Proposed permanent debug VA: VM_MIN_KERNEL_ADDRESS + ARM_TT_L2_SIZE, in the reserved gap below gVirtBase and above low globals; map the same PA framebuffer as Normal-NC in the final TTBR1 before arm_vm_physmap_init changes phystokv(). Keep the early panic sink until normal kprintf startup.
- Patch 0012 validation: all 4 changed C translation units compiled to arm64 objects in `research/post-ttbr0-objs`; internal header export added to osfmk/arm64/Makefile and recreated locally in EXPORT_HDRS for pe_serial.c. All 12 patches apply in CI order and match all 6 edited files. Baselines are saved under `research/pre0012/`.
- Actual mapping-helper host model (`research/early-map-check.c`, barrier stubbed only for host compilation) confirms: VA `0xfffffe0002000000`, L1 index 2016, L2 index 1; descriptor `0x006000009c000605` = framebuffer PA, Normal-NC, outer-shareable, EL1 RW, PXN+UXN. All other L2 entries preserved. The gap is excluded by ARM_LARGE_MEMORY's pmap_virtual_region(0).
- Next boot command line MUST add `-enable_kprintf_spam`: DEVELOPMENT disables kprintf_output by default even when DB_KPRT is set (`pexpert/arm/pe_kprintf.c`). Planned command line: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam`.

### Patch 0012 screen legend (after original stages 1-8)
- 9: kernel framebuffer VA live; 10: TTBR0 off / TLB flushed; 11: physmap pointers rebound.
- 12: calling pmap_bootstrap; 13: pmap_bootstrap returned; 14: early I/O page tables ready; 15: arm_vm_init returned.
- 16: calling serial_init; 17: fbcon config read / mapping; 18: fbcon mapping returned; 19: serial_init returned; 20: kprintf startup complete.
- Normal serial initialization clears the screen, so earlier stages may disappear before 19. If serial exists, early console disables after 20; otherwise early panic output stays enabled.
- Local source sandbox: `research/bt13/xnu` (git baseline `623b060`, patches 0001-0008 already in baseline; uncommitted export edits correspond to patch 0009). Preserve those edits when producing patch 0010.
- Previous compile log/tree: `research/run13.log`, `research/bt13`; previous kernel: `xnu/out/kernel.development.sweet`. New successful log/tree: `research/run14.log`, `research/bt14`; new kernel: `xnu/out-0010/kernel.development.sweet`.
- Current device access: patch-0012 image was temporarily started from FASTBOOT; no adb connection is expected. Never flash partitions for bring-up; use `fastboot boot` with the shim image.
- Patch `0010` lives in `xnu/patches/0010-sweet-early-framebuffer-debug.patch`. Its exact compiled sources are under `research/bt13/xnu`; generated objects are in `research/early-objs`.
- Local checks passed: all 5 changed/new translation units compiled to arm64 Mach-O objects; new console only imports `_doprnt` and `iso_font` (both exist in the previous kernel). All 10 patches applied to a temporary upstream git index in CI order, and all 7 resulting changed source files matched the local compile inputs.
- Reproduce changed-file compilation: `XNU_CC_OBJDIR="$PWD/research/early-objs" python3 tools/xnu-cc.py research/run13.log research/bt13 arm_init.c arm_vm_init.c kern/debug.c arm64/start.s osfmk/arm64/sweet_early.c --per-file` (create the output directory first). The helper now accepts explicit new source paths absent from the old artifact's Makefiles and rejects empty selections.
- Device command result: `adb reboot bootloader`, then `timeout 30s fastboot boot shim/out/shim-boot-0010.img`: send OKAY (16028 KB), boot OKAY, total 0.541s. This confirms bootloader acceptance only, not XNU progress.
- The successful boot above was on 2026-10-14. On 2026-10-15, `timeout 45s fastboot boot ...` timed out waiting for a device; no image was sent. Boot image SHA256 rechecked and unchanged. No new build is needed to repeat the trial.
- Earlier retry: `timeout 90s fastboot boot shim/out/shim-boot-0010.img` timed out (exit 124). This is superseded by the successful 2026-10-15 repeat boot recorded above; do not repeat it until the user reports the screen.
- User observation confirms MMU-on C entry, platform expert, CPU topology/bootstrap, startup bootstrap and cpu_init all complete. Failure is within arm_vm_physmap_init (non-XNU_MONITOR branch), before stage 8 / TTBR0 teardown. Old red shim text remains behind the early console; this is expected because only written rows are cleared.
- New edit/compile sandbox is `research/bt14/xnu` (extracted artifact, NO nested .git; `git diff` there would act on the parent project). Use a saved baseline file / generated unified diff, or explicitly initialize a local baseline before editing. `research/bt13/xnu` does have its own baseline git repo.
- Exact user-reported panic: `arm_vm_init.c:1606 Assertion failed: (temp_ptov_table[ptov_index - 1].va + temp_ptov_table[ptov_index - 1].len) <= physmap_end`.
- Root cause: MacOSX build sets `ARM_LARGE_MEMORY=1`; `XNU_MONITOR` is off. Block alignment in arm_vm_physmap_slide can add gaps, but the non-PPL large-memory physmap_end omitted the padding already present in the small-memory branch. Patch 0011 reserves PTOV_TABLE_SIZE*ARM_TT_TWIG_SIZE (8*32MB) in both the aperture bound and its L1 allocation; monitor/PPL builds retain zero padding. The assertion is preserved.
- Validation: `arm_vm_init.c` compiled to an arm64 object using `research/run14.log` + `research/bt14` (object in `research/physmap-objs`). All 11 patches apply in CI order and produce exactly that source. Host harness `research/physmap-check.c` extracts the real XNU slide function with page-table-write stubs: all 65,536 page-aligned slides within 1GB checked against the current kernel memory layout; old bound fails 65,504 cases, padded bound fails zero; worst overrun 0x1ffc000 bytes. Baseline source saved as `research/arm_vm_init.pre0011.c`.
- CI: https://github.com/dipa-studio/ios-sweet/actions/runs/38638702083 (success; artifacts and full log downloaded).
- New image: `shim/out/shim-boot-0010.img` (16,412,672 bytes, SHA256 `ed2c270e0081bad5ff517be415f9bfe8805463aea7866732203fa97ac737e64e`). Previous image preserved as `shim/out/shim-boot-pre0010.img`.
- New kernel SHA256: `3ee05270cc291c49589a101678f904b1b69cb2f2575e05398bce8a4e052f409a`. Artifact checksums passed; arm64 (not arm64e), early-console symbols present. Payload entry VA `0xfffffe000746a488` -> PA `0xb146a488`; kernel end PA `0xb1ff4000`. Command line remains `debug=0xc serial=3 cpus=1 keepsyms=1`.

### Patch 0010 screen legend
- Bottom-left white 64x32 tile: assembly entered `start_first_cpu`, before page tables/MMU.
- Text `SWEET EARLY 1`: entered `arm_init` with MMU on; 2: platform expert done; 3: CPU topology done; 4: CPU bootstrap done; 5: startup bootstrap done; 6: CPU init done; 7: entering `arm_vm_init`; 8: leaving bootstrap TTBR0.
- `SWEET EARLY PANIC:` prints a copy of panic arguments before normal panic handling needs per-CPU/thread state.
- In patches 0010/0011 the console disabled before TTBR0 invalidation; patch 0012 replaces that with a persistent kernel VA alias and diagnostics through normal serial/kprintf startup (see its legend above).
- Screen contents require a physical observation from the user: adb cannot capture a framebuffer after Android has been replaced by a bare-metal kernel.

## QEMU emulation (2026-10-15)
- `tools/mkadt.py OUT.adt --qemu` = same ADT with QEMU virt GICD 0x08000000 / GICR 0x080a0000 / CNTFRQ 62.5 MHz.
- `tools/qemu-sweet.py PAYLOAD OUTDIR [--secs N] [--hmp "x /8gx ADDR"] [--gdb]`: host-side copy of shim/loader.c
  (segments + ADT + boot_args at their PAs, 6-instruction stub sets x0 and jumps), `-M virt,gic-version=3 -cpu cortex-a76`
  (same ID_AA64MMFR0 as Kryo 470), 4G RAM so 0x9c000000 fb and 0xb0000000 kernel are plain RAM.
  Outputs `fb.png` (the screen), `regs.txt`, `qemu.log` (exceptions with ESR/FAR/ELR). `--gdb` halts with a stub on :1234
  (system `gdb` + `set architecture aarch64`, `hbreak *VA` works with the MMU on).
- Not emulated: Qualcomm XPUs, ABL, real panel, PSCI conduit (QEMU virt uses hvc). Hardware still decides those.
- Example: `python3 tools/mkadt.py /tmp/q.adt --qemu && python3 tools/mkpayload.py xnu/out-0013/kernel.development.sweet /tmp/q.adt /tmp/pq.bin --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam' && python3 tools/qemu-sweet.py /tmp/pq.bin /tmp/q`

## Layout
- `backup/`  partition dumps + full sdb..sdf LUNs, `SHA256SUMS` (all verified on-device == local)
- `dtb/`     live FDT (from OrangeFox), PixelOS boot.img dtb, dtbo, dts versions
- `shim/`    bare-metal boot shim (`./build.sh` -> `out/shim-boot.img`)
- `research/` mainline sm7150 dts, XNU pe_fiq.c etc, PocketDarwin patches
- `tools/unpack_bootv2.py`

## Device access
- No root in PixelOS 17 (user build, adb root disabled). Root = `fastboot boot recovery/recovery.img` (OrangeFox R12.0_2, temp boot, not flashed).
- `fastboot boot` works for stock boot.img, OrangeFox, and our shim.
- Shim resets itself via PSCI SYSTEM_RESET; IMEM restart_reason 0x77665500 is seen
  (bootreason=bootloader) but ABL still boots Android, so it does not stop in fastboot.

## Hardware facts (live DT + shim measurements)
- Framebuffer (ABL cont splash): 0x9c000000, 1080x2400, stride 4320, a8r8g8b8, panel is DSC *video* mode (no kick needed).
- RAM: 0x80000000+2G, 0x100000000+0xfcc00000. Live reserved-memory = PixelOS base dtb + sweet dtbo fixups.
- GICv3: GICD 0x17a00000, GICR 0x17a60000 (stride 0x20000, 8 PEs). GICD_TYPER 0x007B041D: SecurityExtn=1 (DS=0).
  ABL leaves GICD_CTLR = 0x10 (ARE_NS on, groups off). Writing 0x13 reads back 0x12: EnableGrp1A (bit1) is the one that matters.
- GIC Group 1 VERIFIED (shim 2c): vtimer INTID 19 = 30 IRQs/300ms, ptimer INTID 18 = 30, SGI 1 to self = 10/10.
  ICC_SRE=1 already, ICC_CTLR 0x8440, priority/enable writes stick. GICR_IGROUPR0 and GICD_IGROUPRn read 0 from NS
  even though Group 1 delivery works (RAZ in NS view) - do not use them as a health check.
  INTID 28 shows pending constantly (unknown PPI 12).
- Timer 19.2 MHz. Qualcomm PPI numbering: secure-phys/phys/virt/hyp = PPI 1/2/3/0 -> vtimer INTID 19, ptimer 18 (NOT 27/30).
- PSCI 1.1 via SMC, SMCCC 1.1. CPU_ON ok; SYSTEM_SUSPEND and SYSTEM_RESET2 unsupported.
- SMP: CPU_ON works for all 7 secondaries (MPIDR 0x81000n00).
- Entry EL1, MMU off, x0 = DTB (magic ok). ID_AA64MMFR0 = ...101122: 16K granule YES, 4K YES.
- No serial console: debug UART SE is in SPI mode on sweet. Screen is the only debug channel.

## XNU implications
- XNU GICv3 path (pexpert/arm/pe_fiq.c, VMAPPLE) puts the timer (PPI 27) in Group 0 = FIQ. With SecurityExtn=1,
  Group 0 is secure -> impossible from NS EL1. Need: Group 1 IRQ, ICC_IGRPEN1, INTID 19, and the timer handled in the IRQ path.
- XNU VMAPPLE PSCI uses `hvc`; sweet needs `smc`.
- PocketDarwin NonAppleGenericCpu.patch only swaps -mcpu=apple-h7 for -march=armv8-a.

## Milestone 3 (2026-10-14): 16K MMU verified
- ABL loads the Image at 0x80080000 (base 0x80000000 + 0x80000) regardless of text_offset=0.
- 16K granule, T0SZ=28 (L2 start, 32MB blocks), MAIR 0x44ff00, TCR 0x1409CB51C, PARange=2 (40-bit PA).
- Only own image pages WB (Qualcomm XPUs: never map carve-outs cacheable); fb Normal-NC; rest Device.
- AT S1E1R checks all as expected; unmapped -> translation fault L2.
- Fill fb: 110 ms (MMU off) -> 3.5 ms (NC). Memory loop 70 ms -> 0.7 ms. vtimer + SGI IRQs still fine with MMU on.

## XNU loader design notes (xnu-8796)
- Entry: `_start` -> `start_first_cpu`, x0 = boot_args (PA), MMU off, EL1. boot_args: Revision/Version 2,
  virtBase/physBase/memSize/topOfKernelData, Boot_Video (fb 0x9c000000, rowBytes 4320, 1080x2400, depth 32),
  deviceTreeP/Length (ADT), CommandLine[608], bootFlags, memSizeActual.
- start.s maps [kernel mach header .. physBase+memSize) with cacheable BLOCKS. On Qualcomm every XPU carve-out
  must therefore lie below the kernel: use physBase = 0xb0000000 (above ramdump_fb 0xaf000000+16M,
  cdsp_sec, qseecom), end before rmtfs 0xfde01000 -> memSize ~0x4d000000 for bring-up.
- Base ADT: iPhone 8 d20ap DeviceTree from iOS 16.7.16 IPSW (tools/remotezip.py + tools/adt.py; LZFSE payload).
  Template values are empty: the loader must fill chosen/*, memory-map, cpu*/reg etc. like iBoot.
- XNU build: GitHub Actions (dipa-studio/ios-sweet, xnu.yml) via blacktop/darwin-xnu-build, MACOS_VERSION=13.5.
  New-clang fixes in xnu/patches; Xcode 16 iig is incompatible (IORPC.kernelContent) -> macos-14 runner, oldest Xcode.

## Kernel architecture plan (SWEET machine config)
- First stock build (VMAPPLE) is arm64e (PAC). Kryo 470 = ARMv8.2, no PAC -> SWEET must build plain arm64
  (HAS_APPLE_PAC is only defined for __arm64e__, so arm64 drops PAC automatically).
- Template: VMAPPLE (16K pages, GICv3 code in pe_fiq.c) minus APPLEVIRTUALPLATFORM hypercalls/paravirt PAC,
  plus BCM2837 (generic ARM: no APPLE_ARM64_ARCH_FAMILY Apple sysregs). Do not link the KDK lib<cfg>.os.*.a.
- Timer: XNU expects it on FIQ (sleh_fiq -> rtclock_intr). SWEET: GIC Group 1, so sleh_irq must ack ICC_IAR1,
  route INTID 19 to the same timer path, SGIs to cpu_signal_handler, EOI via ICC_EOIR1.
- SMP/interrupts: open-source AppleARMSMP (USE_APPLEARMSMP) needs an IOInterruptController (AIC role) and an
  IOPMGR (CPU power -> PSCI CPU_ON via SMC). Plan: built-in IOKit classes (SweetGIC, SweetPMGR, platform
  expert) compiled into the kernel and matched via iokit/KernelConfigTables.cpp -> no closed kexts needed.
- Debug: xnu patch 0003 sweet-fbcon = kprintf drawn on the framebuffer (ADT node "sweet-fbcon").
- ADT /arm-io ranges must not map to parent 0 (pe_arm_get_soc_base_phys()==0 disables serial): use parent 0x1000000.

## Status 2026-10-14 late: first XNU boot attempt
- SWEET kernel builds (CI run 38635343732, patches 0001-0009). Verified offline: arm64, no PAC, no >v8.2 code,
  70300 classic relocs all in range (slide 0 = no loader work), entry = __start.
- Boot: shim loader worked (initrd 0x846F0000-0x855FE3E0, BOOTARG 0xB1FF8000, JUMP 0xB146A488) but screen stayed
  red -> xnu died/hung before serial_init (fbcon). kprintf is a no-op before STARTUP_SUB_KPRINTF.
- Historical next-step plan (patch 0010, now implemented and built; see active handoff above): early fb debug channel
  1. start.s start_first_cpu (after mov x20,x0 / mov x21,#0): PA marker band (MMU off, direct store to 0x9c000000).
  2. start.s after both create_bootstrap_mapping calls: add ONE block entry to the existing V=P L2 table
     (x25 + 2*PGBYTES; do NOT call create_bootstrap_mapping again: fb and RAM share L1 entry 0, it would replace
     the L2 table). Entry = TYPE_BLOCK|VALID|SH(OUTER)|ATTRINDX(CACHE_ATTRINDX_WRITECOMB=1)|AF|PNX|NX|0x9c000000,
     index = (va & ARM_TT_L2_INDEX_MASK) >> ARM_TT_L2_SHIFT.
  3. new osfmk/arm64/sweet_early.c (+files.arm64 entry): sweet_early_mark(n) colored bands at screen bottom and
     sweet_early_putc using iso_font via VA=PA while the bootstrap TTBR0 is live; disable before
     arm_vm_init's set_mmu_ttb(invalid_ttep) (arm_vm_init.c:2148).
  4. markers in arm_init after PE_init_platform, ml_parse_cpu_topology, cpu_bootstrap, kernel_startup_bootstrap,
     cpu_init, before arm_vm_init.
  5. panic hook at top of panic_trap_to_debugger: va_copy + _doprnt(fmt, &copy, sweet_early_putc, 16).
  Verify with tools/xnu-cc.py (compile+symbols) and patch-order simulation before the single CI run.
## 2026-10-25: fail-closed MT6897 LK entry contract

Added `duchamp/loader/mt6897_entry.c` after comparing the MT8167 LK bootshim
reference with the Duchamp firmware evidence. The gate accepts only EL1
(`CurrentEL=4`), requires `SCTLR_EL1.M/C/I` clear, and bounds the aligned FDT
pointer received in `x0` to a caller-provided live-memory range. EL2 and
MMU/cache-on entry fail closed. This is host-tested metadata validation, not a
phone boot or proof that LK supplies the same register contract.

## 2026-10-25: Duchamp diagnostic bootshim host build

Added `duchamp/bootshim`, a position-independent ARM64 Linux Image diagnostic.
It preserves LK `x0` through `x3` and the old stack pointer, accepts only EL1,
requires `SCTLR_EL1.M/C/I` clear, validates an aligned FDT header in the low
RAM window, writes only a 12-row framebuffer marker, and stops in `WFE`. It has
no XNU branch, storage access, PSCI call, GIC setup, watchdog change, boot-image
wrapper, or flashing command. The local Clang/LLD build produced a 39,840-byte
Image with no relocations and SHA256
`42c23b9ffbc18dc8a9ece93591c6fa91ef613948608129853b8771b5010c71e1`.
This is a host build and inspection result only; it has not run on the phone.

The diagnostic was also wrapped offline as an unsigned Android boot-header-v4
image using only the captured stock header metadata. Stock `boot_a` has kernel
size `0xf8a6e1`, empty ramdisk, header size 1584, version 4, and empty boot
signature. The wrapper replaces only the kernel size/payload and deliberately
omits the invalidated AVB footer. Output size is 45,056 bytes and SHA256 is
`3702cd16974ea42abf05a46cc00256cf1d4e6f4421896c44dea8139df981e824`.
It is not approved for flashing and has not been passed to fastboot.

## 2026-10-25: Duchamp RAM-only fastboot probe

Windows detected the phone as `Android Bootloader Interface`; fastboot reported
`product: duchamp`, `unlocked: yes`, `current-slot: a`, `slot-count: 2`, and
`is-userspace: no`. After explicit approval, the 45,056-byte diagnostic wrapper
was submitted with `fastboot boot` (RAM-only). USB transfer completed, but the
device bootloader rejected the operation with `FAILED (remote: 'unknown command')`.
The phone remained in fastboot on slot `a`; no partition was flashed or modified,
and no bootshim code executed. Therefore this bootloader does not expose the
standard RAM-only `boot` command, and the diagnostic image remains host-tested
only. Do not substitute `fastboot flash` as a workaround.

After rebooting normally, `/proc/config.gz` reported both
`# CONFIG_KEXEC is not set` and `# CONFIG_KEXEC_FILE is not set`; the kexec
sysfs state files were absent as well. Consequently the running Android kernel
cannot provide a second RAM-only launch path for this diagnostic. Enabling that
route would require building and booting a different Android kernel first, so it
does not remove the same verified-boot/deployment boundary.

## 2026-10-25: Duchamp framebuffer and early-XNU QEMU verification

Fixed `tools/qemu-sweet.py` to place its transient QMP UNIX socket under
`/tmp`; the Windows-mounted workspace path exceeded Linux's AF_UNIX path limit
and previously made QEMU exit before starting. A fresh run with QEMU 10.2.1,
`work/payload-duchamp-final.bin`, the matching unstripped kernel, and
`--framebuffer duchamp` rendered the measured 1220x2712, 4992-byte-stride
framebuffer correctly. The decoded screen progressed through all early markers,
including `arm_vm_init returned`, and stopped at the intentional
`DUCHAMP XNU MEMORY READY` milestone. QEMU logged no exceptions or guest errors.

The result classifier now recognizes that explicit Duchamp milestone before
reporting unknown glyphs caused by the diagnostic color band. The repeated
five-second run returned `duchamp_memory_ready`; this verifies the QEMU memory
and framebuffer bootstrap path only, not MT6897 hardware execution.

## 2026-10-25: live A/B partition audit after restoring Magisk

Magisk v30.7 was initially installed by patching a local image that was later
found, through its AVB properties, to be Redmi `topaz` Android 13 rather than
Duchamp. It happened to boot on the unlocked device but must not be treated as
a stock backup. The installed `init_boot_a` was subsequently replaced with a
Magisk-patched image carrying the correct Duchamp/MT6897 Android 14
`V816.0.17.0.UNLMIXM` AVB properties; Android and uid-0 Magisk root were
verified afterward. An exact factory `init_boot_a` is still unavailable.

Root-assisted, read-only copies of the B-slot boot-chain partitions showed that
`boot_b` and `vendor_boot_b` are each exactly 64 MiB of zeroes (SHA256
`3b6a07d0d404fab4e23b6d34bc6696a6a312dd92821332385e5af7c01c421351`).
`init_boot_b` contains an Android boot image and `vbmeta_b` contains AVB data,
but that does not make the slot bootable without its boot and vendor_boot
payloads. Therefore slot `b` must not be selected or treated as a safe isolated
test slot. Populating or cloning the missing B-slot chain would be a separate,
multi-partition operation and is not authorized by the diagnostic work.

The diagnostic bootshim now also has a native host harness that maps stand-ins
at the measured FDT and framebuffer addresses. It verified that EL2 and
MMU-enabled entries leave the framebuffer untouched, invalid and oversized FDT
headers produce only the failure band, a valid FDT produces the success band,
and all stride padding remains unchanged. The complete harness passed, and the
freestanding ARM64 image rebuilt with no relocations and the same 39,840-byte
size.

Added a versioned, checksummed RAM-only diagnostic record containing the entry
gate result, marker decision, FDT magic/size, and preserved EL/SCTLR/x0-x3/SP.
The host harness verifies the record for EL2, MMU-on, invalid, valid, and
oversized-FDT cases. The first freestanding link correctly rejected an implicit
`memcpy` generated by a structure assignment; replacing it with explicit field
copies removed the runtime dependency. Final host tests pass, the ARM64 ELF has
no relocations or unresolved runtime symbols, and its 40,768-byte Image SHA256
is `e5d5802007eda109cc355b9fd2145d48106f6420914a641e12039c4e2c614ffc`.

The marker is now a 12-row visual report: overall status, EL1, MMU/data-cache/
instruction-cache state, FDT range, magic and size, followed by a four-row
alternating build signature. The native harness still passes and verifies row
padding. A second test boots the actual linked ARM64 Image under QEMU, captures
the physical Duchamp framebuffer through QMP, and verifies all rows and padding;
it reports `bootshim-qemu-test: PASS`. The resulting 40,400-byte Image SHA256 is
`54edce9ab28cf389087b1902068529e5b5d7e67df71904df2f40467b293f83b3`.
The offline boot-header-v4 wrapper is 45,056 bytes with SHA256
`75eb610c1b0717f76f8996330017ba8da35f3330d8a8c10b6270ab5370efae60`.

Added a recovery-only PowerShell guard for stock `boot_a` and `init_boot_a`.
It requires explicit confirmation, exact captured size/SHA256, one fastboot
device, product `duchamp`, an unlocked bootloader and active slot `a`, and it
deliberately leaves the phone in fastboot after restoration. Negative tests
confirmed that missing confirmation and a wrong image hash fail before any
fastboot write. The helper's existence is not authorization to flash the
diagnostic image.

## 2026-10-25: first Duchamp diagnostic boot partition trial

After explicit approval, preflight confirmed a charging 45% battery, product
`duchamp`, active slot `a`, unlocked bootloader, a 64 MiB `boot_a` partition,
the stock backup SHA256 `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`,
and diagnostic wrapper SHA256
`75eb610c1b0717f76f8996330017ba8da35f3330d8a8c10b6270ab5370efae60`.
Fastboot successfully wrote the 45,056-byte diagnostic to `boot_a` and rebooted.
Eight seconds later the device exposed neither ADB nor fastboot, which is
consistent with either the intentional WFE stop or an earlier boot-chain stop;
the visual marker result has not yet been reported and must not be inferred.

The user re-entered fastboot with the hardware keys. The guarded recovery tool
verified and restored the full stock `boot_a`, then Android rebooted on slot
`a`. ADB identified `duchamp`, and `su -c id` again returned uid 0 in the Magisk
context. Recovery is therefore verified for this exact trial. No other
partition was changed by the diagnostic test or its recovery.

The user reported that the bootloader stopped before any diagnostic marker.
Offline AOSP `avbtool` inspection then identified the packaging defect: stock
`boot_a` is a full 64 MiB AVB partition with a signed vbmeta block at offset
`0xf90000` and an `AVBf` footer, while the tested 45,056-byte wrapper omitted
that container. A new offline-only wrapper preserves the original partition
size, signed vbmeta, and footer while replacing and zero-padding the payload
region. `avbtool info_image` parses it successfully and verifies the signed
vbmeta; as expected, the boot payload digest no longer matches Xiaomi's hash.
Its SHA256 is
`6bf740d74144d72b0d87fe3df7f55addb22c77f4bb6ce7c748ea773c62aa1716`.
Unlocked-state tolerance of that digest mismatch is not yet proven, so this
image has not been flashed.

The AVB+LZ4 candidate was flashed after explicit approval, but the user again
reported a bootloader stop with no visual marker. The verified stock `boot_a`
was restored, and Android `V816.0.17.0.UNLMIXM`, slot `a`, and uid-0 Magisk root
were verified. This eliminates missing AVB layout and missing LZ4 framing as
sufficient explanations; the preserved Xiaomi vbmeta still carried the old
payload digest and was therefore internally inconsistent.

Built a fourth offline candidate using `avbtool add_hash_footer --algorithm
NONE` so its hash descriptor matches the modified LZ4 payload. Its payload
region, vbmeta offset, partition size, salt, properties, and footer placement
match the stock layout: 16,318,464-byte payload region, vbmeta at `0xf90000`,
and 64 MiB total. AOSP `avbtool verify_image` verifies both its unsigned vbmeta
and boot hash successfully. SHA256 is
`800ddfe8c0e3cba7c5bcbc17a96e95648d4ca082f5913a1ec60dc89dec3ee282`.
Whether the unlocked MT6897 boot chain accepts algorithm `NONE` for `boot` is
not yet known; this candidate has not been flashed.

The AVB-NONE/LZ4 candidate was flashed after explicit approval, but the user
again reported a black bootloader stop with no marker. Stock `boot_a` was
restored and Android, slot `a`, and uid-0 root were verified. This does not yet
prove rejection before execution: the diagnostic assembly itself immediately
halted without drawing for any entry EL other than EL1, and MediaTek may enter
the Linux payload at EL2.

The next diagnostic therefore records `SCTLR_EL2`, installs `VBAR_EL2`, and
draws a red-EL report when entered at EL2 with translation/caches off. EL2 with
translation or caches active remains a no-write stop, and there is still no
`eret` or EL2-to-EL1 transition. Native tests cover safe and MMU-on EL2, and the
linked ARM64 QEMU framebuffer test passes. The 40,608-byte Image SHA256 is
`0e7dd27297335081cc2ec28f6346ec2094b1f7a4bc0f0464bc8b16278a89711c`.
Its fully verified stock-layout AVB-NONE/LZ4 wrapper SHA256 is
`0fb8929162d56a91915b010d7c1cebc9f0a2f2da62204621e07cd698d5dd491e`;
it has not been flashed.

The opaque full-screen-band candidate was flashed after approval and produced
an unambiguous hardware PASS photograph: the upper eight bands were green,
followed by cyan/magenta/cyan/magenta signature bands. This means overall gate
success, EL1 entry, `SCTLR_EL1.M/C/I` all clear, FDT pointer range/alignment
valid, FDT magic valid, and FDT size valid. It also proves the measured
1220x2712 framebuffer base/stride and the watchdog-stop sequence on MT6897.
The local evidence copy is `work/duchamp-entry-contract-pass.jpg`, SHA256
`41b7d9852bf4cfc4853c11abb19c7d4487c5c83ee16a85f25292ecee16bbed86`.

After recording the result, the guarded recovery restored stock `boot_a` and
Android `V816.0.17.0.UNLMIXM`, slot `a`, and uid-0 Magisk root were verified.
This is the first hardware-verified Duchamp LK-to-payload entry contract. It
does not yet prove XNU execution; the next stage is a bounded loader that
materializes the already QEMU-tested payload and retains a fail-closed stop
before any XNU jump until its memory layout is revalidated for hardware.

## 2026-10-25: embedded payload preflight (offline only)

Added a fail-closed payload preflight shared with the existing Duchamp loader
guard. Against the captured live FDT and `payload-duchamp-final.bin`, host tests
pass with 10 segments, physical window `0x1c0000000` + `0x20000000`, entry
`0x1c1480488`, ADT `0x1c24d8000`, boot_args `0x1c24dc000`, and top
`0x1c24e0000`. Negative tests confirm that corrupt payload and FDT headers are
rejected.

The bootshim can now embed the 16,674,432-byte payload and run the same check
against LK's live FDT. It deliberately has no copy loop and no XNU branch. The
linked Image is 16,723,584 bytes, has no relocations, and its embedded payload
byte-compares equal to the source. Existing native entry tests and the previous
non-embedded linked QEMU framebuffer test still pass.

An offline stock-layout LZ4/AVB-NONE wrapper was generated at
`duchamp/bootshim/out-preflight/duchamp-payload-preflight-avb-none-lz4.img`.
It is 64 MiB, retains the measured 16,318,464-byte pre-vbmeta region and AVB
offset, and `avbtool verify_image` verifies both its NONE vbmeta and boot hash.
SHA256 is
`78fe072bfb4f3b7ad555107a61e6b2565be18408ebe4e34947907947ee0e6ff7`.

After explicit approval, preflight verified `duchamp`, MT6897, active slot
`a`, unlocked/secure-no fastboot state, 47% charging battery, and the stock
backup hash before writing this image to `boot_a`. The first photograph caught
the already-drawn entry report while the uncached payload/FDT scan was still in
progress. A later photograph showed rows 0-10 green and row 11 magenta. This is
the defined payload-preflight PASS pattern: the live FDT passed the complete
guard, the embedded payload reported 10 segments, and its physical base/size
matched the required `0x1c0000000` + `0x20000000` window. The evidence copy is
`work/duchamp-payload-preflight-pass.jpg`, SHA256
`21279e680084c8f1f2eaa5a56ff7b04c05564f8ddd75064f41de21232f00c1ec`.
No segment copy or XNU branch occurred.

The user then re-entered fastboot. The guarded recovery tool verified SHA256
`1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`
and restored the 64 MiB stock `boot_a`. Android booted successfully and ADB
reconfirmed `duchamp`, `mt6897`, slot `_a`, build
`V816.0.17.0.UNLMIXM`, and Magisk uid 0. No other partition was changed.

The first full-screen-band candidate was flashed after approval. The user
reported that the retained boot logo disappeared and the panel became black,
while the watchdog remained stopped. This proves the bootshim executed and
wrote the measured framebuffer region; the intended colors were hidden because
their high alpha byte was zero. Stock `boot_a` was restored and Android/root
were verified.

All diagnostic colors now use alpha `0xff` (`0xff00ff00` pass,
`0xffff0000` fail, and opaque cyan/magenta signature bands). Host and linked
QEMU framebuffer tests pass. The 40,624-byte Image SHA256 is
`e1829c0706818265d74815273081bf3069f43dbb92e746ada0e0af0036d6bab5`.
Its fully verified stock-layout AVB-NONE/LZ4 wrapper SHA256 is
`f9168444013865b862233e91049fc1fc95478f3307c95f3770ff7188a5a359e4`;
it has not been flashed.

The watchdog-stop candidate was flashed after approval. The user reported that
the boot logo remained stable for more than 20 seconds instead of resetting.
This confirms the documented TOPRGU write took effect and strongly supports
actual bootshim execution with translation/caches off. No thin diagnostic rows
were noticed. Stock `boot_a` was restored and Android/root were verified.

The framebuffer base in the live `/chosen` data and reserved-memory node is
still `0xfcc2f000`, with 0x33d0000 bytes reserved, so the next visual diagnostic
keeps that address but replaces the nearly invisible one-pixel rows with twelve
226-scanline bands filling the entire 1220x2712 framebuffer and adds a final
`dsb sy; isb`. Native tests and the actual linked QEMU framebuffer test pass.
The 40,656-byte phone Image SHA256 is
`323568f62f52c3a78f4829b27f6458da45f07ebba60b57d685b9b10b24bc0eae`.
Its fully verified AVB-NONE/LZ4 wrapper SHA256 is
`18f1117596c8c10e11ed05bfd70598bbda31cfd7070053562f4298ca260a88fb`;
it has not been flashed.

The EL2-observable candidate produced a materially different hardware result:
the phone reached its boot logo and then reset, instead of remaining at the
earlier bootloader stop. No diagnostic rows were visible. Fastboot was recovered
with the hardware keys, stock `boot_a` was restored, and Android/root were
verified. This is consistent with the modified image being accepted and code
either entering the safe no-framebuffer path or faulting before drawing, then
the bootloader-started watchdog resetting the device; it is not yet proof of a
specific entry EL.

The live DT identifies TOPRGU watchdog MMIO at `0x1c00a000` with the
`mediatek,mt6589-wdt` compatible. Following Linux's upstream `mtk_wdt_stop`
sequence, the phone-only diagnostic now reads mode offset 0, clears enable bit
0, writes key `0x22000000`, issues barriers, and records before/after values.
This occurs only for EL1/EL2 with translation and caches off; otherwise no MMIO
is touched. Host tests pass, a watchdog-disabled QEMU-linked image passes the
actual framebuffer test, and disassembly confirms the intended MMIO sequence.
The phone Image SHA256 is
`60293489e3e60dd0e86a441548dbcf11ab6b1e2f3e6fead0b8bd9aee3bc3fedf`.
Its fully verified stock-layout AVB-NONE/LZ4 wrapper SHA256 is
`6bc5503cd2fa8afc330775deda2be78c5573541fe36d79b1e4fdd0aeb2104dc9`;
it has not been flashed.

The full-size AVB-container image was then flashed after separate approval.
Fastboot accepted all 64 MiB, the device left USB during the attempted boot,
and the user re-entered fastboot with hardware keys. The guarded tool restored
the verified stock `boot_a`; Android, the correct build fingerprint, slot `a`,
and Magisk uid-0 root were verified again. The visual result was not recorded
in the chat, so this trial alone does not prove code execution.

Further offline comparison found that the captured stock kernel payload begins
with LZ4 legacy magic and is reported as LZ4-compressed, while both earlier
diagnostic trials embedded a raw ARM64 Image. Added an `--lz4-legacy` packaging
mode and produced a full-size AVB-container candidate with SHA256
`6cf1159f94c2ead8d8ef8d6a4db8737a7d754d8bda6cb91a1cef8be734541465`.
Its embedded kernel begins with legacy magic `02214c18`, decompresses to 40,400
bytes, and byte-compares equal to the tested bootshim Image. AOSP `avbtool`
parses its preserved footer/vbmeta; the changed payload hash remains the only
expected AVB mismatch. This candidate has not been flashed.

## 2026-10-25: bounded materializer build (offline only)

The loader materializer is now covered by a 512 MiB sparse-window host test
using the captured FDT and final payload. The test byte-compares all 10 copied
segments, verifies every segment's zero-filled tail, verifies the ADT copy and
complete boot_args v2 fields/page, checks an untouched sentinel near the end
of the window, and proves that a rejected corrupt payload performs no
destination write. It passes with physical entry `0x1c1480488` and top
`0x1c24e0000`.

Added an optional `MATERIALIZE=1` bootshim build. It embeds the payload, repeats
the full guard, writes only into the validated `0x1c0000000` + `0x20000000`
RAM window, reports completion visually, and stops. It contains no XNU branch.
The linked ELF has no relocations; disassembly contains no `br`, `blr`, or
`eret`; the embedded payload byte-compares equal to the source. Native loader,
bootshim/preflight, and the non-materializing linked QEMU framebuffer tests all
pass.

The offline stock-layout candidate is
`duchamp/bootshim/out-materialize/duchamp-materialize-nojump-avb-none-lz4.img`,
64 MiB, SHA256
`4febcf25b1fdb1ba4c85d2849cf1223180a5663476f8a7194c9f59657d09ca96`.
AOSP `avbtool verify_image` verifies its NONE vbmeta and boot hash.

After explicit approval, preflight reconfirmed the device, active slot, battery,
root, stock backup hash, and candidate hash. Fastboot wrote only `boot_a`. The
final hardware display showed rows 0-10 green and row 11 cyan, exactly the
defined materializer PASS signature. This proves that the guarded materializer
completed all segment, BSS, ADT, and boot_args writes into the chosen RAM
window and returned without branching to XNU. The evidence copy is
`work/duchamp-materialize-nojump-pass.jpg`, SHA256
`ecc22de1ab37afd5df044dfb8e192e5e30998ec910b0d94862c4cef17ca4674a`.

The user re-entered fastboot and the guarded recovery tool restored stock
`boot_a` after verifying SHA256
`1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`.
Android then completed boot; ADB reconfirmed `duchamp`, `mt6897`, slot `_a`,
build `V816.0.17.0.UNLMIXM`, and Magisk uid 0. No other partition was changed.

## 2026-10-25: no-jump handoff-ready gate (offline only)

Compared the handoff contract with the local HackiOS `xnuloader` and the
existing SWEETXNU loader. Both enter XNU at EL1 with interrupts masked,
translation and caches off, `x0` set to the physical boot_args address, and a
final `dsb sy; ic iallu; dsb sy; isb`. No Qualcomm translation-table setup was
reused.

Added a fail-closed handoff-ready check for the hardware-observed EL1/SCTLR
state and the validated entry/boot_args bounds. The linked AArch64 barrier
disassembles exactly as intended. The ready image has no relocations and no
`br`, `blr`, or `eret`, so it still cannot enter XNU.

Replaced the halt-only vector slots with EL1/EL2 exception capture that records
exception class, ESR, ELR, FAR, and SP in RAM and produces a red visual report.
Both the normal linked QEMU framebuffer test and a deliberate `brk` exception
build pass. Host entry, preflight, materializer, and ready-gate tests also pass.

The offline stock-layout image is
`duchamp/bootshim/out-ready/duchamp-handoff-ready-nojump-avb-none-lz4.img`,
64 MiB, SHA256
`4af103cb18014d4ec15ac611fac98646cbe14f731a10a4d5a42658578a2c2508`.
AOSP `avbtool verify_image` verifies its NONE vbmeta and boot hash.

After explicit approval, the guarded trial reconfirmed `duchamp`, MT6897,
active slot `a`, 49% charging battery, root, and both image hashes before
writing only `boot_a`. The final hardware report showed rows 0-10 green and
row 11 magenta, with no red exception report. This is the defined handoff-ready
PASS signature and proves that materialization, the EL1/MMU/cache-off gate, and
the final architectural barrier sequence all completed before the intentional
no-jump stop. Evidence is
`work/duchamp-handoff-ready-nojump-pass.jpg`, SHA256
`ad238038f610d317639d8ed22c109ad2a6a41271af5f01a7f2f3833bbaf0d6e0`.

The guarded recovery then verified and restored the stock 64 MiB `boot_a`.
Android completed boot, and ADB reconfirmed `duchamp`, `mt6897`, slot `_a`,
build `V816.0.17.0.UNLMIXM`, and Magisk uid 0. No other partition changed.

## 2026-10-25: first XNU jump candidate (offline/QEMU only)

`tools/verify-payload-source.py` rebuilt `payload-duchamp-final.bin` from
`work/kernel-final/kernel.development.sweet`, the payload's embedded ADT, and
its embedded command line. The result matched byte-for-byte at SHA256
`8ab5762816be7f2f39357515ae25cdab5d50b8cd0271663440741948fe9239ac`.
The Mach-O LC_UNIXTHREAD entry is `__start` at virtual
`0xfffffe0007480488`, mapped by the validated plan to physical
`0x1c1480488`. Patch 0082 already gives that path a pre-stack Stage 0
framebuffer marker, so no speculative XNU patch was added.

Added an opt-in `JUMP=1` build requiring the embedded payload, materializer,
and ready gate. Its final assembly masks interrupts, repeats
`dsb sy; ic iallu; dsb sy; isb`, moves the physical boot_args address to `x0`,
and branches to the validated physical entry. Non-JUMP builds remain unchanged.

The complete bootshim->materialize->ready->XNU path passed QEMU with 8 GiB RAM
and the captured phone FDT. After 20 seconds the framebuffer contained 65,972
white pixels; the bootshim never draws white, while the matching XNU has Stage
0 and early-console white output. This is direct evidence that control reached
XNU through the new jump path. The captured raw framebuffer is
`work/qemu-bootshim-jump-fb.raw`.

The phone candidate is
`duchamp/bootshim/out-jump-phone/duchamp-xnu-first-jump-avb-none-lz4.img`,
64 MiB, SHA256
`a8eb491fee193a494581243d077c71a4f03e4ca12ef9a5d63cdf8251aa85d090`.
Its embedded payload byte-compares equal to the verified source; the linked ELF
has no relocations; AOSP `avbtool verify_image` verifies its NONE vbmeta and
boot hash.

After explicit approval, preflight reconfirmed `duchamp`, MT6897, slot `a`,
49% charging battery, root, and the stock/candidate hashes. Fastboot wrote only
`boot_a`. The hardware framebuffer then showed XNU's own early console through
all intended Duchamp checkpoints: `arm_init entered (MMU on)`,
`PE_init_platform done`, `ml_parse_cpu_topology`, `cpu_bootstrap done`,
`kernel_startup_bootstrap done`, `cpu_init done`, entry to `arm_vm_init`,
TTBR0 removal/TLB flush, live kernel framebuffer VA, rebound physmap pointers,
`pmap_bootstrap done`, early I/O page tables, `arm_vm_init returned`, and the
intentional terminal message `DUCHAMP XNU MEMORY READY`. No bootshim exception
report appeared. This is verified XNU execution on POCO X6 Pro/MT6897 through
the early virtual-memory bootstrap, not a claim that iOS userland is running.

The evidence copy is `work/duchamp-xnu-arm-vm-init-pass.jpg`, SHA256
`33696d19f391b8bb3ec49ef7e11242d796360b9e19a06b04b6a8a089637078fd`.
The user re-entered fastboot; guarded recovery verified and restored stock
`boot_a`. Android completed boot, and ADB reconfirmed `duchamp`, `mt6897`,
slot `_a`, build `V816.0.17.0.UNLMIXM`, and Magisk uid 0. No other partition
changed.

## 2026-11-01: passive UFS PRDT observer (offline only)

Pinned GKI and Xiaomi MT6897 sources prove that
`android_vh_ufs_fill_prdt` runs after `scsi_dma_map()` and after the UFS core
fills each PRDT entry. Added a passive observer that filters the exact
`112b0000.ufshci` device and compares existing PRDT, DMA, translated physical,
original physical and SWIOTLB state. It never starts I/O, maps DMA, accesses
MMIO, invokes firmware, attaches an IOMMU domain or changes the hook error.

The corrected AArch64 artifact is 407,280 bytes with SHA256
`fb5b1a887bced8e4b0fbf498ebafc21d4856b4f57bbf2795f1d469bd8c9984c3`.
Offline verification reproduces all 18 captured symbol CRCs, Android Clang
17.0.2, the exact vermagic, `struct module` size `0x440`, and init/exit
relocations `0x170`/`0x3d8`. Source, receipt and runner tests pass. The report
is root-only (`0400`). Aggregate updates use a spinlock-backed coherent
snapshot, the hook unload path waits for in-flight callbacks, and the module
refuses to observe unless the measured dma-direct/no-IOMMU/36-bit contract is
still present.

Added a fail-closed live runner that verifies the exact target, source,
artifact and receipt, rejects the known orphan tracefs instance, uses only a
fixed regular-file read workload, and verifies unload, staged-file removal,
boot ID, kernel taint and kernel logs. The module has not been loaded and no
phone access occurred in this milestone. A normal Android reboot and the exact
module load each require a separate explicit approval. This work does not yet
prove physical firewall access, XNU cache ownership or safe XNU UFS use.

## 2026-11-01: passive UFS PRDT observer (approved live result)

The user separately approved a normal Android reboot and then one temporary
load of the exact artifact with SHA256
`fb5b1a887bced8e4b0fbf498ebafc21d4856b4f57bbf2795f1d469bd8c9984c3`.
The reboot cleared the stale tracefs instance. The fail-closed live runner then
passed with 371 read commands and 17,437 workload-delta segments: every PRDT
entry matched, inverse `dma_to_phys()` translation returned the original
scatterlist physical address, no SWIOTLB segment or 36-bit-limit violation
occurred, and the pinned dma-direct/no-IOMMU contract stayed true. This does
not prove raw DMA/CPU-physical numeric identity because the device has a
`dma_range_map` whose live entries were not captured.

Cleanup was complete: the module unloaded, the staged file and sysfs state
disappeared, boot ID and taint stayed unchanged, and no new kernel fault line
was found. The result SHA256 is
`81f1210b67a659103d3c4c863dd6baafd85e39dfb77132b4382efab1a91de5d4`.
This proves the observed Android UFS DMA route only; firmware/firewall access,
XNU cache ownership and safe XNU controller ownership remain unproven.

## 2026-11-06: LK/FDT handoff contract and blocked phone-layout path

Commit `f3554a3` added an exact offline audit for the saved LK, boot,
vendor-boot, live FDT and `/proc/iomem` captures. The saved LK binary verifies
its own stage-1 mapping at physical `0x50700000` and high VA
`0xffff000050700000`. Its Linux handoff uses SMC `0xc2000115`; LK computes the
kernel and final-FDT targets at runtime rather than embedding fixed targets.

The captured vendor-boot metadata declares `kernel_addr=0x40000000` and both
`tags_addr`/`dtb_addr=0x47c80000`. The stock ARM64 Image has `text_offset=0`.
The `0x76980`-byte live FDT matches the saved runtime page-rounded reservation
`0x47c80000..0x47cf7000`. These are static/corroborating facts, not a captured
runtime PC or incoming `x0`; the report explicitly keeps both runtime claims
false. The FDT establishes 12 GiB RAM, 52 fixed reservations and four dynamic
allocation requests.

A separate `PHONE_LAYOUT=1` bootshim mode now requires the exact audit report,
rejects every payload/transport/materialize/ready/return/jump option, and links
at the static Android Image contract. Its assembly compares runtime `_head`
and inherited `x0`, then always stops in `WFE` before BSS clearing, C, watchdog,
framebuffer, MMIO, copying or an XNU branch. The post-link verifier checks the
actual guard opcodes and branch targets, zero relocations, no undefined symbols,
an empty capsule and absence of execution/transport symbols.

Actual local results: 12 new Python negative/unit tests passed; existing
bootshim host, handoff-ready and XNU-return tests passed; normal QEMU bootshim
regression passed; the missing-contract negative gate passed. The phone-layout
artifact is 40,848 bytes, SHA256
`a8770869c5df2f95ed0bdf7f7337d14cdc8d3b579898c69fa10f9c9fce67f7ba`.
The audit report SHA256 is
`b62fe30e06cb0043d027ffed0dff0116528e40d202d91ae731b676ba7796ecb6`;
the post-link report SHA256 is
`cc2394bccf508e30831f52e39b1f5a2a45095694ffd4b0f3cc88e684fc5571e2`.
No phone, ADB, fastboot, partition, firmware or MMIO access occurred.

Next safe action: capture the numeric runtime Image PC and incoming FDT `x0`
using a separately reviewed no-write diagnostic before considering any phone
transport. UFS/DMA/IOMMU and firmware ownership remain separate blockers.

## 2026-11-06: isolated runtime PC/x0 capture (local and QEMU only)

Commit `62abe49` added a separate `PHONE_CAPTURE=1` bootshim mode. It links an
isolated entry instead of the normal shim, records the runtime `_head` computed
with `adr` plus inherited `x0` in a checksummed 64-byte RAM record, and renders
both values as hexadecimal text on the already measured framebuffer. It does
not link an FDT dereference, watchdog access, payload, transport, materializer,
XNU jump, return channel or storage operation. Unsafe EL/MMU/cache state fails
closed before framebuffer access.

The post-link verifier checked the actual capture opcodes and targets, link base
zero, ARM64 Image header, empty transport capsule, zero relocations, zero
undefined symbols and absence of forbidden capabilities. Negative build gates,
four new verifier tests, five existing phone-layout tests, all bootshim host
tests and the unchanged normal QEMU regression passed.

The actual freestanding capture Image ran in QEMU and measured runtime
`PC=0x40200000`, inherited `x0=0x48000000`, `CurrentEL=0x4`. QMP independently
validated the complete RAM record and representative framebuffer glyph pixels.
Artifact: `work/phone-capture-qemu-v3/Image`, 40,912 bytes, SHA256
`2a7dff64f5e28afa5e7eef74e99ea2d3a273df367f341047891ba3a4ea6d20ea`;
ELF SHA256
`675831def76bb4ee85f55d2b97272f490b7f08caf223d77390264db19e2b0a03`;
verification JSON SHA256
`0e6e10e58588e74c36dbcfbcdf4cc61f11d24b3dcf00642a3674507e801916f1`.

These are QEMU values, not a physical Duchamp capture. No phone, ADB, fastboot,
partition, firmware or phone MMIO access occurred. The saved 2026-10-25 probe
already proves Duchamp LK rejects standard RAM-only `fastboot boot` as an
unknown command, and the installed Android kernel has no kexec. Therefore the
physical capture remains blocked on a documented RAM-only launch mechanism;
do not substitute a boot-partition write. UFS/DMA/IOMMU and firmware ownership
remain separate blockers.
