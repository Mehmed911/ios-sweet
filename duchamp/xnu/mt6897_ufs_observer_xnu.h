#ifndef MT6897_UFS_OBSERVER_XNU_H
#define MT6897_UFS_OBSERVER_XNU_H
#include "mt6897_ufs_observer.h"

struct mt6897_ufs_xnu_observer {
    struct mt6897_ufs_observer provider;
    uintptr_t mapping;
    uint32_t map_calls;
    uint64_t read_calls;
};
/* Explicit trusted platform registration only. No boot-arg/ADT grant parser,
 * firmware producer or automatic caller. An unbound object stays disabled.
 */
int mt6897_ufs_xnu_observer_bind(struct mt6897_ufs_xnu_observer *, uint64_t,
    const struct mt6897_ufs_read_authority *);
#endif
