#!/usr/bin/env python3
"""Devil's Advocate prompt test on 5 real trades.

Tests whether the DA produces specific, useful risk identification
with real price levels or generic fluff.
"""

import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env", override=True)

import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_API_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "batch_api"
OUTPUT_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "test_b"

# The 5 test trades (all have valid CANDIDATE responses with trade_parameters)
TRADES = [
    {"cid": "2025-05-05_london_0930", "label": "Trade 1: BIG WINNER +3.99R", "outcome": "WIN", "r": 3.99},
    {"cid": "2025-01-30_london_0800", "label": "Trade 2: BIG WINNER +3.77R (premium zone)", "outcome": "WIN", "r": 3.77},
    {"cid": "2024-06-05_ny_1445",     "label": "Trade 3: LOSER -1.00R (Opus caught, Sonnet A+)", "outcome": "LOSS", "r": -1.00},
    {"cid": "2025-03-14_london_0745", "label": "Trade 4: LOSER -1.00R (M15 conflict)", "outcome": "LOSS", "r": -1.00},
    {"cid": "2024-04-03_ny_1330",     "label": "Trade 5: MARGINAL +0.05R", "outcome": "WIN", "r": 0.05},
]

DEVILS_ADVOCATE_PROMPT = """You are a risk analyst. The following trade has been approved by the primary analyst. Your job is NOT to argue against it — it is to identify the 3 most specific threats to this trade succeeding. Be precise about price levels and probabilities.

For each risk, provide:
1. A specific description citing exact price levels from the data
2. The price level that would confirm this risk is materializing
3. Your probability estimate (0-100%) that this risk invalidates the trade

Output JSON:
{
  "risks": [
    {
      "description": "string — specific risk with price levels",
      "confirming_level": 0.0,
      "probability_pct": 0,
      "category": "STRUCTURAL_RESISTANCE | MOMENTUM_EXHAUSTION | DISPLACEMENT_DOUBT | TIMING_CONFLICT | CONTEXT_MISMATCH"
    }
  ],
  "recommendation": "PROCEED | CAUTION | DOWNGRADE",
  "overall_risk_assessment": "string — 2 sentences max"
}"""


def load_prompts_and_results():
    prompts = {}
    for fp in sorted(BATCH_API_DIR.glob("*_full_prompts.json")):
        for item in json.load(open(fp)):
            prompts[item["custom_id"]] = item["prompt"]

    raw_results = {}
    for fp in sorted(BATCH_API_DIR.glob("*_raw_results.json")):
        raw_results.update(json.load(open(fp)))

    return prompts, raw_results


def build_da_user_message(prompt_data: dict, sonnet_response: dict) -> str:
    """Build the DA user message: the market data + the approved trade."""
    # Get the market data (user message from original prompt)
    market_data = prompt_data.get("user_message", "")

    # Get the approved trade parameters
    tp = sonnet_response.get("trade_parameters", {})
    reasoning = sonnet_response.get("reasoning", {})

    approved_trade = (
        f"\n\n## APPROVED TRADE\n"
        f"Decision: CANDIDATE\n"
        f"Framework: {sonnet_response.get('framework', '?')}\n"
        f"Grade: {reasoning.get('setup_grade', '?')}\n"
        f"Confidence: {sonnet_response.get('confidence_score', 0)}\n"
        f"Direction: {tp.get('direction', '?')}\n"
        f"Entry: {tp.get('entry_price', 0)}\n"
        f"Stop Loss: {tp.get('stop_loss', 0)}\n"
        f"TP1: {tp.get('take_profit_1', 0)}\n"
        f"TP2: {tp.get('take_profit_2', 0)}\n"
        f"RR Ratio: {tp.get('risk_reward_ratio', 0)}\n"
        f"\n## Primary Analyst Reasoning\n"
        f"D1 Bias: {reasoning.get('daily_bias', {}).get('direction', '?')} "
        f"(conf: {reasoning.get('daily_bias', {}).get('confidence', '?')})\n"
        f"H4 Aligned: {reasoning.get('h4_alignment', {}).get('aligned', '?')}\n"
        f"H1 POI: {reasoning.get('h1_setup', {}).get('poi_type', '?')} at "
        f"{reasoning.get('h1_setup', {}).get('poi_price_level', 0)}\n"
        f"M15 CHoCH: {reasoning.get('m15_confirmation', {}).get('choch_detected', '?')}\n"
        f"Displacement: {reasoning.get('m15_confirmation', {}).get('displacement_quality', '?')} "
        f"({reasoning.get('m15_confirmation', {}).get('displacement_candle_body_vs_avg_ratio', 0)}x)\n"
        f"Sweep: {reasoning.get('liquidity_sweep', {}).get('pool_type', 'none')}\n"
        f"Overall: {reasoning.get('overall_reasoning', '')}\n"
    )

    return market_data + approved_trade


def main():
    prompts, raw_results = load_prompts_and_results()
    client = anthropic.Anthropic()
    results = []

    for t in TRADES:
        cid = t["cid"]
        logger.info(f"\n{'='*70}")
        logger.info(f"{t['label']} — {cid}")
        logger.info(f"{'='*70}")

        prompt = prompts.get(cid)
        if not prompt:
            logger.error(f"Missing prompt for {cid}")
            continue

        # Get original Sonnet response
        raw = raw_results.get(cid, {})
        text = raw.get("text", "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```\w*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        try:
            sonnet_resp = json.loads(text)
        except:
            logger.error(f"Can't parse Sonnet response for {cid}")
            continue

        if sonnet_resp.get("decision") != "CANDIDATE":
            logger.warning(f"Sonnet said {sonnet_resp.get('decision')} not CANDIDATE — using anyway")

        # Build DA message
        da_user_msg = build_da_user_message(prompt, sonnet_resp)

        # Get static context from original system prompt
        static_ctx = ""
        sys_blocks = prompt.get("system", [])
        if isinstance(sys_blocks, list) and sys_blocks:
            static_ctx = sys_blocks[0].get("text", "")

        # Call Sonnet with DA prompt (same model as production)
        da_system = DEVILS_ADVOCATE_PROMPT + "\n\n## Market Context\n" + static_ctx

        logger.info(f"Calling Devil's Advocate...")
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0,
                system=[{"type": "text", "text": da_system}],
                messages=[{"role": "user", "content": da_user_msg}],
            )

            da_text = resp.content[0].text.strip()
            if da_text.startswith("```"):
                da_text = re.sub(r"^```\w*\n?", "", da_text)
                da_text = re.sub(r"\n?```$", "", da_text)
            da_parsed = json.loads(da_text)

            cost = resp.usage.input_tokens * 3 / 1e6 + resp.usage.output_tokens * 15 / 1e6

            # Analyze quality
            risks = da_parsed.get("risks", [])
            rec = da_parsed.get("recommendation", "?")
            assessment = da_parsed.get("overall_risk_assessment", "")

            # Count price levels in risk descriptions
            all_risk_text = " ".join(r.get("description", "") for r in risks)
            price_levels = re.findall(r'\d{3,4}\.\d{1,2}', all_risk_text)
            distinct_prices = len(set(price_levels))

            # Check for generic phrases
            generic_phrases = ["market conditions", "unexpected", "volatile", "general risk",
                              "always possible", "no guarantee", "market uncertainty"]
            generic_count = sum(all_risk_text.lower().count(g) for g in generic_phrases)

            logger.info(f"  Recommendation: {rec}")
            logger.info(f"  Risks: {len(risks)}")
            logger.info(f"  Distinct price levels cited: {distinct_prices}")
            logger.info(f"  Generic phrase count: {generic_count}")
            logger.info(f"  Cost: ${cost:.3f}")

            for i, risk in enumerate(risks):
                logger.info(f"  Risk {i+1} [{risk.get('category', '?')}] ({risk.get('probability_pct', 0)}%):")
                logger.info(f"    {risk.get('description', '')[:150]}")
                logger.info(f"    Confirming level: {risk.get('confirming_level', 0)}")

            logger.info(f"  Assessment: {assessment}")

            results.append({
                "trade": t,
                "recommendation": rec,
                "num_risks": len(risks),
                "distinct_prices": distinct_prices,
                "generic_phrases": generic_count,
                "risks": risks,
                "assessment": assessment,
                "cost": cost,
                "actual_outcome": t["outcome"],
                "actual_r": t["r"],
            })

        except json.JSONDecodeError:
            logger.error(f"DA response not valid JSON: {da_text[:200]}")
            results.append({"trade": t, "error": "parse_error"})
        except Exception as e:
            logger.error(f"DA call failed: {e}")
            results.append({"trade": t, "error": str(e)})

        time.sleep(1)

    # Save results
    with open(OUTPUT_DIR / "devils_advocate_5_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Summary
    print("\n" + "=" * 70)
    print("DEVIL'S ADVOCATE TEST — SUMMARY")
    print("=" * 70)
    print()
    print(f"{'Trade':<45} {'Rec':>10} {'Prices':>7} {'Generic':>8} {'Actual':>8}")
    print("-" * 80)
    for r in results:
        if "error" in r:
            print(f"{r['trade']['label']:<45} ERROR")
            continue
        print(f"{r['trade']['label']:<45} {r['recommendation']:>10} {r['distinct_prices']:>7} "
              f"{r['generic_phrases']:>8} {r['actual_outcome']:>5} {r['actual_r']:+.2f}R")

    print()

    # Key question: did DA recommend DOWNGRADE on losers and PROCEED on winners?
    correct_calls = 0
    total = 0
    for r in results:
        if "error" in r:
            continue
        total += 1
        rec = r["recommendation"]
        outcome = r["actual_outcome"]
        if outcome == "LOSS" and rec in ("DOWNGRADE", "CAUTION"):
            correct_calls += 1
        elif outcome == "WIN" and r["actual_r"] > 1.0 and rec == "PROCEED":
            correct_calls += 1
        elif outcome == "WIN" and r["actual_r"] < 0.5 and rec in ("CAUTION", "PROCEED"):
            correct_calls += 1  # Marginal wins with CAUTION is also correct

    print(f"Correct directional calls: {correct_calls}/{total}")

    # Quality assessment
    avg_prices = sum(r.get("distinct_prices", 0) for r in results if "error" not in r) / max(1, total)
    avg_generic = sum(r.get("generic_phrases", 0) for r in results if "error" not in r) / max(1, total)
    print(f"Average distinct prices per trade: {avg_prices:.1f}")
    print(f"Average generic phrases per trade: {avg_generic:.1f}")
    print()

    if avg_prices >= 3 and avg_generic <= 1:
        print("VERDICT: SPECIFIC AND USEFUL — strong WF-2 candidate")
    elif avg_prices >= 2:
        print("VERDICT: MIXED — some specificity but needs prompt refinement")
    else:
        print("VERDICT: GENERIC FLUFF — same failure as old Bull/Bear debate, kill the idea")


if __name__ == "__main__":
    main()
