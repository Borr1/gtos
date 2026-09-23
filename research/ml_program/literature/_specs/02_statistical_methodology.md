# Domain 02 — Statistical Methodology & Validation in Finance

**Slug:** `02_statistical_methodology`
**Owner:** Phase 1 Worker Agent #2
**Target paper count:** 40-60

---

## 1. Domain scope statement

This domain owns statistical validation methodology for trading-system claims: backtest design, multiple-testing correction, deflated metrics, walk-forward / cross-validation schemes that respect time-series dependence, p-hacking diagnostics, sequential testing (SPRT), CUSUM, false-discovery-rate control, Bayesian posterior calibration, bootstrap inference for non-iid data, and predictive-accuracy comparison. The domain also covers in-sample / out-of-sample protocols, look-ahead and survivorship bias, and the Reality Check / Superior Predictive Ability literature.

**IN scope:** Diebold-Mariano, Hansen SPA, Lopez de Prado CPCV / triple barrier / meta-labeling, deflated Sharpe, FDR (Benjamini-Hochberg, Romano-Wolf), Bayesian model selection in finance, t-stat haircut for selection, encompassing tests, Mincer-Zarnowitz, RBC for forecast comparison.

**OUT of scope:** specific time-series **models** (ARIMA, GARCH application) → 03/16; specific ML **architectures** → 19/20; **theory of stochastic processes** → 01; **distributional fitting / extreme-value inference** → 03; substantive **finding** papers (e.g., predictability of equity premium) belong here only when the methodological angle dominates; otherwise → relevant content domain.

---

## 2. Search strategy

### Keywords
- "deflated Sharpe ratio" OR "Bailey Lopez de Prado"
- "combinatorial purged cross validation" finance
- "triple barrier" "meta labeling" Lopez de Prado
- "data snooping" "reality check" White Hansen
- "false discovery rate" finance trading
- "Diebold Mariano" forecast accuracy
- "Romano Wolf" stepwise multiple testing
- "backtest overfitting" probability
- "selection bias" haircut t-statistic Harvey
- "walk forward" optimization trading
- "expanding window" "rolling window" forecasting
- "SPRT" sequential probability ratio test trading
- "CUSUM" change-point detection finance
- "Sharpe ratio confidence interval" bootstrap
- "encompassing test" forecast
- "bootstrap" non-iid time series finance

### Key journals
- *Journal of Business and Economic Statistics*
- *Journal of Forecasting*
- *International Journal of Forecasting*
- *Journal of Empirical Finance*
- *Journal of Financial Econometrics*
- *Journal of Portfolio Management*
- *Review of Asset Pricing Studies*
- *Quantitative Finance*

### Repositories
- arXiv: `q-fin.ST` (statistical finance), `stat.AP`, `stat.ME`, `econ.EM`
- SSRN Econometrics: Mathematical Methods & Programming eJournal
- NBER Methodology working papers
- David Bailey / Lopez de Prado personal page (`davidhbailey.com`, `quantresearch.org`)
- Hudson and Thames blog (practitioner CPCV)

### Key authors
- Marcos Lopez de Prado, David H. Bailey, Jonathan Borwein (overfitting trio)
- Halbert White, Peter Hansen (reality check / SPA)
- Francis X. Diebold, Roberto Mariano (forecast comparison)
- Joseph Romano, Michael Wolf (multiple testing)
- Campbell Harvey, Yan Liu (t-stat haircut, *and the cross-section of expected returns*)
- Andrew Patton (forecast evaluation)
- Allan Timmermann (forecasting in finance)
- Yacine Ait-Sahalia (high-frequency inference)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Comparing Predictive Accuracy | Diebold, Mariano | 1995 | https://www.tandfonline.com/doi/abs/10.1080/07350015.1995.10524599 |
| 2 | A Reality Check for Data Snooping | White | 2000 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00152 |
| 3 | A Test for Superior Predictive Ability | Hansen | 2005 | search SSRN: hansen+spa — verify before use |
| 4 | Continuous Inspection Schemes (CUSUM) | Page | 1954 | https://academic.oup.com/biomet/article-abstract/41/1-2/100/456627 |
| 5 | Stock Market Prices Do Not Follow Random Walks (variance ratio) | Lo, MacKinlay | 1988 | https://www-2.rotman.utoronto.ca/~kan/3032/pdf/PredictabilityOfReturns_ShortHorizon/Lo_MacKinlay_RFS_1988.pdf |
| 6 | Predictability of Stock Returns: Robustness and Economic Significance | Pesaran, Timmermann | 1995 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1995.tb04055.x |
| 7 | A Comprehensive Look at the Empirical Performance of Equity Premium Prediction | Goyal, Welch | 2008 | https://www.ivo-welch.info/research/journalcopy/2008-rfs.pdf |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 8 | Advances in Financial Machine Learning (book ch.7-12) | Lopez de Prado | 2018 | https://philpapers.org/rec/LPEAIF |
| 9 | The Deflated Sharpe Ratio | Bailey, Lopez de Prado | 2014 | https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf |
| 10 | ...and the Cross-Section of Expected Returns | Harvey, Liu, Zhu | 2016 | seed candidate — verify before use |
| 11 | Backtesting | Lopez de Prado, Lipton | 2024 | seed candidate — search SSRN — verify |
| 12 | Combinatorial Purged Cross-Validation Method | Lopez de Prado / followers | 2018+ | https://towardsai.net/p/l/the-combinatorial-purged-cross-validation-method |
| 13 | A Comprehensive 2022 Look at Equity Premium Prediction | Goyal, Welch, Zafirov | 2022 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3929119 |

---

## 5. GTOS subsystem connections

- **K54 v2 ML pipeline validation** — must use CPCV, not naive k-fold; paper-corpus is the methodological reference.
- **Per-instrument SPRT halt rules** (currently active for XAUUSD LONG-WR-watch) — directly in scope.
- **CUSUM candidate-rate monitor** (`shadow_logs/cusum_candidate_rate_daily.csv`) — methodology grounding.
- **Walk-level vs realized-R discipline** (memory `feedback_walk_level_evidence_not_predictive`) — needs Diebold-Mariano-style joint comparison framing.
- **Validated Numbers maintenance** (K52 re-test) — Bonferroni / Romano-Wolf for the 5 confirmed metrics.
- **Pre-registered hypothesis backlog** (`research/ml_program/PRE_REGISTERED_HYPOTHESES.md`) — survivorship of pre-registered effects vs post-hoc selections.

---

## 6. Cross-domain handoff rules

- Empirical paper that **applies** a method (e.g., Pesaran-Timmermann) is *ours* if its dominant contribution is methodological (recursive forecasting) — content (predictability) gets a cross-link to the relevant domain.
- "Equity premium prediction" content paper goes to domain 13 (factor exposures) or 14 (momentum) only if methodology is incidental.
- ML cross-validation papers in **non-finance** context → keep in domain 19 unless they explicitly address financial-time-series leakage.
- Distributional fitting / EVT / GARCH inference → 03.
- Bayesian model averaging is shared with 19; ours when the application is forecast-comparison or backtesting.

---

## 7. Output spec

Files:
- `research/ml_program/literature/02_statistical_methodology/papers.md`
- `research/ml_program/literature/02_statistical_methodology/papers.csv`

Schema same as domain 01 (id / title / authors / year / source / url / abstract / key_findings / relevance_to_gtos / potential_hypothesis / cross_domain_links).

Worker should annotate each paper with whether it suggests a **specific test** GTOS could run (e.g., "Romano-Wolf step-down on the 47 SPRT-tested instrument-side cells" yields a concrete pre-registrable check).

---

## 8. Quality bar / target

40-60 papers. The methodological literature on backtesting and forecasting is dense; the worker should aim for breadth (cover SPRT, CUSUM, FDR, CV, deflation, encompassing) rather than 30 papers all on Sharpe-ratio variants. Reject any paper without a directly applicable GTOS hypothesis.
