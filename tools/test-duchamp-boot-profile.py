#!/usr/bin/env python3
"""Captured-data profile checks and malformed-input/output-preservation guards."""
import argparse,copy,json,subprocess,sys,tempfile,tomllib,unittest
from pathlib import Path
import duchamp_boot_profile as p
class Profiles(unittest.TestCase):
    raw=None;board=None;template=None;sources=None
    def setUp(self):self.tree=p.hardware.Fdt(self.raw);self.b=copy.deepcopy(self.board)
    def facts(self):return p.facts(self.tree,self.b)
    def test_real_selected_facts(self):
        f=self.facts();self.assertEqual((f['timer_hz'],f['virtual_timer_intid'],f['interrupt_cells']),(13000000,27,4))
        self.assertEqual((f['gicd'],f['gicd_bytes'],f['gicr'],f['gicr_bytes']),(0xc400000,0x40000,0xc440000,0x200000))
        self.assertEqual([c['mpidr'] for c in f['cpus']],[i<<8 for i in range(8)])
    def test_node_name_is_not_cpu_reg(self):
        self.assertEqual(self.facts()['cpus'][4]['mpidr'],0x400)
    def test_phone_qemu_separated(self):
        facts=self.facts();phone,fp=p.build(self.template,'phone',facts,b'x'*64);qemu,fq=p.build(self.template,'qemu',facts,b'x'*64)
        self.assertEqual((fp['timer_hz'],fq['timer_hz']),(13000000,62500000))
        self.assertEqual((fp['gicd'],fq['gicd']),(0xc400000,0x8000000));self.assertNotEqual(phone,qemu)
        for blob,emitted in [(phone,fp),(qemu,fq)]:
            self.assertNotIn(b'qcom,',blob);self.assertNotIn(b'sweet-ufs',blob)
            self.assertFalse(emitted['phone_execution_authorized']);self.assertFalse(emitted['physical_backend_enabled'])
            t,end=p.adt.parse(blob);self.assertEqual(end,len(blob));self.assertEqual(len(p.child(t,'cpus').children),1)
            fb=p.child(t,'sweet-fbcon');self.assertEqual(fb.prop('reg')[:8],p.u64(0xfcc2f000))
            self.assertEqual(fb.prop('width'),p.u32(1220));self.assertEqual(fb.prop('stride'),p.u32(4992))
    def test_unknown_core_bus_ddr_clocks_omitted(self):
        for target,hz in [('phone',13000000),('qemu',62500000)]:
            blob,_=p.build(self.template,target,self.facts(),b'x'*64);t,_=p.adt.parse(blob);cpu=p.child(p.child(t,'cpus'),'cpu0')
            for key in ['clock-frequency','bus-frequency','memory-frequency']:self.assertIsNone(cpu.prop(key))
            self.assertEqual(cpu.prop('timebase-frequency'),p.u32(hz))
    def test_console_above_diagnostic_marker_band(self):
        for target in ['phone','qemu']:
            f=self.facts();blob,emitted=p.build(self.template,target,f,b'x'*64);tree,_=p.adt.parse(blob)
            self.assertEqual(p.child(tree,'sweet-fbcon').prop('height'),p.u32(2680))
            display=p.child(p.child(tree,'arm-io'),'disp0')
            self.assertEqual(display.prop('canvas-height'),p.u32(2712))
            self.assertEqual(emitted['console_viewport']['rows'],83)
            self.assertLessEqual(83*32,f['framebuffer']['height']-32)
    def test_timer_flag_rejected(self):
        n=self.tree.nodes['/timer'];raw=bytearray(n.props['interrupts']);raw[11]=8;n.props['interrupts']=bytes(raw)
        with self.assertRaises(ValueError):self.facts()
    def test_partition_rejected(self):
        n=self.tree.nodes['/timer'];raw=bytearray(n.props['interrupts']);raw[15]=1;n.props['interrupts']=bytes(raw)
        with self.assertRaises(ValueError):self.facts()
    def test_timer_truncation_rejected(self):
        n=self.tree.nodes['/timer'];n.props['interrupts']=n.props['interrupts'][:-4]
        with self.assertRaises(ValueError):self.facts()
    def test_cpu_reg_mismatch(self):
        self.tree.nodes['/cpus/cpu@100'].props['reg']=b'\0\0\x03\0'
        with self.assertRaises(ValueError):self.facts()
    def test_board_clock_mismatch(self):
        self.b['timer']['frequency']='0x0124f800'
        with self.assertRaises(ValueError):self.facts()
    def test_gic_stride_requires_separate_support(self):
        self.tree.nodes['/interrupt-controller'].props['redistributor-stride']=b'\0\0\0\0\0\x04\0\0'
        with self.assertRaises(ValueError):self.facts()
    def test_framebuffer_disagreement(self):
        self.tree.nodes['/chosen'].props['atag,videolfb-fb_base_l']=b'\0'*4
        with self.assertRaises(ValueError):self.facts()
    def test_framebuffer_geometry_bounds(self):
        self.b['framebuffer']['stride']=1
        with self.assertRaises(ValueError):self.facts()
    def test_template_pin(self):
        with self.assertRaises(ValueError):p.build(self.template+b'\0','phone',self.facts())
    def test_explicit_target(self):
        with self.assertRaises(ValueError):p.build(self.template,'auto',self.facts())
    def test_seed_size(self):
        with self.assertRaises(ValueError):p.build(self.template,'phone',self.facts(),b'')
    def test_changed_source_pin(self):
        with tempfile.TemporaryDirectory() as scratch:
            root=Path(scratch);f=root/'drivers/irqchip/irq-gic-v3.c';f.parent.mkdir(parents=True);f.write_bytes(b'changed')
            with self.assertRaises(ValueError):p.sources(root)
            self.assertEqual(f.read_bytes(),b'changed')
    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as scratch:
            root=Path(scratch);sentinel=root/'user';sentinel.write_bytes(b'keep')
            tool=Path(__file__).with_name('build-duchamp-boot-profile.py')
            r=subprocess.run([sys.executable,str(tool),str(root),'--target','phone','--fdt','missing','--template','missing','--sources','missing'],capture_output=True,text=True)
            self.assertEqual(r.returncode,2);self.assertIn('preserve existing output',r.stderr);self.assertEqual(list(root.iterdir()),[sentinel])
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--fdt',type=Path,required=True)
    ap.add_argument('--template',type=Path,required=True);ap.add_argument('--sources',type=Path,required=True);a=ap.parse_args()
    Profiles.raw=a.fdt.read_bytes();assert p.sha(Profiles.raw)==p.FDT_SHA
    Profiles.template=a.template.read_bytes();assert p.sha(Profiles.template)==p.TEMPLATE_SHA
    Profiles.board=tomllib.loads((Path(__file__).resolve().parent.parent/'duchamp/board.toml').read_text())
    Profiles.sources=p.sources(a.sources);unittest.main(argv=[sys.argv[0]])
