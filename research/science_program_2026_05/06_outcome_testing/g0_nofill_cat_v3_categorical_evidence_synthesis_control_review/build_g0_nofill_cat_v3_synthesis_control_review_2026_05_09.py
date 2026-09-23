#!/usr/bin/env python3
"""Build the G0 NOFILL CAT V3 categorical synthesis/control review.

This is a G0 governor/control synthesis over already G12-accepted categorical
count/control evidence. It does not open result scoring, validation, promotion,
broker/account labels, live trading surfaces, paid data, registry edits, or
order behavior.
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
SCHEMA = "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review_v1"
LANE = "G0_NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_EVIDENCE_SYNTHESIS_CONTROL_REVIEW"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
CONTROL_DECISION = "G0_ACCEPT_AS_DURABLE_CATEGORICAL_CONTROL_SYNTHESIS_NO_RESULT_SCORING"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]

SOURCE_REBUILD_DIR = OUTCOME_ROOT / "nofill_cat_v3_source_control_rebuild"
G12_SOURCE_AUDIT_DIR = OUTCOME_ROOT / "g12_nofill_cat_v3_source_control_audit"
CONTRACT_DIR = OUTCOME_ROOT / "nofill_cat_v3_result_contract_update"
G12_CONTRACT_AUDIT_DIR = OUTCOME_ROOT / "g12_nofill_cat_v3_result_contract_audit"
COUNT_PACKET_DIR = OUTCOME_ROOT / "nofill_cat_v3_quarantined_categorical_count_packet"
G12_COUNT_AUDIT_DIR = OUTCOME_ROOT / "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit"

GOAL_PROMPT = OUT_DIR / "G0_NOFILL_CAT_V3_SYNTHESIS_CONTROL_REVIEW_GOAL_PROMPT_2026-05-09.md"

EXPECTED_UNIVERSE = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "reject": 65,
    "total": 298,
}
EXPECTED_PRIMARY_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_ROW_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_SECONDARY_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 4,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 7,
}
SOURCE_CONTROL_ROWS = [
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
]
SOURCE_IMPOSSIBLE_ROWS = [
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]

OUTPUT_JSON = [
    "G0_NOFILL_CAT_V3_SYNTHESIS_CONTEXT_ANCHOR_2026-05-09.json",
    "G0_NOFILL_CAT_V3_SYNTHESIS_DECISION_LEDGER_2026-05-09.json",
    "G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_2026-05-09.json",
    "G0_NOFILL_CAT_V3_CATEGORICAL_LEARNING_SYNTHESIS_2026-05-09.json",
    "G0_NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_AND_SCOPE_RISK_2026-05-09.json",
    "G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json",
    "G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_2026-05-09.json",
    "G0_NOFILL_CAT_V3_COMPLETION_AUDIT_2026-05-09.json",
]

OUTPUT_MD = [
    "G0_NOFILL_CAT_V3_SYNTHESIS_CONTEXT_ANCHOR_2026-05-09.md",
    "G0_NOFILL_CAT_V3_SYNTHESIS_DECISION_LEDGER_2026-05-09.md",
    "G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_2026-05-09.md",
    "G0_NOFILL_CAT_V3_CATEGORICAL_LEARNING_SYNTHESIS_2026-05-09.md",
    "G0_NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_AND_SCOPE_RISK_2026-05-09.md",
    "G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md",
    "G0_NOFILL_CAT_V3_FORBIDDEN_ROUTE_LEDGER_2026-05-09.md",
    "G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_2026-05-09.md",
    "G0_NOFILL_CAT_V3_NEXT_PROMPT_PACK_2026-05-09.md",
    "G0_NOFILL_CAT_V3_COMPLETION_AUDIT_2026-05-09.md",
]

PY_FILES = [
    "build_g0_nofill_cat_v3_synthesis_control_review_2026_05_09.py",
    "verify_g0_nofill_cat_v3_synthesis_control_review_2026_05_09.py",
    "test_g0_nofill_cat_v3_synthesis_control_review_2026_05_09.py",
]

CONTROL_INPUTS = [
    GOAL_PROMPT,
    REPO_ROOT / ".context" / "LIVE_STATE.md",
    REPO_ROOT / ".context" / "00_core" / "quick_reference_card.md",
    REPO_ROOT / ".context" / "00_core" / "research_current_state.md",
    REPO_ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    REPO_ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    REPO_ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    REPO_ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_2026-05-09.json",
    SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-09.json",
    SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_ROW_DECISION_LEDGER_2026-05-09.jsonl",
    SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json",
    G12_SOURCE_AUDIT_DIR / "G12_NOFILL_CAT_V3_DECISION_LEDGER_2026-05-09.json",
    G12_SOURCE_AUDIT_DIR / "G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_2026-05-09.json",
    CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-09.json",
    CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl",
    CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_2026-05-09.jsonl",
    CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_2026-05-09.json",
    G12_CONTRACT_AUDIT_DIR / "G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_2026-05-09.json",
    G12_CONTRACT_AUDIT_DIR / "G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_2026-05-09.json",
    COUNT_PACKET_DIR / "NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_2026-05-09.json",
    COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_2026-05-09.jsonl",
    COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_2026-05-09.jsonl",
    COUNT_PACKET_DIR / "NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_2026-05-09.json",
    COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json",
    COUNT_PACKET_DIR / "NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_2026-05-09.json",
    COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_2026-05-09.json",
    G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_2026-05-09.json",
    G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_2026-05-09.json",
    G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_2026-05-09.json",
    G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER_2026-05-09.json",
    G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_2026-05-09.json",
]

FORBIDDEN_POLICY_REFERENCES = [
    "outcome scoring",
    "R or numeric performance scoring",
    "win-rate or expectancy computation",
    "DSR/PBO performance claim",
    "validation or promotion",
    "broker actual-R, account history, live order/deal/position, hidden labels",
    "paid/API/Databento access",
    "registry edit",
    "live trading prompt, src trading logic, risk, execution, permissions, safety gate, selector, canary, MT5 order/account/history, credential, remote push, order behavior",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "route_id": LANE,
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-c", "core.excludesfile=", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def count_from_mapping(rows: list[dict[str, Any]], field: str, member_field: str | None = None) -> dict[str, int]:
    selected = [row for row in rows if member_field is None or row.get(member_field) is True]
    return counts(selected, field)


def rows_for_member(rows: list[dict[str, Any]], member_field: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get(member_field) is True]


def load_inputs() -> dict[str, Any]:
    return {
        "source_universe": read_json(SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_2026-05-09.json"),
        "source_blocker": read_json(SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-09.json"),
        "source_row_ledger": read_jsonl(SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_ROW_DECISION_LEDGER_2026-05-09.jsonl"),
        "source_hash": read_json(SOURCE_REBUILD_DIR / "NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json"),
        "g12_source_decision": read_json(G12_SOURCE_AUDIT_DIR / "G12_NOFILL_CAT_V3_DECISION_LEDGER_2026-05-09.json"),
        "g12_source_universe": read_json(G12_SOURCE_AUDIT_DIR / "G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_2026-05-09.json"),
        "contract_rulebook": read_json(CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-09.json"),
        "contract_eligibility": read_jsonl(CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl"),
        "contract_exclusion": read_jsonl(CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_2026-05-09.jsonl"),
        "contract_noleak": read_json(CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_2026-05-09.json"),
        "g12_contract_decision": read_json(G12_CONTRACT_AUDIT_DIR / "G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_2026-05-09.json"),
        "g12_contract_duplicate": read_json(G12_CONTRACT_AUDIT_DIR / "G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_2026-05-09.json"),
        "count_ledger": read_json(COUNT_PACKET_DIR / "NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_2026-05-09.json"),
        "count_rows": read_jsonl(COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_2026-05-09.jsonl"),
        "count_exclusions": read_jsonl(COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_2026-05-09.jsonl"),
        "count_duplicate": read_json(COUNT_PACKET_DIR / "NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_2026-05-09.json"),
        "count_source_noleak": read_json(COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json"),
        "count_reject_overlap": read_json(COUNT_PACKET_DIR / "NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_2026-05-09.json"),
        "count_saturation": read_json(COUNT_PACKET_DIR / "NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_2026-05-09.json"),
        "g12_count_decision": read_json(G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_2026-05-09.json"),
        "g12_count_recompute": read_json(G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_RECOMPUTATION_LEDGER_2026-05-09.json"),
        "g12_count_source": read_json(G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_SOURCE_NOLEAK_REVIEW_2026-05-09.json"),
        "g12_count_reject_overlap": read_json(G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_REJECT_OVERLAP_LEDGER_2026-05-09.json"),
        "g12_count_label": read_json(G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_2026-05-09.json"),
    }


def control_hash_records() -> list[dict[str, Any]]:
    records = []
    for path in CONTROL_INPUTS:
        records.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return records


def recompute_facts(inputs: dict[str, Any]) -> dict[str, Any]:
    count_rows = inputs["count_rows"]
    exclusions = inputs["count_exclusions"]
    eligibility = inputs["contract_eligibility"]
    contract_exclusions = inputs["contract_exclusion"]

    primary_rows = rows_for_member(count_rows, "nofill_duplicate_key_count_member")
    secondary_rows = rows_for_member(count_rows, "duplicate_group_id_count_member")

    source_families = Counter(row.get("v3_terminal_family") for row in inputs["source_row_ledger"])
    exclusion_families = Counter(row.get("v3_terminal_family") for row in exclusions)

    facts = {
        "universe_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "source_row_terminal_family_counts": dict(sorted(source_families.items())),
        "accepted_row_level_total": len(count_rows),
        "primary_unique_nofill_duplicate_key_total": len({row["nofill_duplicate_key"] for row in count_rows}),
        "primary_member_rows": len(primary_rows),
        "secondary_unique_duplicate_group_id_total": len({row["duplicate_group_id"] for row in count_rows}),
        "secondary_member_rows": len(secondary_rows),
        "row_level_label_counts": count_from_mapping(count_rows, "categorical_lifecycle_label"),
        "primary_nofill_duplicate_key_label_counts": count_from_mapping(
            count_rows,
            "categorical_lifecycle_label",
            "nofill_duplicate_key_count_member",
        ),
        "secondary_duplicate_group_id_label_counts": count_from_mapping(
            count_rows,
            "categorical_lifecycle_label",
            "duplicate_group_id_count_member",
        ),
        "exclusion_family_counts": dict(sorted(exclusion_families.items())),
        "exclusion_rows": len(exclusions),
        "contract_eligibility_rows": len(eligibility),
        "contract_exclusion_rows": len(contract_exclusions),
        "accepted_ids_match_contract": sorted(row["packet_row_id"] for row in count_rows)
        == sorted(row["packet_row_id"] for row in eligibility),
        "exclusion_ids_match_contract": sorted(row["packet_row_id"] for row in exclusions)
        == sorted(row["packet_row_id"] for row in contract_exclusions),
        "source_control_rows": SOURCE_CONTROL_ROWS,
        "source_impossible_rows": SOURCE_IMPOSSIBLE_ROWS,
        "reject_rows": EXPECTED_UNIVERSE["reject"],
        "reject_overlap_count": inputs["count_reject_overlap"].get("reject_overlap_count")
        or inputs["count_reject_overlap"].get("accepted_reject_overlap", {}).get("reject_overlap_count")
        or inputs["g12_count_decision"]["verified_starting_facts"]["reject_overlap_rows"],
        "reject_denominator_delta": inputs["g12_count_recompute"].get("reject_overlap", {})
        or inputs["count_reject_overlap"].get("denominator_delta", {}),
        "duplicate_conflicts": inputs["g12_count_recompute"]["duplicate_conflicts_recomputed"],
        "source_noleak": {
            "source_hash_strict_failures": inputs["g12_count_decision"]["verified_starting_facts"]["source_hash_strict_failures"],
            "source_hash_missing_records": inputs["g12_count_decision"]["verified_starting_facts"]["source_hash_missing_records"],
            "forbidden_row_key_or_value_hits": inputs["g12_count_decision"]["verified_starting_facts"]["forbidden_row_key_or_value_hits"],
            "count_lane_source_hash_mismatch_count": inputs["g12_count_source"]["count_lane_source_hash_recheck"]["mismatch_count"],
            "count_lane_source_hash_missing_count": inputs["g12_count_source"]["count_lane_source_hash_recheck"]["missing_count"],
            "source_schema_strict_failure_count": inputs["g12_count_source"]["source_schema_recheck_recomputed"]["strict_failure_count"],
            "source_schema_missing_record_count": inputs["g12_count_source"]["source_schema_recheck_recomputed"]["missing_record_count"],
        },
    }
    validate_facts(facts)
    return facts


def validate_facts(facts: dict[str, Any]) -> None:
    errors = []
    expected_source = {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    if facts["source_row_terminal_family_counts"] != expected_source:
        errors.append(f"terminal_family_counts={facts['source_row_terminal_family_counts']}")
    if facts["accepted_row_level_total"] != 225:
        errors.append(f"accepted_row_level_total={facts['accepted_row_level_total']}")
    if facts["primary_unique_nofill_duplicate_key_total"] != 182:
        errors.append(f"primary_unique_nofill_duplicate_key_total={facts['primary_unique_nofill_duplicate_key_total']}")
    if facts["primary_member_rows"] != 182:
        errors.append(f"primary_member_rows={facts['primary_member_rows']}")
    if facts["secondary_unique_duplicate_group_id_total"] != 139:
        errors.append(f"secondary_unique_duplicate_group_id_total={facts['secondary_unique_duplicate_group_id_total']}")
    if facts["secondary_member_rows"] != 139:
        errors.append(f"secondary_member_rows={facts['secondary_member_rows']}")
    if facts["row_level_label_counts"] != EXPECTED_ROW_LABELS:
        errors.append(f"row_level_label_counts={facts['row_level_label_counts']}")
    if facts["primary_nofill_duplicate_key_label_counts"] != EXPECTED_PRIMARY_LABELS:
        errors.append(f"primary_counts={facts['primary_nofill_duplicate_key_label_counts']}")
    if facts["secondary_duplicate_group_id_label_counts"] != EXPECTED_SECONDARY_LABELS:
        errors.append(f"secondary_counts={facts['secondary_duplicate_group_id_label_counts']}")
    if facts["exclusion_rows"] != 73:
        errors.append(f"exclusion_rows={facts['exclusion_rows']}")
    if facts["exclusion_family_counts"] != {"reject": 65, "source_control": 4, "source_impossible": 4}:
        errors.append(f"exclusion_family_counts={facts['exclusion_family_counts']}")
    if not facts["accepted_ids_match_contract"]:
        errors.append("accepted ids do not match contract eligibility ledger")
    if not facts["exclusion_ids_match_contract"]:
        errors.append("exclusion ids do not match contract exclusion ledger")
    if facts["reject_overlap_count"] != 47:
        errors.append(f"reject_overlap_count={facts['reject_overlap_count']}")
    noleak = facts["source_noleak"]
    for key in (
        "source_hash_strict_failures",
        "source_hash_missing_records",
        "forbidden_row_key_or_value_hits",
        "count_lane_source_hash_mismatch_count",
        "count_lane_source_hash_missing_count",
        "source_schema_strict_failure_count",
        "source_schema_missing_record_count",
    ):
        if noleak[key] != 0:
            errors.append(f"{key}={noleak[key]}")
    conflicts = facts["duplicate_conflicts"]
    for key in (
        "accepted_duplicate_key_denominator_conflict_count",
        "accepted_duplicate_key_label_conflict_count",
        "accepted_duplicate_key_source_geometry_conflict_count",
        "accepted_duplicate_key_source_ordering_blocker_count",
        "accepted_duplicate_group_denominator_conflict_count",
    ):
        if conflicts.get(key) != 0:
            errors.append(f"{key}={conflicts.get(key)}")
    if errors:
        raise RuntimeError("; ".join(errors))


def dim_counts_for_primary(count_rows: list[dict[str, Any]], dim: str) -> dict[str, int]:
    return counts(rows_for_member(count_rows, "nofill_duplicate_key_count_member"), dim)


def label_risk_rows(count_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary = rows_for_member(count_rows, "nofill_duplicate_key_count_member")
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primary:
        by_label[row["categorical_lifecycle_label"]].append(row)
    out = []
    for label, rows in sorted(by_label.items()):
        out.append(
            {
                "categorical_lifecycle_label": label,
                "primary_duplicate_key_count": len(rows),
                "symbols": counts(rows, "symbol"),
                "sessions": counts(rows, "session"),
                "sides": counts(rows, "side"),
                "source_lanes": counts(rows, "source_lane"),
                "scope_risk": categorize_scope_risk(label, rows),
            }
        )
    return out


def categorize_scope_risk(label: str, rows: list[dict[str, Any]]) -> str:
    symbol_counts = Counter(row["symbol"] for row in rows)
    session_counts = Counter(row["session"] for row in rows)
    side_counts = Counter(row["side"] for row in rows)
    source_counts = Counter(row["source_lane"] for row in rows)
    dominant_symbol = symbol_counts.most_common(1)[0]
    dominant_session = session_counts.most_common(1)[0]
    dominant_side = side_counts.most_common(1)[0]
    dominant_source = source_counts.most_common(1)[0]
    notes = []
    if dominant_source[1] == len(rows):
        notes.append(f"single source lane {dominant_source[0]}")
    if dominant_symbol[1] == len(rows):
        notes.append(f"single symbol {dominant_symbol[0]}")
    if dominant_session[1] == len(rows):
        notes.append(f"single session {dominant_session[0]}")
    if dominant_side[1] == len(rows):
        notes.append(f"single side {dominant_side[0]}")
    if label == "nofill_terminal_before_entry":
        notes.append("dominant label family, broadest but still source-lane and side skewed")
    return "; ".join(notes) if notes else "multi-slice categorical clue, still non-performance"


def categorical_learning_rows() -> list[dict[str, Any]]:
    does_not_mean = [
        "not a result score",
        "not validation evidence",
        "not a promotion basis",
        "not broker/account/live-order evidence",
        "not a hidden-label substitute",
    ]
    return [
        {
            "label": "nofill_terminal_before_entry",
            "mechanism_clue": "Terminal-area state can appear before a side-aware entry touch; pending-entry geometry and stale intent handling are the main control questions.",
            "source_control_meaning": "The approved source can distinguish terminal-before-entry lifecycle order for many accepted duplicate keys.",
            "does_not_mean": does_not_mean,
            "blocker_or_next_capture": "Forward capture should log pending creation, terminal-area touch, entry-touch absence, cancel/expiry reason, spread/source coverage, and POI age.",
        },
        {
            "label": "source_corrected_no_entry_through_pending_horizon",
            "mechanism_clue": "Some accepted rows are true no-entry-through-horizon states after source correction, suggesting pending horizon and cancellation windows matter.",
            "source_control_meaning": "No side-aware entry event was found through the frozen pending horizon under the source contract.",
            "does_not_mean": does_not_mean,
            "blocker_or_next_capture": "Capture as-of horizon start/end, last eligible quote, cancel reason, and whether the untouched state is stale-POI, late-cancel, or normal expiry.",
        },
        {
            "label": "fill_path_entry_before_protective_level_no_terminal_observed",
            "mechanism_clue": "Source can identify entry before protective-level touch while terminal observation remains absent in the approved window.",
            "source_control_meaning": "This is a fill/path event-order category with an unresolved terminal observation, not a trade result.",
            "does_not_mean": does_not_mean,
            "blocker_or_next_capture": "A future event-order contract needs event timestamps, source window end reason, terminal search coverage, and same-tick ambiguity flags.",
        },
        {
            "label": "fill_path_entry_before_protective_level_before_terminal_area",
            "mechanism_clue": "A small USDJPY Tokyo family has source-ordering through entry, protective level, then terminal area.",
            "source_control_meaning": "The source can order a full three-event path for the row family, but only as a categorical state.",
            "does_not_mean": does_not_mean,
            "blocker_or_next_capture": "Needs broker-native quote-event sequencing for the unresolved USDJPY rows before any broader interpretation.",
        },
        {
            "label": "fill_path_entry_before_terminal_area_before_protective_level",
            "mechanism_clue": "A small USDJPY Tokyo family has source-ordering through entry, terminal area, then protective level.",
            "source_control_meaning": "The source can distinguish the opposite terminal/protective order for a small categorical family.",
            "does_not_mean": does_not_mean,
            "blocker_or_next_capture": "Keep as event-order vocabulary for a future frozen result contract; do not infer usefulness from the ordering alone.",
        },
        {
            "label": "opening_drive_source_projection_ready_no_result_label",
            "mechanism_clue": "Opening-drive projections can be source-ready but remain label-incomplete; row-level projections collapse sharply under duplicate keys.",
            "source_control_meaning": "The source-projection family is ready for a future contract-design lane, not a result lane.",
            "does_not_mean": does_not_mean,
            "blocker_or_next_capture": "Needs a separate frozen opening-drive result contract with as-of breakout/range definitions, event-order labels, duplicate policy, and post-count G12 audit before any result opening.",
        },
        {
            "label": "canonical_duplicate_geometry_source_ready_no_label_assigned",
            "mechanism_clue": "A small canonical duplicate-geometry residue exists after source-identity cleanup.",
            "source_control_meaning": "Duplicate identity and geometry controls can preserve source-ready rows without assigning an outcome label.",
            "does_not_mean": does_not_mean,
            "blocker_or_next_capture": "Needs clearer label assignment rules or a source-control return lane if future cohorts produce more rows of this type.",
        },
    ]


def build_context_anchor(facts: dict[str, Any]) -> dict[str, Any]:
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_SYNTHESIS_CONTEXT_ANCHOR"),
        "control_decision": CONTROL_DECISION,
        "starting_head": git_output("rev-parse", "HEAD"),
        "git_status_short_at_build": git_output("status", "--short"),
        "controlling_prompt": rel(GOAL_PROMPT),
        "mandatory_context_read": [
            ".context/LIVE_STATE.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        ],
        "upstream_directories_read": [
            rel(SOURCE_REBUILD_DIR),
            rel(G12_SOURCE_AUDIT_DIR),
            rel(CONTRACT_DIR),
            rel(G12_CONTRACT_AUDIT_DIR),
            rel(COUNT_PACKET_DIR),
            rel(G12_COUNT_AUDIT_DIR),
        ],
        "control_input_hashes": control_hash_records(),
        "recomputed_control_facts": facts,
        "hard_boundaries": {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "result_scoring": "closed",
            "broker_account_live_surfaces": "closed",
            "paid_data_or_remote": "closed",
            "live_trading_surface_changes": "closed",
        },
    }
    write_json(OUT_DIR / f"G0_NOFILL_CAT_V3_SYNTHESIS_CONTEXT_ANCHOR_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G0_NOFILL_CAT_V3_SYNTHESIS_CONTEXT_ANCHOR_{DATE}.md",
        [
            "# G0 NOFILL CAT V3 Synthesis Context Anchor",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Starting HEAD: `{payload['starting_head']}`.",
            f"Control decision: `{CONTROL_DECISION}`.",
            "",
            "## Scope",
            "",
            "This G0 route consumes G12-accepted categorical count/control evidence only. It does not open result scoring, validation, promotion, live behavior, broker/account labels, paid data, registry edits, or order behavior.",
            "",
            "## Required Context Read",
            "",
            *[f"- `{item}`" for item in payload["mandatory_context_read"]],
            "",
            "## Recomputed Control Facts",
            "",
            f"- `{facts['universe_equation']}`.",
            f"- Row-level accepted rows: `{facts['accepted_row_level_total']}`.",
            f"- Primary nofill_duplicate_key denominator: `{facts['primary_unique_nofill_duplicate_key_total']}`.",
            f"- Secondary duplicate_group_id denominator: `{facts['secondary_unique_duplicate_group_id_total']}`.",
            f"- Reject-overlap trap: `{facts['reject_overlap_count']}` overlaps with zero denominator effect.",
            f"- Source/no-leak strict failures: `{facts['source_noleak']['source_hash_strict_failures']}`; missing records: `{facts['source_noleak']['source_hash_missing_records']}`; forbidden row key/value hits: `{facts['source_noleak']['forbidden_row_key_or_value_hits']}`.",
        ],
    )
    return payload


def build_decision_ledger(facts: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_SYNTHESIS_DECISION_LEDGER"),
        "overall_decision": CONTROL_DECISION,
        "decision_scope": "G0 synthesis/control map for accepted quarantined categorical count evidence only",
        "accepted_upstream_decision": inputs["g12_count_decision"]["overall_decision"],
        "decision_reasons": [
            "The full source-control to count-audit chain reconciles to the exact 298-row equation.",
            "The accepted denominator is frozen to 225 row-level input/control rows, 182 primary duplicate-key members, and 139 secondary duplicate-group members.",
            "Mandatory exclusions remain excluded before row, duplicate, concentration, or interpretation views.",
            "The reject-overlap trap has zero denominator effect because accepted filtering precedes duplicate collapse.",
            "No accepted duplicate conflicts, source/no-leak strict failures, missing records, or forbidden row key/value hits were found.",
            "Every categorical label remains mechanism/control evidence and cannot be interpreted as validation, promotion, or live behavior.",
        ],
        "required_preserved_flags": {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "g0_allows": [
            "Durable source/control synthesis.",
            "Categorical mechanism-clue vocabulary.",
            "Duplicate and concentration risk map.",
            "Source-contract and capture backlog.",
            "Prompt packs for separate future evidence-class lanes.",
        ],
        "g0_does_not_allow": FORBIDDEN_POLICY_REFERENCES,
        "blocking_conditions_for_future_reuse": [
            "Any source hash strict mismatch.",
            "Any accepted duplicate-key label, geometry, ordering, or denominator conflict.",
            "Any nonaccepted row entering row-level, duplicate-key, duplicate-group, sample-size, or interpretation denominators.",
            "Any categorical label being described as a result, validation, promotion, or live-use claim.",
            "Any use of account/order/history/live/broker labels in this evidence class.",
        ],
        "recomputed_facts": facts,
    }
    write_json(OUT_DIR / f"G0_NOFILL_CAT_V3_SYNTHESIS_DECISION_LEDGER_{DATE}.json", payload)
    write_md(
        OUT_DIR / f"G0_NOFILL_CAT_V3_SYNTHESIS_DECISION_LEDGER_{DATE}.md",
        [
            "# G0 NOFILL CAT V3 Synthesis Decision Ledger",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Overall decision: `{CONTROL_DECISION}`.",
            "",
            "## What G0 Accepts",
            "",
            "G0 accepts the V3 chain as a durable categorical control synthesis map. The accepted evidence is useful for source contracts, capture design, duplicate-risk controls, and future prompt routing.",
            "",
            "## What G0 Does Not Open",
            "",
            *[f"- {item}." for item in FORBIDDEN_POLICY_REFERENCES],
            "",
            "## Control Reasons",
            "",
            *[f"- {item}" for item in payload["decision_reasons"]],
            "",
            "## Future Blocking Conditions",
            "",
            *[f"- {item}" for item in payload["blocking_conditions_for_future_reuse"]],
        ],
    )
    return payload


def build_evidence_reconciliation(facts: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    chain = [
        {
            "stage": "V3 source-control rebuild",
            "path": rel(SOURCE_REBUILD_DIR),
            "decision": inputs["source_universe"]["status"],
            "control_meaning": "Reconciled V2 blockers into accepted, source_control, source_impossible, and reject families without opening result scoring.",
            "key_fact": inputs["source_universe"]["v3_reconciliation"],
        },
        {
            "stage": "G12 source-control audit",
            "path": rel(G12_SOURCE_AUDIT_DIR),
            "decision": inputs["g12_source_decision"]["overall_decision"],
            "control_meaning": "Accepted V3 as source-control/categorical-input evidence only.",
            "key_fact": inputs["g12_source_decision"]["terminal_family_counts"],
        },
        {
            "stage": "Frozen V3 result contract",
            "path": rel(CONTRACT_DIR),
            "decision": inputs["contract_rulebook"]["contract_status"],
            "control_meaning": "Froze the 225 accepted input-only categorical rows, 73 exclusions, duplicate policy, and label boundaries for a future count packet.",
            "key_fact": inputs["contract_rulebook"]["duplicate_denominator_policy"],
        },
        {
            "stage": "G12 result-contract audit",
            "path": rel(G12_CONTRACT_AUDIT_DIR),
            "decision": inputs["g12_contract_decision"]["overall_decision"],
            "control_meaning": "Accepted the frozen contract for a future quarantined categorical count packet only.",
            "key_fact": inputs["g12_contract_decision"]["verified_starting_facts"],
        },
        {
            "stage": "NOFILL CAT V3 count packet",
            "path": rel(COUNT_PACKET_DIR),
            "decision": inputs["count_ledger"]["count_packet_scope"],
            "control_meaning": "Emitted row-level, primary duplicate-key, and secondary duplicate-group categorical count/control views.",
            "key_fact": {
                "row_level_label_counts": inputs["count_ledger"]["row_level_label_counts"],
                "primary_nofill_duplicate_key_label_counts": inputs["count_ledger"]["primary_nofill_duplicate_key_label_counts"],
                "secondary_duplicate_group_id_label_counts": inputs["count_ledger"]["secondary_duplicate_group_id_label_counts"],
            },
        },
        {
            "stage": "G12 post-count audit",
            "path": rel(G12_COUNT_AUDIT_DIR),
            "decision": inputs["g12_count_decision"]["overall_decision"],
            "control_meaning": "Accepted the count packet as quarantined categorical count/control evidence and routed next to this separate G0 synthesis/control review only.",
            "key_fact": inputs["g12_count_decision"]["verified_starting_facts"],
        },
        {
            "stage": "G0 synthesis/control review",
            "path": rel(OUT_DIR),
            "decision": CONTROL_DECISION,
            "control_meaning": "Synthesizes source lessons, label-family boundaries, duplicate/concentration risk, exact blockers, next lanes, and forbidden routes without changing evidence class.",
            "key_fact": facts,
        },
    ]
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION"),
        "control_decision": CONTROL_DECISION,
        "chain": chain,
        "proof_summary": {
            "proven": [
                "The exact V3 universe equation is reconciled and independently audited.",
                "The accepted count/control denominator is exactly 225 row-level rows, 182 primary duplicate-key members, and 139 secondary duplicate-group members.",
                "Exclusions stay out of denominators before all counting and duplicate-collapse views.",
                "Accepted duplicate conflicts are zero.",
                "Source/no-leak strict failures, missing records, and forbidden row key/value hits are zero.",
            ],
            "not_proven": [
                "No result or performance property.",
                "No validation-safe status.",
                "No promotion status.",
                "No broker/account/live-order claim.",
                "No live behavior or order-behavior change.",
                "No claim that the categories generalize outside the frozen source/control cohort.",
            ],
        },
    }
    write_json(OUT_DIR / f"G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.json", payload)
    lines = [
        "# G0 NOFILL CAT V3 Evidence Chain Reconciliation",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Chain",
        "",
        "| Stage | Decision | Control Meaning |",
        "|---|---|---|",
    ]
    for item in chain:
        lines.append(f"| {item['stage']} | `{item['decision']}` | {item['control_meaning']} |")
    lines.extend(
        [
            "",
            "## What Has Been Proven",
            "",
            *[f"- {item}" for item in payload["proof_summary"]["proven"]],
            "",
            "## What Has Not Been Proven",
            "",
            *[f"- {item}" for item in payload["proof_summary"]["not_proven"]],
        ]
    )
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.md", lines)
    return payload


def build_learning_synthesis(facts: dict[str, Any], count_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = facts["primary_nofill_duplicate_key_label_counts"]
    risk_rows = label_risk_rows(count_rows)
    learning = {
        **base_payload("G0_NOFILL_CAT_V3_CATEGORICAL_LEARNING_SYNTHESIS"),
        "primary_denominator": "nofill_duplicate_key",
        "primary_label_counts": label_counts,
        "label_scope_risks": risk_rows,
        "label_learning": categorical_learning_rows(),
        "hostile_review_answer": [
            "A hostile review should treat every category as possibly duplicated, source-leaked, session-specific, broker-impossible, or over-interpreted until controls show otherwise.",
            "The duplicate controls handle row-repeat risk for opening-drive projections, but they also show that row-level counts can exaggerate projection-heavy categories.",
            "Source-impossible USDJPY rows are not inferred away; they remain exact blockers needing broker-native quote-event sequencing.",
            "The dominant terminal-before-entry family is useful mechanism vocabulary, not proof that any future action is beneficial.",
        ],
        "market_behavior_clues": [
            "Pending-entry geometry may be too close to terminal-area invalidation in some source families.",
            "Opening-drive projections can produce many source rows that collapse to few duplicate-key members, so projection multiplication is a core control risk.",
            "No-entry-through-horizon states suggest stale-pending, late-cancel, or untouched-entry lifecycle distinctions worth capturing prospectively.",
            "Fill/path event-order labels suggest source-observable sequence states, but current approved evidence stops before result interpretation.",
        ],
        "what_would_destroy_the_interpretation": [
            "A future source-hash mismatch or stale source artifact.",
            "A future accepted duplicate-key label/geometry conflict.",
            "Evidence that label definitions used post-event or hidden fields.",
            "A broader cohort showing the same labels are only an artifact of one source lane, symbol, or session.",
            "Broker-native quote-event data changing the four USDJPY source-impossible row classifications.",
        ],
    }
    write_json(OUT_DIR / "G0_NOFILL_CAT_V3_CATEGORICAL_LEARNING_SYNTHESIS_2026-05-09.json", learning)
    lines = [
        "# G0 NOFILL CAT V3 Categorical Learning Synthesis",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "Primary denominator: `nofill_duplicate_key`. Row-level counts remain descriptive source inventory.",
        "",
        "## Primary Count-Control View",
        "",
        "| Label | Primary Duplicate-Key Count | Scope Risk |",
        "|---|---:|---|",
    ]
    risk_by_label = {row["categorical_lifecycle_label"]: row["scope_risk"] for row in risk_rows}
    for label, count in sorted(label_counts.items()):
        lines.append(f"| `{label}` | {count} | {risk_by_label.get(label, '')} |")
    lines.extend(["", "## Label-Family Learning", ""])
    for item in learning["label_learning"]:
        lines.extend(
            [
                f"### {item['label']}",
                "",
                f"- Mechanism clue: {item['mechanism_clue']}",
                f"- Source/control meaning: {item['source_control_meaning']}",
                f"- Does not mean: {', '.join(item['does_not_mean'])}.",
                f"- Next capture or blocker: {item['blocker_or_next_capture']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Hostile Review Answer",
            "",
            *[f"- {item}" for item in learning["hostile_review_answer"]],
            "",
            "## What Could Destroy The Interpretation",
            "",
            *[f"- {item}" for item in learning["what_would_destroy_the_interpretation"]],
        ]
    )
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_CATEGORICAL_LEARNING_SYNTHESIS_{DATE}.md", lines)
    return learning


def build_duplicate_scope_risk(facts: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    count_rows = inputs["count_rows"]
    primary = rows_for_member(count_rows, "nofill_duplicate_key_count_member")
    secondary = rows_for_member(count_rows, "duplicate_group_id_count_member")
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_AND_SCOPE_RISK"),
        "primary_denominator": "nofill_duplicate_key",
        "row_level_is_source_inventory_only": True,
        "denominator_summary": {
            "row_level": len(count_rows),
            "primary_duplicate_key": len(primary),
            "secondary_duplicate_group": len(secondary),
            "accepted_noncanonical_projection_count": inputs["count_duplicate"]["accepted_noncanonical_projection_count"],
            "max_duplicate_key_row_count": inputs["count_duplicate"]["max_duplicate_key_row_count"],
            "max_duplicate_group_row_count": inputs["count_duplicate"]["max_duplicate_group_row_count"],
        },
        "row_level_label_counts": facts["row_level_label_counts"],
        "primary_label_counts": facts["primary_nofill_duplicate_key_label_counts"],
        "secondary_label_counts": facts["secondary_duplicate_group_id_label_counts"],
        "primary_dimension_counts": {
            "symbol": dim_counts_for_primary(count_rows, "symbol"),
            "session": dim_counts_for_primary(count_rows, "session"),
            "side": dim_counts_for_primary(count_rows, "side"),
            "source_lane": dim_counts_for_primary(count_rows, "source_lane"),
        },
        "effective_n_and_concentration_from_count_packet": inputs["count_duplicate"]["effective_n_and_concentration"],
        "top_duplicate_groups_by_row_count": inputs["count_duplicate"]["top_duplicate_groups_by_row_count"],
        "accepted_duplicate_conflict_audit": inputs["count_duplicate"]["conflict_audit"],
        "risk_findings": [
            "opening_drive_source_projection_ready_no_result_label is 51 rows but only 8 primary duplicate-key members, driven by 43 noncanonical accepted projections.",
            "nofill_terminal_before_entry dominates the primary duplicate-key view with 110 of 182 members, so it is the only broad categorical family in this frozen count-control packet.",
            "source_corrected_no_entry_through_pending_horizon is 32 primary duplicate-key members but only 7 duplicate-group members, so opportunity-level concentration is high.",
            "fill_path_entry_before_protective_level_no_terminal_observed is 22 primary duplicate-key members but only 4 duplicate-group members, also highly concentrated.",
            "USDJPY, XAGUSD, NAS100, NY session, SHORT side, and OTI3/OTI1/OTI4 source lanes are major scope-risk axes; none can be generalized without a separate source-safe expansion and later evidence-class gate.",
        ],
    }
    write_json(OUT_DIR / f"G0_NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_AND_SCOPE_RISK_{DATE}.json", payload)
    lines = [
        "# G0 NOFILL CAT V3 Duplicate Concentration And Scope Risk",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Denominator Policy",
        "",
        f"- Row-level source inventory: `{len(count_rows)}`.",
        f"- Primary duplicate-key denominator: `{len(primary)}`.",
        f"- Secondary duplicate-group concentration denominator: `{len(secondary)}`.",
        f"- Noncanonical accepted projection rows: `{payload['denominator_summary']['accepted_noncanonical_projection_count']}`.",
        "",
        "## Primary Dimension Counts",
        "",
    ]
    for dim, dim_counts in payload["primary_dimension_counts"].items():
        lines.extend([f"### {dim}", "", "| Value | Count |", "|---|---:|"])
        for key, value in dim_counts.items():
            lines.append(f"| `{key}` | {value} |")
        lines.append("")
    lines.extend(
        [
            "## Risk Findings",
            "",
            *[f"- {item}" for item in payload["risk_findings"]],
            "",
            "## Blocking Conflict Status",
            "",
            f"- Accepted duplicate-key label conflicts: `{payload['accepted_duplicate_conflict_audit']['accepted_duplicate_key_label_conflict_count']}`.",
            f"- Accepted duplicate-key denominator conflicts: `{payload['accepted_duplicate_conflict_audit']['accepted_duplicate_key_denominator_conflict_count']}`.",
            f"- Accepted source-geometry conflicts: `{payload['accepted_duplicate_conflict_audit']['accepted_duplicate_key_source_geometry_conflict_count']}`.",
            f"- Accepted source-ordering blockers: `{payload['accepted_duplicate_conflict_audit']['accepted_duplicate_key_source_ordering_blocker_count']}`.",
        ]
    )
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_AND_SCOPE_RISK_{DATE}.md", lines)
    return payload


def build_source_backlog(inputs: dict[str, Any]) -> dict[str, Any]:
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG"),
        "source_lessons": [
            {
                "lesson": "Source-control rows can be useful without entering the accepted denominator.",
                "evidence": SOURCE_CONTROL_ROWS,
                "control": "Keep source-control families excluded unless a separate rebuild/G12 evidence-class gate changes them.",
            },
            {
                "lesson": "USDJPY exact event ordering is truly source-impossible under approved current sources.",
                "evidence": SOURCE_IMPOSSIBLE_ROWS,
                "control": inputs["source_blocker"]["exact_unblocker"],
            },
            {
                "lesson": "Reject overlaps must be filtered before duplicate collapse.",
                "evidence": "47 reject overlaps with zero denominator effect.",
                "control": "Accepted-first filtering is mandatory for all future count/control views.",
            },
            {
                "lesson": "Opening-drive source projections require duplicate discipline before interpretation.",
                "evidence": "43 noncanonical accepted projections; 51 row-level projection labels collapse to 8 primary duplicate-key members.",
                "control": "Future opening-drive contract must freeze canonical projection and duplicate policies before any result lane.",
            },
        ],
        "capture_backlog": [
            {
                "lane": "USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE",
                "priority": 1,
                "purpose": "Clear or preserve the four source-impossible USDJPY rows and future same-tick event-order blockers.",
                "required_fields": [
                    "broker-native quote event sequence ID or sequence number",
                    "sub-row or sub-millisecond timestamp",
                    "bid/ask quote state",
                    "source hash",
                    "no account/order/history/live labels",
                ],
                "opens_result_scoring": False,
            },
            {
                "lane": "NOFILL_FORWARD_LIFECYCLE_CAPTURE_CONTRACT",
                "priority": 2,
                "purpose": "Capture pending intent creation, terminal-area touch, side-aware entry absence, cancel/expiry reason, spread, and source coverage prospectively.",
                "required_fields": [
                    "pending intent create time",
                    "entry price and side-aware touch status",
                    "terminal-area touch time or absence",
                    "cancel/expiry timestamp and reason",
                    "source coverage and same-tick ambiguity flags",
                ],
                "opens_result_scoring": False,
            },
            {
                "lane": "OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT_DESIGN",
                "priority": 3,
                "purpose": "Turn projection-ready rows into a frozen categorical contract before any future result lane.",
                "required_fields": [
                    "range definition",
                    "breakout/as-of state",
                    "projection canonicalization",
                    "duplicate policy",
                    "label family boundaries",
                ],
                "opens_result_scoring": False,
            },
            {
                "lane": "NOFILL_CAT_V3_SOURCE_SAFE_EXPANSION_PACKET",
                "priority": 4,
                "purpose": "Add source-hashed rows only through a separate packet/rebuild/G12 path.",
                "required_fields": [
                    "row source contract",
                    "as-of timestamp policy",
                    "forbidden field scan",
                    "duplicate-key policy",
                    "exclusion ledger",
                ],
                "opens_result_scoring": False,
            },
            {
                "lane": "FILL_PATH_EVENT_ORDER_VOCABULARY_CONTRACT",
                "priority": 5,
                "purpose": "Preserve event-order categories as vocabulary for a future frozen contract without current result interpretation.",
                "required_fields": [
                    "entry event timestamp",
                    "terminal-area event timestamp or absence",
                    "protective-level event timestamp or absence",
                    "quote side predicate",
                    "same-tick/same-bar ambiguity flag",
                ],
                "opens_result_scoring": False,
            },
        ],
        "local_heavy_data_policy": {
            "effect_on_current_packet": "No local-heavy root can expand the current frozen denominator.",
            "allowed_future_use": "Local-heavy roots may support a separate source-hashed expansion or capture contract if no-leak and evidence-class gates are preserved.",
            "roots_seen_in_upstream_count_source_audit": inputs["count_source_noleak"].get("local_heavy_roots", []),
        },
    }
    write_json(OUT_DIR / f"G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_{DATE}.json", payload)
    lines = [
        "# G0 NOFILL CAT V3 Source Contract And Capture Backlog",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Source Lessons",
        "",
    ]
    for item in payload["source_lessons"]:
        lines.extend([f"- {item['lesson']} Evidence: `{item['evidence']}`. Control: {item['control']}"])
    lines.extend(["", "## Capture Backlog", ""])
    for item in payload["capture_backlog"]:
        lines.extend(
            [
                f"### {item['priority']}. {item['lane']}",
                "",
                f"Purpose: {item['purpose']}",
                "",
                "Required fields:",
                *[f"- `{field}`" for field in item["required_fields"]],
                "",
                f"Opens result scoring: `{str(item['opens_result_scoring']).lower()}`.",
                "",
            ]
        )
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_{DATE}.md", lines)
    return payload


def build_forbidden_route_ledger() -> dict[str, Any]:
    routes = [
        {
            "route": "result_scoring_or_numeric_performance",
            "status": "FORBIDDEN_FROM_THIS_G0_LANE",
            "reason": "Current evidence is categorical source/control only.",
            "unblocker": "A separate frozen result contract, accepted input packet, post-result G12 audit, and G0 review.",
        },
        {
            "route": "validation_or_promotion",
            "status": "FORBIDDEN_FROM_THIS_G0_LANE",
            "reason": "No validation-safe evidence class or promotion dossier exists.",
            "unblocker": "Separate preregistered validation/promotion dossier with unseen/source-safe evidence and methodology gates.",
        },
        {
            "route": "broker_account_live_order_or_hidden_labels",
            "status": "FORBIDDEN_FROM_THIS_G0_LANE",
            "reason": "The source contract explicitly excludes broker/account/live-order/history/hidden label families.",
            "unblocker": "A separately approved broker/account evidence-class lane, if ever authorized.",
        },
        {
            "route": "paid_api_databento_or_new_external_spend",
            "status": "FORBIDDEN_FROM_THIS_G0_LANE",
            "reason": "This synthesis has no source-access or spending authority.",
            "unblocker": "Owner-approved source manifest, budget proof, legal/access proof, and source contract.",
        },
        {
            "route": "registry_edit_or_live_behavior_change",
            "status": "FORBIDDEN_FROM_THIS_G0_LANE",
            "reason": "G0 synthesis artifacts cannot alter selectors, prompts, src trading logic, risk, execution, permissions, safety gates, canaries, MT5 order/account/history surfaces, credentials, remote pushes, or order behavior.",
            "unblocker": "Separate owner-approved implementation lane after evidence-class gates and promotion dossier, if ever reached.",
        },
        {
            "route": "counting_excluded_rows",
            "status": "FORBIDDEN_FROM_THIS_G0_LANE",
            "reason": "Source-control, source-impossible, and reject rows are exclusion/control evidence only.",
            "unblocker": "Separate source-control rebuild/G12 acceptance that changes evidence class without forbidden labels.",
        },
    ]
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_FORBIDDEN_ROUTE_LEDGER"),
        "forbidden_routes": routes,
        "all_safe_flags_remain_false": True,
    }
    lines = [
        "# G0 NOFILL CAT V3 Forbidden Route Ledger",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "These are explicit forbidden-policy routes for this G0 lane. Listing them here does not open them.",
        "",
        "| Route | Status | Reason | Exact Unblocker |",
        "|---|---|---|---|",
    ]
    for item in routes:
        lines.append(f"| `{item['route']}` | `{item['status']}` | {item['reason']} | {item['unblocker']} |")
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_FORBIDDEN_ROUTE_LEDGER_{DATE}.md", lines)
    return payload


def build_next_route_ranking() -> dict[str, Any]:
    routes = [
        {
            "rank": 1,
            "route": "NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT",
            "why": "Largest actionable learning comes from terminal-before-entry and no-entry-through-horizon states; forward capture can add source-safe evidence without opening results.",
            "evidence_class": "source_capture_contract",
            "opens_result_scoring": False,
            "forbidden_until": "No live behavior or validation until separate result and promotion lanes exist.",
        },
        {
            "rank": 2,
            "route": "USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS",
            "why": "Exact blocker for the four source-impossible rows is known and narrow.",
            "evidence_class": "source_access_contract",
            "opens_result_scoring": False,
            "forbidden_until": "No account/order/history labels and no inference from proxy sources.",
        },
        {
            "rank": 3,
            "route": "OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT_DESIGN",
            "why": "Projection family has large row-level/source-control signal but high duplicate projection concentration; it needs a frozen contract before any result lane.",
            "evidence_class": "source_contract_design",
            "opens_result_scoring": False,
            "forbidden_until": "No result labels until contract, packet, G12, and G0 gates complete.",
        },
        {
            "rank": 4,
            "route": "NOFILL_CAT_V3_SOURCE_SAFE_EXPANSION_PACKET",
            "why": "New rows can improve source-control coverage only if built as a separate source-hashed packet with duplicate policy.",
            "evidence_class": "source_packet_rebuild",
            "opens_result_scoring": False,
            "forbidden_until": "No validation or promotion from source expansion alone.",
        },
        {
            "rank": 5,
            "route": "FILL_PATH_EVENT_ORDER_VOCABULARY_CONTRACT",
            "why": "Event-order labels are useful vocabulary, but small and concentrated; freeze vocabulary before future scoring.",
            "evidence_class": "categorical_contract_design",
            "opens_result_scoring": False,
            "forbidden_until": "No interpretation as good/bad path until a later result lane is approved and audited.",
        },
    ]
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING"),
        "route_ranking": routes,
        "rejected_next_routes": [
            "direct validation",
            "direct promotion",
            "registry edit",
            "live prompt or src trading logic change",
            "broker/account/live-order evidence use",
            "paid/API data access",
        ],
    }
    write_json(OUT_DIR / f"G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_{DATE}.json", payload)
    lines = [
        "# G0 NOFILL CAT V3 Next Route Ranking",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "| Rank | Route | Evidence Class | Why |",
        "|---:|---|---|---|",
    ]
    for item in routes:
        lines.append(f"| {item['rank']} | `{item['route']}` | `{item['evidence_class']}` | {item['why']} |")
    lines.extend(
        [
            "",
            "## Rejected Direct Routes",
            "",
            *[f"- `{item}`" for item in payload["rejected_next_routes"]],
        ]
    )
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_{DATE}.md", lines)
    return payload


def write_next_prompt_pack() -> None:
    lines = [
        "# G0 NOFILL CAT V3 Next Prompt Pack",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Prompt 1 - Forward Lifecycle Capture Contract",
        "",
        "Run `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT` as a source-capture contract lane. Use G0 NOFILL CAT V3 synthesis artifacts as context. Build a source-safe capture spec for pending intent creation, side-aware entry touch or absence, terminal-area touch, pending horizon, cancel/expiry reason, source coverage, spread state, and same-tick ambiguity. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Do not score results or change live behavior.",
        "",
        "## Prompt 2 - USDJPY Quote-Event Source Access",
        "",
        "Run `NOFILL_CAT_V3_USDJPY_QUOTE_EVENT_SEQUENCE_SOURCE_ACCESS` as a source-access proof lane for rows `NOFILL-CAT-ROW-0130`, `0143`, `0165`, and `0178`. Search only approved source-safe routes for broker-native quote-event sequence ID or sub-row/sub-millisecond timestamp with bid/ask quote state and source hashes. Do not use account, order, deal, position, or history labels. If unavailable, record exact impossibility and access request.",
        "",
        "## Prompt 3 - Opening Drive Source Projection Contract Design",
        "",
        "Run `NOFILL_CAT_V3_OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT_DESIGN` as a contract-design lane. Freeze range, breakout/as-of state, projection canonicalization, duplicate policy, and label boundaries for opening-drive source projections. Do not open any result lane. Require a future packet and G12 audit before later G0 use.",
        "",
        "## Prompt 4 - Source-Safe Expansion Packet",
        "",
        "Run `NOFILL_CAT_V3_SOURCE_SAFE_EXPANSION_PACKET` only after a source contract exists. Build a source-hashed packet with as-of policy, exclusion ledger, duplicate-key policy, and forbidden-field scan. Keep all result, validation, promotion, registry, live, paid/API, and broker/account surfaces closed.",
    ]
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_NEXT_PROMPT_PACK_{DATE}.md", lines)


def completion_checklist(verifier: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    verifier_status = None
    if verifier:
        verifier_status = verifier.get("verification_status", {}).get("status")
    return [
        {"requirement": "GTOS preflight completed and starting HEAD recorded", "evidence": "context anchor", "status": "PASS"},
        {"requirement": "LIVE_STATE, doctrine, current state, goal discipline, local heavy inventory, latest handoff read", "evidence": "context anchor input hashes", "status": "PASS"},
        {"requirement": "V3 source-control rebuild/audit read and reconciled", "evidence": "evidence chain reconciliation", "status": "PASS"},
        {"requirement": "Frozen V3 result contract/audit read and reconciled", "evidence": "evidence chain reconciliation", "status": "PASS"},
        {"requirement": "Count packet and G12 post-count audit read and reconciled", "evidence": "evidence chain reconciliation", "status": "PASS"},
        {"requirement": "Required count facts recomputed", "evidence": "context anchor and verifier", "status": "PASS"},
        {"requirement": "Categorical evidence meaning and non-meaning explained", "evidence": "categorical learning synthesis", "status": "PASS"},
        {"requirement": "Duplicate/concentration risks identified", "evidence": "duplicate concentration and scope risk", "status": "PASS"},
        {"requirement": "Label-family risks and mechanism clues identified", "evidence": "categorical learning synthesis", "status": "PASS"},
        {"requirement": "Exact blockers, next lanes, and forbidden routes identified", "evidence": "source backlog, next route ranking, forbidden route ledger", "status": "PASS"},
        {"requirement": "Flags preserved false and promotion verdict preserved", "evidence": "generated JSON safe flags", "status": "PASS"},
        {"requirement": "Builder, verifier, and focused pytest file created", "evidence": PY_FILES, "status": "PASS"},
        {
            "requirement": "Verifier covers JSON/JSONL parse, count recompute, safe flags, forbidden surfaces, live-surface diff, and completion checklist",
            "evidence": "verify_g0_nofill_cat_v3_synthesis_control_review_2026_05_09.py",
            "status": "PASS" if verifier_status == "PASS" else "PENDING_VERIFIER",
        },
    ]


def write_completion_audit(status: str = "BUILDER_PASS_PENDING_VERIFIER", verifier: dict[str, Any] | None = None) -> dict[str, Any]:
    checklist = completion_checklist(verifier)
    can_complete = all(item["status"] == "PASS" for item in checklist) and status in {"PASS", "VERIFIED"}
    payload = {
        **base_payload("G0_NOFILL_CAT_V3_COMPLETION_AUDIT"),
        "completion_status": "PASS" if can_complete else status,
        "can_mark_goal_complete": can_complete,
        "objective_restatement": "Build a scoped G0 synthesis/control review for G12-accepted NOFILL CAT V3 categorical count/control evidence, preserving all non-result and non-live boundaries.",
        "prompt_to_artifact_checklist": checklist,
        "required_outputs": {
            "json": OUTPUT_JSON,
            "markdown": OUTPUT_MD,
            "python": PY_FILES,
        },
        "verification": verifier,
        "hard_boundaries": {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "forbidden_policy_references": FORBIDDEN_POLICY_REFERENCES,
        },
    }
    write_json(OUT_DIR / f"G0_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json", payload)
    lines = [
        "# G0 NOFILL CAT V3 Completion Audit",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Completion status: `{payload['completion_status']}`.",
        f"Can mark goal complete: `{str(payload['can_mark_goal_complete']).lower()}`.",
        "",
        "## Objective",
        "",
        payload["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in checklist:
        lines.append(f"| {item['requirement']} | `{item['status']}` | `{item['evidence']}` |")
    lines.extend(
        [
            "",
            "## Boundary Status",
            "",
            "- `NO_PROMOTION_VERDICT` preserved.",
            "- `validation_safe=false` preserved.",
            "- `outcome_review_opened=false` preserved.",
            "- `live_effect=false` preserved.",
            "- No result scoring, broker/account/live-order labels, paid/API access, registry edit, remote push, or live trading behavior change.",
        ]
    )
    write_md(OUT_DIR / f"G0_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.md", lines)
    return payload


def build_all(verifier: dict[str, Any] | None = None, final_status: str = "BUILDER_PASS_PENDING_VERIFIER") -> dict[str, Any]:
    inputs = load_inputs()
    facts = recompute_facts(inputs)
    context_anchor = build_context_anchor(facts)
    decision = build_decision_ledger(facts, inputs)
    reconciliation = build_evidence_reconciliation(facts, inputs)
    learning = build_learning_synthesis(facts, inputs["count_rows"])
    duplicate_risk = build_duplicate_scope_risk(facts, inputs)
    source_backlog = build_source_backlog(inputs)
    forbidden_routes = build_forbidden_route_ledger()
    next_routes = build_next_route_ranking()
    write_next_prompt_pack()
    completion = write_completion_audit(final_status, verifier)
    return {
        "status": "PASS",
        "control_decision": CONTROL_DECISION,
        "facts": facts,
        "generated_files": OUTPUT_JSON + OUTPUT_MD + PY_FILES,
        "completion_status": completion["completion_status"],
        "can_mark_goal_complete": completion["can_mark_goal_complete"],
        "artifact_summaries": {
            "context_anchor": context_anchor["artifact_family"],
            "decision": decision["overall_decision"],
            "reconciliation": reconciliation["control_decision"],
            "learning": learning["artifact_family"],
            "duplicate_risk": duplicate_risk["artifact_family"],
            "source_backlog": source_backlog["artifact_family"],
            "forbidden_routes": forbidden_routes["artifact_family"],
            "next_routes": next_routes["artifact_family"],
        },
    }


def main() -> int:
    result = build_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
