# Native QuartzCore trace on the Duchamp QEMU fixture

The original 20F66 backboardd submits its empty swap when QuartzCore
disables the primary display. `IOMFBDisplay::set_enabled_(false)` calls
`set_all_layers_to_null(true)`. The three observed native calls to
`IOMobileFramebufferSwapSetLayer` pass a null IOSurface, and SwapEnd reaches
the kernel with mask `0x80000007` and four zero surface IDs. This is a
layer clear. The trace found no native rendering call that produced a
replacement layer.

The 20F66 cache slide is captured at the successful
`shared_region_check_np` path for backboardd. Later traces also check the
slide against SpringBoard's own shared-cache check. Breakpoint opcodes
are recorded when resident. The kernel image is pinned by
`qemu-service-ram.py`. The debugger observes the actual process and
arguments, and the saved shared RAM verifies the AppleCLCD counters,
pending record and framebuffer.

## Verified blockers and experiments

- The native display path delivered vsync callbacks to QuartzCore. One
  run recorded four callbacks with a nonzero IOMFB connection. Changing
  `CA_FORCE_TIMER` alone still yielded one empty swap.
- The kernel log records repeated `IOAcceleratorES` lookups with zero
  services. QuartzCore's native `CAMetalContextCreate` returned null to
  `EAGLServer::renderer`. In a separate VM, one debugger redirect reached
  QuartzCore's own `sw_new_context`. Timer and vsync callbacks still ran,
  and no native surface was presented in that run.
- A simulated power-button pair was injected into the existing guest
  HID timer. Its button service reported zero clients. A separate test
  called the original BackBoard unblank APIs three times after SpringBoard
  appeared. They returned zero, but no subsequent display power-on or
  eligible layer was observed.
- A SpringBoard worker made synchronous preference requests. Restoring
  the regular cfprefsd job's original lack of forced root/System keys
  left the observed daemon at UID 0 and did not change the display result.

The primary SpringBoard thread was a separate blocker. Stopped-RAM
stacks from the baseline and five variants resolve through
`+[AWClientPreferences initialize]`, `_registerForPrefsChange`,
`_getPreferences` and a synchronous NSXPC reply wait. The main-thread
stack must be distinguished from the CFPreferences worker samples.

In the next trial, only `com.apple.AttentionAwareness` was removed from the
BackBoard job's advertised Mach services in a private QEMU root copy.
The original SpringBoard progressed to scene creation and subsequently
aborted. Its first process exited with SIGABRT, and the controller
reported status 1. The native exception was
`Missing locale identifier in collation dictionary`. The throw stack
resolves to `+[SBHLocalizedIndexedCollationStrategy myCurrentCollation]`
and `prewarm`. The experiment avoids the observed IPC stall in QEMU.
It does not implement the AttentionAwareness service.

The next RAM root added 41 original `UITableViewLocalizedSectionIndex.plist`
files and UIKitCore's original `Info.plist` from the matching 20F66 system
image. All 42 files were read back byte for byte. The locale exception
was no longer observed. SpringBoard restarted after a different SIGABRT,
whose stack resolves through `CoreNLP::NLLangid` and
`_langid_env_create`. The matching `/usr/share/langid/langid.inv` and
23 CoreNLP framework files were extracted from the same image for
the following trial. The receipt records each file's size and hash.

The replay with those 24 files reached UIKit's CoverSheet button
construction and produced a different exception:
`Luminance Map Image must be a CGImage based image`. The throw stack
resolves through `+[UIColorEffect colorEffectLuminanceMap:blendingAmount:]`,
`-[UICoverSheetButton _backgroundEffectsWithBrightness:]`, and
`-[CSQuickActionsView _addOrRemoveCameraButtonIfNecessary]`.
At unslid address `0x1899856c4`, UIKit calls `kitImageNamed:` with
the literal `UICoverSheetButtonLuminanceMap`. The matching 20F66
`UIKitCore.framework/Artwork.bundle/Assets.car` contains that exact
name, and the whole Artwork bundle was absent from the guest root.
The separate `lumaDodgePillCorners` lookups in the log do not identify
the image argument at this throw site.

After 300.276 host seconds, the language-only replay still had one swap,
zero eligible layer writes, four zero surface IDs, and display power off.
The debugger timed out and the runner saved the stopped framebuffer.
A follow-up installed 47 original files from UIKitCore's Artwork bundle
and CoverSheet's catalog and metadata. All 47 were verified by reading
the bytes back from HFS. In 275.329 host seconds, no luminance-map
exception was observed. SpringBoard repeatedly hit a new SIGSEGV at
`__CFGetNonObjCTypeID + 88` (fault address `0x8`) while
`_abCopyCardDisplayDictionary` called `CFBundleCopyBundleLocalizations`.
The native helper `__ABBundle` requests bundle ID
`com.apple.AddressBookLegacy`. That bundle was absent. Its original
resources include 41 variants of `ABLocalizableDefaults.plist`.
AppleCLCD still recorded one empty swap, no eligible layer writes and
power off. The run's AppleCLCD object straddled two noncontiguous pages.
The RAM analyzer verified the two physical mappings through the pinned
kernel's page table and reproduced the live swap record.

The AddressBookLegacy replay installed and read back 92 original
resource files. It advanced to SpringBoard's `SBStartupTransitionToSetup`
and created two native IOSurfaces: ID 2 (184×124 BGRA) and ID 3
(230×186, format `0x4c413038`). The kernel recorded both allocations
under SpringBoard. SpringBoard then aborted in
`CoreEmoji::createFrameworkBundle`. The original CoreEmoji framework
bundle was absent from the test root.
The debugger also observed one QuartzCore context commit from the
original SpringBoard process (PID 34).

The 270.293-second replay ended with display power off, two clear swaps,
no eligible layer writes, and a blank physical framebuffer. The last
swap still had mask `0x80000007` and four zero surface IDs. There was no
`layer_surface_id` event or native scanout capture. Native IOSurface
allocation is verified. The first SpringBoard frame in scanout is still
pending. Extraction of CoreEmoji hit a host I/O error with the Windows
drive full, so there is no CoreEmoji boot result.

## Local replay

Use `prepare-duchamp-quartzcore-root.py` to create a fresh copy with the
QEMU-only BackBoard service change and the pinned UIKitCore resources.
Supply the matching CoreNLP and langid tree with `--language-resources`.
Supply the matching UIKitCore Artwork and CoverSheet tree with
`--artwork-resources`.
Supply the matching AddressBookLegacy tree with `--address-book-resources`.
The tools expect local extractions of the original 20F66 system image.
They do not contain or download Apple files.

Use the original 20F66 readiness root, the pinned large-RAM QEMU ADT
and kernel, and pass `tools/duchamp-quartzcore.gdb` to
`qemu-service-ram.py --debugger-script`. The normal trace is read-only.
`--no-save-guest-root` omits the redundant final HFS image while keeping
the shared RAM, framebuffer and debugger evidence. If the debugger times
out, the runner still captures the stopped VM and records that timeout.
If AppleCLCD straddles physical pages, pass its traced virtual address
from the `power` event to the RAM analyzer with `--object-va`.

The two opt-in experiments use `SWEET_QEMU_POWER_EVENT=1` with
`sweethidtest=7`, or `SWEET_QEMU_SOFTWARE_RENDERER=1` on its own.
They change live QEMU registers for one diagnostic event. Use the
read-only mode for verification of the normal rendering path.

Private evidence and the file-hash manifest are under
`work/quartzcore-qemu-20261107`. The first eligible present, if reached,
is captured immediately after the native kernel call returns. A genuine
SpringBoard frame requires a SpringBoard scene commit, a non-null surface
from backboardd, matching SwapEnd and present IDs, and corresponding
pixels in the physical framebuffer dump.
