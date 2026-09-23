# Domain 15 — Mean Reversion, Cointegration, Statistical Arbitrage

**Slug:** `15_mean_reversion_cointegration_statarb`
**Owner:** Phase 1 Worker Agent #15
**Target paper count:** 30-45

---

## 1. Domain scope statement

This domain owns the literature on mean-reverting strategies and stat-arb: pairs trading (Gatev-Goetzmann-Rouwenhorst), cointegration-based strategies (Engle-Granger, Johansen), Ornstein-Uhlenbeck models for spreads, ratio / spread mean-reversion, short-term reversal anomaly (Lehmann), index arbitrage, ETF-NAV arbitrage, fixed-income relative-value, FX cross-pair arbitrage, basket trading, market-neutral / dollar-neutral construction, half-life estimation, optimal trading bands.

**IN scope:** Engle-Granger 1987 in stat-arb context, Lehmann short-term reversal, Lo-Mackinlay variance ratio in mean-reversion framing, Avellaneda-Lee statistical arbitrage in US equities (PCA-residual pairs), Gatev-Goetzmann-Rouwenhorst pairs, half-life estimation under OU, Ornstein-Uhlenbeck calibration, deep-learning / RL pairs trading.

**OUT of scope:** **Trend / momentum** → 14; **arbitrage limits / capital constraints** → 17 / 22; **execution-cost-aware mean-reversion** → 06; **theoretical OU on filtered probability** → 01; **risk-management of pairs**  → 21.

---

## 2. Search strategy

### Keywords
- "pairs trading" Gatev Goetzmann Rouwenhorst
- "cointegration" Engle Granger pairs
- "Ornstein Uhlenbeck" half life calibration
- "statistical arbitrage" Avellaneda Lee
- "short term reversal" Lehmann week
- "mean reversion" half life half-life finance
- "spread" trading "Sharpe ratio" pairs
- "ETF arbitrage" NAV
- "index arbitrage"
- "fixed income relative value"
- "yield curve" spread butterfly trade
- "FX cross arbitrage" triangular
- "residual" PCA mean reversion
- "stationary spread" Johansen

### Key journals
- *Review of Financial Studies*
- *Journal of Finance*
- *Journal of Financial Economics*
- *Journal of Banking and Finance*
- *Quantitative Finance*
- *Journal of Portfolio Management*
- *Mathematical Finance*

### Repositories
- arXiv `q-fin.TR`, `q-fin.PM`
- SSRN Capital Markets
- AQR pairs / mean reversion library
- Hudson and Thames blog (practitioner)

### Key authors
- Evan Gatev, William Goetzmann, K. Geert Rouwenhorst (pairs)
- Marco Avellaneda, Jeong-Hyun Lee (stat-arb)
- Robert Engle, Clive Granger (cointegration)
- Soren Johansen (cointegration)
- Bruce Lehmann (short-term reversal)
- Andrew Lo, Craig MacKinlay (variance ratio overlap)
- Andrew Patton (cointegration)
- David Hsieh (relative value)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Pairs Trading: Performance of a Relative-Value Arbitrage Rule | Gatev, Goetzmann, Rouwenhorst | 2006 | search Review of Financial Studies — verify |
| 2 | Cointegration and Error Correction: Representation, Estimation, and Testing | Engle, Granger | 1987 | https://users.ssc.wisc.edu/~behansen/718/EngleGranger1987.pdf |
| 3 | Statistical Arbitrage in the U.S. Equities Market | Avellaneda, Lee | 2010 | search SSRN — verify |
| 4 | Fads, Martingales and Market Efficiency (short-term reversal) | Lehmann | 1990 | search Quarterly Journal of Economics — verify |
| 5 | Stock Market Prices Do Not Follow Random Walks | Lo, MacKinlay | 1988 | https://www-2.rotman.utoronto.ca/~kan/3032/pdf/PredictabilityOfReturns_ShortHorizon/Lo_MacKinlay_RFS_1988.pdf |
| 6 | Co-Integration and Likelihood Ratio Tests | Johansen | 1991 | search Econometrica 1991 — verify |
| 7 | Pairs Trading: Quantitative Methods and Analysis (book) | Vidyamurthy | 2004 | Wiley |
| 8 | Optimal Trading Strategies for Mean-Reverting Time Series | Bertram | 2010 | seed candidate — verify SSRN |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Deep learning for pairs trading | various | 2020-23 | search arXiv q-fin.TR pairs deep learning |
| 10 | RL for stat arb | various | 2021-24 | search arXiv q-fin.TR RL pairs |
| 11 | Crypto pairs / triangular arbitrage | various | 2021-24 | search arXiv |
| 12 | Cointegration-based trading on FX cross | various | 2022-24 | search SSRN |
| 13 | Pairs decay 2020-2024 | various | 2022-25 | search SSRN |

---

## 5. GTOS subsystem connections

- **GTOS plays mean-reversion within trend** — order block retest is a mean-reversion entry into a trend. The cointegration literature provides the theory.
- **Pairs / spread trading on cross-pairs** — XAUUSD vs XAGUSD silver-gold ratio; GBPUSD vs EURUSD vs GBPEUR triangular pricing — not currently in GTOS but candidates.
- **K54 v2 features** — half-life of recent rolling spread / recent residual on principal-component as candidate features.
- **Cross-instrument correlation gate** — when correlation breaks down, mean-reversion-style trades on the spread are technically exploitable; but GTOS's gate is for *risk*, not signal.
- **Risk gate inside trending regime** — half-life estimation determines holding-period assumptions.

---

## 6. Cross-domain handoff rules

- **Trend / momentum** → 14.
- **Limits-of-arbitrage capital constraints** → 17.
- **Optimal-execution within pairs** → 06.
- **Cross-asset factor structure** → 13.
- **Behavioral roots of mean-reversion** → 17.
- **OU theory** → 01.
- **Pairs trading as RL agent** → 20.

---

## 7. Output spec

Files:
- `research/ml_program/literature/15_mean_reversion_cointegration_statarb/papers.md`
- `research/ml_program/literature/15_mean_reversion_cointegration_statarb/papers.csv`

Same schema. Special field: `signal_horizon` (intraday / daily / weekly).

---

## 8. Quality bar / target

30-45 papers. Worker should split: ~10 pairs / cointegration foundational, ~5 short-term reversal, ~5 stat-arb / PCA-residual, ~5 ETF / index arb, ~5 FX-cross / commodity-cross stat-arb, ~5 ML / RL stat-arb. The empirical landscape post-2010 is heavily ML-flavored — capture that.
