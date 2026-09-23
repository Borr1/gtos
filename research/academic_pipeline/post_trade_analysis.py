#!/usr/bin/env python3
"""Post-Trade Analysis — LLM structural pattern discovery across wins and losses.

PURPOSE
-------
Send every historical trade back to the LLM with its outcome. Ask the LLM to
identify what structural signals in the ORIGINAL MSO data predicted the win or
loss. Then aggregate across 121 trades to find patterns that survive win/loss
comparison.

APPROACH
--------
Prior work (point-biserial correlations on 30+ numeric features, n=129,
Bonferroni-corrected) found NO pre-trade numeric feature that predicts wins.
Only post-trade metrics (MAE, MFE) correlate with outcomes. The C-gate
(H1 bias + M15 alignment) is the only discriminative signal found.

This analysis asks: can the LLM find QUALITATIVE patterns in the full MSO
context (BOS sequences, zone configurations, structural narratives) that
numeric tests miss?

Critical design: analyze BOTH wins AND losses. A "warning sign" found in
losses only is real. The same sign in wins too = noise.

TWO-PHASE APPROACH
------------------
Phase 1: 121 individual trade analyses (~$2-3)
Phase 2: 1 aggregation call with all analyses (~$0.25)

OUTPUT FILES
------------
data/post_trade_individual_v1.json
data/post_trade_patterns_v1.json
data/post_trade_cost_log_v1.csv
results/post_trade_analysis_v1.md

USAGE
-----
  python post_trade_analysis.py              # Run both phases
  python post_trade_analysis.py --budget 6  # Set budget cap
  python post_trade_analysis.py --dry-run   # No API calls
  python post_trade_analysis.py --phase2-only  # Skip Phase 1, run Phase 2 from saved data

COST ESTIMATE: ~$3-4 total (121 calls × ~$0.025 + 1 aggregation call)
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
PHASE1_MAX_TOKENS = 800
PHASE2_MAX_TOKENS = 5000
TEMPERATURE = 0
BUDGET_CAP = 6.0
TEST_NAME = "post_trade_analysis"
VERSION = "v1"

# ── Paths ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'knowledge_base_backtest' / 'batch_api'
ENTRY_CSV = BASE_DIR / 'research' / 'academic_pipeline' / 'data' / 'entry_engineering_dataset.csv'
OUT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'data'
REPORT_DIR = BASE_DIR / 'research' / 'academic_pipeline' / 'results'
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

PHASE1_OUT = OUT_DIR / f"post_trade_individual_{VERSION}.json"
PHASE2_OUT = OUT_DIR / f"post_trade_patterns_{VERSION}.json"
COST_LOG_OUT = OUT_DIR / f"post_trade_cost_log_{VERSION}.csv"
REPORT_OUT = REPORT_DIR / f"post_trade_analysis_{VERSION}.md"

# ── Cost constants (Sonnet 4.6) ─────────────────────────
INPUT_COST_PER_TOK = 3.0 / 1_000_000
OUTPUT_COST_PER_TOK = 15.0 / 1_000_000

API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1 SYSTEM PROMPT — Individual Post-Trade Analysis
# ═══════════════════════════════════════════════════════════════════════════

PHASE1_SYSTEM_PROMPT = """You are a post-trade analyst for an order block retest trading system. You are given the Market State Object (MSO) that was evaluated BEFORE the trade, plus the actual outcome AFTER the trade.

Your job is to identify what structural signals in the ORIGINAL MSO data were consistent with or contradicted the actual outcome. Be specific — cite exact price levels, BOS events, zone positions from the MSO.

IMPORTANT: Not every losing trade was a bad read. The system has a ~65% win rate — 35% of trades SHOULD lose even when structurally valid. Your analysis must distinguish between:
- TYPE A: "This loss was predictable from the MSO — specific structural weakness X was visible before entry"
- TYPE B: "This was a structurally valid setup that happened to lose — nothing in the MSO predicted this outcome"

For winning trades, similarly distinguish:
- TYPE A: "This win was strongly predicted by structural factors X, Y in the MSO"
- TYPE B: "This was a marginal setup that happened to win — it could easily have gone either way"

## Analysis Framework

For each trade, evaluate from the MSO data:

1. H1 STRUCTURE CLARITY: Was the H1 bias clear and strong, or ambiguous?
   - How many BOS events confirmed the direction?
   - Were any BOS events displaced (disp=True means a significant gap — stronger impulse)?
   - Was there a recent CHoCH that may indicate structure reversing?
   - What was the ratio of the most recent BOS (higher = stronger impulse)?

2. M15 CONTEXT: Was M15 supporting, neutral, or actively opposing at entry time?
   - Any CHoCH events that contradict H1 bias?
   - Were M15 OBs aligned or opposing?

3. ZONE QUALITY: Was there a clear unmitigated OB?
   - Was the zone from H1 or M15?
   - How clean was the impulse that created the zone (ratio value)?
   - Were there multiple unmitigated OBs (possible conflict)?

4. COUNTER-SIGNALS: Any signals visible in the MSO that contradicted the trade direction?
   - FVGs in the opposing direction?
   - Multiple CHoCHs suggesting structure instability?
   - Sweeps that ran against the setup direction?
   - Recent opposing BOS events?

5. H1 BOS SEQUENCE QUALITY: Looking at the full BOS sequence —
   - Were BOS ratios declining (momentum decay)?
   - Were BOS ratios increasing (momentum building)?
   - Was the most recent BOS displaced (strong impulse)?

6. STRUCTURAL FRESHNESS: How recent were the key structural events?
   - Was the creating BOS event old or recent relative to entry?

## Output Format
Respond with ONLY valid JSON starting with { and ending with }.

{
  "trade_id": "<string>",
  "outcome": "WIN | LOSS",
  "r_multiple": <float>,
  "analysis_type": "A_predictable | B_statistical",
  "structural_assessment": {
    "h1_clarity": "strong | moderate | weak",
    "h1_bos_count": <int>,
    "h1_bos_momentum": "building | stable | declining | unclear",
    "recent_h1_choch": <bool>,
    "m15_support": "aligned | neutral | opposing",
    "m15_choch_present": <bool>,
    "zone_quality": "high | medium | low | none",
    "counter_signals_present": <bool>,
    "counter_signal_details": "<specific MSO evidence or null>"
  },
  "key_finding": "<1-2 sentences: single most important observation about this specific trade>",
  "lesson": "<1 sentence: what the system should learn from this trade>"
}"""


def build_phase1_user_message(mso_user_message: str, outcome: str, r_multiple: float,
                               trade_id: str, symbol: str, candle_time: str) -> str:
    """Construct the Phase 1 user message: original MSO + outcome context."""
    outcome_label = "WIN" if outcome == "WIN" else "LOSS"
    r_str = f"{r_multiple:+.3f}R"

    header = f"""## Trade Context
Trade ID: {trade_id}
Symbol: {symbol}
Candle Time: {candle_time}
ACTUAL OUTCOME: {outcome_label} ({r_str})

The following Market State Object was what the system saw BEFORE entering this trade.
Analyze what structural signals in this MSO were consistent with or contradicted the {outcome_label} outcome.

---
## Original Market State Object (pre-entry data only)

"""
    return header + mso_user_message


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2 SYSTEM PROMPT — Pattern Aggregation
# ═══════════════════════════════════════════════════════════════════════════

PHASE2_SYSTEM_PROMPT = """You are a quantitative research analyst for a trading system. You are given post-trade analyses for 121 trades (wins and losses). Your task is to find STRUCTURAL PATTERNS that distinguish wins from losses.

## Rules for Pattern Validity

1. A pattern is only real if it appears significantly MORE often in losses than wins (or vice versa)
2. "I found X in 80% of losses" is meaningless unless you also check what % of WINS have X
3. Quantify everything: "X appears in 15/43 losses (35%) vs 4/78 wins (5%)" ← this is a real signal
4. Small n warning: with 43 losses and 78 wins, any pattern needs >20% prevalence to be meaningful
5. If you find no reliable distinguishing pattern, say so explicitly — this is a valid and important finding
6. Do NOT report patterns where the loss/win prevalence difference is < 15 percentage points
7. Minimum threshold: any pattern must appear in at least 8 trades total to be reported

## What to Check
For each potential pattern, tally its presence in LOSSES and WINS separately:
- H1 BOS momentum (declining vs building/stable)
- Recent H1 CHoCH presence
- M15 CHoCH presence
- Zone quality distribution
- Counter-signal presence
- H1 BOS count ranges
- Analysis type distribution (A_predictable vs B_statistical)
- Any other patterns you identify from the individual analyses

## Output Format
Respond with ONLY valid JSON starting with { and ending with }.

{
  "summary_stats": {
    "total_trades": 121,
    "wins": <int>,
    "losses": <int>,
    "type_a_losses": "<N/43 (X%)>",
    "type_b_losses": "<N/43 (X%)>",
    "type_a_wins": "<N/78 (X%)>",
    "type_b_wins": "<N/78 (X%)>"
  },
  "patterns": [
    {
      "name": "<pattern name>",
      "description": "<what this structural pattern is>",
      "loss_prevalence": "<N/43 (X%)>",
      "win_prevalence": "<N/78 (X%)>",
      "delta_pp": <float — difference in percentage points, loss% minus win%>,
      "mechanism": "<why this structural feature might predict outcomes>",
      "confidence": "high | medium | low",
      "actionable": <bool>,
      "action": "<specific prompt change if actionable, or null>"
    }
  ],
  "null_finding": "<if no patterns survive comparison — explain what this means for the system>",
  "h1_clarity_check": {
    "strong_loss_pct": <float>,
    "strong_win_pct": <float>,
    "weak_loss_pct": <float>,
    "weak_win_pct": <float>,
    "interpretation": "<does H1 clarity distinguish wins from losses?>"
  },
  "cross_reference_finding": "<does the LLM analysis confirm that H1 bias clarity is the primary signal, or does it find something beyond what numeric tests found?>",
  "recommendation": "<concise: specific prompt changes if patterns found, or 'C-gate is sufficient' if not, with reasoning>"
}"""


# ═══════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

cumulative_cost = 0.0
cost_log: list[dict] = []


def track_cost(trade_id: str, phase: str, input_tokens: int, output_tokens: int) -> float:
    cost = input_tokens * INPUT_COST_PER_TOK + output_tokens * OUTPUT_COST_PER_TOK
    global cumulative_cost
    cumulative_cost += cost
    cost_log.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'trade_id': trade_id,
        'phase': phase,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'call_cost': round(cost, 6),
        'cumulative_cost': round(cumulative_cost, 4),
    })
    return cost


def call_api(system_prompt: str, user_message: str, trade_id: str, phase: str,
             max_tokens: int) -> tuple[dict, int, int]:
    """Make a single API call. Returns (parsed_result, input_tokens, output_tokens)."""
    from anthropic import Anthropic
    client = Anthropic()

    time.sleep(0.5)

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
            output_config={'effort': EFFORT},
        )
    except Exception as exc:
        print(f"    API ERROR: {exc}")
        return {'error': str(exc)[:300]}, 0, 0

    raw = resp.content[0].text if resp.content else '{}'
    in_tok = resp.usage.input_tokens
    out_tok = resp.usage.output_tokens
    track_cost(trade_id, phase, in_tok, out_tok)

    # Parse JSON
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
                result = {'parse_error': True, 'raw': raw}
        else:
            result = {'parse_error': True, 'raw': raw}

    return result, in_tok, out_tok


def save_cost_log():
    """Save cost log to CSV."""
    if cost_log:
        pd.DataFrame(cost_log).to_csv(COST_LOG_OUT, index=False)


# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

def load_data() -> tuple[pd.DataFrame, dict[str, dict]]:
    """Load entry dataset and MSOs. Returns (df, mso_map keyed by trade_id)."""
    print("Loading data...")

    df = pd.read_csv(ENTRY_CSV)
    # Filter to trades with MSO data
    df = df[df['data_available'].astype(str).str.lower() == 'true'].copy()
    # Treat BREAKEVEN as LOSS for win/loss binary analysis
    df['outcome_binary'] = df['outcome'].apply(lambda x: 'WIN' if x == 'WIN' else 'LOSS')
    df['win_binary'] = (df['outcome'] == 'WIN').astype(int)
    print(f"  Dataset: {len(df)} trades with MSO data ({df['win_binary'].sum()} wins, {(df['win_binary']==0).sum()} losses)")

    # Build candle_time → row index
    ct_to_row: dict[str, int] = {}
    for idx, row in df.iterrows():
        ct = row['candle_time']
        if ct and ct not in ct_to_row:
            ct_to_row[ct] = idx

    # Load MSOs from all batch_api files
    mso_map: dict[str, dict] = {}
    for fp_path in sorted(DATA_DIR.glob('*_full_prompts.json')):
        with open(fp_path) as f:
            records = json.load(f)
        for rec in records:
            ct = rec.get('candle_time', '')
            if not ct or ct not in ct_to_row:
                continue
            idx = ct_to_row[ct]
            tid = str(df.loc[idx, 'trade_id'])
            if tid in mso_map:
                continue
            prompt_data = rec.get('prompt', {})
            user_msg = prompt_data.get('user_message', '')
            mso_map[tid] = {
                'trade_id': tid,
                'user_message': user_msg,
                'candle_time': ct,
                'kill_zone': rec.get('kill_zone', ''),
                'symbol': str(df.loc[idx, 'symbol']),
                'outcome': str(df.loc[idx, 'outcome_binary']),
                'outcome_raw': str(df.loc[idx, 'outcome']),
                'r_multiple': float(df.loc[idx, 'r_multiple']) if not pd.isna(df.loc[idx, 'r_multiple']) else 0.0,
                'win': int(df.loc[idx, 'win_binary']),
            }

    print(f"  MSOs loaded: {len(mso_map)}")
    return df, mso_map


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1 — Individual Trade Analysis
# ═══════════════════════════════════════════════════════════════════════════

def run_phase1(mso_map: dict[str, dict], budget: float, dry_run: bool) -> list[dict]:
    """Run 121 individual post-trade analyses. Returns list of result dicts."""
    print()
    print("=== PHASE 1: Individual Trade Analysis ===")
    print(f"Trades to analyze: {len(mso_map)}")
    print(f"Budget remaining: ${budget - cumulative_cost:.2f}")
    print()

    # Check for existing partial results to resume from
    existing_results: list[dict] = []
    done_ids: set[str] = set()
    if PHASE1_OUT.exists():
        with open(PHASE1_OUT) as f:
            saved = json.load(f)
        if isinstance(saved, dict) and 'results' in saved:
            existing_results = saved['results']
            done_ids = {r['trade_id'] for r in existing_results}
            print(f"  Resuming: {len(done_ids)} already done")

    results = list(existing_results)
    parse_errors = 0
    trades_sorted = sorted(mso_map.items())

    for i, (tid, mso_data) in enumerate(trades_sorted, 1):
        if tid in done_ids:
            continue

        if cumulative_cost >= budget:
            print(f"\n  BUDGET CAP hit at ${cumulative_cost:.2f} — stopping Phase 1")
            break

        outcome = mso_data['outcome']
        r_mult = mso_data['r_multiple']
        symbol = mso_data['symbol']
        candle_time = mso_data['candle_time']

        done_count = len(results)
        total_count = len(mso_map)
        print(f"  [{done_count + 1}/{total_count}] {tid} ({outcome}, {r_mult:+.2f}R) — ${cumulative_cost:.2f}")

        if dry_run:
            result = {
                'trade_id': tid,
                'candle_time': candle_time,
                'symbol': symbol,
                'kill_zone': mso_data['kill_zone'],
                'outcome': outcome,
                'outcome_raw': mso_data['outcome_raw'],
                'r_multiple': r_mult,
                'win': mso_data['win'],
                'analysis_type': 'DRY_RUN',
                'structural_assessment': {},
                'key_finding': 'DRY_RUN',
                'lesson': 'DRY_RUN',
                'parse_error': False,
                'api_error': False,
            }
        else:
            user_msg = build_phase1_user_message(
                mso_data['user_message'],
                outcome,
                r_mult,
                tid,
                symbol,
                candle_time,
            )
            api_result, in_tok, out_tok = call_api(
                PHASE1_SYSTEM_PROMPT,
                user_msg,
                tid,
                'phase1',
                PHASE1_MAX_TOKENS,
            )

            if 'parse_error' in api_result or 'error' in api_result:
                parse_errors += 1

            # Normalize result
            result = {
                'trade_id': tid,
                'candle_time': candle_time,
                'symbol': symbol,
                'kill_zone': mso_data['kill_zone'],
                'outcome': outcome,
                'outcome_raw': mso_data['outcome_raw'],
                'r_multiple': r_mult,
                'win': mso_data['win'],
                'analysis_type': api_result.get('analysis_type', 'unknown'),
                'structural_assessment': api_result.get('structural_assessment', {}),
                'key_finding': api_result.get('key_finding', ''),
                'lesson': api_result.get('lesson', ''),
                'parse_error': 'parse_error' in api_result,
                'api_error': 'error' in api_result,
            }

        results.append(result)

        # Save incrementally every 10 trades
        if len(results) % 10 == 0 or len(results) == total_count:
            _save_phase1(results, parse_errors)
            save_cost_log()
            print(f"    Saved checkpoint ({len(results)} trades, ${cumulative_cost:.2f})")

    _save_phase1(results, parse_errors)
    save_cost_log()

    wins = [r for r in results if r['win'] == 1]
    losses = [r for r in results if r['win'] == 0]
    print()
    print(f"Phase 1 complete: {len(results)} trades ({len(wins)} wins, {len(losses)} losses)")
    print(f"Parse errors: {parse_errors}")
    print(f"Cost so far: ${cumulative_cost:.2f}")

    return results


def _save_phase1(results: list[dict], parse_errors: int):
    with open(PHASE1_OUT, 'w') as f:
        json.dump({
            'test': TEST_NAME,
            'phase': 1,
            'n_complete': len(results),
            'parse_errors': parse_errors,
            'results': results,
        }, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2 — Pattern Aggregation
# ═══════════════════════════════════════════════════════════════════════════

def build_phase2_user_message(individual_results: list[dict]) -> str:
    """Build the Phase 2 user message containing all 121 individual analyses."""
    wins = [r for r in individual_results if r['win'] == 1]
    losses = [r for r in individual_results if r['win'] == 0]

    lines = [
        f"## Post-Trade Analysis Corpus",
        f"Total trades: {len(individual_results)}",
        f"Wins (outcome=WIN): {len(wins)}",
        f"Losses (outcome=LOSS or BREAKEVEN treated as LOSS): {len(losses)}",
        f"",
        f"## Individual Trade Analyses",
        f"Each analysis below was generated from the original Market State Object plus outcome.",
        f"",
    ]

    # Group by outcome for clarity
    lines.append("### WINS (78 trades)")
    lines.append("")
    for r in sorted(wins, key=lambda x: x.get('r_multiple', 0), reverse=True):
        sa = r.get('structural_assessment', {})
        lines.append(json.dumps({
            'trade_id': r['trade_id'],
            'outcome': 'WIN',
            'r_multiple': r['r_multiple'],
            'analysis_type': r.get('analysis_type', 'unknown'),
            'h1_clarity': sa.get('h1_clarity', 'unknown'),
            'h1_bos_count': sa.get('h1_bos_count', 0),
            'h1_bos_momentum': sa.get('h1_bos_momentum', 'unknown'),
            'recent_h1_choch': sa.get('recent_h1_choch', False),
            'm15_support': sa.get('m15_support', 'unknown'),
            'm15_choch_present': sa.get('m15_choch_present', False),
            'zone_quality': sa.get('zone_quality', 'unknown'),
            'counter_signals_present': sa.get('counter_signals_present', False),
            'counter_signal_details': sa.get('counter_signal_details', None),
            'key_finding': r.get('key_finding', ''),
        }, separators=(',', ':')))

    lines.append("")
    lines.append("### LOSSES (43 trades, including BREAKEVENs)")
    lines.append("")
    for r in sorted(losses, key=lambda x: x.get('r_multiple', 0)):
        sa = r.get('structural_assessment', {})
        lines.append(json.dumps({
            'trade_id': r['trade_id'],
            'outcome': r.get('outcome_raw', 'LOSS'),
            'r_multiple': r['r_multiple'],
            'analysis_type': r.get('analysis_type', 'unknown'),
            'h1_clarity': sa.get('h1_clarity', 'unknown'),
            'h1_bos_count': sa.get('h1_bos_count', 0),
            'h1_bos_momentum': sa.get('h1_bos_momentum', 'unknown'),
            'recent_h1_choch': sa.get('recent_h1_choch', False),
            'm15_support': sa.get('m15_support', 'unknown'),
            'm15_choch_present': sa.get('m15_choch_present', False),
            'zone_quality': sa.get('zone_quality', 'unknown'),
            'counter_signals_present': sa.get('counter_signals_present', False),
            'counter_signal_details': sa.get('counter_signal_details', None),
            'key_finding': r.get('key_finding', ''),
        }, separators=(',', ':')))

    lines.append("")
    lines.append("## Your Task")
    lines.append("Count the prevalence of each structural feature SEPARATELY for wins and losses.")
    lines.append("Report only patterns where loss% - win% > 15pp (or win% - loss% > 15pp).")
    lines.append("A pattern in losses that is equally common in wins is NOT a signal — it is noise.")
    lines.append("If no pattern survives this comparison, report null_finding explicitly.")

    return "\n".join(lines)


def run_phase2(individual_results: list[dict], budget: float, dry_run: bool) -> dict:
    """Run the single pattern aggregation call. Returns pattern dict."""
    print()
    print("=== PHASE 2: Pattern Aggregation ===")

    budget_remaining = budget - cumulative_cost
    if budget_remaining < 0.5:
        print(f"  Insufficient budget for Phase 2 (${budget_remaining:.2f} remaining). Skipping.")
        return {}

    print(f"Budget remaining: ${budget_remaining:.2f}")
    print(f"Individual analyses: {len(individual_results)}")

    if dry_run:
        print("  DRY RUN — skipping Phase 2 API call")
        return {'dry_run': True}

    # Filter out any analyses with errors
    valid = [r for r in individual_results
             if not r.get('parse_error') and not r.get('api_error') and r.get('analysis_type') != 'DRY_RUN']
    skipped = len(individual_results) - len(valid)
    if skipped > 0:
        print(f"  Skipping {skipped} trades with errors")
    print(f"  Sending {len(valid)} analyses to aggregation")

    user_msg = build_phase2_user_message(valid)
    print(f"  User message length: {len(user_msg)} chars (~{len(user_msg)//4} tokens)")

    result, in_tok, out_tok = call_api(
        PHASE2_SYSTEM_PROMPT,
        user_msg,
        'phase2_aggregation',
        'phase2',
        PHASE2_MAX_TOKENS,
    )

    with open(PHASE2_OUT, 'w') as f:
        json.dump({
            'test': TEST_NAME,
            'phase': 2,
            'n_trades_analyzed': len(valid),
            'result': result,
        }, f, indent=2)
    save_cost_log()
    print(f"  Saved {PHASE2_OUT.name}")
    print(f"  Phase 2 cost: ${in_tok * INPUT_COST_PER_TOK + out_tok * OUTPUT_COST_PER_TOK:.2f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# LOCAL STATISTICS (computed from Phase 1 data, not LLM)
# ═══════════════════════════════════════════════════════════════════════════

def compute_local_stats(results: list[dict]) -> dict:
    """Compute basic cross-tabulations from Phase 1 data for the report."""
    wins = [r for r in results if r['win'] == 1]
    losses = [r for r in results if r['win'] == 0]
    n_w, n_l = len(wins), len(losses)

    def pct(n, total):
        return (n / total * 100) if total > 0 else 0.0

    def cross_tab(field: str, value) -> dict:
        w_count = sum(1 for r in wins if r.get('structural_assessment', {}).get(field) == value)
        l_count = sum(1 for r in losses if r.get('structural_assessment', {}).get(field) == value)
        return {
            'wins': f"{w_count}/{n_w} ({pct(w_count, n_w):.0f}%)",
            'losses': f"{l_count}/{n_l} ({pct(l_count, n_l):.0f}%)",
            'delta_pp': pct(l_count, n_l) - pct(w_count, n_w),
        }

    def analysis_type_tab(atype: str) -> dict:
        w_count = sum(1 for r in wins if r.get('analysis_type', '') == atype)
        l_count = sum(1 for r in losses if r.get('analysis_type', '') == atype)
        return {
            'wins': f"{w_count}/{n_w} ({pct(w_count, n_w):.0f}%)",
            'losses': f"{l_count}/{n_l} ({pct(l_count, n_l):.0f}%)",
            'delta_pp': pct(l_count, n_l) - pct(w_count, n_w),
        }

    return {
        'n_wins': n_w,
        'n_losses': n_l,
        'analysis_type': {
            'A_predictable': analysis_type_tab('A_predictable'),
            'B_statistical': analysis_type_tab('B_statistical'),
        },
        'h1_clarity': {
            'strong': cross_tab('h1_clarity', 'strong'),
            'moderate': cross_tab('h1_clarity', 'moderate'),
            'weak': cross_tab('h1_clarity', 'weak'),
        },
        'm15_support': {
            'aligned': cross_tab('m15_support', 'aligned'),
            'neutral': cross_tab('m15_support', 'neutral'),
            'opposing': cross_tab('m15_support', 'opposing'),
        },
        'zone_quality': {
            'high': cross_tab('zone_quality', 'high'),
            'medium': cross_tab('zone_quality', 'medium'),
            'low': cross_tab('zone_quality', 'low'),
        },
        'recent_h1_choch': {
            'True': cross_tab('recent_h1_choch', True),
        },
        'm15_choch': {
            'True': cross_tab('m15_choch_present', True),
        },
        'counter_signals': {
            'True': cross_tab('counter_signals_present', True),
        },
        'h1_momentum': {
            'declining': cross_tab('h1_bos_momentum', 'declining'),
            'building': cross_tab('h1_bos_momentum', 'building'),
            'stable': cross_tab('h1_bos_momentum', 'stable'),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def write_report(phase1_results: list[dict], phase2_result: dict, stats: dict):
    """Write the markdown summary report."""
    n_w = stats['n_wins']
    n_l = stats['n_losses']
    total = n_w + n_l

    patterns = phase2_result.get('patterns', []) if isinstance(phase2_result, dict) else []
    actionable = [p for p in patterns if p.get('actionable')]

    with open(REPORT_OUT, 'w') as f:
        f.write("# Post-Trade Structural Analysis\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Model:** {MODEL}, effort={EFFORT}\n")
        f.write(f"**Trades analyzed:** {total} ({n_w} wins, {n_l} losses)\n")
        f.write(f"**Total cost:** ${cumulative_cost:.2f}\n\n")

        # ── Type A vs Type B ─────────────────────────────
        f.write("## Type A vs Type B Distribution\n\n")
        f.write("*(LLM classification: A = structurally predictable, B = statistically valid loss/win)*\n\n")
        at = stats['analysis_type']
        f.write("| Type | Wins | Losses | Interpretation |\n")
        f.write("|------|------|--------|----------------|\n")
        f.write(f"| A (predictable) | {at['A_predictable']['wins']} | {at['A_predictable']['losses']} | Δ={at['A_predictable']['delta_pp']:+.0f}pp |\n")
        f.write(f"| B (statistical) | {at['B_statistical']['wins']} | {at['B_statistical']['losses']} | Δ={at['B_statistical']['delta_pp']:+.0f}pp |\n")
        f.write("\n")
        f.write("If losses are predominantly Type A: the LLM finds predictable pre-entry signals.\n")
        f.write("If losses are predominantly Type B: the system is already selecting the right setups.\n\n")

        # ── Structural Feature Cross-Tabs ─────────────────
        f.write("## Structural Feature Cross-Tabulation\n\n")
        f.write("*(Computed from Phase 1 individual analyses — local tally, not LLM)*\n\n")

        f.write("### H1 Bias Clarity\n\n")
        f.write("| Value | Wins | Losses | Δ (loss−win) |\n")
        f.write("|-------|------|--------|-------------|\n")
        for val, d in stats['h1_clarity'].items():
            f.write(f"| {val} | {d['wins']} | {d['losses']} | {d['delta_pp']:+.0f}pp |\n")
        f.write("\n")

        f.write("### M15 Support\n\n")
        f.write("| Value | Wins | Losses | Δ (loss−win) |\n")
        f.write("|-------|------|--------|-------------|\n")
        for val, d in stats['m15_support'].items():
            f.write(f"| {val} | {d['wins']} | {d['losses']} | {d['delta_pp']:+.0f}pp |\n")
        f.write("\n")

        f.write("### Zone Quality\n\n")
        f.write("| Value | Wins | Losses | Δ (loss−win) |\n")
        f.write("|-------|------|--------|-------------|\n")
        for val, d in stats['zone_quality'].items():
            f.write(f"| {val} | {d['wins']} | {d['losses']} | {d['delta_pp']:+.0f}pp |\n")
        f.write("\n")

        f.write("### H1 BOS Momentum\n\n")
        f.write("| Value | Wins | Losses | Δ (loss−win) |\n")
        f.write("|-------|------|--------|-------------|\n")
        for val, d in stats['h1_momentum'].items():
            f.write(f"| {val} | {d['wins']} | {d['losses']} | {d['delta_pp']:+.0f}pp |\n")
        f.write("\n")

        f.write("### Binary Signals\n\n")
        f.write("| Signal | Wins | Losses | Δ (loss−win) |\n")
        f.write("|--------|------|--------|-------------|\n")
        f.write(f"| Recent H1 CHoCH | {stats['recent_h1_choch']['True']['wins']} | {stats['recent_h1_choch']['True']['losses']} | {stats['recent_h1_choch']['True']['delta_pp']:+.0f}pp |\n")
        f.write(f"| M15 CHoCH present | {stats['m15_choch']['True']['wins']} | {stats['m15_choch']['True']['losses']} | {stats['m15_choch']['True']['delta_pp']:+.0f}pp |\n")
        f.write(f"| Counter-signals present | {stats['counter_signals']['True']['wins']} | {stats['counter_signals']['True']['losses']} | {stats['counter_signals']['True']['delta_pp']:+.0f}pp |\n")
        f.write("\n")

        # ── Phase 2 Patterns ──────────────────────────────
        f.write("## LLM-Identified Patterns (Phase 2)\n\n")
        if not phase2_result or phase2_result.get('dry_run'):
            f.write("*Phase 2 not run (dry run or insufficient budget)*\n\n")
        elif not patterns:
            null_finding = phase2_result.get('null_finding', 'No patterns identified.')
            f.write(f"**Null result:** {null_finding}\n\n")
        else:
            f.write(f"Patterns found: {len(patterns)} ({len(actionable)} actionable)\n\n")
            # Sort by |delta_pp|
            for p in sorted(patterns, key=lambda x: abs(x.get('delta_pp', 0)), reverse=True):
                conf = p.get('confidence', 'unknown')
                act = "ACTIONABLE" if p.get('actionable') else "informational"
                delta = p.get('delta_pp', 0)
                f.write(f"### {p.get('name', 'Unknown Pattern')} [{conf.upper()} | {act}]\n\n")
                f.write(f"**Description:** {p.get('description', '')}\n\n")
                f.write(f"| | Count |\n|---|---|\n")
                f.write(f"| Loss prevalence | {p.get('loss_prevalence', 'N/A')} |\n")
                f.write(f"| Win prevalence | {p.get('win_prevalence', 'N/A')} |\n")
                f.write(f"| Delta (loss−win) | {delta:+.0f}pp |\n\n")
                f.write(f"**Mechanism:** {p.get('mechanism', '')}\n\n")
                if p.get('actionable') and p.get('action'):
                    f.write(f"**Action:** {p['action']}\n\n")
                f.write("---\n\n")

            null_finding = phase2_result.get('null_finding', '')
            if null_finding:
                f.write(f"**Note on null patterns:** {null_finding}\n\n")

        # ── Cross-Reference ───────────────────────────────
        if isinstance(phase2_result, dict) and not phase2_result.get('dry_run'):
            xref = phase2_result.get('cross_reference_finding', '')
            rec = phase2_result.get('recommendation', '')
            if xref:
                f.write("## Cross-Reference with Prior Findings\n\n")
                f.write(f"{xref}\n\n")
            if rec:
                f.write("## Recommendation\n\n")
                f.write(f"{rec}\n\n")

        # ── Methodology Notes ─────────────────────────────
        f.write("## Methodology Notes\n\n")
        f.write("- **Hindsight bias mitigation:** Both wins AND losses analyzed. Patterns valid only if\n")
        f.write("  they appear significantly more often in one group.\n")
        f.write("- **Threshold:** Pattern reported only if delta > 15pp and n > 8 in that group.\n")
        f.write(f"- **Prior work:** Point-biserial correlations on 30+ numeric features (n=129,\n")
        f.write("  Bonferroni-corrected) found NO pre-trade numeric predictor of wins.\n")
        f.write("- **Only validated signal:** C-gate (H1 bias + M15 alignment) — discriminates CR×WR.\n")
        f.write("- **Population:** 121 trades with MSO data (78 wins, 43 losses incl. 4 BREAKEVEN).\n")
        f.write("- **In-sample only.** All findings require live validation.\n\n")

        # ── Cost Summary ──────────────────────────────────
        f.write("## Cost Summary\n\n")
        phase1_costs = [c for c in cost_log if c.get('phase') == 'phase1']
        phase2_costs = [c for c in cost_log if c.get('phase') == 'phase2']
        p1_cost = sum(c['call_cost'] for c in phase1_costs)
        p2_cost = sum(c['call_cost'] for c in phase2_costs)
        f.write(f"| Phase | Calls | Cost |\n")
        f.write(f"|-------|-------|------|\n")
        f.write(f"| Phase 1 (individual) | {len(phase1_costs)} | ${p1_cost:.2f} |\n")
        f.write(f"| Phase 2 (aggregation) | {len(phase2_costs)} | ${p2_cost:.2f} |\n")
        f.write(f"| **Total** | **{len(cost_log)}** | **${cumulative_cost:.2f}** |\n")

    print(f"  Saved {REPORT_OUT.name}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    phase2_only = '--phase2-only' in sys.argv
    budget = BUDGET_CAP
    for i, arg in enumerate(sys.argv):
        if arg == '--budget' and i + 1 < len(sys.argv):
            budget = float(sys.argv[i + 1])

    if not dry_run and not API_KEY:
        print('ERROR: Set ANTHROPIC_API_KEY and retry.')
        sys.exit(1)

    print("=== Post-Trade Analysis ===")
    print(f"Model: {MODEL}, effort={EFFORT}")
    print(f"Budget cap: ${budget}")
    print(f"Dry run: {dry_run}")
    print(f"Phase 2 only: {phase2_only}")
    print(f"Output dir: {OUT_DIR}")
    print()

    # ── Load data ─────────────────────────────────────────
    df, mso_map = load_data()

    # ── Phase 1 ───────────────────────────────────────────
    if phase2_only:
        # Load existing Phase 1 results
        if not PHASE1_OUT.exists():
            print(f"ERROR: {PHASE1_OUT} not found. Run Phase 1 first.")
            sys.exit(1)
        with open(PHASE1_OUT) as f:
            saved = json.load(f)
        phase1_results = saved.get('results', [])
        print(f"Loaded {len(phase1_results)} Phase 1 results from {PHASE1_OUT.name}")
    else:
        phase1_results = run_phase1(mso_map, budget, dry_run)

    # ── Phase 2 ───────────────────────────────────────────
    phase2_result = run_phase2(phase1_results, budget, dry_run)

    # ── Stats & Report ────────────────────────────────────
    stats = compute_local_stats(phase1_results)
    write_report(phase1_results, phase2_result, stats)

    # ── Final summary ─────────────────────────────────────
    print()
    print("=" * 60)
    print("=== POST-TRADE ANALYSIS COMPLETE ===")
    print("=" * 60)
    print(f"Phase 1 trades analyzed: {len(phase1_results)}")
    wins_done = sum(1 for r in phase1_results if r['win'] == 1)
    losses_done = sum(1 for r in phase1_results if r['win'] == 0)
    print(f"  Wins: {wins_done}, Losses: {losses_done}")

    type_a_losses = sum(1 for r in phase1_results if r['win'] == 0 and r.get('analysis_type') == 'A_predictable')
    type_b_losses = sum(1 for r in phase1_results if r['win'] == 0 and r.get('analysis_type') == 'B_statistical')
    if losses_done > 0:
        print(f"  Loss Type A (predictable): {type_a_losses}/{losses_done} ({type_a_losses/losses_done:.0%})")
        print(f"  Loss Type B (statistical): {type_b_losses}/{losses_done} ({type_b_losses/losses_done:.0%})")

    n_patterns = len(phase2_result.get('patterns', [])) if isinstance(phase2_result, dict) else 0
    n_actionable = sum(1 for p in phase2_result.get('patterns', []) if p.get('actionable')) if isinstance(phase2_result, dict) else 0
    print(f"Phase 2 patterns found: {n_patterns} ({n_actionable} actionable)")
    print(f"Total cost: ${cumulative_cost:.2f}")
    print()
    print(f"Output files:")
    print(f"  {PHASE1_OUT}")
    print(f"  {PHASE2_OUT}")
    print(f"  {COST_LOG_OUT}")
    print(f"  {REPORT_OUT}")
