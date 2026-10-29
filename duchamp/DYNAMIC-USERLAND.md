# C through dyld and libSystem in QEMU

This separate test uses Apple's standalone plain-arm64 restore runtime from
iOS 16.5 (20F66, iPhone X), not the multi-gigabyte system shared cache. The
dependency audit requires 37 files totaling 10,401,536 bytes. It checks Mach-O
architecture, platform metadata, signature-command presence, and all required
library paths. Execution is tested under this development kernel's policy;
signature-command presence does not establish cryptographic trust, production
signing enforcement, or entitlement compatibility.

Apple's files are fetched from its public IPSW and kept under ignored
`research/`. No Apple runtime binaries are included in this repository.

## Prepare the runtime

Requires Python 3, curl, and a recent 7-Zip that can read APFS:

```sh
python3 tools/prepare-darwin-runtime.py research/darwin-20F66
```

Only the 106,954,779-byte restore disk ZIP member is downloaded (about 92 MB
compressed). Its pinned SHA-256 is
`8223b75c9399dfc8cf0971374527d710b69e29e8ef69722b98a82902199fcff5`.
The tool parses IM4P, requires the plain APFS payload, extracts selected
libraries, and audits their dependency closure. It performs no decryption.
Use `--img4 PATH` to reuse the exact downloaded member. An existing
`runtime-root` is never overwritten.

The source URL and APFS hash are saved in `source.json`. The public reference
for the IPSW/version is HackiOS's
[fetch helper](https://github.com/oosexgang/hakios-xnu-kernel/blob/main/sysimage/fetch-from-ipsw.py).

## Build an HFS authoring tool

The host needs the `hfsplus` utility from
[libdmg-hfsplus](https://github.com/planetbeing/libdmg-hfsplus), tested at commit
`7ac55ec64c96f7800d9818ce64c79670e7f02b67`. It edits only a new copy of the
32 MiB HFS baseline. `build-dynamic-root.py` re-extracts every installed file
and compares its bytes with the source, because a host tool's exit code alone
does not prove that an image was populated correctly. The original image is
preserved. This works without a host HFS kernel module or a filesystem mount.

## Build and run

Needs clang, ld64.lld, llvm-nm, QEMU, Python 3, and the HFS tool above. Run from
the repository in Linux/WSL, using the existing kernel from Actions 104:

```sh
sh tools/test-sweet-dynamic.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/qemu-rootvnode-98/root-with-launchd.hfs \
  research/dyld-runtime-20F66/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/userland-dynamic-new 90
```

The output directory must not exist. The C test declares its small Darwin ABI
surface explicitly so it does not need an SDK's headers. It links against the
real runtime libraries with LC_LOAD_DYLINKER `/usr/lib/dyld`, LC_MAIN, and an
ad-hoc code signature. No replacement libc or loader is provided.
The QEMU runner keeps its temporary monitor socket in /tmp and removes it
afterward, allowing these long Windows/WSL artifact paths.

A static PID 1 redirects stdin/stdout/stderr to `/dev/console`, forks, and
execs `/sbin/c-runtime-test`. The C program inspects dyld's loaded image list,
requires libSystem, uses printf, writes/closes/reopens/reads a file and checks
EOF, then calls libc fork/waitpid and verifies child exit 42. The harness
requires the C program's own exit status 0 and stays alive afterward.

The QEMU-only boot arguments add `unentitled_ios_sim_launch=1` because this
kernel was built for macOS while the supplied runtime/program target iOS.
`DYLD_SHARED_REGION=avoid` selects on-disk standalone libraries. Nothing here
establishes phone, UFS, or full iOS userland compatibility.

`run/verification.json` requires all observed C milestones, the linked binary's
loader/dependency metadata, clean child exit, and continuing PID 1 heartbeats.
`no_panic_observed` by itself is insufficient. The first 45-second probe
ended before main. The first 90-second build executed all C milestones but
lacked LC_CODE_SIGNATURE; the verifier correctly rejected it. Adding explicit
`-adhoc_codesign` fixed the build metadata. The final untouched wrapper run
completed for 90 seconds with exit 0 and all 15 checks true, zero unknown
glyphs, and no visible panic. Verified artifacts are under
`work/userland-dynamic-final/`, including `run/verification.json` and `run/fb.txt`.
The C program reported PID 2 and 37 loaded images, its fork child PID 3, and
the harness observed clean exit 0 followed by repeated heartbeats.

The final program SHA-256 is
`8a8427fc901b7d4041079e80e6965253ddb15a031918fcd04d2b5476f6a8953f`;
root `750fc8ec3e2452a708da00aa078a8f6b65d7f27333c18cba17add0899ea67c91`;
payload `422bd7cb12fd82d502cde09070d06822b417ec4f9e9137d23ed0665d7ddd0e05`.
The kernel was reused unchanged from Actions 104, SHA-256
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`.

## Original launchd: separate QEMU test

The same restore disk contains `/sbin/launchd` (525,088 bytes, SHA-256
`4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06`)
and `/usr/libexec/xpcproxy` (96,352 bytes, SHA-256
`2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f`).
Both are plain arm64/iOS Mach-O executables with LC_MAIN and signature
commands. Their required direct libraries are libSystem and libobjc, already
in the tested closure. xpcproxy also names libcryptex_trampoline as a weak
dependency; it is not installed in this test image. Absence of a required
library is therefore not an observed launchd blocker, but runtime behavior
needed the separate guest test described below.

The launchd import list includes Mach port/message operations, dispatch,
host special ports, csops, sandbox checks, and private posix_spawn options.
xpcproxy also imports private spawn/sandbox interfaces. A single running
service exercises only part of these interfaces; successful printf/fork
alone did not establish their behavior. Embedded paths include `/dev/console`,
`/dev/null`, `/private/var/tmp`, and `/private/var/db/com.apple.xpc.launchd`.

The follow-on test in [LAUNCHD-QEMU.md](LAUNCHD-QEMU.md) boots the original
launchd as PID 1 with xpcproxy and one controlled C service, using a separate
root image. It records startup errors and service output. The five supplied
LaunchDaemons are not copied: they include iPhone restore jobs such as
restored_external and diskimagesiod. This earlier dynamic C test still uses
our static diagnostic harness at `/sbin/launchd`.
