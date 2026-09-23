# Domain 19 — AI/ML for Finance — Classical, Deep, Sequence Models

**Slug:** `19_ai_ml_for_finance_classical_deep_sequence`
**Owner:** Phase 1 Worker Agent #19
**Target paper count:** 50-65 (largest — see section 8)

---

## 1. Domain scope statement

This domain owns the application of machine-learning techniques to financial prediction and asset pricing (excluding RL / LLM-agents which live in 20): classical ML (random forests, gradient-boosted trees, SVMs, k-NN), deep learning for time series (CNN, LSTM, GRU, transformer, TCN), feature engineering / selection in finance, ML for asset pricing (Gu-Kelly-Xiu), graph / message-passing for financial networks, autoencoders for non-linear factor models, ML uncertainty quantification, ML interpretability (SHAP, LIME, counterfactual), federated learning in finance, time-series transformers (Time-LLM, Informer, Autoformer in finance contexts), Krauss-Do-Huck stat-arb-with-ML.

**IN scope:** Gu-Kelly-Xiu, Krauss-Do-Huck, deep-learning-LOB (Sirignano, Kondor), HAR-RV with ML, FinBERT for sentiment, text-as-data ML, gradient-boosted trees for return prediction, transformer time-series in finance, SHAP for asset pricing.

**OUT of scope:** **RL agents trading** → 20; **LLM-as-agent** for end-to-end trading → 20; **statistical-validation methodology** → 02 (we keep ML methodology on its own application terms); **theoretical learning theory** without finance application → drop; **classical anomaly detection** → 03 / 05.

---

## 2. Search strategy

### Keywords
- "machine learning" asset pricing Gu Kelly Xiu
- "deep learning" stock prediction
- "LSTM" stock price prediction
- "transformer" finance time series
- "gradient boosted trees" return prediction
- "random forest" trading signal
- "deep learning limit order book" Sirignano
- "FinBERT" financial sentiment
- "text as data" finance ML
- "machine learning factor zoo"
- "SHAP" feature importance asset pricing
- "graph neural network" financial network
- "autoencoder" non-linear factor model
- "uncertainty quantification" ML finance
- "TimeGPT" time series large model
- "Informer" Autoformer financial forecasting
- "machine learning anomaly" trading

### Key journals
- *Review of Financial Studies*
- *Journal of Finance* (occasional)
- *Journal of Financial Economics*
- *Journal of Empirical Finance*
- *Quantitative Finance*
- *European Journal of Operational Research*
- *Expert Systems with Applications*
- *Information Sciences*
- *Pattern Recognition*
- *Neural Networks*

### Repositories
- arXiv `q-fin.ST`, `q-fin.PR`, `q-fin.CP`, `cs.LG`, `stat.ML`
- SSRN AI/ML in Finance
- NBER Asset Pricing (ML papers)
- Bryan Kelly (Yale) personal page
- Justin Sirignano (Oxford) personal page
- Hudson and Thames blog
- AI4Finance Foundation github

### Key authors
- Shihao Gu, Bryan Kelly, Dacheng Xiu (ML asset pricing)
- Christopher Krauss, Nicolas Huck (deep learning stat arb)
- Justin Sirignano (LOB deep learning)
- Marcos Lopez de Prado (financial ML)
- Jakob Kondor, Imre Borovszki (LOB)
- Andrea Coletta (synthetic LOB / GAN)
- Stefan Zohren (Oxford, deep learning execution)
- Dogu Araci (FinBERT)
- Xiao-Yang Liu, Bryan Kelly (FinGPT cross-link)
- Stefano Pasquariello (financial ML)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Empirical Asset Pricing via Machine Learning | Gu, Kelly, Xiu | 2020 | https://academic.oup.com/rfs/article/33/5/2223/5758276 |
| 2 | Advances in Financial Machine Learning (book) | Lopez de Prado | 2018 | https://philpapers.org/rec/LPEAIF |
| 3 | Long Short-Term Memory | Hochreiter, Schmidhuber | 1997 | https://direct.mit.edu/neco/article/9/8/1735/6109/Long-Short-Term-Memory |
| 4 | Attention Is All You Need (transformer) | Vaswani et al | 2017 | https://arxiv.org/abs/1706.03762 |
| 5 | Deep Neural Networks, Gradient-Boosted Trees, Random Forests: Statistical Arbitrage on the S&P 500 | Krauss, Do, Huck | 2017 | https://www.econstor.eu/bitstream/10419/130166/1/856307327.pdf |
| 6 | FinBERT: Financial Sentiment Analysis with Pre-trained Language Models | Araci | 2019 | https://arxiv.org/abs/1908.10063 |
| 7 | Deep Learning for Limit Order Books | Sirignano | 2019 | search Quantitative Finance — verify |
| 8 | Universal features of price formation in financial markets | Sirignano, Cont | 2019 | search arXiv 1803.06917 — verify |
| 9 | Trees, Forests, Chickens, and Eggs: When and Why to Prune Random Forests | various | 2020s | seed candidate — verify |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 10 | Time-LLM: Time Series Forecasting via reprogramming | various | 2024 | https://proceedings.iclr.cc/paper_files/paper/2024/file/680b2a8135b9c71278a09cafb605869e-Paper-Conference.pdf |
| 11 | Stock Market Forecasting: Traditional to LLM | review | 2025 | https://link.springer.com/article/10.1007/s10614-025-11024-w |
| 12 | LLM-guided semantic feature selection for financial forecasting | recent | 2025 | https://www.sciencedirect.com/science/article/pii/S2773186325001471 |
| 13 | Temporal Data Meets LLM | various | 2023 | https://arxiv.org/abs/2306.11025 |
| 14 | Graph neural networks for asset pricing | various | 2022-25 | search arXiv |
| 15 | Conformal prediction in finance | various | 2022-25 | search arXiv |
| 16 | Deep Hedging with neural networks | Buehler, Gonon, Teichmann, Wood | 2019-22 | search arXiv q-fin.PR |
| 17 | Self-supervised representation learning for financial time series | various | 2023-25 | search arXiv |
| 18 | Machine learning portfolio construction post-2020 | various | 2022-25 | search SSRN |

---

## 5. GTOS subsystem connections

- **K54 v2 ML classifier** (Phase 2 rank #1, `project_k54_ml_classifier_baseline_2026-04-27`) — domain 19 is the literature anchor. Worker must produce papers directly applicable to per-regime LightGBM successor architecture.
- **K54 v1 audit** (`research/ml_program/k54_v1_audit.md`) — methodology for the next iteration.
- **F5 — K51 does NOT replicate under proper SHAP + Bonferroni** — literature on proper feature-importance discipline.
- **F16 — displacement_quality_score decay does not replicate at n=240** — literature on small-sample SHAP / boosted-tree variance.
- **Track A anti-pattern classifier OOS failure** (item #7) — literature on robust OOS evaluation.
- **Time-series transformer / LSTM** as alternative to LightGBM for K54 v2.
- **Sirignano-Cont LOB-deep-learning** could inspire features when MT5 tick-level depth becomes available.
- **HALLUC-1 / B7 hallucination** — distinguishing perception failures vs precision bugs cross-links to ML interpretability.

---

## 6. Cross-domain handoff rules

- **RL agent that takes trading actions** → 20.
- **LLM as end-to-end trader** → 20.
- **LLM-extracted features** → ours if used as ML features; → 20 if the LLM is the agent.
- **Validation methodology (CPCV, deflated Sharpe)** → 02.
- **Distributional / GARCH ML** → 03 / 16 split depending on focus.
- **Cross-asset factor ML** → 13.
- **Regime-detection ML** → 05.

---

## 7. Output spec

Files:
- `research/ml_program/literature/19_ai_ml_for_finance_classical_deep_sequence/papers.md`
- `research/ml_program/literature/19_ai_ml_for_finance_classical_deep_sequence/papers.csv`

Same schema. Special fields: `model_class` (linear/tree/SVM/CNN/LSTM/Transformer/GNN/AE/hybrid), `data_input` (price-only / OHLCV / OHLCV+text / orderbook / multi-modal), `prediction_horizon`.

---

## 8. Quality bar / target

50-65 papers. **Justified upper bound:** financial ML is the largest and fastest-moving sub-literature. Worker should explicitly cover (a) classical: RF, GBM, SVM (~10 papers), (b) deep sequence: LSTM, GRU, TCN (~10), (c) transformer / time-series large models (~10), (d) ML asset pricing / Gu-Kelly-Xiu followers (~8), (e) text-data / FinBERT / language (~6), (f) interpretability / SHAP / counterfactual (~5), (g) ML for LOB / microstructure (~5), (h) recent self-supervised / graph / hybrid (~5+). At least 12 post-2022 to capture transformer-era.
