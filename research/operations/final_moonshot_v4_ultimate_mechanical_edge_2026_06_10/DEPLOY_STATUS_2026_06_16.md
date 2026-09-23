# DEPLOY STATUS — 2026-06-16 (current honest state for the VPS session)

## Caches (this commit) — for core-8 re-validation on the VPS
`INTEG_W3_streams_cache.pkl` (454K) + `INTEG_W5_new_streams_cache.pkl` (208K): the W3/W5 stream caches the
VPS needs to rebuild the core-8 book / re-run the W7 harness locally (the live session's prior #1 residual —
caches were present on the research laptop, absent on the VPS). Small, plain git blobs.

## What genuinely SHIPS (gated; iso-ruin-measured, on this branch)
- **Smooth DD-defense governor** (`GTOS_UB_DERISK_MODE=smooth`) + **base 1.25%→2.0%** (`clean3_w7_ceiling_nom2p00`)
  + the **≥2.0%-ceiling smooth-required interlock**. Measured on the LIVE W7 book MC (vol-matched/iso-ruin):
  FN +8% 80→55d, FTMO +10% 124→94d (~25-30% faster), P(pass) 1.0, 0% daily-breach. THE real win. See
  `RESEARCH_MERGE_ACTIVATION_GUIDE_2026_06_15.md` (activation/check/monitor/rollback).
- **Validation machine** (`src/research_infra/validation_integrity/`, 75 tests) — clean-add.
- **vol-cap entry filter** (atr_ratio≤1.8) — a regime-concentrated metals quality filter (gated option).

## What was investigated and does NOT deploy (honest — verified out)
- **Deep target (≥6R):** looked like a 2.6× win on per-trade mean-R (c71-73), but the DEPLOYMENT GATE (c75,
  vol-matched/iso-ruin) showed it's a SAME-BASE artifact — at controlled risk it's SLOWER (21 vs 17d) with
  ~3× the maxDD tail; the live W7 integrator (T1) already found "lifting targets is net-negative at the
  vol-matched book MC". KEEP the live FIXED targets.
- **Per-trade ML/prediction (reach-selection, regime-depth, adaptive-target, stop-by-MAE):** the per-trade
  outcome is NOT forecastable from decision-bar features OOS (c74; CONFIRMED_REAL=[]). Dead end on MT5.

## Honest north-star state
Per-trade edge QUALITY on MT5 is largely exhausted (prediction unpredictable; deep-target a sizing artifact;
breadth cost-capped). The deployable lever is SIZING/governor (shipped here) + LIVE/PAID data going forward.
Full research detail lives on the research branch (not pushable — old science-program LFS history exceeds
GitHub's 2GB object limit); this branch carries the deployable package + the honest deploy decision.
