#ifndef DUCHAMP_BOOT_MENU_KEYS_H
#define DUCHAMP_BOOT_MENU_KEYS_H

#include <stdint.h>

enum duchamp_menu_key {
	DUCHAMP_MENU_NO_KEY = 0,
	DUCHAMP_MENU_VOLUME_UP = 1,
	DUCHAMP_MENU_VOLUME_DOWN = 2,
	DUCHAMP_MENU_POWER = 4,
};

struct duchamp_menu_keys {
	int armed;
};

/* The caller supplies one complete sample. PMIC levels are already decoded. */
enum duchamp_menu_key duchamp_menu_key_sample(struct duchamp_menu_keys *keys,
    uint16_t kpd_mem1, unsigned pmic_pressed);

#endif
