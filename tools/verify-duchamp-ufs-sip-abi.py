#!/usr/bin/env python3
"""Bind the installed Duchamp UFS client to the captured BL31 SiP ABI.

This is an offline verifier. It proves a static ABI evidence chain only; it
does not execute SMC, access MMIO, inspect firewall state, authorize XNU, or
enable the physical UFS backend.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

import duchamp_saved_ufs as saved


REPORT_VERSION = 1
SAVED_AUDIT_SHA256 = (
    "cb4e209b9b7df2f8a1f3b443e963d3e1fce2a3ea45d23599975454fee7456fa9"
)
LIVE_RUNTIME_SHA256 = (
    "fb1fa60b1b6df4f50f7794520be959ba7997f9433cea0f23dc818df9b5681660"
)
BL31_AUDIT_SHA256 = (
    "65e4a5cdd2085c2e2bb48ad9829109f8e39b7a260669074ab59427419b5d110c"
)
BL31_IDENTITY_SHA256 = (
    "1a9060eec770e72f70d1e51b2d0e8b86ab5be45b0ccd6ca73ca6b345171dcba2"
)
MODULE_SHA256 = (
    "7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493"
)
MODULE_BYTES = 14657944
MODULE_BUILD_ID = "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84"
RUNTIME_BUILD_ID_NOTE_SHA256 = (
    "43e40b73715e22b8816df5c5d4979bbda7453d4dd30fedc7f38a99f278d14eb3"
)
ATF_SHA256 = "716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e"
ATF_BYTES = 953976
SERVICE_ID = "0xc2000276"
SELECTORS = {"refclk": 8, "mtcmos": 512, "mcq": 1024}
PINNED_REPORT_SHA256 = (
    "54c963ea6895717b937c1793685f2ebd70c48f9969ff168b2e63d6621accf103"
)

EXPECTED_FRAGMENTS = [
    {
        "name": "mtcmos0", "section": ".text", "begin": "0x23c8",
        "call": "0x23f4",
        "sha256": "a0448d891d1a4bc302bbb351e83a597730b3975295aee7a12675686b10666f86",
        "bytes": 44, "selector": 512, "on": 0, "stage": 0,
    },
    {
        "name": "mtcmos1", "section": ".text", "begin": "0x23f8",
        "call": "0x2420",
        "sha256": "75e79cb3b92488f084f2f2a4bb7a693ad8d2b5136c291446714a6917607c5dbc",
        "bytes": 40, "selector": 512, "on": 1, "stage": 0,
    },
    {
        "name": "refpre", "section": ".text", "begin": "0x4b54",
        "call": "0x4b80",
        "sha256": "7705cbd12240750470316decc5e29f585658f5693d144bcecfd9ef4301d42585",
        "bytes": 44, "selector": 8, "on": None, "stage": 0,
    },
    {
        "name": "refpost", "section": ".text", "begin": "0x4c48",
        "call": "0x4c74",
        "sha256": "23db2fc1566ecd9859e0911689b86aadaa750047c8554e3c81e7877cffc858a6",
        "bytes": 44, "selector": 8, "on": None, "stage": 1,
    },
    {
        "name": "dma", "section": ".text", "begin": "0x12a34",
        "end": "0x12a6c",
        "sha256": "da798be9d4f6093314c2272f698466cd43b852a3b43944f20eea7a0ce2f318a3",
        "bytes": 56,
    },
    {
        "name": "dma64", "section": ".text", "begin": "0x1303c",
        "end": "0x13048",
        "sha256": "f71cde82307cc5ec7e1427ab1dc6589849fcc0605de21eeafe8618f8d431437c",
        "bytes": 12,
    },
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_json(raw, expected_sha256, label):
    require(sha256(raw) == expected_sha256, label + " SHA-256 differs")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(label + " is not valid UTF-8 JSON") from error
    require(isinstance(value, dict), label + " is not a JSON object")
    return value


def load_client_auditor():
    path = Path(__file__).with_name("audit-duchamp-firmware-client.py")
    spec = importlib.util.spec_from_file_location("duchamp_ufs_client_audit", path)
    require(spec is not None and spec.loader is not None,
            "cannot load saved UFS client auditor")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


def parse_build_id_note(raw):
    require(len(raw) >= 16, "truncated GNU build ID")
    namesz, descsz, note_type = struct.unpack_from("<III", raw)
    name_end = 12 + namesz
    desc_offset = (name_end + 3) & ~3
    desc_end = desc_offset + descsz
    require(note_type == 3 and namesz == 4 and raw[12:name_end] == b"GNU\0",
            "unexpected GNU build ID layout")
    require(descsz == 20 and desc_end == len(raw),
            "unexpected GNU build ID extent")
    return raw[desc_offset:desc_end].hex()


def word(text, offset):
    return saved.unpack(text, offset, "<I")[0]


def verify_client_instructions(elf):
    """Verify FID construction, selectors and argument roles in raw code."""
    text = elf.section_data(elf.sections[".text"])
    # Every path builds x0 as 0xc2000276 using this MOVZ/MOVK pair.
    for low, high in ((0x23C8, 0x23E8), (0x23F8, 0x2410),
                      (0x4B54, 0x4B70), (0x4C48, 0x4C60),
                      (0x1E54, 0x1E74)):
        require(word(text, low) == 0x52804EC0 and
                word(text, high) == 0x72B84000,
                "saved client SiP function ID construction differs")
    require(word(text, 0x23EC) == 0x52804001 and
            word(text, 0x2414) == 0x52804001,
            "saved client MTCMOS selector differs")
    require(word(text, 0x4B74) == 0x52800101 and
            word(text, 0x4C64) == 0x52800101,
            "saved client REFCLK selector differs")
    require(word(text, 0x1E78) == 0x52808001,
            "saved client MCQ selector differs")
    require(word(text, 0x2418) == 0x52800022,
            "saved client MTCMOS on argument differs")
    require(word(text, 0x4C6C) == 0x52800023,
            "saved client REFCLK post-stage argument differs")
    return {
        "function_id": SERVICE_ID,
        "function_id_construction": "mov w0,#0x276; movk w0,#0xc200,lsl#16",
        "selectors": SELECTORS,
        "argument_roles": {
            "mtcmos": "x1=512, x2=off/on, remaining unused arguments zero",
            "refclk": "x1=8, x2=state, x3=pre/post",
            "mcq": "x1=1024, x2..x7 zero, result returned through result+8",
        },
    }


def build_report(saved_audit_raw, live_runtime_raw, bl31_audit_raw,
                 bl31_identity_raw, module_raw, runtime_build_id_note_raw,
                 atf_raw):
    saved_audit = load_json(
        saved_audit_raw, SAVED_AUDIT_SHA256, "saved UFS audit"
    )
    live_runtime = load_json(
        live_runtime_raw, LIVE_RUNTIME_SHA256, "live runtime evidence"
    )
    bl31_audit = load_json(
        bl31_audit_raw, BL31_AUDIT_SHA256, "BL31 UFS audit"
    )
    bl31_identity = load_json(
        bl31_identity_raw, BL31_IDENTITY_SHA256, "BL31 identity evidence"
    )
    require(sha256(module_raw) == MODULE_SHA256,
            "saved UFS module SHA-256 differs")
    require(len(module_raw) == MODULE_BYTES, "saved UFS module size differs")
    require(sha256(runtime_build_id_note_raw) ==
                RUNTIME_BUILD_ID_NOTE_SHA256 and
            len(runtime_build_id_note_raw) == 36,
            "runtime UFS build ID note differs")
    require(sha256(atf_raw) == ATF_SHA256 and len(atf_raw) == ATF_BYTES,
            "captured ATF payload differs")

    module_entry = saved_audit.get("modules", {}).get("ufs-mediatek-mod.ko", {})
    require(saved_audit.get("audit_complete") is True and
            module_entry.get("sha256") == MODULE_SHA256 and
            module_entry.get("bytes") == MODULE_BYTES and
            saved_audit.get("saved_client_fragments") == EXPECTED_FRAGMENTS,
            "saved UFS audit provenance or fragments differ")
    require(saved_audit.get("installed_firmware_contract_verified") is False and
            saved_audit.get("physical_backend_enabled") is False,
            "saved UFS audit overclaims physical readiness")

    elf = saved.Elf(module_raw)
    try:
        saved_build_id_note = elf.section_data(
            elf.sections[".note.gnu.build-id"]
        )
    except KeyError as error:
        raise ValueError("saved UFS module lacks GNU build ID") from error
    build_id = parse_build_id_note(saved_build_id_note)
    runtime_build_id = parse_build_id_note(runtime_build_id_note_raw)
    require(build_id == MODULE_BUILD_ID, "saved UFS module build ID differs")
    require(runtime_build_id == MODULE_BUILD_ID and
            runtime_build_id_note_raw == saved_build_id_note,
            "running and saved UFS module build ID notes differ")
    unused_fragments, fragment_receipts = elf.fragments()
    require(fragment_receipts == EXPECTED_FRAGMENTS,
            "raw UFS module fragments differ from saved audit")
    client_audit = load_client_auditor().inspect_client(elf)
    mcq = client_audit.get("mcq_query", {})
    require(client_audit.get("module_sha256") == MODULE_SHA256 and
            mcq.get("function_id") == SERVICE_ID and
            mcq.get("selector") == SELECTORS["mcq"] and
            mcq.get("argument_registers_2_through_7") == 0 and
            mcq.get("fragment_sha256") ==
                "9fa2c04bc9124348dde1bb17b7bba48d317af41c42b7f04ced457a852b10644d",
            "saved UFS client MCQ call differs")
    client_abi = verify_client_instructions(elf)

    runtime_result = live_runtime.get("result", {})
    runtime_firmware = live_runtime.get("firmware", {})
    installed = live_runtime.get("runtime", {}).get("ufs", {}).get(
        "installed_module", {}
    )
    saved_vendor = installed.get("saved_vendor_module", {})
    require(live_runtime.get("report_version") == 2 and
            runtime_result.get("passed") is True,
            "live runtime evidence did not pass")
    require(installed.get("name") == "ufs_mediatek_mod" and
            installed.get("state") == "Live" and
            installed.get("gnu_build_id") == MODULE_BUILD_ID and
            saved_vendor.get("sha256") == MODULE_SHA256 and
            saved_vendor.get("bytes") == MODULE_BYTES and
            saved_vendor.get("gnu_build_id") == MODULE_BUILD_ID and
            saved_vendor.get("build_id_match_verified") is True and
            runtime_firmware.get(
                "installed_ufs_client_binary_identity_verified") is True,
            "running UFS module identity does not match saved vendor module")
    require(runtime_firmware.get("installed_ufs_sip_effect_contract_verified")
            is False and
            runtime_firmware.get("physical_resource_ownership_verified")
            is False,
            "live runtime evidence overclaims firmware effects or ownership")
    runtime_safety = live_runtime.get("safety", {})
    require(runtime_safety.get("offline_analysis_only") is True and
            runtime_safety.get("phone_write") is False and
            runtime_safety.get("partition_access") is False and
            runtime_safety.get("mmio_access") is False,
            "live runtime evidence safety differs")

    service = bl31_audit.get("service", {})
    selectors = bl31_audit.get("selectors", {})
    claims = bl31_audit.get("claims", {})
    require(bl31_audit.get("report_version") == 1 and
            bl31_audit.get("passed") is True and
            service.get("fast64_function_id") == SERVICE_ID,
            "captured BL31 UFS service differs")
    require({name: selectors.get(name, {}).get("value")
             for name in SELECTORS} == SELECTORS,
            "captured BL31 selectors differ")
    for key in (
        "captured_bl31_ufs_service_descriptor_verified",
        "saved_client_function_id_dispatch_verified",
        "saved_refclk_selector_dispatch_verified",
        "saved_mtcmos_selector_dispatch_verified",
        "saved_mcq_selector_dispatch_verified",
    ):
        require(claims.get(key) is True, "missing BL31 static proof: " + key)
    require(claims.get("runtime_smc_return_effect_contract_verified") is False and
            claims.get("physical_resource_ownership_verified") is False and
            claims.get("direct_xnu_mtcmos_mmio_authorized") is False,
            "BL31 audit overclaims runtime effect or authorization")
    bl31_safety = bl31_audit.get("safety", {})
    require(bl31_safety.get("local_file_only") is True and
            bl31_safety.get("firmware_executed") is False and
            bl31_safety.get("smc_execution") is False and
            bl31_safety.get("mmio_access") is False and
            bl31_safety.get("phone_write") is False and
            bl31_safety.get("partition_write") is False,
            "BL31 audit safety differs")

    identity_proofs = bl31_identity.get("proofs", {})
    identity_capture = bl31_identity.get("capture", {})
    require(bl31_identity.get("report_version") == 1 and
            bl31_identity.get("passed") is True and
            bl31_identity.get("verdict") ==
                "installed-bl31-runtime-identity-matched" and
            identity_proofs.get("installed_firmware_identity_proven") is True,
            "running BL31 identity evidence differs")
    require(identity_capture.get("tee_a_sha256") ==
                bl31_audit.get("tee_a", {}).get("sha256") and
            identity_capture.get("atf_sha256") ==
                bl31_audit.get("atf", {}).get("sha256") and
            identity_capture.get("atf_sha256") == sha256(atf_raw),
            "BL31 identity and static audit samples differ")
    require(identity_proofs.get("installed_binary_byte_equivalence_proven")
            is False and
            identity_proofs.get("runtime_smc_effect_contract_proven") is False and
            identity_proofs.get("physical_resource_ownership_proven") is False,
            "BL31 identity evidence overclaims its scope")

    return {
        "report_version": REPORT_VERSION,
        "passed": True,
        "target": {"device": "duchamp", "soc": "mt6897", "engine": "ufs"},
        "client": {
            "running_module": "ufs_mediatek_mod",
            "running_gnu_build_id": MODULE_BUILD_ID,
            "saved_module_sha256": MODULE_SHA256,
            "saved_module_bytes": MODULE_BYTES,
            "running_to_saved_build_id_note_byte_match": True,
            "smccc_call_relocation": "__arm_smccc_smc",
            "abi": client_abi,
            "mcq_fragment_sha256": mcq["fragment_sha256"],
            "smc_fragment_receipts": EXPECTED_FRAGMENTS[:4],
        },
        "firmware": {
            "service_name": service.get("name"),
            "fast64_function_id": SERVICE_ID,
            "selectors": SELECTORS,
            "captured_bl31_dispatch_proven": True,
            "running_bl31_identity": bl31_identity.get("identity"),
            "running_identity_matches_captured_sample": True,
        },
        "proofs": {
            "running_client_build_id_match_proven": True,
            "running_client_byte_equivalence_proven": False,
            "saved_client_smc_call_relocations_proven": True,
            "saved_client_function_id_and_selectors_proven": True,
            "captured_bl31_service_dispatch_proven": True,
            "installed_bl31_runtime_identity_matched": True,
            "static_end_to_end_sip_abi_proven": True,
            "installed_binary_byte_equivalence_proven": False,
            "runtime_smc_effect_contract_proven": False,
            "firewall_state_proven": False,
            "xnu_firmware_abi_authorized": False,
            "physical_resource_ownership_proven": False,
        },
        "inputs": {
            "saved_ufs_audit": {
                "sha256": SAVED_AUDIT_SHA256, "bytes": len(saved_audit_raw),
            },
            "live_runtime_evidence": {
                "sha256": LIVE_RUNTIME_SHA256, "bytes": len(live_runtime_raw),
            },
            "bl31_ufs_audit": {
                "sha256": BL31_AUDIT_SHA256, "bytes": len(bl31_audit_raw),
            },
            "bl31_runtime_identity": {
                "sha256": BL31_IDENTITY_SHA256, "bytes": len(bl31_identity_raw),
            },
            "saved_ufs_module": {
                "sha256": MODULE_SHA256, "bytes": len(module_raw),
                "gnu_build_id": build_id,
            },
            "runtime_ufs_build_id_note": {
                "sha256": RUNTIME_BUILD_ID_NOTE_SHA256,
                "bytes": len(runtime_build_id_note_raw),
                "gnu_build_id": runtime_build_id,
            },
            "captured_atf_payload": {
                "sha256": ATF_SHA256, "bytes": len(atf_raw),
            },
        },
        "safety": {
            "offline_inputs_only": True,
            "phone_access_by_this_tool": False,
            "smc_execution": False,
            "mmio_access": False,
            "firewall_probe": False,
            "partition_access": False,
            "physical_ufs_backend_enabled": False,
        },
        "not_proven": [
            "installed secure firmware byte-for-byte equivalence",
            "SMC return or physical effect contract",
            "firewall state or XNU authorization",
            "clock, reset, PHY, regulator, IRQ or cache ownership",
        ],
        "scope": (
            "static installed-client to captured-BL31 SiP ABI evidence chain; "
            "no SMC effect, firewall state, XNU delegation, resource ownership "
            "or physical UFS authorization"
        ),
        "verdict": (
            "running-client-build-id-to-captured-bl31-static-sip-abi-matched"
        ),
    }


def validate_pinned_report(raw):
    report = load_json(raw, PINNED_REPORT_SHA256, "pinned SiP ABI report")
    proofs = report.get("proofs", {})
    safety = report.get("safety", {})
    require(report.get("report_version") == REPORT_VERSION and
            report.get("passed") is True and
            report.get("verdict") ==
                "running-client-build-id-to-captured-bl31-static-sip-abi-matched" and
            proofs.get("static_end_to_end_sip_abi_proven") is True,
            "pinned SiP ABI report differs")
    for key in (
        "installed_binary_byte_equivalence_proven",
        "running_client_byte_equivalence_proven",
        "runtime_smc_effect_contract_proven",
        "firewall_state_proven",
        "xnu_firmware_abi_authorized",
        "physical_resource_ownership_proven",
    ):
        require(proofs.get(key) is False,
                "pinned SiP ABI report overclaims: " + key)
    require(safety.get("offline_inputs_only") is True and
            safety.get("phone_access_by_this_tool") is False and
            safety.get("smc_execution") is False and
            safety.get("mmio_access") is False and
            safety.get("partition_access") is False and
            safety.get("physical_ufs_backend_enabled") is False,
            "pinned SiP ABI safety differs")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saved_audit", type=Path)
    parser.add_argument("live_runtime", type=Path)
    parser.add_argument("bl31_audit", type=Path)
    parser.add_argument("bl31_identity", type=Path)
    parser.add_argument("saved_module", type=Path)
    parser.add_argument("runtime_build_id_note", type=Path)
    parser.add_argument("atf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing output")
    report = build_report(
        args.saved_audit.read_bytes(), args.live_runtime.read_bytes(),
        args.bl31_audit.read_bytes(), args.bl31_identity.read_bytes(),
        args.saved_module.read_bytes(), args.runtime_build_id_note.read_bytes(),
        args.atf.read_bytes(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
