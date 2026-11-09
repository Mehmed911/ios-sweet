#ifndef DUCHAMP_UFS_GPT_H
#define DUCHAMP_UFS_GPT_H

#include "ufs_readonly.h"

#define DUFS_GPT_GUID_BYTES 16
#define DUFS_GPT_TABLE_BYTES (128u * 128u)

enum dufs_gpt_result {
    DUFS_GPT_INVALID = -8,
    DUFS_GPT_NOT_FOUND = -9
};

struct dufs_gpt_scratch {
    uint8_t block[4096];
    uint8_t primary[DUFS_GPT_TABLE_BYTES];
    uint8_t backup[DUFS_GPT_TABLE_BYTES];
};

/* Bounds expressed in UFS blocks, on the LUN already bound to this host. */
struct dufs_partition {
    uint64_t first_block;
    uint64_t blocks;
};

/* Use after dufs_capacity(). The caller pins the GPT sector size and the
 * unique HFS+ partition GUID in GPT wire order. Require a protective MBR,
 * matching GPT copies and an HFS+/HFSX volume signature. On failure partition
 * is untouched. Scratch must be private to this call and separate from host.
 */
int dufs_gpt_find_hfs(struct dufs_host *, uint32_t gpt_sector_bytes,
    const uint8_t guid[DUFS_GPT_GUID_BYTES], struct dufs_gpt_scratch *,
    struct dufs_partition *);

/* Read relative to an immutable successful selection on the same host. */
int dufs_partition_read(struct dufs_host *, const struct dufs_partition *,
    uint64_t relative_block, uint32_t blocks, void *, size_t);

#endif
