"""0BSD classify a bounded original-process trace, never mint a GPU device."""
BACKBOARD_UUID='E81FD7FD034F3195A4F53C692536E5AA'
def classify(events):
    if any(e.get('kind')=='trace_error' for e in events):return dict(status='TRACE_ERROR',first_frame_verified=False)
    sequence=[e.get('sequence') for e in events]
    if any(type(s) is not int or s<=0 for s in sequence) or sequence!=sorted(set(sequence)):
        return dict(status='INSUFFICIENT_TRACE',first_frame_verified=False)
    ids={(e.get('pid'),e.get('birth')) for e in events if e.get('kind')=='original_main' and
         e.get('name')=='backboardd' and e.get('uuid')==BACKBOARD_UUID}
    ids &= {(e.get('pid'),e.get('birth')) for e in events if e.get('kind')=='original_image_bound' and
            e.get('name')=='backboardd' and e.get('uuid')==BACKBOARD_UUID}
    for start in events:
        key=(start.get('pid'),start.get('birth'))
        if start.get('kind')!='mtl_register_entry' or key not in ids:continue
        rows=[e for e in events if (e.get('pid'),e.get('birth'))==key and e.get('tid')==start.get('tid') and e['sequence']>start['sequence']]
        found={};last=start['sequence']
        bound=any(e.get('kind')=='cache_bound' and (e.get('pid'),e.get('birth'))==key and
                  e.get('cache_uuid')=='E5420DB330D033AA8B7E05B5038BB46D' for e in events)
        for kind in ['mtl_master_return','io_matching_return','mtl_services_return','io_iterator_next_return']:
            alternatives={kind}
            # Fixed mid-function sites are opcode-bound to the reviewed 20F66
            # MTLRegisterDevices call sequence. Its matching literal is
            # IOAcceleratorES. They survive the separate generic-IOKit log cap.
            if bound and kind=='io_matching_return':alternatives.add('mtl_match_dict_return')
            if bound and kind=='io_iterator_next_return':alternatives.add('mtl_iterator_return')
            candidates=[e for e in rows if e['kind'] in alternatives and e['sequence']>last]
            if kind=='io_matching_return':candidates=[e for e in candidates if e['kind']=='mtl_match_dict_return' or e.get('request',{}).get('class_name')=='IOAcceleratorES']
            if kind=='io_iterator_next_return':candidates=[e for e in candidates if e['kind']=='mtl_iterator_return' or e.get('request',{}).get('class_name')=='IOAcceleratorES' and
                    e['request']['arguments'][0]==found['mtl_services_return'].get('iterator')]
            if not candidates:break
            e=candidates[0];found[kind]=e;last=e['sequence']
            value=e.get('result',e.get('arguments',[None])[0])
            if kind!='io_matching_return' and value is not None:value &= 0xffffffff
            interface=None;reason=None
            if kind=='mtl_master_return' and value:interface='IOMasterPort';reason='nonzero kernel return'
            elif kind=='io_matching_return' and not value:interface='IOServiceMatching';reason='null matching dictionary'
            elif kind=='mtl_services_return' and value:interface='IOServiceGetMatchingServices';reason='nonzero kernel return'
            elif kind=='io_iterator_next_return' and value==0:interface='IOIteratorNext';reason='iterator contains no IOAcceleratorES service'
            if interface:
                next_value=value if kind=='io_iterator_next_return' else None
                if kind=='io_iterator_next_return' and found['mtl_services_return'].get('iterator')==0:
                    interface='IOServiceGetMatchingServices'
                    reason='successful query returned MACH_PORT_NULL; no published IOAcceleratorES iterator'
                return dict(status='DISCOVERY_BLOCKER_VERIFIED',first_frame_verified=False,process=dict(pid=key[0],birth=key[1],name='backboardd'),
                    interface=interface,return_value=value,reason=reason,class_name='IOAcceleratorES',
                    subsequent_iterator_next=next_value,
                    matching_query_return=found.get('mtl_services_return',{}).get('arguments',[None])[0],
                    iterator=found.get('mtl_services_return',{}).get('iterator'),evidence_sequences=[start['sequence']]+[e['sequence'] for e in found.values()],
                    capability_validation_proven=False,command_submission_proven=False)
    return dict(status='INSUFFICIENT_TRACE',first_frame_verified=False)
