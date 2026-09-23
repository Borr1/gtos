# Domain 06 — Market Microstructure & Order Book

**Slug:** `06_market_microstructure_orderbook`
**Owner:** Phase 1 Worker Agent #6
**Target paper count:** 45-60

---

## 1. Domain scope statement

This domain owns the empirical and theoretical literature on **how prices form** at the sub-second scale: limit order books, market makers / dealers, bid-ask spreads, asymmetric-information models (Kyle, Glosten-Milgrom), price discovery, market impact, order-book dynamics, queue dynamics, latency arbitrage, fragmentation, lit / dark venues, optimal market-making (Avellaneda-Stoikov and successors), HFT / latency arbitrage, depth / liquidity measurement, transaction-cost analysis (TCA).

**IN scope:** Kyle 1985, Glosten-Milgrom 1985, Roll 1984 implicit spread, Easley-O'Hara PIN/VPIN, Avellaneda-Stoikov optimal market-making, Cont-Kukanov-Stoikov order-flow imbalance, order-book queueing models, hypothesized market-making behavior, price impact functions (linear/sqrt/concave), Almgren optimal execution.

**OUT of scope:** **Order flow as ICT footprint feature** for directional trading → 07; **flow toxicity / VPIN as a regime-detection feature** → 05 with cross-link; **gamma-flow / dealer-hedging effects on indices** → 12; high-frequency **statistical-process modeling** of returns → 03 with cross-link; **execution algorithms applied to retail-size orders** that touch GTOS → ours, but conservative.

---

## 2. Search strategy

### Keywords
- "limit order book" "price impact"
- "bid ask spread" decomposition adverse selection
- "Kyle model" insider trading lambda
- "PIN" "probability informed trading" Easley
- "VPIN" "volume synchronized" toxicity
- "order flow imbalance" Cont Kukanov Stoikov
- "market making" inventory Avellaneda Stoikov
- "optimal execution" Almgren Chriss
- "latency arbitrage" HFT
- "queue position" limit order
- "hidden orders" iceberg execution
- "midprice forecasting" deep learning order book
- "spoofing" "layering" market manipulation
- "flash crash" 2010 microstructure
- "dealer market" inventory risk

### Key journals
- *Journal of Financial Markets*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Journal of Finance*
- *Quantitative Finance*
- *Market Microstructure and Liquidity*
- *Journal of Econometrics*
- *SIAM Journal on Financial Mathematics*

### Repositories
- arXiv `q-fin.TR` (trading), `q-fin.MM` (market microstructure)
- SSRN Microstructure: Specialty journal eJournal
- BIS quarterly market reports
- ECB working papers (FX microstructure)
- Maureen O'Hara, Larry Harris, Avellaneda personal pages
- CFM / Capital Fund Management publications (Bouchaud)

### Key authors
- Albert S. Kyle, Maureen O'Hara, Larry Harris (foundational)
- Lawrence Glosten, Paul Milgrom (foundational)
- Marco Avellaneda, Sasha Stoikov (market-making)
- Rama Cont, Arseniy Kukanov (order flow)
- Robert Almgren, Neil Chriss (optimal execution)
- David Easley, Marcos Lopez de Prado (VPIN / flow toxicity)
- Jean-Philippe Bouchaud, Jonathan Donier, Jean-Francois Muzy (impact, Bouchaud school)
- Charles-Albert Lehalle, Sophie Laruelle (practitioner-academic)
- Anna Obizhaeva, Jiang Wang (Q4 impact)
- Alvaro Cartea, Sebastian Jaimungal (HFT books)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Continuous Auctions and Insider Trading | Kyle | 1985 | https://personal.utdallas.edu/~nina.baranchuk/Fin7310/papers/Kyle1985.pdf |
| 2 | Bid, ask and transaction prices in a specialist market with heterogeneously informed traders | Glosten, Milgrom | 1985 | https://milgrom.people.stanford.edu/wp-content/uploads/1984/09/Bid-Ask-and-Transaction-Prices.pdf |
| 3 | High-frequency trading in a limit order book | Avellaneda, Stoikov | 2008 | https://people.orie.cornell.edu/sfs33/LimitOrderBook.pdf |
| 4 | Optimal Execution of Portfolio Transactions | Almgren, Chriss | 2000 | https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf |
| 5 | The Price Impact of Order Book Events | Cont, Kukanov, Stoikov | 2014 | https://arxiv.org/abs/1011.6402 |
| 6 | Statistical properties of stock order books: empirical results and models | Bouchaud, Mezard, Potters | 2002 | https://arxiv.org/abs/cond-mat/0203511 |
| 7 | Flow Toxicity and Liquidity in a High Frequency World | Easley, Lopez de Prado, O'Hara | 2012 | https://www.quantresearch.org/VPIN.pdf |
| 8 | Optimal execution with nonlinear impact functions | Almgren | 2003 | https://www.tandfonline.com/doi/abs/10.1080/135048602100056 |
| 9 | Market Microstructure In Practice (book, 2nd ed) | Lehalle, Laruelle | 2018 | https://www.worldscientific.com/worldscibooks/10.1142/10739 |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 10 | Cross-impact of order flow imbalance in equity markets | various | 2023 | https://www.tandfonline.com/doi/full/10.1080/14697688.2023.2236159 |
| 11 | The Price Impact of Generalized Order Flow Imbalance | Briola et al | 2021 | https://arxiv.org/pdf/2112.02947 |
| 12 | Order Flow Imbalances and Amplification of Price Movements (US Treasury) | Fed | 2025 | https://www.federalreserve.gov/econres/notes/feds-notes/order-flow-imbalances-and-amplification-of-price-movements-evidence-from-u-s-treasury-markets-20251103.html |
| 13 | Order Flow Decomposition for Price Impact Analysis | various | 2023 | https://dl.acm.org/doi/10.1145/3604237.3626874 |
| 14 | Deep order book LSTM / transformer mid-price | Sirignano, Cont and successors | 2019-2024 | search arXiv q-fin.TR |

---

## 5. GTOS subsystem connections

- **Tick-capture daemon** writes per-tick parquet → `tick_features.py` extracts 12 microstructure features. Domain 06 is the literature anchor for which features are theoretically motivated (OFI, micro-price, queue ratio).
- **E24/E26 microstructure null verdict** (memory `project_microstructure_archived_2026-04-27`) — domain literature should explain *why* M15-aggregated microstructure has limited predictive lift; pointers may exist for sub-M5 thresholds.
- **MT5 spread model** vs venue-true spread — Cont-Stoikov OFI literature directly motivates how to interpret MT5 tick-bid/tick-ask snapshots.
- **Order-block detection (`market_state.py`)** — the OB construct is hypothesized institutional supply/demand zone; Kyle / Glosten-Milgrom adverse-selection theory frames *why* OB retests have edge.
- **K54 v2 features** — order-flow imbalance, micro-price deviation from mid, queue dynamics as candidate features (subject to MT5 data quality).
- **Execution slippage analysis** (Almgren-Chriss; per-instrument) — unused but directly applicable for redacted_account fill-quality assessment.

---

## 6. Cross-domain handoff rules

- **ICT order block / liquidity-grab** narratives → 07.
- **Volume-and-price** auction-theory framing (VWAP, OPEX) → 08.
- **Distributional consequences** (long memory of order flow as Hurst phenomenon) → 03 with cross-link, but Lillo-Farmer-style empirical microstructure stays here.
- **Optimal market making with constraints** → ours (06), but algorithmic-execution-of-meta-orders crosses with 19 / 20.
- **Dealer-gamma options-market hedging flows** → 12 (equity indices + options).
- **FX-specific microstructure** (Lyons hot-potato, Evans-Lyons order flow → exchange rate) → 11 (FX domain) but cross-linked here.

---

## 7. Output spec

Files:
- `research/ml_program/literature/06_market_microstructure_orderbook/papers.md`
- `research/ml_program/literature/06_market_microstructure_orderbook/papers.csv`

Same schema. Each paper should annotate `data_source` (TAQ, EBS, Reuters, Nasdaq ITCH, KOSDAQ, simulated, etc.) — useful when worker assesses applicability to MT5 broker tick data.

---

## 8. Quality bar / target

45-60 papers. Largest in the foundations cluster because microstructure is dense and theory + empirics are both well-developed. Worker should make sure at least 5 papers cover **FX-specific** microstructure (USDJPY, EBS) since GTOS has 4 FX instruments, and 5 papers cover **futures** microstructure (US30, NAS100, gold).
