# BL31 runtime identity receipt

This directory pins the bounded read-only ATF log captured from Duchamp and a
normalized verification tying its four runtime BL31 identity fields to the
same fields extracted from the captured `tee_a` ATF entry.

`tools/verify-duchamp-bl31-runtime-identity.py` validates the exact 5 MiB
`tee_a` capture, its packaged ATF payload, the exact runtime log, and the
original read-only capture report. The producer performs no phone access,
SMC, MMIO, fastboot or partition operation.

The result proves that the running BL31 identifies as the analyzed captured
sample. It does not prove byte-for-byte equivalence with all installed secure
firmware, an SMC physical effect, firewall state, resource ownership, or UFS
authorization. Those gates remain fail-closed.
