#!/usr/bin/env python3
"""Reject an enabled inherited QEMU MCQ controller in full XNU, before HCI writes.

The synthetic handoff deliberately claims cold queues. Independent QTest setup
contradicts it. The real guest observation must win. No phone access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import secrets
import shutil
import struct
import types

import adt
import qemu_ufs

TOOLS = Path(__file__).resolve().parent
SLOT = runpy.run_path(str(TOOLS / "test-duchamp-slot-b-handoff.py"))
PROBE = SLOT["PROBE"]
FIXTURE_STATE = {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_mcq(endpoint, trace, *, release_after_read=False):
    assert not release_after_read
    pci, bar = qemu_ufs.ECAM[0] + (4 << 15), qemu_ufs.BAR[0]
    FIXTURE_STATE["endpoint"] = endpoint
    with PROBE["qtest"](endpoint) as command:
        assert command(f"readl {pci:#x}") == 0x00131b36
        kind = command(f"readl {pci + 0x10:#x}") & 15
        assert kind in (0, 4)
        command(f"writel {pci + 0x10:#x} {bar:#x}")
        if kind == 4:
            command(f"writel {pci + 0x14:#x} 0")
        command(f"writew {pci + 4:#x} 2")
        # Enabled, empty firmware queues. Never submit a request or enable DMA.
        for offset, value in ((0x34, 1), (0x300, 1), (0x424, 0x60003000), (0x428, 0),
                              (0x420, 0x8000001f), (0x404, 0x60002000), (0x408, 0),
                              (0x400, 0x8000001f)):
            command(f"writel {bar + offset:#x} {value:#x}")
        registers = {hex(offset): command(f"readl {bar + offset:#x}")
                     for offset in (0x34, 0x300, 0x400, 0x404, 0x420, 0x424, 0x1000,
                                    0x1004, 0x101c, 0x1020)}
        assert registers["0x34"] == registers["0x300"] == 1
        assert not any(registers[hex(offset)] for offset in (0x1000, 0x1004, 0x101c, 0x1020))
        command(f"writew {pci + 4:#x} 0")
        assert command(f"readw {pci + 4:#x}") == 0
    setup = trace.read_text().splitlines()
    assert setup and sum(line.startswith("ufs_mmio_write ") for line in setup) == 8
    return dict(queue_mode="MCQ", registers=registers, pci_command=0, setup_trace=setup,
                source="Synthetic firmware fixture, before XNU runs", dma_enabled=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("kernel", "ci-receipt", "fixture", "slot-b", "fdt", "output"):
        parser.add_argument("--" + name, type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument("--seconds", type=int, default=90)
    args = parser.parse_args()
    receipt = json.loads(args.ci_receipt.read_text(encoding="utf-8-sig"))
    assert receipt["conclusion"] == "success" and digest(args.kernel) == receipt["sha256"]
    names = PROBE["symbols"](args.kernel)
    assert {"_dufs_snapshot_registers", "_duchamp_qemu_ufs_snapshot_boot_id"} <= names.keys()
    qemu = shutil.which("qemu-system-aarch64")
    assert qemu
    before = digest(args.slot_b)
    args.output.mkdir(parents=True)
    image = args.output / "image"
    image.mkdir()
    tree, end = adt.parse((args.fixture / "qemu-ufs.adt").read_bytes())
    assert end == (args.fixture / "qemu-ufs.adt").stat().st_size
    node = qemu_ufs.child(tree, "duchamp-qemu-ufs")
    node.props = [prop for prop in node.props if prop[0] not in ("gpt-sector-size", "gpt-root-guid")]
    tree_path = args.output / "probe.adt"
    tree_path.write_bytes(adt.serialize(tree))
    assert qemu_ufs.validate_tree(tree) is None
    payload, loaders, _, _ = SLOT["build_image"](
        args, image, tree_path, gpt=False, extra_boot_args=" sweet-qemu-ufs-snapshot=1")
    boot_id = secrets.randbits(62) | (1 << 62)
    loaders, entry_id, record_id, verdict = SLOT["load_mailbox"](
        "matched", args.output, {"matched": boot_id}, loaders)
    assert verdict == 1 and entry_id == record_id
    disk = args.output / "synthetic-probe.raw"
    with disk.open("xb") as stream:
        stream.truncate((qemu_ufs.PROBE_LBA + 2) * qemu_ufs.PROBE_BYTES)
    options, metadata = qemu_ufs.runner_options(payload, disk, "cortex-a76", "duchamp")
    assert metadata["readonly"] and metadata["probe"]["lun"] == 2
    devices = [i for i, option in enumerate(options) if option.startswith("ufs,")]
    assert len(devices) == 1 and "mcq=off" in options[devices[0]]
    options[devices[0]] = options[devices[0]].replace("mcq=off", "mcq=on,mcq-maxq=8")
    metadata["observer_fixture"] = dict(mcq_device=True, max_queues=8,
        transport="one-block probe stopped before initialization", runtime_base="0x1000")
    (args.output / "ufs-input.json").write_text(json.dumps(metadata, indent=2) + "\n")
    # Substitute only the host fixture callback in a fresh function namespace.
    # The full kernel is never patched or linked to replay code.
    original = PROBE["boot_to_probe"]
    def capture_qmp(endpoint, *commands, **kwargs):
        # The guest is now at its compiled terminal WFE. Independently sample
        # its PCI command before the helper captures the framebuffer/cleans up.
        with PROBE["qtest"](FIXTURE_STATE["endpoint"]) as command:
            pci = qemu_ufs.ECAM[0] + (4 << 15)
            FIXTURE_STATE["pci_after_rejection"] = command(f"readw {pci + 4:#x}")
        assert FIXTURE_STATE["pci_after_rejection"] == 2
        return PROBE["sweet"]["qmp"](endpoint, *commands, **kwargs)
    globals_copy = {**original.__globals__, "seed_firmware_ufs": seed_mcq,
                    "sweet": {**PROBE["sweet"], "qmp": capture_qmp}}
    boot = types.FunctionType(original.__code__, globals_copy,
                              original.__name__, original.__defaults__)
    boot.__kwdefaults__ = original.__kwdefaults__
    log, screen, block, result = boot(payload, args.output, options, qemu, args.seconds,
                                    names, PROBE["probe_checkpoint"](args.kernel),
                                    inherited=True, pending=False, compare_record=None,
                                    entry_loaders=loaders)
    SLOT["check_ids"]("inherited MCQ snapshot", screen, entry_id, record_id, 1)
    marker = f"DUCHAMP UFS SNAPSHOT boot=0x{entry_id:016x} status=0 reads=316 blockers=0x29"
    assert marker in log and result["stop_marker"] == PROBE["FAILED"]
    assert block == bytes(qemu_ufs.PROBE_BYTES)
    state = json.loads((args.output / "firmware-state.json").read_text())
    all_trace = (args.output / "ufs.trace").read_text().splitlines()
    setup = state["setup_trace"]
    assert all_trace[:len(setup)] == setup
    guest = all_trace[len(setup):]
    assert len(guest) == 316 and all(line.startswith("ufs_mmio_read ") for line in guest)
    assert guest[:158] == guest[158:]
    assert not any("ufs_exec_scsi_cmd" in line for line in all_trace)
    (args.output / "xnu-only.trace").write_text("\n".join(guest) + "\n")
    assert digest(args.slot_b) == before and digest(args.kernel) == receipt["sha256"]
    report = dict(passed=True, actual_xnu=True, full_kernel_rebuild=True,
                  replay_hooks_applied=False, build=receipt, synthetic_bl31=True,
                  boot_id=hex(entry_id), fixture_claimed_cold=True, observed_inherited_mcq=True,
                  snapshot_reads=316, blockers=41, xnu_controller_writes=0,
                  scsi_commands=0, block_unchanged=True, pci_dma_enabled=False,
                  pci_command_after_rejection=FIXTURE_STATE["pci_after_rejection"],
                  slot_b_image_unchanged=True, result=result, phone_access=False, partition_write=False)
    (args.output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("XNU passive snapshot PASS: inherited MCQ rejected, 316 reads, zero HCI writes/SCSI")


if __name__ == "__main__":
    main()
