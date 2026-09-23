#!/usr/bin/env python3
"""T7 Pure C-Gate Prompt Test — zone info completely absent from prompt.

T6 finding:
- T6 had informational zone fields labeled "do NOT use for decision"
- 22/40 NO_TRADEs were decision integrity violations (DIVs): all C-gates passed
  but LLM rejected based on zone proximity anyway (OB Retest framework requires
  retesting an unmitigated order block / price too far from zone)
- These 22 DIVs had WR=68.2%, +7.5R — good trades thrown away
- Root cause: zone information in prompt primes LLM to evaluate it regardless
  of explicit "informational only" labels

T7 fix:
- REMOVE all zone/proximity/RR content from system prompt entirely
- LLM sees ONLY structural bias data (H1 BOS/CHoCH, M15 alignment)
- MSO still contains OB data in user_message — LLM told to ignore it
- Post-hoc zone analysis by Python from MSO text, not by LLM

T7 target (simulated from T6 if DIVs recovered):
  CR~85%, WR~67%, R~+41.2R

Baselines:
  P2A v1 (deployed): CR=38%,   WR=69.6%, CR×WR=0.265, R=+22.9R
  Unfiltered:        CR=100%,  WR=64.5%, CR×WR=0.645, R=+40.6R
  T6:                CR=66.9%, WR=66.7%, CR×WR=0.446, R=+33.8R
  T6 simulated fix:  CR=~85%,  WR=~67%,  CR×WR=~0.57,  R=~+41.2R

Usage:
  python T7_pure_cgate_prompt.py              # Run all MSOs
  python T7_pure_cgate_prompt.py --budget 4   # Set budget cap
  python T7_pure_cgate_prompt.py --dry-run    # No API calls

Cost estimate: ~$1.5-2.0 (simpler output, no zone fields = shorter responses)
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
TEST_NAME = "T7_pure_cgate"

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

# ── Zone-leak detection keywords ─────────────────────────
ZONE_LEAK_KEYWORDS = [
    'order block', 'unmitigated', 'mitigation', 'fvg', 'breaker block',
    'proximity', 'far from', 'price is far', 'too far', 'not near',
    'price distance', 'ob zone', 'ob retest requires', 'zone requires',
    'retesting', 'not at',
]


# ═══════════════════════════════════════════════════════════════════════════
# T7 SYSTEM PROMPT — Pure C-Gate, No Zone/Proximity/RR Content
# ═══════════════════════════════════════════════════════════════════════════

def get_system_prompt(symbol: str = "XAUUSD") -> str:
    KZ_MAP = {
        "XAUUSD": "- London: 07:00–10:30 UTC\n- New York: 13:00–17:00 UTC (skip first 15 min)",
        "GBPUSD": "- London: 07:00–12:00 UTC\n- New York: 13:00–15:30 UTC",
        "GBPJPY": "- London: 07:00–09:30 UTC\n- New York: 13:00–15:30 UTC",
        "USDJPY": "- London: 07:00–09:30 UTC\n- New York: 13:00–15:30 UTC",
        "US30":   "- London: 08:00–10:30 UTC\n- New York: 13:30–16:00 UTC",
    }
    kz_display = KZ_MAP.get(symbol, KZ_MAP["XAUUSD"])

    return f"""You are a structural bias evaluator for a systematic trading system. Your single task: determine whether H1 shows clear directional bias and M15 does not actively oppose it.

Your evaluation is DATA-DRIVEN — based on structural breaks (BOS and CHoCH) in the Market State Object.

## Active Kill Zones
{kz_display}

## CALIBRATION
Historical base rate: 65–80% of evaluated setups qualify as CANDIDATE. You are identifying structural conditions, not predicting individual outcomes. Match this calibration.

## THE THREE STRUCTURAL GATES

**C1. H1 DIRECTIONAL BIAS** — H1 is the primary and sufficient timeframe.
- 2 or more BOS in the same direction → bias CONFIRMED in that direction.
- CHoCH followed by BOS in the new direction → bias CONFIRMED in the CHoCH direction.
- D1 data (if present) may reinforce H1 but is NOT required.
- H4 data does not exist in this Market State Object — its absence is not a failure.
- No clear recent BOS or CHoCH, or structure genuinely mixed/unclear → C1 FAIL.

**C2. M15 NON-OPPOSITION** — M15 must not be actively working against H1.
- M15 aligned with H1 direction → PASS.
- M15 neutral, ranging, or no clear recent breaks → PASS.
- M15 CHoCH AGAINST H1, or a series of BOS actively opposing H1 → FAIL.
- A single opposing candle or minor pullback does NOT constitute active opposition.

**C3. DIRECTION MATCH**
- H1 bullish → LONG. H1 bearish → SHORT. Mismatch → FAIL.

## DECISION RULE
C1 AND C2 AND C3 all pass → **CANDIDATE**
Any gate fails → **NO_TRADE**
There is no WAIT or HOLD category.

## FRAMEWORK SCOPE
OB Retest framework ONLY. Ignore all other framework instructions in the user message (Breaker Block Retest, session_sweep, equal_sweep, fvg_fill).

## DECISION INTEGRITY
- **If C1, C2, and C3 all pass: output CANDIDATE. There are no other requirements.**
- Do not evaluate price location, distance from any level, or estimated profit potential.
- The Market State Object contains order block and FVG data. **Ignore it for your CANDIDATE/NO_TRADE decision** — use only the BOS/CHoCH structural break data.
- Your entire evaluation is: "Does H1 show clear directional bias? Is M15 not actively opposing it?" That is all.

## TRADE PARAMETERS (if CANDIDATE)
When outputting CANDIDATE, compute approximate trade parameters from M15 price data (recent swings, candle close):
- direction: LONG (bullish) or SHORT (bearish) per H1 bias
- entry_price: current M15 candle close price level
- stop_loss: below the most recent significant swing low (LONG) or above swing high (SHORT)
- take_profit_1: entry ± 1.5 × (entry − stop_loss) distance
- risk_reward_ratio: 1.5
- position_size_lots: 0.01

## OUTPUT RULES
Respond with ONLY valid JSON. Start with {{ and end with }}.
CANDIDATE: under 400 tokens. NO_TRADE: under 250 tokens.

## Output Schema
{{
  "timestamp_utc": "<ISO-8601>",
  "model_used": "{MODEL}",
  "decision": "NO_TRADE | CANDIDATE",
  "confidence_score": <50–90>,
  "framework": "ob_retest | none",
  "kill_zone": "london | ny",
  "reasoning": {{
    "h1_bias": {{
      "direction": "bullish | bearish | unclear",
      "bos_count": <int>,
      "choch_present": <bool>,
      "explanation": "<1 sentence>"
    }},
    "m15_alignment": {{
      "status": "aligned | neutral | opposing",
      "explanation": "<1 sentence>"
    }},
    "c_gate_result": "<1 sentence: all three passed / which gate failed and why>"
  }},
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE: which C gate failed and why>"
}}

When CANDIDATE, set trade_parameters to:
{{
  "direction": "LONG | SHORT",
  "entry_price": <float>,
  "stop_loss": <float>,
  "take_profit_1": <float>,
  "risk_reward_ratio": 1.5,
  "position_size_lots": 0.01
}}

Grounding: Base all structural analysis on BOS and CHoCH events in the Market State Object. Respond with ONLY valid JSON.
"""


# ═══════════════════════════════════════════════════════════════════════════
# POST-HOC ZONE ANALYSIS (Python, not LLM)
# ═══════════════════════════════════════════════════════════════════════════

def parse_mso_zones(user_message: str) -> dict:
    """Extract zone data from MSO text for post-hoc proximity analysis.

    This function parses the MSO user_message to extract H1/M15 OB data and
    current price approximation. Used AFTER LLM evaluation — LLM never sees
    this analysis.
    """
    result = {
        'h1_obs': [],
        'm15_obs': [],
        'h1_atr': None,
        'm15_atr': None,
        'current_price_approx': None,
    }

    # Current price approximation: midpoint of London H/L or Session H/L
    m = re.search(r'London H/L:\s*([\d.]+)/([\d.]+)', user_message)
    if not m:
        m = re.search(r'Session H/L:\s*([\d.]+)/([\d.]+)', user_message)
    if m:
        h, l = float(m.group(1)), float(m.group(2))
        result['current_price_approx'] = (h + l) / 2.0

    def parse_obs_from_section(section_text: str) -> list:
        """Parse Unmitigated OBs from a section of MSO text."""
        obs = []
        # Find the Unmitigated OBs block
        obs_match = re.search(
            r'Unmitigated OBs \(\d+\):(.*?)(?=Unfilled FVGs|Unretested Breaker|P/D:|Avg body:|## |$)',
            section_text, re.DOTALL
        )
        if not obs_match:
            return obs
        obs_text = obs_match.group(1)
        # Parse each OB line: "bullish 2295.52-2280.26 (2024-04-05T15:00)"
        for line in obs_text.strip().split('\n'):
            ob_m = re.search(
                r'(bullish|bearish)\s+([\d.]+)-([\d.]+)\s+\(([^)]+)\)',
                line.strip()
            )
            if ob_m:
                obs.append({
                    'direction': ob_m.group(1),
                    'high': float(ob_m.group(2)),
                    'low': float(ob_m.group(3)),
                    'timestamp': ob_m.group(4),
                })
        return obs

    def parse_atr_from_section(section_text: str) -> float | None:
        atr_m = re.search(r'ATR\(14\):\s*([\d.]+)', section_text)
        return float(atr_m.group(1)) if atr_m else None

    # H1 section
    h1_match = re.search(r'## H1.*?(?=## M15|## Recent|## Current|$)', user_message, re.DOTALL)
    if h1_match:
        h1_text = h1_match.group(0)
        result['h1_obs'] = parse_obs_from_section(h1_text)
        result['h1_atr'] = parse_atr_from_section(h1_text)

    # M15 section
    m15_match = re.search(r'## M15.*?(?=## Recent M15|## Current|$)', user_message, re.DOTALL)
    if m15_match:
        m15_text = m15_match.group(0)
        result['m15_obs'] = parse_obs_from_section(m15_text)
        result['m15_atr'] = parse_atr_from_section(m15_text)

    return result


def compute_posthoc_proximity(current_price: float, obs: list, direction: str, atr: float) -> tuple:
    """Compute proximity of current price to nearest relevant OB.

    Returns (proximity_label, nearest_ob, distance):
      proximity_label: 'inside' | 'approaching' | 'far' | 'none'
      nearest_ob: dict or None
      distance: float or None
    """
    if not obs or current_price is None or atr is None:
        return 'none', None, None

    relevant = [ob for ob in obs if ob['direction'] == direction]
    if not relevant:
        return 'none', None, None

    threshold = 2.0 * atr
    best_prox = None
    best_ob = None
    best_dist = float('inf')

    for ob in relevant:
        ob_high = ob['high']
        ob_low = ob['low']

        # Check if price is inside the OB
        if ob_low <= current_price <= ob_high:
            return 'inside', ob, 0.0

        if direction == 'bullish':
            # For LONG: OB should be below current price (price pulls back to it)
            if current_price > ob_high:
                dist = current_price - ob_high
            else:
                # Bullish OB above current price — unusual, skip for proximity
                continue
        else:  # bearish
            # For SHORT: OB should be above current price
            if current_price < ob_low:
                dist = ob_low - current_price
            else:
                # Bearish OB below current price — unusual, skip
                continue

        if dist < best_dist:
            best_dist = dist
            best_ob = ob

    if best_ob is None:
        return 'none', None, None

    prox = 'approaching' if best_dist <= threshold else 'far'
    return prox, best_ob, best_dist


def compute_posthoc(user_message: str, h1_direction: str) -> dict:
    """Full post-hoc zone analysis for one trade. Returns columns prefixed posthoc_."""
    zones = parse_mso_zones(user_message)

    all_obs = zones['h1_obs'] + zones['m15_obs']
    current_price = zones['current_price_approx']
    atr = zones['m15_atr'] or zones['h1_atr']

    direction = h1_direction if h1_direction in ('bullish', 'bearish') else None
    ob_exists = bool(direction and any(ob['direction'] == direction for ob in all_obs))

    if direction and current_price is not None and atr is not None:
        prox, nearest_ob, dist = compute_posthoc_proximity(current_price, all_obs, direction, atr)
    else:
        prox, nearest_ob, dist = 'none', None, None

    return {
        'posthoc_ob_exists': ob_exists,
        'posthoc_ob_count': sum(1 for ob in all_obs if ob.get('direction') == direction),
        'posthoc_proximity': prox,
        'posthoc_nearest_ob_high': nearest_ob['high'] if nearest_ob else None,
        'posthoc_nearest_ob_low': nearest_ob['low'] if nearest_ob else None,
        'posthoc_price_approx': round(current_price, 5) if current_price else None,
        'posthoc_m15_atr': atr,
        'posthoc_dist_to_ob': round(dist, 4) if dist is not None else None,
        'posthoc_first_touch': True if ob_exists else None,  # All unmitigated OBs are first-touch by definition
    }


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
    """Send raw MSO to LLM with T7 pure C-gate prompt. No zone content in prompt."""
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


def has_zone_leak(text: str) -> bool:
    """Check if text contains zone-related concepts (LLM leaking zone info into decision)."""
    if not text:
        return False
    tl = text.lower()
    return any(kw in tl for kw in ZONE_LEAK_KEYWORDS)


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

    print("=" * 60)
    print(f"=== T7 Pure C-Gate Prompt Test ===")
    print("=" * 60)
    print(f"Model: {MODEL}, effort={EFFORT}, max_tokens={MAX_TOKENS}")
    print(f"Budget cap: ${budget}")
    print(f"Dry run: {dry_run}")
    print()
    print("Design: No zone/proximity/RR in prompt. LLM evaluates H1/M15 structure only.")
    print("Post-hoc: Python parses MSO to compute zone proximity (LLM never sees this).")
    print()

    # ── Load data ─────────────────────────────────────────
    print("Loading data...")
    df_t1 = pd.read_csv(ENTRY_CSV)
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
    print(f"  T1 dataset: {len(df_t1)} trades")

    # Load MSOs by matching candle_time to trades
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
        reasoning = api_result.get('reasoning', {})
        if not isinstance(reasoning, dict):
            reasoning = {}
        h1_bias = reasoning.get('h1_bias', {})
        if not isinstance(h1_bias, dict):
            h1_bias = {}
        m15_align = reasoning.get('m15_alignment', {})
        if not isinstance(m15_align, dict):
            m15_align = {}
        c_gate_result = reasoning.get('c_gate_result', '')

        no_trade_reason = api_result.get('no_trade_reason', '') or ''
        outcome_data = outcomes.get(tid, ('UNKNOWN', 0, 0))

        h1_dir = h1_bias.get('direction', '')
        m15_stat = m15_align.get('status', '')

        # Decision integrity violation: C1 known + C2 not opposing + NO_TRADE
        is_div = (
            h1_dir in ('bullish', 'bearish') and
            m15_stat in ('aligned', 'neutral') and
            decision == 'NO_TRADE'
        )
        zone_leak = has_zone_leak(no_trade_reason) or has_zone_leak(c_gate_result)

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
            'h1_direction': h1_dir,
            'h1_bos_count': h1_bias.get('bos_count', 0),
            'h1_choch_present': h1_bias.get('choch_present', False),
            'm15_status': m15_stat,
            'c_gate_result': c_gate_result,
            'no_trade_reason': no_trade_reason,
            # Integrity analysis
            'is_div': is_div,
            'zone_leak_in_reason': zone_leak,
        }

        # Post-hoc zone analysis (Python only — LLM never sees this)
        if not dry_run and mso_data['user_message']:
            posthoc = compute_posthoc(mso_data['user_message'], h1_dir)
            row.update(posthoc)
        else:
            row.update({
                'posthoc_ob_exists': None,
                'posthoc_ob_count': None,
                'posthoc_proximity': None,
                'posthoc_nearest_ob_high': None,
                'posthoc_nearest_ob_low': None,
                'posthoc_price_approx': None,
                'posthoc_m15_atr': None,
                'posthoc_dist_to_ob': None,
                'posthoc_first_touch': None,
            })

        results.append(row)

    print()

    # ── Save results ──────────────────────────────────────
    print("Saving results...")
    out_path = OUT_DIR / "T7_pure_cgate_results_v1.json"
    with open(out_path, 'w') as f:
        json.dump({'test': TEST_NAME, 'rows': results, 'parse_errors': parse_errors}, f, indent=2)
    print(f"  Saved {out_path.name}")

    cost_path = OUT_DIR / "T7_pure_cgate_cost_log_v1.csv"
    if cost_log:
        pd.DataFrame(cost_log).to_csv(cost_path, index=False)
    else:
        pd.DataFrame(columns=['timestamp', 'trade_id', 'input_tokens', 'output_tokens',
                               'call_cost', 'cumulative_cost']).to_csv(cost_path, index=False)
    print(f"  Saved {cost_path.name}")

    # ── Compute metrics ───────────────────────────────────
    total = len(results)
    candidates = [r for r in results if r['decision'] == 'CANDIDATE']
    no_trades = [r for r in results if r['decision'] == 'NO_TRADE']
    errors = [r for r in results if r['decision'] in ('PARSE_ERROR', 'API_ERROR')]

    n_cand = len(candidates)
    cr = n_cand / total if total > 0 else 0
    cand_wins = sum(1 for r in candidates if r['win'])
    wr = cand_wins / n_cand if n_cand > 0 else 0
    total_r = sum(r['r_multiple'] for r in candidates)

    nt_wr = sum(1 for r in no_trades if r['win']) / len(no_trades) if no_trades else 0
    nt_r = sum(r['r_multiple'] for r in no_trades)

    # Decision Integrity Violations
    divs = [r for r in results if r.get('is_div')]
    zone_leaks = [r for r in results if r.get('zone_leak_in_reason')]
    div_in_no_trades = [r for r in no_trades if r.get('is_div')]

    # C1 vs C2 failure breakdown in NO_TRADEs
    c1_fails = [r for r in no_trades if r.get('h1_direction', '') in ('unclear', '')]
    c2_fails = [r for r in no_trades
                if r.get('h1_direction', '') in ('bullish', 'bearish')
                and r.get('m15_status', '') == 'opposing']
    c3_fails = [r for r in no_trades
                if r.get('h1_direction', '') in ('bullish', 'bearish')
                and r.get('m15_status', '') not in ('opposing', '')
                and 'c3' in (r.get('no_trade_reason', '') or '').lower()]

    # Temporal split (CANDIDATE only)
    pre_2026 = [r for r in candidates if r['candle_time'] < '2026']
    post_2026 = [r for r in candidates if r['candle_time'] >= '2026']

    # Post-hoc zone proximity WR breakdown (CANDIDATEs only)
    posthoc_groups: dict[str, list] = {}
    for r in candidates:
        p = r.get('posthoc_proximity') or 'none'
        posthoc_groups.setdefault(p, []).append(r)

    posthoc_wr: dict[str, tuple] = {}
    for prox, group in posthoc_groups.items():
        pw = sum(r['win'] for r in group) / len(group) if group else 0
        pr = sum(r['r_multiple'] for r in group)
        posthoc_wr[prox] = (len(group), pw, pr)

    # Statistical tests
    se = math.sqrt(wr * (1 - wr) / n_cand) if n_cand > 0 else 0
    ci_lo = wr - 1.96 * se if se else 0
    ci_hi = wr + 1.96 * se if se else 0
    z_vs_50 = (wr - 0.5) / se if se else 0
    z_vs_unf = (wr - 0.645) / se if se else 0

    def _pval_one_tail(z: float) -> float:
        """One-tailed p-value (upper tail)."""
        return 1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))

    p_vs_50 = _pval_one_tail(z_vs_50)
    p_vs_unf = _pval_one_tail(z_vs_unf)

    # ── Console output ────────────────────────────────────
    print()
    print("=" * 65)
    print("=== T7 RESULTS ===")
    print("=" * 65)
    print(f"Total MSOs evaluated : {total}")
    print(f"CANDIDATEs           : {n_cand}")
    print(f"NO_TRADEs            : {len(no_trades)}")
    print(f"Errors/Parse fails   : {len(errors)}")
    print()
    print(f"CR                   : {cr:.1%}")
    print(f"WR (CANDIDATE)       : {wr:.1%}  [{ci_lo:.1%}, {ci_hi:.1%}] 95% CI")
    print(f"CR × WR              : {cr * wr:.3f}")
    print(f"Total R              : {total_r:+.1f}R")
    print(f"Exp/trade            : {total_r / n_cand:.3f}R" if n_cand else "Exp/trade: N/A")
    print(f"NO_TRADE WR          : {nt_wr:.1%} (n={len(no_trades)}, R={nt_r:+.1f}R)")
    print(f"Total cost           : ${cumulative_cost:.2f}")
    print()
    print(f"Decision Integrity Violations (DIVs): {len(div_in_no_trades)}/{len(no_trades)} NO_TRADEs")
    print(f"Zone leaks in reasoning              : {len(zone_leaks)}")
    print(f"T6 had 22 DIVs — T7 target is ~0")
    print()
    print("C-Gate Failure Breakdown (NO_TRADEs):")
    if c1_fails:
        c1_wr = sum(r['win'] for r in c1_fails) / len(c1_fails)
        print(f"  C1 fail (H1 unclear)     : n={len(c1_fails)}, WR={c1_wr:.1%}")
    if c2_fails:
        c2_wr = sum(r['win'] for r in c2_fails) / len(c2_fails)
        print(f"  C2 fail (M15 opposing)   : n={len(c2_fails)}, WR={c2_wr:.1%}")
    if div_in_no_trades:
        div_wr = sum(r['win'] for r in div_in_no_trades) / len(div_in_no_trades)
        div_r = sum(r['r_multiple'] for r in div_in_no_trades)
        print(f"  DIVs (C1+C2 pass, NO_TRADE): n={len(div_in_no_trades)}, WR={div_wr:.1%}, R={div_r:+.1f}R")
    print()
    print("Temporal Split (CANDIDATEs):")
    if pre_2026:
        pre_wr = sum(1 for r in pre_2026 if r['win']) / len(pre_2026)
        print(f"  Pre-2026: {len(pre_2026)} trades, WR={pre_wr:.1%}, R={sum(r['r_multiple'] for r in pre_2026):+.1f}R")
    if post_2026:
        post_wr = sum(1 for r in post_2026 if r['win']) / len(post_2026)
        print(f"  2026:     {len(post_2026)} trades, WR={post_wr:.1%}, R={sum(r['r_multiple'] for r in post_2026):+.1f}R")
    print()
    print("Post-Hoc Zone Proximity (Python, not LLM) — CANDIDATEs:")
    for prox in ['inside', 'approaching', 'far', 'none']:
        if prox in posthoc_wr:
            n, pw, pr = posthoc_wr[prox]
            print(f"  {prox:12s}: n={n:3d}, WR={pw:.1%}, R={pr:+.1f}R")
    print()
    print("Baselines:")
    print(f"  Unfiltered:   CR=100%, WR=64.5%, CR×WR=0.645, R=+40.6R")
    print(f"  P2A v1:       CR=38.0%, WR=69.6%, CR×WR=0.265, R=+22.9R")
    print(f"  T6:           CR=66.9%, WR=66.7%, CR×WR=0.446, R=+33.8R  (22 DIVs)")
    print(f"  T6 sim fix:   CR=~85%,  WR=~67%,  CR×WR=~0.57,  R=~+41.2R (T7 target)")
    print()
    print(f"Statistical: WR vs 50%: z={z_vs_50:.2f}, p={p_vs_50:.4f}")
    print(f"Statistical: WR vs 64.5% (unfiltered): z={z_vs_unf:.2f}, p={p_vs_unf:.4f}")

    # ── Write report ──────────────────────────────────────
    report_path = REPORT_DIR / "T7_pure_cgate_results_v1.md"
    with open(report_path, 'w') as f:
        f.write("# T7 Pure C-Gate Prompt Results\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** {MODEL}, effort={EFFORT}, max_tokens={MAX_TOKENS}\n")
        f.write(f"**Total MSOs:** {total}\n")
        f.write(f"**Total cost:** ${cumulative_cost:.2f}\n\n")

        f.write("## Design\n\n")
        f.write("T7 removes ALL zone/proximity/RR content from the system prompt. The LLM receives:\n")
        f.write("- The full MSO user_message (which still contains OB data)\n")
        f.write("- A system prompt with ONLY: kill zones, C1/C2/C3 structural gates, decision rule\n")
        f.write("- An explicit instruction to IGNORE order block and FVG data for the decision\n\n")
        f.write("Post-hoc zone proximity is computed by Python after evaluations (LLM never sees it).\n\n")
        f.write("**Hypothesis:** Removing zone framing from the prompt will eliminate (or drastically\n")
        f.write("reduce) the 22 DIVs seen in T6, recovering them as CANDIDATEs.\n\n")

        f.write("## Summary Comparison\n\n")
        f.write("| Metric | T7 Pure C-Gate | T6 C-Gate | P2A v1 | Unfiltered | T6 sim fix |\n")
        f.write("|--------|----------------|-----------|--------|------------|------------|\n")
        f.write(f"| MSOs evaluated | {total} | 121 | 121 | 121 | 121 |\n")
        f.write(f"| CANDIDATEs | {n_cand} | 81 | 46 | 121 | ~103 |\n")
        f.write(f"| CR | {cr:.1%} | 66.9% | 38.0% | 100% | ~85% |\n")
        f.write(f"| WR | {wr:.1%} | 66.7% | 69.6% | 64.5% | ~67% |\n")
        f.write(f"| CR×WR | {cr * wr:.3f} | 0.446 | 0.265 | 0.645 | ~0.57 |\n")
        f.write(f"| Total R | {total_r:+.1f}R | +33.8R | +22.9R | +40.6R | ~+41.2R |\n")
        f.write(f"| DIVs (bad NO_TRADEs) | {len(div_in_no_trades)} | 22 | N/A | — | 0 |\n")
        f.write(f"| Zone leaks | {len(zone_leaks)} | 22 | N/A | — | 0 |\n")
        f.write(f"| Parse errors | {len(errors)} | 0 | 21 | — | — |\n\n")

        f.write("## What Changed from T6\n\n")
        f.write("T6 finding: 22/40 NO_TRADEs were DIVs — LLM acknowledged C-gates pass but\n")
        f.write("rejected based on zone proximity despite 'informational only' label:\n")
        f.write("  > 'OB Retest framework requires price to be retesting an unmitigated order block'\n\n")
        f.write("T7 fix: Remove all zone discussion from prompt. System prompt contains:\n")
        f.write("  - NO zone, order block, proximity, distance, ATR, FVG, or RR in decision gates\n")
        f.write("  - ONE instruction: 'The MSO contains OB/FVG data. Ignore it for your decision.'\n")
        f.write("  - Decision is purely: H1 bias + M15 non-opposition\n\n")

        f.write("## Decision Integrity Analysis\n\n")
        f.write(f"**DIVs in T7: {len(div_in_no_trades)}** (T6 had 22)\n\n")
        if div_in_no_trades:
            div_wr_val = sum(r['win'] for r in div_in_no_trades) / len(div_in_no_trades)
            div_r_val = sum(r['r_multiple'] for r in div_in_no_trades)
            f.write(f"DIVs: n={len(div_in_no_trades)}, WR={div_wr_val:.1%}, R={div_r_val:+.1f}R\n\n")
            f.write("DIV details (h1_direction known + m15 not opposing + NO_TRADE):\n\n")
            for r in div_in_no_trades:
                reason = (r.get('no_trade_reason') or '')[:200]
                f.write(f"- {r['trade_id']}: win={r['win']}, R={r['r_multiple']:+.2f}\n")
                f.write(f"  Reason: {reason}\n")
                f.write(f"  Zone leak: {r.get('zone_leak_in_reason', False)}\n\n")
        else:
            f.write("**Zero DIVs detected. T7 eliminated all decision integrity violations.**\n\n")

        f.write(f"**Zone leaks in reasoning: {len(zone_leaks)}**\n")
        if zone_leaks:
            f.write("Trades where LLM mentioned zone-related concepts despite prompt not mentioning them:\n\n")
            for r in zone_leaks:
                reason = (r.get('no_trade_reason') or r.get('c_gate_result') or '')[:200]
                f.write(f"- {r['trade_id']}: decision={r['decision']}, {reason[:150]}\n")
        f.write("\n")

        f.write("## C-Gate Failure Breakdown (NO_TRADEs)\n\n")
        f.write(f"Total NO_TRADEs: {len(no_trades)}\n\n")
        if c1_fails:
            c1_wr_val = sum(r['win'] for r in c1_fails) / len(c1_fails)
            f.write(f"- **C1 fail** (H1 unclear/no structure): n={len(c1_fails)}, WR={c1_wr_val:.1%}, "
                    f"R={sum(r['r_multiple'] for r in c1_fails):+.1f}R\n")
        if c2_fails:
            c2_wr_val = sum(r['win'] for r in c2_fails) / len(c2_fails)
            f.write(f"- **C2 fail** (M15 actively opposing H1): n={len(c2_fails)}, WR={c2_wr_val:.1%}, "
                    f"R={sum(r['r_multiple'] for r in c2_fails):+.1f}R\n")
        if div_in_no_trades:
            div_wr2 = sum(r['win'] for r in div_in_no_trades) / len(div_in_no_trades)
            f.write(f"- **DIVs** (C1+C2 pass, spurious NO_TRADE): n={len(div_in_no_trades)}, "
                    f"WR={div_wr2:.1%}, R={sum(r['r_multiple'] for r in div_in_no_trades):+.1f}R\n")
        remaining = [r for r in no_trades if not r.get('is_div')
                     and r not in c1_fails and r not in c2_fails]
        if remaining:
            rem_wr = sum(r['win'] for r in remaining) / len(remaining)
            f.write(f"- **Other NO_TRADEs**: n={len(remaining)}, WR={rem_wr:.1%}\n")
        f.write("\n")

        f.write("## H1 Bias Distribution\n\n")
        h1_dirs: dict[str, int] = {}
        for r in results:
            d = r.get('h1_direction', 'unknown') or 'unknown'
            h1_dirs[d] = h1_dirs.get(d, 0) + 1
        for d, c in sorted(h1_dirs.items(), key=lambda x: -x[1]):
            f.write(f"- {d}: {c}\n")
        f.write("\n")

        f.write("## Post-Hoc Zone Proximity — CANDIDATEs\n\n")
        f.write("(Computed by Python from MSO text — LLM never saw this)\n\n")
        f.write("This analysis answers: does zone proximity at candle-close correlate with outcome?\n")
        f.write("If 'far' trades have high WR, it confirms proximity-at-close is NOT predictive.\n\n")
        f.write("| Proximity | n | WR | Total R | Interpretation |\n")
        f.write("|-----------|---|----|---------|----------------|\n")
        for prox in ['inside', 'approaching', 'far', 'none']:
            if prox in posthoc_wr:
                n, pw, pr = posthoc_wr[prox]
                interp = {
                    'inside': 'Price already at OB at close',
                    'approaching': 'Price within 2x M15 ATR of OB',
                    'far': 'Price >2x M15 ATR from OB',
                    'none': 'No relevant OB found in MSO',
                }.get(prox, '')
                f.write(f"| {prox} | {n} | {pw:.1%} | {pr:+.1f}R | {interp} |\n")
        f.write("\n")
        f.write("**Expected finding:** 'far' group should have competitive WR (matches T5 finding:\n")
        f.write("Q2 proximity WAITs had 79.2% WR). Proximity at candle-close ≠ proximity at entry.\n")
        f.write("Real entries occur when price reaches the OB during the session, not at close.\n\n")

        f.write("## Temporal Split (CANDIDATEs)\n\n")
        if pre_2026:
            pre_wr_val = sum(1 for r in pre_2026 if r['win']) / len(pre_2026)
            pre_r = sum(r['r_multiple'] for r in pre_2026)
            f.write(f"- Pre-2026: {len(pre_2026)} trades, WR={pre_wr_val:.1%}, R={pre_r:+.1f}R\n")
        if post_2026:
            post_wr_val = sum(1 for r in post_2026 if r['win']) / len(post_2026)
            post_r = sum(r['r_multiple'] for r in post_2026)
            f.write(f"- 2026:     {len(post_2026)} trades, WR={post_wr_val:.1%}, R={post_r:+.1f}R\n")
        f.write("\n")
        f.write("2026 WR decline observed in previous tests reflects known quarterly decay trend\n")
        f.write("(73.2% → 59.4% over 4 quarters, documented in CLAUDE.md validated numbers).\n\n")

        f.write("## Statistical Tests\n\n")
        if n_cand > 0:
            f.write(f"- WR 95% CI: [{ci_lo:.1%}, {ci_hi:.1%}] (n={n_cand})\n")
            f.write(f"- WR vs 50% (random): z={z_vs_50:.2f}, p={p_vs_50:.4f} (one-tail)\n")
            f.write(f"- WR vs 64.5% (unfiltered): z={z_vs_unf:.2f}, p={p_vs_unf:.4f} (one-tail)\n\n")
        f.write("**Limitations:**\n")
        f.write("- n=121 in-sample. All results are post-hoc analysis of the training set.\n")
        f.write("- Bonferroni: T7 is test #7 in sequence. Threshold: p < 0.05/7 = 0.007.\n")
        f.write("- Live validation against new data is the only meaningful test.\n")
        f.write("- n=121 is underpowered to distinguish T7 WR from unfiltered WR (64.5%).\n\n")

        f.write("## Parse Errors\n\n")
        f.write(f"Count: {len(errors)}\n")
        if len(errors) > 3:
            f.write("WARNING: >3 parse errors. Check MAX_TOKENS or API issues.\n")
        f.write("\n")

        f.write("## Next Steps\n\n")
        if len(div_in_no_trades) <= 5 and cr >= 0.78 and wr >= 0.64:
            f.write("**T7 is a deployment candidate.** Get CEO approval before deploying.\n\n")
            f.write("T7 would replace T6/P2A v1 as the live prompt. Evidence:\n")
            f.write(f"- CR×WR = {cr * wr:.3f} vs P2A v1 = 0.265 ({(cr * wr / 0.265 - 1) * 100:.0f}% improvement)\n")
            f.write(f"- Total R = {total_r:+.1f}R vs P2A v1 = +22.9R\n")
            f.write("- DIVs eliminated: fewer spurious rejections\n")
        elif len(div_in_no_trades) > 5:
            f.write(f"**T7 still has {len(div_in_no_trades)} DIVs.** The LLM is reading OB data from the\n")
            f.write("MSO even though the prompt doesn't mention it. Root cause: LLM training prior\n")
            f.write("associates 'OB Retest framework' with proximity requirements regardless of instructions.\n\n")
            f.write("Possible T8 approaches:\n")
            f.write("1. Strip OB data from the user_message before sending to LLM\n")
            f.write("2. Reframe the task as 'structural bias detection' without mentioning 'OB Retest'\n")
            f.write("3. Accept DIVs and filter them post-hoc using Python proximity computation\n")
        else:
            f.write("**Mixed results.** Review DIV count and WR vs baselines before deciding.\n")

    print(f"  Saved {report_path.name}")
    print()
    print(f"Done. Total cost: ${cumulative_cost:.2f}")
