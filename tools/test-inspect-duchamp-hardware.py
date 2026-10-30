#!/usr/bin/env python3
"""Synthetic malformed-tree and dependency-resolution tests; no phone DTB needed."""
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import unittest

path=Path(__file__).with_name('inspect-duchamp-hardware.py')
spec=importlib.util.spec_from_file_location('duchamp_hardware',path)
module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)

DTS='''/dts-v1/;
/ {
 model = "MT6897"; #address-cells = <2>; #size-cells = <2>;
 interrupt-parent = <&gic>;
 chosen { bootargs = "PRIVATE-BOOTARGS"; serial-number = "PRIVATE-SERIAL"; };
 gic: interrupt-controller { compatible = "arm,gic-v3"; #interrupt-cells = <4>; interrupt-controller; };
 clk: clock { #clock-cells = <1>; };
 rst: reset { #reset-cells = <1>; };
 soc { #address-cells = <2>; #size-cells = <2>; ranges;
  phy: phy@12000 { compatible = "mediatek,mt8183-ufsphy";
   reg = <0 0x12000 0 0x1000>; #phy-cells = <0>; };
  ufshci@14000 { compatible = "mediatek,mt8183-ufshci"; reg = <0 0x14000 0 0x1000>;
   phys = <&phy>; clocks = <&clk 42 &clk 118>; clock-names = "mux", "source";
   resets = <&rst 0>; reset-names = "hci"; interrupts = <0 168 4 0>; };
  mali@20000 { compatible = "mediatek,mali", "arm,mali-valhall";
   reg = <0 0x20000 0 0x1000>; interrupts = <0 585 4 0>; interrupt-names = "MMU"; };
 };
};'''


class HardwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=subprocess.run(['dtc','-q','-I','dts','-O','dtb'],input=DTS.encode(),
                               check=True,capture_output=True).stdout

    def tree(self):
        return module.Fdt(self.raw)

    def mutate_header(self,index,value):
        raw=bytearray(self.raw); struct.pack_into('>I',raw,index*4,value); return raw

    def test_hardware_and_privacy(self):
        import json
        result=module.inspect(self.raw)
        ufs=result['nodes']['ufs']
        self.assertEqual(ufs['registers'][0]['physical_address'],'0x14000')
        self.assertEqual([x['args'] for x in ufs['clocks']],[[42],[118]])
        self.assertEqual(ufs['resets'][0]['name'],'hci')
        self.assertEqual(ufs['phys'][0]['args'],[])
        self.assertEqual(ufs['interrupts'][0]['args'],[0,168,4,0])
        self.assertEqual(ufs['iommus'],[])
        self.assertIn('unverified',ufs['dma_contract'])
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_all_truncations_rejected(self):
        for length in range(len(self.raw)):
            with self.subTest(length=length),self.assertRaises(ValueError):
                module.Fdt(self.raw[:length])

    def test_invalid_headers(self):
        for index,value in [(0,0),(1,39),(1,len(self.raw)+1),(2,41),(2,0xffffffff),
                            (3,0xffffffff),(4,41),(5,16),(6,18),(8,0xffffffff),(9,0xffffffff)]:
            with self.subTest(field=index),self.assertRaises(ValueError):
                module.Fdt(self.mutate_header(index,value))

    def test_blocks_overlap(self):
        off=struct.unpack_from('>I',self.raw,8)[0]
        with self.assertRaises(ValueError): module.Fdt(self.mutate_header(3,off))

    def test_unknown_token(self):
        raw=bytearray(self.raw); off=struct.unpack_from('>I',raw,8)[0]
        struct.pack_into('>I',raw,off,0xabcdef)
        with self.assertRaises(ValueError): module.Fdt(raw)

    def test_unresolved_reference(self):
        tree=self.tree(); node=tree.nodes['/soc/ufshci@14000']
        node.props['clocks']=struct.pack('>II',0xabc,1)
        with self.assertRaises(ValueError): tree.references(node,'clocks','#clock-cells','clock-names')

    def test_partial_cell(self):
        tree=self.tree(); node=tree.nodes['/soc/ufshci@14000']; node.props['reg']=b'\0'
        with self.assertRaises(ValueError): tree.registers(node)

    def test_missing_clock_name(self):
        tree=self.tree(); node=tree.nodes['/soc/ufshci@14000']; node.props['clock-names']=b'mux\0'
        with self.assertRaises(ValueError): tree.references(node,'clocks','#clock-cells','clock-names')

    def test_extra_clock_name(self):
        tree=self.tree(); node=tree.nodes['/soc/ufshci@14000']; node.props['clock-names']+=b'extra\0'
        with self.assertRaises(ValueError): tree.references(node,'clocks','#clock-cells','clock-names')

    def test_missing_provider_cells(self):
        tree=self.tree(); del tree.nodes['/clock'].props['#clock-cells']
        with self.assertRaises(ValueError): tree.references(tree.nodes['/soc/ufshci@14000'],'clocks','#clock-cells')

    def test_truncated_provider_args(self):
        tree=self.tree(); node=tree.nodes['/soc/ufshci@14000']; node.props['clocks']=node.props['clocks'][:-4]
        with self.assertRaises(ValueError): tree.references(node,'clocks','#clock-cells')

    def test_no_ranges_is_not_identity(self):
        tree=self.tree(); del tree.nodes['/soc'].props['ranges']
        with self.assertRaises(ValueError): tree.registers(tree.nodes['/soc/mali@20000'])

    def test_nonidentity_ranges(self):
        tree=self.tree(); tree.nodes['/soc'].props['ranges']=struct.pack('>6I',0,0,1,0,0,0x100000)
        result=tree.registers(tree.nodes['/soc/mali@20000'])
        self.assertEqual(result[0]['physical_address'],'0x100020000')

    def test_unmapped_ranges(self):
        tree=self.tree(); tree.nodes['/soc'].props['ranges']=struct.pack('>6I',0,0,0,0,0,0x1000)
        with self.assertRaises(ValueError): tree.registers(tree.nodes['/soc/mali@20000'])

    def test_ambiguous_ranges(self):
        tree=self.tree(); tree.nodes['/soc'].props['ranges']=struct.pack('>6I',0,0,0,0,0,0x100000)*2
        with self.assertRaises(ValueError): tree.registers(tree.nodes['/soc/mali@20000'])

    def test_bad_interrupts(self):
        tree=self.tree(); node=tree.nodes['/soc/mali@20000']; node.props['interrupts']=node.props['interrupts'][:-4]
        with self.assertRaises(ValueError): tree.interrupts(node)

    def test_bad_interrupt_names(self):
        tree=self.tree(); node=tree.nodes['/soc/mali@20000']; node.props['interrupt-names']+=b'extra\0'
        with self.assertRaises(ValueError): tree.interrupts(node)

    def test_unterminated_string(self):
        tree=self.tree(); node=tree.nodes['/']; node.props['model']=b'MT6897'
        with self.assertRaises(ValueError): node.strings('model')

    def test_reg_overflow(self):
        tree=self.tree(); node=tree.nodes['/soc/mali@20000']; node.props['reg']=struct.pack('>4I',0xffffffff,0xffffffff,0,2)
        with self.assertRaises(ValueError): tree.registers(node)

    def test_reg_names_mismatch(self):
        tree=self.tree(); node=tree.nodes['/soc/mali@20000']; node.props['reg-names']=b'a\0b\0'
        with self.assertRaises(ValueError): tree.registers(node)


if __name__=='__main__':
    unittest.main()
