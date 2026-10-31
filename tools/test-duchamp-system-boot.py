#!/usr/bin/env python3
"""Reboot a pinned, already verified Apple-service RAM fixture on a selected kernel.

No Apple files are downloaded, redistributed or changed. No physical device API.
The icount option changes virtual time; it is never a hardware timing result.
"""
import argparse,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def native_workspace(a,repo):
    """Keep all high-frequency guest tracing/snapshots on Linux's filesystem."""
    if os.name!='posix':raise ValueError('native workspace requires Linux/WSL')
    local=Path(tempfile.mkdtemp(prefix='duchamp-system-',dir='/tmp'))
    tools=local/'tools';tools.mkdir();ref=local/'reference';ref.mkdir()
    source_names=['test-duchamp-system-boot.py','verify-sweet-cfprefs-batch.py',
                  'qemu-sweet.py','mkpayload.py','adt.py','qemu_ufs.py']
    sources={name:sha(repo/'tools'/name) for name in source_names}
    for name in source_names:shutil.copy2(repo/'tools'/name,tools/name)
    for name in ['root.hfs','inputs.json','runtime-audit.json','launchctl-root-manifest.json',
                 'sweet-launchd-service','sweet-ipc-client','sweet-launchctl-control']:
        shutil.copy2(a.reference/name,ref/name)
    shutil.copytree(a.reference/'test-sources',ref/'test-sources')
    (ref/'run').mkdir();shutil.copy2(a.reference/'run/verification.json',ref/'run/verification.json')
    for src,dest in [(a.kernel,local/'kernel'),(a.adt,local/'tree.adt'),(a.hfsplus,local/'hfsplus')]:
        shutil.copy2(src,dest)
        if sha(src)!=sha(dest):raise ValueError('native input copy differs')
    (local/'hfsplus').chmod(0o755)
    command=['python3',str(tools/'test-duchamp-system-boot.py'),'--kernel',str(local/'kernel'),
        '--kernel-sha256',a.kernel_sha256,'--root-sha256',a.root_sha256,'--reference',str(ref),
        '--adt',str(local/'tree.adt'),'--hfsplus',str(local/'hfsplus'),'--output',str(local/'result'),
        '--seconds',str(a.seconds)]
    if a.icount_shift is not None:command+=['--icount-shift',str(a.icount_shift)]
    print('Linux-local workspace: '+str(local),flush=True)
    with (local/'console.log').open('w') as log:
        rc=subprocess.run(command,cwd=local,stdout=log,stderr=subprocess.STDOUT).returncode
    # Keep the native evidence directory, including failures; never remove it.
    if (local/'result').exists():shutil.copytree(local/'result',a.output)
    else:a.output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(local/'console.log',a.output/'console.log')
    unchanged=sources=={name:sha(repo/'tools'/name) for name in source_names}
    metadata={'child_exit':rc,'linux_workspace':str(local),'sources_sha256':sources,
              'original_sources_unchanged':unchanged,'timing':'unmodified QEMU clock' if a.icount_shift is None else 'icount',
              'scope':'copied files only; no phone or partition access; native evidence retained'}
    (a.output/'native-workspace.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2))
    return rc if rc else 0 if unchanged else 1

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for arg in ['kernel','reference','adt','hfsplus','output']:ap.add_argument('--'+arg,type=Path,required=True)
    ap.add_argument('--kernel-sha256',required=True);ap.add_argument('--root-sha256',required=True)
    ap.add_argument('--icount-shift',type=int,choices=range(11));ap.add_argument('--seconds',type=int,default=1800)
    ap.add_argument('--native-workspace',action='store_true',help='copy inputs to a new /tmp workspace, then copy results back')
    a=ap.parse_args();repo=Path(__file__).resolve().parent.parent;ref=a.reference.resolve();out=a.output.resolve()
    if out.exists():ap.error('preserve existing output')
    if sha(a.kernel)!=a.kernel_sha256 or sha(ref/'root.hfs')!=a.root_sha256:ap.error('explicit kernel/root pin differs')
    if a.native_workspace:
        a.reference=ref;a.output=out
        return native_workspace(a,repo)
    previous=json.loads((ref/'run/verification.json').read_text());inputs=json.loads((ref/'inputs.json').read_text())
    if not previous['passed'] or len(previous['checks'])!=72 or not all(previous['checks'].values()):
        ap.error('reference must have all72 grouped service checks passing')
    if previous['sha256']['root.hfs']!=a.root_sha256 or sha(a.adt)!=inputs['input_hashes']['adt']:
        ap.error('reference root/ADT provenance differs')
    files=['root.hfs','launchctl-root-manifest.json','runtime-audit.json',
           'sweet-launchd-service','sweet-ipc-client','sweet-launchctl-control']
    before={name:sha(ref/name) for name in files}
    for name,digest in inputs['compiled_source_snapshot'].items():
        if Path(name).name!=name or sha(ref/'test-sources'/name)!=digest:ap.error('reference source snapshot differs')
    for name in ['sweet-launchd-service','sweet-ipc-client','sweet-launchctl-control']:
        if before[name]!=previous['sha256'][name]:ap.error('reference diagnostic binary differs')
    tracked=[repo/'tools'/name for name in ['qemu-sweet.py','mkpayload.py','verify-sweet-cfprefs-batch.py','test-duchamp-system-boot.py']]
    source_hashes={str(p.relative_to(repo)):sha(p) for p in tracked}
    out.mkdir(parents=True,exist_ok=False)
    for name in files:shutil.copyfile(ref/name,out/name)
    shutil.copytree(ref/'test-sources',out/'test-sources')
    # Retain compiled-program provenance; only the selected kernel is different.
    inputs['input_hashes']['kernel']=a.kernel_sha256
    (out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    cmdline='debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
    subprocess.run(['python3',str(repo/'tools/mkpayload.py'),str(a.kernel.resolve()),str(a.adt.resolve()),
                    str(out/'payload.bin'),'--ramdisk',str(out/'root.hfs'),'--cmdline',cmdline],check=True)
    command=['python3',str(repo/'tools/qemu-sweet.py'),str(out/'payload.bin'),str(out/'run'),
        '--secs',str(a.seconds),'--framebuffer','duchamp','--kernel',str(a.kernel.resolve()),
        '--snapshot-interval','5','--save-ramdisk','--fail-on-panic']
    for marker in ['SWEET EARLY PANIC:','SWEET launchctl: FAIL','SWEET launchctl: heartbeat=2 ',
        'PREFERENCES BATCH ERROR','PREFERENCES ERROR','Library not loaded:','Symbol not found:','exited due to SIGSEGV']:
        command+=['--stop-on-text',marker]
    if a.icount_shift is not None:command+=['--icount-shift',str(a.icount_shift)]
    (out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    rc=subprocess.run(command).returncode
    vr=subprocess.run(['python3',str(repo/'tools/verify-sweet-cfprefs-batch.py'),str(out),
        '--hfsplus',str(a.hfsplus.resolve()),'--kernel-sha256',a.kernel_sha256]).returncode
    result=json.loads((out/'run/verification.json').read_text())
    checks={'guest_runner_exit_zero':rc==0,'all_service_checks':vr==0 and result['passed'],
        'kernel_pin_preserved':sha(a.kernel)==a.kernel_sha256,
        'reference_unchanged':before=={n:sha(ref/n) for n in files},
        'input_root_unchanged':sha(out/'root.hfs')==a.root_sha256,
        'harness_sources_unchanged':source_hashes=={str(p.relative_to(repo)):sha(p) for p in tracked}}
    summary={'passed':all(checks.values()),'checks':checks,'service_checks':len(result['checks']),
        'kernel_sha256':a.kernel_sha256,'reference_root_sha256':a.root_sha256,
        'service_report_sha256':sha(out/'run/verification.json'),'harness_sources':source_hashes,
        'execution':json.loads((out/'run/execution.json').read_text()),
        'elapsed_host_seconds':result['elapsed_host_seconds'],
        'scope':'original Apple launchd/notifyd/cfprefsd and Foundation clients in QEMU RAM only; no complete iOS/UI or phone support'}
    (out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
    return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
