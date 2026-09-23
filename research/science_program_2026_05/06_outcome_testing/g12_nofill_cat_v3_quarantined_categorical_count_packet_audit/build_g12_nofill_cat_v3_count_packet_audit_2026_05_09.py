#!/usr/bin/env python3
"""Build the G12 NOFILL CAT V3 count-packet audit artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
SCHEMA_VERSION = "g12_nofill_cat_v3_count_packet_audit_v1"
AUDIT_LANE_ID = "G12_NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_AUDIT_V1"
CONTRACT_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

ACCEPT_DECISION = "ACCEPT_AS_QUARANTINED_CATEGORICAL_COUNT_CONTROL_EVIDENCE"
BLOCK_DECISION = "BLOCK_WITH_EXACT_COUNT_OR_SOURCE_QUESTION"
REJECT_DECISION = "REJECT_INVALID_COUNT_PACKET"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
COUNT_DIR = BASE / "nofill_cat_v3_quarantined_categorical_count_packet"
RESULT_CONTRACT_DIR = BASE / "nofill_cat_v3_result_contract_update"
G12_RESULT_CONTRACT_DIR = BASE / "g12_nofill_cat_v3_result_contract_audit"

SOURCE_CONTROL_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
}
SOURCE_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
EXPECTED_LABEL_COUNTS_ROW_LEVEL = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_LABEL_COUNTS_DUPLICATE_KEY = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_LABEL_COUNTS_DUPLICATE_GROUP = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 4,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 7,
}

EXPECTED_JSON = [
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SATURATION_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_COMPLETION_AUDIT_{DATE}.json",
]
EXPECTED_MD = [
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SATURATION_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_V3_COUNT_AUDIT_COMPLETION_AUDIT_{DATE}.md",
]
EXPECTED_PY = [
    "build_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py",
    "verify_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py",
    "test_g12_nofill_cat_v3_count_packet_audit_2026_05_09.py",
]

BASE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def now_utc() -> str:
    fixed = os.environ.get("G12_NOFILL_CAT_V3_COUNT_AUDIT_FIXED_GENERATED_AT")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def abs_path(path: Path | str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def load_json(path: Path | str) -> Any:
    with abs_path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with abs_path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, title: str, body: str) -> None:
    (OUT_DIR / name).write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def sha256_file(path: Path | str) -> str | None:
    p = abs_path(path)
    if not p.exists() or not p.is_file():
        return None
    digest = hashlib.sha256()
    with p.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_normalized(path: Path | str) -> str | None:
    p = abs_path(path)
    if not p.exists() or not p.is_file():
        return None
    data = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def hash_record(path: Path | str, role: str) -> dict[str, Any]:
    p = abs_path(path)
    return {
        "path": rel(p),
        "role": role,
        "exists": p.exists(),
        "size_bytes": p.stat().st_size if p.exists() and p.is_file() else None,
        "sha256": sha256_file(p) if p.exists() and p.is_file() else None,
        "git_last_commit": git_last_commit(rel(p)) if p.exists() and p.is_file() else None,
    }


def git_output(args: list[str]) -> str:
    try:
        proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    except Exception:
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def git_last_commit(path: str) -> str | None:
    value = git_output(["git", "log", "-1", "--format=%H", "--", path])
    return value or None


def parse_kind(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {"path": rel(path), "parse_status": "NOT_PARSED"}
    try:
        if path.suffix == ".json":
            load_json(path)
            record["parse_status"] = "PASS_JSON"
        elif path.suffix == ".jsonl":
            rows = load_jsonl(path)
            record["parse_status"] = "PASS_JSONL"
            record["row_count"] = len(rows)
        elif path.suffix in {".md", ".py"}:
            path.read_text(encoding="utf-8")
            record["parse_status"] = "PASS_TEXT"
        else:
            record["parse_status"] = "PASS_BYTES"
            path.read_bytes()
    except Exception as exc:
        record["parse_status"] = "FAIL"
        record["error"] = str(exc)
    return record


def all_count_packet_artifacts() -> list[Path]:
    return sorted(abs_path(COUNT_DIR).iterdir(), key=lambda p: p.name)


def rows_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["packet_row_id"]: row for row in rows}


def counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def rows_to_counter(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {row["categorical_lifecycle_label"]: row["count"] for row in rows}


def flag_issues(rows: list[dict[str, Any]], expected_family: str | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        row_id = row.get("packet_row_id")
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append({"packet_row_id": row_id, "issue": "promotion_verdict_not_preserved"})
        if row.get("validation_safe") is not False:
            issues.append({"packet_row_id": row_id, "issue": "validation_safe_not_false"})
        if row.get("outcome_review_opened") is not False:
            issues.append({"packet_row_id": row_id, "issue": "outcome_review_opened_not_false"})
        if row.get("live_effect") is not False:
            issues.append({"packet_row_id": row_id, "issue": "live_effect_not_false"})
        if expected_family and row.get("v3_terminal_family") != expected_family:
            issues.append({"packet_row_id": row_id, "issue": "unexpected_v3_terminal_family", "value": row.get("v3_terminal_family")})
    return issues


def analyze() -> dict[str, Any]:
    accepted_rows = load_jsonl(COUNT_DIR / f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl")
    exclusion_rows = load_jsonl(COUNT_DIR / f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl")
    count_ledger = load_json(COUNT_DIR / f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.json")
    duplicate_diag = load_json(COUNT_DIR / f"NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_{DATE}.json")
    reject_overlap_packet = load_json(COUNT_DIR / f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.json")
    count_source_audit = load_json(COUNT_DIR / f"NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    count_saturation = load_json(COUNT_DIR / f"NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_{DATE}.json")
    count_completion = load_json(COUNT_DIR / f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.json")

    eligibility_rows = load_jsonl(RESULT_CONTRACT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl")
    contract_exclusions = load_jsonl(RESULT_CONTRACT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl")
    frozen_rulebook = load_json(RESULT_CONTRACT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json")
    g12_decision = load_json(G12_RESULT_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json")
    g12_duplicate = load_json(G12_RESULT_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json")
    g12_source = load_json(G12_RESULT_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.json")

    accepted_ids = set(rows_by_id(accepted_rows))
    eligibility_ids = set(rows_by_id(eligibility_rows))
    exclusion_ids = set(rows_by_id(exclusion_rows))
    contract_exclusion_ids = set(rows_by_id(contract_exclusions))

    exclusion_family_counts = Counter(row.get("v3_terminal_family") for row in exclusion_rows)
    universe_counts = {
        "accepted": len(accepted_rows),
        "source_control": exclusion_family_counts.get("source_control", 0),
        "source_impossible": exclusion_family_counts.get("source_impossible", 0),
        "reject": exclusion_family_counts.get("reject", 0),
        "blocked": exclusion_family_counts.get("blocked", 0),
    }
    universe_total = sum(universe_counts.values())

    row_label_counts = Counter(row["categorical_lifecycle_label"] for row in accepted_rows)
    duplicate_key_members = [row for row in accepted_rows if row.get("nofill_duplicate_key_count_member") is True]
    duplicate_group_members = [row for row in accepted_rows if row.get("duplicate_group_id_count_member") is True]
    duplicate_key_label_counts = Counter(row["categorical_lifecycle_label"] for row in duplicate_key_members)
    duplicate_group_label_counts = Counter(row["categorical_lifecycle_label"] for row in duplicate_group_members)

    accepted_keys = {row["nofill_duplicate_key"] for row in accepted_rows}
    accepted_groups = {row["duplicate_group_id"] for row in accepted_rows}
    accepted_unique_keys = len(accepted_keys)
    accepted_unique_groups = len(accepted_groups)

    rows_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted_rows:
        rows_by_key[row["nofill_duplicate_key"]].append(row)
        rows_by_group[row["duplicate_group_id"]].append(row)

    label_conflicts = []
    geometry_conflicts = []
    ordering_blockers = []
    denominator_conflicts = []
    for key, rows in rows_by_key.items():
        labels = {row.get("categorical_lifecycle_label") for row in rows}
        if len(labels) != 1:
            label_conflicts.append({"nofill_duplicate_key": key, "labels": sorted(labels)})
        geometry = {
            (
                row.get("symbol"),
                row.get("session"),
                row.get("side"),
                row.get("source_lane"),
                row.get("source_packet_id"),
                row.get("duplicate_group_id"),
            )
            for row in rows
        }
        if len(geometry) != 1:
            geometry_conflicts.append({"nofill_duplicate_key": key, "geometry_values": [list(item) for item in sorted(geometry)]})
        member_count = sum(1 for row in rows if row.get("nofill_duplicate_key_count_member") is True)
        if member_count != 1:
            denominator_conflicts.append({"nofill_duplicate_key": key, "duplicate_key_count_member_rows": member_count})
        if any(
            row.get("v3_terminal_family") != "accepted"
            or row.get("label_class") != "input_only_categorical"
            or row.get("source_safe_input_only") is not True
            or not row.get("categorical_lifecycle_label")
            for row in rows
        ):
            ordering_blockers.append({"nofill_duplicate_key": key})

    group_denominator_conflicts = []
    for group, rows in rows_by_group.items():
        member_count = sum(1 for row in rows if row.get("duplicate_group_id_count_member") is True)
        if member_count != 1:
            group_denominator_conflicts.append({"duplicate_group_id": group, "duplicate_group_count_member_rows": member_count})

    reject_rows = [row for row in exclusion_rows if row.get("v3_terminal_family") == "reject"]
    source_control_rows = [row for row in exclusion_rows if row.get("v3_terminal_family") == "source_control"]
    source_impossible_rows = [row for row in exclusion_rows if row.get("v3_terminal_family") == "source_impossible"]
    reject_key_overlap = sorted(row["packet_row_id"] for row in reject_rows if row.get("nofill_duplicate_key") in accepted_keys)
    reject_group_overlap = sorted(row["packet_row_id"] for row in reject_rows if row.get("duplicate_group_id") in accepted_groups)
    source_control_key_overlap = sorted(row["packet_row_id"] for row in source_control_rows if row.get("nofill_duplicate_key") in accepted_keys)
    source_impossible_key_overlap = sorted(row["packet_row_id"] for row in source_impossible_rows if row.get("nofill_duplicate_key") in accepted_keys)
    exclusion_denominator_violations = [
        row["packet_row_id"]
        for row in exclusion_rows
        if row.get("row_level_count_member") or row.get("nofill_duplicate_key_count_member") or row.get("duplicate_group_id_count_member")
    ]

    accepted_flag_issues = flag_issues(accepted_rows, "accepted")
    for row in accepted_rows:
        if row.get("source_safe_input_only") is not True:
            accepted_flag_issues.append({"packet_row_id": row.get("packet_row_id"), "issue": "source_safe_input_only_not_true"})
        if row.get("label_class") != "input_only_categorical":
            accepted_flag_issues.append({"packet_row_id": row.get("packet_row_id"), "issue": "label_class_not_input_only_categorical"})
        if row.get("row_level_count_member") is not True:
            accepted_flag_issues.append({"packet_row_id": row.get("packet_row_id"), "issue": "row_level_count_member_not_true"})
    exclusion_flag_issues = flag_issues(exclusion_rows, None)

    forbidden_key_hits = forbidden_key_scan(accepted_rows + exclusion_rows)
    source_recheck = recompute_source_schema_recheck(count_source_audit)
    count_lane_hash_check = recompute_count_lane_hashes(count_source_audit)

    packet_artifact_inventory = []
    packet_artifact_parse = []
    for artifact in all_count_packet_artifacts():
        packet_artifact_inventory.append(hash_record(artifact, "count_packet_artifact_read_for_g12_audit"))
        packet_artifact_parse.append(parse_kind(artifact))

    issues: list[str] = []
    expected_universe = {"accepted": 225, "source_control": 4, "source_impossible": 4, "reject": 65, "blocked": 0}
    if universe_counts != expected_universe or universe_total != 298:
        issues.append("universe_equation_mismatch")
    if accepted_ids != eligibility_ids:
        issues.append("accepted_row_ids_do_not_match_frozen_contract_eligibility")
    if exclusion_ids != contract_exclusion_ids:
        issues.append("exclusion_row_ids_do_not_match_frozen_contract_exclusions")
    if {row["packet_row_id"] for row in source_control_rows} != SOURCE_CONTROL_ROWS:
        issues.append("source_control_row_set_mismatch")
    if {row["packet_row_id"] for row in source_impossible_rows} != SOURCE_IMPOSSIBLE_ROWS:
        issues.append("source_impossible_row_set_mismatch")
    if len(reject_rows) != 65:
        issues.append("reject_row_count_mismatch")
    if accepted_unique_keys != 182 or accepted_unique_groups != 139:
        issues.append("duplicate_denominator_count_mismatch")
    if counter_dict(row_label_counts) != EXPECTED_LABEL_COUNTS_ROW_LEVEL:
        issues.append("row_level_label_count_mismatch")
    if counter_dict(duplicate_key_label_counts) != EXPECTED_LABEL_COUNTS_DUPLICATE_KEY:
        issues.append("duplicate_key_label_count_mismatch")
    if counter_dict(duplicate_group_label_counts) != EXPECTED_LABEL_COUNTS_DUPLICATE_GROUP:
        issues.append("duplicate_group_label_count_mismatch")
    if accepted_flag_issues or exclusion_flag_issues:
        issues.append("safe_flag_or_family_issue")
    if label_conflicts or geometry_conflicts or ordering_blockers or denominator_conflicts or group_denominator_conflicts:
        issues.append("duplicate_conflict_issue")
    if exclusion_denominator_violations:
        issues.append("nonaccepted_denominator_leak")
    if len(reject_key_overlap) != 47 or len(reject_group_overlap) != 47:
        issues.append("reject_overlap_count_mismatch")
    if source_control_key_overlap or source_impossible_key_overlap:
        issues.append("source_control_or_impossible_overlap_with_accepted")
    if source_recheck["strict_failure_count"] != 0 or source_recheck["missing_record_count"] != 0:
        issues.append("source_schema_hash_failure")
    if count_lane_hash_check["mismatch_count"] != 0 or count_lane_hash_check["missing_count"] != 0:
        issues.append("count_lane_source_hash_failure")
    if forbidden_key_hits:
        issues.append("forbidden_row_key_or_value_hit")
    if any(item["parse_status"] == "FAIL" for item in packet_artifact_parse):
        issues.append("count_packet_artifact_parse_failure")
    if count_completion.get("can_mark_goal_complete") is not True:
        issues.append("upstream_count_completion_not_marked_complete")

    return {
        "accepted_rows": accepted_rows,
        "exclusion_rows": exclusion_rows,
        "eligibility_rows": eligibility_rows,
        "contract_exclusions": contract_exclusions,
        "count_ledger": count_ledger,
        "duplicate_diag": duplicate_diag,
        "reject_overlap_packet": reject_overlap_packet,
        "count_source_audit": count_source_audit,
        "count_saturation": count_saturation,
        "count_completion": count_completion,
        "frozen_rulebook": frozen_rulebook,
        "g12_decision": g12_decision,
        "g12_duplicate": g12_duplicate,
        "g12_source": g12_source,
        "packet_artifact_inventory": packet_artifact_inventory,
        "packet_artifact_parse": packet_artifact_parse,
        "universe_counts": universe_counts,
        "universe_total": universe_total,
        "row_label_counts": counter_dict(row_label_counts),
        "duplicate_key_label_counts": counter_dict(duplicate_key_label_counts),
        "duplicate_group_label_counts": counter_dict(duplicate_group_label_counts),
        "accepted_unique_keys": accepted_unique_keys,
        "accepted_unique_groups": accepted_unique_groups,
        "accepted_ids_match_contract": accepted_ids == eligibility_ids,
        "exclusion_ids_match_contract": exclusion_ids == contract_exclusion_ids,
        "source_control_rows": sorted(row["packet_row_id"] for row in source_control_rows),
        "source_impossible_rows": sorted(row["packet_row_id"] for row in source_impossible_rows),
        "reject_row_count": len(reject_rows),
        "accepted_flag_issues": accepted_flag_issues,
        "exclusion_flag_issues": exclusion_flag_issues,
        "label_conflicts": label_conflicts,
        "geometry_conflicts": geometry_conflicts,
        "ordering_blockers": ordering_blockers,
        "denominator_conflicts": denominator_conflicts,
        "group_denominator_conflicts": group_denominator_conflicts,
        "reject_key_overlap": reject_key_overlap,
        "reject_group_overlap": reject_group_overlap,
        "source_control_key_overlap": source_control_key_overlap,
        "source_impossible_key_overlap": source_impossible_key_overlap,
        "exclusion_denominator_violations": exclusion_denominator_violations,
        "source_recheck": source_recheck,
        "count_lane_hash_check": count_lane_hash_check,
        "forbidden_key_hits": forbidden_key_hits,
        "issues": issues,
    }


def forbidden_key_scan(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    forbidden_keys = {
        "actual_r",
        "broker_actual_r",
        "account_history",
        "deal_ticket",
        "order_ticket",
        "position_ticket",
        "mt5_history",
        "hidden_label",
        "win_rate",
        "expectancy",
        "profit_factor",
        "pnl",
        "api_key",
        "password",
        "secret",
        "credential",
    }
    forbidden_value_terms = {
        "broker_actual_r",
        "account_history",
        "deal_ticket",
        "order_ticket",
        "position_ticket",
        "hidden_label",
        "win_rate",
        "expectancy",
        "profit_factor",
        "api_key",
        "password",
    }
    allowed_keys = {"promotion_verdict", "validation_safe", "outcome_review_opened", "live_effect"}
    hits: list[dict[str, Any]] = []

    def walk(value: Any, row_id: str, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                if lowered in forbidden_keys and lowered not in allowed_keys:
                    hits.append({"packet_row_id": row_id, "path": f"{path}.{key}".strip("."), "kind": "forbidden_key"})
                walk(child, row_id, f"{path}.{key}".strip("."))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, row_id, f"{path}[{index}]")
        elif isinstance(value, str):
            lowered_value = value.lower()
            for term in forbidden_value_terms:
                if term in lowered_value:
                    hits.append({"packet_row_id": row_id, "path": path, "kind": "forbidden_value_term", "term": term})

    for row in rows:
        walk(row, row.get("packet_row_id", "UNKNOWN"), "")
    return hits


def recompute_source_schema_recheck(count_source_audit: dict[str, Any]) -> dict[str, Any]:
    schema = count_source_audit.get("source_schema_recheck", {})
    records = schema.get("records", [])
    strict_failures = []
    missing = []
    line_ending_only = []
    mutable_context = []
    strict_matches = []
    for record in records:
        path = record.get("path")
        expected = record.get("expected_sha256")
        p = abs_path(path) if path else None
        if not p or not p.exists():
            missing.append(record)
            continue
        current = sha256_file(p)
        normalized = sha256_normalized(p)
        if expected is None:
            mutable_context.append({**record, "current_sha256": current, "current_normalized_sha256": normalized})
        elif current == expected:
            strict_matches.append({**record, "current_sha256": current})
        elif normalized == expected:
            line_ending_only.append({**record, "current_sha256": current, "current_normalized_sha256": normalized})
        else:
            strict_failures.append({**record, "current_sha256": current, "current_normalized_sha256": normalized})
    return {
        "record_count": len(records),
        "strict_match_count": len(strict_matches),
        "line_ending_only_mismatch_count": len(line_ending_only),
        "mutable_context_presence_count": len(mutable_context),
        "strict_failure_count": len(strict_failures),
        "strict_failures": strict_failures,
        "missing_record_count": len(missing),
        "missing": missing,
    }


def recompute_count_lane_hashes(count_source_audit: dict[str, Any]) -> dict[str, Any]:
    records = count_source_audit.get("count_lane_source_records", [])
    mismatches = []
    line_ending_only = []
    missing = []
    checked = []
    for record in records:
        path = record.get("path")
        expected = record.get("sha256")
        p = abs_path(path) if path else None
        if not p or not p.exists():
            missing.append(record)
            continue
        current = sha256_file(p)
        normalized = sha256_normalized(p)
        checked.append({"path": path, "expected_sha256": expected, "current_sha256": current})
        if expected and current != expected and normalized == expected:
            line_ending_only.append(
                {"path": path, "expected_sha256": expected, "current_sha256": current, "current_normalized_sha256": normalized}
            )
        elif expected and current != expected:
            mismatches.append({"path": path, "expected_sha256": expected, "current_sha256": current})
    return {
        "record_count": len(records),
        "checked_count": len(checked),
        "line_ending_only_mismatch_count": len(line_ending_only),
        "line_ending_only_mismatches": line_ending_only,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "missing_count": len(missing),
        "missing": missing,
    }


def status_from_issues(issues: list[str]) -> str:
    return "PASS" if not issues else "FAIL"


def build_payloads() -> dict[str, dict[str, Any]]:
    analysis = analyze()
    generated_at = now_utc()
    starting_head = git_output(["git", "rev-parse", "HEAD"])
    latest_handoff = git_output(["powershell", "-NoProfile", "-Command", "Get-ChildItem .context\\02_session_handoffs | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty Name"])

    context_inputs = [
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/local_heavy_data_inventory.md",
        ".context/00_core/quick_reference_card.md",
        f".context/02_session_handoffs/{latest_handoff}" if latest_handoff else ".context/02_session_handoffs/",
        str(RESULT_CONTRACT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"),
        str(G12_RESULT_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json"),
        str(COUNT_DIR),
    ]
    context_anchor = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_CONTEXT_ANCHOR",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        "starting_head": starting_head,
        "latest_handoff_read": latest_handoff,
        "controlling_prompt": rel(OUT_DIR / f"G12_NOFILL_CAT_V3_COUNT_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md"),
        "audit_scope": "independent_g12_post_count_control_audit_only",
        "required_context_inputs_read_and_hashed": [hash_record(path, "required_context_or_upstream_input") for path in context_inputs],
        "count_packet_artifacts_read_and_hashed": analysis["packet_artifact_inventory"],
        "count_packet_artifact_parse_results": analysis["packet_artifact_parse"],
        "hard_boundaries_preserved": [
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "no outcome/R/win-rate/expectancy/DSR/PBO performance scoring",
            "no broker/account/order/deal/position/hidden/live labels",
            "no paid/API/Databento, registry, prompts, src trading logic, risk, execution, permissions, safety, selector, canary, credential, remote, or order behavior changes",
        ],
    }

    recomputation_issues = [
        issue
        for issue in analysis["issues"]
        if issue
        in {
            "universe_equation_mismatch",
            "accepted_row_ids_do_not_match_frozen_contract_eligibility",
            "exclusion_row_ids_do_not_match_frozen_contract_exclusions",
            "source_control_row_set_mismatch",
            "source_impossible_row_set_mismatch",
            "reject_row_count_mismatch",
            "duplicate_denominator_count_mismatch",
            "row_level_label_count_mismatch",
            "duplicate_key_label_count_mismatch",
            "duplicate_group_label_count_mismatch",
            "safe_flag_or_family_issue",
            "duplicate_conflict_issue",
            "nonaccepted_denominator_leak",
        }
    ]
    recomputation = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "status": status_from_issues(recomputation_issues),
        "issues": recomputation_issues,
        "universe_equation_recomputed": {
            "text": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
            "total": analysis["universe_total"],
            "terminal_family_counts": analysis["universe_counts"],
        },
        "contract_alignment": {
            "accepted_input_rows": len(analysis["accepted_rows"]),
            "frozen_contract_eligibility_rows": len(analysis["eligibility_rows"]),
            "accepted_ids_match_frozen_contract": analysis["accepted_ids_match_contract"],
            "exclusion_rows": len(analysis["exclusion_rows"]),
            "frozen_contract_exclusion_rows": len(analysis["contract_exclusions"]),
            "exclusion_ids_match_frozen_contract": analysis["exclusion_ids_match_contract"],
        },
        "mandatory_exclusions_recomputed": {
            "source_control_rows": analysis["source_control_rows"],
            "source_impossible_rows": analysis["source_impossible_rows"],
            "reject_row_count": analysis["reject_row_count"],
            "exclusion_denominator_violations": analysis["exclusion_denominator_violations"],
        },
        "accepted_safe_flag_issues": analysis["accepted_flag_issues"],
        "exclusion_safe_flag_issues": analysis["exclusion_flag_issues"],
        "duplicate_denominators_recomputed": {
            "row_level_count": len(analysis["accepted_rows"]),
            "unique_nofill_duplicate_key_count": analysis["accepted_unique_keys"],
            "unique_duplicate_group_id_count": analysis["accepted_unique_groups"],
            "row_level_label_counts": analysis["row_label_counts"],
            "primary_nofill_duplicate_key_label_counts": analysis["duplicate_key_label_counts"],
            "secondary_duplicate_group_id_label_counts": analysis["duplicate_group_label_counts"],
        },
        "duplicate_conflicts_recomputed": {
            "accepted_duplicate_key_label_conflict_count": len(analysis["label_conflicts"]),
            "accepted_duplicate_key_source_geometry_conflict_count": len(analysis["geometry_conflicts"]),
            "accepted_duplicate_key_source_ordering_blocker_count": len(analysis["ordering_blockers"]),
            "accepted_duplicate_key_denominator_conflict_count": len(analysis["denominator_conflicts"]),
            "accepted_duplicate_group_denominator_conflict_count": len(analysis["group_denominator_conflicts"]),
            "label_conflicts": analysis["label_conflicts"],
            "source_geometry_conflicts": analysis["geometry_conflicts"],
            "source_ordering_blockers": analysis["ordering_blockers"],
            "denominator_conflicts": analysis["denominator_conflicts"],
            "group_denominator_conflicts": analysis["group_denominator_conflicts"],
        },
        "packet_claim_cross_checks": {
            "count_ledger_row_level_counts": rows_to_counter(analysis["count_ledger"].get("row_level_label_count_rows", [])),
            "count_ledger_primary_duplicate_key_counts": rows_to_counter(analysis["count_ledger"].get("primary_duplicate_key_label_count_rows", [])),
            "count_ledger_secondary_duplicate_group_counts": rows_to_counter(analysis["count_ledger"].get("secondary_duplicate_group_label_count_rows", [])),
            "duplicate_diag_conflict_audit": analysis["duplicate_diag"].get("conflict_audit", {}),
            "g12_result_contract_decision": analysis["g12_decision"].get("overall_decision"),
        },
    }

    reject_issues = [
        issue
        for issue in analysis["issues"]
        if issue
        in {
            "reject_overlap_count_mismatch",
            "source_control_or_impossible_overlap_with_accepted",
            "nonaccepted_denominator_leak",
        }
    ]
    reject_overlap = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "status": status_from_issues(reject_issues),
        "issues": reject_issues,
        "accepted_filter_applied_before_any_count": True,
        "reject_row_count": analysis["reject_row_count"],
        "reject_key_overlap_with_accepted_count": len(analysis["reject_key_overlap"]),
        "reject_group_overlap_with_accepted_count": len(analysis["reject_group_overlap"]),
        "reject_overlap_packet_row_ids": analysis["reject_key_overlap"],
        "denominator_effect_after_accepted_first_filter": {
            "row_level_count_delta_from_rejects": 0,
            "nofill_duplicate_key_count_delta_from_rejects": 0,
            "duplicate_group_id_count_delta_from_rejects": 0,
            "reason": "Accepted rows are filtered before row-level counts, duplicate-key collapse, and duplicate-group concentration.",
        },
        "source_control_key_overlap_with_accepted": analysis["source_control_key_overlap"],
        "source_impossible_key_overlap_with_accepted": analysis["source_impossible_key_overlap"],
        "packet_claim_cross_check": {
            "packet_reject_key_overlap_count": analysis["reject_overlap_packet"].get("reject_key_overlap_with_accepted_count"),
            "packet_reject_group_overlap_count": analysis["reject_overlap_packet"].get("reject_group_overlap_with_accepted_count"),
            "packet_denominator_effect": analysis["reject_overlap_packet"].get("denominator_effect"),
        },
    }

    label_issues = label_family_issues(analysis)
    label_review = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "status": status_from_issues(label_issues),
        "issues": label_issues,
        "allowed_label_families": label_interpretations(),
        "observed_row_level_label_counts": analysis["row_label_counts"],
        "interpretation_freeze": "All labels are input/control categorical states only. They are not outcome, R, win/loss, expectancy, edge, validation, promotion, live, broker, account, order, deal, position, hidden-label, or paid-data labels.",
        "labels_with_performance_language": [],
        "opening_drive_interpretation": "source projection ready/no-result-label only; it is source readiness inventory, not a performance result.",
        "fill_path_interpretation": "event-order category from approved source/control inputs only; it is not a win, loss, or R outcome.",
        "pending_horizon_interpretation": "source-corrected no-entry-through-pending-horizon category only; it is not a broker cancel/result label.",
    }

    source_issues = [
        issue
        for issue in analysis["issues"]
        if issue
        in {
            "source_schema_hash_failure",
            "count_lane_source_hash_failure",
            "forbidden_row_key_or_value_hit",
            "count_packet_artifact_parse_failure",
            "upstream_count_completion_not_marked_complete",
        }
    ]
    source_review = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "status": status_from_issues(source_issues),
        "issues": source_issues,
        "source_schema_recheck_recomputed": analysis["source_recheck"],
        "count_lane_source_hash_recheck": analysis["count_lane_hash_check"],
        "count_packet_artifact_inventory": analysis["packet_artifact_inventory"],
        "count_packet_artifact_parse_results": analysis["packet_artifact_parse"],
        "row_artifact_forbidden_key_or_value_hits": analysis["forbidden_key_hits"],
        "upstream_count_packet_verifier_behavior_from_committed_completion_audit": {
            "completion_status": analysis["count_completion"].get("completion_status"),
            "can_mark_goal_complete": analysis["count_completion"].get("can_mark_goal_complete"),
            "verification_result_keys": sorted((analysis["count_completion"].get("verification_results") or {}).keys()),
            "artifact_commit_check_status": (analysis["count_completion"].get("verification_results") or {}).get("artifact_commit_check", {}).get("status"),
            "focused_pytest_status": (analysis["count_completion"].get("verification_results") or {}).get("focused_pytest", {}).get("status"),
            "live_surface_diff_status": (analysis["count_completion"].get("verification_results") or {}).get("live_surface_diff", {}).get("status"),
        },
        "upstream_g12_result_contract_source_audit_status": analysis["g12_source"].get("status"),
        "known_line_ending_mismatch_policy": "The single controlling-prompt line-ending-only mismatch remains accepted only through normalized LF hash match; strict row/source artifact mismatches would block.",
    }

    saturation_items = saturation_answers(analysis, recomputation, reject_overlap, label_review, source_review)
    saturation_issues = [item["question_id"] for item in saturation_items if item["status"] != "PASS"]
    saturation = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_SATURATION_REVIEW",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "status": status_from_issues(saturation_issues),
        "issues": saturation_issues,
        "same_evidence_class_ambiguities_closed_or_routed": not saturation_issues,
        "red_team_questions": saturation_items,
        "forbidden_routes_still_closed": [
            "outcome scoring",
            "R/win-rate/expectancy/DSR/PBO performance",
            "validation or promotion",
            "broker actual-R/account-history/live order/deal/position labels",
            "hidden labels",
            "paid/API/Databento",
            "registry edits",
            "live prompts/src trading logic/risk/execution/permissions/safety/selectors/canaries/MT5 order behavior",
        ],
        "accepted_next_route": "Separate G0 no-fill CAT V3 categorical evidence synthesis/control review only, still with NO_PROMOTION_VERDICT and no validation/promotion/live effect.",
        "block_or_reject_route_if_future_drift": "If any count, source hash, forbidden field, duplicate denominator, or label-family issue appears, route back to the exact count packet/source-control lane instead of G0 synthesis.",
    }

    all_issues = sorted(set(analysis["issues"] + label_issues + saturation_issues))
    if any(issue in all_issues for issue in ("forbidden_row_key_or_value_hit", "count_packet_artifact_parse_failure")):
        decision = REJECT_DECISION
        decision_status = "FAIL_REJECTED"
    elif all_issues:
        decision = BLOCK_DECISION
        decision_status = "FAIL_BLOCKED"
    else:
        decision = ACCEPT_DECISION
        decision_status = "PASS_ACCEPTED"

    decision_ledger = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "overall_decision": decision,
        "decision_status": decision_status,
        "decision_reasons": [
            "Exact universe equation independently recomputed from frozen eligibility/exclusion ledgers and count-packet row artifacts.",
            "Accepted rows, duplicate denominators, exclusions, reject-overlap neutrality, source/no-leak controls, and label interpretation all pass.",
            "No outcome scoring, validation, promotion, live-effect, broker/account/order/deal/position, hidden-label, paid/API/Databento, registry, prompt, src trading logic, risk, execution, permissions, safety, selector, canary, credential, remote, or order-behavior lane is opened.",
        ]
        if decision == ACCEPT_DECISION
        else all_issues,
        "issues": all_issues,
        "verified_starting_facts": {
            "starting_head": starting_head,
            "packet_commit_head_when_audit_started": starting_head,
            "universe_equation": recomputation["universe_equation_recomputed"],
            "accepted_input_rows": len(analysis["accepted_rows"]),
            "primary_unique_nofill_duplicate_keys": analysis["accepted_unique_keys"],
            "secondary_unique_duplicate_group_ids": analysis["accepted_unique_groups"],
            "source_control_rows": analysis["source_control_rows"],
            "source_impossible_rows": analysis["source_impossible_rows"],
            "reject_rows": analysis["reject_row_count"],
            "reject_overlap_rows": len(analysis["reject_key_overlap"]),
            "source_hash_strict_failures": analysis["source_recheck"]["strict_failure_count"],
            "source_hash_missing_records": analysis["source_recheck"]["missing_record_count"],
            "forbidden_row_key_or_value_hits": len(analysis["forbidden_key_hits"]),
        },
        "next_route": saturation["accepted_next_route"] if decision == ACCEPT_DECISION else saturation["block_or_reject_route_if_future_drift"],
    }

    completion = {
        **BASE_FLAGS,
        "artifact_family": "G12_NOFILL_CAT_V3_COUNT_AUDIT_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "completion_status": "PENDING_VERIFIER_AND_COMMIT",
        "can_mark_goal_complete": False,
        "objective_restatement": "Run an independent G12 post-count audit of NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET as quarantined categorical input/control evidence only, recomputing the universe, exclusions, duplicate denominators, source/no-leak controls, reject-overlap neutralization, label-family interpretation, verifier behavior, tests, and committed scope before accepting, blocking, or rejecting.",
        "prompt_to_artifact_checklist": completion_checklist(),
        "missing_incomplete_or_weak_requirements": ["Verifier and scoped commit have not finalized this audit yet."],
        "verification_results": {},
    }

    return {
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_CONTEXT_ANCHOR_{DATE}.json": context_anchor,
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_{DATE}.json": decision_ledger,
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json": recomputation,
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER_{DATE}.json": reject_overlap,
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_{DATE}.json": label_review,
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_{DATE}.json": source_review,
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SATURATION_REVIEW_{DATE}.json": saturation,
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_COMPLETION_AUDIT_{DATE}.json": completion,
    }


def label_interpretations() -> dict[str, str]:
    return {
        "canonical_duplicate_geometry_source_ready_no_label_assigned": "canonical duplicate/source geometry is countable as source-ready categorical inventory only",
        "fill_path_entry_before_protective_level_before_terminal_area": "input event-order category only",
        "fill_path_entry_before_protective_level_no_terminal_observed": "input event-order category only",
        "fill_path_entry_before_terminal_area_before_protective_level": "input event-order category only",
        "nofill_terminal_before_entry": "categorical no-fill terminal-before-entry state only",
        "opening_drive_source_projection_ready_no_result_label": "opening-drive source projection readiness category only",
        "source_corrected_no_entry_through_pending_horizon": "source-corrected no-entry-through-pending-horizon category only",
    }


def label_family_issues(analysis: dict[str, Any]) -> list[str]:
    observed = set(analysis["row_label_counts"])
    allowed = set(label_interpretations())
    issues: list[str] = []
    if observed != allowed:
        issues.append("observed_label_family_set_mismatch")
    performance_terms = ("win", "loss", "expectancy", "profit", "edge", "promotion", "validation", "live")
    bad_labels = [label for label in observed if any(term in label.lower() for term in performance_terms)]
    if bad_labels:
        issues.append("label_name_contains_performance_or_promotion_language")
    return issues


def saturation_answers(
    analysis: dict[str, Any],
    recomputation: dict[str, Any],
    reject_overlap: dict[str, Any],
    label_review: dict[str, Any],
    source_review: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "question_id": "reject_overlap_laundering",
            "question": "Could reject rows with shared duplicate keys influence counts, effective-N, or concentration?",
            "answer": "No. 47 reject rows overlap accepted keys/groups, but all reject rows have zero denominator membership and the audit recomputes counts from accepted rows only.",
            "evidence": {
                "reject_key_overlap_count": reject_overlap["reject_key_overlap_with_accepted_count"],
                "denominator_effect": reject_overlap["denominator_effect_after_accepted_first_filter"],
            },
            "status": "PASS" if reject_overlap["status"] == "PASS" else "FAIL",
        },
        {
            "question_id": "nonaccepted_denominator_leak",
            "question": "Did source-control, source-impossible, or reject rows leak into denominators?",
            "answer": "No. Exclusion IDs match the frozen contract, mandatory source-control/source-impossible rows are present, and every exclusion row has row/key/group membership false.",
            "evidence": recomputation["mandatory_exclusions_recomputed"],
            "status": "PASS" if not analysis["exclusion_denominator_violations"] else "FAIL",
        },
        {
            "question_id": "denominator_separation",
            "question": "Are row-level, duplicate-key, and duplicate-group counts separated?",
            "answer": "Yes. The audit separately recomputes 225 row-level rows, 182 primary nofill_duplicate_key members, and 139 secondary duplicate_group_id members with separate label count tables.",
            "evidence": recomputation["duplicate_denominators_recomputed"],
            "status": "PASS" if recomputation["status"] == "PASS" else "FAIL",
        },
        {
            "question_id": "label_family_interpretation",
            "question": "Does any label imply performance, validation, promotion, or live usability?",
            "answer": "No. Every observed label is frozen as categorical input/control only; opening-drive, fill/path, and pending-horizon categories are not result labels.",
            "evidence": label_review["interpretation_freeze"],
            "status": "PASS" if label_review["status"] == "PASS" else "FAIL",
        },
        {
            "question_id": "source_hash_noleak_coverage",
            "question": "Do source hash/no-leak checks cover upstream contract and count artifacts?",
            "answer": "Yes. The audit rechecks upstream source schema hashes, count-lane source records, row-artifact forbidden keys/values, and hashes/parses every count-packet artifact.",
            "evidence": {
                "source_schema_recheck": source_review["source_schema_recheck_recomputed"],
                "count_lane_hash_recheck": source_review["count_lane_source_hash_recheck"],
                "count_packet_artifact_count": len(source_review["count_packet_artifact_inventory"]),
            },
            "status": "PASS" if source_review["status"] == "PASS" else "FAIL",
        },
        {
            "question_id": "verifier_behavior",
            "question": "Does verifier behavior distinguish committed scope from workspace dirt?",
            "answer": "The upstream count-packet completion audit records committed artifact checking, focused pytest, and live-surface diff status. This G12 audit adds its own committed artifact and final git-show scope checks.",
            "evidence": source_review["upstream_count_packet_verifier_behavior_from_committed_completion_audit"],
            "status": "PASS"
            if source_review["upstream_count_packet_verifier_behavior_from_committed_completion_audit"].get("can_mark_goal_complete") is True
            else "FAIL",
        },
        {
            "question_id": "next_route",
            "question": "If accepted, what exact next route is allowed?",
            "answer": "Only a separate G0 no-fill CAT V3 categorical evidence synthesis/control review. Validation, promotion, scoring, registry edits, and live behavior remain closed.",
            "evidence": "G0 synthesis/control review only; no validation/promotion/live effect.",
            "status": "PASS",
        },
    ]


def completion_checklist() -> list[dict[str, Any]]:
    requirements = [
        "GTOS preflight completed and starting HEAD recorded",
        "LIVE_STATE, research state/doctrine, goal discipline, local-heavy inventory, latest handoff, frozen contract, G12 contract audit, and every count-packet artifact read",
        "Exact universe equation and accepted/excluded counts independently recomputed",
        "Duplicate denominators and duplicate conflicts independently recomputed",
        "Reject-overlap neutralization independently recomputed",
        "Source hash/no-leak and forbidden row-field controls independently checked",
        "Label-family interpretation reviewed as input/control only",
        "Saturation review answered required red-team questions",
        "Explicit accept/block/reject decision and exact next route emitted",
        "Builder, verifier, py_compile, focused pytest, committed-diff scope, and final git-show scope checks pass",
        "Scoped artifacts and required context refresh committed",
    ]
    return [{"requirement": item, "status": "PENDING_VERIFIER", "evidence": "pending"} for item in requirements]


def write_markdown(payloads: dict[str, dict[str, Any]]) -> None:
    decision = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_{DATE}.json"]
    recomputation = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json"]
    reject = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER_{DATE}.json"]
    label = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_{DATE}.json"]
    source = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_{DATE}.json"]
    saturation = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SATURATION_REVIEW_{DATE}.json"]
    completion = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_COMPLETION_AUDIT_{DATE}.json"]
    context = payloads[f"G12_NOFILL_CAT_V3_COUNT_AUDIT_CONTEXT_ANCHOR_{DATE}.json"]

    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_CONTEXT_ANCHOR_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Context Anchor",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Starting HEAD: `{context['starting_head']}`",
                f"Audit scope: `{context['audit_scope']}`",
                f"Count-packet artifacts read and hashed: `{len(context['count_packet_artifacts_read_and_hashed'])}`",
                "",
                "Hard boundaries: no outcomes, R, win rate, expectancy, validation, promotion, broker/account/live/order labels, paid/API, registry, or live behavior.",
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Decision Ledger",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Decision: `{decision['overall_decision']}`",
                f"Decision status: `{decision['decision_status']}`",
                f"Next route: {decision['next_route']}",
                "",
                "Reasons:",
                *[f"- {reason}" for reason in decision["decision_reasons"]],
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Recomputations",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{recomputation['status']}`",
                f"Universe: `{recomputation['universe_equation_recomputed']['text']}`",
                f"Accepted rows: `{recomputation['contract_alignment']['accepted_input_rows']}`",
                f"Primary duplicate keys: `{recomputation['duplicate_denominators_recomputed']['unique_nofill_duplicate_key_count']}`",
                f"Secondary duplicate groups: `{recomputation['duplicate_denominators_recomputed']['unique_duplicate_group_id_count']}`",
                f"Duplicate label conflicts: `{recomputation['duplicate_conflicts_recomputed']['accepted_duplicate_key_label_conflict_count']}`",
                f"Duplicate geometry conflicts: `{recomputation['duplicate_conflicts_recomputed']['accepted_duplicate_key_source_geometry_conflict_count']}`",
                f"Duplicate ordering blockers: `{recomputation['duplicate_conflicts_recomputed']['accepted_duplicate_key_source_ordering_blocker_count']}`",
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Reject Overlap Ledger",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{reject['status']}`",
                f"Reject overlap rows: `{reject['reject_key_overlap_with_accepted_count']}`",
                "Denominator deltas after accepted-first filtering: row `0`, duplicate key `0`, duplicate group `0`.",
                "Reject overlaps are documented only; they cannot add to, subtract from, or relabel accepted counts.",
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Label-Family Review",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{label['status']}`",
                label["interpretation_freeze"],
                "",
                "Observed labels:",
                *[f"- `{name}`: {meaning}" for name, meaning in label["allowed_label_families"].items()],
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Source/No-Leak Review",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{source['status']}`",
                f"Source strict failures: `{source['source_schema_recheck_recomputed']['strict_failure_count']}`",
                f"Source missing records: `{source['source_schema_recheck_recomputed']['missing_record_count']}`",
                f"Count-lane hash mismatches: `{source['count_lane_source_hash_recheck']['mismatch_count']}`",
                f"Count packet artifacts hashed: `{len(source['count_packet_artifact_inventory'])}`",
                f"Forbidden row key/value hits: `{len(source['row_artifact_forbidden_key_or_value_hits'])}`",
                f"Upstream verifier completion: `{source['upstream_count_packet_verifier_behavior_from_committed_completion_audit']['completion_status']}`",
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_SATURATION_REVIEW_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Saturation Review",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{saturation['status']}`",
                f"Same-evidence-class ambiguities closed or routed: `{str(saturation['same_evidence_class_ambiguities_closed_or_routed']).lower()}`",
                "",
                "Red-team answers:",
                *[
                    f"- `{item['status']}` `{item['question_id']}`: {item['answer']}"
                    for item in saturation["red_team_questions"]
                ],
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_NEXT_PROMPT_PACK_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Next Prompt Pack",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                "If this G12 audit is accepted, the only allowed next lane is a separate G0 no-fill CAT V3 categorical evidence synthesis/control review.",
                "",
                "Starter message:",
                "",
                "`/goal Run G0_NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_EVIDENCE_SYNTHESIS_CONTROL_REVIEW using the accepted count packet and accepted G12 post-count audit as controlling inputs. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not score outcomes, R, win rate, expectancy, DSR/PBO performance, validation, promotion, broker actual-R, account history, live order/deal/position labels, hidden labels, paid/API/Databento, registry edits, live trading prompts, src trading logic, risk, execution, permissions, safety gates, selectors, MT5 order/account/history surfaces, canaries, credentials, remote pushes, or order behavior.`",
                "",
                "If any future count/source/duplicate/label drift appears, route back to the exact count-packet or source-control lane instead of G0 synthesis.",
            ]
        ),
    )
    write_md(
        f"G12_NOFILL_CAT_V3_COUNT_AUDIT_COMPLETION_AUDIT_{DATE}.md",
        "G12 NOFILL CAT V3 Count Audit Completion Audit",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Completion status: `{completion['completion_status']}`",
                f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`",
                "",
                completion["objective_restatement"],
                "",
                "Checklist:",
                *[f"- `{item['status']}` {item['requirement']}: {item['evidence']}" for item in completion["prompt_to_artifact_checklist"]],
            ]
        ),
    )


def main() -> None:
    payloads = build_payloads()
    for name, payload in payloads.items():
        write_json(name, payload)
    write_markdown(payloads)
    print(json.dumps({"status": "built", "output_dir": rel(OUT_DIR), "json_artifacts": sorted(payloads)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
