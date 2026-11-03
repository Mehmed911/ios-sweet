#include "mt6897_ufs_cache_backend.h"

#include <stddef.h>

#ifdef MT6897_MODEL_FREESTANDING
extern void model_assert_fail(const char *, unsigned);
extern int printf(const char *, ...);
#define TEST_FAIL(expression, line) model_assert_fail((expression), (line))
#else
#include <stdio.h>
#include <stdlib.h>
static void
native_fail(const char *expression, unsigned line)
{
    (void)fprintf(stderr, "line %u: check failed: %s\n", line, expression);
    abort();
}
#define TEST_FAIL(expression, line) native_fail((expression), (line))
#endif

static unsigned checks;
#define CHECK(expression) do { \
    ++checks; \
    if (!(expression)) { \
        TEST_FAIL(#expression, __LINE__); \
    } \
} while (0)

_Alignas(64) static unsigned char cache_buffer[256];
static unsigned clean_calls;
static unsigned flush_calls;
static unsigned barrier_calls;
static unsigned fail_kind;

int
mt6897_ufs_xnu_cache_test_clean(uint64_t address, uint64_t bytes)
{
    ++clean_calls;
    CHECK(address == (uint64_t)(uintptr_t)cache_buffer);
    CHECK(bytes == sizeof(cache_buffer));
    return fail_kind == 1 ? -1 : 0;
}

int
mt6897_ufs_xnu_cache_test_flush(uint64_t address, uint64_t bytes)
{
    ++flush_calls;
    CHECK(address == (uint64_t)(uintptr_t)cache_buffer);
    CHECK(bytes == sizeof(cache_buffer));
    return fail_kind == 2 ? -1 : 0;
}

int
mt6897_ufs_xnu_cache_test_barrier(uint32_t phase)
{
    ++barrier_calls;
    CHECK(phase >= MT6897_UFS_CACHE_BARRIER_TO_DEVICE);
    CHECK(phase <= MT6897_UFS_CACHE_BARRIER_AFTER_CPU);
    return fail_kind == 3 ? -1 : 0;
}

static struct mt6897_ufs_gate_lease
valid_lease(void)
{
    struct mt6897_ufs_gate_lease lease = { 0 };

    lease.version = MT6897_UFS_GATE_LEASE_VERSION;
    lease.flags = MT6897_UFS_LEASE_REQUIRED_FLAGS;
    lease.boot_generation = UINT64_C(0x202611040201);
    lease.evidence_fingerprint = UINT64_C(0xe001);
    lease.lease_id = UINT64_C(0xe002);
    lease.provider_epoch = UINT64_C(0xe003);
    lease.controller_owner_id = UINT64_C(0xe004);
    lease.phy_owner_id = UINT64_C(0xe005);
    lease.dma_owner_id = UINT64_C(0xe006);
    lease.cache_owner_id = UINT64_C(0xe007);
    lease.firmware_owner_id = UINT64_C(0xe008);
    return lease;
}

static struct mt6897_ufs_cache_receipt
valid_receipt(void)
{
    struct mt6897_ufs_cache_receipt receipt = { 0 };

    receipt.version = MT6897_UFS_CACHE_CONTRACT_VERSION;
    receipt.flags = MT6897_UFS_CACHE_REQUIRED_FLAGS;
    receipt.boot_generation = UINT64_C(0x202611040201);
    receipt.cache_owner_id = UINT64_C(0xe007);
    receipt.range_owner_id = UINT64_C(0xe009);
    receipt.cpu_address = (uint64_t)(uintptr_t)cache_buffer;
    receipt.physical_address = UINT64_C(0x100000000);
    receipt.bytes = sizeof(cache_buffer);
    receipt.cache_line_size = MT6897_UFS_XNU_CACHE_LINE_SIZE;
    receipt.clean_implementation_id = MT6897_UFS_XNU_CACHE_CLEAN_ID;
    receipt.flush_implementation_id = MT6897_UFS_XNU_CACHE_FLUSH_ID;
    receipt.barrier_implementation_id = MT6897_UFS_XNU_CACHE_BARRIER_ID;
    return receipt;
}

static void
reset_hooks(void)
{
    clean_calls = 0;
    flush_calls = 0;
    barrier_calls = 0;
    fail_kind = 0;
}

static void
test_contract_validation(void)
{
    struct mt6897_ufs_xnu_cache_backend backend = { 0 };
    struct mt6897_ufs_cache_receipt receipt = valid_receipt();
    struct mt6897_ufs_cache_ops ops = { 0 };

    CHECK(mt6897_ufs_xnu_cache_backend_ops(&backend, &ops) ==
        MT6897_UFS_XNU_CACHE_BACKEND_STATE);
    receipt.clean_implementation_id ^= 1;
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_CONTRACT);
    CHECK(backend.version == 0);
    receipt = valid_receipt();
    receipt.cache_line_size = 32;
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_CONTRACT);
    CHECK(backend.version == 0);
    receipt = valid_receipt();
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_STATE);
    CHECK(mt6897_ufs_xnu_cache_backend_ops(&backend, &ops) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(ops.verify != 0 && ops.clean_to_poc != 0 &&
        ops.flush_to_poc != 0 && ops.barrier != 0);
}

static void
test_valid_callbacks(void)
{
    struct mt6897_ufs_xnu_cache_backend backend = { 0 };
    struct mt6897_ufs_cache_receipt receipt = valid_receipt();
    struct mt6897_ufs_gate_lease lease = valid_lease();
    struct mt6897_ufs_cache_ops ops = { 0 };

    reset_hooks();
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(mt6897_ufs_xnu_cache_backend_ops(&backend, &ops) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(ops.verify(ops.context, &receipt, &lease) == 0);
    CHECK(ops.clean_to_poc(ops.context, receipt.cpu_address,
        receipt.physical_address, receipt.bytes,
        MT6897_UFS_CACHE_BIDIRECTIONAL) == 0);
    CHECK(ops.barrier(ops.context, MT6897_UFS_CACHE_BARRIER_TO_DEVICE,
        MT6897_UFS_CACHE_BIDIRECTIONAL) == 0);
    CHECK(ops.barrier(ops.context, MT6897_UFS_CACHE_BARRIER_BEFORE_CPU,
        MT6897_UFS_CACHE_BIDIRECTIONAL) == 0);
    CHECK(ops.flush_to_poc(ops.context, receipt.cpu_address,
        receipt.physical_address, receipt.bytes,
        MT6897_UFS_CACHE_BIDIRECTIONAL) == 0);
    CHECK(ops.barrier(ops.context, MT6897_UFS_CACHE_BARRIER_AFTER_CPU,
        MT6897_UFS_CACHE_BIDIRECTIONAL) == 0);
    CHECK(clean_calls == 1 && flush_calls == 1 && barrier_calls == 3);
    CHECK(backend.clean_calls == 1 && backend.flush_calls == 1 &&
        backend.barrier_calls == 3 && backend.faulted == 0);
}

static void
test_fail_closed(void)
{
    struct mt6897_ufs_xnu_cache_backend backend = { 0 };
    struct mt6897_ufs_cache_receipt receipt = valid_receipt();
    struct mt6897_ufs_gate_lease lease = valid_lease();
    struct mt6897_ufs_cache_ops ops = { 0 };

    reset_hooks();
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(mt6897_ufs_xnu_cache_backend_ops(&backend, &ops) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    ++lease.cache_owner_id;
    CHECK(ops.verify(ops.context, &receipt, &lease) != 0);
    CHECK(backend.faulted == 1);
    CHECK(clean_calls == 0 && flush_calls == 0 && barrier_calls == 0);
    CHECK(mt6897_ufs_xnu_cache_backend_ops(&backend, &ops) ==
        MT6897_UFS_XNU_CACHE_BACKEND_STATE);

    backend = (struct mt6897_ufs_xnu_cache_backend){ 0 };
    lease = valid_lease();
    reset_hooks();
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(mt6897_ufs_xnu_cache_backend_ops(&backend, &ops) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(ops.verify(ops.context, &receipt, &lease) == 0);
    CHECK(ops.clean_to_poc(ops.context, receipt.cpu_address + 64,
        receipt.physical_address, receipt.bytes,
        MT6897_UFS_CACHE_TO_DEVICE) != 0);
    CHECK(backend.faulted == 1 && clean_calls == 0);

    backend = (struct mt6897_ufs_xnu_cache_backend){ 0 };
    reset_hooks();
    fail_kind = 2;
    CHECK(mt6897_ufs_xnu_cache_backend_init(&backend, &receipt) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(mt6897_ufs_xnu_cache_backend_ops(&backend, &ops) ==
        MT6897_UFS_XNU_CACHE_BACKEND_OK);
    CHECK(ops.flush_to_poc(ops.context, receipt.cpu_address,
        receipt.physical_address, receipt.bytes,
        MT6897_UFS_CACHE_FROM_DEVICE) != 0);
    CHECK(backend.faulted == 1 && flush_calls == 1 &&
        backend.flush_calls == 0);
}

int
main(void)
{
    test_contract_validation();
    test_valid_callbacks();
    test_fail_closed();
    (void)printf("%u MT6897 XNU cache-backend checks passed; "
        "clean=1 flush=1 barriers=3 fail_closed=1\n", checks);
    return 0;
}
