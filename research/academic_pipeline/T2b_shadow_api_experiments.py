#!/usr/bin/env python3
"""
T2b — AI Shadow API Experiments (H-3.3a, H-3.5a, H-9.1a, H-3.2a, H-3.6a)
Shadow experiments to test LLM configuration impact on CANDIDATE frequency.
Budget: $100 cap. Model: claude-sonnet-4-20250514.
Author: Claude Code execution agent
Date: 2026-04-11
"""

import csv
import glob
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ─── Constants ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
BATCH_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
T1_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'
OUT_RESULTS = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'T2b_api_results.json'
OUT_COST = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'T2b_cost_log.csv'
OUT_REPORT = BASE_DIR / 'research' / 'academic_pipeline' / 'results' / 'T2b_shadow_api_results_v1.md'

BUDGET_CAP = 100.0
RATE_LIMIT_SLEEP = 0.5
MODEL = 'claude-sonnet-4-20250514'
SEED = 42
random.seed(SEED)

INPUT_COST_PER_TOK = 3.0 / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

# ─── API key check ────────────────────────────────────────────────────────────
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    print('API_KEY_UNAVAILABLE — set ANTHROPIC_API_KEY and retry.')
    sys.exit(1)

from anthropic import Anthropic
client = Anthropic()

# ─── Cost tracker ─────────────────────────────────────────────────────────────
cumulative_cost = 0.0
cost_log = []


def track_cost(experiment: str, trade_id: str, condition: str,
               input_tokens: int, output_tokens: int) -> float:
    cost = input_tokens * INPUT_COST_PER_TOK + output_tokens * OUTPUT_COST_PER_TOK
    global cumulative_cost
    cumulative_cost += cost
    cost_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'experiment': experiment,
        'trade_id': trade_id,
        'condition': condition,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'call_cost': round(cost, 6),
        'cumulative_cost': round(cumulative_cost, 4),
    })
    return cost


def save_cost_log():
    if not cost_log:
        return
    OUT_COST.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_COST, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_log[0].keys()))
        writer.writeheader()
        writer.writerows(cost_log)


# ─── API call helper ──────────────────────────────────────────────────────────
def evaluate_mso(system_prompt: str, user_message: str,
                 temperature: float = 0, max_tokens: int = 2000,
                 experiment: str = '', trade_id: str = '', condition: str = '') -> dict:
    """Call Claude with the given prompt pair and return parsed JSON."""
    global cumulative_cost

    if cumulative_cost >= BUDGET_CAP:
        return {'decision': 'BUDGET_EXCEEDED',
                'error': f'Cumulative cost ${cumulative_cost:.2f} exceeds ${BUDGET_CAP} cap'}

    time.sleep(RATE_LIMIT_SLEEP)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}]
        )
    except Exception as e:
        return {'decision': 'API_ERROR', 'error': str(e)[:200]}

    usage = response.usage
    track_cost(experiment, trade_id, condition,
               usage.input_tokens, usage.output_tokens)

    text = response.content[0].text
    text_clean = text.strip()
    if text_clean.startswith('```'):
        text_clean = re.sub(r'^```\w*\n?', '', text_clean)
        text_clean = re.sub(r'\n?```$', '', text_clean.strip())

    try:
        return json.loads(text_clean)
    except json.JSONDecodeError:
        s = text_clean.find('{')
        e = text_clean.rfind('}')
        if s >= 0 and e > s:
            try:
                return json.loads(text_clean[s:e + 1])
            except Exception:
                pass
        return {'decision': 'PARSE_ERROR', 'raw': text[:500]}


# ─── Phase 0: Load data ───────────────────────────────────────────────────────
print('\n=== Phase 0: Loading batch data ===')

# Load all full_prompts files
batch_by_ct: dict = {}   # candle_time → entry dict
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

# Load all raw_results — keyed by candle_time
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

# Build by-session index: (date, kill_zone) → sorted list of candle_times
by_session: dict = defaultdict(list)
for ct, item in batch_by_ct.items():
    kz = item.get('kill_zone') or ''
    if kz:
        by_session[(item['date'], kz)].append(ct)
for key in by_session:
    by_session[key].sort()

print(f'  Built {len(by_session)} session indices')

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
        'date': str(row['date']),
        'kill_zone': str(row['kill_zone']),
        'symbol': str(row['symbol']),
        'outcome': outcome,
        'r_multiple': r_mult,
        'win': int(row['win']),
        'system_prompt': batch['system_prompt'],
        'user_message': batch['user_message'],
        'original_decision': raw.get('decision', 'CANDIDATE'),
        'original_confidence': raw.get('confidence_score', 80),
        'setup_grade': str(row.get('setup_grade', 'A')),
    })

print(f'  Matched {len(selected_msos)} T1 trades to batch entries')


# ─── Session memory helpers ───────────────────────────────────────────────────

def _fmt_memory_entry(ct: str, result: dict, override_label: str | None = None) -> str:
    """Format a single candle as a condensed session memory line."""
    decision = override_label or result.get('decision', 'NO_TRADE')
    confidence = result.get('confidence_score', 80)
    no_trade_reason = result.get('no_trade_reason') or ''
    if isinstance(no_trade_reason, dict):
        no_trade_reason = str(no_trade_reason)
    reasoning = result.get('reasoning', {})
    overall = ''
    if isinstance(reasoning, dict):
        overall = reasoning.get('overall_reasoning') or ''
        if isinstance(overall, dict):
            overall = str(overall)
    reason_text = (no_trade_reason or overall or 'no detail available')[:120]
    return f"Candle {ct}: decision={decision}, confidence={confidence}. {reason_text}"


def _build_memory_block(entries: list) -> str:
    """Build the full session memory block text from (ct, result, override_label?) tuples."""
    lines = [
        '## Prior Candle Assessments (this session)',
        'The following are your assessments of prior candles in this kill zone.',
        'Consider the progression: Is a setup developing across candles? '
        'Did a prior candle show a sweep or displacement that sets up the current candle? '
        'If you said WAIT or noted a developing pattern on a prior candle, '
        'check if the trigger has now occurred.',
        '',
    ]
    for e in entries:
        if len(e) == 3:
            ct, result, label = e
        else:
            ct, result = e
            label = None
        lines.append(_fmt_memory_entry(ct, result, label))
    return '\n'.join(lines)


def inject_memory(user_message: str, memory_block: str) -> str:
    """Inject memory block into user_message before '## Current Time:'."""
    inject_pt = '\n## Current Time:'
    idx = user_message.find(inject_pt)
    if idx < 0:
        return user_message + f'\n{memory_block}\n'
    return user_message[:idx] + f'\n{memory_block}\n' + user_message[idx:]


def get_prior_candles(target_ct: str, date: str, kill_zone: str, max_entries: int = 5) -> list:
    """Return up to max_entries (ct, result) pairs from same session before target_ct."""
    session_cts = by_session.get((date, kill_zone), [])
    prior = [(ct, raw_by_ct[ct]) for ct in session_cts
             if ct < target_ct and ct in raw_by_ct]
    return prior[-max_entries:]  # most recent up to max_entries


def scramble_labels(entries: list, seed: int) -> list:
    """Return entries with decision labels randomly shuffled."""
    rng = random.Random(seed)
    labels = [r.get('decision', 'NO_TRADE') for _, r in entries]
    rng.shuffle(labels)
    return [(ct, r, new_label) for (ct, r), new_label in zip(entries, labels)]


# Build CANDIDATE pool for Exp 2 mixed priors (from other sessions)
t1_candle_times = {m['candle_time'] for m in selected_msos}
candidate_pool = [
    (ct, raw_by_ct[ct])
    for ct in raw_by_ct
    if raw_by_ct[ct].get('decision') == 'CANDIDATE' and ct not in t1_candle_times
]
print(f'  Candidate pool for Exp 2 mixed priors: {len(candidate_pool)} entries')


# ─── SMC → Neutral framing ────────────────────────────────────────────────────

SMC_REPLACEMENTS_SYSTEM = [
    # Order matters — do longer phrases first
    ('Smart Money Concepts (SMC) and ICT methodology', 'statistical price structure analysis'),
    ('Smart Money Concepts', 'statistical price structure analysis'),
    ('Smart Money', 'statistical'),
    ('institutional gold trader with 15+ years of experience trading XAUUSD',
     'quantitative analyst specializing in XAUUSD price structure'),
    ('institutional forex trader with 15+ years of experience trading',
     'quantitative analyst specializing in'),
    ('institutional', 'quantitative'),
    ('Order Block Retest', 'Pre-Break Zone Retest'),
    ('Order Block', 'Pre-Break Zone'),
    ('order block', 'pre-break zone'),
    (' OB ', ' PBZ '),
    ('OB zone', 'PBZ zone'),
    ('OB Retest', 'PBZ Retest'),
    ('OB1', 'PBZ1'), ('OB2', 'PBZ2'), ('OB3', 'PBZ3'),
    ('OB4', 'PBZ4'), ('OB5', 'PBZ5'), ('OB6', 'PBZ6'), ('OB7', 'PBZ7'),
    ('Breaker Block', 'Failed Zone'),
    ('breaker block', 'failed zone'),
    ('liquidity sweep', 'stop-cluster activation'),
    ('liquidity', 'stop-cluster pool'),
    ('displacement', 'impulse magnitude'),
    ('Fair Value Gap', 'unfilled price gap'),
    (' FVG', ' UPG'),
    ('premium/discount zone', 'upper/lower half of range'),
    ('premium', 'upper range'),
    ('discount', 'lower range'),
    ('CHoCH', 'structural reversal (SRev)'),
    (' BOS ', ' structural continuation (SCont) '),
    ('kill zone', 'active session window'),
    ('Kill Zone', 'Active Session Window'),
    ('Smart', 'Statistical'),
]

SMC_REPLACEMENTS_USER = [
    ('## Sweeps', '## Stop-Cluster Activations'),
    ('run of ', 'activation of '),
    ('Unmitigated OBs', 'Untouched pre-break zones'),
    ('Unmitigated OB', 'Untouched pre-break zone'),
    ('Unretested Breaker Blocks', 'Untested failed zones'),
    ('Unretested Breaker Block', 'Untested failed zone'),
    ('Unfilled FVGs', 'Unfilled price gaps'),
    ('Unfilled FVG', 'Unfilled price gap'),
    ('bullish OB', 'bullish pre-break zone'),
    ('bearish OB', 'bearish pre-break zone'),
    ('bullish breaker', 'bullish failed-zone'),
    ('bearish breaker', 'bearish failed-zone'),
    ('breaker ', 'failed-zone '),
    ('orig=bullish OB', 'orig=bullish pre-break zone'),
    ('orig=bearish OB', 'orig=bearish pre-break zone'),
    ('CHoCH', 'SRev'),
    ('BOS ', 'SCont '),
    ('BOS\n', 'SCont\n'),
    ('disp=', 'impulse='),
    ('P/D:', 'Range position:'),
    ('## H1 — Order Blocks', '## H1 — Pre-Break Zones'),
    ('## M15 — Order Blocks', '## M15 — Pre-Break Zones'),
    ('Order Block', 'Pre-Break Zone'),
    ('Breakout', 'Structural Break'),
    ('displacement', 'impulse magnitude'),
    ('liquidity', 'stop-cluster'),
    ('Fair Value Gap', 'price gap'),
    (' FVG', ' PG'),
    ('kill zone', 'active session window'),
    ('Kill Zone', 'Active Session Window'),
    ('premium', 'upper-range'),
    ('discount', 'lower-range'),
]

PERSONA_PREAMBLE_PATTERN = re.compile(
    r'^You are [^\n]+\n', re.MULTILINE
)


def neutralize_system_prompt(system_prompt: str) -> str:
    """Apply SMC → neutral replacements to system prompt."""
    text = PERSONA_PREAMBLE_PATTERN.sub(
        'You are a quantitative analyst. '
        'Your role is to evaluate whether a statistical pre-break zone retest setup '
        'exists on the current M15 candle.\n',
        system_prompt, count=1
    )
    for old, new in SMC_REPLACEMENTS_SYSTEM:
        text = text.replace(old, new)
    return text


def neutralize_user_message(user_message: str) -> str:
    """Apply SMC → neutral replacements to user message (MSO data)."""
    text = user_message
    for old, new in SMC_REPLACEMENTS_USER:
        text = text.replace(old, new)
    return text


# ─── Simplified binary prompt for Exp 3 ──────────────────────────────────────
SIMPLIFIED_SYSTEM = """You evaluate M15 forex candles for H1 pre-break zone retest setups.

Rules:
1. Directional bias must be established (D1 or H4+H1 consensus at least 2 of 3 timeframes agree)
2. H4 must align with bias direction
3. An unmitigated H1 pre-break zone must exist from a confirmed structural break
4. Price must be at/near the zone in the correct range half (lower for longs, upper for shorts)
5. M15 must show a structural reversal with impulse magnitude (body >= 1.5x 20-period average) in trade direction
6. Risk-to-reward >= 1.5:1 with SL beyond zone + ATR buffer

If ALL rules are met, respond:
{"decision": "CANDIDATE", "direction": "LONG" or "SHORT", "entry_price": <float>, "stop_loss": <float>, "take_profit_1": <float>}

If ANY rule fails, respond:
{"decision": "NO_TRADE", "reason": "<which rule failed>"}

Respond with ONLY valid JSON. No explanation outside the JSON."""


# ─── Statistics helpers ───────────────────────────────────────────────────────
def candidate_rate(decisions: list) -> float:
    if not decisions:
        return 0.0
    return sum(1 for d in decisions if d == 'CANDIDATE') / len(decisions)


def win_rate(outcomes: list[str]) -> float:
    wins = [o for o in outcomes if o == 'WIN']
    if not outcomes:
        return float('nan')
    return len(wins) / len(outcomes)


def chi2_test(decisions_a: list, decisions_b: list) -> dict:
    """Chi-square test comparing CANDIDATE rates between two conditions."""
    a_cand = sum(1 for d in decisions_a if d == 'CANDIDATE')
    a_no = len(decisions_a) - a_cand
    b_cand = sum(1 for d in decisions_b if d == 'CANDIDATE')
    b_no = len(decisions_b) - b_cand
    table = [[a_cand, a_no], [b_cand, b_no]]
    if min(a_cand, a_no, b_cand, b_no) == 0:
        return {'chi2': float('nan'), 'p': float('nan'), 'table': table}
    chi2, p, _, _ = stats.chi2_contingency(table, correction=False)
    return {'chi2': round(float(chi2), 4), 'p': round(float(p), 6), 'table': table}


def mcnemar_test(decisions_a: list, decisions_b: list) -> dict:
    """McNemar's test for paired CANDIDATE/NO_TRADE decisions."""
    b = sum(1 for a, b in zip(decisions_a, decisions_b)
            if a == 'CANDIDATE' and b != 'CANDIDATE')
    c = sum(1 for a, b in zip(decisions_a, decisions_b)
            if a != 'CANDIDATE' and b == 'CANDIDATE')
    if b + c < 2:
        return {'b': b, 'c': c, 'p': float('nan')}
    result = stats.binomtest(b, b + c, 0.5)
    return {'b': b, 'c': c, 'p': round(float(result.pvalue), 6)}


def safe_wr_test(wr_a: float, n_a: int, wr_b: float, n_b: int) -> dict:
    """Basic proportion test for win rate comparison."""
    if n_a < 5 or n_b < 5:
        return {'p': float('nan'), 'note': 'too few obs'}
    a_wins = round(wr_a * n_a)
    b_wins = round(wr_b * n_b)
    pooled = (a_wins + b_wins) / (n_a + n_b)
    if pooled in (0, 1):
        return {'p': float('nan'), 'note': 'degenerate'}
    se = (pooled * (1 - pooled) * (1 / n_a + 1 / n_b)) ** 0.5
    if se == 0:
        return {'p': float('nan'), 'note': 'zero se'}
    z = (wr_a - wr_b) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return {'z': round(float(z), 3), 'p': round(float(p), 6)}


# ─── Results store ────────────────────────────────────────────────────────────
all_results: dict = {
    'metadata': {
        'date': '2026-04-11',
        'model': MODEL,
        'n_msos': len(selected_msos),
        'seed': SEED,
    },
    'exp1': {},
    'exp2': {},
    'exp3': {},
    'exp4': {},
    'exp5': {},
}


def _nan_to_null(obj):
    """Recursively replace float NaN with None so json.dump emits null, not NaN."""
    if isinstance(obj, float) and (obj != obj):  # NaN check
        return None
    if isinstance(obj, dict):
        return {k: _nan_to_null(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nan_to_null(v) for v in obj]
    return obj


def save_results():
    OUT_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_RESULTS, 'w') as f:
        json.dump(_nan_to_null(all_results), f, indent=2, default=str)


# ─── Experiment 1: Session Memory Label Scrambling (H-3.3a) ──────────────────
print('\n=== Experiment 1: Session Memory Label Scrambling (H-3.3a) ===')

# Select MSOs with >= 3 prior candles in the same session
msos_with_memory = []
for m in selected_msos:
    prior = get_prior_candles(m['candle_time'], m['date'], m['kill_zone'])
    if len(prior) >= 3:
        msos_with_memory.append((m, prior))

print(f'  MSOs with >= 3 prior candles: {len(msos_with_memory)}')

exp1_rows = []
for idx, (mso, prior_entries) in enumerate(msos_with_memory):
    trade_id = mso['trade_id']
    print(f'  [{idx+1}/{len(msos_with_memory)}] {trade_id} cost=${cumulative_cost:.2f}', end='\r')

    if cumulative_cost >= BUDGET_CAP:
        print(f'\n  BUDGET EXCEEDED at {trade_id}')
        break

    # Condition A: real memory
    mem_block_a = _build_memory_block(prior_entries)
    um_a = inject_memory(mso['user_message'], mem_block_a)
    res_a = evaluate_mso(mso['system_prompt'], um_a,
                         experiment='exp1', trade_id=trade_id, condition='A_real')

    # Condition B: scrambled labels
    scrambled = scramble_labels(prior_entries, seed=SEED + idx)
    mem_block_b = _build_memory_block(scrambled)
    um_b = inject_memory(mso['user_message'], mem_block_b)
    res_b = evaluate_mso(mso['system_prompt'], um_b,
                         experiment='exp1', trade_id=trade_id, condition='B_scrambled')

    # Condition C: no memory
    res_c = evaluate_mso(mso['system_prompt'], mso['user_message'],
                         experiment='exp1', trade_id=trade_id, condition='C_nomem')

    exp1_rows.append({
        'trade_id': trade_id,
        'outcome': mso['outcome'],
        'r_multiple': mso['r_multiple'],
        'n_priors': len(prior_entries),
        'dec_A': res_a.get('decision', 'PARSE_ERROR'),
        'dec_B': res_b.get('decision', 'PARSE_ERROR'),
        'dec_C': res_c.get('decision', 'PARSE_ERROR'),
        'conf_A': res_a.get('confidence_score', 0),
        'conf_B': res_b.get('confidence_score', 0),
        'conf_C': res_c.get('confidence_score', 0),
    })

all_results['exp1']['rows'] = exp1_rows
all_results['exp1']['cost_at_end'] = round(cumulative_cost, 4)
save_results()
save_cost_log()
print(f'\n  Exp1 done. Rows: {len(exp1_rows)}. Cost so far: ${cumulative_cost:.2f}')


# ─── Experiment 2: Majority Label Bias (H-3.5a) ──────────────────────────────
print('\n=== Experiment 2: Majority Label Bias (H-3.5a) ===')

rng_exp2 = random.Random(SEED + 100)

exp2_rows = []
for idx, (mso, prior_entries) in enumerate(msos_with_memory):
    trade_id = mso['trade_id']
    print(f'  [{idx+1}/{len(msos_with_memory)}] {trade_id} cost=${cumulative_cost:.2f}', end='\r')

    if cumulative_cost >= BUDGET_CAP:
        print(f'\n  BUDGET EXCEEDED at {trade_id}')
        break

    # Condition A: all-NO_TRADE priors
    forced_notrade = [(ct, r, 'NO_TRADE') for ct, r in prior_entries[:5]]
    mem_a = _build_memory_block(forced_notrade)
    um_a = inject_memory(mso['user_message'], mem_a)
    res_a = evaluate_mso(mso['system_prompt'], um_a,
                         experiment='exp2', trade_id=trade_id, condition='A_allnotrade')

    # Condition B: mixed priors (2 CANDIDATE + 3 NO_TRADE)
    # 3 NO_TRADE from real priors
    notrade_priors = [(ct, r, 'NO_TRADE') for ct, r in prior_entries[:3]]
    # 2 CANDIDATE from candidate_pool (random, excluding same session)
    cand_pool_filtered = [
        (ct, r) for ct, r in candidate_pool
        if ct[:10] != mso['date']  # different date
    ]
    if len(cand_pool_filtered) >= 2:
        sampled_cands = rng_exp2.sample(cand_pool_filtered, 2)
        cand_entries = [(ct, r, 'CANDIDATE') for ct, r in sampled_cands]
    else:
        cand_entries = [(ct, r, 'CANDIDATE') for ct, r in cand_pool_filtered]

    mixed_entries = notrade_priors + cand_entries
    rng_exp2.shuffle(mixed_entries)
    mem_b = _build_memory_block(mixed_entries)
    um_b = inject_memory(mso['user_message'], mem_b)
    res_b = evaluate_mso(mso['system_prompt'], um_b,
                         experiment='exp2', trade_id=trade_id, condition='B_mixed')

    # Condition C: no memory (reuse from exp1 if available, else re-run)
    # Find matching exp1 row to avoid duplicate call
    exp1_match = next((r for r in exp1_rows if r['trade_id'] == trade_id), None)
    if exp1_match:
        dec_c = exp1_match['dec_C']
        conf_c = exp1_match['conf_C']
        reused = True
    else:
        res_c = evaluate_mso(mso['system_prompt'], mso['user_message'],
                             experiment='exp2', trade_id=trade_id, condition='C_nomem')
        dec_c = res_c.get('decision', 'PARSE_ERROR')
        conf_c = res_c.get('confidence_score', 0)
        reused = False

    exp2_rows.append({
        'trade_id': trade_id,
        'outcome': mso['outcome'],
        'r_multiple': mso['r_multiple'],
        'dec_A': res_a.get('decision', 'PARSE_ERROR'),
        'dec_B': res_b.get('decision', 'PARSE_ERROR'),
        'dec_C': dec_c,
        'conf_A': res_a.get('confidence_score', 0),
        'conf_B': res_b.get('confidence_score', 0),
        'conf_C': conf_c,
        'c_reused_from_exp1': reused,
    })

all_results['exp2']['rows'] = exp2_rows
all_results['exp2']['cost_at_end'] = round(cumulative_cost, 4)
save_results()
save_cost_log()
print(f'\n  Exp2 done. Rows: {len(exp2_rows)}. Cost so far: ${cumulative_cost:.2f}')


# ─── Experiment 3: CoT Overthinking (H-9.1a) ─────────────────────────────────
print('\n=== Experiment 3: CoT Overthinking (H-9.1a) ===')

exp3_rows = []
for idx, mso in enumerate(selected_msos):
    trade_id = mso['trade_id']
    print(f'  [{idx+1}/{len(selected_msos)}] {trade_id} cost=${cumulative_cost:.2f}', end='\r')

    if cumulative_cost >= BUDGET_CAP:
        print(f'\n  BUDGET EXCEEDED at {trade_id}')
        break

    # Condition A: full original prompt
    res_a = evaluate_mso(mso['system_prompt'], mso['user_message'],
                         experiment='exp3', trade_id=trade_id, condition='A_full')

    # Condition B: simplified binary prompt
    res_b = evaluate_mso(SIMPLIFIED_SYSTEM, mso['user_message'],
                         experiment='exp3', trade_id=trade_id, condition='B_simplified')

    exp3_rows.append({
        'trade_id': trade_id,
        'outcome': mso['outcome'],
        'r_multiple': mso['r_multiple'],
        'kill_zone': mso['kill_zone'],
        'symbol': mso['symbol'],
        'dec_A': res_a.get('decision', 'PARSE_ERROR'),
        'dec_B': res_b.get('decision', 'PARSE_ERROR'),
        'conf_A': res_a.get('confidence_score', 0),
        'conf_B': res_b.get('confidence_score', 0),
        'agree': res_a.get('decision') == res_b.get('decision'),
    })

all_results['exp3']['rows'] = exp3_rows
all_results['exp3']['cost_at_end'] = round(cumulative_cost, 4)
save_results()
save_cost_log()
print(f'\n  Exp3 done. Rows: {len(exp3_rows)}. Cost so far: ${cumulative_cost:.2f}')


# ─── Experiment 4: SMC vs Neutral Framing (H-3.2a) ───────────────────────────
print('\n=== Experiment 4: SMC vs Neutral Framing (H-3.2a) ===')

# Build neutral system prompt (same for all MSOs — system prompt is shared)
neutral_sys = neutralize_system_prompt(selected_msos[0]['system_prompt'])

exp4_rows = []
for idx, mso in enumerate(selected_msos):
    trade_id = mso['trade_id']
    print(f'  [{idx+1}/{len(selected_msos)}] {trade_id} cost=${cumulative_cost:.2f}', end='\r')

    if cumulative_cost >= BUDGET_CAP:
        print(f'\n  BUDGET EXCEEDED at {trade_id}')
        break

    # Condition A: original SMC framing
    res_a = evaluate_mso(mso['system_prompt'], mso['user_message'],
                         experiment='exp4', trade_id=trade_id, condition='A_smc')

    # Condition B: neutral framing (system + user neutralized)
    # Use mso-specific system prompt in case they differ
    neutral_sys_mso = neutralize_system_prompt(mso['system_prompt'])
    neutral_um = neutralize_user_message(mso['user_message'])
    res_b = evaluate_mso(neutral_sys_mso, neutral_um,
                         experiment='exp4', trade_id=trade_id, condition='B_neutral')

    exp4_rows.append({
        'trade_id': trade_id,
        'outcome': mso['outcome'],
        'r_multiple': mso['r_multiple'],
        'kill_zone': mso['kill_zone'],
        'symbol': mso['symbol'],
        'dec_A': res_a.get('decision', 'PARSE_ERROR'),
        'dec_B': res_b.get('decision', 'PARSE_ERROR'),
        'conf_A': res_a.get('confidence_score', 0),
        'conf_B': res_b.get('confidence_score', 0),
        'agree': res_a.get('decision') == res_b.get('decision'),
    })

all_results['exp4']['rows'] = exp4_rows
all_results['exp4']['cost_at_end'] = round(cumulative_cost, 4)
save_results()
save_cost_log()
print(f'\n  Exp4 done. Rows: {len(exp4_rows)}. Cost so far: ${cumulative_cost:.2f}')


# ─── Experiment 5: 3-Run Self-Consistency (H-3.6a) ───────────────────────────
print('\n=== Experiment 5: 3-Run Self-Consistency (H-3.6a) ===')

exp5_rows = []
for idx, mso in enumerate(selected_msos):
    trade_id = mso['trade_id']
    print(f'  [{idx+1}/{len(selected_msos)}] {trade_id} cost=${cumulative_cost:.2f}', end='\r')

    if cumulative_cost >= BUDGET_CAP:
        print(f'\n  BUDGET EXCEEDED at {trade_id}')
        break

    runs = []
    for run_num in range(3):
        res = evaluate_mso(mso['system_prompt'], mso['user_message'],
                           temperature=0.6,
                           experiment='exp5', trade_id=trade_id,
                           condition=f'run_{run_num}')
        dec = res.get('decision', 'PARSE_ERROR')
        tp = res.get('trade_parameters', {}) or {}
        runs.append({
            'decision': dec,
            'confidence': res.get('confidence_score', 0),
            'entry': tp.get('entry_price', 0),
            'sl': tp.get('stop_loss', 0),
            'tp1': tp.get('take_profit_1', 0),
        })

    decisions = [r['decision'] for r in runs]
    cand_count = sum(1 for d in decisions if d == 'CANDIDATE')

    if cand_count == 3:
        agreement = 'unanimous_candidate'
    elif cand_count == 2:
        agreement = 'majority_candidate'
    elif cand_count == 1:
        agreement = 'majority_notrade'
    else:
        agreement = 'unanimous_notrade'

    # Parameter variance (only if any run is CANDIDATE)
    cand_runs = [r for r in runs if r['decision'] == 'CANDIDATE']
    entry_std = float(np.std([r['entry'] for r in cand_runs])) if len(cand_runs) >= 2 else float('nan')
    sl_std = float(np.std([r['sl'] for r in cand_runs])) if len(cand_runs) >= 2 else float('nan')
    tp_std = float(np.std([r['tp1'] for r in cand_runs])) if len(cand_runs) >= 2 else float('nan')

    exp5_rows.append({
        'trade_id': trade_id,
        'outcome': mso['outcome'],
        'r_multiple': mso['r_multiple'],
        'agreement': agreement,
        'cand_count': cand_count,
        'majority_decision': 'CANDIDATE' if cand_count >= 2 else 'NO_TRADE',
        'dec_run0': runs[0]['decision'],
        'dec_run1': runs[1]['decision'],
        'dec_run2': runs[2]['decision'],
        'entry_std': round(entry_std, 6) if not np.isnan(entry_std) else None,
        'sl_std': round(sl_std, 6) if not np.isnan(sl_std) else None,
        'tp_std': round(tp_std, 6) if not np.isnan(tp_std) else None,
    })

all_results['exp5']['rows'] = exp5_rows
all_results['exp5']['cost_at_end'] = round(cumulative_cost, 4)
save_results()
save_cost_log()
print(f'\n  Exp5 done. Rows: {len(exp5_rows)}. Cost so far: ${cumulative_cost:.2f}')


# ─── Phase 6: Cross-Experiment Synthesis ─────────────────────────────────────
print('\n=== Phase 6: Computing synthesis ===')

BASELINE_WR = 0.65
BASELINE_MONTHLY_TRADES = 17
MEAN_R_WIN = 1.5
BONFERRONI_P = 0.01  # p < 0.01 (5 tests)


def compute_exp_stats(rows: list, dec_col_a: str, dec_col_b: str,
                      outcome_col: str = 'outcome') -> dict:
    """Compute CANDIDATE rates, WR, chi2 for two conditions."""
    dec_a = [r[dec_col_a] for r in rows]
    dec_b = [r[dec_col_b] for r in rows]

    cr_a = candidate_rate(dec_a)
    cr_b = candidate_rate(dec_b)

    # WR for CANDIDATE rows (paired: only where BOTH had valid decisions)
    outcomes_a = [r[outcome_col] for r in rows if r[dec_col_a] == 'CANDIDATE']
    outcomes_b = [r[outcome_col] for r in rows if r[dec_col_b] == 'CANDIDATE']

    wr_a = win_rate(outcomes_a)
    wr_b = win_rate(outcomes_b)
    n_a = len(outcomes_a)
    n_b = len(outcomes_b)

    chi2 = chi2_test(dec_a, dec_b)
    wr_test = safe_wr_test(wr_a, n_a, wr_b, n_b)

    freq_mult = cr_b / cr_a if cr_a > 0 else float('nan')
    monthly_delta = (freq_mult - 1) * BASELINE_MONTHLY_TRADES if not np.isnan(freq_mult) else float('nan')
    net_r = (monthly_delta * BASELINE_WR * MEAN_R_WIN -
             monthly_delta * (1 - BASELINE_WR) * 1.0) if not np.isnan(monthly_delta) else float('nan')

    return {
        'n_total': len(rows),
        'cr_a': round(cr_a, 4),
        'cr_b': round(cr_b, 4),
        'n_cand_a': n_a,
        'n_cand_b': n_b,
        'wr_a': round(float(wr_a), 4) if not np.isnan(wr_a) else None,
        'wr_b': round(float(wr_b), 4) if not np.isnan(wr_b) else None,
        'wr_diff_pp': round((wr_b - wr_a) * 100, 2) if not np.isnan(wr_b) and not np.isnan(wr_a) else None,
        'chi2_stat': chi2.get('chi2'),
        'chi2_p': chi2.get('p'),
        'chi2_sig': chi2.get('p', 1.0) < BONFERRONI_P if chi2.get('p') is not None else False,
        'wr_z': wr_test.get('z'),
        'wr_p': wr_test.get('p'),
        'freq_multiplier': round(float(freq_mult), 3) if not np.isnan(freq_mult) else None,
        'monthly_trade_delta': round(float(monthly_delta), 1) if not np.isnan(monthly_delta) else None,
        'net_r_month': round(float(net_r), 2) if not np.isnan(net_r) else None,
    }


# Exp1 stats
stats_exp1 = {}
if exp1_rows:
    stats_exp1['A_vs_B'] = compute_exp_stats(exp1_rows, 'dec_A', 'dec_B')
    stats_exp1['A_vs_C'] = compute_exp_stats(exp1_rows, 'dec_A', 'dec_C')
    stats_exp1['B_vs_C'] = compute_exp_stats(exp1_rows, 'dec_B', 'dec_C')
    # Mean confidence per condition
    stats_exp1['mean_conf_A'] = round(float(np.nanmean([r['conf_A'] for r in exp1_rows])), 1)
    stats_exp1['mean_conf_B'] = round(float(np.nanmean([r['conf_B'] for r in exp1_rows])), 1)
    stats_exp1['mean_conf_C'] = round(float(np.nanmean([r['conf_C'] for r in exp1_rows])), 1)
all_results['exp1']['stats'] = stats_exp1

# Exp2 stats
stats_exp2 = {}
if exp2_rows:
    stats_exp2['A_vs_B'] = compute_exp_stats(exp2_rows, 'dec_A', 'dec_B')
    stats_exp2['A_vs_C'] = compute_exp_stats(exp2_rows, 'dec_A', 'dec_C')
    # McNemar A vs B
    dec_a2 = [r['dec_A'] for r in exp2_rows]
    dec_b2 = [r['dec_B'] for r in exp2_rows]
    stats_exp2['mcnemar_A_vs_B'] = mcnemar_test(dec_a2, dec_b2)
all_results['exp2']['stats'] = stats_exp2

# Exp3 stats
stats_exp3 = {}
if exp3_rows:
    stats_exp3['A_vs_B'] = compute_exp_stats(exp3_rows, 'dec_A', 'dec_B')
    stats_exp3['agreement_rate'] = round(
        sum(1 for r in exp3_rows if r['agree']) / len(exp3_rows), 4)
    # WR where both agree vs disagree
    agree_cand = [r for r in exp3_rows if r['agree'] and r['dec_A'] == 'CANDIDATE']
    disagree = [r for r in exp3_rows if not r['agree']]
    stats_exp3['wr_when_agree_cand'] = round(win_rate([r['outcome'] for r in agree_cand]), 4)
    stats_exp3['n_disagree'] = len(disagree)
all_results['exp3']['stats'] = stats_exp3

# Exp4 stats
stats_exp4 = {}
if exp4_rows:
    stats_exp4['A_vs_B'] = compute_exp_stats(exp4_rows, 'dec_A', 'dec_B')
    stats_exp4['agreement_rate'] = round(
        sum(1 for r in exp4_rows if r['agree']) / len(exp4_rows), 4)
    # Disagreements
    a_cand_b_no = [r for r in exp4_rows if r['dec_A'] == 'CANDIDATE' and r['dec_B'] != 'CANDIDATE']
    a_no_b_cand = [r for r in exp4_rows if r['dec_A'] != 'CANDIDATE' and r['dec_B'] == 'CANDIDATE']
    stats_exp4['disagreements_a_cand_b_no'] = len(a_cand_b_no)
    stats_exp4['disagreements_a_no_b_cand'] = len(a_no_b_cand)
    stats_exp4['wr_disagreements_a_cand_b_no'] = round(
        win_rate([r['outcome'] for r in a_cand_b_no]), 4) if a_cand_b_no else None
    stats_exp4['wr_disagreements_a_no_b_cand'] = round(
        win_rate([r['outcome'] for r in a_no_b_cand]), 4) if a_no_b_cand else None
all_results['exp4']['stats'] = stats_exp4

# Exp5 stats
stats_exp5 = {}
if exp5_rows:
    # Agreement distribution
    agg_dist = {}
    for cat in ['unanimous_candidate', 'majority_candidate',
                'majority_notrade', 'unanimous_notrade']:
        agg_dist[cat] = sum(1 for r in exp5_rows if r['agreement'] == cat)
    stats_exp5['agreement_distribution'] = agg_dist
    total5 = len(exp5_rows)
    stats_exp5['agreement_rate'] = round(
        (agg_dist['unanimous_candidate'] + agg_dist['unanimous_notrade']) / total5, 4)

    # WR by agreement category
    for cat in ['unanimous_candidate', 'majority_candidate']:
        subset = [r for r in exp5_rows if r['agreement'] == cat]
        outcomes_sub = [r['outcome'] for r in subset]
        stats_exp5[f'wr_{cat}'] = round(win_rate(outcomes_sub), 4) if subset else None
        stats_exp5[f'n_{cat}'] = len(subset)

    # CANDIDATE rate: majority vote vs single run
    single_run_cand_rate = candidate_rate([r['dec_run0'] for r in exp5_rows])
    majority_cand_rate = candidate_rate([r['majority_decision'] for r in exp5_rows])
    stats_exp5['single_run_cr'] = round(single_run_cand_rate, 4)
    stats_exp5['majority_vote_cr'] = round(majority_cand_rate, 4)

    # Parameter variance
    entries_with_std = [r for r in exp5_rows if r['entry_std'] is not None]
    if entries_with_std:
        stats_exp5['mean_entry_std'] = round(
            float(np.nanmean([r['entry_std'] for r in entries_with_std])), 6)
        stats_exp5['mean_sl_std'] = round(
            float(np.nanmean([r['sl_std'] for r in entries_with_std
                              if r['sl_std'] is not None])), 6)

    # Cost estimate: 1x vs 3x vs adaptive
    avg_cost_per_call = (all_results['exp5']['cost_at_end'] -
                         all_results['exp4'].get('cost_at_end', 0)) / max(len(exp5_rows) * 3, 1)
    stats_exp5['cost_per_3run_usd'] = round(avg_cost_per_call * 3, 4)
    stats_exp5['monthly_cost_1x'] = round(avg_cost_per_call * 1 * 30 * BASELINE_MONTHLY_TRADES / 30, 2)
all_results['exp5']['stats'] = stats_exp5

all_results['total_cost'] = round(cumulative_cost, 4)
save_results()

print(f'  Stats computed. Total cost: ${cumulative_cost:.2f}')


# ─── Phase 6: Write markdown report ──────────────────────────────────────────
print('\n=== Phase 6: Writing report ===')

s1 = stats_exp1
s2 = stats_exp2
s3 = stats_exp3
s4 = stats_exp4
s5 = stats_exp5


def fmt_p(p) -> str:
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return 'n/a'
    if p < 0.001:
        return f'{p:.2e}'
    return f'{p:.4f}'


def sig_marker(p) -> str:
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return ''
    return ' ✓ (p<0.01)' if p < BONFERRONI_P else f' (p={fmt_p(p)})'


def fmt_pct(v, default: str = 'n/a') -> str:
    """Format a float as percentage, handling None/nan."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    return f'{v:.1%}'


def fmt_float(v, fmt: str = '.3f', default: str = 'n/a') -> str:
    """Format a float with given format, handling None/nan."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    return format(v, fmt)


report_lines = [
    '# T2b Shadow API Experiment Results',
    '',
    f'**Date:** 2026-04-11',
    f'**Model:** {MODEL}',
    f'**N MSOs (all experiments):** {len(selected_msos)}',
    f'**N MSOs (memory experiments 1-2):** {len(msos_with_memory)}',
    f'**Total API cost:** ${cumulative_cost:.2f}',
    f'**Bonferroni threshold:** p < 0.01 (5 tests)',
    '',
    '---',
    '',
    '## Overview',
    '',
    '**Context from T2a:** Outcomes within the CANDIDATE pool are unpredictable (AUC≈0.5).',
    'The CANDIDATE gate is a deterministic rules check (setup_grade explains 97%).',
    '**Primary optimization target = CANDIDATE rate.** WR differences < 5pp are noise.',
    '',
    '---',
    '',
]

# Exp1 section
report_lines += [
    '## Experiment 1: Session Memory Label Scrambling (H-3.3a)',
    '',
    '**Hypothesis:** Scrambled labels preserve >80% of memory benefit (distributional priming).',
    '',
]

if s1 and s1.get('A_vs_B'):
    ab = s1['A_vs_B']
    ac = s1['A_vs_C']
    report_lines += [
        f'**Sample:** n={ab["n_total"]} MSOs with ≥3 prior candles',
        '',
        '| Condition | CANDIDATE Rate | WR (matched) | Mean Conf |',
        '|-----------|---------------|-------------|-----------|',
        f'| A — real memory | {ab["cr_a"]:.1%} (n={ab["n_cand_a"]}) | {fmt_pct(ab["wr_a"])} | {s1.get("mean_conf_A","?")} |',
        f'| B — scrambled labels | {ab["cr_b"]:.1%} (n={ab["n_cand_b"]}) | {fmt_pct(ab["wr_b"])} | {s1.get("mean_conf_B","?")} |',
        f'| C — no memory | {ac["cr_b"]:.1%} (n={ac["n_cand_b"]}) | {fmt_pct(ac["wr_b"])} | {s1.get("mean_conf_C","?")} |',
        '',
        f'**A vs B chi²:** p={fmt_p(ab["chi2_p"])}{sig_marker(ab["chi2_p"])}',
        f'**A vs C chi²:** p={fmt_p(ac["chi2_p"])}{sig_marker(ac["chi2_p"])}',
        '',
    ]

    # Frequency analysis
    if ab.get('freq_multiplier'):
        report_lines += [
            f'**Frequency multiplier (B/A):** {ab["freq_multiplier"]:.3f}',
            f'**Monthly trade delta:** {ab["monthly_trade_delta"]:+.1f} trades/month',
            f'**Net R/month impact:** {ab["net_r_month"]:+.2f}R',
            '',
        ]

    # Decision gate
    report_lines.append('**Decision gate outcome:**')
    cr_a1 = ab['cr_a']
    cr_b1 = ab['cr_b']
    cr_c1 = ac['cr_b']
    if cr_a1 > 0:
        b_vs_a_pct = abs(cr_b1 - cr_a1) / cr_a1
        if b_vs_a_pct <= 0.20:
            report_lines.append(
                f'B within 20% of A (diff={b_vs_a_pct:.0%}): **DISTRIBUTIONAL PRIMING CONFIRMED.** '
                'Session memory works via format/regime inference, not label content.')
        elif cr_b1 < cr_a1 * 0.80:
            report_lines.append(
                '**LABELS DO MATTER.** B significantly lower than A. '
                'Model learns from prior decisions. Current memory design is correct.')
        else:
            report_lines.append('**INCONCLUSIVE.** B in borderline range.')
    report_lines.append('')
else:
    report_lines.append('*Exp1 data not available (possible budget cap or no MSOs with memory).*\n')

# Exp2 section
report_lines += [
    '---',
    '',
    '## Experiment 2: Majority Label Bias (H-3.5a)',
    '',
    '**Hypothesis:** Mixed priors (2 CANDIDATE + 3 NO_TRADE) produce >5pp higher CANDIDATE rate than all-NO_TRADE.',
    '',
]

if s2 and s2.get('A_vs_B'):
    ab2 = s2['A_vs_B']
    mc = s2.get('mcnemar_A_vs_B', {})
    report_lines += [
        f'**Sample:** n={ab2["n_total"]}',
        '',
        '| Condition | CANDIDATE Rate | WR (matched) |',
        '|-----------|---------------|-------------|',
        f'| A — all NO_TRADE priors | {ab2["cr_a"]:.1%} (n={ab2["n_cand_a"]}) | {fmt_pct(ab2["wr_a"])} |',
        f'| B — mixed priors (2 CAND + 3 NT) | {ab2["cr_b"]:.1%} (n={ab2["n_cand_b"]}) | {fmt_pct(ab2["wr_b"])} |',
        '',
        f'**Chi² A vs B:** p={fmt_p(ab2["chi2_p"])}{sig_marker(ab2["chi2_p"])}',
        f'**McNemar A vs B:** b={mc.get("b","?")}, c={mc.get("c","?")}, p={fmt_p(mc.get("p"))}',
        '',
    ]

    if ab2.get('freq_multiplier'):
        report_lines += [
            f'**Frequency multiplier (B/A):** {ab2["freq_multiplier"]:.3f}',
            f'**Monthly trade delta:** {ab2["monthly_trade_delta"]:+.1f} trades/month',
            f'**Net R/month impact:** {ab2["net_r_month"]:+.2f}R',
            '',
        ]

    diff_pp = (ab2['cr_b'] - ab2['cr_a']) * 100
    report_lines.append('**Decision gate outcome:**')
    if diff_pp > 5 and (ab2.get('chi2_p') or 1.0) < BONFERRONI_P:
        report_lines.append(
            f'**MAJORITY LABEL BIAS CONFIRMED.** B>A by {diff_pp:.1f}pp (p<0.01). '
            'Recommendation: implement memory balancing — always include ≥1 CANDIDATE prior.')
    elif abs(diff_pp) < 3:
        report_lines.append(
            f'No significant majority label bias (diff={diff_pp:+.1f}pp). Not a primary driver of zero-trade problem.')
    else:
        report_lines.append(f'**INCONCLUSIVE.** Diff={diff_pp:+.1f}pp but not significant at Bonferroni threshold.')
    report_lines.append('')
else:
    report_lines.append('*Exp2 data not available.*\n')

# Exp3 section
report_lines += [
    '---',
    '',
    '## Experiment 3: CoT Overthinking (H-9.1a)',
    '',
    '**Hypothesis:** Simplified binary prompt achieves ≥60% WR, comparable to full CoT prompt.',
    '',
]

if s3 and s3.get('A_vs_B'):
    ab3 = s3['A_vs_B']
    report_lines += [
        f'**Sample:** n={ab3["n_total"]}',
        f'**Agreement rate (A=B):** {fmt_pct(s3.get("agreement_rate"))}',
        '',
        '| Condition | CANDIDATE Rate | WR (matched) |',
        '|-----------|---------------|-------------|',
        f'| A — full CoT prompt | {ab3["cr_a"]:.1%} (n={ab3["n_cand_a"]}) | {fmt_pct(ab3["wr_a"])} |',
        f'| B — simplified binary prompt | {ab3["cr_b"]:.1%} (n={ab3["n_cand_b"]}) | {fmt_pct(ab3["wr_b"])} |',
        '',
        f'**Chi² A vs B:** p={fmt_p(ab3["chi2_p"])}{sig_marker(ab3["chi2_p"])}',
    ]
    if s3.get('n_disagree') is not None:
        report_lines.append(f'**Disagreements:** {s3["n_disagree"]} ({s3["n_disagree"]/ab3["n_total"]:.1%})')
    report_lines.append('')

    if ab3.get('freq_multiplier'):
        report_lines += [
            f'**Frequency multiplier (B/A):** {ab3["freq_multiplier"]:.3f}',
            f'**Monthly trade delta:** {ab3["monthly_trade_delta"]:+.1f} trades/month',
            f'**Net R/month impact:** {ab3["net_r_month"]:+.2f}R',
            '',
        ]

    cr_a3 = ab3['cr_a']
    cr_b3 = ab3['cr_b']
    wr_a3 = ab3['wr_a'] or 0
    wr_b3 = ab3['wr_b'] or 0
    report_lines.append('**Decision gate outcome:**')
    freq_gain = (cr_b3 - cr_a3) / cr_a3 if cr_a3 > 0 else 0
    if freq_gain > 0.15 and wr_b3 >= 0.60:
        report_lines.append(
            f'**IMPLEMENT SIMPLIFIED PROMPT.** {freq_gain:.0%} more CANDIDATEs at WR={wr_b3:.1%} (≥60%).')
    elif wr_b3 < 0.55 and freq_gain > 0.15:
        report_lines.append(
            f'Simplified prompt too permissive (WR={wr_b3:.1%} <55%). Keep current prompt.')
    elif abs(wr_b3 - wr_a3) < 0.02 and abs(cr_b3 - cr_a3) < 0.05:
        report_lines.append(
            'CoT overhead adds no value. Simplification safe for token/cost savings.')
    elif wr_a3 > wr_b3 + 0.05:
        report_lines.append(
            f'Full CoT adds measurable value (WR diff={wr_a3-wr_b3:.1%}). Keep current prompt.')
    else:
        report_lines.append(f'INCONCLUSIVE. Freq gain={freq_gain:+.1%}, WR diff={wr_b3-wr_a3:+.1%}.')
    report_lines.append('')
else:
    report_lines.append('*Exp3 data not available.*\n')

# Exp4 section
report_lines += [
    '---',
    '',
    '## Experiment 4: SMC vs Neutral Framing (H-3.2a)',
    '',
    '**Hypothesis:** Neutral framing produces CANDIDATE decisions that align better with actual outcomes.',
    '',
]

if s4 and s4.get('A_vs_B'):
    ab4 = s4['A_vs_B']
    report_lines += [
        f'**Sample:** n={ab4["n_total"]}',
        f'**Agreement rate (A=B):** {fmt_pct(s4.get("agreement_rate"))}',
        '',
        '| Condition | CANDIDATE Rate | WR (matched) |',
        '|-----------|---------------|-------------|',
        f'| A — SMC framing (original) | {ab4["cr_a"]:.1%} (n={ab4["n_cand_a"]}) | {fmt_pct(ab4["wr_a"])} |',
        f'| B — neutral statistical framing | {ab4["cr_b"]:.1%} (n={ab4["n_cand_b"]}) | {fmt_pct(ab4["wr_b"])} |',
        '',
        f'**Chi² A vs B:** p={fmt_p(ab4["chi2_p"])}{sig_marker(ab4["chi2_p"])}',
        f'**Disagreements (A=CAND, B=NT):** {s4.get("disagreements_a_cand_b_no","?")} '
        f'WR={fmt_pct(s4.get("wr_disagreements_a_cand_b_no"))}',
        f'**Disagreements (A=NT, B=CAND):** {s4.get("disagreements_a_no_b_cand","?")} '
        f'WR={fmt_pct(s4.get("wr_disagreements_a_no_b_cand"))}',
        '',
    ]

    if ab4.get('freq_multiplier'):
        report_lines += [
            f'**Frequency multiplier (B/A):** {ab4["freq_multiplier"]:.3f}',
            f'**Monthly trade delta:** {ab4["monthly_trade_delta"]:+.1f} trades/month',
            f'**Net R/month impact:** {ab4["net_r_month"]:+.2f}R',
            '',
        ]

    wr_a4 = ab4['wr_a'] or 0
    wr_b4 = ab4['wr_b'] or 0
    report_lines.append('**Decision gate outcome:**')
    if wr_b4 > wr_a4 + 0.03:
        report_lines.append(f'**NEUTRAL FRAMING BETTER.** WR(B)-WR(A)={wr_b4-wr_a4:.1%}. Recommend prompt revision.')
    elif wr_a4 > wr_b4 + 0.03:
        report_lines.append(f'**SMC FRAMING BETTER** (unexpected). WR(A)-WR(B)={wr_a4-wr_b4:.1%}. Keep current framing.')
    else:
        report_lines.append(f'Framing does not affect WR (diff={wr_b4-wr_a4:+.1%}). Choose based on token cost.')
    report_lines.append('')
else:
    report_lines.append('*Exp4 data not available.*\n')

# Exp5 section
report_lines += [
    '---',
    '',
    '## Experiment 5: 3-Run Self-Consistency (H-3.6a)',
    '',
    '**Hypothesis:** Unanimous 3/3 CANDIDATE has WR>70%; split 2/3 has WR<60%.',
    '',
]

if s5 and s5.get('agreement_distribution'):
    ad = s5['agreement_distribution']
    total5 = sum(ad.values())
    report_lines += [
        f'**Sample:** n={total5}',
        '',
        '| Agreement Category | Count | % |',
        '|-------------------|-------|---|',
        f'| Unanimous CANDIDATE (3/3) | {ad.get("unanimous_candidate",0)} | {ad.get("unanimous_candidate",0)/total5:.1%} |',
        f'| Majority CANDIDATE (2/3) | {ad.get("majority_candidate",0)} | {ad.get("majority_candidate",0)/total5:.1%} |',
        f'| Majority NO_TRADE (1/3) | {ad.get("majority_notrade",0)} | {ad.get("majority_notrade",0)/total5:.1%} |',
        f'| Unanimous NO_TRADE (0/3) | {ad.get("unanimous_notrade",0)} | {ad.get("unanimous_notrade",0)/total5:.1%} |',
        '',
        f'**Overall agreement rate (unanimous):** {fmt_pct(s5.get("agreement_rate"))}',
        '',
        '| Group | WR | N |',
        '|-------|-----|---|',
        f'| Unanimous CANDIDATE | {fmt_pct(s5.get("wr_unanimous_candidate"))} | {s5.get("n_unanimous_candidate","?")} |',
        f'| Majority CANDIDATE | {fmt_pct(s5.get("wr_majority_candidate"))} | {s5.get("n_majority_candidate","?")} |',
        '',
        f'**Single-run CANDIDATE rate:** {fmt_pct(s5.get("single_run_cr"))}',
        f'**Majority-vote CANDIDATE rate:** {fmt_pct(s5.get("majority_vote_cr"))}',
        '',
    ]

    if s5.get('mean_entry_std') is not None:
        report_lines.append(f'**Parameter variance (std across 3 runs):** entry={s5["mean_entry_std"]:.6f}, SL={fmt_float(s5.get("mean_sl_std"), ".6f")}')
        report_lines.append('')

    report_lines.append('**Decision gate outcome:**')
    wr_unm = s5.get('wr_unanimous_candidate') or 0
    wr_maj = s5.get('wr_majority_candidate') or 0
    agr = s5.get('agreement_rate', 0)
    if wr_unm - wr_maj > 0.10:
        report_lines.append(
            f'**SPLIT DISAGREEMENT IS SIGNAL.** Unanimous WR={wr_unm:.1%} vs split WR={wr_maj:.1%} (diff={wr_unm-wr_maj:.1%}). '
            'Abstaining on splits is highest-value intervention.')
    elif agr > 0.95:
        report_lines.append(
            f'Agreement={agr:.1%} >95%. Ensemble adds little signal. '
            'Single-run is sufficient; disagreement logging valuable for edge cases.')
    elif 0.80 <= agr <= 0.90:
        report_lines.append(
            f'Agreement={agr:.1%} (80-90%). Meaningful diversity exists. '
            'Adaptive 2-3 run approach (Aggarwal 2023) is worth implementing.')
    else:
        report_lines.append(f'Agreement={agr:.1%}. Review distribution for further analysis.')
    report_lines.append('')
else:
    report_lines.append('*Exp5 data not available.*\n')

# Combined synthesis
report_lines += [
    '---',
    '',
    '## Phase 6: Combined Architecture Recommendation',
    '',
    '### The Memory Story (Exp 1 + 2)',
    '',
]

if s1.get('A_vs_B') and s2.get('A_vs_B'):
    e1_ab = s1['A_vs_B']
    e2_ab = s2['A_vs_B']
    b_vs_a_pct1 = abs(e1_ab['cr_b'] - e1_ab['cr_a']) / e1_ab['cr_a'] if e1_ab['cr_a'] > 0 else 0
    report_lines += [
        f'- Exp1: Scrambled labels produced {b_vs_a_pct1:.0%} change in CANDIDATE rate vs real labels.',
        f'  → Memory mechanism is primarily {"distributional priming" if b_vs_a_pct1 <= 0.20 else "label-dependent"}.',
        f'- Exp2: Mixed priors ({(e2_ab["cr_b"]-e2_ab["cr_a"])*100:+.1f}pp vs all-NO_TRADE).',
        f'  → Majority label bias {"confirmed" if (e2_ab.get("chi2_p") or 1) < BONFERRONI_P else "not confirmed"} as driver.',
        '',
    ]

report_lines += [
    '### The Prompt Story (Exp 3 + 4)',
    '',
]

if s3.get('A_vs_B') and s4.get('A_vs_B'):
    e3_ab = s3['A_vs_B']
    e4_ab = s4['A_vs_B']
    report_lines += [
        f'- CoT depth (Exp3): Simplified prompt CANDIDATE rate {e3_ab["cr_b"]:.1%} vs full {e3_ab["cr_a"]:.1%}.',
        f'  → {"Simplified is viable" if (e3_ab.get("wr_b") or 0) >= 0.60 else "Full CoT preferred"}.',
        f'- SMC framing (Exp4): Neutral CANDIDATE rate {e4_ab["cr_b"]:.1%} vs SMC {e4_ab["cr_a"]:.1%}.',
        f'  WR diff: {(e4_ab.get("wr_b",0) or 0)-(e4_ab.get("wr_a",0) or 0):+.1%}.',
        f'  → {"Neutral framing preferred" if (e4_ab.get("wr_b",0) or 0) > (e4_ab.get("wr_a",0) or 0) + 0.03 else "SMC framing neutral or better"}.',
        '',
    ]

report_lines += [
    '### The Ensemble Story (Exp 5)',
    '',
]

if s5.get('agreement_distribution'):
    agr5 = s5.get('agreement_rate', 0)
    report_lines += [
        f'- Agreement rate: {agr5:.1%}.',
        f'- {"3-run ensemble justified (>10pp WR gain for unanimous)" if (s5.get("wr_unanimous_candidate",0) or 0) - (s5.get("wr_majority_candidate",0) or 0) > 0.10 else "Single-run sufficient (low gain from ensemble)"}.',
        '',
    ]

report_lines += [
    '### Optimal Component 3A Configuration',
    '',
    '| Dimension | Current | Recommendation | Evidence |',
    '|-----------|---------|---------------|---------|',
]

# Derive recommendations
prompt_rec = 'Keep full CoT'
mem_rec = 'Current design'
eval_rec = 'Single-run'
conf_rec = 'Remove confidence score (use agreement rate if running 2-3x)'

if s3.get('A_vs_B'):
    e3 = s3['A_vs_B']
    freq_g3 = (e3['cr_b'] - e3['cr_a']) / e3['cr_a'] if e3['cr_a'] > 0 else 0
    if freq_g3 > 0.15 and (e3.get('wr_b') or 0) >= 0.60:
        prompt_rec = 'Simplify to binary'
    elif abs(e3['cr_b'] - e3['cr_a']) < 0.05 and abs((e3.get('wr_b', 0) or 0) - (e3.get('wr_a', 0) or 0)) < 0.02:
        prompt_rec = 'Keep full CoT (no gain from simplifying)'

if s1.get('A_vs_B') and s2.get('A_vs_B'):
    e1 = s1['A_vs_B']
    e2 = s2['A_vs_B']
    b_vs_a1 = abs(e1['cr_b'] - e1['cr_a']) / e1['cr_a'] if e1['cr_a'] > 0 else 0
    e2_diff_pp = (e2['cr_b'] - e2['cr_a']) * 100
    if b_vs_a1 <= 0.20 and e2_diff_pp > 5 and (e2.get('chi2_p') or 1) < BONFERRONI_P:
        mem_rec = 'Balance: include ≥1 CANDIDATE prior (Exp2 result)'
    elif b_vs_a1 <= 0.20 and abs(e2_diff_pp) < 3:
        mem_rec = 'Keep real labels (distributional, labels matter less)'

if s5.get('agreement_distribution'):
    agr5 = s5.get('agreement_rate', 0)
    unm_wr = s5.get('wr_unanimous_candidate') or 0
    maj_wr = s5.get('wr_majority_candidate') or 0
    if unm_wr - maj_wr > 0.10:
        eval_rec = '3-run majority (abstain on splits)'
    elif agr5 > 0.90:
        eval_rec = 'Single-run (>90% agreement, ensemble wasteful)'
    elif 0.80 <= agr5 <= 0.90:
        eval_rec = 'Adaptive 2-3 run (Aggarwal 2023)'

report_lines += [
    f'| Prompt | Full SMC CoT | {prompt_rec} | Exp3 + Exp4 |',
    f'| Memory | None (live)/Real (batch) | {mem_rec} | Exp1 + Exp2 |',
    f'| Evaluation | Single-run temp=0 | {eval_rec} | Exp5 |',
    f'| Confidence | Current 50-95 score | {conf_rec} | T2a + Exp5 |',
    '',
]

# Frequency impact table
report_lines += [
    '### Frequency Impact Summary',
    '',
    '| Experiment | Condition | CR Control | CR Experimental | Freq Mult | ΔTrades/mo | ΔR/mo |',
    '|------------|-----------|-----------|----------------|-----------|-----------|-------|',
]

exps_for_freq = [
    ('Exp1 (memory vs none)', s1.get('A_vs_C', {})),
    ('Exp2 (mixed vs all-NT)', s2.get('A_vs_B', {})),
    ('Exp3 (simplified vs full)', s3.get('A_vs_B', {})),
    ('Exp4 (neutral vs SMC)', s4.get('A_vs_B', {})),
]

for label, st in exps_for_freq:
    if st:
        fm = st.get('freq_multiplier')
        mt = st.get('monthly_trade_delta')
        nr = st.get('net_r_month')
        report_lines.append(
            f'| {label} | — | {st["cr_a"]:.1%} | {st["cr_b"]:.1%} | '
            f'{fmt_float(fm, ".3f")} | {fmt_float(mt, "+.1f")} | {fmt_float(nr, "+.2f")} |'
        )

report_lines += [
    '',
    '### Interaction with T2a and T3',
    '',
    '- **T2a:** CANDIDATE gate is deterministic (rules check). LLM adds zone detection + spatial reasoning.',
    '- **T2b:** Tests whether prompt/memory configuration affects pool SIZE (how many CANDIDATEs).',
    '- **T3:** Tests whether feature thresholds (fib depth, structural density) can sub-segment the pool.',
    '- Together: T3 says which trades to take; T2b says how many trades the system generates.',
    '',
    '---',
    '',
    f'*Generated by T2b_shadow_api_experiments.py | Total cost: ${cumulative_cost:.2f} of ${BUDGET_CAP} budget*',
]

OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_REPORT, 'w') as f:
    f.write('\n'.join(report_lines))

print(f'  Report written: {OUT_REPORT}')
save_results()
save_cost_log()
print(f'\n=== T2b Complete ===')
print(f'Total cost: ${cumulative_cost:.2f}')
print(f'Results: {OUT_RESULTS}')
print(f'Cost log: {OUT_COST}')
print(f'Report: {OUT_REPORT}')
