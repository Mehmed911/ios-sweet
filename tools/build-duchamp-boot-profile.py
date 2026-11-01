#!/usr/bin/env python3
"""Produce an offline ADT boot profile and evidence manifest from saved inputs."""
import argparse,json,tomllib
from pathlib import Path
import duchamp_boot_profile as p
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--fdt',type=Path,required=True)
    ap.add_argument('--reference-fdt',type=Path,
                    help='exact pinned DTB required when --fdt is a live runtime variant')
    ap.add_argument('--template',type=Path,required=True);ap.add_argument('--sources',type=Path,required=True)
    ap.add_argument('--target',choices=['phone','qemu'],required=True)
    ap.add_argument('--authorize-phone-gic-trial',action='store_true',
                    help='emit the exact physical-GIC diagnostic capability')
    ap.add_argument('--gic-runtime-evidence',type=Path,
                    help='fresh read-only Android GIC report required for the phone capability')
    ap.add_argument('--board',type=Path,default=Path(__file__).resolve().parent.parent/'duchamp/board.toml')
    a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing output')
    before=p.sources(a.sources);raw=a.fdt.read_bytes();template=a.template.read_bytes();board=a.board.read_bytes()
    reference=a.reference_fdt.read_bytes() if a.reference_fdt else None
    try:tree,provenance=p.validate_fdt(raw,reference)
    except ValueError as error:ap.error(str(error))
    profile=p.facts(tree,tomllib.loads(board.decode()))
    if a.authorize_phone_gic_trial:
        if not a.gic_runtime_evidence:ap.error('--gic-runtime-evidence is required')
        try:
            evidence_raw=a.gic_runtime_evidence.read_bytes()
            evidence=json.loads(evidence_raw)
            gic_evidence=p.validate_phone_gic_evidence(evidence,profile)
        except (OSError,UnicodeError,json.JSONDecodeError,ValueError) as error:ap.error(str(error))
    else:
        if a.gic_runtime_evidence:ap.error('--gic-runtime-evidence requires --authorize-phone-gic-trial')
        evidence_raw=None;gic_evidence=None
    blob,emitted=p.build(template,a.target,profile,
                         authorize_phone_gic=a.authorize_phone_gic_trial)
    if (before!=p.sources(a.sources) or raw!=a.fdt.read_bytes() or template!=a.template.read_bytes()
        or board!=a.board.read_bytes() or (a.reference_fdt and reference!=a.reference_fdt.read_bytes())
        or (a.gic_runtime_evidence and evidence_raw!=a.gic_runtime_evidence.read_bytes())):
        raise ValueError('inputs changed')
    a.output.mkdir(parents=True,exist_ok=False);(a.output/'boot.adt').write_bytes(blob)
    result={'built':True,'fdt_sha256':p.sha(raw),'fdt_provenance':provenance,
        'template_sha256':p.sha(template),'board_sha256':p.sha(board),
        'adt_sha256':p.sha(blob),'saved_hardware':profile,'emitted':emitted,'source_receipts':before,
        'tool_sha256':{f.name:p.sha(f.read_bytes()) for f in [Path(__file__),Path(p.__file__),Path(p.adt.__file__),Path(p.hardware.__file__)]},
        'runtime_counter_frequency_verified':False,'physical_gic_ownership_verified':False,
        'gic_runtime_evidence':None if evidence_raw is None else {
            'sha256':p.sha(evidence_raw),**gic_evidence},
        'scope':'offline single-CPU bootstrap description; no payload jump, firmware calls or phone/partition access'}
    (a.output/'profile.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(a.output),'adt_sha256':p.sha(blob),'emitted':emitted},indent=2))
if __name__=='__main__':main()
