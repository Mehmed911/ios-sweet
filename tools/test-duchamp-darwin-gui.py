#!/usr/bin/env python3
"""Build native Mach-O GUI services; test only QEMU copies of HFS+ fixtures."""
import argparse
import hashlib
import json
import plistlib
from pathlib import Path
import re
import subprocess
import sys
import qemu_ramroot_var as layout
import duchamp_gui_expectations as oracle
import duchamp_source_kernel


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--kernel', type=Path, required=True)
    ap.add_argument('--mkfs', type=Path, required=True)
    ap.add_argument('--verify-only', action='store_true', help='inspect a completed saved guest without rebuilding or booting')
    ap.add_argument('--kernel-manifest', type=Path, help='explicit receipt for a new fully source-linked kernel')
    ap.add_argument('--live-input', action='store_true', help='run the real VirtIO-MMIO device input suite')
    ap.add_argument('--app-touch', action='store_true', help='managed applications and real VirtIO multitouch; implies live input')
    ap.add_argument('--browser-pause', action='store_true', help='briefly expose the real mouse viewer before automated device tests')
    a = ap.parse_args()
    if a.app_touch:
        a.live_input = True
    out = a.output.resolve()
    if not a.verify_only:
        out.mkdir()
    elif not (out / 'guest/run/var-final.hfs').is_file():
        ap.error('no completed saved guest')
    kernel = a.kernel.resolve()
    layout.require_source_kernel(kernel)
    try:
        expected_kernel = duchamp_source_kernel.select(kernel, a.kernel_manifest)
    except ValueError as e:
        ap.error(str(e))
    runtime = layout.REPO / 'research/dyld-runtime-20F66/runtime-root'
    hfs = layout.REPO / 'research/libdmg-hfsplus-build/hfsplus'
    commands = json.loads((out / 'commands.json').read_text()) if a.verify_only else []

    def run(argv, timeout=60):
        argv = list(map(str, argv))
        if a.verify_only and argv[0] != str(hfs):
            return
        log = out / f'command-{len(commands):03}.log'
        with log.open('wb') as f:
            r = subprocess.run(argv, cwd=layout.REPO, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        commands.append(dict(argv=argv, exit_code=r.returncode, log=str(log), sha256=sha(log)))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if r.returncode:
            print(log.read_text(errors='replace'))
            raise RuntimeError(str(log))

    flags = ['-DDC_CANVAS_W=160', '-DDC_CANVAS_H=96']
    run(['clang', '-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
         '-Wall', '-Wextra', '-Werror', *flags, 'tools/duchamp-compositor-core.c',
         'tools/duchamp-window-core.c', 'tools/test-duchamp-window-core.c', '-o', out / 'native'])
    run([out / 'native'])
    if a.live_input:
        run(['clang', '-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
             '-Wall', '-Wextra', '-Werror', 'tools/test-duchamp-virtio-pointer.c', '-o', out / 'input-native'])
        run([out / 'input-native'])
    if a.app_touch:
        run(['clang', '-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-Wall', '-Wextra', '-Werror',
             *flags, 'tools/duchamp-compositor-core.c', 'tools/duchamp-window-core.c', 'tools/test-duchamp-app-touch-core.c', '-o', out / 'app-native'])
        run([out / 'app-native'])
        run(['clang', '-g', '-O1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-Wall', '-Wextra', '-Werror',
             'tools/test-duchamp-virtio-touch.c', '-o', out / 'touch-native'])
        run([out / 'touch-native'])
    compile_flags = ['clang', '-target', 'arm64-apple-ios16.5', '-mcpu=generic', '-march=armv8-a',
                     '-O1', '-Wall', '-Wextra', '-Werror', '-fno-builtin', '-fno-stack-protector']

    def link(dest, objects):
        run(['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5',
             '-adhoc_codesign', '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'),
             '-lSystem.B', '-e', '_main', '-o', out / dest, *objects])

    objs = []
    for name in ('duchamp-compositor-core', 'duchamp-window-core', 'duchamp-darwin-gui'):
        obj = out / (name + '.o')
        run([*compile_flags, *flags, '-c', 'tools/' + name + '.c', '-o', obj])
        objs.append(obj)
    link('gui', objs)
    run([*compile_flags, '-c', 'tools/duchamp-darwin-graphics.c', '-o', out / 'graphics.o'])
    link('graphics', [out / 'graphics.o'])
    run([*compile_flags, '-DSWEET_SYSLOGD_TEST=1', '-DSWEET_NOTIFYD_TEST=1',
         '-DDUCHAMP_DARWIN_GRAPHICS_TEST=1', '-DDUCHAMP_GUI_TEST=1',
         *(['-DDUCHAMP_LIVE_INPUT_TEST=1'] if a.live_input else []),
         *(['-DDUCHAMP_APP_TOUCH_TEST=1'] if a.app_touch else []),
         '-c', 'tools/sweet-launchctl-control.c', '-o', out / 'controller.o'])
    link('controller', [out / 'controller.o'])
    if a.live_input:
        run([*compile_flags, *flags, '-c', 'tools/duchamp-darwin-pointer.c', '-o', out / 'input.o'])
        link('gui-input', [out / 'input.o'])
    if a.app_touch:
        run([*compile_flags, *flags, '-c', 'tools/duchamp-darwin-touch.c', '-o', out / 'touch.o'])
        link('gui-touch', [out / 'touch.o'])
    signer = layout.REPO / 'research/host-ipsw-3.1.739/ipsw'
    if sha(signer) != '7f22f07821cd964c0333172ef9bac734b53df5035a5e7c8ce9ec1580891f6d4c':
        raise RuntimeError('signer changed')
    ent = out / 'hid.plist'
    ent.write_bytes(plistlib.dumps({'com.apple.hid.system.user-access-service': True}))
    run([signer, 'macho', 'sign', '--id', 'org.duchamp.qemu.graphics', '--ad-hoc', '--ent', ent,
         '--output', out / 'graphics-signed', out / 'graphics'])
    for f in ('gui', 'graphics-signed', 'controller'):
        run([signer, 'macho', 'info', out / f])
    if a.app_touch:
        import duchamp_app_touch_oracle as live_oracle
        sequence = live_oracle.write(out)
    elif a.live_input:
        import duchamp_live_input_oracle as live_oracle
        sequence = live_oracle.write(out)
    else:
        sequence = oracle.write(out)
    pixels = b''.join((0xff000000 | (x * 4 << 16) | (y * 8 << 8) | ((x * 13 + y * 7) & 255)).to_bytes(4, 'little')
                      for y in range(32) for x in range(64))
    spec = out / 'graphics-frame.json'
    spec.write_text(json.dumps(dict(x=160, y=1600, width=64, height=32, sha256=hashlib.sha256(pixels).hexdigest())) + '\n')
    guest = out / 'guest'
    guest_command = [sys.executable, '-B', 'tools/test-duchamp-readonly-var.py', guest, '--kernel', kernel,
         '--mkfs', a.mkfs.resolve(), '--var-mib', '4', '--graphics-probe', out / 'graphics-signed',
         '--graphics-controller', out / 'controller', '--frame-witness', spec,
         '--gui-binary', out / 'gui', '--frame-sequence', sequence]
    if a.live_input and not a.verify_only:
        from concurrent.futures import ThreadPoolExecutor
        from duchamp_live_input_test import drive
        if a.app_touch:
            from duchamp_app_touch_test import drive
        runtime = out / 'live-runtime.json'
        guest_command += ['--live-input', out / 'gui-input', '--live-runtime', runtime]
        if a.app_touch:
            guest_command += ['--touch-input', out / 'gui-touch']
        with ThreadPoolExecutor(max_workers=1) as pool:
            import threading
            stop=threading.Event()
            driver = pool.submit(drive, runtime, out / 'host-input', *([stop] if a.app_touch else [a.browser_pause]))
            try:
                run(guest_command, timeout=580)
            except BaseException:
                stop.set()
                raise
            host_result = driver.result()
    else:
        run(guest_command, timeout=580)
    for role in ('gui-shell', 'gui-wm', 'gui-red', 'gui-blue', 'gui-compositor'):
        if a.app_touch and role in ('gui-red', 'gui-blue'):
            continue
        run([hfs, guest / 'run/var-final.hfs', 'extract', '/tmp/ipc-' + role + '.log', out / (role + '.log')])
    if a.app_touch:
        for role in ('applications', 'app-observer'):
            run([hfs, guest / 'run/var-final.hfs', 'extract', '/tmp/ipc-' + role + '.log', out / (role + '.log')])
        for id, color in [(2, 'red'), (3, 'blue')]:
            pieces=[]
            for pid in sorted(set(re.findall(r'app=%d status=0 pid=([1-9]\d*)' % id,(out/'applications.log').read_text())),key=int):
                path=out/('app-'+color+'-'+pid+'.log')
                run([hfs,guest/'run/var-final.hfs','extract','/tmp/ipc-app-'+color+'-'+pid+'.log',path])
                pieces.append(path.read_text())
            (out/('gui-'+color+'.log')).write_text('\n'.join(pieces))
            run([hfs,guest/'run/var-final.hfs','extract','/tmp/app-exit-'+color+'.log',out/('exit-'+color+'.log')])
    traces = {role: (out / (role + '.log')).read_text() for role in
              ('gui-shell', 'gui-wm', 'gui-red', 'gui-blue', 'gui-compositor')}
    shell, comp = traces['gui-shell'], traces['gui-compositor']
    manifest = json.loads((guest / 'run/frame-sequence.json').read_text())
    baseline = json.loads((guest / 'verification.json').read_text())
    checks = dict(source_kernel_unchanged=sha(kernel) == expected_kernel,
                  baseline_filesystems_and_74_services=baseline['passed'],
                  no_gui_failures=all('FAIL' not in t for t in traces.values()),
                  all_processes_under_launchd=all('ppid=1 uid=0 parent=/sbin/launchd' in t for t in traces.values()),
                  desktop_and_launcher='FRAME phase=1' in shell and 'LAUNCH kickstart gui-red status=0' in shell and 'LAUNCH kickstart gui-blue status=0' in shell,
                  focus_and_press_release='PASS focus_and_release id=2 events=2' in shell,
                  move='PASS move rect=26,22,70,44' in shell,
                  resize='PASS resize rect=26,22,80,50' in shell,
                  permission_replay_and_bounds='PASS ownership_replay_bounds' in shell,
                  dead_client_cleanup='PASS process_cleanup id=3' in shell,
                  actual_app_events=re.search(r'DELIVER id=2 seq=1 down=1.*DELIVER id=2 seq=2 down=0', traces['gui-red'], re.S) is not None,
                  wm_restart='PASS service_restart' in shell and 'RECONNECTED' in traces['gui-red'],
                  compositor_survives_restart=len(re.findall('CLEANUP surface=', comp)) >= 5,
                  gui_complete='PASS GUI_COMPLETE' in shell,
                  lifecycle='GUI LIFECYCLE PASS window_manager_runs=2 bootout=4' in
                       (guest / 'guest/launchctl-control.log').read_text())
    # Each saved observation must match the independently generated complete crop.
    if a.live_input:
        checks = dict(source_kernel_unchanged=sha(kernel) == expected_kernel,
                      baseline_filesystems_and_74_services=baseline['passed'],
                      all_processes_under_launchd=all('ppid=1 uid=0 parent=/sbin/launchd' in t for t in traces.values()),
                      no_gui_failures=all('FAIL' not in t for t in traces.values()),
                      live_input_from_driver='origin=virtio' in shell,
                      input_reconnected='generation=2' in shell,
                      forced_release='forced_release=1' in shell,
                      app_received_events='DELIVER id=2 seq=' in traces['gui-red'],
                      launcher='LIVE LAUNCH id=2' in shell and 'LIVE LAUNCH id=3' in shell,
                      lifecycle='GUI LIVE LIFECYCLE PASS input_runs=2 bootout=7' in (guest / 'guest/launchctl-control.log').read_text(),
                      host_device_test=json.loads((out / 'host-input/verification.json').read_text())['passed'])
    if a.app_touch:
        observer=(out/'app-observer.log').read_text()
        applications=(out/'applications.log').read_text()
        checks=dict(source_kernel_unchanged=sha(kernel)==expected_kernel,
                    baseline_filesystems_and_74_services=baseline['passed'],
                    all_processes_under_launchd=all('ppid=1 uid=0 parent=/sbin/launchd' in t for t in [*traces.values(),observer,applications]),
                    no_process_failures=all('FAIL' not in t for t in [*traces.values(),observer,applications]),
                    actual_app_processes='PASS PROCESS_IDENTITIES' in observer,
                    pid_version_binding='PASS PID_VERSION_BINDING' in observer,
                    actual_client_authority_denied=all('PASS APP_ISOLATION' in traces[n] for n in ('gui-red','gui-blue')),
                    foreground_background='PASS FOREGROUND_BACKGROUND' in observer,
                    two_simultaneous_contact_targets='PASS TWO_CONTACTS' in observer,
                    actual_touch_driver='TOUCH INPUT generation=1' in shell and 'origin=virtio' in shell,
                    driver_restart='TOUCH CONNECT' in shell and 'generation=2' in shell,
                    cancel_delivered='PASS CANCEL_DELIVERED' in observer and 'TOUCH CANCEL generation=1 count=2' in shell,
                    both_apps_receive_contacts=all('TOUCH DELIVER' in traces[n] for n in ('gui-red','gui-blue')),
                    graceful_termination='PASS GRACEFUL_EXIT' in observer,
                    process_restart_stale_handle='PASS RESTART' in observer,
                    actual_crash_cleanup='PASS CRASH_EXIT' in observer and 'CLIENT CLEANUP id=2' in traces['gui-wm'],
                    recorded_crash_signal='last terminating signal = Abort trap: 6' in (out/'exit-red.log').read_text(),
                    recorded_graceful_exit='last exit code = 0' in (out/'exit-blue.log').read_text(),
                    crash_restart_identity='PASS CRASH_RESTART' in observer,
                    old_capture_not_retargeted='PASS NEW_CONTACT_ONLY' in observer,
                    complete='PASS APPS_TOUCH_COMPLETE' in observer,
                    lifecycle='GUI APP TOUCH LIFECYCLE PASS touch_runs=2 bootout=9' in (guest/'guest/launchctl-control.log').read_text(),
                    host_device_test=json.loads((out/'host-input/verification.json').read_text())['passed'])
    for name, expected in (live_oracle.frames() if a.live_input else oracle.frames()).items():
        raw = guest / 'run' / ('sequence-' + name + '.raw')
        checks['pixels_' + name] = raw.is_file() and raw.read_bytes() == expected
    report = dict(passed=all(checks.values()), checks=checks, sequence=manifest,
                  kernel_sha256=sha(kernel), gui_sha256=sha(out / 'gui'), phone_operations=[],
                  physical_ufs_enabled=False, physical_status='BLOCKED_BY_MEMORY_EVIDENCE',
                  input_scope='actual VirtIO-MMIO device via QMP/browser -> XNU cdev -> input service -> shell -> WM' if a.live_input else 'QEMU-only audited Mach IPC virtual pointer; IOHID keyboard tested separately',
                  apple_private_graphics_compatibility=False)
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
