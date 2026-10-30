#include "framebuffer.h"
/* This address is ordinary RAM in the test VM, not a scanout/GPU device. */
#define ADDRESS 0xfcc2f000UL
#define WIDTH 1220u
#define HEIGHT 2712u
#define STRIDE 4992u
static void line(const char *p) {
    volatile uint32_t *uart=(void *)0x09000000UL;
    while(*p) { while(uart[6]&(1u<<5)) {} uart[0]=(uint8_t)*p++; }
}
void test_framebuffer_arm(void) {
    uint64_t state,level;
    __asm__ volatile("mrs %0, CurrentEL" : "=r"(level));
    if(level!=4) { line("ARM FB FAIL exception level\n"); return; }
    __asm__ volatile("mrs %0, sctlr_el1" : "=r"(state));
    if(state&0x1005) { line("ARM FB FAIL MMU/cache state\n"); return; }
    volatile uint8_t *fb=(void *)ADDRESS;
    volatile uint8_t *guard=fb-64;
    for(size_t i=0;i<(size_t)STRIDE*HEIGHT+128;i++) guard[i]=0xa5;
    struct dfb_surface surface={fb,(size_t)STRIDE*HEIGHT,WIDTH,HEIGHT,STRIDE};
    uint8_t tile[64]; for(unsigned i=0;i<sizeof(tile);i++) tile[i]=(uint8_t)i;
    struct dfb_surface source={tile,sizeof(tile),4,4,16};
    if(dfb_fill(&surface,(struct dfb_rect){0,0,WIDTH,HEIGHT},0xff123456) ||
       dfb_blit(&surface,WIDTH-4,HEIGHT-4,&source,(struct dfb_rect){0,0,4,4})) {
        line("ARM FB FAIL drawing\n"); return;
    }
    __asm__ volatile("dsb sy" ::: "memory");
    line("ARM FB PASS EL1 MMU/cache off\n");
}
