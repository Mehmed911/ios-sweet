// SPDX-License-Identifier: GPL-2.0-only
/*
 * Read-only DMA/IOMMU contract probe for POCO X6 Pro (duchamp).
 *
 * The module performs no DMA allocation or mapping, MMIO, SMC, IOMMU attach,
 * firmware call, power transition, or storage I/O. It adds one read-only
 * sysfs attribute to the already-bound UFS platform device and removes it on
 * unload. No kernel pointer value is exposed.
 */

#include <linux/dma-map-ops.h>
#include <linux/iommu.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_platform.h>
#include <linux/platform_device.h>
#include <linux/sysfs.h>

#define DUCHAMP_UFS_COMPATIBLE "mediatek,mt8183-ufshci"

static struct device *duchamp_ufs_dev;

static unsigned int duchamp_mask_bits(u64 mask)
{
	unsigned int bits = 0;

	while (mask) {
		bits++;
		mask >>= 1;
	}

	return bits;
}

static ssize_t sweet_dma_iommu_contract_show(struct device *dev,
					     struct device_attribute *attr,
					     char *buf)
{
	const struct dma_map_ops *ops;
	struct iommu_fwspec *fwspec;
	struct iommu_domain *domain;
	u64 streaming_mask = 0;
	u64 coherent_mask;
	u64 bus_limit;
	u64 *mask;
	unsigned int fwspec_num_ids = 0;
	unsigned int fwspec_first_id = 0;
	unsigned int fwspec_last_id = 0;
	unsigned int domain_type = 0;
	bool fwspec_ops_present = false;
	bool fwspec_fwnode_present = false;
	bool domain_is_dma = false;
	bool device_dma_ops_present = false;
	bool dma_ops_bypass_supported = false;
	bool dma_ops_bypass = false;
	bool swiotlb_pool_present = false;

	mask = READ_ONCE(dev->dma_mask);
	if (mask)
		streaming_mask = READ_ONCE(*mask);
	coherent_mask = READ_ONCE(dev->coherent_dma_mask);
	bus_limit = READ_ONCE(dev->bus_dma_limit);
	ops = get_dma_ops(dev);
#ifdef CONFIG_DMA_OPS
	device_dma_ops_present = READ_ONCE(dev->dma_ops) != NULL;
#endif
#ifdef CONFIG_DMA_OPS_BYPASS
	dma_ops_bypass_supported = true;
	dma_ops_bypass = dev->dma_ops_bypass;
#endif
#ifdef CONFIG_SWIOTLB
	swiotlb_pool_present = READ_ONCE(dev->dma_io_tlb_mem) != NULL;
#endif

	fwspec = dev_iommu_fwspec_get(dev);
	if (fwspec) {
		fwspec_ops_present = READ_ONCE(fwspec->ops) != NULL;
		fwspec_fwnode_present = READ_ONCE(fwspec->iommu_fwnode) != NULL;
		fwspec_num_ids = READ_ONCE(fwspec->num_ids);
		if (fwspec_num_ids) {
			fwspec_first_id = READ_ONCE(fwspec->ids[0]);
			fwspec_last_id = READ_ONCE(fwspec->ids[fwspec_num_ids - 1]);
		}
	}

	domain = iommu_get_domain_for_dev(dev);
	if (domain) {
		domain_type = READ_ONCE(domain->type);
		domain_is_dma = iommu_is_dma_domain(domain);
	}

	return sysfs_emit(buf,
		"contract_version=1\n"
		"streaming_mask_pointer_present=%u\n"
		"streaming_dma_mask=0x%016llx\n"
		"streaming_dma_mask_bits=%u\n"
		"coherent_dma_mask=0x%016llx\n"
		"coherent_dma_mask_bits=%u\n"
		"bus_dma_limit=0x%016llx\n"
		"dma_mask_is_coherent_mask=%u\n"
		"dma_range_map_present=%u\n"
		"dma_coherent=%u\n"
		"dma_ops_present=%u\n"
		"device_dma_ops_present=%u\n"
		"dma_ops_bypass_supported=%u\n"
		"dma_ops_bypass=%u\n"
		"swiotlb_pool_present=%u\n"
		"iommu_private_present=%u\n"
		"iommu_group_present=%u\n"
		"iommu_fwspec_present=%u\n"
		"iommu_fwspec_ops_present=%u\n"
		"iommu_fwspec_fwnode_present=%u\n"
		"iommu_fwspec_num_ids=%u\n"
		"iommu_fwspec_first_id=%u\n"
		"iommu_fwspec_last_id=%u\n"
		"iommu_domain_present=%u\n"
		"iommu_domain_type=%u\n"
		"iommu_domain_is_dma=%u\n",
		mask != NULL,
		streaming_mask,
		duchamp_mask_bits(streaming_mask),
		coherent_mask,
		duchamp_mask_bits(coherent_mask),
		bus_limit,
		mask == &dev->coherent_dma_mask,
		READ_ONCE(dev->dma_range_map) != NULL,
		dev_is_dma_coherent(dev),
		ops != NULL,
		device_dma_ops_present,
		dma_ops_bypass_supported,
		dma_ops_bypass,
		swiotlb_pool_present,
		READ_ONCE(dev->iommu) != NULL,
		READ_ONCE(dev->iommu_group) != NULL,
		fwspec != NULL,
		fwspec_ops_present,
		fwspec_fwnode_present,
		fwspec_num_ids,
		fwspec_first_id,
		fwspec_last_id,
		domain != NULL,
		domain_type,
		domain_is_dma);
}

static DEVICE_ATTR_RO(sweet_dma_iommu_contract);

static int __init duchamp_dma_iommu_probe_init(void)
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
	error = device_create_file(duchamp_ufs_dev,
				   &dev_attr_sweet_dma_iommu_contract);
	if (error) {
		put_device(duchamp_ufs_dev);
		duchamp_ufs_dev = NULL;
	}
	return error;
}

static void __exit duchamp_dma_iommu_probe_exit(void)
{
	if (!duchamp_ufs_dev)
		return;
	device_remove_file(duchamp_ufs_dev,
			   &dev_attr_sweet_dma_iommu_contract);
	put_device(duchamp_ufs_dev);
	duchamp_ufs_dev = NULL;
}

module_init(duchamp_dma_iommu_probe_init);
module_exit(duchamp_dma_iommu_probe_exit);

MODULE_DESCRIPTION("Read-only Duchamp UFS DMA/IOMMU contract probe");
MODULE_AUTHOR("ios-sweet Duchamp port");
MODULE_LICENSE("GPL v2");
MODULE_INFO(target_device, "duchamp");
MODULE_INFO(target_soc, "mt6897");
MODULE_INFO(target_kernel,
	    "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407");
