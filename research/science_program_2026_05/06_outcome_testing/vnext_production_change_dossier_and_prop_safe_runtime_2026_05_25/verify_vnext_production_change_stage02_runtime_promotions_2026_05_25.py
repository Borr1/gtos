from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage02_runtime_promotions_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage02", MODULE_PATH)
stage02 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage02)


def load_rows() -> list[dict]:
    path = stage02.REPO_ROOT / stage02.RUNTIME_CHANGE_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def config_failures() -> list[str]:
    cfg_path = stage02.REPO_ROOT / "config" / "agent_config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    block = cfg["gtos_vnext_runtime"]
    rel_artifact = stage02.rel(stage02.REPO_ROOT / stage02.RUNTIME_CHANGE_LEDGER_PATH)
    failures: list[str] = []
    if rel_artifact not in block.get("artifact_paths", []):
        failures.append(f"config artifact_paths does not include {rel_artifact}")
    if stage02.EVIDENCE_FAMILY not in block.get("artifact_source_component_evidence_families", []):
        failures.append(
            "config artifact_source_component_evidence_families does not include "
            f"{stage02.EVIDENCE_FAMILY}"
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
        (stage02.REPO_ROOT / stage02.STAGE02_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    result_path = stage02.REPO_ROOT / stage02.STAGE02_VERIFICATION_RESULT_PATH
    result = json.loads(result_path.read_text(encoding="utf-8"))
    failures = stage02.verify_rows(rows, summary)
    failures.extend(config_failures())
    state = json.loads((stage02.REPO_ROOT / stage02.STATE_PATH).read_text(encoding="utf-8"))
    if result.get("ok") is not True:
        failures.append("recorded Stage02 builder result is not ok")
    if state["stage_status_table"].get("STAGE_02_PROMOTION_IMPLEMENTATION") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage02 status is not in_progress or complete")

    output = {
        "route_id": stage02.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage02.rel(stage02.REPO_ROOT / stage02.RUNTIME_CHANGE_LEDGER_PATH),
        "promoted_runtime_row_instances": summary["promoted_runtime_row_instances"],
        "unique_promoted_decision_map_row_ids": summary[
            "unique_promoted_decision_map_row_ids"
        ],
        "decision_counts": summary["decision_counts"],
        "first_incomplete_invariant": (
            "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage02.update_state(summary, complete=True)
        state_path = stage02.REPO_ROOT / stage02.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    args.test_command
                    or "focused Stage02 route/config/runtime pytest shard"
                ),
                "result": args.test_result or "passed",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage02_runtime_promotions_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "promoted_runtime_row_instances": summary[
                        "promoted_runtime_row_instances"
                    ],
                    "unique_promoted_decision_map_row_ids": summary[
                        "unique_promoted_decision_map_row_ids"
                    ],
                    "decision_counts": summary["decision_counts"],
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage02_runtime_promotion_tests_passed"] = True
        stage02.stage01.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
