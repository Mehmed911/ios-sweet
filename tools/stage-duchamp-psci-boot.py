#!/usr/bin/env python3
"""Stage a fail-closed Duchamp PSCI CPU_ON gate into patched XNU."""
import argparse,hashlib,json
from pathlib import Path


MARKER="DUCHAMP PSCI CPU_ON AUTH GATE V1"


def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError("unexpected or changed SweetCPU source anchor")
    return text.replace(old,new,1)


def transform(text):
    text=once(text,"#include <pexpert/pexpert.h>\n",
        "#include <pexpert/pexpert.h>\n#if defined(DUCHAMP)\n"
        "#include \"duchamp_psci_boot.h\"\n#endif\n")
    anchor='''\treturn (int32_t)x0;
}

class SweetCPU : public IOCPU {'''
    adapters='''\treturn (int32_t)x0;
}

#if defined(DUCHAMP)
/* DUCHAMP PSCI CPU_ON AUTH GATE V1: no phone capability is emitted yet. */
static int
duchamp_psci_authorise(void *context, const struct dpsci_request *request)
{
\t(void)context;
\t(void)request;
\treturn 0;
}

static int
duchamp_psci_conduit(void *context, const struct dpsci_request *request,
    int32_t *status)
{
\t(void)context;
\t*status = sweet_psci_cpu_on(request->target, request->entry,
\t    request->context);
\treturn 0;
}

static const struct dpsci_ops duchamp_psci_ops = {
\tNULL, duchamp_psci_authorise, duchamp_psci_conduit
};
#endif

class SweetCPU : public IOCPU {'''
    text=once(text,anchor,adapters)
    call='''\t__builtin_arm_dsb(DSB_SY);
\tint32_t rc = sweet_psci_cpu_on(cpu->phys_id, entry, getCPUNumber());'''
    gated='''\t__builtin_arm_dsb(DSB_SY);
#if defined(DUCHAMP)
\tconst struct dpsci_request request = {
\t\tcpu->phys_id, entry, getCPUNumber()
\t};
\tint32_t rc = DPSCI_LOCAL_UNVERIFIED;
\tint gate = dpsci_cpu_on(&duchamp_psci_ops, &request, &rc);
\tif (gate != DPSCI_OK) {
\t\tIOLog("DUCHAMP CPU: PSCI CPU_ON denied locally gate=%d\\n", gate);
\t\trc = DPSCI_LOCAL_UNVERIFIED;
\t}
#else
\tint32_t rc = sweet_psci_cpu_on(cpu->phys_id, entry, getCPUNumber());
#endif'''
    return once(text,call,gated)


def stage(root):
    repo=Path(__file__).resolve().parent.parent
    source=repo/"duchamp/drivers/duchamp_psci_boot.h"
    target=root/"iokit/Kernel/arm/duchamp_psci_boot.h"
    receipt=root/"iokit/Kernel/arm/duchamp_psci_boot.json"
    path=root/"iokit/Kernel/arm/SweetCPU.cpp"
    old=path.read_text()
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    if MARKER in old:
        if old.count(MARKER)!=1 or not target.is_file() or target.read_bytes()!=source.read_bytes() or not receipt.is_file():
            raise ValueError("partial or changed PSCI gate staging")
        expected={"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                  "header_sha256":source_hash}
        if json.loads(receipt.read_text())!=expected:
            raise ValueError("changed staged PSCI source")
        return {"already_staged":True,"header_sha256":source_hash}
    if target.exists() or receipt.exists():
        raise ValueError("preserve existing PSCI header/receipt")
    new=transform(old)
    target.write_bytes(source.read_bytes())
    path.write_text(new)
    metadata={"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
              "header_sha256":source_hash}
    receipt.write_text(json.dumps(metadata,indent=2)+"\n")
    return {"already_staged":False,"header_sha256":source_hash}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xnu",type=Path)
    args=parser.parse_args()
    print(json.dumps(stage(args.xnu.resolve()),indent=2))
