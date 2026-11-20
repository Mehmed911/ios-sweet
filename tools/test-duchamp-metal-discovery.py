#!/usr/bin/env python3
"""0BSD synthetic trace/bounds tests; never substitute these for a VM run."""
import copy,importlib.util,tempfile,unittest
from pathlib import Path
from duchamp_metal_discovery import classify,BACKBOARD_UUID
import duchamp_cache_code as cache
class Discovery(unittest.TestCase):
 def setUp(self):
  who=dict(pid=25,birth=90,name='backboardd',tid=274)
  data=[dict(kind='original_main',uuid=BACKBOARD_UUID),dict(kind='original_image_bound',uuid=BACKBOARD_UUID),dict(kind='mtl_register_entry'),
   dict(kind='mtl_master_return',arguments=[0],master_port=44),dict(kind='io_matching_return',result=8192,request=dict(class_name='IOAcceleratorES')),
   dict(kind='mtl_services_return',arguments=[0],iterator=77),dict(kind='io_iterator_next_return',result=0,request=dict(class_name='IOAcceleratorES',arguments=[77]))]
  self.rows=[dict(who,sequence=i+1,**row) for i,row in enumerate(data)]
 def test_complete_empty_iterator(self):self.assertEqual(classify(self.rows)['interface'],'IOIteratorNext')
 def test_null_iterator_is_first_empty_output(self):
  self.rows[5]['iterator']=0;self.rows[-1]['request']['arguments'][0]=0
  r=classify(self.rows)
  self.assertEqual(r['interface'],'IOServiceGetMatchingServices');self.assertEqual(r['return_value'],0)
  self.assertEqual(r['subsequent_iterator_next'],0)
 def test_nil_metal_alone_insufficient(self):self.assertEqual(classify([dict(kind='metal_default_device_return',arguments=[0])])['status'],'INSUFFICIENT_TRACE')
 def test_wrong_uuid(self):
  self.rows[0]['uuid']='0'*32;self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
 def test_reused_pid(self):
  self.rows[2]['birth']=91;self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
 def test_other_thread(self):
  self.rows[-1]['tid']=275;self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
 def test_wrong_iterator(self):
  self.rows[-1]['request']['arguments'][0]=78;self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
 def test_wrong_class(self):
  self.rows[4]['request']['class_name']='IOSurfaceRoot';self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
 def test_master_error_first(self):
  self.rows[3]['arguments'][0]=5;self.assertEqual(classify(self.rows)['interface'],'IOMasterPort')
 def test_matching_error_first(self):
  self.rows[5]['arguments'][0]=0xe00002c0;self.assertEqual(classify(self.rows)['interface'],'IOServiceGetMatchingServices')
 def test_incomplete_trace(self):self.assertEqual(classify(self.rows[:-1])['status'],'INSUFFICIENT_TRACE')
 def test_trace_error(self):
  self.rows.append(dict(kind='trace_error'));self.assertEqual(classify(self.rows)['status'],'TRACE_ERROR')
 def test_fixed_callsite_contract_requires_cache_binding(self):
  self.rows[4]=dict(self.rows[4],kind='mtl_match_dict_return',arguments=[8192])
  self.rows[-1]=dict(self.rows[-1],kind='mtl_iterator_return',arguments=[0])
  self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
  self.rows[1]['cache_uuid']='E5420DB330D033AA8B7E05B5038BB46D'
  self.rows.insert(2,dict(self.rows[1],kind='cache_bound',sequence=2))
  for i,r in enumerate(self.rows):r['sequence']=i+1
  self.assertEqual(classify(self.rows)['interface'],'IOIteratorNext')
 def test_reordered_trace_denied(self):
  self.rows[3],self.rows[4]=self.rows[4],self.rows[3]
  self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
 def test_duplicate_sequence_denied(self):
  self.rows[-1]['sequence']=self.rows[-2]['sequence']
  self.assertEqual(classify(self.rows)['status'],'INSUFFICIENT_TRACE')
 def test_null_dictionary(self):
  self.rows[4]['result']=0
  self.assertEqual(classify(self.rows)['interface'],'IOServiceMatching')
 def test_no_frame_claim(self):self.assertFalse(classify(self.rows)['first_frame_verified'])
class CacheBounds(unittest.TestCase):
 def test_bad_intervals(self):
  for va,n in [(-1,4),(0,0),(0,-1),(0,(1<<20)+1),((1<<64)-1,4)]:
   with self.assertRaises(ValueError):cache.read(va,n)
 def test_hole(self):
  with self.assertRaises(ValueError):cache.read(0x10,4)
 def test_actual_pinned_instruction(self):self.assertEqual(cache.read(0x181b11688,4).hex(),'40020034')
if __name__=='__main__':unittest.main()
