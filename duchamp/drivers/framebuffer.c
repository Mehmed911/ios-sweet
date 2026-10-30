#include "framebuffer.h"
int dfb_validate(const struct dfb_surface *s) {
    if(!s || !s->pixels || !s->width || !s->height || (s->stride&3) ||
       s->width>UINT32_MAX/4 || s->stride<s->width*4 ||
       s->height>SIZE_MAX/s->stride || s->bytes<(size_t)s->height*s->stride ||
       s->bytes>UINTPTR_MAX-(uintptr_t)s->pixels) return -1;
    return 0;
}
static int rectangle(const struct dfb_surface *s, struct dfb_rect r) {
    return dfb_validate(s) || !r.width || !r.height || r.x>=s->width ||
        r.y>=s->height || r.width>s->width-r.x || r.height>s->height-r.y ? -1:0;
}
int dfb_fill(const struct dfb_surface *s, struct dfb_rect r, uint32_t pixel) {
    if(rectangle(s,r)) return -1;
    for(uint32_t y=0;y<r.height;y++) {
        volatile uint8_t *p=s->pixels+(size_t)(r.y+y)*s->stride+(size_t)r.x*4;
        for(uint32_t x=0;x<r.width;x++)
            for(int b=0;b<4;b++) p[(size_t)x*4+b]=(uint8_t)(pixel>>(8*b));
    }
    return 0;
}
int dfb_blit(const struct dfb_surface *d, uint32_t x, uint32_t y,
             const struct dfb_surface *s, struct dfb_rect r) {
    struct dfb_rect target={x,y,r.width,r.height};
    if(rectangle(s,r) || rectangle(d,target)) return -1;
    uintptr_t a=(uintptr_t)d->pixels,b=(uintptr_t)s->pixels;
    if(a<b ? d->bytes>b-a : s->bytes>a-b) return -1; /* reject aliases */
    for(uint32_t row=0;row<r.height;row++) {
        volatile uint8_t *out=d->pixels+(size_t)(y+row)*d->stride+(size_t)x*4;
        const volatile uint8_t *in=s->pixels+(size_t)(r.y+row)*s->stride+(size_t)r.x*4;
        for(size_t col=0;col<(size_t)r.width*4;col++) out[col]=in[col];
    }
    return 0;
}
