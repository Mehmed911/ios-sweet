"""Exact modern VirtIO multitouch profile, layered on the tested mouse profile."""
import struct
import adt
import mkpayload
import qemu_ramroot_var as base
import qemu_pointer_profile as pointer

ARG = ' duchamp_qemu_multitouch=1'
PROPS = [('name', 0, b'duchamp-qemu-multitouch\0'),
         ('compatible', 0, b'qemu,duchamp-virtio-multitouch-v1\0'),
         ('reg', 0, struct.pack('<QQ', 0x0a003c00, 0x200))]


def enable(payload, diagnostic_hid=True):
    pointer.verify(payload, diagnostic_hid)
    offset, size = struct.unpack_from('<2Q', payload, 0x20)
    tree, used = adt.parse(payload[offset:offset + size])
    base.check(used == size and not any(n.name == 'duchamp-qemu-multitouch' for n in tree.children), 'duplicate touch node')
    node = adt.Node()
    node.props = PROPS.copy()
    tree.children.append(node)
    result = bytearray(payload[:offset])
    command = result[mkpayload.CMDLINE:mkpayload.SEG_TABLE].split(b'\0', 1)[0] + ARG.encode()
    base.check(len(command) < mkpayload.BOOT_LINE_LENGTH, 'touch command overflow')
    result[mkpayload.CMDLINE:mkpayload.SEG_TABLE] = command.ljust(mkpayload.BOOT_LINE_LENGTH, b'\0')
    dt = adt.serialize(tree)
    struct.pack_into('<Q', result, 0x28, len(dt))
    result += dt
    verify(result, diagnostic_hid)
    return result


def verify(payload, diagnostic_hid=True):
    base.check(len(payload) >= mkpayload.SEG_TABLE, 'truncated touch payload')
    offset, size = struct.unpack_from('<2Q', payload, 0x20)
    base.check(offset <= len(payload) and size == len(payload) - offset, 'touch ADT extent')
    tree, used = adt.parse(payload[offset:])
    nodes = [n for n in tree.children if n.name == 'duchamp-qemu-multitouch']
    base.check(used == size and len(nodes) == 1 and nodes[0].props == PROPS, 'invalid touch node')
    command = base.BOOT_ARGS + (' sweethidtest=5' if diagnostic_hid else '') + pointer.ARG
    base.check(payload[mkpayload.CMDLINE:mkpayload.SEG_TABLE] == (command + ARG).encode().ljust(mkpayload.BOOT_LINE_LENGTH, b'\0'), 'invalid touch opt-in')
    tree.children.remove(nodes[0])
    result = bytearray(payload[:offset])
    dt = adt.serialize(tree)
    struct.pack_into('<Q', result, 0x28, len(dt))
    result[mkpayload.CMDLINE:mkpayload.SEG_TABLE] = command.encode().ljust(mkpayload.BOOT_LINE_LENGTH, b'\0')
    return pointer.verify(result + dt, diagnostic_hid)
