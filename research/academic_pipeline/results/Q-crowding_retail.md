# Q-8.3 (crowding) + Q-16.4 (retail herding contrarian) — local analysis

Generated: 2026-04-17 10:44 local
Script: `research/academic_pipeline/scripts/q_crowding_retail.py`
Cost: $0 (local only).

## Hypothesis (pre-registered)

**Q-8.3 — internal crowding proxies**

- **H1.** WR trend over time is non-increasing. Kendall's tau between rolling-50-trade window index (chronological) and window WR. Reject null (no trend) if tau < 0 at p < 0.05.
- **H2.** Mean MFE of winning trades compresses over time (crowding front-runs the retest). Kendall's tau on monthly mean MFE of winners.
- **H3 (spread proxy).** Historical CSVs are OHLCV only — no bid/ask — so no direct spread test. Documented as data gap.

**Q-16.4 — retail herding contrarian**

- **H4.** After an extreme prior-day move (|daily return| >= 95th pct of historical XAUUSD daily returns), trades whose direction OPPOSES the extreme have higher WR than trades whose direction FOLLOWS it. Two-proportion z-test, two-sided.
- **H5.** Matched-subset baseline check vs global batch WR (Fisher's exact).

Pre-registered BEFORE computing results. No post-hoc threshold tuning.

## Data

- **Batch trades:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`
  - n=111, date range 2024-04-01 -> 2026-03-13
  - Outcomes: WIN=72, LOSS=36, BE=3
  - Direction: LONG=103, SHORT=7, unknown=1
- **Historical:** `data/historical_2026/XAUUSD_D1.csv` (70 daily bars, Jan 2 - Apr 10 2026).
- **Live records:** 9 JSON snapshots in `knowledge_base/trade_records/XAUUSD/` for Apr 15-16 2026. These are decision-time captures without closed-trade outcomes (no r_multiple) — cannot contribute to WR trend. Documented as Apr 2026 live data gap.

## Method

1. Load unified_trades_v2, sort chronologically.
2. **Q-8.3 WR trend:** rolling 50-trade windows over the chronological series; Kendall tau + Spearman rho between window index and window WR. WR = WINS / (WINS + LOSSES); breakevens excluded from denominator.
3. **Q-8.3 MFE compression:** per-calendar-month mean MFE of winners only (n >= 2/month); Kendall tau + Spearman rho vs month index.
4. **Q-16.4:** derive 95th-percentile abs-return threshold from XAUUSD D1 bars. For each batch trade, look up the most recent D1 bar strictly prior to trade date. If |daily return| >= threshold, classify as "extreme UP" or "extreme DOWN". Label trade as contrarian (direction opposes extreme) or continuation (direction matches). Two-proportion z-test + Fisher's exact.
5. Global batch baseline for sanity.

All stats implemented in pure Python; no scipy dependency.

## Q-8.3 — Internal crowding proxies

### Rolling-window WR trend

- Windows: 62 (window size 50)
- First window WR: 0.646
- Last window WR: 0.694
- WR delta (last - first): +0.048
- **Kendall tau:** +0.754, p = <0.001
- **Spearman rho:** +0.894, p = <0.001

Sampled windows (every Nth):

| window_idx | WR | wins |
|---|---|---|
| 0 | 0.646 | 31 |
| 7 | 0.604 | 29 |
| 14 | 0.625 | 30 |
| 21 | 0.633 | 31 |
| 28 | 0.660 | 33 |
| 35 | 0.673 | 33 |
| 42 | 0.673 | 33 |
| 49 | 0.694 | 34 |
| 56 | 0.714 | 35 |

### MFE compression (winners only)

- Months analyzed: 13
- First 3-month mean MFE (winners): 1.438R
- Last 3-month mean MFE (winners): 1.259R
- **Kendall tau (month_idx vs mean MFE):** +0.128, p = 0.542
- **Spearman rho:** +0.170, p = 0.566

Monthly MFE means:

| month | mean_mfe_R (winners) | n_winners |
|---|---|---|
| 2024-04 | 1.016 | 2 |
| 2024-07 | 1.075 | 3 |
| 2025-01 | 2.225 | 4 |
| 2025-02 | 0.588 | 8 |
| 2025-03 | 1.413 | 7 |
| 2025-05 | 1.889 | 3 |
| 2025-06 | 0.987 | 3 |
| 2025-09 | 1.115 | 6 |
| 2025-10 | 1.634 | 9 |
| 2025-12 | 1.634 | 6 |
| 2026-01 | 0.723 | 11 |
| 2026-02 | 1.489 | 4 |
| 2026-03 | 1.565 | 3 |

### Q-8.3 verdict (reviewer-corrected — see autocorrelation section below)

**INCONCLUSIVE — rolling-window result inflated by autocorrelation.** The original rolling-window tau=+0.754 (p=<0.001) used overlapping 50-trade windows; effective independent sample is ~n_trades/50 = ~2, not ~62. After correction:
  - Non-overlapping windows (stride=50, n=2): tau=+nan, p=NaN.
  - Monthly WR aggregate (min 3 trades/month, n=14): tau=-0.226, p=0.260.
Neither survives Bonferroni alpha=0.025. **No reliable trend is detected; the original 'WR trending UPWARD' conclusion is RETRACTED.** The observed rolling-window positive tau was a statistical artefact of overlapping samples.

### Reviewer correction 2026-04-17 — autocorrelation in rolling-window tau (MAJOR)

**Finding:** The original Kendall tau above was computed on **overlapping** 50-trade windows (stride=1). Consecutive windows share 49 of 50 observations, so the independence assumption underlying Kendall tau's variance formula is violated. Effective sample size is approximately `n_trades / window_size ≈ 2`, not the reported 62. This inflates the z-statistic by approximately √50 and the reported p=<0.001 is not trustworthy.

**Corrections applied:**

1. **Non-overlapping windows** (stride = window size = 50). Each trade enters exactly one window. Only complete windows included (trailing partial dropped).
   - Windows: 2
   - Kendall tau: +nan, p = NaN
   - Spearman rho: +nan, p = NaN

2. **Monthly WR aggregate** (per-month WR = WIN / (WIN+LOSS) on months with >=3 decided trades — independent calendar buckets).
   - Months included: 14
   - Kendall tau (month_idx vs WR): -0.226, p = 0.260
   - Spearman rho: -0.265, p = 0.340

Per-month WR table:

| month | WR | wins | n_decided |
|---|---|---|---|
| 2024-04 | 0.667 | 2 | 3 |
| 2024-07 | 1.000 | 3 | 3 |
| 2025-01 | 0.800 | 4 | 5 |
| 2025-02 | 0.667 | 8 | 12 |
| 2025-03 | 0.636 | 7 | 11 |
| 2025-04 | 0.250 | 1 | 4 |
| 2025-05 | 1.000 | 3 | 3 |
| 2025-06 | 0.375 | 3 | 8 |
| 2025-09 | 0.750 | 6 | 8 |
| 2025-10 | 0.900 | 9 | 10 |
| 2025-12 | 0.750 | 6 | 8 |
| 2026-01 | 0.611 | 11 | 18 |
| 2026-02 | 0.667 | 4 | 6 |
| 2026-03 | 0.600 | 3 | 5 |

**Bonferroni alpha** across the two corrected tests = 0.025. Both must reject to claim a trend.

## Q-16.4 — Contrarian after extreme prior-day move

- XAUUSD D1 bars analyzed: 70
- 95th-percentile abs-return threshold: 4.496%
- Matched trades (extreme prior day, known direction): 2
- Skipped — no prior bar: 79
- Skipped — prior day not extreme: 27
- Skipped — unknown direction: 0

| subset | n | wins | losses | WR |
|---|---|---|---|---|
| contrarian (opposes extreme) | 2 | 1 | 1 | 0.500 |
| continuation (follows extreme) | 0 | 0 | 0 | nan |

- WR delta (contrarian - continuation): +nan
- Two-proportion z = +nan, two-sided p = NaN
- Fisher's exact two-sided p = 1.000
- Subset vs global (sanity): p = 0.621 (global WR 0.667)

### Q-16.4 verdict

**UNDERPOWERED — DATA GAP.** Only 2 batch trades could be matched to a prior-day D1 bar. Root cause: local historical CSVs cover only 2026-01-02 -> 2026-04-10, but 82/111 batch trades occurred in 2024-2025. Effect is not statistically interpretable at this sample size. Test is READY TO RE-RUN once the 2024-2025 D1 gap is closed.

## Caveats

1. **Uneven temporal coverage.** The batch's 111 trades are not uniformly distributed (2024 is thin; 2026-01 alone has 18). Rolling-window indices are trade-count, not time-weighted, so a "decay trend" can be confounded with regime shifts (e.g., the Jan 2026 bull impulse).
2. **Direction bias.** 103/111 = 92.8% of batch trades are LONG. The Q-16.4 test therefore almost entirely asks "after an extreme UP day, do LONG trades perform worse than after an extreme DOWN day" (or vice versa). True directional contrarian testing needs a more balanced sample.
3. **Historical CSVs are 2026-only** (Jan 2 - Apr 10). Pre-2026 batch trades (n=82) have no local D1 bars to derive prior-day moves, so they fall into skipped_no_prior.
4. **OHLCV only.** No bid/ask spread columns, no tick data. H3 (spread-widening crowding proxy) is not testable locally.
5. **Live Apr 2026 records** (9 files) are decision snapshots, not closed trades — no r_multiple — so they cannot contribute to WR trend.
6. **Multiple testing.** Four tests performed (H1 tau, H2 tau, H4 z, H5 Fisher). Bonferroni-adjusted alpha = 0.0125. Only treat a result as confirmed if p < 0.0125.
7. **Reviewer correction (2026-04-17) — autocorrelation:** The rolling-window Kendall tau (window=50, stride=1) was inflated by overlap between consecutive windows; effective sample size was ~2 independent windows, not 62. Corrected tests (non-overlapping stride=50 and monthly WR aggregate) are reported in the Reviewer correction section above. The original claim of "NO CROWDING DECAY — trending UPWARD" has been RETRACTED.

## Data gaps

| Proxy | Status | Why not fillable locally |
|---|---|---|
| CFTC COT speculator positioning | MISSING | Not in repo; requires CFTC weekly download. |
| IG / OANDA client-sentiment | MISSING | Broker-feed API; not public, not cached locally. |
| Google Trends "smart money concept" | MISSING | No cached CSV; requires pytrends + internet. |
| Twitter / Reddit SMC mention volume | MISSING | No cached dataset. |
| Bid/ask spread on OB retest bars | MISSING | Historical CSVs are OHLCV; tick data absent. |
| Post-2024-04 / pre-2026-01 D1 bars | MISSING | Historical export is 2026-only; 2024-2025 batch trades cannot be matched to prior-day moves. |
| Live closed-trade outcomes (Apr 2026) | IN FLIGHT | Only 9 decision-time captures; no exit/r_multiple fields populated. |

## Verdicts

- **Q-8.3:** **INCONCLUSIVE — rolling-window result inflated by autocorrelation.** The original rolling-window tau=+0.754 (p=<0.001) used overlapping 50-trade windows; effective independent sample is ~n_trades/50 = ~2, not ~62. After correction:
  - Non-overlapping windows (stride=50, n=2): tau=+nan, p=NaN.
  - Monthly WR aggregate (min 3 trades/month, n=14): tau=-0.226, p=0.260.
Neither survives Bonferroni alpha=0.025. **No reliable trend is detected; the original 'WR trending UPWARD' conclusion is RETRACTED.** The observed rolling-window positive tau was a statistical artefact of overlapping samples.
- **Q-16.4:** **UNDERPOWERED — DATA GAP.** Only 2 batch trades could be matched to a prior-day D1 bar. Root cause: local historical CSVs cover only 2026-01-02 -> 2026-04-10, but 82/111 batch trades occurred in 2024-2025. Effect is not statistically interpretable at this sample size. Test is READY TO RE-RUN once the 2024-2025 D1 gap is closed.

## Next steps

1. **Close the daily-bar gap.** Export D1 bars for XAUUSD 2024-01 -> 2025-12 from MT5 to enable Q-16.4 on the full batch (n=111 candidates vs ~2 matched now).
2. **Re-run Q-8.3 monthly.** Keep the script in place; after WF-1 concludes (Jul 7 2026), re-run with live trades appended. A persistent negative tau at p < 0.05 is a crowding-decay trigger.
3. **External-proxy capture (CEO approval needed).** Any one of: CFTC COT XAUUSD speculator net position; Google Trends "order block retest"; cached IG sentiment scraper. Each closes one gap identified above.
4. **SHORT-side collection.** The 7.2% SHORT sample is too small for direction-conditioned tests. Ideally 30+ SHORT trades before re-running directional analyses.
5. **Do NOT promote a contrarian filter on this data.** Underpowered / ambiguous per the verdict above. Treat as a candidate shadow-logger only if verdict upgrades.

*End of report.*
