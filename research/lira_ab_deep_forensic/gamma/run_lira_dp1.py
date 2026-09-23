#!/usr/bin/env python3
"""LIRA DP1 — measure LIRA self-consistency on 4 A2 divergent candles.

Mirrors DP1 methodology exactly (run_dp1.py) but swaps in the LIRA
prompt + schema adapter. Goal: is LIRA internally deterministic like
V3 (DP1: 100%) or noisier?

Config: Sonnet 4.6, output_config={"effort": "max"}, temperature=0,
detector_version=v2 (apples-to-apples with DP1).

Budget cap: $5 hard, halts on per-call > $0.30 ceiling.

Usage:
    set -a && source .env && set +a
    python research/lira_ab_deep_forensic/gamma/run_lira_dp1.py
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
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
logger = logging.getLogger("lira_dp1")

from scripts.simulate_t7_live_period import (  # noqa: E402
    build_mso_for_candle,
    load_csv_data,
)

OUT_DIR = PROJECT_ROOT / "research" / "lira_ab_deep_forensic" / "gamma"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# A2 divergent candles — same set DP1 measured for V3 self-consistency.
TARGETS = [
    {
        "idx": 1,
        "candle_time": "2026-02-02T07:00:00Z",
        "kill_zone": "london",
        "category": "override_computed_bias_candidate_short",
        "a2_decision": "REJECTED_L2",
        "a2_pa_decision": "CANDIDATE",
        "a2_direction": "SHORT",
        "a2_bias_direction": "bearish",
        "a2_setup_grade": "A+",
        "a2_no_trade_reason": None,
    },
    {
        "idx": 2,
        "candle_time": "2026-02-04T13:30:00Z",
        "kill_zone": "ny",
        "category": "missing_m15_opposition_detection",
        "a2_decision": "CANDIDATE",
        "a2_pa_decision": "CANDIDATE",
        "a2_direction": "LONG",
        "a2_bias_direction": "bullish",
        "a2_setup_grade": "A+",
        "a2_no_trade_reason": None,
    },
    {
        "idx": 3,
        "candle_time": "2026-02-04T13:45:00Z",
        "kill_zone": "ny",
        "category": "detected_m15_opposition",
        "a2_decision": "NO_TRADE",
        "a2_pa_decision": "NO_TRADE",
        "a2_direction": "",
        "a2_bias_direction": "bullish",
        "a2_setup_grade": "C",
        "a2_no_trade_reason": "c2_m15_opposing",
    },
    {
        "idx": 4,
        "candle_time": "2026-02-06T07:30:00Z",
        "kill_zone": "london",
        "category": "respects_h1_bearish_mso",
        "a2_decision": "NO_TRADE",
        "a2_pa_decision": "NO_TRADE",
        "a2_direction": "",
        "a2_bias_direction": "bullish",
        "a2_setup_grade": "C",
        "a2_no_trade_reason": "c1_failed",
    },
]

RUNS_PER_CANDLE = 5
BUDGET_CAP_USD = 5.0
PER_CALL_CEILING_USD = 0.30  # halt if crossed

INPUT_COST = 3.0 / 1_000_000
OUTPUT_COST = 15.0 / 1_000_000


def _import_lira_module():
    """Load research/v4_prompt_engineering/dp4_lira/prompt_lira.py and schema_adapter.py."""
    dp4_dir = PROJECT_ROOT / "research" / "v4_prompt_engineering" / "dp4_lira"
    spec_p = importlib.util.spec_from_file_location("dp4_lira_prompt", dp4_dir / "prompt_lira.py")
    assert spec_p is not None and spec_p.loader is not None
    mod_p = importlib.util.module_from_spec(spec_p)
    spec_p.loader.exec_module(mod_p)
    assert mod_p.VARIANT_NAME == "lira"

    spec_a = importlib.util.spec_from_file_location("dp4_lira_adapter", dp4_dir / "schema_adapter.py")
    assert spec_a is not None and spec_a.loader is not None
    mod_a = importlib.util.module_from_spec(spec_a)
    spec_a.loader.exec_module(mod_a)
    return mod_p, mod_a


def _mso_to_dict(mso) -> dict:
    """Serialise MSO dataclass hierarchy to JSON. Lifted from run_dp1."""
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


async def evaluate_once(
    mso,
    kill_zone: str,
    config: dict,
    lira_mod,
    adapter_mod,
) -> tuple[dict, float, str]:
    """Run one LIRA API call. Returns (report, cost, raw_text)."""
    import anthropic

    system_prompt = lira_mod.build_system_prompt(config)
    static_ctx = lira_mod.build_static_context(mso)
    candle_time = getattr(mso, "timestamp_utc", "") or ""
    current_time = candle_time if candle_time else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    user_msg = lira_mod.build_user_message(
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
    cost = input_tokens * INPUT_COST + output_tokens * OUTPUT_COST

    # Parse via LIRA adapter (handles double-block self-corrections)
    adapted_report, pa_obj = adapter_mod.adapt_variant_response(
        text, candle_time, kill_zone, "lira",
    )

    # Pull confidence_tier directly from the parsed JSON because the adapter
    # report doesn't carry it (it's LIRA-specific).
    confidence_tier = None
    setup_grade_raw = None
    bias_direction = None
    bias_confidence = None
    no_trade_reason_raw = None
    parse_data = adapter_mod._parse_json_text(text)
    if parse_data is not None:
        confidence_tier = parse_data.get("confidence_tier")
        setup_grade_raw = parse_data.get("setup_grade")
        no_trade_reason_raw = parse_data.get("no_trade_reason")
        just = parse_data.get("justification") or {}
        bias_block = just.get("daily_bias") or {}
        bias_direction = bias_block.get("direction")
        bias_confidence = bias_block.get("confidence")

    decision = adapted_report.get("decision", "PARSE_ERROR")
    direction = adapted_report.get("direction", "") or ""

    report = {
        "candle_time": candle_time,
        "kill_zone": kill_zone,
        "decision": decision,
        "direction": direction,
        "confidence_tier": confidence_tier,
        "setup_grade": setup_grade_raw or adapted_report.get("setup_grade"),
        "no_trade_reason": no_trade_reason_raw or adapted_report.get("no_trade_reason"),
        "daily_bias_direction": bias_direction,
        "daily_bias_confidence": bias_confidence,
        "entry_price": adapted_report.get("entry_price"),
        "stop_loss": adapted_report.get("stop_loss"),
        "take_profit_1": adapted_report.get("take_profit_1"),
        "poi_price_level": adapted_report.get("poi_price_level"),
        "adapter_built_pa_obj": pa_obj is not None,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": round(cost, 4),
    }
    return report, cost, text


async def run_target(
    target: dict,
    all_candles: dict,
    config: dict,
    lira_mod,
    adapter_mod,
    total_cost_ref: list,
) -> None:
    candle_time = target["candle_time"]
    kill_zone = target["kill_zone"]
    target_date = date.fromisoformat(candle_time[:10])
    idx = target["idx"]
    ts_slug = candle_time.replace(":", "_").replace("-", "").replace("T", "_").replace("Z", "")

    logger.info("=" * 60)
    logger.info("Candle %d: %s (%s)", idx, candle_time, kill_zone)
    logger.info("A2 original: %s %s (%s)", target["a2_decision"], target["a2_direction"], target["category"])

    try:
        mso = build_mso_for_candle(all_candles, candle_time, target_date, config)
    except Exception as e:
        logger.error("MSO build FAILED for %s: %s", candle_time, e)
        target["mso_build_error"] = str(e)
        return

    mso_path = OUT_DIR / f"mso_{idx}_{ts_slug}.json"
    mso_dict = _mso_to_dict(mso)
    with open(mso_path, "w") as f:
        json.dump(mso_dict, f, indent=2, default=str)
    logger.info("MSO saved: %s (%d bytes)", mso_path.name, mso_path.stat().st_size)

    target["mso_summary"] = {
        "h1_direction": mso_dict.get("timeframes", {}).get("H1", {}).get("structure", {}).get("direction"),
        "m15_direction": mso_dict.get("timeframes", {}).get("M15", {}).get("structure", {}).get("direction"),
        "h4_direction": mso_dict.get("timeframes", {}).get("H4", {}).get("structure", {}).get("direction"),
        "d1_direction": mso_dict.get("timeframes", {}).get("D1", {}).get("structure", {}).get("direction"),
    }

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
                report, cost, raw_text = await evaluate_once(
                    mso, kill_zone, config, lira_mod, adapter_mod,
                )
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
                "    decision=%s direction=%s tier=%s grade=%s cost=$%.4f time=%.1fs  (total $%.4f)",
                report.get("decision"),
                report.get("direction"),
                report.get("confidence_tier"),
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

    with open(PROJECT_ROOT / "config" / "agent_config.yaml") as fh:
        config = yaml.safe_load(fh)
    config = apply_instrument_overrides(config, "XAUUSD")
    # Pin v2 detector to mirror DP1 + ensure apples-to-apples MSO build.
    config.setdefault("market_state", {})["detector_version"] = "v2"
    config.setdefault("market", {})["symbol"] = "XAUUSD"

    logger.info(
        "Config: primary_model=%s primary_effort=%s detector_version=%s",
        config.get("ai", {}).get("primary_model"),
        config.get("ai", {}).get("primary_effort"),
        config.get("market_state", {}).get("detector_version"),
    )

    lira_mod, adapter_mod = _import_lira_module()
    logger.info("Loaded LIRA prompt + schema adapter")

    all_candles = load_csv_data("XAUUSD")
    if not all_candles.get("M15"):
        logger.error("No M15 data for XAUUSD")
        sys.exit(1)

    total_cost_ref = [0.0]
    t_start = time.time()

    for target in TARGETS:
        await run_target(target, all_candles, config, lira_mod, adapter_mod, total_cost_ref)
        if total_cost_ref[0] >= BUDGET_CAP_USD:
            logger.warning("Budget exhausted — halting further candles.")
            break

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
        "variant": "lira",
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
    with open(OUT_DIR / "lira_dp1_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("=" * 60)
    logger.info("DONE. total cost=$%.4f, elapsed=%.1f min", total_cost_ref[0], elapsed_min)
    logger.info("Summary: %s", OUT_DIR / "lira_dp1_summary.json")


if __name__ == "__main__":
    asyncio.run(main())
