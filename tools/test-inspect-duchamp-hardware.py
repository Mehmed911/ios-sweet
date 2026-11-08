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

PERIPHERALS = '''
&{/} {
    chosen_touch: touch-selector { compatible = "xiaomi-touch"; panel = <&panel>; };
    gpio: gpio-controller {
        compatible = "mediatek,mt6897-pinctrl";
        interrupt-controller; #interrupt-cells = <2>; gpio-controller; #gpio-cells = <2>;
    };
    radio_memory: wifi-pool { compatible = "shared-dma-pool"; };
    wifi@18000000 {
        compatible = "mediatek,wifi"; reg = <0 0x18000000 0 0x700000>;
        memory-region = <&radio_memory>;
    };
    bt@18010000 { compatible = "mediatek,bt"; reg = <0 0x18010000 0 0x1000>; };
    conn@18020000 { compatible = "mediatek,mt6897-consys-atf"; reg = <0 0x18020000 0 0x1000>; };
    audio@11050000 { compatible = "mediatek,mt6897-sound"; reg = <0 0x11050000 0 0x9000>; };
    codec { compatible = "mediatek,mt6368-sound"; };
};
&{/soc} {
    spi@11010000 { compatible = "mediatek,mt6985-spi"; reg = <0 0x11010000 0 0x100>; };
    spi@11012000 {
        compatible = "mediatek,mt6985-spi"; reg = <0 0x11012000 0 0x100>;
        #address-cells = <1>; #size-cells = <0>;
        touch@0 {
            compatible = "focaltech,n11a-3683g-spi"; reg = <0>;
            interrupt-parent = <&gpio>; interrupts = <9 8200>;
            focaltech,reset-gpio = <&gpio 60 0>; focaltech,irq-gpio = <&gpio 9 8200>;
            spi-max-frequency = <15000000>; focaltech,max-touch-number = <10>;
            focaltech,super-resolution-factors = <16>; focaltech,display-coords = <0 0 19520 43392>;
        };
    };
    dsi@1400d000 {
        compatible = "mediatek,mt6897-dsi"; reg = <0 0x1400d000 0 0x1000>;
        #address-cells = <1>; #size-cells = <0>;
        panel: panel@0 { compatible = "test,panel"; reg = <0>; };
    };
    dsi@1420d000 { compatible = "mediatek,mt6897-dsi"; reg = <0 0x1420d000 0 0x1000>; status = "disabled"; };
    usb@11201000 {
        compatible = "mediatek,mtu3"; reg = <0 0x11201000 0 0x2e00>;
        #address-cells = <2>; #size-cells = <2>; ranges;
        xhci@11200000 { compatible = "mediatek,mtk-xhci"; reg = <0 0x11200000 0 0x1000>; };
    };
    i2c@11cc0000 {
        compatible = "mediatek,mt6897-i2c"; reg = <0 0x11cc0000 0 0x1000>;
        #address-cells = <1>; #size-cells = <0>;
        sensor@10 { compatible = "mediatek,imgsensor"; reg = <0x10>; };
    };
    dpmaif@10014000 { compatible = "mediatek,dpmaif"; reg = <0 0x10014000 0 0x1000>; };
    ccif@10209000 { compatible = "mediatek,ccci_ccif"; reg = <0 0x10209000 0 0x1000>; };
};
'''


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
        self.assertNotIn('peripherals', result)

    def test_peripheral_bus_addresses_and_dependencies(self):
        raw = subprocess.run(['dtc', '-q', '-I', 'dts', '-O', 'dtb'],
                             input=(DTS + PERIPHERALS).encode(), check=True, capture_output=True).stdout
        result = module.inspect(raw, peripherals=True)['peripherals']
        self.assertEqual(result['touch']['bus_address'], 0)
        self.assertNotIn('registers', result['touch'])
        self.assertEqual(result['touch']['interrupts'][0]['args'], [9, 8200])
        self.assertEqual(result['touch']['gpios']['focaltech,reset-gpio'][0]['args'], [60, 0])
        self.assertEqual(result['touch_spi']['registers'][0]['physical_address'], '0x11012000')
        self.assertEqual(result['display_dsi']['path'], '/soc/dsi@1400d000')
        self.assertEqual(result['display_panels'][0]['bus_address'], 0)
        self.assertEqual(result['usb_host']['registers'][0]['physical_address'], '0x11200000')
        self.assertEqual(result['wifi']['memory_regions'], ['/wifi-pool'])
        self.assertEqual(result['cameras'][0]['bus_address'], 0x10)
        self.assertNotIn('registers', result['cameras'][0])
        self.assertEqual(result['camera_i2c'][0]['registers'][0]['physical_address'], '0x11cc0000')
        self.assertEqual(result['audio']['codec']['path'], '/codec')

    def test_peripherals_reject_missing_required_node(self):
        with self.assertRaisesRegex(ValueError, 'focaltech,n11a-3683g-spi'):
            module.inspect(self.raw, peripherals=True)

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
