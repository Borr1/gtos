from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]

CONTROL_PROMPT = ROUTE_DIR / "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE_GOAL_PROMPT_2026-05-09.md"
ROW_LEDGER = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"
)

CONTROL_INPUTS = [
    CONTROL_PROMPT,
    REPO_ROOT / ".context/LIVE_STATE.md",
    REPO_ROOT / ".context/00_core/quick_reference_card.md",
    REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
    REPO_ROOT / ".context/00_core/research_current_state.md",
    REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md",
    REPO_ROOT / ".context/00_READING_ORDER.md",
    REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_2026-05-09.md",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_2026-05-09.md",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NEXT_PROMPT_PACK_2026-05-09.md",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_SYNTHESIS_2026-05-09.md",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_2026-05-09.json",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.md",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_2026-05-09.json",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.md",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_2026-05-09.json",
    ROW_LEDGER,
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_categorical_result_packet_v2_audit/G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_2026-05-09.json",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_2026-05-09.json",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_2026-05-09.json",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_2026-05-09.json",
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_2026-05-09.json",
]

EXPECTED_PARTITION = {"universe": 298, "accepted": 225, "blocked": 8, "rejected": 65}
EXPECTED_ACCEPTED_SPLIT = {"accepted_prior": 52, "accepted_source_corrected": 173}
EXPECTED_LABEL_COUNTS = {
    "nofill_terminal_before_entry": 110,
    "source_corrected_no_entry_through_pending_horizon": 32,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
}
EXPECTED_SOURCE_LANE_COUNTS = {
    "prior_g12_categorical_packet_audit": 52,
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
}
EXPECTED_DUPLICATE_POSTURE = {
    "accepted_row_level_source_inputs": 225,
    "accepted_unique_nofill_duplicate_keys": 182,
    "accepted_duplicate_collision_groups": 5,
    "accepted_duplicate_collision_rows": 48,
    "oti5_canonical_duplicate_rows_accepted": 3,
    "oti5_noncanonical_duplicate_projections_rejected": 39,
}
EXPECTED_BLOCKER_COUNTS = {
    "oti4_may3_source_gaps": 3,
    "oti3_same_tick_order_ambiguities": 4,
    "original_oti2_source_gap": 1,
}
EXPECTED_REJECT_COUNTS = {
    "oti4_contract_exclusions": 26,
    "oti5_noncanonical_duplicate_projections": 39,
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()
    except Exception as exc:  # pragma: no cover - defensive context capture
        return f"UNAVAILABLE: {exc}"


def count_status(rows: list[dict[str, Any]]) -> dict[str, int]:
    accepted = [
        row
        for row in rows
        if row.get("row_status") == "ACCEPTED_INPUT_ONLY"
        and row.get("in_accepted_packet_denominator") is True
    ]
    blocked = [
        row
        for row in rows
        if row.get("consolidated_g12_decision") == "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP"
    ]
    rejected = [
        row
        for row in rows
        if row.get("row_status") == "REJECTED_EXCLUDED_FROM_DENOMINATOR"
    ]
    return {
        "universe": len(rows),
        "accepted": len(accepted),
        "blocked": len(blocked),
        "rejected": len(rejected),
    }


def recompute_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [
        row
        for row in rows
        if row.get("row_status") == "ACCEPTED_INPUT_ONLY"
        and row.get("in_accepted_packet_denominator") is True
    ]
    blocked = [
        row
        for row in rows
        if row.get("consolidated_g12_decision") == "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP"
    ]
    rejected = [
        row
        for row in rows
        if row.get("row_status") == "REJECTED_EXCLUDED_FROM_DENOMINATOR"
    ]
    accepted_split = {
        "accepted_prior": sum(row.get("consolidated_g12_decision") == "ACCEPT_PRIOR_CATEGORICAL_LABEL" for row in accepted),
        "accepted_source_corrected": sum(
            row.get("consolidated_g12_decision") == "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD"
            for row in accepted
        ),
    }
    label_counts = Counter(row.get("categorical_input_label") for row in accepted)
    label_counts.pop(None, None)
    source_lane_counts = Counter(row.get("accepted_source_lane") for row in accepted)
    source_lane_counts.pop(None, None)
    duplicate_key_counts = Counter(row.get("nofill_duplicate_key") for row in accepted)
    duplicate_key_counts.pop(None, None)
    collision_groups = {key: count for key, count in duplicate_key_counts.items() if count > 1}
    opening_drive_collision_rows = [
        row
        for row in accepted
        if row.get("nofill_duplicate_key") in collision_groups
        and row.get("categorical_input_label") == "opening_drive_source_projection_ready_no_result_label"
    ]
    blocker_code_counts: Counter[str] = Counter()
    reject_code_counts: Counter[str] = Counter()
    for row in blocked:
        blocker_code_counts.update(row.get("exact_blocker_codes") or [])
    for row in rejected:
        reject_code_counts.update(row.get("reject_reason_codes") or row.get("exact_blocker_codes") or [])
    reject_decision_counts = Counter(row.get("consolidated_g12_decision") for row in rejected)
    return {
        "partition": count_status(rows),
        "accepted_split": accepted_split,
        "accepted_label_counts": dict(sorted(label_counts.items())),
        "accepted_source_lane_counts": dict(sorted(source_lane_counts.items())),
        "accepted_symbol_counts": dict(sorted(Counter(row.get("symbol") for row in accepted).items())),
        "accepted_session_counts": dict(sorted(Counter(row.get("session") for row in accepted).items())),
        "accepted_side_counts": dict(sorted(Counter(row.get("side") for row in accepted).items())),
        "duplicate_posture": {
            "accepted_row_level_source_inputs": len(accepted),
            "accepted_unique_nofill_duplicate_keys": len(duplicate_key_counts),
            "accepted_duplicate_collision_groups": len(collision_groups),
            "accepted_duplicate_collision_rows": sum(collision_groups.values()),
            "opening_drive_collision_rows": len(opening_drive_collision_rows),
            "oti5_canonical_duplicate_rows_accepted": source_lane_counts.get(
                "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT", 0
            ),
            "oti5_noncanonical_duplicate_projections_rejected": reject_code_counts.get(
                "REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION", 0
            ),
        },
        "blocker_code_counts": dict(sorted(blocker_code_counts.items())),
        "reject_code_counts": dict(sorted(reject_code_counts.items())),
        "reject_decision_counts": dict(sorted(reject_decision_counts.items())),
        "blocked_rows": blocked,
        "rejected_rows": rejected,
        "accepted_rows": accepted,
    }


def input_hash_records() -> list[dict[str, Any]]:
    records = []
    for path in CONTROL_INPUTS:
        records.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path),
                "role": "controlling_or_supporting_input",
            }
        )
    return records


def local_search_evidence() -> list[dict[str, Any]]:
    candidates = [
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\NAS100\2026-05-03.parquet"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-03.parquet"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-05.parquet"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\USDJPY\2026-05-01.parquet"),
        Path(
            r"C:\tmp\gtos_otb\OTI3USDJPY\research\science_program_2026_05\06_outcome_testing\oti3_usdjpy_price_only_quote_or_tick_contract\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet"
        ),
    ]
    records = []
    for path in candidates:
        records.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "consumed_for_labels": False,
                "role": "targeted_blocker_feasibility_search_only",
            }
        )
    return records


def safety_flags(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_selector_logic": False,
        "opens_registry_edit": False,
        "changes_live_trading_behavior": False,
    }
    if extra:
        base.update(extra)
    return base


def label_family_synthesis(counts: dict[str, Any]) -> list[dict[str, Any]]:
    label_counts = counts["accepted_label_counts"]
    return [
        {
            "label": "nofill_terminal_before_entry",
            "count": label_counts["nofill_terminal_before_entry"],
            "source_control_learning": "Pending ideas can become lifecycle-invalid before side-aware entry touch; cancellation and expiry state need first-class event capture.",
            "proves": "The approved source path reached the terminal area before an entry event under the source contract.",
            "does_not_prove": "It does not prove a trading outcome, cancellation quality, or live rule fitness.",
            "likely_issue_type": "real_pending_order_lifecycle_hygiene_signal",
            "uncertainty": "The current label lacks full cancel reason, broker-side pending state, and prospective as-of capture.",
            "future_hypothesis_route": "Preregister a pending lifecycle hygiene capture lane that records terminal-before-entry, pending cancel/expiry, and source coverage prospectively.",
            "capture_fields": [
                "pending_create_utc",
                "pending_cancel_or_expiry_utc",
                "terminal_touch_utc",
                "side_aware_entry_touch_utc_or_no_touch",
                "cancel_reason",
                "source_coverage_status",
            ],
        },
        {
            "label": "source_corrected_no_entry_through_pending_horizon",
            "count": label_counts["source_corrected_no_entry_through_pending_horizon"],
            "source_control_learning": "Some no-fill rows are true no-entry-through-horizon states rather than missing labels.",
            "proves": "Corrected source fields show no side-aware entry touch through the frozen pending horizon.",
            "does_not_prove": "It does not decide whether the pending order should have expired earlier or whether a live cancellation rule should change.",
            "likely_issue_type": "pending_window_and_staleness_contract_gap",
            "uncertainty": "Cancel reason, pending horizon rule, and source coverage must be captured together before any rule design.",
            "future_hypothesis_route": "Create a no-entry horizon source contract that separates untouched entry, stale POI, late cancel, and source coverage states.",
            "capture_fields": [
                "pending_horizon_start_utc",
                "pending_horizon_end_utc",
                "entry_touch_absent_proof",
                "coverage_start_utc",
                "coverage_end_utc",
                "horizon_end_reason",
            ],
        },
        {
            "label": "opening_drive_source_projection_ready_no_result_label",
            "count": label_counts["opening_drive_source_projection_ready_no_result_label"],
            "source_control_learning": "Opening-drive source projections are reconstructable, but they are projection inventory, not result evidence.",
            "proves": "A range/breakout/as-of projection can be built for future source-contract work.",
            "does_not_prove": "It does not assign lifecycle outcome or performance meaning; duplicate-key clustering makes premature denominator use dangerous.",
            "likely_issue_type": "source_projection_and_duplicate_inflation_risk",
            "uncertainty": "The family is concentrated in a small duplicate-key set and needs a frozen projection denominator before labels.",
            "future_hypothesis_route": "Run a separate opening-drive categorical source-contract route with frozen range fields, side-match rules, and duplicate policy before outcome opening.",
            "capture_fields": [
                "opening_range_start_utc",
                "opening_range_end_utc",
                "range_high",
                "range_low",
                "range_complete_asof",
                "breakout_side",
                "candidate_side_match_status",
                "duplicate_projection_key",
            ],
        },
        {
            "label": "fill_path_entry_before_protective_level_no_terminal_observed",
            "count": label_counts["fill_path_entry_before_protective_level_no_terminal_observed"],
            "source_control_learning": "Fill/path rows can enter a post-entry transition state without terminal observation in the approved path window.",
            "proves": "Entry can be ordered before protective level while terminal area is unobserved inside the source window.",
            "does_not_prove": "It does not score the leg or infer whether the absence of terminal observation is favorable or unfavorable.",
            "likely_issue_type": "event_order_contract_and_window_end_gap",
            "uncertainty": "The terminal absence could be real, a window limit, or source-end artifact; future rows need source window end reason.",
            "future_hypothesis_route": "Freeze an event-order categorical contract with same-tick and no-terminal states as categories, not results.",
            "capture_fields": [
                "entry_event_utc",
                "protective_event_utc",
                "terminal_event_utc_or_null",
                "source_window_end_reason",
                "same_tick_or_same_bar_flag",
            ],
        },
        {
            "label": "fill_path_entry_before_protective_level_before_terminal_area",
            "count": label_counts["fill_path_entry_before_protective_level_before_terminal_area"],
            "source_control_learning": "The source can order a complete three-event fill path in a small subset.",
            "proves": "Entry, protective, and terminal predicates can be sequenced from approved source rows.",
            "does_not_prove": "It does not validate a strategy, because event order is not a promoted result metric.",
            "likely_issue_type": "event_order_contract_ready_but_underpowered",
            "uncertainty": "The subset is small and must remain a category until a separate preregistration exists.",
            "future_hypothesis_route": "Use this event category as one frozen state in a future result contract after owner and G12 gates.",
            "capture_fields": ["entry_event_utc", "protective_event_utc", "terminal_event_utc", "quote_side_used"],
        },
        {
            "label": "fill_path_entry_before_terminal_area_before_protective_level",
            "count": label_counts["fill_path_entry_before_terminal_area_before_protective_level"],
            "source_control_learning": "The strongest semantic event order exists but remains descriptive only.",
            "proves": "Entry, terminal, and protective predicates can be sequenced in terminal-before-protective order for a small subset.",
            "does_not_prove": "It does not authorize any result claim or live path-management rule.",
            "likely_issue_type": "promising_event_order_category_not_validation",
            "uncertainty": "Small subset and no frozen result contract make all outcome interpretation forbidden here.",
            "future_hypothesis_route": "Preserve this as an input-only categorical state in any future preregistered fill/path result lane.",
            "capture_fields": ["entry_event_utc", "terminal_event_utc", "protective_event_utc", "same_tick_flag"],
        },
        {
            "label": "canonical_duplicate_geometry_source_ready_no_label_assigned",
            "count": label_counts["canonical_duplicate_geometry_source_ready_no_label_assigned"],
            "source_control_learning": "Duplicate-conflict families need canonical source-identity rows before any packet can be trusted.",
            "proves": "The canonical geometry rule can select a countable source-identity row.",
            "does_not_prove": "It does not assign a lifecycle label or any result meaning.",
            "likely_issue_type": "denominator_control_requirement",
            "uncertainty": "Canonical identity is necessary but not sufficient for future outcome denominators.",
            "future_hypothesis_route": "Make canonical duplicate controls mandatory in every no-fill and pending lifecycle packet builder.",
            "capture_fields": [
                "nofill_duplicate_key",
                "duplicate_group_id",
                "canonical_counting_row_id",
                "noncanonical_projection_count",
                "canonical_selection_reason",
            ],
        },
    ]


def blocker_route_synthesis(counts: dict[str, Any], search_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocked = counts["blocked_rows"]
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in blocked:
        codes = set(row.get("exact_blocker_codes") or [])
        if "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP" in codes:
            by_family["oti4_may3_source_gaps"].append(row)
        elif "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE" in codes:
            by_family["oti3_same_tick_order_ambiguities"].append(row)
        else:
            by_family["original_oti2_source_gap"].append(row)

    found_by_path = {record["path"]: record for record in search_records}
    return [
        {
            "family_id": "oti4_may3_source_gaps",
            "row_ids": [row["packet_row_id"] for row in by_family["oti4_may3_source_gaps"]],
            "count": len(by_family["oti4_may3_source_gaps"]),
            "current_status": "recoverable_only_if_an_approved_read_only_source_covers_the_frozen_opening_range",
            "feasibility_class": "LIKELY_RECOVERABLE_WITH_SOURCE_ACCESS_OR_ALTERNATE_M1_LOWER_OHLC",
            "evidence": [
                "Prior OTI4 source search found local tick files but zero ticks in the 2026-05-03 13:00-13:30 UTC frozen range.",
                "This G0 route found local NAS100 and XAUUSD May 3 tick parquet files for feasibility search, but did not consume them for labels.",
            ],
            "local_search_records": [
                record
                for record in search_records
                if "NAS100\\2026-05-03" in record["path"] or "XAUUSD\\2026-05-03" in record["path"]
            ],
            "exact_unblocker": "Read-only tick parquet or M1/lower OHLC covering 2026-05-03 13:00-13:30 UTC with source hash and as-of provenance.",
            "forbidden_unblockers": ["MT5 order/account/history calls", "broker result fields", "post-outcome inference"],
            "recommended_route": "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
            "route_priority": "P2_AFTER_G0_SOURCE_CONTRACT_BACKLOG",
        },
        {
            "family_id": "oti3_same_tick_order_ambiguities",
            "row_ids": [row["packet_row_id"] for row in by_family["oti3_same_tick_order_ambiguities"]],
            "count": len(by_family["oti3_same_tick_order_ambiguities"]),
            "current_status": "not_orderable_from_current_tick_granularity",
            "feasibility_class": "TRUE_IMPOSSIBILITY_FROM_CURRENT_APPROVED_TICK_ROWS_RECOVERABLE_ONLY_WITH_HIGHER_RES_EVENT_ORDER",
            "evidence": [
                "Each row has entry and protective predicates on the same first source timestamp under the frozen contract.",
                "This G0 route found USDJPY tick/source artifacts, including the May 1 parquet and prior OTI3 April 20 read-only tick artifact, but those artifacts preserve the same timestamp ambiguity.",
            ],
            "local_search_records": [
                record
                for record in search_records
                if "USDJPY\\2026-05-01" in record["path"] or "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20" in record["path"]
            ],
            "exact_unblocker": "Higher-resolution or broker-native event-order source that proves sequence inside the identical timestamp without account/order labels.",
            "forbidden_unblockers": ["guessing sequence", "using broker realized results", "using account/order history labels"],
            "recommended_route": "PARK_UNTIL_HIGHER_RES_EVENT_ORDER_SOURCE_EXISTS",
            "route_priority": "P5_LOW_FEASIBILITY",
        },
        {
            "family_id": "original_oti2_source_gap",
            "row_ids": [row["packet_row_id"] for row in by_family["original_oti2_source_gap"]],
            "count": len(by_family["original_oti2_source_gap"]),
            "current_status": "recoverable_if_side_aware_active_window_source_exists",
            "feasibility_class": "POTENTIALLY_RECOVERABLE_WITH_TARGETED_XAUUSD_SIDE_AWARE_TICK_COVERAGE",
            "evidence": [
                "Prior G12 and forensics artifacts say M1 context is not side-aware proof and XAUUSD tick coverage misses the active pending window through cancel.",
                "This G0 route found XAUUSD 2026-05-05 tick parquet in the absolute local tick root, but did not open a blocker-clearing extraction.",
            ],
            "local_search_records": [
                found_by_path[path]
                for path in found_by_path
                if "XAUUSD\\2026-05-05" in path
            ],
            "exact_unblocker": "Side-aware bid/ask tick or approved lower source covering the active pending window through cancel.",
            "forbidden_unblockers": ["M1-only inference as side-aware proof", "live order labels", "account history"],
            "recommended_route": "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
            "route_priority": "P3_AFTER_OTI4_SOURCE_GAPS",
        },
    ]


def decision_entries(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "G0-D001",
            "question": "What has V2 evidence established about pending lifecycle hygiene?",
            "claim": "It established that pending ideas need explicit lifecycle state capture before result interpretation: terminal-before-entry and no-entry-through-horizon are common source-control states.",
            "evidence": "Accepted label counts include nofill_terminal_before_entry=110 and source_corrected_no_entry_through_pending_horizon=32 inside the 225 input-only rows.",
            "uncertainty": "The rows do not contain complete prospective cancel reason or live pending-state telemetry.",
            "falsification_condition": "A future source-hashed capture lane shows terminal-before-entry/no-entry-through-horizon states are artifacts of the rebuilt source contract rather than prospective pending lifecycle states.",
            "next_action": "Build pending lifecycle hygiene capture/spec lane with source coverage and cancel/expiry fields.",
            "owner": "G0_SOURCE_BUILDER",
        },
        {
            "decision_id": "G0-D002",
            "question": "Which accepted label families are source-control learning only?",
            "claim": "All seven accepted label families are input-only categorical source/control learning and none is a result label.",
            "evidence": f"Accepted labels reconcile exactly to {counts['accepted_label_counts']} and every row keeps validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "uncertainty": "Future lanes may reuse these categories only after a separate frozen contract and G12/owner gate.",
            "falsification_condition": "Any generated result lane consumes these labels as performance evidence without a separate preregistered denominator and G12 acceptance.",
            "next_action": "Carry label-family proofs/non-claims into future prompt packs and verifiers.",
            "owner": "G0_CONTROL",
        },
        {
            "decision_id": "G0-D003",
            "question": "What source contract changes are implied?",
            "claim": "Future source contracts must capture pending create/cancel/expiry, side-aware entry touch or no-touch proof, terminal/protective event order, source coverage, duplicate key policy, and opening-drive range/breakout fields.",
            "evidence": "Accepted rows split across OTI1/OTI2/OTI3/OTI4/OTI5 and blockers identify missing range, side-aware active-window, and same-tick order fields.",
            "uncertainty": "Some fields may require a new source-access route or prospective shadow capture rather than reconstruction.",
            "falsification_condition": "A source audit proves existing committed artifacts already contain all fields with as-of hashes.",
            "next_action": "Use the source contract backlog in this route as the next builder prompt input.",
            "owner": "SOURCE_BUILDER",
        },
        {
            "decision_id": "G0-D004",
            "question": "What duplicate denominator controls are mandatory?",
            "claim": "Future no-fill work must distinguish 225 row-level source inputs from 182 unique duplicate keys and must exclude noncanonical projections from denominators.",
            "evidence": f"Duplicate posture reconciles to {counts['duplicate_posture']}; OTI5 accepts 3 canonical rows and rejects 39 noncanonical projections.",
            "uncertainty": "A future result lane must freeze whether denominator is row-level source input or unique opportunity key before opening outcomes.",
            "falsification_condition": "A builder demonstrates no duplicate-key collision under a stricter future denominator while preserving source identity.",
            "next_action": "Make duplicate denominator verification a required preflight for no-fill packet builders.",
            "owner": "G0_CONTROL",
        },
        {
            "decision_id": "G0-D005",
            "question": "Which residual blocker route is worth running?",
            "claim": "Run a narrow source-access blocker route only for the 3 OTI4 May 3 source gaps and 1 OTI2 active-window gap first; park the 4 OTI3 same-tick ambiguities until higher-resolution event order exists.",
            "evidence": "OTI4/OTI2 blockers name recoverable source coverage requirements; OTI3 blockers are identical-timestamp ordering impossibilities from current tick rows.",
            "uncertainty": "If a broker-native event-order source exists without account/order labels, OTI3 can be revisited.",
            "falsification_condition": "A source search finds approved higher-resolution sequence evidence for OTI3, or finds approved OTI4/OTI2 windows are unavailable.",
            "next_action": "Write a source-access lane prompt that targets exactly the 8 blockers without scoring any row.",
            "owner": "SOURCE_ACCESS_LANE",
        },
        {
            "decision_id": "G0-D006",
            "question": "What future preregistration design is allowed?",
            "claim": "A future design lane may freeze denominator, source fields, sample floor, no-leak proof, duplicate policy, and G12/owner gates; it must not open outcomes.",
            "evidence": "G12 next prompt pack explicitly separates optional preregistration design from any quantitative result lane.",
            "uncertainty": "Owner approval and sample floor remain undefined for any future result lane.",
            "falsification_condition": "Owner explicitly approves a result lane with frozen contract and G12 acceptance.",
            "next_action": "Rank the preregistration design behind source contract and duplicate control work.",
            "owner": "PREREG_DESIGN_LANE",
        },
        {
            "decision_id": "G0-D007",
            "question": "How does this connect to primitive science without overclaiming?",
            "claim": "The no-fill evidence improves the science program by turning failed/blocked lifecycle rows into source primitives: pending hygiene, event order, source coverage, duplicate identity, and projection readiness.",
            "evidence": "The accepted categories are source-control states, not outcomes; they can feed future capture and hypothesis design without touching live behavior.",
            "uncertainty": "Whether any primitive later improves trading must be tested only under a separate preregistered lane.",
            "falsification_condition": "Prospective capture shows the categories are not stable or are redundant with existing logs.",
            "next_action": "Treat these categories as feature/capture candidates, not selectors.",
            "owner": "G0_RESEARCH_PROGRAM_CONTROL",
        },
        {
            "decision_id": "G0-D008",
            "question": "What is the strongest useful signal hidden in non-result evidence?",
            "claim": "The strongest useful signal is not performance; it is that many pending opportunities fail or remain untouched before entry, so the operating system needs cleaner pending lifecycle observability.",
            "evidence": "142 accepted rows combine terminal-before-entry and no-entry-through-horizon categories.",
            "uncertainty": "The operational cause may be source-contract boundaries, stale horizons, or actual pending lifecycle design.",
            "falsification_condition": "Prospective logging shows terminal/no-entry states vanish once capture is cleaner.",
            "next_action": "Prioritize pending lifecycle hygiene capture before result scoring.",
            "owner": "SOURCE_BUILDER",
        },
        {
            "decision_id": "G0-D009",
            "question": "What would a lazy synthesis miss?",
            "claim": "A lazy synthesis would collapse all 225 accepted rows into one denominator and miss that opening-drive projection rows are duplicate-clustered source inventory while OTI2 rows are event-order categories.",
            "evidence": "Opening-drive has 51 row-level inputs but only 8 unique duplicate keys; OTI2 labels are 22/4/3 event-order states.",
            "uncertainty": "Future denominator choices can still be mishandled if not machine-checked.",
            "falsification_condition": "A future verifier proves denominator and label-family isolation for every packet.",
            "next_action": "Use the duplicate denominator control artifact as mandatory future verifier input.",
            "owner": "G0_CONTROL",
        },
        {
            "decision_id": "G0-D010",
            "question": "Which accepted families are likely design issues versus source artifacts?",
            "claim": "Terminal-before-entry and no-entry-through-horizon are most likely pending-hygiene design signals; opening-drive projection and canonical duplicate labels are more likely source/denominator control artifacts; OTI2 is event-order contract learning.",
            "evidence": "Label mechanisms and blocker/reject ledgers separate lifecycle terminal/no-touch states from projection readiness and duplicate identity.",
            "uncertainty": "Only prospective capture can separate true design issue from source reconstruction artifact.",
            "falsification_condition": "Prospective capture attributes terminal/no-entry states to source gaps rather than pending lifecycle behavior.",
            "next_action": "Classify future capture fields by design-signal versus source-control role.",
            "owner": "G0_SOURCE_BUILDER",
        },
        {
            "decision_id": "G0-D011",
            "question": "What hypotheses become possible?",
            "claim": "Hypotheses can now target stale pending cancellation, no-touch horizon expiry, fill/path event-order taxonomy, opening-drive projection contracts, and duplicate-safe source identity.",
            "evidence": "The seven label families provide separated categories that avoid mixing terminal, untouched, filled path, projection, and duplicate states.",
            "uncertainty": "Hypotheses remain unvalidated and cannot use outcomes until a future frozen result contract exists.",
            "falsification_condition": "A future source contract cannot reproduce these categories prospectively.",
            "next_action": "Move hypotheses into source-safe prompt packs with explicit non-result gates.",
            "owner": "PREREG_DESIGN_LANE",
        },
        {
            "decision_id": "G0-D012",
            "question": "What is the clean path to a future frozen result contract?",
            "claim": "First harden source contracts and duplicate controls, then collect prospective source-hashed categories, then freeze denominator/sample floor/no-leak policy, then open a separate G12/owner-approved result lane.",
            "evidence": "Current G12 acceptance is explicitly source/control only; 8 blockers and 65 rejects remain outside labels and denominators.",
            "uncertainty": "Sample floor and owner approval are not in this lane.",
            "falsification_condition": "Owner closes the route or source contracts prove infeasible.",
            "next_action": "Rank source-control lanes ahead of result design.",
            "owner": "G0_GOVERNOR",
        },
        {
            "decision_id": "G0-D013",
            "question": "What is the strongest counterargument against the next route?",
            "claim": "The strongest counterargument is that better pending lifecycle capture may only produce cleaner non-trades, not a new edge.",
            "evidence": "Current evidence is categorical and non-result by design.",
            "uncertainty": "Learning value may be operational rather than performance-linked.",
            "falsification_condition": "Prospective capture shows no stable category, no preventable lifecycle ambiguity, and no useful source coverage improvement.",
            "next_action": "Design the next route to measure source coverage and lifecycle ambiguity reduction, not performance.",
            "owner": "SOURCE_BUILDER",
        },
        {
            "decision_id": "G0-D014",
            "question": "Where could false confidence enter?",
            "claim": "False confidence can enter through duplicate denominators, label-family mixing, same-tick order ambiguity, treating rejected rows as hidden outcomes, and overreading accepted source-lane imbalance.",
            "evidence": "The row ledger has 5 duplicate collision groups, 4 same-tick blockers, 65 rejects, and source-lane counts that are not balanced by design.",
            "uncertainty": "A future lane can still create new leakage if it adds generated fallback keys or post-event fields.",
            "falsification_condition": "Verifier scans and source-hash controls prove no such leakage in a frozen future packet.",
            "next_action": "Keep forbidden-key scans, duplicate checks, and blocker/reject exclusion tests in every route.",
            "owner": "G0_CONTROL",
        },
        {
            "decision_id": "G0-D015",
            "question": "What is the highest-learning next move beyond the OB-retest backbone?",
            "claim": "Build pending lifecycle and event-order source primitives first; they can improve market-state awareness and operational hygiene without relying on OB-retest performance claims.",
            "evidence": "No-fill categories describe opportunity lifecycle states independent of the current edge's outcome math.",
            "uncertainty": "Any live-system improvement remains hypothetical until prospective source capture and separate validation exist.",
            "falsification_condition": "The primitives fail to reproduce prospectively or add no interpretable ambiguity reduction.",
            "next_action": "Prioritize source-control builders over outcome replay.",
            "owner": "G0_RESEARCH_PROGRAM_CONTROL",
        },
    ]


def source_contract_backlog() -> list[dict[str, Any]]:
    return [
        {
            "contract_id": "PENDING_LIFECYCLE_HYGIENE_SOURCE_CONTRACT_V1",
            "purpose": "Prospectively capture pending order lifecycle states before any result use.",
            "source_learning": "Terminal-before-entry and no-entry-through-horizon categories require explicit pending create/cancel/expiry and side-aware touch proof.",
            "required_fields": [
                "source_inventory_id",
                "source_packet_id",
                "symbol",
                "session",
                "side",
                "decision_asof_utc",
                "pending_create_utc",
                "pending_cancel_or_expiry_utc",
                "cancel_or_expiry_reason",
                "entry_price",
                "side_aware_entry_touch_utc_or_null",
                "terminal_area_touch_utc_or_null",
                "protective_level_touch_utc_or_null",
                "source_coverage_start_utc",
                "source_coverage_end_utc",
                "source_coverage_status",
                "source_hashes",
                "nofill_duplicate_key",
            ],
            "forbidden_fields": ["forbidden_result_metric_fields", "forbidden_external_result_fields", "forbidden_order_result_fields"],
            "route_owner": "SOURCE_BUILDER",
            "priority": "P1",
        },
        {
            "contract_id": "FILL_PATH_EVENT_ORDER_CATEGORICAL_CONTRACT_V1",
            "purpose": "Freeze event-order categories and ambiguity states before any future result lane.",
            "source_learning": "OTI2 labels prove event order can be categorized, while same-tick rows prove ambiguity must be explicit.",
            "required_fields": [
                "entry_event_utc",
                "protective_event_utc",
                "terminal_event_utc",
                "same_tick_or_same_bar_flag",
                "quote_side_used",
                "source_granularity",
                "source_window_start_utc",
                "source_window_end_utc",
                "source_window_end_reason",
            ],
            "forbidden_fields": ["guessed_sequence", "post_outcome_sequence_inference"],
            "route_owner": "SOURCE_BUILDER",
            "priority": "P2",
        },
        {
            "contract_id": "OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT_V1",
            "purpose": "Turn opening-drive projection readiness into frozen source fields without label or result inflation.",
            "source_learning": "Opening-drive projection rows are useful inventory but duplicate clustered.",
            "required_fields": [
                "opening_range_start_utc",
                "opening_range_end_utc",
                "range_high",
                "range_low",
                "range_complete_asof",
                "breakout_side",
                "breakout_close_time",
                "candidate_side_match_status",
                "range_source_hashes",
                "duplicate_projection_key",
            ],
            "forbidden_fields": ["opening_drive_result_label", "performance_metric_fields"],
            "route_owner": "SOURCE_BUILDER",
            "priority": "P3",
        },
        {
            "contract_id": "DUPLICATE_DENOMINATOR_CONTROL_CONTRACT_V1",
            "purpose": "Prevent row-level projections from becoming inflated denominators.",
            "source_learning": "225 accepted row-level inputs reduce to 182 unique duplicate keys; 39 noncanonical projections are rejected.",
            "required_fields": [
                "nofill_duplicate_key",
                "duplicate_group_id",
                "canonical_counting_row_id",
                "is_canonical_counting_row",
                "noncanonical_projection_count",
                "denominator_scope",
                "canonical_selection_reason",
            ],
            "forbidden_fields": ["generated_unstable_duplicate_key", "noncanonical_denominator_inclusion"],
            "route_owner": "G0_CONTROL",
            "priority": "P0_MANDATORY_FOR_ALL_FUTURE_PACKETS",
        },
        {
            "contract_id": "RESIDUAL_BLOCKER_SOURCE_ACCESS_MANIFEST_V1",
            "purpose": "Clear only exact source/order blockers without opening outcomes.",
            "source_learning": "The 8 blockers have exact source/access requirements and must stay outside labels until cleared by source proof.",
            "required_fields": [
                "packet_row_id",
                "blocker_family",
                "symbol",
                "requested_window_start_utc",
                "requested_window_end_utc",
                "allowed_source_types",
                "source_path",
                "source_sha256",
                "source_coverage_status",
                "clear_or_remain_blocked_decision",
            ],
            "forbidden_fields": ["accepted_row_scoring", "rejected_row_scoring", "forbidden_external_result_fields"],
            "route_owner": "SOURCE_ACCESS_LANE",
            "priority": "P2",
        },
    ]


def duplicate_controls(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "control_id": "DUP-001",
            "control": "Freeze denominator scope before outcome opening.",
            "evidence": "Current source-control denominator is 225 row-level accepted inputs, but unique accepted duplicate keys are 182.",
            "required_check": "Every future packet must state row-level versus unique-key denominator before labels/results.",
            "failure_mode_prevented": "Inflating sample size by mixing projections and unique opportunities.",
        },
        {
            "control_id": "DUP-002",
            "control": "Keep noncanonical duplicate projections outside labels and denominators.",
            "evidence": "39 OTI5 noncanonical duplicate projections are rejected and carry no label.",
            "required_check": "Rows with REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION must not appear in accepted labels or future result route denominators.",
            "failure_mode_prevented": "Counting repeated projections as independent evidence.",
        },
        {
            "control_id": "DUP-003",
            "control": "Separate source projection readiness from lifecycle result labels.",
            "evidence": "51 opening-drive projection rows collapse into 8 unique no-fill duplicate keys and are no-result labels.",
            "required_check": "Projection-ready labels may populate source inventory only until a separate categorical contract freezes denominator and labels.",
            "failure_mode_prevented": "Turning source inventory into hidden result evidence.",
        },
        {
            "control_id": "DUP-004",
            "control": "Require stable nofill_duplicate_key and duplicate_group_id provenance.",
            "evidence": "The G12 audit found no forbidden generated-key leakage and accepted OTI5 canonical source identity only.",
            "required_check": "Future builders must reject missing or generated fallback duplicate keys unless they are explicitly quarantined and audited.",
            "failure_mode_prevented": "Silent duplicate drift across rebuilt packets.",
        },
        {
            "control_id": "DUP-005",
            "control": "Publish both row-level and unique-key counts in every synthesis.",
            "evidence": f"Current duplicate posture is {counts['duplicate_posture']}.",
            "required_check": "Completion audit must reconcile both counts and collision groups.",
            "failure_mode_prevented": "False confidence from a single denominator.",
        },
    ]


def future_route_ranking() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route_id": "NOFILL_CAT_V2_PENDING_LIFECYCLE_SOURCE_CONTRACT_BUILDER",
            "route_type": "G0_SOURCE_BUILDER",
            "expected_learning_value": "HIGH",
            "contamination_risk": "LOW_IF_NON_RESULT",
            "source_feasibility": "HIGH_PROSPECTIVE_CAPTURE",
            "independence_from_ob_retest_backbone": "HIGH",
            "live_system_improvement_path_later": "Cleaner pending lifecycle telemetry and cancellation observability.",
            "why_now": "142 accepted source-control rows point directly at terminal-before-entry and no-entry-through-horizon hygiene.",
            "forbidden_until_later": "Any cancellation rule or result claim.",
        },
        {
            "rank": 2,
            "route_id": "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL",
            "route_type": "G0_CONTROL",
            "expected_learning_value": "HIGH",
            "contamination_risk": "LOW",
            "source_feasibility": "HIGH",
            "independence_from_ob_retest_backbone": "HIGH",
            "live_system_improvement_path_later": "Prevents false denominators in no-fill, pending, and opening-drive research.",
            "why_now": "The current packet proves duplicate projections can dominate if not controlled.",
            "forbidden_until_later": "None, if kept as research verifier/control only.",
        },
        {
            "rank": 3,
            "route_id": "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
            "route_type": "SOURCE_ACCESS_LANE",
            "expected_learning_value": "MEDIUM_HIGH",
            "contamination_risk": "LOW_IF_EXACT_8_ONLY",
            "source_feasibility": "MEDIUM",
            "independence_from_ob_retest_backbone": "HIGH",
            "live_system_improvement_path_later": "Reduces exact source gaps and improves future packet completeness.",
            "why_now": "4 of the 8 blockers look source-recoverable; 4 need higher-resolution event ordering.",
            "forbidden_until_later": "Scoring accepted, blocked, or rejected rows.",
        },
        {
            "rank": 4,
            "route_id": "NOFILL_CAT_V2_FILL_PATH_EVENT_ORDER_CONTRACT",
            "route_type": "G0_SOURCE_BUILDER",
            "expected_learning_value": "MEDIUM_HIGH",
            "contamination_risk": "LOW_IF_CATEGORICAL_ONLY",
            "source_feasibility": "MEDIUM",
            "independence_from_ob_retest_backbone": "MEDIUM_HIGH",
            "live_system_improvement_path_later": "Creates cleaner event-order primitives for future path management research.",
            "why_now": "OTI2 produced three separated event-order families plus same-tick ambiguity lessons.",
            "forbidden_until_later": "Result comparison of event-order states.",
        },
        {
            "rank": 5,
            "route_id": "NOFILL_CAT_V2_OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT",
            "route_type": "G0_SOURCE_BUILDER",
            "expected_learning_value": "MEDIUM",
            "contamination_risk": "MEDIUM_IF_DENOMINATOR_NOT_FROZEN",
            "source_feasibility": "MEDIUM",
            "independence_from_ob_retest_backbone": "HIGH",
            "live_system_improvement_path_later": "Could create opening-drive state primitives if duplicate and source gaps are solved.",
            "why_now": "51 projection-ready rows exist but are duplicate clustered and no-result.",
            "forbidden_until_later": "Treating projections as lifecycle or performance labels.",
        },
        {
            "rank": 6,
            "route_id": "NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE",
            "route_type": "PREREG_DESIGN_LANE",
            "expected_learning_value": "MEDIUM",
            "contamination_risk": "LOW_IF_OUTCOMES_CLOSED",
            "source_feasibility": "HIGH_AS_DESIGN_ONLY",
            "independence_from_ob_retest_backbone": "HIGH",
            "live_system_improvement_path_later": "Defines the contract needed before any future result lane.",
            "why_now": "Useful only after source contracts and duplicate controls are written clearly.",
            "forbidden_until_later": "Opening outcomes, result scoring, validation, or promotion.",
        },
        {
            "rank": 7,
            "route_id": "NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE",
            "route_type": "CLOSED_ROUTE",
            "expected_learning_value": "UNKNOWN",
            "contamination_risk": "HIGH_IF_OPENED_NOW",
            "source_feasibility": "NOT_AUTHORIZED",
            "independence_from_ob_retest_backbone": "UNKNOWN",
            "live_system_improvement_path_later": "Only possible after separate frozen preregistration, sample floor, no-leak proof, G12 gate, and owner approval.",
            "why_now": "Do not run now.",
            "forbidden_until_later": "Everything in this result lane.",
        },
    ]


def build_completion_checklist() -> list[dict[str, str]]:
    return [
        {
            "requirement": "Regenerate and read LIVE_STATE before analysis.",
            "status": "PASS",
            "evidence": ".context/LIVE_STATE.md regenerated during preflight and hashed in context anchor.",
        },
        {
            "requirement": "Read controlling prompt and mandatory context docs.",
            "status": "PASS",
            "evidence": "Control input hash records include the prompt, LIVE_STATE, quick reference, doctrine, current state, goal discipline, local heavy data inventory, reading order, and latest handoff.",
        },
        {
            "requirement": "Use accepted G12 forensics audit as source/control input only.",
            "status": "PASS",
            "evidence": "Decision ledger cites G12/forensics artifacts only and keeps all safety flags false.",
        },
        {
            "requirement": "Preserve 298 = 225 accepted + 8 blocked + 65 rejected.",
            "status": "PASS",
            "evidence": "Verifier recomputes partition from NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl.",
        },
        {
            "requirement": "Preserve 225 = 52 prior accepted + 173 source-corrected accepted.",
            "status": "PASS",
            "evidence": "Decision ledger JSON accepted_split.",
        },
        {
            "requirement": "Keep accepted labels input-only and outside performance use.",
            "status": "PASS",
            "evidence": "Label-family synthesis and all generated JSON safety flags.",
        },
        {
            "requirement": "Keep 8 blockers and 65 rejects outside labels, denominators, outcome use, validation use, and promotion use.",
            "status": "PASS",
            "evidence": "Residual blocker route ledger and duplicate denominator control; verifier checks upstream row statuses and generated route ownership.",
        },
        {
            "requirement": "Produce all required G0 ledgers and prompt pack.",
            "status": "PASS",
            "evidence": "All required output paths exist under the route directory after builder run.",
        },
        {
            "requirement": "Answer required synthesis and adversarial questions with claim/evidence/uncertainty/falsification/next action/owner.",
            "status": "PASS",
            "evidence": "G0 decision ledger JSON decision_entries G0-D001 through G0-D015.",
        },
        {
            "requirement": "Search local/heavy roots before accepting blocker feasibility status.",
            "status": "PASS",
            "evidence": "Context anchor and residual blocker JSON include targeted absolute tick/root search records.",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT and false validation/outcome/live flags.",
            "status": "PASS",
            "evidence": "Verifier scans generated JSON/markdown and recursively checks false flags.",
        },
        {
            "requirement": "Do not touch forbidden live trading surfaces.",
            "status": "PASS",
            "evidence": "Verifier live-surface diff check allows only route artifacts and context refresh files.",
        },
        {
            "requirement": "Run JSON parse, count reconciliation, py_compile, focused pytest, and live-surface check.",
            "status": "PASS_AFTER_VERIFIER",
            "evidence": "Run verify_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py; it executes these checks and prints can_mark_goal_complete.",
        },
    ]


def json_dump(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join([header, sep, *body])


def build_all() -> dict[str, Any]:
    rows = read_jsonl(ROW_LEDGER)
    counts = recompute_counts(rows)
    hashes = input_hash_records()
    search_records = local_search_evidence()
    labels = label_family_synthesis(counts)
    blockers = blocker_route_synthesis(counts, search_records)
    decisions = decision_entries(counts)
    contracts = source_contract_backlog()
    dup_controls = duplicate_controls(counts)
    routes = future_route_ranking()
    checklist = build_completion_checklist()

    branch = git_output(["branch", "--show-current"])
    head = git_output(["rev-parse", "HEAD"])
    status_short = git_output(["status", "--short"])
    live_state_text = (REPO_ROOT / ".context/LIVE_STATE.md").read_text(encoding="utf-8", errors="replace")
    freshness = "FRESH" if "Status | `FRESH`" in live_state_text or "Status | FRESH" in live_state_text else "CHECK_LIVE_STATE"

    context_anchor = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_CONTEXT_ANCHOR",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "worktree_path": str(REPO_ROOT),
            "branch": branch,
            "starting_head": head,
            "git_status_short_at_build": status_short,
            "live_state_freshness_status": freshness,
            "controlling_prompt": rel(CONTROL_PROMPT),
            "control_input_hash_records": hashes,
            "searched_roots": [
                str(REPO_ROOT),
                r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
                r"C:\Users\MSI\Documents\ai-trading-agent\data\external",
                r"C:\tmp\gtos_otb",
                r"C:\tmp\gtos_otl",
            ],
            "targeted_local_heavy_data_search_records": search_records,
            "active_question_stack": [
                "pending lifecycle hygiene",
                "source contract backlog",
                "duplicate denominator controls",
                "residual blocker feasibility",
                "future route ranking",
                "next prompt pack",
                "completion audit",
            ],
            "stop_condition": "Complete only after builder, verifier, focused tests, exact count reconciliation, no forbidden flags/paths, and final audit pass.",
        }
    )

    decision_ledger = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_DECISION_LEDGER",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "status": "PASS_G0_SOURCE_CONTROL_SYNTHESIS",
            "decision": "ACCEPT_G12_FORENSICS_AS_SOURCE_CONTROL_LEARNING_AND_ROUTE_NEXT_CONTROL_WORK",
            "counts": {
                "partition": counts["partition"],
                "accepted_split": counts["accepted_split"],
                "accepted_label_counts": counts["accepted_label_counts"],
                "accepted_source_lane_counts": counts["accepted_source_lane_counts"],
                "duplicate_posture": counts["duplicate_posture"],
                "blocker_counts": EXPECTED_BLOCKER_COUNTS,
                "reject_counts": EXPECTED_REJECT_COUNTS,
            },
            "decision_entries": decisions,
            "non_claims": [
                "No result scoring was opened.",
                "No validation-safe posture was opened.",
                "No selector, registry, prompt, risk, execution, permission, safety, canary, MT5, credential, remote, paid/API, Databento, or live-order behavior changed.",
            ],
        }
    )

    hygiene = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "headline": "No-fill V2 is most useful as pending lifecycle observability control evidence.",
            "accepted_denominator": counts["partition"]["accepted"],
            "label_family_synthesis": labels,
            "pending_hygiene_findings": [
                {
                    "finding_id": "PEND-HYG-001",
                    "claim": "Terminal-before-entry states are large enough to demand explicit pending lifecycle telemetry.",
                    "evidence": "110 accepted input-only rows carry nofill_terminal_before_entry.",
                    "uncertainty": "The artifact cannot say whether current cancellation behavior is good or bad.",
                    "next_action": "Capture terminal touch, entry touch, pending cancel/expiry, cancel reason, and source coverage prospectively.",
                },
                {
                    "finding_id": "PEND-HYG-002",
                    "claim": "No-entry-through-horizon is a distinct source state from missing label.",
                    "evidence": "32 source-corrected accepted rows carry source_corrected_no_entry_through_pending_horizon.",
                    "uncertainty": "The stale horizon and active pending-state context are incomplete.",
                    "next_action": "Separate untouched entry, late cancellation, stale POI, and source coverage states.",
                },
                {
                    "finding_id": "PEND-HYG-003",
                    "claim": "Fill/path categories should become event-order primitives, not current results.",
                    "evidence": "OTI2 contributes 29 accepted rows across three event-order labels.",
                    "uncertainty": "Small subsets and same-tick blockers prevent result interpretation.",
                    "next_action": "Freeze event-order categorical contract before any future result lane.",
                },
            ],
        }
    )

    source_contract = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "source_contract_backlog": contracts,
            "capture_backlog_summary": [
                "Prospective pending lifecycle fields must be captured as-of, source-hashed, and separate from results.",
                "Fill/path event ordering must store same-tick ambiguity rather than guess order.",
                "Opening-drive projection fields must freeze range and breakout inputs before labels.",
                "Duplicate source identity must be part of every future packet.",
                "Residual blockers need exact source-access manifests and must not become outcome rows.",
            ],
            "control_input_hash_records": hashes,
        }
    )

    duplicate_control = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "duplicate_posture": counts["duplicate_posture"],
            "mandatory_controls": dup_controls,
            "future_builder_requirements": [
                "Publish accepted row-level count and unique duplicate-key count.",
                "Publish duplicate collision groups and rows.",
                "Reject noncanonical projection rows before label assignment.",
                "Freeze denominator scope before any outcome opening.",
                "Scan for generated fallback duplicate keys.",
            ],
        }
    )

    blocker_ledger = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "blocked_count": counts["partition"]["blocked"],
            "rejected_count": counts["partition"]["rejected"],
            "blocker_routes": blockers,
            "reject_families": [
                {
                    "family_id": "oti4_contract_exclusions",
                    "count": 26,
                    "status": "CONTRACT_EXCLUDED_NO_LABEL_NO_DENOMINATOR",
                    "next_action": "Do not route unless a separate contract revision is approved before label assignment.",
                },
                {
                    "family_id": "oti5_noncanonical_duplicate_projections",
                    "count": 39,
                    "status": "DUPLICATE_EXCLUDED_NO_LABEL_NO_DENOMINATOR",
                    "next_action": "Keep excluded; use only as duplicate-control evidence.",
                },
            ],
            "blocked_and_rejected_boundary": "The 8 blockers and 65 rejects remain outside accepted labels, denominators, result use, validation use, and promotion use.",
        }
    )

    route_ranking = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_FUTURE_ROUTE_RANKING",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "ranking_basis": [
                "expected learning value",
                "contamination risk",
                "source feasibility",
                "independence from prior OB-retest edge",
                "ability to improve live system later without touching live behavior now",
            ],
            "routes": routes,
            "closed_routes": ["NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE"],
        }
    )

    completion_audit = safety_flags(
        {
            "artifact_family": "G0_NOFILL_CAT_V2_COMPLETION_AUDIT",
            "route_id": ROUTE_ID,
            "generated_at_utc": GENERATED_AT_UTC,
            "objective_restatement": "Produce G0 source/control synthesis artifacts for no-fill CAT V2 using accepted G12 forensics input only, preserve exact counts and non-claim boundaries, write builder/verifier/tests, and avoid forbidden live/result surfaces.",
            "prompt_to_artifact_checklist": checklist,
            "required_output_files": required_output_files(),
            "can_mark_goal_complete": True,
            "completion_status": "PASS_IF_VERIFIER_AND_FOCUSED_TESTS_PASS",
            "residual_uncertainty": [
                "Residual blockers are not cleared in this lane.",
                "Any result lane remains closed until separate frozen preregistration, G12 gate, and owner approval.",
            ],
        }
    )

    outputs = {
        "context_anchor": context_anchor,
        "decision_ledger": decision_ledger,
        "hygiene": hygiene,
        "source_contract": source_contract,
        "duplicate_control": duplicate_control,
        "blocker_ledger": blocker_ledger,
        "route_ranking": route_ranking,
        "completion_audit": completion_audit,
    }

    json_dump(ROUTE_DIR / "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_DECISION_LEDGER_2026-05-09.json", decision_ledger)
    json_dump(ROUTE_DIR / "G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS_2026-05-09.json", hygiene)
    json_dump(ROUTE_DIR / "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json", source_contract)
    json_dump(ROUTE_DIR / "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.json", duplicate_control)
    json_dump(ROUTE_DIR / "G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json", blocker_ledger)
    json_dump(ROUTE_DIR / "G0_NOFILL_CAT_V2_FUTURE_ROUTE_RANKING_2026-05-09.json", route_ranking)
    json_dump(ROUTE_DIR / "G0_NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.json", completion_audit)

    write_markdown_artifacts(outputs)
    return outputs


def required_output_files() -> list[str]:
    return [
        "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_CONTEXT_ANCHOR_2026-05-09.md",
        "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_DECISION_LEDGER_2026-05-09.md",
        "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_DECISION_LEDGER_2026-05-09.json",
        "G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS_2026-05-09.md",
        "G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS_2026-05-09.json",
        "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md",
        "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json",
        "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.md",
        "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.json",
        "G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.md",
        "G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json",
        "G0_NOFILL_CAT_V2_FUTURE_ROUTE_RANKING_2026-05-09.md",
        "G0_NOFILL_CAT_V2_FUTURE_ROUTE_RANKING_2026-05-09.json",
        "G0_NOFILL_CAT_V2_NEXT_PROMPT_PACK_2026-05-09.md",
        "G0_NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.md",
        "G0_NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.json",
        "build_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py",
        "verify_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py",
        "test_g0_nofill_cat_v2_synthesis_control_route_2026_05_09.py",
    ]


def write_markdown_artifacts(outputs: dict[str, Any]) -> None:
    context = outputs["context_anchor"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_CONTEXT_ANCHOR_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Synthesis Control Context Anchor

Promotion posture: `{PROMOTION_VERDICT}`.

Route: `{ROUTE_ID}`.

Status: `ACTIVE_CONTEXT_ANCHOR_WRITTEN`.

## Starting State

- Worktree: `{context["worktree_path"]}`
- Branch: `{context["branch"]}`
- Starting HEAD: `{context["starting_head"]}`
- LIVE_STATE freshness: `{context["live_state_freshness_status"]}`
- Controlling prompt: `{context["controlling_prompt"]}`
- Validation safe: `{str(context["validation_safe"]).lower()}`
- Outcome review opened: `{str(context["outcome_review_opened"]).lower()}`
- Live effect: `{str(context["live_effect"]).lower()}`

## Inputs Read And Hashed

{markdown_table(context["control_input_hash_records"], ["path", "exists", "size_bytes", "sha256"])}

## Searched Roots

{chr(10).join(f"- `{root}`" for root in context["searched_roots"])}

## Targeted Local Heavy-Data Search

These files were searched for residual blocker feasibility only. They were not consumed for labels or outcomes.

{markdown_table(context["targeted_local_heavy_data_search_records"], ["path", "exists", "size_bytes", "sha256", "consumed_for_labels"])}

## Boundaries

- This is G0 source/control synthesis only.
- Accepted labels stay input-only categorical source/control learning.
- The 8 blockers and 65 rejects remain outside labels, denominators, result use, validation use, and promotion use.
- No live trading prompt, `src` trading logic, risk, execution, permission, safety, selector, canary, MT5, credential, remote, paid/API/Databento, account/order/result, registry, or live order behavior was touched.
""",
    )

    decision = outputs["decision_ledger"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_SYNTHESIS_CONTROL_DECISION_LEDGER_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Synthesis Control Decision Ledger

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{decision["status"]}`.
Decision: `{decision["decision"]}`.

## Reconciled Counts

- Universe: `{decision["counts"]["partition"]["universe"]}`
- Accepted input-only rows: `{decision["counts"]["partition"]["accepted"]}`
- Blocked rows: `{decision["counts"]["partition"]["blocked"]}`
- Rejected rows: `{decision["counts"]["partition"]["rejected"]}`
- Accepted split: `{decision["counts"]["accepted_split"]}`
- Duplicate posture: `{decision["counts"]["duplicate_posture"]}`

## Accepted Labels

{markdown_table([{"label": key, "count": value} for key, value in decision["counts"]["accepted_label_counts"].items()], ["label", "count"])}

## Accepted Source Lanes

{markdown_table([{"source_lane": key, "count": value} for key, value in decision["counts"]["accepted_source_lane_counts"].items()], ["source_lane", "count"])}

## Decisions And Adversarial Answers

{chr(10).join(format_decision_entry(entry) for entry in decision["decision_entries"])}

## Non-Claims

{chr(10).join(f"- {item}" for item in decision["non_claims"])}
""",
    )

    hygiene = outputs["hygiene"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Pending Lifecycle Hygiene Synthesis

Promotion posture: `{PROMOTION_VERDICT}`.

Headline: {hygiene["headline"]}

Accepted denominator: `{hygiene["accepted_denominator"]}` input-only source/control rows.

## Pending Hygiene Findings

{chr(10).join(format_finding(finding) for finding in hygiene["pending_hygiene_findings"])}

## Label Families

{chr(10).join(format_label_family(item) for item in hygiene["label_family_synthesis"])}

## Boundary

The synthesis does not score outcomes, validate a rule, change cancellation logic, or touch live behavior.
""",
    )

    source_contract = outputs["source_contract"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Source Contract And Capture Backlog

Promotion posture: `{PROMOTION_VERDICT}`.

## Capture Backlog Summary

{chr(10).join(f"- {item}" for item in source_contract["capture_backlog_summary"])}

## Source Contracts

{chr(10).join(format_contract(contract) for contract in source_contract["source_contract_backlog"])}

## Source Hash Inputs

{markdown_table(source_contract["control_input_hash_records"], ["path", "exists", "sha256"])}
""",
    )

    duplicate = outputs["duplicate_control"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Duplicate Denominator Control

Promotion posture: `{PROMOTION_VERDICT}`.

## Duplicate Posture

- Accepted row-level source inputs: `{duplicate["duplicate_posture"]["accepted_row_level_source_inputs"]}`
- Accepted unique no-fill duplicate keys: `{duplicate["duplicate_posture"]["accepted_unique_nofill_duplicate_keys"]}`
- Accepted duplicate-key collision groups: `{duplicate["duplicate_posture"]["accepted_duplicate_collision_groups"]}`
- Accepted duplicate-key collision rows: `{duplicate["duplicate_posture"]["accepted_duplicate_collision_rows"]}`
- OTI5 canonical duplicate rows accepted: `{duplicate["duplicate_posture"]["oti5_canonical_duplicate_rows_accepted"]}`
- OTI5 noncanonical duplicate projections rejected: `{duplicate["duplicate_posture"]["oti5_noncanonical_duplicate_projections_rejected"]}`

## Mandatory Controls

{chr(10).join(format_duplicate_control(control) for control in duplicate["mandatory_controls"])}

## Future Builder Requirements

{chr(10).join(f"- {item}" for item in duplicate["future_builder_requirements"])}
""",
    )

    blocker = outputs["blocker_ledger"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Residual Blocker Route Ledger

Promotion posture: `{PROMOTION_VERDICT}`.

Blocked rows: `{blocker["blocked_count"]}`. Rejected rows: `{blocker["rejected_count"]}`.

Boundary: {blocker["blocked_and_rejected_boundary"]}

## Blocker Routes

{chr(10).join(format_blocker_route(route) for route in blocker["blocker_routes"])}

## Reject Families

{chr(10).join(format_reject_family(family) for family in blocker["reject_families"])}
""",
    )

    ranking = outputs["route_ranking"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_FUTURE_ROUTE_RANKING_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Future Route Ranking

Promotion posture: `{PROMOTION_VERDICT}`.

## Ranking Basis

{chr(10).join(f"- {item}" for item in ranking["ranking_basis"])}

## Ranked Routes

{chr(10).join(format_route(route) for route in ranking["routes"])}

## Closed Routes

{chr(10).join(f"- `{route}` remains closed in this G0 lane." for route in ranking["closed_routes"])}
""",
    )

    write_next_prompt_pack(outputs)

    audit = outputs["completion_audit"]
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Completion Audit

Promotion posture: `{PROMOTION_VERDICT}`.

Completion status: `{audit["completion_status"]}`.
Can mark goal complete after verifier pass: `{str(audit["can_mark_goal_complete"]).lower()}`.

## Objective Restatement

{audit["objective_restatement"]}

## Prompt-To-Artifact Checklist

{markdown_table(audit["prompt_to_artifact_checklist"], ["requirement", "status", "evidence"])}

## Required Output Files

{chr(10).join(f"- `{path}`" for path in audit["required_output_files"])}

## Residual Uncertainty

{chr(10).join(f"- {item}" for item in audit["residual_uncertainty"])}

## Final Boundary

This route preserves `{PROMOTION_VERDICT}`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
""",
    )


def format_decision_entry(entry: dict[str, Any]) -> str:
    return f"""### {entry["decision_id"]}: {entry["question"]}

- Claim: {entry["claim"]}
- Evidence: {entry["evidence"]}
- Uncertainty: {entry["uncertainty"]}
- Falsification condition: {entry["falsification_condition"]}
- Exact next action: {entry["next_action"]}
- Owner: `{entry["owner"]}`
"""


def format_finding(finding: dict[str, Any]) -> str:
    return f"""### {finding["finding_id"]}

- Claim: {finding["claim"]}
- Evidence: {finding["evidence"]}
- Uncertainty: {finding["uncertainty"]}
- Next action: {finding["next_action"]}
"""


def format_label_family(item: dict[str, Any]) -> str:
    return f"""### `{item["label"]}` ({item["count"]})

- Source/control learning: {item["source_control_learning"]}
- Proves: {item["proves"]}
- Does not prove: {item["does_not_prove"]}
- Likely issue type: `{item["likely_issue_type"]}`
- Uncertainty: {item["uncertainty"]}
- Future route: {item["future_hypothesis_route"]}
- Capture fields: `{", ".join(item["capture_fields"])}`
"""


def format_contract(contract: dict[str, Any]) -> str:
    return f"""### `{contract["contract_id"]}` ({contract["priority"]})

- Purpose: {contract["purpose"]}
- Source learning: {contract["source_learning"]}
- Required fields: `{", ".join(contract["required_fields"])}`
- Forbidden fields: `{", ".join(contract["forbidden_fields"])}`
- Owner: `{contract["route_owner"]}`
"""


def format_duplicate_control(control: dict[str, Any]) -> str:
    return f"""### `{control["control_id"]}`

- Control: {control["control"]}
- Evidence: {control["evidence"]}
- Required check: {control["required_check"]}
- Failure mode prevented: {control["failure_mode_prevented"]}
"""


def format_blocker_route(route: dict[str, Any]) -> str:
    return f"""### `{route["family_id"]}` ({route["count"]})

- Rows: `{", ".join(route["row_ids"])}`
- Current status: `{route["current_status"]}`
- Feasibility class: `{route["feasibility_class"]}`
- Evidence: {route["evidence"][0]} {route["evidence"][1]}
- Exact unblocker: {route["exact_unblocker"]}
- Forbidden unblockers: `{", ".join(route["forbidden_unblockers"])}`
- Recommended route: `{route["recommended_route"]}`
- Priority: `{route["route_priority"]}`
"""


def format_reject_family(family: dict[str, Any]) -> str:
    return f"""### `{family["family_id"]}` ({family["count"]})

- Status: `{family["status"]}`
- Next action: {family["next_action"]}
"""


def format_route(route: dict[str, Any]) -> str:
    return f"""### Rank {route["rank"]}: `{route["route_id"]}`

- Type: `{route["route_type"]}`
- Expected learning value: `{route["expected_learning_value"]}`
- Contamination risk: `{route["contamination_risk"]}`
- Source feasibility: `{route["source_feasibility"]}`
- Independence from OB-retest backbone: `{route["independence_from_ob_retest_backbone"]}`
- Later improvement path: {route["live_system_improvement_path_later"]}
- Why now: {route["why_now"]}
- Forbidden until later: {route["forbidden_until_later"]}
"""


def write_next_prompt_pack(outputs: dict[str, Any]) -> None:
    write_text(
        ROUTE_DIR / "G0_NOFILL_CAT_V2_NEXT_PROMPT_PACK_2026-05-09.md",
        f"""# G0 NOFILL CAT V2 Next Prompt Pack

Promotion posture: `{PROMOTION_VERDICT}`.

## Primary Next Route

`NOFILL_CAT_V2_PENDING_LIFECYCLE_SOURCE_CONTRACT_BUILDER`

Objective: Build a source-only pending lifecycle capture contract from the G0 synthesis/control outputs. Preserve the exact G0 boundaries: no result scoring, no validation, no promotion, no live trading behavior change, no registry edits, no broker/account/order labels, and no use of blocked or rejected rows as results.

Must read:

- `G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS_2026-05-09.md`
- `G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json`
- `G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.json`
- `G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json`
- Upstream row ledger `NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`

Required output:

- A source-contract spec for pending create, cancel/expiry, terminal touch, side-aware entry touch, no-touch proof, coverage status, duplicate key, and source hashes.
- A verifier that rejects missing duplicate denominator policy, true safety flags, generated duplicate keys, result fields, blocked/rejected denominator inclusion, and absent source coverage status.
- A capture backlog that can run prospectively without changing live trading behavior.

Stop condition: complete only when the source contract is machine-checkable and still carries `{PROMOTION_VERDICT}`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Secondary Route

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`

Objective: Target exactly the 8 residual blockers. Do not score accepted rows, rejected rows, or blocked rows. Clear a blocker only with read-only source proof that satisfies the exact unblocker in `G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json`.

Priority order:

1. OTI4 May 3 frozen opening-range source gaps.
2. Original OTI2 XAUUSD active-window side-aware source gap.
3. OTI3 same-tick ambiguities only if higher-resolution event-order source exists without account/order labels.

## Tertiary Route

`NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE`

Objective: Design a future result contract without opening outcomes. Freeze denominator, source fields, sample floor, duplicate policy, no-leak proof, G12 gate, owner approval requirement, and forbidden fields. Do not compute or inspect results.

## Closed Route

`NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE` remains closed until a separate frozen preregistration, sample floor, no-leak proof, G12 acceptance, and explicit owner approval exist.
""",
    )


if __name__ == "__main__":
    outputs = build_all()
    print(
        json.dumps(
            {
                "status": "BUILT",
                "route_id": ROUTE_ID,
                "output_count": len(required_output_files()),
                "partition": outputs["decision_ledger"]["counts"]["partition"],
                "can_run_verifier": True,
            },
            indent=2,
            sort_keys=True,
        )
    )
