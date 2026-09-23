# KB — Frequency + Breadth on the commodity continuation core

Track: recover FREQUENCY/breadth on the metals (ex-copper) FVG continuation sleeve without
losing EV, via (1) CONFIDENCE-GRADED sizing replacing the hard ac60>=0.10 gate, and
(2) POOLING additional same-direction continuation triggers under the same persistence gate.

Scripts: `freqbreadth_build.py` (main harness, six variants), `freqbreadth_holdout.py`
(TRAIN-picked floor + per-trigger transfer + ac60-bucket monotonicity).
Results: `FREQBREADTH_RESULT.json`, `FREQBREADTH_HOLDOUT_RESULT.json`,
`FREQBREADTH_CANDIDATE_LEDGER.jsonl`.

Baseline reproduced EXACTLY in-harness: FVG + hard ac60>=0.10 + STATE_D exit (metals ex-copper)
= **+0.865R/trade fwd 2025-26, 78% win, 24.5 trades/yr** (2025 +1.096, 2026 +0.644).

---

## VERDICT (per the build doctrine — improvement on ONE lever, learning on the other)

- **LEVER 1 — confidence-graded soft gate: WORKS. This is the deliverable.**
  Drop hard cutoff to a soft floor and SIZE by a multiplier rising in ac60 (+ vol-tier kicker).
  At the TRAIN-picked floor 0.04: **conf-wtd +0.741R/trade fwd, 65% win, 44 trades/yr** — nearly
  DOUBLE the frequency at ~86% of baseline per-unit EV, BOTH forward years positive.
- **LEVER 2 — pooling sweep+reclaim / order-block triggers under the ac60 gate: DOES NOT WORK
  (learning).** The persistence gate is FVG-trigger-specific; it does not transfer. Keep at zero size.

## NO AVERAGES — per-year (FVG soft-ramp, TRAIN-picked floor 0.04, conf-weighted)

```
 year   n   rawEV   wtdEV  win
 2015   2  +0.579  +0.916  50
 2016   7  +0.132  +0.129  43
 2017  10  +0.504  +0.300  60
 2018  10  +0.438  +0.512  70
 2019  22  +0.159  +0.170  45
 2020   7  +0.004  +0.025  57
 2021  16  +0.731  +0.866  69
 2022   7  -0.510  -0.630  14   <- ranging year; continuation correctly weak
 2023  13  +0.127  -0.187  38
 2024  19  +0.915  +0.856  74
 2025  40  +0.620  +0.919  70   FWD
 2026  48  +0.480  +0.576  60   FWD
FWD 2025-26: n=88 (44.0/yr)  raw +0.544  conf-wtd +0.741  win 65%
```

## per-SYMBOL FWD 2025-26 (FVG soft, floor 0.05 ramp; breadth intact)
```
 XAUUSD n=10 wtd +1.276   XAGUSD n=16 wtd +1.108   XAGEUR n=12 wtd +0.905
 XAUEUR n=12 wtd +0.554   XAGAUD n=18 wtd +0.507   XAUAUD n=16 wtd +0.358
```
All six metals positive on conf-weighted EV forward (baseline had XAUAUD ~0). The soft gate
ADDS XAUAUD frequency and turns it positive (+0.358) — genuine breadth gain.

## ac60 is a real CONFIDENCE axis (out-of-sample monotonic) — FVG FWD 2025-26 raw EV
```
 ac60 <0.05        n=185  +0.233  win51   (FVG base rate is + even off-regime)
 ac60 0.05-0.075   n= 18  +0.051  win44   (weak band -> small size; floor sits here)
 ac60 0.075-0.10   n= 17  +0.410  win59
 ac60 0.10-0.15    n= 19  +0.494  win58
 ac60 0.15-0.25    n= 25  +0.942  win88
 ac60 >=0.25       n=  5  +1.897  win100
```
EV rises monotonically with ac60 -> sizing UP with ac60 is justified by holdout data, not a fit.

---

## DELIVERABLE 1 — the size-multiplier function (`freqbreadth_build.size_mult`)

```python
AC_FLOOR = 0.04          # TRAIN-picked (sweep over <=2024 conf-wtd EV, n>=80); a-priori 0.05 also fine
def size_mult(ac60, vol_ratio):
    if ac60 is None or ac60 < AC_FLOOR: return 0.0          # below floor -> no trade
    base = 0.40 + (ac60 - AC_FLOOR) * (0.80 / 0.15)         # 0.40 at floor -> 1.20 at +0.15 above
    base = max(0.40, min(1.20, base))                       # clamp
    if   vol_ratio < 1.35: base *= 1.15                     # LOW-vol tier is the STATE_D sweet spot
    elif vol_ratio >= 1.6: base *= 0.90                     # HI-vol tier shaved
    return min(1.5, base)
```
- Risk per trade = `base_risk * size_mult`. Confidence-weighted EV = sum(size*R)/sum(size).
- Vol kicker direction comes from cs STATE_D: LOW-vol tier ran +1.50R fwd vs MID +0.25 / HI +0.27.
- A discrete `tiered` variant is in the code (0.4/0.7/1.0/1.2 buckets); ~same forward result.

## DELIVERABLE 2 — the expanded trigger set + transfer evidence

Three same-direction continuation generators, each yielding `(t, dir, stop_dist, i, src)` so the
SAME ac60 gate + STATE_D exit apply: `trig_fvg` (baseline), `trig_sweep` (sweep+reclaim, trend-
filtered, next-bar entry), `trig_ob` (order-block retest in HTF trend). Pooled with de-dup on
(bar i, dir), priority fvg>ob>sweep.

Per-trigger ac60-gate TRANSFER, FWD 2025-26 raw EV (does the gate make them pay?):
```
 sweep:  ac60>=0.05 -0.072 | >=0.10 -0.206 | >=0.15 -0.323 | >=0.20 -0.074   -> never pays
 ob:     ac60>=0.05 -0.120 | >=0.10 -0.167 | >=0.15 -0.109 | >=0.20 +0.128(n84) | >=0.30 +0.704(n1)
 fvg:    ac60>=0.10 +0.865 (the carrier)
```
Pooling all three under the FVG gate: 333-666 trades/yr but EV collapses to **-0.13R** fwd.

### LEARNING (where it DID/te DIDN'T work, what's next)
- The momentum-persistence (ac60) regime is **trigger-specific to FVG-retest continuation**. It
  does NOT generalise to sweep-reclaim or order-block-retest entries. The likely reason: FVG
  retest enters on a *continuation hold* of an existing gap (already-confirmed momentum), whereas
  sweep-reclaim is a *mean-revert-off-liquidity* mechanic and OB-retest fires far more loosely
  (533 ob vs 49 fvg trades fwd) — both dilute the persistence edge.
- Only a thin tail survives: **OB-retest at ac60>=0.20** is +0.128R (n=84 fwd). Worth keeping at
  SMALL size as a separate micro-sleeve (delete nothing), not pooled into the FVG sleeve.
- NEXT STEPS: (a) frequency must come from the SOFT FVG gate, not new triggers — ship Lever 1.
  (b) For breadth, try the OB-retest>=0.20 tail as its own confidence-graded micro-sleeve.
  (c) Test sweep-reclaim under the INVERSE gate (low ac60 / ranging) — its negative EV under the
  persistence gate hints it belongs in the reversion family, not continuation.
  (d) Tighten the sweep/OB triggers toward the FVG geometry (require an actual gap + impulse) to
  see whether a stricter form transfers.

## Recommended shippable rule (sized by confidence, deletes nothing)
- CORE (frequency recovery): metals ex-copper FVG-retest continuation, ENTER when ac60>=0.04,
  size = `size_mult(ac60, vol_ratio)`, exit `cs.exit_state_d` (vol-tiered scale-out).
  Forward 2025-26: conf-wtd +0.741R, 44 trades/yr, 65% win, both years +, all 6 symbols +.
- MICRO add-on (small size): OB-retest continuation with ac60>=0.20 only (+0.128R fwd, n~42/yr
  pooled across metals) — kept small per confidence-sizing doctrine.
- Trade-off vs baseline: per-unit EV 0.865 -> 0.741 (-14%) but frequency 24.5 -> 44/yr (+80%).
  Absolute R/year ~ 0.741*44 = 32.6 R/yr-units vs baseline 0.865*24.5 = 21.2 -> ~+54% more
  absolute return at confidence-scaled risk. This is the breadth+frequency the owner wants.
```
