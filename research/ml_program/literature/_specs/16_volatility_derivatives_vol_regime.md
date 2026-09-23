# Domain 16 — Volatility Trading, Derivatives, Vol Regime

**Slug:** `16_volatility_derivatives_vol_regime`
**Owner:** Phase 1 Worker Agent #16
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns research on **volatility as a tradeable / forecastable asset** and **derivative pricing as it interacts with cash-market dynamics**: option pricing models (Black-Scholes-Merton, Heston, SABR, rough-volatility), implied volatility surface, vol risk premium, variance swaps, volatility-of-volatility, VIX construction and trading, volatility regimes, leverage effect (price-volatility asymmetry), realized-vs-implied gaps, vol carry, options-implied skew / kurtosis, jump-diffusion, stochastic volatility for FX / commodities / equities, GARCH-vs-implied comparison.

**IN scope:** Black-Scholes-Merton 1973, Heston 1993, SABR (Hagan), rough-volatility (Bayer-Friz-Gatheral, Gatheral-Jaisson-Rosenbaum), Bakshi-Cao-Chen, vol risk premium estimation, VIX intraday / term-structure, variance-swap-based vol exposure, stochastic-volatility for FX (Heston-Nandi), GARCH / HAR implied-vs-realized.

**OUT of scope:** **Distributional GARCH / leverage effect** as descriptive tool → 03; **dealer-gamma flows in equity index** → 12 / 08; **volatility-targeted **portfolio sizing** → 21; **rough-path / signature theory** → 01; **vol regime *detection*** as change-point problem → 05.

---

## 2. Search strategy

### Keywords
- "Black Scholes" option pricing
- "Heston" stochastic volatility
- "SABR" Hagan implied volatility surface
- "rough volatility" Bayer Friz Gatheral
- "variance swap" volatility exposure
- "volatility risk premium" Bollerslev
- "VIX" term structure trading
- "implied volatility" "realized volatility" gap
- "skew" volatility smile
- "vol carry" trading
- "jump diffusion" Merton Kou
- "vol of vol" VVIX
- "variance risk premium"
- "implied skewness" Bakshi
- "volatility regime" detection
- "0DTE volatility" recent

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Journal of Derivatives*
- *Mathematical Finance*
- *Quantitative Finance*
- *Journal of Computational Finance*
- *Risk Magazine* (practitioner)
- *Wilmott Magazine* (practitioner)

### Repositories
- arXiv `q-fin.PR`, `q-fin.MF`, `q-fin.RM`
- SSRN Derivatives
- Ricardo Rebonato personal page
- Jim Gatheral homepage (Baruch College)
- CBOE research / VIX whitepapers

### Key authors
- Fischer Black, Myron Scholes, Robert Merton (foundational)
- Steven Heston (stochastic vol)
- Patrick Hagan (SABR)
- Jim Gatheral (volatility surface, rough vol)
- Tim Bollerslev (variance risk premium)
- Christian Bayer, Peter Friz (rough vol)
- Mathieu Rosenbaum (rough vol)
- Peter Carr (variance swaps)
- Liuren Wu (volatility surface)
- Robert Engle (GARCH overlap)
- Gurdip Bakshi, Charles Cao, Zhiwu Chen (option-implied skewness)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | The Pricing of Options and Corporate Liabilities | Black, Scholes | 1973 | https://www.cs.princeton.edu/courses/archive/fall09/cos323/papers/black_scholes73.pdf |
| 2 | A Closed-Form Solution for Options with Stochastic Volatility | Heston | 1993 | https://www.ma.imperial.ac.uk/~ajacquie/IC_Num_Methods/IC_Num_Methods_Docs/Literature/Heston.pdf |
| 3 | Managing Smile Risk (SABR) | Hagan, Kumar, Lesniewski, Woodward | 2002 | search Wilmott — verify |
| 4 | Volatility is Rough | Gatheral, Jaisson, Rosenbaum | 2018 | search Quantitative Finance — verify |
| 5 | What Good is a Volatility Model? | Engle, Patton | 2001 | https://web-static.stern.nyu.edu/rengle/EnglePattonQF.pdf |
| 6 | Risk and Volatility: Econometric Models and Financial Practice (Nobel lecture) | Engle | 2004 | https://www.aeaweb.org/articles?id=10.1257/0002828041464597 |
| 7 | Modeling and Forecasting Realized Volatility | Andersen, Bollerslev, Diebold, Labys | 2003 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00418 |
| 8 | Variance Risk Premia | Carr, Wu | 2009 | search Review of Financial Studies — verify |
| 9 | Empirical Performance of Alternative Option Pricing Models | Bakshi, Cao, Chen | 1997 | search Journal of Finance — verify |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 10 | Rough Volatility: An Overview | Bayer, Friz, Gatheral | 2018-2023 | seed candidate — verify SSRN |
| 11 | 0DTE Options and Vol Surface 2023-2024 | various | 2023-25 | search SSRN 0DTE |
| 12 | Volatility forecasting machine learning | various | 2020-24 | search arXiv q-fin.PR ML volatility |
| 13 | Path-dependent volatility models | Guyon, Lekeufack | 2022-24 | search arXiv |
| 14 | Variance risk premium 2020-2024 regime change | various | 2022-25 | search SSRN |

---

## 5. GTOS subsystem connections

- **ATR-based SL buffer** (`risk.sl_buffer_atr_multiplier`) — implicit volatility model is GARCH-of-ATR; literature offers stochastic-vol / rough-vol alternatives that may improve calibration during regime shifts.
- **K54 v2 features** — implied vs realized vol spread, VIX, skew, vol risk premium as candidate features.
- **Risk gate during high-vol regimes** — H29 DD-position-reduction triggers on realized DD; literature on vol clustering motivates volatility-aware position sizing.
- **Heartbeat-flatten** (live, item #1) — appropriate volatility threshold for catastrophe-protection trigger.
- **A4 trending_bull replay** — rough-volatility evidence for fast-mean-reverting vol-of-vol explains regime breakdowns.
- **Drawdown manager (H29)** — realized-vol-rolling-window for drawdown forecasting.
- **NFP / FOMC event handling** — vol-jump literature (Carr-Wu, Andersen-Bollerslev) directly informs event-window logic.

---

## 6. Cross-domain handoff rules

- **GARCH families as descriptive distribution / leverage effect** → 03 (we keep the option-pricing-implication side).
- **Realized-volatility long-memory** → 04 (we keep the price-of-vol side).
- **Vol regime *detection*** → 05 (we keep the trading-implication side).
- **Dealer-gamma feedback effects** → 12.
- **Risk management under vol regimes** → 21.
- **OPEX / 0DTE intraday flow** → 08 / 12 split.

---

## 7. Output spec

Files:
- `research/ml_program/literature/16_volatility_derivatives_vol_regime/papers.md`
- `research/ml_program/literature/16_volatility_derivatives_vol_regime/papers.csv`

Same schema. Special field: `model_type` (Black-Scholes / local-vol / Heston-stochastic / rough / GARCH / HAR / hybrid).

---

## 8. Quality bar / target

35-50 papers. Worker should split: ~10 stochastic-vol pricing, ~7 vol risk premium / VIX, ~5 rough vol (modern), ~5 realized-vol / HAR, ~5 implied-skew / smile, ~5 jump-diffusion, ~3 0DTE / recent regime. Aim for 6+ post-2020 papers (rough vol exploded).
