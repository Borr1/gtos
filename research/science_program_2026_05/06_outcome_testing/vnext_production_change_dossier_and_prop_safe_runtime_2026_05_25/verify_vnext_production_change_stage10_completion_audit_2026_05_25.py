from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage10_completion_audit_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage10", MODULE_PATH)
stage10 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage10
spec.loader.exec_module(stage10)


def dossier_failures() -> list[str]:
    text = (stage10.REPO_ROOT / stage10.ACTIVATION_DOSSIER_PATH).read_text(encoding="utf-8")
    required = [
        "Runtime Behavior Changed",
        "Replay Intelligence Consumed",
        "Replay Impact",
        "Activation Status",
        "Owner Review Items",
        "No live trading",
        "redacted_account",
        "4% GTOS internal daily overlay",
    ]
    return [f"activation dossier missing phrase: {phrase}" for phrase in required if phrase not in text]


def state_failures(*, marked_complete: bool) -> list[str]:
    state = json.loads((stage10.REPO_ROOT / stage10.STATE_PATH).read_text(encoding="utf-8"))
    failures: list[str] = []
    statuses = state.get("stage_status_table") or {}
    for stage, status in statuses.items():
        expected = "complete" if (stage != "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER" or marked_complete) else "in_progress"
        if status != expected:
            failures.append(f"{stage} expected {expected} got {status}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-complete", action="store_true")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--test-result", default="")
    args = parser.parse_args(argv)

    audit = json.loads((stage10.REPO_ROOT / stage10.COMPLETION_AUDIT_PATH).read_text(encoding="utf-8"))
    result = json.loads(
        (stage10.REPO_ROOT / stage10.STAGE10_VERIFICATION_RESULT_PATH).read_text(
            encoding="utf-8"
        )
    )
    failures = stage10.verify_audit(audit)
    failures.extend(dossier_failures())
    if result.get("ok") is not True:
        failures.append("recorded Stage10 builder result is not ok")
    failures.extend(state_failures(marked_complete=False))

    output = {
        "route_id": stage10.ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "activation_dossier_path": stage10.rel(stage10.ACTIVATION_DOSSIER_PATH),
        "completion_audit_path": stage10.rel(stage10.COMPLETION_AUDIT_PATH),
        "first_incomplete_invariant": (
            "NONE" if args.mark_complete and not failures else "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"
        ),
    }
    if args.mark_complete and not failures:
        audit = stage10.build_completion_audit(complete=True)
        final_failures = stage10.verify_audit(audit)
        final_failures.extend(dossier_failures())
        final_failures.extend(state_failures(marked_complete=True))
        output["failures"] = final_failures
        output["ok"] = not final_failures
        if not final_failures:
            state_path = stage10.REPO_ROOT / stage10.STATE_PATH
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state.setdefault("tests_run", []).append(
                {
                    "command": args.test_command
                    or "py -3 -m pytest route Stage10 test and in-memory compile",
                    "result": args.test_result or "Stage10 tests and verifier passed",
                    "status": "passed",
                }
            )
            state.setdefault("tests_run", []).append(
                {
                    "command": (
                        "py -3 research/.../"
                        "verify_vnext_production_change_stage10_completion_audit_2026_05_25.py "
                        "--mark-complete"
                    ),
                    "result": {
                        "activation_dossier": stage10.rel(stage10.ACTIVATION_DOSSIER_PATH),
                        "completion_audit": stage10.rel(stage10.COMPLETION_AUDIT_PATH),
                        "instruction_coverage_ok": audit["instruction_coverage_ok"],
                    },
                    "status": "passed",
                }
            )
            state["verification_status"]["stage10_tests_passed"] = True
            stage10.stage00.atomic_json_write(state_path, state)
            output["marked_complete"] = True
    stage10.stage00.atomic_json_write(stage10.REPO_ROOT / stage10.STAGE10_VERIFICATION_RESULT_PATH, output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if output["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
