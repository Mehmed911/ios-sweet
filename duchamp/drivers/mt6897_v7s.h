#ifndef MT6897_V7S_H
#define MT6897_V7S_H
#include <stddef.h>
#include <stdint.h>
/* ARM_V7S + ARM_NS + NO_PERMS + MTK_EXT + MTK_TTBR_EXT, IAS34/OAS35.
 * Offline, 4-KiB pages only. No live update, unmap, allocator or stream routing.
 * This format cannot enforce read-only/no-execute permissions (NO_PERMS).
 */
#define MV7_L1_ENTRIES 16384u
#define MV7_L1_BYTES 65536u
#define MV7_L2_BYTES 1024u
enum mv7_result { MV7_OK=0,MV7_ARGUMENT=-1,MV7_STATE=-2,MV7_RANGE=-3,
                  MV7_OVERLAP=-4,MV7_CAPACITY=-5,MV7_CORRUPT=-6,MV7_SYNC=-7 };
struct mv7_table {
    uint32_t *root,*pool;
    uint64_t root_pa,pool_pa;
    uint32_t capacity,used;
    unsigned state; /* 0 fresh; 1 constructing; 2 sealed; 3 poisoned */
};
struct mv7_sync {
    void *context;
    int (*table)(void *,uint64_t physical,size_t bytes);
    void (*barrier)(void *);
};
int mv7_init(struct mv7_table *,void *root,uint64_t root_pa,void *pool,
             uint64_t pool_pa,uint32_t l2_capacity);
int mv7_map(struct mv7_table *,uint64_t iova,uint64_t physical,uint64_t bytes,int cacheable);
int mv7_translate(const struct mv7_table *,uint64_t iova,uint64_t *physical);
int mv7_seal(struct mv7_table *,const struct mv7_sync *,uint32_t *encoded_ttbr);
/* Keep all allocations reserved after sealing/poisoning until a platform
 * proves that no walker can use them. A sealed table is not device-ready.
 */
#endif
