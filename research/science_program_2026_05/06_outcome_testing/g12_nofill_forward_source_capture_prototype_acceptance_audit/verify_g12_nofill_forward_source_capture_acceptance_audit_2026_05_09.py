#!/usr/bin/env python3
"""Verify the independent G12 source-capture acceptance audit artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_g12_nofill_forward_source_capture_acceptance_audit_2026_05_09 as builder


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
RESULT_JSON = OUT_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json"

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
    "mt5_ea/",
)
ALLOWED_DIRTY_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_prototype_acceptance_audit/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        paths.append(line[3:].replace("\\", "/"))
    return sorted(paths)


def verify_control_flags(name: str, payload: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
        failures.append({"check": "promotion_verdict", "file": name, "value": payload.get("promotion_verdict")})
    for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
        if payload.get(flag) is not False:
            failures.append({"check": "closed_required_flag", "file": name, "flag": flag, "value": payload.get(flag)})
    for flag in (
        "opens_result_scoring",
        "opens_live_wiring",
        "opens_paid_api_or_databento_route",
        "opens_registry_edit",
        "changes_live_trading_behavior",
    ):
        if payload.get(flag) is not False:
            failures.append({"check": "closed_route_flag", "file": name, "flag": flag, "value": payload.get(flag)})


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing = [name for name in builder.AUDIT_JSON + builder.AUDIT_MD if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_audit_artifacts", "missing": missing})

    parsed: dict[str, Any] = {}
    for name in builder.AUDIT_JSON:
        path = OUT_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, payload in parsed.items():
        if isinstance(payload, dict):
            verify_control_flags(name, payload, failures)

    for name in builder.AUDIT_MD:
        path = OUT_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_token", "file": name, "missing": token})
        for literal in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if literal in text:
                failures.append({"check": "forbidden_closed_flag_literal", "file": name, "literal": literal})

    decision = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_ACCEPTANCE_DECISION_LEDGER_2026-05-09.json", {})
    if decision.get("terminal_verdict") != builder.TERMINAL_VERDICT:
        failures.append({"check": "terminal_verdict", "value": decision.get("terminal_verdict")})
    if decision.get("terminal_verdict") not in builder.ALLOWED_TERMINAL_VERDICTS:
        failures.append({"check": "terminal_verdict_not_allowed", "value": decision.get("terminal_verdict")})
    if decision.get("validation_or_promotion_opened") is not False:
        failures.append({"check": "decision_validation_or_promotion_boundary"})

    schema = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_FIELD_AUDIT_2026-05-09.json", {})
    if schema.get("status") != "PASS" or schema.get("contract_field_count") != 55 or schema.get("schema_field_count") != 55:
        failures.append({"check": "schema_field_audit", "status": schema.get("status")})

    hashes = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT_2026-05-09.json", {})
    if hashes.get("content_hash_failure_count") != 0 or hashes.get("missing_manifest_path_count") != 0:
        failures.append({"check": "hash_content_or_missing_failure", "hash_status": hashes.get("status")})
    if hashes.get("text_eol_only_raw_sha_drift_count", 0) + hashes.get("raw_sha_text_portability_risk_count", 0) <= 0:
        failures.append({"check": "expected_text_hash_portability_repair_evidence_absent"})
    if hashes.get("package_self_verifier_portability_blocker") is not True:
        failures.append({"check": "expected_package_verifier_repair_blocker_absent"})

    no_leak = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_REDACTION_AUDIT_2026-05-09.json", {})
    if no_leak.get("status") != "PASS":
        failures.append({"check": "no_leak_audit", "status": no_leak.get("status")})

    denom = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_DUPLICATE_DENOMINATOR_AUDIT_2026-05-09.json", {})
    if denom.get("status") != "PASS" or denom.get("prototype_row_count") != 298:
        failures.append({"check": "denominator_audit", "status": denom.get("status")})
    if (denom.get("row_level_accepted_denominator"), denom.get("primary_duplicate_key_denominator"), denom.get("secondary_duplicate_group_denominator")) != (225, 182, 139):
        failures.append({"check": "accepted_denominators"})

    fixture = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_PROTOTYPE_ROW_AUDIT_2026-05-09.json", {})
    if fixture.get("status") != "PASS" or fixture.get("same_tick_ambiguity_fixture_present") is not True:
        failures.append({"check": "fixture_audit", "status": fixture.get("status")})

    repair = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_BLOCKER_LEDGER_2026-05-09.json", {})
    if repair.get("repair_blocker_count", 0) < 1:
        failures.append({"check": "repair_blocker_count", "value": repair.get("repair_blocker_count")})
    blocker_ids = {item.get("blocker_id") for item in repair.get("blockers", [])}
    if "G12-SRC-CAP-REPAIR-001" not in blocker_ids:
        failures.append({"check": "expected_repair_blocker_id", "ids": sorted(blocker_ids)})

    completion = parsed.get("G12_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-09.json", {})
    if completion.get("can_mark_goal_complete_after_verification_and_commit") is not True:
        failures.append({"check": "completion_status", "value": completion.get("can_mark_goal_complete_after_verification_and_commit")})
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append({"check": "completion_weak_requirements", "value": completion.get("missing_incomplete_or_weak_requirements")})

    dirty_paths = git_status_paths()
    forbidden_live_dirty = [path for path in dirty_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    outside_allowed_dirty = [path for path in dirty_paths if not path.startswith(ALLOWED_DIRTY_PREFIXES)]
    if forbidden_live_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_live_dirty})
    if outside_allowed_dirty:
        warnings.append({"check": "outside_allowed_dirty_informational", "paths": outside_allowed_dirty})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        **builder.CONTROL_FLAGS,
        "terminal_verdict": decision.get("terminal_verdict"),
        "failures": failures,
        "warnings": warnings,
        "json_files_parsed": sorted(parsed),
        "dirty_paths_reviewed": dirty_paths,
        "future_live_logger_wiring_still_requires_owner_approval": True,
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
