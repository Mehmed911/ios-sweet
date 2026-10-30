#!/usr/bin/env python3
"""Test actual adapter function bodies with instrumented UIO/allocation/lock stubs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def function(text,name):
    start=text.index('static int '+name+'(')
    opening=text.index('{',start); depth=1; pos=opening+1
    while depth:
        if text[pos]=='{': depth+=1
        if text[pos]=='}': depth-=1
        pos+=1
    return text[start:pos]+'\n'


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('output',type=Path)
    args=ap.parse_args(); out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent
    source=repo/'duchamp/xnu/qemu_ufs.c'; code=source.read_text()
    test=repo/'duchamp/xnu/test_uio_model.c'
    functions=function(code,'qu_error')+function(code,'qu_read')
    (out/'adapter-functions.inc').write_text(functions)
    binary=out/'uio-tests'
    subprocess.run(['clang','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
        '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(out),str(test),'-o',str(binary)],check=True)
    r=subprocess.run([str(binary)],check=True,capture_output=True,text=True)
    (out/'sanitizer.log').write_text(r.stdout+r.stderr)
    report={'passed':True,'result':r.stdout.strip(),'adapter_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'function_sha256':hashlib.sha256(functions.encode()).hexdigest(),
        'test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),
        'scope':'actual function bodies + instrumented host stubs; guest test still required for XNU/PAN'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))


if __name__=='__main__': main()
