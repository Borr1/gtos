#!/usr/bin/env python3
"""DP4 mini-backtest — one XAUUSD slice end-to-end, one variant at a time.

Monkey-patches `src.prompts.primary_analyzer_prompt.build_system_prompt`
with the target variant's implementation, then runs
`simulate_t7_live_period.run_simulation` over a narrow date range.

All three runs share the same slice so the cross-variant comparison is
apples-to-apples (same MSOs, same fill logic, same outcome lookup).

Usage:
    set -a && source .env && set +a
    python research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py \
        --variant v3_control --slice xauusd_s3 --budget 4
    python research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py \
        --variant lira --slice xauusd_s3 --budget 4
    python research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py \
        --variant nocot --slice xauusd_s3 --budget 4
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import json
import logging
import os
import sys
import time as time_mod
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("dp4_mini")


SLICE_WINDOWS = {
    # Mirror the F3 slice date ranges used in session-38 backtest so the
    # DP4 numbers can be compared back against the F3 baseline per-slice.
    # Dates verified against research/f3_backtest_2026-04-24/*.log per-slice
    # "kill-zone candles in YYYY-MM-DD to YYYY-MM-DD" lines.
    "xauusd_s3": ("2026-01-28", "2026-02-09"),
    "xauusd_s7": ("2026-03-21", "2026-04-02"),
    "usdjpy_s3": ("2026-02-21", "2026-03-17"),
}

SLICE_SYMBOLS = {
    "xauusd_s3": "XAUUSD",
    "xauusd_s7": "XAUUSD",
    "usdjpy_s3": "USDJPY",
}


def _load_variant_module(name: str):
    filename = {
        "v3_control": "prompt_v3.py",
        "lira": "prompt_lira.py",
        "nocot": "prompt_nocot.py",
    }[name]
    path = Path(__file__).parent / filename
    spec = importlib.util.spec_from_file_location(f"dp4_bt_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _install_variant(name: str) -> None:
    """Patch src.prompts.primary_analyzer_prompt to use the chosen variant,
    AND patch simulate_t7._parse_response to use our schema adapter.

    simulate_t7's `evaluate_with_t7` calls
    `from src.prompts.primary_analyzer_prompt import build_system_prompt,
    build_user_message, build_static_context` inside the function body, so
    we have to patch the ATTRIBUTES on the already-imported module (a
    pointer-swap on the names that function imports).

    For parse-response we swap the module-level function so every
    LIRA/No-CoT response gets shaped into a pydantic-valid
    PrimaryAnalysisOutput. Without this swap, LIRA/No-CoT CANDIDATEs would
    all fall through to NO_TRADE_PARSE_FAIL in simulate_t7 line 889 and
    the mini-backtest comparison would be meaningless.
    """
    # Variant prompt wiring
    import src.prompts.primary_analyzer_prompt as prod
    variant = _load_variant_module(name)

    if name != "v3_control":
        prod.build_system_prompt = variant.build_system_prompt
        prod.build_user_message = variant.build_user_message
        prod.build_static_context = variant.build_static_context
        logger.info("Variant %s prompt installed: system-prompt len=%d",
                    name, len(variant.build_system_prompt({})))
    else:
        logger.info("Variant v3_control prompt installed (production V3)")

    # Schema-adapter wiring: monkey-patch simulate_t7._parse_response
    import scripts.simulate_t7_live_period as sim
    from research.v4_prompt_engineering.dp4_lira.schema_adapter import (
        adapt_variant_response,
    )

    def _patched_parse_response(text: str, candle_time: str, kill_zone: str):
        return adapt_variant_response(text, candle_time, kill_zone, name)

    sim._parse_response = _patched_parse_response
    logger.info("simulate_t7._parse_response patched to use %s adapter", name)


async def main_async(args) -> None:
    _install_variant(args.variant)

    # Override OUTPUT_DIR BEFORE importing run_simulation so it picks up
    # our variant-specific output root.
    import scripts.simulate_t7_live_period as sim
    out_dir = PROJECT_ROOT / "research" / "v4_prompt_engineering" / "dp4_lira" / f"mini_backtest_{args.variant}_{args.slice}"
    out_dir.mkdir(parents=True, exist_ok=True)
    sim.OUTPUT_DIR = out_dir

    start, end = SLICE_WINDOWS[args.slice]
    symbol = SLICE_SYMBOLS[args.slice]
    sim_args = argparse.Namespace(
        source="csv",
        start=start,
        end=end,
        symbol=symbol,
        budget=args.budget,
        dry_run=False,
        data_dir=str(PROJECT_ROOT / "data" / "historical_2026"),
        output_dir=str(out_dir),
        detector_version="v2",
        a1_backtest_log_path=None,
        slice_tag=f"dp4_{args.variant}_{args.slice}",
    )

    t0 = time_mod.time()
    await sim.run_simulation(sim_args)
    logger.info("Mini-backtest %s / %s complete in %.1fs  out=%s",
                args.variant, args.slice, time_mod.time() - t0, out_dir)


def main():
    parser = argparse.ArgumentParser(description="DP4 mini-backtest runner")
    parser.add_argument("--variant", required=True,
                        choices=["v3_control", "lira", "nocot"])
    parser.add_argument("--slice", required=True, choices=list(SLICE_WINDOWS))
    parser.add_argument("--budget", type=float, default=4.0,
                        help="Per-variant USD budget hard cap (passed to simulate_t7)")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
