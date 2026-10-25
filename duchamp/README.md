# Duchamp device port

This directory is the device-specific port boundary for the POCO X6 Pro 5G
(`duchamp`, MediaTek MT6897). `board.toml` records values measured from the
live device tree and local read-only extraction.

The current milestone is preflight-only. The loader validates and materializes
the XNU payload into a bounded memory window, and the handoff layer tests the
MMU/cache/entry sequence through callbacks. No callback is a MediaTek firmware
implementation, and no boot or partition-writing path is enabled.

The Qualcomm shim under `shim/` is intentionally outside this port and refuses
`duchamp` and `mt6897` targets. A future UEFI or LK-compatible MediaTek backend
must be added here only after its entry contract is established from Duchamp
firmware and tested without modifying boot partitions.
