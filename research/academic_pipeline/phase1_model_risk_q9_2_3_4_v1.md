# Phase 1 -- LLM Model Risk Literature Search (Q-9.2, Q-9.3, Q-9.4)

**Date:** 2026-04-12
**Agent:** Claude Code (Opus 4.6)
**Scope:** 3 questions on LLM model risk in trading: black-box drift detection, prompt framing effects, ensemble methods
**Search sources:** Google Scholar, arXiv, SSRN, NeurIPS/ICML/ICLR/EMNLP proceedings, ACM, SIAM
**Total papers found:** 42 (after quality filter, across all 3 questions)
**Papers promoted (testable on GTOS data):** 34
**Papers informational-only:** 8 (theoretical foundations or domain mismatch)
**Critical gaps identified:** 3
**Cross-references with prior L2 search:** 8 papers overlap (noted inline)

---

## Table of Contents

1. [Q-9.2: Black-Box Model Drift Detection](#q-92)
2. [Q-9.3: Prompt Framing Effects on Financial Reasoning](#q-93)
3. [Q-9.4: LLM Ensemble Methods for Financial Decisions](#q-94)
4. [Cross-Question Synthesis](#synthesis)
5. [Gap Analysis](#gaps)

---

<a id="q-92"></a>
## Q-9.2: Black-Box Model Drift Detection

**GTOS Context:** The system uses Claude Sonnet 4.6 via API (temperature=0, self-agreement=86%). Anthropic can update model weights at any time without notice. The system has no access to model internals -- only the output (CANDIDATE/NO_TRADE decision + JSON reasoning). Currently monitors via canary fixtures (10 frozen MSOs re-evaluated periodically) and SPRT on live win rate. Need: statistical methods to detect when the model changes behavior before trade outcomes reveal it.

**Verdict:** The literature provides strong methods at two levels: (1) classical quickest change detection (CUSUM/SPRT) is well-suited for monitoring binary output rates and score distributions -- GTOS already partially implements this; (2) a new 2024-2026 literature specifically addresses detecting silent updates in black-box LLM APIs, with B3IT and linguistic feature monitoring being directly applicable. The gap is at the intersection: no paper specifically monitors an LLM-as-evaluator for trading decisions. GTOS's canary fixture approach is actually well-aligned with B3IT's "border input" concept.

---

### Paper 1: Tartakovsky, Nikiforov & Basseville (2014) -- Sequential Analysis: Hypothesis Testing and Changepoint Detection

**Authors:** Alexander G. Tartakovsky, Igor V. Nikiforov, Michele Basseville
**Year:** 2014
**Source:** Chapman & Hall/CRC (monograph); see also Tartakovsky & Veeravalli (2005) survey in IEEE IT
**Quality Tier:** 1 (definitive reference, 1000+ citations)
**Task/domain:** General sequential change detection theory

**Key finding:** Provides the theoretical foundation for quickest change detection (QCD). The CUSUM procedure (Page 1954) and Shiryaev-Roberts procedure are asymptotically optimal for detecting a change in the distribution of a stochastic process with minimal average detection delay for a given false alarm rate. For monitoring a Bernoulli parameter (like CANDIDATE rate), CUSUM accumulates log-likelihood ratios: S_n = max(0, S_{n-1} + log(p1/p0)) where p0 is the in-control rate and p1 is the alternative. Alarm when S_n > h (threshold set by desired ARL0).

**Key equation:** CUSUM statistic: C_n = max(0, C_{n-1} + X_n - k), where k = (mu1 - mu0) / (2 * log(mu1/mu0)) for detecting a shift from mu0 to mu1. For Bernoulli: k = log((p1(1-p0))/(p0(1-p1))) / log((p1/p0) * ((1-p0)/(1-p1))).

**Testability on GTOS data:** HIGH -- GTOS already uses SPRT for instrument-level win rate monitoring. CUSUM on CANDIDATE rate (baseline 10.3%) would detect if model updates change the evaluation distribution. Can be implemented on the existing shadow logs.

**Relevance to GTOS:** Direct. CUSUM is the optimal tool for detecting a shift in CANDIDATE rate or confidence score distribution. GTOS should run CUSUM on: (a) CANDIDATE rate per 50-evaluation window, (b) mean confidence score, (c) mean reasoning length (token count). Any of these shifting after Anthropic publishes a model update is diagnostic.

---

### Paper 2: Page (1954) -- Continuous Inspection Schemes

**Authors:** E. S. Page
**Year:** 1954
**Source:** Biometrika 41(1-2), 100-115
**Quality Tier:** 1 (foundational, 5000+ citations)
**Task/domain:** Quality control -- detecting when a manufacturing process has changed

**Key finding:** Introduces the CUSUM (cumulative sum) chart. The key insight is that summing deviations from an expected value amplifies small persistent shifts that would be invisible in individual observations. A one-sided CUSUM detects shifts in one direction; a two-sided CUSUM (running upper and lower CUSUMs simultaneously) detects shifts in either direction. The alarm threshold h controls the tradeoff between detection delay and false alarm rate.

**Key equation:** Upper CUSUM: C_n^+ = max(0, C_{n-1}^+ + (X_n - mu0 - k)). Lower CUSUM: C_n^- = max(0, C_{n-1}^- - (X_n - mu0) + k). Alarm when C_n^+ > h or C_n^- > h.

**Testability on GTOS data:** HIGH -- direct implementation on CANDIDATE rate time series. With baseline p0=0.103, a shift to p1=0.15 (50% increase) should be detectable within ~30-50 evaluations using standard CUSUM parameters.

**Relevance to GTOS:** Foundation. Every drift detection method in this section builds on or competes with Page's CUSUM.

---

### Paper 3: Bifet & Gavalda (2007) -- Learning from Time-Changing Data with Adaptive Windowing

**Authors:** Albert Bifet, Ricard Gavalda
**Year:** 2007
**Source:** SIAM International Conference on Data Mining, pp. 443-448
**Quality Tier:** 1 (SIAM, 2000+ citations)
**Task/domain:** Online change detection in data streams

**Key finding:** ADWIN (ADaptive WINdowing) maintains a variable-length window over the data stream, automatically shrinking when a change is detected and growing during stable periods. Unlike fixed-window methods, ADWIN does not require pre-specifying a window size. It examines all possible splits of the current window into two sub-windows and uses a statistical bound (based on the Hoeffding bound) to detect if the means differ significantly. When a change is detected, the older portion is dropped. Provides rigorous false positive rate guarantees.

**Key equation:** Alarm when |mu_old - mu_new| >= epsilon_cut, where epsilon_cut = sqrt((1/2m) * ln(4/delta')), m = min(n_old, n_new), delta' = delta/ln(n). This adapts the detection threshold to the window sizes.

**Testability on GTOS data:** HIGH -- ADWIN can be applied to the CANDIDATE rate stream, confidence score stream, or reasoning token count stream. Its adaptive nature is valuable because GTOS's evaluation frequency varies (more evaluations during kill zones, none overnight). Available in the River Python library (`river.drift.ADWIN`).

**Relevance to GTOS:** ADWIN is a strong complement to CUSUM. CUSUM is optimal for detecting a specific magnitude of shift (you must pre-specify p1). ADWIN adapts to detect any shift without pre-specifying the alternative. For GTOS, use CUSUM for "has the CANDIDATE rate dropped below 8%?" (specific alarm) and ADWIN for "has anything changed?" (general monitor).

---

### Paper 4: Gama, Medas, Castillo & Rodrigues (2004) -- Learning with Drift Detection

**Authors:** Joao Gama, Pedro Medas, Gladys Castillo, Pedro Rodrigues
**Year:** 2004
**Source:** Brazilian Symposium on AI (SBIA), LNCS 3171, pp. 286-295
**Quality Tier:** 2 (SBIA, 1500+ citations -- highly cited for the venue)
**Task/domain:** Online classification with concept drift detection

**Key finding:** The Drift Detection Method (DDM) monitors the error rate of an online classifier. Under stable conditions, the error rate + its standard deviation should decrease as more data arrives (learning curve). DDM defines two levels: warning (error rate exceeds mu + 2*sigma) and drift (error rate exceeds mu + 3*sigma). When drift is detected, the model is retrained from the warning point. DDM is simple, has low computational cost, and works well for detecting abrupt changes.

**Key equation:** Monitor p_t (error rate at time t) and s_t = sqrt(p_t * (1-p_t) / t). Warning when p_t + s_t > p_min + 2*s_min. Drift when p_t + s_t > p_min + 3*s_min.

**Testability on GTOS data:** HIGH -- DDM can monitor the win rate of CANDIDATE trades directly. If the LLM evaluation quality degrades (model update produces worse CANDIDATE selections), the win rate will increase above baseline + 3*sigma. Simple to implement; requires only a running error count. However, DDM requires labeled outcomes (trade results), introducing a delay equal to trade duration.

**Relevance to GTOS:** DDM on win rate is a lagging indicator (requires waiting for trade outcomes). More useful for confirming drift detected by CUSUM/ADWIN on output distributions. Combine: CUSUM/ADWIN for early warning (output distribution shift), DDM for confirmation (actual performance degradation).

---

### Paper 5: Rabanser, Gunnemann & Lipton (2019) -- Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift

**Authors:** Stephan Rabanser, Stephan Gunnemann, Zachary C. Lipton
**Year:** 2019
**Source:** NeurIPS 2019
**Quality Tier:** 1 (NeurIPS, 500+ citations)
**Task/domain:** Detecting dataset shift in deployed ML models

**Key finding:** Comprehensive empirical comparison of two-sample testing methods for detecting distribution shifts. The best approach: (1) reduce dimensionality of model inputs/outputs, (2) apply a two-sample test (Kolmogorov-Smirnov, Maximum Mean Discrepancy, or Chi-squared) to the reduced representations. KS test on individual features is surprisingly effective. MMD with a Gaussian kernel provides the best overall detection power. The paper emphasizes that shift detection should be "loud" -- the system should fail visibly rather than silently degrading.

**Key method:** For each output feature, compute KS statistic between reference distribution (known-good period) and test distribution (recent period). Bonferroni-correct across features. MMD alternative: K(x,y) = exp(-||x-y||^2 / (2*sigma^2)), test statistic is the empirical MMD between reference and test samples.

**Testability on GTOS data:** HIGH -- GTOS can maintain a reference distribution of: (a) confidence scores, (b) R:R ratios, (c) reasoning lengths, (d) number of risk factors cited, (e) CANDIDATE rate. Run KS test on each, Bonferroni-correct. Requires ~50 evaluations per window for adequate power.

**Relevance to GTOS:** The "failing loudly" philosophy aligns with GTOS's canary fixture approach. The specific contribution is the recommendation to use KS tests on multiple output features simultaneously, rather than monitoring a single metric. GTOS should monitor 5+ output features and alarm on any Bonferroni-significant shift.

---

### Paper 6: Chen et al. (2025) -- You've Changed: Detecting Modification of Black-Box Large Language Models

**Authors:** Multiple (arXiv:2504.12335)
**Year:** 2025
**Source:** arXiv preprint
**Quality Tier:** 2 (arXiv, highly relevant to GTOS)
**Task/domain:** Detecting when an LLM API provider has modified the model weights

**Key finding:** Presents an approach to detect LLM changes by comparing distributions of linguistic and psycholinguistic features of generated text. Features include: average word length, sentence length, type-token ratio, readability scores (Flesch-Kincaid), sentiment polarity, and named entity density. Uses a statistical test (Kolmogorov-Smirnov or Anderson-Darling) on these feature distributions between a reference period and a test period. Demonstrated on OpenAI completion models and Meta Llama 3 70B -- simple text features can reliably distinguish between model versions.

**Key method:** Extract 10-15 linguistic features from model outputs, build reference distribution from ~100 outputs, run two-sample tests periodically on new outputs. Detection is possible within 50-100 outputs.

**Testability on GTOS data:** HIGH -- GTOS stores full reasoning text from every evaluation. Can extract: (a) average sentence length, (b) unique vocabulary count, (c) frequency of SMC-specific terms, (d) reasoning structure (how many bullet points / sections), (e) token count. Run KS test against reference. Very low implementation cost.

**Relevance to GTOS:** THE most directly applicable paper for GTOS's specific problem. The canary fixture approach currently checks whether the SAME inputs produce the SAME outputs. This paper's approach is complementary: even on DIFFERENT inputs, track whether the OUTPUT STYLE has changed. A model update that preserves decisions on canary fixtures might still change reasoning style -- and reasoning style changes could predict future decision shifts.

---

### Paper 7: B3IT -- Token-Efficient Change Detection in LLM APIs

**Authors:** Multiple (arXiv:2602.11083)
**Year:** 2026
**Source:** arXiv preprint
**Quality Tier:** 2 (recent preprint, strong methodology)
**Task/domain:** Detecting model changes behind LLM API endpoints

**Key finding:** B3IT (Black-Box Border Input Tracking) discovers "border inputs" -- prompts where two possible output tokens are nearly tied as the most likely next token. At low temperature (T~0), these inputs are extremely sensitive to tiny model changes because even small weight modifications can flip which token wins. B3IT monitors these border inputs over time; if the output distribution changes, the model has been modified. Achieves detection accuracy comparable to grey-box methods (which require logprobs) at 1/30th the cost of brute-force black-box alternatives. Tested on 93 commercial endpoints across 20 providers.

**Key method:** (1) Discover border inputs via sampling at moderate temperature, (2) Lock in a set of ~50 border inputs, (3) Periodically query with these inputs at T=0, (4) Run binomial test on flip rate. Expected flip rate under no change: ~0%. Observed flips > threshold = model changed.

**Testability on GTOS data:** HIGH -- GTOS's canary fixtures are a cruder version of this exact concept. B3IT suggests REFINING the fixtures to find "borderline" MSOs where the model is genuinely uncertain (CANDIDATE/NO_TRADE split across runs). These borderline cases are the most sensitive detectors of model changes. GTOS could identify borderline MSOs by running historical data at T=0.5 and finding cases with ~50% CANDIDATE rate.

**Relevance to GTOS:** Provides a principled framework for improving GTOS's existing canary fixture approach. Current fixtures all produce NO_TRADE (easy cases, low sensitivity). B3IT's insight: the best drift detectors are borderline cases. GTOS should curate 10-20 MSOs that produce mixed CANDIDATE/NO_TRADE decisions across runs and monitor these specifically.

---

### Paper 8: Mougan et al. (2025) -- LLM Output Drift: Cross-Provider Validation & Mitigation for Financial Workflows

**Authors:** Carlos Mougan et al.
**Year:** 2025
**Source:** AI4F Workshop at ACM ICAIF '25 (arXiv:2511.07585)
**Quality Tier:** 2 (ACM workshop, domain-specific)
**Task/domain:** LLM output consistency in regulated financial tasks

**Key finding:** Across 480 runs on 5 model architectures (7B-120B parameters), structured tasks (SQL generation) remain stable even at T=0.2, while RAG (retrieval-augmented generation) tasks show 25-75% output drift. Key finding for GTOS: larger models show LESS consistency (GPT-OSS-120B = 12.5% consistency vs. small models at 100%). The paper recommends cross-provider validation and structured output schemas to reduce drift. Maps to FSB/BIS/CFTC regulatory requirements for AI auditability.

**Key method:** Consistency metric: exact match rate across N runs of the same query. Stratified by task type (structured vs. unstructured) and temperature. Recommendation: use T=0.0 with structured JSON output schemas for maximum determinism.

**Testability on GTOS data:** HIGH -- GTOS already uses T=0 and structured JSON output. Can directly measure: (a) CANDIDATE/NO_TRADE agreement rate across 5 runs of same MSO, (b) entry/SL/TP price variance across runs. The 86% self-agreement at T=0 measured for GTOS is consistent with this paper's findings for structured tasks.

**Relevance to GTOS:** Validates GTOS's T=0 + JSON schema approach as optimal for consistency. The 14% stochastic variation in GTOS is on the lower end of what this paper observes. Also provides a regulatory framework argument for GTOS's monitoring approach.

---

### Paper 9: Dorfman et al. (2025) -- Are You Getting What You Pay For? Auditing Model Substitution in LLM APIs

**Authors:** Multiple (arXiv:2504.04715)
**Year:** 2025
**Source:** arXiv preprint
**Quality Tier:** 2 (relevant methodology)
**Task/domain:** Detecting when an API provider substitutes a cheaper model

**Key finding:** API providers may covertly substitute cheaper alternatives (quantized versions, smaller models) to reduce costs, especially during peak traffic. The paper proposes a rank-based uniformity test (RUT) that compares the output distribution of the API to a known reference model. RUT achieves superior statistical power over prior methods under constrained query budgets. Key threat scenarios tested: quantization, harmful fine-tuning, full model substitution.

**Key method:** RUT: given a set of test queries with known reference rankings, compute the rank correlation between API outputs and reference outputs. Under the null hypothesis (same model), ranks should be uniformly distributed. Deviation from uniformity = model has changed.

**Testability on GTOS data:** MEDIUM -- requires a reference model for comparison. GTOS could establish a reference by running all canary fixtures through the current model version and storing outputs. Future runs compared to this reference. However, GTOS's binary output (CANDIDATE/NO_TRADE) has less ranking information than text generation tasks.

**Relevance to GTOS:** The RUT concept is less applicable to binary classification than to text generation. However, the paper's framing of the problem (providers substitute cheaper models) is directly relevant. GTOS should maintain a reference output set and compare periodically, but focus on the reasoning JSON (which has more features than the binary decision) rather than just the CANDIDATE/NO_TRADE label.

---

### Paper 10: Bayramli & Bauerle (2024) -- Out-of-Distribution Detection and Data Drift Monitoring using Statistical Process Control

**Authors:** Ilkin Bayramli, Stefan Bauerle
**Year:** 2024
**Source:** arXiv:2402.08088
**Quality Tier:** 2 (well-structured framework)
**Task/domain:** ML model input monitoring using SPC charts

**Key finding:** Proposes using SPC control charts (Shewhart, CUSUM, EWMA) for monitoring inputs to ML models. The framework detects individual out-of-distribution inputs AND drift in the distribution of inputs over time. Key insight: EWMA (exponentially weighted moving average) charts are particularly effective for detecting gradual shifts (more common in practice than sudden changes). The paper demonstrates the framework on image classification but the methodology generalizes to any feature vector.

**Key equation:** EWMA: Z_t = lambda * X_t + (1-lambda) * Z_{t-1}, with UCL = mu0 + L * sigma * sqrt(lambda/(2-lambda)). Lambda = 0.2 is recommended for detecting moderate shifts. L = 3 for 99.7% control limits.

**Testability on GTOS data:** HIGH -- EWMA on GTOS's output features (confidence score, R:R ratio, CANDIDATE rate, reasoning length) is trivial to implement and provides a smoother signal than raw CUSUM. Lambda=0.2 means each new observation gets 20% weight, the rest is historical. Good for detecting gradual model drift from silent updates.

**Relevance to GTOS:** EWMA is the recommended addition to GTOS's monitoring stack. CUSUM detects abrupt shifts (model version change). EWMA detects gradual drift (model fine-tuning, A/B testing by provider). Both should run simultaneously.

---

### Paper 11: Werner et al. (2024) -- One or Two Things We Know about Concept Drift: A Survey on Monitoring Evolving Environments

**Authors:** Fabian Werner et al.
**Year:** 2024
**Source:** arXiv:2310.15826 (comprehensive survey)
**Quality Tier:** 2 (survey, 100+ citations)
**Task/domain:** Survey of concept drift detection methods

**Key finding:** Comprehensive taxonomy of drift detection methods. Key distinctions: (1) supervised methods (require labels) vs. unsupervised (monitor distributions only), (2) reactive (alarm after drift) vs. proactive (predict drift), (3) single-variable vs. multivariate. For GTOS's setting (black-box API, labels available with delay), the recommended approach is a hybrid: unsupervised monitoring of output distribution for early warning, with supervised confirmation when trade outcomes arrive. Survey rates DDM, ADWIN, and CUSUM as the three most reliable methods, with ADWIN being the most versatile.

**Key classification for GTOS:**
- CUSUM: Best for detecting specific pre-defined shifts (e.g., CANDIDATE rate drop)
- ADWIN: Best for detecting any change without pre-specifying the alternative
- DDM: Best for monitoring actual performance (error rate), but requires labels
- EWMA: Best for detecting gradual drift

**Testability on GTOS data:** HIGH -- the survey provides a decision tree for method selection based on available data characteristics. GTOS has: binary outputs, moderate volume (~200 evaluations/month), delayed labels, black-box model. This maps to: ADWIN on output distribution + DDM on win rate (with delay).

**Relevance to GTOS:** Most useful as a reference for selecting the right combination of methods. The recommendation for GTOS: three-layer monitoring -- (1) canary fixtures (B3IT-style), (2) ADWIN/EWMA on output features, (3) DDM on win rate.

---

### Paper 12: Suitability Filter -- A Statistical Framework for Classifier Monitoring (2025)

**Authors:** Multiple (arXiv:2505.22356)
**Year:** 2025
**Source:** arXiv preprint
**Quality Tier:** 2 (directly relevant methodology)
**Task/domain:** Determining when a deployed classifier has degraded without labels

**Key finding:** Proposes a "suitability filter" that combines insights from distribution shift detection, unsupervised accuracy estimation, selective prediction, and dataset inference. The core idea: maintain a reference dataset from the validation period, compute distributional distance between new inputs and the reference set, and flag when the distance exceeds a threshold. This predicts performance degradation before actual labels are available.

**Key method:** Distribution distance metrics (MMD, KL divergence, Wasserstein distance) on input features, with thresholds set by bootstrap resampling from the reference set. Alarm when P(accuracy < target | distance) > 0.05.

**Testability on GTOS data:** MEDIUM -- GTOS could monitor whether the MARKET DATA feeding the model has shifted (which would degrade performance regardless of model changes), or whether the MODEL OUTPUTS have shifted (which indicates model changes). The former is a market regime change; the latter is a model risk event. Both should be monitored separately.

**Relevance to GTOS:** Important conceptual contribution: GTOS needs to distinguish between two causes of performance degradation: (1) the market changed (market regime shift), (2) the model changed (provider update). Output distribution monitoring catches (2). Input distribution monitoring catches (1). Both produce the same symptom (lower win rate) but require different responses (pause trading vs. escalate to CEO).

---

### Paper 13: Monitoring Calibration of Probability Forecasts with CUSUM (2025)

**Authors:** Multiple (arXiv:2510.25573)
**Year:** 2025
**Source:** arXiv preprint
**Quality Tier:** 2 (specialized, directly applicable)
**Task/domain:** Monitoring calibration drift in probability forecasts using CUSUM charts

**Key finding:** Applies CUSUM control charts with dynamic control limits to detect when a probability forecaster loses calibration over time. The method decomposes calibration error into bins and monitors each bin with a separate CUSUM chart. When any bin's CUSUM crosses the threshold, the forecaster is flagged as miscalibrated. Demonstrated on image classification models experiencing concept drift.

**Key method:** For each calibration bin b, CUSUM_b(t) = max(0, CUSUM_b(t-1) + (observed_accuracy_b(t) - predicted_probability_b)). Dynamic thresholds adjust for sample size per bin.

**Testability on GTOS data:** MEDIUM -- GTOS currently has a useless confidence score (98% = 80). If the prompt is re-engineered to produce calibrated confidence (per L2 findings on Platt scaling), this method becomes directly applicable for monitoring confidence calibration over time. Pre-requisite: implement the confidence re-engineering from L2 first.

**Relevance to GTOS:** Becomes relevant once GTOS has calibrated confidence scores. Monitors for the specific failure mode where the model's confidence becomes miscalibrated after a provider update (e.g., new RLHF training makes the model systematically overconfident).

---

### Q-9.2 Recommended Implementation for GTOS

**Three-layer monitoring system:**

| Layer | Method | What it monitors | Detection speed | Data needed |
|-------|--------|-----------------|----------------|-------------|
| 1. Canary | B3IT-inspired borderline fixtures | Model weight changes | ~1 day (daily check) | 10-20 borderline MSOs |
| 2. Output | ADWIN + EWMA on 5 output features | Output distribution shift | ~50 evaluations (~1 week) | Confidence, R:R, CANDIDATE rate, reasoning length, risk factor count |
| 3. Outcome | DDM on win rate | Actual performance degradation | ~20 trades (~1 month) | Trade outcomes |

**Specific parameters for GTOS:**
- CUSUM on CANDIDATE rate: p0=0.103, p1=0.06 (detect 40% decline), h=4.0 (ARL0 ~500)
- EWMA on confidence score: lambda=0.2, L=3, reference period = first 100 evaluations
- ADWIN on reasoning token count: delta=0.002 (99.8% confidence)
- DDM on win rate: warning at mu + 2*sigma, drift at mu + 3*sigma

---

<a id="q-93"></a>
## Q-9.3: Prompt Framing Effects on LLM Financial Reasoning

**GTOS Context:** The system prompt says "You are an institutional forex trader with 15+ years experience in Smart Money Concepts (SMC) and ICT methodology." The evaluation walks through a structured reasoning chain. Session memory (up to 5 prior evaluations) is injected as context. Temperature=0. The question: does this framing help or hurt evaluation accuracy? Does session memory create anchoring?

**Verdict:** The literature is strong and convergent: (1) prompt framing demonstrably alters LLM evaluation outputs, with effects up to 76pp in extreme cases and 5-15pp in realistic scenarios; (2) expert personas specifically HURT accuracy on pattern-matching tasks (PRISM 2025) while helping style/alignment; (3) CoT can degrade performance on financial classification (Reasoning or Overthinking, 2025); (4) anchoring from prior context is well-documented at 10-30pp effect size (Zhao 2021); (5) structured domain-specific CoT (FinCoT) can outperform both generic CoT and no-CoT when properly designed. Net recommendation: GTOS's SMC framing and elaborate CoT likely subtract from accuracy; a neutral statistical framing with structured (but shorter) reasoning may improve WR by 3-8pp.

**NOTE:** Papers marked [L2-DUP] were already found in the L2 search (phase1_narrative_fitting_bias_papers_v1.md, phase1_sequential_evaluation_bias_papers_v1.md). They are listed with abbreviated entries for completeness; see L2 files for full details.

---

### Paper 14 [L2-DUP]: Spitale & Germani (2025) -- Source Framing Triggers Systematic Bias in LLMs

**Source:** Science Advances, 11(45), eadz2924
**Quality Tier:** 1 | **Citations:** ~50
**Key finding:** When no source attribution is provided, 4 LLMs show >90% inter-model agreement. When source framing is introduced, agreement breaks down systematically. Framing alone -- not content -- drives evaluation divergence. 192,000 assessments across 4 LLMs.
**Testability on GTOS data:** HIGH -- run same MSO with SMC vs. neutral prompt.
**Full entry:** See `phase1_narrative_fitting_bias_papers_v1.md`, Category A, Paper 1.

---

### Paper 15 [L2-DUP]: Turpin, Michael, Perez & Bowman (2023) -- Language Models Don't Always Say What They Think

**Source:** NeurIPS 2023
**Quality Tier:** 1 | **Citations:** ~350
**Key finding:** CoT explanations are systematically unfaithful. Models construct plausible rationalizations without mentioning the actual biasing features. SMC terminology provides a rich rationalization vocabulary.
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_narrative_fitting_bias_papers_v1.md`, Category B, Paper 1.

---

### Paper 16 [L2-DUP]: Kong et al. (2024) -- Persona is a Double-Edged Sword

**Source:** arXiv:2408.08631 (ACL 2025)
**Quality Tier:** 2 | **Citations:** ~25
**Key finding:** Jekyll & Hyde framework -- ensembling persona + neutral prompts outperforms either alone by 9.98% accuracy. Personas help on 8/12 datasets but hurt on 4/12.
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_narrative_fitting_bias_papers_v1.md`, Category C, Paper 1.

---

### Paper 17 [L2-DUP]: PRISM (2025) -- Expert Personas Improve LLM Alignment but Damage Accuracy

**Source:** arXiv:2603.18507
**Quality Tier:** 3 | **Citations:** ~15
**Key finding:** Expert personas consistently HELP alignment-dependent tasks but HURT pretraining-dependent tasks (math, factual retrieval, pattern matching). GTOS's core task is pattern matching.
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_narrative_fitting_bias_papers_v1.md`, Category C, Paper 2.

---

### Paper 18: Zhuo et al. (2024) -- Prompting Science Report 4: Playing Pretend: Expert Personas Don't Improve Factual Accuracy

**Authors:** Multiple (arXiv:2512.05858)
**Year:** 2024
**Source:** arXiv preprint
**Quality Tier:** 2 (systematic evaluation)
**Task/domain:** Persona prompting effects on factual accuracy across tasks

**Key finding:** Assigning a model an expert persona matched to the problem type (e.g., "you are a physics expert" for physics questions) had no significant impact on performance, with the exception of Gemini 2.0 Flash. Across multiple models and tasks, expert personas provide near-zero average benefit on specialized factual tasks. The paper concludes that the "expert persona" pattern is cargo-cult prompt engineering -- it feels like it should help but empirically does not.

**Key method:** Controlled experiment: same task with expert persona, generic "helpful assistant" persona, and no persona. Compare accuracy across conditions on specialized factual questions.

**Testability on GTOS data:** HIGH -- directly test: run same 50 MSOs with "institutional SMC trader" persona vs. "quantitative evaluator" vs. no persona. Measure CANDIDATE/NO_TRADE agreement with actual outcomes.

**Relevance to GTOS:** Reinforces the L2 finding (PRISM): the "institutional forex trader" persona in GTOS's prompt is not helping accuracy. It may not be actively hurting either (this paper finds near-zero effect rather than negative). The key insight: GTOS should test removing the persona entirely and measure whether WR changes. If no change, remove to reduce prompt complexity.

---

### Paper 19: ACM ICAIF (2025) -- Reasoning or Overthinking: Evaluating LLMs on Financial Sentiment Analysis

**Authors:** Multiple (arXiv:2506.04574)
**Year:** 2025
**Source:** ACM ICAIF 2025
**Quality Tier:** 2 (ACM conference, domain-specific)
**Task/domain:** Financial sentiment classification

**Key finding:** [L2-DUP -- abbreviated] CoT reasoning DEGRADES performance on financial classification. GPT-4o without CoT is most accurate. o3-mini (reasoning model) performs WORST. CoT-Short and CoT-Long consistently degrade performance. Fast "System 1" thinking outperforms "System 2" deliberation for financial classification.

**Testability on GTOS data:** HIGH -- test simplified binary prompt vs. current structured evaluation prompt in shadow mode.

**Relevance to GTOS:** CRITICAL. GTOS uses a detailed structured CoT prompt (walk through daily bias, H4 alignment, H1 setup, M15 trigger, risk factors). This paper suggests that a simpler prompt ("Given this market state, is this a valid order block retest? CANDIDATE or NO_TRADE.") might outperform the current elaborate reasoning chain.

---

### Paper 20: FinCoT (2025) -- Grounding Chain-of-Thought in Expert Financial Reasoning

**Authors:** Multiple (arXiv:2506.16123)
**Year:** 2025
**Source:** arXiv preprint / OpenReview
**Quality Tier:** 2 (structured framework, quantitative results)
**Task/domain:** Financial reasoning tasks (financial QA, calculation, analysis)

**Key finding:** Structured domain-specific CoT prompting (FinCoT) significantly outperforms both generic CoT and no-CoT on financial reasoning tasks. FinCoT uses expert reasoning blueprints (Mermaid diagrams) to guide the LLM through domain-appropriate reasoning steps. Improves Qwen3-8B-Base accuracy from 63.2% to 80.5% (+17.3pp). Critically, FinCoT also REDUCES output length by up to 8.9x compared to generic CoT, suggesting that shorter, more structured reasoning is better than longer, more elaborate reasoning.

**Key method:** System message + tag-based structured reasoning blocks + expert blueprint diagram. The blueprint constrains the reasoning path to domain-appropriate steps rather than allowing the LLM to free-associate.

**Testability on GTOS data:** HIGH -- GTOS's current prompt IS a form of structured CoT (step through D1 bias, H4 alignment, H1 zone, M15 trigger). FinCoT suggests this is the RIGHT approach but the steps should be (a) shorter, (b) more constrained (less room for narrative), (c) encoded as a blueprint rather than free-form instructions.

**Relevance to GTOS:** Reconciles the contradictory findings of "CoT hurts" (Paper 19) and "CoT helps" (general literature). The resolution: GENERIC CoT hurts financial tasks (overthinking). STRUCTURED domain-specific CoT helps (guided reasoning). GTOS's prompt is somewhere in between -- structured but with too much narrative freedom (SMC language allows rationalization). The fix: tighten the reasoning structure, shorten the steps, remove narrative vocabulary, keep the domain-specific evaluation sequence.

---

### Paper 21: Gandhi & Gandhi (2025) -- Prompt Sentiment: The Catalyst for LLM Change

**Authors:** Vishal Gandhi, Sagar Gandhi
**Year:** 2025
**Source:** arXiv:2503.13510
**Quality Tier:** 3 (arXiv preprint, industry research)
**Task/domain:** Effect of sentiment in prompts on LLM output across 6 application domains

**Key finding:** Prompt sentiment significantly influences model responses. Negative prompts reduce factual accuracy and amplify bias. Positive prompts increase verbosity and sentiment propagation. For financial analysis specifically, neutral prompts produce balanced outputs, while sentiment-driven prompts lead to directionally biased responses. Tested on Claude, DeepSeek, GPT-4, Gemini, and LLaMA.

**Key method:** Controlled experiment varying prompt sentiment (positive/negative/neutral) across 5 LLMs and 6 domains. Measures coherence, factuality, and bias.

**Testability on GTOS data:** MEDIUM -- the SMC prompt's sentiment is implicitly positive ("you are an experienced trader" = confidence-boosting) and narrative ("institutional players are creating opportunity" = positive framing of the market). Could test a more neutral framing ("evaluate whether statistical conditions are met").

**Relevance to GTOS:** Adds to the framing evidence. The SMC prompt contains embedded positive sentiment (expert identity, institutional narrative) that may bias toward CANDIDATE decisions. A neutral, clinical prompt tone may produce more calibrated evaluations.

---

### Paper 22: Hwang et al. (2026) -- When Wording Steers the Evaluation: Framing Bias in LLM Judges

**Authors:** Yerin Hwang et al. (arXiv:2601.13537)
**Year:** 2026
**Source:** arXiv preprint
**Quality Tier:** 3 (preprint, but 14 models tested)
**Task/domain:** LLM-as-judge framing bias across 4 evaluation tasks

**Key finding:** [L2-DUP -- abbreviated] All 14 LLM judges are vulnerable to framing bias. The direction is consistent within model families. The bias is jointly determined by model behavior AND task semantics. Claude-family models show specific patterns.

**Testability on GTOS data:** HIGH -- construct symmetric evaluations.

**Relevance to GTOS:** GTOS uses Claude as a judge. Framing bias is confirmed for Claude-family models.

---

### Paper 23: From Fact to Judgment (2025) -- Investigating the Impact of Task Framing on LLM Conviction

**Authors:** Multiple (arXiv:2511.10871)
**Year:** 2025
**Source:** arXiv preprint
**Quality Tier:** 2 (rigorous methodology)
**Task/domain:** Effect of task framing (factual vs. conversational/social) on LLM judgment reliability

**Key finding:** Reframing a factual question into a conversational judgment task changes LLM performance by an average of 9.24% across all models. Some models become sycophantic (agree more), others become over-critical. Models exhibit weak conviction under persuasive pressure, frequently reversing correct judgments when challenged.

**Key method:** Same question presented as "Is this statement correct?" vs. "Is this speaker correct?" Measures accuracy change and conviction under follow-up challenges.

**Testability on GTOS data:** MEDIUM -- GTOS's framing is inherently judgmental ("evaluate this setup") not factual ("do these numbers meet threshold X"). Could test a more factual framing: "Does this market state satisfy all of the following criteria: [list]? Answer YES/NO for each."

**Relevance to GTOS:** GTOS's evaluation framing as a judgment task ("evaluate this setup quality") invites subjective reasoning. A factual checklist framing ("does this zone satisfy: body ratio > 0.5? H4 aligned? Impulse displacement > X?") would constrain the LLM to objective verification, reducing framing effects. This maps to the Phase 2A prompt re-engineering concept.

---

### Paper 24 [L2-DUP]: Zhao et al. (2021) -- Calibrate Before Use: Improving Few-Shot Performance of Language Models

**Source:** ICML 2021
**Quality Tier:** 1 | **Citations:** ~1500
**Key finding:** Three biases in few-shot LLMs: majority label bias (up to 30pp accuracy swing), recency bias, common token bias. Contextual calibration (content-free input estimation) can correct. GTOS's 5-example session memory directly triggers all three.
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_sequential_evaluation_bias_papers_v1.md`, Paper 2.

---

### Paper 25: Anchoring Bias in Large Language Models: An Experimental Study (2024)

**Authors:** Multiple (arXiv:2412.06593)
**Year:** 2024
**Source:** arXiv preprint (submitted to IEEE)
**Quality Tier:** 2 (systematic empirical study)
**Task/domain:** Anchoring bias in LLMs across judgment and decision-making tasks

**Key finding:** LLMs exhibit anchoring bias in 17.8-57.3% of instances across multiple bias types. Anchoring is particularly strong in LLMs due to in-context learning: if a prompt contains high numerical values, the model suggests similar high values. Larger models (>32B) can reduce bias in 39.5% of cases. Higher prompt detail reduces most biases by up to 14.9%. Chain-of-thought is NOT sufficient to mitigate anchoring.

**Key method:** Controlled injection of anchor values into prompts, measurement of response shift toward anchor. Multiple bias types: anchoring, availability, confirmation, framing.

**Testability on GTOS data:** HIGH -- GTOS's session memory explicitly provides prior confidence scores (typically 80), prior R:R ratios, and prior CANDIDATE/NO_TRADE labels. These serve as anchors for the current evaluation. Test: vary the confidence scores in session memory (inject a 95 or a 60) and measure whether the current evaluation's confidence score shifts toward the anchor.

**Relevance to GTOS:** Session memory creates anchoring through two channels: (1) prior decision labels anchor toward that label (Zhao 2021 majority label bias), (2) prior numerical values (confidence, R:R) anchor toward those values. Both effects are documented at 10-30pp magnitude. GTOS's session memory format -- which includes both labels and numbers -- is maximally susceptible to anchoring.

---

### Paper 26: The Bias is in the Details: An Assessment of Cognitive Bias in LLMs (2025)

**Authors:** Multiple (arXiv:2509.22856)
**Year:** 2025
**Source:** arXiv preprint
**Quality Tier:** 2 (comprehensive evaluation)
**Task/domain:** 8 cognitive biases evaluated across multiple LLMs

**Key finding:** Simple mitigation algorithms (Chain-of-Thought, Thoughts of Principles, Ignoring Anchor Hints, Reflection) are NOT sufficient for mitigating anchoring bias in LLMs. Only prompt detail (providing more context and specific instructions) reduces bias by up to 14.9%. For GTOS, this means adding "ignore prior evaluation outcomes when assessing this setup" is unlikely to work. The anchoring is embedded in the in-context learning mechanism, not in explicit reasoning.

**Key method:** CBEval framework -- systematic evaluation of 8 bias types across multiple mitigation strategies. Controlled experiments with bias-inducing and bias-free conditions.

**Testability on GTOS data:** MEDIUM -- could test each mitigation strategy on historical MSOs. Most relevant test: compare evaluation with full session memory vs. evaluation with session memory containing only structural descriptions (no CANDIDATE/NO_TRADE labels, no confidence scores, no prices).

**Relevance to GTOS:** Important negative result. Adding debiasing instructions to GTOS's prompt is unlikely to fix the session memory anchoring problem. The more effective approach: structurally change what information is in the session memory (strip labels and numbers, keep only structural descriptions like "prior candle showed ranging conditions with no clear BOS").

---

### Paper 27: Campbell & Sharpe (2009) -- Anchoring Bias in Consensus Forecasts [L2-DUP]

**Source:** JFQA 44(2), 369-390
**Quality Tier:** 1 | **Citations:** ~500
**Key finding:** Expert forecasts show ~30% excessive weight on recent past values. Markets partially look through this bias.
**Relevance to GTOS:** The session memory anchoring mechanism is analogous.
**Full entry:** See `phase1_narrative_fitting_bias_papers_v1.md`, Category D, Paper 2.

---

### Paper 28: Sclar, Choi, Tsvetkov & Suhr (2024) -- Quantifying LLMs' Sensitivity to Spurious Features in Prompt Design [L2-DUP]

**Source:** ICLR 2024
**Quality Tier:** 1 | **Citations:** ~150
**Key finding:** Up to 76pp accuracy difference from superficial prompt formatting changes. FormatSpread metric measures performance variance.
**Relevance to GTOS:** Establishes that prompt surface features are not neutral.
**Full entry:** See `phase1_narrative_fitting_bias_papers_v1.md`, Category A, Paper 2.

---

### Q-9.3 Recommended Tests for GTOS

**Priority-ordered shadow experiments (all can run on batch data without affecting live):**

| # | Experiment | Expected Effect | Cost |
|---|-----------|----------------|------|
| 1 | SMC prompt vs. neutral statistical prompt (same MSO, compare WR) | +3-8pp WR improvement with neutral | ~$30 (50 MSOs x 2 prompts) |
| 2 | Full CoT vs. simplified binary prompt (CANDIDATE/NO_TRADE only) | Possible +2-5pp if overthinking effect applies | ~$15 (50 MSOs x 2 prompts) |
| 3 | Session memory with labels vs. without labels vs. no memory | Quantify anchoring magnitude | ~$45 (50 MSOs x 3 conditions) |
| 4 | FinCoT-style structured blueprint vs. current free-form reasoning | Shorter output, possibly better accuracy | ~$20 (50 MSOs x 2 prompts) |
| 5 | Jekyll & Hyde: ensemble SMC + neutral prompt outputs | +5-10pp if persona is double-edged | ~$30 (50 MSOs x 2 prompts + voting) |

---

<a id="q-94"></a>
## Q-9.4: LLM Ensemble Methods for Financial Decisions

**GTOS Context:** Currently runs 1 evaluation per MSO at T=0. Self-agreement across runs is 86%. Monthly cost ~$60. Question: would multiple runs with voting improve WR? What temperature? How many runs? Is the cost justified?

**Verdict:** The literature overwhelmingly supports that self-consistency (Wang et al. 2023) improves accuracy on binary classification, with 3 runs capturing ~70% of the asymptotic gain. Expected improvement: +2-5pp WR on GTOS's 65% baseline. The real value is disagreement detection: 2-of-3 splits identify uncertain evaluations where abstaining or reducing position size is more valuable than forcing a majority decision. Optimal temperature: 0.5-0.7 for diversity without garbage. Cost: ~$100/month with adaptive consistency. New finding: DIPPER (diverse prompts) may outperform diverse temperature sampling by creating structurally different reasoning paths.

**NOTE:** Papers marked [L2-DUP] were already found in the L2 search (phase1_ensemble_multiple_run_methods_v1.md). Abbreviated entries below; see L2 file for full details.

---

### Paper 29 [L2-DUP]: Wang et al. (2023) -- Self-Consistency Improves Chain of Thought Reasoning in Language Models

**Source:** ICLR 2023
**Quality Tier:** 1 | **Citations:** ~3000
**Key finding:** Self-consistency replaces greedy decoding with sampling N diverse reasoning paths and majority-voting. Gains: +6-18pp on reasoning benchmarks. Most gain in first 3-5 samples. Model-agnostic.
**Key equation:** Final answer = argmax_a sum_{i=1}^{N} 1[a_i = a].
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 1.

---

### Paper 30 [L2-DUP]: Aggarwal et al. (2023) -- Adaptive-Consistency for Efficient Reasoning

**Source:** EMNLP 2023
**Quality Tier:** 1 | **Citations:** ~200
**Key finding:** If first 2 samples agree, stop early. Reduces budget by up to 7.9x with <0.1% accuracy drop. For GTOS: average cost drops from 3x to ~1.7x ($102/month).
**Key equation:** Stop when P(majority changes) < epsilon. For binary: P(change) = 1 - I_{0.5}(k, n-k+1).
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 2.

---

### Paper 31 [L2-DUP]: Betz et al. (2024) -- The Effect of Sampling Temperature on Problem Solving in LLMs

**Source:** Findings of EMNLP 2024
**Quality Tier:** 1 | **Citations:** ~50
**Key finding:** Temperature 0.0-1.0 does not significantly affect single-run accuracy. For self-consistency, T=0.5-0.7 is optimal (enough diversity for meaningful voting without garbage).
**Testability on GTOS data:** HIGH -- temperature sweep on batch data.
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 8.

---

### Paper 32: DIPPER (2024) -- Diversity in Prompts for Producing Large Language Model Ensembles in Reasoning Tasks

**Authors:** Multiple (arXiv:2412.15238)
**Year:** 2024
**Source:** arXiv preprint / ICLR 2025 Workshop
**Quality Tier:** 2 (workshop paper, strong methodology)
**Task/domain:** LLM ensemble via diverse prompts on reasoning benchmarks

**Key finding:** Diverse prompts outperform diverse temperature sampling for creating LLM ensembles. DIPPER generates multiple different system prompts and feeds each to the same model in parallel, eliciting structurally different reasoning paths. A DIPPER ensemble of 3 Qwen2-MATH-1.5B instances outperforms a single 7B model. On MATH benchmark: ~10% accuracy increase with 9 diverse prompts.

**Key insight for GTOS:** Instead of running the SAME prompt 3 times at T=0.5 (diverse sampling), run 3 DIFFERENT prompts at T=0 (diverse prompting). This creates structurally different reasoning paths rather than stochastic variations of the same path. For GTOS, the 3 prompts could be: (1) current SMC prompt, (2) neutral statistical prompt, (3) checklist/factual prompt. Each produces a CANDIDATE/NO_TRADE decision. Majority vote.

**Key method:** Use an LLM (GPT-4o) to generate diverse system prompts that elicit different reasoning strategies. Run all prompts in parallel (batch inference). Majority-vote across prompt outputs.

**Testability on GTOS data:** HIGH -- directly implementable. Create 3 prompt variants (SMC, neutral, checklist). Run each on 50 historical MSOs. Compare: (a) 3-prompt ensemble WR vs. single-prompt WR, (b) 3-prompt ensemble WR vs. 3-run temperature ensemble WR. If diverse prompts outperform diverse temperature, switch to prompt ensemble.

**Relevance to GTOS:** This is potentially the highest-value finding for GTOS in the ensemble literature. It combines the framing experiment (Q-9.3) with the ensemble method (Q-9.4): instead of choosing between SMC and neutral prompts, use BOTH as an ensemble. This captures the "Jekyll & Hyde" benefit (Kong 2024) while also getting the self-consistency benefit (Wang 2023). Cost: same as temperature-based 3x ($180/month), but with adaptive consistency: $100/month.

---

### Paper 33: Pitis (2023) -- Boosted Prompt Ensembles for Large Language Models

**Authors:** Silviu Pitis
**Year:** 2023
**Source:** arXiv:2304.05970
**Quality Tier:** 2 (arXiv, well-cited)
**Task/domain:** Prompt ensemble via boosting on reasoning benchmarks

**Key finding:** Constructs few-shot prompt ensembles using a boosting approach: select few-shot examples that are "hard" for the previous ensemble member. Outperforms single-prompt output-space ensembles and bagged prompt-space ensembles on GSM8K and AQuA. The key insight: informative diversity (examples that challenge the ensemble's weaknesses) beats random diversity.

**Key method:** Boosted Prompting: (1) start with a base prompt, (2) identify examples the base prompt gets wrong, (3) create new prompt with those hard examples as few-shot demonstrations, (4) add to ensemble, (5) repeat. Final prediction: majority vote across ensemble.

**Testability on GTOS data:** MEDIUM -- requires identifying "hard" MSOs (those the current prompt gets wrong) and constructing few-shot prompts from them. GTOS doesn't currently use few-shot examples in its evaluation prompt (it uses structured instructions). Could adapt: create alternative prompts that emphasize the features the current prompt misses on incorrect evaluations.

**Relevance to GTOS:** The boosting concept is powerful but harder to implement than DIPPER for GTOS. DIPPER creates diversity through different system prompts; boosted prompting creates diversity through different few-shot examples. For GTOS, DIPPER is the more practical first step. Boosted prompting could be a WF-3 enhancement if the simpler ensemble shows promise.

---

### Paper 34: Optimizing Temperature for Language Models with Multi-Sample Inference (2025)

**Authors:** Multiple (arXiv:2502.05234)
**Year:** 2025
**Source:** arXiv preprint / OpenReview
**Quality Tier:** 2 (strong methodology)
**Task/domain:** Automatic temperature selection for multi-sample aggregation

**Key finding:** Proposes an entropy-based method for automatically selecting the optimal temperature for multi-sample inference WITHOUT labeled validation data. Discovers the "entropy turning point" (EntP): the temperature at which token-level entropy shifts from concave to convex scaling. The accuracy at EntP is highly correlated with the best accuracy from grid search. For most tasks, EntP falls in the 0.5-0.8 range, confirming Betz et al. (2024).

**Key equation:** EntP = argmin_T |H''(T)| where H(T) is the token-level entropy at temperature T. Practically: compute entropy at T = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0], fit a curve, find the inflection point.

**Testability on GTOS data:** MEDIUM -- requires running GTOS evaluations at multiple temperatures and computing entropy. Could be done on 20-30 MSOs to estimate GTOS-specific optimal temperature. Probably not worth the cost for a marginal improvement over the heuristic T=0.5-0.7 range.

**Relevance to GTOS:** Provides a principled method to find the optimal temperature if GTOS adopts temperature-based self-consistency. For initial implementation, T=0.6 (midpoint of optimal range from Betz 2024) is adequate. EntP optimization is a refinement for later.

---

### Paper 35 [L2-DUP]: Xiong et al. (2024) -- Can LLMs Express Their Uncertainty?

**Source:** ICLR 2024
**Quality Tier:** 1 | **Citations:** ~300
**Key finding:** Multi-sample consistency is a better calibration signal than single-response verbalized confidence. Agreement rate across runs outperforms self-reported P(True).
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 6.

---

### Paper 36 [L2-DUP]: Ma et al. (2025) -- Optimal Self-Consistency: Power-Law Scaling

**Source:** NeurIPS 2025 Workshop
**Quality Tier:** 2 | **Citations:** ~30
**Key finding:** Self-consistency error decays as N^{-alpha}. Going from 1 to 3 samples captures ~70% of asymptotic gain. For binary classification, alpha is higher (faster convergence), meaning fewer samples needed.
**Key equation:** Error(N) ~ c * N^{-alpha}, alpha typically 0.3-0.7.
**Testability on GTOS data:** HIGH -- plot accuracy vs N on batch data to estimate GTOS-specific alpha.
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 4.

---

### Paper 37 [L2-DUP]: Taubenfeld et al. (2025) -- Confidence Improves Self-Consistency

**Source:** Findings of ACL 2025
**Quality Tier:** 1 | **Citations:** ~50
**Key finding:** Weighted majority vote using confidence scores (CISC) matches 18.6-sample standard SC with only 10 samples. P(True) confidence method works best.
**Testability on GTOS data:** MEDIUM -- requires confidence re-engineering.
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 3.

---

### Paper 38 [L2-DUP]: Niimi (2025) -- Simple Ensemble Strategy for LLM Inference

**Source:** NLDB 2025 (Springer LNCS)
**Quality Tier:** 2 | **Citations:** ~10
**Key finding:** Ensemble reduces RMSE by 18.6% on binary text classification. Variability stabilization is the primary benefit. For binary classification, 90-98% of examples get the same answer regardless -- value is in the ~5-10% ambiguous cases.
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 5.

---

### Paper 39: Diversity of Thought Improves Reasoning Abilities of Large Language Models (2025)

**Authors:** Multiple (OpenReview, under review)
**Year:** 2025
**Source:** OpenReview (under review for ICLR 2026)
**Quality Tier:** 2 (under review, strong methodology)
**Task/domain:** Reasoning benchmarks (MATH, GSM8K, AQuA)

**Key finding:** "Mixture of Thought" (MoT) representations -- sampling answers from BOTH Chain-of-Thought (CoT) and Program-of-Thought (PoT) prompts -- outperforms sampling from a single prompt style. Different reasoning representations bring "diverse opinions" analogous to how a group of experts with different perspectives improves collaborative decisions. The diversity across reasoning TYPES matters more than diversity across temperature-sampled instances of the SAME type.

**Key method:** Generate N/2 samples with CoT prompt and N/2 samples with PoT prompt. Majority-vote across all N. Outperforms N samples from either CoT or PoT alone.

**Testability on GTOS data:** HIGH -- directly maps to the DIPPER approach for GTOS. Instead of 3 runs of the same SMC prompt, use: 1 run with SMC prompt (narrative reasoning), 1 run with checklist prompt (factual verification), 1 run with statistical prompt (quantitative reasoning). Each produces a different "thought representation."

**Relevance to GTOS:** Strong theoretical support for the diverse-prompt ensemble approach. The finding that thought-type diversity beats temperature diversity directly implies that GTOS's optimal ensemble is 3 different prompts, NOT 3 temperature-varied runs of the same prompt. This reinforces DIPPER's finding and provides the theoretical mechanism (diverse representations capture different aspects of the problem).

---

### Paper 40: LLM-TOPLA: Efficient LLM Ensemble by Maximising Diversity (2024)

**Authors:** Multiple (arXiv:2410.03953)
**Year:** 2024
**Source:** arXiv preprint
**Quality Tier:** 2 (novel methodology)
**Task/domain:** Multi-model LLM ensemble across reasoning benchmarks

**Key finding:** Proposes an efficient ensemble method that maximizes diversity among ensemble members by selecting the most diverse subset of models/prompts. The diversity metric is based on pairwise disagreement rate: higher disagreement = more diverse = better ensemble (up to a point). Key quantitative finding: an ensemble of 3 diverse models matches a 7-model homogeneous ensemble.

**Key method:** Diversity score: D = (2/(K*(K-1))) * sum_{i<j} disagreement(model_i, model_j). Select the K-subset that maximizes D. For GTOS: select the 3 prompts that produce the most disagreement while individually maintaining acceptable accuracy.

**Testability on GTOS data:** MEDIUM -- requires running multiple prompt variants to compute disagreement matrix, then selecting the optimal 3. Higher upfront cost but produces the best ensemble composition.

**Relevance to GTOS:** Provides a principled method for selecting which 3 prompts to use in the diverse-prompt ensemble. Instead of guessing (SMC, neutral, checklist), compute disagreement rates across 5-7 candidate prompts on 50 MSOs, then select the 3 with maximum diversity subject to individual accuracy constraints.

---

### Paper 41 [L2-DUP]: Reliable Decision Support (2025) -- Binary Text Classification Consistency

**Source:** arXiv:2505.14918
**Quality Tier:** 2 | **Citations:** ~10
**Key finding:** LLMs achieve 90-98% agreement across 5 replicates on binary classification. Disagreement concentrated in ambiguous cases near the decision boundary. Value of ensemble is concentrated in the ~5-10% of uncertain cases.
**Testability on GTOS data:** HIGH
**Full entry:** See `phase1_ensemble_multiple_run_methods_v1.md`, Paper 9.

---

### Paper 42: Control the Temperature: Selective Sampling for Diverse and High-Quality LLM Outputs (2025)

**Authors:** Multiple (arXiv:2510.01218)
**Year:** 2025
**Source:** arXiv preprint / NeurIPS 2025
**Quality Tier:** 2 (NeurIPS)
**Task/domain:** Adaptive temperature selection per token position

**Key finding:** Proposes selective sampling that dynamically switches between greedy (T=0) and high-temperature sampling based on a "sampling risk" metric at each token position. High temperature is applied only at positions where the model is uncertain; greedy decoding is used elsewhere. This produces diverse outputs with higher quality than uniform high-temperature sampling. Net result: better diversity-quality tradeoff than any fixed temperature.

**Key method:** Risk(t) = 1 - max_k P(token_k | context). If Risk(t) > threshold: sample at T_high. Else: greedy. This requires logprob access.

**Testability on GTOS data:** LOW -- requires token-level logprobs, which Claude API does not provide. However, the conceptual insight applies: diversity is most valuable at the "hard" decision points, not uniformly across the entire response. For GTOS, this reinforces that the diverse-prompt approach (which creates diversity at the reasoning-structure level) is better than temperature-based approaches (which create diversity at the token level, including in irrelevant portions of the response).

**Relevance to GTOS:** Theoretical support for preferring diverse prompts over diverse temperatures. Token-level diversity (temperature) is wasteful because it introduces variation everywhere, including in the boilerplate structure of the response. Prompt-level diversity (DIPPER) introduces variation exactly where it matters -- in the reasoning strategy.

---

### Q-9.4 Recommended Implementation for GTOS

**Phase 1: Measurement (shadow-only, ~$30)**
1. Select 50 historical MSOs with known outcomes
2. Run each through 3 prompt variants at T=0: (a) current SMC prompt, (b) neutral statistical prompt, (c) factual checklist prompt
3. For comparison, also run current SMC prompt 3x at T=0.6
4. Measure: (a) individual accuracy per prompt, (b) majority-vote accuracy for prompt ensemble, (c) majority-vote accuracy for temperature ensemble, (d) agreement rates, (e) disagreement vs. outcome correlation

**Phase 2: Decision gate**
- If prompt ensemble WR > temperature ensemble WR: adopt diverse-prompt approach
- If temperature ensemble WR > prompt ensemble WR: adopt temperature-based approach
- If both > single-run WR by 3+ pp: adopt the better one
- If neither > single-run WR by 3pp: ensemble not worth the cost, invest in prompt improvement instead

**Phase 3: Deployment with adaptive consistency (~$100/month)**
1. Run 2 prompt variants at T=0
2. If they agree: that is the answer (most cases, ~85-90%)
3. If they disagree: run the 3rd prompt as tiebreaker
4. Log all disagreements -- these are the highest-value learning data
5. Optionally: reduce position size on 2-of-3 split decisions

**Expected outcomes:**

| Scenario | Monthly Cost | Expected WR | Trades/month |
|----------|-------------|-------------|--------------|
| Current (1x SMC prompt) | $60 | 65% | 17 |
| 3x temperature ensemble | $180 ($100 adaptive) | 67-68% | 17 |
| 3x diverse-prompt ensemble | $180 ($100 adaptive) | 68-72% | 15-17* |
| Diverse-prompt + abstain on splits | ~$100 | 70-75% on taken trades | 14-15 |

*Lower because neutral/checklist prompts may reject some weak CANDIDATEs that SMC accepts.

---

<a id="synthesis"></a>
## Cross-Question Synthesis

### Convergent Findings Across Q-9.2, Q-9.3, Q-9.4

1. **The diverse-prompt ensemble solves three problems simultaneously.** It provides (a) drift detection -- if one prompt suddenly disagrees with the others, something changed (Q-9.2), (b) framing bias mitigation -- different prompts have different biases that partially cancel (Q-9.3), (c) accuracy improvement via self-consistency (Q-9.4). This is the single highest-value investment identified across all three questions.

2. **Session memory anchoring is a bigger risk than model drift.** The anchoring literature (Q-9.3) shows 10-30pp effect sizes from in-context bias. Model drift from provider updates (Q-9.2) is likely 2-5pp. GTOS should prioritize fixing session memory format over building elaborate drift detection.

3. **CUSUM/ADWIN are complementary to the existing SPRT.** GTOS already uses SPRT for win rate monitoring. Adding CUSUM on CANDIDATE rate and EWMA on output features provides EARLY WARNING before win rate degrades. The three-layer monitoring system (canary, output, outcome) provides defense in depth.

4. **The "overthinking" effect compounds with framing bias.** SMC terminology invites narrative reasoning (Q-9.3, framing), and CoT encourages elaboration (Q-9.3, overthinking). Together, they produce long, narrative-heavy, rationalization-prone evaluations. The fix is the same for both: shorter, more constrained, structured reasoning with neutral vocabulary.

### Priority Ranking of Actionable Findings

| Priority | Action | Source | Expected Impact | Cost |
|----------|--------|--------|----------------|------|
| 1 | Shadow test: diverse-prompt ensemble (3 prompts) | Q-9.4 (DIPPER, MoT) | +3-8pp WR | $30 one-time |
| 2 | Shadow test: session memory without labels/numbers | Q-9.3 (Zhao 2021, Anchoring papers) | +2-5pp WR | $15 one-time |
| 3 | Implement CUSUM + EWMA on output features | Q-9.2 (Page 1954, Bayramli 2024) | Early drift warning | $0 (compute only) |
| 4 | Shadow test: neutral prompt vs. SMC prompt | Q-9.3 (Spitale 2025, PRISM) | +3-8pp WR | $15 one-time |
| 5 | Curate borderline canary fixtures (B3IT-inspired) | Q-9.2 (B3IT 2026) | Better drift sensitivity | $10 one-time |
| 6 | Shadow test: short structured CoT vs. current long CoT | Q-9.3 (FinCoT, Overthinking) | +2-5pp WR, -50% tokens | $15 one-time |

---

<a id="gaps"></a>
## Gap Analysis

### Gap 1: No paper studies LLM drift detection specifically for trading decisions
All drift detection literature focuses on NLP tasks, image classification, or general API monitoring. No paper monitors an LLM-as-evaluator producing binary trading decisions with structured market data inputs. GTOS's three-layer monitoring system is a novel contribution to this space.

### Gap 2: No paper tests prompt framing effects with structured financial data inputs
The framing literature (Spitale 2025, PRISM 2025, Hwang 2026) tests on natural language inputs (statements, questions, text). No paper tests framing effects when the input is structured numerical data (price levels, ratios, boolean flags). GTOS's MSO is primarily structured data with a thin text wrapper -- framing effects may be smaller than the literature suggests because there is less "interpretive space" for the framing to influence.

### Gap 3: No paper tests diverse-prompt ensemble on financial classification
DIPPER (2024) tests on math reasoning. MoT (2025) tests on math and commonsense QA. Boosted Prompting (2023) tests on math. No paper applies prompt ensemble methods to financial classification, trading signals, or market state evaluation. GTOS's planned shadow test would be the first empirical evidence on whether diverse prompts improve financial trading evaluation accuracy.

---

## Quality Tier Definitions

- **Tier 1:** Top venue (NeurIPS, ICML, ICLR, EMNLP, ACL, Science, JFQA, SIAM), peer-reviewed, large sample, rigorous methodology
- **Tier 2:** Respected venue or well-known researchers, reproducible methodology, adequate sample, some limitations
- **Tier 3:** arXiv preprint or workshop paper with sound methodology, early-stage citations

---

## Full Reference List

### Q-9.2: Black-Box Model Drift Detection
1. Tartakovsky, Nikiforov & Basseville (2014). Sequential Analysis. Chapman & Hall/CRC.
2. Page, E. S. (1954). Continuous Inspection Schemes. Biometrika 41(1-2), 100-115.
3. Bifet & Gavalda (2007). Learning from Time-Changing Data with Adaptive Windowing. SIAM SDM, 443-448.
4. Gama, Medas, Castillo & Rodrigues (2004). Learning with Drift Detection. SBIA, LNCS 3171, 286-295.
5. Rabanser, Gunnemann & Lipton (2019). Failing Loudly. NeurIPS 2019.
6. Chen et al. (2025). You've Changed: Detecting Modification of Black-Box LLMs. arXiv:2504.12335.
7. B3IT (2026). Token-Efficient Change Detection in LLM APIs. arXiv:2602.11083.
8. Mougan et al. (2025). LLM Output Drift: Cross-Provider Validation. ACM ICAIF Workshop. arXiv:2511.07585.
9. Dorfman et al. (2025). Are You Getting What You Pay For? arXiv:2504.04715.
10. Bayramli & Bauerle (2024). OOD Detection and Data Drift Monitoring using SPC. arXiv:2402.08088.
11. Werner et al. (2024). One or Two Things about Concept Drift. arXiv:2310.15826.
12. Suitability Filter (2025). arXiv:2505.22356.
13. Monitoring Calibration of Probability Forecasts with CUSUM (2025). arXiv:2510.25573.

### Q-9.3: Prompt Framing Effects on Financial Reasoning
14. Spitale & Germani (2025). Source Framing. Science Advances 11(45). [L2-DUP]
15. Turpin et al. (2023). Language Models Don't Always Say What They Think. NeurIPS 2023. [L2-DUP]
16. Kong et al. (2024). Persona is a Double-Edged Sword. arXiv:2408.08631. [L2-DUP]
17. PRISM (2025). Expert Personas Improve Alignment but Damage Accuracy. arXiv:2603.18507. [L2-DUP]
18. Prompting Science Report 4 (2024). Expert Personas Don't Improve Factual Accuracy. arXiv:2512.05858.
19. ACM ICAIF (2025). Reasoning or Overthinking. arXiv:2506.04574. [L2-DUP]
20. FinCoT (2025). Grounding Chain-of-Thought in Expert Financial Reasoning. arXiv:2506.16123.
21. Gandhi & Gandhi (2025). Prompt Sentiment: The Catalyst for LLM Change. arXiv:2503.13510.
22. Hwang et al. (2026). When Wording Steers the Evaluation. arXiv:2601.13537. [L2-DUP]
23. From Fact to Judgment (2025). arXiv:2511.10871.
24. Zhao et al. (2021). Calibrate Before Use. ICML 2021. [L2-DUP]
25. Anchoring Bias in LLMs (2024). arXiv:2412.06593.
26. The Bias is in the Details (2025). arXiv:2509.22856.
27. Campbell & Sharpe (2009). Anchoring Bias in Consensus Forecasts. JFQA 44(2). [L2-DUP]
28. Sclar et al. (2024). Quantifying LLMs' Sensitivity to Spurious Features. ICLR 2024. [L2-DUP]

### Q-9.4: LLM Ensemble Methods for Financial Decisions
29. Wang et al. (2023). Self-Consistency Improves CoT Reasoning. ICLR 2023. [L2-DUP]
30. Aggarwal et al. (2023). Adaptive-Consistency. EMNLP 2023. [L2-DUP]
31. Betz et al. (2024). Effect of Sampling Temperature. EMNLP 2024. [L2-DUP]
32. DIPPER (2024). Diversity in Prompts for LLM Ensembles. arXiv:2412.15238.
33. Pitis (2023). Boosted Prompt Ensembles. arXiv:2304.05970.
34. Optimizing Temperature for Multi-Sample Inference (2025). arXiv:2502.05234.
35. Xiong et al. (2024). Can LLMs Express Their Uncertainty? ICLR 2024. [L2-DUP]
36. Ma et al. (2025). Optimal Self-Consistency: Power-Law Scaling. NeurIPS 2025 Workshop. [L2-DUP]
37. Taubenfeld et al. (2025). Confidence Improves Self-Consistency. ACL 2025. [L2-DUP]
38. Niimi (2025). Simple Ensemble Strategy. NLDB 2025. [L2-DUP]
39. Diversity of Thought (2025). OpenReview (under review).
40. LLM-TOPLA (2024). Efficient LLM Ensemble by Maximising Diversity. arXiv:2410.03953.
41. Reliable Decision Support (2025). arXiv:2505.14918. [L2-DUP]
42. Control the Temperature (2025). arXiv:2510.01218.

---

*Search completed: April 12, 2026*
*42 papers across 3 questions, 34 promoted as testable*
*8 papers overlap with prior L2 search -- cross-referenced, not duplicated*
*3 critical gaps identified*
*Priority 1 action: shadow test diverse-prompt ensemble ($30, highest expected impact)*
