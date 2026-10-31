#ifndef MT6897_UFS_TOPCKGEN_H
#define MT6897_UFS_TOPCKGEN_H

#include <stdint.h>

/* Saved Duchamp FDT resource. This model never turns it into a pointer. */
#define MTUFS_TOPCKGEN_BASE 0x10000000ull
#define MTUFS_TOPCKGEN_SIZE 0x1000u

#define MTUFS_TOP_CLK_CFG_UPDATE1 0x008u
#define MTUFS_TOP_CLK_CFG_10 0x0b0u
#define MTUFS_TOP_CLK_CFG_10_SET 0x0b4u
#define MTUFS_TOP_CLK_CFG_10_CLR 0x0b8u

enum mtufs_top_clock {
    MTUFS_TOP_AES_UFSFDE_SEL = 41,
    MTUFS_TOP_UFS_SEL = 42,
};

enum mtufs_top_parent {
    MTUFS_TOP_MAINPLL_D4 = 117,
    MTUFS_TOP_MAINPLL_D4_D2 = 118,
    MTUFS_TOP_UNIVPLL_D6 = 139,
    MTUFS_TOP_MMPLL_D6 = 172,
};

enum mtufs_top_result {
    MTUFS_TOP_OK = 0,
    MTUFS_TOP_ARGUMENT = -1,
    MTUFS_TOP_UNVERIFIED = -2,
    MTUFS_TOP_IO = -3,
    MTUFS_TOP_TIMEOUT = -4,
    MTUFS_TOP_FAULTED = -5,
};

enum mtufs_top_access {
    MTUFS_TOP_READ = 0,
    MTUFS_TOP_WRITE = 1,
};

struct mtufs_topckgen_ops {
    void *context;
    /* The platform owner must approve every individual register access. */
    int (*authorise)(void *, unsigned clock_id, uint32_t offset,
                     enum mtufs_top_access access);
    int (*read32)(void *, uint32_t offset, uint32_t *value);
    int (*write32)(void *, uint32_t offset, uint32_t value);
    void (*barrier)(void *);
    uint64_t (*microseconds)(void *);
};

struct mtufs_topckgen {
    struct mtufs_topckgen_ops ops;
    uint32_t timeout_us;
    uint16_t max_polls;
    uint8_t state;
};

/* Zero-initialize and bind once. There is deliberately no recovery/reset API. */
int mtufs_topckgen_bind(struct mtufs_topckgen *,
                        const struct mtufs_topckgen_ops *,
                        uint32_t timeout_us, uint16_t max_polls);
int mtufs_topckgen_set_parent(struct mtufs_topckgen *, unsigned clock_id,
                              unsigned parent_id);
int mtufs_topckgen_enable(struct mtufs_topckgen *, unsigned clock_id);
int mtufs_topckgen_disable(struct mtufs_topckgen *, unsigned clock_id);
int mtufs_topckgen_status(struct mtufs_topckgen *, unsigned clock_id,
                          unsigned *selector, int *enabled);
int mtufs_topckgen_faulted(const struct mtufs_topckgen *);

#endif
