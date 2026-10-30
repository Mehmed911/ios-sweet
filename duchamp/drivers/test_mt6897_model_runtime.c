/* QEMU virt MODEL TEST ONLY. Not a phone boot image or hardware backend. */
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
extern int main(void);

static void put(char c) {
    volatile uint32_t *uart=(void *)0x09000000ull; /* QEMU virt PL011 */
    while(uart[6]&(1u<<5)) {}
    uart[0]=(unsigned char)c;
}
static void text(const char *s) { while(*s) put(*s++); }
static void number(unsigned n) {
    char buf[10]; unsigned i=0;
    do { buf[i++]=(char)('0'+n%10); n/=10; } while(n);
    while(i) put(buf[--i]);
}
static void finish(uint64_t code) __attribute__((noreturn));
static void finish(uint64_t code) {
    uint64_t block[2]={0x20026,code};
    register uint64_t op __asm__("x0")=0x20; /* semihost SYS_EXIT_EXTENDED */
    register uint64_t arg __asm__("x1")=(uintptr_t)block;
    __asm__ volatile("hlt #0xf000" : "+r"(op),"+r"(arg) :: "memory");
    for(;;) __asm__ volatile("wfe");
}
void model_assert_fail(const char *expression,unsigned line) {
    text("MT6897 ARM64 MODEL FAIL line "); number(line); text(": ");
    text(expression); put('\n'); finish(1);
}
void *memcpy(void *dst,const void *src,size_t n) {
    unsigned char *d=dst; const unsigned char *s=src;
    for(size_t i=0;i<n;i++) d[i]=s[i];
    return dst;
}
void *memset(void *dst,int c,size_t n) {
    unsigned char *d=dst;
    for(size_t i=0;i<n;i++) d[i]=(unsigned char)c;
    return dst;
}
int memcmp(const void *a,const void *b,size_t n) {
    const unsigned char *x=a,*y=b;
    for(size_t i=0;i<n;i++) if(x[i]!=y[i]) return (int)x[i]-(int)y[i];
    return 0;
}
int printf(const char *format,...) {
    va_list args; va_start(args,format);
    while(*format) {
        if(*format!='%') put(*format++);
        else {
            format++;
            if(*format++!='u') model_assert_fail("unsupported test format",__LINE__);
            number(va_arg(args,unsigned));
        }
    }
    va_end(args); return 0;
}
void model_entry(void) {
    if(main()) finish(1);
    text("MT6897 ARM64 MODEL PASS\n"); finish(0);
}
void model_exception(uint64_t esr,uint64_t elr,uint64_t far) {
    uint64_t values[]={esr,elr,far};
    text("MT6897 ARM64 MODEL EXCEPTION ESR/ELR/FAR ");
    for(unsigned i=0;i<3;i++) {
        for(int shift=60;shift>=0;shift-=4) put("0123456789abcdef"[(values[i]>>shift)&15]);
        put(' ');
    }
    put('\n'); finish(1);
}
