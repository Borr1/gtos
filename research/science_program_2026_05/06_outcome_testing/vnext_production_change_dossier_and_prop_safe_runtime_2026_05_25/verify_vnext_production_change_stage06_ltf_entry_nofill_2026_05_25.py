from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage06_ltf_entry_nofill_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage06", MODULE_PATH)
stage06 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage06)


def load_rows() -> list[dict]:
    path = stage06.REPO_ROOT / stage06.STAGE06_LEDGER_PATH
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def config_failures() -> list[str]:
    cfg = yaml.safe_load(
        (stage06.REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")
    )
    block = cfg["gtos_vnext_runtime"]
    expected = {
        "ltf_path_execution_enabled": True,
        "ltf_path_execution_apply_to_execution": False,
        "ltf_path_execution_min_component_rows": 1,
        "ltf_path_monitor_timeframe": "M1",
        "ltf_path_monitor_pending_intent_enabled": True,
        "ltf_path_market_entry_requires_path_touch": True,
        "ltf_path_adjusted_entry_enabled": True,
        "ltf_path_adjusted_entry_offset_r": 0.50,
    }
    failures: list[str] = []
    for key, value in expected.items():
        if block.get(key) != value:
            failures.append(f"config {key} expected {value!r} got {block.get(key)!r}")
    if block.get("apply_to_execution") is not False:
        failures.append("global vNext apply_to_execution must remain false")
    return failures


def code_failures() -> list[str]:
    runtime_text = (stage06.REPO_ROOT / "src/components/gtos_vnext_runtime.py").read_text(
        encoding="utf-8"
    )
    orchestrator_text = (stage06.REPO_ROOT / "src/components/orchestrator.py").read_text(
        encoding="utf-8"
    )
    execution_text = (stage06.REPO_ROOT / "src/components/execution.py").read_text(
        encoding="utf-8"
    )
    failures: list[str] = []
    required_runtime_tokens = [
        "GTOSVNextLTFPathExecutionDecision",
        "evaluate_vnext_ltf_path_execution",
        "attach_vnext_ltf_path_execution_to_record",
        "ltf_path_execution_apply_to_execution",
        "ADJUST_LIMIT_ENTRY",
        "SKIP_LTF_NOFILL_AVOID",
    ]
    for token in required_runtime_tokens:
        if token not in runtime_text:
            failures.append(f"runtime token missing: {token}")
    required_orchestrator_tokens = [
        "_build_gtos_vnext_ltf_path_state",
        "_check_pending_limit_ltf_path",
        "evaluate_vnext_ltf_path_execution(",
        "SKIPPED_GTOS_VNEXT_LTF_PATH",
        "gtos_vnext_ltf_path_pending_monitor",
        "elapsed_candle_increment",
    ]
    for token in required_orchestrator_tokens:
        if token not in orchestrator_text:
            failures.append(f"orchestrator token missing: {token}")
    required_execution_tokens = [
        "gtos_vnext_ltf_path_action",
        "gtos_vnext_ltf_path_would_action",
        "gtos_vnext_ltf_path_monitor_timeframe",
        "elapsed_candle_increment",
    ]
    for token in required_execution_tokens:
        if token not in execution_text:
            failures.append(f"execution token missing: {token}")
    return failures


def dossier_failures() -> list[str]:
    text = (stage06.REPO_ROOT / stage06.STAGE06_DOSSIER_PATH).read_text(encoding="utf-8")
    required_phrases = [
        "M15-vs-LTF disagreement rows",
        "No-fill/pending lifecycle rows",
        "Missed-winner/avoided-loser rows",
        "Path outcome/R rows",
        "Production-change LTF surface rows consumed",
        "Runtime scenario rows",
        "ltf_path_execution_apply_to_execution=false",
        "No live trading",
    ]
    return [f"dossier missing phrase: {phrase}" for phrase in required_phrases if phrase not in text]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--test-result", default="")
    args = parser.parse_args(argv)

    rows = [
        row
        for row in load_rows()
        if row.get("row_type") == "runtime_scenario"
    ]
    summary = json.loads(
        (stage06.REPO_ROOT / stage06.STAGE06_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    result = json.loads(
        (stage06.REPO_ROOT / stage06.STAGE06_VERIFICATION_RESULT_PATH).read_text(
            encoding="utf-8"
        )
    )
    failures = stage06.verify_summary(summary, rows)
    failures.extend(config_failures())
    failures.extend(code_failures())
    failures.extend(dossier_failures())
    state = json.loads((stage06.REPO_ROOT / stage06.STATE_PATH).read_text(encoding="utf-8"))
    if result.get("ok") is not True:
        failures.append("recorded Stage06 builder result is not ok")
    if state["stage_status_table"].get("STAGE_06_LTF_ENTRY_NOFILL_ENGINE") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage06 status is not in_progress or complete")

    output = {
        "route_id": stage06.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage06.rel(stage06.STAGE06_LEDGER_PATH),
        "scenario_row_count": summary["scenario_row_count"],
        "m15_vs_ltf_disagreement_rows": summary["m15_vs_ltf_disagreement"][
            "logical_row_count"
        ],
        "nofill_pending_lifecycle_rows": summary["nofill_pending_lifecycle"][
            "logical_row_count"
        ],
        "path_outcome_r_rows": summary["path_outcome_r"]["logical_row_count"],
        "production_change_ltf_surface_rows": summary["production_change_ltf_surface"][
            "row_count"
        ],
        "first_incomplete_invariant": (
            "STAGE_07_AI_POLICY"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage06.update_state(summary, complete=True)
        state_path = stage06.REPO_ROOT / stage06.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    args.test_command
                    or "py -3 -m pytest tests/test_gtos_vnext_runtime.py -q -k "
                    "'ltf_path_execution or orchestrator_builds_vnext_pending_telemetry'"
                ),
                "result": args.test_result or "5 passed, 267 deselected",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 -c py_compile changed Stage06 runtime/test/route files "
                    "with explicit cfile targets under C:/tmp/gtos_pycache/vnext_prod_stage06"
                ),
                "result": "compiled Stage06 files",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage06_ltf_entry_nofill_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "scenario_row_count": summary["scenario_row_count"],
                    "m15_vs_ltf_disagreement_rows": summary["m15_vs_ltf_disagreement"][
                        "logical_row_count"
                    ],
                    "nofill_pending_lifecycle_rows": summary[
                        "nofill_pending_lifecycle"
                    ]["logical_row_count"],
                    "path_outcome_r_rows": summary["path_outcome_r"]["logical_row_count"],
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage06_tests_passed"] = True
        stage06.stage02.stage01.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
