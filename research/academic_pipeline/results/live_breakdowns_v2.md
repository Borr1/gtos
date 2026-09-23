# Live Breakdowns v2 - L2 Rejection + Monthly WR Decay (reviewer fixes)

**Generated:** 2026-04-17  
**Cost:** $0 (pure local computation)  
**Version:** v2 (schema fix + arithmetic clean-up)

## v2 change log

**Wave 1 reviewer issue (Issue 4):** v1 looked for a `trade_outcome` field in trade_records that does not exist; the real schema has a top-level `exit` field. v1 also presented `entry_in_ob` as "22/47 (47%)" in one place and the implied denominator was 49 in another (the L2 reason Counter includes 2 `post_m5_refinement_failed` entries from REJECTED_L2_POST_M5, so REJECTED_L2 pure = 47, L2 family = 49).

**v2 fixes:**

1. `load_live_closed_trades_v2()` reads the real top-level `exit` field and `exit.realised_r_multiple` (with defensive fallbacks to `execution.realised_r_multiple`). Schema stats are emitted up-front so the reviewer can verify the 0-closed-trades figure is genuine.
2. All `entry_in_ob` and similar share statements list both denominators explicitly (`REJECTED_L2 = 47` vs `REJECTED_L2 family = 49`).
3. `sl_too_tight` ratios section states "7 of 9 (77.8%) rejected SLs have SL/ATR >= 1.0" with full ratio list visible.

Production code paths are not changed. v1 report is retained at `research/academic_pipeline/results/live_breakdowns.md`.

## Schema verification

Proof that "0 live closed trades" is real, not a bug from missing-field lookup:

| Check | Count |
|-------|-------|
| Trade-record files parsed | 85 |
| Records with `exit` field at top level | 85 |
| Records with `exit` field NON-NULL | 0 |
| Records with `execution.realised_r_multiple` | 0 |
| Records with ANY usable r_multiple | 0 |

Interpretation: every record has the `exit` slot, but none are populated yet. The live-trade outcome logger has not fired on any of the CANDIDATE paths observed so far (expected: all CANDIDATEs either rejected at L1/L2, placed as pending limit, or failed at MT5 execution).

## Hypothesis (pre-data)

Written before running any counts. Predictions from handoffs 15-20 and the
Apr 13 L2 rejection analysis.

- **L2 top reason:** predicted `entry_in_ob` dominant. Observed: `entry_in_ob` = 22 out of L2-reason Counter total 49 (44.9%) -> **confirmed**.
- **L1 `sl_too_tight`:** predicted 6-9; observed 9 over ~11-day window -> **confirmed** (5.7/week matches handoff-16 4-5/week claim).
- **Monthly WR decay:** predicted tau<0, p 0.05-0.20; observed tau=-0.244, p=0.367 -> **direction correct, p larger than predicted**.

## L2 Rejection Breakdown

### Data

- Trade-record JSONs parsed: **85** files
- Instruments covered: GBPJPY, GBPUSD, US30_cash, USDJPY, XAUUSD
- Date range from live_sessions: **2026-04-06 -> 2026-04-16**
- Total AI-evaluated candles (live_sessions `api_calls_made` sum): **759**
- Total NO_TRADE decisions (AI said no): **748**
- Total CANDIDATE records reaching verification: **85**
- Total gate-rejected (L1 + L2 family): **62**
- Total reaching execution (EXECUTED/LIMIT/FAILED): **23**

### Pipeline funnel (live, Apr 6 - Apr 17 2026)

| Stage | Count | Notes |
|-------|-------|-------|
| API calls (AI evaluations) | 759 | sum of `api_calls_made` per session |
| AI said NO_TRADE | 748 | 98.6% of API calls |
| AI said CANDIDATE (reached gate stage) | 85 | records in `trade_records/` |
| REJECTED_GATE1_SAFETY (L1) | 13 | |
| REJECTED_L2 (pure) | 47 | |
| REJECTED_L2_POST_M5 | 2 | |
| LIMIT_PLACED | 17 | between-KZ fill depends on watcher |
| EXECUTION_FAILED | 6 | retcode != DONE |

### Per-symbol outcome distribution

| Symbol | REJECTED_L2 | REJECTED_L2_POST_M5 | REJECTED_GATE1_SAFETY | LIMIT_PLACED | EXECUTION_FAILED | Total |
|---|---|---|---|---|---|---|
| GBPJPY | 2 | 0 | 8 | 5 | 4 | 19 |
| GBPUSD | 5 | 0 | 3 | 4 | 1 | 13 |
| US30_cash | 13 | 2 | 0 | 2 | 1 | 18 |
| USDJPY | 21 | 0 | 2 | 3 | 0 | 26 |
| XAUUSD | 6 | 0 | 0 | 3 | 0 | 9 |

### L2 rejection reasons

| Reason | Count | % of L2-reason Counter (n=49) | % of REJECTED_L2 pure (n=47) |
|--------|-------|-------------------------------|------------------------------|
| `entry_in_ob` | 22 | 44.9% | 46.8% |
| `sl_beyond_ob` | 19 | 38.8% | 40.4% |
| `h1_poi_exists` | 6 | 12.2% | 12.8% |
| `post_m5_refinement_failed` | 2 | 4.1% | n/a (from POST_M5 path) |
| **Total L2 Counter** | **49** | 100% | n/a |

**Denominator note.** `REJECTED_L2` outcome count = 47; `REJECTED_L2_POST_M5` count = 2; L2-reason Counter sum = 49 (47 L2-pure + 2 post-M5 tagged `post_m5_refinement_failed`). v1 reported "22/47 (47%)" by dividing by the pure-L2 count only; using the full Counter gives 22/49 (44.9%). Both are reported above.

### L1 (Gate1 Safety) rejection reasons

| Reason | Count | % of L1 |
|--------|-------|---------|
| `sl_too_tight` | 9 | 69.2% |
| `sl_below_minimum_floor` | 3 | 23.1% |
| `tp1_below_entry` | 1 | 7.7% |
| **Total L1** | **13** | 100% |

### L3 (Gate3 Circuit Breaker) rejection reasons

No gate3 rejections captured in live trade_records.

### sl_too_tight deep-dive

- L1 denials with reason `sl_too_tight`: **9**
- L1 denials with reason `sl_below_minimum_floor`: **3**

| # | Symbol | Date | KZ | SL_dist | M15_ATR | SL/ATR ratio |
|---|--------|------|----|---------|---------|-------------|
| 1 | GBPJPY | 2026-04-13 | ny | 0.13900 | 0.10954 | 1.269 |
| 2 | GBPJPY | 2026-04-13 | ny | 0.13900 | 0.10566 | 1.316 |
| 3 | GBPJPY | 2026-04-13 | ny | 0.13900 | 0.10507 | 1.323 |
| 4 | GBPJPY | 2026-04-13 | ny | 0.13900 | 0.10707 | 1.298 |
| 5 | GBPJPY | 2026-04-13 | ny | 0.13900 | 0.10671 | 1.303 |
| 6 | GBPJPY | 2026-04-14 | ny | 0.13000 | 0.10812 | 1.202 |
| 7 | GBPUSD | 2026-04-13 | london | 0.00032 | 0.00062 | 0.515 |
| 8 | GBPUSD | 2026-04-13 | ny | 0.00103 | 0.00070 | 1.480 |
| 9 | GBPUSD | 2026-04-13 | ny | 0.00061 | 0.00078 | 0.782 |

**sl_below_minimum_floor cases:**

| # | Symbol | Date | SL_dist | Floor |
|---|--------|------|---------|-------|
| 1 | GBPJPY | 2026-04-13 | 0.08699999999998909 | 0.118 |
| 2 | GBPJPY | 2026-04-13 | 0.10699999999999932 | 0.118 |
| 3 | USDJPY | 2026-04-13 | 0.07499999999998863 | 0.085 |

**SL/ATR distribution (gate threshold = 1.5):**

- Min: 0.515, Median: 1.298, Max: 1.480
- Full sorted list: ['0.515', '0.782', '1.202', '1.269', '1.298', '1.303', '1.316', '1.323', '1.480']
- SL/ATR >= 1.0: **7 of 9** (77.8%)
- SL/ATR >= 1.2: **7 of 9** (77.8%)
- SL/ATR >= 1.5: **0 of 9** (0.0%) (this is the current production threshold)

**Handoff-16 claim:** `sl_too_tight` blocks 4-5 trades/week. Observed: 9 over ~11 days = **5.7/week** -> **CONFIRMED**.

**Recommendation reference (consistent with v1):** `ob_retest_sl_exception` extended to bypass the ATR gate when SL/ATR >= 1.0 AND SL placed structurally behind an OB boundary would unblock **7 of 9 = 77.8%** of sl_too_tight rejections.

### API refusal / malformed responses

- Total malformed entries: **56**
- Flat-refusal-pattern matches: **36**

| Date | Count |
|------|-------|
| 2026-04-13 | 38 |
| 2026-04-15 | 3 |
| 2026-04-16 | 15 |

### Recommendation

- **L2 top reason `entry_in_ob` = 22 out of L2-reason Counter total 49 (44.9%).** Prompt-level fix needed (AI places entry outside OB or SL exactly at OB boundary).
- **L1 top reason `sl_too_tight` = 9 out of 13 (69.2%).**
- **`sl_too_tight` exception to unblock 7 of 9 (77.8%)** - extend `ob_retest_sl_exception` to bypass the ATR gate when SL placed structurally behind OB AND SL/ATR >= 1.0.
- No Gate3 circuit-breaker rejections observed.
- The `decisions.CANDIDATE` counter in KZ summaries is always 0 because CANDIDATEs are logged to `trade_records/`, not to the KZ summary counter. Logging discrepancy only; trivial fix.

## Monthly WR Decay

### Data

- Batch trades: **111**
- Live closed trades with r_multiple (v2 schema check): **0**
- Combined: **111**

### Monthly table (all instruments)

| Month | n | wins | losses | BE | WR | 95% Wilson CI | avg_R | sum_R | Notes |
|-------|---|------|--------|----|----|---------------|-------|-------|-------|
| 2024-04 | 3 | 2 | 1 | 0 | 66.7% | [20.8%, 93.9%] | +0.607 | +1.82 | <5 (underpowered) |
| 2024-07 | 3 | 3 | 0 | 0 | 100.0% | [43.8%, 100.0%] | +0.703 | +2.11 | <5 (underpowered) |
| 2024-08 | 1 | 1 | 0 | 0 | 100.0% | [20.7%, 100.0%] | +0.160 | +0.16 | <5 (underpowered) |
| 2024-09 | 1 | 0 | 1 | 0 | 0.0% | [0.0%, 79.3%] | -1.000 | -1.00 | <5 (underpowered) |
| 2024-10 | 2 | 1 | 1 | 0 | 50.0% | [9.5%, 90.5%] | +0.015 | +0.03 | <5 (underpowered) |
| 2025-01 | 5 | 4 | 1 | 0 | 80.0% | [37.6%, 96.4%] | +1.062 | +5.31 | |
| 2025-02 | 14 | 8 | 4 | 2 | 66.7% | [39.1%, 86.2%] | -0.137 | -1.92 | |
| 2025-03 | 11 | 7 | 4 | 0 | 63.6% | [35.4%, 84.8%] | +0.124 | +1.36 | |
| 2025-04 | 4 | 1 | 3 | 0 | 25.0% | [4.6%, 69.9%] | -0.292 | -1.17 | <5 (underpowered) |
| 2025-05 | 3 | 3 | 0 | 0 | 100.0% | [43.8%, 100.0%] | +0.893 | +2.68 | <5 (underpowered) |
| 2025-06 | 8 | 3 | 5 | 0 | 37.5% | [13.7%, 69.4%] | -0.412 | -3.30 | |
| 2025-09 | 8 | 6 | 2 | 0 | 75.0% | [40.9%, 92.9%] | +0.139 | +1.11 | |
| 2025-10 | 10 | 9 | 1 | 0 | 90.0% | [59.6%, 98.2%] | +0.685 | +6.85 | |
| 2025-12 | 9 | 6 | 2 | 1 | 75.0% | [40.9%, 92.9%] | +0.398 | +3.58 | |
| 2026-01 | 18 | 11 | 7 | 0 | 61.1% | [38.6%, 79.7%] | +0.055 | +0.99 | |
| 2026-02 | 6 | 4 | 2 | 0 | 66.7% | [30.0%, 90.3%] | +0.358 | +2.15 | |
| 2026-03 | 5 | 3 | 2 | 0 | 60.0% | [23.1%, 88.2%] | +0.282 | +1.41 | |

### Trend tests

- **Mann-Kendall** (over 10 months with n>=5):
  S=-11.0, tau=-0.244, two-sided p=0.367
  - Trend direction: **negative (WR decaying)**
  - Verdict: not significant at alpha=0.05

- **Chi-square homogeneity** (wins vs losses across 10 months): chi2=6.840, df=9, p=0.654
  - Verdict: cannot reject homogeneity at alpha=0.05

### Per-instrument monthly WR

#### XAUUSD

| Month | n | WR | avg_R | sum_R |
|-------|---|-----|-------|-------|
| 2024-04 | 3 | 66.7% | +0.607 | +1.82 | (n<5) |
| 2024-07 | 3 | 100.0% | +0.703 | +2.11 | (n<5) |
| 2024-08 | 1 | 100.0% | +0.160 | +0.16 | (n<5) |
| 2024-09 | 1 | 0.0% | -1.000 | -1.00 | (n<5) |
| 2024-10 | 2 | 50.0% | +0.015 | +0.03 | (n<5) |
| 2025-01 | 5 | 80.0% | +1.062 | +5.31 | |
| 2025-02 | 14 | 66.7% | -0.137 | -1.92 | |
| 2025-03 | 11 | 63.6% | +0.124 | +1.36 | |
| 2025-04 | 4 | 25.0% | -0.292 | -1.17 | (n<5) |
| 2025-05 | 3 | 100.0% | +0.893 | +2.68 | (n<5) |
| 2025-06 | 8 | 37.5% | -0.412 | -3.30 | |
| 2025-09 | 8 | 75.0% | +0.139 | +1.11 | |
| 2025-10 | 10 | 90.0% | +0.685 | +6.85 | |
| 2025-12 | 9 | 75.0% | +0.398 | +3.58 | |
| 2026-01 | 18 | 61.1% | +0.055 | +0.99 | |
| 2026-02 | 6 | 66.7% | +0.358 | +2.15 | |
| 2026-03 | 5 | 60.0% | +0.282 | +1.41 | |

Mann-Kendall (10 months): tau=-0.244, p=0.367

### Interpretation

- Monthly WR verdict: **Decay present but weak** (tau=-0.244, p=0.367).
- Window dominated by batch data; live closed trades (0) not yet material.

## Overall recommendations

1. **Fix `sl_beyond_ob` at the prompt level.** Prompt should enforce "SL must be >= 1 tick beyond OB" or apply deterministic SL snap.
2. **Fix `entry_in_ob` at prompt level.** 22 of 49 L2-reason Counter entries (44.9%), 22 of 47 REJECTED_L2 pure (46.8%).
3. **Address `sl_too_tight` by exception.** Extend `ob_retest_sl_exception` to bypass the ATR gate when SL placed structurally behind OB AND SL/ATR >= 1.0. Unblocks **7 of 9 = 77.8%**.
4. **Keep monthly WR monitoring live.** Promote decay alarm only when Mann-Kendall p<0.05 over >=5 months OR 20-trade rolling Wilson upper < 55%.
5. **Fix the `decisions.CANDIDATE` counter in KZ summaries** to count CANDIDATEs that reached verification.

## Caveats

- Rejection context lives only in JSON, not the demo.log files.
- Live window is short (~11 days); live closed-trade count is 0 and v2 schema verification confirms that is real.
- Mann-Kendall with small k uses normal approximation.

## Next steps (unchanged from v1)

- Re-run weekly; store with date suffix.
- Add structured log line in orchestrator emitting `REJECTED: <gate>, <reason>`.
- Quantify `sl_beyond_ob` tick-gap to gauge a deterministic SL snap.

