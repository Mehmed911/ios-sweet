# Duchamp hardware specifications

The generated hardware.json and docs/MT6897_HARDWARE_MAP.md are canonical.
SoC: MT6897; device: POCO X6 Pro 5G. Target A715/A510 and Mali-G615 MC6 identities
come from the device description; do not use a foreign core/GPU initialization.
Captured RAM is 12 GiB from 0x40000000, including substantial reserved ranges.
The existing inherited framebuffer is 1220x2712, stride 4992, 32-bit.

Unknown runtime ownership is explicitly UNKNOWN in every generated node.
No device serial, bootargs, firmware, DTB/DTBO binary or system image is included.
