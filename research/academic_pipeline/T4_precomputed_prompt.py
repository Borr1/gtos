#!/usr/bin/env python3
"""T4 Pre-Computed Prompt Test — Run pre-computation on 121 MSOs.

This script:
1. Loads MSOs from batch_api files
2. Pre-computes arithmetic (Q3-Q7 + bonus) using precompute_mso.py
3. Sends the pre-computed summary to the LLM for structural judgment (C1-C3, Q1-Q2)
4. Compares results to baseline (P2A v1: CR=38%, WR=69.6%)

Usage:
  python T4_precomputed_prompt.py              # Run all 121 MSOs
  python T4_precomputed_prompt.py --budget 6   # Set budget cap
  python T4_precomputed_prompt.py --dry-run    # Just pre-compute, no API calls

Cost estimate: ~$5-6 (same as T3 variants)
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from precompute_mso import precompute

# ── CONFIG ──────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"
EFFORT = "max"
MAX_TOKENS = 2000
TEMPERATURE = 0
BUDGET_CAP = 7.0
TEST_NAME = "T4_precomputed"

# ── Paths ───────────────────────────────────────────────
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
# SYSTEM PROMPT FOR PRE-COMPUTED INPUT
# ═══════════════════════════════════════════════════════════════════════════

def get_system_prompt(symbol: str = "XAUUSD") -> str:
    """Build the system prompt for pre-computed evaluation."""

    # Symbol-specific configuration
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

    return f"""You are a quantitative setup evaluator for an order block retest trading system.

You will receive a COMPUTED ARITHMETIC section containing verified calculations (distances, ratios, RR geometry, SL checks). Use these exact numbers instead of trying to compute from raw prices — the arithmetic has already been done correctly.

Your job is to do ALL scoring yourself (Q1–Q7 + bonus), using the computed facts as inputs.

## STEP 1: STRUCTURAL JUDGMENT (C1/C2/C3)
Interpret the H1 and M15 structural data to establish directional bias.
- C1. DIRECTIONAL BIAS: Use H1 structure as primary. If H1 is clearly bullish (recent BOS/CHoCH in bullish direction), bias is bullish. If bearish, bias is bearish. If unclear, check M15. If both unclear → NO_TRADE.
- C2. ALIGNMENT: Check that M15 does not actively oppose H1 direction. M15 unclear/ranging is acceptable.
- C3. DIRECTION MATCH: Trade direction must match bias. LONG for bullish, SHORT for bearish.

## STEP 2: SCORE Q1–Q7 + BONUS

**Q1 (0–15): H1 structural break quality**
- BOS (break of protected swing in trend direction): 15 points
- CHoCH (shift from opposing to aligned direction): 12 points
- No confirmed break in aligned direction: 0 points

**Q2 (0–20): Zone identification**
- Unmitigated OB from the impulse that caused the structural break: 20 points
- Not present or mitigated: 0 points

**Q3 (0–15): Zone proximity** — use the computed distance
- Price INSIDE zone: 15 points
- Price approaching zone (within ~1–2 ATR, OR candle wick/low reached into zone even if close is above): 10 points
- Zone identified but price has moved significantly away: 5 points
- No relevant zone: 0 points
- NOTE: The computed distance uses the close price. If the raw MSO shows the candle LOW touched the zone, that IS a retest even if the close is above — score as approaching (10) or inside (15).

**Q4 (0–10): Premium/discount position** — use the computed label
- DISCOUNT for longs / PREMIUM for shorts: 10 points
- EQUILIBRIUM: 5 points
- Wrong side (PREMIUM for longs / DISCOUNT for shorts): 0 points

**Q5 (0–15): M15 confirmation** — use computed body ratio and CHoCH detection
- CHoCH detected AND body ratio >= 1.5x average: 15 points (STRONG)
- CHoCH detected AND body ratio >= 1.2x average: 10 points (MODERATE)
- No CHoCH OR body ratio < 1.2x: 0 points (WEAK)

**Q6 (0–10): Risk/reward** — use the computed RR
- RR >= 1.5:1 (computed value): 10 points
- RR < 1.5:1: 0 points

**Q7 (0–5): SL adequacy** — use the computed SL/ATR and minimum checks
- Both SL/ATR >= 1.5x AND SL >= instrument minimum: 5 points
- Either check fails: 0 points

**Bonus (0–10): Context enhancers** — use computed facts
- First touch (unmitigated zone): +5 points
- M15 FVG overlaps zone: +3 points
- Compact impulse (<=7 H1 candles, if detectable): +2 points

## STEP 3: DECISION
Total = Q1 + Q2 + Q3 + Q4 + Q5 + Q6 + Q7 + bonus
- Total >= 65 AND C1–C3 all pass → CANDIDATE
- Total 45–64 → WAIT
- Total < 45 OR any C fail → NO_TRADE

## CALIBRATION
Based on validated historical performance:
- Approximately 40–60% of setups reaching this evaluation qualify as CANDIDATE.
- The system's edge comes from OB zone continuation mechanics (~65–70% win rate).
- Over-rejection costs +0.20R expected value. Both false positives and false negatives have real costs.
- If rejecting >70% of evaluated setups, recalibrate upward. If accepting >60%, tighten judgment.

## Kill Zone Windows
{kz_display}

## ZONE FRESHNESS RULE (HARD)
Only trade the FIRST retest of an OB zone. If mitigated=true in the MSO → NO_TRADE.
First-touch continuation rate: 72.7%; subsequent touches: 31.5%.

## TARGETS
TP1 MUST be EXACTLY 1.5x SL distance from entry:
  - LONG: TP1 = entry + 1.5 x (entry - SL)
  - SHORT: TP1 = entry - 1.5 x (SL - entry)

## CONFIDENCE SCORE
Map your evaluation score to confidence:
  - Score 65-74 → confidence 65-72
  - Score 75-84 → confidence 73-80
  - Score 85+ → confidence 81-90
Show your score breakdown in confidence_computation.

## SETUP GRADE
  - Score 85+: A+
  - Score 75-84: A
  - Score 65-74: B+
  - Score 50-64: B
  - Score < 50: C

## DECISION INTEGRITY
- Score ALL seven questions yourself — the COMPUTED ARITHMETIC section gives you the facts, not the scores.
- If your total is >= 65 and C1–C3 all pass, output CANDIDATE. Do not invent additional concerns beyond the scoring framework. Trust the score.
- The computed distances, ratios, and RR values are verified arithmetic — use them as-is. The interpretation (how to score) is yours.

## OUTPUT RULES
- Respond with ONLY valid JSON matching the schema below.
- For NO_TRADE: state which requirement failed or the score breakdown. Under 500 tokens.
- For CANDIDATE: include full score breakdown. Under 800 tokens.
- If C1 or C2 fail, output minimal JSON: decision, kill_zone, framework="none", no_trade_reason only.

## Data Grounding Rules
- Base ALL analysis on the data in the pre-computed summary AND raw MSO data.
- If you cannot determine structure direction, state "unclear" — do not force a classification.
- Respond with ONLY valid JSON. Start with {{ and end with }}.

## Output Schema
{{
  "timestamp_utc": "<ISO-8601>",
  "model_used": "{MODEL}",
  "decision": "NO_TRADE | CANDIDATE | WAIT",
  "confidence_score": <0-100>,
  "confidence_computation": "<Q1=X Q2=Y Q3=Z Q4=A Q5=B Q6=C Q7=D bonus=E = total → conf>",
  "framework": "ob_retest | breaker_retest | none",
  "kill_zone": "london | ny",
  "frameworks_evaluated": {{
    "ob_retest": {{"qualified": <bool>, "score": <int>, "reason": "<summary>"}},
    "breaker_retest": {{"qualified": <bool>, "score": <int>, "reason": "<summary>"}}
  }},
  "reasoning": {{
    "daily_bias": {{"direction": "bullish|bearish|ranging", "confidence": "high|medium|low", "explanation": "<1 sentence>"}},
    "h4_alignment": {{"aligned": <bool>, "explanation": "<1 sentence>"}},
    "h1_setup": {{"poi_identified": <bool>, "poi_type": "OB|none", "poi_price_level": <float>, "zone": "premium|discount|neutral", "causing_event_type": "BOS|CHoCH|unknown", "explanation": "<1 sentence>"}},
    "m15_confirmation": {{"choch_detected": <bool>, "displacement_quality": "strong|medium|weak|none", "explanation": "<1 sentence>"}},
    "setup_grade": "A+|A|B+|B|C",
    "overall_reasoning": "<2 sentences max>"
  }},
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE>",
  "wait_reason": "<if WAIT>",
  "precomputed_override": null
}}

When CANDIDATE, trade_parameters:
{{
  "direction": "LONG|SHORT",
  "entry_price": <float>,
  "stop_loss": <float>,
  "take_profit_1": <float>,
  "risk_reward_ratio": <float>,
  "position_size_lots": 0.01
}}
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


def evaluate_mso_with_precompute(
    user_message: str,
    trade_id: str,
    symbol: str,
    candle_close: float,
    candle_open: float | None = None,
    dry_run: bool = False,
) -> tuple[dict, dict]:
    """
    Pre-compute the MSO and evaluate via API.

    Returns: (api_result, precomputed_values)
    """
    # Calculate body if we have both candle prices
    current_body = None
    if candle_close and candle_open and not pd.isna(candle_open):
        current_body = abs(candle_close - candle_open)

    # Pre-compute
    computed, summary = precompute(
        user_message,
        symbol=symbol,
        current_price=float(candle_close),
        current_body=current_body,
    )

    if dry_run:
        # Return mock result without API call
        return {
            'decision': 'DRY_RUN',
            'q3_label': computed.get('q3_label'),
            'q3_distance_atr': computed.get('q3_distance_atr'),
        }, computed

    # API call
    from anthropic import Anthropic
    client = Anthropic()

    system_prompt = get_system_prompt(symbol)

    time.sleep(0.5)

    create_kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{'role': 'user', 'content': summary}],
    )
    create_kwargs['output_config'] = {'effort': EFFORT}

    try:
        response = client.messages.create(**create_kwargs)
    except Exception as exc:
        return {'decision': 'API_ERROR', 'error': str(exc)[:300]}, computed

    usage = response.usage
    track_cost(trade_id, usage.input_tokens, usage.output_tokens)

    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text.strip())

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        s = text.find('{')
        e_idx = text.rfind('}')
        if s >= 0 and e_idx > s:
            try:
                result = json.loads(text[s:e_idx + 1])
            except Exception:
                result = {'decision': 'PARSE_ERROR', 'raw': text[:500]}
        else:
            result = {'decision': 'PARSE_ERROR', 'raw': text[:500]}

    return result, computed


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Parse args
    dry_run = '--dry-run' in sys.argv
    budget = BUDGET_CAP
    for i, arg in enumerate(sys.argv):
        if arg == '--budget' and i + 1 < len(sys.argv):
            budget = float(sys.argv[i + 1])

    if not dry_run and not API_KEY:
        print('ERROR: Set ANTHROPIC_API_KEY and retry.')
        sys.exit(1)

    print(f"=== T4 Pre-Computed Prompt Test ===")
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
                'candle_close': matching.iloc[0]['candle_close'],
                'candle_open': matching.iloc[0]['candle_open'],
            }
    print(f"  Loaded {len(msos)} MSOs")
    print()

    # ── Run evaluation ────────────────────────────────────
    print("Running evaluation...")
    results = []
    n_skipped = 0  # Track data mismatch skips

    for i, (tid, mso_data) in enumerate(sorted(msos.items()), 1):
        if cumulative_cost >= budget:
            print(f"  BUDGET CAP hit at ${cumulative_cost:.2f}")
            break

        symbol = mso_data['symbol']
        candle_close = mso_data['candle_close']
        candle_open = mso_data['candle_open']

        if pd.isna(candle_close):
            print(f"  [{i}/{len(msos)}] {tid} — SKIPPED (no candle close)")
            n_skipped += 1
            continue

        # Pre-compute first to check for data mismatch
        current_body = None
        if candle_close and candle_open and not pd.isna(candle_open):
            current_body = abs(float(candle_close) - float(candle_open))

        computed, summary = precompute(
            mso_data['user_message'],
            symbol=symbol,
            current_price=float(candle_close),
            current_body=current_body,
        )

        # Check for data mismatch: zone price should be within 5x of entry price
        zone = computed.get('nearest_zone')
        if zone and zone.get('high'):
            zone_high = zone['high']
            price_ratio = zone_high / float(candle_close) if candle_close > 0 else float('inf')
            if price_ratio > 5 or price_ratio < 0.2:
                print(f"  [{i}/{len(msos)}] {tid} — SKIPPED (data mismatch: zone={zone_high:.2f}, price={candle_close:.5f})")
                n_skipped += 1
                continue

        print(f"  [{i}/{len(msos)}] {tid} (${cumulative_cost:.2f})")

        api_result, computed = evaluate_mso_with_precompute(
            mso_data['user_message'],
            tid,
            symbol,
            float(candle_close),
            float(candle_open) if not pd.isna(candle_open) else None,
            dry_run=dry_run,
        )

        decision = str(api_result.get('decision', 'PARSE_ERROR')).upper()
        confidence = api_result.get('confidence_score', 0)
        grade = api_result.get('reasoning', {}).get('setup_grade', '') if isinstance(api_result.get('reasoning'), dict) else ''

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
            'grade': grade,
            'framework': api_result.get('framework', ''),
            # Computed facts (inputs to LLM scoring, not scores themselves)
            'q3_label': computed.get('q3_label', ''),
            'q3_distance_atr': computed.get('q3_distance_atr'),
            'q4_label': computed.get('q4_label', ''),
            'q4_position_pct': computed.get('q4_position_pct'),
            'q5_label': computed.get('q5_label', ''),
            'q5_ratio': computed.get('q5_ratio'),
            'q6_rr': computed.get('q6_rr'),
            'q7_sl_in_atr': computed.get('q7_sl_in_atr'),
            'q7_meets_atr': computed.get('q7_meets_atr'),
            'nearest_zone_source': computed.get('nearest_zone_source', ''),
            'bonus_first_touch': computed.get('bonus_first_touch', False),
            'bonus_fvg_present': computed.get('bonus_fvg_present', False),
        }
        results.append(row)

    print()

    # ── Save results ──────────────────────────────────────
    print("Saving results...")
    out_path = OUT_DIR / f"T4_precomputed_results_v2.json"
    with open(out_path, 'w') as f:
        json.dump({'test': TEST_NAME, 'rows': results, 'n_skipped': n_skipped}, f, indent=2)
    print(f"  Saved {out_path.name}")

    # Cost log
    cost_path = OUT_DIR / f"T4_precomputed_cost_log_v2.csv"
    pd.DataFrame(cost_log).to_csv(cost_path, index=False)
    print(f"  Saved {cost_path.name}")

    # ── Quick stats ───────────────────────────────────────
    df = pd.DataFrame(results)
    n_evaluated = len(df)
    n_cand = (df.decision == 'CANDIDATE').sum()
    n_parse = (df.decision == 'PARSE_ERROR').sum()

    # CR on evaluated MSOs only (excludes skipped data mismatches)
    cr = n_cand / n_evaluated if n_evaluated > 0 else 0

    # Total MSOs including skipped
    n_total = len(msos)
    n_valid = n_evaluated  # Evaluated = valid (after skipping mismatches)

    cand_df = df[df.decision == 'CANDIDATE']
    wr = cand_df.win.mean() if len(cand_df) > 0 else 0
    total_r = cand_df.r_multiple.sum() if len(cand_df) > 0 else 0

    print()
    print("=" * 60)
    print("=== T4 RESULTS ===")
    print("=" * 60)
    print(f"Total MSOs: {n_total}")
    print(f"Valid MSOs: {n_valid} (skipped {n_skipped} data mismatches)")
    print(f"CANDIDATEs: {n_cand}")
    print(f"CR (valid only): {cr:.1%}")
    print(f"WR: {wr:.1%}")
    print(f"CR × WR: {cr * wr:.3f}")
    print(f"Total R: {total_r:+.1f}R")
    print(f"Parse errors: {n_parse}")
    print(f"Total cost: ${cumulative_cost:.2f}")
    print()
    print("Baseline comparison:")
    print("  P2A v1: CR=38%, WR=69.6%, CR×WR=0.265")
    print()

    # ── Generate report ───────────────────────────────────
    report_path = REPORT_DIR / f"T4_precomputed_results_v2.md"
    report_lines = [
        "# T4 Pre-Computed Prompt Results",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Model:** {MODEL}, effort={EFFORT}",
        f"**Total MSOs:** {n_total}",
        f"**Valid MSOs:** {n_valid} (skipped {n_skipped} data mismatches)",
        f"**Total cost:** ${cumulative_cost:.2f}",
        "",
        "## Summary",
        "",
        "| Metric | T4 Pre-Computed | Baseline (P2A v1) | Delta |",
        "|--------|-----------------|-------------------|-------|",
        f"| Valid MSOs | {n_valid} | 121 | {n_valid - 121:+d} |",
        f"| Skipped (data mismatch) | {n_skipped} | 0 | — |",
        f"| CR (valid only) | {cr:.1%} | 38.0% | {(cr - 0.38) * 100:+.1f}pp |",
        f"| WR | {wr:.1%} | 69.6% | {(wr - 0.696) * 100:+.1f}pp |",
        f"| CR×WR | {cr * wr:.3f} | 0.265 | {cr * wr - 0.265:+.3f} |",
        f"| CANDIDATEs | {n_cand} | 46 | {n_cand - 46:+d} |",
        f"| Total R | {total_r:+.1f}R | +13.7R | {total_r - 13.7:+.1f}R |",
        "",
        "## Pre-Computed Score Distribution",
        "",
    ]

    if len(cand_df) > 0:
        report_lines.extend([
            "### CANDIDATE trades — computed fact distribution",
            "",
            f"- Q3 label breakdown: {cand_df.q3_label.value_counts().to_dict()}",
            f"- Q3 mean distance (ATR): {cand_df.q3_distance_atr.mean():.2f}" if cand_df.q3_distance_atr.notna().any() else "- Q3 distance: N/A",
            f"- Q4 label breakdown: {cand_df.q4_label.value_counts().to_dict()}",
            f"- Q5 label breakdown: {cand_df.q5_label.value_counts().to_dict()}",
            f"- Q5 mean body ratio: {cand_df.q5_ratio.mean():.2f}" if cand_df.q5_ratio.notna().any() else "- Q5 ratio: N/A",
            f"- Zone source breakdown: {cand_df.nearest_zone_source.value_counts().to_dict()}",
            f"- Bonus first touch: {cand_df.bonus_first_touch.sum()}/{len(cand_df)}",
            f"- Bonus FVG present: {cand_df.bonus_fvg_present.sum()}/{len(cand_df)}",
            "",
        ])

    report_lines.extend([
        "## Parse Errors",
        "",
        f"Count: {n_parse}",
        "",
    ])

    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    print(f"  Saved {report_path.name}")
