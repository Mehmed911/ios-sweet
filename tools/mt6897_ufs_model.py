"""Software model for Duchamp UFS queues and non-coherent DMA ownership."""

from collections import deque
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import runpy
import struct


REPO = Path(__file__).resolve().parent.parent
XIAOMI_COMMIT = "3c4ccd07d5624879555ec710c11bb8818e5cb5c6"
SOURCE_BLOBS = {
    "ufs-mediatek.c": "7159d8ebf89f4bd9127b5de910b4d80ea895f78f",
    "ufs-mediatek.h": "12a0284d9c4fe169ca049f5f4a57e901855d9906",
    "ufs-mediatek-sip.h": "28a3a4f3c13ff4a94c1d90e29717b2428c7588e8",
}
BLOCK_BYTES = 4096  # The virtual UFS media used by the GPT integration test.
POOL_PA = 0x60000000
POOL_BYTES = 2 * BLOCK_BYTES
RING_DEPTH = 4  # A small ring with one unused slot for the test model.
PRD = struct.Struct("<QII")


def load_profile(dtb, sources):
    dma = runpy.run_path(str(REPO / "tools/assess-mt6897-ufs-dma-map.py"))
    require = dma["require"]
    raw = dtb.read_bytes()
    digest = dma["sha256"](raw)
    require(digest == dma["FDT_SHA256"], "saved Duchamp DTB hash differs")
    tree, _ = dma["load_fdt"](REPO, raw)
    node = tree.nodes["/soc/ufshci@112b0000"]
    registers, = tree.registers(node)
    irq = [entry["args"] for entry in tree.interrupts(node)]
    require(len(irq) == 9 and all(len(spec) == 4 and spec[0] == 0 for spec in irq),
            "expected one host IRQ and eight MCQ IRQ declarations")
    require(not ({"iommus", "iommu-map", "dma-coherent"} & node.props.keys()),
            "unexpected UFS DMA declaration")
    require(all("dma-coherent" not in tree.nodes[path].props for path in ("/soc", "/")),
            "unexpected inherited DMA coherency")
    windows = dma["decode_dma_ranges"](node.parent)
    require(len(windows) == 1 and windows[0]["identity"], "expected the saved identity window")

    source = {}
    for name, expected in SOURCE_BLOBS.items():
        blob = (sources / name).read_bytes()
        git_blob = hashlib.sha1(f"blob {len(blob)}\0".encode() + blob).hexdigest()
        require(git_blob == expected, f"Xiaomi source blob differs: {name}")
        source[name] = blob.decode()
    header = source["ufs-mediatek.h"]
    stride = int(re.search(r"(?m)^#define REG_UFS_MCQ_STRIDE\s+(0x[0-9a-fA-F]+)", header)[1], 16)
    offsets = {reg: int(re.search(rf"(?m)^#define REG_UFS_MTK_{reg}\s+(0x[0-9a-fA-F]+)", header)[1], 16)
               for reg in ("SQD", "SQIS", "CQD", "CQIS")}
    require("ufs_mtk_get_mcq_en(res)" in source["ufs-mediatek.c"] and
            "UFS_MTK_SIP_GET_MCQ_EN" in source["ufs-mediatek-sip.h"], "missing MCQ policy source")
    queue_regs = [{reg: offset + stride * index for reg, offset in offsets.items()}
                  for index in range(len(irq) - 1)]
    require(max(queue_regs[-1].values()) + 4 <= int(registers["bytes"], 16),
            "MCQ registers leave the saved HCI aperture")
    return dict(dtb_sha256=digest, xiaomi_commit=XIAOMI_COMMIT, source_blobs=SOURCE_BLOBS,
                hci=registers, host_gic_intid=irq[0][1] + 32,
                mcq_gic_intids=[spec[1] + 32 for spec in irq[1:]], mcq_stride=stride,
                mcq_register_offsets=queue_regs,
                dt_disables_mcq="mediatek,ufs-disable-mcq" in node.props,
                dma_windows=windows, iommu_binding_present=False,
                dma_coherent_declared=False, modeled_cache="separate CPU and device views"), dma


class DmaPool:
    def __init__(self, windows, dma):
        self.windows = windows
        self.dma = dma
        self.cpu = bytearray(POOL_BYTES)
        self.device = bytearray(POOL_BYTES)

    def address(self, offset, length):
        self.span(offset, length)
        return self.dma["translate_pa_to_dma"](self.windows, POOL_PA + offset, length)

    def span(self, offset, length):
        if not 0 <= offset < POOL_BYTES or not 0 < length <= POOL_BYTES - offset:
            raise ValueError("DMA outside the model-owned pool")
        return slice(offset, offset + length)

    def device_span(self, bus, length):
        pa = self.dma["translate_dma_to_pa"](self.windows, bus, length)
        return self.span(pa - POOL_PA, length)

    def sync_for_device(self, offset, length):
        span = self.span(offset, length)
        self.device[span] = self.cpu[span]

    def sync_for_cpu(self, offset, length):
        span = self.span(offset, length)
        self.cpu[span] = self.device[span]


class Ring:
    def __init__(self):
        self.head = self.tail = 0
        self.items = deque()

    def push(self, item):
        if len(self.items) == RING_DEPTH - 1:
            raise ValueError("MCQ ring full")
        self.items.append(item)
        self.tail = (self.tail + 1) % RING_DEPTH

    def pop(self):
        item = self.items.popleft()
        self.head = (self.head + 1) % RING_DEPTH
        return item


@dataclass(frozen=True)
class LegacySnapshot:
    hce: int = 0
    transfer_doorbell: int = 0
    task_doorbell: int = 0
    transfer_run: int = 0
    task_run: int = 0
    outstanding: int = 0

    def fields(self):
        return (self.hce, self.transfer_doorbell, self.task_doorbell,
                self.transfer_run, self.task_run, self.outstanding)


class UfsModel:
    def __init__(self, profile, dma, *, mcq=False, firmware_allows_mcq=False):
        if mcq and (profile["dt_disables_mcq"] or not firmware_allows_mcq):
            raise ValueError("MCQ not permitted by the model firmware policy")
        self.pool = DmaPool(profile["dma_windows"], dma)
        self.legacy_request = None
        self.legacy_completion = None
        self.active = True
        self.task_pending = False
        self.rings = [(Ring(), Ring()) for _ in profile["mcq_gic_intids"]] if mcq else []

    def submit(self, lba, descriptor_dma, queue=0):
        if not self.active:
            raise ValueError("controller is stopped")
        request = (lba, descriptor_dma)
        if self.rings:
            self.rings[queue][0].push(request)
        elif self.legacy_request is not None or self.legacy_completion is not None:
            raise ValueError("legacy slot is busy")
        else:
            self.legacy_request = request

    def transfer(self, disk, request):
        lba, desc = request
        entry = self.pool.device_span(desc, PRD.size)
        bus, reserved, last_byte = PRD.unpack(self.pool.device[entry])
        if reserved or last_byte != BLOCK_BYTES - 1 or bus % BLOCK_BYTES:
            raise ValueError("invalid or unpublished PRDT entry")
        target = self.pool.device_span(bus, BLOCK_BYTES)
        if entry.start < target.stop and target.start < entry.stop:
            raise ValueError("descriptor and data DMA overlap")
        disk.seek(lba * BLOCK_BYTES)
        block = disk.read(BLOCK_BYTES)
        if len(block) != BLOCK_BYTES:
            raise ValueError("UFS READ outside the fixture")
        self.pool.device[target] = block

    def step(self, disk, queue=0):
        if self.rings:
            sq, cq = self.rings[queue]
            if len(cq.items) == RING_DEPTH - 1:
                raise ValueError("MCQ completion ring full")
            request = sq.pop()
        else:
            request = self.legacy_request
            self.legacy_request = None
        if request is None:
            raise ValueError("no pending UFS request")
        try:
            self.transfer(disk, request)
            completion = "ok"
        except ValueError as error:
            completion = str(error)
        if self.rings:
            cq.push(completion)
        else:
            self.legacy_completion = completion

    def reap(self, queue=0):
        if self.rings:
            return self.rings[queue][1].pop()
        completion = self.legacy_completion
        self.legacy_completion = None
        return completion

    def legacy_state(self):
        busy = self.legacy_request is not None
        return LegacySnapshot(int(self.active), int(busy), int(self.task_pending), int(self.active),
                              int(self.task_pending), int(busy) + int(self.task_pending))

    def mcq_state(self):
        return [dict(sq_head=sq.head, sq_tail=sq.tail, cq_head=cq.head, cq_tail=cq.tail)
                for sq, cq in self.rings]

    def stop(self):
        if (self.legacy_request is not None or self.legacy_completion is not None or self.task_pending or
                any(sq.items or cq.items for sq, cq in self.rings)):
            raise ValueError("UFS queues not drained")
        self.active = False


def refused(action, expected):
    try:
        action()
    except ValueError as error:
        assert expected in str(error), error
        return str(error)
    raise AssertionError(f"model failed to refuse: {expected}")


def exercise_model(dtb, sources, disk_path, gpt):
    profile, dma = load_profile(dtb, sources)
    with disk_path.open("rb") as disk:
        disk.seek(gpt["root_offset"])
        expected = disk.read(BLOCK_BYTES)
        assert expected[1024:1026] in (b"H+", b"HX")
        lba, tail = divmod(gpt["root_offset"], BLOCK_BYTES)
        assert not tail

        def submit(model, *, lba=lba, clean=True, target=None, queue=0):
            pool = model.pool
            address = pool.address(BLOCK_BYTES, BLOCK_BYTES) if target is None else target
            PRD.pack_into(pool.cpu, 0, address, 0, BLOCK_BYTES - 1)
            if clean:
                pool.sync_for_device(0, PRD.size)
            model.submit(lba, pool.address(0, PRD.size), queue)

        legacy = UfsModel(profile, dma)
        submit(legacy, lba=0)
        pending = legacy.legacy_state()
        legacy_busy = refused(legacy.stop, "queues not drained")
        refused(lambda: submit(legacy), "slot is busy")
        legacy.step(disk)
        assert legacy.reap() == "ok"
        legacy.pool.sync_for_cpu(BLOCK_BYTES, BLOCK_BYTES)
        sector = gpt["sector_bytes"]
        assert legacy.pool.cpu[BLOCK_BYTES + sector:BLOCK_BYTES + sector + 8] == b"EFI PART"
        submit(legacy)
        legacy.step(disk)
        assert legacy.reap() == "ok"
        stale_data = bytes(legacy.pool.cpu[BLOCK_BYTES:]) != expected
        assert stale_data and legacy.pool.device[BLOCK_BYTES:] == expected
        legacy.pool.sync_for_cpu(BLOCK_BYTES, BLOCK_BYTES)
        assert legacy.pool.cpu[BLOCK_BYTES:] == expected
        legacy.stop()
        clean_state = legacy.legacy_state()
        assert not any(clean_state.fields())

        task = UfsModel(profile, dma)
        task.task_pending = True
        task_pending = task.legacy_state()
        task_busy = refused(task.stop, "queues not drained")

        stale = UfsModel(profile, dma)
        submit(stale, clean=False)
        stale.step(disk)
        no_clean = stale.reap()
        assert no_clean == "invalid or unpublished PRDT entry" and not any(stale.pool.device[BLOCK_BYTES:])

        window = profile["dma_windows"][0]
        fault_address = window["dma_start"] + window["bytes"]
        outside = UfsModel(profile, dma)
        submit(outside, target=fault_address)
        outside.step(disk)
        dma_fault = outside.reap()
        assert dma_fault == "DMA request is unmapped or ambiguous" and not any(outside.pool.device[BLOCK_BYTES:])
        refused(lambda: outside.pool.device_span(POOL_PA + POOL_BYTES, BLOCK_BYTES), "model-owned pool")

        mcq_denied = refused(lambda: UfsModel(profile, dma, mcq=True), "not permitted")
        mcq = UfsModel(profile, dma, mcq=True, firmware_allows_mcq=True)
        queue = len(mcq.rings) - 1
        submit(mcq, queue=queue)
        sq_pending = mcq.mcq_state()[queue]
        refused(mcq.stop, "queues not drained")
        mcq.step(disk, queue)
        cq_pending = mcq.mcq_state()[queue]
        refused(mcq.stop, "queues not drained")
        assert mcq.reap(queue) == "ok"
        mcq.pool.sync_for_cpu(BLOCK_BYTES, BLOCK_BYTES)
        assert mcq.pool.cpu[BLOCK_BYTES:] == expected
        # Wrap both rings and check that the other queues remain empty.
        for _ in range(RING_DEPTH - 1):
            submit(mcq, queue=queue)
            mcq.step(disk, queue)
            assert mcq.reap(queue) == "ok"
        mcq.stop()
        assert not any(value for state in mcq.mcq_state() for value in state.values())
        assert sq_pending == dict(sq_head=0, sq_tail=1, cq_head=0, cq_tail=0)
        assert cq_pending == dict(sq_head=1, sq_tail=1, cq_head=0, cq_tail=1)

    model_cases = {
        "matched": (1, clean_state, 0x3f),
        "busy_queue": (1, pending, 0x3f),
        "busy_task_queue": (1, task_pending, 0x3f),
        "mcq_mode": (2, mcq.legacy_state(), 0x3f),
        "missing_dma": (1, clean_state, 0x2f),
        "missing_cache": (1, clean_state, 0x1f),
    }
    report = dict(profile=profile, read_lba=lba, block_bytes=BLOCK_BYTES,
                  block_sha256=hashlib.sha256(expected).hexdigest(), legacy_gpt_and_hfs_read=True,
                  legacy_busy=legacy_busy, task_busy=task_busy, missing_descriptor_clean=no_clean,
                  data_stale_before_cpu_sync=stale_data, dma_outside_window=dma_fault,
                  mcq_firmware_denial=mcq_denied, mcq_test_queue=queue,
                  mcq_sq_pending=sq_pending, mcq_cq_pending=cq_pending, mcq_wrap_and_drain=True,
                  handoff_cases={name: dict(mode=mode, proof=proof, legacy=vars(state))
                                 for name, (mode, state, proof) in model_cases.items()},
                  physical_ufs_authorized=False)
    return report, model_cases


def check_guest_legacy_trace(trace, allowed):
    queue = re.findall(r"(?m)^ufs_(process_db|complete_req) UTRLDBR slot (\d+)$", trace)
    failures = re.findall(r"(?m)^ufs_err_dma_\w+.*$", trace)
    assert not failures, failures
    if allowed:
        assert queue and len(queue) % 2 == 0
        assert queue == [(event, "0") for _ in range(len(queue) // 2)
                         for event in ("process_db", "complete_req")], queue
    else:
        assert not trace.strip()
    return dict(virtual_legacy_requests=len(queue) // 2, virtual_dma_errors=len(failures))
