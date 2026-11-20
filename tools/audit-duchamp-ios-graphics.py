#!/usr/bin/env python3
"""0BSD inspect actual HFS guest dependencies and original local launchd jobs."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
from duchamp_macho_preflight import closure, guest_path, inspect

REPO=Path(__file__).resolve().parents[1]
ENTRIES=['/usr/libexec/backboardd','/System/Library/CoreServices/SpringBoard.app/SpringBoard']
FRAMEWORKS=[
    '/System/Library/PrivateFrameworks/GraphicsServices.framework/GraphicsServices',
    '/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics',
    '/System/Library/Frameworks/QuartzCore.framework/QuartzCore',
    '/System/Library/Frameworks/IOSurface.framework/IOSurface',
    '/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit',
    '/System/Library/PrivateFrameworks/UIKitCore.framework/UIKitCore',
    '/System/Library/PrivateFrameworks/BackBoardHIDEventFoundation.framework/BackBoardHIDEventFoundation',
    '/System/Library/PrivateFrameworks/RunningBoardServices.framework/RunningBoardServices',
    '/System/Library/PrivateFrameworks/FrontBoardServices.framework/FrontBoardServices',
    '/System/Library/PrivateFrameworks/SpringBoard.framework/SpringBoard']


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--guest-image',type=Path,required=True)
    p.add_argument('--hfs-tool',type=Path,default=REPO/'research/libdmg-hfsplus-build/hfsplus')
    a=p.parse_args();out=a.output.resolve();out.mkdir()
    image=a.guest_image.resolve();before=sha(image)
    extracted=out/'guest-files';extracted.mkdir()
    commands=[];looked={}
    cache_index=REPO/'work/20F66-cache-v4/cache-info.json'
    index=json.loads(cache_index.read_text());cache={x['name']:x for x in index['dylibs']}

    def locate(guest):
        guest=guest_path(guest)
        if guest in looked:return looked[guest]
        dest=extracted/guest.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
        argv=list(map(str,[a.hfs_tool.resolve(),image,'extract',guest,dest]))
        r=subprocess.run(argv,capture_output=True,text=True)
        commands.append(dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        missing='No such file' in r.stdout+r.stderr or not dest.is_file()
        if r.returncode and not missing:raise RuntimeError(commands[-1])
        looked[guest]=None if missing else dest
        return looked[guest]

    entries={entry:closure(entry,locate,cache) for entry in ENTRIES}
    frameworks={}
    for guest in FRAMEWORKS:
        file=locate(guest)
        frameworks[guest]=dict(classification='REQUIRES_APPLE_COMPONENT' if guest in cache else 'UNKNOWN',
            guest_file_present=file is not None,host_cache_entry=cache.get(guest),execution_proven=False)
        if file:
            frameworks[guest]['macho']=inspect(file)
            frameworks[guest]['classification']='UNKNOWN' # presence is not API implementation
    jobs={}
    source=REPO/'work/ui-daemon-scan-v1/apple-extracted/System/Library/LaunchDaemons'
    for name in ['com.apple.backboardd.plist','com.apple.SpringBoard.plist']:
        f=source/name;job=plistlib.loads(f.read_bytes())
        jobs[name]=dict(source=str(f),sha256=sha(f),job=job,
                       declared_mach_services=list(job.get('MachServices',{})),
                       registered_in_this_guest=False,outbound_dependencies_proven=False)
    report=dict(guest_image=str(image),guest_sha256=before,guest_unchanged=sha(image)==before,
        entries=entries,frameworks=frameworks,jobs=jobs,commands=commands,
        host_cache_inventory=dict(path=str(cache_index),sha256=sha(cache_index),uuid=index['uuid'],images=len(cache),
          note='Offline inventory only; not proof that this guest mapped the cache or verified its contents'),
        scope=dict(physical_device=False,execution=False,closure_is_api_compatibility=False,signature_authentication=False))
    (out/'dependency-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(guest_unchanged=report['guest_unchanged'],entries={k:dict(complete=v['static_closure_complete'],
        files=len(v['files']),missing=len(v['missing']),first_missing=v['missing'][:1],invalid=v['invalid']) for k,v in entries.items()}),indent=2))
    return 0 if report['guest_unchanged'] else 1


if __name__=='__main__':raise SystemExit(main())
