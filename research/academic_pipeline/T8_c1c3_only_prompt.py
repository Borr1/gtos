#!/usr/bin/env python3
"""T8 C1+C3 Only Prompt Test — C2 (M15 alignment) removed from decision.

T6 finding (C2 analysis):
- T6 NO_TRADE total: 40
  - m15_status=opposing (C2 failures): 17, WR=47.1%
  - m15_status=aligned but still NO_TRADE: 23, WR=69.6%
- T6 CANDIDATE: 81, WR=66.7%

T8 removes C2 entirely. Decision = C1 (H1 directional bias) + C3 (direction match) only.
M15 structural data is present in the MSO but is LOGGED, not used as a decision gate.

Hypotheses:
- If C2 adds value: T8 WR < 66.7% (T6) — C2 rejections were noise → accepting them pulls WR down
- If C2 is neutral/destructive: T8 WR >= 66.7%, Total R higher due to more trades
- Definitive test: WR of m15_opposing=True vs False among T8 CANDIDATEs

Baselines:
  P2A v1 (deployed): CR=38.0%, WR=69.6%, CR×WR=0.265, R=+22.9R
  Unfiltered:        CR=100%,  WR=64.5%, CR×WR=0.645, R=+40.6R
  T6 (C1+C2+C3):    CR=66.9%, WR=66.7%, CR×WR=0.446, R=+33.8R
  T7 (C1+C2+C3, no zone info): running in parallel — results TBD

Usage:
  python T8_c1c3_only_prompt.py              # Run all MSOs
  python T8_c1c3_only_prompt.py --budget 4   # Set budget cap
  python T8_c1c3_only_prompt.py --dry-run    # No API calls

Cost estimate: ~$1.5-2.5 (121 MSOs, simpler schema = shorter responses)
"""

import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ── CONFIG ──────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"
EFFORT = "max"
MAX_TOKENS = 1200
TEMPERATURE = 0
BUDGET_CAP = 4.0
TEST_NAME = "T8_c1c3_only"

# ── Paths ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
ENTRY_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'
OUT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'data'
REPORT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'results'
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ── Cost constants (Sonnet 4.6) ─────────────────────────
INPUT_COST_PER_TOK = 3.0 / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')


# ═══════════════════════════════════════════════════════════════════════════
# T8 SYSTEM PROMPT — C1 + C3 ONLY (no C2)
# ═══════════════════════════════════════════════════════════════════════════

def get_system_prompt(symbol: str = "XAUUSD") -> str:
    SL_MIN_MAP = {
        "XAUUSD": "$5.00",
        "GBPUSD": "50 pips",
        "GBPJPY": "50 pips",
        "USDJPY": "50 pips",
        "US30": "50 points",
    }
    KZ_MAP = {
        "XAUUSD": "- London Open: 07:00-10:30 UTC\n- NY Open: 13:00-17:00 UTC (skip 13:00-13:15)",
        "GBPUSD": "- London Open: 07:00-12:00 UTC\n- NY Open: 13:00-15:30 UTC",
        "GBPJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "USDJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "US30": "- London Open: 08:00-10:30 UTC\n- NY Open: 13:30-16:00 UTC",
    }
    sl_min = SL_MIN_MAP.get(symbol, "$5.00")
    kz_display = KZ_MAP.get(symbol, KZ_MAP["XAUUSD"])

    return f"""You are a quantitative setup evaluator for an order block retest trading system. Your task is to determine whether the current M15 candle meets the structural criteria for an entry.

Your evaluation must be DATA-DRIVEN — based on the specific BOS/CHoCH structure in the Market State Object.

## Kill Zone Windows
{kz_display}

## CALIBRATION
The system's edge is order block zone continuation (~65-70% win rate). 80-95% of evaluated setups should qualify as CANDIDATE. The ONLY reason to output NO_TRADE is if H1 directional bias is unclear or mixed.

## CRITICAL REQUIREMENTS — THE ONLY DECISION GATES

Two checks determine your decision. Nothing else.

C1. DIRECTIONAL BIAS — H1 is the primary and SUFFICIENT indicator.
- H1 shows 2+ BOS in the same direction → bias CONFIRMED.
- H1 shows a CHoCH from opposing to new direction → bias CONFIRMED in CHoCH direction.
- If D1 data is present and agrees with H1, note it — but D1 is NOT required.
- H4 data is NOT available in the Market State Object. Do not reference it or penalize its absence.
- If H1 has no recent BOS or CHoCH, or structure is truly mixed/unclear → FAIL C1.

C3. DIRECTION MATCH — LONG only if H1 bias is bullish. SHORT only if bearish.

## DECISION
- C1 PASS AND C3 PASS → CANDIDATE
- Either fails → NO_TRADE
- There is no WAIT category.

If H1 has clear directional bias (C1) and the trade direction matches (C3), output CANDIDATE. No other requirements exist.

## FRAMEWORK SCOPE
This evaluation applies the OB Retest framework ONLY. The user message may reference other frameworks (Breaker Block Retest, session_sweep, equal_sweep, fvg_fill) — IGNORE all non-OB-Retest instructions entirely. Apply OB Retest rules only.

## M15 DATA — LOG ONLY, DO NOT USE FOR DECISION
The MSO contains M15 structural data (BOS events, CHoCH, protected swings). Log the M15 bias direction in your response for analysis purposes, but M15 DOES NOT affect your CANDIDATE/NO_TRADE decision.

Your decision is based solely on H1 structural bias (C1) and direction match (C3).

Do not evaluate M15 opposition, zone existence, zone proximity, risk-reward, order block freshness, FVG fills, or premium/discount positioning. These are NOT decision factors.

The Market State Object contains order block, FVG, and M15 structural data. IGNORE all of it for your CANDIDATE/NO_TRADE decision. Focus ONLY on H1 BOS/CHoCH direction.

## DECISION INTEGRITY
- Do not require M15 alignment or non-opposition for CANDIDATE.
- Do not require price to be near a zone. C1+C3 pass → CANDIDATE. Full stop.
- A trade direction of LONG with H1 bullish bias = CANDIDATE (assuming C1 confirmed).

## TARGETS (if CANDIDATE)
TP1 = EXACTLY 1.5x SL distance from entry.
- LONG: TP1 = entry + 1.5 × (entry - SL)
- SHORT: TP1 = entry - 1.5 × (SL - entry)
Minimum SL: {sl_min}

## OUTPUT RULES
- Respond with ONLY valid JSON. Start with {{ and end with }}.
- CANDIDATE response: under 450 tokens. NO_TRADE: under 250 tokens.

## Output Schema
{{
  "timestamp_utc": "<ISO-8601>",
  "model_used": "{MODEL}",
  "decision": "NO_TRADE | CANDIDATE",
  "confidence_score": <50-90>,
  "framework": "ob_retest | none",
  "kill_zone": "london | ny",
  "reasoning": {{
    "h1_bias": {{
      "direction": "bullish | bearish | unclear",
      "bos_count": <int>,
      "choch_present": <bool>,
      "explanation": "<1 sentence>"
    }},
    "c_gate_result": "<1 sentence: C1+C3 passed / which failed and why>"
  }},
  "logged_m15": {{
    "direction": "bullish | bearish | unclear",
    "opposing_h1": <bool>,
    "explanation": "<1 sentence — M15 structural summary, not used for decision>"
  }},
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE: C1 failed because... / C3 failed because...>"
}}

When CANDIDATE, trade_parameters:
{{
  "direction": "LONG | SHORT",
  "entry_price": <float>,
  "stop_loss": <float>,
  "take_profit_1": <float>,
  "risk_reward_ratio": <float>,
  "position_size_lots": 0.01
}}

## Data Grounding Rules
- Base ALL analysis on the Market State Object data. If a pattern is not in the MSO, it does not exist.
- If you cannot determine H1 direction with confidence, state "unclear" — do not force.
- Respond with ONLY valid JSON.
"""


# ═══════════════════════════════════════════════════════════════════════════
# POST-HOC ZONE PROXIMITY PARSING
# ═══════════════════════════════════════════════════════════════════════════

def parse_mso_proximity(user_message: str, candle_close: float, direction: str = 'LONG') -> dict:
    """Parse H1 Unmitigated OBs from MSO text and compute zone proximity.

    This is a Python-side post-hoc computation — the LLM does NOT assess proximity.
    Used to answer: "Would zone proximity have predicted outcomes in T8 CANDIDATEs?"
    """
    result = {
        'zone_exists': False,
        'proximity': 'none',
        'h1_atr': None,
        'distance': None,
        'nearest_ob_high': None,
        'nearest_ob_low': None,
    }

    if not user_message or candle_close is None or candle_close == 0:
        return result

    # Extract H1 section (up to ## M15)
    h1_match = re.search(r'(## H1.*?)(?=## M15|## Recent M15|## Current Time|$)', user_message, re.DOTALL)
    if not h1_match:
        return result
    h1_text = h1_match.group(1)

    # Parse H1 ATR
    atr_match = re.search(r'ATR\(14\):\s*([\d.]+)', h1_text)
    h1_atr = float(atr_match.group(1)) if atr_match else None
    result['h1_atr'] = h1_atr

    # Parse H1 Unmitigated OBs
    ob_section_match = re.search(
        r'Unmitigated OBs\s*\(\d+\):\s*(.*?)(?=Unfilled FVGs|P/D:|Avg body|ATR|$)',
        h1_text, re.DOTALL
    )
    if not ob_section_match:
        return result

    obs = []
    for m in re.finditer(r'(bullish|bearish)\s+([\d.]+)-([\d.]+)', ob_section_match.group(1)):
        obs.append({
            'dir': m.group(1),
            'high': float(m.group(2)),
            'low': float(m.group(3)),
        })

    if not obs:
        return result

    result['zone_exists'] = True

    # Prefer OBs matching trade direction
    ob_dir = 'bullish' if direction == 'LONG' else 'bearish'
    relevant = [ob for ob in obs if ob['dir'] == ob_dir]
    if not relevant:
        relevant = obs  # fallback to all OBs

    # Find nearest OB to candle close
    min_dist = float('inf')
    nearest = None
    for ob in relevant:
        if ob['low'] <= candle_close <= ob['high']:
            min_dist = 0.0
            nearest = ob
            break
        d = min(abs(candle_close - ob['high']), abs(candle_close - ob['low']))
        if d < min_dist:
            min_dist = d
            nearest = ob

    if nearest is None:
        return result

    result['distance'] = round(min_dist, 4)
    result['nearest_ob_high'] = nearest['high']
    result['nearest_ob_low'] = nearest['low']

    # Classify proximity using 2x H1 ATR threshold
    if min_dist == 0.0:
        result['proximity'] = 'inside'
    elif h1_atr and min_dist <= 2.0 * h1_atr:
        result['proximity'] = 'approaching'
    else:
        result['proximity'] = 'far'

    return result


# ═══════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

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


def evaluate_mso(user_message: str, trade_id: str, symbol: str) -> dict:
    """Send raw MSO to LLM with T8 C1+C3-only prompt. No C2 gate."""
    from anthropic import Anthropic
    client = Anthropic()

    system_prompt = get_system_prompt(symbol)
    time.sleep(0.5)

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
            output_config={'effort': EFFORT},
        )
    except Exception as exc:
        return {'decision': 'API_ERROR', 'error': str(exc)[:300]}

    raw = resp.content[0].text if resp.content else '{}'
    track_cost(trade_id, resp.usage.input_tokens, resp.usage.output_tokens)

    # Parse JSON — direct parse first, then brace-finding fallback
    try:
        cleaned = raw.strip()
        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```\w*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```$', '', cleaned.strip())
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        s = raw.find('{')
        e_idx = raw.rfind('}')
        if s >= 0 and e_idx > s:
            try:
                result = json.loads(raw[s:e_idx + 1])
            except Exception:
                result = {'decision': 'PARSE_ERROR', 'raw': raw[:500]}
        else:
            result = {'decision': 'PARSE_ERROR', 'raw': raw[:500]}

    return result


# ═══════════════════════════════════════════════════════════════════════════
# STATISTICAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def wr_ci_95(wins: int, n: int) -> tuple[float, float]:
    """95% CI for win rate using normal approximation."""
    if n == 0:
        return 0.0, 0.0
    wr = wins / n
    se = math.sqrt(wr * (1 - wr) / n)
    return max(0, wr - 1.96 * se), min(1, wr + 1.96 * se)


def z_test_wr(wins: int, n: int, null_wr: float) -> tuple[float, float]:
    """One-sided z-test: WR > null_wr. Returns (z, p_value)."""
    if n == 0:
        return 0.0, 1.0
    wr = wins / n
    se = math.sqrt(null_wr * (1 - null_wr) / n)
    if se == 0:
        return 0.0, 1.0
    z = (wr - null_wr) / se
    # p = P(Z > z) one-tailed
    p = 0.5 * (1 - math.erf(z / math.sqrt(2)))
    return z, p


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """2x2 Fisher exact test. Two-sided.
    Table: [[a, b], [c, d]]
    Returns (odds_ratio, p_value)."""
    try:
        from scipy.stats import fisher_exact
        result = fisher_exact([[a, b], [c, d]], alternative='two-sided')
        return float(result.statistic), float(result.pvalue)
    except ImportError:
        pass

    # Manual: OR and chi-square approximation
    n = a + b + c + d
    if n == 0:
        return 0.0, 1.0
    or_val = (a * d) / (b * c) if (b > 0 and c > 0) else float('inf')
    # Chi-square with Yates correction
    expected_a = (a + b) * (a + c) / n
    if expected_a == 0:
        return or_val, 1.0
    chi2 = n * ((abs(a * d - b * c) - n / 2) ** 2) / ((a + b) * (c + d) * (a + c) * (b + d))
    # chi2 with 1 df, two-sided — approximate p
    p = math.exp(-chi2 / 2)
    return or_val, min(1.0, p)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    budget = BUDGET_CAP
    for i, arg in enumerate(sys.argv):
        if arg == '--budget' and i + 1 < len(sys.argv):
            budget = float(sys.argv[i + 1])

    if not dry_run and not API_KEY:
        print('ERROR: Set ANTHROPIC_API_KEY and retry.')
        sys.exit(1)

    print(f"=== T8 C1+C3 Only Prompt Test ===")
    print(f"Model: {MODEL}, effort={EFFORT}")
    print(f"Budget cap: ${budget}")
    print(f"Dry run: {dry_run}")
    print()

    # ── Load data ─────────────────────────────────────────
    print("Loading data...")
    df_t1 = pd.read_csv(ENTRY_CSV)
    outcomes = {}
    candle_closes = {}
    directions = {}
    for _, row in df_t1.iterrows():
        outcome = str(row['outcome'])
        if outcome == 'BREAKEVEN':
            outcome = 'LOSS'
        tid = row['trade_id']
        outcomes[tid] = (
            outcome,
            float(row['r_multiple']) if not pd.isna(row['r_multiple']) else 0.0,
            int(row['win']),
        )
        candle_closes[tid] = float(row['candle_close']) if not pd.isna(row.get('candle_close', float('nan'))) else None
        directions[tid] = str(row.get('direction', 'LONG'))
    print(f"  T1 dataset: {len(df_t1)} trades")

    # Load MSOs
    msos = {}
    for fp_path in sorted(DATA_DIR.glob('*_full_prompts.json')):
        with open(fp_path) as f:
            records = json.load(f)
        for rec in records:
            ct = rec.get('candle_time', '')
            if not ct:
                continue
            matching = df_t1[df_t1['candle_time'] == ct]
            if matching.empty:
                continue
            tid = matching.iloc[0]['trade_id']
            if tid in msos:
                continue
            prompt_data = rec.get('prompt', {})
            user_msg = prompt_data.get('user_message', '')
            msos[tid] = {
                'trade_id': str(tid),
                'user_message': user_msg,
                'candle_time': ct,
                'kill_zone': rec.get('kill_zone', ''),
                'symbol': matching.iloc[0]['symbol'],
            }
    print(f"  Loaded {len(msos)} MSOs")
    print()

    # ── Run evaluation ────────────────────────────────────
    print("Running evaluation...")
    results = []
    parse_errors = 0

    for i, (tid, mso_data) in enumerate(sorted(msos.items()), 1):
        if cumulative_cost >= budget:
            print(f"  BUDGET CAP hit at ${cumulative_cost:.2f}")
            break

        symbol = mso_data['symbol']
        print(f"  [{i}/{len(msos)}] {tid} (${cumulative_cost:.2f})")

        if dry_run:
            api_result = {'decision': 'DRY_RUN'}
        else:
            api_result = evaluate_mso(
                mso_data['user_message'],
                tid,
                symbol,
            )

        decision = str(api_result.get('decision', 'PARSE_ERROR')).upper()
        if decision in ('PARSE_ERROR', 'API_ERROR'):
            parse_errors += 1

        confidence = api_result.get('confidence_score', 0)
        framework = api_result.get('framework', '')

        # Extract reasoning fields
        reasoning = api_result.get('reasoning', {}) if isinstance(api_result.get('reasoning'), dict) else {}
        h1_bias = reasoning.get('h1_bias', {}) if isinstance(reasoning.get('h1_bias'), dict) else {}
        c_gate_result = reasoning.get('c_gate_result', '')

        # Extract logged_m15 fields
        logged_m15 = api_result.get('logged_m15', {}) if isinstance(api_result.get('logged_m15'), dict) else {}
        m15_direction = logged_m15.get('direction', '')
        m15_opposing = bool(logged_m15.get('opposing_h1', False))

        outcome_data = outcomes.get(tid, ('UNKNOWN', 0, 0))
        candle_close = candle_closes.get(tid)
        trade_direction = directions.get(tid, 'LONG')

        # Post-hoc zone proximity (Python-parsed from MSO text)
        proximity_data = parse_mso_proximity(
            mso_data['user_message'],
            candle_close or 0.0,
            trade_direction,
        )

        row = {
            'trade_id': tid,
            'candle_time': mso_data['candle_time'],
            'symbol': symbol,
            'kill_zone': mso_data['kill_zone'],
            'outcome': outcome_data[0],
            'r_multiple': outcome_data[1],
            'win': outcome_data[2],
            'decision': decision,
            'confidence': confidence,
            'framework': framework,
            # C-gate fields
            'h1_direction': h1_bias.get('direction', ''),
            'h1_bos_count': h1_bias.get('bos_count', 0),
            'h1_choch_present': h1_bias.get('choch_present', False),
            'c_gate_result': c_gate_result,
            'no_trade_reason': api_result.get('no_trade_reason', ''),
            # Logged M15 (not a decision factor — for post-hoc analysis)
            'm15_logged_direction': m15_direction,
            'm15_logged_opposing': m15_opposing,
            # Post-hoc zone proximity (Python-computed from MSO text)
            'posthoc_zone_exists': proximity_data['zone_exists'],
            'posthoc_proximity': proximity_data['proximity'],
            'posthoc_distance': proximity_data['distance'],
            'posthoc_h1_atr': proximity_data['h1_atr'],
        }
        results.append(row)

    print()

    # ── Save results ──────────────────────────────────────
    print("Saving results...")
    out_path = OUT_DIR / "T8_c1c3_only_results_v1.json"
    with open(out_path, 'w') as f:
        json.dump({'test': TEST_NAME, 'rows': results, 'parse_errors': parse_errors}, f, indent=2)
    print(f"  Saved {out_path.name}")

    cost_path = OUT_DIR / "T8_c1c3_only_cost_log_v1.csv"
    pd.DataFrame(cost_log).to_csv(cost_path, index=False)
    print(f"  Saved {cost_path.name}")

    # ── Compute metrics ───────────────────────────────────
    total = len(results)
    candidates = [r for r in results if r['decision'] == 'CANDIDATE']
    no_trades = [r for r in results if r['decision'] == 'NO_TRADE']
    errors = [r for r in results if r['decision'] in ('PARSE_ERROR', 'API_ERROR')]

    n_cand = len(candidates)
    cr = n_cand / total if total > 0 else 0
    cand_wins = sum(r['win'] for r in candidates)
    wr = cand_wins / n_cand if n_cand > 0 else 0
    total_r = sum(r['r_multiple'] for r in candidates)
    exp_per_trade = total_r / n_cand if n_cand > 0 else 0.0

    nt_wins = sum(r['win'] for r in no_trades)
    nt_wr = nt_wins / len(no_trades) if no_trades else 0
    nt_r = sum(r['r_multiple'] for r in no_trades)

    # ── M15 opposition analysis (key T8 metric) ──────────
    cand_m15_opposing = [r for r in candidates if r.get('m15_logged_opposing')]
    cand_m15_aligned = [r for r in candidates if not r.get('m15_logged_opposing')]

    n_opp = len(cand_m15_opposing)
    n_ali = len(cand_m15_aligned)
    wr_opp = sum(r['win'] for r in cand_m15_opposing) / n_opp if n_opp > 0 else None
    wr_ali = sum(r['win'] for r in cand_m15_aligned) / n_ali if n_ali > 0 else None
    r_opp = sum(r['r_multiple'] for r in cand_m15_opposing)
    r_ali = sum(r['r_multiple'] for r in cand_m15_aligned)

    # Fisher exact test: opposing vs aligned win rates
    fisher_result = None
    if n_opp > 0 and n_ali > 0:
        opp_wins = sum(r['win'] for r in cand_m15_opposing)
        opp_losses = n_opp - opp_wins
        ali_wins = sum(r['win'] for r in cand_m15_aligned)
        ali_losses = n_ali - ali_wins
        or_val, p_val = fisher_exact_2x2(opp_wins, opp_losses, ali_wins, ali_losses)
        fisher_result = {'or': or_val, 'p': p_val}

    # ── Post-hoc zone proximity analysis ─────────────────
    prox_wr = {}
    for prox in ['inside', 'approaching', 'far', 'none']:
        group = [r for r in candidates if r.get('posthoc_proximity') == prox]
        if group:
            g_wins = sum(r['win'] for r in group)
            prox_wr[prox] = {
                'n': len(group),
                'wins': g_wins,
                'wr': g_wins / len(group),
                'r': sum(r['r_multiple'] for r in group),
            }

    # ── Temporal split ────────────────────────────────────
    pre_2026 = [r for r in candidates if r['candle_time'] < '2026']
    post_2026 = [r for r in candidates if r['candle_time'] >= '2026']

    # ── H1 direction distribution ─────────────────────────
    h1_dirs_all = {}
    for r in results:
        d = r.get('h1_direction', 'unknown') or 'unknown'
        h1_dirs_all[d] = h1_dirs_all.get(d, 0) + 1

    # ── NO_TRADE breakdown ────────────────────────────────
    nt_h1_unclear = [r for r in no_trades if 'unclear' in (r.get('h1_direction', '')).lower()]
    nt_c3_fail = [r for r in no_trades if 'c3' in (r.get('no_trade_reason', '') or '').lower()]
    nt_other = [r for r in no_trades if r not in nt_h1_unclear and r not in nt_c3_fail]

    # ── Print summary ─────────────────────────────────────
    print()
    print("=" * 65)
    print("=== T8 RESULTS ===")
    print("=" * 65)
    print(f"Total MSOs:   {total}")
    print(f"CANDIDATEs:   {n_cand}")
    print(f"NO_TRADE:     {len(no_trades)}")
    print(f"Errors:       {len(errors)}")
    print(f"Parse errors: {parse_errors}")
    print()
    print(f"CR:           {cr:.1%}")
    print(f"WR:           {wr:.1%}")
    ci_lo, ci_hi = wr_ci_95(cand_wins, n_cand)
    print(f"WR 95% CI:    [{ci_lo:.1%}, {ci_hi:.1%}]")
    print(f"CR × WR:      {cr * wr:.3f}")
    print(f"Total R:      {total_r:+.1f}R")
    print(f"Exp/trade:    {exp_per_trade:+.3f}R")
    print(f"NO_TRADE WR:  {nt_wr:.1%} (n={len(no_trades)}, R={nt_r:+.1f}R)")
    print(f"Total cost:   ${cumulative_cost:.2f}")
    print()
    print("Baselines:")
    print(f"  Unfiltered:   CR=100%,  WR=64.5%, CR×WR=0.645, R=+40.6R")
    print(f"  P2A v1:       CR=38.0%, WR=69.6%, CR×WR=0.265, R=+22.9R")
    print(f"  T6 (C1+C2+C3):CR=66.9%, WR=66.7%, CR×WR=0.446, R=+33.8R")
    print(f"  T8 (C1+C3):   CR={cr:.1%}, WR={wr:.1%}, CR×WR={cr*wr:.3f}, R={total_r:+.1f}R")
    print()

    print("=== M15 OPPOSITION ANALYSIS (key T8 finding) ===")
    if n_opp > 0:
        ci_lo_opp, ci_hi_opp = wr_ci_95(sum(r['win'] for r in cand_m15_opposing), n_opp)
        print(f"CANDIDATE m15_opposing=True:  n={n_opp}, WR={wr_opp:.1%} [{ci_lo_opp:.1%}, {ci_hi_opp:.1%}], R={r_opp:+.1f}R")
    if n_ali > 0:
        ci_lo_ali, ci_hi_ali = wr_ci_95(sum(r['win'] for r in cand_m15_aligned), n_ali)
        print(f"CANDIDATE m15_opposing=False: n={n_ali}, WR={wr_ali:.1%} [{ci_lo_ali:.1%}, {ci_hi_ali:.1%}], R={r_ali:+.1f}R")
    if fisher_result:
        print(f"Fisher exact: OR={fisher_result['or']:.2f}, p={fisher_result['p']:.4f}")
        if fisher_result['p'] < 0.05:
            print("  → SIGNIFICANT: M15 opposition correlates with outcomes (C2 adds value)")
        else:
            print("  → NOT SIGNIFICANT: M15 opposition does not reliably predict outcomes")
    print()

    if pre_2026:
        pre_wr = sum(r['win'] for r in pre_2026) / len(pre_2026)
        print(f"Pre-2026:  {len(pre_2026)} trades, WR={pre_wr:.1%}, R={sum(r['r_multiple'] for r in pre_2026):+.1f}R")
    if post_2026:
        post_wr = sum(r['win'] for r in post_2026) / len(post_2026)
        print(f"2026:      {len(post_2026)} trades, WR={post_wr:.1%}, R={sum(r['r_multiple'] for r in post_2026):+.1f}R")

    # ── Write report ──────────────────────────────────────
    report_path = REPORT_DIR / "T8_c1c3_only_results_v1.md"
    with open(report_path, 'w') as f:
        f.write("# T8 C1+C3 Only Prompt Results\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** {MODEL}, effort={EFFORT}\n")
        f.write(f"**Test:** C1 (H1 bias) + C3 (direction match) only. C2 (M15 alignment) removed.\n")
        f.write(f"**Total MSOs:** {total}\n")
        f.write(f"**Total cost:** ${cumulative_cost:.2f}\n\n")

        # ── Summary table ──────────────────────────────────
        f.write("## Summary\n\n")
        f.write("| Metric | T8 (C1+C3) | T6 (C1+C2+C3) | P2A v1 | Unfiltered | T8 vs T6 | T8 vs P2A |\n")
        f.write("|--------|-----------|----------------|--------|------------|----------|----------|\n")
        f.write(f"| MSOs evaluated | {total} | 121 | 121 | 121 | — | — |\n")
        f.write(f"| CANDIDATEs | {n_cand} | 81 | 46 | 121 | {n_cand - 81:+d} | {n_cand - 46:+d} |\n")
        f.write(f"| CR | {cr:.1%} | 66.9% | 38.0% | 100% | {(cr - 0.669) * 100:+.1f}pp | {(cr - 0.38) * 100:+.1f}pp |\n")
        f.write(f"| WR | {wr:.1%} | 66.7% | 69.6% | 64.5% | {(wr - 0.667) * 100:+.1f}pp | {(wr - 0.696) * 100:+.1f}pp |\n")
        f.write(f"| CR×WR | {cr * wr:.3f} | 0.446 | 0.265 | 0.645 | {cr * wr - 0.446:+.3f} | {cr * wr - 0.265:+.3f} |\n")
        f.write(f"| Total R | {total_r:+.1f}R | +33.8R | +22.9R | +40.6R | {total_r - 33.8:+.1f}R | {total_r - 22.9:+.1f}R |\n")
        f.write(f"| Exp/trade | {exp_per_trade:+.3f}R | +0.417R | +0.498R | +0.336R | — | — |\n")
        f.write(f"| NO_TRADE WR | {nt_wr:.1%} | 60.0% | 60.6% | — | — | — |\n\n")

        # ── Interpretation ─────────────────────────────────
        f.write("## What T8 Tests\n\n")
        f.write("T6 kept C2 (M15 must not actively oppose H1). In T6:\n")
        f.write("- 40 NO_TRADEs total: 17 had m15_status=opposing (C2 failures, WR=47.1%), ")
        f.write("23 had m15_status=aligned but still NO_TRADE (C1/C3 failures)\n")
        f.write("- 35 of 40 NO_TRADEs had h1_direction=bullish — meaning C2 was the primary gate\n\n")
        f.write("T8 removes C2. Expected:\n")
        f.write("- CR > 85% (C2-rejected trades now accepted)\n")
        f.write("- If C2 adds value: WR drops below 66.7% (more bad trades accepted)\n")
        f.write("- If C2 is noise: WR stays near 66.7%, Total R > T6 due to more trades\n")
        f.write("- Definitive test: Fisher exact on m15_opposing vs m15_aligned WR\n\n")

        # ── M15 opposition analysis ─────────────────────────
        f.write("## M15 Opposition Analysis — Does C2 Add Value?\n\n")
        f.write("This is the primary T8 finding. Among T8 CANDIDATEs, was M15 opposition a predictor?\n\n")
        if n_opp > 0 and n_ali > 0:
            ci_lo_opp, ci_hi_opp = wr_ci_95(sum(r['win'] for r in cand_m15_opposing), n_opp)
            ci_lo_ali, ci_hi_ali = wr_ci_95(sum(r['win'] for r in cand_m15_aligned), n_ali)
            f.write(f"| Group | n | WR | 95% CI | Total R |\n")
            f.write(f"|-------|---|----|--------|--------|\n")
            f.write(f"| m15_opposing=True (C2 would reject) | {n_opp} | {wr_opp:.1%} | [{ci_lo_opp:.1%}, {ci_hi_opp:.1%}] | {r_opp:+.1f}R |\n")
            f.write(f"| m15_opposing=False (C2 would pass) | {n_ali} | {wr_ali:.1%} | [{ci_lo_ali:.1%}, {ci_hi_ali:.1%}] | {r_ali:+.1f}R |\n\n")
            if fisher_result:
                f.write(f"**Fisher exact test:** OR={fisher_result['or']:.2f}, p={fisher_result['p']:.4f}\n\n")
                if fisher_result['p'] < 0.05:
                    f.write("**Verdict: SIGNIFICANT** — M15 opposition is a reliable outcome predictor. ")
                    f.write("C2 adds measurable discriminative value. Removing it hurts quality.\n\n")
                elif fisher_result['p'] < 0.10:
                    f.write("**Verdict: MARGINAL** — weak trend (p<0.10) but not statistically robust at α=0.05. ")
                    f.write("C2 may add slight value but evidence is insufficient to require it.\n\n")
                else:
                    f.write("**Verdict: NOT SIGNIFICANT** — M15 opposition does not reliably predict outcomes ")
                    f.write(f"(p={fisher_result['p']:.4f}). C2 adds noise more than signal. Recommend removing C2.\n\n")
                    if wr_opp is not None and wr_ali is not None:
                        wr_diff = wr_opp - wr_ali
                        f.write(f"WR difference: {wr_diff:+.1%} (opposing vs aligned). ")
                        if abs(wr_diff) < 0.05:
                            f.write("Negligible — C2 adds virtually nothing.\n\n")
                        elif wr_diff < 0:
                            f.write("Direction is correct (opposing has lower WR), but effect too small to be reliable.\n\n")
                        else:
                            f.write("WARNING: Opposing trades have HIGHER WR — C2 was removing good trades.\n\n")
        else:
            f.write("Insufficient data for M15 opposition analysis.\n\n")

        # ── NO_TRADE breakdown ──────────────────────────────
        f.write("## NO_TRADE Breakdown\n\n")
        f.write(f"Total NO_TRADE: {len(no_trades)}\n")
        if nt_h1_unclear:
            nt_u_wr = sum(r['win'] for r in nt_h1_unclear) / len(nt_h1_unclear)
            f.write(f"- H1 unclear/mixed (C1 fail): {len(nt_h1_unclear)}, WR={nt_u_wr:.1%}\n")
        if nt_c3_fail:
            nt_c3_wr = sum(r['win'] for r in nt_c3_fail) / len(nt_c3_fail)
            f.write(f"- C3 direction mismatch: {len(nt_c3_fail)}, WR={nt_c3_wr:.1%}\n")
        if nt_other:
            nt_o_wr = sum(r['win'] for r in nt_other) / len(nt_other)
            f.write(f"- Other/unclassified: {len(nt_other)}, WR={nt_o_wr:.1%}\n")
        f.write("\n")
        f.write("**Expected:** T8 should have very few NO_TRADEs. The only valid rejection ")
        f.write("is H1 bias truly unclear. If T8 still shows many NO_TRADEs, the LLM is ")
        f.write("adding implicit gates despite being told not to.\n\n")

        # ── H1 bias distribution ────────────────────────────
        f.write("## H1 Bias Distribution\n\n")
        for d, c in sorted(h1_dirs_all.items(), key=lambda x: -x[1]):
            f.write(f"- {d}: {c}\n")
        f.write("\n")
        f.write("Expected: ~95%+ bullish (dataset is majority XAUUSD longs in a bull market period).\n\n")

        # ── Post-hoc zone proximity ─────────────────────────
        f.write("## Post-hoc Zone Proximity (Python-computed, NOT LLM-assessed)\n\n")
        f.write("Proximity computed from MSO text by parsing H1 Unmitigated OBs and comparing ")
        f.write("to candle close price. Uses 2× H1 ATR(14) as the 'approaching' threshold.\n\n")
        f.write("This is the definitive test of whether zone proximity predicts outcomes ")
        f.write("(without the LLM proximity-estimation error seen in T5).\n\n")
        if prox_wr:
            f.write("| Proximity | n | WR | Total R | Notes |\n")
            f.write("|-----------|---|----|---------|-------|\n")
            for prox in ['inside', 'approaching', 'far', 'none']:
                if prox in prox_wr:
                    d = prox_wr[prox]
                    ci_l, ci_h = wr_ci_95(d['wins'], d['n'])
                    note = ""
                    if prox == 'inside':
                        note = "Price at zone edge"
                    elif prox == 'approaching':
                        note = "Within 2× ATR"
                    elif prox == 'far':
                        note = "> 2× ATR from zone"
                    f.write(f"| {prox} | {d['n']} | {d['wr']:.1%} [{ci_l:.1%}, {ci_h:.1%}] | {d['r']:+.1f}R | {note} |\n")
            f.write("\n")
            f.write("If 'far' WR < 'inside'/'approaching' WR: zone proximity matters and should be a gate.\n")
            f.write("If 'far' WR ≈ 'inside'/'approaching': T5's proximity rejections were wrong, confirming T6/T8.\n\n")
        else:
            f.write("Insufficient proximity data.\n\n")

        # ── Temporal split ──────────────────────────────────
        f.write("## Temporal Split\n\n")
        if pre_2026:
            p_wr = sum(r['win'] for r in pre_2026) / len(pre_2026)
            p_r = sum(r['r_multiple'] for r in pre_2026)
            f.write(f"- Pre-2026: {len(pre_2026)} trades, WR={p_wr:.1%}, R={p_r:+.1f}R\n")
        if post_2026:
            q_wr = sum(r['win'] for r in post_2026) / len(post_2026)
            q_r = sum(r['r_multiple'] for r in post_2026)
            f.write(f"- 2026: {len(post_2026)} trades, WR={q_wr:.1%}, R={q_r:+.1f}R\n")
        f.write("\n")

        # ── Statistical notes ───────────────────────────────
        f.write("## Statistical Notes\n\n")
        if n_cand > 0:
            ci_lo_main, ci_hi_main = wr_ci_95(cand_wins, n_cand)
            f.write(f"- T8 WR 95% CI: [{ci_lo_main:.1%}, {ci_hi_main:.1%}] (n={n_cand})\n")
            z_rand, p_rand = z_test_wr(cand_wins, n_cand, 0.5)
            z_unfilt, p_unfilt = z_test_wr(cand_wins, n_cand, 0.645)
            z_t6, p_t6 = z_test_wr(cand_wins, n_cand, 0.667)
            f.write(f"- WR vs 50% (random): z={z_rand:.2f}, p={p_rand:.4f}\n")
            f.write(f"- WR vs 64.5% (unfiltered): z={z_unfilt:.2f}, p={p_unfilt:.4f}\n")
            f.write(f"- WR vs 66.7% (T6): z={z_t6:.2f}, p={p_t6:.4f}\n")
        f.write("- n=121 in-sample. All findings are post-hoc on the training set.\n")
        f.write("- Bonferroni: T8 is test #8. Corrected threshold α=0.05/8=0.006.\n")
        f.write("- Live validation is required before deploying any T-series findings.\n\n")

        # ── Parse errors ────────────────────────────────────
        f.write("## Parse Errors\n\n")
        f.write(f"Count: {parse_errors}\n")
        if parse_errors > 3:
            f.write("WARNING: >3 parse errors. Check MAX_TOKENS=1200 vs response length.\n")
        f.write("\n")

        # ── Decision: C2 verdict ────────────────────────────
        f.write("## C2 Value Verdict\n\n")
        f.write("Based on T8 results:\n\n")
        if fisher_result:
            if fisher_result['p'] < 0.05:
                f.write(f"**C2 adds value.** Fisher p={fisher_result['p']:.4f} — M15 opposition significantly ")
                f.write("predicts worse outcomes. T6 (C1+C2+C3) is the better prompt.\n")
            elif fisher_result['p'] < 0.15:
                f.write(f"**C2 is marginal.** Fisher p={fisher_result['p']:.4f} — weak trend toward C2 adding ")
                f.write("value, but insufficient evidence. T6 vs T8 decision requires judgment.\n")
            else:
                f.write(f"**C2 adds no significant value.** Fisher p={fisher_result['p']:.4f}.\n")
                if n_cand > 0 and total_r > 33.8:
                    f.write(f"T8 Total R ({total_r:+.1f}R) > T6 (+33.8R): removing C2 captures more trades ")
                    f.write("without proportional WR loss. C1+C3 is the more permissive and productive filter.\n")
                else:
                    f.write("However, T8 Total R does not clearly exceed T6 (+33.8R). ")
                    f.write("Neither T6 nor T8 has a definitive edge over the other on this dataset.\n")
        else:
            f.write("Insufficient data for C2 verdict.\n")

    print(f"\n  Saved {report_path.name}")
    print(f"\nDone. Total cost: ${cumulative_cost:.2f}")
