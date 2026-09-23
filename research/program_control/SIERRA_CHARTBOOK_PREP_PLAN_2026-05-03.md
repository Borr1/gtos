# Sierra Chartbook Prep Plan For Expanded OOS Goal - 2026-05-03

Status: research/data-prep plan  
Promotion posture: `NO_PROMOTION_VERDICT`  
Live-system impact: none  
AI/API cost: none

## Purpose

Define which Sierra Chart charts should be opened before dispatching the next fresh expanded-OOS research goal, and how the selection should be made.

The objective is not to hand-pick only the instruments we already expect to work. The objective is to prepare a broad but relevant Sierra data universe so the fresh goal session can autonomously rank, prune, and branch without being blocked by missing local `.scid` files.

## Decision

Use a staged Sierra chartbook, not an everything-download.

Sierra currently contains `1,820` symbol-setting entries and `877` depth-capable entries. Opening everything is technically noisy and methodologically bad:

- it increases download/storage/UI load,
- many symbols are irrelevant to GTOS,
- low-liquidity series create bad tick/orderflow measurements,
- every extra symbol increases multiple-testing burden,
- depth capture for too many symbols can become heavy without giving proportional value.

The right plan is a wide pre-registered universe:

1. Core GTOS futures proxies.
2. Strong controls for regime and cross-market awareness.
3. Optional aggressive expansion symbols if Sierra handles the first wave cleanly.

## Critical Clarification: Intraday Chart Versus Historical Chart

For this program, open **Intraday Charts**, not Sierra's **Historical Chart** button.

This is easy to misunderstand because Sierra uses the phrase "historical intraday data" for backfilled tick/intraday data. The button choice still matters:

| Sierra action | What it is for | Use for this plan? |
|---|---|---|
| `Open Intraday Chart` | Intraday/tick data, `.scid` files, Volume by Price, VWAP, footprint/Numbers Bars, trade-count bars, and active depth-dependent studies | Yes |
| `Open Historical Chart` | Historical daily-or-higher charting | No, not for the orderflow/heatmap research substrate |

So when opening `NQM26-CME`, `GCM26-COMEX`, `6JM26-CME`, and the rest, choose the concrete child contract and click `Open Intraday Chart`.

If more old intraday data is needed, use Sierra's historical-intraday download settings/procedures on an Intraday chart. Do not switch to Historical Chart unless the specific task is daily-bar context only.

## Zulz-Style Feature Mapping

The Zulz pack is not just "price charts." It uses several Sierra features. They come from different data layers:

| Zulz / orderflow feature | Sierra feature / substrate | Data requirement | Historical availability |
|---|---|---|---|
| VWAP + ETH/RTH deviations | VWAP studies on intraday data | `.scid` trades/bars | Backfilled intraday is enough |
| Volume Profile, LVN/HVN/POC | Volume by Price / Volume Profile | `.scid` volume-at-price or tick/trade volume | Backfilled intraday is enough if data quality is good |
| Footprint / Vol x Delta | Numbers Bars / bid-ask volume at price | tick/intraday bid/ask volume | Backfilled intraday may work; quality must be verified |
| 2000-trade bars | Intraday bar period set to Number of Trades | tick/trade records | Backfilled intraday may work; can also be rebuilt by parser |
| Large-trade bubbles | large-volume trade markers | trade size/volume | Backfilled intraday may work; thresholds unknown without Zulz template |
| Stacked imbalances | Numbers Bars calculations | bid/ask volume at price | Backfilled intraday may work; thresholds are parameterized |
| Heatmap / resting liquidity targets | Market Depth Historical Graph / depth files | `.depth` market-depth recording | Mostly forward/recent capture; not a long-horizon historical substitute |
| MBO / queue display | Market by Order columns | Sierra Package 12 + MBO subscription path | Not full historical; Sierra docs limit displayed MBO to quantity >= 3 and do not make it a long-horizon historical MBO archive |

Interpretation:

- The historical chartbook gets us most of the research substrate for VWAP, LVN, volume profile, footprint-style approximations, trade-count bars, and large-trade/imbalance research.
- The forward depth chartbook is what gets us heatmap/resting-liquidity behavior. This is primarily live/forward/recent-session data, not years of old heatmap history.
- The visual Zulz chart layout is a Sierra study/template problem. The raw research value comes from the data files; the exact Zulz look would require manually adding studies or buying/importing his chartbook templates.

## Zulz-Style Layout Versus Data Prep

The public Zulz product descriptions describe a **three-panel Sierra layout**, not one plain chart:

| Panel | Publicly described contents | GTOS prep implication |
|---|---|---|
| Left context | 5-minute and 15-minute charts, higher/lower-timeframe VWAP and deviations, higher-timeframe Volume Profile aligned right | Useful visual context; data comes from intraday `.scid` |
| Center execution | Auto ETH/RTH VWAP with deviations, each session's Volume Profile, Delta Profile by price, CVD, Liquidity Heatmap | Requires intraday `.scid`; heatmap requires `.depth` |
| Right footprint | Vol x Delta footprint, per-candle Volume Profile/POC, large-trade bubbles, stacked imbalances, total candle delta/volume | Requires accurate tick/bid-ask volume; exact thresholds are unknown without template |

The same pack says he can watch multiple contracts and then open the orderflow charts for the specific contract that reaches a setup. This argues against building a full heavy three-panel footprint/heatmap layout for 50+ instruments on day one.

Practical split:

- **For the fresh research goal:** open Intraday charts and depth-capture charts so Sierra creates parseable `.scid` and `.depth` files. The agent can compute VWAP, LVN/HVN/POC, CVD proxies, trade-count bars, and footprint-like bid/ask-volume features from files.
- **For human visual discretionary replication:** build Zulz-like layouts only for the core futures where it matters most: NQ/MNQ, ES/MES, GC/MGC, YM/MYM, CL/MCL, and maybe SI/SIL. This is optional for the research goal and should not block it.
- **For exact Zulz settings:** public sources identify the adjustable knobs but not their values: Large Volume Trade Threshold, Heatmap Thresholds, and Footprint Chart Tick Compression. Those are template/Discord parameters, not recoverable from Sierra itself.

Therefore the manual prep should not try to fully recreate the paid Zulz chartbook across every symbol before research starts. First capture the data. Add visual studies/layouts only where useful.

## How The Fresh Session Stays Autonomous

The fresh goal session should not need to choose from zero Sierra coverage.

It should start by inventorying whatever Sierra files exist after chartbook prep:

- `C:\SierraChart\Data\*.scid`
- `C:\SierraChart\Data\MarketDepthData\*.depth`

Then it should decide what to test using coverage/quality rules:

- timestamp span,
- row count,
- gap rate,
- bid/ask/volume availability,
- active-session overlap with GTOS kill zones,
- proxy relevance to live instruments,
- whether the evidence class is `FUTURES_PROXY_TRANSFER`, `CROSS_INSTRUMENT_TRANSFER`, `REGIME_TRANSFER`, or `DISCOVERY_ONLY`.

If the fresh session discovers a missing symbol after launch, it should not stall. It should either:

- fall back to MT5 OHLCV,
- fall back to Databento only if explicitly allowed/cost-capped,
- or write a follow-up Sierra open request.

## Two Chartbooks, Not One

Use two Sierra chartbook concepts.

| Chartbook | Purpose | Symbols | Depth? |
|---|---|---|---|
| `GTOS_HISTORICAL_RESEARCH` | Backfill and historical high-resolution research | broader continuous/active futures universe | no or optional |
| `GTOS_FORWARD_DEPTH_CAPTURE` | Ongoing active-session tick/depth capture | smaller front-month high-value universe | yes |

Reason:

- Historical replay needs breadth and old regimes.
- Depth/L2 capture needs quality, open charts, and forward recording. It is not free historical truth for every symbol.

For historical futures, prefer Sierra continuous futures charts where possible so older contracts are pulled cleanly. For forward depth, use exact active front-month contracts.

## Recommended First Wave

Open this before the expanded-OOS goal. This is the recommended balance: wide enough for autonomy, narrow enough to stay controlled.

### Already Local / Keep Updating If Useful

These already have local `.scid` files and should be kept if they are useful:

| Symbol | Use |
|---|---|
| `NQM26-CME` | NAS100 futures proxy |
| `MNQM26-CME` | NAS100 micro proxy |
| `MESM26-CME` | S&P micro control |
| `YMM26-CBOT` | US30 futures proxy |
| `EURUSD` | FX spot/control |
| `XAUUSD` | spot gold/control |
| `BTCUSDT_PERP_BINANCE` | crypto/regime control |
| `TICK-NYSE` | US market internals |
| `AAPL` | equity control |
| `AMZN-NQTV` | equity control |

### Core GTOS Proxy Charts

Open these in `GTOS_HISTORICAL_RESEARCH`. Exact active contract month can be adjusted by Sierra `Find Symbol`; record the exact symbol opened.

| GTOS need | Sierra symbol/pattern | Priority |
|---|---|---:|
| NAS100 | `NQ?##-CME`, `MNQ?##-CME` | P0 |
| US30 | `YM?##-CBOT`, `MYM?##-CBOT` | P0 |
| Gold | `GC?##-COMEX`, `MGC?##-COMEX` | P0 |
| Silver | `SI?##-COMEX`, `SIL?##-COMEX` | P0 |
| USDJPY inverse proxy | `6J?##-CME` | P0 |
| GBPUSD proxy | `6B?##-CME` | P0 |
| EURUSD control/proxy | `6E?##-CME`, plus spot `EURUSD` | P1 |
| S&P/equity-index control | `ES?##-CME`, `MES?##-CME` | P1 |
| Oil/risk regime | `CL?##-NYMEX`, `MCL?##-NYMEX` | P1 |
| Rates/liquidity regime | `ZN?##-CBOT`, `ZB?##-CBOT` | P1 |
| Russell/risk breadth | `RTY?##-CME`, `M2K?##-CME` | P1 |
| AUD/CAD/CHF controls | `6A?##-CME`, `6C?##-CME`, `6S?##-CME` | P2 |
| Volatility control | `VX?##-CFE`, `VXM?##-CFE` | P2 |

Expected size: about `25` to `35` charts depending on whether micro/full contracts are both opened.

## Forward Depth Capture Subset

For `GTOS_FORWARD_DEPTH_CAPTURE`, start smaller. Depth is most useful where it maps to live GTOS instruments and high-liquidity market state.

Recommended first depth set:

| Use | Symbol/pattern |
|---|---|
| NAS100 | `NQ?##-CME`, `MNQ?##-CME` |
| US30 | `YM?##-CBOT`, `MYM?##-CBOT` |
| Gold | `GC?##-COMEX`, `MGC?##-COMEX` |
| Silver | `SI?##-COMEX`, `SIL?##-COMEX` |
| USDJPY | `6J?##-CME` |
| GBPUSD | `6B?##-CME` |
| EURUSD control | `6E?##-CME` |
| S&P control | `ES?##-CME`, `MES?##-CME` |
| Oil regime | `CL?##-NYMEX` |
| Rates regime | `ZN?##-CBOT` |

Expected size: about `12` to `16` depth charts.

Do not start with depth recording for 60+ symbols. First prove Sierra records usable `.depth` files through one full active cycle for the core set.

## Aggressive Expansion Tier

If the first wave downloads cleanly and Sierra remains stable, add a second wave for breadth:

| Category | Examples |
|---|---|
| US breadth/stat internals | `ADV-NYSE`, `DECL-NYSE`, `ADV-NASDAQ`, `DECL-NASDAQ`, `ADV-NQ`, `DECL-NQ`, `NISS-NQ` |
| ETF controls | `SPY`, `QQQ`, `DIA`, `GLD`, `SLV` variants available in Sierra |
| Major equity controls | `NVDA`, `MSFT`, `AAPL`, `AMZN`, `META` variants available in Sierra |
| Europe/equity regime | `FDAX?##-EUREX`, `FDXM?##-EUREX`, `FESX?##-EUREX` if available |
| FX micro controls | `M6E?##-CME`, `M6A?##-CME` if available |

Expected additional size: `20` to `40` charts.

This tier is useful for regime and cross-market awareness, not direct promotion evidence.

## Owner Action Checklist

Before launching the next fresh goal session:

1. Open Sierra Chart.
2. Create or open a new chartbook named `GTOS_HISTORICAL_RESEARCH`.
3. For each first-wave pattern above, use `File >> Find Symbol`.
4. Select the active contract from Sierra's list, or manually type the exact symbol if needed.
5. Open an Intraday chart.
6. For futures history, use continuous futures chart settings where appropriate for longer lookbacks.
7. Save the chartbook.
8. Create or open `GTOS_FORWARD_DEPTH_CAPTURE`.
9. Open only the depth subset.
10. Enable depth recording for those symbol patterns if available.
11. Keep Sierra running through active sessions.
12. After download/recording starts, let the agent inventory `C:\SierraChart\Data`.

The owner does not need to manually export CSV files. Once Sierra creates `.scid` or `.depth` files, the agent can parse them directly.

## Fresh Goal Session Instruction

Add this to the expanded-OOS goal prompt:

> First inventory Sierra local files and compare them against `research/program_control/SIERRA_CHARTBOOK_PREP_PLAN_2026-05-03.md`. Use available Sierra files aggressively for futures-proxy and orderflow-aware research. Do not treat missing Sierra symbols as a blocker; fall back to MT5, cached Databento, or write a follow-up chart-open request. Keep every result evidence-classed and preserve `NO_PROMOTION_VERDICT`.

## Practical Recommendation

Prepare the recommended first wave before launch: `25` to `35` historical charts plus `12` to `16` forward depth charts.

That gives the fresh session real autonomy without opening hundreds of irrelevant instruments. If Sierra handles it cleanly, expand to `50` to `75` total charts in a second wave.
