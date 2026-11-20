#!/usr/bin/env python3
"""0BSD bind passive trace sites to the actual source kernel and 20F66 cache."""
import argparse,hashlib,json,struct,subprocess,sys
from pathlib import Path
from duchamp_source_kernel import select
from duchamp_dwarf_layout import parse,layout
from duchamp_macho_preflight import inspect

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--kernel-manifest',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve();out.mkdir(exist_ok=True)
    receipt=a.kernel_manifest.resolve();r=json.loads(receipt.read_text());kernel=Path(r['kernel']);pin=select(kernel,receipt)
    layouts={};objects=[]
    for object_name,names in {'sleh.o':['thread','thread_ro','task'],'kern_proc.o':['proc'],'sys_generic.o':['write_args'],
        'SweetSurface.cpo':['SweetSurface','IOSurfaceRootUserClient'],
        'SweetFramebuffer.cpo':['AppleCLCD','IOMobileFramebufferUserClient','IOExternalMethodArguments']}.items():
        obj=next(x for x in r['input_objects'] if Path(x['object']).name==object_name)
        assert sha(obj['object'])==obj['new_object_sha256']
        text=subprocess.check_output(['llvm-dwarfdump','--debug-info',obj['object']],text=True)
        (out/(object_name+'.dwarf.txt')).write_text(text)
        records=parse(text)
        for n in names:layouts[n]=layout(records,n)
        objects.append(obj)
    nm=subprocess.check_output(['llvm-nm','--defined-only',str(kernel)],text=True)
    symbols={p[-1]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())>=3}
    names={'cache_check':'_shared_region_check_np','surface_method':'__ZN23IOSurfaceRootUserClient14externalMethodEjP25IOExternalMethodArgumentsP24IOExternalMethodDispatchP8OSObjectPv',
        'fb_method':'__ZN29IOMobileFramebufferUserClient14externalMethodEjP25IOExternalMethodArgumentsP24IOExternalMethodDispatchP8OSObjectPv',
        'swap':'__ZN9AppleCLCD4swapEPKh','present':'__ZN9AppleCLCD7presentEPKh',
        'surface_address':'__ZN12SweetSurface13kernelAddressEv','completion_write':'_write',
        'completion_write_nocancel':'_write_nocancel'}
    data=kernel.read_bytes();at=32;segments=[]
    for _ in range(struct.unpack_from('<I',data,16)[0]):
        cmd,size=struct.unpack_from('<II',data,at)
        if cmd==0x19:
            va,span,off,amount=struct.unpack_from('<4Q',data,at+24);segments.append((va,off,amount))
        at+=size
    def bytes_at(va):
        for base,off,size in segments:
            if base<=va and va+4<=base+size:return data[off+va-base:off+va-base+4].hex()
        raise ValueError('kernel site outside file-backed segment')
    sites={n:dict(address=symbols[s],opcode=bytes_at(symbols[s]),symbol=s) for n,s in names.items()}
    mapping=json.loads(Path('work/20F66-cache-v4/cache-info.json').read_text())
    cache=Path('work/20F66-cache-v4/apple-extracted/System/Library/Caches/com.apple.dyld')
    components={}
    for p in cache.glob('dyld_shared_cache_arm64*'):
        if p.name.endswith('.symbols'):continue
        with p.open('rb') as f:header=f.read(104)
        import uuid
        components[str(uuid.UUID(bytes=header[88:104])).upper()]=p
    user={ 'transaction_commit':0x1882d5148,'context_commit':0x1882a7e3c,'render_display':0x1882d90dc,
        'display_create_surface':0x188372634,'display_present_surface':0x1885244ec,'display_swap_layer':0x188531698,
        'sw_new_context':0x188437dd4,'metal_new_context':0x188437f9c,'null_new_context':0x188437e28,
        # The first site is immediately AFTER MTLCreateSystemDefaultDevice;
        # the historical metal_device_result name denotes the wrapper RET.
        'metal_default_device_return':0x18837b740,
        'metal_device_result':0x18837b758,'display_metal_result':0x1885330c4,
        'iosurface_create':0x1a392fed4,'swap_set_layer':0x1af1c0848,'kern_swap_set_layer':0x1af1c08a4}
    user_sites={}
    for name,va in user.items():
        found=[]
        for uid,maps in mapping['mappings'].items():
            for m in maps:
                if m['address']<=va and va+4<=m['address']+m['size']:
                    p=components[uid];off=m.get('file_offset',0)+va-m['address']
                    with p.open('rb') as f:f.seek(off);opcode=f.read(4).hex()
                    found.append((p,opcode))
        if len(found)!=1:raise ValueError('ambiguous cache code mapping')
        p,opcode=found[0]
        symbol=subprocess.check_output(['research/host-ipsw-3.1.739/ipsw','dyld','a2s',str(cache/'dyld_shared_cache_arm64'),hex(va),'--image','--demangle'],text=True)
        user_sites[name]=dict(address=va,opcode=opcode,symbolication=symbol,component=str(p),component_sha256=sha(p))
    originals={}
    for name,path in {'backboardd':'work/ui-daemon-scan-v1/apple-extracted/usr/libexec/backboardd',
        'SpringBoard':'work/springboard-bundle-v2/apple-extracted/System/Library/CoreServices/SpringBoard.app/SpringBoard'}.items():
        m=inspect(path);d=Path(path).read_bytes();originals[name]=dict(uuid=m['uuid'],sha256=m['sha256'],entry=m['main_entry'],opcode=d[m['main_entry']:m['main_entry']+4].hex())
    config=dict(version=1,kernel=str(kernel),kernel_sha256=pin,kernel_manifest=str(receipt),
        linked_layout_objects=objects,layouts=layouts,kernel_sites=sites,user_sites=user_sites,
        cache_uuid='E5420DB330D033AA8B7E05B5038BB46D',originals=originals,
        kernel_segments=segments,source_trace_sha256=sha('tools/duchamp-render-passive.gdb'),passive_only=True,
        physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
    (out/'trace-config.json').write_text(json.dumps(config,indent=2)+'\n')
    print(json.dumps(dict(kernel=pin,layout_types=len(layouts),kernel_sites=len(sites),user_sites=len(user_sites))))

if __name__=='__main__':main()
