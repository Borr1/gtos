# Data Inventory Report — 2026-04-06

Complete catalog of all data files, schemas, field coverage, and analysis feasibility.

---

## 1. Trade Index (129 trades)

**Path:** `knowledge_base/index/_trade_index.json`
**Version:** 2, reseeded 2026-04-04 from `reseed_from_sessions.py`
**Date range:** 2024-03-01 to 2026-03-13 (chronologically sorted)

### Instrument & Outcome Breakdown

| Symbol | Count | WIN | LOSS | BREAKEVEN |
|--------|-------|-----|------|-----------|
| XAUUSD | 105 | — | — | — |
| GBPUSD | 24 | — | — | — |
| **Total** | **129** | — | — | — |

Frameworks: ob_retest (majority), breaker_retest, session_sweep
Grades: A, A+
Kill zones: london, ny

### Field Coverage (15 fields, all 100% coverage except where noted)

| Field | Type | Coverage | Min | Max | Mean | Notes |
|-------|------|----------|-----|-----|------|-------|
| r_multiple | float | 100% | -1.0 | 3.99 | 0.278 | Primary outcome |
| mfe_r | float | 99% | 0.0 | 6.672 | 1.194 | |
| mae_r | float | 99% | 0.0 | 3.042 | 0.547 | |
| hold_time_candles | int | 99% | 1 | 66 | 30.3 | |
| direction | null | 100% | — | — | — | **ALL NULL** |
| kill_zone | string | 100% | — | — | — | london, ny |
| grade | string | 100% | — | — | — | A, A+ |
| framework | string | 100% | — | — | — | ob_retest, breaker_retest, session_sweep |
| outcome | string | 100% | — | — | — | WIN, LOSS, BREAKEVEN |
| exit_type | string | 99% | — | — | — | 6 values |
| symbol | string | 100% | — | — | — | XAUUSD, GBPUSD |
| date | string | 100% | — | — | — | 97 unique dates |
| trade_id | string | 100% | — | — | — | 129 unique |

### MISSING Critical Fields (NOT in trade index)

- entry_price, entry_time, sl_price, tp1_price
- d1_direction, h4_direction
- displacement_ratio, ob_price, ob_freshness
- body_range_ratio, causing_event_type
- session_memory_used, confidence_score

**Implication:** The trade index is a SUMMARY file. Per-trade structural details (prices, HTF alignment, OB features) are NOT stored here. They exist only in session replay files or batch API response caches.

---

## 2. Displacement Database (6,641 records, 94 fields)

**Path:** `knowledge_base_backtest/analysis/displacement_database_20260403_0030.json`
**Size:** 13.1 MB
**Instrument:** XAUUSD only
**Granularity:** Per-displacement-candle (M15 candles that pass displacement threshold)

### Key Fields (all 100% coverage unless noted)

| Field | Type | Coverage | Values/Range |
|-------|------|----------|-------------|
| cont_3h | bool | 100% | true=3272 (49.3%) |
| cont_1h | bool | 100% | true=3222 (48.5%) |
| cont_session | bool | 100% | true=3315 (49.9%) |
| in_ote | bool | 100% | true=768 (11.6%) |
| in_prem | bool | 100% | true=4007 (60.3%) |
| in_disc | bool | 100% | true=2634 (39.7%) |
| tight | num | 100% | 0.198 - 4.354, mean=1.096 |
| consol | num | 100% | 0.231 - 3.1, mean=0.900 |
| kz | bool | 100% | true=1416 (21.3%) |
| d1_dir | string | 100% | bearish, bullish, insufficient_data, transitional |
| h4_dir | string | 100% | bearish, bullish, transitional |
| h4_aligned_d1 | bool | 100% | true=3463 (52.1%) |
| set | string | 100% | disc, val |
| origin_revisited | bool | 100% | true=5560 (83.7%) |
| date | string | 100% | 516 unique dates |
| session | string | 100% | asian, late, london, ny |
| direction | string | 100% | bearish, bullish |
| strength | string | 100% | extreme, standard, strong |
| body_ratio | num | 100% | 2.0 - 30.04, mean=3.194 |
| creates_fvg | bool | 100% | true=4082 (61.5%) |
| sweep | bool | 100% | true=5812 (87.5%) |
| sweep_level | string | 88% | asian_high/low, pdh, pdl, session_high/low |
| mfe_3h | num | 100% | 0.0 - 419.61 (raw $ move) |
| mae_3h | num | 100% | 0.0 - 260.82 |
| mfe_3h_bm | num | 100% | 0.0 - 21.28 (body multiples) |

**94 total fields** including: timestamp, dow, kz_min, body_size, wick_ratio, OHLCV, fvg_size/pct, crosses_rn, rn_level, csld, csls, liq_depth, levels_swept, mss, nc_body_ratio, nc_dir, nc_rej_wick, ob_dist, ob_type, p5/p10 context, pd_body_pct, pd_dir, pd_rva, pdh/pdl, revisit_candles/depth/mfe, seq, sweep_cb/quality/wick, volume, align, ct, exhaust, first_kz, m15_aligned/dir, prior_body.

---

## 3. OB Retest Comprehensive (1,520 OBs — Aggregate Only)

**Path:** `knowledge_base_backtest/analysis/ob_retest_comprehensive_20260405.json`
**Size:** 35 KB
**Granularity:** AGGREGATE statistics, NOT per-OB records
**Data range:** 2024-04-01 to 2026-03-30
**Discovery:** 2024-04-01 to 2025-06-30 | **Validation:** 2025-07-01 to 2026-03-30

### OB Census

| Instrument | Total OBs | Retested | KZ Retested |
|------------|-----------|----------|-------------|
| XAUUSD | 820 | 805 (98.2%) | 355 (43.3%) |
| GBPUSD | 700 | 700 (100%) | 425 (60.7%) |
| **Combined** | **1,520** | **1,505 (99.0%)** | **780 (51.3%)** |

Baseline continuation rate: 66.45%

### Feature Ranking (16 features analyzed)

Features tested by chi-squared with discovery/validation split:
- hour_of_retest, nearby_ob_count, day_of_week, premium_discount_zone, body_range_ratio, causing_event_type, freshness_candles, h4_alignment, d1_strength, instrument, and more

Each feature has: discovery groups (n, continuation_rate, avg_mfe_r, avg_mae_r), chi2, p-value, validation groups.

### Combination Tests

6 discovery combinations tested with Bonferroni correction.

### What IS available

- Per-hour, per-day, per-zone continuation rates
- Feature chi-squared and p-values (discovery + validation)
- Multi-feature combination lift analysis
- Quality score definitions and thresholds
- AI selection comparison (traded vs non-traded OBs)

### What is NOT available (per-OB records)

- Individual OB price zones, exact timestamps
- Per-OB retracement percentages
- Per-OB continuation outcomes linked to individual features

---

## 4. Phase B FVG Comprehensive (Aggregate Only)

**Path:** `knowledge_base_backtest/analysis/smc_phase_b_comprehensive_20260405.json`
**Size:** 32 KB
**Granularity:** AGGREGATE — no per-event records

### Event Type Summary

| Event Type | XAUUSD n | XAUUSD WR | GBPUSD n | GBPUSD WR | Features |
|------------|----------|-----------|----------|-----------|----------|
| b1_fvg_fill | 1,783 | 52.1% | 1,827 | 38.1% | 8 features |
| b2_breaker_block | 383 | 40.2% | 419 | 18.1% | 3 features |
| b3_equal_hl | 1,188 | 18.7% | 2,321 | 13.6% | 4 features |
| b4_rejection_block | 11,591 | 31.3% | 12,467 | 11.6% | 4 features |
| b5_volume_imbalance | 13,598 | 24.7% | 7,474 | 9.9% | 2 features |

FVG features analyzed: width_pct_atr, creation_displacement_ratio, freshness_candles, fill_percentage, d1_aligned, pd_zone, session, in_silver_bullet

Structure: discovery/validation/total splits with feature group breakdowns.

**No per-FVG records, no dates, no price boundaries.**

---

## 5. Sweep Atlas (Microstructure Stream 1)

**Path:** `knowledge_base_backtest/analysis/microstructure_stream1_sweeps_20260405.json`
**Size:** 1.6 MB
**Granularity:** PER-DAY with nested per-sweep arrays

### Structure

- `daily_data`: XAUUSD (515 days), GBPUSD (515 days)
  - Per day: date, dow, asian_h/l, asian_width, pdh, pdl, adr_20, asian_pct_adr
  - Nested `sweeps[]` per day with: sweep_time, level_swept, level_value, sweep_type (breakout/rejection), wick_distance, kz, mins_into_kz, next_candle_dir
- `sweep_summary`: by_level, by_level_kz aggregate stats
- `post_sweep_behavior`: by_level, by_kz — MFE/net move at 30min/1hr/2hr
- `sweep_sequencing`: multi-sweep pattern data

Sweep levels: asian_h, asian_l, pdh, pdl
Has per-sweep records with timestamps, level, type, kz, and next-candle direction.

---

## 6. Microstructure Streams 2-6 (All Aggregate)

| Stream | File | Size | Top-Level Keys |
|--------|------|------|---------------|
| 2: Displacements | microstructure_stream2_displacements_20260405.json | 326 KB | clustering, feature_ranking, metadata, ob_retest, pre_conditions, timing_heatmap |
| 3: OB Quality | microstructure_stream3_ob_quality_20260405.json | 3.9 KB | 3A_ob_census, 3B_ob_characteristics, 3C_ob_survival, metadata |
| 4: Sequences | microstructure_stream4_sequences_20260405.json | 8.6 KB | 4A_winning_anatomy, 4B_losing_anatomy, 4C_comparison, metadata |
| 5: Session Dynamics | microstructure_stream5_session_dynamics_20260405.json | 14 KB | 5A_first_hour_persistence, 5B_asian_predictor, 5C_london_ny_relationship, 5D_volatility_by_hour |
| 6: Cross-Instrument | microstructure_stream6_cross_instrument_20260405.json | 2.7 KB | 6A_correlation, 6B_divergence_signal, 6C_sweep_timing |

---

## 7. Raw Candle Data Coverage

### CRITICAL: XAUUSD and GBPUSD have TINY recent-only data

| File | Rows | Start | End | Size | Notes |
|------|------|-------|-----|------|-------|
| **XAUUSD_D1** | **60** | 2026-01-09 | 2026-04-02 | 3.8 KB | **~3 months only** |
| **XAUUSD_H1** | **200** | 2026-03-23 | 2026-04-02 | 12 KB | **~10 days only** |
| **XAUUSD_H4** | **120** | 2026-03-06 | 2026-04-02 | 7.4 KB | **~1 month only** |
| **XAUUSD_M15** | **700** | 2026-03-24 | 2026-04-02 | 42 KB | **~10 days only** |
| **XAUUSD_M5** | **300** | 2026-04-01 | 2026-04-02 | 18 KB | **~2 days only** |
| **GBPUSD_D1** | **60** | 2026-01-12 | 2026-04-03 | 4.0 KB | **~3 months only** |
| **GBPUSD_H1** | **200** | 2026-03-24 | 2026-04-03 | 13 KB | **~10 days only** |
| **GBPUSD_H4** | **120** | 2026-03-06 | 2026-04-03 | 7.8 KB | **~1 month only** |
| **GBPUSD_M15** | **700** | 2026-03-25 | 2026-04-03 | 45 KB | **~10 days only** |
| **GBPUSD_M5** | **300** | 2026-04-02 | 2026-04-03 | 19 KB | **~1 day only** |

### Full-history CSVs (used by analysis scripts via historical_data_loader.py)

| File | Rows | Start | End | Size |
|------|------|-------|-----|------|
| EURUSD_D1 | 586 | 2024-01-02 | 2026-04-03 | 29 KB |
| EURUSD_H1 | 13,976 | 2024-01-02 | 2026-04-03 | 795 KB |
| EURUSD_H4 | 3,502 | 2024-01-02 | 2026-04-03 | 201 KB |
| EURUSD_M15 | 55,864 | 2024-01-02 | 2026-04-03 | 3.1 MB |
| EURUSD_M5 | 90,000 | 2025-01-16 | 2026-04-03 | 5.0 MB |
| NAS100_D1 | 545 | 2024-01-02 | 2026-04-03 | 28 KB |
| NAS100_H1 | 12,348 | 2024-01-02 | 2026-04-03 | 715 KB |
| NAS100_H4 | 3,239 | 2024-01-02 | 2026-04-03 | 189 KB |
| NAS100_M15 | 49,215 | 2024-01-02 | 2026-04-02 | 2.8 MB |
| NAS100_M5 | 90,000 | 2024-10-24 | 2026-04-03 | 5.0 MB |
| XAGUSD_D1 | 583 | 2024-01-02 | 2026-04-02 | 26 KB |
| XAGUSD_H1 | 13,471 | 2024-01-02 | 2026-04-02 | 693 KB |
| XAGUSD_H4 | 3,495 | 2024-01-02 | 2026-04-02 | 182 KB |
| XAGUSD_M15 | 53,789 | 2024-01-02 | 2026-04-02 | 2.7 MB |
| XAGUSD_M5 | 90,000 | 2024-12-31 | 2026-04-02 | 4.4 MB |
| DXY_D1 | 515 | 2024-02-29 | 2026-04-02 | 19 KB |
| economic_calendar | 31 | 2026-04-01 | 2026-05-27 | 1.5 KB |

**Key insight:** XAUUSD/GBPUSD CSVs in `data/` are rolling MT5 live-feed buffers (~60-700 rows). The analysis scripts (displacement scanner, OB retest, etc.) use `historical_data_loader.py` which loads from TradingView CSV exports — those appear to be the EURUSD/NAS100/XAGUSD files, but **the original XAUUSD/GBPUSD historical CSVs that the analysis scripts used are NOT currently in `data/`** — the analysis scripts likely loaded them when they existed, and the files were later replaced by MT5's rolling buffer.

**Column schemas differ:** EURUSD/NAS100/XAGUSD use `[time, open, high, low, close, volume]`. XAUUSD/GBPUSD use MT5 format `[time, open, high, low, close, tick_volume, spread, real_volume]`.

---

## 8. Configuration

**Path:** `config/agent_config.yaml`
**Size:** ~5.5 KB
**Instruments configured:** XAUUSD, GBPUSD, EURUSD, NAS100, XAGUSD
**Deployment phase:** 2 (paper)
**Primary model:** claude-sonnet-4-20250514
**Enabled frameworks:** ob_retest only

---

## 9. Prompt Files

| File | Path |
|------|------|
| Primary Analyzer | src/prompts/primary_analyzer_prompt.py (29 KB) |
| Bull Agent | src/prompts/bull_agent_prompt.py |
| Bear Agent | src/prompts/bear_agent_prompt.py |
| Judge | src/prompts/judge_prompt.py |
| Postmortem | src/prompts/postmortem_prompt.py |
| Short validation batch | prompts/short_validation_batch_prompt.md |

---

## 10. Live Sessions

**Count:** 0
No live session files found yet.

---

## 11. Scripts (30 total)

| Script | Size | Purpose |
|--------|------|---------|
| batch_backtest.py | 52 KB | Anthropic batch API backtesting |
| backtest_runner.py | 48 KB | Single-threaded backtest harness |
| replay_session.py | 35 KB | Historical session replay |
| historical_data_loader.py | 32 KB | TradingView CSV / MT5 data loader |
| ob_retest_comprehensive.py | 70 KB | OB retest analysis (produced Section 3) |
| ob_retest_pressure_test.py | 55 KB | OB retest validation |
| smc_phase_b_comprehensive.py | 56 KB | FVG/breaker/equal HL analysis |
| unconstrained_edge_discovery.py | 50 KB | Feature mining on displacement DB |
| edge_discovery_d1unclear.py | 76 KB | Edge discovery for D1-unclear days |
| edge_discovery_pressure_test.py | 35 KB | Edge discovery validation |
| microstructure_stream1_sweeps.py | 25 KB | Sweep atlas generator |
| microstructure_stream5_6.py | 27 KB | Session dynamics + cross-instrument |
| smc_a1_silver_bullet.py | 12 KB | Silver bullet timing analysis |
| smc_a2_judas_swing.py | 17 KB | AMD/Judas swing analysis |
| smc_a3_ote_zone.py | 13 KB | OTE zone validation |
| smc_a4_consolidation.py | 18 KB | Consolidation predictor |
| smc_a5_session_retracement.py | 20 KB | Session range retracement |
| smc_a6_sweep_clustering.py | 17 KB | Double/triple sweep patterns |
| seed_knowledge_base.py | 16 KB | KB seeder from validated data |
| reseed_from_sessions.py | 17 KB | Re-seed KB from session files |
| comprehensive_analysis.py | 55 KB | Unified analysis (legacy) |
| + 9 more... | | |

---

## 12. Analysis Feasibility Matrix

### POSSIBLE analyses (data exists)

| Analysis | Data Source | Key Fields |
|----------|------------|------------|
| Trade R-multiple distribution | trade_index | r_multiple, mfe_r, mae_r |
| Win rate by framework/grade/KZ | trade_index | outcome, framework, grade, kill_zone |
| Displacement continuation rates | displacement_db | cont_3h, direction, kz, session |
| HTF alignment effect on continuation | displacement_db | d1_dir, h4_dir, h4_aligned_d1, cont_3h |
| OTE zone continuation | displacement_db | in_ote, cont_3h |
| Body ratio as quality predictor | displacement_db | body_ratio, cont_3h |
| Sweep level continuation | displacement_db | sweep, sweep_level, cont_3h |
| FVG creation after displacement | displacement_db | creates_fvg, fvg_size, cont_3h |
| Origin revisited analysis | displacement_db | origin_revisited, revisit_depth, revisit_mfe |
| Hour-of-day continuation heatmap | displacement_db | timestamp (extract hour), cont_3h |
| Day-of-week effects | displacement_db | dow, cont_3h |
| Consolidation as predictor | displacement_db | tight, consol, cont_3h |
| OB retest feature importance | ob_comprehensive | feature_ranking (pre-computed chi2) |
| Sweep timing patterns | sweep_atlas | per-sweep records with timestamps |
| Post-sweep behavior (MFE) | sweep_atlas | post_sweep_behavior data |

### BLOCKED analyses (data gaps)

| Analysis | Missing Data | Workaround |
|----------|-------------|------------|
| Per-trade structural features | trade_index lacks entry_price, HTF direction, OB features | Join trade dates with displacement_db by date+kz? Lossy. |
| Per-OB retest outcomes | ob_comprehensive is aggregate only | Re-run ob_retest_comprehensive.py with per-record output |
| Per-FVG fill outcomes | fvg_comprehensive is aggregate only | Re-run smc_phase_b_comprehensive.py with per-record output |
| GBPUSD displacement analysis | displacement_db is XAUUSD only | Build GBPUSD displacement DB from GBPUSD candle data |
| Historical candle walk analysis | XAUUSD/GBPUSD CSVs are tiny rolling buffers | Need to re-export full history from TradingView or MT5 |
| Trade direction analysis | direction field is ALL NULL | Parse from session files or batch API responses |
| Cross-trade feature correlation | No per-trade features | Need enriched trade index |

### SURPRISES / INCONSISTENCIES

1. **`direction` field is ALL NULL** in the trade index — 129 trades have no long/short recorded
2. **XAUUSD/GBPUSD CSVs are tiny** (~60-700 rows) vs EURUSD/NAS100/XAGUSD (thousands of rows) — suggests MT5 rolling buffer replaced historical exports
3. **Displacement DB is XAUUSD only** — no GBPUSD displacement records despite GBPUSD being a traded instrument
4. **OB comprehensive and FVG comprehensive are aggregate-only** — no way to slice/regroup without re-running the scripts
5. **1 trade has no mfe_r/mae_r/hold_time/exit_type** (99.2% coverage = 128/129)
6. **Trade index has no per-trade features** — cannot correlate trade outcomes with structural properties without joining external data

---

*Generated 2026-04-06. Read-only inventory session — no data was modified.*
