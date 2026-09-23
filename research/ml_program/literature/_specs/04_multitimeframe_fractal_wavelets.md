# Domain 04 — Multi-Timeframe, Fractal, Wavelets & Hurst

**Slug:** `04_multitimeframe_fractal_wavelets`
**Owner:** Phase 1 Worker Agent #4
**Target paper count:** 30-45

---

## 1. Domain scope statement

This domain owns research on **time-scale decomposition** of price series and how information / dynamics differ across scales: wavelet analysis (CWT, DWT, MODWT, wavelet variance, wavelet coherence), Hurst-exponent / DFA / R-S analysis as time-series feature, multi-resolution analysis, multi-timeframe (MTF) trading models including HAR / MIDAS / mixed-frequency forecasting, fractal / monofractal vs multifractal classification of financial time series, intraday seasonality decomposition by wavelet, scale-dependent volatility / correlation, tick-vs-bar information aggregation.

**IN scope:** Gencay-Selcuk-Whitcher wavelet methodology, DFA / R-S Hurst estimation, HAR-RV (heterogeneous autoregressive) time-aggregation, MIDAS, intraday volatility patterns by wavelet, scale-by-scale Granger causality, fractal-dimension estimation as feature, multi-scale dependence.

**OUT of scope:** **Theoretical** fractional Brownian motion construction → 01; **distributional** moment scaling (multifractal-as-stylized-fact) → 03 with cross-link; high-frequency **microstructure** order-book scale phenomena → 06; ICT-style multi-timeframe **trading rules** based on H4/H1/M15 hierarchy → 07.

---

## 2. Search strategy

### Keywords
- "wavelet analysis" finance OR "wavelet transform" stock
- "Hurst exponent" financial time series
- "detrended fluctuation analysis" DFA returns
- "multi-resolution analysis" volatility
- "HAR-RV" heterogeneous autoregressive realized volatility Corsi
- "MIDAS" mixed-frequency forecasting Ghysels
- "wavelet coherence" co-movement markets
- "multi-timeframe" trading prediction
- "scale dependent" correlation finance
- "intraday seasonality" wavelet
- "rescaled range" R/S forex gold
- "fractional Brownian motion" estimator empirical
- "wavelet variance" financial scaling
- "multi-scale Granger causality" finance
- "MODWT" maximal overlap wavelet finance

### Key journals
- *Physica A*
- *Quantitative Finance*
- *Journal of Empirical Finance*
- *International Review of Financial Analysis*
- *Journal of Forecasting*
- *Computational Economics*
- *Studies in Nonlinear Dynamics & Econometrics*

### Repositories
- arXiv `q-fin.ST`, `physics.soc-ph`
- Bocconi/IGIER working papers (Corsi HAR)
- SSRN Forecasting eJournal
- Gencay personal page archives
- Whitcher Brandon github (waveslim package)

### Key authors
- Ramazan Gencay, Faruk Selcuk, Brandon Whitcher (wavelet / FX)
- Fulvio Corsi (HAR-RV)
- Eric Ghysels (MIDAS)
- Edgar E. Peters (popularization of fractal markets hypothesis — practitioner)
- Vince Vuilleumier, Jean-Francois Muzy (multifractal cascades)
- Donald Percival, Andrew Walden (wavelet textbook)
- Aldrich Aldrich (long-memory time series)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | An Introduction to Wavelets and Other Filtering Methods in Finance and Economics | Gencay, Selcuk, Whitcher | 2001 | book — Academic Press; reference text |
| 2 | Long-Term Storage Capacity of Reservoirs (R/S, Hurst) | Hurst | 1951 | https://ascelibrary.org/doi/10.1061/TACEAT.0006518 |
| 3 | A Simple Approximate Long-Memory Model of Realized Volatility (HAR-RV) | Corsi | 2009 | search SSRN — verify before use |
| 4 | The MIDAS Touch: Mixed Data Sampling Regression Models | Ghysels, Santa-Clara, Valkanov | 2004 | search SSRN — verify before use |
| 5 | Differentiating Intraday Seasonalities Through Wavelet Multi-Scaling | Gencay, Selcuk, Whitcher | 2001 | Physica A 289(3), 543-556 |
| 6 | Scaling Properties of Foreign Exchange Volatility | Gencay, Selcuk, Whitcher | 2001 | Physica A 289(1), 249-266 |
| 7 | A brief history of long memory: Hurst, Mandelbrot and the Road to ARFIMA | Graves, Gramacy, Watkins, Franzke | 2014 | https://arxiv.org/pdf/1406.6018 |
| 8 | Multifractal Detrended Fluctuation Analysis | Kantelhardt et al | 2002 | search Physica A — verify before use |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 9 | Long Memory and Fractality Among Global Equity Markets — Wavelet Approach | various | 2020 | https://link.springer.com/article/10.1007/s40953-020-00220-0 |
| 10 | Multivariate rescaled range analysis | Recent extension | 2021 | https://www.sciencedirect.com/science/article/abs/pii/S0378437121008815 |
| 11 | Rough volatility surveys (multifractality at small scales) | Bayer, Friz, Gatheral | 2018-2023 | seed candidate |
| 12 | Wavelet co-movement gold/USD/EUR/equities | search 2022-2024 | 2022-24 | search arXiv q-fin.ST |

---

## 5. GTOS subsystem connections

- **System operates on M15** — but markets-state.py reads H1, H4 OBs / FVGs / structure. Multi-timeframe consistency / leakage between scales is core to ICT methodology.
- **Tick-feature daemon (`tick_features.py`)** — bridges sub-M15 microstructure into M15 features; HAR-RV-style aggregation literature directly applicable.
- **K54 v2 features** — fractal/Hurst features (rolling Hurst on returns, DFA exponent) as candidate inputs.
- **Edge-decay diagnostics** (F11 OB-zone advantage decay velocity) — multi-scale regime decomposition could disambiguate: is decay a slow-scale (months) phenomenon, a faster regime shift, or scale-mixed?
- **Regime classifier** (`regime_classifier.py` H4-swing) — wavelet-based regime boundaries as alternative to swing-count.
- **Cross-instrument correlation matrix** — wavelet coherence as time-scale-aware alternative to Pearson rho.

---

## 6. Cross-domain handoff rules

- Pure **fractional Brownian motion theory** → 01.
- **Multifractal moments** treated as stylized fact → 03 with cross-link.
- **Order-book / tick microstructure scale phenomena** (e.g., Bouchaud's Hurst on order flow) → 06.
- **MTF trading rules** (HTF bias + LTF entry) → 07 (ICT/SMC academic adjacent).
- **Volatility-of-volatility / VIX scale** → 16.
- A paper that does Hurst-on-returns is ours; Hurst-on-order-flow is 06.

---

## 7. Output spec

Files:
- `research/ml_program/literature/04_multitimeframe_fractal_wavelets/papers.md`
- `research/ml_program/literature/04_multitimeframe_fractal_wavelets/papers.csv`

Same schema. Worker should explicitly note for each paper which timeframes it studied (sub-tick / tick / M1 / M5 / M15 / H1 / H4 / D1 / W1) — this maps directly to GTOS execution timeframe and informs multi-timeframe feature engineering.

---

## 8. Quality bar / target

30-45 papers. Smaller than methodology / distributional because the domain is more specialized. Aim for at least 5 papers explicitly on FX or commodity (gold) wavelet / multi-scale, since GTOS instruments concentrate there.
