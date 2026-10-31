#ifndef DUCHAMP_PSCI_BOOT_H
#define DUCHAMP_PSCI_BOOT_H
#include <stdint.h>

/* Fail-closed PSCI CPU_ON gate for the captured MT6897 topology.  This core
 * performs no SMC itself.  A platform adapter must independently authorize
 * the exact request before the conduit callback can run. */
enum dpsci_result { DPSCI_OK=0,DPSCI_ARGUMENT=-1,DPSCI_UNVERIFIED=-2,
                    DPSCI_IO=-3 };
#define DPSCI_LOCAL_UNVERIFIED ((int32_t)(-2147483647-1))
struct dpsci_request { uint64_t target,entry,context; };
struct dpsci_ops {
    void *context;
    int (*authorise)(void *,const struct dpsci_request *);
    int (*conduit)(void *,const struct dpsci_request *,int32_t *status);
};
static inline int dpsci_cpu_on(const struct dpsci_ops *ops,
    const struct dpsci_request *request,int32_t *status) {
    if(!ops || !request || !status || !ops->authorise || !ops->conduit)
        return DPSCI_ARGUMENT;
    /* Duchamp has boot MPIDR 0 and seven secondary MPIDRs 0x100..0x700.
     * The XNU logical CPU context is the matching Aff1 value. */
    if(!request->entry || (request->entry&3) || request->context<1 ||
       request->context>7 || request->target!=(request->context<<8))
        return DPSCI_ARGUMENT;
    if(ops->authorise(ops->context,request)!=1) return DPSCI_UNVERIFIED;
    int32_t observed=DPSCI_LOCAL_UNVERIFIED;
    if(ops->conduit(ops->context,request,&observed)) return DPSCI_IO;
    *status=observed;
    return DPSCI_OK;
}
#endif
