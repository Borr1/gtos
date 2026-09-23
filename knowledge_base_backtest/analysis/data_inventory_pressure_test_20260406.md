# Data Inventory Pressure Test — 2026-04-06

## Overall Verdict: PASS WITH NOTES

No critical failures. Inventory is accurate on all verified dimensions. Three notes requiring attention.

---

## Summary Table

| Test | Verdict | Details |
|------|---------|---------|
| T1: File Completeness | PASS | 219 analysis files matched exactly. +2 self-referential (inventory files). |
| T2: Trade Index | PASS | 129 records, 15 fields, all coverage %s match, samples verified. |
| T3: OB Comprehensive | PASS w/note | Aggregate confirmed. 1520 OBs match. has_freshness semantically ambiguous. |
| T4: FVG Comprehensive | PASS | Aggregate confirmed. FVG counts exact match. No dates confirmed. |
| T5: Displacement DB | PASS | 6641 records, 94 fields, all critical fields confirmed, sample exact match. |
| T6: Candle CSVs | PASS | All 27 CSVs verified: rows, columns, date ranges, gap counts all match. |
| T7: Cross-Reference | PASS | 0 contradictions found across all cross-checks. |
| T8: Analysis Feasibility | PASS | 19 possible, 7 blocked, 2 partial, 2 blocked-on-Windows. |
| T9: Expected Files | PASS w/notes | All 27 expected files found on disk. 5 outside inventory scope (by design). |

---

## Notes Requiring Attention

### Note 1: Session Files Not Inventoried

**331 session JSON files** in `knowledge_base_backtest/sessions/` were not cataloged. These contain:
- Per-session trade outcomes (same lean format as trade index — no entry_price, no direction)
- Per-candle evaluations with decision/confidence/grade/framework
- Pre-session context (D1/H4 directions may be here)

**Impact:** The session files are the raw source data for the trade index. While they don't add new fields beyond what's in the trade index, the candle evaluations contain confidence scores and grades that could enable additional analysis.

### Note 2: has_freshness Semantics

The inventory reports `has_freshness: False` for OB comprehensive. This is technically correct (no per-OB freshness data), but `freshness_candles` IS one of the 16 features in the chi-squared ranking. A reader might wrongly conclude freshness wasn't analyzed.

### Note 3: Rolling Stats + Failure Patterns

`knowledge_base/statistics/rolling_stats.json` and `knowledge_base/patterns/failure_patterns.json` exist on disk but aren't mentioned in the inventory's main narrative. They're in the JSON (under the KB file listing) but not prominently surfaced.

---

## Test 1: File Completeness

| Metric | Value |
|--------|-------|
| Analysis files on disk | 221 |
| Analysis files in inventory | 219 |
| Delta | +2 (the inventory files themselves) |
| Missing from inventory | 0 |
| Stale in inventory | 0 |

Additional directories NOT in inventory scope:
- `knowledge_base_backtest/sessions/` — 331 session JSONs
- `knowledge_base_backtest/batch_api/` — 53 batch API JSONs + prompt files
- `knowledge_base_backtest/batch_results/` — 2 progress files

**Verdict: PASS** — All analysis files correctly captured.

---

## Test 2: Trade Index Accuracy

| Check | Result |
|-------|--------|
| Record count | 129 = 129 |
| Field count | 15 = 15 |
| Missing fields | 0 |
| r_multiple coverage | 100.0% vs 100.0% MATCH |
| mfe_r coverage | 99.2% vs 99.2% MATCH |
| mae_r coverage | 99.2% vs 99.2% MATCH |
| kill_zone coverage | 100.0% vs 100.0% MATCH |
| grade coverage | 100.0% vs 100.0% MATCH |
| Sample winner verified | Exact match on trade_id + all fields |
| Sample loser verified | Exact match on trade_id + all fields |
| XAUUSD count | 105 = 105 |
| GBPUSD count | 24 = 24 |
| Chronological | True = True |
| Date range | [2024-03-01, 2026-03-13] = [2024-03-01, 2026-03-13] |

**Additional finding:** Session files contain the same lean trade format — `direction` is absent everywhere (not just NULL in the trade index, it was never captured by the pipeline).

**Verdict: PASS**

---

## Test 3: OB Comprehensive Granularity

| Check | Result |
|-------|--------|
| Granularity claim | "aggregate" — CORRECT |
| Per-record arrays found | None (largest array is feature_ranking at 16 elements) |
| Total OBs | 1520 = 1520 |
| Top-level keys match | 12 = 12 |
| Feature count | 16 = 16 |
| has_retracement_pct | False = False |
| has_price_zones | False = False |
| has_freshness | False = False (but freshness_candles IS a ranked feature) |
| has_body_range_ratio | True = True |
| has_causing_event_type | True = True |

**Verdict: PASS WITH NOTE** (has_freshness semantics)

---

## Test 4: FVG Comprehensive Granularity

| Check | Result |
|-------|--------|
| Granularity claim | "aggregate" — CORRECT |
| Top-level keys | 6 = 6 (match) |
| FVG fill XAUUSD n | 1783 = 1783 |
| FVG fill GBPUSD n | 1827 = 1827 |
| has_dates | False = False |
| Per-record fields | None — CORRECT |

**Verdict: PASS**

---

## Test 5: Displacement DB

| Check | Result |
|-------|--------|
| Record count | 6641 = 6641 |
| Field count | 94 = 94 |
| Fields set match | Exact match (0 missing, 0 extra) |
| Sample record | Exact match by timestamp |
| cont_3h | bool, exists |
| in_ote | bool, exists |
| set values | {disc, val} — matches |
| Instrument | XAUUSD (prices 2235-5561) |

**Verdict: PASS**

---

## Test 6: Candle CSVs

All 27 CSV files verified independently:

| Check | Result |
|-------|--------|
| All files exist | 27/27 |
| Row counts match | 27/27 |
| Column names match | 27/27 |
| Date ranges match | 27/27 |
| M15 gap counts match | N/A (no gaps reported in inventory, none found) |

**Verdict: PASS**

---

## Test 7: Cross-Reference Consistency

| Check | Result |
|-------|--------|
| 129 = 105 + 24 | PASS |
| 1520 = 820 + 700 | PASS |
| Displacement count = 6641 | PASS |
| Live sessions = 0 | PASS |
| Displacement DB noted XAUUSD-only | PASS |
| Trade dates vs CSV dates | Expected mismatch (rolling buffer) |

**Contradictions found: 0**

**Verdict: PASS**

---

## Test 8: Analysis Feasibility Matrix

### POSSIBLE (19 analyses)

| # | Analysis | Data Source | Key Fields |
|---|----------|------------|------------|
| 1 | Monte Carlo simulation | trade_index | r_multiple |
| 2 | Rolling edge stability | trade_index | r_multiple + date |
| 3 | Trade autocorrelation | trade_index | outcome sequence |
| 4 | Drawdown duration | trade_index | r_multiple + date |
| 5 | DOW x KZ matrix | trade_index | kill_zone + date |
| 6 | Failed origin revisit | displacement_db | origin_revisited + cont_3h |
| 7 | GBPUSD FVG gap investigation | fvg_comprehensive | per-instrument aggregates |
| 8 | HTF alignment effect | displacement_db | d1_dir, h4_dir, h4_aligned_d1, cont_3h |
| 9 | OTE zone continuation | displacement_db | in_ote, cont_3h |
| 10 | Body ratio predictor | displacement_db | body_ratio, cont_3h |
| 11 | Sweep level continuation | displacement_db | sweep, sweep_level, cont_3h |
| 12 | FVG creation after displacement | displacement_db | creates_fvg, fvg_size, cont_3h |
| 13 | Origin revisited analysis | displacement_db | origin_revisited, revisit_depth, revisit_mfe |
| 14 | Hour-of-day heatmap | displacement_db | timestamp, cont_3h |
| 15 | Day-of-week effects | displacement_db | dow, cont_3h |
| 16 | Consolidation as predictor | displacement_db | tight, consol, cont_3h |
| 17 | OB retest feature importance | ob_comprehensive | pre-computed chi2 ranking |
| 18 | Sweep timing patterns | sweep_atlas | per-sweep records |
| 19 | Post-sweep behavior | sweep_atlas | post_sweep_behavior data |

### BLOCKED (7 analyses)

| # | Analysis | Blocker |
|---|----------|---------|
| 1 | Continuous retracement curve | OB comprehensive is aggregate — no per-OB retracement data |
| 2 | First-candle momentum | No entry_time anywhere. XAUUSD M15 only 700 rows |
| 3 | MFE time-profile | No entry_time. Tiny M15 CSV |
| 4 | Impulse leg character | OB aggregate. XAUUSD H1 only 200 rows |
| 5 | FVG vs OB date overlap | Both aggregate — no per-event dates |
| 6 | Regime classification | XAUUSD D1 only 60 rows from 2026. Need full history |
| 7 | BE stop optimization | No entry_time. XAUUSD M15 only 700 rows |

### PARTIAL (2 analyses)

| # | Analysis | Limitation |
|---|----------|-----------|
| 1 | Logistic regression | 10 features available but all outcome/metadata — no structural features |
| 2 | Economic calendar tagging | Calendar only covers 2026-04-01 onward, not backtest period |

### BLOCKED ON WINDOWS (2 analyses)

| # | Analysis | Needs |
|---|----------|-------|
| 1 | Spread at entry | MT5 tick data export |
| 2 | Full economic calendar | MT5 calendar export |

**Key insight:** The displacement_db is the richest analysis source (6641 records, 94 fields). Most blocked analyses need either per-record data from aggregate files or historical candle CSVs overwritten by MT5.

**Verdict: PASS** — Every analysis correctly categorized.

---

## Test 9: Expected Files

| File | Status |
|------|--------|
| INDEX.md | In inventory |
| data_exploitation_20260405.json/md | In inventory |
| microstructure_master_20260405.json | In inventory |
| microstructure_stream1-6 (all 6) | In inventory |
| ob_retest_comprehensive_20260405.json | In inventory |
| smc_*.json (all 7 SMC files) | In inventory |
| smc_event_comprehensive_20260405.md | In inventory |
| smc_event_pressure_test_20260405.json | In inventory |
| config/agent_config.yaml | In inventory (config section) |
| src/prompts/primary_analyzer_prompt.py | In inventory (prompt section) |
| rolling_stats.json | On disk, not in analysis inventory (KB scope) |
| failure_patterns.json | On disk, not in analysis inventory (KB scope) |
| src/components/market_state.py | On disk, not in scope (source code) |
| src/components/verification.py | On disk, not in scope (source code) |
| docs/preflight_checklist.md | On disk, not in scope (documentation) |

**Genuinely missing: 0**

**Verdict: PASS WITH NOTES** — 5 files outside inventory scope are on disk and accessible.

---

*Pressure test completed 2026-04-06. Inventory verified as accurate and complete within stated scope.*
