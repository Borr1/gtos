# Phase 3 Lower-Timeframe Data Rescue Audit

**Created UTC:** 2026-05-01
**Scope:** Resolve whether the Phase 3 M1/M5/tick label constraint is an exporter problem, a terminal setting problem, or a broker/source problem.
**Status:** Research/tooling only. No live trading logic, prompt, or config behavior changed. Updated after the MT5 max-bars rescue completed.

## Bottom Line

The M1/M5 bar-data constraint is resolved for the current redacted_account terminal after setting MT5 Charts max bars to Unlimited and restarting/refreshing the terminal state. No broker switch is currently needed for the historical M1/M5 truth layer.

Post-change verification:

```text
terminal_info.maxbars = 100000000
terminal path = C:\Program Files\MetaTrader 5
server = redacted_account-Server 2
login = 0
```

The original blocker was the terminal setting: before the change, `terminal_info.maxbars = 100000`, matching the observed ~100k-row cap in the first Phase 3 lower-timeframe export. Smaller export chunks did not solve it while `maxbars` remained 100000.

The remaining constraint is historical tick depth. Recent tick windows are available, but broad 2025/January 2026 tick backfill is not available from the current terminal state. Tick-level same-bar ordering remains a forward-only or alternate-source research problem.

## Evidence

### Existing Chunked Export

Existing export:

```text
data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1/manifest.json
```

It requested:

```text
start = 2022-01-01T00:00:00Z
end = 2026-05-01T00:00:00Z
chunk_days = 30
timeframes = M1,M5,H1,D1
errors = []
```

Observed lower-timeframe first available rows:

| Symbol | M1 first | M5 first |
| --- | --- | --- |
| XAUUSD | 2026-01-19 11:59 | 2024-11-29 06:40 |
| XAGUSD | 2026-01-19 11:39 | 2024-11-29 03:20 |
| GBPJPY | 2026-01-23 08:54 | 2024-12-26 11:25 |
| USDJPY | 2026-01-23 08:58 | 2024-12-26 17:30 |
| GBPUSD | 2026-01-23 09:15 | 2024-12-26 16:50 |
| NAS100 | 2026-01-20 05:27 | 2024-11-28 06:30 |
| US30_cash | 2026-01-20 02:01 | 2024-11-28 06:10 |

### Smaller-Chunk Rescue Test

Command run against current redacted_account terminal:

```powershell
python scripts/export_mt5_research_ohlcv.py `
  --start 2022-01-01 --end 2026-05-01 `
  --timeframes M1,M5 `
  --symbol XAUUSD:XAUUSD `
  --chunk-days 1 `
  --label phase3_rescue_xau_m1_m5_chunk1_20220501 `
  --yes-live-readonly
```

Result:

| Timeframe | chunks_requested | raw_rows_returned | rows | first | last |
| --- | ---: | ---: | ---: | --- | --- |
| M1 | 1581 | 101217 | 99738 | 2026-01-19 12:29 | 2026-04-30 23:59 |
| M5 | 1581 | 101010 | 99947 | 2024-11-29 07:10 | 2026-04-30 23:55 |

Interpretation: one-day chunks do not move history backward. The limiting factor is not the exporter chunk size. It is the terminal/server history substrate, with terminal `maxbars=100000` as the first fixable constraint.

### Post-Maxbars Rescue Export

After the CEO set MT5 Charts max bars to Unlimited, the terminal reported:

```text
terminal_info.maxbars = 100000000
```

One-symbol XAUUSD retest:

```powershell
python scripts/export_mt5_research_ohlcv.py `
  --start 2022-01-01 --end 2026-05-01 `
  --timeframes M1,M5 `
  --symbol XAUUSD:XAUUSD `
  --chunk-days 1 `
  --label phase3_rescue_xau_m1_m5_chunk1_after_maxbars `
  --yes-live-readonly
```

Result:

| Timeframe | rows | first | last |
| --- | ---: | --- | --- |
| XAUUSD M1 | 1528838 | 2022-01-03 01:00 | 2026-04-30 23:59 |
| XAUUSD M5 | 305941 | 2022-01-03 01:00 | 2026-04-30 23:55 |

All-symbol export:

```text
data/mt5_research_exports/phase3_rescue_all_m1_m5_chunk1_after_maxbars/manifest.json
errors = []
```

| Symbol | M1 first | M1 rows | M5 first | M5 rows |
| --- | --- | ---: | --- | ---: |
| GBPJPY | 2022-01-03 00:00 | 1602547 | 2022-01-03 00:00 | 320888 |
| GBPUSD | 2022-01-03 00:00 | 1601117 | 2022-01-03 00:00 | 321006 |
| USDJPY | 2022-01-03 00:00 | 1601161 | 2022-01-03 00:00 | 321024 |
| XAUUSD | 2022-01-03 01:00 | 1528838 | 2022-01-03 01:00 | 305941 |
| XAGUSD | 2022-01-03 01:00 | 1485307 | 2022-01-03 01:00 | 297511 |
| NAS100 | 2022-10-20 11:00 | 1052457 | 2022-10-20 11:00 | 212964 |
| US30_cash | 2022-10-20 11:00 | 1051102 | 2022-10-20 11:00 | 212948 |

Interpretation: the terminal max-bars setting was the fixable M1/M5 blocker. Metals and FX now cover the full requested 2022-2026 research window from the first trading session in January 2022. NAS100 and US30_cash start at 2022-10-20 from this broker's available index history, so pre-2022-10 index intraday truth remains unavailable from redacted_account.

### Rescued Truth-Layer Rerun

The first full rescued truth-layer rerun exposed a research-script performance issue: with full M1 history available, the resolver path repeatedly copied full multi-year M1/M5 series and timed out at 30 minutes. The research-only truth-layer script was updated to slice the legal lower-timeframe horizon before calling the shared mechanical resolver.

Successful rerun:

```text
report = research/phase_3_external_feed_validation/HISTORICAL_OPPORTUNITY_TRUTH_LAYER_V2_RESCUED_2026-05-01.md
summary = data/external/validation/calendar_macro_bundle_v1/historical_opportunities/truth_layer/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_summary_20260501T061655Z.json
output_jsonl = data/external/validation/calendar_macro_bundle_v1/historical_opportunities/truth_layer/phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl
rows = 205197
unique_keys = 205197
ai_call_count_sum = 0
```

Lower-timeframe coverage improved materially:

| Timeframe | attempted | local coverage | local coverage rate | selected truth rows | horizon complete |
| --- | ---: | ---: | ---: | ---: | ---: |
| M1 | 73950 | 73387 | 99.24% | 30421 | 11836 |
| M5 | 73950 | 73401 | 99.26% | 10098 | 25349 |

The lower `horizon_complete` count is expected because a 96-M15-bar hold window maps to 1440 M1 bars or 288 M5 bars, and many intraday windows cross weekends/market breaks. Local coverage, not full 24-hour contiguity, is the key blocker that the max-bars rescue fixed.

### Tick-History Probe

New script:

```text
scripts/inspect_mt5_tick_availability.py
```

Command run:

```powershell
python scripts/inspect_mt5_tick_availability.py `
  --label phase3_tick_history_probe_20260501 `
  --write-json `
  --yes-live-readonly
```

Artifact:

```text
data/mt5_research_exports/tick_availability/phase3_tick_history_probe_20260501_20260501T053133Z.json
```

Tick availability summary:

| Window | XAUUSD | XAGUSD | GBPJPY | USDJPY | GBPUSD | NAS100 | US30_cash |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-04-30 13:00-14:00 UTC | 31597 | 9632 | 33218 | 25236 | 17549 | 40833 | 11069 |
| 2026-04-27 13:00-14:00 UTC | 14680 | 6494 | 8446 | 3250 | 5882 | 14564 | 2637 |
| 2026-01-20 13:00-14:00 UTC | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2025-12-01 13:00-14:00 UTC | 0 | 0 | 0 | 4879 | 0 | 0 | 0 |

Interpretation: historical tick data is available for recent days, but not broadly for January 2026 or December 2025 from the current terminal state. Tick backfill is therefore a separate source-retention problem, not solved by the current forward tick capture.

### Post-Maxbars Tick Constraint Confirmation

After `terminal_info.maxbars` increased to `100000000`, the tick probe was rerun to verify whether the chart-history fix also changed tick-history availability:

```powershell
python scripts/inspect_mt5_tick_availability.py `
  --label phase3_tick_history_probe_post_maxbars_20260501 `
  --write-json `
  --yes-live-readonly
```

Artifact:

```text
data/mt5_research_exports/tick_availability/phase3_tick_history_probe_post_maxbars_20260501_20260501T062554Z.json
```

Post-maxbars tick availability summary:

| Window | XAUUSD | XAGUSD | GBPJPY | USDJPY | GBPUSD | NAS100 | US30_cash |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-04-30 13:00-14:00 UTC | 31597 | 9632 | 33218 | 25236 | 17549 | 40833 | 11069 |
| 2026-04-27 13:00-14:00 UTC | 14680 | 6494 | 8446 | 3250 | 5882 | 14564 | 2637 |
| 2026-01-20 13:00-14:00 UTC | 0 | 0 | 0 | 5410 | 0 | 0 | 0 |
| 2025-12-01 13:00-14:00 UTC | 0 | 0 | 0 | 4879 | 0 | 0 | 0 |

Interpretation: raising MT5 max bars fixed historical M1/M5 bar depth but did not broadly backfill historical tick depth. The current redacted_account terminal exposes recent ticks for all symbols and isolated older USDJPY tick windows, but not broad historical tick coverage across metals, crosses, or indices. Save this as a research constraint: historical tick ordering is not a blocker for M1/M5 truth-layer work, but it remains unresolved for tick-level same-bar sequencing until an alternate tick source or forward-captured live tick sample is available.

## CEO Action Completed

The safe terminal-setting fix on the current redacted_account terminal worked. Do not switch the live redacted_account terminal to another broker for the M1/M5 bar-data truth layer.

1. In MT5, open:

```text
Tools -> Options -> Charts
```

2. Set both values as high as MT5 allows:

```text
Max bars in history
Max bars in chart
```

Recommended target if MT5 accepts it:

```text
999999999
```

If MT5 clamps it, use the highest accepted value.

3. Restart MT5.

4. Tell Codex when the terminal is back up. Then rerun:

```powershell
@'
import MetaTrader5 as mt5
if not mt5.initialize():
    raise SystemExit(mt5.last_error())
try:
    print(mt5.terminal_info().maxbars)
finally:
    mt5.shutdown()
'@ | python -
```

The target condition is:

```text
terminal_info.maxbars >> 100000
```

Observed condition:

```text
terminal_info.maxbars = 100000000
```

## Post-Change Commands Run

First re-test one symbol, because this cheaply tells us if the setting solved the cap:

```powershell
python scripts/export_mt5_research_ohlcv.py `
  --start 2022-01-01 --end 2026-05-01 `
  --timeframes M1,M5 `
  --symbol XAUUSD:XAUUSD `
  --chunk-days 1 `
  --label phase3_rescue_xau_m1_m5_chunk1_after_maxbars `
  --yes-live-readonly
```

Pass condition:

```text
XAUUSD_M1 first moves materially earlier than 2026-01-19
XAUUSD_M5 first moves materially earlier than 2024-11-29
rows materially exceed ~100k per timeframe
```

This passed. Then all symbols were exported:

```powershell
python scripts/export_mt5_research_ohlcv.py `
  --start 2022-01-01 --end 2026-05-01 `
  --timeframes M1,M5 `
  --chunk-days 1 `
  --label phase3_rescue_all_m1_m5_chunk1_after_maxbars `
  --yes-live-readonly
```

Then the rescued truth layer was rerun:

```powershell
python scripts/build_historical_opportunity_truth_layer.py `
  --data-dir data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1 `
  --data-dir data/mt5_research_exports/phase3_rescue_all_m1_m5_chunk1_after_maxbars `
  --write --quiet
```

The command completed successfully after the research script was optimized to avoid full-series lower-timeframe resolver copies.

## If Current redacted_account Still Caps History

This contingency did not trigger for M1/M5 bars. Keep it only as the path for deeper historical tick data or for pre-2022-10 NAS100/US30 intraday index history.

Next path:

1. Keep the live redacted_account terminal running for trading.
2. Install or use a separate MT5 terminal for a demo/free broker with deeper history.
3. Do not log the live redacted_account terminal out during live operation.
4. Use the exporter with `--terminal-path` pointing at the alternate terminal:

```powershell
python scripts/export_mt5_research_ohlcv.py `
  --terminal-path "C:\Path\To\Alternate MT5\terminal64.exe" `
  --start 2022-01-01 --end 2026-05-01 `
  --timeframes M1,M5 `
  --chunk-days 1 `
  --label phase3_altbroker_m1_m5_chunk1 `
  --yes-live-readonly
```

Required broker evaluation criteria:

- M1 history starts near 2022-01-01 for FX/metals if possible.
- M5 history starts near 2022-01-01.
- NAS100/US30 symbol mapping is explicit and stable.
- OHLC price scale is compatible or can be normalized.
- Tick data has more than a few days/weeks of retention if same-bar ordering is the target.
- Bid/ask/spread availability is preserved for execution-quality studies.

## Research Implication

The v2 truth taxonomy is now usable as the historical M1/M5 label-quality substrate for the requested Phase 3 diagnostics. Parameter optimization should still respect the remaining boundaries:

- M1/M5 truth is substantially rescued and can support controlled research sweeps.
- Historical tick truth is not broadly rescued and should remain forward-only or alternate-source research.
- NAS100/US30_cash have redacted_account intraday history from 2022-10-20 onward, not from 2022-01-01.
- Any parameter sweep still needs DSR/PBO accounting and should use high-confidence/lower-timeframe-resolved cohorts or explicitly sensitivity-test low-confidence rows.

This avoids reaching a later optimization stage only to discover that the label substrate was avoidably weak.
