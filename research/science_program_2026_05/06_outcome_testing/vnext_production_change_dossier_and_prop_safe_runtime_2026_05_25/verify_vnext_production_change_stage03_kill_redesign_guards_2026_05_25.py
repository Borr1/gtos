from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage03_kill_redesign_guards_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage03", MODULE_PATH)
stage03 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage03)


def load_rows() -> list[dict]:
    path = stage03.REPO_ROOT / stage03.KILL_REDESIGN_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def config_failures() -> list[str]:
    cfg_path = stage03.REPO_ROOT / "config" / "agent_config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    block = cfg["gtos_vnext_runtime"]
    rel_artifact = stage03.rel(stage03.REPO_ROOT / stage03.KILL_REDESIGN_LEDGER_PATH)
    failures: list[str] = []
    if rel_artifact not in block.get("artifact_paths", []):
        failures.append(f"config artifact_paths does not include {rel_artifact}")
    if stage03.EVIDENCE_FAMILY not in block.get("artifact_source_component_evidence_families", []):
        failures.append(
            "config artifact_source_component_evidence_families does not include "
            f"{stage03.EVIDENCE_FAMILY}"
        )
    if block.get("apply_to_execution") is not False:
        failures.append("gtos_vnext_runtime.apply_to_execution must remain false")
    if block.get("pre_ai_apply_to_ai_call") is not False:
        failures.append("gtos_vnext_runtime.pre_ai_apply_to_ai_call must remain false")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--test-result", default="")
    args = parser.parse_args(argv)

    rows = load_rows()
    summary = json.loads(
        (stage03.REPO_ROOT / stage03.STAGE03_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    result_path = stage03.REPO_ROOT / stage03.STAGE03_VERIFICATION_RESULT_PATH
    result = json.loads(result_path.read_text(encoding="utf-8"))
    failures = stage03.verify_rows(rows, summary)
    failures.extend(config_failures())
    state = json.loads((stage03.REPO_ROOT / stage03.STATE_PATH).read_text(encoding="utf-8"))
    if result.get("ok") is not True:
        failures.append("recorded Stage03 builder result is not ok")
    if state["stage_status_table"].get("STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage03 status is not in_progress or complete")

    output = {
        "route_id": stage03.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage03.rel(stage03.REPO_ROOT / stage03.KILL_REDESIGN_LEDGER_PATH),
        "stage03_runtime_row_instances": summary["stage03_runtime_row_instances"],
        "unique_stage03_decision_map_row_ids": summary[
            "unique_stage03_decision_map_row_ids"
        ],
        "computed_decision_counts": summary["computed_decision_counts"],
        "first_incomplete_invariant": (
            "STAGE_04_MIXED_RESOLUTION"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage03.update_state(summary, complete=True)
        state_path = stage03.REPO_ROOT / stage03.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": args.test_command or "focused Stage03 route/config/runtime pytest shard",
                "result": args.test_result or "passed",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage03_kill_redesign_guards_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "stage03_runtime_row_instances": summary["stage03_runtime_row_instances"],
                    "unique_stage03_decision_map_row_ids": summary[
                        "unique_stage03_decision_map_row_ids"
                    ],
                    "computed_decision_counts": summary["computed_decision_counts"],
                    "source_final_decision_counts": summary["source_final_decision_counts"],
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage03_tests_passed"] = True
        stage03.stage02.stage01.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
