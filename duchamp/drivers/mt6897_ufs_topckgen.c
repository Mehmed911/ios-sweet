#include "mt6897_ufs_topckgen.h"

/* Callback-only model of the two UFS-related CLK_CFG_10 composites. It does
 * not control either parent PLL and does not establish firmware ownership.
 */
struct top_clock_desc {
    unsigned clock_id;
    uint8_t shift;
    uint8_t gate_bit;
    uint8_t update_bit;
    unsigned parent[2];
    uint8_t selector[2];
};

static const struct top_clock_desc top_clocks[] = {
    { MTUFS_TOP_AES_UFSFDE_SEL, 16, 23, 11,
      { MTUFS_TOP_UNIVPLL_D6, MTUFS_TOP_MAINPLL_D4 }, { 6, 1 } },
    { MTUFS_TOP_UFS_SEL, 24, 31, 12,
      { MTUFS_TOP_MAINPLL_D4_D2, MTUFS_TOP_MMPLL_D6 }, { 1, 7 } },
};

static const struct top_clock_desc *clock_desc(unsigned clock_id)
{
    unsigned i;

    for (i = 0; i < sizeof(top_clocks) / sizeof(top_clocks[0]); i++) {
        if (top_clocks[i].clock_id == clock_id) {
            return &top_clocks[i];
        }
    }
    return 0;
}

static int fail(struct mtufs_topckgen *top, int result)
{
    top->state = 2;
    return result;
}

static int ready(struct mtufs_topckgen *top,
                 const struct top_clock_desc *desc)
{
    if (!top || !desc) {
        return MTUFS_TOP_ARGUMENT;
    }
    return top->state == 1 ? MTUFS_TOP_OK : MTUFS_TOP_FAULTED;
}

static int authorised(struct mtufs_topckgen *top,
                      const struct top_clock_desc *desc, uint32_t offset,
                      enum mtufs_top_access access, int mutated)
{
    if (top->ops.authorise(top->ops.context, desc->clock_id, offset, access) == 1) {
        return MTUFS_TOP_OK;
    }
    return mutated ? fail(top, MTUFS_TOP_UNVERIFIED) : MTUFS_TOP_UNVERIFIED;
}

static int read_reg(struct mtufs_topckgen *top,
                    const struct top_clock_desc *desc, uint32_t offset,
                    uint32_t *value, int mutated)
{
    int result = authorised(top, desc, offset, MTUFS_TOP_READ, mutated);

    if (result != MTUFS_TOP_OK) {
        return result;
    }
    if (top->ops.read32(top->ops.context, offset, value) != 0) {
        return fail(top, MTUFS_TOP_IO);
    }
    return MTUFS_TOP_OK;
}

static int write_reg(struct mtufs_topckgen *top,
                     const struct top_clock_desc *desc, uint32_t offset,
                     uint32_t value, int *mutated)
{
    int result = authorised(top, desc, offset, MTUFS_TOP_WRITE, *mutated);

    if (result != MTUFS_TOP_OK) {
        return result;
    }
    if (top->ops.write32(top->ops.context, offset, value) != 0) {
        return fail(top, MTUFS_TOP_IO);
    }
    *mutated = 1;
    return MTUFS_TOP_OK;
}

static int wait_cfg(struct mtufs_topckgen *top,
                    const struct top_clock_desc *desc, uint32_t mask,
                    uint32_t expected, int mutated)
{
    uint64_t start = top->ops.microseconds(top->ops.context);
    uint16_t poll;

    for (poll = 0; poll < top->max_polls; poll++) {
        uint32_t value;
        int result = read_reg(top, desc, MTUFS_TOP_CLK_CFG_10, &value, mutated);

        if (result != MTUFS_TOP_OK) {
            return result;
        }
        if ((value & mask) == expected) {
            return MTUFS_TOP_OK;
        }
        if (top->ops.microseconds(top->ops.context) - start >= top->timeout_us) {
            return fail(top, MTUFS_TOP_TIMEOUT);
        }
    }
    return fail(top, MTUFS_TOP_TIMEOUT);
}

int mtufs_topckgen_bind(struct mtufs_topckgen *top,
                        const struct mtufs_topckgen_ops *ops,
                        uint32_t timeout_us, uint16_t max_polls)
{
    if (!top || !ops || !timeout_us || timeout_us > 100000u ||
        !max_polls || max_polls > 1024u || !ops->authorise ||
        !ops->read32 || !ops->write32 || !ops->barrier ||
        !ops->microseconds) {
        return MTUFS_TOP_ARGUMENT;
    }
    if (top->state != 0) {
        return MTUFS_TOP_FAULTED;
    }
    top->ops = *ops;
    top->timeout_us = timeout_us;
    top->max_polls = max_polls;
    top->state = 1;
    return MTUFS_TOP_OK;
}

int mtufs_topckgen_set_parent(struct mtufs_topckgen *top, unsigned clock_id,
                              unsigned parent_id)
{
    const struct top_clock_desc *desc = clock_desc(clock_id);
    uint32_t value, mask, selected;
    unsigned i;
    int mutated = 0;
    int result = ready(top, desc);

    if (result != MTUFS_TOP_OK) {
        return result;
    }
    for (i = 0; i < 2; i++) {
        if (desc->parent[i] == parent_id) {
            break;
        }
    }
    if (i == 2) {
        return MTUFS_TOP_ARGUMENT;
    }
    mask = 7u << desc->shift;
    selected = (uint32_t)desc->selector[i] << desc->shift;
    result = read_reg(top, desc, MTUFS_TOP_CLK_CFG_10, &value, mutated);
    if (result != MTUFS_TOP_OK || (value & mask) == selected) {
        return result;
    }
    result = write_reg(top, desc, MTUFS_TOP_CLK_CFG_10_CLR, mask, &mutated);
    if (result == MTUFS_TOP_OK) {
        result = write_reg(top, desc, MTUFS_TOP_CLK_CFG_10_SET,
                           selected, &mutated);
    }
    if (result == MTUFS_TOP_OK) {
        result = write_reg(top, desc, MTUFS_TOP_CLK_CFG_UPDATE1,
                           1u << desc->update_bit, &mutated);
    }
    if (result != MTUFS_TOP_OK) {
        return result;
    }
    top->ops.barrier(top->ops.context);
    return wait_cfg(top, desc, mask, selected, mutated);
}

static int set_gate(struct mtufs_topckgen *top, unsigned clock_id, int enable)
{
    const struct top_clock_desc *desc = clock_desc(clock_id);
    uint32_t mask;
    int mutated = 0;
    int result = ready(top, desc);

    if (result != MTUFS_TOP_OK) {
        return result;
    }
    mask = 1u << desc->gate_bit;
    result = write_reg(top, desc,
                       enable ? MTUFS_TOP_CLK_CFG_10_CLR
                              : MTUFS_TOP_CLK_CFG_10_SET,
                       mask, &mutated);
    if (result != MTUFS_TOP_OK) {
        return result;
    }
    top->ops.barrier(top->ops.context);
    return wait_cfg(top, desc, mask, enable ? 0u : mask, mutated);
}

int mtufs_topckgen_enable(struct mtufs_topckgen *top, unsigned clock_id)
{
    return set_gate(top, clock_id, 1);
}

int mtufs_topckgen_disable(struct mtufs_topckgen *top, unsigned clock_id)
{
    return set_gate(top, clock_id, 0);
}

int mtufs_topckgen_status(struct mtufs_topckgen *top, unsigned clock_id,
                          unsigned *selector, int *enabled)
{
    const struct top_clock_desc *desc = clock_desc(clock_id);
    uint32_t value;
    int result;

    if (!selector || !enabled) {
        return MTUFS_TOP_ARGUMENT;
    }
    result = ready(top, desc);
    if (result != MTUFS_TOP_OK) {
        return result;
    }
    result = read_reg(top, desc, MTUFS_TOP_CLK_CFG_10, &value, 0);
    if (result != MTUFS_TOP_OK) {
        return result;
    }
    *selector = (value >> desc->shift) & 7u;
    *enabled = (value & (1u << desc->gate_bit)) == 0;
    return MTUFS_TOP_OK;
}

int mtufs_topckgen_faulted(const struct mtufs_topckgen *top)
{
    return top != 0 && top->state == 2;
}
