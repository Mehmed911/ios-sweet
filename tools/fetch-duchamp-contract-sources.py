#!/usr/bin/env python3
"""Fetch the public, pinned evidence catalog; never overwrite differing files."""
import argparse,hashlib,json,re,urllib.request
from pathlib import Path,PurePosixPath

def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args()
    repo=Path(__file__).resolve().parent.parent;out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    entries=json.loads((repo/'duchamp/drivers/mt6897-contract-sources.json').read_text())['files']
    for e in entries:
        rel=PurePosixPath(e['path'])
        if rel.is_absolute() or '..' in rel.parts or '\\' in e['path']:raise ValueError('unsafe source path')
        if not re.fullmatch(r'[\w.-]+/[\w.-]+',e['repository']) or not re.fullmatch(r'[0-9a-f]{40}',e['commit']):
            raise ValueError('invalid repository/commit pin')
        target=out/e['path']
        if target.exists():
            if blob(target.read_bytes())!=e['git_blob']:raise ValueError('preserve differing source: '+e['path'])
            continue
        url='https://raw.githubusercontent.com/'+e['repository']+'/'+e['commit']+'/'+e['path']
        with urllib.request.urlopen(url,timeout=30) as response:data=response.read(8*1024*1024+1)
        if len(data)>8*1024*1024 or blob(data)!=e['git_blob']:raise ValueError('download Git blob mismatch')
        data.decode('utf-8');target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)
    print(str(len(entries))+' pinned source files verified; differing files never overwritten')
if __name__=='__main__':main()
