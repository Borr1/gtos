#!/usr/bin/env python3
"""
T2c — Sonnet 4.6 effort=high experiment.
Tests whether effort=high on Sonnet 4.6 affects CANDIDATE rate and WR vs Sonnet 4 baseline.
Budget: $50. Model: claude-sonnet-4-6-20250514. Effort: high.
Author: Claude Code execution agent
Date: 2026-04-12
"""

import csv
import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ─── Configuration (one variable changes per agent) ──────────────────────────
EFFORT_LEVEL = 'high'        # This agent: high
MODEL_PRIMARY = 'claude-sonnet-4-6'
MODEL_FALLBACKS = ['claude-sonnet-4-6-latest']
BUDGET_CAP = 50.0

# ─── Constants ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
BATCH_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
T1_CSV = (BASE_DIR / 'research' / 'academic_pipeline'
          / 'data' / 'entry_engineering_dataset.csv')
DATA_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'data'
RESULTS_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'results'
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_COST_PER_TOK  = 3.0  / 1_000_000   # Sonnet 4.6 input:  $3/MTok
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000   # Sonnet 4.6 output: $15/MTok

# ─── API key check ────────────────────────────────────────────────────────────
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    print('API_KEY_UNAVAILABLE — set ANTHROPIC_API_KEY and retry.')
    sys.exit(1)

from anthropic import Anthropic
client = Anthropic()

# ─── Cost tracker ─────────────────────────────────────────────────────────────
cumulative_cost = 0.0
cost_log: list[dict] = []


def track_cost(trade_id: str, input_tokens: int, output_tokens: int) -> float:
    cost = input_tokens * INPUT_COST_PER_TOK + output_tokens * OUTPUT_COST_PER_TOK
    global cumulative_cost
    cumulative_cost += cost
    cost_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'trade_id': trade_id,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'call_cost': round(cost, 6),
        'cumulative_cost': round(cumulative_cost, 4),
    })
    return cost


# ─── Phase -1: Verify model ID and effort support ─────────────────────────────
print('\n=== Phase -1: Model verification ===')

working_model: str | None = None
for candidate_id in [MODEL_PRIMARY] + MODEL_FALLBACKS:
    try:
        test = client.messages.create(
            model=candidate_id,
            max_tokens=100,
            temperature=0,
            messages=[{'role': 'user', 'content': 'Reply with just the word "ready"'}],
            output_config={'effort': EFFORT_LEVEL},
        )
        working_model = candidate_id
        print(f'  Model check OK: {candidate_id} → "{test.content[0].text.strip()[:50]}"')
        break
    except Exception as exc:
        err_str = str(exc)[:200]
        print(f'  {candidate_id} FAILED: {err_str}')
        # If error is about output_config, not the model ID, stop trying
        if 'output_config' in err_str.lower() or 'effort' in err_str.lower():
            print('  output_config/effort parameter not accepted — '
                  'trying without it to confirm model availability...')
            try:
                test2 = client.messages.create(
                    model=candidate_id,
                    max_tokens=100,
                    temperature=0,
                    messages=[{'role': 'user', 'content': 'Reply with just the word "ready"'}],
                )
                print(f'  Model {candidate_id} works WITHOUT effort param. '
                      f'effort param is unsupported — will run without it '
                      f'and flag in report.')
                working_model = candidate_id + '_no_effort'
                break
            except Exception:
                pass

if not working_model:
    print('ERROR: No working model found. Exiting.')
    sys.exit(1)

USE_EFFORT = not working_model.endswith('_no_effort')
MODEL = working_model.replace('_no_effort', '')
print(f'  Using model: {MODEL}, effort={EFFORT_LEVEL}, USE_EFFORT={USE_EFFORT}')


# ─── API call helper ──────────────────────────────────────────────────────────
def evaluate_mso(system_prompt: str, user_message: str, trade_id: str = '') -> dict:
    """Call Sonnet 4.6 with effort parameter and return parsed JSON."""
    global cumulative_cost

    if cumulative_cost >= BUDGET_CAP:
        return {
            'decision': 'BUDGET_EXCEEDED',
            'error': f'Cumulative cost ${cumulative_cost:.2f} exceeds ${BUDGET_CAP} cap',
        }

    time.sleep(0.5)  # Rate limiting

    create_kwargs: dict = dict(
        model=MODEL,
        max_tokens=4096,
        temperature=0,
        system=system_prompt,
        messages=[{'role': 'user', 'content': user_message}],
    )
    if USE_EFFORT:
        create_kwargs['output_config'] = {'effort': EFFORT_LEVEL}

    try:
        response = client.messages.create(**create_kwargs)
    except Exception as exc:
        return {'decision': 'API_ERROR', 'error': str(exc)[:300]}

    usage = response.usage
    track_cost(trade_id, usage.input_tokens, usage.output_tokens)

    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text.strip())

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s = text.find('{')
        e_idx = text.rfind('}')
        if s >= 0 and e_idx > s:
            try:
                return json.loads(text[s:e_idx + 1])
            except Exception:
                pass
        return {'decision': 'PARSE_ERROR', 'raw': text[:500]}


# ─── Phase 0: Load data ───────────────────────────────────────────────────────
print('\n=== Phase 0: Loading batch data ===')

# Load all full_prompts files → keyed by candle_time
batch_by_ct: dict = {}
for fp_path in glob.glob(str(BATCH_DIR / '*_full_prompts.json')):
    with open(fp_path) as f:
        data = json.load(f)
    for item in data:
        ct = item.get('candle_time', '')
        if not ct:
            continue
        sys_list = item['prompt']['system']
        sys_text = sys_list[0]['text'] if isinstance(sys_list, list) else sys_list
        batch_by_ct[ct] = {
            'system_prompt': sys_text,
            'user_message': item['prompt']['user_message'],
        }

print(f'  Loaded {len(batch_by_ct)} batch entries from full_prompts files')

# Load all raw_results → keyed by candle_time (original Sonnet 4 decisions)
raw_by_ct: dict = {}
for rp_path in glob.glob(str(BATCH_DIR / '*_raw_results.json')):
    fp_path = rp_path.replace('_raw_results.json', '_full_prompts.json')
    if not os.path.exists(fp_path):
        continue
    with open(rp_path) as f:
        results = json.load(f)
    with open(fp_path) as f:
        fp_data = json.load(f)
    cid_to_ct = {item['custom_id']: item['candle_time'] for item in fp_data}
    for cid, v in results.items():
        ct = cid_to_ct.get(cid)
        if not ct:
            continue
        txt = v.get('text', '') or ''
        if not txt:
            continue
        try:
            raw_by_ct[ct] = json.loads(txt)
        except Exception:
            pass

print(f'  Loaded {len(raw_by_ct)} raw results')

# Load T1 dataset and match to batch
df_t1 = pd.read_csv(T1_CSV)
print(f'  T1 dataset: {len(df_t1)} trades')

selected_msos: list[dict] = []
for _, row in df_t1.iterrows():
    ct = row['candle_time']
    if ct not in batch_by_ct:
        continue
    outcome = str(row['outcome'])
    if outcome == 'BREAKEVEN':
        outcome = 'LOSS'
    batch = batch_by_ct[ct]
    raw = raw_by_ct.get(ct, {})
    r_mult = float(row['r_multiple']) if not pd.isna(row['r_multiple']) else 0.0
    selected_msos.append({
        'trade_id': str(row['trade_id']),
        'candle_time': ct,
        'symbol': str(row['symbol']),
        'kill_zone': str(row['kill_zone']),
        'outcome': outcome,
        'r_multiple': r_mult,
        'win': int(row['win']),
        'system_prompt': batch['system_prompt'],
        'user_message': batch['user_message'],
        # Note: All T1 trades were originally CANDIDATE (by construction — they resulted in
        # real trades). The raw_by_ct might not always have them if batch data is incomplete.
        'original_decision': raw.get('decision', 'CANDIDATE'),
        'original_confidence': raw.get('confidence_score', 80),
    })

n_matched = len(selected_msos)
print(f'  Matched {n_matched} MSOs to batch entries')
if n_matched < 100:
    print(f'  WARNING: Only {n_matched} matched — expected ~121. '
          f'Check candle_time format in batch vs T1.')


# ─── Phase 1: API evaluations ─────────────────────────────────────────────────
print(f'\n=== Phase 1: Running {n_matched} evaluations (effort={EFFORT_LEVEL}) ===')

results: list[dict] = []

for i, mso in enumerate(selected_msos):
    print(f'  [{i+1}/{n_matched}] {mso["trade_id"]} (${cumulative_cost:.2f})')

    api_result = evaluate_mso(
        mso['system_prompt'],
        mso['user_message'],
        trade_id=mso['trade_id'],
    )

    reasoning = api_result.get('reasoning', {})
    if isinstance(reasoning, str):
        reasoning = {}
    setup_grade = reasoning.get('setup_grade', '') if isinstance(reasoning, dict) else ''

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
        # New Sonnet 4.6 effort=high decision
        'new_decision': api_result.get('decision', 'PARSE_ERROR'),
        'new_confidence': api_result.get('confidence_score', 0),
        'new_setup_grade': setup_grade,
        'new_framework': api_result.get('framework', ''),
        # Full response for debugging
        'new_response': api_result,
    })

    if cumulative_cost >= BUDGET_CAP:
        print(f'  BUDGET CAP REACHED at ${cumulative_cost:.2f} — stopping.')
        break

print(f'\nCompleted {len(results)} evaluations. Total cost: ${cumulative_cost:.2f}')


# ─── Phase 2: Analysis ────────────────────────────────────────────────────────
print('\n=== Phase 2: Analysis ===')

df = pd.DataFrame(results)
n_total = len(df)

n_candidate = (df['new_decision'] == 'CANDIDATE').sum()
n_no_trade  = (df['new_decision'] == 'NO_TRADE').sum()
n_other     = n_total - n_candidate - n_no_trade

candidate_rate = n_candidate / n_total if n_total > 0 else 0.0

# WR among new CANDIDATEs
candidates = df[df['new_decision'] == 'CANDIDATE']
if len(candidates) > 0:
    wr = candidates['win'].mean()
    wr_n = len(candidates)
    avg_r = candidates['r_multiple'].mean()
    conf_mean = candidates['new_confidence'].mean()
    conf_std  = candidates['new_confidence'].std()
else:
    wr = float('nan')
    wr_n = 0
    avg_r = float('nan')
    conf_mean = conf_std = 0.0

cr_wr = candidate_rate * wr if not np.isnan(wr) else 0.0

# Original Sonnet 4 baseline
# All T1 trades were CANDIDATE by construction, but some raw_by_ct entries may differ
orig_candidate_rate = (df['original_decision'] == 'CANDIDATE').sum() / n_total
orig_candidates = df[df['original_decision'] == 'CANDIDATE']
orig_wr = orig_candidates['win'].mean() if len(orig_candidates) > 0 else float('nan')
orig_wr_n = len(orig_candidates)
orig_cr_wr = orig_candidate_rate * orig_wr if not np.isnan(orig_wr) else 0.0
orig_conf = orig_candidates['original_confidence'].mean() if len(orig_candidates) > 0 else 0.0

# Agreement analysis (McNemar's test — paired)
n_both_cand = int(((df['new_decision'] == 'CANDIDATE') &
                    (df['original_decision'] == 'CANDIDATE')).sum())
n_new_only  = int(((df['new_decision'] == 'CANDIDATE') &
                    (df['original_decision'] != 'CANDIDATE')).sum())
n_orig_only = int(((df['new_decision'] != 'CANDIDATE') &
                    (df['original_decision'] == 'CANDIDATE')).sum())
n_neither   = int(((df['new_decision'] != 'CANDIDATE') &
                    (df['original_decision'] != 'CANDIDATE')).sum())

agreement_rate = (n_both_cand + n_neither) / n_total if n_total > 0 else 0.0

b, c = n_new_only, n_orig_only
if b + c > 0:
    mcnemar_chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    mcnemar_p = float(1.0 - stats.chi2.cdf(mcnemar_chi2, df=1))
else:
    mcnemar_chi2 = 0.0
    mcnemar_p = 1.0

# Lost trades: Sonnet 4 said CANDIDATE, Sonnet 4.6 says NO_TRADE
lost_trades = df[(df['original_decision'] == 'CANDIDATE') &
                 (df['new_decision'] != 'CANDIDATE')]
lost_wr = lost_trades['win'].mean() if len(lost_trades) > 0 else float('nan')
lost_n  = len(lost_trades)

# Gained trades: Sonnet 4.6 says CANDIDATE, Sonnet 4 said NO_TRADE
gained_trades = df[(df['new_decision'] == 'CANDIDATE') &
                   (df['original_decision'] != 'CANDIDATE')]
gained_wr = gained_trades['win'].mean() if len(gained_trades) > 0 else float('nan')
gained_n  = len(gained_trades)

# Both CANDIDATE WR
both_cand = df[(df['new_decision'] == 'CANDIDATE') &
               (df['original_decision'] == 'CANDIDATE')]
both_wr = both_cand['win'].mean() if len(both_cand) > 0 else float('nan')

# Token usage
if cost_log:
    avg_input  = float(np.mean([c['input_tokens'] for c in cost_log]))
    avg_output = float(np.mean([c['output_tokens'] for c in cost_log]))
    avg_cost   = float(np.mean([c['call_cost'] for c in cost_log]))
else:
    avg_input = avg_output = avg_cost = 0.0

total_cost = cumulative_cost
monthly_cost = avg_cost * 17  # 17 trades/month expected

# Distributions
conf_dist = candidates['new_confidence'].value_counts().sort_index().to_dict() \
    if len(candidates) > 0 else {}
grade_dist = df['new_setup_grade'].value_counts().to_dict()
framework_dist = candidates['new_framework'].value_counts().to_dict() \
    if len(candidates) > 0 else {}

print(f'  CANDIDATE rate: {candidate_rate:.1%} ({n_candidate}/{n_total})')
print(f'  WR (new CANDIDATEs): {wr:.1%} (n={wr_n})' if not np.isnan(wr) else '  WR: nan')
print(f'  CR×WR: {cr_wr:.4f}')
print(f'  Agreement with baseline: {agreement_rate:.1%}')
print(f'  McNemar p: {mcnemar_p:.4f}')
print(f'  Lost trades: {lost_n} (WR={lost_wr:.1%})' if not np.isnan(lost_wr)
      else f'  Lost trades: {lost_n}')


# ─── Phase 3: Save outputs ────────────────────────────────────────────────────
print('\n=== Phase 3: Saving outputs ===')

# Serialize results (new_response may contain non-JSON-serializable types)
safe_rows = []
for r in results:
    row = dict(r)
    # Convert new_response to a serializable form
    nr = row.get('new_response', {})
    if isinstance(nr, dict):
        row['new_response'] = {
            k: str(v) if not isinstance(v, (str, int, float, bool, type(None), list, dict))
            else v
            for k, v in nr.items()
        }
    safe_rows.append(row)

output_data = {
    'metadata': {
        'model': MODEL,
        'model_primary': MODEL_PRIMARY,
        'effort_level': EFFORT_LEVEL,
        'use_effort_param': USE_EFFORT,
        'n_msos': n_total,
        'total_cost': round(total_cost, 4),
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'baseline_model': 'claude-sonnet-4-20250514',
        'temperature': 0,
    },
    'summary': {
        'candidate_rate': round(candidate_rate, 4),
        'wr': round(wr, 4) if not np.isnan(wr) else None,
        'cr_wr': round(cr_wr, 4),
        'n_candidate': int(n_candidate),
        'n_no_trade': int(n_no_trade),
        'n_other': int(n_other),
        'n_total': n_total,
        'orig_candidate_rate': round(orig_candidate_rate, 4),
        'orig_wr': round(orig_wr, 4) if not np.isnan(orig_wr) else None,
        'orig_cr_wr': round(orig_cr_wr, 4),
        'agreement_with_baseline': round(agreement_rate, 4),
        'mcnemar_chi2': round(mcnemar_chi2, 4),
        'mcnemar_p': round(mcnemar_p, 6),
        'n_both_cand': n_both_cand,
        'n_orig_only': n_orig_only,
        'n_new_only': n_new_only,
        'n_neither': n_neither,
        'lost_trades_n': lost_n,
        'lost_trades_wr': round(lost_wr, 4) if not np.isnan(lost_wr) else None,
        'gained_trades_n': gained_n,
        'gained_trades_wr': round(gained_wr, 4) if not np.isnan(gained_wr) else None,
        'avg_confidence': round(conf_mean, 1),
        'avg_r_multiple': round(avg_r, 4) if not np.isnan(avg_r) else None,
        'avg_input_tokens': round(avg_input, 0),
        'avg_output_tokens': round(avg_output, 0),
        'avg_cost_per_call': round(avg_cost, 6),
        'total_cost': round(total_cost, 4),
        'projected_monthly_cost': round(monthly_cost, 4),
    },
    'distributions': {
        'confidence': conf_dist,
        'setup_grade': grade_dist,
        'framework': framework_dist,
    },
    'rows': safe_rows,
}

out_json = DATA_DIR / f'T2c_{EFFORT_LEVEL}_results.json'
with open(out_json, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)
print(f'  Saved results JSON: {out_json}')

# Cost log CSV
out_cost = DATA_DIR / f'T2c_{EFFORT_LEVEL}_cost_log.csv'
if cost_log:
    with open(out_cost, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_log[0].keys()))
        writer.writeheader()
        writer.writerows(cost_log)
    print(f'  Saved cost log: {out_cost}')

# ─── Markdown report ──────────────────────────────────────────────────────────
def pct(v: float | None) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'n/a'
    return f'{v:.1%}'


def fmt_n(v: float | None, n: int = 4) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'n/a'
    return f'{v:.{n}f}'


# Build raw decision log table
decision_rows: list[str] = []
for r in results:
    decision_rows.append(
        f"| {r['trade_id'][:35]:<35} | {r['outcome']:<8} "
        f"| {r['original_decision']:<12} | {r['new_decision']:<12} "
        f"| {r.get('new_confidence',0):>3} | {r.get('new_setup_grade',''):>5} |"
    )
decision_table = '\n'.join(decision_rows)

# Confidence distribution string
conf_str = ', '.join([f'{k}:{v}' for k, v in sorted(conf_dist.items())]) \
    if conf_dist else 'n/a'
grade_str = ', '.join([f'{k}:{v}' for k, v in grade_dist.items()]) \
    if grade_dist else 'n/a'
framework_str = ', '.join([f'{k}:{v}' for k, v in framework_dist.items()]) \
    if framework_dist else 'n/a'

lost_interp: str
if not np.isnan(lost_wr) and lost_n > 0:
    if lost_wr > 0.65:
        lost_interp = (f'**OVER-REJECTING good trades** (WR={pct(lost_wr)} > 65%) '
                       f'— Opus-like behavior detected.')
    elif lost_wr < 0.50:
        lost_interp = (f'**CORRECTLY filtering losers** (WR={pct(lost_wr)} < 50%) '
                       f'— Sonnet 4.6 adds discriminatory value.')
    else:
        lost_interp = (f'**Random rejection** (WR={pct(lost_wr)}, 50-65%) '
                       f'— no discriminatory signal.')
else:
    lost_interp = 'n/a (no lost trades or no data)'

effort_note = ('' if USE_EFFORT
               else '\n> **NOTE:** `output_config` / `effort` parameter was not accepted '
                    'by the SDK version in use. Results are Sonnet 4.6 at default effort '
                    '(no effort param). Mark results accordingly.\n')

report = f"""# T2c Model Shootout: Sonnet 4.6 effort={EFFORT_LEVEL}

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Model:** {MODEL}
**Effort:** {EFFORT_LEVEL} (USE_EFFORT={USE_EFFORT})
**Baseline:** claude-sonnet-4-20250514 (Sonnet 4, no effort param)
**N MSOs:** {n_total}
**Total cost:** ${total_cost:.4f}
{effort_note}
---

## Results

| Metric | Sonnet 4 (baseline) | Sonnet 4.6 effort={EFFORT_LEVEL} |
|--------|--------------------|---------------------------------|
| CANDIDATE rate | {pct(orig_candidate_rate)} (n={orig_wr_n}) | {pct(candidate_rate)} (n={n_candidate}) |
| WR (of CANDIDATEs) | {pct(orig_wr)} | {pct(wr)} (n={wr_n}) |
| CR × WR | {fmt_n(orig_cr_wr)} | {fmt_n(cr_wr)} |
| Avg confidence | {orig_conf:.1f} | {conf_mean:.1f} |
| Avg output tokens | ~500 | {avg_output:.0f} |
| Cost per call | ~$0.02 | ${avg_cost:.4f} |
| Projected monthly (17 trades) | ~$0.34 | ${monthly_cost:.4f} |

---

## Agreement Analysis

| Category | N | WR |
|----------|---|-----|
| Both CANDIDATE | {n_both_cand} | {pct(both_wr)} |
| Sonnet 4.6 only (gained) | {gained_n} | {pct(gained_wr)} |
| Sonnet 4 only (lost) | {lost_n} | {pct(lost_wr)} |
| Neither | {n_neither} | — |
| **Agreement rate** | **{agreement_rate:.1%}** | — |
| McNemar χ²={mcnemar_chi2:.3f} p={mcnemar_p:.4f} | {'sig' if mcnemar_p < 0.05 else 'n/s'} | — |

---

## Lost Trades Analysis

Sonnet 4.6 rejected **{lost_n}** trades that Sonnet 4 accepted.
- WR of rejected trades: {pct(lost_wr)}
- Interpretation: {lost_interp}

> Rule of thumb:
> - WR > 65% → over-rejecting (Opus-like, bad)
> - WR < 50% → filtering correctly (good)
> - WR 50-65% → random noise (neutral)

---

## Framework Distribution (Sonnet 4.6 CANDIDATEs)

{', '.join([f'{k}: {v}' for k, v in framework_dist.items()]) if framework_dist else 'n/a'}

---

## Grade Distribution

{grade_str}

---

## Confidence Distribution (CANDIDATEs only)

{conf_str}

---

## Token Usage

| Metric | Value |
|--------|-------|
| Avg input tokens | {avg_input:.0f} |
| Avg output tokens | {avg_output:.0f} |
| Avg cost per call | ${avg_cost:.5f} |
| Total cost | ${total_cost:.4f} |
| Projected monthly (17 trades/month) | ${monthly_cost:.4f} |

---

## Decision Breakdown

| Decision | N | % |
|----------|---|---|
| CANDIDATE | {n_candidate} | {pct(n_candidate/n_total if n_total else 0)} |
| NO_TRADE  | {n_no_trade}  | {pct(n_no_trade/n_total if n_total else 0)} |
| Other (errors, WAIT, etc.) | {n_other} | {pct(n_other/n_total if n_total else 0)} |

---

## Raw Decision Log

| trade_id | outcome | orig_decision | new_decision | conf | grade |
|----------|---------|---------------|--------------|------|-------|
{decision_table}
"""

out_report = RESULTS_DIR / f'T2c_{EFFORT_LEVEL}_results_v1.md'
with open(out_report, 'w') as f:
    f.write(report)
print(f'  Saved report: {out_report}')

print('\n=== DONE ===')
print(f'  Model: {MODEL} (effort={EFFORT_LEVEL}, use_effort={USE_EFFORT})')
print(f'  N evaluated: {n_total}')
print(f'  CANDIDATE rate: {pct(candidate_rate)} ({n_candidate}/{n_total})')
print(f'  WR: {pct(wr)} (n={wr_n})')
print(f'  CR×WR: {fmt_n(cr_wr)}')
print(f'  Total cost: ${total_cost:.4f}')
print(f'  Results: {out_json}')
print(f'  Report:  {out_report}')
