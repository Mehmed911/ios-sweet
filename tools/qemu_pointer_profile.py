"""Exact opt-in VirtIO pointer profile; base RAMDisk/UFS restrictions persist."""
import struct
import adt
import mkpayload
import qemu_ramroot_var as base

COMPATIBLE = b'qemu,duchamp-virtio-pointer-v1\0'
REG = struct.pack('<QQ', 0x0a003e00, 0x200)
ARG = ' duchamp_qemu_pointer=1'


def enable(payload, diagnostic_hid=True):
    base.verify(payload, diagnostic_hid=diagnostic_hid)
    offset, size = struct.unpack_from('<2Q', payload, 0x20)
    tree, used = adt.parse(payload[offset:offset + size])
    base.check(used == size and not any(n.name == 'duchamp-qemu-pointer' for n in tree.children), 'duplicate pointer')
    node = adt.Node()
    node.props = [('name', 0, b'duchamp-qemu-pointer\0'), ('compatible', 0, COMPATIBLE), ('reg', 0, REG)]
    tree.children.append(node)
    result = bytearray(payload[:offset])
    dt = adt.serialize(tree)
    struct.pack_into('<Q', result, 0x28, len(dt))
    command = base.BOOT_ARGS + (' sweethidtest=5' if diagnostic_hid else '') + ARG
    base.check(len(command) < mkpayload.BOOT_LINE_LENGTH, 'command too large')
    result[mkpayload.CMDLINE:mkpayload.SEG_TABLE] = command.encode().ljust(mkpayload.BOOT_LINE_LENGTH, b'\0')
    result += dt
    verify(result, diagnostic_hid)
    return result


def verify(payload, diagnostic_hid=True):
    offset, size = struct.unpack_from('<2Q', payload, 0x20)
    base.check(offset <= len(payload) and size == len(payload) - offset, 'invalid pointer ADT extent')
    command = base.BOOT_ARGS + (' sweethidtest=5' if diagnostic_hid else '')
    base.check(payload[mkpayload.CMDLINE:mkpayload.SEG_TABLE] ==
               (command + ARG).encode().ljust(mkpayload.BOOT_LINE_LENGTH, b'\0'), 'invalid pointer command')
    tree, used = adt.parse(payload[offset:])
    nodes = [n for n in tree.children if n.name == 'duchamp-qemu-pointer']
    base.check(used == size and len(nodes) == 1 and nodes[0].props ==
               [('name', 0, b'duchamp-qemu-pointer\0'), ('compatible', 0, COMPATIBLE), ('reg', 0, REG)], 'invalid pointer metadata')
    tree.children.remove(nodes[0])
    dt = adt.serialize(tree)
    normal = bytearray(payload[:offset])
    normal[mkpayload.CMDLINE:mkpayload.SEG_TABLE] = command.encode().ljust(mkpayload.BOOT_LINE_LENGTH, b'\0')
    struct.pack_into('<Q', normal, 0x28, len(dt))
    normal += dt
    return base.verify(normal, diagnostic_hid=diagnostic_hid)
