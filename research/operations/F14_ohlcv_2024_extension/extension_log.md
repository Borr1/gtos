# F14 — OHLCV historical extension to 2024-03

**Status:** Shipped 2026-04-27.
**Branch:** `feat/research-f14-ohlcv-extension-2024-03` (off `feat/research-f6-ohlcv-extension-2025-10` at `72383af`).
**Owner:** Research / Phase 1 decay-diagnostic program.

## Goal

F6 extended `data/historical_2026/` OHLCV from 2026-01-02 → 2025-10-01 across the
10-instrument fleet × 4 timeframes. F6 noted: *"Extending OHLCV to 2024 is the natural
follow-up."* and called out **91 pre-2025-10 trades** (82.7% UNTAGGED in A3 stratification)
that the trade index `_trade_index.json` references but no OHLCV could resolve.

The pursuit-to-clarity question: *Is the MT5 broker history genuinely capped at ~6 months,
making those 91 trades a hard limit?* — empirical answer below.

## Methodology

Re-uses F6's `scripts/research/extract_ohlcv_history.py` (paranoid MT5 → CSV extractor,
idempotent on `(symbol, tf, timestamp)`, broker-symbol mapping verified live). No code
changes; F6's tests still pass (104/104).

### Extraction sequence (3 runs, idempotent appends)

| Run | Window (UTC) | Purpose | Cells | Bars fetched | Bars appended |
| --- | --- | --- | --- | --- | --- |
| 1 | 2024-03-01 → 2025-09-30 | Cover all trades in `_trade_index.json` (earliest 2024-03-01) | 40 | 502,953 | 502,953 |
| 2 | 2024-02-01 → 2024-03-01 | Warmup-window pad (80×H4 lookback for 2024-03-01 trade) | 40 | 25,979 | 25,951 |
| 3 | 2025-09-30 → 2025-10-02 | Patch a 1-day H4 gap at the F6/F14 window seam | 40 | ~1,212 | 1,212 |

**Total bars appended by F14: 530,116.** Total CSV rows now: 708,964.

### Run-3 forensic note (window seam gap)

F6's window started at `2025-10-01` (inclusive). F14's first run ended at `2025-09-30`
(exclusive of `2025-09-30`). Both are correct end-exclusive interpretations of MT5
`copy_rates_range`, but the seam left **only the 2025-09-30 00:00 UTC H4 bar** in
`XAUUSD_H4.csv` (and similar patterns on other instruments). The 04:00, 08:00, 12:00,
16:00, 20:00 UTC H4 boundaries on 2025-09-30 were missing. Direct MT5 probe confirmed
all 6 H4 bars exist on the broker side; the seam was a script-window artifact, not a
broker-history hole. Run 3 patches the gap.

For posterity: `extract_ohlcv_history.py` interprets `--end` as **exclusive**. Future
extensions should overlap by ≥1 candle at each window seam to avoid the same gap, or be
re-stitched after the fact.

## Per-instrument earliest broker timestamp (post-F14)

D1 + H4 data start cleanly at `2024-02-01`. F6 baseline was `2025-10-01`.

| Instrument | Earliest CSV ts (post-F14) | Earliest CSV ts (pre-F14 / F6) | New bars added (D1+H4 only) |
| --- | --- | --- | --- |
| XAUUSD | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,879 (D1+H4) |
| US30 (US30_cash) | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,876 |
| USDJPY | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,892 |
| GBPJPY | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,892 |
| XAGUSD | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,879 |
| NAS100 (US100.cash) | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,864 |
| GBPUSD | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,892 |
| EURUSD | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,892 |
| GER40 (GER40.cash) | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,820 |
| UK100 (UK100.cash) | 2024-02-01 00:00:00 | 2025-10-01 00:00:00 | +2,815 |

Per-CSV row counts (D1 / H4):

```
XAUUSD     D1=575    H4=3,449
US30_cash  D1=576    H4=3,439
USDJPY     D1=578    H4=3,468
GBPJPY     D1=578    H4=3,468
XAGUSD     D1=575    H4=3,449
NAS100     D1=576    H4=3,440
GBPUSD     D1=578    H4=3,468
EURUSD     D1=578    H4=3,468
GER40      D1=564    H4=3,384
UK100      D1=564    H4=3,376
```

## Hard data limit verdict

**The "MT5 broker history is genuinely capped at ~6 months" hypothesis is REFUTED.**

Empirical probes against the FTMO-Demo terminal (account 1513076540) on 2026-04-26:

| Symbol | Probe window | Result |
| --- | --- | --- |
| XAUUSD D1 | 2010-01 → 2010-06 | 106 bars, earliest **2010-01-04** |
| XAUUSD D1 | 2015-01 → 2015-06 | 107 bars, earliest 2015-01-02 |
| XAUUSD D1 | 2018-01 → 2018-06 | 108 bars, earliest 2018-01-02 |
| XAUUSD D1 | 2020-01 → 2020-06 | 107 bars, earliest 2020-01-02 |
| XAUUSD D1 | 2022-01 → 2022-06 | 107 bars, earliest 2022-01-03 |
| GBPUSD H4 | 2023-01 → 2024-03 | 1,813 bars, earliest 2023-01-02 |

The MetaQuotes FTMO-Demo terminal carries D1 history back to **at least 2010-01-04**
for XAUUSD; intraday H4 confirmed back to 2023-01-02 for GBPUSD. **F14's choice to
stop at 2024-02-01 is bounded by `_trade_index.json`** (earliest trade `2024-03-01`),
**not by broker history**.

If a future extension wants pre-2024 data (for backtest infrastructure that reaches
further back), the same script + a wider `--start` window will work without code change.

## Pre/post F14 comparison

| Metric | Before F14 (F6 baseline) | After F14 |
| --- | --- | --- |
| OHLCV start (CSV) | 2025-10-01 | **2024-02-01** |
| Backfill rows | 7,096 | **30,322** (+327%) |
| Backfill earliest tag | 2025-10-20 | **2024-02-20** |
| A3 UNTAGGED overall | 26.3% (108/411) | **0.0% (0/411)** |
| A3 UNTAGGED in 2026 window | 0.0% (0/284) | 0.0% (0/284) |
| A3 UNTAGGED pre-2025-10 trades | 82.7% (91/110) | **0.0% (0/110)** |
| Trade-index population (A3) | 411 | 411 (unchanged — index unmodified) |

## Pre-2024-03 trades — broker can supply, but trade index doesn't reach there

`_trade_index.json` earliest trade is `bt_2024-03-01_ny_001_gbpusd`. There are
**0 trades pre-2024-03** in the index. The broker has data back to ≥2010 (probed),
so any future trade-index extension would have OHLCV available without further data
work — **F14 has retired the data-depth limit for the project's full historical
backtest population**.

## Tests

`pytest tests/scripts/test_extract_ohlcv_history.py tests/research_infra/test_stratification.py -v`
→ **104 passed in 0.95s**. No code changes; only data extension.

## Logs

Raw stdout/stderr captured in:
- `raw_extraction.log` — Run 1
- `raw_extraction_warmup.log` — Run 2
- `raw_backfill.log` / `raw_backfill_extended.log` / `raw_backfill_final.log` — three v2 backfill iterations
- `raw_a3.log` — first A3 re-run (Run 1 only; UNTAGGED 0.5%)

Final A3 stats: `research/decay_diagnostic/A3_stratification/{strata.jsonl,change_points.json,report.md}`.

## Out of scope (per brief)

- No production-code edits.
- No Anthropic API calls (preflight 7/8 OK; step 8 ANTHROPIC skipped per CLAUDE.md task spec).
- No order placement on MT5 (read-only history extraction).
- No edits to `_trade_index.json` or `trades_unified.csv`.

## Forward links

- F6 baseline doc: `git show 72383af -- src/research_infra/docs/A3_stratification.md`.
- A3 outputs (post-F14): `research/decay_diagnostic/A3_stratification/`.
- Extraction script: `scripts/research/extract_ohlcv_history.py` (no changes from F6).
- Backfill script: `scripts/research/backfill_v2_regime.py` (no changes; consumes wider CSVs automatically).
