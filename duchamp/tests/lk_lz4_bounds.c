/* Exercise the saved LK decoder in QEMU Normal RAM with real guard pages.
 * This program does not boot LK/XNU or establish physical-device ownership.
 */
#include <stdint.h>
#include <stddef.h>
#include "fixture.h"

#define INPUT_END UINT64_C(0x43000000)
#define OUTPUT_END UINT64_C(0x46000000)
#define FRAME ((const volatile unsigned char *)UINT64_C(0x60000000))
#define REFERENCE ((const volatile unsigned char *)UINT64_C(0x68000000))
#define CAPACITY UINT64_C(0x800000)
#define SENTINEL 0xa5

static uint64_t l1[512] __attribute__((aligned(4096)));
static uint64_t l2[512] __attribute__((aligned(4096)));
static uint64_t input_l3[512] __attribute__((aligned(4096)));
static uint64_t output_l3[512] __attribute__((aligned(4096)));
static volatile unsigned completed;
static volatile unsigned expected_fault;

static void host(unsigned long op, const void *p) {
    register unsigned long x0 __asm__("x0") = op;
    register const void *x1 __asm__("x1") = p;
    __asm__ volatile("hlt #0xf000" : "+r"(x0) : "r"(x1) : "memory");
}
static void text(const char *s) { host(4, s); }
static void number(uint64_t n) {
    char b[24]; unsigned k=23; b[k]=0;
    do { b[--k]=(char)('0'+n%10); n/=10; } while(n);
    text(b+k);
}
static void hex(uint64_t n) {
    char b[19]; const char *digits="0123456789abcdef";
    b[0]='0'; b[1]='x'; b[18]=0;
    for(unsigned i=0;i<16;i++) b[17-i]=digits[(n>>(i*4))&15];
    text(b);
}
__attribute__((noreturn)) static void finish(unsigned code) {
    unsigned long block[2]={0x20026,code};
    host(0x20,block);
    for(;;) __asm__ volatile("wfe");
}
__attribute__((noreturn)) static void fail(unsigned code) {
    text("FAIL code="); number(code); text("\n"); finish(code);
}

void test_mmu_setup(void) {
    /* Only the QEMU RAM bank is mapped. The two end pages are invalid. */
    for(unsigned i=0;i<512;i++) {
        l1[i]=0;
        l2[i]=(UINT64_C(0x40000000)+((uint64_t)i<<21))|0x701;
        input_l3[i]=(INPUT_END+((uint64_t)i<<12))|0x703;
        output_l3[i]=(OUTPUT_END+((uint64_t)i<<12))|0x703;
    }
    input_l3[0]=0; output_l3[0]=0;
    l2[(INPUT_END-UINT64_C(0x40000000))>>21]=(uint64_t)input_l3|3;
    l2[(OUTPUT_END-UINT64_C(0x40000000))>>21]=(uint64_t)output_l3|3;
    l1[1]=(uint64_t)l2|3;
    uint64_t mair=0xff, tcr=UINT64_C(0x200003519), sctlr;
    __asm__ volatile("msr mair_el1, %0"::"r"(mair):"memory");
    __asm__ volatile("msr ttbr0_el1, %0"::"r"(l1):"memory");
    __asm__ volatile("msr ttbr1_el1, xzr; msr tcr_el1, %0; dsb sy; tlbi vmalle1; dsb sy; isb"::"r"(tcr):"memory");
    __asm__ volatile("mrs %0, sctlr_el1":"=r"(sctlr));
    sctlr=(sctlr&~UINT64_C(2))|0x1005;
    __asm__ volatile("msr sctlr_el1, %0; isb"::"r"(sctlr):"memory");
}

static int run(unsigned block, uint64_t capacity, unsigned truncate, int should_fail) {
    uint64_t size=fixture_blocks[block].compressed-truncate;
    uint64_t wanted=fixture_blocks[block].expanded;
    volatile unsigned char *input=(volatile unsigned char *)(INPUT_END-size);
    volatile unsigned char *output=(volatile unsigned char *)(OUTPUT_END-capacity);
    for(uint64_t j=0;j<size;j++) input[j]=FRAME[fixture_blocks[block].offset+j];
    for(unsigned j=1;j<=64;j++) input[-(int)j]=SENTINEL;
    for(uint64_t j=0;j<capacity;j++) output[j]=SENTINEL;
    for(unsigned j=1;j<=64;j++) output[-(int)j]=SENTINEL;
    int (*decoder)(const void *,void *,int,int)=
        (int (*)(const void *,void *,int,int))UINT64_C(0x50758f20);
    int got=decoder((const void *)input,(void *)output,(int)size,(int)capacity);
    for(unsigned j=1;j<=64;j++) if(input[-(int)j]!=SENTINEL || output[-(int)j]!=SENTINEL) fail(31);
    for(uint64_t j=0;j<size;j++) if(input[j]!=FRAME[fixture_blocks[block].offset+j]) fail(32);
    if(should_fail) {
        if(got>=0) fail(33);
    } else {
        if(got<0 || (uint64_t)got!=wanted) fail(34);
        for(uint64_t j=0;j<wanted;j++) if(output[j]!=REFERENCE[fixture_blocks[block].logical+j]) fail(35);
        if(block==6 && capacity>wanted) {
            uint64_t count=0,first=capacity,last=0;
            for(uint64_t j=wanted;j<capacity;j++) if(output[j]!=SENTINEL) {
                if(first==capacity) first=j; last=j; count++;
            }
            if(count!=4 || first!=wanted || last!=wanted+3) fail(39);
            for(unsigned j=0;j<4;j++) if(output[wanted+j]!=0) fail(40);
            text("TAIL changed="); number(count); text(" first="); number(first); text(" last="); number(last); text("\n");
            text("TAIL four zero bytes from wide match copy verified\n");
        }
    }
    completed++;
    text("PASS case="); number(completed); text(" block="); number(block);
    text(" capacity="); number(capacity); text(" result=");
    if(got<0) {text("-"); number((uint64_t)(-(int64_t)got));} else number((uint64_t)got);
    text("\n");
    return got;
}

void test_main(void) {
    text("LK LZ4 guard regression; isolated QEMU only\n");
    for(unsigned i=0;i<7;i++) run(i,CAPACITY,0,0);
    run(6,fixture_blocks[6].expanded,0,0);
    run(6,fixture_blocks[6].expanded-1,0,1);
    run(0,CAPACITY-1,0,1);
    run(6,0,0,1);
    run(6,CAPACITY,1,1);
    if(completed!=12) fail(36);
    /* Negative fixture: claim 8 MiB but map only logical output bytes.
     * The first fast-copy tail write must fault on OUTPUT_END. */
    uint64_t size=fixture_blocks[6].compressed;
    volatile unsigned char *input=(volatile unsigned char *)(INPUT_END-size);
    volatile unsigned char *output=(volatile unsigned char *)(OUTPUT_END-fixture_blocks[6].expanded);
    for(uint64_t j=0;j<size;j++) input[j]=FRAME[fixture_blocks[6].offset+j];
    for(uint64_t j=0;j<fixture_blocks[6].expanded;j++) output[j]=SENTINEL;
    expected_fault=1;
    int (*decoder)(const void *,void *,int,int)=
        (int (*)(const void *,void *,int,int))UINT64_C(0x50758f20);
    decoder((const void *)input,(void *)output,(int)size,(int)CAPACITY);
    fail(37);
}

void test_fault(const uint64_t *registers) {
    uint64_t esr,pc,far;
    __asm__ volatile("mrs %0, esr_el1":"=r"(esr));
    __asm__ volatile("mrs %0, elr_el1":"=r"(pc));
    __asm__ volatile("mrs %0, far_el1":"=r"(far));
    text("FAULT pc=");hex(pc);text(" far=");hex(far);text(" esr=");hex(esr);text("\n");
    for(unsigned j=0;j<31;j++) {text(" x");number(j);text("=");hex(registers[j]);}
    text("\n");
    if(!expected_fault || completed!=12 || far!=OUTPUT_END ||
       (esr>>26)!=0x25 || !(esr&0x40) || (esr&0x3f)<4 || (esr&0x3f)>7 ||
       pc<UINT64_C(0x50758f20) || pc>=UINT64_C(0x50759238)) fail(38);
    text("PASS case=13 expected fast-copy tail guard fault\n");
    text("PASS 13/13; physical ownership unproven\n");
    finish(0);
}
