#include "mt6897_platform.h"

void
duchamp_mt6897_platform_profile(struct duchamp_mt6897_platform *platform)
{
	if (platform == 0) {
		return;
	}
	platform->gicd_base = UINT64_C(0x0c400000);
	platform->gicr_base = UINT64_C(0x0c440000);
	platform->gicr_size = UINT64_C(0x200000);
	platform->timer_frequency = UINT64_C(0x00c65d40);
	platform->framebuffer_base = UINT64_C(0xfcc2f000);
	platform->framebuffer_stride = UINT64_C(4992);
	platform->framebuffer_width = 1220;
	platform->framebuffer_height = 2712;
	platform->framebuffer_depth = 32;
}
