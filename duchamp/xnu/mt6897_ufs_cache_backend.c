#include "mt6897_ufs_cache_backend.h"

#include <stddef.h>

#if defined(MT6897_UFS_XNU_CACHE_BACKEND_TEST)
extern int mt6897_ufs_xnu_cache_test_clean(uint64_t, uint64_t);
extern int mt6897_ufs_xnu_cache_test_flush(uint64_t, uint64_t);
extern int mt6897_ufs_xnu_cache_test_barrier(uint32_t);
#else
/* vm_offset_t is uintptr_t on the ARM64 XNU target.  Keeping the declarations
 * local also lets the policy object compile freestanding for import auditing. */
extern void CleanPoC_DcacheRegion(uintptr_t, size_t);
extern void FlushPoC_DcacheRegion(uintptr_t, size_t);
#endif

static int
direction_valid(enum mt6897_ufs_cache_direction direction)
{
    return direction == MT6897_UFS_CACHE_TO_DEVICE ||
        direction == MT6897_UFS_CACHE_FROM_DEVICE ||
        direction == MT6897_UFS_CACHE_BIDIRECTIONAL;
}

static int
phase_valid(enum mt6897_ufs_cache_barrier_phase phase)
{
    return phase == MT6897_UFS_CACHE_BARRIER_TO_DEVICE ||
        phase == MT6897_UFS_CACHE_BARRIER_BEFORE_CPU ||
        phase == MT6897_UFS_CACHE_BARRIER_AFTER_CPU;
}

static int
receipt_equal(const struct mt6897_ufs_cache_receipt *left,
    const struct mt6897_ufs_cache_receipt *right)
{
#define RECEIPT_EQUAL(field) (left->field == right->field)
    return RECEIPT_EQUAL(version) && RECEIPT_EQUAL(flags) &&
        RECEIPT_EQUAL(boot_generation) && RECEIPT_EQUAL(cache_owner_id) &&
        RECEIPT_EQUAL(range_owner_id) && RECEIPT_EQUAL(cpu_address) &&
        RECEIPT_EQUAL(physical_address) && RECEIPT_EQUAL(bytes) &&
        RECEIPT_EQUAL(cache_line_size) && RECEIPT_EQUAL(reserved0) &&
        RECEIPT_EQUAL(clean_implementation_id) &&
        RECEIPT_EQUAL(flush_implementation_id) &&
        RECEIPT_EQUAL(barrier_implementation_id);
#undef RECEIPT_EQUAL
}

static int
receipt_valid(const struct mt6897_ufs_cache_receipt *receipt)
{
    if (receipt == 0 ||
        receipt->version != MT6897_UFS_CACHE_CONTRACT_VERSION ||
        receipt->flags != MT6897_UFS_CACHE_REQUIRED_FLAGS ||
        receipt->boot_generation == 0 || receipt->cache_owner_id == 0 ||
        receipt->range_owner_id == 0 || receipt->cpu_address == 0 ||
        receipt->physical_address == 0 || receipt->bytes == 0 ||
        receipt->bytes > UINT32_MAX || receipt->reserved0 != 0 ||
        receipt->cache_line_size != MT6897_UFS_XNU_CACHE_LINE_SIZE ||
        receipt->clean_implementation_id !=
            MT6897_UFS_XNU_CACHE_CLEAN_ID ||
        receipt->flush_implementation_id !=
            MT6897_UFS_XNU_CACHE_FLUSH_ID ||
        receipt->barrier_implementation_id !=
            MT6897_UFS_XNU_CACHE_BARRIER_ID) {
        return 0;
    }
    return (receipt->cpu_address &
            (MT6897_UFS_XNU_CACHE_LINE_SIZE - 1)) == 0 &&
        (receipt->physical_address &
            (MT6897_UFS_XNU_CACHE_LINE_SIZE - 1)) == 0 &&
        (receipt->bytes & (MT6897_UFS_XNU_CACHE_LINE_SIZE - 1)) == 0 &&
        receipt->cpu_address <= UINT64_MAX - (receipt->bytes - 1) &&
        receipt->physical_address <= UINT64_MAX - (receipt->bytes - 1);
}

static int
backend_zero(const struct mt6897_ufs_xnu_cache_backend *backend)
{
    const struct mt6897_ufs_cache_receipt *receipt;

    if (backend == 0) {
        return 0;
    }
    receipt = &backend->receipt;
    return receipt->version == 0 && receipt->flags == 0 &&
        receipt->boot_generation == 0 && receipt->cache_owner_id == 0 &&
        receipt->range_owner_id == 0 && receipt->cpu_address == 0 &&
        receipt->physical_address == 0 && receipt->bytes == 0 &&
        receipt->cache_line_size == 0 && receipt->reserved0 == 0 &&
        receipt->clean_implementation_id == 0 &&
        receipt->flush_implementation_id == 0 &&
        receipt->barrier_implementation_id == 0 &&
        backend->clean_calls == 0 && backend->flush_calls == 0 &&
        backend->barrier_calls == 0 && backend->version == 0 &&
        backend->faulted == 0;
}

static void
copy_receipt(struct mt6897_ufs_cache_receipt *destination,
    const struct mt6897_ufs_cache_receipt *source)
{
#define COPY_RECEIPT(field) destination->field = source->field
    COPY_RECEIPT(version);
    COPY_RECEIPT(flags);
    COPY_RECEIPT(boot_generation);
    COPY_RECEIPT(cache_owner_id);
    COPY_RECEIPT(range_owner_id);
    COPY_RECEIPT(cpu_address);
    COPY_RECEIPT(physical_address);
    COPY_RECEIPT(bytes);
    COPY_RECEIPT(cache_line_size);
    COPY_RECEIPT(reserved0);
    COPY_RECEIPT(clean_implementation_id);
    COPY_RECEIPT(flush_implementation_id);
    COPY_RECEIPT(barrier_implementation_id);
#undef COPY_RECEIPT
}

static int
backend_ready(struct mt6897_ufs_xnu_cache_backend *backend)
{
    return backend != 0 &&
        __atomic_load_n(&backend->version, __ATOMIC_ACQUIRE) ==
            MT6897_UFS_XNU_CACHE_BACKEND_VERSION &&
        __atomic_load_n(&backend->faulted, __ATOMIC_ACQUIRE) == 0 &&
        receipt_valid(&backend->receipt);
}

static int
backend_fault(struct mt6897_ufs_xnu_cache_backend *backend)
{
    if (backend != 0) {
        __atomic_store_n(&backend->faulted, 1, __ATOMIC_RELEASE);
    }
    return -1;
}

static int
backend_verify(void *context,
    const struct mt6897_ufs_cache_receipt *receipt,
    const struct mt6897_ufs_gate_lease *lease)
{
    struct mt6897_ufs_xnu_cache_backend *backend = context;

    if (!backend_ready(backend) || receipt == 0 || lease == 0 ||
        !receipt_equal(receipt, &backend->receipt) ||
        lease->boot_generation != receipt->boot_generation ||
        lease->cache_owner_id != receipt->cache_owner_id) {
        return backend_fault(backend);
    }
    return 0;
}

static int
range_valid(struct mt6897_ufs_xnu_cache_backend *backend,
    uint64_t cpu_address, uint64_t physical_address, uint64_t bytes,
    enum mt6897_ufs_cache_direction direction)
{
    return backend_ready(backend) && direction_valid(direction) &&
        cpu_address == backend->receipt.cpu_address &&
        physical_address == backend->receipt.physical_address &&
        bytes == backend->receipt.bytes;
}

static int
backend_clean(void *context, uint64_t cpu_address,
    uint64_t physical_address, uint64_t bytes,
    enum mt6897_ufs_cache_direction direction)
{
    struct mt6897_ufs_xnu_cache_backend *backend = context;

    if (!range_valid(backend, cpu_address, physical_address, bytes,
        direction)) {
        return backend_fault(backend);
    }
#if defined(MT6897_UFS_XNU_CACHE_BACKEND_TEST)
    if (mt6897_ufs_xnu_cache_test_clean(cpu_address, bytes) != 0) {
        return backend_fault(backend);
    }
#else
    CleanPoC_DcacheRegion((uintptr_t)cpu_address, (size_t)bytes);
#endif
    (void)__atomic_fetch_add(&backend->clean_calls, UINT64_C(1),
        __ATOMIC_RELAXED);
    return 0;
}

static int
backend_flush(void *context, uint64_t cpu_address,
    uint64_t physical_address, uint64_t bytes,
    enum mt6897_ufs_cache_direction direction)
{
    struct mt6897_ufs_xnu_cache_backend *backend = context;

    if (!range_valid(backend, cpu_address, physical_address, bytes,
        direction)) {
        return backend_fault(backend);
    }
#if defined(MT6897_UFS_XNU_CACHE_BACKEND_TEST)
    if (mt6897_ufs_xnu_cache_test_flush(cpu_address, bytes) != 0) {
        return backend_fault(backend);
    }
#else
    FlushPoC_DcacheRegion((uintptr_t)cpu_address, (size_t)bytes);
#endif
    (void)__atomic_fetch_add(&backend->flush_calls, UINT64_C(1),
        __ATOMIC_RELAXED);
    return 0;
}

static int
backend_barrier(void *context,
    enum mt6897_ufs_cache_barrier_phase phase,
    enum mt6897_ufs_cache_direction direction)
{
    struct mt6897_ufs_xnu_cache_backend *backend = context;

    if (!backend_ready(backend) || !phase_valid(phase) ||
        !direction_valid(direction)) {
        return backend_fault(backend);
    }
#if defined(MT6897_UFS_XNU_CACHE_BACKEND_TEST)
    if (mt6897_ufs_xnu_cache_test_barrier((uint32_t)phase) != 0) {
        return backend_fault(backend);
    }
#else
    __asm__ volatile("dsb sy" ::: "memory");
    if (phase == MT6897_UFS_CACHE_BARRIER_AFTER_CPU) {
        __asm__ volatile("isb" ::: "memory");
    }
#endif
    (void)__atomic_fetch_add(&backend->barrier_calls, UINT64_C(1),
        __ATOMIC_RELAXED);
    return 0;
}

enum mt6897_ufs_xnu_cache_backend_result
mt6897_ufs_xnu_cache_backend_init(
    struct mt6897_ufs_xnu_cache_backend *backend,
    const struct mt6897_ufs_cache_receipt *receipt)
{
    if (backend == 0 || receipt == 0) {
        return MT6897_UFS_XNU_CACHE_BACKEND_ARGUMENT;
    }
    if (!backend_zero(backend)) {
        return MT6897_UFS_XNU_CACHE_BACKEND_STATE;
    }
    if (!receipt_valid(receipt)) {
        return MT6897_UFS_XNU_CACHE_BACKEND_CONTRACT;
    }
    copy_receipt(&backend->receipt, receipt);
    backend->clean_calls = 0;
    backend->flush_calls = 0;
    backend->barrier_calls = 0;
    backend->faulted = 0;
    __atomic_store_n(&backend->version,
        MT6897_UFS_XNU_CACHE_BACKEND_VERSION, __ATOMIC_RELEASE);
    return MT6897_UFS_XNU_CACHE_BACKEND_OK;
}

enum mt6897_ufs_xnu_cache_backend_result
mt6897_ufs_xnu_cache_backend_ops(
    struct mt6897_ufs_xnu_cache_backend *backend,
    struct mt6897_ufs_cache_ops *ops_out)
{
    if (backend == 0 || ops_out == 0) {
        return MT6897_UFS_XNU_CACHE_BACKEND_ARGUMENT;
    }
    if (!backend_ready(backend)) {
        return MT6897_UFS_XNU_CACHE_BACKEND_STATE;
    }
    ops_out->context = backend;
    ops_out->verify = backend_verify;
    ops_out->clean_to_poc = backend_clean;
    ops_out->flush_to_poc = backend_flush;
    ops_out->barrier = backend_barrier;
    return MT6897_UFS_XNU_CACHE_BACKEND_OK;
}
