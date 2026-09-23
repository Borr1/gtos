# KB cycle 75 — DEPLOYMENT GATE: the deep-target "breakthrough" largely evaporates at vol-matched book sizing (HONEST CORRECTION)

The live W7 integrator (INTEG_W7 T1) recorded that lifting targets is NET NEGATIVE at the vol-matched book
MC (lower Sharpe, higher maxDD tail, SLOWER days-to-pass). My c71-73 deep-target win measured mean-R + R-per-
bar (both rise with depth) but NEVER Sharpe / variance / vol-matching. Decisive iso-vol test (metals
per-decision-day series, 2R vs 6R, challenge MC at fixed AND vol-matched base). `CYCLE75_DEEP_TARGET_ISOVOL.json`.

## RESULT — T1 substantially CONFIRMED; my c71-73 over-claimed (same-base mean-R artifact).
- **Sharpe (the metric I missed):** 2R daily Sharpe 0.0912 vs 6R 0.1026 — only MILDLY higher on the metals
  core (not the 2.6× the mean-R implied; and T1 found it LOWER on the full 11-sleeve book).
- **maxDD tail:** 2R cumulative DD 9.54% vs 6R **26.96%** at 1% sizing — deep target ~3× the drawdown tail
  (T1's "higher maxDD tail" CONFIRMED). Variance, not return, dominates the deepening.
- **Challenge MC (FN +8%, static floor, smooth-defense):**
  - SAME base 2.0%: 2R pass 0.86 / 17d ; 6R pass 0.76 / 8d (faster but LOWER pass-rate + the 27% DD tail).
  - VOL-MATCHED (iso-ruin: 6R sized DOWN to 1.16% to equal daily vol): 2R pass 0.86 / **17d** ; 6R pass 0.99
    / **21d** — at controlled risk the deep target is SLOWER (21>17d), though higher pass-prob + lower
    worst-day (−1.21% vs −2.09%). T1's "SLOWER days-to-pass" CONFIRMED.

## HONEST CORRECTION (the deployment gate caught a 2nd over-claim — after c74 caught the prediction layer)
- My c71/c72/c73 "deep target ~doubles per-trade R, faster velocity, deployable at 2.0%" was measured at the
  SAME base on mean-R + R-per-bar — which IGNORES the variance explosion. At the deployment-relevant basis
  (vol-matched / iso-ruin), the deep target does NOT deliver faster passes or more return — its higher mean
  is offset by ~3× the DD tail, forcing a size-down that makes it SLOWER. The "breakthrough" was a
  measurement artifact (wrong metric: mean-R instead of vol-matched Sharpe + maxDD-tail + iso-ruin speed).
- What IS true: at iso-vol the deep target is a RIGHT-SKEWED, SAFER-BUT-SLOWER risk-profile dial (higher
  pass-prob 0.99 vs 0.86, lower worst-day) — an OPTION for a pass-probability-maximizing owner, NOT a
  return/speed win. The live book's FIXED targets are defensible (the W7 builders were right; T1 stands).
- LESSON (program-level): per-trade mean-R / R-per-bar are the WRONG deployment metrics for a fat-tailed
  edge under a maxDD cap. The right metric is vol-matched Sharpe + maxDD-tail + iso-ruin days-to-pass. Apply
  this to ALL future geometry/sizing claims (re-audit any that used mean-R).

## DISPOSITION (corrected)
- **Deep target: NOT a deploy-now breakthrough.** Do NOT wire it as a "faster/more-return" change. It is a
  risk-profile dial (safer+slower at iso-ruin) — present it to the owner as an option, not a recommendation.
- The genuinely-shipped wins this session stand on their own basis: smooth DD-defense + 2.0% sizing (c61, the
  faster-passes lever, measured at iso-ruin on the live book) and the validation machine. The c67 vol-cap is
  a (regime-concentrated) selection filter. The deep target and the ML/prediction cells are NOT deploy wins.
- The honest north-star status: per-trade EDGE QUALITY on MT5 is largely EXHAUSTED (prediction unpredictable
  c74; deep target a same-base artifact c75) — the remaining levers are SIZING/governor (shipped) + live/paid
  data. This is the deployment gate preventing a wrong live change.

**Files.** `CYCLE75_deep_target_isovol.py`, `KNOWLEDGE_BASE/validation/CYCLE75_DEEP_TARGET_ISOVOL.json`.
