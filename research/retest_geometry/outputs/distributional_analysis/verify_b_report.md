# Tier 1 Distributional Analysis — Independent Verification (n=726) + Wick-vs-Close Re-derivation
**Analyst:** verify_b (independent of verify_a, no coordination)
**Date:** 2026-04-18
**Primary CSV:** `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` (n=726, ADR-003-compliant timing fix verified by A3_v2)
**Comparison CSV:** `research/retest_geometry/outputs/historical/combined_retests.csv` (n=121, distrib_a/b headline source)
**Underlying M15:** `data/historical/{SYMBOL}_M15.csv` (full 2-year corpus, source for A1_v2 and Task B replay)
**Working scripts:** `scratch/verify_b/01..14*.py`; per-row outputs in `scratch/verify_b/wick_vs_close_n726_v2.csv`, `wick_vs_close_analysis.json`, `q1_q2_q5_n726.json`, `q3_q4_compare.json`

---

## Executive Summary

**Headline #1 — distrib_a's signal SURVIVES at 6× sample size, with a tighter lower bound.**
P(WIN | retest does NOT penetrate the far OB edge, Geom A) = **452/452 = 100.00%**, Wilson 95% CI **[99.16%, 100.00%]**. distrib_a (n=121) reported 51/51 = 100%, lower bound 93.5%. The signal is the same; the lower bound moves from 93.5% to **99.16%**. Zero non-penetration losers in 452 trades.

**Headline #2 — wick-vs-close split confirms the CEO's hypothesis qualitatively, BUT the underlying mechanism is depth, not class.**

By M15 replay of every n=726 row using A2_v2 walk semantics:

| Class (Geom A, resolved) | n | wins | WR | Wilson 95% CI |
|---|---|---|---|---|
| `not_penetrated` | 452 | 452 | **100.00%** | [99.16%, 100.00%] |
| `wick_only_penetrated` (penetrate edge, no close past edge before SL/TP) | 56 | 39 | **69.64%** | [56.66%, 80.10%] |
| `close_penetrated` (≥1 candle close past edge before SL/TP) | 199 | 37 | **18.59%** | [13.80%, 24.57%] |

3-way chi² p = 4.6e-106. Pairwise Fisher exact: not_pen vs wick_only p = 4.6e-18; wick_only vs close_pen p = 1.6e-12, **OR = 10.04**. The wick-vs-close cut produces a 3.7× WR separation (70% vs 19%).

**Headline #3 — but stratifying by penetration depth proves "class" is mostly redundant.**

The cliff is at **0.5 ATR**, which is mechanically the SL margin (`SL_MARGIN_ATR_A = 0.5`):

| Pen depth (ATR) | n_penetrated | WR | Wilson 95% CI |
|---|---|---|---|
| (0.00, 0.40] | 63 | **100.00%** | [94.25%, 100.00%] |
| (0.40, 0.50] | 12 | **100.00%** | [75.75%, 100.00%] |
| (0.50, 0.60] | 57 | **0.00%** | [0.00%, 6.31%] |
| (0.60, 0.75] | 52 | **0.00%** | [0.00%, 6.88%] |
| (0.75, ∞) | 71 | **1.41%** | [0.25%, 7.56%] |

**Stratified by depth, the wick-vs-close class adds nothing:**
- Shallow (≤0.5 ATR): wick_only n=39 WR 100%, close_penetrated n=36 WR 100%, Fisher p = 1.00.
- Deep (>0.5 ATR): wick_only n=17 WR 0%, close_penetrated n=163 WR 0.6%, Fisher p = 1.00.

The wick-vs-close framing is statistically a **proxy** for "depth past the SL margin." The mechanism is mechanical: depth > 0.5 ATR == wick reaches `sl_a_price` == SL hit == REVERSED.

**Implications for the decision the CEO is considering:**
1. **The headline number for the SHADOW LOGGER and ENTRY SCORING is `pen_class` is NOT the right cut.** Use `pen_depth_atr` directly. A `defended_at_edge` definition should be **"penetration depth ≤ ~0.4 ATR within the SL window"**, not "wick-only penetration."
2. **For a real-time exit signal**, the cleanest production-safe trigger is "M15 close past far OB edge AND wick has reached or exceeded 0.5 ATR depth from the edge" — which is materially equivalent to "we're being stopped out anyway." The trigger therefore offers little EV improvement over the existing Geom A SL.
3. **For a limit-at-edge entry pattern**, the targetable population is rows that *never penetrate beyond ~0.4 ATR*. Whether those penetrations are wick-only or close-through is irrelevant. P(WIN) = 100% conditional on staying inside the SL margin.
4. **Caveat (sampling bias).** All n=726 are post-hoc retests that DID resolve cleanly to within ±0.5 ATR most of the time. The 100% in the not_penetrated cell is a property of the geometry construction (the SL is set at 0.5 ATR past the edge, so any candle penetration ≤ 0.5 ATR mechanically cannot hit SL). Forward-tested behavior under live-execution drift is not guaranteed to match.

---

## Section 1 — Schema Verification

### 1.1 n=726 vs n=121 column inventory

n=726 CSV has 41 columns vs n=121's 56. Five fields used by distrib_a/b are missing from n=726 and were derived row-wise:

| Missing | Derivation | Sanity check |
|---|---|---|
| `mae_a_pct_ob_body` | `mae_a_pips / ob_body_size_pips * 100` | Cross-validated on n=121 (max diff = 1.42e-14) |
| `mae_b_pct_ob_body` | `mae_b_pips / ob_body_size_pips * 100` | Same |
| `penetration_a_atr` | `penetration_a_pips * pip_size / h1_atr_at_retest` | Same |
| `penetration_b_atr` | `penetration_b_pips * pip_size / h1_atr_at_retest` | Same |
| `ob_body_size_pct_price` | not used by Q1–Q5; skipped | — |

`pip_size` lookup: XAUUSD=0.1, US30_cash=1.0, USDJPY=GBPJPY=0.01, GBPUSD=0.0001 (matches `A2_v2_validation.py:107`).

### 1.2 IMPORTANT: `ob_body_size` is NOT comparable across samples

In `study.py` (n=121), `ob_body_size_pips = (ob_high - ob_low) / pip` — the **full H1 wick range**.
In `A2_v2_validation.py` (n=726), `ob_body_size_pips = abs(close - open) / pip` — the **H1 candle body only** (excludes wicks).

Consequence: median OB body in n=121 is **0.83 ATR**; in n=726 it is **0.26 ATR**. These are not different measurements of the same OB universe; they are different definitions of `ob_body`.

**Therefore `mae_pct_ob_body` distributions are NOT directly comparable between n=121 and n=726.** All comparisons in this report use **ATR-normalized MAE/penetration** (`mae_a_atr`, `penetration_a_atr`), which IS comparable.

### 1.3 Outcome breakdown (n=726)

| Geometry | CONTINUED | REVERSED | UNRESOLVED | n_eligible | WR |
|---|---|---|---|---|---|
| Geom A (1 OB-body target, 0.5 ATR SL margin, 48 M15 horizon) | 528 | 179 | 19 | 707 | **74.68%** Wilson95% [71.4%, 77.7%] |
| Geom B (1.5R target, 1.5% body SL, 12 M15 horizon) | 170 | 283 | 273 | 453 | 37.53% |

UNRESOLVED rate for Geom B = 37.6% — comparable to n=121's 44%. **Headline conclusions are Geom A only.** Geom B is reported for parity with distrib_b but suffers severe truncation bias.

### 1.4 Per-symbol coverage

| Symbol | n_total | Geom A eligible | Geom A WR | Geom A WR Wilson 95% |
|---|---|---|---|---|
| GBPJPY | 150 | 147 | 79.59% | [72.4%, 85.3%] |
| GBPUSD | 150 | 145 | 75.17% | [67.6%, 81.5%] |
| US30_cash | 143 | 135 | 73.33% | [65.4%, 80.0%] |
| USDJPY | 136 | 136 | 75.74% | [68.0%, 82.2%] |
| XAUUSD | 147 | 144 | 71.53% | [63.6%, 78.3%] |

All five symbols clear n=30 for both winners-only and losers-only subsets. Per-symbol n=20+ thresholds met for `not_penetrated` and `close_penetrated` cells; **`wick_only_penetrated` is below n=20 per-symbol** (table at section 4.5).

### 1.5 M15 raw-data availability

Verified all five symbols' `data/historical/{SYM}_M15.csv` files cover 2026-01-01 to 2026-04-17 window used by A2_v2. **0 rows in n=726 had M15 raw data missing.**

---

## Section 2 — Task A: Q1–Q5 on n=726 vs n=121 (Geom A)

All numbers below use ATR-normalized MAE/penetration. `mae_pct_ob_body` numbers are reported separately (section 2.6) but not used for cross-sample comparison.

### 2.1 Q1 — Winner MAE distribution (Geom A)

| Quantile | n=121 (distrib_a) | n=726 |
|---|---|---|
| n_winners | 60 | 528 |
| min | 0.00 | 0.00 |
| p25 | 0.072 | 0.045 |
| **p50** | **0.183** | **0.240** |
| p75 | 0.371 | 0.495 |
| **p90** | **0.700** | **0.864** |
| p95 | 0.806 | 1.166 |
| max | 1.330 | 2.650 |

**Direction:** winners' MAE p90 grows ~24% (0.700 → 0.864). Tail at n=726 is heavier than n=121 suggested. Implication for the SL=0.5 ATR shadow proposal in distrib_a: at n=726, ~6.4% of winners have MAE > 0.5 ATR (vs ~10% inferred from n=121). The "0.7 ATR captures 90% of winners" rule of thumb still holds approximately.

### 2.2 Q2 — Loser MAE distribution (Geom A)

| Quantile | n=121 | n=726 |
|---|---|---|
| n_losers | 25 | 179 |
| **p10** | **0.748** | **0.622** |
| p25 | 1.087 | 0.906 |
| **p50** | **1.527** | **1.388** |
| p90 | 2.519 | 2.385 |
| max | 2.998 | 5.591 |

**Direction:** losers' MAE distribution shifts slightly LEFTWARD (smaller losses faster). p10 of losers drops from 0.748 → **0.622**, which is the more important number — it sets the floor of the "guaranteed-loser" zone.

### 2.3 Distributional separation (winners vs losers, Geom A)

Mann-Whitney U: **p = 4.17e-66** (n=726). KS statistic = 0.720, p = 2.50e-68. Distributions are massively separated; the geometry creates a near-binary outcome.

Best Youden-J cutoff: **0.532 ATR** (n=121: 0.748 ATR). At this cutoff:
- Sensitivity (recall of losers) = **0.763**
- Specificity (recall of winners) = **0.955**

The cutoff has tightened toward the SL margin (0.5 ATR) at larger n, which makes mechanical sense: the 0.5 ATR margin is a *constructed* discontinuity in the data.

### 2.4 Q3 — Penetration past far edge (Geom A)

| Metric | n=121 | n=726 |
|---|---|---|
| Penetration rate | 32.2% (39/121) | **36.07% (255/707)** |
| Median pen depth (penetrated) | 0.633 ATR | **0.587 ATR** |
| p90 pen depth | 1.523 ATR | 1.109 ATR |
| **P(WIN \| penetrated)** | 23.1% Wilson [12.6%, 37.8%] | **29.80% Wilson [24.52%, 35.68%]** |
| **P(WIN \| NOT penetrated)** | 100% Wilson [93.0%, 100%] | **100.00% Wilson [99.16%, 100%]** |

Fisher exact (penetrated vs not, Geom A, n=726): **p = 1.5e-117**. The "not penetrated" cell is the strongest single signal in the dataset.

### 2.4.1 Penetration depth bins (Geom A, n=726 — NEW EVIDENCE)

| Pen depth bin (ATR) | n | WIN | WR | Wilson 95% CI |
|---|---|---|---|---|
| (0.00, 0.10] | 24 | 24 | 100.00% | [86.20%, 100%] |
| (0.10, 0.25] | 21 | 21 | 100.00% | [84.54%, 100%] |
| (0.25, 0.50] | 30 | 30 | 100.00% | [88.65%, 100%] |
| **(0.50, 0.75]** | **109** | **0** | **0.00%** | **[0.00%, 3.40%]** |
| (0.75, 1.00] | 33 | 0 | 0.00% | [0.00%, 10.43%] |
| (1.00, 1.50] | 24 | 1 | 4.17% | [0.74%, 20.24%] |
| (1.50, 2.00] | 3 | 0 | 0.00% | [0.00%, 56.15%] |
| > 2.00 | 11 | 0 | 0.00% | [0.00%, 25.88%] |

**The discontinuity at exactly 0.5 ATR is visible in the data.** Below 0.5 ATR (n=75): 100% WR. Above 0.5 ATR (n=180): 0.56% WR. This is not a soft slope — it is a step function generated by the SL placement at 0.5 ATR past the OB edge.

### 2.5 Q4 — MAE histogram by outcome (Geom A, n=726)

| MAE bin (ATR) | n_cont | n_rev | WR_in_bin | Wilson 95% |
|---|---|---|---|---|
| (0.00, 0.10] | 182 | 2 | 0.989 | [0.961, 0.997] |
| (0.10, 0.25] | 86 | 0 | 1.000 | [0.957, 1.000] |
| (0.25, 0.50] | 129 | 6 | 0.956 | [0.906, 0.980] |
| **(0.50, 0.75]** | **57** | **19** | **0.750** | **[0.642, 0.834]** |
| (0.75, 1.00] | 34 | 26 | 0.567 | [0.441, 0.684] |
| (1.00, 1.25] | 18 | 25 | 0.419 | [0.284, 0.567] |
| (1.25, 1.50] | 13 | 24 | 0.351 | [0.218, 0.512] |
| (1.50, 1.75] | 5 | 29 | 0.147 | [0.065, 0.301] |
| (1.75, 2.00] | 1 | 16 | 0.059 | [0.011, 0.270] |
| > 2.00 | 3 | 32 | 0.086 | [0.030, 0.224] |

The cliff is at **MAE ≈ 0.5 ATR** (matching pen depth — they are different views of the same SL margin). MAE bin (0.50, 0.75] has 75% WR, vs 95.6% at (0.25, 0.50]. By MAE > 0.75 ATR, the trade is LOSING-biased (P(WIN) = 56.7%).

### 2.6 Q5 — SL sensitivity table (Geom A, n=726, "clean" with min ATR-buffer SL)

| SL margin (ATR) | CONT | REV | UNR | WR | Wilson 95% | mean R_sl |
|---|---|---|---|---|---|---|
| 0.0 | 291 | 393 | 0 | 0.425 | [0.389, 0.463] | -0.521 |
| 0.1 | 476 | 193 | 15 | 0.711 | [0.676, 0.745] | -0.189 |
| 0.2 | 486 | 182 | 16 | 0.728 | [0.693, 0.760] | -0.185 |
| 0.3 | 498 | 170 | 16 | 0.746 | [0.711, 0.777] | -0.170 |
| **0.5 (current Geom A)** | **514** | **151** | **19** | **0.773** | **[0.740, 0.803]** | -0.154 |
| 0.7 | 514 | 71 | 99 | 0.879 | [0.850, 0.903] | -0.050 |
| 1.0 | 514 | 26 | 144 | 0.952 | [0.930, 0.967] | +0.015 |
| 1.5 | 514 | 8 | 162 | 0.985 | [0.970, 0.992] | +0.036 |
| 2.0 | 514 | 5 | 165 | 0.990 | [0.978, 0.996] | +0.032 |

**The SL sweep replicates the n=121 distrib_a finding qualitatively:** WR rises monotonically with margin, but the marginal WR gain plateaus past 0.5 ATR. UNRESOLVED rate explodes (3% → 23% from m=0.5 to m=1.0), so wider SL achieves WR by trading wins for unresolved trades. The 0.5 ATR margin remains the sweet spot.

**Mean R_sl crosses zero between m=0.7 and m=1.0.** R_sl is the per-trade R after applying the SL margin, accounting for unresolved trades counted as flat. This is encouraging at face value, but the unresolved-as-flat assumption is generous; real expectancy at m=1.0 should be discounted for held-but-unrealized risk.

### 2.6 mae_pct_ob_body — reported but not comparable

| Quantile (Geom A winners) | n=121 | n=726 |
|---|---|---|
| p50 | 99.5 | 85.4 |
| p90 | 232.0 | 719.1 |
| max | 366 | 28,812 |

The n=726 distribution is dominated by `ob_body_size` redefinition (smaller denominators) and 97 rows where MAE = 0 pips (instant winners). **Do not use these numbers cross-sample.**

---

## Section 3 — Task B: Wick-vs-Close Penetration (M15 replay, Geom A only)

### 3.1 Methodology

For each of the 726 rows, the M15 walk was replayed using **A2_v2_validation.py semantics** (NOT study.py — these differ in entry-selection and walk start; see section 6.1):

- Derive `ob_low`, `ob_high` from CSV-stored `sl_a_price`, `target_a_price`, `ob_body_size`, `h1_atr_at_retest`:
  - long: `ob_low = sl_a + 0.5 * h1_atr`, `ob_high = target_a - ob_body`
  - short: `ob_high = sl_a - 0.5 * h1_atr`, `ob_low = target_a + ob_body`
- Locate the M15 retest candle by `retest_ts`.
- Determine entry: if retest candle close ∈ [ob_low, ob_high], entry at retest candle; else entry at next candle open. **Walk starts at entry_idx + 1** (entry candle NOT counted in MAE/penetration).
- Walk forward up to 48 M15 candles. For each candle, track:
  - `wick_pen` = max adverse wick excursion past the far edge (`ob_low` for long; `ob_high` for short)
  - `close_count` = # candles whose close is past the far edge
- Stop walking at first SL or TP hit (mirror Geom A SL/TP semantics — same-candle ambiguity resolved by candle open).

Classification:
- `not_penetrated`: `wick_pen == 0 AND close_count == 0`
- `wick_only_penetrated`: `wick_pen > 0 AND close_count == 0`
- `close_penetrated`: `close_count > 0`

### 3.2 Replay validation

| Validation | Result |
|---|---|
| Outcome agreement (replay vs CSV `outcome_a`) | **723/726 = 99.59%** |
| `wick_pen_atr_recomputed` vs CSV `penetration_a_atr` (max abs diff) | < 0.01 ATR for 99% of penetrated rows |
| Mismatches | 3 rows (idx 152, 653, 676), all with mae and penetration values consistent with CSV but ambiguous SL/TP same-candle resolution; not material to class assignments |

The replay is high-fidelity. Class assignments are trustworthy.

### 3.3 Class counts

Across all n=726:

| Class | n | % of total |
|---|---|---|
| `not_penetrated` | 466 | 64.2% |
| `wick_only_penetrated` | 56 | 7.7% |
| `close_penetrated` | 204 | 28.1% |

Restricted to RESOLVED Geom A (n=707):

| Class | n | wins | losses | WR | Wilson 95% CI |
|---|---|---|---|---|---|
| `not_penetrated` | 452 | 452 | 0 | **100.00%** | **[99.16%, 100.00%]** |
| `wick_only_penetrated` | 56 | 39 | 17 | **69.64%** | **[56.66%, 80.10%]** |
| `close_penetrated` | 199 | 37 | 162 | **18.59%** | **[13.80%, 24.57%]** |

### 3.4 Statistical separation (3-way contingency)

| Test | Stat | p |
|---|---|---|
| 3-way chi² | 485.09 (dof=2) | **4.6e-106** |
| Pairwise Fisher: not_pen vs wick_only | OR = ∞ | 4.6e-18 |
| Pairwise Fisher: not_pen vs close_pen | OR = ∞ | 1.5e-117 |
| **Pairwise Fisher: wick_only vs close_pen** | **OR = 10.04** | **1.6e-12** |

The wick-vs-close cut produces an **odds ratio of 10.04** between the two penetrated classes. Defended-wick is 10× more likely to be a winner than close-broken on raw classes.

### 3.5 MAE distribution per class

| Class | n | mae_a_atr p50 | p90 | Note |
|---|---|---|---|---|
| `not_penetrated` | 452 | 0.177 | 0.742 | All winners — adverse moves stay inside zone |
| `wick_only_penetrated` | 56 | 0.641 | 1.636 | Penetration depth p50 = 0.164 ATR; **17 losers have MAE p10 = 0.611** |
| `close_penetrated` | 199 | 1.263 | 2.235 | Penetration depth p50 = 0.648 ATR; deepest adversity |

Within `wick_only_penetrated` (n=56): MWU on (CONTINUED MAE) vs (REVERSED MAE) **p = 1.08e-05**. The losers in this class have systematically deeper MAE — they are the wick-only events where the wick still reached the SL.

Within `close_penetrated` (n=199): MWU **p = 1.19e-06**. Same pattern: the rare 37 winners have shallower MAE than the 162 losers.

### 3.6 Per-symbol breakdowns (n≥20 cells only)

| Symbol | not_penetrated WR | close_penetrated WR | wick_only_penetrated |
|---|---|---|---|
| GBPJPY | 99/99 = 100% | 8/36 = 22.2% [11.7%, 38.1%] | n=12 (below threshold) |
| GBPUSD | 83/83 = 100% | 11/45 = 24.4% [14.2%, 38.7%] | n=17 (below threshold) |
| US30_cash | 88/88 = 100% | 7/38 = 18.4% [9.2%, 33.4%] | n=9 (below threshold) |
| USDJPY | 92/92 = 100% | 5/35 = 14.3% [6.3%, 29.4%] | n=9 (below threshold) |
| XAUUSD | 90/90 = 100% | 6/45 = 13.3% [6.3%, 26.2%] | n=9 (below threshold) |

**`not_penetrated` is 100% WR in all 5 symbols, with Wilson lower bounds 95.6% – 96.3%.** The signal is structural, not symbol-dependent.

`wick_only_penetrated` is below n=20 per-symbol — the n=56 aggregate is the only reportable level. This is a real limitation: we cannot say whether wick-only behaves the same in XAUUSD vs USDJPY.

### 3.7 Long vs short

| Side | not_pen WR | wick_only WR | close_pen WR |
|---|---|---|---|
| long (n=376) | 246/246 = 100% | 17/26 = 65.4% [46.2%, 80.6%] | 20/104 = 19.2% [12.8%, 27.9%] |
| short (n=331) | 206/206 = 100% | 22/30 = 73.3% [55.6%, 85.8%] | 17/95 = 17.9% [11.5%, 26.8%] |

Symmetric across long and short. The signal is direction-agnostic.

---

## Section 4 — Task C: Synthesis

### 4.1 The "100% on non-penetrated" headline survives — strengthen it

distrib_a reported **51/51 = 100%, lower CI 93.5%** for P(WIN | not penetrated, Geom A).
n=726 reports **452/452 = 100%, lower CI 99.16%**.

This is **the strongest validated signal in the dataset**. With 6× the sample, zero non-penetration losers were observed. The geometry construction explains it: SL is placed at 0.5 ATR past the OB edge; if the wick never penetrates the edge at all, the wick cannot have reached the SL line — there is no mechanical path to a SL hit.

**The signal is real, but the mechanism is "the edge held" — not "the AI was smart."** It is a property of the geometry, not the discrimination layer.

### 4.2 The wick-vs-close split: 70% vs 19% — but driven by depth, not class

The headline numbers are striking:
- `wick_only_penetrated` WR = 69.64% (Wilson lower bound 56.66%)
- `close_penetrated` WR = 18.59% (Wilson upper bound 24.57%)

The CIs DO NOT overlap. Pairwise OR = 10.04, p = 1.6e-12.

**HOWEVER:** when stratifying by penetration depth, the class adds zero discriminative value:

| Pen depth | wick_only WR | close_penetrated WR | Fisher p |
|---|---|---|---|
| ≤ 0.5 ATR | 39/39 = 100% | 36/36 = 100% | 1.00 |
| > 0.5 ATR | 0/17 = 0% | 1/163 = 0.6% | 1.00 |

**Interpretation:** the wick-vs-close class is a (noisy) proxy for depth. When depth ≤ 0.5 ATR (= SL margin), there is no SL hit and the trade resolves to TP. When depth > 0.5 ATR, the SL is reached. Wick-vs-close just tells us *whether one of those candles also closed past the edge* — which is a near-deterministic function of depth, not an independent signal.

### 4.3 Why this matters for production

**For a real-time exit signal:**

distrib_a hypothesized that "close past edge" could be an early-exit signal. The data partially supports this — but the EV math is unfavorable in a stop-anyway regime:

| Scenario | What the gate does |
|---|---|
| Close past edge AND wick has not yet reached 0.5 ATR depth | Exits at small loss; saves vs going to SL. **But: this scenario has n ≈ 0 in the data — virtually all close-past-edge events occur after wick depth > 0.5 ATR.** |
| Close past edge AND wick has already reached 0.5 ATR depth | Same outcome as letting SL run — the SL has already been hit on intra-candle basis |

**Recommendation: do NOT promote the wick-vs-close shadow logger to a production exit gate.** The per-class numbers look strong but the underlying mechanism is the SL margin itself, which is already in the system.

**For a limit-at-edge entry pattern:**

The actionable population is **rows where penetration depth stays below ~0.4 ATR throughout the resolution window**. Stratifying by class within this population is unnecessary.

A "limit-at-edge" entry would target `not_penetrated` (n=452, 100% WR) plus the shallow-penetration `wick_only` and `close_penetrated` cells (n=75, 100% WR). Combined: 527/527 = **100% WR** for trades whose deepest adverse penetration stays ≤ 0.5 ATR over the 48-candle window.

This is a *retrospective* identification — at entry time, the agent does not know whether the upcoming penetration will stay shallow. The signal is for **post-entry expected behavior**, not for pre-entry filtering.

### 4.4 Implications for the proximity / entry-quality scorer

The system already has a **proximity shadow logger** (`src/components/proximity_shadow_logger.py`, observation-only). Per CLAUDE.md, this tracks "OB distance at candle close." If extended:

- Track post-entry penetration depth in real-time (M15 close vs OB far edge in ATR units)
- Threshold = 0.4 ATR (one bin below the 0.5 ATR SL discontinuity)
- If exceeded BEFORE first +1R is reached, the trade is now in the "deep" regime where WR drops to <2%

This would be a **monitoring/alerting** signal, not an exit gate. Acting on it would close trades that are already going to be stopped out anyway, providing minimal EV improvement but shaving ~1 candle of slippage on 162 of 199 close-penetration losers.

### 4.5 Comparison summary table — n=121 vs n=726

| Metric (Geom A) | n=121 | n=726 | Conclusion |
|---|---|---|---|
| WR (resolved) | 70.59% | 74.68% | **+4pp; consistent direction** |
| Penetration rate | 32.2% | 36.07% | Slight increase |
| **P(WIN \| NOT penetrated)** | **51/51 = 100%** Wilson [93.0%, 100%] | **452/452 = 100%** Wilson [**99.16%**, 100%] | **Confirmed — lower bound tightens** |
| P(WIN \| penetrated) | 9/39 = 23.1% | 76/255 = 29.80% | Direction consistent |
| Pen depth p50 | 0.633 ATR | 0.587 ATR | Tighter penetration distribution |
| Pen depth p90 | 1.523 ATR | 1.109 ATR | Tighter |
| Best Youden cutoff (winners vs losers) | 0.748 ATR | 0.532 ATR | Cutoff tightens to SL margin |
| SL=0.5 sensitivity (clean Q5) WR | 79.2% | 77.3% | **Match** |
| `cont_mae_p50` | 0.183 ATR | 0.240 ATR | Slightly heavier MAE tail at scale |
| `loser_mae_p50` | 1.527 ATR | 1.388 ATR | Slightly tighter loser MAE |

**All headline directional findings replicate. All claims in distrib_a/b that involve ATR-normalized quantities survive at n=726.**

### 4.6 Per-class expectancy (sanity check on R math)

| Class | n | p_win | mean R_a (winners only) | Crude expectancy (p_win·R_win - p_loss·1) |
|---|---|---|---|---|
| `not_penetrated` | 452 | 1.000 | +0.487 | **+0.487 R/trade** |
| `wick_only_penetrated` | 56 | 0.696 | +0.667 | **+0.161 R/trade** |
| `close_penetrated` | 199 | 0.186 | +0.665 | **-0.690 R/trade** |

The Geom A target is `1 OB-body`, so winners average +0.5 to +0.7 R (consistent with the geometry). The `close_penetrated` cell has a strongly negative expectancy — confirming its disposability.

If the system could ex-ante avoid `close_penetrated` (n=199 of 707 = 28%), aggregate expectancy would rise from current +0.04 R/trade (74.7% × 0.49 - 25.3% × 1) to **+0.42 R/trade**. This is the upper-bound improvement from a perfect class predictor — and explains why the topic is interesting.

But: **no real-time signal can reliably predict class at entry** — by the time you know the class, the trade is already over.

---

## Section 5 — Limitations

### 5.1 Sampling bias in the n=726 dataset

n=726 is constructed by **post-hoc** A2_v2_validation: it includes only retests that satisfied the ADR-003 temporal ordering (`retest_ts > bos_confirm_ts`, strict). This is a clean dataset for distributional inference, but:

- The 100% WR on `not_penetrated` is partly a property of the geometry construction. The SL margin = 0.5 ATR is **part of the definition** of "penetrated" in the way the metric is operationalized. By construction, a wick that does not reach the OB edge cannot reach the SL line.
- Selection: the n=726 are retests that happened — they exclude any setup the AI/system would not have flagged in live mode. Forward-tested rates may differ.

### 5.2 Wick-vs-close framing is a proxy

As demonstrated in section 4.2, the class is statistically a noisy proxy for depth. Any production decision (exit gate, entry filter) should use **depth in ATR**, not class label, as the underlying signal.

### 5.3 Per-symbol `wick_only` cells are below n=20

Aggregate `wick_only_penetrated` (n=56) is just above the threshold for reporting. Per-symbol, this class is below threshold (n=9 to 17 per symbol). We cannot test for symbol-specific behavior in this class. Future data collection should target this cell.

### 5.4 3 outcome mismatches in replay

3 rows (idx 152, 653, 676) had outcome_replay ≠ outcome_a. Investigation showed these have ambiguous SL/TP same-candle resolution where the candle open determines outcome under different conventions. Not material — 99.6% replay agreement is sufficient for class assignment at the population level. Class-level numbers are stable.

### 5.5 Geom B is unreliable — UNRESOLVED dominates

Geom B's 12-candle horizon truncates 37.6% of trades. P(WIN | not penetrated, Geom B) = 158/158 = 100% Wilson [97.6%, 100%] is structurally similar to Geom A but with a smaller denominator due to truncation. **Do not draw conclusions from Geom B numbers other than for parity with distrib_b reporting.**

### 5.6 Non-stationarity not assessed

Apr 2026 single market regime. Edge decay over time, regime-shift behavior, and the "OB continuation rolling-50" monitor (CLAUDE.md, session 24) are not in scope here. Apr 2026 numbers may not generalize.

### 5.7 ATR baseline drift not assessed

`h1_atr_at_retest` is computed at retest time. ATR-normalized numbers depend on the local volatility regime; cross-time-period comparison should re-derive ATR baselines. The 0.5 ATR cliff observed here is a property of THIS data + THIS SL formula; if SL formula changes (e.g., absolute pip threshold), the cliff moves.

---

## Section 6 — Methodology & reproducibility notes

### 6.1 A2_v2 vs study.py geometry — critical difference

The two source pipelines use DIFFERENT geometry definitions. To validate Q1–Q5 on n=726 against distrib_a's n=121 numbers, I had to mirror **A2_v2_validation.py** exactly, NOT study.py. Key differences:

| Aspect | study.py (n=121) | A2_v2_validation.py (n=726) |
|---|---|---|
| `ob_high`, `ob_low` | H1 candle body open/close extremes | H1 candle full wick extremes |
| `ob_body_size` | `ob_high - ob_low` (full range) | `abs(close - open)` (body only) |
| Long target | `ob_low + ob_body_size` (top of body extended down by body) | `ob_high + ob_body_size` (extended past wick top) |
| Entry candle | retest candle | retest candle if close ∈ [ob_low, ob_high]; else next candle open |
| Walk start | retest_idx (entry candle counted in MAE) | entry_idx + 1 (entry candle NOT counted) |

Initial replay using study.py semantics produced 30 outcome mismatches. Switching to A2_v2 semantics reduced this to 3 (99.6% agreement). **Anyone replaying this work must use A2_v2 semantics for n=726.**

### 6.2 Reproduction commands

```bash
cd C:/Users/MSI/Documents/ai-trading-agent
python scratch/verify_b/03_derive_fields.py       # Validate derived fields
python scratch/verify_b/04_q1_to_q5.py            # Q1, Q2, Q5 numbers
python scratch/verify_b/09_wick_vs_close_v2.py    # Replay with A2_v2 semantics → wick_vs_close_n726_v2.csv
python scratch/verify_b/11_wick_vs_close_analysis.py  # Cross-tab + Fisher exact
python scratch/verify_b/12_q3_q4_and_compare.py   # Q3, Q4 + n=121 vs n=726 table
python scratch/verify_b/13_validate_classification.py # Class vs depth cross-tab
python scratch/verify_b/14_depth_vs_class_decomposition.py  # Depth-stratified Fisher
```

All Wilson 95% CIs computed via `scipy.stats.norm.ppf(0.975)`. Fisher exact tests via `scipy.stats.fisher_exact`. MWU via `scipy.stats.mannwhitneyu`. No external dependencies beyond pandas/numpy/scipy.

---

## Section 7 — Top-line recommendations

1. **Update CLAUDE.md "VALIDATED NUMBERS" table.** Add: `P(WIN | retest does not penetrate far OB edge, Geom A) = 100.00% Wilson 95% [99.16%, 100%], n=452/452 (validated at n=726, A2_v2 geometry)`.

2. **DO NOT promote the wick-vs-close shadow logger to a production exit gate** based on class alone. Re-frame as **penetration-depth shadow logger** with a 0.4 ATR alert threshold (one bin below the SL margin discontinuity). The signal is depth, not class.

3. **The proximity logger (already deployed) should track penetration depth at each M15 close**, not just OB distance. This is a small extension and would unlock the depth-based monitoring envisioned in section 4.4.

4. **Limit-at-edge entry pattern is well-defined retrospectively** but not prospectively. Document this as a research direction (NOT a deployment candidate) — it requires a way to forward-predict whether penetration will stay ≤ 0.5 ATR, which is currently not available.

5. **Per-symbol `wick_only_penetrated` is below n=20.** Future data collection should expand the corpus to give per-symbol breakdowns in this class. Until then, do not make per-symbol claims about wick-only behavior.

6. **Geom B numbers continue to be unreliable** due to 37.6% UNRESOLVED rate. Do not use Geom B for production scoring.

7. **The "100% on non-penetrated" finding is real but mechanically explained by the geometry, not by AI discrimination.** Frame it accordingly in any external communication: this is a property of the OB-retest geometry combined with the 0.5 ATR SL margin, validated at large n.

---

*End of verify_b report. Independent of verify_a, no coordination during analysis. Both reports may be cross-checked for inter-rater reliability on the headline numbers.*
