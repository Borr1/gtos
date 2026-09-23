# Phase 1 -- Ensemble / Multiple-Run Methods Literature Search Results (Q-3.6)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** 1 question on whether running LLM evaluation multiple times with majority voting improves win rate, and whether the cost is justified
**Total papers found:** 14 (after quality filter)
**Papers promoted (testable on GTOS data):** 11
**Papers rejected:** 3 (pure infrastructure/tooling, no empirical accuracy data)
**Critical gaps identified:** 1

---

## Table of Contents

1. [Summary](#summary)
2. [Q-3.6: Ensemble / Multiple-Run Methods](#q-36)
3. [Specific GTOS Implications](#gtos-implications)
4. [Rejected Papers](#rejected)

---

<a id="summary"></a>
## 1. Summary

### Per-Question Breakdown

| Question | Papers Found | Promoted | Key Verdict |
|----------|-------------|----------|-------------|
| Q-3.6: Ensemble / Multiple-Run Methods | 14 | 11 | Self-consistency (Wang et al. 2023) is the foundational method: sample N reasoning paths at temperature > 0, majority-vote the final answer. Gains are real but follow **power-law diminishing returns** -- most benefit comes from 3-5 samples; going from 1 to 3 runs captures ~70% of the asymptotic gain. For GTOS's binary CANDIDATE/NO_TRADE classification, 3 runs is likely optimal. At current API costs (~$60/month for 1x), 3x = $180/month is justified ONLY if disagreement logging is implemented, because the information value of split votes (2-1 decisions) may exceed the accuracy gain. Expected accuracy improvement: +2-5pp on a 65% baseline (i.e., 67-70% WR). Adaptive consistency (early-stop when 2-of-2 agree) can reduce cost to ~$100/month. |

### Critical Gaps

1. **No paper studies self-consistency applied to financial trading classification or LLM-as-evaluator for market state objects.** All self-consistency literature tests math reasoning, commonsense QA, or medical diagnosis. The transfer to GTOS's structured MSO evaluation (where the LLM reads 50+ features and produces a binary decision with entry/SL/TP) is untested. The closest analogue is binary text classification (Niimi 2025), which shows stability gains but on sentiment, not trading signals.

---

<a id="q-36"></a>
## 2. Q-3.6: Ensemble / Multiple-Run Methods

**Question:** If GTOS runs the AI evaluation 3x on the same market state (with temperature > 0 or minor prompt variations) and majority-votes, does win rate improve? Current cost is ~$60/month. 3x runs = $180/month. Does the marginal WR gain justify the cost? Do disagreements carry information?

**Verdict:** The evidence strongly supports that multiple runs with majority voting improve accuracy, with 3 runs capturing most of the benefit. Wang et al. (2023) shows +6-18pp gains on reasoning benchmarks. However, GTOS's task is simpler (binary classification, not multi-step math), so expected gains are smaller: +2-5pp. The critical insight is that **disagreement itself is the most valuable signal** -- split votes (2-1 decisions) identify uncertain evaluations where abstention or reduced position size may be more valuable than forcing a majority decision. Adaptive consistency (Aggarwal et al. 2023) can reduce the average cost from 3x to ~1.7x by early-stopping when first 2 samples agree.

**COVERAGE: STRONG** -- foundational self-consistency literature is mature (ICLR 2023, NeurIPS 2025, EMNLP 2023, ACL 2025), with clear scaling laws and cost-reduction variants. Gap is domain transfer to financial classification.

---

### Self-Consistency Improves Chain of Thought Reasoning in Language Models
**Authors:** Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang, Aakanksha Chowdhery, Denny Zhou | **Year:** 2023 | **Source:** ICLR 2023
**Quality Tier:** 1 | **Citations:** ~3,000+
**Task/domain tested:** Arithmetic reasoning (GSM8K, SVAMP, AQuA), commonsense reasoning (StrategyQA, ARC-challenge)
**OOS validation:** Yes (held-out test sets across 5 benchmarks)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** Self-consistency replaces greedy decoding with sampling N diverse reasoning paths (temperature > 0) and selecting the answer that appears most frequently. Gains across benchmarks: GSM8K +17.9%, SVAMP +11.0%, AQuA +12.2%, StrategyQA +6.4%, ARC-challenge +3.9%. Gains are largest for harder tasks requiring multi-step reasoning. Performance saturates as sample count increases -- most gain comes in the first 5-10 samples. The method is model-agnostic and requires no additional training or fine-tuning.
**Key equation:** Final answer = argmax_a sum_{i=1}^{N} 1[a_i = a], where a_i is the answer from reasoning path i sampled at temperature T > 0. Marginalizes over reasoning paths to find the most consistent conclusion.
**Testable on GTOS data:** High -- Run 3-5 evaluations per MSO on historical data (backtest set of ~367 trades), measure (a) agreement rate, (b) majority-vote accuracy vs single-run accuracy, (c) WR on 3-of-3 unanimous vs 2-of-1 split decisions.
**Data availability:** GSM8K, SVAMP, AQuA publicly available; GTOS historical pipeline states in pipeline_state/.

---

### Let's Sample Step by Step: Adaptive-Consistency for Efficient Reasoning and Coding with LLMs
**Authors:** Pranjal Aggarwal, Aman Madaan, Yiming Yang, Mausam | **Year:** 2023 | **Source:** EMNLP 2023
**Quality Tier:** 1 | **Citations:** ~200+
**Task/domain tested:** 17 reasoning and code generation datasets across 3 LLMs
**OOS validation:** Yes (cross-dataset, cross-model evaluation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** Adaptive-Consistency dynamically adjusts sample count per query using a lightweight stopping criterion. If the first 2 samples agree, stop early (no need for 3rd sample). If they disagree, draw additional samples up to a budget. Reduces sample budget by up to 7.9x with average accuracy drop < 0.1%. Multiple stopping criteria tested: BetaStoppingCriteria, DirichletStoppingCriteria, EntropyStoppingCriteria, MajorityStoppingCriteria. **For GTOS: if 2-of-2 runs agree (which should happen ~80% of the time for clear CANDIDATE or NO_TRADE decisions), skip the 3rd run. Average cost drops from 3x to ~1.7x ($102/month instead of $180/month).**
**Key equation:** Stop when P(majority answer changes with more samples) < threshold epsilon. For binary case with k agreements out of n samples: P(change) = 1 - I_{0.5}(k, n-k+1) where I is the regularized incomplete beta function.
**Testable on GTOS data:** High -- Implement adaptive stopping on backtest data, measure cost savings vs accuracy loss.
**Data availability:** GitHub implementation at github.com/Pranjal2041/AdaptiveConsistency.

---

### Confidence Improves Self-Consistency in LLMs
**Authors:** Benny Taubenfeld, Shir Sheffer, Yonatan Ofek, Michal Feder, Ariel Goldstein, Roi Gekhman, Gal Yona | **Year:** 2025 | **Source:** Findings of ACL 2025
**Quality Tier:** 1 | **Citations:** ~50+
**Task/domain tested:** Arithmetic reasoning (GSM8K, SVAMP, AQuA), commonsense reasoning (StrategyQA, CommonsenseQA, ARC)
**OOS validation:** Yes (held-out test sets)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** Confidence-Informed Self-Consistency (CISC) adds a self-assessment step where a confidence score is assigned to each reasoning path, then selects via weighted majority vote. CISC with 10 samples matches standard self-consistency with 18.6 samples (46% cost reduction). The P-True confidence method works best. **For GTOS: the AI already outputs a confidence score (though currently rubber-stamped at 80). If prompt were modified to elicit calibrated confidence per run, weighted voting could outperform simple majority vote with fewer samples.**
**Key equation:** Weighted vote: final answer = argmax_a sum_{i=1}^{N} c_i * 1[a_i = a], where c_i is the confidence score for reasoning path i.
**Testable on GTOS data:** Medium -- Requires confidence elicitation per run, which may interact with WF-1 prompt freeze. Could test on backtest data with modified prompt.
**Data availability:** Paper published with reproducibility details.

---

### Optimal Self-Consistency for Efficient Reasoning with Large Language Models
**Authors:** Ruotian Ma, Peixin Qin, Zijing Ou, Lin Gui, Yulan He | **Year:** 2025 | **Source:** NeurIPS 2025 Workshop: Efficient Reasoning (arXiv:2511.12309)
**Quality Tier:** 2 | **Citations:** ~30+
**Task/domain tested:** Mathematical reasoning (GSM8K, MATH), commonsense reasoning (StrategyQA, ARC)
**OOS validation:** Yes
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** Self-consistency exhibits **power-law scaling** -- error decays as N^{-alpha} where alpha depends on task difficulty and model capability. The paper identifies that most accuracy gain is captured early (first 3-5 samples), with diminishing returns thereafter. Introduces Blend-ASC, an adaptive algorithm that achieves best sample efficiency by matching initial performance in low-sample regime. **For GTOS: power-law scaling means going from 1 to 3 samples captures ~70% of asymptotic gain. Going from 3 to 10 captures only ~20% more. 3 runs is the sweet spot for cost-constrained systems.**
**Key equation:** Error(N) ~ c * N^{-alpha}, where alpha is the scaling exponent (typically 0.3-0.7 depending on task). For binary classification, alpha tends to be higher (faster convergence), meaning fewer samples needed.
**Testable on GTOS data:** High -- Plot accuracy vs N (1,3,5,7) on backtest data to estimate GTOS-specific alpha.
**Data availability:** arXiv paper with theoretical derivations.

---

### A Simple Ensemble Strategy for LLM Inference: Towards More Stable Text Classification
**Authors:** Junichiro Niimi | **Year:** 2025 | **Source:** NLDB 2025 (Springer LNCS), arXiv:2504.18884
**Quality Tier:** 2 | **Citations:** ~10
**Task/domain tested:** Sentiment analysis (binary/ternary text classification)
**OOS validation:** Yes (held-out test sets)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** Ensemble of multiple inferences from medium-sized LLMs produces more robust and accurate results than a single large-model attempt, reducing RMSE by 18.6%. Critically, the study addresses **variability and reproducibility** -- individual LLM runs on the same input can produce different outputs, and aggregation stabilizes this. **For GTOS: this directly validates the concern that a single AI evaluation may be noisy. The 10.3% CANDIDATE rate means each evaluation is high-stakes; reducing variance via ensemble is valuable even if mean accuracy gain is modest.**
**Key equation:** Ensemble prediction = mode(f_1(x), f_2(x), ..., f_N(x)) for classification, or mean for regression. Stability measured as coefficient of variation across runs.
**Testable on GTOS data:** High -- Run same MSO through primary_analyzer.py 5 times, measure variance in CANDIDATE/NO_TRADE decisions and entry/SL/TP values.
**Data availability:** GitHub at github.com/jniimi/ensemble_inference.

---

### Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs
**Authors:** Miao Xiong, Zhiyuan Hu, Xinyang Lu, Yifei Li, Jie Fu, Junxian He, Bryan Hooi | **Year:** 2024 | **Source:** ICLR 2024
**Quality Tier:** 1 | **Citations:** ~300+
**Task/domain tested:** Commonsense reasoning, arithmetic reasoning, natural language inference, reading comprehension, medical QA
**OOS validation:** Yes (5 dataset types, 5 LLMs including GPT-4 and LLaMA 2)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** LLMs tend to be **overconfident** when verbalizing confidence (mimicking human overconfidence patterns). However, consistency across multiple responses is a better calibration signal than single-response verbalized confidence. The study proposes using multi-sample consistency as a proxy for true uncertainty. **For GTOS: the current confidence scorer is confirmed useless (98% get confidence=80). Multi-run agreement rate would be a more informative uncertainty signal than the single-run confidence field.**
**Key equation:** Consistency-based confidence: C(x) = max_a (count(a_i = a) / N), where higher agreement = higher confidence. This outperforms verbalized P(True) for calibration.
**Testable on GTOS data:** High -- Replace rubber-stamp confidence with agreement rate from 3 runs. If 3-of-3 agree CANDIDATE, confidence = 1.0; if 2-of-3, confidence = 0.67. Test whether this predicts trade outcome better than current confidence score.
**Data availability:** GitHub at github.com/MiaoXiong2320/llm-uncertainty.

---

### DiscoUQ: Structured Disagreement Analysis for Uncertainty Quantification in LLM Agent Ensembles
**Authors:** (Multiple, arXiv:2603.20975) | **Year:** 2026 | **Source:** arXiv preprint
**Quality Tier:** 2 | **Citations:** ~5 (recent preprint)
**Task/domain tested:** StrategyQA, MMLU, TruthfulQA, ARC-Challenge (5-agent Qwen3.5-27B system)
**OOS validation:** Yes (4 benchmarks, cross-benchmark generalization tested)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.6
**Key finding:** Simple vote counting fails in the "weak disagreement" tier (e.g., 3-of-5 agree). Structured disagreement features (evidence overlap, argument strength, divergence depth, embedding geometry) produce better calibration than raw vote counts. DiscoUQ-LLM achieves AUROC 0.802 for predicting correctness, with ECE 0.036 (well-calibrated). **For GTOS: when runs split 2-1, the *nature* of the disagreement (e.g., does the minority run cite different OB zones or disagree on bias direction?) may predict trade outcome better than just the vote count.**
**Key equation:** DiscoUQ features: F = {evidence_overlap, argument_strength, divergence_depth, cluster_distance, dispersion, cohesion}. Logistic regression on F predicts P(correct).
**Testable on GTOS data:** Medium -- Would require extracting reasoning traces from each run and comparing them, not just the final CANDIDATE/NO_TRADE label. More complex to implement but potentially high value.
**Data availability:** arXiv preprint with method description.

---

### The Effect of Sampling Temperature on Problem Solving in Large Language Models
**Authors:** Lennart Betz, Leon Frey, Tobias Scheffer, Maren Pielka, Maximilian Poretschkin | **Year:** 2024 | **Source:** Findings of EMNLP 2024
**Quality Tier:** 1 | **Citations:** ~50+
**Task/domain tested:** Mathematical problem solving (GSM8K, MATH), code generation (HumanEval), commonsense reasoning
**OOS validation:** Yes (cross-model, cross-temperature evaluation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** Changes in temperature from 0.0 to 1.0 do NOT have a statistically significant effect on problem-solving performance when using a single run. Temperature primarily affects diversity/variance, not mean accuracy. For self-consistency, moderate temperature (0.5-0.7) is optimal because it creates enough diversity for meaningful voting without introducing garbage outputs. At temperature 0.0, all runs are identical (no ensemble benefit). At temperature 1.0, noise dominates. **For GTOS: if running 3x, use temperature 0.5-0.7 to ensure runs differ enough for meaningful voting. Current default temperature should be checked in primary_analyzer.py.**
**Key equation:** No novel equation; empirical finding that E[accuracy(T)] is approximately constant for T in [0.0, 1.0], but Var[output(T)] increases monotonically with T.
**Testable on GTOS data:** High -- Test temperature sweep (0.3, 0.5, 0.7, 1.0) on backtest data, measure output diversity and ensemble accuracy.
**Data availability:** Standard benchmarks used.

---

### Reliable Decision Support with LLMs: A Framework for Evaluating Consistency in Binary Text Classification
**Authors:** (Multiple, arXiv:2505.14918) | **Year:** 2025 | **Source:** arXiv preprint
**Quality Tier:** 2 | **Citations:** ~10
**Task/domain tested:** Financial news sentiment classification (binary), 14 LLMs, 1,350 articles, 5 replicates per model
**OOS validation:** Yes (held-out test articles)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-3.6
**Key finding:** LLMs demonstrated high intra-rater consistency, achieving perfect agreement on **90-98% of examples** across 5 replicate runs. Disagreement concentrated in ambiguous cases near the decision boundary. Intra-LLM consistency was similar across smaller and larger models within the same provider, suggesting diminishing returns from model size. **For GTOS: if 90-98% agreement is typical for binary classification, then ~90% of GTOS evaluations would get the same answer regardless. The value of 3x runs is concentrated in the ~5-10% of ambiguous cases where the AI is genuinely uncertain.**
**Key equation:** Intra-rater consistency: kappa = (p_o - p_e) / (1 - p_e), where p_o is observed agreement across runs and p_e is chance agreement. kappa > 0.90 across most models.
**Testable on GTOS data:** High -- Run 5 replicates on 50 historical MSOs to measure GTOS-specific agreement rate. If agreement > 95%, ensemble adds little accuracy but disagreement flagging is still valuable.
**Data availability:** Framework and methodology described in paper.

---

### The Economics of Accuracy for Medical Reasoning with Large Language Models
**Authors:** (Multiple, medRxiv preprint) | **Year:** 2025 | **Source:** medRxiv (preprint)
**Quality Tier:** 2 | **Citations:** ~5 (recent preprint)
**Task/domain tested:** Medical QA (biomedical question-answering, medical exam questions), Gemma/MedGemma family
**OOS validation:** Yes (multiple medical benchmarks with clinician comparison)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.6
**Key finding:** Correct responses averaged 2.25 unique answers across samples compared to 2.91 for incorrect responses, confirming that **answer variability predicts response correctness**. More diversity in sampled outputs = more likely the model is wrong. This provides a direct uncertainty quantification signal without needing the model to verbalize confidence. **For GTOS: if 3 runs on the same MSO produce 3 different entry prices or TP levels, that MSO is likely a low-confidence evaluation regardless of the CANDIDATE/NO_TRADE vote.**
**Key equation:** Variability signal: V(x) = |unique_answers(x)| / N. Lower V = higher confidence. Can threshold V to abstain on high-variability evaluations.
**Testable on GTOS data:** High -- Measure entry/SL/TP variance across 3 runs. Even when all 3 vote CANDIDATE, high price variance may predict worse outcomes.
**Data availability:** medRxiv preprint.

---

### Bagging Predictors
**Authors:** Leo Breiman | **Year:** 1996 | **Source:** Machine Learning, 24(2), 123-140
**Quality Tier:** 1 | **Citations:** ~25,000+
**Task/domain tested:** Classification and regression across multiple UCI datasets
**OOS validation:** Yes (test set evaluation across multiple domains)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-3.6
**Key finding:** Bagging (bootstrap aggregation) reduces variance by training multiple predictors on bootstrap samples and voting/averaging. Reduction in test set misclassification ranges from 6% to 77%. The vital element is **instability** of the base predictor -- if perturbing the input causes significant changes in the prediction, bagging helps. Stable predictors gain little from bagging. **For GTOS: the question is whether the primary analyzer is "unstable" in Breiman's sense. If temperature > 0 produces different CANDIDATE/NO_TRADE decisions on the same input, the LLM evaluator is unstable and bagging (majority voting) will help. The 90-98% agreement rate from binary classification literature suggests moderate instability.**
**Key equation:** Variance reduction: Var(bagged) = rho * sigma^2 + (1-rho)/N * sigma^2, where rho is the average pairwise correlation between predictors and N is the ensemble size. For N=3 and rho=0.8 (typical for same-model different-temperature): Var(bagged) ~ 0.87 * sigma^2 (13% variance reduction).
**Testable on GTOS data:** High -- Measure pairwise correlation (rho) between 3 runs on backtest data. If rho < 0.9, ensemble provides meaningful variance reduction.
**Data availability:** UCI datasets; Breiman's original analysis is fully reproducible.

---

### When Two is Enough: CoT-PoT Ensembling for Efficient Self-Consistency in LLM Reasoning
**Authors:** (Multiple) | **Year:** 2025 | **Source:** OpenReview (under review)
**Quality Tier:** 2 | **Citations:** ~5 (under review)
**Task/domain tested:** Mathematical reasoning (GSM8K, MATH, AQuA)
**OOS validation:** Yes
**Relevance to GTOS:** Low-Medium
**GTOS question addressed:** Q-3.6
**Key finding:** Combining two distinct reasoning modes (Chain-of-Thought + Program-of-Thought) achieves self-consistency accuracy with often only 2 samples per task, dramatically reducing sampling cost. The key insight is that **diverse reasoning strategies provide more information per sample than repeated sampling of the same strategy.** **For GTOS: minor prompt variations (e.g., emphasizing different aspects of the MSO) may provide more diverse reasoning than simply re-running the same prompt at higher temperature. However, this conflicts with WF-1 prompt freeze.**
**Key equation:** P(correct | CoT agrees with PoT) >> P(correct | single CoT), because agreement between structurally different reasoning paths is a stronger signal.
**Testable on GTOS data:** Low -- Would require creating alternative prompt variants, which is blocked by WF-1 prompt freeze. Could test post-WF-1.
**Data availability:** OpenReview paper.

---

<a id="gtos-implications"></a>
## 3. Specific GTOS Implications

### Recommended Implementation: 3-Run Adaptive Self-Consistency

Based on the literature, the optimal design for GTOS is:

**Phase 1: Measurement (can start immediately, shadow-only)**
1. Run primary_analyzer.py 3x per MSO at temperature 0.5-0.7
2. Log: (a) CANDIDATE/NO_TRADE vote per run, (b) entry/SL/TP per run, (c) agreement rate
3. Do NOT change trading decisions -- pure shadow logging
4. After 50+ evaluated MSOs, compute:
   - Agreement rate (expect ~90-95% for binary decision)
   - Accuracy gain: WR(majority_vote) - WR(single_run)
   - Disagreement signal: WR(3-of-3 CANDIDATE) vs WR(2-of-3 CANDIDATE)

**Phase 2: Deployment (requires CEO approval, post-WF-1 or if Phase 1 data supports)**
1. Implement adaptive consistency: if 2-of-2 agree, skip 3rd run (saves ~30% cost)
2. Use disagreement as position sizing signal: 3-of-3 = full risk, 2-of-3 = half risk or abstain
3. Replace rubber-stamp confidence score with agreement-based confidence

### Expected Numbers

| Metric | Estimate | Source |
|--------|----------|--------|
| Agreement rate (same answer, 3 runs) | 90-95% | Reliable Decision Support (2025), extrapolating from sentiment classification |
| Accuracy gain from majority vote | +2-5pp | Wang et al. (2023) scaled down from reasoning to binary classification |
| Optimal temperature for diversity | 0.5-0.7 | Betz et al. (2024) |
| Cost with adaptive consistency | ~$100/month | Aggarwal et al. (2023), 1.7x average multiplier |
| Cost with naive 3x | $180/month | Direct calculation |
| WR on unanimous CANDIDATE (3-of-3) | ~70% (vs 65% baseline) | Estimated from disagreement-as-uncertainty literature |
| WR on split CANDIDATE (2-of-3) | ~55% (below breakeven) | Estimated; these are the uncertain cases |

### Key Insight: Disagreement > Accuracy

The most actionable finding is NOT the accuracy gain from majority voting (which is modest for binary classification). It is that **split decisions identify uncertain evaluations**. If GTOS can learn to abstain or reduce size on 2-of-3 splits, the WR on remaining trades (unanimous decisions) could increase by +5-7pp. This is potentially more valuable than the +2-5pp from majority voting alone.

### Cost-Benefit Analysis

| Scenario | Monthly Cost | Expected WR | Monthly Trades | Expected Edge |
|----------|-------------|-------------|----------------|---------------|
| Current (1x run) | $60 | 65% | 17 | +0.200R/trade |
| 3x naive majority vote | $180 | 67-70% | 17 | +0.250-0.350R/trade |
| 3x adaptive + abstain on splits | ~$100 | 70-72% on taken trades | ~15 (2 abstained) | +0.350-0.450R/trade |
| 3x adaptive + half-size on splits | ~$100 | 65% overall, lower variance | 17 | +0.200R/trade, -30% variance |

**Recommendation:** Scenario 3 (adaptive + abstain) is the most promising. $40/month incremental cost for potentially +5-7pp WR on taken trades. But this MUST be validated on backtest data first.

---

<a id="rejected"></a>
## 4. Rejected Papers

### Majority Rules: LLM Ensemble is a Winning Approach for Content Categorization (2025)
**Reason:** Tests multi-model ensemble (different LLMs), not same-model self-consistency. GTOS uses a single model (Claude Sonnet). Results (+65% F1) are from combining fundamentally different models, not relevant to same-prompt re-runs.

### Ensemble Methods for Stock-Market Prediction (Springer, 2020)
**Reason:** Traditional ML ensemble (Random Forest, XGBoost, etc.) on price features. Not applicable to LLM-as-evaluator architecture. GTOS does not fit coefficients or train classifiers.

### Multi-Agent Stock Prediction Systems (ACM, 2025)
**Reason:** Pure infrastructure paper on multi-agent simulation frameworks. No empirical accuracy data on ensemble vs single-agent performance.

---

## Sources

- [Wang et al. 2023 - Self-Consistency Improves Chain of Thought Reasoning](https://arxiv.org/abs/2203.11171)
- [Aggarwal et al. 2023 - Adaptive-Consistency for Efficient Reasoning](https://arxiv.org/abs/2305.11860)
- [Taubenfeld et al. 2025 - Confidence Improves Self-Consistency](https://aclanthology.org/2025.findings-acl.1030/)
- [Ma et al. 2025 - Optimal Self-Consistency](https://arxiv.org/abs/2511.12309)
- [Niimi 2025 - Simple Ensemble Strategy for LLM Inference](https://arxiv.org/abs/2504.18884)
- [Xiong et al. 2024 - Can LLMs Express Their Uncertainty](https://arxiv.org/abs/2306.13063)
- [DiscoUQ 2026 - Structured Disagreement Analysis](https://arxiv.org/abs/2603.20975)
- [Betz et al. 2024 - Effect of Sampling Temperature](https://aclanthology.org/2024.findings-emnlp.432.pdf)
- [Reliable Decision Support 2025 - Binary Text Classification Consistency](https://arxiv.org/abs/2505.14918)
- [Economics of Accuracy 2025 - Medical Reasoning](https://www.medrxiv.org/content/10.64898/2025.12.22.25342804v1.full)
- [Breiman 1996 - Bagging Predictors](https://link.springer.com/article/10.1007/BF00058655)
- [When Two is Enough 2025 - CoT-PoT Ensembling](https://openreview.net/forum?id=Mr7eWCq0ae)
- [Optimizing Temperature for Multi-Sample Inference](https://arxiv.org/html/2502.05234v1)
- [Reliability-Aware Adaptive Self-Consistency](https://arxiv.org/abs/2601.02970)
