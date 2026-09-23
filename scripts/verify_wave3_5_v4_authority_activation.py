#!/usr/bin/env python3
"""Verify Wave3.5 V4 authority activation and Wave4/Wave5 readiness."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(
    "research/operations/final_moonshot_wave3_5_v4_authority_activation_2026_06_05"
)
RESULT_PATH = ROUTE_DIR / "WAVE3_5_VERIFICATION_RESULT.json"

REQUIRED_WAVE2_CONTRACTS = (
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/"
    "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/"
    "WAVE2_FEATURE_LABEL_STORE_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/"
    "WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/"
    "WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT.json",
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/"
    "WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json",
)

REQUIRED_ROUTE_ARTIFACTS = (
    "WAVE3_5_V4_AUTHORITY_ACTIVATION_MATRIX.json",
    "WAVE3_5_SCOPE_LEDGER.json",
    "WAVE4_WAVE5_LAUNCH_PLAN.md",
    "WAVE4_WAVE5_GOAL_SESSION_STARTERS.md",
    "COMPLETION_AUDIT.md",
)


def _get(mapping: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def verify(repo: Path) -> dict[str, Any]:
    config = _read_yaml(repo / "config/agent_config.yaml")
    runtime = config.get("gtos_vnext_runtime") or {}
    market_whiteboard = config.get("market_whiteboard_v2") or {}
    historical_replay = config.get("historical_replay_digital_twin_v4") or {}
    runtime_control = config.get("runtime_control") or {}
    issues: list[str] = []

    expected_true_paths = {
        "runtime_control.enabled": (runtime_control, ("enabled",)),
        "gtos_vnext_runtime.enabled": (runtime, ("enabled",)),
        "gtos_vnext_runtime.apply_to_execution": (runtime, ("apply_to_execution",)),
        "moonshot_dynamic_execution_router_apply_to_execution": (
            runtime,
            ("moonshot_dynamic_execution_router_apply_to_execution",),
        ),
        "moonshot_exit_policy_v4_apply_to_execution": (
            runtime,
            ("moonshot_exit_policy_v4_apply_to_execution",),
        ),
        "profit_harvest_mfe_capture_v4_enabled": (
            runtime,
            ("profit_harvest_mfe_capture_v4_enabled",),
        ),
        "moonshot_dynamic_target_stop_geometry_v4_enabled": (
            runtime,
            ("moonshot_dynamic_target_stop_geometry_v4_enabled",),
        ),
        "selector_v4_enabled": (runtime, ("selector_v4_enabled",)),
        "selector_v4_apply_to_execution": (runtime, ("selector_v4_apply_to_execution",)),
        "selector_v4_live_activation_allowed": (
            runtime,
            ("selector_v4_live_activation_allowed",),
        ),
        "scheduler_v4_best_trade_allocator_enabled": (
            runtime,
            ("scheduler_v4_best_trade_allocator_enabled",),
        ),
        "scheduler_v4_best_trade_allocator_apply_to_execution": (
            runtime,
            ("scheduler_v4_best_trade_allocator_apply_to_execution",),
        ),
        "scheduler_v4_best_trade_allocator_live_activation_allowed": (
            runtime,
            ("scheduler_v4_best_trade_allocator_live_activation_allowed",),
        ),
        "probability_debate_team_engine_v4.enabled": (
            runtime,
            ("probability_debate_team_engine_v4", "enabled"),
        ),
        "probability_debate_team_engine_v4.apply_to_execution": (
            runtime,
            ("probability_debate_team_engine_v4", "apply_to_execution"),
        ),
        "execution_manager_v4_enabled": (runtime, ("execution_manager_v4_enabled",)),
        "execution_manager_v4_apply_to_execution": (
            runtime,
            ("execution_manager_v4_apply_to_execution",),
        ),
        "validation_anti_overfit_v4_enabled": (
            runtime,
            ("validation_anti_overfit_v4_enabled",),
        ),
        "validation_anti_overfit_v4_apply_to_execution": (
            runtime,
            ("validation_anti_overfit_v4_apply_to_execution",),
        ),
        "live_decision_packet_v4_enabled": (runtime, ("live_decision_packet_v4_enabled",)),
        "market_whiteboard_v2.enabled": (market_whiteboard, ("enabled",)),
        "historical_replay_digital_twin_v4.enabled": (
            historical_replay,
            ("enabled",),
        ),
    }
    for label, (mapping, path) in expected_true_paths.items():
        if _get(mapping, path) is not True:
            issues.append(f"{label}_not_true")

    expected_values = {
        "gtos_vnext_runtime.mode": (
            runtime,
            ("mode",),
            "production_replacement_vnext_moonshot",
        ),
        "probability_debate_team_engine_v4.runtime_disposition": (
            runtime,
            ("probability_debate_team_engine_v4", "runtime_disposition"),
            "active_v4_authority",
        ),
        "execution_manager_v4_production_disposition": (
            runtime,
            ("execution_manager_v4_production_disposition",),
            "active_v4_authority",
        ),
        "market_whiteboard_v2.runtime_disposition": (
            market_whiteboard,
            ("runtime_disposition",),
            "active_v4_authority",
        ),
    }
    for label, (mapping, path, expected) in expected_values.items():
        if _get(mapping, path) != expected:
            issues.append(f"{label}_not_{expected}")

    critical = _get(market_whiteboard, ("source_requirements", "critical_sources")) or []
    if "tick" in critical or "spread" in critical:
        issues.append("market_whiteboard_v2_duplicates_tick_or_spread_cost_engine_sources")

    if runtime.get("replacement_ml_apply_to_execution") is not False:
        issues.append("replacement_ml_apply_to_execution_must_wait_for_wave5_model_registry")

    for rel in REQUIRED_WAVE2_CONTRACTS:
        if not (repo / rel).exists():
            issues.append(f"missing_wave2_contract:{rel}")
    for rel in REQUIRED_ROUTE_ARTIFACTS:
        if not (repo / ROUTE_DIR / rel).exists():
            issues.append(f"missing_route_artifact:{rel}")

    active_text_paths = [
        repo / "src/components/selector_v4.py",
        repo / "src/components/probability_debate_v4.py",
        repo / "src/components/execution_manager_v4.py",
        repo / "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
        repo / "config/agent_config.yaml",
    ]
    stale_tokens = ("staged_default_off", "default-off until", "not live-deployed")
    stale_hits: list[dict[str, Any]] = []
    for path in active_text_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in stale_tokens:
            if token in text:
                stale_hits.append({"path": str(path.relative_to(repo)), "token": token})
    if stale_hits:
        issues.append("active_v4_surface_contains_stale_staging_tokens")

    return {
        "schema_version": "wave3_5_v4_authority_activation_verification_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "active_config_summary": {
            "selector_v4_apply_to_execution": runtime.get("selector_v4_apply_to_execution"),
            "scheduler_v4_best_trade_allocator_apply_to_execution": runtime.get(
                "scheduler_v4_best_trade_allocator_apply_to_execution"
            ),
            "probability_debate_apply_to_execution": _get(
                runtime,
                ("probability_debate_team_engine_v4", "apply_to_execution"),
            ),
            "execution_manager_v4_apply_to_execution": runtime.get(
                "execution_manager_v4_apply_to_execution"
            ),
            "exit_policy_v4_apply_to_execution": runtime.get(
                "moonshot_exit_policy_v4_apply_to_execution"
            ),
            "profit_harvest_mfe_capture_v4_enabled": runtime.get(
                "profit_harvest_mfe_capture_v4_enabled"
            ),
            "market_whiteboard_v2_enabled": market_whiteboard.get("enabled"),
            "historical_replay_digital_twin_v4_enabled": historical_replay.get("enabled"),
            "replacement_ml_apply_to_execution": runtime.get("replacement_ml_apply_to_execution"),
            "runtime_control_enabled": runtime_control.get("enabled"),
        },
        "stale_token_hits": stale_hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()

    repo = Path.cwd()
    result = verify(repo)
    if args.write_result:
        (repo / RESULT_PATH).parent.mkdir(parents=True, exist_ok=True)
        (repo / RESULT_PATH).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
