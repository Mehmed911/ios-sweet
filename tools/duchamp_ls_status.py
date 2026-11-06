"""Interpret the witnessed 20F66 unsigned LS session-status reply, not OSStatus."""
import re


def parse(text):
    reply=re.findall(r'(?m)^LSD NATIVE STATUS REPLY status=(\d+)$',text)
    result=re.findall(r'(?m)^LSD NATIVE QUERY RESULT reply=1 error=0 status=(\d+)$',text)
    wrapper=re.findall(r'(?m)^LSD NATIVE WRAPPER status=(\d+) matches=1$',text)
    passed=re.findall(r'(?m)^LSD NATIVE TRANSPORT PASS status=(\d+)$',text)
    values=reply+result+wrapper+passed
    valid=all(len(items)==1 for items in (reply,result,wrapper,passed)) and len(set(values))==1
    status=int(reply[0]) if valid else None
    valid=bool(valid and status is not None and 0<=status<=0xffffffff and 'LSD NATIVE QUERY ERROR' not in text)
    return dict(transport_verified=valid,status=status if valid else None,
        database_seeded=bool(valid and status&0x100),
        database_seeding_complete=bool(valid and status&0x100 and not status&0x200))
