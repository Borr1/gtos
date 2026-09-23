#!/usr/bin/env python3
"""
T2c — Sonnet 4.6 Model + Effort Level Shootout: effort=medium
Tests whether Sonnet 4.6 at medium effort produces different CANDIDATE rate or WR
compared to Sonnet 4 (no effort param) on the same 121 trades.

Model: claude-sonnet-4-6 (verified working; claude-sonnet-4-6-20250514 returns 404)
Effort: medium
Budget: $50 cap
Date: 2026-04-12
"""

import csv
import glob
import json
import os
import re
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

EFFORT_LEVEL = 'medium'
MODEL = 'claude-sonnet-4-6'        # verified working; versioned ID returns 404
BUDGET_CAP = 50.0
RATE_LIMIT_SLEEP = 0.5

INPUT_COST_PER_TOK = 3.0 / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

OUT_JSON = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / f'T2c_{EFFORT_LEVEL}_results.json'
OUT_COST = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / f'T2c_{EFFORT_LEVEL}_cost_log.csv'
OUT_REPORT = BASE_DIR / 'research' / 'academic_pipeline' / 'results' / f'T2c_{EFFORT_LEVEL}_results_v1.md'

assert EFFORT_LEVEL in ('medium', 'high', 'max'), f"Invalid effort: {EFFORT_LEVEL}"

# ─── API key check ────────────────────────────────────────────────────────────
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    print('API_KEY_UNAVAILABLE — set ANTHROPIC_API_KEY and retry.')
    sys.exit(1)

from anthropic import Anthropic
client = Anthropic()

# ─── Model verification ───────────────────────────────────────────────────────
print(f'\n=== T2c Sonnet 4.6 effort={EFFORT_LEVEL} ===')
print(f'Verifying model: {MODEL}')
try:
    test = client.messages.create(
        model=MODEL,
        max_tokens=20,
        temperature=0,
        messages=[{'role': 'user', 'content': 'Reply with just the word "ready"'}],
        output_config={'effort': EFFORT_LEVEL},
    )
    print(f'  Model check OK: {test.content[0].text.strip()[:40]}')
except Exception as e:
    print(f'  Model check FAILED: {e}')
    sys.exit(1)

# ─── Cost tracker ─────────────────────────────────────────────────────────────
cumulative_cost = 0.0
cost_log = []


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
            model=MODEL,
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
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        s = text.find('{')
        e = text.rfind('}')
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e + 1])
            except Exception:
                pass
        return {'decision': 'PARSE_ERROR', 'raw': text[:500]}


# ─── Phase 0: Load data ───────────────────────────────────────────────────────
print('\n=== Phase 0: Loading batch data ===')

# Load all full_prompts files
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

# Load raw_results — keyed by candle_time (original Sonnet 4 decisions)
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
        'date': str(row['date']),
        'kill_zone': str(row['kill_zone']),
        'symbol': str(row['symbol']),
        'outcome': outcome,
        'r_multiple': r_mult,
        'win': int(row['win']),
        'system_prompt': batch['system_prompt'],
        'user_message': batch['user_message'],
        # All 121 T1 trades are CANDIDATE by construction — this is the baseline
        'original_decision': raw.get('decision', 'CANDIDATE'),
        'original_confidence': raw.get('confidence_score', 80),
    })

print(f'  Matched {len(selected_msos)} T1 trades to batch entries')
if len(selected_msos) < 100:
    print(f'  WARNING: fewer than 100 matched — check batch data coverage')


# ─── Phase 1: API Evaluation ──────────────────────────────────────────────────
print(f'\n=== Phase 1: Evaluating {len(selected_msos)} MSOs with effort={EFFORT_LEVEL} ===')

results = []

for i, mso in enumerate(selected_msos):
    print(f"  [{i+1}/{len(selected_msos)}] {mso['trade_id']} (${cumulative_cost:.2f})", flush=True)

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
        print(f"  BUDGET CAP REACHED at ${cumulative_cost:.2f}")
        break

print(f'\nCompleted {len(results)} evaluations. Total cost: ${cumulative_cost:.2f}')


# ─── Phase 2: Analysis ────────────────────────────────────────────────────────
print('\n=== Phase 2: Analysis ===')

df = pd.DataFrame(results)

n_total = len(df)
n_candidate = int((df['new_decision'] == 'CANDIDATE').sum())
n_no_trade = int((df['new_decision'] == 'NO_TRADE').sum())
n_other = n_total - n_candidate - n_no_trade

candidate_rate = n_candidate / n_total

# WR among CANDIDATEs
candidates = df[df['new_decision'] == 'CANDIDATE']
if len(candidates) > 0:
    wr = float(candidates['win'].mean())
    wr_n = len(candidates)
else:
    wr = float('nan')
    wr_n = 0

cr_wr = candidate_rate * wr if not np.isnan(wr) else 0.0

# Original Sonnet 4 baseline
# All 121 T1 trades are CANDIDATE by construction → orig CANDIDATE rate = 100%
orig_candidate_rate = 1.0  # by construction of T1 dataset
orig_wr = float(df['win'].mean())  # WR of full population
orig_wr_n = n_total
orig_cr_wr = orig_candidate_rate * orig_wr  # = orig_wr since rate=1.0

# McNemar's test: new_decision vs original (all CANDIDATE)
# b = Sonnet 4.6 says CANDIDATE, original says NO_TRADE → impossible (all orig = CANDIDATE)
# c = Sonnet 4.6 says NO_TRADE, original says CANDIDATE → the "lost trades"
# So: b=0, c=n_no_trade+n_other, a=n_candidate, d=0
b = n_candidate   # new=CANDIDATE, orig=CANDIDATE (agreement)
c = n_no_trade + n_other  # new!=CANDIDATE, orig=CANDIDATE (disagreement)
# McNemar only uses discordant pairs b_disc (orig=CANDIDATE, new=NO_TRADE) vs c_disc (orig=NO_TRADE, new=CANDIDATE)
# Since all orig are CANDIDATE: b_disc=0, c_disc=n_no_trade+n_other
b_disc = 0
c_disc = n_no_trade + n_other
if b_disc + c_disc > 0:
    mcnemar_chi2 = (abs(b_disc - c_disc) - 1) ** 2 / (b_disc + c_disc)
    mcnemar_p = float(1 - stats.chi2.cdf(mcnemar_chi2, df=1))
else:
    mcnemar_chi2 = 0.0
    mcnemar_p = 1.0

# Agreement analysis
agreement_rate = float((df['new_decision'] == 'CANDIDATE').mean())  # = candidate_rate since all orig=CANDIDATE

# Lost trades: originally CANDIDATE (all), now not CANDIDATE
lost_trades = df[df['new_decision'] != 'CANDIDATE']
lost_wr = float(lost_trades['win'].mean()) if len(lost_trades) > 0 else float('nan')
lost_n = len(lost_trades)

# Both CANDIDATE (agreement)
both_candidate = df[df['new_decision'] == 'CANDIDATE']
both_wr = float(both_candidate['win'].mean()) if len(both_candidate) > 0 else float('nan')

# Confidence distribution
if len(candidates) > 0:
    conf_mean = float(candidates['new_confidence'].mean())
    conf_std = float(candidates['new_confidence'].std())
    conf_dist = candidates['new_confidence'].value_counts().sort_index().to_dict()
else:
    conf_mean = conf_std = 0.0
    conf_dist = {}

grade_dist = df['new_setup_grade'].value_counts().to_dict()
framework_dist = candidates['new_framework'].value_counts().to_dict() if len(candidates) > 0 else {}

# Token usage
if cost_log:
    avg_input = float(np.mean([c['input_tokens'] for c in cost_log]))
    avg_output = float(np.mean([c['output_tokens'] for c in cost_log]))
    avg_cost_per_call = float(np.mean([c['call_cost'] for c in cost_log]))
else:
    avg_input = avg_output = avg_cost_per_call = 0.0

print(f'  N total: {n_total}')
print(f'  CANDIDATE: {n_candidate} ({candidate_rate:.1%})')
print(f'  NO_TRADE: {n_no_trade}')
print(f'  Other (errors): {n_other}')
print(f'  WR (of CANDIDATEs): {wr:.1%} (n={wr_n})')
print(f'  CR × WR: {cr_wr:.4f}')
print(f'  Lost trades (rejected): {lost_n}, WR: {lost_wr:.1%}' if not np.isnan(lost_wr) else f'  Lost trades: {lost_n}')
print(f'  McNemar p: {mcnemar_p:.6f}')
print(f'  Avg input tokens: {avg_input:.0f}')
print(f'  Avg output tokens: {avg_output:.0f}')
print(f'  Total cost: ${cumulative_cost:.4f}')


# ─── Phase 3: Output ──────────────────────────────────────────────────────────
print('\n=== Phase 3: Saving outputs ===')

# Save JSON results
output_data = {
    'metadata': {
        'model': MODEL,
        'effort_level': EFFORT_LEVEL,
        'n_msos': len(results),
        'total_cost': round(cumulative_cost, 4),
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'baseline_model': 'claude-sonnet-4-20250514',
        'note': 'model claude-sonnet-4-6-20250514 returned 404; used claude-sonnet-4-6 alias',
    },
    'summary': {
        'candidate_rate': round(candidate_rate, 4),
        'wr': round(wr, 4) if not np.isnan(wr) else None,
        'cr_wr': round(cr_wr, 4),
        'n_candidate': n_candidate,
        'n_no_trade': n_no_trade,
        'n_other': n_other,
        'n_total': n_total,
        'orig_candidate_rate': orig_candidate_rate,
        'orig_wr': round(orig_wr, 4),
        'orig_cr_wr': round(orig_cr_wr, 4),
        'agreement_with_baseline': round(agreement_rate, 4),
        'mcnemar_p': round(mcnemar_p, 6),
        'lost_trades_n': lost_n,
        'lost_trades_wr': round(lost_wr, 4) if not np.isnan(lost_wr) else None,
        'both_candidate_n': int(len(both_candidate)),
        'both_candidate_wr': round(both_wr, 4) if not np.isnan(both_wr) else None,
        'avg_confidence': round(conf_mean, 1),
        'conf_std': round(conf_std, 1),
        'avg_input_tokens': round(avg_input, 0),
        'avg_output_tokens': round(avg_output, 0),
        'avg_cost_per_call': round(avg_cost_per_call, 6),
        'total_cost': round(cumulative_cost, 4),
    },
    'distributions': {
        'confidence': conf_dist,
        'grade': grade_dist,
        'framework': framework_dist,
    },
    'rows': results,
}

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_JSON, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)
print(f'  Saved: {OUT_JSON}')

# Save cost log
if cost_log:
    OUT_COST.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_COST, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_log[0].keys()))
        writer.writeheader()
        writer.writerows(cost_log)
    print(f'  Saved: {OUT_COST}')

# Build raw decision log table
decision_rows = []
for r in results:
    decision_rows.append(
        f"| {r['trade_id'][:30]} | {r['outcome']} | CANDIDATE | {r['new_decision']} "
        f"| {r['new_confidence']} | {r['new_setup_grade'] or '-'} |"
    )

# Compute monthly projection
monthly_cost = avg_cost_per_call * 17  # 17 trades/month estimate

# Write report
report_lines = [
    f"# T2c Model Shootout: Sonnet 4.6 effort={EFFORT_LEVEL}",
    f"",
    f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}  ",
    f"**Model:** {MODEL}  ",
    f"**Effort:** {EFFORT_LEVEL}  ",
    f"**Baseline:** claude-sonnet-4-20250514 (Sonnet 4, no effort param)  ",
    f"**N MSOs:** {n_total}  ",
    f"**Total cost:** ${cumulative_cost:.4f}  ",
    f"**Note:** claude-sonnet-4-6-20250514 returned 404; used claude-sonnet-4-6 alias  ",
    f"",
    f"## Results",
    f"",
    f"| Metric | Sonnet 4 (baseline) | Sonnet 4.6 effort={EFFORT_LEVEL} |",
    f"|--------|--------------------|---------------------------------|",
    f"| CANDIDATE rate | 100% (by construction) | {candidate_rate:.1%} |",
    f"| WR (of CANDIDATEs) | {orig_wr:.1%} (n={orig_wr_n}) | {wr:.1%} (n={wr_n}) |" if not np.isnan(wr) else f"| WR (of CANDIDATEs) | {orig_wr:.1%} (n={orig_wr_n}) | N/A (0 candidates) |",
    f"| CR × WR | {orig_cr_wr:.4f} | {cr_wr:.4f} |",
    f"| Avg confidence | 80 (rubber stamp) | {conf_mean:.1f} |",
    f"| Avg output tokens | ~500 | {avg_output:.0f} |",
    f"| Cost per call | ~$0.02 | ${avg_cost_per_call:.4f} |",
    f"",
    f"## Agreement Analysis",
    f"",
    f"| Category | N | WR |",
    f"|----------|---|-----|",
    f"| Both CANDIDATE (agreement) | {len(both_candidate)} | {both_wr:.1%} |" if not np.isnan(both_wr) else f"| Both CANDIDATE | 0 | N/A |",
    f"| Sonnet 4.6 rejects (lost trades) | {lost_n} | {lost_wr:.1%} |" if not np.isnan(lost_wr) else f"| Sonnet 4.6 rejects (lost trades) | {lost_n} | N/A |",
    f"",
    f"## Lost Trades Analysis",
    f"",
    f"Sonnet 4.6 rejected {lost_n} trades that Sonnet 4 accepted.",
]
if not np.isnan(lost_wr):
    report_lines.append(f"- WR of rejected trades: {lost_wr:.1%}")
    if lost_wr > 0.65:
        report_lines.append("- **VERDICT: OVER-REJECTING** — Sonnet 4.6 removes good trades (Opus-like behavior)")
    elif lost_wr < 0.50:
        report_lines.append("- **VERDICT: CORRECT FILTERING** — Sonnet 4.6 removes more losers than winners")
    else:
        report_lines.append("- **VERDICT: RANDOM REJECTION** — Sonnet 4.6 rejects randomly (no discriminatory value)")

report_lines += [
    f"",
    f"## Framework Distribution (Sonnet 4.6 CANDIDATEs)",
    f"",
    f"```",
    f"{json.dumps(framework_dist, indent=2)}",
    f"```",
    f"",
    f"## Grade Distribution",
    f"",
    f"```",
    f"{json.dumps(grade_dist, indent=2)}",
    f"```",
    f"",
    f"## Confidence Distribution",
    f"",
    f"```",
    f"{json.dumps({str(k): v for k, v in conf_dist.items()}, indent=2)}",
    f"```",
    f"",
    f"## Token Usage",
    f"",
    f"- Avg input tokens: {avg_input:.0f}",
    f"- Avg output tokens: {avg_output:.0f}",
    f"- Total cost: ${cumulative_cost:.4f}",
    f"- Projected monthly cost at 17 trades/month: ${monthly_cost:.4f}",
    f"",
    f"## Raw Decision Log",
    f"",
    f"| trade_id | outcome | original | new_decision | new_confidence | new_grade |",
    f"|----------|---------|----------|--------------|----------------|-----------|",
] + decision_rows

report_text = '\n'.join(report_lines) + '\n'

OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_REPORT, 'w') as f:
    f.write(report_text)
print(f'  Saved: {OUT_REPORT}')

print('\n=== DONE ===')
print(f'Model: {MODEL}  Effort: {EFFORT_LEVEL}')
print(f'CANDIDATE rate: {candidate_rate:.1%}  WR: {wr:.1%}  CR×WR: {cr_wr:.4f}')
print(f'Total cost: ${cumulative_cost:.4f}')
