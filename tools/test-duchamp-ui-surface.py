#!/usr/bin/env python3
"""Build and boot a CPU-only UI buffer probe in QEMU; export private evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import struct
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
ENTRIES = {
    '/System/Library/Frameworks/IOSurface.framework/IOSurface': '9e35ccdd66a72d02809741d476bb67eda4462a198c790267ae19b66fc8ecac53',
    '/System/Library/PrivateFrameworks/IOMobileFramebuffer.framework/IOMobileFramebuffer': 'c28d2dfa6117eaad413eb3d88c79ae183e234af4defe42d938783620103f62b6',
    '/System/Library/PrivateFrameworks/MiniDisplay.framework/MiniDisplay': 'ec987046344826d11e0b6a8380847c17e6be277622b6cc5fef6e341c6e4d7bd5',
}
RESULT = b'IOSurface CPU sharing PASS: 64x32 BGRA, 2048 pixels, exec child read+write, parent verified\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seconds', type=int, default=600)
    args = parser.parse_args()
    out = args.output.resolve()
    require(not out.exists(), 'preserve existing output')
    audit = json.loads(args.audit.read_text())
    files = {}
    for entry, pin in ENTRIES.items():
        result = audit['entries'][entry]
        require(result['complete'] and result['files'][entry]['sha256'] == pin, 'required UI closure/pin mismatch: ' + entry)
        for guest, item in result['files'].items():
            require(guest.startswith('/') and '..' not in guest.split('/'), 'unsafe guest path')
            require(sha(Path(item['source'])) == item['sha256'], 'changed source: ' + guest)
            if guest in files:
                require(files[guest]['sha256'] == item['sha256'], 'closure conflict')
            files[guest] = item
    kernel = REPO / 'work/ci-41543710742-kernel/artifact/kernel.development.sweet'
    adt = REPO / 'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt'
    base = REPO / 'work/launchd-final/root.hfs'
    hfs = REPO / 'research/libdmg-hfsplus-build/hfsplus'
    require(sha(kernel) == 'e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b', 'kernel mismatch')
    require(sha(adt) == 'a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8', 'QEMU ADT mismatch')
    require(sha(hfs) == 'be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b', 'HFS helper mismatch')
    out.mkdir(parents=True)
    # Allocation, execution and export share a single WSL process lifetime.
    native = Path(tempfile.mkdtemp(prefix='duchamp-ui-surface-'))
    try:
        logs = native / 'logs'
        logs.mkdir()

        def run(label, command, check=True):
            result = subprocess.run([str(arg) for arg in command], cwd=REPO, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            (logs / (label + '.log')).write_text(result.stdout)
            if check:
                require(result.returncode == 0, label + ' failed: ' + result.stdout[-4000:])
            return result

        for source, name in ((kernel, 'kernel'), (adt, 'qemu.adt'), (base, 'root.hfs'), (hfs, 'hfsplus')):
            shutil.copyfile(source, native / name)
        (native / 'hfsplus').chmod(0o755)
        shutil.copyfile(args.audit, native / 'dependency-audit.json')
        sources = native / 'test-sources'
        sources.mkdir()
        for name in ('sweet-ui-surface.m', 'sweet-foundation-api.h', 'sweet-ipc.h'):
            shutil.copyfile(REPO / 'tools' / name, sources / name)

        def volume(*command, check=True):
            return run('hfs-' + str(len(list(logs.iterdir()))), [native / 'hfsplus', native / 'root.hfs', *command], check)

        original = {}
        for guest, pin in {
            '/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
            '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f',
        }.items():
            volume('extract', guest, native / 'roundtrip')
            require(sha(native / 'roundtrip') == pin, 'base original executable mismatch')
            original[guest] = pin
        jobs = volume('ls', '/System/Library/LaunchDaemons').stdout
        require(re.findall(r'[^\s/]+\.plist', jobs) == ['org.sweet.qemu.c-service.plist'], 'unexpected base jobs')
        volume('grow', str(128 << 20))
        header = (native / 'root.hfs').read_bytes()[1024:1536]
        block, count = struct.unpack_from('>II', header, 40)
        require(header[:2] == b'H+' and block * count == (128 << 20), 'RAM root volume size mismatch')
        runtime = native / 'runtime'
        for guest, item in files.items():
            target = runtime / guest.lstrip('/')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item['source'], target)
        run('compile', ['clang', '-target', 'arm64-apple-ios16.5', '-Wall', '-Wextra', '-Werror', '-O1',
            '-fno-stack-protector', '-fno-builtin', '-fno-objc-arc', '-fobjc-exceptions',
            '-c', sources / 'sweet-ui-surface.m', '-o', native / 'probe.o'])
        run('link', ['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5',
            '-adhoc_codesign', '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'), '-lSystem.B', '-lobjc.A',
            '-F' + str(runtime / 'System/Library/Frameworks'), '-framework', 'Foundation',
            '-framework', 'CoreFoundation', '-framework', 'IOSurface', '-e', '_main',
            '-o', native / 'sweet-ui-surface', native / 'probe.o'])
        install = {guest: runtime / guest.lstrip('/') for guest in files}
        foundation = REPO / 'research/foundation-runtime-20F66-v2'
        resource_pins = json.loads((foundation / 'source.json').read_text())['resources']
        for guest, pin in resource_pins.items():
            source = foundation / 'runtime-root' / guest.lstrip('/')
            require(sha(source) == pin, 'resource pin mismatch')
            install[guest] = source
        job = native / 'ui-probe.plist'
        job.write_bytes(plistlib.dumps(dict(Label='org.sweet.qemu.ui-surface',
            ProgramArguments=['/sbin/sweet-ui-surface'], RunAtLoad=True, KeepAlive=False,
            UserName='root', GroupName='wheel', LimitLoadToSessionType='System',
            StandardOutPath='/dev/console', StandardErrorPath='/dev/console')))
        # Replace the existing job file in this copied image. The legacy HFS
        # helper's catalog deletion path rejects this grown-volume key.
        install['/System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist'] = job
        install['/sbin/sweet-ui-surface'] = native / 'sweet-ui-surface'
        known = set()
        installed = {}
        for guest, source in sorted(install.items()):
            for parent in reversed(Path(guest).parents):
                name = parent.as_posix()
                if name not in known:
                    listing = volume('ls', name, check=False).stdout
                    if 'No such file or directory' in listing:
                        volume('mkdir', name)
                        volume('chmod', '755', name)
                    known.add(name)
            volume('add', source, guest)
            volume('chmod', '755' if guest in files or guest == '/sbin/sweet-ui-surface' else '644', guest)
            volume('extract', guest, native / 'roundtrip')
            require((native / 'roundtrip').read_bytes() == source.read_bytes(), 'install byte mismatch: ' + guest)
            installed[guest] = sha(source)
        (native / 'inputs.json').write_text(json.dumps(dict(kernel=sha(kernel), adt=sha(adt), base=sha(base),
            initial_root=sha(native / 'root.hfs'), installed=installed, originals=original,
            sources={path.name: sha(path) for path in sources.iterdir()}), indent=2) + '\n')
        cmdline = 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 duchamp_timer_irq_ack=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
        run('payload', ['python3', REPO / 'tools/mkpayload.py', native / 'kernel', native / 'qemu.adt',
            native / 'payload.bin', '--ramdisk', native / 'root.hfs', '--cmdline', cmdline])
        print('UI probe: running QEMU with original IOSurface/Foundation and two independent processes', flush=True)
        runner = run('qemu', ['python3', REPO / 'tools/qemu-sweet.py', native / 'payload.bin', native / 'run',
            '--secs', str(args.seconds), '--framebuffer', 'duchamp', '--kernel', native / 'kernel',
            '--snapshot-interval', '5', '--save-ramdisk', '--fail-on-panic',
            '--stop-on-text', 'UI PROBE HEARTBEAT=2', '--stop-on-text', 'SWEET ipc ui-parent: FAIL',
            '--stop-on-text', 'SWEET ipc ui-child: FAIL', '--stop-on-text', 'Library not loaded:',
            '--stop-on-text', 'Symbol not found:', '--stop-on-text', 'SWEET EARLY PANIC:'], check=False)
        guest = native / 'guest'
        guest.mkdir()
        hashes_match = True
        for index, (path, pin) in enumerate({**original, **installed}.items()):
            target = guest / ('installed-' + str(index))
            result = run('guest-file-' + str(index), [native / 'hfsplus', native / 'run/ramdisk-final.hfs', 'extract', path, target], check=False)
            hashes_match &= result.returncode == 0 and target.is_file() and sha(target) == pin
        for name, path in [('parent.log', '/private/var/tmp/ipc-ui-parent.log'),
                           ('child.log', '/private/var/tmp/ipc-ui-child.log'), ('result.txt', '/private/var/tmp/ui-surface-result.txt')]:
            run('guest-' + name, [native / 'hfsplus', native / 'run/ramdisk-final.hfs', 'extract', path, guest / name], check=False)
        parent = (guest / 'parent.log').read_text() if (guest / 'parent.log').exists() else ''
        child = (guest / 'child.log').read_text() if (guest / 'child.log').exists() else ''
        frame = (native / 'run/fb.txt').read_text()
        p = re.search(r'IDENTITY pid=(\d+) ppid=1 uid=0 parent=/sbin/launchd', parent)
        c = re.search(r'UI CHILD EXEC pid=(\d+) ppid=(\d+) surface=(\d+)', child)
        created = re.search(r'UI SURFACE CREATED id=(\d+) width=64 height=32 row=(\d+) allocation=(\d+)', parent)
        marks = ['UI PROBE ENTERED', 'UI FRAMEWORKS LOADED', 'UI SURFACE CREATED', 'UI SAME PROCESS LOOKUP VERIFIED',
                 'UI CHILD SPAWNED', 'UI PARENT SHARED WRITEBACK VERIFIED', 'UI SURFACE CPU SHARING PASS', 'UI PROBE HEARTBEAT=1', 'UI PROBE HEARTBEAT=2']
        positions = [parent.find(mark) for mark in marks]
        checks = dict(required_closures_complete=True, critical_original_library_pins=True,
            installed_and_original_hashes_match=bool(hashes_match), qemu_runner_exit_zero=runner.returncode == 0,
            root_child_of_original_launchd=bool(p), independent_exec_child=bool(p and c and p[1] == c[2] and p[1] != c[1]),
            child_surface_id_matches=bool(c and created and c[3] == created[1]),
            child_verified_2048_pixels='UI CHILD SHARED PIXELS VERIFIED width=64 height=32 pixels=2048' in child,
            child_normal_exit='UI CHILD EXIT status=0' in child,
            parent_verified_child_writeback='UI PARENT SHARED WRITEBACK VERIFIED pixels=2048 child_status=0' in parent,
            all_parent_markers_in_order=all(pos >= 0 for pos in positions) and positions == sorted(positions),
            exact_saved_result=(guest / 'result.txt').is_file() and (guest / 'result.txt').read_bytes() == RESULT,
            two_heartbeats='UI PROBE HEARTBEAT=2' in parent,
            no_diagnostic_failure=not any(mark in parent + child + frame for mark in ('FAIL ', 'Library not loaded:', 'Symbol not found:', 'panic(cpu')))
        report = dict(passed=all(checks.values()), checks=checks, installed_count=len(installed),
            dependency_binary_count=len(files), elapsed_host_seconds=json.loads((native / 'run/result.json').read_text())['elapsed_host_seconds'],
            kernel_sha256=sha(kernel), payload_sha256=sha(native / 'payload.bin'),
            initial_root_sha256=sha(native / 'root.hfs'),
            scope=dict(phone_access=False, partition_write=False, display_swap=False, mali_acceleration=False,
                       physical_dma_or_cache_ownership=False, full_gui=False))
        (native / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)
        require(report['passed'], 'UI surface QEMU proof did not pass')
    finally:
        shutil.copytree(native, out / 'evidence')


if __name__ == '__main__':
    main()
