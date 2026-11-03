#include "mt6897_ufs_gate.h"

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

#define BOOT_GENERATION UINT64_C(0x202611030001)

struct verifier_model {
    enum mt6897_ufs_gate_verdict verdict;
    unsigned mode;
    unsigned verifier_calls;
    unsigned mmio_calls;
    unsigned smc_calls;
    unsigned dma_calls;
    struct mt6897_ufs_gate *gate;
    struct mt6897_ufs_gate_evidence *evidence;
    enum mt6897_ufs_gate_result nested_result;
    uint64_t nested_blockers;
    struct mt6897_ufs_gate_verifier_request last;
};

static void
make_valid_lease(const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    lease->version = MT6897_UFS_GATE_LEASE_VERSION;
    lease->flags = MT6897_UFS_LEASE_REQUIRED_FLAGS;
    lease->boot_generation = request->evidence.boot_generation;
    lease->evidence_fingerprint = request->evidence_fingerprint;
    lease->lease_id = UINT64_C(0x1001);
    lease->provider_epoch = UINT64_C(0x2002);
    lease->controller_owner_id = UINT64_C(0x3003);
    lease->phy_owner_id = UINT64_C(0x4004);
    lease->dma_owner_id = UINT64_C(0x5005);
    lease->cache_owner_id = UINT64_C(0x6006);
    lease->firmware_owner_id = UINT64_C(0x7007);
}

static enum mt6897_ufs_gate_verdict
model_verifier(void *context,
    const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    struct verifier_model *model = (struct verifier_model *)context;
    struct mt6897_ufs_gate_verifier_request *mutable_request;
    struct mt6897_ufs_gate_lease nested_lease = { 0 };

    ++model->verifier_calls;
    model->last = *request;
    make_valid_lease(request, lease);
    switch (model->mode) {
    case 1: lease->version = 99; break;
    case 2: lease->flags &= ~MT6897_UFS_LEASE_NONREVOKABLE_UNTIL_BOOT_END; break;
    case 3: lease->flags |= UINT32_C(0x80000000); break;
    case 4: ++lease->boot_generation; break;
    case 5: ++lease->evidence_fingerprint; break;
    case 6: lease->lease_id = 0; break;
    case 7: lease->provider_epoch = 0; break;
    case 8: lease->controller_owner_id = 0; break;
    case 9: lease->phy_owner_id = 0; break;
    case 10: lease->dma_owner_id = 0; break;
    case 11: lease->cache_owner_id = 0; break;
    case 12: lease->firmware_owner_id = 0; break;
    case 20:
        mutable_request =
            (struct mt6897_ufs_gate_verifier_request *)(uintptr_t)request;
        mutable_request->required ^= MT6897_UFS_E_PLATFORM_MATCH;
        break;
    case 21:
        model->evidence->known ^= MT6897_UFS_E_PLATFORM_MATCH;
        break;
    case 22:
        model->nested_result = mt6897_ufs_gate_authorize(model->gate,
            model->evidence, model_verifier, model, &nested_lease,
            &model->nested_blockers);
        break;
    case 23:
        model->gate->cookie ^= UINT64_C(1);
        break;
    default:
        break;
    }
    if (model->mode == 30) {
        return (enum mt6897_ufs_gate_verdict)99;
    }
    return model->verdict;
}

static void
check_no_hardware(const struct verifier_model *model)
{
    CHECK(model->mmio_calls == 0);
    CHECK(model->smc_calls == 0);
    CHECK(model->dma_calls == 0);
}

static int
lease_is_zero(const struct mt6897_ufs_gate_lease *lease)
{
    return lease->version == 0 && lease->flags == 0 &&
        lease->boot_generation == 0 && lease->evidence_fingerprint == 0 &&
        lease->lease_id == 0 && lease->provider_epoch == 0 &&
        lease->controller_owner_id == 0 && lease->phy_owner_id == 0 &&
        lease->dma_owner_id == 0 && lease->cache_owner_id == 0 &&
        lease->firmware_owner_id == 0;
}

static struct mt6897_ufs_gate_evidence
direct_evidence(int bounce_required)
{
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);

    evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED;
    if (bounce_required) {
        evidence.asserted |= MT6897_UFS_E_BOUNCE_REQUIRED |
            MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP;
        evidence.bounce_start = UINT64_C(0x80000000);
        evidence.bounce_size = UINT64_C(0x200000);
        evidence.bounce_owner_id = UINT64_C(0xb001);
    } else {
        evidence.asserted |= MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    }
    evidence.known = evidence.asserted;
    return evidence;
}

static struct mt6897_ufs_gate_evidence
iommu_evidence(void)
{
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);

    evidence.route = (uint32_t)MT6897_UFS_GATE_ROUTE_IOMMU;
    evidence.asserted = MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_IOMMU_REQUIRED | MT6897_UFS_E_NONCOHERENT_DEVICE;
    evidence.known = evidence.asserted;
    evidence.iommu_stream_id = UINT32_C(0x123);
    evidence.iommu_domain_id = UINT64_C(0xd001);
    evidence.iommu_table_id = UINT64_C(0xd002);
    evidence.iommu_mapping_epoch = UINT64_C(0xd003);
    return evidence;
}

static void
test_saved_receipts(void)
{
    static const uint8_t expected_fdt[32] = {
        0x9c, 0x49, 0x58, 0x9f, 0x70, 0x04, 0x41, 0x27,
        0xbe, 0x89, 0x41, 0xa9, 0xea, 0x55, 0x37, 0x97,
        0x7f, 0x44, 0x0c, 0xcd, 0x5a, 0xc1, 0x5c, 0xfd,
        0x24, 0xe1, 0x20, 0xc8, 0xa1, 0x18, 0x1d, 0x29
    };
    static const uint8_t expected_firmware[32] = {
        0x71, 0x62, 0x22, 0xa6, 0x32, 0xe4, 0xa0, 0x62,
        0x3a, 0x2e, 0x46, 0x7e, 0x17, 0xf1, 0xd3, 0x6f,
        0x38, 0xa3, 0x7f, 0x79, 0xa1, 0xc0, 0x26, 0x44,
        0x7f, 0xe7, 0x24, 0xe7, 0x5e, 0x90, 0xe0, 0x7e
    };
    static const uint8_t expected_firmware_audit[32] = {
        0x65, 0xe4, 0xa5, 0xcd, 0xd2, 0x08, 0x5c, 0x2e,
        0x2b, 0xb4, 0x8a, 0xd9, 0x82, 0x91, 0x09, 0xf8,
        0xe3, 0x9b, 0x7a, 0x26, 0x06, 0x69, 0x07, 0x4a,
        0xb5, 0x94, 0x27, 0x41, 0x9b, 0x5d, 0x11, 0x0c
    };
    static const uint8_t expected_runtime[32] = {
        0x71, 0x23, 0x6c, 0x08, 0xc0, 0x35, 0x4f, 0xf0,
        0x73, 0x3d, 0x44, 0xa6, 0x4e, 0x50, 0x5d, 0x11,
        0x7d, 0xfd, 0x45, 0x94, 0xe3, 0x70, 0xbe, 0xdd,
        0x81, 0xfa, 0xd3, 0xec, 0x93, 0xd1, 0xbf, 0x4d
    };
    static const uint8_t expected_prdt[32] = {
        0x1e, 0x4c, 0x73, 0x5d, 0x31, 0x60, 0x04, 0xc8,
        0x3f, 0x9d, 0xb7, 0x15, 0x38, 0x18, 0x63, 0x57,
        0x11, 0x2c, 0x75, 0x67, 0xda, 0xec, 0xd1, 0x2b,
        0xe5, 0x2b, 0xa2, 0x4e, 0x74, 0xea, 0x40, 0x18
    };
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);

    CHECK(evidence.version == MT6897_UFS_GATE_EVIDENCE_VERSION);
    CHECK(evidence.route == MT6897_UFS_GATE_ROUTE_DIRECT_DMA);
    CHECK(evidence.boot_generation == BOOT_GENERATION);
    CHECK(evidence.ufs_hci_base == MT6897_UFS_DUCHAMP_HCI_BASE);
    CHECK(evidence.ufs_hci_size == MT6897_UFS_DUCHAMP_HCI_SIZE);
    CHECK(evidence.ufs_phy_base == MT6897_UFS_DUCHAMP_PHY_BASE);
    CHECK(evidence.ufs_phy_size == MT6897_UFS_DUCHAMP_PHY_SIZE);
    CHECK(evidence.firmware_service_id == MT6897_UFS_DUCHAMP_SIP_UFS64);
    CHECK(evidence.firmware_refclk_selector == 8);
    CHECK(evidence.firmware_mtcmos_selector == 512);
    CHECK(evidence.firmware_mcq_selector == 1024);
    CHECK(evidence.dma_cpu_start == 0);
    CHECK(evidence.dma_device_start == 0);
    CHECK(evidence.dma_size == MT6897_UFS_DUCHAMP_DMA_SIZE);
    CHECK(evidence.dma_limit == MT6897_UFS_DUCHAMP_DMA_LIMIT);
    CHECK(evidence.dma_address_bits == MT6897_UFS_DUCHAMP_DMA_BITS);
    CHECK(evidence.cache_line_size == 64);
    for (unsigned index = 0; index < 32; ++index) {
        CHECK(evidence.fdt_sha256[index] == expected_fdt[index]);
        CHECK(evidence.firmware_sha256[index] == expected_firmware[index]);
        CHECK(evidence.firmware_audit_sha256[index] ==
            expected_firmware_audit[index]);
        CHECK(evidence.runtime_dma_report_sha256[index] ==
            expected_runtime[index]);
        CHECK(evidence.prdt_report_sha256[index] == expected_prdt[index]);
    }
}

static void
test_saved_evidence_is_denied(void)
{
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(BOOT_GENERATION);
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct verifier_model model = {
        .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
    };
    uint64_t blockers = 0;

    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_DENIED);
    CHECK(blockers == MT6897_UFS_CURRENT_DUCHAMP_BLOCKERS);
    CHECK(gate.state == MT6897_UFS_GATE_STATE_DENIED);
    CHECK(model.verifier_calls == 0);
    CHECK(lease_is_zero(&lease));
    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_NOT_ZERO);
    CHECK(mt6897_ufs_gate_authorize(&gate, 0, 0, 0, &lease, &blockers) ==
        MT6897_UFS_GATE_FAULT);
    CHECK(blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(model.verifier_calls == 0);
    check_no_hardware(&model);
}

static void
test_direct_lease(void)
{
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct mt6897_ufs_gate_lease saved_lease;
    struct verifier_model model = {
        .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
    };
    uint64_t blockers = ~UINT64_C(0);

    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_LEASED);
    CHECK(blockers == 0);
    CHECK(model.verifier_calls == 1);
    CHECK(gate.state == MT6897_UFS_GATE_STATE_LEASED);
    CHECK(gate.evidence_fingerprint ==
        mt6897_ufs_gate_evidence_fingerprint(&evidence));
    CHECK(lease.flags == MT6897_UFS_LEASE_REQUIRED_FLAGS);
    CHECK(mt6897_ufs_gate_lease_check(&gate, &lease, &blockers) ==
        MT6897_UFS_GATE_LEASED);
    CHECK(mt6897_ufs_gate_lease_check(&gate, &lease, &blockers) ==
        MT6897_UFS_GATE_LEASED);
    CHECK(model.verifier_calls == 1);
    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_NOT_ZERO);
    check_no_hardware(&model);

    /* authorize() cannot be used as an implicit lease check or rearm path. */
    saved_lease = lease;
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_FAULT);
    CHECK(blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(model.verifier_calls == 1);
    CHECK(gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(mt6897_ufs_gate_lease_check(&gate, &saved_lease, &blockers) ==
        MT6897_UFS_GATE_FAULT);
    CHECK(blockers == MT6897_UFS_BLOCK_BAD_STATE);
}

static void
test_each_direct_requirement(void)
{
    static const uint64_t bits[] = {
        MT6897_UFS_E_PLATFORM_MATCH,
        MT6897_UFS_E_FIRMWARE_EFFECT_CONTRACT,
        MT6897_UFS_E_RESOURCE_OWNERSHIP,
        MT6897_UFS_E_CACHE_MAINTENANCE_OWNERSHIP,
        MT6897_UFS_E_DIRECT_DMA_SELECTED,
        MT6897_UFS_E_DIRECT_DMA_APERTURE,
        MT6897_UFS_E_DIRECT_ADDRESS_TRANSLATION,
        MT6897_UFS_E_IOMMU_ABSENT
    };
    size_t index;

    for (index = 0; index < sizeof(bits) / sizeof(bits[0]); ++index) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct verifier_model model = {
            .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
        };
        uint64_t blockers = 0;

        evidence.asserted &= ~bits[index];
        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
            &model, &lease, &blockers) == MT6897_UFS_GATE_DENIED);
        CHECK(blockers == bits[index]);
        CHECK(model.verifier_calls == 0);
        CHECK(lease_is_zero(&lease));
        check_no_hardware(&model);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct verifier_model model = {
            .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
        };
        uint64_t blockers = 0;

        evidence.asserted &= ~MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
            &model, &lease, &blockers) == MT6897_UFS_GATE_DENIED);
        CHECK(blockers == MT6897_UFS_BLOCK_BOUNCE_DISPOSITION);
        CHECK(model.verifier_calls == 0);
    }
}

static void
test_bounce_and_iommu_routes(void)
{
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_evidence evidence = direct_evidence(1);
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct verifier_model model = {
        .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
    };
    uint64_t blockers = 0;

    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_LEASED);
    CHECK(mt6897_ufs_gate_lease_check(&gate, &lease, &blockers) ==
        MT6897_UFS_GATE_LEASED);
    check_no_hardware(&model);

    {
        static const uint64_t bits[] = {
            MT6897_UFS_E_IOMMU_ATTACHED,
            MT6897_UFS_E_IOMMU_DOMAIN_OWNERSHIP,
            MT6897_UFS_E_IOMMU_STREAM_ID,
            MT6897_UFS_E_IOMMU_TABLE_OWNERSHIP,
            MT6897_UFS_E_IOMMU_MAPPING_OWNERSHIP
        };
        size_t index;

        for (index = 0; index < sizeof(bits) / sizeof(bits[0]); ++index) {
            struct mt6897_ufs_gate iommu_gate = { 0 };
            struct mt6897_ufs_gate_evidence iommu = iommu_evidence();
            struct mt6897_ufs_gate_lease iommu_lease = { 0 };
            struct verifier_model iommu_model = {
                .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
            };

            iommu.asserted &= ~bits[index];
            CHECK(mt6897_ufs_gate_init(&iommu_gate, BOOT_GENERATION) ==
                MT6897_UFS_GATE_INIT_OK);
            CHECK(mt6897_ufs_gate_authorize(&iommu_gate, &iommu,
                model_verifier, &iommu_model, &iommu_lease, &blockers) ==
                MT6897_UFS_GATE_DENIED);
            CHECK(blockers == bits[index]);
            CHECK(iommu_model.verifier_calls == 0);
        }
    }
    {
        struct mt6897_ufs_gate iommu_gate = { 0 };
        struct mt6897_ufs_gate_evidence iommu = iommu_evidence();
        struct mt6897_ufs_gate_lease iommu_lease = { 0 };
        struct verifier_model iommu_model = {
            .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
        };

        CHECK(mt6897_ufs_gate_init(&iommu_gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&iommu_gate, &iommu,
            model_verifier, &iommu_model, &iommu_lease, &blockers) ==
            MT6897_UFS_GATE_LEASED);
        CHECK(mt6897_ufs_gate_lease_check(&iommu_gate, &iommu_lease,
            &blockers) == MT6897_UFS_GATE_LEASED);
        CHECK(iommu_model.verifier_calls == 1);
        check_no_hardware(&iommu_model);
    }
}

static void
expect_evidence_fault(struct mt6897_ufs_gate_evidence evidence,
    uint64_t expected)
{
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct verifier_model model = {
        .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
    };
    uint64_t blockers = 0;

    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_FAULT);
    CHECK(blockers == expected);
    CHECK(gate.state == MT6897_UFS_GATE_STATE_FAULT);
    CHECK(model.verifier_calls == 0);
    CHECK(lease_is_zero(&lease));
    check_no_hardware(&model);
}

static void
test_bad_evidence(void)
{
    struct mt6897_ufs_gate_evidence e;

    e = direct_evidence(0); e.version = 99;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_VERSION);
    e = direct_evidence(0); ++e.boot_generation;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BOOT_GENERATION);
    e = direct_evidence(0); e.route = 99;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_UNKNOWN_ROUTE);
    e = direct_evidence(0); e.known |= UINT64_C(1) << 47;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_UNKNOWN_EVIDENCE);
    e = direct_evidence(0); e.known &= ~MT6897_UFS_E_PLATFORM_MATCH;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_UNKNOWN_EVIDENCE);
    e = direct_evidence(0); e.asserted |= MT6897_UFS_E_BOUNCE_REQUIRED |
        MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP; e.known = e.asserted;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE);
    e = direct_evidence(0); e.asserted |= MT6897_UFS_E_IOMMU_ATTACHED;
    e.known = e.asserted;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE);
    e = direct_evidence(0); e.ufs_hci_base++;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0);
    /* A static hash receipt must not be all zero. */
    for (unsigned i = 0; i < 32; ++i) e.firmware_sha256[i] = 0;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0);
    for (unsigned i = 0; i < 32; ++i) e.firmware_audit_sha256[i] = 0;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0); e.cache_line_size = 63;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0); e.dma_limit--;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0);
    for (unsigned i = 0; i < 32; ++i) e.runtime_dma_report_sha256[i] = 0;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0); e.dma_size = 0;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0);
    for (unsigned i = 0; i < 32; ++i) e.prdt_report_sha256[i] = 0;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(1); e.bounce_owner_id = 0;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = iommu_evidence(); e.iommu_domain_id = 0;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
    e = direct_evidence(0); e.reserved0 = 1;
    expect_evidence_fault(e, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT);
}

static void
test_verifier_protocol(void)
{
    static const struct outcome {
        enum mt6897_ufs_gate_verdict verdict;
        unsigned mode;
        enum mt6897_ufs_gate_result result;
        uint64_t blockers;
    } outcomes[] = {
        { MT6897_UFS_GATE_VERIFY_DENY, 0, MT6897_UFS_GATE_DENIED,
            MT6897_UFS_BLOCK_VERIFIER_DENIED },
        { MT6897_UFS_GATE_VERIFY_FAULT, 0, MT6897_UFS_GATE_FAULT,
            MT6897_UFS_BLOCK_VERIFIER_FAULT },
        { MT6897_UFS_GATE_VERIFY_APPROVE, 30, MT6897_UFS_GATE_FAULT,
            MT6897_UFS_BLOCK_VERIFIER_PROTOCOL }
    };
    size_t index;

    for (index = 0; index < sizeof(outcomes) / sizeof(outcomes[0]); ++index) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct verifier_model model = {
            .verdict = outcomes[index].verdict,
            .mode = outcomes[index].mode
        };
        uint64_t blockers = 0;

        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
            &model, &lease, &blockers) == outcomes[index].result);
        CHECK(blockers == outcomes[index].blockers);
        CHECK(model.verifier_calls == 1);
        CHECK(lease_is_zero(&lease));
        check_no_hardware(&model);
    }
    for (unsigned mode = 1; mode <= 12; ++mode) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct verifier_model model = {
            .verdict = MT6897_UFS_GATE_VERIFY_APPROVE,
            .mode = mode
        };
        uint64_t blockers = 0;

        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
            &model, &lease, &blockers) == MT6897_UFS_GATE_FAULT);
        CHECK(blockers == MT6897_UFS_BLOCK_BAD_LEASE);
        CHECK(model.verifier_calls == 1);
        CHECK(lease_is_zero(&lease));
        check_no_hardware(&model);
    }
    for (unsigned mode = 20; mode <= 23; ++mode) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct verifier_model model = {
            .verdict = MT6897_UFS_GATE_VERIFY_APPROVE,
            .mode = mode,
            .gate = &gate,
            .evidence = &evidence
        };
        uint64_t blockers = 0;
        uint64_t expected = mode == 22 ? MT6897_UFS_BLOCK_BAD_STATE :
            MT6897_UFS_BLOCK_VERIFIER_PROTOCOL;

        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
            &model, &lease, &blockers) == MT6897_UFS_GATE_FAULT);
        CHECK(blockers == expected);
        CHECK(model.verifier_calls == 1);
        if (mode == 22) {
            CHECK(model.nested_result == MT6897_UFS_GATE_FAULT);
            CHECK(model.nested_blockers == MT6897_UFS_BLOCK_BAD_STATE);
        }
        check_no_hardware(&model);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        uint64_t blockers = 0;

        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, 0, 0,
            &lease, &blockers) == MT6897_UFS_GATE_DENIED);
        CHECK(blockers == MT6897_UFS_BLOCK_VERIFIER_MISSING);
    }
}

static void
test_lease_binding_and_runtime_fault(void)
{
    for (unsigned field = 0; field < 8; ++field) {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct mt6897_ufs_gate_lease wrong;
        struct verifier_model model = {
            .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
        };
        uint64_t blockers = 0;

        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
            &model, &lease, &blockers) == MT6897_UFS_GATE_LEASED);
        wrong = lease;
        switch (field) {
        case 0: ++wrong.boot_generation; break;
        case 1: ++wrong.evidence_fingerprint; break;
        case 2: ++wrong.lease_id; break;
        case 3: ++wrong.provider_epoch; break;
        case 4: ++wrong.controller_owner_id; break;
        case 5: ++wrong.dma_owner_id; break;
        case 6: ++wrong.cache_owner_id; break;
        default: ++wrong.firmware_owner_id; break;
        }
        CHECK(mt6897_ufs_gate_lease_check(&gate, &wrong, &blockers) ==
            MT6897_UFS_GATE_FAULT);
        CHECK(blockers == MT6897_UFS_BLOCK_BAD_LEASE);
        CHECK(mt6897_ufs_gate_lease_check(&gate, &lease, &blockers) ==
            MT6897_UFS_GATE_FAULT);
        CHECK(blockers == MT6897_UFS_BLOCK_BAD_LEASE);
        CHECK(model.verifier_calls == 1);
    }
    {
        struct mt6897_ufs_gate gate = { 0 };
        struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
        struct mt6897_ufs_gate_lease lease = { 0 };
        struct verifier_model model = {
            .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
        };
        uint64_t blockers = 0;

        CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
            MT6897_UFS_GATE_INIT_OK);
        CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
            &model, &lease, &blockers) == MT6897_UFS_GATE_LEASED);
        CHECK(mt6897_ufs_gate_fault(&gate, 0, &blockers) ==
            MT6897_UFS_GATE_FAULT);
        CHECK(blockers == MT6897_UFS_BLOCK_PROVIDER_RUNTIME);
        /* The immutable bytes may remain, but terminal state revokes use. */
        CHECK(!lease_is_zero(&gate.lease));
        CHECK(mt6897_ufs_gate_lease_check(&gate, &lease, &blockers) ==
            MT6897_UFS_GATE_FAULT);
        CHECK(blockers == MT6897_UFS_BLOCK_PROVIDER_RUNTIME);
    }
}

static void
test_initialization_and_arguments(void)
{
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_evidence evidence = direct_evidence(0);
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct verifier_model model = {
        .verdict = MT6897_UFS_GATE_VERIFY_APPROVE
    };
    uint64_t blockers = UINT64_C(0xabc);

    CHECK(mt6897_ufs_gate_init(0, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_ARGUMENT);
    CHECK(mt6897_ufs_gate_init(&gate, 0) ==
        MT6897_UFS_GATE_INIT_GENERATION);
    gate.state = 1;
    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_NOT_ZERO);
    gate = (struct mt6897_ufs_gate){ 0 };
    CHECK(mt6897_ufs_gate_authorize(&gate, &evidence, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_FAULT);
    CHECK(blockers == MT6897_UFS_BLOCK_BAD_STATE);
    CHECK(model.verifier_calls == 0);
    CHECK(mt6897_ufs_gate_init(&gate, BOOT_GENERATION) ==
        MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&gate, 0, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_FAULT);
    CHECK(blockers == MT6897_UFS_BLOCK_BAD_ARGUMENT);
    CHECK(model.verifier_calls == 0);
    CHECK(mt6897_ufs_gate_authorize(0, &evidence, model_verifier,
        &model, &lease, &blockers) == MT6897_UFS_GATE_ARGUMENT);
    CHECK(mt6897_ufs_gate_lease_check(0, &lease, &blockers) ==
        MT6897_UFS_GATE_ARGUMENT);
    CHECK(mt6897_ufs_gate_fault(0, 0, &blockers) ==
        MT6897_UFS_GATE_ARGUMENT);
}

static void
test_fingerprint_binding(void)
{
    struct mt6897_ufs_gate_evidence left = direct_evidence(0);
    struct mt6897_ufs_gate_evidence right = left;
    uint64_t original = mt6897_ufs_gate_evidence_fingerprint(&left);

    CHECK(original != 0);
    CHECK(original == mt6897_ufs_gate_evidence_fingerprint(&right));
    ++right.dma_size;
    CHECK(original != mt6897_ufs_gate_evidence_fingerprint(&right));
    right = left;
    right.fdt_sha256[31] ^= 1;
    CHECK(original != mt6897_ufs_gate_evidence_fingerprint(&right));
    CHECK(mt6897_ufs_gate_evidence_fingerprint(0) == 0);
}

int
main(void)
{
    test_saved_receipts();
    test_saved_evidence_is_denied();
    test_direct_lease();
    test_each_direct_requirement();
    test_bounce_and_iommu_routes();
    test_bad_evidence();
    test_verifier_protocol();
    test_lease_binding_and_runtime_fault();
    test_initialization_and_arguments();
    test_fingerprint_binding();
    (void)printf("DUCHAMP current evidence decision=denied "
        "boot_generation=0x202611030001 "
        "blocker_mask=0x000100000000040e verifier_calls=0 "
        "hardware_access=false mmio_access=false smc_execution=false "
        "dma_access=false phone_access=false\n");
    (void)printf("%u MT6897 UFS lease-gate checks passed; no MMIO/SMC/DMA calls\n",
        checks);
    return 0;
}
