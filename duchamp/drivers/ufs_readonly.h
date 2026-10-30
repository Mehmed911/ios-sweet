#ifndef DUCHAMP_UFS_READONLY_H
#define DUCHAMP_UFS_READONLY_H
#include <stddef.h>
#include <stdint.h>

/* Single-owner, polling, legacy UFSHCI transport. No physical backend here.
 * The platform must own/quiesce the controller and provide DMA/cache handling.
 * A timeout poisons the host: DMA storage MUST stay reserved until the platform
 * proves quiescence. Never bind these callbacks to phone MMIO without that work.
 */
enum dufs_result {
    DUFS_OK = 0, DUFS_ARGUMENT = -1, DUFS_PLATFORM = -2, DUFS_STATE = -3,
    DUFS_TIMEOUT = -4, DUFS_DMA = -5, DUFS_RESPONSE = -6, DUFS_SCSI = -7
};
enum dufs_timeout { DUFS_WAIT_NONE=0,DUFS_WAIT_DEADLINE=1,DUFS_WAIT_POLLS=2 };
#define DUFS_MAX_POLLS 1000000u
struct dufs_io {
    void *context;
    uint32_t (*read32)(void *, uint32_t);
    void (*write32)(void *, uint32_t, uint32_t);
    int (*dma_write)(void *, uint64_t, const void *, size_t);
    int (*dma_read)(void *, uint64_t, void *, size_t);
    void (*barrier)(void *);
    uint64_t (*milliseconds)(void *);
};
struct dufs_config {
    struct dufs_io io;
    uint64_t dma_begin, dma_end; /* bus address interval, end exclusive */
    uint64_t list_dma, command_dma, data_dma;
    uint32_t timeout_ms;
    uint8_t exclusive_platform_ready, lun;
    /* Resource policy, not a measured MT6897 timing parameter. Shared across
     * all waits/queries within one public operation; callbacks must return.
     */
    uint32_t poll_limit;
};
#define DUFS_MAX_TRANSFER (256u * 1024u)
#define DUFS_LIST_BYTES 1024u
#define DUFS_COMMAND_BYTES 1152u
struct dufs_host {
    struct dufs_config config;
    uint64_t blocks;
    uint32_t block_bytes, version;
    uint32_t poll_remaining;
    uint8_t state, tag, device_ready, timeout_reason;
    uint8_t list[DUFS_LIST_BYTES], command[DUFS_COMMAND_BYTES];
    uint8_t data[DUFS_MAX_TRANSFER];
};
/* Allocate zero-initialized storage. Bind once; no automatic rebind/reset. */
size_t dufs_host_size(void);
unsigned dufs_timeout_cause(const struct dufs_host *);
int dufs_bind(struct dufs_host *, const struct dufs_config *);
int dufs_start(struct dufs_host *);
int dufs_nop(struct dufs_host *);
int dufs_device_init(struct dufs_host *);
int dufs_capacity(struct dufs_host *, uint64_t *blocks, uint32_t *block_bytes);
int dufs_read(struct dufs_host *, uint64_t lba, uint32_t blocks,
              void *destination, size_t destination_bytes);
#endif
