/* Pinned Linux parameter bodies with fixture globals; no kernel/firmware boot. */
#include <stdbool.h>
#include <stddef.h>
#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *,unsigned) __attribute__((noreturn));
int printf(const char *,...);
#define assert(x) ((x)?(void)0:model_assert_fail(#x,__LINE__))
static int strcmp(const char *a,const char *b) {
    while(*a && *a==*b){a++;b++;}return (unsigned char)*a-(unsigned char)*b;
}
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#endif
static unsigned checks,warnings;
#define CHECK(x) do{checks++;assert(x);}while(0)
#define __init
#define EINVAL 22
#define IO_TLB_SEGSIZE 128
#define ALIGN(x,a) (((x)+(a)-1)&~((a)-1))
#define isdigit(x) ((x)>='0' && (x)<='9')
#define pr_warn_once(...) ((void)warnings++)
#define WARN_ON(x) ((x)?(warnings++,true):false)
static bool swiotlb_force_bounce,swiotlb_force_disable,disable_dma32;
static unsigned long default_nslabs;
/* Numeric sizing is outside this fixture; it must never be called here. */
static unsigned long simple_strtoul(const char *s,char **end,unsigned base) {
    (void)s;(void)end;(void)base;CHECK(false);return 0;
}
static void swiotlb_adjust_nareas(unsigned long n){(void)n;CHECK(false);}
enum {KVM_MODE_DEFAULT,KVM_MODE_PROTECTED,KVM_MODE_NONE};
static unsigned kvm_mode;
static bool hyp_available,in_hyp;
static bool is_hyp_mode_available(void){return hyp_available;}
static bool is_kernel_in_hyp_mode(void){return in_hyp;}
#include "policy-reference.inc"

int main(void) {
    CHECK(setup_io_tlb_npages("noforce")==0);
    CHECK(swiotlb_force_disable && !swiotlb_force_bounce);
    CHECK(setup_io_tlb_npages("force")==0);
    CHECK(swiotlb_force_disable && swiotlb_force_bounce); /* sticky, not last wins */
    swiotlb_force_disable=swiotlb_force_bounce=false;
    CHECK(setup_io_tlb_npages("force")==0);
    CHECK(!swiotlb_force_disable && swiotlb_force_bounce);
    CHECK(setup_io_tlb_npages("noforce")==0);
    CHECK(swiotlb_force_disable && swiotlb_force_bounce);
    swiotlb_force_disable=swiotlb_force_bounce=false;
    CHECK(setup_io_tlb_npages("")==0);
    CHECK(setup_io_tlb_npages("invalid")==0);
    CHECK(!swiotlb_force_disable && !swiotlb_force_bounce && !default_nslabs);
    CHECK(early_disable_dma32(NULL)==-EINVAL);
    CHECK(!disable_dma32);
    CHECK(early_disable_dma32("off")==0 && !disable_dma32);
    CHECK(early_disable_dma32("on")==0 && disable_dma32);
    CHECK(early_disable_dma32("off")==0 && disable_dma32); /* does not undo */
    CHECK(early_disable_dma32("ON")==0 && disable_dma32);
    CHECK(early_kvm_mode_cfg(NULL)==-EINVAL);
    for(unsigned available=0;available<2;available++)for(unsigned vhe=0;vhe<2;vhe++) {
        hyp_available=available;in_hyp=vhe;kvm_mode=KVM_MODE_DEFAULT;warnings=0;
        CHECK(early_kvm_mode_cfg("protected")==0);
        CHECK(kvm_mode==((available && !vhe)?KVM_MODE_PROTECTED:KVM_MODE_DEFAULT));
        CHECK(warnings==((!available || vhe)?1u:0u));
        CHECK(early_kvm_mode_cfg("none")==0 && kvm_mode==KVM_MODE_NONE);
        kvm_mode=KVM_MODE_DEFAULT;warnings=0;
        CHECK(early_kvm_mode_cfg("nvhe")==((available && vhe)?-EINVAL:0));
        CHECK(kvm_mode==KVM_MODE_DEFAULT);
        CHECK(warnings==((!available || vhe)?1u:0u));
        CHECK(early_kvm_mode_cfg("invalid")==(!available?0:-EINVAL));
    }
    printf("%u saved boot-policy checks passed\n",checks);return 0;
}
