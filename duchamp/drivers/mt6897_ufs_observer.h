#ifndef MT6897_UFS_OBSERVER_H
#define MT6897_UFS_OBSERVER_H
#include <stdint.h>
#include "ufs_register_snapshot.h"

/* Internal platform interface, NOT a BL31/LK wire format or a boot argument.
 * Authority callbacks must validate an independently established same-boot
 * read grant. They must not power, clock, reset or probe hardware themselves.
 * This grant permits observation of an active host; it grants NO DMA, storage
 * ownership, cache maintenance, interrupt acknowledgement or UFS command.
 */
enum {
    MUO_WINDOW_READABLE = 1u << 0, MUO_POWER_PINNED = 1u << 1,
    MUO_BUS_CLOCKS_PINNED = 1u << 2, MUO_NS_READ_ALLOWED = 1u << 3,
    MUO_PINS_UNTIL_RESET = 1u << 4, MUO_NONDESTRUCTIVE_READS = 1u << 5,
    MUO_REQUIRED = 0x3f, MUO_GRANT_VERSION = 1
};
struct mt6897_ufs_read_grant {
    uint32_t version, rights;
    uint64_t boot_id, grant_id, owner_id, resource_epoch, base;
    uint32_t bytes, reserved;
};
struct mt6897_ufs_read_authority {
    void *context;
    int (*verify)(void *, uint64_t boot_id, struct mt6897_ufs_read_grant *);
    int (*check)(void *, const struct mt6897_ufs_read_grant *);
};
struct mt6897_ufs_observer_bus {
    void *context;
    /* One permanent, read-only device mapping. No teardown: the authority
     * must keep accessibility/power/clocks pinned until reset, even if the
     * observation permission is later revoked. These callbacks must return.
     */
    uintptr_t (*map_readonly)(void *, uint64_t base, uint32_t bytes);
    int (*read32)(void *, uintptr_t mapping, uint32_t offset, uint32_t *);
};
enum mt6897_ufs_observer_result {
    MUO_OK = 0, MUO_ARGUMENT = -1, MUO_DISABLED = -2, MUO_STATE = -3,
    MUO_DENIED = -4, MUO_MAP = -5, MUO_IO = -6, MUO_LAYOUT = -7,
    MUO_REVOKED = -8
};
enum mt6897_ufs_observer_state {
    MUO_OFF, MUO_BOUND, MUO_CHECKING, MUO_MAPPING, MUO_READING, MUO_LOAD, MUO_DONE, MUO_FAULTED
};
struct mt6897_ufs_observer {
    uint32_t state;
    uint64_t boot_id;
    struct mt6897_ufs_read_authority authority;
    struct mt6897_ufs_observer_bus bus;
    struct mt6897_ufs_read_grant grant;
    uintptr_t mapping;
};
/* Zero-initialize, bind once, capture once. Bind performs no callbacks.
 * Concurrent capture is refused. Each mapping/read has an atomic dispatch
 * authorization point. Revocation which wins that point prevents dispatch;
 * an already authorized callback may finish under the pinned grant. Revocation
 * which wins the final publication CAS discards the complete/partial result.
 * No fault recovery is provided for a powered-off or inaccessible device.
 */
int mt6897_ufs_observer_bind(struct mt6897_ufs_observer *, uint64_t,
    const struct mt6897_ufs_read_authority *, const struct mt6897_ufs_observer_bus *);
int mt6897_ufs_observer_capture(struct mt6897_ufs_observer *, struct dufs_register_snapshot *);
void mt6897_ufs_observer_revoke(struct mt6897_ufs_observer *);
#endif
