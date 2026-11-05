# MT6897 UFS SiP ABI receipt

This directory pins a normalized, offline receipt that joins four bounded
pieces of evidence:

1. the running Android UFS module GNU build-ID note matches the saved vendor
   module note byte for byte;
2. the saved module constructs SiP function ID `0xc2000276`, uses selectors
   `8`, `512`, and `1024`, and calls `__arm_smccc_smc`;
3. the captured BL31 sample registers the same function ID and dispatches the
   same selectors; and
4. the running BL31 identity strings match the captured sample identity.

`tools/verify-duchamp-ufs-sip-abi.py` reproduces the receipt from the ignored
raw evidence. This proves a static installed-client-to-BL31 ABI evidence chain.
It does **not** prove byte-for-byte installed secure-firmware equivalence, an
SMC return or physical effect, firewall state, XNU delegation, cache or
resource ownership, or physical UFS authorization. The physical backend stays
disabled.
