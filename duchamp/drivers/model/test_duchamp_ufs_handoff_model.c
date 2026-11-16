#include "duchamp_ufs_handoff_model.h"

#ifdef MT6897_MODEL_FREESTANDING
extern void model_assert_fail(const char *, unsigned);
extern void *memset(void *, int, size_t);
extern int memcmp(const void *, const void *, size_t);
extern int printf(const char *, ...);
#define CHECK(expr) do { if (!(expr)) model_assert_fail(#expr, __LINE__); } while (0)
#else
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define CHECK(expr) assert(expr)
#endif

#define BOOT UINT64_C(0x202611150002)
#define PA UINT64_C(0x80000000)
#define PA_BYTES UINT64_C(0x2000000)

struct fixture {
    struct uhf_session session;
    struct mt6897_ufs_gate gate;
    struct mt6897_ufs_gate_lease lease;
    struct mt6897_ufs_gate_evidence gate_evidence;
    struct uhf_current current;
    struct uhf_ops ops;
    uint8_t input[UHF_BYTES + 2], trusted[UHF_BYTES];
    unsigned auth_calls, sample_calls, deny, revoke_auth, revoke_gate, reenter, mutate_input;
    int auth_result, sample_result;
};
static unsigned cases;

static uint8_t *
wire(struct fixture *f)
{
    return f->input + 1; /* Intentionally unaligned. */
}

static void
put(struct fixture *f, unsigned offset, unsigned bytes, uint64_t value)
{
    for (unsigned i = 0; i < bytes; ++i)
        wire(f)[offset + i] = (uint8_t)(value >> (i * 8));
}

static void
approve_packet(struct fixture *f)
{
    for (unsigned i = 0; i < UHF_BYTES; ++i) f->trusted[i] = wire(f)[i];
}

static enum mt6897_ufs_gate_verdict
approve(void *context, const struct mt6897_ufs_gate_verifier_request *r,
    struct mt6897_ufs_gate_lease *l)
{
    (void)context;
    CHECK(r->evidence.boot_generation == BOOT);
    *l = (struct mt6897_ufs_gate_lease){
        .version = MT6897_UFS_GATE_LEASE_VERSION, .flags = MT6897_UFS_LEASE_REQUIRED_FLAGS,
        .boot_generation = BOOT, .evidence_fingerprint = r->evidence_fingerprint,
        .lease_id = 21, .provider_epoch = 22, .controller_owner_id = 23,
        .phy_owner_id = 24, .firmware_owner_id = 25, .dma_owner_id = 26,
        .cache_owner_id = 27
    };
    return MT6897_UFS_GATE_VERIFY_APPROVE;
}

static int
authorize_bytes(void *context, const uint8_t *bytes, size_t size)
{
    struct fixture *f = context;
    f->auth_calls++;
    CHECK(bytes != wire(f) && size == UHF_BYTES);
    if (f->mutate_input) wire(f)[0] ^= 0xff;
    if (f->reenter) CHECK(uhf_claim(&f->session) == UHF_STATE);
    if (f->revoke_auth) uhf_revoke(&f->session);
    if (f->deny || memcmp(bytes, f->trusted, UHF_BYTES)) return 0;
    return f->auth_result; /* Test oracle only, never a physical issuer. */
}

static int
sample(void *context, struct uhf_current *c)
{
    struct fixture *f = context;
    f->sample_calls++;
    if (f->revoke_gate) {
        uint64_t blockers;
        CHECK(mt6897_ufs_gate_fault(&f->gate, MT6897_UFS_BLOCK_PROVIDER_RUNTIME, &blockers) ==
            MT6897_UFS_GATE_FAULT);
    }
    *c = f->current;
    return f->sample_result;
}

static void
reset(struct fixture *f, unsigned route)
{
    memset(f, 0, sizeof(*f));
    const int translated = route == MT6897_UFS_GATE_ROUTE_IOMMU;
    struct mt6897_ufs_gate_evidence e = mt6897_ufs_gate_duchamp_known_evidence(BOOT);
    e.route = route;
    e.asserted = MT6897_UFS_E_COMMON_REQUIRED | MT6897_UFS_E_NONCOHERENT_DEVICE;
    if (translated) {
        e.asserted |= MT6897_UFS_E_IOMMU_REQUIRED;
        e.iommu_stream_id = 0;
        e.iommu_domain_id = 42;
        e.iommu_table_id = 43;
        e.iommu_mapping_epoch = 44;
    } else {
        e.asserted |= MT6897_UFS_E_DIRECT_BASE_REQUIRED | MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    }
    e.known = e.asserted;
    uint64_t blockers;
    CHECK(mt6897_ufs_gate_init(&f->gate, BOOT) == MT6897_UFS_GATE_INIT_OK);
    CHECK(mt6897_ufs_gate_authorize(&f->gate, &e, approve, NULL, &f->lease, &blockers) ==
        MT6897_UFS_GATE_LEASED);
    f->gate_evidence = e;
    f->current = (struct uhf_current){
        .slot = UHF_SLOT_B, .route = route, .boot_id = BOOT,
        .prerequisites = UHF_PREREQ_REQUIRED, .cache_owner = f->lease.cache_owner_id,
        .sequence = 17, .now_ms = 110, .max_age_ms = 30, .authority_id = 91,
        .isolation_epoch = 44, .iommu_domain = e.iommu_domain_id,
        .protected_pa = PA, .protected_bytes = PA_BYTES
    };
    for (unsigned i = 0; i < UHF_DIGEST_BYTES; ++i) {
        f->current.kernel_digest[i] = wire(f)[288 + i] = (uint8_t)(i + 1);
        f->current.firmware_digest[i] = wire(f)[320 + i] = e.firmware_sha256[i];
        f->current.fdt_digest[i] = wire(f)[352 + i] = e.fdt_sha256[i];
    }
    for (unsigned i = 0; i < 8; ++i) wire(f)[i] = (uint8_t)"DUCHUFS1"[i];
    put(f, 8, 4, UHF_VERSION); put(f, 12, 4, UHF_BYTES);
    put(f, 16, 4, UHF_BOARD_DUCHAMP_MT6897); put(f, 20, 4, UHF_SLOT_B);
    put(f, 24, 4, UHF_STAGE_FINAL_BL31); put(f, 28, 4, route);
    put(f, 32, 4, UHF_OWN_REQUIRED); put(f, 36, 4, UHF_PREREQ_REQUIRED);
    put(f, 40, 4, translated ? UHF_DMA_IOMMU_REQUIRED : UHF_DMA_DIRECT_REQUIRED);
    put(f, 44, 4, translated ? UHF_MCQ : UHF_LEGACY);
    put(f, 48, 4, translated ? 8 : 1);
    put(f, 64, 8, BOOT); put(f, 72, 8, f->current.sequence);
    put(f, 80, 8, 100); put(f, 88, 8, 120);
    put(f, 96, 8, MT6897_UFS_DUCHAMP_HCI_BASE); put(f, 104, 8, MT6897_UFS_DUCHAMP_HCI_SIZE);
    put(f, 112, 8, f->lease.lease_id); put(f, 120, 8, f->lease.evidence_fingerprint);
    put(f, 128, 8, f->lease.provider_epoch); put(f, 136, 8, f->current.authority_id);
    put(f, 144, 8, f->lease.controller_owner_id); put(f, 152, 8, f->lease.phy_owner_id);
    put(f, 160, 8, f->lease.firmware_owner_id); put(f, 168, 8, f->lease.dma_owner_id);
    put(f, 176, 8, f->lease.cache_owner_id);
    for (unsigned offset = 184; offset <= 208; offset += 8) put(f, offset, 8, offset);
    put(f, 216, 8, f->current.isolation_epoch); put(f, 224, 8, e.iommu_domain_id);
    for (unsigned offset = 232; offset <= 264; offset += 8) put(f, offset, 8, offset);
    put(f, 272, 8, PA); put(f, 280, 8, PA_BYTES);
    for (unsigned i = UHF_SIGNED_BYTES; i < UHF_BYTES; ++i) wire(f)[i] = (uint8_t)(i + 1);
    approve_packet(f);
    f->auth_result = f->sample_result = 1;
    f->ops = (struct uhf_ops){ f, authorize_bytes, sample };
}

static enum uhf_result
accept(struct fixture *f, size_t bytes)
{
    return uhf_accept(&f->session, wire(f), bytes, &f->gate, &f->lease,
        &f->gate_evidence, &f->ops);
}

static void
record_case(enum uhf_result status)
{
    printf("UFS HANDOFF FORMAT case=%u status=%u\n", ++cases, (unsigned)status);
}

static void
terminal(struct fixture *f)
{
    unsigned auths = f->auth_calls, samples = f->sample_calls;
    CHECK(f->session.state == UHF_FAULTED);
    CHECK(accept(f, UHF_BYTES) == UHF_REVOKED);
    CHECK(uhf_claim(&f->session) == UHF_REVOKED);
    CHECK(uhf_check(&f->session) == UHF_REVOKED);
    CHECK(f->auth_calls == auths && f->sample_calls == samples);
}

static void
deny(struct fixture *f, size_t size, enum uhf_result expected, unsigned auth, unsigned samples)
{
    CHECK(accept(f, size) == expected);
    CHECK(f->auth_calls == auth && f->sample_calls == samples);
    terminal(f);
    record_case(expected);
}

int
main(void)
{
    struct fixture f;
    struct uhf_record parsed, before;
    const unsigned direct = MT6897_UFS_GATE_ROUTE_DIRECT_DMA;
    const unsigned iommu = MT6897_UFS_GATE_ROUTE_IOMMU;
    reset(&f, direct);
    memset(&parsed, 0xa5, sizeof(parsed));
    before = parsed;
    for (unsigned i = 0; i < UHF_BYTES; ++i) {
        CHECK(uhf_parse(wire(&f), i, &parsed) == UHF_FORMAT);
        CHECK(!memcmp(&parsed, &before, sizeof(parsed)));
    }
    CHECK(uhf_parse(wire(&f), UHF_BYTES + 1, &parsed) == UHF_FORMAT);
    CHECK(uhf_parse(wire(&f), UHF_BYTES, &parsed) == UHF_OK);
    CHECK(parsed.boot_id == BOOT && parsed.protected_pa == PA && parsed.protected_bytes == PA_BYTES);
    CHECK(uhf_claim(&f.session) == UHF_STATE && uhf_check(&f.session) == UHF_STATE);
    f.mutate_input = f.reenter = 1;
    CHECK(accept(&f, UHF_BYTES) == UHF_OK);
    CHECK(uhf_check(&f.session) == UHF_STATE);
    f.gate_evidence.route = 0; /* The session owns its evidence copy. */
    CHECK(uhf_claim(&f.session) == UHF_OK && uhf_check(&f.session) == UHF_OK);
    CHECK(uhf_claim(&f.session) == UHF_STATE);
    CHECK(f.auth_calls == 3 && f.sample_calls == 3);
    record_case(UHF_OK);

    reset(&f, iommu);
    CHECK(accept(&f, UHF_BYTES) == UHF_OK && uhf_claim(&f.session) == UHF_OK);
    f.current.now_ms = 119;
    CHECK(uhf_check(&f.session) == UHF_OK);
    f.current.now_ms = 120;
    CHECK(uhf_check(&f.session) == UHF_FRESHNESS);
    terminal(&f);
    record_case(UHF_OK); record_case(UHF_FRESHNESS);

    struct change { unsigned offset, bytes; uint64_t value; enum uhf_result expected; };
    const struct change invalid[] = {
        {0,1,0,UHF_FORMAT}, {8,4,2,UHF_FORMAT}, {12,4,UHF_BYTES-1,UHF_FORMAT},
        {16,4,1,UHF_IDENTITY}, {20,4,1,UHF_IDENTITY}, {24,4,0,UHF_IDENTITY},
        {28,4,0,UHF_DMA_UNSAFE}, {32,4,UHF_OWN_REQUIRED ^ UHF_OWN_DMA,UHF_RESOURCE},
        {36,4,UHF_PREREQ_REQUIRED ^ UHF_BUS_CLOCKS_PINNED,UHF_RESOURCE},
        {36,4,UHF_PREREQ_REQUIRED ^ UHF_DOMAIN_ON,UHF_RESOURCE},
        {36,4,UHF_PREREQ_REQUIRED ^ UHF_PHY_READY,UHF_RESOURCE},
        {36,4,UHF_PREREQ_REQUIRED ^ UHF_RESET_DEASSERTED,UHF_RESOURCE},
        {36,4,UHF_PREREQ_REQUIRED | 0x800u,UHF_RESOURCE},
        {40,4,UHF_DMA_DIRECT_REQUIRED ^ UHF_DRAIN_COMPLETE,UHF_DMA_UNSAFE},
        {40,4,UHF_DMA_DIRECT_REQUIRED ^ UHF_QUEUE_SNAPSHOT_COMPLETE,UHF_DMA_UNSAFE},
        {40,4,UHF_DMA_DIRECT_REQUIRED ^ UHF_DMA_CACHE_SYNCHRONIZED,UHF_DMA_UNSAFE},
        {40,4,UHF_DMA_DIRECT_REQUIRED ^ UHF_DIRECT_FILTER_PROVEN,UHF_DMA_UNSAFE},
        {40,4,UHF_DMA_DIRECT_REQUIRED ^ UHF_OLD_SUBMISSIONS_FENCED,UHF_DMA_UNSAFE},
        {40,4,UHF_DMA_DIRECT_REQUIRED ^ UHF_OLD_DESCRIPTORS_QUARANTINED,UHF_DMA_UNSAFE},
        {40,4,UHF_DMA_DIRECT_REQUIRED ^ UHF_XNU_MEMORY_ISOLATED,UHF_DMA_UNSAFE},
        {44,4,0,UHF_DMA_UNSAFE}, {48,4,2,UHF_DMA_UNSAFE},
        {52,4,1,UHF_DMA_UNSAFE}, {56,4,1,UHF_DMA_UNSAFE}, {60,4,1,UHF_DMA_UNSAFE},
        {64,8,0,UHF_IDENTITY}, {72,8,0,UHF_FRESHNESS}, {88,8,100,UHF_FRESHNESS},
        {96,8,0,UHF_IDENTITY}, {104,8,0x2000,UHF_IDENTITY},
        {112,8,0,UHF_LEASE}, {120,8,0,UHF_LEASE}, {128,8,23,UHF_LEASE},
        {136,8,0,UHF_PROVENANCE}, {144,8,25,UHF_LEASE},
        {176,8,0,UHF_LEASE}, {184,8,0,UHF_RESOURCE},
        {216,8,0,UHF_DMA_UNSAFE}, {224,8,4,UHF_DMA_UNSAFE},
        {232,8,0,UHF_DMA_UNSAFE}, {240,8,0,UHF_DMA_UNSAFE},
        {248,8,0,UHF_DMA_UNSAFE}, {256,8,0,UHF_DMA_UNSAFE},
        {264,8,0,UHF_DMA_UNSAFE}, {272,8,UINT64_MAX,UHF_DMA_UNSAFE},
        {280,8,0,UHF_DMA_UNSAFE}, {184,8,31337,UHF_PROVENANCE}
    };
    for (unsigned i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i) {
        const struct change *m = &invalid[i];
        reset(&f, direct); put(&f, m->offset, m->bytes, m->value);
        deny(&f, UHF_BYTES, m->expected, m->value == 31337, 0);
    }
    reset(&f, direct); deny(&f, UHF_BYTES - 1, UHF_FORMAT, 0, 0);
    reset(&f, direct); deny(&f, UHF_BYTES + 1, UHF_FORMAT, 0, 0);
    reset(&f, direct);
    memset(wire(&f) + UHF_SIGNED_BYTES, 0, UHF_BYTES - UHF_SIGNED_BYTES);
    deny(&f, UHF_BYTES, UHF_PROVENANCE, 0, 0);
    reset(&f, direct); wire(&f)[UHF_BYTES - 1] ^= 1;
    deny(&f, UHF_BYTES, UHF_PROVENANCE, 1, 0);
    reset(&f, direct); f.auth_result = 2; deny(&f, UHF_BYTES, UHF_PROVENANCE, 1, 0);
    reset(&f, direct); f.sample_result = 0; deny(&f, UHF_BYTES, UHF_FRESHNESS, 1, 1);
    reset(&f, direct); f.current.slot = 1; deny(&f, UHF_BYTES, UHF_IDENTITY, 1, 1);
    reset(&f, direct); f.current.boot_id++; deny(&f, UHF_BYTES, UHF_IDENTITY, 1, 1);
    reset(&f, direct); f.current.kernel_digest[31] ^= 1;
    deny(&f, UHF_BYTES, UHF_IDENTITY, 1, 1);
    reset(&f, direct); f.current.firmware_digest[0] ^= 1;
    deny(&f, UHF_BYTES, UHF_IDENTITY, 1, 1);
    reset(&f, direct); f.current.fdt_digest[15] ^= 1;
    deny(&f, UHF_BYTES, UHF_IDENTITY, 1, 1);
    reset(&f, direct); f.current.authority_id++; deny(&f, UHF_BYTES, UHF_PROVENANCE, 1, 1);
    const uint32_t missing_resources[] = {
        UHF_RESET_DEASSERTED, UHF_BUS_CLOCKS_PINNED, UHF_REFCLK_PINNED,
        UHF_DOMAIN_ON, UHF_RAILS_PINNED, UHF_LIFETIME_PINNED
    };
    for (unsigned i = 0; i < sizeof(missing_resources) / sizeof(missing_resources[0]); ++i) {
        reset(&f, direct);
        f.current.prerequisites &= ~missing_resources[i];
        deny(&f, UHF_BYTES, UHF_RESOURCE, 1, 1);
    }
    reset(&f, direct); f.current.cache_owner = 0; deny(&f, UHF_BYTES, UHF_RESOURCE, 1, 1);
    reset(&f, direct); f.current.cache_owner++; deny(&f, UHF_BYTES, UHF_RESOURCE, 1, 1);
    reset(&f, direct);
    CHECK(accept(&f, UHF_BYTES) == UHF_OK && uhf_claim(&f.session) == UHF_OK);
    f.current.prerequisites &= ~UHF_RESET_DEASSERTED;
    CHECK(uhf_check(&f.session) == UHF_RESOURCE);
    terminal(&f); record_case(UHF_RESOURCE);
    reset(&f, direct); f.current.now_ms = 99; deny(&f, UHF_BYTES, UHF_FRESHNESS, 1, 1);
    reset(&f, direct); f.current.sequence++; deny(&f, UHF_BYTES, UHF_FRESHNESS, 1, 1);
    reset(&f, direct); f.current.max_age_ms = 19; deny(&f, UHF_BYTES, UHF_FRESHNESS, 1, 1);
    reset(&f, direct); f.current.protected_bytes--; deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 1, 1);
    reset(&f, direct); f.current.isolation_epoch++; deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 1, 1);
    reset(&f, direct); f.current.route = iommu; deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 1, 1);
    reset(&f, iommu); f.current.stream_id++; deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 1, 1);
    reset(&f, iommu); f.current.iommu_domain++; deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 1, 1);
    reset(&f, iommu); put(&f, 40, 4, UHF_DMA_IOMMU_REQUIRED ^ UHF_IOTLB_INVALIDATED_SYNCED);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);
    reset(&f, iommu); put(&f, 40, 4, UHF_DMA_IOMMU_REQUIRED ^ UHF_DEVICE_TRANSLATIONS_ACCOUNTED);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);
    reset(&f, iommu); put(&f, 40, 4, UHF_DMA_IOMMU_REQUIRED ^ UHF_SMMU_STREAM_BLOCKED);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);
    reset(&f, iommu); put(&f, 60, 4, UINT32_MAX);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);

    /* A matching provenance/current fixture cannot change the gate's scope. */
    reset(&f, direct);
    f.current.route = iommu;
    f.current.iommu_domain = 42;
    put(&f, 28, 4, iommu);
    put(&f, 40, 4, UHF_DMA_IOMMU_REQUIRED);
    put(&f, 224, 8, f.current.iommu_domain);
    approve_packet(&f);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);

    reset(&f, iommu);
    f.current.route = direct;
    f.current.iommu_domain = 0;
    put(&f, 28, 4, direct);
    put(&f, 40, 4, UHF_DMA_DIRECT_REQUIRED);
    put(&f, 224, 8, 0);
    approve_packet(&f);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);

    reset(&f, iommu);
    put(&f, 60, 4, ++f.current.stream_id);
    approve_packet(&f);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);

    reset(&f, iommu);
    put(&f, 224, 8, ++f.current.iommu_domain);
    approve_packet(&f);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);

    reset(&f, iommu);
    put(&f, 216, 8, ++f.current.isolation_epoch);
    approve_packet(&f);
    deny(&f, UHF_BYTES, UHF_DMA_UNSAFE, 0, 0);

    reset(&f, direct);
    f.gate_evidence.boot_generation++;
    deny(&f, UHF_BYTES, UHF_LEASE, 0, 0);

    reset(&f, iommu);
    f.gate_evidence.iommu_table_id++;
    deny(&f, UHF_BYTES, UHF_LEASE, 0, 0);

    reset(&f, direct);
    f.current.firmware_digest[0] ^= 1;
    put(&f, 320, 1, f.current.firmware_digest[0]);
    approve_packet(&f);
    deny(&f, UHF_BYTES, UHF_IDENTITY, 0, 0);

    reset(&f, direct);
    f.current.fdt_digest[0] ^= 1;
    put(&f, 352, 1, f.current.fdt_digest[0]);
    approve_packet(&f);
    deny(&f, UHF_BYTES, UHF_IDENTITY, 0, 0);

    reset(&f, direct);
    CHECK(accept(&f, UHF_BYTES) == UHF_OK);
    f.current.now_ms--;
    CHECK(uhf_claim(&f.session) == UHF_FRESHNESS);
    terminal(&f); record_case(UHF_FRESHNESS);

    reset(&f, direct);
    CHECK(accept(&f, UHF_BYTES) == UHF_OK);
    f.revoke_auth = 1;
    CHECK(uhf_claim(&f.session) == UHF_REVOKED);
    CHECK(f.auth_calls == 2 && f.sample_calls == 1);
    terminal(&f); record_case(UHF_REVOKED);

    reset(&f, direct);
    CHECK(accept(&f, UHF_BYTES) == UHF_OK && uhf_claim(&f.session) == UHF_OK);
    f.deny = 1;
    CHECK(uhf_check(&f.session) == UHF_PROVENANCE);
    terminal(&f); record_case(UHF_PROVENANCE);

    reset(&f, direct);
    CHECK(accept(&f, UHF_BYTES) == UHF_OK && uhf_claim(&f.session) == UHF_OK);
    f.revoke_gate = 1;
    CHECK(uhf_check(&f.session) == UHF_LEASE);
    terminal(&f); record_case(UHF_LEASE);

    reset(&f, direct);
    uhf_revoke(&f.session);
    terminal(&f); record_case(UHF_REVOKED);

    reset(&f, direct);
    f.ops.verify_provenance = NULL;
    CHECK(accept(&f, UHF_BYTES) == UHF_ARGUMENT && f.session.state == UHF_NEW);
    CHECK(!f.auth_calls && !f.sample_calls);
    record_case(UHF_ARGUMENT);

    printf("DUCHAMP UFS HANDOFF FORMAT PASS cases=%u\n", cases);
    return 0;
}
