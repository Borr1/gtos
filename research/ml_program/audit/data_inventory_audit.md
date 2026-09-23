# K54 v2 — Data Inventory Audit

**Auditor:** Data Inventory Auditor (Opus 4.7, max effort)
**Date:** 2026-04-28
**Scope:** Q1.2 hypothesis (per-regime LightGBM AUC ≥0.61, n=582 trades; cross-instrument ≥4/7; cross-period ≥2/3)
**Output dir:** `research/ml_program/audit/`
**Auxiliary CSVs:** `coverage_table.csv`, `m15_per_period.csv`, `trade_cohort.csv`, `d1_direction.csv`, `d1_5bar_ohlcv_distribution.csv`, `d1_5bar_trade_cohort.csv`
**Driver scripts:** `_audit_run.py`, `_d1_5bar_analysis.py`
**Data cutoff respected:** ≤2026-04-28; no live holdout (2026-04-29 → 2026-05-12) accessed.

---

## Section 1 — Per-instrument per-TF coverage table

For each of 7 instruments × 4 TFs (M15, H1, H4, D1), the **best (longest-history) source** found across `data/historical/`, `data/historical_2026/`, `data/`, `data/raw/`, `data/old_huggingface_backup/`. Full multi-source table in `coverage_table.csv` (68 rows). Best-source summary:

| Symbol | TF | Rows | First | Last | Gaps | Source |
|---|---|---:|---|---|---:|---|
| XAUUSD | M15 | 48,359 | 2024-04-01 01:00 | 2026-04-17 23:15 | 111 | `data/historical/XAUUSD_M15.csv` |
| XAUUSD | H1 | 15,020 | 2023-10-02 01:00 | 2026-04-17 23:00 | 134 | `data/historical/XAUUSD_H1.csv` |
| XAUUSD | H4 | 4,629 | 2023-03-31 20:00 | 2026-03-30 16:00 | 156 | `data/historical/XAUUSD_H4.csv` |
| XAUUSD | D1 | 772 | 2023-04-03 | 2026-03-30 | 0 | `data/historical/XAUUSD_D1.csv` |
| XAGUSD | M15 | 53,789 | 2024-01-02 01:00 | 2026-04-02 22:45 | 121 | `data/XAGUSD_M15.csv` |
| XAGUSD | H1 | 13,471 | 2024-01-02 01:00 | 2026-04-02 22:00 | 121 | `data/XAGUSD_H1.csv` |
| XAGUSD | H4 | 3,495 | 2024-01-02 00:00 | 2026-04-02 20:00 | 118 | `data/XAGUSD_H4.csv` |
| XAGUSD | D1 | 583 | 2024-01-02 | 2026-04-02 | 0 | `data/XAGUSD_D1.csv` |
| USDJPY | M15 | 50,970 | 2024-03-31 23:45 | 2026-04-17 23:15 | 110 | `data/historical/USDJPY_M15.csv` |
| USDJPY | H1 | 20,243 | 2023-01-16 13:00 | 2026-04-17 23:00 | 171 | `data/historical/USDJPY_H1.csv` |
| USDJPY | H4 | 10,000 | 2019-10-30 18:00 | 2026-04-03 17:00 | 336 | `data/historical/USDJPY_H4.csv` |
| USDJPY | D1 | 3,000 | 2014-09-09 21:00 | 2026-04-02 21:00 | 0 | `data/historical/USDJPY_D1.csv` |
| GBPJPY | M15 | **100,967** | **2022-03-28 11:00** | 2026-04-17 23:15 | 212 | `data/historical/GBPJPY_M15.csv` |
| GBPJPY | H1 | 20,243 | 2023-01-16 13:00 | 2026-04-17 23:00 | 171 | `data/historical/GBPJPY_H1.csv` |
| GBPJPY | H4 | 10,000 | 2019-10-30 20:00 | 2026-04-03 20:00 | 336 | `data/historical/GBPJPY_H4.csv` |
| GBPJPY | D1 | 3,000 | 2014-09-10 | 2026-04-03 | 0 | `data/historical/GBPJPY_D1.csv` |
| GBPUSD | M15 | 50,970 | 2024-03-31 23:45 | 2026-04-17 23:15 | 110 | `data/historical/GBPUSD_M15.csv` |
| GBPUSD | H1 | 20,243 | 2023-01-16 13:00 | 2026-04-17 23:00 | 171 | `data/historical/GBPUSD_H1.csv` |
| GBPUSD | H4 | 10,000 | 2019-10-30 18:00 | 2026-04-03 17:00 | 336 | `data/historical/GBPUSD_H4.csv` |
| GBPUSD | D1 | 3,000 | 2014-09-09 21:00 | 2026-04-02 21:00 | 0 | `data/historical/GBPUSD_D1.csv` |
| US30_cash | M15 | **100,929** | **2022-01-06 02:15** | 2026-04-17 23:15 | 253 | `data/historical/US30_cash_M15.csv` |
| US30_cash | H1 | 20,233 | 2022-11-10 16:00 | 2026-04-17 23:00 | 201 | `data/historical/US30_cash_H1.csv` |
| US30_cash | H4 | 10,000 | 2019-10-15 13:00 | 2026-04-03 13:00 | 330 | `data/historical/US30_cash_H4.csv` |
| US30_cash | D1 | 1,828 | 2019-02-07 22:00 | 2026-04-02 21:00 | 0 | `data/historical/US30_cash_D1.csv` |
| NAS100 | M15 | 49,215 | 2024-01-02 01:00 | 2026-04-02 23:45 | 129 | `data/NAS100_M15.csv` |
| NAS100 | H1 | 12,348 | 2024-01-02 01:00 | 2026-04-03 01:00 | 127 | `data/NAS100_H1.csv` |
| NAS100 | H4 | 3,239 | 2024-01-02 00:00 | 2026-04-03 00:00 | 108 | `data/NAS100_H4.csv` |
| NAS100 | D1 | 545 | 2024-01-02 | 2026-04-03 | 0 | `data/NAS100_D1.csv` |

### Coverage notes
1. **No instrument is missing any TF.** All 7 × 4 = 28 (instrument, TF) cells are populated.
2. **Pre-2024 M15 coverage exists for only 2 of 7 instruments**: GBPJPY (from 2022-03-28) and US30_cash (from 2022-01-06). XAUUSD/XAGUSD/USDJPY/GBPUSD/NAS100 M15 starts in **2024**.
3. **D1 history is much longer than M15** for FX majors (USDJPY/GBPJPY/GBPUSD: 2014→present, 3000 daily bars; XAUUSD: 2023-04→present, 772 bars). M15 is the binding constraint for cross-period replication.
4. **The K54 v1 audit's caveat (§7) is partially refuted.** Audit said "pre-2024 data has only XAUUSD/GBPUSD coverage". Empirically: pre-2024 **M15** has only **GBPJPY + US30_cash** (XAUUSD/GBPUSD M15 do NOT extend pre-2024). The audit's claim refers to the *trade cohort*, not OHLCV — see Section 3.
5. **`historical_2026/` is a thin partial export** (2025-10-01 → 2026-04-24, ~14k M15 bars per instrument). Not a substitute for `data/historical/` for cross-period work; supersedes only for the recent 7-month tail.
6. **Gap counts** are non-zero on most sub-daily TFs but reflect normal weekend/holiday gaps + occasional broker-server outages (5× median spacing, capped at 60h to avoid weekend false positives). Gap density is similar across instruments (~0.2-0.5% of bars), no anomalous black-out periods.
7. **Tick (M1) data exists** in `data/historical_2026/` for all 7 instruments (Apr-28 timestamps, 5-6 MB each), but is M1 not M15 and only covers the recent tail. Microstructure family treats M1 as Phase-2 enhancement, not core to v2 hypothesis.

---

## Section 2 — Cross-period replication feasibility verdict

### Per-period M15 candle counts (`m15_per_period.csv`)

| Symbol | 2022-2023 | 2024-2025 | 2026 | Periods ≥1000 |
|---|---:|---:|---:|---:|
| XAUUSD | 0 | 92,148 | 14,891 | **2** |
| XAGUSD | 0 | 53,684 | 13,387 | **2** |
| USDJPY | 0 | 49,901 | 15,082 | **2** |
| GBPJPY | **43,852** | 56,052 | 15,072 | **3** |
| GBPUSD | 0 | 49,901 | 15,082 | **2** |
| US30_cash | **46,817** | 53,063 | 14,328 | **3** |
| NAS100 | 0 | 49,234 | 13,265 | **2** |

### Verdict (cross-period replication, per brief gate)

The brief's cross-period gate ("test on ≥2 of 3 periods") has two interpretations:

**Interpretation A — train-on-historical, test-on-2026 (the original brief intent):**
- "Train on 2022-2025, test on 2026" requires data in **both** {2022-2023 or 2024-2025} and {2026} for each instrument.
- All 7 of 7 instruments meet this interpretation (≥1000 candles in both 2024-2025 AND 2026). **Feasible: 7/7.**
- BUT this collapses to "train on 2024-2025, test on 2026" for 5 of 7 (no 2022-2023 data).

**Interpretation B — proper 3-period replication (2022-2023 → 2024-2025 → 2026 walk-forward):**
- Requires data in **all 3 periods** with ≥1000 candles.
- Only **GBPJPY** and **US30_cash** meet this. **Feasible: 2/7.**
- This is the only interpretation that lets K54 v2 distinguish "edge replicates across regimes" from "edge survives one walk-forward year".

**Q1.2 cross-period gate verdict (≥2 of {2022-2023, 2024-2025, 2026}): feasible on 7/7 instruments under Interpretation A; 2/7 under Interpretation B.**

The K54 v2 modeler should use Interpretation A as the primary gate (matches the brief's "train on 2022-2025, test on 2026") and treat Interpretation B as a stretch goal restricted to GBPJPY/US30_cash. **The 2 of 7 figure is the more honest representation of "cross-period generalization" because the 5-of-7 fall back to a single walk-forward (2024-2025 → 2026), not true cross-period replication.**

### Caveat — alignment with cross-instrument gate
The Phase-2 brief's cross-instrument gate is "works on ≥4 of 7 instruments". Under Interpretation B, only 2 instruments can be tested on the strict cross-period gate, so the cross-instrument gate must use Interpretation A. **Recommendation: report both interpretations in K54 v2 final card.**

---

## Section 3 — Per-instrument trade-cohort distribution

### Total cohort size — discrepancy with brief

The brief states "411 trades in K54 v1's F14-extended dataset". **The actual K54 v1 `features.csv` (committed at `.claude/worktrees/agent-a01c00db65592ac2b/research/k54_ml_classifier_baseline/features.csv`) contains 582 rows (583 lines incl. header).** The K54 v1 audit (`research/ml_program/k54_v1_audit.md:295`) explicitly flags this exact discrepancy: "memory says 'F14-extended dataset (8086 H1 windows + 411 trades)'. This is incorrect: K54 v1 actually used 582 rows from 3 sources (439 F11 + 33 trade_index + 110 unified_csv), and 411 ≈ rows after deduping the F11 source roughly (memory probably meant 439). The 8086 H1 windows figure refers to the F11 BOS event count, NOT trades."

**This audit reports against the canonical 582 rows, not the brief's 411.** All distributions below are computed from `features.csv` (582 rows) directly.

### By source (`scripts/k54_build_features.py:80-83` data sources)

| Source | Rows | Path |
|---|---:|---|
| `f11_mechanical` | 439 | `research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl` |
| `unified_csv` | 110 | `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv` |
| `trade_index` | 33 | `knowledge_base/index/_trade_index.json` |
| **Total** | **582** | |

### By symbol

| Symbol | Trades | % |
|---|---:|---:|
| XAUUSD | 191 | 32.8% |
| GBPUSD | 74 | 12.7% |
| USDJPY | 74 | 12.7% |
| GBPJPY | 66 | 11.3% |
| US30_cash | 66 | 11.3% |
| NAS100 | 57 | 9.8% |
| XAGUSD | 54 | 9.3% |

### By symbol × period

| Symbol | 2022-2023 | 2024-2025 | 2026 | Total |
|---|---:|---:|---:|---:|
| XAUUSD | 0 | **108** | 83 | 191 |
| GBPUSD | 0 | 6 | 68 | 74 |
| USDJPY | 0 | 0 | 74 | 74 |
| GBPJPY | 0 | 0 | 66 | 66 |
| US30_cash | 0 | 0 | 66 | 66 |
| NAS100 | 0 | 0 | 57 | 57 |
| XAGUSD | 0 | 0 | 54 | 54 |
| **Total** | **0** | **114** | **468** | **582** |

**Observations:**
- **Zero trades pre-2024** in the K54 v1 trade cohort. The K54 v1 audit's "pre-2024 data has only XAUUSD/GBPUSD coverage" claim is wrong by sign — pre-2024 data has **no** trades at all in this cohort.
- 2024-2025 trades: 114 total (108 XAUUSD + 6 GBPUSD only). The other 5 instruments contribute zero pre-2026.
- 2026 trades dominate: 468 of 582 = 80.4% of the cohort.

### By symbol × source

| Symbol | f11_mechanical | trade_index | unified_csv | Total |
|---|---:|---:|---:|---:|
| XAUUSD | 54 | 28 | 109 | 191 |
| GBPUSD | 68 | 5 | 1 | 74 |
| USDJPY | 74 | 0 | 0 | 74 |
| GBPJPY | 66 | 0 | 0 | 66 |
| US30_cash | 66 | 0 | 0 | 66 |
| NAS100 | 57 | 0 | 0 | 57 |
| XAGUSD | 54 | 0 | 0 | 54 |
| **Total** | **439** | **33** | **110** | **582** |

(Computed directly from `features.csv` rows; columns sum across to symbol totals. ✓)

**Observations:**
- All 5 non-XAU/GBPUSD instruments come **exclusively** from F11 mechanical population — no AI-graded trades, no batch simulator runs.
- XAUUSD has the most heterogeneous source mix (3-source) AND is the dominant unified_csv contributor (109 of 110 unified_csv rows are XAUUSD).
- GBPUSD has 3-source but mostly F11 (68 of 74); only 5 trade_index + 1 unified_csv.

### By regime tag (low-N flags at n<30)

| Symbol | UNTAGGED | bullish | bearish | transitional |
|---|---:|---:|---:|---:|
| XAUUSD | 129 | 39 | 7 [LOW-N] | 16 [LOW-N] |
| GBPUSD | 17 [LOW-N] | 13 [LOW-N] | 24 [LOW-N] | 20 [LOW-N] |
| USDJPY | 13 [LOW-N] | 38 | 2 [LOW-N] | 21 [LOW-N] |
| GBPJPY | 7 [LOW-N] | 25 [LOW-N] | 8 [LOW-N] | 26 [LOW-N] |
| US30_cash | 66 | 0 | 0 | 0 |
| NAS100 | 6 [LOW-N] | 9 [LOW-N] | 26 [LOW-N] | 16 [LOW-N] |
| XAGUSD | 5 [LOW-N] | 20 [LOW-N] | 13 [LOW-N] | 16 [LOW-N] |

**Per-cell n<30 statistical-power deficit:** **22 of 28 (symbol × regime) cells fail n≥30.** Only 6 cells have ≥30 trades:
- XAUUSD bullish (n=39) — only XAU regime cell that survives
- XAUUSD UNTAGGED (n=129) — pre-2026 cohort, no regime backfill
- USDJPY bullish (n=38)
- US30_cash UNTAGGED (n=66) — entire US30 cohort is untagged (no regime backfill match)
- *(none for XAG, GBPJPY, GBPUSD, NAS100, XAGUSD)*

**The K54 v2 per-regime model proposal hits a hard sample-size wall:** ML training per (symbol × regime) combination has insufficient n for 22 of 28 cells. The K54 v1 design (`k54_train.py:189-208`) handles this with `--min-regime-rows 20` fallback to global model — but at n=20, signal is dominated by noise.

**For K54 v2, this means:**
- Per-regime models are only viable for global-regime ensembles (regime as feature, not gate). The "regime as gate" approach used by K54 v1 will train noise classifiers on most cells.
- A pooled cross-instrument model is the only path to per-regime n≥30. But that contradicts F15's "regime is load-bearing" finding because regime semantics differ across instruments.
- Cross-period extension (Section 2) is the only fix. Pulling 2022-2023 data into the cohort *requires* generating new mechanical OB-retest labels from 2022-2023 OHLCV.

### UNTAGGED cohort breakdown (243 of 582 = 41.8%)

The UNTAGGED rows are those whose `(symbol, H4 timestamp)` did not match the F4-format regime backfill (`shadow_logs/structure_detector_backfill_2026.jsonl`, which begins 2026-01-21 per the first record). Distribution:
- XAUUSD UNTAGGED 129: ~all pre-2026 (108 from 2024-2025, 21 from 2026 outside backfill window).
- US30_cash UNTAGGED 66: 100% — backfill has no US30_cash entries, only EURUSD/XAUUSD/GBPUSD/etc per spot-check.
- GBPUSD UNTAGGED 17, USDJPY 13, NAS100 6, XAGUSD 5, GBPJPY 7.

**K54 v2 critical gap:** the regime backfill needs cross-instrument extension to all 7 instruments × multi-period coverage before per-regime modeling can work cleanly. The current backfill is XAUUSD-centric and 2026-only.

---

## Section 4 — D1 direction distribution + MTF rescue verdict

### Two views computed

The catalog feature `regime_d1_direction_bullish` is defined at `feature_catalogs/CATALOG_v2.csv:1212` as **D1 close[i] vs close[i-5] > +0.5%** (5-bar lookback, ±0.5% deadband). Two distributions matter:

**(A) Per-period OHLCV-derived distribution** (all D1 candles in period):
File: `d1_5bar_ohlcv_distribution.csv`. Tells us whether the OHLCV regime backbone has variance.

**(B) Trade-cohort-aligned distribution** (D1 5-bar direction at each trade timestamp):
File: `d1_5bar_trade_cohort.csv`. Tells us whether the MTF feature has variance *as it appears to the K54 model*.

### View A — D1 5-bar OHLCV distribution (% bull / % bear / % neutral)

| Symbol | 2022-2023 | 2024-2025 | 2026 |
|---|---|---|---|
| XAUUSD | 36.7 / 36.7 / 26.6 (n=188) | 54.7 / 25.5 / 19.7 (n=517) | **56.5 / 38.7 / 4.8 (n=62)** **[VARIANCE-STARVED]** |
| XAGUSD | n/a | 56.4 / 32.4 / 11.1 (n=512) | **54.5 / 40.9 / 4.5 (n=66)** **[VARIANCE-STARVED]** |
| USDJPY | 43.8 / 27.6 / 28.6 (n=518) | 39.1 / 27.4 / 33.5 (n=519) | 48.5 / 21.2 / 30.3 (n=66) |
| GBPJPY | 39.6 / 31.7 / 28.8 (n=518) | 38.3 / 22.2 / 39.5 (n=519) | 30.3 / 25.8 / 43.9 (n=66) |
| GBPUSD | 33.0 / 36.5 / 30.5 (n=518) | 32.0 / 27.7 / 40.3 (n=519) | 16.7 / 40.9 / 42.4 (n=66) |
| US30_cash | 41.3 / 35.5 / 23.3 (n=516) | 47.4 / 29.4 / 23.2 (n=517) | 27.3 / 47.0 / 25.8 (n=66) |
| NAS100 | n/a | 53.8 / 31.4 / 14.8 (n=474) | 27.3 / 53.0 / 19.7 (n=66) |

### View B — D1 5-bar at trade timestamps (trade cohort)

| Symbol | 2024-2025 | 2026 |
|---|---|---|
| XAUUSD | 73.1 / 14.8 / 12.0 (n=108) | **60.2 / 34.9 / 4.8 (n=83)** **[VARIANCE-STARVED]** |
| XAGUSD | n/a | **53.7 / 42.6 / 3.7 (n=54)** **[VARIANCE-STARVED]** |
| USDJPY | n/a | 40.5 / 17.6 / 41.9 (n=74) |
| GBPJPY | n/a | 24.2 / 42.4 / 33.3 (n=66) |
| GBPUSD | 33.3 / 16.7 / 50.0 (n=6) | 16.2 / 48.5 / 35.3 (n=68) |
| US30_cash | n/a | 43.9 / 31.8 / 24.2 (n=66) |
| NAS100 | n/a | 38.6 / 43.9 / 17.5 (n=57) |

### Saturation analysis

**The Structure family's "MTF saturation" claim is REFINED, not refuted:**

1. The original concern (CATALOG_v2.md:73) that "D1 direction is +1 for the entire 2026 gold cohort" is **not literally true**. XAUUSD 2026 trade cohort has 60.2% bull, 34.9% bear, only 4.8% neutral. So the binary `regime_d1_direction_bullish` is +1 on 60% and the binary `regime_d1_direction_bearish` is +1 on 35% — both have variance. **What's saturated is the deadband (neutral / "ranging") class — only 4.8% of XAUUSD 2026 trades fall in the ±0.5% band.**

2. The MTF agreement features that compare H4 vs D1 direction will see XAU-specific variance starvation in the **neutral / "no D1 signal"** category, not in bull/bear. Features like `regime_h4_d1_agreement` (CATALOG_v2.csv:1214) still have variance because H4 swings frequently against the D1 5-bar direction.

3. **Cross-instrument variance is healthier than cross-period.** GBPUSD 2026 trade cohort (16.2 / 48.5 / 35.3) and GBPJPY 2026 (24.2 / 42.4 / 33.3) have well-balanced bull/bear/neutral. The metals (XAU, XAG) are the saturation outliers — they share a sustained 2026 directional run.

### MTF rescue verdict — RESCUED (conditional)

| Verdict layer | Result | Notes |
|---|---|---|
| Cross-period rescue (2022-2023 OHLCV) | **RESCUED for FX + indices** | XAUUSD 2022-2023 D1 5-bar is **36.7 / 36.7 / 26.6** — perfectly balanced. Compare 2026: 56.5 / 38.7 / 4.8. Adding 2022-2023 backfill restores neutral-class variance. **But 2022-2023 OHLCV exists for only GBPJPY + US30_cash for M15, plus all 7 for D1.** D1-only backfill can still inject MTF feature variance on the trade-replication side. |
| Cross-instrument rescue (within 2026) | **RESCUED for non-metals** | GBPUSD/GBPJPY/USDJPY/US30/NAS100 have neutral-class fractions 30-44% in 2026 trade cohort. Pooled cross-instrument cohort dilutes XAU saturation. |
| XAU cohort alone (2026) | **STILL-SATURATED** | XAU + XAG 2026 trade cohorts both <5% neutral. Per-instrument modeling on metals will see variance starvation. |

**Bottom-line MTF verdict for K54 v2:**
- **Pooled cross-instrument cohort: RESCUED.** MTF features have variance in the union of 7 instruments × 2026.
- **Per-instrument XAU/XAG cohort: STILL-SATURATED.** MTF features carry near-zero neutral signal.
- **Cross-period rescue (2022-2023 backfill): RESCUED IF we can synthesize trade labels on pre-2024 OHLCV** (XAUUSD M15 not available pre-2024 → blocks F11-style mechanical labeling for the saturated metals).

**The MTF feature subset survives if K54 v2 trains pooled-instrument and lets LightGBM split-gain at the cells where MTF disagreement exists. It does NOT survive a per-instrument-XAU model, and the 2022-2023 OHLCV escape is partial (covers only D1 lookback, since M15 isn't available pre-2024 for XAU).**

---

## Section 5 — Recommendations for Week 4 modeler

1. **Use the canonical 582-row K54 v1 features.csv** (`worktrees/agent-a01c00db65592ac2b/.../features.csv`), NOT the brief's "411". The K54 v1 audit confirms 582 is correct (439 F11 + 33 trade_index + 110 unified_csv).

2. **Cross-period gate is feasible at 7/7 only under Interpretation A** (train 2024-2025, test 2026). Under Interpretation B (true 3-period replication 2022→2024→2026), only **2/7** — GBPJPY + US30_cash. Report both interpretations on the final v2 card.

3. **Per-regime modeling cannot be the K54 v2 default for n<30 cells.** 22 of 28 (symbol × regime) cells fail n≥30. Path forward:
   - **Do not gate on regime per (instrument, regime).** Use regime as a feature in pooled cross-instrument model.
   - **Reserve per-regime models for the 6 viable cells:** XAUUSD UNTAGGED (n=129), XAUUSD bullish (n=39), USDJPY bullish (n=38), US30_cash UNTAGGED (n=66), and pool remainder into a 4-class regime feature in a global model.
   - **Extend regime backfill to all 7 instruments × multiple periods.** Current backfill is XAUUSD-2026-centric (2026-01-21 onward).

4. **Fix the trade_id-keyed dedup bug** (K54 v1 audit §recommendations.2). 33 trade_index rows are 1:1 duplicates of unified_csv rows with `_xauusd` suffix. Switch to `(date, symbol, direction, framework, realized_r)` tuple-keyed dedup. Expected post-dedup count: ~549 (582 - 33).

5. **Synthesize 2022-2023 trade labels** by running F11 mechanical OB-retest detection on `data/historical/GBPJPY_M15.csv` (43,852 candles, 2022-03 to 2023-12) and `data/historical/US30_cash_M15.csv` (46,817 candles, 2022-01 to 2023-12). Estimated yield: ~50-100 mechanical CANDs per instrument × 2 = ~100-200 additional trade rows. This is the only path to true cross-period replication on at least 2 of 7 instruments.

6. **MTF saturation mitigation:** For the cross-instrument pooled model, MTF features are RESCUED. For per-instrument XAU/XAG models, drop the 14 MTF agreement features OR lower the deadband from ±0.5% to ±0.25% to reclaim some neutral-class variance. (Current 4.8% neutral is below noise-floor for binary feature stability ρ.)

7. **Regime backfill build-out (2022-2023, all 7 instruments)** is a Phase-2 prerequisite. Without it, the per-regime ML hypothesis cannot be tested at the cross-period gate level. The H4 swing detector (`identify_structure(H4)`) needs to run on all 7 instruments for the 2022-2023 H4 OHLCV (which exists for all 7 except XAGUSD/NAS100 → constraint).

8. **Treat XAUUSD-only validation as a known weak corner.** With XAU 2026 trade cohort 4.8% neutral D1 + LONG-side selectivity collapse already documented in F15, a per-XAU model will overfit to the bull-direction collapse. Pooled cross-instrument is the safer baseline and the only path that satisfies the cross-instrument gate (≥4/7 instruments).

9. **Holdout discipline check:** This audit accessed only data ≤2026-04-28; the prospective live holdout 2026-04-29 → 2026-05-12 was not touched. K54 v2 modeler should flag any data refresh that pulls past 2026-04-28 timestamps (live tick capture, FN trades posted after 2026-04-28 23:59 UTC).

10. **Suggested K54 v2 train/test split (cross-period gate Interpretation A):**
   - **Train:** all rows with `date_iso < 2026-01-01` → ~114 rows (XAUUSD 108 + GBPUSD 6). Insufficient on its own.
   - **Augment with synthesized 2022-2023 labels** (item 5 above) → ~250-350 rows.
   - **Test:** 2026 cohort (468 rows) split via CPCV-with-purge (Q1.2 brief's validation method).
   - **Live holdout:** 2026-04-29 → 2026-05-12 opened ONCE.

---

## Methodology notes

- All counts derived from raw CSV row counts (header excluded) and JSON line counts.
- D1 direction methodology (Section 4, View A in `d1_direction.csv`): close>open=bull, close<open=bear, body<25% of range=ranging. This is the H4-swing-style detection (per `_audit_run.py:319`).
- D1 5-bar methodology (Section 4 Views A/B in `d1_5bar_*.csv`): close[i] vs close[i-5], threshold ±0.5%, matching the catalog feature definition (`feature_catalogs/CATALOG_v2.csv:1212`).
- Period boundaries: 2022-2023 = years {2022, 2023}; 2024-2025 = {2024, 2025}; 2026 = {2026}. Year extracted from first 4 chars of CSV time column.
- Gap detection: 5× median spacing OR >4h jump, capped at 60h to avoid weekend false positives. Window: first 200 timestamps for median estimation.
- "Best source" per (symbol, TF) selected by largest row count among de-duped paths (resolves data/historical/GBPUSD_*.csv → data/GBPUSD_*.csv symlinks).
- All file writes use `encoding="utf-8"` per Windows compatibility constraint.
- No Anthropic API calls made (subscription-bounded constraint).
