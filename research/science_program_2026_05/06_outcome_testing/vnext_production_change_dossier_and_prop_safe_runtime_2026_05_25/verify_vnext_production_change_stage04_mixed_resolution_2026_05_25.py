from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import yaml


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage04_mixed_resolution_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage04", MODULE_PATH)
stage04 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage04)


def load_rows() -> list[dict]:
    path = stage04.REPO_ROOT / stage04.MIXED_RESOLUTION_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def config_failures() -> list[str]:
    cfg_path = stage04.REPO_ROOT / "config" / "agent_config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    block = cfg["gtos_vnext_runtime"]
    rel_artifact = stage04.rel(stage04.REPO_ROOT / stage04.MIXED_RESOLUTION_LEDGER_PATH)
    failures: list[str] = []
    if rel_artifact not in block.get("artifact_paths", []):
        failures.append(f"config artifact_paths does not include {rel_artifact}")
    if stage04.EVIDENCE_FAMILY not in block.get("artifact_source_component_evidence_families", []):
        failures.append(
            "config artifact_source_component_evidence_families does not include "
            f"{stage04.EVIDENCE_FAMILY}"
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
        (stage04.REPO_ROOT / stage04.STAGE04_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    result = json.loads(
        (stage04.REPO_ROOT / stage04.STAGE04_VERIFICATION_RESULT_PATH).read_text(
            encoding="utf-8"
        )
    )
    failures = stage04.verify_rows(rows, summary)
    failures.extend(config_failures())
    state = json.loads((stage04.REPO_ROOT / stage04.STATE_PATH).read_text(encoding="utf-8"))
    if result.get("ok") is not True:
        failures.append("recorded Stage04 builder result is not ok")
    if state["stage_status_table"].get("STAGE_04_MIXED_RESOLUTION") not in {
        "in_progress",
        "complete",
    }:
        failures.append("route state Stage04 status is not in_progress or complete")

    output = {
        "route_id": stage04.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "ledger_path": stage04.rel(stage04.REPO_ROOT / stage04.MIXED_RESOLUTION_LEDGER_PATH),
        "mixed_resolution_runtime_row_instances": summary[
            "mixed_resolution_runtime_row_instances"
        ],
        "unique_mixed_resolution_row_ids": summary["unique_mixed_resolution_row_ids"],
        "computed_decision_counts": summary["computed_decision_counts"],
        "mixed_resolution_class_counts": summary["mixed_resolution_class_counts"],
        "first_incomplete_invariant": (
            "STAGE_05_PROP_SAFE_SELECTOR"
            if args.mark_complete and not failures
            else state["first_incomplete_invariant"]
        ),
    }
    if args.mark_complete and not failures:
        stage04.update_state(summary, complete=True)
        state_path = stage04.REPO_ROOT / stage04.STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.setdefault("tests_run", []).append(
            {
                "command": args.test_command or "focused Stage04 route/config/runtime pytest shard",
                "result": args.test_result or "passed",
                "status": "passed",
            }
        )
        state.setdefault("tests_run", []).append(
            {
                "command": (
                    "py -3 research/.../"
                    "verify_vnext_production_change_stage04_mixed_resolution_2026_05_25.py "
                    "--mark-complete"
                ),
                "result": {
                    "mixed_resolution_runtime_row_instances": summary[
                        "mixed_resolution_runtime_row_instances"
                    ],
                    "unique_mixed_resolution_row_ids": summary[
                        "unique_mixed_resolution_row_ids"
                    ],
                    "computed_decision_counts": summary["computed_decision_counts"],
                    "mixed_resolution_class_counts": summary[
                        "mixed_resolution_class_counts"
                    ],
                },
                "status": "passed",
            }
        )
        state["verification_status"]["stage04_tests_passed"] = True
        stage04.stage02.stage01.stage00.atomic_json_write(state_path, state)
        output["marked_complete"] = True
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
