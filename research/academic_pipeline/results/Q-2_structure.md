# Q-2 Structure Detection Analysis

**Generated:** 2026-04-17T01:53:42.269502+00:00
**H1 source:** `data/historical_2026/XAUUSD_H1.csv` (Jan 2 - Apr 10, 2026)
**Batch source:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n=111)
**Analysis scope:** XAUUSD (batch is XAUUSD-only; H1/M15 from historical_2026/)

## Hypothesis (pre-data)

Stated before opening the outcome distributions:

- **H-2.1 (null):** No swing-detection algorithm significantly beats fixed-lookback min_bars=2 at predicting 6-candle continuation at p<0.05 Bonferroni-adjusted across algorithms tested. Rationale: the GTOS edge is OB zone-based, not swing-frequency based (Test A rerun result, +17pp). Changing swing grammar changes *which* OBs we detect but not the underlying mean-reversion mechanism.
- **H-2.6 (alt):** `displacement_quality` does NOT strongly predict WR in the 111-trade batch. Prior T3 KILLED H1 `h1_last_break_disp` and M15 `displacement_ratio` at n=121 with Bonferroni-adjusted p>0.01. CEO flagged for revival because prior ran on Phase 1-2 broken system. If WR spread across displacement levels remains <=5pp or chi-square p>0.05, confirm KILL. Otherwise promote as shadow.

## Data

- H1 candles: **1606** (XAUUSD, 2026-01-02 01:00:00 -> 2026-04-10 23:00:00).
- M15 candles: **6420** (XAUUSD, 2026-01-02 01:00:00 -> 2026-04-10 23:45:00).
- Batch trades: **111** (2024-04-01 to 2026-03-13).
- Batch displacement_quality distribution: {'strong': 105, 'weak': 1, 'medium': 5}
- Batch outcome distribution: {'LOSS': 36, 'WIN': 72, 'BREAKEVEN': 3}

## Method

**Q-2.1 swing algorithms:**
- A (fixed-lookback): market_state.detect_swings min_bars=2 (current production).
- B (directional-change): Guillaume et al. 1997, thresholds theta in {0.1%, 0.3%, 0.5%, 1.0%}.
- C (Bry-Boschan light): 5-period local peak/trough, filter to alternation + min cycle >=5.

**Q-2.1 evaluation metric:** 6-candle forward continuation rate.
For a detected swing_LOW at index i, a 'win' = close[i+6] > swing.price (bullish continuation from the trough).
For a detected swing_HIGH at index i, a 'win' = close[i+6] < swing.price.
This tests the directional signal the swing carries: does price continue away from the extreme or revert?
Two-proportion z-test vs the fixed-lookback baseline; chi-square across all algorithms; Bonferroni alpha=0.05/6.

**Q-2.6 displacement:**
Primary: categorical `displacement_quality` ('weak' / 'medium' / 'strong') already in batch JSON.
Secondary (feasibility): reconstructed impulse magnitude (max(high)-min(low) across the 10 M15 candles prior to entry) / ATR14(M15). Batch dates 2024-04-01 to 2026-03-13; M15 CSV 2026-01-02 onwards -> only ~2 months of trades reconstructable. Honest reconstruction, no fabrication for out-of-range trades.

## Q-2.1 Algorithm comparison

### Swing counts / amplitude / 6-candle continuation (look-ahead-free)

**Fairness note on detection delay:** a swing is only confirmable in live trading after a lag characteristic of the algorithm. We compute continuation as `close[swing_idx + delay + 6] vs swing.price` so that no algorithm benefits from reading the future.
- A fixed-lookback min_bars=2: delay = 2 candles (swing confirmed 2 bars after formation)
- B directional-change: delay = 0 (DC tags a swing exactly when the reversal threshold is breached; already causal)
- C Bry-Boschan light w=5: delay = 5 (peak confirmed only after 5 bars without a higher high)

Without this adjustment, BB-light's 'alternation enforced' filter produces a selection-bias win rate (~99%) because only swings followed by a real alternation survive the filter. The delay-adjusted metric is the fair comparison.

| Algorithm | Delay | Total swings | Swings/day | Avg amplitude (price) | Cont. WR | 95% CI | n |
|---|---:|---:|---:|---:|---:|:---:|---:|
| A_fixed_mb2 | 2 | 432 | 4.41 | 77.48 | 77.2% | [73.0% - 80.9%] | 429 |
| B_DC_theta=0.1pct | 0 | 774 | 7.90 | 58.03 | 74.2% | [71.0% - 77.2%] | 772 |
| B_DC_theta=0.3pct | 0 | 726 | 7.41 | 61.12 | 75.6% | [72.3% - 78.5%] | 724 |
| B_DC_theta=0.5pct | 0 | 554 | 5.65 | 73.95 | 78.8% | [75.2% - 82.0%] | 552 |
| B_DC_theta=1.0pct | 0 | 244 | 2.49 | 122.15 | 87.7% | [83.0% - 91.3%] | 244 |
| C_BryBoschan_w5_cyc5 | 5 | 123 | 1.26 | 144.55 | 91.8% | [85.6% - 95.5%] | 122 |

### Pairwise two-proportion z-test vs fixed-lookback baseline

Bonferroni correction: **6 comparisons**, adjusted alpha = 0.05 / 6 = 0.00833.

| Algorithm | WR | Delta vs baseline (pp) | Raw p | Bonferroni significant? |
|---|---:|---:|---:|:---:|
| B_DC_theta=0.1pct | 74.2% | -2.9 | 0.2589 | no |
| B_DC_theta=0.3pct | 75.6% | -1.6 | 0.5368 | no |
| B_DC_theta=0.5pct | 78.8% | +1.6 | 0.5359 | no |
| B_DC_theta=1.0pct | 87.7% | +10.5 | 0.0008 | YES |
| C_BryBoschan_w5_cyc5 | 91.8% | +14.6 | 0.0003 | YES |

**Omnibus chi-square** across 6 algorithms: p = 0.0000

### Ranking by continuation rate (higher = better predictive power)

1. **C_BryBoschan_w5_cyc5** — 91.8% (122 swings, 123 total detected)
2. **B_DC_theta=1.0pct** — 87.7% (244 swings, 244 total detected)
3. **B_DC_theta=0.5pct** — 78.8% (552 swings, 554 total detected)
4. **A_fixed_mb2** — 77.2% (429 swings, 432 total detected)
5. **B_DC_theta=0.3pct** — 75.6% (724 swings, 726 total detected)
6. **B_DC_theta=0.1pct** — 74.2% (772 swings, 774 total detected)

## Q-2.6 Displacement revival

### Primary: categorical `displacement_quality` (full 111-trade batch)

| displacement_quality | n | W | L | BE | WR | 95% CI |
|---|---:|---:|---:|---:|---:|:---:|
| weak | 1 | 1 | 0 | 0 | 100.0% | [20.7% - 100.0%] |
| medium | 5 | 3 | 1 | 1 | 75.0% | [30.1% - 95.4%] |
| strong | 105 | 68 | 35 | 2 | 66.0% | [56.4% - 74.4%] |

**Chi-square across displacement levels:** p = 0.7245

**Strong vs (weak+medium) combined:** 66.0% vs 80.0% (delta -14.0pp, p = 0.5172, n_strong=103, n_other=5)

**Sample caveat:** n(weak)=1 trade(s), n(medium)=5 trade(s). Strong dominates the batch (105 of 111 = 94.6%). This is by design: the Phase 1-2 AI classifier labeled most CANDIDATE setups 'strong' (confidence scoring rubber stamp, per T2a). Non-strong cells are statistically too small to detect moderate effects.

### Secondary: reconstructed impulse magnitude (M15, 10-candle lookback, ATR14)

- Reconstruction matched: **29** of 111 trades (26.1%).
- Not matched: 82 (M15 CSV starts 2026-01-02; batch includes 2024-04-01 onwards). No fabrication: unmatched trades excluded.

Quartile thresholds on impulse_range/ATR14: Q1<=3.12, Q2<=4.10, Q3<=4.48.

| Bucket | n | W | L | WR | Avg R |
|---|---:|---:|---:|---:|---:|
| Q1_low | 8 | 6 | 2 | 75.0% | +0.272 |
| Q2 | 7 | 2 | 5 | 28.6% | -0.416 |
| Q3 | 7 | 4 | 3 | 57.1% | +0.157 |
| Q4_high | 7 | 6 | 1 | 85.7% | +0.597 |

**Chi-square across reconstructed magnitude quartiles:** p = 0.1306 (n=29)

## Caveats

1. **H1 XAUUSD only.** ~100 trading days (Jan 2 - Apr 10, 2026) = modest H1 sample. Continuation rates are computed over all swings detected, but per-algorithm swing counts vary wildly (DC 1.0% gives tens, BB light gives hundreds of swings). Lower-n algorithms have wider CIs.
2. **Continuation metric is a proxy for predictive power, not a trading edge test.** A swing_low whose close[+6] is higher confirms the swing was informative *in isolation*; it does not mean trading it would be profitable (no SL/TP, no transaction cost).
3. **6-candle horizon is arbitrary.** Chosen as roughly 1.5x the typical H1 OB retest distance per architecture.md. Sensitivity not tested here.
4. **Batch `displacement_quality` distribution is massively skewed** (105/111 'strong'). Any categorical revival test is under-powered for weak/medium cells. The Phase 1-2 classifier may have been a rubber stamp (corroborated by T2a's 'confidence_score=80' for 98% of setups).
5. **M15 reconstruction is 2026-only.** 2024-2025 trades cannot be reconstructed from available historical_2026/. We report only what matches and do not extrapolate.
6. **No API calls / no live-data use.** Local only.

## Verdicts

- **Q-2.1:** **H-2.1 null REJECTED ON THE CONTINUATION METRIC — BUT INTERPRET CAREFULLY.** C_BryBoschan_w5_cyc5 beats baseline by +14.6pp at p=0.0003 < Bonferroni 0.00833. **However**, it emits only 123 swings vs baseline 432 (ratio 0.28x). The higher continuation rate reflects selection — larger-amplitude swings (avg amplitude 144.5 vs 77.5) trivially have more room to continue before reverting. This does NOT mean switching the production swing algorithm will improve trading outcomes; it tests a *signal property*, not an edge. **Action:** do NOT swap `market_state.detect_swings` based on this test alone. The production-relevant follow-up is OB-continuation parity across algorithms (see Next steps).
- **Q-2.6:** **INSUFFICIENT DATA — CONFIRM KILL on categorical, DEFER on magnitude.** The categorical `displacement_quality` test is under-powered (n_other=5: 1 weak + 5 medium). Chi-square across levels p=0.7245, strong-vs-other delta -14.0pp p=0.5172. Consistent with prior T3 KILL. Reconstructed-magnitude quartile test (n=29) chi-square p=0.1306. Pattern U-shaped (75%->29%->57%->86%) — extremes win, middle loses. Suggests a non-monotone displacement effect, but n=29 is too small to trust. Not enough signal or sample to overturn prior. Revisit when post-T7 live data accrues (T7 prompt does not self-classify displacement, so the categorical field will likely be blank anyway — the magnitude reconstruction route is the only path forward).

## Next steps

1. **Do NOT change `market_state.detect_swings` based on Q-2.1 alone.** The continuation metric is confounded by amplitude selection (larger swings trivially continue further). Current production fixed-lookback min_bars=2 stays.
2. **Production-relevant follow-up for Q-2.1:** swap the swing algorithm upstream of `find_order_blocks` and compare OB-retest continuation rates (70% baseline) across A/B/C. An algorithm that detects fewer, higher-quality OBs at the same or better retest WR would be the real improvement. This requires building a parallel shadow pipeline and is a multi-week effort.
3. **Q-2.6 categorical revival is not feasible on current data.** T7 prompt does not self-classify displacement; the `displacement_quality` field will not be populated for post-Apr-12 trades. Default path: rely on reconstructed impulse/ATR magnitude as a live feature (log-only) once the M15 historical corpus covers enough post-T7 trades (~3 months).
4. **Secondary hint from reconstructed magnitude (n=29):** U-shape (Q1 75% / Q2 29% / Q3 57% / Q4 86%) is interesting but chi-square p=0.13 and n=29 is far below promotion threshold. Do NOT act on it. Re-test with n>=80 reconstructable trades.
5. **Consider** continuation-rate test across multiple horizons (3/6/12/24 candles) with full Bonferroni for Q-2.1 if someone is curious — but the amplitude-selection confound persists across horizons. Lower priority than the OB-parity test in (2).
