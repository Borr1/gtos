# KB cycle 67 — execution-geometry optimization (multi-agent Workflow; owner directive "stops/targets too far")

**Setup.** Workflow of 5 opus agents, one per geometry dimension, each fitting on TRAIN(≤2021) and scoring
OOS(2022-24)+SEALED(2025+) ONCE, on the deployed metals FVG-retest stream (W5.wf_stream(2.0), 482 trades,
baseline WF full R +0.2264 / sealed mean-R 0.2271). Adversarial verify phase deflated by the TOTAL 150-trial
budget (DSR/Bonferroni + block-permutation + paired bootstrap). Principal independently re-derived the winner.

## RESULT — 1 of 5 dimensions yields a REAL improvement; the other 4 are within-noise/overfit.

**CONFIRMED REAL — volatility-regime TRADE FILTER (not a stop/target change).** Drop entries when
`atr_ratio > 1.8` (ATR14 at the decision bar > 1.8× its own 100-bar average) — i.e. don't enter on
volatility EXTREMES. Confirms the cycle-26/c35 prior on the sealed slice with deflation:
- SEALED: mean-R **0.227 → 0.444 (~doubling)**, R-per-bar **0.020 → 0.044 (2.2×)**, win-rate 0.42 → 0.50,
  median bars-to-exit 5 (drops ~21% of trades, the bad-regime ones). Verified: reproduces exactly, no
  look-ahead (atr_ratio backward-only), pre-registered minimal-intervention pick (gentlest cap that raises
  TRAIN = 1.8, NOT the leaky max-over-40), bounded (only drops trades), survives 150-trial deflation
  (block-perm p~0.0003-0.0015 → Bonferroni 0.0015-0.04; bootstrap CI lower bound positive at all block sizes).
- **HONEST CAVEATS (verifier-flagged, material):** (1) the value is REGIME-CONCENTRATED — almost all of it
  is the 2025-2026 metals vol-spike (TRAIN benefit only +0.026); (2) the OOS win is statistically
  half-supported (only 3 high-vol trades existed in calm 2022-24); (3) at the most conservative
  block-20+Bonferroni-150 the deflated p is borderline (~0.18), though block-5/10 clear. So: real and
  deflation-surviving, but its forward generalization to OTHER regimes is an inductive assumption.

**REJECTED (within-noise / overfit), the direct "move the lines" changes — the important insight:**
- **STOP** (ATR-multiple, train-best 1.5×): +0.045R sealed = WITHIN NOISE (paired t=0.42, perm p=0.37, drop
  one trade → collapses). Notably the train-best stop was ~1.39× WIDER, not tighter, and it DEGRADED
  R-per-bar + doubled hold time. Tightening the stop did NOT win.
- **TARGET/EXIT** (trail-after-peak, deeper fixed): did not robustly beat on both splits.
- **DEEPER TARGET 3×ATR / Fib-1.272** (levels_ml): +0.06R sealed = WITHIN NOISE; win-rate COLLAPSES
  0.42→0.33, per-trade Sharpe DECLINES — it just harvests the fat tail at higher variance; multiplicity
  artifact (15/45 variants "beat both splits"). Rejected.
- **ENTRY** (deeper-pullback, W3): faster (median 3 bars) + higher win (0.435) but the agent did not claim a
  robust both-splits beat (n shifts to 193) → LEAD, not confirmed.

## THE DEEP INSIGHT (refines the owner's hypothesis — report honestly)
The excursion data (c66) made stops/targets LOOK too far. But rigorously re-backtesting tighter stops /
closer targets / trails through the machine, they do NOT robustly beat the baseline — **because the metals
edge's expectancy lives in the FAT RIGHT TAIL** (a minority of trades run to 4-14R). Tight targets cut the
tail that pays; tight stops cut runners. So the geometry lines are closer to optimal than the percentiles
suggested. **The real lever is WHICH TRADES to take (entry/trade selection by regime), not WHERE to move the
stop/target.** That is actually the "knowing exactly when/where to enter" part of the owner's vision — and
it's the dimension that produced the one real win (the vol-extreme filter).

## DISPOSITION
- **Vol-cap ≤1.8 entry filter:** a sealed-validated, deflation-surviving refinement of the deployed metals
  entry (confirms c26/c35). Candidate to wire into the live metals sleeve — GATED, owner-decides, AFTER
  verifying the live sleeve's entry parity (the live gate is a vol FLOOR; this adds an upper CAP). Caveat:
  regime-concentrated; deploy as a conservative quality filter (it only drops trades, never adds risk).
- **Leads for the continuing geometry program:** (a) deeper-pullback ENTRY (faster, higher win — re-test for
  a robust both-splits beat); (b) confluence STACKING beyond single vol-cap (2-3 conditions, trial-budgeted);
  (c) a deeper ML reach-predictor (this cycle's shallow tree didn't win); (d) the same geometry pass on the
  us_equity sleeve. The owner's broader vision (advanced geometry/quant levels, arbitrage, ML) is multi-cycle;
  this is cycle 1 with 1 real win + leads, NOT a closure.

**Files.** `geom_{stop,target_exit,entry,confluence,levels_ml}.py`, `GEOM_*_RESULT.json`, Workflow
wf_c8bc27da-436.
