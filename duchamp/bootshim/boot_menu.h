#ifndef DUCHAMP_BOOT_MENU_H
#define DUCHAMP_BOOT_MENU_H

#include "../loader/plan.h"

int duchamp_boot_menu_qemu(const struct duchamp_framebuffer *fb,
    int xnu_available);

#endif
