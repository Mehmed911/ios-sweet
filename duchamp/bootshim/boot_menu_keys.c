#include "boot_menu_keys.h"

enum duchamp_menu_key
duchamp_menu_key_sample(struct duchamp_menu_keys *keys, uint16_t kpd_mem1,
    unsigned pmic_pressed)
{
	if (pmic_pressed & ~(DUCHAMP_MENU_VOLUME_DOWN | DUCHAMP_MENU_POWER)) {
		keys->armed = 0;
		return DUCHAMP_MENU_NO_KEY;
	}

	/* The saved Duchamp keymap puts volume up at active-low KP_MEM1 bit 0. */
	unsigned pressed = pmic_pressed;
	if ((kpd_mem1 & 1U) == 0)
		pressed |= DUCHAMP_MENU_VOLUME_UP;

	if (pressed == 0) {
		keys->armed = 1;
		return DUCHAMP_MENU_NO_KEY;
	}
	if (!keys->armed)
		return DUCHAMP_MENU_NO_KEY;

	keys->armed = 0;
	/* Ignore chords until all keys are released. */
	if ((pressed & (pressed - 1U)) != 0)
		return DUCHAMP_MENU_NO_KEY;
	return (enum duchamp_menu_key)pressed;
}
