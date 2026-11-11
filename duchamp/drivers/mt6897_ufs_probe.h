#ifndef MT6897_UFS_PROBE_H
#define MT6897_UFS_PROBE_H

#include "mt6897_ufs_provider.h"
#include "ufs_readonly.h"

#define MT6897_UFS_PROBE_LUN 2u
#define MT6897_UFS_PROBE_LBA UINT64_C(276480)
#define MT6897_UFS_PROBE_BYTES 4096u

struct mt6897_ufs_probe_ops {
    void *context;
    int (*prepare)(void *, struct dufs_config *);
};

struct mt6897_ufs_probe {
    struct mt6897_ufs_provider provider;
    struct mt6897_ufs_probe_ops ops;
    struct dufs_host *host;
    uint32_t attempted;
    uint8_t block[MT6897_UFS_PROBE_BYTES];
};

/*
 * Bind a zero-initialized probe and transport before publishing them.
 * The platform supplies the verified legacy controller and DMA/cache route
 * through prepare, which runs only under a live lease. The platform must
 * serialize ownership changes against an in-flight transaction. Keep the
 * transport and DMA buffers reserved until the platform proves quiescence.
 */
enum mt6897_ufs_provider_result mt6897_ufs_probe_bind(
    struct mt6897_ufs_probe *, struct mt6897_ufs_gate *,
    const struct mt6897_ufs_gate_lease *, struct dufs_host *,
    const struct mt6897_ufs_probe_ops *, uint64_t *blockers_out);

/* One attempt per probe. Errors leave the caller's destination untouched. */
enum mt6897_ufs_provider_result mt6897_ufs_probe_read(
    struct mt6897_ufs_probe *, void *destination, size_t bytes,
    uint64_t *blockers_out);

#endif
