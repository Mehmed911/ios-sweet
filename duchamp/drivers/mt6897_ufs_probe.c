#include "mt6897_ufs_probe.h"

enum { SCSI_READ_16 = 0x88 };

static int
probe_dispatch(void *context, const struct mt6897_ufs_provider_request *request,
    uint64_t *result)
{
    struct mt6897_ufs_probe *probe = context;
    struct dufs_host *host = probe->host;
    struct dufs_config config = { 0 };
    uint64_t blocks;
    uint32_t block_bytes;
    int error;

    if (request->version != MT6897_UFS_PROVIDER_REQUEST_VERSION ||
        request->operation != MT6897_UFS_PROVIDER_COMMAND ||
        request->argument[0] != SCSI_READ_16 ||
        request->argument[1] != MT6897_UFS_PROBE_LUN ||
        request->argument[2] != MT6897_UFS_PROBE_LBA ||
        request->argument[3] != 1 ||
        __atomic_load_n(&probe->attempted, __ATOMIC_ACQUIRE) != 1) {
        return DUFS_ARGUMENT;
    }

    error = probe->ops.prepare(probe->ops.context, &config);
    if (error != 0) {
        return error;
    }
    config.lun = MT6897_UFS_PROBE_LUN;
    error = dufs_bind(host, &config);
    if (error == 0) {
        error = dufs_start(host);
    }
    if (error == 0) {
        error = dufs_nop(host);
    }
    if (error == 0) {
        error = dufs_device_init(host);
    }
    if (error == 0) {
        error = dufs_capacity(host, &blocks, &block_bytes);
    }
    if (error != 0) {
        return error;
    }
    if (blocks <= MT6897_UFS_PROBE_LBA || block_bytes != MT6897_UFS_PROBE_BYTES) {
        return DUFS_RESPONSE;
    }
    error = dufs_read(host, MT6897_UFS_PROBE_LBA, 1, probe->block,
        sizeof(probe->block));
    if (error == 0) {
        *result = block_bytes;
    }
    return error;
}

enum mt6897_ufs_provider_result
mt6897_ufs_probe_bind(struct mt6897_ufs_probe *probe,
    struct mt6897_ufs_gate *gate, const struct mt6897_ufs_gate_lease *lease,
    struct dufs_host *host, const struct mt6897_ufs_probe_ops *ops,
    uint64_t *blockers_out)
{
    enum mt6897_ufs_provider_result result;

    if (probe == 0 || host == 0 || ops == 0 || ops->prepare == 0) {
        return MT6897_UFS_PROVIDER_ARGUMENT;
    }
    if (probe->host != 0 || probe->attempted != 0 || host->state != 0) {
        return MT6897_UFS_PROVIDER_STATE;
    }
    const struct mt6897_ufs_provider_ops provider_ops = { probe, probe_dispatch };
    probe->host = host;
    probe->ops = *ops;
    result = mt6897_ufs_provider_bind(&probe->provider, gate, lease,
        &provider_ops, blockers_out);
    if (result != MT6897_UFS_PROVIDER_OK) {
        probe->host = 0;
        probe->ops = (struct mt6897_ufs_probe_ops){ 0 };
    }
    return result;
}

enum mt6897_ufs_provider_result
mt6897_ufs_probe_read(struct mt6897_ufs_probe *probe, void *destination,
    size_t bytes, uint64_t *blockers_out)
{
    uint32_t unused = 0;
    uint64_t result = 0;
    enum mt6897_ufs_provider_result status;

    if (probe == 0 || destination == 0 || bytes != MT6897_UFS_PROBE_BYTES ||
        blockers_out == 0) {
        return MT6897_UFS_PROVIDER_ARGUMENT;
    }
    if (!__atomic_compare_exchange_n(&probe->attempted, &unused, 1, 0,
        __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) {
        return MT6897_UFS_PROVIDER_STATE;
    }
    status = mt6897_ufs_provider_command(&probe->provider, SCSI_READ_16,
        MT6897_UFS_PROBE_LUN, MT6897_UFS_PROBE_LBA, 1, &result, blockers_out);
    if (status != MT6897_UFS_PROVIDER_OK) {
        return status;
    }
    if (result != bytes) {
        return mt6897_ufs_provider_fault(&probe->provider,
            MT6897_UFS_BLOCK_PROVIDER_RUNTIME, blockers_out);
    }

    uint8_t *output = destination;
    for (size_t i = 0; i < bytes; ++i) {
        output[i] = probe->block[i];
    }
    return MT6897_UFS_PROVIDER_OK;
}
