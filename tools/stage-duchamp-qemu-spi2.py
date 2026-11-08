#!/usr/bin/env python3
"""Stage the Duchamp FocalTech protocol and QEMU SPI2 replay into XNU."""
import argparse
from pathlib import Path


SOURCES = (
    "duchamp/drivers/duchamp_ft3683g.c",
    "duchamp/drivers/duchamp_ft3683g.h",
    "duchamp/xnu/qemu_spi2_touch.c",
)
HID_ANCHOR = """void
SweetHIDButtons::testFired(OSObject *owner, IOTimerEventSource *sender)
{
	SweetHIDButtons *self = (SweetHIDButtons *)owner;
"""
HID_HOOK = """#if defined(DUCHAMP)
extern "C" int duchamp_qemu_spi2_touch_step(unsigned step);
#endif

""" + HID_ANCHOR + """#if defined(DUCHAMP)
	int spi2_delay = duchamp_qemu_spi2_touch_step(self->fTestCount);
	if (spi2_delay) {
		if (spi2_delay > 0) {
			++self->fTestCount;
			sender->setTimeoutMS(spi2_delay);
		}
		return;
	}
#endif
"""


def stage(root):
    repo = Path(__file__).resolve().parents[1]
    paths = {root / "bsd/dev" / Path(src).name: (repo / src).read_bytes() for src in SOURCES}
    config = root / "bsd/conf/files"
    hid = root / "iokit/Kernel/arm/hid/SweetHID.cpp"
    config_text = config.read_text()
    hid_text = hid.read_text()
    anchor = "bsd/dev/sweet_touch.c\t\t\tstandard\n"
    entries = ("bsd/dev/duchamp_ft3683g.c\t\tstandard\n"
               "bsd/dev/qemu_spi2_touch.c\t\tstandard\n")
    if HID_HOOK in hid_text:
        if anchor + entries not in config_text or any(
            not path.is_file() or path.read_bytes() != data for path, data in paths.items()
        ):
            raise ValueError("partial or changed SPI2 integration")
        return
    if config_text.count(anchor) != 1 or hid_text.count(HID_ANCHOR) != 1:
        raise ValueError("unexpected SWEET source anchors")
    if any(path.exists() for path in paths) or any(path.name in config_text for path in paths):
        raise ValueError("refusing to overwrite an existing SPI2 integration")
    for path, data in paths.items():
        with path.open("xb") as target:
            target.write(data)
    config.write_text(config_text.replace(anchor, anchor + entries, 1))
    hid.write_text(hid_text.replace(HID_ANCHOR, HID_HOOK, 1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xnu", type=Path)
    args = parser.parse_args()
    try:
        stage(args.xnu)
    except (OSError, ValueError) as error:
        parser.exit(1, f"QEMU SPI2 staging failed: {error}\n")
