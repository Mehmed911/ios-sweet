"""0BSD read linked-object DWARF member locations, including anonymous records."""
import re


def parse(text):
    records, stack, current = {}, [], None
    for line in text.splitlines():
        m=re.match(r'^(0x[0-9a-f]+):(\s+)(DW_TAG_\w+)',line)
        if m:
            depth=(len(m[2])-1)//2
            current=dict(id=int(m[1],16),tag=m[3],attrs={},children=[])
            records[current['id']]=current
            while stack and stack[-1][0]>=depth:stack.pop()
            if stack:stack[-1][1]['children'].append(current['id'])
            stack.append((depth,current));continue
        m=re.search(r'DW_AT_(\w+)\s+\((.*)\)$',line)
        if m and current:
            value=m[2]
            if value.startswith('"'):value=value[1:-1]
            elif value.startswith('0x'):value=int(value.split()[0],16)
            current['attrs'][m[1]]=value
    return records


def layout(records,name):
    candidates=[r for r in records.values() if r['tag'] in ('DW_TAG_structure_type','DW_TAG_class_type','DW_TAG_union_type')
                and r['attrs'].get('name')==name and 'byte_size' in r['attrs']]
    if len(candidates)!=1:raise ValueError('ambiguous/missing concrete type: '+name)
    root=candidates[0];members={}
    def walk(r,base,seen):
        if r['id'] in seen:raise ValueError('recursive anonymous layout')
        for c in r['children']:
            child=records[c]
            if child['tag']!='DW_TAG_member':continue
            attrs=child['attrs'];off=attrs.get('data_member_location',0)
            if 'bit_size' in attrs or 'data_bit_offset' in attrs:continue
            if not isinstance(off,int) or off<0:raise ValueError('nonconstant member offset')
            label=attrs.get('name')
            if label:
                if label in members:raise ValueError('duplicate member')
                members[label]=base+off
            elif isinstance(attrs.get('type'),int):
                walk(records[attrs['type']],base+off,seen|{r['id']})
    walk(root,0,set())
    # Zero-length ABI padding arrays may be located exactly at the end.
    # Readers must separately validate the requested field width.
    if any(v>root['attrs']['byte_size'] for v in members.values()):raise ValueError('member outside type')
    return dict(bytes=root['attrs']['byte_size'],members=members,die=root['id'],declaration=root['attrs'].get('decl_file'))
