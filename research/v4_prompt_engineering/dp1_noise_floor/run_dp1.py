#!/usr/bin/env python3
"""DP1 V3 noise-floor measurement.

For each of 4 A2 divergent XAUUSD candles, rebuild the MSO and call the
current V3 production prompt 5x with Sonnet 4.6 effort=max. Log all
responses. Measure self-agreement rate.

Pre-registered thresholds (from V4_SYNTHESIS_AND_PLAN.md line 125):
 - >=85% agreement: V3 is deterministic -> V4 iteration on-target
 - 70-85%: mostly deterministic but noise exists -> caveat
 - <70%: V3 is noise-driven -> V4 validation needs larger samples

Usage:
    set -a && source .env && set +a
    python research/v4_prompt_engineering/dp1_noise_floor/run_dp1.py

Matches A2 config:
 - detector_version: v2 (override)
 - Sonnet 4.6 effort=max via output_config (per src/components/primary_analyzer.py:358)
 - temperature=0
 - max_tokens=2000

Budget cap: $2 hard, halts if per-call spend > $0.25.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger("dp1")

from scripts.simulate_t7_live_period import (  # noqa: E402
    build_mso_for_candle,
    load_csv_data,
)

OUT_DIR = PROJECT_ROOT / "research" / "v4_prompt_engineering" / "dp1_noise_floor"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Candles to test (A2 original decisions in COMMENT; actual decisions re-verified
# against all_results.json earlier)
TARGETS = [
    {
        "idx": 1,
        "candle_time": "2026-02-02T07:00:00Z",
        "kill_zone": "london",
        "a2_decision": "REJECTED_L2",
        "a2_pa_decision": "CANDIDATE",
        "a2_direction": "SHORT",
        "a2_bias_direction": "bearish",
        "a2_setup_grade": "A+",
        "a2_no_trade_reason": None,
        "category": "override_computed_bias_candidate_short",
    },
    {
        "idx": 2,
        "candle_time": "2026-02-04T13:30:00Z",
        "kill_zone": "ny",
        "a2_decision": "CANDIDATE",
        "a2_pa_decision": "CANDIDATE",
        "a2_direction": "LONG",
        "a2_bias_direction": "bullish",
        "a2_setup_grade": "A+",
        "a2_no_trade_reason": None,
        "category": "missing_m15_opposition_detection",
    },
    {
        "idx": 3,
        "candle_time": "2026-02-04T13:45:00Z",
        "kill_zone": "ny",
        "a2_decision": "NO_TRADE",
        "a2_pa_decision": "NO_TRADE",
        "a2_direction": "",
        "a2_bias_direction": "bullish",
        "a2_setup_grade": "C",
        "a2_no_trade_reason": "c2_m15_opposing",
        "category": "detected_m15_opposition",
    },
    {
        "idx": 4,
        "candle_time": "2026-02-06T07:30:00Z",
        "kill_zone": "london",
        "a2_decision": "NO_TRADE",
        "a2_pa_decision": "NO_TRADE",
        "a2_direction": "",
        "a2_bias_direction": "bullish",
        "a2_setup_grade": "C",
        "a2_no_trade_reason": "c1_failed",
        "category": "respects_h1_bearish_mso",
    },
]

RUNS_PER_CANDLE = 5
BUDGET_CAP_USD = 2.0
PER_CALL_CEILING_USD = 0.25  # halt if crossed


def _mso_to_dict(mso) -> dict:
    """Serialise a market-state dataclass hierarchy to plain JSON.

    Uses dataclasses.asdict where possible, falling back to vars() / str().
    """
    import dataclasses as _dc

    def _serialize(obj):
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [_serialize(x) for x in obj]
        if isinstance(obj, dict):
            return {str(k): _serialize(v) for k, v in obj.items()}
        if _dc.is_dataclass(obj):
            return _serialize(_dc.asdict(obj))
        if hasattr(obj, "__dict__"):
            return {k: _serialize(v) for k, v in vars(obj).items() if not k.startswith("_")}
        return str(obj)

    return _serialize(mso)


async def evaluate_once(mso, kill_zone: str, config: dict) -> tuple[dict, float, str]:
    """Run one V3 API call against the given MSO/kill-zone. Returns (report, cost, raw_text)."""
    import anthropic
    from src.prompts.primary_analyzer_prompt import build_system_prompt, build_user_message, build_static_context
    from src.utils.validation import strip_json_fences

    system_prompt = build_system_prompt(config)
    static_ctx = build_static_context(mso)
    candle_time = getattr(mso, "timestamp_utc", "") or ""
    current_time = candle_time if candle_time else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    user_msg = build_user_message(
        mso, {}, current_time,
        kill_zone=kill_zone,
        additional_context="",
    )

    client = anthropic.Anthropic()

    model_id = config.get("ai", {}).get("primary_model", "claude-sonnet-4-6")
    effort = config.get("ai", {}).get("primary_effort", "max")

    response = client.messages.create(
        model=model_id,
        max_tokens=2000,
        temperature=0,
        output_config={"effort": effort},
        system=f"{system_prompt}\n\n## Static Context (D1/H4/Session)\n{static_ctx}",
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text if response.content else ""
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    INPUT_COST = 3.0 / 1_000_000
    OUTPUT_COST = 15.0 / 1_000_000
    cost = input_tokens * INPUT_COST + output_tokens * OUTPUT_COST

    # Parse
    cleaned = strip_json_fences(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "candle_time": candle_time,
            "kill_zone": kill_zone,
            "decision": "PARSE_ERROR",
            "error": "JSON decode failed",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": round(cost, 4),
        }, cost, text

    report = {
        "candle_time": candle_time,
        "kill_zone": kill_zone,
        "decision": data.get("decision", "PARSE_ERROR"),
        "daily_bias_direction": data.get("reasoning", {}).get("daily_bias", {}).get("direction", "?"),
        "daily_bias_confidence": data.get("reasoning", {}).get("daily_bias", {}).get("confidence", "?"),
        "setup_grade": data.get("reasoning", {}).get("setup_grade", "?"),
        "no_trade_reason": data.get("no_trade_reason", None),
        "confidence_score": data.get("confidence_score", None),
        "framework": data.get("framework", None),
        "direction": (data.get("trade_parameters") or {}).get("direction", ""),
        "entry_price": (data.get("trade_parameters") or {}).get("entry_price", None),
        "stop_loss": (data.get("trade_parameters") or {}).get("stop_loss", None),
        "take_profit_1": (data.get("trade_parameters") or {}).get("take_profit_1", None),
        "model_reported_name": data.get("model_used", "?"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": round(cost, 4),
    }
    return report, cost, text


async def run_target(
    target: dict,
    all_candles: dict,
    config: dict,
    symbol: str,
    total_cost_ref: list,
) -> None:
    candle_time = target["candle_time"]
    kill_zone = target["kill_zone"]
    target_date = date.fromisoformat(candle_time[:10])
    idx = target["idx"]
    ts_slug = candle_time.replace(":", "_").replace("-", "").replace("T", "_").replace("Z", "")

    # Build MSO
    logger.info("=" * 60)
    logger.info("Candle %d: %s (%s)", idx, candle_time, kill_zone)
    logger.info("A2 original: %s %s (%s)", target["a2_decision"], target["a2_direction"], target["category"])

    try:
        mso = build_mso_for_candle(all_candles, candle_time, target_date, config)
    except Exception as e:
        logger.error("MSO build FAILED for %s: %s", candle_time, e)
        target["mso_build_error"] = str(e)
        return

    # Save MSO
    mso_path = OUT_DIR / f"mso_{idx}_{ts_slug}.json"
    mso_dict = _mso_to_dict(mso)
    # Trim verbose structure detector fields to keep file readable
    with open(mso_path, "w") as f:
        json.dump(mso_dict, f, indent=2, default=str)
    logger.info("MSO saved: %s (%d bytes)", mso_path.name, mso_path.stat().st_size)

    # Also capture MSO summary for report
    target["mso_summary"] = {
        "h1_direction": mso_dict.get("timeframes", {}).get("H1", {}).get("structure", {}).get("direction"),
        "m15_direction": mso_dict.get("timeframes", {}).get("M15", {}).get("structure", {}).get("direction"),
        "h4_direction": mso_dict.get("timeframes", {}).get("H4", {}).get("structure", {}).get("direction"),
        "d1_direction": mso_dict.get("timeframes", {}).get("D1", {}).get("structure", {}).get("direction"),
    }

    # Run RUNS_PER_CANDLE times
    replay_path = OUT_DIR / f"replays_{idx}_{ts_slug}.jsonl"
    reports = []
    with open(replay_path, "w") as fh:
        for run_i in range(1, RUNS_PER_CANDLE + 1):
            if total_cost_ref[0] >= BUDGET_CAP_USD:
                logger.error("BUDGET CAP $%.2f reached before run %d. Halting.", BUDGET_CAP_USD, run_i)
                break
            logger.info("  Run %d/%d ...", run_i, RUNS_PER_CANDLE)
            t0 = time.time()
            try:
                report, cost, raw_text = await evaluate_once(mso, kill_zone, config)
            except Exception as e:
                logger.error("  API call failed: %s", e)
                error_row = {
                    "run": run_i,
                    "candle_time": candle_time,
                    "error": str(e),
                    "cost": 0,
                }
                fh.write(json.dumps(error_row) + "\n")
                continue

            elapsed = time.time() - t0
            report["run"] = run_i
            report["elapsed_s"] = round(elapsed, 1)
            report["raw_response"] = raw_text
            reports.append(report)
            total_cost_ref[0] += cost

            logger.info(
                "    decision=%s direction=%s bias=%s grade=%s cost=$%.4f time=%.1fs  (total $%.4f)",
                report.get("decision"),
                report.get("direction"),
                report.get("daily_bias_direction"),
                report.get("setup_grade"),
                cost,
                elapsed,
                total_cost_ref[0],
            )

            if cost > PER_CALL_CEILING_USD:
                logger.error("Per-call cost $%.4f exceeded ceiling $%.2f. Halting.", cost, PER_CALL_CEILING_USD)
                break

            fh.write(json.dumps(report) + "\n")
            fh.flush()

    target["replay_path"] = str(replay_path.relative_to(PROJECT_ROOT))
    target["mso_path"] = str(mso_path.relative_to(PROJECT_ROOT))
    target["reports"] = reports


async def main() -> None:
    import yaml
    from src.utils.config import apply_instrument_overrides

    # Load config, apply XAUUSD overrides, force detector_version=v2 to match A2
    with open(PROJECT_ROOT / "config" / "agent_config.yaml") as fh:
        config = yaml.safe_load(fh)
    config = apply_instrument_overrides(config, "XAUUSD")
    config.setdefault("market_state", {})["detector_version"] = "v2"
    # Ensure symbol is set so MSO attaches it
    config.setdefault("market", {})["symbol"] = "XAUUSD"

    logger.info("Config: primary_model=%s primary_effort=%s detector_version=%s",
                config.get("ai", {}).get("primary_model"),
                config.get("ai", {}).get("primary_effort"),
                config.get("market_state", {}).get("detector_version"))

    # Load all candles for XAUUSD
    all_candles = load_csv_data("XAUUSD")
    if not all_candles.get("M15"):
        logger.error("No M15 data for XAUUSD")
        sys.exit(1)

    total_cost_ref = [0.0]
    t_start = time.time()

    for target in TARGETS:
        await run_target(target, all_candles, config, "XAUUSD", total_cost_ref)
        if total_cost_ref[0] >= BUDGET_CAP_USD:
            logger.warning("Budget exhausted — halting further candles.")
            break

    # Final summary JSON
    elapsed_min = (time.time() - t_start) / 60.0
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_minutes": round(elapsed_min, 2),
        "total_cost_usd": round(total_cost_ref[0], 4),
        "budget_cap_usd": BUDGET_CAP_USD,
        "runs_per_candle": RUNS_PER_CANDLE,
        "config_primary_model": config.get("ai", {}).get("primary_model"),
        "config_primary_effort": config.get("ai", {}).get("primary_effort"),
        "detector_version": config.get("market_state", {}).get("detector_version"),
        "targets": [
            {
                "idx": t["idx"],
                "candle_time": t["candle_time"],
                "kill_zone": t["kill_zone"],
                "category": t["category"],
                "a2_decision": t["a2_decision"],
                "a2_pa_decision": t["a2_pa_decision"],
                "a2_direction": t["a2_direction"],
                "a2_bias_direction": t["a2_bias_direction"],
                "a2_setup_grade": t["a2_setup_grade"],
                "a2_no_trade_reason": t["a2_no_trade_reason"],
                "mso_summary": t.get("mso_summary"),
                "mso_path": t.get("mso_path"),
                "replay_path": t.get("replay_path"),
                "n_reports": len(t.get("reports", [])),
                "reports": [
                    {k: v for k, v in r.items() if k != "raw_response"}
                    for r in t.get("reports", [])
                ],
            }
            for t in TARGETS
        ],
    }
    with open(OUT_DIR / "dp1_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("=" * 60)
    logger.info("DONE. total cost=$%.4f, elapsed=%.1f min", total_cost_ref[0], elapsed_min)
    logger.info("Summary: %s", OUT_DIR / "dp1_summary.json")


if __name__ == "__main__":
    asyncio.run(main())
