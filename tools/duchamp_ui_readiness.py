"""Require witnessed native operations, not lookup/liveness or unverified flags."""
import math
import re


def registry(text,require_app=False):
    callback=re.findall(r'(?m)^REGISTRY REBUILD RESULT callback=(\d+) transport_error=(\d+) rebuilt=(\d+) code=(-?\d+)$',text)
    samples=re.findall(r'(?m)^REGISTRY AFTER sample=(\d+) witnessed=(\d+) status=(\d+) complete=(\d+)$',text)
    last=samples[-1] if samples else None
    status=int(last[2]) if last else None
    bit_complete=status is not None and 0<=status<=0xffffffff and bool(status&0x100) and not status&0x200
    valid=callback==[('1','0','1','0')] and last is not None and last[1]=='1' and last[3]=='1' and bit_complete
    valid=bool(valid and text.count('REGISTRY NATIVE COMPLETE PASS\n')==1 and
        re.findall(r'(?m)^READINESS DONE kind=registry status=(-?\d+)$',text)==['0'] and 'REGISTRY STATUS ERROR' not in text)
    app=re.findall(r'(?m)^REGISTRY APP identifier=com\.apple\.springboard installed=1 placeholder=0 path=/System/Library/CoreServices/SpringBoard\.app$',text)
    app_valid=len(app)==1 and text.count('REGISTRY APP RECORD PASS\n')==1
    valid=valid and (not require_app or app_valid)
    return dict(verified=bool(valid),status=status,database_seeding_complete=bool(bit_complete),
        springboard_record_verified=app_valid,
        inventory_of_stock_apps_verified=False)


def display(text):
    rows=re.findall(r'(?m)^DISPLAY NATIVE REPLY sample=(\d+) kr=(-?\d+) values=([^\n ]+) flags=(\d+),(\d+) valid=(\d+)$',text)
    valid=len(rows)==2 and [row[0] for row in rows]==['0','1']
    parsed=[]
    for row in rows:
        try:values=[float(value) for value in row[2].split(',')]
        except ValueError:values=[]
        good=row[1]=='0' and row[3] in ('0','1') and row[4] in ('0','1') and row[5]=='1'
        good=good and len(values)==4 and all(math.isfinite(value) and 0<value<=16384 for value in values[:3])
        good=good and len(values)==4 and math.isfinite(values[3]) and 0<=values[3]<=16384
        valid=valid and good
        parsed.append(dict(sample=int(row[0]),kernel_return=int(row[1]),values=values,valid=bool(good)))
    valid=bool(valid and text.count('DISPLAY NATIVE QUERY PASS\n')==1 and
        re.findall(r'(?m)^READINESS DONE kind=display status=(-?\d+)$',text)==['0'])
    return dict(verified=valid,replies=parsed,rendering_verified=False)
