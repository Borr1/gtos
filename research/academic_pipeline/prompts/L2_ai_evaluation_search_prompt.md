# L2 AI Evaluation Optimization Literature Search Prompt (Q-3.1 to Q-3.7 + Q-9.1)
## For: Claude Code execution agent (Opus, high effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor

---

## Literature Search: AI Evaluation Optimization for Structured Trading Decisions (Q-3.1 to Q-3.7 + Q-9.1)

### Context

GTOS uses Claude Sonnet (claude-sonnet-4-20250514) as the decision engine in Component 3A. The AI receives a structured JSON Market State Object (MSO) containing ~30-50 features (swing positions, OB zones, FVGs, displacement quality, premium/discount, session levels, etc.) and outputs a structured JSON decision (CANDIDATE / NO_TRADE / WAIT) with trade parameters.

**How the AI currently works:**
- Input: structured JSON (~3000-5000 tokens of MSO data)
- Prompt: ~2500 tokens of OB retest evaluation instructions (see src/prompts/primary_analyzer_prompt.py)
- Output: structured JSON with decision, reasoning, trade parameters
- Model: Claude Sonnet (not GPT — this matters for Q-9.1)
- Cost: ~$60/month at current evaluation frequency
- The AI does NOT train or fine-tune — it reasons over each MSO independently
- Session memory: up to 5 recent evaluations are included as context in subsequent calls within the same kill zone session

**What we know about AI performance:**
- Batch WR: 65% overall, per-instrument range 59.5%-75%
- AI adds ~0pp to entry WR over mechanical OB entries (Test A rerun, n=219, p=NS) — the edge is zone detection, not AI selectivity
- Confidence scorer is a rubber stamp: 98% of CANDIDATEs get confidence=80. Confirmed useless, now in shadow mode.
- CANDIDATE rate: 10.3% of evaluated setups
- Session memory doubles expectancy (+0.66R vs +0.33R) in batch — mechanism unknown, unconfirmed live
- The system prompt includes anti-hallucination guardrails, conciseness rules, and a self-check step

**The existential question:** If a logistic regression on the same 7 displacement features matches the LLM (Q-3.7), we're paying $60/month for intelligence that a free statistical model provides. This search session determines whether the AI component is justified, needs fixing, or should be replaced.

### Questions

**Q-3.1: Optimal Signal Combination Method**
Search terms: "Bayesian" AND "signal combination" AND ("trading" OR "classification")
Also search: "structured data" AND ("LLM" OR "language model") AND ("tabular" OR "classification"), "expert system" AND "machine learning" AND "comparison" AND "financial", "Naive Bayes" AND "trading signal" AND "combination"
What we need: Is the LLM reasoning optimally over the structured features, or would a formal Bayesian combination rule (compute P(continuation | feature_1, feature_2, ...) via Bayes' theorem with empirical priors) outperform it? This overlaps with Q-3.7. The literature on "LLMs on tabular data" (2023-2024) is directly relevant — multiple papers show LLMs underperform gradient-boosted trees on structured/tabular tasks.

**Q-3.2: Narrative Fitting Bias from SMC Terminology**
Search terms: "framing effect" AND ("decision making" OR "judgment") AND ("financial" OR "trading")
Also search: "anchoring bias" AND "expert" AND "forecast", "narrative bias" AND ("AI" OR "machine learning") AND "prediction", "technical analysis" AND "cognitive bias", "Smart Money Concepts" AND "empirical"
What we need: The prompt uses SMC/ICT terminology — "order blocks," "liquidity sweeps," "displacement," "premium/discount." If "order block" is just "pullback to last opposing candle before a structural break," does the narrative wrapper help the AI reason better (by providing a causal framework) or hurt (by introducing terminology-specific biases)? The cognitive science literature on framing effects in expert judgment is relevant. Also: are there papers testing whether causal framing vs statistical framing changes AI model outputs?

**Q-3.3: Session Memory as Bayesian Updating**
Search terms: "sequential decision" AND "Bayesian updating" AND ("trading" OR "financial")
Also search: "context window" AND "decision quality" AND "AI", "in-context learning" AND "financial" AND "sequential", "adaptive" AND "intraday" AND "learning" AND "trading"
What we need: Session memory in GTOS means the AI sees up to 5 previous evaluations from the same kill zone when making a new decision. Batch testing showed +0.33R expectancy without memory → +0.66R with memory. What is the mechanism? Is the AI doing Bayesian updating (adjusting priors based on recent evaluations) or something else (pattern matching, anchoring)? The in-context learning literature (2023+) may explain how LLMs use prior examples to improve subsequent predictions. If we can formalize the mechanism, we can optimize the memory window (maybe 3 is better than 5, or 8 is better than 5).

**Q-3.4: Confidence Calibration Methods**
Search terms: "probability calibration" AND ("classifier" OR "machine learning") AND ("financial" OR "trading")
Also search: "Platt scaling" AND "calibration", "isotonic regression" AND "probability", "calibration curve" AND "reliability diagram" AND "prediction", "overconfidence" AND "AI" AND "financial forecast"
What we need: The current confidence scorer assigns 80 to 98% of CANDIDATEs — it is NOT calibrated. Question: (1) Is there a calibration method that would make the confidence score useful? (2) What features should the calibration model use? (3) Is the calibration problem with the LLM's own confidence, or with the separate confidence scoring module? The Platt scaling and isotonic regression literature provides standard methods. The question is whether they work with very small calibration sets (n~129 trades).

**Q-3.5: Sequential Evaluation Accuracy and Bias**
Search terms: "sequential decision" AND ("degradation" OR "fatigue" OR "drift") AND ("AI" OR "expert")
Also search: "anchoring" AND "sequential" AND "evaluation", "recency bias" AND "classification" AND "sequential", "order effect" AND "judgment" AND "multiple"
What we need: Does the AI's performance degrade through a kill zone session? The AI evaluates 10-20 candles per session. If later evaluations show lower WR or higher false-positive rate, there is an optimal session length. Note: for LLMs, this is about prompt/context effects, not fatigue — but anchoring to earlier evaluations (via session memory) could create bias. Does seeing 5 NO_TRADEs make the 6th evaluation more likely to be CANDIDATE (desperation bias)? Or less likely (conservative anchoring)?

**Q-3.6: Ensemble / Multiple-Run Methods**
Search terms: "self-consistency" AND "language model" AND ("reasoning" OR "decision")
Also search: "ensemble" AND ("LLM" OR "language model") AND "voting", "temperature" AND "sampling" AND "consistency" AND "AI", "multiple runs" AND "trading" AND "robustness", "bagging" AND "classifier" AND "cost benefit"
What we need: If we run the AI evaluation 3x on the same MSO (with temperature > 0 or minor prompt variations) and majority-vote, does WR improve? The self-consistency literature (Wang et al. 2023) shows this works for reasoning tasks. The cost is 3x API ($180/month instead of $60/month). The question is: what is the optimal number of runs, and does the marginal WR gain justify the cost? Also: do disagreements between runs carry information (i.e., if 2/3 say CANDIDATE and 1/3 says NO_TRADE, is that worse than 3/3 CANDIDATE)?

**Q-3.7: LLM vs Simple Statistical Model**
Search terms: "tabular data" AND ("LLM" OR "large language model") AND ("comparison" OR "benchmark")
Also search: "logistic regression" AND "trading" AND ("comparison" OR "versus" OR "benchmark"), "gradient boosting" AND "tabular" AND "language model", "simple model" AND "complex model" AND "financial" AND "comparison", "XGBoost" AND "LLM" AND "structured"
What we need: This is the existential question. If we train a logistic regression (or XGBoost) on the 7 key features (OB present, displacement quality, FVG present, touch count, premium/discount, H4 alignment, volume ratio) using the 129 trades as training data — does it match or beat the LLM's 65% WR? The "LLMs on tabular data" literature (2023-2024) consistently shows LLMs underperform tree-based methods on structured/tabular classification. But GTOS's task involves spatial reasoning over price structures, not pure tabular classification. The key question is: WHERE in the GTOS pipeline does LLM reasoning add value, if not in overall WR?

**Q-9.1: LLM Performance on Financial Reasoning Tasks**
Search terms: "LLM" AND "financial" AND ("reasoning" OR "analysis") AND ("benchmark" OR "evaluation")
Also search: "GPT" AND "financial" AND "performance" AND "assessment", "Claude" AND "financial" AND "analysis", "language model" AND "trading" AND "decision" AND "quality", "FinBench" OR "FLUE" OR "FinanceBench" (known financial LLM benchmarks)
What we need: How does Sonnet (or comparable LLMs) perform on financial reasoning tasks? Are there benchmarks? The BloombergGPT paper (2023) and FinGPT papers (2023) provide some data but mostly on NLP tasks (sentiment, NER), not on structured trading decisions. We need papers that test LLM reasoning on structured numerical inputs — closer to what GTOS actually does. If no such benchmark exists, document this as a critical gap.

**IMPORTANT NOTE for Q-9.1:** This literature is almost entirely from 2023-2025 and much of it is low quality (preprints, no peer review, small samples). Apply extra scrutiny. Require reproducible methodology and meaningful sample sizes. A blog post claiming "GPT-4 can trade" is not evidence.

### Exclusion Filters

REJECT papers that:
- Focus on LLM-generated trading signals from natural language (news sentiment, earnings calls) — GTOS uses structured data, not text
- Focus on reinforcement learning for portfolio optimization (different paradigm)
- Are "prompt engineering tips" without empirical evaluation
- Are from predatory journals (MDPI special issues, Hindawi)
- Claim exceptional trading performance without OOS validation or statistical testing
- Use backtesting without transaction costs

### Quality Filter (5 dimensions)

Rate each paper on:
1. **Testability on GTOS data:** Can we test this on our 129 trades / MSO evaluation pipeline? (High/Medium/Low)
2. **Data availability:** Does this need data beyond what GTOS produces (evaluation logs, MSO, outcomes)? (Available/Partial/Unavailable)
3. **Relevance to GTOS pipeline:** Does this address Component 3A specifically? (Direct/Indirect/Tangential)
4. **Journal tier:** Tier 1 (NeurIPS, ICML, ICLR, JF, RFS, QF), Tier 2 (AAAI, ACL, good finance/ML journals), Tier 3 (arXiv preprint, decent workshop), Tier 4 (MDPI, predatory, blog)
5. **OOS validation / reproducibility:** (Yes/Partial/No)

Promote papers scoring well on at least 3 of 5 dimensions.

### Cross-Reference Requirement

Check papers against:
- research/academic_pipeline/phase1_priority_a_papers.md (69 papers)
- research/academic_pipeline/phase1_entry_engineering_papers_v1.md (51 papers)
- research/academic_pipeline/phase1_feature_engineering_papers_v1.md (if it exists by the time you run)

Note cross-references; do not repeat full entries.

### Output Format

Match the structure of phase1_entry_engineering_papers_v1.md:
- Per-question sections with verdict
- Per-paper entries with: Authors, Year, Source, Quality Tier, Citations, Asset class / task tested, OOS validation, Relevance to GTOS, Question addressed, Key finding, Key equation / method, Testable on GTOS data
- Cross-Question Synthesis section
- Specific GTOS Implications section (testable hypotheses with method, prediction, required data)
- Rejected Papers table
- Full reference list

### Save Path

Save as: research/academic_pipeline/phase1_ai_evaluation_papers_v1.md

### Constraints

- Do NOT modify any files in src/ or prompts/
- The LLM-on-tabular-data findings (Q-3.7) should be interpreted carefully — GTOS's task involves SPATIAL reasoning over price structures, not pure tabular classification. A paper showing XGBoost beats GPT on Kaggle tabular datasets does not automatically mean XGBoost beats Sonnet on OB evaluation.
- Null results are valuable — "there is no evidence that LLMs outperform simple models on structured trading decisions" would be an important finding
- If a question has thin coverage, state "THIN COVERAGE" and explain what was searched and not found
- Quality over quantity — 8 excellent papers beat 25 mediocre ones
- Be especially critical of papers from 2023-2025 that claim LLMs can trade profitably — this literature has a massive publication bias problem

---

## Pressure Test Log

**Issues found and fixed before delivery:**
1. Q-3.1 and Q-3.7 overlap significantly → Acknowledged explicitly, added "LLM on tabular data" literature as a bridge between them
2. Q-3.2 needed cognitive science literature (framing effects, anchoring) not just finance → Added cognitive psychology search terms
3. Q-3.4 framed as "is it calibrated?" but answer is already known (NO) → Reframed as "what calibration METHODS would fix it" and "can they work with n=129"
4. Q-3.6 lacked LLM-specific ensemble methods → Added "self-consistency" (Wang et al. 2023) and "chain-of-thought voting" to search terms
5. Q-9.1 literature is mostly low-quality 2023+ preprints → Added explicit quality warning and requirement for reproducible methodology
6. Q-3.7 could be misread as "LLMs are bad at tabular data, therefore drop the LLM" → Added caveat that GTOS task involves spatial reasoning, not pure tabular classification
7. Missing financial LLM benchmark names → Added FinBench, FLUE, FinanceBench to Q-9.1 search terms
8. Missing cross-reference against feature engineering papers (may exist by execution time) → Added conditional cross-reference
9. Exclusion filter too broad initially — would have caught RL papers that ARE relevant to Q-3.3 → Narrowed to "RL for portfolio optimization" specifically
