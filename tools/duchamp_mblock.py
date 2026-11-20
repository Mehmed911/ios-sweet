"""Decode the archived Duchamp LK v2 mblock layout, without granting access.

The layout is corroborated against lk_a.bin and the saved FDT, not a portable
MediaTek ABI. A decoded free pool is allocator bookkeeping in that archive;
it is not evidence of current ownership, reservation lifetime, or DMA exclusion.
"""

import hashlib
import struct

from duchamp_memory_placement import Interval


SIZE = 0x5818
CAPACITY = 128
RESERVED_OFFSET = 0xc18
RESERVED_STRIDE = 0x98


def decode_mblock(raw):
    if len(raw) != SIZE:
        raise ValueError("unsupported mblock length")
    free_count = struct.unpack_from("<Q", raw)[0]
    magic, version, reserved_count, padding = struct.unpack_from("<4I", raw, 0xc08)
    if magic != 0x99999999 or version != 2 or padding:
        raise ValueError("unsupported mblock header")
    if not 0 < free_count <= CAPACITY or not 0 <= reserved_count <= CAPACITY:
        raise ValueError("mblock count out of bounds")
    free, reserved = [], []
    for index in range(free_count):
        start, size, rank = struct.unpack_from("<QQQ", raw, 8 + index * 24)
        row = {"name": f"free-{index}", "slot": index, "start": start,
               "bytes": size, "rank": rank}
        Interval.from_row(row)
        if (start | size) & 0xfff or rank not in (0, 1):
            raise ValueError("invalid Duchamp free-pool alignment or rank")
        free.append(row)
    # Slots after free_count can retain stale bytes. Do not interpret them.
    # Reserved entries instead have holes, so reserved_count is not a bound
    # on the slot number. Inspect all 128 slots and verify the active count.
    for index in range(CAPACITY):
        offset = RESERVED_OFFSET + index * RESERVED_STRIDE
        start, size, mapping = struct.unpack_from("<QQI", raw, offset)
        if not start and not size:
            if any(raw[offset:offset + RESERVED_STRIDE]):
                raise ValueError("nonempty unused reservation slot")
            continue
        name = raw[offset + 20:offset + 148]
        terminator = name.find(b"\0")
        if terminator <= 0:
            raise ValueError("missing reservation name or terminator")
        try:
            label = name[:terminator].decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("invalid reservation name") from error
        if any(ord(char) < 32 or ord(char) > 126 for char in label):
            raise ValueError("nonprintable reservation name")
        row = {"name": label, "slot": index, "start": start,
               "bytes": size, "mapping": mapping}
        Interval.from_row(row)
        if (start | size) & 0xfff or mapping not in (0, 1):
            raise ValueError("invalid reservation alignment or mapping flag")
        reserved.append(row)
    if len(reserved) != reserved_count:
        raise ValueError("reservation count disagrees with active slots")
    spans = [(row, Interval.from_row(row)) for row in free + reserved]
    spans.sort(key=lambda item: item[1].start)
    for (left, a), (right, b) in zip(spans, spans[1:]):
        if a.intersects(b):
            raise ValueError(f"overlapping mblock entries {left['name']} / {right['name']}")
    return {"format": "duchamp-archived-lk-mblock-v2", "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "free": free,
            "reserved": reserved, "physical_execution_authorized": False,
            "evidence_scope": "archived-allocator-bookkeeping-only"}
