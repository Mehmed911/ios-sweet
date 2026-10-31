"""Saved-DTB to isolated single-CPU XNU boot profiles. No device access."""
import copy,hashlib,importlib.util,os,struct,sys
from pathlib import Path
import adt
FDT_SHA='9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29'
TEMPLATE_SHA='be512dce04bf581d188440246b4e3402de057a43f4c178da7984a68ccbb9ba2f'
COMMIT='cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6'
SOURCE_PINS={'drivers/irqchip/irq-gic-v3.c':'b0c065108bb7c8dc343e067e39bdd2d6d95676f0',
 'include/linux/irqchip/arm-gic-v3.h':'d4a40c7f8e05361e7f53ee9d5858490e5a97d92b',
 'Documentation/devicetree/bindings/timer/arm,arch_timer.yaml':'c5fc3b6c8bd0bfeaf06867ab2d58b0be07729236',
 'Documentation/devicetree/bindings/interrupt-controller/arm,gic-v3.yaml':'9f7d3e11aacb8aa377f05a7a08666a12a81b54e2'}
spec=importlib.util.spec_from_file_location('boot_hw',Path(__file__).with_name('inspect-duchamp-hardware.py'))
hardware=importlib.util.module_from_spec(spec);sys.modules[spec.name]=hardware;spec.loader.exec_module(hardware)
u32=lambda *v:struct.pack('<%dI'%len(v),*v)
u64=lambda *v:struct.pack('<%dQ'%len(v),*v)
string=lambda *v:('\0'.join(v)+'\0').encode()
sha=lambda data:hashlib.sha256(data).hexdigest()

def sources(root):
    receipt=[]
    for name,digest in SOURCE_PINS.items():
        data=(root/name).read_bytes()
        if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=digest:raise ValueError('source pin differs: '+name)
        receipt.append({'path':name,'git_blob':digest,'sha256':sha(data),'commit':COMMIT})
    return receipt

def facts(tree,board):
    if tree.nodes['/'].strings('model')!=['MT6897']:raise ValueError('MT6897 capture required')
    pick=lambda name:[n for n in tree.nodes.values() if name in n.strings('compatible')]
    gics=pick('arm,gic-v3');timers=pick('arm,armv8-timer');pscis=pick('arm,psci-1.0')
    if len(gics)!=1 or len(timers)!=1 or len(pscis)!=1:raise ValueError('ambiguous GIC/timer/PSCI')
    gic=gics[0];timer=timers[0];regs=tree.registers(gic)
    if len(regs)!=2 or gic.scalar('#redistributor-regions',1)!=1 or 'redistributor-stride' in gic.props:
        raise ValueError('unsupported GIC region/stride layout')
    d,ds,r,rs=[int(regs[i][key],0) for i in range(2) for key in ['physical_address','bytes']]
    if not d or not r or any(v%65536 for v in [d,ds,r,rs]) or ds<65536 or rs<131072 or ds>r-d:
        raise ValueError('invalid/overlapping GIC extents')
    width=gic.scalar('#interrupt-cells');irqs=tree.interrupts(timer)
    if width not in [3,4] or len(irqs)!=4:raise ValueError('unsupported architected timer specifiers')
    intids=[]
    for irq in irqs:
        a=irq['args']
        if irq['provider']!=gic.path or len(a)!=width or a[0]!=1 or a[1]>15 or a[2]!=4 or (width==4 and a[3]!=0):
            raise ValueError('unsupported timer PPI/flags/partition')
        intids.append(a[1]+16)
    freq=timer.scalar('clock-frequency')
    if not freq or freq!=int(board['timer']['frequency'],0):raise ValueError('board/FDT timer mismatch')
    if pscis[0].strings('method')!=['smc']:raise ValueError('unsupported PSCI declaration')
    cpus=[]
    for n in tree.nodes.values():
        if n.props.get('device_type')!=b'cpu\0':continue
        cells=n.cells('reg');comp=n.strings('compatible')
        if len(cells)!=1 or not comp or cells[0]&~0xffffff or n.strings('status') not in [[],['okay']]:
            raise ValueError('unsupported CPU reg/status')
        cpus.append({'mpidr':cells[0],'compatible':comp[0]})
    cpus.sort(key=lambda c:c['mpidr'])
    if len(cpus)!=8 or [c['mpidr'] for c in cpus]!=[i<<8 for i in range(8)] or len({c['mpidr'] for c in cpus})!=8:
        raise ValueError('captured CPU IDs differ')
    if [c['compatible'] for c in cpus]!=['arm,cortex-a510']*4+['arm,cortex-a715']*4:raise ValueError('captured CPU types differ')
    for key,value in [('gicd_base',d),('gicr_base',r),('gicr_size',rs)]:
        if int(board['interrupts'][key],0)!=value:raise ValueError('board/FDT GIC mismatch')
    chosen=tree.nodes['/chosen'];tag=chosen.props.get('atag,videolfb',b'')
    if len(tag)<20:raise ValueError('missing framebuffer tag')
    fb=struct.unpack_from('<Q',tag)[0];reserved=struct.unpack_from('<I',tag,16)[0]
    split=chosen.scalar('atag,videolfb-fb_base_l') | chosen.scalar('atag,videolfb-fb_base_h')<<32
    if fb!=split or reserved!=chosen.scalar('atag,videolfb-vramSize'):raise ValueError('framebuffer tag disagreement')
    b=board['framebuffer'];stride=b['stride'];height=b['height'];width_px=b['width'];extent=(stride*height+4095)&~4095
    if int(b['base'],0)!=fb or b['depth']!=32 or stride<width_px*4 or min(width_px,height)<1 or extent>reserved:
        raise ValueError('framebuffer extent/geometry mismatch')
    return {'gicd':d,'gicd_bytes':ds,'gicr':r,'gicr_bytes':rs,'interrupt_cells':width,
            'timer_hz':freq,'timer_intids':intids,'virtual_timer_intid':intids[2],
            'psci_method':'smc','cpus':cpus,'framebuffer':{'base':fb,'bytes':extent,'reserved_bytes':reserved,
            'width':width_px,'height':height,'stride':stride,'depth':32},
            'geometry_source':b['source'],'memory_base':int(board['memory']['payload_base'],0),
            'memory_bytes':int(board['memory']['payload_size'],0)}

def child(node,name):
    found=[c for c in node.children if c.name==name]
    if len(found)!=1:raise ValueError('ambiguous template node '+name)
    return found[0]
def setprop(node,key,value):
    node.props=[p for p in node.props if p[0]!=key]+[(key,0,value)]
def build(template,target,profile,seed=None):
    if target not in ['phone','qemu']:raise ValueError('explicit phone/qemu target required')
    if sha(template)!=TEMPLATE_SHA:raise ValueError('template pin differs')
    if seed is not None and len(seed)!=64:raise ValueError('diagnostic seed must have64 bytes')
    tree,end=adt.parse(template)
    if end!=len(template):raise ValueError('trailing template bytes')
    chosen=child(tree,'chosen');mapping=child(chosen,'memory-map')
    if mapping.prop('RAMDisk') is not None:raise ValueError('template already has a RAMDisk')
    setprop(chosen,'random-seed',os.urandom(64) if seed is None else seed)
    setprop(chosen,'firmware-version',string('duchamp-'+target+'-boot-profile-v1'))
    setprop(chosen,'system-firmware-version',string('duchamp-'+target+'-boot-profile-v1'))
    setprop(chosen,'dram-base',u64(profile['memory_base']));setprop(chosen,'dram-size',u64(profile['memory_bytes']))
    tree.children=[c for c in tree.children if c.name not in ['sweet-ufs','duchamp-qemu-ufs']]
    comps=['D22AP','iPhone10,3','xiaomi,sweet','AppleARM']
    comps[2:2]=['xiaomi,duchamp','mediatek,mt6897'] if target=='phone' else ['qemu,virt']
    setprop(tree,'compatible',string(*comps))
    cpus=child(tree,'cpus');cpu=copy.deepcopy(child(cpus,'cpu0'));cpus.children=[cpu]
    # TCG supplies a counter frequency, not measured core/bus/DDR rates.
    cpu.props=[p for p in cpu.props if p[0] not in ['clock-frequency','bus-frequency','memory-frequency']]
    if target=='phone':
        cp=profile['cpus'][0];freq=profile['timer_hz'];d=profile['gicd'];ds=profile['gicd_bytes'];r=profile['gicr'];rs=profile['gicr_bytes']
    else:
        cp={'mpidr':0,'compatible':'arm,cortex-a76'};freq=62500000;d=0x8000000;ds=0x10000;r=0x80a0000;rs=0x100000
    setprop(cpu,'reg',u32(cp['mpidr']));setprop(cpu,'compatible',string(cp['compatible'],'ARM,v8'))
    for key in ['timebase-frequency','fixed-frequency','peripheral-frequency']:setprop(cpu,key,u32(freq))
    arm=child(tree,'arm-io');gic=child(arm,'gic')
    ranges=arm.prop('ranges')
    if len(ranges)!=24:raise ValueError('unsupported arm-io translation')
    bus,soc,span=struct.unpack('<3Q',ranges)
    if bus!=0 or not soc or d<soc or r<soc or d+ds>soc+span or r+rs>soc+span:raise ValueError('GIC outside template bus')
    setprop(gic,'reg',u64(d-soc,ds,r-soc,rs));setprop(gic,'virtual-timer-intid',u32(profile['virtual_timer_intid']))
    fb=profile['framebuffer'];fbnode=child(tree,'sweet-fbcon')
    setprop(fbnode,'reg',u64(fb['base'],fb['bytes']))
    for key in ['width','stride']:setprop(fbnode,key,u32(fb[key]))
    # sweet_early_mark() paints the last32 pixels; fbcon's height is a text
    # viewport, distinct from the full display/boot_args framebuffer geometry.
    console_height=fb['height']-32
    if console_height<32:raise ValueError('no complete console row above diagnostic band')
    setprop(fbnode,'height',u32(console_height))
    display=child(arm,'disp0');setprop(display,'canvas-width',u32(fb['width']));setprop(display,'canvas-height',u32(fb['height']))
    blob=adt.serialize(tree)
    if b'qcom,' in blob:raise ValueError('unexpected Qualcomm hardware identity')
    emitted={'target':target,'gicd':d,'gicd_bytes':ds,'gicr':r,'gicr_bytes':rs,'timer_hz':freq,
        'virtual_timer_intid':profile['virtual_timer_intid'],'boot_mpidr':cp['mpidr'],'cpu_count':1,
        'secondary_start_enabled':False,'physical_backend_enabled':False,'phone_execution_authorized':False,
        'template_identity_aliases_retained':['D22AP','iPhone10,3','xiaomi,sweet','AppleARM'],
        'unknown_cpu_bus_memory_clocks_omitted':True}
    emitted['console_viewport']={'height':console_height,'rows':console_height//32,'reserved_bottom_pixels':32}
    return blob,emitted
