# Exact pinned e465723a kernel's EL0 synchronous vector. A virtual hardware
# breakpoint reads user state at exception entry; no guest memory is patched.
python
import gdb,json,struct
names={r.name.upper():r.name for r in gdb.newest_frame().architecture().registers()}
selected={k:names.get(k) for k in ('ESR_EL1','FAR_EL1','ELR_EL1')}
gdb.write('SYSTEM_REGISTERS '+json.dumps(selected)+'\n')
def reg(name):
    return int(gdb.parse_and_eval('$'+name))
class NullFault(gdb.Breakpoint):
    def __init__(self):
        super().__init__('*0xfffffe000747d400',type=gdb.BP_HARDWARE_BREAKPOINT,internal=True)
    def stop(self):
        esr=reg(selected['ESR_EL1']);far=reg(selected['FAR_EL1'])
        if esr!=0x92000006 or far!=8:return False
        data={'esr':hex(esr),'far':hex(far),'elr':hex(reg(selected['ELR_EL1'])),
              'registers':{('x'+str(i)):hex(reg('x'+str(i))) for i in range(31)},'frames':[]}
        fp=reg('x29')
        for i in range(16):
            if not fp or fp&7:break
            try:
                previous,lr=struct.unpack('<QQ',bytes(gdb.selected_inferior().read_memory(fp,16)))
            except Exception as error:
                data['frame_error']=str(error);break
            data['frames'].append({'fp':hex(fp),'previous_fp':hex(previous),'lr':hex(lr)})
            if previous<=fp:break
            fp=previous
        with open('null-fault.json','x') as output:json.dump(data,output,indent=2)
        gdb.write('NULL_FAULT_CAPTURED '+json.dumps(data)+'\n')
        return True
try:
    if not all(selected.values()):raise RuntimeError('system registers unavailable')
    catcher=NullFault()
    gdb.execute('continue')
except Exception as error:
    gdb.write('TRACE_ERROR '+str(error)+'\n')
finally:
    try:gdb.execute('detach')
    except Exception as error:gdb.write('DETACH_ERROR '+str(error)+'\n')
end
