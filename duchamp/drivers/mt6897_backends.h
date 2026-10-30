#ifndef MT6897_BACKENDS_H
#define MT6897_BACKENDS_H
#include <stddef.h>
#include <stdint.h>
enum mb_result { MB_OK=0,MB_ARGUMENT=-1,MB_UNVERIFIED=-2,MB_STATE=-3,
                 MB_IO=-4,MB_TIMEOUT=-5,MB_BUSY=-6,MB_RANGE=-7 };
enum mb_resource { MB_PMIF=1,MB_DISP_IOMMU=2,MB_MDP_IOMMU=3 };
struct mb_io {
    void *context;
    /* Positive authorization covers matched resources, clocks/power, secure
     * ownership and serialization. No physical mappings are supplied here.
     */
    int (*authorise)(void *,unsigned resource);
    int (*read32)(void *,unsigned bank,uint32_t offset,uint32_t *);
    int (*write32)(void *,unsigned bank,uint32_t offset,uint32_t);
    void (*barrier)(void *);
    uint64_t (*microseconds)(void *);
    int (*delay_us)(void *,uint32_t);
};
struct mb_pmif { struct mb_io io; unsigned state; };
/* Matched mt6897/mt6xxx SWINF2, saved DTB route mask=0 (SPMI-M). The
 * initialized PMIF/controller and clocks remain a provider precondition.
 */
int mb_pmif_bind(struct mb_pmif *,const struct mb_io *,uint32_t route_mask);
int mb_pmif_transfer(struct mb_pmif *,unsigned sid,uint32_t address,
                     void *bytes,size_t count,int write);
struct mb_pmic_ops {
    void *context;
    int (*authorise)(void *,unsigned rail,int write);
    int (*lock)(void *);
    void (*unlock)(void *);
    int (*read)(void *,unsigned sid,uint16_t address,void *,size_t);
    int (*write)(void *,unsigned sid,uint16_t address,const void *,size_t);
    int (*delay_us)(void *,uint32_t);
};
enum mb_rail { MB_VEMC=0,MB_VBUCK3=1 };
struct mb_pmic { struct mb_pmic_ops ops; unsigned state; };
int mb_pmic_bind(struct mb_pmic *,const struct mb_pmic_ops *);
int mb_pmic_voltage(struct mb_pmic *,unsigned rail,uint32_t microvolts);
int mb_pmic_enable(struct mb_pmic *,unsigned rail);
/* No disable, global probe/shutdown, mode changes or guessed voltage target.
 * VEMC fine trim is preserved. Output/readback is not measured rail voltage.
 */
struct mb_fw_ops {
    void *context;
    int (*authorise)(void *,const uint64_t request[8]);
    int (*conduit)(void *,const uint64_t request[8],uint64_t reply[4]);
    int (*verify_reply)(void *,const uint64_t request[8],const uint64_t reply[4]);
};
struct mb_firmware { struct mb_fw_ops ops; uint64_t last_reply[4]; unsigned state; };
int mb_firmware_bind(struct mb_firmware *,const struct mb_fw_ops *);
int mb_firmware_ufs(struct mb_firmware *,const uint64_t request[8],uint64_t reply[4]);
/* Raw AArch64 SMCCC transport. Only a trusted authorized provider may use it.
 * It is never installed by default. Requires the firmware's SMCCC register-
 * preservation contract. Local tests use a separate QEMU EL3 monitor.
 */
void mb_smc_raw(const uint64_t request[8],uint64_t reply[4]);
enum mb_iommu_client { MB_CLIENT_UNVERIFIED_UFS=0,MB_CLIENT_DISP=1,MB_CLIENT_MDP=2 };
struct mb_iommu {
    struct mb_io io;
    uint64_t iova_begin,iova_end;
    unsigned client,state;
};
int mb_iommu_bind(struct mb_iommu *,const struct mb_io *,unsigned client,
                  uint64_t aperture_begin,uint64_t aperture_end);
/* Register programming for an already powered/configured, exclusively owned,
 * quiescent normal domain. encoded_ttbr MUST come from a matched ARM_V7S/
 * MTK_TTBR_EXT table builder and table cache synchronization; the positive
 * table_authorised argument attests that external prerequisite.
 * This API does not build tables or route clients/streams. UFS is refused.
 */
int mb_iommu_install(struct mb_iommu *,uint32_t encoded_ttbr,int table_authorised);
int mb_iommu_invalidate(struct mb_iommu *,uint64_t iova,uint64_t bytes);
#endif
