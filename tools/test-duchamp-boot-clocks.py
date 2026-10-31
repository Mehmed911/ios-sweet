#!/usr/bin/env python3
"""Execute the actual staged PE clock function with mocked saved-DT properties."""
import argparse,hashlib,importlib.util,json,re,subprocess
from pathlib import Path

spec=importlib.util.spec_from_file_location('boot_stage',Path(__file__).with_name('stage-duchamp-gic-boot.py'))
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)
sha=lambda b:hashlib.sha256(b).hexdigest()

def function(text):
    start=text.index('void\npe_identify_machine(');body=text.index('{',start);end=body+1;depth=1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--source',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing output')
    original=a.source.read_bytes();text=original.decode();updated=stage.clock_source(text)
    fields=sorted(set(re.findall(r'gPEClockFrequencyInfo\.(\w+)',text)))
    prefix='''#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
typedef int boot_args;typedef int DTEntry;typedef int OpaqueDTEntryIterator;
#define kSuccess 0
#define bzero(p,n) memset(p,0,n)
static uint64_t counter=13000000,bus=100000000,core=1000000000;
static int have_bus,have_core;
static uintptr_t pe_arm_get_soc_base_phys(void){return 0x1000000;}
static int SecureDTLookupEntry(void *root,const char *name,DTEntry *out){*out=1;return 0;}
static int SecureDTInitEntryIterator(DTEntry node,OpaqueDTEntryIterator *iter){*iter=0;return 0;}
static int SecureDTIterateEntries(OpaqueDTEntryIterator *iter,DTEntry *node){if((*iter)++)return -1;*node=2;return 0;}
static int SecureDTGetProperty(DTEntry node,const char *name,const void **value,unsigned *size){
    *size=8;
    if(!strcmp(name,"state")){*value="running";return 0;}
    if(!strcmp(name,"timebase-frequency")){*value=&counter;*size=4;return 0;}
    if(!strcmp(name,"bus-frequency") && have_bus){*value=&bus;return 0;}
    if(!strcmp(name,"clock-frequency") && have_core){*value=&core;return 0;}
    return -1;
}
typedef struct {'''+''.join('uint64_t '+name+';' for name in fields)+'''} clock_frequency_info_t;
static clock_frequency_info_t gPEClockFrequencyInfo;
'''
    suffix='''
int main(int argc,char **argv){
    if(argc==1){
        have_bus=have_core=0;pe_identify_machine(0);
        assert(gPEClockFrequencyInfo.cpu_clock_rate_hz==0);
        assert(gPEClockFrequencyInfo.bus_clock_rate_hz==0);
        assert(gPEClockFrequencyInfo.timebase_frequency_hz==13000000);
        assert(gPEClockFrequencyInfo.bus_to_cpu_rate_num==0);
        assert(gPEClockFrequencyInfo.bus_to_cpu_rate_den==2);
        assert(gPEClockFrequencyInfo.bus_to_dec_rate_num==0);
        assert(gPEClockFrequencyInfo.bus_to_dec_rate_den==1);
        have_bus=have_core=1;bus=1;pe_identify_machine(0);
        assert(gPEClockFrequencyInfo.bus_to_dec_rate_num==0);
        assert(gPEClockFrequencyInfo.bus_to_dec_rate_den==1);
        bus=100000000;counter=0;pe_identify_machine(0);
        assert(gPEClockFrequencyInfo.bus_to_dec_rate_num==0);
        assert(gPEClockFrequencyInfo.bus_to_dec_rate_den==1);
    }
    have_bus=have_core=1;counter=62500000;bus=100000000;core=1000000000;
    pe_identify_machine(0);
    assert(gPEClockFrequencyInfo.bus_to_cpu_rate_num==20);
    assert(gPEClockFrequencyInfo.bus_to_cpu_rate_den==2);
    assert(gPEClockFrequencyInfo.bus_to_dec_rate_num==1);
    assert(gPEClockFrequencyInfo.bus_to_dec_rate_den==1);
    puts("PE CLOCK CONSUMER PASS");return 0;
}
'''
    a.output.mkdir(parents=True,exist_ok=False);reports={}
    cases=[('baseline-missing',text,False,[]),('duchamp',updated,True,[]),('legacy-known',updated,False,['known'])]
    for name,body,duchamp,args in cases:
        src=a.output/(name+'.c');exe=a.output/name
        src.write_text(prefix+function(body)+suffix)
        cmd=['clang','-std=c11','-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all']
        if duchamp:cmd+=['-DDUCHAMP=1']
        subprocess.run(cmd+[str(src),'-o',str(exe)],check=True,capture_output=True)
        result=subprocess.run([str(exe.resolve()),*args],capture_output=True,text=True)
        (a.output/(name+'.log')).write_text(result.stdout+result.stderr)
        reports[name]={'exit':result.returncode,'expected_failure':name=='baseline-missing'}
        if name=='baseline-missing':assert result.returncode!=0 and 'division by zero' in result.stderr
        else:assert result.returncode==0 and 'PE CLOCK CONSUMER PASS' in result.stdout
    assert a.source.read_bytes()==original
    report={'passed':True,'source_sha256':sha(original),'staged_sha256':sha(updated.encode()),
        'executed_function_sha256':sha(function(updated).encode()),'cases':reports,
        'scope':'actual PE function, mocked DT/compiler-native structs; no hardware clock or phone test'}
    (a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
