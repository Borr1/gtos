# Domain 10 — Gold & Commodities Specific

**Slug:** `10_gold_commodities`
**Owner:** Phase 1 Worker Agent #10
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns commodity-market research with a strong gold focus: gold-as-hedge, gold-as-safe-haven, gold-dollar relationship, real-rate gold model, central-bank gold reserves, Shanghai Gold Exchange / LBMA / COMEX cross-venue dynamics, gold futures vs spot basis, silver-gold ratio, oil-gold relationship, commodity-currency spillover, COT-position-based commodity returns, contango / backwardation roll yield, commodity volatility / seasonality.

**IN scope:** Erb-Harvey commodity futures, Baur-Lucey gold safe-haven, Pukthuanthong-Roll gold-dollar, gold-real-rate models, central-bank-gold-purchase impact studies, gold-stock cointegration, oil and copper as macro regime indicators, COT-on-gold predictive papers, commodity term-structure literature, silver / platinum / palladium-specific work.

**OUT of scope:** **Commodity-currency macro relationships** (AUD-CAD-NOK) → 11; **option-implied gold volatility** → 16; **gold futures pricing-theory** (convenience yield models) → 01 / 16 split; **gold risk premium in factor models** → 13; **dealer-gamma in COMEX gold options OPEX** → 08.

---

## 2. Search strategy

### Keywords
- "gold price" determinants real rate
- "gold safe haven" stocks bonds Baur Lucey
- "gold dollar" Pukthuanthong Roll exchange rate
- "central bank gold" reserves return
- "gold futures basis" contango
- "Shanghai Gold Exchange" arbitrage
- "LBMA fix" gold afternoon morning
- "gold inflation hedge" empirical
- "silver gold ratio" trading
- "oil gold" relationship spillover
- "commodity index" S&P GSCI return
- "COT gold" speculator hedger
- "gold ETF" GLD demand
- "commodity term structure" roll yield
- "gold mining" stocks beta
- "platinum palladium" trade industrial

### Key journals
- *Journal of Banking and Finance*
- *Resources Policy*
- *Energy Economics*
- *Journal of Commodity Markets*
- *Financial Analysts Journal*
- *Journal of Futures Markets*
- *Review of Financial Studies* (occasional)
- *Journal of International Money and Finance*

### Repositories
- arXiv `q-fin.GN`
- SSRN Commodities & Energy eJournal
- World Gold Council research
- BIS commodity studies
- IMF working papers (commodity exporter)
- LBMA research
- OECD commodity working papers

### Key authors
- Claude Erb, Campbell Harvey (commodity futures)
- Dirk Baur, Brian Lucey (gold safe haven)
- Kuntara Pukthuanthong, Richard Roll (gold-dollar)
- Steven Capie, Terence Mills, Geoffrey Wood (gold long-history)
- Robert Engle (commodity vol — overlap)
- Kenneth Singleton (commodities and macro)
- Hilary Till (commodity research)
- World Gold Council (institutional research)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | The Strategic and Tactical Value of Commodity Futures | Erb, Harvey | 2006 | https://people.duke.edu/~charvey/Research/Working_Papers/W77_The_tactical_and.pdf |
| 2 | Is Gold a Hedge or a Safe Haven? An Analysis of Stocks, Bonds and Gold | Baur, Lucey | 2010 | https://brianmlucey.wordpress.com/wp-content/uploads/2011/05/gold_safehavenorhedge_fr.pdf |
| 3 | Is gold a safe haven? International evidence | Baur, McDermott | 2010 | https://www.sciencedirect.com/science/article/abs/pii/S0378426609003343 |
| 4 | Gold and the Dollar (and the Euro, Pound, and Yen) | Pukthuanthong, Roll | 2011 | https://ideas.repec.org/a/eee/jbfina/v35y2011i8p2070-2083.html |
| 5 | Gold as a hedge against the dollar | Capie, Mills, Wood | 2005 | search Journal of International Financial Markets, Institutions and Money — verify |
| 6 | The Golden Constant: The English and American Experience 1560-2007 | Erb, Harvey | 2013 | search Financial Analysts Journal — verify |
| 7 | Strategic Asset Allocation: Gold's Role | World Gold Council | various | wgc.org research |
| 8 | Anything but gold - The golden constant revisited | recent | 2021 | https://www.sciencedirect.com/science/article/abs/pii/S2405851321000040 |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Nonlinear dynamics of gold and the dollar (recent) | various | 2020 | https://www.sciencedirect.com/science/article/abs/pii/S1062940820300577 |
| 10 | Turn-of-the-year affect in gold prices: Decomposition Analysis | various | 2020 | https://arxiv.org/pdf/2003.11027 |
| 11 | Gold market liquidity / safe haven post-COVID | various | 2021-23 | search SSRN |
| 12 | Central bank gold purchases 2022-2024 | World Gold Council | 2022-25 | wgc.org |
| 13 | Gold and crypto safe-haven | various | 2022-24 | search arXiv q-fin.GN |
| 14 | LBMA fix vs continuous-trade gold | various | 2022-25 | search SSRN |

---

## 5. GTOS subsystem connections

- **XAUUSD primary instrument** — every empirical XAU paper directly informs the system; this domain is among the highest-leverage.
- **K52 — XAUUSD WR vs breakeven 62%** — gold-edge literature should explain *why* 62% is plausible / decay-risk.
- **F11 — XAU OB-zone advantage decay velocity** — domain literature on edge-decay in gold-trading rules.
- **F2 — XAU London/trending_bull LONG cell -59.8pp** — the regime-conditioned LONG-side selectivity collapse may relate to gold-specific real-rate / DXY regimes.
- **A6 — LONG-side selectivity collapse** — gold safe-haven literature relevant: gold rallies asymmetrically on bad news, so LONG-side edge may differ from SHORT-side fundamentally.
- **XAGUSD recently added (2026-04-25)** — silver-gold ratio literature gives priors for silver's behavior.
- **Cross-instrument correlation gate** — gold-vs-FX correlation literature underpins the JPY_CROSSES + DXY context.
- **Risk gate at NFP / FOMC** — gold-volatility-around-events literature anchors event-window logic.

---

## 6. Cross-domain handoff rules

- **AUD/CAD/NOK as commodity-currency pairs** → 11 (we keep gold-as-driver-of-currency-flows; 11 keeps currency-as-asset).
- **Heston / SABR fitting on COMEX gold options** → 16.
- **Gold dealer-gamma / OPEX** → 08.
- **Gold in factor models / equity-bond-gold portfolio risk** → 13.
- **Behavioral gold demand** (Indian wedding-season, Chinese New Year) → 17 (we keep the empirical price effect).
- **Quantum / hedge fund gold strategies** → 22.

---

## 7. Output spec

Files:
- `research/ml_program/literature/10_gold_commodities/papers.md`
- `research/ml_program/literature/10_gold_commodities/papers.csv`

Same schema. Special field: `commodity_subset` (gold / silver / platinum / palladium / oil / copper / agricultural / index).

---

## 8. Quality bar / target

35-50 papers. Worker should ensure: at least 20 specifically on gold; at least 5 on silver / silver-gold ratio; at least 5 on oil-gold or commodity-correlation; at least 5 on commodity-currency spillover (cross-link to 11); at least 5 specifically post-2020 to capture recent regime (rates-driven gold, central-bank-buying era).
