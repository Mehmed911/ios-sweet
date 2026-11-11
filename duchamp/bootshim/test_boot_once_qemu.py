#!/usr/bin/env python3
"""Replay Android pmsg production and an A/B firmware selector in QEMU virt."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from test_boot_menu_qemu import boot, expect, press, qmp_session
from test_qemu import qmp_call


PMSG_ADDRESS = 0x48160000
PMSG_SIZE = 0x10000
FIXTURE_ADDRESS = 0x41000000
GUARD_SIZE = 16
HEADER = struct.Struct("<4sII")
CAPACITY = PMSG_SIZE - HEADER.size
REQUEST = b"\nDUCHAMP:BOOT-XNU-ONCE\n"


def android_ring(payload):
    """Model pmsg's write cursor, valid byte count and wrapped payload."""
    end = len(payload) % CAPACITY
    valid = min(len(payload), CAPACITY)
    data = bytearray(CAPACITY)
    start = (end - valid) % CAPACITY
    for i, byte in enumerate(payload[-valid:] if valid else b""):
        data[(start + i) % CAPACITY] = byte
    return HEADER.pack(b"DBGC", end, valid) + data


def consumed(ring):
    _, end, size = HEADER.unpack_from(ring)
    data = ring[HEADER.size:]
    oldest = (end - size) % CAPACITY
    valid = (data[oldest:] + data[:oldest])[:size]
    updated = bytearray(ring)
    match = valid.find(REQUEST)
    while match != -1:
        updated[HEADER.size + (oldest + match + 1) % CAPACITY] = ord("!")
        match = valid.find(REQUEST, match + 1)
    return updated


def read_zone(qmp, temp):
    snapshot = temp / "pmsg-and-guards.bin"
    with qmp_session(qmp) as stream:
        qmp_call(stream, "pmemsave", val=PMSG_ADDRESS - GUARD_SIZE,
                 size=PMSG_SIZE + 2 * GUARD_SIZE, filename=str(snapshot))
    return snapshot.read_bytes()


def expect_guest_reset(stream):
    while packet := stream.readline():
        event = json.loads(packet)
        if event.get("event") == "RESET":
            if event["data"] != {"guest": True, "reason": "guest-reset"}:
                raise RuntimeError(f"Unexpected reset: {event!r}")
            return
    raise RuntimeError("Missing QEMU guest-reset event")


def expect_no_reset(stream):
    stream.write(b'{"execute":"query-status","id":"still-running"}\n')
    stream.flush()
    while packet := stream.readline():
        response = json.loads(packet)
        if response.get("event") in ("RESET", "SHUTDOWN"):
            raise RuntimeError(f"Unexpected reset event: {response!r}")
        if response.get("id") == "still-running":
            if response.get("return", {}).get("status") != "running":
                raise RuntimeError(f"Guest is no longer running: {response!r}")
            return
    raise RuntimeError("QEMU stopped without confirming guest state")


def verify_case(image, dtb, output, name, ring, outcome, readback):
    fixture = output / f"{name}.fixture.bin"
    fixture.write_bytes(ring)
    with boot(image, output, name, dtb, ram_fixture=(fixture, FIXTURE_ADDRESS),
              warm_reset=True) as (guest, qmp, temp, log):
        cursor = 0

        def serial(line):
            nonlocal cursor
            cursor = expect(guest, log, line, after=cursor)

        def select_slot(slot):
            serial("DUCHAMP ONCE SELECT SLOT")
            press(guest, slot)

        select_slot(b"A")
        serial("DUCHAMP ONCE ANDROID A READY")
        empty = read_zone(qmp, temp)
        if empty != bytes(PMSG_SIZE + 2 * GUARD_SIZE):
            raise RuntimeError("pmsg RAM was populated before Android A published it")
        with qmp_session(qmp) as stream:
            press(guest, b"W")
            serial("DUCHAMP ONCE ANDROID A PMSG PUBLISHED")
            expect_guest_reset(stream)

        serial("DUCHAMP ONCE SELECT SLOT")
        if read_zone(qmp, temp) != empty[:GUARD_SIZE] + ring + empty[-GUARD_SIZE:]:
            raise RuntimeError("Android A's pmsg ring did not survive the guest reset")
        press(guest, b"B")
        serial(f"DUCHAMP ONCE B {outcome}")
        has_request = outcome == "CONSUMED REQUEST"
        if has_request:
            serial("DUCHAMP ONCE B XNU DISPATCH SIMULATED")
        serial("DUCHAMP ANDROID NEXT SLOT REQUEST A")

        expected = empty[:GUARD_SIZE] + (consumed(ring) if has_request else ring) + empty[-GUARD_SIZE:]
        if read_zone(qmp, temp) != expected:
            raise RuntimeError("Bootshim made an unexpected pmsg or guard-byte change")

        with qmp_session(qmp) as stream:
            if readback is not None:
                press(guest, readback)
            if readback == b"A":
                serial("DUCHAMP ANDROID NEXT SLOT VERIFIED A")
                expect_guest_reset(stream)
            else:
                reason = "NEXT SLOT" if readback is not None else "NO READBACK"
                serial(f"DUCHAMP ANDROID BLOCKED {reason}")
                expect_no_reset(stream)

        replay_checked = False
        if readback == b"A":
            select_slot(b"A")
            serial("DUCHAMP ONCE ANDROID A READY")
            if read_zone(qmp, temp) != expected:
                raise RuntimeError("pmsg state changed across return to A")
            if has_request:
                # Enter B again with the same RAM and without a second publish.
                with qmp_session(qmp) as stream:
                    qmp_call(stream, "system_reset")
                select_slot(b"B")
                serial("DUCHAMP ONCE B NO REQUEST")
                serial("DUCHAMP ANDROID NEXT SLOT REQUEST A")
                if read_zone(qmp, temp) != expected:
                    raise RuntimeError("Replay changed the consumed ring")
                replay_checked = True

    expected_dispatches = int(has_request)
    if log.count(b"DUCHAMP ONCE B XNU DISPATCH SIMULATED\n") != expected_dispatches:
        raise RuntimeError("Unexpected number of XNU dispatches")
    expected_entries = 2 + int(readback == b"A") + int(replay_checked)
    if log.count(b"DUCHAMP ONCE SELECT SLOT\n") != expected_entries:
        raise RuntimeError("Unexpected number of bootshim entries")
    print(f"{name}: PASS {outcome}, readback={readback!r}, replay={replay_checked}", flush=True)
    return {"bootshim_outcome": outcome, "xnu_dispatch_count": expected_dispatches,
            "a_to_b_guest_reset": True, "pmsg_and_guards_verified": True,
            "return_readback": readback.decode() if readback else None,
            "return_guest_reset_and_a_entry": readback == b"A",
            "replay_rejected_after_reset": replay_checked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("dtb", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    dtb = args.dtb.resolve()
    node = "/reserved-memory/mblock-2-pstore"
    reg = subprocess.check_output(["fdtget", "-tx", dtb, node, "reg"], text=True)
    upper, address, size_upper, size = (int(word, 16) for word in reg.split())
    if upper or size_upper or address + size != PMSG_ADDRESS + PMSG_SIZE:
        raise RuntimeError("Duchamp DTB does not match the modeled pstore region")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    linear = android_ring(b"Android log" + REQUEST)
    stale = bytearray(android_ring(b"log"))
    stale[64:64 + len(REQUEST)] = REQUEST
    bad_cursor = HEADER.pack(b"DBGC", CAPACITY, len(REQUEST)) + linear[HEADER.size:]
    cases = (
        ("linear", linear, "CONSUMED REQUEST", b"A"),
        ("wrapped", android_ring(b"x" * (CAPACITY - 7) + REQUEST), "CONSUMED REQUEST", b"A"),
        ("missing", android_ring(b""), "NO REQUEST", b"A"),
        ("stale", stale, "NO REQUEST", b"A"),
        ("later-log", android_ring(REQUEST + b"later log"), "CONSUMED REQUEST", b"A"),
        ("duplicate", android_ring(REQUEST + REQUEST[1:]), "CONSUMED REQUEST", b"A"),
        ("truncated", android_ring(REQUEST[:-1]), "NO REQUEST", b"A"),
        ("invalid-header", bad_cursor, "INVALID PMSG", b"A"),
        ("wrong-slot", linear, "CONSUMED REQUEST", b"B"),
        ("no-readback", linear, "CONSUMED REQUEST", None),
    )
    result = {"machine": "QEMU virt", "pmsg_address": hex(PMSG_ADDRESS),
              "pmsg_size": PMSG_SIZE, "dtb_sha256": hashlib.sha256(dtb.read_bytes()).hexdigest(),
              "android_pmsg_writer_and_slot_provider": "simulated",
              "physical_phone_tested": False, "xnu_kernel_executed": False,
              "cases": {name: verify_case(args.image.resolve(), dtb, output, name,
                                          ring, outcome, reply)
                        for name, ring, outcome, reply in cases}}
    (output / "verification.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
