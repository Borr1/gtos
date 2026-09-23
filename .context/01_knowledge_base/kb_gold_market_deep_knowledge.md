# KB: Gold Market Deep Knowledge — How XAUUSD Actually Works

**Version:** 1.0 | **Date:** 2026-04-05 | **Status:** Final Synthesis  
**Sources:** 6 research sessions + 1 Claude Code empirical analysis + 1 red team review  
**Purpose:** Permanent reference for the AI trading mentor. Searchable by `project_knowledge_search`.

---

## 1. Three-Layer Market Architecture — How Gold Trades

Gold does not trade on a single exchange. It trades across three interconnected layers, each with different participants, liquidity profiles, and price discovery roles. Understanding this architecture is essential because it determines what our MT5 charts actually represent and why session-based patterns exist.

### Layer 1: LBMA OTC Market (London — Physical Center)

The London Bullion Market Association (LBMA) oversees the world's largest physical gold market. This is a wholesale, over-the-counter market where trades are bilateral — negotiated directly between counterparties without a central order book. Approximately $25 billion settles through London daily in cleared volume, with estimated gross daily turnover significantly higher. [HIGH confidence — LBMA official clearing data]

Thirteen market-making member banks (including HSBC, JP Morgan, Goldman Sachs, UBS, Citibank) are required to quote continuous two-way prices during London business hours. Settlement is T+2 via "loco London" — physical gold held in London vaults (Bank of England, HSBC, JP Morgan, Brinks, Malca-Amit, Loomis). Gold is held either "allocated" (specific bars segregated for the client) or "unallocated" (the client has a claim on the bank's pool). The unallocated system operates with significant leverage; exact backing ratios are not publicly audited and should not be assumed.

**The LBMA Gold Price (Fix)** is set twice daily via electronic auction administered by ICE Benchmark Administration (IBA):

- **AM Fix: 10:30 AM London time** = 09:30 UTC (BST) / 10:30 UTC (GMT)
- **PM Fix: 3:00 PM London time** = 14:00 UTC (BST) / 15:00 UTC (GMT)

The fix involves 12-15 direct participants submitting buy/sell orders in 30-second rounds until the imbalance falls within a 10,000 oz threshold. This benchmark price is referenced globally — ETF NAV calculations, central bank valuations, mining contracts, and physical settlement all reference it. [HIGH confidence — ICE Benchmark Administration documentation]

**Critical for the trading system:** The AM Fix falls within or at the boundary of the London kill zone (07:00-10:30 UTC). The PM Fix falls within the NY kill zone (13:00-15:30 UTC). Fix-related institutional order flow concentrates in the 30-60 minutes preceding the fix, creating directional flows that overlap with our trading windows.

### Layer 2: COMEX Futures (New York — Price Discovery Engine)

COMEX (CME Group) handles approximately 80% of global gold futures volume. On a typical day, 200,000-300,000 contracts trade, each representing 100 troy ounces. Less than 1% result in physical delivery. Trading occurs nearly 23 hours/day on CME Globex, with regular trading hours starting at 08:20 AM ET (12:20 UTC). [HIGH confidence — CME Group documentation]

Despite LBMA handling far more notional volume, academic research (Hauptfleisch, Putniņš & Lucey, 2016, *Journal of Futures Markets*, 17-year sample at 1-second granularity) demonstrates that **COMEX futures contribute MORE to gold price discovery than London OTC on average.** This is because COMEX provides a transparent, centralized limit order book while London's OTC market is opaque. Market structure matters more than raw volume for price discovery. [HIGH confidence — peer-reviewed, replicated finding]

The spot XAU/USD price that retail traders see is derived from the nearest active COMEX futures contract, adjusted for cost of carry. Arbitrageurs keep COMEX and LBMA aligned via Exchange for Physical (EFP) transactions; the typical spread is approximately $3-4/oz under normal conditions.

**COMEX opening at approximately 12:20-13:00 UTC coincides with the start of our NY kill zone.** The heaviest COMEX volume occurs in the first 2-3 hours, overlapping perfectly.

### Layer 3: Retail CFD/Broker Layer (Where We Trade)

When we trade XAU/USD on MetaTrader 5, we are NOT trading on LBMA or COMEX. We trade a Contract for Difference (CFD) — a bilateral contract between us and the broker's liquidity provider. [HIGH confidence]

The broker aggregates price feeds from institutional spot dealers and the nearest liquid COMEX futures, applies their own spread markup, and streams bid/ask to MT5. Execution is either internalized (broker takes the other side) or routed to a liquidity provider. Everything is cash-settled; there is no physical delivery.

**Practical implications for the system:**
- Our spread gate (>30 cents) measures broker-level spread, not institutional spread. It correlates with but doesn't directly represent market depth.
- Different brokers show slightly different candle shapes (especially wicks) because their LPs and spread models differ. Our "order blocks" are computed from our specific broker's feed.
- This doesn't invalidate the edge — structural patterns persist across reasonable price feeds — but exact-pip entries and stops should include buffers, and candle values may show small discrepancies vs. TradingView.

---

## 2. Who Moves Gold — The Actors and Their Behavior

### Central Banks (Macro Demand Floor, NOT Intraday Signal)

Central bank gold buying has been the dominant structural force since 2022: approximately 1,082 tonnes (2022), 1,037t (2023), 1,045t (2024), and 863t (2025), against total annual mine production of ~3,600-3,700 tonnes. Central banks are absorbing 23-29% of newly mined gold. [HIGH confidence — World Gold Council primary data]

Key buyers in 2025 included Poland (102t), Kazakhstan (57t), Brazil (43t), Azerbaijan (38t), and China (27t reported, likely significantly higher unreported). China stopped publicly reporting purchases in May 2024 and likely continues buying through commercial banks and state enterprises. [HIGH confidence for reported figures; LOW for China actual totals]

**How central bank purchases affect our system:** They are almost entirely invisible on intraday charts. Central banks buy through LBMA market makers via OTC negotiation — not on COMEX, not on any exchange. A bank buying 100 tonnes/year is buying ~$28 million/day, absorbed by market makers as normal flow without single-day impact. The purchases create a **structural demand floor**, not identifiable price patterns. When gold drops, central banks with allocation targets buy more aggressively, creating persistent bid interest below market. J.P. Morgan estimates sovereign buyers become aggressive at roughly 10-15% below current prices. [HIGH for mechanism, MEDIUM for specific floor levels]

**Operational rule:** Central bank buying supports the D1/H4 bullish bias assessment. It is NOT an intraday signal. As long as central banks remain net buyers, the macro tailwind for bullish gold setups persists.

### Managed Money (CTAs, Hedge Funds) — Speculative Momentum

Managed money represents the speculative positioning that dominates COMEX futures. As of late March 2026, managed money held approximately 120,000 long contracts vs. 27,000 short contracts (net long ~93K). This is at the 52nd percentile of its 4-year range. [HIGH confidence — CFTC disaggregated report]

**COT positioning has ZERO predictive value for gold at 1-week or 4-week horizons.** This was conclusively demonstrated by the Claude Code empirical analysis: 209 weekly records (2022-2025), Spearman correlations of +0.048 (managed money level vs 1-week return, p=0.495) and +0.095 (vs 4-week, p=0.170). Extreme positioning (>90th / <10th percentile) showed no significant difference in forward returns (all p > 0.4). [HIGH confidence — rigorous empirical test]

This null result holds during a period where gold moved from ~$1,800 to ~$2,600+, meaning the massive trend swamped any positioning signal. **Do NOT implement COT as a filter, input, or context signal for the system.** Adding it would inject noise and increase prompt narrative fitting risk.

### Swap Dealers (LBMA Market Makers — Hedging, Not Directional)

Swap dealers held ~30,000 long / ~212,000 short contracts as of March 2026 — the largest short category. These are LBMA market makers hedging their OTC exposure via COMEX futures. Their positioning reflects OTC market flow, NOT their directional view. [HIGH confidence]

### Algorithmic Market Makers

Modern gold futures trading on COMEX is increasingly dominated by algorithmic market-making firms (Citadel Securities, Jump Trading, XTX Markets, etc.). These firms profit from bid-ask spread capture, not directional bets or retail stop-hunting. Retail flow is a tiny fraction of gold's daily volume. The idea that institutions engineer multi-hour price moves to capture retail stops is unsupported by any published microstructure study. [HIGH confidence]

---

## 3. Session Dynamics — Why Time Structure Matters for Gold

### Why Asian Sessions Produce Ranges

During Asian hours (approximately 00:00-07:00 UTC), the primary LBMA market makers are closed. Active participants are Tokyo-based banks (TOCOM/JPX), Shanghai Gold Exchange participants, Australian banks, and Singapore desks. This participant base is significantly smaller than London's. Shanghai futures contribute only ~15% of gold price discovery during Asian hours, compared to COMEX's 47% even during Asian hours (Sehgal, 2021). [HIGH confidence]

The mechanical result: lower volume, wider spreads, less directional conviction. Price tends to range. The Asian session high and low become visible reference levels on every institutional desk's screen. Stop orders cluster above the Asian high and below the Asian low — not as conspiracy, but as the mechanical result of every risk manager and algorithmic system seeing the same levels.

**Gold-specific finding:** Gold sweeps of Asian range levels are 96.3% breakout/continuation events, NOT reversals. This is instrument-specific — GBPUSD shows 19.6% rejection. For gold, do NOT trade against an Asian range sweep. Look for OB retests in the direction of the sweep. [HIGH confidence — project data]

### London Open (07:00 UTC) — Regime Change, Not Just More Volume

At 07:00 UTC, LBMA member banks come online. The changes are structural:
1. OTC liquidity depth increases 5-10x as 13 market-making banks begin quoting.
2. Positioning for the AM Fix (09:30/10:30 UTC) begins, creating directional flows.
3. European macro data releases cluster 07:00-10:00 UTC.
4. Physical gold settlement flows activate.

**However, the empirical evidence challenges the assumption that London produces the biggest moves.** The Claude Code analysis found London (07:00-10:00 UTC) average hourly range was 0.608% — NOT statistically higher than overnight (0.706%, Mann-Whitney p=0.954). **Gold volatility peaks in NY session (13:00-15:00 UTC), not London.** Peak hourly ranges: 14:00 UTC = 1.053%, 15:00 UTC = 1.073%. [HIGH confidence — 60-day empirical sample]

This creates an important insight: **the system's strong London performance (82.8% WR on late London setups) is likely driven by setup quality, not volatility.** The AM Fix creates concentrated institutional order flow that produces clean structural breaks with genuine directional conviction — even if the volatility magnitude is unremarkable. Quality of displacement matters more than size of displacement. [MEDIUM confidence — hypothesis consistent with data but not directly tested]

### NY Open (13:00 UTC) — Flow Collision Zone

At approximately 13:00 UTC, COMEX volume surges. The London-NY overlap (12:00-16:00 UTC) is the most liquid and most informative gold window globally, contributing >50% of daily price discovery. [HIGH confidence — Hauptfleisch et al., 2016]

**The first 15 minutes are problematic.** The system recorded 0% WR on trades at exactly 13:00 UTC (n=7 — small but directionally consistent with academic evidence). Four converging mechanisms explain this:

1. **Flow collision:** European closing flows (profit-taking) collide with American opening flows (new positions).
2. **Algorithmic momentum ignition:** SEC-documented strategies where algorithms spark aggressive initial moves that reverse. Session opens are the optimal environment.
3. **Order flow imbalance reversal:** Academic research across asset classes shows large-trader order flow peaks in the first half-hour then reverses, creating adverse selection for first-candle followers.
4. **PM Fix positioning:** Institutional participants begin positioning 1-2 hours before the PM Fix, which can create false initial moves.

[HIGH confidence for the multi-source convergence; LOW-MEDIUM for the n=7 internal data alone]

**Operational rule:** Skip 13:00-13:15 UTC entirely for XAUUSD. Zero-cost filter with robust multi-source justification.

### DST Awareness — Hidden Variable

The LBMA Fix times are defined in London local time (BST/GMT), NOT UTC. US data releases are defined in US Eastern Time. This creates windows during UK/US DST transitions where the relationship between our fixed UTC kill zones and underlying institutional events shifts. For example, in early November the AM Fix moves from 09:30 to 10:30 UTC, and NFP moves from 12:30 to 13:30 UTC.

**Operational rule:** Track whether WR differs during DST-transition weeks. This is a free analysis that could reveal a hidden performance confound. [MEDIUM confidence — identified as hidden variable, untested]

---

## 4. Kill Zone Alignment with Market Microstructure

| Kill Zone | UTC | Microstructural Justification |
|---|---|---|
| London | 07:00-10:30 | LBMA banks online, massive OTC liquidity increase. AM Fix at 09:30/10:30 UTC creates concentrated institutional flow. Extended to 10:30 is justified by 82.8% late-London WR and Fix capture. |
| NY | 13:00-15:30 | COMEX volume surge, US data releases, London-NY overlap. Peak gold volatility (1.05% avg hourly range). Skip 13:00-13:15 (collision zone). |
| Tokyo (JPY only) | 00:00-03:00 | Thin OTC liquidity, TOCOM + SGE active. Range-building phase. JPY-specific because carry trade dynamics create directional setups that gold does not have. |

**Gap: 10:30-13:00 UTC is correctly uncovered for XAUUSD.** Extended London testing showed 45.6% continuation in this window — below baseline. The structural reason: by 10:30, London's directional move is typically complete, and the pre-NY lull creates choppy action. Do NOT expand London KZ beyond 10:30 for gold. [HIGH confidence]

---

## 5. Gold-Specific Institutional Calendar Events

| Event | Timing | Impact | System Response |
|---|---|---|---|
| LBMA AM Fix | 09:30 or 10:30 UTC (DST) | Concentrated institutional flow, clean structural breaks | Captured by London KZ extension |
| LBMA PM Fix | 14:00 or 15:00 UTC (DST) | ETF NAV settlement, speculative participation | Captured by NY KZ |
| NFP | 12:30 or 13:30 UTC (DST) | Highest single-day volatility spike for gold | System shows 68% WR on news days; avoid exact 13:00 candle on NFP days |
| FOMC | 18:00 UTC (14:00 ET) | Dominant predictor of intraday gold price jumps (Smales, 2024) | Falls outside KZ, but pre-announcement positioning starts hours earlier. Consider reduced size on FOMC days |
| COMEX Monthly OPEX | Third Friday | Potential "pinning" at round strikes. Effect is small and brief | NOT worth a calendar filter at current trade frequency |
| BCOM/GSCI Rebalancing | Early January, annually | One-time selling pressure. Effect is small | NOT worth a calendar filter |

[HIGH confidence for NFP/FOMC; MEDIUM for fix dynamics; LOW for OPEX/rebalancing effects]

---

## 6. Day-of-Week and Seasonal Patterns — Null Results

The Claude Code analysis tested day-of-week effects on 1,068 daily bars (2022-2026):

- Individual day returns: Tuesday and Wednesday showed individually significant returns (p=0.035, p=0.040), but the omnibus Kruskal-Wallis test across all days was NOT significant (p=0.768). Individual day results do not survive this omnibus test.
- Day-of-week volatility: NOT significant (Kruskal-Wallis p=0.115).

**Operational rule:** Do NOT implement day-of-week filters. No calendar-based time filter is statistically warranted. [HIGH confidence — clean null results]

---

## 7. DXY-Gold Relationship

The DXY-gold inverse correlation is very stable. Over 816 common trading days (2023-2026): Pearson r = -0.369 (p = 1.1e-27), regression slope of -1.078 (1% DXY move → approximately -1.08% gold move), R² = 0.136. The 30-day rolling correlation was negative 95.7% of the time, with only brief breakdown periods lasting less than 3 weeks. [HIGH confidence — large empirical sample]

**However:** R² of 0.136 means DXY explains only 14% of gold's daily moves. At the M15/H1 timeframe, the signal-to-noise ratio is questionable for intraday decisions. The relationship is reliable directionally but not deterministic.

**Operational rule:** DXY direction is useful as soft context. It is NOT a hard filter or gate. Do not invest development time in a DXY integration layer. When DXY and gold move in the same direction simultaneously (4.3% of the time), treat it as an anomaly worth noting but not as an invalidation signal. [HIGH confidence]

---

## 8. Open Questions and Known Unknowns

1. **Does London setup quality explain the system's strong London performance despite unremarkable London volatility?** Untested. The distinction between setup quality and volatility as drivers of WR has not been formally investigated.

2. **How does algorithmic market-making on COMEX interact with H1 structural patterns?** If algo strategies have shortened the decay window for structural levels, this directly impacts the system's edge. No academic paper covers this.

3. **Does the broker's specific liquidity provider create systematic candle bias?** We don't know our broker's LP identity or their aggregation methodology. Different brokers showing different wicks at the same moment is documented.

4. **What happens to gold price discovery as Shanghai's share grows?** Sehgal (2021) found Shanghai's contribution increasing from ~15% to ~26%. If this trend continues, Asian session assumptions may need revision.

5. **China's unreported gold purchases:** The single largest uncertainty in gold market analysis. If true buying is 200+ tonnes/year (vs 27t reported in 2025), the structural bid is even stronger than publicly estimated. This is unknowable from public sources.

---

## Sources

- LBMA Official Documentation — OTC market guide, Gold Price FAQs, clearing data (January 2026)
- ICE Benchmark Administration — LBMA Gold Price methodology
- CME Group — COMEX gold futures specifications, volume data
- Hauptfleisch, Putniņš & Lucey (2016) — "Who Sets the Price of Gold?" *Journal of Futures Markets*, 36(6), 564-586
- Sehgal & Sobti (2021) — "Who leads in intraday gold price discovery?" *Journal of Futures Markets*, 41(7), 1092-1123
- Caminschi & Heaney (2014) — "Fixing a Leaky Fixing" *Journal of Futures Markets*, 34(11), 1003-1039
- Smales (2024) — "Gold Intra-day Returns and Monetary Policy Shocks" *International Review of Financial Analysis*
- World Gold Council — Gold Demand Trends Full Year 2025, Central Bank Gold Reserves Survey
- CFTC — Commitments of Traders (Disaggregated), weekly reports 2022-2026
- Claude Code empirical analysis — COT correlations, hourly volatility, DXY analysis, seasonality (2026-04-05)
- Multiple broker documentation (Dukascopy, Axi, Saxo) — CFD pricing mechanics

---

*End of Document 1. Approximately 4,500 words.*
