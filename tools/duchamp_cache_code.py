"""0BSD bounded reads/decoding of the local 20F66 cache; no ObjC analysis."""
import json,struct,uuid,subprocess,sys,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ROOT=Path('work/20F66-cache-v4/apple-extracted/System/Library/Caches/com.apple.dyld')
M=json.loads(Path('work/20F66-cache-v4/cache-info.json').read_text())['mappings'];FILES={}
for p in ROOT.glob('dyld_shared_cache_arm64*'):
 if p.name.endswith('.symbols'):continue
 with p.open('rb') as f:h=f.read(104)
 FILES[str(uuid.UUID(bytes=h[88:104])).upper()]=p

def read(va,n):
 if not isinstance(va,int) or not isinstance(n,int) or not 0<n<=1<<20 or not 0<=va<=(1<<64)-n:raise ValueError('invalid cache interval')
 matches=[(FILES[u],m.get('file_offset',0)+va-m['address']) for u,maps in M.items() for m in maps if m['address']<=va and va+n<=m['address']+m['size']]
 if len(matches)!=1:raise ValueError('ambiguous/out-of-bounds cache VA')
 p,off=matches[0]
 with p.open('rb') as f:f.seek(off);b=f.read(n)
 if len(b)!=n:raise ValueError('short cache read')
 return b

def symbol(va):
 r=subprocess.run(['research/host-ipsw-3.1.739/ipsw','dyld','a2s',str(ROOT/'dyld_shared_cache_arm64'),hex(va),'--image','--demangle'],capture_output=True,text=True)
 return dict(exit_code=r.returncode,text=r.stdout+r.stderr)

def dump(va,n):
 code=read(va,n);dis=list(Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(code,va))
 return dict(address=hex(va),code=code.hex(),instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str) for i in dis],symbol=symbol(va))
if __name__=='__main__':
 va=int(sys.argv[1],0);n=int(sys.argv[2],0);item=dump(va,n)
 Path(sys.argv[3]).write_text(json.dumps(item,indent=2)+'\n')
 print(item['symbol']['text']);print('\n'.join(f"{i['address']} {i['mnemonic']} {i['operands']}" for i in item['instructions']))
