#!/usr/bin/env python3
"""Replay pinned Xcode-15 IIG source outputs for this early-stop XNU build.

Does not run an old tool or change IORPC. It copies generated public-source
headers/implementations only after verifying the original artifact, inputs,
configuration, and cached output hashes. Not a general IIG replacement.
"""
from pathlib import Path
import argparse,hashlib,io,json,os,shutil,sys,tarfile,zipfile
ARCHIVE_SHA256='b81e875ad922d3b248ea6e4adc2b16435a19b46d98a9ebcba6e797f7f38853c7'
SOURCE_COMMIT='fdad0de8dc0e75c5ea84762adc03f7232dc91f19'
GENERATED='build/xnu.obj/DEVELOPMENT_ARM64_SWEET/iokit/DEVELOPMENT/DriverKit/'
def digest(b):return hashlib.sha256(b).hexdigest()
def normalized(b):return b.replace(b'\r\n',b'\n')
def stage(archive,out):
 if digest(archive.read_bytes())!=ARCHIVE_SHA256:raise ValueError('Pinned artifact ZIP hash mismatch')
 if out.exists() and any(out.iterdir()):raise ValueError('Cache target must be empty')
 out.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  names=[n for n in z.namelist() if n=='buildtree.tgz']
  if len(names)!=1 or z.getinfo(names[0]).file_size>128*1024*1024:raise ValueError('Unexpected buildtree archive')
  compressed=z.read(names[0])
 inputs={};outputs={}
 with tarfile.open(fileobj=io.BytesIO(compressed),mode='r:gz') as t:
  for item in t:
   name=item.name.removeprefix('./')
   if not item.isfile():continue
   source=name.startswith('xnu/iokit/DriverKit/') and Path(name).suffix in ('.iig','.h')
   critical=name=='xnu/iokit/IOKit/IORPC.h'
   generated=name.startswith(GENERATED) and (name.endswith('.h') or name.endswith('.iig.cpp'))
   if not (source or critical or generated):continue
   if item.size>4*1024*1024:raise ValueError('Unexpected cache file size')
   data=t.extractfile(item).read()
   if source or critical:inputs[name.removeprefix('xnu/')]=digest(normalized(data))
   if generated:
    leaf=Path(name).name
    if leaf in outputs:raise ValueError('Duplicate generated file')
    (out/leaf).write_bytes(data);outputs[leaf]=digest(data)
 stems=sorted(Path(n).stem for n in inputs if n.endswith('.iig'))
 if len(stems)!=17 or len(outputs)!=34:raise ValueError('Unexpected IIG cache inventory')
 for stem in stems:
  if stem+'.h' not in outputs or stem+'.iig.cpp' not in outputs:raise ValueError('Incomplete generated pair')
 report={'source_commit':SOURCE_COMMIT,'artifact_zip_sha256':ARCHIVE_SHA256,'generator':'iig DriverKit-286, Xcode 15','configuration':{'MACOS_VERSION':'13.5','KERNEL_CONFIG':'DEVELOPMENT','MACHINE_CONFIG':'SWEET'},'input_sha256_lf':inputs,'output_sha256':outputs,'definitions':stems}
 (out/'manifest.json').write_text(json.dumps(report,indent=2))
 return report
def replay(arguments,cache):
 if '--' not in arguments:raise ValueError('Missing IIG frontend separator')
 split=arguments.index('--');front=arguments[split+1:]
 ap=argparse.ArgumentParser(allow_abbrev=False)
 ap.add_argument('--def',dest='definition',type=Path,required=True)
 ap.add_argument('--header',type=Path,required=True);ap.add_argument('--impl',type=Path,required=True)
 ap.add_argument('--framework-name',required=True)
 a=ap.parse_args(arguments[:split])
 if a.framework_name!='DriverKit' or a.definition.suffix!='.iig':raise ValueError('Unexpected IIG invocation')
 if not all(flag in front for flag in ('-D__IIG=1','-DDRIVERKIT_PRIVATE=1','-DPRIVATE_WIFI_ONLY=1')):raise ValueError('IIG configuration changed')
 m=json.loads((cache/'manifest.json').read_text())
 if m['artifact_zip_sha256']!=ARCHIVE_SHA256 or m['source_commit']!=SOURCE_COMMIT:raise ValueError('Cache provenance mismatch')
 for key,value in m['configuration'].items():
  if os.environ.get(key)!=value:raise ValueError('Unsupported frozen-IIG build configuration: '+key)
 source=a.definition.resolve().parents[2]
 if a.definition.resolve().parent.name!='DriverKit' or a.definition.resolve().parent.parent.name!='iokit':raise ValueError('Unexpected definition path')
 stem=a.definition.stem
 if stem not in m['definitions']:raise ValueError('Unknown IIG definition')
 # Include all input definitions and sibling public headers, not only this file.
 for name,expected in m['input_sha256_lf'].items():
  if digest(normalized((source/name).read_bytes()))!=expected:raise ValueError('Frozen IIG source input changed: '+name)
 copies=[]
 for dest,name in ((a.header,stem+'.h'),(a.impl,stem+'.iig.cpp')):
  if dest.name!=name or source in dest.resolve().parents:raise ValueError('Unexpected generated output path')
  data=(cache/name).read_bytes()
  if digest(data)!=m['output_sha256'][name]:raise ValueError('Cached IIG output changed: '+name)
  copies.append((dest,data))
 for dest,data in copies:
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 print('Pinned Xcode-15 IIG sources: '+stem)
def main():
 if sys.argv[1:2]==['stage']:
  ap=argparse.ArgumentParser();ap.add_argument('stage');ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
  m=stage(a.archive,a.out);print(json.dumps({'definitions':len(m['definitions']),'generated_files':len(m['output_sha256']),'artifact_zip_sha256':ARCHIVE_SHA256}))
 else:
  folder=os.environ.get('DUCHAMP_IIG_CACHE')
  if not folder:raise ValueError('DUCHAMP_IIG_CACHE is required')
  replay(sys.argv[1:],Path(folder))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError) as e:raise SystemExit('Frozen IIG refused: '+str(e))
