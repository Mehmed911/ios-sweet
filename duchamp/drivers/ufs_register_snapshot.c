#include "ufs_register_snapshot.h"

struct reader {
    const struct dufs_snapshot_source *source;
    uint32_t runtime, reads;
};
static int read_register(struct reader *r, uint32_t offset, uint32_t *value)
{
    const struct dufs_snapshot_source *s = r->source;
    if ((offset & 3) || offset > s->bytes - 4)
        return DUFS_SNAPSHOT_LAYOUT;
    if (s->allow_read(s->context, s->boot_id, s->physical_base, s->bytes))
        return DUFS_SNAPSHOT_DENIED;
    ++r->reads;
    return s->read32(s->context, offset, value) ? DUFS_SNAPSHOT_IO : 0;
}
#define READ(offset, field) do { \
    int error = read_register(r, (offset), &(field)); \
    if (error) return error; \
} while (0)

static int sample(struct reader *r, struct dufs_register_sample *v)
{
    READ(0, v->cap);
    READ(8, v->version);
    if (v->cap == UINT32_MAX || v->version < 0x100 || v->version > 0x4ff)
        return DUFS_SNAPSHOT_LAYOUT;
    READ(0x34, v->hce);
    READ(0x30, v->hcs);
    if (v->hce > 3 || v->hcs == UINT32_MAX)
        return DUFS_SNAPSHOT_LAYOUT;
    READ(0x50, v->transfer_base_lo); READ(0x54, v->transfer_base_hi);
    READ(0x58, v->transfer_doorbell); READ(0x60, v->transfer_run);
    READ(0x70, v->task_base_lo); READ(0x74, v->task_base_hi);
    READ(0x78, v->task_doorbell); READ(0x80, v->task_run);
    if (!(v->cap & (1u << 30)))
        return 0;
    READ(4, v->mcqcap);
    v->queues = (v->mcqcap & 255) + 1;
    v->queue_config_base = ((v->mcqcap >> 16) & 255) * 0x200;
    /* Runtime offsets come from the platform source, never from an assumed
     * QEMU address. QCFGPTR is hardware supplied and checked before use.
     */
    if (v->queues > DUFS_MCQ_MAX_QUEUES || v->queue_config_base < 0x400 ||
        v->queue_config_base + v->queues * DUFS_MCQ_CONFIG_STRIDE > r->runtime)
        return DUFS_SNAPSHOT_LAYOUT;
    READ(0x300, v->config);
    for (uint32_t i = 0; i < v->queues; ++i) {
        struct dufs_queue_snapshot *q = &v->queue[i];
        uint32_t c = v->queue_config_base + i * DUFS_MCQ_CONFIG_STRIDE;
        uint32_t o = r->runtime + i * DUFS_MCQ_STRIDE;
        READ(c, q->sq_attr); READ(c + 4, q->sq_base_lo);
        READ(c + 8, q->sq_base_hi); READ(c + 0xc, q->sq_dao);
        READ(c + 0x10, q->sq_isao); READ(c + 0x14, q->sq_config);
        READ(c + 0x20, q->cq_attr); READ(c + 0x24, q->cq_base_lo);
        READ(c + 0x28, q->cq_base_hi); READ(c + 0x2c, q->cq_dao);
        READ(c + 0x30, q->cq_isao); READ(c + 0x34, q->cq_config);
        READ(o + DUFS_MCQ_SQ_HEAD, q->sq_head);
        READ(o + DUFS_MCQ_SQ_TAIL, q->sq_tail);
        READ(o + DUFS_MCQ_SQ_IS, q->sq_is);
        READ(o + DUFS_MCQ_CQ_HEAD, q->cq_head);
        READ(o + DUFS_MCQ_CQ_TAIL, q->cq_tail);
        READ(o + DUFS_MCQ_CQ_IS, q->cq_is);
    }
    return 0;
}
#undef READ

static int bad_pointer(uint32_t attr, uint32_t head, uint32_t tail)
{
    uint32_t bytes = ((attr & 0xffff) + 1) * 4;
    if (!(attr & (1u << 31)))
        return head || tail;
    return bytes < 64 || (bytes & 31) || (head & 31) || (tail & 31) ||
        head >= bytes || tail >= bytes;
}
static uint32_t blockers(const struct dufs_register_sample *v)
{
    uint32_t b = v->hce ? DUFS_SNAPSHOT_HCE_ACTIVE : 0;
    if (v->transfer_run || v->task_run) b |= DUFS_SNAPSHOT_LEGACY_RUNNING;
    if (v->transfer_doorbell || v->task_doorbell) b |= DUFS_SNAPSHOT_LEGACY_PENDING;
    if (v->transfer_base_lo || v->transfer_base_hi || v->task_base_lo || v->task_base_hi)
        b |= DUFS_SNAPSHOT_LISTS_CONFIGURED;
    if (v->config & 1) b |= DUFS_SNAPSHOT_MCQ_ENABLED;
    for (uint32_t i = 0; i < v->queues; ++i) {
        const struct dufs_queue_snapshot *q = &v->queue[i];
        if ((q->sq_attr | q->cq_attr) & (1u << 31)) b |= DUFS_SNAPSHOT_MCQ_ENABLED;
        if (q->sq_head != q->sq_tail || q->cq_head != q->cq_tail || q->sq_is || q->cq_is)
            b |= DUFS_SNAPSHOT_MCQ_PENDING;
        if (q->sq_attr || q->cq_attr || q->sq_base_lo || q->sq_base_hi ||
            q->cq_base_lo || q->cq_base_hi || q->sq_config || q->cq_config)
            b |= DUFS_SNAPSHOT_LISTS_CONFIGURED;
        if (bad_pointer(q->sq_attr, q->sq_head, q->sq_tail) ||
            bad_pointer(q->cq_attr, q->cq_head, q->cq_tail)) b |= DUFS_SNAPSHOT_BAD_POINTER;
    }
    return b;
}
static int equal_sample(const struct dufs_register_sample *a,
    const struct dufs_register_sample *b)
{
    /* All fields are uint32_t. Compare bytes without depending on libc. */
    const unsigned char *x = (const void *)a, *y = (const void *)b;
    for (unsigned i = 0; i < sizeof(*a); ++i) if (x[i] != y[i]) return 0;
    return 1;
}
int dufs_snapshot_registers(const struct dufs_snapshot_source *source,
    struct dufs_register_snapshot *output)
{
    if (!source || !output || !source->allow_read || !source->read32 ||
        !source->boot_id || (source->physical_base & 3) || source->bytes < 0x84 ||
        source->physical_base > UINT64_MAX - source->bytes)
        return DUFS_SNAPSHOT_ARGUMENT;
    struct reader r = { .source = source };
    switch (source->profile) {
    case DUFS_SNAPSHOT_MT6897:
        if (source->physical_base != DUFS_MTK_HCI_BASE || source->bytes != DUFS_MTK_HCI_BYTES)
            return DUFS_SNAPSHOT_LAYOUT;
        r.runtime = DUFS_MTK_MCQ_RUNTIME;
        break;
    case DUFS_SNAPSHOT_QEMU:
        if (source->bytes != 0x2000) return DUFS_SNAPSHOT_LAYOUT;
        r.runtime = DUFS_QEMU_MCQ_RUNTIME;
        break;
    default: return DUFS_SNAPSHOT_LAYOUT;
    }
    struct dufs_register_snapshot result = { .boot_id = source->boot_id,
        .physical_base = source->physical_base, .profile = source->profile };
    int error = sample(&r, &result.first);
    if (!error) error = sample(&r, &result.last);
    if (error) return error;
    result.reads = r.reads;
    result.blockers = blockers(&result.first) | blockers(&result.last);
    if (!equal_sample(&result.first, &result.last)) result.blockers |= DUFS_SNAPSHOT_CHANGED;
    *output = result;
    return DUFS_SNAPSHOT_OK;
}
