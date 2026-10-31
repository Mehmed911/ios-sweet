#!/usr/bin/env python3
"""Fetch a pinned comparison firmware source; never identifies installed BL31."""
import argparse,base64,hashlib,json,urllib.request
from pathlib import Path
COMMIT='f3083e2e6c508d58f9bce1b2fce5eeb0903a4c6d'
BLOB='5cb9eb7f5f683a9d3c8f99be6dc209f27b7af266'
PATH='plat/mediatek/drivers/ufs/ufs_ctrl.c'
URL='https://chromium.googlesource.com/chromiumos/third_party/arm-trusted-firmware/+/'+COMMIT+'/'+PATH
def check(data):
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=BLOB:raise ValueError('reference source blob differs')
    return {'commit':COMMIT,'git_blob':BLOB,'path':PATH,'url':URL,'sha256':hashlib.sha256(data).hexdigest(),
            'installed_firmware_identity_verified':False}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing output')
    with urllib.request.urlopen(URL+'?format=TEXT',timeout=30) as response:raw=response.read(1024*1024+1)
    if len(raw)>1024*1024:raise ValueError('reference response too large')
    data=base64.b64decode(raw,validate=True);receipt=check(data)
    a.output.mkdir(parents=True,exist_ok=False);(a.output/'ufs_ctrl.c').write_bytes(data)
    (a.output/'source.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
