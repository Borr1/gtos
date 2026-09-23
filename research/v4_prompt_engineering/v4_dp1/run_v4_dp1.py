#!/usr/bin/env python3
"""V4-DP1 — V4 DRAFT prompt replay on the 4 A2 divergent XAUUSD candles.

Mirror of DP1 methodology (5x per candle, Sonnet 4.6 effort=max, temperature=0,
detector_version=v2) but swapping V3 production system prompt for the V4 DRAFT
system prompt at `research/v4_prompt_engineering/primary_analyzer_prompt_v4_DRAFT.py`.

Notes:
 - V4 DRAFT only overrides the system prompt template. The user message
   builder + static context builder are UNCHANGED from V3, per the V4 DRAFT's
   own docstring: "Rest of file (user message builder etc.) remains
   identical to V3. Not re-including here since V4 only modifies
   _SYSTEM_PROMPT_TEMPLATE block."
 - MSO build uses same path as DP1 (scripts.simulate_t7_live_period) and
   same detector_version=v2 override so MSO state is bit-identical to DP1
   run (which is in turn bit-identical to A2's MSO state).

Budget cap: $2 hard, halts if per-call spend > $0.25 (mirrors DP1).

Usage:
    set -a && source .env && set +a
    python research/v4_prompt_engineering/v4_dp1/run_v4_dp1.py
"""

from __future__ import annotations

import asyncio
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
logger = logging.getLogger("v4_dp1")

from scripts.simulate_t7_live_period import (  # noqa: E402
    build_mso_for_candle,
    load_csv_data,
)

OUT_DIR = PROJECT_ROOT / "research" / "v4_prompt_engineering" / "v4_dp1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V4_DRAFT_PATH = (
    PROJECT_ROOT
    / "research"
    / "v4_prompt_engineering"
    / "primary_analyzer_prompt_v4_DRAFT.py"
)


def _load_v4_draft_system_prompt_builder():
    """Dynamically load V4 DRAFT's build_system_prompt + set_price_format.

    We DO NOT want to shadow the production primary_analyzer_prompt module;
    we ONLY want V4's system-prompt template. The user message + static
    context builders come from V3 production (unchanged, per V4 docstring).
    """
    spec = importlib.util.spec_from_file_location(
        "v4_draft_prompt_module", V4_DRAFT_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Candles — identical to DP1 (A2 divergent candles)
TARGETS = [
    {
        "idx": 1,
        "candle_time": "2026-02-02T07:00:00Z",
        "kill_zone": "london",
        "v3_typical_decision": "NO_TRADE",
        "v3_typical_direction": "",
        "v3_typical_reason": "c1_failed",
        "f3_actual": "LONG WIN +1.5R",
        "a2_actual": "CAND SHORT -> L2-rej 0R",
        "counterfactual_R": {"LONG": 1.5, "SHORT": 0.0, "NO_TRADE": 0.0},
        "v3_typical_R": 0.0,
    },
    {
        "idx": 2,
        "candle_time": "2026-02-04T13:30:00Z",
        "kill_zone": "ny",
        "v3_typical_decision": "NO_TRADE",
        "v3_typical_direction": "",
        "v3_typical_reason": "c1_failed",
        "f3_actual": "NO_TRADE",
        "a2_actual": "LONG LOSS -1R",
        "counterfactual_R": {"LONG": -1.0, "SHORT": 0.0, "NO_TRADE": 0.0},
        "v3_typical_R": 0.0,
    },
    {
        "idx": 3,
        "candle_time": "2026-02-04T13:45:00Z",
        "kill_zone": "ny",
        "v3_typical_decision": "NO_TRADE",
        "v3_typical_direction": "",
        "v3_typical_reason": "c1_failed",  # or c2_m15_opposing (mix 3:2 in DP1)
        "f3_actual": "LONG LOSS -1R",
        "a2_actual": "NO_TRADE",
        "counterfactual_R": {"LONG": -1.0, "SHORT": 0.0, "NO_TRADE": 0.0},
        "v3_typical_R": 0.0,
    },
    {
        "idx": 4,
        "candle_time": "2026-02-06T07:30:00Z",
        "kill_zone": "london",
        "v3_typical_decision": "CANDIDATE",
        "v3_typical_direction": "LONG",
        "v3_typical_reason": None,
        "f3_actual": "LONG WIN +1.5R",
        "a2_actual": "NO_TRADE c1_failed",
        "counterfactual_R": {"LONG": 1.5, "SHORT": 0.0, "NO_TRADE": 0.0},
        "v3_typical_R": 1.5,
    },
]

RUNS_PER_CANDLE = 5
BUDGET_CAP_USD = 2.0
PER_CALL_CEILING_USD = 0.25


def _mso_to_dict(mso) -> dict:
    """Serialise a market-state dataclass hierarchy to plain JSON (same as DP1)."""
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
    v4_module,
    mso,
    kill_zone: str,
    config: dict,
) -> tuple[dict, float, str]:
    """Run one V4 API call. Returns (report, cost, raw_text)."""
    import anthropic
    from src.prompts.primary_analyzer_prompt import build_user_message, build_static_context
    from src.utils.validation import strip_json_fences

    # Sync price format between V4 and V3 modules — V4's build_system_prompt
    # respects config["prompt"]["price_format"] so no explicit set needed.
    system_prompt = v4_module.build_system_prompt(config)
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
            "raw_response_snippet": text[:400],
        }, cost, text

    no_trade_reason = data.get("no_trade_reason", None)
    # Schema-violation heuristic: reason outside R1-R8 allow-list
    V4_ALLOW_LIST = {
        "c1_failed", "c2_m15_opposing", "c3_direction_mismatch",
        "no_qualifying_h1_poi", "self_check_failed", "wrong_side_sl",
        "degenerate_trade_parameters", "ai_output_malformed",
    }
    schema_violation = (
        no_trade_reason is not None
        and no_trade_reason not in V4_ALLOW_LIST
    )

    report = {
        "candle_time": candle_time,
        "kill_zone": kill_zone,
        "decision": data.get("decision", "PARSE_ERROR"),
        "daily_bias_direction": data.get("reasoning", {}).get("daily_bias", {}).get("direction", "?"),
        "daily_bias_confidence": data.get("reasoning", {}).get("daily_bias", {}).get("confidence", "?"),
        "setup_grade": data.get("reasoning", {}).get("setup_grade", "?"),
        "no_trade_reason": no_trade_reason,
        "no_trade_reason_schema_violation": schema_violation,
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
    v4_module,
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

    logger.info("=" * 60)
    logger.info("Candle %d: %s (%s)", idx, candle_time, kill_zone)
    logger.info("V3 typical (DP1): %s %s (%s)",
                target["v3_typical_decision"],
                target["v3_typical_direction"],
                target.get("v3_typical_reason"))

    try:
        mso = build_mso_for_candle(all_candles, candle_time, target_date, config)
    except Exception as e:
        logger.error("MSO build FAILED for %s: %s", candle_time, e)
        target["mso_build_error"] = str(e)
        return

    # Save MSO (should bit-match DP1's MSO — validate)
    mso_path = OUT_DIR / f"v4_mso_{idx}_{ts_slug}.json"
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

    replay_path = OUT_DIR / f"v4_replays_{idx}_{ts_slug}.jsonl"
    reports = []
    with open(replay_path, "w") as fh:
        for run_i in range(1, RUNS_PER_CANDLE + 1):
            if total_cost_ref[0] >= BUDGET_CAP_USD:
                logger.error("BUDGET CAP $%.2f reached before run %d. Halting.", BUDGET_CAP_USD, run_i)
                break
            logger.info("  Run %d/%d ...", run_i, RUNS_PER_CANDLE)
            t0 = time.time()
            try:
                report, cost, raw_text = await evaluate_once(v4_module, mso, kill_zone, config)
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
                "    decision=%s direction=%s bias=%s grade=%s ntr=%s (schema_ok=%s) conf=%s cost=$%.4f time=%.1fs  (total $%.4f)",
                report.get("decision"),
                report.get("direction"),
                report.get("daily_bias_direction"),
                report.get("setup_grade"),
                report.get("no_trade_reason"),
                not report.get("no_trade_reason_schema_violation"),
                report.get("confidence_score"),
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
    # MATCH DP1 EXACTLY — detector v2 override to mirror A2 state
    config.setdefault("market_state", {})["detector_version"] = "v2"
    config.setdefault("market", {})["symbol"] = "XAUUSD"

    # Load V4 DRAFT system-prompt builder
    v4_module = _load_v4_draft_system_prompt_builder()
    logger.info("V4 DRAFT loaded from: %s", V4_DRAFT_PATH)

    logger.info("Config: primary_model=%s primary_effort=%s detector_version=%s",
                config.get("ai", {}).get("primary_model"),
                config.get("ai", {}).get("primary_effort"),
                config.get("market_state", {}).get("detector_version"))

    all_candles = load_csv_data("XAUUSD")
    if not all_candles.get("M15"):
        logger.error("No M15 data for XAUUSD")
        sys.exit(1)

    total_cost_ref = [0.0]
    t_start = time.time()

    for target in TARGETS:
        await run_target(v4_module, target, all_candles, config, "XAUUSD", total_cost_ref)
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
        "prompt_variant": "V4_DRAFT",
        "prompt_source": str(V4_DRAFT_PATH.relative_to(PROJECT_ROOT)),
        "targets": [
            {
                "idx": t["idx"],
                "candle_time": t["candle_time"],
                "kill_zone": t["kill_zone"],
                "v3_typical_decision": t["v3_typical_decision"],
                "v3_typical_direction": t["v3_typical_direction"],
                "v3_typical_reason": t.get("v3_typical_reason"),
                "f3_actual": t.get("f3_actual"),
                "a2_actual": t.get("a2_actual"),
                "counterfactual_R": t.get("counterfactual_R"),
                "v3_typical_R": t.get("v3_typical_R"),
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
    with open(OUT_DIR / "v4_dp1_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("=" * 60)
    logger.info("DONE. total cost=$%.4f, elapsed=%.1f min", total_cost_ref[0], elapsed_min)
    logger.info("Summary: %s", OUT_DIR / "v4_dp1_summary.json")


if __name__ == "__main__":
    asyncio.run(main())
