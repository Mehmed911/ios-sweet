#!/usr/bin/env python3
"""0BSD private 20F66 intact-cache/source-XNU RAM-only execution experiment.

The separate 3 GiB md0 is intentionally writable for runtime diagnostics.
The established read-only md0 + writable md1 profile is never changed.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from duchamp_source_kernel import select

REPO = Path(__file__).resolve().parents[1]


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--kernel-manifest', type=Path, required=True)
    ap.add_argument('--seconds', type=int, default=600)
    a = ap.parse_args()
    out = a.output.resolve(); out.mkdir()
    receipt = a.kernel_manifest.resolve()
    kernel = Path(json.loads(receipt.read_text())['kernel'])
    pin = select(kernel, receipt)
    native = Path(tempfile.mkdtemp(prefix='duchamp-ios20f66-', dir='/var/tmp'))
    (out/'native-directory.txt').write_text(str(native)+'\n')
    commands = []

    def run(argv, check=True):
        argv = list(map(str, argv)); log = out/('command-%03d.log'%len(commands))
        with log.open('wb') as f:
            r = subprocess.run(argv, cwd=REPO, stdout=f, stderr=subprocess.STDOUT, timeout=240)
        commands.append(dict(argv=argv, exit_code=r.returncode, log=str(log), sha256=sha(log)))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        if check and r.returncode:
            raise RuntimeError(log.read_text(errors='replace'))
        return r

    hfs = REPO/'research/libdmg-hfsplus-build/hfsplus'
    base = REPO/'work/launchctl-notifyd-v3/root.hfs'
    if sha(base) != '3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf':
        raise ValueError('diagnostic base changed')
    if sha(hfs) != 'be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b':
        raise ValueError('HFS tool changed')
    cache_dir = REPO/'work/20F66-cache-v4/apple-extracted/System/Library/Caches/com.apple.dyld'
    cache_receipt = REPO/'work/20F66-cache-v4/receipt.json'
    if sha(cache_receipt) != '30eb89efbe8fb1c63b6599a9ecffad13b6b956f644e9ef91cf351b61b97f1fab':
        raise ValueError('cache receipt changed')
    cache = {n:v for n,v in json.loads(cache_receipt.read_text())['files'].items() if not n.endswith('.symbols')}
    if len(cache) != 43:
        raise ValueError('incomplete runtime cache')
    for n,v in cache.items():
        if Path(n).name != n or sha(cache_dir/n) != v['sha256'] or (cache_dir/n).stat().st_size != v['bytes']:
            raise ValueError('cache bytes changed: '+n)
    if shutil.disk_usage(native).free < 25<<30:
        raise ValueError('insufficient native disk budget')
    root = native/'root.hfs'; shutil.copyfile(base, root)
    run([hfs,root,'grow',str(3<<30)])
    runtime = REPO/'research/dyld-runtime-20F66/runtime-root'
    run(['clang','-target','arm64-apple-ios16.5','-march=armv8-a','-O1','-Wall','-Wextra','-Werror',
         '-fno-builtin','-fno-stack-protector','-c','tools/duchamp-ios20f66-runtime.c','-o',out/'observer.o'])
    run(['ld64.lld','-arch','arm64','-platform_version','ios','16.5','16.5','-adhoc_codesign',
         '-syslibroot',runtime,'-L'+str(runtime/'usr/lib'),'-lSystem.B','-e','_main','-o',out/'observer',out/'observer.o'])
    run(['clang','-target','arm64-apple-ios16.5','-DDUCHAMP_USE_SHARED_CACHE=1',
         '-c','tools/sweet-launchd-bootstrap.S','-o',out/'bootstrap.o'])
    run([sys.executable,'tools/mkinit.py',out/'bootstrap.o',out/'launchd.sweet'])
    installs = {'/sbin/sweet-launchctl-control':out/'observer',
                '/usr/appleinternal/sbin/launchd.sweet':out/'launchd.sweet'}
    for n in cache:
        installs['/System/Library/Caches/com.apple.dyld/'+n] = cache_dir/n
    originals = {
        '/usr/libexec/backboardd':'work/ui-daemon-scan-v1/apple-extracted/usr/libexec/backboardd',
        '/System/Library/CoreServices/SpringBoard.app/SpringBoard':'work/springboard-bundle-v2/apple-extracted/System/Library/CoreServices/SpringBoard.app/SpringBoard',
        '/System/Library/CoreServices/SystemVersion.plist':'work/services-system-resources-v1/apple-extracted/System/Library/CoreServices/SystemVersion.plist',
        '/System/Library/BackBoard/EventProcessorConfiguration.plist':'work/services-backboard-resources-v1/apple-extracted/System/Library/BackBoard/EventProcessorConfiguration.plist',
        '/usr/share/icu/icudt70l.dat':'work/services-icu-resources-v1/apple-extracted/usr/share/icu/icudt70l.dat'}
    installs.update({g:REPO/s for g,s in originals.items()})
    known = set(); installed = {}
    for guest, source in installs.items():
        for directory in reversed(Path(guest).parents):
            if str(directory) in known:
                continue
            known.add(str(directory))
            r = subprocess.run(list(map(str,[hfs,root,'ls',directory])),capture_output=True,text=True)
            if 'No such file' in r.stdout+r.stderr:
                run([hfs,root,'mkdir',directory]);run([hfs,root,'chmod','755',directory])
        run([hfs,root,'add',source,guest]);run([hfs,root,'chmod','755' if guest.startswith(('/sbin/','/usr/libexec/','/usr/appleinternal/')) or guest.endswith('/SpringBoard') else '644',guest])
        run([hfs,root,'extract',guest,native/'roundtrip'])
        if sha(source) != sha(native/'roundtrip'):
            raise ValueError('guest roundtrip differs: '+guest)
        installed[guest] = dict(sha256=sha(source),bytes=source.stat().st_size)
        print('installed',guest,flush=True)
    for directory in ('/private/var/mobile','/private/var/mobile/Library','/private/var/mobile/Library/Preferences'):
        r = subprocess.run(list(map(str,[hfs,root,'ls',directory])),capture_output=True,text=True)
        if 'No such file' in r.stdout+r.stderr:
            run([hfs,root,'mkdir',directory])
        run([hfs,root,'chmod','755',directory]);run([hfs,root,'chown','501',directory]);run([hfs,root,'chgrp','501',directory])
    inputs = dict(kernel_sha256=pin,kernel_manifest=str(receipt),installed=installed,
        root_bytes=root.stat().st_size,root_sha256=sha(root),writable_test_root=True,
        preserved_small_dual_ramdisk=True,phone_operations=[],physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
    (out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    spec = importlib.util.spec_from_file_location('duchamp_large_ram',REPO/'tools/qemu-service-ram.py')
    vm = importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)
    print('booting exact source-linked kernel with intact 43-file cache',flush=True)
    started = time.monotonic()
    result = vm.run_vm(kernel,REPO/'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt',
        root,native/'run',a.seconds,['SWEET ipc ios20f66: COMPLETE','SWEET ipc ios20f66: FAIL','SWEET EARLY PANIC:',
        'SWEET launchd bootstrap: TEST FAILED'],kernel_manifest=receipt)
    (out/'qemu-result.json').write_text(json.dumps(result,indent=2)+'\n')
    for p in (native/'run').iterdir():
        if p.is_file() and p.stat().st_size < 50<<20:
            shutil.copyfile(p,out/p.name)
    final = native/'run/ramdisk-final.hfs'
    for guest,name in [('/private/var/tmp/ipc-ios20f66.log','observer.log'),
        ('/private/var/tmp/apple-backboardd-loader.log','backboardd-loader.log'),
        ('/private/var/tmp/apple-SpringBoard-loader.log','SpringBoard-loader.log')]:
        run([hfs,final,'extract',guest,out/name],check=False)
    (out/'elapsed.json').write_text(json.dumps(dict(seconds=time.monotonic()-started))+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
