# Sierra Chart Owner Setup SOP For GTOS

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Short Answer

Install the Sierra Chart desktop application locally and log in with the Sierra account that has Service Package 12 active.

GTOS does not need an API bridge first. The first validated path is file-based:

1. Sierra records market-depth data into `.depth` files.
2. Sierra provides intraday chart/trade data as `.scid` files or exported CSV.
3. GTOS reads those files from disk and builds a parser/parity report.

DTC/API/ACSIL bridges are later options only if `.depth` files are insufficient.

## Why File-Based First

The verified Sierra research path is:

1. `.depth` parser first.
2. ACSIL exporter second if `.depth` parsing is insufficient.
3. DTC/live bridge third only after local access is proven.

Reason:

- Sierra `.depth` files have an official documented binary format.
- Market-depth files are the evidence needed for parser/parity work.
- Sierra DTC has market-data message structures, but the DTC server path has restriction language and should not be the first dependency.
- This is a parser/parity proof, not a live trading integration.

## Install / Login

1. Install Sierra Chart on Windows.
2. Prefer the default install path if possible: `C:\SierraChart`.
3. Start Sierra Chart and log in with the Sierra account.
4. Confirm the active package is Service Package 12 / Integrated Advanced + MBO.
5. Do not connect Sierra to MT5 and do not activate Denali real-time exchange fees for this first proof.

## Delayed Feed Setup

Use Sierra's included Delayed Exchange Data Feed first.

Sierra official delayed-feed instructions say the delayed data is accessible when the current selected service is one of the supported services, including `SC Data`.

Inside Sierra:

1. Open `Global Settings >> Data/Trade Service Settings`.
2. Use `SC Data` for the delayed-feed proof.
3. If using `SC Data`, Sierra's delayed-feed page says to set `Allow Support for Sierra Chart Data Feeds` to `No` on the `Common Settings` tab to ensure delayed data is received.
4. Connect with `File >> Connect to Data Feed`.
5. If no streaming appears immediately, allow `10` to `15` minutes; Sierra notes this can happen when a delayed symbol has not recently been subscribed on the server.

For CME/CBOT/COMEX/NYMEX, delayed data is delayed by `10 minutes and 10 seconds`. This is acceptable for parser validation and not acceptable for live lead-time research.

## Depth And MBO Settings

Set maximum depth:

1. Open `Global Settings >> Sierra Chart Server Settings >> General`.
2. Set `Max Depth Levels` to `0`.
3. Reconnect to the data feed after changing it.

Set MBO subscription:

1. Open `Global Settings >> Sierra Chart Server Settings`.
2. Set `Subscribe Market by Order Data When Market Depth Subscribed` to `Yes`.
3. Set `Use Separate Connection for Market by Order Data` to `Yes`.
4. Reconnect with `File >> Connect to Data Feed`.

MBO caveat:

- Sierra Package 12 is required for MBO display.
- Sierra says only MBO orders with quantity `>=3` are transmitted/displayed.
- Sierra says MBO is not recorded or downloadable historically.
- The systematic parser target remains `.depth`, not historical MBO order IDs.

## First Symbol To Capture

Start with one symbol only:

- `NQ` or `MNQ`, active front contract from `File >> Find Symbol`.

Do not start with all symbols. The first objective is one clean parser proof.

After the first proof passes, use this first-wave set:

| GTOS symbol | Sierra/futures target |
|---|---|
| NAS100 | `NQ` or `MNQ` |
| XAUUSD | `GC` or `MGC` |
| XAGUSD | `SI` |
| US30 | `YM` or `MYM` |
| GBPUSD | `6B` |
| USDJPY | `6J` |

GBPJPY is not first-wave because it needs a synthetic `6B` / inverted `6J` proxy.

## Enable Market Depth Recording

For the active symbol:

1. Open `File >> Find Symbol`.
2. Select the active front contract for `NQ` or `MNQ`.
3. Open an Intraday chart.
4. Open the symbol settings area documented by Sierra for Market Depth Historical Graph.
5. Select the symbol or symbol pattern.
6. Set `Record Market Depth Data` to `Yes`.
7. Add `Market Depth Historical Graph` to the chart through `Analysis >> Studies`.
8. Confirm the heatmap/market-depth graph is nonblank while the market is active.

Market-depth files are stored under Sierra's data folder:

`[SierraChartInstall]\Data\MarketDepthData\`

Usually:

`C:\SierraChart\Data\MarketDepthData\`

## Capture Window

Preferred first capture:

- Symbol: `NQ` or `MNQ`
- Feed: delayed
- Duration: at least `30` minutes
- Session: active US futures session, preferably a period with visible depth changes
- Output: one `.depth` file plus one intraday `.scid` or exported intraday CSV

As of this SOP date, `2026-05-02` is a Saturday, so live futures depth may not stream until the next CME futures session opens. If the chart is blank on Saturday, that is an expected market-hours issue, not a Sierra failure.

## Files GTOS Needs

After capture, provide or place:

1. One `.depth` file from:
   - `C:\SierraChart\Data\MarketDepthData\`
2. One matching intraday `.scid` file from:
   - `C:\SierraChart\Data\`
3. Or one exported intraday CSV if `.scid` is inconvenient.
4. One short capture note with:
   - Sierra package,
   - feed used,
   - exact symbol,
   - local chart timezone if visible,
   - UTC start/end of capture if known,
   - whether Market Depth Historical Graph was nonblank,
   - whether MBO columns were visible.

Preferred repo intake folder:

`research/sierrachart_data_source_research_2026-05-02/samples/`

Suggested filenames:

- `NQ_YYYYMMDD_delayed.depth`
- `NQ_YYYYMMDD_intraday.scid`
- `NQ_YYYYMMDD_intraday.csv`
- `NQ_YYYYMMDD_capture_notes.md`

Do not overwrite previous samples. Add `_run1`, `_run2`, `_delayed`, or `_denali` as needed.

## What Codex Does Next

Once the sample exists, Codex should:

1. Read the `.depth` file header.
2. Verify magic `0x44444353` (`SCDD`), header size, record size, and version.
3. Convert Sierra UTC timestamps.
4. Replay the order book.
5. Produce top-N depth, imbalance, wall, near-touch add/delete, and number-of-orders features.
6. Compare against a Databento-overlapping window if available.
7. Write a parity report with `NO_PROMOTION_VERDICT`.

## Do Not Do Yet

- Do not activate Denali real-time market-depth exchange fees yet.
- Do not buy individual CME/CBOT/COMEX/NYMEX market-depth add-ons yet.
- Do not attempt live trading integration.
- Do not build DTC/API bridge first.
- Do not treat delayed data as a lead-time signal.

Denali real-time should only be considered after `.depth` parser/parity passes.
