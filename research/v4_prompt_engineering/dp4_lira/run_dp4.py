#!/usr/bin/env python3
"""DP4 A/B test runner for V3 / LIRA / No-CoT variants.

Executes the three-stage plan in one process:
 - Step 2: dry-run each variant once per MSO on a 4-6 MSO fixture set
 - Step 3: A/B consistency — 3x per variant per MSO at temperature=0

The mini-backtest (Step 4) runs as a separate script `run_mini_backtest.py`
because it re-uses the existing T7 simulate_t7_live_period.py pipeline
but with a swapped-in primary_analyzer prompt module.

Budget guardrails:
 - $15 soft-halt after steps 2+3 combined (continue to report).
 - $25 hard-halt (exit immediately).

Usage:
    set -a && source .env && set +a
    python research/v4_prompt_engineering/dp4_lira/run_dp4.py
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
logger = logging.getLogger("dp4")

from scripts.simulate_t7_live_period import (  # noqa: E402
    build_mso_for_candle,
    load_csv_data,
)

OUT_DIR = PROJECT_ROOT / "research" / "v4_prompt_engineering" / "dp4_lira"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 4 DP1 MSOs (canonical divergent-candle set from agent A2) + 2 random MSOs
# sampled from the XAUUSD Feb slice for out-of-sample breadth.
FIXTURE_MSOS = [
    {
        "idx": 1,
        "candle_time": "2026-02-02T07:00:00Z",
        "kill_zone": "london",
        "category": "override_computed_bias_candidate_short",
        "source": "dp1",
    },
    {
        "idx": 2,
        "candle_time": "2026-02-04T13:30:00Z",
        "kill_zone": "ny",
        "category": "missing_m15_opposition_detection",
        "source": "dp1",
    },
    {
        "idx": 3,
        "candle_time": "2026-02-04T13:45:00Z",
        "kill_zone": "ny",
        "category": "detected_m15_opposition",
        "source": "dp1",
    },
    {
        "idx": 4,
        "candle_time": "2026-02-06T07:30:00Z",
        "kill_zone": "london",
        "category": "respects_h1_bearish_mso",
        "source": "dp1",
    },
    # Two additional XAUUSD candles from s3 (Feb) where A2 got CANDIDATEs
    # that filled: one win, one loss. Sampling a winning + losing day keeps
    # the A/B set from being skewed toward one outcome.
    {
        "idx": 5,
        "candle_time": "2026-01-30T08:00:00Z",
        "kill_zone": "london",
        "category": "a2_cand_long_win",
        "source": "a2_s3",
    },
    {
        "idx": 6,
        "candle_time": "2026-01-30T13:15:00Z",
        "kill_zone": "ny",
        "category": "a2_cand_long_loss",
        "source": "a2_s3",
    },
]

RUNS_PER_VARIANT_STEP3 = 3
VARIANT_NAMES = ["v3_control", "lira", "nocot"]
BUDGET_SOFT_HALT_USD = 15.0
BUDGET_HARD_HALT_USD = 25.0
PER_CALL_CEILING_USD = 0.30
INPUT_COST = 3.0 / 1_000_000
OUTPUT_COST = 15.0 / 1_000_000

# State shared across steps
STATE = {
    "total_cost": 0.0,
    "call_count": 0,
    "step2_results": [],  # dry-run
    "step3_results": [],  # consistency
    "errors": [],
}


_VARIANT_MODULE_CACHE: dict[str, object] = {}


def _import_variant(name: str):
    """Load one of our three prompt modules by VARIANT_NAME.

    Loads directly from file path so we do not need to litter the
    research/ tree with __init__.py files just for this experiment.
    """
    if name in _VARIANT_MODULE_CACHE:
        return _VARIANT_MODULE_CACHE[name]

    filename = {
        "v3_control": "prompt_v3.py",
        "lira": "prompt_lira.py",
        "nocot": "prompt_nocot.py",
    }[name]
    path = Path(__file__).parent / filename
    spec = importlib.util.spec_from_file_location(f"dp4_{name}", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.VARIANT_NAME == name, f"variant name mismatch: {mod.VARIANT_NAME} vs {name}"
    _VARIANT_MODULE_CACHE[name] = mod
    return mod


async def evaluate_once(
    mso,
    kill_zone: str,
    config: dict,
    variant_name: str,
) -> tuple[dict, float, str]:
    """Run one API call for a given variant. Returns (parsed_report, cost, raw_text)."""
    import anthropic
    from src.utils.validation import strip_json_fences

    mod = _import_variant(variant_name)

    system_prompt = mod.build_system_prompt(config)
    static_ctx = mod.build_static_context(mso)
    candle_time = getattr(mso, "timestamp_utc", "") or ""
    current_time = candle_time or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    user_msg = mod.build_user_message(
        mso, {}, current_time,
        kill_zone=kill_zone,
        additional_context="",
    )

    client = anthropic.Anthropic()
    model_id = config.get("ai", {}).get("primary_model", "claude-sonnet-4-6")
    effort = config.get("ai", {}).get("primary_effort", "max")

    t0 = time.time()
    response = client.messages.create(
        model=model_id,
        max_tokens=2000,
        temperature=0,
        output_config={"effort": effort},
        system=f"{system_prompt}\n\n## Static Context (D1/H4/Session)\n{static_ctx}",
        messages=[{"role": "user", "content": user_msg}],
    )
    elapsed = time.time() - t0

    text = response.content[0].text if response.content else ""
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = input_tokens * INPUT_COST + output_tokens * OUTPUT_COST

    cleaned = strip_json_fences(text)
    parse_ok = True
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        parse_ok = False
        data = {"_parse_error": str(e)}

    tp = data.get("trade_parameters") if isinstance(data, dict) else None
    tp = tp if isinstance(tp, dict) else {}
    report = {
        "variant": variant_name,
        "candle_time": candle_time,
        "kill_zone": kill_zone,
        "decision": data.get("decision", "PARSE_ERROR") if parse_ok else "PARSE_ERROR",
        "direction": (tp.get("direction") or data.get("direction") or ""),
        "no_trade_reason": data.get("no_trade_reason"),
        "setup_grade": (
            data.get("setup_grade")
            or (data.get("reasoning") or {}).get("setup_grade")
            or "?"
        ),
        "confidence_tier": data.get("confidence_tier"),
        "confidence_score": data.get("confidence_score"),
        "entry_price": tp.get("entry_price"),
        "stop_loss": tp.get("stop_loss"),
        "take_profit_1": tp.get("take_profit_1"),
        "poi_price_level": (
            data.get("poi_price_level")
            or (data.get("justification") or {}).get("h1_setup", {}).get("poi_price_level")
            or (data.get("reasoning") or {}).get("h1_setup", {}).get("poi_price_level")
        ),
        "parse_ok": parse_ok,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": round(cost, 5),
        "elapsed_s": round(elapsed, 1),
    }
    return report, cost, text


async def run_variant_on_candle(
    target: dict,
    all_candles: dict,
    config: dict,
    variant_name: str,
    runs: int,
    phase: str,
) -> list[dict]:
    """Run `variant_name` `runs` times against the MSO built from target."""
    candle_time = target["candle_time"]
    target_date = date.fromisoformat(candle_time[:10])
    kill_zone = target["kill_zone"]
    idx = target["idx"]

    try:
        mso = build_mso_for_candle(all_candles, candle_time, target_date, config)
    except Exception as e:  # noqa: BLE001
        msg = f"MSO build FAILED candle={candle_time} err={e}"
        logger.error(msg)
        STATE["errors"].append({"phase": phase, "candle_time": candle_time, "error": str(e)})
        return []

    variant_rows = []
    for run_i in range(1, runs + 1):
        if STATE["total_cost"] >= BUDGET_HARD_HALT_USD:
            logger.error("Hard budget $%.2f reached. Halting.", BUDGET_HARD_HALT_USD)
            return variant_rows
        logger.info(
            "  [%s] variant=%s idx=%d run=%d/%d tot_cost=$%.3f",
            phase, variant_name, idx, run_i, runs, STATE["total_cost"],
        )
        try:
            report, cost, raw = await evaluate_once(mso, kill_zone, config, variant_name)
        except Exception as e:  # noqa: BLE001
            msg = f"API error variant={variant_name} candle={candle_time}: {e}"
            logger.error(msg)
            STATE["errors"].append(
                {"phase": phase, "variant": variant_name, "candle_time": candle_time, "error": str(e)},
            )
            continue

        STATE["total_cost"] += cost
        STATE["call_count"] += 1
        report["idx"] = idx
        report["run"] = run_i
        report["phase"] = phase
        report["raw_response"] = raw
        variant_rows.append(report)

        logger.info(
            "    -> decision=%s dir=%s reason=%s grade=%s tier=%s toks(i/o)=%d/%d cost=$%.4f %.1fs",
            report["decision"], report["direction"], report.get("no_trade_reason"),
            report.get("setup_grade"), report.get("confidence_tier"),
            report["input_tokens"], report["output_tokens"],
            report["cost"], report["elapsed_s"],
        )

        if cost > PER_CALL_CEILING_USD:
            logger.error("Per-call $%.4f exceeded ceiling $%.3f — halting.", cost, PER_CALL_CEILING_USD)
            break

    return variant_rows


async def step2_dry_run(all_candles: dict, config: dict) -> None:
    """Run each variant ONCE per MSO to verify schema + basic sanity."""
    logger.info("=" * 72)
    logger.info("STEP 2 — DRY-RUN (1 call per variant per MSO = %d calls)",
                len(FIXTURE_MSOS) * len(VARIANT_NAMES))
    logger.info("=" * 72)

    for target in FIXTURE_MSOS:
        logger.info("MSO idx=%d %s (%s)", target["idx"], target["candle_time"], target["category"])
        for variant in VARIANT_NAMES:
            rows = await run_variant_on_candle(
                target, all_candles, config, variant,
                runs=1, phase="step2_dry_run",
            )
            STATE["step2_results"].extend(rows)

    # Halt-gate: any variant with >1 parse error, or obviously degenerate output?
    parse_errs = {}
    decision_counts = {}
    for r in STATE["step2_results"]:
        v = r["variant"]
        parse_errs[v] = parse_errs.get(v, 0) + (0 if r["parse_ok"] else 1)
        decision_counts.setdefault(v, {}).setdefault(r["decision"], 0)
        decision_counts[v][r["decision"]] += 1

    logger.info("Step 2 parse errors per variant: %s", parse_errs)
    logger.info("Step 2 decision tally per variant: %s", decision_counts)

    for v, n_err in parse_errs.items():
        if n_err > 1:
            logger.error("Variant %s has %d parse errors in step 2 — halting per spec.", v, n_err)
            _dump_state()
            sys.exit(2)


async def step3_consistency(all_candles: dict, config: dict) -> None:
    """Re-run each variant N times per MSO at temperature=0."""
    logger.info("=" * 72)
    logger.info("STEP 3 — A/B CONSISTENCY (%d calls per variant per MSO = %d calls)",
                RUNS_PER_VARIANT_STEP3,
                len(FIXTURE_MSOS) * len(VARIANT_NAMES) * RUNS_PER_VARIANT_STEP3)
    logger.info("=" * 72)

    if STATE["total_cost"] >= BUDGET_SOFT_HALT_USD:
        logger.warning("Soft-halt budget already reached — skipping step 3.")
        return

    for target in FIXTURE_MSOS:
        logger.info("MSO idx=%d %s", target["idx"], target["candle_time"])
        for variant in VARIANT_NAMES:
            rows = await run_variant_on_candle(
                target, all_candles, config, variant,
                runs=RUNS_PER_VARIANT_STEP3, phase="step3_consistency",
            )
            STATE["step3_results"].extend(rows)


def _dump_state() -> None:
    """Persist everything we know to disk so the report script can read it."""
    out = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "total_cost": round(STATE["total_cost"], 4),
        "call_count": STATE["call_count"],
        "variant_names": VARIANT_NAMES,
        "fixture_msos": FIXTURE_MSOS,
        "step2_results": STATE["step2_results"],
        "step3_results": STATE["step3_results"],
        "errors": STATE["errors"],
    }
    path = OUT_DIR / "dp4_ab_results.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    logger.info("Dumped state: %s  (total cost $%.4f, %d calls)",
                path, STATE["total_cost"], STATE["call_count"])


async def main() -> None:
    import yaml
    from src.utils.config import apply_instrument_overrides

    with open(PROJECT_ROOT / "config" / "agent_config.yaml") as fh:
        config = yaml.safe_load(fh)
    config = apply_instrument_overrides(config, "XAUUSD")
    # Match v2 detector (current production LIVE as v2_shadow but F2.3 lets us
    # pin it to v2 for this research run so prompt inputs match main-line MSO)
    config.setdefault("market_state", {})["detector_version"] = "v2"
    config.setdefault("market", {})["symbol"] = "XAUUSD"

    logger.info(
        "Config: primary_model=%s effort=%s detector_version=%s",
        config.get("ai", {}).get("primary_model"),
        config.get("ai", {}).get("primary_effort"),
        config.get("market_state", {}).get("detector_version"),
    )

    all_candles = load_csv_data("XAUUSD")
    if not all_candles.get("M15"):
        logger.error("No M15 data for XAUUSD — cannot run.")
        sys.exit(1)

    t_start = time.time()
    try:
        await step2_dry_run(all_candles, config)
        _dump_state()
        await step3_consistency(all_candles, config)
    finally:
        _dump_state()
        logger.info(
            "DP4 A/B complete in %.1fs  spend=$%.4f  calls=%d",
            time.time() - t_start, STATE["total_cost"], STATE["call_count"],
        )


if __name__ == "__main__":
    asyncio.run(main())
