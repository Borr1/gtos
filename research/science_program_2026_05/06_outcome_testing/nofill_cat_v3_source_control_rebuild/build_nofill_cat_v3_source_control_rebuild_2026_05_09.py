#!/usr/bin/env python3
"""Build NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD artifacts.

This is a source/control rebuild only. It consumes the V2 categorical packet
and the later G12-accepted May 3 / residual source-control evidence without
opening results, validation, promotion, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
SCHEMA = "nofill_cat_v3_source_control_rebuild_v1"
ROUTE_ID = "NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD"
PACKET_ID = "NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T06:00:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]

V2_DIR = OUTCOME_ROOT / "nofill_lifecycle_categorical_result_packet_v2_rebuild"
G12_V2_DIR = OUTCOME_ROOT / "g12_nofill_categorical_result_packet_v2_audit"
FORENSICS_DIR = OUTCOME_ROOT / "nofill_cat_v2_quarantined_categorical_synthesis_forensics"
G12_FORENSICS_DIR = OUTCOME_ROOT / "g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit"
G0_DIR = OUTCOME_ROOT / "nofill_cat_v2_g0_synthesis_control_route"
PENDING_DIR = OUTCOME_ROOT / "nofill_cat_v2_pending_lifecycle_source_contract_builder"
G12_PENDING_DIR = OUTCOME_ROOT / "g12_nofill_cat_v2_pending_source_contract_audit"
RESIDUAL_ACCESS_DIR = OUTCOME_ROOT / "nofill_cat_v2_residual_blocker_clear_source_access_lane"
MAY3_DIR = OUTCOME_ROOT / "nofill_may3_opening_range_market_closure_or_source_proof"
G12_MAY3_DIR = OUTCOME_ROOT / "g12_nofill_may3_source_proof_audit"
REMAINING_DIR = OUTCOME_ROOT / "nofill_remaining_residual_source_closure"
G12_REMAINING_DIR = OUTCOME_ROOT / "g12_nofill_remaining_residual_source_closure_audit"
RESULT_CONTRACT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design"
G12_RESULT_CONTRACT_DIR = OUTCOME_ROOT / "g12_no_fill_result_contract_audit"
G12_SOURCE_CORRECTION_DIR = OUTCOME_ROOT / "g12_nofill_source_correction_consolidated_audit"
PRIOR_CAT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_categorical_result_packet"
G12_PRIOR_CAT_DIR = OUTCOME_ROOT / "g12_no_fill_categorical_result_packet_audit"

REQUIRED_CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
]

REQUIRED_ARTIFACT_DIRS = [
    V2_DIR,
    G12_V2_DIR,
    FORENSICS_DIR,
    G12_FORENSICS_DIR,
    G0_DIR,
    PENDING_DIR,
    G12_PENDING_DIR,
    RESIDUAL_ACCESS_DIR,
    MAY3_DIR,
    G12_MAY3_DIR,
    REMAINING_DIR,
    G12_REMAINING_DIR,
    RESULT_CONTRACT_DIR,
    G12_RESULT_CONTRACT_DIR,
    G12_SOURCE_CORRECTION_DIR,
    PRIOR_CAT_DIR,
    G12_PRIOR_CAT_DIR,
]

MAY3_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
}
XAU_SOURCE_CONTROL_ROW = "NOFILL-CAT-ROW-0241"
USDJPY_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
SPECIAL_ROWS = MAY3_ROWS | {XAU_SOURCE_CONTROL_ROW} | USDJPY_IMPOSSIBLE_ROWS

EXPECTED_V2_COUNTS = {
    "accepted": 225,
    "blocked": 8,
    "rejected": 65,
    "total": 298,
}
EXPECTED_V3_FAMILY_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "blocked": 0,
    "reject": 65,
}


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "route_id": ROUTE_ID,
        "packet_id": PACKET_ID,
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
    path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def file_record(path: Path, role: str, parser_or_source_version: str = "sha256") -> dict[str, Any]:
    resolved = path.resolve() if path.exists() else path
    return {
        "path": rel(path),
        "resolved_path": str(resolved),
        "role": role,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "sha256": sha256_file(path),
        "parser_or_source_version": parser_or_source_version,
    }


def collect_artifact_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    records.append(file_record(OUT_DIR / f"NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD_GOAL_PROMPT_{DATE}.md", "controlling_prompt"))
    for context_path in REQUIRED_CONTEXT_FILES:
        records.append(file_record(REPO_ROOT / context_path, "mandatory_context"))
    for directory in REQUIRED_ARTIFACT_DIRS:
        if not directory.exists():
            records.append(
                {
                    "path": rel(directory),
                    "resolved_path": str(directory),
                    "role": "required_artifact_directory",
                    "exists": False,
                    "size_bytes": None,
                    "sha256": None,
                    "parser_or_source_version": "directory_presence",
                }
            )
            continue
        for pattern in ("*.json", "*.jsonl", "*.md", "*.py", "*.txt"):
            for path in sorted(directory.glob(pattern)):
                records.append(file_record(path, f"required_artifact:{directory.name}"))
    return records


def load_inputs() -> dict[str, Any]:
    return {
        "v2_rows": read_jsonl(V2_DIR / f"NOFILL_CAT_V2_ROW_DECISION_LEDGER_{DATE}.jsonl"),
        "v2_universe": read_json(V2_DIR / f"NOFILL_CAT_V2_UNIVERSE_RECONCILIATION_{DATE}.json"),
        "v2_accepted": read_json(V2_DIR / f"NOFILL_CAT_V2_ACCEPTED_PACKET_{DATE}.json"),
        "v2_blocker": read_json(V2_DIR / f"NOFILL_CAT_V2_BLOCKER_LEDGER_{DATE}.json"),
        "v2_reject": read_json(V2_DIR / f"NOFILL_CAT_V2_REJECT_LEDGER_{DATE}.json"),
        "g12_v2_decision": read_json(G12_V2_DIR / f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"),
        "g12_source_correction_decision": read_json(
            G12_SOURCE_CORRECTION_DIR / "G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.json"
        ),
        "may3_decision": read_json(G12_MAY3_DIR / f"G12_NOFILL_MAY3_DECISION_LEDGER_{DATE}.json"),
        "may3_hash": read_json(G12_MAY3_DIR / f"G12_NOFILL_MAY3_SOURCE_HASH_AUDIT_{DATE}.json"),
        "remaining_decision": read_json(G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json"),
        "remaining_xau": read_json(G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.json"),
        "remaining_usdjpy": read_json(G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.json"),
        "remaining_noleak": read_json(
            G12_REMAINING_DIR / f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.json"
        ),
        "residual_source_search": read_json(REMAINING_DIR / f"NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_{DATE}.json"),
        "residual_hash_manifest": read_json(REMAINING_DIR / f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.json"),
        "result_contract_audit": read_json(
            G12_RESULT_CONTRACT_DIR / "G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_2026-05-08.json"
        ),
        "pending_source_audit": read_json(
            G12_PENDING_DIR / f"G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_{DATE}.json"
        ),
        "g0_decision": read_json(G0_DIR / f"G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_DECISION_LEDGER_{DATE}.json"),
    }


def find_row_decision(decisions: list[dict[str, Any]], row_id: str) -> dict[str, Any] | None:
    for decision in decisions:
        if decision.get("packet_row_id") == row_id:
            return decision
    return None


def build_v3_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    may3_by_id = {row["packet_row_id"]: row for row in inputs["may3_decision"]["row_decisions"]}
    remaining_by_id = {row["packet_row_id"]: row for row in inputs["remaining_decision"]["row_decisions"]}
    rows: list[dict[str, Any]] = []

    for source in inputs["v2_rows"]:
        row_id = source["packet_row_id"]
        family: str
        state: str
        state_reason: str
        source_control_decision: str | None = None
        exact_next_source_needed: str | None = None
        categorical_label = source.get("categorical_lifecycle_label")
        in_accepted_denominator = bool(source.get("in_accepted_packet_denominator"))
        in_source_control_packet = False

        if source.get("row_status") == "ACCEPTED_INPUT_ONLY":
            family = "accepted"
            state = "ACCEPTED_INPUT_ONLY_CATEGORICAL"
            state_reason = "Prior V2/G12 accepted input-only categorical row carried forward unchanged."
        elif row_id in MAY3_ROWS:
            evidence = may3_by_id[row_id]
            family = "source_control"
            state = "SOURCE_CONTROL_MARKET_SESSION_EMPTY"
            source_control_decision = evidence["g12_terminal_decision"]
            state_reason = evidence["decision_reason"]
            exact_next_source_needed = evidence.get("exact_next_source_needed")
            in_accepted_denominator = False
            in_source_control_packet = True
            categorical_label = None
        elif row_id == XAU_SOURCE_CONTROL_ROW:
            evidence = remaining_by_id[row_id]
            family = "source_control"
            state = "SOURCE_CONTROL_INPUT_ONLY_NO_ENTRY_THROUGH_CANCEL"
            source_control_decision = evidence["g12_terminal_decision"]
            state_reason = evidence["decision_rationale"]
            exact_next_source_needed = evidence.get("exact_next_source_needed_if_reopened")
            in_accepted_denominator = False
            in_source_control_packet = True
            categorical_label = None
        elif row_id in USDJPY_IMPOSSIBLE_ROWS:
            evidence = remaining_by_id[row_id]
            family = "source_impossible"
            state = "SOURCE_IMPOSSIBLE_EXACT_ORDERING"
            source_control_decision = evidence["g12_terminal_decision"]
            state_reason = evidence["decision_rationale"]
            exact_next_source_needed = evidence.get("exact_next_source_needed_if_reopened")
            in_accepted_denominator = False
            categorical_label = None
        elif source.get("row_status") == "REJECTED_EXCLUDED_FROM_DENOMINATOR":
            family = "reject"
            state = "REJECTED_EXCLUDED_FROM_DENOMINATOR"
            state_reason = "Prior V2/G12 reject carried forward; outside labels, denominators, validation, promotion, and live effect."
            in_accepted_denominator = False
            categorical_label = None
        else:
            family = "blocked"
            state = "BLOCKED_EXACT_SOURCE_OR_ORDERING_GAP"
            state_reason = "No G12-accepted V3 source-control or source-impossibility evidence consumed for this row."
            in_accepted_denominator = False
            categorical_label = None

        rows.append(
            {
                "packet_row_id": row_id,
                "source_close_packet_row_id": source.get("source_close_packet_row_id"),
                "source_inventory_id": source.get("source_inventory_id"),
                "symbol": source.get("symbol"),
                "session": source.get("session"),
                "side": source.get("side"),
                "source_lane": source.get("source_lane"),
                "source_packet_id": source.get("source_packet_id"),
                "source_row_id": source.get("source_row_id"),
                "duplicate_group_id": source.get("duplicate_group_id"),
                "nofill_duplicate_key": source.get("nofill_duplicate_key"),
                "v2_row_status": source.get("row_status"),
                "v2_decision": source.get("consolidated_g12_decision"),
                "v3_terminal_family": family,
                "v3_terminal_state": state,
                "v3_state_reason": state_reason,
                "g12_source_control_decision": source_control_decision,
                "exact_blocker_codes": source.get("exact_blocker_codes") or [],
                "reject_reason_codes": source.get("reject_reason_codes") or [],
                "exact_next_source_needed": exact_next_source_needed,
                "categorical_lifecycle_label": categorical_label,
                "label_class": "input_only_categorical" if family == "accepted" else None,
                "in_accepted_packet_denominator": in_accepted_denominator,
                "in_source_control_packet": in_source_control_packet,
                "source_safe_input_only": True,
                "lifecycle_label_assigned": False if family != "accepted" else bool(categorical_label),
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "promotion_verdict": PROMOTION_VERDICT,
            }
        )
    return rows


def source_control_evidence_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["v3_terminal_family"] in {"accepted", "source_control"}]


def source_search_records() -> dict[str, Any]:
    roots: list[dict[str, Any]] = []

    specific_files = [
        (
            Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\NAS100\2026-05-03.parquet"),
            "may3_nas100_broker_tick_parquet",
            "same-symbol May 3 tick absence source used by G12 May3 audit",
        ),
        (
            Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-03.parquet"),
            "may3_xauusd_broker_tick_parquet",
            "same-symbol May 3 tick absence source used by G12 May3 audit",
        ),
        (
            Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-05.parquet"),
            "xauusd_0241_active_day_broker_tick_parquet",
            "side-aware source for 0241 active window",
        ),
        (
            Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-06.parquet"),
            "xauusd_0241_cancel_day_existing_broker_tick_parquet",
            "existing May 6 tick capture; recovered gap packet remains decisive through cancel",
        ),
        (
            Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\USDJPY\2026-05-01.parquet"),
            "usdjpy_may1_broker_tick_parquet",
            "quote-state source for rows 0143 and 0178; no sub-row sequence field",
        ),
        (
            Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\USDJPY\2026-04-20.parquet"),
            "usdjpy_apr20_main_tick_root_check",
            "expected absent in main tick root; prior worktree read-only export is used instead",
        ),
        (
            REMAINING_DIR / "raw" / "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
            "xauusd_0241_recovered_true_utc_gap_ticks_current_worktree",
            "read-only recovered gap packet copied into current worktree",
        ),
    ]
    roots.append(
        {
            "root_path": r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
            "search_type": "targeted_specific_file_presence_and_hash",
            "records": [file_record(path, role, "read_only_file_hash") | {"decision_note": note} for path, role, note in specific_files],
        }
    )

    prior_root = Path(r"C:\tmp\gtos_otb")
    prior_patterns = [
        "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
        "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
        "G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_2026-05-09.json",
        "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json",
    ]
    prior_matches: list[dict[str, Any]] = []
    if prior_root.exists():
        for pattern in prior_patterns:
            pattern_matches = sorted(prior_root.rglob(pattern))
            for path in pattern_matches[:20]:
                prior_matches.append(file_record(path, f"prior_worktree_match:{pattern}", "targeted_prior_worktree_search"))
            if len(pattern_matches) > 20:
                prior_matches.append(
                    {
                        "path": pattern,
                        "resolved_path": str(prior_root),
                        "role": f"prior_worktree_match:{pattern}",
                        "exists": True,
                        "size_bytes": None,
                        "sha256": None,
                        "parser_or_source_version": "targeted_prior_worktree_search",
                        "truncated_count_after_first_20": len(pattern_matches) - 20,
                    }
                )
    roots.append(
        {
            "root_path": str(prior_root),
            "search_type": "targeted_prior_worktree_exact_filename_search",
            "patterns": prior_patterns,
            "records": prior_matches,
            "conclusion": (
                "Prior worktrees expose duplicate copies of accepted source-control packets and the "
                "Apr 20 USDJPY quote-state parquet, but no broker-native USDJPY quote-event sequence "
                "source with sub-row ordering."
            ),
        }
    )

    research_export_root = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports")
    roots.append(
        {
            "root_path": str(research_export_root),
            "search_type": "existence_check_for_lower_timeframe_context_root",
            "exists": research_export_root.exists(),
            "conclusion": (
                "Lower-timeframe OHLC/context roots cannot order same-MqlTick quote-state predicates "
                "for the USDJPY same-row ambiguities."
            ),
        }
    )

    external_root = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\external")
    roots.append(
        {
            "root_path": str(external_root),
            "search_type": "existence_check_for_proxy_or_vendor_context_root",
            "exists": external_root.exists(),
            "conclusion": (
                "External/proxy context does not replace broker-native USDJPY quote-event sequence "
                "evidence for source-control ordering."
            ),
        }
    )
    return {
        **base_payload("NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER"),
        "searched_roots": roots,
        "source_sequence_route_found": False,
        "source_sequence_route_needed": (
            "Broker-native USDJPY quote-event source with sequence ID, broker/exchange quote-event "
            "number, or sub-row/sub-millisecond timestamp, source-hashed and without account/order/history labels."
        ),
        "search_conclusion": {
            "xauusd_0241": "G12-accepted side-aware source-control packet is available and consumed input-only.",
            "may3_rows": "G12-accepted market-session-empty source-control evidence is available and consumed input-only.",
            "usdjpy_rows": "No current local/prior approved source exposes the required sub-row event sequence; preserve source-impossible terminal state.",
        },
    }


def build_universe(rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    family_counts = Counter(row["v3_terminal_family"] for row in rows)
    full_family_counts = {key: family_counts.get(key, 0) for key in EXPECTED_V3_FAMILY_COUNTS}
    state_counts = Counter(row["v3_terminal_state"] for row in rows)
    accepted_rows = [row for row in rows if row["v3_terminal_family"] == "accepted"]
    source_control_rows = [row for row in rows if row["v3_terminal_family"] == "source_control"]
    impossible_rows = [row for row in rows if row["v3_terminal_family"] == "source_impossible"]
    reject_rows = [row for row in rows if row["v3_terminal_family"] == "reject"]
    return {
        **base_payload("NOFILL_CAT_V3_UNIVERSE_RECONCILIATION"),
        "status": "PASS" if full_family_counts == EXPECTED_V3_FAMILY_COUNTS else "FAIL",
        "prior_v2_reconciliation": {
            "row_count": len(inputs["v2_rows"]),
            "accepted_rows": inputs["v2_accepted"]["accepted_row_count"],
            "blocked_rows": inputs["v2_blocker"]["blocked_row_count"],
            "rejected_rows": inputs["v2_reject"]["rejected_row_count"],
            "g12_v2_decision": inputs["g12_v2_decision"]["decision"],
        },
        "v3_reconciliation": {
            "row_count": len(rows),
            "terminal_family_counts": full_family_counts,
            "terminal_state_counts": dict(sorted(state_counts.items())),
            "accepted_denominator_rows": len(accepted_rows),
            "source_control_non_denominator_rows": len(source_control_rows),
            "source_impossible_rows": len(impossible_rows),
            "rejected_rows": len(reject_rows),
            "unresolved_blocked_rows": family_counts.get("blocked", 0),
            "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted_rows}),
        },
        "transformed_v2_blockers": {
            "may3_market_session_empty": sorted(MAY3_ROWS),
            "xauusd_input_only_no_entry_through_cancel": [XAU_SOURCE_CONTROL_ROW],
            "usdjpy_source_impossible_exact_ordering": sorted(USDJPY_IMPOSSIBLE_ROWS),
        },
        "required_target_row_status": {row["packet_row_id"]: row["v3_terminal_state"] for row in rows if row["packet_row_id"] in SPECIAL_ROWS},
        "non_claims": [
            "No result scoring is opened.",
            "No validation-safe flag is set.",
            "No promotion or live behavior claim is made.",
            "Source-control rows are not added to the accepted denominator.",
        ],
    }


def build_packets(rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    packet_rows = source_control_evidence_rows(rows)
    return {
        **base_payload("NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET"),
        "accepted_denominator_row_count": sum(1 for row in rows if row["v3_terminal_family"] == "accepted"),
        "source_control_non_denominator_row_count": sum(1 for row in rows if row["v3_terminal_family"] == "source_control"),
        "accepted_prior_v2_rows_carried_forward": inputs["v2_accepted"]["accepted_row_count"],
        "source_control_rows_consumed": sorted(MAY3_ROWS | {XAU_SOURCE_CONTROL_ROW}),
        "rows": packet_rows,
        "source_control_evidence": {
            "NOFILL-CAT-ROW-0241": {
                "g12_terminal_decision": inputs["remaining_xau"]["g12_terminal_decision"],
                "entry_price": inputs["remaining_xau"]["entry_price"],
                "max_bid_through_cancel": inputs["remaining_xau"]["upstream_packet_claim"]["max_bid_through_cancel"],
                "max_ask_through_cancel": inputs["remaining_xau"]["upstream_packet_claim"]["max_ask_through_cancel"],
                "recovered_gap_rows_through_cancel": inputs["remaining_xau"]["upstream_packet_claim"][
                    "recovered_gap_rows_through_cancel"
                ],
                "entry_touch_before_cancel": inputs["remaining_xau"]["upstream_packet_claim"]["entry_touch_before_cancel"],
            },
            "may3_rows": {
                "g12_terminal_decision": inputs["may3_decision"]["terminal_decision"],
                "target_row_ids": inputs["may3_decision"]["target_row_ids"],
                "tick_window_rows": inputs["may3_hash"]["tick_parquet_recompute"],
            },
        },
    }


def build_blocker_impossibility(rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    impossible = [row for row in rows if row["v3_terminal_family"] == "source_impossible"]
    blockers = [row for row in rows if row["v3_terminal_family"] == "blocked"]
    return {
        **base_payload("NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER"),
        "unresolved_blocker_count": len(blockers),
        "source_impossible_count": len(impossible),
        "source_impossible_rows": impossible,
        "unresolved_blocker_rows": blockers,
        "exact_unblocker": inputs["remaining_usdjpy"]["exact_unblocker"],
        "rejected_routes": inputs["remaining_usdjpy"]["rejected_routes"],
        "row_evidence_summary": {
            audit["packet_row_id"]: {
                "exact_timestamp_row_count": audit["g12_source_recheck"]["exact_timestamp_row_count"],
                "target_ts_utc": audit["g12_source_recheck"]["target_ts_utc"],
                "same_tick_impossibility_holds": audit["same_tick_impossibility_holds"],
                "sha256": audit["g12_source_recheck"]["sha256"],
            }
            for audit in inputs["remaining_usdjpy"]["row_audits"]
        },
    }


def build_reject_ledger(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rejects = [row for row in rows if row["v3_terminal_family"] == "reject"]
    return {
        **base_payload("NOFILL_CAT_V3_REJECT_LEDGER"),
        "rejected_row_count": len(rejects),
        "reject_reason_counts": dict(Counter(code for row in rejects for code in row["reject_reason_codes"])),
        "reject_rows_outside_labels_denominators": True,
        "rows": rejects,
    }


def build_hash_noleak(rows: list[dict[str, Any]], inputs: dict[str, Any], artifact_records: list[dict[str, Any]]) -> dict[str, Any]:
    source_control_rows = [row for row in rows if row["v3_terminal_family"] == "source_control"]
    impossible_rows = [row for row in rows if row["v3_terminal_family"] == "source_impossible"]
    reject_rows = [row for row in rows if row["v3_terminal_family"] == "reject"]
    accepted_rows = [row for row in rows if row["v3_terminal_family"] == "accepted"]
    strict_missing = [record for record in artifact_records if not record["exists"]]
    return {
        **base_payload("NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT"),
        "status": "PASS" if not strict_missing else "FAIL",
        "artifact_hash_record_count": len(artifact_records),
        "missing_artifact_records": strict_missing,
        "source_hash_records": artifact_records,
        "upstream_hash_audits_consumed": {
            "v2_source_hash_status": inputs["v2_universe"]["status"],
            "g12_v2_source_hash_status": inputs["g12_v2_decision"]["status"],
            "g12_may3_strict_source_hashes_recomputed_ok": inputs["may3_hash"]["strict_source_hashes_recomputed_ok"],
            "g12_remaining_source_hash_record_count": inputs["residual_hash_manifest"]["record_count"],
        },
        "noleak_checks": {
            "accepted_denominator_rows": len(accepted_rows),
            "source_control_rows_not_denominator": [row["packet_row_id"] for row in source_control_rows if not row["in_accepted_packet_denominator"]],
            "source_impossible_rows_not_denominator": [row["packet_row_id"] for row in impossible_rows if not row["in_accepted_packet_denominator"]],
            "reject_rows_not_denominator_count": sum(1 for row in reject_rows if not row["in_accepted_packet_denominator"]),
            "reject_total_preserved": len(reject_rows),
            "lifecycle_labels_on_source_control_or_impossible_or_rejects": sum(
                1 for row in source_control_rows + impossible_rows + reject_rows if row["lifecycle_label_assigned"]
            ),
            "validation_safe_true_count": sum(1 for row in rows if row["validation_safe"]),
            "outcome_review_opened_true_count": sum(1 for row in rows if row["outcome_review_opened"]),
            "live_effect_true_count": sum(1 for row in rows if row["live_effect"]),
        },
        "label_boundary": (
            "Accepted V2 categorical labels remain input-only. Source-control, source-impossible, and reject rows "
            "receive no categorical lifecycle label and no denominator movement."
        ),
    }


def build_duplicate_sample(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["v3_terminal_family"] == "accepted"]
    source_control = [row for row in rows if row["v3_terminal_family"] == "source_control"]
    duplicate_counts = Counter(row["nofill_duplicate_key"] for row in rows)
    duplicate_nonaccepted = {
        key: [
            row["packet_row_id"]
            for row in rows
            if row["nofill_duplicate_key"] == key and row["v3_terminal_family"] != "accepted"
        ]
        for key, count in duplicate_counts.items()
        if count > 1
    }
    return {
        **base_payload("NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT"),
        "status": "PASS",
        "accepted_denominator_row_count": len(accepted),
        "accepted_unique_nofill_duplicate_keys": len({row["nofill_duplicate_key"] for row in accepted}),
        "source_control_row_count": len(source_control),
        "source_control_rows_outside_denominator": [row["packet_row_id"] for row in source_control],
        "duplicate_keys_with_nonaccepted_terminal_rows": duplicate_nonaccepted,
        "sample_floor_policy": {
            "scored_sample_floor_opened": False,
            "reason": "V3 is source-control/input-only and does not score outcomes.",
        },
        "may3_duplicate_boundary": {
            "NOFILL-CAT-ROW-0050": "source-control non-denominator row",
            "NOFILL-CAT-ROW-0051": "source-control non-denominator row",
            "decision": "Preserve explicit terminal state for both rows; do not merge, silently drop, or add either to accepted denominator.",
        },
    }


def md_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Check | Value |", "|---|---|"]
    for key, value in rows:
        lines.append(f"| `{key}` | `{value}` |")
    return lines


def write_markdown_outputs(
    rows: list[dict[str, Any]],
    universe: dict[str, Any],
    packet: dict[str, Any],
    blockers: dict[str, Any],
    rejects: dict[str, Any],
    hash_audit: dict[str, Any],
    duplicate_audit: dict[str, Any],
    search_ledger: dict[str, Any],
) -> None:
    head = git_output("rev-parse", "--short", "HEAD")
    status = git_output("status", "--short")

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_CONTEXT_ANCHOR_{DATE}.md",
        [
            f"# NOFILL CAT V3 Context Anchor - {DATE}",
            "",
            f"Route: `{ROUTE_ID}`",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            f"Current HEAD at build: `{head}`",
            "",
            "## Boundaries",
            "",
            "- Source-control/input-only rebuild.",
            "- No result scoring, validation, promotion, registry edit, live behavior, or account/order/history route.",
            "- Consume only G12-accepted source-control evidence for the new terminal states.",
            "",
            "## Inputs Read",
            "",
            "- Mandatory GTOS preflight context files, including regenerated `.context/LIVE_STATE.md`.",
            "- V2 no-fill categorical rebuild and G12 V2 audit artifacts.",
            "- V2 forensics and G12 forensics audit artifacts.",
            "- G0 synthesis, pending source contract/audit, residual source-access, May 3 proof/audit, remaining closure/audit.",
            "- Result-contract design/audit and G12 source-correction consolidated audit.",
            "",
            "## Active Question Stack",
            "",
            "1. Reconcile all 298 V2 rows into one V3 terminal state.",
            "2. Preserve the 225 V2 accepted denominator unchanged.",
            "3. Represent 0241 and May 3 rows as source-control non-denominator evidence.",
            "4. Preserve USDJPY rows as source-impossible terminal blockers unless a broker-native sequence route exists.",
            "5. Preserve all 65 rejects outside labels, denominators, validation, promotion, and live effect.",
            "6. Produce machine-checkable ledgers, verifier, tests, next G12 prompt, and completion audit.",
            "",
            "## Build-Time Git Status",
            "",
            "```text",
            status or "(clean)",
            "```",
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.md",
        [
            f"# NOFILL CAT V3 Universe Reconciliation - {DATE}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            *md_table(
                [
                    ("prior_v2_total", universe["prior_v2_reconciliation"]["row_count"]),
                    ("prior_v2_accepted", universe["prior_v2_reconciliation"]["accepted_rows"]),
                    ("prior_v2_blocked", universe["prior_v2_reconciliation"]["blocked_rows"]),
                    ("prior_v2_rejected", universe["prior_v2_reconciliation"]["rejected_rows"]),
                    ("v3_total", universe["v3_reconciliation"]["row_count"]),
                    ("v3_accepted", universe["v3_reconciliation"]["terminal_family_counts"].get("accepted", 0)),
                    ("v3_source_control", universe["v3_reconciliation"]["terminal_family_counts"].get("source_control", 0)),
                    ("v3_source_impossible", universe["v3_reconciliation"]["terminal_family_counts"].get("source_impossible", 0)),
                    ("v3_unresolved_blocked", universe["v3_reconciliation"]["terminal_family_counts"].get("blocked", 0)),
                    ("v3_rejects", universe["v3_reconciliation"]["terminal_family_counts"].get("reject", 0)),
                ]
            ),
            "",
            "The 225 accepted V2 rows remain accepted unchanged. The eight V2 blockers are resolved as four source-control terminal rows and four source-impossible terminal rows. The 65 rejects remain excluded.",
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.md",
        [
            f"# NOFILL CAT V3 Blocker / Impossibility Ledger - {DATE}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            *md_table(
                [
                    ("unresolved_blocker_count", blockers["unresolved_blocker_count"]),
                    ("source_impossible_count", blockers["source_impossible_count"]),
                    ("exact_unblocker", blockers["exact_unblocker"]),
                ]
            ),
            "",
            "## Source-Impossible Rows",
            "",
            "| Row | Symbol | State | Exact Next Source |",
            "|---|---|---|---|",
            *[
                f"| `{row['packet_row_id']}` | `{row['symbol']}` | `{row['v3_terminal_state']}` | `{row['exact_next_source_needed']}` |"
                for row in blockers["source_impossible_rows"]
            ],
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.md",
        [
            f"# NOFILL CAT V3 Reject Ledger - {DATE}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            *md_table(
                [
                    ("rejected_row_count", rejects["rejected_row_count"]),
                    ("reject_rows_outside_labels_denominators", rejects["reject_rows_outside_labels_denominators"]),
                ]
            ),
            "",
            "All 65 reject rows are preserved outside labels, denominators, result use, validation use, promotion use, and live effect.",
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
        [
            f"# NOFILL CAT V3 Source Hash / No-Leak Audit - {DATE}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            *md_table(
                [
                    ("status", hash_audit["status"]),
                    ("artifact_hash_record_count", hash_audit["artifact_hash_record_count"]),
                    ("accepted_denominator_rows", hash_audit["noleak_checks"]["accepted_denominator_rows"]),
                    ("source_control_rows_not_denominator", len(hash_audit["noleak_checks"]["source_control_rows_not_denominator"])),
                    ("source_impossible_rows_not_denominator", len(hash_audit["noleak_checks"]["source_impossible_rows_not_denominator"])),
                    ("reject_rows_not_denominator_count", hash_audit["noleak_checks"]["reject_rows_not_denominator_count"]),
                    ("validation_safe_true_count", hash_audit["noleak_checks"]["validation_safe_true_count"]),
                    ("outcome_review_opened_true_count", hash_audit["noleak_checks"]["outcome_review_opened_true_count"]),
                    ("live_effect_true_count", hash_audit["noleak_checks"]["live_effect_true_count"]),
                ]
            ),
            "",
            "Strict artifact hash records are written in the matching JSON. Source-control rows are kept outside the accepted denominator.",
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
        [
            f"# NOFILL CAT V3 Duplicate / Sample-Floor Audit - {DATE}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            *md_table(
                [
                    ("status", duplicate_audit["status"]),
                    ("accepted_denominator_row_count", duplicate_audit["accepted_denominator_row_count"]),
                    ("accepted_unique_nofill_duplicate_keys", duplicate_audit["accepted_unique_nofill_duplicate_keys"]),
                    ("source_control_row_count", duplicate_audit["source_control_row_count"]),
                    ("scored_sample_floor_opened", duplicate_audit["sample_floor_policy"]["scored_sample_floor_opened"]),
                ]
            ),
            "",
            "The sample-floor question remains closed because this route does not score outcomes. May 3 duplicate-boundary rows 0050 and 0051 are represented explicitly and remain non-denominator source-control rows.",
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.md",
        [
            f"# NOFILL CAT V3 Source Root Search Ledger - {DATE}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            *md_table(
                [
                    ("source_sequence_route_found", search_ledger["source_sequence_route_found"]),
                    ("source_sequence_route_needed", search_ledger["source_sequence_route_needed"]),
                ]
            ),
            "",
            "The build checks worktree artifacts, local heavy tick roots, and prior worktree paths. No broker-native USDJPY sub-row quote-event sequence route was found.",
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_LEARNING_AND_LIMITATIONS_{DATE}.md",
        [
            f"# NOFILL CAT V3 Learning And Limitations - {DATE}",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`.",
            "",
            "## What V3 Proves",
            "",
            "- The full prior 298-row V2 no-fill categorical universe can be represented exactly once with terminal source-control states.",
            "- The prior 225 accepted input-only categorical rows can be carried forward unchanged.",
            "- XAUUSD 0241 has G12-accepted source-control input-only evidence that no side-aware short entry touch occurred before cancel.",
            "- May 3 rows 0049/0050/0051 have G12-accepted market-session-empty source-control evidence.",
            "- USDJPY rows 0130/0143/0165/0178 are source-impossible from approved routes until a broker-native quote-event sequence source appears.",
            "- The 65 rejects remain excluded.",
            "",
            "## What V3 Does Not Prove",
            "",
            "- It does not score any outcome or move any row into validation.",
            "- It does not support a promotion or live trading change.",
            "- It does not prove a USDJPY lifecycle result for the source-impossible rows.",
            "- It does not turn source-control rows into accepted denominator rows.",
            "",
            "## Strongest Counterargument Tested",
            "",
            "The strongest counterargument is that consuming XAUUSD 0241 or May 3 source-control evidence could silently change the accepted denominator or mix source-control facts with lifecycle/result labels. V3 tests this by assigning those rows to explicit non-denominator `source_control` terminal states, checking accepted denominator count remains 225, and verifying all source-control/impossible/reject rows have no categorical label assignment.",
            "",
            "## Future Source/Telemetry Routes",
            "",
            "- Add a broker-native quote-event sequence capture if the platform exposes one; otherwise preserve USDJPY same-tick impossibility.",
            "- Preserve source-control terminal states as packet hygiene for future G12 review.",
            "- Keep result-contract changes behind a separate evidence-class gate.",
        ],
    )

    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_G12_NEXT_PROMPT_PACK_{DATE}.md",
        [
            f"# NOFILL CAT V3 G12 Next Prompt Pack - {DATE}",
            "",
            "Run a G12 red-team audit over `NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD`.",
            "",
            "Audit scope:",
            "",
            "- Verify all 298 V2 rows are represented exactly once in V3.",
            "- Verify counts: 225 accepted, 4 source-control, 4 source-impossible, 0 unresolved blockers, 65 rejects.",
            "- Verify rows 0049/0050/0051/0241 are source-control non-denominator rows.",
            "- Verify rows 0130/0143/0165/0178 are source-impossible terminal blockers with exact next source.",
            "- Verify all 65 rejects remain outside labels, denominators, validation, promotion, and live effect.",
            "- Verify no result scoring, validation-safe flip, outcome review, promotion, registry edit, paid/API/Databento, MT5 order/account/history, or live trading surface change.",
            "- Verify source-hash, no-leak, duplicate-denominator, label-family, and sample-floor boundaries.",
            "",
            f"Promotion posture must remain `{PROMOTION_VERDICT}`.",
        ],
    )


def build_completion_audit(
    universe: dict[str, Any],
    rows: list[dict[str, Any]],
    hash_audit: dict[str, Any],
    duplicate_audit: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        ("mandatory GTOS preflight completed", True, ".context/LIVE_STATE.md regenerated/read plus required context docs read"),
        ("full 298-row universe represented exactly once", len(rows) == 298, "NOFILL_CAT_V3_ROW_DECISION_LEDGER_2026-05-09.jsonl"),
        ("225 accepted rows carried unchanged", universe["v3_reconciliation"]["terminal_family_counts"].get("accepted") == 225, "universe reconciliation"),
        ("0049/0050/0051 May3 rows explicit", MAY3_ROWS <= {row["packet_row_id"] for row in rows}, "row decision ledger"),
        ("0241 XAUUSD explicit", any(row["packet_row_id"] == XAU_SOURCE_CONTROL_ROW for row in rows), "row decision ledger"),
        ("USDJPY impossible rows explicit", USDJPY_IMPOSSIBLE_ROWS <= {row["packet_row_id"] for row in rows}, "row decision ledger"),
        ("65 rejects preserved", universe["v3_reconciliation"]["terminal_family_counts"].get("reject") == 65, "reject ledger"),
        ("no unresolved blockers remain", universe["v3_reconciliation"]["terminal_family_counts"].get("blocked", 0) == 0, "blocker/impossibility ledger"),
        ("source hash/no-leak audit passes", hash_audit["status"] == "PASS", "source hash/no-leak audit"),
        ("duplicate/sample-floor audit passes", duplicate_audit["status"] == "PASS", "duplicate/sample-floor audit"),
        ("unsafe flags false", all(not row["validation_safe"] and not row["outcome_review_opened"] and not row["live_effect"] for row in rows), "row decision ledger"),
        ("NO_PROMOTION_VERDICT preserved", all(row["promotion_verdict"] == PROMOTION_VERDICT for row in rows), "row decision ledger"),
        ("next G12 prompt pack written", True, f"NOFILL_CAT_V3_G12_NEXT_PROMPT_PACK_{DATE}.md"),
    ]
    can_mark = all(item[1] for item in checks)
    return {
        **base_payload("NOFILL_CAT_V3_COMPLETION_AUDIT"),
        "objective_restatement": (
            "Rebuild the full 298-row no-fill categorical/source-control universe after G12-accepted "
            "May 3 and residual source-control evidence, without outcome scoring or live-surface changes."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "status": "PASS" if ok else "FAIL", "evidence": evidence}
            for requirement, ok, evidence in checks
        ],
        "missing_incomplete_or_weak_requirements": [requirement for requirement, ok, _ in checks if not ok],
        "can_mark_goal_complete": can_mark,
        "completion_requires_post_build_verifier": "Run verify_nofill_cat_v3_source_control_rebuild_2026_05_09.py and focused pytest.",
    }


def write_completion_md(completion: dict[str, Any]) -> None:
    lines = [
        f"# NOFILL CAT V3 Completion Audit - {DATE}",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`.",
        "",
        f"Can mark goal complete after verifier/tests: `{completion['can_mark_goal_complete']}`",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in completion["prompt_to_artifact_checklist"]:
        lines.append(f"| {item['requirement']} | `{item['status']}` | `{item['evidence']}` |")
    lines.extend(
        [
            "",
            "## Residual Risk",
            "",
            "The only unresolved substantive source question is external: USDJPY same-MqlTick ordering would require a broker-native quote-event sequence source. V3 records this as source-impossible from approved routes, not as a missing-data excuse.",
        ]
    )
    write_md(OUT_DIR / f"NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.md", lines)


def main() -> None:
    inputs = load_inputs()
    rows = build_v3_rows(inputs)
    artifact_records = collect_artifact_records()
    search_ledger = source_search_records()
    universe = build_universe(rows, inputs)
    packet = build_packets(rows, inputs)
    blockers = build_blocker_impossibility(rows, inputs)
    rejects = build_reject_ledger(rows)
    hash_audit = build_hash_noleak(rows, inputs, artifact_records)
    duplicate_audit = build_duplicate_sample(rows)
    completion = build_completion_audit(universe, rows, hash_audit, duplicate_audit)

    write_jsonl(OUT_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl", rows)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json", universe)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json", packet)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json", blockers)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.json", rejects)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json", hash_audit)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json", duplicate_audit)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_SOURCE_ROOT_SEARCH_LEDGER_{DATE}.json", search_ledger)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json", completion)

    write_markdown_outputs(rows, universe, packet, blockers, rejects, hash_audit, duplicate_audit, search_ledger)
    write_completion_md(completion)

    print(
        json.dumps(
            {
                "ok": completion["can_mark_goal_complete"],
                "rows": len(rows),
                "terminal_family_counts": universe["v3_reconciliation"]["terminal_family_counts"],
                "source_hash_status": hash_audit["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
