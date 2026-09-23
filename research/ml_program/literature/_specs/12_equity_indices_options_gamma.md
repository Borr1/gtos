# Domain 12 — Equity Indices, Options, Gamma Flow

**Slug:** `12_equity_indices_options_gamma`
**Owner:** Phase 1 Worker Agent #12
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns equity-index research relevant to **NAS100 / US30 / S&P 500** trading: index-level stylized facts, dealer-gamma exposure (GEX) and intraday momentum / mean reversion driven by it, options-flow effects on cash markets, OPEX pinning, VIX dynamics, vol risk premium, leverage effect on indices, intraday seasonality of S&P / NDX / DJI, post-FOMC index reactions, sector-rotation interactions, ETF-vs-index basis, mini-futures liquidity dynamics.

**IN scope:** Bollen-Whaley index option net-buying-pressure, Barbon-Buraschi gamma-fragility, Ni-Pearson-Poteshman OPEX pinning, ETF arbitrage research, Garleanu-Pedersen-Poteshman demand-based-option-pricing, Cheng intraday momentum, Lou-Polk-Skouras (asset growth → return), event-day indices behavior.

**OUT of scope:** **Volatility surface / SABR / Heston** as pricing model → 16; **OPEX volume / VWAP general framework** → 08 (we keep equity-index-OPEX specifically); **factor models / cross-section** → 13; **VIX-for-trading vol** → 16.

---

## 2. Search strategy

### Keywords
- "dealer gamma" S&P SPX hedging flow
- "net buying pressure" index options Bollen Whaley
- "OPEX pinning" stock SPY
- "GEX" "gamma exposure" intraday
- "VIX term structure" front month
- "index ETF" arbitrage SPY QQQ
- "demand based option pricing" Garleanu Pedersen Poteshman
- "intraday momentum" NASDAQ FOMC
- "post-earnings drift" index PEAD
- "sector rotation" index option
- "0DTE" 0-day-to-expiry options
- "implied volatility surface" SPX
- "skew" puts protective demand
- "minor index" US30 DJX
- "Russell 2000" small cap

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Journal of Derivatives*
- *Journal of Futures Markets*
- *Management Science*
- *Financial Analysts Journal*

### Repositories
- arXiv `q-fin.PR`, `q-fin.TR`
- SSRN Derivatives eJournal
- NBER Asset Pricing
- CBOE research
- SpotGamma / SqueezeMetrics whitepapers

### Key authors
- Robert Whaley, Nicholas Bollen (options markets)
- Andrea Barbon, Andrea Buraschi (gamma fragility)
- Sophie Ni, Neil Pearson, Allen Poteshman (pinning)
- Nicolae Garleanu, Lasse Pedersen, Allen Poteshman (option demand)
- Robin Greenwood (ETF arbitrage)
- Roberto Pancrazi, Klaus Peter (VIX term-structure)
- Lily Liu (recent VIX work)
- Tobias Adrian (vol risk premia)
- Charles Cao (vol)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Does Net Buying Pressure Affect the Shape of Implied Volatility Functions? | Bollen, Whaley | 2004 | https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2004.00647.x |
| 2 | Demand-Based Option Pricing | Garleanu, Pedersen, Poteshman | 2009 | search Review of Financial Studies — verify |
| 3 | Stock Price Clustering on Option Expiration Days | Ni, Pearson, Poteshman | 2005 | search Journal of Financial Economics — verify |
| 4 | Gamma Fragility | Barbon, Buraschi | 2021 | https://www.abarbon.com/assets/Barbon_Buraschi_2021_Gamma_Fragility.pdf |
| 5 | A New Approach to Measuring Financial Contagion | Forbes, Rigobon | 2002 | search Journal of Finance — verify |
| 6 | Why Stock Markets Crash (book) | Sornette | 2003 | https://press.princeton.edu/books/paperback/9780691175959/why-stock-markets-crash |
| 7 | Hedge Funds and the Technology Bubble | Brunnermeier, Nagel | 2004 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00690.x |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 8 | Where does gamma hedge drive the intraday market move? | recent AFA | 2024 | https://afajof.org/management/viewp.php?n=129472 |
| 9 | 0DTE option growth effects on SPX intraday | various | 2023-24 | search SSRN 0DTE |
| 10 | How Dealers' Gamma impacts underlying stocks | BSIC review | 2022 | https://bsic.it/how-dealers-gamma-impacts-underlying-stocks/ |
| 11 | NDX vs SPX divergence post-2020 mega-cap concentration | various | 2022-25 | search SSRN |
| 12 | VIX term-structure regimes 2020-2024 | various | 2023-24 | search Journal of Derivatives |
| 13 | Market liquidity 2022 fed-tightening regime | various | 2023 | search SSRN |

---

## 5. GTOS subsystem connections

- **NAS100 (3-day observe mode)** — dealer-gamma literature highly relevant; HALLUC-1 root-cause was rounding, but trading-edge literature for NAS100 must check OPEX-day / GEX flips before signing off on specs.
- **US30** — DJI-specific gamma flow, fewer 0DTE products, structurally different from SPX/NDX.
- **F9 — US30 hallucination decomposed** — 40% TP artifact + 14% real; literature on dense-price-grid behavior of indices grounds the artifact / real decomposition.
- **K54 v2 features** — VIX, GEX, term-structure slope, put-call ratio as candidate features (must be available historically for backfill).
- **NAS_US30 specialist hypothesis** — Q1.4 plan reset envisions a per-instrument routed model; index-specific literature is the input.
- **Cross-instrument correlation gate** — NAS100 vs US30 typically high-correlated except at sector-rotation events; literature underpins regime-aware correlation.
- **Risk gate at FOMC / CPI** — index-event-day reactions literature.

---

## 6. Cross-domain handoff rules

- **Cross-section equity factor anomalies** (size, value, momentum on individual stocks) → 13.
- **Equity index option-implied **volatility-trading** strategies** → 16.
- **Equity intraday volume / VWAP general** → 08 (we keep index-OPEX-specific gamma flows).
- **Macro central-bank surprise on indices** → 11 (we keep the index-side reaction; 11 keeps the policy framing).
- **Industry / sector rotation** → 13.
- **Quantum / hedge fund S&P alpha strategies** → 22.

---

## 7. Output spec

Files:
- `research/ml_program/literature/12_equity_indices_options_gamma/papers.md`
- `research/ml_program/literature/12_equity_indices_options_gamma/papers.csv`

Same schema. Special field: `index_studied` (SPX / NDX / DJI / RUT / VIX / multi).

---

## 8. Quality bar / target

35-50 papers. Aim for ~12 dealer-gamma / OPEX, ~10 VIX / vol-risk-premium, ~8 intraday momentum / mean-reversion, ~5 0DTE-era specific, ~5 ETF arbitrage / index-construction. Pre-2020 dominated by SPX; post-2020 must capture NDX / 0DTE / 2022-tightening regime.
