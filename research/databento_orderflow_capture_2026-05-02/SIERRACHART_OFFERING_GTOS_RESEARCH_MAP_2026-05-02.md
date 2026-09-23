# Sierra Chart Offering Map For GTOS Orderflow Research

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Source Scope

Official Sierra Chart pages crawled from the site navigation and documentation table of contents:

- Home page
- Description of Service Packages and Pricing
- Supported Data and Trading Services
- Futures data inclusion page
- Delayed Exchange Data Feed
- Sierra Chart Historical Data Service
- Denali Exchange Data Feed
- Market By Order Data
- Market Depth Historical Graph
- Market Depth Data File Format
- ACSIL Historical Market Depth Data
- DTC Protocol / market-depth messages
- Numbers Bars
- Volume By Price
- Intraday export and historical intraday data pages

## Executive Read

Sierra Chart is valuable for GTOS, but not in the simplistic way "it gives unlimited historical MBO back to 2007."

The useful split is:

1. Historical tick/intraday/volume/footprint research: strong.
2. Historical market-depth level files: useful, but limited to recent server retention and local recording.
3. Live/forward depth capture: strong.
4. Market by Order display/queue analysis: useful live/visual functionality, but not currently a historical MBO download/recording replacement.
5. Long historical MBO backfill: still Databento, not Sierra, based on the official docs crawled.

## Packages

Current official monthly package prices found:

| Package | Price | GTOS relevance |
|---|---:|---|
| Service Package 3 Base Standard | `$26/mo` | Not enough for our orderflow/depth research. |
| Service Package 5 Base Advanced | `$36/mo` | Advanced studies, but no Denali support. |
| Service Package 10 Integrated Standard | `$36/mo` | Denali/external connectivity, but lacks advanced studies and MBO. |
| Service Package 11 Integrated Advanced | `$46/mo` | Good for Denali + advanced studies + Market Depth Historical Graph. |
| Service Package 12 Integrated Advanced + MBO | `$56/mo` | Best GTOS research package if we want MBO/queue display plus advanced studies. |

Multi-month Package 12 discounts found:

- 3 months: `$142.80`, equivalent `$47.60/mo`
- 6 months: `$252.00`, equivalent `$42.00/mo`
- 12 months: `$436.80`, equivalent `$36.40/mo`

GTOS package interpretation:

- If we only need depth levels, Numbers Bars, Volume by Price, and Denali integration: Package 11 is probably enough.
- If we want Market by Order display/queue features: Package 12 is required.
- Since the whole question is orderflow/full-depth/MBO validation, Package 12 is the clean research package.

## Data Feeds

### Delayed Exchange Data Feed

Useful for cost-free research and setup validation:

- Included with Sierra Chart packages.
- CME/CBOT/COMEX/NYMEX delay: 10 minutes and 10 seconds.
- EUREX/CFE/equities delay: 15 minutes.
- Includes market depth and Market by Order where supported, but NASDAQ TotalView delayed excludes market depth.
- No exchange fees and no funded futures account requirement.

GTOS use:

- Good first setup lane.
- Good for testing Sierra Chart export, depth-file parsing, chart replay, Numbers Bars, VBP, and market-depth visualization without paying exchange fees.
- Not useful for live decision impact. Research only.

### Denali Exchange Data Feed

Useful for real-time forward capture:

- Real-time and historical data for CME, CBOT, NYMEX, COMEX, EUREX, CFE, NASDAQ TotalView, US equities, and CBOE indexes.
- Up to `1400` market-depth levels per side.
- Up to `2000` concurrently streaming symbols.
- Tick-by-tick, unfiltered, full market-depth feed direct from exchanges.
- CME Group market-depth data needs an exchange option that includes market depth.

GTOS use:

- Best feed for real-time/forward Sierra Chart capture.
- For our proxies:
  - `NQ` and `ES`: CME
  - `YM`: CBOT
  - `GC` and `SI`: COMEX
  - possible `CL`: NYMEX if later used

### Denali Exchange Fees

Relevant nonprofessional monthly fees found:

| Exchange option | Price | Market depth |
|---|---:|---|
| Full CME Group with Market Depth | `$40.50/mo` | yes |
| Full CME Group without Market Depth | `$6.00/mo` | no |
| CME with Market Depth | `$13.50/mo` | yes |
| CBOT with Market Depth | `$13.50/mo` | yes |
| COMEX with Market Depth | `$13.50/mo` | yes |
| NYMEX with Market Depth | `$13.50/mo` | yes |

For GTOS, the Full CME Group with Market Depth is the cleanest if we want `NQ/ES/YM/GC/SI` together. It costs the same as CME+CBOT+COMEX individually and adds NYMEX coverage.

Important constraint:

- Lower-cost nonprofessional CME Group exchange fees require a verified live funded futures trading account with a supported trading service.
- Evaluator/prop-style accounts may not qualify under CME rules.
- Without that qualification, professional/no-supported-account fees are much higher.

## Historical Data

Official historical-data page says:

- CME/NYMEX/COMEX/CBOT tick-by-tick futures data begins at `2011`.
- Before that, CME/NYMEX/COMEX/CBOT data is 1-minute units and begins at `June 2008`.
- Historical daily commodity futures can go much further back, but that is not orderflow/depth.

Important note:

- I did not validate a "back to 2007" claim from the official pages crawled here. The pages I found say June 2008 for pre-tick 1-minute CME-group intraday and 2011 for tick-by-tick.

GTOS use:

- Sierra historical tick/intraday data can help with long-horizon footprint-ish bid/ask volume and volume-profile studies.
- It does not solve long historical market-depth/MBO backfill.

## Market Depth Historical Graph / Depth Files

Sierra Chart can record and load market-depth history:

- Market Depth Historical Graph requires an Advanced package.
- Must enable `Record Market Depth Data` for the symbol.
- Depth files are stored in `Data/MarketDepthData`.
- File naming is `[symbol].[UTC date].depth`.
- The file covers UTC `00:00:00` to `23:59:59`.
- The depth file format is documented.
- Records include command, UTC timestamp, number of orders at the price level, price, and total quantity.
- Full snapshots are written every 10 minutes.

Retention ambiguity:

- One section says historical market depth can be downloaded for the previous 15 days with Denali.
- Another section says market-depth data is maintained on Sierra servers for a maximum of 180 days, and CME Group depth is maintained for 180 days.
- Treat this as an operational ambiguity to verify inside Sierra or with support before relying on historical depth availability.

GTOS use:

- Very useful for forward/recent top-of-book/full-depth-level research.
- Good replacement for our MBP-10-style depth-state features.
- Not equivalent to Databento historical MBO order-identity reconstruction.

## Market By Order

Official MBO page says:

- MBO is available from Denali and Delayed Exchange Data Feed for CME, CBOT, NYMEX, COMEX, EUREX, NASDAQ TotalView, and CFE, except NASDAQ TotalView delayed does not provide MBO.
- MBO shows the specific limit orders that make up market depth at each price and their queue position.
- Access is limited to Service Package 12.
- Currently only MBO orders with quantity greater than or equal to `3` are transmitted/displayed in the DOM MBO columns.
- There is no support for recording MBO data or downloading historical MBO data.

GTOS implication:

- Sierra MBO is not a historical Databento MBO replacement.
- Sierra MBO can support live/forward visual or DOM queue research.
- For systematic feature extraction, the documented `.depth` files are level-depth files, not order-identity MBO files.
- If we need historical order-ID add/cancel/modify/fill reconstruction, Databento remains the right source.

## Footprint, Volume, And Profile Features

Useful Sierra Chart features:

- Numbers Bars: bid/ask volume footprint, delta-style views, POC/highlight logic.
- Volume By Price: volume profiles, POC/value-area style research, session/range-defined profiles.
- Market Depth Historical Graph: heatmap-style depth visualization and level-state data.
- Chart Replay: can replay historical charts and market depth when depth data is available.

GTOS use:

- These map cleanly to the Zulz/orderflow research vocabulary:
  - footprint,
  - LVN/HVN/POC,
  - absorption proxies,
  - heatmap/resting liquidity,
  - liquidity pull/add at price levels,
  - replay around GTOS candidate windows.

## Programmatic Access / Export

Available paths:

1. Intraday export:
   - Intraday data can be exported to text/CSV.
   - Export timestamps are UTC/GMT.

2. Market depth files:
   - `.depth` binary format is documented.
   - It includes add/modify/delete level commands, quantity, price, number of orders, and UTC timestamps.
   - This is the best GTOS path for automated depth feature extraction.

3. ACSIL:
   - `c_ACSILDepthBars` exposes historical market-depth bars loaded into a chart.
   - Studies must set `sc.MaintainHistoricalMarketDepthData = TRUE`.

4. DTC:
   - DTC provides market-depth request/snapshot/update messages.
   - DTC market-depth messages include side, price, quantity, level, timestamp, and number of orders.
   - The market-data message page did not show MBO/order-ID message support in the sections crawled.

GTOS implementation preference:

- First parser target: Sierra `.depth` files.
- Second target: ACSIL exporter if `.depth` parsing is inconvenient.
- Third target: DTC for live streaming if we decide to build a running bridge.

## What GTOS Actually Needs

Minimum research setup:

- Sierra Chart Package 12 for MBO + advanced studies.
- Start with Delayed Exchange Data Feed.
- Enable depth recording for `NQ`, then `GC`, `SI`, `YM`, `ES` as needed.
- Build `.depth` parser and parity check against Databento MBP/MBO features.

Real-time forward setup:

- Package 12.
- Denali real-time exchange data.
- Full CME Group with Market Depth if nonprofessional/funded-account rules are satisfied.
- If no qualifying funded futures account exists, use delayed feed first and avoid professional fees unless there is a clear operational reason.

Not needed now:

- Teton order routing.
- Live trading integration.
- Any Sierra-generated signal wired into GTOS live decisions.

## Recommended GTOS Plan

1. Do not buy anything until we confirm whether delayed Package 12 access can produce the needed `.depth` files and MBO DOM views.
2. Build a Sierra `.depth` parser spec against the documented file format.
3. Ask the owner to provide one small Sierra `MarketDepthData` export/file for `NQ` around a known Databento NAS100 candidate date.
4. Compare Sierra depth features to the Databento MBO/MBP feature contract:
   - top-20 total depth,
   - imbalance,
   - wall concentration,
   - near-touch add/remove,
   - NumOrders at price level,
   - snapshots around candidate time.
5. If parity is good, use Sierra delayed/real-time capture for forward NAS100 research.
6. Expand to `GC/SI/YM/ES` only after NAS100 parser parity is proven.

## Open Questions

1. Does Package 12 delayed feed expose enough MBO/depth functionality without exchange fees for our export/parity work?
2. Which exact Sierra files are available locally after enabling Record Market Depth Data for delayed data?
3. Can Sierra expose live MBO order identities programmatically, or only visually in DOM columns?
4. Which funded futures account route, if any, is available to qualify for nonprofessional Denali CME-group real-time exchange fees?
5. Does the server retention for CME depth behave as 15 days or 180 days in practice?

## Current Verdict

Sierra Chart is worth using for GTOS, but the first validated use should be:

`Sierra depth-level forward capture and visual replay parity`, not `historical MBO replacement`.

Keep Databento for historical MBO reconstruction. Use Sierra for forward/recent depth capture, footprint/profile tooling, and potentially cheaper ongoing NAS100 full-depth research once parser parity is verified.
