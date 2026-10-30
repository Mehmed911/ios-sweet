"""Strict opt-in virtual UFS profile; shared by the builder/runner and tests."""
import hashlib
from pathlib import Path
import stat
import struct
import adt

FIRMWARE=b'duchamp-qemu-ufs-fixture-v1\0'
COMPATIBLE=b'qemu,ufs-test-only\0'
BAR=(0x10000000,0x1000)
ECAM=(0x3f000000,0x1000000)


def child(node,name):
    matches=[c for c in node.children if c.name==name]
    if len(matches)!=1:
        raise ValueError(f'expected exactly one ADT {name}')
    return matches[0]


def validate_tree(tree):
    chosen=child(tree,'chosen')
    if chosen.prop('firmware-version')!=FIRMWARE:
        raise ValueError('not a virtual UFS firmware profile')
    if chosen.prop('dram-base')!=struct.pack('<Q',0x1c0000000) or chosen.prop('dram-size')!=struct.pack('<Q',0x20000000):
        raise ValueError('virtual UFS requires the established Duchamp memory window')
    node=child(tree,'duchamp-qemu-ufs')
    if node.prop('compatible')!=COMPATIBLE or node.prop('reg')!=struct.pack('<2Q',*BAR) or node.prop('ecam')!=struct.pack('<2Q',*ECAM):
        raise ValueError('virtual PCI UFS resource mismatch')
    if child(chosen,'memory-map').prop('RAMDisk') is not None:
        raise ValueError('virtual UFS test must not contain a fallback RAMDisk')
    if any(c.name=='sweet-ufs' for c in tree.children):
        raise ValueError('physical Qualcomm UFS node is not allowed in this fixture')
    armio=child(tree,'arm-io'); gic=child(armio,'gic')
    ranges=armio.prop('ranges'); registers=gic.prop('reg')
    if ranges!=struct.pack('<3Q',0,0x01000000,0xff000000) or not registers or len(registers)!=32:
        raise ValueError('unknown virtual arm-io/GIC address translation')
    d,ds,r,rs=struct.unpack('<4Q',registers)
    if (d+0x01000000,r+0x01000000)!=(0x08000000,0x080a0000) or ds<0x10000 or rs<0x20000 or gic.prop('virtual-timer-intid')!=struct.pack('<I',27):
        raise ValueError('GIC/timer profile does not match QEMU virt')


def build_tree(raw):
    tree,end=adt.parse(raw)
    if end!=len(raw):
        raise ValueError('ADT has trailing data')
    if any(c.name in ('duchamp-qemu-ufs','sweet-ufs') for c in tree.children):
        raise ValueError('base must be a QEMU ADT without storage nodes')
    chosen=child(tree,'chosen')
    if child(chosen,'memory-map').prop('RAMDisk') is not None:
        raise ValueError('base ADT already contains RAMDisk')
    chosen.props=[(n,f,FIRMWARE if n=='firmware-version' else v) for n,f,v in chosen.props]
    node=adt.Node(); node.props=[('name',0,b'duchamp-qemu-ufs\0'),
        ('compatible',0,COMPATIBLE),('reg',0,struct.pack('<2Q',*BAR)),('ecam',0,struct.pack('<2Q',*ECAM))]
    tree.children.append(node)
    validate_tree(tree)
    return adt.serialize(tree)


def runner_options(payload,image,cpu,framebuffer):
    if cpu!='cortex-a76' or framebuffer!='duchamp':
        raise ValueError('virtual UFS requires Cortex-A76 and Duchamp framebuffer')
    offset,size=struct.unpack_from('<2Q',payload,0x20)
    if offset>len(payload) or size>len(payload)-offset:
        raise ValueError('payload ADT outside image')
    tree,end=adt.parse(payload[offset:offset+size])
    if end!=size:
        raise ValueError('invalid payload ADT length')
    validate_tree(tree)
    args=payload[0x48:0x48+608].split(b'\0')[0].decode('ascii').split()
    if args.count('rd=qufs0')!=1 or args.count('sweet-qemu-ufs=1')!=1:
        raise ValueError('missing explicit virtual UFS boot arguments')
    if any(x.startswith('rd=') and x!='rd=qufs0' or x.startswith('rootrw=') and x!='rootrw=0' or
           x.startswith('sweet-qemu-ufs=') and x!='sweet-qemu-ufs=1' or
           x.startswith('ufsrw=') and x!='ufsrw=0' for x in args):
        raise ValueError('ambiguous root or writable storage boot arguments')
    path=Path(image).resolve()
    if not stat.S_ISREG(path.stat().st_mode) or ',' in str(path):
        raise ValueError('UFS image must be a regular file with a comma-free path')
    raw=path.read_bytes()
    if len(raw)%4096 or len(raw)<1024*1024 or raw[1024:1026] not in (b'H+',b'HX'):
        raise ValueError('UFS fixture must be an aligned HFS+ file')
    metadata={'image':str(path),'image_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
              'readonly':True,'bar':list(BAR),'ecam':list(ECAM),'bus':0,'slot':4,'function':0,
              'no_ramdisk':True,'scope':'QEMU-only virtual UFS; no physical device'}
    options=['-drive',f'file={path},format=raw,if=none,id=duchamp_lu0,readonly=on',
             '-device','ufs,id=duchamp_ufs,addr=04.0,mcq=off',
             '-device','ufs-lu,drive=duchamp_lu0,bus=duchamp_ufs,lun=0']
    return options,metadata
