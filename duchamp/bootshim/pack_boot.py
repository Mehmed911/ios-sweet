#!/usr/bin/env python3
import argparse
import hashlib
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

PAGE_SIZE = 4096
HEADER_SIZE_V4 = 1584
CMDLINE_OFFSET = 44
CMDLINE_SIZE = 1536
SIGNATURE_SIZE_OFFSET = 1580
AVB_FOOTER_SIZE = 64
AVB_FOOTER_FORMAT = ">4sIIQQQ28s"


def aligned(value):
    return (value + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1)


def read_u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data, offset, value):
    struct.pack_into("<I", data, offset, value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock-boot", required=True, type=Path)
    parser.add_argument("--kernel", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--preserve-avb-container", action="store_true",
        help="preserve the stock full-size AVB container and signed vbmeta; "
             "the payload hash will intentionally no longer verify")
    parser.add_argument(
        "--lz4-legacy", action="store_true",
        help="compress the ARM64 Image as an LZ4 legacy frame, matching the "
             "captured Duchamp stock boot kernel format")
    args = parser.parse_args()

    stock = args.stock_boot.read_bytes()
    kernel = args.kernel.read_bytes()
    if len(stock) < PAGE_SIZE or stock[:8] != b"ANDROID!":
        raise SystemExit("stock image is not an Android boot image")
    if read_u32(stock, 40) != 4 or read_u32(stock, 20) != HEADER_SIZE_V4:
        raise SystemExit("stock image is not boot header v4")
    if read_u32(stock, 12) != 0:
        raise SystemExit("stock boot ramdisk is not empty")
    if read_u32(stock, SIGNATURE_SIZE_OFFSET) != 0:
        raise SystemExit("stock boot signature is not empty")
    if not kernel or len(kernel) > 64 * 1024 * 1024:
        raise SystemExit("diagnostic kernel size is invalid")
    if kernel[56:60] != b"ARM\x64":
        raise SystemExit("diagnostic kernel lacks the ARM64 Linux Image magic")

    if args.lz4_legacy:
        lz4 = shutil.which("lz4")
        if not lz4:
            raise SystemExit("lz4 is required for --lz4-legacy")
        with tempfile.TemporaryDirectory(prefix="duchamp-lz4-") as temp:
            source = Path(temp) / "Image"
            compressed = Path(temp) / "Image.lz4"
            source.write_bytes(kernel)
            subprocess.run(
                [lz4, "-l", "-f", str(source), str(compressed)],
                check=True, stdout=subprocess.DEVNULL)
            kernel = compressed.read_bytes()
        if kernel[:4] != bytes.fromhex("02214c18"):
            raise SystemExit("lz4 did not produce a legacy frame")
        print("kernel_format=lz4-legacy")

    header = bytearray(stock[:HEADER_SIZE_V4])
    write_u32(header, 8, len(kernel))
    write_u32(header, 12, 0)
    write_u32(header, SIGNATURE_SIZE_OFFSET, 0)
    payload = header + bytes(PAGE_SIZE - len(header)) + kernel
    payload += bytes(aligned(len(payload)) - len(payload))
    if args.preserve_avb_container:
        if len(stock) < AVB_FOOTER_SIZE:
            raise SystemExit("stock image is too small for an AVB footer")
        footer = struct.unpack(
            AVB_FOOTER_FORMAT, stock[-AVB_FOOTER_SIZE:])
        magic, major, minor, original_size, vbmeta_offset, vbmeta_size, _ = footer
        if magic != b"AVBf" or major != 1 or minor != 0:
            raise SystemExit("stock image lacks the expected AVB 1.0 footer")
        if original_size != vbmeta_offset or not vbmeta_size:
            raise SystemExit("stock AVB layout is not the expected hash-footer form")
        if vbmeta_offset + vbmeta_size > len(stock) - AVB_FOOTER_SIZE:
            raise SystemExit("stock AVB metadata lies outside the image")
        if len(payload) > original_size:
            raise SystemExit("diagnostic payload overlaps stock AVB metadata")
        output = bytearray(stock)
        output[:original_size] = bytes(original_size)
        output[:len(payload)] = payload
        output = bytes(output)
        print(f"avb_container=preserved partition_size={len(output)}")
        print(f"avb_vbmeta_offset={vbmeta_offset} avb_vbmeta_size={vbmeta_size}")
        print("avb_payload_hash=expected-mismatch")
    else:
        output = payload
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(output)

    cmdline = header[CMDLINE_OFFSET:CMDLINE_OFFSET + CMDLINE_SIZE].split(b"\0", 1)[0]
    print(f"header_version=4 header_size={HEADER_SIZE_V4}")
    print(f"kernel_size={len(kernel)} ramdisk_size=0 signature_size=0")
    print(f"cmdline={cmdline.decode('ascii', errors='replace')!r}")
    print(f"image_size={len(output)}")
    print(f"sha256={hashlib.sha256(output).hexdigest()}")


if __name__ == "__main__":
    main()
