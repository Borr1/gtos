#!/usr/bin/env python3
"""T3 Prompt Ablation — 5 prompt variants on same 121 MSOs.

Tests L4 model risk hypotheses D10, D12, D13, D14 individually.
D17 (ensemble) computed from results post-hoc (no extra API calls).

Variants:
  A: smc_persona   — Add back "institutional SMC trader" persona (D10 reverse)
  B: no_role        — Remove ALL role framing, just instructions (D10 full)
  C: checklist      — YES/NO factual checklist, no judgment (D12)
  D: binary         — Minimal no-CoT prompt (D13)
  E: blueprint      — FinCoT rigid step-by-step (D14)

Usage:
  python T3_prompt_ablation.py            # Run all 5 variants
  python T3_prompt_ablation.py A C        # Run only variants A and C
  python T3_prompt_ablation.py --budget 8 # Set budget cap per variant

Cost estimate: ~$5/variant × 5 = ~$25 total
"""

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── CONFIG ──────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"
EFFORT = "max"
MAX_TOKENS = 2000
TEMPERATURE = 0
BUDGET_PER_VARIANT = 6.0
TEST_NAME = "T3_prompt_ablation"

# ── Paths ───────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
ENTRY_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'
OUT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'data'
REPORT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'results'
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ── Cost constants (Sonnet 4.6) ─────────────────────────
INPUT_COST_PER_TOK  = 3.0  / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
if not API_KEY:
    print('ERROR: Set ANTHROPIC_API_KEY and retry.')
    sys.exit(1)

from anthropic import Anthropic
client = Anthropic()


# ═══════════════════════════════════════════════════════════════════════════
# PROMPT VARIANTS
# ═══════════════════════════════════════════════════════════════════════════

# Shared output schema (used by A, B, C, E — D has a minimal schema)
_OUTPUT_SCHEMA = """## Output Schema
{
  "timestamp_utc": "<ISO-8601>",
  "model_used": "<model>",
  "decision": "NO_TRADE | CANDIDATE | WAIT",
  "confidence_score": <0-100>,
  "confidence_computation": "<score breakdown>",
  "framework": "ob_retest | breaker_retest | none",
  "kill_zone": "london | ny",
  "frameworks_evaluated": {
    "ob_retest": {"qualified": <bool>, "score": <int>, "reason": "<summary>"},
    "breaker_retest": {"qualified": <bool>, "score": <int>, "reason": "<summary>"}
  },
  "reasoning": {
    "daily_bias": {"direction": "bullish|bearish|ranging", "confidence": "high|medium|low", "protected_swing_level": <float>, "explanation": "<1 sentence>"},
    "h4_alignment": {"aligned": <bool>, "h4_pois_identified": [], "explanation": "<1 sentence>"},
    "h1_setup": {"poi_identified": <bool>, "poi_type": "OB|FVG|liquidity_zone|none", "poi_price_level": <float>, "zone": "premium|discount|neutral", "fib_retracement_pct": <float>, "causing_event_type": "BOS|CHoCH|unknown", "explanation": "<1 sentence>"},
    "liquidity_sweep": {"detected": <bool>, "pool_type": "<type>", "sweep_quality": "clean|messy|ambiguous", "sweep_price": <float>, "explanation": "<1 sentence>"},
    "m15_confirmation": {"choch_detected": <bool>, "displacement_quality": "strong|medium|weak|none", "displacement_candle_body_vs_avg_ratio": <float>, "explanation": "<1 sentence>"},
    "similar_historical_setups_considered": [],
    "setup_grade": "A+|A|B+|B|C",
    "overall_reasoning": "<2-3 sentences>"
  },
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE>",
  "wait_reason": "<if WAIT>"
}

When CANDIDATE, trade_parameters:
{
  "direction": "LONG|SHORT",
  "entry_price": <float>,
  "stop_loss": <float>,
  "sl_buffer_applied": <float>,
  "take_profit_1": <float>,
  "take_profit_2": <float>,
  "take_profit_3": <float>,
  "risk_reward_ratio": <float>,
  "position_size_lots": 0.01
}"""

# Shared scoring criteria (used by A, B, E — C and D restructure these)
_SCORING_CRITERIA = """## CRITICAL REQUIREMENTS (any failure → NO_TRADE)
C1. DIRECTIONAL BIAS: Establish directional bias from available timeframes. If the most recent D1 structural break (BOS or CHoCH) establishes a clear direction, use D1 as the primary bias. If D1 has no recent structural break or is ambiguous, use H4 direction as the primary reference. If H4 is also unclear, require at least two of D1/H4/H1 to agree on direction. If no directional agreement exists → NO_TRADE.
C2. H4 ALIGNMENT: H4 must not ACTIVELY OPPOSE the established bias direction. H4 ranging or unclear is acceptable when D1 is clearly directional. Only a clear H4 structural bias in the OPPOSITE direction triggers failure.
C3. DIRECTION MATCH: Trade direction must align with the established bias. LONG only if bullish, SHORT only if bearish.

## QUALIFYING CRITERIA (score each)
Q1. H1 STRUCTURAL BREAK: BOS in trend direction = 15pts, CHoCH to aligned = 12pts, None = 0pts.
Q2. UNMITIGATED ORDER BLOCK: Unmitigated H1 OB from impulse that caused structural break (check timeframes.H1.order_blocks where mitigated=false) = 20pts, absent/mitigated = 0pts.
Q3. PRICE PROXIMITY TO ZONE: Within OB boundaries = 15pts, within 1x M15 ATR(14) of boundary = 10pts, beyond = 0pts.
Q4. PREMIUM/DISCOUNT: Correct side of impulse = 10pts, equilibrium (45-55%) = 5pts, wrong side = 0pts.
Q5. M15 CONFIRMATION: CHoCH + strong displacement (body >= 1.5x avg) = 15pts, moderate (1.2-1.5x) = 10pts, weak/none = 0pts.
Q6. MINIMUM R:R to TP1: RR >= 1.5 = 10pts, else 0pts.
Q7. STOP LOSS: SL >= 1.5x M15 ATR(14) AND >= {sl_min_display} = 5pts, else 0pts.
BONUS: First touch +5, FVG +3, Compact impulse (<=7 H1 candles) +2. Max = 100.

## DECISION THRESHOLDS
Score >= 65 AND C1-C3 pass → CANDIDATE | Score 45-64 → WAIT | Score < 45 OR C fail → NO_TRADE"""

# Shared rules
_SHARED_RULES = """## ZONE FRESHNESS (HARD)
Only trade FIRST retest of an OB zone. If previously entered → zone is CONSUMED. First-touch: 72.7%, subsequent: 31.5%.

## BREAKER BLOCK RETEST (alternative)
If OB Retest < 65, also evaluate breaker blocks. Same scoring (substitute breaker for OB). Pick higher if both >= 65.

## TARGETS
TP1 = EXACTLY 1.5x SL distance from entry. LONG: TP1 = entry + 1.5*(entry-SL). SHORT: TP1 = entry - 1.5*(SL-entry).

## RULES
- Respond with ONLY valid JSON. Must start with { and end with }.
- NO_TRADE: state which failed, < 500 tokens.
- CANDIDATE: full breakdown, < 800 tokens.
- If C1/C2 fail: minimal JSON (decision, kill_zone, framework="none", no_trade_reason only).
- If CANDIDATE: m15_confirmation.choch_detected MUST be true.
- If h1_setup.poi_identified is false or poi_type is "none": MUST be NO_TRADE.
- Base ALL analysis on MSO data only. If not in MSO, it does not exist."""


# ─── VARIANT A: SMC Persona (D10 reverse test) ──────────────────────────
def prompt_A(kz_display, sl_min, zone_max):
    return f"""You are an institutional gold trader with 15+ years of Smart Money Concepts experience. You specialize in identifying high-probability OB retest setups where institutional order flow creates predictable continuation patterns.

Your task is to determine whether the current M15 candle meets the criteria for an entry setup based on price structure, zone quality, and trigger confirmation. Your evaluation must be DATA-DRIVEN.

## Kill Zone Windows
{kz_display}

## CALIBRATION
- Approximately 40-60% of evaluated setups qualify as CANDIDATE.
- The edge comes from OB zone continuation mechanics (~65-70% WR on qualifying zones).
- Over-rejection costs +0.20R expected value. Both false positives and false negatives have real costs.
- If rejecting >70% of evaluated setups, recalibrate.

{_SCORING_CRITERIA.replace('{sl_min_display}', sl_min)}

## CONFIDENCE
Score 65-74 → conf 65-72 | Score 75-84 → conf 73-80 | Score 85+ → conf 81-90.
Show breakdown: "Q1=15 Q2=20 ... = 80 → conf 78"

## GRADE
85+: A+ | 75-84: A | 65-74: B+ | 50-64: B | <50: C

## DECISION INTEGRITY
If score >= 65 and C1-C3 pass → output CANDIDATE. Trust the score — do not invent additional concerns.

{_SHARED_RULES.replace('{zone_max_display}', zone_max)}

{_OUTPUT_SCHEMA}"""


# ─── VARIANT B: No Role At All (D10 full removal) ───────────────────────
def prompt_B(kz_display, sl_min, zone_max):
    return f"""Determine whether the current M15 candle meets the criteria for an order block retest entry setup. Evaluate based on price structure, zone quality, and trigger confirmation using ONLY the data in the Market State Object provided.

## Kill Zone Windows
{kz_display}

## CALIBRATION
- Approximately 40-60% of evaluated setups qualify as CANDIDATE.
- The system's statistical edge: ~65-70% WR on qualifying OB zones.
- Over-rejection costs +0.20R. Both false positives and false negatives have real costs.
- If rejecting >70%, recalibrate.

{_SCORING_CRITERIA.replace('{sl_min_display}', sl_min)}

## CONFIDENCE
Score 65-74 → conf 65-72 | Score 75-84 → conf 73-80 | Score 85+ → conf 81-90.
Show breakdown: "Q1=15 Q2=20 ... = 80 → conf 78"

## GRADE
85+: A+ | 75-84: A | 65-74: B+ | 50-64: B | <50: C

## DECISION INTEGRITY
If score >= 65 and C1-C3 pass → CANDIDATE. Do not add concerns beyond the scoring.

{_SHARED_RULES.replace('{zone_max_display}', zone_max)}

{_OUTPUT_SCHEMA}"""


# ─── VARIANT C: Factual Checklist (D12) ──────────────────────────────────
def prompt_C(kz_display, sl_min, zone_max):
    return f"""Answer the following factual questions about the Market State Object provided. Each question has a defined answer format. Do not interpret or narrativize — verify facts from the data.

## Kill Zone Windows
{kz_display}

## HARD GATES (if ANY answer is NO → output NO_TRADE immediately)
G1. Does at least one of D1/H4 show a clear structural break (BOS or CHoCH) establishing directional bias? [YES/NO]
G2. Is H4 NOT actively opposing the established bias direction? (H4 unclear/ranging = YES) [YES/NO]
G3. Would the trade direction (LONG if bullish, SHORT if bearish) align with the bias? [YES/NO]

If all gates = YES, continue to scoring.

## SCORING CHECKLIST (answer each, sum points)
S1. H1 structural break in trade direction? BOS=15pts, CHoCH=12pts, None=0pts. [BOS/CHOCH/NONE] → ___pts
S2. Is there an unmitigated H1 OB from the impulse that caused the structural break? Check timeframes.H1.order_blocks where mitigated=false. [YES=20/NO=0] → ___pts
S3. How close is current price to the OB zone? [INSIDE=15/WITHIN_1ATR=10/BEYOND=0] → ___pts
S4. Is OB on correct side of impulse? Longs: discount. Shorts: premium. [CORRECT=10/EQUILIBRIUM=5/WRONG=0] → ___pts
S5. Does M15 show CHoCH + displacement? Body/avg ratio: >=1.5x=15, 1.2-1.5x=10, <1.2x=0. [STRONG=15/MOD=10/WEAK=0] → ___pts
S6. Is R:R to TP1 >= 1.5? TP1 = entry + 1.5*(entry-SL) for LONG. [YES=10/NO=0] → ___pts
S7. Is SL >= 1.5x M15 ATR(14) AND >= {sl_min}? [YES=5/NO=0] → ___pts
S8. BONUS: First touch? [+5] FVG present? [+3] Compact impulse <=7 H1 candles? [+2]

TOTAL = S1+S2+S3+S4+S5+S6+S7+S8 = ___

## DECISION
TOTAL >= 65 AND all gates YES → CANDIDATE
TOTAL 45-64 → WAIT
TOTAL < 45 OR any gate NO → NO_TRADE

## ZONE FRESHNESS (overrides above)
If OB zone was previously entered (mitigated=true in MSO) → NO_TRADE regardless of score.

## ALSO CHECK breaker blocks if OB score < 65.
Use same checklist substituting breaker zone for OB. Pick higher scorer if both >= 65.

## CONFIDENCE = total score. GRADE: 85+:A+, 75-84:A, 65-74:B+, 50-64:B, <50:C

## OUTPUT
Respond ONLY with valid JSON. Start with {{. End with }}.
For NO_TRADE under 500 tokens. For CANDIDATE under 800 tokens.

{_OUTPUT_SCHEMA}"""


# ─── VARIANT D: No-CoT Binary (D13) ─────────────────────────────────────
def prompt_D(kz_display, sl_min, zone_max):
    return f"""Evaluate this M15 candle for an OB retest entry. Output CANDIDATE, WAIT, or NO_TRADE.

Kill zones: {kz_display}

Requirements: D1/H4 directional bias must exist (C1), H4 must not oppose (C2), direction must match bias (C3). Score: H1 break (BOS=15,CHoCH=12), unmitigated H1 OB (20), price in/near zone (15/10/0), premium-discount (10/5/0), M15 CHoCH+displacement (15/10/0), RR>=1.5 (10), SL adequate (5), bonus first-touch/FVG/compact (+5/+3/+2). Score>=65+C1-C3=CANDIDATE, 45-64=WAIT, else NO_TRADE. TP1=1.5x SL from entry. First-touch zones only. If h1_setup.poi_identified=false → NO_TRADE. If CANDIDATE: m15 choch must be true. SL minimum: {sl_min}.

Respond with ONLY this JSON:
{{
  "timestamp_utc": "<ISO-8601>",
  "model_used": "<model>",
  "decision": "NO_TRADE|CANDIDATE|WAIT",
  "confidence_score": <total_score>,
  "confidence_computation": "<e.g. Q1=15 Q2=20 Q3=10 Q4=10 Q5=15 Q6=10 Q7=5 = 85>",
  "framework": "ob_retest|breaker_retest|none",
  "kill_zone": "london|ny",
  "no_trade_reason": "<if NO_TRADE>",
  "trade_parameters": {{
    "direction": "LONG|SHORT",
    "entry_price": <float>,
    "stop_loss": <float>,
    "take_profit_1": <float>,
    "risk_reward_ratio": <float>,
    "position_size_lots": 0.01
  }}
}}
trade_parameters = null if not CANDIDATE. No markdown, no preamble."""


# ─── VARIANT E: FinCoT Blueprint (D14) ──────────────────────────────────
def prompt_E(kz_display, sl_min, zone_max):
    return f"""Evaluate this M15 candle for an order block retest entry. Follow each step exactly. Each step produces ONE value — not a paragraph.

Kill zones: {kz_display}

## STEP 1: BIAS
Read D1 structural breaks. D1 direction = [BULLISH / BEARISH / UNCLEAR]
If D1 UNCLEAR: Read H4. H4 direction = [BULLISH / BEARISH / UNCLEAR]
If both UNCLEAR: Check if 2 of D1/H4/H1 agree. Agreement = [YES direction / NO]
Final bias = [BULLISH / BEARISH / NONE]
If NONE → STOP. Output NO_TRADE.

## STEP 2: H4 CHECK
H4 actively opposes bias? = [YES / NO / UNCLEAR]
If YES → STOP. Output NO_TRADE.

## STEP 3: DIRECTION
Trade direction = [LONG if BULLISH / SHORT if BEARISH]

## STEP 4: H1 BREAK (Q1)
Most recent H1 structural event in trade direction = [BOS / CHOCH / NONE]
Points = [15 / 12 / 0]

## STEP 5: OB ZONE (Q2)
Unmitigated H1 OB from that impulse exists? Check timeframes.H1.order_blocks mitigated=false.
= [YES / NO]
If mitigated or previously touched → zone CONSUMED → 0 points
Points = [20 / 0]

## STEP 6: PROXIMITY (Q3)
Current price vs OB zone: [INSIDE / WITHIN_1_ATR / BEYOND]
Points = [15 / 10 / 0]

## STEP 7: POSITION (Q4)
OB in correct side of impulse? Longs=discount, Shorts=premium.
= [CORRECT / EQUILIBRIUM / WRONG]
Points = [10 / 5 / 0]

## STEP 8: M15 TRIGGER (Q5)
M15 CHoCH detected? = [YES / NO]
If YES: body/avg ratio = [value]
Displacement = [STRONG >= 1.5x / MODERATE 1.2-1.5x / WEAK < 1.2x]
Points = [15 / 10 / 0]

## STEP 9: R:R (Q6)
SL = OB extreme + buffer. TP1 = entry + 1.5*(entry-SL) for LONG, or entry - 1.5*(SL-entry) for SHORT.
RR = [value]
RR >= 1.5? = [YES / NO]
Points = [10 / 0]

## STEP 10: SL CHECK (Q7)
SL distance >= 1.5x M15 ATR(14) AND >= {sl_min}? = [YES / NO]
Points = [5 / 0]

## STEP 11: BONUS
First touch? [+5 / 0]. FVG? [+3 / 0]. Compact impulse <=7 candles? [+2 / 0]

## STEP 12: TOTAL
Total = Q1 + Q2 + Q3 + Q4 + Q5 + Q6 + Q7 + bonus = [value]

## STEP 13: DECISION
If total >= 65 → CANDIDATE. If 45-64 → WAIT. If < 45 → NO_TRADE.
Grade: 85+:A+, 75-84:A, 65-74:B+, 50-64:B, <50:C

## ALSO CHECK breaker blocks if OB score < 65. Same steps, substitute breaker for OB.

## OUTPUT
Respond ONLY with valid JSON (start with {{, end with }}). Under 800 tokens for CANDIDATE, 500 for NO_TRADE.

{_OUTPUT_SCHEMA}"""


# ═══════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE (adapted from P2A_v2_s46_max.py)
# ═══════════════════════════════════════════════════════════════════════════

cumulative_cost = 0.0
cost_log: list[dict] = []


def track_cost(variant: str, trade_id: str, input_tokens: int, output_tokens: int) -> float:
    cost = input_tokens * INPUT_COST_PER_TOK + output_tokens * OUTPUT_COST_PER_TOK
    global cumulative_cost
    cumulative_cost += cost
    cost_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'variant': variant,
        'trade_id': trade_id,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'call_cost': round(cost, 6),
        'cumulative_cost': round(cumulative_cost, 4),
    })
    return cost


def evaluate_mso(system_prompt: str, user_message: str, variant: str, trade_id: str) -> dict:
    global cumulative_cost

    time.sleep(0.5)

    create_kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{'role': 'user', 'content': user_message}],
    )
    create_kwargs['output_config'] = {'effort': EFFORT}

    try:
        response = client.messages.create(**create_kwargs)
    except Exception as exc:
        return {'decision': 'API_ERROR', 'error': str(exc)[:300]}

    usage = response.usage
    track_cost(variant, trade_id, usage.input_tokens, usage.output_tokens)

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


def get_prompt_for_variant(variant: str, trade_id: str) -> str:
    symbol = "XAUUSD"
    tid_lower = trade_id.lower()
    for sym in ["gbpusd", "gbpjpy", "usdjpy", "us30"]:
        if sym in tid_lower:
            symbol = sym.upper()
            break

    KZ_MAP = {
        "XAUUSD": "- London Open: 07:00-10:30 UTC\n- NY Open: 13:00-17:00 UTC (skip 13:00-13:15)",
        "GBPUSD": "- London Open: 07:00-12:00 UTC\n- NY Open: 13:00-15:30 UTC",
        "GBPJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "USDJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "US30": "- London Open: 08:00-10:30 UTC\n- NY Open: 13:30-16:00 UTC",
    }
    SL_MAP = {"XAUUSD": "$5.00", "GBPUSD": "50 pips", "GBPJPY": "50 pips",
              "USDJPY": "50 pips", "US30": "50 points"}
    ZM_MAP = {"XAUUSD": "$15", "GBPUSD": "150 pips", "GBPJPY": "150 pips",
              "USDJPY": "150 pips", "US30": "150 points"}

    kz = KZ_MAP.get(symbol, KZ_MAP["XAUUSD"])
    sl = SL_MAP.get(symbol, "$5.00")
    zm = ZM_MAP.get(symbol, "$15")

    prompt_fn = {"A": prompt_A, "B": prompt_B, "C": prompt_C, "D": prompt_D, "E": prompt_E}
    return prompt_fn[variant](kz, sl, zm)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Parse args
    variants_to_run = ["A", "B", "C", "D", "E"]
    for arg in sys.argv[1:]:
        if arg.startswith("--budget"):
            BUDGET_PER_VARIANT = float(sys.argv[sys.argv.index(arg) + 1])
        elif arg.upper() in variants_to_run:
            if variants_to_run == ["A", "B", "C", "D", "E"]:
                variants_to_run = []
            variants_to_run.append(arg.upper())

    VARIANT_NAMES = {
        "A": "smc_persona",
        "B": "no_role",
        "C": "checklist",
        "D": "binary_no_cot",
        "E": "fincot_blueprint",
    }

    # ── Model check ───────────────────────────────────────
    print("=== Model verification ===")
    try:
        test = client.messages.create(
            model=MODEL, max_tokens=50, temperature=0,
            messages=[{'role': 'user', 'content': 'Reply "ready"'}],
            output_config={'effort': EFFORT},
        )
        print(f"  OK: {MODEL} with effort={EFFORT}")
    except Exception as e:
        print(f"  FAILED: {e}")
        sys.exit(1)

    # ── Load data ─────────────────────────────────────────
    print("\n=== Loading data ===")
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
            }
    print(f"  Loaded {len(msos)} MSOs")

    # ── Run variants ──────────────────────────────────────
    all_results = {}

    for variant in variants_to_run:
        vname = VARIANT_NAMES[variant]
        variant_cost = 0.0
        print(f"\n{'='*60}")
        print(f"=== Variant {variant}: {vname} ===")
        print(f"{'='*60}")

        variant_results = []
        for i, (tid, mso) in enumerate(sorted(msos.items()), 1):
            if variant_cost >= BUDGET_PER_VARIANT:
                print(f"  BUDGET CAP hit at ${variant_cost:.2f}")
                break

            system_prompt = get_prompt_for_variant(variant, tid)
            print(f"  [{i}/{len(msos)}] {tid} (${cumulative_cost:.2f})")

            api_result = evaluate_mso(system_prompt, mso['user_message'], variant, tid)

            decision = str(api_result.get('decision', 'PARSE_ERROR')).upper()
            confidence = api_result.get('confidence_score', 0)
            grade = api_result.get('reasoning', {}).get('setup_grade', '') if isinstance(api_result.get('reasoning'), dict) else ''
            if not grade:
                grade = api_result.get('setup_grade', '')

            outcome_data = outcomes.get(tid, ('UNKNOWN', 0, 0))

            row = {
                'trade_id': tid,
                'candle_time': mso['candle_time'],
                'symbol': tid.split('_')[-1].upper() if '_' in tid else 'XAUUSD',
                'kill_zone': mso['kill_zone'],
                'outcome': outcome_data[0],
                'r_multiple': outcome_data[1],
                'win': outcome_data[2],
                'variant': variant,
                'variant_name': vname,
                'decision': decision,
                'confidence': confidence,
                'grade': grade,
                'framework': api_result.get('framework', ''),
            }
            variant_results.append(row)

            call_cost = cost_log[-1]['call_cost'] if cost_log else 0
            variant_cost += call_cost

        all_results[variant] = variant_results
        print(f"\n  Variant {variant} complete: ${variant_cost:.2f}")

        # Quick stats
        vdf = pd.DataFrame(variant_results)
        n_cand = (vdf.decision == 'CANDIDATE').sum()
        n_total = len(vdf)
        cr = n_cand / n_total if n_total > 0 else 0
        cand_wins = vdf[(vdf.decision == 'CANDIDATE') & (vdf.win == 1)]
        wr = len(cand_wins) / n_cand if n_cand > 0 else 0
        print(f"  CR={cr:.1%} ({n_cand}/{n_total}), WR={wr:.1%}, CR*WR={cr*wr:.3f}")

    # ── Save results ──────────────────────────────────────
    print(f"\n{'='*60}")
    print("=== Saving results ===")

    # Per-variant JSON
    for variant, vresults in all_results.items():
        vname = VARIANT_NAMES[variant]
        out_path = OUT_DIR / f"T3_{vname}_results.json"
        with open(out_path, 'w') as f:
            json.dump({'variant': variant, 'name': vname, 'rows': vresults}, f, indent=2)
        print(f"  Saved {out_path.name}")

    # Cost log
    cost_path = OUT_DIR / f"T3_ablation_cost_log.csv"
    pd.DataFrame(cost_log).to_csv(cost_path, index=False)

    # ── Comparative report ────────────────────────────────
    report = []
    report.append("# T3 Prompt Ablation Results\n")
    report.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**Model:** {MODEL}, effort={EFFORT}")
    report.append(f"**Total cost:** ${cumulative_cost:.2f}")
    report.append(f"**MSOs evaluated:** {len(msos)}\n")

    # Load baseline (P2A v1) for comparison
    baseline_path = OUT_DIR / "P2A_s46_max_new_results.json"
    if baseline_path.exists():
        with open(baseline_path) as f:
            baseline = json.load(f)
        bl_rows = pd.DataFrame(baseline['rows'])
        bl_cr = (bl_rows.new_decision == 'CANDIDATE').sum() / len(bl_rows)
        bl_cand = bl_rows[bl_rows.new_decision == 'CANDIDATE']
        bl_wr = bl_cand.win.mean() if len(bl_cand) > 0 else 0
        report.append(f"**Baseline (P2A v1):** CR={bl_cr:.1%}, WR={bl_wr:.1%}, CR*WR={bl_cr*bl_wr:.3f}\n")

    report.append("## Comparison Table\n")
    report.append("| Variant | Name | CR | WR | CR*WR | n_CAND | Total R | Parse Errors |")
    report.append("|---------|------|----|----|-------|--------|---------|-------------|")

    for variant in variants_to_run:
        vresults = all_results.get(variant, [])
        if not vresults:
            continue
        vdf = pd.DataFrame(vresults)
        vname = VARIANT_NAMES[variant]
        n_total = len(vdf)
        n_cand = (vdf.decision == 'CANDIDATE').sum()
        n_parse = (vdf.decision == 'PARSE_ERROR').sum()
        cr = n_cand / n_total if n_total > 0 else 0
        cand = vdf[vdf.decision == 'CANDIDATE']
        wr = cand.win.mean() if len(cand) > 0 else 0
        total_r = cand.r_multiple.sum() if len(cand) > 0 else 0
        report.append(f"| {variant} | {vname} | {cr:.1%} | {wr:.1%} | {cr*wr:.3f} | {n_cand} | {total_r:+.1f}R | {n_parse} |")

    # D17: Ensemble analysis
    if len(all_results) >= 3:
        report.append("\n## D17: Ensemble Analysis (majority vote)\n")
        # Try all 3-variant combinations
        from itertools import combinations
        combos = list(combinations(variants_to_run, 3))
        for combo in combos:
            # Align on trade_ids
            dfs = {}
            for v in combo:
                vdf = pd.DataFrame(all_results[v])
                dfs[v] = vdf.set_index('trade_id')['decision']

            common_ids = set.intersection(*[set(d.index) for d in dfs.values()])
            if len(common_ids) < 10:
                continue

            ensemble_decisions = {}
            for tid in common_ids:
                votes = [dfs[v].get(tid, 'NO_TRADE') for v in combo]
                n_cand = sum(1 for v in votes if v == 'CANDIDATE')
                ensemble_decisions[tid] = 'CANDIDATE' if n_cand >= 2 else 'NO_TRADE'

            # Compute stats
            n_ens_cand = sum(1 for d in ensemble_decisions.values() if d == 'CANDIDATE')
            cr_ens = n_ens_cand / len(common_ids)
            ens_wins = sum(1 for tid, d in ensemble_decisions.items()
                          if d == 'CANDIDATE' and outcomes.get(tid, (None, 0, 0))[2] == 1)
            wr_ens = ens_wins / n_ens_cand if n_ens_cand > 0 else 0
            total_r_ens = sum(outcomes.get(tid, (None, 0, 0))[1]
                              for tid, d in ensemble_decisions.items() if d == 'CANDIDATE')

            combo_name = "+".join(f"{v}({VARIANT_NAMES[v]})" for v in combo)
            report.append(f"**{combo_name}:**")
            report.append(f"  CR={cr_ens:.1%}, WR={wr_ens:.1%}, CR*WR={cr_ens*wr_ens:.3f}, Total R={total_r_ens:+.1f}")

            # Agreement rate
            unanimous = sum(1 for tid in common_ids
                           if len(set(dfs[v].get(tid, '') for v in combo)) == 1)
            report.append(f"  Agreement rate: {unanimous/len(common_ids):.1%} ({unanimous}/{len(common_ids)})")

            # Split vs unanimous WR (D20)
            unan_cand = [tid for tid in common_ids
                         if all(dfs[v].get(tid) == 'CANDIDATE' for v in combo)]
            split_cand = [tid for tid in common_ids
                          if ensemble_decisions[tid] == 'CANDIDATE' and tid not in unan_cand]
            if unan_cand:
                unan_wr = np.mean([outcomes.get(tid, (None, 0, 0))[2] for tid in unan_cand])
                report.append(f"  Unanimous CANDIDATE WR: {unan_wr:.1%} (n={len(unan_cand)})")
            if split_cand:
                split_wr = np.mean([outcomes.get(tid, (None, 0, 0))[2] for tid in split_cand])
                report.append(f"  Split-decision CANDIDATE WR: {split_wr:.1%} (n={len(split_cand)})")
            report.append("")

    report.append(f"\n---\n*Generated by T3_prompt_ablation.py — total cost ${cumulative_cost:.2f}*")

    report_path = REPORT_DIR / "T3_prompt_ablation_results_v1.md"
    report_path.write_text("\n".join(report))
    print(f"\n  Report: {report_path}")
    print(f"\n=== DONE. Total cost: ${cumulative_cost:.2f} ===")
