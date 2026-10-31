#!/usr/bin/env python3
"""Stage a fail-closed CNTFRQ/ADT contract check into patched XNU."""
import argparse,hashlib,json
from pathlib import Path


MARKER="DUCHAMP CNTFRQ CONTRACT V1"


def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError("unexpected or changed arm_init source anchor")
    return text.replace(old,new,1)


def transform(text):
    text=once(text,"#include <arm/cpu_internal.h>\n",
        "#include <arm/cpu_internal.h>\n#if defined(DUCHAMP)\n"
        "#include <arm/duchamp_timer_boot.h>\n#endif\n")
    call="\tcpu_timebase_init(TRUE);"
    guarded='''#if defined(DUCHAMP)
\t/* DUCHAMP CNTFRQ CONTRACT V1: an architected read, never MMIO/firmware. */
\tuint64_t const duchamp_cntfrq = __builtin_arm_rsr64("CNTFRQ_EL0");
\tuint32_t const duchamp_expected_cntfrq =
\t    gPEClockFrequencyInfo.timebase_frequency_hz;
\tint const duchamp_cntfrq_status = dtimer_frequency_check(
\t    duchamp_expected_cntfrq, duchamp_cntfrq);
\tif (duchamp_cntfrq_status != DTIMER_OK) {
\t\tpanic("DUCHAMP TIMER: CNTFRQ contract failed %d expected=%u observed=%llu",
\t\t    duchamp_cntfrq_status, duchamp_expected_cntfrq, duchamp_cntfrq);
\t}
\tkprintf("DUCHAMP TIMER: CNTFRQ verified %llu Hz\\n", duchamp_cntfrq);
#endif

\tcpu_timebase_init(TRUE);'''
    return once(text,call,guarded)


def stage(root):
    repo=Path(__file__).resolve().parent.parent
    source=repo/"duchamp/drivers/duchamp_timer_boot.h"
    target=root/"osfmk/arm/duchamp_timer_boot.h"
    receipt=root/"osfmk/arm/duchamp_timer_boot.json"
    path=root/"osfmk/arm/arm_init.c"
    old=path.read_text()
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    if MARKER in old:
        if old.count(MARKER)!=1 or not target.is_file() or target.read_bytes()!=source.read_bytes() or not receipt.is_file():
            raise ValueError("partial or changed timer contract staging")
        expected={"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                  "header_sha256":source_hash}
        if json.loads(receipt.read_text())!=expected:
            raise ValueError("changed staged timer source")
        return {"already_staged":True,"header_sha256":source_hash}
    if target.exists() or receipt.exists():
        raise ValueError("preserve existing timer header/receipt")
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
