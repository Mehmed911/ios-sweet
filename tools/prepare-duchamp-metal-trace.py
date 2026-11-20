#!/usr/bin/env python3
"""0BSD extend a source-bound passive trace with actual 20F66 Metal/IOKit sites."""
import argparse,concurrent.futures,hashlib,json,uuid
from pathlib import Path
from duchamp_source_kernel import select
import duchamp_cache_code as cache

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('baseline',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
 c=json.loads(a.baseline.read_text());pin=select(Path(c['kernel']),Path(c['kernel_manifest']))
 if c['kernel_sha256']!=pin or not c['passive_only']:raise ValueError('source-bound passive baseline required')
 sites=dict(mtl_default_entry=0x181a34b3c,mtl_array_init=0x181a3142c,mtl_register_entry=0x181b115ec,
  mtl_master_return=0x181b11618,mtl_match_dict_return=0x181b11644,mtl_services_return=0x181b11654,
  mtl_iterator_return=0x181b11688,mtl_next_iterator_return=0x181b116c8,mtl_device_class_return=0x181b11698,
  mtl_array_count_return=0x181a34448,
  io_matching=0x18e53dd48,io_getmatching_services=0x18e542df4,io_iterator_next=0x18e545fd0,
  io_open=0x18e54c55c,io_connect_call=0x18e539c28)
 def one(item):
  name,va=item;raw=cache.read(va,4);symbol=cache.symbol(va)
  if symbol['exit_code']:raise ValueError('symbolication failed')
  return name,dict(address=va,opcode=raw.hex(),symbolication=symbol['text'])
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:c['user_sites'].update(dict(pool.map(one,sites.items())))
 components={};mappings=[];excluded=[]
 for uid,items in cache.M.items():
  if not any(m['init_prot']&4 for m in items):continue
  if uid not in cache.FILES:
   symbols=cache.ROOT/'dyld_shared_cache_arm64.symbols'
   with symbols.open('rb') as f:f.seek(88);symbol_uuid=str(uuid.UUID(bytes=f.read(16))).upper()
   if uid!=symbol_uuid:raise ValueError('unavailable executable cache component: '+uid)
   # ipsw reports a synthetic __TEXT mapping for the separate debug-symbols
   # file. It is not one of the runtime cache components and must not admit
   # a userspace return address in the observer.
   excluded.append(dict(uuid=uid,path=str(symbols.resolve()),reason='separate debug-symbols file, never an allowed runtime return mapping'))
   continue
  p=cache.FILES[uid].resolve()
  if any(m['init_prot']&4 for m in items):components[str(p)]=sha(p)
  for m in items:
   if m['init_prot']&4:mappings.append(dict(address=m['address'],size=m['size'],file_offset=m.get('file_offset',0),path=str(p)))
 c.update(cache_text_mappings=mappings,cache_text_components=components,source_trace_sha256=sha('tools/duchamp-render-passive.gdb'),
          excluded_mappings=excluded,trace_purpose='Original 20F66 Metal device enumeration + independently labelled IOSurface diagnostic')
 a.output.mkdir(parents=True,exist_ok=False);(a.output/'trace-config.json').write_text(json.dumps(c,indent=2)+'\n')
 print(json.dumps(dict(kernel=pin,user_sites=len(c['user_sites']),executable_cache_maps=len(mappings))))
if __name__=='__main__':main()
