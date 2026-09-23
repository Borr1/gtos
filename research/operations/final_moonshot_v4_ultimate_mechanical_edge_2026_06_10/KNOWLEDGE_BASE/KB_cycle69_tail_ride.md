# KB cycle 69 — WIDE-MOVEMENT (fat-tail) prediction + reach-conditioned dynamic geometry — the owner's thesis CONFIRMED

**Owner directive:** the wide movements (big runners) are where the money is — predict WHICH trades become
runners and RIDE those, filter/tighten the rest, with real quant. Tested by the principal (no subagents —
session-limited; better for the load-bearing call anyway), leak-free, on the deployed metals stream (482
trades), reusing `SELECTION_FEATURE_STORE.jsonl` (entry_idx + 13 decision-bar features + mfe_R) + geometry_lib.

## RESULT — the strongest geometry/selection finding in the program; directly validates the thesis.

**(1) The ceiling is enormous (ORACLE = perfect tail knowledge).** Riding the reach≥4R trades with a DEEP 6R
target (fixed-2R the rest): sealed mean-R **0.227 → 0.962 (4.2×)**, OOS 0.399 → 1.361. Fixed-2R caps the
runners at 2R and leaves the fat tail on the table — exactly the owner's point. (A TRAILING ride is NEGATIVE
−0.08/−0.18 — it gives the tail back on pullbacks; the correct ride is a DEEP FIXED target.)

**(2) The tail is genuinely predictable (better than the 2R-hit).** Train-fit logistic on 13 decision-bar
features → tail (mfe_R≥4R): AUC train 0.748 / OOS 0.688 / **SEALED 0.671** (overfit gap only 0.077). The
big runners are MORE predictable than the binary 2R-hit (c68 AUC 0.64) — predicting magnitude/tail is the
better-posed target, as the owner intuited.

**(3) The realistic dynamic policy beats fixed-2R, robustly.** Ride the predicted top-tercile (threshold on
TRAIN) with a deep 6R target, fixed-2R the rest:
- SEALED: mean-R **0.227 → 0.489 (~2.15×)**, ride 44/181 trades, **beats RANDOM riding of the same n at
  p=0.0076** (the right null — accounts for fat-tail variance). 
- ROBUST: drop top 1/2/3 ridden winners → delta holds +0.24/+0.22/+0.20 (NOT an outlier artifact).
- BOTH sealed years positive: 2025 +0.393 (n=108), 2026 +0.069 (n=73).
- Within-cycle trial budget low (~6: 2 ride modes × tercile × predictor) → deflated p ≈ 0.046, still sig;
  and it is a DIRECTED test of a strong prior (owner thesis + c66 fat tail), not a blind search.

## WHY THIS WORKS WHERE c67/c68 WERE MARGINAL
c68 selected trades but kept the FIXED 2R exit → upside capped at 2R (limited gain, within-noise). c69 (a)
predicts the TAIL specifically (AUC 0.67 > 0.64) and (b) RIDES it with a deep target (captures the fat tail's
4-14R). Better target + capturing the upside = a real, robust improvement. This is the synthesis of the
owner's two points: filter for quality (predict) AND ride the wide movements (deep exit on the predicted runners).

## HONEST TIER + CAVEATS (real, needs live-confirm + sizing re-validation — NOT certified-deploy-now)
- SEALED is strong + robust; OOS (2022-24) is directionally strong (+0.45) but NOT significant (p=0.11) on a
  tiny sample (54 trades, 23 ridden). 2026 benefit is small (+0.07) — some regime concentration (2025).
- The deep-6R ride RAISES return VARIANCE (fewer hits, bigger payoffs). This changes the daily-P&L
  distribution → the c61 sizing / governor / −5% daily-limit analysis MUST be re-run on the deep-target
  distribution before any live sizing (a 6R-target metals cluster is a bigger daily swing).
- → Disposition: REAL, deployable CANDIDATE (gated): a predict-tail-and-ride-deep dynamic-geometry layer on
  the metals sleeve. Wire gated; re-validate sizing on the new distribution; live-confirm the predictor on
  virgin trades (the frozen tail-model + the deep-ride policy, pre-registered here).

## NEXT
- Re-run the c61 sizing analysis on the deep-ride return distribution (does the fatter tail breach −5% daily
  at the target base? probably need lower base or the smooth-defense).
- Combine with the c67 vol-cap (drop vol-extreme entries) — selection AND tail-ride together.
- Stronger tail predictor (more features / the moonshot follow-avoid-mixed conditions, validated mechanically).
- Apply to the us_equity sleeve (harness `eq_stream()` is built).

**Files.** `CYCLE69_tail_ride.py`, `KNOWLEDGE_BASE/validation/CYCLE69_TAIL_RIDE.json`.

---
## CORRECTION (cycle 71 — adversarial verification deflated this)
The adversarial verification (tail_v2 Workflow) found c69 OVER-CLAIMED the PREDICTION's role: the ML
tail-selection is WITHIN-NOISE at the 51-trial deflation and OOS-INSIGNIFICANT (p≈0.11-0.13). It reproduces
exactly and is leak-free, and it survives simple nulls (rand-sel p=0.0069, block-rot p=0.0056), but NOT the
strict trial-budget bar. Critically, **ride-ALL-deep with NO predictor beats the selective policy on raw
mean-R** → the DEEP TARGET, not the prediction, is the driver. The prediction retains only a minor
risk-adjusted role (Sharpe/win-rate). See KB_cycle71_deep_target.md: the robust, every-year-positive,
paired-significant, downside-neutral finding is simply DEEPENING THE TARGET to ~6R. Treat c69's "predict +
ride" as superseded by c71's "deepen the target" (+ optional selection refinement, not the edge).
