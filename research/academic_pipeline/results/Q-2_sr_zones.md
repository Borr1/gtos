# Q-2 S/R zones — round numbers, PDH/PDL, premium/discount

*Generated:* 2026-04-17T01:52:15+00:00

## Hypothesis (pre-registered)

**Q-2.3a (round numbers):** WR within 0.5 ATR of a $5 round level == WR elsewhere. Alt: difference >= +5pp.

**Q-2.3b (PDH/PDL):** WR within 0.5 ATR of PDH or PDL == WR elsewhere. Alt: difference >= +5pp.

**Q-2.3c (directional alignment near PDH/PDL):** WR of long-near-PDL / short-near-PDH ("sweep-and-retest") == WR of long-near-PDH / short-near-PDL ("against"). Alt: >= +5pp.

**Q-2.7a (premium/discount):** Kruskal-Wallis on r_multiple across {discount, neutral, premium}; directional alignment (long-in-discount or short-in-premium) vs against-range WR >= +5pp.

## Pre-registration disclosure (reviewer correction, 2026-04-17)

**Disclosure:** The round-number analysis in §Q-2.3a explores **multiple grids ($5, $10, $25, $50) at multiple proximity thresholds (0.10, 0.25, 0.50 ATR)** and the directional-alignment sub-analyses (Q-2.3c, Q-2.7 aligned-vs-against) were **not pre-registered prior to data inspection**. The grid selection was iterative: the $5/0.5-ATR spec was degenerate (every trade classified as 'near'), so the search migrated to wider grids and tighter proximities until non-degenerate partitions emerged. This is a **multiple-comparison / HARKing hazard** under the terminology of Kerr (1998). The original report presented effect sizes and p-values at face value without correction, which is **not valid** as a formal hypothesis test.

**Corrected family size:** The analysis space is **8 grid cells** (4 grids × 2 proximity thresholds examined per grid, including the spec $5/0.5-ATR cell and the $10/$25/$50 combinations reported) × **2 directional interpretations per cell** (delta WR can favour 'near' or 'far', both were inspected) = **16 family-wise comparisons**.

- Bonferroni-corrected α at family-wise 0.05 level: **α = 0.05 / 16 = 0.003125**.
- None of the Q-2.3 round-number grid results reach this threshold:

| grid / proximity | delta WR | Fisher p | Corrected α=0.003125 |
|---|---|---|---|
| $5 / 0.5 ATR | degenerate | n/a | n/a |
| $10 / 0.10 ATR | +0.028 | 0.7973 | FAIL |
| $25 / 0.25 ATR | +0.009 | 1.0000 | FAIL |
| $50 / 0.25 ATR | +0.060 | 0.5516 | FAIL |

- Q-2.3b (PDH/PDL near-vs-far): Fisher p = 0.2035 -> **FAIL corrected threshold**.
- Q-2.3c directional alignment: Fisher p = 0.1024 -> **FAIL corrected threshold**.
- Q-2.7a discount/neutral/premium Kruskal-Wallis: p = 0.6133 -> **FAIL corrected threshold**.
- Q-2.7 with-range vs against-range: Fisher p = 0.1165 -> **FAIL corrected threshold**.

**Procedural consequence:** no finding in Q-2 survives family-wise multiple-comparison correction. The directional-flip discussion that followed the main results is reframed below as an **observation requiring prospective replication**, not as an actionable signal.

## Data

- Trades source: `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base_backtest\analysis\unified_trades_v2_20260331.json` — 111 records, 110 with valid entry_price/direction/r_multiple.
- All trades are XAUUSD (entry-price heuristic 2254–5580, trade_id prefix `bt_` is symbol-agnostic).
- OHLCV: `C:\Users\MSI\Documents\ai-trading-agent\data\historical\XAUUSD_D1.csv` (D1 2023-04 to 2026-03, 772 bars) and `C:\Users\MSI\Documents\ai-trading-agent\data\historical\XAUUSD_H4.csv` (H4, 4629 bars). These cover the full trade window (unlike `data/historical_2026/` which is 2026-only).
- Enriched trades used in analysis: **110** (missing D1 context skipped: 0).
- ATR: Wilder 14-period on D1, measured on the D1 bar preceding the trade (or most recent D1 bar before the trade date for weekend entries).
- PDH/PDL: high/low of the D1 bar immediately preceding the trade's D1 bar.
- H4 range: low/high over the 5 H4 bars immediately before the trade date (approximation — trade entry timestamps are not in the dataset, so we use prior-day H4 context, not intraday).
- Round-number step: $5.00 for XAUUSD.
- SciPy available: True

## Method

For each trade, compute (a) absolute distance from entry to nearest $5 round level in ATR units, (b) absolute distance from entry to PDH and to PDL in ATR units, (c) position of entry inside the prior-5-H4 range (0 = at low/discount, 1 = at high/premium). Bucket and compare WR, mean R, and distribution (Mann-Whitney / Fisher).

Proximity threshold: 0.5 ATR (task spec). Premium/discount cuts: < 0.3, 0.3-0.7, > 0.7 (task spec).

## Q-2.3 Results

### (a) Round-number proximity

Task spec asks for $5 grid at 0.5 ATR. On XAUUSD, D1 ATR (median $36) makes 0.5 ATR span several $5-steps and every trade registers as 'near'. We report the degenerate spec cut for completeness, then run wider grids ($10/$25/$50) with tighter proximity. Primary verdict uses the $50-grid / 0.25-ATR split (non-degenerate and where round-figure clustering is strongest on gold).

| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| $5 grid, <=0.5 ATR (spec) | 110 | 0.655 | +0.198 | +0.160 | no |
| $5 grid, >0.5 ATR (spec) | 0 | - | - | - | yes |


| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| $10 grid, <=0.10 ATR (primary) | 91 | 0.659 | +0.199 | +0.160 | no |
| $10 grid, >0.10 ATR | 19 | 0.632 | +0.195 | +0.150 | no |

- Fisher's exact ($10 grid, near vs far): WR 0.659 vs 0.632 (delta +0.028), Fisher p = 0.7973.
- Mann-Whitney on r_multiple ($10 grid): p = 0.9080, mean_R delta +0.003.

| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| $25 grid, <=0.25 ATR | 93 | 0.656 | +0.156 | +0.190 | no |
| $25 grid, >0.25 ATR | 17 | 0.647 | +0.426 | +0.120 | no |

- Fisher's exact ($25 grid): WR 0.656 vs 0.647 (delta +0.009), Fisher p = 1.0000.

| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| $50 grid, <=0.25 ATR | 54 | 0.685 | +0.364 | +0.230 | no |
| $50 grid, >0.25 ATR | 56 | 0.625 | +0.038 | +0.140 | no |

- Fisher's exact ($50 grid): WR 0.685 vs 0.625 (delta +0.060), Fisher p = 0.5516.

### (b) PDH/PDL proximity (nearer of the two)

| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| near PDH or PDL (<= 0.5 ATR) | 89 | 0.685 | +0.227 | +0.160 | no |
| far (> 0.5 ATR) | 21 | 0.524 | +0.074 | +0.090 | no |

- Fisher's exact (near vs far): WR 0.685 vs 0.524 (delta +0.162), Fisher p = 0.2035.
- Mann-Whitney on r_multiple: p = 0.5348, mean_R delta +0.153.

### (c) Directional alignment near PDH/PDL

| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| aligned (long@PDL / short@PDH) | 33 | 0.576 | +0.117 | +0.110 | no |
| against (long@PDH / short@PDL) | 56 | 0.750 | +0.292 | +0.160 | no |

- Fisher's exact (aligned vs against): WR 0.576 vs 0.750 (delta -0.174), Fisher p = 0.1024.
- Mann-Whitney on r_multiple: p = 0.4466, mean_R delta -0.175.

## Q-2.7 Results

### Premium / discount bucketing

| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| discount (<0.3) | 19 | 0.579 | +0.292 | +0.200 | no |
| neutral (0.3-0.7) | 27 | 0.481 | -0.010 | +0.000 | no |
| premium (>0.7) | 64 | 0.750 | +0.258 | +0.160 | no |

- Kruskal-Wallis on r_multiple across three buckets: p = 0.6133

### Directional alignment (SMC with/against-range)

| bucket | n | WR | mean R | median R | underpowered? |
|---|---|---|---|---|---|
| with range (long@discount or short@premium) | 24 | 0.583 | +0.177 | +0.110 | no |
| against range (long@premium or short@discount) | 59 | 0.763 | +0.302 | +0.160 | no |

- Fisher's exact (with vs against range): WR 0.583 vs 0.763 (delta -0.179), Fisher p = 0.1165.
- Mann-Whitney on r_multiple: p = 0.4618, mean_R delta -0.125.

## Verdicts (corrected for multiple comparisons, α = 0.003125)

**Q-2.3a round-number proximity:** **KILL / INCONCLUSIVE** — none of the four grid variants reach family-wise α. Largest point effect was $50-grid delta WR +0.060 (p=0.5516); even uncorrected this is not significant at α=0.05.

**Q-2.3b PDH/PDL proximity:** **KILL / INCONCLUSIVE** — WR 0.685 vs 0.524 (delta +0.162, p=0.2035). Fails corrected threshold; would not even reach uncorrected α=0.05.

**Q-2.3c directional alignment near PDH/PDL:** **INCONCLUSIVE (exploratory observation only)** — WR 0.576 vs 0.750 (delta -0.174, p=0.1024). Fails corrected threshold. The -17pp point estimate is large but the test was not pre-registered and the sub-bucket search space was large; treat as an exploratory observation that **requires prospective replication on out-of-sample trades** before any action.

**Q-2.7a premium/discount (directional):** **INCONCLUSIVE (exploratory observation only)** — WR 0.583 vs 0.763 (delta -0.179, p=0.1165). Fails corrected threshold. Same caveats as Q-2.3c.

### Directional-flip observation (re-framed)

A -17pp delta between 'aligned with SMC textbook' (long@PDL / short@PDH) and 'against textbook' (long@PDH / short@PDL) appears in both the PDH/PDL and premium/discount analyses. **This was not a pre-registered hypothesis** — it was noticed AFTER the main grids produced null results. The pattern should be read as:

- **Observation** (not finding): in this batch of 111 trades, entries that an SMC purist would call 'wrong-way' performed better on WR and mean R than entries they would call 'textbook sweep-and-retest'.
- **Possible explanation**: the OB-retest framework deliberately places entries AFTER BOS, meaning 'long near PDH' is typically a continuation entry on a bullish break, not a fade. The textbook-SMC label misclassifies the entry condition.
- **Why this is not a finding**: (a) not pre-registered; (b) p-values do not reach either uncorrected α=0.05 or corrected α=0.003125; (c) sample n=89 is below the 130+ needed to detect a -17pp effect at 80% power; (d) the explanation is post-hoc.
- **What to do with it**: log a prospective shadow test — for the next 50 T7 live trades, classify each by SMC textbook vs continuation, compare WR. If the direction holds across an independent sample, re-evaluate. Until then, **no filter changes**.

Rationalisations of the form "fade the zone works for GTOS because the edge is continuation-driven" are removed from this report — they were post-hoc narratives on underpowered data.

## Caveats

- **All trades XAUUSD** — cross-instrument generalisation untested here (no US30/JPY-pair trades in the batch file).
- **Single-instrument sample n ~= 110** after context filtering; sub-buckets can drop below 15 and are flagged underpowered.
- **H4 range uses prior-day 5-bar window**, not intraday at the actual entry time. Unified trade records store only the trade date, not an entry timestamp, so we can't tighten this without separate tick/M15 reconstruction.
- **ATR is D1 Wilder 14** on the prior D1 bar. Intraday ATR (e.g. H4 or M15) would give tighter proximity thresholds but is noisier.
- **Round-number grid fixed at $5** per task spec. $10 and $25 grids may show different clustering (literature: Osler 2003 — round-figure clustering of stop/limit orders).
- **Correlated with entry OB**: the OB-retest framework may already concentrate entries near PDH/PDL (impulse origins often break prior daily extremes). Any observed confirming signal partly restates the OB edge.
- **Multiple-testing correction applied (reviewer fix 2026-04-17):** 16-way family-wise Bonferroni α = 0.003125. No result survives. See the "Pre-registration disclosure" section at the top of this report.

## Next steps

- If any bucket shows |delta-WR| >= 5pp AND n >= 30 AND p < 0.05 uncorrected, escalate to a prospective shadow gate (log-only, min. 30 trades before promotion).
- Cross-instrument sanity check: rerun on per-instrument batch files when available (US30/JPY-pairs). The current dataset cannot test H2.3/2.7 outside XAUUSD.
- Reconstruct per-trade entry timestamps from pipeline_state/ so H4 range can be computed at entry candle close rather than prior-day approximation.
- Consider wider proximity threshold (0.25 ATR / 1.0 ATR) and alternative round grids ($10, $25, $50) as robustness checks.
