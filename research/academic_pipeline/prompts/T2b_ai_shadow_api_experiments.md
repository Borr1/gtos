# T2b — AI Shadow API Experiments (H-3.3a, H-3.5a, H-9.1a, H-3.2a, H-3.6a)
## For: Claude Code execution agent (Sonnet, max effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor
## Basis: phase1_ai_evaluation_papers_v1.md (96 papers, 7 hypotheses)
## Budget: ~$80 in Claude API calls
## Prerequisite: T2a completed. Results: AUC≈0.5 for all ML models — outcomes within CANDIDATE pool are unpredictable. The CANDIDATE gate is a deterministic rules check (setup_grade explains 97%). Confidence score DEAD. This makes T2b HIGH PRIORITY — the question is no longer "does the LLM add accuracy?" (it doesn't) but "does the LLM's current configuration suppress CANDIDATE FREQUENCY?" Every experiment below should be interpreted FREQUENCY-FIRST: which condition produces more CANDIDATEs? WR differences < 5pp between conditions are noise (base rate is mechanical ~65%).

---

## Overview

Run 5 shadow API experiments that re-evaluate historical MSOs under modified conditions. Each experiment tests a specific mechanism identified by the L2 literature search. ALL experiments are shadow-only — they do NOT modify the live system.

**Experiments:**
1. **H-3.3a** — Session memory label scrambling (~$15)
2. **H-3.5a** — Majority label bias in session memory (~$15)
3. **H-9.1a** — CoT overthinking: simplified vs full prompt (~$10)
4. **H-3.2a** — SMC vs neutral statistical framing (~$10)
5. **H-3.6a** — 3-run self-consistency (~$30)

**Bonferroni correction:** 5 tests → p < 0.01 significance threshold.
**Practical significance:** |ΔWR| > 3pp or |ΔR| > 0.10R to be actionable.

---

## Phase 0: Shared Data Extraction

### Step 0.1: Select 50+ historical MSOs with known outcomes

From `knowledge_base_backtest/batch_api/`, select CANDIDATE evaluations where we know the trade outcome (WIN/LOSS) from the trade index.

**Selection criteria:**
1. Trade must be in `knowledge_base/index/_trade_index.json` with known outcome
2. The corresponding batch evaluation must have a `*_full_prompts.json` entry with the complete MSO (`prompt.user_message`) and system prompt (`prompt.system`)
3. The raw result must be parseable as CANDIDATE JSON

**T1 already matched 121 trades to batch evaluations.** Use the T1 matching logic or the T1 dataset (`research/academic_pipeline/data/entry_engineering_dataset.csv`) to identify which batch file + candle_time corresponds to each trade_id.

**Target: ALL matchable CANDIDATE evaluations (expect ~100-120).** More is better for statistical power.

### Step 0.2: Extract complete prompt pairs

For each selected MSO, store:
```python
{
    'trade_id': str,
    'candle_time': str,
    'system_prompt': str,       # From prompt.system (the full text, not the cache wrapper)
    'user_message': str,        # From prompt.user_message (MSO + dynamic context)
    'original_decision': str,   # CANDIDATE (all selected are CANDIDATEs)
    'original_confidence': int,
    'outcome': str,             # WIN or LOSS
    'r_multiple': float,
    'kill_zone': str,
}
```

**NOTE on system prompt format:** The batch `prompt.system` field is a list containing one dict: `[{'type': 'text', 'text': '...', 'cache_control': ...}]`. Extract the `text` field for the actual prompt string.

### Step 0.3: Build session memory contexts

For experiments H-3.3a and H-3.5a, we need to construct synthetic session memory blocks. Real session memory looks like this (injected into the user message):

```
## Prior Candle Assessments (this session)
The following are your assessments of prior candles in this kill zone.
Consider the progression: Is a setup developing across candles? ...

[Candle 1 evaluation summary]
[Candle 2 evaluation summary]
...
[Candle 5 evaluation summary]
```

**To construct session memory:** For each test MSO, find 5 other evaluations from the SAME date and kill zone in the batch data. These are the natural "prior candle" evaluations. Extract their condensed JSON (decision, brief reasoning) to build the memory block.

If fewer than 5 same-session evaluations exist: use 3. If fewer than 3: skip this MSO for memory experiments.

### Step 0.4: API call helper

```python
import anthropic
import json

client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY from environment

def evaluate_mso(system_prompt: str, user_message: str, 
                 temperature: float = 0, max_tokens: int = 2000) -> dict:
    """Call Claude Sonnet with the given prompt pair and return parsed JSON."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    text = response.content[0].text
    # Parse JSON from response (handle markdown fences)
    text_clean = text.strip()
    if text_clean.startswith("```"):
        text_clean = text_clean.split("```json")[-1].split("```")[0].strip()
    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        # Try finding first { to last }
        s = text_clean.find("{")
        e = text_clean.rfind("}")
        if s >= 0 and e > s:
            return json.loads(text_clean[s:e+1])
        return {"decision": "PARSE_ERROR", "raw": text}
```

**Rate limiting:** Insert `time.sleep(0.5)` between API calls to avoid rate limits. Total calls across all experiments: ~500-600. At ~$0.003/call average: ~$1.50-1.80 per 500 calls. Wait — actual cost is higher because input tokens are ~3000-5000 per call at $3/MTok input. Estimate: ~500 calls × 4K input tokens × $3/MTok = $6 input + output. Total ~$10-15 per experiment.

**Budget tracking:** Log cost after each experiment. Stop if cumulative cost exceeds $100.

---

## Experiment 1: Session Memory Label Scrambling (H-3.3a)

**Hypothesis:** Session memory with randomized CANDIDATE/NO_TRADE labels preserves >80% of the memory benefit, indicating the mechanism is distributional priming (regime inference), not outcome learning.

**Literature basis:** Min et al. 2022 (EMNLP) showed in-context learning works even with random labels. Xie et al. 2022 (ICLR) showed ICL is implicit Bayesian inference on the format, not the labels.

### Method

For each selected MSO (n~100):

**Condition A — Original memory:** Inject 5 real prior evaluations from the same session with their actual decisions (mostly NO_TRADE, occasionally CANDIDATE/WAIT).

**Condition B — Scrambled labels:** Same 5 prior evaluations, but randomly reassign each decision to CANDIDATE/NO_TRADE/WAIT (preserving the original distribution of labels across all sessions, but randomly shuffled per MSO). Keep the MSO data and reasoning text identical — only change the decision label.

**Condition C — No memory:** Original user_message with no session memory block.

```python
import random
random.seed(42)

for mso in selected_msos:
    # Condition A: real memory
    user_msg_a = inject_session_memory(mso['user_message'], mso['real_memory'])
    result_a = evaluate_mso(mso['system_prompt'], user_msg_a)
    
    # Condition B: scrambled labels
    scrambled = scramble_labels(mso['real_memory'], seed=42+idx)
    user_msg_b = inject_session_memory(mso['user_message'], scrambled)
    result_b = evaluate_mso(mso['system_prompt'], user_msg_b)
    
    # Condition C: no memory
    result_c = evaluate_mso(mso['system_prompt'], mso['user_message'])
```

### Metrics
- CANDIDATE rate per condition (A, B, C)
- Among CANDIDATEs that match original trades: WR per condition
- Mean confidence score per condition
- Agreement rate: % of MSOs where new decision matches original

### Decision gate
- If CANDIDATE_rate(B) is within 20% of CANDIDATE_rate(A): distributional priming confirmed. Session memory works via format/regime inference, not label content.
- If CANDIDATE_rate(C) << CANDIDATE_rate(A) AND CANDIDATE_rate(B) ≈ CANDIDATE_rate(A): memory helps, but labels don't matter. Simplify memory to include only MSO structure, not prior verdicts.
- If CANDIDATE_rate(B) << CANDIDATE_rate(A): labels DO matter. The model learns from prior decisions. Current memory design is correct.

---

## Experiment 2: Majority Label Bias (H-3.5a)

**Hypothesis:** When all 5 prior evaluations are NO_TRADE, the CANDIDATE rate drops by >5pp compared to when priors contain at least one CANDIDATE.

**Literature basis:** Zhao et al. 2021 (ICML) showed majority label bias up to 30pp in ICL. This is the leading candidate explanation for the zero-trade problem.

### Method

For each selected MSO (n~100):

**Condition A — All-NO_TRADE priors:** Inject 5 prior evaluations, ALL with decision=NO_TRADE (this is the typical real situation — CANDIDATE rate is 10.3%, so most sessions have all NO_TRADE priors).

**Condition B — Mixed priors:** Inject 5 prior evaluations where 2 are CANDIDATE and 3 are NO_TRADE. Use REAL CANDIDATE evaluations from OTHER sessions/dates as the 2 CANDIDATE priors. This tests whether seeing CANDIDATEs in the context makes the model more willing to output CANDIDATE.

**Condition C — No memory** (reuse from Experiment 1 if same MSOs).

### Metrics
- CANDIDATE rate per condition
- McNemar's test: paired comparison of CANDIDATE/NO_TRADE decisions between A and B
- Among trades where A says NO_TRADE but B says CANDIDATE: what is the true outcome? (This identifies trades lost to conservative bias.)

### Decision gate
- If CANDIDATE_rate(B) > CANDIDATE_rate(A) by >5pp (McNemar p < 0.01): majority label bias confirmed. This IS a contributing factor to the zero-trade problem.
  - **Immediate action:** Implement memory balancing — always include at least 1 CANDIDATE evaluation in session memory context, even if synthetic.
- If difference < 3pp: majority label bias is not a significant factor at this sample size.

---

## Experiment 3: CoT Overthinking (H-9.1a)

**Hypothesis:** A simplified binary prompt ("Is this a valid OB retest? YES/NO") achieves ≥ 60% WR, comparable to the full structured CoT prompt.

**Literature basis:** "Reasoning or Overthinking" (ACM ICAIF 2025) found CoT degrades financial classification accuracy vs direct prompting. The structured reasoning in the GTOS prompt may be causing "overthinking" — elaborate justification for wrong decisions.

### Method

**Prompt variant — Simplified binary:**

```python
SIMPLIFIED_PROMPT = """You evaluate M15 forex candles for H1 Order Block retest setups.

Rules:
1. Directional bias must be established (D1 or H4+H1 consensus)
2. H4 must align with bias direction  
3. Unmitigated H1 OB must exist from a confirmed structural break
4. Price must be at/near the OB in the correct zone (discount for longs, premium for shorts)
5. M15 must show CHoCH with displacement (body >= 1.5x 20-period average) in trade direction
6. R:R >= 1.5:1 with SL beyond OB + ATR buffer

If ALL rules are met, respond: {"decision": "CANDIDATE", "direction": "LONG"/"SHORT", "entry_price": <float>, "stop_loss": <float>, "take_profit_1": <float>}
If ANY rule fails, respond: {"decision": "NO_TRADE", "reason": "<which rule failed>"}

Respond with ONLY valid JSON. No explanation."""
```

This strips: SMC terminology, persona framing, self-check steps, confidence scoring, detailed reasoning fields, setup grading, breaker block evaluation.

For each selected MSO (n~100):

**Condition A — Full prompt:** Original system prompt + user message (temperature=0)
**Condition B — Simplified prompt:** Simplified system prompt + same user message (temperature=0)

### Metrics
- Decision agreement rate (A vs B)
- CANDIDATE rate per condition
- Among CANDIDATEs matched to trades: WR per condition
- Confidence of agreement: when both say CANDIDATE, does WR differ from when they disagree?

### Decision gate
- If CANDIDATE_rate(B) > CANDIDATE_rate(A) by >15% AND WR(B) >= 60%: **IMPLEMENT** simplified prompt. The extra CANDIDATEs carry the OB-zone base rate, and frequency gain outweighs any marginal WR dip.
- If WR(B) >= WR(A) - 2pp AND CANDIDATE_rate similar: the structured CoT is overhead for accuracy. Simplify the prompt (saves tokens, faster).
- If WR(B) < WR(A) - 5pp AND CANDIDATE_rate similar: the structured reasoning adds measurable value. Keep it.
- If CANDIDATE_rate(B) >> CANDIDATE_rate(A) AND WR(B) < 55%: the simplified prompt is too permissive — it lets through non-OB-zone trades. Keep current prompt.

---

## Experiment 4: SMC vs Neutral Framing (H-3.2a)

**Hypothesis:** A neutral statistical prompt (no "order blocks," "liquidity sweeps," "Smart Money" language) produces CANDIDATE decisions that align better with actual outcomes.

**Literature basis:** Spitale & Germani 2025 (Science Advances) showed source framing triggers systematic bias in LLMs. Turpin et al. 2023 (NeurIPS) showed LLMs rationalize with provided frameworks even when the framework doesn't affect the actual reasoning.

### Method

**Prompt variant — Neutral statistical framing:**

Take the original system prompt and systematically replace:
- "institutional forex trader" → "quantitative analyst"
- "Smart Money Concepts (SMC) and ICT methodology" → "statistical price structure analysis"
- "Order Block" / "OB" → "pre-break opposing candle zone" / "PBZ"
- "liquidity sweep" → "stop-cluster activation"
- "displacement" → "impulse magnitude"
- "Fair Value Gap" / "FVG" → "unfilled price gap"
- "premium/discount zone" → "upper/lower half of range"
- "CHoCH" → "structural reversal"
- "BOS" → "structural continuation"
- "kill zone" → "active session window"
- Remove the persona preamble entirely ("You are an institutional forex trader with 15+ years...")
- Remove "Smart Money" from all contexts
- Keep all rules (U1-U7, OB1-OB7) functionally identical, just with neutral language

**IMPORTANT:** Also neutralize the MSO text in the user message. Replace the same terms in the dynamic data. The MSO uses terms like "Sweeps," "Unmitigated OBs," "Unfilled FVGs" — replace these consistently.

For each selected MSO (n~100):

**Condition A — SMC framing:** Original prompt + original user message
**Condition B — Neutral framing:** Neutralized prompt + neutralized user message

### Metrics
- CANDIDATE rate per condition
- Decision agreement rate
- Among matched trades: WR per condition
- Confidence score distribution per condition
- Among DISAGREEMENTS (A=CANDIDATE, B=NO_TRADE or vice versa): what is the true outcome?

### Decision gate
- If WR(B) > WR(A) by > 3pp: neutral framing is better. Recommend prompt revision.
- If WR(A) > WR(B) by > 3pp: SMC framing helps (unexpected — the narrative provides useful structure).
- If difference < 3pp: framing doesn't matter for accuracy. Choose based on other factors (conciseness, token cost).

---

## Experiment 5: 3-Run Self-Consistency (H-3.6a)

**Hypothesis:** Unanimous 3-of-3 CANDIDATE decisions have WR > 70%, while split 2-of-3 decisions have WR < 60%. Disagreement rate is ~5-20%.

**Literature basis:** Wang et al. 2023 (ICLR) self-consistency. Betz et al. 2024 (EMNLP) optimal temperature 0.5-0.7. Aggarwal et al. 2023 (EMNLP) adaptive consistency for cost reduction.

### Method

For each selected MSO (n~100):

Run 3 evaluations using the ORIGINAL prompt + MSO, but with temperature=0.6:

```python
results = []
for run in range(3):
    result = evaluate_mso(
        mso['system_prompt'], 
        mso['user_message'],
        temperature=0.6  # Betz et al. 2024: optimal for diversity
    )
    results.append(result)
```

Classify each MSO:
- **Unanimous CANDIDATE:** 3/3 say CANDIDATE
- **Majority CANDIDATE:** 2/3 say CANDIDATE
- **Majority NO_TRADE:** 2/3 say NO_TRADE
- **Unanimous NO_TRADE:** 3/3 say NO_TRADE

### Metrics
- Distribution of agreement categories
- WR per category (among trades with known outcomes)
- For CANDIDATE trades: does the unanimous/split classification predict outcome?
- Entry/SL/TP variance across runs: how much do trade parameters differ?
- Effective CANDIDATE rate under majority vote vs single-run

### Cost analysis
- Track actual API cost for this experiment
- Compute: cost per marginal WR point gained
- Compare: 1x run at $60/month vs 3x at $180/month vs adaptive consistency at ~$100/month

### Decision gate
- If WR(unanimous) - WR(split) > 10pp: abstaining on splits is the highest-value intervention
- If agreement > 95%: ensemble adds little signal; disagreement logging still valuable for the ~5% uncertain cases
- If agreement 80-90%: meaningful diversity exists. Adaptive consistency (Aggarwal 2023) is worth implementing — stop after 2 runs if they agree, only run 3rd if they disagree

---

## Phase 6: Cross-Experiment Synthesis

After all 5 experiments, write:

### 1. The Memory Story (Exp 1 + 2)
- Does session memory help via labels or via distributional context?
- Is the zero-trade problem partially caused by majority-NO_TRADE bias?
- Combined recommendation: what should session memory look like?

### 2. The Prompt Story (Exp 3 + 4)
- Does the structured CoT help or hurt?
- Does SMC framing help or hurt?
- Combined recommendation: what should the prompt look like?
- Note: these two experiments test DIFFERENT things. CoT tests reasoning depth. SMC tests framing. A prompt could be simplified AND neutralized, or one but not the other.

### 3. The Ensemble Story (Exp 5)
- Is self-consistency worth the cost?
- Is disagreement logging worth the (lower) cost of running 2x with adaptive stopping?
- Does agreement rate replace the confidence score?

### 4. Combined Architecture Recommendation
Given ALL 5 results, what is the optimal Component 3A configuration?
- Prompt: full/simplified × SMC/neutral = 4 combinations. Which is best?
- Memory: real labels / scrambled labels / balanced labels / no memory?
- Evaluation: single-run / 3-run majority / adaptive 2-3 run?
- Confidence: current score / agreement rate / something else?

### 5. Frequency Impact Assessment (CRITICAL — most important section)
T2a proved outcomes within the CANDIDATE pool are unpredictable (AUC≈0.5). The system's edge is OB zone continuation mechanics (~65% base rate), NOT AI selectivity. This means:

- **Primary optimization target = CANDIDATE rate.** Any configuration that produces more CANDIDATEs WITHOUT dropping WR below ~60% is a net positive.
- **WR differences < 5pp between conditions are NOISE.** Do not recommend architecture changes based on small WR differences. The sample (n~100) has ~50% power for a 5pp difference.
- **The highest-value finding** from T2b would be: "Condition X produces N% more CANDIDATEs at statistically indistinguishable WR." That directly translates to more trades/month at the same edge.

For each experiment, compute and report:
- **Frequency multiplier:** CANDIDATE_rate(experimental) / CANDIDATE_rate(control)
- **Expected monthly trade delta:** frequency_multiplier × 17 current trades/month - 17
- **Net expected R/month impact:** trade_delta × 0.65 × mean_R_win - trade_delta × 0.35 × 1.0

### 6. Interaction with T2a and T3 results
- T2a confirmed: CANDIDATE gate is deterministic rules check (AUC=1.000). The LLM's value is zone detection + spatial reasoning on M15 confirmation, NOT statistical prediction.
- T3 tests whether specific feature thresholds (fib depth, round numbers, BOS quality) can sub-segment the CANDIDATE pool. T2b tests whether prompt/memory configuration affects pool SIZE.
- Together: T3 findings affect which trades to take, T2b findings affect how many trades the system generates.

---

## Output Files

Save results to: `research/academic_pipeline/results/T2b_shadow_api_results_v1.md`
Save analysis script to: `research/academic_pipeline/T2b_shadow_api_experiments.py`
Save raw API results to: `research/academic_pipeline/data/T2b_api_results.json`
Save cost tracking to: `research/academic_pipeline/data/T2b_cost_log.csv`

---

## Constraints

- **Do NOT modify any files in src/ or prompts/** — this is shadow testing only
- **Do NOT fabricate API responses.** If an API call fails, log the error and continue.
- **seed=42** for all randomization (label scrambling, session memory construction)
- **temperature=0** for all experiments except Experiment 5 (which uses 0.6)
- **temperature=0.6** for Experiment 5 only (per Betz et al. 2024)
- **Bonferroni threshold: p < 0.01** (5 tests)
- **Budget cap: $100.** Log cumulative cost after each experiment. If budget is exceeded, stop and report partial results for remaining experiments.
- **Rate limit: time.sleep(0.5)** between API calls
- **Never overwrite existing files** — use _v1 suffix
- **Model: claude-sonnet-4-20250514** — match the production model exactly
- If ANTHROPIC_API_KEY is not set: report "API_KEY_UNAVAILABLE" and exit. Do NOT hardcode any key.

---

## Prerequisites (execution agent must complete before starting)

### Environment Setup
```bash
pip install anthropic pandas scipy numpy
```

### Environment Variable
```bash
# MUST be set before running. If missing, exit with "API_KEY_UNAVAILABLE"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Required Codebase Reading (read these files BEFORE writing any code)

1. **`src/prompts/primary_analyzer_prompt.py`** — Read in full. Understand:
   - `build_system_prompt()` (line 66) — the full system prompt structure
   - `build_user_message()` (line 621) — how MSO + session memory + dynamic context are assembled
   - Session memory injection (lines 649-659) — the "## Prior Candle Assessments" block format
   - This is what you're replicating/modifying in the API calls

2. **`knowledge_base_backtest/batch_api/`** — List files, then read one `*_full_prompts.json` to understand the structure:
   - List format: `[{custom_id, date, candle_time, kill_zone, prompt: {system, user_message, model, temperature, max_tokens}}]`
   - `prompt.system` is wrapped in `[{'type': 'text', 'text': '...', 'cache_control': ...}]` — extract the inner `.text` field
   - `prompt.user_message` contains the full MSO with dynamic context

3. **`knowledge_base_backtest/batch_api/*_raw_results.json`** — Read one to understand response format:
   - Dict keyed by `date_kz_time` → AI decision JSON with action, direction, entry, sl, tp, confidence_score, reasoning

4. **`research/academic_pipeline/data/entry_engineering_dataset.csv`** — T1 already matched 121 trades to batch evaluations. Use this as the starting point for MSO selection.

5. **`knowledge_base/index/_trade_index.json`** — Trade outcomes (WIN/LOSS/BE) for matched trades

### API Knowledge Required

The execution agent must know how to use the Anthropic Messages API:
```python
from anthropic import Anthropic

client = Anthropic()  # Uses ANTHROPIC_API_KEY env var

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    temperature=0,  # or 0.6 for Experiment 5
    system=system_prompt_text,  # str, NOT a list
    messages=[{"role": "user", "content": user_message_text}]
)

# Parse response
ai_text = response.content[0].text
# Then json.loads(ai_text) to get the decision JSON
```

### Cost Tracking
- claude-sonnet-4-20250514: ~$3/1M input tokens, ~$15/1M output tokens
- Each evaluation: ~4000 input tokens (system + MSO) + ~500 output tokens ≈ $0.02/call
- Budget: $100 cap. Log cumulative cost in `research/academic_pipeline/data/T2b_cost_log.csv`
- Formula: `cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000`

---

## Pressure Test Log

**Issues found and fixed before delivery:**
1. Batch data has NO session memory (single-shot) → Experiments 1-2 must CONSTRUCT synthetic memory blocks from same-session evaluations. Added detailed construction instructions.
2. System prompt in batch data is wrapped in `[{'type': 'text', 'text': '...'}]` list → Added note to extract the inner text field.
3. SMC→neutral experiment needs to neutralize BOTH system prompt AND user message MSO text → Added explicit list of term replacements for user message.
4. Missing budget tracking → Added per-experiment cost logging with $100 cap.
5. Missing rate limiting → Added time.sleep(0.5) between calls.
6. Experiment 3 (CoT) simplified prompt was too stripped — missing minimum viable rules → Added the 6 essential rules in neutral language.
7. Missing cross-experiment interaction analysis → Added combined architecture recommendation section.
8. Missing connection to T2a results → Added explicit dependency: if T2a shows XGBoost matches, T2b experiments are informational, not actionable.
9. Experiment 2 didn't specify where to get CANDIDATE priors for mixed condition → Added: use real CANDIDATE evaluations from other sessions/dates.
10. Missing McNemar's test for paired comparison in Experiment 2 → Added.
11. Experiment 5 didn't specify what to do with trade parameter variance → Added: track entry/SL/TP variance across runs.
12. Missing prerequisites section → Added: pip installs, API key check, codebase reading list, API usage example, cost tracking formula.
