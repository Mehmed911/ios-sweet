#!/usr/bin/env python3
"""Require actual XNU root mount + PID1 reads over read-only QEMU UFS."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
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
    ap.add_argument('--backends',action='store_true',help='require the opt-in kernel backend/table selftest and devfs receipt')
    args=ap.parse_args()
    repo=Path(__file__).resolve().parent.parent
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    kernel=args.kernel.resolve(); fixture=args.fixture.resolve()
    test_paths=[repo/'tools'/name for name in ('qemu-sweet.py','qemu_ufs.py','duchamp-ufs-init.S',
        'test-duchamp-ufs-xnu.py','build-duchamp-ufs-fixture.py','mkpayload.py')]
    init_name='duchamp-backend-init.S' if args.backends else 'duchamp-ufs-init.S'
    if args.backends: test_paths.append(repo/'tools'/init_name)
    source_hashes={str(p.relative_to(repo)):digest(p) for p in test_paths}
    if digest(kernel)!=args.kernel_sha256:
        ap.error('kernel hash differs from the explicitly selected CI artifact')
    manifest=json.loads((fixture/'fixture.json').read_text())
    if manifest['init_source_sha256']!=digest(repo/'tools'/init_name):
        ap.error('fixture init was built from a different diagnostic source')
    for name,expected in manifest['sha256'].items():
        if digest(fixture/name)!=expected: ap.error('fixture changed: '+name)
    symbols=subprocess.check_output(['llvm-nm','--defined-only',str(kernel)],text=True)
    names={line.split()[-1] for line in symbols.splitlines() if line.split()}
    required={'_duchamp_qemu_ufs_rootdev','_dufs_bind','_dufs_read','_dufs_start','_dufs_timeout_cause'}
    if args.backends:
        required|={'_duchamp_qemu_backends_prepare','_mv7_map','_mv7_seal','_mb_iommu_install',
                   '_mb_pmic_voltage','_mb_pmif_transfer','_mb_firmware_ufs','_mp_prepare',
                   '_md_bind','_mufs_clock_set'}
    if not required<=names: ap.error('kernel lacks the new BSD/core integration')
    physical_symbols={}
    if args.backends:
        for name in ('_root_pa','_pool_pa','_data_pa'):
            matches=[int(line.split()[0],16) for line in symbols.splitlines() if line.split()[-1]==name]
            if len(matches)!=1: ap.error('backend physical diagnostic symbol not unique: '+name)
            physical_symbols[name]=matches[0]
    cmdline='debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=qufs0 rootrw=0 sweet-qemu-ufs=1 sweet_console_fb=1'
    if args.backends: cmdline+=' sweet-qemu-backends=1'
    payload=out/'payload.bin'
    subprocess.run(['python3',str(repo/'tools/mkpayload.py'),str(kernel),str(fixture/'qemu-ufs.adt'),
                    str(payload),'--cmdline',cmdline],check=True)
    packed=payload.read_bytes()
    virt_base,=struct.unpack_from('<Q',packed,0x10)
    phys_base,=struct.unpack_from('<Q',packed,0x38)
    # The runner copies each static segment at PA = VA - virt_base + phys_base.
    # Physical monitor reads remain valid when the CPU has returned to EL0.
    physical_locations={name:address-virt_base+phys_base for name,address in physical_symbols.items()}
    run=out/'run'
    command=['python3',str(repo/'tools/qemu-sweet.py'),str(payload),str(run),
        '--kernel',str(kernel),'--framebuffer','duchamp','--ufs-image',str(fixture/'root.hfs'),
        '--secs',str(args.seconds),'--snapshot-interval','2','--fail-on-panic',
        '--stop-on-text','SWEET EARLY PANIC:','--stop-on-text','DUCHAMP UFS PID1 FAIL',
        '--stop-on-text','DUCHAMP UFS PID1 heartbeat']
    # Read stopped-guest globals through the monitor; do not alter guest state.
    for address in physical_locations.values():
        command+=['--hmp',f'xp/1gx 0x{address:x}']
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
    if args.backends:
        required_text+=['QEMU XNU BACKENDS SELFTEST PASS',
            'DUCHAMP XNU BACKENDS PASS tables=1 mmu=1 pmic=1 fw_verified=0 physical=0',
            'DUCHAMP XNU BACKEND RECEIPT EOF EROFS PASS']
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
    physical_addresses={}
    if args.backends:
        stopped=(run/'regs.txt').read_text()
        for name,address in physical_locations.items():
            match=re.search(rf'(?m)^(?:0x)?{address:016x}:\s+(0x[0-9a-f]+)',stopped)
            if match: physical_addresses[name]=int(match[1],16)
        root=physical_addresses.get('_root_pa',0)
        checks['physical_root_alignment_and_range']=bool(root and root%65536==0 and root+65536<=1<<35)
    report={'passed':all(checks.values()),'checks':checks,'kernel_sha256':args.kernel_sha256,
        'early_log_visibility':{text:text in screen for text in ('DUCHAMP QUFS READY','DUCHAMP QUFS ROOT SELECTED')},
        'test_source_hashes':source_hashes,
        'ci_run':args.ci_run,'ci_head':args.ci_head,'fixture':manifest,
        'payload_sha256':digest(payload),'source_root_unchanged':checks['host_image_unchanged'],
        'elapsed_host_seconds':result.get('elapsed_host_seconds'),'sampled_frames':len(frames),
        'framebuffer_is_sampled':True,'backend_selftest_requested':args.backends,
        'stopped_guest_physical_addresses':{name:hex(value) for name,value in physical_addresses.items()},
        'physical_diagnostics_read_only':True,
        'scope':'XNU + read-only virtual UFS/HFS+ + diagnostic PID1; optional in-kernel backend/table RAM models, no physical phone/backend'}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
