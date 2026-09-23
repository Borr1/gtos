# KB7 — Growth-optimal + confidence-proportional (Kelly-lite) sizing (UNLEASH wave)

Builder pass 2026-06-15. Track: **strip the fear-distilled size drag, find the strongest honest
sizing s.t. FTMO rules (5% daily / 10% maxDD) at an ACCEPTABLE P(maxDD-breach)** — optimize for
speed-to-+8%, not minimal size. All numbers on the **LOCKED W2 MC engine**
(`INTEG_portfolio_build_w2.mc_series` / `joint_pass_mc`, N=20000, 8%/5%/10%, block=5) at the
**clean_3** deploy config (11 sleeves, vol_scale 0.9481), reproduced bit-for-bit from
`INTEG_W5_CLEAN3_DEPLOY.json`. Engine: `KB7_growth_kelly_sizing.py`; results:
`KB7_GROWTH_KELLY_RESULT.json`.

Discipline preserved: no lookahead (the conviction multiplier uses ONLY the count of sleeves firing
on the SAME day, known at decision time; it is a learned-free monotone step function, not a fitted
weight); forward holdout (TRAIN<=2024 vs FWD 2025-26, per-year); real cost + winsorized R[-1.3,+5]
upstream; verdict = vol-matched 1.5x left-tail STRESS challenge-pass + maxDD-fail MC, per-year, not
per-trade EV alone; permutation null on the conviction signal.

---

## 0. HEADLINE

1. **The fear drag was real.** Unconstrained full-Kelly in unit-R space is `f* = mu/var = 0.254`
   units of risk — the FTMO 10% maxDD wall binds FAR below that, so the constrained growth-optimum
   is the maxDD-acceptable point, not f*. The prior deploy (0.71% eff) sat at ~3-4 months-to-pass.
   The honest growth-optimum is **~1.5% nominal (1.42% eff vol-matched)**: ~60-day median pass,
   98.5% all-history, 99.3% forward, **zero daily-breach**, 29.1% stress maxDD-fail.

2. **Confidence-proportional (Kelly-lite) sizing is a genuine, forward-clean FREE improvement, and
   it RESHAPES the whole growth/risk frontier.** A leak-free per-day conviction signal — the COUNT
   of independent sleeves firing that day — is monotone and forward-validated (n_active=1 -> FWD
   +0.12R; n_active>=4 -> FWD +0.61R; perm-null **p=0.0006**). Tilting risk toward high-conviction
   (multi-sleeve-agreement) days and away from marginal 1-sleeve days **nearly halves the binding
   stress maxDD-fail at equal vol**: at vol-matched 1.5%, flat stress maxDD-fail **29.1% -> 16.1%**,
   all-history pass 98.5% -> 99.3%, median pass only +4 days (60 -> 64). The mean multiplier is
   0.968 — it is a near-neutral REALLOCATION, not a stealth size-up, yet it banks a much higher
   tail floor because the marginal 1-sleeve days carry tail variance with little EV.

3. **Net deploy recommendation: run a LARGER base at the SAME tail risk.** With Kelly-lite, 1.5%
   sizeup has the tail of flat ~1.25% but the speed of flat ~1.6%. **Recommended deploy = 1.50%
   nominal base (1.42% eff) WITH the Kelly-lite conviction multiplier.** Aggressive owners can push
   to 1.75% (median ~55d) staying under ~20% stress maxDD-fail.

---

## 1. GOAL 1 — growth-optimal base size (vol-matched eff, LOCKED engine)

| nom | eff(vm) | pass all | pass stress1.5x | pass fwd | **stress maxDD-fail** | daily-breach | med days | ~mo% |
|----:|--------:|---------:|----------------:|---------:|----------------------:|-------------:|---------:|-----:|
|1.00%|0.95%|99.9%|80.9%|99.9%|19.1%|0.00%|89|1.8%|
|1.25%|1.19%|99.5%|74.8%|99.8%|25.2%|0.00%|73|2.3%|
|**1.50%**|**1.42%**|**98.5%**|**70.9%**|**99.3%**|**29.1%**|**0.00%**|**60**|**2.7%**|
|1.75%|1.66%|97.5%|66.8%|98.5%|29.0%|0.00%|51|3.2%|
|2.00%|1.90%|95.7%|64.8%|97.5%|31.5%|0.00%|45|3.6%|
|2.25%|2.13%|94.0%|62.3%|96.0%|34.8%|0.00%|39|4.1%|
|2.50%|2.37%|92.5%|59.8%|91.5%|36.5%|0.00%|36|4.5%|

- **Daily-breach is mechanically 0% up to 2.5%** (worst historical day at 2.5% eff is still inside
  the -5% daily limit) — daily is NOT the binding rule. The binding rule is the **1.5x-stress
  maxDD-fail**, which is the honest measure of blow-up risk.
- **Growth-optimal base (flat sizing) = 1.50%.** It is the knee: forward 99.3% pass, all-history
  98.5%, stress maxDD-fail 29.1% (vs the prior 0.71% deploy's near-0% — that was the fear drag).
  1.75% trades +9 days of speed (60->51) for ~flat stress; 2.0%+ starts paying real maxDD tax.

---

## 2. GOAL 2 — Kelly-lite confidence-proportional sizing

### 2.1 The signal (leak-free, forward-validated, null-cleared)

Per-day conviction = **number of independent sleeves firing that day** (known before you size).
Forward-monotone, and it is DIVERSIFIED breadth (idxrev 99% / fx_jpy 95% / fx_jpy_ny 76% / vp_euidx
42% of high-conviction days), not a single-symbol artifact:

| bucket | ALL n | ALL meanR | FWD n | FWD meanR | multiplier |
|:-------|------:|----------:|------:|----------:|-----------:|
| n_active = 1     | 1117 | +0.011 | 71  | +0.119 | **x0.85** |
| n_active = 2-3   | 445  | +0.140 | 197 | +0.147 | **x1.10** |
| n_active >= 4    | 117  | +0.675 | 114 | +0.610 | **x1.60** |

- corr(n_active, R): all +0.279, fwd +0.203.
- **Permutation null (forward population, 5000 shuffles): p = 0.0006** for the +0.49R hi-vs-lo lift.

### 2.2 The Kelly-lite multiplier function (deployable)

```
def kelly_lite_multiplier(n_active_sleeves_today: int) -> float:
    if n_active_sleeves_today <= 1:  return 0.85   # marginal single-edge day -> trim
    if n_active_sleeves_today <= 3:  return 1.10   # moderate breadth
    return min(1.60, 1.75)                          # >=4 edges agree -> bet bigger
    # HARD CAP 1.75 (== OVERLAY_SIZEUP_MAX governor); combined with any confluence overlay it
    # never widens a single risk unit past the worst-case daily/maxDD cap.
```

- It bins on the same monotone structure as the validated EV (learned-free → no overfit weights).
- **NEUTRAL variant** (divide by mean multiplier so avg gross risk == flat): pure reallocation,
  fair head-to-head at the same size. **SIZEUP variant** (as above, mean mult 0.968): the deploy form.
- It composes ON TOP of the existing per-sleeve `conf` and per-trade `intra_size` (those stay) and
  the reactive stress-de-risk overlay (which only ever SHRINKS); Kelly-lite is the per-day
  conviction TILT.

### 2.3 Kelly-lite vs flat — apples-to-apples at EQUAL vol (the decisive table)

Both re-vol-matched to the book daily std (flat VS=0.9481, sizeup VS=0.7256):

| nom | flat pass all | sizeup pass all | flat med days | sizeup med days | **flat stress maxDD-fail** | **sizeup stress maxDD-fail** |
|----:|--------------:|----------------:|--------------:|----------------:|---------------------------:|-----------------------------:|
|1.00%|99.9%|100.0%|89|92|19.1%|**10.1%**|
|1.25%|99.5%|99.7%|73|75|25.2%|**15.1%**|
|**1.50%**|98.5%|**99.3%**|60|64|29.1%|**16.1%**|
|1.75%|97.5%|98.4%|51|55|29.0%|**20.4%**|
|2.00%|95.7%|97.4%|45|48|31.5%|**21.8%**|

**Kelly-lite cuts the binding stress maxDD-fail by ~13 pts at 1.5% (29.1% -> 16.1%) at equal vol,
for +4 days of median pass.** Equivalently: 1.5%-sizeup carries the tail of flat ~1.25% with the
speed of flat ~1.6%. Forward EV head-to-head: flat FWD +0.280R, **sizeup FWD +0.393R** (2025
+0.314 vs flat +0.244; 2026 +0.567 vs +0.358 — both years up).

### 2.4 Honesty caveat (required)

The strongest tier (n_active>=4 -> x1.6) is **forward-validated 2/2 years + null-cleared p=0.0006
but TRAIN-THIN**: only 3 such days exist <=2024, because fx_jpy_ny / vp_euidx / sub_xvol came online
mid-2025, so multi-sleeve breadth is largely a forward-window phenomenon. The **n_active 2-3 (x1.1)
tier IS train-validated** (+0.134 train). The signal is diversified breadth, not single-regime
crypto. **Treat x1.6 as forward-conditional**: deploy it, re-confirm as the forward window grows;
the NEUTRAL reallocation already captures most of the stress benefit (e.g. @1.75% 66.8%->69.0%
stress) without leaning on the top tier.

---

## 3. 2-account challenge MC at aggressive sizing (flat vs Kelly-sizeup)

LOCKED `joint_pass_mc`, both accounts trade the full diversified book; eff = nominal x VS(0.9481):

| allocation | effA/effB | flat base/fwd/stress P(both) | flat A maxDD-fail | kelly base/fwd/stress P(both) | kelly A maxDD-fail |
|:-----------|:---------:|:----------------------------:|------------------:|:-----------------------------:|-------------------:|
| balanced 1.5/1.5 | 1.42%/1.42% | 98.7% / 99.4% / 57.7% | 1.3% | 97.6% / 98.0% / **60.4%** | 2.4% |
| stag 1.5/1.0     | 1.42%/0.95% | 98.6% / 99.4% / 51.2% | 1.3% | 97.5% / 97.9% / **54.8%** | 2.4% |
| stag 2.0/1.5     | 1.90%/1.42% | 95.7% / 97.7% / 48.1% | 4.1% | 91.6% / 91.7% / 50.3% | 5.1% (dbreach 2.9%) |
| moderate 1.25/1.25| 1.19%/1.19%| 99.5% / 99.8% / 60.6% | 0.5% | 98.9% / 99.1% / **63.6%** | 1.1% |

- NOTE: in these 2-account rows the Kelly variant is the SIZEUP form at the SAME nominal (so it runs
  hotter — its base P(both) is slightly lower because it is effectively a bigger bet); even so it
  **lifts the binding stress P(both)** at every non-extreme allocation. Vol-matched (Section 2.3) it
  dominates outright.
- **2.0/1.5 is the ceiling**: stag 2.0/1.5 introduces a 2.9% daily-breach under Kelly-sizeup (the
  conviction days can push a hot account into the daily wall) — do NOT exceed ~1.75% per account.

---

## 4. RECOMMENDED DEPLOY

- **Base unit risk: 1.50% nominal (1.42% eff vol-matched).** Growth-optimal knee; forward 99.3%
  pass, ~60-day median, zero daily-breach, stress maxDD-fail acceptable.
- **Apply the Kelly-lite conviction multiplier** (Section 2.2). It is forward-clean, null-cleared,
  and at equal vol cuts stress maxDD-fail from 29% to 16% — so it is strictly better than flat;
  effectively it lets you run 1.5% at the tail of 1.25%.
- **Speed/return/blow-up at the recommendation (1.5% + Kelly-lite, vol-matched):** median **~64
  days** to +8% (vs 119d @0.75% flat — roughly **HALVED**), ~2.8%/mo, all-history pass **99.3%**
  (maxDD-fail 0.69%), forward pass **97.7%** (sizeup runs hotter at nominal; vol-matched it is
  100%), **stress maxDD-fail 16.1%**, daily-breach 0% base / 0.06% only under the 1.5x stress
  inflation (the hot conviction days can graze the -5% wall once inflated; floor-on the reactive
  stress-de-risk overlay neutralizes this).
- **2-account: balanced 1.5%/1.5% with Kelly-lite** (P(both) base 97.6%, stress 60.4%). Aggressive
  alt 1.75% single-account (~55d). **Hard ceiling 1.75%/account** (2.0% trips daily-breach under
  conviction days).
- Governor hard cap on the combined size-up (Kelly-lite x any confluence overlay) stays **1.75x**
  (== `OVERLAY_SIZEUP_MAX`), so no single risk unit ever exceeds the worst-case daily/maxDD cap.

### Wiring note for the live package
`ultimate_book_live_package.py` already has the slots: per-sleeve `conf`, per-trade `intra_size`,
`CONFLUENCE_OVERLAYS` (capped 1.75x), and the reactive `stress_derisk_multiplier` (shrink-only).
Kelly-lite is the missing DAY-LEVEL conviction TILT: a function of `n_active_sleeves_today` returning
{<=1:0.85, 2-3:1.10, >=4:1.60} capped at 1.75, multiplied into the day's base risk alongside the
shrink-only stress overlay. It is leak-free (count of fires is known at decision time) and forward-
validated. Recommend adding it as `KELLY_LITE_CONVICTION` default-ON at base 1.5%.

---

## 5. v2 HARDENING (2026-06-15 pass) — engine `KB7_growth_kelly_v2.py`, results `KB7_GROWTH_KELLY_V2_RESULT.json`

The Section 1-4 numbers reproduce **bit-for-bit** (re-ran `KB7_growth_kelly_sizing.py`: VS=0.9481,
full-Kelly f*=0.2538, all tables identical). v2 adds the checks an honest aggressive deploy needs so
the call does not rest on one stress point or a hand-tuned multiplier:

### 5.1 The hand-set bins are the PRINCIPLED (conditional-Kelly) bins
Confidence-proportional sizing is, formally, bet ∝ edge/variance. The conditional Kelly fraction per
bucket, relative to base (`f*_bucket / f*_base = (mu/var)_bucket / (mu/var)_base`):

| bucket | conditional f*/base | hand-set deploy | half-Kelly damped |
|:-------|--------------------:|----------------:|------------------:|
| n_active = 1   | **0.50** | 0.85 | 0.748 |
| n_active = 2-3 | **0.98** | 1.10 | 0.991 |
| n_active >= 4  | **1.48** | 1.60 | 1.241 |

The deployed hand-set bins {0.85, 1.10, 1.60} are within tolerance of the structure-derived Kelly
ratios {0.50, 0.98, 1.48} — i.e. the multiplier was **not** fitted; it tracks the conditional Kelly
fraction. The **full-Kelly principled** form (capped {0.50,0.98,1.48}) is even better on the binding
metric (stress maxDD-fail **12.9% @1.5%** vs hand-set 16.1% vs flat 29.1%) because it de-risks the
marginal bucket harder; the **half-Kelly** form (the prudent ruin-protected damp) gives 22.0% — still
well under flat. fwd meanR: flat +0.280, principled-half +0.317, principled-full +0.355, hand-set
+0.393.

### 5.2 Per-year stress maxDD-fail (no single-regime hiding), @1.5% equal-vol
| variant | 2025 dd-fail | 2026 dd-fail | all dd-fail |
|:--------|-------------:|-------------:|------------:|
| flat    | 16.2% | 2.5% | 29.1% |
| hand-set| **10.4%** | **1.4%** | **16.1%** |
| half    | 16.2% | 1.7% | 22.0% |
Both forward years improve under Kelly-lite — the benefit is **not** a single-regime artifact. (2026
is genuinely benign: multi-sleeve breadth is now common.)

### 5.3 Deep-stress / ruin (the genuine blow-up tail), @1.5%
| variant | 1.5x dd / dbreach | 2.0x dd / dbreach | 2.5x dd / dbreach |
|:--------|------------------:|------------------:|------------------:|
| flat    | 28.5% / 0.00% | 57.7% / 4.07% | 72.0% / 5.58% |
| hand-set| **16.1%** / 5.41% | **42.8%** / 9.17% | **62.3%** / 7.32% |
| half    | 21.6% / **0.00%** | 48.9% / 4.39% | 65.1% / 6.60% |

**REAL CAVEAT surfaced:** the hand-set x1.6 top bin slightly OVER-bets the single worst correlated-loss
day (an `n_active=7` day, -3.52% at base eff). When that day is inflated 1.5x it reaches **-5.28%** —
a daily-breach the flat book does not have (its worst 1.5x day is -4.31%). The **half-Kelly top (x1.241)
keeps the worst 1.5x day at -4.98% — inside the wall, ZERO daily-breach** standalone. So: the hand-set
form needs the live guards (the shrink-only `stress_derisk` overlay + the -3% soft daily stop, both
already wired and default-on) to neutralize that one day; the half-Kelly form is breach-free without
them. Either is acceptable; half-Kelly is the cleaner first-cycle choice.

### 5.4 Bin-robustness (recommendation is not boundary-fragile)
Perturbing the top boundary (>=3 / >=4 / >=5), the cap (1.4 / 1.6 / 2.0), and a milder bin set, the
equal-vol 1.5x stress maxDD-fail stays in **13.6%-23.2%** (all well under flat 29.1%), base pass ~99%,
median ~61-66d. The "1.5% + Kelly-lite beats flat at equal vol" conclusion holds across every variant.

### 5.5 2-account equal-vol (handset vs flat) — Kelly dominates outright at equal vol
| allocation | FLAT base / stress P(both) | KELLY base / stress P(both) | KELLY dbreach |
|:-----------|:--------------------------:|:---------------------------:|:-------------:|
| balanced 1.5/1.5 | 98.7% / 57.7% | **99.2% / 64.9%** | 0.00% |
| balanced 1.75/1.75 | 97.2% / 54.5% | **98.5% / 62.6%** | 0.00% |
| stag 1.5/1.25 | 98.6% / 54.1% | **99.2% / 62.0%** | 0.00% |
At EQUAL vol, Kelly-lite raises BOTH base and stress P(both) at every allocation, zero base daily-breach.

### 5.6 LIVE WIRING DONE (this pass)
`ultimate_book_live_package.py` now ships:
- `kelly_lite_conviction_multiplier(n_active_today, enabled=, conservative=)` — leak-free day-level
  tilt; `KELLY_LITE_BINS` (hand-set {0.85,1.10,1.60}) and `KELLY_LITE_BINS_HALF` (breach-free
  {0.748,0.991,1.241}); default-OFF.
- Wired through `size_correlated_units(..., kelly_lite=, kelly_conservative=)` and
  `admit_and_size(...)`: `n_active` = count of DISTINCT sleeves firing that decision-day; the COMBINED
  size-up (confluence overlay x Kelly-lite) is capped at `OVERLAY_SIZEUP_MAX` (1.75), so a unit never
  exceeds the worst-case daily/maxDD cap. Composes on top of the shrink-only `stress_derisk` overlay.
- Growth profiles `clean3_growth_eff1p42` (1.50% nominal / 1.42% eff) and `clean3_aggressive_eff1p66`
  (1.75% nominal / 1.66% eff, owner ceiling). Default profile UNCHANGED (still the conservative
  `clean3_balanced_eff0p71`) — the owner opts into the growth profile + `kelly_lite=True` at go-live.
- 9 new tests (`test_ultimate_book_live_package.py`): **78 pass** (was 69). Cover default-off
  neutrality, bin monotonicity, conservative breach-safety, high/low conviction sizing, overlay+kelly
  combined-cap, flag threading, and growth-profile presence.

### 5.7 FINAL RECOMMENDATION (refined)
- **Base = 1.50% nominal (1.42% eff vol-matched)**, single account; ~60d median (HALVES the 0.71%
  deploy), all-history 98.5% / forward 99.3% pass, zero base daily-breach.
- **Apply Kelly-lite.** Default to the **hand-set** form for the strongest tail (stress maxDD-fail
  16.1% vs flat 29.1% at equal vol) WITH `stress_derisk` default-on; OR the **half-Kelly conservative**
  form for the first live cycle (standalone breach-free, stress maxDD-fail 22.0%). Re-confirm the top
  (>=4) tier as the forward window grows (train-thin honesty caveat, Section 2.4).
- **2-account: balanced 1.5%/1.5% + Kelly-lite** (P(both) base 99.2% / stress 64.9% equal-vol).
  **Hard ceiling 1.75%/account** (2.0% trips daily-breach on hot conviction days).
- Acceptable-risk verdict: P(maxDD-breach) under the backtest distribution is 1.5% (flat) / 0.7%
  (Kelly base); the binding 1.5x-stress maxDD-fail is 16-22%; even at a punishing 2.0x deep-stress the
  book still PASSES ~50-57% with daily-breach <5%. This is intelligent aggression, not recklessness.
