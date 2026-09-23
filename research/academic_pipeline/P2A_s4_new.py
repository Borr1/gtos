#!/usr/bin/env python3
"""
Phase 2A — Prompt Re-Engineering Test: P2A_s4_new
Tests the re-engineered system prompt on Sonnet 4 (old model, no effort param).
Hypothesis: New prompt will increase CR from 55.8% baseline while maintaining WR >= 58%.
Budget: $6. Model: claude-sonnet-4-20250514. Effort: None. max_tokens: 2000. temp: 0.
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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ─── Configuration ────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-20250514"
EFFORT = None           # No effort param for Sonnet 4
TEST_NAME = "P2A_s4_new"
MAX_TOKENS = 2000       # Matches original batch config (NOT 4096 from T2c)
TEMPERATURE = 0
BUDGET_CAP = 6.0

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
BATCH_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
T1_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'
DATA_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'data'
RESULTS_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'results'
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Cost constants (Sonnet 4: $3/MTok in, $15/MTok out) ─────────────────────
INPUT_COST_PER_TOK  = 3.0  / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

# ─── API key check ───────────────────────────────────────────────────────────
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


# ─── NEW SYSTEM PROMPT (Phase 2A re-engineered) ──────────────────────────────
# Template variables: {kz_display}, {sl_min_display}, {zone_max_display}
# Substituted per instrument in get_prompt_for_trade()

NEW_SYSTEM_PROMPT_TEMPLATE = r"""You are a quantitative setup evaluator for an order block retest trading system. Your task is to determine whether the current M15 candle meets the criteria for an entry setup based on price structure, zone quality, and trigger confirmation.

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
```json
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
```

When decision is "CANDIDATE", trade_parameters MUST be:
```json
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
}
```"""


# ─── Template variable substitution ──────────────────────────────────────────

KZ_MAP = {
    "XAUUSD": "- London Open: 07:00-10:30 UTC\n- NY Open: 13:00-17:00 UTC (skip 13:00-13:15)",
    "GBPUSD": "- London Open: 07:00-12:00 UTC\n- NY Open: 13:00-15:30 UTC",
    "GBPJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
    "USDJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
    "US30":   "- London Open: 08:00-10:30 UTC\n- NY Open: 13:30-16:00 UTC",
}

SL_MAP = {
    "XAUUSD": "$5.00",
    "GBPUSD": "50 pips",
    "GBPJPY": "50 pips",
    "USDJPY": "50 pips",
    "US30":   "50 points",
}

ZM_MAP = {
    "XAUUSD": "$15",
    "GBPUSD": "150 pips",
    "GBPJPY": "150 pips",
    "USDJPY": "150 pips",
    "US30":   "150 points",
}


def detect_symbol(trade_id: str, csv_symbol: str = "") -> str:
    """Detect instrument from CSV symbol column or trade_id string."""
    if csv_symbol and csv_symbol != "UNKNOWN":
        return csv_symbol
    tid = trade_id.lower()
    if "gbpusd" in tid:
        return "GBPUSD"
    elif "gbpjpy" in tid:
        return "GBPJPY"
    elif "usdjpy" in tid:
        return "USDJPY"
    elif "us30" in tid:
        return "US30"
    return "XAUUSD"


def get_prompt_for_symbol(symbol: str) -> str:
    """Return the new system prompt with correct template variables for the given symbol."""
    prompt = NEW_SYSTEM_PROMPT_TEMPLATE
    prompt = prompt.replace("{kz_display}", KZ_MAP.get(symbol, KZ_MAP["XAUUSD"]))
    prompt = prompt.replace("{sl_min_display}", SL_MAP.get(symbol, "$5.00"))
    prompt = prompt.replace("{zone_max_display}", ZM_MAP.get(symbol, "$15"))
    return prompt


# ─── API call helper ─────────────────────────────────────────────────────────

def evaluate_mso(system_prompt: str, user_message: str, trade_id: str = "") -> dict:
    """Call Sonnet 4 and return parsed JSON."""
    global cumulative_cost

    if cumulative_cost >= BUDGET_CAP:
        return {
            'decision': 'BUDGET_EXCEEDED',
            'error': f'Cumulative cost ${cumulative_cost:.2f} exceeds ${BUDGET_CAP} cap',
        }

    time.sleep(0.5)  # Rate limiting

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
        )
    except Exception as exc:
        return {'decision': 'API_ERROR', 'error': str(exc)[:300]}

    usage = response.usage
    track_cost(trade_id, usage.input_tokens, usage.output_tokens)

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
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


# ─── Phase 0: Model verification ─────────────────────────────────────────────
print(f'\n=== Phase 0: Model verification ({MODEL}) ===')

try:
    test = client.messages.create(
        model=MODEL,
        max_tokens=100,
        temperature=0,
        messages=[{'role': 'user', 'content': 'Reply with just the word "ready"'}],
    )
    print(f'  Model check OK: {MODEL} → "{test.content[0].text.strip()[:50]}"')
except Exception as exc:
    print(f'  ERROR: {MODEL} not available: {exc}')
    sys.exit(1)


# ─── Phase 1: Load data ──────────────────────────────────────────────────────
print('\n=== Phase 1: Loading batch data ===')

# Load all full_prompts files → keyed by candle_time (proven T2c method)
batch_by_ct: dict = {}
for fp_path in sorted(glob.glob(str(BATCH_DIR / '*_full_prompts.json'))):
    with open(fp_path) as f:
        data = json.load(f)
    for item in data:
        ct = item.get('candle_time', '')
        if not ct:
            continue
        # Extract user_message only — system prompt is REPLACED with new prompt
        prompt_data = item.get('prompt', {})
        user_msg = prompt_data.get('user_message', '')
        if not user_msg:
            continue
        batch_by_ct[ct] = {
            'user_message': user_msg,
        }

print(f'  Loaded {len(batch_by_ct)} batch entries from full_prompts files')

# Load T1 dataset
df_t1 = pd.read_csv(T1_CSV)
print(f'  T1 dataset: {len(df_t1)} trades')

# Join T1 trades with batch prompts via candle_time
selected_msos: list[dict] = []
for _, row in df_t1.iterrows():
    ct = row['candle_time']
    if ct not in batch_by_ct:
        continue

    outcome = str(row['outcome'])
    if outcome == 'BREAKEVEN':
        outcome = 'LOSS'

    r_mult = float(row['r_multiple']) if not pd.isna(row['r_multiple']) else 0.0
    symbol = detect_symbol(str(row['trade_id']), str(row.get('symbol', '')))

    selected_msos.append({
        'trade_id': str(row['trade_id']),
        'candle_time': ct,
        'symbol': symbol,
        'kill_zone': str(row['kill_zone']),
        'outcome': outcome,
        'r_multiple': r_mult,
        'win': int(row['win']),
        'user_message': batch_by_ct[ct]['user_message'],
        'original_decision': 'CANDIDATE',  # All T1 trades were originally executed
    })

n_matched = len(selected_msos)
print(f'  Matched {n_matched} MSOs to batch entries (target: ~121)')
if n_matched < 100:
    print(f'  WARNING: Only {n_matched} matched — check candle_time format.')


# ─── Phase 2: API evaluations ────────────────────────────────────────────────
print(f'\n=== Phase 2: Running {n_matched} evaluations ({MODEL}, max_tokens={MAX_TOKENS}) ===')

results: list[dict] = []

for i, mso in enumerate(selected_msos):
    print(f'  [{i+1}/{n_matched}] {mso["trade_id"]} (${cumulative_cost:.2f})')

    system_prompt = get_prompt_for_symbol(mso['symbol'])

    api_result = evaluate_mso(
        system_prompt,
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
        'original_decision': mso['original_decision'],
        'new_decision': api_result.get('decision', 'PARSE_ERROR'),
        'new_confidence': api_result.get('confidence_score', 0),
        'new_setup_grade': setup_grade,
        'new_framework': api_result.get('framework', ''),
        'new_confidence_computation': api_result.get('confidence_computation', ''),
        'new_response': api_result,
    })

    if cumulative_cost >= BUDGET_CAP:
        print(f'  BUDGET CAP REACHED at ${cumulative_cost:.2f} — stopping.')
        break

print(f'\nCompleted {len(results)} evaluations. Total cost: ${cumulative_cost:.2f}')


# ─── Phase 3: Analysis ───────────────────────────────────────────────────────
print('\n=== Phase 3: Analysis ===')

df = pd.DataFrame(results)
n_total = len(df)

n_candidate = (df['new_decision'] == 'CANDIDATE').sum()
n_no_trade  = (df['new_decision'] == 'NO_TRADE').sum()
n_wait      = (df['new_decision'] == 'WAIT').sum()
n_other     = n_total - n_candidate - n_no_trade - n_wait

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

# Lost trades: originally CANDIDATE (all 121), now rejected
lost_trades = df[df['new_decision'] != 'CANDIDATE']
lost_wr = lost_trades['win'].mean() if len(lost_trades) > 0 else float('nan')
lost_n = len(lost_trades)

# WR by symbol
symbol_stats = {}
for sym in df['symbol'].unique():
    sym_df = df[df['symbol'] == sym]
    sym_cand = sym_df[sym_df['new_decision'] == 'CANDIDATE']
    symbol_stats[sym] = {
        'n_total': len(sym_df),
        'n_candidate': len(sym_cand),
        'cr': len(sym_cand) / len(sym_df) if len(sym_df) > 0 else 0,
        'wr': sym_cand['win'].mean() if len(sym_cand) > 0 else float('nan'),
    }

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
grades = Counter(r.get('new_setup_grade', '?') for r in results)
confs = Counter(r.get('new_confidence', 0) for r in results if r.get('new_decision') == 'CANDIDATE')
frameworks = Counter(r.get('new_framework', '') for r in results if r.get('new_decision') == 'CANDIDATE')

print(f'  CANDIDATE rate: {candidate_rate:.1%} ({n_candidate}/{n_total})')
print(f'  WR (new CANDIDATEs): {wr:.1%} (n={wr_n})' if not np.isnan(wr)
      else '  WR: nan (0 CANDIDATEs)')
print(f'  CR×WR: {cr_wr:.4f}')
print(f'  Lost trades: {lost_n} (WR={lost_wr:.1%})' if not np.isnan(lost_wr)
      else f'  Lost trades: {lost_n}')
print(f'  WAIT count: {n_wait}')


# ─── Phase 4: Save outputs ───────────────────────────────────────────────────
print('\n=== Phase 4: Saving outputs ===')

# Serialize results safely
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
        'model': MODEL,
        'effort_level': str(EFFORT),
        'prompt': 'phase2a_reengineered',
        'test_name': TEST_NAME,
        'n_msos': n_total,
        'total_cost': round(total_cost, 4),
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'max_tokens': MAX_TOKENS,
        'temperature': TEMPERATURE,
        'baseline_model': 'claude-sonnet-4-20250514 (Sonnet 4 batch, old prompts)',
    },
    'summary': {
        'candidate_rate': round(candidate_rate, 4),
        'wr': round(wr, 4) if not np.isnan(wr) else None,
        'cr_wr': round(cr_wr, 4),
        'n_candidate': int(n_candidate),
        'n_no_trade': int(n_no_trade),
        'n_wait': int(n_wait),
        'n_other': int(n_other),
        'n_total': n_total,
        'lost_trades_n': lost_n,
        'lost_trades_wr': round(lost_wr, 4) if not np.isnan(lost_wr) else None,
        'avg_confidence': round(conf_mean, 1),
        'avg_r_multiple': round(avg_r, 4) if not np.isnan(avg_r) else None,
        'avg_input_tokens': round(avg_input, 0),
        'avg_output_tokens': round(avg_output, 0),
        'avg_cost_per_call': round(avg_cost, 6),
        'total_cost': round(total_cost, 4),
        'projected_monthly_cost': round(monthly_cost, 4),
    },
    'distributions': {
        'confidence': dict(confs),
        'grade': dict(grades),
        'framework': dict(frameworks),
    },
    'symbol_breakdown': {
        sym: {k: (round(v, 4) if isinstance(v, float) and not np.isnan(v) else
                  None if isinstance(v, float) and np.isnan(v) else v)
              for k, v in stats_dict.items()}
        for sym, stats_dict in symbol_stats.items()
    },
    'rows': safe_rows,
}

out_json = DATA_DIR / f'{TEST_NAME}_results.json'
with open(out_json, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)
print(f'  Saved results JSON: {out_json}')

# Cost log CSV
out_cost = DATA_DIR / f'{TEST_NAME}_cost_log.csv'
if cost_log:
    with open(out_cost, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(cost_log[0].keys()))
        writer.writeheader()
        writer.writerows(cost_log)
    print(f'  Saved cost log: {out_cost}')


# ─── Markdown report ─────────────────────────────────────────────────────────
def pct(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'n/a'
    return f'{v:.1%}'


def fmt_n(v, n: int = 4) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'n/a'
    return f'{v:.{n}f}'


# Build raw decision log table
decision_rows: list[str] = []
for r in results:
    decision_rows.append(
        f"| {r['trade_id'][:40]:<40} | {r['outcome']:<8} "
        f"| {r['new_decision']:<12} | {r.get('new_confidence',0):>4} "
        f"| {r.get('new_setup_grade',''):>5} | {r.get('new_framework',''):>15} |"
    )
decision_table = '\n'.join(decision_rows)

# Grade/confidence/framework distribution strings
grade_str = ', '.join([f'{k}: {v}' for k, v in sorted(grades.items())]) if grades else 'n/a'
conf_str = ', '.join([f'{k}: {v}' for k, v in sorted(confs.items())]) if confs else 'n/a'
framework_str = ', '.join([f'{k}: {v}' for k, v in frameworks.items()]) if frameworks else 'n/a'

# Lost trades interpretation
if not np.isnan(lost_wr) and lost_n > 0:
    if lost_wr > 0.65:
        lost_interp = (f'**OVER-REJECTING good trades** (WR={pct(lost_wr)} > 65%) '
                       f'— prompt too conservative.')
    elif lost_wr < 0.50:
        lost_interp = (f'**CORRECTLY filtering losers** (WR={pct(lost_wr)} < 50%) '
                       f'— new prompt adds discriminatory value.')
    else:
        lost_interp = (f'**Random rejection** (WR={pct(lost_wr)}, 50-65%) '
                       f'— no discriminatory signal.')
else:
    lost_interp = 'n/a (no lost trades or no data)'

# Symbol breakdown table
symbol_rows = []
for sym, ss in sorted(symbol_stats.items()):
    symbol_rows.append(
        f"| {sym} | {ss['n_total']} | {ss['n_candidate']} | {pct(ss['cr'])} | {pct(ss['wr'])} |"
    )
symbol_table = '\n'.join(symbol_rows)

# Score computation examples (first 5 CANDIDATEs)
score_examples = []
for r in results:
    if r.get('new_decision') == 'CANDIDATE' and r.get('new_confidence_computation'):
        score_examples.append(
            f"- **{r['trade_id'][:35]}**: {r['new_confidence_computation']}"
        )
    if len(score_examples) >= 5:
        break
score_section = '\n'.join(score_examples) if score_examples else 'No CANDIDATEs with score breakdowns.'

report = f"""# Phase 2A: {TEST_NAME}

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Model:** {MODEL}
**Effort:** {EFFORT or 'none'}
**Prompt:** Phase 2A re-engineered (scored evaluation, no self-check, quantified tolerances)
**N MSOs:** {n_total}
**Total cost:** ${total_cost:.4f}
**max_tokens:** {MAX_TOKENS}

---

## Results

| Metric | Value |
|--------|-------|
| CANDIDATE rate | {pct(candidate_rate)} ({n_candidate}/{n_total}) |
| WR (of CANDIDATEs) | {pct(wr)} (n={wr_n}) |
| CR x WR | {fmt_n(cr_wr)} |
| Lost trades WR | {pct(lost_wr)} (n={lost_n}) |
| WAIT count | {n_wait} |
| Avg output tokens | {avg_output:.0f} |
| Total cost | ${total_cost:.4f} |
| Projected monthly (17 trades/mo) | ${monthly_cost:.4f} |

---

## Comparison to Baselines

| Config | CR | WR | CR*WR |
|--------|----|----|-------|
| Sonnet 4 batch (old prompts) | 55.8% | 61.1% | 0.341 |
| S4.6 medium (old prompts) | 13.2% | 50.0% | 0.066 |
| S4.6 high (old prompts) | 17.4% | 52.4% | 0.091 |
| S4.6 max (old prompts) | 16.5% | 60.0% | 0.099 |
| **{TEST_NAME} (NEW prompt)** | **{pct(candidate_rate)}** | **{pct(wr)}** | **{fmt_n(cr_wr)}** |

---

## Lost Trades Analysis

New prompt rejected **{lost_n}** trades that Sonnet 4 originally accepted (all 121 were original CANDIDATEs).
- WR of rejected trades: {pct(lost_wr)}
- Interpretation: {lost_interp}

> Rule of thumb:
> - WR > 65% → over-rejecting (bad)
> - WR < 50% → filtering correctly (good)
> - WR 50-65% → random noise (neutral)

---

## Symbol Breakdown

| Symbol | N total | N CANDIDATE | CR | WR |
|--------|---------|-------------|----|----|
{symbol_table}

---

## Decision Breakdown

| Decision | N | % |
|----------|---|---|
| CANDIDATE | {n_candidate} | {pct(n_candidate/n_total if n_total else 0)} |
| NO_TRADE  | {n_no_trade}  | {pct(n_no_trade/n_total if n_total else 0)} |
| WAIT      | {n_wait}      | {pct(n_wait/n_total if n_total else 0)} |
| Other (errors) | {n_other} | {pct(n_other/n_total if n_total else 0)} |

---

## Grade Distribution

{grade_str}

---

## Confidence Distribution (CANDIDATEs only)

{conf_str}

---

## Framework Distribution (CANDIDATEs only)

{framework_str}

---

## Score Computation Examples (first 5 CANDIDATEs)

{score_section}

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

## Raw Decision Log

| trade_id | outcome | new_decision | conf | grade | framework |
|----------|---------|--------------|------|-------|-----------|
{decision_table}
"""

out_report = RESULTS_DIR / f'{TEST_NAME}_results_v1.md'
with open(out_report, 'w') as f:
    f.write(report)
print(f'  Saved report: {out_report}')

print('\n=== DONE ===')
print(f'  Model: {MODEL} (effort={EFFORT})')
print(f'  N evaluated: {n_total}')
print(f'  CANDIDATE rate: {pct(candidate_rate)} ({n_candidate}/{n_total})')
print(f'  WR: {pct(wr)} (n={wr_n})')
print(f'  CR×WR: {fmt_n(cr_wr)}')
print(f'  Total cost: ${total_cost:.4f}')
print(f'  Results: {out_json}')
print(f'  Report:  {out_report}')
