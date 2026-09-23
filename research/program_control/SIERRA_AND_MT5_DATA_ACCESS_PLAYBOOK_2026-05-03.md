# Sierra And MT5 Data Access Playbook - 2026-05-03

Status: research/tooling only  
Promotion posture: `NO_PROMOTION_VERDICT`  
Live-system impact: none  
AI/API cost: none

## Purpose

Answer the operational data-access question for the expanded out-of-sample research program:

1. Can a fresh goal session get any data it needs from Sierra Chart, or does the owner need to open/download charts first?
2. Is MT5 limited to symbols already visible in Market Watch, or can the agent add broker symbols to Market Watch and export them?

## Bottom Line

MT5 is API-friendly. Sierra Chart is file/chart-driven unless we explicitly build and validate a bridge.

For MT5, the agent can discover broker symbols, select hidden symbols, and export OHLCV without the owner manually adding them to Market Watch.

For Sierra Chart, the agent can immediately use any local `.scid` and `.depth` files that already exist under `C:\SierraChart\Data`. For symbols that do not already have files, Sierra generally needs a chart opened so it downloads and maintains the local intraday data file. That chart-opening step is currently a Sierra UI/chartbook preparation step, not a proven agent API call.

## MT5 Probe Result

Probe date: `2026-05-03`

The agent selected a currently hidden tradable symbol and tested data access before and after `symbol_select`.

Symbol tested: `SGDJPY`

| Field | Result |
|---|---:|
| Total MT5 symbols visible to API | 76 |
| Hidden tradable symbols found | 43 |
| `SGDJPY` visible before probe | false |
| `SGDJPY` selected before probe | false |
| H1 rows before `symbol_select(True)` | 25 |
| `symbol_select(True)` result | true |
| H1 rows after `symbol_select(True)` | 25 |
| Restored to hidden after probe | true |

Interpretation:

- MT5 can return data for at least some broker-listed symbols even while they are hidden from Market Watch.
- `MetaTrader5.symbol_select(symbol, True)` can also add a hidden broker symbol to Market Watch programmatically.
- Therefore the fresh research session should not require manual Market Watch preparation for ordinary MT5 broker symbols.
- Manual action is only needed if the broker account/terminal itself lacks the symbol, the symbol alias is unknown, the terminal is disconnected, or the broker has no history for the requested range.

## Sierra Chart Probe Result

The current Sierra install has useful local data files and a large symbol catalog, but it does not currently expose a local programmatic chart/data endpoint.

Observed local state:

- Sierra install: `C:\SierraChart`
- Data folder: `C:\SierraChart\Data`
- Running process: `SierraChart_64.exe`
- Local `.scid` files currently include: `AAPL`, `AMZN-NQTV`, `BTCUSDT_PERP_BINANCE`, `EURUSD`, `MESM26-CME`, `MNQM26-CME`, `NQM26-CME`, `TICK-NYSE`, `XAUUSD`, `YMM26-CBOT`
- No local listening port was observed on DTC historical defaults `11098` or `11099`.

Existing proof of utilization:

- `scripts/inspect_sierra_scid.py` can parse Sierra `.scid` files directly.
- It exported `NQM26-CME` tick/intraday records for `2026-04-15 13:00-14:00 UTC`.
- That means once a Sierra `.scid` file exists locally, the agent can consume it without using Sierra's UI export function.

## Sierra Chart Limits Found

The cached Sierra documentation and current runtime checks point to these constraints:

1. Chart opening is the primary download trigger.
   - Sierra docs repeatedly route symbol access through `File >> Find Symbol` and `Open Intraday Chart`.
   - For expired futures, docs say the symbol may need to be manually typed into `Selected Symbol`.
   - For unlisted symbols, docs state the symbol can still be typed manually into `Selected Symbol`.

2. The DTC path is not currently usable as-is.
   - Current Sierra runtime has no observed local DTC listener on the expected ports.
   - Sierra's DTC server docs state market-data restrictions and explicitly reject real-time or historical data access through DTC for CME Group, EUREX, NASDAQ, CBOE, and US equities originating from UTP/CTA.
   - That makes DTC a poor first path for the futures markets GTOS most wants: CME, CBOT, COMEX, and NYMEX.

3. Service Package 12 is still valuable.
   - The value is not that it gives us a simple external Python download API.
   - The value is that it opens a large Sierra data universe and lets Sierra create high-resolution local data files when charts are opened.
   - Once those files exist, GTOS can parse them directly and reuse them across research sessions.

## What The Owner Needs To Do For Sierra

For a missing Sierra symbol, the reliable current process is:

1. In Sierra Chart, select `File >> Find Symbol`.
2. Choose the desired symbol if listed, or manually type the exact symbol into `Selected Symbol`.
3. Press `Open Intraday Chart`.
4. Let Sierra finish downloading.
5. Save a dedicated GTOS data chartbook once the target charts exist.
6. Keep Sierra open when collecting ongoing live/tick/depth data.

For historical futures, prefer continuous futures charts when the research needs long lookback behavior. For exact contract replay, open the exact contract month/year symbol.

For market depth, opening an intraday chart is not enough by itself. The chart/symbol must be configured to record market depth data, and the chart needs to be open while depth data is being collected. Existing local `.depth` evidence is currently tiny and not enough for broad L2 research.

## What The Agent Can Do For Sierra Now

Immediately:

- Inventory local Sierra `.scid` files.
- Parse existing `.scid` files to CSV or research-native dataframes.
- Slice by symbol/date/time.
- Validate coverage, gaps, first/last timestamps, and record counts.
- Use those files in expanded OOS replay research.

Not proven yet:

- Programmatically tell Sierra to open a new chart for a missing symbol.
- Programmatically request missing CME/CBOT/COMEX/NYMEX historical data through DTC.
- Programmatically cause Sierra to backfill market depth for a symbol that was never previously recorded.

Possible future bridge options:

| Bridge | What it could solve | Current assessment |
|---|---|---|
| Saved GTOS Sierra chartbook | Owner opens first-wave charts once; future sessions read growing `.scid` files | Best immediate path |
| DTC historical client | Could query supported historical data if server is enabled | Blocked/low priority for CME-family futures due documented restrictions |
| ACSIL exporter/study | Could export from open charts and access Sierra-specific structures | Useful later, still requires chartbook/open charts |
| UI automation | Could click through `Find Symbol` workflows | Fragile; not a robust research foundation |

## Fresh Goal Session Instructions

Use this order:

1. Start with MT5 for broad OHLCV expansion because it can be discovered and exported by code.
2. Use existing Sierra `.scid` files for high-resolution replay where available.
3. Ask the owner to open/save a Sierra GTOS data chartbook for the first-wave missing symbols.
4. After the chartbook exists, consume the generated `.scid` files directly with `scripts/inspect_sierra_scid.py`.
5. Treat Sierra market depth as a separate capture program, not as guaranteed historical data.

Suggested first Sierra chartbook wave:

| Research use | Sierra symbols/patterns |
|---|---|
| NAS100 proxy | `NQ?##-CME`, `MNQ?##-CME` |
| US30 proxy | `YM?##-CBOT`, `MYM?##-CBOT` |
| Gold proxy | `GC?##-COMEX`, `MGC?##-COMEX` |
| Silver proxy | `SI?##-COMEX`, `SIL?##-COMEX` |
| GBPUSD proxy | `6B?##-CME` |
| USDJPY proxy | `6J?##-CME` |
| EURUSD control | `6E?##-CME` |
| AUD/USD, CAD/USD, CHF/USD controls | `6A?##-CME`, `6C?##-CME`, `6S?##-CME` |
| Oil regime/control | `CL?##-NYMEX`, `MCL?##-NYMEX` |
| Rates regime/control | `ZN?##-CBOT`, `ZB?##-CBOT` |

## Decision

For the next research goal, do not wait on a perfect Sierra automation API. Use a two-lane plan:

1. MT5 lane: agent-led discovery/export for broad symbol/date OOS.
2. Sierra lane: owner opens/saves a GTOS data chartbook for selected high-value symbols, then agent parses the resulting `.scid` files.

This gets value from the paid Sierra package without pretending it behaves like the MT5 Python API.
