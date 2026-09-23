# distrib_b — OB Retest Geometry Distributional Analysis

**Source:** `research/retest_geometry/outputs/historical/combined_retests.csv` (n=121, ADR-003-compliant)
**Author:** distrib_b (independent analyst, no coordination with distrib_a)
**Date:** 2026-04-18

---

## Executive Summary

**Headline numbers (Geom A, n=121, 77 CONTINUED / 33 REVERSED / 11 UNRESOLVED):**

1. **Winner MAE (Q1):** median **0.38× ATR**, p75 **0.75× ATR**, p90 **1.06× ATR**, p95 **1.17× ATR**. The current SL distance from entry (0.5×ATR + median etf 0.84 = ~1.34×ATR) is roughly aligned with the winner-MAE p90.

2. **Loser MAE (Q2):** median **1.51× ATR**, p10 **0.87× ATR**. Mann-Whitney U winner-vs-loser MAE: **p < 1e-12** (mechanically expected; useful as data-quality sanity).

3. **Penetration past far edge (Q3):** **58/121 = 47.9%** of all rows have any penetration. P(WIN | penetrated, ex-UNR) = **40.0%** vs P(WIN | not penetrated) = **100.0%** (Fisher p < 1e-12). **Penetration is a strong reversal signal but not absolute** — 22 CONTINUED rows had some penetration.

4. **Reversal point within OB (Q4):** CONTINUED median MAE = **55% of OB body**, vs REVERSED median **196%**. Win rate ex-UNR is **100%** in bins 0-100% of OB, then drops sharply: 100-125% bin = 54.5%, 150-200% = 23.1%, >200% = 26.3%. **The 100% boundary is the cliff** — once price clears the far edge by any meaningful margin, win probability collapses.

5. **SL sensitivity (Q5):** clean-sample knee (mean R-units) at **m = 1.0× ATR** (+0.480 R) vs live m=0.5 (+0.324 R). Tightening below 0.3× ATR clearly destroys expectancy. **m=0.7-1.0 looks marginally better** but the improvement is largely an artefact of REVERSED rows being reclassified as UNRESOLVED (no bar-level data to confirm later target hits). **Recommendation: shadow-test m=0.7 for ≥30 trades before changing live.**

**Key caveats:** n=121 is small. SL re-scoring lacks bar-level data (looser-SL outcomes are conservatively marked UNRESOLVED, not WIN). Geom B's tight SL produces 43.8% UNRESOLVED — the 3h horizon is too short for meaningful Geom B conclusions.

---

## 1. Data Verification

- Rows: **121** (expected n=121, ADR-003-compliant)
- Columns: 34
- Symbols: USDJPY=33, US30_cash=28, XAUUSD=22, GBPJPY=19, GBPUSD=19
- Sides: long=88, short=33
- Sessions (NaN=7): Tokyo=60, NY=31, London=23, nan=7

**Outcome semantics (verified by reading `study.py:626-754`):**
- `CONTINUED` = target hit before SL within horizon → equivalent to WIN
- `REVERSED` = SL hit before target within horizon → equivalent to LOSS
- `UNRESOLVED` = neither hit within horizon (Geom A: 48 M15 candles = 12h; Geom B: 12 M15 candles = 3h)
- Entry candle (j=0) is excluded from SL/TP checks but INCLUDED in MAE/penetration tracking

**Outcome counts:**

| Outcome | Geom A | Geom B |
|---------|--------|--------|
| CONTINUED | 77 | 33 |
| REVERSED | 33 | 35 |
| UNRESOLVED | 11 | 53 |

**NaN counts (key fields):**

| field | NaN |
|---|---|
| `mae_a_atr` | 0 |
| `mae_a_pct_ob_body` | 0 |
| `penetration_a_atr` | 0 |
| `mae_b_atr` | 0 |
| `mae_b_pct_ob_body` | 0 |
| `penetration_b_atr` | 0 |
| `continuation_r_a` | 44 |
| `continuation_r_b` | 88 |

**Note on continuation_r NaNs:** expected — only CONTINUED rows have a `continuation_r` value. Geom A: 44 NaN = 33 REVERSED + 11 UNRESOLVED. Geom B: 88 NaN = 35 REVERSED + 53 UNRESOLVED. Confirmed clean.

**Sanity checks on extreme values:**

- `mae_a_atr` range: [0.039, 4.918]
- `mae_a_pct_ob_body` range: [6.9%, 814.1%]
- `penetration_a_atr` range: [0.000, 3.106]
- `ob_body_size_atr` range: [0.189, 2.189]
- `mae_a_pct_ob_body` > 100% (penetrated past far edge): **53/121** (43.8%)
- `mae_a_pct_ob_body` > 200%: 21/121 (17.4%)
- `mae_a_pct_ob_body` < 0%: 0 (negative would indicate field semantic anomaly; OK if 0)

**Cross-reference (a2_validation):** independent reimplementation has n=1141 rows. Used only for sanity comparisons; not for primary numbers.

**Derived field:** `entry_to_far_atr` — distance from entry to far OB edge in ATR units, computed by inverting the SL_A formula. Distribution:
- n=121 | mean=0.886 | std=0.725 | p10=-0.001 | p25=0.467 | p50=0.842 | p75=1.193 | p90=1.764 | p95=2.049 | max=4.162
- Negative values: 13 (entry candle wicked through OB — entry sits outside the far edge)

---

## Q1. MAE Distribution of WINNERS (CONTINUED)

**Question:** how much adverse excursion does a typical winner endure before reversing? If we tighten SL below the winner-MAE p90, ~10% of real winners would be killed.

### Geom A — Winners
**n = 77 winners** out of 121 retests (63.6% of all rows)

- `mae_a_atr`: n=77 | mean=0.538 | std=0.416 | p10=0.157 | p25=0.236 | p50=0.382 | p75=0.747 | p90=1.055 | p95=1.175 | max=2.038
- `mae_a_pct_ob_body`: n=77 | mean=72.6 | std=64.0 | p10=16.8 | p25=28.4 | p50=55.4 | p75=93.3 | p90=144.4 | p95=217.6 | max=309.3

**Per symbol (Geom A, n>=20 only):**

| symbol | n_wins | mean ATR | p50 ATR | p75 ATR | p90 ATR | mean %OB | p50 %OB | p90 %OB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GBPJPY | n=19 (too small) | — | — | — | — | — | — | — |
| GBPUSD | n=19 (too small) | — | — | — | — | — | — | — |
| US30_cash | 12 | 0.581 | 0.442 | 0.915 | 1.148 | 66.2 | 52.4 | 89.4 |
| USDJPY | 29 | 0.458 | 0.327 | 0.587 | 0.858 | 74.0 | 54.8 | 176.2 |
| XAUUSD | 15 | 0.582 | 0.651 | 0.775 | 0.829 | 80.6 | 83.0 | 102.0 |

### Geom B — Winners
**n = 33 winners** out of 121 retests (27.3% of all rows)

- `mae_b_atr`: n=33 | mean=0.377 | std=0.418 | p10=0.093 | p25=0.180 | p50=0.262 | p75=0.355 | p90=0.651 | p95=1.220 | max=2.026
- `mae_b_pct_ob_body`: n=33 | mean=56.1 | std=62.9 | p10=9.9 | p25=20.6 | p50=39.4 | p75=55.3 | p90=117.4 | p95=182.6 | max=300.6

**Per symbol (Geom B, n>=20 only):**

| symbol | n_wins | mean ATR | p50 ATR | p75 ATR | p90 ATR | mean %OB | p50 %OB | p90 %OB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GBPJPY | n=19 (too small) | — | — | — | — | — | — | — |
| GBPUSD | n=19 (too small) | — | — | — | — | — | — | — |
| US30_cash | 3 | 0.437 | 0.255 | 0.616 | 0.832 | 109.7 | 18.9 | 244.2 |
| USDJPY | 14 | 0.358 | 0.254 | 0.301 | 0.490 | 50.0 | 32.4 | 103.2 |
| XAUUSD | 2 | 0.247 | 0.247 | 0.281 | 0.302 | 37.6 | 37.6 | 50.4 |

### Interpretation (Geom A)
- Median winner endures **0.38× ATR** of MAE; 75% endure ≤ **0.75 ATR**; 90% endure ≤ **1.06 ATR**; 95% endure ≤ **1.17 ATR**.
- Setting an SL at < ~**1.06× ATR from entry** would have killed ~10% of historical winners.
- Note: Geom A's actual SL distance from entry is `entry_to_far + 0.5×ATR` = median 0.84 + 0.5 = ~1.34 ATR. The current 0.5×ATR margin past the OB IS already roughly aligned with the winner-MAE p90.

---

## Q2. MAE Distribution of LOSERS (REVERSED)

**Question:** how does loser MAE compare to winner MAE? Is there a separation point?

### Geom A — Losers
**n = 33 losers**

- `mae_a_atr`: n=33 | mean=1.742 | std=0.970 | p10=0.873 | p25=1.106 | p50=1.510 | p75=2.034 | p90=2.694 | p95=3.551 | max=4.918
- `mae_a_pct_ob_body`: n=33 | mean=219.2 | std=130.1 | p10=118.3 | p25=148.3 | p50=196.1 | p75=238.6 | p90=333.9 | p95=389.4 | max=814.1

### Geom B — Losers
**n = 35 losers**

- `mae_b_atr`: n=35 | mean=1.104 | std=0.629 | p10=0.375 | p25=0.631 | p50=1.048 | p75=1.351 | p90=2.059 | p95=2.326 | max=2.724
- `mae_b_pct_ob_body`: n=35 | mean=179.9 | std=128.0 | p10=94.9 | p25=112.2 | p50=161.0 | p75=192.2 | p90=233.0 | p95=304.5 | max=814.1

### Geom A — Winner vs Loser Separation

| Stat | Winners (CONTINUED) | Losers (REVERSED) |
|---|---:|---:|
| p10 mae_atr | 0.157 | 0.873 |
| p25 mae_atr | 0.236 | 1.106 |
| p50 mae_atr | 0.382 | 1.510 |
| p75 mae_atr | 0.747 | 2.034 |
| p90 mae_atr | 1.055 | 2.694 |
| p95 mae_atr | 1.175 | 3.551 |
| mean mae_atr | 0.538 | 1.742 |
| n | 77 | 33 |

**Mann-Whitney U (winner MAE < loser MAE):** U=190, p=9.525e-13

**Overlap region:**
- Winner p90 MAE = **1.06 ATR**
- Loser p10 MAE = **0.87 ATR**
- Loser p25 MAE = **1.11 ATR**
- Winner p75 MAE = **0.75 ATR**
- Overlap = winners with MAE > 0.87 ATR AND losers with MAE < 1.06 ATR.
- 14/77 winners have MAE >= loser p10
- 8/33 losers have MAE <= winner p90

**Important caveat:** loser MAE is *mechanically* >= the SL distance (REVERSED iff price reached SL). Winner MAE is mechanically < the SL distance (CONTINUED iff price never hit SL). The 'separation point' is therefore the SL distance itself. This MAE distribution is informative for **WHERE WITHIN THE WINDOW BEFORE TARGET** the average winner draws down — not for predicting outcomes from MAE in real time.

---

## Q3. Penetration Frequency Past Far OB Edge

### Geom A
- **(a)** Rows with any penetration past far edge: **58/121** = 47.9% [39.2, 56.8] (Wilson 95% CI)
- **(b)** Conditional penetration depth (rows with pen>0): n=58 | mean=0.736 | std=0.555 | p10=0.195 | p25=0.415 | p50=0.644 | p75=0.911 | p90=1.252 | p95=1.657 | max=3.106
- **(c)** P(CONTINUED | penetrated, ex-UNR): **40.0% [28.1, 53.2] (n=55)**
  P(CONTINUED | no penetration, ex-UNR): **100.0% [93.5, 100.0] (n=55)**
  Fisher exact (penetration vs no-penetration on outcome): p=2.065e-13
  CONTINUED-AND-PENETRATED depth: n=22 | mean=0.429 ATR | p50=0.349 | p90=1.001 | max=1.338
  REVERSED-AND-PENETRATED depth: n=33 | mean=0.975 ATR | p50=0.726 | p90=1.578 | max=3.106

### Geom B
- **(a)** Rows with any penetration past far edge: **47/121** = 38.8% [30.6, 47.7] (Wilson 95% CI)
- **(b)** Conditional penetration depth (rows with pen>0): n=47 | mean=0.532 | std=0.480 | p10=0.104 | p25=0.187 | p50=0.292 | p75=0.808 | p90=1.212 | p95=1.449 | max=1.990
- **(c)** P(CONTINUED | penetrated, ex-UNR): **20.5% [11.2, 34.5] (n=44)**
  P(CONTINUED | no penetration, ex-UNR): **100.0% [86.2, 100.0] (n=24)**
  Fisher exact (penetration vs no-penetration on outcome): p=2.565e-11
  CONTINUED-AND-PENETRATED depth: n=9 | mean=0.639 ATR | p50=0.689 | p90=1.209 | max=1.338
  REVERSED-AND-PENETRATED depth: n=35 | mean=0.526 ATR | p50=0.283 | p90=1.213 | max=1.990

---

## Q4. Histogram of `mae_pct_ob_body`

Where in the OB does the typical retest reach before turning? 0% = reverses at entry; 100% = reverses at far edge; >100% = penetrates past far edge.

### Geom A
| bin (% of OB) | total | %total | CONTINUED | REVERSED | UNRESOLVED |
|---|---:|---:|---:|---:|---:|
| <0 | 0 | 0.0% | 0 | 0 | 0 |
| 0-25 | 17 | 14.0% | 17 | 0 | 0 |
| 25-50 | 17 | 14.0% | 17 | 0 | 0 |
| 50-75 | 18 | 14.9% | 16 | 0 | 2 |
| 75-100 | 16 | 13.2% | 12 | 0 | 4 |
| 100-125 | 12 | 9.9% | 6 | 5 | 1 |
| 125-150 | 6 | 5.0% | 1 | 4 | 1 |
| 150-200 | 14 | 11.6% | 3 | 10 | 1 |
| >200 | 21 | 17.4% | 5 | 14 | 2 |

**All-outcomes summary:** n=121 | mean=117.5 | std=107.7 | p10=20.6 | p25=46.7 | p50=89.7 | p75=161.0 | p90=238.6 | p95=288.0 | max=814.1
- CONTINUED median: **55.4%** of OB body
- REVERSED median: **196.1%** of OB body
- Modal bin (all): **>200** (21 rows)
- Modal bin (CONTINUED only): **0-25**
- Modal bin (REVERSED only): **>200**

**P(CONTINUED | bin), ex-UNR, with Wilson 95% CI:**
| bin | n_resolved | n_continued | rate (Wilson 95% CI) |
|---|---:|---:|---|
| <0 | 0 | — | — |
| 0-25 | 17 | 17 | 100.0% [81.6, 100.0] (n=17) |
| 25-50 | 17 | 17 | 100.0% [81.6, 100.0] (n=17) |
| 50-75 | 16 | 16 | 100.0% [80.6, 100.0] (n=16) |
| 75-100 | 12 | 12 | 100.0% [75.8, 100.0] (n=12) |
| 100-125 | 11 | 6 | 54.5% [28.0, 78.7] (n=11) |
| 125-150 | 5 | 1 | 20.0% [3.6, 62.4] (n=5) |
| 150-200 | 13 | 3 | 23.1% [8.2, 50.3] (n=13) |
| >200 | 19 | 5 | 26.3% [11.8, 48.8] (n=19) |

### Geom B
| bin (% of OB) | total | %total | CONTINUED | REVERSED | UNRESOLVED |
|---|---:|---:|---:|---:|---:|
| <0 | 0 | 0.0% | 0 | 0 | 0 |
| 0-25 | 19 | 15.7% | 11 | 0 | 8 |
| 25-50 | 22 | 18.2% | 11 | 0 | 11 |
| 50-75 | 21 | 17.4% | 6 | 2 | 13 |
| 75-100 | 20 | 16.5% | 1 | 4 | 15 |
| 100-125 | 8 | 6.6% | 1 | 4 | 3 |
| 125-150 | 6 | 5.0% | 0 | 5 | 1 |
| 150-200 | 14 | 11.6% | 1 | 11 | 2 |
| >200 | 11 | 9.1% | 2 | 9 | 0 |

**All-outcomes summary:** n=121 | mean=96.2 | std=96.0 | p10=19.8 | p25=37.5 | p50=74.7 | p75=128.0 | p90=180.4 | p95=222.3 | max=814.1
- CONTINUED median: **39.4%** of OB body
- REVERSED median: **161.0%** of OB body
- Modal bin (all): **25-50** (22 rows)
- Modal bin (CONTINUED only): **0-25**
- Modal bin (REVERSED only): **150-200**

**P(CONTINUED | bin), ex-UNR, with Wilson 95% CI:**
| bin | n_resolved | n_continued | rate (Wilson 95% CI) |
|---|---:|---:|---|
| <0 | 0 | — | — |
| 0-25 | 11 | 11 | 100.0% [74.1, 100.0] (n=11) |
| 25-50 | 11 | 11 | 100.0% [74.1, 100.0] (n=11) |
| 50-75 | 8 | 6 | 75.0% [40.9, 92.9] (n=8) |
| 75-100 | 5 | 1 | 20.0% [3.6, 62.4] (n=5) |
| 100-125 | 5 | 1 | 20.0% [3.6, 62.4] (n=5) |
| 125-150 | 5 | 0 | 0.0% [0.0, 43.4] (n=5) |
| 150-200 | 12 | 1 | 8.3% [1.5, 35.4] (n=12) |
| >200 | 11 | 2 | 18.2% [5.1, 47.7] (n=11) |

---

## Q5. SL Sensitivity Analysis

**Approach:** for each row, re-score the outcome at SL multiples m ∈ {0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0} × H1 ATR past the far OB edge. (Geom A only — Geom B uses a different SL formula and is not the live system's SL.)

**Decision:** SL re-scoring requires comparing the worst MAE-past-far-edge against the new SL margin. Since the CSV exposes `penetration_a_atr` directly (max distance past the far OB edge throughout the 48-candle window), the rule simplifies to: **stopped at margin m iff penetration_atr >= m**.

**Caveats:**
- Penetration is computed from j=0 (entry candle); the simulator's SL/TP check skips j=0. **Skip-entry-candle exception:** for CONTINUED rows with `time_to_mae == 0`, the worst penetration was on j=0, and a tighter SL also wouldn't have triggered in real-world execution (entries fill at the candle close or next-candle open, so the wick that registered MAE happened BEFORE entry). For these 13 rows I preserve CONTINUED.
- For other CONTINUED rows: if `time_to_mae > 0` AND `time_to_mae < time_to_continuation`, the worst MAE happened mid-window before target hit → flip to REVERSED under tighter SL. If `time_to_mae >= time_to_continuation`, MAE recorded at/after target hit → preserve CONTINUED.
- For UNRESOLVED rows, tighter SL may convert them to REVERSED (if max penetration exceeded m) or leave them UNRESOLVED. Looser SL leaves them UNRESOLVED.
- Geom A target is FIXED (entry + ob_body, regardless of SL), so loosening SL does NOT shrink the target. Loosening SL turns some REVERSED rows into either CONTINUED (if target was hit before max MAE) or UNRESOLVED.
- I do NOT attempt to re-score CONTINUED rows that were stopped UNDER tighter SL but might still have hit target later — that would require bar-by-bar walk; the CSV only gives `time_to_mae` and `time_to_continuation`. I flag the rare case `time_to_mae < time_to_continuation` (max MAE happens BEFORE target hit) as 'now REVERSED' under tighter SL, and the case `time_to_mae >= time_to_continuation` (max MAE registers AT or AFTER target hit) as 'still CONTINUED'.

| SL margin (×ATR) | CONTINUED | REVERSED | UNRESOLVED | WR (ex-UNR) | Expectancy_R (ex-UNR) | Total resolved |
|---:|---:|---:|---:|---:|---:|---:|
| **0.0** | 39 | 82 | 0 | 32.2% | -0.242 | 121 |
| **0.1** | 67 | 46 | 8 | 59.3% | +0.356 | 113 |
| **0.2** | 68 | 44 | 9 | 60.7% | +0.424 | 112 |
| **0.3** | 69 | 43 | 9 | 61.6% | +0.442 | 112 |
| **0.5** | 75 | 35 | 11 | 68.2% | +0.604 | 110 |
| **0.7** | 76 | 19 | 26 | 80.0% | +0.891 | 95 |
| **1.0** | 77 | 11 | 33 | 87.5% | +1.107 | 88 |
| **1.5** | 77 | 4 | 40 | 95.1% | +1.289 | 81 |
| **2.0** | 77 | 2 | 42 | 97.5% | +1.347 | 79 |

**R-unit note:** the `continuation_r` in the CSV is in **OB-body units** (price travelled past entry, divided by `ob_body_size`), NOT in SL-distance units. So the 'Expectancy_R' column above is OB-body-normalized: e.g. +0.5 means winners on average travelled half the OB body past entry before exit. For losers, R = -1.0 in OB-body units is wrong (loser actually loses the SL distance, which is `entry_to_far + m` ATR, NOT 1 OB body). I therefore present a SECOND table below with R expressed in **SL-distance units** (true risk-multiple).

**Table 2A: outcomes re-scored at each SL margin (SL-units = continuation_atr / new_sl_dist_atr), FULL sample**

| SL margin (×ATR) | CONTINUED | REVERSED | UNRESOLVED | WR (ex-UNR) | Mean R (SL-units) | Median R (SL-units) | Resolved |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **0.0** | 39 | 82 | 0 | 32.2% | -0.191 | -1.000 | 121 |
| **0.1** | 67 | 46 | 8 | 59.3% | +1.057 | +0.789 | 113 |
| **0.2** | 68 | 44 | 9 | 60.7% | +0.648 | +0.715 | 112 |
| **0.3** | 69 | 43 | 9 | 61.6% | +0.354 | +0.657 | 112 |
| **0.5** | 75 | 35 | 11 | 68.2% | +2.223 | +0.628 | 110 |
| **0.7** | 76 | 19 | 26 | 80.0% | +0.563 | +0.593 | 95 |
| **1.0** | 77 | 11 | 33 | 87.5% | +0.619 | +0.506 | 88 |
| **1.5** | 77 | 4 | 40 | 95.1% | +0.470 | +0.429 | 81 |
| **2.0** | 77 | 2 | 42 | 97.5% | +0.392 | +0.362 | 79 |

**Caveat on Table 2A:** 13 rows have `entry_to_far_atr < 0` (entry candle wicked through OB → entry sits past far edge). For these, `new_sl_dist = etf + m` is very small or negative for low m, inflating R-units when winners survive. Mean is therefore unstable; use **median** column or the cleaned table below for robust comparison.

**Table 2B: outcomes re-scored, CLEAN sample (drop rows where entry_to_far<0 OR new_sl_dist<0.2 ATR)**

| SL margin (×ATR) | CONTINUED | REVERSED | UNRESOLVED | WR (ex-UNR) | Mean R (SL-units) | Median R (SL-units) | Resolved |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **0.0** | 37 | 68 | 0 | 35.2% | -0.140 | -1.000 | 105 |
| **0.1** | 66 | 34 | 8 | 66.0% | +0.452 | +0.834 | 100 |
| **0.2** | 66 | 33 | 9 | 66.7% | +0.369 | +0.756 | 99 |
| **0.3** | 67 | 32 | 9 | 67.7% | +0.311 | +0.693 | 99 |
| **0.5** | 72 | 25 | 11 | 74.2% | +0.324 | +0.649 | 97 |
| **0.7** | 72 | 11 | 25 | 86.7% | +0.453 | +0.594 | 83 |
| **1.0** | 72 | 4 | 32 | 94.7% | +0.480 | +0.513 | 76 |
| **1.5** | 72 | 3 | 33 | 96.0% | +0.384 | +0.414 | 75 |
| **2.0** | 72 | 2 | 34 | 97.3% | +0.328 | +0.346 | 74 |

**Knee analysis:** I report two knee candidates — by mean SL-units expectancy and by median SL-units expectancy — on the cleaned sample (Table 2B).

- **Knee (mean R, clean):** m = **1.0× ATR**, mean = **+0.480 R**, median = +0.513 R.
- **Knee (median R, clean):** m = **0.1× ATR**, mean = +0.452 R, median = **+0.834 R**.
- **Live system (m=0.5× ATR):** mean = +0.324 R, median = +0.649 R (clean sample).

---

## Recommendations (Actionable)

**1. SL margin (above OB far edge):**
   - Current: 0.5× ATR (Geom A) → 0.5 + median entry-to-far (0.84) = **~1.34× ATR total SL distance from entry**.
   - Winner-MAE p75 = **0.75 ATR**; p90 = **1.06 ATR**; p95 = **1.17 ATR**.
   - Knee from Q5 (clean sample, mean R-units) = **m = 1.0× ATR**; (median R-units) = **m = 0.1× ATR**.
   - Live m=0.5 expectancy = +0.324 R (mean), +0.649 R (median).
   - **Recommendation:** with n=121 small, treat the knee as suggestive only. Going from m=0.5 → m=0.7 (mean R: +0.324 → +0.453) and m=0.5 → m=1.0 (mean R: +0.324 → +0.480) both shows higher expectancy, but the underlying mechanism is partly that more REVERSED rows become UNRESOLVED (we cannot prove them as winners or losers without bar-level data). **Tightening below 0.3× ATR is clearly unfavourable** (median R drops). A reasonable next step: forward-test m=0.7 in shadow mode for 30+ trades.

**2. Penetration is a continuation killer signal — but not absolute:**
   - Of 77 CONTINUED rows, **22 had at least some penetration** (28.6%) — meaning price went BEYOND the far edge yet still resolved as a winner.
   - All 33 REVERSED rows had penetration (mechanically — they hit SL which is past the far edge).
   - **Real-time signal:** if you observe penetration > 1.17× ATR (winner-CONTINUED p95 of penetration when pen>0), the trade has historically essentially never been a winner — consider a tighter manual stop.

**3. Entry placement within the OB:**
   - Median CONTINUED `mae_pct_ob_body` = **55.4%** (price reverses ~55% of the way through the OB body before continuing).
   - p75 = 93.3% | p90 = 144.4%.
   - 15/77 CONTINUED rows had MAE past the far edge (19%).
   - Implication: entries placed deeper in the OB (near far edge) would catch the actual reversal point more often, but require simultaneously tightening SL to maintain risk parity. Net effect must be measured.

**4. Geom B (Test A live-aligned SL) reality:**
   - Geom B used 33 CONTINUED, 35 REVERSED, 53 UNRESOLVED out of 121.
   - Resolved-only WR: 48.5% [37.1, 60.2] (n=68).
   - Geom B SL is much tighter (XAUUSD: 0.1% of OB edge; FX: 0.00015 absolute) → many more UNRESOLVED in 12-candle window.
   - The **53/121 = 43.8% UNRESOLVED rate** for Geom B suggests the 3h horizon is too short for tight-SL geometry. To draw conclusions about live SL, extend horizon or accept the very-short-window limitation.

---

## Limitations & Caveats

1. **Sample size:** n=121 total. Per-symbol n: USDJPY=33, US30=28, XAUUSD=22, GBPJPY=19, GBPUSD=19. GBPJPY and GBPUSD per-symbol stats are below the n>=20 threshold and are reported as 'n too small'.
2. **Skip-entry-candle convention:** the simulator does not check SL/TP on the entry candle (j=0). Penetration/MAE ARE tracked on j=0. My SL sensitivity treats any penetration >= m as a stop-out, which **overstates** stop-out rates for rows where the worst MAE happens on the entry candle wick. 13 CONTINUED rows have time_to_mae=0 — these are the affected rows.
3. **No bar-by-bar data:** I cannot re-simulate looser-SL outcomes precisely. When original was REVERSED and tighter SL would still have been hit, I correctly classify as REVERSED. When original was REVERSED and looser SL would not have been hit, the trade may eventually have hit target OR run out the clock. I conservatively classify as UNRESOLVED.
4. **R-unit ambiguity:** the CSV's `continuation_r` is in **OB-body units**, not SL-distance units. I converted to SL-units in Table 2 of Q5 to enable apples-to-apples comparison across SL margins.
5. **Geom A target is fixed (entry + 1×ob_body), not 1R or 1.5R relative to SL.** So tightening SL improves the target/risk ratio AS WELL AS killing some winners — net effect on expectancy is non-trivial.
6. **Sessions field has 7 NaN.** I did not stratify by session because session is not the focus of these questions.
7. **Side imbalance:** 88 long vs 33 short. Per-side analysis not requested but stratified results may differ.
8. **Validation set (n=726) NOT used for primary numbers.** Schema differs (different SL/target rules); used only for sanity checks.

---

## Methodological Choices (for cross-comparison with distrib_a)

**Outcome-name convention:** I use `CONTINUED ≡ WIN`, `REVERSED ≡ LOSS`, `UNRESOLVED ≡ unknown` throughout. Where the prompt said 'WIN' I queried `outcome_a == 'CONTINUED'`.

**Wilson 95% CI:** used `scipy.stats.norm.ppf(0.975)` with the Wilson score formula `(p + z²/2n ± z·sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n)`.

**`entry_to_far_atr` derivation:** inverted the Geom A SL formula. For long: `(entry - sl_a)/ATR - 0.5`. For short: `(sl_a - entry)/ATR - 0.5`. Verified against `mae - penetration` (where pen > 0); diffs all < 0.004 ATR (rounding).

**SL re-scoring rule (final):** `stopped_under_m ≡ penetration_atr >= m`, **with skip-entry-candle exception**: if original CONTINUED AND `time_to_mae == 0`, the worst penetration registered on the entry candle (j=0). The simulator's SL/TP check skips j=0; preserve CONTINUED. For other CONTINUED rows: if `time_to_mae < time_to_continuation`, flip to REVERSED. REVERSED stays REVERSED. UNRESOLVED with high penetration → REVERSED. For looser m: REVERSED with `penetration_atr < m` (wouldn't have been stopped) → UNRESOLVED (cannot prove target hit without bar-level data). This **understates** wins for looser SL — conservative direction.

**Verification of SL re-scoring at m=0.5 (sanity check):** my rescore at m=0.5 produces 75 CONT / 35 REV / 11 UNR; actual is 77 CONT / 33 REV / 11 UNR. The 2-row delta is rows 66 and 75 — both have `entry_to_far_atr < -0.5`, so my edge-case rule (new_sl_dist <= 0 → REVERSED) misclassifies them. These 2 rows are dropped in Table 2B (clean sample), where the rescore matches actual outcomes exactly.

**Bin choice for Q4:** `[<0, 0-25, 25-50, 50-75, 75-100, 100-125, 125-150, 150-200, >200]` percent of OB body. Added 150-200 bin because the upper tail is heavy.

**Mann-Whitney U test (Q2):** one-sided, alternative = winner MAE less than loser MAE. Used as sanity (the answer is mechanically yes by construction; p-value sanity-checks the data).

**No fabrication / no extrapolation beyond data:** every reported number traces to the CSV. If a question can't be answered cleanly, I said so explicitly (Q5 caveats).
