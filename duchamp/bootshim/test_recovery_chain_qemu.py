#!/usr/bin/env python3
"""Chain the stock Android kernel and test the recovery path on QEMU virt."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import stat
import struct
import subprocess
import time

from test_boot_menu_qemu import boot, press, qmp_session
from test_boot_once_qemu import expect_guest_reset, expect_no_reset


LINUX_ADDRESS = 0x50000000
RECOVERY_DTB = 0x49000000
ANDROID_DTB = 0x49200000
RECOVERY_INITRD = 0x60000000
ANDROID_INITRD = 0x70000000


def make_probe_archive(output):
    probe = output / "probe.elf"
    subprocess.run([
        "clang", "--target=aarch64-linux-gnu", "-fuse-ld=lld", "-O2",
        "-static", "-nostdlib", "-ffreestanding", "-fno-stack-protector",
        "-Wall", "-Wextra", "-Werror", "-Wl,-e,_start", "-o", probe,
        Path(__file__).with_name("qemu_recovery_probe.c"),
    ], check=True)
    archive = bytearray()
    members = (
        ("dev", stat.S_IFDIR | 0o755, b"", 0, 0),
        ("dev/console", stat.S_IFCHR | 0o600, b"", 5, 1),
        ("proc", stat.S_IFDIR | 0o755, b"", 0, 0),
        ("duchamp-recovery-probe", stat.S_IFREG | 0o755, probe.read_bytes(), 0, 0),
        ("TRAILER!!!", 0, b"", 0, 0),
    )
    for inode, (name, mode, data, major, minor) in enumerate(members, 1):
        filename = name.encode() + b"\0"
        fields = (inode, mode, 0, 0, 1, 0, len(data), 0, 0, major, minor, len(filename), 0)
        archive.extend(b"070701" + "".join(f"{field:08x}" for field in fields).encode())
        archive.extend(filename)
        archive.extend(bytes(-len(archive) % 4))
        archive.extend(data)
        archive.extend(bytes(-len(archive) % 4))
    return bytes(archive)


def make_dtb(base, output, name, slot, ramdisk, address, probe):
    dtb = output / f"{name}.dtb"
    dtb.write_bytes(base.read_bytes())
    command = ("earlycon=pl011,mmio32,0x09000000 console=ttyAMA0,115200 "
               f"loglevel={6 if probe else 7} kasan=off panic=0 "
               f"androidboot.slot_suffix=_{slot} ")
    if slot == "b":
        command += "androidboot.mode=recovery androidboot.force_normal_boot=0 "
    if probe:
        command += "rdinit=/duchamp-recovery-probe "
    subprocess.run(["fdtput", "-t", "s", dtb, "/chosen", "bootargs", command], check=True)
    for prop, value in (("linux,initrd-start", address),
                        ("linux,initrd-end", address + ramdisk.stat().st_size)):
        subprocess.run(["fdtput", "-t", "x", dtb, "/chosen", prop, "0", f"{value:x}"], check=True)
    return dtb


class Serial:
    def __init__(self, guest, transcript):
        self.guest = guest
        self.transcript = transcript
        self.cursor = 0

    def wait(self, *markers, timeout=8, required=True):
        deadline = time.monotonic() + timeout
        while True:
            hits = [(self.transcript.find(marker, self.cursor), marker) for marker in markers]
            found = [(offset, marker) for offset, marker in hits if offset >= 0]
            if found:
                offset, marker = min(found)
                self.cursor = offset + len(marker)
                return marker.decode()
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.guest.stdout], [], [], remaining)[0]:
                break
            data = os.read(self.guest.stdout.fileno(), 8192)
            if not data:
                break
            self.transcript.extend(data)
        if required:
            raise RuntimeError(f"Missing {markers!r}: {self.transcript[-1800:]!r}")
        return None

    def choose(self, slot):
        self.wait(b"DUCHAMP RECOVERY SELECT SLOT")
        press(self.guest, slot)

    def request_recovery(self):
        self.choose(b"B")
        self.wait(b"DUCHAMP RECOVERY B WAITING FOR REQUEST")
        press(self.guest, b"R")
        self.wait(b"DUCHAMP RECOVERY B ENTER ANDROID KERNEL")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shim", type=Path)
    parser.add_argument("stock_kernel", type=Path)
    parser.add_argument("recovery_ramdisk", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    shim = args.shim.resolve()
    stock = args.stock_kernel.resolve()
    recovery = args.recovery_ramdisk.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with stock.open("rb") as handle:
        header = handle.read(64)
    offset, size = struct.unpack_from("<QQ", header, 8)
    if (header[56:60] != b"ARM\x64" or offset or not 0 < size <= 0x10000000
            or stock.stat().st_size > size):
        raise RuntimeError("Stock Android Image does not fit the QEMU staging window")
    if recovery.stat().st_size > ANDROID_INITRD - RECOVERY_INITRD - 0x10000:
        raise RuntimeError("OrangeFox ramdisk exceeds the QEMU staging window")

    base = output / "virt.dtb"
    subprocess.run([
        "qemu-system-aarch64", "-M", f"virt,gic-version=3,dumpdtb={base}",
        "-cpu", "cortex-a76", "-m", "8G", "-smp", "1", "-nodefaults", "-display", "none",
    ], check=True)
    probe = make_probe_archive(output)
    android_probe = output / "android-a-probe.initramfs"
    android_probe.write_bytes(probe)
    recovery_probe = output / "recovery-b-probe.initramfs"
    data = recovery.read_bytes()
    recovery_probe.write_bytes(data + bytes(-len(data) % 4) + probe)
    android_dtb = make_dtb(base, output, "android-a", "a", android_probe, ANDROID_INITRD, True)
    probe_dtb = make_dtb(base, output, "recovery-probe-b", "b", recovery_probe, RECOVERY_INITRD, True)
    orangefox_dtb = make_dtb(base, output, "orangefox-b", "b", recovery, RECOVERY_INITRD, False)
    base_fixtures = ((stock, LINUX_ADDRESS), (android_dtb, ANDROID_DTB), (android_probe, ANDROID_INITRD))

    with boot(shim, output, "no-request") as (guest, _qmp, _temp, log):
        serial = Serial(guest, log)
        serial.choose(b"B")
        serial.wait(b"DUCHAMP RECOVERY B WAITING FOR REQUEST")
        press(guest, b"N")
        serial.wait(b"DUCHAMP RECOVERY B NO REQUEST")
    if b"ENTER ANDROID KERNEL" in log:
        raise RuntimeError("Bootshim entered Linux without a recovery request")
    print("no-request: PASS", flush=True)

    with boot(shim, output, "invalid-payload") as (guest, _qmp, _temp, log):
        serial = Serial(guest, log)
        serial.choose(b"B")
        serial.wait(b"DUCHAMP RECOVERY B WAITING FOR REQUEST")
        press(guest, b"R")
        serial.wait(b"DUCHAMP RECOVERY INVALID QEMU PAYLOAD")
    print("invalid-payload: PASS", flush=True)

    fixtures = base_fixtures + ((probe_dtb, RECOVERY_DTB), (recovery_probe, RECOVERY_INITRD))
    for name, reply in (("return-to-a", b"A\n"), ("wrong-readback", b"B\n")):
        with boot(shim, output, name, ram_fixtures=fixtures, warm_reset=True) as (guest, qmp, _temp, log):
            serial = Serial(guest, log)
            serial.request_recovery()
            serial.wait(b"DUCHAMP RETURN PROBE RECOVERY B PID1", timeout=55)
            serial.wait(b"DUCHAMP RETURN PROBE NEXT SLOT REQUEST A")
            with qmp_session(qmp) as stream:
                press(guest, reply)
                if reply == b"A\n":
                    serial.wait(b"DUCHAMP RETURN PROBE NEXT SLOT VERIFIED A")
                    expect_guest_reset(stream)
                else:
                    serial.wait(b"DUCHAMP RETURN PROBE WRONG SLOT")
                    expect_no_reset(stream)
            if reply == b"A\n":
                serial.choose(b"A")
                serial.wait(b"DUCHAMP RECOVERY A ENTER ANDROID KERNEL")
                serial.wait(b"DUCHAMP RETURN PROBE ANDROID KERNEL A PID1", timeout=55)
        print(f"{name}: PASS", flush=True)

    fixtures = base_fixtures + ((orangefox_dtb, RECOVERY_DTB), (recovery, RECOVERY_INITRD))
    with boot(shim, output, "orangefox", ram_fixtures=fixtures) as (guest, _qmp, _temp, log):
        serial = Serial(guest, log)
        serial.request_recovery()
        serial.wait(b"init first stage started", timeout=60)
        serial.wait(b'comm="recovery"', timeout=70)
        serial.wait(b"Can't open blockdev", timeout=10, required=False)
    missing_blockdev = b"Can't open blockdev" in log
    missing_partitions = b"partition(s) not found after polling timeout" in log
    print("orangefox: PASS packaged recovery process observed", flush=True)

    result = {
        "machine": "QEMU virt, no drives or network",
        "stock_kernel_sha256": hashlib.sha256(stock.read_bytes()).hexdigest(),
        "orangefox_recovery_ramdisk_sha256": hashlib.sha256(recovery.read_bytes()).hexdigest(),
        "slot_b_no_request_does_not_chain": True,
        "slot_b_missing_payload_rejected": True,
        "stock_android_kernel_entered_from_bootshim_b": True,
        "orangefox_first_stage_init_started": True,
        "packaged_orangefox_recovery_process_observed": True,
        "android_init_reported_missing_partitions": missing_partitions,
        "guest_reported_missing_blockdev": missing_blockdev,
        "orangefox_ui_or_boot_control_verified": False,
        "simulated_slot_provider_verified_linux_guest_reset_and_a_probe": True,
        "wrong_slot_readback_blocks_reset": True,
        "full_android_a_userspace_tested": False,
        "physical_phone_or_partitions_touched": False,
    }
    (output / "verification.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
