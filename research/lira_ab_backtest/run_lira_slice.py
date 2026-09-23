#!/usr/bin/env python3
"""LIRA 12-slice A/B backtest — single-slice runner.

Mirrors `research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py` but
accepts symbol / start / end / output-dir directly via CLI so the same
script can drive all 12 A2/F3 slices (XAUUSD x8 + USDJPY x4).

Apples-to-apples with A2 v2-active backtest:
  - same slice boundaries (XAUUSD 12-day windows, USDJPY 25-day windows)
  - --detector-version v2 (NOT v2_shadow)
  - same fill / outcome logic via simulate_t7
  - LIRA prompt + schema_adapter monkey-patched in (replace V3 system prompt
    + replace simulate_t7._parse_response with adapt_variant_response)

Usage:
    set -a && source .env && set +a
    python research/lira_ab_backtest/run_lira_slice.py \
        --symbol XAUUSD --start 2026-01-02 --end 2026-01-14 \
        --output-dir research/lira_ab_backtest/slices/xauusd_s1 --budget 6
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import logging
import os
import sys
import time as time_mod
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("lira_ab")


def _load_lira_module():
    path = PROJECT_ROOT / "research" / "v4_prompt_engineering" / "dp4_lira" / "prompt_lira.py"
    spec = importlib.util.spec_from_file_location("lira_ab_prompt_lira", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _install_lira() -> None:
    """Patch primary_analyzer_prompt with LIRA + simulate_t7._parse_response with adapter."""
    import src.prompts.primary_analyzer_prompt as prod
    lira = _load_lira_module()

    prod.build_system_prompt = lira.build_system_prompt
    prod.build_user_message = lira.build_user_message
    prod.build_static_context = lira.build_static_context
    logger.info("LIRA prompt installed: system-prompt len=%d",
                len(lira.build_system_prompt({})))

    import scripts.simulate_t7_live_period as sim
    from research.v4_prompt_engineering.dp4_lira.schema_adapter import (
        adapt_variant_response,
    )

    def _patched_parse_response(text: str, candle_time: str, kill_zone: str):
        return adapt_variant_response(text, candle_time, kill_zone, "lira")

    sim._parse_response = _patched_parse_response
    logger.info("simulate_t7._parse_response patched to use LIRA adapter")


async def main_async(args) -> None:
    _install_lira()

    import scripts.simulate_t7_live_period as sim
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    sim.OUTPUT_DIR = out_dir

    sim_args = argparse.Namespace(
        source="csv",
        start=args.start,
        end=args.end,
        symbol=args.symbol,
        budget=args.budget,
        dry_run=False,
        data_dir=str(PROJECT_ROOT / "data" / "historical_2026"),
        output_dir=str(out_dir),
        detector_version="v2",
        a1_backtest_log_path=None,
        slice_tag=f"lira_{args.symbol.lower()}_{args.start}_{args.end}",
    )

    t0 = time_mod.time()
    await sim.run_simulation(sim_args)
    logger.info("LIRA slice %s %s..%s complete in %.1fs  out=%s",
                args.symbol, args.start, args.end, time_mod.time() - t0, out_dir)


def main():
    parser = argparse.ArgumentParser(description="LIRA 12-slice A/B backtest runner")
    parser.add_argument("--symbol", required=True, choices=["XAUUSD", "USDJPY"])
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--budget", type=float, default=6.0,
                        help="USD budget hard cap (default $6/slice)")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
