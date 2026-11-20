#!/usr/bin/env python3
"""0BSD closure regression cases; these never claim runtime compatibility."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('closure20',Path(__file__).with_name('audit-duchamp-20f66-closure.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def record(name,dependencies=(),minimum='16.5'):
    return {'header':{'cpu':'AARCH64','subcpu':'ARM64'},'loads':[
        {'load_cmd':'LC_ID_DYLIB','name':name},
        {'load_cmd':'LC_BUILD_VERSION','platform':'iOS','min_os':minimum}]+
        [{'load_cmd':'LC_LOAD_DYLIB','name':d} for d in dependencies]}


class ClosureTests(unittest.TestCase):
    def run_closure(self,images):
        return audit.closure('/app',{'dependencies':[{'path':'/A','weak':False}]},images)

    def test_recursive_cycle(self):
        r=self.run_closure(audit.cache_index([record('/A',['/B']),record('/B',['/A'])]))
        self.assertTrue(r['strong_metadata_closure_complete']);self.assertEqual(len(r['nodes']),3)
        self.assertFalse(r['runtime_abi_compatibility_proven'])

    def test_transitive_missing(self):
        r=self.run_closure({'/A':record('/A',['/missing'])})
        self.assertEqual(r['unresolved']['/missing']['classification'],'MISSING')

    def test_arm64e(self):
        r=record('/A');r['header']['subcpu']='ARM64E'
        self.assertEqual(self.run_closure({'/A':r})['unresolved']['/A']['classification'],'ARCHITECTURE_MISMATCH')

    def test_wrong_cpu(self):
        r=record('/A');r['header']['cpu']='AMD64'
        self.assertFalse(self.run_closure({'/A':r})['strong_metadata_closure_complete'])

    def test_earlier_deployment_target(self):
        self.assertTrue(self.run_closure({'/A':record('/A',minimum='15.4')})['strong_metadata_closure_complete'])

    def test_future_target(self):
        self.assertFalse(self.run_closure({'/A':record('/A',minimum='17')})['strong_metadata_closure_complete'])

    def test_other_platform(self):
        r=record('/A');r['loads'][1]['platform']='macOS'
        self.assertFalse(self.run_closure({'/A':r})['strong_metadata_closure_complete'])

    def test_unknown_runpath(self):
        r=self.run_closure({'/A':record('/A',['@rpath/B'])})
        self.assertEqual(r['unresolved']['@rpath/B']['classification'],'UNKNOWN')

    def test_optional_dependency(self):
        r=record('/A');r['loads'].append({'load_cmd':'LC_LOAD_WEAK_DYLIB','name':'/optional'})
        result=self.run_closure({'/A':r});self.assertTrue(result['strong_metadata_closure_complete'])
        self.assertTrue(result['edges'][-1]['weak'])

    def test_duplicate_identity(self):
        r=record('/A')
        with self.assertRaises(ValueError):audit.cache_index([r,copy.deepcopy(r)])

    def test_absent_identity(self):
        r=record('/A');r['loads'].pop(0)
        with self.assertRaises(ValueError):audit.cache_index([r])

    def test_original_dyld_identity(self):
        r=record('/usr/lib/dyld');r['loads'][0]['load_cmd']='LC_ID_DYLINKER'
        self.assertIn('/usr/lib/dyld',audit.cache_index([r]))

    def test_standalone_interpreter_is_required(self):
        root={'dependencies':[],'dylinker':'/usr/lib/dyld'}
        self.assertFalse(audit.closure('/app',root,{})['strong_metadata_closure_complete'])
        r=audit.closure('/app',root,{}, {'/usr/lib/dyld':{'dependencies':[]}})
        self.assertTrue(r['strong_metadata_closure_complete'])
        self.assertEqual(r['nodes']['/usr/lib/dyld']['classification'],'AVAILABLE_AND_COMPATIBLE')


if __name__=='__main__':unittest.main()
