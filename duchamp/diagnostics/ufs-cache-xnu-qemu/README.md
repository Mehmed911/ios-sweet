# XNU UFS cache backend — pinned QEMU execution

This directory pins the successful `test-duchamp-ufs-xnu.py --backends`
result from CI run `41740480659`, commit
`03a3f9d0141848f3245f86598e477ad36d8ade4b`.

The exact raw verification file has SHA-256
`ecb7460c49ca0475807749b15ee9c8b88da1d7e2bd8effe5c2398632e797e373`.
`tools/interpret-duchamp-xnu-cache-qemu.py` validates that result, the kernel
and payload hashes, every QEMU check, and the exact implementation blobs from
the CI commit.

The test executed the lease-bound cache backend inside the real XNU kernel in
QEMU. The success marker is emitted only after one clean-to-PoC callback, one
flush-to-PoC callback and three barriers complete, while the physical provider
path remains fail-closed. The same run mounted the read-only HFS root, reached
PID 1 and observed no panic.

This proves the XNU implementation and callback ordering. It does **not**
prove MT6897 outer/system-cache reachability, physical cache ownership,
firmware/firewall delegation, or UFS resource ownership on the phone. The
physical backend therefore remains disabled.
