"""Read-only parsers for one captured Duchamp boot/vendor-boot evidence set.

No device access, module loading, firmware execution or physical authorization.
Extracted modules and instruction fragments must remain outside Git.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

BOOT_SHA='1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12'
VENDOR_SHA='d1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49'
FDT_SHA='9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29'
UFS_SHA='7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493'
RELEASE='6.1.57-android14-11-gcf2c2dc91b9e-ab11782407'
GKI='cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6'
MODULES=('iommu_debug.ko','iommu_secure.ko','mtk_iommu.ko','phy-mtk-ufs.ko',
         'ufs-mediatek-dbg.ko','ufs-mediatek-mod.ko')
# Offsets are section-relative in the pinned ET_REL module, never runtime PAs.
SMC_BLOCKS=(('mtcmos0',0x23c8,0x23f4,512,0,0),('mtcmos1',0x23f8,0x2420,512,1,0),
            ('refpre',0x4b54,0x4b80,8,None,0),('refpost',0x4c48,0x4c74,8,None,1))

def sha(data):return hashlib.sha256(data).hexdigest()
def pinned(path,expected):
    data=Path(path).read_bytes()
    if sha(data)!=expected:raise ValueError('saved artifact hash mismatch: '+Path(path).name)
    return data
def unpack(data,offset,fmt):
    if offset<0 or offset+struct.calcsize(fmt)>len(data):raise ValueError('truncated binary structure')
    return struct.unpack_from(fmt,data,offset)
def span(data,offset,size):
    if offset<0 or size<0 or offset+size>len(data):raise ValueError('binary extent out of bounds')
    return data[offset:offset+size]
def lz4(data):
    if data[:4]!=b'\x02\x21\x4c\x18':raise ValueError('expected captured legacy LZ4 frame')
    # Input hashes are checked before this call; only captured images are accepted.
    r=subprocess.run(['lz4','-dc'],input=data,capture_output=True,check=True,timeout=30)
    if len(r.stdout)>128*1024*1024:raise ValueError('decompressed image too large')
    return r.stdout
def boot_contents(path):
    data=pinned(path,BOOT_SHA)
    if data[:8]!=b'ANDROID!' or unpack(data,40,'<I')[0]!=4:raise ValueError('expected boot v4')
    image=lz4(span(data,4096,unpack(data,8,'<I')[0]))
    release=re.search(rb'Linux version ([^ \x00\n]+)',image)
    if not release or release[1].decode()!=RELEASE:raise ValueError('saved kernel release differs')
    start=image.index(b'IKCFG_ST')+8;end=image.index(b'IKCFG_ED',start)
    config=gzip.decompress(image[start:end])
    if len(config)>1024*1024:raise ValueError('kernel config too large')
    return image,config
def vendor_contents(path):
    data=pinned(path,VENDOR_SHA)
    if data[:8]!=b'VNDRBOOT' or unpack(data,8,'<I')[0]!=4:raise ValueError('expected vendor boot v4')
    page=unpack(data,12,'<I')[0];header=unpack(data,2096,'<I')[0]
    if page!=4096 or header!=2128:raise ValueError('vendor boot header differs')
    return lz4(span(data,(header+page-1)&~(page-1),unpack(data,24,'<I')[0]))
def selected_cpio(data,metadata=None):
    offset=0;archives=0;modules={}
    while offset<len(data):
        if data[offset]==0:offset+=1;continue
        if span(data,offset,6)!=b'070701':raise ValueError('unsupported newc archive')
        raw=span(data,offset+6,104)
        h=[int(raw[i*8:i*8+8],16) for i in range(13)]
        mode,size,namesize=h[1],h[6],h[11]
        if not 1<=namesize<=4096:raise ValueError('cpio name length')
        name=span(data,offset+110,namesize)
        if name[-1:]!=b'\0':raise ValueError('cpio name terminator')
        name=name[:-1].decode('utf-8')
        start=(offset+110+namesize+3)&~3;content=span(data,start,size)
        offset=(start+size+3)&~3
        if name=='TRAILER!!!':archives+=1;continue
        if name=='lib/modules/modules.load' and metadata is not None:
            if 'module_load_intent' in metadata:raise ValueError('duplicate module load list')
            metadata['module_load_intent']=[n for n in content.decode('utf-8').splitlines() if n in MODULES]
            metadata['modules_load_sha256']=sha(content)
            metadata['module_load_is_runtime_observation']=False
        for module in MODULES:
            if name=='lib/modules/'+module:
                if mode&0o170000!=0o100000 or module in modules:raise ValueError('nonregular/duplicate module')
                modules[module]=content
    if archives!=2 or set(modules)!=set(MODULES):raise ValueError('captured module/archive set differs')
    if sha(modules['ufs-mediatek-mod.ko'])!=UFS_SHA:raise ValueError('UFS module provenance mismatch')
    return modules

class Elf:
    def __init__(self,data):
        self.data=data
        if data[:6]!=b'\x7fELF\x02\x01' or unpack(data,16,'<HH')!=(1,183):raise ValueError('not AArch64 ET_REL')
        off=unpack(data,40,'<Q')[0];stride,count,strings=unpack(data,58,'<HHH')
        if stride!=64 or not 0<strings<count<65536:raise ValueError('ELF section table shape')
        self.headers=[unpack(data,off+i*64,'<IIQQQQIIQQ') for i in range(count)]
        names=self.section_data(strings);self.sections={}
        for i,h in enumerate(self.headers):
            n=self.cstring(names,h[0]);self.sections[n]=i
        self.symbols=[]
        symidx=self.sections['.symtab'];h=self.headers[symidx];strings=self.section_data(h[6])
        if h[9]!=24 or h[5]%24:raise ValueError('ELF symbol layout')
        for pos in range(h[4],h[4]+h[5],24):
            n,info,other,section,value,size=unpack(data,pos,'<IBBHQQ')
            self.symbols.append((self.cstring(strings,n),section,value,size))
    @staticmethod
    def cstring(data,offset):
        if not 0<=offset<len(data):raise ValueError('ELF string offset')
        end=data.find(b'\0',offset)
        if end<0:raise ValueError('ELF string terminator')
        return data[offset:end].decode('utf-8')
    def section_data(self,index):
        h=self.headers[index];return span(self.data,h[4],h[5])
    def modinfo(self):
        result={k:[] for k in ('vermagic','name','srcversion','depends')}
        for item in self.section_data(self.sections['.modinfo']).split(b'\0'):
            k,_,v=item.partition(b'=');key=k.decode('utf-8')
            if key in result:result[key].append(v.decode('utf-8'))
        return result
    def call(self,address,target):
        index=self.sections['.rela.text'];h=self.headers[index]
        if h[9]!=24 or h[5]%24:raise ValueError('ELF relocation layout')
        matches=[]
        for pos in range(h[4],h[4]+h[5],24):
            offset,info,addend=unpack(self.data,pos,'<QQq')
            if offset==address:matches.append((info&0xffffffff,self.symbols[info>>32][0],addend))
        if matches!=[(283,target,0)]:raise ValueError('unexpected external call relocation')
    def fragments(self):
        text=self.section_data(self.sections['.text']);out={};proof=[]
        for name,begin,end,selector,on,stage in SMC_BLOCKS:
            self.call(end,'__arm_smccc_smc')
            if unpack(text,end,'<I')[0]&0xfc000000!=0x94000000:raise ValueError('expected BL opcode')
            block=span(text,begin,end-begin);out[name]=block
            proof.append({'name':name,'section':'.text','begin':hex(begin),'call':hex(end),
                          'sha256':sha(block),'bytes':len(block),'selector':selector,'on':on,'stage':stage})
        self.call(0x12a44,'dma_set_mask');self.call(0x12a58,'dma_set_mask');self.call(0x12a68,'dma_set_coherent_mask')
        for name,begin,end in [('dma',0x12a34,0x12a6c),('dma64',0x1303c,0x13048)]:
            out[name]=span(text,begin,end-begin)
            proof.append({'name':name,'section':'.text','begin':hex(begin),'end':hex(end),'sha256':sha(out[name]),'bytes':end-begin})
        return out,proof

def sources(repo,directory):
    catalog=json.loads((repo/'duchamp/drivers/mt6897-contract-sources.json').read_text())
    result={}
    for e in catalog['files']:
        data=(Path(directory)/e['path']).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if blob!=e['git_blob']:raise ValueError('source blob mismatch: '+e['path'])
        result[e['path']]={'git_blob':blob,'sha256':sha(data),'commit':e['commit']}
    return result
