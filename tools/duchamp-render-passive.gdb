# QEMU only. Hardware breakpoints and reads; no register/memory/function writes.
python
import gdb,hashlib,json,os,struct,time
from pathlib import Path
from collections import Counter
cfg=json.loads(Path(os.environ['DUCHAMP_PASSIVE_TRACE_CONFIG']).read_text())
plan=json.loads(Path('layout.json').read_text())
if not (cfg['passive_only'] and plan['qemu_only'] and not plan['physical_storage'] and
        cfg['kernel_sha256']==plan['kernel_sha256']):raise RuntimeError('not a bound QEMU source profile')
kernel=Path(cfg['kernel']).read_bytes()
if hashlib.sha256(kernel).hexdigest()!=cfg['kernel_sha256']:raise RuntimeError('kernel changed')
log=Path('render-events.jsonl').open('x');points=[];counts=Counter();pending={};retpoints={};owners={};frames={};done=False
started=time.monotonic();seq=0;user_installed=False;installed_sites=set()
matchnames={};iteratornames={}
registers={r.name.upper():r.name for r in gdb.newest_frame().architecture().registers()}
def reg(n):return int(gdb.parse_and_eval('$'+registers.get(n.upper(),n)))&((1<<64)-1)
def read(a,n):
    if not a or not 0<=n<=32<<20:raise ValueError('read bounds')
    return bytes(gdb.selected_inferior().read_memory(a,n))
def uint(a,n=8):return int.from_bytes(read(a,n),'little')
def optional_string(a):
    try:return read(a,96).split(b'\0')[0].decode('ascii','replace')
    except gdb.MemoryError:return None
def field(a,t,n,size=8):
    desc=cfg['layouts'][t];offset=desc['members'][n]
    if offset+size>desc['bytes']:raise ValueError('field width outside bound type')
    return uint(a+offset,size)
def identity():
    thread=reg('TPIDR_EL1')
    if thread<0xffff000000000000:return None
    ro=field(thread,'thread','t_tro')
    if not ro or field(ro,'thread_ro','tro_owner')!=thread:return None
    proc=field(ro,'thread_ro','tro_proc');task=field(ro,'thread_ro','tro_task')
    if not proc:
        # Timer/work-loop callbacks may have a valid kernel thread but no BSD
        # process. Observe presentation without inventing a userspace owner.
        if reg('pc')<0xffff000000000000:return None
        return dict(pid=0,name='<kernel-thread>',task=task,birth=0,
                    tid=field(thread,'thread','thread_id'),kernel_context=True)
    name=read(proc+cfg['layouts']['proc']['members']['p_name'],33).split(b'\0')[0].decode('ascii','replace')
    return dict(pid=field(proc,'proc','p_pid',4),name=name,task=task,
                birth=field(task,'task','task_uniqueid'),tid=field(thread,'thread','thread_id'))
def emit(kind,who=None,**kw):
    global seq
    seq+=1;row=dict(sequence=seq,host_seconds=round(time.monotonic()-started,4),kind=kind)
    if who:row.update(who)
    row.update(kw);log.write(json.dumps(row)+'\n');log.flush()
def opcode(va):
    for base,off,size in cfg['kernel_segments']:
        if base<=va and va+4<=base+size:return kernel[off+va-base:off+va-base+4].hex()
    raise ValueError('return outside file-backed kernel')
def header_uuid(base):
    h=read(base,32);magic,cpu,sub,kind,ncmd,size,flags,_=struct.unpack('<8I',h)
    if magic!=0xfeedfacf or cpu!=0x100000c or sub&0xffffff or size>65536 or ncmd>4096:raise ValueError('process Mach-O header')
    raw=read(base+32,size);at=0;identifier=None
    for _ in range(ncmd):
        cmd,n=struct.unpack_from('<II',raw,at)
        if n<8 or n>len(raw)-at:raise ValueError('process commands')
        if cmd==0x1b:identifier=raw[at+8:at+24].hex().upper()
        at+=n
    return identifier
def record(rec):
    raw=read(rec,0x46c)
    return dict(swap_id=struct.unpack_from('<I',raw,0x50)[0],surfaces=list(struct.unpack_from('<4I',raw,0x54)),
                mask=struct.unpack_from('<I',raw,0x104)[0],rect_a=[list(struct.unpack_from('<4i',raw,0x64+i*16)) for i in range(4)],
                rect_b=[list(struct.unpack_from('<4i',raw,0xc4+i*16)) for i in range(4)])
def surface(s):
    return {k:field(s,'SweetSurface',k,4) for k in ['id','width','height','bytesPerRow','offset','pixelFormat','allocSize']}
def framebuffer(fb):
    x={k:field(fb,'AppleCLCD',k,4) for k in ['fWidth','fHeight','fRowBytes','fLogicalW','fLogicalH','fOffX','fOffY']}
    x.update(fPhys=field(fb,'AppleCLCD','fPhys'),fPixels=field(fb,'AppleCLCD','fPixels'),power_off=bool(field(fb,'AppleCLCD','fPowerOff',1)))
    return x
def capture(fb,label):
    v=framebuffer(fb);size=v['fRowBytes']*v['fHeight']
    if v['fPhys']!=0xfcc2f000 or v['fWidth']!=1220 or v['fHeight']!=2712 or v['fRowBytes']!=4992:raise ValueError('unexpected framebuffer')
    with Path('guest-ram.bin').open('rb') as f:f.seek(v['fPhys']-plan['ram_base']);data=f.read(size)
    if len(data)!=size:raise ValueError('frame truncated')
    path=Path(label+'.raw');path.write_bytes(data)
    return dict(path=str(path),sha256=hashlib.sha256(data).hexdigest(),bytes=size,configuration=v)

class Return(gdb.Breakpoint):
    def __init__(self,va):
        super().__init__('*'+hex(va),type=gdb.BP_HARDWARE_BREAKPOINT,internal=True);self.va=va
    def stop(self):
        try:
            who=identity()
            if not who:return False
            key=(self.va,who['tid']);jobs=pending.pop(key,[])
            for kind,data in jobs:returned(kind,who,data)
            if not any(k[0]==self.va for k in pending):self.enabled=False
            return done
        except Exception as e:emit('trace_error',error=str(e),pc=hex(reg('pc')));return True
def on_return(kind,who,data):
    va=reg('x30')
    if read(va,4).hex()!=opcode(va):raise ValueError('return opcode mismatch')
    if va not in retpoints:retpoints[va]=Return(va);points.append(retpoints[va])
    retpoints[va].enabled=True
    pending.setdefault((va,who['tid']),[]).append((kind,data))
def on_user_return(kind,who,data):
    va=reg('x30');slide=field(who['task'],'task','task_shared_region_slide',4)
    unslid=va-slide
    ranges=[r for r in cfg.get('cache_text_mappings',[]) if r['address']<=unslid and unslid+4<=r['address']+r['size']]
    if len(ranges)!=1:raise ValueError('user return outside unique executable cache mapping')
    item=ranges[0]
    with Path(item['path']).open('rb') as f:
        f.seek(item['file_offset']+unslid-item['address']);expected=f.read(4)
    if len(expected)!=4 or read(va,4)!=expected:raise ValueError('user return opcode mismatch')
    if va not in retpoints:retpoints[va]=Return(va);points.append(retpoints[va])
    retpoints[va].enabled=True
    pending.setdefault((va,who['tid']),[]).append((kind,data))
def returned(kind,who,data):
    global user_installed
    if kind=='cache':
        task=who['task'];slide=field(task,'task','task_shared_region_slide',4)
        uid=read(task+cfg['layouts']['task']['members']['task_shared_region_uuid'],16).hex().upper()
        if uid!=cfg['cache_uuid'] or slide>0x56110000 or slide%0x4000:return
        base=0x180000000+slide
        if read(base+88,16).hex().upper()!=uid:raise ValueError('cache UUID memory mismatch')
        emit('cache_bound',who,slide=slide,cache_uuid=uid)
        if not user_installed:
            for n,s in cfg['user_sites'].items():add(s['address']+slide,n,s['opcode'])
            user_installed=True
        if who['name'] in cfg['originals']:
            h=field(task,'task','mach_header_vm_address');expected=cfg['originals'][who['name']]
            try:
                actual=header_uuid(h)
            except gdb.MemoryError:
                emit('image_header_pending',who,base=h)
            else:
                if actual!=expected['uuid'].replace('-',''):raise ValueError('original executable UUID mismatch')
                emit('original_image_bound',who,base=h,uuid=actual)
            add(h+expected['entry'],'original_main',expected['opcode'])
    elif kind=='surface_method':
        args=data['args'];sel=data['selector'];ret=reg('x0')&0xffffffff
        output=field(args,'IOExternalMethodArguments','structureOutput');size=field(args,'IOExternalMethodArguments','structureOutputSize',4)
        detail={}
        if ret==0 and sel in (0,4,34) and output and size>=0x20:
            sid=uint(output+0x18,4);detail=dict(surface_id=sid,user_pixels=uint(output),alloc_size=uint(output+0x1c,4))
            if sel==0:owners[sid]=dict(pid=who['pid'],birth=who['birth'],name=who['name'])
        if ret==0 and sel==35:
            scalar=field(args,'IOExternalMethodArguments','scalarOutput')
            if scalar and field(args,'IOExternalMethodArguments','scalarOutputCount',4)>=1:
                detail['mach_port']=uint(scalar)&0xffffffff
        emit('surface_method_return',who,selector=sel,result=ret,**detail)
    elif kind=='fb_method':emit('fb_method_return',who,selector=data['selector'],result=reg('x0')&0xffffffff)
    elif kind=='surface_address':
        ptr=reg('x0');s=data['surface'];emit('surface_backing',who,surface=s,address=ptr)
        if ptr and 0<s['allocSize']<=32<<20 and s['id'] not in frames and len(frames)<8:
            raw=read(ptr,s['allocSize']);name='surface-%d-%d.raw'%(s['id'],seq)
            Path(name).write_bytes(raw);frames[s['id']]=name;emit('surface_bytes',who,surface=s,path=name,sha256=hashlib.sha256(raw).hexdigest(),owner=owners.get(s['id']))
    elif kind=='present':
        ids=data['record']['surfaces']
        emit('present_completed',who,record=data['record'],owners={str(i):owners.get(i) for i in ids if i},
             frame=capture(data['fb'],'present-%08x-%06d'%(data['record']['swap_id'],seq)) if any(ids) else None,
             empty_submission=not any(ids))
    elif kind.startswith('io_'):
        result=reg('x0')&0xffffffff;detail={}
        key=(who['pid'],who['birth'])
        if kind=='io_matching':
            if data['class_name'] is None:data['class_name']=optional_string(data['arguments'][0])
            result=reg('x0');matchnames[key+(result,)]=data['class_name']
        elif kind=='io_getmatching_services' and result==0:
            iterator=uint(data['output'],4);detail['iterator']=iterator
            iteratornames[key+(iterator,)]=data.get('class_name')
        elif kind=='io_open' and result==0:detail['connection']=uint(data['output'],4)
        emit(kind+'_return',who,result=result,request=data,**detail)

class Trace(gdb.Breakpoint):
    def __init__(self,va,kind,expected):
        super().__init__('*'+hex(va),type=gdb.BP_HARDWARE_BREAKPOINT,internal=True);self.kind=kind;self.expected=expected
    def stop(self):
        global done
        try:
            who=identity()
            if not who:return False
            kind=self.kind
            if kind.startswith('completion_write'):
                if not who['name'].startswith('sweet-platform'):return False
                args=reg('x1');m=cfg['layouts']['write_args']['members'];n=uint(args+m['nbyte']);p=uint(args+m['cbuf'])
                if not 0<n<=512:return False
                s=read(p,n).decode('utf-8','replace')
                if 'PLATFORM SERVICES DONE status=' in s:emit('controller_complete',who,line=s);done=True;return True
                return False
            if kind=='cache_check':
                if who['name'] in ('backboardd','SpringBoard','launchd'):on_return('cache',who,{})
                return False
            key=(kind,who['pid']);counts[key]+=1
            resident=True
            try:actual_opcode=read(reg('pc'),4).hex()
            except gdb.MemoryError:
                if reg('pc')>=0xffff000000000000:raise
                resident=False
                emit('user_site_before_page_fetch',who,site=kind,pc=reg('pc'),expected_opcode=self.expected)
            else:
                if actual_opcode!=self.expected:raise ValueError('site opcode mismatch: '+kind)
            if kind=='original_main':
                h=field(who['task'],'task','mach_header_vm_address');actual=header_uuid(h)
                if actual!=cfg['originals'][who['name']]['uuid'].replace('-',''):raise ValueError('main executable UUID mismatch')
                emit('original_main',who,pc=reg('pc'),base=h,uuid=actual,instruction_bytes_resident=resident)
                self.enabled=False
            elif kind in ('surface_method','fb_method'):
                sel=reg('x1')&0xffffffff;args=reg('x2');client=reg('x0');t='IOSurfaceRootUserClient' if kind=='surface_method' else 'IOMobileFramebufferUserClient'
                own=field(client,t,'fTask');inputs=[]
                count=field(args,'IOExternalMethodArguments','scalarInputCount',4)
                scalar=field(args,'IOExternalMethodArguments','scalarInput')
                if scalar and 0<count<=8:inputs=[uint(scalar+i*8) for i in range(count)]
                emit(kind,who,selector=sel,client_task=own,caller_task_matches=own==who['task'],scalar_input=inputs,raw_arguments=[reg('x'+str(i)) for i in range(4)])
                if counts[key]<=200:on_return(kind,who,dict(args=args,selector=sel))
            elif kind in ('swap','present'):
                rec=record(reg('x1'));emit(kind,who,record=rec,framebuffer=framebuffer(reg('x0')))
                if kind=='present':on_return('present',who,dict(fb=reg('x0'),record=rec))
            elif kind=='surface_address':
                s=surface(reg('x0'))
                if s['id']>1:on_return(kind,who,dict(surface=s))
            elif kind.startswith('io_'):
                if who['name'] not in cfg['originals'] and not who['name'].startswith('sweet-iosurface'):return False
                if counts[key]>80:return False
                args=[reg('x'+str(i)) for i in range(6)];data=dict(arguments=args,caller=reg('x30'))
                taskkey=(who['pid'],who['birth'])
                if kind=='io_matching':
                    data['class_name']=optional_string(args[0])
                elif kind=='io_getmatching_services':
                    data.update(output=args[2],class_name=matchnames.get(taskkey+(args[1],)))
                elif kind=='io_iterator_next':data['class_name']=iteratornames.get(taskkey+(args[0],))
                elif kind=='io_open':data['output']=args[3]
                emit(kind,who,**data);on_user_return(kind,who,data)
                if counts[key]==80:
                    emit('site_observation_capped',who,site=kind,global_site_disabled=True,limit=80)
                    self.enabled=False
            elif kind.startswith('mtl_') and who['name'] in cfg['originals']:
                if counts[key]<=40:
                    detail={}
                    if kind=='mtl_master_return' and (reg('x0')&0xffffffff)==0:
                        detail['master_port']=uint(reg('x29')-0x14,4)
                    elif kind=='mtl_services_return' and (reg('x0')&0xffffffff)==0:
                        detail['iterator']=uint(reg('sp')+0x18,4)
                    emit(kind,who,pc=reg('pc'),lr=reg('x30'),arguments=[reg('x'+str(i)) for i in range(6)],**detail)
                    if kind in ('mtl_default_entry','mtl_array_count_return') and counts[key]==40:
                        emit('site_observation_capped',who,site=kind,global_site_disabled=True,limit=40)
                        self.enabled=False
            elif who['name'] in ('backboardd','SpringBoard') and counts[key]<=40:
                emit(kind,who,pc=reg('pc'),lr=reg('x30'),arguments=[reg('x'+str(i)) for i in range(6)])
                if kind in ('metal_device_result','metal_default_device_return') and counts[key]==40:
                    emit('site_observation_capped',who,site=kind,global_site_disabled=True,limit=40)
                    self.enabled=False
            return False
        except Exception as e:emit('trace_error',error=str(e),pc=hex(reg('pc')));return True
def add(va,kind,expected):
    if (va,kind) in installed_sites:return
    installed_sites.add((va,kind))
    p=Trace(va,kind,expected);points.append(p)
try:
    emit('trace_started',kernel_sha256=cfg['kernel_sha256'],hardware_breakpoints_only=True,guest_register_or_memory_writes=False)
    for n,s in cfg['kernel_sites'].items():add(s['address'],n,s['opcode'])
    gdb.execute('continue')
    emit('trace_stopped',controller_complete=done,counters={str(k):v for k,v in counts.items()})
finally:
    for p in points:p.delete()
    log.close()
    gdb.execute('detach')
end
