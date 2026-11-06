#!/usr/bin/env python3
"""Try the untouched 20F66 cache through a read-only QEMU UFS disk, not RAMDisk.

All outputs are private, new directories. A PASS needs the exact live cache
UUID, in-cache image headers, and original Objective-C class metadata.
This is not a launchd, daemon RPC, GUI, phone or physical UFS test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import traceback
import uuid
import qemu_ufs

REPO = Path(__file__).resolve().parents[1]
CACHE_UUID = 'E5420DB3-30D0-33AA-8B7E-05B5038BB46D'
RECEIPT_PIN = '30eb89efbe8fb1c63b6599a9ecffad13b6b956f644e9ef91cf351b61b97f1fab'
CACHE_GUEST = '/System/Library/Caches/com.apple.dyld/'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for data in iter(lambda: source.read(4 << 20), b''):
            digest.update(data)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--seconds', type=int, default=240)
    args = ap.parse_args()
    out = args.output.resolve()
    require(not out.exists(), 'preserve existing output')
    require(10 <= args.seconds <= 900, 'bounded QEMU duration required')
    cache_root = REPO / 'work/20F66-cache-v4'
    receipt_path = cache_root / 'receipt.json'
    require(sha(receipt_path) == RECEIPT_PIN, 'cache receipt changed')
    receipt = json.loads(receipt_path.read_text())
    cache = cache_root / 'apple-extracted' / CACHE_GUEST.lstrip('/')
    components = {name: item for name, item in receipt['files'].items() if not name.endswith('.symbols')}
    require(len(components) == 43, 'unexpected runtime component count')
    for name, item in components.items():
        require(re.fullmatch(r'dyld_shared_cache_arm64(?:\.\d\d(?:\.dyld(?:linkedit|data))?)?', name), 'unsafe cache component: ' + name)
        source = cache / name
        require(source.stat().st_size == item['bytes'] and sha(source) == item['sha256'], 'cache component changed: ' + name)
    with (cache / 'dyld_shared_cache_arm64').open('rb') as source:
        header = source.read(104)
    require(header[:7] == b'dyld_v1' and str(uuid.UUID(bytes=header[88:104])).upper() == CACHE_UUID, 'cache main identity differs')
    pinned = {
        'kernel': (REPO / 'work/ci-41543710742-kernel/artifact/kernel.development.sweet', 'e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b'),
        'base.adt': (REPO / 'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt', 'a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8'),
        'hfsplus': (REPO / 'research/libdmg-hfsplus-build/hfsplus', 'be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b'),
        'root.hfs': (REPO / 'work/launchd-final/root.hfs', '491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f'),
    }
    for path, pin in pinned.values():
        require(sha(path) == pin, 'input pin changed: ' + str(path))
    source_paths = [REPO / 'tools' / name for name in (
        'sweet-shared-cache-probe.c', 'duchamp-shared-cache-init.S', 'test-duchamp-shared-cache.py',
        'qemu_ufs.py', 'qemu-sweet.py', 'mkpayload.py', 'mkinit.py')]
    source_hashes = {p.name: sha(p) for p in source_paths}
    out.mkdir(parents=True)
    # /tmp is tmpfs on this machine. Keep the 3 GiB disk on the native disk
    # filesystem and stream every hash, avoiding duplicated whole-image reads.
    parent = Path.home() / '.cache/duchamp-qemu-tests'
    parent.mkdir(parents=True, exist_ok=True)
    native = Path(tempfile.mkdtemp(prefix='shared-cache-', dir=parent))
    report = dict(passed=False, native_directory=str(native), scope=dict(
        phone_access=False, partition_write=False, physical_ufs=False,
        original_launchd_tested=False, daemon_reply=False, full_gui=False))
    rc = 1
    try:
        logs = native / 'logs'; logs.mkdir()
        def run(label, command, check=True):
            result = subprocess.run([str(a) for a in command], cwd=REPO,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            (logs / (label + '.log')).write_text(result.stdout)
            if check:
                require(result.returncode == 0, label + ' failed: ' + result.stdout[-3000:])
            return result
        for name, (path, _) in pinned.items():
            shutil.copyfile(path, native / name)
        (native / 'hfsplus').chmod(0o755)
        (native / 'test-sources').mkdir()
        for path in source_paths:
            shutil.copyfile(path, native / 'test-sources' / path.name)
        def volume(*args, check=True):
            return run('hfs-' + str(len(list(logs.iterdir()))), [native / 'hfsplus', native / 'root.hfs', *args], check)
        volume('grow', str(3 << 30))
        with (native / 'root.hfs').open('rb') as source:
            source.seek(1024); hfs_header = source.read(512)
        block, count = struct.unpack_from('>II', hfs_header, 40)
        require(hfs_header[:2] == b'H+' and block * count == 3 << 30, 'HFS volume grow failed')
        if 'No such file or directory' in volume('ls', '/dev', check=False).stdout:
            volume('mkdir', '/dev')
        volume('chmod', '755', '/dev')
        require('No such file or directory' not in volume('ls', '/dev').stdout, 'missing devfs mountpoint')
        runtime = REPO / 'research/darwin-launchd-20F66/runtime-root'
        run('compile-probe', ['clang', '-target', 'arm64-apple-ios16.5', '-Wall', '-Wextra', '-Werror',
            '-O1', '-fno-stack-protector', '-fno-builtin', '-c', native / 'test-sources/sweet-shared-cache-probe.c', '-o', native / 'probe.o'])
        run('link-probe', ['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5',
            '-adhoc_codesign', '-syslibroot', runtime, '-L' + str(runtime / 'usr/lib'), '-lSystem.B',
            '-e', '_main', '-o', native / 'probe', native / 'probe.o'])
        run('compile-init', ['clang', '-target', 'arm64-apple-ios16.5', '-c',
            native / 'test-sources/duchamp-shared-cache-init.S', '-o', native / 'init.o'])
        run('link-init', ['python3', REPO / 'tools/mkinit.py', native / 'init.o', native / 'init'])
        install = {CACHE_GUEST + name: cache / name for name in components}
        install.update({'/sbin/launchd': native / 'init', '/sbin/sweet-shared-cache-probe': native / 'probe'})
        known = set(); installed = {}
        for index, (guest, path) in enumerate(sorted(install.items())):
            for directory in reversed(Path(guest).parents):
                name = directory.as_posix()
                if name not in known:
                    listing = volume('ls', name, check=False).stdout
                    if 'No such file or directory' in listing:
                        volume('mkdir', name); volume('chmod', '755', name)
                    known.add(name)
            volume('add', path, guest)
            volume('chmod', '755' if guest.startswith('/sbin/') else '644', guest)
            volume('extract', guest, native / 'roundtrip')
            pin = sha(path)
            if guest.startswith(CACHE_GUEST):
                require(pin == components[Path(guest).name]['sha256'], 'source cache changed during install')
            require(sha(native / 'roundtrip') == pin, 'HFS roundtrip mismatch: ' + guest)
            installed[guest] = pin
            print('shared-cache: installed %d/%d %s' % (index + 1, len(install), Path(guest).name), flush=True)
        volume('extract', '/usr/lib/dyld', native / 'original-dyld')
        require(sha(native / 'original-dyld') == sha(runtime / 'usr/lib/dyld'), 'original dyld changed')
        (native / 'qemu.adt').write_bytes(qemu_ufs.build_tree((native / 'base.adt').read_bytes()))
        root_pin = sha(native / 'root.hfs')
        inputs = dict(cache_receipt=RECEIPT_PIN, cache_uuid=CACHE_UUID,
            runtime_components=len(components), runtime_cache_bytes=sum(x['bytes'] for x in components.values()),
            symbols_omitted=True, installed=installed, source_hashes=source_hashes,
            input_pins={name: pin for name, (_, pin) in pinned.items()}, root_sha256=root_pin,
            dyld_sha256=sha(native / 'original-dyld'))
        (native / 'inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
        cmdline = ('debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress '
            'rd=qufs0 rootrw=0 sweet-qemu-ufs=1 sweet_console_fb=1 duchamp_timer_irq_ack=1 '
            'unentitled_ios_sim_launch=1')
        run('payload', ['python3', REPO / 'tools/mkpayload.py', native / 'kernel', native / 'qemu.adt',
            native / 'payload.bin', '--cmdline', cmdline])
        print('shared-cache: starting original dyld + untouched cache on read-only QEMU storage', flush=True)
        result = run('qemu', ['python3', REPO / 'tools/qemu-sweet.py', native / 'payload.bin', native / 'run',
            '--kernel', native / 'kernel', '--framebuffer', 'duchamp', '--ufs-image', native / 'root.hfs',
            '--secs', str(args.seconds), '--snapshot-interval', '4', '--fail-on-panic',
            '--stop-on-text', 'SWEET SHARED CACHE: PASS', '--stop-on-text', 'SWEET SHARED CACHE: FAIL',
            '--stop-on-text', 'SWEET SHARED CACHE: EXEC FAILED', '--stop-on-text', 'SWEET EARLY PANIC:',
            '--stop-on-text', 'SWEET SHARED CACHE: CHILD EXITED',
            '--stop-on-text', 'DEVFS MOUNT FAILED', '--stop-on-text', 'PID1 CONSOLE OPEN FAILED',
            '--stop-on-text', 'Library not loaded:', '--stop-on-text', 'Symbol not found:'], check=False)
        state = json.loads((native / 'run/result.json').read_text())
        texts = sorted((native / 'run/frames').glob('*.txt')) + [native / 'run/fb.txt', native / 'run/serial.txt']
        screen = '\n'.join(p.read_text(errors='replace') for p in texts if p.is_file())
        (native / 'observed.txt').write_text(screen)
        checks = {
            'qemu_exit_zero': result.returncode == 0,
            'static_pid1_fork_exec': 'SWEET SHARED CACHE: STATIC PID1 FORK EXEC' in screen,
            'dynamic_child_main': bool(re.search(r'DYNAMIC MAIN pid=([2-9]|[1-9][0-9]+) ppid=1\b', screen)),
            'exact_live_cache_uuid': 'UUID ' + CACHE_UUID.replace('-', '') in screen,
            'live_cache_range': bool(re.search(r'RANGE base=0x[1-9a-fA-F][0-9a-fA-F]* bytes=[1-9][0-9]*', screen)),
            'original_mcm_in_cache_and_objc': 'FRAMEWORK index=0 incache=1 class=MCMError' in screen,
            'original_cachedelete_in_cache_and_objc': 'FRAMEWORK index=1 incache=1 class=CDRecentInfo' in screen,
            'complete_pass_marker': 'SWEET SHARED CACHE: PASS step=uuid-range-frameworks-objc' in screen,
            'success_stop': state.get('stop_marker') == 'SWEET SHARED CACHE: PASS',
            'no_observed_failure': not any(marker in screen for marker in ('panic(cpu ', 'SWEET EARLY PANIC:',
                'SWEET SHARED CACHE: FAIL', 'EXEC FAILED', 'Library not loaded:', 'Symbol not found:',
                'DEVFS MOUNT FAILED', 'PID1 CONSOLE OPEN FAILED', 'SWEET SHARED CACHE: CHILD EXITED')),
            'readonly_disk_unchanged': sha(native / 'root.hfs') == root_pin,
            'base_unchanged': sha(pinned['root.hfs'][0]) == pinned['root.hfs'][1],
            'test_sources_unchanged': source_hashes == {p.name: sha(p) for p in source_paths},
        }
        report.update(passed=all(checks.values()), checks=checks, qemu_result=state,
            root_sha256=root_pin, kernel_sha256=sha(native / 'kernel'), payload_sha256=sha(native / 'payload.bin'),
            runtime_components=len(components), runtime_cache_bytes=inputs['runtime_cache_bytes'])
        rc = 0 if report['passed'] else 1
    except Exception:
        report['error'] = traceback.format_exc()
        print(report['error'], flush=True)
    finally:
        (native / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        shutil.copytree(native, out / 'evidence')
    print(json.dumps(report, indent=2), flush=True)
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
