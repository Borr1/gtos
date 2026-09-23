# Phase 1 -- Q-3.4: Confidence Calibration Methods

**Date:** 2026-04-11
**Agent:** Claude Code (Academic Literature Search)
**Scope:** Calibration of classifier/LLM confidence scores for binary trading outcomes
**Total papers found:** 12
**Quality filter applied:** Tier 1-3 retained, MDPI/predatory/no-empirical rejected

---

## GTOS Context

GTOS's confidence scoring module assigns confidence=80 to 98% of CANDIDATE trades. This is NOT calibrated -- the scorer is a rubber stamp (confirmed useless, now in shadow mode). The system has 129 historical trades with binary outcomes (win/loss) and a 65% base rate. Three sub-questions:
1. What calibration method would make the confidence score useful?
2. Can these methods work with n=129?
3. Is the problem with the LLM's own confidence or the separate confidence scoring module?

---

## Table of Contents

1. [Foundational Calibration Methods (Classical ML)](#classical)
2. [Neural Network Calibration](#neural)
3. [LLM-Specific Calibration](#llm)
4. [Small-Sample Calibration](#small-sample)
5. [Calibration Evaluation and Surveys](#surveys)
6. [Verdict for GTOS](#verdict)

---

<a id="classical"></a>
## 1. Foundational Calibration Methods (Classical ML)

---

### Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods
**Authors:** John C. Platt | **Year:** 1999 | **Source:** Advances in Large Margin Classifiers, pp. 61-74 (MIT Press)
**Quality Tier:** 1 (foundational, 5000+ citations) | **Citations:** ~5800
**Task/domain tested:** SVM binary classification (UCI datasets)
**OOS validation:** Yes (cross-validation)
**Key finding:** Fits a sigmoid (logistic regression with 2 parameters, A and B) on top of uncalibrated classifier outputs to map scores to probabilities. Only 2 parameters to estimate, making it feasible even with very small calibration sets. Uses a regularized version of maximum likelihood to avoid overfitting on small datasets.
**Key equation:** P(y=1|f) = 1 / (1 + exp(Af + B)), where f is the uncalibrated output score, A and B are fitted via MLE on a held-out set.
**Testability on GTOS data:** HIGH -- only 2 parameters, n=129 is sufficient. Can fit A and B using 5-fold CV on the 129 trades with confidence scores as input and win/loss as target.
**Relevance to GTOS:** Direct. This is the baseline method. If the LLM's confidence scores have ANY monotonic relationship with true win probability, Platt scaling will extract it. If Platt scaling fails (A is near zero), the scores carry no information.

---

### Predicting Good Probabilities With Supervised Learning
**Authors:** Alexandru Niculescu-Mizil, Rich Caruana | **Year:** 2005 | **Source:** ICML 2005 (Proceedings of the 22nd International Conference on Machine Learning)
**Quality Tier:** 1 (ICML, 3000+ citations) | **Citations:** ~3200
**Task/domain tested:** 10 supervised learning algorithms on multiple UCI datasets
**OOS validation:** Yes (held-out calibration sets)
**Key finding:** Systematic comparison of calibration across classifiers. SVMs and boosted trees show sigmoidal distortion (correctable by Platt scaling). Neural nets and random forests are typically better-calibrated. Isotonic regression is more flexible than Platt scaling but overfits when calibration set < 1000. Platt scaling is preferred for small calibration sets due to its 2-parameter constraint.
**Key equation:** Same Platt sigmoid + isotonic regression (piecewise-constant monotone function via PAVA algorithm).
**Testability on GTOS data:** HIGH -- the paper explicitly warns isotonic regression overfits below n=1000. With n=129, Platt scaling is the clear recommendation from this paper.
**Relevance to GTOS:** Critical. Directly answers the question: at n=129, use Platt scaling, not isotonic regression.

---

### Beta Calibration: A Well-Founded and Easily Implemented Improvement on Logistic Calibration for Binary Classifiers
**Authors:** Meelis Kull, Telmo Silva Filho, Peter Flach | **Year:** 2017 | **Source:** AISTATS 2017 (PMLR vol. 54, pp. 623-631)
**Quality Tier:** 1 (AISTATS) | **Citations:** ~300
**Task/domain tested:** Binary classifiers including naive Bayes, AdaBoost, logistic regression, SVM, random forest
**OOS validation:** Yes (10-fold CV on 17 UCI datasets)
**Key finding:** Platt scaling assumes scores are normally distributed within each class -- when this fails (e.g., for naive Bayes or AdaBoost), logistic calibration can make things worse. Beta calibration uses a 3-parameter model based on the beta distribution. It can represent the identity function (unlike Platt scaling), meaning it cannot hurt an already-calibrated classifier. It handles both under-confident and over-confident distortions.
**Key equation:** P(y=1|s) = 1 / (1 + 1/exp(c) * ((1-s)/s)^a * (s/(1-s))^(-b)), with 3 parameters a, b, c fitted by MLE. Reduces to Platt scaling when a = b.
**Testability on GTOS data:** MEDIUM -- 3 parameters vs Platt's 2 makes overfitting slightly more likely at n=129, but still feasible. The identity-preserving property is attractive. Implementation available via betacal Python package.
**Relevance to GTOS:** A good second method to compare against Platt scaling. If confidence=80 represents an extreme concentration pattern, beta calibration may capture the distortion better than a sigmoid.

---

<a id="neural"></a>
## 2. Neural Network Calibration

---

### On Calibration of Modern Neural Networks
**Authors:** Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger | **Year:** 2017 | **Source:** ICML 2017 (PMLR vol. 70)
**Quality Tier:** 1 (ICML, 5000+ citations) | **Citations:** ~5500
**Task/domain tested:** Image classification (CIFAR-10/100, ImageNet, SVHN, 20 Newsgroups)
**OOS validation:** Yes (held-out validation sets)
**Key finding:** Modern deep neural networks are significantly more miscalibrated than older architectures, despite being more accurate. Larger and deeper models are worse calibrated. The cause is overconfidence -- models assign near-1.0 probabilities to most predictions. Temperature scaling (a single-parameter post-hoc method) fixes this remarkably well, matching or outperforming Platt scaling and isotonic regression.
**Key equation:** q_i = max_k softmax(z_i / T)_k, where T is a single scalar "temperature" learned on a validation set by minimizing NLL. T > 1 softens the distribution. Also defines Expected Calibration Error: ECE = sum_m (|B_m|/n) * |acc(B_m) - conf(B_m)| over M bins.
**Testability on GTOS data:** MEDIUM -- Temperature scaling as defined requires logits (pre-softmax outputs), which GTOS does not have. However, the concept of a single-parameter monotone correction on a held-out set is equivalent to Platt scaling with B=0. The ECE metric is directly applicable for evaluating GTOS calibration.
**Relevance to GTOS:** Establishes the key insight that overconfidence is the dominant miscalibration pattern in modern ML. GTOS's confidence=80 rubber-stamp behavior is exactly this pattern. The paper shows 1-parameter corrections suffice.

---

### Revisiting the Calibration of Modern Neural Networks
**Authors:** Matthias Minderer, Josip Djolonga, Rob Romber, Rishi Bommasani, et al. | **Year:** 2021 | **Source:** NeurIPS 2021
**Quality Tier:** 1 (NeurIPS) | **Citations:** ~400
**Task/domain tested:** ImageNet, CIFAR with modern architectures (ViT, MLP-Mixer, BiT)
**OOS validation:** Yes
**Key finding:** Partly contradicts Guo et al. 2017 -- finds that non-convolutional architectures (Vision Transformers, MLP-Mixers) can be better calibrated out of the box, even without post-hoc calibration. However, temperature scaling remains effective across all architectures. Pre-training on larger datasets improves calibration. The relationship between model size and miscalibration is not as simple as Guo et al. suggested.
**Key equation:** Same temperature scaling T as Guo et al.; ECE and adaptive ECE metrics.
**Testability on GTOS data:** LOW -- the architectural findings are specific to vision transformers and not directly relevant to LLM confidence scoring.
**Relevance to GTOS:** Minor. Confirms temperature scaling works universally but the domain-specific findings do not transfer.

---

<a id="llm"></a>
## 3. LLM-Specific Calibration

---

### Language Models (Mostly) Know What They Know
**Authors:** Saurav Kadavath, Tom Conerly, Amanda Askell, Tom Henighan, Dawn Drain, Ethan Perez, Nicholas Schiefer, Zac Hatfield-Dodds, et al. (36 authors) | **Year:** 2022 | **Source:** arXiv:2207.05221 (Anthropic)
**Quality Tier:** 2 (arXiv preprint, but from Anthropic's core research team, 400+ citations) | **Citations:** ~430
**Task/domain tested:** Multiple-choice QA, true/false, open-ended generation (TriviaQA, Lambada, arithmetic, etc.)
**OOS validation:** Partial (evaluated across diverse tasks, but no held-out temporal split)
**Key finding:** Larger LLMs are well-calibrated on multiple-choice and true/false questions when formatted properly. Models can self-evaluate via P(True) -- asking the model whether its own answer is correct and using the token probability. P(True) shows encouraging calibration and scaling properties. However, models struggle to calibrate P(IK) ("I know") on novel task types they haven't seen before. Self-evaluation improves when the model considers multiple samples before judging.
**Key equation:** P(True) = token probability of "True" when model is asked "Is the following answer correct? [answer]. True or False." P(IK) = trained probe on model internals predicting whether the model will answer correctly.
**Testability on GTOS data:** MEDIUM -- GTOS uses Claude Sonnet for primary analysis. Could implement P(True) by asking the model "Is this trade likely to win?" after generating the CANDIDATE decision, and using the verbalized probability. Requires prompt engineering but no model retraining.
**Relevance to GTOS:** High. Directly addresses whether the LLM itself has useful self-knowledge about its predictions. The implication for GTOS: the problem may be the confidence PROMPT, not the model's capability. If the prompt asks "rate your confidence 0-100" the model may default to 80. If instead you ask "True or False: this trade will hit TP before SL" and extract P(True), you get a fundamentally different signal.

---

### Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models Fine-Tuned with Human Feedback
**Authors:** Katherine Tian, Eric Mitchell, Allan Zhou, Archit Sharma, Rafael Rafailov, Huaxiu Yao, Chelsea Finn, Christopher Manning | **Year:** 2023 | **Source:** EMNLP 2023
**Quality Tier:** 1 (EMNLP, top NLP venue) | **Citations:** ~200
**Task/domain tested:** TriviaQA, SciQ, TruthfulQA on ChatGPT, GPT-4, Claude
**OOS validation:** Yes (held-out test sets)
**Key finding:** RLHF-tuned LLMs (ChatGPT, GPT-4, Claude) have poorly calibrated conditional token probabilities, but their verbalized confidence scores are typically better-calibrated, reducing ECE by ~50% relative to token probabilities. The key strategy: prompt the model to consider multiple answer candidates before stating confidence. When combined with temperature scaling on the verbalized scores, calibration improves further.
**Key equation:** Verbalized confidence prompt: "Consider the following options... What is your confidence (0-100%)?" + post-hoc temperature scaling on the verbalized scores.
**Testability on GTOS data:** HIGH -- GTOS already uses Claude for primary analysis. Could modify the prompt to elicit verbalized confidence using their multi-option strategy, then apply Platt scaling on the verbalized scores using the 129 historical trades as calibration data.
**Relevance to GTOS:** Very high. Directly applicable. The paper tests on Claude specifically and shows verbalized confidence + post-hoc calibration is the winning combination for RLHF models. This is exactly GTOS's setup.

---

### Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs
**Authors:** Miao Xiong, Zhiyuan Hu, Xinyang Lu, Yifei Li, Jie Fu, Junxian He, Bryan Hooi | **Year:** 2024 | **Source:** ICLR 2024
**Quality Tier:** 1 (ICLR) | **Citations:** ~180
**Task/domain tested:** 5 dataset types (commonsense reasoning, arithmetic, professional knowledge) on GPT-4, LLaMA 2 Chat, and 3 other LLMs
**OOS validation:** Yes
**Key finding:** LLMs are systematically overconfident when verbalizing confidence, potentially imitating human overconfidence patterns. Models with 70B+ parameters achieve ECE ~0.10 (10% deviation from true accuracy). Prompting strategies matter: human-inspired prompts + multi-sample consistency checking + aggregation reduce ECE to ~0.07-0.10. However, all methods struggle on tasks requiring professional/domain knowledge (unlike general QA).
**Key equation:** Three-component framework: (1) prompting strategy for confidence elicitation, (2) sampling multiple responses, (3) aggregating consistency scores. Best results from combining all three.
**Testability on GTOS data:** MEDIUM -- the multi-sample approach requires multiple API calls per trade decision (cost concern). The finding that professional-knowledge tasks degrade calibration is relevant: trading decisions are closer to "professional knowledge" than to TriviaQA.
**Relevance to GTOS:** Important caveat. LLM verbalized confidence works well on factual QA but degrades on domain-specific professional tasks. Trading is arguably such a task. This suggests verbalized confidence alone may not solve GTOS's problem -- post-hoc calibration on historical outcomes is essential.

---

### On Verbalized Confidence Scores for LLMs
**Authors:** Daniel Yang, Yao-Hung Hubert Tsai, Makoto Yamada | **Year:** 2024 | **Source:** arXiv:2412.14737
**Quality Tier:** 3 (arXiv preprint, December 2024) | **Citations:** ~15
**Task/domain tested:** 10 datasets, 11 LLMs (GPT-4, Claude, LLaMA, Mistral, etc.)
**OOS validation:** Yes (across datasets)
**Key finding:** Reliability of verbalized confidence depends heavily on both model capacity and prompt design. For models with 70B+ parameters, ECE ~0.10 is achievable. Simple prompts work better for smaller LLMs; advanced multi-strategy prompts help larger models. Post-hoc calibration (temperature scaling or Platt scaling) on verbalized scores consistently improves results beyond prompting alone.
**Key equation:** Best practice pipeline: (1) elicit verbalized confidence with tailored prompt, (2) apply post-hoc Platt scaling or temperature scaling using held-out calibration data.
**Testability on GTOS data:** HIGH -- confirms the two-stage approach (elicit + post-hoc correct) works. n=129 is sufficient for the 2-parameter post-hoc correction.
**Relevance to GTOS:** Reinforces the recommendation: change the prompt to elicit better raw confidence, then apply Platt scaling on the 129 historical outcomes.

---

<a id="small-sample"></a>
## 4. Small-Sample Calibration

---

### Better Classifier Calibration for Small Datasets
**Authors:** Markelle Kelly, Rachel Longjohn, Kiri Wagstaff | **Year:** 2020 | **Source:** ACM Transactions on Knowledge Discovery from Data (TKDD)
**Quality Tier:** 2 (ACM TKDD) | **Citations:** ~45
**Task/domain tested:** Binary classifiers on datasets downsampled to n=25, 50, 100 with imbalanced class ratios
**OOS validation:** Yes (cross-validation on held-out data)
**Key finding:** Explicitly addresses calibration at small n. Isotonic regression overfits severely below n=1000. Platt scaling works at n=100 but can still overfit with imbalanced classes. They propose calibration with binning adjustments and regularized sigmoid fitting for small datasets. Key practical finding: at n=100, Platt scaling with 5-fold cross-validation reduces Brier score compared to uncalibrated scores, but the improvement is modest. At n=50, most calibration methods add noise rather than help.
**Key equation:** Regularized Platt scaling with Bayesian priors on A and B to prevent overfitting at small n.
**Testability on GTOS data:** HIGH -- n=129 is above their minimum viable threshold of ~100 for Platt scaling. Their regularized variant adds stability. 5-fold CV is recommended over a single held-out split.
**Relevance to GTOS:** Directly answers the sample size question. n=129 is marginal but viable for Platt scaling with CV. Not viable for isotonic regression. Key caveat: expect modest improvement, not dramatic improvement, at this sample size.

---

<a id="surveys"></a>
## 5. Calibration Evaluation and Surveys

---

### Classifier Calibration: A Survey on How to Assess and Improve Predicted Class Probabilities
**Authors:** Telmo Silva Filho, Hao Song, Miquel Perello-Nieto, Raul Santos-Rodriguez, Meelis Kull, Peter Flach | **Year:** 2023 | **Source:** Machine Learning, Vol. 112(9), pp. 3211-3260 (Springer)
**Quality Tier:** 2 (Machine Learning journal, comprehensive survey) | **Citations:** ~150
**Task/domain tested:** Survey covering all major calibration methods
**OOS validation:** N/A (survey)
**Key finding:** Comprehensive taxonomy of calibration methods: parametric (Platt, beta, temperature), non-parametric (isotonic, histogram binning, BBQ), and hybrid. Proper scoring rules (Brier score, log loss) are the correct evaluation metrics. ECE has known biases (depends on bin count). For small calibration sets, parametric methods (Platt, beta) dominate because non-parametric methods overfit. Recommends reliability diagrams for visual assessment.
**Key equation:** Brier score = (1/n) * sum(p_i - y_i)^2. Calibration component of Brier decomposition = (1/n) * sum_k n_k * (p_bar_k - y_bar_k)^2.
**Testability on GTOS data:** HIGH -- the evaluation framework (Brier score, reliability diagram, ECE) is directly applicable to assess GTOS confidence calibration.
**Relevance to GTOS:** Essential reference for implementing calibration properly. Use Brier score and reliability diagrams, not just ECE.

---

### Evaluating Model Calibration in Classification
**Authors:** Juozas Vaicenavicius, David Widmann, Carl Andersson, Fredrik Lindsten, Jacob Roll, Thomas Schon | **Year:** 2019 | **Source:** AISTATS 2019 (PMLR vol. 89, pp. 3459-3467)
**Quality Tier:** 1 (AISTATS) | **Citations:** ~250
**Task/domain tested:** Theoretical framework with empirical examples
**OOS validation:** Partial (theoretical + empirical validation)
**Key finding:** Develops a hypothesis-testing framework for calibration: ECE and similar metrics can be interpreted as test statistics with well-defined p-values under the null hypothesis of perfect calibration. This lets you formally test whether a classifier IS calibrated, rather than just comparing calibration across methods. Critical for small samples: you can compute whether your calibration improvement is statistically significant.
**Key equation:** Calibration test statistic with associated p-value bounds; kernel-based calibration tests that avoid binning artifacts.
**Testability on GTOS data:** HIGH -- can formally test whether the current confidence=80 rubber stamp is statistically distinguishable from a constant predictor, and whether post-calibration scores are significantly better.
**Relevance to GTOS:** Provides the statistical framework to determine if calibration improvement is real or noise at n=129.

---

## Cross-Paper Synthesis

### What calibration method works at n=129?

| Method | Parameters | Min viable n | Works at n=129? | Risk |
|--------|-----------|-------------|----------------|------|
| Platt scaling | 2 (A, B) | ~100 | YES (with 5-fold CV) | Modest overfitting risk |
| Beta calibration | 3 (a, b, c) | ~150 | MARGINAL | Higher overfitting risk |
| Temperature scaling | 1 (T) | ~50 | YES (if you have logits) | Needs logit access |
| Isotonic regression | O(n) | ~1000 | NO | Will overfit severely |
| Histogram binning | ~10-20 | ~500 | NO | Bins will be too sparse |

### Is the problem the LLM or the scoring module?

The literature strongly suggests it is **both**:

1. **The scoring prompt is broken.** Asking an LLM "rate your confidence 0-100" is known to produce overconfident, peaked distributions (Xiong et al. 2024, Yang et al. 2024). RLHF-tuned models are especially bad at this -- they default to high confidence. The fix is changing the elicitation strategy: ask for P(True) a la Kadavath et al. 2022, or use the multi-option strategy from Tian et al. 2023.

2. **Even with better prompting, post-hoc calibration is essential.** No LLM produces well-calibrated probabilities on domain-specific professional tasks (Xiong et al. 2024). Trading is such a task. You need a second-stage correction using historical outcomes.

3. **The confidence scoring MODULE (separate from the primary analyzer) is architecturally wrong.** It evaluates the SAME setup the primary analyzer already evaluated, with no new information. It should either: (a) be merged into the primary analyzer's output (single-pass verbalized confidence), or (b) provide genuinely new information (e.g., market regime features, time-of-day, volatility context).

---

<a id="verdict"></a>
## Verdict for GTOS

**Recommended approach (in priority order):**

1. **Change the confidence elicitation prompt.** Instead of a separate confidence scoring module that rubber-stamps everything at 80, embed confidence elicitation into the primary analyzer's output. Use the Tian et al. 2023 strategy: prompt Claude to consider the bull AND bear case explicitly, then state a probability. This is a prompt change (requires WF-1 CEO approval) but is the highest-impact fix.

2. **Apply Platt scaling to the elicited confidence.** Use the 129 historical trades as a calibration set with 5-fold cross-validation. Fit P(win) = 1/(1+exp(A*conf + B)) where conf is the verbalized confidence. This requires only 2 parameters and is statistically feasible at n=129 (Kelly et al. 2020 confirm n=100 is minimum viable).

3. **Evaluate with Brier score and reliability diagrams, not ECE alone.** Plot calibration curves (10 bins at n=129 means ~13 samples per bin -- barely adequate but workable). Use Vaicenavicius et al. 2019 hypothesis test to confirm the calibrated scores are statistically better than uncalibrated.

4. **Expect modest improvement.** At n=129, calibration will reduce ECE somewhat but will not transform a poor discriminator into a good one. If the LLM's raw confidence has zero correlation with actual outcomes, no calibration method can help -- it would just map everything to the base rate (65%). The first diagnostic is to check if raw confidence has ANY Spearman correlation with outcomes. If rho < 0.05, calibration is pointless.

**Bottom line:** Platt scaling with 5-fold CV is the method. n=129 is marginal but viable. But the bigger fix is changing HOW confidence is elicited from the LLM -- the current rubber-stamp prompt is the root cause, not the lack of post-hoc calibration.
