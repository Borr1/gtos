"""Standalone verifier for the SCID as-of sealed-validation execution packet."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import build_scid_asof_sealed_validation_execution_packet_2026_05_11 as builder


VERIFICATION_RESULT = (
    builder.ROUTE_DIR
    / f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE_TAG}.json"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_if_changed(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8", newline="\n")


def git_status() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=builder.ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def path_exists(name: str) -> bool:
    return (builder.ROUTE_DIR / name).exists()


def result_artifact_absence() -> bool:
    return not any((builder.ROUTE_DIR / name).exists() for name in builder.RESULT_ARTIFACT_NAMES)


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    return (
        payload.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and payload.get("validation_safe") is False
        and payload.get("outcome_review_opened") is False
        and payload.get("live_effect") is False
    )


def generated_json_paths() -> list[Path]:
    return [
        builder.ROUTE_DIR / f"{builder.PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_PREOUTCOME_FREEZE_PACKET_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_FROZEN_ROWSET_MANIFEST_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_VARIANT_FAMILY_REGISTRY_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_BASELINE_CONTROL_REGISTRY_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_DUPLICATE_PROXY_DENOMINATOR_AUDIT_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_NOLEAK_LABEL_FAMILY_AUDIT_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_MULTIPLE_TESTING_DSR_PBO_EFFECTIVE_N_LEDGER_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_CONCENTRATION_REGIME_SESSION_SYMBOL_LEDGER_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_FAILURE_ANATOMY_LEDGER_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_FALSIFICATION_STOP_LEDGER_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_SATURATION_REDTEAM_LEDGER_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_RESULT_ARTIFACT_OMISSION_LEDGER_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_LARGE_ARTIFACT_STORAGE_AUDIT_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE_TAG}.json",
        builder.ROUTE_DIR / f"{builder.PREFIX}_OUTPUT_MANIFEST_{builder.DATE_TAG}.json",
    ]


def verify() -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []

    required_files = [
        builder.ROUTE_DIR / f"{builder.PREFIX}_CONTEXT_ANCHOR_{builder.DATE_TAG}.md",
        *generated_json_paths(),
        builder.ROUTE_DIR / f"{builder.PREFIX}_INTERPRETATION_LIMITS_{builder.DATE_TAG}.md",
        Path(__file__).resolve(),
        builder.ROUTE_DIR / "build_scid_asof_sealed_validation_execution_packet_2026_05_11.py",
        builder.ROUTE_DIR / "test_scid_asof_sealed_validation_execution_packet_2026_05_11.py",
        builder.REPAIR_PROMPT,
    ]
    for path in required_files:
        if not path.exists():
            failures.append(f"missing required file: {builder.repo_path(path)}")

    if failures:
        return {
            "schema_version": builder.SCHEMA_VERSION,
            "route_id": builder.ROUTE_ID,
            "evidence_class": builder.EVIDENCE_CLASS,
            "terminal_decision": builder.TERMINAL_DECISION,
            "ok": False,
            "can_mark_goal_complete": False,
            "failures": failures,
            "warnings": warnings,
            **builder.SAFE_FLAGS,
        }

    prerequisite = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{builder.DATE_TAG}.json")
    freeze = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_PREOUTCOME_FREEZE_PACKET_{builder.DATE_TAG}.json")
    rowset = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_FROZEN_ROWSET_MANIFEST_{builder.DATE_TAG}.json")
    variants = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_VARIANT_FAMILY_REGISTRY_{builder.DATE_TAG}.json")
    duplicate = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_DUPLICATE_PROXY_DENOMINATOR_AUDIT_{builder.DATE_TAG}.json")
    noleak = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_NOLEAK_LABEL_FAMILY_AUDIT_{builder.DATE_TAG}.json")
    mt = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_MULTIPLE_TESTING_DSR_PBO_EFFECTIVE_N_LEDGER_{builder.DATE_TAG}.json")
    large = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_LARGE_ARTIFACT_STORAGE_AUDIT_{builder.DATE_TAG}.json")
    completion = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE_TAG}.json")
    omission = load_json(builder.ROUTE_DIR / f"{builder.PREFIX}_RESULT_ARTIFACT_OMISSION_LEDGER_{builder.DATE_TAG}.json")

    checks = {
        "prerequisite_acceptance": prerequisite.get("activation_prerequisite_passed") is True,
        "freeze_before_result": freeze.get("freeze_packet_emitted_before_any_result_row") is True
        and freeze.get("result_rows_read_derived_or_written") is False,
        "missing_target_spec_terminal": freeze.get("outcome_target_definitions", {}).get("status")
        == "MISSING_SPEC",
        "exact_3014": rowset.get("candidate_input_row_count") == 3014,
        "exact_2432": rowset.get("sealed_row_count") == 2432,
        "exact_582": rowset.get("stress_row_count") == 582,
        "exact_365": rowset.get("discovery_exclusion_count") == 365,
        "exact_7_groups": rowset.get("candidate_denominator_group_count") == 7,
        "row_coverage": rowset.get("all_candidate_rows_covered_once") is True,
        "known_families_addressed": variants.get("all_known_families_addressed") is True
        and variants.get("known_family_count") == 11,
        "no_executable_families": variants.get("executable_family_count") == 0,
        "all_families_exactly_blocked": all(
            row.get("execution_status") == "NOT_EXECUTABLE_MISSING_FROZEN_OUTCOME_TARGET_SPEC"
            for row in variants.get("families", [])
        ),
        "baselines_control_only": variants.get("control_only_family_count") == 4,
        "duplicate_proxy_clean": duplicate.get("audit_pass") is True,
        "noleak_clean": noleak.get("audit_pass") is True,
        "mt_not_computable": mt.get("dsr_status") == "NOT_COMPUTABLE_NO_RESULT_ROWS_NO_FROZEN_TARGET_HORIZON",
        "large_artifact_clean": large.get("audit_pass") is True,
        "result_artifacts_absent": result_artifact_absence()
        and omission.get("result_artifacts_emitted") is False,
        "repair_prompt_present": builder.REPAIR_PROMPT.exists(),
        "completion_audit_can_complete": completion.get("can_mark_goal_complete") is True,
    }
    for name, ok in checks.items():
        if not ok:
            failures.append(name)

    for path in generated_json_paths():
        payload = load_json(path)
        if not safe_flags_closed(payload):
            failures.append(f"safe flags not closed: {builder.repo_path(path)}")

    forbidden_raw_exts = {".scid", ".parquet", ".csv", ".dly", ".bin"}
    route_files = [
        p
        for p in builder.ROUTE_DIR.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ] + [builder.REPAIR_PROMPT]
    raw_or_large = [
        builder.repo_path(path)
        for path in sorted(set(route_files))
        if path.suffix.lower() in forbidden_raw_exts or path.stat().st_size > 100_000_000
    ]
    if raw_or_large:
        failures.append(f"raw_or_large_artifacts_present: {raw_or_large}")

    status = git_status()
    scoped_status = [
        line
        for line in status
        if "scid_asof_sealed_validation_execution_packet" in line
        or "SCID_ASOF_SEALED_VALIDATION_EXECUTION_PACKET_REPAIR_PROMPT" in line
    ]
    forbidden_live_roots = ("src/", "config/", "prompts/")
    forbidden_scoped_live = []
    for line in scoped_status:
        path_part = line[3:].replace("\\", "/") if len(line) > 3 else line.replace("\\", "/")
        if path_part.startswith(forbidden_live_roots):
            forbidden_scoped_live.append(line)
    if forbidden_scoped_live:
        failures.append(f"forbidden scoped live surface changes: {forbidden_scoped_live}")

    result = {
        "schema_version": builder.SCHEMA_VERSION,
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "terminal_decision": builder.TERMINAL_DECISION,
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "warnings": warnings,
        "checks": checks,
        "dirty_state_scoped_diff": {
            "scoped_entry_count": len(scoped_status),
            "scoped_entries": scoped_status,
            "no_forbidden_live_surface_in_scoped_entries": not forbidden_scoped_live,
        },
        "result_artifacts_absent": result_artifact_absence(),
        "repair_prompt": builder.repo_path(builder.REPAIR_PROMPT),
        **builder.SAFE_FLAGS,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="print verification without writing result")
    args = parser.parse_args()
    result = verify()
    if args.check_only:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        write_json_if_changed(VERIFICATION_RESULT, result)
        print(json.dumps({"ok": result["ok"], "can_mark_goal_complete": result["can_mark_goal_complete"], "failures": result["failures"]}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
