# Domain 05 — Change-Point Detection & Regime Switching

**Slug:** `05_change_point_regime_switching`
**Owner:** Phase 1 Worker Agent #5
**Target paper count:** 35-50

---

## 1. Domain scope statement

This domain owns the literature on **detecting** structural breaks and **modeling** regime shifts in financial time series: Hamilton Markov-switching, threshold autoregression, smooth-transition models, hidden Markov models for asset returns, online change-point detection (Bayesian online change-point, ADWIN, BOCPD), CUSUM and Page-Hinkley, structural-break tests (Andrews, Bai-Perron), regime-conditional asset pricing, structural-VAR with regime, dynamic factor models with regime, time-varying parameter (TVP) models.

**IN scope:** Hamilton 1989 and successors, Markov regime-switching GARCH (MSGARCH), HMM volatility regimes, sticky vs adaptive regimes, RuLSIF, Page CUSUM as detector (cross-link to 02), Bayesian online change-point, neural change-point, evidence on regime persistence in FX / equities / commodities.

**OUT of scope:** **Theoretical** Markov processes / hidden Markov measure-theory → 01; **CUSUM as inference / sequential test** with controlled error rate → 02; **regime-aware portfolio construction** → 13 / 21; **regime-dependent prompt or rule** in trading rules → 17 (adaptive markets); **stochastic-volatility regime in option pricing** → 16.

---

## 2. Search strategy

### Keywords
- "Markov regime switching" Hamilton finance
- "MSGARCH" regime-switching GARCH
- "structural break" Bai Perron stock
- "hidden Markov model" volatility regime returns
- "Bayesian online change point detection" BOCPD finance
- "Page Hinkley" change point streaming
- "ADWIN" adaptive windowing concept drift
- "smooth transition autoregressive" STAR finance
- "threshold autoregressive" TAR Tong financial
- "regime dependent" risk premium asset pricing
- "time varying parameter" Bayesian TVP DSGE finance
- "concept drift" detection trading
- "online segmentation" financial time series
- "Andrews structural change" Quandt
- "regime conditional Sharpe" allocation

### Key journals
- *Journal of Econometrics*
- *Journal of Applied Econometrics*
- *Journal of Business and Economic Statistics*
- *Econometrica*
- *Quantitative Finance*
- *Studies in Nonlinear Dynamics & Econometrics*
- *Annals of Statistics*

### Repositories
- arXiv `q-fin.ST`, `econ.EM`, `stat.ME`
- NBER methodology
- SSRN Econometric Modeling: Capital Markets
- Hamilton homepage UCSD
- Bai personal page (Boston U) for structural-break work

### Key authors
- James D. Hamilton (regime-switching)
- Jushan Bai, Pierre Perron (structural breaks)
- Donald Andrews (structural-break inference)
- Allan Timmermann (regime / forecasting)
- Massimo Guidolin (regime-switching asset pricing)
- Donald W. K. Andrews
- Howell Tong (threshold AR)
- Siem Jan Koopman (state-space / TVP)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle | Hamilton | 1989 | https://users.ssc.wisc.edu/~behansen/718/Hamilton1989.pdf |
| 2 | Continuous Inspection Schemes (CUSUM) | Page | 1954 | https://academic.oup.com/biomet/article-abstract/41/1-2/100/456627 |
| 3 | Estimating and Testing Linear Models with Multiple Structural Changes | Bai, Perron | 1998 | search Econometrica 1998 — verify |
| 4 | Tests for Parameter Instability and Structural Change with Unknown Change Point | Andrews | 1993 | search Econometrica 1993 — verify |
| 5 | Threshold Autoregression and Some Frequency-Domain Methods (book/papers) | Tong | 1990 | Oxford Stat Sci |
| 6 | Bayesian Online Change Point Detection | Adams, MacKay | 2007 | https://arxiv.org/abs/0710.3742 (verify) |
| 7 | Regime Switching Models (Palgrave entry) | Hamilton | 2005 | https://econweb.ucsd.edu/~jhamilto/palgrav1.pdf |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 8 | State of cumulative sum sequential changepoint testing 70 years after Page | Biometrika review | 2024 | https://academic.oup.com/biomet/article-abstract/111/2/367/7486557 |
| 9 | Forecasting under structural breaks (Pesaran-Pick / Pesaran-Timmermann update) | Pesaran et al | 2020+ | search SSRN — verify |
| 10 | Bayesian regime detection in HFT | various | 2021-2024 | search arXiv q-fin.ST + change point |
| 11 | Deep change-point detection for time series | various | 2021+ | search arXiv stat.ML + change point |
| 12 | MSGARCH applications to crypto / commodities | various | 2023-25 | search ScienceDirect |

---

## 5. GTOS subsystem connections

- **F15 finding** — XAUUSD H1 78% bullish regime to H2 4.8% bullish regime is a regime *shift*, and the F15 synthesis is grounded in this domain. Detection methodology: BOCPD or Page-CUSUM on regime-classifier output.
- **Regime classifier** (`regime_classifier.py`) currently uses H4-swing 4-class; HMM and MSGARCH alternatives are direct candidates.
- **F10 / A5 verdict** — UNTAGGED 100% regime → 15.5% via shared structure_log_loader; bearish 84.6% (n=39) cell — the contrast is regime-dependent. Domain literature underpins testing whether differences are statistical regimes or finite-sample artifact.
- **K54 v2 regime-aware ML classifier** — Phase 2 rank #1 task; the regime-conditional asset-pricing literature is the literature anchor.
- **S1 monthly-decay shadow monitor** — change-point detection on rolling-50 OB continuation; if WR shifts > 5pp, alarm.
- **CUSUM candidate-rate daily monitor** — already in production, this domain's literature supports calibration.

---

## 6. Cross-domain handoff rules

- **Statistical-test machinery** for sequential testing (Wald, Robbins-Siegmund) → 02.
- **Theoretical Markov chains** measure-theoretic / ergodic → 01.
- **Distribution-fit-by-regime** stylized facts → 03.
- **Trading rules conditioned on detected regime** → 17 (adaptive markets) or 14 (trend / momentum).
- **Multi-asset / portfolio regime-dependent allocation** → 13 / 21.
- A paper that **detects** is ours; a paper that **trades on** the detection belongs in the trading-rule domain.

---

## 7. Output spec

Files:
- `research/ml_program/literature/05_change_point_regime_switching/papers.md`
- `research/ml_program/literature/05_change_point_regime_switching/papers.csv`

Same schema. Each paper should have an extra `online_or_offline` annotation: does the method support real-time detection (needed for live system), or is it offline-only?

---

## 8. Quality bar / target

35-50 papers. Worker must distinguish (a) detection methods (CUSUM, BOCPD, kernel CP), (b) regime-switching models (HMM, MSGARCH, MSAR), (c) structural-break inference (Andrews, Bai-Perron), and (d) financial regime evidence. Aim for at least 8 papers in each of (a)-(c) and 10 in (d).
