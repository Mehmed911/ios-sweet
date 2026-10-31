#include "mt6897_ufs_topckgen.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static unsigned checks;
#define CHECK(value) do { checks++; assert(value); } while (0)

struct write_event {
    uint32_t offset;
    uint32_t value;
};

struct model {
    uint32_t cfg;
    uint32_t shadow;
    struct write_event event[8];
    char io[32];
    unsigned authorisations;
    unsigned reads;
    unsigned writes;
    unsigned barriers;
    unsigned delay_reads;
    unsigned fail_read_on;
    unsigned fail_write_on;
    unsigned deny_auth_at;
    unsigned io_count;
    uint64_t tick;
    int permitted;
    int access_token;
    int pending;
    int stall;
};

static void trace_io(struct model *model, char kind)
{
    assert(model->io_count + 1 < sizeof(model->io));
    model->io[model->io_count++] = kind;
    model->io[model->io_count] = '\0';
}

static int authorise(void *context, unsigned clock_id, uint32_t offset,
                     enum mtufs_top_access access)
{
    struct model *model = context;

    assert(clock_id == MTUFS_TOP_AES_UFSFDE_SEL ||
           clock_id == MTUFS_TOP_UFS_SEL);
    assert(offset == MTUFS_TOP_CLK_CFG_10 ||
           offset == MTUFS_TOP_CLK_CFG_10_SET ||
           offset == MTUFS_TOP_CLK_CFG_10_CLR ||
           offset == MTUFS_TOP_CLK_CFG_UPDATE1);
    assert(access == MTUFS_TOP_READ || access == MTUFS_TOP_WRITE);
    model->authorisations++;
    if (model->deny_auth_at == model->authorisations) {
        return 0;
    }
    if (model->permitted) {
        assert(model->access_token == 0);
        model->access_token = 1;
    }
    return model->permitted;
}

static int read32(void *context, uint32_t offset, uint32_t *value)
{
    struct model *model = context;

    assert(model->access_token == 1);
    model->access_token = 0;
    model->reads++;
    trace_io(model, 'R');
    assert(offset == MTUFS_TOP_CLK_CFG_10);
    if (model->fail_read_on == model->reads) {
        return -1;
    }
    if (model->pending && !model->stall) {
        if (model->delay_reads == 0) {
            model->cfg = model->shadow;
            model->pending = 0;
        } else {
            model->delay_reads--;
        }
    }
    *value = model->cfg;
    return 0;
}

static int write32(void *context, uint32_t offset, uint32_t value)
{
    struct model *model = context;

    assert(model->access_token == 1);
    model->access_token = 0;
    model->writes++;
    trace_io(model, 'W');
    assert(model->writes <= sizeof(model->event) / sizeof(model->event[0]));
    model->event[model->writes - 1].offset = offset;
    model->event[model->writes - 1].value = value;
    if (model->fail_write_on == model->writes) {
        return -1;
    }
    if (offset == MTUFS_TOP_CLK_CFG_10_CLR ||
        offset == MTUFS_TOP_CLK_CFG_10_SET) {
        if (!model->pending) {
            model->shadow = model->cfg;
        }
        if (offset == MTUFS_TOP_CLK_CFG_10_CLR) {
            model->shadow &= ~value;
        } else {
            model->shadow |= value;
        }
        model->pending = 1;
    } else {
        assert(offset == MTUFS_TOP_CLK_CFG_UPDATE1);
    }
    return 0;
}

static void barrier(void *context)
{
    ((struct model *)context)->barriers++;
}

static uint64_t microseconds(void *context)
{
    return ((struct model *)context)->tick++;
}

static struct mtufs_topckgen_ops make_ops(struct model *model)
{
    struct mtufs_topckgen_ops ops = {
        model, authorise, read32, write32, barrier, microseconds
    };
    return ops;
}

static void reset_trace(struct model *model)
{
    model->authorisations = 0;
    model->reads = 0;
    model->writes = 0;
    model->barriers = 0;
    model->fail_read_on = 0;
    model->fail_write_on = 0;
    model->deny_auth_at = 0;
    model->access_token = 0;
    model->io_count = 0;
    model->tick = 0;
    memset(model->event, 0, sizeof(model->event));
    memset(model->io, 0, sizeof(model->io));
}

static void test_bind(void)
{
    struct model model = { .permitted = 1 };
    struct mtufs_topckgen top = { 0 };
    struct mtufs_topckgen_ops ops = make_ops(&model);
    struct mtufs_topckgen_ops bad;

    CHECK(MTUFS_TOPCKGEN_BASE == 0x10000000ull);
    CHECK(MTUFS_TOPCKGEN_SIZE == 0x1000u);
    CHECK(mtufs_topckgen_bind(0, &ops, 10, 4) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_bind(&top, 0, 10, 4) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_bind(&top, &ops, 0, 4) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_bind(&top, &ops, 100001, 4) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 0) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 1025) == MTUFS_TOP_ARGUMENT);
    bad = ops; bad.authorise = 0;
    CHECK(mtufs_topckgen_bind(&top, &bad, 10, 4) == MTUFS_TOP_ARGUMENT);
    bad = ops; bad.read32 = 0;
    CHECK(mtufs_topckgen_bind(&top, &bad, 10, 4) == MTUFS_TOP_ARGUMENT);
    bad = ops; bad.write32 = 0;
    CHECK(mtufs_topckgen_bind(&top, &bad, 10, 4) == MTUFS_TOP_ARGUMENT);
    bad = ops; bad.barrier = 0;
    CHECK(mtufs_topckgen_bind(&top, &bad, 10, 4) == MTUFS_TOP_ARGUMENT);
    bad = ops; bad.microseconds = 0;
    CHECK(mtufs_topckgen_bind(&top, &bad, 10, 4) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 4) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 4) == MTUFS_TOP_FAULTED);
    CHECK(!mtufs_topckgen_faulted(&top));
    CHECK(!mtufs_topckgen_faulted(0));
}

static void test_parent(unsigned clock_id, unsigned parent_id,
                        unsigned selector, unsigned shift,
                        unsigned update_bit)
{
    const uint32_t mask = 7u << shift;
    const uint32_t initial = 0xa55aa55au & ~mask;
    struct model model = { .cfg = initial };
    struct mtufs_topckgen top = { 0 };
    struct mtufs_topckgen_ops ops = make_ops(&model);

    CHECK(mtufs_topckgen_bind(&top, &ops, 20, 8) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_set_parent(&top, clock_id, parent_id) ==
          MTUFS_TOP_UNVERIFIED);
    CHECK(model.authorisations == 1 && model.reads == 0 && model.writes == 0);
    CHECK(!mtufs_topckgen_faulted(&top));

    model.permitted = 1;
    reset_trace(&model);
    CHECK(mtufs_topckgen_set_parent(&top, clock_id, parent_id) == MTUFS_TOP_OK);
    CHECK(strcmp(model.io, "RWWWR") == 0);
    CHECK(model.authorisations == model.reads + model.writes);
    CHECK(model.reads == 2 && model.writes == 3 && model.barriers == 1);
    CHECK(model.event[0].offset == MTUFS_TOP_CLK_CFG_10_CLR &&
          model.event[0].value == mask);
    CHECK(model.event[1].offset == MTUFS_TOP_CLK_CFG_10_SET &&
          model.event[1].value == selector << shift);
    CHECK(model.event[2].offset == MTUFS_TOP_CLK_CFG_UPDATE1 &&
          model.event[2].value == 1u << update_bit);
    CHECK((model.cfg & mask) == selector << shift);
    CHECK((model.cfg & ~mask) == (initial & ~mask));

    reset_trace(&model);
    CHECK(mtufs_topckgen_set_parent(&top, clock_id, parent_id) == MTUFS_TOP_OK);
    CHECK(strcmp(model.io, "R") == 0 && model.writes == 0);
    CHECK(model.authorisations == 1);
}

static void test_gates(unsigned clock_id, unsigned gate_bit)
{
    const uint32_t gate = 1u << gate_bit;
    struct model model = { .cfg = gate, .permitted = 1 };
    struct mtufs_topckgen top = { 0 };
    struct mtufs_topckgen_ops ops = make_ops(&model);
    unsigned selector = 99;
    int enabled = -1;

    CHECK(mtufs_topckgen_bind(&top, &ops, 20, 8) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_enable(&top, clock_id) == MTUFS_TOP_OK);
    CHECK(strcmp(model.io, "WR") == 0);
    CHECK(model.event[0].offset == MTUFS_TOP_CLK_CFG_10_CLR &&
          model.event[0].value == gate);
    CHECK(model.authorisations == 2 && model.barriers == 1);
    CHECK((model.cfg & gate) == 0);

    reset_trace(&model);
    CHECK(mtufs_topckgen_status(&top, clock_id, &selector, &enabled) ==
          MTUFS_TOP_OK);
    CHECK(strcmp(model.io, "R") == 0 && model.authorisations == 1);
    CHECK(enabled == 1);

    reset_trace(&model);
    CHECK(mtufs_topckgen_disable(&top, clock_id) == MTUFS_TOP_OK);
    CHECK(strcmp(model.io, "WR") == 0);
    CHECK(model.event[0].offset == MTUFS_TOP_CLK_CFG_10_SET &&
          model.event[0].value == gate);
    CHECK(model.authorisations == 2 && model.barriers == 1);
    CHECK((model.cfg & gate) == gate);
}

static void test_bounds_and_faults(void)
{
    struct model model = { .cfg = 0, .permitted = 1, .delay_reads = 2 };
    struct mtufs_topckgen top = { 0 };
    struct mtufs_topckgen_ops ops = make_ops(&model);
    unsigned selector;
    int enabled;
    unsigned before;

    CHECK(mtufs_topckgen_bind(&top, &ops, 100, 3) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MMPLL_D6) == MTUFS_TOP_OK);
    CHECK(model.reads == 4 && model.writes == 3);
    CHECK(model.authorisations == 7);

    model = (struct model){ .cfg = 0, .permitted = 1, .stall = 1 };
    top = (struct mtufs_topckgen){ 0 };
    ops = make_ops(&model);
    CHECK(mtufs_topckgen_bind(&top, &ops, 100, 2) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MMPLL_D6) == MTUFS_TOP_TIMEOUT);
    CHECK(model.reads == 3 && model.writes == 3);
    CHECK(mtufs_topckgen_faulted(&top));
    before = model.authorisations;
    CHECK(mtufs_topckgen_enable(&top, MTUFS_TOP_UFS_SEL) == MTUFS_TOP_FAULTED);
    CHECK(model.authorisations == before);

    model = (struct model){ .cfg = 0, .permitted = 1, .stall = 1 };
    top = (struct mtufs_topckgen){ 0 };
    ops = make_ops(&model);
    CHECK(mtufs_topckgen_bind(&top, &ops, 1, 20) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MMPLL_D6) == MTUFS_TOP_TIMEOUT);
    CHECK(model.reads == 2 && model.writes == 3);

    model = (struct model){ .permitted = 1, .fail_read_on = 1 };
    top = (struct mtufs_topckgen){ 0 };
    ops = make_ops(&model);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 4) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_status(&top, MTUFS_TOP_UFS_SEL, &selector, &enabled) ==
          MTUFS_TOP_IO);
    CHECK(mtufs_topckgen_faulted(&top));

    model = (struct model){ .permitted = 1, .fail_write_on = 2 };
    top = (struct mtufs_topckgen){ 0 };
    ops = make_ops(&model);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 4) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MMPLL_D6) == MTUFS_TOP_IO);
    CHECK(model.reads == 1 && model.writes == 2 && mtufs_topckgen_faulted(&top));

    model = (struct model){ .permitted = 1, .fail_read_on = 2 };
    top = (struct mtufs_topckgen){ 0 };
    ops = make_ops(&model);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 4) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MMPLL_D6) == MTUFS_TOP_IO);
    CHECK(model.writes == 3 && mtufs_topckgen_faulted(&top));
}

static void test_authorisation_and_arguments(void)
{
    struct model model = { .permitted = 1, .deny_auth_at = 2 };
    struct mtufs_topckgen top = { 0 };
    struct mtufs_topckgen_ops ops = make_ops(&model);
    unsigned selector = 77;
    int enabled = 77;
    unsigned accesses;

    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 8) == MTUFS_TOP_OK);
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MMPLL_D6) == MTUFS_TOP_UNVERIFIED);
    CHECK(model.reads == 1 && model.writes == 0);
    CHECK(!mtufs_topckgen_faulted(&top));

    model.deny_auth_at = 0;
    reset_trace(&model);
    model.deny_auth_at = 3;
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MMPLL_D6) == MTUFS_TOP_UNVERIFIED);
    CHECK(model.reads == 1 && model.writes == 1);
    CHECK(mtufs_topckgen_faulted(&top));

    model = (struct model){ .permitted = 1 };
    top = (struct mtufs_topckgen){ 0 };
    ops = make_ops(&model);
    CHECK(mtufs_topckgen_bind(&top, &ops, 10, 8) == MTUFS_TOP_OK);
    accesses = model.authorisations;
    CHECK(mtufs_topckgen_set_parent(&top, 40, MTUFS_TOP_MMPLL_D6) ==
          MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_set_parent(&top, MTUFS_TOP_UFS_SEL,
                                    MTUFS_TOP_MAINPLL_D4) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_enable(&top, 99) == MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_status(&top, MTUFS_TOP_UFS_SEL, 0, &enabled) ==
          MTUFS_TOP_ARGUMENT);
    CHECK(mtufs_topckgen_status(&top, MTUFS_TOP_UFS_SEL, &selector, 0) ==
          MTUFS_TOP_ARGUMENT);
    CHECK(model.authorisations == accesses && model.reads == 0 && model.writes == 0);
    CHECK(selector == 77 && enabled == 77);
}

int main(void)
{
    test_bind();
    test_parent(MTUFS_TOP_AES_UFSFDE_SEL, MTUFS_TOP_UNIVPLL_D6, 6, 16, 11);
    test_parent(MTUFS_TOP_AES_UFSFDE_SEL, MTUFS_TOP_MAINPLL_D4, 1, 16, 11);
    test_parent(MTUFS_TOP_UFS_SEL, MTUFS_TOP_MAINPLL_D4_D2, 1, 24, 12);
    test_parent(MTUFS_TOP_UFS_SEL, MTUFS_TOP_MMPLL_D6, 7, 24, 12);
    test_gates(MTUFS_TOP_AES_UFSFDE_SEL, 23);
    test_gates(MTUFS_TOP_UFS_SEL, 31);
    test_bounds_and_faults();
    test_authorisation_and_arguments();
    printf("%u MT6897 UFS topckgen callback-model checks passed; no MMIO backend\n",
           checks);
    return 0;
}
