# Domain 03 — Distributional Characteristics & Tails

**Slug:** `03_distributional_characteristics`
**Owner:** Phase 1 Worker Agent #3
**Target paper count:** 40-55

---

## 1. Domain scope statement

This domain owns the empirical and theoretical study of asset-return distributions: heavy tails, power-law scaling, stable distributions, generalized hyperbolic / NIG / Variance Gamma families, EVT (POT, block-maxima, Hill estimator), volatility clustering as observed phenomenon, GARCH families and their stationary distributions, leverage effect, asymmetric tails, time-aggregation behavior, multifractal moment scaling, copulas for dependence (with link to factor / cross-asset where relevant).

**IN scope:** Cont stylized facts, Mandelbrot stable laws, Hill estimators, EVT-based VaR/ES, GARCH/EGARCH/GJR/FIGARCH/HAR-RV as descriptive models, fat-tail diagnostics, tail-index estimation, Pareto-stable distributions, scaling exponents.

**OUT of scope:** SDE / theory underneath stable processes → 01; **regime-switching dynamics** for distributions → 05; option-implied volatility surfaces / vol-of-vol → 16; multifractal **forecasting** application → 04; **statistical-test machinery** for tail comparison → 02 (when the methodology is the contribution; the empirical fit is ours); risk-based **position sizing** under fat tails → 21.

---

## 2. Search strategy

### Keywords
- "stylized facts" asset returns Cont
- "heavy tail" "power law" financial returns
- "extreme value theory" VaR financial
- "Hill estimator" tail index stocks
- "stable distribution" Pareto-Levy stocks gold
- "GARCH" "leverage effect" asymmetric volatility
- "FIGARCH" long memory volatility
- "HAR-RV" realized volatility heterogeneous
- "multifractal" "asset returns" moment scaling
- "fat tail" risk gold commodity
- "tail index" estimation finance
- "POT peaks over threshold" financial returns
- "skewness kurtosis" asset returns conditional
- "volatility clustering" empirical
- "generalized hyperbolic" NIG variance gamma returns

### Key journals
- *Quantitative Finance*
- *Journal of Empirical Finance*
- *Journal of Econometrics*
- *Physica A: Statistical Mechanics and its Applications*
- *Journal of Banking and Finance*
- *Mathematical Finance*
- *Review of Financial Studies* (when distributional)

### Repositories
- arXiv: `q-fin.ST`, `q-fin.RM`, `physics.soc-ph` (econophysics)
- SSRN Econophysics journal
- BIS working papers (extreme tails for risk)
- Bouchaud / CFM publication archive (`cfm.com/publications`)

### Key authors
- Rama Cont (stylized facts / theoretical)
- Benoit Mandelbrot (stable laws / multifractality)
- Jean-Philippe Bouchaud, Marc Potters (econophysics)
- Tim Bollerslev, Robert Engle (GARCH)
- Torben G. Andersen, Francis X. Diebold (realized volatility)
- Paul Embrechts, Claudia Klueppelberg (EVT)
- Eric Renault, Nour Meddahi (volatility processes)
- Adlai Fisher, Laurent Calvet (multifractal)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | The Variation of Certain Speculative Prices | Mandelbrot | 1963 | https://web.williams.edu/Mathematics/sjmiller/public_html/341Fa09/econ/Mandelbroit_VariationCertainSpeculativePrices.pdf |
| 2 | Empirical Properties of Asset Returns: Stylized Facts and Statistical Issues | Cont | 2001 | http://rama.cont.perso.math.cnrs.fr/pdf/empirical.pdf |
| 3 | Autoregressive Conditional Heteroscedasticity (ARCH) | Engle | 1982 | http://www.econ.uiuc.edu/~econ536/Papers/engle82.pdf |
| 4 | Generalized ARCH (GARCH) | Bollerslev | 1986 | https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf |
| 5 | Long-Term Storage Capacity of Reservoirs (R/S) | Hurst | 1951 | https://ascelibrary.org/doi/10.1061/TACEAT.0006518 |
| 6 | Modeling and Forecasting Realized Volatility | Andersen, Bollerslev, Diebold, Labys | 2003 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00418 |
| 7 | A Multifractal Model of Asset Returns | Mandelbrot, Fisher, Calvet | 1997 | https://users.math.yale.edu/~bbm3/web_pdfs/Cowles1164.pdf |
| 8 | Modelling Extremal Events for Insurance and Finance (book) | Embrechts, Klueppelberg, Mikosch | 1997 | Springer (textbook) |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Revisiting Cont's Stylized Facts for Modern Stock Markets | Vyetrenko et al (MITRE) | 2023 | https://arxiv.org/html/2311.07738v2 |
| 10 | Rough volatility: an overview | Bayer, Friz, Gatheral (review) | 2018-2023 | seed candidate — verify before use |
| 11 | High-frequency tail-risk estimation in FX | various | 2020+ | search arXiv q-fin.ST + Hill estimator + intraday |
| 12 | GARCH crude oil / commodity volatility | search recent applied | 2024-2025 | https://www.researchgate.net/publication/386889773 |

---

## 5. GTOS subsystem connections

- **GTOS distributional findings memory** (`project_distributional_findings`) — fat tail xi=0.35 for gold, GARCH persistence 0.9906, 6.2x more 3-sigma events than Gaussian; this domain is the literature anchor.
- **SL buffer calibration** (`risk.sl_buffer_atr_multiplier`) — tail-index-aware buffer sizing.
- **Heartbeat-flatten kill switch** — appropriate VaR/ES thresholds for catastrophe protection under fat tails.
- **Drawdown manager (H29)** — distribution of equity-curve drawdowns; first-passage under heavy tails.
- **Per-instrument profiles** — different tail-indices across XAU/EUR/JPY/indices warrant per-symbol risk parameters.
- **Cross-instrument correlation gate** — copula tail-dependence rather than Pearson rho for stress periods.
- **Validated Number K52 — XAUUSD WR vs breakeven** — distributional baseline for "what would WR look like under random returns?"

---

## 6. Cross-domain handoff rules

- A paper on **stochastic-volatility option pricing** that fits a Heston/SABR model → 16. We keep it if the contribution is the **physical-measure** distributional result, not pricing.
- **Order-flow long memory** (Lillo-Farmer) → 06 / 07; we keep the Hurst-exponent result if generalized to returns themselves.
- **Wavelet decomposition** for forecasting → 04. We keep multifractal **moment scaling** results.
- **EVT for portfolio risk / Kelly under fat tails** → 21 if the contribution is sizing; ours if the contribution is fitting.
- Multivariate copula for **factor / portfolio risk** → 13; ours if the focus is bivariate tail dependence as a stylized fact.

---

## 7. Output spec

Files:
- `research/ml_program/literature/03_distributional_characteristics/papers.md`
- `research/ml_program/literature/03_distributional_characteristics/papers.csv`

Same schema as domain 01.

Special annotation: every paper proposing a distribution / tail estimator should produce a `gtos_diagnostic` field — what diagnostic could GTOS run on its own data to check whether this distribution / scaling holds for XAU/USDJPY/etc.

---

## 8. Quality bar / target

40-55 papers. Strong literature. Worker should ensure coverage across (a) tails / EVT, (b) volatility clustering / GARCH families, (c) realized-volatility / high-frequency, (d) scaling / multifractal, (e) leverage / asymmetry — at least 5 papers in each cluster.
