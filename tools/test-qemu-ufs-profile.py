#!/usr/bin/env python3
"""Virtual-UFS profile rejection tests using synthetic ADT/image inputs."""
from copy import deepcopy
from pathlib import Path
import struct
import tempfile
import unittest
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

    def test_payload_bounds(self):
        p=bytearray(self.payload()); struct.pack_into('<Q',p,0x20,len(p)+1)
        with self.assertRaises(ValueError): profile.runner_options(p,self.image,'cortex-a76','duchamp')


if __name__=='__main__': unittest.main()
