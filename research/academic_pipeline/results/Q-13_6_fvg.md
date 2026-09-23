# Q-13.6 — FVG / Liquidity-Void Characterization on XAUUSD (M15 + H1)

**Status:** PRE-REGISTERED (hypothesis written before any data inspection)
**Date:** 2026-04-17
**Analyst:** GTOS Research Agent (Wave 3, $0 local)
**Data:** `data/historical_2026/XAUUSD_M15.csv` + `data/historical_2026/XAUUSD_H1.csv` (Jan 2 – Apr 10 2026)
**Script:** `research/academic_pipeline/scripts/q_13_6_fvg.py`

---

## 1. Hypotheses (PRE-REGISTERED — written before any data inspection)

### Primary research questions
- **Q-2.4:** What is the raw formation rate and fill rate of M15 FVGs on XAUUSD? Characterize gap size distribution, time-to-fill, continuation-before-fill, and fill horizons.
- **Q-13.6:** Do FVGs adjacent to an OB retest (OB-ADJACENT) or formed inside a displacement impulse (IMPULSE-FVG) have different fill/continuation patterns than ISOLATED FVGs?

### FVG classes (pre-registered, disjoint-allowed — a gap may appear in multiple classes)
- **ISOLATED:** no detected OB within a +/-10 candle window around the FVG formation candle.
- **OB-ADJACENT:** at least one detected OB whose formation_index is within +/-10 candles of the FVG formation candle.
- **IMPULSE-FVG:** the FVG gap-candle (candle i, the middle of the 3-candle pattern) has a range `(high - low) >= 1.5 * ATR14(at i-1)`. Uses the same 1.5x ratio already used by `detect_structure_breaks` for `displacement_present`.

A single FVG can be both OB-ADJACENT and IMPULSE-FVG. For the headline comparisons, the non-overlapping contrast is IMPULSE-FVG vs ISOLATED-only (FVGs that are neither OB-ADJACENT nor IMPULSE).

### H0 (null)
Fill behaviour is driven by mean-reversion + volatility alone; the subclass labels add no information. Specifically:
1. Fill rate at horizon h is equal across ISOLATED, OB-ADJACENT, IMPULSE-FVG within +/-5pp.
2. Median time-to-fill is within +/-2 candles across classes.
3. Continuation-before-fill (measured in ATR units) is within +/-0.5 ATR across classes.

### H1 (alternative — pre-registered threshold for PROMOTE)
1. **IMPULSE-FVG fill rate at 50-candle horizon >= 60%** (vs null 50%) on M15.
2. **Difference (IMPULSE-FVG - ISOLATED) >= +10pp** at the 50-candle horizon on M15.
3. Both of the above must also appear with consistent sign (same direction) on H1 with at least n >= 30 per class on H1.

### Pre-registered decision rule
- **PROMOTE** (shadow log feature on M15 + H1): all three H1 conditions met AND two-proportion z-test p < 0.025 (Bonferroni = 0.05 / 2 timeframes).
- **SHADOW** (log-only, do NOT wire): 50-horizon fill rate >= 55% for IMPULSE-FVG and delta vs ISOLATED >= +5pp on M15, even if H1 fails.
- **KILL**: fill rate differences < +5pp, or IMPULSE-FVG fill rate < 55% at h=50.
- **INSUFFICIENT_DATA**: n(class) < 20 on M15 OR n(class) < 10 on H1.

### Directional prior (stated before looking)
I expect:
- Most M15 FVGs are small (< 0.5 ATR), filled quickly (< 10 candles), and statistically uninteresting.
- IMPULSE-FVG will have the longest continuation-before-fill because the impulse candle often precedes a BOS and the gap persists into the next swing. Fill rate at h=50 may be ~65-75% — large gaps, by definition, require retrace but also persist longer.
- OB-ADJACENT FVGs will mostly overlap with IMPULSE-FVG. Their "extra edge" above impulse will be small (<= +3pp). This is why I flag the corroboration/novelty distinction up front.
- ISOLATED FVGs should fill fastest and show minimal continuation.

### Corroboration vs novelty disclosure
Pre-existing GTOS research states that "FVG in impulse" adds +7-20pp WR across 6 instruments (CLAUDE.md, Validated Numbers table). That finding is about **trade outcomes** (WR conditional on entries taken near an FVG inside an impulse). This study instead characterizes **raw fill / continuation behaviour of FVGs as structural objects**, independent of any entry mechanism. If the IMPULSE-FVG class shows a high fill rate with long continuation-before-fill, it CORROBORATES the prior at the structural layer (same physical pattern, same direction). If the IMPULSE-FVG class shows high fill rate WITHOUT long continuation, the prior WR-lift has a different explanation. Either way, the test here is orthogonal to the prior trade-outcome test and cannot by itself "double-count" evidence.

### Multiple-testing correction
- Primary tests: fill-rate at h=20, 50, 100 × 3 classes × 2 timeframes = 18 cells, but the *hypothesis-level* test is a single two-proportion z-test at h=50 on (IMPULSE-FVG vs ISOLATED) per timeframe. **Bonferroni divisor = 2** (M15 and H1).
- Secondary / exploratory tests (gap-size distribution, time-to-fill medians, OB-ADJACENT splits) reported but flagged explicitly as NOT meeting the promotion threshold regardless of p-value.

### What I will NOT do (pre-registered discipline)
- I will NOT choose the "best" horizon after looking. Only h=20, 50, 100 are pre-registered; 50 is the primary.
- I will NOT swap the ATR lookback (14 M15 / 14 H1) after seeing results.
- I will NOT relax the 1.5 ATR impulse definition.
- I will NOT re-classify ISOLATED vs OB-ADJACENT based on a different window than +/-10 candles.
- I will NOT report a verdict if n(class) < 20 on M15 or n(class) < 10 on H1.

### Agent reliability note
Per CLAUDE.md Agent Reliability Rules, all numbers in sections 2+ below are computed by the committed script. "File not found" or "insufficient sample" will be reported verbatim, not fabricated. No financial or deployment decision is made here — the verdict is a conditional gate, not a recommendation.

---

*Sections 2+ below are computed from the committed script. Section 1 is frozen after writing.*

## 2. Data audit

- M15 candles: **6420** (2026-01-02 01:00:00 -> 2026-04-10 23:45:00)
- H1 candles: **1606** (2026-01-02 01:00:00 -> 2026-04-10 23:00:00)
- Generated: 2026-04-17T02:31:13.736874+00:00
- Script: `research/academic_pipeline/scripts/q_13_6_fvg.py`

## M15 — raw population

- Candles loaded: **6420** (2026-01-02 01:00:00 -> 2026-04-10 23:45:00)
- FVGs detected: **1363** (762 bull, 601 bear)
- Formation rate: **0.212** FVGs/candle (1 FVG every 4.7 candles)
- IMPULSE-FVG count: **480** (35.2% of all FVGs)
- OB-ADJACENT count: **973** (71.4% of all FVGs)
- ISOLATED-only (neither OB-adj nor impulse): **239** (17.5% of all FVGs)

### Gap size (gap / ATR14 at candle i-1)

| Subset | n | mean | median | p25 | p75 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| all FVGs | 1361 | 0.46 | 0.28 | 0.11 | 0.55 | 0.00 | 8.61 |
| IMPULSE-FVG | 480 | 0.79 | 0.56 | 0.27 | 0.95 | 0.00 | 8.61 |
| ISOLATED-only | 239 | 0.24 | 0.18 | 0.07 | 0.36 | 0.00 | 2.10 |

### Fill rate by horizon (candles after FVG formation)

| Subset | n | h=20 | 95% CI | h=50 (PRIMARY) | 95% CI | h=100 | 95% CI |
|---|---:|---:|:---:|---:|:---:|---:|:---:|
| all FVGs | 1363 | 84.7% | [82.7% - 86.6%] | 89.7% | [87.9% - 91.2%] | 91.6% | [90.0% - 93.0%] |
| IMPULSE-FVG | 480 | 84.8% | [81.3% - 87.7%] | 89.6% | [86.5% - 92.0%] | 92.3% | [89.6% - 94.4%] |
| ISOLATED-only | 239 | 84.1% | [78.9% - 88.2%] | 90.4% | [86.0% - 93.5%] | 91.2% | [86.9% - 94.2%] |
| OB-ADJACENT | 973 | 85.0% | [82.6% - 87.1%] | 89.5% | [87.4% - 91.3%] | 92.0% | [90.1% - 93.5%] |

### Time-to-fill (candles, FILLED FVGs only)

| Subset | n | mean | median | p25 | p75 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| all filled FVGs | 1335 | 59.94 | 2.00 | 1.00 | 7.00 | 1.00 | 5082.00 |
| IMPULSE-FVG filled | 467 | 50.09 | 2.00 | 1.00 | 6.00 | 1.00 | 5046.00 |
| ISOLATED-only filled | 230 | 37.36 | 2.00 | 1.00 | 8.75 | 1.00 | 1910.00 |

### Continuation-before-fill (max impulse-direction move in ATR units)

| Subset | n | mean | median | p25 | p75 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| IMPULSE-FVG | 480 | 7.45 | 1.49 | 0.77 | 3.13 | 0.00 | 188.55 |
| ISOLATED-only | 239 | 5.83 | 1.15 | 0.52 | 2.73 | 0.00 | 173.06 |

### Primary test: IMPULSE-FVG vs ISOLATED-only fill rate at h=50

- Delta (IMPULSE - ISOLATED): **-0.8pp**
- Two-proportion z-test p-value: **0.7401**
- Bonferroni-adjusted alpha (2 timeframes): 0.025 — not significant

## H1 — raw population

- Candles loaded: **1606** (2026-01-02 01:00:00 -> 2026-04-10 23:00:00)
- FVGs detected: **319** (187 bull, 132 bear)
- Formation rate: **0.199** FVGs/candle (1 FVG every 5.0 candles)
- IMPULSE-FVG count: **114** (35.7% of all FVGs)
- OB-ADJACENT count: **223** (69.9% of all FVGs)
- ISOLATED-only (neither OB-adj nor impulse): **54** (16.9% of all FVGs)

### Gap size (gap / ATR14 at candle i-1)

| Subset | n | mean | median | p25 | p75 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| all FVGs | 317 | 0.49 | 0.26 | 0.11 | 0.66 | 0.00 | 3.67 |
| IMPULSE-FVG | 114 | 0.90 | 0.77 | 0.35 | 1.25 | 0.01 | 3.67 |
| ISOLATED-only | 52 | 0.22 | 0.13 | 0.06 | 0.33 | 0.00 | 0.84 |

### Fill rate by horizon (candles after FVG formation)

| Subset | n | h=20 | 95% CI | h=50 (PRIMARY) | 95% CI | h=100 | 95% CI |
|---|---:|---:|:---:|---:|:---:|---:|:---:|
| all FVGs | 319 | 81.8% | [77.2% - 85.7%] | 87.5% | [83.4% - 90.7%] | 88.7% | [84.8% - 91.7%] |
| IMPULSE-FVG | 114 | 79.8% | [71.5% - 86.2%] | 84.2% | [76.4% - 89.8%] | 84.2% | [76.4% - 89.8%] |
| ISOLATED-only | 54 | 90.7% | [80.1% - 96.0%] | 92.6% | [82.4% - 97.1%] | 92.6% | [82.4% - 97.1%] |
| OB-ADJACENT | 223 | 80.7% | [75.0% - 85.4%] | 87.9% | [83.0% - 91.5%] | 89.7% | [85.0% - 93.0%] |

### Time-to-fill (candles, FILLED FVGs only)

| Subset | n | mean | median | p25 | p75 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| all filled FVGs | 307 | 38.58 | 2.00 | 1.00 | 7.00 | 1.00 | 1264.00 |
| IMPULSE-FVG filled | 106 | 34.28 | 2.00 | 1.00 | 7.75 | 1.00 | 1262.00 |
| ISOLATED-only filled | 52 | 18.21 | 2.00 | 1.00 | 3.25 | 1.00 | 478.00 |

### Continuation-before-fill (max impulse-direction move in ATR units)

| Subset | n | mean | median | p25 | p75 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| IMPULSE-FVG | 114 | 9.01 | 1.46 | 0.73 | 3.89 | 0.11 | 96.38 |
| ISOLATED-only | 54 | 2.31 | 0.89 | 0.53 | 1.61 | 0.00 | 29.18 |

### Primary test: IMPULSE-FVG vs ISOLATED-only fill rate at h=50

- Delta (IMPULSE - ISOLATED): **-8.4pp**
- Two-proportion z-test p-value: **0.1326**
- Bonferroni-adjusted alpha (2 timeframes): 0.025 — not significant

## Verdict (pre-registered gate)

- **Result label:** **KILL**
- Bonferroni-adjusted alpha: 0.025
- Sample size gate M15 (n>=20 each class): pass (n_impulse=480, n_isolated=239)
- Sample size gate H1 (n>=10 each class): pass (n_impulse=114, n_isolated=54)
- H1 sign matches M15: True

### Per-timeframe test summary

| TF | IMPULSE fill h=50 | ISOLATED fill h=50 | Delta (pp) | p-value | n_imp | n_iso |
|---|---:|---:|---:|---:|---:|---:|
| M15 | 89.6% | 90.4% | -0.8 | 0.7401 | 480 | 239 |
| H1 | 84.2% | 92.6% | -8.4 | 0.1326 | 114 | 54 |

### Verdict rules applied

- PROMOTE: n sufficient on both TFs AND IMPULSE fill h=50 >= 60% on BOTH AND delta >= +10pp on BOTH AND p < 0.025 on BOTH AND H1 sign matches M15.
- SHADOW: M15 IMPULSE fill h=50 >= 55% AND delta >= +5pp on M15, but PROMOTE conditions not all met.
- KILL: neither PROMOTE nor SHADOW triggered and samples sufficient.
- INSUFFICIENT_DATA: n-class gates failed on either TF.

## Overlap disclosure — corroboration vs novelty

The prior GTOS finding is **'FVG-in-impulse' adds +7-20pp WR across 6 instruments** (CLAUDE.md Validated Numbers table, entry-signal level). The present study tests the **structural** property — raw fill rate and continuation of FVGs as objects on the chart, independent of any trade decision. The two measurements are orthogonal: a high structural fill rate can coexist with a low trade WR (and vice versa), since the trade result also depends on entry price, SL, and TP mechanics that are not modelled here.

Statements below mark each primary finding as CORROBORATION or NOVEL:

- **M15:** IMPULSE fill h=50 = 89.6% vs ISOLATED 90.4%, median continuation IMPULSE = 1.49 ATR vs ISOLATED 1.15 ATR. Does NOT corroborate the structural version of the prior on this TF — the prior is about trade WR not fill rate, so this is consistent but not supportive.
- **H1:** IMPULSE fill h=50 = 84.2% vs ISOLATED 92.6%, median continuation IMPULSE = 1.46 ATR vs ISOLATED 0.89 ATR. Does NOT corroborate the structural version of the prior on this TF — the prior is about trade WR not fill rate, so this is consistent but not supportive.

## Caveats

1. **Single instrument, single window.** XAUUSD only, Jan 2 -> Apr 10 2026 (~100 trading days). M15 ~6420 candles, H1 ~1606 candles. Fills at h=100 require the FVG to form at least 100 candles before the end of the window — late-window FVGs are right-censored (treated as unfilled at the far horizon if no fill has yet occurred). A Kaplan-Meier treatment would be cleaner; we report the simple cumulative rate.

2. **FVG definition chosen to match production.** We use the `identify_fvgs` indices (i-1, i, i+1) from `src/components/market_state.py`. The task brief described the pattern with indices (i-2, i), which is operationally equivalent (the gap candle is the middle candle; the brief's notation swaps the anchor). We document the mapping and honour the production convention.

3. **Impulse threshold is a single 1.5x ATR rule.** Chosen to match `detect_structure_breaks` `displacement_present`. Not swept. An impulse candle is an object-level property of candle i; the FVG itself is defined by i-1 and i+1. A gap can exist without the middle candle being an impulse, and an impulse candle may leave no gap.

4. **OB-ADJACENCY window is +/-10 candles.** Not swept. Corresponds to the production back-walk distance in `identify_order_blocks` (10-candle lookback from the break). Different windows would change the ISOLATED vs OB-ADJACENT split.

5. **Fill = any wick overlap.** A bull FVG is "filled" the first time a candle's low <= top of the gap. Some traders require body-based fill or 50% midpoint fill. We use wick-based because it is the most permissive (gives the highest fill rate) — any stricter rule would only make the comparisons more conservative.

6. **Continuation-before-fill can be zero.** If the first post-pattern candle wicks straight back into the gap, continuation_atr = 0 even for a formally-flagged IMPULSE-FVG. This is correct and reflects real behaviour.

7. **Multiple-testing.** Only h=50 is primary; h=20 and h=100 are descriptive. Bonferroni divisor = 2 (M15 and H1). All secondary tests (gap-size distribution, time-to-fill medians, OB-ADJACENT fill rates) are exploratory and do NOT meet the promotion threshold no matter the p-value.

8. **Right-censoring of continuation metric.** `continuation_atr` is measured from candle i+2 until fill, or until end-of-data. Unfilled FVGs have their continuation measured over whatever remaining candles exist. This may bias ISOLATED / fast-fill FVGs' max continuation downward relative to IMPULSE / long-persist FVGs.

9. **Not a trade edge test.** High fill rate with large continuation-before-fill is a necessary but not sufficient condition for an entry-signal edge. This study does not implement SL/TP/spread/slippage, so no PnL or WR is computed.

10. **No API calls.** Local analysis only.

## Next steps

1. **If verdict is PROMOTE or SHADOW:** add an observation-only shadow logger for detected M15 FVGs (formation time, side, gap_size_pct_atr, is_impulse, is_ob_adjacent, fill outcome at h=50). Mirror the existing `proximity_shadow_logger.py` pattern. At least 30 trades worth of post-deployment data before any trading-logic change is proposed (per CLAUDE.md).

2. **If verdict is KILL:** record the test outcome and deprioritise FVG structural classification as an entry feature. The prior +7-20pp WR-lift finding stands on its own (trade-outcome measurement) but is not corroborated at the structural fill-rate layer.

3. **Extend to other instruments.** The Validated Numbers +7-20pp figure is cross-instrument (6 symbols). Running this exact script on USDJPY, GBPJPY, GBPUSD, US30 requires only swapping the CSV paths and rerunning. Bonferroni divisor becomes 2 x 5 = 10.

4. **Sensitivity analyses that are allowed under the pre-registered rules:**
   - Different ATR lookback (21, 50) — separately reported, not replacing primary.
   - Different impulse threshold (1.25, 1.75, 2.0 ATR) — sweep, report the full curve, do not cherry-pick.
   - Body-based fill rule vs wick-based — robustness check.

5. **What would require new pre-registration:** any re-classification scheme (e.g. "high-impulse FVG" = 2.5 ATR), any different horizon set, any subset of the sample by session or regime.

