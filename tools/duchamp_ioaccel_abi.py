#!/usr/bin/env python3
"""0BSD: bounded, offline analysis of the original 20F66 IOAccelerator consumer.

This is NOT an IOUserClient, graphics provider or producer-side ABI definition.
Recognizing a request shape or decoding bytes never establishes mappings,
ownership, synchronization, driver compatibility or successful execution.
No address read from a descriptor is dereferenced by this module.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

DESCRIPTOR_BYTES = 600
OFFSET_START = 0x58
OFFSET_CAPACITY = (DESCRIPTOR_BYTES - OFFSET_START) // 4
U64_MAX = (1 << 64) - 1
CONNECTION_TYPES = frozenset((1, 2, 4))


class CaptureError(ValueError):
    """Malformed capture or unsafe-to-model consumer arithmetic."""


def _integer(value, label, maximum=U64_MAX):
    if type(value) is not int or not 0 <= value <= maximum:
        raise CaptureError(label + ' must be an unsigned bounded integer')
    return value


def _bytes(value):
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise CaptureError('capture must be a contiguous byte buffer')
    try:
        return bytes(memoryview(value).cast('B'))
    except (TypeError, ValueError) as e:
        raise CaptureError('capture must be a contiguous byte buffer') from e


def _result(**fields):
    return dict(fields, graphics_execution=False, ownership='UNKNOWN',
                mapping='UNKNOWN', synchronization='UNKNOWN',
                provider_compatible=False)


def decode_descriptor(capture):
    """Decode only original consumer accesses; reject out-of-capture reads.

    The 128-entry ceiling follows the capture's available bytes, not a verified
    producer maximum. Text is searched only up to the first offset access.
    Neither this boundary nor a terminating NUL proves the kernel string field's
    declared extent. Count 1 uses the base directly; count >=2 adds offsets.
    """
    data = _bytes(capture)
    if len(data) != DESCRIPTOR_BYTES:
        raise CaptureError('selector-2 capture must contain exactly 600 bytes')
    base = struct.unpack_from('<Q', data, 0)[0]
    count = struct.unpack_from('<i', data, 0x14)[0]
    if not 0 <= count <= OFFSET_CAPACITY:
        raise CaptureError('consumer count outside bounded capture capacity')
    text_prefix = data[0x18:OFFSET_START]
    nul = text_prefix.find(b'\0')
    offsets = []
    if count >= 2:
        offsets = list(struct.unpack_from('<' + 'I' * count, data, OFFSET_START))
    addresses = [base] if count == 1 else [base + n for n in offsets]
    # The consumer performs a u32 load at each address. Reject wrapping both
    # the addition and that load. This is offline arithmetic, NOT map validation.
    if any(a > U64_MAX - 3 for a in addresses):
        raise CaptureError('consumer address or four-byte load would wrap')
    return _result(
        status='STATIC_CONSUMER_BYTES_DECODED', size=len(data),
        sha256=hashlib.sha256(data).hexdigest(), base_raw=base,
        opaque_08_0f=data[8:16].hex(),
        opaque_u32_10=struct.unpack_from('<I', data, 0x10)[0],
        signed_count_14=count,
        dlsym_text_prefix_hex=text_prefix.hex(),
        dlsym_name_hex=text_prefix[:nul].hex() if nul >= 0 else None,
        dlsym_terminated_in_prefix=nul >= 0,
        text_extent='UNKNOWN; 64-byte inspection bound is inferred',
        offset_words=offsets, consumer_addresses=addresses,
        trailing_uninterpreted_hex=data[OFFSET_START + len(offsets) * 4:].hex(),
        capture_capacity_is_not_producer_limit=True,
        actual_producer_response_observed=False)


# Each tuple is an ORIGINAL static call shape: structure-input size and
# requested output capacity. They are not a full dispatch table. The same
# selector means different things on different client types.
STRUCT_SHAPES = {
    (1, 7): (16, 0),
    (1, 2): (0, 600),
    (1, 0): (0, 64),
    (1, 5): (0, 24),
    (2, 7): (0, 16),
}


def inspect_request(connection_type, selector, input_bytes=b'', output_capacity=0):
    """Recognize call-site shapes without executing or blessing the request."""
    kind = _integer(connection_type, 'connection type', (1 << 32) - 1)
    method = _integer(selector, 'selector', (1 << 32) - 1)
    capacity = _integer(output_capacity, 'output capacity')
    data = _bytes(input_bytes)
    if kind not in CONNECTION_TYPES:
        raise CaptureError('connection type not established in this audit')
    shape = STRUCT_SHAPES.get((kind, method))
    if shape is not None:
        if (len(data), capacity) != shape:
            raise CaptureError('request differs from verified static call shape')
        return _result(status='STATIC_SHAPE_RECOGNIZED', connection_type=kind,
                       selector=method, input_bytes=len(data),
                       requested_output_bytes=capacity)
    if (kind, method) == (4, 1):
        if len(data) < 8:
            raise CaptureError('queue prefix is shorter than eight bytes')
        count = struct.unpack_from('<i', data, 4)[0]
        if count < 0 or count > (U64_MAX - 8) // 24:
            raise CaptureError('negative or overflowing queue record count')
        if len(data) != 8 + 24 * count:
            raise CaptureError('queue bytes do not equal 8 + 24 * count')
        if capacity != 0:
            raise CaptureError('this queue call has no structure output')
        return _result(status='STATIC_SHAPE_RECOGNIZED', connection_type=kind,
                       selector=method, input_bytes=len(data), record_count=count,
                       command_semantics='UNKNOWN')
    return _result(status='UNSUPPORTED_UNKNOWN_METHOD', connection_type=kind,
                   selector=method)


def assess_memory_claim(base, size, owner_pid, caller_pid, live, mapped, sync):
    """Negative evidence checks, NOT an Apple allocation or handle API.

    Even all positive caller assertions cannot verify the unknown 20F66
    producer contract. Never issue a grant or turn these inputs into ownership.
    Used to ensure a future caller cannot mistake arithmetic for map evidence.
    """
    base = _integer(base, 'base')
    size = _integer(size, 'size')
    owner_pid = _integer(owner_pid, 'owner pid', (1 << 31) - 1)
    caller_pid = _integer(caller_pid, 'caller pid', (1 << 31) - 1)
    reasons = []
    if not size or base > U64_MAX - (size - 1):
        reasons.append('INVALID_OR_WRAPPING_RANGE')
    if not owner_pid or owner_pid != caller_pid:
        reasons.append('OWNER_MISMATCH')
    if live is not True:
        reasons.append('STALE_OR_UNKNOWN_HANDLE')
    if mapped is not True:
        reasons.append('MAPPING_UNVERIFIED')
    if sync is not True:
        reasons.append('SYNCHRONIZATION_UNVERIFIED')
    reasons.append('PRODUCER_CONTRACT_UNVERIFIED')
    return _result(status='EXECUTION_REFUSED', reasons=reasons)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('descriptor', type=Path)
    args = ap.parse_args()
    # Read one byte beyond the expected size to reject oversized files without
    # loading attacker-controlled or accidentally huge artifacts into memory.
    with args.descriptor.open('rb') as f:
        capture = f.read(DESCRIPTOR_BYTES + 1)
    try:
        print(json.dumps(decode_descriptor(capture), indent=2))
    except CaptureError as e:
        ap.exit(2, 'capture rejected: ' + str(e) + '\n')


if __name__ == '__main__':
    main()
