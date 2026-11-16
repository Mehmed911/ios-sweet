#!/usr/bin/env python3
"""Offline fixtures use ephemeral keys and a scope rejected by the hardware-input CLI."""

from copy import deepcopy
import json
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import tempfile
import time


TOOL = Path(__file__).with_name("verify-duchamp-final-handoff.py")
V = runpy.run_path(str(TOOL))
CASE_SCOPE = "offline-test"
NOW = 2_000_000_000
FDT = (struct.pack(">10I", 0xd00dfeed, 72, 56, 72, 40, 17, 16, 0, 0, 16) +
       bytes(16) + struct.pack(">4I", 1, 0, 2, 9))
ADT = b"opaque mock runtime ADT bytes"
OBS = b"opaque mock owner observation"


def command(*args):
    return subprocess.run(args, capture_output=True, check=True, timeout=20).stdout


def encode(value):
    return json.dumps(value, indent=2).encode() + b"\n"


def make_key(root, name):
    key = root / f"{name}.private"
    public = root / f"{name}.der"
    command("openssl", "genpkey", "-algorithm", "ED25519", "-out", key)
    command("openssl", "pkey", "-in", key, "-pubout", "-outform", "DER", "-out", public)
    return key, public.read_bytes()


def test(root):
    capture = root / "capture"
    capture.mkdir()
    keys = {name: make_key(root, name) for name in ("final-bl31", "xnu-entry", "wrong")}
    sha = V["digest"]
    profile = {name: sha(name.encode()) for name in (*V["IMAGES"], "device", "challenge")}
    profile.update(bl31_key_sha256=sha(keys["final-bl31"][1]), entry_key_sha256=sha(keys["xnu-entry"][1]),
                   not_before=NOW-1, not_after=NOW+1, shim_pc=0x40000000, fdt_pa=0x47c80000,
                   xnu_pc=0x1c1480488, xnu_argument=0x1c456c000, adt_sha256=sha(ADT))
    common = dict(format=V["FORMAT"], scope=CASE_SCOPE, board=V["BOARD"], device=profile["device"],
                  challenge=profile["challenge"], boot_id="1"*32, slot="b",
                  images={key: profile[key] for key in V["IMAGES"]}, fdt_sha256=sha(FDT))
    bl31 = dict(common, stage="final-bl31-exit", sequence=20, ns_pc=profile["shim_pc"],
                fdt_pa=profile["fdt_pa"], observations={
                    name: dict(source=source, sha256=sha(OBS)) for name, source in V["SOURCES"].items()
                })
    entry = dict(common, stage="actual-xnu-entry", sequence=21,
                 bl31_record_sha256="0"*64, shim_pc=profile["shim_pc"], fdt_pa=profile["fdt_pa"],
                 xnu_pc=profile["xnu_pc"], xnu_argument=profile["xnu_argument"], adt_sha256=sha(ADT))

    def sign(name, raw, key_name=None):
        path = capture / f"{name}.json"
        path.write_bytes(raw)
        key, public = keys[key_name or name]
        (capture/f"{name}.der").write_bytes(public)
        command("openssl", "pkeyutl", "-sign", "-rawin", "-inkey", key, "-in", path,
                "-out", capture/f"{name}.sig")

    def prepare(firmware, kernel, *, raw_bl31=None):
        raw = encode(firmware) if raw_bl31 is None else raw_bl31
        sign("final-bl31", raw)
        sign("xnu-entry", encode(dict(kernel, bl31_record_sha256=sha(raw))))
        (capture/"incoming.dtb").write_bytes(FDT)
        (capture/"entry.adt").write_bytes(ADT)
        for name in V["SOURCES"]:
            (capture/f"{name}.bin").write_bytes(OBS)

    def run(trusted=profile, current=NOW, scope=CASE_SCOPE):
        return V["verify"](capture, trusted, current, scope)

    checks = 0

    def deny(why, **kw):
        nonlocal checks
        try:
            run(**kw)
        except V["Rejected"] as error:
            assert why in str(error), (why, str(error))
            checks += 1
        else:
            raise AssertionError(f"accepted rejected case: {why}")

    prepare(bl31, entry)
    result = run()
    assert result["authenticated_entry_pair"]
    assert not result["physical_ufs_authorized"] and not result["resource_ownership_validated"]
    assert set(result["observations_bound"]) == V["SOURCES"].keys()
    assert result["observations_missing"] == []
    checks += 1

    prepare(dict(bl31, observations={}), entry)
    result = run()
    assert result["authenticated_entry_pair"] and not result["physical_ufs_authorized"]
    assert set(result["observations_missing"]) == V["SOURCES"].keys()
    checks += 1

    for key, value, label in (
        ("boot_id", "2"*32, "boot ID mismatch"),
        ("scope", "another-scope", "scope or board"),
        ("board", "other", "scope or board"),
        ("stage", "bootshim-ready", "stage or slot"),
        ("sequence", 20, "event order"),
        ("sequence", True, "invalid integer"),
        ("slot", "a", "stage or slot"),
        ("challenge", "2"*64, "challenge mismatch"),
        ("device", "2"*64, "device mismatch"),
        ("shim_pc", 0x40008000, "bootshim PC mismatch"),
        ("fdt_pa", 0x48000000, "incoming x0 mismatch"),
        ("fdt_sha256", "2"*64, "DTB digest mismatch"),
        ("xnu_pc", 0x40000000, "XNU entry PC mismatch"),
        ("xnu_argument", 0x47c80000, "XNU x0 mismatch"),
        ("adt_sha256", "2"*64, "ADT digest mismatch"),
    ):
        prepare(bl31, dict(entry, **{key: value}))
        deny(label)

    for key in V["IMAGES"]:
        changed = deepcopy(bl31)
        changed["images"][key] = "2"*64
        prepare(changed, entry)
        deny(f"measured {key} mismatch")

    prepare(bl31, entry)
    deny("expired", current=NOW+1)
    deny("premature", current=NOW-2)
    deny("too long", trusted=dict(profile, not_after=NOW+900))
    deny("independent keys", trusted=dict(profile, entry_key_sha256=profile["bl31_key_sha256"]))
    deny("capture scope", scope=V["PHYSICAL_SCOPE"])
    deny("out-of-band pin", trusted=dict(profile, bl31_key_sha256=sha(keys["wrong"][1])))
    sign("xnu-entry", encode(dict(entry, bl31_record_sha256="2"*64)))
    deny("exact BL31 record")

    prepare(bl31, entry)
    sign("xnu-entry", (capture/"xnu-entry.json").read_bytes(), "wrong")
    (capture/"xnu-entry.der").write_bytes(keys["xnu-entry"][1])
    deny("invalid capture signature")
    prepare(bl31, entry)
    with (capture/"final-bl31.json").open("ab") as stream:
        stream.write(b" ")
    deny("invalid capture signature")

    prepare(bl31, entry, raw_bl31=encode(bl31).replace(b'"slot": "b",', b'"slot": "b", "slot": "b",'))
    deny("duplicate JSON key")
    prepare(bl31, entry)
    (capture/"incoming.dtb").write_bytes(FDT + b"x")
    deny("non-exact incoming FDT")
    prepare(bl31, entry)
    (capture/"entry.adt").write_bytes(ADT + b"x")
    deny("ADT digest mismatch")
    prepare(bl31, entry)
    (capture/"entry.adt").unlink()
    (capture/"entry.adt").symlink_to(root/"outside.adt")
    (root/"outside.adt").write_bytes(ADT)
    deny("expected a regular file")
    (capture/"entry.adt").unlink()
    prepare(bl31, entry)
    (capture/"incoming.dtb").write_bytes(bytes(2 * 1024 * 1024 + 1))
    deny("invalid input length")
    prepare(bl31, entry)
    (capture/"reset.bin").write_bytes(OBS + b"x")
    deny("reset: observation bytes differ")
    prepare(bl31, entry)
    (capture/"iommu_route.bin").unlink()
    deny("iommu_route.bin")
    changed = deepcopy(bl31)
    changed["observations"]["reset"]["source"] = "bootshim"
    prepare(changed, entry)
    deny("wrong observation source")
    prepare(dict(bl31, observations={"userspace-story": {}}), entry)
    deny("unrecognized observation class")
    prepare(dict(bl31, grant=True), entry)
    deny("unexpected or missing fields")
    prepare(bl31, entry)
    public = capture/"final-bl31.der"
    public.write_bytes(bytes(public.stat().st_size))
    deny("expected a DER Ed25519 public key")

    # A cryptographically valid synthetic fixture must stay out of the CLI's
    # physical capture mode. Use a file-pinned live window only for this check.
    prepare(bl31, entry)
    now = int(time.time())
    policy = root/"policy.json"
    policy.write_bytes(encode(dict(profile, not_before=now-3, not_after=now+60)))
    result = subprocess.run([sys.executable, "-B", TOOL, capture, "--trusted-profile", policy],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 1 and "capture scope" in result.stderr and not result.stdout
    checks += 1
    print(f"Duchamp final-exit/XNU offline correlation PASS cases={checks}")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="duchamp-offline-keys-") as temp:
        test(Path(temp))
