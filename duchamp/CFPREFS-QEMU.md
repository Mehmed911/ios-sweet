# Original cfprefsd / NSUserDefaults in QEMU

This fixture is confined to QEMU and its HFS+ RAM root. It does not connect
to a phone or access UFS, USB or boot partitions.

The grouped live-update and service-restart scenario is documented in
[CFPREFS-BATCH-QEMU.md](CFPREFS-BATCH-QEMU.md).

## Verified result — 2026-10-30

The final run, work/launchctl-cfprefs-v5, exited 0 and passed **49/49
checks**, including **112 file-hash checks** (110 installed files plus
original launchd and xpcproxy). Its runtime audit found 92 binaries with
no missing strong or explicitly observed dynamic dependencies.

The writer was PID 5, independent readers were PIDs 12 and 15, the observer
was PID 3, and the selected regular cfprefsd was PID 7. The original
regular endpoint stayed running with runs=1 and the same PID before and
after both reads. The separate system-session job stayed unstarted with
runs=0; this test does not claim that endpoint was exercised. All ten
actual launchctl processes exited 0. The writer and both reader runs
exited normally with status 0 and were reaped; they remained stopped
through two heartbeats.

All three probes verified that direct creation and reading failed with
ENOENT at all three standard preference paths inside the empty chroot.
Both fresh readers obtained all three exact values without a setter call.
The saved real-root plist at
/private/var/root/Library/Preferences/org.sweet.qemu.preferences.plist
contained exactly device="DUCHAMP", integer soc=6897 and boolean
enabled=true. The saved chroot directory was still empty.

The VM stopped on its second success heartbeat after **978.85 host
seconds**, with 75 sampled frames, zero unknown glyphs and no visible
kernel panic. No new kernel build or GitHub Actions run was needed.

| Local artifact | SHA-256 |
| --- | --- |
| Initial RAM root | 14dde88259e13d1f5c352d7eee4ec1c7c02afd74305180626db54e119f86abba |
| Payload | 33579779ba49f0fb307bf9a0e7e5eee47c6f0fc7f70aec58f58234be1f399f68 |
| Saved RAM root | a648ed135606d03c51dcc1f838ce0310d936ea95b5c72ab78eabdac1bc2173f7 |

The complete report is work/launchctl-cfprefs-v5/run/verification.json;
captured guest files are in work/launchctl-cfprefs-v5/guest/.
Failed attempts v1 through v4 remain preserved.

## Inputs and provenance

The original 20F66 system-image cfprefsd is 53,232 bytes, plain ARM64,
targets iOS 16.5 and reports source version 1977. Its only external import
is `__CFXPreferencesDaemon_main`, supplied by the pinned CoreFoundation.
Its SHA-256 is:

`05e6c217284c2e4f669243fe24296f3ba9abb53a750c9d3860348b0b43c978e2`.

Both original launch jobs are recorded in the local runtime's source.json:

| Original job | SHA-256 |
| --- | --- |
| com.apple.cfprefsd.xpc.daemon.plist | 16aa60c1effb6b7e7775712582bf4572c56ca1a25d1aca322eb822b03a06189f |
| com.apple.cfprefsd.xpc.daemon.system.plist | a34c6b85e29c1523d84597c81393e048c70274e5871c346d1969a7d413658f77 |

They export the separate native Mach names `com.apple.cfprefsd.daemon`
and `com.apple.cfprefsd.daemon.system`. For this fixture both jobs are
enabled on demand in the System session, as root/wheel, without KeepAlive.
The original system job's conditional feature-flag Disabled rule is
explicitly overridden in the test job. No Mach-name aliases are added.
The daemon and framework executable bytes remain unmodified.

The selectively extracted system-image member is 096-04088-077.dmg,
volume SydneyF20F66.D22D221OS. These are local file hashes, not an
independent whole-system-image signature verification.

The runtime merges the existing pinned Foundation closure with original
syslogd and notifyd and adds cfprefsd plus its observed dynamic
MobileCoreServices closure: 92 audited Mach-O files, 107,016,192 bytes,
plus seven existing Foundation resources. Apple files
and system images stay outside Git.

## What the test requires

- A separate Objective-C writer uses NSUserDefaults with suite
  `org.sweet.qemu.preferences`. It sets device="DUCHAMP", soc=6897 and
  enabled=true, calls synchronize and verifies exact readback.
- A separate reader uses the same public API and does not set values.
  Original launchd starts it through the pinned Procursus launchctl.
  The observer runs the reader twice and requires distinct PIDs,
  normal exit status zero and launchd runs=1 then runs=2.
- Each probe first loads the observed dynamic MobileCoreServices library,
  requires its FSEventStreamCreate symbol and initializes the NSUserDefaults
  class. It warms the preferences runtime by reading the unset key "unused"
  from the independent domain org.sweet.qemu.runtime-warmup, with no value
  setters. This does not create/read/write the fixture suite. It then
  enters an empty chroot and changes cwd to its new root
  before creating NSUserDefaults or accessing any preference. The probes
  verify ENOENT for attempted direct creation at all three standard root
  preference paths, and again for reading those paths after the API calls.
  No directory descriptor or cwd outside the jail is retained. Outside
  descriptors point only to the console and regular log/readiness/release files;
  those files carry no preference values. Bootstrap Mach ports continue
  to reach the original daemon outside the jail.
- Native launchd records identify the original daemon, which must stay
  at the same PID with runs=1. Only the isolated writer sets the values;
  two independent isolated reader processes must receive all three.
  Direct-file fallback cannot reach the real plist from these probes.
- The host reopens the saved RAM filesystem and requires a real plist
  with the three exact values and their integer/boolean types.
- All installed file hashes and original launchd/xpcproxy hashes are
  rechecked after execution, alongside captured CLI output, daemon
  stability and two stopped-probe heartbeats.

There is no injected/interposing library in the final fixture and no
fabricated protocol response. This proves shared daemon-backed values
without claiming a per-message IPC payload trace. Successful readback
in the writer's own cache alone is explicitly insufficient.

## Replay

From the repository in WSL, with the previous local assets present:

```sh
python3 tools/prepare-cfprefs-runtime.py \
  research/foundation-runtime-20F66-v2/runtime-root \
  research/notifyd-runtime-20F66-v2/runtime-root \
  research/cfprefsd-20F66/apple-extracted \
  research/cfprefs-runtime-20F66-v2 \
  --dynamic-root research/foundation-20F66/apple-extracted \
  --apfs research/darwin-launchd-20F66/restore.apfs

sh tools/test-sweet-cfprefs.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt work/launchd-final/root.hfs \
  research/cfprefs-runtime-20F66-v2/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-cfprefs-v5 1500
```

Both scripts refuse an existing output directory. Select a fresh name
for another attempt. Never use a previous scenario's modified root as
the base. The kernel is the unchanged Actions 104 artifact:
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`.

The builder grows a fresh copy of the original diagnostic base to 128 MiB,
creates only absent directories, and re-extracts every installed file
for byte comparison. The runner saves its final RAM root and stops at
the second success heartbeat or a diagnostic failure.

## Scope

This test concerns local preferences shared between root programs under
one QEMU System session. Persistence is within the saved RAM filesystem.
It does not establish persistence across a reboot, sandboxed application
domains, daemon restart, concurrent writers, iOS UI readiness or MT6897
hardware compatibility.
The FSEvents service and filesystem-change delivery are not tested here.

## First failed attempt and diagnosis

The initial 85-file strong closure passed its dependency audit, but QEMU
rejected it: cfprefsd repeatedly died with SIGSEGV. The writer read its
own cached values, without a verified daemon roundtrip or a saved plist.
The failure gate correctly rejected that result. The attempt is preserved
at work/launchctl-cfprefs: 440.585 host seconds, zero unknown glyphs and
no visible kernel panic, stopped on the writer FAIL marker.

A separate debug boot used a hardware breakpoint at address zero.
It captured PC=0, x8=0 and LR=0x100e22fd0. Matching the preceding
instructions against the pinned files identified CoreFoundation file
offset 0xfafd0, in `_onqueue_locked_CFPrefsRecreateFileWatcher`.
The instruction at 0xfafcc was `blr x8`, using the unset
FSEventStreamCreate pointer. The CF initializer at 0x187738 obtains that
pointer through dlopen of
/System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices
and dlsym. That framework was absent from the first image.

MobileCoreServices reexports CoreServices; the latter actually exports
FSEventStreamCreate in this restore. Its seven additional strong-closure
files fit the existing 128 MiB volume. The correction adds these original
files and audits MobileCoreServices as an explicit entry. It does not
patch the null call or fabricate an FSEvents implementation. Debug
registers, instruction bytes and the file match are preserved locally
under work/cfprefs-null-debug.

The second attempt (work/launchctl-cfprefs-v2) included that closure.
The sampled SIGSEGV disappeared and a plist with two values was saved.
It still failed the transport gate: no interpose hook ran, including
the connection-creation hook. That is not a successful preferences test.
The final fixture replaces that unavailable observation method with
filesystem isolation, while retaining the requirement for all three
values, two independent readers, a saved plist and stable original daemon.
The failed images and their reports remain untouched.

The third attempt (work/launchctl-cfprefs-v3) entered the empty root
successfully and proved direct creation failed at all three paths, but
the writer then died with SIGSEGV when starting NSUserDefaults. The host
stopped this VM after the sampled failure, saved its halted RAM root,
and recorded host-stop.txt. Its 460.87-second report is a failed,
host-stopped attempt, not a passed kernel/service test.

The fourth attempt prepared the dynamic library and class but still
failed with a sampled writer SIGSEGV. The periodic-frame null observer
instead caught a normal QMP sampling pause at a nonzero kernel PC; that
record is explicitly marked as invalid fault evidence in observer-note.txt.
It is not a kernel crash or a null-branch diagnosis. That observer was
disconnected, and a separate boot without periodic sampling is used for
fault diagnosis.

The subsequent fixture warms the runtime on an independent empty domain
before isolation, while delaying every fixture-suite access until after
chroot. The runner also stops immediately on sampled SIGSEGV. No successful
preference persistence is inferred from the failed attempts.

The separate chroot debug boot watched PC=0 but did not catch this later
failure. Reviewing v4's exception log instead showed a data abort at
FAR=8 and nonzero ELR=0x100ba674c. Its precise function was not established;
the host stopped the unsuitable diagnostic VM. The observed correction
is initialization on the separate empty domain before chroot, verified
by all three successful probes in v5. This is not attributed to a
particular unverified internal function.
