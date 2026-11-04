// SPDX-License-Identifier: GPL-2.0-only
/*
 * Passive UFS PRDT observer v3 for POCO X6 Pro (duchamp).
 *
 * This version preserves the v2 observer and adds a bounded snapshot of the
 * live dma_range_map, direct DMA-vs-physical comparisons, and SWIOTLB state.
 * It observes existing UFS mappings only. It never starts storage I/O, maps
 * DMA, touches MMIO, invokes firmware, or changes an IOMMU domain.
 */

#include <linux/dma-direct.h>
#include <linux/dma-map-ops.h>
#include <linux/errno.h>
#include <linux/iommu.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_platform.h>
#include <linux/overflow.h>
#include <linux/scatterlist.h>
#include <linux/spinlock.h>
#include <linux/swiotlb.h>
#include <linux/sysfs.h>
#include <linux/tracepoint.h>
#include <scsi/scsi_cmnd.h>
#include <trace/hooks/ufshcd.h>
#include <ufs/ufshcd.h>

#define DUCHAMP_UFS_COMPATIBLE "mediatek,mt8183-ufshci"
#define DUCHAMP_UFS_DMA_LIMIT 0x0000000fffffffffULL
#define DUCHAMP_MAX_PRDT_SEGMENTS SG_ALL
#define DUCHAMP_MAX_PRDT_ENTRY_SIZE 4096U
#define DUCHAMP_DMA_RANGE_COUNT 1U

struct duchamp_dma_contract_snapshot {
	const struct bus_dma_region *map;
	struct io_tlb_mem *swiotlb;
	u64 cpu_start;
	u64 dma_start;
	u64 size;
	u64 offset;
	u64 bus_dma_limit;
	unsigned long swiotlb_nslabs;
	bool map_identity;
	bool swiotlb_force_bounce;
	bool valid;
};

struct duchamp_prdt_stats_v3 {
	u64 hook_calls;
	u64 target_calls;
	u64 rejected_calls;
	u64 commands;
	u64 segments;
	u64 read_commands;
	u64 write_commands;
	u64 bidirectional_commands;
	u64 unknown_direction_commands;
	u64 hook_error_calls;
	u64 zero_length_segments;
	u64 dma_end_overflows;
	u64 translated_phys_invalid;
	u64 original_phys_end_overflows;
	u64 expected_dma_invalid;
	u64 prdt_address_mismatches;
	u64 prdt_length_mismatches;
	u64 swiotlb_segments;
	u64 raw_dma_phys_matches;
	u64 raw_dma_phys_mismatches;
	u64 phys_to_dma_matches;
	u64 phys_to_dma_mismatches;
	u64 dma_to_phys_matches;
	u64 dma_to_phys_mismatches;
	u64 above_4g_segments;
	u64 outside_bus_limit_segments;
	u64 runtime_contract_changes;
	u64 min_dma_address;
	u64 max_dma_end;
	u64 min_original_phys;
	u64 max_original_phys_end;
	u64 max_segment_length;
};

static DEFINE_SPINLOCK(duchamp_stats_lock);
static struct duchamp_prdt_stats_v3 duchamp_stats = {
	.min_dma_address = U64_MAX,
	.min_original_phys = U64_MAX,
};

static struct duchamp_dma_contract_snapshot duchamp_dma_contract;
static struct device *duchamp_ufs_dev;

static bool duchamp_direct_contract_matches(struct device *dev)
{
	struct iommu_fwspec *fwspec;
	u64 *mask;

	mask = READ_ONCE(dev->dma_mask);
	if (!mask || READ_ONCE(*mask) != U64_MAX ||
	    READ_ONCE(dev->coherent_dma_mask) != U64_MAX ||
	    READ_ONCE(dev->bus_dma_limit) != DUCHAMP_UFS_DMA_LIMIT ||
	    !READ_ONCE(dev->dma_range_map) || dev_is_dma_coherent(dev) ||
	    get_dma_ops(dev) || READ_ONCE(dev->iommu) ||
	    READ_ONCE(dev->iommu_group))
		return false;
#ifdef CONFIG_DMA_OPS
	if (READ_ONCE(dev->dma_ops))
		return false;
#endif
#ifdef CONFIG_DMA_OPS_BYPASS
	if (READ_ONCE(dev->dma_ops_bypass))
		return false;
#endif
#ifdef CONFIG_SWIOTLB
	if (!READ_ONCE(dev->dma_io_tlb_mem))
		return false;
#endif
	fwspec = dev_iommu_fwspec_get(dev);
	if (fwspec || iommu_get_domain_for_dev(dev))
		return false;
	return true;
}

static int duchamp_capture_dma_contract(struct device *dev)
{
	const struct bus_dma_region *map;
	struct io_tlb_mem *swiotlb;
	u64 cpu_end;
	u64 dma_end;
	u64 cpu_start;
	u64 dma_start;
	u64 size;
	u64 offset;

	map = READ_ONCE(dev->dma_range_map);
	if (!map)
		return -ENODEV;

	cpu_start = (u64)READ_ONCE(map[0].cpu_start);
	dma_start = (u64)READ_ONCE(map[0].dma_start);
	size = READ_ONCE(map[0].size);
	offset = READ_ONCE(map[0].offset);
	if (!size || READ_ONCE(map[DUCHAMP_DMA_RANGE_COUNT].size))
		return -ERANGE;
	if (check_add_overflow(cpu_start, size - 1, &cpu_end) ||
	    check_add_overflow(dma_start, size - 1, &dma_end))
		return -EOVERFLOW;
	if (cpu_start - dma_start != offset)
		return -ERANGE;

	swiotlb = READ_ONCE(dev->dma_io_tlb_mem);
	if (!swiotlb)
		return -ENODEV;

	duchamp_dma_contract.map = map;
	duchamp_dma_contract.swiotlb = swiotlb;
	duchamp_dma_contract.cpu_start = cpu_start;
	duchamp_dma_contract.dma_start = dma_start;
	duchamp_dma_contract.size = size;
	duchamp_dma_contract.offset = offset;
	duchamp_dma_contract.bus_dma_limit = READ_ONCE(dev->bus_dma_limit);
	duchamp_dma_contract.swiotlb_nslabs = READ_ONCE(swiotlb->nslabs);
	duchamp_dma_contract.swiotlb_force_bounce =
		READ_ONCE(swiotlb->force_bounce);
	duchamp_dma_contract.map_identity = cpu_start == dma_start && !offset;
	duchamp_dma_contract.valid = true;
	return 0;
}

static bool duchamp_dma_contract_stable(struct device *dev)
{
	const struct bus_dma_region *map;
	struct io_tlb_mem *swiotlb;
	u64 *mask;

	if (!READ_ONCE(duchamp_dma_contract.valid))
		return false;
	mask = READ_ONCE(dev->dma_mask);
	if (!mask || READ_ONCE(*mask) != U64_MAX ||
	    READ_ONCE(dev->coherent_dma_mask) != U64_MAX ||
	    dev_is_dma_coherent(dev) || get_dma_ops(dev) ||
	    READ_ONCE(dev->iommu) || READ_ONCE(dev->iommu_group) ||
	    dev_iommu_fwspec_get(dev))
		return false;
#ifdef CONFIG_DMA_OPS
	if (READ_ONCE(dev->dma_ops))
		return false;
#endif
#ifdef CONFIG_DMA_OPS_BYPASS
	if (READ_ONCE(dev->dma_ops_bypass))
		return false;
#endif
	map = READ_ONCE(dev->dma_range_map);
	swiotlb = READ_ONCE(dev->dma_io_tlb_mem);
	if (map != duchamp_dma_contract.map ||
	    swiotlb != duchamp_dma_contract.swiotlb)
		return false;
	return (u64)READ_ONCE(map[0].cpu_start) ==
			duchamp_dma_contract.cpu_start &&
		(u64)READ_ONCE(map[0].dma_start) ==
			duchamp_dma_contract.dma_start &&
		READ_ONCE(map[0].size) == duchamp_dma_contract.size &&
		READ_ONCE(map[0].offset) == duchamp_dma_contract.offset &&
		!READ_ONCE(map[DUCHAMP_DMA_RANGE_COUNT].size) &&
		READ_ONCE(dev->bus_dma_limit) ==
			duchamp_dma_contract.bus_dma_limit &&
		READ_ONCE(swiotlb->nslabs) ==
			duchamp_dma_contract.swiotlb_nslabs &&
		READ_ONCE(swiotlb->force_bounce) ==
			duchamp_dma_contract.swiotlb_force_bounce;
}

static void duchamp_count_direction(struct duchamp_prdt_stats_v3 *stats,
				    enum dma_data_direction direction)
{
	switch (direction) {
	case DMA_FROM_DEVICE:
		stats->read_commands++;
		break;
	case DMA_TO_DEVICE:
		stats->write_commands++;
		break;
	case DMA_BIDIRECTIONAL:
		stats->bidirectional_commands++;
		break;
	default:
		stats->unknown_direction_commands++;
		break;
	}
}

static void duchamp_merge_stats(const struct duchamp_prdt_stats_v3 *update)
{
	unsigned long flags;

	spin_lock_irqsave(&duchamp_stats_lock, flags);
	duchamp_stats.hook_calls += update->hook_calls;
	duchamp_stats.target_calls += update->target_calls;
	duchamp_stats.rejected_calls += update->rejected_calls;
	duchamp_stats.commands += update->commands;
	duchamp_stats.segments += update->segments;
	duchamp_stats.read_commands += update->read_commands;
	duchamp_stats.write_commands += update->write_commands;
	duchamp_stats.bidirectional_commands += update->bidirectional_commands;
	duchamp_stats.unknown_direction_commands +=
		update->unknown_direction_commands;
	duchamp_stats.hook_error_calls += update->hook_error_calls;
	duchamp_stats.zero_length_segments += update->zero_length_segments;
	duchamp_stats.dma_end_overflows += update->dma_end_overflows;
	duchamp_stats.translated_phys_invalid +=
		update->translated_phys_invalid;
	duchamp_stats.original_phys_end_overflows +=
		update->original_phys_end_overflows;
	duchamp_stats.expected_dma_invalid += update->expected_dma_invalid;
	duchamp_stats.prdt_address_mismatches +=
		update->prdt_address_mismatches;
	duchamp_stats.prdt_length_mismatches +=
		update->prdt_length_mismatches;
	duchamp_stats.swiotlb_segments += update->swiotlb_segments;
	duchamp_stats.raw_dma_phys_matches += update->raw_dma_phys_matches;
	duchamp_stats.raw_dma_phys_mismatches +=
		update->raw_dma_phys_mismatches;
	duchamp_stats.phys_to_dma_matches += update->phys_to_dma_matches;
	duchamp_stats.phys_to_dma_mismatches +=
		update->phys_to_dma_mismatches;
	duchamp_stats.dma_to_phys_matches += update->dma_to_phys_matches;
	duchamp_stats.dma_to_phys_mismatches +=
		update->dma_to_phys_mismatches;
	duchamp_stats.above_4g_segments += update->above_4g_segments;
	duchamp_stats.outside_bus_limit_segments +=
		update->outside_bus_limit_segments;
	duchamp_stats.runtime_contract_changes +=
		update->runtime_contract_changes;
	if (update->min_dma_address != U64_MAX)
		duchamp_stats.min_dma_address =
			min(duchamp_stats.min_dma_address,
			    update->min_dma_address);
	duchamp_stats.max_dma_end = max(duchamp_stats.max_dma_end,
					update->max_dma_end);
	if (update->min_original_phys != U64_MAX)
		duchamp_stats.min_original_phys =
			min(duchamp_stats.min_original_phys,
			    update->min_original_phys);
	duchamp_stats.max_original_phys_end =
		max(duchamp_stats.max_original_phys_end,
		    update->max_original_phys_end);
	duchamp_stats.max_segment_length =
		max(duchamp_stats.max_segment_length,
		    update->max_segment_length);
	spin_unlock_irqrestore(&duchamp_stats_lock, flags);
}

static void duchamp_observe_ufs_prdt_v3(void *unused, struct ufs_hba *hba,
					struct ufshcd_lrb *lrbp,
					unsigned int segments, int *err)
{
	struct duchamp_prdt_stats_v3 update = {
		.hook_calls = 1,
		.min_dma_address = U64_MAX,
		.min_original_phys = U64_MAX,
	};
	struct scsi_cmnd *cmd;
	struct scatterlist *sg_list;
	struct scatterlist *sg;
	size_t entry_size;
	u64 bus_limit;
	unsigned int i;

	(void)unused;
	if (!hba || !hba->dev || hba->dev != READ_ONCE(duchamp_ufs_dev))
		goto merge;
	update.target_calls = 1;
	if (err && READ_ONCE(*err))
		update.hook_error_calls = 1;
	if (!duchamp_dma_contract_stable(hba->dev)) {
		update.runtime_contract_changes = 1;
		update.rejected_calls = 1;
		goto merge;
	}
	if (!hba->host || !lrbp || !lrbp->cmd || !lrbp->ucd_prdt_ptr ||
	    !segments || segments > DUCHAMP_MAX_PRDT_SEGMENTS ||
	    segments > READ_ONCE(hba->host->sg_tablesize)) {
		update.rejected_calls = 1;
		goto merge;
	}
	entry_size = ufshcd_sg_entry_size(hba);
	if (entry_size < sizeof(struct ufshcd_sg_entry) ||
	    entry_size > DUCHAMP_MAX_PRDT_ENTRY_SIZE) {
		update.rejected_calls = 1;
		goto merge;
	}
	cmd = lrbp->cmd;
	sg_list = scsi_sglist(cmd);
	if (!sg_list) {
		update.rejected_calls = 1;
		goto merge;
	}
	bus_limit = READ_ONCE(hba->dev->bus_dma_limit);
	update.commands = 1;
	duchamp_count_direction(&update, cmd->sc_data_direction);

	for_each_sg(sg_list, sg, segments, i) {
		struct ufshcd_sg_entry *prd;
		phys_addr_t original_phys;
		phys_addr_t translated_phys;
		dma_addr_t dma_address;
		dma_addr_t expected_dma;
		u64 dma_end;
		u64 original_end;
		u64 length;
		u64 prdt_address;
		u64 prdt_length;

		update.segments++;
		dma_address = sg_dma_address(sg);
		length = sg_dma_len(sg);
		if (!length) {
			update.zero_length_segments++;
			continue;
		}
		prd = (struct ufshcd_sg_entry *)
			((u8 *)lrbp->ucd_prdt_ptr + i * entry_size);
		prdt_address = le64_to_cpu(READ_ONCE(prd->addr));
		prdt_length = (u64)le32_to_cpu(READ_ONCE(prd->size)) + 1;
		if (prdt_address != (u64)dma_address)
			update.prdt_address_mismatches++;
		if (prdt_length != length)
			update.prdt_length_mismatches++;

		if (check_add_overflow((u64)dma_address, length - 1,
				       &dma_end)) {
			update.dma_end_overflows++;
			continue;
		}
		original_phys = sg_phys(sg);
		if (check_add_overflow((u64)original_phys, length - 1,
				       &original_end)) {
			update.original_phys_end_overflows++;
			continue;
		}
		update.min_dma_address = min(update.min_dma_address,
					     (u64)dma_address);
		update.max_dma_end = max(update.max_dma_end, dma_end);
		update.min_original_phys = min_t(u64, update.min_original_phys,
						 (u64)original_phys);
		update.max_original_phys_end =
			max(update.max_original_phys_end, original_end);
		update.max_segment_length =
			max(update.max_segment_length, length);

		if ((u64)dma_address == (u64)original_phys)
			update.raw_dma_phys_matches++;
		else
			update.raw_dma_phys_mismatches++;
		expected_dma = phys_to_dma(hba->dev, original_phys);
		if (expected_dma == DMA_MAPPING_ERROR)
			update.expected_dma_invalid++;
		else if (expected_dma == dma_address)
			update.phys_to_dma_matches++;
		else
			update.phys_to_dma_mismatches++;
		translated_phys = dma_to_phys(hba->dev, dma_address);
		if (translated_phys == (phys_addr_t)-1)
			update.translated_phys_invalid++;
		else if (translated_phys == original_phys)
			update.dma_to_phys_matches++;
		else
			update.dma_to_phys_mismatches++;
		if (translated_phys != (phys_addr_t)-1 &&
		    is_swiotlb_buffer(hba->dev, translated_phys))
			update.swiotlb_segments++;

		if (dma_end > U32_MAX)
			update.above_4g_segments++;
		if (!bus_limit || (u64)dma_address > bus_limit ||
		    length - 1 > bus_limit - (u64)dma_address)
			update.outside_bus_limit_segments++;
	}
merge:
	duchamp_merge_stats(&update);
}

static u64 duchamp_min_or_zero(u64 value)
{
	return value == U64_MAX ? 0 : value;
}

static ssize_t sweet_ufs_prdt_observation_v3_show(struct device *dev,
						  struct device_attribute *attr,
						  char *buf)
{
	struct duchamp_prdt_stats_v3 snapshot;
	unsigned long flags;
	bool contract_stable;
	bool complete;
	bool raw_identity;
	bool direct_identity;

	(void)attr;
	spin_lock_irqsave(&duchamp_stats_lock, flags);
	snapshot = duchamp_stats;
	spin_unlock_irqrestore(&duchamp_stats_lock, flags);
	contract_stable = duchamp_direct_contract_matches(dev) &&
		duchamp_dma_contract_stable(dev);
	complete = snapshot.segments > 0 && contract_stable &&
		!snapshot.rejected_calls && !snapshot.hook_error_calls &&
		!snapshot.unknown_direction_commands &&
		!snapshot.zero_length_segments && !snapshot.dma_end_overflows &&
		!snapshot.translated_phys_invalid &&
		!snapshot.original_phys_end_overflows &&
		!snapshot.expected_dma_invalid &&
		!snapshot.prdt_address_mismatches &&
		!snapshot.prdt_length_mismatches &&
		!snapshot.outside_bus_limit_segments &&
		!snapshot.runtime_contract_changes &&
		snapshot.raw_dma_phys_matches +
			snapshot.raw_dma_phys_mismatches == snapshot.segments &&
		snapshot.phys_to_dma_matches +
			snapshot.phys_to_dma_mismatches == snapshot.segments &&
		snapshot.dma_to_phys_matches +
			snapshot.dma_to_phys_mismatches == snapshot.segments;
	raw_identity = complete &&
		snapshot.raw_dma_phys_matches == snapshot.segments &&
		!snapshot.raw_dma_phys_mismatches;
	direct_identity = raw_identity && duchamp_dma_contract.map_identity &&
		!snapshot.swiotlb_segments &&
		snapshot.phys_to_dma_matches == snapshot.segments &&
		!snapshot.phys_to_dma_mismatches &&
		snapshot.dma_to_phys_matches == snapshot.segments &&
		!snapshot.dma_to_phys_mismatches;

	return sysfs_emit(buf,
		"observation_version=3\n"
		"root_read_only=1\n"
		"coherent_snapshot=1\n"
		"runtime_direct_dma_contract=%u\n"
		"dma_range_count=%u\n"
		"dma_range_terminated=1\n"
		"dma_range_cpu_start=0x%016llx\n"
		"dma_range_dma_start=0x%016llx\n"
		"dma_range_size=0x%016llx\n"
		"dma_range_offset=0x%016llx\n"
		"dma_range_identity=%u\n"
		"dma_range_stable=%u\n"
		"swiotlb_pool_present=1\n"
		"swiotlb_pool_active=%u\n"
		"swiotlb_force_bounce=%u\n"
		"hook_calls=%llu\n"
		"target_calls=%llu\n"
		"rejected_calls=%llu\n"
		"commands=%llu\n"
		"segments=%llu\n"
		"read_commands=%llu\n"
		"write_commands=%llu\n"
		"bidirectional_commands=%llu\n"
		"unknown_direction_commands=%llu\n"
		"hook_error_calls=%llu\n"
		"zero_length_segments=%llu\n"
		"dma_end_overflows=%llu\n"
		"translated_phys_invalid=%llu\n"
		"original_phys_end_overflows=%llu\n"
		"expected_dma_invalid=%llu\n"
		"prdt_address_mismatches=%llu\n"
		"prdt_length_mismatches=%llu\n"
		"swiotlb_segments=%llu\n"
		"raw_dma_phys_matches=%llu\n"
		"raw_dma_phys_mismatches=%llu\n"
		"phys_to_dma_matches=%llu\n"
		"phys_to_dma_mismatches=%llu\n"
		"dma_to_phys_matches=%llu\n"
		"dma_to_phys_mismatches=%llu\n"
		"above_4g_segments=%llu\n"
		"outside_bus_limit_segments=%llu\n"
		"runtime_contract_changes=%llu\n"
		"min_dma_address=0x%016llx\n"
		"max_dma_end=0x%016llx\n"
		"min_original_phys=0x%016llx\n"
		"max_original_phys_end=0x%016llx\n"
		"max_segment_length=%llu\n"
		"runtime_bus_dma_limit=0x%016llx\n"
		"observation_complete=%u\n"
		"all_prdt_entries_match=%u\n"
		"all_raw_dma_equals_original_phys=%u\n"
		"all_phys_to_dma_matches=%u\n"
		"all_dma_to_phys_matches=%u\n"
		"no_swiotlb_observed=%u\n"
		"observed_direct_identity_route=%u\n",
		contract_stable,
		DUCHAMP_DMA_RANGE_COUNT,
		duchamp_dma_contract.cpu_start,
		duchamp_dma_contract.dma_start,
		duchamp_dma_contract.size,
		duchamp_dma_contract.offset,
		duchamp_dma_contract.map_identity,
		contract_stable,
		duchamp_dma_contract.swiotlb_nslabs > 0,
		duchamp_dma_contract.swiotlb_force_bounce,
		snapshot.hook_calls,
		snapshot.target_calls,
		snapshot.rejected_calls,
		snapshot.commands,
		snapshot.segments,
		snapshot.read_commands,
		snapshot.write_commands,
		snapshot.bidirectional_commands,
		snapshot.unknown_direction_commands,
		snapshot.hook_error_calls,
		snapshot.zero_length_segments,
		snapshot.dma_end_overflows,
		snapshot.translated_phys_invalid,
		snapshot.original_phys_end_overflows,
		snapshot.expected_dma_invalid,
		snapshot.prdt_address_mismatches,
		snapshot.prdt_length_mismatches,
		snapshot.swiotlb_segments,
		snapshot.raw_dma_phys_matches,
		snapshot.raw_dma_phys_mismatches,
		snapshot.phys_to_dma_matches,
		snapshot.phys_to_dma_mismatches,
		snapshot.dma_to_phys_matches,
		snapshot.dma_to_phys_mismatches,
		snapshot.above_4g_segments,
		snapshot.outside_bus_limit_segments,
		snapshot.runtime_contract_changes,
		duchamp_min_or_zero(snapshot.min_dma_address),
		snapshot.max_dma_end,
		duchamp_min_or_zero(snapshot.min_original_phys),
		snapshot.max_original_phys_end,
		snapshot.max_segment_length,
		READ_ONCE(dev->bus_dma_limit),
		complete,
		complete,
		raw_identity,
		complete && snapshot.phys_to_dma_matches == snapshot.segments &&
			!snapshot.phys_to_dma_mismatches,
		complete && snapshot.dma_to_phys_matches == snapshot.segments &&
			!snapshot.dma_to_phys_mismatches,
		complete && !snapshot.swiotlb_segments,
		direct_identity);
}

static DEVICE_ATTR(sweet_ufs_prdt_observation_v3, 0400,
		   sweet_ufs_prdt_observation_v3_show, NULL);

static int __init duchamp_ufs_prdt_observer_v3_init(void)
{
	struct platform_device *pdev;
	struct device_node *node;
	int error;

	node = of_find_compatible_node(NULL, NULL, DUCHAMP_UFS_COMPATIBLE);
	if (!node)
		return -ENODEV;
	pdev = of_find_device_by_node(node);
	of_node_put(node);
	if (!pdev)
		return -ENODEV;
	duchamp_ufs_dev = &pdev->dev;
	if (!duchamp_direct_contract_matches(duchamp_ufs_dev)) {
		error = -EXDEV;
		goto put_device;
	}
	error = duchamp_capture_dma_contract(duchamp_ufs_dev);
	if (error)
		goto put_device;
	error = register_trace_android_vh_ufs_fill_prdt(duchamp_observe_ufs_prdt_v3,
							NULL);
	if (error)
		goto put_device;
	error = device_create_file(duchamp_ufs_dev,
				   &dev_attr_sweet_ufs_prdt_observation_v3);
	if (error)
		goto unregister_hook;
	return 0;

unregister_hook:
	unregister_trace_android_vh_ufs_fill_prdt(duchamp_observe_ufs_prdt_v3,
						  NULL);
	tracepoint_synchronize_unregister();
put_device:
	WRITE_ONCE(duchamp_dma_contract.valid, false);
	put_device(duchamp_ufs_dev);
	duchamp_ufs_dev = NULL;
	return error;
}

static void __exit duchamp_ufs_prdt_observer_v3_exit(void)
{
	if (!duchamp_ufs_dev)
		return;
	device_remove_file(duchamp_ufs_dev,
			   &dev_attr_sweet_ufs_prdt_observation_v3);
	unregister_trace_android_vh_ufs_fill_prdt(duchamp_observe_ufs_prdt_v3,
						  NULL);
	tracepoint_synchronize_unregister();
	WRITE_ONCE(duchamp_dma_contract.valid, false);
	put_device(duchamp_ufs_dev);
	duchamp_ufs_dev = NULL;
}

module_init(duchamp_ufs_prdt_observer_v3_init);
module_exit(duchamp_ufs_prdt_observer_v3_exit);

MODULE_DESCRIPTION("Passive Duchamp UFS PRDT DMA observer v3");
MODULE_AUTHOR("ios-sweet Duchamp port");
MODULE_LICENSE("GPL v2");
MODULE_INFO(target_device, "duchamp");
MODULE_INFO(target_soc, "mt6897");
MODULE_INFO(target_kernel,
	    "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407");
MODULE_INFO(observation_mode, "existing-io-only");
