#!/usr/bin/env python3
"""Test B — Prompt-Neutral Experiment.

Three-arm design:
  Arm A: 30 MSOs through CURRENT production prompt (non-determinism baseline)
  Arm B: Same 30 MSOs through neutral prompt (stripped of identity/anchoring)

Selects 30 trades (15W + 15L) balanced across date range from existing
batch results, extracts their pre-built prompts, constructs both arms,
submits via Anthropic Batch API, analyzes decision flips.

Usage:
    # Dry run — select trades, validate 5 MSOs, show cost estimate
    python scripts/test_b_prompt_neutral.py --dry-run

    # Submit both arms as batch
    python scripts/test_b_prompt_neutral.py

    # Resume with existing batch IDs
    python scripts/test_b_prompt_neutral.py --resume-arm-a msgbatch_XXX --resume-arm-b msgbatch_YYY
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env", override=True)

from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BATCH_API_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "batch_api"
SESSIONS_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "sessions"
OUTPUT_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "test_b"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "claude-sonnet-4-20250514"


# ═══════════════════════════════════════════════════════════════════════
# NEUTRAL PROMPT — stripped of identity framing and anchoring language
# ═══════════════════════════════════════════════════════════════════════

def build_neutral_system_prompt() -> str:
    """Build the neutral system prompt.

    Identical mechanical criteria (U1-U7, OB1-OB7, BR1-BR7) and output schema
    as the production prompt. Removes:
    - Identity framing ("institutional gold trader with 15+ years")
    - Quality signal guidance (FVG, displacement-at-OB, impulse compactness)
    - Anchoring language (win-rate boosts, percentage improvements)
    - Self-check emotional guidance ("Am I forcing this?")
    - Confidence scoring guidance
    - Setup grading descriptions
    Keeps: All mechanical rules, output schema, anti-hallucination guardrails.
    """

    return """You are a market analysis system. Your role is to evaluate whether an H1 Order Block Retest setup exists on the current M15 candle.

## Kill Zone Windows
{kz_display}
You will be told which window is being evaluated. The OB Retest setup is evaluated in BOTH kill zones.

## UNIVERSAL REQUIREMENTS
If ANY requirement fails, output NO_TRADE immediately:

U1. DIRECTIONAL BIAS: Establish directional bias from the highest available timeframe. If Daily structure is clearly bullish or bearish, use Daily as the primary bias. If Daily is unclear or ranging, use H4 and H1 directional consensus — at least two of D1/H4/H1 must agree on direction for a valid bias. If no timeframe consensus exists → NO_TRADE.
U2. H4 ALIGNMENT: If Daily bias is clear, H4 must agree with Daily direction. If Daily is unclear, H4 direction becomes the primary higher-timeframe reference — H4 must be clearly directional (not ranging). If both Daily and H4 are unclear → NO_TRADE.
U3. M15 CONFIRMATION: After the setup trigger, M15 must show a CHoCH with displacement in the trade direction. CHoCH = body close beyond the most recent protected M15 swing. Displacement = at least one candle with body >= 1.5x the 20-period average body size. Without M15 CHoCH + displacement → NO_TRADE.
U4. DIRECTION MATCH: Trade direction must match the established directional bias (from D1 if clear, or from H4+H1 consensus if D1 is unclear). LONG only if bias is bullish, SHORT only if bias is bearish.
U5. MINIMUM RR: Risk-to-reward must be >= 1:1.5 to the first target after applying SL buffer.
U6. SL REQUIREMENTS: Stop loss must be >= 1.5x M15 ATR(14) AND >= $5.00 absolute minimum.
U7. KILL ZONE: The setup trigger must occur within the active kill zone window.

## EVALUATION SEQUENCE

Step 1: Establish directional bias per U1. Check U2 (H4 alignment with the established bias). If no valid bias can be established or U2 fails → NO_TRADE. State the bias source used (Daily, or H4+H1 consensus if Daily is unclear).

Step 2: Evaluate BOTH frameworks on this candle:
  a) OB Retest criteria (OB1 through OB7)
  b) Breaker Block Retest criteria (BR1 through BR7)
Pick the best qualifying setup. If both qualify, prefer the one with stronger displacement and tighter zone. If neither qualifies → NO_TRADE.

Step 3: Verify all criteria are met. If any criterion is not cleanly met → NO_TRADE.

---

## H1 ORDER BLOCK RETEST — SETUP CRITERIA

OB1. H1 STRUCTURAL BREAK: H1 must show a confirmed CHoCH OR BOS in the direction aligned with the established directional bias.
  - Bullish CHoCH: H1 was in bearish structure, price body-closed above the protected LH → H1 shifting bullish
  - Bullish BOS: H1 was already bullish, price broke above the last swing high → H1 continues bullish
  - Either qualifies. The order blocks in the MSO include blocks created from BOTH BOS and CHoCH events. Check the causing_event_type field to distinguish them.
  - If neither CHoCH nor BOS is detected on H1 in the aligned direction → NO_TRADE.
OB2. UNMITIGATED ORDER BLOCK: An unmitigated H1 order block exists from the impulse leg that caused the structural break (BOS or CHoCH). The OB is the last opposing candle before the displacement move. Check timeframes.H1.order_blocks for unmitigated OBs.
OB3. PRICE AT OB: Current price has pulled back into or near the OB zone.
OB4. PREMIUM/DISCOUNT: The OB must be in the correct zone relative to the impulse:
  - For longs: OB must be in discount (below 50% of the impulse)
  - For shorts: OB must be in premium (above 50% of the impulse)
OB5. M15 CONFIRMATION: At or near the OB, M15 shows CHoCH + displacement in the trade direction (U3).
OB6. STOP LOSS: Beyond the OB extreme (high for bearish OB, low for bullish OB) + ATR buffer. Must satisfy U6.
OB7. TARGETS: TP1 MUST be EXACTLY 1.5x SL distance from entry. TP1 = entry + 1.5 * (entry - SL) for LONGS, or entry - 1.5 * (SL - entry) for SHORTS. TP2 and TP3 are optional (set to 0 if not applicable).

---

## H1 BREAKER BLOCK RETEST — SETUP CRITERIA

BR1. DAILY BIAS + H4 ALIGNMENT: Same as OB Retest (U1, U2).
BR2. UNMITIGATED BREAKER BLOCK: An unretested H1 breaker block exists in the MSO (check timeframes.H1.breaker_blocks where is_retested=false). The breaker direction must align with the established directional bias.
BR3. PRICE AT BREAKER ZONE: Current price has pulled back into or near the breaker block zone.
BR4. DISPLACEMENT QUALITY: The original OB was broken with displacement (strong candle body through the zone, not a slow grind).
BR5. ZONE QUALITY: The breaker zone should be relatively tight (not a massive zone). Zones wider than $15 are lower quality.
BR6. M15 CONFIRMATION: At or near the breaker zone, M15 shows CHoCH + displacement in the trade direction (U3).
BR7. ENTRY + SL + TP: Entry at or within the breaker block zone. SL beyond the zone extreme. TP1 MUST be EXACTLY 1.5x SL distance from entry. SL must satisfy U6.

---

## SETUP GRADING
- A+: ALL requirements met + displacement quality strong (>= 2x avg body)
- A: ALL criteria met but displacement quality moderate (1.5-2x avg body)
- B+ or below: Any criterion not cleanly met → DO NOT OUTPUT AS CANDIDATE

Only A+ and A setups qualify as CANDIDATE.

## CONFIDENCE SCORE
Rate 50-95 based on overall confluence count.
Show a one-line computation in confidence_computation.

## CRITICAL RULES
- Evaluate BOTH the OB Retest AND Breaker Block Retest criteria on every candle within the kill zone.
- Base ALL analysis on the Market State Object data. If a level, swing, or pattern is not in the data, it does not exist.
- If structure is unclear on any timeframe, state "unclear" — do NOT force a classification.
- When signals conflict, default to NO_TRADE.
- You can output at most ONE CANDIDATE per candle.

## TOKEN EFFICIENCY
If U1 or U2 fail, output a minimal JSON response with only: decision, kill_zone, framework set to "none", and a one-sentence no_trade_reason. Do NOT evaluate OB criteria when U1 or U2 have already failed.

## Output Format
Respond with ONLY a valid JSON object. No preamble, no markdown fences, no text outside the JSON.

```json
{
  "timestamp_utc": "<ISO-8601 timestamp of the candle being evaluated>",
  "model_used": "claude-sonnet-4-20250514",
  "decision": "NO_TRADE" | "CANDIDATE" | "WAIT",
  "confidence_score": <0-100 integer>,
  "confidence_computation": "<e.g. Baseline 70 + strong displacement (+5) - partial OB (-5) = 70>",
  "framework": "ob_retest" | "breaker_retest" | "none",
  "kill_zone": "london" | "ny",
  "frameworks_evaluated": {
    "ob_retest": {"qualified": false, "reason": "<why it didn't qualify>"},
    "breaker_retest": {"qualified": false, "reason": "<why it didn't qualify>"}
  },
  "reasoning": {
    "daily_bias": {
      "direction": "bullish" | "bearish" | "ranging",
      "confidence": "high" | "medium" | "low",
      "protected_swing_level": <float price level or 0.0>,
      "explanation": "<1-2 sentence summary>"
    },
    "h4_alignment": {
      "aligned": true | false,
      "h4_pois_identified": ["<OB/FVG description>", ...],
      "explanation": "<1-2 sentence summary>"
    },
    "h1_setup": {
      "poi_identified": true | false,
      "poi_type": "OB" | "FVG" | "liquidity_zone" | "none",
      "poi_price_level": <float or 0.0>,
      "zone": "premium" | "discount" | "neutral",
      "fib_retracement_pct": <float 0-100 or 0.0>,
      "causing_event_type": "BOS" | "CHoCH" | "unknown",
      "explanation": "<1-2 sentence summary>"
    },
    "liquidity_sweep": {
      "detected": true | false,
      "pool_type": "asian_high" | "asian_low" | "pdh" | "pdl" | "equal_highs" | "equal_lows" | "session_high" | "session_low" | "london_high" | "london_low" | "none",
      "sweep_quality": "clean" | "messy" | "ambiguous",
      "sweep_price": <float or 0.0>,
      "explanation": "<1-2 sentence summary>"
    },
    "m15_confirmation": {
      "choch_detected": true | false,
      "displacement_quality": "strong" | "medium" | "weak" | "none",
      "displacement_candle_body_vs_avg_ratio": <float or 0.0>,
      "explanation": "<1-2 sentence summary>"
    },
    "similar_historical_setups_considered": [],
    "setup_grade": "A+" | "A" | "B+" | "B" | "C",
    "overall_reasoning": "<2-4 sentence summary of the full analysis>"
  },
  "trade_parameters": null,
  "no_trade_reason": "<brief reason if NO_TRADE, else null>",
  "wait_reason": "<brief reason if WAIT, else null>"
}
```

When decision is "CANDIDATE", trade_parameters MUST be:
```json
{
  "direction": "LONG" | "SHORT",
  "entry_price": <float>,
  "stop_loss": <float>,
  "sl_buffer_applied": <float>,
  "take_profit_1": <float>,
  "take_profit_2": <float>,
  "take_profit_3": <float>,
  "risk_reward_ratio": <float>,
  "position_size_lots": 0.01
}
```

## Data Grounding Rules
- Base ALL analysis on the price data provided in the Market State Object. If a price level, swing, or pattern is not present in the Market State Object, it does not exist.
- If you cannot determine a structure direction with high confidence from the data provided, state 'unclear' — do not force a classification.
- Respond with ONLY valid JSON matching the schema. Your response MUST start with { and end with }. No preamble, no markdown fences, no explanation outside the JSON.

## Internal Consistency Rules
- If decision is CANDIDATE, m15_confirmation.choch_detected MUST be true (otherwise violates U3).
- If m15_confirmation.choch_detected is false, decision MUST be NO_TRADE.
- If h1_setup.poi_identified is FALSE or h1_setup.poi_type is "none", the decision MUST be NO_TRADE.

## Conciseness Rules
- Keep each reasoning section explanation to 1-2 sentences.
- The overall_reasoning field MUST be under 100 words.
- For NO_TRADE decisions, be especially brief.
""".replace("{kz_display}", "- London Open: 07:00\u201309:30 UTC\n- NY Open: 13:00\u201315:30 UTC").strip()


# ═══════════════════════════════════════════════════════════════════════
# PROMPT DIFF — Document exact differences between production and neutral
# ═══════════════════════════════════════════════════════════════════════

PROMPT_DIFF = """
## Production vs Neutral Prompt Differences

REMOVED in neutral:
1. Identity framing: "institutional gold trader with 15+ years of experience trading XAUUSD"
   → Replaced with: "market analysis system"
2. Quality signal: "Displacement creating an FVG: ~11% higher continuation rates"
3. Quality signal: "Displacement at a pre-existing OB zone: ~5% lower probability"
4. Quality signal: "Impulse compactness: 7 or fewer candles ~85% vs 8+ candles ~55%"
5. Self-check step: "Am I forcing this because no trade has been found?"
   "Is displacement genuinely strong or am I rationalizing?"
   "Would a skeptical, experienced institutional trader agree?"
6. Reasoning Quality Signals: "Reference 8+ distinct price levels (+17pp)"
   "Avoid hedging phrases (+13pp)"
7. Confidence scoring anchoring language removed
8. BOS/CHoCH strength commentary ("BOS provides stronger confirmation")

KEPT identical:
- U1-U7 mechanical requirements
- OB1-OB7 criteria
- BR1-BR7 criteria
- Output JSON schema
- Anti-hallucination guardrails
- Internal consistency rules
- Conciseness rules
- Setup grading thresholds (A+, A, B+)
- TP1 = 1.5x SL rule
- SL >= 1.5x ATR + $5 minimum
"""


# ═══════════════════════════════════════════════════════════════════════
# Trade selection
# ═══════════════════════════════════════════════════════════════════════

def select_30_trades() -> list[dict]:
    """Select 15 winners + 15 losers balanced across date range."""
    all_trades = []
    for f in sorted(SESSIONS_DIR.glob("*.json")):
        d = json.load(open(f))
        ts = d.get("trade_summary", {})
        if not (isinstance(ts, dict) and ts.get("trade_taken")):
            continue
        evals = d.get("candle_evaluations", [])
        candidate = None
        for e in evals:
            if e.get("decision") == "CANDIDATE" and e.get("trade_executed"):
                candidate = e
                break
        if not candidate:
            continue

        ct = candidate["candle_time"]
        kz = candidate.get("kill_zone", "london")
        date_str = d["date"]
        time_part = ct[11:16].replace(":", "")
        custom_id = f"{date_str}_{kz}_{time_part}"

        all_trades.append({
            "date": date_str,
            "candle_time": ct,
            "kill_zone": kz,
            "custom_id": custom_id,
            "outcome": ts["outcome"],
            "r_multiple": ts.get("r_multiple", 0),
        })

    wins = [t for t in all_trades if t["outcome"] == "WIN"]
    losses = [t for t in all_trades if t["outcome"] == "LOSS"]

    # Sample 15 from each, spaced across date range
    # Sort by date and pick every Nth
    wins_sorted = sorted(wins, key=lambda x: x["date"])
    losses_sorted = sorted(losses, key=lambda x: x["date"])

    step_w = max(1, len(wins_sorted) // 15)
    step_l = max(1, len(losses_sorted) // 15)

    selected_wins = wins_sorted[::step_w][:15]
    selected_losses = losses_sorted[::step_l][:15]

    # If we don't have 15 of either, pad from remaining
    if len(selected_wins) < 15:
        remaining = [w for w in wins_sorted if w not in selected_wins]
        selected_wins += remaining[:15 - len(selected_wins)]
    if len(selected_losses) < 15:
        remaining = [l for l in losses_sorted if l not in selected_losses]
        selected_losses += remaining[:15 - len(selected_losses)]

    selected = selected_wins + selected_losses
    selected.sort(key=lambda x: x["date"])

    logger.info(f"Selected {len(selected)} trades: "
                f"{sum(1 for t in selected if t['outcome']=='WIN')}W "
                f"{sum(1 for t in selected if t['outcome']=='LOSS')}L")
    return selected


# ═══════════════════════════════════════════════════════════════════════
# Prompt extraction
# ═══════════════════════════════════════════════════════════════════════

def load_prompt_index() -> dict:
    """Load all pre-built prompts from batch_api, indexed by custom_id."""
    index = {}
    for fp in sorted(BATCH_API_DIR.glob("*_full_prompts.json")):
        try:
            data = json.load(open(fp))
            for item in data:
                index[item["custom_id"]] = item["prompt"]
        except Exception as e:
            logger.warning(f"Failed to load {fp.name}: {e}")
    logger.info(f"Loaded {len(index)} prompts from batch_api")
    return index


def extract_user_message(prompt_data: dict) -> str:
    """Extract the user message text from a prompt dict."""
    return prompt_data.get("user_message", "")


def extract_static_context(prompt_data: dict) -> str:
    """Extract the static context (D1/H4/session data) from system blocks."""
    system = prompt_data.get("system", [])
    if isinstance(system, list) and system:
        text = system[0].get("text", "")
        # Static context is after "## Static Context (D1/H4/Session)"
        marker = "## Static Context (D1/H4/Session)"
        idx = text.find(marker)
        if idx >= 0:
            return text[idx:]
    return ""


# ═══════════════════════════════════════════════════════════════════════
# Build batch requests
# ═══════════════════════════════════════════════════════════════════════

def build_arm_a_requests(trades: list[dict], prompt_index: dict) -> list[Request]:
    """Arm A: Production prompt (exact same as original batch)."""
    requests = []
    for t in trades:
        cid = t["custom_id"]
        prompt = prompt_index.get(cid)
        if not prompt:
            logger.warning(f"Missing prompt for {cid}")
            continue

        requests.append(Request(
            custom_id=f"armA_{cid}",
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=2000,
                temperature=0,
                system=prompt["system"],
                messages=[{"role": "user", "content": prompt["user_message"]}],
            ),
        ))
    return requests


def build_arm_b_requests(trades: list[dict], prompt_index: dict) -> list[Request]:
    """Arm B: Neutral prompt + same user message (market data)."""
    neutral_system = build_neutral_system_prompt()
    requests = []
    for t in trades:
        cid = t["custom_id"]
        prompt = prompt_index.get(cid)
        if not prompt:
            logger.warning(f"Missing prompt for {cid}")
            continue

        # Extract static context from original and append to neutral
        static_ctx = extract_static_context(prompt)
        full_neutral = neutral_system + "\n\n" + static_ctx

        requests.append(Request(
            custom_id=f"armB_{cid}",
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=2000,
                temperature=0,
                system=[{
                    "type": "text",
                    "text": full_neutral,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": prompt["user_message"]}],
            ),
        ))
    return requests


# ═══════════════════════════════════════════════════════════════════════
# MSO validation
# ═══════════════════════════════════════════════════════════════════════

def validate_mso_from_prompt(prompt_data: dict, custom_id: str) -> tuple[bool, str]:
    """Validate that a prompt contains valid MSO data in the user message."""
    user_msg = prompt_data.get("user_message", "")
    issues = []

    # Check for key MSO sections
    required_sections = [
        "## Dynamic Market Data",
        "## H1",
        "## M15",
        "Candle:",
    ]
    for section in required_sections:
        if section not in user_msg:
            issues.append(f"Missing section: {section}")

    # Check system prompt has static context
    system = prompt_data.get("system", [])
    if isinstance(system, list) and system:
        sys_text = system[0].get("text", "")
        if "## D1" not in sys_text:
            issues.append("Missing D1 in static context")
        if "## H4" not in sys_text:
            issues.append("Missing H4 in static context")
        if "Session Levels" not in sys_text:
            issues.append("Missing Session Levels")
    else:
        issues.append("No system blocks found")

    if issues:
        return False, f"{custom_id}: {', '.join(issues)}"
    return True, f"{custom_id}: OK"


# ═══════════════════════════════════════════════════════════════════════
# Batch submission + polling
# ═══════════════════════════════════════════════════════════════════════

def submit_batch(client: Anthropic, requests: list[Request], arm_label: str) -> str:
    """Submit a batch and return the batch ID."""
    logger.info(f"Submitting {arm_label}: {len(requests)} requests")
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    logger.info(f"{arm_label} batch submitted: {batch_id}")
    return batch_id


def poll_batch(client: Anthropic, batch_id: str, arm_label: str) -> dict:
    """Poll until batch completes, return {custom_id: parsed_response}."""
    logger.info(f"Polling {arm_label} batch {batch_id}...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        logger.info(f"  {arm_label}: {status} — "
                     f"succeeded={counts.succeeded} failed={counts.errored} "
                     f"processing={counts.processing}")
        if status == "ended":
            break
        time.sleep(30)

    # Download results
    results = {}
    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        if result.result.type == "succeeded":
            msg = result.result.message
            text = msg.content[0].text if msg.content else ""
            # Parse JSON
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```\w*\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            try:
                parsed = json.loads(text)
                results[cid] = {"status": "ok", "response": parsed, "raw": text}
            except json.JSONDecodeError:
                results[cid] = {"status": "parse_error", "raw": text}
        else:
            results[cid] = {"status": "error", "error": str(result.result)}

    logger.info(f"{arm_label}: {len(results)} results collected, "
                f"{sum(1 for r in results.values() if r['status']=='ok')} parsed OK")
    return results


# ═══════════════════════════════════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════════════════════════════════

def analyze_results(trades: list[dict], arm_a: dict, arm_b: dict) -> str:
    """Compare decisions between arms and generate report."""
    lines = []
    lines.append("# Test B Results — Prompt-Neutral Experiment")
    lines.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Model: {MODEL}")
    lines.append(f"Trades: {len(trades)} (15W + 15L)")
    lines.append("")
    lines.append(PROMPT_DIFF)
    lines.append("")

    # Build comparison table
    lines.append("## Decision Comparison")
    lines.append("")
    lines.append("| Date | KZ | Outcome | Arm A Decision | Arm B Decision | Flipped? |")
    lines.append("|------|-----|---------|---------------|---------------|----------|")

    flips = []
    total_valid = 0
    arm_a_candidates = 0
    arm_b_candidates = 0

    for t in trades:
        cid = t["custom_id"]
        a_key = f"armA_{cid}"
        b_key = f"armB_{cid}"

        a_data = arm_a.get(a_key, {})
        b_data = arm_b.get(b_key, {})

        a_decision = "ERROR"
        b_decision = "ERROR"

        if a_data.get("status") == "ok":
            a_decision = a_data["response"].get("decision", "PARSE_ERROR")
        if b_data.get("status") == "ok":
            b_decision = b_data["response"].get("decision", "PARSE_ERROR")

        if a_decision == "CANDIDATE":
            arm_a_candidates += 1
        if b_decision == "CANDIDATE":
            arm_b_candidates += 1

        flipped = a_decision != b_decision and "ERROR" not in (a_decision, b_decision)
        if "ERROR" not in (a_decision, b_decision):
            total_valid += 1

        flip_marker = "YES" if flipped else ""
        if flipped:
            flips.append({
                "date": t["date"],
                "outcome": t["outcome"],
                "arm_a": a_decision,
                "arm_b": b_decision,
                "r_multiple": t["r_multiple"],
            })

        lines.append(f"| {t['date']} | {t['kill_zone']:>3} | {t['outcome']:>5} | "
                     f"{a_decision:<13} | {b_decision:<13} | {flip_marker} |")

    lines.append("")
    lines.append("## Summary Statistics")
    lines.append("")
    lines.append(f"- Total valid comparisons: {total_valid}")
    lines.append(f"- Arm A CANDIDATE count: {arm_a_candidates}")
    lines.append(f"- Arm B CANDIDATE count: {arm_b_candidates}")
    lines.append(f"- Total decision flips: {len(flips)}")
    if total_valid > 0:
        lines.append(f"- Flip rate: {len(flips)/total_valid:.1%}")
    lines.append("")

    if flips:
        lines.append("## Flipped Trades Detail")
        lines.append("")
        win_flips = [f for f in flips if f["outcome"] == "WIN"]
        loss_flips = [f for f in flips if f["outcome"] == "LOSS"]
        lines.append(f"- Winner flips: {len(win_flips)}")
        lines.append(f"- Loser flips:  {len(loss_flips)}")
        lines.append("")

        # Were flips beneficial?
        # A flip from CANDIDATE→NO_TRADE on a loser is GOOD (avoided loss)
        # A flip from CANDIDATE→NO_TRADE on a winner is BAD (missed win)
        # A flip from NO_TRADE→CANDIDATE on a winner is GOOD (caught win)
        # A flip from NO_TRADE→CANDIDATE on a loser is BAD (took loss)
        good_flips = 0
        bad_flips = 0
        for f in flips:
            if f["outcome"] == "LOSS" and f["arm_a"] == "CANDIDATE" and f["arm_b"] != "CANDIDATE":
                good_flips += 1
                lines.append(f"  GOOD: {f['date']} — Production took LOSS, neutral avoided it")
            elif f["outcome"] == "WIN" and f["arm_a"] != "CANDIDATE" and f["arm_b"] == "CANDIDATE":
                good_flips += 1
                lines.append(f"  GOOD: {f['date']} — Production missed WIN, neutral caught it")
            elif f["outcome"] == "WIN" and f["arm_a"] == "CANDIDATE" and f["arm_b"] != "CANDIDATE":
                bad_flips += 1
                lines.append(f"  BAD: {f['date']} — Production caught WIN, neutral missed it")
            elif f["outcome"] == "LOSS" and f["arm_a"] != "CANDIDATE" and f["arm_b"] == "CANDIDATE":
                bad_flips += 1
                lines.append(f"  BAD: {f['date']} — Production avoided LOSS, neutral took it")
            else:
                lines.append(f"  NEUTRAL: {f['date']} — {f['arm_a']}→{f['arm_b']} on {f['outcome']}")

        lines.append("")
        lines.append(f"- Good flips (neutral better): {good_flips}")
        lines.append(f"- Bad flips (production better): {bad_flips}")

    lines.append("")
    lines.append("## Non-Determinism Check (Arm A)")
    lines.append("")
    lines.append("Arm A uses the production prompt — same prompt that generated the original")
    lines.append("batch decisions. Any Arm A decision that differs from the original batch")
    lines.append("result represents LLM non-determinism (expected with temperature=0).")
    lines.append("")

    # Check original batch decisions
    orig_flips = 0
    for t in trades:
        cid = t["custom_id"]
        a_key = f"armA_{cid}"
        a_data = arm_a.get(a_key, {})
        if a_data.get("status") != "ok":
            continue
        a_decision = a_data["response"].get("decision", "")
        # Original decision was CANDIDATE (trade was executed)
        if a_decision != "CANDIDATE":
            orig_flips += 1
            lines.append(f"  Non-determinism: {t['date']} — Original=CANDIDATE, Arm A re-run={a_decision}")

    lines.append(f"\n- Arm A non-determinism rate: {orig_flips}/{total_valid} "
                 f"({orig_flips/max(1,total_valid):.1%})")
    lines.append("")

    lines.append("## Interpretation Guide")
    lines.append("")
    lines.append("- If Arm B flip rate ~ Arm A non-determinism rate: Prompt framing has NO effect")
    lines.append("- If Arm B flip rate >> non-determinism rate: Prompt framing matters")
    lines.append("- If flips disproportionately affect losers: Neutral prompt may be more selective")
    lines.append("- If flips disproportionately affect winners: Production prompt has better signal")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Test B — Prompt-Neutral Experiment")
    parser.add_argument("--dry-run", action="store_true",
                        help="Select trades, validate MSOs, estimate cost. No API calls.")
    parser.add_argument("--resume-arm-a", type=str, default=None,
                        help="Resume with existing Arm A batch ID")
    parser.add_argument("--resume-arm-b", type=str, default=None,
                        help="Resume with existing Arm B batch ID")
    args = parser.parse_args()

    # Step 1: Select trades
    trades = select_30_trades()
    logger.info(f"Selected {len(trades)} trades")
    for t in trades:
        logger.info(f"  {t['date']} {t['kill_zone']:>7} {t['outcome']:>5} {t['r_multiple']:+.2f}R")

    # Step 2: Load prompt index
    prompt_index = load_prompt_index()

    # Step 3: Validate 5 MSOs
    logger.info("\n=== MSO Validation (first 5) ===")
    all_valid = True
    for t in trades[:5]:
        prompt = prompt_index.get(t["custom_id"])
        if not prompt:
            logger.error(f"MISSING: {t['custom_id']}")
            all_valid = False
            continue
        valid, msg = validate_mso_from_prompt(prompt, t["custom_id"])
        logger.info(f"  {msg}")
        if not valid:
            all_valid = False

    if not all_valid:
        logger.error("MSO validation failed! Fix before proceeding.")
        sys.exit(1)
    logger.info("All 5 MSO validations passed.")

    # Step 4: Build requests
    arm_a_reqs = build_arm_a_requests(trades, prompt_index)
    arm_b_reqs = build_arm_b_requests(trades, prompt_index)
    logger.info(f"Arm A: {len(arm_a_reqs)} requests")
    logger.info(f"Arm B: {len(arm_b_reqs)} requests")

    # Cost estimate
    # ~3K input tokens + ~1K output per request, at batch 50% discount
    total_reqs = len(arm_a_reqs) + len(arm_b_reqs)
    est_input_tokens = total_reqs * 3000
    est_output_tokens = total_reqs * 1000
    # Sonnet 4: $3/1M input, $15/1M output, 50% batch discount
    est_cost = (est_input_tokens * 3 / 1_000_000 + est_output_tokens * 15 / 1_000_000) * 0.5
    logger.info(f"Estimated cost: ${est_cost:.2f} ({total_reqs} requests)")

    if args.dry_run:
        logger.info("DRY RUN — no API calls made.")
        # Save trade selection
        with open(OUTPUT_DIR / "selected_trades.json", "w") as f:
            json.dump(trades, f, indent=2)
        logger.info(f"Trade selection saved to {OUTPUT_DIR / 'selected_trades.json'}")
        return

    # Step 5: Submit batches
    client = Anthropic()

    if args.resume_arm_a:
        arm_a_batch_id = args.resume_arm_a
    else:
        arm_a_batch_id = submit_batch(client, arm_a_reqs, "Arm A")

    if args.resume_arm_b:
        arm_b_batch_id = args.resume_arm_b
    else:
        arm_b_batch_id = submit_batch(client, arm_b_reqs, "Arm B")

    # Save batch IDs
    batch_meta = {
        "arm_a_batch_id": arm_a_batch_id,
        "arm_b_batch_id": arm_b_batch_id,
        "submitted_at": datetime.now().isoformat(),
        "trades": trades,
    }
    with open(OUTPUT_DIR / "batch_meta.json", "w") as f:
        json.dump(batch_meta, f, indent=2)

    # Step 6: Poll both batches
    arm_a_results = poll_batch(client, arm_a_batch_id, "Arm A")
    arm_b_results = poll_batch(client, arm_b_batch_id, "Arm B")

    # Save raw results
    with open(OUTPUT_DIR / "arm_a_results.json", "w") as f:
        json.dump(arm_a_results, f, indent=2)
    with open(OUTPUT_DIR / "arm_b_results.json", "w") as f:
        json.dump(arm_b_results, f, indent=2)

    # Step 7: Analyze
    report = analyze_results(trades, arm_a_results, arm_b_results)

    results_path = _PROJECT_ROOT / "test_b_results.md"
    with open(results_path, "w") as f:
        f.write(report)
    logger.info(f"Results saved to {results_path}")

    # Also save to output dir
    with open(OUTPUT_DIR / "test_b_results.md", "w") as f:
        f.write(report)

    print("\n" + report)


if __name__ == "__main__":
    main()
