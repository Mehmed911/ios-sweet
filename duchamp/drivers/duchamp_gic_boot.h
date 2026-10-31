#ifndef DUCHAMP_GIC_BOOT_H
#define DUCHAMP_GIC_BOOT_H
/* Bounded GICR bootstrap algorithms. Callbacks must return. This validates
 * extents, not secure ownership or the accessibility of physical MMIO.
 * GICR stride/affinity follows the pinned Linux GICv3 implementation; see
 * duchamp/MT6897-BOOT-PLATFORM.md. No distributor/ICC configuration here.
 */
#include <stdint.h>
#define DGIC_FRAME UINT64_C(0x10000)
#define DGIC_MAX_FRAMES 256u
#define DGIC_MAX_POLLS 1000000u
enum dgic_result {DGIC_OK=0,DGIC_ARGUMENT=-1,DGIC_RANGE=-2,DGIC_IO=-3,
                  DGIC_NOT_FOUND=-4,DGIC_LIMIT=-5,DGIC_TIMEOUT=-6,DGIC_ID=-7};
enum dgic_timeout {DGIC_WAIT_NONE=0,DGIC_WAIT_CLOCK=1,DGIC_WAIT_POLLS=2};
struct dgic_io {
    void *context;
    int (*read32)(void *,uint64_t,uint32_t *);
    int (*read64)(void *,uint64_t,uint64_t *);
    int (*write32)(void *,uint64_t,uint32_t);
    uint64_t (*nanoseconds)(void *);
    void (*barrier)(void *);
};
struct dgic_wake_result {uint32_t initial,last,reads,writes,timeout_cause;};

static inline int dgic_regions_valid(uint64_t soc,uint64_t d,uint64_t ds,uint64_t r,uint64_t rs) {
    if(d>UINT64_MAX-soc || r>UINT64_MAX-soc)return 0;
    d+=soc;r+=soc;
    if(!d || !r || (d&(DGIC_FRAME-1)) || (r&(DGIC_FRAME-1)) ||
       ds<DGIC_FRAME || rs<2*DGIC_FRAME || (ds&(DGIC_FRAME-1)) || (rs&(DGIC_FRAME-1)) ||
       ds>UINT64_MAX-d || rs>UINT64_MAX-r || rs>DGIC_MAX_FRAMES*4*DGIC_FRAME)return 0;
    return d<r?ds<=r-d:rs<=d-r;
}
static inline uint32_t dgic_affinity(uint64_t mpidr) {
    return (uint32_t)(mpidr&UINT64_C(0xffffff)) | (uint32_t)((mpidr>>8)&UINT64_C(0xff000000));
}
static inline int dgic_find(const struct dgic_io *io,uint64_t bytes,uint64_t stride,
                           uint64_t mpidr,unsigned frames,uint64_t *found) {
    if(!io || !io->read32 || !io->read64 || !found || !frames || frames>DGIC_MAX_FRAMES)return DGIC_ARGUMENT;
    if(bytes<2*DGIC_FRAME || (bytes&(DGIC_FRAME-1)) ||
       (stride && (stride<2*DGIC_FRAME || (stride&(DGIC_FRAME-1)))))return DGIC_RANGE;
    uint32_t pidr2;
    if(io->read32(io->context,0xffe8,&pidr2))return DGIC_IO;
    if((pidr2&0xf0)!=0x30 && (pidr2&0xf0)!=0x40)return DGIC_ID;
    uint64_t offset=0;
    for(unsigned n=0;n<frames;n++) {
        if(offset>bytes-2*DGIC_FRAME)return DGIC_RANGE;
        uint64_t typer;
        if(io->read64(io->context,offset+8,&typer))return DGIC_IO;
        uint64_t span=(typer&2)?4*DGIC_FRAME:2*DGIC_FRAME;
        uint64_t step=stride?stride:span;
        if(step<span || span>bytes-offset || step>UINT64_MAX-offset)return DGIC_RANGE;
        if((uint32_t)(typer>>32)==dgic_affinity(mpidr)){*found=offset;return DGIC_OK;}
        if(typer&16)return DGIC_NOT_FOUND;
        if(step>=bytes-offset)return step==bytes-offset?DGIC_NOT_FOUND:DGIC_RANGE;
        offset+=step;
    }
    return DGIC_LIMIT;
}
static inline int dgic_wake(const struct dgic_io *io,uint64_t bytes,uint64_t pe,
                           uint64_t timeout_ns,uint32_t polls,struct dgic_wake_result *result) {
    if(!io || !io->read32 || !io->write32 || !io->nanoseconds || !io->barrier || !result ||
       timeout_ns>UINT64_C(60000000000) || !polls || polls>DGIC_MAX_POLLS)return DGIC_ARGUMENT;
    if(bytes<2*DGIC_FRAME || (pe&(DGIC_FRAME-1)) || pe>bytes-2*DGIC_FRAME)return DGIC_RANGE;
    struct dgic_wake_result d={0,0,0,0,0};
    uint64_t start=io->nanoseconds(io->context);
    int status=DGIC_TIMEOUT;
    while(d.reads<polls) {
        d.reads++;
        if(io->read32(io->context,pe+0x14,&d.last)){status=DGIC_IO;break;}
        if(d.reads==1) {
            d.initial=d.last;
            if(d.last&2) {
                d.writes=1;
                if(io->write32(io->context,pe+0x14,d.last&~2u)){status=DGIC_IO;break;}
                io->barrier(io->context);
            } else if(!(d.last&4)){status=DGIC_OK;break;}
        } else if(!(d.last&6)){status=DGIC_OK;break;}
        if(timeout_ns && io->nanoseconds(io->context)-start>=timeout_ns){d.timeout_cause=DGIC_WAIT_CLOCK;break;}
    }
    if(status==DGIC_TIMEOUT && !d.timeout_cause)d.timeout_cause=DGIC_WAIT_POLLS;
    *result=d;return status;
}
#endif
