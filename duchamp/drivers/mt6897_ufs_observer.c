#include "mt6897_ufs_observer.h"

static uint32_t state(const struct mt6897_ufs_observer *o)
{
    return __atomic_load_n(&o->state, __ATOMIC_ACQUIRE);
}
static int transition(struct mt6897_ufs_observer *o, uint32_t old, uint32_t next)
{
    return __atomic_compare_exchange_n(&o->state, &old, next, 0,
        __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE);
}
void mt6897_ufs_observer_revoke(struct mt6897_ufs_observer *o)
{
    if (o) __atomic_store_n(&o->state, MUO_FAULTED, __ATOMIC_RELEASE);
}
static int valid_grant(const struct mt6897_ufs_observer *o)
{
    const struct mt6897_ufs_read_grant *g = &o->grant;
    return g->version == MUO_GRANT_VERSION && g->rights == MUO_REQUIRED &&
        g->boot_id == o->boot_id && g->grant_id && g->owner_id && g->resource_epoch &&
        g->base == DUFS_MTK_HCI_BASE && g->bytes == DUFS_MTK_HCI_BYTES && !g->reserved;
}
static int current(struct mt6897_ufs_observer *o, uint32_t required)
{
    return state(o) == required && valid_grant(o) &&
        o->authority.check(o->authority.context, &o->grant) == 0 &&
        state(o) == required && valid_grant(o);
}
static int allow_read(void *context, uint64_t boot, uint64_t base, uint32_t bytes)
{
    struct mt6897_ufs_observer *o = context;
    return boot != o->boot_id || base != DUFS_MTK_HCI_BASE || bytes != DUFS_MTK_HCI_BYTES ||
        !current(o, MUO_READING);
}
static int read32(void *context, uint32_t offset, uint32_t *value)
{
    struct mt6897_ufs_observer *o = context;
    if ((offset & 3) || offset > DUFS_MTK_HCI_BYTES - 4 ||
        !transition(o, MUO_READING, MUO_LOAD))
        return -1;
    int result = o->bus.read32(o->bus.context, o->mapping, offset, value);
    return transition(o, MUO_LOAD, MUO_READING) ? result : -1;
}
int mt6897_ufs_observer_bind(struct mt6897_ufs_observer *o, uint64_t boot,
    const struct mt6897_ufs_read_authority *authority, const struct mt6897_ufs_observer_bus *bus)
{
    if (!o || !boot || !authority || !authority->verify || !authority->check ||
        !bus || !bus->map_readonly || !bus->read32) return MUO_ARGUMENT;
    /* Configuration is installed once before publication to other threads. */
    const struct mt6897_ufs_read_grant *g = &o->grant;
    if (state(o) != MUO_OFF || o->boot_id || o->mapping ||
        o->authority.context || o->authority.verify || o->authority.check ||
        o->bus.context || o->bus.map_readonly || o->bus.read32 ||
        g->version || g->rights || g->boot_id || g->grant_id || g->owner_id ||
        g->resource_epoch || g->base || g->bytes || g->reserved)
        return MUO_STATE;
    o->boot_id = boot;
    o->authority = *authority;
    o->bus = *bus;
    __atomic_store_n(&o->state, MUO_BOUND, __ATOMIC_RELEASE);
    return MUO_OK;
}
int mt6897_ufs_observer_capture(struct mt6897_ufs_observer *o,
    struct dufs_register_snapshot *output)
{
    if (!o || !output) return MUO_ARGUMENT;
    if (!transition(o, MUO_BOUND, MUO_CHECKING)) {
        uint32_t s = state(o);
        return s == MUO_OFF ? MUO_DISABLED : s == MUO_FAULTED ? MUO_REVOKED : MUO_STATE;
    }
    struct mt6897_ufs_read_grant grant = { 0 };
    int result = MUO_ARGUMENT;
    if (!o->boot_id || !o->authority.verify || !o->authority.check ||
        !o->bus.map_readonly || !o->bus.read32) goto fail;
    result = MUO_DENIED;
    if (o->authority.verify(o->authority.context, o->boot_id, &grant)) goto fail;
    o->grant = grant;
    if (!current(o, MUO_CHECKING)) goto fail;
    /* This transition is the mapping authorization point. Revocation which
     * wins it prevents map; a map already authorized may finish but no read
     * is allowed unless the subsequent transition also succeeds.
     */
    if (!transition(o, MUO_CHECKING, MUO_MAPPING)) goto fail;
    o->mapping = o->bus.map_readonly(o->bus.context, DUFS_MTK_HCI_BASE, DUFS_MTK_HCI_BYTES);
    result = MUO_MAP;
    if (!o->mapping || (o->mapping & 3) || o->mapping > UINTPTR_MAX - DUFS_MTK_HCI_BYTES)
        goto fail;
    result = MUO_REVOKED;
    if (!transition(o, MUO_MAPPING, MUO_READING)) goto fail;
    struct dufs_register_snapshot captured = { 0 };
    const struct dufs_snapshot_source source = { .context = o, .allow_read = allow_read,
        .read32 = read32, .boot_id = o->boot_id, .physical_base = DUFS_MTK_HCI_BASE,
        .bytes = DUFS_MTK_HCI_BYTES, .profile = DUFS_SNAPSHOT_MT6897 };
    int error = dufs_snapshot_registers(&source, &captured);
    if (error) {
        result = error == DUFS_SNAPSHOT_DENIED ? MUO_DENIED :
            error == DUFS_SNAPSHOT_LAYOUT ? MUO_LAYOUT : MUO_IO;
        goto fail;
    }
    result = MUO_DENIED;
    if (!current(o, MUO_READING)) goto fail;
    result = MUO_REVOKED;
    if (!transition(o, MUO_READING, MUO_DONE)) goto fail;
    *output = captured;
    return MUO_OK; /* Observation only, including active/inherited queue flags. */
fail:
    if (state(o) == MUO_FAULTED) result = MUO_REVOKED;
    mt6897_ufs_observer_revoke(o);
    return result;
}
