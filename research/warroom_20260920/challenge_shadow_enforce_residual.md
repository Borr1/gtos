# Challenge shadow ENFORCE residual — 2026-09-20 08:44 ICT
tape sumR **-38.5948** → shadow residual **0.5857** (Δ 39.1805)
reject=23 allow_cut=29 allow_full=8

## Residual sumR by asset
- **XAU** n=33 tape=-16.413 shadow=-2.1797 Δ=14.2333 reject=0 cut=28
- **INDEX** n=16 tape=-16.6386 shadow=0.0 Δ=16.6386 reject=16 cut=0
- **CRYPTO** n=3 tape=-3.28 shadow=0.0 Δ=3.28 reject=3 cut=0
- **FX** n=8 tape=-2.2632 shadow=2.7654 Δ=5.0286 reject=4 cut=1

## Rule hits
`{'G4_XAU_DSP_FS_HALF': 21, 'G6_SESSION_0_75': 23, 'G8_ORIG_STOP_NO_SILENT_REENTRY': 30, 'G2_XA_HUGE': 4, 'G1_INDEX': 16, 'G5_EVENT_GAP_SHADOW': 3, 'G3_ORB_CRYPTO': 3, 'G7_KEEP_NO_BOOST_MAX1': 5}`

G6 amend: Asia included; Asia_London_pre + Off_hours left alone; keep_surface exempt
G8 amend: silent remint blocked; ≥15m only as new named fire
