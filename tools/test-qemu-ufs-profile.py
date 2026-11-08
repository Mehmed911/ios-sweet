#!/usr/bin/env python3
"""Virtual-UFS profile rejection tests using synthetic ADT/image inputs."""
from copy import deepcopy
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import hashlib
import adt
import qemu_ufs as profile


def node(name,props=(),children=()):
    n=adt.Node(); n.props=[('name',0,name.encode()+b'\0')]+[(k,0,v) for k,v in props]
    n.children=list(children); return n


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='qufs-profile-')
        self.image=Path(self.tmp.name)/'test.hfs'
        raw=bytearray(1024*1024); raw[1024:1026]=b'H+'; self.image.write_bytes(raw)
        self.base=node('root',children=[node('chosen',[
            ('dram-base',struct.pack('<Q',0x1c0000000)),('dram-size',struct.pack('<Q',0x20000000)),
            ('firmware-version',b'baseline\0')],[node('memory-map')]),
            node('arm-io',[('ranges',struct.pack('<3Q',0,0x1000000,0xff000000))],[node('gic',[
                ('reg',struct.pack('<4Q',0x07000000,0x10000,0x070a0000,0x100000)),
                ('virtual-timer-intid',struct.pack('<I',27))])])])
        self.tree,_=adt.parse(profile.build_tree(adt.serialize(self.base)))

    def tearDown(self): self.tmp.cleanup()

    def payload(self,tree=None,args='rd=qufs0 sweet-qemu-ufs=1 rootrw=0'):
        raw=adt.serialize(self.tree if tree is None else tree)
        data=bytearray(0x300+len(raw)); struct.pack_into('<2Q',data,0x20,0x300,len(raw))
        text=args.encode(); data[0x48:0x48+len(text)]=text; data[0x300:]=raw
        return bytes(data)

    def reject(self,tree=None,args='rd=qufs0 sweet-qemu-ufs=1 rootrw=0',cpu='cortex-a76',fb='duchamp'):
        with self.assertRaises(ValueError):
            profile.runner_options(self.payload(tree,args),self.image,cpu,fb)

    def setprop(self,tree,node_name,key,value):
        target=profile.child(tree,node_name)
        target.props=[(n,f,v) for n,f,v in target.props if n!=key]+[(key,0,value)]

    def test_valid_readonly_profile(self):
        options,meta=profile.runner_options(self.payload(),self.image,'cortex-a76','duchamp')
        self.assertIn('readonly=on',options[1]); self.assertTrue(meta['no_ramdisk'])
        self.assertTrue(meta['readonly']); self.assertEqual(meta['slot'],4)
        self.assertEqual(self.base.children[0].prop('firmware-version'),b'baseline\0')

    def test_writable_root(self): self.reject(args='rd=qufs0 sweet-qemu-ufs=1 rootrw=1')
    def test_writable_ufs(self): self.reject(args='rd=qufs0 sweet-qemu-ufs=1 ufsrw=1')
    def test_other_root(self): self.reject(args='rd=md0 sweet-qemu-ufs=1')
    def test_duplicate_root(self): self.reject(args='rd=qufs0 rd=md0 sweet-qemu-ufs=1')
    def test_duplicate_gate(self): self.reject(args='rd=qufs0 sweet-qemu-ufs=1 sweet-qemu-ufs=0')
    def test_missing_gate(self): self.reject(args='rd=qufs0')
    def test_other_cpu(self): self.reject(cpu='cortex-a715')
    def test_other_framebuffer(self): self.reject(fb='sweet')

    def test_physical_firmware(self):
        self.setprop(self.tree,'chosen','firmware-version',b'phone\0'); self.reject()

    def test_bad_bar(self):
        self.setprop(self.tree,'duchamp-qemu-ufs','reg',struct.pack('<2Q',0x112b0000,0x3000)); self.reject()

    def test_bad_ecam(self):
        self.setprop(self.tree,'duchamp-qemu-ufs','ecam',struct.pack('<2Q',0,0x1000)); self.reject()

    def test_bad_ram_window(self):
        self.setprop(self.tree,'chosen','dram-base',struct.pack('<Q',0x80000000)); self.reject()

    def test_ramdisk_forbidden(self):
        m=profile.child(profile.child(self.tree,'chosen'),'memory-map')
        m.props.append(('RAMDisk',0,struct.pack('<2Q',0x1c1000000,0x1000))); self.reject()

    def data_payload(self, args='rd=qufs0 sweet-qemu-ufs=1 rootrw=0'):
        base, size = 0x1c0000000, 1 << 20
        virt_base = 0xfffffe0007000000
        data_va = virt_base + 0x4000
        table_end = profile.SEG_TABLE + 2 * 32
        data_offset = table_end + 16
        tree = deepcopy(self.tree)
        mmap = profile.child(profile.child(tree, 'chosen'), 'memory-map')
        mmap.props.append(('RAMDisk', 0, struct.pack('<2Q', base + 0x4000, size)))
        raw_adt = adt.serialize(tree)
        adt_offset = data_offset + size
        data = bytearray(adt_offset + len(raw_adt))
        struct.pack_into('<8sII7Q', data, 0, b'SWEETXNU', 1, 2, virt_base, virt_base,
                         adt_offset, len(raw_adt), data_va + size, base, 0x20000000)
        text = args.encode()
        data[0x48:0x48 + len(text)] = text
        struct.pack_into('<8Q', data, profile.SEG_TABLE, virt_base, 0x4000, table_end, 16,
                         data_va, size, data_offset, size)
        data[data_offset + 1024:data_offset + 1026] = b'H+'
        data[adt_offset:] = raw_adt
        return data, data_offset

    def test_var_ramdisk_requires_opt_in(self):
        payload, _ = self.data_payload()
        with self.assertRaisesRegex(ValueError, 'fallback RAMDisk'):
            profile.runner_options(payload, self.image, 'cortex-a76', 'duchamp')

    def test_var_ramdisk_keeps_ufs_readonly(self):
        payload, offset = self.data_payload()
        options, meta = profile.runner_options(payload, self.image, 'cortex-a76', 'duchamp',
                                                var_ramdisk=True)
        self.assertIn('readonly=on', options[1])
        self.assertTrue(meta['readonly'])
        self.assertFalse(meta['no_ramdisk'])
        self.assertEqual(meta['data_ramdisk']['sha256'],
                         hashlib.sha256(payload[offset:offset + (1 << 20)]).hexdigest())

    def test_var_ramdisk_rejects_implicit_and_alternate_root(self):
        for args in ('rd=qufs0 sweet-qemu-ufs=1', 'rd=md0 sweet-qemu-ufs=1 rootrw=0',
                     'rd=qufs0 sweet-qemu-ufs=1 rootrw=1',
                     'rd=qufs0 sweet-qemu-ufs=1 rootrw=0 pmd0=0x80000000.0x1000'):
            with self.subTest(args=args), self.assertRaises(ValueError):
                payload, _ = self.data_payload(args)
                profile.runner_options(payload, self.image, 'cortex-a76', 'duchamp', var_ramdisk=True)

    def test_var_ramdisk_rejects_overlap_and_non_hfs_payload(self):
        payload, offset = self.data_payload()
        payload[offset + 1024:offset + 1026] = b'XX'
        with self.assertRaisesRegex(ValueError, 'complete HFS'):
            profile.runner_options(payload, self.image, 'cortex-a76', 'duchamp', var_ramdisk=True)
        payload, _ = self.data_payload()
        struct.pack_into('<Q', payload, profile.SEG_TABLE + 8, 0x8000)
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            profile.runner_options(payload, self.image, 'cortex-a76', 'duchamp', var_ramdisk=True)

    def test_qualcomm_node_forbidden(self):
        self.tree.children.append(node('sweet-ufs')); self.reject()

    def test_physical_gic_forbidden(self):
        gic=profile.child(profile.child(self.tree,'arm-io'),'gic')
        gic.props=[(k,f,struct.pack('<4Q',0xb400000,0x10000,0xb440000,0x200000) if k=='reg' else v)
                   for k,f,v in gic.props]; self.reject()

    def test_duplicate_node(self):
        self.tree.children.append(deepcopy(profile.child(self.tree,'duchamp-qemu-ufs'))); self.reject()

    def test_bad_image(self):
        self.image.write_bytes(b'no volume'); self.reject()

    def test_image_hashing_does_not_read_whole_image(self):
        expected=hashlib.sha256(self.image.read_bytes()).hexdigest()
        with patch.object(Path,'read_bytes',side_effect=AssertionError('unbounded image read')):
            _,meta=profile.runner_options(self.payload(),self.image,'cortex-a76','duchamp')
        self.assertEqual(meta['sha256'],expected)
        self.assertEqual(meta['image_bytes'],1024*1024)

    def test_payload_bounds(self):
        p=bytearray(self.payload()); struct.pack_into('<Q',p,0x20,len(p)+1)
        with self.assertRaises(ValueError): profile.runner_options(p,self.image,'cortex-a76','duchamp')


if __name__=='__main__': unittest.main()
