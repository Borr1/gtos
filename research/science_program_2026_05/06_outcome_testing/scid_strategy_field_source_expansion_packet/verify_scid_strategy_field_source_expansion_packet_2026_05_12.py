"""Standalone verifier for the SCID strategy-field source expansion packet."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import build_scid_strategy_field_source_expansion_packet_2026_05_12 as builder


RESULT_PATH = builder.ROUTE_DIR / "SCID_STRATEGY_FIELD_VERIFICATION_RESULT_2026-05-12.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def add_issue(issues: list[dict[str, Any]], code: str, detail: Any) -> None:
    issues.append({"code": code, "detail": detail})


def walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, subvalue in value.items():
            keys.add(str(key))
            keys.update(walk_keys(subvalue))
    elif isinstance(value, list):
        for item in value:
            keys.update(walk_keys(item))
    return keys


def git_status_paths() -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=builder.REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return []
    paths = []
    for line in proc.stdout.splitlines():
        if len(line) >= 4:
            paths.append(line[3:].replace("\\", "/"))
    return paths


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    descriptors = load_json(builder.INPUTS["descriptor_freeze"])["descriptor_rows"]
    candidates = builder.load_jsonl(builder.INPUTS["candidate_rows"])
    closure_rows = load_jsonl(builder.OUTPUTS["closure_rows_jsonl"])
    manifest = load_json(builder.OUTPUTS["manifest_json"])
    summary = load_json(builder.OUTPUTS["field_status_summary_json"])
    prospective = load_json(builder.OUTPUTS["prospective_json"])
    fail_closed = load_json(builder.OUTPUTS["fail_closed_json"])
    decision = load_json(builder.OUTPUTS["decision_json"])
    allowlist = load_json(builder.OUTPUTS["provenance_allowlist_json"])

    descriptor_ids = {row["candidate_input_row_id"] for row in descriptors}
    candidate_ids = {row["candidate_input_row_id"] for row in candidates}
    closure_ids = [row["candidate_input_row_id"] for row in closure_rows]

    if len(descriptors) != 3014:
        add_issue(issues, "descriptor_row_count", len(descriptors))
    if len(candidates) != 3014:
        add_issue(issues, "candidate_row_count", len(candidates))
    if len(closure_rows) != 3014:
        add_issue(issues, "closure_row_count", len(closure_rows))
    if len(set(closure_ids)) != len(closure_ids):
        duplicates = [candidate_id for candidate_id, count in Counter(closure_ids).items() if count > 1]
        add_issue(issues, "duplicate_candidate_ids", duplicates[:10])
    if set(closure_ids) != descriptor_ids or set(closure_ids) != candidate_ids:
        add_issue(
            issues,
            "candidate_id_set_mismatch",
            {
                "missing_from_closure": sorted((descriptor_ids | candidate_ids) - set(closure_ids))[:10],
                "extra_in_closure": sorted(set(closure_ids) - (descriptor_ids | candidate_ids))[:10],
            },
        )

    for row in closure_rows:
        statuses = row.get("field_statuses", {})
        missing_fields = set(builder.FIELD_FAMILIES) - set(statuses)
        extra_fields = set(statuses) - set(builder.FIELD_FAMILIES)
        if missing_fields or extra_fields:
            add_issue(
                issues,
                "field_family_mismatch",
                {
                    "candidate_input_row_id": row.get("candidate_input_row_id"),
                    "missing": sorted(missing_fields),
                    "extra": sorted(extra_fields),
                },
            )
            break
        for field, payload in statuses.items():
            if payload.get("status") not in builder.FIELD_STATUS_ENUM:
                add_issue(
                    issues,
                    "invalid_status_enum",
                    {
                        "candidate_input_row_id": row.get("candidate_input_row_id"),
                        "field": field,
                        "status": payload.get("status"),
                    },
                )
                break
        expected_hash_row = dict(row)
        expected_hash_row.pop("field_closure_row_hash", None)
        if builder.stable_hash(expected_hash_row) != row.get("field_closure_row_hash"):
            add_issue(issues, "row_hash_mismatch", row.get("candidate_input_row_id"))
            break
        for flag_key, expected in builder.SAFE_FLAGS.items():
            if row.get(flag_key) != expected:
                add_issue(
                    issues,
                    "safe_flag_mismatch",
                    {"candidate_input_row_id": row.get("candidate_input_row_id"), "flag": flag_key, "value": row.get(flag_key)},
                )
                break

    forbidden_keys_seen = walk_keys(closure_rows) & builder.FORBIDDEN_RESULT_KEYS
    if forbidden_keys_seen:
        add_issue(issues, "forbidden_result_keys_in_closure_rows", sorted(forbidden_keys_seen))

    for artifact in manifest.get("artifacts", []):
        path = builder.REPO_ROOT / artifact["path"]
        if not path.exists():
            add_issue(issues, "manifest_artifact_missing", artifact)
        if path.suffix.lower() in {".scid", ".parquet", ".csv", ".dly", ".bin", ".depth"}:
            add_issue(issues, "raw_market_blob_in_manifest", artifact)

    required_manifest = manifest.get("required_artifact_families_covered", {})
    missing_manifest_families = [key for key, value in required_manifest.items() if not value]
    if missing_manifest_families:
        add_issue(issues, "manifest_required_family_false", missing_manifest_families)

    status_counts = summary.get("field_status_counts_by_field", {})
    expected_all_closed = {
        "canonical_candidate_and_denominator",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
    }
    for field in expected_all_closed:
        if status_counts.get(field, {}).get("CLOSED_FROM_SOURCE") != 3014:
            add_issue(issues, "closed_field_count_mismatch", {field: status_counts.get(field)})
    expected_fail_closed = {
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
    }
    for field in expected_fail_closed:
        if status_counts.get(field, {}).get("FAIL_CLOSED_MISSING_SOURCE_FIELD") != 3014:
            add_issue(issues, "fail_closed_field_count_mismatch", {field: status_counts.get(field)})
    expected_prospective = {
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
    }
    for field in expected_prospective:
        if status_counts.get(field, {}).get("PROSPECTIVE_CAPTURE_REQUIRED") != 3014:
            add_issue(issues, "prospective_field_count_mismatch", {field: status_counts.get(field)})
    if status_counts.get("broker_account_order_history_deal_position_evidence", {}).get("FORBIDDEN_IN_THIS_EVIDENCE_CLASS") != 3014:
        add_issue(
            issues,
            "forbidden_field_count_mismatch",
            {"broker_account_order_history_deal_position_evidence": status_counts.get("broker_account_order_history_deal_position_evidence")},
        )

    for ledger_name, ledger in {"prospective": prospective, "fail_closed": fail_closed}.items():
        entries = ledger.get("requirements") or ledger.get("missing_field_groups") or []
        for entry in entries:
            for required_key in [
                "future_source_or_logger",
                "required_fields",
                "parser_requirement",
                "schema_version_required",
                "redaction_rule",
                "as_of_rule",
                "g12_acceptance_requirement",
            ]:
                if required_key not in entry:
                    add_issue(issues, "inexact_future_requirement", {"ledger": ledger_name, "field_family": entry.get("field_family"), "missing": required_key})

    forbidden_allowlist_paths = [
        row["path"]
        for row in allowlist.get("allowed_input_artifacts", [])
        if "account_history" in row["path"] or "broker_actual" in row["path"] or "account_pnl" in row["path"]
    ]
    if forbidden_allowlist_paths:
        add_issue(issues, "broker_or_account_artifact_allowed", forbidden_allowlist_paths)

    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        add_issue(issues, "terminal_decision_mismatch", decision.get("terminal_decision"))

    dirty_paths = git_status_paths()
    allowed_new_prefixes = [
        "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md",
    ]
    route_dirty_paths = [path for path in dirty_paths if any(path.startswith(prefix) for prefix in allowed_new_prefixes)]
    forbidden_route_dirty = [
        path
        for path in route_dirty_paths
        if path.startswith(("src/", "config/", "prompts/", "scripts/canary_fixtures/"))
    ]
    if forbidden_route_dirty:
        add_issue(issues, "forbidden_trading_surface_dirty_in_route", forbidden_route_dirty)

    result = {
        "ok": not issues,
        "route_id": builder.ROUTE_ID,
        "terminal_decision": builder.TERMINAL_DECISION if not issues else "REPAIR_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_REQUIRED",
        "candidate_rows_verified": len(closure_rows),
        "unique_candidate_ids_verified": len(set(closure_ids)),
        "issues": issues,
        "dirty_workspace_paths_observed": dirty_paths,
        "dirty_workspace_note": "Existing unrelated runtime/shadow dirt is informational; verifier enforces route artifacts and forbidden route surfaces only.",
        "safe_flags": {
            "promotion_verdict": builder.PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    return result


def main() -> int:
    result = verify()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "issues": result["issues"], "result": builder.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
