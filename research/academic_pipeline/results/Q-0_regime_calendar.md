# Q-0 Regime & Calendar Effects Analysis

**Date generated:** 2026-04-17  
**Author:** Claude Code (GTOS research agent, $0 local analysis)  
**Batch:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n=111)  
**D1 source:** `data/historical/XAUUSD_D1.csv` (2023-04-03 -> 2026-03-30)

## Hypothesis (pre-registered)

**Q-0.1** Null: prior-day D1 shape independent of trade outcome.  
Alt: `clean_trend_up` / `clean_trend_down` class WR >= baseline+10pp with n>=20.

**Q-0.7** Null: each calendar tag's WR == `none`-baseline WR.  
Alt: at least one tag shows |delta_WR| > 10pp with n>=15.

## Data

- Batch trades: **111** (WIN=72, LOSS=36, BREAKEVEN=3)
- Baseline WR (WIN / (WIN+LOSS)): **0.667** (66.7%)
- Prior-day D1 match failures: 0 (batch date before D1 coverage)
- Batch date range: 2024-04-01 ... 2026-03-13  (note: unordered)

## Method

### Q-0.1 D1 shape classification
For each trade date `d`, fetch D1 bar at last trading day < d. Compute body/range,
close-location, wick ratios, direction. Class rules:

- `clean_trend_up`: body/range > 0.7 AND close_loc >= 0.8 AND bull
- `clean_trend_down`: body/range > 0.7 AND close_loc <= 0.2 AND bear
- `indecision`: body/range < 0.3
- `neutral`: else
- `no_d1`: no D1 bar available (batch dates prior to 2023-04-03)

### Q-0.7 Calendar tags
- `fomc_day`: trade date matches a known FOMC meeting day (2024-01-30 .. 2026-03-19, hard-coded)
- `fomc_adjacent`: +-1 business day from any FOMC day, not itself a FOMC day
- `opex_day`: 3rd Friday of the month
- `comex_delivery`: within last 5 business days of the month (approx. COMEX gold delivery window)
- `turn_of_month`: last 3 + first 3 business days of month
- `none`: no tag applies (used as baseline for Fisher's 2x2)

A single trade can carry multiple tags; WR per tag is computed independently.
All tests two-sided, `scipy.stats.fisher_exact` / `chi2_contingency`. Breakevens excluded from WR.

## Q-0.1 Results: prior-day D1 shape

| Class | n | WIN | LOSS | BE | WR (W/W+L) | avg R | Wilson 95% CI | delta_WR vs baseline |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| `clean_trend_up` | 30 | 17 | 11 | 2 | 60.7% | +0.101 | [42.4%, 76.4%] | -6.0pp |
| `clean_trend_down` | 4 **LOW-n** | 1 | 3 | 0 | 25.0% | -0.685 | [4.6%, 69.9%] | -41.7pp |
| `indecision` | 42 | 31 | 10 | 1 | 75.6% | +0.360 | [60.7%, 86.2%] | +8.9pp |
| `neutral` | 35 | 23 | 12 | 0 | 65.7% | +0.193 | [49.2%, 79.2%] | -1.0pp |

**Chi-square across classes (excl. no_d1/degenerate):** chi2 = 5.06, p = 0.1674

## Q-0.7 Results: calendar tags

| Tag | n | WIN | LOSS | BE | WR (W/W+L) | avg R | delta_WR vs none | OR | p (Fisher 2x2) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `none` (baseline) | 53 | 34 | 17 | 2 | 66.7% | +0.270 | - | - | - |
| `fomc_day` | 14 **LOW-n** | 10 | 4 | 0 | 71.4% | +0.074 | +4.8pp | 1.25 | 1.000 |
| `fomc_adjacent` | 6 **LOW-n** | 6 | 0 | 0 | 100.0% | +1.552 | +33.3pp | inf | 0.164 |
| `opex_day` | 7 **LOW-n** | 2 | 4 | 1 | 33.3% | -0.207 | -33.3pp | 0.25 | 0.179 |
| `comex_delivery` | 23 | 14 | 9 | 0 | 60.9% | +0.013 | -5.8pp | 0.78 | 0.793 |
| `turn_of_month` | 31 | 19 | 12 | 0 | 61.3% | +0.143 | -5.4pp | 0.79 | 0.641 |

## Caveats

- **Single-symbol (XAUUSD-only) batch.** Prices (2254..5580) and date density confirm this is the gold backtest; results do not generalize to US30/USDJPY/GBPJPY/GBPUSD.
- **Total sample n=111.** Any sub-bucket with n<15 is flagged **LOW-n** and should be read as hypothesis-generating only.
- **No multiple-comparison correction applied.** With ~5 tags tested, a raw p<0.05 is roughly p<0.25 corrected — none of the observed p-values reach Bonferroni significance.
- **Batch is survivorship-filtered.** unified_trades_v2 contains only setups that passed all pre-batch gates (H1 bias, OB retest, etc.), so these WRs are post-filter; they describe selection residuals, not raw intraday regime.
- **FOMC dates hard-coded from public Federal Reserve calendar (Jan 2024 - Mar 2026).** `data/economic_calendar.csv` was not used: it covers Apr-May 2026 only with zero batch overlap (confirmed by wave-1 Q-10.2).
- **D1 shape uses prior trading day, not calendar day** — weekends/holidays resolved by walking back <=7 days.
- **Tag overlap:** a single trade can appear in multiple tags (e.g., `fomc_adjacent` + `turn_of_month`); per-tag rows are marginal, not mutually exclusive. The `none` baseline excludes every tagged trade.
- **Breakeven (n=3) excluded from WR computation** but included in `n` and `avg R`.

## Verdicts

### Q-0.1 — prior-day D1 shape
- Best `clean_trend` class: **`clean_trend_up`** — WR = 60.7%, n = 30 (delta vs baseline = -6.0pp)
- Pre-registered promote threshold: n>=20 AND delta>=+10pp -> **n_ok=True, edge_ok=False**
- **VERDICT: KILL** — sample is sufficient but edge is below the +10pp bar; D1 shape gating does not justify added complexity.

### Q-0.7 — calendar tags
- No calendar tag with n>=15 AND |delta_WR|>10pp at baseline.
- `fomc_adjacent`: delta = +33.3pp but n = 6 < 15 -> **DEFER** (underpowered).
- `opex_day`: delta = -33.3pp but n = 7 < 15 -> **DEFER** (underpowered).
- **VERDICT: DEFER for: fomc_adjacent, opex_day**.

## Next steps

1. Any tag marked PROMOTE: add to the shadow logger (observation-only, no gating) and re-evaluate after 30+ fresh post-Apr 2026 trades.
2. Any tag marked DEFER (low n): park in roadmap; revisit once batch v3 is larger (n>=200).
3. Q-0.1 improvement idea: extend D1 features to include ATR percentile and gap-open size, re-test once per-instrument batches exist.
4. Q-0.7 improvement idea: expand FOMC tagging to include release-hour M15 window only (09:00-15:00 UTC on FOMC day), since overnight FOMC asymmetry may be masking the release-hour effect.
5. Cross-validate on live forward data (Apr 2026+) — 29 batch trades fall in the live-data window, so any finding here has moderate lookhead risk and must be confirmed out-of-sample before gating.

---
Generated by `research/academic_pipeline/scripts/q_0_regime_calendar.py`. Reproduction: `python research/academic_pipeline/scripts/q_0_regime_calendar.py`.