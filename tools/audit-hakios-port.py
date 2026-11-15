#!/usr/bin/env python3
"""Inventory every tracked device-reference file and map it without executing it.

Full inventories include binaries by hash only. Source scanning is not a claim
of successful compilation, physical validation, or complete manual line review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

REPO = Path(__file__).resolve().parent.parent
PINS = {"mt6768": "ad65e1f4b3ba479e9d7ada98f17398b83cc6f285",
        "mt6833": "c24467f3074d9bfbd7cb92e2d20beacd91e468b5"}
URLS = {"mt6768": "https://github.com/oosexgang/hakios-mt6768",
        "mt6833": "https://github.com/AnkitChoudhary-1/Hackios-mt6833-port"}


def mapping(path):
    if path.endswith("device.conf"):
        return ["devices/duchamp/device.conf"], "Adapt metadata; physical claims are not inherited"
    if "configs/" in path:
        return ["devices/duchamp/configs/duchamp_defconfig", "devices/duchamp/soc/configs/mt6897.config"], "Adapt schema; disable foreign hardware and runtime flags"
    if path.endswith("soc.conf"):
        return ["devices/duchamp/soc/soc.conf"], "Use MT6897 facts, not MT6833 core/GPU descriptions"
    if path.endswith((".dtb", ".dts")):
        return ["devices/duchamp/hardware.json"], "Reject foreign hardware data; derive facts from pinned Duchamp FDT"
    if "ufs" in path.lower() or "emmc" in path.lower() or path.endswith("msdc.h"):
        return ["duchamp/drivers/ufs_readonly.c", "duchamp/drivers/ufs_register_snapshot.c", "duchamp/xnu/qemu_ufs.c"], "Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible"
    if "/loader/" in path or path.startswith("mtkloader/"):
        name = Path(path).name
        equivalent = {"start.S": "duchamp/bootshim/start.S", "link.ld": "duchamp/bootshim/shim.ld",
                      "mtkloader.c": "duchamp/bootshim/shim.c", "build.sh": "devices/duchamp/mtkloader/build.sh",
                      "build_flashed.py": "devices/duchamp/mtkloader/build_flashed.py"}
        if name in equivalent:
            return [equivalent[name]], "Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven"
        return [], "Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy"
    if Path(path).name in ("gpt-carve.py", "system-flash.sh", "xnu-cycle.sh", "boot-xnu.sh"):
        return [], "Not imported: executes partition/slot/reboot operations prohibited in this task"
    if path.endswith("chainboot.py"):
        return ["duchamp/bootshim/pack_boot.py"], "Header-v2/gzip/32-MiB packer cannot replace Duchamp v4/LZ4/64-MiB packaging; no Android chainboot equivalence"
    if any(p in path for p in ("/drivers/", "kernel/bsd/", "kernel/iokit/", "kernel/patches/")):
        return [], "Review dependencies only; hardware/runtime port deferred until UFS and recovery validation"
    if path.endswith(("README.md", "README.ru.md")) or path.startswith("docs/"):
        return ["docs/HAKIOS_SOURCE_AUDIT.md"], "Reference claims compared with actual source; no claim of device validation"
    return [], "Inventoried and scanned where textual; not needed for the bounded offline port stage"


def inventory(root, kind):
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != PINS[kind]: raise ValueError(f"{kind}: unexpected reference commit")
    if subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"]):
        raise ValueError(f"{kind}: reference worktree changed")
    names = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0")[:-1]
    rows = []
    for name in names:
        raw = (root / name).read_bytes()
        text = raw.decode("utf-8", errors="replace") if b"\0" not in raw else ""
        destinations, action = mapping(name)
        includes = re.findall(r'^\s*#\s*include\s*[<"]([^>"\n]+)', text, re.M)
        patterns = r"ufs_read_sectors|find_partition|chain_android|pmsg_take|boot_choice|mtkloader_main|ufs_wait_idle|hakios_mtk_ufs_root"
        anchors = [dict(line=i, symbol=m[0]) for i, line in enumerate(text.splitlines(), 1)
                   if (m := re.findall(r"\b(" + patterns + r")\s*\(", line))]
        risks = {word: len(re.findall(word, text)) for word in (r"\bfastboot\b", r"\b(?:wr32|writel|ufs_wr)\s*\(", r"\bsmc\b")}
        rows.append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                         text_lines=len(text.splitlines()), includes=includes, critical_anchors=anchors,
                         sensitive_operation_counts=risks, destinations=destinations, action=action,
                         status="ANALYZED", binary=not bool(text) and bool(raw)))
    licenses = [row["path"] for row in rows if "LICENSE" in row["path"] or row["path"].endswith("NOTICE")]
    return dict(url=URLS[kind], commit=head, tracked_count=len(rows),
                license_files=licenses, review="All tracked blobs inventoried, textual sources statically scanned; critical boot/storage paths inspected separately", files=rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in PINS: ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = {name: inventory(getattr(args, name), name) for name in PINS}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "reference-inventory.json").write_text(json.dumps(result, indent=2) + "\n")
    text = ["# HakiOS file mapping", "", "Every tracked MT6768 and community MT6833 file is listed, including unported files. An empty destination means no equivalent was invented. See reference-inventory.json for hashes, includes, critical line anchors and scan scope.", ""]
    for kind, data in result.items():
        text += [f"## {kind}: `{data['commit']}` ({data['tracked_count']} files)", "", "| Exact source path | Existing/new Duchamp counterpart | Action |", "| --- | --- | --- |"]
        for row in data["files"]:
            dest = ", ".join("`" + p + "`" for p in row["destinations"]) or "None (not ported)"
            text.append(f"| `{row['path']}` | {dest} | {row['action']} |")
        text.append("")
    (args.output / "HAKIOS_FILE_MAPPING.md").write_text("\n".join(text))
    print(json.dumps({k:dict(commit=v["commit"], files=v["tracked_count"], license_files=v["license_files"]) for k,v in result.items()},indent=2))


if __name__ == "__main__": main()
