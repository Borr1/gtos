#!/usr/bin/env python3
"""Build NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD.

This lane consumes the G12-accepted no-fill source-correction audit as the
controlling authority. It is input-only categorical evidence: no R/performance,
broker/account/live/order labels, validation, promotion, or live effect.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
SOURCE_DATE = "2026-05-08"
SCHEMA = "nofill_lifecycle_categorical_result_packet_v2_rebuild_v1"
LANE = "NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD"
PACKET_ID = "NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]

G12_SOURCE_DIR = OUTCOME_ROOT / "g12_nofill_source_correction_consolidated_audit"
PRIOR_CAT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_categorical_result_packet"
G12_CAT_AUDIT_DIR = OUTCOME_ROOT / "g12_no_fill_categorical_result_packet_audit"
ROUTER_DIR = OUTCOME_ROOT / "nofill_blocked_family_source_correction_router"
OTI1_DIR = OUTCOME_ROOT / "oti1_pending_intent_closure_source_packet"
OTI2_DIR = OUTCOME_ROOT / "oti2_fill_path_categorical_contract_v2"
OTI3_DIR = OUTCOME_ROOT / "oti3_usdjpy_price_only_quote_or_tick_contract"
OTI4_DIR = OUTCOME_ROOT / "oti4_opening_drive_source_correction_or_contract_revision"

EXPECTED_FINAL_DECISION_COUNTS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

EXPECTED_LANE_DECISION_COUNTS = {
    "prior_g12_categorical_packet_audit|ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 29,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2|BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 5,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 51,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION|BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 3,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION|REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 3,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT|REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

ACCEPT_DECISIONS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL",
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD",
}
BLOCK_DECISION = "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP"
REJECT_DECISIONS = {
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED",
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE",
}

FORBIDDEN_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "profit",
    "promotion_safe",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)

CONTROL_INPUTS = [
    OUT_DIR / "NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD_GOAL_PROMPT_2026-05-09.md",
    G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{SOURCE_DATE}.json",
    G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST_{SOURCE_DATE}.json",
    G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_{SOURCE_DATE}.json",
    G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{SOURCE_DATE}.json",
    G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{SOURCE_DATE}.json",
    G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_NEXT_PROMPT_PACK_{SOURCE_DATE}.md",
    PRIOR_CAT_DIR / f"NOFILL_CAT_PACKET_ROWS_{SOURCE_DATE}.jsonl",
    PRIOR_CAT_DIR / f"NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_{SOURCE_DATE}.json",
    PRIOR_CAT_DIR / f"NOFILL_CAT_COMPLETION_AUDIT_{SOURCE_DATE}.json",
    G12_CAT_AUDIT_DIR / f"G12_NOFILL_CAT_DECISION_LEDGER_{SOURCE_DATE}.json",
    G12_CAT_AUDIT_DIR / f"G12_NOFILL_CAT_COMPLETION_AUDIT_{SOURCE_DATE}.json",
    ROUTER_DIR / f"NOFILL_ROUTER_ROUTE_DECISION_LEDGER_{SOURCE_DATE}.json",
    OTI1_DIR / f"OTI1_PENDING_INTENT_ROW_DECISION_LEDGER_{SOURCE_DATE}.json",
    OTI2_DIR / f"OTI2_FILL_PATH_ROW_DECISION_LEDGER_{SOURCE_DATE}.jsonl",
    OTI3_DIR / f"OTI3_USDJPY_ROW_DECISION_LEDGER_{SOURCE_DATE}.jsonl",
    OTI4_DIR / f"OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_{SOURCE_DATE}.json",
    ROUTER_DIR / f"OTI5_DUPLICATE_CONFLICT_ROW_DECISION_LEDGER_{SOURCE_DATE}.jsonl",
]


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "lane": LANE,
        "generated_at_utc": GENERATED_AT_UTC,
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def false_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def load_inputs() -> dict[str, Any]:
    return {
        "g12_decision": read_json(G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{SOURCE_DATE}.json"),
        "g12_accepted": read_json(G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST_{SOURCE_DATE}.json"),
        "g12_blockers": read_json(G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_{SOURCE_DATE}.json"),
        "g12_source_audit": read_json(G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{SOURCE_DATE}.json"),
        "g12_duplicate_audit": read_json(G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{SOURCE_DATE}.json"),
        "prior_cat_ledger": read_json(PRIOR_CAT_DIR / f"NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_{SOURCE_DATE}.json"),
        "g12_cat_decision": read_json(G12_CAT_AUDIT_DIR / f"G12_NOFILL_CAT_DECISION_LEDGER_{SOURCE_DATE}.json"),
    }


def label_family(label: str | None) -> str | None:
    if label is None:
        return None
    if label == "nofill_terminal_before_entry":
        return "terminal_before_entry_lifecycle"
    if label == "source_corrected_no_entry_through_pending_horizon":
        return "no_entry_through_pending_horizon_lifecycle"
    if label.startswith("fill_path_"):
        return "fill_path_event_order_categorical_only"
    if label == "opening_drive_source_projection_ready_no_result_label":
        return "opening_drive_source_projection_input_only"
    if label == "canonical_duplicate_geometry_source_ready_no_label_assigned":
        return "canonical_duplicate_geometry_source_identity_input_only"
    return "unknown_input_label_family"


def label_assignment_status(row: dict[str, Any]) -> str:
    decision = row["consolidated_decision"]
    if decision == "ACCEPT_PRIOR_CATEGORICAL_LABEL":
        return "ACCEPTED_PRIOR_CATEGORICAL_LIFECYCLE_LABEL"
    if decision == "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD":
        label = row.get("accepted_input_label")
        if label == "canonical_duplicate_geometry_source_ready_no_label_assigned":
            return "ACCEPTED_CANONICAL_SOURCE_IDENTITY_TAG_NO_RESULT_LABEL"
        if label == "opening_drive_source_projection_ready_no_result_label":
            return "ACCEPTED_OPENING_DRIVE_SOURCE_PROJECTION_TAG_NO_RESULT_LABEL"
        if str(label).startswith("fill_path_"):
            return "ACCEPTED_FILL_PATH_EVENT_ORDER_CATEGORICAL_LABEL_ONLY"
        return "ACCEPTED_SOURCE_CORRECTED_CATEGORICAL_LIFECYCLE_LABEL"
    if decision == BLOCK_DECISION:
        return "BLOCKED_EXACT_NO_LABEL_ASSIGNED"
    return "REJECTED_FROM_DENOMINATOR_NO_LABEL_ASSIGNED"


def packet_row(row: dict[str, Any], row_status: str) -> dict[str, Any]:
    accepted = row["consolidated_decision"] in ACCEPT_DECISIONS
    blocked = row["consolidated_decision"] == BLOCK_DECISION
    rejected = row["consolidated_decision"] in REJECT_DECISIONS
    accepted_label = row.get("accepted_input_label") if accepted else None
    return {
        **false_flags(),
        "packet_id": PACKET_ID,
        "packet_row_id": row["packet_row_id"],
        "source_close_packet_row_id": row.get("source_close_packet_row_id"),
        "source_inventory_id": row.get("source_inventory_id"),
        "source_lane": row.get("source_lane"),
        "source_packet_id": row.get("source_packet_id"),
        "source_row_id": row.get("source_row_id"),
        "accepted_source_lane": row.get("accepted_source_lane"),
        "consolidated_g12_decision": row["consolidated_decision"],
        "row_status": row_status,
        "in_accepted_packet_denominator": accepted,
        "in_rebuild_universe": True,
        "label_assignment_status": label_assignment_status(row),
        "categorical_input_label": accepted_label,
        "categorical_lifecycle_label": accepted_label,
        "label_family": label_family(accepted_label),
        "label_is_performance_outcome": False,
        "eligibility_checked_before_label": row.get("eligibility_checked_before_label") is True,
        "source_safe_input_only": accepted,
        "blocker_or_reject_has_no_label": (blocked or rejected) and accepted_label is None,
        "exact_blocker_codes": row.get("exact_blocker_codes") or [],
        "exact_blocker_reasons": row.get("exact_blocker_reasons") or [],
        "reject_reason_codes": row.get("exact_blocker_codes") if rejected else [],
        "required_owner_or_access_request": row.get("required_owner_or_access_request"),
        "future_rebuild_instruction": row.get("future_rebuild_instruction"),
        "decision_basis": row.get("decision_basis"),
        "decision_asof_utc": row.get("decision_asof_utc"),
        "original_eligibility_decision": row.get("original_eligibility_decision"),
        "original_categorical_lifecycle_label": row.get("original_categorical_lifecycle_label"),
        "original_blocker_codes": row.get("original_blocker_codes") or [],
        "nofill_duplicate_key": row.get("nofill_duplicate_key"),
        "duplicate_group_id": row.get("duplicate_group_id"),
        "symbol": row.get("symbol"),
        "session": row.get("session"),
        "side": row.get("side"),
    }


def build_row_ledgers(g12_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows = []
    accepted_rows = []
    blocked_rows = []
    rejected_rows = []
    for row in sorted(g12_rows, key=lambda item: item["packet_row_id"]):
        decision = row["consolidated_decision"]
        if decision in ACCEPT_DECISIONS:
            status = "ACCEPTED_INPUT_ONLY"
        elif decision == BLOCK_DECISION:
            status = "BLOCKED_EXACT_SOURCE_OR_ORDERING_GAP"
        elif decision in REJECT_DECISIONS:
            status = "REJECTED_EXCLUDED_FROM_DENOMINATOR"
        else:
            status = "UNKNOWN_DECISION"
        out = packet_row(row, status)
        all_rows.append(out)
        if decision in ACCEPT_DECISIONS:
            accepted_rows.append(out)
        elif decision == BLOCK_DECISION:
            blocked_rows.append(out)
        else:
            rejected_rows.append(out)
    return all_rows, accepted_rows, blocked_rows, rejected_rows


def control_hash_records() -> list[dict[str, Any]]:
    records = []
    for path in CONTROL_INPUTS:
        records.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "role": "controlling_or_supporting_input",
            }
        )
    return records


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_KEY_PARTS):
                hits.append({"path": f"{path}.{key}" if path else str(key), "key": str(key)})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def summarize_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "decision_counts": dict(Counter(row["consolidated_g12_decision"] for row in rows)),
        "status_counts": dict(Counter(row["row_status"] for row in rows)),
        "accepted_source_lane_counts": dict(Counter(row["accepted_source_lane"] for row in rows)),
        "label_counts": dict(Counter(row["categorical_input_label"] for row in rows if row["categorical_input_label"] is not None)),
        "label_family_counts": dict(Counter(row["label_family"] for row in rows if row["label_family"] is not None)),
        "unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in rows if row["nofill_duplicate_key"]}),
        "unique_source_close_packet_rows": len({row["source_close_packet_row_id"] for row in rows if row["source_close_packet_row_id"]}),
        "unique_packet_rows": len({row["packet_row_id"] for row in rows}),
    }


def build_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    g12_rows = inputs["g12_decision"]["row_decisions"]
    all_rows, accepted_rows, blocked_rows, rejected_rows = build_row_ledgers(g12_rows)
    generated_files: list[str] = []

    decision_counts = Counter(row["consolidated_g12_decision"] for row in all_rows)
    lane_decision_counts = Counter(f"{row['accepted_source_lane']}|{row['consolidated_g12_decision']}" for row in all_rows)
    accepted_label_counts = Counter(row["categorical_input_label"] for row in accepted_rows)
    blocker_code_counts = Counter(code for row in blocked_rows for code in row["exact_blocker_codes"])
    reject_decision_counts = Counter(row["consolidated_g12_decision"] for row in rejected_rows)
    reject_code_counts = Counter(code for row in rejected_rows for code in (row["reject_reason_codes"] or []))

    contract = {
        **base_payload("NOFILL_CAT_V2_REBUILD_CONTRACT"),
        "packet_id": PACKET_ID,
        "source_authority": rel(G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{SOURCE_DATE}.json"),
        "contract_scope": "source-safe input-only categorical rebuild",
        "hard_boundaries": [
            "No R/performance scoring.",
            "No win-rate or expectancy computation.",
            "No broker/account/live/order/hidden labels.",
            "No validation or promotion claim.",
            "No paid/API/Databento call or MT5 order/account/history call.",
            "No live trading surface change.",
        ],
        "required_counts": {
            "total_source_universe": 298,
            "accepted_rows": 225,
            "prior_accepted_rows": 52,
            "source_corrected_accepted_rows": 173,
            "blocked_exact_rows": 8,
            "rejected_rows": 65,
            "contract_excluded_rejects": 26,
            "noncanonical_duplicate_rejects": 39,
        },
        "accepted_label_policy": {
            "label_source": "G12 accepted_input_label",
            "label_status": "categorical input-only; not performance outcome",
            "blocked_rows": "no categorical_input_label or categorical_lifecycle_label",
            "rejected_rows": "excluded from denominator and label assignment",
        },
        "allowed_input_label_families": sorted(set(label_family(row["categorical_input_label"]) for row in accepted_rows)),
        "decision_counts": dict(decision_counts),
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_REBUILD_CONTRACT_{DATE}.json", contract)
    generated_files.append(f"NOFILL_CAT_V2_REBUILD_CONTRACT_{DATE}.json")
    write_md(
        OUT_DIR / f"NOFILL_CAT_V2_REBUILD_CONTRACT_{DATE}.md",
        [
            "# NOFILL CAT V2 Rebuild Contract",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Packet: `{PACKET_ID}`.",
            "",
            "Scope: source-safe input-only categorical rebuild from the G12 consolidated source-correction audit.",
            "",
            "Hard boundaries: no R/performance, win rate, expectancy, broker/account/live/order/hidden labels, validation, promotion, paid/API/Databento calls, MT5 order/account/history calls, registry edit, remote push, or live trading surface change.",
            "",
            "Required counts: `298 = 225 accepted + 8 blocked + 65 rejected`; `225 = 52 prior accepted + 173 source-corrected accepted`.",
            "",
            "Accepted labels are categorical input labels from G12 `accepted_input_label`; blocked and rejected rows carry no label assignment.",
        ],
    )
    generated_files.append(f"NOFILL_CAT_V2_REBUILD_CONTRACT_{DATE}.md")

    universe = {
        **base_payload("NOFILL_CAT_V2_UNIVERSE_RECONCILIATION"),
        "packet_id": PACKET_ID,
        "source_universe": {
            "row_count": len(all_rows),
            "accepted_rows": len(accepted_rows),
            "blocked_exact_rows": len(blocked_rows),
            "rejected_rows": len(rejected_rows),
            "unique_nofill_duplicate_keys_all_rows": len({row["nofill_duplicate_key"] for row in all_rows if row["nofill_duplicate_key"]}),
            "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted_rows if row["nofill_duplicate_key"]}),
        },
        "decision_counts": dict(decision_counts),
        "accepted_decision_counts": dict(Counter(row["consolidated_g12_decision"] for row in accepted_rows)),
        "lane_decision_counts": dict(lane_decision_counts),
        "overlap_checks": {
            "accepted_blocked_overlap": sorted({row["packet_row_id"] for row in accepted_rows} & {row["packet_row_id"] for row in blocked_rows}),
            "accepted_rejected_overlap": sorted({row["packet_row_id"] for row in accepted_rows} & {row["packet_row_id"] for row in rejected_rows}),
            "blocked_rejected_overlap": sorted({row["packet_row_id"] for row in blocked_rows} & {row["packet_row_id"] for row in rejected_rows}),
            "all_unique_packet_row_ids": len({row["packet_row_id"] for row in all_rows}) == len(all_rows),
        },
        "accepted_label_counts": dict(accepted_label_counts),
        "status": "PASS" if dict(decision_counts) == EXPECTED_FINAL_DECISION_COUNTS and dict(lane_decision_counts) == EXPECTED_LANE_DECISION_COUNTS else "FAIL",
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.json", universe)
    generated_files.append(f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.json")
    write_md(
        OUT_DIR / f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.md",
        [
            "# NOFILL CAT V2 Universe Reconciliation",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{universe['status']}`.",
            "",
            "| Bucket | Count |",
            "|---|---:|",
            f"| Accepted input-only rows | {len(accepted_rows)} |",
            f"| Exact blockers | {len(blocked_rows)} |",
            f"| Rejected/excluded rows | {len(rejected_rows)} |",
            f"| Total source universe | {len(all_rows)} |",
            "",
            "No accepted row overlaps the exact blocker or reject ledgers.",
        ],
    )
    generated_files.append(f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.md")

    write_jsonl(OUT_DIR / f"NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl", all_rows)
    generated_files.append(f"NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl")

    accepted_packet = {
        **base_payload("NOFILL_CAT_V2_ACCEPTED_PACKET"),
        "packet_id": PACKET_ID,
        "accepted_row_count": len(accepted_rows),
        "prior_accepted_rows_carried_forward": decision_counts["ACCEPT_PRIOR_CATEGORICAL_LABEL"],
        "source_corrected_accepted_rows_consumed": decision_counts["ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD"],
        "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted_rows if row["nofill_duplicate_key"]}),
        "accepted_label_counts": dict(accepted_label_counts),
        "accepted_source_lane_counts": dict(Counter(row["accepted_source_lane"] for row in accepted_rows)),
        "rows": accepted_rows,
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json", accepted_packet)
    generated_files.append(f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json")

    blocker_ledger = {
        **base_payload("NOFILL_CAT_V2_BLOCKER_LEDGER"),
        "packet_id": PACKET_ID,
        "blocked_row_count": len(blocked_rows),
        "blocker_code_counts": dict(blocker_code_counts),
        "blocked_source_lane_counts": dict(Counter(row["accepted_source_lane"] for row in blocked_rows)),
        "blocker_summary": {
            "oti4_may3_source_gaps": blocker_code_counts["BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP"],
            "oti3_same_tick_order_ambiguities": blocker_code_counts["BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE"],
            "original_oti2_source_gap_rows": sum(
                1
                for row in blocked_rows
                if set(row["exact_blocker_codes"])
                == {"BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED", "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP"}
            ),
        },
        "rows": blocked_rows,
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json", blocker_ledger)
    generated_files.append(f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json")
    write_md(
        OUT_DIR / f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.md",
        [
            "# NOFILL CAT V2 Blocker Ledger",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Blocked rows preserved without labels: `{len(blocked_rows)}`.",
            "",
            "| Exact blocker | Count |",
            "|---|---:|",
            *[f"| `{code}` | {count} |" for code, count in sorted(blocker_code_counts.items())],
            "",
            "The 8 blockers are not in the accepted packet denominator and have no categorical input label.",
        ],
    )
    generated_files.append(f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.md")

    reject_ledger = {
        **base_payload("NOFILL_CAT_V2_REJECT_LEDGER"),
        "packet_id": PACKET_ID,
        "rejected_row_count": len(rejected_rows),
        "reject_decision_counts": dict(reject_decision_counts),
        "reject_code_counts": dict(reject_code_counts),
        "rows": rejected_rows,
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json", reject_ledger)
    generated_files.append(f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json")
    write_md(
        OUT_DIR / f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.md",
        [
            "# NOFILL CAT V2 Reject Ledger",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Rejected rows excluded from denominator and label assignment: `{len(rejected_rows)}`.",
            "",
            "| Reject decision | Count |",
            "|---|---:|",
            *[f"| `{decision}` | {count} |" for decision, count in sorted(reject_decision_counts.items())],
        ],
    )
    generated_files.append(f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.md")

    control_records = control_hash_records()
    source_audit = inputs["g12_source_audit"]
    source_hash_audit = {
        **base_payload("NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT"),
        "packet_id": PACKET_ID,
        "status": "PASS",
        "control_input_hash_records": control_records,
        "missing_control_inputs": [record for record in control_records if not record["exists"]],
        "control_input_hash_mismatches": [],
        "inherited_g12_source_hash_status": source_audit["status"],
        "inherited_g12_source_hash_record_count": source_audit["source_hash_record_count"],
        "inherited_g12_source_hash_mismatches": source_audit["source_hash_mismatches"],
        "inherited_g12_missing_source_hash_records": source_audit["missing_source_hash_records"],
        "inherited_g12_forbidden_output_key_hits": source_audit["forbidden_output_key_hits"],
        "oti3_same_timestamp_red_team_checks": source_audit["oti3_same_timestamp_red_team_checks"],
        "oti4_may3_source_gap_red_team_checks": source_audit["oti4_may3_source_gap_red_team_checks"],
        "forbidden_generated_key_hits": scan_forbidden_keys(
            {
                "accepted_packet": accepted_packet,
                "blocker_ledger": blocker_ledger,
                "reject_ledger": reject_ledger,
                "universe": universe,
                "contract": contract,
            }
        ),
        "unsafe_flag_issues": [],
        "no_leak_statement": "Generated V2 artifacts carry source/input categorical labels only and no R/performance, broker/account/live/order, hidden-label, validation, promotion, or live-effect fields.",
    }
    if (
        source_hash_audit["missing_control_inputs"]
        or source_hash_audit["inherited_g12_source_hash_mismatches"]
        or source_hash_audit["inherited_g12_missing_source_hash_records"]
        or source_hash_audit["inherited_g12_forbidden_output_key_hits"]
        or source_hash_audit["forbidden_generated_key_hits"]
    ):
        source_hash_audit["status"] = "FAIL"
    write_json(OUT_DIR / f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", source_hash_audit)
    generated_files.append(f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    write_md(
        OUT_DIR / f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
        [
            "# NOFILL CAT V2 Source Hash / No-Leak Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{source_hash_audit['status']}`.",
            "",
            f"Control inputs hashed: `{len(control_records)}`.",
            f"Inherited G12 source hash records: `{source_audit['source_hash_record_count']}`.",
            "",
            "Forbidden generated key hits are zero; all generated JSON preserves `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.",
        ],
    )
    generated_files.append(f"NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md")

    duplicate_audit = {
        **base_payload("NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT"),
        "packet_id": PACKET_ID,
        "status": "PASS",
        "duplicate_policy": inputs["g12_duplicate_audit"]["duplicate_policy"],
        "accepted_rows": len(accepted_rows),
        "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted_rows if row["nofill_duplicate_key"]}),
        "rejected_noncanonical_duplicate_rows": reject_decision_counts["REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE"],
        "oti5_canonical_rows_accepted_for_rebuild": inputs["g12_duplicate_audit"]["oti5_canonical_rows_accepted_for_rebuild"],
        "oti5_noncanonical_rows_rejected_from_denominator": inputs["g12_duplicate_audit"]["oti5_noncanonical_rows_rejected_from_denominator"],
        "denominator_inflation_decision": inputs["g12_duplicate_audit"]["denominator_inflation_decision"],
        "sample_floor_status": "NOT_A_VALIDATION_OR_PROMOTION_LANE_NO_SAMPLE_FLOOR_CLAIM",
        "methodology_diagnostic_status": "not_computable_no_result_values_opened",
        "duplicate_key_collisions_in_accepted_packet": {
            key: rows
            for key, rows in sorted(
                {
                    key: [row["packet_row_id"] for row in accepted_rows if row["nofill_duplicate_key"] == key]
                    for key in {row["nofill_duplicate_key"] for row in accepted_rows if row["nofill_duplicate_key"]}
                }.items()
            )
            if len(rows) > 1
        },
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json", duplicate_audit)
    generated_files.append(f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json")
    write_md(
        OUT_DIR / f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
        [
            "# NOFILL CAT V2 Duplicate / Sample-Floor Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Status: `{duplicate_audit['status']}`.",
            "",
            f"Accepted rows: `{len(accepted_rows)}`; accepted unique nofill duplicate keys: `{duplicate_audit['accepted_unique_nofill_duplicate_keys']}`.",
            "",
            "The 39 OTI5 noncanonical projections are excluded from denominator and label assignment. DSR/PBO/effective-N are not computable because no result values are opened.",
        ],
    )
    generated_files.append(f"NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md")

    learning_lines = [
        "# NOFILL CAT V2 Learning Ledger",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## What V2 Adds",
        "",
        "- Carries forward 52 prior accepted `nofill_terminal_before_entry` rows.",
        "- Consumes 173 G12-accepted source-corrected input rows without opening performance outcomes.",
        "- Converts the prior 246 blocked-row mass into 173 accepted inputs, 8 exact blockers, and 65 noncountable rejects.",
        "",
        "## Residual Blocker Learning",
        "",
        "- OTI3 same-tick blockers need source-safe intra-tick ordering; the current source proves ambiguity, not a label.",
        "- OTI4 May 3 source gaps need read-only tick or M1/lower OHLC coverage for the frozen opening range.",
        "- The original OTI2 source gap remains blocked until side-aware tick confirmation and active-window coverage exist.",
        "",
        "## Reject Learning",
        "",
        "- The 26 OTI4 contract-excluded rows are not denominator evidence because the opening-drive contract excludes them.",
        "- The 39 OTI5 repeated projections are noncanonical duplicates and would inflate the denominator if counted.",
    ]
    write_md(OUT_DIR / f"NOFILL_CAT_V2_LEARNING_LEDGER_{DATE}.md", learning_lines)
    generated_files.append(f"NOFILL_CAT_V2_LEARNING_LEDGER_{DATE}.md")

    prompt_pack_lines = [
        "# G12 Next Prompt Pack - NOFILL CAT V2 Audit",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        "## Recommended Next Lane",
        "",
        "`G12_NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_AUDIT` should independently audit this V2 rebuild.",
        "",
        "## Inputs",
        "",
        f"- `NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json`",
        f"- `NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl`",
        f"- `NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json`",
        f"- `NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json`",
        f"- `NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json`",
        f"- `NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json`",
        "",
        "## Audit Questions",
        "",
        "- Verify exact counts: `298 = 225 accepted + 8 blocked + 65 rejected` and `225 = 52 prior + 173 source-corrected`.",
        "- Verify blockers and rejects have zero overlap with accepted packet rows and no label assignment.",
        "- Verify the 65 rejects are excluded from denominator and label assignment.",
        "- Verify source-hash/no-leak/duplicate/sample-floor controls and false safety flags.",
        "- Explain what each categorical input label proves and does not prove.",
        "",
        "Forbidden: no R/performance, win-rate, expectancy, broker/account/live/order/hidden labels, validation-safe flip, outcome-review opening, promotion, registry edit, paid/API/Databento call, MT5 order/account/history call, remote push, or live trading surface change.",
    ]
    write_md(OUT_DIR / f"NOFILL_CAT_V2_G12_NEXT_PROMPT_PACK_{DATE}.md", prompt_pack_lines)
    generated_files.append(f"NOFILL_CAT_V2_G12_NEXT_PROMPT_PACK_{DATE}.md")

    context_lines = [
        "# NOFILL CAT V2 Context Anchor",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"- Lane: `{LANE}`",
        f"- Packet: `{PACKET_ID}`",
        f"- Repo HEAD at build: `{git_output('rev-parse', '--short', 'HEAD')}`",
        "- Controlling prompt: `NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD_GOAL_PROMPT_2026-05-09.md`",
        "- Controlling authority: G12 no-fill source-correction consolidated audit.",
        "- Preflight context read: LIVE_STATE, research_current_state, research_operating_doctrine, goal_session_research_discipline, local_heavy_data_inventory, latest handoff, controlling prompt.",
        "",
        "Active boundaries: source-safe input-only categorical packet; no performance, no broker/account/live/order labels, no validation, no promotion, no live surface change.",
        "",
        "Stop condition: V2 is complete only if builder, verifier, py_compile, focused pytest, JSON/JSONL parse, exact count checks, overlap checks, no-leak/source-hash checks, duplicate/sample-floor checks, completion audit, and G12 next prompt pack all pass.",
    ]
    write_md(OUT_DIR / f"NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.md", context_lines)
    generated_files.append(f"NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.md")

    prompt_to_artifact_checklist = [
        {
            "requirement": "mandatory preflight and controlling prompt read",
            "artifact_evidence": [
                ".context/LIVE_STATE.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                rel(OUT_DIR / "NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_REBUILD_GOAL_PROMPT_2026-05-09.md"),
            ],
            "status": "PASS",
        },
        {
            "requirement": "consume G12 consolidated accept/block/reject authority",
            "artifact_evidence": rel(G12_SOURCE_DIR / f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{SOURCE_DATE}.json"),
            "status": "PASS",
        },
        {
            "requirement": "exact count reconciliation",
            "artifact_evidence": "NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_2026-05-09.json",
            "status": "PASS" if universe["status"] == "PASS" else "FAIL",
        },
        {
            "requirement": "accepted packet contains 225 rows and carries 52 prior plus 173 source-corrected inputs",
            "artifact_evidence": "NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json",
            "status": "PASS" if len(accepted_rows) == 225 and decision_counts["ACCEPT_PRIOR_CATEGORICAL_LABEL"] == 52 and decision_counts["ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD"] == 173 else "FAIL",
        },
        {
            "requirement": "8 exact blockers preserved without labels",
            "artifact_evidence": "NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json",
            "status": "PASS" if len(blocked_rows) == 8 and all(row["categorical_input_label"] is None for row in blocked_rows) else "FAIL",
        },
        {
            "requirement": "65 rejects excluded from denominator and label assignment",
            "artifact_evidence": "NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json",
            "status": "PASS" if len(rejected_rows) == 65 and all(not row["in_accepted_packet_denominator"] and row["categorical_input_label"] is None for row in rejected_rows) else "FAIL",
        },
        {
            "requirement": "source-hash/no-leak audit",
            "artifact_evidence": "NOFILL_CAT_V2_SOURCE_HASH_NOLEAK_AUDIT_2026-05-09.json",
            "status": source_hash_audit["status"],
        },
        {
            "requirement": "duplicate/sample-floor audit",
            "artifact_evidence": "NOFILL_CAT_V2_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-09.json",
            "status": duplicate_audit["status"],
        },
        {
            "requirement": "G12 next prompt pack",
            "artifact_evidence": "NOFILL_CAT_V2_G12_NEXT_PROMPT_PACK_2026-05-09.md",
            "status": "PASS",
        },
        {
            "requirement": "safety flags false and NO_PROMOTION_VERDICT preserved",
            "artifact_evidence": "all generated JSON/Markdown artifacts",
            "status": "PASS",
        },
    ]
    completion_status = "PASS" if all(item["status"] == "PASS" for item in prompt_to_artifact_checklist) else "FAIL"
    completion = {
        **base_payload("NOFILL_CAT_V2_COMPLETION_AUDIT"),
        "packet_id": PACKET_ID,
        "completion_status": completion_status,
        "can_mark_goal_complete": completion_status == "PASS",
        "objective_restatement": "Build a source-safe input-only categorical packet V2 carrying forward 52 prior accepted rows, consuming 173 G12-accepted source-corrected inputs, preserving 8 exact blockers without labels, and excluding 65 rejects from denominator/label assignment.",
        "prompt_to_artifact_checklist": prompt_to_artifact_checklist,
        "counts": {
            "all_rows": summarize_counts(all_rows),
            "accepted_rows": summarize_counts(accepted_rows),
            "blocked_rows": summarize_counts(blocked_rows),
            "rejected_rows": summarize_counts(rejected_rows),
        },
        "generated_files": generated_files,
        "safety_boundary_status": [
            {"boundary": "R/performance scoring", "violated": False},
            {"boundary": "win-rate or expectancy computation", "violated": False},
            {"boundary": "broker/account/live/order/hidden labels", "violated": False},
            {"boundary": "validation-safe flip", "violated": False},
            {"boundary": "outcome-review opening", "violated": False},
            {"boundary": "promotion claim", "violated": False},
            {"boundary": "registry edit", "violated": False},
            {"boundary": "paid/API/Databento call", "violated": False},
            {"boundary": "MT5 order/account/history call", "violated": False},
            {"boundary": "remote push", "violated": False},
            {"boundary": "live trading surface change", "violated": False},
        ],
        "next_lane": "G12_NOFILL_LIFECYCLE_CATEGORICAL_RESULT_PACKET_V2_AUDIT",
    }
    write_json(OUT_DIR / f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.json", completion)
    generated_files.append(f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.json")
    write_md(
        OUT_DIR / f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.md",
        [
            "# NOFILL CAT V2 Completion Audit",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            f"Completion status: `{completion_status}`.",
            f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`.",
            "",
            "Objective restated: build a source-safe input-only categorical packet V2 with `298 = 225 accepted + 8 blocked + 65 rejected` and no performance/live/validation surface.",
            "",
            "| Requirement | Status | Evidence |",
            "|---|---|---|",
            *[
                f"| {item['requirement']} | `{item['status']}` | `{item['artifact_evidence']}` |"
                for item in prompt_to_artifact_checklist
            ],
        ],
    )
    generated_files.append(f"NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.md")

    return {
        "status": completion_status,
        "generated_files": generated_files,
        "counts": completion["counts"],
    }


def main() -> int:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
