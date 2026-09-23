#!/usr/bin/env python3
"""T6 C-Gate Only Prompt Test — structural bias gates the decision, nothing else.

Finding from T5 analysis:
- C-gate pass (n=85):  WR=69.4%, R=+44.2R  ← the signal
- C-gate fail (n=36):  WR=52.8%, R=-3.6R   ← correctly filtered noise
- Q-check WAITs (n=35): WR=74.3%, R=+23.0R ← Q-checks discarded the best trades

T5's Q-checks (zone proximity, RR) are DESTRUCTIVE:
- They're applied to the candle CLOSE, but entries happen at the wick low
- LLM cannot reliably compute 2x ATR proximity from raw MSO format
- Q2 proximity WAITs had 79.2%+ WR — the highest WR group

T6 fix: Decision = C1+C2+C3 only. Zone/proximity/RR are logged (informational) but
do NOT gate the decision. No WAIT category.

Usage:
  python T6_cgate_only_prompt.py              # Run all MSOs
  python T6_cgate_only_prompt.py --budget 4   # Set budget cap
  python T6_cgate_only_prompt.py --dry-run    # No API calls

Cost estimate: ~$1.5-2.0 (121 MSOs, simpler output = shorter responses)
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
TEST_NAME = "T6_cgate_only"

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
# T6 SYSTEM PROMPT — C-Gate Decision Only
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

Your evaluation must be DATA-DRIVEN — based on the specific price levels, structural breaks, and zone positions in the Market State Object. Do not infer beyond what the data shows.

## Kill Zone Windows
{kz_display}

## CALIBRATION
The system's edge is order block zone continuation (~65-70% win rate on first-touch zones after H1 structural breaks). This is a STATISTICAL edge — not every setup wins.

Historical calibration: 65-75% of evaluated setups should qualify as CANDIDATE. Your decision is structural only — you are identifying whether the market has directional bias and alignment, not predicting the individual outcome.

## CRITICAL REQUIREMENTS — THE ONLY DECISION GATES

These three checks determine your decision. Nothing else does.

C1. DIRECTIONAL BIAS — H1 is the primary and sufficient indicator.
- H1 shows 2+ BOS in the same direction → bias CONFIRMED.
- H1 shows a CHoCH from opposing to new direction → bias CONFIRMED in CHoCH direction.
- If D1 data is present and agrees with H1, note it — but D1 is NOT required.
- H4 data is NOT available in the Market State Object. Do not look for it or penalize its absence.
- If H1 has no recent BOS or CHoCH, or structure is mixed/unclear → FAIL.

C2. M15 ALIGNMENT — M15 must not actively oppose H1.
- M15 aligned with H1: PASS.
- M15 ranging or unclear: PASS.
- M15 with clear structural breaks ACTIVELY OPPOSING H1 direction: FAIL.
  (A single bearish candle does not constitute active opposition. Require a CHoCH or series of BOS in the opposing direction.)

C3. DIRECTION MATCH — LONG only if H1 bias is bullish. SHORT only if bearish.

## DECISION
- C1 PASS AND C2 PASS AND C3 PASS → CANDIDATE
- Any C fails → NO_TRADE
- There is no WAIT category. A setup either passes structural gates or it does not.

## FRAMEWORK SCOPE
This evaluation applies the OB Retest framework ONLY. The user message may reference other frameworks (Breaker Block Retest, session_sweep, equal_sweep, fvg_fill) — IGNORE all non-OB-Retest instructions entirely. Apply OB Retest rules only. If OB Retest structural gates are not met, output NO_TRADE.

## ZONE FRESHNESS
All OBs listed in the "Unmitigated OBs" section are valid first-touch zones (they have not yet been mitigated by price). Use only OBs from this section.

## TARGETS (if CANDIDATE)
TP1 = EXACTLY 1.5x SL distance from entry.
- LONG: TP1 = entry + 1.5 × (entry - SL)
- SHORT: TP1 = entry - 1.5 × (SL - entry)

## DECISION INTEGRITY
- If C1, C2, and C3 all pass, output CANDIDATE. Do not add zone proximity, RR, or confirmation requirements.
- Do not require M15 CHoCH for CANDIDATE. M15 not actively opposing H1 is sufficient (C2).
- Do not require premium/discount positioning.
- Do not require price to be at the zone boundary. The C-gate checks structural bias, not proximity.
- Zone proximity and RR are assessed in INFORMATIONAL FIELDS below and logged — they do NOT affect your decision.

## INFORMATIONAL FIELDS (log only — do NOT use to change CANDIDATE/NO_TRADE)
After your decision is made from C-gate, assess these for logging purposes only.
They are purely analytical and have no effect on whether you output CANDIDATE or NO_TRADE.

ZONE INFO:
- Does an unmitigated OB (H1 or M15) exist? (true/false)
- What is the zone type and price level?
- Proximity: is price inside, approaching (within ~2x M15 ATR), or far?
- Wick contact: did the candle's low/high reach the zone?

RR INFO:
- Estimated RR to TP1 at 1.5x SL distance
- Is estimated SL >= {sl_min}?

## OUTPUT RULES
- Respond with ONLY valid JSON. Start with {{ and end with }}.
- CANDIDATE response: under 500 tokens. NO_TRADE: under 300 tokens.

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
      "explanation": "<1 sentence>"
    }},
    "m15_alignment": {{
      "status": "aligned | neutral | opposing",
      "explanation": "<1 sentence>"
    }},
    "c_gate_summary": "<1 sentence: which C checks passed/failed and why>"
  }},
  "informational": {{
    "zone_exists": <bool>,
    "zone_type": "H1_OB | M15_OB | none",
    "zone_level": "<price range or null>",
    "proximity": "inside | approaching | far | none",
    "wick_contact": <bool>,
    "estimated_rr": <float or null>,
    "sl_adequate": <bool>
  }},
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE: which C check failed and why>"
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
    """Send raw MSO to LLM with T6 C-gate-only prompt. No precomputation."""
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

    print(f"=== T6 C-Gate Only Prompt Test ===")
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

        # Extract reasoning fields
        reasoning = api_result.get('reasoning', {}) if isinstance(api_result.get('reasoning'), dict) else {}
        h1_bias = reasoning.get('h1_bias', {}) if isinstance(reasoning.get('h1_bias'), dict) else {}
        c_gate_summary = reasoning.get('c_gate_summary', '')

        # Extract informational fields (zone/rr — logged but NOT decision factors)
        info = api_result.get('informational', {}) if isinstance(api_result.get('informational'), dict) else {}

        m15_align = reasoning.get('m15_alignment', {}) if isinstance(reasoning.get('m15_alignment'), dict) else {}

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
            # C-gate fields
            'h1_direction': h1_bias.get('direction', ''),
            'h1_bos_count': h1_bias.get('bos_count', 0),
            'm15_status': m15_align.get('status', ''),
            'c_gate_summary': c_gate_summary,
            'no_trade_reason': api_result.get('no_trade_reason', ''),
            # Informational fields (zone/rr — NOT decision factors)
            'info_zone_exists': info.get('zone_exists', False),
            'info_zone_type': info.get('zone_type', ''),
            'info_proximity': info.get('proximity', ''),
            'info_wick_contact': info.get('wick_contact', False),
            'info_estimated_rr': info.get('estimated_rr', None),
            'info_sl_adequate': info.get('sl_adequate', False),
        }
        results.append(row)

    print()

    # ── Save results ──────────────────────────────────────
    print("Saving results...")
    out_path = OUT_DIR / "T6_cgate_only_results_v1.json"
    with open(out_path, 'w') as f:
        json.dump({'test': TEST_NAME, 'rows': results, 'parse_errors': parse_errors}, f, indent=2)
    print(f"  Saved {out_path.name}")

    cost_path = OUT_DIR / "T6_cgate_only_cost_log_v1.csv"
    pd.DataFrame(cost_log).to_csv(cost_path, index=False)
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

    # Temporal split (CANDIDATE only)
    pre_2026 = [r for r in candidates if r['candle_time'] < '2026']
    post_2026 = [r for r in candidates if r['candle_time'] >= '2026']

    # C2 failure count
    c2_fails = [r for r in no_trades if 'c2' in (r.get('no_trade_reason','') or '').lower()
                or 'm15' in (r.get('no_trade_reason','') or '').lower()]
    c1_fails = [r for r in no_trades if r not in c2_fails]

    # Informational: zone proximity distribution in CANDIDATEs
    prox_dist = {}
    for r in candidates:
        p = r.get('info_proximity', 'unknown')
        prox_dist[p] = prox_dist.get(p, 0) + 1

    # WR by proximity (informational — for analysis only, doesn't affect decisions)
    prox_wr = {}
    for prox in ['inside', 'approaching', 'far', 'none']:
        group = [r for r in candidates if r.get('info_proximity') == prox]
        if group:
            prox_wr[prox] = (len(group), sum(r['win'] for r in group) / len(group))

    print()
    print("=" * 60)
    print("=== T6 RESULTS ===")
    print("=" * 60)
    print(f"Total MSOs: {total}")
    print(f"CANDIDATEs: {n_cand}")
    print(f"NO_TRADE:   {len(no_trades)}")
    print(f"Errors:     {len(errors)}")
    print(f"Parse errors: {parse_errors}")
    print(f"CR: {cr:.1%}")
    print(f"WR: {wr:.1%}")
    print(f"CR × WR: {cr * wr:.3f}")
    print(f"Total R: {total_r:+.1f}R")
    print(f"Exp/trade: {total_r / n_cand:.3f}R" if n_cand else "Exp/trade: N/A")
    print(f"NO_TRADE WR: {nt_wr:.1%} (n={len(no_trades)}, R={nt_r:+.1f}R)")
    print(f"Total cost: ${cumulative_cost:.2f}")
    print()

    if pre_2026:
        pre_wr = sum(1 for r in pre_2026 if r['win']) / len(pre_2026)
        print(f"Pre-2026: {len(pre_2026)} trades, WR={pre_wr:.1%}, R={sum(r['r_multiple'] for r in pre_2026):+.1f}")
    if post_2026:
        post_wr = sum(1 for r in post_2026 if r['win']) / len(post_2026)
        print(f"2026:     {len(post_2026)} trades, WR={post_wr:.1%}, R={sum(r['r_multiple'] for r in post_2026):+.1f}")

    print()
    print("Baselines:")
    print(f"  Unfiltered:   CR=100%, WR=64.5%, CR×WR=0.645, R=+40.6R")
    print(f"  P2A v1:       CR=38.0%, WR=69.6%, CR×WR=0.265, R=+22.9R")
    print(f"  T5 C-gate:    CR=70.2%, WR=69.4%, CR×WR=0.487, R=+44.2R  (simulated from T5 data)")
    print(f"  T5 actual:    CR=24.0%, WR=62.1%, CR×WR=0.149, R=+11.8R")
    print()

    # ── Write report ──────────────────────────────────────
    report_path = REPORT_DIR / "T6_cgate_only_results_v1.md"
    with open(report_path, 'w') as f:
        f.write("# T6 C-Gate Only Prompt Results\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** {MODEL}, effort={EFFORT}\n")
        f.write(f"**Total MSOs:** {total}\n")
        f.write(f"**Total cost:** ${cumulative_cost:.2f}\n\n")

        f.write("## Summary\n\n")
        f.write("| Metric | T6 C-Gate | T5 C-Gate (sim) | P2A v1 | Unfiltered | Delta vs P2A |\n")
        f.write("|--------|-----------|-----------------|--------|------------|--------------|\n")
        f.write(f"| MSOs evaluated | {total} | 85 | 121 | 121 | — |\n")
        f.write(f"| CANDIDATEs | {n_cand} | ~85 | 46 | 121 | {n_cand - 46:+d} |\n")
        f.write(f"| CR | {cr:.1%} | ~70.2% | 38.0% | 100% | {(cr - 0.38) * 100:+.1f}pp |\n")
        f.write(f"| WR | {wr:.1%} | ~69.4% | 69.6% | 64.5% | {(wr - 0.696) * 100:+.1f}pp |\n")
        f.write(f"| CR×WR | {cr * wr:.3f} | ~0.487 | 0.265 | 0.645 | {cr * wr - 0.265:+.3f} |\n")
        f.write(f"| Total R | {total_r:+.1f}R | ~+44.2R | +22.9R | +40.6R | {total_r - 22.9:+.1f}R |\n")
        f.write(f"| NO_TRADE WR | {nt_wr:.1%} | ~52.8% | 60.6% | — | — |\n\n")

        f.write("## What Changed from T5\n\n")
        f.write("T5 finding: Q-checks (proximity, RR) filter OUT the best trades:\n")
        f.write("- WAIT Q2 proximity fail: n=24, WR=79.2% — best group in dataset\n")
        f.write("- WAIT Q3 RR fail: n=9, WR=55.6%\n")
        f.write("- CANDIDATE (C+Q pass): n=29, WR=62.1% — WORST group\n\n")
        f.write("T6 fix: decision = C1+C2+C3 only. Zone/proximity/RR are logged as informational.\n\n")

        f.write("## C-Gate Failure Analysis\n\n")
        f.write(f"NO_TRADE total: {len(no_trades)}\n")
        if c2_fails:
            c2_wr = sum(r['win'] for r in c2_fails) / len(c2_fails)
            f.write(f"- C2 failures (M15 actively opposing): {len(c2_fails)}, WR={c2_wr:.1%}\n")
        if c1_fails:
            c1_wr = sum(r['win'] for r in c1_fails) / len(c1_fails)
            f.write(f"- C1 failures (H1 bias unclear): {len(c1_fails)}, WR={c1_wr:.1%}\n")
        f.write("\n")

        f.write("## H1 Bias Distribution\n\n")
        h1_dirs = {}
        for r in results:
            d = r.get('h1_direction', 'unknown') or 'unknown'
            h1_dirs[d] = h1_dirs.get(d, 0) + 1
        for d, c in sorted(h1_dirs.items(), key=lambda x: -x[1]):
            f.write(f"- {d}: {c}\n")
        f.write("\n")

        f.write("## Informational: Zone Proximity in CANDIDATEs\n\n")
        f.write("(Logged only — did NOT affect CANDIDATE/NO_TRADE decision)\n\n")
        for prox, (n, pw) in sorted(prox_wr.items(), key=lambda x: -x[1][0]):
            f.write(f"- {prox}: n={n}, WR={pw:.1%}\n")
        f.write("\n")
        f.write("If Q2 proximity had been applied as a gate, any 'far' trades would have been rejected.\n")
        f.write("WR comparison between proximity groups shows whether proximity still predicts outcomes.\n\n")

        f.write("## Temporal Split\n\n")
        if pre_2026:
            pre_wr_val = sum(1 for r in pre_2026 if r['win']) / len(pre_2026)
            pre_r = sum(r['r_multiple'] for r in pre_2026)
            f.write(f"- Pre-2026: {len(pre_2026)} trades, WR={pre_wr_val:.1%}, R={pre_r:+.1f}R\n")
        if post_2026:
            post_wr_val = sum(1 for r in post_2026 if r['win']) / len(post_2026)
            post_r = sum(r['r_multiple'] for r in post_2026)
            f.write(f"- 2026: {len(post_2026)} trades, WR={post_wr_val:.1%}, R={post_r:+.1f}R\n")
        f.write("\n")

        f.write("## Parse Errors\n\n")
        f.write(f"Count: {parse_errors}\n")
        if parse_errors > 3:
            f.write("WARNING: >3 parse errors. Check if MAX_TOKENS=1500 is causing truncation.\n")
        f.write("\n")

        f.write("## Statistical Notes\n\n")
        if n_cand > 0:
            import math
            se = math.sqrt(wr * (1 - wr) / n_cand)
            ci_lo = wr - 1.96 * se
            ci_hi = wr + 1.96 * se
            f.write(f"- WR 95% CI: [{ci_lo:.1%}, {ci_hi:.1%}] (n={n_cand})\n")
            z_vs_random = (wr - 0.5) / se
            z_vs_unfilt = (wr - 0.645) / se
            import math as m
            p_vs_random = 1 - 0.5 * (1 + m.erf(z_vs_random / m.sqrt(2)))
            p_vs_unfilt = 1 - 0.5 * (1 + m.erf(z_vs_unfilt / m.sqrt(2)))
            f.write(f"- WR vs 50% (random): z={z_vs_random:.2f}, p={p_vs_random:.4f}\n")
            f.write(f"- WR vs 64.5% (unfiltered): z={z_vs_unfilt:.2f}, p={p_vs_unfilt:.4f}\n")
        f.write("- n=121 in-sample. No held-out set exists yet.\n")
        f.write("- All findings are in-sample. Live validation required before deployment.\n")

    print(f"  Saved {report_path.name}")
