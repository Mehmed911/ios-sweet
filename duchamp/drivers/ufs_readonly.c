#include "ufs_readonly.h"

/* Wire fields are encoded explicitly: UFSHCI little endian, UPIU/SCSI big endian.
 * Independent implementation; register/packet references are in DRIVERS.md.
 */
enum { CAP=0, VER=8, IS=0x20, IE=0x24, HCS=0x30, HCE=0x34,
       LIST_LO=0x50, LIST_HI=0x54, DOORBELL=0x58, RUN=0x60,
       UIC=0x90, ARG1=0x94, ARG2=0x98, ARG3=0x9c };
static void clear(void *p, size_t n) { uint8_t *b=p; while(n--) *b++=0; }
static void copy(void *d, const void *s, size_t n) {
    uint8_t *a=d; const uint8_t *b=s; while(n--) *a++=*b++;
}
static void le32(uint8_t *p, uint32_t v) { for(int i=0;i<4;i++) p[i]=(uint8_t)(v>>(8*i)); }
static void be32(uint8_t *p, uint32_t v) { for(int i=0;i<4;i++) p[i]=(uint8_t)(v>>(24-8*i)); }
static void be64(uint8_t *p, uint64_t v) { for(int i=0;i<8;i++) p[i]=(uint8_t)(v>>(56-8*i)); }
static uint32_t getle32(const uint8_t *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
static uint64_t getbe(const uint8_t *p, size_t n) {
    uint64_t v=0; while(n--) v=(v<<8)|*p++; return v;
}
static uint32_t rd(struct dufs_host *h, uint32_t off) {
    return h->config.io.read32(h->config.io.context,off);
}
static void wr(struct dufs_host *h, uint32_t off, uint32_t v) {
    h->config.io.write32(h->config.io.context,off,v);
}
static void fence(struct dufs_host *h) { h->config.io.barrier(h->config.io.context); }
static uint64_t now(struct dufs_host *h) { return h->config.io.milliseconds(h->config.io.context); }
static int bad(struct dufs_host *h, int code) { h->state=3; return code; }
static int timeout(struct dufs_host *h,unsigned reason) {
    h->timeout_reason=(uint8_t)reason;return bad(h,DUFS_TIMEOUT);
}
static void begin(struct dufs_host *h) {
    h->poll_remaining=h->config.poll_limit;h->timeout_reason=DUFS_WAIT_NONE;
}
static int wait_bits(struct dufs_host *h, uint32_t off, uint32_t mask, uint32_t value) {
    uint64_t start=now(h);
    do {
        if(!h->poll_remaining) return timeout(h,DUFS_WAIT_POLLS);
        h->poll_remaining--;
        if((rd(h,off)&mask)==value) return 0;
    } while(now(h)-start < h->config.timeout_ms);
    return timeout(h,DUFS_WAIT_DEADLINE);
}
static int inside(uint64_t a, uint64_t n, uint64_t lo, uint64_t hi) {
    return lo<hi && a>=lo && a<hi && n<=hi-a;
}
static int separate(uint64_t a, uint64_t n, uint64_t b, uint64_t m) {
    return a<b ? n<=b-a : m<=a-b;
}
static int fits_bits(uint64_t a,uint64_t n,unsigned bits) {
    return bits && bits<=64 && n && n-1<=UINT64_MAX-a &&
        (bits==64 || !((a+n-1)>>bits));
}
size_t dufs_host_size(void) { return sizeof(struct dufs_host); }
unsigned dufs_timeout_cause(const struct dufs_host *h) { return h?h->timeout_reason:DUFS_WAIT_NONE; }
int dufs_bind(struct dufs_host *h, const struct dufs_config *c) {
    if(!h || !c) return DUFS_ARGUMENT;
    if(h->state) return DUFS_STATE;
    if(c->exclusive_platform_ready!=1) return DUFS_PLATFORM;
    if(!c->io.read32 || !c->io.write32 || !c->io.dma_write || !c->io.dma_read ||
       !c->io.barrier || !c->io.milliseconds || !c->timeout_ms ||
       c->timeout_ms>60000 || !c->poll_limit || c->poll_limit>DUFS_MAX_POLLS ||
       c->lun>7 || (c->list_dma&1023) ||
       (c->command_dma&127) || (c->data_dma&3)) return DUFS_ARGUMENT;
    const uint64_t a[]={c->list_dma,c->command_dma,c->data_dma};
    const uint64_t n[]={DUFS_LIST_BYTES,DUFS_COMMAND_BYTES,DUFS_MAX_TRANSFER};
    for(int i=0;i<3;i++) {
        if(!inside(a[i],n[i],c->dma_begin,c->dma_end)) return DUFS_ARGUMENT;
        if(!fits_bits(a[i],n[i],i==2?c->data_address_bits:c->descriptor_address_bits))
            return DUFS_ARGUMENT;
        for(int j=0;j<i;j++) if(!separate(a[i],n[i],a[j],n[j])) return DUFS_ARGUMENT;
    }
    struct dufs_config config=*c;
    clear(h,sizeof(*h)); h->config=config; h->state=1; return 0;
}
int dufs_start(struct dufs_host *h) {
    if(!h || h->state!=1) return DUFS_STATE;
    begin(h);
    /* Cold, exclusively assigned host only. Do not steal inherited queues. */
    if(rd(h,HCE) || rd(h,DOORBELL) || rd(h,RUN)) return bad(h,DUFS_STATE);
    uint32_t cap=rd(h,CAP);
    h->version=rd(h,VER);
    if(h->version<0x100 || h->version>0x4ff) return bad(h,DUFS_STATE);
    /* CAP64 is a separate controller ceiling. Check allocated extents, not
     * the end of a potentially much larger declared bus aperture. */
    if(!(cap&(1u<<24)) &&
       (!fits_bits(h->config.list_dma,DUFS_LIST_BYTES,32) ||
        !fits_bits(h->config.command_dma,DUFS_COMMAND_BYTES,32) ||
        !fits_bits(h->config.data_dma,DUFS_MAX_TRANSFER,32)))
        return bad(h,DUFS_ARGUMENT);
    wr(h,IE,0); wr(h,HCE,1);
    if(wait_bits(h,HCE,1,1) || wait_bits(h,HCS,8,8)) return DUFS_TIMEOUT;
    wr(h,IS,1u<<10); wr(h,ARG1,0); wr(h,ARG2,0); wr(h,ARG3,0);
    fence(h); wr(h,UIC,0x16); /* DME_LINK_STARTUP, not a MediaTek power sequence */
    if(wait_bits(h,IS,1u<<10,1u<<10)) return DUFS_TIMEOUT;
    if(rd(h,ARG2)&255) return bad(h,DUFS_RESPONSE);
    wr(h,IS,1u<<10);
    if(wait_bits(h,HCS,3,3)) return DUFS_TIMEOUT;
    if(h->config.io.dma_write(h->config.io.context,h->config.list_dma,h->list,sizeof(h->list)))
        return bad(h,DUFS_DMA);
    fence(h);
    wr(h,LIST_LO,(uint32_t)h->config.list_dma);
    wr(h,LIST_HI,(uint32_t)(h->config.list_dma>>32)); wr(h,RUN,1); fence(h);
    if(rd(h,LIST_LO)!=(uint32_t)h->config.list_dma ||
       rd(h,LIST_HI)!=(uint32_t)(h->config.list_dma>>32) || !(rd(h,RUN)&1))
        return bad(h,DUFS_STATE);
    h->state=2; return 0;
}
/* Only NOP, fDeviceInit queries, READ CAPACITY(16) and READ(16) reach this.
 * There is intentionally no public arbitrary-CDB or write interface.
 */
static int request(struct dufs_host *h, const uint8_t *cdb, uint32_t bytes, uint8_t query) {
    if(h->state!=2) return DUFS_STATE;
    if(!h->poll_remaining) return timeout(h,DUFS_WAIT_POLLS);
    if(!(rd(h,HCE)&1) || (rd(h,HCS)&3)!=3 || rd(h,DOORBELL) ||
       rd(h,LIST_LO)!=(uint32_t)h->config.list_dma ||
       rd(h,LIST_HI)!=(uint32_t)(h->config.list_dma>>32) || !(rd(h,RUN)&1))
        return bad(h,DUFS_STATE);
    clear(h->list,sizeof(h->list)); clear(h->command,sizeof(h->command));
    clear(h->data,bytes);
    if(++h->tag==0) ++h->tag;
    uint8_t *cmd=h->command, *d=h->list;
    cmd[0]=query?0x16:(cdb?1:0); cmd[1]=bytes?0x40:0;
    cmd[2]=cdb?h->config.lun:0; cmd[3]=h->tag;
    if(query) { cmd[5]=query==6?0x81:1; cmd[12]=query; cmd[13]=1; }
    if(cdb) { be32(cmd+12,bytes); copy(cmd+16,cdb,16); }
    le32(d,(1u<<28)|(bytes?(2u<<25):0)|(1u<<24)); le32(d+8,15);
    le32(d+16,(uint32_t)h->config.command_dma); le32(d+20,(uint32_t)(h->config.command_dma>>32));
    le32(d+24,(128u<<16)|128u); /* response offset/length in DWORDs */
    if(bytes) {
        le32(d+28,(256u<<16)|1u);
        le32(cmd+1024,(uint32_t)h->config.data_dma);
        le32(cmd+1028,(uint32_t)(h->config.data_dma>>32)); le32(cmd+1036,bytes-1);
    }
    struct dufs_io *io=&h->config.io;
    if(io->dma_write(io->context,h->config.command_dma,cmd,sizeof(h->command)) ||
       (bytes && io->dma_write(io->context,h->config.data_dma,h->data,bytes)) ||
       io->dma_write(io->context,h->config.list_dma,d,sizeof(h->list))) return bad(h,DUFS_DMA);
    fence(h); wr(h,DOORBELL,1);
    if(wait_bits(h,DOORBELL,1,0)) return DUFS_TIMEOUT;
    fence(h);
    if(io->dma_read(io->context,h->config.list_dma,d,32) ||
       io->dma_read(io->context,h->config.command_dma+512,cmd+512,512)) return bad(h,DUFS_DMA);
    const uint8_t *rsp=cmd+512;
    if((getle32(d+8)&255) || rsp[0]!=(query?0x36:(cdb?0x21:0x20)) ||
       rsp[2]!=(cdb?h->config.lun:0) || rsp[3]!=h->tag) return bad(h,DUFS_RESPONSE);
    if(cdb && rsp[7]) {
        /* A cold device may report UNIT ATTENTION (e.g. power-on/reset).
         * Only a valid fixed-format UNIT ATTENTION is retryable; every other
         * status or malformed sense response poisons this conservative core.
         */
        uint64_t segment=getbe(rsp+10,2), sense=getbe(rsp+32,2);
        if(rsp[7]==2 && rsp[6]<=1 && segment>=20 && segment<=480 &&
           sense>=18 && sense<=segment-2 &&
           ((rsp[34]&0x7f)==0x70 || (rsp[34]&0x7f)==0x71) && (rsp[36]&15)==6)
            return DUFS_SCSI;
        return bad(h,DUFS_SCSI);
    }
    if(rsp[6]) return bad(h,DUFS_RESPONSE);
    if(cdb && ((rsp[1]&0x60) || getbe(rsp+12,4))) return bad(h,DUFS_RESPONSE);
    if(bytes && io->dma_read(io->context,h->config.data_dma,h->data,bytes)) return bad(h,DUFS_DMA);
    wr(h,IS,1); return 0;
}
int dufs_nop(struct dufs_host *h) {
    if(!h)return DUFS_ARGUMENT;
    if(h->state!=2)return DUFS_STATE;
    begin(h);return request(h,0,0,0);
}
static int scsi_read(struct dufs_host *h, const uint8_t *cdb, uint32_t bytes) {
    for(int attempt=0;attempt<3;attempt++) {
        int r=request(h,cdb,bytes,0);
        if(r!=DUFS_SCSI || h->state!=2) return r;
        wr(h,IS,1); /* acknowledge the completed UNIT ATTENTION request */
    }
    return bad(h,DUFS_SCSI);
}
int dufs_device_init(struct dufs_host *h) {
    if(!h || h->state!=2 || h->device_ready) return DUFS_STATE;
    begin(h);
    int r=request(h,0,0,6); if(r) return r; /* SET_FLAG fDeviceInit, no user-data write */
    uint64_t start=now(h);
    do {
        r=request(h,0,0,5); if(r) return r; /* READ_FLAG */
        const uint8_t *rsp=h->command+512;
        if(rsp[12]!=5 || rsp[13]!=1) return bad(h,DUFS_RESPONSE);
        uint64_t value=getbe(rsp+20,4);
        if(!value) { h->device_ready=1; return 0; }
        if(value!=1) return bad(h,DUFS_RESPONSE);
        /* Every READ_FLAG request consumes the same operation-wide budget. */
    } while(now(h)-start<h->config.timeout_ms);
    return timeout(h,DUFS_WAIT_DEADLINE);
}
int dufs_capacity(struct dufs_host *h, uint64_t *blocks, uint32_t *block_bytes) {
    if(!h || !blocks || !block_bytes) return DUFS_ARGUMENT;
    if(h->state!=2 || !h->device_ready) return DUFS_STATE;
    begin(h);
    uint8_t cdb[16]={0x9e,0x10}; be32(cdb+10,32);
    int r=scsi_read(h,cdb,32); if(r) return r;
    uint64_t last=getbe(h->data,8); uint32_t size=(uint32_t)getbe(h->data+8,4);
    if(last==UINT64_MAX || size<512 || size>65536 || (size&(size-1))) return bad(h,DUFS_RESPONSE);
    h->blocks=last+1; h->block_bytes=size; *blocks=h->blocks; *block_bytes=size; return 0;
}
int dufs_read(struct dufs_host *h, uint64_t lba, uint32_t blocks, void *dest, size_t n) {
    if(!h || !dest || !blocks) return DUFS_ARGUMENT;
    if(h->state!=2 || !h->block_bytes) return DUFS_STATE;
    uint64_t bytes=(uint64_t)blocks*h->block_bytes;
    if(lba>=h->blocks || blocks>h->blocks-lba || bytes>DUFS_MAX_TRANSFER || bytes!=n)
        return DUFS_ARGUMENT;
    begin(h);
    uint8_t cdb[16]={0x88}; be64(cdb+2,lba); be32(cdb+10,blocks);
    int r=scsi_read(h,cdb,(uint32_t)bytes); if(r) return r;
    copy(dest,h->data,n); return 0;
}
