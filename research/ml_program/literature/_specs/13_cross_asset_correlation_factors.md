# Domain 13 — Cross-Asset Correlation & Factor Exposures

**Slug:** `13_cross_asset_correlation_factors`
**Owner:** Phase 1 Worker Agent #13
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns research on **co-movement and shared risk factors** across markets and asset classes: contagion vs interdependence, time-varying correlations, regime-dependent correlations, factor models (Fama-French, Carhart, q-factor, mispricing factors), cross-asset value / momentum / carry, dollar / liquidity / safe-haven factors, AQR-style global factor zoo, factor rotation, asset-class diversification, copulas for cross-asset tail dependence, principal-component decompositions of cross-asset volatility, network / spillover analysis (Diebold-Yilmaz).

**IN scope:** Forbes-Rigobon contagion vs interdependence, Asness-Moskowitz-Pedersen value-and-momentum-everywhere, dynamic conditional correlation, BEKK-GARCH multivariate volatility, Diebold-Yilmaz spillover, equity-bond-FX-commodity factor models, Fama-French 3 / 5 / 6, Hou-Xue-Zhang q-factor, Stambaugh-Yuan mispricing.

**OUT of scope:** **Single-factor models** as theory → 01; **portfolio risk-aware sizing** under correlation → 21; **cross-instrument correlation as a trading-rule input** (specific to GTOS) → 07 cross-link; **rolling-correlation diagnostic** as time-series tool → 04 / 05; equity-cross-section anomaly mining → can be ours if shared with multiple asset classes, otherwise → 13 stays light.

---

## 2. Search strategy

### Keywords
- "no contagion" interdependence Forbes Rigobon
- "value momentum everywhere" Asness Moskowitz Pedersen
- "dynamic conditional correlation" Engle DCC
- "BEKK GARCH" multivariate volatility
- "Diebold Yilmaz" spillover network connectedness
- "factor zoo" Harvey Liu
- "q factor model" Hou Xue Zhang
- "five factor model" Fama French
- "carry trade" cross-asset Burnside
- "global factor" investment Lustig
- "equity bond correlation" regime
- "stock bond" hedging safe haven
- "copula" tail dependence cross-asset
- "principal component" yield curve
- "PCA" cross-sectional factor model
- "tail risk premium" factor

### Key journals
- *Journal of Finance*
- *Journal of Financial Economics*
- *Review of Financial Studies*
- *Journal of Portfolio Management*
- *Review of Asset Pricing Studies*
- *Journal of Financial and Quantitative Analysis*
- *Journal of Empirical Finance*
- *Critical Finance Review*

### Repositories
- arXiv `q-fin.PM` (portfolio management), `q-fin.ST`
- SSRN Capital Markets: Asset Pricing & Valuation
- NBER Asset Pricing
- AQR Capital Management research library
- Kenneth French data library
- Hou-Xue-Zhang q-factor data

### Key authors
- Cliff Asness, Tobias Moskowitz, Lasse Pedersen (factor cross-asset)
- Kristin Forbes, Roberto Rigobon (contagion)
- Eugene Fama, Kenneth French (factor models)
- Kewei Hou, Chen Xue, Lu Zhang (q-factor)
- Robert Stambaugh, Yu Yuan (mispricing)
- Robert Engle, Tim Bollerslev (multivariate vol — overlap)
- Francis X. Diebold, Kamil Yilmaz (spillover)
- Campbell Harvey, Yan Liu (factor zoo)
- John Cochrane (asset pricing review)
- Lasse Pedersen (cross-asset)
- Adrian, Etula, Muir (intermediary asset pricing)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Common Risk Factors in the Returns on Stocks and Bonds | Fama, French | 1993 | https://www.bauer.uh.edu/rsusmel/phd/Fama-French_JFE93.pdf |
| 2 | Value and Momentum Everywhere | Asness, Moskowitz, Pedersen | 2013 | https://elmwealth.com/wp-content/uploads/2017/06/valmomeverywhere_asness_moskowitz_and_pedersen__march_2008.pdf |
| 3 | No Contagion, Only Interdependence | Forbes, Rigobon | 2002 | https://www.nber.org/system/files/working_papers/w7267/w7267.pdf |
| 4 | Dynamic Conditional Correlation | Engle | 2002 | https://faculty.washington.edu/ezivot/econ589/EngleDCCJBES.pdf |
| 5 | A Five-Factor Asset Pricing Model | Fama, French | 2015 | search Journal of Financial Economics — verify |
| 6 | Digesting Anomalies: An Investment Approach (q-factor) | Hou, Xue, Zhang | 2015 | search RFS — verify |
| 7 | Better Than Beta: Mispricing Factors | Stambaugh, Yuan | 2017 | search SSRN — verify |
| 8 | Time Series Momentum | Moskowitz, Ooi, Pedersen | 2012 | https://fairmodel.econ.yale.edu/ec439/jpde.pdf |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Empirical Asset Pricing via Machine Learning | Gu, Kelly, Xiu | 2020 | https://academic.oup.com/rfs/article/33/5/2223/5758276 |
| 10 | The Factor Zoo and Bonferroni adjustment | Harvey, Liu | 2014-2024 | search Journal of Finance |
| 11 | Spillover and connectedness 2020-22 stress | Diebold, Yilmaz, recent | 2021-23 | search Journal of Econometrics |
| 12 | Factor instability across regimes 2020-25 | various | 2022-25 | search Critical Finance Review |
| 13 | Macro factor (intermediary asset pricing) | Adrian, Etula, Muir | 2020+ | search NBER |

---

## 5. GTOS subsystem connections

- **Cross-instrument correlation gate** — DCC, BEKK, copulas as alternatives to current static Pearson rho with thresholds. Memory note (`feedback_decision_preservation`): JPY_CROSSES rationale must be preserved; DCC gives a principled way to flag regime-shift in correlation.
- **Portfolio drawdown emergency stop** — factor decomposition of GTOS daily PnL identifies whether losses are factor-driven or instrument-specific.
- **K54 v2 features** — DXY, VIX, factor proxies (HML, MOM, carry FX) as candidate cross-asset features.
- **NAS_US30 specialist (Phase 2 plan)** — index-vs-FX-vs-gold factor exposure as fork-criterion.
- **F11 OB-zone advantage decay** — methodology question: is decay shared across all instruments (factor-driven) or instrument-specific (idiosyncratic)?
- **Project distributional findings** — fat-tail Hill xi=0.35 for gold may be factor-driven (real-rate / dollar) — cross-asset correlation literature underpins.

---

## 6. Cross-domain handoff rules

- **Single-asset distribution / GARCH** → 03.
- **Cross-asset volatility-of-volatility** → 16.
- **Theoretical no-arbitrage / SDF** → 01.
- **Factor *trading*** (long-short value / momentum portfolios) → 14 if momentum-focused, 15 if mean-reversion-focused.
- **Risk-management application of factors** → 21.
- **Macro central-bank effects on cross-asset** → 11.
- We keep the empirical / model-fitting work; downstream domains take the application.

---

## 7. Output spec

Files:
- `research/ml_program/literature/13_cross_asset_correlation_factors/papers.md`
- `research/ml_program/literature/13_cross_asset_correlation_factors/papers.csv`

Same schema. Special field: `asset_classes_covered` (FX / equity / bond / commodity / crypto / multi-class).

---

## 8. Quality bar / target

35-50 papers. Worker should ensure: ~10 factor models, ~8 dynamic / regime-dependent correlation, ~5 spillover / network, ~7 cross-asset value/momentum/carry, ~5 contagion / safe-haven, ~5 ML-based factor selection. At least 8 papers post-2020 to capture the post-COVID / post-tightening regime.
