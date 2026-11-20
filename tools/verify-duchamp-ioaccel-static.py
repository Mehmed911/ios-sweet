#!/usr/bin/env python3
"""0BSD: rebind bounded static claims to the original local 20F66 cache bytes.

Not a test of a running Apple graphics provider. Does not request GPU services.
"""
import argparse
import hashlib
import json
from pathlib import Path
import uuid
import duchamp_cache_code as cache


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('evidence',type=Path)
    ap.add_argument('--prior',required=True,type=Path)
    args=ap.parse_args();out=args.evidence;prior=args.prior
    files=[out/'descriptor-consumer-original.json',out/'descriptor-symbol-resolver.json',
           out/'dlsym-stub.json',out/'device-config64.json',out/'device-shared-size.json',
           out/'device-max-resource.json']
    files += [out/(s+'.json') for s in ('device-release','shared-release',
              'queue-release','shared-create-devshmem','shared-destroy-devshmem')]
    files += [prior/(s+'-bounded.json') for s in ('ioaccel_shared_create',
              'ioaccel_queue_create','ioaccel_queue_submit','ioaccel_resource_create')]
    checked=[];instructions={}
    for path in files:
        d=json.loads(path.read_text());code=bytes.fromhex(d['code']);va=int(d['address'],16)
        assert cache.read(va,len(code))==code, 'cache code differs: '+str(path)
        decoded=cache.Cs(cache.CS_ARCH_ARM64,cache.CS_MODE_ARM).disasm(code,va)
        rows=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str) for i in decoded]
        assert rows==d['instructions'], 'disassembly differs: '+str(path)
        instructions.update({r['address']:(r['mnemonic'],r['operands']) for r in rows})
        checked.append(dict(path=str(path.resolve()),va=hex(va),size=len(code),
                            code_sha256=hashlib.sha256(code).hexdigest(),
                            artifact_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    anchors={
        '0x1b2fb2534':('mov','w8, #0x258'),
        '0x1b2fb2540':('add','x4, sp, #0x30'),
        '0x1b2fb2548':('mov','w1, #2'),
        '0x1b2fb2598':('ldr','x21, [sp, #0x30]'),
        '0x1b2fb25a4':('ldr','w20, [sp, #0x44]'),
        '0x1b2fb25c4':('ldr','w9, [sp, #0x88]'),
        '0x1b2fb25d8':('add','x10, x10, #0x5c'),
        '0x1b2fb25dc':('ldr','w11, [x10, x8, lsl #2]'),
        '0x1b2fb2620':('ldr','w12, [x12]'),
        '0x1b2fb2634':('ldr','d0, [sp, #0x38]'),
        '0x1b2fb263c':('ldr','w8, [sp, #0x40]'),
        '0x1b2fb2648':('add','x1, x8, #0x18'),
        '0x1b2fb2650':('bl','#0x1b68f6058'),
        '0x1b2fb2668':('add','x4, x19, #0x270'),
        '0x1b2fb2670':('mov','w1, #0'),
        '0x1b2fb2d98':('mov','w2, #2'),
        '0x1b2fb4284':('mov','w2, #4'),
        '0x1b2fb4578':('ldr','w22, [x20, #4]'),
        '0x1b2fb45a8':('mov','w8, #0x18'),
        '0x1b2fb45b0':('madd','x5, x21, x8, x9'),
        '0x1b2fb2f34':('mov','w8, #0x10'),
        '0x1b2fb2f50':('mov','w1, #5'),
        '0x1b2fb2f54':('mov','w3, #1'),
        '0x1b2fb2f8c':('ldp','w24, w26, [sp, #0x20]'),
        '0x1b2fb30fc':('mov','w1, #6'),
        '0x1b2fb3100':('mov','w3, #1'),
        '0x1b2fb272c':('b','#0x1b68f5ecc'),
        '0x1b2fb2eb8':('b','#0x1b68f5ecc'),
        '0x1b2fb44ec':('b','#0x1b68f5ecc'),
    }
    for address,pair in anchors.items():assert instructions[address]==pair,(address,instructions.get(address))
    symbol=cache.symbol(0x1a6c2cc88)
    assert symbol['exit_code']==0 and '0x1a6c2cc88: _dlsym' in symbol['text']
    with (cache.ROOT/'dyld_shared_cache_arm64').open('rb') as f:header=f.read(104)
    cache_uuid=str(uuid.UUID(bytes=header[88:104])).upper()
    assert cache_uuid=='E5420DB3-30D0-33AA-8B7E-05B5038BB46D'
    report=dict(passed=True,cache_uuid=cache_uuid,code_intervals=checked,
                instruction_anchors=len(anchors),dlsym_symbol=symbol,
                actual_producer_descriptor_observed=False,
                first_springboard_frame_verified=False,
                status='BLOCKED_BY_UNKNOWN_ABI')
    (out/'static-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,intervals=len(checked),anchors=len(anchors),
                         dlsym_verified=True,cache_uuid=cache_uuid)))


if __name__=='__main__':main()
