#!/usr/bin/env python3
"""Require actual XNU root mount + PID1 reads over read-only QEMU UFS."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kernel',type=Path,required=True)
    ap.add_argument('--kernel-sha256',required=True)
    ap.add_argument('--fixture',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--ci-run'); ap.add_argument('--ci-head')
    ap.add_argument('--seconds',type=int,default=180)
    args=ap.parse_args()
    repo=Path(__file__).resolve().parent.parent
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    kernel=args.kernel.resolve(); fixture=args.fixture.resolve()
    test_paths=[repo/'tools'/name for name in ('qemu-sweet.py','qemu_ufs.py','duchamp-ufs-init.S',
        'test-duchamp-ufs-xnu.py','build-duchamp-ufs-fixture.py')]
    source_hashes={str(p.relative_to(repo)):digest(p) for p in test_paths}
    if digest(kernel)!=args.kernel_sha256:
        ap.error('kernel hash differs from the explicitly selected CI artifact')
    manifest=json.loads((fixture/'fixture.json').read_text())
    if manifest['init_source_sha256']!=digest(repo/'tools/duchamp-ufs-init.S'):
        ap.error('fixture init was built from a different diagnostic source')
    for name,expected in manifest['sha256'].items():
        if digest(fixture/name)!=expected: ap.error('fixture changed: '+name)
    symbols=subprocess.check_output(['llvm-nm','--defined-only',str(kernel)],text=True)
    names={line.split()[-1] for line in symbols.splitlines() if line.split()}
    required={'_duchamp_qemu_ufs_rootdev','_dufs_bind','_dufs_read','_dufs_start'}
    if not required<=names: ap.error('kernel lacks the new BSD/core integration')
    cmdline='debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=qufs0 rootrw=0 sweet-qemu-ufs=1 sweet_console_fb=1'
    payload=out/'payload.bin'
    subprocess.run(['python3',str(repo/'tools/mkpayload.py'),str(kernel),str(fixture/'qemu-ufs.adt'),
                    str(payload),'--cmdline',cmdline],check=True)
    run=out/'run'
    command=['python3',str(repo/'tools/qemu-sweet.py'),str(payload),str(run),
        '--kernel',str(kernel),'--framebuffer','duchamp','--ufs-image',str(fixture/'root.hfs'),
        '--secs',str(args.seconds),'--snapshot-interval','2','--fail-on-panic',
        '--stop-on-text','SWEET EARLY PANIC:','--stop-on-text','DUCHAMP UFS PID1 FAIL',
        '--stop-on-text','DUCHAMP UFS PID1 heartbeat']
    rc=subprocess.run(command).returncode
    result=json.loads((run/'result.json').read_text())
    metadata=json.loads((run/'ufs-input.json').read_text())
    frames=sorted((run/'frames').glob('*.txt'))
    screen='\n'.join(p.read_text() for p in frames)
    if (run/'fb.txt').exists(): screen+='\n'+(run/'fb.txt').read_text()
    required_text=['QEMU RAM ROOT MOUNTED','QEMU ROOTVNODE READY','DUCHAMP UFS PID1 ENTERED',
        'DUCHAMP UFS ROOT DEVICE MATCH',
        'DUCHAMP UFS RAW HEADER READ PASS','DUCHAMP UFS WRITE OPEN REFUSED EROFS',
        'DUCHAMP UFS OFFSET READ PASS','DUCHAMP UFS USER COPY FAULT HANDLED',
        'DUCHAMP UFS HFS FILE BYTES MATCH','DUCHAMP UFS PID1 READ PASS','DUCHAMP UFS PID1 heartbeat']
    checks={text:text in screen for text in required_text}
    checks.update({
        'runner_exit_zero':rc==0,'decoded_framebuffer':result.get('unknown_glyphs')==0,
        'no_observed_panic':result.get('status')=='no_panic_observed' and not any(
            x in screen for x in ('panic(cpu ','SWEET EARLY PANIC:','DUCHAMP UFS PID1 FAIL','DUCHAMP QUFS ATTACH FAILED')),
        'success_stop':result.get('stop_marker')=='DUCHAMP UFS PID1 heartbeat',
        'host_image_unchanged':digest(fixture/'root.hfs')==manifest['sha256']['root.hfs']==metadata['sha256'],
        'readonly_no_ramdisk':metadata['readonly'] and metadata['no_ramdisk'],
        'kernel_pin_preserved':digest(kernel)==args.kernel_sha256,
        'compiled_adapter_symbols_present':required<=names})
    checks['test_sources_unchanged']=source_hashes=={str(p.relative_to(repo)):digest(p) for p in test_paths}
    report={'passed':all(checks.values()),'checks':checks,'kernel_sha256':args.kernel_sha256,
        'early_log_visibility':{text:text in screen for text in ('DUCHAMP QUFS READY','DUCHAMP QUFS ROOT SELECTED')},
        'test_source_hashes':source_hashes,
        'ci_run':args.ci_run,'ci_head':args.ci_head,'fixture':manifest,
        'payload_sha256':digest(payload),'source_root_unchanged':checks['host_image_unchanged'],
        'elapsed_host_seconds':result.get('elapsed_host_seconds'),'sampled_frames':len(frames),
        'framebuffer_is_sampled':True,'scope':'XNU + read-only virtual UFS/HFS+ + diagnostic PID1; no physical phone/backend'}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
