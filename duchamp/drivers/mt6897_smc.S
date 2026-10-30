/* AArch64 SMCCC raw conduit. Caller supplies authorization and ABI proof. */
.text
.p2align 2
.global mb_smc_raw
.type mb_smc_raw,%function
mb_smc_raw:
    stp x19, x30, [sp, #-16]!
    mov x19, x1
    mov x9, x0
    ldp x6, x7, [x9, #48]
    ldp x4, x5, [x9, #32]
    ldp x2, x3, [x9, #16]
    ldp x0, x1, [x9]
    smc #0
    stp x0, x1, [x19]
    stp x2, x3, [x19, #16]
    ldp x19, x30, [sp], #16
    ret
.size mb_smc_raw,.-mb_smc_raw
