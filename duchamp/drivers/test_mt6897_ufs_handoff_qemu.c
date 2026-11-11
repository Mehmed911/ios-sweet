/* Standalone QEMU test. The BL31 and XNU records are synthetic. */
#if !defined(MT6897_MODEL_FREESTANDING) || !defined(DUCHAMP_QEMU_UFS_HANDOFF_TEST)
#error "Build only through the standalone QEMU handoff test runner"
#endif

#include "mt6897_ufs_probe.h"

extern void model_assert_fail(const char *, unsigned);
extern int printf(const char *, ...);
extern void *memcpy(void *, const void *, size_t);
extern int memcmp(const void *, const void *, size_t);

#define CHECK(expr) do { \
    if (!(expr)) model_assert_fail(#expr, __LINE__); \
} while (0)

#define BOOT_ID UINT64_C(0x202611110002)
#define IMAGE_ID UINT64_C(0x584e555f4d4f444c)
#define BLOCK_SIZE MT6897_UFS_PROBE_BYTES
#define QEMU_PCI UINT64_C(0x3f020000)
#define QEMU_BAR UINT64_C(0x10000000)
#define DMA_POOL_SIZE 0x60000u

enum queue_mode { LEGACY = 1, MCQ };
enum proof {
    FINAL_EXIT = 1u << 0,
    HCE_OBSERVED = 1u << 1,
    QUEUES_OBSERVED = 1u << 2,
    RESOURCES_GRANTED = 1u << 3,
    DMA_GRANTED = 1u << 4,
    CACHE_GRANTED = 1u << 5
};
enum refusal { ALLOWED, BOOT_MISMATCH, QUEUES, DMA, CACHE, PROVENANCE, REVOKED };

struct queue_sample {
    uint32_t sq_head, sq_tail, cq_head, cq_tail;
};

struct firmware_record {
    uint64_t boot_id, image_id;
    uint32_t proof, mode, hce, outstanding;
    uint32_t transfer_doorbell, task_doorbell, transfer_run, task_run;
    uint32_t mcq_count, mcq_observed;
    struct queue_sample mcq[8];
    uint64_t dma_owner, cache_owner;
};

struct xnu_entry_record {
    uint64_t boot_id, image_id;
};

struct verification {
    const struct firmware_record *firmware;
    const struct xnu_entry_record *entry;
    enum refusal refusal;
    unsigned calls;
};

struct transport {
    unsigned dispatch, pci, mmio, dma, reads;
    uint8_t destination[BLOCK_SIZE];
};

static struct dufs_host controller;
static _Alignas(4096) uint8_t dma_pool[DMA_POOL_SIZE];

static enum refusal
verify_records(const struct verification *input, uint64_t current_boot)
{
    const struct firmware_record *fw = input->firmware;
    const struct xnu_entry_record *entry = input->entry;

    if (!fw || !entry || !fw->boot_id || fw->boot_id != entry->boot_id ||
        entry->boot_id != current_boot)
        return BOOT_MISMATCH;
    if (fw->image_id != entry->image_id || entry->image_id != IMAGE_ID ||
        !(fw->proof & FINAL_EXIT) || !(fw->proof & RESOURCES_GRANTED))
        return PROVENANCE;
    if (!(fw->proof & HCE_OBSERVED) || fw->hce ||
        !(fw->proof & QUEUES_OBSERVED) || fw->outstanding ||
        fw->task_doorbell || fw->task_run)
        return QUEUES;

    if (fw->mode == LEGACY) {
        if (fw->transfer_doorbell || fw->transfer_run ||
            fw->mcq_count || fw->mcq_observed)
            return QUEUES;
    } else if (fw->mode == MCQ) {
        if (!fw->mcq_count || fw->mcq_count > sizeof(fw->mcq) / sizeof(fw->mcq[0]) ||
            fw->mcq_observed != (1u << fw->mcq_count) - 1u)
            return QUEUES;
        for (uint32_t i = 0; i < fw->mcq_count; ++i) {
            const struct queue_sample *q = &fw->mcq[i];
            if (q->sq_head != q->sq_tail || q->cq_head != q->cq_tail)
                return QUEUES;
        }
    } else {
        return QUEUES;
    }
    if (!(fw->proof & DMA_GRANTED) || !fw->dma_owner)
        return DMA;
    if (!(fw->proof & CACHE_GRANTED) || !fw->cache_owner)
        return CACHE;
    return ALLOWED;
}

static enum mt6897_ufs_gate_verdict
model_verify(void *context, const struct mt6897_ufs_gate_verifier_request *request,
    struct mt6897_ufs_gate_lease *lease)
{
    struct verification *input = context;

    ++input->calls;
    input->refusal = verify_records(input, request->evidence.boot_generation);
    if (input->refusal != ALLOWED)
        return MT6897_UFS_GATE_VERIFY_DENY;

    *lease = (struct mt6897_ufs_gate_lease) {
        .version = MT6897_UFS_GATE_LEASE_VERSION,
        .flags = MT6897_UFS_LEASE_REQUIRED_FLAGS,
        .boot_generation = request->evidence.boot_generation,
        .evidence_fingerprint = request->evidence_fingerprint,
        .lease_id = 1,
        .provider_epoch = 1,
        .controller_owner_id = 2,
        .phy_owner_id = 3,
        .firmware_owner_id = 4,
        .dma_owner_id = input->firmware->dma_owner,
        .cache_owner_id = input->firmware->cache_owner
    };
    return MT6897_UFS_GATE_VERIFY_APPROVE;
}

static uint32_t
qemu_read32(void *context, uint32_t offset)
{
    ++((struct transport *)context)->mmio;
    return *(volatile uint32_t *)(QEMU_BAR + offset);
}

static void
qemu_write32(void *context, uint32_t offset, uint32_t value)
{
    ++((struct transport *)context)->mmio;
    *(volatile uint32_t *)(QEMU_BAR + offset) = value;
}

static int
dma_in_pool(uint64_t address, size_t bytes)
{
    uint64_t begin = (uintptr_t)dma_pool;
    return address >= begin && bytes <= sizeof(dma_pool) &&
        address - begin <= sizeof(dma_pool) - bytes;
}

static int
qemu_dma_write(void *context, uint64_t address, const void *source, size_t bytes)
{
    ++((struct transport *)context)->dma;
    if (!dma_in_pool(address, bytes))
        return -1;
    memcpy((void *)(uintptr_t)address, source, bytes);
    return 0;
}

static int
qemu_dma_read(void *context, uint64_t address, void *destination, size_t bytes)
{
    ++((struct transport *)context)->dma;
    if (!dma_in_pool(address, bytes))
        return -1;
    memcpy(destination, (const void *)(uintptr_t)address, bytes);
    return 0;
}

static void
qemu_barrier(void *context)
{
    (void)context;
    __asm__ volatile("dsb sy; isb" ::: "memory");
}

static uint64_t
qemu_milliseconds(void *context)
{
    (void)context;
    uint64_t counter, frequency;
    __asm__ volatile("mrs %0, cntpct_el0; mrs %1, cntfrq_el0"
        : "=r"(counter), "=r"(frequency));
    return counter / (frequency / 1000);
}

static int
qemu_prepare(void *context, struct dufs_config *config)
{
    struct transport *io = context;
    ++io->dispatch;

    volatile uint32_t *pci = (void *)QEMU_PCI;
    ++io->pci;
    CHECK(pci[0] == UINT32_C(0x00131b36) && pci[2] >> 16 == 0x0109);
    CHECK((pci[1] & 7) == 0);
    uint32_t bar_type = pci[4] & 15;
    CHECK(bar_type == 0 || bar_type == 4);
    pci[4] = (uint32_t)QEMU_BAR;
    if (bar_type == 4)
        pci[5] = 0;
    *(volatile uint16_t *)(QEMU_PCI + 4) = 6;
    qemu_barrier(NULL);
    CHECK((pci[4] & ~15u) == QEMU_BAR);

    uint64_t pa = (uintptr_t)dma_pool;
    *config = (struct dufs_config) {
        .io = { io, qemu_read32, qemu_write32, qemu_dma_write, qemu_dma_read,
            qemu_barrier, qemu_milliseconds },
        .dma_begin = pa, .dma_end = pa + sizeof(dma_pool),
        .list_dma = pa, .command_dma = pa + 0x1000, .data_dma = pa + 0x10000,
        .timeout_ms = 3000, .poll_limit = DUFS_MAX_POLLS,
        .exclusive_platform_ready = 1,
        .descriptor_address_bits = 64, .data_address_bits = 64
    };
    return 0;
}

static void
run_case(unsigned id, const struct firmware_record *fw,
    const struct xnu_entry_record *entry, enum refusal expected)
{
    struct mt6897_ufs_gate gate = { 0 };
    struct mt6897_ufs_gate_lease lease = { 0 };
    struct mt6897_ufs_probe probe = { 0 };
    struct transport io = { 0 };
    struct verification input = { .firmware = fw, .entry = entry };
    const struct mt6897_ufs_probe_ops ops = { .context = &io, .prepare = qemu_prepare };
    struct mt6897_ufs_gate_evidence evidence = mt6897_ufs_gate_duchamp_known_evidence(BOOT_ID);
    uint64_t blockers = 0, bytes = 0;

    /* These inputs make the existing policy reach the synthetic verifier. */
    evidence.asserted |= MT6897_UFS_E_COMMON_REQUIRED |
        MT6897_UFS_E_DIRECT_BASE_REQUIRED | MT6897_UFS_E_BOUNCE_NOT_REQUIRED;
    evidence.known = evidence.asserted;

    CHECK(mt6897_ufs_gate_init(&gate, BOOT_ID) == MT6897_UFS_GATE_INIT_OK);
    enum mt6897_ufs_gate_result verdict = mt6897_ufs_gate_authorize(
        &gate, &evidence, model_verify, &input, &lease, &blockers);
    CHECK(input.calls == 1 && input.refusal == (expected == REVOKED ? ALLOWED : expected));
    for (unsigned i = 0; i < BLOCK_SIZE; ++i)
        io.destination[i] = 0xa5;
    if (expected == ALLOWED || expected == REVOKED) {
        CHECK(verdict == MT6897_UFS_GATE_LEASED && blockers == 0);
        CHECK(mt6897_ufs_probe_bind(&probe, &gate, &lease, &controller, &ops, &blockers) ==
            MT6897_UFS_PROVIDER_OK);
    } else {
        CHECK(verdict == MT6897_UFS_GATE_DENIED);
        CHECK(blockers == MT6897_UFS_BLOCK_VERIFIER_DENIED && !lease.lease_id);
        CHECK(mt6897_ufs_probe_bind(&probe, &gate, &lease, &controller, &ops, &blockers) ==
            MT6897_UFS_PROVIDER_LEASE);
        const uint64_t args[4] = { 0 };
        uint64_t result;
        for (unsigned op = 0; op < MT6897_UFS_PROVIDER_OPERATION_COUNT; ++op) {
            CHECK(mt6897_ufs_provider_call(&probe.provider, op, args, &result, &blockers) ==
                MT6897_UFS_PROVIDER_FAULTED);
        }
    }
    if (expected == REVOKED) {
        CHECK(mt6897_ufs_gate_fault(&gate, MT6897_UFS_BLOCK_PROVIDER_RUNTIME, &blockers) ==
            MT6897_UFS_GATE_FAULT);
        CHECK(blockers == MT6897_UFS_BLOCK_PROVIDER_RUNTIME);
    }
    CHECK(mt6897_ufs_probe_read(&probe, io.destination, BLOCK_SIZE - 1, &blockers) ==
        MT6897_UFS_PROVIDER_ARGUMENT);
    enum mt6897_ufs_provider_result read = mt6897_ufs_probe_read(
        &probe, io.destination, sizeof(io.destination), &blockers);
    if (expected == ALLOWED) {
        CHECK(read == MT6897_UFS_PROVIDER_OK && io.dispatch == 1);
        ++io.reads;
        bytes = BLOCK_SIZE;
        for (unsigned i = 0; i < BLOCK_SIZE; ++i)
            CHECK(io.destination[i] == (uint8_t)(i * 17u + 3u));
    } else {
        CHECK(read == (expected == REVOKED ? MT6897_UFS_PROVIDER_LEASE :
            MT6897_UFS_PROVIDER_FAULTED));
        CHECK(bytes == 0 && probe.provider.dispatches == 0 && io.dispatch == 0);
        CHECK(io.pci == 0 && io.mmio == 0 && io.dma == 0 && io.reads == 0);
        for (unsigned i = 0; i < BLOCK_SIZE; ++i)
            CHECK(io.destination[i] == 0xa5);
    }
    CHECK(mt6897_ufs_probe_read(&probe, io.destination, BLOCK_SIZE, &blockers) ==
        MT6897_UFS_PROVIDER_STATE);
    printf("UFS HANDOFF case=%u refusal=%u dispatch=%u pci=%u mmio=%u dma=%u reads=%u bytes=%u\n",
        id, (unsigned)expected, io.dispatch, io.pci, io.mmio, io.dma, io.reads, (unsigned)bytes);
}

int
main(void)
{
    const struct xnu_entry_record entry = { BOOT_ID, IMAGE_ID };
    const struct xnu_entry_record stale_entry = { BOOT_ID - 1, IMAGE_ID };
    const struct firmware_record ready = {
        .boot_id = BOOT_ID, .image_id = IMAGE_ID,
        .proof = FINAL_EXIT | HCE_OBSERVED | QUEUES_OBSERVED |
            RESOURCES_GRANTED | DMA_GRANTED | CACHE_GRANTED,
        .mode = LEGACY, .dma_owner = 5, .cache_owner = 6
    };
    struct firmware_record fw = ready;
    run_case(1, NULL, &entry, BOOT_MISMATCH);
    run_case(2, &ready, NULL, BOOT_MISMATCH);
    run_case(3, &ready, &stale_entry, BOOT_MISMATCH);
    fw.boot_id = stale_entry.boot_id;
    run_case(4, &fw, &stale_entry, BOOT_MISMATCH);
    fw = ready;
    fw.image_id ^= 1;
    run_case(5, &fw, &entry, PROVENANCE);
    fw = ready;
    fw.proof &= ~FINAL_EXIT;
    run_case(6, &fw, &entry, PROVENANCE);
    fw = ready;
    fw.proof &= ~HCE_OBSERVED;
    run_case(7, &fw, &entry, QUEUES);
    fw = ready;
    fw.hce = 1;
    run_case(8, &fw, &entry, QUEUES);
    fw = ready;
    fw.proof &= ~QUEUES_OBSERVED;
    run_case(9, &fw, &entry, QUEUES);
    fw = ready;
    fw.transfer_doorbell = 1;
    run_case(10, &fw, &entry, QUEUES);
    fw = ready;
    fw.task_doorbell = 1;
    run_case(11, &fw, &entry, QUEUES);
    fw = ready;
    fw.mode = MCQ;
    fw.mcq_count = 2;
    fw.mcq_observed = 1;
    run_case(12, &fw, &entry, QUEUES);
    fw.mcq_observed = 3;
    fw.mcq[1].cq_tail = 1;
    run_case(13, &fw, &entry, QUEUES);
    fw.mcq[1].cq_tail = 0;
    fw.outstanding = 1;
    run_case(14, &fw, &entry, QUEUES);
    fw.outstanding = 0;
    const struct verification mcq = { .firmware = &fw, .entry = &entry };
    CHECK(verify_records(&mcq, BOOT_ID) == ALLOWED);
    fw = ready;
    fw.proof &= ~DMA_GRANTED;
    run_case(15, &fw, &entry, DMA);
    fw = ready;
    fw.proof &= ~CACHE_GRANTED;
    run_case(16, &fw, &entry, CACHE);
    fw = ready;
    fw.dma_owner = 0;
    run_case(17, &fw, &entry, DMA);
    fw = ready;
    fw.cache_owner = 0;
    run_case(18, &fw, &entry, CACHE);
    fw = ready;
    fw.proof &= ~RESOURCES_GRANTED;
    run_case(19, &fw, &entry, PROVENANCE);
    run_case(20, &ready, &entry, REVOKED);
    run_case(21, &ready, &entry, ALLOWED);
    return 0;
}
