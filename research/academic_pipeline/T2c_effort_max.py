#!/usr/bin/env python3
"""
T2c — Sonnet 4.6 Model + Effort Level Shootout: effort=max
Tests whether Sonnet 4.6 at effort=max produces a different CANDIDATE rate or WR
than the Sonnet 4 baseline on the same 121 MSOs.
Budget: $50 cap.
Author: Claude Code execution agent
Date: 2026-04-12
"""

import csv
import glob
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
BATCH_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
T1_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'

EFFORT_LEVEL = 'max'
MODEL_PRIMARY = 'claude-sonnet-4-6'
MODEL_FALLBACKS = ['claude-sonnet-4-6-latest']
BUDGET_CAP = 50.0
RATE_LIMIT_SLEEP = 0.5
INPUT_COST_PER_TOK = 3.0 / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

OUT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'data'
OUT_RESULTS = OUT_DIR / f'T2c_{EFFORT_LEVEL}_results.json'
OUT_COST = OUT_DIR / f'T2c_{EFFORT_LEVEL}_cost_log.csv'
OUT_REPORT = BASE_DIR / 'research' / 'academic_pipeline' / 'results' / f'T2c_{EFFORT_LEVEL}_results_v1.md'

assert EFFORT_LEVEL in ('medium', 'high', 'max'), f"Invalid effort: {EFFORT_LEVEL}"

# ─── API setup ────────────────────────────────────────────────────────────────
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    print('API_KEY_UNAVAILABLE — set ANTHROPIC_API_KEY and retry.')
    sys.exit(1)

from anthropic import Anthropic
client = Anthropic()

# ─── Cost tracker ─────────────────────────────────────────────────────────────
cumulative_cost = 0.0
cost_log = []
working_model = MODEL_PRIMARY


def track_cost(trade_id: str, input_tokens: int, output_tokens: int) -> float:
    global cumulative_cost
    cost = input_tokens * INPUT_COST_PER_TOK + output_tokens * OUTPUT_COST_PER_TOK
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


# ─── Model verification ───────────────────────────────────────────────────────
print('\n=== Model Verification ===')
verified = False
for candidate_model in [MODEL_PRIMARY] + MODEL_FALLBACKS:
    try:
        test = client.messages.create(
            model=candidate_model,
            max_tokens=100,
            temperature=0,
            messages=[{'role': 'user', 'content': 'Reply with just the word "ready"'}],
            output_config={'effort': EFFORT_LEVEL},
        )
        print(f'  Model check OK: {candidate_model} → "{test.content[0].text.strip()}"')
        working_model = candidate_model
        verified = True
        break
    except Exception as e:
        print(f'  Model check FAILED for {candidate_model}: {e}')

if not verified:
    print('ERROR: No working model found. Exiting.')
    sys.exit(1)

print(f'  Using model: {working_model} with effort={EFFORT_LEVEL}')


# ─── API call helper ──────────────────────────────────────────────────────────
def evaluate_mso(system_prompt: str, user_message: str, trade_id: str = '') -> dict:
    """Call Sonnet 4.6 with effort parameter and return parsed JSON."""
    global cumulative_cost

    if cumulative_cost >= BUDGET_CAP:
        return {'decision': 'BUDGET_EXCEEDED',
                'error': f'Cumulative cost ${cumulative_cost:.2f} exceeds ${BUDGET_CAP} cap'}

    time.sleep(RATE_LIMIT_SLEEP)

    try:
        response = client.messages.create(
            model=working_model,
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
            output_config={'effort': EFFORT_LEVEL},
        )
    except Exception as e:
        return {'decision': 'API_ERROR', 'error': str(e)[:300]}

    usage = response.usage
    track_cost(trade_id, usage.input_tokens, usage.output_tokens)

    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = text.split('```json')[-1].split('```')[0].strip()
        if not text:
            text = response.content[0].text.strip()
            s = text.find('{')
            e = text.rfind('}')
            if s >= 0 and e > s:
                text = text[s:e+1]

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


# ─── Phase 0: Load data ───────────────────────────────────────────────────────
print('\n=== Phase 0: Loading batch data ===')

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
            'kill_zone': item.get('kill_zone') or '',
            'date': ct[:10],
            'custom_id': item.get('custom_id', ''),
            'candle_time': ct,
        }

print(f'  Loaded {len(batch_by_ct)} batch entries from full_prompts files')

# Load raw results (original Sonnet 4 decisions)
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

print(f'  Loaded {len(raw_by_ct)} raw results (Sonnet 4 baseline decisions)')

# Load T1 dataset and match
df_t1 = pd.read_csv(T1_CSV)
print(f'  T1 dataset: {len(df_t1)} trades')

selected_msos: list = []
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
        'date': str(row.get('date', ct[:10])),
        'kill_zone': str(row['kill_zone']),
        'symbol': str(row['symbol']),
        'outcome': outcome,
        'r_multiple': r_mult,
        'win': int(row['win']),
        'system_prompt': batch['system_prompt'],
        'user_message': batch['user_message'],
        'original_decision': raw.get('decision', 'CANDIDATE'),
        'original_confidence': raw.get('confidence_score', 80),
    })

print(f'  Matched {len(selected_msos)} MSOs to batch entries')
if len(selected_msos) < 100:
    print(f'  WARNING: Only {len(selected_msos)} matched — expected ~121. Check batch data coverage.')


# ─── Phase 1: API Evaluations ─────────────────────────────────────────────────
print(f'\n=== Phase 1: Running {len(selected_msos)} evaluations at effort={EFFORT_LEVEL} ===')
print(f'  Budget cap: ${BUDGET_CAP:.2f}')

results = []
for i, mso in enumerate(selected_msos):
    print(f'  [{i+1}/{len(selected_msos)}] {mso["trade_id"]} (${cumulative_cost:.4f})', flush=True)

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
        'original_decision': mso['original_decision'],
        'original_confidence': mso['original_confidence'],
        'new_decision': result.get('decision', 'PARSE_ERROR'),
        'new_confidence': result.get('confidence_score', 0),
        'new_setup_grade': result.get('reasoning', {}).get('setup_grade', '') if isinstance(result.get('reasoning'), dict) else '',
        'new_framework': result.get('framework', ''),
        'new_response': result,
    })

    if cumulative_cost >= BUDGET_CAP:
        print(f'  BUDGET CAP REACHED at ${cumulative_cost:.2f}')
        break

print(f'\nCompleted {len(results)} evaluations. Total cost: ${cumulative_cost:.4f}')


# ─── Phase 2: Analysis ────────────────────────────────────────────────────────
print('\n=== Phase 2: Analysis ===')

df = pd.DataFrame(results)

n_total = len(df)
n_candidate = int((df['new_decision'] == 'CANDIDATE').sum())
n_no_trade = int((df['new_decision'] == 'NO_TRADE').sum())
n_other = n_total - n_candidate - n_no_trade

candidate_rate = n_candidate / n_total if n_total > 0 else 0.0

# WR among CANDIDATEs
candidates = df[df['new_decision'] == 'CANDIDATE']
if len(candidates) > 0:
    wr = float(candidates['win'].mean())
    wr_n = len(candidates)
else:
    wr = float('nan')
    wr_n = 0

cr_wr = candidate_rate * wr if not np.isnan(wr) else 0.0

# Sonnet 4 baseline — all 121 trades are CANDIDATEs by construction
orig_candidate_rate = 1.0  # by construction
orig_candidates = df  # all are Sonnet 4 CANDIDATEs
orig_wr = float(orig_candidates['win'].mean()) if len(orig_candidates) > 0 else float('nan')
orig_wr_n = len(orig_candidates)
orig_cr_wr = orig_candidate_rate * orig_wr if not np.isnan(orig_wr) else 0.0
orig_conf = float(df['original_confidence'].mean())

# McNemar's test (paired: same MSOs, different models)
# Since all original decisions are CANDIDATE (by construction), new_only = n_no_trade
n_both_cand = n_candidate          # new=CAND, orig=CAND (orig always CAND)
n_new_only = 0                     # new=CAND but orig=NO_TRADE — impossible (orig always CAND)
n_orig_only = n_no_trade + n_other  # new=NO_TRADE but orig=CAND
n_neither = 0                      # impossible

b, c = n_new_only, n_orig_only     # b=0, c=rejected by Sonnet 4.6
if b + c > 0:
    mcnemar_chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    mcnemar_p = float(1 - stats.chi2.cdf(mcnemar_chi2, df=1))
else:
    mcnemar_chi2 = 0.0
    mcnemar_p = 1.0

# Agreement rate
agreement_rate = float((df['new_decision'] == 'CANDIDATE').mean())  # same as candidate_rate here

# Lost trades: Sonnet 4 said CAND, Sonnet 4.6 says NOT CAND
lost_trades = df[df['new_decision'] != 'CANDIDATE']
lost_wr = float(lost_trades['win'].mean()) if len(lost_trades) > 0 else float('nan')

# Confidence distribution
if len(candidates) > 0:
    conf_mean = float(candidates['new_confidence'].mean())
    conf_std = float(candidates['new_confidence'].std())
    conf_dist = candidates['new_confidence'].value_counts().sort_index().to_dict()
else:
    conf_mean = conf_std = 0.0
    conf_dist = {}

# Grade and framework
grade_dist = df['new_setup_grade'].value_counts().to_dict()
framework_dist = candidates['new_framework'].value_counts().to_dict() if len(candidates) > 0 else {}

# Token usage
if cost_log:
    avg_input = float(np.mean([c['input_tokens'] for c in cost_log]))
    avg_output = float(np.mean([c['output_tokens'] for c in cost_log]))
    avg_cost_per_call = float(np.mean([c['call_cost'] for c in cost_log]))
else:
    avg_input = avg_output = avg_cost_per_call = 0.0

# WR of lost trades interpretation
if not np.isnan(lost_wr):
    if lost_wr > 0.65:
        lost_verdict = f'OVER-REJECTING: {lost_wr:.1%} WR on rejected trades > 65% — removing good trades (Opus-like behavior)'
    elif lost_wr < 0.50:
        lost_verdict = f'BETTER FILTER: {lost_wr:.1%} WR on rejected trades < 50% — correctly filtering losers'
    else:
        lost_verdict = f'RANDOM REJECTION: {lost_wr:.1%} WR on rejected trades (50-65%) — no discriminatory value'
else:
    lost_verdict = 'N/A (no rejections)'

print(f'  CANDIDATE rate: {candidate_rate:.1%} ({n_candidate}/{n_total})')
print(f'  WR of CANDIDATEs: {wr:.1%} (n={wr_n})' if not np.isnan(wr) else '  WR: N/A')
print(f'  CR × WR: {cr_wr:.4f}')
print(f'  McNemar p: {mcnemar_p:.6f}')
print(f'  Lost trades: {len(lost_trades)} — {lost_verdict}')
print(f'  Avg output tokens: {avg_output:.0f}')


# ─── Phase 3: Save outputs ────────────────────────────────────────────────────
print('\n=== Phase 3: Saving outputs ===')

OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

# 3.1 JSON results
output_data = {
    'metadata': {
        'model': working_model,
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
        'n_candidate': n_candidate,
        'n_no_trade': n_no_trade,
        'n_other': n_other,
        'agreement_with_baseline': round(agreement_rate, 4),
        'mcnemar_p': round(mcnemar_p, 6),
        'lost_trades_n': len(lost_trades),
        'lost_trades_wr': round(lost_wr, 4) if not np.isnan(lost_wr) else None,
        'avg_confidence': round(conf_mean, 1),
        'avg_input_tokens': round(avg_input, 0),
        'avg_output_tokens': round(avg_output, 0),
        'orig_wr': round(orig_wr, 4) if not np.isnan(orig_wr) else None,
        'orig_cr_wr': round(orig_cr_wr, 4),
        'orig_conf': round(orig_conf, 1),
    },
    'rows': results,
}

with open(OUT_RESULTS, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)
print(f'  Saved: {OUT_RESULTS}')

# 3.2 Cost log
if cost_log:
    with open(OUT_COST, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_log[0].keys()))
        writer.writeheader()
        writer.writerows(cost_log)
    print(f'  Saved: {OUT_COST}')

# 3.3 Report
monthly_cost = round(17 * avg_cost_per_call, 2) if avg_cost_per_call > 0 else 0.0

# Build raw decision table
decision_rows = []
for r in results:
    decision_rows.append(
        f"| {r['trade_id']} | {r['outcome']} | {r['original_decision']} | "
        f"{r['new_decision']} | {r['new_confidence']} | {r['new_setup_grade'] or '-'} |"
    )
decision_table = '\n'.join(decision_rows)

grade_lines = '\n'.join(f'- {k}: {v}' for k, v in sorted(grade_dist.items()))
framework_lines = '\n'.join(f'- {k}: {v}' for k, v in sorted(framework_dist.items()))
conf_lines = '\n'.join(f'- {k}: {v}' for k, v in sorted(conf_dist.items()))

report = f"""# T2c Model Shootout: Sonnet 4.6 effort={EFFORT_LEVEL}

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Model:** {working_model}
**Effort:** {EFFORT_LEVEL}
**Baseline:** claude-sonnet-4-20250514 (Sonnet 4, no effort param)
**N MSOs:** {n_total}
**Total cost:** ${cumulative_cost:.4f}

## Results

| Metric | Sonnet 4 (baseline) | Sonnet 4.6 effort={EFFORT_LEVEL} |
|--------|--------------------|---------------------------------|
| CANDIDATE rate | 100% (by construction) | {candidate_rate:.1%} |
| WR (of CANDIDATEs) | {orig_wr:.1%} (n={orig_wr_n}) | {f'{wr:.1%} (n={wr_n})' if not np.isnan(wr) else 'N/A'} |
| CR × WR | {orig_cr_wr:.4f} | {cr_wr:.4f} |
| Avg confidence | {orig_conf:.1f} | {conf_mean:.1f} |
| Avg output tokens | ~500 | {avg_output:.0f} |
| Cost per call | ~$0.02 | ${avg_cost_per_call:.4f} |

## Agreement Analysis

| Category | N | WR |
|----------|---|-----|
| Both CANDIDATE | {n_both_cand} | {f'{float(candidates["win"].mean()):.1%}' if len(candidates) > 0 else 'N/A'} |
| Sonnet 4.6 rejects (lost trades) | {len(lost_trades)} | {f'{lost_wr:.1%}' if not np.isnan(lost_wr) else 'N/A'} |

## Lost Trades Analysis

Sonnet 4.6 rejected {len(lost_trades)} trades that Sonnet 4 accepted.
- WR of rejected trades: {f'{lost_wr:.1%}' if not np.isnan(lost_wr) else 'N/A'}
- **Verdict:** {lost_verdict}
- McNemar's test p={mcnemar_p:.6f} — {'statistically significant shift in CANDIDATE rate' if mcnemar_p < 0.05 else 'no statistically significant difference from baseline'}

## Framework Distribution (Sonnet 4.6 CANDIDATEs)

{framework_lines if framework_lines else '(none)'}

## Grade Distribution

{grade_lines if grade_lines else '(none)'}

## Confidence Distribution

{conf_lines if conf_lines else '(none)'}

## Token Usage

- Avg input tokens: {avg_input:.0f}
- Avg output tokens: {avg_output:.0f}
- Total cost: ${cumulative_cost:.4f}
- Projected monthly cost at 17 trades/month: ${monthly_cost:.2f}

## Raw Decision Log

| trade_id | outcome | original_decision | new_decision | new_confidence | new_grade |
|----------|---------|------------------|--------------|----------------|-----------|
{decision_table}
"""

with open(OUT_REPORT, 'w') as f:
    f.write(report)
print(f'  Saved: {OUT_REPORT}')

print(f'\n=== DONE ===')
print(f'Model: {working_model}')
print(f'Effort: {EFFORT_LEVEL}')
print(f'N evaluated: {len(results)}')
print(f'CANDIDATE rate: {candidate_rate:.1%}')
print(f'WR: {wr:.1%} (n={wr_n})' if not np.isnan(wr) else 'WR: N/A')
print(f'CR×WR: {cr_wr:.4f}')
print(f'Total cost: ${cumulative_cost:.4f}')
print(f'Lost trades verdict: {lost_verdict}')
