/* SPDX-License-Identifier: 0BSD */
/* Darwin ARM64 wire subset checked against this build's device_server.h. */
#ifndef DUCHAMP_IOKIT_WIRE_H
#define DUCHAMP_IOKIT_WIRE_H
typedef unsigned char dg_u8;
typedef unsigned short dg_u16;
typedef unsigned int dg_u32;
typedef unsigned long long dg_u64;
typedef unsigned long dg_size;
extern void *memcpy(void *, const void *, dg_size);
extern void *memset(void *, int, dg_size);
struct dg_head { dg_u32 bits,size,remote,local,voucher; int id; };
struct __attribute__((packed,aligned(4))) dg_port { dg_u32 name,pad; dg_u16 pad2; dg_u8 disposition,type; };
struct __attribute__((packed,aligned(4))) dg_ool { dg_u64 address; dg_u8 deallocate,copy,pad,type; dg_u32 size; };
struct __attribute__((packed,aligned(4))) dg_open {
    struct dg_head h; dg_u32 count; struct dg_port task; struct dg_ool properties;
    dg_u8 ndr[8]; dg_u32 type; dg_u8 property_ndr[8]; dg_u32 properties_count;
};
struct __attribute__((packed,aligned(4))) dg_map {
    struct dg_head h; dg_u32 count; struct dg_port task; dg_u8 ndr[8];
    dg_u32 type; dg_u64 address,size; dg_u32 flags;
};
_Static_assert(sizeof(struct dg_head)==24,"Mach header");
_Static_assert(sizeof(struct dg_port)==12,"Mach port descriptor");
_Static_assert(sizeof(struct dg_ool)==16,"Mach OOL descriptor");
_Static_assert(__builtin_offsetof(struct dg_ool,type)==11,"LP64 OOL descriptor type");
_Static_assert(__builtin_offsetof(struct dg_ool,size)==12,"LP64 OOL descriptor size");
_Static_assert(sizeof(struct dg_open)==80,"io_service_open_extended request");
_Static_assert(sizeof(struct dg_map)==72,"io_connect_map_memory_into_task request");
static inline dg_u32 dg_get32(const void *p) { dg_u32 v;memcpy(&v,p,4);return v; }
static inline dg_u64 dg_get64(const void *p) { dg_u64 v;memcpy(&v,p,8);return v; }
static inline void dg_put32(void *p,dg_u32 v) {memcpy(p,&v,4);}
static inline void dg_put64(void *p,dg_u64 v) {memcpy(p,&v,8);}
struct dg_event {dg_u64 timestamp,sender;dg_u32 type,usage_page,usage,down;};
/* Single consumer; producer uses release/acquire IOSharedDataQueue indices. */
static inline int dg_queue_pop(void *mapping,dg_u64 mapped,struct dg_event *event) {
    dg_u8 *p=mapping;
    if(!p || mapped<16 || ((unsigned long)p&3))return -1;
    dg_u32 size=dg_get32(p),head=__atomic_load_n((dg_u32 *)(p+4),__ATOMIC_ACQUIRE);
    dg_u32 tail=__atomic_load_n((dg_u32 *)(p+8),__ATOMIC_ACQUIRE);
    if(size<4 || size>mapped-12 || head>size || tail>size)return -1;
    if(head==tail)return 0;
    dg_u32 at=head;
    if(size-at<4 || dg_get32(p+12+at)>size-at-4) {
        if(tail>=head)return -1;
        at=0;
    }
    dg_u32 n=dg_get32(p+12+at);
    if(n<52 || n>size-at-4 || (at<tail && n+4>tail-at))return -1;
    const dg_u8 *data=p+16+at;
    dg_u32 attrs=dg_get32(data+20),count=dg_get32(data+24);
    if(!count || count>16 || attrs>n-28 || n-28-attrs<24)return -1;
    const dg_u8 *body=data+28+attrs;
    dg_u32 bytes=dg_get32(body);
    if(bytes<24 || bytes>n-28-attrs)return -1;
    event->timestamp=dg_get64(data);event->sender=dg_get64(data+8);
    event->type=dg_get32(body+4);
    dg_u16 page,usage;memcpy(&page,body+16,2);memcpy(&usage,body+18,2);
    event->usage_page=page;event->usage=usage;event->down=dg_get32(body+20);
    __atomic_store_n((dg_u32 *)(p+4),at+4+n,__ATOMIC_RELEASE);
    return 1;
}
#endif
