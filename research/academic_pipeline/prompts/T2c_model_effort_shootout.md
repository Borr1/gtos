# T2c — Sonnet 4.6 Model + Effort Level Shootout
## For: Claude Code execution agent (one agent per effort level)
## Date: April 12, 2026
## Written by: Strategic Research Advisor
## Basis: T2b results + prompt drift analysis + Anthropic effort API docs
## Budget: $50 per agent ($150 total across 3 agents)

---

## CRITICAL: Set YOUR effort level

This prompt is deployed to 3 SEPARATE agents, each testing ONE effort level.

**YOU are testing effort level: `__EFFORT_LEVEL__`**

Replace `__EFFORT_LEVEL__` with exactly ONE of: `medium`, `high`, `max`

Each agent runs independently on the same 121 trades. Do NOT run other effort levels.

---

## Context

The GTOS trading system uses Claude Sonnet 4 (`claude-sonnet-4-20250514`) to evaluate M15 candles for XAUUSD/GBPUSD trade setups. The system is underperforming — near-zero trades in live operation.

**What we already know (from T2a + T2b):**
- Outcomes within the CANDIDATE pool are unpredictable (AUC≈0.5). The edge is OB zone mechanics (~65% base WR), not AI selectivity.
- Session memory suppresses CANDIDATE rate by 55% (distributional priming effect, p=0.007).
- Full CoT prompt is essential (simplified prompt → 0% CANDIDATE rate).
- Confidence scores are dead (rubber stamp at 80).
- **Primary optimization = CANDIDATE rate.** More trades at ~65% WR = more profit.

**What we don't know:**
- Does Sonnet 4.6 perform differently than Sonnet 4 on this task?
- Does the `effort` parameter affect CANDIDATE rate or WR?
- Does higher effort cause over-reasoning (like Opus/thinking did — 92-96% rejection)?
- Or does it improve decision quality without killing frequency?

**Prior finding (April 5):** Opus and forced-thinking on Sonnet 4 rejected 92-100% of trades. They interpreted "at or near the OB zone" hyper-literally. The `effort` parameter is DIFFERENT from forced thinking — it's a behavioral signal, not a strict thinking budget. It does NOT require temperature=1. This experiment tests whether effort on Sonnet 4.6 avoids the old over-rejection problem.

---

## What You Are Testing

**Single variable:** Sonnet 4.6 at effort=`__EFFORT_LEVEL__` (temperature=0, no extended thinking).

**Baseline comparison:** The original batch results from Sonnet 4 (temperature=0, no effort parameter) are already stored in the batch data. You will compare your results against these.

**Hypothesis:** Sonnet 4.6 at the tested effort level produces a different CANDIDATE rate and/or WR than Sonnet 4, on the same MSOs with the same prompts.

---

## Phase 0: Load Data

Reuse the T2b data loading logic. The code is in `research/academic_pipeline/T2b_shadow_api_experiments.py` — read it for reference.

### Step 0.1: Load MSOs

```python
import json, glob, os, csv, time, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

import pandas as pd
import numpy as np
from scipy import stats

BASE_DIR = Path(__file__).parent.parent.parent
BATCH_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
T1_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'

# CONFIGURATION — THIS IS THE ONLY THING THAT CHANGES BETWEEN AGENTS
EFFORT_LEVEL = '__EFFORT_LEVEL__'  # One of: 'medium', 'high', 'max'
MODEL = 'claude-sonnet-4-6-20250514'
BUDGET_CAP = 50.0

# Verify effort level is valid
assert EFFORT_LEVEL in ('medium', 'high', 'max'), f"Invalid effort: {EFFORT_LEVEL}"
```

### Step 0.2: Load batch entries (same as T2b)

Load ALL `*_full_prompts.json` files from `knowledge_base_backtest/batch_api/`. For each entry, extract:
- `candle_time` → key
- `prompt.system[0].text` → system_prompt (the full text including embedded market data)
- `prompt.user_message` → user_message

Also load ALL `*_raw_results.json` files to get the ORIGINAL Sonnet 4 decisions for comparison.

### Step 0.3: Match to T1 trades

Use `research/academic_pipeline/data/entry_engineering_dataset.csv` to get the 121+ trades with known outcomes. Match each trade's `candle_time` to the batch entry. Store:

```python
selected_msos = []
for _, row in df_t1.iterrows():
    ct = row['candle_time']
    if ct not in batch_by_ct:
        continue
    batch = batch_by_ct[ct]
    outcome = str(row['outcome'])
    if outcome == 'BREAKEVEN':
        outcome = 'LOSS'
    selected_msos.append({
        'trade_id': str(row['trade_id']),
        'candle_time': ct,
        'system_prompt': batch['system_prompt'],
        'user_message': batch['user_message'],
        'outcome': outcome,
        'r_multiple': float(row['r_multiple']) if not pd.isna(row['r_multiple']) else 0.0,
        'win': int(row['win']),
        'symbol': str(row['symbol']),
        'kill_zone': str(row['kill_zone']),
        'original_decision': raw_by_ct.get(ct, {}).get('decision', 'CANDIDATE'),
        'original_confidence': raw_by_ct.get(ct, {}).get('confidence_score', 80),
    })
```

Print: `Matched {len(selected_msos)} MSOs to batch entries`

Target: ~121 trades. If fewer than 100, investigate why.

---

## Phase 1: API Evaluation

### Step 1.1: API call helper

```python
from anthropic import Anthropic

API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    print('API_KEY_UNAVAILABLE — set ANTHROPIC_API_KEY and retry.')
    sys.exit(1)

client = Anthropic()

INPUT_COST_PER_TOK = 3.0 / 1_000_000   # Sonnet 4.6 input: $3/MTok
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000  # Sonnet 4.6 output: $15/MTok
cumulative_cost = 0.0
cost_log = []

def evaluate_mso(system_prompt: str, user_message: str, trade_id: str = '') -> dict:
    """Call Sonnet 4.6 with effort parameter and return parsed JSON."""
    global cumulative_cost

    if cumulative_cost >= BUDGET_CAP:
        return {'decision': 'BUDGET_EXCEEDED',
                'error': f'Cumulative cost ${cumulative_cost:.2f} exceeds ${BUDGET_CAP} cap'}

    time.sleep(0.5)  # Rate limiting

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,            # Increased from 2000 — effort=max may need more room
            temperature=0,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
            output_config={'effort': EFFORT_LEVEL},  # <-- THE KEY PARAMETER
        )
    except Exception as e:
        return {'decision': 'API_ERROR', 'error': str(e)[:300]}

    usage = response.usage
    cost = usage.input_tokens * INPUT_COST_PER_TOK + usage.output_tokens * OUTPUT_COST_PER_TOK
    cumulative_cost += cost
    cost_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'trade_id': trade_id,
        'input_tokens': usage.input_tokens,
        'output_tokens': usage.output_tokens,
        'call_cost': round(cost, 6),
        'cumulative_cost': round(cumulative_cost, 4),
    })

    # Parse JSON from response
    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = text.split('```json')[-1].split('```')[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s = text.find('{')
        e = text.rfind('}')
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e+1])
            except Exception:
                pass
        return {'decision': 'PARSE_ERROR', 'raw': text[:500]}
```

### Step 1.2: Run evaluations

```python
results = []

for i, mso in enumerate(selected_msos):
    print(f"  [{i+1}/{len(selected_msos)}] {mso['trade_id']} (${cumulative_cost:.2f})")

    result = evaluate_mso(
        mso['system_prompt'],
        mso['user_message'],
        trade_id=mso['trade_id'],
    )

    results.append({
        'trade_id': mso['trade_id'],
        'candle_time': mso['candle_time'],
        'symbol': mso['symbol'],
        'kill_zone': mso['kill_zone'],
        'outcome': mso['outcome'],
        'r_multiple': mso['r_multiple'],
        'win': mso['win'],
        # Original Sonnet 4 decision
        'original_decision': mso['original_decision'],
        'original_confidence': mso['original_confidence'],
        # New Sonnet 4.6 decision
        'new_decision': result.get('decision', 'PARSE_ERROR'),
        'new_confidence': result.get('confidence_score', 0),
        'new_setup_grade': result.get('reasoning', {}).get('setup_grade', ''),
        'new_framework': result.get('framework', ''),
        # Full response for debugging
        'new_response': result,
    })

    if cumulative_cost >= BUDGET_CAP:
        print(f"  BUDGET CAP REACHED at ${cumulative_cost:.2f}")
        break

print(f"\nCompleted {len(results)} evaluations. Total cost: ${cumulative_cost:.2f}")
```

---

## Phase 2: Analysis

### Step 2.1: Core metrics

Compute these on the completed results:

```python
df = pd.DataFrame(results)

# Decisions
n_total = len(df)
n_candidate = (df['new_decision'] == 'CANDIDATE').sum()
n_no_trade = (df['new_decision'] == 'NO_TRADE').sum()
n_other = n_total - n_candidate - n_no_trade  # WAIT, PARSE_ERROR, etc.

candidate_rate = n_candidate / n_total

# WR among CANDIDATEs (only those with known outcomes)
candidates = df[df['new_decision'] == 'CANDIDATE']
if len(candidates) > 0:
    wr = candidates['win'].mean()
    wr_n = len(candidates)
else:
    wr = float('nan')
    wr_n = 0

# CR × WR product (the real metric)
cr_wr = candidate_rate * wr if not np.isnan(wr) else 0

# Original Sonnet 4 baseline (from the batch data)
orig_candidate_rate = (df['original_decision'] == 'CANDIDATE').sum() / n_total
orig_candidates = df[df['original_decision'] == 'CANDIDATE']
orig_wr = orig_candidates['win'].mean() if len(orig_candidates) > 0 else float('nan')
orig_cr_wr = orig_candidate_rate * orig_wr if not np.isnan(orig_wr) else 0
```

### Step 2.2: Statistical tests

```python
from scipy.stats import chi2_contingency, fisher_exact

# Chi-squared: CANDIDATE rate new vs original
# Build 2x2 table: [new_cand, new_no_trade] vs [orig_cand, orig_no_trade]
# Use McNemar's test (paired comparison — same MSOs, different models)
n_both_cand = ((df['new_decision'] == 'CANDIDATE') & (df['original_decision'] == 'CANDIDATE')).sum()
n_new_only = ((df['new_decision'] == 'CANDIDATE') & (df['original_decision'] != 'CANDIDATE')).sum()
n_orig_only = ((df['new_decision'] != 'CANDIDATE') & (df['original_decision'] == 'CANDIDATE')).sum()
n_neither = ((df['new_decision'] != 'CANDIDATE') & (df['original_decision'] != 'CANDIDATE')).sum()

# McNemar's test
b, c = n_new_only, n_orig_only
if b + c > 0:
    mcnemar_chi2 = (abs(b - c) - 1)**2 / (b + c)  # with continuity correction
    mcnemar_p = 1 - stats.chi2.cdf(mcnemar_chi2, df=1)
else:
    mcnemar_chi2 = 0
    mcnemar_p = 1.0

# WR comparison (if both have CANDIDATEs)
# Fisher exact on paired outcomes
```

### Step 2.3: Agreement analysis

```python
# How often does Sonnet 4.6 agree with Sonnet 4?
agreement_rate = ((df['new_decision'] == 'CANDIDATE') == (df['original_decision'] == 'CANDIDATE')).mean()

# Disagreement breakdown
# Type 1: Sonnet 4 said CANDIDATE, Sonnet 4.6 says NO_TRADE (lost trades)
lost_trades = df[(df['original_decision'] == 'CANDIDATE') & (df['new_decision'] != 'CANDIDATE')]
lost_wr = lost_trades['win'].mean() if len(lost_trades) > 0 else float('nan')

# Type 2: Sonnet 4 said NO_TRADE, Sonnet 4.6 says CANDIDATE (gained trades)
# Note: original_decision is always CANDIDATE for our 121 trades (they were selected as CANDIDATEs)
# So "gained trades" means Sonnet 4.6 ALSO says CANDIDATE where Sonnet 4 did.
# "Lost trades" means Sonnet 4.6 rejects what Sonnet 4 accepted.
```

**IMPORTANT NOTE:** All 121 MSOs in the T1 dataset were originally CANDIDATE decisions. So the Sonnet 4 baseline CANDIDATE rate on this population is 100% by construction. The meaningful metric is: **what fraction does Sonnet 4.6 ALSO call CANDIDATE?** If it's lower, Sonnet 4.6 is MORE selective. If 100%, it agrees with Sonnet 4's selections.

This means:
- `CANDIDATE rate` = fraction Sonnet 4.6 agrees with Sonnet 4's CANDIDATE call
- `lost_trades` = MSOs where Sonnet 4 said CANDIDATE but Sonnet 4.6 says NO_TRADE
- The WR of `lost_trades` tells us: are the rejected trades disproportionately wins or losses?
- If lost_trades WR < 50%: Sonnet 4.6 is BETTER at filtering (removes more losers than winners)
- If lost_trades WR > 65%: Sonnet 4.6 is WORSE (removes good trades, like Opus did)

### Step 2.4: Confidence and grading

```python
# Confidence distribution
if len(candidates) > 0:
    conf_mean = candidates['new_confidence'].mean()
    conf_std = candidates['new_confidence'].std()
    conf_dist = candidates['new_confidence'].value_counts().sort_index()
else:
    conf_mean = conf_std = 0

# Setup grade distribution
grade_dist = df['new_setup_grade'].value_counts()

# Framework used
framework_dist = candidates['new_framework'].value_counts() if len(candidates) > 0 else pd.Series()
```

### Step 2.5: Token usage

```python
# Average tokens per call
if cost_log:
    avg_input = np.mean([c['input_tokens'] for c in cost_log])
    avg_output = np.mean([c['output_tokens'] for c in cost_log])
    avg_cost = np.mean([c['call_cost'] for c in cost_log])
    total_cost = cumulative_cost
```

---

## Phase 3: Output

### Step 3.1: Save results

```python
# JSON results
output_data = {
    'metadata': {
        'model': MODEL,
        'effort_level': EFFORT_LEVEL,
        'n_msos': len(results),
        'total_cost': round(cumulative_cost, 4),
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'baseline_model': 'claude-sonnet-4-20250514',
    },
    'summary': {
        'candidate_rate': round(candidate_rate, 4),
        'wr': round(wr, 4) if not np.isnan(wr) else None,
        'cr_wr': round(cr_wr, 4),
        'n_candidate': int(n_candidate),
        'n_no_trade': int(n_no_trade),
        'n_other': int(n_other),
        'agreement_with_baseline': round(agreement_rate, 4),
        'mcnemar_p': round(mcnemar_p, 6),
        'lost_trades_n': len(lost_trades),
        'lost_trades_wr': round(lost_wr, 4) if not np.isnan(lost_wr) else None,
        'avg_confidence': round(conf_mean, 1),
        'avg_input_tokens': round(avg_input, 0) if cost_log else 0,
        'avg_output_tokens': round(avg_output, 0) if cost_log else 0,
    },
    'rows': results,  # WARNING: contains full response JSON — may be large
}

# Save
out_json = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / f'T2c_{EFFORT_LEVEL}_results.json'
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)
```

### Step 3.2: Save cost log

```python
out_cost = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / f'T2c_{EFFORT_LEVEL}_cost_log.csv'
if cost_log:
    with open(out_cost, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_log[0].keys()))
        writer.writeheader()
        writer.writerows(cost_log)
```

### Step 3.3: Write report

Save to: `research/academic_pipeline/results/T2c_{EFFORT_LEVEL}_results_v1.md`

Report format:

```markdown
# T2c Model Shootout: Sonnet 4.6 effort={EFFORT_LEVEL}

**Date:** {date}
**Model:** claude-sonnet-4-6-20250514
**Effort:** {EFFORT_LEVEL}
**Baseline:** claude-sonnet-4-20250514 (Sonnet 4, no effort param)
**N MSOs:** {n}
**Total cost:** ${cost}

## Results

| Metric | Sonnet 4 (baseline) | Sonnet 4.6 effort={EFFORT_LEVEL} |
|--------|--------------------|---------------------------------|
| CANDIDATE rate | 100% (by construction) | {candidate_rate}% |
| WR (of CANDIDATEs) | {orig_wr}% (n={orig_n}) | {wr}% (n={wr_n}) |
| CR × WR | {orig_cr_wr} | {cr_wr} |
| Avg confidence | {orig_conf} | {conf_mean} |
| Avg output tokens | ~500 | {avg_output} |
| Cost per call | ~$0.02 | ${avg_cost} |

## Agreement Analysis

| Category | N | WR |
|----------|---|-----|
| Both CANDIDATE | {n_both_cand} | {wr_both}% |
| Sonnet 4.6 rejects (lost trades) | {n_lost} | {wr_lost}% |

## Lost Trades Analysis

Sonnet 4.6 rejected {n_lost} trades that Sonnet 4 accepted.
- WR of rejected trades: {wr_lost}%
- If > 65%: Sonnet 4.6 is OVER-REJECTING good trades (Opus-like behavior)
- If < 50%: Sonnet 4.6 is CORRECTLY filtering out losers
- If 50-65%: Sonnet 4.6 is rejecting randomly (no discriminatory value)

## Framework Distribution (Sonnet 4.6 CANDIDATEs)

{framework_dist}

## Grade Distribution

{grade_dist}

## Confidence Distribution

{conf_dist}

## Token Usage

- Avg input tokens: {avg_input}
- Avg output tokens: {avg_output}
- Total cost: ${total_cost}
- Projected monthly cost at 17 trades/day: ${monthly_cost}

## Raw Decision Log

{table of trade_id | outcome | original_decision | new_decision | new_confidence | new_grade}
```

---

## Constraints

- **Do NOT modify any files in src/ or prompts/** — this is shadow testing only
- **Do NOT fabricate API responses.** If an API call fails, log the error and continue.
- **Model: `claude-sonnet-4-6-20250514`** — NOT the old Sonnet 4
- **Effort: `__EFFORT_LEVEL__`** — do NOT run other effort levels
- **temperature=0** — deterministic, same as production
- **max_tokens=4096** — increased from 2000 to accommodate effort=max verbosity
- **output_config={"effort": EFFORT_LEVEL}** — the key parameter under test
- **Rate limit: time.sleep(0.5)** between API calls
- **Budget cap: $50** per agent. Stop and report if exceeded.
- **Never overwrite existing files** — use effort-level-specific filenames
- If ANTHROPIC_API_KEY is not set: report "API_KEY_UNAVAILABLE" and exit.

---

## Prerequisites

### Environment Setup
```bash
pip install anthropic pandas scipy numpy
```

### Environment Variable
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Required Reading (before writing code)

1. **`research/academic_pipeline/T2b_shadow_api_experiments.py`** — Read Phase 0 (lines 1-220). Reuse the data loading logic. This is your template for loading batch data and matching to T1 trades.

2. **`knowledge_base_backtest/batch_api/`** — One `*_full_prompts.json` to verify structure: `[{custom_id, candle_time, prompt: {system: [{type, text, cache_control}], user_message, model, max_tokens, temperature}}]`

3. **`research/academic_pipeline/data/entry_engineering_dataset.csv`** — The 121+ trades with known outcomes (trade_id, candle_time, outcome, r_multiple, win, symbol, kill_zone).

### API Syntax for Effort

```python
response = client.messages.create(
    model='claude-sonnet-4-6-20250514',
    max_tokens=4096,
    temperature=0,
    system=system_prompt_text,     # str, NOT a list
    messages=[{'role': 'user', 'content': user_message_text}],
    output_config={'effort': 'medium'},  # or 'high' or 'max'
)
```

**Note:** The `output_config` parameter is separate from `thinking`. We are NOT enabling thinking. We are only setting effort level. Temperature stays at 0. No `thinking` parameter needed.

### Verify Model ID

Before running evaluations, verify the model is accessible:

```python
try:
    test = client.messages.create(
        model='claude-sonnet-4-6-20250514',
        max_tokens=100,
        temperature=0,
        messages=[{'role': 'user', 'content': 'Reply with just the word "ready"'}],
        output_config={'effort': EFFORT_LEVEL},
    )
    print(f"Model check OK: {test.content[0].text}")
except Exception as e:
    print(f"Model check FAILED: {e}")
    # If model ID is wrong, try: 'claude-sonnet-4-6-latest'
    # Report the error and exit
    sys.exit(1)
```

**If the model ID `claude-sonnet-4-6-20250514` fails:** Try `claude-sonnet-4-6-latest` or just `claude-sonnet-4-6`. Report whichever works in the results metadata.

---

## Output Files

- `research/academic_pipeline/data/T2c_{EFFORT_LEVEL}_results.json` — Full results with per-trade decisions
- `research/academic_pipeline/data/T2c_{EFFORT_LEVEL}_cost_log.csv` — Per-call cost tracking
- `research/academic_pipeline/results/T2c_{EFFORT_LEVEL}_results_v1.md` — Human-readable report
- `research/academic_pipeline/T2c_model_effort_shootout.py` — The analysis script (save your code)

---

## Pressure Test Log

1. All 121 MSOs were originally CANDIDATE — so Sonnet 4 baseline CANDIDATE rate is 100% by construction. The real question is what fraction Sonnet 4.6 also calls CANDIDATE. Added explicit note about this.
2. System prompt in batch data is wrapped in list format — extract `.text` field. Documented.
3. `output_config` parameter syntax verified against Anthropic docs. Not to be confused with `thinking` parameter.
4. max_tokens increased to 4096 to prevent truncation at effort=max.
5. Model ID may vary — added fallback check and reporting.
6. Sonnet 4.6 pricing verified: same as Sonnet 4 ($3/$15 per MTok). Effort=max costs more due to more output tokens, not higher per-token rates.
7. Added token usage tracking to quantify cost difference between effort levels.
8. Rate limiting at 0.5s per call = ~60 seconds for 121 calls. Total runtime ~2 min per condition.
9. Budget cap $50 per agent (generous — expected cost is $25-50 depending on effort level).
10. The `output_config` parameter may not be available in older versions of the `anthropic` Python package. Add `pip install --upgrade anthropic` to prerequisites.
