#ifndef MT6897_UFS_CACHE_BACKEND_H
#define MT6897_UFS_CACHE_BACKEND_H

#include <stdint.h>

#include "mt6897_ufs_cache.h"

/*
 * XNU/generic-ARM64 implementation of the lease-bound cache callbacks.
 *
 * This backend owns no UFS, DMA, MMIO or firmware operation.  It can only be
 * reached through mt6897_ufs_cache after a valid activation lease has been
 * bound.  The implementation identifiers pin the exact PoC primitives and
 * barrier sequence used by this version.
 */
#define MT6897_UFS_XNU_CACHE_BACKEND_VERSION UINT32_C(1)
#define MT6897_UFS_XNU_CACHE_LINE_SIZE UINT32_C(64)
#define MT6897_UFS_XNU_CACHE_CLEAN_ID UINT64_C(0x584e55434c4e0001)
#define MT6897_UFS_XNU_CACHE_FLUSH_ID UINT64_C(0x584e55464c530001)
#define MT6897_UFS_XNU_CACHE_BARRIER_ID UINT64_C(0x584e554252520001)

enum mt6897_ufs_xnu_cache_backend_result {
    MT6897_UFS_XNU_CACHE_BACKEND_OK = 0,
    MT6897_UFS_XNU_CACHE_BACKEND_ARGUMENT = -1,
    MT6897_UFS_XNU_CACHE_BACKEND_CONTRACT = -2,
    MT6897_UFS_XNU_CACHE_BACKEND_STATE = -3
};

struct mt6897_ufs_xnu_cache_backend {
    struct mt6897_ufs_cache_receipt receipt;
    uint64_t clean_calls;
    uint64_t flush_calls;
    uint64_t barrier_calls;
    uint32_t version;
    uint32_t faulted;
};

enum mt6897_ufs_xnu_cache_backend_result
mt6897_ufs_xnu_cache_backend_init(
    struct mt6897_ufs_xnu_cache_backend *backend,
    const struct mt6897_ufs_cache_receipt *receipt);

enum mt6897_ufs_xnu_cache_backend_result
mt6897_ufs_xnu_cache_backend_ops(
    struct mt6897_ufs_xnu_cache_backend *backend,
    struct mt6897_ufs_cache_ops *ops_out);

#endif
