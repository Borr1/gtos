#!/usr/bin/env python3
"""Verify Wave3 profit-harvest/MFE-capture V4 artifacts and code behavior."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_ROUTE_DIR = Path("research/operations/wave3_profit_harvest_mfe_capture_v4_2026_06_04")
WAVE2_DIR = Path("research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04")
FORBIDDEN_ARTIFACT_MARKERS = [
    '"broker_runtime_change_status": true',
    '"live_deployment_status": "deployed"',
    '"remote_push_status": true',
    '"paid_api_call_status": true',
    '"credential_mutation_status": true',
    '"broker_mutation_status": true',
]
REQUIRED_SEMANTIC_OWNERS = {
    "same_symbol_same_instrument_lifecycle_v4",
    "partial_be_trailing_stale_thesis_exit_policy_v4",
    "probability_debate_team_engine_v4",
    "follow_avoid_mixed_numeric_confluence_v4",
    "wave4_wave5_ml_feature_label_store_contract",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no} JSONL parse failed: {exc}") from exc
            if not isinstance(row, dict):
                raise AssertionError(f"{path}:{line_no} JSONL row is not an object")
            rows.append(row)
    return rows


def run_py_compile(paths: list[str]) -> dict[str, Any]:
    cmd = ["python3", "-m", "py_compile", *paths]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "status": "passed" if proc.returncode == 0 else "failed",
    }


def run_pytest_probe() -> dict[str, Any]:
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/test_dynamic_execution_policy.py",
        "tests/test_limit_order_flow.py",
        "-k",
        "profit_harvest_v4 or required_manifest_contains_moonshot_policy_families",
        "--basetemp=/tmp/gtos_wave3_profit_harvest_pytest",
        "-q",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode == 0:
        status = "passed"
        friction = None
    elif "No module named pytest" in proc.stderr:
        if shutil.which("uv"):
            uv_cmd = [
                "uv",
                "run",
                "--no-project",
                "--with",
                "pytest",
                "--with",
                "pyyaml",
                "--with",
                "pydantic",
                "python",
                "-m",
                "pytest",
                "tests/test_dynamic_execution_policy.py",
                "tests/test_limit_order_flow.py",
                "-k",
                "profit_harvest_v4 or required_manifest_contains_moonshot_policy_families",
                "--basetemp=/tmp/gtos_wave3_profit_harvest_pytest",
                "-q",
            ]
            uv_proc = subprocess.run(uv_cmd, text=True, capture_output=True, check=False)
            return {
                "command": " ".join(uv_cmd),
                "direct_python_command": " ".join(cmd),
                "direct_python_returncode": proc.returncode,
                "direct_python_stdout": proc.stdout,
                "direct_python_stderr": proc.stderr,
                "returncode": uv_proc.returncode,
                "stdout": uv_proc.stdout,
                "stderr": uv_proc.stderr,
                "status": "passed_via_uv_pytest" if uv_proc.returncode == 0 else "failed",
                "environment_friction": None if uv_proc.returncode == 0 else "uv_pytest_failed_after_direct_pytest_missing",
            }
        status = "environment_friction_pytest_missing"
        friction = "python3 interpreter has no pytest module installed"
    else:
        status = "failed"
        friction = None
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "status": status,
        "environment_friction": friction,
    }


def run_functional_checks() -> dict[str, Any]:
    from src.components import execution as execution_module
    from src.mt5.mt5_mock import MockMT5
    from src.research.dynamic_execution_policy import (
        PathObservation,
        profit_harvest_mfe_capture_v4_policy,
        simulate_policy,
    )

    replay = simulate_policy(
        profit_harvest_mfe_capture_v4_policy(
            min_mfe_r=0.25,
            micro_partial_trigger_r=0.9,
            micro_partial_close_ratio=0.0,
            trail_gap_r=1.0,
            giveback_close_r=0.5,
            final_target_r=2.0,
        ),
        [
            PathObservation(
                index=1,
                high_r=0.75,
                low_r=0.20,
                close_r=0.25,
                time_utc="2026-06-04T00:01:00Z",
            )
        ],
    )
    assert replay.exit_reason == "giveback_close"
    assert replay.final_r == 0.25

    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    execution_module.record_slippage = lambda *args, **kwargs: None
    execution_module.record_close_slippage = lambda *args, **kwargs: None
    config = {
        "risk": {"risk_per_trade_pct": 1.0},
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_partial_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
            "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
            "profit_harvest_mfe_capture_v4_enabled": True,
            "profit_harvest_mfe_capture_v4_min_mfe_r": 0.25,
            "profit_harvest_mfe_capture_v4_trail_gap_r": 0.35,
            "profit_harvest_mfe_capture_v4_protect_floor_r": 0.0,
            "profit_harvest_mfe_capture_v4_close_on_giveback_r": 0.50,
            "profit_harvest_mfe_capture_v4_stale_minutes": 360,
            "profit_harvest_mfe_capture_v4_stale_min_mfe_r": 0.25,
            "profit_harvest_mfe_capture_v4_stale_close_below_r": 0.0,
        },
    }
    engine = execution_module.ExecutionEngine(mt5, config)
    state = engine.open_trade(
        {
            "direction": "LONG",
            "stop_loss": 2640.0,
            "take_profit_1": 2665.0,
            "gtos_vnext_execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
            "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
            "gtos_vnext_dynamic_policy_applied": True,
            "gtos_vnext_dynamic_be_trigger_r": 1.0,
            "gtos_vnext_dynamic_final_target_r": 3.0,
            "gtos_vnext_dynamic_partial_close_ratio": 0.5,
        },
        account_balance=100000.0,
    )
    assert state is not None
    mt5.set_tick(
        bid=state.entry_price + 0.60 * state.sl_distance,
        ask=state.entry_price + 0.60 * state.sl_distance + 0.18,
    )
    action = engine.check_and_manage_trade({})
    assert action == "vnext_profit_harvest_mfe_capture_v4_sl_modified"
    assert engine.active_trade is not None
    assert engine.active_trade.sl_at_breakeven is True

    return {
        "status": "passed",
        "checks": [
            "source_bound_replay_giveback_close",
            "execution_overlay_subtrigger_sl_protect",
        ],
    }


def verify_artifacts(route_dir: Path) -> dict[str, Any]:
    if not route_dir.is_dir():
        raise AssertionError(f"route_dir missing: {route_dir}")

    json_files = sorted(route_dir.glob("*.json"))
    jsonl_files = sorted(route_dir.glob("*.jsonl"))
    md_files = sorted(route_dir.glob("*.md"))
    for path in json_files:
        read_json(path)
    jsonl_row_counts = {path.name: len(read_jsonl(path)) for path in jsonl_files}

    upstream_filled = read_jsonl(WAVE2_DIR / "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl")
    upstream_loser_mfe = read_jsonl(WAVE2_DIR / "WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl")
    source_rows = read_jsonl(route_dir / "WAVE3_PROFIT_HARVEST_FILLED_TRADE_SOURCE_COVERAGE.jsonl")
    fixture_rows = read_jsonl(route_dir / "WAVE3_PROFIT_HARVEST_LOSER_MFE_FIXTURES.jsonl")
    semantic_rows = read_jsonl(route_dir / "WAVE3_SEMANTIC_OWNERSHIP_HANDOFF_LEDGER.jsonl")
    instruction = read_json(route_dir / "WAVE3_INSTRUCTION_COVERAGE_CHECKLIST.json")
    contract = read_json(route_dir / "WAVE3_PROFIT_HARVEST_MFE_TRIGGER_CONTRACT.json")

    errors: list[str] = []
    if len(source_rows) != len(upstream_filled):
        errors.append(f"source coverage rows {len(source_rows)} != upstream {len(upstream_filled)}")
    if len(fixture_rows) != len(upstream_loser_mfe):
        errors.append(f"fixture rows {len(fixture_rows)} != upstream {len(upstream_loser_mfe)}")
    if len(fixture_rows) != 29:
        errors.append(f"fixture row count expected 29 got {len(fixture_rows)}")

    for row in fixture_rows:
        if row.get("result_use_status") != "source_bound_path_fixture_not_counterfactual_pnl":
            errors.append(f"fixture {row.get('row_id')} has bad result_use_status")
        if row.get("broker_runtime_change_status") is not False:
            errors.append(f"fixture {row.get('row_id')} has broker_runtime_change_status not false")
        if not row.get("v4_actions_supported"):
            errors.append(f"fixture {row.get('row_id')} lacks v4_actions_supported")

    owners = {row.get("owner_lane") for row in semantic_rows}
    missing_owners = REQUIRED_SEMANTIC_OWNERS - owners
    if missing_owners:
        errors.append(f"missing semantic owners: {sorted(missing_owners)}")

    required_instruction = {
        "goal_session_research_discipline_read_after_preflight": True,
        "research_operating_doctrine_read_after_preflight": True,
        "no_arbitrary_top_n": True,
        "forbidden_surfaces_untouched": True,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
    }
    for key, expected in required_instruction.items():
        if instruction.get(key) is not expected:
            errors.append(f"instruction {key} expected {expected!r} got {instruction.get(key)!r}")

    if contract.get("runtime_boundary", {}).get("broker_runtime_change_status") is not False:
        errors.append("contract broker_runtime_change_status is not false")
    if contract.get("production_overlay", {}).get("default_disposition") != "staged_default_off":
        errors.append("contract production overlay is not staged_default_off")

    artifact_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in [*json_files, *jsonl_files, *md_files]
    ).lower()
    for marker in FORBIDDEN_ARTIFACT_MARKERS:
        if marker in artifact_text:
            errors.append(f"forbidden artifact marker present: {marker}")

    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "json_files": [path.name for path in json_files],
        "jsonl_files": [path.name for path in jsonl_files],
        "jsonl_row_counts": jsonl_row_counts,
        "fixture_row_count": len(fixture_rows),
        "source_coverage_row_count": len(source_rows),
        "semantic_owner_count": len(owners),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route_dir", nargs="?", default=str(DEFAULT_ROUTE_DIR))
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()

    route_dir = Path(args.route_dir)
    artifact_result = verify_artifacts(route_dir)
    compile_result = run_py_compile(
        [
            "src/components/execution.py",
            "src/research/dynamic_execution_policy.py",
            "scripts/build_wave3_profit_harvest_mfe_capture_v4.py",
            "scripts/verify_wave3_profit_harvest_mfe_capture_v4.py",
        ]
    )
    functional_result = run_functional_checks()
    pytest_result = run_pytest_probe()
    ok = (
        artifact_result["status"] == "passed"
        and compile_result["status"] == "passed"
        and functional_result["status"] == "passed"
        and pytest_result["status"] in {"passed", "passed_via_uv_pytest"}
    )
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "route_dir": str(route_dir),
        "status": "passed" if ok else "failed",
        "artifact_result": artifact_result,
        "py_compile_result": compile_result,
        "functional_result": functional_result,
        "pytest_result": pytest_result,
        "environment_friction_status": pytest_result["status"],
        "broker_runtime_change_status": False,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
    }
    if args.write_result:
        out = route_dir / "WAVE3_VERIFICATION_RESULT.json"
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
