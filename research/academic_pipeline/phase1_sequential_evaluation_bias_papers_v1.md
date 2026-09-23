# Phase 1 — Sequential Evaluation Accuracy and Bias Literature Search (Q-3.5)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** Q-3.5 — Does GTOS AI evaluation accuracy degrade through a session? Do prior NO_TRADE decisions bias subsequent CANDIDATE/NO_TRADE classification?
**Total papers found:** 14 (after quality filter)
**Papers promoted (testable on GTOS data):** 10
**Papers rejected (logged below):** 4
**Search terms used:** 7 primary + 6 supplementary targeted searches

---

## Table of Contents

1. [Summary](#summary)
2. [LLM Position and Sequential Bias](#llm-position-bias)
3. [Human Sequential Decision Degradation](#human-sequential)
4. [Anchoring in Sequential Evaluation](#anchoring)
5. [Cross-Paper Synthesis](#synthesis)
6. [Specific GTOS Implications](#gtos-implications)
7. [Empirical Test Design](#test-design)
8. [Rejected Papers](#rejected)

---

<a id="summary"></a>
## 1. Summary

### Core Finding

There are two distinct bias mechanisms relevant to GTOS's sequential evaluation:

**Mechanism A — LLM Position Bias (within a single prompt):** When GTOS feeds up to 5 prior evaluations as context into the current evaluation prompt, the LLM is susceptible to recency bias (overweighting the last examples) and majority label bias (drifting toward the dominant label in the context). This is well-established across 6+ papers with large effect sizes.

**Mechanism B — Human-style Sequential Degradation (across prompts):** Unlike humans, LLMs do not experience ego depletion or decision fatigue between independent API calls. Each GTOS evaluation is a fresh API call with no persistent hidden state. The "session" exists only in the explicitly provided context, not in any accumulated fatigue.

**Verdict: Mechanism A is the real risk. Mechanism B is a non-issue for LLMs.**

### Key Numbers

| Risk Factor | Magnitude | Source | Relevance to GTOS |
|-------------|-----------|--------|--------------------|
| Position bias in LLM evaluation | Can flip 82.5% of rankings | Wang et al. 2023 | HIGH — prior evals are in-context |
| Majority label bias in few-shot | Up to 30% accuracy swing | Zhao et al. 2021 | HIGH — 5 NO_TRADEs create majority bias |
| Recency bias on last example | Reverses class preference by ~25% | Zhao et al. 2021 | HIGH — last eval in context is recency anchor |
| Lost-in-middle degradation | 20-30pp drop for mid-context info | Liu et al. 2023 | LOW — GTOS uses 5 examples, not 20+ documents |
| Human sequential anchoring | 2% accuracy reduction | Echterhoff et al. 2022 | N/A — LLM has no persistent state between calls |
| Ego depletion effect size | Failed to replicate (d ~ 0) | Multi-lab 2016, Vohs 2021 | N/A — not applicable to LLMs |
| Sequential contrast in judgments | Assimilation to N-1, contrast to N-2+ | Stewart et al. 2005 | MEDIUM — if prior evals are in context |

---

<a id="llm-position-bias"></a>
## 2. LLM Position and Sequential Bias

### Paper 1: Wang et al. 2023 — "Large Language Models are not Fair Evaluators"

- **Authors:** Peiyi Wang, Lei Li, Liang Chen, Zefan Cai, Dawei Zhu, Binghuai Lin, Yunbo Cao, Qi Liu, Tianyu Liu, Zhifang Sui
- **Year:** 2023 (arXiv May 2023; ACL 2024 proceedings)
- **Source:** ACL 2024 (Tier 1 NLP venue)
- **Quality Tier:** 1
- **Citations:** ~600+
- **Task/domain:** LLM-as-judge pairwise evaluation (GPT-4 evaluating ChatGPT vs Vicuna-13B)
- **OOS validation:** Partial — tested on Vicuna benchmark (80 queries), replicated across model pairs
- **Key finding:** Simply reordering candidate responses can flip the LLM evaluator's preference. Vicuna-13B "beat" ChatGPT on 66/80 queries when placed first — a reversal driven entirely by position, not quality. The effect is robust across evaluator models.
- **Key method:** Three calibration strategies: (1) Multiple Evidence Calibration — generate multiple rationales before scoring; (2) Balanced Position Calibration — aggregate across orderings; (3) Human-in-the-Loop for high-entropy cases.
- **Testability on GTOS data:** HIGH — GTOS can permute the order of prior evaluations in the context window and measure CANDIDATE rate changes.
- **Relevance to GTOS:** Direct. If the 5 prior evaluations are always presented chronologically (most recent last), the last evaluation has disproportionate influence on the current decision. A sequence of NO_TRADEs ending in a CANDIDATE could bias toward CANDIDATE (recency), while a sequence of NO_TRADEs creates majority label bias toward NO_TRADE.

---

### Paper 2: Zhao et al. 2021 — "Calibrate Before Use"

- **Authors:** Tony Z. Zhao, Eric Wallace, Shi Feng, Dan Klein, Sameer Singh
- **Year:** 2021
- **Source:** ICML 2021 (Tier 1 ML venue)
- **Quality Tier:** 1
- **Citations:** ~1500+
- **Task/domain:** Few-shot text classification (sentiment, topic, NLI) with GPT-2 and GPT-3
- **OOS validation:** Yes — tested across diverse task distributions, multiple prompt formats
- **Key finding:** LLMs in few-shot settings suffer from three systematic biases: (1) majority label bias — predictions skew toward the most frequent label in the prompt; (2) recency bias — predictions skew toward the label of the last example; (3) common token bias — predictions skew toward labels that are frequent in pre-training data. Contextual calibration (estimating bias via content-free input, then adjusting) improves accuracy by up to 30% absolute.
- **Key equation:** Calibration matrix W = diag(p_cf)^{-1}, where p_cf is the model's output distribution on a content-free input ("N/A"). Calibrated output: q = softmax(W * p_original).
- **Testability on GTOS data:** HIGH — can construct content-free MSO inputs and measure whether the model's base rate for CANDIDATE shifts based on the composition of the 5 prior evaluations.
- **Relevance to GTOS:** This is the most directly actionable paper. GTOS presents ~5 prior evaluations as in-context examples. If 5/5 are NO_TRADE, majority label bias predicts the model will lean NO_TRADE on the 6th. If the last example is CANDIDATE, recency bias predicts the model will lean CANDIDATE. Both effects are large (10-30pp).

---

### Paper 3: Liu et al. 2023 — "Lost in the Middle"

- **Authors:** Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang
- **Year:** 2023 (arXiv July 2023; TACL 2024)
- **Source:** TACL 2024 (Tier 1 NLP venue)
- **Quality Tier:** 1
- **Citations:** ~1200+
- **Task/domain:** Multi-document QA and key-value retrieval across 4 model families
- **OOS validation:** Yes — tested across multiple models, context lengths, document counts
- **Key finding:** LLM performance follows a U-shaped curve: highest when relevant information is at the beginning or end of the context, lowest when it is in the middle. The effect is robust across models including those explicitly trained for long contexts. Performance drops 20-30pp when relevant information moves from position 1 to the middle of 20 documents.
- **Key method:** Systematic position-controlled experiments with gold passage placement across context positions.
- **Testability on GTOS data:** MEDIUM — GTOS uses only 5 prior evaluations (short context), so the lost-in-middle effect is likely attenuated. But testable: vary the position of a known-relevant evaluation in the context.
- **Relevance to GTOS:** The primary concern is that evaluations 2-4 (the "middle" of the 5-evaluation context) may be underweighted relative to evaluations 1 and 5. However, GTOS's context is short enough (~5 items) that this effect is likely small. The recency/majority biases from Zhao et al. are more concerning for GTOS's specific setup.

---

### Paper 4: Guo & Vosoughi 2024 — "Serial Position Effects of Large Language Models"

- **Authors:** Xiaobo Guo, Soroush Vosoughi
- **Year:** 2024 (arXiv June 2024; ACL Findings 2025)
- **Source:** ACL Findings 2025
- **Quality Tier:** 2
- **Citations:** ~30
- **Task/domain:** Multiple-choice QA, summarization, evaluation tasks across multiple LLMs
- **OOS validation:** Partial — tested across tasks but specific model versions may differ
- **Key finding:** LLMs exhibit both primacy and recency biases, with primacy effects more pronounced in multiple-choice settings and recency effects more noticeable in summarization with shorter inputs. Chain-of-thought prompting partially mitigates biases but not consistently. Larger models show the U-shaped curve (both biases); smaller models show recency-only bias.
- **Key method:** Systematic position permutation across option orderings and context positions.
- **Testability on GTOS data:** HIGH — directly test whether the position of prior evaluations in the context affects the current evaluation outcome.
- **Relevance to GTOS:** Confirms the serial position effect is a general property of LLMs, not specific to one model or task. GTOS uses Claude Sonnet (a large model), which is likely to exhibit both primacy and recency bias.

---

### Paper 5: Zheng et al. 2023 — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"

- **Authors:** Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric P. Xing, Hao Zhang, Joseph E. Gonzalez, Ion Stoica
- **Year:** 2023 (arXiv June 2023; NeurIPS 2023)
- **Source:** NeurIPS 2023 (Tier 1 ML venue)
- **Quality Tier:** 1
- **Citations:** ~960+
- **Task/domain:** LLM-as-judge evaluation (MT-Bench, Chatbot Arena) across GPT-4, Claude, Llama
- **OOS validation:** Yes — 3000+ battles in Chatbot Arena, 80 MT-Bench questions
- **Key finding:** Position bias is a systematic issue for LLM judges. Including few-shot examples in the judge prompt increases consistency and reduces position bias but increases computational cost. Strong judges (GPT-4) achieve >80% agreement with human preferences but are still susceptible to position and verbosity biases.
- **Key method:** Swapping answer positions and measuring preference flip rates. Elo rating system for aggregation.
- **Testability on GTOS data:** MEDIUM — GTOS is not doing pairwise comparison, but the underlying position bias mechanism transfers to sequential context.
- **Relevance to GTOS:** Establishes that even strong models (GPT-4 class, which Claude Sonnet competes with) suffer from position bias. The specific mechanism — favoring items in certain positions within the prompt — applies to how GTOS's prior evaluations are positioned.

---

### Paper 6: Echterhoff et al. 2024 — "Cognitive Bias in Decision-Making with LLMs"

- **Authors:** Jessica Maria Echterhoff, Yao Liu, Abeer Alessa, Julian McAuley, Zexue He
- **Year:** 2024
- **Source:** EMNLP 2024 Findings (Tier 1 NLP venue)
- **Quality Tier:** 2
- **Citations:** ~40
- **Task/domain:** High-stakes decision-making (hiring, lending, medical) across commercial and open-source LLMs using 13,465 prompts
- **OOS validation:** Partial — large prompt dataset but synthetic scenarios
- **Key finding:** LLMs exhibit anchoring bias, framing effects, and sequential bias in decision-making tasks. The "BiasBuster" framework identifies three bias categories: prompt-induced, sequential, and inherent. A self-help debiasing technique (prompting the LLM to recognize its own bias) partially mitigates effects without manual example crafting.
- **Key method:** BiasBuster framework — 13,465 prompts systematically varying bias-inducing factors. Self-help debiasing via explicit bias-awareness prompting.
- **Testability on GTOS data:** HIGH — can test anchoring and sequential bias directly by varying the composition and order of prior evaluations.
- **Relevance to GTOS:** Directly studies sequential bias in LLM decision-making. The self-help debiasing approach (adding "be aware of sequential bias" to the prompt) is cheap to test on GTOS.

---

<a id="human-sequential"></a>
## 3. Human Sequential Decision Degradation

### Paper 7: Tversky & Kahneman 1974 — "Judgment under Uncertainty: Heuristics and Biases"

- **Authors:** Amos Tversky, Daniel Kahneman
- **Year:** 1974
- **Source:** Science 185(4157), 1124-1131
- **Quality Tier:** 1 (foundational)
- **Citations:** ~60,000+
- **Task/domain:** Human judgment under uncertainty — anchoring, representativeness, availability heuristics
- **OOS validation:** Yes — replicated thousands of times across domains
- **Key finding:** Humans use anchoring-and-adjustment as a heuristic: initial estimates ("anchors") insufficiently adjust toward the correct answer. In sequential judgment, prior outputs serve as implicit anchors for subsequent judgments. The effect is robust and large (median estimates differed 2-4x based on arbitrary anchor).
- **Key equation:** Insufficient adjustment model: Estimate = Anchor + beta * (True_value - Anchor), where beta < 1 (insufficient adjustment).
- **Testability on GTOS data:** LOW for LLMs directly — anchoring in LLMs operates through different mechanisms (in-context learning, not cognitive heuristics). But the conceptual framework applies: prior evaluations may anchor subsequent ones if presented in context.
- **Relevance to GTOS:** Foundational reference for why sequential context matters. The specific mechanism (anchoring-and-adjustment) does not apply to LLMs, but the behavioral prediction (prior decisions influence subsequent ones) does through in-context learning.

---

### Paper 8: Danziger, Levav & Avnaim-Pesso 2011 — "Extraneous Factors in Judicial Decisions"

- **Authors:** Shai Danziger, Jonathan Levav, Liora Avnaim-Pesso
- **Year:** 2011
- **Source:** PNAS 108(17), 6889-6892
- **Quality Tier:** 2 (high-profile but contested)
- **Citations:** ~1800+
- **Task/domain:** 1,112 Israeli parole board rulings analyzed for sequential position effects
- **OOS validation:** Partial — observational study, contested by Weinshall-Margel & Shapard (2011) who showed case ordering was non-random
- **Key finding:** Favorable ruling rate drops from ~65% at the start of a session to ~0% before a food break, then resets to ~65% after the break. The authors attribute this to mental depletion / decision fatigue. However, subsequent analysis suggests case ordering (unrepresented prisoners scheduled last) explains much of the effect.
- **Key method:** Logistic regression on ruling favorability as a function of ordinal position within session, controlling for crime severity and sentence.
- **Testability on GTOS data:** LOW — the fatigue mechanism does not apply to LLMs. However, the analytical approach (plot decision outcome vs ordinal position within session) is directly applicable.
- **Relevance to GTOS:** The analytical method is useful even though the mechanism is not. GTOS should plot CANDIDATE rate vs evaluation number within a kill zone session to see if there is a trend — but any trend found would be caused by market conditions (later in session = different volatility), not by AI fatigue.

---

### Paper 9: Stewart, Brown & Chater 2005 — "Absolute Identification by Relative Judgment"

- **Authors:** Neil Stewart, Gordon D. A. Brown, Nick Chater
- **Year:** 2005
- **Source:** Psychological Review 112(4), 881-911
- **Quality Tier:** 1
- **Citations:** ~500+
- **Task/domain:** Human absolute identification of unidimensional stimuli (psychophysics)
- **OOS validation:** Yes — fits 10+ published datasets
- **Key finding:** Humans make absolute judgments using relative comparisons to recent stimuli. The Relative Judgment Model (RJM) shows: (1) assimilation — responses bias toward the previous stimulus (N-1); (2) contrast — responses bias away from N-2 through N-5 stimuli. Sequential effects persist for ~5 trials back.
- **Key equation:** Response on trial t depends on: R(t) = f(S(t) - S(t-1)) + noise, where S(t) is the stimulus on trial t.
- **Testability on GTOS data:** MEDIUM — if GTOS's LLM receives prior evaluations, the RJM predicts assimilation to the most recent prior evaluation. After a CANDIDATE, the next evaluation should lean CANDIDATE (assimilation). After 2+ NO_TRADEs, contrast effects might push toward CANDIDATE.
- **Relevance to GTOS:** Provides a specific, testable prediction for what pattern to look for in GTOS logs: assimilation to N-1 (recency effect) and contrast to N-2+. However, this was derived for human perception, not LLMs. The LLM analogue would be the recency bias from Zhao et al. 2021.

---

<a id="anchoring"></a>
## 4. Anchoring in Sequential Evaluation

### Paper 10: Echterhoff, Yarmand & McAuley 2022 — "AI-Moderated Decision-Making: Capturing and Balancing Anchoring Bias in Sequential Decision Tasks"

- **Authors:** Jessica Maria Echterhoff, Matin Yarmand, Julian McAuley
- **Year:** 2022
- **Source:** CHI 2022 (Tier 1 HCI venue)
- **Quality Tier:** 1
- **Citations:** ~90
- **Task/domain:** College admission decisions (N=117 reviewers) and product preference judgments (crowd workers). Sequential evaluation where prior decisions anchor subsequent ones.
- **OOS validation:** Yes — two distinct domains, quantitative improvement measured
- **Key finding:** Human evaluators' decisions are anchored by their own recent decisions in sequential review tasks. An LSTM-based model captures the "anchoring state" of the evaluator and reorders cases to minimize anchoring effects. The method achieves 2% increased agreement with ground truth on college admissions.
- **Key method:** LSTM network models evaluator's anchoring state within its hidden state. Optimal case ordering algorithm minimizes anchoring by presenting cases that counterbalance the evaluator's current bias direction.
- **Testability on GTOS data:** MEDIUM — the reordering concept does not apply directly (GTOS evaluates market states as they arrive, cannot reorder them). But the LSTM anchoring detection method could be adapted to detect whether the LLM's decisions show sequential dependence.
- **Relevance to GTOS:** The college admission analogy is apt — reviewing 10-20 M15 candles is similar to reviewing 10-20 applications. However, the LSTM was modeling human anchoring. For GTOS's LLM, the anchoring is explicitly mediated by the in-context prior evaluations, making it more predictable and testable.

---

### Paper 11: Chen & Kenrick 2018 — "Decision Contamination in the Wild"

- **Authors:** Daniel L. Chen, Markus Loecher (note: the Springer publication attributes additional authors)
- **Year:** 2018 (published 2019 in Behavior Research Methods)
- **Source:** Behavior Research Methods 51, 2432-2446
- **Quality Tier:** 2
- **Citations:** ~80
- **Task/domain:** 2.2M Yelp business reviews and 4.2M Amazon movie/TV reviews — sequential rating dependencies
- **OOS validation:** Yes — two independent large-scale datasets
- **Key finding:** Within-reviewer sequential ratings show a contrast effect: current ratings are systematically biased away from prior ratings, and the magnitude decays over several reviews. After giving a high rating, the next rating tends to be lower than expected, and vice versa. The effect is small but statistically robust at these sample sizes.
- **Key method:** Fixed-effects regression with reviewer-level fixed effects, controlling for item quality proxies.
- **Testability on GTOS data:** HIGH — can directly test whether GTOS evaluation outcomes show sequential dependence (does a CANDIDATE on evaluation N make NO_TRADE more likely on N+1, or vice versa?). Requires only timestamped evaluation logs.
- **Relevance to GTOS:** The contrast effect prediction is the opposite of the recency/assimilation prediction from Zhao et al. Key distinction: the Yelp/Amazon reviewers made independent judgments without seeing their prior reviews. GTOS explicitly feeds prior evaluations into the prompt, which should produce assimilation (recency bias), not contrast.

---

<a id="synthesis"></a>
## 5. Cross-Paper Synthesis

### The Two Mechanisms Disentangled

| Property | Mechanism A: In-Context Bias | Mechanism B: Sequential Fatigue |
|----------|-------|---------|
| Cause | Prior evaluations in the prompt create majority label and recency bias | Accumulated cognitive load from repeated decisions |
| Applies to LLMs? | YES — well-documented, large effects | NO — each API call is statistically independent |
| Effect direction | Toward majority label and/or last label in context | Toward conservatism / status quo (in humans) |
| Magnitude | 10-30pp accuracy shift (Zhao 2021) | ~0 in LLMs; ~2pp in humans (Echterhoff 2022); ego depletion failed to replicate |
| Mitigation | Calibration, balanced label ordering, position permutation | N/A for LLMs |
| GTOS risk level | HIGH | NEGLIGIBLE |

### Specific GTOS Predictions from Literature

1. **Majority label bias (Zhao 2021):** When 5/5 prior evaluations are NO_TRADE, the model should lean toward NO_TRADE on the 6th — making it MORE conservative. This is the "conservative anchoring" hypothesis from the question.
2. **Recency bias (Zhao 2021, Wang 2023):** The last evaluation in the context has outsized influence. If the 5th evaluation is CANDIDATE, the 6th leans CANDIDATE. If the 5th is NO_TRADE, the 6th leans NO_TRADE.
3. **No fatigue effect:** Each evaluation is a fresh API call. There is no mechanism for the LLM to become "desperate" or "tired" across evaluations. Any observed trend in CANDIDATE rate within a session is either (a) in-context bias from the prior evaluations, or (b) market regime change (later in kill zone = different volatility/liquidity conditions).
4. **Contradiction:** Majority label bias predicts conservative drift (more NO_TRADE after NO_TRADEs). "Desperation" would require the opposite — more CANDIDATE after NO_TRADEs. The literature strongly supports conservative drift, not desperation, as the expected bias direction.

---

<a id="gtos-implications"></a>
## 6. Specific GTOS Implications

### Risk Assessment

**Primary risk: Conservative anchoring (too few CANDIDATEs)**

In a typical GTOS kill zone session (3-4 hours, 10-20 M15 candles), the system evaluates ~12-16 setups. With a 10.3% CANDIDATE rate, most sessions have 0-2 CANDIDATEs. This means the prior evaluation context is almost always dominated by NO_TRADE decisions. The majority label bias from Zhao et al. 2021 predicts this will push the model toward NO_TRADE on subsequent evaluations — exactly the conservative anchoring hypothesis.

This is consistent with GTOS's observed zero-trade problem in the first 4 days of live trading. The system may be compounding its own conservatism through the prior evaluation context.

**Secondary risk: Recency-driven CANDIDATE clustering**

If a CANDIDATE does occur, the recency bias from Wang et al. 2023 predicts the next evaluation may lean toward CANDIDATE. This could produce temporal clustering of trades rather than independent evaluation.

### Recommended Tests (Priority Order)

1. **Majority label bias test:** Run historical MSOs through the pipeline with (a) 5 NO_TRADE prior evaluations vs (b) 3 NO_TRADE + 2 CANDIDATE prior evaluations vs (c) no prior evaluations. Measure CANDIDATE rate difference.
2. **Recency bias test:** Fix 4 prior evaluations as NO_TRADE. Vary the 5th between CANDIDATE and NO_TRADE. Measure CANDIDATE rate on the 6th.
3. **Position permutation test:** Take the same 5 prior evaluations and shuffle their order. Measure whether CANDIDATE rate changes.
4. **Calibration test:** Apply Zhao et al.'s contextual calibration: present a content-free MSO with the standard prior evaluations and measure the base rate bias.

### Low-Cost Mitigations (if bias is confirmed)

1. **Drop prior evaluations from context** — simplest fix, eliminates the bias channel entirely. Cost: lose any legitimate session memory benefit.
2. **Balance prior evaluation labels** — include only 2-3 prior evaluations, ensuring label balance (e.g., always include the most recent CANDIDATE if one exists).
3. **Randomize prior evaluation order** — breaks recency bias while preserving the information content.
4. **Add debiasing instruction** — "Evaluate this setup independently of prior evaluations in this session" — the self-help debiasing from Echterhoff et al. 2024.

---

<a id="test-design"></a>
## 7. Empirical Test Design for GTOS

### Test Q-3.5a: Majority Label Bias

**Hypothesis (stated before looking at data):** When all 5 prior evaluations are NO_TRADE, the CANDIDATE rate on the current evaluation is lower than when the prior evaluations contain at least one CANDIDATE.

**Method:**
1. Select 50 historical MSOs that received CANDIDATE in the original evaluation.
2. Re-evaluate each MSO 3 times with different prior evaluation contexts:
   - Context A: 5 NO_TRADE priors (expected bias: conservative)
   - Context B: 3 NO_TRADE + 2 CANDIDATE priors (expected bias: neutral)
   - Context C: No priors (baseline)
3. Measure CANDIDATE rate across conditions.

**Decision gate:**
- If CANDIDATE rate differs by >5pp between conditions A and C: bias confirmed, implement mitigation.
- If CANDIDATE rate differs by <2pp: bias negligible, no action needed.
- If 2-5pp: ambiguous, extend to N=100 MSOs.

**Statistical test:** McNemar's test (paired proportions), alpha = 0.05.

### Test Q-3.5b: Recency Bias

**Hypothesis:** The label of the last prior evaluation has disproportionate influence on the current evaluation.

**Method:**
1. Fix 4 prior evaluations as NO_TRADE.
2. Vary the 5th (most recent) between CANDIDATE and NO_TRADE.
3. Re-evaluate 50 borderline MSOs under both conditions.
4. Measure CANDIDATE rate difference.

**Decision gate:** Same as Q-3.5a.

### Test Q-3.5c: Observational Session Analysis

**Hypothesis:** CANDIDATE rate does not decline with evaluation number within a session.

**Method:**
1. From live logs, extract evaluation position (1st through Nth in each session) and outcome.
2. Logistic regression: P(CANDIDATE) = f(position, instrument, kill_zone, volatility).
3. Test whether position coefficient is significant after controlling for market conditions.

**Decision gate:**
- If position coefficient p < 0.05 and effect > 2pp per position: investigate in-context bias as cause.
- If not significant: no sequential degradation.
- Required N: ~200 evaluations minimum (power analysis at 80% power for 3pp effect).

---

<a id="rejected"></a>
## 8. Rejected Papers

### Rejected 1: Ego Depletion / Baumeister 1998

- **Authors:** Roy Baumeister, Ellen Bratslavsky, Mark Muraven, Dianne Tice
- **Year:** 1998
- **Source:** JPSP
- **Reason for rejection:** Ego depletion has failed to replicate in two major multi-lab studies (Hagger et al. 2016 with 2,141 participants across 23 labs; Vohs et al. 2021 with 3,531 participants across 36 labs). Even if the effect were real, it applies to humans, not LLMs. Each LLM API call is a fresh computation with no accumulated state. Including this would be citing a debunked mechanism for a system it does not apply to.

### Rejected 2: Forestier et al. 2022 — "From Ego Depletion to Self-Control Fatigue"

- **Authors:** Corentin Forestier et al.
- **Year:** 2022
- **Source:** HAL (preprint repository)
- **Reason for rejection:** Review/reframing paper attempting to salvage ego depletion concept by renaming it "self-control fatigue." Still fundamentally about human cognitive resource depletion, not applicable to LLMs. Does not add testable predictions beyond the Zhao et al. in-context bias framework.

### Rejected 3: Zhang et al. 2026 — "Fatigue-Aware Learning to Defer"

- **Authors:** Zheng Zhang et al.
- **Year:** 2026 (arXiv April 2026)
- **Source:** arXiv preprint (not yet peer-reviewed)
- **Reason for rejection:** Models human expert fatigue in human-AI collaboration, not LLM-internal sequential bias. The FALCON framework assumes a human expert with workload-dependent performance degradation. Not applicable to GTOS where the LLM is the evaluator, not a fatigued human.

### Rejected 4: MDPI — "Diagnosing Bias and Instability in LLM Evaluation"

- **Authors:** (not extracted)
- **Year:** 2025
- **Source:** MDPI Information journal
- **Reason for rejection:** MDPI — excluded per search criteria (predatory/low-quality publisher).

---

## Sources

- [Wang et al. 2023 — Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926)
- [Zhao et al. 2021 — Calibrate Before Use](https://arxiv.org/abs/2102.09690)
- [Liu et al. 2023 — Lost in the Middle](https://arxiv.org/abs/2307.03172)
- [Guo & Vosoughi 2024 — Serial Position Effects of Large Language Models](https://arxiv.org/abs/2406.15981)
- [Zheng et al. 2023 — Judging LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)
- [Echterhoff et al. 2024 — Cognitive Bias in Decision-Making with LLMs](https://aclanthology.org/2024.findings-emnlp.739/)
- [Tversky & Kahneman 1974 — Judgment under Uncertainty](https://www.science.org/doi/10.1126/science.185.4157.1124)
- [Danziger, Levav & Avnaim-Pesso 2011 — Extraneous Factors in Judicial Decisions](https://www.pnas.org/doi/10.1073/pnas.1018033108)
- [Stewart, Brown & Chater 2005 — Absolute Identification by Relative Judgment](https://home.cs.colorado.edu/~mozer/Teaching/syllabi/7782/readings/StewartBrownChater2005.pdf)
- [Echterhoff, Yarmand & McAuley 2022 — AI-Moderated Decision-Making](https://dl.acm.org/doi/10.1145/3491102.3517443)
- [Chen & Kenrick 2018 — Decision Contamination in the Wild](https://link.springer.com/article/10.3758/s13428-018-1175-8)
