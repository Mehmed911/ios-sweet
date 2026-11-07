#!/usr/bin/env python3
"""Submit a known BGRA frame to AppleCLCD and check the stopped QEMU scanout."""
import argparse
import importlib.util
import json
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
UI_FIXTURE = REPO / 'work/ui-surface-qemu-v3/evidence'
UI_ROOT_PIN = '10ed2fc8043e5c8d0515e2544bb741b82fd49ab6357c7589ac5d14f943f1d524'
HFS_PIN = 'be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b'
JOB = '/System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist'
PROBE = '/sbin/sweet-compositor-frame'


def check_pixels(raw):
    x, y, width, height, stride = 521, 1801, 64, 32, 4992
    if len(raw) != stride * 2712:
        raise ValueError('unexpected framebuffer extent')
    expected = [[0xff000000 | (col * 4 << 16) | (row * 8 << 8) | ((col * 13 + row * 7) & 255)
                 for col in range(width)] for row in range(height)]
    return sum(actual == pixel for row, line in enumerate(expected)
               for actual, pixel in zip(struct.unpack_from('<64I', raw, (y + row) * stride + x * 4), line))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('service_ram', REPO / 'tools/qemu-service-ram.py')
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    base, helper = UI_FIXTURE / 'root.hfs', UI_FIXTURE / 'hfsplus'
    vm.require(vm.sha(base) == UI_ROOT_PIN and vm.sha(helper) == HFS_PIN, 'fixture pin mismatch')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    native = Path(tempfile.mkdtemp(prefix='compositor-frame-', dir=Path.home() / '.cache/duchamp-qemu-tests'))
    print('QEMU scanout probe working directory:', native, flush=True)
    root = Path(shutil.copyfile(base, native / 'root.hfs'))
    helper = Path(shutil.copyfile(helper, native / 'hfsplus'))
    helper.chmod(0o755)
    runtime = UI_FIXTURE / 'runtime'
    frameworks = runtime / 'System/Library/Frameworks'
    program, obj = native / 'probe', native / 'probe.o'
    compile_log = out / 'build.log'

    def run(*argv):
        with compile_log.open('a') as log:
            subprocess.run([str(arg) for arg in argv], check=True, stdout=log, stderr=subprocess.STDOUT)

    run('clang', '-target', 'arm64-apple-ios16.5', '-Wall', '-Wextra', '-Werror', '-O1',
        '-fno-stack-protector', '-fno-builtin', '-c', REPO / 'tools/sweet-compositor-frame.m', '-o', obj)
    run('ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5', '-adhoc_codesign',
        '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'), '-lSystem.B', '-lobjc.A',
        '-F' + str(frameworks), '-framework', 'Foundation', '-framework', 'CoreFoundation',
        '-framework', 'IOSurface', frameworks / 'IOKit.framework/Versions/A/IOKit', '-e', '_main', '-o', program, obj)
    job = native / 'probe.plist'
    job.write_bytes(plistlib.dumps(dict(Label='org.sweet.qemu.compositor-frame', ProgramArguments=[PROBE],
        RunAtLoad=True, UserName='root', GroupName='wheel', LimitLoadToSessionType='System',
        StandardOutPath='/dev/console', StandardErrorPath='/dev/console')))
    for source, guest, mode in ((job, JOB, '644'), (program, PROBE, '755')):
        run(helper, root, 'add', source, guest)
        run(helper, root, 'chmod', mode, guest)
        roundtrip = native / 'roundtrip'
        run(helper, root, 'extract', guest, roundtrip)
        vm.require(vm.sha(source) == vm.sha(roundtrip), 'installation mismatch: ' + guest)
        roundtrip.unlink()

    cmdline = ('debug=0xc serial=3 cpus=1 keepsyms=1 -noprogress rd=md0 rootrw=1 sweet_console_fb=1 '
               'duchamp_timer_irq_ack=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet sweetfb_noconsole=1')
    evidence = native / 'run'
    result = vm.run_vm(REPO / 'work/ci-41543710742-kernel/artifact/kernel.development.sweet',
        REPO / 'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt', root,
        evidence, 75, ['SWEET EARLY PANIC:', 'Library not loaded:', 'Symbol not found:', 'frame-probe: FAIL'], cmdline)
    for name in ('layout.json', 'result.json', 'fb.raw', 'fb.png', 'fb.txt', 'qemu-stderr.txt'):
        source = evidence / name
        if source.is_file():
            shutil.copyfile(source, out / name)
    run(helper, evidence / 'ramdisk-final.hfs', 'extract', '/private/var/tmp/ipc-frame-probe.log', out / 'probe.log')
    guest = (out / 'probe.log').read_text()
    raw = (out / 'fb.raw').read_bytes()
    matched = check_pixels(raw)
    checks = dict(all_2048_bgra_pixels=matched == 2048,
        launchd_child='ppid=1 uid=0 parent=/sbin/launchd' in guest,
        swap_submitted='FRAME SUBMITTED ' in guest and 'FAIL ' not in guest,
        stopped_scanout_saved=result.get('saved_guest_root') is True and not result['stop_marker'],
        roots_unchanged=result['source_root_unchanged'] and vm.sha(base) == UI_ROOT_PIN)
    report = dict(passed=all(checks.values()), checks=checks, matched_pixels=matched,
        framebuffer_sha256=vm.sha(out / 'fb.raw'), probe_sha256=vm.sha(program), native_run=str(evidence),
        elapsed_host_seconds=result['elapsed_host_seconds'], rectangle=[521, 1801, 64, 32],
        scope=dict(qemu_only=True, synthetic_frame=True, native_compositor=False, gpu=False))
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
