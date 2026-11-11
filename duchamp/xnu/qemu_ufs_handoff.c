/* An opt-in record for the virtual UFS controller, supplied by the QEMU fixture. */
#if defined(ARM64_BOARD_CONFIG_SWEET) || defined(DUCHAMP_HANDOFF_PINNED_QEMU_REPLAY)
#include <stdint.h>
#include <stddef.h>

#if defined(DUCHAMP_HANDOFF_PINNED_QEMU_REPLAY)
/* The local replay links these calls to the pinned Darwin kernel's symbols. */
typedef const void *DTEntry;
enum { kSuccess = 1 };
extern int PE_parse_boot_argn(const char *, void *, int);
extern int SecureDTLookupEntry(DTEntry, const char *, DTEntry *);
extern int SecureDTGetProperty(DTEntry, const char *, const void **, unsigned *);
#else
#include <pexpert/pexpert.h>
#include <pexpert/device_tree.h>
#endif

enum handoff_verdict {
    HANDOFF_OFF, HANDOFF_ALLOW, HANDOFF_BOOT_ID, HANDOFF_QUEUES,
    HANDOFF_DMA, HANDOFF_CACHE, HANDOFF_INVALID
};
enum handoff_proof {
    FINAL_EXIT = 1u << 0, HCE_OBSERVED = 1u << 1, QUEUES_OBSERVED = 1u << 2,
    RESOURCES_GRANTED = 1u << 3, DMA_GRANTED = 1u << 4, CACHE_GRANTED = 1u << 5
};

/* Little-endian, version 1. The sole supported model is legacy UFS. */
struct bl31_fixture {
    uint32_t version, proof;
    uint64_t boot_id;
    uint32_t mode, hce, transfer_doorbell, task_doorbell;
    uint32_t transfer_run, task_run, outstanding, reserved;
    uint64_t dma_owner, cache_owner;
};

static struct {
    uint64_t entry_id, bl31_id;
    enum handoff_verdict verdict;
} handoff;

void duchamp_qemu_ufs_handoff_enter(void);
extern void sweet_early_mark(unsigned int, const char *);
int duchamp_qemu_ufs_handoff_allows(void);

static int
qemu_profile(DTEntry chosen)
{
    static const char qemu_firmware[] = "duchamp-qemu-ufs-fixture-v1";
    const void *value;
    unsigned size;

    if (SecureDTGetProperty(chosen, "firmware-version", &value, &size) != kSuccess ||
        size != sizeof(qemu_firmware))
        return 0;
    const char *name = value;
    for (unsigned i = 0; i < sizeof(qemu_firmware); ++i)
        if (name[i] != qemu_firmware[i])
            return 0;
    return 1;
}

static enum handoff_verdict
check_record(const struct bl31_fixture *record)
{
    if (record->version != 1 || record->reserved ||
        (record->proof & (FINAL_EXIT | RESOURCES_GRANTED)) != (FINAL_EXIT | RESOURCES_GRANTED))
        return HANDOFF_INVALID;
    if (!handoff.entry_id || handoff.entry_id != record->boot_id)
        return HANDOFF_BOOT_ID;
    if ((record->proof & (HCE_OBSERVED | QUEUES_OBSERVED)) != (HCE_OBSERVED | QUEUES_OBSERVED) ||
        record->mode != 1 || record->hce || record->transfer_doorbell || record->task_doorbell ||
        record->transfer_run || record->task_run || record->outstanding)
        return HANDOFF_QUEUES;
    if (!(record->proof & DMA_GRANTED) || !record->dma_owner)
        return HANDOFF_DMA;
    if (!(record->proof & CACHE_GRANTED) || !record->cache_owner)
        return HANDOFF_CACHE;
    return HANDOFF_ALLOW;
}

static void
capture_entry(void)
{
    uint32_t enabled = 0;
    if (!PE_parse_boot_argn("sweet-qemu-ufs-handoff", &enabled, sizeof(enabled)))
        return;

    handoff.verdict = HANDOFF_INVALID;
    DTEntry chosen;
    const void *value;
    unsigned size;
    if (enabled != 1 || SecureDTLookupEntry(NULL, "/chosen", &chosen) != kSuccess ||
        !qemu_profile(chosen))
        return;

    /* The loader supplies the entry ID in boot args, independently of the
     * synthetic BL31 record in the ADT. Capture it as soon as PE opens the ADT.
     */
    PE_parse_boot_argn("sweet-qemu-boot-id", &handoff.entry_id, sizeof(handoff.entry_id));
    struct bl31_fixture record;
    if (SecureDTGetProperty(chosen, "qemu-bl31-ufs", &value, &size) != kSuccess ||
        size != sizeof(record))
        return;

    /* ADT values can be only four-byte aligned. */
    const unsigned char *source = value;
    unsigned char *destination = (void *)&record;
    for (unsigned i = 0; i < sizeof(record); ++i)
        destination[i] = source[i];

    handoff.bl31_id = record.boot_id;
    handoff.verdict = check_record(&record);
}

static void
write_id(char *label, uint64_t id)
{
    for (unsigned i = 0; i < 16; ++i) {
        label[15 - i] = "0123456789abcdef"[id & 15u];
        id >>= 4;
    }
}

static void
report_entry(unsigned stage)
{
    char label[] = "UFS XNU=0000000000000000 BL31=0000000000000000 V=0";
    write_id(label + sizeof("UFS XNU=") - 1, handoff.entry_id);
    write_id(label + sizeof("UFS XNU=0000000000000000 BL31=") - 1, handoff.bl31_id);
    label[sizeof(label) - 2] = (char)('0' + handoff.verdict);
    sweet_early_mark(stage, label);
}

void
duchamp_qemu_ufs_handoff_enter(void)
{
    capture_entry();
    if (handoff.verdict != HANDOFF_OFF)
        report_entry(2);
}

int
duchamp_qemu_ufs_handoff_allows(void)
{
    uint32_t enabled = 0;
    if (handoff.verdict == HANDOFF_OFF)
        return !PE_parse_boot_argn("sweet-qemu-ufs-handoff", &enabled, sizeof(enabled));
    report_entry(163);
    return handoff.verdict == HANDOFF_ALLOW;
}
#endif
