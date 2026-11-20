#!/usr/bin/env python3
"""Run the isolated Duchamp read-only root and writable var QEMU test."""
import argparse
import json
import plistlib
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

import qemu_ramroot_var as layout

REPO = layout.REPO
ADT = REPO / 'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt'
SERVICES = REPO / 'work/launchctl-notifyd-v3'
HFS = REPO / 'research/libdmg-hfsplus-build/hfsplus'
RUNTIME = REPO / 'research/dyld-runtime-20F66/runtime-root'
PYTHON = (sys.executable, '-B')
FAILURES = {
    'missing-mountpoint': 'VAR PREFLIGHT FAIL missing /private/var errno=2',
    'missing-md1': 'DUCHAMP DUAL RAMDISK missing RAMDisk or',
    'failed-mount': 'VAR PREFLIGHT FAIL mount /dev/md1 errno=',
    'bad-permissions': 'VAR PREFLIGHT FAIL tmp permissions errno=0',
    'bad-alias': 'VAR PREFLIGHT FAIL /var resolution errno=0',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--kernel', type=Path, required=True, help='source-built SWEET kernel')
    ap.add_argument('--mkfs', type=Path, required=True, help='host mkfs.hfsplus executable')
    ap.add_argument('--adt', type=Path, default=ADT, help='storage-free QEMU base ADT')
    ap.add_argument('--service-fixture', type=Path, default=SERVICES, help='verified service root and manifests')
    ap.add_argument('--hfs-tool', type=Path, default=HFS, help='host hfsplus image editor')
    ap.add_argument('--runtime', type=Path, default=RUNTIME, help='Darwin library root used by the probe linker')
    ap.add_argument('--prepare-only', action='store_true', help='generate the HFS+ images, ADT and payload')
    ap.add_argument('--case', choices=('success', *FAILURES), default='success')
    ap.add_argument('--var-mib', type=int, choices=(4, 8, 32), default=32,
                    help='writable volume size for the boot-image fit check')
    ap.add_argument('--graphics-probe', type=Path, help='opt-in QEMU diagnostic Mach-O, never a phone image')
    ap.add_argument('--graphics-controller', type=Path, help='matching controller with graphics bootstrap enabled')
    ap.add_argument('--frame-witness', type=Path, help='bounded QEMU framebuffer observation specification')
    ap.add_argument('--compositor-binary', type=Path, help='entitled QEMU compositor service')
    ap.add_argument('--compositor-client', type=Path, help='unentitled QEMU compositor clients')
    ap.add_argument('--gui-binary', type=Path, help='opt-in QEMU GUI experiment, never a phone payload')
    ap.add_argument('--live-input', type=Path, help='QEMU VirtIO input service binary, requires GUI')
    ap.add_argument('--live-runtime', type=Path, help='write live QMP/framebuffer connection details outside temporary guest directory')
    ap.add_argument('--interactive-input', action='store_true', help='prepare normal live jobs without the diagnostic observer')
    ap.add_argument('--touch-input', type=Path, help='native VirtIO multitouch service and managed-application profile')
    ap.add_argument('--frame-sequence', type=Path, help='ordered compositor framebuffer observations')
    args = ap.parse_args()
    if bool(args.graphics_probe) != bool(args.graphics_controller):
        ap.error('graphics probe and controller must be supplied together')
    if args.graphics_probe and (args.case != 'success' or not args.frame_witness):
        ap.error('graphics diagnostic requires success profile and frame witness')
    if any((args.compositor_binary, args.compositor_client)) and not all(
            (args.compositor_binary, args.compositor_client, args.frame_sequence, args.graphics_probe)):
        ap.error('compositor requires both binaries, frame sequence and graphics baseline')
    if args.gui_binary and (args.compositor_binary or not args.frame_sequence or not args.graphics_probe):
        ap.error('GUI requires separate frame sequence and graphics baseline')
    if args.frame_sequence and not (args.compositor_binary or args.gui_binary):
        ap.error('frame sequence requires compositor or GUI')
    if bool(args.live_input) != bool(args.live_runtime) or (args.live_input and not args.gui_binary):
        ap.error('live input requires its runtime output and GUI binary')
    if args.interactive_input and (not args.live_input or not args.prepare_only):
        ap.error('interactive input is a prepare-only live profile')
    if args.touch_input and (not args.live_input or not args.gui_binary):
        ap.error('touch input requires GUI and pointer profile')
    var_bytes = args.var_mib * 1024**2
    kernel = args.kernel.resolve()
    adt, fixture, hfs, runtime = (path.resolve() for path in
                                  (args.adt, args.service_fixture, args.hfs_tool, args.runtime))
    layout.require_source_kernel(kernel)
    out = args.output.resolve()
    out.mkdir()
    commands = []

    def run(*argv):
        command = [str(item) for item in argv]
        job = {'argv': command, 'cwd': str(REPO)}
        commands.append(job)
        with (out / f'command-{len(commands):03}.log').open('wb') as stream:
            result = subprocess.run(command, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT)
        job.update(exit_code=result.returncode, log=stream.name)
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        result.check_returncode()
        return Path(stream.name)

    inputs = [fixture / 'root.hfs', kernel, adt, args.mkfs.resolve(), hfs]
    if args.graphics_probe:
        inputs += [args.graphics_probe.resolve(), args.graphics_controller.resolve(), args.frame_witness.resolve()]
    if args.compositor_binary:
        inputs += [args.compositor_binary.resolve(), args.compositor_client.resolve(), args.frame_sequence.resolve()]
    if args.gui_binary:
        inputs += [args.gui_binary.resolve(), args.frame_sequence.resolve()]
    if args.live_input:
        inputs += [args.live_input.resolve()]
    before = {p: layout.digest(p.read_bytes()) for p in inputs}
    layout.check(before[fixture/'root.hfs'] ==
                 '3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf',
                 'services root digest mismatch')
    for name in ('launchctl-root-manifest.json', 'runtime-audit.json', 'sweet-launchd-service',
                 'sweet-ipc-client', 'sweet-launchctl-control'):
        shutil.copyfile(fixture / name, out / name)
    root, var = out / 'root.hfs', out / 'var.hfs'
    shutil.copyfile(fixture / 'root.hfs', root)
    with var.open('xb') as stream:
        stream.truncate(var_bytes)
    run(args.mkfs.resolve(), '-v', 'DuchampVar', var)
    run(hfs, root, 'mkdir', '/dev')
    if args.case == 'missing-mountpoint':
        run(hfs, root, 'mv', '/private/var', '/private/var-test-hidden')
    if args.case == 'bad-alias':
        run(hfs, root, 'symlink', '/var', '/private/etc')
    for directory in ('/tmp', '/run', '/log', '/db', '/root', '/mobile', '/empty',
                      '/log/com.apple.xpc.launchd', '/db/com.apple.xpc.launchd', '/db/launchd.db'):
        run(hfs, var, 'mkdir', directory)
        mode = ('700' if args.case == 'bad-permissions' else '1777') if directory == '/tmp' else '755'
        run(hfs, var, 'chmod', mode, directory)
    if args.case == 'failed-mount':
        # Keep the HFS+ signature, but give both volume headers an invalid allocation block size.
        with var.open('r+b') as image:
            for header in (1024, var_bytes - 1024):
                image.seek(header + 40)
                image.write(b'\0' * 4)
    bootstrap = out / 'launchd.sweet'
    preparation = out / 'duchamp-var-prepare'
    run('clang', '-target', 'arm64-apple-ios16.5', '-DDUCHAMP_WRITABLE_VAR',
        '-c', 'tools/sweet-launchd-bootstrap.S', '-o', out / 'bootstrap.o')
    run(*PYTHON, 'tools/mkinit.py', out / 'bootstrap.o', bootstrap)
    run('clang', '-target', 'arm64-apple-ios16.5', '-Wall', '-Wextra', '-Werror',
        '-O2', '-fno-builtin', '-fno-stack-protector', '-c', 'tools/duchamp-var-prepare.c',
        '-o', out / 'prepare.o')
    run('ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5',
        '-adhoc_codesign', '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'), '-lSystem.B',
        '-e', '_main', '-o', preparation, out / 'prepare.o')
    manifest_path = out / 'launchctl-root-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    installs = [('/usr/appleinternal/sbin/launchd.sweet', bootstrap),
                ('/sbin/duchamp-var-prepare', preparation)]
    if args.graphics_probe:
        job = out / 'duchamp-graphics.plist'
        job.write_bytes(plistlib.dumps({'Label': 'org.duchamp.qemu.graphics',
            'ProgramArguments': ['/sbin/duchamp-darwin-graphics'], 'RunAtLoad': True,
            'KeepAlive': False, 'LimitLoadToSessionType': 'System', 'UserName': 'root',
            'GroupName': 'wheel', 'StandardOutPath': '/dev/console', 'StandardErrorPath': '/dev/console'}))
        installs += [('/sbin/duchamp-darwin-graphics', args.graphics_probe.resolve()),
                     ('/sbin/duchamp-graphics.plist', job),
                     ('/sbin/sweet-launchctl-control', args.graphics_controller.resolve())]
    if args.compositor_binary:
        installs += [('/sbin/duchamp-compositor', args.compositor_binary.resolve()),
                     ('/sbin/duchamp-compositor-client', args.compositor_client.resolve())]
        for name, label, arguments in (
                ('compositor', 'org.duchamp.qemu.compositor', ['/sbin/duchamp-compositor', '--selftest']),
                ('red', 'org.duchamp.qemu.comp-red', ['/sbin/duchamp-compositor-client', 'red']),
                ('overlay', 'org.duchamp.qemu.comp-overlay', ['/sbin/duchamp-compositor-client', 'overlay']),
                ('compositor-normal', 'org.duchamp.qemu.compositor-normal', ['/sbin/duchamp-compositor']),
                ('early-red', 'org.duchamp.qemu.comp-early-red', ['/sbin/duchamp-compositor-client', 'red-exit']),
                ('early-overlay', 'org.duchamp.qemu.comp-early-overlay', ['/sbin/duchamp-compositor-client', 'overlay-exit'])):
            job = out / ('duchamp-' + name + '.plist')
            content = {'Label': label, 'ProgramArguments': arguments, 'RunAtLoad': True, 'KeepAlive': False,
                       'LimitLoadToSessionType': 'System', 'UserName': 'root', 'GroupName': 'wheel',
                       'StandardOutPath': '/dev/console', 'StandardErrorPath': '/dev/console'}
            if name in ('compositor', 'compositor-normal'):
                content['MachServices'] = {'org.duchamp.qemu.compositor': True}
            job.write_bytes(plistlib.dumps(content))
            installs.append(('/sbin/' + job.name, job))
    if args.gui_binary:
        installs += [(path, args.gui_binary.resolve()) for path in
                     ('/sbin/duchamp-gui-compositor', '/sbin/duchamp-window-manager',
                      '/sbin/duchamp-gui-shell', '/sbin/duchamp-gui-app')]
        if args.touch_input:
            installs += [(path, args.gui_binary.resolve()) for path in
                         ('/sbin/duchamp-app-manager', '/sbin/duchamp-app-observer', '/sbin/duchamp-app-red', '/sbin/duchamp-app-blue')]
        for name, program, argv, service in (
                ('gui-compositor', '/sbin/duchamp-gui-compositor', ['compositor'], 'org.duchamp.qemu.gui-compositor'),
                ('gui-wm', '/sbin/duchamp-window-manager', ['manager', *(['--apps'] if args.touch_input else [])], 'org.duchamp.qemu.window-manager'),
                ('gui-red', '/sbin/duchamp-app-red' if args.touch_input else '/sbin/duchamp-gui-app', ['red', *(['--apps'] if args.touch_input else [])], None),
                ('gui-blue', '/sbin/duchamp-app-blue' if args.touch_input else '/sbin/duchamp-gui-app', ['blue', *(['--apps'] if args.touch_input else [])], None),
                ('gui-shell', '/sbin/duchamp-gui-shell', ['shell', '--apps' if args.touch_input else '--live' if args.live_input else '--selftest'],
                 'org.duchamp.qemu.gui-shell.input' if args.live_input else None),
                *([('gui-input', '/sbin/duchamp-pointer-input', [], None)] if args.live_input else []),
                *([('gui-apps', '/sbin/duchamp-app-manager', ['applications'], 'org.duchamp.qemu.applications'),
                   ('gui-touch', '/sbin/duchamp-touch-input', [], None)] if args.touch_input else []),
                *([('app-observer', '/sbin/duchamp-app-observer', ['app-observer'], None)]
                  if args.touch_input and not args.interactive_input else []),
                *([('gui-live-observer', '/sbin/duchamp-gui-shell', ['live-observer'], None)]
                  if args.live_input and not args.touch_input and not args.interactive_input else [])):
            job = out / ('duchamp-' + name + '.plist')
            content = {'Label': 'org.duchamp.qemu.' + name, 'ProgramArguments': [program, *argv],
                       'RunAtLoad': name not in ('gui-red', 'gui-blue'), 'KeepAlive': name == 'gui-wm',
                       'UserName': 'root', 'GroupName': 'wheel', 'ProcessType': 'Standard',
                       'StandardOutPath': '/dev/console', 'StandardErrorPath': '/dev/console'}
            if service:
                content['MachServices'] = {service: True}
            job.write_bytes(plistlib.dumps(content))
            installs.append(('/sbin/' + job.name, job))
        if args.live_input:
            installs.append(('/sbin/duchamp-pointer-input', args.live_input.resolve()))
        if args.touch_input:
            installs.append(('/sbin/duchamp-touch-input', args.touch_input.resolve()))
    with tempfile.TemporaryDirectory(prefix='duchamp-var-') as scratch:
        for path, file in installs:
            run(hfs, root, 'add', file, path)
            run(hfs, root, 'chmod', '755', path)
            roundtrip = Path(scratch) / file.name
            run(hfs, root, 'extract', path, roundtrip)
            layout.check(roundtrip.read_bytes() == file.read_bytes(), f'failed root readback {path}')
            manifest['files'][path] = layout.digest(roundtrip.read_bytes())
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')

    package = out / 'package'
    missing = ('--missing-device',) if args.case == 'missing-md1' else ()
    diagnostic = ('--diagnostic-hid',) if args.graphics_probe else ()
    run(*PYTHON, 'tools/qemu_ramroot_var.py', kernel, adt, root, var, package, *missing, *diagnostic)
    report = json.loads((package / 'layout.json').read_text())
    payload = out / 'payload.bin'
    shutil.copyfile(package / 'payload.bin', payload)
    repacked = layout.build(kernel, adt, root, var, bool(missing), bool(args.graphics_probe))
    if args.live_input:
        import qemu_pointer_profile
        payload.write_bytes(qemu_pointer_profile.enable(payload.read_bytes(), bool(args.graphics_probe)))
        repacked = qemu_pointer_profile.enable(repacked, bool(args.graphics_probe))
    if args.touch_input:
        import qemu_touch_profile
        payload.write_bytes(qemu_touch_profile.enable(payload.read_bytes(), bool(args.graphics_probe)))
        repacked = qemu_touch_profile.enable(repacked, bool(args.graphics_probe))
    layout.check(repacked == payload.read_bytes(), 'payload repack changed')
    del repacked
    # The opt-in pointer adds ADT metadata after the ordinary package was
    # validated. Report the image actually passed to QEMU, retaining the base
    # package digest separately rather than mislabelling it as the run image.
    if args.live_input:
        report['base_payload_sha256'] = report['payload_sha256']
        actual = payload.read_bytes()
        offset, size = struct.unpack_from('<QQ', actual, 0x20)
        report.update(payload_sha256=layout.digest(actual), payload_bytes=len(actual),
                      adt_sha256=layout.digest(actual[offset:offset + size]),
                      virtual_pointer_profile=True)
        if args.touch_input:
            report['virtual_multitouch_profile'] = True
    seeds = {p: layout.digest(p.read_bytes()) for p in (root, var)}
    layout.check({key: report['layout'][key]['sha256'] for key in ('root', 'var')} ==
                 {p.stem: digest for p, digest in seeds.items()}, 'payload seed digest mismatch')
    report.update(case=args.case, inputs={str(path): sha for path, sha in before.items()},
                  payload_repack_identical=True, graphics_diagnostic=bool(args.graphics_probe))
    if args.prepare_only:
        report.update(inputs_unchanged=all(layout.digest(path.read_bytes()) == sha
                                           for path, sha in before.items()), guest_booted=False)
        (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        return 0 if report['inputs_unchanged'] else 1
    result_dir = out / 'run'
    positive = args.case == 'success'
    # Keep frequent TCG/QMP writes off the Windows shared filesystem.
    with tempfile.TemporaryDirectory(prefix='duchamp-var-guest-') as scratch:
        native = Path(scratch) / 'run'
        try:
            run(*PYTHON, 'tools/qemu-sweet.py', payload, native, '--kernel', kernel,
                '--framebuffer', 'duchamp', '--secs', '360' if positive else '180',
                '--snapshot-interval', '1' if args.gui_binary else '5', '--save-ramdisk',
                *(['--save-var-ramdisk'] if positive else []),
                *(['--fail-on-panic'] if not missing else []),
                '--stop-on-text', FAILURES['missing-md1'],
                '--stop-on-text', 'VAR PREFLIGHT FAIL',
                '--stop-on-text', 'SWEET launchd bootstrap: TEST FAILED',
                '--stop-on-text', 'SWEET launchctl: heartbeat=2 ',
                *(['--diagnostic-hid', '--frame-witness', args.frame_witness.resolve()] if args.graphics_probe else []),
                *(['--frame-sequence', args.frame_sequence.resolve()] if args.frame_sequence else []),
                *(['--virtio-pointer', '--live-runtime', args.live_runtime.resolve()] if args.live_input else []),
                *(['--virtio-multitouch'] if args.touch_input else []),
                *(['--stop-on-text', 'SWEET ipc gui-shell: FAIL', '--stop-on-text', 'SWEET ipc gui-wm: FAIL',
                   '--stop-on-text', 'SWEET ipc gui-compositor: FAIL', '--stop-on-text', 'SWEET ipc gui-red: FAIL',
                   '--stop-on-text', 'SWEET ipc gui-blue: FAIL'] if args.gui_binary else []),
                *(['--stop-on-text', 'SWEET ipc compositor: FAIL', '--stop-on-text', 'SWEET ipc comp-red: FAIL',
                   '--stop-on-text', 'SWEET ipc comp-overlay: FAIL'] if args.compositor_binary else []),
                '--stop-on-text', 'Library not loaded:', '--stop-on-text', 'Symbol not found:')
        finally:
            if native.is_dir():
                shutil.copytree(native, result_dir)
    result = json.loads((result_dir / 'result.json').read_text())
    frames = sorted((result_dir / 'frames').glob('*.txt'))
    console = '\n'.join(p.read_text() for p in [*frames, result_dir / 'fb.txt', result_dir / 'serial.txt']
                        if p.is_file())
    checks = {
        'root_dump_identical': layout.digest((result_dir / 'ramdisk-final.hfs').read_bytes()) == seeds[root],
        'root_and_var_seeds_unchanged': all(layout.digest(p.read_bytes()) == sha for p, sha in seeds.items()),
        'original_inputs_unchanged': all(layout.digest(p.read_bytes()) == sha for p, sha in before.items()),
    }
    if not missing:
        checks['devfs_console_ready'] = 'DEVFS CONSOLE READY' in console
    if positive:
        var_final = result_dir / 'var-final.hfs'
        witness = out / 'witness.txt'
        run(hfs, var_final, 'extract', '/tmp/duchamp-var-witness', witness)
        service_report = out / 'service-verification.json'
        run(*PYTHON, 'tools/verify-sweet-syslogd.py', out, '--hfsplus', hfs, '--notifyd',
            *(['--graphics'] if args.graphics_probe else []),
            *(['--compositor'] if args.compositor_binary else []),
            *(['--gui'] if args.gui_binary else []),
            *(['--live-input'] if args.live_input else []),
            *(['--app-touch'] if args.touch_input else []),
            '--var-image', var_final, '--report', service_report)
        service = json.loads(service_report.read_text())
        witness_lines = [line.split('=', 1) for line in witness.read_text().splitlines()]
        evidence = dict(witness_lines)
        layout.check(len(witness_lines) == len(evidence) == 7, 'ambiguous preflight witness')
        checks.update({
            'devfs_console_ready': evidence.get('console') == '/dev/console',
            'md1_registered_and_mounted': evidence.get('source') == '/dev/md1',
            'root_write_rejected': evidence.get('root_errno') == '30',
            'raw_root_write_open_rejected': evidence.get('raw_root_errno') in ('13', '30'),
            'enospc_and_recovery': evidence.get('capacity_errno') == '28'
                                  and 0 < int(evidence.get('filled_bytes', '0')) < var_bytes,
            'writable_var_and_alias': evidence.get('alias') == '/private/var',
            'original_launchd_pid1': service['original_file_checks']['/sbin/launchd']
                                     and service['checks']['four_distinct_processes'],
            'services_pass_all_74': service['passed'] and len(service['checks']) == 74,
        })
        report['preflight_witness'] = evidence
        report['var_final_sha256'] = layout.digest(var_final.read_bytes())
    else:
        checks.update({
            'expected_failure': FAILURES[args.case] in console,
            'launchd_not_execed': 'SWEET launchd bootstrap: PID 1 exec original /sbin/launchd' not in console,
        })
    report.update(passed=all(checks.values()), guest_booted=True, checks=checks,
                  elapsed_host_seconds=result['elapsed_host_seconds'], result=result['status'])
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
