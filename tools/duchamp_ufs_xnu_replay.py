"""Link the handoff source into a pinned XNU copy for the local QEMU replay."""
import hashlib
from pathlib import Path
import re
import struct
import subprocess

BASE_SHA256 = "9ea1ed93bb392753bbb11dda532eadfbdf766118508c8cb52f4af222167fbca0"
TEXT = 0xfffffe0007b46e00
TEXT_LIMIT = 0xfffffe0007b48000
STATE = 0xfffffe0007b95000
STATE_LIMIT = 0xfffffe0007b95040
PLATFORM_CALL = 0xfffffe0007ad293c
ROOT_ENTRY = 0xfffffe00074df5f8

THUNKS = """
.text
.global replay_platform
replay_platform:
    str x30, [sp, #-16]!
    bl PE_init_platform
    bl duchamp_qemu_ufs_handoff_enter
    ldr x30, [sp], #16
    ret

.global replay_root
replay_root:
    stp x0, x30, [sp, #-16]!
    bl duchamp_qemu_ufs_handoff_allows
    mov w9, w0
    ldp x0, x30, [sp], #16
    cbz w9, 1f
    sub sp, sp, #0x120
    b original_root_body
1:
    mov w0, #1
    ret

"""
KERNEL_APIS = (
    "PE_init_platform", "sweet_early_mark", "PE_parse_boot_argn",
    "SecureDTLookupEntry", "SecureDTGetProperty", "memcpy",
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def symbols(file):
    result = {}
    for line in subprocess.check_output(["llvm-nm", "--defined-only", str(file)], text=True).splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]+) \w (\S+)", line)
        if match:
            result[match[2]] = int(match[1], 16)
    return result


def macho_segments(data):
    assert struct.unpack_from("<II", data) == (0xfeedfacf, 0x0100000c)
    ncmds = struct.unpack_from("<I", data, 16)[0]
    offset = 32
    for _ in range(ncmds):
        command, size = struct.unpack_from("<II", data, offset)
        if command == 0x19:
            name, va, vmsize, pos, filesz = struct.unpack_from("<16s4Q", data, offset + 8)
            nsects = struct.unpack_from("<I", data, offset + 64)[0]
            ranges = []
            for i in range(nsects):
                addr, length = struct.unpack_from("<QQ", data, offset + 72 + 80 * i + 32)
                ranges.append((addr, addr + length))
            yield name.rstrip(b"\0").decode(), va, vmsize, pos, filesz, ranges
        offset += size


def branch(from_va, to_va, link=False):
    delta = to_va - from_va
    assert delta % 4 == 0 and -(1 << 27) <= delta < (1 << 27)
    return (0x94000000 if link else 0x14000000) | ((delta // 4) & 0x03ffffff)


def build_replay(kernel, out):
    raw = bytearray(kernel.read_bytes())
    assert digest(raw) == BASE_SHA256
    segments = list(macho_segments(raw))
    names = symbols(kernel)
    assert names["_duchamp_qemu_ufs_rootdev"] == ROOT_ENTRY
    source = Path(__file__).resolve().parents[1] / "duchamp/xnu/qemu_ufs_handoff.c"
    thunks, script, elf, code = (out / name for name in ("thunks.S", "replay.ld", "replay.elf", "replay.text"))
    thunks.write_text(THUNKS)
    definitions = "\n".join(f"{name} = {names['_' + name]:#x};" for name in KERNEL_APIS)
    script.write_text(f"""{definitions}
original_root_body = {ROOT_ENTRY + 4:#x};
SECTIONS {{
  .replay {TEXT:#x} : {{ *(.text*) *(.rodata*) }}
  .state {STATE:#x} (NOLOAD) : {{ *(.bss*) }}
  /DISCARD/ : {{ *(.comment) *(.eh_frame*) }}
}}
ASSERT(SIZEOF(.state) <= {STATE_LIMIT - STATE}, "state exceeds reserved padding")
ASSERT(SIZEOF(.replay) <= {TEXT_LIMIT - TEXT}, "code exceeds reserved padding")
""")
    subprocess.run(["clang", "--target=aarch64-none-elf", "-O2", "-ffreestanding", "-fno-builtin",
                    "-fno-stack-protector", "-mgeneral-regs-only", "-mstrict-align",
                    "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-Wall", "-Wextra", "-Werror",
                    "-DDUCHAMP_HANDOFF_PINNED_QEMU_REPLAY", "-nostdlib", "-fuse-ld=lld",
                    "-Wl,-e,replay_platform", "-Wl,-T," + str(script),
                    str(thunks), str(source), "-o", str(elf)], check=True)
    subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=.replay", str(elf), str(code)], check=True)
    linked = symbols(elf)

    def file_offset(va, size, *, padding=False):
        for segment, base, _, pos, span, sections in segments:
            if base <= va and va + size <= base + span:
                if padding:
                    assert all(va + size <= start or va >= end for start, end in sections if start != end)
                return pos + va - base
        raise ValueError(f"No file-backed kernel segment for {va:#x}")

    blob = code.read_bytes()
    pos = file_offset(TEXT, len(blob), padding=True)
    state_pos = file_offset(STATE, STATE_LIMIT - STATE, padding=True)
    assert len(blob) and not any(raw[pos:pos + len(blob)]) and not any(raw[state_pos:state_pos + STATE_LIMIT - STATE])
    raw[pos:pos + len(blob)] = blob
    hooks = [
        (PLATFORM_CALL, branch(PLATFORM_CALL, names["_PE_init_platform"], True), "replay_platform", True),
        (ROOT_ENTRY, 0xd10483ff, "replay_root", False),
    ]
    for va, expected, target, link in hooks:
        off = file_offset(va, 4)
        assert struct.unpack_from("<I", raw, off)[0] == expected
        struct.pack_into("<I", raw, off, branch(va, linked[target], link))
    image = out / "kernel.qemu-handoff"
    image.write_bytes(raw)
    return image, dict(base_sha256=BASE_SHA256, replay_sha256=digest(raw), source_sha256=digest(source.read_bytes()),
                       code_bytes=len(blob), linked_symbols={name: hex(linked[name]) for _, _, name, _ in hooks})
