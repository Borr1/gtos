# Domain 09 — Round-Number Effects & Level Magnetism

**Slug:** `09_round_numbers_level_magnetism`
**Owner:** Phase 1 Worker Agent #9
**Target paper count:** 20-30 (justified bound — see section 8)

---

## 1. Domain scope statement

This domain owns research on **price clustering at round numbers and psychological levels** and the related "magnetism" / "barrier" effects: clustering of bids/asks at 00 and 50 endings, mathematical / behavioral / institutional explanations, evidence of round-number support / resistance / breakout asymmetry, Donaldson-Kim Dow-thousands barriers, gold and FX round-number price clustering, intraday round-number-trigger effects, "ghost levels" (50-pip / 100-pip / quarter-figure round numbers in FX), Benford's law tests in stock prices, ICT-style levels' overlap with round numbers.

**IN scope:** Donaldson-Kim 1993, Sopranzetti-Datar 2002, Goodhart-Curcio 1991, Osler stop-cluster work to the extent it lives at round numbers, Schwartz Van Ness Van Ness clustering literature, gold market round-number work, intraday FX 00/50 mass studies, psychological-barrier momentum / mean-reversion contrasts.

**OUT of scope:** General **support/resistance / TA pattern recognition** → 07; **dealer-gamma magnetism at strike prices** → 12; **stop-loss cascades** as a microstructure mechanism → 06 / 07 split; **FX-fixing 4pm magnetism** → 08; round-number psychology as a human bias → 18.

---

## 2. Search strategy

### Keywords
- "psychological barriers" stock market round number
- "price clustering" foreign exchange Sopranzetti
- "round number effect" Donaldson Kim Dow Jones
- "00 ending" "50 ending" bid ask FX
- "limit order clustering" round price
- "Benford's law" stock prices clustering
- "psychological barriers" Asian European stock market
- "round number magnetism" intraday
- "support resistance" round number gold
- "5000 barrier" "10000 barrier" Dow market
- "quarter figure" FX clustering
- "00 level" forex
- "ghost level" trader

### Key journals
- *Journal of Financial Markets*
- *Journal of Banking and Finance*
- *Financial Review*
- *International Review of Financial Analysis*
- *Pacific-Basin Finance Journal*
- *Applied Economics*
- *Journal of Behavioral Finance*

### Repositories
- arXiv `q-fin.GN`, `q-fin.ST`
- SSRN Behavioral Finance eJournal
- CFA Institute research bulletins
- FMG LSE discussion papers
- Federal Reserve Board working papers

### Key authors
- Glen Donaldson, Harold Kim (Dow round numbers)
- Ben Sopranzetti, Vinay Datar (FX clustering)
- Charles Goodhart, Richard Curcio (FX bid/ask clustering)
- Carol Osler (stop-cluster / round-number FX)
- Lawrence Harris (price clustering grand-old-man)
- Robin Greenwood (psychological barriers — sometimes)
- Joachim Inkmann, Bernard Wong (psychological barrier studies)
- Jay Coughenour (clustering)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Stock Prices, Round Numbers and Closeness | Donaldson, Kim | 1993 | search Journal of Financial Quantitative Analysis 1993 — verify |
| 2 | Price clustering in foreign exchange spot markets | Sopranzetti, Datar | 2002 | Journal of Financial Markets 5(4):411-417 |
| 3 | The clustering of bid/ask prices and the spread in the foreign exchange market | Goodhart, Curcio | 1991 | http://eprints.lse.ac.uk/119186/ |
| 4 | On the hypothesis of psychological barriers in stock markets and Benford's Law | Ley, Varian | 1994 | https://www.sciencedirect.com/science/article/abs/pii/S0927539897000248 |
| 5 | Stop-Loss Orders and Price Cascades in Currency Markets | Osler | 2005 | search Journal of International Money and Finance — verify |
| 6 | Stock Price Clustering and Discreteness | Harris | 1991 | search Review of Financial Studies — verify |
| 7 | Psychological barriers in European stock markets: Where are they? | Bertola, Caporale | 2008 | https://www.sciencedirect.com/science/article/abs/pii/S1044028308000549 |
| 8 | Evidence of psychological barriers in the conditional moments of major world stock indices | Cyree, Domian, Louton, Yobaccio | 1999 | https://ideas.repec.org/a/wly/revfec/v8y1999i1p73-91.html |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Intraday price behavior of cryptocurrencies (round numbers) | Urquhart | 2017+ | https://www.sciencedirect.com/science/article/abs/pii/S1544612318302927 |
| 10 | Psychological barriers and option pricing in a local volatility model | various | 2022 | https://www.sciencedirect.com/science/article/abs/pii/S1062940822001991 |
| 11 | Psychological Barriers in Frontier Equities | various | 2016 | https://www.researchgate.net/publication/310810401 |
| 12 | Are there Psychological Barriers in Asian Stock Markets? | various | 2019 | https://www.researchgate.net/publication/335625037 |
| 13 | Psychological barriers in individual stocks in the United States | Li | thesis | https://thesis.eur.nl/pub/9479/9479-Li.pdf |
| 14 | Round-number effects in commodities (gold) | various | 2022-25 | search SSRN — verify |

---

## 5. GTOS subsystem connections

- **Component 2 (`market_state.py`)** — OB / FVG detection bias near round numbers; F12 / NAS100 hallucination root-cause analysis showed precision-rounding bugs near round-tick zones.
- **EURUSD / GBPUSD tight-FX overrides** — the FX-clustering literature directly motivates why 5-tick / 8-tick buffers are different per pair.
- **NAS100 + US30 round-number kill-zone interactions** — major round numbers (NAS 20000, US30 40000) are documented magnetic; calendar-feature-overfit risk in K54 must avoid ingesting these implicitly.
- **A4 trending_bull replay** — many trending_bull cohorts cluster around round-number breakouts; literature explains both directions of edge (continuation after break, mean-revert at level).
- **K54 v2 features** — distance-to-nearest-round-number as candidate feature; literature anchors why this should help.
- **Touch-count gate** — second touches at round-number levels behave differently from second touches at arbitrary levels.

---

## 6. Cross-domain handoff rules

- **Stop-loss-cascade microstructure** → 06 / 07.
- **Trader behavioral psychology** at round numbers → 18 (we keep the **price-data-evidence** papers).
- **OPEX strike-price magnetism in indices** → 08 / 12.
- **Multi-asset / cross-instrument round-number co-movement** → 13.
- **Volume profile at round-number levels** → 08.
- The bright line: ours is empirical evidence in the *price data* of round-number effects; downstream domains own the trading-rule, behavioral-explanation, or option-market interpretation.

---

## 7. Output spec

Files:
- `research/ml_program/literature/09_round_numbers_level_magnetism/papers.md`
- `research/ml_program/literature/09_round_numbers_level_magnetism/papers.csv`

Same schema. Special field: `level_granularity` — does the paper study big round (1000s, 100s), medium (50s, 25s), or fine (10s, 5s, half-dollar) level effects?

---

## 8. Quality bar / target

20-30 papers. **Justified lower bound:** the literature is finite and tightly clustered. Worker should NOT pad. Acceptable to come back with 18 strong papers if that exhausts the search; document in synthesis. Do search for cryptocurrency round-number papers (2017+) since these are recent and methodologically clean.
