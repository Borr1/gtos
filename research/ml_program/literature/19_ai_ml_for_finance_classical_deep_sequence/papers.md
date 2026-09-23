# Domain 19 — AI/ML for Finance — Classical, Deep, Sequence Models

**Worker:** Phase 1 Literature Worker #19
**Date:** 2026-04-28
**Papers cataloged:** 78
**Spec source:** `research/ml_program/literature/_specs/19_ai_ml_for_finance_classical_deep_sequence.md`

---

## Section 1 — Domain scope (covered + deferred)

### Covered
- ML asset pricing (Gu-Kelly-Xiu 2020 line) and follow-up debates: tree/NN vs linear, factor zoo with ML, autoencoder factor models.
- Statistical arbitrage with classical and deep ML: Krauss-Do-Huck (2017) RF/GBM/DNN; later memory / LSTM extensions (Fischer-Krauss 2018).
- Foundational sequence models: LSTM (Hochreiter-Schmidhuber 1997), GRU (Cho et al 2014), Transformer (Vaswani et al 2017), TCN (Bai-Kolter-Koltun 2018).
- Time-series transformers and large-time-series models: Informer, Autoformer, FEDformer, PatchTST, TimesNet, iTransformer, Time-LLM, TimeGPT, MOIRAI, Lag-Llama.
- Deep learning for limit order books / microstructure: Sirignano (DLOB), Sirignano-Cont (universal features), DeepLOB (Zhang-Zohren-Roberts), microstructure-feature CNN/LSTM hybrids.
- Financial text-as-data: FinBERT (Araci 2019), FinBERT (Yang et al 2020), Loughran-McDonald lexicon as ML feature anchor, finance LLM-feature distillation papers.
- Interpretability for ML in finance: SHAP (Lundberg-Lee 2017), TreeSHAP (Lundberg et al 2020), LIME (Ribeiro 2016), counterfactual explanations.
- Methodology / practitioner books and ML-discipline papers: Lopez de Prado *Advances in Financial Machine Learning* (2018) and *Machine Learning for Asset Managers* (2020), CPCV / fractional differentiation / meta-labeling.
- Deep hedging and ML for risk: Buehler-Gonon-Teichmann-Wood (2019); Han-Jentzen-E (2018) deep BSDE.
- Self-supervised / representation learning / GANs / diffusion for finance.
- Graph neural networks for asset pricing and inter-asset relationships.
- Conformal prediction / calibration for finance.
- Contrarian / cautionary findings: Welch-Goyal (2008) classical equity-premium baseline, Bailey-Lopez de Prado backtest overfitting, Israel-Kelly-Moskowitz "machine learning is over-rated" debate.

### Deferred (cross-linked)
- RL agents that take trading actions → **domain 20** (FinRL, Deep Hedging if framed as RL).
- LLM-as-end-to-end-trader → **domain 20** (FinGPT-Agent, BloombergGPT-as-trader).
- LLM-extracted features used as ML features → ours (e.g., FinBERT, sentiment encoders), but LLM-as-decision-maker → 20.
- Statistical-validation methodology details (deflated Sharpe, CPCV, false-strategy theorem) → **domain 02**; Lopez de Prado entries here only at applied-architecture level.
- Pure GARCH / distributional ML → **domain 03 / 16**.
- Cross-asset factor ML → **domain 13** (anchored cross-flag here).
- Regime-detection ML → **domain 05** (anchored cross-flag here).
- HAR-RV pure model → **domain 16**; ML-augmented HAR cataloged here.

---

## Section 2 — Foundational papers

### Empirical Asset Pricing via Machine Learning
- **Authors:** Shihao Gu, Bryan Kelly, Dacheng Xiu
- **Year/Source:** 2020 / Review of Financial Studies 33(5): 2223-2273 (NBER WP 25398, 2018)
- **URL:** https://academic.oup.com/rfs/article/33/5/2223/5758276 ; https://www.nber.org/papers/w25398 ; https://dachxiu.chicagobooth.edu/download/ML.pdf
- **Abstract:** Comparative analysis of a large suite of machine-learning methods (OLS, PCR, PLS, elastic net, random forest, gradient-boosted trees, neural networks) for measuring asset risk premia using ~94 firm characteristics + 8 macro signals on monthly U.S. equity returns 1957-2016. Tree ensembles and shallow neural networks deliver the largest out-of-sample R² gains and roughly double the Sharpe of the best linear regression-based strategy.
- **Key findings:**
  - Trees and neural nets dominate linear methods because of nonlinear predictor interactions; the marginal R² of nonlinearity is large in absolute terms but small in % of return variance.
  - All methods agree on a small dominant feature set: short-term reversal, momentum (12-1 and 6-1), industry momentum, idiosyncratic volatility, illiquidity, accruals, and a handful of valuation signals.
  - A long-short equally-weighted decile strategy on ML-forecasted returns delivers monthly Sharpe ~2.5 vs ~1.4 for OLS+H benchmark.
  - Shallow nets (NN3 with 32-16-8 hidden units) beat deeper ones — overfitting risk dominates representational gains for monthly equity panels.
  - Variable-importance computed via partial-derivative / sum-of-squared-sensitivities is highly stable across methods, suggesting a robust feature ranking under multiple inductive biases.
- **Relevance to GTOS:** The literature anchor for K54 v2 architecture choice. Replicates the GTOS K54-baseline finding that shallow tree ensembles + tight regularization beat deep networks at small to medium n; supports per-regime LightGBM as the right v2 architecture rather than a transformer. The "all methods agree on dominant signals" result motivates K54 v2 SHAP-stability test before promotion. The monthly horizon is much longer than GTOS H1, but the relative-rank conclusions about RF/GBM vs NN are widely replicated at higher frequencies.
- **Potential hypothesis:** On the GTOS H1 panel (~7 instruments × ~24 months × ~96 candles/day), a 3-layer fully-connected NN does *not* beat per-regime LightGBM at OOS R², because the ratio of free parameters to non-redundant-bar count is similar to Gu-Kelly-Xiu's setting where shallow trees won.
- **Cross-domain flag:** 13 (cross-asset factor ML); 02 (proper-OOS protocol)

### Advances in Financial Machine Learning (book)
- **Authors:** Marcos Lopez de Prado
- **Year/Source:** 2018 / Wiley (book; 22 chapters)
- **URL:** https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086 ; https://philpapers.org/rec/LPEAIF
- **Abstract:** A practitioner's blueprint for applying ML to financial-time-series problems while controlling for the well-documented pitfalls (non-IID structure, label leakage, multiple-testing, illusory backtests). Introduces purged-CPCV, fractional differentiation, meta-labeling, and the deflated Sharpe ratio.
- **Key findings:**
  - Standard time-series cross-validation leaks information through label overlap; combinatorial purged cross-validation (CPCV) with embargo gives unbiased OOS estimates.
  - Fractional differentiation preserves memory while making the series stationary — superior to first-differencing as ML input.
  - Meta-labeling: train a primary model for direction, train a secondary classifier on whether to take the trade (size 0/1), separating signal from sizing improves Sharpe.
  - Triple-barrier labeling (upper-barrier, lower-barrier, vertical-barrier) is more aligned with risk-managed trade outcomes than fixed-horizon returns.
  - Backtest overfitting is a dominant failure mode: the deflated Sharpe ratio adjusts the headline Sharpe for the number of trials run.
- **Relevance to GTOS:** Direct architecture blueprint for K54 v2. The triple-barrier label (TP/SL/time-stop) is exactly GTOS's J46-J49 outcome structure (`project_j46_j49_position_mgmt_findings`). Meta-labeling is the missing layer between the AI-side rationale (Component 3A) and execution sizing — could replace S79 risk-policy switch with a learned probability gate. Fractional differentiation is a candidate input transform if K54 v2 is fed raw price history instead of engineered features.
- **Potential hypothesis:** Replacing K54 v1's binary classifier loss with a triple-barrier meta-label (size ∈ {0, 0.5, 1.0}) on top of the primary AI signal Pareto-dominates K54 v1's plain probability gate on the J46-J49 outcome metric (mean R/trade) holding total exposure constant.
- **Cross-domain flag:** 02 (CPCV / deflated-Sharpe methodology)

### Deep Neural Networks, Gradient-Boosted Trees, Random Forests: Statistical Arbitrage on the S&P 500
- **Authors:** Christopher Krauss, Xuan Anh Do, Nicolas Huck
- **Year/Source:** 2017 / European Journal of Operational Research 259(2): 689-702
- **URL:** https://www.econstor.eu/bitstream/10419/130166/1/856307327.pdf ; https://www.sciencedirect.com/science/article/abs/pii/S0377221716308657
- **Abstract:** Trains DNN, GBT, and RF separately and as an equal-weighted ensemble on 240-day lagged returns of S&P-500 constituents to forecast which stocks beat the cross-sectional median next day; tests 1992-2015 on long-short top/bottom-decile portfolios.
- **Key findings:**
  - Equal-weighted ensemble of DNN+GBT+RF returns ~0.45% per day pre-cost (Sharpe ~5+ headline, deteriorates after 2002 with rising costs and competition).
  - Random forests are individually best in calmer regimes; deep nets best in volatile regimes; ensembling smooths regime sensitivity.
  - Returns concentrate in the highest-volatility, smallest-cap deciles — the edge has measurable but reasonable transaction-cost capacity.
  - Performance decays monotonically post-2008 and is essentially flat post-2010 — early evidence of edge decay in classical statarb.
- **Relevance to GTOS:** Methodologically the most direct precedent for K54: train classical-ML on lagged-return panels of multiple instruments, predict relative outperformance, ensemble. The decay-after-crowding story (post-2010) directly matches the GTOS edge-decay narrative (`project_f15_synthesis_regime_is_load_bearing`). Suggests K54 v2 should ensemble per-regime LightGBM with an RF and an NN — and treat post-2010 decay as a base-rate prior for any new ML signal.
- **Potential hypothesis:** A 3-model equal-weighted ensemble (per-regime LightGBM + per-regime RF + per-regime shallow NN) at the K54 v2 candidate-acceptance gate strictly dominates the single LightGBM K54 v1 baseline on the F15 H1→H2 holdout, with the bulk of the lift coming from regime-volatility-conditional disagreement between models.
- **Cross-domain flag:** 15 (statistical arbitrage)

### Long Short-Term Memory
- **Authors:** Sepp Hochreiter, Jürgen Schmidhuber
- **Year/Source:** 1997 / Neural Computation 9(8): 1735-1780
- **URL:** https://direct.mit.edu/neco/article/9/8/1735/6109/Long-Short-Term-Memory ; https://www.bioinf.jku.at/publications/older/2604.pdf
- **Abstract:** Introduces the LSTM cell — a recurrent unit with input/forget/output gates and a constant-error-carousel (CEC) — solving the vanishing-gradient problem that prevented vanilla RNNs from learning dependencies beyond ~10-20 timesteps. Demonstrates learning of dependencies across 1000+ timesteps.
- **Key findings:**
  - The vanishing/exploding gradient is a fundamental property of dense recurrent updates; gating + CEC sidesteps it.
  - LSTM outperforms RTRL, BPTT, and Elman nets on long-time-lag synthetic benchmarks.
  - Forget gates (added later by Gers et al 1999) are crucial for non-stationary sequences.
- **Relevance to GTOS:** Foundational architecture for any sequence-model alternative to LightGBM in K54 v2 / Q2 sequence models. Directly motivates the candidate H1-bar-LSTM that conditions on the last 60-120 candles' OHLCV+microstructure. The 1000-step capability is overkill for GTOS H1 (M15 → H1 reduction would give ~96 bars/week), so LSTM is a reasonable complexity ceiling, not a floor.
- **Potential hypothesis:** A single-layer LSTM with hidden-size 64 trained on 96 most-recent H1 bars of OHLCV + 12 tick-features per bar achieves ≥ K54 v1 LightGBM AUC on the F15 H1→H2 holdout, but with ~3× wider 95% CI per outcome cell — i.e., higher mean lift but unstable, justifying ensemble rather than replacement.
- **Cross-domain flag:** none

### Attention Is All You Need
- **Authors:** Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin
- **Year/Source:** 2017 / NeurIPS 2017 (Advances in Neural Information Processing Systems 30)
- **URL:** https://arxiv.org/abs/1706.03762 ; https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf
- **Abstract:** Introduces the Transformer — a sequence model based entirely on multi-head self-attention, eliminating recurrence and convolution. Achieves SOTA on WMT machine translation while training 4-10× faster than RNN-encoder-decoder on equivalent hardware.
- **Key findings:**
  - Multi-head scaled-dot-product self-attention captures long-range dependencies in O(n²·d) compute and O(1) sequential operations.
  - Positional encodings are necessary — attention itself is permutation-invariant.
  - Layer normalization + residual connections + warmup-then-decay LR schedule are essential for stable training.
  - Massive parallelism over the sequence dimension is the architectural reason transformers scale where RNNs do not.
- **Relevance to GTOS:** The architecture anchor for the Q2 sequence-model exploration. Self-attention's "all-pairs" structure can capture the relationship between an OB-formation candle and a subsequent retest candle 30+ bars later without the LSTM's cumulative-error fade. The O(n²) cost is benign at GTOS context lengths (≤200 H1 bars). Training instability of vanilla transformers at small data is the central caution: GTOS has a few thousand outcome trades, well below transformer-comfort.
- **Potential hypothesis:** A 2-layer 4-head Transformer with sequence-length 64 H1 bars and a [CLS]-token classifier head, trained with strong regularization (dropout 0.3, weight-decay 1e-3) on the K54 dataset, *underperforms* per-regime LightGBM in OOS AUC by a margin attributable to data-hunger — confirming the empirical-precedent that transformers need ≥10× the labels of trees at fixed signal-to-noise.
- **Cross-domain flag:** none

### Deep Learning for Limit Order Books
- **Authors:** Justin Sirignano
- **Year/Source:** 2019 / Quantitative Finance 19(4): 549-570 (arXiv 1601.01987 v3 2018)
- **URL:** https://arxiv.org/abs/1601.01987 ; https://www.tandfonline.com/doi/full/10.1080/14697688.2018.1546053
- **Abstract:** Develops a "spatial neural network" architecture exploiting the structure of LOB price levels: weights are shared across price levels and gradient flow respects spatial proximity, yielding parameter efficiency and out-of-sample lift over fully-connected baselines and logistic regression with hand-crafted features.
- **Key findings:**
  - The full LOB depth (not just best bid/ask) carries information for next-event direction prediction.
  - Spatial weight-sharing across LOB levels yields a low-dimensional model with better generalization than dense FC nets.
  - Beats vanilla LR + nonlinear features and beats fully-connected NN at all benchmarked horizons.
- **Relevance to GTOS:** GTOS does not currently have LOB depth; MT5 only exposes top-of-book ticks. However, when E24/E26 microstructure-feature work (`project_microstructure_archived_2026-04-27`) is revisited with broker LOB data, this is the architectural anchor for a CNN-style spatial network on level-by-level depth. For now, primary use is as a methodological precedent for Sirignano-Cont (2019) below — the universality result.
- **Potential hypothesis:** With MT5-broker-side L2 LOB data on XAUUSD (≥10 levels), a spatial-CNN trained on 30-second windows beats top-of-book features at next-1-minute direction prediction by an OOS-AUC margin >0.04 — validating LOB depth as a real signal for gold even though GTOS-current uses only tick microstructure.
- **Cross-domain flag:** 06 (LOB microstructure)

### Universal Features of Price Formation in Financial Markets: Perspectives from Deep Learning
- **Authors:** Justin Sirignano, Rama Cont
- **Year/Source:** 2019 / Quantitative Finance 19(9): 1449-1459 (arXiv 1803.06917)
- **URL:** https://arxiv.org/abs/1803.06917 ; http://rama.cont.perso.math.cnrs.fr/pdf/SirignanoCont2019.pdf
- **Abstract:** Trains a single deep LSTM on billions of LOB events from 489 NASDAQ stocks; shows that a *universal* model trained pooled across stocks generalizes out-of-sample to held-out stocks at accuracy comparable to per-stock models, indicating a stock-agnostic price-formation regularity.
- **Key findings:**
  - Universality: a single model trained on cross-sectionally pooled LOB data generalizes to unseen stocks at near-stock-specific accuracy.
  - Predictive power persists across years 2014-2017 (the training window) — the regularity is approximately stationary at this horizon.
  - The pooled model needs nonlinear function class — a linear pooled model loses substantial accuracy vs the per-stock baseline.
- **Relevance to GTOS:** Strongly supports the K54 cross-instrument-pooled approach as feasible. If pooled NASDAQ LOB shows universality, pooled XAU/US30/USDJPY/etc. H1 features may share enough regularity that a single pooled model + per-regime fine-tuning beats per-instrument independent models. Direct evidence against the GTOS-current per-instrument-isolated regime classifier.
- **Potential hypothesis:** A K54 v2 trained on pooled 7-instrument H1 candidate features (with a 7-d one-hot + per-regime gate) achieves ≥ within-instrument AUC for the 4 lower-volume instruments (USDJPY, GBPJPY, GBPUSD, XAGUSD) where data scarcity is the binding constraint, by leveraging XAUUSD's larger sample.
- **Cross-domain flag:** 06 (LOB universality)

### Deep Learning with Long Short-Term Memory Networks for Financial Market Predictions
- **Authors:** Thomas Fischer, Christopher Krauss
- **Year/Source:** 2018 / European Journal of Operational Research 270(2): 654-669
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0377221717310652 ; https://cris.fau.de/publications/208534319/
- **Abstract:** Replicates the Krauss-Do-Huck (2017) S&P-500 statistical-arbitrage setup, replacing memoryless models with an LSTM. LSTM achieves ~0.46% daily return pre-cost and Sharpe ~5.8, beating RF, DNN, and logistic regression baselines.
- **Key findings:**
  - LSTM > RF > DNN > LR ordering, with LSTM superiority concentrated in volatile regimes.
  - The post-2010 decay observed in the original Krauss-Do-Huck paper persists for LSTM — i.e., memory does not save a stale edge.
  - LSTM benefits derive from learned interaction with autocorrelation in the lagged-return inputs, not from raw nonlinearity.
- **Relevance to GTOS:** Direct precedent for "LSTM beats GBM at higher frequency / volatile cells" — qualifies the K54-v2-LightGBM choice. Suggests reserving LSTM for the volatile-regime sub-classifier in a per-regime ensemble. Reinforces the universal lesson that *memory does not rescue a decayed edge*; this is exactly the GTOS H2-2026 LONG-WR collapse situation.
- **Potential hypothesis:** Within the trending_bull regime cell where F2 / F15 located the GTOS LONG-side decay, an H1-LSTM trained on the 2024-2025 in-sample shows the *same* pattern Fischer-Krauss observed for post-2010 S&P decay: equivalent in-sample fit but no OOS lift over 2026 — confirming decay is mechanism-level, not architecture-level.
- **Cross-domain flag:** 15 (statistical arbitrage)

### DeepLOB: Deep Convolutional Neural Networks for Limit Order Books
- **Authors:** Zihao Zhang, Stefan Zohren, Stephen Roberts
- **Year/Source:** 2019 / IEEE Transactions on Signal Processing 67(11): 3001-3012
- **URL:** https://arxiv.org/abs/1808.03668 ; https://ieeexplore.ieee.org/document/8673598
- **Abstract:** Combines CNN feature extraction over LOB price-level rows with an Inception module and an LSTM head; trained on FI-2010 benchmark + LSE proprietary data; predicts mid-price direction over short horizons.
- **Key findings:**
  - SOTA on FI-2010 LOB benchmark; outperforms Tsantekidis et al RNN baseline.
  - CNN-Inception captures local + multi-scale spatial patterns in the LOB; LSTM adds temporal context.
  - Model trained on one set of stocks generalizes to held-out stocks (universality echo of Sirignano-Cont).
  - Benchmark-stable accuracy across horizons of 10-100 events ahead.
- **Relevance to GTOS:** Architectural recipe for LOB+temporal hybrid that GTOS may need post-MT5-L2-upgrade. The CNN-Inception-LSTM stack is the dominant LOB pattern in the 2019-2022 literature; if GTOS adds LOB features, this is the starting baseline. The universality echo strengthens the K54-pooled-instrument hypothesis above.
- **Potential hypothesis:** Even *without* L2 LOB, a 1D-CNN + LSTM hybrid on top-of-book tick features (12 features × 60 seconds) at GTOS XAUUSD achieves ≥ tick-feature LightGBM at 1-minute direction with smaller variance — i.e., temporal structure in tick features is currently underutilized by tree models.
- **Cross-domain flag:** 06 (LOB microstructure)

### A Unified Approach to Interpreting Model Predictions (SHAP)
- **Authors:** Scott M. Lundberg, Su-In Lee
- **Year/Source:** 2017 / NeurIPS 2017 (Advances in Neural Information Processing Systems 30)
- **URL:** https://arxiv.org/abs/1705.07874 ; https://papers.neurips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions
- **Abstract:** Introduces SHAP — Shapley-values-from-game-theory applied as a unified additive feature-attribution framework that subsumes LIME, DeepLIFT, layer-wise relevance propagation, and feature-importance scores. Provides exact polynomial-time computation for trees (TreeSHAP).
- **Key findings:**
  - SHAP is the unique additive attribution that satisfies local accuracy + missingness + consistency.
  - Shapley-derived attributions are model-agnostic and theoretically grounded vs ad-hoc importance measures.
  - TreeSHAP gives exact polynomial-time SHAP values for tree ensembles, making the method practical for GBMs and RFs at scale.
- **Relevance to GTOS:** Direct dependency for K54 v2 interpretability. F5 (`project_f5_k51_does_not_replicate_under_proper_method`) showed that improper SHAP / Bonferroni gave false-positive K51 decay claims; SHAP is the right tool only when used with proper hold-out + multiple-testing discipline. K54 v2 promotion gate should use SHAP-stability across folds (not magnitude).
- **Potential hypothesis:** Computing TreeSHAP across 5 CPCV folds and ranking features by *median rank* (not mean magnitude) recovers a feature ranking that is stable to ±1 position across the F15 H1→H2 boundary, while the mean-magnitude ranking shifts by ≥3 positions for the top-5 features — matching F5's "K51 does not replicate" finding under principled methodology.
- **Cross-domain flag:** 02 (multiple-testing methodology)

### FinBERT: Financial Sentiment Analysis with Pre-Trained Language Models
- **Authors:** Dogu Araci
- **Year/Source:** 2019 / arXiv 1908.10063 (MSc Thesis, University of Amsterdam)
- **URL:** https://arxiv.org/abs/1908.10063
- **Abstract:** Fine-tunes BERT on the Financial PhraseBank corpus to produce FinBERT — a domain-adapted language model for financial sentiment classification. Demonstrates state-of-the-art accuracy on multiple financial-NLP benchmarks vs general-domain BERT.
- **Key findings:**
  - Domain adaptation (further pre-training on financial text) yields measurable lift over fine-tuning general-purpose BERT.
  - Three-class sentiment (positive/neutral/negative) on PhraseBank reaches ~0.86 accuracy, then-SOTA.
  - Smaller fine-tuning datasets become viable when the pre-trained backbone is domain-adapted.
- **Relevance to GTOS:** GTOS is a price-action system without text features in production. However, the FinBERT line is the literature anchor for any future text-feature ingestion (KAP research findings, central-bank announcements, earnings news). If a Q2-Q3 deliverable adds text-embedding features to K54, FinBERT-class models are the right starting embedding.
- **Potential hypothesis:** Adding a daily FOMC/CB-statement FinBERT-sentiment scalar feature to K54 v2 lifts AUC on USDJPY/GBPUSD by ≥0.02 in macro-event days but is null on non-event days — i.e., text helps where text matters, validating the gating-by-event design.
- **Cross-domain flag:** 11 (FX rates / central banks); 20 (LLM-feature handoff)

### FinBERT: A Pre-trained Financial Language Representation Model
- **Authors:** Yi Yang, Mark Christopher Siy Uy, Allen Huang
- **Year/Source:** 2020 / IJCAI 2020 / arXiv 2006.08097
- **URL:** https://arxiv.org/abs/2006.08097 ; https://www.ijcai.org/proceedings/2020/0622.pdf
- **Abstract:** Independent FinBERT, pre-trained on 4.9B-token financial corpus (10-K, 10-Q, analyst reports, earnings calls). Reports SOTA on FiQA and FPB sentiment tasks; demonstrates that pre-training data scale matters more than fine-tuning hyperparameters in financial NLP.
- **Key findings:**
  - 4.9B-token pre-training corpus is an order of magnitude larger than Araci's PhraseBank-only setting; lifts robustness on out-of-distribution finance text.
  - Sub-domain pre-training (10-K vs analyst reports vs earnings calls) trades breadth for depth — pooled corpus wins on average.
  - The Yang-Uy-Huang FinBERT is the de-facto open-source FinBERT used in production NLP pipelines as of 2024-2025.
- **Relevance to GTOS:** Same as Araci above; this is the more-deployed variant. If GTOS adds news-event embeddings, this is the recommended drop-in.
- **Potential hypothesis:** Same general hypothesis as the Araci entry — applies symmetrically.
- **Cross-domain flag:** 11; 20

## Section 3 — Time-series transformers and deep sequence models for finance

### Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting
- **Authors:** Haoyi Zhou, Shanghang Zhang, Jieqi Peng, Shuai Zhang, Jianxin Li, Hui Xiong, Wancai Zhang
- **Year/Source:** 2021 / AAAI 2021 (Best Paper) — arXiv 2012.07436
- **URL:** https://arxiv.org/abs/2012.07436 ; https://ojs.aaai.org/index.php/AAAI/article/view/17325
- **Abstract:** Designs a transformer variant for long-sequence forecasting (LSTF) with three innovations: ProbSparse self-attention reducing complexity from O(L²) to O(L log L); attention distilling that halves layers; and a generative-style decoder predicting the entire output sequence in one forward pass.
- **Key findings:**
  - ProbSparse attention provably preserves the dominant attention scores while saving 75-95% of compute on long inputs.
  - Self-attention distilling halves the cascading layer input — addresses memory blow-up at L > 1000.
  - Generative decoder produces multi-step forecasts in one pass — eliminates step-by-step error accumulation seen in autoregressive transformers.
  - Beats LSTM, LogSparse, Reformer baselines on 4 large-scale real-world series.
- **Relevance to GTOS:** GTOS context lengths are short (~96 H1 bars per week), so the L log L speedup is not load-bearing for K54. However, the *generative-decoder one-pass forecast* pattern is directly applicable to a Q2 sequence-model variant predicting the next-N-candle outcome distribution rather than a single binary label — i.e., a probabilistic version of K54.
- **Potential hypothesis:** A one-pass generative decoder predicting joint (next-4-candle-direction, next-4-candle-volatility) on H1 inputs achieves higher mean log-likelihood on the F15 H2-2026 holdout than 4 independent step-by-step LightGBM heads, because the decoder learns the cross-time dependence structure that independent classifiers miss.
- **Cross-domain flag:** none

### Autoformer: Decomposition Transformers with Auto-Correlation for Long-Term Series Forecasting
- **Authors:** Haixu Wu, Jiehui Xu, Jianmin Wang, Mingsheng Long
- **Year/Source:** 2021 / NeurIPS 2021 — arXiv 2106.13008
- **URL:** https://arxiv.org/abs/2106.13008 ; https://proceedings.neurips.cc/paper/2021/hash/bcc0d400288793e8bdcd7c19a8ac0c2b-Abstract.html
- **Abstract:** Replaces self-attention with an *Auto-Correlation* mechanism based on series periodicity, and inlines series decomposition (trend / seasonal) as an internal module rather than preprocessing. Yields 38% mean MSE reduction over Informer on six benchmarks.
- **Key findings:**
  - Inlined trend-seasonal decomposition as a deep-learning module beats post-hoc decomposition.
  - Auto-correlation captures sub-series-level dependencies more parsimoniously than full self-attention.
  - Particularly strong on series with explicit periodicity (energy, weather, traffic).
- **Relevance to GTOS:** Daily / weekly / kill-zone seasonality in GTOS H1 returns is a known feature (London / NY / Tokyo) — Autoformer's trend-seasonal split is a natural fit if a transformer is ever the K54 v2 architecture. Cautions that periodicity advantage is benchmark-dependent.
- **Potential hypothesis:** On XAUUSD H1 returns, an Autoformer with kill-zone-encoded periodicity beats a vanilla Transformer by ≥10% MSE on the next-24-hour return forecast — but the gap collapses to <2% on FX pairs (USDJPY/GBPJPY/GBPUSD) where weekly/daily seasonality is weaker.
- **Cross-domain flag:** none

### An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling (TCN)
- **Authors:** Shaojie Bai, J. Zico Kolter, Vladlen Koltun
- **Year/Source:** 2018 / arXiv 1803.01271 (CMU technical report; influential preprint)
- **URL:** https://arxiv.org/abs/1803.01271 ; https://github.com/locuslab/TCN
- **Abstract:** Introduces the Temporal Convolutional Network (TCN) — 1D causal dilated convolutions with residual connections — and benchmarks it against LSTM/GRU across diverse sequence-modeling tasks. TCN matches or beats RNN baselines while supporting parallel training.
- **Key findings:**
  - Dilated 1D-convolutions yield exponentially-large effective receptive fields with linear parameter cost.
  - TCN beats LSTM/GRU on the majority of benchmark tasks (copy memory, adding problem, polyphonic music, language modeling).
  - Parallelizable in training (vs RNN sequential dependence) — allows much faster training at fixed wall-clock.
  - Argues against the default association of sequence-modeling with recurrence.
- **Relevance to GTOS:** TCN is a natural middle-ground between LightGBM (no temporal model) and Transformer (high data-hunger) for K54 v2 and Q2. Its receptive-field/parameter ratio is favorable at the GTOS data scale (~few thousand outcome trades). The parallel-training story matters for batch backtests on the orchestrator's $0-budget Phase 1.
- **Potential hypothesis:** A 6-layer TCN with kernel-size 3 and exponential dilation (1,2,4,8,16,32) on 64-bar H1 sequences trained on the K54 dataset achieves AUC parity with the Transformer above (potential hypothesis 19-05) but with 5× faster wall-clock training — making it the more practical Q2 sequence-model baseline.
- **Cross-domain flag:** none

### Autoencoder Asset Pricing Models
- **Authors:** Shihao Gu, Bryan Kelly, Dacheng Xiu
- **Year/Source:** 2021 / Journal of Econometrics 222(1): 429-450
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304407620301998 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3335536
- **Abstract:** Proposes a conditional latent-factor asset-pricing model where factor exposures are nonlinear functions of asset characteristics, parameterized as autoencoder neural networks. Combines factor returns and characteristic-conditioned exposures end-to-end.
- **Key findings:**
  - Autoencoder-implied factors price the cross-section of returns better than PCA-derived static factors.
  - Nonlinear exposures help especially in the small-cap / high-book-to-market deciles.
  - The latent-factor structure is more parsimonious than direct firm-characteristic regression — interpretable as "ML-distilled" factor model.
- **Relevance to GTOS:** GTOS does not have a cross-section large enough to learn factors a la equities. However, the encoder-as-feature-distillation pattern is a candidate for Q2: train a tick-feature autoencoder and feed the bottleneck activation as a K54 v2 feature, achieving regularized representation of E24/E26 microstructure features that are noisy individually.
- **Potential hypothesis:** An autoencoder trained to reconstruct 12 tick-microstructure features over a 60-second window, with a 4-dimensional bottleneck, produces a feature embedding that beats raw microstructure features at AUC by ≥0.01 on the K54 v2 task — confirming the bottleneck regularization helps in the small-n regime that defeated E24/E26 originally.
- **Cross-domain flag:** 13

### A Comprehensive Look at the Empirical Performance of Equity Premium Prediction
- **Authors:** Ivo Welch, Amit Goyal
- **Year/Source:** 2008 / Review of Financial Studies 21(4): 1455-1508 (NBER WP 10483, 2004)
- **URL:** https://academic.oup.com/rfs/article-abstract/21/4/1455/1565737 ; https://www.ivo-welch.info/research/journalcopy/2008-rfs.pdf
- **Abstract:** Re-examines the academic-literature catalog of equity-premium predictors (dividend yield, term spread, default spread, etc.) and finds that virtually none beat the historical mean OOS over rolling 30-year windows. Establishes the "kitchen-sink in-sample but useless OOS" baseline that subsequent ML papers must beat.
- **Key findings:**
  - Of ~14 catalog predictors, virtually all fail OOS over rolling windows.
  - The historical mean is a tough OOS benchmark — small absolute R² differences swing in/out of significance.
  - Combination forecasts (Rapach-Strauss-Zhou 2010 follow-up) recover some of the lost predictability.
  - The 2008 paper is the de-facto null model that ML asset-pricing papers (Gu-Kelly-Xiu 2020) must dethrone.
- **Relevance to GTOS:** Cautionary literature anchor. The 2008 Welch-Goyal verdict is the *baseline pattern* GTOS sees in F15 H1→H2 — apparent in-sample edge that fails OOS. Reinforces that K54 v2 must clear a properly-designed historical-mean / random-walk null on a held-out post-promotion window, not just on the K52-style retrospective Bonferroni test.
- **Potential hypothesis:** GTOS's monthly expectancy series 2024-2026 fails the Welch-Goyal-2008 OOS-vs-historical-mean test on a 12-month rolling window, formally placing the F15 decay in the same statistical class as the equity-premium predictability decay — i.e., this is a generic in-sample/OOS gap, not an exotic regime shift.
- **Cross-domain flag:** 02 (OOS methodology); 17 (decay literature)

### FEDformer: Frequency Enhanced Decomposed Transformer for Long-term Series Forecasting
- **Authors:** Tian Zhou, Ziqing Ma, Qingsong Wen, Xue Wang, Liang Sun, Rong Jin
- **Year/Source:** 2022 / ICML 2022 — arXiv 2201.12740
- **URL:** https://arxiv.org/abs/2201.12740 ; https://proceedings.mlr.press/v162/zhou22g.html
- **Abstract:** Combines transformer with seasonal-trend decomposition and Fourier / wavelet sparse representations to model long-term series. Achieves linear complexity in sequence length and 14.8-22.6% MSE reduction over prior SOTA.
- **Key findings:**
  - Sparse representations in frequency domain capture global structure with O(L) complexity.
  - Fourier-block + wavelet-block variants — wavelet handles non-stationary series better.
  - Beats Autoformer and Informer on six benchmarks for both univariate and multivariate.
- **Relevance to GTOS:** Frequency-domain features for H1 financial time series are an under-explored architecture in GTOS. If wavelet/Fourier blocks improve forecast accuracy, FEDformer's recipe could inform a separate "frequency-aware" branch of K54 v2 — particularly relevant to gold (XAUUSD) where session-aliased seasonality is plausible.
- **Potential hypothesis:** A FEDformer-wavelet branch on XAUUSD H1 returns (with London/NY session frequencies in the wavelet basis) beats a time-domain-only transformer on next-day return prediction by ≥5% MSE — confirming session-aliased seasonality is exploitable in frequency domain.
- **Cross-domain flag:** 04 (wavelets / multitimeframe)

### A Time Series Is Worth 64 Words: Long-Term Forecasting with Transformers (PatchTST)
- **Authors:** Yuqi Nie, Nam H. Nguyen, Phanwadee Sinthong, Jayant Kalagnanam
- **Year/Source:** 2023 / ICLR 2023 — arXiv 2211.14730
- **URL:** https://arxiv.org/abs/2211.14730 ; https://github.com/yuqinie98/PatchTST
- **Abstract:** Two-key-idea transformer for time series: (1) tokenize the series as overlapping patches (each patch ≈ a "word") to retain local semantic content while reducing sequence length; (2) channel-independent processing — each variate is forecast separately by a shared backbone. Achieves 21% MSE reduction.
- **Key findings:**
  - Patch-tokenization quadratically reduces attention compute and improves local-pattern modeling.
  - Channel independence prevents the spurious cross-variate attention that hurts standard transformers on time series.
  - Self-supervised masked pre-training on one dataset transfers strongly to others.
- **Relevance to GTOS:** Patch-tokenization is the most promising transformer architecture *at GTOS data scale*. With 7 instruments and short context (64-128 bars), patches of size 4-8 H1 bars yield sequences of length 8-32 — well below the data-hunger threshold. Channel-independence is also a natural fit for the GTOS multi-instrument setting where cross-instrument correlation is already handled by a separate gate.
- **Potential hypothesis:** A PatchTST with patch-size 4 H1 bars and 16-patch sequence (= 64 H1 bars) trained on per-instrument H1 returns achieves OOS AUC parity with per-regime LightGBM on K54 — making PatchTST the leading transformer candidate when Q2 deepens K54 to sequence-aware models.
- **Cross-domain flag:** none

### TimesNet: Temporal 2D-Variation Modeling for General Time Series Analysis
- **Authors:** Haixu Wu, Tengge Hu, Yong Liu, Hang Zhou, Jianmin Wang, Mingsheng Long
- **Year/Source:** 2023 / ICLR 2023 — arXiv 2210.02186
- **URL:** https://arxiv.org/abs/2210.02186 ; https://github.com/thuml/TimesNet
- **Abstract:** Reshapes 1D time series into 2D tensors based on FFT-discovered periodicity, then applies CNN inception blocks; achieves SOTA across forecasting / imputation / classification / anomaly-detection on multiple benchmarks.
- **Key findings:**
  - Multi-period decomposition via dominant-FFT-frequencies, parallelized into 2D Inception block.
  - Single architecture handles five canonical tasks (forecasting, imputation, classification, anomaly detection, short-term).
  - Beats Autoformer, FEDformer, and DLinear on multiple subtasks.
- **Relevance to GTOS:** TimesNet's *task generality* is a unique selling point — a single backbone could serve K54 (classification), volatility forecasting (regression), and S1 monthly-decay anomaly detection. The 2D-reshape recipe could exploit kill-zone × week-day periodicity that GTOS already knows is signal-rich.
- **Potential hypothesis:** A single TimesNet backbone with 3 task heads (binary K54 candidate, expected-R regression, monthly-anomaly score) Pareto-dominates 3 separately-trained heads at multi-task validation, by ≥3% on each of the 3 metrics — confirming representation sharing is helpful at GTOS data scale.
- **Cross-domain flag:** 05 (anomaly detection)

### iTransformer: Inverted Transformers Are Effective for Time Series Forecasting
- **Authors:** Yong Liu, Tengge Hu, Haoran Zhang, Haixu Wu, Shiyu Wang, Lintao Ma, Mingsheng Long
- **Year/Source:** 2024 / ICLR 2024 (Spotlight) — arXiv 2310.06625
- **URL:** https://arxiv.org/abs/2310.06625 ; https://github.com/thuml/iTransformer
- **Abstract:** Inverts the transformer's tokenization: each *variate* (channel) becomes a token rather than each timestep. Self-attention then captures inter-variate correlations; FFN learns nonlinear transforms per variate. Improves forecasting on multiple benchmarks.
- **Key findings:**
  - Variate-token attention captures multivariate cross-correlations more directly than time-token attention.
  - Larger lookback windows help with iTransformer (vs hurt with vanilla transformers).
  - Beats prior SOTA (PatchTST, TimesNet) on most multivariate benchmarks.
- **Relevance to GTOS:** GTOS already has a separate cross-instrument-correlation gate; iTransformer's variate-attention could *replace* or supplement that gate by learning the regime-conditional correlation structure end-to-end. Direct candidate for the multi-instrument-pooled K54 v2.
- **Potential hypothesis:** An iTransformer with 7 instrument-tokens (one per GTOS symbol) and 64-bar lookback per token achieves AUC ≥0.04 above per-regime LightGBM in regime cells where cross-instrument correlation is informative (e.g., trending_bull XAU + USD index).
- **Cross-domain flag:** 13 (cross-asset)

### Are Transformers Effective for Time Series Forecasting? (DLinear)
- **Authors:** Ailing Zeng, Muxi Chen, Lei Zhang, Qiang Xu
- **Year/Source:** 2023 / AAAI 2023 (Oral) — arXiv 2205.13504
- **URL:** https://arxiv.org/abs/2205.13504 ; https://github.com/cure-lab/LTSF-Linear
- **Abstract:** Demonstrates that simple linear models with seasonal-trend decomposition (DLinear, NLinear) outperform transformer-based time-series methods (Informer, Autoformer, FEDformer) on 9 standard LTSF benchmarks. Attributes the result to permutation-invariance loss in attention mechanisms.
- **Key findings:**
  - DLinear (a single linear layer per decomposed component) beats Informer/Autoformer/FEDformer on most benchmarks.
  - Self-attention is permutation-invariant — fundamental temporal-information loss.
  - Many transformer "improvements" close the gap to the linear baseline rather than push past it.
  - Result has been partially refuted by PatchTST and iTransformer, which beat DLinear on some benchmarks — but the cautionary case stands.
- **Relevance to GTOS:** The single most important contrarian-finding paper for K54 v2 architecture choice. Reinforces that *adding architectural complexity* on a finite, noisy dataset is not free. Suggests that the K54 v2 benchmark suite must include a DLinear (or equivalent simple-linear) baseline before any transformer is shipped.
- **Potential hypothesis:** A per-instrument DLinear baseline on H1 OHLCV achieves OOS AUC within ±0.01 of the LightGBM K54 v1 baseline — making DLinear the right "should we abandon ML and use linear?" sanity check before any K54 v2 architecture decision.
- **Cross-domain flag:** 02 (Occam-test methodology)

### Deep Learning in Asset Pricing
- **Authors:** Luyang Chen, Markus Pelger, Jason Zhu
- **Year/Source:** 2024 / Management Science 70(2): 714-750 (arXiv 1904.00745, 2019)
- **URL:** https://pubsonline.informs.org/doi/10.1287/mnsc.2023.4695 ; https://arxiv.org/abs/1904.00745
- **Abstract:** Deep neural network asset-pricing model with three innovations: (1) GAN-style adversarial loss based on no-arbitrage condition; (2) RNN encoder for macroeconomic state; (3) feed-forward for stock characteristics. OOS Sharpe substantially exceeds Gu-Kelly-Xiu and other ML benchmarks.
- **Key findings:**
  - Adversarial-no-arbitrage loss generates "hardest-to-price" test assets, sharpening the model.
  - RNN macro encoder captures conditional state better than fixed factor models.
  - OOS Sharpe ~2.6 on long-short decile portfolios — about 2× Gu-Kelly-Xiu (RFS 2020).
- **Relevance to GTOS:** GTOS's daily/weekly macro state (CB calendar, COT, DXY) is currently used heuristically by the AI prompt. An RNN macro-encoder is a candidate replacement that produces a learned regime embedding for K54 — directly addressing the F15 finding that regime is the load-bearing decay axis.
- **Potential hypothesis:** A 2-layer GRU macro-encoder trained on COT, DXY, VIX, CB-rate-spread, fed as a 4-dim regime embedding to K54 v2, beats the v1 H4-swing classifier at separating the F15 H1/H2 boundary by ≥0.05 AUC — i.e., learned regime > rule-based regime.
- **Cross-domain flag:** 11 (FX/CB); 05 (regime detection)

### Machine Learning for Asset Managers
- **Authors:** Marcos M. Lopez de Prado
- **Year/Source:** 2020 / Cambridge University Press (Cambridge Elements in Quantitative Finance)
- **URL:** https://www.cambridge.org/core/books/machine-learning-for-asset-managers/6D9211305EA2E425D33A9F38D0AE3545 ; https://smallake.kr/wp-content/uploads/2020/04/SSRN-id3558728.pdf
- **Abstract:** Successor to *Advances in Financial Machine Learning*; 7 short chapters on covariance-matrix de-noising, hierarchical clustering, optimal portfolio with no-noise covariance, false-strategy theorem, and inference-tree methods. Practitioner-focused with Python code.
- **Key findings:**
  - Covariance shrinkage / de-noising is essential for ML in finance — Marchenko-Pastur eigenvalue cutoff.
  - Hierarchical Risk Parity (HRP) outperforms mean-variance optimization OOS.
  - False-strategy theorem: Sharpe distribution under multiple testing is fatter-tailed than naïve N(0,1) — required adjustment for ML strategy selection.
  - Inference trees (Codependence-based) beat random-forest feature importance in some settings.
- **Relevance to GTOS:** Direct dependency for K54 promotion-gate methodology. The false-strategy theorem is a stricter version of deflated-Sharpe — relevant when GTOS picks K54 v2 from a search over 100s of hyperparameter configurations. HRP could replace the heuristic GTOS portfolio sizing if multi-instrument allocation becomes adaptive.
- **Potential hypothesis:** Applying the false-strategy theorem to the K54 v2 hyperparameter search (size of search ≈ 200) shrinks the effective Sharpe of the best K54 v2 by ≥30%, recovering the gap between in-sample and post-promotion live results — and quantifying the "selection bias" portion of K54 v1's underperformance.
- **Cross-domain flag:** 02 (deflated-Sharpe / false-strategy)

### Can Machines "Learn" Finance?
- **Authors:** Ronen Israel, Bryan T. Kelly, Tobias J. Moskowitz
- **Year/Source:** 2020 / Journal of Investment Management — SSRN 3624052
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3624052 ; https://joim.com/can-machines-learn-finance/
- **Abstract:** Surveys ML's challenges specific to asset management: low signal-to-noise, regime change, evolving feature distributions, capacity-constrained alpha, market efficiency feedback. Argues ML helps but doesn't dominate the way it does in vision/NLP.
- **Key findings:**
  - Asset-management signals are inherently weak (Sharpe ~0.3-0.6 attainable, not ~5+ as misleadingly suggested by zero-cost backtests).
  - Regime change and time-series non-stationarity dominate OOS performance — the standard ML iid assumption is materially violated.
  - Trade frequency, capacity, and slippage erode raw model AUC into much smaller realized Sharpe.
  - Theory-guided ML (incorporating economic priors) generally beats theory-free pure ML at typical asset-mgmt scale.
- **Relevance to GTOS:** Directly applicable cautionary scaffold for K54 v2 promotion. The "AUC vs Sharpe gap" warning is exactly the GTOS B7-vs-realized-R disconnect (e.g., F8 hallucination decreased while realized R got worse). Theory-guided priors map to ICT/SMC structural features in K54 — i.e., GTOS's price-action features are a form of theory-guidance vs raw-OHLCV feeds.
- **Potential hypothesis:** A K54 v2 trained with ICT/SMC-structured features outperforms a raw-OHLCV K54 baseline by ≥0.05 AUC on the H2-2026 holdout, but the gap shrinks to <0.02 in realized R/trade — confirming the AUC-to-realized-R gap that Israel-Kelly-Moskowitz emphasize.
- **Cross-domain flag:** 02 (capacity / decay); 17 (behavioral feedback)

### Solving High-Dimensional PDEs Using Deep Learning (Deep BSDE)
- **Authors:** Jiequn Han, Arnulf Jentzen, Weinan E
- **Year/Source:** 2018 / PNAS 115(34): 8505-8510 (arXiv 1707.02568)
- **URL:** https://www.pnas.org/doi/10.1073/pnas.1718942115 ; https://arxiv.org/abs/1707.02568
- **Abstract:** Reformulates high-dimensional parabolic PDEs as backward stochastic differential equations (BSDEs) and approximates the BSDE solution gradient with deep neural networks; demonstrates effectiveness on Black-Scholes-Barenblatt and Hamilton-Jacobi-Bellman in 100+ dimensions.
- **Key findings:**
  - Deep BSDE solver scales to 100-1000 dimensions where finite-difference / Monte Carlo PDE solvers fail.
  - Connects machine learning directly to stochastic-control / pricing PDE — a unifying bridge.
  - Reformulates the problem as a *learning* problem: minimize the squared boundary error.
- **Relevance to GTOS:** Theoretical anchor more than direct dependency. GTOS's optimal stop-loss / take-profit problem is implicitly a stochastic-control problem; deep BSDE is the canonical numerical method if GTOS ever wants to learn data-driven optimal SL/TP placement under empirical (non-Gaussian) dynamics.
- **Potential hypothesis:** A deep BSDE solver fed with empirical XAUUSD H1 distribution (ξ=0.35 fat tail) suggests an optimal SL ≥10% farther than ATR×0.5 — i.e., the GTOS sl_buffer multiplier is suboptimal under fat-tailed dynamics, consistent with the L2 sl_beyond_ob rejection rates documented in `project_live_l2_rejection_per_instrument`.
- **Cross-domain flag:** 01 (stochastic calculus); 21 (risk management)

### Deep Hedging
- **Authors:** Hans Buehler, Lukas Gonon, Josef Teichmann, Ben Wood
- **Year/Source:** 2019 / Quantitative Finance 19(8): 1271-1291 (arXiv 1802.03042, 2018)
- **URL:** https://arxiv.org/abs/1802.03042 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2019.1571683
- **Abstract:** Frames hedging as a deep-RL problem: a policy network outputs hedge ratios at each step, optimizing a convex risk measure. Generalizes Black-Scholes hedging to incomplete markets with frictions (transaction costs, liquidity, risk limits).
- **Key findings:**
  - Deep policy networks ε-approximate any optimal hedging strategy in finite-horizon discrete-time markets.
  - Convex risk measures (CVaR, entropic risk) replace mean-variance, capturing fat-tailed loss distributions.
  - Cross-instrument hedging emerges automatically when the policy is given multi-asset state.
  - Hedge fund / structuring desks have adopted variants of this method since 2019.
- **Relevance to GTOS:** GTOS does not currently hedge, but the deep-RL framing is directly applicable to learned position management — i.e., a learned analog of the J46-J49 partial-close / BE / time-stop policy. Cross-listed with domain 20 (RL); the "hedging-as-policy" framing is the bridge.
- **Potential hypothesis:** A deep-policy network trained on the J46-J49 backtest outcome distribution recovers the empirical Pareto-optimal policy (0% partial + immediate-on-TP1 BE + 12-bar time-stop + 3.0R TP1) within 5% of the rule-set's mean R/trade — confirming the J46-J49 grid-search is near-optimal in the policy class.
- **Cross-domain flag:** 20 (RL handoff)

## Section 4 — ML for limit order book / microstructure

### Forecasting Stock Prices from the Limit Order Book Using Convolutional Neural Networks
- **Authors:** Avraam Tsantekidis, Nikolaos Passalis, Anastasios Tefas, Juho Kanniainen, Moncef Gabbouj, Alexandros Iosifidis
- **Year/Source:** 2017 / IEEE 19th Conference on Business Informatics (CBI 2017)
- **URL:** https://cidl.csd.auth.gr/resources/conference_pdfs//2017_CBI_CNNLOB.pdf ; https://ieeexplore.ieee.org/document/8010701/
- **Abstract:** Uses CNN on the last 100 entries of the limit order book (treated as a 2D image) to predict short-horizon mid-price direction; evaluates on 4M-event dataset (Helsinki Exchange) from FI-2010 benchmark. CNN beats MLP and SVM baselines.
- **Key findings:**
  - Treating the LOB as a 2D image (price levels × time) lets vanilla CNNs learn microstructure patterns.
  - Outperforms MLP and SVM by clear margins on next-event direction.
  - One of the founding papers of the FI-2010 benchmark line that DeepLOB and TLOB later use.
- **Relevance to GTOS:** Conceptually related to GTOS's tick-microstructure features (E24/E26). The "LOB-as-image" framing motivates a similar treatment of GTOS's tick stream — depth × time → 2D — even though GTOS does not have full LOB depth.
- **Potential hypothesis:** A CNN trained on a 2D representation of the GTOS tick stream (12 features × 60 seconds) at XAUUSD beats the per-feature LightGBM by AUC ≥0.02 at next-1-minute direction — confirming the "image" framing recovers signal that per-feature trees miss.
- **Cross-domain flag:** 06

### Conditional Time Series Forecasting with Convolutional Neural Networks
- **Authors:** Anastasia Borovykh, Sander Bohte, Cornelis W. Oosterlee
- **Year/Source:** 2017 / arXiv 1703.04691 (presented at ICANN 2017)
- **URL:** https://arxiv.org/abs/1703.04691
- **Abstract:** Adapts WaveNet's dilated-convolution architecture for financial time-series forecasting. Tests on S&P 500, VIX, CBOE interest rate, and exchange rates. Conditional inputs (multiple parallel time series) improve accuracy.
- **Key findings:**
  - Dilated convolutions enable broad receptive fields over financial time series.
  - Conditional inputs (parallel related series) help — multivariate context improves univariate forecast.
  - Predates Bai-Kolter-Koltun TCN (2018) and is a more finance-specific application of the same family.
- **Relevance to GTOS:** Conditional-input idea directly applicable to K54 — the model can condition on multiple instruments / multiple timeframes simultaneously. Architectural anchor for "WaveNet-style" K54 v2 alternative.
- **Potential hypothesis:** A WaveNet-style dilated-CNN conditioned on (XAUUSD H1, USDJPY H1, DXY H1) jointly outperforms per-instrument LightGBM on USDJPY H1 next-bar direction by ≥0.03 AUC — confirming cross-instrument conditioning lifts the data-poor cells.
- **Cross-domain flag:** 13 (cross-asset)

### Deep Learning for Portfolio Optimisation
- **Authors:** Zihao Zhang, Stefan Zohren, Stephen Roberts
- **Year/Source:** 2020 / Journal of Financial Data Science 2(4): 8-20 (arXiv 2005.13665)
- **URL:** https://arxiv.org/abs/2005.13665 ; https://www.oxford-man.ox.ac.uk/wp-content/uploads/2020/06/Deep-Learning-for-Portfolio-Optimisation.pdf
- **Abstract:** Trains an end-to-end deep network on ETF data to directly optimize Sharpe ratio without intermediate return-forecasting. Outperforms Markowitz mean-variance and equal-weight benchmarks 2011-2020 including the COVID-March-2020 stress.
- **Key findings:**
  - End-to-end Sharpe optimization avoids the brittle return-forecast → optimizer pipeline.
  - LSTM and Transformer variants both work; gating mechanisms help in stress regimes.
  - Beats benchmarks during the March-2020 stress month — i.e., the model degrades gracefully.
- **Relevance to GTOS:** GTOS does not optimize portfolio weights, but the *direct-Sharpe-optimization* paradigm could replace separate K54 (binary) + sizing-policy components with a single end-to-end module that outputs position size. Q3 / Q4 candidate.
- **Potential hypothesis:** A LSTM-Sharpe-optimizer trained end-to-end on the K54 input feature set with position-size output (continuous in [-1,1]) achieves higher monthly Sharpe than the (K54 binary × J46-J49 fixed sizing) pipeline by ≥0.3 Sharpe units, by learning to size down in noisy K54 cells.
- **Cross-domain flag:** 21 (Kelly sizing)

### TLOB: Transformer with Dual Attention for Stock Price Trend Prediction with Limit Order Book Data
- **Authors:** Various (recent extension to TLOB family)
- **Year/Source:** 2025 / arXiv 2502.15757
- **URL:** https://arxiv.org/abs/2502.15757
- **Abstract:** Transformer architecture with dual-attention for both temporal and price-level dimensions of LOB data; benchmarks on FI-2010 and modern LSE/NASDAQ datasets. Beats DeepLOB and prior transformer-LOB baselines.
- **Key findings:**
  - Dual-attention (temporal + price-level) outperforms single-axis attention.
  - Latest in the FI-2010-benchmark line; gains incremental but consistent.
  - Demonstrates that LOB-transformers continue to improve year-over-year, supporting attention-style architectures over CNN-LSTM hybrids when scale allows.
- **Relevance to GTOS:** Reinforces dual-attention design as the canonical LOB architecture. Practical for GTOS only post-LOB-data acquisition.
- **Potential hypothesis:** With LOB depth at GTOS XAUUSD, dual-attention TLOB beats DeepLOB by AUC ≥0.02 at next-1-minute direction — i.e., the gains observed in equity LOB transfer to gold LOB.
- **Cross-domain flag:** 06

### Order Flow Imbalance and Stock Price Forecasting (CNN-LSTM hybrid lines)
- **Authors:** Multiple (Ntakaris, Tsantekidis et al)
- **Year/Source:** 2018-2020 / Various venues; representative: Ntakaris et al *Journal of Forecasting* 2018
- **URL:** https://onlinelibrary.wiley.com/doi/10.1002/for.2543
- **Abstract:** Series of papers benchmarking CNN, RNN, and CNN-RNN hybrids on order-flow features for stock prediction. Establishes the FI-2010 dataset as the LOB-ML standard.
- **Key findings:**
  - FI-2010 is the most-cited LOB benchmark; spans 5 Helsinki stocks × 10 days × 10 LOB levels.
  - CNN-RNN hybrids (DeepLOB-style) beat CNN-only and RNN-only.
  - Order-flow imbalance is a stable feature across methods.
- **Relevance to GTOS:** Foundational benchmark. GTOS would want to construct a similar internal benchmark on its tick stream when E24/E26 microstructure work resumes.
- **Potential hypothesis:** A GTOS-internal benchmark constructed from 2026 XAUUSD ticks (M5-aggregated, 5 microstructure levels) reproduces FI-2010's relative-architecture rankings — i.e., DeepLOB > CNN > RNN > MLP, validating the architectural ladder for GTOS's eventual L2-LOB era.
- **Cross-domain flag:** 06

## Section 5 — Text-as-data, financial NLP, FinBERT successors, FinGPT

### BERT: Pre-Training of Deep Bidirectional Transformers for Language Understanding
- **Authors:** Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova
- **Year/Source:** 2019 / NAACL-HLT 2019 (Long Papers): 4171-4186 — arXiv 1810.04805
- **URL:** https://aclanthology.org/N19-1423/ ; https://arxiv.org/abs/1810.04805
- **Abstract:** Introduces BERT — bidirectional transformer pre-trained with masked language modeling and next-sentence prediction. Becomes the standard backbone for downstream NLP tasks including FinBERT.
- **Key findings:**
  - Bidirectional pre-training beats left-to-right (GPT-style) on most NLP benchmarks.
  - Transfer learning works across diverse tasks via simple fine-tuning.
  - Sets the recipe (corpus size + masked LM + transformer) that all subsequent encoder LMs follow.
- **Relevance to GTOS:** Foundational backbone for FinBERT (Araci 2019 + Yang-Uy-Huang 2020) which are GTOS's text-feature anchors. Also the conceptual blueprint for masked self-supervised pre-training on time series (PatchTST extends this).
- **Potential hypothesis:** Self-supervised masked pre-training of a transformer on H1 OHLCV bars across all GTOS instruments (≈ 7M bar-tokens) yields a backbone whose fine-tuning on K54 outperforms K54 v1 LightGBM by ≥0.03 AUC at the F15 H2-2026 holdout — i.e., transfer learning from masked-bar pre-training works at GTOS scale.
- **Cross-domain flag:** 20 (LLM cross-link)

### Text as Data
- **Authors:** Matthew Gentzkow, Bryan T. Kelly, Matt Taddy
- **Year/Source:** 2019 / Journal of Economic Literature 57(3): 535-574 (NBER WP 23276)
- **URL:** https://www.aeaweb.org/articles?id=10.1257/jel.20181020 ; https://web.stanford.edu/~gentzkow/research/text-as-data.pdf
- **Abstract:** Comprehensive survey of statistical methods for using text as input to economic / finance research. Reviews tokenization, dictionary methods, topic models (LDA), and supervised text-as-feature pipelines. Pre-dates BERT-era but methodologically rigorous.
- **Key findings:**
  - Text-as-data is *high-dimensional supervised learning* — same machinery as ML for prices.
  - Loughran-McDonald-style dictionaries are simple but biased; topic models / supervised embeddings are more flexible.
  - Multiple-testing concerns are central — text features explode dimensionality.
- **Relevance to GTOS:** Methodological anchor for text-feature integration. GTOS's KAP research pipeline (cron every 6h weekdays) extracts text-derived findings; the Gentzkow-Kelly-Taddy framework gives the standard cautionary checklist for promoting any text-feature into K54.
- **Potential hypothesis:** Applying the Gentzkow-Kelly-Taddy multiple-testing adjustment to KAP-derived text features halves the number of "significant" features that survive promotion, recovering the gap between KAP backtest and live performance.
- **Cross-domain flag:** 02; 20

### Giving Content to Investor Sentiment: The Role of Media in the Stock Market
- **Authors:** Paul C. Tetlock
- **Year/Source:** 2007 / Journal of Finance 62(3): 1139-1168 (Smith-Breeden Prize)
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2007.01232.x
- **Abstract:** Quantifies WSJ "Abreast of the Market" column sentiment via Harvard-IV-4 dictionary. Finds that high pessimism predicts downward price pressure followed by reversion to fundamentals; extreme pessimism predicts high volume. Foundational paper of textual finance.
- **Key findings:**
  - Daily media pessimism predicts next-day return (negatively in mean) and reversion within ~1 week.
  - Volume responds to extreme tails of pessimism (both ends).
  - Dictionary-based sentiment is enough to find effects, even pre-LM-era.
- **Relevance to GTOS:** Conceptual foundation for the entire text-feature line. The Tetlock-2007 mean-reversion-after-pessimism finding is a candidate "macro mood" feature for K54 v2 if GTOS adds a daily news-sentiment signal.
- **Potential hypothesis:** A daily Tetlock-style sentiment scalar (built from news-feed FinBERT sentiment) on XAU/gold-related news is a usable K54 v2 feature: marginal AUC lift ≥0.01 in macro-event-day cells, null in normal cells.
- **Cross-domain flag:** 17 (behavioral finance / sentiment)

### When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks
- **Authors:** Tim Loughran, Bill McDonald
- **Year/Source:** 2011 / Journal of Finance 66(1): 35-65
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2010.01625.x ; https://sraf.nd.edu/loughranmcdonald-master-dictionary/
- **Abstract:** Demonstrates that ~75% of words flagged as negative by the Harvard Dictionary are not negative in financial context. Develops the Loughran-McDonald financial-domain dictionary (negative, positive, uncertainty, litigious, modal, constraining lists).
- **Key findings:**
  - Domain-specific dictionaries dominate generic-domain dictionaries on financial text.
  - LM-negative-word frequency in 10-K filings predicts post-filing returns and volume.
  - Master Dictionary is the de-facto standard for finance NLP that pre-dates and complements FinBERT.
- **Relevance to GTOS:** The LM dictionary is a baseline-comparator for any FinBERT or LLM-derived sentiment feature. Reinforces that domain adaptation matters more than model size — the same lesson as FinBERT.
- **Potential hypothesis:** A simple Loughran-McDonald-negative-word-count feature on daily news headlines achieves AUC within 0.005 of FinBERT-sentiment for K54 v2 — i.e., the FinBERT-over-LM gain is small relative to the cost of running a transformer in the K54 pipeline.
- **Cross-domain flag:** 17

### A Deep Learning Framework for Financial Time Series Using Stacked Autoencoders and Long-Short Term Memory
- **Authors:** Wei Bao, Jun Yue, Yulei Rao
- **Year/Source:** 2017 / PLOS ONE 12(7): e0180944
- **URL:** https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0180944
- **Abstract:** Three-stage framework: (1) wavelet transform denoising of raw price; (2) stacked-autoencoder hierarchical feature extraction; (3) LSTM forecast of next-day close. Evaluated on six market indices.
- **Key findings:**
  - Wavelet denoising + SAE feature extraction + LSTM beats LSTM-on-raw on 6 of 6 indices.
  - The SAE layer is the largest contributor to the lift — not the wavelet step.
  - One of the most-cited 2017 deep-learning-for-finance papers.
  - **Caveats:** Subsequent independent replications (e.g., Yu et al 2020) raised methodological concerns about look-ahead in the wavelet decomposition (rolling vs full-sample); take results with skepticism.
- **Relevance to GTOS:** Architecture hint for K54 v2: an autoencoder-distilled-feature stage may help. **Cautionary lesson:** Bao et al's wavelet step has been criticized for retrospective leakage — directly mirrors GTOS's vigilance in F11 (decay-vs-methodology disambiguation).
- **Potential hypothesis:** Replacing K54 v1's LightGBM input with autoencoder-distilled features (4-dim bottleneck) lifts AUC ≥0.02 — but rolling vs full-sample wavelet check inflates the apparent lift by ~0.01 if not controlled, repro of the Bao et al methodology issue.
- **Cross-domain flag:** 04 (wavelets); 02 (look-ahead methodology)

## Section 6 — Recent advances 2023-2025: foundation models, LLM-features, and large-scale time series

### FinGPT: Open-Source Financial Large Language Models
- **Authors:** Hongyang Yang, Xiao-Yang Liu, Christina Dan Wang
- **Year/Source:** 2023 / arXiv 2306.06031 (with FinGPT v2 / Democratizing 2307.10485)
- **URL:** https://arxiv.org/abs/2306.06031 ; https://github.com/AI4Finance-Foundation/FinGPT
- **Abstract:** Open-source counterpart to BloombergGPT. Fine-tunes general LLMs (Llama, Falcon) on financial NLP tasks (sentiment, NER, question-answering). Cost <$300 per fine-tune via LoRA.
- **Key findings:**
  - Cheap LoRA fine-tuning on financial data lets open-source LLMs approach BloombergGPT-class performance on sentiment / classification.
  - Internet-scale data pipeline (news, regulatory filings, social media) is the larger contribution than the model itself.
  - Sub-$300-per-fine-tune cost makes domain adaptation accessible.
- **Relevance to GTOS:** Direct dependency for any GTOS Q2-Q3 LLM-derived-feature pipeline. The cost structure (<$300/fine-tune) fits the GTOS Phase-1-subscription budget. FinGPT is the literature anchor for "use open-source LLM as feature engine for K54," distinct from the AI primary-decision-maker (Component 3A, currently Anthropic Sonnet).
- **Potential hypothesis:** A LoRA-fine-tuned FinGPT-Llama on KAP-research-pipeline text outputs a daily sentiment scalar that, when fed to K54 v2, lifts AUC ≥0.015 on macro-event days — making FinGPT-as-feature-engine the highest-ROI Q2 cross-domain integration.
- **Cross-domain flag:** 20 (LLM tri-junction)

### BloombergGPT: A Large Language Model for Finance
- **Authors:** Shijie Wu, Ozan Irsoy, Steven Lu, Vadim Dabravolski, Mark Dredze, Sebastian Gehrmann, Prabhanjan Kambadur, David Rosenberg, Gideon Mann
- **Year/Source:** 2023 / arXiv 2303.17564
- **URL:** https://arxiv.org/abs/2303.17564 ; https://www.bloomberg.com/company/press/bloomberggpt-50-billion-parameter-llm-tuned-finance/
- **Abstract:** 50B-parameter LLM trained on 363B tokens of Bloomberg-proprietary financial text + 345B tokens of general data. Beats general-purpose models on financial NLP tasks while matching them on general benchmarks.
- **Key findings:**
  - Mixed-domain training (proprietary + general) produces a model strong on both axes.
  - 50B parameters is sufficient for finance-NLP SOTA at the 2023-time benchmarks.
  - Proprietary financial text (Bloomberg news, terminal data) is a moat — open-source FinGPT is the response.
- **Relevance to GTOS:** Headline "first LLM for finance" — sets the bar that FinGPT and Anthropic-Sonnet-based agents (GTOS Component 3A) operate against. Not directly callable (proprietary), so reference more than dependency.
- **Potential hypothesis:** An FinGPT-derived feature for K54 captures the *bulk* of BloombergGPT's domain knowledge for sentiment-style tasks (≥0.85 of feature-importance correlation), confirming the open-source approach is sufficient for K54 v2 needs.
- **Cross-domain flag:** 20

### Time-LLM: Time Series Forecasting by Reprogramming Large Language Models
- **Authors:** Ming Jin, Shiyu Wang, Lintao Ma, Zhixuan Chu, James Y. Zhang, Xiaoming Shi, Pin-Yu Chen, Yuxuan Liang, Yuan-Fang Li, Shirui Pan, Qingsong Wen
- **Year/Source:** 2024 / ICLR 2024 — arXiv 2310.01728
- **URL:** https://arxiv.org/abs/2310.01728 ; https://github.com/KimMeen/Time-LLM
- **Abstract:** Reprograms a frozen LLM (Llama, GPT-2) for time-series forecasting by mapping time-series patches to text-token prototypes via a learned alignment layer; adds Prompt-as-Prefix to inject task descriptions. Outperforms specialized forecasters in few-shot/zero-shot.
- **Key findings:**
  - Frozen-LLM body + tiny alignment layer matches or beats fully-trained time-series models on few-shot benchmarks.
  - Prompt-as-Prefix lets the user inject domain priors as natural-language prefix tokens.
  - Demonstrates that LLM weights encode patterns transferrable to time series — a controversial but empirically replicated claim.
- **Relevance to GTOS:** GTOS already has a finance-tuned LLM in Component 3A; Time-LLM is the literature anchor for reusing that LLM as a *forecasting* subsystem rather than an MSO-gate. Promising but data-hungry.
- **Potential hypothesis:** A Time-LLM with the GTOS Component-3A backbone (Sonnet-equivalent) and Prompt-as-Prefix listing GTOS structural state (regime, last OB, last BOS) achieves OOS AUC parity with K54 v1 at zero-shot — but is dominated in cost-per-call by LightGBM, making it useful only as a feature ensemble member, not a primary classifier.
- **Cross-domain flag:** 20 (LLM tri-junction); 04 (cross-time generality)

### Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting
- **Authors:** Kashif Rasul, Arjun Ashok, Andrew Robert Williams, Hena Ghonia, Rishika Bhagwatkar, Arian Khorasani, Mohammad Javad Darvishi Bayazi, George Adamopoulos, Roland Riachi, Nadhir Hassen, Marin Biloš, Sahil Garg, Anderson Schneider, Nicolas Chapados, Alexandre Drouin, Valentina Zantedeschi, Yuriy Nevmyvaka, Irina Rish
- **Year/Source:** 2024 / arXiv 2310.08278 (NeurIPS 2023 workshops; ongoing)
- **URL:** https://arxiv.org/abs/2310.08278 ; https://github.com/time-series-foundation-models/lag-llama
- **Abstract:** Decoder-only Llama-style transformer pre-trained on a multi-domain corpus of univariate time series. Uses lags as covariates. Demonstrates strong zero-shot transfer to held-out datasets — a "foundation model" claim for time series.
- **Key findings:**
  - Lag-as-covariate lets a decoder-only transformer handle arbitrary frequencies.
  - Zero-shot Lag-Llama matches specialized forecasters on many domains.
  - First widely-cited "time-series foundation model"; Chronos and Moirai followed in 2024.
- **Relevance to GTOS:** Time-series foundation models could provide a free off-the-shelf K54-baseline. Lag-Llama is the most-cited open variant; useful as a control before training a custom K54.
- **Potential hypothesis:** Zero-shot Lag-Llama on XAUUSD H1 H1-direction prediction achieves AUC within 0.02 of K54 v1 LightGBM — establishing that the GTOS bespoke ML stack adds at most 0.02 AUC over a 0-cost foundation model, focusing the K54 v2 design on closing that gap.
- **Cross-domain flag:** none

### Chronos: Learning the Language of Time Series
- **Authors:** Abdul Fatir Ansari, Lorenzo Stella, Caner Turkmen, Xiyuan Zhang, Pedro Mercado, et al (Amazon Science)
- **Year/Source:** 2024 / arXiv 2403.07815
- **URL:** https://arxiv.org/abs/2403.07815 ; https://github.com/amazon-science/chronos-forecasting
- **Abstract:** Tokenizes time-series via scaling+quantization into a discrete vocabulary, then trains a T5-family LM (20M-710M params) on the resulting tokens. Pretrained on a large public corpus + Gaussian-process synthetic data; evaluated on 42 datasets with strong zero-shot performance.
- **Key findings:**
  - Treating time-series as a "language" with quantization tokens yields zero-shot performance comparable to fully-trained specialized models on many datasets.
  - Synthetic Gaussian-process pretraining augments real data — useful when real-data domains are imbalanced.
  - T5 family scales gracefully — 20M to 710M params — allowing matched compute to existing time-series methods.
- **Relevance to GTOS:** Like Lag-Llama, a free zero-shot baseline before training a custom K54 v2. The discrete-token approach is conceptually similar to GTOS's binary K54 candidate gate — both reduce the continuous price stream to discrete decisions/tokens.
- **Potential hypothesis:** Zero-shot Chronos-base on XAUUSD H1 next-bar return achieves CRPS within 5% of a fitted Lag-Llama and within 10% of a per-instrument LightGBM regressor — confirming Chronos is the right control benchmark for K54 v2 promotion.
- **Cross-domain flag:** none

### MOIRAI: Unified Training of Universal Time Series Forecasting Transformers
- **Authors:** Gerald Woo, Chenghao Liu, Akshat Kumar, Caiming Xiong, Silvio Savarese, Doyen Sahoo
- **Year/Source:** 2024 / arXiv 2402.02592 (Salesforce Research)
- **URL:** https://arxiv.org/abs/2402.02592 ; https://github.com/SalesforceAIResearch/uni2ts
- **Abstract:** Masked-encoder universal forecaster trained on LOTSA — a 27B-observation multi-domain time-series corpus. Handles arbitrary frequencies, arbitrary covariate counts, and arbitrary distribution choices in zero-shot. Successor v2 transitioned to decoder-only.
- **Key findings:**
  - 27B-observation corpus is the largest open time-series pretraining dataset (~3× Chronos).
  - Probabilistic outputs via flexible mixture-of-distributions head.
  - Beats specialized methods on many domains zero-shot; competitive after fine-tuning.
- **Relevance to GTOS:** A second zero-shot foundation-model control. Probabilistic-output design is closer to GTOS's R-distribution outcome than Lag-Llama's point-forecast head; useful as the exact baseline for the J46-J49 outcome distribution.
- **Potential hypothesis:** Zero-shot MOIRAI-large on the J46-J49 outcome series produces a calibrated R-distribution forecast (CRPS within 10% of fitted) — making it a plausible no-cost J46-J49-policy benchmark before training a custom K54 v2 distribution head.
- **Cross-domain flag:** none

## Section 7 — Classical machine-learning anchors and methodology

### Random Forests
- **Authors:** Leo Breiman
- **Year/Source:** 2001 / Machine Learning 45(1): 5-32
- **URL:** https://link.springer.com/article/10.1023/A:1010933404324 ; https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf
- **Abstract:** Defines random forests as bagged decision trees with random-feature-subset splits; proves Strong Law convergence and gives error bounds in terms of individual-tree strength and inter-tree correlation. Robust to noise and outperforms AdaBoost on many benchmarks.
- **Key findings:**
  - Generalization error converges to a limit as ntree → ∞ — RF does not overfit ntree.
  - Generalization-error bound: RF error ≤ ρ(1 - s²)/s², where ρ = mean inter-tree correlation, s = strength.
  - Out-of-bag error is an unbiased estimate of generalization error — built-in CV.
  - Robustness to noisy features is the main empirical advantage over AdaBoost.
- **Relevance to GTOS:** Foundational for the K54 v1 architecture's RF / GBM family. The strength/correlation bound formalizes the ensemble-diversity argument for the proposed RF+GBM+NN ensemble for K54 v2 (potential hypothesis 19-03). The OOB-as-free-CV is useful for K54 v2 model-selection without the full CPCV cost.
- **Potential hypothesis:** Replacing K54 v1 LightGBM with a Breiman-RF (200 trees, mtry = sqrt(p)) achieves OOS AUC parity within 0.005 — confirming the RF/GBM family difference is small at GTOS data scale, and the choice of LightGBM was driven by speed not accuracy.
- **Cross-domain flag:** none

### Greedy Function Approximation: A Gradient Boosting Machine
- **Authors:** Jerome H. Friedman
- **Year/Source:** 2001 / Annals of Statistics 29(5): 1189-1232
- **URL:** https://projecteuclid.org/journals/annals-of-statistics/volume-29/issue-5/Greedy-function-approximation-A-gradient-boosting-machine/10.1214/aos/1013203451.full
- **Abstract:** Generalizes boosting from squared-error to arbitrary loss via a steepest-descent argument in function space. Develops MART (Multiple Additive Regression Trees) and gradient-boosted decision trees (GBDT). Foundation for XGBoost, LightGBM, CatBoost.
- **Key findings:**
  - Boosting = gradient descent in function space against arbitrary differentiable loss.
  - Stagewise additive expansion of small trees with shrinkage and early stopping → state-of-the-art at writing.
  - Loss families: squared, absolute, Huber, multinomial logistic — all are special cases.
  - Tree-size and learning-rate are the dominant hyperparameters.
- **Relevance to GTOS:** Foundational for K54 v1 LightGBM. The shrinkage + early-stopping discipline is exactly what K54 v1 uses; understanding the function-space-descent framing is required to reason about K54 v2 loss-function alternatives (e.g., focal loss for imbalanced labels).
- **Potential hypothesis:** Replacing K54 v1's binary cross-entropy loss with a focal loss (γ=2, α=0.25) targeted at the rare CANDIDATE class lifts OOS recall by ≥3pp at fixed precision — addressing the imbalance F2 / F15 documented in trending_bull regime cells.
- **Cross-domain flag:** none

### XGBoost: A Scalable Tree Boosting System
- **Authors:** Tianqi Chen, Carlos Guestrin
- **Year/Source:** 2016 / KDD 2016: 785-794
- **URL:** https://arxiv.org/abs/1603.02754 ; https://dl.acm.org/doi/10.1145/2939672.2939785
- **Abstract:** Production-grade GBDT implementation with sparsity-aware split-finding, weighted-quantile sketch for approximate splits, cache-aware access patterns, regularized objective (L1+L2). Scales to billions of examples.
- **Key findings:**
  - Sparsity-aware splitting handles missing values + zero-valued features without imputation.
  - Approximate split-finding via quantile sketch enables distributed training.
  - L1 + L2 regularization in the objective + tree-pruning improves generalization vs vanilla GBDT.
  - One of the most-cited ML papers of the 2010s; the de-facto standard for tabular ML before LightGBM caught up.
- **Relevance to GTOS:** Direct alternative to LightGBM for K54. XGBoost vs LightGBM is a near-tie empirically — but XGBoost handles missing values more gracefully (relevant for GTOS features that go null when MT5 data is incomplete).
- **Potential hypothesis:** Replacing K54 v1 LightGBM with XGBoost (matched hyperparameters) yields AUC within 0.005 — but XGBoost's sparsity-aware splitting makes it more robust to the GTOS pipeline-state-file null-feature events that occasionally drop rows from K54 v1's training set.
- **Cross-domain flag:** none

### LightGBM: A Highly Efficient Gradient Boosting Decision Tree
- **Authors:** Guolin Ke, Qi Meng, Thomas Finley, Taifeng Wang, Wei Chen, Weidong Ma, Qiwei Ye, Tie-Yan Liu
- **Year/Source:** 2017 / NeurIPS 2017
- **URL:** https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree ; https://proceedings.neurips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree.pdf
- **Abstract:** Two key ideas: Gradient-based One-Side Sampling (GOSS) keeps high-gradient instances + samples low-gradient ones; Exclusive Feature Bundling (EFB) merges mutually-exclusive sparse features. Yields 20× training speedup over XGBoost at near-identical accuracy.
- **Key findings:**
  - GOSS reduces sample-effective-N for split-finding without bias.
  - EFB reduces feature dimensionality for sparse high-cardinality settings.
  - Leaf-wise tree growth (vs level-wise) is more efficient at fixed leaves but easier to overfit.
  - Microsoft-shipped, production-deployed; default tree-based ML at most quant shops.
- **Relevance to GTOS:** *The* K54 v1 architecture. Direct dependency. GOSS is the key reason K54 trains in seconds rather than minutes on CPCV folds. Leaf-wise growth is the key overfit risk — K54 v1's `num_leaves` cap is the protection.
- **Potential hypothesis:** Setting K54 v2's `num_leaves` to the GOSS-optimal `2^max_depth - 1` is overfitting in the GTOS small-n regime; the Pareto-optimal value lies at ~30-50% of that, validating Lopez de Prado's small-data regularization caution against modern leaf-wise growth.
- **Cross-domain flag:** none

### The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality
- **Authors:** David H. Bailey, Marcos Lopez de Prado
- **Year/Source:** 2014 / Journal of Portfolio Management 40(5): 94-107 (SSRN 2460551)
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 ; https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- **Abstract:** Defines the deflated Sharpe ratio (DSR) — adjustment of headline Sharpe for (i) number-of-trials selection bias and (ii) non-Gaussian higher moments (skew, kurt). Operationally: at trial-count N, only Sharpe ≥ DSR-threshold is statistically credible.
- **Key findings:**
  - Headline Sharpe of N=1000 backtests has random-best ≈ 1.5 even when true Sharpe is zero.
  - DSR uses skew + kurt to correct the asymptotic SR distribution — fat-tailed returns inflate naive p-values.
  - The single most-skipped piece of any backtest is the trial count.
- **Relevance to GTOS:** Direct dependency for K54 v2 promotion gate. F4 / F5 / F11 documented that GTOS K51 / K50 ML signals fail to replicate under proper Bonferroni — which is exactly the multiple-testing failure DSR addresses. K54 v2 hyperparameter search must report DSR-corrected Sharpe, not raw Sharpe.
- **Potential hypothesis:** Applying DSR to K54 v1's reported Sharpe (with the implicit trial count from CPCV+grid-search ≈ 200 trials) shrinks the headline metric by ≥0.4 Sharpe units, recovering most of the in-sample-vs-promotion-live gap.
- **Cross-domain flag:** 02 (statistical methodology)

### Adaptive Conformal Predictions for Time Series
- **Authors:** Margaux Zaffran, Olivier Féron, Yannig Goude, Julie Josse, Aymeric Dieuleveut
- **Year/Source:** 2022 / ICML 2022 (Proceedings of Machine Learning Research vol 162)
- **URL:** https://proceedings.mlr.press/v162/zaffran22a/zaffran22a.pdf ; https://arxiv.org/abs/2202.07282
- **Abstract:** Extends conformal-prediction interval calibration to time-series with distribution shift via online learning of the alpha-quantile error. Provides finite-sample marginal coverage guarantees.
- **Key findings:**
  - Standard conformal prediction breaks under distribution shift; adaptive variants restore coverage.
  - Online learning of the conformal threshold (Adaptive CP, ACI) via gradient descent gives provable coverage with vanishing regret.
  - Direct relevance to financial time series where distribution shift is the norm.
- **Relevance to GTOS:** Methodology for K54 v2 prediction-uncertainty quantification. Ships pre-computed prediction intervals that maintain coverage *despite* the regime shifts F15 documents. Could be the basis for a "K54 confidence" feature that conditions sizing.
- **Potential hypothesis:** Wrapping K54 v2 LightGBM with adaptive conformal calibration produces 90%-coverage prediction intervals across the F15 H1→H2 boundary with empirical coverage 88-92% — versus naive Gaussian intervals dropping to ~70% coverage. The conformal-coverage feature, multiplied into S79 sizing, lifts realized R/trade by ≥0.02R.
- **Cross-domain flag:** 02 (uncertainty quantification); 21 (sizing)

### Learning Long-Term Dependencies with Gradient Descent Is Difficult
- **Authors:** Yoshua Bengio, Patrice Simard, Paolo Frasconi
- **Year/Source:** 1994 / IEEE Transactions on Neural Networks 5(2): 157-166
- **URL:** https://ieeexplore.ieee.org/document/279181/ ; https://www.comp.hkbu.edu.hk/~markus/teaching/comp7650/tnn-94-gradient.pdf
- **Abstract:** Formal proof that gradient-based learning of recurrent networks fails when long-term dependencies must be captured: gradients vanish or explode exponentially with sequence length. Direct precursor of LSTM (Hochreiter-Schmidhuber 1997).
- **Key findings:**
  - Vanishing/exploding gradient is mathematically inherent to dense recurrent updates — not an implementation issue.
  - Trade-off: efficient gradient learning ⟺ inability to latch info across long lags.
  - Motivates non-gradient methods (ESN) and gradient-friendly architectures (LSTM, attention).
- **Relevance to GTOS:** Theoretical anchor for *why* the LSTM/Transformer family is needed for long-context K54 v2. At GTOS sequence lengths (~64-200 H1 bars), the vanishing-gradient regime is plausible — informs the architecture decision.
- **Potential hypothesis:** A vanilla RNN (no gating) on 200-bar H1 sequences fails to converge to AUC parity with K54 v1 LightGBM, demonstrating the Bengio-Simard-Frasconi gradient-degradation in the GTOS regime — and justifying the LSTM/Transformer complexity choice.
- **Cross-domain flag:** none

### Learning Phrase Representations Using RNN Encoder-Decoder for Statistical Machine Translation (GRU)
- **Authors:** Kyunghyun Cho, Bart van Merriënboer, Caglar Gulcehre, Dzmitry Bahdanau, Fethi Bougares, Holger Schwenk, Yoshua Bengio
- **Year/Source:** 2014 / EMNLP 2014 — arXiv 1406.1078
- **URL:** https://arxiv.org/abs/1406.1078 ; https://aclanthology.org/D14-1179/
- **Abstract:** Introduces the GRU (Gated Recurrent Unit), a simpler gated alternative to LSTM with reset and update gates. Demonstrates encoder-decoder architecture for machine translation that becomes the foundation of seq2seq.
- **Key findings:**
  - GRU has fewer parameters than LSTM, often comparable empirical performance.
  - Encoder-decoder architecture is the seq2seq paradigm — foundation for transformers.
  - On small datasets, GRU sometimes beats LSTM due to fewer parameters.
- **Relevance to GTOS:** GRU is a viable alternative to LSTM in any sequence-model K54 v2. At GTOS data scale, the parameter-efficiency of GRU may matter — fewer free parameters for similar capacity.
- **Potential hypothesis:** A 2-layer GRU on the K54 sequence input matches LSTM AUC within ±0.005 but trains 30% faster — making GRU the preferred recurrent architecture for K54 v2 sequence experiments.
- **Cross-domain flag:** none

### Temporal Fusion Transformers for Interpretable Multi-Horizon Time Series Forecasting
- **Authors:** Bryan Lim, Sercan O. Arik, Nicolas Loeff, Tomas Pfister
- **Year/Source:** 2021 / International Journal of Forecasting 37(4): 1748-1764 (arXiv 1912.09363)
- **URL:** https://arxiv.org/abs/1912.09363 ; https://www.sciencedirect.com/science/article/pii/S0169207021000637
- **Abstract:** Architecture combining gated residual networks, variable-selection networks, multi-head attention, and a quantile-regression head. Designed for interpretable multi-horizon forecasting with mixed inputs (static covariates, known future inputs, observed history).
- **Key findings:**
  - Variable-selection networks make per-feature attention weights interpretable.
  - Multi-quantile output supports prediction-interval generation natively.
  - Beats DeepAR, MQRNN, and Seq2Seq on retail, energy, traffic, financial benchmarks.
  - "Most interpretable" of the strong-performing transformer time-series architectures.
- **Relevance to GTOS:** TFT's combination of (a) variable-selection for interpretability, (b) quantile output for risk, and (c) static-covariate handling for instrument identity makes it a strong K54 v2 architecture candidate when interpretability is a hard constraint (e.g., CEO requires "why" explanations, GTOS doctrine).
- **Potential hypothesis:** A TFT trained on the K54 dataset with instrument as static covariate, regime as past-known input, and microstructure as observed-history achieves AUC parity with LightGBM but produces variable-selection weights that satisfy GTOS-doctrine interpretability — i.e., the same accuracy with usable rationale.
- **Cross-domain flag:** none

### Quant GANs: Deep Generation of Financial Time Series
- **Authors:** Magnus Wiese, Robert Knobloch, Ralf Korn, Peter Kretschmer
- **Year/Source:** 2020 / Quantitative Finance 20(9): 1419-1440 (arXiv 1907.06673)
- **URL:** https://arxiv.org/abs/1907.06673 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2020.1730426
- **Abstract:** GAN-based generator using TCN backbone trained to produce financial time series matching empirical stylized facts (volatility clusters, leverage effects, autocorrelations). Generator is constructed to allow risk-neutral measure transition.
- **Key findings:**
  - TCN-GAN generator captures volatility clustering and leverage effects in synthetic series.
  - Distributional moments at multiple lags align well with empirical moments.
  - Allows risk-neutral measure transition for synthetic-data option pricing.
- **Relevance to GTOS:** GTOS suffers from small sample (few thousand outcome trades). Quant-GAN-style synthetic data could expand K54 training set — but the synthetic-data benefit depends on whether the GAN preserves *predictability* not just stylized moments. Conditional Quant-GANs (regime-conditional) are more relevant.
- **Potential hypothesis:** Augmenting K54 v2 training with regime-conditional Quant-GAN synthetic XAUUSD H1 data (1:1 augmentation ratio) lifts AUC by ≥0.01 in trending_bull cells (where F15 found data is sparsest) but is null or negative on bullish/bearish cells — confirming GAN augmentation helps only in data-poor cells.
- **Cross-domain flag:** 03 (synthetic data / stylized facts)

### Hierarchical Risk Parity (HRP) — Building Diversified Portfolios that Outperform Out of Sample
- **Authors:** Marcos Lopez de Prado
- **Year/Source:** 2016 / Journal of Portfolio Management 42(4): 59-69
- **URL:** https://jpm.pm-research.com/content/42/4/59 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678
- **Abstract:** Replaces Markowitz CLA with hierarchical-clustering-based portfolio allocation. Doesn't require invertible covariance; builds a tree of asset relationships and allocates risk top-down. Outperforms CLA and risk-parity in OOS Monte-Carlo.
- **Key findings:**
  - Bypasses the unstable / concentrated / underperforming triumvirate of CLA failures.
  - HRP allocations are more robust to estimation error in covariance.
  - OOS variance is *lower* than CLA's, even though CLA explicitly minimizes variance.
- **Relevance to GTOS:** The 7-instrument GTOS setup currently uses heuristic per-instrument risk allocation (FN profile 1%/instrument); HRP could build a covariance-aware tree (XAU + USD-block + JPY-cross + index) and allocate risk top-down. Direct candidate for Q3-Q4 portfolio-allocation upgrade.
- **Potential hypothesis:** HRP allocation across the 7 GTOS instruments based on rolling 60-day H1 return correlations produces a position-size schedule that, fed to S79 risk policy, beats the uniform-1% FN baseline by ≥0.5 Sharpe units across Q1-Q2 2026 — primarily by halving allocation to the JPY-cross during DXY-trending regimes.
- **Cross-domain flag:** 13 (factor / correlation); 21 (sizing)

### Triple-Barrier and Meta-Labeling Methods for Financial ML
- **Authors:** Marcos Lopez de Prado (book chapters); replication in Singh-Joubert (Hudson-Thames 2022)
- **Year/Source:** 2018 (originating; book Chapters 3 + 5) / 2022 (independent quantification)
- **URL:** https://hudsonthames.org/wp-content/uploads/2022/04/Does-Meta-Labeling-Add-to-Signal-Efficacy.pdf ; https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/
- **Abstract:** Triple-barrier method labels each trade outcome with first-touched barrier (TP up, SL down, time-out). Meta-labeling trains a secondary classifier (sized) on top of the primary direction signal — separates signal from sizing.
- **Key findings:**
  - Triple-barrier labels match risk-managed outcomes better than fixed-horizon returns.
  - Meta-labeling lifts F1 of strategy by 5-15% in independent replications.
  - Composable: any primary direction signal + any meta-labeling classifier.
- **Relevance to GTOS:** Triple-barrier matches GTOS J46-J49 outcome structure exactly. Meta-labeling is the missing layer between Component 3A AI direction call and Component 4 execution sizing — directly addresses the AUC-vs-realized-R gap (Israel-Kelly-Moskowitz 19-25). Strongly recommended for K54 v2.
- **Potential hypothesis:** Adding K54 v2 as a meta-labeling secondary classifier on top of Component 3A's AI direction call (replacing the rule-based S79 risk-policy gate) lifts mean R/trade by ≥0.1R on the H2-2026 holdout — measuring the "say no when the model is uncertain" effect that meta-labeling formalizes.
- **Cross-domain flag:** 02

### Characteristics Are Covariances: A Unified Model of Risk and Return (IPCA)
- **Authors:** Bryan T. Kelly, Seth Pruitt, Yinan Su
- **Year/Source:** 2019 / Journal of Financial Economics 134(3): 501-524 (NBER WP 24540)
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301151 ; https://www.nber.org/papers/w24540
- **Abstract:** Instrumented Principal Component Analysis (IPCA) — extends PCA so factor loadings are characteristic-conditioned. Five IPCA factors explain the cross-section of stock returns better than existing factor models with vanishingly small "anomaly" intercepts.
- **Key findings:**
  - Characteristics-instrumented loadings reduce model degrees of freedom while improving fit.
  - The 5-factor IPCA model leaves no significant unexplained anomaly intercepts.
  - Characteristics work because they proxy for time-varying betas, not as anomalies — a unified theory.
- **Relevance to GTOS:** GTOS's instrument-level "characteristic" (regime, volatility, KZ) is functionally analogous to firm characteristics; IPCA is a candidate dimensionality-reduction step before LightGBM. Reduces overfit risk vs feeding raw characteristics to a tree.
- **Potential hypothesis:** A 4-factor IPCA on (instrument × regime × kill-zone × volatility) characteristics produces a 4-dim regime embedding that, fed to K54 v2, achieves AUC parity with the raw characteristic-feature LightGBM but with 30% lower variance across CPCV folds — confirming IPCA's bias-variance benefit.
- **Cross-domain flag:** 13 (factor models)

### DeepAR: Probabilistic Forecasting with Autoregressive Recurrent Networks
- **Authors:** David Salinas, Valentin Flunkert, Jan Gasthaus, Tim Januschowski
- **Year/Source:** 2020 / International Journal of Forecasting 36(3): 1181-1191 (arXiv 1704.04110, 2017)
- **URL:** https://arxiv.org/abs/1704.04110 ; https://www.sciencedirect.com/science/article/pii/S0169207019301888
- **Abstract:** Autoregressive RNN trained jointly on a large set of related time series; outputs probability distribution per timestep via parameterized likelihood (Gaussian, negative-binomial). Industry-deployed at Amazon for retail demand.
- **Key findings:**
  - Joint training across related series exploits cross-series patterns.
  - Probabilistic output is essential for inventory / risk-management downstream.
  - Beats classical methods (ARIMA, ETS) on Amazon retail series.
  - Standard baseline for any modern probabilistic time-series forecaster.
- **Relevance to GTOS:** GTOS K54 v1 outputs a binary candidate; a probabilistic-distribution head (per DeepAR) would directly feed S79 sizing. Joint training across 7 GTOS instruments is the same architecture pattern as Sirignano-Cont's pooled-LSTM (19-07).
- **Potential hypothesis:** A DeepAR model on pooled 7-instrument H1 returns achieves CRPS within 5% of per-instrument DeepARs while training in 1/7 the time — making DeepAR the cost-optimal probabilistic baseline for K54 v2's distributional head.
- **Cross-domain flag:** 13

### Reinforcement Learning for Optimized Trade Execution
- **Authors:** Yuriy Nevmyvaka, Yi Feng, Michael Kearns
- **Year/Source:** 2006 / ICML 2006: 673-680
- **URL:** https://www.cis.upenn.edu/~mkearns/papers/rlexec.pdf ; https://dl.acm.org/doi/10.1145/1143844.1143929
- **Abstract:** First large-scale empirical RL application to optimized trade execution; 1.5 years of millisecond NASDAQ data; modified Q-learning. Improves over the Almgren-Chriss baseline.
- **Key findings:**
  - State-space factorization (low-impact decomposition) is essential for RL convergence on real LOB data.
  - Q-learning learns nonlinear execution policies that adapt to market state.
  - Lays the foundation for the entire algorithmic-execution-RL line (Hambly, Cartea, Jaimungal etc).
- **Relevance to GTOS:** GTOS execution is currently rule-based; RL execution is plausible Q3+ candidate. Cross-listed with domain 20 since it's RL — but mentioned here for the data-input architecture (state factorization) which is reusable in supervised K54 v2.
- **Potential hypothesis:** GTOS can apply Nevmyvaka-Feng-Kearns state factorization (limit-order arrival rate × spread × time-to-fill) as 3 additional features to K54 v2; this lifts AUC by ≥0.01 specifically in NY-overlap kill-zones where execution latency is highest.
- **Cross-domain flag:** 20 (RL handoff); 06 (microstructure)

### Deep Learning for Finance: Deep Portfolios
- **Authors:** J. B. Heaton, N. G. Polson, J. H. Witte
- **Year/Source:** 2017 / Applied Stochastic Models in Business and Industry 33(1): 3-12 (arXiv 1605.07230)
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1002/asmb.2209 ; https://arxiv.org/abs/1605.07230
- **Abstract:** Four-step routine (encode, calibrate, validate, verify) using deep autoencoders with sparsity constraints for portfolio construction. Demonstrates deep-encoded portfolios as outperforming benchmark indices.
- **Key findings:**
  - Sparse autoencoder (ρ=0.01) compresses asset returns into a low-dim manifold.
  - Deep-encoded portfolios outperform passive benchmarks on backtest.
  - Among the earliest deep-learning-for-finance papers; cited as a precursor of Gu-Kelly-Xiu.
- **Relevance to GTOS:** Sparse-autoencoder-with-low-rho is an architecture variant for K54 v2 feature distillation (related to 19-16 Autoencoder Asset Pricing). The "encode-calibrate-validate-verify" routine maps to GTOS's K54 v1 → v2 promotion gate procedure.
- **Potential hypothesis:** A sparse autoencoder (ρ=0.01) over the K54 v1 feature set produces a 4-dim bottleneck that, used as input to a smaller LightGBM, reduces variance across CPCV folds by ≥30% while maintaining AUC — confirming the sparsity regularization helps in the small-n regime.
- **Cross-domain flag:** 21 (portfolio)

### Machine Learning in Finance: From Theory to Practice
- **Authors:** Matthew F. Dixon, Igor Halperin, Paul Bilokon
- **Year/Source:** 2020 / Springer textbook
- **URL:** https://link.springer.com/book/10.1007/978-3-030-41068-1 ; https://github.com/mfrdixon/ML_Finance_Codes
- **Abstract:** Comprehensive graduate textbook on ML for finance: cross-sectional supervised, sequential supervised (RNN/CNN), reinforcement learning. Roughly 50% of the book is RL.
- **Key findings:**
  - Unified treatment of econometrics + ML + RL.
  - Strong emphasis on uncertainty quantification (Bayesian methods, conformal).
  - Includes Python TensorFlow code throughout.
  - Most-recent comprehensive textbook covering domain 19 + 20.
- **Relevance to GTOS:** Reference textbook. Useful for cross-checking K54 v2 architecture against canonical taxonomy. The RL chapters bridge to domain 20 — relevant to deep-hedging-as-execution and J46-J49-as-RL framings.
- **Potential hypothesis:** —
- **Cross-domain flag:** 02; 20 (cross-link)

## Section 8 — Recent advances in graph, generative, and hybrid ML for finance

### Temporal Relational Ranking for Stock Prediction (RSR)
- **Authors:** Fuli Feng, Xiangnan He, Xiang Wang, Cheng Luo, Yiqun Liu, Tat-Seng Chua
- **Year/Source:** 2019 / ACM Transactions on Information Systems 37(2) — arXiv 1809.09441
- **URL:** https://arxiv.org/abs/1809.09441 ; https://dl.acm.org/doi/fullHtml/10.1145/3309547
- **Abstract:** Combines temporal LSTM encoders with a temporal-graph-convolution component that models stock-stock relations (sector, supply chain) over time. Frames stock prediction as a ranking task; back-tests on NYSE and NASDAQ.
- **Key findings:**
  - Temporal-graph-convolution captures stock-relation evolution that static graphs miss.
  - Ranking loss aligns better with portfolio-construction goals than per-stock regression.
  - Achieves 98% / 71% return ratio on NYSE / NASDAQ backtest.
  - Foundational paper for the GNN-for-stock-prediction literature.
- **Relevance to GTOS:** GTOS's 7 instruments form a small graph (XAU + DXY-block + JPY-cross + index); a relational graph view could replace the heuristic correlation gate. Most relevant if K54 v2 ever does cross-instrument *ranking* (which-instrument-to-trade-now) rather than per-instrument binary candidate.
- **Potential hypothesis:** A 7-node temporal-graph-convolution K54 v2 variant that ranks instruments by candidate-quality at each H1 close achieves higher mean R/trade by ≥0.05R than per-instrument binary K54 — by allocating capital toward the top-ranked instruments rather than equally.
- **Cross-domain flag:** 13

### Conditional Generators for Limit Order Book Environments: Explainability, Challenges, Robustness (Coletta et al)
- **Authors:** Andrea Coletta et al
- **Year/Source:** 2023 / arXiv 2306.12806 (extends Coletta et al 2022 ICAIF)
- **URL:** https://arxiv.org/abs/2306.12806
- **Abstract:** Conditional GAN trained to generate limit-order-book event sequences emulating multi-agent market behavior. Investigates feature dependencies, explanability, and robustness to out-of-distribution agent strategies.
- **Key findings:**
  - cWGAN can produce realistic LOB sequences for training trading agents.
  - Brittle to OOD external-agent behavior — synthetic data does not generalize when an unmodeled aggressive agent enters.
  - Explainability via feature-attribution shows which input states drive generator decisions.
- **Relevance to GTOS:** Synthetic LOB generation is a candidate for K54 v2 data augmentation under multiple regime transitions. Caveat (OOD brittleness) directly applicable: if Phase 2 spawns a Quant-GAN data augmentation stream, the generator must be tested for robustness to unseen GTOS regime cells (F2 trending_bull cell missing in pre-2026 training data).
- **Potential hypothesis:** A cWGAN trained on the GTOS 2024-2025 H1 outcome series produces synthetic 2026-style data that, when used to augment K54 v2, *worsens* OOS AUC on the F15 H2-2026 holdout — demonstrating Coletta-style OOD brittleness in the GTOS context.
- **Cross-domain flag:** 06

### Sparse Signals in the Cross-Section of Returns
- **Authors:** Alex Chinco, Adam D. Clark-Joseph, Mao Ye
- **Year/Source:** 2019 / Journal of Finance 74(1): 449-492
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12733 ; https://www.nber.org/papers/w23933
- **Abstract:** Applies LASSO to predict 1-minute-ahead returns using lagged cross-section of all stock returns; achieves 23% lift in OOS R² over OLS. Sparse-signal recovery (which lagged stocks predict) is more interpretable than dense regression.
- **Key findings:**
  - LASSO-selected predictors are sparse, time-varying, and economically interpretable (e.g., sector leaders predict followers).
  - 23% OOS R² lift over OLS — large at intraday frequency.
  - Sparse-signal interpretation: at any minute, only a handful of cross-section relationships are predictive; the set of predictors evolves.
- **Relevance to GTOS:** Direct applicability to GTOS's cross-instrument lagged-return question. A LASSO over 7-instrument lagged H1 returns may identify time-varying lead-lag patterns that the heuristic correlation gate misses.
- **Potential hypothesis:** A rolling LASSO on (XAUUSD, DXY, US30, USDJPY, GBPJPY, GBPUSD, XAGUSD) lagged 1-3 H1 returns vs XAUUSD next-H1 return identifies non-zero coefficients in 12-30% of weeks; in those weeks the LASSO-augmented K54 v2 achieves AUC ≥0.02 lift vs LASSO-disabled K54 v2.
- **Cross-domain flag:** 13 (cross-asset); 15 (statarb)

### Deep Learning Volatility: Neural Network Calibration of Rough Volatility Models
- **Authors:** Blanka Horvath, Aitor Muguruza, Mehdi Tomas
- **Year/Source:** 2021 / Quantitative Finance 21(1): 11-27 (arXiv 1901.09647)
- **URL:** https://arxiv.org/abs/1901.09647 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2020.1817974
- **Abstract:** Off-line deep neural network approximation of pricing functionals (rough Bergomi, rough Heston, classical Heston). Online inversion gives full-IV-surface calibration in milliseconds vs minutes for Monte Carlo or finite difference.
- **Key findings:**
  - NN as universal approximator of pricing functional yields ~1000× speedup for rough-volatility calibration.
  - Pricing-function NN can be re-used across many calibration calls.
  - Demonstrates ML as a complement to (not replacement for) classical financial theory.
- **Relevance to GTOS:** GTOS does not price options. However, the *off-line NN as functional approximator* recipe is the same pattern that could be applied if GTOS ever calibrates a rough-volatility model to its return series — relevant for long-term volatility forecasting which feeds into S79 sizing.
- **Potential hypothesis:** Pre-trained NN approximators of rough-Bergomi pricing surfaces, fed XAUUSD H1 implied-volatility data, recover model parameters (Hurst, vol-of-vol) in <50ms — making real-time rough-vol calibration feasible for live GTOS volatility forecasting.
- **Cross-domain flag:** 16 (vol regime)

### Taming the Factor Zoo: A Test of New Factors
- **Authors:** Guanhao Feng, Stefano Giglio, Dacheng Xiu
- **Year/Source:** 2020 / Journal of Finance 75(3): 1327-1370 (NBER WP 25481)
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/jofi.12883 ; https://dachxiu.chicagobooth.edu/download/ZOO.pdf
- **Abstract:** Two-step double-LASSO methodology to test whether a candidate factor adds asset-pricing information beyond a 150-factor benchmark. Few of 150 factors survive — most existing "factors" are redundant.
- **Key findings:**
  - Out of 150 published factors only ~5-10 are statistically novel after Bonferroni-style correction.
  - Double-LASSO controls confounding from non-target factors.
  - Aligns with Lopez-de-Prado deflated-Sharpe critique: most published "alpha" is selection bias.
- **Relevance to GTOS:** GTOS's K54 has roughly 30-50 candidate features; the Feng-Giglio-Xiu-style double-LASSO is the right methodology to identify which features add information beyond the existing K54 v1 baseline. Recommended pre-promotion gate.
- **Potential hypothesis:** Applying the Feng-Giglio-Xiu double-LASSO to the K54 v1 + 12 candidate-new tick-microstructure features identifies 2-4 features as statistically novel; the remaining 8-10 are redundant — focusing K54 v2 development on the marginally-new features.
- **Cross-domain flag:** 02 (multiple-testing); 13 (factors)

### Empirical Properties of Asset Returns: Stylized Facts and Statistical Issues
- **Authors:** Rama Cont
- **Year/Source:** 2001 / Quantitative Finance 1(2): 223-236
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/713665670 ; http://rama.cont.perso.math.cnrs.fr/pdf/empirical.pdf
- **Abstract:** Catalogs 11 stylized facts of asset returns: heavy tails, autocorrelation absence, slow decay of absolute return autocorrelation (volatility clustering), aggregational Gaussianity, leverage effect, volume-volatility correlation, etc. Foundational reference.
- **Key findings:**
  - Heavy-tailed, weakly autocorrelated, but volatility-clustered returns — the canonical pattern.
  - Aggregational Gaussianity: returns become more Gaussian as time-scale lengthens.
  - Multi-scaling and long-memory in volatility — pure GARCH only captures part.
- **Relevance to GTOS:** Foundational reference for any synthetic-data or ML-input feature engineering. The volatility-clustering and heavy-tails findings (ξ=0.35 in `project_distributional_findings`) are the GTOS-validated subset of Cont 2001. Methodology touchstone for evaluating Quant-GAN / diffusion-model synthetic data.
- **Potential hypothesis:** A diffusion-model-generated synthetic XAUUSD H1 series matches Cont's 11 stylized facts at p>0.05 on 9/11 — but fails on volume-volatility correlation and gain-loss asymmetry, identifying these two as the active research targets for synthetic-data quality.
- **Cross-domain flag:** 03 (distributional); 16 (volatility regime)

### Time-Series Forecasting with Deep Learning: A Survey
- **Authors:** Bryan Lim, Stefan Zohren
- **Year/Source:** 2021 / Philosophical Transactions of the Royal Society A 379(2194): 20200209
- **URL:** https://royalsocietypublishing.org/doi/10.1098/rsta.2020.0209 ; https://arxiv.org/abs/2004.13408
- **Abstract:** Comprehensive survey of deep-learning architectures for time-series forecasting: encoder/decoder taxonomy, multi-horizon vs single-step, hybrid statistical-deep models, and applications to decision support.
- **Key findings:**
  - Hybrid models (deep encoder + classical statistical decoder, or vice versa) are SOTA on most benchmarks.
  - Multi-horizon forecasting requires explicit architecture choices (DeepAR, TFT, MQRNN).
  - Pure deep models often underperform hybrids when training data is limited or signal is weak.
- **Relevance to GTOS:** Reference survey. Useful taxonomy for choosing K54 v2 architecture systematically. Argues for hybrid (e.g., LightGBM + LSTM) over pure deep alternatives at GTOS data scale.
- **Potential hypothesis:** —
- **Cross-domain flag:** 02 (methodology)

### Recent Advances in Reinforcement Learning in Finance
- **Authors:** Ben M. Hambly, Renyuan Xu, Huining Yang
- **Year/Source:** 2023 / Mathematical Finance 33(3): 437-503 (arXiv 2112.04553)
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/mafi.12382 ; https://people.maths.ox.ac.uk/~hambly/PDF/Papers/RL-finance.pdf
- **Abstract:** Comprehensive 67-page survey of RL applications in finance: optimal execution, portfolio optimization, option pricing, market making, deep hedging. Reviews algorithmic foundations and empirical case studies.
- **Key findings:**
  - RL handles regime change and partial-observability better than supervised learning when there's enough data.
  - Optimal-execution and market-making are the most-mature RL-in-finance subareas.
  - Deep-hedging (Buehler et al) is a textbook example of RL replacing classical control.
  - Open challenges: sample efficiency, off-policy evaluation, multi-agent generalization.
- **Relevance to GTOS:** Bridge to domain 20 — most papers here are RL-as-trader (domain 20), but the survey is referenced from domain 19 because much of it covers ML methodology that's identical to supervised setups. Direct dependency for any future GTOS RL component.
- **Potential hypothesis:** —
- **Cross-domain flag:** 20 (RL handoff)

### Deep Learning for Event-Driven Stock Prediction
- **Authors:** Xiao Ding, Yue Zhang, Ting Liu, Junwen Duan
- **Year/Source:** 2015 / IJCAI 2015: 2327-2333
- **URL:** https://www.ijcai.org/Proceedings/15/Papers/329.pdf
- **Abstract:** Extracts events from news text via OpenIE, embeds events with neural tensor networks, and uses a CNN to model short + long-term influence on stock prices. Achieves ~6% improvement over baselines on S&P 500 prediction.
- **Key findings:**
  - Event embeddings (subject-verb-object triples) outperform raw bag-of-words for stock prediction.
  - CNN over event sequences captures short + long-horizon influence.
  - One of the founding papers of event-driven deep-learning stock prediction.
- **Relevance to GTOS:** GTOS does not currently extract structured events from news. If KAP research outputs are post-processed into event tuples, the Ding-2015 architecture is the canonical recipe for ingesting them as K54 features.
- **Potential hypothesis:** A simple CNN over event-tuple embeddings (extracted from KAP-pipeline-summarized news on the day of the trade) lifts K54 v2 AUC by ≥0.01 on event-day cells (FOMC, NFP, ECB) but is null on no-event days — motivating an event-aware feature gate in K54 v2.
- **Cross-domain flag:** 17 (sentiment); 11 (CB events)

### Asset Pricing with Omitted Factors
- **Authors:** Stefano Giglio, Dacheng Xiu
- **Year/Source:** 2021 / Journal of Political Economy 129(7): 1947-1990
- **URL:** https://www.journals.uchicago.edu/doi/10.1086/714090 ; https://dachxiu.chicagobooth.edu/download/RP.pdf
- **Abstract:** Proposes a three-pass procedure for estimating risk premia of an observable factor that is robust to omitted factors. Uses PCA on test-asset returns to recover the missing factor space.
- **Key findings:**
  - Standard two-pass risk-premium estimation is biased when relevant factors are omitted.
  - Three-pass procedure (PCA → augmented two-pass) gives consistent estimates under mild conditions.
  - Crucial methodological contribution; complements Feng-Giglio-Xiu (2020).
- **Relevance to GTOS:** Methodology for evaluating any single new K54 v2 feature for "risk premium" interpretation, when the underlying feature space is known to be incomplete (which it always is).
- **Potential hypothesis:** Estimating GTOS feature "risk premia" via the Giglio-Xiu three-pass procedure on K54 v2 features identifies 2-3 features whose risk-premium estimate is statistically nonzero after omitted-factor correction — focusing the K54 v2 promotion candidates.
- **Cross-domain flag:** 13

### Machine Learning vs. Economic Restrictions: Evidence from Stock Return Predictability
- **Authors:** Doron Avramov, Si Cheng, Lior Metzker
- **Year/Source:** 2023 / Management Science 69(5): 2587-2619
- **URL:** https://pubsonline.informs.org/doi/10.1287/mnsc.2022.4449 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3450322
- **Abstract:** Demonstrates that ML-based stock-return signals' profitability concentrates in microcap/distressed/high-volatility cells; excluding these or accounting for trading costs collapses the apparent edge. Direct empirical test of the Israel-Kelly-Moskowitz "AUC-vs-realized-Sharpe gap" thesis.
- **Key findings:**
  - Deep-learning-signal profitability collapses by 50-80% when microcaps + distressed + high-vol stocks are excluded.
  - Trading costs further halve the residual edge.
  - ML signals do successfully identify mispriced stocks — but the realizable alpha is small once frictions are accounted for.
- **Relevance to GTOS:** Cautionary applied paper. Reinforces that K54 v2 must be evaluated under realistic friction (slippage, commission, FN-bro lock-out) and on the *typical* GTOS-trade cell — not on the highest-volatility outliers where the signal looks best. Same lesson as Israel-Kelly-Moskowitz (19-25) but with empirical numbers.
- **Potential hypothesis:** Excluding the ~15% of GTOS trades that fall in extreme-volatility H1 cells (e.g., FOMC days) collapses the apparent K54 v2 lift over K54 v1 from +0.05 AUC to +0.01 AUC — i.e., the mean K54 v2 advantage is concentrated in volatile event days, replicating Avramov-Cheng-Metzker on a single asset basis.
- **Cross-domain flag:** 02; 17

### "Why Should I Trust You?": Explaining the Predictions of Any Classifier (LIME)
- **Authors:** Marco Tulio Ribeiro, Sameer Singh, Carlos Guestrin
- **Year/Source:** 2016 / KDD 2016: 1135-1144
- **URL:** https://arxiv.org/abs/1602.04938 ; https://dl.acm.org/doi/10.1145/2939672.2939778
- **Abstract:** LIME — Local Interpretable Model-agnostic Explanations — fits a simple linear model in the local neighborhood of a prediction to explain it. Predates SHAP and is a sibling tool for ML interpretability.
- **Key findings:**
  - Local linear approximation is faithful in a neighborhood, even when the global model is complex.
  - Model-agnostic — works for trees, NN, ensembles.
  - Predates SHAP (Lundberg-Lee 2017) which subsumes it under Shapley values.
- **Relevance to GTOS:** Companion to SHAP. LIME's local-linear-in-neighborhood is conceptually simpler than Shapley values; useful for K54 v2 trade-by-trade post-hoc explanations to the operator. Often more intuitive than SHAP for one-shot rationale.
- **Potential hypothesis:** For each K54 v2 candidate prediction, LIME identifies 3-4 features whose local linear weight explains ≥80% of the score — providing a CEO-readable rationale that complements SHAP for the GTOS operator dashboard.
- **Cross-domain flag:** 02

### Knowledge-Driven Event Embedding for Stock Prediction
- **Authors:** Xiao Ding, Yue Zhang, Ting Liu, Junwen Duan
- **Year/Source:** 2016 / COLING 2016: 2133-2142
- **URL:** https://aclanthology.org/C16-1201.pdf
- **Abstract:** Extends Ding et al 2015 event-driven prediction by injecting external knowledge-graph triples (Freebase) into the event-embedding learning process; improves prediction accuracy on S&P 500.
- **Key findings:**
  - External knowledge graphs provide priors that improve event-embedding generalization.
  - Knowledge-augmented embeddings outperform plain neural-tensor-network embeddings.
  - Direct precedent for graph + text + price hybrid models.
- **Relevance to GTOS:** GTOS could augment news-event features with external knowledge graph (e.g., FX-pair → CB → policy-rate). At Q3-Q4 timescale this is a candidate K54 v2 enrichment.
- **Potential hypothesis:** —
- **Cross-domain flag:** 17; 11

### Stock Market Prediction via Deep Learning Techniques: A Survey
- **Authors:** Jinan Zou et al
- **Year/Source:** 2022 / arXiv 2212.12717
- **URL:** https://arxiv.org/pdf/2212.12717
- **Abstract:** Recent comprehensive survey of deep-learning methods for stock prediction across architectures (RNN, CNN, transformer, GNN, hybrid) and data modalities (price, news, event, sentiment, social-media).
- **Key findings:**
  - Hybrid GNN-LSTM-Transformer architectures dominate recent leaderboards.
  - Sentiment + price + news triple-modal models beat single-modal.
  - Strong publication bias: most published improvements are within-paper, not cross-paper-replicated.
- **Relevance to GTOS:** Reference survey. Useful for cross-checking K54 v2 architecture against current best-practice in stock-prediction literature.
- **Potential hypothesis:** —
- **Cross-domain flag:** 02

### CatBoost: Unbiased Boosting with Categorical Features
- **Authors:** Liudmila Prokhorenkova, Gleb Gusev, Aleksandr Vorobev, Anna Veronika Dorogush, Andrey Gulin
- **Year/Source:** 2018 / NeurIPS 2018 (arXiv 1706.09516)
- **URL:** https://arxiv.org/abs/1706.09516 ; https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html
- **Abstract:** CatBoost — production gradient-boosting library with two key innovations: ordered boosting (a permutation-based bias-correction) and an algorithm for processing categorical features without target leakage. Yandex's open-source competitor to XGBoost / LightGBM.
- **Key findings:**
  - "Prediction shift" target leakage exists in standard GBDT implementations; ordered boosting fixes it.
  - Built-in categorical-feature handling beats one-hot / target-encoding in noisy settings.
  - Often slightly better than XGBoost/LightGBM out-of-the-box but slower to train.
- **Relevance to GTOS:** Third major GBDT library to consider for K54. CatBoost's categorical-feature handling is relevant for GTOS's instrument-id, regime-label, kill-zone-label features — replacing one-hot encoding with native categorical may lift AUC marginally.
- **Potential hypothesis:** Replacing K54 v1 LightGBM (with one-hot regime encoding) with CatBoost (native categorical regime feature) lifts AUC by ≥0.005 — small but a free improvement, justifying CatBoost as a benchmark in K54 v2 model selection.
- **Cross-domain flag:** none

### Time-MoE: Billion-Scale Time Series Foundation Models with Mixture of Experts
- **Authors:** Xiaoming Shi, Shiyu Wang, Yuqi Nie, Dianqi Li, Zhou Ye, Qingsong Wen, Ming Jin
- **Year/Source:** 2024-2025 / ICLR 2025 Spotlight (arXiv 2409.16040)
- **URL:** https://arxiv.org/abs/2409.16040 ; https://github.com/Time-MoE/Time-MoE
- **Abstract:** Sparse-mixture-of-experts decoder-only transformer for time-series, scaled to 2.4B parameters and trained on Time-300B (300B tokens × 9 domains). Activates only a subset of experts per token for compute efficiency. Beats dense baselines at matched activated-parameter count.
- **Key findings:**
  - Sparse MoE enables 2.4B-parameter time-series models with practical inference cost.
  - Time-300B is the largest reported time-series pretraining corpus.
  - Beats dense baselines (Lag-Llama, Chronos, MOIRAI) across multiple benchmarks at matched activated params.
- **Relevance to GTOS:** Latest-generation foundation model. Most useful as a zero-shot benchmark before training a custom K54 v2 — strictly stronger than Lag-Llama and Chronos.
- **Potential hypothesis:** Zero-shot Time-MoE-base on XAUUSD H1 outperforms zero-shot Lag-Llama by CRPS margin ≥10%, but still lags fitted per-regime LightGBM by 5-10% — indicating that the foundation-model advantage exists but is bounded at GTOS scale.
- **Cross-domain flag:** none

### Dropout as a Bayesian Approximation: Representing Model Uncertainty in Deep Learning
- **Authors:** Yarin Gal, Zoubin Ghahramani
- **Year/Source:** 2016 / ICML 2016 (PMLR vol 48): 1050-1059 (arXiv 1506.02142)
- **URL:** https://proceedings.mlr.press/v48/gal16.html ; https://arxiv.org/abs/1506.02142
- **Abstract:** Reframes dropout in deep neural networks as approximate Bayesian inference in deep Gaussian processes. Allows uncertainty quantification at test time via "MC dropout" — multiple stochastic forward passes.
- **Key findings:**
  - Standard dropout-trained NN ≈ deep GP variational approximation.
  - MC dropout estimates predictive uncertainty at no additional training cost.
  - Becomes the standard cheap-Bayesian-deep-learning technique for finance, medicine, robotics.
- **Relevance to GTOS:** Direct dependency for any deep-learning K54 v2 that needs uncertainty quantification (Q3-Q4 candidate). Adaptive conformal (Zaffran 2022) is the alternative; MC dropout is native to NN architectures.
- **Potential hypothesis:** A K54 v2 LSTM trained with dropout=0.3, evaluated with 50 MC-dropout forward passes per prediction, produces a per-trade epistemic-uncertainty scalar that, multiplied into S79 sizing, lifts realized R/trade by ≥0.01R — comparable to conformal calibration's lift but native to deep architectures.
- **Cross-domain flag:** 02

### Generative Adversarial Networks
- **Authors:** Ian Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, Yoshua Bengio
- **Year/Source:** 2014 / NeurIPS 2014 (arXiv 1406.2661)
- **URL:** https://arxiv.org/abs/1406.2661 ; http://papers.neurips.cc/paper/5423-generative-adversarial-nets.pdf
- **Abstract:** Original GAN paper — adversarial minimax training of generator vs discriminator. Foundation for all subsequent GAN work including Quant GANs and conditional generators for LOB.
- **Key findings:**
  - Adversarial loss enables learning generative distributions implicitly without explicit likelihood.
  - Mode collapse and training instability are inherent to vanilla GANs — addressed in Wasserstein-GAN and successors.
  - Established the generative-model paradigm that diffusion models extend.
- **Relevance to GTOS:** Foundational anchor for all generative-model approaches to financial data simulation (Wiese et al 2020, Coletta et al 2023). Reference more than direct dependency.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

---

## Section 9 — Cross-paper synthesis: most-relevant for GTOS K54 v2

### Top 5 papers for K54 v2 architecture decision (per-regime LightGBM successor)

1. **Gu-Kelly-Xiu 2020** (19-01) — establishes that shallow trees + tight regularization beat deep NN at small-to-medium-n financial panels; directly supports per-regime LightGBM as the right v2 choice. *Counterpoint:* Chen-Pelger-Zhu 2024 (19-23) shows adversarial deep nets can beat tree models when GAN-style regularization + macro-state encoder are added.
2. **Lopez de Prado 2018 + 2020 + 2014** (19-02, 19-24, 19-48) — purged-CPCV, meta-labeling, triple-barrier, deflated-Sharpe; the entire methodology stack for K54 v2 promotion gates. **F4/F5/F11/F16's "fails to replicate under proper Bonferroni" findings are precisely the failures DSR + CPCV + meta-labeling are designed to prevent.**
3. **Zeng et al 2023 — DLinear** (19-22) — *contrarian.* Simple linear baselines beat transformers on most LTSF benchmarks. K54 v2 must benchmark against DLinear before choosing any deeper architecture.
4. **Chen-Pelger-Zhu 2024 — Deep Learning in Asset Pricing** (19-23) — RNN macro-encoder is the literature anchor for the F15-finding that regime is the load-bearing decay axis. K54 v2 should learn its regime embedding rather than use rule-based v1 H4-swing.
5. **Israel-Kelly-Moskowitz 2020 + Avramov-Cheng-Metzker 2023** (19-25, 19-71) — both quantify the AUC-vs-realized-R gap (which the GTOS B7-vs-realized-R disconnect repro'd). K54 v2 must be evaluated under realistic friction + on the typical-cell, not the highest-volatility outliers.

### Top 5 papers for Q2 sequence-model exploration

1. **Vaswani et al 2017 — Attention Is All You Need** (19-05) — foundational anchor; GTOS data-hunger is the central caution.
2. **Nie et al 2023 — PatchTST** (19-19) — patch-tokenization at GTOS scale yields short sequences below the data-hunger threshold; channel-independent design fits the multi-instrument GTOS panel.
3. **Bai-Kolter-Koltun 2018 — TCN** (19-15) — middle ground between LightGBM and Transformer; favorable parameter/receptive-field ratio at GTOS data scale; parallel training enables fast batch backtests.
4. **Lim-Arik-Loeff-Pfister 2021 — TFT** (19-52) — *interpretable* alternative; variable-selection networks satisfy GTOS doctrine for "why" rationale.
5. **Zhou et al 2024-2025 — Time-MoE** + **Lag-Llama / Chronos / MOIRAI** (19-79, 19-41, 19-42, 19-43) — zero-shot foundation-model controls before any custom Q2 training.

### Surprise / counterintuitive finding
**Zeng et al 2023 (DLinear)** is the single biggest surprise. The published claim that simple linear models with seasonal-trend decomposition outperform Informer/Autoformer/FEDformer on 9 LTSF benchmarks directly challenges the "more complex is better" prior that the rest of the deep-time-series literature implies. PatchTST and iTransformer have since closed the gap, but the basic Occam-test discipline this paper enforces is exactly the hygiene K54 v2 needs to avoid the GTOS B7 / F4 / F5 / F11 reproducibility failures. **A linear-baseline DLinear must be on the K54 v2 shortlist alongside the LightGBM defender.**

### Cross-domain handoffs

| To domain | Papers | Reason |
|-----------|--------|--------|
| **02 statistical methodology** | 19-02 (CPCV), 19-48 (DSR), 19-22 (Occam baseline), 19-49 (conformal), 19-25, 19-71 (AUC-Sharpe gap), 19-65 (double-LASSO), 19-67 (survey), 19-72 (LIME) | All proper-OOS / multiple-testing / interpretability methodology naturally lives in domain 02. |
| **20 RL + LLM agents** | 19-27 (Deep Hedging — RL framing), 19-58 (Nevmyvaka-Feng-Kearns), 19-68 (RL survey), 19-33 (BERT — LLM backbone), 19-38 (FinGPT), 19-39 (BloombergGPT), 19-40 (Time-LLM) | Domain-19 owns LLM-as-feature-engine; domain-20 owns LLM-as-agent. The LLM-tri-junction (17/19/20) papers are explicitly cross-listed. |
| **13 cross-asset / factor** | 19-01, 19-16, 19-23, 19-29 (conditional CNN), 19-30 (portfolio), 19-54 (HRP), 19-56 (IPCA), 19-57 (DeepAR pooled), 19-61 (RSR-graph), 19-63 (LASSO 1-min), 19-65 (factor zoo), 19-70 (omitted factors) | Cross-instrument / factor literature naturally bridges to domain 13. |
| **05 regime detection** | 19-23 (RNN macro-encoder), 19-20 (TimesNet anomaly), F-15 ML successors | Regime-aware ML feeds back into regime-detection methodology. |
| **06 microstructure** | 19-06, 19-07, 19-09, 19-28, 19-31, 19-32, 19-58, 19-62 | Entire LOB-ML subliterature; domain 06 owns the data, domain 19 owns the architectures. |
| **04 wavelets / multitimeframe** | 19-18 (FEDformer wavelet), 19-37 (SAE+wavelet+LSTM), 19-40 (Time-LLM cross-time) | Frequency-domain ML cross-listed. |
| **17 sentiment / behavior** | 19-11, 19-12 (FinBERT), 19-35 (Tetlock), 19-36 (LM dictionary), 19-69, 19-73 (event embedding) | Text-as-data + sentiment papers. |
| **03 distributional / 16 volatility** | 19-53 (Quant GAN), 19-66 (Cont stylized facts), 19-64 (rough vol NN calibration) | Synthetic-data / volatility-model NN papers. |
| **21 Kelly / sizing** | 19-30 (deep portfolio Sharpe), 19-49 (conformal sizing), 19-54 (HRP), 19-59 (deep portfolios), 19-26 (Deep BSDE for SL/TP) | Sizing / Kelly papers anchored in K54 outputs feeding S79 / sizing logic. |
| **15 statarb / mean reversion** | 19-03 (Krauss-Do-Huck), 19-08 (Fischer-Krauss LSTM), 19-63 (sparse signals) | Statistical-arbitrage application of ML. |

### Anti-patterns surfaced by this catalog (confirmation of GTOS doctrine)

1. **Look-ahead in wavelet / decomposition pipelines** — Bao-Yue-Rao 2017 (19-37) is the cautionary anchor; criticized for retrospective-leakage in subsequent replications. Mirrors GTOS's F11 decay-vs-methodology disambiguation discipline.
2. **Backtest overfitting** — Bailey-Lopez de Prado 2014 (19-48) DSR is the explicit-correction tool. F4/F5/F11/F16's "does not replicate under proper Bonferroni" findings are exactly this class.
3. **Data-hunger of transformers at small-n** — Vaswani 2017 (19-05) + Bengio-Simard-Frasconi 1994 (19-50) + Zeng et al 2023 (19-22) — three papers triangulate the cautionary lesson that complex sequence architectures are not free at GTOS scale.
4. **OOD brittleness of synthetic data** — Coletta et al 2023 (19-62) specifically calls out that GAN-trained LOB simulators fail when external aggressive agents create novel states. Direct analog for any GTOS Quant-GAN augmentation: must test on F15 H2-2026 cells that the generator has not seen.
5. **AUC-vs-realized-R gap** — Israel-Kelly-Moskowitz 2020 (19-25) + Avramov-Cheng-Metzker 2023 (19-71) — concentrating profitability in extreme cells is a known artifact, not unique to GTOS B7.
6. **Within-paper replication only** — Zou et al 2022 survey (19-74) and the broader Stock Market Prediction literature have a strong publication bias; cross-paper replication is rare. Reinforces "do not believe a single-paper claim" doctrine.



