/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_DARWIN_IOKIT_H
#define DUCHAMP_DARWIN_IOKIT_H
#include "sweet-ipc.h"
#include "duchamp-iokit-wire.h"
#include "duchamp-iokit-contract.h"
extern dg_u32 mach_task_self_,mach_host_self(void);
extern int host_get_io_main(dg_u32,dg_u32 *),mach_port_allocate(dg_u32,int,dg_u32 *);
extern int mach_port_destroy(dg_u32,dg_u32),mach_port_deallocate(dg_u32,dg_u32);
extern int mach_msg(void *,dg_u32,dg_u32,dg_u32,dg_u32,dg_u32,dg_u32);
extern int usleep(unsigned int);
extern dg_u32 _dyld_image_count(void);
extern dg_u32 mig_get_reply_port(void);
extern void mig_dealloc_reply_port(dg_u32);
/* XNU mach/message.h mach_msg2(): explicitly identify kernel-object RPCs. */
extern int mach_msg2_internal(void *,dg_u64,dg_u64,dg_u64,dg_u64,dg_u64,dg_u64,dg_u64);
static const dg_u8 ndr[8]={0,0,0,0,1,0,0,0};
static unsigned char message[8192] __attribute__((aligned(8)));
static inline int rpc(dg_u32 port,int id,dg_u32 size,int complex) {
    if(!dg_object_valid(port) || size<24 || size>sizeof(message))return -1;
    dg_u32 reply=mig_get_reply_port();
    if(!reply)return -1;
    struct dg_head h={19u|(21u<<8)|(complex?0x80000000u:0),size,port,reply,0,id};
    memcpy(message,&h,24);
    int result=mach_msg2_internal(message,0x200000103ull,
        (dg_u64)size<<32|h.bits,(dg_u64)reply<<32|port,(dg_u64)(dg_u32)id<<32,
        (dg_u64)reply<<32|(complex?dg_get32(message+24):0),sizeof(message),3000);
    if(result){mig_dealloc_reply_port(reply);ipc_note("RPC id=%d transport=0x%x",id,result);return result;}
    struct dg_head *r=(void *)message;
    if(r->id!=id+100 || r->size<24 || r->size>sizeof(message))return -2;
    return 0;
}
static inline dg_u32 match(dg_u32 master,const char *name) {
    if(!dg_object_valid(master) || !name || !*name)return 0;
    char xml[300];int n=snprintf(xml,sizeof(xml),"<dict><key>IOProviderClass</key><string>%s</string></dict>",name);
    if(n<0 || (unsigned)n>=sizeof(xml))return 0;
    memset(message,0,sizeof(message));memcpy(message+24,ndr,8);
    dg_put32(message+32,(dg_u32)n+1);memcpy(message+36,xml,(dg_size)n+1);
    if(rpc(master,2880,36+((n+4)&~3),0))return 0;
    struct dg_head *r=(void *)message;
    if(!(r->bits&0x80000000u) || r->size!=40 || dg_get32(message+24)!=1) {
        ipc_note("MATCH_REPLY %s bits=%x bytes=%u result=%x",name,r->bits,r->size,dg_get32(message+32));return 0;
    }
    ipc_note("MATCH_SERVICE %s port=0x%x",name,dg_get32(message+28));
    return dg_get32(message+28);
}
static inline dg_u32 open_client(dg_u32 service,dg_u32 type) {
    if(!dg_object_valid(service))return 0;
    struct dg_open q={0};q.count=2;q.task.name=mach_task_self_;q.task.disposition=19;
    q.properties.type=1;q.properties.copy=1;q.type=type;
    memcpy(q.ndr,ndr,8);memcpy(q.property_ndr,ndr,8);memcpy(message,&q,sizeof(q));
    if(rpc(service,2862,sizeof(q),1))return 0;
    struct dg_head *r=(void *)message;
    if(!(r->bits&0x80000000u) || r->size!=52 || dg_get32(message+24)!=1 || dg_get32(message+48)) {
        ipc_note("OPEN type=%x size=%u result=%x",type,r->size,
            r->size==36?dg_get32(message+32):dg_get32(message+48));return 0;
    }
    return dg_get32(message+28);
}
static inline int method(dg_u32 connection,dg_u32 selector,const dg_u64 *scalars,dg_u32 count,
                  const void *input,dg_u32 inbytes,void *output,dg_u32 *outbytes,dg_u64 *out,dg_u32 *outcount) {
    if(!dg_object_valid(connection) ||
       !dg_method_request_valid(scalars,count,input,inbytes,output,outbytes,out,outcount))return -1;
    memset(message,0,sizeof(message));memcpy(message+24,ndr,8);
    dg_put32(message+32,selector);dg_put32(message+36,count);
    dg_u32 at=40;
    if(count){memcpy(message+at,scalars,count*8);at+=count*8;}
    dg_put32(message+at,inbytes);at+=4;
    if(inbytes)memcpy(message+at,input,inbytes);
    at+=(inbytes+3)&~3u;at+=16;
    dg_put32(message+at,outbytes?*outbytes:0);dg_put32(message+at+4,outcount?*outcount:0);at+=24;
    int rc=rpc(connection,2865,at,0);if(rc)return rc;
    struct dg_head *h=(void *)message;
    if(h->size<36 || (h->bits&0x80000000u))return -2;
    rc=(int)dg_get32(message+32);if(rc)return rc;
    if(h->size<40)return -3;
    dg_u32 bytes=dg_get32(message+36),maxbytes=outbytes?*outbytes:0;
    if(bytes>maxbytes || bytes>4096 || 40+((bytes+3)&~3u)+4>h->size)return -4;
    if(bytes)memcpy(output,message+40,bytes);
    at=40+((bytes+3)&~3u);
    dg_u32 n=dg_get32(message+at);at+=4;
    if(n>(outcount?*outcount:0) || n>16 || at+n*8+8>h->size)return -5;
    if(n)memcpy(out,message+at,n*8);
    if(outbytes)*outbytes=bytes;if(outcount)*outcount=n;
    return 0;
}
static inline int map_queue(dg_u32 connection,void **address,dg_u64 *size) {
    if(!dg_object_valid(connection) || !address || !size)return -1;
    struct dg_map q={0};q.count=1;q.task.name=mach_task_self_;q.task.disposition=19;q.flags=1;
    memcpy(q.ndr,ndr,8);memcpy(message,&q,sizeof(q));
    int rc=rpc(connection,2863,sizeof(q),1);if(rc)return rc;
    if(((struct dg_head *)message)->size!=52 || dg_get32(message+32))return -1;
    *address=(void *)(unsigned long)dg_get64(message+36);*size=dg_get64(message+44);
    return !*address || *size<16 || *size>1024*1024?-2:0;
}
static inline int notify(dg_u32 connection,dg_u32 port) {
    memset(message,0,sizeof(message));dg_put32(message+24,1);
    struct dg_port p={port,0,0,20,0};memcpy(message+28,&p,12);memcpy(message+40,ndr,8);
    int rc=rpc(connection,2818,56,1);return rc?rc:(int)dg_get32(message+32);
}
#endif
