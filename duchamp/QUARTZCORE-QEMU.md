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
`layer_surface_id` event or native scanout capture in that run.
The initial CoreEmoji extraction hit a host I/O error with the Windows
drive full.

## CoreEmoji replay and verified scanout

Seven previous QEMU RAM-root dumps were compressed in place on NTFS.
Each file's SHA-256 matched before and after compression. The original
20F66 system image was then hashed again. The new isolated guest root
included 557 original CoreEmoji resource files (196,082,409 bytes).
Every installed file was read back from HFS. The original base root and
the prepared input root retained their hashes.

SpringBoard PID 34 stayed alive through the 315.202-second replay and
made four observed QuartzCore context commits. BackBoard PID 25 created
IOSurface 5 (1220×2712 BGRA, 5120-byte source stride). The native trace
correlated its non-null `SwapSetLayer` with layer 0 and ID 5, then
`SwapEnd` 17, mask `0x1`, and the same record at AppleCLCD present.
The debugger sampled five rows at the pinned kernel copy call and read
them back at physical address `0xfcc2f000` after present. All five
matched their source bytes, and four differed from the prior scanout.

Every active pixel of that first frame was black. The final QMP image
showed a black screen with launchd console text. A visible SpringBoard
interface remains unverified. The first scanout image SHA-256 is
`86f6c313ffd935db24829f42ba67d894183a397467babf09a6f330ec3bf91af6`.
The separate synthetic control matched all 2048 known BGRA pixels and
all five sampled rows. The verifier rejected a changed surface ID and
a one-byte change to the captured native frame.

The private replay evidence is in `work/quartzcore-emoji-qemu-20261107`.
Its manifest SHA-256 is
`4602731ada509574f3e94ec70076a874fb7ff3380c1f5d42077953ab35ba23ec`.

## Setup Assistant replay

The original 20F66 `/Applications/Setup.app` identifies itself as
`com.apple.purplebuddy`. Its 95 linked libraries are present by install
name in the matching shared-cache inventory. The isolated root adds
632 original app files and 13 files from the original SetupAssistant,
SetupAssistantUI and SetupAssistantSupport framework bundles. The
executable is installed as mode 0755. All 645 file contents are pinned
and verified by reading them back from HFS.

The first replay used the existing 20-second LaunchServices query
deadline. The readiness controller logged `PLATFORM NATIVE QUERY TIMEOUT`
and stopped before launching SpringBoard. Launchd subsequently recorded
a successful exit from the native query client. The Setup fixture builds
the diagnostic controller with a 45-second deadline and keeps its native
reply, service identity and registry checks.

With that change, the native LaunchServices reply returned status 256
and the registry rebuild succeeded. SpringBoard PID 34 reached
`SBStartupTransitionToSetup` and `_activateSetupWithCompletion`.
The guest log then recorded `Unable to execute launch request` and
`Could not find plist for domain attribute`, both from the matching
RunningBoard image. SpringBoard aborted during its app-layout transition.
No Setup exec was observed in this trial.

The guest lacked the `/System/Library/LifecyclePolicy` and
`/System/Library/RunningBoard` trees. The policy replay adds 82 matching
20F66 files, including the FrontBoard domain-attributes plist and
metadata for RunningBoard and FrontBoard. Each file is pinned and read
back from HFS. The debugger traces RunningBoard's request, execution
and completion entry points after SpringBoard requests Setup.

The policy replay kept SpringBoard alive and reached RunningBoard's
launch execution entry, with no Setup exec or eligible display transfer
observed. The saved `launchctl print` output showed `lsd` in `user/501`
and `runningboardd` in `system`. The console recorded unsuccessful
system lookups for `com.apple.lsd.mapdb` from runningboardd, although
the original lsd job advertised that endpoint.

`--setup-lsd-system` adds `LimitLoadToSessionType=System` to the
original lsd job on a separate Setup replay root. It retains the
`mobile` credentials, native service names and native binary.

Two replays with the launch-result trace stopped before the Setup
transition because the development kernel reported an interrupt latency
panic. The system-lsd replay confirmed the job's system bootstrap domain
and the successful UID 501 LaunchServices reply. Its interrupt handler
took 24.017264 ms against a 13.631488 ms limit. The earlier replay with
the user-domain lsd job reported 32.622288 ms against the same limit.

The system-lsd retry used `ml-timeout-interrupt-masked-scale=4` in
`qemu-service-ram.py`'s `run_vm(cmdline=...)` for the diagnostic VM.
The timeout remained enabled. The run ended after 460.256 host seconds
with no XNU panic observed. SpringBoard PID 34 entered both Setup
transition sites. RunningBoard returned a null launch result with
`RBSRequestErrorDomain` code 5 six times. Launchd identified
`UIKitApplication:com.apple.purplebuddy[...][rb-legacy]` in the system
domain and returned error 134, `Service cannot load in requested session`.
SpringBoard subsequently aborted with its app-layout assertion.

The validator in the matching 20F66 launchd image reads
`LimitLoadToSessionType` at unslid address `0x100003578`. A mismatch
branches to the error 134 return at `0x100003698`. The serialized
submission recovered from PID 1 matches a rejected label in the
console. It names `/Applications/Setup.app/Setup` and user `mobile`
and omits `LimitLoadToSessionType`. The stopped launchd contains a
system domain with session name `System` and a user domain with
session name `iOSUser`. The validator's missing-key path rejects the
system domain when its session-name pointer is set. The next replay
needs to validate correct session selection for this specific job.

There was no Setup exec, Setup context commit, or eligible captured
present in this run. The console framebuffer records the refusal.
Private evidence is in
`work/quartzcore-setup-qemu-20261107/session-rejection`.

The first session correction traced the incoming job pointer, then
missed the native check because launchd copied the job dictionary.
Tracing the normalized dictionary allowed the native validator to
accept the system session. The original Setup executable then ran as
PID 38 and mapped the matching shared cache. Its bootstrap lookup for
`com.apple.backboard.display.services` failed in `system`. The native
BackBoard job advertised that service in `user/501`. A Setup frame
was still unobserved in that run. RunningBoard later killed PID 38
with a process-launch watchdog violation. The saved log reports a
20-second allowance and reason `0x8BADF00D`.

The system-session replay evidence is in
`work/quartzcore-setup-qemu-20261107/session-system-exec`.

With the user-domain correction, launchd accepted `iOSUser` and
executed Setup as UID 501. The first replay hit the default 20-second
scene-create watchdog. An isolated HFS copy added the native
FrontBoard preference `FBLaunchWatchdogExceptions` for
`com.apple.purplebuddy` only, with value 100. FrontBoard reported a
120-second allowance for this app. The readback was owned by UID 501,
GID 501, with mode 0600. Setup PID 38 still expired during scene
creation. Its main-thread stack reached an infinite semaphore wait in
`ProximitySetupController` while waiting for `hasConnection:`.

The watchdog replay verified all five sampled rows for IOSurface 5
in SwapEnd 5. Its active pixels were black, and the trace contained
no Setup context commit. The framebuffer and watchdog evidence are
in `work/quartzcore-setup-qemu-20261107/session-watchdog`.

The manual-setup replay retained the 120-second Setup allowance and
accepted `iOSUser` for the job launched by SpringBoard PID 34.
Setup PID 37 obtained BackBoard display port 4611. The native
main-screen request returned status 0 and dimensions 1125×2436.
After the optional proximity resume check returned false, Setup
committed three QuartzCore contexts.

BackBoard submitted IOSurface 5 in six captured swaps after those
commits. The active pixels of all six captures were black. In a
separate diagnostic on the same guest, the debugger redirected a
null Metal result into QuartzCore's software-context constructor.
Three more swaps also presented black pixels from IOSurface 5.
These captures establish the framebuffer transfer. They contain
no visible Setup interface.

A read-only trace of the software renderer then observed
`SWContext::set_destination` and `SWContext::draw_elements`. The
1125×2436 destination at a 4608-byte stride contained the native
Hello screen when read from BackBoard's memory. The display still
selected a separate 1220×2712 surface with a 5120-byte stride.

The one-frame software scanout replay captured the native
1125×2436 pixels after drawing and scaled them to 1220×2712. The
debugger copied those bytes to the IOSurface already selected by
native SwapEnd, immediately before AppleCLCD read its first row.
The debugger then captured the physical framebuffer after present.
The Hello screen is visible in that capture.

SpringBoard PID 34 launched Setup PID 37 in `user/501`. Setup
received BackBoard display port 5891 and a successful native screen
reply. `SwapSetLayer` and `SwapEnd` 215 both identify IOSurface 5,
layer 0. Five sampled rows and all 3,308,640 active BGRA pixels
matched the scaled software source. The console-text decoder
reported incomplete decode on the graphical frame. The raw pixel
verifier and visual inspection confirmed the frame.

The evidence and both raw buffers are in
`work/quartzcore-setup-qemu-20261107/physical-hello`. The physical
PNG SHA-256 is
`9a9d229e82e0577cdc235b92530c1db62d0626ed31d3f2476e5357112461f010`.
The verification manifest SHA-256 is
`d87d314412d2ca9f8e13bd668e0fa7f4bc26def58abf421cb8e77e040c57f104`.

## Local replay

Use `prepare-duchamp-quartzcore-root.py` to create a fresh copy with the
QEMU-only BackBoard service change and the pinned UIKitCore resources.
Supply the matching CoreNLP and langid tree with `--language-resources`.
Supply the matching UIKitCore Artwork and CoverSheet tree with
`--artwork-resources`.
Supply the matching AddressBookLegacy tree with `--address-book-resources`.
Supply the matching CoreEmoji tree with `--emoji-resources`.
Supply the matching Setup app and framework tree with `--setup-resources`.
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
`work/quartzcore-qemu-20261107`. The first eligible present is captured immediately after the native kernel
call returns. Run `tools/verify-duchamp-native-frame.py RUN_DIRECTORY`
to check the layer ID, SwapEnd record and bytes. The report tracks whether
the active framebuffer contains any nonblack RGB pixels separately from
transfer verification.
For a Setup replay, set `SWEET_QEMU_SETUP_TRACE=1` for the QEMU runner.
The debugger records SpringBoard's Setup transition and activation
calls, follows Setup's native cache and context commits, and captures
later swaps. Use `--swap-id` to verify one numbered capture.

To test the session correction, set `SWEET_QEMU_SETUP_SESSION=1` with
the Setup trace. The debugger checks the running PID 1 image and the
exact legacy Setup job label. It selects the existing `user/501`
domain, follows the submitted and normalized job pointers, and supplies
the existing `iOSUser` name when the session argument is absent.
The native validator and the job submission report their results
separately. The experiment changes only live QEMU registers.

`SWEET_QEMU_SETUP_WITHOUT_PROXIMITY=1` runs a separate manual-setup
experiment. It checks the code at the expected Setup offset and
returns false from its proximity resume check inside QEMU. This mode
arms the scanout trace after the first Setup context commit to limit
debugger stops during launch. The display trace records Setup's
BackBoard Mach port and the native main-screen service reply
separately from any verified scanout.

For the one-frame scanout experiment, enable
`SWEET_QEMU_SETUP_SOFTWARE_SCANOUT=1` alongside the Setup trace,
session correction, manual setup and software renderer switches.
The experiment uses nearest-neighbor scaling in QEMU. Verify the
captured swap with the frame checker. When the software blit is in
the trace, it also checks every active framebuffer pixel against
the saved native software buffer.

For continuous Setup scanout and one bottom-edge swipe, add
`SWEET_QEMU_SETUP_SWIPE=1` and the QEMU boot argument
`sweethidtest=15`. The debugger uses the kernel's existing test
timer to feed the registered touchscreen with a down event, moves
and an up event. It traces touchscreen clients and queue submissions,
and refreshes the native layer after changed QuartzCore draws. It
saves the software buffer and the physical scanout under the same
SwapEnd number for each sampled frame.

BackBoard needs the original arm64 20F66
`/System/Library/HIDPlugins/ServicePlugins/IOHIDEventServicePlugin.plugin`
bundle in the test root to open the `HIDServiceSupport` device. The
local replay helper can install the three bundle files into the
QEMU RAM copy and verify their bytes by readback. Its
`SWEET_QEMU_SETUP_HID_PLUGIN` input is a private directory with
`Info.plist`, `IOHIDEventServicePlugin` and `CodeResources`.
No Apple files are included in the repository.

The gesture-v4 replay enqueued all ten touchscreen events to
BackBoard and reached Setup's native language table. The captured
language list is visible in `native-frame-00000417.png`. SwapEnd
1047 and SwapSetLayer agree on layer 0, IOSurface 5. The verifier
matched every active pixel at 1220×2712. The image is dim and some
language labels show missing glyphs. The evidence directory
`work/quartzcore-setup-qemu-20261107/gesture-v4` retains the trace and
the compressed raw software and framebuffer buffers.

The local Setup replay can restore the matching 20F66 fallback fonts
with `SWEET_QEMU_SETUP_FONTS`. Use `tools/extract-duchamp-setup-fonts.py` on
the original system image's `System/Library/Fonts` directory. The
replay pins the manifest, grows only the temporary HFS RAM copy by
128 MiB, and hashes all installed files again after reading them
back. The existing 3 GiB base image is retained.

Add `SWEET_QEMU_SETUP_REGION=1` to the swipe replay with the fonts
and HID bundle installed. After the native language table draws
its rows, the debugger saves the language frame and feeds a tap
through SweetHIDTouch at the first row. The trace records the
selected index and native locale controller. Subsequent captures
record the region phase and use the same per-swap pixel verifier.

In region-v1 the language list at SwapEnd 631 shows the restored
Chinese, Japanese, Korean, Arabic and Thai labels. Setup accepted
row 0, labeled English, and displayed Select Your Country or Region
at SwapEnd 793. Both captures verify against IOSurface 5, layer 0.
The PNGs, per-swap raw buffers and trace are in
`work/quartzcore-setup-qemu-20261107/region-v1`.
