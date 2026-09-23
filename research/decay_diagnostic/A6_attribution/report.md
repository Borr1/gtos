# A6 — Bayesian Decay Attribution (XAUUSD)

Decomposes the H1->H2 2026 WR decay across 11 components. Beta-binomial conjugate-prior (Beta(1.0, 1.0) prior). 95% credible intervals via Monte Carlo composition. Bonferroni correction applied across the family of components.

## Top-line counts

| Period | n | wins | WR |
|---|---:|---:|---:|
| H1 (2026-01..02) | 63 | 30 | 47.6% |
| H2 (2026-03..04) | 44 | 17 | 38.6% |
| **Observed delta** | | | **+8.98pp** |

## Decay attribution

| Component | H1 stratum WRs | H2 stratum WRs | attributed pp | 95% CI | raw_p | bonf_p |
|---|---|---|---:|---|---:|---:|
| framework | ob_retest: 47.6% (n=63) | ob_retest: 38.6% (n=44) | +8.98 | [-9.78, 26.54] | 0.3569 | 1.0000 |
| kill_zone | london: 64.5% (n=31), ny: 31.2% (n=32) | london: 50.0% (n=26), ny: 22.2% (n=18) | +12.27 | [-6.69, 28.53] | 0.4300 | 1.0000 |
| side | LONG: 48.4% (n=62), SHORT: 0.0% (n=1) | LONG: 18.8% (n=32), SHORT: 91.7% (n=12) | +29.64 | [8.98, 44.71] | 0.0051 | 0.0560 |
| ob_zone | ob_pullback: 47.6% (n=63) | ob_pullback: 38.6% (n=44) | +8.98 | [-9.78, 26.54] | 0.3569 | 1.0000 |
| displacement_quality | - | - | +0.00 | - | 1.0000 | 1.0000 |
| fvg_present | no_fvg_required: 47.6% (n=63) | no_fvg_required: 38.6% (n=44) | +8.98 | [-9.78, 26.54] | 0.3569 | 1.0000 |
| touch_count | - | - | +0.00 | - | 1.0000 | 1.0000 |
| setup_grade | A: 33.3% (n=12), A+: 51.0% (n=51) | A: 25.0% (n=4), A+: 40.0% (n=40) | +10.98 | [-9.60, 29.74] | 0.2970 | 1.0000 |
| bias | bullish: 47.6% (n=63) | bearish: 91.7% (n=12), bullish: 18.8% (n=32) | +28.87 | [8.05, 43.85] | 0.0061 | 0.0673 |
| l2_passed | pass: 47.6% (n=63) | pass: 38.6% (n=44) | +8.98 | [-9.78, 26.54] | 0.3569 | 1.0000 |
| regime | UNTAGGED: 51.0% (n=51), bearish: 0.0% (n=1), bullish: 0.0% (n=2), transitional: 44.4% (n=9) | UNTAGGED: 29.2% (n=24), bearish: 83.3% (n=6), transitional: 35.7% (n=14) | +21.81 | [-3.79, 39.75] | 0.0758 | 0.8343 |
| **Total attributed (mean)** | | | **+12.68** | | | |
| **Observed delta** | | | **+8.98** | | | |
| **Residual (unexplained)** | | | **-3.70** | | | |

## Per-component stratum detail

### framework

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ob_retest | 63 | 30 | 47.6% | 0.477 | 44 | 17 | 38.6% | 0.391 | USED |

### kill_zone

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| london | 31 | 20 | 64.5% | 0.636 | 26 | 13 | 50.0% | 0.500 | USED |
| ny | 32 | 10 | 31.2% | 0.324 | 18 | 4 | 22.2% | 0.250 | USED |

### side

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| LONG | 62 | 30 | 48.4% | 0.484 | 32 | 6 | 18.8% | 0.206 | USED |
| SHORT | 1 | 0 | 0.0% | 0.333 | 12 | 11 | 91.7% | 0.857 | LOW_N / LOW_N_H1 |

### ob_zone

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ob_pullback | 63 | 30 | 47.6% | 0.477 | 44 | 17 | 38.6% | 0.391 | USED |

### displacement_quality

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| __missing__ | 63 | 30 | 47.6% | 0.477 | 44 | 17 | 38.6% | 0.391 | MISSING / MISSING_BOTH |

### fvg_present

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| no_fvg_required | 63 | 30 | 47.6% | 0.477 | 44 | 17 | 38.6% | 0.391 | USED |

### touch_count

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| __missing__ | 63 | 30 | 47.6% | 0.477 | 44 | 17 | 38.6% | 0.391 | MISSING / MISSING_BOTH |

### setup_grade

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A | 12 | 4 | 33.3% | 0.357 | 4 | 1 | 25.0% | 0.333 | LOW_N / LOW_N_H2 |
| A+ | 51 | 26 | 51.0% | 0.509 | 40 | 16 | 40.0% | 0.405 | USED |

### bias

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| bearish | 0 | 0 | - | 0.500 | 12 | 11 | 91.7% | 0.857 | LOW_N / ABSENT_H1 |
| bullish | 63 | 30 | 47.6% | 0.477 | 32 | 6 | 18.8% | 0.206 | USED |

### l2_passed

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pass | 63 | 30 | 47.6% | 0.477 | 44 | 17 | 38.6% | 0.391 | USED |

### regime

| Value | H1 n | H1 wins | H1 WR | H1 mean (post.) | H2 n | H2 wins | H2 WR | H2 mean (post.) | flag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| UNTAGGED | 51 | 26 | 51.0% | 0.509 | 24 | 7 | 29.2% | 0.308 | USED |
| bearish | 1 | 0 | 0.0% | 0.333 | 6 | 5 | 83.3% | 0.750 | LOW_N / LOW_N_H1 |
| bullish | 2 | 0 | 0.0% | 0.250 | 0 | 0 | - | 0.500 | LOW_N / ABSENT_H2 |
| transitional | 9 | 4 | 44.4% | 0.455 | 14 | 5 | 35.7% | 0.375 | LOW_N / LOW_N_H1 |

## Strategic verdict

**Top decay driver:** `side` (+29.64pp, 21% of total absolute attributable mass; raw_p=0.0051, bonf_p=0.0560).

Ranked by absolute magnitude: `side` (+29.6pp), `bias` (+28.9pp), `regime` (+21.8pp), `kill_zone` (+12.3pp), `setup_grade` (+11.0pp).

## Methodology

- Beta(α₀, β₀) = (1.0, 1.0) uninformed prior. Posterior per stratum: `Beta(α₀ + wins, β₀ + losses)`.
- Per-component attribution: `sum_strata( (WR_h1 - WR_h2) * n_share_h2 )` over strata with n ≥ 10 in BOTH H1 and H2.
- 95% credible interval via 4000 Monte Carlo draws of WR_h1, WR_h2 ~ Beta posteriors, recomputing the weighted sum.
- Chi-square sum-of-2x2 contingency over used strata for raw_p; Bonferroni correction across the component family.
- `Total attributed (mean)` averages across components rather than summing — each component is an alternative full decomposition over its own strata. Summing would double-count.

## Caveats

- Inputs: A1 results.jsonl (C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aaa10c07278eee86f\research\**\all_results*.json); n_trades_total=107.
- A5 regime/setup_grade join: 107 / 107 matched on (symbol, candle_close_time). A5's source population is the older `_trade_index.json`, NOT the full A1 backtest population — this limits regime/setup_grade attribution power and most strata flag MISSING.
- Trade-index displacement_quality join: 0 / 107 matched on (symbol, date). 2026 trade-index rows carry no displacement_quality; coverage is therefore zero on the decay window of interest.
- `touch_count` and authentic `fvg_present` are NOT recoverable from A1 / A5 / session JSONs (they're properties of the underlying market_state snapshot). Both surface as MISSING_VALUE for all rows; their stratum rows will be skipped from the attribution sum. The synthesized `fvg_present` here is a coarse proxy keyed off framework only.
- `n_unfilled_h2`=0: H2 rows with `ai_outcome_resolved=False` (no realized R recorded). These do NOT enter the rate aggregation. If H2 fill-rate dropped, the attribution analyzes the survivor cohort only.
- Additional notes:
  - `ob_zone` is synthesized from `framework`, not measured directly.
  - `fvg_present` is synthesized from `framework`, not measured directly.
- `r_multiple` proxy: AI realized R from A1 (`ai_realized_r` field). Trades without recorded realized R are dropped from rate aggregations (neither win nor loss).
- Per memory `feedback_walk_level_evidence_not_predictive`: this analysis is realized-R based.

