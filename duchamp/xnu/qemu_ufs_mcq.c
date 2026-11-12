/*
 * QEMU 10.2 UFS transport. Keep the BSD/GPT
 * driver and its checked request/response code, replacing only its queue I/O.
 * The physical MT6897 backend and inherited-queue policy are independent.
 */
#if defined(ARM64_BOARD_CONFIG_SWEET) || defined(DUCHAMP_PINNED_QEMU_MCQ_REPLAY)
#include "ufs_readonly.h"

extern int PE_parse_boot_argn(const char *, void *, int);
extern void sweet_early_mark(unsigned, const char *);
int dufs_mcq_bind(struct dufs_host *, const struct dufs_config *);

enum {
    CAP = 0, MCQCAP = 4, IS = 0x20,
    LIST_LO = 0x50, LIST_HI = 0x54, DB = 0x58, RUN = 0x60,
    CONFIG = 0x300, SQ = 0x400, CQ = 0x420,
    SQ_TAIL = 0x1004, CQ_HEAD = 0x101c, CQ_TAIL = 0x1020, CQ_IS = 0x1024,
    ENTRY_BYTES = 32, RING_BYTES = 4 * ENTRY_BYTES,
    SQ_OFFSET = 0x2000, CQ_OFFSET = 0x3000,
    QUEUE_ENABLE = 1u << 31,
    QUEUE_ATTR = QUEUE_ENABLE | (RING_BYTES / 4 - 1),
    FAULT_DMA_ADDRESS = 1, FAULT_SQ_SYNC = 2, FAULT_QEMU_DMA = 3
};

union mcq_entry {
    uint64_t qword[4];
    uint8_t byte[ENTRY_BYTES];
};

static struct {
    struct dufs_io bus;
    uint64_t base;
    unsigned fault, offset;
    uint8_t ready, pending, complete, poisoned, ocs;
} mcq;

static uint32_t read_reg(uint32_t reg)
{
    return mcq.bus.read32(mcq.bus.context, reg);
}

static void write_reg(uint32_t reg, uint32_t value)
{
    mcq.bus.write32(mcq.bus.context, reg, value);
}

static void set_base(uint32_t reg, unsigned offset)
{
    uint64_t address = mcq.base + offset;
    write_reg(reg, (uint32_t)address);
    write_reg(reg + 4, (uint32_t)(address >> 32));
}

static void start_queues(void)
{
    /* qu_prepare allocates a zeroed, permanent pool. Both rings occupy
     * separate pages between the existing command descriptor and data. */
    if (!(read_reg(CAP) & (1u << 30)) ||
        (read_reg(MCQCAP) & 0xff00ffu) != 0x020007u ||
        read_reg(SQ) || read_reg(CQ) || read_reg(SQ + 12) != 0x1000 ||
        read_reg(CQ + 12) != CQ_HEAD ||
        read_reg(SQ_TAIL) || read_reg(CQ_HEAD) || read_reg(CQ_TAIL))
        return;
    write_reg(CONFIG, 1);
    set_base(CQ + 4, CQ_OFFSET);
    write_reg(CQ, QUEUE_ATTR);
    set_base(SQ + 4, SQ_OFFSET);
    write_reg(SQ, QUEUE_ATTR);
    mcq.ready = (read_reg(CONFIG) & 1) && read_reg(SQ) == QUEUE_ATTR &&
        read_reg(CQ) == QUEUE_ATTR;
}

static void reject(const char *reason)
{
    mcq.poisoned = 1;
    sweet_early_mark(163, reason);
}

static unsigned next_offset(void)
{
    return (mcq.offset + ENTRY_BYTES) % RING_BYTES;
}

static void submit(uint32_t value)
{
    union mcq_entry entry;
    mcq.complete = 0;
    if (mcq.poisoned)
        return;
    if (!mcq.ready || mcq.pending || value != 1 ||
        mcq.bus.dma_read(mcq.bus.context, mcq.base, &entry, sizeof(entry)))
        return reject("DUCHAMP MCQ DMA REJECTED");
    if (mcq.fault == FAULT_DMA_ADDRESS)
        entry.qword[2] = UINT64_C(0x1000000000);
    if (entry.qword[2] != mcq.base + 0x1000)
        return reject("DUCHAMP MCQ DMA REJECTED");
    if (mcq.fault == FAULT_SQ_SYNC)
        return reject("DUCHAMP MCQ CACHE SYNC REQUIRED");
    /* Explicit emulator-only control: force an actual UCD bus fault after
     * validation. QEMU leaves that SQ request outstanding on DMA failure. */
    if (mcq.fault == FAULT_QEMU_DMA)
        entry.qword[2] = UINT64_C(0x1000000000);
    if (mcq.bus.dma_write(mcq.bus.context, mcq.base + SQ_OFFSET + mcq.offset,
        &entry, sizeof(entry)))
        return reject("DUCHAMP MCQ DMA REJECTED");
    mcq.bus.barrier(mcq.bus.context);
    mcq.pending = 1;
    write_reg(SQ_TAIL, next_offset());
}

static uint32_t poll_completion(void)
{
    if (!mcq.pending || mcq.poisoned)
        return 0;
    uint32_t tail = read_reg(CQ_TAIL);
    if (tail == mcq.offset)
        return 1;
    union mcq_entry entry;
    if (tail != next_offset() ||
        mcq.bus.dma_read(mcq.bus.context, mcq.base + CQ_OFFSET + mcq.offset,
            &entry, sizeof(entry)) ||
        entry.qword[0] != mcq.base + 0x1000 || entry.byte[17]) {
        reject("DUCHAMP MCQ COMPLETION REJECTED");
        return 0;
    }
    mcq.ocs = entry.byte[16];
    mcq.offset = tail;
    mcq.pending = 0;
    mcq.complete = 1;
    write_reg(CQ_HEAD, tail);
    write_reg(CQ_IS, 1);
    write_reg(IS, 1u << 20);
    return 0;
}

static uint32_t mcq_read(void *context, uint32_t offset)
{
    (void)context;
    switch (offset) {
    case LIST_LO: return (uint32_t)mcq.base;
    case LIST_HI: return (uint32_t)(mcq.base >> 32);
    case RUN: return mcq.ready;
    case DB: return poll_completion();
    default: return read_reg(offset);
    }
}

static void mcq_write(void *context, uint32_t offset, uint32_t value)
{
    (void)context;
    switch (offset) {
    case LIST_LO:
    case LIST_HI: break;
    case RUN: start_queues(); break;
    case DB: submit(value); break;
    default: write_reg(offset, value); break;
    }
}

static int mcq_dma_read(void *context, uint64_t address, void *buffer, size_t bytes)
{
    if (mcq.poisoned || (address == mcq.base && (!mcq.complete || bytes != ENTRY_BYTES)))
        return -1;
    int result = mcq.bus.dma_read(context, address, buffer, bytes);
    if (!result && address == mcq.base) {
        ((uint8_t *)buffer)[8] = mcq.ocs;
        mcq.complete = 0;
    }
    return result;
}

int dufs_mcq_bind(struct dufs_host *host, const struct dufs_config *config)
{
    int result = dufs_bind(host, config);
    unsigned enabled = 0;
    if (result || !PE_parse_boot_argn("sweet-qemu-ufs-mcq", &enabled, sizeof(enabled)))
        return result;
    uint64_t base = config->dma_begin;
    if (enabled != 1 || mcq.base || base % 0x4000 || config->list_dma != base ||
        config->command_dma != base + 0x1000 || config->data_dma != base + 0x10000 ||
        config->dma_end - base != 0x60000)
        return DUFS_PLATFORM;
    PE_parse_boot_argn("sweet-qemu-mcq-fault", &mcq.fault, sizeof(mcq.fault));
    if (mcq.fault > FAULT_QEMU_DMA)
        return DUFS_PLATFORM;
    mcq.base = base;
    mcq.bus = config->io;
    host->config.io.read32 = mcq_read;
    host->config.io.write32 = mcq_write;
    host->config.io.dma_read = mcq_dma_read;
    return 0;
}
#endif
