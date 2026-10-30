#ifndef MT6897_UFS_CLOCK_LEAVES_H
#define MT6897_UFS_CLOCK_LEAVES_H
#include <stdint.h>
/* Only the six ufscfg AO/PDN leaf gates. No topckgen mux, PMIC, PHY, SiP,
 * reset, DMA or physical MMIO backend. Firmware/parent/power ownership must
 * be established by the caller before its authorise callback permits access.
 */
enum mufs_bank { MUFS_AO=0, MUFS_PDN=1 };
enum mufs_result { MUFS_OK=0,MUFS_ARGUMENT=-1,MUFS_UNVERIFIED=-2,
                   MUFS_IO=-3,MUFS_TIMEOUT=-4,MUFS_FAULTED=-5 };
struct mufs_clock_ops {
    void *context;
    int (*authorise)(void *,unsigned bank,unsigned id);
    int (*read32)(void *,unsigned bank,uint32_t offset,uint32_t *value);
    int (*write32)(void *,unsigned bank,uint32_t offset,uint32_t value);
    void (*barrier)(void *);
    uint64_t (*microseconds)(void *);
};
struct mufs_clocks { struct mufs_clock_ops ops; uint32_t timeout_us; uint8_t state; };
/* Zero-initialize, bind once. A failed transaction latches faulted state;
 * no rollback/retry or reset of another shared resource is attempted.
 */
int mufs_clocks_bind(struct mufs_clocks *,const struct mufs_clock_ops *,uint32_t timeout_us);
int mufs_clock_status(struct mufs_clocks *,unsigned bank,unsigned id,int *enabled);
int mufs_clock_set(struct mufs_clocks *,unsigned bank,unsigned id,int enable);
uint64_t mufs_clock_bank_address(unsigned bank);
#endif
