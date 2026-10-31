#!/usr/bin/env python3
"""Produce an offline ADT boot profile and evidence manifest from saved inputs."""
import argparse,json,tomllib
from pathlib import Path
import duchamp_boot_profile as p
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--fdt',type=Path,required=True)
    ap.add_argument('--template',type=Path,required=True);ap.add_argument('--sources',type=Path,required=True)
    ap.add_argument('--target',choices=['phone','qemu'],required=True)
    ap.add_argument('--board',type=Path,default=Path(__file__).resolve().parent.parent/'duchamp/board.toml')
    a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing output')
    before=p.sources(a.sources);raw=a.fdt.read_bytes();template=a.template.read_bytes();board=a.board.read_bytes()
    if p.sha(raw)!=p.FDT_SHA:ap.error('saved FDT pin differs')
    profile=p.facts(p.hardware.Fdt(raw),tomllib.loads(board.decode()))
    blob,emitted=p.build(template,a.target,profile)
    if before!=p.sources(a.sources) or raw!=a.fdt.read_bytes() or template!=a.template.read_bytes() or board!=a.board.read_bytes():
        raise ValueError('inputs changed')
    a.output.mkdir(parents=True,exist_ok=False);(a.output/'boot.adt').write_bytes(blob)
    result={'built':True,'fdt_sha256':p.FDT_SHA,'template_sha256':p.sha(template),'board_sha256':p.sha(board),
        'adt_sha256':p.sha(blob),'saved_hardware':profile,'emitted':emitted,'source_receipts':before,
        'tool_sha256':{f.name:p.sha(f.read_bytes()) for f in [Path(__file__),Path(p.__file__),Path(p.adt.__file__),Path(p.hardware.__file__)]},
        'runtime_counter_frequency_verified':False,'physical_gic_ownership_verified':False,
        'scope':'offline single-CPU bootstrap description; no payload jump, firmware calls or phone/partition access'}
    (a.output/'profile.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(a.output),'adt_sha256':p.sha(blob),'emitted':emitted},indent=2))
if __name__=='__main__':main()
