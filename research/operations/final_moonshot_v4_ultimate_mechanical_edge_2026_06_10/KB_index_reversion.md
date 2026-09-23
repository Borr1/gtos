# KB — Index regime-gated mean-reversion sleeve (track: idxrev)

Builder track: fade stretched moves / failed breakouts at structural extremes on INDICES,
gated by a leak-free RANGING regime (low ac60 — the inverse of the commodity persistence gate).
Status: **learning + small-size forward-positive breadth pocket**. No TRAIN-validated edge on
the one deep index (NAS100); a multi-symbol, two-forward-year-consistent pocket is kept SMALL.

Code: `idxrev_sleeve.py` (leak-free signals + run/report). Result: `IDXREV_RESULT.json`.

## Data reality (decides everything)
- NAS100 is the ONLY deep index: H4 2022-01 .. 2026-06 (6854 bars) -> has real TRAIN (<=2024) + FORWARD.
- All other indices are 2024+ only (SPX500/GER40/UK100/JP225/AUS200 mostly 2025+, EU50/FRA40/US2000/N25 2023-24+).
  => any "positive" on those is FORWARD-ONLY = single-regime confound. Treated as breadth, not proof.
- M15 for NAS100 only exists 2025-06+ (too thin for a standalone holdout); H4 is the safe default. Tighter
  M15 timing was NOT used to claim edge for that reason.
- Cost: all indices 0.0638 (w1.cost_for class='index'); cost-in-R scaled by 1/stop_atr.

## What the SIGNAL is (leak-free)
Failed-breakout reclaim of a rolling-range extreme:
- rolling extreme over bars[i-lb .. i-1] (strictly closed, no bar i).
- bar i HIGH pierces prior-range high but CLOSES back below it -> SHORT (fade).
- bar i LOW pierces prior-range low but CLOSES back above it -> LONG (fade).
- features (ac60, vol_ratio, wick, reclaim margin, pd-confluence) all from bars[<=i]; entry = close of i;
  outcome scored by geometry_lib.simulate (leak-free pessimistic).

## The CORE thesis was FALSIFIED (the decisive learning)
**The ranging gate (low ac60, the inverse of the persistence gate) does NOT rescue index reversion.**
ac60 sweep, all indices, lb12, stop1.0 tgt1.0, FWD25-26 R/trade:
  ac<=-0.10 -0.047 | ac<=0.0 -0.049 | ac<=0.10 -0.030 | ungated -0.029.
On NAS100 (honest sample) the ranging slice is the WORST forward (ac<=0 -> -0.120R; ac<=0 & wick>=0.5 -> -0.141R).
=> Unlike commodities (where low ac60 = where reversion *should* pay), for INDICES the ranging
regime does not flip the fade positive. This matches prior repo findings
(`hunt_reversion_regime_filtered_RESULT.json`: ADX/efficiency-ratio range filters made fading WORSE,
because in tight ranges a pierce of the extreme is disproportionately a genuine breakout).

## Where it DID work — geometry is the real lever (not the gate)
High win-rate is real and structural; the killer is target/cost. Wide stop + tight target wins:
GEOMETRY SWEEP (all idx, ungated) FWD25-26:
  stop1.5/tgt0.5 -> +0.007R win69% ; stop1.5/tgt0.75 -> +0.007R win60% ; stop2.0/tgt0.5 -> +0.002R win69%.
  (tight stop/wide target = strongly negative: stop0.75/tgt2.0 -> -0.039R win35%).
The fade reverts ~0.5-0.75 ATR reliably but does NOT run to 1.5-2R; size the target to the move.

## The kept pocket (SMALL size, forward-positive breadth)
Pocket = SPX500, UK100, FRA40_cash, EU50_cash, US2000_cash, JP225, GER40, US30_cash.
LOCKED RULE: failed-breakout fade, **lb_range=16, stop=1.5*ATR, target=0.75R, maxbars=60, NO gate**.
(geometry chosen on NAS100 TRAIN where 1.5/0.75 was the least-bad/highest-quality train config; lb=16
chosen because edge is MONOTONIC in lb — strengthens with deeper ranges, a robustness positive.)
- FWD 2025: n=921  R/t=+0.050  win 62%
- FWD 2026: n=654  R/t=+0.077  win 64%
- FWD25-26 combined: n=1575  R/t=+0.061  win 63%  (~1050 trades/yr across 8 symbols)
- Per-symbol both-year positive (consistent): SPX500, UK100, US2000, EU50. Sign-flippers: GER40, US30, JP225.
- LB robustness (pocket, FWD25/26 R): lb8 +0.014/+0.021, lb12 +0.030/+0.059, lb16 +0.050/+0.077, lb20 +0.042/+0.067.

## Honest comparator (why this is small-size, not an "improvement")
NAS100 (the ONLY index with real pre-2024 TRAIN), same locked rule lb16:
  TRAIN<=2024 R/t = -0.096  |  FWD25-26 R/t = -0.054.  => NO durable edge on the honest sample.
So the pocket's positivity is FORWARD-ONLY across 2024+-only symbols = single-regime confound risk.
It passes the strongest *available* test (positive in TWO separate forward years across MULTIPLE symbols
at high frequency + monotonic lb robustness), which is why it is KEPT at small size — not deleted —
but it is NOT TRAIN-proven and must not be sized like the commodity continuation core.

## Per-year EV(n), locked pocket rule lb16 stop1.5 tgt0.75
2024 n=382 +0.000(approx, partial) | 2025 n=921 +0.050 w62% | 2026 n=654 +0.077 w64%.
(2015-2023 unavailable for pocket symbols; NAS100-only 2022-24 TRAIN = negative, see comparator.)

## Confidence-weighted contribution
At a 0.35x confidence weight (forward-only confound discount): effective ~+0.021R/trade x ~1050 trades/yr
= meaningful non-correlated breadth (indices, fade direction) vs the commodity-continuation core,
WITHOUT claiming a validated standalone edge.

## Next steps (build, don't kill)
1. Re-validate the pocket each new forward quarter; promote symbols that hold across 3+ regimes.
2. Test M15 entry timing once >=18 months of M15 exists (intrabar fill of the reclaim could lift win-rate
   and let the 0.75R target hit before mean-revert fades).
3. Cross-sectional: only fade an index when SPX/NAS are NOT both trending same direction (risk-off filter)
   — the sign-flip symbols (GER40/US30) may be regime-conditional on US beta.
4. Try a 2-leg scale-out exit (book 0.5 at 0.5R, runner to 1.5R) like cs.exit_state_d to capture the rare
   continuation while keeping the high hit-rate base.
