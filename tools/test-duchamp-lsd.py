#!/usr/bin/env python3
"""Boot unchanged mobile lsd and witness its process/ports in QEMU RAM only."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[1]
LSD = '/usr/libexec/lsd'
LSD_PIN = 'cb9a5082ac7448e1ff8ee30e45925909568f39e6f4dc30e0bbbdf4332c27d0e4'
JOB_PIN = '9728a545bd4cdde11d2f264ef547c5a15717964d8029b37fa71ffa23010b3a78'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--seconds', type=int, default=240)
    args = ap.parse_args()
    out = args.output.resolve()
    require(not out.exists(), 'preserve existing output')
    scan = REPO / 'work/ui-daemon-scan-v1'
    audit = json.loads((scan / 'audit.json').read_text())['entries'][LSD]
    require(audit['complete'] and audit['files'][LSD]['sha256'] == LSD_PIN, 'original lsd closure missing or changed')
    files = {guest: (Path(item['source']), item['sha256']) for guest, item in audit['files'].items()}
    prefs = REPO / 'research/cfprefs-runtime-20F66-v2'
    pref_audit = json.loads((prefs / 'runtime-audit.json').read_text())
    require(pref_audit['passed'], 'supporting runtime closure failed')
    for guest, item in pref_audit['files'].items():
        require(guest not in files or files[guest][1] == item['sha256'], 'closure conflict')
        files[guest] = (prefs / 'runtime-root' / guest.lstrip('/'), item['sha256'])
    require(files['/bin/launchctl'][1] == '11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d', 'CLI pin mismatch')
    for guest, (path, pin) in files.items():
        require(guest.startswith('/') and '..' not in guest.split('/') and sha(path) == pin, 'changed or unsafe dependency: ' + guest)
    original_job = scan / 'apple-extracted/System/Library/LaunchDaemons/com.apple.lsd.plist'
    require(sha(original_job) == JOB_PIN, 'original job mismatch')
    job = plistlib.loads(original_job.read_bytes())
    require(job['UserName'] == 'mobile' and len(job['MachServices']) == 13 and job['ProgramArguments'] == [LSD], 'job contract mismatch')
    kernel = REPO / 'work/ci-41543710742-kernel/artifact/kernel.development.sweet'
    adt = REPO / 'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt'
    hfs = REPO / 'research/libdmg-hfsplus-build/hfsplus'
    base = REPO / 'work/launchd-final/root.hfs'
    require(sha(kernel) == 'e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b', 'kernel pin mismatch')
    require(sha(adt) == 'a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8', 'QEMU ADT mismatch')
    require(sha(hfs) == 'be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b', 'HFS helper mismatch')
    out.mkdir(parents=True)
    native = Path(tempfile.mkdtemp(prefix='duchamp-lsd-'))
    try:
        logs = native / 'logs'
        logs.mkdir()
        def run(name, command, check=True):
            result = subprocess.run([str(arg) for arg in command], cwd=REPO, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (logs / (name + '.log')).write_text(result.stdout)
            if check:
                require(result.returncode == 0, name + ': ' + result.stdout[-4000:])
            return result
        for source, name in ((kernel, 'kernel'), (adt, 'qemu.adt'), (hfs, 'hfsplus'), (base, 'root.hfs')):
            shutil.copyfile(source, native / name)
        (native / 'hfsplus').chmod(0o755)
        def volume(*command, check=True):
            return run('hfs-' + str(len(list(logs.iterdir()))), [native / 'hfsplus', native / 'root.hfs', *command], check)
        originals = {'/sbin/launchd': '4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06',
                     '/usr/libexec/xpcproxy': '2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f'}
        for guest, pin in originals.items():
            volume('extract', guest, native / 'roundtrip')
            require(sha(native / 'roundtrip') == pin, 'base executable pin mismatch')
        require(re.findall(r'[^\s/]+\.plist', volume('ls', '/System/Library/LaunchDaemons').stdout)
                == ['org.sweet.qemu.c-service.plist'], 'unexpected base jobs')
        volume('grow', str(128 << 20))
        sources = native / 'test-sources'
        sources.mkdir()
        for name in ('sweet-lsd-probe.c', 'sweet-ipc.h'):
            shutil.copyfile(REPO / 'tools' / name, sources / name)
        run('compile', ['clang', '-target', 'arm64-apple-ios16.5', '-Wall', '-Wextra', '-Werror', '-O1',
            '-fno-stack-protector', '-fno-builtin', '-c', sources / 'sweet-lsd-probe.c', '-o', native / 'observer.o'])
        run('link', ['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5', '-adhoc_codesign',
            '-syslibroot', prefs / 'runtime-root', '-L' + str(prefs / 'runtime-root/usr/lib'), '-lSystem.B',
            '-e', '_main', '-o', native / 'sweet-lsd-probe', native / 'observer.o'])
        install = {guest: path for guest, (path, pin) in files.items()}
        info = json.loads((prefs / 'source.json').read_text())
        for guest, pin in info['resources'].items():
            path = prefs / 'runtime-root' / guest.lstrip('/')
            require(sha(path) == pin, 'resource changed')
            install[guest] = path
        job.update(StandardOutPath='/private/var/tmp/lsd-console.log', StandardErrorPath='/private/var/tmp/lsd-console.log')
        jobs = {'com.apple.lsd.plist': job,
            'org.sweet.qemu.c-service.plist': dict(Label='org.sweet.qemu.lsd-control',
                ProgramArguments=['/sbin/sweet-lsd-probe'], RunAtLoad=True, KeepAlive=False,
                UserName='root', GroupName='wheel', LimitLoadToSessionType='System',
                StandardOutPath='/dev/console', StandardErrorPath='/dev/console')}
        notify = dict(info['notifyd_source']['original_job'])
        notify.update(RunAtLoad=True, KeepAlive=False, UserName='root', GroupName='wheel',
            StandardOutPath='/private/var/tmp/notifyd-console.log', StandardErrorPath='/private/var/tmp/notifyd-console.log',
            ProgramArguments=['/usr/sbin/notifyd', '-d', '-log_file', '/private/var/tmp/notifyd-debug.log', '-shm_pages', '0'])
        jobs['com.apple.notifyd.plist'] = notify
        for name, meta in info['cfprefsd_source']['original_jobs'].items():
            entry = dict(meta['original_job'])
            entry.update(Disabled=False, RunAtLoad=False, KeepAlive=False, UserName='root', GroupName='wheel',
                LimitLoadToSessionType='System', StandardOutPath='/private/var/tmp/cfprefsd-console.log',
                StandardErrorPath='/private/var/tmp/cfprefsd-console.log')
            jobs[name] = entry
        for name, entry in jobs.items():
            path = native / name
            path.write_bytes(plistlib.dumps(entry))
            install['/System/Library/LaunchDaemons/' + name] = path
        install['/sbin/sweet-lsd-probe'] = native / 'sweet-lsd-probe'
        known, installed = set(), {}
        for guest, path in sorted(install.items()):
            for parent in reversed(Path(guest).parents):
                name = parent.as_posix()
                if name not in known:
                    if 'No such file or directory' in volume('ls', name, check=False).stdout:
                        volume('mkdir', name); volume('chmod', '755', name)
                    known.add(name)
            volume('add', path, guest)
            volume('chmod', '644' if guest.endswith('.plist') else '755', guest)
            volume('extract', guest, native / 'roundtrip')
            require((native / 'roundtrip').read_bytes() == path.read_bytes(), 'install mismatch: ' + guest)
            installed[guest] = sha(path)
        (native / 'inputs.json').write_text(json.dumps(dict(kernel=sha(kernel), adt=sha(adt), base=sha(base),
            initial_root=sha(native / 'root.hfs'), installed=installed, originals=originals, lsd_original_job=JOB_PIN,
            source_hashes={path.name: sha(path) for path in sources.iterdir()},
            note='Original lsd UserName/MachServices/arguments/on-demand policy preserved; only stdout/stderr redirected. notifyd/cfprefsd use explicit diagnostic job overrides.'), indent=2) + '\n')
        cmdline = 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 duchamp_timer_irq_ack=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
        run('payload', ['python3', REPO / 'tools/mkpayload.py', native / 'kernel', native / 'qemu.adt', native / 'payload.bin', '--ramdisk', native / 'root.hfs', '--cmdline', cmdline])
        print('lsd: QEMU starting, native mobile identity and 13 original endpoints', flush=True)
        runner = run('qemu', ['python3', REPO / 'tools/qemu-sweet.py', native / 'payload.bin', native / 'run',
            '--secs', str(args.seconds), '--framebuffer', 'duchamp', '--kernel', native / 'kernel',
            '--snapshot-interval', '5', '--save-ramdisk', '--fail-on-panic', '--stop-on-text', 'LSD PROBE DONE',
            '--stop-on-text', 'SWEET EARLY PANIC:', '--stop-on-text', 'Library not loaded:', '--stop-on-text', 'Symbol not found:'], check=False)
        guest = native / 'guest'
        guest.mkdir()
        for name, path in [('control.log', '/private/var/tmp/ipc-lsd-control.log'), ('lsd-console.log', '/private/var/tmp/lsd-console.log'),
                           ('start.txt', '/private/var/tmp/lsd-cli-start.txt')]:
            run('extract-' + name, [native / 'hfsplus', native / 'run/ramdisk-final.hfs', 'extract', path, guest / name], check=False)
        for number in range(20):
            run('startup-' + str(number), [native / 'hfsplus', native / 'run/ramdisk-final.hfs', 'extract',
                '/private/var/tmp/lsd-cli-startup-' + str(number) + '.txt', guest / ('startup-' + str(number) + '.txt')], check=False)
        matching = True
        for index, (path, pin) in enumerate({**originals, **installed}.items()):
            dest = guest / ('installed-' + str(index))
            result = run('guest-file-' + str(index), [native / 'hfsplus', native / 'run/ramdisk-final.hfs', 'extract', path, dest], check=False)
            matching &= result.returncode == 0 and dest.exists() and sha(dest) == pin
        text = (guest / 'control.log').read_text() if (guest / 'control.log').exists() else ''
        identities = re.findall(r'LSD NATIVE IDENTITY pid=(\d+) ppid=1 uid=501 gid=501 path=/usr/libexec/lsd', text)
        ports = re.findall(r'LSD ENDPOINT PUBLISHED name=(\S+) lookup=0', text)
        health = re.findall(r'LSD HEALTH check=(\d+) pid=(\d+) stable=1', text)
        checks = dict(strong_closure_complete=True, original_lsd_and_job_pins=True,
            all_installed_hashes_match=bool(matching), qemu_exit_zero=runner.returncode == 0,
            root_observer_child_of_launchd=bool(re.search(r'IDENTITY pid=\d+ ppid=1 uid=0 parent=/sbin/launchd', text)),
            native_mobile_lsd=bool(identities), all_13_native_names_published=set(ports) == set(job['MachServices']),
            three_stable_identity_checks=len(health) == 3 and [row[0] for row in health] == ['1', '2', '3'] and
                len({row[1] for row in health} | set(identities)) == 1,
            complete_saved_result='LSD PROBE DONE status=0' in text,
            no_diagnostic_failure='LSD PROBE FAIL' not in text)
        report = dict(passed=all(checks.values()), checks=checks, installed_count=len(installed),
            elapsed_host_seconds=json.loads((native / 'run/result.json').read_text())['elapsed_host_seconds'],
            kernel_sha256=sha(kernel), payload_sha256=sha(native / 'payload.bin'), root_sha256=sha(native / 'root.hfs'),
            scope=dict(phone_access=False, partition_write=False, native_application_request_proven=False,
                       mach_lookup_is_daemon_reply=False, full_gui=False, physical_ufs=False))
        (native / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)
        require(report['passed'], 'lsd startup/endpoint proof did not pass; retain diagnostics')
    finally:
        shutil.copytree(native, out / 'evidence')


if __name__ == '__main__':
    main()
