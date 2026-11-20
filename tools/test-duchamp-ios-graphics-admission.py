#!/usr/bin/env python3
"""0BSD exact-XNU passive capabilities and bounded unmodified Apple exec trials."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import qemu_ramroot_var as layout
from duchamp_source_kernel import select

REPO=Path(__file__).resolve().parents[1]
APPLE={
 '/usr/libexec/backboardd':('work/ui-daemon-scan-v1/apple-extracted/usr/libexec/backboardd','686f26a6a7b749fd0ae30acca704022da8cb6f85b5c39a0e0e09e25ffd00d273'),
 '/System/Library/CoreServices/SpringBoard.app/SpringBoard':('work/springboard-bundle-v2/apple-extracted/System/Library/CoreServices/SpringBoard.app/SpringBoard','7926a1ba0b115cf45102b2c3d8e4eb7bc9c84bcf70b573d2a798690d9148059c')}


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def terminal_status(status):
    """Darwin wait.h terminal encoding; high exit bits are invalid on a signal."""
    if type(status) is not int or not 0<=status<=65535 or status&127==127:
        raise ValueError('not a terminal Darwin wait status')
    signal=status&127
    return dict(signal=signal,exit_status=None if signal else (status>>8)&255,
                core_dumped=bool(signal and status&128))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--kernel-manifest',type=Path,required=True)
    ap.add_argument('--mkfs',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve();out.mkdir()
    receipt=json.loads(a.kernel_manifest.read_text());kernel=Path(receipt['kernel']);pin=select(kernel,a.kernel_manifest)
    commands=[]

    def run(argv,timeout=180,check=True):
        argv=list(map(str,argv));log=out/('command-%03d.log'%len(commands))
        with log.open('wb') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,cwd=REPO,timeout=timeout)
        commands.append(dict(argv=argv,exit_code=r.returncode,log=str(log),sha256=sha(log)))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if check and r.returncode:raise RuntimeError(log.read_text(errors='replace'))
        return r

    run([sys.executable,'-B','tools/test-duchamp-macho-preflight.py'])
    run([sys.executable,'-B','tools/test-duchamp-readonly-var.py',out/'guest','--kernel',kernel,'--mkfs',a.mkfs.resolve(),'--var-mib','4','--prepare-only'])
    runtime=REPO/'research/dyld-runtime-20F66/runtime-root';hfs=REPO/'research/libdmg-hfsplus-build/hfsplus'
    run(['clang','-target','arm64-apple-ios16.5','-mcpu=generic','-march=armv8-a','-O1','-Wall','-Wextra','-Werror','-fno-builtin','-fno-stack-protector',
         '-c','tools/duchamp-ios-graphics-admission.c','-o',out/'admission.o'])
    run(['ld64.lld','-arch','arm64','-platform_version','ios','16.5','16.5','-adhoc_codesign','-syslibroot',runtime,'-L'+str(runtime/'usr/lib'),'-lSystem.B','-e','_main','-o',out/'admission',out/'admission.o'])
    root=out/'guest/root.hfs';var=out/'guest/var.hfs'
    installs={'/sbin/sweet-launchctl-control':out/'admission'}
    for guest,(source,digest) in APPLE.items():
        source=REPO/source
        if sha(source)!=digest:raise ValueError('original Apple file changed: '+str(source))
        installs[guest]=source
    known=set()
    for guest,source in installs.items():
        for directory in reversed(Path(guest).parents):
            if str(directory) in known:continue
            known.add(str(directory))
            # mkdir may report an existing directory; inspect the existing image first.
            r=subprocess.run(list(map(str,[hfs,root,'ls',directory])),capture_output=True,text=True)
            if 'No such file' in r.stdout+r.stderr:
                run([hfs,root,'mkdir',directory]);run([hfs,root,'chmod','755',directory])
        run([hfs,root,'add',source,guest]);run([hfs,root,'chmod','755',guest])
        run([hfs,root,'extract',guest,out/'roundtrip'])
        if sha(out/'roundtrip')!=sha(source):raise ValueError('HFS installed bytes differ')
    run([sys.executable,'-B','tools/audit-duchamp-ios-graphics.py',out/'dependency-audit','--guest-image',root])
    payload=out/'payload.bin';payload.write_bytes(layout.build(kernel,layout.REPO/'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt',root,var))
    profile=layout.verify(payload.read_bytes())
    initial=sha(root)
    run([sys.executable,'-B','tools/qemu-sweet.py',payload,out/'run','--kernel',kernel,'--framebuffer','duchamp','--secs','360','--snapshot-interval','2',
         '--save-ramdisk','--save-var-ramdisk','--fail-on-panic','--stop-on-text','SWEET ipc ios-admission: COMPLETE','--stop-on-text','SWEET ipc ios-admission: FAIL'],timeout=420)
    traces={}
    for guest,name in [('/tmp/ipc-ios-admission.log','admission.log'),('/tmp/apple-backboardd-loader.log','backboardd-loader.log'),('/tmp/apple-SpringBoard-loader.log','SpringBoard-loader.log'),('/tmp/duchamp-var-witness','var-witness.txt')]:
        run([hfs,out/'run/var-final.hfs','extract',guest,out/name]);traces[name]=(out/name).read_text(errors='replace')
    state=json.loads((out/'run/result.json').read_text());trace=traces['admission.log']
    observations={}
    for name in ('backboardd','SpringBoard'):
        found=re.search(r'APPLE EXEC name='+name+r' pid=(\d+) target_uid=501 exec_errno=(\d+) accepted=(\d+) wait_status=(\d+) signal=(\d+) exit=(\d+) timeout=(\d+)',trace)
        observations[name]=dict(zip(['pid','exec_errno','accepted','wait_status','signal','exit','timeout'],map(int,found.groups()))) if found else {}
        if observations[name]:
            observations[name]['raw_exit_bits']=observations[name].pop('exit')
            observations[name].update(terminal_status(observations[name]['wait_status']))
        observations[name]['loader_log']=traces[name+'-loader.log']
        blocked='Library not loaded:' in observations[name]['loader_log'] or observations[name].get('exec_errno',0)>0
        observations[name]['service_started']=False if blocked else None
        observations[name]['scope']='bounded direct-exec admission; original launchd service domain not tested'
    witness=dict(line.split('=',1) for line in traces['var-witness.txt'].splitlines())
    checks=dict(exact_source_kernel=sha(kernel)==pin,native_parent_launchd='ppid=1 uid=0 parent=/sbin/launchd' in trace,
        complete='COMPLETE' in trace,no_probe_failures='FAIL' not in trace,
        actual_display_and_surface_queries='CAPABILITY surface_limits_version=1 row_mask=63 display=1220x2712' in trace,
        no_shared_cache_reported='cache_present=0' in trace,
        original_binaries_installed=all(sha(REPO/s)==h for s,h in APPLE.values()),
        actual_exec_observations=all(o.get('pid',0)>1 and o.get('timeout')==0 for o in observations.values()),
        loader_blockers_observed=all('Library not loaded:' in o['loader_log'] or o.get('exec_errno',0)>0 for o in observations.values()),
        no_graphical_success_claim=all(o['service_started'] is False for o in observations.values()),
        root_readonly_unchanged=initial==sha(out/'run/ramdisk-final.hfs'),
        writable_var=sha(var)!=sha(out/'run/var-final.hfs'),
        filesystem_witness=witness.get('root_errno')=='30' and witness.get('capacity_errno')=='28',
        no_panic_observed=state['status']=='no_panic_observed',
        ufs_disabled=profile['root']['bytes']==32*1024**2 and profile['var']['bytes']==4*1024**2)
    report=dict(passed=all(checks.values()),checks=checks,observations=observations,kernel_sha256=pin,
        payload_sha256=sha(payload),root_sha256=initial,profile=profile,
        authentic_graphical_services_running=False if all(o['service_started'] is False for o in observations.values()) else None,
        phone_operations=[],physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
