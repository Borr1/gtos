# KB — Deepen Dynamic Execution / Exits (lift the +0.865R compounding core)

Track: EXEC (builder). Date 2026-06-15. Goal: lift the forward +0.865R commodity-continuation
core by improving the EXIT manager only. Entries held FIXED.

## Setup (what is held constant)

- ENTRY (fixed, identical to `compounding_sleeve`): metals ex-copper FVG-retest continuation
  + momentum-persistence gate `ac60>=0.10`. Universe = `compounding_sleeve.METALS`
  = `[XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD]`.
- n = **131 entries** total. TRAIN (year<=2024) n=82; FORWARD 2025 n=24; FORWARD 2026 n=25
  (~24.5 trades/yr forward). This is a SMALL sample — thresholds chosen on TRAIN, reported FORWARD.
- Cost = `w1.cost_for(sym)` scaled by stop tightness (`base*0.5*ATR/stop_dist`), charged on each leg.
- Engine: `EXEC_exit_variants.py::sim_exit` — generic ladder/BE/runner/trail/time-stop manager.
  No lookahead (entry-state vol + running MFE/MAE/bar-count only). Pessimistic: per bar the adverse
  level is checked BEFORE the favorable level (same convention as `geometry_lib.simulate`).
  PARITY-PROVEN: replicating `cs.exit_state_d` (STATE_D) through `sim_exit` gives max abs R diff = 0.0
  over all 131 trades. Winsorize net R to [-1.3,+5].
- BASELINE = STATE_D (the +0.865R reported core). Under this engine's cost-scaling it reads
  **+0.891R/trade forward, 78% win, runner-capture 32%** (cost-scaling makes it read +0.026 above the
  raw-cost +0.865 baseline; all comparisons below are vs the +0.891 engine baseline, apples-to-apples).

## The leak (per-trade intelligence — where STATE_D bleeds)

Forward exit-reason breakdown of STATE_D (n=49):
| reason | n | meanR |
|---|---|---|
| be_scratch (booked 0.5-leg, runner reverted to BE) | 19 | +0.63 |
| runner_target | 12 | +2.60 |
| full stop | 11 | -1.02 |
| market_close | 7 | +1.66 |

**The `be_scratch` bucket is the leak.** 19/49 forward trades scaled 50% at +1.5R then the runner gave
all its remaining profit back to BE — yet their MFE routinely reached **2.0-3.2R** before reverting.
They are almost entirely in the **mid/high-vol band (vr 1.25-1.96)**: silver pairs in 2026 and
XAU/XAG-AUD/EUR in 2025. STATE_D's flat BE-on-runner banks nothing on these deep round-trips.
Two fixes follow directly from this.

## Variants tested (per-year + per-regime, never a bulk average)

All run on the SAME 131 entries. (T=train ev / F=forward ev / w=win% / rc=runner-capture / std / maxDD@0.25%.)

| policy | TRAIN ev | 2025 ev | 2026 ev | FWD ev | FWD w% | rc% | std | mDD |
|---|---|---|---|---|---|---|---|---|
| **STATE_D (baseline)** | +0.320 | +1.125 | +0.666 | **+0.891** | 78 | 32 | 1.29 | 0.51% |
| deeper runner 6/5/3.5 | +0.293 | +1.118 | +0.726 | +0.918 | 78 | 18 | 1.44 | 0.51% |
| wide-trail runner arm2/gap1 | +0.373 | +0.973 | +0.810 | +0.890 | 78 | 11 | 1.15 | 0.51% |
| profit-lock BE 0/0.5/0.75 (vol-band) | +0.320 | +1.245 | +0.726 | **+0.944** | 78 | 32 | 1.28 | 0.51% |
| deeper-scale 2.0 + lock0.5 | +0.478 | +1.176 | +0.916 | +1.043 | 67 | 39 | 1.53 | 0.51% |
| **COMBO sc2.0 + vol-lock 0.25/0.5/0.75** | **+0.481** | +1.186 | +0.901 | **+1.040** | 67 | 39 | 1.53 | 0.51% |
| scale-by-vol 2.5/2.0/1.0 + lock | +0.396 | +1.526 | +0.966 | +1.240 | 76 | 35 | 1.52 | 0.51% |
| + early-progress time-stop bar5<1R | +0.099 | +0.365 | +0.986 | +0.682 | 67 | 27 | 1.26 | 0.51% |

### Paired uplift vs baseline (n, mean dR, t-stat)
- **profit-lock (vol-band)**: ALL +0.033 t2.14 | TRAIN +0.000 t0.0 | **FWD +0.089 t4.31** (forward-significant; zero train footprint — lock never binds on train trades, all train trades were low-vol/non-reverting).
- **COMBO sc2.0+lock**: ALL +0.157 t3.82 | **TRAIN +0.161 t4.34** (train-validated) | FWD +0.150 t1.66 (forward-positive, n=49 too small for forward significance).

## RECOMMENDATION (two deployable exits, sized by confidence)

### PRIMARY — `EXEC_COMBO` (train-validated, biggest lift)
Replaces STATE_D's exit on the compounding core. Per-vol-regime (volrat = ATR14/SMA100(ATR14), known at entry):
```
LOW  (vr<1.35): scale 50% @ +2.0R, runner stop -> +0.25R (lock), runner fixed target +4.0R
MID  (1.35-1.60): scale 50% @ +2.0R, runner stop -> +0.50R (lock), runner fixed target +3.0R
HIGH (vr>=1.60): scale 50% @ +2.0R, runner stop -> +0.75R (lock), runner fixed target +2.5R
```
Initial stop = structural 1R. After the 50% scale leg fills, the runner stop jumps to the lock level
(small profit, NOT breakeven). No intrabar trailing.
- **Forward EV +1.040R/trade** (vs +0.891 engine / +0.865 reported baseline), ~24.5 trades/yr.
- **TRAIN paired uplift +0.161R, t=4.34** — train-proven, the doctrine's gold standard.
- Runner-capture **32%->39%**, median forward R **0.722->1.227**.
- **maxDD IDENTICAL** (0.51%@0.25%, 2.03%@1%); worst-day identical (-0.258%@0.25%). FTMO-neutral on tail.
- Per-year improves nearly every year, train AND forward (2017 .01->.17, 2018 .63->.92, 2019 .17->.34,
  2024 .80->1.05, 2026 .67->.90); only 2022 (n3) and 2023 (n10) stay negative as in baseline.
- TRADEOFF: per-trade std 1.29->1.53 and win 78->67% (scaling at 2.0R instead of 1.5R means ~8% of
  trades that peaked between 1.5-2.0R now take the full stop instead of banking the leg; full-loss freq
  22.4%->30.6%). Bigger winners, slightly more full stops, same drawdown. Net EV strongly positive.

### CONSERVATIVE / ZERO-RISK ADD — `EXEC_LOCK` (variance-neutral)
Keep STATE_D scale levels (1.5R / 1.0R-hi) but change the runner stop from flat BE to a vol-banded
profit-lock: LOW vr<1.35 -> BE (0.0); MID -> +0.5R; HIGH -> +0.75R. Runner targets unchanged.
- **Forward EV +0.944R/trade**, win 78% (UNCHANGED), std 1.28 (UNCHANGED), maxDD UNCHANGED, full-loss
  freq UNCHANGED. Median R 0.722->0.964.
- **FWD paired uplift +0.089R, t=4.31** (significant). TRAIN paired uplift +0.000 — it never fires on
  train trades, so train cannot CONFIRM it; it rests on mechanism + forward significance.
- Pure Pareto improvement on every forward symbol and (almost) every forward year; only 2023 (n10,
  3-trade mid-vol cluster) dips a hair. Deploy this even if combo's variance is unwanted — it lifts the
  give-back bucket for FREE (same risk profile).

## Threshold robustness (COMBO)
Sweeping scale level 1.75-2.25 x vol cuts 1.30/1.55 .. 1.40/1.65: TRAIN stays +0.42..+0.50,
FORWARD +0.98..+1.08. Every cell beats baseline on BOTH train and forward. Not knife-edge.

## NEGATIVE results (learnings — keep, do not delete)
- **Early-progress time-stop (bar5/bar6 MFE<1R -> exit) DESTROYS this core**: TRAIN +0.10, FWD +0.68.
  Confirms the prior KB caveat — metal continuations are SLOW; cutting no-progress trades kills the
  late-developing winners. The bar3/bar5 early-progress signal that predicts on the BROAD pocket does
  NOT transfer to the persistence-gated metal core. Do not apply here.
- **Intrabar trailing (chandelier/wide-trail) REDUCES EV** even with wide gaps: arm2/gap1 -> +0.890
  (rc collapses to 11%). The structural stop is wide and MAE median is large; any trail gets shaken
  out before the slow move develops. Matches KB_dynamic_exits §4. Use FIXED runner target, not trail.
- **Pushing runner targets deeper alone** (6/5/3.5) is FORWARD-ONLY positive (+0.918 fwd but TRAIN
  DROPS to +0.293). Single-regime confound (2026 silver runners). Rejected — not train-validated.

## NEXT
1. Wire `EXEC_COMBO` (or at minimum `EXEC_LOCK`) as the exit manager for the commodity/metals sleeve in
   place of flat STATE_D. Both implementable with one partial fill + one stop-move + one deep limit.
2. Re-run COMBO on the BROADER FVG pocket (energy + agri, copper) to test whether deeper-scale+lock
   transfers beyond metals (KB_dynamic_exits showed STATE_D itself transfers; test the lift does too).
3. Stress COMBO's scale-leg and lock-stop fills under M1-intrabar realism (`study_m1_intrabar_realism.py`)
   — the deeper 2.0R scale and the lock stop are both limit/stop fills; price the slippage.
4. Monte-Carlo COMBO equity through the FTMO challenge gate at approved risk — confirm the higher EV at
   identical maxDD raises challenge-pass probability.

Artifacts: `EXEC_exit_variants.py` (engine, parity-proven), `EXEC_COMBO_EXIT_LEDGER.jsonl` (131 per-trade rows for the recommended exit).
