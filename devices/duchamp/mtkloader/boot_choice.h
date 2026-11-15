#ifndef DUCHAMP_HAKIOS_BOOT_CHOICE_H
#define DUCHAMP_HAKIOS_BOOT_CHOICE_H
#include <stddef.h>
#include <stdint.h>
/* RAM-buffer policy only. No physical address, reset, slot or flash operation.
 * A real caller must independently establish retention, cache publication and
 * Android recovery. These internal assertions are not a firmware wire ABI.
 */
enum { DUCHAMP_CHOICE_ANDROID=0, DUCHAMP_CHOICE_XNU_ONCE=1, DUCHAMP_CHOICE_INVALID=-1 };
struct duchamp_boot_choice_access {
    unsigned readable, writable, retained, cache_publication_ready, android_fallback_ready;
};
int duchamp_take_xnu_request(volatile void *, size_t, const struct duchamp_boot_choice_access *);
#endif
