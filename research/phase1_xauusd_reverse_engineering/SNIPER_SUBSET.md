# Phase 1 Track D: GTOS Sniper Subset Analysis

**Owner:** Phase 1 Track D agent (research sub-agent)
**Branch:** `research/phase1-track-d-sniper-subset`
**Verdict:** **REJECT (as currently defined) / INSUFFICIENT SAMPLE (as softened)**
**Date:** 2026-04-24
**Status:** research-only, no src/config/prompts touched

---

## TL;DR

The sniper definition *as requested* — `setup_grade=A+ AND touch_count=1 AND m5_refined=true AND realized_RR ≥ 2.0` — **cannot be validly tested** on available data for two independent reasons, EITHER of which is fatal:

1. **Data fields don't exist.** `touch_count` and `m5_refined` are NOT persisted on any historical per-trade record. Touch count lives on OB metadata in live trade records (reconstructable via entry-price match, though imperfectly) and in the `raw_response` field of F3 backtest CANDIDATEs (regex-extractable). `m5_refined` state is written ONLY to the per-candle snapshot file `pipeline_state/m5_refinement.json` which is overwritten every candle — historical state is irretrievable. Exact sniper cell n = **0** across all 199 master-frame rows.

2. **The `realized_RR ≥ 2.0` axis is tautological.** Every trade in the batch with `realized_RR ≥ 2.0` is, by construction, a WIN (LOSS r_multiple range: [-1.0, -0.09]; WIN range: [+0.05, +3.99]; all 14 trades with r_multiple ≥ 2.0 are WINs). A filter that conditions on the outcome is not a filter — it is a definition. The observed "100% WR in sniper cell" is a mathematical identity, not an edge.

**Honest reduction of the sniper to validly testable axes** (`setup_grade=A+ AND touch_count=1`) yields **n=13, WR 53.8% [29.1, 76.8] Wilson 95%**, which is NOT different from the complement (WR 61.5% [53.5, 68.9]) — raw p = 0.767, Bonferroni-adjusted p = 1.00. **No edge.**

No filter recommendation possible. See §8 "Required sample size" for power analysis.

---

## 1. Data provenance

### 1a. Sources verified

| Source | Path | Rows | Outcome coverage | Touch-count coverage | m5_refined coverage |
|--------|------|------|---:|---:|---:|
| **Batch enriched index** | `knowledge_base/index/_trade_index.json` | 129 | 129 (100%) | 0 (field absent) | 0 (field absent) |
| **F3 backtest** (12 slices, Jan-Apr 2026) | `research/f3_backtest_2026-04-24/*/all_results.json` | 32 filled CANDIDATEs | 32 (100%) | 28 (via regex on `raw_response`) | 0 (F3 doesn't run M5 refinement) |
| **Live trade records** | `knowledge_base/trade_records/{SYM}/*.json` | 38 (not REJECTED) | 0 (all `LIMIT_PLACED` or `EXECUTION_FAILED`) | 14 (target OB matched by entry price) | 0 (not persisted on trade record) |
| **Master dataframe** | `research/phase1_xauusd_reverse_engineering/master_df.jsonl` | 199 | 161 | 42 | 0 |

### 1b. "367 trades" disambiguation

CLAUDE.md's §Validated Numbers claims "Batch population: 367 trades". This number is an *aggregate count across session-file `trade_executed=true` markers* (count tally = 379 trade_executed events, 259 unique trade_ids across top-level + per-symbol sessions). The **canonical enriched trade-level record** is `knowledge_base/index/_trade_index.json` with `trade_count: 129`, reseeded 2026-04-04 from session simulator. The 367 vs 259 vs 129 discrepancy is documented in `.context/backlog_synthesis_2026-04-18/00_MASTER_BACKLOG.md` (lines 154-163) as "output lost in worktree merge issues"; the current live KB (reseeded) is 129. **This Track D analysis uses the 129 enriched rows + F3 + live trade records, not the unrecoverable 367.** Honest partial analysis per CLAUDE.md §Reliability Rule #2.

### 1c. Excluded rows (all 38 live trade records)

All 38 candidate rows from `knowledge_base/trade_records/{SYM}/*.json` had `final_outcome ∈ {LIMIT_PLACED, EXECUTION_FAILED}` — no realized outcome captured. Live records capture decision-time state only; outcome is written to a separate exit summary that is not linked in these records. **None of the 38 rows contribute to WR/expectancy analysis**, but 14 contributed recoverable `touch_count` values via entry-price match against H1 OB list in the MSO.

### 1d. Schema verification table

| Field | batch_index | f3_backtest | live_trade_record | Comment |
|-------|:-:|:-:|:-:|-|
| `trade_id` | YES | YES (synthetic) | YES | |
| `symbol` | YES | YES | YES | |
| `direction` | PARTIAL (null in 24/129 rows) | YES | YES | batch_index LONG/SHORT inferred from session_simulator; 24 have null |
| `setup_grade` | YES (A+, A) | YES (A+ only) | YES (A+ only) | F3 and live only produce A+ due to V2 prompt's "A+ for CANDIDATE, C for NO_TRADE" rule |
| `touch_count` | **NO** | PARTIAL (28/32 via regex) | PARTIAL (14/38 via OB match) | batch completely missing |
| `m5_refined` | **NO** | **NO** | **NO** | Never persisted to per-trade records |
| `realized_RR` (r_multiple) | YES | YES (cap ~1.5 — F3 planned_rr=1.5) | NO | F3 cap excludes ≥2.0 stratum entirely |
| `outcome` | YES (WIN/LOSS/BREAKEVEN) | YES | **NO** | |

---

## 2. Stratification table (4-dim, cells with n ≥ 5)

n=161 rows with realized outcome.

| grade | touch_count | m5_refined | realized_RR | n | WR% | WR Wilson 95% CI | exp R |
|:-----:|:-----------:|:----------:|:-----------:|--:|----:|:-----------------|------:|
| A     | missing     | missing    | <1.5        | 29 | 48.3 | [31.4, 65.6] | -0.252 |
| A+    | 1           | missing    | <1.5        |  6 |  0.0 | [0.0, 39.0]  | -1.000 |
| A+    | 1           | missing    | 1.5-1.99    |  7 | 100.0 | [64.6, 100.0] | +1.501 |
| A+    | 2           | missing    | 1.5-1.99    |  7 | 100.0 | [64.6, 100.0] | +1.500 |
| A+    | missing     | missing    | <1.5        | 83 | 55.4 | [44.7, 65.6] | -0.131 |
| A+    | missing     | missing    | 1.5-1.99    |  6 | 100.0 | [61.0, 100.0] | +1.778 |
| A+    | missing     | missing    | ≥2.0        | 10 | 100.0 | [72.2, 100.0] | +2.776 |

**Key observation:** every cell where `realized_RR ≥ 1.5` shows 100% WR. This is the tautology surface — realized_RR buckets at or above the planned TP level are populated only by WIN outcomes, except in the pathological case where a LOSS can be counted above R=1.5 (does not occur in this batch).

---

## 3. Exact sniper cell: `(A+, touch_count=1, m5_refined=true, realized_RR ≥ 2.0)`

**n = 0.** No row in the master frame satisfies all four axes simultaneously, because:

- `m5_refined=true` → requires `m5_refined` data. Not persisted historically. **0 rows.**
- `touch_count=1 AND realized_RR ≥ 2.0` → possible in principle, but F3 is the only source with recoverable touch_count, and F3's planned_rr is capped at 1.5 so realized_RR ≥ 2.0 cannot occur there. Batch has no touch_count. Live has no outcome. **0 rows.**

Per CLAUDE.md §Reliability Rule "Small-sample honesty: if sniper n < 20, report the number + stop": **halting the exact-sniper quantitative test at n=0.**

---

## 4. Softened-definition sensitivity analysis

Sequentially drop unrecoverable / tautological axes, testing "sniper-like vs non-sniper-like" WR and expectancy differences. **Bonferroni k=3** applied to the three comparisons (α_raw=0.05, α_Bonferroni=0.0167).

| Definition | n_A | WR_A% (Wilson) | exp_A (bootstrap) | n_B | WR_B% | exp_B | ΔWR | Δexp (boot 95% CI) | Fisher p_raw | **Fisher p_Bonferroni** | Valid? |
|------------|----:|:-------------:|:-----------------:|----:|:-----:|:-----:|:---:|:------------------:|-----------:|-----------------------:|--------|
| **`A+` AND `realized_RR ≥ 2.0`** | 10 | 100 [72.2, 100] | +2.776 [+2.49, +3.08] | 151 | 58.3 [50.3, 65.8] | +0.139 [-0.02, +0.32] | +41.7pp | +2.641 [+2.32, +2.99] | 0.0068 | **0.0204** | **NO (tautological)** |
| `A+` AND `touch_count=1` | 13 | 53.8 [29.1, 76.8] | +0.347 [-0.42, +0.93] | 148 | 61.5 [53.5, 68.9] | +0.299 [+0.12, +0.49] | -7.6pp | +0.040 [-0.63, +0.72] | 0.7680 | **1.0000** | **YES — not significant** |
| `A+` AND `touch_count=1` AND `realized_RR ≥ 1.5` | 7 | 100 [64.6, 100] | +1.501 [+1.50, +1.50] | 154 | 59.1 [51.2, 66.5] | +0.249 [+0.05, +0.44] | +40.9pp | +1.251 [+1.06, +1.44] | 0.0432 | **0.1295** | **NO (partial tautology)** |

Note: p-values shown are Fisher's exact two-sided (appropriate for small-n 2x2). Permutation-bootstrap p-values (n_iter=5000) agree to within 0.007 in all three rows, confirming the result is not a test-selection artifact.

### 4a. The tautology problem

Realized-RR axes (`≥1.5`, `≥2.0`) are downstream consequences of outcome. **Any filter conditioning on realized_RR is an outcome filter, not a setup filter, and has zero predictive value ex ante.** A valid "sniper" filter must use only pre-trade inputs. After removing realized_RR, we are left with only `setup_grade=A+ AND touch_count=1`, which shows **no edge** (ΔWR -7.6pp, p_Bonferroni = 1.00).

### 4b. The only non-tautological result

`A+ AND touch_count=1` (n=13):
- WR 53.8% Wilson 95% CI [29.1, 76.8] — **wider than the 62% XAUUSD baseline**, does not reject it, does not support a filter.
- Expectancy +0.347R [-0.42, +0.93] — CI straddles zero.
- Ranks **below** the complement (+0.299R [+0.12, +0.49]) on WR; essentially tied on expectancy.
- **Verdict: no edge.**

---

## 5. Robustness (per-instrument, per-source breakdown)

Using `A+ AND realized_RR ≥ 2.0` as the (tautologically) "sniper-like" subset. Reported for completeness; does NOT change the verdict because the axis is invalid.

### 5a. Per-instrument

| Symbol | subset n | sniper n | WR_S% [CI] | non_s n | WR_non% [CI] |
|--------|---------:|---------:|:-----------|--------:|:-------------|
| GBPUSD | 24 | 3 | 100 [43.9, 100] | 21 | 61.9 [40.9, 79.2] |
| USDJPY | 19 | 0 | N/A | 19 | — |
| XAUUSD | 118 | 7 | 100 [64.6, 100] | 111 | 57.7 [48.4, 66.4] |

USDJPY insufficient (0 snipers). Both GBPUSD and XAUUSD show 100% WR in sniper cell — tautologically expected. n=3 GBPUSD is far below the n≥20 threshold; n=7 XAUUSD likewise. No robustness claim survives.

### 5b. Per-source

| Source | subset n | sniper n | WR_S% [CI] | non_s n | WR_non% [CI] |
|--------|---------:|---------:|:-----------|--------:|:-------------|
| batch_index | 129 | 10 | 100 [72.2, 100] | 119 | 58.8 [49.8, 67.3] |
| f3_backtest | 32 | 0 | N/A | 32 | — |

F3 insufficient (planned_rr=1.5 prevents realized_RR ≥ 2.0 by construction). Effect is batch-only, thus unreplicated.

---

## 6. Required sample size for 80% power, 5pp uplift detection

Two-proportion z-test, α=0.05 two-sided, power=0.80, comparing baseline WR vs (baseline + 5pp):

| Baseline | Target | n per arm |
|---------:|-------:|----------:|
| 55% | 60% | 1,529 |
| 60% | 65% | 1,467 |
| 62% | 65% | 1,433 |
| 65% | 70% | 1,372 |

**To confirm a 5pp WR uplift on a meaningful "sniper vs non-sniper" split requires ~1,400-1,500 trades per arm.** Current GTOS throughput (~17 trades/month) needs ~14 *years* of live trading to accumulate a single arm at that size. Either:
(a) run a batch backtest on a larger historical population with full schema persistence (touch_count + m5_refined captured per trade), or
(b) abandon the 5pp-uplift power target in favor of a larger uplift target with correspondingly smaller n.

---

## 7. Verdict

### ADOPT: no

The exact sniper definition cannot be computed (n=0 for m5_refined=true).

### REJECT: yes, for the valid non-tautological reduction

`setup_grade=A+ AND touch_count=1` shows **n=13, WR 53.8% [29.1, 76.8] Wilson 95%, expectancy +0.347R [-0.42, +0.93] bootstrap 95%**, which does not differ significantly from the complement (p_Bonferroni = 1.00). **The touch_count=1 axis, conditional on A+, does NOT add edge.**

### INSUFFICIENT SAMPLE: also yes, as a backstop

Even for the most optimistic tautology-including softened definition (`A+ AND realized_RR ≥ 2.0`), the per-arm sample required for 80% power on 5pp uplift is 1,400+. Current n=10 is ~140× below that threshold.

### Meta: the data is not instrumented for the question asked

`touch_count` and `m5_refined` must be persisted on every filled trade record going forward before this question can be validly answered. **Infrastructure recommendation** (NOT trading-logic change, so allowed without CEO approval per CLAUDE.md §WF-1 Discipline): add `target_ob_touch_count` and `m5_refined` boolean to the trade_record persistence layer (src/components/orchestrator.py `_log_candle` / `save_trade_record` path) and/or to `candidate_features_log.jsonl`. After ≥6 months of persisted live data, re-run this analysis.

---

## 8. Caveats

1. **Small sample.** 161 rows with realized outcome is already marginal; the sniper cell is 0-13 rows depending on softening. All effect-size CIs are very wide.
2. **Multiple-testing adjustment.** Bonferroni k=3 applied. Under FDR control (Benjamini-Hochberg) the tautology-including `A+ AND r≥2.0` result would remain significant at p≈0.014, but we reject it on *construct validity* grounds (tautology), not on p-value grounds.
3. **Source heterogeneity.** Batch uses session-simulator exits (CLOSED_BE, CLOSED_TP1_THEN_TIMEOUT, CLOSED_SESSION_TIMEOUT, CLOSED_TRAIL). F3 uses T7 simulator (SL-first on wide candles, no tick data). Live records have no exit data. **The batch's r_multiple distribution reflects the batch simulator's exit logic, not a real trade's exit.** A real-market edge test requires live forward data.
4. **Tautology axis.** The `realized_RR` stratification is an outcome descriptor, not a filter input. Should never be used as a sniper-filter axis. The sniper definition as stated is methodologically unsound regardless of data availability.
5. **LONG-only bias.** Per CLAUDE.md §Unresolved #4, the batch v1 detector emitted overwhelmingly LONG candidates. Track D findings are LONG-heavy and not generalizable to post-v2_shadow promotion behavior.
6. **Canonical "367 trades" is a historical aggregate count, not a surviving per-trade resource.** The current live trade index is 129. Per CLAUDE.md §Reliability Rule #2 ("file not found is always acceptable"), we used the 129 + 32 + live available instead of fabricating the missing 238 rows.

---

## 9. Artifacts

| File | Purpose |
|------|---------|
| `build_master_df.py` | Aggregates 3 sources into `master_df.jsonl` |
| `analyze_sniper.py` | Runs stratification + Bonferroni-corrected comparisons |
| `master_df.jsonl` | 199 rows, one per trade/candidate (only 161 with outcome) |
| `strata_summary.csv` | Full 4-dim stratification with n, WR, Wilson CI, expectancy, bootstrap CI |
| `sniper_comparisons.csv` | Sniper-like vs non-sniper comparisons with Bonferroni-adjusted p-values |

---

## 10. Expected R/month lift if (counterfactually) we adopted

Not applicable. Under the non-tautological reduction the sniper-like set is **worse** than the complement on both WR (-7.6pp) and not meaningfully different on expectancy; adopting would reduce trade volume by ~8% while providing no edge gain. Per CEO's high-quality-frequency framing, the optimization variable `freq × avg_R × WR` drops from `1.00 × 0.299 × 0.615 = 0.184` (no filter) to `0.08 × 0.347 × 0.538 = 0.015` on the retained stratum — a 92% drop in expected R/month contribution from the filtered-in slice. **Definitively do not adopt.**
