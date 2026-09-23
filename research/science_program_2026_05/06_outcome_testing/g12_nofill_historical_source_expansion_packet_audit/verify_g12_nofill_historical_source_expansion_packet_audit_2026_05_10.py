#!/usr/bin/env python3
"""Verify the independent G12 NOFILL source-expansion packet audit."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g12_nofill_historical_source_expansion_packet_audit_2026_05_10 as builder


OUT_DIR = builder.OUT_DIR
RESULT_PATH = OUT_DIR / builder.VERIFICATION_RESULT_NAME
BAD_FRAGMENTS = tuple(
    item.lower()
    for item in (
        "tb" + "d",
        "to" + "do",
        "un" + "known",
        "may" + "be",
        "la" + "ter",
        "not" + " " + "yet" + " " + "decided",
    )
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=builder.REPO_ROOT,
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
        item = line[3:].replace("\\", "/")
        if " -> " in item:
            item = item.split(" -> ", 1)[1]
        paths.append(item)
    return sorted(paths)


def recursive_bad_flags(value: Any, path: str = "$") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in {"validation_safe", "outcome_review_opened", "live_effect"} and item is not False:
                hits.append({"path": child, "value": item})
            if key in {
                "opens_result_scoring",
                "opens_validation",
                "opens_promotion",
                "opens_registry_edit",
                "opens_paid_api_or_databento_route",
                "opens_remote_push",
                "opens_live_restart",
                "opens_live_trading_behavior",
                "opens_mt5_order_account_history_behavior",
                "credentials_touched",
                "changes_live_trading_behavior",
            } and item is not False:
                hits.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != builder.PROMOTION_VERDICT:
                hits.append({"path": child, "value": item})
            hits.extend(recursive_bad_flags(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(recursive_bad_flags(item, f"{path}[{index}]"))
    return hits


def scan_placeholders() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    scan_paths = sorted(
        list(OUT_DIR.glob("*.json"))
        + list(OUT_DIR.glob("*.jsonl"))
        + list(OUT_DIR.glob("*.md"))
        + list(OUT_DIR.glob("*.py"))
    )
    for path in scan_paths:
        if path.name == builder.VERIFICATION_RESULT_NAME:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for fragment in BAD_FRAGMENTS:
            if fragment in text:
                hits.append({"path": builder.rel(path), "fragment": fragment})
    return hits


def verify_python_syntax() -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for path in OUT_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    return failures


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})

    parsed: dict[str, Any] = {}
    for name in builder.JSON_ARTIFACTS:
        path = OUT_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(path)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for path in OUT_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_tokens", "file": path.name, "missing": token})
        for token in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if token in text:
                failures.append({"check": "md_true_safe_flag", "file": path.name, "token": token})

    for name, payload in parsed.items():
        if isinstance(payload, dict):
            bad = recursive_bad_flags(payload, name)
            if bad:
                failures.append({"check": "safe_or_forbidden_flags", "file": name, "hits": bad})

    decision = parsed.get(f"{builder.OUTPUT_PREFIX}_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") not in {builder.ACCEPT_TERMINAL_DECISION, builder.BLOCKER_TERMINAL_DECISION}:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})

    packet = parsed.get(f"{builder.OUTPUT_PREFIX}_SOURCE_PACKET_ROW_RECOMPUTATION_AUDIT_{builder.DATE}.json", {})
    if packet.get("packet_row_count_recomputed") != 2 or packet.get("audit_passed") is not True:
        failures.append({"check": "packet_recomputation", "value": packet})
    observed = [(row.get("symbol"), row.get("decision_time_utc")) for row in packet.get("observed_rows", [])]
    if observed != builder.EXPECTED_PACKET_ROWS:
        failures.append({"check": "expected_packet_rows", "value": observed})

    hashes = parsed.get(f"{builder.OUTPUT_PREFIX}_SOURCE_HASH_PARSER_HASH_AUDIT_{builder.DATE}.json", {})
    if hashes.get("strict_hash_blocker_count") != decision.get("exact_repair_source_requirement_count"):
        failures.append({"check": "source_hash_parser_hash", "value": hashes})
    for exact_requirement in decision.get("exact_repair_source_requirements", []):
        if not exact_requirement.get("exact_repair_requirement") or not exact_requirement.get("path"):
            failures.append({"check": "source_hash_blocker_exactness", "value": exact_requirement})
    if hashes.get("mutable_context_drift_count", 0) < 0:
        failures.append({"check": "mutable_context_drift_count", "value": hashes.get("mutable_context_drift_count")})

    contamination = parsed.get(f"{builder.OUTPUT_PREFIX}_CONTAMINATION_PURGE_EMBARGO_AUDIT_{builder.DATE}.json", {})
    if contamination.get("audit_passed") is not True:
        failures.append({"check": "contamination_embargo", "value": contamination})

    field = parsed.get(f"{builder.OUTPUT_PREFIX}_55_FIELD_BINDING_AUDIT_{builder.DATE}.json", {})
    if field.get("runtime_field_count") != 55 or field.get("audit_passed") is not True:
        failures.append({"check": "field_55_binding", "value": field})
    if field.get("binding_class_counts") != builder.EXPECTED_BINDING_CLASS_COUNTS:
        failures.append({"check": "field_binding_class_counts", "value": field.get("binding_class_counts")})

    future20 = parsed.get(f"{builder.OUTPUT_PREFIX}_FUTURE20_EXTRACTION_FAIL_CLOSED_AUDIT_{builder.DATE}.json", {})
    if future20.get("runtime_future20_field_count") != 20 or future20.get("audit_passed") is not True:
        failures.append({"check": "future20", "value": future20})
    if future20.get("status_counts") != builder.EXPECTED_FUTURE20_STATUS_COUNTS:
        failures.append({"check": "future20_status_counts", "value": future20.get("status_counts")})

    noleak = parsed.get(f"{builder.OUTPUT_PREFIX}_FORBIDDEN_REDACTED_NOLEAK_AUDIT_{builder.DATE}.json", {})
    if noleak.get("audit_passed") is not True:
        failures.append({"check": "forbidden_noleak", "value": noleak})

    duplicate = parsed.get(f"{builder.OUTPUT_PREFIX}_DUPLICATE_DENOMINATOR_AUDIT_{builder.DATE}.json", {})
    if duplicate.get("audit_passed") is not True:
        failures.append({"check": "duplicate_denominator", "value": duplicate})
    if duplicate.get("row_level_count") != 2:
        failures.append({"check": "duplicate_row_level_count", "value": duplicate.get("row_level_count")})

    blocker_audit = parsed.get(f"{builder.OUTPUT_PREFIX}_BLOCKER_REJECT_EXACTNESS_AUDIT_{builder.DATE}.json", {})
    if blocker_audit.get("audit_passed") is not True:
        failures.append({"check": "blocker_reject_exactness", "value": blocker_audit})
    if blocker_audit.get("blocked_candidate_count") != 37 or blocker_audit.get("rejected_candidate_count") != 9:
        failures.append({"check": "blocker_reject_counts", "value": blocker_audit})

    saturation = parsed.get(f"{builder.OUTPUT_PREFIX}_SATURATION_ADVERSARIAL_ISSUE_LEDGER_{builder.DATE}.json", {})
    if saturation.get("audit_passed") is not True or saturation.get("same_evidence_class_gaps_exposed") != []:
        failures.append({"check": "saturation", "value": saturation})

    repair = parsed.get(f"{builder.OUTPUT_PREFIX}_EXACT_REPAIR_SOURCE_REQUIREMENT_LEDGER_{builder.DATE}.json", {})
    if repair.get("exact_repair_source_requirement_count") != decision.get("exact_repair_source_requirement_count"):
        failures.append({"check": "repair_source_requirement", "value": repair})
    for exact_requirement in repair.get("remaining_requirements", []):
        if not exact_requirement.get("exact_repair_requirement") or not exact_requirement.get("path"):
            failures.append({"check": "repair_source_requirement_exactness", "value": exact_requirement})

    future = parsed.get(f"{builder.OUTPUT_PREFIX}_FUTURE_ROUTE_ELIGIBILITY_LEDGER_{builder.DATE}.json", {})
    if future.get("validation_remains_closed") is not True or future.get("result_scoring_remains_closed") is not True:
        failures.append({"check": "future_route_closed_gates", "value": future})

    rerun = parsed.get(f"{builder.OUTPUT_PREFIX}_TARGET_VERIFIER_TEST_RERUN_REPORT_{builder.DATE}.json", {})
    if not all(rerun.get("checks", {}).values()):
        failures.append({"check": "target_verifier_test_rerun", "value": rerun})

    completion = parsed.get(f"{builder.OUTPUT_PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("completion_standard_satisfied") is not True or completion.get("can_mark_goal_complete") is not True:
        failures.append({"check": "completion_standard", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})

    placeholder_hits = scan_placeholders()
    if placeholder_hits:
        failures.append({"check": "placeholder_scan", "hits": placeholder_hits[:50]})

    syntax_failures = verify_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_ast_syntax", "failures": syntax_failures})

    dirty_paths = [path for path in git_status_paths() if path != builder.rel(RESULT_PATH)]
    forbidden_dirty = [
        path for path in dirty_paths if any(path.startswith(prefix) for prefix in builder.FORBIDDEN_LIVE_DIRTY_PREFIXES)
    ]
    if forbidden_dirty:
        failures.append({"check": "git_forbidden_live_surface_dirty_paths", "paths": forbidden_dirty})
    allowed_info = [path for path in dirty_paths if path.startswith("research/") or path.startswith(".context/")]
    if allowed_info:
        warnings.append({"check": "git_dirty_research_or_context_paths", "paths": allowed_info})

    result = {
        "ok": failures == [],
        "route_id": builder.ROUTE_ID,
        "target_route_id": builder.TARGET_ROUTE_ID,
        "terminal_decision": decision.get("terminal_decision"),
        "failures": failures,
        "warnings": warnings,
        "packet_row_count": packet.get("packet_row_count_recomputed"),
        "blocked_candidate_count": blocker_audit.get("blocked_candidate_count"),
        "rejected_candidate_count": blocker_audit.get("rejected_candidate_count"),
        "field_count": field.get("runtime_field_count"),
        "future20_field_count": future20.get("runtime_future20_field_count"),
        "exact_repair_source_requirement_count": repair.get("exact_repair_source_requirement_count"),
        "can_mark_goal_complete": failures == [],
        "promotion_verdict": builder.PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    output = verify()
    print(json.dumps(output, indent=2, sort_keys=True))
    raise SystemExit(0 if output["ok"] else 1)
