/* Passive UFSHCI/MCQ observation. No controller writes or DMA interface. */
#ifndef DUCHAMP_UFS_REGISTER_SNAPSHOT_H
#define DUCHAMP_UFS_REGISTER_SNAPSHOT_H
#include <stdint.h>

enum {
    DUFS_MTK_HCI_BASE = 0x112b0000, DUFS_MTK_HCI_BYTES = 0x3000,
    DUFS_MTK_MCQ_RUNTIME = 0x2800, DUFS_QEMU_MCQ_RUNTIME = 0x1000,
    DUFS_MCQ_STRIDE = 0x30, DUFS_MCQ_CONFIG_STRIDE = 0x40,
    DUFS_MCQ_MAX_QUEUES = 8,
    DUFS_MCQ_SQ_HEAD = 0, DUFS_MCQ_SQ_TAIL = 4,
    DUFS_MCQ_SQ_IS = 0x14, DUFS_MCQ_CQ_HEAD = 0x1c,
    DUFS_MCQ_CQ_TAIL = 0x20, DUFS_MCQ_CQ_IS = 0x24
};
enum dufs_snapshot_profile { DUFS_SNAPSHOT_MT6897 = 1, DUFS_SNAPSHOT_QEMU };
enum dufs_snapshot_error {
    DUFS_SNAPSHOT_OK = 0, DUFS_SNAPSHOT_ARGUMENT = -1,
    DUFS_SNAPSHOT_DENIED = -2, DUFS_SNAPSHOT_IO = -3,
    DUFS_SNAPSHOT_LAYOUT = -4
};
enum dufs_snapshot_blocker {
    DUFS_SNAPSHOT_HCE_ACTIVE = 1u << 0,
    DUFS_SNAPSHOT_LEGACY_RUNNING = 1u << 1,
    DUFS_SNAPSHOT_LEGACY_PENDING = 1u << 2,
    DUFS_SNAPSHOT_MCQ_ENABLED = 1u << 3,
    DUFS_SNAPSHOT_MCQ_PENDING = 1u << 4,
    DUFS_SNAPSHOT_LISTS_CONFIGURED = 1u << 5,
    DUFS_SNAPSHOT_BAD_POINTER = 1u << 6,
    DUFS_SNAPSHOT_CHANGED = 1u << 7
};
struct dufs_snapshot_source {
    void *context;
    /* Must revalidate permission to READ a powered, accessible aperture from
     * this boot. The callback must return. This is not a DMA/ownership grant.
     * No MMIO is attempted when it denies, including mid-capture revocation.
     */
    int (*allow_read)(void *, uint64_t boot_id, uint64_t base, uint32_t bytes);
    int (*read32)(void *, uint32_t offset, uint32_t *value);
    uint64_t boot_id, physical_base;
    uint32_t bytes;
    enum dufs_snapshot_profile profile;
};
struct dufs_queue_snapshot {
    uint32_t sq_attr, sq_base_lo, sq_base_hi, sq_dao, sq_isao, sq_config;
    uint32_t cq_attr, cq_base_lo, cq_base_hi, cq_dao, cq_isao, cq_config;
    uint32_t sq_head, sq_tail, sq_is, cq_head, cq_tail, cq_is;
};
struct dufs_register_sample {
    uint32_t cap, mcqcap, version, hce, hcs, config;
    uint32_t transfer_base_lo, transfer_base_hi, transfer_doorbell, transfer_run;
    uint32_t task_base_lo, task_base_hi, task_doorbell, task_run;
    uint32_t queues, queue_config_base;
    struct dufs_queue_snapshot queue[DUFS_MCQ_MAX_QUEUES];
};
struct dufs_register_snapshot {
    uint64_t boot_id, physical_base;
    enum dufs_snapshot_profile profile;
    uint32_t reads, blockers;
    struct dufs_register_sample first, last;
};
/* Two bounded passes. Output is unchanged on error. Success only means that
 * both samples were acquired; inspect blockers. Even zero blockers do NOT
 * establish exclusive ownership, queue drain over time, DMA or cache rights.
 * Never dereferences inherited queue addresses or resumes firmware requests.
 */
int dufs_snapshot_registers(const struct dufs_snapshot_source *,
    struct dufs_register_snapshot *);
#endif
