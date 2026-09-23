# SierraChart Symbol Catalog, Download, And SCID Probe - 2026-05-03

Status: research/tooling only  
Promotion posture: `NO_PROMOTION_VERDICT`  
Live-system impact: none  
AI/API cost: none

## Purpose

The owner clarified that the default Sierra files (`AAPL`, `EURUSD`, etc.) are not the real question. The real question is whether Service Package 12 gives GTOS a much larger symbol universe, and whether Codex can download/open a non-default instrument itself or needs Sierra UI/operator action.

## What Was Tested

1. Parsed Sierra's local symbol catalog:
   - `C:\SierraChart\SymbolSettings\SymbolSettings.scdataallservices.xml`
2. Checked whether non-default GTOS-relevant symbols already had local `.scid` or `.depth` files.
3. Checked whether the running SierraChart process exposes a local listening/DTC endpoint for programmatic chart/data requests.
4. Added and tested a research-only `.scid` parser/exporter:
   - `scripts/inspect_sierra_scid.py`
   - `tests/test_inspect_sierra_scid.py`
5. Exported one existing Sierra intraday slice from binary `.scid` to CSV to prove file-level utilization.

## Current Sierra Runtime State

SierraChart is installed and running:

- Install path: `C:\SierraChart`
- Data folder: `C:\SierraChart\Data`
- Process: `SierraChart_64.exe`
- Active external connections observed by `netstat`:
  - remote `0.0.0.0:10042`
  - remote `0.0.0.0:443`
  - remote `0.0.0.0:10043`
  - remote `0.0.0.0:10043`
  - remote `0.0.0.0:10043`

No local listening port was observed for the Sierra process. That means the current local instance does not expose a usable local DTC/API server from this session.

## Symbol Catalog Result

The local Sierra symbol catalog contains `1,820` settings entries.

Top categories:

| Count | Category |
|---:|---|
| 442 | NASDAQ TotalView delayed/realtime stocks |
| 221 | CBOE Global Indexes Additional realtime |
| 200 | Market Stats realtime |
| 113 | Futures - EUREX delayed/realtime |
| 105 | Futures - CME delayed/realtime |
| 95 | Futures - CBOT delayed/realtime |
| 87 | Futures - ICE US end-of-day |
| 41 | Forex - FXCM realtime |
| 38 | Futures - NYMEX delayed/realtime |
| 28 | CFD - FXCM realtime |
| 19 | US Equities consolidated tape delayed/realtime |
| 13 | Futures - COMEX delayed/realtime |
| 9 | US Equities consolidated tape with depth delayed/realtime |
| 6 | Binance realtime |
| 5 | Futures - CFE delayed/realtime |

Depth-capable entries by category total `877`:

| Count | Category |
|---:|---|
| 441 | NASDAQ TotalView delayed/realtime stocks |
| 112 | Futures - EUREX delayed/realtime |
| 105 | Futures - CME delayed/realtime |
| 95 | Futures - CBOT delayed/realtime |
| 46 | Futures - CBOT spreads |
| 38 | Futures - NYMEX delayed/realtime |
| 13 | Futures - COMEX delayed/realtime |
| 11 | BitMEX realtime |
| 8 | US Equities consolidated tape with depth delayed/realtime |
| 5 | Futures - CFE delayed/realtime |
| 2 | Deribit realtime |
| 1 | Bitfinex realtime |

Interpretation: Package 12 gives us a materially bigger research universe than the default files. The catalog includes the futures proxies GTOS cares about and many more depth-capable markets.

## GTOS-Relevant Symbol Patterns Present

Important delayed/realtime depth-capable patterns in the catalog:

| GTOS use | Sierra pattern | Description |
|---|---|---|
| NAS100 proxy | `NQ?##-CME` | E-mini Nasdaq 100 |
| NAS100 micro proxy | `MNQ?##-CME` | Micro E-mini Nasdaq 100 |
| SPX/equity-index control | `ES?##-CME` | E-mini S&P 500 |
| SPX micro control | `MES?##-CME` | Micro E-mini S&P 500 |
| US30 proxy | `YM?##-CBOT` | Mini Dow Industrials |
| US30 micro proxy | `MYM?##-CBOT` | Micro Dow |
| XAUUSD futures proxy | `GC?##-COMEX` | Gold |
| XAUUSD micro proxy | `MGC?##-COMEX` | E-micro Gold |
| XAGUSD futures proxy | `SI?##-COMEX` | Silver |
| XAGUSD smaller proxy | `SIL?##-COMEX` | Silver 1000 oz |
| GBPUSD proxy | `6B?##-CME` | British Pound |
| USDJPY inverse proxy | `6J?##-CME` | Japanese Yen |
| EURUSD proxy/control | `6E?##-CME` | Euro FX |
| AUDUSD proxy/control | `6A?##-CME` | Australian Dollar |
| USDCAD proxy/control | `6C?##-CME` | Canadian Dollar |
| USDCHF proxy/control | `6S?##-CME` | Swiss Franc |
| Oil macro/control | `CL?##-NYMEX` | WTI Crude Oil |
| Oil micro/control | `MCL?##-NYMEX` | Micro WTI Crude Oil |
| Rates/risk control | `ZN?##-CBOT` | 10-Year Treasury Note |
| Rates/risk control | `ZB?##-CBOT` | Treasury Bond |
| Small-cap index control | `RTY?##-CME` | E-mini Russell 2000 |
| Small-cap micro control | `M2K?##-CME` | Micro Russell 2000 |

## Non-Default Download Attempt Result

Checked for local files for non-default target contracts:

| Symbol checked | `.scid` exists | `.depth` exists |
|---|---:|---:|
| `GCM26-COMEX` | false | false |
| `MGCQ26-COMEX` | false | false |
| `6JM26-CME` | false | false |
| `6BM26-CME` | false | false |
| `ZNM26-CBOT` | false | false |
| `RTYM26-CME` | false | false |
| `M2KM26-CME` | false | false |
| `CLM26-NYMEX` | false | false |
| `MCLM26-NYMEX` | false | false |
| `SILN26-COMEX` | false | false |

I also checked whether Sierra exposes a local listening endpoint for programmatic data requests. It does not in the current configuration. The running Sierra process has outbound data-server connections, but no local listening/DTC port.

Conclusion:

- The symbol universe is available in Sierra's catalog.
- The agent can parse and export any `.scid` / `.depth` file once Sierra has created/downloaded it.
- With the current Sierra setup, Codex cannot force a new non-default symbol download purely through a local API because no local DTC/API server is enabled and Sierra's documented workflow opens symbols through `File >> Find Symbol`.
- To create the first `.scid` for a non-default symbol like `GCM26-COMEX` or `6JM26-CME`, Sierra currently needs a chart opened for that symbol through the UI or through a future DTC/automation bridge.

This is not a Package 12 limitation. It is an automation/control limitation of the current local setup.

## Direct SCID Utilization Proof

Added research-only parser/exporter:

```powershell
python scripts\inspect_sierra_scid.py `
  --data-dir C:\SierraChart\Data `
  --inventory-json data\sierrachart_exports\scid_inventory_2026-05-03.json `
  --export-file C:\SierraChart\Data\NQM26-CME.scid `
  --start 2026-04-15T13:00:00Z `
  --end 2026-04-15T14:00:00Z `
  --export-csv data\sierrachart_exports\NQM26-CME_2026-04-15_1300_1400_scid.csv
```

Export result:

| Field | Value |
|---|---:|
| Source | `C:\SierraChart\Data\NQM26-CME.scid` |
| Window | `2026-04-15 13:00:00` to `14:00:00 UTC` |
| Rows | `58,374` |
| First close | `25,990.0` |
| Last close | `26,068.5` |
| Min close | `25,979.0` |
| Max close | `26,072.25` |
| Sum total volume | `63,022` |
| Sum bid volume | `31,099` |
| Sum ask volume | `31,923` |

This proves the big Sierra `.scid` files are immediately usable by GTOS without manual CSV export. The `BidVolume` and `AskVolume` fields make Sierra useful for footprint/delta-style research even when market-depth files are not yet available.

## Current Local SCID Inventory Highlights

The existing local `.scid` files are not the full universe, but they are substantial:

| File | Records | First UTC | Last UTC |
|---|---:|---|---|
| `AAPL.scid` | `81,665,195` | `2025-10-28T14:33:36.122Z` | `2026-05-01T23:59:59.654Z` |
| `EURUSD.scid` | `25,225,959` | `2025-10-28T14:27:04.217Z` | `2026-05-01T20:58:59.320Z` |
| `MESM26-CME.scid` | `29,659,284` | `2025-10-28T14:29:35.469Z` | `2026-05-01T20:59:59.678Z` |
| `MNQM26-CME.scid` | `31,587,574` | `2025-10-28T14:54:37.713Z` | `2026-04-09T16:01:34.952Z` |
| `NQM26-CME.scid` | `16,876,942` | `2025-10-28T16:30:44.719Z` | `2026-05-01T20:59:59.073Z` |
| `XAUUSD.scid` | `9,463,561` | `2025-10-28T14:19:09.044Z` | `2026-05-01T20:44:58.881Z` |
| `YMM26-CBOT.scid` | `917,231` | `2025-10-30T14:03:53.366Z` | `2026-05-01T20:59:57.305Z` |
| `BTCUSDT_PERP_BINANCE.scid` | `16,141,345` | `2025-10-28T14:29:17Z` | `2026-05-03T04:08:21.521Z` |

## Depth File Reality

Current local market-depth files:

| File | Size |
|---|---:|
| `NQM26-CME.2026-05-01.depth` | `160` bytes |
| `NQM26-CME.2026-05-02.depth` | `16,792` bytes |

Those prove the `.depth` parser path, but they are not enough for market/orderflow research because the first capture was weekend/market-closed constrained. The $56 Package 12 value is best realized by deliberately opening target symbols and enabling market-depth recording during active sessions.

## How To Use Package 12 Best From Here

1. Build the symbol-opening queue from the catalog, not from defaults.
2. First wave:
   - `NQM26-CME` / `MNQM26-CME`
   - `GCM26-COMEX` / `MGC?##-COMEX` active contract
   - `YMM26-CBOT` / `MYM?##-CBOT` active contract
   - `6JM26-CME`
   - `6BM26-CME`
   - `SIM26-COMEX` or active silver contract
   - `CLM26-NYMEX` / `MCLM26-NYMEX`
3. For each symbol:
   - open an Intraday chart in Sierra,
   - let historical intraday data download,
   - enable `Record Market Depth Data` for the symbol pattern if depth is wanted,
   - keep the chart open through active sessions,
   - let Codex parse `.scid` and `.depth` files from disk.
4. Codex then exports slices, builds OHLC/footprint/depth features, and joins them to GTOS candidate clocks.

## Important Interpretation

Package 12 does not mean "every market has already been downloaded." It means we now have the entitlement/tooling to access a much larger universe and MBO/depth features. Sierra only creates local `.scid`/`.depth` files for symbols that are opened/recorded. Once those files exist, Codex can do the rest.

Current verdict:

- Symbol universe: strong and broad.
- File parsing: now proven for `.scid`; previously proven for `.depth`.
- Non-default code-only download: blocked by no local DTC/API endpoint and Sierra's UI-driven chart-open workflow.
- Best next step: open target charts in Sierra for the first-wave futures proxies, then let Codex batch parse/export/replay.
