#!/usr/bin/env python3
"""Verify the G12 no-API mechanical replay source-control audit route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


DATE = "2026-05-10"
ROUTE_ID = "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT"
SCHEMA_VERSION = "g12_no_api_mechanical_replay_source_control_audit_v1"
PREFIX = "G12_NO_API_MECHANICAL_REPLAY"
ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "DECISION_LEDGER",
    "TARGET_ARTIFACT_PARSE_AUDIT",
    "SOURCE_SELECTION_HASH_AUDIT",
    "SCHEMA_DUPLICATE_ASOF_AUDIT",
    "FAMILY_REGISTRY_AUDIT",
    "CANDIDATE_INVENTORY_AUDIT",
    "DISCOVERY_PATH_LABEL_INVENTORY_AUDIT",
    "GIT_LFS_STORAGE_AUDIT",
    "EXCLUDED_SEARCH_CONTINUATION_AUDIT",
    "NOLEAK_FORBIDDEN_SURFACE_AUDIT",
    "TARGET_CODE_SOURCE_AUDIT",
    "TARGET_VERIFIER_TEST_REPORT",
    "SATURATION_SELF_REDTEAM_LEDGER",
    "REPAIR_FOLLOWUP_LEDGER",
    "DIRTY_STATE_SCOPE_AUDIT",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]

FORBIDDEN_TRUE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_mt5_order_account_history_behavior",
    "opens_remote_push",
    "opens_registry_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_path(route_dir: Path, stem: str) -> Path:
    return route_dir / f"{PREFIX}_{stem}_{DATE}.json"


def flag_failures(payload: Mapping[str, Any], label: str) -> list[str]:
    failures = []
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        failures.append(f"{label}: promotion_verdict is not NO_PROMOTION_VERDICT")
    for flag in FORBIDDEN_TRUE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{label}: {flag} is not false")
    return failures


def verify(route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for stem in REQUIRED_STEMS:
        path = json_path(route_dir, stem)
        if not path.exists():
            failures.append(f"missing artifact: {path}")
            continue
        try:
            payloads[stem] = read_json(path)
        except Exception as exc:
            failures.append(f"parse failure for {path}: {exc!r}")

    for stem, payload in payloads.items():
        failures.extend(flag_failures(payload, stem))

    if payloads.get("DECISION_LEDGER", {}).get("terminal_decision") != "ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE":
        failures.append("terminal decision is not ACCEPT_AS_NO_API_MECHANICAL_REPLAY_SOURCE_CONTROL_SUBSTRATE")

    completion = payloads.get("COMPLETION_AUDIT", {})
    if completion.get("can_mark_goal_complete") is not True:
        failures.append("completion audit does not set can_mark_goal_complete=true")
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append("completion audit reports missing/incomplete/weak requirements")

    required_pass_stems = [
        "TARGET_ARTIFACT_PARSE_AUDIT",
        "SOURCE_SELECTION_HASH_AUDIT",
        "SCHEMA_DUPLICATE_ASOF_AUDIT",
        "FAMILY_REGISTRY_AUDIT",
        "CANDIDATE_INVENTORY_AUDIT",
        "DISCOVERY_PATH_LABEL_INVENTORY_AUDIT",
        "GIT_LFS_STORAGE_AUDIT",
        "EXCLUDED_SEARCH_CONTINUATION_AUDIT",
        "NOLEAK_FORBIDDEN_SURFACE_AUDIT",
        "TARGET_CODE_SOURCE_AUDIT",
        "TARGET_VERIFIER_TEST_REPORT",
        "SATURATION_SELF_REDTEAM_LEDGER",
        "DIRTY_STATE_SCOPE_AUDIT",
    ]
    for stem in required_pass_stems:
        if payloads.get(stem, {}).get("status") != "PASS":
            failures.append(f"{stem} status is not PASS")

    candidate = payloads.get("CANDIDATE_INVENTORY_AUDIT", {})
    if candidate.get("candidate_row_count_raw_attempts") != 13_540_033:
        failures.append("candidate raw-attempt count mismatch")
    if candidate.get("unique_candidate_denominator") != 12_852_758:
        failures.append("candidate unique denominator mismatch")
    if candidate.get("candidate_rows_written_recomputed") != 120_000:
        failures.append("candidate compact row recompute mismatch")

    path = payloads.get("DISCOVERY_PATH_LABEL_INVENTORY_AUDIT", {})
    if path.get("path_label_row_count") != 12_852_758:
        failures.append("path-label count mismatch")
    if path.get("path_label_rows_written_recomputed") != 120_000:
        failures.append("path-label compact row recompute mismatch")

    lfs = payloads.get("GIT_LFS_STORAGE_AUDIT", {})
    for record in lfs.get("large_jsonl_records", []):
        if record.get("head_blob_is_lfs_pointer") is not True:
            failures.append(f"LFS pointer missing for {record.get('path')}")
        if record.get("local_materialized_for_jsonl_parsing") is not True:
            failures.append(f"LFS object not materialized for {record.get('path')}")
        if record.get("pointer_matches_local_worktree") is not True:
            failures.append(f"LFS pointer/local worktree mismatch for {record.get('path')}")
    if lfs.get("raw_blob_violations_over_100mb"):
        failures.append("raw >100MB Git blob violation present")

    repair = payloads.get("REPAIR_FOLLOWUP_LEDGER", {})
    if repair.get("exact_repair_blockers"):
        failures.append("repair ledger has exact repair blockers")

    manifest = payloads.get("OUTPUT_MANIFEST", {})
    for path_text in manifest.get("artifact_paths", []):
        artifact_path = ROOT / path_text
        if not artifact_path.exists():
            failures.append(f"manifest path missing: {path_text}")

    result = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": "verification_result",
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "terminal_decision": payloads.get("DECISION_LEDGER", {}).get("terminal_decision"),
        "candidate_raw_attempt_count": candidate.get("candidate_row_count_raw_attempts"),
        "candidate_unique_denominator": candidate.get("unique_candidate_denominator"),
        "path_label_row_count": path.get("path_label_row_count"),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_promotion": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_api_or_databento_route": False,
        "opens_mt5_order_account_history_behavior": False,
        "opens_remote_push": False,
        "opens_registry_edit": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }
    output_path = route_dir / f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = verify(args.route_dir)
    if not args.quiet:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
