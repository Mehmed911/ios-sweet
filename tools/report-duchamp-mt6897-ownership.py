#!/usr/bin/env python3
"""Report saved Duchamp MT6897 resource declarations without device access.

The report is deliberately limited to an exact, previously captured DTB and
local source evidence.  A DTB describes references and address ranges; it does
not prove which execution level owns a resource, that firmware delegates it,
or that DMA is usable at runtime.  This tool therefore reports declarations
separately from physical ownership and never treats a missing ``iommus``
property as proof of DMA bypass.

The implementation reuses ``tools/inspect-duchamp-hardware.py`` for bounded
FDT parsing and phandle/address resolution.  It only reads local files and
prints JSON to stdout.  It has no MMIO, subprocess, network, adb, fastboot, or
partition interface.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


# Loading the existing parser must not create a __pycache__ side effect.
sys.dont_write_bytecode = True


EXPECTED_DTB_SHA256 = (
    "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
)

REFERENCE_PROPERTIES = (
    ("clocks", "#clock-cells", "clock-names"),
    ("resets", "#reset-cells", "reset-names"),
    ("power-domains", "#power-domain-cells", "power-domain-names"),
    ("iommus", "#iommu-cells", None),
)

LOCAL_SOURCE_FILES = {
    "gic": [
        "duchamp/drivers/duchamp_gic_boot.h",
    ],
    "timer": [
        "xnu/patches/0205-duchamp-startup-vtimer-declaration.patch",
        "xnu/patches/0211-duchamp-first-timer-irq-witness.patch",
    ],
    "firmware": [
        "duchamp/drivers/mt6897_firmware.c",
        "duchamp/drivers/mt6897_smc.S",
    ],
    "power": [
        "duchamp/drivers/mt6897_pmif.c",
        "duchamp/drivers/mt6897_pmic.c",
        "duchamp/drivers/mt6897_ufs_platform.c",
    ],
    "iommu": [
        "duchamp/drivers/mt6897_iommu.c",
        "duchamp/drivers/mt6897_ufs_dma.c",
    ],
    "ufs": [
        "duchamp/drivers/mt6897_ufs_platform.c",
        "duchamp/drivers/mt6897_ufs_clocks.c",
        "duchamp/drivers/mt6897_ufs_dma.c",
        "duchamp/drivers/ufs_readonly.c",
    ],
}

SOURCE_MANIFESTS = (
    "duchamp/drivers/mt6897-platform-sources.json",
    "duchamp/drivers/mt6897-backend-sources.json",
    "duchamp/drivers/mt6897-contract-sources.json",
)

RESOURCE_KEYS = (
    "reg",
    "interrupts",
    "clocks",
    "resets",
    "power_domains",
    "iommus",
)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def load_fdt_parser(repo):
    """Load the repository's existing bounded FDT parser."""
    parser_path = repo / "tools/inspect-duchamp-hardware.py"
    spec = importlib.util.spec_from_file_location(
        "duchamp_saved_fdt_parser", parser_path
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load saved-DTB parser: {parser_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, parser_path


def node_compatibles(node):
    return node.strings("compatible") if "compatible" in node.props else []


def status(node):
    if "status" not in node.props:
        return {"explicit": False, "value": "okay (implicit)"}
    values = node.strings("status")
    if len(values) != 1:
        raise ValueError(f"{node.path}:status: expected one string")
    return {"explicit": True, "value": values[0]}


def raw_cells(node, key):
    return [hex(value) for value in node.cells(key)]


def decoded_property(node, key, decoder):
    present = key in node.props
    result = {"present": present, "entries": []}
    if not present:
        return result
    try:
        result["entries"] = decoder()
    except (KeyError, UnicodeError, ValueError) as error:
        result["raw_cells"] = raw_cells(node, key)
        result["decode_error"] = str(error)
    return result


def references(tree, node, key, count_key, names_key):
    actual_names = names_key if names_key and names_key in node.props else None
    return tree.references(node, key, count_key, actual_names)


def phandle_list(tree, node, key):
    entries = []
    for handle in node.cells(key):
        provider = tree.provider(handle)
        entries.append(
            {
                "provider": provider.path,
                "compatible": node_compatibles(provider),
            }
        )
    return entries


def describe_node(tree, node):
    resources = {
        "reg": decoded_property(node, "reg", lambda: tree.registers(node)),
        "interrupts": decoded_property(
            node,
            "interrupts-extended"
            if "interrupts-extended" in node.props
            else "interrupts",
            lambda: tree.interrupts(node),
        ),
    }
    if "interrupts" not in node.props and "interrupts-extended" not in node.props:
        resources["interrupts"] = {"present": False, "entries": []}

    for key, count_key, names_key in REFERENCE_PROPERTIES:
        resources[key.replace("-", "_")] = decoded_property(
            node,
            key,
            lambda key=key, count_key=count_key, names_key=names_key: references(
                tree, node, key, count_key, names_key
            ),
        )

    details = {}
    if "method" in node.props:
        details["method"] = node.strings("method")
    if "phys" in node.props:
        details["phys"] = decoded_property(
            node, "phys", lambda: references(tree, node, "phys", "#phy-cells", "phy-names")
        )
    if "mboxes" in node.props:
        details["mboxes"] = decoded_property(
            node, "mboxes", lambda: references(tree, node, "mboxes", "#mbox-cells", None)
        )
    if "shmem" in node.props:
        details["shmem"] = decoded_property(
            node, "shmem", lambda: phandle_list(tree, node, "shmem")
        )
    for key in ("dma-ranges", "iommu-map"):
        if key in node.props:
            details[key.replace("-", "_")] = {
                "present": True,
                "raw_cells": raw_cells(node, key),
                "interpretation": "declaration only; runtime routing is not proven",
            }
    details["dma_coherent"] = {
        "present": "dma-coherent" in node.props,
        "interpretation": "property presence only; runtime coherency is not tested",
    }

    supplies = {}
    for key in sorted(node.props):
        if not key.endswith("-supply"):
            continue
        try:
            provider = tree.provider(node.scalar(key))
            supplies[key] = {
                "provider": provider.path,
                "compatible": node_compatibles(provider),
            }
        except (KeyError, ValueError) as error:
            supplies[key] = {
                "raw_cells": raw_cells(node, key),
                "decode_error": str(error),
            }
    if supplies:
        details["supplies"] = supplies

    roles = []
    for label, provider_key, consumer_keys in (
        ("interrupt", "#interrupt-cells", ("interrupts", "interrupts-extended")),
        ("clock", "#clock-cells", ("clocks",)),
        ("reset", "#reset-cells", ("resets",)),
        ("power-domain", "#power-domain-cells", ("power-domains",)),
        ("iommu", "#iommu-cells", ("iommus", "iommu-map")),
    ):
        if provider_key in node.props:
            roles.append(label + "-provider")
        if any(key in node.props for key in consumer_keys):
            roles.append(label + "-consumer")

    return {
        "path": node.path,
        "status": status(node),
        "compatibles": node_compatibles(node),
        "roles": roles,
        "resources": resources,
        "details": details,
    }


def has_compatible(node, fragment):
    fragment = fragment.lower()
    return any(fragment in value.lower() for value in node_compatibles(node))


def sorted_nodes(nodes):
    return [
        node
        for _, node in sorted(
            {node.path: node for node in nodes}.items(), key=lambda item: item[0]
        )
    ]


def resource_provider_paths(tree, node):
    providers = set()
    for key, count_key, names_key in REFERENCE_PROPERTIES:
        if key not in node.props:
            continue
        try:
            providers.update(
                entry["provider"]
                for entry in references(tree, node, key, count_key, names_key)
            )
        except (KeyError, UnicodeError, ValueError):
            pass
    if "phys" in node.props:
        try:
            providers.update(
                entry["provider"]
                for entry in references(tree, node, "phys", "#phy-cells", "phy-names")
            )
        except (KeyError, UnicodeError, ValueError):
            pass
    for key in node.props:
        if key.endswith("-supply"):
            try:
                providers.add(tree.provider(node.scalar(key)).path)
            except (KeyError, ValueError):
                pass
    return providers


def category_nodes(tree):
    nodes = list(tree.nodes.values())

    gic = [
        node
        for node in nodes
        if node.path == "/interrupt-controller"
        or has_compatible(node, "gic-v3")
        or has_compatible(node, "mediatek,gic")
    ]

    timer = [
        node
        for node in nodes
        if node.path == "/timer"
        or "systimer@" in node.path
        or any("timer" in value.lower() for value in node_compatibles(node))
    ]

    firmware = [
        node
        for node in nodes
        if node.path == "/psci"
        or node.path == "/firmware"
        or node.path.startswith("/firmware/")
        or node.path == "/sspm@1c300000"
        or has_compatible(node, "smc-v1")
    ]

    power = [
        node
        for node in nodes
        if "#power-domain-cells" in node.props
        or has_compatible(node, "scpsys")
        or has_compatible(node, "gpusys")
        or has_compatible(node, "vmm_spm")
        or node.path == "/soc/spmi@1cc04000"
        or (
            node.parent is not None
            and node.parent.path == "/soc/spmi@1cc04000"
            and any(value.startswith("mediatek,mt63") for value in node_compatibles(node))
        )
    ]

    iommu = [
        node
        for node in nodes
        if "#iommu-cells" in node.props
        or "iommus" in node.props
        or any("iommu" in value.lower() for value in node_compatibles(node))
    ]

    ufs_hosts = [node for node in nodes if has_compatible(node, "ufshci")]
    ufs = [
        node
        for node in nodes
        if any("ufs" in value.lower() for value in node_compatibles(node))
    ]
    for host in ufs_hosts:
        for provider_path in resource_provider_paths(tree, host):
            if provider_path in tree.nodes:
                ufs.append(tree.nodes[provider_path])
    return {
        "gic": sorted_nodes(gic),
        "timer": sorted_nodes(timer),
        "firmware": sorted_nodes(firmware),
        "power": sorted_nodes(power),
        "iommu": sorted_nodes(iommu),
        "ufs": sorted_nodes(ufs),
    }


def ufs_dma_ancestry(tree, host):
    result = []
    node = host
    while node is not None:
        entry = {"path": node.path}
        for key in ("iommus", "iommu-map", "dma-ranges"):
            entry[key.replace("-", "_")] = {
                "present": key in node.props,
                "raw_cells": raw_cells(node, key) if key in node.props else [],
            }
        entry["dma_coherent"] = "dma-coherent" in node.props
        result.append(entry)
        node = node.parent
    return result


def category_ownership(name, nodes, tree):
    gaps = {
        "gic": [
            "DTB MMIO/interrupt declarations do not prove EL3 or secure-firmware ownership/delegation.",
            "Physical GICD/GICR access and interrupt delivery have not been established by this report.",
        ],
        "timer": [
            "DTB timer declarations do not prove the physical counter frequency or runtime interrupt delivery.",
            "No ownership or enable-state evidence is available from a static DTB.",
        ],
        "firmware": [
            "PSCI/SCMI/SMC declarations do not identify or validate the installed firmware implementation.",
            "Firmware ABI support, service ownership, and delegation remain unproven.",
        ],
        "power": [
            "Power-domain, PMIF, and PMIC declarations do not prove safe physical sequencing or ownership.",
            "Runtime regulator/clock/reset state and secure-firmware mediation remain unproven.",
        ],
        "iommu": [
            "IOMMU provider declarations do not establish an active translation domain for UFS.",
            "Stream IDs, page-table ownership, reserved regions, and physical DMA behavior remain unproven.",
        ],
        "ufs": [
            "UFS MMIO, IRQ, clock, reset, PHY, and supply declarations do not prove controller ownership.",
            "Physical link startup, DMA routing/coherency, and storage access remain unproven.",
        ],
    }[name]
    result = {
        "dtb_declaration": "present" if nodes else "missing",
        "runtime_owner": "unproven",
        "physical_access_tested": False,
        "gaps": gaps,
        "nodes": [describe_node(tree, node) for node in nodes],
    }
    if name == "ufs":
        hosts = [node for node in nodes if has_compatible(node, "ufshci")]
        if len(hosts) != 1:
            result["ufs_dma_route"] = {
                "verified": False,
                "reason": f"expected one UFS host, found {len(hosts)}",
                "ancestry": [],
            }
        else:
            ancestry = ufs_dma_ancestry(tree, hosts[0])
            declared = any(
                entry["iommus"]["present"] or entry["iommu_map"]["present"]
                for entry in ancestry
            )
            result["ufs_dma_route"] = {
                "verified": False,
                "dtb_iommu_binding_declared_on_host_or_ancestors": declared,
                "reason": (
                    "a DTB binding is present but cannot prove the physical route"
                    if declared
                    else "no iommus or iommu-map binding exists on the UFS host or its ancestors; "
                    "absence does not prove direct/bypass DMA"
                ),
                "ancestry": ancestry,
            }
    return result


def find_values(value, key):
    found = []
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key:
                found.append(current_value)
            found.extend(find_values(current_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_values(item, key))
    return found


def source_evidence(repo, dtb_hash, parser_path):
    manifests = []
    for relative in SOURCE_MANIFESTS:
        path = repo / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        hashes = sorted(set(find_values(data, "captured_fdt_sha256")))
        repositories = []
        seen_repositories = set()
        for repository in find_values(data, "repository"):
            if repository not in seen_repositories:
                repositories.append(repository)
                seen_repositories.add(repository)
        manifests.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "captured_fdt_sha256": hashes,
                "matches_report_dtb": (
                    set(hashes) == {dtb_hash} if hashes else None
                ),
                "repositories": repositories,
                "scope_statements": find_values(data, "scope"),
            }
        )

    local_sources = {}
    for category, relatives in LOCAL_SOURCE_FILES.items():
        local_sources[category] = []
        for relative in relatives:
            path = repo / relative
            local_sources[category].append(
                {
                    "path": relative,
                    "present": path.is_file(),
                    "sha256": sha256_file(path) if path.is_file() else None,
                    "ownership_proof": False,
                }
            )
    return {
        "parser": {
            "path": parser_path.relative_to(repo).as_posix(),
            "sha256": sha256_file(parser_path),
            "reused": True,
        },
        "manifests": manifests,
        "local_sources": local_sources,
        "interpretation": (
            "Local source and provenance receipts constrain implementation assumptions; "
            "they do not prove installed firmware identity or physical resource ownership."
        ),
    }


def build_report(raw, repo):
    repo = Path(repo).resolve()
    observed_hash = sha256_bytes(raw)
    if observed_hash != EXPECTED_DTB_SHA256:
        raise ValueError(
            "saved Duchamp DTB provenance mismatch: "
            f"expected {EXPECTED_DTB_SHA256}, got {observed_hash}"
        )
    parser, parser_path = load_fdt_parser(repo)
    tree = parser.Fdt(raw)
    if tree.nodes["/"].strings("model") != ["MT6897"]:
        raise ValueError("saved DTB root model is not MT6897")

    selected = category_nodes(tree)
    categories = {
        name: category_ownership(name, nodes, tree)
        for name, nodes in selected.items()
    }
    return {
        "report_version": 1,
        "dtb": {
            "sha256": observed_hash,
            "bytes": len(raw),
            "model": "MT6897",
            "provenance": "exact saved Duchamp DTB evidence",
        },
        "categories": categories,
        "source_evidence": source_evidence(repo, observed_hash, parser_path),
        "unproven_ownership": [
            "runtime timer and interrupt delivery on MT6897",
            "GIC and secure-firmware delegation/ownership",
            "installed PSCI/SCMI/SiP firmware contracts",
            "power/clock/reset sequencing ownership",
            "UFS DMA/IOMMU route and coherency",
            "physical UFS controller, PHY, and storage access",
        ],
        "safety": {
            "offline_only": True,
            "read_only_inputs": True,
            "mmio_access": False,
            "adb_access": False,
            "fastboot_access": False,
            "phone_access": False,
            "partition_access": False,
            "network_access": False,
            "subprocess_execution": False,
        },
        "scope": (
            "static saved-DTB and local-source inspection only; no physical ownership, "
            "firmware compatibility, runtime delivery, DMA, or storage claim"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dtb", type=Path, help="exact saved Duchamp phone-fdt.bin")
    parser.add_argument(
        "--compact", action="store_true", help="emit compact rather than indented JSON"
    )
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    try:
        raw = args.dtb.read_bytes()
        report = build_report(raw, repo)
    except (json.JSONDecodeError, OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"ownership report failed: {error}\n")
    if args.compact:
        print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
