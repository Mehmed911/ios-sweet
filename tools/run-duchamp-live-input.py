#!/usr/bin/env python3
"""Run the tested normal Darwin GUI with a local browser mouse viewer.

No phone transport. Uses copied RAM images; CTRL+C stops only this QEMU.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from duchamp_live_input import Viewer
from duchamp_source_kernel import select


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--kernel-manifest', type=Path, required=True)
    ap.add_argument('--artifacts', type=Path, required=True, help='accepted live-test directory with gui/input/graphics binaries')
    ap.add_argument('--mkfs', type=Path, required=True)
    ap.add_argument('--seconds', type=int, default=3600)
    ap.add_argument('--applications', action='store_true', help='managed apps with the second VirtIO multitouch device')
    a = ap.parse_args()
    out = a.output.resolve()
    out.mkdir()
    artifacts = a.artifacts.resolve()
    receipt = json.loads(a.kernel_manifest.read_text())
    kernel = Path(receipt['kernel'])
    select(kernel, a.kernel_manifest)
    repo = Path(__file__).resolve().parents[1]
    runtime = repo / 'research/dyld-runtime-20F66/runtime-root'
    commands = []

    def run(argv):
        argv = list(map(str, argv))
        log = out / ('command-%03d.log' % len(commands))
        with log.open('wb') as f:
            r = subprocess.run(argv, stdout=f, stderr=subprocess.STDOUT, timeout=180)
        commands.append(dict(argv=argv, exit_code=r.returncode, log=str(log), sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if r.returncode:
            raise RuntimeError(log.read_text(errors='replace'))

    run(['clang', '-target', 'arm64-apple-ios16.5', '-mcpu=generic', '-march=armv8-a', '-O1', '-Wall', '-Wextra', '-Werror',
         '-fno-builtin', '-fno-stack-protector', '-DSWEET_SYSLOGD_TEST=1', '-DSWEET_NOTIFYD_TEST=1',
         '-DDUCHAMP_DARWIN_GRAPHICS_TEST=1', '-DDUCHAMP_GUI_TEST=1', '-DDUCHAMP_LIVE_INPUT_TEST=1',
         *(['-DDUCHAMP_APP_TOUCH_TEST=1'] if a.applications else []),
         '-DDUCHAMP_GUI_INTERACTIVE=1', '-c', 'tools/sweet-launchctl-control.c', '-o', out / 'controller.o'])
    run(['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5', '-adhoc_codesign',
         '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'), '-lSystem.B', '-e', '_main', '-o', out / 'controller', out / 'controller.o'])
    runtime_file = out / 'live-runtime.json'
    run([sys.executable, '-B', 'tools/test-duchamp-readonly-var.py', out / 'guest', '--kernel', kernel,
         '--mkfs', a.mkfs.resolve(), '--var-mib', '4', '--graphics-probe', artifacts / 'graphics-signed',
         '--graphics-controller', out / 'controller', '--frame-witness', artifacts / 'graphics-frame.json',
         '--gui-binary', artifacts / 'gui', '--frame-sequence', artifacts / ('app-touch-frame-sequence.json' if a.applications else 'live-frame-sequence.json'),
         '--live-input', artifacts / 'gui-input', '--live-runtime', runtime_file,
         *(['--touch-input', artifacts / 'gui-touch'] if a.applications else []),
         '--interactive-input', '--prepare-only'])
    viewer = None
    with tempfile.TemporaryDirectory(prefix='duchamp-interactive-') as scratch:
        qemu_out = Path(scratch) / 'run'
        argv = [sys.executable, '-B', 'tools/qemu-sweet.py', out / 'guest/payload.bin', qemu_out, '--kernel', kernel,
                '--framebuffer', 'duchamp', '--secs', str(a.seconds), '--snapshot-interval', '5', '--save-ramdisk',
                '--save-var-ramdisk', '--diagnostic-hid', '--virtio-pointer', '--live-runtime', runtime_file,
                *(['--virtio-multitouch'] if a.applications else []),
                '--fail-on-panic', '--stop-on-text', 'SWEET ipc gui-shell: FAIL']
        log = out / 'qemu.log'
        with log.open('wb') as stream:
            p = subprocess.Popen(list(map(str, argv)), stdout=stream, stderr=subprocess.STDOUT)
            try:
                for _ in range(600):
                    if runtime_file.exists():
                        r = json.loads(runtime_file.read_text())
                        if Path(r['memory']).exists() and Path(r['memory']).stat().st_size == r['ram_bytes']:
                            if a.applications:
                                from duchamp_touch_input import TouchViewer
                                viewer = TouchViewer(r, out / 'viewer')
                            else:
                                viewer = Viewer(r, out / 'viewer')
                            print(viewer.url, flush=True)
                            break
                    if p.poll() is not None:
                        raise RuntimeError('QEMU failed before live viewer was ready')
                    time.sleep(.1)
                else:
                    raise TimeoutError('live RAM unavailable')
                p.wait()
            except KeyboardInterrupt:
                p.send_signal(2)
                p.wait(timeout=15)
            finally:
                if viewer:
                    viewer.close()
                if p.poll() is None:
                    p.send_signal(2)
                    try:
                        p.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait()
                import shutil
                if qemu_out.is_dir():
                    shutil.copytree(qemu_out, out / 'run')
        commands.append(dict(argv=list(map(str, argv)), exit_code=p.returncode, log=str(log)))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    return 0 if p.returncode in (0, 130) else p.returncode


if __name__ == '__main__':
    raise SystemExit(main())
