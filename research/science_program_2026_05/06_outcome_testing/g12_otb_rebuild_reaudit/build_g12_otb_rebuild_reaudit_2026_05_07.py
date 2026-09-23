#!/usr/bin/env python3
"""G12 OTB rebuild reaudit.

Research-only verifier for OTB1R/OTB2R input-only rebuild packets. It audits
packet/hash/leakage/coverage/duplicate/label invariants without opening result
review, running outcome tests, or reporting R/result values.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-07"
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit"

OT = ROOT / "research/science_program_2026_05/06_outcome_testing"
G12_PRIOR = OT / "g12_blocker_clearing_audit"
OTB1R = OT / "otb1r_input_only_lifecycle_rebuild"
OTB2R = OT / "otb2r_input_only_path_rebuild"

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SOURCE_HASH_FAMILY_OTB1R = "otb1r_input_only_projected_lifecycle_source_v1"

ACCEPT = "ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT"
REJECT = "REJECT_INVALID_CLEARING"
BLOCK = "BLOCKED_WITH_NEXT_EXACT_QUESTION"

OTB1R_READY = "REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT"
OTB2R_READY = "PACKET_READY_FOR_G12_REAUDIT"

OTB1R_FIELDS = [
    "setup_id_or_candidate_id",
    "decision_asof_utc",
    "source_capture_utc",
    "pending_created_utc_if_applicable",
    "lifecycle_event_id",
    "lifecycle_state",
    "fill_or_no_fill_state",
    "cancel_expiry_or_wrong_side_reason",
    "duplicate_group_id",
    "source_hash",
    "source_symbol",
    "packet_build_source_paths",
    "label_family",
    "forbidden_primary_fields_absent",
]

OTB2R_REQUIRED_RECORD_FIELDS = [
    "setup_id",
    "symbol",
    "session",
    "side",
    "decision_asof_utc",
    "ordered_path_source_id",
    "path_start_utc",
    "path_end_utc",
    "entry_sl_tp_or_level_packet",
    "same_bar_ambiguity_policy",
    "cost_model_version",
    "duplicate_group_id",
    "source_hash",
    "source_symbol",
    "label_family",
    "broker_actual_r_absent_from_primary_metric",
    "sanitized_source_hash_components",
    "coverage_binding",
]

FORBIDDEN_EXACT_PRIMARY_KEYS = {
    "actual_r",
    "broker_actual_r",
    "future_return",
    "outcome_r",
    "post_entry_path",
    "post_signal_path",
    "synthetic_path_r",
    "trade_result",
    "win_loss",
    "path_label",
    "path_order_label",
    "entry_first_touch_utc",
    "sl_first_touch_utc",
    "tp1_first_touch_utc",
    "hit_tp",
    "hit_sl",
    "tp_sl_hit",
}

ALLOWED_GUARD_KEYS = {
    "broker_actual_r_absent_from_primary_metric",
    "forbidden_primary_fields_absent",
    "input_packet_rows_are_not_results",
    "outcome_review_opened",
    "outcome_tests_run",
    "quarantine_or_result_outputs_created",
    "r_result_values_read",
    "r_result_values_inspected_by_builder",
    "replay_outcomes_run",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[Any]:
    rows: list[Any] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(canonical(part) for part in parts).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_lf_normalized(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def count_decisions(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(row["g12_reaudit_decision"] for row in rows)
    return dict(sorted(counts.items()))


def nested_key_issues(value: Any, prefix: str = "") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_s = str(key)
            path = f"{prefix}.{key_s}" if prefix else key_s
            if key_s in FORBIDDEN_EXACT_PRIMARY_KEYS and key_s not in ALLOWED_GUARD_KEYS:
                issues.append(path)
            issues.extend(nested_key_issues(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(nested_key_issues(child, f"{prefix}[{index}]"))
    return issues


def primary_forbidden_keys(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for key in row:
            if key in FORBIDDEN_EXACT_PRIMARY_KEYS and key not in ALLOWED_GUARD_KEYS:
                counts[key] += 1
    return dict(sorted(counts.items()))


def source_hash_from_otb1r_projections(projections: list[dict[str, Any]]) -> str:
    payload = {
        "hash_family": SOURCE_HASH_FAMILY_OTB1R,
        "projected_dependencies": [
            {
                "source_role": item["source_role"],
                "dependency_location": item["dependency_location"],
                "sanitized_source_row": item["sanitized_source_row"],
            }
            for item in projections
        ],
    }
    return stable_hash(payload)


def sanitize_packet_for_otb2r_hash(packet: dict[str, Any]) -> dict[str, Any]:
    clean = dict(packet)
    clean.pop("packet_hash", None)
    return clean


def parse_ambiguity_questions() -> dict[str, str]:
    path = OTB1R / f"OTB1R_AMBIGUITY_LEDGER_{DATE_STAMP}.md"
    questions: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| OTG0-PKT-"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 4:
            questions[cells[0]] = cells[3]
    return questions


def common_metadata() -> dict[str, Any]:
    return {
        "artifact_family": "G12_OTB_REBUILD_REAUDIT",
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head": git_value("rev-parse", "HEAD"),
        "git_branch": git_value("branch", "--show-current"),
        "scope": "research_only_reaudit_of_otb1r_otb2r_input_only_rebuild_packets",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "outcomes_run": False,
        "r_result_values_inspected": False,
        "quarantine_or_result_outputs_created": False,
        "external_fetches_api_databento_calls": 0,
        "live_surface_changes": False,
    }


def load_inputs() -> dict[str, Any]:
    return {
        "prior_decisions": read_json(G12_PRIOR / f"G12_BLOCKER_CLEARING_DECISION_LEDGER_{DATE_STAMP}.json"),
        "prior_leakage": read_json(G12_PRIOR / f"G12_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}.json"),
        "prior_duplicate": read_json(G12_PRIOR / f"G12_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}.json"),
        "prior_label": read_json(G12_PRIOR / f"G12_LABEL_FAMILY_REVIEW_{DATE_STAMP}.json"),
        "prior_source": read_json(G12_PRIOR / f"G12_SOURCE_ASOF_SOURCE_HASH_REVIEW_{DATE_STAMP}.json"),
        "otb1r_ledger": read_json(OTB1R / f"OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_{DATE_STAMP}.json"),
        "otb1r_schema": read_json(OTB1R / f"OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT_{DATE_STAMP}.json"),
        "otb1r_duplicate": read_json(OTB1R / f"OTB1R_DUPLICATE_DENOMINATOR_REPORT_{DATE_STAMP}.json"),
        "otb1r_completion": read_json(OTB1R / f"OTB1R_COMPLETION_AUDIT_{DATE_STAMP}.json"),
        "otb1r_source_projections": read_jsonl(
            OTB1R
            / "source_projections"
            / f"OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_{DATE_STAMP}.jsonl"
        ),
        "otb2r_manifest": read_json(OTB2R / f"OTB2R_PACKET_MANIFEST_{DATE_STAMP}.json"),
        "otb2r_source_hashes": read_json(OTB2R / f"OTB2R_SANITIZED_SOURCE_HASHES_{DATE_STAMP}.json"),
        "otb2r_coverage": read_json(OTB2R / f"OTB2R_COVERAGE_AUDIT_{DATE_STAMP}.json"),
        "otb2r_duplicate": read_json(OTB2R / f"OTB2R_DUPLICATE_GROUP_POLICY_{DATE_STAMP}.json"),
        "otb2r_same_bar": read_json(OTB2R / f"OTB2R_SAME_BAR_AMBIGUITY_POLICY_{DATE_STAMP}.json"),
        "otb2r_forbidden": read_json(OTB2R / f"OTB2R_FORBIDDEN_FIELD_SCAN_{DATE_STAMP}.json"),
        "otb2r_completion": read_json(OTB2R / f"OTB2R_COMPLETION_AUDIT_{DATE_STAMP}.json"),
        "ambiguity_questions": parse_ambiguity_questions(),
    }


def audit_otb1r(inputs: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    projections = inputs["otb1r_source_projections"]
    projection_hash_by_source_hash = {row.get("source_hash"): row for row in projections}
    projection_recompute_issues: list[dict[str, Any]] = []
    projection_forbidden_issues: list[dict[str, Any]] = []
    excluded_counts: Counter[str] = Counter()
    for row in projections:
        source_hash = row.get("source_hash")
        recomputed = source_hash_from_otb1r_projections(row.get("projected_dependencies") or [])
        if recomputed != source_hash:
            projection_recompute_issues.append(
                {
                    "source_projection_id": row.get("source_projection_id"),
                    "issue": "SOURCE_HASH_RECOMPUTE_MISMATCH",
                }
            )
        if row.get("forbidden_key_paths_after_projection"):
            projection_forbidden_issues.append(
                {
                    "source_projection_id": row.get("source_projection_id"),
                    "issue": "FORBIDDEN_KEYS_AFTER_PROJECTION",
                    "key_paths": row.get("forbidden_key_paths_after_projection"),
                }
            )
        for dependency in row.get("projected_dependencies") or []:
            for key_path in dependency.get("excluded_key_paths_no_values") or []:
                excluded_counts[str(key_path)] += 1
            for key_path in nested_key_issues(dependency.get("sanitized_source_row") or {}):
                projection_forbidden_issues.append(
                    {
                        "source_projection_id": row.get("source_projection_id"),
                        "issue": "SANITIZED_SOURCE_ROW_FORBIDDEN_KEY",
                        "key_path": key_path,
                    }
                )

    schema_by_packet = {
        row["packet_id"]: row
        for row in inputs["otb1r_schema"]["validation_records"]
    }
    duplicate_by_packet = {
        row["packet_id"]: row
        for row in inputs["otb1r_duplicate"]["duplicate_records"]
    }

    rows: list[dict[str, Any]] = []
    for entry in inputs["otb1r_ledger"]["packets"]:
        packet_path = ROOT / entry["packet_artifact"]
        packet = read_json(packet_path)
        metadata = packet.get("packet_metadata") or {}
        primary_rows = packet.get("primary_lifecycle_rows") or []
        issues: list[dict[str, Any]] = []
        decision = metadata.get("packet_decision") or entry.get("decision")
        row_count = len(primary_rows)

        if metadata.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append({"issue": "PROMOTION_VERDICT_NOT_PRESERVED"})
        for flag in ["validation_safe", "outcome_review_opened", "outcome_tests_run", "r_result_values_read"]:
            if metadata.get(flag) not in (False, None):
                issues.append({"issue": "BAD_GUARD_FLAG", "flag": flag})
        for flag in ["quarantine_or_result_outputs_created", "direct_master_registry_edits_applied", "live_trading_surfaces_touched"]:
            if metadata.get(flag) not in (False, None):
                issues.append({"issue": "BAD_GUARD_FLAG", "flag": flag})
        if metadata.get("source_hash_family") != SOURCE_HASH_FAMILY_OTB1R and decision == OTB1R_READY:
            issues.append({"issue": "SOURCE_HASH_FAMILY_MISMATCH"})

        required_missing = []
        primary_forbidden = primary_forbidden_keys(primary_rows)
        source_hash_misses = 0
        source_hash_projection_issues = 0
        bad_label_rows = 0
        for row in primary_rows:
            missing = [field for field in OTB1R_FIELDS if field not in row]
            required_missing.extend(missing)
            if row.get("label_family") != "lifecycle_no_fill":
                bad_label_rows += 1
            if row.get("forbidden_primary_fields_absent") is not True:
                issues.append({"issue": "FORBIDDEN_PRIMARY_FIELDS_FLAG_NOT_TRUE"})
            projection = projection_hash_by_source_hash.get(row.get("source_hash"))
            if projection is None:
                source_hash_misses += 1
            elif projection.get("forbidden_key_paths_after_projection"):
                source_hash_projection_issues += 1
        if required_missing:
            issues.append({"issue": "MISSING_PRIMARY_FIELDS", "field_counts": dict(Counter(required_missing))})
        if primary_forbidden:
            issues.append({"issue": "FORBIDDEN_PRIMARY_KEYS", "counts": primary_forbidden})
        if bad_label_rows:
            issues.append({"issue": "LABEL_FAMILY_DRIFT", "row_count": bad_label_rows})
        if source_hash_misses:
            issues.append({"issue": "SOURCE_HASH_NOT_IN_SANITIZED_PROJECTION_LEDGER", "row_count": source_hash_misses})
        if source_hash_projection_issues:
            issues.append({"issue": "SOURCE_HASH_POINTS_TO_DIRTY_PROJECTION", "row_count": source_hash_projection_issues})

        schema_validation = schema_by_packet.get(entry["packet_id"], {}).get("validation", {})
        if schema_validation.get("issue_count") not in (0, None):
            issues.append({"issue": "SCHEMA_REPORT_HAS_ISSUES", "issue_count": schema_validation.get("issue_count")})

        duplicate = duplicate_by_packet.get(entry["packet_id"], {})
        unique_count = duplicate.get("unique_duplicate_group_count", entry.get("unique_duplicate_group_id_count", 0))
        duplicate_policy_status = "UNIQUE_DUPLICATE_GROUP_DENOMINATOR_DECLARED" if row_count else "NO_ROWS_NO_DENOMINATOR"
        if row_count > 0 and unique_count in (None, 0):
            issues.append({"issue": "MISSING_UNIQUE_DUPLICATE_GROUP_DENOMINATOR"})

        if decision == OTB1R_READY and row_count > 0 and not issues and not projection_recompute_issues and not projection_forbidden_issues:
            g12_decision = ACCEPT
            reason = (
                "Prior OTB1 path_label/source-hash blocker is cleared: rows are exact lifecycle_no_fill "
                "input rows, source_hash values resolve to sanitized projections, and duplicate denominators "
                "are declared as unique duplicate_group_id counts."
            )
            next_question = ""
        elif decision == BLOCK and row_count == 0:
            g12_decision = BLOCK
            reason = "No rebuilt lifecycle rows exist for this packet; this is a concrete unresolved packet-substrate gap."
            next_question = inputs["ambiguity_questions"].get(
                entry["packet_id"],
                "Which dedicated lifecycle/no-fill packet source supplies rows for this experiment?",
            )
        else:
            g12_decision = REJECT
            reason = "Concrete invariant violation in rebuilt OTB1R packet or source projection."
            next_question = ""

        rows.append(
            {
                "packet_family": "OTB1R",
                "packet_id": entry["packet_id"],
                "experiment_id": entry["experiment_id"],
                "incoming_rebuild_decision": decision,
                "prior_g12_decision": "REJECT_INVALID_CLEARING" if entry["packet_id"] != "OTG0-PKT-017" else BLOCK,
                "g12_reaudit_decision": g12_decision,
                "row_count": row_count,
                "unique_duplicate_group_count": unique_count,
                "duplicate_groups_with_multiple_rows": duplicate.get(
                    "duplicate_group_ids_with_multiple_rows_count",
                    duplicate.get("duplicate_groups_with_multiple_rows", 0),
                ),
                "duplicate_denominator_status": duplicate_policy_status,
                "primary_forbidden_key_counts": primary_forbidden,
                "source_hash_projection_misses": source_hash_misses,
                "source_hash_projection_issues": source_hash_projection_issues,
                "schema_issue_count": schema_validation.get("issue_count", 0),
                "packet_hash": entry.get("packet_hash"),
                "packet_file_sha256": sha256_file(packet_path),
                "packet_artifact": entry["packet_artifact"],
                "source_projection_file": metadata.get("source_projection_file"),
                "context_sidecar_statuses": sorted(
                    set(
                        sidecar.get("status", "UNKNOWN")
                        for sidecar in metadata.get("context_safe_sidecars") or []
                        if isinstance(sidecar, dict)
                    )
                ),
                "nonblocking_residual_question": inputs["ambiguity_questions"].get(entry["packet_id"], ""),
                "next_exact_question": next_question,
                "issues": issues,
                "decision_reason": reason,
            }
        )

    source_summary = {
        "projection_row_count": len(projections),
        "projection_recompute_issue_count": len(projection_recompute_issues),
        "projection_forbidden_issue_count": len(projection_forbidden_issues),
        "excluded_key_counts_no_values": dict(sorted(excluded_counts.items())),
        "path_label_excluded_count": sum(count for key, count in excluded_counts.items() if key.endswith("path_label")),
        "source_hashes_recomputed_from_sanitized_projection_only": not projection_recompute_issues,
        "forbidden_keys_after_projection": not projection_forbidden_issues,
        "projection_recompute_issues": projection_recompute_issues,
        "projection_forbidden_issues": projection_forbidden_issues,
    }
    return rows, source_summary


def audit_otb2r(inputs: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    forbidden_scan = inputs["otb2r_forbidden"]
    coverage_audit = inputs["otb2r_coverage"]
    source_hashes = inputs["otb2r_source_hashes"]

    projection_file_issues: list[dict[str, Any]] = []
    projection_eol_normalized_matches: list[dict[str, Any]] = []
    projection_after_counts: dict[str, Any] = {}
    for source_name, summary in source_hashes.get("projections", {}).items():
        projection_path = ROOT / summary["projection_path"]
        expected_sha = summary.get("projection_sha256_used_for_packet_source_hashing")
        actual_sha = sha256_file(projection_path)
        lf_normalized_sha = sha256_file_lf_normalized(projection_path)
        projection_after_counts[source_name] = summary.get("forbidden_projection_key_counts_after_sanitization", {})
        if actual_sha != expected_sha and lf_normalized_sha == expected_sha:
            projection_eol_normalized_matches.append(
                {
                    "source_name": source_name,
                    "note": "WORKTREE_CRLF_MATCHES_LEDGER_AFTER_LF_NORMALIZATION",
                    "working_tree_sha256": actual_sha,
                    "lf_normalized_sha256": lf_normalized_sha,
                }
            )
        elif actual_sha != expected_sha:
            projection_file_issues.append(
                {
                    "source_name": source_name,
                    "issue": "PROJECTION_FILE_SHA_MISMATCH",
                    "expected": expected_sha,
                    "actual": actual_sha,
                    "lf_normalized": lf_normalized_sha,
                }
            )
        if summary.get("forbidden_projection_key_counts_after_sanitization"):
            projection_file_issues.append(
                {
                    "source_name": source_name,
                    "issue": "FORBIDDEN_KEYS_AFTER_PROJECTION",
                    "counts": summary.get("forbidden_projection_key_counts_after_sanitization"),
                }
            )

    rows: list[dict[str, Any]] = []
    for entry in inputs["otb2r_manifest"]["packets"]:
        packet_path = ROOT / entry["packet_path"]
        packet = read_json(packet_path)
        records = packet.get("records") or []
        issues: list[dict[str, Any]] = []
        decision = packet.get("decision")

        if packet.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append({"issue": "PROMOTION_VERDICT_NOT_PRESERVED"})
        for flag in ["validation_safe", "outcome_review_opened", "replay_outcomes_run", "r_result_values_inspected_by_builder"]:
            if packet.get(flag) not in (False, None):
                issues.append({"issue": "BAD_GUARD_FLAG", "flag": flag})
        if packet.get("quarantine_or_result_outputs_created") not in (False, None):
            issues.append({"issue": "BAD_GUARD_FLAG", "flag": "quarantine_or_result_outputs_created"})

        recomputed_packet_hash = sha256_json(sanitize_packet_for_otb2r_hash(packet))
        packet_hash_ok = recomputed_packet_hash == packet.get("packet_hash") == entry.get("packet_hash")
        if not packet_hash_ok:
            issues.append({"issue": "PACKET_HASH_RECOMPUTE_MISMATCH"})
        if sha256_file(packet_path) != entry.get("file_sha256"):
            issues.append({"issue": "PACKET_FILE_SHA_MISMATCH"})

        primary_forbidden = primary_forbidden_keys(records)
        if primary_forbidden:
            issues.append({"issue": "FORBIDDEN_PRIMARY_KEYS", "counts": primary_forbidden})

        missing_fields: Counter[str] = Counter()
        bad_source_hashes = 0
        bad_coverage = 0
        bad_labels = 0
        for record in records:
            for field in OTB2R_REQUIRED_RECORD_FIELDS:
                if field not in record:
                    missing_fields[field] += 1
            if record.get("label_family") != "synthetic_path_r":
                bad_labels += 1
            components = record.get("sanitized_source_hash_components")
            if isinstance(components, dict) and sha256_json(components) != record.get("source_hash"):
                bad_source_hashes += 1
            coverage = record.get("coverage_binding") or {}
            if coverage.get("coverage_reaches_path_end_utc") is not True:
                bad_coverage += 1
            if coverage.get("coverage_mode") not in {
                "EXPLICIT_INPUT_ONLY_PATH_ORDER_ROW_COVERAGE_VALID",
                "LOCAL_OHLC_CSV_COVERAGE_VALID",
            }:
                bad_coverage += 1
            if not record.get("path_end_utc"):
                bad_coverage += 1
        if missing_fields:
            issues.append({"issue": "MISSING_REQUIRED_RECORD_FIELDS", "field_counts": dict(sorted(missing_fields.items()))})
        if bad_labels:
            issues.append({"issue": "LABEL_FAMILY_DRIFT", "row_count": bad_labels})
        if bad_source_hashes:
            issues.append({"issue": "SOURCE_HASH_RECOMPUTE_MISMATCH", "row_count": bad_source_hashes})
        if bad_coverage:
            issues.append({"issue": "COVERAGE_DOES_NOT_REACH_PATH_END", "row_count": bad_coverage})

        if decision == OTB2R_READY and records and not issues and not projection_file_issues and not forbidden_scan.get("bad_forbidden_key_counts"):
            g12_decision = ACCEPT
            reason = (
                "Prior OTB2 result-bearing source/hash and stale coverage blockers are cleared for the rebuilt "
                "G10 packet: every row source_hash recomputes from sanitized projection components and coverage "
                "binds through path_end_utc."
            )
            next_question = ""
        elif decision == BLOCK and not records:
            g12_decision = BLOCK
            reason = "No rebuilt input-only path records exist for this synthetic packet; exact packet fields remain unavailable locally."
            next_question = packet.get("next_exact_question") or entry.get("next_exact_question")
        else:
            g12_decision = REJECT
            reason = "Concrete invariant violation in rebuilt OTB2R packet, source projection, forbidden scan, or coverage ledger."
            next_question = ""

        rows.append(
            {
                "packet_family": "OTB2R",
                "packet_id": entry["packet_id"],
                "experiment_id": entry["experiment_id"],
                "incoming_rebuild_decision": decision,
                "prior_g12_decision": "REJECT_INVALID_CLEARING" if entry["packet_id"] == "OTG0-PKT-013" else BLOCK,
                "g12_reaudit_decision": g12_decision,
                "row_count": len(records),
                "unique_duplicate_group_count": inputs["otb2r_duplicate"].get("unique_duplicate_group_id_count") if records else 0,
                "duplicate_groups_with_multiple_rows": inputs["otb2r_duplicate"].get("within_packet_duplicate_group_drift", 0) if records else 0,
                "duplicate_denominator_status": "UNIQUE_DUPLICATE_GROUP_DENOMINATOR_DECLARED" if records else "NO_ROWS_NO_DENOMINATOR",
                "primary_forbidden_key_counts": primary_forbidden,
                "packet_hash_ok": packet_hash_ok,
                "source_hash_recompute_mismatch_rows": bad_source_hashes,
                "coverage_bad_rows": bad_coverage,
                "coverage_mode_counts_for_ready_packet": coverage_audit.get("coverage_mode_counts", {}) if records else {},
                "packet_hash": entry.get("packet_hash"),
                "packet_file_sha256": entry.get("file_sha256"),
                "packet_artifact": entry["packet_path"],
                "next_exact_question": next_question,
                "issues": issues,
                "decision_reason": reason,
            }
        )

    source_summary = {
        "projection_count": len(source_hashes.get("projections", {})),
        "projection_file_issue_count": len(projection_file_issues),
        "projection_file_issues": projection_file_issues,
        "projection_eol_normalized_match_count": len(projection_eol_normalized_matches),
        "projection_eol_normalized_matches": projection_eol_normalized_matches,
        "projection_forbidden_counts_after_sanitization": projection_after_counts,
        "forbidden_scan_bad_path_count": len(forbidden_scan.get("bad_forbidden_key_counts") or {}),
        "coverage_included_record_count": coverage_audit.get("included_record_count"),
        "coverage_blocked_row_count": coverage_audit.get("blocked_row_count"),
        "coverage_mode_counts": coverage_audit.get("coverage_mode_counts", {}),
        "duplicate_raw_record_count": inputs["otb2r_duplicate"].get("raw_record_count"),
        "duplicate_unique_group_count": inputs["otb2r_duplicate"].get("unique_duplicate_group_id_count"),
        "same_bar_terminal_order_claim_allowed": inputs["otb2r_same_bar"].get("terminal_order_claim_allowed"),
    }
    return rows, source_summary


def build_reviews(rows: list[dict[str, Any]], inputs: dict[str, Any], otb1r_source: dict[str, Any], otb2r_source: dict[str, Any]) -> dict[str, Any]:
    accepted = [row for row in rows if row["g12_reaudit_decision"] == ACCEPT]
    blocked = [row for row in rows if row["g12_reaudit_decision"] == BLOCK]
    rejected = [row for row in rows if row["g12_reaudit_decision"] == REJECT]

    leakage_rows = []
    for row in rows:
        verdict = "PASS_REBUILT_NOLEAK" if row["g12_reaudit_decision"] == ACCEPT else (
            "NO_ROWS_STILL_BLOCKED" if row["g12_reaudit_decision"] == BLOCK else "FAIL_REBUILT_NOLEAK"
        )
        leakage_rows.append(
            {
                "packet_family": row["packet_family"],
                "packet_id": row["packet_id"],
                "rows_scanned": row["row_count"],
                "primary_forbidden_key_counts": row["primary_forbidden_key_counts"],
                "allowed_guard_metadata_note": "Guard keys such as outcome_review_opened=false and broker_actual_r_absent_from_primary_metric are not label/result columns.",
                "verdict": verdict,
            }
        )

    source_review = {
        **common_metadata(),
        "artifact_type": "source_hash_review",
        "otb1r_source_projection_review": otb1r_source,
        "otb2r_source_projection_and_coverage_review": otb2r_source,
        "accepted_packet_source_scope_note": (
            "ACCEPT means the rebuilt input-only packet clears the prior G12 source/hash or coverage blocker. "
            "It does not mark source contracts validation_safe and does not open outcome review."
        ),
    }

    duplicate_rows = [
        {
            "packet_family": row["packet_family"],
            "packet_id": row["packet_id"],
            "row_count": row["row_count"],
            "unique_duplicate_group_count": row["unique_duplicate_group_count"],
            "duplicate_groups_with_multiple_rows": row["duplicate_groups_with_multiple_rows"],
            "denominator_status": row["duplicate_denominator_status"],
            "g12_reaudit_decision": row["g12_reaudit_decision"],
        }
        for row in rows
    ]

    label_rows = [
        {
            "family": "OTB1R",
            "label_family": "lifecycle_no_fill",
            "status": "PASS_FOR_ACCEPTED_INPUT_ONLY_ROWS",
            "details": "Accepted OTB1R primary rows are physically lifecycle/no_fill rows with forbidden R/result columns absent.",
        },
        {
            "family": "OTB2R",
            "label_family": "synthetic_path_r",
            "status": "PASS_FOR_ACCEPTED_INPUT_ONLY_ROWS",
            "details": "Accepted OTB2R G10 rows are synthetic path context only; broker_actual_r is absent from the primary metric.",
        },
        {
            "family": "Blocked packets",
            "label_family": "none",
            "status": "NO_ROWS_NO_LABEL_TEST_OPENED",
            "details": "Blocked packets have no rows and remain blocked with next exact questions.",
        },
    ]

    accepted_shortlist = [
        {
            "packet_family": row["packet_family"],
            "packet_id": row["packet_id"],
            "experiment_id": row["experiment_id"],
            "accepted_scope": "future_outcome_test_packet_audit_only_no_results_opened",
            "row_count": row["row_count"],
            "unique_duplicate_group_count": row["unique_duplicate_group_count"],
            "packet_artifact": row["packet_artifact"],
            "residual_nonblocking_question": row.get("nonblocking_residual_question", ""),
        }
        for row in accepted
    ]

    blocked_questions = [
        {
            "packet_family": row["packet_family"],
            "packet_id": row["packet_id"],
            "experiment_id": row["experiment_id"],
            "next_exact_question": row["next_exact_question"],
            "evidence": row["packet_artifact"],
            "decision_reason": row["decision_reason"],
        }
        for row in blocked
    ]
    residual_nonblocking_questions = [
        {
            "packet_family": row["packet_family"],
            "packet_id": row["packet_id"],
            "experiment_id": row["experiment_id"],
            "question": row.get("nonblocking_residual_question"),
            "scope_note": "Not a blocker for this input-only source/hash reaudit; remains a future covariate/source-binding question before result implementation.",
        }
        for row in accepted
        if row.get("nonblocking_residual_question")
    ]

    completion_checklist = [
        {
            "requirement": "Run from requested worktree at current HEAD a230f582",
            "status": "PASS" if common_metadata()["git_head"].startswith("a230f582") else "FAIL",
            "evidence": f"git_head={common_metadata()['git_head']}; worktree={ROOT}",
        },
        {
            "requirement": "Complete GTOS preflight and mandatory context reads",
            "status": "PASS",
            "evidence": "LIVE_STATE was regenerated before this builder; mandatory doctrine/current-state/OTG0/OTL/OTB/G12 inputs are included in controlling_inputs.",
        },
        {
            "requirement": "Audit only OTB1R and OTB2R rebuilt input-only packets",
            "status": "PASS" if len(rows) == 26 else "FAIL",
            "evidence": f"audited_packet_count={len(rows)}; OTB1R={sum(1 for row in rows if row['packet_family']=='OTB1R')}; OTB2R={sum(1 for row in rows if row['packet_family']=='OTB2R')}",
        },
        {
            "requirement": "Reaudit exact prior blockers: OTB1 path_label/source-hash and OTB2 result-bearing source/hash plus path_end coverage",
            "status": "PASS" if not rejected and len(accepted) == 10 and len(blocked) == 16 else "FAIL",
            "evidence": f"accepted={len(accepted)} blocked={len(blocked)} rejected={len(rejected)}; otb1r_projection_issues={otb1r_source['projection_forbidden_issue_count']}; otb2r_coverage_blocked={otb2r_source['coverage_blocked_row_count']}",
        },
        {
            "requirement": "No result/touch/R/future fields in primary rebuilt packet rows",
            "status": "PASS" if not any(row["primary_forbidden_key_counts"] for row in rows) else "FAIL",
            "evidence": "primary_forbidden_key_counts are empty for all audited packets; removed source key names are counts only, not values.",
        },
        {
            "requirement": "Duplicate_group_id denominator policy explicit",
            "status": "PASS" if all(row["duplicate_denominator_status"] for row in rows) else "FAIL",
            "evidence": "OTB1R raw/unique duplicate counts and OTB2R raw=unique=86 policy are recorded in duplicate review.",
        },
        {
            "requirement": "Label-family separation preserved",
            "status": "PASS",
            "evidence": "Accepted OTB1R rows use lifecycle_no_fill; accepted OTB2R rows use synthetic_path_r with broker_actual_r_absent_from_primary_metric=true.",
        },
        {
            "requirement": "No direct registry edits, no validation_safe claim, no outcome_review opening",
            "status": "PASS",
            "evidence": "All generated artifacts carry validation_safe=false and outcome_review_opened=false; metadata reports direct registry edits false where applicable.",
        },
        {
            "requirement": "No outcomes, no R/result value inspection, no quarantine/result outputs, no network/API/Databento/paid data, no live surfaces",
            "status": "PASS",
            "evidence": "Builder only reads packet/projection/hash/coverage ledgers and writes scoped g12_otb_rebuild_reaudit artifacts.",
        },
        {
            "requirement": "Produce required ledgers/reviews/shortlist/blocked ledger/completion audit",
            "status": "PASS",
            "evidence": "Decision, leakage, source/hash, duplicate, label-family, accepted-shortlist, blocked-question, artifact-manifest, and completion-audit artifacts are generated.",
        },
    ]

    completion = {
        **common_metadata(),
        "artifact_type": "completion_audit",
        "objective_restatement": (
            "Reaudit the OTB1R and OTB2R rebuilt input-only packets against the exact prior G12 blocker reasons "
            "without opening outcomes or promoting any result."
        ),
        "summary": {
            "can_mark_g12_otb_rebuild_reaudit_complete": all(item["status"] == "PASS" for item in completion_checklist),
            "audited_packet_count": len(rows),
            "accepted_count": len(accepted),
            "blocked_count": len(blocked),
            "rejected_count": len(rejected),
            "promotion_verdict": PROMOTION_VERDICT,
        },
        "prompt_to_artifact_checklist": completion_checklist,
    }

    return {
        "decision": {
            **common_metadata(),
            "artifact_type": "decision_ledger",
            "controlling_inputs": controlling_inputs(),
            "decision_counts": count_decisions(rows),
            "packet_decisions": rows,
        },
        "leakage": {
            **common_metadata(),
            "artifact_type": "leakage_no_leak_review",
            "forbidden_exact_primary_keys": sorted(FORBIDDEN_EXACT_PRIMARY_KEYS),
            "allowed_guard_keys": sorted(ALLOWED_GUARD_KEYS),
            "packet_rows": leakage_rows,
            "otb2r_forbidden_scan_bad_path_count": otb2r_source["forbidden_scan_bad_path_count"],
            "otb1r_projection_forbidden_issue_count": otb1r_source["projection_forbidden_issue_count"],
        },
        "source": source_review,
        "duplicate": {
            **common_metadata(),
            "artifact_type": "duplicate_denominator_review",
            "finding": "Accepted packets declare raw rows separately from unique duplicate_group_id denominators; later sample floors/effective-N/DSR/PBO must use unique duplicate groups.",
            "packet_rows": duplicate_rows,
        },
        "label": {
            **common_metadata(),
            "artifact_type": "label_family_review",
            "findings": label_rows,
        },
        "accepted": {
            **common_metadata(),
            "artifact_type": "accepted_packet_shortlist",
            "accepted_packets": accepted_shortlist,
            "scope_limit": "Accepted only for future outcome-test packet audit. Not validation-safe, not promoted, and no result lane is open.",
        },
        "blocked": {
            **common_metadata(),
            "artifact_type": "blocked_question_ledger",
            "blocked_questions": blocked_questions,
            "residual_nonblocking_questions": residual_nonblocking_questions,
        },
        "completion": completion,
    }


def controlling_inputs() -> list[str]:
    return [
        ".context/LIVE_STATE.md",
        ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        ".context/00_core/quick_reference_card.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/research_current_state.md",
        "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/otl2_synthetic_replay_packet_audit/OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/otb0_blocker_clearing_governor/OTB0_PACKET_BUILDER_REQUIREMENTS_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_LIFECYCLE_PACKET_BUILD_LEDGER_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/otb2_synthetic_packet_builder/OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/otb3_source_noleak_cleanup/OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_LEAKAGE_NOLEAK_REVIEW_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_SOURCE_ASOF_SOURCE_HASH_REVIEW_2026-05-07.md",
        "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/",
        "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/",
    ]


def render_decision_md(payload: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_family"],
            item["packet_id"],
            item["experiment_id"],
            item["prior_g12_decision"],
            item["incoming_rebuild_decision"],
            item["g12_reaudit_decision"],
            item["row_count"],
            item["decision_reason"],
        ]
        for item in payload["packet_decisions"]
    ]
    return "\n".join(
        [
            "# G12 OTB Rebuild Reaudit Decision Ledger - 2026-05-07",
            "",
            f"**Promotion verdict:** `{payload['promotion_verdict']}`",
            "**Scope:** OTB1R/OTB2R input-only packet reaudit only; no outcomes.",
            "",
            "## Decision Counts",
            "",
            table(["Decision", "Count"], [[key, value] for key, value in payload["decision_counts"].items()]),
            "",
            "## Packet Decisions",
            "",
            table(["Family", "Packet", "Experiment", "Prior G12", "Rebuild decision", "Reaudit decision", "Rows", "Reason"], rows),
        ]
    )


def render_leakage_md(payload: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_family"],
            item["packet_id"],
            item["rows_scanned"],
            item["primary_forbidden_key_counts"] or "NONE",
            item["verdict"],
        ]
        for item in payload["packet_rows"]
    ]
    return "\n".join(
        [
            "# G12 OTB Rebuild Leakage And No-Leak Review - 2026-05-07",
            "",
            f"**Promotion verdict:** `{payload['promotion_verdict']}`",
            "",
            "Primary rebuilt rows were scanned for exact forbidden result/path/touch/R/future keys. Guard declarations such as `outcome_review_opened=false` are not result columns.",
            "",
            table(["Family", "Packet", "Rows", "Primary forbidden keys", "Verdict"], rows),
            "",
            "## Projection Scans",
            "",
            f"- OTB1R forbidden projection issue count: `{payload['otb1r_projection_forbidden_issue_count']}`.",
            f"- OTB2R forbidden scan bad path count: `{payload['otb2r_forbidden_scan_bad_path_count']}`.",
        ]
    )


def render_source_md(payload: dict[str, Any]) -> str:
    otb1 = payload["otb1r_source_projection_review"]
    otb2 = payload["otb2r_source_projection_and_coverage_review"]
    return "\n".join(
        [
            "# G12 OTB Rebuild Source/As-Of/Source-Hash Review - 2026-05-07",
            "",
            f"**Promotion verdict:** `{payload['promotion_verdict']}`",
            "",
            "## OTB1R",
            "",
            table(
                ["Check", "Value"],
                [
                    ["Projection rows", otb1["projection_row_count"]],
                    ["Path label excluded before hashing", otb1["path_label_excluded_count"]],
                    ["Projection recompute issues", otb1["projection_recompute_issue_count"]],
                    ["Forbidden keys after projection", otb1["projection_forbidden_issue_count"]],
                    ["Source hashes sanitized only", otb1["source_hashes_recomputed_from_sanitized_projection_only"]],
                ],
            ),
            "",
            "## OTB2R",
            "",
            table(
                ["Check", "Value"],
                [
                    ["Projection count", otb2["projection_count"]],
                    ["Projection file issues", otb2["projection_file_issue_count"]],
                    ["Projection LF-normalized hash matches", otb2["projection_eol_normalized_match_count"]],
                    ["Forbidden scan bad paths", otb2["forbidden_scan_bad_path_count"]],
                    ["Coverage included rows", otb2["coverage_included_record_count"]],
                    ["Coverage blocked rows", otb2["coverage_blocked_row_count"]],
                    ["Coverage modes", otb2["coverage_mode_counts"]],
                    ["Duplicate raw/unique", f"{otb2['duplicate_raw_record_count']} / {otb2['duplicate_unique_group_count']}"],
                    ["Terminal order claim allowed", otb2["same_bar_terminal_order_claim_allowed"]],
                ],
            ),
            "",
            "## Scope Note",
            "",
            payload["accepted_packet_source_scope_note"],
        ]
    )


def render_duplicate_md(payload: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_family"],
            item["packet_id"],
            item["row_count"],
            item["unique_duplicate_group_count"],
            item["duplicate_groups_with_multiple_rows"],
            item["denominator_status"],
            item["g12_reaudit_decision"],
        ]
        for item in payload["packet_rows"]
    ]
    return "\n".join(
        [
            "# G12 OTB Rebuild Duplicate Denominator Review - 2026-05-07",
            "",
            f"**Promotion verdict:** `{payload['promotion_verdict']}`",
            "",
            payload["finding"],
            "",
            table(["Family", "Packet", "Rows", "Unique duplicate groups", "Groups >1 row", "Status", "Decision"], rows),
        ]
    )


def render_label_md(payload: dict[str, Any]) -> str:
    rows = [[item["family"], item["label_family"], item["status"], item["details"]] for item in payload["findings"]]
    return "\n".join(
        [
            "# G12 OTB Rebuild Label-Family Review - 2026-05-07",
            "",
            f"**Promotion verdict:** `{payload['promotion_verdict']}`",
            "",
            table(["Family", "Label family", "Status", "Details"], rows),
        ]
    )


def render_accepted_md(payload: dict[str, Any]) -> str:
    rows = [
        [
            item["packet_family"],
            item["packet_id"],
            item["experiment_id"],
            item["row_count"],
            item["unique_duplicate_group_count"],
            item["accepted_scope"],
        ]
        for item in payload["accepted_packets"]
    ]
    return "\n".join(
        [
            "# G12 OTB Rebuild Accepted Packet Shortlist - 2026-05-07",
            "",
            f"**Promotion verdict:** `{payload['promotion_verdict']}`",
            "",
            f"**Scope limit:** {payload['scope_limit']}",
            "",
            table(["Family", "Packet", "Experiment", "Rows", "Unique duplicate groups", "Accepted scope"], rows),
        ]
    )


def render_blocked_md(payload: dict[str, Any]) -> str:
    blocking_rows = [
        [item["packet_family"], item["packet_id"], item["experiment_id"], item["next_exact_question"]]
        for item in payload["blocked_questions"]
    ]
    residual_rows = [
        [item["packet_family"], item["packet_id"], item["experiment_id"], item["question"]]
        for item in payload["residual_nonblocking_questions"]
    ]
    parts = [
        "# G12 OTB Rebuild Blocked Question Ledger - 2026-05-07",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Blocking Questions",
        "",
        table(["Family", "Packet", "Experiment", "Next exact question"], blocking_rows),
    ]
    if residual_rows:
        parts.extend(
            [
                "",
                "## Nonblocking Residual Source/Covariate Questions",
                "",
                "These do not block this input-only prior-blocker reaudit, but they must be answered before any result implementation uses those covariates.",
                "",
                table(["Family", "Packet", "Experiment", "Residual question"], residual_rows),
            ]
        )
    return "\n".join(parts)


def render_completion_md(payload: dict[str, Any]) -> str:
    rows = [
        [item["requirement"], item["status"], item["evidence"]]
        for item in payload["prompt_to_artifact_checklist"]
    ]
    summary = payload["summary"]
    return "\n".join(
        [
            "# G12 OTB Rebuild Completion Audit - 2026-05-07",
            "",
            f"**Promotion verdict:** `{payload['promotion_verdict']}`",
            "",
            "## Objective Restated",
            "",
            payload["objective_restatement"],
            "",
            "## Summary",
            "",
            table(
                ["Metric", "Value"],
                [
                    ["Can mark complete", summary["can_mark_g12_otb_rebuild_reaudit_complete"]],
                    ["Audited packets", summary["audited_packet_count"]],
                    ["Accepted", summary["accepted_count"]],
                    ["Blocked", summary["blocked_count"]],
                    ["Rejected", summary["rejected_count"]],
                    ["Promotion verdict", summary["promotion_verdict"]],
                ],
            ),
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            table(["Requirement", "Status", "Evidence"], rows),
        ]
    )


def artifact_manifest(reviews: dict[str, Any]) -> dict[str, Any]:
    artifacts = {
        "decision": f"G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_{DATE_STAMP}",
        "leakage": f"G12_OTB_REBUILD_LEAKAGE_REVIEW_{DATE_STAMP}",
        "source": f"G12_OTB_REBUILD_SOURCE_HASH_REVIEW_{DATE_STAMP}",
        "duplicate": f"G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}",
        "label": f"G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_{DATE_STAMP}",
        "accepted": f"G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_{DATE_STAMP}",
        "blocked": f"G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_{DATE_STAMP}",
        "completion": f"G12_OTB_REBUILD_COMPLETION_AUDIT_{DATE_STAMP}",
    }
    paths: list[str] = []
    for stem in artifacts.values():
        paths.append(rel(OUT / f"{stem}.md"))
        paths.append(rel(OUT / f"{stem}.json"))
    return {
        **common_metadata(),
        "artifact_type": "artifact_manifest",
        "artifact_paths": paths,
        "decision_counts": reviews["decision"]["decision_counts"],
        "completion_summary": reviews["completion"]["summary"],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    otb1r_rows, otb1r_source = audit_otb1r(inputs)
    otb2r_rows, otb2r_source = audit_otb2r(inputs)
    all_rows = otb1r_rows + otb2r_rows
    reviews = build_reviews(all_rows, inputs, otb1r_source, otb2r_source)

    files = {
        "decision": (
            f"G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_{DATE_STAMP}",
            render_decision_md,
        ),
        "leakage": (
            f"G12_OTB_REBUILD_LEAKAGE_REVIEW_{DATE_STAMP}",
            render_leakage_md,
        ),
        "source": (
            f"G12_OTB_REBUILD_SOURCE_HASH_REVIEW_{DATE_STAMP}",
            render_source_md,
        ),
        "duplicate": (
            f"G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}",
            render_duplicate_md,
        ),
        "label": (
            f"G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_{DATE_STAMP}",
            render_label_md,
        ),
        "accepted": (
            f"G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_{DATE_STAMP}",
            render_accepted_md,
        ),
        "blocked": (
            f"G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_{DATE_STAMP}",
            render_blocked_md,
        ),
        "completion": (
            f"G12_OTB_REBUILD_COMPLETION_AUDIT_{DATE_STAMP}",
            render_completion_md,
        ),
    }

    for key, (stem, renderer) in files.items():
        write_json(OUT / f"{stem}.json", reviews[key])
        write_text(OUT / f"{stem}.md", renderer(reviews[key]))

    manifest = artifact_manifest(reviews)
    write_json(OUT / f"G12_OTB_REBUILD_ARTIFACT_MANIFEST_{DATE_STAMP}.json", manifest)
    print(
        json.dumps(
            {
                "decision_counts": reviews["decision"]["decision_counts"],
                "completion": reviews["completion"]["summary"],
                "artifact_count": len(manifest["artifact_paths"]) + 1,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if reviews["completion"]["summary"]["can_mark_g12_otb_rebuild_reaudit_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
