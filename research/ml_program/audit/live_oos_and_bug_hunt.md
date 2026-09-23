# K54 v2 Live OOS Estimator + Bug Hunt

**Audit date:** 2026-04-28
**Auditor:** Claude Code (Live OOS Estimator + Bug Hunter)
**Scope:** Q1 (live OOS holdout n estimate), Q2 (live evaluations training-data viability), Q3 (dedup-bug recurrence sweep), Q4 (precision-mismatch handling) for K54 v2 6-family modules.
**Data cutoff for stability scoring:** ≤2026-04-28 23:59 UTC (holdout 2026-04-29..05-12 untouched).

---

## Section 1 — Live OOS setup count estimate

### 1.1 Inventory of data sources for live OOS projection

#### Source A: `knowledge_base/live_evaluations/{SYMBOL}/*.jsonl`

Per-symbol per-day decision logs. Each record has `decision` ∈ {CANDIDATE, REJECT (various)}, full MSO snapshot, AI verdict, framework, regime label. Schema (verified on `USDJPY/2026-04-24.jsonl` first record):

```
['timestamp','candle_time','symbol','kill_zone','decision','daily_bias_direction',
 'daily_bias_confidence','h4_aligned','h1_poi_identified','h1_poi_type','h1_zone',
 'h1_fib_pct','h1_causing_event','sweep_detected','sweep_type','sweep_quality',
 'm15_choch','m15_displacement_quality','m15_displacement_ratio','setup_grade',
 'confidence_score','framework','session_memory_count','align_score','spread',
 'candle_index_in_kz','no_trade_reason','wait_reason','reasoning_word_count',
 'reasoning_price_count','overall_reasoning']
```

**Inventory across all 7 symbols** (records counted by date file existence + JSONL line count):

| Symbol    | Files | Eval records | CANDIDATE | REJECT | Days w/ data |
|-----------|------:|-------------:|----------:|-------:|-------------:|
| GBPJPY    |    17 |          298 |        23 |    275 |           17 |
| GBPUSD    |    11 |          161 |        29 |    132 |           11 |
| NAS100    |     1 |           14 |         0 |     14 |            1 |
| US30_cash |    15 |          268 |        36 |    232 |           15 |
| USDJPY    |    15 |          345 |        39 |    306 |           15 |
| XAGUSD    |     1 |           14 |         0 |     14 |            1 |
| XAUUSD    |    11 |          219 |        12 |    207 |           11 |
| **All**   |    71 |     **1319** |   **139** | **1180** |        — |

**Per-day cadence (post 2026-04-13 active fleet window):**

| Date       | Eval | CAND | Notes |
|------------|-----:|-----:|-------|
| 2026-04-13 |   98 |   36 | First multi-instrument-active day |
| 2026-04-14 |   63 |   16 | |
| 2026-04-15 |   69 |   14 | |
| 2026-04-16 |   98 |   11 | |
| 2026-04-17 |  111 |    8 | |
| 2026-04-19 |    4 |    0 | Sunday partial |
| 2026-04-20 |   58 |   11 | Active |
| 2026-04-21 |   82 |   17 | Active |
| 2026-04-22 |   32 |    4 | |
| 2026-04-23 |   52 |    9 | |
| 2026-04-24 |    2 |    1 | Friday partial |
| 2026-04-27 |   67 |   10 | **FN deploy day** (NAS100 + XAGUSD added live) |
| 2026-04-28 |   12 |    1 | In progress at audit time |

**Cadence summary (full-trading-day rate, days with ≥50 eval):** 12.3 CAND/day across 7 instruments (n=3 days: 04-20, 04-21, 04-23).

**Cadence summary (post-FN-deploy, 2026-04-27..28):** ~7.3 CAND/day (n=1.5 days, partial). The day-1 rate (10 CAND) is consistent with the active-week mean (7.0/day, n=6 days including partials).

#### Source B: `knowledge_base/index/_trade_index.json`

**STALE INDEX CONFIRMED.** File mtime: **2026-04-05 21:20 UTC**, content `reseeded_at: 2026-04-04T05:55:04`. Contents: 129 backtest trades, date range 2024-03-01 → **2026-03-13** — predates April 2026 trading entirely. **Zero April 2026 trades.** Symbols: only XAUUSD (105) + GBPUSD (24) — does not even cover the full fleet.

**Root cause of staleness:** `KnowledgeBase.update_trade_index` (`src/components/knowledge_base.py:134-154`) is only fired by `KnowledgeBase.write_trade()` which writes legacy `knowledge_base/trades/tr_*.yaml` files. The legacy `trades/` directory is **EMPTY** (`ls knowledge_base/trades/` shows no files). The new live path writes to `knowledge_base/trade_records/{SYMBOL}/*.json` (A3 v1.1 schema) which does NOT update `_trade_index.json`. Net effect: `_trade_index.json` is a frozen 2026-04-04 reseed snapshot, never refreshed by live trading.

#### Source C: `knowledge_base/trade_records/{SYMBOL}/*.json`

| Symbol    | Files (April 2026) |
|-----------|-------------------:|
| XAUUSD    |                 12 |
| US30_cash |                 36 |
| USDJPY    |                 44 |
| GBPJPY    |                 41 |
| GBPUSD    |                 28 |
| **Total** |            **161** |

Schema (sample `US30_cash/2026-04-27_london_0915.json`): `metadata, decision_pipeline, context_at_decision, mso, prompt, ai_response, trade_parameters, execution, exit, instrumentation, shadow_data, shadow`.

**Critical data-quality finding: `execution: null` and `exit: null` in 159/159 (100%) of April 2026 records inspected.** No `order_id` populated. Confirms the pre-existing memory `project_trade_records_enrichment_gap`. Trade records capture CANDIDATE decisions with intent (`trade_parameters`) but never get back-filled with realized R when the order fills/closes. **Realized-R via this source is unavailable for the holdout.**

#### Source D: `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv`

mtime: **2026-04-19 23:48 UTC** (stale). 151 rows total, max date **2026-03**. **No April 2026 trades.** Useful for pre-April training but not the holdout.

### 1.2 Cross-reference + staleness flags

| Source                        | mtime          | Newest data | April 2026 fills | Realized R |
|-------------------------------|----------------|-------------|-----------------:|-----------:|
| `live_evaluations`            | rolling daily  | 2026-04-28  | 139 CAND, 1180 REJECT | NO   |
| `_trade_index.json`           | 2026-04-05     | 2026-03-13  | 0                | YES (129)  |
| `trade_records/`              | rolling daily  | 2026-04-28  | 161 CAND captures | **NO** (`execution: null`) |
| `trades_unified.csv`          | 2026-04-19     | 2026-03     | 0                | YES (151)  |

**Net realized-R availability for live OOS holdout 2026-04-29..05-12: depends on a side-process not visible in any of the 4 sources.** The system's labelled-fill pipeline (the one that populated K54 v1's 94-trade Apr 1-24 holdout per the K54 v1 audit) is offline relative to the catalog the modeler can see. Either (a) a manual back-fill process runs out-of-band, or (b) F11 mechanical replay (on M15 OHLCV at BOS times) is the source of post-cutoff labels.

### 1.3 14-day OOS holdout n projection

**Window:** 2026-04-29 → 2026-05-12 = 14 calendar days = **10 weekdays** (Sat 5/2, Sun 5/3, Sat 5/9, Sun 5/10 excluded; FX trades all weekdays incl 5/1).

**CANDIDATE-level projections:**

| Scenario                                  | CAND/day | 14-day total | Notes |
|-------------------------------------------|---------:|-------------:|-------|
| Conservative (pre-FN active-week mean)    |      7.0 |       70-80  | 6-day window, includes partials |
| Central (full-trading-day rate)           |     12.3 |      120-130 | n=3 high-eval days (≥50 eval) |
| Post-FN observed (day-1 only, n=1)        |     10.0 |          100 | Single-day extrapolation |
| Pre-registered hypothesis estimate        |      ~0.6 |          ~8 | Per Q1.2 §60: "~17 trades/month × 14/30 = ~8 fleet setups" — **filled trades, not CANDIDATEs** |

**FILLED-TRADE-level projection (matches K54 v1 holdout cadence):**

K54 v1 holdout was **94 filled trades over 24 calendar days = 3.9 fills/day** (per K54 v1 audit Section 3). Applying that rate to the 14-day window: **~55 expected filled trades**. The pre-registered hypothesis estimate of "~8" appears to use the historical batch frequency (~17 trades/month, single-instrument XAUUSD, pre-fleet expansion) and does not reflect the 7-orchestrator FN deployment.

**Best central estimate for OOS holdout n: ~50-100 filled trades.** Lower bound assumes some fill-rate degradation from limit-order misses; upper bound assumes the active-week CAND-to-fill conversion approximates ~50%.

### 1.4 AUC SE at projected n + can the gate distinguish 0.61 from 0.55?

Hanley-McNeil AUC standard error, ~40% positive class (typical for K54 trade outcomes):

| n   | SE (AUC=0.61) | z-score (0.61 vs 0.55) | One-tailed p |
|----:|--------------:|-----------------------:|-------------:|
|  50 |        0.083  |                   0.72 |       0.234  |
|  80 |        0.065  |                   0.92 |       0.179  |
| 100 |        0.058  |                   1.03 |       0.152  |
| 120 |        0.053  |                   1.13 |       0.130  |
| 150 |        0.048  |                   1.26 |       0.103  |
| 168 |        0.045  |                   1.34 |       0.091  |

**Verdict on Q1: At realistic n=50-100, the holdout CANNOT distinguish AUC 0.61 from 0.55 at p<0.05 (one-tailed).** The pre-registered hypothesis (Q1.2 §60) explicitly acknowledges this: *"Setup-level n is small; CPCV gate (a) carries the primary statistical weight, holdout gate (b) is the leakage-discipline check."* The 14-day holdout is **NOT** the statistical workhorse — CPCV is. The holdout is a binary leakage-tripwire, not a power-driven test.

---

## Section 2 — Live evaluations training-data verdict

### 2.1 Pre-2026-04-29 live_evaluations records — usable as additional training data?

**Window:** 2026-04-06 → 2026-04-28 (data cutoff). Roughly **1,319 evaluation records** across 7 symbols (139 CANDIDATE + 1,180 REJECT).

### 2.2 Per-record availability of training-relevant fields

From schema inspection of `USDJPY/2026-04-24.jsonl` (first CANDIDATE record):

| Field                          | Available? | Notes |
|--------------------------------|------------|-------|
| timestamp / candle_time        | YES        | Full ISO UTC |
| symbol, kill_zone              | YES        | |
| decision (CAND/REJECT)         | YES        | |
| daily_bias_direction/conf      | YES        | |
| h4_aligned, h1_poi_identified, h1_poi_type, h1_zone, h1_fib_pct, h1_causing_event | YES | Full MSO snapshot |
| sweep_detected/type/quality    | YES        | |
| m15_choch, m15_displacement_*  | YES        | |
| setup_grade, confidence_score  | YES        | |
| framework                      | YES        | ob_retest / fvg_fill / breaker_re_entry |
| session_memory_count, align_score, spread | YES | |
| no_trade_reason / wait_reason  | YES (REJECT only) | |
| reasoning_*                    | YES        | |
| **regime label**               | NO direct field | Must be joined from `shadow_logs/regime_classifications.jsonl` or `structure_detector_backfill_2026.jsonl` |
| **realized R**                 | **NO**     | live_evaluations have NO outcome field. Decision-only logs. |
| **execution / fill**           | **NO**     | Not in schema. |

### 2.3 Verdict

**REJECT-cohort: USABLE for negative-class training data IF the modeler relabels REJECT → "system says no" rather than "trade lost".** This is a different prediction target than K54 v1 (which is `realized_r > 0`). For the K54 v2 binary classifier this is **NOT a drop-in expansion**; it's a different problem (decision-prediction vs outcome-prediction).

**CANDIDATE-cohort: NOT USABLE as labelled training data on its own** — no realized R. Pairing with `trade_records/` doesn't help (execution always null). Would require:
1. Replaying CANDs through a backtest using OHLCV to compute realized R → out-of-scope for stability scoring.
2. Manual back-fill from MT5 trade history (ground truth) → operational, not in the audit scope.

**Schema drift since 2026-04-27:** No drift detected. Schema is consistent across 2026-04-06 → 2026-04-28. NAS100 + XAGUSD added 2026-04-27 with same schema.

**Net verdict on Q2: NOT USABLE as additional training data without an out-of-band realized-R backfill.** The data quality is high and the volume is significant (~139 CAND across 7 symbols), but the missing outcome label disqualifies it for K54 v2 supervised learning. Modeler should defer until either:
- (a) An MT5-history-driven backfill process produces realized_r per CANDIDATE → trade_records, OR
- (b) An OHLCV-replay backtest engine produces synthetic realized_r per CANDIDATE.

If (a) or (b) is shipped, expansion estimate: **~55-100 additional labelled trades** beyond the 411 F14-extended set, weighted toward LONG-bias 2026-04 cohort.

---

## Section 3 — Dedup-pattern bug recurrence sweep

### 3.1 K54 v1 caveat 9 (the originating bug)

Per `research/ml_program/k54_v1_audit.md:292`:

> **Train-set duplication risk via trade_id-keyed dedup.** Spot-checked `bt_2024-04-01_london_001` (unified_csv) and `bt_2024-04-01_london_001_xauusd` (trade_index) appear as 2 rows with identical realized R. Fix: tuple-keyed dedup (date, symbol, direction, framework, realized_r).

### 3.2 Per-module dedup verdict

| Module                          | Loads trade-data? | Sources joined | Dedup logic | Verdict |
|---------------------------------|-------------------|----------------|-------------|---------|
| `regime.py`                     | NO (extractor only) | — | — | **CLEAN** — pure feature extractor, takes (symbol, ts, side) |
| `structure.py`                  | NO (extractor only) | — | — | **CLEAN** |
| `microstructure.py`             | NO (extractor only) | — | — | **CLEAN** |
| `volatility.py`                 | NO (extractor only) | — | — | **CLEAN** |
| `liquidity.py`                  | NO (extractor only) | — | — | **CLEAN** |
| `time_session.py`               | NO (extractor only) | — | — | **CLEAN** |
| `_compute_stability.py` (time_session scorer) | YES | F11 + trade_index | **NONE** — `all_recs = f11 + ti` (line 132) | **BUG REPRODUCED — no dedup at all** |
| `_compute_structure_stability.py` | YES | F11 only | n/a | **CLEAN** (single-source) |
| `_run_microstructure_stability.py` | YES | F11 only | n/a | **CLEAN** (single-source) |
| `_score_liquidity_stability.py` | YES | F11 only | n/a | **CLEAN** (single-source) |
| `_run_volatility_catalog.py`    | YES | F11 + trade_index + unified | (symbol, ts) tuple, F11 priority (line 290-299) | **BUG PARTIAL — see §3.3** |
| `_emit_catalog.py`              | NO (catalog formatter) | — | — | **CLEAN** |
| `_build_structure_catalog.py`   | NO (catalog formatter) | — | — | **CLEAN** |
| `_build_liquidity_catalog.py`   | NO (catalog formatter) | — | — | **CLEAN** |

### 3.3 Empirical bug magnitude (volatility scorer)

I simulated the volatility scorer's `(symbol, ts)` dedup on the same source files at the audit-time data state. Pre-2026-04 cohort with `realized_r != null`:

- F11 records: 345
- trade_index records: 129
- trades_unified records: 151

**Volatility scorer dedup behavior** (key = `(symbol, ts)` where F11 ts = bos_time, trade_index/unified ts = `date + KZ_HOUR`):
- Total kept: **496** (F11 345, trade_index 129, unified 22)

**Tuple-keyed dedup `(date, symbol, realized_r)` would keep:** **467 records.**

**Double-counting magnitude: 29 records (~6% of volatility cohort) currently double-weighted** by the (symbol, ts) key but would be correctly collapsed by tuple-key. Direct trade_id collisions (no suffix-strip) between trade_index and unified: **40 trade_ids** appear in both. F11 records with BOS-time on a KZ-default hour AND matching a trade_index/unified row: ~29.

**The bug is NOT the original K54 v1 trade_id-keyed-dedup variant** (volatility uses tuple-key); it's a **near-miss**: the dedup tuple is too narrow. F11's BOS-precise hour vs trade_index's KZ-snapped hour rarely collide, so the same trade gets in twice.

### 3.4 time_session scorer is the worst case

`_compute_stability.py:132`: `all_recs = f11 + ti` — **no dedup at all**. This is the time_session family's stability scorer. Population: **F11 (n=345) + trade_index (n=129) = 474 rows**, of which an unknown subset are direct duplicates of the same backtest trade. Time-session features (hour-of-day buckets, KZ flags) are *especially* sensitive because the trade_index records snap to KZ-default hours (8, 14, 1) — so duplicates concentrate in those hour bins, biasing the Spearman ρ on hour-of-day features.

### 3.5 Family verdicts (Q3 summary)

| Family         | Stability scorer file                  | Dedup verdict |
|----------------|----------------------------------------|---------------|
| Regime         | (no scorer; uses regime.csv catalog only) | **CLEAN** |
| Structure      | `_compute_structure_stability.py`      | **CLEAN** (F11-only) |
| Liquidity      | `_score_liquidity_stability.py`        | **CLEAN** (F11-only) |
| Microstructure | `_run_microstructure_stability.py`     | **CLEAN** (F11-only) |
| Volatility     | `_run_volatility_catalog.py`           | **PARTIAL BUG** (~6% double-weight, 29 records) |
| Time_session   | `_compute_stability.py`                | **FULL BUG** (no dedup, 474 rows include ~unknown # of duplicates) |

Two of six families inherit the K54 v1 caveat 9 bug pattern — both modules where multiple trade-data sources are unioned. The four F11-only modules are immune by construction.

---

## Section 4 — Precision-mismatch handling audit

### 4.1 The precision asymmetry

Per `research/ml_program/feature_catalogs/CATALOG_v2.md:124, 172` (cited cross-cutting flag):

> Pre-2026-04 trade_index snaps to KZ-hour (date-only entry time precision); only F11 has bos-time precision. Stability ρ may be biased toward features that move slowly enough to survive the snap-to-hour error (Volatility flagged this).

Concrete schemas:

- **F11 record:** `bos.bos_time = "2026-01-05T17:00:00+00:00"` (precise to M15 close).
- **Trade index record:** `t.date = "2026-01-05"`, `t.kill_zone = "ny"` → `ts = "2026-01-05 14:00:00 UTC"` (KZ-default hour 14).
- **Trades unified record:** same date+KZ-snap as trade_index.

For an XAUUSD NY trade where the BOS occurred at 17:00 UTC and the trade entered after retest at 17:30:
- F11 places the row at 17:00 UTC.
- trade_index places the row at 14:00 UTC.

**The same trade gets two rows at two different hours** in a unioned cohort. Time-of-day-sensitive features (hour-of-day bucket, KZ phase, intraday vol percentile) compute different values at 14:00 vs 17:00 → injects noise into the Spearman ρ.

### 4.2 Per-module precision-mismatch verdict

| Module / scorer                         | F11 used? | trade_index used? | Mitigation? | Bias direction |
|-----------------------------------------|-----------|-------------------|-------------|----------------|
| `_compute_stability.py` (time_session)  | YES (n=345) | YES (n=129) | **NONE** | **BIAS HEAVY** — trade_index always lands on KZ-default hour, distorting hour-of-day Spearman ρ |
| `_run_volatility_catalog.py`            | YES | YES + unified | (sym, ts) dedup helps slightly; weighting note in `volatility.md:54` flags but does not fix | **BIAS MODEST** for hourly features; minimal for daily-rolling features |
| `_compute_structure_stability.py`       | YES | NO | n/a (F11-only) | **NONE** |
| `_score_liquidity_stability.py`         | YES | NO | n/a (F11-only) | **NONE** |
| `_run_microstructure_stability.py`      | YES | NO | n/a (F11-only) | **NONE** |
| Regime catalog (regime.csv)             | source-agnostic | source-agnostic | Note in `CATALOG_v2.md:124` | **N/A** (no Spearman scoring done in this family) |

### 4.3 The two affected modules

**Time_session (worst-affected):**
- 129 of 474 rows (27%) snap to {01, 08, 14} UTC.
- Time_session features include `hour_utc`, `is_london_open_window`, `intraday_vol_*` — all of which compute different values at the snap vs the precise BOS time.
- Spearman ρ for hour-of-day features will be biased by the artificial 27% concentration at those hours, **inflating apparent stability** of hour-bucket features.

**Volatility (modestly affected):**
- The (symbol, ts) dedup partially compensates (collapses trade_index ↔ unified collisions), but F11 ↔ trade_index of the same trade still get two rows.
- Volatility features that average over rolling windows (>24 bars) are minimally affected; features at hourly granularity (intraday vol percentile, GARCH lag-1) ARE affected.

### 4.4 Recommended fix

For the K54 v2 modeler:

**Recommendation 1 (load-time dedup):** Tuple-keyed dedup `(date, symbol, direction, framework, round(realized_r, 3))` at load time, applied BEFORE any scoring. Reduces the 474 → ~445 rows (extrapolating volatility's 29-row collapse to time_session). Resolves the K54 v1 caveat 9 + cross-source duplication.

**Recommendation 2 (per-source weighting):** When rows survive dedup but come from different sources, weight by source precision in the Spearman computation. Concretely, for the unioned cohort:
- F11 rows: weight 1.0 (BOS-time precision).
- trade_index rows: weight 0.5 (KZ-hour precision; ±2-3 hour error).
- trades_unified rows: weight 0.5 (same precision class).

Implement via `weights` argument in `scipy.stats.spearmanr` → no, scipy doesn't support weighted Spearman directly; instead compute weighted Pearson on rank-transformed data.

**Recommendation 3 (per-source train splits):** For features known to be hour-sensitive (time_session, intraday volatility), report stability ρ separately for the F11-only cohort vs the unioned cohort. If the F11-only ρ is the more conservative (smaller |ρ|), use it as the gating threshold; if the unioned ρ flips sign vs F11-only, treat as unstable per-source.

**Recommendation 4 (modeler-side):** When the K54 v2 modeler builds the training matrix, prefer F11-only rows for hour-sensitive features and use trade_index/unified ONLY for date-sensitive aggregations (day-of-week, day-of-month). This is the minimum-invasive fix at modeling time.

---

## Section 5 — Recommendations for Week 4 modeler

### 5.1 Live OOS holdout (Q1)

1. **Do not gate K54 v2 ship/no-ship on the 14-day holdout AUC alone.** With realistic n=50-100 filled trades, AUC SE is 0.06-0.08 — not enough to discriminate 0.61 from 0.55 at p<0.05. Pre-registered hypothesis Q1.2 already documents this; CPCV is the statistical workhorse. The holdout is a leakage-tripwire only.
2. **Resolve the realized-R backfill question BEFORE 2026-05-12.** Currently no source visible to the modeler labels post-2026-04-28 trades with realized R. Either (a) commission an MT5-history-driven backfill, or (b) use F11 mechanical replay on M15 OHLCV at BOS times in the holdout window. Document the choice in the K54 v2 spec.
3. **Update `_trade_index.json` regeneration plan.** The file has been frozen since 2026-04-04 reseed and is referenced by 3+ family modules' stability scorers. Either:
   - (a) Re-run `scripts/reseed_from_sessions.py` (or successor) to refresh _trade_index from `trade_records/` + MT5 history. Current state silently misleads any agent that assumes the file is current.
   - (b) Document that `_trade_index.json` is a frozen snapshot intentionally and stability scorers consume it as-is. Add a header comment to the JSON.

### 5.2 Live evaluations as training data (Q2)

4. **Do not include 2026-04-13..28 live_evaluations records in K54 v2 training data.** Without realized R, they cannot serve as labelled examples for a binary classifier. They MAY serve as **decision-process auxiliary features** (e.g., AI confidence calibration shadow signal) but that's a different track — out-of-scope for K54 v2.
5. **If a backfill ships, expect ~55-100 additional trades.** Apply the same CPCV-with-purge framework; do NOT add the new trades to a frozen K54 v2 train split — re-run the train pipeline from scratch.

### 5.3 Dedup bug remediation (Q3)

6. **Patch `_compute_stability.py` (time_session)** before running stability scoring on the v2 catalog. The current `all_recs = f11 + ti` line is functionally identical to K54 v1's caveat 9 bug. Replace with:
   ```python
   tuple_seen = set()
   all_recs = []
   for src in (f11, ti):
       for r in src:
           key = (r["ts_iso"][:10], r["symbol"], round(r["realized_r"], 3))
           # Optionally include direction/framework if available in src
           if key in tuple_seen:
               continue
           tuple_seen.add(key)
           all_recs.append(r)
   ```
7. **Tighten `_run_volatility_catalog.py:290-299`** to use tuple-key in addition to (symbol, ts). Concretely, key on `(symbol, date_str, round(r["realized_r"], 3))` — this catches F11 ↔ trade_index of same backtest trade where bos_time and KZ-snap differ in hour but agree on date+symbol+realized_r. Recovers ~29 over-counted rows (~6% of cohort).
8. **Re-run stability scoring after patches.** All catalog `*_stability.csv` / `_*_stability.json` outputs must be regenerated. Compare top-15 features pre/post — features whose ρ moves outside the post-patch n-adjusted SE band were the bias victims.

### 5.4 Precision-mismatch handling (Q4)

9. **Adopt per-source weighting** for the time_session and volatility families. F11 rows weight 1.0; trade_index/unified rows weight 0.5. Implementable as duplication of F11 rows or by replacing the spearmanr call with a weighted Pearson-on-ranks.
10. **For hour-sensitive features only**, report two stability scores per feature: ρ_unioned (current convention) and ρ_F11_only (precision-pure). Prefer ρ_F11_only when the two disagree by > 1 SE. Add a column `precision_pure_rho` to the catalogs.
11. **Document the precision asymmetry in the K54 v2 spec.** The modeler must know that hour-of-day features have noisier stability scores than they appear and should weight them lower at feature selection time.

### 5.5 Operational hygiene (out-of-scope but flagged)

12. **`_trade_index.json` 21-day staleness should be fixed regardless of K54 v2.** Multiple stability scorers consume it; many other research scripts (per memory `project_trade_records_enrichment_gap`) need real-time fill data. Without a refresh process, any agent grepping `_trade_index.json` is reading an April-4-frozen snapshot.
13. **`trade_records/{SYMBOL}/*.json` execution back-fill is the load-bearing fix.** All April 2026 records have `execution: null` and `exit: null`. Until this is repaired, the entire ML research program is constrained to the F11 + (frozen) trade_index + (frozen) trades_unified cohort.

---

## Audit summary

| Q   | Verdict |
|-----|---------|
| Q1  | OOS holdout n ≈ 50-100 filled trades; AUC SE ≈ 0.06-0.08; **gate cannot distinguish 0.61 from 0.55 at p<0.05**. Pre-registered hypothesis acknowledges this and routes statistical weight to CPCV. |
| Q2  | Live evaluations are **NOT usable as training data** without realized-R backfill. CANDIDATE captures lack outcome labels; trade_records have `execution: null` 100%. ~139 CAND across 7 symbols available if a backfill ships. |
| Q3  | **2/6 family scorers inherit the K54 v1 caveat 9 dedup bug**. Time_session (no dedup at all, 474 rows) is the worst; volatility (~6% double-weighted, 29 rows) is partial. The 4 F11-only scorers are clean. |
| Q4  | **Precision mismatch affects 2/6 families** (time_session worst, volatility moderate). Trade_index records snap to KZ-hour (14/8/1 UTC) creating artificial concentration at those hours that biases hour-sensitive Spearman ρ. F11 BOS-precise rows are gold standard. Recommend per-source weighting + precision-pure ρ column. |
| Surprise | **`knowledge_base/index/_trade_index.json` is frozen at 2026-04-04 with ZERO April 2026 trades** — the live-trade pipeline writes to `trade_records/` (not `trades/`), so the legacy `update_trade_index` hook never fires. Stability scorers that load this file think they're reading "current backtest + live trades" but are reading a 24-day-stale reseed snapshot. Affects time_session + volatility families directly. |
