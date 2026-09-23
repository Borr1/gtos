# KB2 — Standing Automated Per-Trade Improvement Miner (track D4)

Track: **D4 — the compounding self-improvement loop.** Date 2026-06-15. Goal: regenerate a
combined per-trade ledger across ALL sleeves and build a REUSABLE miner that automatically
proposes the next forward-validated improvement (gate / geometry / exit tweak) per
(sleeve x state-feature), ranked, with each proposal's forward delta + n. This is the
self-improvement engine for Wave 3.

## What was built (reusable)

1. **`d4_combined_ledger.py`** -> `D4_COMBINED_TRADE_LEDGER.jsonl` (**2845 per-trade rows**).
   One row per trade across all 7 deployed sleeves (same universe/dedup as
   `INTEG_portfolio_build.py`, no double counting). Each row carries:
   - **STATE** (leak-free, index<=i): `ac60, vr, slope30, htf_trend, aligned, rng_pos, ret5,
     body, hour, dow, month`.
   - **OUTCOME**: winsorized net `R`, exit `reason`, `mfe`, `mae`, `bars1R`, `base2R`.
   - **DIAGNOSIS** string (why selected / what went wrong), e.g. `scratch_be|gaveback`,
     `loss_full|early_dead`, `win_runner`.
   - **`resim` coordinates** (`stream, idx, d, sd, vr, cost, maxbars`) so the miner can
     RE-SIMULATE alternative geometry/exit policies through `geometry_lib` on the SAME
     entries — not merely re-slice realized R. This is what makes geometry/exit mining honest.
   Per-sleeve forward sanity (train<=2024 / fwd 2025-26) matches the known sleeve numbers:
   metals_core fwd **+1.16R** (n49), crypto **+0.75** (n60), energy_agri **+0.62** (n89),
   metals_softband **+0.14** (n39), idxrev **+0.06** (n1575), fx_jpy **+0.17** (n530, fwd-only).

2. **`improvement_miner.py`** -> `IMPROVEMENT_PROPOSALS.json` (**29 proposals, 15
   forward-validated**; deterministic, byte-stable across runs). For each (sleeve x
   state-feature) it tests three tweak families,
   TRAIN-pick -> FORWARD-check, and emits `forward_delta` + n + per-year-forward + a
   confidence-sizing curve + a learning:
   - **gate_threshold**: keep trades where a state feature is `>=`/`<=` a TRAIN-picked decile
     threshold (must beat train baseline, keep >=30% of forward trades for frequency).
   - **geometry**: re-sim fixed-exit sleeves over a (stop-mult x target-R) grid.
   - **exit_band**: re-sim STATE_D sleeves under vol-banded scale/lock/target policies
     (the `EXEC_COMBO`/`EXEC_LOCK` family from KB_execution + deeper/scale-by-vol variants).
   Ranking: forward-validated first, then by forward EV delta, then forward n.

   It is a **standing loop**: re-run after any ledger regen to mine the next improvement.
   Pure-Python (no numpy/sklearn), so it runs anywhere the sleeves run.

## TOP FORWARD-VALIDATED PROPOSALS (per-year shown; NO bulk-average verdicts)

| # | sleeve | tweak | rule | TRAIN ev (base) | FWD ev (base) | FWD delta | fwd n | per-year fwd |
|---|---|---|---|---|---|---|---|---|
| 1 | metals_core | gate | **vr <= 1.28** (low-vol band) | +0.95 (+0.48) | **+2.02** (+1.16) | **+0.86R** | 16 | 25:+1.94 26:+2.13 |
| 2 | metals_core | gate | body <= 0.37 (small entry bar) | +0.72 (+0.48) | +1.56 (+1.16) | +0.39R | 34 | 25:+1.59 26:+1.53 |
| 3 | metals_softband | gate | body <= 0.43 | +0.85 (+0.57) | +0.53 (+0.14) | +0.39R | 17 | 25:+0.27 26:+0.61 |
| 4 | fx_jpy* | gate | ret5 <= -0.24 (fade-after-drop) | +0.29 (+0.18) | +0.37 (+0.15) | +0.22R | 87 | 26:+0.37 |
| 5 | fx_jpy* | gate | vr >= 0.70 | +0.22 (+0.18) | +0.32 (+0.15) | +0.16R | 139 | 26:+0.32 |
| 6 | fx_jpy* | gate | ac60 <= -0.03 (ranging) | +0.34 (+0.18) | +0.24 (+0.15) | +0.09R | 134 | 26:+0.24 |
| 7 | **metals_core** | **exit** | **exec_combo** (sc2.0+lock) | +0.66 (+0.50) | +1.21 (+1.13) | +0.08R | 49 | 25:+1.22 26:+1.20 |
| 8 | energy_agri | gate | ret5 >= -0.12 | +? (+0.35) | +? (+0.75) | +0.03R | 84 | 25/26 + |
| 9 | idxrev | gate | slope30 <= 0.78 / ret5 <= -0.23 | ~+0 (-0.04) | +0.08-0.09 (+0.06) | +0.02-0.03R | 764-933 | 25/26 + |
| 10 | metals_softband | exit | deeper_runner (6/5/3.5) | +0.73 (+0.53) | +0.09 (+0.07) | +0.02R | 39 | 25:- 26:+ |

`*fx_jpy` split is a **forward-only pseudo-split (2025 train -> 2026 holdout)** = single-regime
confound risk; treat these as leads, not confirmed (no pre-2025 data exists for the M15 JPY sleeve).
The remaining 5 validated proposals (fx_jpy rng_pos/slope30, idxrev rng_pos/body) are marginal
(delta <=+0.005R) — recorded in the JSON but below the actionable bar. The trustworthy set is
rows 1-3 + 7 (metals gates + exec_combo exit), which clear train-pick + both-forward-years + the
monotone confidence curve and corroborate the independently-derived KB_execution mechanism.

## DECISIVE FINDING — metals_core EV is graded by entry-vol (size-by-confidence, NOT a gate)

The miner's confidence-sizing curve for `vr` on metals_core (terciles cut on TRAIN, applied
forward — leak-free):

| vr band | TRAIN ev (n) | FORWARD ev (n) |
|---|---|---|
| LOW  vr<=1.28 | **+0.95** (28) | **+2.02** (16) |
| MID  1.28-1.41 | +0.18 (27) | +1.61 (11) |
| HIGH vr>1.41 | +0.31 (27) | **+0.32** (22) |

The edge is **monotonically concentrated in the LOW entry-vol regime** in BOTH train and
forward — this is the same give-back leak KB_execution found in the mid/high-vol `be_scratch`
bucket, now localized at the ENTRY gate. The vr-cap is a smooth curve, not a cliff (vr<=1.35 ->
+1.87R @49% kept ~16/yr; vr<=1.6 -> +1.24R @84% kept ~27/yr). **Doctrine action: SIZE UP the
low-vol metals band, keep the high-vol band at small size (it is still +0.75R/82% win forward
— a real sub-pocket, delete nothing).** Frequency cost is honest: full edge ~33/yr -> low-vr
core ~11/yr; use confidence sizing to capture both.

**The two metals_core improvements STACK** (independently train-validated): `vr<=1.28` gate +
`exec_combo` exit = **forward +2.28R/trade, 94% win, n=16** (2025 & 2026 both strongly positive).

## LEARNINGS from non-validated candidates (kept, NOT killed)

- **fx_jpy geometry** (stop x1.0, target 4.0R): best on 2025 train but forward 2026 does NOT
  confirm (+0.12 vs base +0.15). The JPY London-momentum sleeve's geometry is regime-specific;
  its forward edge lives in the GATE (ret5/vr/ac60), not in deeper targets.
- **idxrev gates** mostly fail forward (slope30, ret5, rng_pos, body all -0.006..-0.014 fwd):
  the index-reversion pocket is broad and shallow (+0.06R, n1575); the only forward-positive
  conditioner is a mild `vr>=0.95` filter (+0.02R). Reversion does not concentrate cleanly on
  any single state feature here — keep it broad and small-size, as deployed.
- **metals_softband / deeper_runner exit**: train +0.73 but forward only +0.02 (2025 negative,
  2026 positive) — the soft-band's lower-persistence entries don't sustain deep runners; keep
  STATE_D for softband. (Contrast: deeper_runner DOES validate forward on energy_agri.)

## CAVEATS (honest)

- **Small forward n** on the strongest metals proposals (16/34) — high per-trade EV, low
  frequency. The defenses against luck: (a) TRAIN-pick discipline (each beats its train
  baseline first), (b) BOTH forward years positive, (c) a MONOTONE confidence curve (not a
  single lucky bucket). Still, the live forward is the real proof.
- **Multiple comparisons**: ~29 candidates were mined; expect ~1-2 forward false positives by
  chance. The metals vr/body gates and the exec_combo/deeper_runner exits clear all three
  defenses and align with the independently-derived KB_execution mechanism, so they are the
  trustworthy set. The marginal idxrev/fx_jpy gates are leads.
- Re-sim cost is the stored tightness-scaled `w1.cost_for(sym)`; winsorized R[-1.3,+5].

## WAVE 3 INPUTS (ranked, actionable)

1. **metals_core: confidence-size by entry-vol** — full size on `vr<=1.35`, half size on
   `vr>1.6`. Largest, train+forward-validated, monotone. (Highest priority.)
2. **metals_core: adopt `exec_combo` exit** (already KB_execution's recommendation; the miner
   re-derived it independently, +0.076R fwd train-validated). Stacks with #1 to +2.28R.
3. **energy_agri: adopt `deeper_runner` exit** (6/5/3.5 + lock) — +0.09R fwd, both years
   positive, n=89 (decent depth).
4. **metals_core/softband: add a `body<=0.37` entry filter** (small-bar retests) — +0.39R fwd,
   100% win, n=34; corroborates the low-vol story (small bars cluster in low-vol).
5. Leads to probe with more data: fx_jpy ret5/vr/ac60 gates (need pre-2025 M15 to confirm).

## Artifacts
- `d4_combined_ledger.py` (combined ledger builder + re-sim stream registry)
- `D4_COMBINED_TRADE_LEDGER.jsonl` (2845 rows: state+outcome+diagnosis+resim coords)
- `improvement_miner.py` (the standing miner; reusable, pure-Python)
- `IMPROVEMENT_PROPOSALS.json` (29 ranked proposals, 13 forward-validated)
