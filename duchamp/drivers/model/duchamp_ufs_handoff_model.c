#ifndef DUCHAMP_UFS_HANDOFF_MODEL_TEST
#error "Duchamp UFS handoff model is restricted to offline tests"
#endif

#include "duchamp_ufs_handoff_model.h"

static uint32_t
le32(const uint8_t *b)
{
    return (uint32_t)b[0] | (uint32_t)b[1] << 8 |
        (uint32_t)b[2] << 16 | (uint32_t)b[3] << 24;
}

static uint64_t
le64(const uint8_t *b)
{
    return le32(b) | (uint64_t)le32(b + 4) << 32;
}

static int
equal(const uint8_t *a, const uint8_t *b, size_t size)
{
    uint8_t diff = 0;
    for (size_t i = 0; i < size; ++i) diff |= a[i] ^ b[i];
    return !diff;
}

static int
nonzero(const uint8_t *b, size_t size)
{
    uint8_t seen = 0;
    for (size_t i = 0; i < size; ++i) seen |= b[i];
    return seen != 0;
}

enum uhf_result
uhf_parse(const void *wire, size_t size, struct uhf_record *record)
{
    static const uint8_t magic[] = { 'D', 'U', 'C', 'H', 'U', 'F', 'S', '1' };
    const uint8_t *b = wire;
    if (!b || !record)
        return UHF_ARGUMENT;
    if (size != UHF_BYTES || !equal(b, magic, sizeof(magic)) ||
        le32(b + 8) != UHF_VERSION || le32(b + 12) != UHF_BYTES)
        return UHF_FORMAT;
    struct uhf_record out = {
        .board = le32(b + 16), .slot = le32(b + 20),
        .stage = le32(b + 24), .route = le32(b + 28),
        .ownership = le32(b + 32), .prerequisites = le32(b + 36),
        .dma = le32(b + 40), .queue_mode = le32(b + 44),
        .queue_count = le32(b + 48), .busy_queues = le32(b + 52),
        .outstanding_dma = le32(b + 56), .stream_id = le32(b + 60),
        .boot_id = le64(b + 64), .sequence = le64(b + 72),
        .issued_ms = le64(b + 80), .expires_ms = le64(b + 88),
        .hci_base = le64(b + 96), .hci_bytes = le64(b + 104),
        .lease_id = le64(b + 112), .evidence_fingerprint = le64(b + 120),
        .provider_epoch = le64(b + 128), .authority_id = le64(b + 136),
        .controller_owner = le64(b + 144), .phy_owner = le64(b + 152),
        .firmware_owner = le64(b + 160), .dma_owner = le64(b + 168),
        .cache_owner = le64(b + 176), .clock_owner = le64(b + 184),
        .power_owner = le64(b + 192), .reset_owner = le64(b + 200),
        .irq_owner = le64(b + 208), .isolation_epoch = le64(b + 216),
        .iommu_domain = le64(b + 224), .queue_snapshot_id = le64(b + 232),
        .fabric_fence_id = le64(b + 240), .descriptor_pool_id = le64(b + 248),
        .cache_receipt_id = le64(b + 256), .isolation_receipt_id = le64(b + 264),
        .protected_pa = le64(b + 272), .protected_bytes = le64(b + 280),
    };
    for (size_t i = 0; i < UHF_DIGEST_BYTES; ++i) {
        out.kernel_digest[i] = b[288 + i];
        out.firmware_digest[i] = b[320 + i];
        out.fdt_digest[i] = b[352 + i];
    }
    *record = out;
    return UHF_OK;
}

static int
valid_dma(const struct uhf_record *r)
{
    if (r->busy_queues || r->outstanding_dma || !r->queue_snapshot_id ||
        !r->fabric_fence_id || !r->descriptor_pool_id || !r->cache_receipt_id ||
        !r->isolation_receipt_id || !r->isolation_epoch || !r->protected_bytes ||
        r->protected_bytes > UINT64_MAX - r->protected_pa)
        return 0;
    if (!((r->queue_mode == UHF_LEGACY && r->queue_count == 1) ||
        (r->queue_mode == UHF_MCQ && r->queue_count && r->queue_count <= 8)))
        return 0;
    if (r->route == MT6897_UFS_GATE_ROUTE_DIRECT_DMA)
        return r->dma == UHF_DMA_DIRECT_REQUIRED && !r->stream_id && !r->iommu_domain;
    if (r->route == MT6897_UFS_GATE_ROUTE_IOMMU)
        return r->dma == UHF_DMA_IOMMU_REQUIRED && r->iommu_domain &&
            r->stream_id != UINT32_MAX;
    return 0;
}

static enum uhf_result
check_scope(const struct uhf_record *r, const struct uhf_current *c, uint64_t last_now)
{
    if (c->slot != UHF_SLOT_B || c->boot_id != r->boot_id ||
        !equal(c->kernel_digest, r->kernel_digest, UHF_DIGEST_BYTES) ||
        !equal(c->firmware_digest, r->firmware_digest, UHF_DIGEST_BYTES) ||
        !equal(c->fdt_digest, r->fdt_digest, UHF_DIGEST_BYTES))
        return UHF_IDENTITY;
    if (!c->max_age_ms || c->sequence != r->sequence || c->now_ms < last_now ||
        c->now_ms < r->issued_ms || c->now_ms >= r->expires_ms ||
        r->expires_ms - r->issued_ms > c->max_age_ms)
        return UHF_FRESHNESS;
    if (c->authority_id != r->authority_id)
        return UHF_PROVENANCE;
    if (c->route != r->route || c->isolation_epoch != r->isolation_epoch ||
        c->stream_id != r->stream_id || c->iommu_domain != r->iommu_domain ||
        c->protected_pa != r->protected_pa || c->protected_bytes != r->protected_bytes)
        return UHF_DMA_UNSAFE;
    return UHF_OK;
}

static enum uhf_result
validate(struct uhf_session *s)
{
    struct uhf_record r;
    enum uhf_result status = uhf_parse(s->wire, sizeof(s->wire), &r);
    if (status)
        return status;
    if (r.board != UHF_BOARD_DUCHAMP_MT6897 || r.slot != UHF_SLOT_B ||
        r.stage != UHF_STAGE_FINAL_BL31 || !r.boot_id ||
        r.hci_base != MT6897_UFS_DUCHAMP_HCI_BASE || r.hci_bytes != MT6897_UFS_DUCHAMP_HCI_SIZE ||
        !nonzero(r.kernel_digest, UHF_DIGEST_BYTES) || !nonzero(r.firmware_digest, UHF_DIGEST_BYTES) ||
        !nonzero(r.fdt_digest, UHF_DIGEST_BYTES))
        return UHF_IDENTITY;
    if (!r.sequence || r.expires_ms <= r.issued_ms)
        return UHF_FRESHNESS;
    const struct mt6897_ufs_gate_lease *l = &s->lease;
    if (r.ownership != UHF_OWN_REQUIRED || r.prerequisites != UHF_PREREQ_REQUIRED ||
        !r.clock_owner || !r.power_owner || !r.reset_owner || !r.irq_owner)
        return UHF_RESOURCE;
    if (!valid_dma(&r))
        return UHF_DMA_UNSAFE;
    if (!r.lease_id || !r.evidence_fingerprint || !r.provider_epoch ||
        r.lease_id != l->lease_id || r.evidence_fingerprint != l->evidence_fingerprint ||
        r.boot_id != l->boot_generation || r.provider_epoch != l->provider_epoch ||
        r.controller_owner != l->controller_owner_id || r.phy_owner != l->phy_owner_id ||
        r.firmware_owner != l->firmware_owner_id || r.dma_owner != l->dma_owner_id ||
        r.cache_owner != l->cache_owner_id)
        return UHF_LEASE;
    if (!r.authority_id || !nonzero(s->wire + UHF_SIGNED_BYTES, UHF_BYTES - UHF_SIGNED_BYTES))
        return UHF_PROVENANCE;

    uint64_t blockers;
    if (mt6897_ufs_gate_lease_check(s->gate, l, &blockers) != MT6897_UFS_GATE_LEASED)
        return UHF_LEASE;
    if (s->ops.verify_provenance(s->ops.context, s->wire, sizeof(s->wire)) != 1)
        return UHF_PROVENANCE;

    struct uhf_current current = {0};
    if (s->ops.sample_current(s->ops.context, &current) != 1)
        return UHF_FRESHNESS;
    status = check_scope(&r, &current, s->last_now);
    if (status)
        return status;
    if (mt6897_ufs_gate_lease_check(s->gate, l, &blockers) != MT6897_UFS_GATE_LEASED)
        return UHF_LEASE;
    s->last_now = current.now_ms;
    return UHF_OK;
}

static enum uhf_result
enter(struct uhf_session *s, uint32_t from)
{
    if (!s)
        return UHF_ARGUMENT;
    if (__atomic_compare_exchange_n(&s->state, &from, UHF_CHECKING, 0,
        __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE))
        return UHF_OK;
    return from == UHF_FAULTED ? UHF_REVOKED : UHF_STATE;
}

static enum uhf_result
finish(struct uhf_session *s, enum uhf_result result, uint32_t to)
{
    uint32_t checking = UHF_CHECKING;
    if (!__atomic_compare_exchange_n(&s->state, &checking, result ? UHF_FAULTED : to, 0,
        __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE))
        return UHF_REVOKED;
    return result;
}

enum uhf_result
uhf_accept(struct uhf_session *s, const void *wire, size_t size,
    struct mt6897_ufs_gate *gate, const struct mt6897_ufs_gate_lease *lease,
    const struct uhf_ops *ops)
{
    if (!gate || !lease || !ops || !ops->verify_provenance || !ops->sample_current || !wire)
        return UHF_ARGUMENT;
    enum uhf_result result = enter(s, UHF_NEW);
    if (result)
        return result;
    if (size != UHF_BYTES)
        return finish(s, UHF_FORMAT, UHF_VALIDATED);
    s->gate = gate;
    s->lease = *lease;
    s->ops = *ops;
    const uint8_t *b = wire;
    for (size_t i = 0; i < size; ++i) s->wire[i] = b[i];
    return finish(s, validate(s), UHF_VALIDATED);
}

enum uhf_result
uhf_claim(struct uhf_session *s)
{
    enum uhf_result result = enter(s, UHF_VALIDATED);
    return result ? result : finish(s, validate(s), UHF_CLAIMED);
}

enum uhf_result
uhf_check(struct uhf_session *s)
{
    enum uhf_result result = enter(s, UHF_CLAIMED);
    return result ? result : finish(s, validate(s), UHF_CLAIMED);
}

void
uhf_revoke(struct uhf_session *s)
{
    if (s) __atomic_store_n(&s->state, UHF_FAULTED, __ATOMIC_RELEASE);
}
