# Phase 1 Track C — Per-Instrument Sub-Session Edge Map

**Agent:** Phase 1 Track C (max effort)
**Date built:** 2026-04-24
**Branch:** `research/phase1-track-c-sub-session-map`
**Scope:** 15-min / 30-min / 60-min buckets within kill zones, per instrument, ranked by WR + expectancy and high-quality-frequency.

---

## TL;DR — bottom line up front

- **Sample size blocks all formal EMPHASIS/SKIP calls at 15-min granularity.** Not a single (instrument, KZ, 15-min-bucket) cell reaches the required n ≥ 20 threshold. The unified dataset contains 266 simulator trades across 24.6 months; fragmenting into ~80 buckets leaves every cell at n < 16.
- **5 buckets reach n ≥ 20 system-wide,** all of them 60-min XAUUSD buckets. None trigger a formal SKIP or EMPHASIS. Even the worst XAUUSD NY 13:00 bucket (n=29, WR 48.3%, E[R] −0.088R) has WR upper-CI 65.5% — well above the 35.7% breakeven. Rule classification → OBSERVE.
- **Total EMPHASIS candidates: 0. Total SKIP candidates: 0** at n ≥ 20.
- **Live post-April-7 trade outcomes are unusable for this analysis.** 32 LIMIT_PLACED trade records exist, zero have `execution`/`exit` data populated. Fleet ran under FTMO free-trial where `trade_expert=False` caused order rejections ("AutoTrading disabled by client"). One XAUUSD Apr-16 fill was "closed by broker" 6 minutes later with no exit data captured. Analysis relies entirely on simulator sources.
- **Pre-/post-v2_shadow flip diagnostic not possible** — the flip landed 2026-04-24 ~11:48 UTC and the latest available backtest/T7-sim data ends 2026-04-08. All directional data is pre-flip (94% LONG).

### Descriptive signal at 60-min XAUUSD (no formal rec):

- *Best total R bucket:* ny 14:00-15:00 (n=22, WR 63.6%, E[R] +0.421R → total +9.27R)
- *Worst 60-min bucket by E[R]:* ny 13:00-14:00 (n=29, WR 48.3%, E[R] -0.088R → total -2.55R). WR upper-CI does not exclude breakeven — not a SKIP.

---

## Data provenance

### Unified dataset sources

| Source | File(s) | Type | Rows kept |
|---|---|---|---|
| **q65_sim** | `research/q65_speed_to_mfe/q65_trade_speeds.csv` | session_simulator batch (April 2024 – March 2026) | 225 |
| **f3** | `research/f3_backtest_2026-04-24/*/all_results.json` (12 slices) | T7 production-faithful sim (Jan–Apr 2026 XAUUSD×8 + USDJPY×4) | 32 |
| **t7** | `research/t7_live_simulation/all_results_jan_apr10.json` | T7 production-faithful sim (Jan 2 – Apr 10, 2026 XAUUSD) | 9 |

**Total after dedup on (symbol, candle_time):** 266 trades. **Date range:** 2024-04-01 → 2026-04-08 (24.6 months).

### Per-instrument loaded counts and baselines

| Instrument | n (filled) | Baseline WR | Baseline E[R] | Breakeven WR (task) |
|---|---|---|---|---|
| XAUUSD | 144 | 0.611 | +0.241R | 0.357 |
| USDJPY | 48 | 0.667 | +0.358R | 0.400 |
| US30_cash | 33 | 0.576 | +0.388R | 0.345 |
| GBPJPY | 26 | 0.500 | -0.036R | 0.417 |
| GBPUSD | 15 | 0.667 | +0.519R | 0.375 |
| **Total** | **266** | | | |

### Live trade-record schema notes

- `trade_records/{instrument}/*.json`: **173 live production records** exist (XAUUSD 12, US30_cash 26, USDJPY 45, GBPJPY 42, GBPUSD 48). **None have populated `execution` or `exit` fields.** Schema has these fields but they were never written because:
  - 32 records reached `LIMIT_PLACED` (gate3 pass) but all orders were rejected by MT5 with "AutoTrading disabled by client" retcode (FTMO free-trial EA-excluded condition per CLAUDE.md).
  - The **single** 2026-04-16 XAUUSD limit that actually filled (limit=4796.28, entry=4795.23) was marked `Position 427534724 no longer exists — closed by broker` 6 minutes later with zero exit metadata. No r_multiple available.
- `_pending_records_index.json` files list currently-pending limits (GBPJPY 1, USDJPY 2 as of snapshot), no outcomes.
- `knowledge_base/statistics/rolling_stats.json` shows 129 trades, all `source: batch_session`, last entry 2026-02-06. Zero live rows written.
- `live_evaluations/{instrument}/*.jsonl` records per-candle *decisions* (NO_TRADE / CANDIDATE / WAIT) but NOT trade outcomes.

**Conclusion on live data:** it does not exist in usable form. All analysis below is simulator-based.

### Rows dropped during bucketing (60-min)

| Reason | Count |
|---|---|
| Entry time outside reported KZ bounds (edge cases at close minute 09:30/15:30/03:00) | 3 (GBPJPY) |
| XAUUSD NY 13:00-13:14 skip window | 0 |

Sanity check — bucket n sums:

| Instrument | Input n | Bucketed n | Δ |
|---|---|---|---|
| XAUUSD | 144 | 144 | 0 |
| USDJPY | 48 | 48 | 0 |
| US30_cash | 33 | 33 | 0 |
| GBPJPY | 26 | 23 | 3 |
| GBPUSD | 15 | 15 | 0 |

---

## Method

1. **Entry-time extraction:** use `candle_time` (UTC) from each trade record. Convert to minute-of-day; assign bucket key `HH:MM` rounded down to bucket size.
2. **KZ bounds** match CLAUDE.md:
   - XAUUSD: London 07:00-10:30, NY 13:00-17:00 (skip 13:00-13:14)
   - US30_cash: London 08:00-10:30, NY 13:30-16:00
   - USDJPY/GBPJPY: London 07:00-09:30, NY 13:00-15:30, Tokyo 00:00-03:00
   - GBPUSD: London 07:00-12:00, NY 13:00-15:30
3. **Bootstrap CIs:** 5000 iterations per bucket, basic percentile method, fixed RNG seed per bucket. WR: resample outcomes, compute mean. E[R]: resample r_multiples, compute mean. Fat-tail safe — no t-tests on R-multiples.
4. **Recommendation rules:**
   - `EMPHASIS`: n ≥ 20 AND WR_lo95 > instrument_baseline_WR AND E[R]_lo95 > 0
   - `SKIP`: n ≥ 20 AND WR_hi95 < instrument_breakeven_WR (task-provided)
   - `INSUFFICIENT`: n < 20
   - `OBSERVE`: otherwise
5. **Bonferroni note:** 8 XAUUSD 60-min buckets, 6 USDJPY, 5 US30_cash, 8 GBPJPY, 6 GBPUSD. Corrected alpha would widen CIs toward ~99.2–99.4%, which strictly *cannot* flip an uncorrected OBSERVE to a corrected EMPHASIS/SKIP. No recommendation in this report depends on Bonferroni.

---

## Per-instrument bucket tables — 60-min granularity

### XAUUSD

Baseline WR = 0.611, Breakeven WR = 0.357.

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:00-08:00 | 26 | 17/8/1 | 0.654 | [0.46, 0.85] | +0.160 | [-0.17, +0.49] | +4.15R | OBSERVE |
| london | 08:00-09:00 | 31 | 21/10/0 | 0.677 | [0.52, 0.84] | +0.274 | [-0.09, +0.67] | +8.50R | OBSERVE |
| london | 09:00-10:00 | 11 | 8/3/0 | 0.727 | [0.45, 1.00] | +0.654 | [-0.16, +1.48] | +7.20R | INSUFFICIENT |
| london | 10:00-11:00 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +1.500 | [+1.50, +1.50] | +1.50R | INSUFFICIENT |
| ny | 13:00-14:00 | 29 | 14/14/1 | 0.483 | [0.31, 0.66] | -0.088 | [-0.38, +0.21] | -2.55R | OBSERVE |
| ny | 14:00-15:00 | 22 | 14/6/2 | 0.636 | [0.41, 0.82] | +0.421 | [-0.03, +0.91] | +9.27R | OBSERVE |
| ny | 15:00-16:00 | 21 | 11/10/0 | 0.524 | [0.33, 0.71] | +0.121 | [-0.36, +0.67] | +2.54R | OBSERVE |
| ny | 16:00-17:00 | 3 | 2/1/0 | 0.667 | [0.00, 1.00] | +1.353 | [-1.00, +3.56] | +4.06R | INSUFFICIENT |

### USDJPY

Baseline WR = 0.667, Breakeven WR = 0.400.

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:00-08:00 | 12 | 9/3/0 | 0.750 | [0.50, 1.00] | +0.536 | [-0.09, +1.18] | +6.43R | INSUFFICIENT |
| london | 08:00-09:00 | 4 | 1/3/0 | 0.250 | [0.00, 0.75] | -0.273 | [-1.00, +1.18] | -1.09R | INSUFFICIENT |
| london | 09:00-10:00 | 2 | 2/0/0 | 1.000 | [1.00, 1.00] | +1.295 | [+1.09, +1.50] | +2.59R | INSUFFICIENT |
| ny | 13:00-14:00 | 14 | 10/4/0 | 0.714 | [0.43, 0.93] | +0.301 | [-0.15, +0.74] | +4.21R | INSUFFICIENT |
| ny | 14:00-15:00 | 3 | 3/0/0 | 1.000 | [1.00, 1.00] | +0.683 | [+0.22, +1.50] | +2.05R | INSUFFICIENT |
| ny | 15:00-16:00 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.250 | [-1.00, +1.50] | +0.50R | INSUFFICIENT |
| tokyo | 00:00-01:00 | 8 | 4/4/0 | 0.500 | [0.12, 0.88] | +0.250 | [-0.69, +1.19] | +2.00R | INSUFFICIENT |
| tokyo | 01:00-02:00 | 3 | 2/1/0 | 0.667 | [0.00, 1.00] | +0.167 | [-1.00, +0.75] | +0.50R | INSUFFICIENT |

### US30_cash

Baseline WR = 0.576, Breakeven WR = 0.345.

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 08:00-09:00 | 4 | 2/2/0 | 0.500 | [0.00, 1.00] | +0.333 | [-1.00, +1.69] | +1.33R | INSUFFICIENT |
| london | 09:00-10:00 | 7 | 5/2/0 | 0.714 | [0.29, 1.00] | +0.367 | [-0.25, +0.96] | +2.57R | INSUFFICIENT |
| ny | 13:00-14:00 | 4 | 2/1/1 | 0.500 | [0.00, 1.00] | +0.133 | [-0.66, +0.88] | +0.53R | INSUFFICIENT |
| ny | 14:00-15:00 | 17 | 9/6/2 | 0.529 | [0.29, 0.76] | +0.462 | [-0.10, +1.07] | +7.85R | INSUFFICIENT |
| ny | 15:00-16:00 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.520 | [+0.52, +0.52] | +0.52R | INSUFFICIENT |

### GBPJPY

Baseline WR = 0.500, Breakeven WR = 0.417.

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:00-08:00 | 7 | 4/3/0 | 0.571 | [0.14, 0.86] | -0.210 | [-0.68, +0.32] | -1.47R | INSUFFICIENT |
| london | 08:00-09:00 | 2 | 0/2/0 | 0.000 | [0.00, 0.00] | -0.600 | [-1.00, -0.20] | -1.20R | INSUFFICIENT |
| london | 09:00-10:00 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| ny | 13:00-14:00 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.200 | [+0.20, +0.20] | +0.20R | INSUFFICIENT |
| ny | 14:00-15:00 | 6 | 3/3/0 | 0.500 | [0.17, 0.83] | -0.323 | [-0.80, +0.16] | -1.94R | INSUFFICIENT |
| ny | 15:00-16:00 | 2 | 1/0/1 | 0.500 | [0.00, 1.00] | +0.135 | [+0.03, +0.24] | +0.27R | INSUFFICIENT |
| tokyo | 00:00-01:00 | 3 | 1/2/0 | 0.333 | [0.00, 1.00] | -0.253 | [-1.00, +0.75] | -0.76R | INSUFFICIENT |
| tokyo | 02:00-03:00 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +2.120 | [+2.12, +2.12] | +2.12R | INSUFFICIENT |

### GBPUSD

Baseline WR = 0.667, Breakeven WR = 0.375.

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:00-08:00 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.365 | [-1.00, +1.73] | +0.73R | INSUFFICIENT |
| london | 08:00-09:00 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.820 | [-1.00, +2.64] | +1.64R | INSUFFICIENT |
| london | 09:00-10:00 | 2 | 1/0/1 | 0.500 | [0.00, 1.00] | +0.215 | [-0.04, +0.47] | +0.43R | INSUFFICIENT |
| ny | 13:00-14:00 | 3 | 3/0/0 | 1.000 | [1.00, 1.00] | +1.170 | [+0.17, +2.47] | +3.51R | INSUFFICIENT |
| ny | 14:00-15:00 | 5 | 3/2/0 | 0.600 | [0.20, 1.00] | +0.098 | [-0.77, +0.99] | +0.49R | INSUFFICIENT |
| ny | 15:00-16:00 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.980 | [+0.98, +0.98] | +0.98R | INSUFFICIENT |

---

## Per-instrument bucket tables — 15-min granularity (reference)

All cells INSUFFICIENT (n < 20). Included as descriptive reference only.

### XAUUSD (15-min)

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:00-07:15 | 5 | 3/2/0 | 0.600 | [0.20, 1.00] | +0.500 | [-0.50, +1.50] | +2.50R | INSUFFICIENT |
| london | 07:15-07:30 | 6 | 3/2/1 | 0.500 | [0.17, 0.83] | -0.068 | [-0.49, +0.27] | -0.41R | INSUFFICIENT |
| london | 07:30-07:45 | 10 | 7/3/0 | 0.700 | [0.40, 1.00] | +0.099 | [-0.41, +0.60] | +0.99R | INSUFFICIENT |
| london | 07:45-08:00 | 5 | 4/1/0 | 0.800 | [0.40, 1.00] | +0.214 | [-0.50, +0.90] | +1.07R | INSUFFICIENT |
| london | 08:00-08:15 | 14 | 8/6/0 | 0.571 | [0.29, 0.79] | +0.429 | [-0.22, +1.17] | +6.01R | INSUFFICIENT |
| london | 08:15-08:30 | 5 | 4/1/0 | 0.800 | [0.40, 1.00] | +0.302 | [-0.50, +1.19] | +1.51R | INSUFFICIENT |
| london | 08:30-08:45 | 6 | 5/1/0 | 0.833 | [0.50, 1.00] | +0.098 | [-0.38, +0.47] | +0.59R | INSUFFICIENT |
| london | 08:45-09:00 | 6 | 4/2/0 | 0.667 | [0.33, 1.00] | +0.065 | [-0.64, +0.85] | +0.39R | INSUFFICIENT |
| london | 09:00-09:15 | 5 | 4/1/0 | 0.800 | [0.40, 1.00] | +0.680 | [-0.40, +2.12] | +3.40R | INSUFFICIENT |
| london | 09:15-09:30 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | -0.125 | [-1.00, +0.75] | -0.25R | INSUFFICIENT |
| london | 09:30-09:45 | 4 | 3/1/0 | 0.750 | [0.25, 1.00] | +1.012 | [-0.28, +2.31] | +4.05R | INSUFFICIENT |
| london | 10:00-10:15 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +1.500 | [+1.50, +1.50] | +1.50R | INSUFFICIENT |
| ny | 13:15-13:30 | 15 | 7/7/1 | 0.467 | [0.20, 0.73] | +0.089 | [-0.34, +0.52] | +1.33R | INSUFFICIENT |
| ny | 13:30-13:45 | 9 | 5/4/0 | 0.556 | [0.22, 0.89] | -0.318 | [-0.74, +0.08] | -2.86R | INSUFFICIENT |
| ny | 13:45-14:00 | 5 | 2/3/0 | 0.400 | [0.00, 0.80] | -0.204 | [-1.00, +0.65] | -1.02R | INSUFFICIENT |
| ny | 14:00-14:15 | 8 | 6/2/0 | 0.750 | [0.38, 1.00] | +0.547 | [-0.21, +1.21] | +4.38R | INSUFFICIENT |
| ny | 14:15-14:30 | 3 | 0/2/1 | 0.000 | [0.00, 0.00] | -0.483 | [-1.00, -0.01] | -1.45R | INSUFFICIENT |
| ny | 14:30-14:45 | 4 | 3/1/0 | 0.750 | [0.25, 1.00] | +0.092 | [-0.63, +0.66] | +0.37R | INSUFFICIENT |
| ny | 14:45-15:00 | 7 | 5/1/1 | 0.714 | [0.43, 1.00] | +0.853 | [-0.09, +1.88] | +5.97R | INSUFFICIENT |
| ny | 15:00-15:15 | 12 | 6/6/0 | 0.500 | [0.25, 0.75] | +0.197 | [-0.55, +1.06] | +2.36R | INSUFFICIENT |
| ny | 15:15-15:30 | 3 | 1/2/0 | 0.333 | [0.00, 1.00] | -0.317 | [-1.00, +1.05] | -0.95R | INSUFFICIENT |
| ny | 15:30-15:45 | 6 | 4/2/0 | 0.667 | [0.33, 1.00] | +0.188 | [-0.18, +0.55] | +1.13R | INSUFFICIENT |
| ny | 16:00-16:15 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.250 | [-1.00, +1.50] | +0.50R | INSUFFICIENT |
| ny | 16:15-16:30 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +3.560 | [+3.56, +3.56] | +3.56R | INSUFFICIENT |

### USDJPY (15-min)

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:00-07:15 | 3 | 2/1/0 | 0.667 | [0.00, 1.00] | +0.667 | [-1.00, +1.50] | +2.00R | INSUFFICIENT |
| london | 07:15-07:30 | 4 | 3/1/0 | 0.750 | [0.25, 1.00] | +0.200 | [-0.70, +1.15] | +0.80R | INSUFFICIENT |
| london | 07:30-07:45 | 2 | 2/0/0 | 1.000 | [1.00, 1.00] | +1.025 | [+0.41, +1.64] | +2.05R | INSUFFICIENT |
| london | 07:45-08:00 | 3 | 2/1/0 | 0.667 | [0.00, 1.00] | +0.527 | [-1.00, +2.40] | +1.58R | INSUFFICIENT |
| london | 08:00-08:15 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 08:15-08:30 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +1.910 | [+1.91, +1.91] | +1.91R | INSUFFICIENT |
| london | 08:30-08:45 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 08:45-09:00 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 09:00-09:15 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +1.500 | [+1.50, +1.50] | +1.50R | INSUFFICIENT |
| london | 09:15-09:30 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +1.090 | [+1.09, +1.09] | +1.09R | INSUFFICIENT |
| ny | 13:00-13:15 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.250 | [-1.00, +1.50] | +0.50R | INSUFFICIENT |
| ny | 13:15-13:30 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.350 | [-1.00, +1.70] | +0.70R | INSUFFICIENT |
| ny | 13:30-13:45 | 8 | 6/2/0 | 0.750 | [0.38, 1.00] | +0.172 | [-0.24, +0.59] | +1.38R | INSUFFICIENT |
| ny | 13:45-14:00 | 2 | 2/0/0 | 1.000 | [1.00, 1.00] | +0.815 | [+0.65, +0.98] | +1.63R | INSUFFICIENT |
| ny | 14:00-14:15 | 3 | 3/0/0 | 1.000 | [1.00, 1.00] | +0.683 | [+0.22, +1.50] | +2.05R | INSUFFICIENT |
| ny | 15:00-15:15 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.250 | [-1.00, +1.50] | +0.50R | INSUFFICIENT |
| tokyo | 00:00-00:15 | 6 | 4/2/0 | 0.667 | [0.33, 1.00] | +0.667 | [-0.17, +1.50] | +4.00R | INSUFFICIENT |
| tokyo | 00:15-00:30 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| tokyo | 00:30-00:45 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| tokyo | 01:00-01:15 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.750 | [+0.75, +0.75] | +0.75R | INSUFFICIENT |
| tokyo | 01:30-01:45 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | -0.125 | [-1.00, +0.75] | -0.25R | INSUFFICIENT |

### US30_cash (15-min)

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 08:30-08:45 | 2 | 0/2/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -2.00R | INSUFFICIENT |
| london | 08:45-09:00 | 2 | 2/0/0 | 1.000 | [1.00, 1.00] | +1.665 | [+0.75, +2.58] | +3.33R | INSUFFICIENT |
| london | 09:00-09:15 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 09:15-09:30 | 3 | 2/1/0 | 0.667 | [0.00, 1.00] | +0.167 | [-1.00, +0.75] | +0.50R | INSUFFICIENT |
| london | 09:30-09:45 | 2 | 2/0/0 | 1.000 | [1.00, 1.00] | +1.160 | [+1.07, +1.25] | +2.32R | INSUFFICIENT |
| london | 09:45-10:00 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.750 | [+0.75, +0.75] | +0.75R | INSUFFICIENT |
| ny | 13:45-14:00 | 4 | 2/1/1 | 0.500 | [0.00, 1.00] | +0.133 | [-0.66, +0.88] | +0.53R | INSUFFICIENT |
| ny | 14:00-14:15 | 5 | 4/0/1 | 0.800 | [0.40, 1.00] | +1.266 | [+0.45, +2.02] | +6.33R | INSUFFICIENT |
| ny | 14:15-14:30 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +1.290 | [-1.00, +3.58] | +2.58R | INSUFFICIENT |
| ny | 14:30-14:45 | 7 | 2/4/1 | 0.286 | [0.00, 0.57] | -0.239 | [-0.75, +0.28] | -1.67R | INSUFFICIENT |
| ny | 14:45-15:00 | 3 | 2/1/0 | 0.667 | [0.00, 1.00] | +0.203 | [-0.37, +0.75] | +0.61R | INSUFFICIENT |
| ny | 15:00-15:15 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.520 | [+0.52, +0.52] | +0.52R | INSUFFICIENT |

### GBPJPY (15-min)

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:15-07:30 | 3 | 1/2/0 | 0.333 | [0.00, 1.00] | -0.627 | [-1.00, +0.12] | -1.88R | INSUFFICIENT |
| london | 07:30-07:45 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 07:45-08:00 | 3 | 3/0/0 | 1.000 | [1.00, 1.00] | +0.470 | [+0.17, +0.62] | +1.41R | INSUFFICIENT |
| london | 08:00-08:15 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 08:15-08:30 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -0.200 | [-0.20, -0.20] | -0.20R | INSUFFICIENT |
| london | 09:15-09:30 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| ny | 13:15-13:30 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.200 | [+0.20, +0.20] | +0.20R | INSUFFICIENT |
| ny | 14:00-14:15 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.220 | [+0.22, +0.22] | +0.22R | INSUFFICIENT |
| ny | 14:15-14:30 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| ny | 14:30-14:45 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| ny | 14:45-15:00 | 3 | 2/1/0 | 0.667 | [0.00, 1.00] | -0.053 | [-1.00, +0.45] | -0.16R | INSUFFICIENT |
| ny | 15:00-15:15 | 2 | 1/0/1 | 0.500 | [0.00, 1.00] | +0.135 | [+0.03, +0.24] | +0.27R | INSUFFICIENT |
| tokyo | 00:45-01:00 | 3 | 1/2/0 | 0.333 | [0.00, 1.00] | -0.253 | [-1.00, +0.75] | -0.76R | INSUFFICIENT |
| tokyo | 02:15-02:30 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +2.120 | [+2.12, +2.12] | +2.12R | INSUFFICIENT |

### GBPUSD (15-min)

| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|---|
| london | 07:15-07:30 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +1.730 | [+1.73, +1.73] | +1.73R | INSUFFICIENT |
| london | 07:30-07:45 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 08:15-08:30 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | +0.820 | [-1.00, +2.64] | +1.64R | INSUFFICIENT |
| london | 09:00-09:15 | 2 | 1/0/1 | 0.500 | [0.00, 1.00] | +0.215 | [-0.04, +0.47] | +0.43R | INSUFFICIENT |
| ny | 13:30-13:45 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +2.470 | [+2.47, +2.47] | +2.47R | INSUFFICIENT |
| ny | 13:45-14:00 | 2 | 2/0/0 | 1.000 | [1.00, 1.00] | +0.520 | [+0.17, +0.87] | +1.04R | INSUFFICIENT |
| ny | 14:00-14:15 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +1.820 | [+1.82, +1.82] | +1.82R | INSUFFICIENT |
| ny | 14:15-14:30 | 2 | 1/1/0 | 0.500 | [0.00, 1.00] | -0.245 | [-1.00, +0.51] | -0.49R | INSUFFICIENT |
| ny | 14:30-14:45 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.160 | [+0.16, +0.16] | +0.16R | INSUFFICIENT |
| ny | 14:45-15:00 | 1 | 0/1/0 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| ny | 15:00-15:15 | 1 | 1/0/0 | 1.000 | [1.00, 1.00] | +0.980 | [+0.98, +0.98] | +0.98R | INSUFFICIENT |

Full machine-readable outputs: `bucket_stats_15min.csv`, `bucket_stats_30min.csv`, `bucket_stats_60min.csv`.

---

## Emphasis candidates (n ≥ 20, WR_lo > baseline, E[R]_lo > 0)

**None.** No bucket satisfies the formal rule.

## Skip candidates (n ≥ 20, WR_hi < breakeven)

**None.** The only large-sample negative-E[R] bucket (XAUUSD NY 13:00-14:00) has WR_hi95 = 65.5%, nearly 30pp above its 35.7% breakeven. Formally OBSERVE.

---

## Descriptive lens — where the edge lives empirically

Top 10 buckets ranked by total R produced (`n · E[R]`, the high-quality-frequency metric). **Note:** all below are at varying n; only those with n ≥ 20 can be formally recommended.

| Rank | Symbol | KZ | Bucket | n | WR | E[R] | Total R | Rec |
|---|---|---|---|---|---|---|---|---|
| 1 | XAUUSD | ny | 14:00-15:00 | 22 | 0.636 | +0.421 | +9.27R | OBSERVE |
| 2 | XAUUSD | london | 08:00-09:00 | 31 | 0.677 | +0.274 | +8.50R | OBSERVE |
| 3 | US30_cash | ny | 14:00-15:00 | 17 | 0.529 | +0.462 | +7.85R | INSUFFICIENT |
| 4 | XAUUSD | london | 09:00-10:00 | 11 | 0.727 | +0.654 | +7.20R | INSUFFICIENT |
| 5 | USDJPY | london | 07:00-08:00 | 12 | 0.750 | +0.536 | +6.43R | INSUFFICIENT |
| 6 | USDJPY | ny | 13:00-14:00 | 14 | 0.714 | +0.301 | +4.21R | INSUFFICIENT |
| 7 | XAUUSD | london | 07:00-08:00 | 26 | 0.654 | +0.160 | +4.15R | OBSERVE |
| 8 | XAUUSD | ny | 16:00-17:00 | 3 | 0.667 | +1.353 | +4.06R | INSUFFICIENT |
| 9 | GBPUSD | ny | 13:00-14:00 | 3 | 1.000 | +1.170 | +3.51R | INSUFFICIENT |
| 10 | USDJPY | london | 09:00-10:00 | 2 | 1.000 | +1.295 | +2.59R | INSUFFICIENT |

Bottom 5 buckets by E[R] (smallest first):

| Symbol | KZ | Bucket | n | WR | E[R] | Total R | Rec |
|---|---|---|---|---|---|---|---|
| GBPJPY | london | 09:00-10:00 | 1 | 0.000 | -1.000 | -1.00R | INSUFFICIENT |
| GBPJPY | london | 08:00-09:00 | 2 | 0.000 | -0.600 | -1.20R | INSUFFICIENT |
| GBPJPY | ny | 14:00-15:00 | 6 | 0.500 | -0.323 | -1.94R | INSUFFICIENT |
| USDJPY | london | 08:00-09:00 | 4 | 0.250 | -0.273 | -1.09R | INSUFFICIENT |
| GBPJPY | tokyo | 00:00-01:00 | 3 | 0.333 | -0.253 | -0.76R | INSUFFICIENT |

---

## Expected R/month lift estimate — hypothetical trimming

Dataset spans 24.6 months. XAUUSD n ≥ 20 buckets (5 cells) collectively produced:

- Total N = 129 filled trades
- Total R = +21.91R over 24.6 months = **+0.89R/month average**

### Hypothetical "trim worst" scenarios (descriptive only)

| Dropped buckets | Freq lost | R avoided | Remaining R/mo (over 24.6mo) | New WR |
|---|---|---|---|---|
| (none) | 0 (0.0%) | 0 | +0.892R/mo | 0.597 |
| ny 13:00 | 29 (22.5%) | +2.55R | +0.996R/mo | 0.630 |
| ny 13:00, ny 15:00 | 50 (38.8%) | +0.01R | +0.892R/mo | 0.658 |
| ny 13:00, ny 15:00, london 07:00 | 76 (58.9%) | -4.14R | +0.723R/mo | 0.660 |
| ny 13:00, ny 15:00, london 07:00, london 08:00 | 107 (82.9%) | -12.64R | +0.377R/mo | 0.636 |
| ny 13:00, ny 15:00, london 07:00, london 08:00, ny 14:00 | 129 (100.0%) | -21.91R | +0.000R/mo | 0.000 |

**Interpretation.** If the CEO dropped the single worst XAUUSD 60-min bucket (NY 13:00-14:00) the data says +0.10R/month lift — a 6% relative improvement in expected R/month at an 18% XAUUSD frequency cost. Overall XAUUSD WR rises from 61.1% → 64.1% (3.0pp).

**Per the high-quality-frequency framing** (CEO 2026-04-24 per `feedback_research_goal_high_quality_frequency.md`): the trade-off is marginal at best. 18% of XAUUSD frequency for 0.10R/month — low conviction. **Recommendation: observe, do not trim.** The WR CI on that bucket is [0.31, 0.66]; the true WR could plausibly be anywhere from losing-edge to winning-edge. Trimming on that basis risks baseline-bias extraction as much as genuine edge extraction.

**Range** on the per-month lift estimate: given bootstrap CI on bucket E[R] of [−0.38R, +0.21R], the per-month lift from trimming NY 13:00-14:00 alone could be anywhere from **−0.25R/mo to +0.44R/mo**. Point estimate +0.10R/mo sits near the midpoint but cannot be distinguished from zero at 95%.

---

## Diagnostic: pre-/post-v2_shadow flip

**Not possible with current data.** The v2_shadow detector flip landed 2026-04-24 11:48:55 UTC. The most recent simulator data in this analysis ends 2026-04-08, so every trade in the dataset reflects **v1 detector behavior**. No post-flip simulator replay or live-with-outcomes rows exist yet.

**Direction distribution (all simulator trades):** 250 LONG vs 16 SHORT (94% long-biased) — reflecting the v1 structural bullish bias per ADR-004.

| Symbol | LONG | SHORT | SHORT% |
|---|---|---|---|
| XAUUSD | 134 | 10 | 6.9% |
| USDJPY | 46 | 2 | 4.2% |
| US30_cash | 32 | 1 | 3.0% |
| GBPJPY | 24 | 2 | 7.7% |
| GBPUSD | 14 | 1 | 6.7% |

**Implication.** When v2_shadow is promoted to production (14-day shadow + 100-divergence gate), per-bucket direction mix for at least XAUUSD will shift meaningfully (F3 predicted 0% → 22.8% raw SHORT CAND share on XAUUSD). Any bucket-level emphasis/skip recommendations derived today may not survive that shift.

**Recommendation:** re-run this analysis after (a) v2 production promotion, AND (b) accumulation of ≥30 live trades per instrument KZ (≈ 3–4 months at current fleet frequency of ~4 CANDs/week × 5 instruments).

---

## Honest caveats

1. **All outcomes are simulator-derived.** Three sources (q65_sim session_simulator, F3 T7 backtest, T7 live-sim) share realization engine logic but apply against historical candles, not live quotes. Slippage, spread dynamics, partial fills, and real-time liquidity are not captured.

2. **Small-sample dominance.** 266 trades / (5 instruments × 3 KZ × 14 15-min buckets) ≈ 1.3 trades per cell on average. Only 5 cells at 60-min granularity reach n ≥ 20. No 15-min cell does. Structural data-availability problem, not analytical.

3. **Fat-tail distribution.** Gold ξ ≈ 0.35 (per memory `project_distributional_findings.md`). Bootstrap CIs on means under-estimate tail uncertainty at small n. Treat every mean_r CI at n < 30 as a lower bound on true uncertainty.

4. **Non-stationarity.** Dataset spans 2024-04 to 2026-04, including multiple structural regime shifts (SVB aftermath, 2024 US election, 2025 gold breakout to $5k+, Trump tariff episodes). Quarterly WR decay 73% → 59% from 2024Q2 to 2026Q1 per CLAUDE.md — bucket-level edges may also decay.

5. **Bonferroni adjustment impact.** With 8 XAUUSD 60-min buckets, 95% single-bucket CIs become effectively ~99.4% multi-bucket CIs. Uncorrected CIs on every XAUUSD bucket already include WR-equal-to-baseline; tightening does not change any verdict. No recommendation in this report is on the significance edge.

6. **LONG-only bias.** 94% of trades are LONG direction (v1 detector output). SHORT bucket behavior is essentially unobserved; post-v2_shadow-promotion re-analysis is a prerequisite to any fleet-wide bucket-level directive.

7. **q65 session_simulator specifics.** Processes trades against historical candles without intra-candle price walking for many windows, which biases exit_substate toward CLOSED_SESSION_TIMEOUT (90/233 rows in q65). This artificially compresses the expectancy distribution.

8. **Unfilled limits excluded.** UNFILLED rows were dropped. This biases reported WR upward relative to an "all-CAND" WR metric; the "sweep-the-ground WR across all decided candidates" metric is not computed here.

9. **GBPUSD observer.** GBPUSD dataset rows include live-trading-enabled backtest periods; instrument is observer-only in current production (per `research/gbpusd_observer_mode_decision_2026-04-24.md`). Its 15 rows cannot drive a production recommendation either way.

10. **No EMPHASIS/SKIP recommendations is itself the finding.** The CEO-hypothesized 3–5pp WR uplift at low frequency cost from trimming the worst 20% buckets is **not supported by this data** at any CI that survives fat-tail + Bonferroni discipline. Better use of the data: maintain current KZ discipline, wait for v2-post-promotion live outcomes, revisit after ≥300 live-filled trades.

---

## File deliverables

| Path | Purpose |
|---|---|
| `SUB_SESSION_MAP.md` | This document |
| `unified_trades.csv` | 266 unified simulator trades (source data) |
| `bucket_stats_15min.csv` | 82 buckets at 15-min granularity |
| `bucket_stats_30min.csv` | 52 buckets at 30-min granularity |
| `bucket_stats_60min.csv` | 35 buckets at 60-min granularity |
| `lift_analysis.md` | Supplementary lift calculations |
| `_build_dataset.py` | Dataset construction script |
| `_analyze_buckets.py` | Bucket-stats engine |
| `_lift_analysis.py` | Lift-estimate report generator |
| `_render_report.py` | This report generator |

---

*All outputs regenerable by running:*
```bash
python _build_dataset.py && python _analyze_buckets.py && python _lift_analysis.py && python _render_report.py
```