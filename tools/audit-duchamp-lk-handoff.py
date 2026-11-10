#!/usr/bin/env python3
"""Document the saved Duchamp LK/Linux/FDT handoff without device access.

This audit accepts only the exact saved artifacts.  It distinguishes LK's own
bootstrap mapping from the Android Image load contract and from the final live
FDT handoff address.  It does not execute firmware, contact a phone, authorize
a phone boot, or turn static metadata into a runtime-register claim.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys


LK_BYTES = 16 * 1024 * 1024
LK_SHA256 = "f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a"
BOOT_SHA256 = "1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12"
VENDOR_BOOT_SHA256 = "d1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49"
FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
IOMEM_SHA256 = "b6bf43ce2bcbe1d5d425b46977afe238653859f61403339b674a2c065054f833"
STOCK_IMAGE_SHA256 = "39baa1bd10c50eaf9d91d8e2d94e6345d220a9703deec7c03dece82d9b44cdfe"

MTK_OUTER_MAGIC = 0x58881688
MTK_INNER_MAGIC = 0x58891689
MTK_HEADER_BYTES = 0x200
MTK_ALIGNMENT = 0x10
LK_ENTRY_PAYLOAD_BYTES = 0xF1C70
LK_MAP_RECORD_OFFSET = 0xD6200
LK_ALIAS_LITERAL_OFFSET = 0x508
LK_PHYSICAL_BASE = 0x50700000
LK_VIRTUAL_ALIAS = 0xFFFF000050700000
LK_MAPPING_BYTES = 0x12000000
LK_HANDOFF_CALLSITE_OFFSET = 0x10054
LK_HANDOFF_CALLSITE = bytes.fromhex(
    "a12280521f2003d5c06300100140b872"
    "e20313aae30316aae4031faa92250094"
)
LK_SMC_TRAMPOLINE_OFFSET = 0x10CD4
LK_SMC_TRAMPOLINE = bytes.fromhex("240080d2030000d4c0035fd6")
LK_SMC_FUNCTION_ID = 0xC2000115

BL31_BYTES = 953976
BL31_SHA256 = "716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e"
BL31_BASE = 0x48800000
BL31_KERNEL_BOOT_DESCRIPTOR = 0x65500
BL31_KERNEL_BOOT_HANDLER = 0xB63C
BL31_BOOT_CALLBACK_BOUNDS = 0x67118 + 5 * 8
BL31_BOOT_CALLBACKS = (
    ("sip_emi_set_nsr_permission", 0x37150),
    ("spm_smpu_hre_first_bk", 0x3B5F8),
)
# Saved handler selects callback group 5 before the final helper. The
# iterator reads both bounds and calls each 16-byte entry's function.
BL31_BOOT_CALLBACK_CALLSITE = bytes.fromhex(
    "26feff97a0008052950200f9b575009423720094"
)
BL31_BOOT_CALLBACK_ITERATOR = bytes.fromhex(
    "f40100f094620491955a61f8550200b436040011887a76f8bf0208ebc2010054"
    "73010090737a2a91a80640f900013fd6"
)

ANDROID_IMAGE_LOAD = 0x40000000
LIVE_FDT_ADDRESS = 0x47C80000
LIVE_FDT_BYTES = 0x76980
LIVE_FDT_RESERVED_BYTES = 0x77000
VENDOR_RAMDISK_ADDRESS = 0x66F00000
BOOT_PAGE_BYTES = 4096
BOOT_KERNEL_BYTES = 16295649
STOCK_IMAGE_BYTES = 34765312
STOCK_IMAGE_MEMORY_BYTES = 0x21D0000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def receipt(path, raw):
    return {
        "path": str(path.resolve()),
        "bytes": len(raw),
        "sha256": sha256(raw),
    }


def u32(raw, offset):
    require(0 <= offset <= len(raw) - 4, "truncated 32-bit field")
    return struct.unpack_from("<I", raw, offset)[0]


def u64(raw, offset):
    require(0 <= offset <= len(raw) - 8, "truncated 64-bit field")
    return struct.unpack_from("<Q", raw, offset)[0]


def align_up(value, alignment):
    require(alignment > 0 and alignment & (alignment - 1) == 0,
            "alignment must be a power of two")
    return (value + alignment - 1) & ~(alignment - 1)


def c_string(raw, offset, width):
    require(0 <= offset and 0 < width <= len(raw) - offset,
            "truncated string field")
    value = raw[offset:offset + width].split(b"\0", 1)[0]
    try:
        return value.decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("non-ASCII package entry name") from error


def range_record(name, start, size, **extra):
    require(0 <= start < 1 << 64 and 0 < size <= (1 << 64) - start,
            f"invalid range: {name}")
    result = {
        "name": name,
        "start": start,
        "start_hex": hex(start),
        "bytes": size,
        "bytes_hex": hex(size),
        "end_exclusive": start + size,
        "end_exclusive_hex": hex(start + size),
    }
    result.update(extra)
    return result


def overlaps(first_start, first_size, second_start, second_size):
    return (first_size > 0 and second_size > 0 and
            first_start < second_start + second_size and
            second_start < first_start + first_size)


def parse_mtk_package(raw):
    entries = []
    offset = 0
    while offset + MTK_HEADER_BYTES <= len(raw):
        if u32(raw, offset) != MTK_OUTER_MAGIC:
            require(all(value in (0, 0xFF) for value in raw[offset:]),
                    "unexpected bytes after final MTK package entry")
            break
        payload_bytes = u32(raw, offset + 4)
        name = c_string(raw, offset + 8, 32)
        require(name, "empty MTK package entry name")
        require(u32(raw, offset + 0x30) == MTK_INNER_MAGIC,
                f"{name}: unexpected inner magic")
        payload_offset = u32(raw, offset + 0x34)
        require(payload_offset == MTK_HEADER_BYTES,
                f"{name}: unexpected payload offset")
        payload_start = offset + payload_offset
        payload_end = payload_start + payload_bytes
        require(payload_end <= len(raw), f"{name}: payload exceeds partition")
        entries.append({
            "name": name,
            "entry_offset": offset,
            "entry_offset_hex": hex(offset),
            "payload_offset": payload_start,
            "payload_offset_hex": hex(payload_start),
            "payload_bytes": payload_bytes,
            "payload_bytes_hex": hex(payload_bytes),
            "payload_sha256": sha256(raw[payload_start:payload_end]),
        })
        offset = align_up(payload_end, MTK_ALIGNMENT)
    require(entries, "LK partition has no MTK package entries")
    return entries


def inspect_lk(raw):
    require(len(raw) == LK_BYTES, "lk_a size differs")
    require(sha256(raw) == LK_SHA256, "lk_a SHA-256 differs")
    entries = parse_mtk_package(raw)
    first = entries[0]
    require(first["name"] == "lk" and
            first["payload_offset"] == MTK_HEADER_BYTES and
            first["payload_bytes"] == LK_ENTRY_PAYLOAD_BYTES,
            "first LK package entry differs")
    require(LK_MAP_RECORD_OFFSET + 24 <=
            first["payload_offset"] + first["payload_bytes"],
            "LK bootstrap map record is outside the LK payload")
    physical, virtual, size = struct.unpack_from(
        "<QQQ", raw, LK_MAP_RECORD_OFFSET)
    require((physical, virtual, size) ==
            (LK_PHYSICAL_BASE, LK_VIRTUAL_ALIAS, LK_MAPPING_BYTES),
            "LK bootstrap mapping record differs")
    alias_literal = u64(raw, LK_ALIAS_LITERAL_OFFSET)
    require(alias_literal == LK_VIRTUAL_ALIAS,
            "LK startup virtual-alias literal differs")
    require(raw[LK_HANDOFF_CALLSITE_OFFSET:
                LK_HANDOFF_CALLSITE_OFFSET + len(LK_HANDOFF_CALLSITE)] ==
            LK_HANDOFF_CALLSITE,
            "LK Linux handoff callsite differs")
    require(raw[LK_SMC_TRAMPOLINE_OFFSET:
                LK_SMC_TRAMPOLINE_OFFSET + len(LK_SMC_TRAMPOLINE)] ==
            LK_SMC_TRAMPOLINE,
            "LK secure-monitor trampoline differs")
    return {
        "partition_bytes": len(raw),
        "partition_sha256": sha256(raw),
        "package_entries": entries,
        "self_bootstrap_mapping": {
            "status": "verified-in-exact-lk-binary",
            "physical_base": physical,
            "physical_base_hex": hex(physical),
            "virtual_alias": virtual,
            "virtual_alias_hex": hex(virtual),
            "mapped_bytes": size,
            "mapped_bytes_hex": hex(size),
            "mapping_record_partition_offset": LK_MAP_RECORD_OFFSET,
            "mapping_record_partition_offset_hex": hex(LK_MAP_RECORD_OFFSET),
            "startup_alias_literal_partition_offset": LK_ALIAS_LITERAL_OFFSET,
            "startup_alias_literal_partition_offset_hex":
                hex(LK_ALIAS_LITERAL_OFFSET),
            "interpretation": (
                "LK's own stage-1 bootstrap map binds this exact binary to "
                "physical 0x50700000 and high VA 0xffff000050700000"
            ),
            "runtime_pc_register_captured": False,
        },
        "linux_handoff": {
            "status": "verified-in-exact-lk-binary",
            "mechanism": "secure-monitor-call",
            "smc_function_id": LK_SMC_FUNCTION_ID,
            "smc_function_id_hex": hex(LK_SMC_FUNCTION_ID),
            "callsite_partition_offset": LK_HANDOFF_CALLSITE_OFFSET,
            "callsite_partition_offset_hex":
                hex(LK_HANDOFF_CALLSITE_OFFSET),
            "trampoline_partition_offset": LK_SMC_TRAMPOLINE_OFFSET,
            "trampoline_partition_offset_hex":
                hex(LK_SMC_TRAMPOLINE_OFFSET),
            "callsite_arguments": {
                "x0": "secure trampoline address",
                "x1": "SMC function ID 0xc2000115",
                "x2": "runtime-computed kernel target address",
                "x3": "runtime-computed final FDT address",
                "x4": "0",
            },
            "trampoline_arguments": {
                "x0": "SMC function ID 0xc2000115",
                "x1": "runtime-computed kernel target address",
                "x2": "runtime-computed final FDT address",
                "x3": "0",
                "x4": "1",
            },
            "kernel_target_is_fixed_in_lk_binary": False,
            "fdt_target_is_fixed_in_lk_binary": False,
        },
    }


def inspect_bl31_handoff(raw):
    require(len(raw) == BL31_BYTES, "captured BL31 size differs")
    digest = sha256(raw)
    require(digest == BL31_SHA256, "captured BL31 SHA-256 differs")
    handler, fast32, fast64, name, _ = struct.unpack_from(
        "<QIIQQ", raw, BL31_KERNEL_BOOT_DESCRIPTOR)
    require((handler, fast32, fast64) ==
            (BL31_BASE + BL31_KERNEL_BOOT_HANDLER, 0x82000115,
             LK_SMC_FUNCTION_ID) and
            c_string(raw, name - BL31_BASE, 32) == "MTK_SIP_KERNEL_BOOT",
            "captured BL31 kernel boot descriptor differs")
    for start, instructions in (
        (0xB6B8, BL31_BOOT_CALLBACK_CALLSITE),
        (0x28DB4, BL31_BOOT_CALLBACK_ITERATOR),
    ):
        require(raw[start:start + len(instructions)] == instructions,
                "captured BL31 boot callback instructions differ")
    begin, end = struct.unpack_from("<QQ", raw, BL31_BOOT_CALLBACK_BOUNDS)
    require((begin, end) == (BL31_BASE + 0x61C70, BL31_BASE + 0x61C90),
            "captured BL31 boot callback table bounds differ")
    callbacks = []
    for index, (expected_name, expected_target) in enumerate(BL31_BOOT_CALLBACKS):
        offset = begin - BL31_BASE + index * 16
        name, target = struct.unpack_from("<QQ", raw, offset)
        observed_name = c_string(raw, name - BL31_BASE, 32)
        require((observed_name, target) ==
                (expected_name, BL31_BASE + expected_target),
                "captured BL31 boot callback entry differs")
        callbacks.append({"name": observed_name, "handler_file_offset": hex(expected_target)})
    return {
        "scope": "static captured BL31 only",
        "capture_sha256": digest,
        "kernel_boot_descriptor_file_offset": hex(BL31_KERNEL_BOOT_DESCRIPTOR),
        "kernel_boot_handler_file_offset": hex(BL31_KERNEL_BOOT_HANDLER),
        "boot_callbacks_in_table_order": callbacks,
        "required_observation_point":
            "after BL31 boot callbacks and before the non-secure handoff",
        "installed_bl31_binary_equivalence_proven": False,
        "xnu_handoff_snapshot_present": False,
        "ufs_queues_idle_proven": False,
        "ufs_resource_delegation_proven": False,
        "physical_ufs_authorized": False,
    }


def decompress_legacy_lz4(raw):
    require(raw[:4] == bytes.fromhex("02214c18"),
            "stock kernel is not an LZ4 legacy frame")
    executable = shutil.which("lz4")
    require(executable is not None, "lz4 is required to inspect stock boot")
    process = subprocess.run(
        [executable, "-dc"], input=raw, capture_output=True, timeout=60)
    require(process.returncode == 0,
            "cannot decompress stock kernel: " +
            process.stderr.decode("utf-8", errors="replace"))
    require(len(process.stdout) <= 128 * 1024 * 1024,
            "decompressed stock kernel is unexpectedly large")
    return process.stdout


def parse_arm64_image(image):
    require(len(image) >= 64 and image[56:60] == b"ARM\x64",
            "stock kernel lacks an ARM64 Image header")
    text_offset = u64(image, 8)
    memory_bytes = u64(image, 16)
    flags = u64(image, 24)
    require(text_offset == 0, "stock Image text_offset differs")
    require(memory_bytes == STOCK_IMAGE_MEMORY_BYTES,
            "stock Image memory size differs")
    require(flags == 0xA, "stock Image flags differ")
    return {
        "file_bytes": len(image),
        "sha256": sha256(image),
        "text_offset": text_offset,
        "text_offset_hex": hex(text_offset),
        "memory_bytes": memory_bytes,
        "memory_bytes_hex": hex(memory_bytes),
        "flags": flags,
        "flags_hex": hex(flags),
        "magic": "ARM\\x64",
    }


def inspect_boot(raw, decompressor=decompress_legacy_lz4):
    require(sha256(raw) == BOOT_SHA256, "boot_a SHA-256 differs")
    require(raw[:8] == b"ANDROID!", "boot_a magic differs")
    require(u32(raw, 20) == 1584 and u32(raw, 40) == 4,
            "boot_a is not the captured header-v4 image")
    kernel_bytes = u32(raw, 8)
    require(kernel_bytes == BOOT_KERNEL_BYTES,
            "boot_a kernel size differs")
    require(BOOT_PAGE_BYTES + kernel_bytes <= len(raw),
            "boot_a kernel is truncated")
    compressed = raw[BOOT_PAGE_BYTES:BOOT_PAGE_BYTES + kernel_bytes]
    image = decompressor(compressed)
    require(len(image) == STOCK_IMAGE_BYTES,
            "decompressed stock Image size differs")
    require(sha256(image) == STOCK_IMAGE_SHA256,
            "decompressed stock Image SHA-256 differs")
    return {
        "partition_bytes": len(raw),
        "partition_sha256": sha256(raw),
        "kernel_bytes": kernel_bytes,
        "kernel_format": "lz4-legacy",
        "image": parse_arm64_image(image),
    }


def inspect_vendor_boot(raw):
    require(sha256(raw) == VENDOR_BOOT_SHA256,
            "vendor_boot_a SHA-256 differs")
    require(raw[:8] == b"VNDRBOOT" and u32(raw, 8) == 4,
            "vendor_boot_a is not header version 4")
    page_size = u32(raw, 12)
    kernel_address = u32(raw, 16)
    ramdisk_address = u32(raw, 20)
    ramdisk_bytes = u32(raw, 24)
    tags_address = u32(raw, 2076)
    header_bytes = u32(raw, 2096)
    dtb_bytes = u32(raw, 2100)
    dtb_address = u64(raw, 2104)
    require(page_size == 4096 and header_bytes == 2128,
            "vendor_boot_a header shape differs")
    require(kernel_address == ANDROID_IMAGE_LOAD,
            "vendor_boot_a kernel_addr differs")
    require(ramdisk_address == VENDOR_RAMDISK_ADDRESS,
            "vendor_boot_a ramdisk_addr differs")
    require(tags_address == LIVE_FDT_ADDRESS and
            dtb_address == LIVE_FDT_ADDRESS,
            "vendor_boot_a tags_addr/dtb_addr differ")
    require(ramdisk_bytes > 0 and dtb_bytes > 0,
            "vendor_boot_a declares an empty ramdisk or DTB")
    return {
        "partition_bytes": len(raw),
        "partition_sha256": sha256(raw),
        "header_version": 4,
        "page_size": page_size,
        "header_bytes": header_bytes,
        "kernel_addr": kernel_address,
        "kernel_addr_hex": hex(kernel_address),
        "ramdisk_addr": ramdisk_address,
        "ramdisk_addr_hex": hex(ramdisk_address),
        "ramdisk_bytes": ramdisk_bytes,
        "ramdisk_bytes_hex": hex(ramdisk_bytes),
        "tags_addr": tags_address,
        "tags_addr_hex": hex(tags_address),
        "dtb_addr": dtb_address,
        "dtb_addr_hex": hex(dtb_address),
        "packaged_dtb_bytes": dtb_bytes,
        "packaged_dtb_bytes_hex": hex(dtb_bytes),
    }


def load_fdt_parser(repo):
    parser_path = repo / "tools" / "inspect-duchamp-hardware.py"
    spec = importlib.util.spec_from_file_location(
        "duchamp_handoff_fdt_parser", parser_path)
    require(spec is not None and spec.loader is not None,
            "cannot load saved-DTB parser")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def integer(cells):
    require(cells, "empty integer property")
    value = 0
    for cell in cells:
        value = value << 32 | cell
    return value


def decode_pairs(node, key, address_cells, size_cells):
    cells = node.cells(key)
    stride = address_cells + size_cells
    require(1 <= address_cells <= 2 and 1 <= size_cells <= 2 and
            cells and len(cells) % stride == 0,
            f"{node.path}:{key}: unsupported range cells")
    result = []
    for offset in range(0, len(cells), stride):
        start = integer(cells[offset:offset + address_cells])
        size = integer(cells[offset + address_cells:offset + stride])
        require(size > 0 and start + size <= 1 << 64,
                f"{node.path}:{key}: invalid range")
        result.append((start, size))
    return result


def inspect_fdt(raw, repo):
    require(len(raw) == LIVE_FDT_BYTES, "live FDT size differs")
    require(sha256(raw) == FDT_SHA256, "live FDT SHA-256 differs")
    parser = load_fdt_parser(repo)
    tree = parser.Fdt(raw)
    root = tree.nodes["/"]
    require(root.strings("model") == ["MT6897"] and
            "mediatek,MT6897" in root.strings("compatible"),
            "live FDT is not the captured MT6897 tree")
    address_cells = root.scalar("#address-cells")
    size_cells = root.scalar("#size-cells")
    memory_ranges = []
    for node in tree.nodes.values():
        if node.path == "/memory" or node.path.startswith("/memory@"):
            memory_ranges.extend(
                range_record(node.path, start, size)
                for start, size in decode_pairs(
                    node, "reg", address_cells, size_cells))
    require(memory_ranges == [range_record(
        "/memory", 0x40000000, 0x300000000)],
        "live FDT memory range differs")

    reserved_node = tree.nodes.get("/reserved-memory")
    require(reserved_node is not None and
            reserved_node.scalar("#address-cells") == 2 and
            reserved_node.scalar("#size-cells") == 2 and
            reserved_node.props.get("ranges", b"") == b"",
            "unsupported reserved-memory translation")
    fixed = []
    dynamic = []
    for node in tree.nodes.values():
        if node.parent is not reserved_node:
            continue
        flags = [name for name in ("no-map", "reusable")
                 if name in node.props]
        if "reg" in node.props:
            for start, size in decode_pairs(node, "reg", 2, 2):
                fixed.append(range_record(node.path, start, size,
                                          flags=flags))
        elif "size" in node.props:
            requested = integer(node.cells("size"))
            allowed = (decode_pairs(node, "alloc-ranges", 2, 2)
                       if "alloc-ranges" in node.props else
                       [(item["start"], item["bytes"])
                        for item in memory_ranges])
            dynamic.append({
                "name": node.path,
                "requested_bytes": requested,
                "requested_bytes_hex": hex(requested),
                "alignment": (integer(node.cells("alignment"))
                              if "alignment" in node.props else None),
                "allocation_ranges": [
                    range_record(node.path + ":alloc", start, size)
                    for start, size in allowed
                ],
                "flags": flags,
            })
        else:
            raise ValueError(f"{node.path}: missing reservation description")
    require(len(fixed) == 52 and len(dynamic) == 4,
            "live FDT reservation count differs")

    chosen = tree.nodes.get("/chosen")
    require(chosen is not None, "live FDT lacks /chosen")
    initrd_start = integer(chosen.cells("linux,initrd-start"))
    initrd_end = integer(chosen.cells("linux,initrd-end"))
    require(initrd_start == VENDOR_RAMDISK_ADDRESS and
            initrd_start < initrd_end,
            "live FDT initrd range differs")
    framebuffer = next(
        (item for item in fixed
         if item["name"] == "/reserved-memory/mblock-15-framebuffer"),
        None)
    require(framebuffer is not None and
            framebuffer["start"] == 0xFCC2F000 and
            framebuffer["bytes"] == 0x33D0000,
            "live FDT framebuffer reservation differs")

    reserve_offset = struct.unpack_from(">I", raw, 16)[0]
    memreserve_count = 0
    cursor = reserve_offset
    while cursor + 16 <= len(raw):
        start, size = struct.unpack_from(">QQ", raw, cursor)
        cursor += 16
        if start == 0 and size == 0:
            break
        memreserve_count += 1
    else:
        raise ValueError("unterminated FDT memreserve map")
    require(memreserve_count == 0, "live FDT memreserve map differs")

    return {
        "bytes": len(raw),
        "sha256": sha256(raw),
        "model": "MT6897",
        "compatible": "mediatek,MT6897",
        "memory": memory_ranges,
        "fixed_reservations": fixed,
        "dynamic_reservation_requests": dynamic,
        "fixed_reservation_count": len(fixed),
        "dynamic_reservation_count": len(dynamic),
        "header_memreserve_count": memreserve_count,
        "initrd": range_record(
            "/chosen/linux,initrd", initrd_start,
            initrd_end - initrd_start),
        "framebuffer": framebuffer,
        "self_physical_address_property_present": False,
    }


def parse_iomem(raw):
    try:
        text = raw.decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("iomem capture is not ASCII") from error
    ranges = []
    for line in text.splitlines():
        match = re.match(
            r"^\s*([0-9a-fA-F]+)-([0-9a-fA-F]+)\s*:\s*(.*?)\s*$",
            line)
        if not match:
            continue
        start = int(match.group(1), 16)
        end_inclusive = int(match.group(2), 16)
        require(end_inclusive >= start, "invalid iomem interval")
        ranges.append({
            "start": start,
            "end_inclusive": end_inclusive,
            "bytes": end_inclusive - start + 1,
            "label": match.group(3),
        })
    require(ranges, "iomem capture has no ranges")
    return ranges


def find_iomem(ranges, start, size, label):
    matches = [item for item in ranges
               if item["start"] == start and item["bytes"] == size and
               item["label"] == label]
    require(len(matches) == 1,
            f"iomem lacks exact {start:#x}+{size:#x} {label} range")
    return range_record("/proc/iomem:" + label, start, size,
                        label=label)


def inspect_iomem(raw, fdt_report, vendor_report):
    require(sha256(raw) == IOMEM_SHA256, "iomem SHA-256 differs")
    ranges = parse_iomem(raw)
    fdt = find_iomem(
        ranges, LIVE_FDT_ADDRESS, LIVE_FDT_RESERVED_BYTES, "reserved")
    initrd_bytes = align_up(fdt_report["initrd"]["bytes"], 4096)
    initrd = find_iomem(
        ranges, vendor_report["ramdisk_addr"], initrd_bytes, "reserved")
    containing_ram = [item for item in ranges
                      if item["label"] == "System RAM" and
                      item["start"] <= LIVE_FDT_ADDRESS and
                      LIVE_FDT_ADDRESS + LIVE_FDT_RESERVED_BYTES <=
                      item["start"] + item["bytes"]]
    require(len(containing_ram) == 1,
            "iomem does not place the live FDT in exactly one System RAM range")
    return {
        "sha256": sha256(raw),
        "live_fdt_reservation": fdt,
        "initrd_reservation": initrd,
        "containing_system_ram": range_record(
            "/proc/iomem:System RAM", containing_ram[0]["start"],
            containing_ram[0]["bytes"], label="System RAM"),
    }


def build_report(paths, blobs, repo):
    lk = inspect_lk(blobs["lk"])
    boot = inspect_boot(blobs["boot"])
    vendor = inspect_vendor_boot(blobs["vendor_boot"])
    fdt = inspect_fdt(blobs["fdt"], repo)
    iomem = inspect_iomem(blobs["iomem"], fdt, vendor)

    fixed_overlaps = [item for item in fdt["fixed_reservations"]
                      if overlaps(ANDROID_IMAGE_LOAD,
                                  LIVE_FDT_ADDRESS - ANDROID_IMAGE_LOAD,
                                  item["start"], item["bytes"])]
    require(not fixed_overlaps,
            "candidate Android Image window overlaps a fixed FDT reservation")
    dynamic_candidates = []
    for item in fdt["dynamic_reservation_requests"]:
        if any(overlaps(ANDROID_IMAGE_LOAD,
                        LIVE_FDT_ADDRESS - ANDROID_IMAGE_LOAD,
                        allowed["start"], allowed["bytes"])
               for allowed in item["allocation_ranges"]):
            dynamic_candidates.append(item["name"])

    return {
        "report_version": 1,
        "result": "PASS",
        "decision": "offline-layout-documented-phone-execution-blocked",
        "inputs": {
            name: receipt(paths[name], blobs[name])
            for name in ("lk", "boot", "vendor_boot", "fdt", "iomem")
        },
        "lk": lk,
        "android_image_contract": {
            "status": "verified-static-contract-not-runtime-pc-capture",
            "load_address": vendor["kernel_addr"],
            "load_address_hex": vendor["kernel_addr_hex"],
            "entry_address_from_text_offset":
                vendor["kernel_addr"] + boot["image"]["text_offset"],
            "entry_address_from_text_offset_hex": hex(
                vendor["kernel_addr"] + boot["image"]["text_offset"]),
            "vendor_boot": vendor,
            "stock_boot": boot,
            "final_initrd_note": (
                "the live initrd starts at vendor ramdisk_addr but is larger "
                "than vendor_ramdisk_size after LK assembles the final initrd"
            ),
            "runtime_entry_pc_captured": False,
        },
        "fdt_handoff": {
            "status": "corroborated-by-vendor-header-and-runtime-reservation",
            "address": LIVE_FDT_ADDRESS,
            "address_hex": hex(LIVE_FDT_ADDRESS),
            "live_bytes": fdt["bytes"],
            "live_bytes_hex": hex(fdt["bytes"]),
            "reserved_bytes": LIVE_FDT_RESERVED_BYTES,
            "reserved_bytes_hex": hex(LIVE_FDT_RESERVED_BYTES),
            "vendor_tags_addr_matches": vendor["tags_addr"] == LIVE_FDT_ADDRESS,
            "vendor_dtb_addr_matches": vendor["dtb_addr"] == LIVE_FDT_ADDRESS,
            "runtime_iomem_page_rounded_match": True,
            "incoming_x0_value_captured": False,
            "dtb_self_describes_physical_address": False,
        },
        "live_fdt": fdt,
        "runtime_iomem": iomem,
        "phone_layout": {
            "mode": "offline-link-and-layout-preflight-only",
            "image_base": ANDROID_IMAGE_LOAD,
            "image_base_hex": hex(ANDROID_IMAGE_LOAD),
            "image_ceiling_exclusive": LIVE_FDT_ADDRESS,
            "image_ceiling_exclusive_hex": hex(LIVE_FDT_ADDRESS),
            "maximum_image_bytes_before_fdt":
                LIVE_FDT_ADDRESS - ANDROID_IMAGE_LOAD,
            "maximum_image_bytes_before_fdt_hex": hex(
                LIVE_FDT_ADDRESS - ANDROID_IMAGE_LOAD),
            "expected_entry_x0": LIVE_FDT_ADDRESS,
            "expected_entry_x0_hex": hex(LIVE_FDT_ADDRESS),
            "fixed_reservation_overlap": False,
            "dynamic_allocation_ranges_intersecting_window":
                dynamic_candidates,
            "source_capsule_placement_verified": False,
            "actual_lk_entry_registers_captured": False,
            "execution_authorized": False,
        },
        "claims": {
            "exact_lk_partition_verified": True,
            "lk_self_bootstrap_mapping_verified": True,
            "lk_runtime_pc_register_captured": False,
            "android_image_static_load_contract_verified": True,
            "android_image_runtime_entry_pc_captured": False,
            "fdt_handoff_address_corroborated": True,
            "fdt_incoming_x0_captured": False,
            "ram_and_reserved_memory_parsed": True,
            "phone_layout_preflight_permitted": True,
            "phone_execution_ready": False,
        },
        "unknowns": [
            "the numeric LK-to-Image entry PC has not been captured at runtime",
            "the numeric incoming x0 FDT pointer has not been captured at runtime",
            "the DTB does not describe its own physical address",
            "dynamic reserved-memory final allocations are not established here",
            "a transport/capsule placement for a phone image is not established",
        ],
        "safety": {
            "local_files_only": True,
            "phone_access": False,
            "adb_access": False,
            "fastboot_access": False,
            "partition_write": False,
            "flash": False,
            "mmio_access": False,
            "firmware_execution": False,
            "jump_to_xnu": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lk", type=Path, required=True)
    parser.add_argument("--boot", type=Path, required=True)
    parser.add_argument("--vendor-boot", type=Path, required=True)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--iomem", type=Path, required=True)
    parser.add_argument("--atf", type=Path,
                        help="optionally audit the pinned saved BL31 binary")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.output.exists():
        parser.error("preserve existing output")
    paths = {
        "lk": arguments.lk,
        "boot": arguments.boot,
        "vendor_boot": arguments.vendor_boot,
        "fdt": arguments.fdt,
        "iomem": arguments.iomem,
    }
    try:
        blobs = {name: path.resolve().read_bytes()
                 for name, path in paths.items()}
        report = build_report(paths, blobs, Path(__file__).resolve().parent.parent)
        if arguments.atf is not None:
            atf = arguments.atf.resolve().read_bytes()
            report["captured_bl31_handoff"] = inspect_bl31_handoff(atf)
            report["inputs"]["atf"] = receipt(arguments.atf, atf)
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        with arguments.output.open("x", encoding="utf-8") as output:
            output.write(json.dumps(report, indent=2) + "\n")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, "LK handoff audit failed: " + str(error) + "\n")
    print("duchamp-lk-handoff: PASS "
          f"lk={LK_PHYSICAL_BASE:#x} image={ANDROID_IMAGE_LOAD:#x} "
          f"fdt={LIVE_FDT_ADDRESS:#x} execution=blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
