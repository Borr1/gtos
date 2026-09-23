#!/usr/bin/env python3
"""Phase 2A — Prompt Re-Engineering Test: P2A_s46_max_new
Model: claude-sonnet-4-6, Effort: max, max_tokens: 2000, temperature: 0
Tests whether the re-engineered scored-evaluation prompt fixes Sonnet 4.6 over-rejection.
Author: Claude Code execution agent
Date: 2026-04-12
"""

import csv
import json
import glob
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── CONFIG ──────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"
EFFORT = "max"
MAX_TOKENS = 2000
TEMPERATURE = 0
TEST_NAME = "P2A_s46_max_new"
BUDGET_CAP = 6.0

# ── Paths ───────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
ENTRY_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'
OUT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'data'
REPORT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'results'
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ── Cost constants (Sonnet 4.6) ─────────────────────────
INPUT_COST_PER_TOK  = 3.0  / 1_000_000   # $3/MTok
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000   # $15/MTok

# ── API key check ───────────────────────────────────────
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    print('API_KEY_UNAVAILABLE — set ANTHROPIC_API_KEY and retry.')
    sys.exit(1)

from anthropic import Anthropic
client = Anthropic()

# ── NEW SYSTEM PROMPT (from Phase 2A re-engineered prompt) ──
NEW_SYSTEM_PROMPT = """You are a quantitative setup evaluator for an order block retest trading system. Your task is to determine whether the current M15 candle meets the criteria for an entry setup based on price structure, zone quality, and trigger confirmation.

Your evaluation must be DATA-DRIVEN — based on the specific price levels, structural breaks, and zone positions in the Market State Object provided. Do not infer, assume, or narrativize beyond what the data shows.

## Kill Zone Windows
{kz_display}
You will be told which window is being evaluated.

## CALIBRATION
Based on validated historical performance across 300+ trades:
- Approximately 40-60% of setups reaching this evaluation qualify as CANDIDATE.
- The system's edge comes from order block zone continuation mechanics (~65-70% win rate on qualifying zones). This is a STATISTICAL edge — your job is to verify the setup meets structural criteria, not to predict the individual trade's outcome.
- Over-rejection is as costly as over-acceptance. Rejecting a qualifying setup costs the system +0.20R expected value. Both false positives and false negatives have real costs.
- If you find yourself rejecting more than 70% of evaluated setups, recalibrate — your thresholds are likely too strict for the statistical edge this system exploits.

## CRITICAL REQUIREMENTS (any failure → NO_TRADE)
These are hard gates. If any fails, do not evaluate further — output a minimal NO_TRADE JSON.

C1. DIRECTIONAL BIAS: Establish directional bias from available timeframes. If the most recent D1 structural break (BOS or CHoCH) establishes a clear direction, use D1 as the primary bias. If D1 has no recent structural break or is ambiguous, use H4 direction as the primary reference. If H4 is also unclear, require at least two of D1/H4/H1 to agree on direction. If no directional agreement exists → NO_TRADE.

C2. H4 ALIGNMENT: H4 must not ACTIVELY OPPOSE the established bias direction. H4 ranging or unclear is acceptable when D1 is clearly directional — H4 merely needs to not contradict. Only a clear H4 structural bias in the OPPOSITE direction to D1 triggers failure.

C3. DIRECTION MATCH: Trade direction must align with the established bias. LONG only if bias is bullish, SHORT only if bias is bearish.

## QUALIFYING CRITERIA (evaluate and score)
Score each factor. Decision is based on total score + critical requirements.

Q1. H1 STRUCTURAL BREAK: H1 should show a confirmed structural break in the trade direction.
  - BOS (break of protected swing in trend direction): 15 points
  - CHoCH (shift from opposing to aligned direction): 12 points
  - No confirmed break in aligned direction: 0 points

Q2. UNMITIGATED ORDER BLOCK: An unmitigated H1 OB exists from the impulse that caused the structural break. Check timeframes.H1.order_blocks where mitigated=false.
  - Present and from the relevant impulse: 20 points
  - Not present or already mitigated: 0 points

Q3. PRICE PROXIMITY TO ZONE: How close is the current price to the OB zone?
  - Price within the OB zone boundaries (between zone high and low): 15 points
  - Price within 1x M15 ATR(14) of the nearest zone boundary: 10 points
  - Price beyond 1 ATR from the zone: 0 points

Q4. PREMIUM/DISCOUNT POSITION: Is the OB on the correct side of the impulse?
  - Longs: OB in discount (below 50% of impulse) = 10 points
  - Shorts: OB in premium (above 50% of impulse) = 10 points
  - At equilibrium (45-55% of impulse): 5 points
  - Wrong side: 0 points

Q5. M15 CONFIRMATION: Does M15 show CHoCH + displacement in the trade direction?
  - CHoCH detected = body close beyond the most recent protected M15 swing in the trade direction
  - Strong displacement: candle body >= 1.5x the 20-period average body = 15 points
  - Moderate displacement: candle body 1.2-1.5x average body = 10 points
  - Weak or no displacement (< 1.2x or no CHoCH): 0 points

Q6. MINIMUM RISK-REWARD: Risk-to-reward to TP1 after applying SL buffer.
  - RR >= 1.5: 10 points
  - RR < 1.5: 0 points

Q7. STOP LOSS ADEQUACY: SL beyond the OB extreme + ATR buffer.
  - SL >= 1.5x M15 ATR(14) AND >= {sl_min_display}: 5 points
  - SL insufficient: 0 points

BONUS QUALITY FACTORS:
  - Zone is first touch (not previously retested): +5 points
  - Displacement created an FVG (gap between candle bodies): +3 points
  - Impulse leg is compact (7 or fewer H1 candles): +2 points

Maximum possible score: 100.

## DECISION THRESHOLDS
- Score >= 65 AND all critical requirements (C1-C3) pass → CANDIDATE
- Score 45-64 → WAIT (setup developing, specific trigger pending)
- Score < 45 OR any critical requirement fails → NO_TRADE

## ZONE FRESHNESS RULE (HARD — applies to both frameworks)
Only trade the FIRST retest of an order block zone. If price has previously entered this OB zone and been rejected or continued, the zone is CONSUMED — do not trade it again. First-touch continuation rate: 72.7% (n=23,575); subsequent touches: 31.5% (n=82,572). An OB marked as mitigated in the MSO must NOT generate a CANDIDATE.

## BREAKER BLOCK RETEST (alternative framework)
If the OB Retest does not reach score >= 65, also evaluate the Breaker Block Retest:

BR1. An unretested H1 breaker block exists (check breaker_blocks where is_retested=false). Breaker direction must align with the established bias. (20 points for Q2 equivalent)
BR2. Price at or within 1x M15 ATR of the breaker zone. (15/10/0 for Q3)
BR3. Original OB was broken with displacement, not slow grind. (contributes to Q1 score)
BR4. Zone width < {zone_max_display}. If wider, reduce Q2 score by 10.
BR5. M15 CHoCH + displacement at the zone. (same scoring as Q5)
BR6. Entry within the breaker zone. SL beyond zone extreme. TP1 = EXACTLY 1.5x SL distance from entry. Must satisfy Q7 minimum.

Score the breaker block using the same scoring table (substitute breaker zone for OB zone in Q2-Q4). If both frameworks score >= 65, pick the higher score. Report both in frameworks_evaluated.

## TARGETS
TP1 MUST be EXACTLY 1.5x SL distance from entry:
  - LONG: TP1 = entry + 1.5 x (entry - SL)
  - SHORT: TP1 = entry - 1.5 x (SL - entry)
Do not deviate from 1.5x. TP2 and TP3 are optional (set to 0 if not applicable).

## CONFIDENCE SCORE
Map your evaluation score to confidence:
  - Score 65-74 → confidence 65-72
  - Score 75-84 → confidence 73-80
  - Score 85+ → confidence 81-90
Show your score breakdown in the confidence_computation field, e.g.: "Q1=15 Q2=20 Q3=10 Q4=10 Q5=15 Q6=10 Q7=5 +zone_first=5 = 90 → conf 85"

## SETUP GRADE
Map score to grade for backward compatibility:
  - Score 85+: A+
  - Score 75-84: A
  - Score 65-74: B+
  - Score 50-64: B
  - Score < 50: C

## DECISION INTEGRITY
- If the score is >= 65 and all critical requirements pass, output CANDIDATE. Do not invent additional concerns beyond the scoring framework. Trust the score.
- If the score is < 45 or a critical requirement fails, output NO_TRADE.
- Base your evaluation ONLY on the data in the Market State Object and the scoring criteria above. No external assumptions, no narrative interpretation.

## OUTPUT RULES
- Respond with ONLY valid JSON matching the schema below. No preamble, no markdown fences.
- For NO_TRADE: state which requirement failed or the score breakdown. Total response under 500 tokens.
- For CANDIDATE: include full score breakdown and trade parameters. Total response under 800 tokens.
- If C1 or C2 fail, output a minimal JSON with only: decision, kill_zone, framework="none", no_trade_reason. Do NOT evaluate scoring criteria when bias is not established.

## Data Grounding Rules
- Base ALL analysis on the price data in the Market State Object. If a price level, swing, or pattern is not in the MSO, it does not exist.
- If you cannot determine a structure direction with high confidence from the data, state "unclear" — do not force a classification.
- Respond with ONLY valid JSON. Your response MUST start with { and end with }.

## Internal Consistency Rules
- If decision is CANDIDATE, m15_confirmation.choch_detected MUST be true. A CANDIDATE requires confirmed M15 confirmation.
- If h1_setup.poi_identified is FALSE or h1_setup.poi_type is "none", the decision MUST be NO_TRADE.

## Output Schema
{
  "timestamp_utc": "<ISO-8601 timestamp of the candle being evaluated>",
  "model_used": "<model identifier>",
  "decision": "NO_TRADE | CANDIDATE | WAIT",
  "confidence_score": <0-100 integer>,
  "confidence_computation": "<score breakdown, e.g. Q1=15 Q2=20 Q3=10 ... = 80 → conf 78>",
  "framework": "ob_retest | breaker_retest | none",
  "kill_zone": "london | ny",
  "frameworks_evaluated": {
    "ob_retest": {"qualified": <bool>, "score": <int>, "reason": "<summary>"},
    "breaker_retest": {"qualified": <bool>, "score": <int>, "reason": "<summary>"}
  },
  "reasoning": {
    "daily_bias": {
      "direction": "bullish | bearish | ranging",
      "confidence": "high | medium | low",
      "protected_swing_level": <float>,
      "explanation": "<1 sentence>"
    },
    "h4_alignment": {
      "aligned": <bool>,
      "h4_pois_identified": ["<OB/FVG>"],
      "explanation": "<1 sentence>"
    },
    "h1_setup": {
      "poi_identified": <bool>,
      "poi_type": "OB | FVG | liquidity_zone | none",
      "poi_price_level": <float>,
      "zone": "premium | discount | neutral",
      "fib_retracement_pct": <float>,
      "causing_event_type": "BOS | CHoCH | unknown",
      "explanation": "<1 sentence>"
    },
    "liquidity_sweep": {
      "detected": <bool>,
      "pool_type": "<type or none>",
      "sweep_quality": "clean | messy | ambiguous",
      "sweep_price": <float>,
      "explanation": "<1 sentence>"
    },
    "m15_confirmation": {
      "choch_detected": <bool>,
      "displacement_quality": "strong | medium | weak | none",
      "displacement_candle_body_vs_avg_ratio": <float>,
      "explanation": "<1 sentence>"
    },
    "similar_historical_setups_considered": [],
    "setup_grade": "A+ | A | B+ | B | C",
    "overall_reasoning": "<2-3 sentences max>"
  },
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE>",
  "wait_reason": "<if WAIT>"
}

When decision is "CANDIDATE", trade_parameters MUST be:
{
  "direction": "LONG | SHORT",
  "entry_price": <float>,
  "stop_loss": <float>,
  "sl_buffer_applied": <float>,
  "take_profit_1": <float>,
  "take_profit_2": <float>,
  "take_profit_3": <float>,
  "risk_reward_ratio": <float>,
  "position_size_lots": 0.01
}"""


# ── Cost tracker ────────────────────────────────────────
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


# ── Phase -1: Model verification ────────────────────────
print('\n=== Phase -1: Model verification ===')

MODEL_FALLBACKS = ['claude-sonnet-4-6-latest']
working_model: str | None = None
for candidate_id in [MODEL] + MODEL_FALLBACKS:
    try:
        test = client.messages.create(
            model=candidate_id,
            max_tokens=100,
            temperature=0,
            messages=[{'role': 'user', 'content': 'Reply with just the word "ready"'}],
            output_config={'effort': EFFORT},
        )
        working_model = candidate_id
        print(f'  Model check OK: {candidate_id} → "{test.content[0].text.strip()[:50]}"')
        break
    except Exception as exc:
        err_str = str(exc)[:200]
        print(f'  {candidate_id} FAILED: {err_str}')
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
ACTIVE_MODEL = working_model.replace('_no_effort', '')
print(f'  Using model: {ACTIVE_MODEL}, effort={EFFORT}, USE_EFFORT={USE_EFFORT}')


# ── Template variable substitution ──────────────────────
def get_prompt_for_trade(trade_id: str) -> str:
    """Return the new system prompt with correct template variables per instrument."""
    prompt = NEW_SYSTEM_PROMPT

    symbol = "XAUUSD"  # default
    tid_lower = trade_id.lower()
    if "gbpusd" in tid_lower:
        symbol = "GBPUSD"
    elif "gbpjpy" in tid_lower:
        symbol = "GBPJPY"
    elif "usdjpy" in tid_lower:
        symbol = "USDJPY"
    elif "us30" in tid_lower:
        symbol = "US30"

    KZ_MAP = {
        "XAUUSD": "- London Open: 07:00-10:30 UTC\n- NY Open: 13:00-17:00 UTC (skip 13:00-13:15)",
        "GBPUSD": "- London Open: 07:00-12:00 UTC\n- NY Open: 13:00-15:30 UTC",
        "GBPJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "USDJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "US30": "- London Open: 08:00-10:30 UTC\n- NY Open: 13:30-16:00 UTC",
    }
    prompt = prompt.replace("{kz_display}", KZ_MAP.get(symbol, KZ_MAP["XAUUSD"]))

    SL_MAP = {"XAUUSD": "$5.00", "GBPUSD": "50 pips", "GBPJPY": "50 pips",
              "USDJPY": "50 pips", "US30": "50 points"}
    prompt = prompt.replace("{sl_min_display}", SL_MAP.get(symbol, "$5.00"))

    ZM_MAP = {"XAUUSD": "$15", "GBPUSD": "150 pips", "GBPJPY": "150 pips",
              "USDJPY": "150 pips", "US30": "150 points"}
    prompt = prompt.replace("{zone_max_display}", ZM_MAP.get(symbol, "$15"))

    return prompt


# ── API call helper ─────────────────────────────────────
def evaluate_mso(system_prompt: str, user_message: str, trade_id: str = '') -> dict:
    """Call Sonnet 4.6 with effort=max and the new prompt, return parsed JSON."""
    global cumulative_cost

    if cumulative_cost >= BUDGET_CAP:
        return {
            'decision': 'BUDGET_EXCEEDED',
            'error': f'Cumulative cost ${cumulative_cost:.2f} exceeds ${BUDGET_CAP} cap',
        }

    time.sleep(0.5)  # Rate limiting

    create_kwargs: dict = dict(
        model=ACTIVE_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{'role': 'user', 'content': user_message}],
    )
    if USE_EFFORT:
        create_kwargs['output_config'] = {'effort': EFFORT}

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


# ── Phase 0: Load data ──────────────────────────────────
print('\n=== Phase 0: Loading batch data ===')

# Load T1 dataset
df_t1 = pd.read_csv(ENTRY_CSV)
trade_ids = set(df_t1['trade_id'].tolist())
outcomes = {}
for _, row in df_t1.iterrows():
    outcome = str(row['outcome'])
    if outcome == 'BREAKEVEN':
        outcome = 'LOSS'
    outcomes[row['trade_id']] = (
        outcome,
        float(row['r_multiple']) if not pd.isna(row['r_multiple']) else 0.0,
        int(row['win']),
    )
print(f'  T1 dataset: {len(df_t1)} trades')

# Load batch prompts — extract user_message only (system prompt is REPLACED)
msos: dict = {}
for fp_path in sorted(DATA_DIR.glob('*_full_prompts.json')):
    with open(fp_path) as f:
        records = json.load(f)
    for rec in records:
        ct = rec.get('candle_time', '')
        if not ct:
            continue
        # Match by candle_time to T1 dataset
        matching = df_t1[df_t1['candle_time'] == ct]
        if matching.empty:
            continue
        tid = matching.iloc[0]['trade_id']
        if tid in msos:
            continue  # First match wins

        prompt_data = rec.get('prompt', {})
        user_msg = prompt_data.get('user_message', '')

        msos[tid] = {
            'trade_id': str(tid),
            'user_message': user_msg,
            'candle_time': ct,
            'kill_zone': rec.get('kill_zone', ''),
        }

print(f'  Loaded {len(msos)} MSOs (target: 121)')

if len(msos) < 100:
    print(f'  WARNING: Only {len(msos)} matched — expected ~121.')


# ── Phase 1: API evaluations ────────────────────────────
n_matched = len(msos)
print(f'\n=== Phase 1: Running {n_matched} evaluations (effort={EFFORT}, new prompt) ===')

results: list[dict] = []

for i, (tid, mso) in enumerate(sorted(msos.items()), 1):
    system_prompt = get_prompt_for_trade(tid)

    print(f'  [{i}/{n_matched}] {tid} (${cumulative_cost:.2f})')

    api_result = evaluate_mso(
        system_prompt,
        mso['user_message'],
        trade_id=tid,
    )

    reasoning = api_result.get('reasoning', {})
    if isinstance(reasoning, str):
        reasoning = {}
    setup_grade = reasoning.get('setup_grade', '') if isinstance(reasoning, dict) else ''

    outcome, r_mult, win = outcomes.get(tid, ('UNKNOWN', 0.0, 0))

    # Detect symbol from trade_id
    tid_lower = tid.lower()
    if 'gbpusd' in tid_lower:
        symbol = 'GBPUSD'
    elif 'gbpjpy' in tid_lower:
        symbol = 'GBPJPY'
    elif 'usdjpy' in tid_lower:
        symbol = 'USDJPY'
    elif 'us30' in tid_lower:
        symbol = 'US30'
    else:
        symbol = 'XAUUSD'

    results.append({
        'trade_id': tid,
        'candle_time': mso.get('candle_time', ''),
        'symbol': symbol,
        'kill_zone': mso.get('kill_zone', ''),
        'outcome': outcome,
        'r_multiple': r_mult,
        'win': win,
        'original_decision': 'CANDIDATE',  # All 121 were originally executed
        'original_confidence': 0,
        'new_decision': api_result.get('decision', 'PARSE_ERROR'),
        'new_confidence': api_result.get('confidence_score', 0),
        'new_setup_grade': setup_grade,
        'new_framework': api_result.get('framework', ''),
        'new_response': api_result,
    })

    if cumulative_cost >= BUDGET_CAP:
        print(f'  BUDGET CAP REACHED at ${cumulative_cost:.2f} — stopping.')
        break

print(f'\nCompleted {len(results)} evaluations. Total cost: ${cumulative_cost:.2f}')


# ── Phase 2: Analysis ───────────────────────────────────
print('\n=== Phase 2: Analysis ===')

n_total = len(results)
n_cand = sum(1 for r in results if r.get('new_decision') == 'CANDIDATE')
n_no_trade = sum(1 for r in results if r.get('new_decision') == 'NO_TRADE')
n_wait = sum(1 for r in results if r.get('new_decision') == 'WAIT')
n_other = n_total - n_cand - n_no_trade - n_wait

cand_results = [r for r in results if r.get('new_decision') == 'CANDIDATE']
cand_wins = sum(1 for r in cand_results if r.get('outcome') == 'WIN')
cand_wr = cand_wins / n_cand if n_cand > 0 else 0
cr = n_cand / n_total if n_total > 0 else 0
cr_wr = cr * cand_wr

# Lost trades analysis (originally CANDIDATE, now rejected)
lost = [r for r in results if r.get('new_decision') != 'CANDIDATE']
lost_wins = sum(1 for r in lost if r.get('outcome') == 'WIN')
lost_wr = lost_wins / len(lost) if lost else 0
lost_n = len(lost)

# Grade distribution
grades = Counter(r.get('new_setup_grade', '?') for r in results)
confs = Counter(r.get('new_confidence', 0) for r in cand_results)

# Average tokens
avg_in = sum(c['input_tokens'] for c in cost_log) / len(cost_log) if cost_log else 0
avg_out = sum(c['output_tokens'] for c in cost_log) / len(cost_log) if cost_log else 0
avg_cost = sum(c['call_cost'] for c in cost_log) / len(cost_log) if cost_log else 0

# Average confidence
avg_conf = (sum(r.get('new_confidence', 0) for r in cand_results) / n_cand) if n_cand else 0
# Average R multiple for candidates
avg_r = (sum(r.get('r_multiple', 0) for r in cand_results) / n_cand) if n_cand else 0

total_cost = cumulative_cost
monthly_cost = avg_cost * 17  # 17 trades/month expected

# Framework distribution
framework_dist = Counter(r.get('new_framework', '') for r in cand_results)

print(f'  CANDIDATE rate: {cr:.1%} ({n_cand}/{n_total})')
print(f'  WR (new CANDIDATEs): {cand_wr:.1%} (n={n_cand})' if n_cand > 0 else '  WR: n/a (0 candidates)')
print(f'  CR x WR: {cr_wr:.4f}')
print(f'  Lost trades: {lost_n} (WR={lost_wr:.1%})')
print(f'  WAIT count: {n_wait}')


# ── Phase 3: Save outputs ───────────────────────────────
print('\n=== Phase 3: Saving outputs ===')

# Serialize results
safe_rows = []
for r in results:
    row = dict(r)
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
        'model': ACTIVE_MODEL,
        'effort_level': EFFORT,
        'use_effort_param': USE_EFFORT,
        'prompt': 'phase2a_reengineered',
        'n_msos': n_total,
        'total_cost': round(total_cost, 4),
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'baseline_model': 'claude-sonnet-4-20250514',
        'temperature': TEMPERATURE,
        'max_tokens': MAX_TOKENS,
    },
    'summary': {
        'candidate_rate': round(cr, 4),
        'wr': round(cand_wr, 4) if n_cand > 0 else None,
        'cr_wr': round(cr_wr, 4),
        'n_candidate': n_cand,
        'n_no_trade': n_no_trade,
        'n_wait': n_wait,
        'n_other': n_other,
        'n_total': n_total,
        'lost_trades_n': lost_n,
        'lost_trades_wr': round(lost_wr, 4) if lost_n > 0 else None,
        'avg_confidence': round(avg_conf, 1),
        'avg_r_multiple': round(avg_r, 4) if n_cand > 0 else None,
        'avg_input_tokens': round(avg_in, 0),
        'avg_output_tokens': round(avg_out, 0),
        'avg_cost_per_call': round(avg_cost, 6) if cost_log else 0,
        'total_cost': round(total_cost, 4),
        'projected_monthly_cost': round(monthly_cost, 4),
    },
    'distributions': {
        'confidence': dict(confs),
        'grade': dict(grades),
        'framework': dict(framework_dist),
    },
    'rows': safe_rows,
}

out_json = OUT_DIR / f'{TEST_NAME}_results.json'
with open(out_json, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)
print(f'  Saved results JSON: {out_json}')

# Cost log CSV
out_cost = OUT_DIR / f'{TEST_NAME}_cost_log.csv'
if cost_log:
    with open(out_cost, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_log[0].keys()))
        writer.writeheader()
        writer.writerows(cost_log)
    print(f'  Saved cost log: {out_cost}')


# ── Markdown report ─────────────────────────────────────
def pct(v: float | None) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'n/a'
    return f'{v:.1%}'


# Build raw decision log table
decision_rows: list[str] = []
for r in results:
    decision_rows.append(
        f"| {r['trade_id'][:40]:<40} | {r.get('outcome','?'):<8} "
        f"| {r.get('new_decision','?'):<12} | {r.get('new_confidence',0):>3} "
        f"| {r.get('new_setup_grade','?'):>5} |"
    )
decision_table = '\n'.join(decision_rows)

# Distributions as strings
conf_str = ', '.join([f'{k}:{v}' for k, v in sorted(confs.items())]) \
    if confs else 'n/a'
grade_str = ', '.join([f'{k}:{v}' for k, v in grades.items()]) \
    if grades else 'n/a'
framework_str = ', '.join([f'{k}:{v}' for k, v in framework_dist.items()]) \
    if framework_dist else 'n/a'

# Lost trades interpretation
if lost_n > 0:
    if lost_wr > 0.65:
        lost_interp = (f'**OVER-REJECTING good trades** (WR={pct(lost_wr)} > 65%) '
                       f'— still too conservative.')
    elif lost_wr < 0.50:
        lost_interp = (f'**CORRECTLY filtering losers** (WR={pct(lost_wr)} < 50%) '
                       f'— new prompt adds discriminatory value.')
    else:
        lost_interp = (f'**Random rejection** (WR={pct(lost_wr)}, 50-65%) '
                       f'— no discriminatory signal.')
else:
    lost_interp = 'n/a (no lost trades)'

effort_note = ('' if USE_EFFORT
               else '\n> **NOTE:** `output_config` / `effort` parameter was not accepted '
                    'by the SDK. Results are Sonnet 4.6 at default effort.\n')

report = f"""# Phase 2A: {TEST_NAME}

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Model:** {ACTIVE_MODEL}
**Effort:** {EFFORT} (USE_EFFORT={USE_EFFORT})
**Prompt:** Phase 2A re-engineered (scored evaluation, no self-check, quantified tolerances)
**N MSOs:** {n_total}
**Total cost:** ${total_cost:.4f}
**max_tokens:** {MAX_TOKENS}
{effort_note}
---

## Results

| Metric | Value |
|--------|-------|
| CANDIDATE rate | {pct(cr)} ({n_cand}/{n_total}) |
| WR (of CANDIDATEs) | {pct(cand_wr)} (n={n_cand}) |
| CR x WR | {cr_wr:.4f} |
| Lost trades WR | {pct(lost_wr)} (n={lost_n}) |
| WAIT count | {n_wait} |
| Avg confidence | {avg_conf:.1f} |
| Avg output tokens | {avg_out:.0f} |
| Total cost | ${total_cost:.4f} |

---

## Comparison to T2c (old prompt)

| Config | CR | WR | CR*WR |
|--------|----|----|-------|
| Sonnet 4 batch (old prompts) | 55.8% | 61.1% | 0.341 |
| T2c S4.6 high (old prompt) | 17.4% | 52.4% | 0.091 |
| T2c S4.6 max (old prompt) | 16.5% | 60.0% | 0.099 |
| **{TEST_NAME} (NEW prompt)** | **{pct(cr)}** | **{pct(cand_wr)}** | **{cr_wr:.4f}** |

---

## Lost Trades Analysis

New prompt rejected **{lost_n}** trades that the original system accepted (all 121 were originally CANDIDATE).
- WR of rejected trades: {pct(lost_wr)}
- Interpretation: {lost_interp}

> Rule of thumb:
> - WR > 65% → over-rejecting (bad)
> - WR < 50% → filtering correctly (good)
> - WR 50-65% → random noise (neutral)

---

## Decision Breakdown

| Decision | N | % |
|----------|---|---|
| CANDIDATE | {n_cand} | {pct(n_cand/n_total if n_total else 0)} |
| NO_TRADE  | {n_no_trade}  | {pct(n_no_trade/n_total if n_total else 0)} |
| WAIT | {n_wait} | {pct(n_wait/n_total if n_total else 0)} |
| Other (errors, etc.) | {n_other} | {pct(n_other/n_total if n_total else 0)} |

---

## Grade Distribution

{grade_str}

---

## Framework Distribution (CANDIDATEs)

{framework_str}

---

## Confidence Distribution (CANDIDATEs)

{conf_str}

---

## Token Usage

| Metric | Value |
|--------|-------|
| Avg input tokens | {avg_in:.0f} |
| Avg output tokens | {avg_out:.0f} |
| Avg cost per call | ${avg_cost:.5f} |
| Total cost | ${total_cost:.4f} |
| Projected monthly (17 trades/month) | ${monthly_cost:.4f} |

---

## Raw Decision Log

| trade_id | outcome | new_decision | confidence | grade |
|----------|---------|--------------|------------|-------|
{decision_table}
"""

out_report = REPORT_DIR / f'{TEST_NAME}_results_v1.md'
with open(out_report, 'w') as f:
    f.write(report)
print(f'  Saved report: {out_report}')

print(f'\n=== DONE ===')
print(f'  Model: {ACTIVE_MODEL} (effort={EFFORT}, use_effort={USE_EFFORT})')
print(f'  N evaluated: {n_total}')
print(f'  CANDIDATE rate: {pct(cr)} ({n_cand}/{n_total})')
print(f'  WR: {pct(cand_wr)} (n={n_cand})')
print(f'  CR x WR: {cr_wr:.4f}')
print(f'  Total cost: ${total_cost:.4f}')
print(f'  Results: {out_json}')
print(f'  Report:  {out_report}')
