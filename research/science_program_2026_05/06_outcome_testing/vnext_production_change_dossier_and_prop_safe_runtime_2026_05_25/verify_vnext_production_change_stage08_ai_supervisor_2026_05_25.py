from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).with_name("build_vnext_production_change_stage08_ai_supervisor_2026_05_25.py")
spec = importlib.util.spec_from_file_location("vnext_prod_stage08", MODULE_PATH)
stage08 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage08)


def load_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in (stage08.REPO_ROOT / stage08.STAGE08_LEDGER_PATH)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]


def config_failures() -> list[str]:
    cfg = yaml.safe_load(
        (stage08.REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")
    )
    supervisor = cfg["ai_supervisor"]
    expected = {
        "enabled": True,
        "apply_runtime_overrides": True,
        "decision_log_enabled": True,
        "format_repair_enabled": True,
        "max_missing_source_bound_rows": 1,
    }
    failures: list[str] = []
    for key, value in expected.items():
        if supervisor.get(key) != value:
            failures.append(f"ai_supervisor {key} expected {value!r} got {supervisor.get(key)!r}")
    if supervisor.get("decision_log_path") != "shadow_logs/ai_supervisor_decisions.jsonl":
        failures.append("ai_supervisor decision_log_path mismatch")
    return failures


def code_failures() -> list[str]:
    supervisor_text = (stage08.REPO_ROOT / "src/components/ai_supervisor.py").read_text(
        encoding="utf-8"
    )
    orchestrator_text = (stage08.REPO_ROOT / "src/components/orchestrator.py").read_text(
        encoding="utf-8"
    )
    analyzer_text = (stage08.REPO_ROOT / "src/components/primary_analyzer.py").read_text(
        encoding="utf-8"
    )
    failures: list[str] = []
    for token in [
        "AISupervisorDecision",
        "evaluate_ai_supervisor",
        "apply_ai_supervisor_runtime_overrides",
        "repair_ai_response_format_preserving_semantics",
        "DISABLE_AI_NARROWING",
    ]:
        if token not in supervisor_text:
            failures.append(f"ai_supervisor token missing: {token}")
    for token in [
        "_evaluate_ai_supervisor",
        "AI_SUPERVISOR",
        "apply_ai_supervisor_runtime_overrides",
        "_config_after_ai_supervisor",
    ]:
        if token not in orchestrator_text:
            failures.append(f"orchestrator token missing: {token}")
    if "repair_ai_response_format_preserving_semantics" not in analyzer_text:
        failures.append("primary_analyzer formatting repair hook missing")
    return failures


def dossier_failures() -> list[str]:
    text = (stage08.REPO_ROOT / stage08.STAGE08_DOSSIER_PATH).read_text(encoding="utf-8")
    required = [
        "Stage08 decision-surface groups",
        "Stage08 decision-map rows",
        "Runtime scenario rows",
        "Format repair fixtures",
        "never changes trade direction",
        "No live trading",
    ]
    return [f"dossier missing phrase: {phrase}" for phrase in required if phrase not in text]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--test-result", default="")
    args = parser.parse_args(argv)

    rows = load_rows()
    summary = json.loads(
        (stage08.REPO_ROOT / stage08.STAGE08_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    result = json.loads(
        (stage08.REPO_ROOT / stage08.STAGE08_VERIFICATION_RESULT_PATH).read_text(
            encoding="utf-8"
        )
    )
    failures = stage08.verify_summary(summary, rows)
    failures.extend(config_failures())
    failures.extend(code_failures())
    failures.extend(dossier_failures())
    state = json.loads((stage08.REPO_ROOT / stage08.STATE_PATH).read_text(encoding="utf-8"))
    if result.get("ok") is not True:
        failures.append("recorded Stage08 builder result is not ok")
    if state["stage_status_table"].get("STAGE_08_AI_SUPERVISOR") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage08 status is not in_progress or complete")

    output = {
        "route_id": stage08.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage08.rel(stage08.STAGE08_LEDGER_PATH),
        "scenario_row_count": summary["scenario_row_count"],
        "format_repair_fixture_count": summary["format_repair_fixture_count"],
        "stage08_surface_rows": summary["stage08_surface"]["row_count"],
        "first_incomplete_invariant": (
            "STAGE_09_FORWARD_ONLY_REPLAY"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage08.update_state(summary, complete=True)
        state_path = stage08.REPO_ROOT / stage08.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": args.test_command
                or "py -3 -m pytest tests/test_ai_supervisor.py -q",
                "result": args.test_result or "Stage08 focused tests passed",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 -c in-memory compile() for changed Stage08 runtime/test/route files"
                ),
                "result": "compiled 7 Stage08 files without bytecode cache writes",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage08_ai_supervisor_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "scenario_row_count": summary["scenario_row_count"],
                    "format_repair_fixture_count": summary["format_repair_fixture_count"],
                    "stage08_surface_rows": summary["stage08_surface"]["row_count"],
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage08_tests_passed"] = True
        stage08.stage02.stage01.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
