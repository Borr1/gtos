#!/usr/bin/env python3
"""T5 Structural-Only Prompt Test — C-gate fix + no scoring.

Root cause findings from P2A v1 analysis:
1. H4 data present in 0% of 31,145 MSOs. D1 in 11.5%.
   Prompt C1 requires D1→H4→"2 of 3 agree" — impossible with only H1.
2. Q1-Q7 score has r=-0.06, p=0.574 correlation with wins — zero signal.
3. Only the structural C-gate predicts outcomes.

T5 fix: Make H1 sufficient for C-gate. Drop Q1-Q7 scoring. Keep structural
quality checks (OB exists, proximity reasonable, RR >= 1.5).

Usage:
  python T5_structural_prompt.py              # Run all MSOs
  python T5_structural_prompt.py --budget 4   # Set budget cap
  python T5_structural_prompt.py --dry-run    # No API calls

Cost estimate: ~$2 (121 MSOs × ~$0.02 each)
"""

import json
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
MAX_TOKENS = 1500
TEMPERATURE = 0
BUDGET_CAP = 4.0
TEST_NAME = "T5_structural"

# ── Paths ─────────────────────────────────────���─────────
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
# T5 SYSTEM PROMPT — Structural Assessment Only
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

    return f"""You are a quantitative setup evaluator for an order block retest trading system. Your task is to determine whether the current M15 candle meets the criteria for an entry.

Your evaluation must be DATA-DRIVEN — based on the specific price levels, structural breaks, and zone positions in the Market State Object. Do not infer beyond what the data shows.

## Kill Zone Windows
{kz_display}

## CALIBRATION
The system's edge is order block zone continuation (~65-70% win rate on first-touch zones after H1 structural breaks). This is a STATISTICAL edge. Your job is structural verification, not outcome prediction.

Historical calibration: 50-70% of evaluated setups should qualify as CANDIDATE. If you reject more than 60%, your thresholds are too strict. The cost of rejecting a valid setup is +0.34R expected value lost.

## CRITICAL REQUIREMENTS (any failure → NO_TRADE)

C1. DIRECTIONAL BIAS — H1 is the primary and sufficient indicator.
- H1 shows 2+ BOS in the same direction → bias CONFIRMED.
- H1 shows a CHoCH from opposing to new direction → bias CONFIRMED in CHoCH direction.
- If D1 data is present and agrees with H1, note it — but D1 is NOT required.
- H4 data is NOT available in the Market State Object. Do not look for it or penalize its absence.
- If H1 has no recent BOS or CHoCH, or structure is mixed/unclear → NO_TRADE.

C2. M15 ALIGNMENT — M15 must not actively oppose H1.
- M15 aligned with H1: pass.
- M15 ranging or unclear: pass.
- M15 with clear structural breaks OPPOSING H1 direction: FAIL.

C3. DIRECTION MATCH — LONG only if H1 bias is bullish. SHORT only if bearish.

## QUALIFYING CHECKS (evaluate after C1-C3 pass)

Q1. ZONE EXISTS: An unmitigated order block (H1 or M15) exists. Check order_blocks where mitigated=false.
- If no unmitigated OB exists → NO_TRADE.

Q2. ZONE PROXIMITY: Price is approaching or at the zone.
- Price INSIDE the zone boundaries: PASS.
- Price within ~2x M15 ATR of the nearest zone boundary: PASS.
- Candle wick/low reached into the zone even if close is above: PASS (this IS a retest).
- Price far beyond 2x ATR with no wick contact: FAIL.
- Use both H1 and M15 OBs. The nearest valid unmitigated zone counts.

Q3. RISK-REWARD: With entry at current price and SL beyond the zone extreme (+ small buffer):
- RR to TP1 (1.5x SL distance) >= 1.5:1: PASS.
- SL must be >= {sl_min}: PASS.
- RR < 1.5 or SL below minimum: FAIL.

## DECISION
- C1+C2+C3 pass AND Q1+Q2+Q3 pass → CANDIDATE
- C1+C2+C3 pass but any Q fails → WAIT (setup developing)
- Any C fails → NO_TRADE

## ZONE FRESHNESS (HARD)
Only trade the FIRST retest. All OBs listed in the "Unmitigated OBs" section are valid (they have not yet been mitigated by price). Use only OBs from this section.

## FRAMEWORK SCOPE
This evaluation applies the OB Retest framework ONLY. The user message may ask you to evaluate both OB Retest and Breaker Block Retest — IGNORE the Breaker Block Retest instruction entirely. Apply OB Retest rules only. If OB Retest criteria are not met, output NO_TRADE. Do not apply Breaker Block Retest rules or let Breaker Block analysis influence your decision.

## TARGETS
TP1 = EXACTLY 1.5x SL distance from entry.
- LONG: TP1 = entry + 1.5 × (entry - SL)
- SHORT: TP1 = entry - 1.5 × (SL - entry)

## DECISION INTEGRITY
- If C1-C3 pass and Q1-Q3 pass, output CANDIDATE. Do not add extra requirements beyond what is listed above.
- Do not require M15 CHoCH for CANDIDATE. M15 not opposing H1 is sufficient (C2).
- Do not require premium/discount positioning. Zone existence and proximity are sufficient.
- The system's edge is in the zone, not in confirmation signals. Trust the zone.

## OUTPUT RULES
- Respond with ONLY valid JSON. Start with {{ and end with }}.
- CANDIDATE response: under 600 tokens. NO_TRADE: under 400 tokens.

## Output Schema
{{
  "timestamp_utc": "<ISO-8601>",
  "model_used": "{MODEL}",
  "decision": "NO_TRADE | CANDIDATE | WAIT",
  "confidence_score": <50-90>,
  "framework": "ob_retest | none",
  "kill_zone": "london | ny",
  "reasoning": {{
    "h1_bias": {{
      "direction": "bullish | bearish | unclear",
      "bos_count": <int>,
      "explanation": "<1 sentence>"
    }},
    "m15_alignment": {{
      "status": "aligned | neutral | opposing",
      "explanation": "<1 sentence>"
    }},
    "zone": {{
      "exists": <bool>,
      "type": "H1_OB | M15_OB | none",
      "level": "<price range>",
      "proximity": "inside | approaching | far",
      "first_touch": <bool>
    }},
    "risk_reward": {{
      "rr": <float>,
      "sl_adequate": <bool>
    }},
    "overall": "<1-2 sentences>"
  }},
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE>",
  "wait_reason": "<if WAIT>"
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
- Base ALL analysis on the Market State Object data. If a price level or pattern is not in the MSO, it does not exist.
- If you cannot determine H1 direction with confidence, state "unclear" — do not force.
- Respond with ONLY valid JSON.
"""


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
    """Send raw MSO to LLM with T5 structural prompt. No precomputation."""
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

    # Parse JSON — try direct parse first, then brace-finding fallback
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

    print(f"=== T5 Structural-Only Prompt Test ===")
    print(f"Model: {MODEL}, effort={EFFORT}")
    print(f"Budget cap: ${budget}")
    print(f"Dry run: {dry_run}")
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

        # Extract structural reasoning
        reasoning = api_result.get('reasoning', {}) if isinstance(api_result.get('reasoning'), dict) else {}
        h1_bias = reasoning.get('h1_bias', {}) if isinstance(reasoning.get('h1_bias'), dict) else {}
        zone = reasoning.get('zone', {}) if isinstance(reasoning.get('zone'), dict) else {}
        rr_info = reasoning.get('risk_reward', {}) if isinstance(reasoning.get('risk_reward'), dict) else {}

        outcome_data = outcomes.get(tid, ('UNKNOWN', 0, 0))

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
            'h1_direction': h1_bias.get('direction', ''),
            'h1_bos_count': h1_bias.get('bos_count', 0),
            'zone_exists': zone.get('exists', False),
            'zone_type': zone.get('type', ''),
            'zone_proximity': zone.get('proximity', ''),
            'zone_first_touch': zone.get('first_touch', False),
            'rr': rr_info.get('rr', 0),
            'no_trade_reason': api_result.get('no_trade_reason', ''),
            'wait_reason': api_result.get('wait_reason', ''),
        }
        results.append(row)

    print()

    # ── Save results ──────────────────────────────────────
    print("Saving results...")
    out_path = OUT_DIR / "T5_structural_results_v1.json"
    with open(out_path, 'w') as f:
        json.dump({'test': TEST_NAME, 'rows': results, 'parse_errors': parse_errors}, f, indent=2)
    print(f"  Saved {out_path.name}")

    cost_path = OUT_DIR / "T5_structural_cost_log_v1.csv"
    pd.DataFrame(cost_log).to_csv(cost_path, index=False)
    print(f"  Saved {cost_path.name}")

    # ── Compute metrics ───────────────────────────────────
    total = len(results)
    candidates = [r for r in results if r['decision'] == 'CANDIDATE']
    no_trades = [r for r in results if r['decision'] == 'NO_TRADE']
    waits = [r for r in results if r['decision'] == 'WAIT']

    n_cand = len(candidates)
    cr = n_cand / total if total > 0 else 0
    cand_wins = sum(1 for r in candidates if r['win'])
    wr = cand_wins / n_cand if n_cand > 0 else 0
    total_r = sum(r['r_multiple'] for r in candidates)

    # Rejected outcomes (for comparison)
    rejected = no_trades + waits
    rej_wr = sum(1 for r in rejected if r['win']) / len(rejected) if rejected else 0

    # Temporal split
    pre_2026 = [r for r in candidates if r['candle_time'] < '2026']
    post_2026 = [r for r in candidates if r['candle_time'] >= '2026']

    print()
    print("=" * 60)
    print("=== T5 RESULTS ===")
    print("=" * 60)
    print(f"Total MSOs: {total}")
    print(f"CANDIDATEs: {n_cand}")
    print(f"NO_TRADE: {len(no_trades)}")
    print(f"WAIT: {len(waits)}")
    print(f"Parse errors: {parse_errors}")
    print(f"CR: {cr:.1%}")
    print(f"WR: {wr:.1%}")
    print(f"CR × WR: {cr * wr:.3f}")
    print(f"Total R: {total_r:+.1f}R")
    print(f"Exp/trade: {total_r / n_cand:.3f}R" if n_cand else "Exp/trade: N/A")
    print(f"Rejected WR: {rej_wr:.1%} (n={len(rejected)})")
    print(f"Total cost: ${cumulative_cost:.2f}")
    print()

    if pre_2026:
        pre_wr = sum(1 for r in pre_2026 if r['win']) / len(pre_2026)
        print(f"Pre-2026: {len(pre_2026)} trades, WR={pre_wr:.1%}, R={sum(r['r_multiple'] for r in pre_2026):+.1f}")
    if post_2026:
        post_wr = sum(1 for r in post_2026 if r['win']) / len(post_2026)
        print(f"2026:     {len(post_2026)} trades, WR={post_wr:.1%}, R={sum(r['r_multiple'] for r in post_2026):+.1f}")
    print()

    print("Baseline comparison:")
    print(f"  P2A v1: CR=38%, WR=69.6%, CR×WR=0.265, R=+22.9")
    print(f"  Unfiltered: CR=100%, WR=64.5%, R=+40.6")
    print()

    # ── Write report ──────────────────────────────────────
    report_path = REPORT_DIR / "T5_structural_results_v1.md"
    with open(report_path, 'w') as f:
        f.write(f"# T5 Structural-Only Prompt Results\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** {MODEL}, effort={EFFORT}\n")
        f.write(f"**Total MSOs:** {total}\n")
        f.write(f"**Total cost:** ${cumulative_cost:.2f}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"| Metric | T5 Structural | P2A v1 Baseline | Unfiltered | Delta vs P2A |\n")
        f.write(f"|--------|---------------|-----------------|------------|-------------|\n")
        f.write(f"| MSOs evaluated | {total} | 121 | 121 | — |\n")
        f.write(f"| CANDIDATEs | {n_cand} | 46 | 121 | {n_cand - 46:+d} |\n")
        f.write(f"| CR | {cr:.1%} | 38.0% | 100% | {(cr - 0.38) * 100:+.1f}pp |\n")
        f.write(f"| WR | {wr:.1%} | 69.6% | 64.5% | {(wr - 0.696) * 100:+.1f}pp |\n")
        f.write(f"| CR×WR | {cr * wr:.3f} | 0.265 | 0.645 | {cr * wr - 0.265:+.3f} |\n")
        f.write(f"| Total R | {total_r:+.1f}R | +22.9R | +40.6R | {total_r - 22.9:+.1f}R |\n")
        f.write(f"| Rejected WR | {rej_wr:.1%} | 60.6% | — | — |\n")
        f.write(f"\n## Key changes from P2A v1\n\n")
        f.write(f"1. C1: H1 is primary and sufficient (D1 optional, H4 removed)\n")
        f.write(f"2. C2: M15 not opposing (H4 reference removed)\n")
        f.write(f"3. Q1-Q7 scoring removed entirely (r=-0.06, p=0.574 — no signal)\n")
        f.write(f"4. Three binary checks replace scoring: zone exists + proximity + RR\n")
        f.write(f"5. M15 CHoCH no longer required for CANDIDATE\n")
        f.write(f"6. Proximity threshold relaxed to 2x ATR (was 1x)\n")
        f.write(f"\n## H1 Bias Distribution\n\n")

        h1_dirs = {}
        for r in results:
            d = r.get('h1_direction', 'unknown')
            h1_dirs[d] = h1_dirs.get(d, 0) + 1
        for d, c in sorted(h1_dirs.items(), key=lambda x: -x[1]):
            f.write(f"- {d}: {c}\n")

        f.write(f"\n## Zone Distribution\n\n")
        zone_types = {}
        for r in candidates:
            zt = r.get('zone_type', 'unknown')
            zone_types[zt] = zone_types.get(zt, 0) + 1
        for zt, c in sorted(zone_types.items(), key=lambda x: -x[1]):
            f.write(f"- {zt}: {c}\n")

        if pre_2026:
            pre_wr_val = sum(1 for r in pre_2026 if r['win']) / len(pre_2026)
            f.write(f"\n## Temporal Split\n\n")
            f.write(f"- Pre-2026: {len(pre_2026)} trades, WR={pre_wr_val:.1%}\n")
        if post_2026:
            post_wr_val = sum(1 for r in post_2026 if r['win']) / len(post_2026)
            f.write(f"- 2026: {len(post_2026)} trades, WR={post_wr_val:.1%}\n")

        f.write(f"\n## Parse Errors\n\nCount: {parse_errors}\n")

    print(f"  Saved {report_path.name}")
