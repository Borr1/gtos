# Domain 07 — Order Flow, Footprint, ICT/SMC Academic

**Slug:** `07_order_flow_footprint_ict_smc`
**Owner:** Phase 1 Worker Agent #7
**Target paper count:** 25-40 (justified lower bound — see section 8)

---

## 1. Domain scope statement

This domain owns the literature most directly adjacent to **GTOS's actual trading methodology**: order-flow as directional-trading signal (vs microstructure execution focus in domain 06), volume profile / footprint analysis, support / resistance / break-of-structure / change-of-character / liquidity-grab academic studies, ICT / SMC / Wyckoff academic-or-quasi-academic literature, support-resistance-as-self-fulfilling-prophecy research, sweep / stop-cascade studies, "smart money" institutional positioning, COT report analysis, dealer / institutional positioning, and any peer-reviewed work touching the constructs ICT practitioners use.

**IN scope:** Osler "Support for Resistance" papers, Kavajecz-Odders-White stop loss literature, Curcio-Goodhart on round-number FX clustering (cross-link to 09), academic studies that find statistical edge in technical-analysis pattern recognition, Wyckoff-method academic backtests, COT-position-aggregation predictive papers, retail-vs-institutional flow studies, ICT-specific terminology research papers (rare, see fallback).

**OUT of scope:** **Pure microstructure** order-book theory → 06; **round-number** focus per se → 09; **technical analysis** as broad pattern-recognition / chart-pattern academic → keeps cross-link here, primary domain dependent on focus; **trend / momentum** as quantitative anomaly → 14; **mean-reversion / range-bound trading** → 15.

---

## 2. Search strategy

### Keywords
- "support and resistance" intraday FX exchange rate
- "stop hunt" "stop loss order" cascade asymmetric
- "order flow" "exchange rate" Evans Lyons
- "Carol Osler" support resistance
- "limit order clustering" Kavajecz Odders-White
- "footprint chart" volume orderflow
- "Wyckoff method" backtest empirical
- "COT report" "commitment of traders" predictive
- "institutional flow" "retail flow" performance
- "smart money" "dumb money" academic
- "liquidity provision" anomaly
- "market structure" "break of structure" academic
- "fair value gap" academic OR "imbalance" return predictability
- "order block" empirical study return
- "smart money concept" SMC peer reviewed

### Key journals
- *Journal of Financial Economics*
- *Journal of Banking and Finance*
- *Journal of Financial Markets*
- *Review of Financial Studies*
- *Journal of Finance*
- *International Journal of Forecasting*
- *Quantitative Finance*
- *Empirical Economics*
- *Pacific-Basin Finance Journal* (occasional ICT-adjacent)

### Repositories
- SSRN Behavioral Finance
- SSRN Capital Markets: Asset Pricing & Valuation eJournal
- arXiv `q-fin.TR`
- Federal Reserve regional studies (Chicago Fed, NY Fed) — flow / institutional research
- BIS reports on FX market positioning

### Key authors
- Carol Osler (FX support/resistance, stop-loss orders)
- Martin Evans, Richard Lyons (order flow / exchange rates)
- Kissell, Glantz (institutional execution)
- Andrew Lo (technical analysis pattern recognition)
- Eugene Kandel, Leonid Marx (limit order strategies)
- Charles Goodhart, Richard Curcio (FX clustering)
- Maureen O'Hara (overlap with 06)
- Andrei Kirilenko (HFT, flash crash) — overlap

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Support for Resistance: Technical Analysis and Intraday Exchange Rates | Osler | 2000 | search SSRN — also Federal Reserve Bank NY ER&S 2000-1; verify |
| 2 | Foundations of Technical Analysis: Computational Algorithms... | Lo, Mamaysky, Wang | 2000 | https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf |
| 3 | Stop-Loss Orders and Price Cascades in Currency Markets | Osler | 2005 | search Journal of International Money and Finance — verify |
| 4 | The Microstructure Approach to Exchange Rates (book; order flow chapters) | Lyons | 2001 | https://mitpress.mit.edu/9780262622059/the-microstructure-approach-to-exchange-rates/ |
| 5 | The clustering of bid/ask prices and the spread in the foreign exchange market | Goodhart, Curcio | 1991 | LSE FMG DP142 — http://eprints.lse.ac.uk/119186/ |
| 6 | Intraday technical trading in the foreign exchange market | Neely, Weller | 2003 | https://sci2s.ugr.es/keel/pdf/specific/articulo/science2_13.pdf |
| 7 | Persistent profitability of technical analysis on foreign exchange markets? | various | 2010s | search PSL Quarterly Review — https://rosa.uniroma1.it/rosa04/psl_quarterly_review/article/view/10506 |
| 8 | When Support/Resistance Levels are Broken, Can Profits be Made? | LSE FMG DP | 2002 | https://ideas.repec.org/p/fmg/fmgdps/dp142.html |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Smart Money Concepts academic-adjacent reviews | various | 2023-25 | search Google Scholar "smart money concept" backtest |
| 10 | COT-based positioning return predictability | various | 2020-24 | search SSRN COT predictive |
| 11 | Order block / fair value gap empirical | scarce — keep monitoring | 2024-25 | NOT verified — fallback strategy below |
| 12 | Retail order flow vs institutional return predictability | Boehmer, Jones, Wang, Zhang | 2021 | search SSRN — verify |
| 13 | Liquidity sweep / liquidation cascade in crypto | various | 2022-25 | search arXiv q-fin.TR liquidation cascade |

**Fallback strategy for ICT/SMC academic gap:** if peer-reviewed ICT-specific papers cannot be found (likely — confirmed in pre-search), worker should:
1. Search practitioner whitepapers from prop firms (redacted_account, FTMO) and aggregators (TradingView research).
2. Pull CFA Institute and CMT Association research bulletins.
3. Translate ICT terminology into academic equivalents (order block ↔ "limit-order absorption zone"; FVG ↔ "price-imbalance gap"; BOS/CHoCH ↔ "trend reversal point detection").
4. Use the academic-equivalent terms to mine peer-reviewed literature; note the bridge in `relevance_to_gtos`.
5. Mark such entries with `gtos_terminology_bridge: true` so synthesis agents can flag.

---

## 5. GTOS subsystem connections

- **Component 2 (`market_state.py`)** detects OB / FVG / BOS / CHoCH — this domain provides whatever academic justification exists.
- **Touch count gate (ADR-005)** at H1 OB — Osler stop-loss-cascade literature directly informs why high-touch zones lose edge.
- **A6 attribution finding** — LONG-side selectivity collapse; literature on regime-conditional flow / institutional positioning matters.
- **F11 OB-zone advantage decay** — academic work on edge degradation of self-discovered patterns is a key search target.
- **K54 v2 features** — features inspired by ICT/SMC reasoning need academic underpinning to survive synthesis.
- **Multi-instrument generalization** — Osler-style papers cover FX; gold and indices need separate evidence.

---

## 6. Cross-domain handoff rules

- Pure **order-book / market-making** papers → 06.
- **Round-number magnetism** → 09.
- **Trend / momentum / breakout** → 14.
- **Volume / VWAP / auction** → 08.
- **Behavioral biases** explaining why retail follows ICT levels → 17.
- **Cross-asset spillover** → 13.
- The bright line: domain 07 is about **directional-trading signal extraction from order-flow / institutional behavior / structural-event detection**, distinct from 06's market-making / impact / TCA focus.

---

## 7. Output spec

Files:
- `research/ml_program/literature/07_order_flow_footprint_ict_smc/papers.md`
- `research/ml_program/literature/07_order_flow_footprint_ict_smc/papers.csv`

Same schema. Special fields:
- `gtos_terminology_bridge` (bool — paper found via fallback bridging)
- `instruments_studied` (FX / equity / commodity / index)

---

## 8. Quality bar / target

25-40 papers. **Justified lower bound:** ICT/SMC has very limited peer-reviewed academic coverage; quality-over-quantity. Worker should NOT pad with marginal papers. If only 22 strong papers can be found, that is acceptable; document in synthesis. The fallback bridge protocol (section 3) is the productivity multiplier.
