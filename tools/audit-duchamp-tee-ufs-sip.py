#!/usr/bin/env python3
"""Statically audit the captured Duchamp BL31 UFS SiP handler.

This command reads the local tee_a capture only.  It pins the service
descriptor, dispatcher and selector branches for REFCLK, MTCMOS and MCQ.  It
does not execute the firmware, issue an SMC, access MMIO or prove that a zero
firmware reply means the requested physical effect occurred.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct


TEE_A_BYTES = 5 * 1024 * 1024
TEE_A_SHA256 = "37d7d5acbe02289465af9702cbcafb1986394332a3462badda398556d32e587d"
ATF_BYTES = 0xE8E78
ATF_SHA256 = "716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e"
ATF_LOAD_BASE = 0x48800000

UFS_FID_FAST32 = 0x82000276
UFS_FID_FAST64 = 0xC2000276
UFS_HANDLER = 0x48845008
UFS_NAME = "MTK_SIP_KERNEL_UFS_CONTROL"
UFS_NAME_ADDRESS = 0x4886196D
UFS_RUNTIME_INDEX_ADDRESS = 0x48866164

SELECTOR_REFCLK = 8
SELECTOR_MTCMOS = 0x200
SELECTOR_MCQ = 0x400

PINNED_REGIONS = {
    "smc_dispatch": (0x2B198, "c94e80520940b8721f00096b80240054"
                     "097480520940b8721f00096ba1260054"),
    "smc_handler_index": (0x2B634, "c80100f009c9c279e8031faa4902f837"
                          "0a0700b04a39c3793f010a6bca010054"),
    "ufs_handler_entry": (0x45008, "fd7bbda9f44f02a9f30301aae80300aa"
                          "000080921ffd00f1f65701a9fd030091"
                          "6c020054090500d13f1d00f128040054"
                          "680000b008593f918a0000100b796978"),
    "selector_decode": (0x45080, "1f0104f1002500541f0108f1000b0054"
                        "1f0110f1a1240054480600f008516839"
                        "660000141f0101f1e00b00541f0102f1"),
    "refclk_branch": (0x45170, "5f040071200a0054621d0035531d0034"
                      "480600f0085568391f050071201f0054"
                      "530600f073620091e00313aa6615ff97"),
    "mtcmos_on_branch": (0x451EC, "930500b420008052a1d3ff97360600d0"
                         "340600d0f503002a94623b91c8de4eb9"
                         "a8140034880640f9e00314aa01208052"
                         "00013fd6a6000014141800b4bc6bff97"),
    "mtcmos_off_branch": (0x4529C, "e0031f2a5bd4ff97f403002ae0031f2a"
                          "73d3ff971500140b9000001473130035"
                          "480600f008516839"),
    "mcq_result_branch": (0x45238, "e0031faa880200f9ba000014880240b9"
                          "f57c801208011f32"),
    "known_selector_return": (0x45524, "e0031faaf44f42a9f65741a9fd7bc3a8"
                              "c0035fd6"),
    "selector_jump_table": (0x52FD6, "00002a0036012d003601360136014800"),
    "ufs_service_descriptor": (0x66020, "085084480000000076020082760200c2"
                               "6d198648000000006461864800000000"),
    "mtcmos_control_0_entry": (0x3A078, "fd7bbda9f44f02a914c283521480a372"
                               "2a008052b30600b0894238d1ca62a172"
                               "1f040071f50b00f9fd0300917f9209b9"
                               "2a0100b9c0020054e803002ae0031f2a"),
    "mtcmos_control_0_status": (0x3A104, "880240b96800f036880240b98801f837"
                                "880240b9f57c801208011e32880200b9"
                                "880240b90801f037200080522f2b0094"
                                "b506003163ffff541100001400008012"),
    "mtcmos_control_1_entry": (0x3A40C, "fd7bbda9f44f02a993c283521380a372"
                               "2a008052b40600b0695238d1ca62a172"
                               "1f040071f50b00f9fd0300919f9209b9"
                               "2a0100b960060054e803002ae0031f2a"),
    "mtcmos_control_1_status": (0x3A50C, "680240b96800f036680240b98801f837"
                                "680240b9f57c801208011e32680200b9"
                                "680240b90801f037200080522d2a0094"
                                "b506003163ffff541100001400008012"
                                "33000014889249b94006805208050011"
                                "889209b9232a0094680240b908011d32"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def u16(raw, offset):
    require(offset >= 0 and offset + 2 <= len(raw), "truncated 16-bit field")
    return struct.unpack_from("<H", raw, offset)[0]


def s16(raw, offset):
    require(offset >= 0 and offset + 2 <= len(raw), "truncated signed field")
    return struct.unpack_from("<h", raw, offset)[0]


def u32(raw, offset):
    require(offset >= 0 and offset + 4 <= len(raw), "truncated 32-bit field")
    return struct.unpack_from("<I", raw, offset)[0]


def u64(raw, offset):
    require(offset >= 0 and offset + 8 <= len(raw), "truncated 64-bit field")
    return struct.unpack_from("<Q", raw, offset)[0]


def c_string(raw, offset, maximum=128):
    require(offset >= 0 and offset < len(raw), "string pointer outside atf")
    end = raw.find(b"\0", offset, min(len(raw), offset + maximum))
    require(end >= 0, "unterminated service name")
    try:
        return raw[offset:end].decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("non-ASCII service name") from error


def receipt(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def decode_conditional_target(pc, word):
    require(word & 0xFF000010 == 0x54000000,
            "instruction is not an AArch64 conditional branch")
    immediate = (word >> 5) & 0x7FFFF
    if immediate & (1 << 18):
        immediate -= 1 << 19
    return pc + immediate * 4


def decode_bl_target(pc, word):
    require(word & 0xFC000000 == 0x94000000,
            "instruction is not an AArch64 BL")
    immediate = word & 0x03FFFFFF
    if immediate & (1 << 25):
        immediate -= 1 << 26
    return pc + immediate * 4


def decode_movz_movk32(movz, movk):
    require(movz & 0x7F800000 == 0x52800000,
            "instruction is not a 32-bit MOVZ")
    require(movk & 0x7F800000 == 0x72800000,
            "instruction is not a 32-bit MOVK")
    require(movz & 0x1F == movk & 0x1F,
            "move-wide destination registers differ")
    low_shift = ((movz >> 21) & 1) * 16
    high_shift = ((movk >> 21) & 1) * 16
    value = ((movz >> 5) & 0xFFFF) << low_shift
    mask = 0xFFFF << high_shift
    value = (value & ~mask) | (((movk >> 5) & 0xFFFF) << high_shift)
    return value & 0xFFFFFFFF


def audit_atf(atf, expected_bytes=None, expected_sha256=None):
    atf_receipt = receipt(atf)
    if expected_bytes is not None:
        require(atf_receipt["bytes"] == expected_bytes, "atf size differs")
    if expected_sha256 is not None:
        require(atf_receipt["sha256"] == expected_sha256, "atf SHA-256 differs")

    region_receipts = {}
    for name, (offset, encoded) in PINNED_REGIONS.items():
        expected = bytes.fromhex(encoded)
        require(offset + len(expected) <= len(atf),
                "truncated pinned region: " + name)
        actual = atf[offset:offset + len(expected)]
        require(actual == expected, "pinned BL31 region differs: " + name)
        region_receipts[name] = {
            "offset": offset,
            "bytes": len(expected),
            "sha256": hashlib.sha256(actual).hexdigest(),
        }

    descriptor = 0x66020
    handler = u64(atf, descriptor)
    fid32 = u32(atf, descriptor + 8)
    fid64 = u32(atf, descriptor + 12)
    name_address = u64(atf, descriptor + 16)
    index_address = u64(atf, descriptor + 24)
    require(handler == UFS_HANDLER, "UFS handler pointer differs")
    require(fid32 == UFS_FID_FAST32 and fid64 == UFS_FID_FAST64,
            "UFS service function IDs differ")
    require(name_address == UFS_NAME_ADDRESS, "UFS service-name pointer differs")
    require(index_address == UFS_RUNTIME_INDEX_ADDRESS,
            "UFS runtime-index pointer differs")
    name_offset = name_address - ATF_LOAD_BASE
    require(c_string(atf, name_offset) == UFS_NAME, "UFS service name differs")
    index_offset = index_address - ATF_LOAD_BASE
    require(s16(atf, index_offset) == -1,
            "static UFS service index is not the expected registration sentinel")

    dispatch_pc = ATF_LOAD_BASE + 0x2B1A4
    dispatch_target = decode_conditional_target(dispatch_pc, u32(atf, 0x2B1A4))
    require(dispatch_target == ATF_LOAD_BASE + 0x2B634,
            "UFS dispatch target differs")

    jump_base = ATF_LOAD_BASE + 0x45050
    refclk_entry = u16(atf, 0x52FD6 + (SELECTOR_REFCLK - 1) * 2)
    refclk_target = jump_base + refclk_entry * 4
    require(refclk_target == ATF_LOAD_BASE + 0x45170,
            "REFCLK selector target differs")

    mtcmos_branch_pc = ATF_LOAD_BASE + 0x4508C
    mtcmos_target = decode_conditional_target(
        mtcmos_branch_pc, u32(atf, 0x4508C)
    )
    require(mtcmos_target == ATF_LOAD_BASE + 0x451EC,
            "MTCMOS selector target differs")
    mtcmos_on_call = decode_bl_target(ATF_LOAD_BASE + 0x451F4,
                                      u32(atf, 0x451F4))
    mtcmos_off_call = decode_bl_target(ATF_LOAD_BASE + 0x452A0,
                                       u32(atf, 0x452A0))
    mtcmos_followup_call = decode_bl_target(ATF_LOAD_BASE + 0x452AC,
                                            u32(atf, 0x452AC))
    require(mtcmos_on_call == ATF_LOAD_BASE + 0x3A078,
            "MTCMOS on helper target differs")
    require(mtcmos_off_call == ATF_LOAD_BASE + 0x3A40C,
            "MTCMOS off helper target differs")
    require(mtcmos_followup_call == ATF_LOAD_BASE + 0x3A078,
            "MTCMOS follow-up helper target differs")

    mcq_reject_pc = ATF_LOAD_BASE + 0x45094
    mcq_reject_target = decode_conditional_target(mcq_reject_pc,
                                                   u32(atf, 0x45094))
    require(mcq_reject_target == ATF_LOAD_BASE + 0x45528,
            "MCQ selector reject target differs")
    mcq_target = ATF_LOAD_BASE + 0x45098

    control_0 = decode_movz_movk32(u32(atf, 0x3A080), u32(atf, 0x3A084))
    control_1 = decode_movz_movk32(u32(atf, 0x3A414), u32(atf, 0x3A418))
    unlock_value_0 = decode_movz_movk32(u32(atf, 0x3A088),
                                        u32(atf, 0x3A094))
    unlock_value_1 = decode_movz_movk32(u32(atf, 0x3A41C),
                                        u32(atf, 0x3A428))
    require(control_0 == 0x1C001E10 and control_1 == 0x1C001E14,
            "MTCMOS control addresses differ")
    require(unlock_value_0 == 0x0B160001
            and unlock_value_1 == 0x0B160001,
            "MTCMOS unlock value differs")

    return {
        "report_version": 1,
        "passed": True,
        "atf": atf_receipt,
        "service": {
            "name": UFS_NAME,
            "descriptor_offset": descriptor,
            "handler_address": f"0x{handler:08x}",
            "fast32_function_id": f"0x{fid32:08x}",
            "fast64_function_id": f"0x{fid64:08x}",
            "static_registration_index": -1,
            "dispatcher_target": f"0x{dispatch_target:08x}",
        },
        "selectors": {
            "refclk": {
                "value": SELECTOR_REFCLK,
                "target": f"0x{refclk_target:08x}",
                "pre_post_stage_checks_present": True,
            },
            "mtcmos": {
                "value": SELECTOR_MTCMOS,
                "target": f"0x{mtcmos_target:08x}",
                "body_present": True,
                "on_helper_target": f"0x{mtcmos_on_call:08x}",
                "off_helper_target": f"0x{mtcmos_off_call:08x}",
                "followup_helper_target": f"0x{mtcmos_followup_call:08x}",
            },
            "mcq": {
                "value": SELECTOR_MCQ,
                "target": f"0x{mcq_target:08x}",
                "state_load_and_result_store_present": True,
            },
        },
        "mtcmos_mmio": {
            "unlock_register": "0x1c001000",
            "unlock_value": "0x0b160001",
            "control_registers": [
                f"0x{control_0:08x}",
                f"0x{control_1:08x}",
            ],
            "polled_status_bits": [30, 31],
            "captured_bl31_direct_mmio_paths_present": True,
            "safe_xnu_direct_readback_authorized": False,
        },
        "pinned_regions": region_receipts,
        "claims": {
            "captured_bl31_ufs_service_descriptor_verified": True,
            "saved_client_function_id_dispatch_verified": True,
            "saved_refclk_selector_dispatch_verified": True,
            "saved_mtcmos_selector_dispatch_verified": True,
            "saved_mcq_selector_dispatch_verified": True,
            "mtcmos_body_present_in_captured_binary": True,
            "known_selector_common_zero_return_present": True,
            "captured_bl31_mtcmos_mmio_paths_verified": True,
            "zero_reply_proves_physical_effect": False,
            "direct_xnu_mtcmos_mmio_authorized": False,
            "runtime_smc_return_effect_contract_verified": False,
            "physical_resource_ownership_verified": False,
            "xnu_physical_ufs_ready": False,
        },
        "safety": {
            "local_file_only": True,
            "firmware_executed": False,
            "smc_execution": False,
            "mmio_access": False,
            "adb_access_by_this_tool": False,
            "phone_write": False,
            "partition_write": False,
            "fastboot_access": False,
        },
        "scope": (
            "static dispatch and branch evidence only; known-selector paths "
            "share a zero-return exit and direct secure-firmware MMIO paths "
            "do not authorize XNU MMIO, so runtime effects cannot be inferred"
        ),
    }


def load_tee_inspector():
    path = Path(__file__).resolve().with_name("inspect-duchamp-tee.py")
    spec = importlib.util.spec_from_file_location("duchamp_tee_inspector", path)
    require(spec is not None and spec.loader is not None,
            "cannot load tee inspector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tee_image", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing output")
    try:
        tee = args.tee_image.resolve().read_bytes()
        inspector = load_tee_inspector()
        tee_report = inspector.inspect_image(tee, TEE_A_BYTES, TEE_A_SHA256)
        start = tee_report["atf_entry"]["payload_start"]
        end = tee_report["atf_entry"]["payload_end_exclusive"]
        report = audit_atf(tee[start:end], ATF_BYTES, ATF_SHA256)
        report["tee_a"] = tee_report["input"]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n",
                               encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.exit(1, "UFS SiP audit failed: " + str(error) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
