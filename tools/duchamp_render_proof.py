"""0BSD conservative first-frame predicates; never infer ownership from pixels."""
def direct_springboard_owner(owner,identities):
    return bool(owner and owner.get('name')=='SpringBoard' and
                (owner.get('pid'),owner.get('birth')) in identities)

def matching_pixels(source,frame,surface,display,a,b):
    """Reproduce the existing CPU-copy clipping, with strict source bounds.

    Only BGRA/4-byte surfaces are eligible here. This checks a copy, not the
    authenticity of the process which produced its contents.
    """
    w,h=surface['width'],surface['height'];stride=surface['bytesPerRow'];offset=surface['offset']
    fw,fh,fs=display['fWidth'],display['fHeight'],display['fRowBytes']
    if (surface['pixelFormat']!=0x42475241 or not 0<w<=16384 or not 0<h<=16384 or
        stride<w*4 or len(source)!=surface['allocSize'] or not 0<=offset<=len(source) or
        fw<=0 or fh<=0 or fs<fw*4 or len(frame)!=fs*fh):return False
    sx,sy=a[:2];dx,dy,cw,ch=b
    if cw<=0 or ch<=0:cw,ch=w,h
    if sx<0 or sy<0:sx=sy=0
    if dx<0 or dy<0:dx=dy=0
    signed=lambda x:x-(1<<32) if x&(1<<31) else x
    dx-=signed(display['fOffX']);dy-=signed(display['fOffY'])
    if dx<0:sx-=dx;cw+=dx;dx=0
    if dy<0:sy-=dy;ch+=dy;dy=0
    cw=min(cw,w-sx,fw-dx);ch=min(ch,h-sy,fh-dy)
    if cw<=0 or ch<=0:return False
    end=offset+(sy+ch-1)*stride+(sx+cw)*4
    if end>len(source):return False
    return all(source[offset+(sy+y)*stride+sx*4:offset+(sy+y)*stride+(sx+cw)*4]==
               frame[(dy+y)*fs+dx*4:(dy+y)*fs+(dx+cw)*4] for y in range(ch))

def eligible(events,owner,surface_id):
    identities={(e['pid'],e['birth']) for e in events if e['kind']=='original_main' and e.get('name')=='SpringBoard'
                and e.get('uuid')=='40EC75F076C13DEB85F139369B09E9D5'}
    if not direct_springboard_owner(owner,identities) or not surface_id:return False
    pid,birth=owner['pid'],owner['birth']
    return (any(e['kind']=='context_commit' and (e.get('pid'),e.get('birth'))==(pid,birth) for e in events) and
        any(e['kind']=='surface_method' and e.get('selector')==0 and e.get('caller_task_matches') is True and
            (e.get('pid'),e.get('birth'))==(pid,birth) for e in events) and
        any(e['kind']=='surface_method_return' and e.get('selector')==0 and e.get('result')==0 and
            e.get('surface_id')==surface_id and (e.get('pid'),e.get('birth'))==(pid,birth) for e in events))
