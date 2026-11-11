"""Strict opt-in virtual UFS profile; shared by the builder/runner and tests."""
import hashlib
from pathlib import Path
import stat
import struct
import uuid
import adt
from mkpayload import PAGE, SEG_TABLE

FIRMWARE=b'duchamp-qemu-ufs-fixture-v1\0'
COMPATIBLE=b'qemu,ufs-test-only\0'
BAR=(0x10000000,0x1000)
ECAM=(0x3f000000,0x1000000)
GPT_ROOT_GUID=uuid.UUID('a1f31536-d200-4eb6-b196-530f8768ea63')
PROBE_LUN=2
PROBE_LBA=276480
PROBE_BYTES=4096


def child(node,name):
    matches=[c for c in node.children if c.name==name]
    if len(matches)!=1:
        raise ValueError(f'expected exactly one ADT {name}')
    return matches[0]


def gpt_profile(node):
    sectors = [value for name, _, value in node.props if name == 'gpt-sector-size']
    guids = [value for name, _, value in node.props if name == 'gpt-root-guid']
    if not sectors and not guids:
        return None
    if (len(sectors) != 1 or sectors[0] not in (struct.pack('<I', 512), struct.pack('<I', 4096))
            or len(guids) != 1 or len(guids[0]) != 16 or not any(guids[0])):
        raise ValueError('virtual UFS requires exactly one valid GPT sector size and root GUID')
    return struct.unpack('<I', sectors[0])[0], uuid.UUID(bytes_le=guids[0])


def validate_tree(tree, *, allow_data_ramdisk=False):
    chosen=child(tree,'chosen')
    if chosen.prop('firmware-version')!=FIRMWARE:
        raise ValueError('not a virtual UFS firmware profile')
    if chosen.prop('dram-base')!=struct.pack('<Q',0x1c0000000) or chosen.prop('dram-size')!=struct.pack('<Q',0x20000000):
        raise ValueError('virtual UFS requires the established Duchamp memory window')
    node=child(tree,'duchamp-qemu-ufs')
    if node.prop('compatible')!=COMPATIBLE or node.prop('reg')!=struct.pack('<2Q',*BAR) or node.prop('ecam')!=struct.pack('<2Q',*ECAM):
        raise ValueError('virtual PCI UFS resource mismatch')
    if not allow_data_ramdisk and child(chosen,'memory-map').prop('RAMDisk') is not None:
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
    return gpt_profile(node)


def build_tree(raw, *, gpt=None):
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
    if gpt:
        sector, guid = gpt
        node.props.extend([('gpt-sector-size',0,struct.pack('<I',sector)),
                           ('gpt-root-guid',0,guid.bytes_le)])
    tree.children.append(node)
    validate_tree(tree)
    return adt.serialize(tree)


def data_ramdisk(payload, tree, adt_offset, adt_size):
    chosen = child(tree, 'chosen')
    mmap = child(chosen, 'memory-map')
    properties = [value for name, _, value in mmap.props if name == 'RAMDisk']
    if len(properties) != 1 or len(properties[0]) != 16:
        raise ValueError('expected exactly one bounded data RAMDisk')
    address, size = struct.unpack('<2Q', properties[0])
    magic, version, nsegs = struct.unpack_from('<8sII', payload)
    virt_base, _, _, _, kernel_end, phys_base, mem_size = struct.unpack_from('<7Q', payload, 16)
    table_end = SEG_TABLE + 32 * nsegs
    if (magic != b'SWEETXNU' or version != 1 or nsegs < 2 or table_end > adt_offset
            or (phys_base, mem_size) != (0x1c0000000, 0x20000000)):
        raise ValueError('invalid payload layout for the data RAMDisk')
    if (address % PAGE or size % PAGE or not (1 << 20) <= size <= (64 << 20)
            or address < phys_base):
        raise ValueError('data RAMDisk must be aligned and at most 64 MiB')
    va = virt_base + address - phys_base
    top = (kernel_end + adt_size + PAGE - 1) & -PAGE
    if va + size != kernel_end or top + PAGE > virt_base + mem_size:
        raise ValueError('data RAMDisk must end at the reserved payload boundary')
    segments = list(struct.iter_unpack('<4Q', payload[SEG_TABLE:table_end]))
    for segment_va, span, offset, length in segments[:-1]:
        if (segment_va < virt_base or segment_va + span > va or length > span
                or offset < table_end or offset + length > adt_offset):
            raise ValueError('kernel segment conflicts with data RAMDisk')
    segment_va, span, offset, length = segments[-1]
    if ((segment_va, span, length) != (va, size, size)
            or offset < table_end or offset + length > adt_offset
            or any(start + count > offset for _, _, start, count in segments[:-1])
            or payload[offset+1024:offset+1026] not in (b'H+', b'HX')):
        raise ValueError('data RAMDisk is not a complete HFS+ payload segment')
    return {'address': address, 'bytes': size,
            'sha256': hashlib.sha256(memoryview(payload)[offset:offset+size]).hexdigest()}


def runner_options(payload,image,cpu,framebuffer, *, var_ramdisk=False):
    if cpu!='cortex-a76' or framebuffer!='duchamp':
        raise ValueError('virtual UFS requires Cortex-A76 and Duchamp framebuffer')
    offset,size=struct.unpack_from('<2Q',payload,0x20)
    if offset>len(payload) or size>len(payload)-offset:
        raise ValueError('payload ADT outside image')
    tree,end=adt.parse(payload[offset:offset+size])
    if end!=size:
        raise ValueError('invalid payload ADT length')
    gpt=validate_tree(tree, allow_data_ramdisk=var_ramdisk)
    args=payload[0x48:0x48+608].split(b'\0')[0].decode('ascii').split()
    if args.count('rd=qufs0')!=1 or args.count('sweet-qemu-ufs=1')!=1:
        raise ValueError('missing explicit virtual UFS boot arguments')
    if any(x.startswith('rd=') and x!='rd=qufs0' or x.startswith('rootrw=') and x!='rootrw=0' or
           x.startswith('sweet-qemu-ufs=') and x!='sweet-qemu-ufs=1' or
           x.startswith('ufsrw=') and x!='ufsrw=0' for x in args):
        raise ValueError('ambiguous root or writable storage boot arguments')
    probe_args = [x for x in args if x == 'sweet-qemu-ufs-probe' or
                  x.startswith('sweet-qemu-ufs-probe=')]
    if probe_args and (probe_args != ['sweet-qemu-ufs-probe=1'] or gpt or var_ramdisk or
                       args.count('rootrw=0') != 1 or
                       any(x.startswith(('pmd', 'vmd')) for x in args)):
        raise ValueError('one-block probe requires one opt-in and a read-only disk without a root volume')
    if var_ramdisk and (args.count('rootrw=0') != 1
            or any(x.startswith(('pmd', 'vmd')) for x in args)):
        raise ValueError('data RAMDisk requires explicit read-only root and no alternate memory devices')
    if gpt and (args.count('rootrw=0') != 1 or any(x.startswith(('pmd','vmd')) for x in args)):
        raise ValueError('GPT fixture requires explicit read-only root and no alternate memory devices')
    var_layout = data_ramdisk(payload, tree, offset, size) if var_ramdisk else None
    path=Path(image).resolve()
    if not stat.S_ISREG(path.stat().st_mode) or ',' in str(path):
        raise ValueError('UFS image must be a regular file with a comma-free path')
    before=path.stat()
    digest=hashlib.sha256()
    with path.open('rb') as source:
        if before.st_size%4096 or before.st_size<1024*1024:
            raise ValueError('UFS fixture must be aligned and at least 1 MiB')
        if probe_args:
            if before.st_size < (PROBE_LBA + 1) * PROBE_BYTES:
                raise ValueError('UFS probe image does not contain the reference LBA')
        elif gpt:
            source.seek(gpt[0])
            if source.read(8)!=b'EFI PART':
                raise ValueError('GPT fixture must contain a whole disk with a primary GPT header')
        else:
            source.seek(1024)
            if source.read(2) not in (b'H+',b'HX'):
                raise ValueError('UFS fixture must be an aligned HFS+ file')
        source.seek(0)
        for chunk in iter(lambda: source.read(4*1024*1024),b''):
            digest.update(chunk)
    after=path.stat()
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if identity(before)!=identity(after):
        raise ValueError('UFS fixture changed while hashing')
    metadata={'image':str(path),'image_bytes':before.st_size,'sha256':digest.hexdigest(),
              'readonly':True,'bar':list(BAR),'ecam':list(ECAM),'bus':0,'slot':4,'function':0,
              'no_ramdisk':not var_ramdisk,'scope':'QEMU-only virtual UFS; no physical device'}
    if var_layout:
        metadata['data_ramdisk'] = var_layout
    if gpt:
        metadata['gpt']={'sector_bytes':gpt[0],'root_guid':str(gpt[1])}
    lun = PROBE_LUN if probe_args else 0
    if probe_args:
        metadata['probe'] = {'lun': lun, 'lba': PROBE_LBA, 'bytes': PROBE_BYTES}
    drive_id = f'duchamp_lu{lun}'
    options=['-drive',f'file={path},format=raw,if=none,id={drive_id},readonly=on',
             '-device','ufs,id=duchamp_ufs,addr=04.0,mcq=off',
             '-device',f'ufs-lu,drive={drive_id},bus=duchamp_ufs,lun={lun}']
    return options,metadata
