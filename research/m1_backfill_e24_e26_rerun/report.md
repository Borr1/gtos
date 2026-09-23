# P1 — M1 backfill + E24/E26 re-run (real M1)

_Generated_: 2026-04-27T19:31:29.268523+00:00
_Branch_: feat/research-m1-backfill-microstructure-rerun

## Executive verdict

**Verdict code: `NULL_VERDICT_CONFIRMED`**

No (symbol × feature) cell reached raw significance even with real M1. The M15-fallback null verdict from the prior E24+E26 run is upheld.

## Phase A — M1 backfill (redacted_account-Server 2)

- All 7 production instruments backfilled from MT5 as of 2026-04-27.
- **Broker M1 cap empirically observed**: oldest available M1 ranges from 2026-01-14 (XAUUSD/US30/XAGUSD/NAS100) to 2026-01-20 (FX pairs).
- All symbols pulled the maximum 100,003 M1 bars (~3.5 months). redacted_account-Server 2 does NOT serve M1 history beyond ~2026-01-14, so the broker cap is below the 1-year minimum mentioned in the task brief.

Per-symbol details: see `research/m1_backfill_e24_e26_rerun/m1_backfill_log.csv`.

## Phase B — E24/E26 re-run with real M1

### Telemetry

- Total backtest fills harvested: 279
- Per-fill feature rows out: 73
- Skipped: 206 (reasons: {'OUT_OF_M1_RANGE': 189, 'M1_FILE_MISSING': 17})
- Symbols with M1 loaded: ['XAUUSD', 'GBPJPY', 'GBPUSD', 'USDJPY', 'US30_cash']

### Per-cell correlations (real M1)

| symbol | feature | n | rho | p | p_bonferroni | verdict |
|---|---|---|---|---|---|---|
| XAUUSD | cumulative_delta | 24 | -0.0257 | 0.905248 | 1.0 | NO_SIGNAL |
| XAUUSD | footprint_imbalance | 24 | -0.0437 | 0.839507 | 1.0 | NO_SIGNAL |
| XAUUSD | micro_reversal_count | 24 | -0.0018 | 0.993426 | 1.0 | NO_SIGNAL |
| GBPJPY | cumulative_delta | 16 | 0.2673 | 0.316976 | 1.0 | NO_SIGNAL |
| GBPJPY | footprint_imbalance | 16 | 0.2839 | 0.28665 | 1.0 | NO_SIGNAL |
| GBPJPY | micro_reversal_count | 16 | -0.0417 | 0.87802 | 1.0 | NO_SIGNAL |
| GBPUSD | cumulative_delta | 4 | None | None | None | INSUFFICIENT_N |
| GBPUSD | footprint_imbalance | 4 | None | None | None | INSUFFICIENT_N |
| GBPUSD | micro_reversal_count | 4 | None | None | None | INSUFFICIENT_N |
| USDJPY | cumulative_delta | 15 | 0.0707 | 0.802424 | 1.0 | NO_SIGNAL |
| USDJPY | footprint_imbalance | 15 | 0.0706 | 0.802599 | 1.0 | NO_SIGNAL |
| USDJPY | micro_reversal_count | 15 | -0.1554 | 0.58026 | 1.0 | NO_SIGNAL |
| US30_cash | cumulative_delta | 14 | 0.1869 | 0.522334 | 1.0 | NO_SIGNAL |
| US30_cash | footprint_imbalance | 14 | 0.1691 | 0.563348 | 1.0 | NO_SIGNAL |
| US30_cash | micro_reversal_count | 14 | 0.376 | 0.185208 | 1.0 | NO_SIGNAL |

**Family size (cells with n >= 10)**: 12
- SURVIVES_BONFERRONI: 0
- RAW_SIG_NOT_SURVIVING: 0
- NO_SIGNAL: 12
- INSUFFICIENT_N: 3

### Per-feature pooled view

| feature | cells | median rho | mean rho | raw_sig | bonferroni | verdict |
|---|---|---|---|---|---|---|
| cumulative_delta | 4 | 0.1288 | 0.1248 | 0 | 0 | NO_SIGNAL |
| footprint_imbalance | 4 | 0.1198 | 0.12 | 0 | 0 | NO_SIGNAL |
| micro_reversal_count | 4 | -0.0218 | 0.0443 | 0 | 0 | NO_SIGNAL |

### Side-by-side: M15-fallback baseline vs real-M1 re-run

This is the load-bearing comparison: did real M1 surface signal that the M15-fallback proxy missed?

| symbol | feature | n_m1 | rho_m1 | p_bf_m1 | n_m15 | rho_m15 | p_bf_m15 | delta_|rho| | verdict_m1 |
|---|---|---|---|---|---|---|---|---|---|
| XAUUSD | cumulative_delta | 24 | -0.0257 | 1.0 | 49 | 0.0709 | 1.0 | -0.0452 | NO_SIGNAL |
| XAUUSD | footprint_imbalance | 24 | -0.0437 | 1.0 | 49 | -0.0369 | 1.0 | 0.0068 | NO_SIGNAL |
| XAUUSD | micro_reversal_count | 24 | -0.0018 | 1.0 | 49 | -0.0086 | 1.0 | -0.0068 | NO_SIGNAL |
| GBPJPY | cumulative_delta | 16 | 0.2673 | 1.0 | 42 | -0.0559 | 1.0 | 0.2114 | NO_SIGNAL |
| GBPJPY | footprint_imbalance | 16 | 0.2839 | 1.0 | 42 | -0.0666 | 1.0 | 0.2173 | NO_SIGNAL |
| GBPJPY | micro_reversal_count | 16 | -0.0417 | 1.0 | 42 | 0.0439 | 1.0 | -0.0022 | NO_SIGNAL |
| GBPUSD | cumulative_delta | 4 | None | None | 7 | None | None | None | INSUFFICIENT_N |
| GBPUSD | footprint_imbalance | 4 | None | None | 7 | None | None | None | INSUFFICIENT_N |
| GBPUSD | micro_reversal_count | 4 | None | None | 7 | None | None | None | INSUFFICIENT_N |
| USDJPY | cumulative_delta | 15 | 0.0707 | 1.0 | 33 | 0.0097 | 1.0 | 0.061 | NO_SIGNAL |
| USDJPY | footprint_imbalance | 15 | 0.0706 | 1.0 | 33 | 0.0277 | 1.0 | 0.0429 | NO_SIGNAL |
| USDJPY | micro_reversal_count | 15 | -0.1554 | 1.0 | 33 | 0.1516 | 1.0 | 0.0038 | NO_SIGNAL |
| US30_cash | cumulative_delta | 14 | 0.1869 | 1.0 | 41 | 0.1618 | 1.0 | 0.0251 | NO_SIGNAL |
| US30_cash | footprint_imbalance | 14 | 0.1691 | 1.0 | 41 | 0.1686 | 1.0 | 0.0005 | NO_SIGNAL |
| US30_cash | micro_reversal_count | 14 | 0.376 | 1.0 | 41 | 0.0581 | 1.0 | 0.3179 | NO_SIGNAL |

### Top-3 absolute rho per cell (M1)

| symbol | feature | rho | p | p_bf | n |
|---|---|---|---|---|---|
| US30_cash | micro_reversal_count | 0.376 | 0.185208 | 1.0 | 14 |
| GBPJPY | footprint_imbalance | 0.2839 | 0.28665 | 1.0 | 16 |
| GBPJPY | cumulative_delta | 0.2673 | 0.316976 | 1.0 | 16 |

## Phase 2 implication

**Real M1 input confirms the M15-fallback null verdict.**

Recommendation: archive the `cumulative_delta` / `footprint_imbalance` / `micro_reversal_count` triplet from the active research backlog. The synthetic-tick reconstructor as a class is upper-bounded by Lee-Ready 1991 candle-direction proxy — adding a longer lookback or different bar aggregations is unlikely to change the verdict.

**Strategic note**: per `project_f15_synthesis_regime_is_load_bearing`, the H2 decay is regime-conditioned LONG-side selectivity collapse. Phase 2 research budget is better spent on (a) regime-aware K54 ML classifier, (b) Phase 2 prompt research targeting *regime-conditional selectivity* in trending_bull cohort, NOT on OHLC-derivable microstructure features.

## Reconstructor sample (XAUUSD 2026-04-15 13:00-13:30 UTC)

- Input timeframe: **M1** (was `M15_fallback` in prior run)
- Bars consumed: 30
- Synthetic ticks emitted: 120

See `reconstructor_validation_m1.csv` for the full 4-tick OHLC path dump.

## Reproducibility

```bash
# Phase A — backfill M1 from MT5 (requires redacted_account terminal logged in)
python research/m1_backfill_e24_e26_rerun/backfill_m1.py

# Phase B — re-run E24/E26 with real M1
python research/m1_backfill_e24_e26_rerun/rerun_e26_m1.py
```