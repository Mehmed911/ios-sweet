#!/usr/bin/env python3
"""Build the 0BSD IOKit probe and run the exact source-built XNU in QEMU.

Only copied RAM-root fixtures are modified. No phone transport is present.
"""
import argparse
import hashlib
import json
import plistlib
from pathlib import Path
import re
import subprocess
import sys
import qemu_ramroot_var as layout
import duchamp_source_kernel

KERNEL_SHA = 'e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--kernel', type=Path, required=True)
    ap.add_argument('--mkfs', type=Path, required=True)
    ap.add_argument('--compositor', action='store_true', help='also run the separate compositor and two clients')
    ap.add_argument('--kernel-manifest', type=Path, help='explicit receipt for a new source-linked kernel')
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir()
    kernel = args.kernel.resolve()
    try:
        kernel_sha = duchamp_source_kernel.select(kernel, args.kernel_manifest)
    except ValueError as e:
        ap.error(str(e))
    runtime = layout.REPO / 'research/dyld-runtime-20F66/runtime-root'
    hfs = layout.REPO / 'research/libdmg-hfsplus-build/hfsplus'
    commands = []

    def run(argv, timeout=60):
        argv = list(map(str, argv))
        log = out / f'command-{len(commands):03}.log'
        with log.open('wb') as stream:
            result = subprocess.run(argv, cwd=layout.REPO, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        commands.append(dict(argv=argv, cwd=str(layout.REPO), exit_code=result.returncode,
                             log=str(log), sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode:
            print(log.read_text(errors='replace'))
            raise RuntimeError('command failed: ' + str(log))

    run(['clang', '-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
         '-Wall', '-Wextra', '-Werror', 'tools/test-duchamp-iokit-wire.c', '-o', out / 'wire-native'])
    run([out / 'wire-native'])
    run([sys.executable, '-B', 'tools/test-qemu-frame-witness.py'])
    if args.compositor:
        run(['clang', '-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
             '-Wall', '-Wextra', '-Werror', 'tools/duchamp-compositor-core.c',
             'tools/test-duchamp-compositor-core.c', '-o', out / 'core-native'])
        run([out / 'core-native'])
    for name, source, flags in (
            ('graphics', 'tools/duchamp-darwin-graphics.c', []),
            ('controller', 'tools/sweet-launchctl-control.c',
             ['-DSWEET_SYSLOGD_TEST=1', '-DSWEET_NOTIFYD_TEST=1', '-DDUCHAMP_DARWIN_GRAPHICS_TEST=1'] +
             (['-DDUCHAMP_COMPOSITOR_TEST=1'] if args.compositor else []))):
        run(['clang', '-target', 'arm64-apple-ios16.5', '-mcpu=generic', '-march=armv8-a',
             '-O1', '-Wall', '-Wextra', '-Werror', '-fno-builtin', '-fno-stack-protector',
             *flags, '-c', source, '-o', out / (name + '.o')])
        run(['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5',
             '-adhoc_codesign', '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'),
             '-lSystem.B', '-e', '_main', '-o', out / name, out / (name + '.o')])
    signer = layout.REPO / 'research/host-ipsw-3.1.739/ipsw'
    if hashlib.sha256(signer.read_bytes()).hexdigest() != '7f22f07821cd964c0333172ef9bac734b53df5035a5e7c8ce9ec1580891f6d4c':
        raise RuntimeError('offline signing tool changed')
    entitlement = {'com.apple.hid.system.user-access-service': True}
    entfile = out / 'graphics.entitlements.plist'
    entfile.write_bytes(plistlib.dumps(entitlement))
    run([signer, 'macho', 'sign', '--id', 'org.duchamp.qemu.graphics', '--ad-hoc',
         '--ent', entfile, '--output', out / 'graphics-signed', out / 'graphics'])
    run([signer, 'macho', 'info', out / 'graphics-signed', '--ent'])
    if plistlib.loads(Path(commands[-1]['log']).read_bytes()) != entitlement:
        raise RuntimeError('unexpected graphics entitlement set')
    extra_guest = []
    if args.compositor:
        for name in ('duchamp-compositor-core', 'duchamp-darwin-compositor'):
            run(['clang', '-target', 'arm64-apple-ios16.5', '-mcpu=generic', '-march=armv8-a',
                 '-O1', '-Wall', '-Wextra', '-Werror', '-fno-builtin', '-fno-stack-protector',
                 '-c', 'tools/' + name + '.c', '-o', out / (name + '.o')])
        run(['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5',
             '-adhoc_codesign', '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'), '-lSystem.B',
             '-e', '_main', '-o', out / 'compositor-client', out / 'duchamp-compositor-core.o', out / 'duchamp-darwin-compositor.o'])
        run([signer, 'macho', 'sign', '--id', 'org.duchamp.qemu.compositor', '--ad-hoc',
             '--ent', entfile, '--output', out / 'compositor-service', out / 'compositor-client'])
        run([signer, 'macho', 'info', out / 'compositor-service', '--ent'])
        if plistlib.loads(Path(commands[-1]['log']).read_bytes()) != entitlement:
            raise RuntimeError('unexpected compositor entitlement set')
        import duchamp_compositor_expectations
        sequence = duchamp_compositor_expectations.write(out)
        extra_guest = ['--compositor-binary', out / 'compositor-service',
                       '--compositor-client', out / 'compositor-client', '--frame-sequence', sequence]
    pixels = b''.join((0xff000000 | ((x * 4) << 16) | ((y * 8) << 8) |
                       ((x * 13 + y * 7) & 255)).to_bytes(4, 'little')
                      for y in range(32) for x in range(64))
    spec = out / 'frame-spec.json'
    spec.write_text(json.dumps(dict(x=160, y=1600, width=64, height=32,
                                   sha256=hashlib.sha256(pixels).hexdigest()), indent=2) + '\n')
    guest = out / 'guest'
    run([sys.executable, '-B', 'tools/test-duchamp-readonly-var.py', guest,
         '--kernel', kernel, '--mkfs', args.mkfs.resolve(), '--var-mib', '4',
         '--graphics-probe', out / 'graphics-signed', '--graphics-controller', out / 'controller',
         '--frame-witness', spec, *extra_guest], timeout=540)
    for source, dest in (('/tmp/duchamp-graphics-witness', 'graphics-witness.txt'),
                         ('/tmp/ipc-darwin-gfx.log', 'graphics-trace.txt')):
        run([hfs, guest / 'run/var-final.hfs', 'extract', source, out / dest])
    trace = (out / 'graphics-trace.txt').read_text()
    witness_path = out / 'graphics-witness.txt'
    frame_path = guest / 'run/framebuffer-witness.json'
    if not witness_path.read_bytes().strip() or not frame_path.is_file():
        report = dict(passed=False, failure='guest did not produce both process and framebuffer witnesses',
                      trace=trace, kernel_sha256=kernel_sha, phone_operations=[], physical_ufs_enabled=False)
        (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        return 1
    witness = dict(line.split('=', 1) for line in witness_path.read_text().splitlines())
    frame = json.loads(frame_path.read_text())
    original = json.loads((guest / 'verification.json').read_text())
    checks = {
        'source_kernel_unchanged': hashlib.sha256(kernel.read_bytes()).hexdigest() == kernel_sha,
        'dynamic_process_under_launchd': int(witness['pid']) > 1 and witness['ppid'] == '1' and int(witness['images']) > 1,
        'four_services_match_and_absent_rejected': 'MATCH AppleCLCD IOCoreSurfaceRoot SweetHIDButtons SweetHIDTouch; absent rejected' in trace,
        'actual_shared_hid_queue': int(witness['input_events']) >= 2 and int(witness['notifications']) >= 1,
        'press_and_release_order': re.search(r'INPUT event=1 down=1 .*INPUT event=2 down=0', trace, re.S) is not None,
        'surface_and_swap_identified': int(witness['surface']) > 0 and int(witness['swap']) > 0 and
            f"surface={witness['surface']} rect=160,1600,64,32" in trace,
        'framebuffer_bytes_match': frame['matched'] and (guest / 'run/framebuffer-witness.raw').read_bytes() == pixels,
        'ramroot_and_services_preserved': original['passed'] and original['checks']['services_pass_all_74'],
        'readonly_root_preserved': original['checks']['root_dump_identical'] and original['checks']['root_write_rejected'],
        'writable_var_preserved': original['checks']['writable_var_and_alias'] and original['checks']['enospc_and_recovery'],
    }
    report = dict(passed=all(checks.values()), checks=checks, kernel_sha256=kernel_sha,
                  witness=witness, framebuffer=frame, phone_operations=[], physical_ufs_enabled=False,
                  screenshot=str(guest / 'run/framebuffer-witness.png'),
                  scope='QEMU diagnostic pattern and virtual keyboard; no SpringBoard or physical GPU/input claim')
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
