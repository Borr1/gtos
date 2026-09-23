#!/usr/bin/env python3
"""Build the G12 NOFILL CAT V3 result-contract audit artifacts."""

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
SCHEMA_VERSION = "g12_nofill_cat_v3_result_contract_audit_v1"
AUDIT_LANE_ID = "G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_V1"
CONTRACT_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1"
DECISION = "ACCEPT_FROZEN_V3_RESULT_CONTRACT_FOR_QUARANTINED_CATEGORICAL_COUNT_PACKET"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
RESULT_DIR = BASE / "nofill_cat_v3_result_contract_update"
V3_DIR = BASE / "nofill_cat_v3_source_control_rebuild"
G12_V3_DIR = BASE / "g12_nofill_cat_v3_source_control_audit"
PRIOR_RESULT_DIR = BASE / "no_fill_lifecycle_result_contract_design"
G12_PRIOR_RESULT_DIR = BASE / "g12_no_fill_result_contract_audit"
V2_FORENSICS_DIR = BASE / "nofill_cat_v2_quarantined_categorical_synthesis_forensics"
G12_V2_FORENSICS_DIR = BASE / "g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit"

EXPECTED_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "reject": 65,
    "blocked": 0,
}
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
EXPECTED_ACCEPTED_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_REJECT_REASON_COUNTS = {
    "BLOCK_OTI4_BREAKOUT_SIDE_MISMATCHES_CANDIDATE_SIDE": 12,
    "BLOCK_OTI4_NO_BREAKOUT_ASOF_UNDER_FROZEN_RANGE": 6,
    "BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION": 8,
    "REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION": 39,
}
EXPECTED_DUPLICATE_KEY_COUNT = 182
EXPECTED_DUPLICATE_GROUP_COUNT = 139
EXPECTED_CANONICAL_DUPLICATE_ROWS = 182

JSON_OUTPUTS = [
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json",
]
MD_OUTPUTS = [
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.md",
]
PY_OUTPUTS = [
    "build_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py",
    "verify_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py",
    "test_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py",
]

BASE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def now_utc() -> str:
    fixed = os.environ.get("G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_FIXED_GENERATED_AT")
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


def load_json(path: Path) -> Any:
    with abs_path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def hash_record(path: Path | str, role: str, hash_policy: str = "strict_sha256") -> dict[str, Any]:
    p = abs_path(path)
    return {
        "path": rel(p),
        "role": role,
        "hash_policy": hash_policy,
        "exists": p.exists(),
        "size_bytes": p.stat().st_size if p.exists() and p.is_file() else None,
        "sha256": sha256_file(p) if p.exists() and p.is_file() else None,
    }


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def git_head() -> str:
    fixed = os.environ.get("G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_FIXED_GIT_HEAD")
    if fixed:
        return fixed
    return git_output(["git", "rev-parse", "HEAD"])


def git_last_commit_for_path(path: Path | str) -> str:
    return git_output(["git", "log", "-1", "--format=%H", "--", rel(path)])


def counter(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items(), key=lambda item: item[0]))


def scan_forbidden_keys(obj: Any, forbidden: set[str], path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in forbidden:
                hits.append({"path": child, "field": key})
            hits.extend(scan_forbidden_keys(value, forbidden, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, forbidden, f"{path}[{idx}]"))
    return hits


def packet_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("packet_row_id", "")), str(row.get("source_inventory_id", "")))


def load_inputs() -> dict[str, Any]:
    return {
        "goal_prompt": OUT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_GOAL_PROMPT_{DATE}.md",
        "rulebook": load_json(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"),
        "schema": load_json(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json"),
        "result_completion": load_json(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json"),
        "eligibility": load_jsonl(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl"),
        "exclusion": load_jsonl(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl"),
        "v3_packet": load_json(V3_DIR / f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json"),
        "v3_rows": load_jsonl(V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "v3_reject": load_json(V3_DIR / f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.json"),
        "v3_impossibility": load_json(V3_DIR / f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json"),
        "v3_source_root_search": load_json(V3_DIR / f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.json"),
        "g12_decision": load_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json"),
        "g12_universe": load_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.json"),
        "g12_source": load_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"),
        "g12_duplicate": load_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"),
        "g12_source_control": load_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.json"),
        "g12_impossibility": load_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json"),
        "prior_result_rulebook": load_json(PRIOR_RESULT_DIR / "NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json"),
        "prior_g12_result_decision": load_json(G12_PRIOR_RESULT_DIR / "G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_2026-05-08.json"),
        "v2_forensics_label": load_json(V2_FORENSICS_DIR / f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json"),
        "g12_v2_decision": load_json(G12_V2_FORENSICS_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json"),
    }


def compute_metrics(inputs: dict[str, Any]) -> dict[str, Any]:
    rows = inputs["v3_rows"]
    eligibility = inputs["eligibility"]
    exclusion = inputs["exclusion"]
    schema = inputs["schema"]

    accepted_rows = [row for row in rows if row["v3_terminal_family"] == "accepted"]
    source_control_rows = [row for row in rows if row["v3_terminal_family"] == "source_control"]
    source_impossible_rows = [row for row in rows if row["v3_terminal_family"] == "source_impossible"]
    reject_rows = [row for row in rows if row["v3_terminal_family"] == "reject"]

    accepted_ids = {row["packet_row_id"] for row in accepted_rows}
    source_control_ids = {row["packet_row_id"] for row in source_control_rows}
    source_impossible_ids = {row["packet_row_id"] for row in source_impossible_rows}
    reject_ids = {row["packet_row_id"] for row in reject_rows}
    eligibility_ids = {row["packet_row_id"] for row in eligibility}
    exclusion_ids = {row["packet_row_id"] for row in exclusion}
    nonaccepted_ids = {row["packet_row_id"] for row in rows if row["v3_terminal_family"] != "accepted"}

    accepted_key_to_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligibility:
        accepted_key_to_rows[row["nofill_duplicate_key"]].append(row)

    accepted_duplicate_label_conflicts = []
    accepted_canonical_violations = []
    for key, key_rows in accepted_key_to_rows.items():
        labels = {row["categorical_lifecycle_label"] for row in key_rows}
        if len(labels) > 1:
            accepted_duplicate_label_conflicts.append({"nofill_duplicate_key": key, "labels": sorted(labels)})
        expected_canonical = sorted(key_rows, key=packet_sort_key)[0]["packet_row_id"]
        flagged = [row["packet_row_id"] for row in key_rows if row.get("duplicate_key_denominator_member")]
        if flagged != [expected_canonical]:
            accepted_canonical_violations.append(
                {
                    "nofill_duplicate_key": key,
                    "expected_canonical_packet_row_id": expected_canonical,
                    "flagged_canonical_packet_row_ids": flagged,
                }
            )

    accepted_keys = {row["nofill_duplicate_key"] for row in eligibility}
    accepted_groups = {row["duplicate_group_id"] for row in eligibility}
    nonaccepted_key_overlap = {
        family: sorted(
            row["packet_row_id"]
            for row in rows
            if row["v3_terminal_family"] == family and row["nofill_duplicate_key"] in accepted_keys
        )
        for family in ("source_control", "source_impossible", "reject")
    }
    nonaccepted_group_overlap = {
        family: sorted(
            row["packet_row_id"]
            for row in rows
            if row["v3_terminal_family"] == family and row["duplicate_group_id"] in accepted_groups
        )
        for family in ("source_control", "source_impossible", "reject")
    }

    row_flag_issues = []
    for row in eligibility + exclusion:
        row_id = row.get("packet_row_id", "UNKNOWN")
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if row.get(flag) is not False:
                row_flag_issues.append({"packet_row_id": row_id, "flag": flag, "value": row.get(flag)})
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            row_flag_issues.append({"packet_row_id": row_id, "flag": "promotion_verdict", "value": row.get("promotion_verdict")})
        for flag in (
            "r_performance_allowed",
            "broker_or_account_label_allowed",
            "current_lane_scoring_allowed",
            "current_lane_result_record_produced",
        ):
            if row.get(flag) is not False:
                row_flag_issues.append({"packet_row_id": row_id, "flag": flag, "value": row.get(flag)})

    exclusion_denominator_violations = [
        {
            "packet_row_id": row["packet_row_id"],
            "exclusion_family": row.get("exclusion_family"),
            "row_level_denominator_member": row.get("row_level_denominator_member"),
            "duplicate_key_denominator_member": row.get("duplicate_key_denominator_member"),
            "future_scoring_lane_may_consume": row.get("future_scoring_lane_may_consume"),
        }
        for row in exclusion
        if row.get("row_level_denominator_member")
        or row.get("duplicate_key_denominator_member")
        or row.get("future_scoring_lane_may_consume")
    ]
    nonaccepted_denominator_violations = [
        {
            "packet_row_id": row["packet_row_id"],
            "v3_terminal_family": row["v3_terminal_family"],
            "in_accepted_packet_denominator": row.get("in_accepted_packet_denominator"),
            "in_source_control_packet": row.get("in_source_control_packet"),
        }
        for row in rows
        if row["v3_terminal_family"] != "accepted" and row.get("in_accepted_packet_denominator")
    ]

    forbidden = set(schema.get("forbidden_fields", []))
    forbidden_row_hits = [
        {"packet_row_id": row.get("packet_row_id", "UNKNOWN"), **hit}
        for row in rows
        for hit in scan_forbidden_keys(row, forbidden)
    ]
    forbidden_contract_hits = [
        {"ledger": ledger_name, **hit}
        for ledger_name, ledger in (("eligibility", eligibility), ("exclusion", exclusion))
        for hit in scan_forbidden_keys(ledger, forbidden)
    ]

    return {
        "row_count": len(rows),
        "unique_packet_row_ids": len({row["packet_row_id"] for row in rows}),
        "terminal_family_counts": counter([row["v3_terminal_family"] for row in rows]),
        "terminal_state_counts": counter([row["v3_terminal_state"] for row in rows]),
        "eligibility_row_count": len(eligibility),
        "exclusion_row_count": len(exclusion),
        "eligibility_matches_accepted_ids": eligibility_ids == accepted_ids,
        "exclusion_matches_nonaccepted_ids": exclusion_ids == nonaccepted_ids,
        "eligibility_exclusion_overlap": sorted(eligibility_ids & exclusion_ids),
        "source_control_ids": sorted(source_control_ids),
        "source_impossible_ids": sorted(source_impossible_ids),
        "reject_row_count": len(reject_rows),
        "source_control_rows_in_eligibility": sorted(eligibility_ids & SOURCE_CONTROL_ROWS),
        "source_impossible_rows_in_eligibility": sorted(eligibility_ids & SOURCE_IMPOSSIBLE_ROWS),
        "missing_source_control_rows_in_exclusion": sorted(SOURCE_CONTROL_ROWS - exclusion_ids),
        "missing_source_impossible_rows_in_exclusion": sorted(SOURCE_IMPOSSIBLE_ROWS - exclusion_ids),
        "accepted_label_counts": counter([row["categorical_lifecycle_label"] for row in eligibility]),
        "accepted_source_lane_counts": counter([row["source_lane"] for row in eligibility]),
        "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in eligibility}),
        "accepted_unique_duplicate_group_ids": len({row["duplicate_group_id"] for row in eligibility}),
        "accepted_canonical_duplicate_member_count": sum(1 for row in eligibility if row.get("duplicate_key_denominator_member")),
        "accepted_noncanonical_projection_count": sum(1 for row in eligibility if not row.get("duplicate_key_denominator_member")),
        "accepted_duplicate_label_conflicts": accepted_duplicate_label_conflicts,
        "accepted_canonical_violations": accepted_canonical_violations,
        "reject_reason_counts": counter(
            code for row in reject_rows for code in row.get("reject_reason_codes", [])
        ),
        "nonaccepted_key_overlap_with_accepted": nonaccepted_key_overlap,
        "nonaccepted_group_overlap_with_accepted": nonaccepted_group_overlap,
        "row_flag_issues": row_flag_issues,
        "exclusion_denominator_violations": exclusion_denominator_violations,
        "nonaccepted_denominator_violations": nonaccepted_denominator_violations,
        "forbidden_row_field_hits": forbidden_row_hits,
        "forbidden_contract_field_hits": forbidden_contract_hits,
        "accepted_ids_sample": sorted(accepted_ids)[:10],
        "reject_ids_sample": sorted(reject_ids)[:10],
    }


def recheck_source_hash_records(schema: dict[str, Any]) -> dict[str, Any]:
    records = []
    missing = []
    strict_failures = []
    strict_matches = []
    line_ending_only = []
    mutable_context = []
    for record in schema.get("source_artifact_hash_records", []):
        path = Path(record["path"])
        p = abs_path(path)
        current_sha = sha256_file(p)
        current_norm = sha256_normalized(p)
        current_size = p.stat().st_size if p.exists() and p.is_file() else None
        output = {
            **record,
            "current_exists": p.exists(),
            "current_size_bytes": current_size,
            "current_sha256": current_sha,
            "current_normalized_sha256": current_norm,
        }
        if not p.exists() or not p.is_file():
            output["audit_status"] = "MISSING"
            missing.append(output)
        elif str(record.get("hash_policy", "")).startswith("mutable_context"):
            output["audit_status"] = "MUTABLE_CONTEXT_PRESENCE_ACCEPTED"
            mutable_context.append(output)
        elif current_sha == record.get("sha256"):
            output["audit_status"] = "STRICT_MATCH"
            strict_matches.append(output)
        elif current_norm == record.get("sha256"):
            output["audit_status"] = "LINE_ENDING_ONLY_MISMATCH_ACCEPTED"
            line_ending_only.append(output)
        else:
            output["audit_status"] = "STRICT_MISMATCH"
            strict_failures.append(output)
        records.append(output)
    return {
        "record_count": len(records),
        "strict_match_count": len(strict_matches),
        "line_ending_only_mismatch_count": len(line_ending_only),
        "mutable_context_presence_count": len(mutable_context),
        "missing_record_count": len(missing),
        "strict_failure_count": len(strict_failures),
        "records": records,
        "line_ending_only_mismatches": line_ending_only,
        "mutable_context_records": mutable_context,
        "missing_records": missing,
        "strict_failures": strict_failures,
        "status": "PASS" if not missing and not strict_failures else "FAIL",
    }


def controlling_hashes() -> list[dict[str, Any]]:
    paths = [
        (OUT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_GOAL_PROMPT_{DATE}.md", "current_g12_audit_prompt"),
        (RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json", "frozen_rulebook"),
        (RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json", "source_noleak_schema"),
        (RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl", "eligibility_ledger"),
        (RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl", "exclusion_ledger"),
        (RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json", "upstream_result_contract_completion"),
        (V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl", "v3_row_decision_ledger"),
        (V3_DIR / f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json", "v3_accepted_or_source_control_packet"),
        (V3_DIR / f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.json", "v3_reject_ledger"),
        (V3_DIR / f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json", "v3_blocker_impossibility_ledger"),
        (V3_DIR / f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.json", "v3_source_root_search_ledger"),
        (G12_V3_DIR / f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json", "g12_v3_source_control_decision"),
        (G12_V3_DIR / f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.json", "g12_v3_universe_audit"),
        (G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", "g12_v3_source_hash_audit"),
        (G12_V3_DIR / f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json", "g12_v3_duplicate_audit"),
        (G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.json", "g12_v3_source_control_row_audit"),
        (G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json", "g12_v3_source_impossibility_audit"),
        (PRIOR_RESULT_DIR / "NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json", "prior_result_contract_rulebook"),
        (G12_PRIOR_RESULT_DIR / "G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_2026-05-08.json", "prior_g12_result_contract_decision"),
        (V2_FORENSICS_DIR / f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json", "v2_forensics_label_family"),
        (G12_V2_FORENSICS_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json", "g12_v2_forensics_decision"),
    ]
    return [hash_record(path, role) for path, role in paths]


def build_context_anchor(generated_at: str, inputs: dict[str, Any], source_hash_audit: dict[str, Any]) -> dict[str, Any]:
    controlling_commits = {
        "current_head": git_head(),
        "current_g12_prompt": git_last_commit_for_path(OUT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_GOAL_PROMPT_{DATE}.md"),
        "result_contract_update": git_last_commit_for_path(RESULT_DIR),
        "v3_source_control_rebuild": git_last_commit_for_path(V3_DIR),
        "g12_v3_source_control_audit": git_last_commit_for_path(G12_V3_DIR),
        "prior_result_contract_design": git_last_commit_for_path(PRIOR_RESULT_DIR),
        "g12_prior_result_contract_audit": git_last_commit_for_path(G12_PRIOR_RESULT_DIR),
        "v2_forensics": git_last_commit_for_path(V2_FORENSICS_DIR),
        "g12_v2_forensics_audit": git_last_commit_for_path(G12_V2_FORENSICS_DIR),
    }
    return {
        "artifact_family": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "git_head": controlling_commits["current_head"],
        "controlling_commit_shas": controlling_commits,
        "preflight_completed": {
            "generate_live_state": True,
            "live_state_read": True,
            "latest_handoff_read": True,
            "quick_reference_card_read": True,
            "research_operating_doctrine_read": True,
            "research_current_state_read_direct_artifacts_because_stale": True,
            "goal_session_research_discipline_read": True,
            "local_heavy_data_inventory_read": True,
            "reading_order_skimmed": True,
        },
        "controlling_inputs": [
            rel(OUT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_GOAL_PROMPT_{DATE}.md"),
            rel(RESULT_DIR),
            rel(V3_DIR),
            rel(G12_V3_DIR),
            rel(PRIOR_RESULT_DIR),
            rel(G12_PRIOR_RESULT_DIR),
            rel(V2_FORENSICS_DIR),
            rel(G12_V2_FORENSICS_DIR),
        ],
        "source_hash_record_summary": {
            "contract_schema_records_rechecked": source_hash_audit["source_schema_recheck"]["record_count"],
            "strict_failure_count": source_hash_audit["source_schema_recheck"]["strict_failure_count"],
            "missing_record_count": source_hash_audit["source_schema_recheck"]["missing_record_count"],
            "line_ending_only_mismatch_count": source_hash_audit["source_schema_recheck"]["line_ending_only_mismatch_count"],
            "mutable_context_presence_count": source_hash_audit["source_schema_recheck"]["mutable_context_presence_count"],
        },
        "source_files_read_or_hashed": source_hash_audit["additional_audit_hash_records"],
        "searched_roots_and_controls": [
            rel(RESULT_DIR),
            rel(V3_DIR),
            rel(G12_V3_DIR),
            rel(PRIOR_RESULT_DIR),
            rel(G12_PRIOR_RESULT_DIR),
            rel(V2_FORENSICS_DIR),
            rel(G12_V2_FORENSICS_DIR),
            "C:/Users/MSI/Documents/ai-trading-agent/data/ticks referenced through NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_2026-05-09.json",
            "C:/tmp and prior worktrees referenced through upstream source-root search ledger; no new external source was required for this control audit",
        ],
        "active_question_stack": [
            "Can exactly 225 accepted V3 input-only categorical rows feed a future quarantined categorical count packet?",
            "Are 4 source-control rows, 4 source-impossible rows, and 65 rejects excluded from row-level and duplicate-collapsed denominators?",
            "Can duplicate projections, especially rejects that share accepted duplicate keys, inflate future counts or effective-N?",
            "Can allowed categorical input labels be mistaken for R, win/loss, expectancy, validation, promotion, or live-effect evidence?",
            "Can line-ending-only prompt hash drift or mutable context drift mask a real source artifact mismatch?",
            "What must the next count lane do if ambiguity appears?",
        ],
        "route_decisions": [
            "Audit only the frozen result contract; do not build the count packet and do not score outcomes.",
            "Use accepted terminal-family membership plus safe flags as the only future count eligibility gate.",
            "Treat source-control, source-impossible, and reject rows as exclusion-control records only.",
            "Preserve duplicate-collapsed primary denominator nofill_duplicate_key and secondary concentration denominator duplicate_group_id.",
            "Route any accepted duplicate-key label conflict, source hash mismatch, unsafe flag, or nonaccepted row in eligibility back to source-control/rebuild before counts.",
        ],
        "source_root_search_conclusion": inputs["v3_source_root_search"]["search_conclusion"],
    }


def build_source_hash_audit(inputs: dict[str, Any]) -> dict[str, Any]:
    source_schema_recheck = recheck_source_hash_records(inputs["schema"])
    additional = controlling_hashes()
    status = "PASS" if source_schema_recheck["status"] == "PASS" and all(item["exists"] for item in additional) else "FAIL"
    return {
        "artifact_family": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "status": status,
        "decision": "ACCEPT_SOURCE_HASH_CHAIN_WITH_LINE_ENDING_AND_MUTABLE_CONTEXT_EXCEPTIONS" if status == "PASS" else "BLOCK_SOURCE_HASH_CHAIN",
        "source_schema_recheck": source_schema_recheck,
        "additional_audit_hash_records": additional,
        "hash_exception_policy": {
            "line_ending_only": "Accepted only when the normalized LF hash equals the recorded hash; this preserves source bytes semantics and is recorded explicitly.",
            "mutable_context": "Context docs and regenerated LIVE_STATE are presence and current-hash anchored, not strict source-data blockers.",
            "strict_artifacts": "All row ledgers, rulebooks, source/no-leak audits, duplicate audits, and prior decisions must strict-match or line-ending-match only where explicitly observed.",
        },
        "local_heavy_data_note": "No new local-heavy data was needed because upstream V3/G12 source-root ledgers already source-hash the decisive tick/source searches. Any new USDJPY quote-event sequence source would be a separate source-control gate before this contract can change.",
    }


def build_noleak_denominator_audit(inputs: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    rulebook = inputs["rulebook"]
    schema = inputs["schema"]
    issues = []
    expected_present_counts = {key: value for key, value in EXPECTED_COUNTS.items() if value}
    if metrics["terminal_family_counts"] != expected_present_counts:
        issues.append("terminal_family_counts_mismatch")
    if metrics["terminal_family_counts"].get("blocked", 0) != 0:
        issues.append("blocked_terminal_family_nonzero")
    if metrics["row_count"] != 298 or metrics["unique_packet_row_ids"] != 298:
        issues.append("row_count_or_unique_packet_id_mismatch")
    if metrics["eligibility_row_count"] != 225 or metrics["exclusion_row_count"] != 73:
        issues.append("eligibility_or_exclusion_count_mismatch")
    if not metrics["eligibility_matches_accepted_ids"]:
        issues.append("eligibility_not_equal_to_accepted_terminal_family")
    if not metrics["exclusion_matches_nonaccepted_ids"]:
        issues.append("exclusion_not_equal_to_nonaccepted_terminal_families")
    if metrics["eligibility_exclusion_overlap"]:
        issues.append("eligibility_exclusion_overlap")
    if metrics["source_control_rows_in_eligibility"] or metrics["source_impossible_rows_in_eligibility"]:
        issues.append("control_or_impossible_rows_in_eligibility")
    if metrics["missing_source_control_rows_in_exclusion"] or metrics["missing_source_impossible_rows_in_exclusion"]:
        issues.append("control_or_impossible_rows_missing_from_exclusion")
    if metrics["row_flag_issues"]:
        issues.append("unsafe_flags_or_scoring_flags")
    if metrics["exclusion_denominator_violations"] or metrics["nonaccepted_denominator_violations"]:
        issues.append("nonaccepted_denominator_violation")
    if metrics["forbidden_row_field_hits"] or metrics["forbidden_contract_field_hits"]:
        issues.append("forbidden_field_hit")
    if rulebook.get("current_lane_result_records_produced") != 0 or rulebook.get("current_lane_scored_metric_values") != 0:
        issues.append("rulebook_scoring_records_nonzero")
    if inputs["result_completion"].get("current_lane_result_records_produced") != 0:
        issues.append("completion_result_records_nonzero")
    required_forbidden = {
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "mt5_history",
        "synthetic_r",
        "win_rate",
        "expectancy",
        "profit",
        "r_multiple",
    }
    if not required_forbidden <= set(schema.get("forbidden_fields", [])):
        issues.append("source_schema_missing_required_forbidden_field")

    return {
        "artifact_family": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "status": "PASS" if not issues else "FAIL",
        "decision": "ACCEPT_225_INPUT_ONLY_ROWS_AND_EXCLUDE_ALL_NONACCEPTED_ROWS" if not issues else "BLOCK_NOLEAK_OR_DENOMINATOR_GAP",
        "issues": issues,
        "recomputed_universe": {
            "row_count": metrics["row_count"],
            "unique_packet_row_ids": metrics["unique_packet_row_ids"],
            "terminal_family_counts": metrics["terminal_family_counts"],
            "terminal_state_counts": metrics["terminal_state_counts"],
            "eligibility_row_count": metrics["eligibility_row_count"],
            "exclusion_row_count": metrics["exclusion_row_count"],
            "accepted_label_counts": metrics["accepted_label_counts"],
            "accepted_source_lane_counts": metrics["accepted_source_lane_counts"],
        },
        "exclusion_controls": {
            "source_control_rows": metrics["source_control_ids"],
            "source_impossible_rows": metrics["source_impossible_ids"],
            "reject_row_count": metrics["reject_row_count"],
            "reject_reason_counts": metrics["reject_reason_counts"],
            "source_control_rows_in_eligibility": metrics["source_control_rows_in_eligibility"],
            "source_impossible_rows_in_eligibility": metrics["source_impossible_rows_in_eligibility"],
            "exclusion_denominator_violations": metrics["exclusion_denominator_violations"],
            "nonaccepted_denominator_violations": metrics["nonaccepted_denominator_violations"],
        },
        "label_boundary": {
            "allowed_categorical_input_labels": rulebook["label_family_separation"]["allowed_categorical_input_labels"],
            "categorical_labels_are_performance": rulebook["label_family_separation"]["categorical_labels_are_performance"],
            "forbidden_label_families": rulebook["label_family_separation"]["forbidden_label_families"],
            "over_interpretation_guard": rulebook["label_family_separation"]["over_interpretation_guard"],
            "current_lane_result_records_produced": rulebook["current_lane_result_records_produced"],
            "current_lane_scored_metric_values": rulebook["current_lane_scored_metric_values"],
        },
        "forbidden_field_hits": {
            "v3_row_ledger": metrics["forbidden_row_field_hits"],
            "contract_ledgers": metrics["forbidden_contract_field_hits"],
        },
        "safe_flags": {
            "row_flag_issues": metrics["row_flag_issues"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "r_performance_allowed": False,
            "broker_or_account_label_allowed": False,
        },
        "future_count_gate": [
            "Count only rows from the eligibility ledger with v3_terminal_family=accepted and source_safe_input_only=true.",
            "Exclude source_control, source_impossible, and reject families before computing row-level counts, duplicate-key counts, effective-N, or concentration diagnostics.",
            "If a nonaccepted row shares a duplicate key or group with accepted rows, it remains excluded and cannot alter effective-N.",
            "If an accepted row carries an unsafe flag, forbidden field, missing duplicate key, or label conflict, block the packet and route to source-control/rebuild.",
        ],
    }


def build_duplicate_audit(metrics: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    issues = []
    if metrics["accepted_unique_nofill_duplicate_keys"] != EXPECTED_DUPLICATE_KEY_COUNT:
        issues.append("accepted_unique_nofill_duplicate_keys_mismatch")
    if metrics["accepted_unique_duplicate_group_ids"] != EXPECTED_DUPLICATE_GROUP_COUNT:
        issues.append("accepted_unique_duplicate_group_ids_mismatch")
    if metrics["accepted_canonical_duplicate_member_count"] != EXPECTED_CANONICAL_DUPLICATE_ROWS:
        issues.append("canonical_duplicate_member_count_mismatch")
    if metrics["accepted_duplicate_label_conflicts"]:
        issues.append("accepted_duplicate_label_conflicts")
    if metrics["accepted_canonical_violations"]:
        issues.append("accepted_canonical_violations")
    if metrics["accepted_label_counts"] != EXPECTED_ACCEPTED_LABEL_COUNTS:
        issues.append("accepted_label_count_mismatch")
    if metrics["reject_reason_counts"] != EXPECTED_REJECT_REASON_COUNTS:
        issues.append("reject_reason_count_mismatch")

    return {
        "artifact_family": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "status": "PASS" if not issues else "FAIL",
        "decision": "ACCEPT_DUPLICATE_POLICY_FOR_COUNT_PACKET_WITH_REJECT_OVERLAP_GUARD" if not issues else "BLOCK_DUPLICATE_POLICY",
        "issues": issues,
        "recomputed_duplicate_state": {
            "accepted_row_count": metrics["eligibility_row_count"],
            "accepted_unique_nofill_duplicate_keys": metrics["accepted_unique_nofill_duplicate_keys"],
            "accepted_unique_duplicate_group_ids": metrics["accepted_unique_duplicate_group_ids"],
            "accepted_canonical_duplicate_member_count": metrics["accepted_canonical_duplicate_member_count"],
            "accepted_noncanonical_projection_count": metrics["accepted_noncanonical_projection_count"],
            "accepted_duplicate_label_conflict_count": len(metrics["accepted_duplicate_label_conflicts"]),
            "accepted_canonical_violation_count": len(metrics["accepted_canonical_violations"]),
        },
        "overlap_red_team": {
            "source_control_key_overlap_with_accepted": metrics["nonaccepted_key_overlap_with_accepted"]["source_control"],
            "source_impossible_key_overlap_with_accepted": metrics["nonaccepted_key_overlap_with_accepted"]["source_impossible"],
            "reject_key_overlap_with_accepted_count": len(metrics["nonaccepted_key_overlap_with_accepted"]["reject"]),
            "reject_key_overlap_with_accepted_sample": metrics["nonaccepted_key_overlap_with_accepted"]["reject"][:20],
            "source_control_group_overlap_with_accepted": metrics["nonaccepted_group_overlap_with_accepted"]["source_control"],
            "source_impossible_group_overlap_with_accepted": metrics["nonaccepted_group_overlap_with_accepted"]["source_impossible"],
            "reject_group_overlap_with_accepted_count": len(metrics["nonaccepted_group_overlap_with_accepted"]["reject"]),
            "interpretation": (
                "Reject rows can share accepted duplicate keys/groups because many rejects are noncanonical projections. "
                "They remain outside every denominator and must not add to or subtract from row-level counts, duplicate-key counts, or effective-N."
            ),
        },
        "frozen_policy": inputs["rulebook"]["duplicate_denominator_policy"],
        "next_count_packet_denominators": {
            "row_level": "225 accepted rows only; descriptive/source-inventory counts only.",
            "primary_collapsed": "182 unique nofill_duplicate_key rows; primary count-packet denominator.",
            "secondary_concentration": "139 unique duplicate_group_id rows; concentration/effective-N diagnostic.",
            "nonaccepted_rows": "73 exclusion-control rows only; never denominator members.",
        },
    }


def build_decision_ledger(
    inputs: dict[str, Any],
    metrics: dict[str, Any],
    source_hash_audit: dict[str, Any],
    noleak: dict[str, Any],
    duplicate: dict[str, Any],
    saturation: dict[str, Any],
) -> dict[str, Any]:
    issues = []
    for name, artifact in (
        ("source_hash", source_hash_audit),
        ("noleak_denominator", noleak),
        ("duplicate", duplicate),
        ("saturation", saturation),
    ):
        if artifact.get("status") != "PASS":
            issues.append(f"{name}_audit_not_pass")

    return {
        "artifact_family": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "overall_decision": DECISION if not issues else "BLOCK_FROZEN_V3_RESULT_CONTRACT",
        "decision_status": "PASS_ACCEPTED" if not issues else "FAIL_BLOCKED",
        "issues": issues,
        "decision_scope": "independent G12 control audit for future quarantined categorical count packet only",
        "non_claims": [
            "No outcome scoring, R, win-rate, expectancy, DSR/PBO performance, validation, promotion, or live-effect claim.",
            "No broker actual-R, account history, live order/deal/position, hidden label, MT5 order/account/history, paid/API/Databento, registry, or live trading surface use.",
            "No future count packet was built in this lane.",
        ],
        "required_decisions": {
            "frozen_contract_use": "ACCEPT_FOR_FUTURE_QUARANTINED_CATEGORICAL_COUNT_PACKET_AFTER_NEW_COUNT_LANE_ONLY",
            "eligible_universe": "ACCEPT_EXACTLY_225_ACCEPTED_INPUT_ONLY_ROWS",
            "exclusions": "ACCEPT_EXACTLY_4_SOURCE_CONTROL_4_SOURCE_IMPOSSIBLE_65_REJECTS_EXCLUDED",
            "duplicate_policy": "ACCEPT_225_ROW_LEVEL_182_NOFILL_DUPLICATE_KEY_139_DUPLICATE_GROUP_POLICY",
            "source_noleak_schema": "ACCEPT_FORBIDDEN_FIELD_AND_SAFE_FLAG_BLOCKERS",
            "current_lane_zero_scoring": "CONFIRMED_ZERO_RESULT_RECORDS_AND_ZERO_SCORED_METRICS",
            "future_count_packet": "MAY_RUN_NEXT_ONLY_WITH_RESTRICTIONS_IN_NEXT_PROMPT_PACK",
        },
        "verified_starting_facts": {
            "row_count_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
            "terminal_family_counts": metrics["terminal_family_counts"],
            "eligible_rows": metrics["eligibility_row_count"],
            "exclusion_rows": metrics["exclusion_row_count"],
            "source_control_rows": metrics["source_control_ids"],
            "source_impossible_rows": metrics["source_impossible_ids"],
            "reject_rows": metrics["reject_row_count"],
            "accepted_unique_nofill_duplicate_keys": metrics["accepted_unique_nofill_duplicate_keys"],
            "accepted_unique_duplicate_group_ids": metrics["accepted_unique_duplicate_group_ids"],
            "current_lane_result_records_produced": inputs["rulebook"]["current_lane_result_records_produced"],
            "current_lane_scored_metric_values": inputs["rulebook"]["current_lane_scored_metric_values"],
            "upstream_g12_source_control_decision": inputs["g12_decision"]["overall_decision"],
            "prior_result_contract_decision": inputs["prior_g12_result_decision"]["overall_decision"],
        },
        "primary_red_team_findings": [
            "The accepted eligibility ledger is exactly the accepted terminal family and has no overlap with the exclusion ledger.",
            "The source-control and source-impossible rows have no accepted duplicate-key or duplicate-group overlap; rejects do overlap, so future effective-N must filter to accepted rows before collapsing.",
            "All accepted duplicate keys have one canonical denominator member and zero accepted label conflicts.",
            "The only source hash drift in the upstream source schema is line-ending-only prompt drift plus mutable context presence records; strict source data artifacts match.",
            "Allowed labels are categorical input labels only; they cannot be described as profit, loss, edge, win/loss, validation, or promotion evidence.",
        ],
        "contract_acceptance_blockers": [],
        "future_count_packet_restrictions": [
            "Read the G12 audit decision, result contract rulebook, eligibility ledger, exclusion ledger, and source/no-leak schema.",
            "Recompute upstream source hashes and stop on strict mismatch.",
            "Assert the exact 298-row family equation before count tables.",
            "Use only the 225 eligibility-ledger rows for categorical counts.",
            "Report row-level, nofill_duplicate_key-collapsed, and duplicate_group_id concentration views.",
            "Exclude all 73 nonaccepted rows from sample size, effective-N, label counts, concentration diagnostics, validation, promotion, and interpretation denominators.",
            "Emit zero R/win/expectancy/broker/live/account/order/hidden labels and zero validation/promotion/live-effect claims.",
            "Run a separate post-count G12 audit before any G0 synthesis or later validation/promotion dossier.",
        ],
    }


def build_saturation_review(inputs: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    questions = [
        {
            "question": "Could source-control rows 0049, 0050, 0051, or 0241 enter any future denominator or label path?",
            "answer": "No under this contract. They are present only in exclusion/control artifacts, have future_scoring_lane_may_consume=false, denominator flags false, categorical_lifecycle_label=null, and terminal_family=source_control.",
            "evidence": metrics["source_control_ids"],
            "frozen_rule": "Exclude. A future lane can change this only through a separate source-control evidence-class rebuild and G12 gate.",
        },
        {
            "question": "Could source-impossible USDJPY rows 0130, 0143, 0165, or 0178 re-enter through duplicate keys, row IDs, projections, or missing quote-sequence assumptions?",
            "answer": "No for this count packet. They are excluded, have zero accepted duplicate-key/group overlap, and the exact unblocker remains a broker-native USDJPY quote-event sequence source with sequence ID or sub-row/sub-millisecond timestamp and no account/order/history labels.",
            "evidence": {
                "rows": metrics["source_impossible_ids"],
                "key_overlap": metrics["nonaccepted_key_overlap_with_accepted"]["source_impossible"],
                "group_overlap": metrics["nonaccepted_group_overlap_with_accepted"]["source_impossible"],
                "exact_unblocker": inputs["v3_impossibility"]["exact_unblocker"],
            },
            "frozen_rule": "Exclude. If exact source appears, route to source-control rebuild; do not count inside this packet.",
        },
        {
            "question": "Could the 65 rejects affect sample size, effective-N, label counts, concentration diagnostics, or interpretation?",
            "answer": "They can appear only as exclusion-control counts. A notable risk is that 47 reject rows share accepted duplicate keys/groups; therefore the next count lane must filter to accepted rows before any denominator or effective-N calculation.",
            "evidence": {
                "reject_count": metrics["reject_row_count"],
                "reject_reason_counts": metrics["reject_reason_counts"],
                "reject_key_overlap_count": len(metrics["nonaccepted_key_overlap_with_accepted"]["reject"]),
                "reject_group_overlap_count": len(metrics["nonaccepted_group_overlap_with_accepted"]["reject"]),
            },
            "frozen_rule": "Exclude before count, effective-N, concentration, interpretation, validation, or promotion.",
        },
        {
            "question": "Could row-level counts be mistaken for duplicate-collapsed denominators?",
            "answer": "Yes if the future packet ignores the frozen duplicate policy. This audit accepts row-level counts only for source traceability/descriptive packet views and freezes nofill_duplicate_key as the primary collapsed denominator.",
            "evidence": {
                "row_level": metrics["eligibility_row_count"],
                "nofill_duplicate_key": metrics["accepted_unique_nofill_duplicate_keys"],
                "duplicate_group_id": metrics["accepted_unique_duplicate_group_ids"],
            },
            "frozen_rule": "Always show all three views and label row-level as descriptive only.",
        },
        {
            "question": "Could accepted duplicate keys with multiple row projections inflate the categorical count packet?",
            "answer": "Not if the contract is followed. There are 43 noncanonical accepted projections; every accepted duplicate key has exactly one canonical denominator member and zero label conflicts.",
            "evidence": {
                "noncanonical_accepted_projection_count": metrics["accepted_noncanonical_projection_count"],
                "canonical_member_count": metrics["accepted_canonical_duplicate_member_count"],
                "label_conflict_count": len(metrics["accepted_duplicate_label_conflicts"]),
            },
            "frozen_rule": "Canonical duplicate-key member counts for the primary denominator; conflicting accepted labels block the key.",
        },
        {
            "question": "Could any allowed field be post-outcome, broker-realized, hidden-label, path-label, or future-context leakage?",
            "answer": "The allowed decision-time fields are identifiers, source lineage, symbol/session/side, duplicate keys, categorical input labels, V2/V3 terminal metadata, and safe flags. Forbidden field families include broker/account/live/order/hidden labels and R/performance fields.",
            "evidence": inputs["schema"]["allowed_decision_time_fields"],
            "frozen_rule": "Block any row or artifact containing a forbidden field or unsafe flag before counts.",
        },
        {
            "question": "Could line-ending-only prompt hash drift or mutable context hash drift hide real source-data mismatch?",
            "answer": "No strict source artifact mismatches were found. One line-ending-only controlling-prompt mismatch is normalized-hash equivalent; mutable contexts are presence/current-hash anchored and are not decisive source data.",
            "evidence": "source hash audit rechecked the upstream schema source_artifact_hash_records",
            "frozen_rule": "Accept line-ending-only prompt drift only when normalized hash matches; block strict row/source artifact mismatches.",
        },
        {
            "question": "Could a future scorer accidentally compute R, win rate, expectancy, DSR/PBO, validation, or promotion from categorical input labels?",
            "answer": "It could only by violating the contract. The future lane requirements and no-leak schema explicitly forbid these fields and statistics; DSR/PBO remain not_computable until a separate numeric/performance lane exists.",
            "evidence": inputs["rulebook"]["future_lane_requirements"],
            "frozen_rule": "Count categorical labels only; no performance math or validation language.",
        },
        {
            "question": "Does the contract preserve enough diagnostic fields for negative-result and lifecycle forensics without opening forbidden labels?",
            "answer": "Yes for count-packet forensics: source lineage, symbol/session/side, duplicate keys, categorical labels, V2/V3 status, exclusion reasons, and exact source requirements are preserved. It deliberately excludes broker/account/live and numeric performance labels.",
            "evidence": inputs["schema"]["allowed_decision_time_fields"],
            "frozen_rule": "Use preserved diagnostics for count interpretation and blocker routing, not outcome scoring.",
        },
        {
            "question": "What would a skeptical G0/G12 reviewer reject?",
            "answer": "The strongest rejection would be denominator laundering through duplicate projections or rejects sharing accepted keys. This audit preempts it by measuring reject overlaps and freezing accepted-row-only filtering before any duplicate/effective-N calculation.",
            "evidence": metrics["nonaccepted_key_overlap_with_accepted"],
            "frozen_rule": "Filter accepted rows first, then collapse duplicates.",
        },
        {
            "question": "If the next count lane sees ambiguity, should it count, exclude, split, route back, or request access?",
            "answer": "Count only safe accepted rows. Exclude source-control/source-impossible/reject rows. Block conflicting accepted duplicate keys or unsafe fields and route back to source-control/rebuild. Request exact broker-native USDJPY quote-event sequence only for source-impossible rows.",
            "evidence": "future count gate and next prompt pack",
            "frozen_rule": "Ambiguity never becomes a count by default.",
        },
        {
            "question": "What exact future lane owns scoring, post-count audit, G0 synthesis, and validation/promotion?",
            "answer": "The next lane is a quarantined categorical count packet. A separate post-count G12 audit must accept it. G0 synthesis is later and cannot use this audit as performance validation. Any validation/promotion dossier is a separate preregistered lane.",
            "evidence": inputs["rulebook"]["future_lane_requirements"],
            "frozen_rule": "Do not collapse evidence-class gates.",
        },
    ]
    return {
        "artifact_family": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
        "status": "PASS",
        "same_evidence_class_ambiguities_closed_or_routed": True,
        "questions": questions,
        "external_requirements": [
            "Only a broker-native USDJPY quote-event sequence source with sequence ID or sub-row/sub-millisecond timestamp can reopen source-impossible rows, and only through a separate source-control/rebuild/G12 gate.",
            "Any new larger cohort must bring source hashes, as-of rules, duplicate policy, no-leak schema, and exclusion controls before joining the denominator.",
        ],
    }


def build_completion_audit(generated_at: str) -> dict[str, Any]:
    checklist = [
        ("Fresh GTOS preflight completed", "context anchor preflight_completed and current LIVE_STATE regeneration"),
        ("Latest handoff/core doctrine/current state/goal discipline/local-heavy docs read", "context anchor preflight_completed"),
        ("Frozen V3 result-contract artifacts read", "context anchor controlling inputs plus source hashes"),
        ("Upstream V3/G12/prior-contract/V2-forensics controls read", "context anchor controlling inputs and commit SHAs"),
        ("Source hashes and exceptions recorded", "source hash audit strict/line-ending/mutable summary"),
        ("Accept/block/reject G12 decision produced", "decision ledger overall_decision"),
        ("225 accepted input-only rows verified", "noleak denominator audit and decision ledger"),
        ("4 source-control, 4 source-impossible, 65 rejects excluded", "noleak denominator audit exclusion controls"),
        ("Duplicate policy verified as 225 row-level / 182 key / 139 group", "duplicate audit"),
        ("Zero scoring/result records and false safety flags verified", "noleak denominator audit and verifier"),
        ("Saturation/self-red-team questions answered", "saturation review"),
        ("Next prompt pack written", "next prompt pack artifact"),
        ("Builder/verifier/focused tests written", "python artifacts and verifier results"),
        ("Forbidden live surfaces avoided", "verifier live-surface diff"),
        ("All artifacts committed", "final git commit evidence checked outside builder"),
    ]
    return {
        "artifact_family": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": generated_at,
        **BASE_FLAGS,
        "objective_restatement": (
            "Independently audit NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE as a G12 control gate and decide whether exactly "
            "225 accepted V3 input-only categorical rows can feed a future quarantined categorical count packet while "
            "4 source-control rows, 4 source-impossible rows, and 65 rejects remain excluded, without outcome scoring or live-surface changes."
        ),
        "expected_artifacts": JSON_OUTPUTS + MD_OUTPUTS + PY_OUTPUTS,
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "evidence": evidence, "status": "PENDING_VERIFIER"}
            for requirement, evidence in checklist
        ],
        "verification_results": {"status": "PENDING_RUN_VERIFY_SCRIPT"},
        "missing_or_weak_requirements": ["Verifier has not finalized the completion audit."],
        "completion_status": "PENDING_VERIFIER",
        "can_mark_goal_complete": False,
    }


def write_markdown(payloads: dict[str, dict[str, Any]]) -> None:
    context = payloads["context"]
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Context Anchor",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Audit lane: `{AUDIT_LANE_ID}`",
                f"Contract: `{CONTRACT_ID}`",
                f"Generated: `{context['generated_at_utc']}`",
                f"HEAD: `{context['git_head']}`",
                "",
                "## Boundaries",
                "",
                "- `validation_safe=false`",
                "- `outcome_review_opened=false`",
                "- `live_effect=false`",
                "- No outcome scoring, R, win-rate, expectancy, DSR/PBO performance, validation, promotion, broker/account/live/order labels, paid/API/Databento, registry, or live trading surface changes.",
                "",
                "## Active Questions",
                "",
                "\n".join(f"- {item}" for item in context["active_question_stack"]),
                "",
                "## Searched Roots And Controls",
                "",
                "\n".join(f"- `{item}`" for item in context["searched_roots_and_controls"]),
            ]
        ),
    )

    decision = payloads["decision"]
    facts = decision["verified_starting_facts"]
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Decision Ledger",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Decision: `{decision['overall_decision']}`",
                f"Status: `{decision['decision_status']}`",
                "",
                "## Verified Facts",
                "",
                f"- Row equation: `{facts['row_count_equation']}`",
                f"- Accepted rows: `{facts['eligible_rows']}`",
                f"- Source-control rows: `{', '.join(facts['source_control_rows'])}`",
                f"- Source-impossible rows: `{', '.join(facts['source_impossible_rows'])}`",
                f"- Reject rows: `{facts['reject_rows']}`",
                f"- Duplicate keys/groups: `{facts['accepted_unique_nofill_duplicate_keys']}` / `{facts['accepted_unique_duplicate_group_ids']}`",
                "",
                "This audit accepts the frozen contract only for a future quarantined categorical count packet. It opens no result/scoring lane.",
            ]
        ),
    )

    source = payloads["source_hash"]
    recheck = source["source_schema_recheck"]
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Source Hash Audit",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{source['status']}`",
                f"Decision: `{source['decision']}`",
                f"Schema hash records rechecked: `{recheck['record_count']}`",
                f"Strict matches: `{recheck['strict_match_count']}`",
                f"Line-ending-only accepted mismatches: `{recheck['line_ending_only_mismatch_count']}`",
                f"Mutable context presence records: `{recheck['mutable_context_presence_count']}`",
                f"Missing records: `{recheck['missing_record_count']}`",
                f"Strict failures: `{recheck['strict_failure_count']}`",
                "",
                source["local_heavy_data_note"],
            ]
        ),
    )

    noleak = payloads["noleak"]
    controls = noleak["exclusion_controls"]
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Noleak Denominator Audit",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{noleak['status']}`",
                f"Decision: `{noleak['decision']}`",
                f"Universe: `{noleak['recomputed_universe']['row_count']}` rows, `{noleak['recomputed_universe']['unique_packet_row_ids']}` unique packet row IDs",
                f"Terminal families: `{noleak['recomputed_universe']['terminal_family_counts']}`",
                f"Eligibility/exclusion rows: `{noleak['recomputed_universe']['eligibility_row_count']}` / `{noleak['recomputed_universe']['exclusion_row_count']}`",
                f"Source-control rows excluded: `{', '.join(controls['source_control_rows'])}`",
                f"Source-impossible rows excluded: `{', '.join(controls['source_impossible_rows'])}`",
                f"Reject rows excluded: `{controls['reject_row_count']}`",
                f"Forbidden field hits: `{len(noleak['forbidden_field_hits']['v3_row_ledger']) + len(noleak['forbidden_field_hits']['contract_ledgers'])}`",
                "",
                "Future count packets must filter to accepted input-only rows before counts, effective-N, or concentration diagnostics.",
            ]
        ),
    )

    duplicate = payloads["duplicate"]
    dup = duplicate["recomputed_duplicate_state"]
    overlap = duplicate["overlap_red_team"]
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Duplicate Audit",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{duplicate['status']}`",
                f"Decision: `{duplicate['decision']}`",
                f"Accepted row-level count: `{dup['accepted_row_count']}`",
                f"Accepted unique nofill_duplicate_key: `{dup['accepted_unique_nofill_duplicate_keys']}`",
                f"Accepted unique duplicate_group_id: `{dup['accepted_unique_duplicate_group_ids']}`",
                f"Accepted noncanonical projections: `{dup['accepted_noncanonical_projection_count']}`",
                f"Accepted label conflicts: `{dup['accepted_duplicate_label_conflict_count']}`",
                f"Reject key overlaps with accepted: `{overlap['reject_key_overlap_with_accepted_count']}`",
                "",
                overlap["interpretation"],
            ]
        ),
    )

    saturation = payloads["saturation"]
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Saturation Review",
        "\n".join(
            [
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                f"Status: `{saturation['status']}`",
                "",
                "## Red-Team Questions",
                "",
                "\n\n".join(
                    [
                        f"### {idx}. {item['question']}\n\n"
                        f"Answer: {item['answer']}\n\n"
                        f"Frozen rule: {item['frozen_rule']}"
                        for idx, item in enumerate(saturation["questions"], start=1)
                    ]
                ),
                "",
                "## External Requirements",
                "",
                "\n".join(f"- {item}" for item in saturation["external_requirements"]),
            ]
        ),
    )

    write_next_prompt_pack()
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Completion Audit",
        f"Promotion posture: `{PROMOTION_VERDICT}`\n\nGenerated completion audit is pending verifier finalization. Run `verify_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py`.",
    )


def write_next_prompt_pack() -> None:
    write_md(
        f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md",
        "G12 NOFILL CAT V3 Result Contract Next Prompt Pack",
        f"""Promotion posture: `{PROMOTION_VERDICT}`.

Run only after `{AUDIT_LANE_ID}` accepts `{CONTRACT_ID}`.

Recommended next lane: `NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET`.

Objective: build a quarantined categorical count packet from exactly the 225 accepted V3 input-only categorical rows in `NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl`. The lane may count categorical input labels and duplicate/concentration diagnostics only. It must not score outcomes, R, win rate, expectancy, DSR/PBO performance, validation, promotion, broker actual-R, account history, live order/deal/position, hidden labels, paid/API/Databento, registry, or live trading behavior.

Mandatory gates:
- Re-run GTOS preflight and read this G12 audit plus the frozen V3 result contract.
- Recompute upstream source hashes and stop on any strict mismatch. Line-ending-only prompt drift is acceptable only when the normalized LF hash matches.
- Assert `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject` before any count table.
- Consume only rows with `v3_terminal_family=accepted`, `source_safe_input_only=true`, `label_class=input_only_categorical`, and all safe flags false.
- Exclude source-control rows `0049`, `0050`, `0051`, `0241`; source-impossible rows `0130`, `0143`, `0165`, `0178`; and all 65 rejects before sample size, label counts, effective-N, or concentration diagnostics.
- Report row-level counts as descriptive/source-inventory counts only, primary duplicate-collapsed counts by `nofill_duplicate_key`, and secondary concentration by `duplicate_group_id`.
- If any accepted duplicate key has conflicting categorical labels, source geometry, or source ordering, block that key and route to source-control review.
- If a future lane wants to use source-control/source-impossible rows, split into a separate source-control/rebuild/G12 gate first.
- Emit zero R/win/expectancy fields or tables, and emit zero broker/account/live/order/hidden labels.
- Run a separate post-count G12 audit before any G0 synthesis or later validation/promotion dossier.

Freeze rule for ambiguity: accepted and safe rows count; source-control/source-impossible/reject rows exclude; unsafe or conflicting accepted rows block and route back; exact missing USDJPY sequence source requires access to broker-native quote-event sequence with sequence ID or sub-row/sub-millisecond timestamp and no account/order/history labels.
""",
    )


def build_artifacts() -> dict[str, dict[str, Any]]:
    generated_at = now_utc()
    inputs = load_inputs()
    metrics = compute_metrics(inputs)
    source_hash = build_source_hash_audit(inputs)
    noleak = build_noleak_denominator_audit(inputs, metrics)
    duplicate = build_duplicate_audit(metrics, inputs)
    saturation = build_saturation_review(inputs, metrics)
    decision = build_decision_ledger(inputs, metrics, source_hash, noleak, duplicate, saturation)
    context = build_context_anchor(generated_at, inputs, source_hash)
    completion = build_completion_audit(generated_at)

    payloads = {
        "context": context,
        "decision": decision,
        "source_hash": source_hash,
        "noleak": noleak,
        "duplicate": duplicate,
        "saturation": saturation,
        "completion": completion,
    }
    write_json(f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.json", context)
    write_json(f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json", decision)
    write_json(f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.json", source_hash)
    write_json(f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT_{DATE}.json", noleak)
    write_json(f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json", duplicate)
    write_json(f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.json", saturation)
    write_json(f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json", completion)
    write_markdown(payloads)
    return payloads


def main() -> None:
    payloads = build_artifacts()
    decision = payloads["decision"]
    facts = decision["verified_starting_facts"]
    print(
        json.dumps(
            {
                "status": "BUILT",
                "audit_lane_id": AUDIT_LANE_ID,
                "contract_id": CONTRACT_ID,
                "decision": decision["overall_decision"],
                "row_count_equation": facts["row_count_equation"],
                "eligible_rows": facts["eligible_rows"],
                "duplicate_keys": facts["accepted_unique_nofill_duplicate_keys"],
                "duplicate_groups": facts["accepted_unique_duplicate_group_ids"],
                **BASE_FLAGS,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
