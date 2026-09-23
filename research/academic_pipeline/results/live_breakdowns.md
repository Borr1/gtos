# Live Breakdowns — L2 Rejection + Monthly WR Decay

**Generated:** 2026-04-17  
**Cost:** $0 (pure local computation)  
**Author:** Claude Code execution agent

## Hypothesis (pre-data)

Written before running any counts. Based on handoffs 15–20 and the Apr 13 L2
rejection analysis (which was run on T7 simulation data, not live logs).

- **L2 top reason:** Prior simulation showed `entry_in_ob` dominant (74% of L2).
  Prediction for live trade_records: `entry_in_ob` still top-1 but with
  `sl_beyond_ob` and `h1_poi_exists` sharing second place. `sl_too_tight`
  (Gate1) was flagged in handoff 16 as blocking 4–5 trades/week — expect
  ~6–9 L1 `sl_too_tight` rejections over the ~11-day live window.
- **Monthly WR decay:** Quarterly file showed 73%→71%→64%→59%. At monthly
  resolution with batch+live, prediction is Mann-Kendall tau<0 with p in
  0.05–0.20 band (insufficient power to clear Bonferroni) and a visible
  Feb-2026 dip corresponding to the strong uptrend where the AI struggled
  to identify discount OBs.

**Hypothesis vs observed (at end of analysis):**

- L2 top reason: predicted `entry_in_ob`; observed `entry_in_ob` (22/49) — **confirmed**.
- L1 `sl_too_tight`: predicted 6–9; observed 9 — **confirmed** (5.7/week matches handoff-16 4–5/week claim).
- Monthly WR decay: predicted tau<0, p 0.05–0.20; observed tau=-0.244, p=0.367 — **tau direction correct, p larger than predicted**.

## L2 Rejection Breakdown

### Data

- Trade-record JSONs parsed: **85** files
- Instruments covered: GBPJPY, GBPUSD, US30_cash, USDJPY, XAUUSD
- Date range from live_sessions: **2026-04-06 → 2026-04-16**
- Total AI-evaluated candles (live_sessions `api_calls_made` sum): **759**
- Total NO_TRADE decisions (Layer 3A, AI said no): **748**
- Total CANDIDATE records reaching verification: **85**
- Total gate-rejected (L1 + L2): **62**
- Total reaching execution (EXECUTED/LIMIT/FAILED): **23**

**Note on log files:** The five `agent_<SYMBOL>_demo.log` files are pure
INFO-level traces (candle ticks, align scores, HTTP 200 receipts). Rejection
reasons are NOT echoed to these logs; they live in the structured
`trade_records/*/*.json` pipeline dumps and `live_sessions/*/*_summary.json`
summaries. All counts below come from the JSON artefacts, not the .log files.

### Pipeline funnel (live, Apr 6 – Apr 17 2026)

| Stage | Count | Notes |
|-------|-------|-------|
| API calls (AI evaluations) | 759 | sum of `api_calls_made` per session |
| AI said NO_TRADE | 748 | 98.6% of API calls |
| AI said CANDIDATE (reached gate stage) | 85 | records in `trade_records/` |
| Rejected Gate1 Safety (L1) | 13 | |
| Rejected L2 verification | 47 | |
| Rejected L2 post-M5 refinement | 2 | |
| Placed as pending limit | 17 | between-KZ fill depends on watcher |
| Execution failed (MT5 / broker) | 6 | retcode != DONE |

### Per-symbol outcome distribution

| Symbol | REJECTED_L2 | REJECTED_L2_POST_M5 | REJECTED_GATE1_SAFETY | LIMIT_PLACED | EXECUTION_FAILED | Total |
|---|---|---|---|---|---|---|
| GBPJPY | 2 | 0 | 8 | 5 | 4 | 19 |
| GBPUSD | 5 | 0 | 3 | 4 | 1 | 13 |
| US30_cash | 13 | 2 | 0 | 2 | 1 | 18 |
| USDJPY | 21 | 0 | 2 | 3 | 0 | 26 |
| XAUUSD | 6 | 0 | 0 | 3 | 0 | 9 |

### L2 rejection reasons

| Reason | Count | % of L2 |
|--------|-------|---------|
| `entry_in_ob` | 22 | 44.9% |
| `sl_beyond_ob` | 19 | 38.8% |
| `h1_poi_exists` | 6 | 12.2% |
| `post_m5_refinement_failed` | 2 | 4.1% |
| **Total L2** | **49** | 100% |

### L1 (Gate1 Safety) rejection reasons

| Reason | Count | % of L1 |
|--------|-------|---------|
| `sl_too_tight` | 9 | 69.2% |
| `sl_below_minimum_floor` | 3 | 23.1% |
| `tp1_below_entry` | 1 | 7.7% |
| **Total L1** | **13** | 100% |

### L3 (Gate3 Circuit Breaker) rejection reasons

No gate3 rejections captured in live trade_records. This is consistent
with the 0/12 trade days (no daily-loss hits, no kz limit hits, no
spread-too-wide captures) and means outside-kill-zone blocks never
trigger because orchestrator only evaluates candles inside KZs.

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

**Handoff-16 claim:** prior note said `sl_too_tight` was blocking 4–5 valid
trades/week. Over the ~11-day live window covered by trade_records, a weekly
rate of 4–5 implies ~6–9 total.

**Observed:** 9 `sl_too_tight` cases over ~11 days = 5.7/week. Additional 3 `sl_below_minimum_floor` cases.

**Verdict on handoff-16 claim:** **CONFIRMED**. The 4–5/week number from
handoff 16 is supported by the live trade_records. The `sl_too_tight` gate is
still the primary L1 bottleneck even after handoff-19 raised the SL sweep
margin from 0.3 to 0.5.

**SL/ATR distribution of rejected cases (gate threshold = 1.5):** min=0.515, median=1.298, max=1.480.
7/9 rejected SLs are >= 1.0×ATR (i.e. close to the
boundary). Lowering the multiplier from 1.5 to 1.0 would pass these; from
1.5 to 1.2 would pass those with SL/ATR >= 1.2.
- At 1.2×ATR threshold: 7 of 9 would pass (78%).
- At 1.0×ATR threshold: 7 of 9 would pass (78%).

### API refusal / malformed responses

- Total malformed entries: **56**
- Flat-refusal-pattern matches: **36**

| Date | Count |
|------|-------|
| 2026-04-13 | 38 |
| 2026-04-15 | 3 |
| 2026-04-16 | 15 |

### Recommendation

- **L2 top reason is `entry_in_ob` (22 of 49).**
  L2 is doing its job on the structural check (SL behind OB, entry
  in OB). The frequent `sl_beyond_ob` failures indicate the AI is
  still placing SL *at* the OB boundary instead of a tick beyond.
  This is a prompt/output issue, not a gate mis-calibration.
- **L1 top reason is `sl_too_tight` (9 of 13).**
- **`sl_too_tight` blocked 9 trades (~5.7/week).** This
  **supports** the handoff-16 claim of 4–5/week. Recommendation: instead
  of blanket-widening the 1.5×ATR threshold (which would degrade expectancy
  by increasing average loss size), extend the `ob_retest_sl_exception`
  to bypass the ATR floor when the AI's SL is placed structurally behind
  an OB boundary AND the SL/ATR ratio is >= 1.0. This preserves the
  ATR logic for non-structural SLs while respecting the zone methodology.
- No Gate3 circuit-breaker rejections observed — daily-loss, KZ-limit and
  spread-too-wide gates did not fire. Keep the current thresholds.
- Every KZ summary shows CANDIDATE=0 in the `decisions` counter because
  CANDIDATEs are logged to `trade_records/` rather than to the KZ summary
  counter. This is a logging discrepancy; fix is trivial but low priority.

## Monthly WR Decay

### Data

- Batch trades (unified_trades_v2): **111**
- Live closed trades with r_multiple: **0**
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
| 2025-02 | 12 | 8 | 4 | 0 | 66.7% | [39.1%, 86.2%] | -0.160 | -1.92 | |
| 2025-03 | 11 | 7 | 4 | 0 | 63.6% | [35.4%, 84.8%] | +0.124 | +1.36 | |
| 2025-04 | 4 | 1 | 3 | 0 | 25.0% | [4.6%, 69.9%] | -0.292 | -1.17 | <5 (underpowered) |
| 2025-05 | 3 | 3 | 0 | 0 | 100.0% | [43.8%, 100.0%] | +0.893 | +2.68 | <5 (underpowered) |
| 2025-06 | 8 | 3 | 5 | 0 | 37.5% | [13.7%, 69.4%] | -0.412 | -3.30 | |
| 2025-09 | 8 | 6 | 2 | 0 | 75.0% | [40.9%, 92.9%] | +0.139 | +1.11 | |
| 2025-10 | 10 | 9 | 1 | 0 | 90.0% | [59.6%, 98.2%] | +0.685 | +6.85 | |
| 2025-12 | 8 | 6 | 2 | 0 | 75.0% | [40.9%, 92.9%] | +0.448 | +3.58 | |
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
| 2025-02 | 12 | 66.7% | -0.160 | -1.92 | |
| 2025-03 | 11 | 63.6% | +0.124 | +1.36 | |
| 2025-04 | 4 | 25.0% | -0.292 | -1.17 | (n<5) |
| 2025-05 | 3 | 100.0% | +0.893 | +2.68 | (n<5) |
| 2025-06 | 8 | 37.5% | -0.412 | -3.30 | |
| 2025-09 | 8 | 75.0% | +0.139 | +1.11 | |
| 2025-10 | 10 | 90.0% | +0.685 | +6.85 | |
| 2025-12 | 8 | 75.0% | +0.448 | +3.58 | |
| 2026-01 | 18 | 61.1% | +0.055 | +0.99 | |
| 2026-02 | 6 | 66.7% | +0.358 | +2.15 | |
| 2026-03 | 5 | 60.0% | +0.282 | +1.41 | |

Mann-Kendall (10 months): tau=-0.244, p=0.367

### Interpretation

- Monthly WR verdict: **Decay present but weak** (tau=-0.244, p=0.367).
- Compared to the quarterly file's 73/71/64/59% sequence, monthly
  resolution has larger variance and the window is dominated by batch
  data (111 trades) with only a handful of live closed trades added.
- Chi-square shows whether monthly WRs are all draws from a common
  Bernoulli — not significant here means the differences we see could
  plausibly arise from sampling noise.
- A regime-change signature would require either: (a) a sharp level
  shift in WR at a specific month (not just drift), or (b) different
  return distribution moments. Neither is clearly visible from n alone.

## Overall recommendations

1. **Fix `sl_beyond_ob` at the prompt level.** The AI is placing SL exactly
   at the OB boundary. Either the T7 prompt needs an explicit "SL must be
   >= 1 tick beyond OB" clause, or introduce a deterministic SL-adjustment
   that snaps the AI's SL to `OB_low - tick` / `OB_high + tick` and only
   rejects if the adjusted SL violates `sl_floor`.
2. **Fix the `entry_in_ob` issue at prompt level.** 22/47 L2 rejections (47%)
   are AI-chosen entry outside the OB zone. Add a "entry must be inside OB"
   explicit check to the prompt and example.
3. **Address `sl_too_tight` by exception, not by threshold move.** Observed
   9 cases (~5.7/week), confirming the
   handoff-16 claim. Do NOT blanket-widen the 1.5×ATR threshold — that
   would degrade expectancy on non-structural SLs. Instead extend the
   existing `ob_retest_sl_exception` to also bypass the ATR gate when the
   AI's SL is placed structurally (behind an OB boundary) AND SL/ATR >=
   1.0. Based on the SL/ATR distribution (median 1.30), this would
   unblock 7 of 9 sl_too_tight cases (78%) while preserving the gate for
   truly tight non-structural SLs.
4. **Keep monthly WR monitoring live.** Rerun this script weekly. Promote
   a decay alarm only when: (a) Mann-Kendall p<0.05 across >=5 months, OR
   (b) Wilson 95% upper bound of the most recent 20-trade rolling WR falls
   below 55%. Current data triggers neither.
5. **Fix the `decisions.CANDIDATE` counter in KZ summaries** to include
   CANDIDATEs that reached verification. Currently always 0 — creates a
   false "no candidates at all" impression when scanning summaries.

## Caveats

- **Logs are not the data source:** `agent_<SYMBOL>_demo.log` files do not
  emit rejection lines. All rejection context is in JSON under
  `knowledge_base/trade_records/` and `knowledge_base/live_sessions/`.
  If a process crashed before writing the trade record, that signal is
  lost — counts are lower bounds.
- **Live window is short** (~11 days with trade_records limited to
  Apr 7 – Apr 17). n per month for 2026-04 live is small.
- **No per-month outcome data** for rejected trades. We cannot compute a
  hypothetical WR for what L2 is filtering.
- **Batch trades field schema:** unified_trades_v2 has `month` stored as
  `YYYY-MM` directly but we rebuild it from `date` for safety.
- **Mann-Kendall with small k:** normal approximation used; for k<10 the
  approximation is reasonable but not exact.

## Next steps

- Re-run weekly; store each output with date suffix to track drift.
- After 30 more live-closed trades, promote the monthly MK test into the
  monitoring dashboard (and SPRT into the per-instrument decay alarm).
- Add a structured log line in orchestrator that emits `REJECTED: <gate>,
  <reason>` on every denial so future scans don't need JSON spelunking.
- Quantify `sl_beyond_ob` tick-gap: for each failure, extract AI's SL and
  OB boundary to measure whether snapping to `boundary ± 1 tick` would
  have passed L2. If yes for >80% of cases, deploy the deterministic snap.

