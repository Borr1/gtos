# Domain 08 — Volume, Auction Theory, VWAP, OPEX

**Slug:** `08_volume_auction_vwap_opex`
**Owner:** Phase 1 Worker Agent #8
**Target paper count:** 30-45

---

## 1. Domain scope statement

This domain owns the literature on **volume as information signal**, market-profile and auction-theoretic frameworks, VWAP-anchored trading and execution, options expiration (OPEX) and pinning effects on cash markets, dealer-gamma flows in index and stock markets that interact with cash settlement, end-of-day / open / close volume dynamics, fixing windows (London 4pm, Tokyo 3pm), seasonality of intraday volume and its predictive content.

**IN scope:** Karpoff volume-volatility relation, Steidlmayer market-profile / auction-market theory, VWAP execution research, Bollen-Whaley index-option net-buying-pressure, gamma-pinning OPEX studies (Ni, Pearson, Poteshman), end-of-day mechanical flows, FX fix studies (London 4pm Evans, Lyons; ESMA reports).

**OUT of scope:** **Order-book / market-making theory** → 06; **dealer-gamma in indices broader equity-index domain** → 12 (we keep the methodology, 12 keeps the asset-class specifics); **VPIN as toxicity** → 06; **volume profile as ICT trading rule** → 07.

---

## 2. Search strategy

### Keywords
- "volume volatility relation" Karpoff
- "VWAP" execution benchmark
- "market profile" Steidlmayer auction
- "OPEX" "options expiration" stock pinning
- "dealer gamma" index hedging flow
- "net buying pressure" implied volatility Bollen Whaley
- "London 4pm fix" FX manipulation
- "intraday volume seasonality" U-shape
- "auction market theory" range trading
- "open interest" futures predictive
- "GEX" "gamma exposure" SpotGamma
- "end of day flow" mechanical mutual fund
- "rebalance day" pension equity
- "month end FX flow" hedge ratio
- "fixing window" liquidity FX

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Journal of Financial Markets*
- *Journal of Banking and Finance*
- *Financial Analysts Journal*
- *Journal of Futures Markets*
- *Journal of Derivatives*

### Repositories
- arXiv `q-fin.TR`, `q-fin.PR`
- SSRN Capital Markets eJournal
- BIS quarterly review
- ECB working papers (FX fix manipulation)
- Federal Reserve regional working papers
- SpotGamma / SqueezeMetrics whitepapers (practitioner)

### Key authors
- Jonathan Karpoff (volume-volatility)
- Pete Steidlmayer (market profile - practitioner-classic)
- Robert Whaley (options markets)
- Nicholas Bollen (options expiration / IV)
- Sophie Ni, Neil Pearson, Allen Poteshman (option pinning)
- Andrea Barbon, Andrea Buraschi (gamma fragility)
- Ananth Madhavan (VWAP / execution)
- Robert Almgren (VWAP optimization)
- Charles-Albert Lehalle (VWAP literature)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | The Relation between Price Changes and Trading Volume: A Survey | Karpoff | 1987 | search Journal of Financial and Quantitative Analysis 1987 — verify |
| 2 | Does Net Buying Pressure Affect the Shape of Implied Volatility Functions? | Bollen, Whaley | 2004 | https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2004.00647.x |
| 3 | Stock Price Clustering on Option Expiration Days | Ni, Pearson, Poteshman | 2005 | search Journal of Financial Economics 2005 — verify |
| 4 | Gamma Fragility | Barbon, Buraschi | 2021 | https://www.abarbon.com/assets/Barbon_Buraschi_2021_Gamma_Fragility.pdf |
| 5 | Optimal Execution of Portfolio Transactions (VWAP context) | Almgren, Chriss | 2000 | https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf |
| 6 | Markets, Profile, and Method: a Trader's Theory | Steidlmayer | 1984+ | practitioner-classic |
| 7 | Trading Volume: Definitions, Data Analysis, and Implications of Portfolio Theory | Lo, Wang | 2000 | search Review of Financial Studies — verify |
| 8 | The Long Memory of Order Flow in the FX Spot Market | various | 2016 | https://people.maths.ox.ac.uk/porterm/papers/long-memory-published.pdf |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Where does gamma hedge drive the intraday market move? | recent AFA | 2024 | https://afajof.org/management/viewp.php?n=129472 |
| 10 | How Dealers' Gamma impacts underlying stocks (review) | BSIC | 2022 | https://bsic.it/how-dealers-gamma-impacts-underlying-stocks/ |
| 11 | OPEX pinning robustness post-2020 | various | 2022-25 | search arXiv q-fin.TR option pinning |
| 12 | London 4pm FX fix post-reforms | ECB / Reserve Bank Australia | 2021-24 | search ECB working papers |
| 13 | End-of-day rebalancing flow ETF / mutual fund | various | 2022-25 | search SSRN |

---

## 5. GTOS subsystem connections

- **NAS100 / US30 kill zones around 13:30 / 14:30 UTC** — OPEX / dealer-gamma flows directly inform why those windows are noisy (or magnetic) on the third Friday of each month.
- **Tick-feature daemon volume** — Karpoff volume-volatility framing motivates volume-imbalance features.
- **Cross-instrument correlation gate** — month-end / quarter-end fixing flows can break correlation gates spuriously; calendar-aware adjustment is a hypothesis target.
- **Best execution / slippage** — VWAP-anchored execution literature is the academic baseline for our market-orders-vs-limit-orders trade-off (`execution.py`).
- **A4 trending_bull replay finding** — many of the L2 sl_buffer 0.0 patterns occur near round-number / fixing-time clusters.
- **NAS100 hallucination** post-fix (HALLUC-1 root cause) — academic intuition: NAS100 mid-price near OPEX is harder to reason about precisely because dealer-gamma flows distort small ticks.

---

## 6. Cross-domain handoff rules

- **Pure microstructure / market-making** → 06.
- **Round-number psychological-barrier** clustering → 09 (we keep volume-clustering at fixing).
- **Equity-index gamma flow regime / behavior of options market itself** → 12.
- **Vol-of-vol pricing under gamma flow** → 16.
- **VWAP optimization with transaction-cost objective** → 06.
- We claim the **interaction between cash-market price and options-/futures-market-derived flow** as our specialty — the reverse is 12.

---

## 7. Output spec

Files:
- `research/ml_program/literature/08_volume_auction_vwap_opex/papers.md`
- `research/ml_program/literature/08_volume_auction_vwap_opex/papers.csv`

Same schema. Special field: `intraday_window` — does the paper isolate a specific intraday time window (open / mid / close / fix / OPEX day), since GTOS operates on kill-zone windows.

---

## 8. Quality bar / target

30-45 papers. Worker should pre-allocate ~10 papers to OPEX / dealer-gamma, ~10 to VWAP / execution, ~8 to volume-volatility / market-profile, ~5 to fixing windows, ~5 to seasonality / mechanical flows.
