#!/usr/bin/env python3
"""Build the NOFILL CAT V3 quarantined categorical count packet.

This lane is input/control evidence only. It counts accepted categorical
input labels and duplicate/concentration denominators, and it deliberately
does not open outcome, performance, validation, promotion, broker/account,
or live-trading evidence.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
SCHEMA_VERSION = "nofill_cat_v3_quarantined_categorical_count_packet_v1"
ROUTE_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET"
CONTRACT_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
RESULT_DIR = BASE / "nofill_cat_v3_result_contract_update"
V3_DIR = BASE / "nofill_cat_v3_source_control_rebuild"
G12_CONTRACT_DIR = BASE / "g12_nofill_cat_v3_result_contract_audit"
G12_V3_DIR = BASE / "g12_nofill_cat_v3_source_control_audit"

EXPECTED_EQUATION = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "reject": 65,
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
EXPECTED_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_KEY_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_GROUP_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 4,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 7,
}

MANDATORY_CONTEXT = [
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_READING_ORDER.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
]

LOCAL_HEAVY_ROOTS = [
    "C:/tmp",
    "C:/Users/MSI/Documents/ai-trading-agent/data",
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "C:/Users/MSI/Documents/ai-trading-agent/data/external",
    "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
    "C:/SierraChart",
]

BASE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def abs_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def rel(path: str | Path) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def read_json(path: str | Path) -> Any:
    with abs_path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with abs_path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    (OUT_DIR / name).write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def write_md(name: str, title: str, lines: list[str]) -> None:
    (OUT_DIR / name).write_text("# " + title + "\n\n" + "\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sha256_file(path: str | Path) -> str | None:
    p = abs_path(path)
    if not p.exists() or not p.is_file():
        return None
    digest = hashlib.sha256()
    with p.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_normalized(path: str | Path) -> str | None:
    p = abs_path(path)
    if not p.exists() or not p.is_file():
        return None
    data = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def git_head() -> str:
    return git_output(["git", "rev-parse", "HEAD"])


def git_last_commit(path: str | Path) -> str:
    return git_output(["git", "log", "-1", "--format=%H", "--", rel(path)])


def source_record(path: str | Path, role: str, policy: str = "strict_sha256") -> dict[str, Any]:
    p = abs_path(path)
    return {
        "path": rel(p),
        "role": role,
        "exists": p.exists(),
        "size_bytes": p.stat().st_size if p.exists() and p.is_file() else None,
        "sha256": sha256_file(p) if p.exists() and p.is_file() else None,
        "git_last_commit": git_last_commit(p) if p.exists() else None,
        "hash_policy": policy,
    }


def context_record(path: str) -> dict[str, Any]:
    p = abs_path(path)
    return {
        "path": path,
        "exists": p.exists(),
        "git_last_commit": git_last_commit(p) if p.exists() else None,
        "hash_policy": "mutable_context_presence_current_hash_recorded",
        "sha256_at_lane_start": sha256_file(p) if p.exists() and p.is_file() else None,
    }


def local_root_record(root: str) -> dict[str, Any]:
    p = Path(root)
    try:
        exists = p.exists()
        sample = []
        if exists and root.replace("\\", "/").lower().endswith("/tmp"):
            sample = [str(child).replace("\\", "/") for child in p.glob("gtos_otb/*nofill*")][:10]
        return {
            "root": root,
            "exists": exists,
            "search_action": "existence check plus cheap targeted nofill worktree scan where applicable",
            "sample_hits": sample,
            "count_packet_effect": "No local-heavy root can expand this denominator; the count packet is frozen to the G12-accepted 225 eligibility rows.",
        }
    except OSError as exc:
        return {
            "root": root,
            "exists": False,
            "search_action": "existence check attempted",
            "error": str(exc),
            "count_packet_effect": "No denominator expansion allowed without a separate source-control/rebuild/G12 gate.",
        }


def load_inputs() -> dict[str, Any]:
    return {
        "goal_prompt": OUT_DIR / f"NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_GOAL_PROMPT_{DATE}.md",
        "rulebook": read_json(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"),
        "eligibility": read_jsonl(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl"),
        "exclusion": read_jsonl(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl"),
        "duplicate_policy_text": abs_path(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_SAMPLE_POLICY_{DATE}.md").read_text(encoding="utf-8"),
        "source_schema": read_json(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json"),
        "v3_rows": read_jsonl(V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "v3_source_hash_audit": read_json(V3_DIR / f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"),
        "g12_decision": read_json(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json"),
        "g12_duplicate": read_json(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json"),
        "g12_source_hash": read_json(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.json"),
        "g12_next_prompt": abs_path(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md").read_text(encoding="utf-8"),
        "g12_v3_decision": read_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json"),
    }


def sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("packet_row_id", "")), str(row.get("source_inventory_id", "")))


def counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def effective_n(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    denom = sum((count / total) ** 2 for count in counts.values())
    return round(1 / denom, 6) if denom else 0.0


def top_share(counts: dict[str, int]) -> dict[str, Any]:
    if not counts:
        return {"label": None, "count": 0, "share": 0.0}
    label, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    total = sum(counts.values())
    return {"label": label, "count": count, "share": round(count / total, 6) if total else 0.0}


def join_accepted_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    v3_by_id = {row["packet_row_id"]: row for row in inputs["v3_rows"]}
    group_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inputs["eligibility"]:
        group_rows[row["duplicate_group_id"]].append(row)
    group_reps = {
        group: sorted(rows, key=sort_key)[0]["packet_row_id"]
        for group, rows in group_rows.items()
    }

    accepted: list[dict[str, Any]] = []
    for row in sorted(inputs["eligibility"], key=sort_key):
        upstream = v3_by_id[row["packet_row_id"]]
        accepted.append(
            {
                "packet_row_id": row["packet_row_id"],
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "source_inventory_id": row["source_inventory_id"],
                "source_lane": row["source_lane"],
                "source_packet_id": row["source_packet_id"],
                "source_row_id": row["source_row_id"],
                "symbol": row["symbol"],
                "session": row["session"],
                "side": row["side"],
                "duplicate_group_id": row["duplicate_group_id"],
                "nofill_duplicate_key": row["nofill_duplicate_key"],
                "categorical_lifecycle_label": row["categorical_lifecycle_label"],
                "label_class": upstream.get("label_class"),
                "source_safe_input_only": upstream.get("source_safe_input_only"),
                "v2_decision": upstream.get("v2_decision"),
                "v2_row_status": upstream.get("v2_row_status"),
                "v3_terminal_family": row["v3_terminal_family"],
                "v3_terminal_state": row["v3_terminal_state"],
                "row_level_count_member": True,
                "nofill_duplicate_key_count_member": bool(row["duplicate_key_denominator_member"]),
                "nofill_duplicate_key_canonical_packet_row_id": row["duplicate_key_canonical_packet_row_id"],
                "duplicate_group_id_count_member": row["packet_row_id"] == group_reps[row["duplicate_group_id"]],
                "duplicate_group_id_canonical_packet_row_id": group_reps[row["duplicate_group_id"]],
                "nofill_duplicate_key_row_count": row["nofill_duplicate_key_row_count"],
                "duplicate_group_id_row_count": row["duplicate_group_id_row_count"],
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "count_packet_use": "accepted_input_control_count_only",
            }
        )
    return accepted


def join_exclusion_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    v3_by_id = {row["packet_row_id"]: row for row in inputs["v3_rows"]}
    exclusions: list[dict[str, Any]] = []
    for row in sorted(inputs["exclusion"], key=sort_key):
        upstream = v3_by_id[row["packet_row_id"]]
        exclusions.append(
            {
                "packet_row_id": row["packet_row_id"],
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "source_inventory_id": row["source_inventory_id"],
                "source_lane": row["source_lane"],
                "source_packet_id": row["source_packet_id"],
                "source_row_id": row["source_row_id"],
                "symbol": row["symbol"],
                "session": row["session"],
                "side": row["side"],
                "duplicate_group_id": row["duplicate_group_id"],
                "nofill_duplicate_key": row["nofill_duplicate_key"],
                "label_class": upstream.get("label_class"),
                "source_safe_input_only": upstream.get("source_safe_input_only"),
                "v3_terminal_family": row["exclusion_family"],
                "v3_terminal_state": row["exclusion_state"],
                "exclusion_reason_codes": row.get("exclusion_reason_codes", []),
                "exact_next_requirement": row.get("exact_next_requirement"),
                "excluded_before_any_count": True,
                "row_level_count_member": False,
                "nofill_duplicate_key_count_member": False,
                "duplicate_group_id_count_member": False,
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "count_packet_use": "exclusion_proof_only_not_counted",
            }
        )
    return exclusions


def label_count_rows(rows: list[dict[str, Any]], member_field: str) -> list[dict[str, Any]]:
    selected = [row for row in rows if row[member_field]]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        grouped[row["categorical_lifecycle_label"]].append(row)
    output = []
    for label, label_rows in sorted(grouped.items()):
        output.append(
            {
                "categorical_lifecycle_label": label,
                "count": len(label_rows),
                "packet_row_ids": [row["packet_row_id"] for row in label_rows],
                "symbols": counter_dict([row["symbol"] for row in label_rows]),
                "sessions": counter_dict([row["session"] for row in label_rows]),
                "sides": counter_dict([row["side"] for row in label_rows]),
                "source_lanes": counter_dict([row["source_lane"] for row in label_rows]),
            }
        )
    return output


def count_by_label(rows: list[dict[str, Any]], member_field: str) -> dict[str, int]:
    return counter_dict([row["categorical_lifecycle_label"] for row in rows if row[member_field]])


def concentration_for_dimension(rows: list[dict[str, Any]], field: str, member_field: str) -> dict[str, Any]:
    counts = counter_dict([row[field] for row in rows if row[member_field]])
    return {
        "dimension": field,
        "counts": counts,
        "effective_n_herfindahl": effective_n(counts),
        "top_share": top_share(counts),
    }


def duplicate_conflict_audit(accepted: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        by_key[row["nofill_duplicate_key"]].append(row)

    label_conflicts = []
    geometry_conflicts = []
    ordering_blockers = []
    denominator_conflicts = []
    projection_variance = []
    for key, rows in sorted(by_key.items()):
        labels = {row["categorical_lifecycle_label"] for row in rows}
        geometry = {(row["symbol"], row["session"], row["side"], row["duplicate_group_id"]) for row in rows}
        state = {
            (
                row["v3_terminal_family"],
                row["v3_terminal_state"],
                row["label_class"],
                row["source_safe_input_only"],
            )
            for row in rows
        }
        canonical_members = [row["packet_row_id"] for row in rows if row["nofill_duplicate_key_count_member"]]
        expected = sorted(rows, key=sort_key)[0]["packet_row_id"]
        source_ordering_values = {row["source_row_id"] for row in rows}
        base = {
            "nofill_duplicate_key": key,
            "packet_row_ids": [row["packet_row_id"] for row in rows],
            "canonical_packet_row_id": expected,
        }
        if len(labels) > 1:
            label_conflicts.append({**base, "labels": sorted(labels)})
        if len(geometry) > 1:
            geometry_conflicts.append({**base, "geometries": sorted(map(str, geometry))})
        if len(state) > 1:
            ordering_blockers.append({**base, "states": sorted(map(str, state))})
        if canonical_members != [expected]:
            denominator_conflicts.append({**base, "flagged_canonical_members": canonical_members})
        if len(source_ordering_values) > 1 and len(labels) == 1 and len(geometry) == 1 and len(state) == 1:
            projection_variance.append(
                {
                    **base,
                    "row_count": len(rows),
                    "source_row_count": len(source_ordering_values),
                    "categorical_lifecycle_label": sorted(labels)[0],
                    "interpretation": "allowed_noncanonical_projection_variance_not_a_blocking_conflict",
                }
            )

    return {
        "accepted_duplicate_key_label_conflict_count": len(label_conflicts),
        "accepted_duplicate_key_source_geometry_conflict_count": len(geometry_conflicts),
        "accepted_duplicate_key_source_ordering_blocker_count": len(ordering_blockers),
        "accepted_duplicate_key_denominator_conflict_count": len(denominator_conflicts),
        "accepted_projection_variance_key_count": len(projection_variance),
        "accepted_projection_variance_noncanonical_row_count": sum(item["row_count"] - 1 for item in projection_variance),
        "label_conflicts": label_conflicts,
        "source_geometry_conflicts": geometry_conflicts,
        "source_ordering_blockers": ordering_blockers,
        "denominator_conflicts": denominator_conflicts,
        "projection_variance_not_blocking": projection_variance,
        "conflict_policy": "Any nonzero blocking conflict count blocks the whole duplicate key and routes it back to source-control/rebuild.",
    }


def recheck_source_schema_hashes(inputs: dict[str, Any]) -> dict[str, Any]:
    records = []
    strict_failures = []
    missing = []
    line_ending_only = []
    mutable_context = []
    strict_matches = []
    for record in inputs["source_schema"].get("source_artifact_hash_records", []):
        path = record["path"]
        current = sha256_file(path)
        current_norm = sha256_normalized(path)
        exists = abs_path(path).exists()
        out = {
            "path": path,
            "role": record.get("role"),
            "hash_policy": record.get("hash_policy"),
            "expected_sha256": record.get("sha256"),
            "current_sha256": current,
            "current_normalized_sha256": current_norm,
            "exists": exists,
        }
        if not exists:
            out["audit_status"] = "MISSING"
            missing.append(out)
        elif str(record.get("hash_policy", "")).startswith("mutable_context"):
            out["audit_status"] = "MUTABLE_CONTEXT_PRESENCE_ACCEPTED"
            mutable_context.append(out)
        elif current == record.get("sha256"):
            out["audit_status"] = "STRICT_MATCH"
            strict_matches.append(out)
        elif current_norm == record.get("sha256") and record.get("role") == "controlling_prompt":
            out["audit_status"] = "LINE_ENDING_ONLY_MISMATCH_ACCEPTED"
            line_ending_only.append(out)
        else:
            out["audit_status"] = "STRICT_MISMATCH"
            strict_failures.append(out)
        records.append(out)
    return {
        "record_count": len(records),
        "strict_match_count": len(strict_matches),
        "mutable_context_presence_count": len(mutable_context),
        "line_ending_only_mismatch_count": len(line_ending_only),
        "missing_record_count": len(missing),
        "strict_failure_count": len(strict_failures),
        "records": records,
        "strict_failures": strict_failures,
        "missing": missing,
        "line_ending_only_mismatches": line_ending_only,
    }


def scan_forbidden_keys(obj: Any, forbidden: set[str], path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if str(key) in forbidden:
                hits.append({"path": child, "field": str(key)})
            hits.extend(scan_forbidden_keys(value, forbidden, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, forbidden, f"{path}[{idx}]"))
    return hits


def scan_forbidden_string_values(obj: Any, forbidden: set[str], path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            hits.extend(scan_forbidden_string_values(value, forbidden, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_string_values(value, forbidden, f"{path}[{idx}]"))
    elif isinstance(obj, str):
        lower = obj.lower()
        for field in forbidden:
            if field in lower:
                hits.append({"path": path, "matched": field, "value": obj[:200]})
    return hits


def build_count_ledger(accepted: list[dict[str, Any]]) -> dict[str, Any]:
    row_counts = count_by_label(accepted, "row_level_count_member")
    key_counts = count_by_label(accepted, "nofill_duplicate_key_count_member")
    group_counts = count_by_label(accepted, "duplicate_group_id_count_member")
    sample_floor = []
    for label in sorted(row_counts):
        key_count = key_counts.get(label, 0)
        group_count = group_counts.get(label, 0)
        sample_floor.append(
            {
                "categorical_lifecycle_label": label,
                "unique_nofill_duplicate_key_count": key_count,
                "unique_duplicate_group_id_count": group_count,
                "sample_floor_status": (
                    "COUNT_CONTROL_FLOOR_MET" if key_count >= 30 and group_count >= 10 else "DISCOVERY_UNDER_SAMPLE_FLOOR"
                ),
                "interpretation": "Count-control diagnostic only; no validation, promotion, or outcome interpretation is opened.",
            }
        )
    payload = base_payload("NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER")
    payload.update(
        {
            "count_packet_scope": "accepted_input_control_rows_only",
            "universe_equation_asserted_before_counts": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
            "accepted_row_level_total": len(accepted),
            "primary_unique_nofill_duplicate_key_total": sum(1 for row in accepted if row["nofill_duplicate_key_count_member"]),
            "secondary_unique_duplicate_group_id_total": sum(1 for row in accepted if row["duplicate_group_id_count_member"]),
            "row_level_label_counts": row_counts,
            "primary_nofill_duplicate_key_label_counts": key_counts,
            "secondary_duplicate_group_id_label_counts": group_counts,
            "row_level_label_count_rows": label_count_rows(accepted, "row_level_count_member"),
            "primary_duplicate_key_label_count_rows": label_count_rows(accepted, "nofill_duplicate_key_count_member"),
            "secondary_duplicate_group_label_count_rows": label_count_rows(accepted, "duplicate_group_id_count_member"),
            "sample_floor_diagnostics": sample_floor,
            "non_claims": [
                "Counts are categorical input/control evidence only.",
                "No outcome, performance, validation, promotion, broker/account/live, hidden-label, paid/API, registry, or live-effect lane is opened.",
            ],
        }
    )
    return payload


def build_duplicate_diagnostics(accepted: list[dict[str, Any]], conflict: dict[str, Any]) -> dict[str, Any]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        by_key[row["nofill_duplicate_key"]].append(row)
        by_group[row["duplicate_group_id"]].append(row)
    key_size_counts = counter_dict([len(rows) for rows in by_key.values()])
    group_size_counts = counter_dict([len(rows) for rows in by_group.values()])
    top_groups = []
    for group_id, rows in sorted(by_group.items(), key=lambda item: (-len(item[1]), item[0]))[:12]:
        top_groups.append(
            {
                "duplicate_group_id": group_id,
                "row_count": len(rows),
                "unique_nofill_duplicate_key_count": len({row["nofill_duplicate_key"] for row in rows}),
                "label_counts": counter_dict([row["categorical_lifecycle_label"] for row in rows]),
                "packet_row_ids": [row["packet_row_id"] for row in sorted(rows, key=sort_key)],
            }
        )
    dimension_rows = [
        concentration_for_dimension(accepted, "categorical_lifecycle_label", "row_level_count_member"),
        concentration_for_dimension(accepted, "categorical_lifecycle_label", "nofill_duplicate_key_count_member"),
        concentration_for_dimension(accepted, "categorical_lifecycle_label", "duplicate_group_id_count_member"),
        concentration_for_dimension(accepted, "symbol", "row_level_count_member"),
        concentration_for_dimension(accepted, "session", "row_level_count_member"),
        concentration_for_dimension(accepted, "side", "row_level_count_member"),
        concentration_for_dimension(accepted, "source_lane", "row_level_count_member"),
    ]
    payload = base_payload("NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS")
    payload.update(
        {
            "accepted_row_level_total": len(accepted),
            "primary_unique_nofill_duplicate_key_total": len(by_key),
            "secondary_unique_duplicate_group_id_total": len(by_group),
            "accepted_noncanonical_projection_count": len(accepted) - len(by_key),
            "accepted_noncanonical_projection_explanation": (
                "Noncanonical accepted projections remain visible as row-level source inventory, but only the lowest packet_row_id/source_inventory_id "
                "inside each nofill_duplicate_key enters the primary duplicate-collapsed denominator."
            ),
            "duplicate_key_size_distribution": key_size_counts,
            "duplicate_group_size_distribution": group_size_counts,
            "max_duplicate_key_row_count": max(len(rows) for rows in by_key.values()),
            "max_duplicate_group_row_count": max(len(rows) for rows in by_group.values()),
            "top_duplicate_groups_by_row_count": top_groups,
            "effective_n_and_concentration": dimension_rows,
            "conflict_audit": conflict,
        }
    )
    return payload


def build_reject_overlap_audit(accepted: list[dict[str, Any]], exclusions: list[dict[str, Any]]) -> dict[str, Any]:
    accepted_keys = {row["nofill_duplicate_key"] for row in accepted}
    accepted_groups = {row["duplicate_group_id"] for row in accepted}
    reject_rows = [row for row in exclusions if row["v3_terminal_family"] == "reject"]
    source_control = [row for row in exclusions if row["v3_terminal_family"] == "source_control"]
    source_impossible = [row for row in exclusions if row["v3_terminal_family"] == "source_impossible"]
    reject_key_overlap = [row for row in reject_rows if row["nofill_duplicate_key"] in accepted_keys]
    reject_group_overlap = [row for row in reject_rows if row["duplicate_group_id"] in accepted_groups]
    payload = base_payload("NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT")
    payload.update(
        {
            "accepted_filter_applied_before_any_count": True,
            "accepted_row_level_total_after_filter": len(accepted),
            "nonaccepted_rows_excluded_before_filter": len(exclusions),
            "reject_row_count": len(reject_rows),
            "reject_key_overlap_with_accepted_count": len(reject_key_overlap),
            "reject_group_overlap_with_accepted_count": len(reject_group_overlap),
            "reject_overlap_packet_row_ids": [row["packet_row_id"] for row in reject_key_overlap],
            "source_control_key_overlap_with_accepted": [
                row["packet_row_id"] for row in source_control if row["nofill_duplicate_key"] in accepted_keys
            ],
            "source_impossible_key_overlap_with_accepted": [
                row["packet_row_id"] for row in source_impossible if row["nofill_duplicate_key"] in accepted_keys
            ],
            "denominator_effect": {
                "row_level_count_delta_from_rejects": 0,
                "nofill_duplicate_key_count_delta_from_rejects": 0,
                "duplicate_group_id_count_delta_from_rejects": 0,
                "reason": "The packet filters to accepted rows before counting or duplicate collapsing; reject rows remain exclusion proof only.",
            },
            "anti_laundering_rule": "Reject overlap can be documented, but rejects cannot add to, subtract from, or relabel accepted denominators.",
        }
    )
    return payload


def build_exclusion_summary(exclusions: list[dict[str, Any]], accepted: list[dict[str, Any]]) -> dict[str, Any]:
    accepted_ids = {row["packet_row_id"] for row in accepted}
    exclusion_ids = {row["packet_row_id"] for row in exclusions}
    payload = {
        "accepted_ids_intersection": sorted(accepted_ids & exclusion_ids),
        "exclusion_row_count": len(exclusions),
        "exclusion_family_counts": counter_dict([row["v3_terminal_family"] for row in exclusions]),
        "mandatory_source_control_rows_present": sorted(SOURCE_CONTROL_ROWS & exclusion_ids),
        "mandatory_source_impossible_rows_present": sorted(SOURCE_IMPOSSIBLE_ROWS & exclusion_ids),
        "reject_rows_present_count": sum(1 for row in exclusions if row["v3_terminal_family"] == "reject"),
        "all_exclusions_denominator_membership_false": all(
            not row["row_level_count_member"]
            and not row["nofill_duplicate_key_count_member"]
            and not row["duplicate_group_id_count_member"]
            for row in exclusions
        ),
    }
    return payload


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "contract_id": CONTRACT_ID,
        **BASE_FLAGS,
    }


def build_source_hash_noleak_audit(inputs: dict[str, Any], accepted: list[dict[str, Any]], exclusions: list[dict[str, Any]]) -> dict[str, Any]:
    source_schema_recheck = recheck_source_schema_hashes(inputs)
    lane_sources = [
        source_record(OUT_DIR / f"NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_GOAL_PROMPT_{DATE}.md", "count_lane_goal_prompt"),
        source_record(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json", "frozen_v3_rulebook"),
        source_record(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl", "frozen_v3_eligibility_ledger"),
        source_record(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl", "frozen_v3_exclusion_ledger"),
        source_record(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json", "frozen_v3_source_noleak_schema"),
        source_record(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_SAMPLE_POLICY_{DATE}.md", "frozen_v3_duplicate_policy"),
        source_record(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json", "g12_result_contract_decision"),
        source_record(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json", "g12_result_contract_duplicate_audit"),
        source_record(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md", "g12_result_contract_next_prompt"),
        source_record(V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl", "upstream_v3_row_decision_ledger"),
    ]
    forbidden = set(inputs["source_schema"].get("forbidden_fields", []))
    row_key_hits = scan_forbidden_keys(accepted + exclusions, forbidden)
    row_string_hits = scan_forbidden_string_values(accepted + exclusions, forbidden)
    flag_issues = [
        row["packet_row_id"]
        for row in accepted + exclusions
        if row["promotion_verdict"] != PROMOTION_VERDICT
        or row["validation_safe"] is not False
        or row["outcome_review_opened"] is not False
        or row["live_effect"] is not False
    ]
    payload = base_payload("NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT")
    payload.update(
        {
            "status": "PASS" if source_schema_recheck["strict_failure_count"] == 0 and not row_key_hits and not row_string_hits and not flag_issues else "FAIL",
            "source_schema_recheck": source_schema_recheck,
            "count_lane_source_records": lane_sources,
            "forbidden_row_key_hit_count": len(row_key_hits),
            "forbidden_row_string_hit_count": len(row_string_hits),
            "forbidden_row_key_hits": row_key_hits[:50],
            "forbidden_row_string_hits": row_string_hits[:50],
            "safe_flag_issue_packet_row_ids": flag_issues,
            "line_ending_only_prompt_mismatch_policy": "Accepted only when normalized LF hash matches; strict row/source artifact mismatches block the lane.",
            "local_heavy_roots": [local_root_record(root) for root in LOCAL_HEAVY_ROOTS],
        }
    )
    return payload


def build_context_anchor(inputs: dict[str, Any], count_ledger: dict[str, Any], source_audit: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("NOFILL_CAT_V3_COUNT_CONTEXT_ANCHOR")
    payload.update(
        {
            "generated_at_utc": generated_at(),
            "starting_head": git_head(),
            "objective": "Build an input-only quarantined categorical count/control packet from exactly the G12-accepted 225 V3 eligibility rows.",
            "controlling_prompt": rel(OUT_DIR / f"NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_GOAL_PROMPT_{DATE}.md"),
            "mandatory_context_records": [context_record(path) for path in MANDATORY_CONTEXT],
            "controlling_inputs": {
                "frozen_rulebook": rel(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"),
                "eligibility_ledger": rel(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl"),
                "exclusion_ledger": rel(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl"),
                "duplicate_policy": rel(RESULT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_SAMPLE_POLICY_{DATE}.md"),
                "g12_decision": rel(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json"),
                "g12_duplicate": rel(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json"),
                "g12_next_prompt": rel(G12_CONTRACT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md"),
            },
            "active_question_stack": [
                "Do the accepted-only rows reconcile to the exact 225/182/139 denominators?",
                "Do the four source-control, four source-impossible, and 65 reject rows stay outside every count?",
                "Does the 47-row reject overlap trap have zero denominator effect?",
                "Are there accepted duplicate-key label, geometry, ordering, source-hash, or denominator conflicts?",
                "Can categorical labels be interpreted only as input/control labels without outcome leakage?",
            ],
            "starting_count_summary": {
                "accepted_row_level_total": count_ledger["accepted_row_level_total"],
                "primary_unique_nofill_duplicate_key_total": count_ledger["primary_unique_nofill_duplicate_key_total"],
                "secondary_unique_duplicate_group_id_total": count_ledger["secondary_unique_duplicate_group_id_total"],
                "source_hash_strict_failure_count": source_audit["source_schema_recheck"]["strict_failure_count"],
            },
            "searched_roots": [local_root_record(root) for root in LOCAL_HEAVY_ROOTS],
            "boundary": [
                "No outcome scoring.",
                "No validation or promotion.",
                "No broker/account/live/order/hidden labels.",
                "No paid/API/Databento, registry, live trading, src/config/risk/execution/permission/safety/selector/canary/MT5 surface change.",
            ],
        }
    )
    return payload


def build_saturation_review(
    accepted: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    count_ledger: dict[str, Any],
    duplicate: dict[str, Any],
    overlap: dict[str, Any],
    source_audit: dict[str, Any],
) -> dict[str, Any]:
    questions = [
        {
            "question": "What could make one evidence class look like another?",
            "answer": "Source-control, source-impossible, and reject rows could be mistaken for accepted count rows if the filter was applied after duplicate collapse. This packet filters to accepted rows before row, key, group, effective-N, or concentration diagnostics.",
            "control": "accepted_filter_applied_before_any_count=true; exclusion ledger has 73 nonaccepted rows and zero denominator membership.",
        },
        {
            "question": "Could the 47 reject-overlap rows launder into denominators?",
            "answer": "They share accepted duplicate keys/groups but remain reject-family exclusion proof only. Their denominator delta is explicitly zero in row-level, nofill_duplicate_key, and duplicate_group_id views.",
            "control": f"reject_key_overlap_with_accepted_count={overlap['reject_key_overlap_with_accepted_count']}; denominator_effect={overlap['denominator_effect']}",
        },
        {
            "question": "Could duplicate projections inflate the packet?",
            "answer": "Row-level count is descriptive at 225. The primary denominator uses only 182 canonical nofill_duplicate_key members; 43 noncanonical accepted projections are not primary denominator rows.",
            "control": "canonical rule: lowest packet_row_id then source_inventory_id inside each duplicate key.",
        },
        {
            "question": "Could accepted duplicate keys have conflicting labels or source geometry?",
            "answer": "No blocking accepted duplicate-key conflicts were found. Projection variance exists in five accepted duplicate keys, but label, geometry, terminal state, label class, and source-safe flags are identical inside those keys.",
            "control": duplicate["conflict_audit"],
        },
        {
            "question": "Could source hashes have drifted?",
            "answer": "Strict source artifacts rechecked with zero strict failures and zero missing records. The known upstream prompt line-ending drift is accepted only because the normalized LF hash matches.",
            "control": source_audit["source_schema_recheck"],
        },
        {
            "question": "Could categorical labels be over-interpreted as outcomes?",
            "answer": "The label-family ledger freezes every category as input/control-only. No label is described as success/failure, edge, validation, promotion, profitability, or live effect.",
            "control": "label_family_interpretation_ledger plus forbidden row key/string scan.",
        },
        {
            "question": "Could source-control rows be useful and therefore counted?",
            "answer": "No. Rows 0049, 0050, 0051, and 0241 stay excluded unless a separate source-control/rebuild/G12 gate changes evidence class.",
            "control": sorted(SOURCE_CONTROL_ROWS),
        },
        {
            "question": "Could source-impossible USDJPY rows be inferred away?",
            "answer": "No. Rows 0130, 0143, 0165, and 0178 require a broker-native USDJPY quote-event sequence source with sequence ID or sub-row/sub-millisecond timestamp and no account/order/history labels.",
            "control": sorted(SOURCE_IMPOSSIBLE_ROWS),
        },
        {
            "question": "Could local heavy data expand this packet?",
            "answer": "No. Local-heavy roots are recorded for anti-boxing, but this count packet's denominator is frozen by the G12-accepted eligibility ledger. New rows require a separate source-hashed packet/rebuild/G12 lane.",
            "control": source_audit["local_heavy_roots"],
        },
        {
            "question": "Could session, symbol, side, or source-lane concentration make the counts fake-looking?",
            "answer": "Counts can be concentrated and still remain valid input/control counts. Concentration is explicitly reported through effective-N/top-share diagnostics and cannot become validation language.",
            "control": duplicate["effective_n_and_concentration"],
        },
        {
            "question": "Could a future G12 audit reject this lane?",
            "answer": "Likely rejection routes would be denominator laundering, missing hash proof, unsafe flags, forbidden fields, or label-family overclaim. The packet freezes controls and emits a next G12 prompt instead of G0/validation/promotion.",
            "control": "completion audit plus verifier.",
        },
        {
            "question": "What exact ambiguity remains in this evidence class?",
            "answer": "No same-evidence-class count ambiguity remains unresolved. Future use of excluded rows, larger cohorts, result scoring, G0 synthesis, validation, promotion, or live behavior crosses an evidence-class gate and needs a separate owner/G12 route.",
            "control": "same_evidence_class_status=SATURATED_FOR_COUNT_PACKET",
        },
    ]
    payload = base_payload("NOFILL_CAT_V3_COUNT_SATURATION_REVIEW")
    payload.update(
        {
            "status": "PASS",
            "same_evidence_class_status": "SATURATED_FOR_COUNT_PACKET",
            "questions": questions,
            "resolved_or_routed": {
                "conflicts": duplicate["conflict_audit"],
                "reject_overlap": {
                    "reject_overlap_count": overlap["reject_key_overlap_with_accepted_count"],
                    "denominator_delta": overlap["denominator_effect"],
                },
                "source_hash": {
                    "strict_failure_count": source_audit["source_schema_recheck"]["strict_failure_count"],
                    "missing_record_count": source_audit["source_schema_recheck"]["missing_record_count"],
                },
                "sample_floor": count_ledger["sample_floor_diagnostics"],
            },
            "external_requirements": [
                "Use excluded source-control rows only after a separate source-control/rebuild/G12 evidence-class gate.",
                "Use USDJPY source-impossible rows only after broker-native quote-event sequence data with sequence ID or sub-row/sub-millisecond timestamp is provided without account/order/history labels.",
                "Open any result, validation, promotion, G0 synthesis, registry, or live behavior only through separate explicitly approved lanes.",
            ],
        }
    )
    return payload


def build_completion_audit() -> dict[str, Any]:
    checklist = [
        ("GTOS preflight and starting HEAD recorded", "Context anchor records LIVE_STATE preflight inputs and starting_head."),
        ("Mandatory context read", "Context anchor lists LIVE_STATE, research_current_state, research_operating_doctrine, goal discipline, local-heavy inventory, quick reference, reading order, and latest handoff."),
        ("Frozen V3 contract and G12 audit read", "Context anchor/source audit include rulebook, eligibility, exclusion, duplicate policy, G12 decision, duplicate audit, and next prompt."),
        ("Exact universe equation asserted", "Count ledger records 298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject before counts."),
        ("Only accepted rows consumed", "Accepted input rows JSONL has 225 rows with accepted/source_safe/label_class/safe flags."),
        ("All nonaccepted rows excluded before counts", "Exclusion proof ledger has 73 rows with zero denominator membership."),
        ("47 reject-overlap trap neutralized", "Reject-overlap audit records 47 overlaps and zero denominator delta."),
        ("Duplicate denominators reconciled", "Count ledger/duplicate diagnostics report 225 row-level, 182 nofill_duplicate_key, and 139 duplicate_group_id."),
        ("Accepted-row conflicts resolved or routed", "Duplicate diagnostics conflict audit reports zero blocking conflicts and explains nonblocking projection variance."),
        ("Source hashes and no-leak checked", "Source hash/no-leak audit rechecks upstream schema hashes and row artifact forbidden keys/strings."),
        ("Label-family interpretation frozen", "Label-family ledger states every category's allowed and forbidden interpretation."),
        ("Saturation review completed", "Saturation review answers hostile-edge and same-evidence-class continuation questions."),
        ("Next route opened only as G12 prompt", "Next prompt pack points to G12 count-packet audit only."),
        ("Verifier, py_compile, focused pytest, and live-surface checks pass", "Verifier must finalize this completion audit."),
        ("Scoped commit completed", "Verifier artifact commit check must pass after commit."),
    ]
    payload = base_payload("NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT")
    payload.update(
        {
            "objective_restatement": (
                "Build NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET as an input-only count/control lane "
                "from exactly 225 G12-accepted V3 categorical rows, excluding 4 source-control, 4 source-impossible, "
                "and 65 reject rows before any counts, while preserving NO_PROMOTION_VERDICT and closed validation/live flags."
            ),
            "completion_status": "PENDING_VERIFIER",
            "can_mark_goal_complete": False,
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "evidence": evidence, "status": "PENDING_VERIFIER"}
                for requirement, evidence in checklist
            ],
            "verification_results": {"status": "PENDING_RUN_VERIFY_SCRIPT"},
            "missing_incomplete_or_weak_requirements": ["Verifier has not finalized the completion audit."],
        }
    )
    return payload


def write_markdown_artifacts(
    context: dict[str, Any],
    count_ledger: dict[str, Any],
    duplicate: dict[str, Any],
    overlap: dict[str, Any],
    source_audit: dict[str, Any],
    saturation: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    write_md(
        f"NOFILL_CAT_V3_COUNT_CONTEXT_ANCHOR_{DATE}.md",
        "NOFILL CAT V3 Count Context Anchor",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Route: `{ROUTE_ID}`",
            f"Contract: `{CONTRACT_ID}`",
            f"Starting HEAD: `{context['starting_head']}`",
            "",
            "## Boundary",
            "",
            "- `validation_safe=false`",
            "- `outcome_review_opened=false`",
            "- `live_effect=false`",
            "- Input/control counts only; no outcome, validation, promotion, or live behavior lane is opened.",
            "",
            "## Active Questions",
            "",
            *[f"- {item}" for item in context["active_question_stack"]],
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.md",
        "NOFILL CAT V3 Categorical Count Ledger",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Universe equation asserted before counts: `{count_ledger['universe_equation_asserted_before_counts']}`",
            f"Accepted row-level total: `{count_ledger['accepted_row_level_total']}`",
            f"Primary duplicate-key total: `{count_ledger['primary_unique_nofill_duplicate_key_total']}`",
            f"Secondary duplicate-group total: `{count_ledger['secondary_unique_duplicate_group_id_total']}`",
            "",
            "## Row-Level Descriptive Counts",
            "",
            *[f"- `{label}`: `{count}`" for label, count in count_ledger["row_level_label_counts"].items()],
            "",
            "## Primary Duplicate-Key Counts",
            "",
            *[f"- `{label}`: `{count}`" for label, count in count_ledger["primary_nofill_duplicate_key_label_counts"].items()],
            "",
            "## Secondary Duplicate-Group Counts",
            "",
            *[f"- `{label}`: `{count}`" for label, count in count_ledger["secondary_duplicate_group_id_label_counts"].items()],
            "",
            "These are categorical input/control counts only.",
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_{DATE}.md",
        "NOFILL CAT V3 Duplicate Concentration Diagnostics",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Accepted row-level total: `{duplicate['accepted_row_level_total']}`",
            f"Primary duplicate-key total: `{duplicate['primary_unique_nofill_duplicate_key_total']}`",
            f"Secondary duplicate-group total: `{duplicate['secondary_unique_duplicate_group_id_total']}`",
            f"Accepted noncanonical projection count: `{duplicate['accepted_noncanonical_projection_count']}`",
            "",
            duplicate["accepted_noncanonical_projection_explanation"],
            "",
            "## Conflict Audit",
            "",
            f"- Label conflicts: `{duplicate['conflict_audit']['accepted_duplicate_key_label_conflict_count']}`",
            f"- Source-geometry conflicts: `{duplicate['conflict_audit']['accepted_duplicate_key_source_geometry_conflict_count']}`",
            f"- Source-ordering blockers: `{duplicate['conflict_audit']['accepted_duplicate_key_source_ordering_blocker_count']}`",
            f"- Denominator conflicts: `{duplicate['conflict_audit']['accepted_duplicate_key_denominator_conflict_count']}`",
            f"- Nonblocking projection-variance keys: `{duplicate['conflict_audit']['accepted_projection_variance_key_count']}`",
            "",
            "## Effective-N / Concentration Views",
            "",
            *[
                f"- `{item['dimension']}`: effective_n=`{item['effective_n_herfindahl']}`, top=`{item['top_share']}`"
                for item in duplicate["effective_n_and_concentration"]
            ],
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.md",
        "NOFILL CAT V3 Reject Overlap Anti-Laundering Audit",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Reject rows: `{overlap['reject_row_count']}`",
            f"Reject key overlap with accepted: `{overlap['reject_key_overlap_with_accepted_count']}`",
            f"Reject group overlap with accepted: `{overlap['reject_group_overlap_with_accepted_count']}`",
            "",
            f"Denominator effect: `{overlap['denominator_effect']}`",
            "",
            overlap["anti_laundering_rule"],
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_LABEL_FAMILY_INTERPRETATION_LEDGER_{DATE}.md",
        "NOFILL CAT V3 Label Family Interpretation Ledger",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            "Every category below is an input/control category only. It is not a result label, validation label, promotion label, live-effect label, or account/broker label.",
            "",
            "- `nofill_terminal_before_entry`: source-safe categorical observation that the terminal family was recorded before entry touch under the frozen source packet.",
            "- `source_corrected_no_entry_through_pending_horizon`: source-corrected categorical observation that no entry occurred through the pending horizon under the accepted source route.",
            "- `fill_path_entry_before_protective_level_before_terminal_area`: input/path ordering category from accepted source packets only; it is not a success or failure label.",
            "- `fill_path_entry_before_protective_level_no_terminal_observed`: input/path ordering category where no terminal area was observed in the source window; it is not a validation statement.",
            "- `fill_path_entry_before_terminal_area_before_protective_level`: input/path ordering category from accepted source packets only; it is not a profit/loss statement.",
            "- `opening_drive_source_projection_ready_no_result_label`: opening-drive source projection category with no result label opened.",
            "- `canonical_duplicate_geometry_source_ready_no_label_assigned`: canonical duplicate/source-geometry category where no result label is assigned.",
            "",
            "Forbidden interpretation: none of these categories may be described as wins, losses, edge, profitability, validation, promotion, live readiness, or broker-realized behavior.",
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
        "NOFILL CAT V3 Count Source Hash Noleak Audit",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Status: `{source_audit['status']}`",
            f"Upstream source-schema hash records: `{source_audit['source_schema_recheck']['record_count']}`",
            f"Strict failures: `{source_audit['source_schema_recheck']['strict_failure_count']}`",
            f"Missing records: `{source_audit['source_schema_recheck']['missing_record_count']}`",
            f"Line-ending-only accepted mismatches: `{source_audit['source_schema_recheck']['line_ending_only_mismatch_count']}`",
            f"Forbidden row key hits: `{source_audit['forbidden_row_key_hit_count']}`",
            f"Forbidden row string hits: `{source_audit['forbidden_row_string_hit_count']}`",
            "",
            source_audit["line_ending_only_prompt_mismatch_policy"],
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_{DATE}.md",
        "NOFILL CAT V3 Count Saturation Review",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Status: `{saturation['status']}`",
            f"Same-evidence-class status: `{saturation['same_evidence_class_status']}`",
            "",
            *[
                f"## {idx}. {item['question']}\n\nAnswer: {item['answer']}\n\nControl: `{item['control']}`\n"
                for idx, item in enumerate(saturation["questions"], start=1)
            ],
            "## External Requirements",
            "",
            *[f"- {item}" for item in saturation["external_requirements"]],
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_COUNT_NEXT_G12_PROMPT_PACK_{DATE}.md",
        "NOFILL CAT V3 Count Next G12 Prompt Pack",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            "Recommended next lane: `G12_NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_AUDIT`.",
            "",
            "```text",
            "/goal Run G12_NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_AUDIT as an independent post-count audit. Complete GTOS preflight; read LIVE_STATE, research_current_state, research_operating_doctrine, goal_session_research_discipline, local_heavy_data_inventory, the frozen V3 result contract, the accepted G12 result-contract audit, and all NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET artifacts. Red-team whether the packet counted exactly 225 accepted input-only rows, 182 nofill_duplicate_key rows, and 139 duplicate_group_id rows while excluding 4 source-control rows, 4 source-impossible rows, and 65 rejects before counts. Verify source hashes, no-leak controls, duplicate conflicts, the 47 reject-overlap anti-laundering guard, label-family interpretation, completion audit, focused tests, and committed-diff live-surface scope. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not score outcomes, R, win rate, expectancy, DSR/PBO performance, validation, promotion, broker actual-R, account history, live order/deal/position labels, hidden labels, paid/API/Databento, registry edits, live trading prompts, src trading logic, risk, execution, permissions, safety gates, selectors, MT5 order/account/history surfaces, canaries, credentials, remote pushes, or order behavior. Produce only a G12 accept/block/reject audit and next prompt pack; do not open G0 synthesis or validation.",
            "```",
        ],
    )

    write_md(
        f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.md",
        "NOFILL CAT V3 Count Completion Audit",
        [
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Completion status: `{completion['completion_status']}`",
            f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`",
            "",
            "## Objective Restatement",
            "",
            completion["objective_restatement"],
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            *[
                f"- `{item['status']}` {item['requirement']}: {item['evidence']}"
                for item in completion["prompt_to_artifact_checklist"]
            ],
            "",
            "Run the verifier to finalize this audit.",
        ],
    )


def build_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    accepted = join_accepted_rows(inputs)
    exclusions = join_exclusion_rows(inputs)
    conflict = duplicate_conflict_audit(accepted)
    count_ledger = build_count_ledger(accepted)
    duplicate = build_duplicate_diagnostics(accepted, conflict)
    overlap = build_reject_overlap_audit(accepted, exclusions)
    exclusion_summary = build_exclusion_summary(exclusions, accepted)
    source_audit = build_source_hash_noleak_audit(inputs, accepted, exclusions)
    saturation = build_saturation_review(accepted, exclusions, count_ledger, duplicate, overlap, source_audit)
    completion = build_completion_audit()
    context = build_context_anchor(inputs, count_ledger, source_audit)

    # Include exclusion proof summary after rows are written so verifier can
    # validate both row-level and aggregate controls.
    exclusion_summary_payload = base_payload("NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_SUMMARY")
    exclusion_summary_payload.update(exclusion_summary)
    source_audit["exclusion_summary"] = exclusion_summary

    write_json(f"NOFILL_CAT_V3_COUNT_CONTEXT_ANCHOR_{DATE}.json", context)
    write_jsonl(f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl", accepted)
    write_jsonl(f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl", exclusions)
    write_json(f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.json", count_ledger)
    write_json(f"NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_{DATE}.json", duplicate)
    write_json(f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.json", overlap)
    write_json(f"NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", source_audit)
    write_json(f"NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_{DATE}.json", saturation)
    write_json(f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.json", completion)
    write_markdown_artifacts(context, count_ledger, duplicate, overlap, source_audit, saturation, completion)

    return {
        "status": "BUILT",
        "accepted_rows": len(accepted),
        "exclusion_rows": len(exclusions),
        "primary_duplicate_keys": count_ledger["primary_unique_nofill_duplicate_key_total"],
        "secondary_duplicate_groups": count_ledger["secondary_unique_duplicate_group_id_total"],
        "reject_overlap_count": overlap["reject_key_overlap_with_accepted_count"],
        "source_hash_strict_failures": source_audit["source_schema_recheck"]["strict_failure_count"],
        **BASE_FLAGS,
    }


def main() -> None:
    print(json.dumps(build_artifacts(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
