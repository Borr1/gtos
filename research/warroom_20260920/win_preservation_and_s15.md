# Win preservation + S15 seeds — 2026-09-20 08:45 ICT

## LABEL 293128383
KEEP×Off_hours×false_structure — S15 review only, **not hard-off**.

## Win preservation under G4–G8
wins n=7 (XAU 5 / FX 2)
tape wins sumR=15.921 → shadow 15.0685
XAU wins tape 11.089 → shadow 10.2365
FX wins tape 4.832 → shadow 4.832
allow_full n=6
wrongly_cut KEEP/REJECT n=0
nonkeep wins still size-cut n=1
- CUT_WIN 292667008 XAU dsp_three_fresh tapeR=3.41 shadowR=2.5575 mult=0.75 rules=['G6_SESSION_0_75']

## Extend beyond 60
mt5_extra=0 label_extra=0 — combined-60 already = locked51 + ingest9; MT5 dump had exactly those 60 closed. No further Challenge closes on tape.

## S15 cost-row seeds
- **S15_FS_HALF_STILL_LOSING** n=21 tapeR=-21.4804 shadowR=-8.7127 — G4 size×0.5 applied; residual loss remains — S15 cost of false_structure admits after half-size
- **S15_KEEP_OFFHOURS_FS_SINGLETON** n=1 tapeR=-0.94 shadowR=-0.94 — Review false admit vs keep surface — NOT hard-off
- **S15_INDEX_REJECTS** n=16 tapeR=-16.6386 shadowR=0.0 — Cost avoided by G1 hard gate — shadow residual 0; tape bleed for Dig cost sheet
- **S15_CRYPTO_ORB_REJECTS** n=3 tapeR=-3.28 shadowR=0.0 — Cost avoided by G3 orb_crypto hard gate
