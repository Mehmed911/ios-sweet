#ifndef MT6897_UFS_DMA_H
#define MT6897_UFS_DMA_H
#include <stddef.h>
#include <stdint.h>

/* Streaming-DMA ownership for one caller-reserved, contiguous private pool.
 * No physical IOMMU page tables, stream IDs, identity/bypass inference or
 * memory allocator. CPU VA, physical address and returned device IOVA differ.
 */
enum md_result { MD_OK=0,MD_ARGUMENT=-1,MD_UNVERIFIED=-2,MD_STATE=-3,
                 MD_IO=-4,MD_RANGE=-5,MD_BUSY=-6 };
enum md_route { MD_UNKNOWN=0,MD_VERIFIED_BUS_WINDOW=1,MD_VERIFIED_IOMMU=2 };
enum md_direction { MD_TO_DEVICE=1,MD_FROM_DEVICE=2,MD_BIDIRECTIONAL=3 };
enum md_state { MD_NEW=0,MD_BOUND,MD_CPU,MD_DEVICE,MD_POISONED,MD_RELEASED };
struct md_config {
    void *cpu;
    uint64_t physical,bytes,device_begin,device_end; /* end exclusive */
    uint32_t cache_line,alignment,address_bits;
    enum md_route route;
    enum md_direction direction;
};
struct md_ops {
    void *context;
    /* Includes reserved-memory ownership, correct domain/device/stream,
     * established route and noncoherent cache policy. 1 means authorized.
     */
    int (*authorise)(void *,const struct md_config *);
    int (*idle)(void *); /* 1 only after real controller/DMA quiescence */
    /* Failed map may have side effects. Pool is retained on ANY map error.
     * Successful map is contiguous, with an opaque provider-owned cookie.
     */
    int (*map)(void *,uint64_t physical,uint64_t bytes,enum md_direction,
               uint64_t *device_address,uint64_t *cookie);
    int (*sync_device)(void *,void *cpu,uint64_t bytes,enum md_direction);
    int (*sync_cpu)(void *,void *cpu,uint64_t bytes,enum md_direction);
    void (*barrier)(void *);
    int (*unmap)(void *,uint64_t cookie,uint64_t device_address,uint64_t bytes,
                 enum md_direction);
};
struct md_pool {
    struct md_config config;
    struct md_ops ops;
    uint64_t device,cookie;
    enum md_state state;
};
/* Zero initialize and serialize. The complete allocation must own its cache
 * lines; callbacks synchronize the entire pool. No coherent fast-path guess.
 */
int md_bind(struct md_pool *,const struct md_config *,const struct md_ops *);
int md_map(struct md_pool *);
int md_for_device(struct md_pool *);
int md_for_cpu(struct md_pool *);
int md_release(struct md_pool *);
void md_poison(struct md_pool *); /* Never unmaps or releases the allocation. */
/* No accessor returns a usable device address before successful map.
 * DEVICE/POISONED allocations must stay reserved until platform recovery,
 * which this API intentionally does not implement.
 */
#endif
