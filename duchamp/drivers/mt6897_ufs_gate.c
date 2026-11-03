#include "mt6897_ufs_gate.h"

#define MT6897_UFS_GATE_COOKIE UINT64_C(0x6d74363839377566)
#define MT6897_UFS_E_DIRECT_ONLY \
    (MT6897_UFS_E_DIRECT_BASE_REQUIRED | MT6897_UFS_E_BOUNCE_REQUIRED | \
     MT6897_UFS_E_BOUNCE_NOT_REQUIRED | \
     MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP)
#define MT6897_UFS_E_IOMMU_ONLY MT6897_UFS_E_IOMMU_REQUIRED

_Static_assert((MT6897_UFS_E_ALL & MT6897_UFS_BLOCK_CONTROL_MASK) == 0,
    "evidence and control blockers must not overlap");
_Static_assert((MT6897_UFS_E_DIRECT_ONLY & MT6897_UFS_E_IOMMU_ONLY) == 0,
    "direct and IOMMU evidence must be disjoint");

#ifdef MT6897_UFS_GATE_TEST_HOOKS
extern void mt6897_ufs_gate_test_after_claim(void);
extern void mt6897_ufs_gate_test_before_authorize_latch_publish(void);
extern void mt6897_ufs_gate_test_before_lease_publish(void);
#endif

static uint32_t
gate_state_load(const struct mt6897_ufs_gate *gate)
{
    return __atomic_load_n(&gate->state, __ATOMIC_ACQUIRE);
}

static void
gate_state_store(struct mt6897_ufs_gate *gate,
    enum mt6897_ufs_gate_state state)
{
    __atomic_store_n(&gate->state, (uint32_t)state, __ATOMIC_RELEASE);
}

static int
gate_state_claim(struct mt6897_ufs_gate *gate, uint32_t *expected,
    enum mt6897_ufs_gate_state desired)
{
    return __atomic_compare_exchange_n(&gate->state, expected,
        (uint32_t)desired, 0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE);
}

static int32_t
gate_result_load(const struct mt6897_ufs_gate *gate)
{
    return __atomic_load_n(&gate->result, __ATOMIC_ACQUIRE);
}

static void
gate_result_store(struct mt6897_ufs_gate *gate,
    enum mt6897_ufs_gate_result result)
{
    __atomic_store_n(&gate->result, (int32_t)result, __ATOMIC_RELEASE);
}

static uint64_t
gate_blockers_load(const struct mt6897_ufs_gate *gate)
{
    return __atomic_load_n(&gate->blockers, __ATOMIC_ACQUIRE);
}

static void
gate_blockers_store(struct mt6897_ufs_gate *gate, uint64_t blockers)
{
    __atomic_store_n(&gate->blockers, blockers, __ATOMIC_RELEASE);
}

static uint32_t
gate_contention_load(const struct mt6897_ufs_gate *gate)
{
    return __atomic_load_n(&gate->contention, __ATOMIC_ACQUIRE);
}

static void
gate_contention_store(struct mt6897_ufs_gate *gate, uint32_t value)
{
    __atomic_store_n(&gate->contention, value, __ATOMIC_RELEASE);
}

static void
zero_lease(struct mt6897_ufs_gate_lease *lease)
{
    if (lease == 0) {
        return;
    }
    lease->version = 0;
    lease->flags = 0;
    lease->boot_generation = 0;
    lease->evidence_fingerprint = 0;
    lease->lease_id = 0;
    lease->provider_epoch = 0;
    lease->controller_owner_id = 0;
    lease->phy_owner_id = 0;
    lease->dma_owner_id = 0;
    lease->cache_owner_id = 0;
    lease->firmware_owner_id = 0;
}

static int
bytes_zero(const uint8_t *bytes, uint32_t count)
{
    uint32_t index;

    for (index = 0; index < count; ++index) {
        if (bytes[index] != 0) {
            return 0;
        }
    }
    return 1;
}

static int
bytes_equal(const uint8_t *left, const uint8_t *right, uint32_t count)
{
    uint32_t index;

    for (index = 0; index < count; ++index) {
        if (left[index] != right[index]) {
            return 0;
        }
    }
    return 1;
}

static int
bytes_nonzero(const uint8_t *bytes, uint32_t count)
{
    return !bytes_zero(bytes, count);
}

static int
lease_zero(const struct mt6897_ufs_gate_lease *lease)
{
    return lease->version == 0 && lease->flags == 0 &&
        lease->boot_generation == 0 && lease->evidence_fingerprint == 0 &&
        lease->lease_id == 0 && lease->provider_epoch == 0 &&
        lease->controller_owner_id == 0 && lease->phy_owner_id == 0 &&
        lease->dma_owner_id == 0 && lease->cache_owner_id == 0 &&
        lease->firmware_owner_id == 0;
}

static int
gate_zero(const struct mt6897_ufs_gate *gate)
{
    return gate->cookie == 0 && gate->boot_generation == 0 &&
        gate->evidence_fingerprint == 0 && gate->blockers == 0 &&
        gate->state == 0 && gate->contention == 0 && gate->result == 0 &&
        gate->reserved_state == 0 && lease_zero(&gate->lease);
}

static void
copy_evidence(struct mt6897_ufs_gate_evidence *destination,
    const struct mt6897_ufs_gate_evidence *source)
{
    uint32_t index;

    destination->version = source->version;
    destination->route = source->route;
    destination->boot_generation = source->boot_generation;
    destination->known = source->known;
    destination->asserted = source->asserted;
    for (index = 0; index < 32; ++index) {
        destination->fdt_sha256[index] = source->fdt_sha256[index];
        destination->firmware_sha256[index] = source->firmware_sha256[index];
        destination->firmware_audit_sha256[index] =
            source->firmware_audit_sha256[index];
        destination->runtime_dma_report_sha256[index] =
            source->runtime_dma_report_sha256[index];
        destination->prdt_report_sha256[index] =
            source->prdt_report_sha256[index];
    }
    destination->ufs_hci_base = source->ufs_hci_base;
    destination->ufs_hci_size = source->ufs_hci_size;
    destination->ufs_phy_base = source->ufs_phy_base;
    destination->ufs_phy_size = source->ufs_phy_size;
    destination->firmware_service_id = source->firmware_service_id;
    destination->firmware_refclk_selector =
        source->firmware_refclk_selector;
    destination->firmware_mtcmos_selector =
        source->firmware_mtcmos_selector;
    destination->firmware_mcq_selector = source->firmware_mcq_selector;
    destination->dma_cpu_start = source->dma_cpu_start;
    destination->dma_device_start = source->dma_device_start;
    destination->dma_size = source->dma_size;
    destination->dma_limit = source->dma_limit;
    destination->dma_address_bits = source->dma_address_bits;
    destination->cache_line_size = source->cache_line_size;
    destination->bounce_start = source->bounce_start;
    destination->bounce_size = source->bounce_size;
    destination->bounce_owner_id = source->bounce_owner_id;
    destination->iommu_stream_id = source->iommu_stream_id;
    destination->reserved0 = source->reserved0;
    destination->iommu_domain_id = source->iommu_domain_id;
    destination->iommu_table_id = source->iommu_table_id;
    destination->iommu_mapping_epoch = source->iommu_mapping_epoch;
}

static void
zero_evidence(struct mt6897_ufs_gate_evidence *evidence)
{
    uint32_t index;

    evidence->version = 0;
    evidence->route = 0;
    evidence->boot_generation = 0;
    evidence->known = 0;
    evidence->asserted = 0;
    for (index = 0; index < 32; ++index) {
        evidence->fdt_sha256[index] = 0;
        evidence->firmware_sha256[index] = 0;
        evidence->firmware_audit_sha256[index] = 0;
        evidence->runtime_dma_report_sha256[index] = 0;
        evidence->prdt_report_sha256[index] = 0;
    }
    evidence->ufs_hci_base = 0;
    evidence->ufs_hci_size = 0;
    evidence->ufs_phy_base = 0;
    evidence->ufs_phy_size = 0;
    evidence->firmware_service_id = 0;
    evidence->firmware_refclk_selector = 0;
    evidence->firmware_mtcmos_selector = 0;
    evidence->firmware_mcq_selector = 0;
    evidence->dma_cpu_start = 0;
    evidence->dma_device_start = 0;
    evidence->dma_size = 0;
    evidence->dma_limit = 0;
    evidence->dma_address_bits = 0;
    evidence->cache_line_size = 0;
    evidence->bounce_start = 0;
    evidence->bounce_size = 0;
    evidence->bounce_owner_id = 0;
    evidence->iommu_stream_id = 0;
    evidence->reserved0 = 0;
    evidence->iommu_domain_id = 0;
    evidence->iommu_table_id = 0;
    evidence->iommu_mapping_epoch = 0;
}

static void
copy_request(struct mt6897_ufs_gate_verifier_request *destination,
    const struct mt6897_ufs_gate_verifier_request *source)
{
    destination->version = source->version;
    destination->route = source->route;
    destination->required = source->required;
    destination->evidence_fingerprint = source->evidence_fingerprint;
    copy_evidence(&destination->evidence, &source->evidence);
}

static void
copy_lease(struct mt6897_ufs_gate_lease *destination,
    const struct mt6897_ufs_gate_lease *source)
{
    destination->version = source->version;
    destination->flags = source->flags;
    destination->boot_generation = source->boot_generation;
    destination->evidence_fingerprint = source->evidence_fingerprint;
    destination->lease_id = source->lease_id;
    destination->provider_epoch = source->provider_epoch;
    destination->controller_owner_id = source->controller_owner_id;
    destination->phy_owner_id = source->phy_owner_id;
    destination->dma_owner_id = source->dma_owner_id;
    destination->cache_owner_id = source->cache_owner_id;
    destination->firmware_owner_id = source->firmware_owner_id;
}

static uint64_t
hash_byte(uint64_t hash, uint8_t value)
{
    return (hash ^ value) * UINT64_C(1099511628211);
}

static uint64_t
hash_u32(uint64_t hash, uint32_t value)
{
    unsigned shift;

    for (shift = 0; shift < 32; shift += 8) {
        hash = hash_byte(hash, (uint8_t)(value >> shift));
    }
    return hash;
}

static uint64_t
hash_u64(uint64_t hash, uint64_t value)
{
    unsigned shift;

    for (shift = 0; shift < 64; shift += 8) {
        hash = hash_byte(hash, (uint8_t)(value >> shift));
    }
    return hash;
}

static uint64_t
hash_bytes(uint64_t hash, const uint8_t *bytes, uint32_t count)
{
    uint32_t index;

    for (index = 0; index < count; ++index) {
        hash = hash_byte(hash, bytes[index]);
    }
    return hash;
}

uint64_t
mt6897_ufs_gate_evidence_fingerprint(
    const struct mt6897_ufs_gate_evidence *evidence)
{
    uint64_t hash = UINT64_C(1469598103934665603);

    if (evidence == 0) {
        return 0;
    }
    hash = hash_u32(hash, evidence->version);
    hash = hash_u32(hash, evidence->route);
    hash = hash_u64(hash, evidence->boot_generation);
    hash = hash_u64(hash, evidence->known);
    hash = hash_u64(hash, evidence->asserted);
    hash = hash_bytes(hash, evidence->fdt_sha256, 32);
    hash = hash_bytes(hash, evidence->firmware_sha256, 32);
    hash = hash_bytes(hash, evidence->firmware_audit_sha256, 32);
    hash = hash_bytes(hash, evidence->runtime_dma_report_sha256, 32);
    hash = hash_bytes(hash, evidence->prdt_report_sha256, 32);
    hash = hash_u64(hash, evidence->ufs_hci_base);
    hash = hash_u64(hash, evidence->ufs_hci_size);
    hash = hash_u64(hash, evidence->ufs_phy_base);
    hash = hash_u64(hash, evidence->ufs_phy_size);
    hash = hash_u32(hash, evidence->firmware_service_id);
    hash = hash_u32(hash, evidence->firmware_refclk_selector);
    hash = hash_u32(hash, evidence->firmware_mtcmos_selector);
    hash = hash_u32(hash, evidence->firmware_mcq_selector);
    hash = hash_u64(hash, evidence->dma_cpu_start);
    hash = hash_u64(hash, evidence->dma_device_start);
    hash = hash_u64(hash, evidence->dma_size);
    hash = hash_u64(hash, evidence->dma_limit);
    hash = hash_u32(hash, evidence->dma_address_bits);
    hash = hash_u32(hash, evidence->cache_line_size);
    hash = hash_u64(hash, evidence->bounce_start);
    hash = hash_u64(hash, evidence->bounce_size);
    hash = hash_u64(hash, evidence->bounce_owner_id);
    hash = hash_u32(hash, evidence->iommu_stream_id);
    hash = hash_u32(hash, evidence->reserved0);
    hash = hash_u64(hash, evidence->iommu_domain_id);
    hash = hash_u64(hash, evidence->iommu_table_id);
    return hash_u64(hash, evidence->iommu_mapping_epoch);
}

static int
evidence_equal(const struct mt6897_ufs_gate_evidence *left,
    const struct mt6897_ufs_gate_evidence *right)
{
    return left->version == right->version &&
        left->route == right->route &&
        left->boot_generation == right->boot_generation &&
        left->known == right->known &&
        left->asserted == right->asserted &&
        bytes_equal(left->fdt_sha256, right->fdt_sha256, 32) &&
        bytes_equal(left->firmware_sha256, right->firmware_sha256, 32) &&
        bytes_equal(left->firmware_audit_sha256,
            right->firmware_audit_sha256, 32) &&
        bytes_equal(left->runtime_dma_report_sha256,
            right->runtime_dma_report_sha256, 32) &&
        bytes_equal(left->prdt_report_sha256,
            right->prdt_report_sha256, 32) &&
        left->ufs_hci_base == right->ufs_hci_base &&
        left->ufs_hci_size == right->ufs_hci_size &&
        left->ufs_phy_base == right->ufs_phy_base &&
        left->ufs_phy_size == right->ufs_phy_size &&
        left->firmware_service_id == right->firmware_service_id &&
        left->firmware_refclk_selector == right->firmware_refclk_selector &&
        left->firmware_mtcmos_selector == right->firmware_mtcmos_selector &&
        left->firmware_mcq_selector == right->firmware_mcq_selector &&
        left->dma_cpu_start == right->dma_cpu_start &&
        left->dma_device_start == right->dma_device_start &&
        left->dma_size == right->dma_size &&
        left->dma_limit == right->dma_limit &&
        left->dma_address_bits == right->dma_address_bits &&
        left->cache_line_size == right->cache_line_size &&
        left->bounce_start == right->bounce_start &&
        left->bounce_size == right->bounce_size &&
        left->bounce_owner_id == right->bounce_owner_id &&
        left->iommu_stream_id == right->iommu_stream_id &&
        left->reserved0 == right->reserved0 &&
        left->iommu_domain_id == right->iommu_domain_id &&
        left->iommu_table_id == right->iommu_table_id &&
        left->iommu_mapping_epoch == right->iommu_mapping_epoch;
}

static int
request_equal(const struct mt6897_ufs_gate_verifier_request *left,
    const struct mt6897_ufs_gate_verifier_request *right)
{
    return left->version == right->version && left->route == right->route &&
        left->required == right->required &&
        left->evidence_fingerprint == right->evidence_fingerprint &&
        evidence_equal(&left->evidence, &right->evidence);
}

static int
lease_equal(const struct mt6897_ufs_gate_lease *left,
    const struct mt6897_ufs_gate_lease *right)
{
    return left->version == right->version && left->flags == right->flags &&
        left->boot_generation == right->boot_generation &&
        left->evidence_fingerprint == right->evidence_fingerprint &&
        left->lease_id == right->lease_id &&
        left->provider_epoch == right->provider_epoch &&
        left->controller_owner_id == right->controller_owner_id &&
        left->phy_owner_id == right->phy_owner_id &&
        left->dma_owner_id == right->dma_owner_id &&
        left->cache_owner_id == right->cache_owner_id &&
        left->firmware_owner_id == right->firmware_owner_id;
}

static int
lease_valid(const struct mt6897_ufs_gate_lease *lease,
    uint64_t boot_generation, uint64_t fingerprint)
{
    return lease->version == MT6897_UFS_GATE_LEASE_VERSION &&
        (lease->flags & MT6897_UFS_LEASE_REQUIRED_FLAGS) ==
            MT6897_UFS_LEASE_REQUIRED_FLAGS &&
        (lease->flags & ~MT6897_UFS_LEASE_REQUIRED_FLAGS) == 0 &&
        lease->boot_generation == boot_generation &&
        lease->evidence_fingerprint == fingerprint &&
        lease->lease_id != 0 && lease->provider_epoch != 0 &&
        lease->controller_owner_id != 0 && lease->phy_owner_id != 0 &&
        lease->dma_owner_id != 0 && lease->cache_owner_id != 0 &&
        lease->firmware_owner_id != 0;
}

static enum mt6897_ufs_gate_result
latch(struct mt6897_ufs_gate *gate, enum mt6897_ufs_gate_state state,
    enum mt6897_ufs_gate_result result, uint64_t blockers,
    uint64_t *blockers_out)
{
    gate_result_store(gate, result);
    gate_blockers_store(gate, blockers);
    gate_state_store(gate, state);
    *blockers_out = blockers;
    return result;
}

static enum mt6897_ufs_gate_result
latched_result(struct mt6897_ufs_gate *gate, uint64_t *blockers_out)
{
    uint32_t state = gate_state_load(gate);

    if (state == (uint32_t)MT6897_UFS_GATE_STATE_DENIED &&
        gate_result_load(gate) == (int32_t)MT6897_UFS_GATE_DENIED &&
        gate_blockers_load(gate) != 0) {
        *blockers_out = gate_blockers_load(gate);
        return MT6897_UFS_GATE_DENIED;
    }
    if (state == (uint32_t)MT6897_UFS_GATE_STATE_FAULT &&
        gate_result_load(gate) == (int32_t)MT6897_UFS_GATE_FAULT &&
        gate_blockers_load(gate) != 0) {
        *blockers_out = gate_blockers_load(gate);
        return MT6897_UFS_GATE_FAULT;
    }
    return latch(gate, MT6897_UFS_GATE_STATE_FAULT,
        MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_BAD_STATE, blockers_out);
}

static enum mt6897_ufs_gate_result
terminal_fault(struct mt6897_ufs_gate *gate, uint64_t blocker,
    uint64_t *blockers_out)
{
    uint32_t state;
    uint32_t expected;

    /*
     * This flag is a sticky terminal request, not merely a diagnostic.  The
     * authorization owner checks it on both sides of every publication
     * point, including while the state is temporarily CONTENDED.
     */
    gate_contention_store(gate, 1);
    for (;;) {
        state = gate_state_load(gate);
        if (state == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
            return latched_result(gate, blockers_out);
        }
        if (state == (uint32_t)MT6897_UFS_GATE_STATE_CONTENDED ||
            state ==
                (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED) {
            *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
            return MT6897_UFS_GATE_FAULT;
        }
        if (state ==
            (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE) {
            expected = state;
            if (gate_state_claim(gate, &expected,
                MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED)) {
                *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
                return MT6897_UFS_GATE_FAULT;
            }
            continue;
        }
        expected = state;
        if (gate_state_claim(gate, &expected,
            MT6897_UFS_GATE_STATE_CONTENDED)) {
            return latch(gate, MT6897_UFS_GATE_STATE_FAULT,
                MT6897_UFS_GATE_FAULT, blocker, blockers_out);
        }
    }
}

static enum mt6897_ufs_gate_result
authorize_latch(struct mt6897_ufs_gate *gate,
    enum mt6897_ufs_gate_state expected_state,
    enum mt6897_ufs_gate_state terminal_state,
    enum mt6897_ufs_gate_result result, uint64_t blockers,
    uint64_t *blockers_out)
{
    uint32_t expected = (uint32_t)expected_state;
    enum mt6897_ufs_gate_result published;

    if (gate_contention_load(gate) != 0) {
        terminal_state = MT6897_UFS_GATE_STATE_FAULT;
        result = MT6897_UFS_GATE_FAULT;
        blockers = MT6897_UFS_BLOCK_BAD_STATE;
    }
    if (gate_state_claim(gate, &expected,
        MT6897_UFS_GATE_STATE_CONTENDED)) {
        if (gate_contention_load(gate) != 0) {
            terminal_state = MT6897_UFS_GATE_STATE_FAULT;
            result = MT6897_UFS_GATE_FAULT;
            blockers = MT6897_UFS_BLOCK_BAD_STATE;
        }
#ifdef MT6897_UFS_GATE_TEST_HOOKS
        mt6897_ufs_gate_test_before_authorize_latch_publish();
#endif
        if (gate_contention_load(gate) != 0) {
            terminal_state = MT6897_UFS_GATE_STATE_FAULT;
            result = MT6897_UFS_GATE_FAULT;
            blockers = MT6897_UFS_BLOCK_BAD_STATE;
        }
        published = latch(gate, terminal_state, result, blockers,
            blockers_out);
        if (result != MT6897_UFS_GATE_FAULT &&
            gate_contention_load(gate) != 0) {
            return terminal_fault(gate, MT6897_UFS_BLOCK_BAD_STATE,
                blockers_out);
        }
        return published;
    }
    if (expected_state == MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE &&
        expected ==
            (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED) {
        return latch(gate, MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    if (expected == (uint32_t)MT6897_UFS_GATE_STATE_DENIED ||
        expected == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
        return latched_result(gate, blockers_out);
    }
    if (expected == (uint32_t)MT6897_UFS_GATE_STATE_CONTENDED ||
        expected ==
            (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED) {
        *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
        return MT6897_UFS_GATE_FAULT;
    }
    return terminal_fault(gate, MT6897_UFS_BLOCK_VERIFIER_PROTOCOL,
        blockers_out);
}

enum mt6897_ufs_gate_init_result
mt6897_ufs_gate_init(struct mt6897_ufs_gate *gate, uint64_t boot_generation)
{
    if (gate == 0) {
        return MT6897_UFS_GATE_INIT_ARGUMENT;
    }
    if (boot_generation == 0) {
        return MT6897_UFS_GATE_INIT_GENERATION;
    }
    if (!gate_zero(gate)) {
        return MT6897_UFS_GATE_INIT_NOT_ZERO;
    }
    gate->cookie = MT6897_UFS_GATE_COOKIE;
    gate->boot_generation = boot_generation;
    gate_result_store(gate, MT6897_UFS_GATE_FAULT);
    gate_blockers_store(gate, MT6897_UFS_BLOCK_BAD_STATE);
    gate_contention_store(gate, 0);
    gate_state_store(gate, MT6897_UFS_GATE_STATE_ARMED);
    return MT6897_UFS_GATE_INIT_OK;
}

static uint64_t
receipt_faults(const struct mt6897_ufs_gate_evidence *evidence)
{
    uint64_t asserted = evidence->asserted;
    uint64_t end;

    if ((asserted & MT6897_UFS_E_PLATFORM_MATCH) != 0 &&
        (!bytes_nonzero(evidence->fdt_sha256, 32) ||
         evidence->ufs_hci_base != MT6897_UFS_DUCHAMP_HCI_BASE ||
         evidence->ufs_hci_size != MT6897_UFS_DUCHAMP_HCI_SIZE ||
         evidence->ufs_phy_base != MT6897_UFS_DUCHAMP_PHY_BASE ||
         evidence->ufs_phy_size != MT6897_UFS_DUCHAMP_PHY_SIZE)) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    if ((asserted & MT6897_UFS_E_FIRMWARE_EFFECT_CONTRACT) != 0 &&
        (!bytes_nonzero(evidence->firmware_sha256, 32) ||
         !bytes_nonzero(evidence->firmware_audit_sha256, 32) ||
         evidence->firmware_service_id != MT6897_UFS_DUCHAMP_SIP_UFS64 ||
         evidence->firmware_refclk_selector != 8 ||
         evidence->firmware_mtcmos_selector != 512 ||
         evidence->firmware_mcq_selector != 1024)) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    if ((asserted & MT6897_UFS_E_RESOURCE_OWNERSHIP) != 0 &&
        (evidence->ufs_hci_base != MT6897_UFS_DUCHAMP_HCI_BASE ||
         evidence->ufs_hci_size != MT6897_UFS_DUCHAMP_HCI_SIZE ||
         evidence->ufs_phy_base != MT6897_UFS_DUCHAMP_PHY_BASE ||
         evidence->ufs_phy_size != MT6897_UFS_DUCHAMP_PHY_SIZE)) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    if ((asserted & MT6897_UFS_E_CACHE_MAINTENANCE_OWNERSHIP) != 0 &&
        (((asserted & MT6897_UFS_E_NONCOHERENT_DEVICE) == 0) ||
         evidence->cache_line_size == 0 ||
         (evidence->cache_line_size & (evidence->cache_line_size - 1)) != 0)) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    if ((asserted & MT6897_UFS_E_DIRECT_DMA_APERTURE) != 0 &&
        (!bytes_nonzero(evidence->runtime_dma_report_sha256, 32) ||
         evidence->dma_address_bits != MT6897_UFS_DUCHAMP_DMA_BITS ||
         evidence->dma_limit != MT6897_UFS_DUCHAMP_DMA_LIMIT)) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    if ((asserted & MT6897_UFS_E_DIRECT_ADDRESS_TRANSLATION) != 0 &&
        (!bytes_nonzero(evidence->prdt_report_sha256, 32) ||
         evidence->dma_size == 0 ||
         evidence->dma_device_start > evidence->dma_limit ||
         evidence->dma_size - 1 >
            evidence->dma_limit - evidence->dma_device_start ||
         evidence->dma_cpu_start > UINT64_MAX - (evidence->dma_size - 1))) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    if ((asserted & MT6897_UFS_E_BOUNCE_REQUIRED) != 0) {
        if (evidence->bounce_size == 0 || evidence->bounce_owner_id == 0 ||
            evidence->bounce_start > UINT64_MAX - (evidence->bounce_size - 1)) {
            return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
        }
        end = evidence->bounce_start + evidence->bounce_size - 1;
        if (end > evidence->dma_limit) {
            return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
        }
    }
    if ((asserted & MT6897_UFS_E_BOUNCE_NOT_REQUIRED) != 0 &&
        (evidence->bounce_start != 0 || evidence->bounce_size != 0 ||
         evidence->bounce_owner_id != 0)) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    if (evidence->route == (uint32_t)MT6897_UFS_GATE_ROUTE_IOMMU &&
        (asserted & MT6897_UFS_E_IOMMU_REQUIRED) ==
            MT6897_UFS_E_IOMMU_REQUIRED &&
        (evidence->iommu_stream_id == UINT32_MAX ||
         evidence->iommu_domain_id == 0 || evidence->iommu_table_id == 0 ||
         evidence->iommu_mapping_epoch == 0)) {
        return MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    return 0;
}

enum mt6897_ufs_gate_result
mt6897_ufs_gate_authorize(struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_evidence *evidence,
    mt6897_ufs_gate_verifier_fn verifier, void *verifier_context,
    struct mt6897_ufs_gate_lease *lease_out, uint64_t *blockers_out)
{
    struct mt6897_ufs_gate_evidence saved_evidence;
    struct mt6897_ufs_gate_verifier_request request;
    struct mt6897_ufs_gate_verifier_request saved_request;
    struct mt6897_ufs_gate_lease candidate;
    enum mt6897_ufs_gate_verdict verdict;
    uint64_t faults = 0;
    uint64_t missing = 0;
    uint64_t required;
    uint64_t fingerprint;
    uint64_t asserted;
    uint32_t state;
    uint32_t expected;

    if (gate == 0 || lease_out == 0 || blockers_out == 0) {
        return MT6897_UFS_GATE_ARGUMENT;
    }
    zero_lease(lease_out);
    if (gate->cookie != MT6897_UFS_GATE_COOKIE) {
        *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
        return MT6897_UFS_GATE_FAULT;
    }
    state = gate_state_load(gate);
    if (state == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
        return latched_result(gate, blockers_out);
    }
    if (state != (uint32_t)MT6897_UFS_GATE_STATE_ARMED) {
        gate_contention_store(gate, 1);
        return terminal_fault(gate, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    expected = (uint32_t)MT6897_UFS_GATE_STATE_ARMED;
    if (!gate_state_claim(gate, &expected,
        MT6897_UFS_GATE_STATE_VERIFYING)) {
        gate_contention_store(gate, 1);
        return terminal_fault(gate, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
#ifdef MT6897_UFS_GATE_TEST_HOOKS
    mt6897_ufs_gate_test_after_claim();
#endif
    if (gate_result_load(gate) != (int32_t)MT6897_UFS_GATE_FAULT ||
        gate_blockers_load(gate) != MT6897_UFS_BLOCK_BAD_STATE ||
        gate->boot_generation == 0 || gate->evidence_fingerprint != 0 ||
        gate->reserved_state != 0 || !lease_zero(&gate->lease)) {
        return authorize_latch(gate, MT6897_UFS_GATE_STATE_VERIFYING,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_BAD_STATE, blockers_out);
    }
    if (evidence == 0) {
        return authorize_latch(gate, MT6897_UFS_GATE_STATE_VERIFYING,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_BAD_ARGUMENT,
            blockers_out);
    }

    copy_evidence(&saved_evidence, evidence);
    asserted = saved_evidence.asserted;
    if (saved_evidence.version != MT6897_UFS_GATE_EVIDENCE_VERSION) {
        faults |= MT6897_UFS_BLOCK_BAD_VERSION;
    }
    if (saved_evidence.boot_generation != gate->boot_generation ||
        saved_evidence.boot_generation == 0) {
        faults |= MT6897_UFS_BLOCK_BOOT_GENERATION;
    }
    if (saved_evidence.route != (uint32_t)MT6897_UFS_GATE_ROUTE_DIRECT_DMA &&
        saved_evidence.route != (uint32_t)MT6897_UFS_GATE_ROUTE_IOMMU) {
        faults |= MT6897_UFS_BLOCK_UNKNOWN_ROUTE;
    }
    if (((saved_evidence.known | asserted) & ~MT6897_UFS_E_ALL) != 0 ||
        (asserted & ~saved_evidence.known) != 0) {
        faults |= MT6897_UFS_BLOCK_UNKNOWN_EVIDENCE;
    }
    if ((asserted & (MT6897_UFS_E_BOUNCE_REQUIRED |
            MT6897_UFS_E_BOUNCE_NOT_REQUIRED)) ==
        (MT6897_UFS_E_BOUNCE_REQUIRED |
            MT6897_UFS_E_BOUNCE_NOT_REQUIRED)) {
        faults |= MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE;
    }
    if ((asserted & MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP) != 0 &&
        (asserted & MT6897_UFS_E_BOUNCE_REQUIRED) == 0) {
        faults |= MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE;
    }
    if (saved_evidence.route ==
            (uint32_t)MT6897_UFS_GATE_ROUTE_DIRECT_DMA &&
        (asserted & MT6897_UFS_E_IOMMU_ONLY) != 0) {
        faults |= MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE;
    }
    if (saved_evidence.route == (uint32_t)MT6897_UFS_GATE_ROUTE_IOMMU &&
        (asserted & MT6897_UFS_E_DIRECT_ONLY) != 0) {
        faults |= MT6897_UFS_BLOCK_CONTRADICTORY_EVIDENCE;
    }
    if (saved_evidence.reserved0 != 0) {
        faults |= MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT;
    }
    /* Structural/protocol errors take precedence over receipt details. */
    if (faults == 0) {
        faults = receipt_faults(&saved_evidence);
    }
    if (faults != 0) {
        return authorize_latch(gate, MT6897_UFS_GATE_STATE_VERIFYING,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, faults, blockers_out);
    }

    required = MT6897_UFS_E_COMMON_REQUIRED;
    if (saved_evidence.route ==
        (uint32_t)MT6897_UFS_GATE_ROUTE_DIRECT_DMA) {
        required |= MT6897_UFS_E_DIRECT_BASE_REQUIRED;
        if ((asserted & MT6897_UFS_E_BOUNCE_REQUIRED) != 0) {
            required |= MT6897_UFS_E_BOUNCE_REQUIRED |
                MT6897_UFS_E_BOUNCE_MEMORY_OWNERSHIP;
        } else if ((asserted & MT6897_UFS_E_BOUNCE_NOT_REQUIRED) != 0) {
            required |= MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
        } else {
            missing |= MT6897_UFS_BLOCK_BOUNCE_DISPOSITION;
        }
    } else {
        required |= MT6897_UFS_E_IOMMU_REQUIRED;
    }
    missing |= required & ~asserted;
    if (missing != 0) {
        return authorize_latch(gate, MT6897_UFS_GATE_STATE_VERIFYING,
            MT6897_UFS_GATE_STATE_DENIED,
            MT6897_UFS_GATE_DENIED, missing, blockers_out);
    }
    if (verifier == 0) {
        return authorize_latch(gate, MT6897_UFS_GATE_STATE_VERIFYING,
            MT6897_UFS_GATE_STATE_DENIED,
            MT6897_UFS_GATE_DENIED, MT6897_UFS_BLOCK_VERIFIER_MISSING,
            blockers_out);
    }

    fingerprint = mt6897_ufs_gate_evidence_fingerprint(&saved_evidence);
    if (fingerprint == 0) {
        return authorize_latch(gate, MT6897_UFS_GATE_STATE_VERIFYING,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_BAD_EVIDENCE_RECEIPT,
            blockers_out);
    }
    request.version = MT6897_UFS_GATE_EVIDENCE_VERSION;
    request.route = saved_evidence.route;
    request.required = required;
    request.evidence_fingerprint = fingerprint;
    copy_evidence(&request.evidence, &saved_evidence);
    copy_request(&saved_request, &request);
    zero_lease(&candidate);

    if (gate_contention_load(gate) != 0) {
        return authorize_latch(gate, MT6897_UFS_GATE_STATE_VERIFYING,
            MT6897_UFS_GATE_STATE_FAULT, MT6897_UFS_GATE_FAULT,
            MT6897_UFS_BLOCK_BAD_STATE, blockers_out);
    }
    gate_result_store(gate, MT6897_UFS_GATE_FAULT);
    gate_blockers_store(gate, MT6897_UFS_BLOCK_VERIFIER_FAULT);
    expected = (uint32_t)MT6897_UFS_GATE_STATE_VERIFYING;
    if (!gate_state_claim(gate, &expected,
        MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE)) {
        if (expected == (uint32_t)MT6897_UFS_GATE_STATE_DENIED ||
            expected == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
            return latched_result(gate, blockers_out);
        }
        *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
        return MT6897_UFS_GATE_FAULT;
    }
    if (gate_contention_load(gate) != 0) {
        return authorize_latch(gate,
            MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE,
            MT6897_UFS_GATE_STATE_FAULT, MT6897_UFS_GATE_FAULT,
            MT6897_UFS_BLOCK_BAD_STATE, blockers_out);
    }
    verdict = verifier(verifier_context, &request, &candidate);

    state = gate_state_load(gate);
    if (state ==
            (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED ||
        gate_contention_load(gate) != 0) {
        return authorize_latch(gate,
            MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE,
            MT6897_UFS_GATE_STATE_FAULT, MT6897_UFS_GATE_FAULT,
            MT6897_UFS_BLOCK_BAD_STATE, blockers_out);
    }
    if (gate->cookie != MT6897_UFS_GATE_COOKIE ||
        state != (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE ||
        gate_result_load(gate) != (int32_t)MT6897_UFS_GATE_FAULT ||
        gate_blockers_load(gate) != MT6897_UFS_BLOCK_VERIFIER_FAULT ||
        gate->boot_generation != saved_evidence.boot_generation ||
        gate->evidence_fingerprint != 0 ||
        gate->reserved_state != 0 || !lease_zero(&gate->lease)) {
        state = gate_state_load(gate);
        if (gate->cookie == MT6897_UFS_GATE_COOKIE &&
            (state == (uint32_t)MT6897_UFS_GATE_STATE_DENIED ||
             state == (uint32_t)MT6897_UFS_GATE_STATE_FAULT)) {
            return latched_result(gate, blockers_out);
        }
        gate->cookie = MT6897_UFS_GATE_COOKIE;
        gate->boot_generation = saved_evidence.boot_generation;
        zero_lease(&gate->lease);
        gate->evidence_fingerprint = 0;
        gate->reserved_state = 0;
        return authorize_latch(gate,
            MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_VERIFIER_PROTOCOL,
            blockers_out);
    }
    if (!request_equal(&request, &saved_request) ||
        !evidence_equal(evidence, &saved_evidence)) {
        return authorize_latch(gate,
            MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_VERIFIER_PROTOCOL,
            blockers_out);
    }
    if (verdict == MT6897_UFS_GATE_VERIFY_DENY) {
        return authorize_latch(gate,
            MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE,
            MT6897_UFS_GATE_STATE_DENIED,
            MT6897_UFS_GATE_DENIED, MT6897_UFS_BLOCK_VERIFIER_DENIED,
            blockers_out);
    }
    if (verdict == MT6897_UFS_GATE_VERIFY_FAULT) {
        return authorize_latch(gate,
            MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_VERIFIER_FAULT,
            blockers_out);
    }
    if (verdict != MT6897_UFS_GATE_VERIFY_APPROVE ||
        !lease_valid(&candidate, gate->boot_generation, fingerprint)) {
        return authorize_latch(gate,
            MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE,
            MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT,
            verdict == MT6897_UFS_GATE_VERIFY_APPROVE ?
                MT6897_UFS_BLOCK_BAD_LEASE :
                MT6897_UFS_BLOCK_VERIFIER_PROTOCOL,
            blockers_out);
    }

    expected = (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_ACTIVE;
    if (!gate_state_claim(gate, &expected,
        MT6897_UFS_GATE_STATE_CONTENDED)) {
        if (expected ==
            (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED) {
            return latch(gate, MT6897_UFS_GATE_STATE_FAULT,
                MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_BAD_STATE,
                blockers_out);
        }
        if (expected == (uint32_t)MT6897_UFS_GATE_STATE_DENIED ||
            expected == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
            return latched_result(gate, blockers_out);
        }
        *blockers_out = MT6897_UFS_BLOCK_VERIFIER_PROTOCOL;
        return MT6897_UFS_GATE_FAULT;
    }
#ifdef MT6897_UFS_GATE_TEST_HOOKS
    mt6897_ufs_gate_test_before_lease_publish();
#endif
    if (gate_contention_load(gate) != 0) {
        return latch(gate, MT6897_UFS_GATE_STATE_FAULT,
            MT6897_UFS_GATE_FAULT, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    gate->evidence_fingerprint = fingerprint;
    copy_lease(&gate->lease, &candidate);
    gate_result_store(gate, MT6897_UFS_GATE_LEASED);
    gate_blockers_store(gate, 0);
    gate_state_store(gate, MT6897_UFS_GATE_STATE_LEASED);
    if (gate_contention_load(gate) != 0) {
        return terminal_fault(gate, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    copy_lease(lease_out, &candidate);
    *blockers_out = 0;
    return MT6897_UFS_GATE_LEASED;
}

enum mt6897_ufs_gate_result
mt6897_ufs_gate_lease_check(struct mt6897_ufs_gate *gate,
    const struct mt6897_ufs_gate_lease *lease, uint64_t *blockers_out)
{
    uint32_t state;

    if (gate == 0 || lease == 0 || blockers_out == 0) {
        return MT6897_UFS_GATE_ARGUMENT;
    }
    if (gate->cookie != MT6897_UFS_GATE_COOKIE) {
        *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
        return MT6897_UFS_GATE_FAULT;
    }
    state = gate_state_load(gate);
    if (state == (uint32_t)MT6897_UFS_GATE_STATE_DENIED ||
        state == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
        return latched_result(gate, blockers_out);
    }
    if (state == (uint32_t)MT6897_UFS_GATE_STATE_CONTENDED) {
        *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
        return MT6897_UFS_GATE_FAULT;
    }
    if (state ==
        (uint32_t)MT6897_UFS_GATE_STATE_VERIFIER_CONTENDED) {
        *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
        return MT6897_UFS_GATE_FAULT;
    }
    if (state != (uint32_t)MT6897_UFS_GATE_STATE_LEASED ||
        gate_contention_load(gate) != 0 ||
        gate_result_load(gate) != (int32_t)MT6897_UFS_GATE_LEASED ||
        gate_blockers_load(gate) != 0 || gate->evidence_fingerprint == 0 ||
        !lease_valid(&gate->lease, gate->boot_generation,
            gate->evidence_fingerprint) ||
        !lease_equal(lease, &gate->lease)) {
        return terminal_fault(gate, MT6897_UFS_BLOCK_BAD_LEASE,
            blockers_out);
    }
    state = gate_state_load(gate);
    if (state != (uint32_t)MT6897_UFS_GATE_STATE_LEASED) {
        if (state == (uint32_t)MT6897_UFS_GATE_STATE_DENIED ||
            state == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
            return latched_result(gate, blockers_out);
        }
        return terminal_fault(gate, MT6897_UFS_BLOCK_BAD_STATE,
            blockers_out);
    }
    *blockers_out = 0;
    return MT6897_UFS_GATE_LEASED;
}

enum mt6897_ufs_gate_result
mt6897_ufs_gate_fault(struct mt6897_ufs_gate *gate,
    uint64_t provider_blocker, uint64_t *blockers_out)
{
    uint32_t state;

    if (gate == 0 || blockers_out == 0) {
        return MT6897_UFS_GATE_ARGUMENT;
    }
    if (gate->cookie != MT6897_UFS_GATE_COOKIE) {
        *blockers_out = MT6897_UFS_BLOCK_BAD_STATE;
        return MT6897_UFS_GATE_FAULT;
    }
    state = gate_state_load(gate);
    if (state == (uint32_t)MT6897_UFS_GATE_STATE_DENIED ||
        state == (uint32_t)MT6897_UFS_GATE_STATE_FAULT) {
        return latched_result(gate, blockers_out);
    }
    if (provider_blocker == 0) {
        provider_blocker = MT6897_UFS_BLOCK_PROVIDER_RUNTIME;
    }
    return terminal_fault(gate,
        provider_blocker | MT6897_UFS_BLOCK_PROVIDER_RUNTIME,
        blockers_out);
}

struct mt6897_ufs_gate_evidence
mt6897_ufs_gate_duchamp_known_evidence(uint64_t boot_generation)
{
    static const uint8_t fdt_sha256[32] = {
        0x9c, 0x49, 0x58, 0x9f, 0x70, 0x04, 0x41, 0x27,
        0xbe, 0x89, 0x41, 0xa9, 0xea, 0x55, 0x37, 0x97,
        0x7f, 0x44, 0x0c, 0xcd, 0x5a, 0xc1, 0x5c, 0xfd,
        0x24, 0xe1, 0x20, 0xc8, 0xa1, 0x18, 0x1d, 0x29
    };
    static const uint8_t firmware_sha256[32] = {
        0x71, 0x62, 0x22, 0xa6, 0x32, 0xe4, 0xa0, 0x62,
        0x3a, 0x2e, 0x46, 0x7e, 0x17, 0xf1, 0xd3, 0x6f,
        0x38, 0xa3, 0x7f, 0x79, 0xa1, 0xc0, 0x26, 0x44,
        0x7f, 0xe7, 0x24, 0xe7, 0x5e, 0x90, 0xe0, 0x7e
    };
    static const uint8_t firmware_audit_sha256[32] = {
        0x65, 0xe4, 0xa5, 0xcd, 0xd2, 0x08, 0x5c, 0x2e,
        0x2b, 0xb4, 0x8a, 0xd9, 0x82, 0x91, 0x09, 0xf8,
        0xe3, 0x9b, 0x7a, 0x26, 0x06, 0x69, 0x07, 0x4a,
        0xb5, 0x94, 0x27, 0x41, 0x9b, 0x5d, 0x11, 0x0c
    };
    static const uint8_t runtime_dma_report_sha256[32] = {
        0x71, 0x23, 0x6c, 0x08, 0xc0, 0x35, 0x4f, 0xf0,
        0x73, 0x3d, 0x44, 0xa6, 0x4e, 0x50, 0x5d, 0x11,
        0x7d, 0xfd, 0x45, 0x94, 0xe3, 0x70, 0xbe, 0xdd,
        0x81, 0xfa, 0xd3, 0xec, 0x93, 0xd1, 0xbf, 0x4d
    };
    static const uint8_t prdt_report_sha256[32] = {
        0x1e, 0x4c, 0x73, 0x5d, 0x31, 0x60, 0x04, 0xc8,
        0x3f, 0x9d, 0xb7, 0x15, 0x38, 0x18, 0x63, 0x57,
        0x11, 0x2c, 0x75, 0x67, 0xda, 0xec, 0xd1, 0x2b,
        0xe5, 0x2b, 0xa2, 0x4e, 0x74, 0xea, 0x40, 0x18
    };
    struct mt6897_ufs_gate_evidence evidence;
    uint32_t index;

    zero_evidence(&evidence);
    evidence.version = MT6897_UFS_GATE_EVIDENCE_VERSION;
    evidence.route = (uint32_t)MT6897_UFS_GATE_ROUTE_DIRECT_DMA;
    evidence.boot_generation = boot_generation;
    evidence.known = MT6897_UFS_E_PLATFORM_MATCH |
        MT6897_UFS_E_DIRECT_DMA_SELECTED | MT6897_UFS_E_DIRECT_DMA_APERTURE |
        MT6897_UFS_E_IOMMU_ABSENT | MT6897_UFS_E_NONCOHERENT_DEVICE |
        MT6897_UFS_E_SWIOTLB_POOL_PRESENT;
    evidence.asserted = evidence.known;
    for (index = 0; index < 32; ++index) {
        evidence.fdt_sha256[index] = fdt_sha256[index];
        evidence.firmware_sha256[index] = firmware_sha256[index];
        evidence.firmware_audit_sha256[index] =
            firmware_audit_sha256[index];
        evidence.runtime_dma_report_sha256[index] =
            runtime_dma_report_sha256[index];
        evidence.prdt_report_sha256[index] = prdt_report_sha256[index];
    }
    evidence.ufs_hci_base = MT6897_UFS_DUCHAMP_HCI_BASE;
    evidence.ufs_hci_size = MT6897_UFS_DUCHAMP_HCI_SIZE;
    evidence.ufs_phy_base = MT6897_UFS_DUCHAMP_PHY_BASE;
    evidence.ufs_phy_size = MT6897_UFS_DUCHAMP_PHY_SIZE;
    evidence.firmware_service_id = MT6897_UFS_DUCHAMP_SIP_UFS64;
    evidence.firmware_refclk_selector = 8;
    evidence.firmware_mtcmos_selector = 512;
    evidence.firmware_mcq_selector = 1024;
    evidence.dma_cpu_start = 0;
    evidence.dma_device_start = 0;
    evidence.dma_size = MT6897_UFS_DUCHAMP_DMA_SIZE;
    evidence.dma_limit = MT6897_UFS_DUCHAMP_DMA_LIMIT;
    evidence.dma_address_bits = MT6897_UFS_DUCHAMP_DMA_BITS;
    evidence.cache_line_size = 64;
    return evidence;
}
