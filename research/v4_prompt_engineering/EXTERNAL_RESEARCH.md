# EXTERNAL_RESEARCH.md — GTOS V4 Prompt Engineering Foundation

**Research Agent A (MAXIMUM EFFORT)**
**Date:** 2026-04-24
**Branch:** `research/v4-prompt-external-research`
**Scope:** Anthropic official docs + academic literature + production LLM trading systems + practitioner patterns

---

## 1. Executive Summary

The V3 problem (AI inconsistency on MSO-label-vs-CHoCH-override across similar-but-not-identical candles) is not a GTOS-specific bug — it is a **named, well-studied failure mode** in the LLM literature: **semantic consistency failure under instruction-hierarchy conflict**. Frontier models, including Claude Sonnet 4, exhibit it at measurable and reproducible rates.

### Top 10 evidence-backed design principles for V4

1. **Instruction hierarchies in system prompts don't reliably hold** (Lanham et al. *Control Illusion* 2025 — "Primary Obedience Rate collapses to 9.6-45.8% when constraints conflict; GPT-4o averages 40.8%"). V4 must state priority explicitly *inside the user-visible reasoning scaffold*, not implicitly via section ordering.

2. **Temperature=0 ≠ determinism** (Atil et al. *arXiv:2408.04667*, 2024). Accuracy variations up to 15% across "identical" runs; batch-context effects are the dominant source. Do not blame the prompt for all variance — **measure noise floor first** before attributing any inconsistency to V3.

3. **For intuition-driven financial classification, CoT often degrades accuracy** (Hung et al. *Reasoning or Overthinking*, arXiv:2506.04574, 2025). GPT-4o No-CoT 0.727 macro-F1 > CoT-Long 0.668. The **LIRA** pattern (predict label first, justify after) outperformed forward-chained CoT. **This contradicts GTOS's V3 direction of adding more reasoning scaffolding.** GTOS's decision is somewhere between intuition (pattern recognition) and computation (multi-factor gate check), so the empirical test matters.

4. **Context length degrades performance even with perfect retrieval** (Liu et al. *Context Length Alone Hurts*, arXiv:2510.05381, 2025). Up to 85% accuracy loss at 30K tokens; degradation starts at ~7.5K tokens *even with masked distractors*. V3 at ~15K tokens is in the danger zone. Prune or chunk before adding.

5. **"Lost in the middle" is still real on Claude 4.6-class models** (Liu et al. 2023, replicated broadly). Put the most critical rules at the *top* and the output schema at the *bottom*. Mid-prompt constraint blocks are the weakest position.

6. **Structured Outputs (JSON Schema + enum) materially reduces malformed/ambiguous decisions** (Anthropic Structured Outputs docs, 2026; multiple benchmarks). Without it, even careful prompts produce ~10-15% parse errors. With enum-constrained `no_trade_reason` and `candidate_direction`, V4 can close R1's biggest unfinished surface (reason-code allowlist enforcement, `Optional[str]` → `Literal[...]`).

7. **Few-shot examples with diverse contrasts beat instructions** (Weng 2023, TradingAgents 2024, AD-FCoT arXiv:2509.12611). For decision consistency, 3-5 *explicitly contrasting* worked examples (positive case + rejected-similar-case + edge case) is the highest-leverage addition. **GTOS V3 currently has no worked examples** — just rule text.

8. **The "think" tool / scratchpad pattern gives 1.6-54% improvement on policy-heavy decisions** (Anthropic think-tool blog, τ-bench Airline 0.370→0.570). Claude Sonnet 4.6 supports `<thinking>` tags natively with adaptive thinking; use explicit "list applicable rules before deciding" scaffolding.

9. **Prompt-Reverse Inconsistency (PRIN) — ~40% even on GPT-4** (Ma et al. arXiv:2504.01282, 2025). Models give different answers to "which are correct?" vs "which are incorrect?" on the same problem. V4 should avoid rule duplication that phrases the same gate from opposite directions — GTOS V3 already has some of this.

10. **ATLAS finding: Claude Sonnet 4 drifts toward "overly rigid, procedural instructions" under self-reflection loops** (Zhou et al. arXiv:2510.15949, 2025). This is the closest-named cousin of GTOS's V3 regression: V3 was expanded to close gaming surfaces, which made the procedural text more rigid, which (per ATLAS) is exactly the Claude Sonnet 4 failure mode. V4 must bias toward principle-based rules, not procedure-listing.

### Open research gaps (need GTOS experiments)

- **Noise floor measurement.** No external source gives XAUUSD MSO-specific self-agreement rate at effort=max. GTOS must run 30 replays of 10 candles to establish baseline variance before attributing V3 brittleness to prompt text.
- **CoT helpful/harmful boundary for SMC decisions.** Literature is split. GTOS's task is structured enough to benefit from CoT but also intuition-laden enough to hurt — needs A/B.
- **Example ordering / majority-label bias at GTOS scale.** Few-shot literature (Zhao et al. biases) establishes the bias but GTOS has never added worked examples. V4 design must pre-audit candidate examples for majority-label bias.
- **Confidence calibration for trading gates.** `Mind the Confidence Gap` shows LLMs are severely miscalibrated on factoid QA, but no public study replicates on SMC order-block trading. GTOS's `confidence_score=72` phenomenon needs in-house calibration curve.

---

## 2. Anthropic Best-Practices Synthesis

Sources: [Prompting best practices master doc](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Structured Outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [Extended Thinking docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking), [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), [Think tool](https://www.anthropic.com/engineering/claude-think-tool), [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

### 2.1 Structured decision prompts
- **Golden rule** (direct quote): *"Show your prompt to a colleague with minimal context on the task and ask them to follow it. If they'd be confused, Claude will be too."*
- **Be specific, be sequential**: *"Provide instructions as sequential steps using numbered lists or bullet points when the order or completeness of steps matters."* V3's multi-gate C1/C2/C3 pattern is consistent with this. **But** — Anthropic pairs this with an anti-overengineering warning (below).
- **Give Claude a role**: even one sentence helps. GTOS's `_INSTRUMENT_IDENTITY` mapping ("institutional gold trader with 15+ years") aligns with this.
- **Context > negation**: *"Tell Claude what to do instead of what not to do."* V3 has heavy "do not do X / reject if Y" phrasing — this should be recast positively where feasible.

### 2.2 Long-context prompts (>5k tokens)
Direct quotes:
- *"Put longform data at the top. Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples. This can significantly improve performance across all models. Queries at the end can improve response quality by up to 30% in tests."*
- *"Structure document content and metadata with XML tags"* — wrap MSO in `<market_state>`, history in `<session_memory>`, rules in `<gates>`.
- *"Ground responses in quotes. For long document tasks, ask Claude to quote relevant parts of the documents first before carrying out its task."* — for V4, consider making the model echo the relevant MSO fields into a `<evidence>` block before the decision.

### 2.3 Effort=max / adaptive thinking
- *"Max effort can deliver performance gains in some use cases, but may show diminishing returns from increased token usage. **This setting can also sometimes be prone to overthinking.**"* — this is the explicit Anthropic warning that more reasoning can hurt, and directly relates to GTOS V3's observed variability.
- *"Claude Opus 4.7 respects effort levels strictly"* — not relevant for GTOS (Sonnet 4.6) but worth noting for migration paths.
- *"When you're deciding how to approach a problem, choose an approach and commit to it. Avoid revisiting decisions unless you encounter new information that directly contradicts your reasoning."* — this is the **direct Anthropic-recommended counter to reasoning drift**. V4 should include this language.
- *"[With extended thinking enabled] Prefer general instructions over prescriptive steps."* — this is load-bearing for the V3 regression. V3 added prescriptive steps (more gaming-pattern prohibitions, more explicit thresholds). Anthropic says the opposite is usually better.

### 2.4 Multi-criteria gates
Anthropic's [building effective agents](https://www.anthropic.com/engineering/building-effective-agents) post recommends the **parallelization pattern**: *"LLMs generally perform better when each consideration is handled by a separate LLM call, allowing focused attention on each specific aspect."*

**Implication for GTOS**: the current single-call C1/C2/C3 gate is *against* this guidance at the architectural level. But parallel multi-call would cost 3× and break the single-decision contract with permissions.py. A middle path: keep single-call, but use **explicit rubric scaffolding** (see LLM-RUBRIC below), which ACL 2024 paper shows "reduces variance in scoring by separating evaluation into distinct categories."

### 2.5 JSON structured output
- JSON Schema + enum-constrained fields **eliminate schema-violation errors** (from ~10-15% in raw-JSON prompting to 0% with Structured Outputs).
- Key recommendation: *"Use enums over free-text. Mark all decision fields as required. Set `additionalProperties: false`."*
- **Direct fit for GTOS V4**: move `no_trade_reason: Optional[str]` → `no_trade_reason: Literal["R1",...,"R8"]` enforced at the schema layer. This closes the V3 "off-allow-list reasons silently logged not rejected" gap mechanically rather than via prompt text.
- **Caveat**: 20 strict tools, 24 optional parameters, 16 union types per request. GTOS is well under all limits.

### 2.6 Preventing "AI reasoning drift"
Anthropic explicit recommendations aggregated across docs:

1. **Commit-to-approach phrasing** (quoted 2.3 above).
2. **Self-check prefix**: *"Before you finish, verify your answer against [test criteria]."*
3. **Multishot with `<thinking>` tags** to show the desired reasoning pattern; Claude generalizes the style.
4. **"Think" tool** for policy-heavy decisions — "list applicable rules" before answering.
5. **Ground all analysis in quoted evidence** — this is GTOS's existing `ANTI_HALLUCINATION` block, but can be tightened.
6. **Anthropic multi-agent research system post** reports 90.2% improvement over single-agent — driven mostly by token spend (80% of variance explained by tokens). **Not directly applicable** to GTOS since ingesting 15× tokens per decision would break the API budget; but the *source-quality heuristics* finding ("models preferred SEO-optimized content farms over authoritative sources") is a useful reminder that Claude has biases that need explicit prompt correction.

### 2.7 Evals + variance measurement (Anthropic recommendation)
From [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents):
- *"Each task has its own success rate—maybe 90% on one task, 50% on another—and a task that passed on one eval run might fail on the next."*
- Distinguish **pass@k** (probability of at least one success across k attempts) vs **pass^k** (probability *all* k trials succeed). For high-stakes agents: *"pass^k matters because users expect reliable behavior every time."*
- **Direct implication for V4**: GTOS canary's 60 fixtures are pass@1 style. V4 validation should add **pass^5** on the 4 divergent candles (run each 5×, count how many are 5/5 consistent). This measures the *V4 consistency improvement* directly, not just accuracy.

---

## 3. Academic / Research Synthesis

### 3.1 Self-consistency + CoT foundations
- **Wang et al. 2022 — Self-Consistency** ([arXiv:2203.11171](https://arxiv.org/abs/2203.11171)): sample multiple reasoning paths, majority-vote. +17.9% GSM8K, +11.0% SVAMP. **Tradeoff**: N× inference cost. **Relevance to GTOS**: not directly runnable (cost), but conceptually, **running V4 5× per decision and requiring 4/5 agreement is an aggressive consistency mechanism** if budget permits.

- **Wei et al. 2022 — Chain-of-Thought** ([arXiv:2201.11903](https://arxiv.org/abs/2201.11903)): CoT improves reasoning on arithmetic/commonsense/symbolic tasks with sufficiently large models.

- **Saparov et al. 2024 — CoT brittleness** (arXiv:2508.01191-adjacent): CoT gains **do not generalize out-of-distribution**. Up to 33.3% accuracy drop with noisy rationales. **CD-CoT mitigation** (rephrase, select, explore, vote) achieves +17.8% recovery. **Relevance**: GTOS's input distribution (specific SMC concepts like OB, CHoCH, displacement) is narrow relative to training data; the signal CoT provides may be weaker than on generic benchmarks.

### 3.2 Decision consistency under similar inputs (the direct V3 problem)
- **Ma et al. 2025 — Prompt-Reverse Inconsistency (PRIN)** ([arXiv:2504.01282](https://arxiv.org/html/2504.01282v1)): GPT-4 ~40%, Qwen 2.5 ~60%, Llama-3 ~80% inconsistency on "which is correct" vs "which is incorrect" for identical inputs. *"PRIN does not positively correlate with Randomness Inconsistency or Paraphrase Inconsistency"* — **this is a logical flaw independent of sampling.**
 - **Mitigation**: CoT for each option + explicit negation explanation reduced PRIN substantially.
 - **GTOS application**: V3 has opposite-direction phrasings of the same gate ("accept if X" + "reject if !X"); consider removing the negated variant, or ensure they appear together with explicit consistency-contract language.

- **Khatun et al. 2024 — Chain of Guidance** ([arXiv:2502.15924](https://arxiv.org/html/2502.15924v1)): three-stage paraphrase + rank + select. Entailment score 35.5 → 84.4 (text-davinci-003). Fine-tuned models "more than twice as consistent." **Not cheap to deploy** (multi-pass) but the *pattern* of "constrain the output space" is relevant — Structured Outputs is a single-pass variant.

- **Atil et al. 2024 — Non-Determinism of "Deterministic" LLM Settings** ([arXiv:2408.04667](https://arxiv.org/html/2408.04667v5)): **15% accuracy swing across 10 runs at temp=0**. Professional Accounting (GPT-4o) 57.8%-89.0%. Total Agreement Rate on raw responses often <50%, sometimes 7%. **Causes**: batch continuous batching + prefix caching + floating-point at scale + hardware heterogeneity. **Mitigations**: restrict max generation tokens, report ranges, regression testing over unit testing.
 - **This is the single most important data point for GTOS V4 planning.** If the baseline noise floor on Claude Sonnet 4.6 MSO decisions is 10-15% (which aligns with the "2 Feb 2026 divergent trades / ~15 candidate calls" anecdote), **no prompt change can push it below that floor**. V4 should target ≤5% *residual* variance above whatever baseline the replay establishes.

### 3.3 Long-context degradation
- **Liu et al. 2023 — Lost in the Middle**: U-shape performance across document positions. Performance highest at start/end, lowest in middle. Applies to frontier models including Claude.
- **Hong et al. 2025 — Context Length Alone Hurts** ([arXiv:2510.05381](https://arxiv.org/html/2510.05381v1)): 13.9%-85% degradation with long inputs *even when retrieval is perfect*. Degradation starts at ~7.5K tokens. Claude-3.5 affected. **V3 is 15K tokens** — in the danger zone. Recommended mitigation: *explicit evidence extraction step* before the decision (4-31% accuracy recovery observed).

### 3.4 Financial sentiment / decision prompts — empirical
- **Hung et al. 2025 — Reasoning or Overthinking** ([arXiv:2506.04574](https://arxiv.org/html/2506.04574v1)): 4,845 Financial PhraseBank sentences. **GPT-4o No-CoT (0.727 macro-F1) > CoT-Short (0.687) > CoT-Long (0.668).** Longer token outputs → worse performance. o3-mini generated 4-5× more tokens and achieved the **lowest** scores.
 - **LIRA** (predict label first, justify after) vs forward CoT: LIRA 0.689 vs CoT-Long 0.668 on GPT-4o. Outperforms because it "echoes cognitive findings on post hoc rationalization."
 - **Direct GTOS implication**: the V4 output order `{candidate_direction, candidate_rationale, reject_reasons}` (decision first, justification after) may outperform current V3 order `{reasoning_thread, decision}`. This is testable.

- **Kim et al. 2024 — Financial Statement Analysis with LLMs** ([arXiv:2407.17866](https://arxiv.org/html/2407.17866v2)): 150,678 firm-years. **Simple prompt (52.33%) ≈ analyst (52.71%); CoT prompt 60.35%; ANN 60.45%.** Here CoT *helped* (+8pp). Task is structured, non-narrative tabular data — closer to GTOS's MSO decision than sentiment classification.
 - **This is evidence that CoT helps GTOS-like structured tasks.**
 - Reconcile with Hung et al.: when the task requires **computation and synthesis** (financial ratios → earnings direction), CoT adds value; when the task is **pattern recognition** (sentiment), CoT hurts. GTOS MSO decision is on the boundary.

- **Shi et al. 2025 — Can LLMs Trade?** ([arXiv:2504.10789](https://arxiv.org/html/2504.10789v1)): *"LLMs... faithfully follow directions regardless of profit implications... maintain their strategic direction even when market conditions change, following their instructions even if doing so results in financial losses."* **GTOS-relevant**: Claude's compliance is a feature, not a bug, for gate enforcement — the model will follow rigid rules. The failure mode is *interpretive* ambiguity in the rules, not strategic drift.

- **Shi et al. 2025 — Can LLM Investing Strategies Outperform?** ([arXiv:2505.07078](https://arxiv.org/html/2505.07078v5)): FINSABER 20-year backtest. LLM-agent strategies *"neither... generate statistically significant alpha"* (all p>0.34). FinAgent Sharpe 0.241 vs Buy-and-Hold Sharpe 0.703. *"Improving prompts alone won't solve LLM investor underperformance."* **Sobering but**: this is about alpha-generation, not about *filtering/gating* a mechanically-valid edge (which is GTOS's actual task). Misapplying this paper would be a category error.

- **Xiao et al. 2024 — TradingAgents** ([arXiv:2412.20138](https://arxiv.org/html/2412.20138v3)): multi-agent with explicit Bull/Bear researchers, risk-seeking/neutral/conservative gates. Returns 23-26% Jan-Mar 2024, Sharpe 5.6-8.2. **Caveat**: single 3-month window, no cross-period validation. **Design insight**: *"Agents communicate primarily through structured documents"* — natural-language dialogue reserved for debate; analyst/trader outputs are structured. GTOS's `MarketStateObject` serialization is aligned with this.

- **Zhou et al. 2025 — ATLAS** ([arXiv:2510.15949](https://arxiv.org/html/2510.15949v1)): **this is the closest external analog to GTOS.**
 - Adaptive-OPRO (prompt optimized against windowed returns): GPT-o3 -6.11% → 9.02% ROI; GPT-o4-mini -1.30% → 9.06%.
 - Win rate jumps: GPT-o4-mini 29.17% → 65.28% (bullish regime).
 - **The Reflection Paradox**: self-reflection loops *degrade* performance. Claude Sonnet 4 reflection -5.69% vs baseline -7.26% — still bad.
 - **Model-specific drift pattern**: *"Claude Sonnet 4: High variance, erratic patterns; reasoning mode increases variance further. Drifts toward overly rigid, procedural instructions."* **This is the direct analog to GTOS's V3 regression.** ATLAS observed Claude Sonnet 4 drifting to rigid procedural rules as a *failure mode*, not a feature. V3 → V4 evolution should bias *away* from procedural expansion.

- **Liu et al. 2025 — LLM-Guided RL in Quant Trading** ([arXiv:2508.02366](https://arxiv.org/html/2508.02366v2)):
 - LLM signals integrated via **entropy-adjusted confidence** (signal strength weighted by output certainty).
 - **Writer-Judge iterative refinement loop** (with regret minimization) improved prompts: Sharpe 0.69 (baseline) → 1.02 (P4 optimized prompt); lowest perplexity 1.35, lowest entropy 0.67.
 - Expert review (10 professionals, 3-dimension rubric: economic rationale, domain fidelity, trade safety): avg 2.7/3.0 on P4.
 - **Reproducibility finding**: LLM+RL outperformed RL-only in 4 of 6 stocks, Sharpe 1.10 vs 0.64 (p<0.05). **"All observed improvements stemmed from LLM guidance"** (no RL algorithm change).
 - **Implications for GTOS**: entropy-adjusted confidence is a well-validated pattern for soft-weighting LLM signals. GTOS currently uses `confidence_score` as hard field but does not weight downstream execution by entropy. Future work only — V4 itself doesn't need it.

- **Weiser 2025 — When Valid Signals Fail** ([arXiv:2604.10996](https://arxiv.org/html/2604.10996)): LLM feature IC optimized -0.024 → +0.104 by treating prompt as hyperparameter. **Crucially**: same feature works in calm H2 2025 (Sharpe 1.038) and fails in volatile H1 2025 (Sharpe -0.267). **GTOS implication**: regime-dependent LLM-signal decay is real. Monitor the structure-detector promotion gate (already scheduled).

### 3.5 Instruction hierarchy + conflict resolution
- **Geng et al. 2025 — Control Illusion** ([arXiv:2502.15851](https://arxiv.org/html/2502.15851v1)): 1,200 test cases × 6 models including Claude.
 - **Baseline single-constraint compliance**: 75-91%. **With conflict: 9.6-45.8%.**
 - **GPT-4o 40.8% < GPT-4o-mini 45.8%** — larger ≠ better on hierarchy.
 - **Explicit acknowledgment of conflicts**: 0-20%.
 - **What works**: labeled constraints ("Constraint 1 PRIORITY:...") boosted Llama-70B from 14.2% to 75.8% on some tests. **Placing guidance in *user* message sometimes outperformed system messages.**
 - **Direct GTOS V4 implication**: the V3 "MSO label vs recent CHoCH override" is a textbook priority conflict. V4 needs explicit `PRIORITY 1 / PRIORITY 2 / PRIORITY 3` labeling, *in-line*, not implicit via section ordering. This is the highest-leverage concrete change this document recommends.

- **OpenAI 2024 — Instruction Hierarchy** ([arXiv:2404.13208](https://arxiv.org/abs/2404.13208)): hierarchy is a training-time property, not a prompt-time property. Prompts can reinforce it but not create it from scratch.

- **ManyIH 2025 — Many-Tier Hierarchy** ([arXiv:2604.09443](https://arxiv.org/html/2604.09443)): models can handle up to 12 priority levels but degrade. **Keep GTOS to ≤4 priority tiers.**

### 3.6 Confidence calibration
- **Zhu et al. 2025 — Mind the Confidence Gap** ([arXiv:2502.11028](https://arxiv.org/html/2502.11028v3)): LLMs systematically overconfident. *"Models claiming 93% confidence while being completely wrong."* ECE 0.45 on SimpleQA for GPT-4o.
 - **Distractor mitigation**: presenting one correct + three plausible wrong options yields **up to 460% relative accuracy gain and 90% ECE reduction**. (Classic n-AFC pattern.)
 - **GTOS V4 implication for confidence_score**: V3 asks AI for a free-form confidence score 0-100; result is ~72 for every CAND. Consider **forced-choice** instead: `confidence_tier: Literal["high_conviction", "moderate", "marginal_pass"]` enforced by enum. Forces the model to commit to a discrete category rather than hedging to 72.

- **Kadavath et al. 2022, Anthropic** — LLM "P(True)" self-evaluation: Claude 3.5-class models are reasonably well-calibrated on verbal-probability questions when asked post-hoc. GTOS's confidence-as-part-of-CAND-output is a single-pass variant, which is known to be worse-calibrated than explicit P(True) separate calls.

### 3.7 Few-shot best practices
- **Zhao et al. 2021** (cited in Weng 2023): biases in few-shot:
 1. **Majority label bias** — imbalanced distribution skews predictions.
 2. **Recency bias** — models echo the label at the end.
 3. **Common token bias** — preference for frequent tokens.
 - **Implication for V4 example design**: if GTOS adds 4 worked examples, they must have balanced LONG/SHORT/NO_TRADE counts and be shuffled.

- **Weng 2023 — Prompt Engineering** ([lilianweng.github.io](https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/)): few-shot biases "cause dramatically different performance, from near random guess to near SoTA."

- **Zhang et al. 2025 — The Few-shot Dilemma** ([arXiv:2509.13196](https://arxiv.org/html/2509.13196v1)): "over-prompting." Performance peaks 10-20 examples on 8B+ models, then declines. **Smaller models degrade from example 1.** Sonnet 4.6 is large enough to absorb 3-5 examples without degradation.

- **Sujan et al. 2025 — AD-FCoT** ([arXiv:2509.12611](https://arxiv.org/html/2509.12611)): analogy-driven CoT for financial sentiment. Two *contrasting* historical analogies (positive-outcome + negative-outcome) embedded in the prompt. AD-FCoT 54.92% vs Few-Shot 54.70% accuracy — **modest gain, but transparency benefits** (auditable reasoning). Pattern is: "this case resembles [past case X] which resolved [direction]."
 - **GTOS application**: V4 worked examples could follow the AD-FCoT pattern — two contrasting MSO snapshots (one valid CAND, one similar-looking but rejected CAND) with explicit "this is different from X because..." reasoning.

### 3.8 LLM-as-judge rubric design
- **Hashemi et al. 2024 — LLM-Rubric** ([ACL 2024](https://aclanthology.org/2024.acl-long.745.pdf)): multidimensional rubrics "reduce variance in scoring by separating evaluation into distinct categories." Calibration against human judgments.
- **Liu et al. 2023 — G-Eval** (EMNLP 2023): "providing a scoring scale and rubric, with LLMs generating a chain of thought of detailed evaluation steps."
- **Promptfoo LLM-Rubric docs**: *"Specifying well-defined rubrics and concrete examples is key... including example responses along with their corresponding scores significantly improves reliability."*
 - **GTOS V4 application**: current C1/C2/C3 scaffold is already rubric-style. Strengthen by:
 1. Making each gate return a boolean (enum) explicitly.
 2. Requiring the AI to echo the gate-check outcome in a `<gate_checks>` XML block before the final decision.
 3. Rejecting post-hoc if the echoed gate-checks don't match the decision (A5-style post-AI validator).

---

## 4. Industry Practitioner Patterns

### 4.1 Production LLM-trading systems (public lessons)

- **Ilya Navogitsyn (Quant Dev, 2026)** via [Dataconomy](https://dataconomy.com/2026/01/30/llms-dont-invent-alpha-a-quant-devs-reality-check-on-ai-in-trading/) (403 on fetch, quoted from search result): *"Before an LLM touches anything close to live trading, it needs hard boundaries, full observability, and the ability to fail loudly. Every output must be reviewable, reproducible, and easy to say 'no' to."* — matches GTOS's existing permission gates, A5 post-AI validator, shadow loggers. The prescription is "guardrails + observability > better prompts."

- **Numerai + JPMorgan $500M validation (2025)**: crowdsourced model ensemble, not LLM-direct-trading. **Inference**: the production industry treats LLMs as *feature extractors* or *model ensemble members*, not as autonomous deciders. GTOS's architecture (LLM as MSO gate, not as price-predictor) is consistent with this.

- **ATLAS paper observation**: *"The order-level action space (specifying order type, size, price, timing) reveals execution quality separately from analytical ability, exposing models that produce sound analysis but poor position-sizing decisions."* — GTOS separates this correctly: AI emits CANDIDATE + directional zone; execution.py applies position-sizing deterministically.

### 4.2 Retail + Claude-specific trading resources

- **PickMyTrade Claude 4.1 guide**: emphasis on "verify outputs, AI can hallucinate prices," "define acceptance criteria," "require human review." No specific prompt templates that go beyond Anthropic's own docs.

- **Roguequant "Prompt Engineering for Traders"**: claims "profit factor 2.0 → 5.0 via prompt structure alone." No rigorous evidence. 8-pattern list aligns with Anthropic best practices. **Treat as opinion piece** — useful for vocabulary, not evidence.

- **QuantVPS / Medium Claude-trading guides**: repeat Anthropic best practices, add "backtest overfitting" and "hallucination" warnings. No novel patterns beyond what's in section 2.

- **r/algotrading overall signal**: production retail LLM-trading is largely *workflow* (code generation, backtest writing) not *decision* (live gate). Very few systems resemble GTOS's architecture. **GTOS is ahead of the public retail LLM-trading curve** in terms of live-running with an LLM gate.

### 4.3 Prompt-engineering / eval tooling

- **DSPy (Stanford)**: declarative prompt programming, automatic optimization (MIPROv2, GEPA). Reported **20 percentage-point improvement** on structured extraction via DSPy + GEPA + BAML Adapter. **Not a drop-in for GTOS V4** (would require re-architecting the prompt build path) but worth considering for V5 — treat prompts as declarative code with optimization metrics (win rate, CAND rate).

- **Promptfoo**: `llm-rubric` assertions, `--repeat` flag for determinism testing, CI integration. **Directly applicable to V4 canary harness** — add `--repeat 5` on the 4 V3-divergent candles to measure self-agreement rate before/after V4.

---

## 5. Specific Recommendations Mapped to GTOS V4

### Question 1 — Multi-timeframe structural conflicts (D1 bullish + H1 bearish CHoCH → what should AI do?)

**Evidence base**: §3.5 (Control Illusion, Instruction Hierarchy), §3.4 (Trading-R1, ATLAS), §2.6 (Anthropic commit-to-approach).

**Recommendation**: **Explicit priority table in the prompt, not hierarchical implication.**

```
<priority_resolution>
When timeframes disagree, resolve in this order:
1. PRIMARY (Tradable): H1 structure — determines direction of this trade.
2. CONTEXT (Do-not-fight): D1 + H4 — if they strongly contradict H1, REJECT (no trade), do not inverse.
3. TRIGGER (Entry timing): M15 — does not override direction; only chooses entry.

Concrete examples:
- D1 bullish, H4 neutral, H1 bearish CHoCH → REJECT (H4 doesn't support H1's new direction).
- D1 bullish, H4 bullish, H1 bearish CHoCH → REJECT (H1 contradicts both higher TFs; likely pullback noise, not new structure).
- D1 bullish, H4 bullish, H1 bullish BOS + M15 pullback to OB → CANDIDATE LONG.
- D1 bearish, H4 bearish, H1 bullish CHoCH + strong displacement + untested demand OB → CANDIDATE LONG (H1 is tradable, D1/H4 are "watch for failure" not "fight the trade").

This resolves the known V3 inconsistency where the AI sometimes respected MSO H1 strictly and sometimes overrode it based on daily bias.
</priority_resolution>
```

**Rationale**: Control Illusion study shows labeled "Constraint 1 PRIORITY" boosted hierarchy adherence by up to 60pp. The concrete example list closes interpretive ambiguity (the V3 core failure mode).

### Question 2 — Decision consistency across similar-but-not-identical inputs

**Evidence base**: §3.2 (PRIN, Chain of Guidance, Non-Determinism), §3.3 (Lost in the Middle, Context Length), §3.5 (Hierarchy).

**Recommendations** (ordered by leverage):

1. **Measure noise floor first.** Run V3 prompt 10× on the 4 divergent candles. Establish baseline self-agreement rate. Atil et al. suggest this will be 50-85%, not 100%. V4 cannot go below that floor; the goal is *residual* improvement.

2. **Shrink context.** V3 at 15K tokens is in the degradation zone (§3.3). Dedupe R1-R8 allow-list (currently appears 3× per CLAUDE.md unresolved #5). Move verbose examples to `<examples>` at the end (Anthropic query-at-end gives up to 30% improvement).

3. **Structured Outputs with Literal-enum fields.** Close the `no_trade_reason: Optional[str]` loophole mechanically — ~10-15% of reasoning-drift is just the model picking a slightly-different reason phrase. Force to allow-list at the schema layer.

4. **"Think first" scratchpad** with explicit gate-echo before decision:
```
<gate_checks>
C1_structure_aligned: true | false
C2_valid_OB_exists: true | false
C3_displacement_quality: strong | moderate | weak
</gate_checks>
<decision>CANDIDATE | NO_TRADE</decision>
```
Add A5-style post-AI validator: if `decision == CANDIDATE` but any `C*` is false, reject.

5. **Temperature=0 is already set, but do not treat as magic.** Add a `--repeat 3` regression harness for canary: new fixtures run 3× with majority vote (dev-only, not production path).

### Question 3 — Bias-override rules ("recent event overrides prior structure")

**Evidence base**: §3.5 (Control Illusion), §3.4 (Trading-R1 multi-TF arbitration), §2.3 (Anthropic commit-to-approach).

**Recommendation**: Forbid the open-ended "recent event overrides bias" interpretation. Replace with explicit enumerated cases.

```
<bias_override_rules>
The MSO computed_bias is authoritative EXCEPT in these specific enumerated cases:

OVERRIDE-1: H1 BOS with displacement ≥ 1.5 ATR and mitigation of prior structure high/low → new H1 structure direction is tradable, regardless of D1 bias (but see priority_resolution for D1 conflict handling).

OVERRIDE-2: H1 CHoCH alone is NOT sufficient to override computed_bias. A CHoCH requires confirmation via (a) BOS in the new direction, OR (b) displacement candle closing beyond the CHoCH level.

OVERRIDE-3: "Recent event overrides bias" is NOT a valid rationale outside OVERRIDE-1 and OVERRIDE-2. Any CANDIDATE emission citing "recent CHoCH suggests a reversal" is INVALID.
</bias_override_rules>
```

**Rationale**: This is the exact prescription from the ATLAS + Control Illusion literature — turn interpretive rules into enumerated cases with explicit fallbacks. Prevents the V3 loophole.

### Question 4 — Structured multi-criteria gate evaluation (C1/C2/C3 pattern)

**Evidence base**: §2.4 (Anthropic parallelization recommendation), §3.8 (LLM-Rubric, G-Eval, AD-FCoT).

**Recommendations**:

1. **Keep single-call** (parallelization would 3× cost; not cost-justified for MSO gate).
2. **Per-gate enum outputs** (not free-text): each gate returns `pass | fail | marginal`.
3. **Rubric-scaffolded CoT** inside `<gate_checks>` block, one paragraph per gate explicitly citing MSO fields.
4. **Post-AI validator** (A5-pattern): if `decision == CANDIDATE` requires all three `pass`, reject otherwise.
5. **Worked examples** (2-3, AD-FCoT style): one obvious pass, one obvious reject, one borderline-that-should-reject. Show the full `<gate_checks>` reasoning pattern.

### Question 5 — Gaming-pattern prevention without new interpretive ambiguity

**Evidence base**: §3.5 (hierarchy), §3.6 (Structured Outputs), CLAUDE.md unresolved #5.

**Recommendations**:

1. **Move all enforcement to Structured Outputs schema where possible.** `touches < 2` is enforceable as a JSON Schema `minimum: 2` constraint on a derived field — if the AI emits `touches: 1`, the response is schema-invalid before it hits the parser. No prompt-text reliance needed.
2. **For the non-schema-enforceable patterns** (e.g., "at-current-price" loophole), use **explicit enumerated forbidden patterns** with one-line rationale:
 ```
 <forbidden_patterns>
 1. OB touches < 2 (unproven zone; requires prior reaction to validate).
 2. Entry price at or within 0.3 ATR of current price (no pullback opportunity; entry-quality gate).
 3. Weak-bias CAND (computed_bias = "weakly_bullish" AND no strong supporting framework).
 4. Partial-mitigation CAND (OB already tested and held; retest bias degraded).
 5. Age-stale CAND (OB > 72 H1 candles old without fresh touches).
 </forbidden_patterns>
 ```
3. **Avoid negative-prompting where positive works**: Anthropic recommendation. E.g., "Only emit CANDIDATE if the zone is fresh (≥ 2 touches confirmed, age < 72 H1 candles)" beats "do not emit CANDIDATE on stale/partial/weak/at-price zones" — same information, less cognitive load for the model.
4. **V4 prompt length target: ≤ 70% of V3.** The R1-R8 3× duplication (CLAUDE.md unresolved #5) should drop to 1×. Total target ≤ 10K tokens (vs ~15K current).

### Question 6 — Confidence calibration

**Evidence base**: §3.6 (Mind the Confidence Gap, distractor 460% gain).

**Recommendations**:

1. **Replace free-form `confidence_score: int 0-100` with `confidence_tier: Literal["high_conviction", "moderate", "marginal_pass"]`.** Forced-choice vastly outperforms free-form (basis: 460% accuracy gain on SimpleQA with forced n-AFC format).
2. **Calibrate tiers against live data** over 90 days. Shadow-log tier vs outcome. If high_conviction WR is not >10pp above moderate, the calibration is broken — deprecate the tier.
3. **Do not use confidence for execution filtering in V4.** Current `confidence_filter_mode: shadow` is correct. Only promote to `active` after validated calibration curve.
4. **Distractor pattern (optional, research-phase)**: for post-hoc eval only, ask the AI "Which direction is more probable, and by how much?" after the CANDIDATE emission, with LONG/SHORT/NO_TRADE as 3-way distractor. Compare distractor-based confidence to self-reported `confidence_tier`. Literature suggests distractor-based is better-calibrated.

---

## 6. Open Research Gaps

1. **Noise floor on GTOS MSO decisions.** No external study replicates GTOS's exact setup. Must run **V3 self-agreement replay** on the 4 divergent candles (n≥10 replays each) to establish baseline. Gap between observed divergence rate and floor is the *attributable* V3 failure.

2. **CoT helpful-or-harmful boundary for SMC decisions.** Financial sentiment (Hung 2025) says No-CoT wins; financial statement analysis (Kim 2024) says CoT wins. GTOS task is in between. Must A/B V4-with-CoT vs V4-LIRA (decision-first-then-justify) on the same canary.

3. **Prompt length vs decision quality at GTOS scale.** General literature (§3.3) shows degradation ≥7.5K tokens. GTOS at 15K has not been A/B'd against a lean 8K variant on live decisions. Gap: is V3 brittleness *fundamentally* a length problem, or a rule-conflict problem?

4. **Few-shot example impact on classification consistency.** No GTOS prompt to date has worked examples. Literature predicts large gain (+15-40% vs zero-shot) but also majority-label bias if examples are imbalanced. Gap: design 3-5 AD-FCoT-style contrasting MSO examples and measure impact on self-agreement rate.

5. **Structured Outputs rollout cost.** Anthropic's Structured Outputs feature has a first-request grammar-compilation latency. GTOS decision-path latency is not in the critical path (M15 candle close → AI call has seconds of slack), but untested at production. Gap: micro-benchmark Structured-Outputs-enabled V4 vs current V3 latency.

6. **Confidence tier calibration.** Literature gives strong priors (distractors help) but no SMC-specific data. Gap: 30-90 days shadow data of `confidence_tier` vs outcome to build calibration curve.

7. **Model migration (Sonnet 4.6 → Opus 4.7).** Anthropic says 4.7 "respects effort levels strictly" and is "more literal." Unclear whether the V3-specific inconsistency is Sonnet-4.6-specific or persists on 4.7. Gap: run same 4-divergent-candle test on Opus 4.7 with V3 prompt (cheap sanity check: ~$5).

---

## 7. Bibliography

### Anthropic official sources

1. [Prompting best practices (master doc)](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — Anthropic, current (2026).
2. [Structured Outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — Anthropic, 2026.
3. [Extended Thinking / Adaptive Thinking docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) — Anthropic, 2026.
4. [Effort parameter docs](https://platform.claude.com/docs/en/build-with-claude/effort) — Anthropic, 2026.
5. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — Anthropic Engineering, Dec 2024.
6. [The "think" tool](https://www.anthropic.com/engineering/claude-think-tool) — Anthropic Engineering, Mar 2025. τ-Bench results (0.370→0.570 Airline).
7. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Anthropic Engineering, Sep 2025.
8. [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — Anthropic Engineering, Jun 2025. 90.2% gain vs single-agent.
9. [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — Anthropic Engineering, Jan 2026. pass@k vs pass^k.
10. [Designing AI-resistant technical evaluations](https://www.anthropic.com/engineering/AI-resistant-technical-evaluations) — Anthropic Engineering, Jan 2026.
11. [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) — Anthropic Engineering, Apr 2026.
12. [Prompt engineering for business performance](https://www.anthropic.com/news/prompt-engineering-for-business-performance) — Anthropic news. Fortune 500 case study, 20% accuracy improvement.

### Academic — consistency + determinism

13. Wang, X. et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning in Language Models*. [arXiv:2203.11171](https://arxiv.org/abs/2203.11171). GSM8K +17.9%.
14. Atil et al. (2024). *Non-Determinism of "Deterministic" LLM Settings*. [arXiv:2408.04667](https://arxiv.org/html/2408.04667v5). 15% variance at temp=0.
15. Ma et al. (2025). *Prompt-Reverse Inconsistency*. [arXiv:2504.01282](https://arxiv.org/html/2504.01282v1). GPT-4 40% PRIN.
16. Khatun et al. (2024). *Improving Consistency through Chain of Guidance*. [arXiv:2502.15924](https://arxiv.org/html/2502.15924v1). Entailment 35.5→84.4.
17. Geng et al. (2025). *Control Illusion: The Failure of Instruction Hierarchies*. [arXiv:2502.15851](https://arxiv.org/html/2502.15851v1). GPT-4o 40.8% on conflict resolution.
18. Wallace et al. (OpenAI) (2024). *The Instruction Hierarchy*. [arXiv:2404.13208](https://arxiv.org/abs/2404.13208).

### Academic — long context

19. Liu et al. (2023). *Lost in the Middle: How Language Models Use Long Contexts*. arXiv:2307.03172. U-shape across position.
20. Hong et al. (2025). *Context Length Alone Hurts LLM Performance Despite Perfect Retrieval*. [arXiv:2510.05381](https://arxiv.org/html/2510.05381v1). 85% loss at 30K.

### Academic — CoT brittleness + when to use

21. Wei et al. (2022). *Chain-of-Thought Prompting Elicits Reasoning in LLMs*. [arXiv:2201.11903](https://arxiv.org/abs/2201.11903).
22. Saparov et al. (2024/2025). *Is Chain-of-Thought Reasoning of LLMs a Mirage?* arXiv:2508.01191. 33.3% accuracy drop with noisy rationales. CD-CoT recovers +17.8%.
23. (Unknown auth) (2025). *When Chain of Thought is Necessary, Language Models Struggle to Evade It*. [arXiv:2507.05246](https://arxiv.org/pdf/2507.05246). Monitor-evasion finding.

### Academic — financial LLM decisions

24. Hung et al. (2025). *Reasoning or Overthinking: Evaluating LLMs on Financial Sentiment Analysis*. [arXiv:2506.04574](https://arxiv.org/html/2506.04574v1). No-CoT beats CoT; LIRA pattern.
25. Kim et al. (2024). *Financial Statement Analysis with Large Language Models*. [arXiv:2407.17866](https://arxiv.org/html/2407.17866v2). GPT-4 CoT 60.35% beats analysts 52.71%.
26. Shi et al. (2025). *Can Large Language Models Trade? Testing Financial Theories with LLM Agents*. [arXiv:2504.10789](https://arxiv.org/html/2504.10789v1). LLMs faithfully follow prompts regardless of profit.
27. Shi et al. (2025). *Can LLM-based Financial Investing Strategies Outperform the Market?* [arXiv:2505.07078](https://arxiv.org/html/2505.07078v5). FINSABER, no statistically-significant alpha.
28. Xiao et al. (2024). *TradingAgents: Multi-Agents LLM Financial Trading Framework*. [arXiv:2412.20138](https://arxiv.org/html/2412.20138v3). 23-26% cumulative return, Sharpe 5.6-8.2 (3-month window).
29. Zhou et al. (2025). *ATLAS: Adaptive Trading with LLM Agents Through Dynamic Prompt Optimization*. [arXiv:2510.15949](https://arxiv.org/html/2510.15949v1). **Claude Sonnet 4 drifts to rigid procedural rules under reflection.**
30. Liu et al. (2025). *Language Model Guided RL in Quantitative Trading*. [arXiv:2508.02366](https://arxiv.org/html/2508.02366v2). Entropy-adjusted confidence, Writer-Judge loop, Sharpe 0.69→1.02.
31. Weiser (2025). *When Valid Signals Fail: Regime Boundaries Between LLM Features and RL Trading Policies*. [arXiv:2604.10996](https://arxiv.org/html/2604.10996). IC -0.024→+0.104 via prompt-as-hyperparameter; regime-dependent decay.
32. Sujan et al. (2025). *Analogy-Driven Financial Chain-of-Thought (AD-FCoT)*. [arXiv:2509.12611](https://arxiv.org/html/2509.12611). Contrasting historical analogies; 54.92% vs 54.70% few-shot.
33. Trading-R1 (2025). *Financial Trading with LLM Reasoning via RL*. [arXiv:2509.11420](https://arxiv.org/pdf/2509.11420). Multi-TF arbitration rules.
34. Gupta et al. (2025). *Tracing Positional Bias in Financial Decision-Making: Mechanistic Insights from Qwen2.5*. [arXiv:2508.18427](https://arxiv.org/html/2508.18427v1). 73,440 observations; Risk category stubbornly biased even at 14B.

### Academic — calibration

35. Zhu et al. (2025). *Mind the Confidence Gap: Overconfidence, Calibration, and Distractor Effects in LLMs*. [arXiv:2502.11028](https://arxiv.org/html/2502.11028v3). 460% accuracy gain, 90% ECE reduction via distractors.
36. Kadavath et al. (2022). *Language Models (Mostly) Know What They Know*. Anthropic P(True) self-evaluation.
37. (Multi-auth) (2024). *Uncertainty Quantification and Confidence Calibration in LLMs: A Survey*. [arXiv:2503.15850](https://arxiv.org/html/2503.15850).

### Academic — prompt engineering foundations

38. Weng, L. (2023). [Prompt Engineering](https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/). Comprehensive lilianweng.github.io guide.
39. Zhao et al. (2021). *Calibrate Before Use: Improving Few-Shot Performance of Language Models*. Biases in few-shot (majority, recency, common-token).
40. Zhang et al. (2025). *The Few-shot Dilemma: Over-prompting Large Language Models*. [arXiv:2509.13196](https://arxiv.org/html/2509.13196v1). Over-prompting curve; peak at 10-20 examples on 8B+ models.
41. Hashemi et al. (2024). *LLM-Rubric: A Multidimensional, Calibrated Approach*. [ACL 2024](https://aclanthology.org/2024.acl-long.745.pdf).
42. Liu et al. (2023). *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment*. EMNLP 2023.

### Industry + Practitioner

43. [LLMs Don't Invent Alpha: A Quant Dev's Reality Check](https://dataconomy.com/2026/01/30/llms-dont-invent-alpha-a-quant-devs-reality-check-on-ai-in-trading/). Dataconomy, Jan 2026.
44. [Claude 4.1 for Trading: 2025 Algo-Trading Copilot Guide](https://blog.pickmytrade.trade/claude-4-1-for-trading-guide/). PickMyTrade.
45. [Prompt Engineering for Traders: Making ChatGPT and Claude Fight](https://roguequant.substack.com/p/prompt-engineering-for-traders-how). Roguequant Substack.
46. [Quantifying The Irrational: LLM Prompt for Automated Trading](https://celanbryant.medium.com/quantifying-the-irrational-how-to-create-the-best-llm-prompt-for-automated-trading-strategies-6cde15e0f846). Medium.
47. [Testing Claude Sonnet 4.6 Adaptive Thinking on Production AI Agents](https://resolve.ai/blog/Our-early-impressions-of-Claude-Sonnet-4.6). Resolve.ai.
48. [Numerai structure + JPMorgan $500M](https://www.ainvest.com/news/future-quantitative-finance-jpmorgan-500m-bet-numerai-validates-ai-driven-crowdsourcing-scalable-alpha-generator-2508/). Ainvest, Aug 2025.

### Tooling

49. [DSPy framework](https://dspy.ai/) — declarative prompt programming. Stanford NLP.
50. [Promptfoo](https://www.promptfoo.dev/) — LLM eval + regression testing with `--repeat`.
51. [Why Temperature=0 Doesn't Guarantee Determinism](https://mbrenndoerfer.com/writing/why-llms-are-not-deterministic). Practitioner blog.

---

**End of EXTERNAL_RESEARCH.md.**
