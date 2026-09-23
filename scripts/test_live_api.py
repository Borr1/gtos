#!/usr/bin/env python3
"""Manual integration test — runs the REAL pipeline with REAL Claude API calls.

Usage:
    # Cost estimate only (no API calls)
    python scripts/test_live_api.py --date 2025-11-15 --cost-estimate

    # Full run with real API calls
    python scripts/test_live_api.py --date 2025-11-15

    # Full run with debate round 2
    python scripts/test_live_api.py --date 2025-11-15 --round2

    # Verbose output (print full JSON responses)
    python scripts/test_live_api.py --date 2025-11-15 --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Ensure project root is importable ──────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

from src.components.debate import DebateEngine
from src.components.knowledge_base import KnowledgeBase
from src.components.primary_analyzer import PrimaryAnalyzer
from src.models.market_state_models import (
    DataQuality,
    MarketStateObject,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    Swing,
    TimeframeState,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Cost estimation
# ═══════════════════════════════════════════════════════════════════════

# Sonnet pricing: $3/M input tokens, $15/M output tokens
# Average primary analysis: ~3K input tokens, ~1.5K output tokens
# Average debate agent: ~3.5K input tokens, ~1K output tokens
# Judge: ~5K input tokens, ~1K output tokens

COST_ESTIMATES = {
    "primary_analysis": {
        "input_tokens": 3000,
        "output_tokens": 1500,
        "cost_usd": 3000 * 3 / 1_000_000 + 1500 * 15 / 1_000_000,  # ~$0.0315
    },
    "bull_agent": {
        "input_tokens": 3500,
        "output_tokens": 1000,
        "cost_usd": 3500 * 3 / 1_000_000 + 1000 * 15 / 1_000_000,  # ~$0.0255
    },
    "bear_agent": {
        "input_tokens": 3500,
        "output_tokens": 1000,
        "cost_usd": 3500 * 3 / 1_000_000 + 1000 * 15 / 1_000_000,  # ~$0.0255
    },
    "bull_rebuttal": {
        "input_tokens": 4000,
        "output_tokens": 800,
        "cost_usd": 4000 * 3 / 1_000_000 + 800 * 15 / 1_000_000,  # ~$0.024
    },
    "bear_rebuttal": {
        "input_tokens": 4000,
        "output_tokens": 800,
        "cost_usd": 4000 * 3 / 1_000_000 + 800 * 15 / 1_000_000,  # ~$0.024
    },
    "judge": {
        "input_tokens": 5000,
        "output_tokens": 1000,
        "cost_usd": 5000 * 3 / 1_000_000 + 1000 * 15 / 1_000_000,  # ~$0.030
    },
}


def print_cost_estimate(round2: bool = False) -> None:
    """Print estimated API costs without making any calls."""
    print("\n" + "=" * 60)
    print("COST ESTIMATE (no API calls will be made)")
    print("=" * 60)
    print(f"{'Component':<22} {'Input Tok':>10} {'Output Tok':>11} {'Cost USD':>10}")
    print("-" * 60)

    total_input = 0
    total_output = 0
    total_cost = 0.0

    # Primary analysis always runs
    for name in ["primary_analysis"]:
        e = COST_ESTIMATES[name]
        print(f"{name:<22} {e['input_tokens']:>10,} {e['output_tokens']:>11,} ${e['cost_usd']:>8.4f}")
        total_input += e["input_tokens"]
        total_output += e["output_tokens"]
        total_cost += e["cost_usd"]

    # If CANDIDATE → debate runs
    print(f"\n  (If Primary Analyzer returns CANDIDATE:)")
    debate_components = ["bull_agent", "bear_agent"]
    if round2:
        debate_components += ["bull_rebuttal", "bear_rebuttal"]
    debate_components.append("judge")

    for name in debate_components:
        e = COST_ESTIMATES[name]
        print(f"  {name:<20} {e['input_tokens']:>10,} {e['output_tokens']:>11,} ${e['cost_usd']:>8.4f}")
        total_input += e["input_tokens"]
        total_output += e["output_tokens"]
        total_cost += e["cost_usd"]

    print("-" * 60)
    print(f"{'TOTAL (worst case)':<22} {total_input:>10,} {total_output:>11,} ${total_cost:>8.4f}")
    print(f"\n  NO_TRADE scenario:  ~${COST_ESTIMATES['primary_analysis']['cost_usd']:.4f}")
    no_debate_total = sum(
        COST_ESTIMATES[n]["cost_usd"]
        for n in ["primary_analysis", "bull_agent", "bear_agent", "judge"]
    )
    print(f"  CANDIDATE (R1 only): ~${no_debate_total:.4f}")
    print(f"  CANDIDATE (R1+R2):   ~${total_cost:.4f}")
    print(f"\n  Model: claude-sonnet-4-20250514")
    print(f"  Pricing: $3/M input, $15/M output")
    print("=" * 60 + "\n")


# ═══════════════════════════════════════════════════════════════════════
# Synthetic market state for a given date
# ═══════════════════════════════════════════════════════════════════════

def build_synthetic_mso(date_str: str) -> MarketStateObject:
    """Build a synthetic MarketStateObject for testing.

    In production this would come from MT5 or historical CSV data.
    For manual testing we create a plausible bullish setup.
    """
    ts = f"{date_str}T07:15:00Z"

    def make_tf(direction: str, base_price: float) -> TimeframeState:
        return TimeframeState(
            swings=[
                Swing(index=0, type="low", price=base_price - 30, time=f"{date_str}T00:00:00Z"),
                Swing(index=5, type="high", price=base_price + 10, time=f"{date_str}T04:00:00Z"),
                Swing(index=10, type="low", price=base_price - 20, time=f"{date_str}T06:00:00Z"),
                Swing(index=15, type="high", price=base_price + 15, time=f"{date_str}T07:00:00Z"),
            ],
            structure=StructureAnalysis(
                direction=direction,
                protected_swing=Swing(
                    index=10, type="low", price=base_price - 20,
                    time=f"{date_str}T06:00:00Z",
                ),
                swing_sequence=["HH", "HL", "HH", "HL"] if direction == "bullish" else ["LH", "LL"],
                hh_count=2 if direction == "bullish" else 0,
                hl_count=2 if direction == "bullish" else 0,
            ),
            structure_events=[
                StructureEvent(
                    type="BOS" if direction == "bullish" else "CHoCH",
                    direction=direction,
                    level_broken=base_price + 5,
                    close_price=base_price + 8,
                    candle_index=14,
                    time=f"{date_str}T07:00:00Z",
                    displacement_present=True,
                    displacement_ratio=2.1,
                ),
            ],
            avg_candle_body=3.5,
        )

    m15_tf = TimeframeState(
        swings=[
            Swing(index=0, type="low", price=2693.0, time=f"{date_str}T07:00:00Z"),
            Swing(index=3, type="high", price=2705.0, time=f"{date_str}T07:15:00Z"),
        ],
        structure=StructureAnalysis(
            direction="bullish",
            protected_swing=Swing(index=0, type="low", price=2693.0, time=f"{date_str}T07:00:00Z"),
            swing_sequence=["HL", "HH"],
        ),
        structure_events=[
            StructureEvent(
                type="CHoCH",
                direction="bullish",
                level_broken=2703.0,
                close_price=2706.0,
                candle_index=3,
                time=f"{date_str}T07:15:00Z",
                displacement_present=True,
                displacement_ratio=2.3,
            ),
        ],
        avg_candle_body=2.0,
    )

    return MarketStateObject(
        timestamp_utc=ts,
        timeframes={
            "D1": make_tf("bullish", 2700.0),
            "H4": make_tf("bullish", 2700.0),
            "H1": make_tf("bullish", 2700.0),
            "M15": m15_tf,
        },
        session_levels=SessionLevels(
            asian_high=2710.0,
            asian_low=2690.0,
            pdh=2715.0,
            pdl=2685.0,
        ),
        spread_cents=22.0,
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=False,
            timestamp_utc=ts,
        ),
    )


# ═══════════════════════════════════════════════════════════════════════
# Main pipeline runner
# ═══════════════════════════════════════════════════════════════════════

async def run_pipeline(date_str: str, round2: bool = False, verbose: bool = False) -> None:
    """Run the full pipeline with real Claude API calls."""
    print(f"\n{'=' * 60}")
    print(f"LIVE API TEST — Date: {date_str}")
    print(f"{'=' * 60}\n")

    # Load config
    config_path = _PROJECT_ROOT / "config" / "agent_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    config["ai"]["debate_round2_enabled"] = round2

    # Initialize KB in a temp location
    test_kb_path = _PROJECT_ROOT / "knowledge_base_test_live"
    kb = KnowledgeBase(base_path=str(test_kb_path))
    kb.initialize_rules()

    # Build synthetic MSO
    mso = build_synthetic_mso(date_str)
    print(f"[MSO] Built synthetic MarketStateObject for {date_str}")
    print(f"  Daily: {mso.timeframes['D1'].structure.direction}")
    print(f"  H4:    {mso.timeframes['H4'].structure.direction}")
    print(f"  Spread: {mso.spread_cents} cents")
    print()

    # ── Step 1: Primary Analysis ──────────────────────────────────────
    print("[PRIMARY ANALYZER] Calling Claude API...")
    t0 = time.time()

    analyzer = PrimaryAnalyzer(config, kb)
    pa_result = await analyzer.analyze(mso)

    t1 = time.time()
    print(f"[PRIMARY ANALYZER] Done in {t1 - t0:.1f}s")
    print(f"  Decision:   {pa_result.decision}")
    print(f"  Confidence: {pa_result.confidence_score}")
    print(f"  Grade:      {pa_result.reasoning.setup_grade}")

    if pa_result.decision == "NO_TRADE":
        print(f"  Reason:     {pa_result.no_trade_reason}")
        print(f"\n  Daily Bias: {pa_result.reasoning.daily_bias.direction} "
              f"({pa_result.reasoning.daily_bias.confidence})")
        print(f"  H4 Aligned: {pa_result.reasoning.h4_alignment.aligned}")
        print(f"  Overall:    {pa_result.reasoning.overall_reasoning[:200]}")

    elif pa_result.decision == "CANDIDATE":
        tp = pa_result.trade_parameters
        if tp:
            print(f"  Direction:  {tp.direction}")
            print(f"  Entry:      {tp.entry_price}")
            print(f"  SL:         {tp.stop_loss}")
            print(f"  TP1:        {tp.take_profit_1}")
            print(f"  RR:         {tp.risk_reward_ratio}")

    if verbose:
        print(f"\n  Full response:\n{json.dumps(pa_result.model_dump(mode='json'), indent=2)}")

    # ── Step 2: Debate (if CANDIDATE) ─────────────────────────────────
    if pa_result.decision == "CANDIDATE":
        print(f"\n[DEBATE] Trade is CANDIDATE — initiating debate...")
        print(f"  Round 2 enabled: {round2}")

        t2 = time.time()
        debate = DebateEngine(config, kb)
        kb_context = kb.assemble_full_context(mso)
        verdict = await debate.run_debate(mso, pa_result, kb_context)
        t3 = time.time()

        print(f"\n[DEBATE] Done in {t3 - t2:.1f}s")
        print(f"  Verdict:       {verdict.verdict}")
        print(f"  Winner:        {verdict.winning_perspective}")
        print(f"  Confidence:    {verdict.confidence_score}")
        print(f"  Bull Strength: {verdict.bull_argument_strength}")
        print(f"  Bear Strength: {verdict.bear_argument_strength}")
        print(f"  Key Factor:    {verdict.key_factor[:200]}")
        print(f"  Summary:       {verdict.summary[:200]}")

        decision = DebateEngine.evaluate_verdict(verdict)
        print(f"\n  Final Decision: {decision}")

        if verbose:
            print(f"\n  Full verdict:\n{json.dumps(verdict.model_dump(mode='json'), indent=2)}")

    else:
        print("\n[DEBATE] Skipped — not a CANDIDATE.")

    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE")
    print(f"{'=' * 60}\n")


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manual integration test with real Claude API calls.",
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Historical date in YYYY-MM-DD format (e.g., 2025-11-15)",
    )
    parser.add_argument(
        "--cost-estimate",
        action="store_true",
        help="Print estimated API cost without making any calls.",
    )
    parser.add_argument(
        "--round2",
        action="store_true",
        help="Enable debate Round 2 (rebuttals).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full JSON responses.",
    )

    args = parser.parse_args()

    # Validate date
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD.")
        sys.exit(1)

    if args.cost_estimate:
        print_cost_estimate(round2=args.round2)
        return

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    asyncio.run(run_pipeline(args.date, round2=args.round2, verbose=args.verbose))


if __name__ == "__main__":
    main()
