#!/usr/bin/env python3
"""Verify the independent G12 NOFILL historical partition/source-binding audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import build_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10 as builder


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

    decision = parsed.get(builder.JSON_ARTIFACTS[1], {})
    if decision.get("terminal_decision") != builder.ACCEPT_TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    if decision.get("exact_repair_source_blocker_count") != 0:
        failures.append({"check": "decision_blockers", "value": decision.get("exact_repair_source_blockers")})

    universe = parsed.get(builder.JSON_ARTIFACTS[2], {})
    if universe.get("target_row_count") != 298:
        failures.append({"check": "cat_v3_row_count", "value": universe.get("target_row_count")})
    if universe.get("target_family_counts") != builder.EXPECTED_FAMILY_COUNTS:
        failures.append({"check": "cat_v3_family_counts", "value": universe.get("target_family_counts")})
    if universe.get("sealed_validation_current_committed_nofill_rows_recomputed") != 0:
        failures.append({"check": "zero_sealed_rows", "value": universe.get("sealed_validation_current_committed_nofill_rows_recomputed")})
    if not all(universe.get("checks", {}).values()):
        failures.append({"check": "universe_checks", "value": universe.get("checks")})

    contamination = parsed.get(builder.JSON_ARTIFACTS[3], {})
    if contamination.get("contaminated_row_count_recomputed") != 298 or contamination.get("audit_passed") is not True:
        failures.append({"check": "contamination_reaudit", "value": contamination})

    fields = parsed.get(builder.JSON_ARTIFACTS[4], {})
    if fields.get("field_count_recomputed") != 55:
        failures.append({"check": "field_count", "value": fields.get("field_count_recomputed")})
    if fields.get("runtime_future_logger_field_count_recomputed") != 20:
        failures.append({"check": "future_field_count", "value": fields.get("runtime_future_logger_field_count_recomputed")})
    if fields.get("design_terminal_status_counts_recomputed") != builder.EXPECTED_DESIGN_COUNTS:
        failures.append({"check": "design_status_counts", "value": fields.get("design_terminal_status_counts_recomputed")})
    if fields.get("binding_class_counts_recomputed") != builder.EXPECTED_BINDING_CLASS_COUNTS:
        failures.append({"check": "binding_class_counts", "value": fields.get("binding_class_counts_recomputed")})
    if fields.get("forbidden_rows_with_raw_route") != []:
        failures.append({"check": "forbidden_fields_raw_route", "value": fields.get("forbidden_rows_with_raw_route")})

    field_blockers = parsed.get(builder.JSON_ARTIFACTS[5], {})
    if field_blockers.get("future_logger_or_source_extraction_requirement_count_recomputed") != 20:
        failures.append({"check": "field_blocker_count", "value": field_blockers})
    if not all(field_blockers.get("checks", {}).values()):
        failures.append({"check": "field_blocker_checks", "value": field_blockers.get("checks")})

    duplicate = parsed.get(builder.JSON_ARTIFACTS[6], {})
    if duplicate.get("primary_duplicate_key_unique_count_recomputed") != 182:
        failures.append({"check": "duplicate_key_count", "value": duplicate})
    if duplicate.get("secondary_duplicate_group_unique_count_recomputed") != 139:
        failures.append({"check": "duplicate_group_count", "value": duplicate})
    if not all(duplicate.get("checks", {}).values()):
        failures.append({"check": "duplicate_checks", "value": duplicate.get("checks")})

    local_search = parsed.get(builder.JSON_ARTIFACTS[7], {})
    if local_search.get("audit_passed") is not True:
        failures.append({"check": "local_heavy_reaudit", "value": local_search})
    if local_search.get("nofill_forward_source_capture_log_hits_rechecked") != []:
        failures.append({"check": "nofill_log_absence", "value": local_search.get("nofill_forward_source_capture_log_hits_rechecked")})

    boundary = parsed.get(builder.JSON_ARTIFACTS[8], {})
    if boundary.get("opened_forbidden_surfaces") != [] or boundary.get("forbidden_live_surface_dirty_paths") != []:
        failures.append({"check": "forbidden_boundary", "value": boundary})

    rerun = parsed.get(builder.JSON_ARTIFACTS[9], {})
    if not all(rerun.get("checks", {}).values()):
        failures.append({"check": "target_rerun", "value": rerun.get("checks")})

    saturation = parsed.get(builder.JSON_ARTIFACTS[10], {})
    if saturation.get("question_count") != 8 or saturation.get("same_evidence_class_gaps_exposed") != []:
        failures.append({"check": "saturation", "value": saturation})
    for item in saturation.get("questions", []):
        if item.get("status") != "CLEARED":
            failures.append({"check": "saturation_item", "value": item})

    instruction = parsed.get(builder.JSON_ARTIFACTS[11], {})
    if instruction.get("all_requirements_covered") is not True:
        failures.append({"check": "instruction_coverage", "value": instruction})
    for row in instruction.get("coverage_rows", []):
        if row.get("status") != "PASS":
            failures.append({"check": "instruction_row", "value": row})

    repair = parsed.get(builder.JSON_ARTIFACTS[12], {})
    if repair.get("exact_repair_source_blocker_count") != 0 or repair.get("remaining_blockers") != []:
        failures.append({"check": "repair_blocker_ledger", "value": repair})

    completion = parsed.get(builder.JSON_ARTIFACTS[13], {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_standard", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})

    placeholder_hits = scan_placeholders()
    if placeholder_hits:
        failures.append({"check": "placeholder_scan", "hits": placeholder_hits[:50]})

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
        "cat_v3_partition_rows": universe.get("target_row_count"),
        "sealed_validation_current_committed_nofill_rows": universe.get(
            "sealed_validation_current_committed_nofill_rows_recomputed"
        ),
        "field_count": fields.get("field_count_recomputed"),
        "future_requirement_count": field_blockers.get(
            "future_logger_or_source_extraction_requirement_count_recomputed"
        ),
        "exact_repair_source_blocker_count": repair.get("exact_repair_source_blocker_count"),
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
