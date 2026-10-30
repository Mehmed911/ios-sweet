#!/usr/bin/env python3
"""Check the six supported leaf gates against a register model, not a phone."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('output',type=Path)
    ap.add_argument('--hardware-report',type=Path)
    args=ap.parse_args(); out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    src=Path(__file__).resolve().parent.parent/'duchamp/drivers'
    binary=out/'clock-tests'
    files=[src/'mt6897_ufs_clocks.c',src/'mt6897_ufs_clocks.h',src/'test_mt6897_clocks.c']
    subprocess.run(['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
        '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(files[0]),str(files[2]),
        '-o',str(binary)],check=True)
    r=subprocess.run([str(binary)],check=True,capture_output=True,text=True)
    (out/'sanitizer.log').write_text(r.stdout+r.stderr)
    obj=out/'clocks.arm64.o'
    subprocess.run(['clang','-target','aarch64-none-elf','-std=c11','-O2','-ffreestanding',
        '-fno-builtin','-mgeneral-regs-only','-Wall','-Wextra','-Werror','-c',str(files[0]),'-o',str(obj)],check=True)
    imports=subprocess.check_output(['llvm-nm','--undefined-only',str(obj)],text=True).strip()
    if imports: raise RuntimeError('unexpected freestanding imports: '+imports)
    report={'passed':True,'native_result':r.stdout.strip(),'freestanding_arm64_compile':True,
        'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'scope':'six AO/PDN leaf gates in a native register model; no physical MMIO, power/PHY/SiP or XNU integration'}
    if args.hardware_report:
        hardware=json.loads(args.hardware_report.read_text())
        if hardware['fdt_sha256']!='9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29':
            raise RuntimeError('unexpected captured-DTB provenance')
        selected=[]; remaining=[]
        for clock in hardware['nodes']['ufs']['clocks']:
            if clock['provider'] in ('/syscon@112b8000','/syscon@112bb000'):
                cells=clock['provider_reg_cells']
                if len(cells)!=4 or cells[0] or cells[2] or cells[3]!=0x1000 or len(clock['args'])!=1:
                    raise RuntimeError('leaf clock provider format changed')
                selected.append((clock['name'],cells[1],clock['args'][0]))
            else: remaining.append(clock['name'])
        expected=[('unipro_tx_sym',0x112b8000,0),('unipro_rx_sym0',0x112b8000,1),
            ('unipro_rx_sym1',0x112b8000,2),('unipro_sysclk',0x112b8000,3),
            ('ufshci_ufs',0x112bb000,0),('ufshci_aes',0x112bb000,1)]
        if selected!=expected: raise RuntimeError('captured leaf clock IDs differ from implementation')
        report['captured_fdt_leaf_mapping_verified']=True
        report['unimplemented_topckgen_references']=remaining
        report['physical_platform_backend_complete']=False
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))


if __name__=='__main__': main()
