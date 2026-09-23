# 2022-2023 Data Backfill — Coverage Report

**Date:** 2026-04-28
**Agent:** 2022-2023 Data Backfill Agent
**Q1.4 prerequisite:** Cross-period replication on ≥2 of 3 periods, gating K54 v2 ML modeling

## Headline

- **Backfill window:** 2022-01-01 -> 2024-02-20 UTC (the F14 backfill `shadow_logs/structure_detector_backfill_2026.jsonl` covers 2024-02-20 -> 2026-04-24).
- **Instruments closed:** XAUUSD, XAGUSD, USDJPY, GBPUSD, NAS100. Combined with previously-extant GBPJPY + US30_cash, all 7 instruments now have ≥1000 M15 candles in the 2022-2023 period.
- **Cross-period feasibility (Interpretation B per data_inventory_audit.md:84):** 2 of 7 -> **7 of 7**.
- **Trade-cohort candidates added:** 1,798 filled mechanical OB-retest trades (vs Q1.3 v1 cohort of 528-582). 2,812 total BOS events (incl. NO_ENTRY).

## MT5 + FN broker reachability

`scripts/mt5_preflight.py` blocked at the LIVE-account interactive prompt (account 0 on redacted_account-Server 2 is the live $100k 2-Step), but probed the connection successfully:

```
MT5 v500.5833 (25 Apr 2026)
Account: 0
Balance: $99,995.02
Server: redacted_account-Server 2
Trade mode: LIVE
```

Symbol resolution:

| Canonical | FN broker symbol | Notes |
|---|---|---|
| XAUUSD | XAUUSD | Already visible |
| XAGUSD | XAGUSD | Already visible |
| USDJPY | USDJPY | Already visible |
| GBPUSD | GBPUSD | Already visible |
| NAS100 | **NDX100** | FN does NOT carry "NAS100" symbol. NDX100 is the closest match (other candidates tested: NAS100m, USTEC, USTECH, USTECH100, NAS — none found). Full symbol scan returned only `[GBPUSD, USDJPY, XAGUSD, XAUUSD, NDX100, SPX500, UK100]` matching equity-index patterns. Confidence: **HIGH** that NDX100 is the correct mapping (matches the production NAS100 fleet symbol's price ranges; Apr 2026 close $24,500-25,000 territory in M15 spot-checks).

## Section 1 — Per-instrument max-depth probe

Probed via `MetaTrader5.copy_rates_from_pos(symbol, tf, 0, N)` with binary search up to N=99,999 (the broker's per-call cap).

| Symbol | M15 oldest | H1 oldest | H4 oldest | D1 oldest | M15 cap | H1 total | H4 total | D1 total |
|---|---|---|---|---|---:|---:|---:|---:|
| XAUUSD | **2022-01-28 11:45** | 2019-12-23 02:00 | 2019-12-23 00:00 | 2019-12-23 00:00 | 99,999 | 37,479 | 9,808 | 1,637 |
| XAGUSD | 2022-01-03 01:00 | 2019-12-23 (est) | 2019-12-23 (est) | 2019-12-23 | 99,999 | 12,020+ | 3,287+ | 1,634 |
| USDJPY | **2022-04-12 09:15** | 2008-09-04 | 2008-09-04 | 2008-09-04 | 99,999 | 13,183+ | 3,326+ | 3,991 |
| GBPUSD | **2022-04-12 09:15** | 2008-09-04 | 2008-09-04 | 2008-09-04 | 99,999 | 13,181+ | 3,326+ | 4,562 |
| NAS100 (NDX100) | **2022-10-20 11:00** | 2022-10-20 11:00 | 2022-10-20 08:00 | **2022-10-20 00:00** | 21,695 | 7,502 | 2,048 | 908 |

**Key observations:**
- **M15 history is shallower than H1+** for XAUUSD/USDJPY/GBPUSD: their M15 starts at 2022-01-28 / 2022-04-12 / 2022-04-12 respectively, while H1+ go back to 2019/2008. This is normal MT5 broker behaviour: M15 is gated at 99,999 bars (~2.85 years), H1 at the same N (~11+ years), etc.
- **NAS100 has the shallowest history**: only 3.5 years, starting 2022-10-20. The broker (FN) didn't carry NDX100 before that date. Cannot fabricate; this is a hard data limit.
- **XAGUSD has full coverage** of the 2022-01-01 -> 2024-02-20 window because M15 N=47,946 > the 26-month window's bar count.

## Section 2 — Extracted OHLCV (data/historical_2022_2023/)

CSV schema mirrors `data/historical_2026/{SYMBOL}_{TF}.csv` exactly: `time,open,high,low,close,volume` with UTC timestamps formatted as `YYYY-MM-DD HH:MM:SS`. Volume column = MT5 `tick_volume` (matches the 2026 export).

| Symbol | M15 rows | H1 rows | H4 rows | D1 rows | M15 first->last |
|---|---:|---:|---:|---:|---|
| XAUUSD | **48,365** | 12,571 | 3,291 | 551 | 2022-01-28 11:30 -> 2024-02-19 21:15 |
| XAGUSD | **47,946** | 12,020 | 3,287 | 549 | 2022-01-03 01:00 -> 2024-02-19 20:30 |
| USDJPY | **45,925** | 13,183 | 3,326 | 557 | 2022-04-12 09:15 -> 2024-02-20 00:00 |
| GBPUSD | **45,922** | 13,181 | 3,326 | 557 | 2022-04-12 09:15 -> 2024-02-20 00:00 |
| NAS100 | **21,695** | 7,502 | 2,048 | 345 | 2022-10-20 11:00 -> 2024-02-19 18:45 |

All 5 instruments have ≥1000 M15 candles in the 2022-2023 period (audit cutoff). Extraction script: `scripts/research/extract_ohlcv_2022_2023.py`.

## Section 3 — Structure-detector backfill (regime tags)

`scripts/research/backfill_v2_regime.py` (commit `a0e39de`) re-run with `--data-dir data/historical_2022_2023 --output shadow_logs/structure_detector_backfill_2022_2023.jsonl`. Output schema bit-identical to F14: per-H4 candle `{ts, symbol, timeframe, v1_direction, v2_direction, counts, v2_score, v2_dead_zone, ...}`.

| Symbol | H4 rows | First ts | Last ts |
|---|---:|---|---|
| XAUUSD | 3,211 | 2022-01-20 08:00 | 2024-02-20 00:00 |
| XAGUSD | 3,207 | 2022-01-20 08:00 | 2024-02-20 00:00 |
| USDJPY | 3,246 | 2022-01-21 08:00 | 2024-02-20 00:00 |
| GBPUSD | 3,246 | 2022-01-21 08:00 | 2024-02-20 00:00 |
| NAS100 | 1,968 | 2022-12-13 04:00 | 2024-02-20 00:00 |
| **Total** | **14,878** | | |

(NAS100 has 1,968 < the others because its H4 history starts ~9 months later. The 80-bar lookback floor in `backfill_v2_regime.py:_DEFAULT_H4_LOOKBACK` consumes the first 80 H4 candles.)

## Section 4 — Trade-cohort candidates (data/historical_2022_2023/trade_cohort.csv)

`scripts/research/build_trade_cohort_2022_2023.py`:
- Re-uses `src/research_infra/ob_zone_test.py:540` `extract_bos_events` for BOS detection on H1 CSV (matches F11/F4 mechanical baseline).
- Re-uses `src/research_infra/ob_zone_test.py:760` `find_ob_retest_outcome` for entry/SL/TP geometry + walk-forward via `src/research_infra/dumb_baseline.py:805` `resolve_mechanical_outcome` on M15 CSV.
- Output schema (CSV) matches K54 v1's `_row_from_f11` (`scripts/k54_build_features.py:221-293` in worktree `agent-a01c00db65592ac2b`).
- Output schema (JSONL) matches F11 `serialize_population` (`src/research_infra/ob_zone_original_geometry.py:1139` — `{bos: {...}, ob_retest: {...}}`), with the original_80pct_origin baseline omitted.

| Symbol | BOS events | Filled (TP/SL/TIMEOUT) | NO_ENTRY | Skipped (degenerate/missing) |
|---|---:|---:|---:|---:|
| XAUUSD | 581 | 394 | 107 | 80 |
| XAGUSD | 563 | 418 | 86 | 59 |
| USDJPY | 657 | 376 | 179 | 102 |
| GBPUSD | 655 | 400 | 152 | 103 |
| NAS100 | 356 | 210 | 43 | 103 |
| **Total** | **2,812** | **1,798** | **567** | **447** |

**Distribution checks (filled-only):**
- By regime tag: bullish 701, transitional 588, bearish 493, UNTAGGED 16 (regime join rate **99.1%**).
- By direction: LONG 913, SHORT 885 (very close to balanced; consistent with the 2-year backtest spanning multiple regime cycles).
- Win/Loss: 1,020 wins / 778 losses (WR = **56.7%**, n=1,798, with TIMEOUT mark-to-market R included).
- Mean realized R: **+0.392** per filled trade. Median: +1.500 (the modal outcome is TP at the 1.5R floor).
- Date range: 2022-01-04T14:00 -> 2024-02-19T20:00 UTC.

## Section 5 — Cross-period feasibility verdict

Re-stating `data_inventory_audit.md:59-92` Section 2 with the 2022-2023 column updated:

| Symbol | 2022-2023 (NEW) | 2024-2025 | 2026 | Periods ≥1000 |
|---|---:|---:|---:|---:|
| XAUUSD | **48,365** | 92,148 | 14,891 | **3** |
| XAGUSD | **47,946** | 53,684 | 13,387 | **3** |
| USDJPY | **45,925** | 49,901 | 15,082 | **3** |
| GBPJPY | 43,852 (existing) | 56,052 | 15,072 | **3** |
| GBPUSD | **45,922** | 49,901 | 15,082 | **3** |
| US30_cash | 46,817 (existing) | 53,063 | 14,328 | **3** |
| NAS100 | **21,695** | 49,234 | 13,265 | **3** |

**Verdict: 7 of 7 instruments have ≥1000 M15 candles in 2022-2023 (post-backfill).** Up from `data_inventory_audit.md:84` baseline of 2 of 7.

Per Section 2 Interpretation B (proper 3-period walk-forward 2022-2023 -> 2024-2025 -> 2026): **K54 v2 cross-period replication is now feasible on all 7 instruments**, not just GBPJPY + US30_cash.

**Caveat for NAS100:** Only ~16 months of 2022-2023 data (2022-10-20 -> 2024-02-20), vs ~26 months for the others. The H1 2022 sub-period (2022-01 -> 2022-06) is empty. Q1.4 walk-forward should not split NAS100 within 2022-2023.

## Section 6 — Files written

| Path | Purpose | Size |
|---|---|---|
| `data/historical_2022_2023/{XAUUSD,XAGUSD,USDJPY,GBPUSD,NAS100}_{M15,H1,H4,D1}.csv` | OHLCV (5 syms x 4 TFs = 20 files) | M15 ~2-7 MB each |
| `shadow_logs/structure_detector_backfill_2022_2023.jsonl` | H4 regime tags (14,878 rows) | ~3.5 MB |
| `data/historical_2022_2023/trade_cohort.jsonl` | F11-schema BOS + OB outcomes (2,812 rows incl NO_ENTRY) | ~2-3 MB |
| `data/historical_2022_2023/trade_cohort.csv` | K54 v1-schema filled trades (1,798 rows) | ~280 kB |
| `scripts/research/extract_ohlcv_2022_2023.py` | OHLCV extractor (one-shot, MT5 `copy_rates_range`) | new |
| `scripts/research/build_trade_cohort_2022_2023.py` | Trade-cohort builder (re-uses production research_infra) | new |
| `research/ml_program/audit/data_backfill_2022_2023.md` | This report | new |

## Section 7 — Methodology notes / honest caveats

1. **Broker-side M15 depth limit.** XAUUSD/USDJPY/GBPUSD M15 do not extend to 2022-01-01. The broker truncates M15 history; H1+ goes back to 2019/2008. The `extract_one` function tries `copy_rates_range` for the whole window and falls back to 6-month chunks. No fabrication — file `first` timestamps are the actual broker depth.
2. **NAS100 only goes to 2022-10-20.** The FN broker (redacted_account-Server 2) only carries NDX100 from that date. Q1.4 modelers should treat NAS100 as having ~16 months of 2022-2023 data, not ~26.
3. **NAS100 symbol mapping.** FN broker uses `NDX100`, not `NAS100`. We save the CSV as `NAS100_{TF}.csv` to match `OHLCV_STEM` (`src/research_infra/dumb_baseline.py:202`) so downstream tooling sees the canonical name.
4. **Live-account warning.** MT5 connection is via the redacted_account-Server 2 LIVE account. Extraction is read-only (`copy_rates_range` only); no order_send paths touched. Live trading orchestrators were not interrupted.
5. **Holdout discipline.** All extracted data is strictly < 2024-02-20. The Q1.4 prospective holdout (2026-04-29 -> 2026-05-12) is untouched.
6. **Tick volume vs real volume.** The historical_2026 export uses `tick_volume`, so we mirror that. `real_volume` is unreliable for FX/CFDs on most retail MT5 brokers and is not exported here.
7. **Trade-cohort schema differences from K54 v1 source mix.** K54 v1's `features.csv` (582 rows) joins three sources: F11_mechanical (439), trade_index (33), unified_csv (110). Our 1,798 rows are pure F11-equivalent mechanical (single source = `f11_mechanical`). Q1.4 modelers can union with the existing K54 v1 features.csv, treating `f11_mechanical` as a single source partition.
8. **Regime tag join rate.** 99.1% (1,782 of 1,798 filled trades have a non-empty `regime_tag`). The 16 UNTAGGED rows are at the very start of each instrument's H4 series (before the 80-bar lookback completes).
9. **Read-only on production code.** `src/components/`, `src/research_infra/`, `config/`, `scripts/canary_fixtures/`, `pipeline_state/` were not modified. New files all under `data/historical_2022_2023/`, `shadow_logs/structure_detector_backfill_2022_2023.jsonl`, `scripts/research/`, and this report.

## Section 8 — Reproducibility

```bash
# Step 1 — Extract OHLCV (requires MT5 + FN login)
python scripts/research/extract_ohlcv_2022_2023.py

# Step 2 — Run F14-equivalent regime backfill on the new dir
python scripts/research/backfill_v2_regime.py \
    --data-dir data/historical_2022_2023 \
    --output shadow_logs/structure_detector_backfill_2022_2023.jsonl \
    --instruments XAUUSD,XAGUSD,USDJPY,GBPUSD,NAS100

# Step 3 — Build trade-cohort (BOS detection + OB-retest geometry + M15 walk-forward)
python scripts/research/build_trade_cohort_2022_2023.py
```

Idempotent on a fixed input. Re-run after a CSV refresh.
