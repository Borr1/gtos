# Primitive Orderflow Source Synthesis For GTOS

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Primary evidence index: `research/primitive_orderflow_sources_2026-05-02/SOURCE_INDEX_2026-05-02.md`

## Executive Answer

We are not logically locked into Sierra Chart and Databento.

But after checking more primitive routes, the practical current answer is:

- For GTOS futures proxies, the true primitive source is CME Group exchange market data, especially Globex futures depth/orderflow for `NQ/MNQ`, `YM/MYM`, `GC/MGC`, `SI`, `6B`, and `6J`.
- The best practical programmatic route to that source remains Databento `GLBX.MDP3` for historical/API research because we already proved trades, MBP-10, and MBO extraction in our own pipeline.
- The best practical visual/forward-capture route remains Sierra Chart Package 12 plus delayed-feed validation first, then Denali if parser/parity proves useful.
- Direct exchange feeds are theoretically best for latency and purity, but not automatically cheaper or easier. They add licensing, entitlement, network, feed-handler, storage, and maintenance burden.
- For spot FX, there is no single primitive consolidated order book. The closest "primitive" sources are institutional CLOB or ECN venues such as LMAX, LSEG FX Matching/FXall, CME EBS, Integral, or similar venues. These are venue-specific truth, not whole-market truth.
- LMAX is the strongest non-CME source found in this pass because it explicitly offers Level 2, Level 3, and ITCH full-order-book data from its own central limit order books. Follow-up fee evidence shows it is a real institutional venue source, not a cheap shortcut: LMAX Exchange ITCH is `$80,000/mo` for `LD4`, or `$25,000/mo` only after very large volume conditions; standard FIX 10-level combined FX/metals depth is `$15,000/mo` before connection fees.
- Nasdaq TotalView/ITCH is primitive for Nasdaq equities, but it is not the primitive source for NAS100/NQ futures. It may become useful only if we research the Nasdaq-100 equity basket/constituent lead-lag layer.

So the decision is not "Sierra + Databento forever." The better framing is:

1. **CME futures orderflow lane:** Databento for historical/API + Sierra for forward visual/depth capture.
2. **FX venue lane:** investigate LMAX/LSEG/EBS only if we want venue-specific spot FX CLOB orderflow beyond futures proxies.
3. **Direct exchange lane:** defer until the system needs institutional latency and can justify feed-handler/licensing overhead.

## What "Primitive" Means Here

Primitive means where the book is formed or first distributed:

- exchange-native feeds,
- venue CLOB feeds,
- order-by-order or market-by-order data where available,
- market-by-price depth where order IDs are not available,
- timestamps and transport close enough to the source to test lead/lag against MT5 broker ticks.

Primitive does not mean:

- old daily/1-minute history,
- retail broker quotes,
- generic chart feeds,
- vendor claims without export/API access,
- data that cannot be time-aligned to our MT5 broker stream.

## Instrument Mapping

| GTOS instrument | Best primitive-ish source now | Why |
|---|---|---|
| NAS100 | CME `NQ/MNQ` via Databento/Sierra/Denali | NQ futures are the centralized, liquid listed proxy. Nasdaq TotalView is for equities, not NQ futures. |
| US30 | CBOT `YM/MYM` via Databento/Sierra/Denali | YM futures are the centralized listed proxy for Dow exposure. |
| XAUUSD | COMEX `GC/MGC` via Databento/Sierra/Denali | Spot gold is OTC/fragmented; COMEX futures are the clean centralized depth proxy. |
| XAGUSD | COMEX `SI` via Databento/Sierra/Denali | Spot silver is fragmented; COMEX futures are the clean centralized depth proxy. |
| GBPUSD | CME `6B` plus optional venue-specific LMAX/LSEG FX | Futures proxy is centralized; spot FX venues are useful but not universal. |
| USDJPY | CME `6J` inverted plus optional venue-specific LMAX/LSEG FX | Futures proxy is centralized; spot FX venues are useful but not universal. |
| GBPJPY | synthetic `6B` and inverted `6J`; optional venue-specific spot FX | No clean single futures proxy. Cross construction and validation are mandatory. |

## Source Ranking

| Rank | Source route | Primitive quality | Historical/API | Forward/visual | Friction | GTOS read |
|---:|---|---|---|---|---|---|
| 1 | Direct CME Group market data / MDP 3.0 | Highest for CME futures | Likely possible only with direct licensing/vendor workflows | Highest latency potential if engineered correctly | Very high | The pure source, but not the right first implementation path. |
| 2 | Databento `GLBX.MDP3` | Near-primitive normalized CME data from colocation | Strong and already working in GTOS for trades, MBP-10, MBO | Live API possible, visual tooling absent | Low/medium | Best programmatic research route now. |
| 3 | Sierra Chart Denali / delayed + `.depth` | Direct exchange feed through Sierra; depth-level capture | Recent/local depth capture, no historical MBO recording/download | Strong platform, heatmap, footprint, replay | Low/medium | Best visual and forward-capture route now. |
| 4 | LMAX Exchange / LMAX Global market data | Venue-native FX/metals/index CLOB-style data | Claims historical intraday/T+1 and Level 2/3/ITCH, depending on lane | Strong if access granted | High to very high, professional/institutional | Serious FX venue candidate, but Exchange ITCH/full-depth economics are not GTOS-budget practical. |
| 5 | Rithmic | DMA/execution plus real-time/delayed/historical data | Unclear historical depth/MBO API from public page | Strong if using futures broker stack | Medium/high | Worth revisiting if we open futures broker/execution path. |
| 6 | dxFeed futures | Exchange-sourced vendor route | Real-time/delayed/historical replay/download claimed | API route, no GTOS proof yet | Medium | Useful backup vendor; did not beat Databento/Sierra on current evidence. |
| 7 | CQG | Broad multi-asset vendor/broker ecosystem | Broad but less specific from public page | Platform/API route | Medium/high | Useful institutional vendor, not a sharper current research route. |
| 8 | Nasdaq TotalView/ITCH | Primitive for Nasdaq equities | Equity order-book/tick-history lane | Good for equity basket research | Medium | Not primary for NQ/NAS100 futures. |
| 9 | IQFeed | Good broad retail/pro data | Strong OHLC/tick history claims, Nasdaq Level II add-on | Platform/API feed | Low/medium | Not enough for full CME MBO/depth research. |

## What This Means For "Before MT5 Broker Finds Out"

The idea is valid, but it must be measured, not assumed.

For CFDs/MT5 symbols, broker quotes are derived from one or more liquidity sources. CME futures orderflow can lead broker CFD quotes in some situations, but that lead is not guaranteed for every symbol/session/regime. To make it real, we need a lead/lag validation protocol:

1. Capture broker MT5 ticks with UTC timestamps and broker-clock skew correction.
2. Capture the primitive/proxy feed simultaneously: Databento live, Sierra Denali `.depth`, or Sierra delayed for parser-only tests.
3. Align by symbol proxy:
   - `NQ/MNQ` vs NAS100,
   - `YM/MYM` vs US30,
   - `GC/MGC` vs XAUUSD,
   - `SI` vs XAGUSD,
   - `6B` vs GBPUSD,
   - inverted `6J` vs USDJPY,
   - synthetic `6B/6J` vs GBPJPY.
4. Measure signed return lead/lag, spread-adjusted direction, depth shocks, wall pulls/adds, and MT5 response delay.
5. Report by symbol/session/regime; do not generalize one source to every instrument.

This is where Sierra/Databento can add direct system value even before any live signal:

- market awareness,
- broker quote lag diagnostics,
- CFD-vs-futures proxy validation,
- orderflow event tagging,
- better post-trade forensics,
- selective event-window capture.

## Direct Exchange Feeds Are Not Automatically Better For Us

Direct exchange is the purest data source, but the engineering burden matters:

- exchange agreements and professional/nonprofessional classification,
- entitlement and redistribution constraints,
- multicast/network connectivity or vendor gateway,
- feed-handler implementation,
- packet loss/recovery handling,
- symbol/security definitions,
- binary protocol parsing,
- storage/replay format,
- monitoring and clock sync,
- historical replay procurement.

For a retail/proprietary research system, a normalized source can be "more correct for us" than direct raw multicast if it gives verifiable historical access, clean schemas, and reproducible extraction now.

Databento and Sierra are not primitive in the philosophical sense, but they are close enough to the source and materially more usable for current GTOS research.

## Better-Than-Sierra/Databento Candidates

### LMAX

LMAX is the only newly inspected source that deserves active follow-up.

Evidence found:

- venue CLOB language,
- firm limit order liquidity,
- Level 2 aggregated depth,
- Level 3 disaggregated order-book entries,
- ITCH full-depth binary protocol,
- real-time via FIX, Java/.NET, REST API,
- historical intraday/T+1 delivery,
- data centers/venues in `LD4`, `NY4`, `TY3`, and `SG1`.

Potential use:

- FX-specific orderflow research where futures proxies are insufficient,
- GBPUSD/USDJPY direct venue comparison,
- possibly metals/index CFD venue data if contract coverage and fees make sense.

Blocker:

- fee schedule now materially argues against LMAX Exchange as the immediate GTOS source. The user-supplied LMAX Exchange PDF, effective `01 JUNE 2026`, states `LD4` ITCH access costs `$80,000/mo`, reducible to `$25,000/mo` only if total global volumes exceed `$25bn` and a minimum aggressive/passive ratio of `30%` is reached. Standard FIX 10-level combined FX/metals depth is `$15,000/mo`, and non-eligible FIX feeds are throttled to `10` updates/sec.
- LMAX Global has a lower-cost schedule, but it appears to be a different LMAX Group lane. Its fee matrix includes TOB free at 1 update/sec, 2-5 levels from `$2,000` to `$12,000`, and 5+/10 levels from `$3,500` to `$15,000`, with a fee waiver if trading `>$5M/mo`. Before using it, we need to verify whether it exposes the same venue book, what historical/API rights exist, and whether it is suitable as primitive spot-FX orderflow evidence.

### Direct CME MDP 3.0

This is the true primitive source for our futures proxy lane.

Potential use:

- lowest-latency futures orderflow,
- direct feed-handler research,
- cleanest source for NQ/YM/GC/SI/6B/6J.

Blocker:

- direct public CME product pages were blocked by `403`, and the practical burden is high. Until we need institutional-grade latency, Databento/Sierra are better paths.

### Rithmic

Rithmic may matter if we later connect a futures broker/account and want execution plus data in one stack.

Evidence found:

- direct market access,
- high speed / low latency / ultra-low latency,
- real-time, delayed, and historical market data,
- broker/FCM neutral positioning.

Blocker:

- public page did not prove historical full-depth/MBO export comparable to Databento or Sierra `.depth`.

## Sources That Do Not Replace The Current Stack

Nasdaq TotalView/ITCH:

- Useful for Nasdaq equities and possible Nasdaq-100 constituent lead/lag studies.
- Not the primitive source for NAS100 futures/NQ.

IQFeed:

- Useful broad market data vendor.
- Does not solve full CME MBO/depth better than Databento/Sierra on evidence found.

CQG:

- Strong broad market-data/trading vendor.
- Public evidence is broad coverage, not a better GTOS extraction path.

dxFeed:

- Real-time/delayed/historical futures vendor with CME/CBOT/NYMEX/COMEX coverage.
- Worth keeping as backup or quote request, but no current evidence it beats Databento for MBO/MBP or Sierra for visual/full-depth workflow.

Cboe/ICE/Eurex:

- Primitive for their listed products.
- Not primary for our current CME futures proxy universe unless we add Cboe/ICE/Eurex-listed instruments.

## Current Decision

Keep the current working source architecture:

1. **Databento** for targeted historical/programmatic exchange data, especially CME `GLBX.MDP3` trades, MBP-10, and MBO.
2. **Sierra Chart** for delayed validation first, then Denali forward capture if `.depth` parser/parity passes.
3. **LMAX** as the first serious non-CME source to investigate if we want venue-native spot FX CLOB orderflow.
4. **Direct CME MDP 3.0** as a later institutional route, not the next practical step.

This is not vendor lock-in. It is a staged architecture:

- use the closest practical source now,
- verify with actual data and parser parity,
- only move closer to raw exchange feeds if the measured benefit exceeds the operational cost.

## Open Ambiguities

1. LMAX fee schedule is now parsed, but product identity remains open: LMAX Exchange and LMAX Global appear to be different fee/product lanes. LMAX Exchange ITCH/full-depth is too expensive for immediate GTOS research; LMAX Global is lower cost but needs source-provenance and access-rights verification.
2. LSEG FX Matching/FXall detailed data-feed pages were not accessible from the attempted direct URLs; only the product map from the LSEG FX homepage was usable.
3. Direct CME MDP 3.0 pricing/access requirements remain externally blocked from public `curl.exe` fetches.
4. Rithmic public page does not establish a historical full-depth/MBO export comparable to Databento.
5. dxFeed may have a viable futures historical depth offering, but the public page did not prove order-by-order/MBO access or better economics.
6. Whether primitive/proxy feeds lead the MT5 broker feed must be measured per instrument. It cannot be assumed.

## Next Steps

1. Keep Sierra Package 12 delayed-feed validation as the immediate low-cost parser/heatmap path.
2. Build the Sierra `.depth` parser and Databento parity report before considering Denali live fees.
3. Design a broker-vs-primitive lead/lag study using synchronized MT5 tick logs and Databento/Sierra futures proxy data.
4. Treat LMAX as a monitored venue-native candidate, not the next immediate source. Only continue if we can verify LMAX Global provenance/API/historical rights or obtain a non-ITCH Exchange lane that is cheap enough and not throttled out of lead-lag usefulness.
5. Revisit Rithmic only if we open a futures broker/account or need combined execution/data.
6. Keep dxFeed as a backup vendor to quote if Databento access/cost becomes a blocker.
7. Do not spend effort on direct CME MDP feed-handler work unless a future dossier shows Databento/Sierra latency/coverage is insufficient.
