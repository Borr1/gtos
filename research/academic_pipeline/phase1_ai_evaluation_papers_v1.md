# Phase 1 -- AI Evaluation Optimization Literature Search Results (Q-3.1 to Q-3.7 + Q-9.1)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** 8 questions on AI evaluation optimization for structured trading decisions
**Search sources:** Google Scholar, arXiv, SSRN, NeurIPS/ICML/ICLR/EMNLP proceedings, Science, JFQA, ACM
**Total papers found:** 96 (after quality filter, across all questions)
**Papers promoted (testable on GTOS data):** 72
**Papers rejected:** 24 (MDPI, predatory, ego depletion failed replication, no empirical)
**Critical gaps identified:** 4
**Parallel search agents:** 8 (one per question)
**Detailed per-question files:** See individual files in this directory for full paper entries

---

## Table of Contents

1. [Summary](#summary)
2. [Q-3.1: Optimal Signal Combination Method](#q-31)
3. [Q-3.2: Narrative Fitting Bias from SMC Terminology](#q-32)
4. [Q-3.3: Session Memory as Bayesian Updating](#q-33)
5. [Q-3.4: Confidence Calibration Methods](#q-34)
6. [Q-3.5: Sequential Evaluation Accuracy and Bias](#q-35)
7. [Q-3.6: Ensemble / Multiple-Run Methods](#q-36)
8. [Q-3.7: LLM vs Simple Statistical Model](#q-37)
9. [Q-9.1: LLM Performance on Financial Reasoning Tasks](#q-91)
10. [Cross-Question Synthesis](#synthesis)
11. [Specific GTOS Implications](#gtos-implications)
12. [Rejected Papers](#rejected)
13. [Full Reference List](#references)

---

<a id="summary"></a>
## 1. Summary

### Per-Question Breakdown

| Question | Papers | Promoted | Key Verdict |
|----------|--------|----------|-------------|
| Q-3.1: Signal Combination | 11 | 11 | XGBoost/TabPFN dominate LLMs on tabular data. At n=129, TabPFN is strongest free baseline. LLM advantage is zero-shot domain knowledge + semantic feature names. |
| Q-3.2: Narrative Bias | 14 | 14 | SMC terminology likely HURTS discriminative accuracy. Persona prompts help alignment but hurt pattern-matching accuracy (PRISM 2025). |
| Q-3.3: Session Memory | 14 | 14 | Memory works via implicit Bayesian regime inference + distributional priming, NOT literal outcome learning. 5-example window is near-optimal. |
| Q-3.4: Confidence Calibration | 12 | 12 | Platt scaling with 5-fold CV is feasible at n=129. But upstream fix needed: change confidence elicitation prompt from "rate 0-100" to structured P(True). |
| Q-3.5: Sequential Bias | 14 | 10 | LLM fatigue is a non-issue. In-context majority label bias is the real risk: 5 NO_TRADEs bias toward conservative NO_TRADE (up to 30pp, Zhao 2021). |
| Q-3.6: Ensemble Methods | 14 | 11 | 3 runs optimal. Expected +2-5pp accuracy. Real value: disagreement flags uncertain evaluations. Adaptive consistency reduces cost from $180 to ~$100/month. |
| Q-3.7: LLM vs Simple Model | 14 | 10 | Tabular literature overwhelmingly favors XGBoost/TabPFN. BUT GTOS task involves spatial reasoning on price geometry -- no paper tests this. Empirically unresolved. |
| Q-9.1: LLM Financial Benchmarks | 14 | 14 | CRITICAL GAP: No benchmark exists for "LLM on structured market data for trading decisions." GTOS is in uncharted territory. WF-1 data IS the benchmark. |

### Cross-References from Previous Searches

| Paper | Previous Search | New Relevance |
|-------|----------------|---------------|
| Timmermann (2006) Forecast Combinations | Q-1.4 signal combination | Q-3.1: equal weights dominate at n<300 |
| Hegselmann et al. (2023) TabLLM | Q-1.5 feature count | Q-3.7: LLM competitive only in few-shot (<8 samples) |
| Bailey et al. (2014) PBO | Q-1.5 feature count | Q-3.7: any XGBoost baseline must be PBO-tested |
| Gu, Kelly, Xiu (2020) | Q-1.5 feature count | Q-3.7: trees capture nonlinear financial interactions |
| Osler (2003, 2005) | Q-2.2 OB mechanism | Q-3.2: underlying phenomenon is real; terminology overlay is not |

### Critical Gaps

1. **No benchmark for LLM on structured market data.** GTOS's specific use case (JSON MSO -> binary CANDIDATE/NO_TRADE) has zero published benchmark coverage.
2. **No paper tests LLM spatial reasoning on price structure evaluation.** The tabular data literature tests pure tabular; no study compares LLM text-based spatial evaluation of OB/FVG/BOS geometry against tabular classifiers.
3. **No paper benchmarks LLMs against tree models at exactly n=100-200 on financial classification.** The few-shot literature uses different domains.
4. **No paper studies multi-run self-consistency applied to financial trading classification.** All self-consistency literature tests math/commonsense QA.

---

<a id="q-31"></a>
## 2. Q-3.1: Optimal Signal Combination Method

**Detailed file:** `phase1_signal_combination_and_features_v1.md` (Q-1.4/Q-1.5, partial overlap)

**Verdict:** The literature strongly shows that on structured tabular data, classical ML models (XGBoost, Random Forest) and purpose-built tabular foundation models (TabPFN) substantially outperform LLMs doing zero-shot classification -- the gap is dramatic (F1 0.87 vs 0.43 in Ghaffarzadeh-Esfahani et al. 2025). However, at n=129 the LLM requires zero training data and brings domain knowledge via its prompt -- Ben-David & Frank (2009) show expert systems remain competitive with ML in this regime. TabPFN v2 (Hollmann et al. 2025, Nature) is the most promising shadow comparison candidate.

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Grinsztajn et al. (2022), NeurIPS | 1 | Trees beat DL on 45 tabular datasets: 3 inductive bias advantages | High |
| Shwartz-Ziv & Armon (2022), Info Fusion | 2 | XGBoost beats all DL tabular models on their OWN benchmarks. Ensemble of XGBoost+DL beats either alone. | High |
| Hollmann et al. (2025), Nature | 1 | TabPFN v2 outperforms all at n<10K in 2.8 seconds | High -- GTOS n=129 is TabPFN's sweet spot |
| Ghaffarzadeh-Esfahani et al. (2025), Sci Reports | 2 | XGBoost F1=0.87 vs GPT-4 F1=0.43 on tabular medical data | High -- directly analogous architecture |
| Avramov (2002), JFE | 1 | BMA outperforms single-model selection in small samples | Medium |
| Sui et al. (2024), WSDM | 2 | MSO serialization format (JSON vs HTML vs text) materially affects LLM accuracy | High -- near-zero-cost experiment |
| Ben-David & Frank (2009), ESWA | 2 | Expert systems competitive with ML when domain knowledge is strong and n is moderate | Medium |
| Diebold & Shin (2019), IJF | 1 | Prune weak forecasters, equally average survivors (peLASSO) | Medium-High |
| McAlinn & West (2019), JoE | 1 | Dynamic Bayesian Predictive Synthesis for time-varying combination weights | Low -- needs 500+ trades |
| Borisov et al. (2024), IEEE TNNLS | 1 | Survey confirms GBDTs still mostly outperform DNNs on tabular data | Medium |
| Bendtsen & Pena (2016), IJAR | 2 | Gated Bayesian Networks for regime-dependent signal combination | Low -- data-hungry |

**Practical recommendation:** The highest-value test is a shadow evaluation where TabPFN v2 or Naive Bayes is run on the same MSO features the LLM receives, and agreement/disagreement is logged. Meanwhile, the serialization format experiment (Sui et al. 2024) is a near-zero-cost improvement opportunity.

---

<a id="q-32"></a>
## 3. Q-3.2: Narrative Fitting Bias from SMC Terminology

**Detailed file:** `phase1_narrative_fitting_bias_papers_v1.md`

**Verdict:** The literature strongly suggests SMC terminology HURTS discriminative accuracy while providing no measurable benefit to the decision output. Three converging lines of evidence: (1) LLMs alter evaluations based on framing alone, not content (Spitale 2025, Science Advances). (2) CoT rationalizations are unfaithful to actual decision drivers -- SMC provides rich vocabulary for post-hoc justification (Turpin 2023, NeurIPS). (3) Expert personas help alignment tasks but hurt accuracy on pattern-matching tasks (PRISM 2025), and GTOS's core task IS pattern matching.

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Spitale & Germani (2025), Science Advances | 1 | Framing alone drives LLM evaluation divergence. 4 LLMs, 192K assessments. | High |
| Turpin et al. (2023), NeurIPS | 1 | CoT is unfaithful. Biasing features change outputs but aren't mentioned in reasoning. | High |
| Sclar et al. (2024), ICLR | 1 | Up to 76pp accuracy difference from superficial prompt formatting. | Medium |
| Zhuo et al. (2024), EMNLP Findings | 2 | Subjective tasks are MOST vulnerable to prompt sensitivity. GTOS is subjective. | High |
| Kong et al. (2024), arXiv | 3 | Personas hurt 4/12 benchmarks. Jekyll & Hyde ensemble of persona + neutral outperforms either. | High |
| PRISM/USC (2025), arXiv | 3 | Expert personas HELP alignment, HURT accuracy on pattern-matching. GTOS is pattern-matching. | High |
| Tversky & Kahneman (1981), Science | 1 | Foundational: framing produces complete preference reversals. | Low |
| Campbell & Sharpe (2009), JFQA | 1 | Expert forecasts anchored ~30% excessive weight on recent past. | Medium |
| Osler (2003, 2005), JIMF | 1 | Underlying phenomenon is real (stop-cascade mean-reversion). SMC terminology is overlay. | N/A |

**Test protocol (Kong 2024 Jekyll & Hyde):** Run 50+ MSOs with known outcomes through (a) SMC prompt, (b) neutral statistical prompt, (c) ensemble. Priority: MEDIUM -- WF-2 investigation. Can shadow-test NOW without violating WF-1.

---

<a id="q-33"></a>
## 4. Q-3.3: Session Memory as Bayesian Updating

**Detailed file:** `phase1_session_memory_bayesian_updating_v1.md`

**Verdict:** Session memory most likely doubles expectancy through a hybrid of implicit Bayesian regime inference (narrowing posterior over market state from prior evaluations) and format/distribution calibration (priming with data structure and session characteristics). It is NOT literal learning from trade outcomes. The gradient descent interpretation predicts the current 5-example window is near-optimal.

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Xie et al. (2022), ICLR | 1 | ICL as implicit Bayesian inference over latent concepts. Model marginalizes over session "regime." | High |
| Min et al. (2022), EMNLP | 1 | Ground truth labels barely matter. Format + distribution + label space drive ICL. CRITICAL for GTOS. | High -- label scrambling test |
| Akyurek et al. (2023), ICLR | 1 | ICL implements implicit ridge regression. Each example = gradient step. Diminishing returns at ~5. | High |
| Von Oswald et al. (2023), ICML | 1 | Proves single attention layer = one GD step on MSE loss. Theoretical foundation. | Medium |
| Falck et al. (2024), ICML | 1 | ICL is NOT purely Bayesian. Violates martingale property. Example ORDER matters. | High -- permutation test |
| Shen et al. (2025), NeurIPS | 1 | Self-generated trajectories as ICL examples improve sequential decisions by 16-24pp. | High |
| Olsson et al. (2022), Anthropic | 1 | Induction heads: mechanical substrate for ICL via [A][B]...[A]->[B] pattern completion. | Medium |
| Bai et al. (2023), NeurIPS | 1 | Transformers adaptively select learning algorithm based on input. May do regime-dependent evaluation. | Medium |
| Dai et al. (2023), ACL Findings | 2 | ICL = meta-gradient. Momentum attention (weighting recent more heavily) improves. | Medium |
| Tsaknaki et al. (2024), QF | 2 | BOCPD for order flow regime detection -- parametric version of what GTOS memory approximates. | Medium |

**Priority experiments (ranked):**
1. **Label scrambling test** -- randomize CANDIDATE/NO_TRADE in memory, keep MSO data. If expectancy stays at +0.66R, it's distributional priming. HIGHEST PRIORITY.
2. **Memory scaling curve** -- test with 0, 1, 2, 3, 4, 5 examples. Expected: logarithmic (steep then flat).
3. **Permutation sensitivity** -- shuffle example order. Quantifies position bias.
4. **Regime coherence** -- does memory help more in stable vs. volatile sessions?

---

<a id="q-34"></a>
## 5. Q-3.4: Confidence Calibration Methods

**Detailed file:** `phase1_confidence_calibration_papers_v1.md`

**Verdict:** Platt scaling with 5-fold CV is feasible at n=129 (2 parameters, minimum viable n~100). But the bigger problem is upstream: the current confidence prompt is architecturally broken. RLHF-tuned models produce rubber-stamp behavior by design. Fix: change elicitation to multi-option consideration (Tian et al. 2023), then apply Platt scaling. First diagnostic: check if raw confidence has ANY Spearman correlation with outcomes -- if rho~0, no calibration method can help.

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Platt (1999), MIT Press | 1 | Foundational 2-parameter sigmoid calibration. Feasible at n=129. | High |
| Niculescu-Mizil & Caruana (2005), ICML | 1 | Isotonic regression overfits below n=1000. Platt scaling preferred for small sets. | High |
| Guo et al. (2017), ICML | 1 | Modern DNNs overconfident. Temperature scaling (1 param) suffices. Defines ECE. | Medium |
| Kadavath et al. (2022), Anthropic | 2 | LLMs "mostly know what they know." P(True) approach better calibrated than raw confidence. | Medium |
| Tian et al. (2023), EMNLP | 1 | Verbalized confidence + temperature scaling is winning combo for RLHF models (inc. Claude). | High |
| Xiong et al. (2024), ICLR | 1 | LLMs systematically overconfident on domain-specific tasks. Trading is domain-specific. | Medium |
| Kelly et al. (2020), ACM TKDD | 2 | Directly tested calibration at n=25/50/100. Platt scaling works at n=100 with 5-fold CV. | High |
| Kull et al. (2017), AISTATS | 1 | Beta calibration: 3 params, can represent identity. Marginal at n=129. | Medium |
| Vaicenavicius et al. (2019), AISTATS | 1 | Hypothesis testing framework for calibration significance. | High |

### Calibration Method Feasibility at n=129

| Method | Parameters | Min viable n | Works at n=129? |
|--------|-----------|-------------|----------------|
| Platt scaling | 2 | ~100 | YES (with 5-fold CV) |
| Beta calibration | 3 | ~150 | MARGINAL |
| Temperature scaling | 1 | ~50 | YES (if logits available) |
| Isotonic regression | O(n) | ~1000 | NO -- will overfit |

---

<a id="q-35"></a>
## 6. Q-3.5: Sequential Evaluation Accuracy and Bias

**Detailed file:** `phase1_sequential_evaluation_bias_papers_v1.md`

**Verdict:** Sequential "fatigue" is a non-issue for LLMs (each API call is independent). The real risk is in-context majority label bias: when 5/5 prior evaluations are NO_TRADE, the model biases toward NO_TRADE on the 6th (Zhao et al. 2021, up to 30pp swing). This may be a contributing factor to the observed zero-trade problem. The "desperation" hypothesis is contradicted by the literature -- expected direction is MORE conservatism after NO_TRADE runs, not less.

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Zhao et al. (2021), ICML | 1 | Majority label bias: up to 30pp accuracy swing. Recency bias: last example has outsized influence. | High |
| Wang et al. (2023), ACL | 1 | Position reordering can flip 82.5% of LLM judge rankings. | High |
| Liu et al. (2023), TACL | 1 | "Lost in the middle": 20-30pp drop for mid-context info. Less severe at 5 examples. | Medium |
| Zheng et al. (2023), NeurIPS | 1 | Position bias is systematic for LLM judges, even strong ones. | Medium |
| Echterhoff et al. (2024), EMNLP Findings | 2 | Self-help debiasing ("be aware of bias") partially mitigates effects. | High |
| Stewart et al. (2005), Psych Review | 1 | Assimilation to N-1, contrast to N-2+. 5-trial sequential effects. | Medium |

**Key prediction:** 5 NO_TRADE priors -> conservative bias on 6th evaluation. This is consistent with the zero-trade problem.

---

<a id="q-36"></a>
## 7. Q-3.6: Ensemble / Multiple-Run Methods

**Detailed file:** `phase1_ensemble_multiple_run_methods_v1.md`

**Verdict:** 3 runs is optimal. Self-consistency follows power-law scaling (Ma et al. 2025, NeurIPS Workshop) -- most gain in first 3-5 samples. Expected accuracy gain: +2-5pp on 65% baseline. The REAL value is disagreement logging: split votes identify uncertain evaluations where abstention may boost effective WR by +5-7pp on remaining trades. Adaptive consistency (Aggarwal et al. 2023) reduces cost from $180 to ~$100/month.

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Wang et al. (2023), ICLR | 1 | Foundational self-consistency: +6-18pp on reasoning, saturates at 5-10 samples. | High |
| Aggarwal et al. (2023), EMNLP | 1 | Adaptive-Consistency: early-stop when 2-of-2 agree. 7.9x cost reduction. | High |
| Ma et al. (2025), NeurIPS Workshop | 2 | Power-law scaling: 1->3 runs captures ~70% of asymptotic benefit. | High |
| Betz et al. (2024), EMNLP Findings | 1 | Temperature 0.5-0.7 optimal for self-consistency diversity. | High |
| Xiong et al. (2024), ICLR | 1 | Multi-run consistency is better calibration signal than verbalized confidence. | High |
| Breiman (1996), Machine Learning | 1 | Bagging: if base predictor is unstable, averaging reduces variance. | High |
| Niimi (2025), NLDB | 2 | Binary classification achieves 90-98% agreement across 5 replicates. | High |

### Cost-Benefit Analysis

| Scenario | Monthly Cost | Expected WR | Trades/Month |
|----------|-------------|-------------|--------------|
| Current (1x run) | $60 | 65% | 17 |
| 3x naive majority vote | $180 | 67-70% | 17 |
| 3x adaptive + abstain on splits | ~$100 | 70-72% on taken | ~15 |

---

<a id="q-37"></a>
## 8. Q-3.7: LLM vs Simple Statistical Model

**Detailed file:** `phase1_llm_vs_statistical_model_v1.md`

**Verdict:** The tabular data literature strongly favors XGBoost/TabPFN over LLMs for pure tabular classification at n=129. However, GTOS's task is NOT pure tabular -- the LLM processes spatial/structural descriptions of price geometry that cannot be reduced to 7 columns without information loss. No paper directly tests this hybrid task. The question is empirically unresolved. The existing Test A finding (AI adds ~0pp to entry WR) is the strongest internal evidence against the LLM, but was measured when the confidence scorer was a confirmed rubber stamp.

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Grinsztajn et al. (2022), NeurIPS | 1 | Trees beat DL on 45 datasets: 3 specific inductive bias advantages. | High |
| Hollmann et al. (2022/2025), ICLR + Nature | 1 | TabPFN outperforms all at n<10K. GTOS n=129 is its sweet spot. | High |
| Shwartz-Ziv & Armon (2022), Info Fusion | 1 | XGBoost beats all DL on own benchmarks. XGBoost+DL ensemble beats either. | High |
| McElfresh et al. (2023), NeurIPS | 1 | GBDT vs NN debate overstated. TabPFN wins on small datasets (<3K). | High |
| Ghaffarzadeh-Esfahani et al. (2025), Sci Reports | 2 | XGBoost F1=0.87 vs GPT-4 F1=0.43 on tabular medical data. Massive gap. | Medium |
| Huertas (2024), FedCSIS | 3 | LLM beats GBDT only with <8 labeled examples. At n=129, GBDTs dominate. | Medium |
| Forex ML comparison (2025), ESWA | 2 | XGBoost achieves 55-60% on forex directional prediction. | High |

**The testable experiment:** Build XGBoost/TabPFN on 7 features, compare OOS WR to LLM's 65%.
- If baseline >= 62%: LLM is overhead.
- If baseline < 58%: spatial reasoning justifies the $60/month.

---

<a id="q-91"></a>
## 9. Q-9.1: LLM Performance on Financial Reasoning Tasks

**Detailed file:** `phase1_llm_financial_reasoning_q9_1_v1.md`

**CRITICAL GAP CONFIRMED:** No benchmark exists for "LLM reasoning on structured market data for trading decisions." GTOS's specific pipeline (structured JSON MSO -> binary CANDIDATE/NO_TRADE via structured CoT prompt) has ZERO direct benchmark coverage. GTOS is operating in genuinely uncharted territory.

### What IS Benchmarked vs What GTOS Does

| Benchmarked Task | GTOS Coverage |
|------------------|---------------|
| Financial NLP (sentiment, NER) | NONE -- GTOS doesn't use LLM for NLP |
| Financial QA (document-based) | NONE |
| Financial math/calculation | NONE |
| Earnings direction (structured) | PARTIAL -- closest analog (Kim et al. 2024) |
| Stock movement (text-based) | NONE -- GTOS uses structured MSO |
| LLM trading in simulation | NONE |
| Strategy code generation | NONE |

### Key Papers

| Paper | Tier | Finding | GTOS Testability |
|-------|------|---------|-----------------|
| Kim, Muhn, Nikolaev (2024), U. Chicago | 1 | GPT-4 achieves 60.35% on binary earnings prediction from structured data. Closest analog. | Medium |
| FinBen (2024), NeurIPS | 1 | 21 LLMs: excel at NLP, struggle at reasoning/forecasting. Model size != prediction quality. | Medium |
| FinanceBench (2023), Patronus AI | 2 | GPT-4-Turbo fails on 81% of multi-step numerical financial QA. | Low |
| "Overthinking" paper (2025), ACM ICAIF | 2 | CoT reasoning DEGRADES financial classification vs direct prompting. CRITICAL for GTOS. | High |
| FinGPT (2023), NeurIPS Workshop | 3 | Stock movement prediction: 45-53% accuracy. Essentially random. | Low |
| QuantAgent (2025), arXiv | 3 | Closest structural analog to GTOS. Multi-agent LLMs on OHLCV + indicators. Limited rigor. | High |
| "The New Quant" (2025), arXiv | 2 | Survey of 84 studies. Recommends walk-forward evaluation. GTOS WF-1 aligns. | High |

---

<a id="synthesis"></a>
## 10. Cross-Question Synthesis

### The Seven Interlocking Findings

**Finding 1: The LLM is likely suboptimal as a tabular classifier (Q-3.1, Q-3.7).**
XGBoost/TabPFN beat LLMs on structured data by large margins (F1 0.87 vs 0.43). At n=129, TabPFN is the strongest free baseline. The LLM's advantage is zero-shot domain knowledge and spatial reasoning -- neither of which has been empirically isolated.

**Finding 2: SMC terminology likely hurts accuracy (Q-3.2).**
Expert personas help alignment but hurt pattern-matching accuracy (PRISM 2025). SMC provides a rich rationalization vocabulary (Turpin 2023) that may reduce the LLM's discriminative signal. The underlying phenomenon (stop-cascade mean-reversion) is real; the terminology overlay is not necessary.

**Finding 3: Session memory works, but not via outcome learning (Q-3.3).**
ICL mechanism papers (Xie 2022, Min 2022, Akyurek 2023) converge: the model uses prior evaluations for regime inference and distributional calibration, not learning from trade results. This means session memory should work even with scrambled labels -- and the current 5-example window is near-optimal.

**Finding 4: The confidence scorer is fixable (Q-3.4).**
The rubber-stamp behavior is caused by the elicitation prompt, not model incapability. Changing to multi-option consideration + P(True) (Tian et al. 2023) combined with Platt scaling on n=129 outcomes should produce a useful signal. First check: does raw confidence have ANY correlation with outcomes?

**Finding 5: Session memory creates conservative bias (Q-3.5).**
The 5 NO_TRADE priors that dominate session context create majority label bias toward NO_TRADE (Zhao 2021, up to 30pp). This is a plausible contributing factor to the zero-trade problem. This directly interacts with Finding 3.

**Finding 6: Three runs is optimal, but disagreement is the real signal (Q-3.6).**
Self-consistency gains are real but modest for binary classification (+2-5pp). The actionable insight: split votes identify uncertain evaluations. Abstaining on 2-of-3 splits could increase WR on remaining trades by +5-7pp. Cost: ~$100/month with adaptive stopping.

**Finding 7: GTOS is in uncharted territory (Q-9.1).**
No benchmark covers structured market state -> binary trading decision via LLM. GTOS's WF-1 walk-forward data is, by default, the only empirical evidence that will exist for this specific use case. The "overthinking" finding (CoT degrades financial classification) should be shadow-tested.

### The Meta-Narrative

The findings tell a coherent story: **GTOS's LLM component is likely doing several things simultaneously, some valuable and some harmful:**

**Valuable:**
- Spatial reasoning over price geometry (OB-FVG-BOS relationships) that can't be reduced to 7 tabular features
- Session memory as implicit regime inference (Finding 3)
- Zero-shot domain knowledge from pre-training (no training data needed)
- Semantic feature name interpretation ("touch_count: 1" = first zone test)

**Harmful:**
- SMC narrative as rationalization scaffold (Finding 2)
- Conservative bias from majority-NO_TRADE session memory (Finding 5)
- CoT "overthinking" may degrade binary classification accuracy (Finding 7)
- Rubber-stamp confidence is architectural failure, not model limitation (Finding 4)

**Unknown:**
- Whether spatial reasoning adds measurable WR above 7 tabular features (Finding 1)
- Whether the LLM component is justified at all vs TabPFN (Finding 1)
- Optimal prompt framing: neutral vs narrative (Finding 2)

### The Interaction Effects

Several findings interact in important ways:

1. **Session memory bias (F5) x Confidence calibration (F4):** If session memory creates conservative drift AND confidence scores are meaningless, the system has two compounding failures -- it misses trades AND can't distinguish confidence levels on the ones it takes.

2. **SMC framing (F2) x CoT overthinking (F7):** The SMC narrative provides exactly the kind of rich reasoning vocabulary that CoT uses for "overthinking." A neutral prompt with direct classification might both remove framing bias AND reduce overthinking.

3. **Ensemble methods (F6) x Confidence calibration (F4):** Multi-run agreement rate is a better confidence signal than verbalized confidence. If implementing 3-run self-consistency, replace the rubber-stamp confidence with agreement rate -- this makes the separate confidence module obsolete.

4. **LLM vs baseline (F1) x Spatial reasoning (F1/F7):** The XGBoost/TabPFN baseline test is the single most important experiment. If the baseline matches 65% WR, all other LLM optimizations (F2-F6) become moot -- replace the LLM with the free model. If the baseline falls short, the spatial reasoning component justifies investment in optimizing the LLM.

---

<a id="gtos-implications"></a>
## 11. Specific GTOS Implications

### Priority-Ranked Testable Hypotheses

All hypotheses stated BEFORE looking at GTOS outcome data, as per agent reliability rules.

#### Priority 1: The Existential Question (Q-3.7)

**Hypothesis H-3.7a:** XGBoost trained on 7 key features achieves < 58% OOS WR, confirming the LLM's spatial reasoning adds value.

**Method:** Extract 7 features (OB present, displacement quality, FVG present, touch count, premium/discount, H4 alignment, volume ratio) from all 129+ CANDIDATE evaluations. Train XGBoost with leave-one-out cross-validation. Also train TabPFN v2 (open-source, sub-second inference). Compare OOS WR to LLM's 65%.

**Prediction:** Based on Test A finding (AI adds ~0pp to entry WR) and the tabular data literature, XGBoost/TabPFN should achieve 60-65% WR. If they do, the LLM is likely overhead for the tabular component.

**Decision gate:**
- If baseline >= 62%: LLM overhead confirmed. Consider replacement or hybrid.
- If baseline < 58%: Spatial reasoning justified. Invest in optimizing LLM.
- If 58-62%: Ambiguous. Extend to 200+ trades.

**Required data:** 129 trades with outcomes + 7 feature values per trade.
**Timeline:** After 50+ live trades (to increase sample).
**Cost:** $0 (TabPFN is free, XGBoost is free).

---

#### Priority 2: Session Memory Label Scrambling (Q-3.3)

**Hypothesis H-3.3a:** Session memory with randomized CANDIDATE/NO_TRADE labels preserves >80% of the memory benefit, indicating the mechanism is distributional priming, not outcome learning.

**Method:** Re-evaluate 50 historical MSOs 3 ways: (a) original session memory, (b) session memory with scrambled labels (MSO data intact, CANDIDATE/NO_TRADE randomly reassigned), (c) no memory. Compare expectancy.

**Prediction:** (b) will show expectancy near (a), both substantially above (c).

**Decision gate:** If (b) expectancy within 20% of (a): mechanism is distributional priming. Simplify memory to include only MSO structure, not prior verdicts.

**Required data:** 50 historical MSOs with known outcomes.
**Cost:** ~$15 in API calls.

---

#### Priority 3: Majority Label Bias in Session Memory (Q-3.5)

**Hypothesis H-3.5a:** When all 5 prior evaluations are NO_TRADE, the CANDIDATE rate is lower by > 5pp compared to when prior evaluations contain at least one CANDIDATE.

**Method:** Re-evaluate 50 MSOs that received CANDIDATE with: (a) 5 NO_TRADE priors, (b) 3 NO_TRADE + 2 CANDIDATE priors, (c) no priors. Compare CANDIDATE rate.

**Prediction:** (a) will show 5-15pp lower CANDIDATE rate than (c), per Zhao et al. 2021.

**Decision gate:** If > 5pp difference: implement mitigation (balanced label context, or drop priors).

**Required data:** 50 historical CANDIDATE MSOs.
**Cost:** ~$15 in API calls.

---

#### Priority 4: Confidence Score Diagnostic (Q-3.4)

**Hypothesis H-3.4a:** The current raw confidence score (which clusters at 80) has Spearman rho < 0.05 with actual trade outcomes.

**Method:** Compute Spearman correlation between historical confidence scores and binary outcomes across 129 trades.

**Prediction:** rho ~ 0 (no correlation). The confidence score carries zero discriminative information.

**Decision gate:**
- If rho < 0.05: current confidence is confirmed useless. Post-hoc calibration cannot help -- need to change elicitation prompt (WF-2).
- If rho > 0.10: surprising -- apply Platt scaling immediately and shadow-log calibrated predictions.

**Required data:** 129 trades with confidence scores and outcomes.
**Cost:** $0 (analysis only).

---

#### Priority 5: CoT Overthinking Test (Q-9.1)

**Hypothesis H-9.1a:** A simplified binary prompt ("Given this market state, is this a valid OB-retest trade? YES/NO") achieves >= 60% WR, comparable to the current structured CoT prompt.

**Method:** Re-evaluate 50 historical MSOs with (a) current full CoT prompt, (b) simplified binary prompt with no reasoning chain. Compare WR.

**Prediction:** Based on the "overthinking" finding (ACM ICAIF 2025), the simplified prompt may match or beat the CoT prompt on binary accuracy.

**Decision gate:** If simplified >= CoT - 2pp: the structured reasoning is overhead. Consider simplification for WF-2.

**Required data:** 50 historical MSOs with known outcomes.
**Cost:** ~$10 in API calls.
**Note:** Does NOT require changing the live prompt (shadow test only).

---

#### Priority 6: SMC vs Neutral Framing Test (Q-3.2)

**Hypothesis H-3.2a:** A neutral statistical prompt ("Is this pullback-to-pre-break-zone a continuation setup?") produces CANDIDATE rates that better align with actual outcomes than the current SMC prompt.

**Method:** Kong 2024 Jekyll & Hyde protocol: run 50+ MSOs through (a) SMC prompt, (b) neutral prompt, (c) ensemble. Compare WR alignment.

**Prediction:** Neutral prompt should show better discrimination (fewer false-positive CANDIDATEs) based on framing bias literature.

**Decision gate:** If neutral WR > SMC WR by > 3pp: recommend prompt revision for WF-2.

**Required data:** 50 historical MSOs with known outcomes.
**Cost:** ~$10 in API calls.
**Note:** WF-1 prompt is frozen. This is shadow research only.

---

#### Priority 7: 3-Run Self-Consistency Shadow (Q-3.6)

**Hypothesis H-3.6a:** 3-of-3 unanimous CANDIDATE decisions have WR > 70%, while 2-of-3 split decisions have WR < 60%.

**Method:** Run primary_analyzer.py 3x per MSO at temperature 0.5-0.7 on 50+ historical MSOs. Log agreement rate, entry/SL/TP variance.

**Prediction:** ~90% agreement rate. Unanimous decisions higher WR than splits.

**Decision gate:**
- If agreement > 95%: ensemble adds little; disagreement logging still valuable for the ~5% uncertain cases.
- If agreement 80-90%: ensemble adds meaningful signal. Consider adaptive consistency implementation.
- If WR(3-of-3) - WR(2-of-3) > 10pp: abstaining on splits is the highest-value intervention.

**Required data:** 50+ historical MSOs.
**Cost:** ~$30 in API calls (3x current).

---

### Implementation Sequencing

| Phase | Tests | WF-1 Safe? | Estimated Cost |
|-------|-------|-----------|----------------|
| Immediate (this week) | H-3.4a (confidence diagnostic), H-3.7a (XGBoost/TabPFN baseline) | YES (analysis only) | $0 |
| Near-term (this month) | H-3.3a (label scrambling), H-3.5a (majority label bias) | YES (shadow API calls) | ~$30 |
| Medium-term (before WF-2) | H-9.1a (CoT overthinking), H-3.2a (SMC vs neutral), H-3.6a (3-run consistency) | YES (shadow only) | ~$50 |
| WF-2 implementation | Deploy winning changes to live prompt | Requires CEO approval | TBD |

**Total shadow testing budget: ~$80 across all experiments.**

---

<a id="rejected"></a>
## 12. Rejected Papers (Across All Questions)

| Paper / Source | Question | Reason for Rejection |
|----------------|----------|---------------------|
| Various MDPI behavioral finance surveys | Q-3.2 | MDPI quality concerns |
| AI bias in healthcare papers | Q-3.2 | Domain mismatch -- fairness bias, not framing |
| Blog posts on prompt engineering | Q-3.2, Q-3.6 | No empirical evaluation |
| Ego depletion (Baumeister 1998) | Q-3.5 | Failed to replicate in two major multi-lab studies |
| "Self-Control Fatigue" reframing (2022) | Q-3.5 | Rebranding debunked construct |
| Fatigue-Aware Learning to Defer (2026) | Q-3.5 | Models human fatigue, not LLM sequential bias |
| MDPI "Diagnosing Bias and Instability" | Q-3.5 | MDPI excluded per protocol |
| Ensemble Methods for Stock-Market (2020) | Q-3.6 | Traditional ML ensemble, not LLM self-consistency |
| Multi-Agent Stock Prediction (ACM 2025) | Q-3.6 | Pure infrastructure, no accuracy data |
| Majority Rules LLM Ensemble (2025) | Q-3.6 | Multi-model ensemble, not same-model consistency |
| Various MDPI candlestick CNN papers | Q-3.7 | MDPI, no OOS, claims 99.3% accuracy |
| "AI Reshaping Financial Modeling" (Nature npj) | Q-3.7 | Review/opinion, no empirical comparison |
| Various Medium blog posts | Q-3.7, Q-9.1 | Not peer-reviewed |
| MDPI "Sustainability"/"Applied Sciences" LLM papers | Q-9.1 | Predatory venue |
| Blog posts claiming "GPT-4 can trade" | Q-9.1 | No reproducible methodology |
| Retail SMC trading guides | Q-3.2 | Marketing materials, zero empirical content |
| Papers with n<50 and no statistical testing | Q-9.1 | Insufficient rigor |

---

<a id="references"></a>
## 13. Full Reference List (Tier 1-2 Papers Only)

### Signal Combination (Q-3.1)
- Grinsztajn, Oyallon, Varoquaux (2022). "Why Do Tree-Based Models Still Outperform Deep Learning on Tabular Data?" NeurIPS 2022.
- Shwartz-Ziv, Armon (2022). "Tabular Data: Deep Learning is Not All You Need." Information Fusion 81.
- Hollmann, Mueller, Eggensperger, Hutter (2025). "Accurate Predictions on Small Data with a Tabular Foundation Model." Nature.
- Avramov (2002). "Stock Return Predictability and Model Uncertainty." JFE 64(3).
- McAlinn, West (2019). "Dynamic Bayesian Predictive Synthesis in Time Series Forecasting." J. Econometrics 210(1).
- Diebold, Shin (2019). "Machine Learning for Regularized Survey Forecast Combination." IJF 35(4).
- Ghaffarzadeh-Esfahani et al. (2025). "Large Language Models versus Classical ML Performance." Scientific Reports 15.
- Sui, Zhou, Zhou, Han, Zhang (2024). "Table Meets LLM." WSDM 2024.

### Narrative Bias (Q-3.2)
- Spitale, Germani (2025). "Source Framing Triggers Systematic Bias in LLMs." Science Advances 11(45).
- Turpin, Michael, Perez, Bowman (2023). "Language Models Don't Always Say What They Think." NeurIPS 2023.
- Sclar, Choi, Tsvetkov, Suhr (2024). "Quantifying LLMs' Sensitivity to Spurious Features in Prompt Design." ICLR 2024.
- Tversky, Kahneman (1981). "The Framing of Decisions and the Psychology of Choice." Science 211.
- Campbell, Sharpe (2009). "Anchoring Bias in Consensus Forecasts." JFQA 44(2).
- Osler (2003, 2005). "Currency Orders and Exchange-Rate Dynamics" / "Stop-Loss Orders and Price Cascades." JIMF.

### Session Memory (Q-3.3)
- Xie, Raghunathan, Liang, Ma (2022). "An Explanation of ICL as Implicit Bayesian Inference." ICLR 2022.
- Min, Lyu, Holtzman, Artetxe, Lewis, Hajishirzi, Zettlemoyer (2022). "Rethinking the Role of Demonstrations." EMNLP 2022.
- Akyurek, Schuurmans, Andreas, Ma, Zhou (2023). "What Learning Algorithm is ICL?" ICLR 2023.
- Von Oswald, Niklasson, Randazzo et al. (2023). "Transformers Learn In-Context by Gradient Descent." ICML 2023.
- Falck, Wang, Holmes (2024). "Is ICL Bayesian? A Martingale Perspective." ICML 2024.
- Garg, Tsipras, Liang, Valiant (2022). "What Can Transformers Learn In-Context?" NeurIPS 2022.
- Bai, Chen, Wang, Xiong, Mei (2023). "Transformers as Statisticians." NeurIPS 2023.
- Shen, Shridhar et al. (2025). "Self-Generated ICE for Sequential Decision-Making." NeurIPS 2025.
- Olsson, Elhage, Nanda et al. (2022). "In-context Learning and Induction Heads." Anthropic.

### Confidence Calibration (Q-3.4)
- Platt (1999). "Probabilistic Outputs for SVMs." MIT Press.
- Niculescu-Mizil, Caruana (2005). "Predicting Good Probabilities." ICML 2005.
- Guo, Pleiss, Sun, Weinberger (2017). "On Calibration of Modern Neural Networks." ICML 2017.
- Tian, Mitchell, Zhou et al. (2023). "Just Ask for Calibration." EMNLP 2023.
- Xiong, Hu, Lu et al. (2024). "Can LLMs Express Their Uncertainty?" ICLR 2024.
- Kadavath et al. (2022). "Language Models (Mostly) Know What They Know." Anthropic/arXiv.
- Kull, Silva Filho, Flach (2017). "Beta Calibration." AISTATS 2017.
- Vaicenavicius et al. (2019). "Evaluating Model Calibration in Classification." AISTATS 2019.
- Kelly, Longjohn, Wagstaff (2020). "Better Classifier Calibration for Small Datasets." ACM TKDD.

### Sequential Bias (Q-3.5)
- Zhao, Wallace, Feng, Klein, Singh (2021). "Calibrate Before Use." ICML 2021.
- Wang et al. (2023). "Large Language Models are not Fair Evaluators." ACL 2024.
- Liu, Lin, Hewitt et al. (2023). "Lost in the Middle." TACL 2024.
- Zheng et al. (2023). "Judging LLM-as-a-Judge." NeurIPS 2023.
- Tversky, Kahneman (1974). "Judgment under Uncertainty: Heuristics and Biases." Science 185.
- Stewart, Brown, Chater (2005). "Absolute Identification by Relative Judgment." Psych Review 112(4).
- Echterhoff, Yarmand, McAuley (2022). "AI-Moderated Decision-Making." CHI 2022.

### Ensemble Methods (Q-3.6)
- Wang, Wei, Schuurmans et al. (2023). "Self-Consistency Improves Chain of Thought Reasoning." ICLR 2023.
- Aggarwal, Madaan, Yang, Mausam (2023). "Adaptive-Consistency for Efficient Reasoning." EMNLP 2023.
- Betz, Frey, Scheffer, Pielka, Poretschkin (2024). "Effect of Sampling Temperature." EMNLP Findings 2024.
- Xiong et al. (2024). "Can LLMs Express Their Uncertainty?" ICLR 2024.
- Breiman (1996). "Bagging Predictors." Machine Learning 24(2).
- Taubenfeld et al. (2025). "Confidence Improves Self-Consistency." ACL Findings 2025.

### LLM vs Statistical Model (Q-3.7)
- Grinsztajn et al. (2022). NeurIPS 2022. (see Q-3.1)
- Hollmann et al. (2022/2025). ICLR 2023 + Nature 2025. (see Q-3.1)
- Shwartz-Ziv, Armon (2022). Information Fusion 81. (see Q-3.1)
- McElfresh et al. (2023). NeurIPS 2023.
- Gorishniy, Rubachev, Khrulkov, Babenko (2021). "Revisiting Deep Learning for Tabular Data." NeurIPS 2021.
- Borisov et al. (2022). "Deep Neural Networks and Tabular Data: A Survey." IEEE TNNLS.
- Levin et al. (2023). "Transfer Learning with Deep Tabular Models." ICLR 2023.

### LLM Financial Benchmarks (Q-9.1)
- Kim, Muhn, Nikolaev (2024). "Financial Statement Analysis with Large Language Models." U. Chicago.
- Xie, Han, Chen et al. (2024). "FinBen." NeurIPS 2024 Datasets & Benchmarks.
- Shah, Chava, Campria (2022). "FLUE: Financial Language Understanding Evaluation." EMNLP 2022.
- Wu, Irsoy, Lu et al. (2023). "BloombergGPT." Bloomberg/arXiv.
- Islam, Shek, Mathur et al. (2023). "FinanceBench." Patronus AI/arXiv.
- "Reasoning or Overthinking" (2025). ACM ICAIF 2025.

---

*This file consolidates findings from 8 parallel search agents. Detailed per-question files with full paper entries are available in this directory. Last updated: April 11, 2026.*
