# Phase 1 -- LLM vs Simple Statistical Model Literature Search Results (Q-3.7)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** The existential question -- can logistic regression or XGBoost on 7 key features match or beat the LLM's 65% WR at n=129?
**Total papers found:** 14 (after quality filter)
**Papers promoted (testable on GTOS data):** 10
**Papers rejected:** 4 (MDPI, no OOS, or tangential)
**Critical gaps identified:** 2

---

## Table of Contents

1. [Summary](#summary)
2. [Q-3.7: LLM vs Simple Statistical Model](#q-37)
3. [Cross-Question Synthesis](#synthesis)
4. [Specific GTOS Implications](#gtos-implications)
5. [Rejected Papers](#rejected)

---

<a id="summary"></a>
## 1. Summary

### The Core Question

GTOS uses Claude Sonnet ($60/month) to evaluate OB-retest setups by reading a ~95-field Market State Object (MSO). The MSO contains both tabular features (touch count, premium/discount ratio, volume ratio, H4 alignment) and spatial/structural data (relative positions of OBs, FVGs, BOS levels, swing points). If XGBoost or logistic regression on the 7 key tabular features achieves comparable WR, the LLM component is unjustified.

### Per-Source Breakdown

| Source | Papers | Key Verdict |
|--------|--------|-------------|
| Tabular DL benchmarks | 6 | Tree-based models (XGBoost, CatBoost) dominate deep learning AND LLMs on pure tabular classification with sufficient samples. At n=129, this is borderline -- TabPFN or well-tuned trees should match ~65% WR if the signal is purely in the 7 features. |
| LLM-on-tabular studies | 4 | LLMs competitive only in few-shot (<8 samples) or zero-shot settings. With 129 labeled trades, XGBoost has enough data to learn any tabular pattern the LLM captures. |
| LLM spatial/structural reasoning | 2 | LLMs struggle with spatial reasoning but can process compositional multi-feature descriptions. GTOS's MSO is a hybrid: partly tabular, partly spatial narrative. This is the crux of the justification question. |
| Financial ML benchmarks | 2 | XGBoost consistently beats LLMs on structured financial data. No paper tests LLM spatial reasoning on price structure specifically. |

### Critical Gaps

1. **No paper tests LLM spatial reasoning on price structure evaluation.** The closest analogue is candlestick chart pattern recognition via CNNs, but no study compares LLM text-based spatial evaluation of OB/FVG/BOS geometry against tabular classifiers on the same data.
2. **No paper benchmarks LLMs against tree models at exactly n=100-200 on financial classification.** The few-shot literature (Hegselmann 2023, Huertas 2024) uses different domain data. The financial ML literature (Gu et al. 2020) uses large samples.

### Cross-References from Previous Searches

| Paper | Previous Search | New Relevance |
|-------|----------------|---------------|
| Hegselmann et al. 2023 (TabLLM) | Q-1.5 (feature count) | Directly relevant -- LLM competitive in few-shot but GTOS has 129 samples, past the crossover |
| Bailey et al. 2014 (PBO) | Q-1.5 (feature count) | Any feature selection for XGBoost baseline must be PBO-tested |
| Gu, Kelly, Xiu 2020 | Q-1.5 (feature count) | Shows tree models capture nonlinear interactions in financial data at scale; question is whether this holds at n=129 |

---

<a id="q-37"></a>
## 2. Q-3.7: LLM vs Simple Statistical Model

**Question:** Does the LLM component of GTOS provide value over a simple statistical model (logistic regression, XGBoost) trained on the same 7 key features?

**Verdict:** The tabular data literature overwhelmingly favors tree-based models over LLMs for pure tabular classification. However, GTOS's task is NOT pure tabular classification -- it involves spatial reasoning over price structure geometry (relative positions of OBs, FVGs, candle bodies, and structural breaks). No paper directly tests this hybrid task. The LLM's justification rests on this spatial reasoning component, which cannot be easily reduced to 7 tabular features. The empirically testable question is: does an XGBoost trained on 7 features achieve >= 62% WR OOS? If yes, the LLM is overhead. If no, the spatial reasoning adds value.

**COVERAGE: PARTIAL** -- Strong evidence on the tabular side; zero evidence on LLM spatial reasoning for price structure evaluation.

---

### Paper 1: Why Do Tree-Based Models Still Outperform Deep Learning on Tabular Data?

**Authors:** Leo Grinsztajn, Edouard Oyallon, Gael Varoquaux | **Year:** 2022 | **Source:** NeurIPS 2022 (Datasets and Benchmarks Track)
**Quality Tier:** 1 | **Citations:** ~1,200+
**Task/domain tested:** 45 datasets from varied domains, medium-sized (~10K samples)
**OOS validation:** Yes (standard train/test splits with extensive hyperparameter search, 20,000 GPU-hours)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.7

**Key finding:** Tree-based models (XGBoost, Random Forest, GBDTs) remain state-of-the-art on medium-sized tabular data (~10K samples), even without accounting for their superior speed. Three specific inductive biases explain this: (1) **robustness to uninformative features** -- trees naturally ignore irrelevant columns; (2) **preservation of data orientation** -- trees respect the natural structure of tabular features, unlike neural nets that learn rotationally invariant representations; (3) **ability to learn irregular (non-smooth) functions** -- decision boundaries in tabular data are often sharp/discontinuous, which trees model natively but neural nets smooth over.

**Key equation / method:** Empirical benchmark across 45 datasets with controlled hyperparameter search. No single equation -- the contribution is the identification of three inductive bias gaps.

**Testability on GTOS data:** High -- directly testable. Train XGBoost on the 7 key features (OB present, displacement quality, FVG present, touch count, premium/discount, H4 alignment, volume ratio) and compare OOS WR to the LLM's 65%.

**GTOS-specific note:** At n=129, GTOS is below the "medium-sized" threshold of ~10K. However, the inductive bias findings hold at any sample size. The critical caveat: this paper tests pure tabular features. GTOS's MSO contains spatial/structural information (e.g., "OB is at 61.8% fib level," "FVG overlaps with OB zone") that may not be reducible to 7 columns.

---

### Paper 2: Deep Neural Networks and Tabular Data: A Survey

**Authors:** Vadim Borisov, Tobias Leemann, Kathrin Sessler, Johannes Haug, Martin Pawelczyk, Gjergji Kasneci | **Year:** 2022 | **Source:** IEEE Transactions on Neural Networks and Learning Systems (arXiv 2110.01889)
**Quality Tier:** 1 | **Citations:** ~800+
**Task/domain tested:** Survey across multiple domains and datasets
**OOS validation:** N/A (survey paper, reviews OOS methodology of cited work)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.7

**Key finding:** Comprehensive survey concluding that "algorithms based on gradient-boosted tree ensembles still mostly outperform deep learning models on supervised learning tasks" for tabular data. Categorizes DNN approaches into three groups: data transformations (encoding tabular data for neural nets), specialized architectures (attention-based, tree-mimicking), and regularization models. The survey finds that despite 50+ proposed DNN architectures for tabular data, none consistently beats well-tuned GBDTs.

**Key equation / method:** Taxonomy of approaches rather than a single method. Key insight: the "tabular data problem" is fundamentally different from image/text because features are heterogeneous (mixing categorical, ordinal, continuous), there is no spatial/temporal locality to exploit, and feature interactions are irregular.

**Testability on GTOS data:** Medium -- the survey's conclusions support testing XGBoost as a baseline but do not provide a specific methodology. The heterogeneous-features finding is relevant: GTOS's 7 features are indeed heterogeneous (binary, ordinal, continuous).

---

### Paper 3: Tabular Data: Deep Learning is Not All You Need

**Authors:** Ravid Shwartz-Ziv, Amitai Armon | **Year:** 2022 | **Source:** Information Fusion, Vol. 81, pp. 84-90
**Quality Tier:** 1 | **Citations:** ~900+
**Task/domain tested:** Multiple benchmark datasets used in the papers proposing deep tabular models
**OOS validation:** Yes (uses the same evaluation protocols as the original DL papers)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.7

**Key finding:** XGBoost outperforms recently proposed deep learning models for tabular data across all tested datasets, including the datasets used in the papers that proposed the deep models. XGBoost also requires much less hyperparameter tuning. However, an ensemble of deep models WITH XGBoost outperforms XGBoost alone -- suggesting DL captures complementary signal.

**Key equation / method:** Direct comparison using identical train/test splits. The ensemble finding is operationally relevant: f_ensemble = alpha * f_XGB + (1-alpha) * f_DL, where optimal alpha is estimated on validation data.

**Testability on GTOS data:** High -- directly testable. The ensemble finding is particularly relevant: even if XGBoost matches the LLM on tabular features, the LLM might capture complementary spatial/structural signal that an ensemble would exploit.

**GTOS-specific note:** The ensemble finding maps to a potential architecture: use XGBoost as a first-pass filter on 7 features, then use the LLM only on the subset that passes. This could reduce API costs by 90% while retaining the spatial reasoning benefit.

---

### Paper 4: When Do Neural Nets Outperform Boosted Trees on Tabular Data?

**Authors:** Duncan McElfresh, Sujay Khandagale, Jonathan Valverde, Vishak Prasad C, Benjamin Feuer, Chinmay Hegde, Ganesh Ramakrishnan, Micah Goldblum, Colin White | **Year:** 2023 | **Source:** NeurIPS 2023 (Datasets and Benchmarks Track)
**Quality Tier:** 1 | **Citations:** ~250+
**Task/domain tested:** 19 algorithms across 176 datasets
**OOS validation:** Yes (standardized splits, metafeature analysis)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.7

**Key finding:** The debate between NNs and GBDTs is overstated. For "a surprisingly high number of datasets, either the performance difference between GBDTs and NNs is negligible, or light hyperparameter tuning on a GBDT is more important" than algorithm choice. GBDTs are specifically better at handling skewed/heavy-tailed feature distributions and dataset irregularities. One exception: TabPFN outperforms all methods on average for datasets with up to 3,000 training samples.

**Key equation / method:** Metafeature analysis to identify dataset characteristics that predict whether NNs or GBDTs will win. Released the TabZilla Benchmark Suite (36 challenging datasets).

**Testability on GTOS data:** High -- GTOS's n=129 falls within TabPFN's optimal range (<3,000 samples). The metafeature analysis could predict whether GTOS's dataset characteristics favor trees or NNs. Key question: do GTOS features have skewed/heavy-tailed distributions? (If yes, GBDTs should win.)

**GTOS-specific note:** Touch count is heavily right-skewed (mostly 1-2, rarely 3+). Volume ratio can be heavy-tailed. These characteristics favor GBDTs according to this paper.

---

### Paper 5: TabPFN: A Transformer That Solves Small Tabular Classification Problems in a Second

**Authors:** Noah Hollmann, Samuel Muller, Katharina Eggensperger, Frank Hutter | **Year:** 2022/2025 | **Source:** ICLR 2023 (v1); Nature (v2, 2025)
**Quality Tier:** 1 | **Citations:** ~500+ (ICLR version); Nature version published Jan 2025
**Task/domain tested:** OpenML-CC18 benchmark (18 datasets meeting size criteria), 67 additional small datasets; Nature version: datasets up to 10,000 samples
**OOS validation:** Yes (standard benchmark evaluation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.7

**Key finding (ICLR 2023 / v1):** TabPFN, a transformer trained on 100M synthetic datasets via in-context learning, "clearly outperforms boosted trees" on the OpenML-CC18 benchmark for datasets with up to 1,000 training samples. Achieves 230x speedup on CPU vs AutoML. Limited to 1,000 samples, 100 numerical features, 10 classes.

**Key finding (Nature 2025 / v2):** TabPFN v2 outperforms all previous methods on datasets with up to 10,000 samples. In 2.8 seconds, TabPFN outperforms an ensemble of the strongest baselines tuned for 4 hours. Requires only 50% of the data to achieve the same accuracy as the previously best model.

**Key equation / method:** Prior-Data Fitted Network: trains a transformer to approximate Bayesian inference by meta-learning on synthetic datasets drawn from a causal prior. At inference, the entire training set is fed as context, and predictions are made via a single forward pass (no gradient updates).

**Testability on GTOS data:** High -- GTOS has 129 samples, 7 features, binary classification (CANDIDATE vs NO_TRADE). This falls squarely in TabPFN's sweet spot (<1,000 samples). TabPFN could be the strongest baseline to compare against the LLM.

**GTOS-specific note:** TabPFN is a transformer doing in-context learning on tabular data -- conceptually similar to what the LLM does, but purpose-built for tabular classification. If TabPFN achieves >= 62% WR on the 7 features, the LLM's tabular understanding is matched by a free, sub-second model. The remaining question would be whether the LLM adds value through spatial reasoning on the full MSO.

---

### Paper 6: Revisiting Deep Learning Models for Tabular Data

**Authors:** Yury Gorishniy, Ivan Rubachev, Valentin Khrulkov, Artem Babenko | **Year:** 2021 | **Source:** NeurIPS 2021
**Quality Tier:** 1 | **Citations:** ~1,100+
**Task/domain tested:** Multiple benchmark tabular datasets
**OOS validation:** Yes (standard benchmark protocols)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.7

**Key finding:** Proposes FT-Transformer, a simple Transformer adaptation for tabular data that tokenizes each feature and uses self-attention to model feature interactions. FT-Transformer is competitive with GBDTs across all tasks (unlike ResNet, which wins only on some). Key insight: "there is still no universally superior solution" -- FT-Transformer closes the gap but does not consistently beat GBDTs.

**Key equation / method:** Feature Tokenizer + Transformer: each feature x_i is embedded into a d-dimensional token via a learned linear projection, then processed by standard Transformer layers. Self-attention captures pairwise feature interactions.

**Testability on GTOS data:** Medium -- FT-Transformer is more complex than needed for 7 features at n=129. However, the attention mechanism could reveal which feature interactions matter (e.g., touch_count x premium_discount, or FVG_present x H4_alignment).

---

### Paper 7: Gradient Boosting Trees and Large Language Models for Tabular Data Few-Shot Learning

**Authors:** Carlos Huertas | **Year:** 2024 | **Source:** FedCSIS 2024 Data Mining Competition (1st Place)
**Quality Tier:** 3 (competition paper, not peer-reviewed journal)
**Task/domain tested:** FedCSIS 2024 challenge dataset
**OOS validation:** Partial (competition leaderboard evaluation)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.7

**Key finding:** TabLLM (LLM fine-tuned on serialized tabular data) shows advantages over GBDT only with 8 or fewer labeled examples. Above ~8 samples, GBDT becomes competitive at a fraction of the runtime. For larger datasets, few-shot learning still improves ensemble diversity when combined with ExtraTrees.

**Key equation / method:** Comparison of TabLLM serialization vs LightGBM with forced node splitting for limited samples.

**Testability on GTOS data:** Medium -- The 8-sample crossover point is critical. GTOS has 129 labeled trades, which is well above the threshold where GBDTs should dominate. This paper supports the hypothesis that XGBoost should match or beat the LLM on pure tabular features at n=129.

---

### Paper 8: Large Language Models versus Classical Machine Learning: Performance in COVID-19 Mortality Prediction Using High-Dimensional Tabular Data

**Authors:** Ghaffarzadeh-Esfahani et al. (40+ authors) | **Year:** 2025 | **Source:** Scientific Reports 15, 42712 (Nature portfolio)
**Quality Tier:** 2 | **Citations:** New (2025)
**Task/domain tested:** COVID-19 mortality prediction, 9,134 patients across 4 hospitals, high-dimensional tabular data
**OOS validation:** Yes (internal + external validation across hospital sites)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.7

**Key finding:** XGBoost achieved F1=0.87 (internal) and F1=0.83 (external). GPT-4 zero-shot achieved F1=0.43. Fine-tuned Mistral-7b achieved F1=0.74 on external validation. Classical ML outperformed LLMs by 0.09-0.44 F1 points on structured tabular data. Fine-tuning substantially improved LLM performance but did not close the gap.

**Key equation / method:** Direct comparison of zero-shot LLMs, fine-tuned LLMs, and classical ML (XGBoost, RF, SVM) on identical data splits.

**Testability on GTOS data:** Medium -- Different domain (medical vs financial), but the finding that XGBoost beats GPT-4 by 0.44 F1 points on structured tabular data is striking. The gap narrows with fine-tuning, but GTOS does not fine-tune Sonnet.

**GTOS-specific note:** GTOS uses Sonnet in zero-shot/few-shot mode (prompt + MSO, no fine-tuning). The COVID-19 study shows zero-shot GPT-4 achieves only 49% of XGBoost's F1 on pure tabular data. This is the strongest evidence against the LLM component -- IF the task were purely tabular.

---

### Paper 9: LIFT: Language-Interfaced Fine-Tuning for Non-Language Machine Learning Tasks

**Authors:** Tuan Dinh, Yuchen Zeng et al. | **Year:** 2022 | **Source:** NeurIPS 2022
**Quality Tier:** 1 | **Citations:** ~300+
**Task/domain tested:** Multiple low-dimensional classification and regression tasks
**OOS validation:** Yes (standard benchmarks)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.7

**Key finding:** Fine-tuned GPT-2 on serialized tabular data (converting rows to natural language sentences) performs comparably to the best baselines on low-dimensional classification tasks. The approach works by converting datasets into sentences and fine-tuning the pretrained LM. Performance is competitive but does not consistently beat XGBoost/Random Forest.

**Key equation / method:** Serialization: each row becomes "feature_1 is value_1, feature_2 is value_2, ..., the label is ___." Fine-tuning predicts the masked label.

**Testability on GTOS data:** Low -- GTOS does not fine-tune the LLM. LIFT's finding supports the idea that LLMs can process tabular data, but the fine-tuning requirement makes it architecturally different from GTOS's zero-shot approach.

---

### Paper 10: Well-tuned Simple Nets Excel on Tabular Datasets

**Authors:** Arlind Kadra, Marius Lindauer, Frank Hutter, Josif Grabocka | **Year:** 2021 | **Source:** NeurIPS 2021
**Quality Tier:** 1 | **Citations:** ~500+
**Task/domain tested:** 40 tabular datasets
**OOS validation:** Yes (standard benchmark splits)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.7

**Key finding:** Well-regularized plain MLPs (with a "cocktail" of 13 regularization techniques) significantly outperform state-of-the-art specialized neural architectures AND outperform XGBoost on many datasets. The key is not architecture complexity but regularization.

**Key equation / method:** Joint optimization over 13 regularizers: dropout, weight decay, batch normalization, learning rate schedules, data augmentation, label smoothing, cutout, mixup, etc. The optimal combination varies per dataset.

**Testability on GTOS data:** Low -- With n=129, the regularization cocktail approach risks overfitting the hyperparameter search itself. More relevant as a methodological caution: any comparison must use well-tuned baselines, not default-parameter XGBoost.

---

### Paper 11: LLMs on Tabular Data: Prediction, Generation, and Understanding -- A Survey

**Authors:** Xi Fang, Weijie Xu, Fiona Anting Tan, Jiani Zhang, Ziqing Hu et al. | **Year:** 2024 | **Source:** Transactions on Machine Learning Research (TMLR)
**Quality Tier:** 2 | **Citations:** ~150+
**Task/domain tested:** Survey across multiple domains
**OOS validation:** N/A (survey)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.7

**Key finding:** Comprehensive survey of LLMs applied to tabular data across prediction, generation, and understanding tasks. Key methodological insight: serialization format (free-form text, HTML, CSV, JSON) has a direct impact on LLM performance on tabular tasks. LLMs' primary advantage is in zero-shot/few-shot settings and when semantic feature names provide useful prior knowledge.

**Key equation / method:** Taxonomy of serialization approaches and their performance impact.

**Testability on GTOS data:** Medium -- GTOS's MSO is already serialized as structured JSON. The survey suggests that feature naming matters: "ob_zone_present" carries semantic meaning that a pure numerical encoding would lose. This is a genuine LLM advantage.

**GTOS-specific note:** The semantic serialization advantage is real for GTOS. Feature names like "displacement_quality," "premium_discount_zone," and "touch_count" carry domain knowledge that the LLM can leverage. XGBoost sees columns 0-6; the LLM sees named concepts with domain semantics.

---

### Paper 12: Is Deep Learning Finally Better Than Decision Trees on Tabular Data?

**Authors:** Guri Zabергja, Arlind Kadra, Christian M. M. Frey, Josif Grabocka | **Year:** 2024/2025 | **Source:** arXiv (under review)
**Quality Tier:** 2 (preprint, not yet peer-reviewed) | **Citations:** New
**Task/domain tested:** 17 methods across 68 diverse datasets
**OOS validation:** Yes (standardized benchmark evaluation)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.7

**Key finding:** Empirical evidence suggests "a paradigm shift, where Deep Learning methods outperform classical approaches" on tabular data. This challenges the Grinsztajn et al. (2022) consensus. However, the shift is driven primarily by foundation models (TabPFN-class) and properly tuned Transformers, not by LLMs used as zero-shot classifiers.

**Key equation / method:** Large-scale benchmark replication with updated DL methods.

**Testability on GTOS data:** Medium -- The "paradigm shift" applies to purpose-built tabular DL (TabPFN, FT-Transformer), not to general-purpose LLMs doing zero-shot classification. For GTOS, the implication is: TabPFN might be the strongest baseline, not XGBoost.

---

### Paper 13: Levin et al. -- Transfer Learning with Deep Tabular Models

**Authors:** Roman Levin, Valeriia Cherepanova, Avi Schwarzschild, Arpit Bansal, C. Bayan Bruss, Tom Goldstein, Andrew Gordon Wilson, Micah Goldblum | **Year:** 2023 | **Source:** ICLR 2023
**Quality Tier:** 1 | **Citations:** ~200+
**Task/domain tested:** MetaMIMIC medical dataset (12 binary prediction tasks, 34,925 patients, 172 features)
**OOS validation:** Yes (cross-task transfer evaluation)
**Relevance to GTOS:** Low-Medium
**GTOS question addressed:** Q-3.7

**Key finding:** Transfer learning with deep tabular models provides a "definitive advantage over gradient boosted decision tree methods when downstream data is limited." Supervised pre-training yields more transferable features than self-supervised approaches. The advantage is largest with very small downstream samples.

**Key equation / method:** Pre-train DNN on related tabular tasks, then fine-tune on target task with limited data.

**Testability on GTOS data:** Low -- GTOS has no related pre-training data. However, the finding that DL advantages emerge specifically with limited data echoes the TabPFN and TabLLM results. At n=129, transfer learning from a pre-trained model could theoretically help, but no suitable pre-training source exists for OB-retest classification.

---

### Paper 14: Predictive Modeling of Foreign Exchange Trading Signals Using Machine Learning Techniques

**Authors:** Multiple (ScienceDirect 2025) | **Year:** 2025 | **Source:** Expert Systems with Applications (Elsevier)
**Quality Tier:** 2 | **Citations:** New (2025)
**Task/domain tested:** Forex directional forecasting, 6 major currency pairs, daily and intraday data (2000-2023)
**OOS validation:** Yes (walk-forward out-of-sample testing)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.7

**Key finding:** Ensemble models (Random Forest, XGBoost) show superior performance compared to all other approaches across all prediction horizons. XGBoost produces the highest percentage profit (~55-60%) for shorter horizons. Logistic regression yields lower outcomes but serves as a useful linear baseline. XGBoost achieved significantly higher accuracy rates than the majority class rate in OOS evaluation.

**Key equation / method:** Walk-forward OOS evaluation with multiple ML algorithms on standardized technical features.

**Testability on GTOS data:** High -- Same domain (forex/commodities), same task (directional prediction), similar feature types (technical indicators). The finding that XGBoost achieves 55-60% accuracy on forex directional prediction provides a direct benchmark. GTOS's 65% WR is higher, but the comparison is confounded by different feature sets and filtering (GTOS only trades high-conviction setups via the CANDIDATE filter, not every candle).

---

<a id="synthesis"></a>
## 3. Cross-Question Synthesis

### The Tabular Data Consensus (Strong)

The literature is unambiguous on pure tabular classification:

1. **Tree-based models (XGBoost, CatBoost, Random Forest) dominate** LLMs, deep learning, and even specialized tabular transformers on most tabular datasets (Grinsztajn 2022, Shwartz-Ziv 2022, Borisov 2022).
2. **The margin narrows with small samples**: Below ~1,000 samples, TabPFN (a purpose-built tabular transformer) becomes competitive with or beats trees (Hollmann 2022/2025, McElfresh 2023).
3. **LLMs add value only in few-shot (<8 samples) or zero-shot settings** where no labeled data exists (Huertas 2024, Hegselmann 2023). At n=129, GTOS is well past this threshold.
4. **On structured financial/medical data, XGBoost beats GPT-4 by large margins** in zero-shot settings (Ghaffarzadeh-Esfahani 2025: 0.87 vs 0.43 F1).

### The Spatial Reasoning Exception (Weak but Relevant)

The tabular consensus does NOT address GTOS's specific use case. GTOS's LLM evaluates:

- **Spatial relationships**: "The OB zone sits at the 61.8% fib retracement of the last impulse, overlapping with an unfilled FVG from 3 candles ago"
- **Structural narrative**: "Price swept the previous swing low, creating a BOS, then formed a bullish OB with a 78% body ratio in the displacement candle"
- **Compositional reasoning**: "The confluence of OB + FVG + premium zone + H4 alignment suggests high-probability continuation"

These are NOT reducible to 7 tabular columns. The LLM processes a rich text description of market structure that encodes spatial and compositional information. No paper in the tabular data literature tests this type of hybrid task.

### The Testable Hypothesis

The literature points to a clear experiment:

1. Extract 7 key features from all 129 historical CANDIDATE evaluations
2. Train XGBoost (with proper cross-validation / leave-one-out at n=129)
3. Train TabPFN (purpose-built for small tabular datasets)
4. Compare OOS WR to the LLM's 65%

**If XGBoost/TabPFN >= 62% OOS**: The LLM's tabular understanding is matched. The remaining $60/month cost must be justified by spatial reasoning value alone.
**If XGBoost/TabPFN < 58% OOS**: The LLM captures signal beyond the 7 features -- likely from spatial/structural reasoning on the full MSO.

---

<a id="gtos-implications"></a>
## 4. Specific GTOS Implications

### Immediate Actions (Post-WF-1)

| Action | Priority | Evidence | Timeline |
|--------|----------|----------|----------|
| Build XGBoost baseline on 7 features | High | Grinsztajn 2022, Shwartz-Ziv 2022: trees dominate tabular | After 50+ live trades |
| Build TabPFN baseline on 7 features | High | Hollmann 2025: TabPFN dominates at n<1000 | After 50+ live trades |
| Compare OOS WR of XGBoost/TabPFN to LLM | Critical | All papers: the question is empirically answerable | After 50+ live trades |
| If XGBoost matches LLM: test hybrid (XGBoost filter + LLM for borderline) | Medium | Shwartz-Ziv 2022: ensembles of DL+trees outperform either alone | Post-comparison |
| Feature ablation: measure LLM WR with reduced MSO (tabular only vs full) | High | Test spatial reasoning value directly | Post-comparison |

### The Cost-Benefit Framing

| Scenario | Monthly Cost | Expected WR | Implication |
|----------|-------------|-------------|-------------|
| LLM only (current) | $60 | 65% | Baseline |
| XGBoost only (7 features) | $0 | TBD (estimated 58-65%) | If >= 62%, LLM unjustified |
| TabPFN only (7 features) | $0 | TBD (estimated 60-66%) | Strongest free alternative |
| XGBoost filter + LLM for borderline | ~$15 | TBD | 75% cost reduction if filter works |
| LLM with reduced MSO (tabular features only) | $60 | TBD | Tests spatial reasoning value |

### Why the LLM Might Still Win (Despite the Literature)

1. **Semantic feature names**: The LLM reads "touch_count: 1" and knows this means "first test of the OB zone." XGBoost sees column[3] = 1. The LLM's pre-training on trading/financial text gives it domain priors that XGBoost must learn from 129 samples.

2. **Compositional feature interactions**: The LLM can reason about "FVG inside the OB zone during a premium session with H4 alignment" as a single gestalt. XGBoost must learn this 4-way interaction from data, which requires >>129 samples at 4 features.

3. **Spatial geometry**: The relative position of price to OB boundaries, FVG fill level, and swing structure is encoded in the MSO as spatial description. This is not reducible to tabular features without significant feature engineering.

4. **Novelty detection**: The LLM can recognize unusual market conditions (e.g., "price gapped through the OB zone" or "the impulse had unusually low volume") that are not captured in the 7 features. XGBoost is blind to anything outside its feature set.

### Why the LLM Might Lose (Despite the Spatial Argument)

1. **The edge is in the zone, not the evaluation**: Test A rerun (n=219) showed OB zones add +17pp mechanically, but the AI adds ~0pp to entry WR. The edge is zone detection (Component 2), not AI evaluation (Component 3A).

2. **Confirmed rubber stamp**: The confidence scorer assigns 80 to 98% of setups. If the LLM cannot discriminate, a simple statistical model that also cannot discriminate would be equally (un)useful.

3. **Sample size favors trees**: At n=129, XGBoost has enough data to learn the 7 binary/ordinal features. The Huertas (2024) crossover at n=8 is far below GTOS's sample size.

4. **Cost asymmetry**: $60/month x 12 = $720/year for a component that may add 0pp to entry WR (Test A finding).

---

<a id="rejected"></a>
## 5. Rejected Papers

| Paper | Reason for Rejection |
|-------|---------------------|
| Various MDPI candlestick CNN papers (2024) | MDPI journal, no OOS validation, claims 99.3% accuracy without statistical testing |
| "AI Reshaping Financial Modeling" (Nature npj, 2025) | Review/opinion piece, no empirical comparison |
| Medium blog posts on XGBoost vs LLM | Not peer-reviewed |
| Candlestick pattern CNN papers without OOS | Missing OOS validation requirement |

---

## 6. Search Terms Used

1. "tabular data LLM large language model comparison benchmark"
2. "logistic regression trading comparison versus benchmark"
3. "gradient boosting tabular language model"
4. "simple model complex model financial comparison"
5. "XGBoost LLM structured data"
6. "deep learning vs traditional models tabular data"
7. "when do LLMs beat statistical models structured data"
8. Targeted searches for Grinsztajn 2022, Borisov 2022, TabPFN, Hegselmann TabLLM, Shwartz-Ziv 2022, Gorishniy FT-Transformer, Kadra well-tuned nets, LIFT, McElfresh TabZilla, forex ML comparison

---

## 7. Verdict

**The tabular data literature strongly favors XGBoost/TabPFN over LLMs for pure tabular classification, especially at n=129 where labeled data is sufficient for tree-based learning.** However, GTOS's task is NOT pure tabular classification -- the LLM processes a rich spatial/structural description of price geometry (OB position relative to FVG, impulse structure, zone boundaries) that cannot be reduced to 7 columns without information loss. No paper in the literature directly tests LLM spatial reasoning on price structure evaluation against tabular classifiers on the same data. The question is therefore empirically unresolved and must be answered by building an XGBoost/TabPFN baseline on the 7 features and comparing OOS WR to the LLM's 65%. If the baseline matches, the $60/month is overhead. If it falls short by >4pp, the spatial reasoning component justifies the cost. The existing Test A finding (AI adds ~0pp to entry WR) is the strongest evidence against the LLM, but this was measured on a population where the confidence scorer was a confirmed rubber stamp -- a properly discriminating LLM or statistical model might show different results.
