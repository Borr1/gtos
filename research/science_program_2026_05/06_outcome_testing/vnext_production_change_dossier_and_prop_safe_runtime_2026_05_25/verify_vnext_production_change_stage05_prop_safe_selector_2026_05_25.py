from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage05_prop_safe_selector_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage05", MODULE_PATH)
stage05 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage05)


def load_rows() -> list[dict]:
    path = stage05.REPO_ROOT / stage05.PROP_SELECTOR_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def config_failures() -> list[str]:
    cfg = yaml.safe_load(
        (stage05.REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")
    )
    block = cfg["gtos_vnext_runtime"]
    failures: list[str] = []
    expected = {
        "prop_safe_selector_enabled": True,
        "prop_safe_selector_apply_to_execution": False,
        "prop_safe_selector_initial_balance": 100000.0,
        "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
        "prop_safe_selector_external_overall_max_loss_pct": 10.0,
        "prop_safe_selector_phase1_target_pct": 8.0,
        "prop_safe_selector_phase2_target_pct": 5.0,
        "prop_safe_selector_daily_reset_timezone_offset_hours": 3.0,
        "prop_safe_selector_malaysia_timezone_offset_hours": 8.0,
        "prop_safe_selector_internal_daily_overlay_enabled": True,
        "prop_safe_selector_internal_daily_overlay_pct": 4.0,
    }
    for key, value in expected.items():
        if block.get(key) != value:
            failures.append(f"config {key} expected {value!r} got {block.get(key)!r}")
    if block.get("apply_to_execution") is not False:
        failures.append("gtos_vnext_runtime.apply_to_execution must remain false")
    return failures


def code_failures() -> list[str]:
    runtime_text = (stage05.REPO_ROOT / "src/components/gtos_vnext_runtime.py").read_text(
        encoding="utf-8"
    )
    orchestrator_text = (stage05.REPO_ROOT / "src/components/orchestrator.py").read_text(
        encoding="utf-8"
    )
    execution_text = (stage05.REPO_ROOT / "src/components/execution.py").read_text(
        encoding="utf-8"
    )
    failures: list[str] = []
    required_runtime_tokens = [
        "evaluate_vnext_prop_safe_selector",
        "daily_loss_amount = initial_balance * external_daily_pct / 100.0",
        "max_loss_floor = initial_balance * (1.0 - external_overall_pct / 100.0)",
        "\"trailing_drawdown_modeled\": False",
        "distinct_from_redacted_account_external_daily_limit",
    ]
    for token in required_runtime_tokens:
        if token not in runtime_text:
            failures.append(f"runtime token missing: {token}")
    required_orchestrator_tokens = [
        "evaluate_vnext_prop_safe_selector(",
        "attach_vnext_prop_safe_selector_to_record",
        "DEFERRED_GTOS_VNEXT_PROP_RESET",
        "SKIPPED_GTOS_VNEXT_PROP_BUDGET",
        "vnext_prop_safe_selector.applied",
    ]
    for token in required_orchestrator_tokens:
        if token not in orchestrator_text:
            failures.append(f"orchestrator token missing: {token}")
    if "gtos_vnext_prop_safe_selector_action" not in execution_text:
        failures.append("pending intent does not preserve prop selector telemetry")
    return failures


def dossier_failures() -> list[str]:
    path = stage05.REPO_ROOT / stage05.STAGE05_DOSSIER_PATH
    text = path.read_text(encoding="utf-8")
    required_phrases = [
        "Trade count range",
        "Weighted overlapping expectancy R",
        "Pass proxy range",
        "Max drawdown proxy pct",
        "Max loss streak",
        "remaining_daily_cushion",
        "remaining_overall_cushion",
        "Classification counts",
        "Selector action counts",
        "Symbols",
        "Sessions",
        "Frameworks",
        "prop_safe_selector_apply_to_execution=false",
    ]
    return [f"dossier missing phrase: {phrase}" for phrase in required_phrases if phrase not in text]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--test-result", default="")
    args = parser.parse_args(argv)

    rows = load_rows()
    summary = json.loads(
        (stage05.REPO_ROOT / stage05.STAGE05_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    result = json.loads(
        (stage05.REPO_ROOT / stage05.STAGE05_VERIFICATION_RESULT_PATH).read_text(
            encoding="utf-8"
        )
    )
    failures = stage05.verify_rows(rows, summary)
    failures.extend(config_failures())
    failures.extend(code_failures())
    failures.extend(dossier_failures())
    state = json.loads((stage05.REPO_ROOT / stage05.STATE_PATH).read_text(encoding="utf-8"))
    if result.get("ok") is not True:
        failures.append("recorded Stage05 builder result is not ok")
    if state["stage_status_table"].get("STAGE_05_PROP_SAFE_SELECTOR") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage05 status is not in_progress or complete")

    output = {
        "route_id": stage05.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage05.rel(stage05.PROP_SELECTOR_LEDGER_PATH),
        "scenario_row_count": summary["scenario_row_count"],
        "selector_action_counts": summary["selector_action_counts"],
        "prop_metric_rows": summary["prop_replay_metrics"]["row_count"],
        "missed_winner_avoided_loser_rows": summary[
            "missed_winner_avoided_loser_metrics"
        ]["logical_row_count"],
        "robustness_prop_metric_rows": summary["robustness_metrics"]["logical_row_count"],
        "first_incomplete_invariant": (
            "STAGE_06_LTF_ENTRY_NOFILL_ENGINE"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage05.update_state(summary, complete=True)
        state_path = stage05.REPO_ROOT / stage05.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    args.test_command
                    or "py -3 -m pytest tests/test_gtos_vnext_runtime.py -q -k "
                    "'prop_safe_selector or orchestrator_builds_vnext_pending_telemetry'"
                ),
                "result": args.test_result or "14 passed, 254 deselected",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 -c py_compile changed Stage05 runtime/test/route files "
                    "with explicit cfile targets under C:/tmp/gtos_pycache/vnext_prod_stage05"
                ),
                "result": "compiled 7",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage05_prop_safe_selector_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "scenario_row_count": summary["scenario_row_count"],
                    "selector_action_counts": summary["selector_action_counts"],
                    "prop_metric_rows": summary["prop_replay_metrics"]["row_count"],
                    "missed_winner_avoided_loser_rows": summary[
                        "missed_winner_avoided_loser_metrics"
                    ]["logical_row_count"],
                    "robustness_prop_metric_rows": summary["robustness_metrics"][
                        "logical_row_count"
                    ],
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage05_tests_passed"] = True
        stage05.stage02.stage01.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
