#!/usr/bin/env python3
"""0BSD offline tests; synthetic unit pixels are never runtime frame evidence."""
import ast
from pathlib import Path
import unittest
from duchamp_dwarf_layout import parse,layout
from duchamp_render_proof import eligible,matching_pixels

def passive(source):
    code=source.split('python\n',1)[1].rsplit('\nend',1)[0]
    tree=ast.parse(code)
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):
            if n.func.attr=='write_memory':raise ValueError('guest memory write')
            if isinstance(n.func.value,ast.Name) and n.func.value.id=='gdb' and n.func.attr=='execute':
                if not n.args or not isinstance(n.args[0],ast.Constant) or n.args[0].value not in ('continue','detach'):
                    raise ValueError('nonpassive GDB command')
    if 'type=gdb.BP_HARDWARE_BREAKPOINT' not in code:raise ValueError('hardware breakpoint policy missing')

class ObserverTests(unittest.TestCase):
    def test_current_observer_passive_commands(self):passive(Path('tools/duchamp-render-passive.gdb').read_text())
    def test_register_rewrite_denied(self):
        with self.assertRaises(ValueError):passive("python\ngdb.execute('set $x0=0')\n# type=gdb.BP_HARDWARE_BREAKPOINT\nend")
    def test_memory_rewrite_denied(self):
        with self.assertRaises(ValueError):passive("python\ngdb.selected_inferior().write_memory(1,b'X')\n# type=gdb.BP_HARDWARE_BREAKPOINT\nend")
    def test_dynamic_commands_denied(self):
        with self.assertRaises(ValueError):passive("python\ngdb.execute(command)\n# type=gdb.BP_HARDWARE_BREAKPOINT\nend")
    def test_missing_hardware_policy(self):
        with self.assertRaises(ValueError):passive('python\ngdb.execute(\'continue\')\nend')
    def test_unknown_dwarf_type(self):
        with self.assertRaises(ValueError):layout({},'not-a-type')
    def test_ambiguous_dwarf_type(self):
        r={1:dict(id=1,tag='DW_TAG_structure_type',attrs=dict(name='T',byte_size=8),children=[]),
           2:dict(id=2,tag='DW_TAG_structure_type',attrs=dict(name='T',byte_size=8),children=[])}
        with self.assertRaises(ValueError):layout(r,'T')
    def test_member_outside_record(self):
        r={1:dict(id=1,tag='DW_TAG_structure_type',attrs=dict(name='T',byte_size=8),children=[2]),
           2:dict(id=2,tag='DW_TAG_member',attrs=dict(name='x',data_member_location=16),children=[])}
        with self.assertRaises(ValueError):layout(r,'T')

class ProofTests(unittest.TestCase):
    def setUp(self):
        self.events=[dict(kind='original_main',name='SpringBoard',pid=34,birth=90,uuid='40EC75F076C13DEB85F139369B09E9D5'),
            dict(kind='context_commit',name='SpringBoard',pid=34,birth=90),
            dict(kind='surface_method_return',name='SpringBoard',pid=34,birth=90,selector=0,result=0,surface_id=2)]
        self.events.append(dict(kind='surface_method',name='SpringBoard',pid=34,birth=90,selector=0,caller_task_matches=True))
        self.owner=dict(name='SpringBoard',pid=34,birth=90)
        self.s=dict(width=2,height=2,bytesPerRow=8,offset=0,pixelFormat=0x42475241,allocSize=16)
        self.d=dict(fWidth=2,fHeight=2,fRowBytes=8,fOffX=0,fOffY=0)
    def test_unit_positive_is_not_runtime_evidence(self):
        self.assertTrue(eligible(self.events,self.owner,2));self.assertTrue(matching_pixels(bytes(16),bytes(16),self.s,self.d,[0,0,2,2],[0,0,2,2]))
    def test_pixels_alone_do_not_prove_producer(self):self.assertFalse(eligible([],self.owner,2))
    def test_backboard_surface_not_springboard_proof(self):self.assertFalse(eligible(self.events,{**self.owner,'name':'backboardd'},2))
    def test_reused_pid_birth_mismatch(self):self.assertFalse(eligible(self.events,{**self.owner,'birth':91},2))
    def test_missing_transaction(self):self.assertFalse(eligible(self.events[:1]+self.events[2:],self.owner,2))
    def test_wrong_surface_id(self):self.assertFalse(eligible(self.events,self.owner,3))
    def test_failed_creation(self):
        self.events[2]['result']=1;self.assertFalse(eligible(self.events,self.owner,2))
    def test_truncated_backing(self):self.assertFalse(matching_pixels(bytes(15),bytes(16),self.s,self.d,[0,0,2,2],[0,0,2,2]))
    def test_wrong_pixel_format(self):self.assertFalse(matching_pixels(bytes(16),bytes(16),{**self.s,'pixelFormat':1},self.d,[0,0,2,2],[0,0,2,2]))
    def test_pitch_and_frame_bounds(self):self.assertFalse(matching_pixels(bytes(16),bytes(16),{**self.s,'bytesPerRow':4},self.d,[0,0,2,2],[0,0,2,2]))
    def test_modified_scanout(self):self.assertFalse(matching_pixels(bytes(16),b'X'+bytes(15),self.s,self.d,[0,0,2,2],[0,0,2,2]))
    def test_wrong_binary_uuid(self):
        self.events[0]['uuid']='0'*32;self.assertFalse(eligible(self.events,self.owner,2))
    def test_negative_offset(self):self.assertFalse(matching_pixels(bytes(16),bytes(16),{**self.s,'offset':-1},self.d,[0,0,2,2],[0,0,2,2]))
    def test_wrong_client_task(self):
        self.events[-1]['caller_task_matches']=False;self.assertFalse(eligible(self.events,self.owner,2))

if __name__=='__main__':unittest.main()
