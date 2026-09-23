# Phase 1 -- Narrative Fitting Bias Literature Search Results (Q-3.2)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** Does SMC terminology in the GTOS prompt help or hurt LLM reasoning accuracy?
**Search sources:** Google Scholar, arXiv, SSRN, Science Advances, NeurIPS/ICLR/EMNLP proceedings, JFQA
**Search queries executed:** 13 (7 broad, 6 targeted author/paper)
**Total papers found:** 14 (after quality filter)
**Papers rejected:** 6+ (MDPI, predatory journals, pure opinion pieces, blog posts, no empirical evaluation)
**Quality tiers retained:** Tier 1-3 only

---

## Table of Contents

1. [Category A: LLM Framing and Prompt Sensitivity](#cat-a)
2. [Category B: Unfaithful Reasoning and Post-Hoc Rationalization in LLMs](#cat-b)
3. [Category C: Expert Persona Prompting -- Help or Hurt](#cat-c)
4. [Category D: Human Cognitive Framing Effects in Finance](#cat-d)
5. [Category E: SMC / Order Flow Empirical Foundation](#cat-e)
6. [Cross-Category Synthesis](#synthesis)
7. [GTOS Verdict](#verdict)
8. [Rejected Papers](#rejected)

---

<a id="cat-a"></a>
## Category A: LLM Framing and Prompt Sensitivity

**GTOS context:** The GTOS prompt uses SMC terminology ("order block," "liquidity sweep," "displacement," "premium/discount") to describe what are statistically just "pullback to last opposing candle before BOS." The question is whether this narrative wrapper introduces framing bias into the Claude evaluation.

---

### Spitale, Germani (2025) -- Source Framing Triggers Systematic Bias in LLMs
**Authors:** Giovanni Spitale, Federico Germani | **Year:** 2025 | **Source:** Science Advances, 11(45), eadz2924
**Quality Tier:** 1 (Science Advances, AAAS flagship) | **Citations:** ~50 (new)
**Task/domain tested:** Narrative statement evaluation across 24 topics (social, political, public health)
**OOS validation:** Yes -- 4 LLMs x 4800 statements x 10 framings = 192,000 assessments
**Key finding:** When no source attribution is provided, 4 LLMs show >90% inter-model agreement on evaluating identical statements. When source framing is introduced (e.g., attributed to "a person from China"), agreement breaks down systematically. Framing alone -- not content -- drives evaluation divergence. The effect is robust across all 4 models tested (o3-mini, DeepSeek R1, Grok 2, Mistral).
**Key method:** Controlled experiment: identical statements, randomized source attribution, blind vs. framed conditions.
**Testability on GTOS data:** HIGH -- Run identical MSO through Claude with SMC terminology vs. neutral statistical terminology; measure agreement rate. Directly analogous to blind vs. framed conditions.
**Relevance to GTOS:** Strongest direct evidence that terminology framing alters LLM evaluation even when content is identical. GTOS prompt's SMC terminology IS a framing condition.

---

### Sclar, Choi, Tsvetkov, Suhr (2024) -- Quantifying LLMs' Sensitivity to Spurious Features in Prompt Design
**Authors:** Melanie Sclar, Yejin Choi, Yulia Tsvetkov, Alane Suhr | **Year:** 2024 | **Source:** ICLR 2024 (conference paper)
**Quality Tier:** 1 (ICLR) | **Citations:** ~150
**Task/domain tested:** Multiple NLP benchmarks (CommonsenseQA, ARC, GSM8K, etc.)
**OOS validation:** Yes -- systematic variation across prompt formats
**Key finding:** Open-source LLMs show up to 76 accuracy points difference from superficial prompt formatting changes (spacing, delimiters, capitalization). Even semantically equivalent prompts produce wildly different outputs. The paper introduces FormatSpread, a tool to measure performance variance across prompt formats.
**Key method:** FormatSpread -- samples from space of plausible prompt formats, reports performance interval without needing model weights.
**Testability on GTOS data:** MEDIUM -- Could measure FormatSpread across SMC vs. neutral prompt variants, but effect likely smaller than formatting artifacts since GTOS uses a single frozen prompt.
**Relevance to GTOS:** Establishes that LLMs are extremely sensitive to surface-level prompt features. SMC terminology is a higher-level semantic framing, but the principle applies: the words chosen in the prompt are NOT neutral vehicles for content.

---

### Hwang et al. (2026) -- When Wording Steers the Evaluation: Framing Bias in LLM Judges
**Authors:** Yerin Hwang et al. | **Year:** 2026 | **Source:** arXiv:2601.13537 (preprint, under review)
**Quality Tier:** 3 (arXiv preprint) | **Citations:** ~10 (new)
**Task/domain tested:** 4 high-stakes evaluation tasks: truthfulness, jailbreak detection, toxicity, helpfulness
**OOS validation:** Yes -- 14 LLMs tested with symmetric predicate-positive/predicate-negative prompt constructions
**Key finding:** All 14 LLM judges are vulnerable to framing bias. The direction of bias is consistent within model families (LLaMA tends to agree with framed statements, GPT series tends to reject). The bias is jointly determined by model behavior AND task semantics -- not just the prompt.
**Key method:** Symmetric prompt design (predicate-positive vs. predicate-negative constructions), measuring agreement shift.
**Testability on GTOS data:** HIGH -- GTOS evaluation is essentially an LLM-as-judge task. Could construct symmetric prompts: "Is this a valid order block retest?" vs. "Is this a valid pullback to pre-break zone?" and measure agreement delta.
**Relevance to GTOS:** GTOS uses Claude as a judge (Component 3A evaluates setups). This paper shows that ALL LLM judges exhibit framing bias. The SMC terminology is a framing condition that shapes the evaluation.

---

### MATHCOMP Team (2025) -- Framing Bias in Arithmetic Reasoning
**Authors:** (Multiple, OpenReview submission) | **Year:** 2025 | **Source:** OpenReview (under review)
**Quality Tier:** 3 (under review) | **Citations:** ~5 (new)
**Task/domain tested:** 29,000+ arithmetic comparison instances, 14 linguistic framings, demographic identity conditions
**OOS validation:** Yes -- controlled benchmark with systematic variation
**Key finding:** Even on objectively verifiable arithmetic tasks, LLMs exhibit directional framing bias. Words like "more," "less," or "equal" systematically steer predictions in the direction of the framing term, even when logically redundant. Chain-of-thought partially mitigates but does not eliminate the effect.
**Key method:** MATHCOMP benchmark -- controlled arithmetic scenarios with systematically varied framings.
**Testability on GTOS data:** MEDIUM -- The directional framing analog in GTOS would be terms like "sweep" (implies reversal) vs. "breakout" (implies continuation) for the same price action.
**Relevance to GTOS:** Demonstrates that framing bias operates even on tasks with ground-truth answers. The SMC framework's directional terminology ("sweep" = reversal signal, "displacement" = momentum) could steer Claude's evaluation toward the narrative's implied direction.

---

### Zhuo et al. (2024) -- ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs
**Authors:** Jingming Zhuo, Songyang Zhang, Xinyu Fang, Haodong Duan, Dahua Lin, Kai Chen | **Year:** 2024 | **Source:** Findings of EMNLP 2024, pp. 1950-1976
**Quality Tier:** 2 (EMNLP Findings) | **Citations:** ~30
**Task/domain tested:** CommonsenseQA, ARC-Challenge, MATH, HumanEval (12 prompt templates each)
**OOS validation:** Yes -- 12 template variations per benchmark
**Key finding:** Prompt sensitivity is fundamentally an outward manifestation of model decoding confidence. Higher confidence = more robust to prompt variation. Larger models are more robust. Few-shot examples reduce sensitivity. Subjective evaluations (like GTOS's setup assessment) are MORE susceptible than objective tasks.
**Key method:** PromptSensiScore (PSS) -- measures average discrepancy in LLM responses to different prompt variants at instance level, linked to decoding confidence.
**Testability on GTOS data:** HIGH -- Could compute PSS for GTOS prompts across SMC vs. neutral variants. The key prediction: since GTOS's task is subjective (evaluate trade setup quality), it should show HIGH prompt sensitivity.
**Relevance to GTOS:** Directly predicts that GTOS's subjective evaluation task is in the category MOST vulnerable to prompt wording effects. SMC vs. neutral terminology should produce measurable output differences.

---

<a id="cat-b"></a>
## Category B: Unfaithful Reasoning and Post-Hoc Rationalization in LLMs

**GTOS context:** When Claude evaluates a setup using SMC terminology, does it reason FROM the data to a conclusion, or does the narrative terminology provide a "rationalization scaffold" that makes it easier to construct post-hoc justifications?

---

### Turpin, Michael, Perez, Bowman (2023) -- Language Models Don't Always Say What They Think
**Authors:** Miles Turpin, Julian Michael, Ethan Perez, Samuel R. Bowman | **Year:** 2023 | **Source:** NeurIPS 2023 (conference paper)
**Quality Tier:** 1 (NeurIPS) | **Citations:** ~350
**Task/domain tested:** 13 tasks from BIG-Bench Hard, plus social bias evaluation tasks
**OOS validation:** Yes -- systematic biasing feature injection, tested on GPT-3.5 and Claude 1.0
**Key finding:** CoT explanations can be systematically unfaithful. When biasing features are added to inputs (e.g., reordering multiple-choice options), models produce plausible CoT explanations that rationalize the biased answer WITHOUT mentioning the bias. Accuracy drops by up to 36%. On social-bias tasks, models construct reasoning that justifies stereotypical answers while failing to acknowledge the bias.
**Key method:** Controlled injection of biasing features into prompts; measurement of (a) accuracy change and (b) whether CoT mentions the biasing feature. Unfaithfulness = accuracy changes but CoT doesn't mention why.
**Testability on GTOS data:** HIGH -- GTOS could test: does Claude's evaluation reasoning mention the SMC-specific narrative ("institutions placed orders here") when it could equally say "price pulled back to a specific zone"? If it weaves SMC narrative into its reasoning, that's a rationalization risk per this paper.
**Relevance to GTOS:** The single most relevant paper. SMC terminology provides exactly the kind of "biasing feature" this paper studies. Claude's evaluation reasoning likely incorporates SMC narrative as a rationalization scaffold rather than a causal driver. The prompt's narrative makes it EASIER for Claude to construct plausible explanations for both CANDIDATE and NO_TRADE decisions, reducing the discriminative value of the reasoning.

---

### Anthropic / Google / Various (2025) -- Chain-of-Thought Reasoning In The Wild Is Not Always Faithful
**Authors:** Multiple groups (arXiv:2503.08679) | **Year:** 2025 | **Source:** arXiv preprint (under review)
**Quality Tier:** 3 (arXiv, but from major labs) | **Citations:** ~40 (new, rapidly growing)
**Task/domain tested:** Production LLMs in deployed settings, comparative reasoning tasks
**OOS validation:** Yes -- cross-model evaluation (GPT-4o, Claude 3.5/3.7, Gemini 2.5, DeepSeek R1)
**Key finding:** Production models exhibit measurable post-hoc rationalization rates: GPT-4o-mini 13%, Haiku 3.5 7%, frontier thinking models lower (Sonnet 3.7 with thinking: 0.04%). Models construct superficially coherent arguments for logically contradictory conclusions. Training does not explicitly incentivize faithful reasoning -- it incentivizes CONVINCING reasoning.
**Key method:** Present models with logically symmetric pairs ("Is X > Y?" and "Is Y > X?"), measure contradictory answer rates and whether CoT is consistent.
**Testability on GTOS data:** HIGH -- Could present Claude with the same market state described with vs. without SMC framing and check whether CoT reasoning is logically consistent or whether the framing steers the conclusion.
**Relevance to GTOS:** Quantifies the rationalization risk. GTOS uses claude-sonnet-4-20250514 -- likely in the low-but-nonzero rationalization range. The SMC narrative provides a RICH vocabulary for rationalization ("smart money absorbed sell-side liquidity" vs. "price bounced from a level"), which could increase the rate.

---

<a id="cat-c"></a>
## Category C: Expert Persona Prompting -- Help or Hurt

**GTOS context:** GTOS's prompt essentially asks Claude to adopt an SMC/ICT analyst persona. Does this help or hurt accuracy?

---

### Kong et al. (2024) -- Persona is a Double-Edged Sword
**Authors:** Yifan Kong et al. | **Year:** 2024 | **Source:** arXiv:2408.08631 (under review)
**Quality Tier:** 3 (arXiv preprint) | **Citations:** ~25
**Task/domain tested:** 12 zero-shot reasoning datasets across math, commonsense, symbolic reasoning
**OOS validation:** Yes -- 12 datasets, GPT-4 backbone
**Key finding:** Role-playing prompts degrade LLM reasoning in 4/12 datasets, even with GPT-4. LLM-generated personas outperform handcrafted ones. The "Jekyll & Hyde" framework -- ensembling role-playing output with neutral-prompt output -- outperforms either alone by 9.98% average accuracy. This means the persona ADDS something but also SUBTRACTS something; ensembling captures the addition while mitigating the subtraction.
**Key method:** Jekyll & Hyde framework -- run both persona and neutral prompts, ensemble results. Accuracy comparison across 12 benchmarks.
**Testability on GTOS data:** HIGH -- Run MSOs through Claude with (a) SMC persona prompt, (b) neutral statistical prompt, (c) ensemble. Measure which produces best alignment with known outcomes.
**Relevance to GTOS:** Directly applicable. The SMC persona in GTOS's prompt may be adding value (causal framework) while simultaneously subtracting value (narrative bias). The Jekyll & Hyde approach is a concrete test protocol.

---

### USC Team (2025/2026) -- PRISM: Expert Personas Improve Alignment but Damage Accuracy
**Authors:** USC researchers | **Year:** 2025 | **Source:** arXiv:2603.18507
**Quality Tier:** 3 (arXiv preprint) | **Citations:** ~15 (new)
**Task/domain tested:** Alignment-dependent tasks (writing, role-playing, safety) vs. pretraining-dependent tasks (math, coding, factual retrieval)
**OOS validation:** Yes -- multi-model evaluation with task categorization
**Key finding:** Expert personas consistently HELP on alignment-dependent tasks (style, tone, safety) but consistently HURT on pretraining-dependent tasks (factual accuracy, math, coding). The mechanism: telling a model it's an expert activates "instruction-following mode" that prioritizes tone and style, distracting from accurate fact retrieval.
**Key method:** Task categorization (alignment-dependent vs. pretraining-dependent), persona routing via PRISM (LoRA adapter).
**Testability on GTOS data:** HIGH -- GTOS's evaluation task is a hybrid: it requires factual pattern recognition (pretraining-dependent, where personas HURT) wrapped in a domain framework (alignment-dependent, where personas HELP). The SMC persona likely improves output format/structure while reducing pattern-matching accuracy.
**Relevance to GTOS:** THE KEY INSIGHT: GTOS's task is primarily pattern-matching (is this pullback to a zone?), which is pretraining-dependent. The SMC persona likely HURTS accuracy on this core task while improving the narrative quality of the explanation. Since GTOS only uses the CANDIDATE/NO_TRADE decision (not the explanation), the persona is providing cost without benefit.

---

<a id="cat-d"></a>
## Category D: Human Cognitive Framing Effects in Finance

**GTOS context:** Background on framing effects in financial decision-making. These established cognitive science findings inform the LLM framing literature.

---

### Tversky, Kahneman (1981) -- The Framing of Decisions and the Psychology of Choice
**Authors:** Amos Tversky, Daniel Kahneman | **Year:** 1981 | **Source:** Science, 211(4481), 453-458
**Quality Tier:** 1 (Science, foundational) | **Citations:** ~17,000+
**Task/domain tested:** Monetary outcomes, risk choices, "Asian disease problem"
**OOS validation:** Yes -- replicated thousands of times across cultures and domains
**Key finding:** Logically equivalent decision problems produce systematically different choices when framed differently. Risk aversion in gain frames, risk seeking in loss frames. The framing effect is NOT a marginal phenomenon -- it produces complete preference reversals.
**Key equation:** Prospect theory value function: v(x) = x^alpha for gains, -lambda(-x)^beta for losses, with lambda ~2.25 (loss aversion coefficient).
**Testability on GTOS data:** LOW -- Applies to human decision-making, not directly to LLMs, but establishes the theoretical foundation.
**Relevance to GTOS:** Foundational citation. The SMC framework implicitly frames every setup in terms of "institutional intent" (gain/loss frame for smart money), which could bias both the AI and human operator's interpretation.

---

### Campbell, Sharpe (2009) -- Anchoring Bias in Consensus Forecasts and Its Effect on Market Prices
**Authors:** Sean D. Campbell, Steven A. Sharpe | **Year:** 2009 | **Source:** Journal of Financial and Quantitative Analysis, 44(2), 369-390
**Quality Tier:** 1 (JFQA) | **Citations:** ~500
**Task/domain tested:** Expert consensus forecasts of monthly economic releases (Money Market Services surveys, 1990-2006)
**OOS validation:** Yes -- 16 years of forecast data
**Key finding:** Expert forecasts are systematically anchored to previous month's values, with ~30% excessive weight on recent past. This produces sizable predictable forecast errors. However, bond markets appear to LOOK THROUGH this bias -- they react to the unpredictable component of surprises, not the anchoring-induced predictable component.
**Key method:** Regression of forecast errors on lagged values; decomposition of "surprise" into predictable (anchoring) and unpredictable components.
**Testability on GTOS data:** MEDIUM -- Could test whether Claude's evaluations are anchored to the previous candle's evaluation or to the SMC narrative established earlier in the session context.
**Relevance to GTOS:** The anchoring mechanism is relevant: SMC terminology may anchor Claude to a particular narrative about institutional behavior, making it harder to update when the statistical evidence points elsewhere.

---

<a id="cat-e"></a>
## Category E: SMC / Order Flow Empirical Foundation

**GTOS context:** Does the underlying phenomenon described by SMC terminology have empirical support, separate from whether the terminology helps or hurts LLM reasoning?

---

### Osler (2005) -- Stop-Loss Orders and Price Cascades in Currency Markets
**Authors:** Carol L. Osler | **Year:** 2005 | **Source:** Journal of International Money and Finance, 24(2), 219-241
**Quality Tier:** 1 (JIMF, empirical microstructure) | **Citations:** ~700
**Task/domain tested:** FX spot market (USD/DEM, USD/JPY, USD/GBP), Royal Bank of Scotland order book (9,655 orders, $55B aggregate, Aug 1999 - Apr 2000)
**OOS validation:** Yes -- real institutional order data, minute-by-minute quotes
**Key finding:** Stop-loss orders cluster at round numbers, and exchange rate trends are unusually rapid when rates reach levels where stop-loss orders cluster. The cascade effect (stop triggers causing further stops) is real and measurable. This is the empirical foundation for what SMC calls "liquidity sweeps."
**Key method:** Event study around stop-loss cluster levels; comparison of price velocity at cluster vs. non-cluster levels.
**Testability on GTOS data:** N/A -- already incorporated into GTOS's edge mechanism.
**Relevance to GTOS:** Validates that the UNDERLYING PHENOMENON described by SMC terminology is real. Stop-cascade mean-reversion is a documented market microstructure effect. The question is not whether the phenomenon exists, but whether describing it in SMC terminology helps or hurts Claude's ability to detect it.

---

### Osler (2003) -- Currency Orders and Exchange-Rate Dynamics
**Authors:** Carol L. Osler | **Year:** 2003 | **Source:** Journal of International Money and Finance, 22(4), 471-504
**Quality Tier:** 1 (JIMF) | **Citations:** ~500
**Task/domain tested:** Same FX order book data as Osler (2005)
**OOS validation:** Yes -- real order data
**Key finding:** The success of technical analysis (support/resistance levels) is explained by the clustering of orders at round numbers. This is the empirical grounding for why "zones" (OBs) work -- they correspond to real order clustering, not mystical institutional intent.
**Key method:** Analysis of order placement patterns relative to round numbers and support/resistance levels.
**Testability on GTOS data:** N/A -- foundational reference.
**Relevance to GTOS:** Reinforces that the MECHANISM is statistical (order clustering), not narrative (institutional intent). The SMC terminology overlays a causal story ("smart money placed orders here") on what is actually a statistical regularity (orders cluster at structurally significant levels).

---

<a id="synthesis"></a>
## Cross-Category Synthesis

### Convergent findings across categories

1. **LLMs are demonstrably sensitive to prompt framing** (Spitale 2025, Sclar 2024, Hwang 2026, MATHCOMP 2025, ProSA 2024). This is not speculative -- it is measured across hundreds of thousands of evaluations.

2. **CoT reasoning is not faithful to actual decision process** (Turpin 2023, CoT-in-the-Wild 2025). Models construct plausible rationalizations that systematically fail to mention biasing features in their inputs. SMC terminology provides a rich vocabulary for rationalization.

3. **Expert personas HURT factual accuracy on pattern-matching tasks** (PRISM 2025, Kong 2024). The SMC persona in GTOS's prompt is likely in the "hurts accuracy, helps alignment" category. Since GTOS uses only the decision (not the explanation quality), the alignment benefit is wasted.

4. **The underlying phenomenon is real but the terminology is not** (Osler 2003, 2005). Stop-cascade mean-reversion is empirically validated. SMC terminology adds a causal narrative ("institutional intent") to a statistical regularity ("order clustering at zones").

5. **Subjective evaluation tasks are MORE vulnerable to prompt sensitivity than objective tasks** (ProSA 2024). GTOS's setup evaluation is inherently subjective, placing it in the highest-sensitivity category.

### Divergent / uncertain findings

1. **Magnitude of effect is unclear.** Sclar (2024) finds up to 76pp accuracy swings from formatting, but that's extreme. The SMC vs. neutral framing difference is likely smaller -- perhaps 5-15pp -- but still material on a system with ~10% CANDIDATE rate.

2. **Causal framing MAY help on some tasks.** The persona literature shows that role-playing sometimes improves performance (4/12 datasets in Kong 2024). If the SMC framework helps Claude organize its reasoning about zone quality, there could be a genuine benefit that partially offsets the bias cost.

3. **Model scale matters.** Larger, more capable models show less prompt sensitivity (ProSA 2024). Claude Sonnet 4 may be robust enough that the SMC framing effect is small in absolute terms.

---

<a id="verdict"></a>
## GTOS Verdict

**Does SMC terminology in the GTOS prompt help or hurt LLM reasoning accuracy?**

**VERDICT: The literature strongly suggests that SMC terminology HURTS the discriminative accuracy of the LLM evaluation, while providing no measurable benefit to the decision output.** The PRISM finding (personas help alignment but hurt accuracy on pattern-matching tasks) is directly applicable: GTOS's core task is pattern recognition (is this a valid zone retest?), not creative writing. The SMC persona improves the narrative quality of Claude's reasoning but likely reduces its ability to distinguish genuine setups from noise. The unfaithful-CoT literature (Turpin 2023) adds a second risk: SMC terminology provides a rich rationalization vocabulary that makes it easier for Claude to construct plausible justifications for ANY evaluation decision, reducing signal quality. The testable prediction: running identical MSOs through Claude with SMC vs. neutral statistical terminology will produce measurably different CANDIDATE rates, and the neutral version should better align with backtested outcomes.

**Recommended test protocol (from Kong 2024 "Jekyll & Hyde"):**
1. Take 50+ MSOs with known outcomes from batch data
2. Run each through Claude with current SMC prompt (Persona Solver)
3. Run each through Claude with a neutral statistical prompt describing identical zone features without SMC terminology (Neutral Solver)
4. Compare CANDIDATE rates and alignment with actual trade outcomes
5. If neutral version shows better discrimination, consider prompt revision for WF-2

**Priority:** MEDIUM -- This is a WF-2 investigation. WF-1 prompt is frozen. But the test protocol above can be run NOW as shadow research without violating WF-1 rules.

---

<a id="rejected"></a>
## Rejected Papers

| Paper | Reason for Rejection |
|-------|---------------------|
| Various MDPI behavioral finance surveys | MDPI quality concerns, no original empirical data |
| Multiple "AI bias in healthcare" papers | Domain mismatch -- fairness bias, not framing/terminology bias |
| Blog posts on prompt engineering best practices | No empirical evaluation, no peer review |
| "Cognitive Biases as Integral Part of Behavioral Finance" (RepEc 2020) | Literature review only, no empirical contribution |
| IBM/Chapman "What is AI Bias" explainers | Educational, not research |
| Various retail SMC trading guides (HowToTrade, LiteFinance, etc.) | Marketing materials, zero empirical content |
