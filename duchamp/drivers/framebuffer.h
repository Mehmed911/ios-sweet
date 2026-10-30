#ifndef DUCHAMP_SOFTWARE_FRAMEBUFFER_H
#define DUCHAMP_SOFTWARE_FRAMEBUFFER_H
#include <stddef.h>
#include <stdint.h>
/* Caller-owned, mapped 32-bit surface. Pixel values are little-endian raw
 * values in the inherited pixel format; this API does not guess RGB ordering.
 * No GPU, scanout, power, mapping or cache implementation is implied.
 */
struct dfb_surface {
    volatile uint8_t *pixels;
    size_t bytes;
    uint32_t width, height, stride;
};
struct dfb_rect { uint32_t x,y,width,height; };
int dfb_validate(const struct dfb_surface *);
int dfb_fill(const struct dfb_surface *, struct dfb_rect, uint32_t raw_pixel);
int dfb_blit(const struct dfb_surface *dst, uint32_t x, uint32_t y,
             const struct dfb_surface *src, struct dfb_rect);
#endif
