# Sierra Chart And Primitive Data Source Synthesis For GTOS

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Primary evidence index: `research/sierrachart_data_source_research_2026-05-02/SOURCE_INDEX_2026-05-02.md`

## Executive Verdict

Sierra Chart is useful for GTOS, and specifically useful for the "real orderflow / heat / full-depth" path. It is not just another basic OHLC feed.

The correct interpretation is:

- Sierra Chart + Denali/delayed feed is a strong platform for forward and recent depth-level capture, heatmap replay, footprint, volume profile, and discretionary/visual orderflow study.
- Sierra Chart is not a long-horizon historical MBO replacement because its own MBO page says there is no support for recording MBO or downloading historical MBO.
- Databento remains the better validated source for targeted historical MBO/MBP event windows because it exposes programmatic MBO/MBP schemas and we already ran GTOS feature extraction on it.
- The truly primitive source is the exchange feed itself, but direct CME website fetches were blocked, and direct exchange feeds are normally institutional/licensed infrastructure. For GTOS, the practical primitive-ish routes are Databento for historical/programmatic exchange data and Sierra/Denali for ongoing platform capture.
- For forex/CFD symbols, Sierra's own Forex/CFD feed is not true exchange orderflow: it has no market depth, no centralized true volume, and volume is indicative quote-change volume. Futures proxies remain the serious orderflow route for FX-like GTOS symbols.

## What Sierra Chart Offers That Matters

### Packages

Official package prices fetched from Sierra:

| Package | Price | GTOS read |
|---|---:|---|
| Service Package 3 Base Standard | `$26/mo` | Not enough for full GTOS orderflow research. |
| Service Package 5 Base Advanced | `$36/mo` | Advanced studies, but base packages do not support Denali. |
| Service Package 10 Integrated Standard | `$36/mo` | Integrated/external/Denali support, but not advanced studies or MBO. |
| Service Package 11 Integrated Advanced | `$46/mo` | Depth studies, Numbers Bars, Volume by Price, Denali, external services. |
| Service Package 12 Integrated Advanced + MBO | `$56/mo` | Required if we want Sierra's MBO DOM/queue functionality. |

Package 12 is the clean research package because the ambiguity we are trying to close includes MBO/queue behavior, not just bars.

### Delayed Exchange Data Feed

Sierra's delayed feed is not a toy for this research lane:

- CME, CBOT, COMEX, NYMEX are delayed by `10 minutes and 10 seconds`.
- EUREX, CFE, US equities are delayed by `15 minutes`.
- It includes market depth and MBO where supported.
- It has no exchange fees and no funded futures account requirement.
- Sierra says market-depth dependent features, including Market Depth Historical Graph, work with delayed data.

GTOS implication:

- This is the first low-cost validation lane.
- It cannot be used for live decision lead-time.
- It can validate parsing, export, depth-file behavior, heatmap replay, and feature parity against Databento without burning real-time exchange fees.

### Denali Exchange Data Feed

Denali is the Sierra route that matters for real-time forward capture:

- Sierra describes it as tick-by-tick and unfiltered.
- Sierra states full market-depth data is direct from exchanges.
- Sierra states up to `1400` market-depth levels per side.
- Sierra states up to `2000` symbols can stream concurrently.
- Sierra states Direct CME FIX data feed integration at its backend.
- CME Group market depth requires an exchange option that includes market depth.

For our current futures proxy universe, the clean Denali exchange bundle is CME Group with market depth:

| GTOS instrument | Futures proxy | Exchange family |
|---|---|---|
| NAS100 | `NQ` / `MNQ` | CME |
| US30 | `YM` / `MYM` | CBOT |
| XAUUSD | `GC` / `MGC` | COMEX |
| XAGUSD | `SI` / silver micro if available | COMEX |
| GBPUSD | `6B` | CME |
| USDJPY | `6J`, inverted vs spot USDJPY | CME |
| GBPJPY | no clean single proxy | synthetic `6B` and inverted `6J` / cross proxy only |

### Exchange Fees / Account Constraint

Verified Sierra nonprofessional monthly fees from the Denali page:

| Exchange option | Price | Market depth |
|---|---:|---|
| Full CME Group with Market Depth | `$40.50/mo` | yes |
| Full CME Group without Market Depth | `$6.00/mo` | no |
| CME with Market Depth | `$13.50/mo` | yes |
| CBOT with Market Depth | `$13.50/mo` | yes |
| COMEX with Market Depth | `$13.50/mo` | yes |
| NYMEX with Market Depth | `$13.50/mo` | yes |

Important verified constraint:

- Lower-cost CME Group nonprofessional real-time fees require a verified live funded futures trading account with a supported trading service.
- Sierra states evaluator/funding-evaluator accounts do not count.
- Sierra states without qualifying account/support, professional/no-supported-account exchange fees are much higher.

This means the recommended order is:

1. Use delayed feed first.
2. Only activate Denali real-time market-depth fees after we prove that Sierra depth files provide the exact feature contract we need.
3. Before real-time fees, verify whether the owner has a supported live funded futures account that satisfies CME's nonprofessional requirement.

## What Sierra Does Not Solve

### Historical Futures MBO

The Sierra MBO page is explicit enough for GTOS:

- MBO requires Service Package 12.
- MBO shows specific orders and queue position in DOM columns.
- Only orders with quantity `>=3` are currently transmitted/displayed.
- Sierra says there is no support for recording MBO data or downloading historical MBO data.

Therefore:

- Sierra MBO is not a historical order-ID reconstruction source.
- Sierra `.depth` files are depth-level files, not MBO order-identity files.
- Databento stays relevant for historical MBO.

### Long Historical Depth

Sierra historical OHLC/tick history is strong, but historical market depth is a different category.

Verified Sierra historical data:

- CME/NYMEX/COMEX/CBOT futures tick-by-tick intraday begins at `2011`.
- Before that, CME-group futures intraday is 1-minute data beginning `June 2008`.
- Sierra Forex/CFD intraday data is available back to `December 2007`, but that is not futures depth/orderflow.
- Sierra Market Depth Historical Graph page says market-depth data is maintained on Sierra servers for a maximum of `180` days, with CME Group depth maintained for `180` days.

The owner's "back to 2007" point is partly true but category-specific:

- `December 2007` applies to Sierra's Forex/CFD intraday service.
- `June 2008` applies to pre-tick CME-group futures intraday.
- `2011` applies to CME-group futures tick-by-tick.
- None of those dates mean historical MBO or historical full-depth back to 2007.

## Programmatic Extraction Paths

### Sierra `.depth` Files

This is the primary GTOS parser target.

Verified format facts:

- Files live in Sierra's `Data/MarketDepthData` folder.
- File extension is `.depth`.
- Filename format is `[symbol].[UTC date].depth`.
- Each file covers UTC `00:00:00` through `23:59:59`.
- Header size is `64` bytes.
- Header magic is `0x44444353` (`SCDD`).
- Record size is `24` bytes.
- Records include `DateTime`, `Command`, `Flags`, `NumOrders`, `Price`, `Quantity`, and reserved padding.
- `DateTime` is UTC and represented as microseconds since Sierra's `SCDateTime` epoch of `1899-12-30`.
- Commands include clear book, add bid/ask, modify bid/ask, delete bid/ask.
- Full market-depth snapshots are written every `10` minutes and can be identified by `COMMAND_CLEAR_BOOK`, followed by add records, with the final record flagged `FLAG_END_OF_BATCH`.

GTOS feature compatibility:

- Top-N total depth: yes.
- Bid/ask imbalance: yes.
- Wall concentration: yes.
- Near-touch add/remove: yes.
- Number of orders at level: yes.
- Heatmap/replay state: yes.
- Individual order IDs / queue order lifecycle: no.

### Intraday / Footprint Exports

Sierra intraday export supports UTC text/CSV with:

- Date,
- Time,
- Open,
- High,
- Low,
- Last,
- Volume,
- NumberOfTrades,
- BidVolume,
- AskVolume.

Numbers Bars and Volume by Price require tick-by-tick data for highest accuracy. Numbers Bars do not require market-depth data; they require bid/ask/trade classification. This matters because footprint and heatmap are separate datasets:

- Footprint/delta = trade aggressor / bid-ask volume path.
- Heatmap/resting liquidity = market-depth path.

We should keep those as separate feature families.

### DTC / ACSIL

Sierra DTC pages document market-depth message structures with side, price, quantity, timestamp, level, and number of orders, and also document websocket support. However, the DTC Server page includes restriction language saying to read market-data restrictions and says market data is not accessible through the DTC Protocol Server.

Therefore DTC is not the first GTOS extraction path until proven locally. The order should be:

1. `.depth` parser.
2. ACSIL exporter if `.depth` parsing is insufficient.
3. DTC bridge only after a local Sierra instance proves the market-data path is accessible for our symbols and package.

## Primitive Source Comparison

### Exchange Direct

The true primitive source for CME/CBOT/COMEX/NYMEX products is the exchange feed itself. Automated fetches to CME's public site returned a 403 block, and this synthesis does not rely on blocked CME pages for detailed claims.

Practical read:

- Direct exchange feeds are the cleanest conceptual source.
- They usually require licensing, professional market data agreements, infrastructure, and operational work.
- They are not the right first step unless Sierra/Databento both fail to give us the needed evidence.

### Databento

Verified current role:

- Databento offers real-time and historical market data APIs and states it sources data directly from colocation sites.
- Saved Databento docs bundle exposes `GLBX.MDP3`, `MBO`, `MBP-10`, historical `timeseries.get_range`, and live subscribe examples.
- The docs classify MBO as L3/full order book and MBP-10 as L2/market depth.
- Our existing GTOS Databento work already extracted trades, MBP-10, and MBO features around candidate windows.

GTOS read:

- Databento is still the best source for targeted historical MBO/MBP validation.
- It is not the cheapest route for indefinite all-symbol full-depth capture.
- With the remaining free usage, use it surgically to validate Sierra parity and close historical ambiguity, not as an always-on feed.

### IQFeed

Official IQFeed page evidence:

- Real-time true tick-by-tick for US/Canadian equities.
- Market depth / Nasdaq Level II available for additional fee.
- `180` calendar days of tick history with microsecond timestamps where available.
- 1-minute history for US stocks/futures/indexes back to `May 2007`.
- Daily/weekly/monthly OHLCVOI can go much further back, including US futures as far back as 1959.

GTOS read:

- IQFeed is useful for broad historical bars and recent tick history.
- It is not shown in the fetched evidence as a better full-depth futures/MBO source than Sierra/Databento.
- Keep as a fallback for non-depth historical coverage, not the primary orderflow source.

### CQG

Official CQG page evidence:

- CQG connects to over `85` global market data sources, `45` tradable exchanges, and `139` broker environments.
- CQG offers broad multi-asset market data, routing, analytics, and FX sources including EBS and CQG Global FX.

Sierra-specific constraint:

- Sierra's CQG page says CME Group and EUREX market data in Sierra are only provided through Denali, not CQG.

GTOS read:

- CQG may be useful institutionally, especially for broad market access and FX/energy/metals ecosystems.
- Inside Sierra, CQG is not the cleaner route for CME-group depth than Denali.
- It is not the next practical GTOS step.

### dxFeed / Bookmap / Rithmic

Fetch results:

- dxFeed page returned an anti-bot redirect / blocked path.
- Bookmap attempted URL returned 404.
- Rithmic attempted URL returned a 404 page.

No claims are made from those failed pages. They remain open if the owner wants to provide specific URLs or account docs later.

## Instrument-Specific Implications

### NAS100

Use `NQ`/`MNQ`. This is the cleanest first full-depth Sierra target because we already have Databento NAS100 MBO/MBP diagnostics and a registered NAS100 depth-adverse-selection hypothesis.

### US30

Use `YM`/`MYM`, with `ES` as an optional broad equity-index control. US30 has sparse candidate count in the current orderflow set, so Sierra forward capture matters more than more retrospective over-analysis.

### Gold / XAUUSD

Use COMEX `GC`/`MGC` for real orderflow. Sierra's CFD gold feed is not enough because Sierra says its CFD service has no market depth and no true centralized volume. Futures depth is the serious data.

### Silver / XAGUSD

Use COMEX `SI` or the relevant micro silver contract if supported. Same logic as gold.

### GBPUSD

Use CME `6B` as the futures proxy for orderflow. Sierra Forex/CFD data can give bid/ask quote history, but not true market depth or centralized volume. Proxy validation remains required.

### USDJPY

Use CME `6J`, inverted relative to spot USDJPY. The inversion/proxy ambiguity remains active and must be validated with candidate-window alignment.

### GBPJPY

No clean single futures proxy. Use synthetic reasoning from GBPUSD/6B and USDJPY/6J only as diagnostic context. This should not be treated as a strict activation map without a separate validation file.

## Recommended GTOS Plan

### Step 1: Sierra Delayed Capture Proof

Use Sierra Package 12 if available, start with delayed data, and enable market-depth recording for:

1. `NQ` / `MNQ`
2. `GC` / `MGC`
3. `SI`
4. `YM` / `MYM`
5. `6B`
6. `6J`
7. optional `ES` as equity-index control

Required proof files:

- at least one `.depth` file per symbol family,
- at least one intraday `.scid` or exported CSV per symbol family,
- screenshots or logs confirming Market Depth Historical Graph and MBO columns load for Package 12 delayed data.

### Step 2: Parser And Parity

Build and validate a Sierra `.depth` parser against the documented structure.

Parity checks against Databento:

- top-10/top-20 total depth,
- top-10/top-20 imbalance,
- wall concentration,
- near-touch add/remove intensity,
- number of orders at level,
- snapshot reconstruction around candidate time.

Acceptance for parser parity:

- parse succeeds on real Sierra `.depth` files,
- UTC conversion matches Sierra chart timestamps,
- reconstructed book is monotonic by side and price,
- no negative quantities,
- clear-book/snapshot batches replay cleanly,
- parity report says `NO_PROMOTION_VERDICT`.

### Step 3: Databento Usage After Sierra Proof

Use remaining Databento credits only to answer concrete parity or ambiguity questions:

- If Sierra depth parser disagrees with Databento MBP-10, pull the exact same event window from Databento.
- If MBO vs depth-level features diverge, pull MBO only around the candidate windows that need order-identity evidence.
- Do not spend on dead time. Fetch event windows around GTOS candidate clocks, pre-fill delivery path, and immediate post-fill failure/success path.

### Step 4: Forward Capture

Once parser parity is proven:

- run Sierra delayed capture continuously during active futures sessions for research,
- store `.depth` and intraday exports by symbol/date,
- build a daily feature extractor into research artifacts,
- append features to the existing orderflow candidate ledger,
- keep the live system untouched.

### Step 5: Real-Time Denali Decision

Only after Sierra delayed proof:

- If owner has a supported live funded futures account, consider Package 12 + Denali + Full CME Group with Market Depth.
- If no qualifying account exists, continue delayed research first.
- If real-time is needed for lead-time studies, document the exact monthly cost and account eligibility before activation.

## Ambiguities Still Open

1. Whether Package 12 delayed data exposes MBO DOM columns exactly as needed for our practical workflow.
2. Whether delayed mode writes `.depth` files identically enough for parser validation.
3. Whether DTC market data is practically accessible in our local Sierra setup despite the restriction language.
4. Whether the owner has a qualifying supported live funded futures account for CME nonprofessional Denali fees.
5. Whether Sierra's `180` day market-depth retention is available for every symbol we care about, every contract month, and delayed-vs-real-time mode.
6. Whether `6J` inversion remains stable enough for USDJPY GTOS candidate windows across sessions/regimes.
7. Whether GBPJPY can be represented by any useful orderflow proxy or must remain non-orderflow until a better source is found.

## Current Decision

Sierra Chart is worth using, but as:

`Sierra depth-level forward/recent capture + visual orderflow replay + footprint/profile tooling`

not as:

`unlimited historical MBO backfill`.

The correct next build is a Sierra `.depth` parser plus a real-file parity report against Databento. No promotion, no live integration, no live trading change.
