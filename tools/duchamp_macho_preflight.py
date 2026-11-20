"""0BSD bounded Mach-O admission metadata; no loader, signing or API emulation."""
from pathlib import Path
import posixpath
import runpy
import struct
import uuid

_macho = runpy.run_path(str(Path(__file__).with_name('audit-darwin-runtime.py')))['macho']
MAX64 = (1 << 64) - 1


def inspect(path):
    """Validate command/segment boundaries before using the existing auditor."""
    data = Path(path).read_bytes()
    if len(data) < 32:
        raise ValueError('truncated Mach-O header')
    magic, cpu, subtype, kind, count, size, flags, _ = struct.unpack_from('<8I', data)
    if magic != 0xfeedfacf or cpu != 0x100000c or subtype & 0xffffff:
        raise ValueError('requires thin plain ARM64; arm64e is a separate target')
    if count > 4096 or size > len(data) - 32 or count > size // 8:
        raise ValueError('invalid load-command extent/count')
    end, at = 32 + size, 32
    identifier, image_uuid, segments = None, None, []
    fixups = []
    for _ in range(count):
        if end - at < 8:
            raise ValueError('truncated load command')
        cmd, length = struct.unpack_from('<II', data, at)
        if length < 8 or length % 8 or length > end - at:
            raise ValueError('invalid load-command size/alignment')

        def require(n):
            if length < n:
                raise ValueError('short load-command structure')

        def string(minimum):
            require(minimum)
            offset, = struct.unpack_from('<I', data, at + 8)
            if offset < minimum or offset >= length:
                raise ValueError('invalid command string offset')
            raw = data[at+offset:at+length]
            if b'\0' not in raw:
                raise ValueError('unterminated command string')
            name = raw.split(b'\0', 1)[0].decode('utf-8')
            if not name or any(ord(c) < 32 for c in name):
                raise ValueError('invalid command string')
            return name

        if cmd in (0xc, 0xd, 0x80000018, 0x8000001f, 0x80000023):
            name = string(24)
            if cmd == 0xd:
                if identifier is not None:
                    raise ValueError('duplicate dylib identity')
                identifier = name
        elif cmd in (0xe, 0xf, 0x8000001c):
            string(12)
        elif cmd == 0x1b:
            require(24)
            if image_uuid is not None:
                raise ValueError('duplicate UUID')
            image_uuid = str(uuid.UUID(bytes=data[at+8:at+24])).upper()
        elif cmd == 0x32:
            require(24)
            tools, = struct.unpack_from('<I', data, at+20)
            if tools > (length-24)//8:
                raise ValueError('invalid build-version tools')
        elif cmd == 0x80000028:
            require(24)
        elif cmd == 0x19:
            require(72)
            name = data[at+8:at+24].split(b'\0', 1)[0].decode('ascii')
            va, span, off, amount = struct.unpack_from('<4Q', data, at+24)
            nsects, = struct.unpack_from('<I', data, at+64)
            if nsects > (length-72)//80 or span > MAX64-va or off > len(data) or amount > len(data)-off or amount > span:
                raise ValueError('invalid segment bounds')
            segments.append(dict(name=name, address=va, bytes=span, fileoff=off, filesize=amount))
        elif cmd in (0x1d, 0x80000033, 0x80000034):
            require(16)
            off, amount = struct.unpack_from('<2I', data, at+8)
            if off > len(data) or amount > len(data)-off:
                raise ValueError('linkedit data outside file')
            if cmd != 0x1d:
                fixups.append(dict(command=cmd, offset=off, bytes=amount))
        elif cmd in (0x22, 0x80000022):
            require(48)
            values = struct.unpack_from('<10I', data, at+8)
            for off, amount in zip(values[::2], values[1::2]):
                if off > len(data) or amount > len(data)-off:
                    raise ValueError('dyld information outside file')
            fixups.append(dict(command=cmd, ranges=list(values)))
        elif cmd & 0x80000000:
            raise ValueError('unknown required dyld command')
        at += length
    if at != end:
        raise ValueError('load-command count does not cover declared extent')
    result = _macho(Path(path))
    result.update(uuid=image_uuid, dylib_id=identifier, segments=segments, fixup_metadata=fixups,
                  cache_only=bool(flags & 0x80000000), signature_authenticated=False)
    return result


def guest_path(value):
    if not isinstance(value, str) or not value.startswith('/') or '\0' in value or '\\' in value or '..' in value.split('/'):
        raise ValueError('unsafe or unresolved guest path')
    return posixpath.normpath(value)


def closure(entry, locate, cache_images=()):
    """Static strong closure. Cache inventory never satisfies a guest dependency."""
    files, missing, invalid, weak, edges = {}, [], {}, [], []
    todo = [guest_path(entry)]
    seen = set()
    while todo:
        guest = todo.pop(0)
        if guest in seen:
            continue
        seen.add(guest)
        if guest in invalid:
            continue
        try:
            path = locate(guest_path(guest))
        except ValueError as error:
            invalid[guest] = str(error)
            continue
        if path is None:
            missing.append(dict(path=guest, in_host_cache_inventory=guest in cache_images))
            continue
        try:
            item = inspect(path)
        except (ValueError, UnicodeError, struct.error) as error:
            invalid[guest] = str(error)
            continue
        files[guest] = dict(item, source=str(path))
        if item['cache_only']:
            invalid[guest] = 'MH_DYLIB_IN_CACHE is not a standalone guest dylib'
        if item['dylinker']:
            todo.append(item['dylinker'])
        for dep in item['dependencies']:
            target = dep['path']
            if target.startswith('@loader_path/'):
                target = posixpath.dirname(guest) + '/' + target[13:]
            elif target.startswith('@executable_path/'):
                target = posixpath.dirname(entry) + '/' + target[17:]
            elif target.startswith('@rpath/'):
                # Runpath resolution, including inheritance, is intentionally
                # unsupported here. An unresolved
                # strong runpath is unknown, not a missing absolute file.
                if not dep['weak']:
                    invalid[target] = 'requires loader-chain rpath resolution'
            edges.append(dict(importer=guest, requested=dep['path'], target=target, weak=dep['weak']))
            if dep['weak']:
                weak.append(dict(importer=guest, path=target))
            else:
                todo.append(target)
    return dict(entry=entry, static_closure_complete=not missing and not invalid,
                files=files, missing=missing, invalid=invalid, weak_not_required=weak, edges=edges,
                execution_proven=False, dynamic_imports_proven=False, signature_authenticated=False)
