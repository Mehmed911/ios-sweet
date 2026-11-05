# Duchamp UFS resource-binding capture

`capture-duchamp-ufs-resource-bindings.py` records a bounded, read-only view of
the Linux drivers currently bound to the MT6897 UFS controller, PHY, clocks,
reset providers, DVFSRC, SCPSYS, regulators, SLB observer and UFS IRQ handlers.

The report deliberately distinguishes three facts:

1. A Linux provider or handler is bound now.
2. SLB/SCMI and firewall/protection modules are loaded now.
3. Neither fact delegates the resource, firmware ABI, firewall, system cache or
   interrupt controller to XNU.

The command performs no phone write, module load, SELinux-policy change, MMIO,
SMC, DMA, UFS command or block-device access.  The physical backend remains
disabled, and every XNU authorization field remains false.

The pinned 2026-11-05 capture proves eight Linux driver bindings, three UFS
regulator observations and nine UFS IRQ-handler bindings on active slot `_a`.
Its SHA-256 is
`aaecd9757df5291eeab90ade83cba46d4be73cf57d710ac0bb5e60f6977119f7`.
