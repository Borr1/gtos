"""Verify G0 NOFILL forward source-capture synthesis/readiness artifacts."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10 as builder


BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parents[3]
RESULT_JSON = BASE / "G0_NOFILL_FORWARD_SOURCE_CAPTURE_SYNTHESIS_VERIFICATION_RESULT_2026-05-10.json"


def _git_changed_names() -> list[str]:
    names = set()
    for args in (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"]):
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        names.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(names)


def _load_json(path: Path, issues: list[str]) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - diagnostic branch
        issues.append(f"json_parse_failed:{path.name}:{exc}")
        return None


def _safe_flag_scan(payloads: dict[str, dict[str, Any]], issues: list[str]) -> None:
    for name, payload in payloads.items():
        if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
            issues.append(f"bad_promotion_verdict:{name}")
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if payload.get(flag) is not False:
                issues.append(f"bad_safe_flag:{name}:{flag}={payload.get(flag)!r}")
        for flag in (
            "opens_result_scoring",
            "opens_validation",
            "opens_promotion",
            "opens_registry_edit",
            "opens_paid_api_or_databento_route",
            "opens_live_trading_behavior",
            "changes_live_trading_behavior",
            "credentials_touched",
            "remote_push_opened",
        ):
            if payload.get(flag) is not False:
                issues.append(f"bad_boundary_flag:{name}:{flag}={payload.get(flag)!r}")


def _placeholder_scan(issues: list[str]) -> None:
    blocked_tokens = ("TBD", "TODO", "unknown", "maybe")
    for path in list(BASE.glob("*.json")) + list(BASE.glob("*.md")):
        if path.name == RESULT_JSON.name:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in blocked_tokens:
            if token in text:
                issues.append(f"placeholder_token:{path.name}:{token}")


def _syntax_scan(issues: list[str]) -> None:
    for path in [
        BASE / "build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
        BASE / "verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
        BASE / "test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
    ]:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            issues.append(f"syntax_parse_failed:{path.name}:{exc}")


def _runtime_log_check(issues: list[str]) -> dict[str, Any]:
    audit = builder.inspect_nofill_runtime_log()
    if audit.get("exists"):
        if audit.get("validation_issues"):
            issues.append("runtime_nofill_log_validation_issues")
        if audit.get("safe_flag_issues"):
            issues.append("runtime_nofill_log_safe_flag_issues")
        if audit.get("forbidden_leak_issues"):
            issues.append("runtime_nofill_log_forbidden_leak_issues")
    return audit


def verify() -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    required = (
        builder.REQUIRED_JSON
        + builder.REQUIRED_MD
        + [
            "build_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
            "verify_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
            "test_g0_nofill_forward_source_capture_implementation_synthesis_readiness_route_2026_05_10.py",
        ]
    )
    for name in required:
        if not (BASE / name).exists():
            issues.append(f"missing_required_artifact:{name}")

    payloads: dict[str, dict[str, Any]] = {}
    for name in builder.REQUIRED_JSON:
        path = BASE / name
        if path.exists():
            payload = _load_json(path, issues)
            if isinstance(payload, dict):
                payloads[name] = payload

    _safe_flag_scan(payloads, issues)
    _placeholder_scan(issues)
    _syntax_scan(issues)

    decision = payloads.get(
        f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_{builder.DATE}.json",
        {},
    )
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        issues.append("terminal_decision_not_accept")
    if decision.get("canonical_source_control_implementation_evidence_on_main") is not True:
        issues.append("canonical_source_control_implementation_not_reconciled_on_main")

    readiness = payloads.get(
        f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_SHADOW_READINESS_OBSERVATION_AUDIT_{builder.DATE}.json",
        {},
    )
    allowed_readiness = {
        "SOURCE_CONTROL_READY_EXPECTED_NO_ROW_OWNER_RESTART_OR_NEXT_CANDIDATE_CHECK_REQUIRED",
        "ROWS_PRESENT_SCHEMA_AUDIT_REQUIRED",
    }
    if readiness.get("shadow_readiness_state") not in allowed_readiness:
        issues.append(f"bad_shadow_readiness_state:{readiness.get('shadow_readiness_state')!r}")
    if readiness.get("broken_logger_evidence_found") is True:
        issues.append("broken_logger_evidence_found")

    blockers = payloads.get(
        f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_BLOCKER_APPROVAL_LEDGER_{builder.DATE}.json",
        {},
    )
    if blockers.get("source_control_repair_blockers") != []:
        issues.append("unexpected_source_control_repair_blockers")

    completion = payloads.get(
        f"G0_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{builder.DATE}.json",
        {},
    )
    if completion.get("completion_standard_satisfied") is not True:
        issues.append("completion_standard_not_satisfied")
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        issues.append("completion_audit_has_missing_requirements")

    g12_decision = builder.read_json(builder.CONTROL_INPUTS["g12_decision"])
    g12_blockers = builder.read_json(builder.CONTROL_INPUTS["g12_repair_blockers"])
    if g12_decision.get("terminal_decision") != "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY":
        issues.append("g12_terminal_decision_not_accepted")
    if g12_blockers.get("exact_repair_blocker_count") != 0:
        issues.append("g12_repair_blockers_not_zero")

    runtime_audit = _runtime_log_check(issues)

    dirty_names = _git_changed_names()
    allowed_prefixes = {
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    }
    route_prefix = str(BASE.relative_to(REPO_ROOT)).replace("\\", "/") + "/"
    forbidden_dirty = [
        name
        for name in dirty_names
        if not name.startswith(route_prefix) and name not in allowed_prefixes
    ]
    if forbidden_dirty:
        issues.append(f"forbidden_dirty_paths:{forbidden_dirty}")

    result = {
        "artifact": "G0_NOFILL_FORWARD_SOURCE_CAPTURE_SYNTHESIS_VERIFICATION_RESULT",
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        **builder.base_flags(),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "warnings": warnings,
        "json_files_parsed": sorted(payloads),
        "required_artifacts_checked": required,
        "dirty_paths_reviewed": dirty_names,
        "runtime_log_audit": runtime_audit,
        "g12_terminal_decision": g12_decision.get("terminal_decision"),
        "g12_exact_repair_blocker_count": g12_blockers.get("exact_repair_blocker_count"),
        "can_mark_goal_complete_after_commit": not issues,
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
