#!/usr/bin/env python3
"""0BSD: correlate the new contract probe with the exact source-kernel trace.

Requires completed original-service verification and independently labelled
IOSurface evidence. Does not authorize hardware or certify a rendered frame.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from duchamp_graphics_provider import parse
from duchamp_metal_discovery import classify
from duchamp_source_kernel import select


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path)
    a=ap.parse_args();out=a.output.resolve();trial=out/'trial-1'
    inputs=json.loads((trial/'inputs.json').read_text())
    # A new audit run may reuse an unchanged, separately preserved source
    # build and guest binaries. Follow its explicit receipts, never fall back
    # to a different kernel or silently copy/relabel previous execution logs.
    manifest=Path(inputs.get('kernel_manifest',out/'kernel/build-manifest.json'))
    kernel=json.loads(manifest.read_text())['kernel'];pin=select(Path(kernel),manifest)
    config=Path(inputs.get('trace_config',out/'trace/trace-config.json'));cfg=json.loads(config.read_text())
    assert cfg['kernel_sha256']==pin and cfg['passive_only'] is True
    assert Path(cfg['kernel_manifest']).resolve()==manifest.resolve()
    assert cfg['source_trace_sha256']==sha('tools/duchamp-render-passive.gdb')
    assert inputs['trace_config_sha256']==sha(config)
    assert inputs['kernel']==pin
    build=Path(inputs.get('guest_build_reused',out/'guest-build'))
    for path,digest in json.loads((build/'source-pins.json').read_text()).items():
        assert sha(path)==digest, 'guest source changed since compilation: '+path
    services=json.loads((trial/'service-verification.json').read_text())
    assert services['passed'] and len(services['checks'])==22
    provider=parse((out/'platform-graphics-provider-contract.txt').read_text());assert provider['passed']
    pid=int(provider['process'][0])
    events=[json.loads(s) for s in (trial/'render-events.jsonl').read_text().splitlines()]
    assert events[0]['kernel_sha256']==pin and not any(e['kind']=='trace_error' for e in events)
    metal=classify(events);assert metal['status']=='DISCOVERY_BLOCKER_VERIFIED'
    assert metal['iterator']==0 and metal['class_name']=='IOAcceleratorES'
    methods=[e for e in events if e.get('pid')==pid and e['kind'] in ('surface_method','surface_method_return')]
    entered=[e for e in methods if e['kind']=='surface_method']
    returned=[e for e in methods if e['kind']=='surface_method_return']
    assert len(entered)==len(returned)==4
    assert all(e['caller_task_matches'] is True for e in entered)
    assert [e['selector'] for e in entered]==[13,13,0xffffffff,34]
    assert [e['result']&0xffffffff for e in returned]==[0,0xe00002db,0xe00002c7,0xe00002bf]
    for entry,result in zip(entered,returned):
        assert (entry['pid'],entry['birth'],entry['tid'],entry['selector'])==(result['pid'],result['birth'],result['tid'],result['selector'])
        assert entry['sequence']<result['sequence']
    original=[e for e in events if e.get('name') in ('backboardd','SpringBoard')]
    swaps=[e for e in original if e['kind']=='swap']
    assert swaps and all(e['record']['surfaces']==[0,0,0,0] for e in swaps)
    assert not [e for e in original if e['kind']=='surface_method' and e['selector']==0]
    assert not [e for e in original if e['kind']=='present']
    surface=(out/'platform-iosurface-contract.txt').read_text()
    assert len(re.findall(r'^SURFACE CHECK \S+ passed=1$',surface,re.M))==24
    assert 'SURFACE DONE checks=24 failed=0 cross_process=0 metal_compatibility=0' in surface
    control=(out/'ipc-platform-services.log').read_text()
    for tag in ('iosurface-contract','graphics-provider-contract'):
        assert f'PLATFORM COMMAND tag={tag} status=0x0 timeout=0' in control
    report=dict(passed=True,status='BLOCKED_BY_UNIMPLEMENTED_GRAPHICS_API',kernel_sha256=pin,
                service_checks=22,iosurface_checks=24,provider_checks=26,methods=methods,
                original_discovery=metal,original_swaps=swaps,first_springboard_frame_verified=False,
                physical_status='BLOCKED_BY_MEMORY_EVIDENCE',phone_operations=[])
    (out/'correlated-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('methods','original_swaps')},indent=2))


if __name__=='__main__':
    main()
