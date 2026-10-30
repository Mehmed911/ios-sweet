#!/usr/bin/env python3
"""Read a saved DTB and resolve storage/graphics dependencies without device I/O.

Only selected hardware properties are emitted, never /chosen/bootargs, serials
or the full tree. Missing iommus is recorded as unknown, not DMA-bypass proof.
"""
import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import struct


@dataclass
class Node:
    path: str
    parent: object
    props: dict = field(default_factory=dict)

    def cells(self, key):
        raw = self.props.get(key, b'')
        if len(raw) % 4:
            raise ValueError(f'{self.path}:{key}: partial cell')
        return list(struct.unpack(f'>{len(raw)//4}I', raw))

    def strings(self, key):
        raw = self.props.get(key, b'')
        if not raw:
            return []
        if raw[-1] != 0:
            raise ValueError(f'{self.path}:{key}: missing string terminator')
        return raw[:-1].decode('utf-8').split('\0')

    def scalar(self, key, default=None):
        if key not in self.props:
            if default is not None:
                return default
            raise ValueError(f'{self.path}:{key}: missing')
        value = self.cells(key)
        if len(value) != 1:
            raise ValueError(f'{self.path}:{key}: expected one cell')
        return value[0]


class Fdt:
    def __init__(self, raw):
        if len(raw)<40 or len(raw)>32*1024*1024:
            raise ValueError('DTB size out of bounds')
        magic, total, off, strings, reserve, version, last, _, ns, nb = struct.unpack_from('>10I',raw)
        if magic != 0xd00dfeed or total>len(raw) or total<40 or version<17 or last>17:
            raise ValueError('invalid DTB header')
        spans = [(off,nb),(strings,ns)]
        if off%4 or reserve%8 or reserve<40 or any(a<40 or a>total or n>total-a for a,n in spans):
            raise ValueError('DTB block out of bounds')
        if off<strings+ns and strings<off+nb:
            raise ValueError('overlapping DTB blocks')
        reserve_end = min([a for a,_ in spans if a>=reserve]+[total])
        pos=reserve
        while pos+16<=reserve_end:
            address,size=struct.unpack_from('>QQ',raw,pos); pos+=16
            if not address and not size:
                break
        else:
            raise ValueError('unterminated DTB reservation map')
        if any(reserve<a+n and a<pos for a,n in spans):
            raise ValueError('overlapping DTB reservations')
        table=raw[strings:strings+ns]
        self.nodes, self.handles = {}, {}
        stack, pos, limit, ended = [], off, off+nb, False
        while pos+4<=limit:
            token=struct.unpack_from('>I',raw,pos)[0]; pos+=4
            if token==1:
                end=raw.find(b'\0',pos,limit)
                if end<0 or len(stack)>=64:
                    raise ValueError('invalid node name/depth')
                name=raw[pos:end].decode('utf-8'); pos=(end+4)&~3
                if '/' in name or (not stack and (name or self.nodes)) or (stack and not name):
                    raise ValueError('invalid DTB root/path')
                parent=stack[-1] if stack else None
                path=(parent.path.rstrip('/')+'/'+name) if parent else '/'
                if path in self.nodes:
                    raise ValueError('duplicate node')
                node=Node(path,parent); self.nodes[path]=node; stack.append(node)
            elif token==2:
                if not stack:
                    raise ValueError('unbalanced end node')
                stack.pop()
            elif token==3:
                if not stack or pos+8>limit:
                    raise ValueError('property outside node')
                length,index=struct.unpack_from('>II',raw,pos); pos+=8
                if index>=ns or length>limit-pos:
                    raise ValueError('property out of bounds')
                end=table.find(b'\0',index)
                if end<0:
                    raise ValueError('unterminated property name')
                key=table[index:end].decode('utf-8')
                if not key or key in stack[-1].props:
                    raise ValueError('duplicate/empty property')
                stack[-1].props[key]=raw[pos:pos+length]; pos=(pos+length+3)&~3
            elif token==4:
                pass
            elif token==9:
                if stack or '/' not in self.nodes:
                    raise ValueError('incomplete DTB tree')
                ended=True; break
            else:
                raise ValueError(f'unknown DTB token {token}')
        if not ended:
            raise ValueError('missing DTB end token')
        for node in self.nodes.values():
            keys=[node.scalar(k) for k in ('phandle','linux,phandle') if k in node.props]
            if keys and (len(set(keys))!=1 or keys[0] in (0,0xffffffff) or keys[0] in self.handles):
                raise ValueError('invalid/duplicate phandle')
            if keys:
                self.handles[keys[0]]=node

    def provider(self, handle):
        if handle not in self.handles:
            raise ValueError(f'unresolved phandle {handle:#x}')
        return self.handles[handle]

    def references(self, node, key, count_key, names_key=None):
        cells=node.cells(key); out=[]; pos=0
        names=node.strings(names_key) if names_key else []
        while pos<len(cells):
            provider=self.provider(cells[pos]); pos+=1
            count=provider.scalar(count_key)
            if count>16 or count>len(cells)-pos:
                raise ValueError(f'{node.path}:{key}: invalid provider argument count')
            entry={'provider':provider.path,'compatible':provider.strings('compatible'),
                   'args':cells[pos:pos+count],'provider_reg_cells':provider.cells('reg')}
            if names_key:
                if len(names)<=len(out):
                    raise ValueError(f'{node.path}:{names_key}: missing name')
                entry['name']=names[len(out)]
            out.append(entry); pos+=count
        if names_key and len(names)!=len(out):
            raise ValueError(f'{node.path}:{names_key}: extra name')
        return out

    @staticmethod
    def integer(cells):
        value=0
        for cell in cells:
            value=(value<<32)|cell
        return value

    def translate(self, bus, address, size):
        while bus.parent:
            if 'ranges' not in bus.props:
                raise ValueError(f'{bus.path}: missing ranges; physical address unknown')
            cells=bus.cells('ranges')
            if cells:
                na=bus.scalar('#address-cells',2); pa=bus.parent.scalar('#address-cells',2)
                ns=bus.scalar('#size-cells',1); width=na+pa+ns
                if not 1<=na<=2 or not 1<=pa<=2 or not 1<=ns<=2 or len(cells)%width:
                    raise ValueError('unsupported ranges format')
                matches=[]
                for i in range(0,len(cells),width):
                    child=self.integer(cells[i:i+na]); parent=self.integer(cells[i+na:i+na+pa])
                    length=self.integer(cells[i+na+pa:i+width])
                    if child<=address and address-child<=length and size<=length-(address-child):
                        matches.append(parent+address-child)
                if len(matches)!=1:
                    raise ValueError('unmapped/ambiguous bus address')
                address=matches[0]
            if address>0xffffffffffffffff or size>0x10000000000000000-address:
                raise ValueError('physical range overflow')
            bus=bus.parent
        return address

    def registers(self, node):
        if not node.parent:
            return []
        a=node.parent.scalar('#address-cells',2); s=node.parent.scalar('#size-cells',1)
        cells=node.cells('reg'); names=node.strings('reg-names')
        if not 1<=a<=2 or not 1<=s<=2 or len(cells)%(a+s):
            raise ValueError(f'{node.path}: unsupported MMIO reg format')
        result=[]
        for i in range(0,len(cells),a+s):
            bus=self.integer(cells[i:i+a]); size=self.integer(cells[i+a:i+a+s])
            if not size or size>0x10000000000000000-bus:
                raise ValueError('invalid MMIO extent')
            entry={'bus_address':hex(bus),'physical_address':hex(self.translate(node.parent,bus,size)),
                   'bytes':hex(size)}
            if names:
                if len(result)>=len(names):
                    raise ValueError('missing reg-name')
                entry['name']=names[len(result)]
            result.append(entry)
        if names and len(names)!=len(result):
            raise ValueError('extra reg-name')
        return result

    def interrupts(self, node):
        if 'interrupts-extended' in node.props:
            return self.references(node,'interrupts-extended','#interrupt-cells')
        cells=node.cells('interrupts')
        if not cells:
            return []
        ancestor=node
        while ancestor and 'interrupt-parent' not in ancestor.props:
            ancestor=ancestor.parent
        if not ancestor:
            raise ValueError('missing interrupt-parent')
        parent=self.provider(ancestor.scalar('interrupt-parent')); width=parent.scalar('#interrupt-cells')
        if not 1<=width<=8 or len(cells)%width:
            raise ValueError('invalid interrupts length')
        names=node.strings('interrupt-names')
        entries=[{'provider':parent.path,'compatible':parent.strings('compatible'),
                  'args':cells[i:i+width]} for i in range(0,len(cells),width)]
        if names:
            if len(names)!=len(entries):
                raise ValueError('interrupt-names mismatch')
            for entry,name in zip(entries,names):
                entry['name']=name
        return entries


def inspect(raw):
    tree=Fdt(raw)
    if tree.nodes['/'].strings('model')!=['MT6897']:
        raise ValueError('expected captured MT6897 model')
    selected={}
    for role, compatible in [('ufs','mediatek,mt8183-ufshci'),
                             ('ufs_phy','mediatek,mt8183-ufsphy'), ('gpu','mediatek,mali')]:
        matches=[n for n in tree.nodes.values() if compatible in n.strings('compatible')]
        if len(matches)!=1:
            raise ValueError(f'{role}: expected one matching node')
        node=matches[0]
        entry={'path':node.path,'compatible':node.strings('compatible'),
               'status':node.strings('status') or ['okay (implicit)'],
               'registers':tree.registers(node),'interrupts':tree.interrupts(node),
               'clocks':tree.references(node,'clocks','#clock-cells','clock-names'),
               'resets':tree.references(node,'resets','#reset-cells','reset-names'),
               'phys':tree.references(node,'phys','#phy-cells'),
               'iommus':tree.references(node,'iommus','#iommu-cells'),
               'dma_coherent_property_present':'dma-coherent' in node.props,
               'supplies':{},'flags':[key for key,value in node.props.items()
                                       if key.startswith('mediatek,') and not value]}
        for key,value in node.props.items():
            if key.endswith('-supply') or key in ('protected-memory-allocator','physical-memory-group-manager'):
                provider=tree.provider(node.scalar(key))
                entry['supplies'][key]={'provider':provider.path,'compatible':provider.strings('compatible')}
        entry['dma_contract']='unverified; absent iommus/dma-coherent properties do not prove bypass/coherency'
        selected[role]=entry
    return {'fdt_sha256':hashlib.sha256(raw).hexdigest(),'nodes':selected,
            'scope':'saved-DTB inspection only; no MMIO, firmware, DMA or device test'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('dtb',type=Path); ap.add_argument('output',type=Path)
    args=ap.parse_args()
    try:
        report=inspect(args.dtb.read_bytes())
        with args.output.open('x',encoding='utf-8') as out:
            out.write(json.dumps(report,indent=2)+'\n')
    except (ValueError,OSError,UnicodeError) as e:
        ap.exit(1,f'hardware inspection failed: {e}\n')
    print(json.dumps({'sha256':report['fdt_sha256'],
                      'nodes':{k:v['path'] for k,v in report['nodes'].items()}},indent=2))


if __name__=='__main__':
    main()
