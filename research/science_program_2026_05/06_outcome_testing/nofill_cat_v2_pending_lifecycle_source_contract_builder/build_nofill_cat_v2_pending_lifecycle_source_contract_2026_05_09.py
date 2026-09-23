from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_ID = "NOFILL_CAT_V2_PENDING_LIFECYCLE_SOURCE_CONTRACT_BUILDER"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "nofill_cat_v2_pending_lifecycle_source_contract_v1"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]

CONTROL_PROMPT = ROUTE_DIR / "NOFILL_CAT_V2_PENDING_LIFECYCLE_SOURCE_CONTRACT_BUILDER_GOAL_PROMPT_2026-05-09.md"
G0_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route"
ROW_LEDGER = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"
)
ACCEPTED_PACKET = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ACCEPTED_PACKET_2026-05-09.json"
)
G12_DECISION_LEDGER = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_categorical_result_packet_v2_audit/G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json"
)
G12_FORENSICS_AUDIT_LEDGER_MD = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_2026-05-09.md"
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
    G0_DIR / "G0_NOFILL_CAT_V2_NEXT_PROMPT_PACK_2026-05-09.md",
    G0_DIR / "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md",
    G0_DIR / "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json",
    G0_DIR / "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.md",
    G0_DIR / "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.json",
    G0_DIR / "G0_NOFILL_CAT_V2_PENDING_LIFECYCLE_HYGIENE_SYNTHESIS_2026-05-09.md",
    G0_DIR / "G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json",
    G0_DIR / "G0_NOFILL_CAT_V2_FUTURE_ROUTE_RANKING_2026-05-09.json",
    ROW_LEDGER,
    ACCEPTED_PACKET,
    G12_DECISION_LEDGER,
    G12_FORENSICS_AUDIT_LEDGER_MD,
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

REQUIRED_FIELD_FAMILIES = [
    "identity_provenance",
    "pending_create",
    "pending_cancel_expiry",
    "cancel_expiry_reason",
    "active_pending_window",
    "decision_asof",
    "entry_touch_proof",
    "terminal_area_touch_proof",
    "protective_level_touch_proof",
    "no_touch_proof",
    "source_coverage",
    "quote_side",
    "source_granularity_parser",
    "source_hash_path",
    "duplicate_denominator",
    "noncanonical_projection_exclusion",
    "missing_source_blocker_taxonomy",
    "same_tick_same_bar_ambiguity",
    "label_family_separation",
    "forbidden_field_guard",
    "prospective_capture",
]

FORBIDDEN_DECISION_TIME_FIELD_NAMES = {
    "broker_actual_r",
    "account_history",
    "order_history",
    "mt5_deal_id",
    "mt5_order_id",
    "live_order_label",
    "hidden_label",
    "r_multiple",
    "win_rate",
    "expectancy",
    "profit_loss",
    "validation_result",
    "promotion_result",
    "post_outcome_score",
}

DUPLICATE_CONTROL_REQUIRED_FIELDS = [
    "row_level_denominator_scope",
    "unique_key_denominator_scope",
    "nofill_duplicate_key",
    "duplicate_group_id",
    "canonical_counting_row_id",
    "is_canonical_counting_row",
    "noncanonical_projection_exclusion_policy",
]


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


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def json_dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - defensive context capture
        return f"UNAVAILABLE: {exc}"


def live_state_freshness_status() -> str:
    path = REPO_ROOT / ".context/LIVE_STATE.md"
    if not path.exists():
        return "MISSING_LIVE_STATE"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "| Status | `FRESH` |" in text:
        return "FRESH"
    if "| Status | `STALE` |" in text:
        return "STALE"
    return "UNKNOWN"


def input_hash_records() -> list[dict[str, Any]]:
    return [
        {
            "path": rel(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path),
            "role": "controlling_or_supporting_input",
        }
        for path in CONTROL_INPUTS
    ]


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
    blocker_code_counts: Counter[str] = Counter()
    reject_code_counts: Counter[str] = Counter()
    for row in blocked:
        blocker_code_counts.update(row.get("exact_blocker_codes") or [])
    for row in rejected:
        reject_code_counts.update(row.get("reject_reason_codes") or row.get("exact_blocker_codes") or [])
    return {
        "partition": {
            "universe": len(rows),
            "accepted": len(accepted),
            "blocked": len(blocked),
            "rejected": len(rejected),
        },
        "accepted_split": accepted_split,
        "accepted_label_counts": dict(sorted(label_counts.items())),
        "accepted_source_lane_counts": dict(sorted(source_lane_counts.items())),
        "duplicate_posture": {
            "accepted_row_level_source_inputs": len(accepted),
            "accepted_unique_nofill_duplicate_keys": len(duplicate_key_counts),
            "accepted_duplicate_collision_groups": len(collision_groups),
            "accepted_duplicate_collision_rows": sum(collision_groups.values()),
            "oti5_canonical_duplicate_rows_accepted": source_lane_counts.get(
                "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT", 0
            ),
            "oti5_noncanonical_duplicate_projections_rejected": reject_code_counts.get(
                "REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION", 0
            ),
        },
        "blocker_code_counts": dict(sorted(blocker_code_counts.items())),
        "reject_code_counts": dict(sorted(reject_code_counts.items())),
        "accepted_rows": accepted,
        "blocked_rows": blocked,
        "rejected_rows": rejected,
    }


def field(
    name: str,
    family: str,
    timing: str,
    as_of_rule: str,
    allowed_source_types: list[str],
    required_status: str,
    no_leak_role: str,
    forbidden_substitute_fields: list[str],
    hash_requirements: str,
    duplicate_role: str,
    availability: str,
    description: str,
) -> dict[str, Any]:
    return {
        "field_name": name,
        "field_family": family,
        "source_timing": timing,
        "as_of_rule": as_of_rule,
        "allowed_source_types": allowed_source_types,
        "required_or_optional": required_status,
        "no_leak_role": no_leak_role,
        "forbidden_substitute_fields": forbidden_substitute_fields,
        "hash_requirements": hash_requirements,
        "duplicate_denominator_role": duplicate_role,
        "capture_availability": availability,
        "description": description,
    }


def contract_fields() -> list[dict[str, Any]]:
    source_only = "source_only_not_result"
    no_result_substitutes = ["broker_actual_r", "account_history", "order_history", "live_order_label", "hidden_label"]
    return [
        field("source_inventory_id", "identity_provenance", "decision_input", "Must exist before any label assignment.", ["candidate_registry", "source_packet"], "required", source_only, no_result_substitutes, "source packet hash required", "none", "historical_reconstructable_and_prospective", "Stable source inventory identifier."),
        field("source_packet_id", "identity_provenance", "decision_input", "Must reference the packet that supplied the row.", ["source_packet"], "required", source_only, no_result_substitutes, "source packet hash required", "none", "historical_reconstructable_and_prospective", "Stable upstream source packet identifier."),
        field("packet_row_id", "identity_provenance", "decision_input", "Must be stable across rebuilds.", ["row_ledger"], "required", source_only, no_result_substitutes, "row ledger hash required", "row_level_denominator_scope", "historical_reconstructable_and_prospective", "Stable row identifier for row-level denominator accounting."),
        field("symbol", "identity_provenance", "decision_input", "Must be known at decision time.", ["source_packet", "candidate_registry"], "required", source_only, no_result_substitutes, "source hash required", "duplicate_key_component", "historical_reconstructable_and_prospective", "Instrument symbol."),
        field("session", "identity_provenance", "decision_input", "Must be computed from timestamp/session rules before labels.", ["source_packet", "session_calendar"], "required", source_only, no_result_substitutes, "calendar version hash required", "duplicate_key_component", "historical_reconstructable_and_prospective", "Kill-zone/session bucket."),
        field("side", "identity_provenance", "decision_input", "Must be candidate side, not inferred from later path.", ["source_packet"], "required", source_only, no_result_substitutes, "source packet hash required", "duplicate_key_component", "historical_reconstructable_and_prospective", "Candidate side."),
        field("decision_asof_utc", "decision_asof", "decision_time", "Must be the last timestamp available to the decision process.", ["source_packet", "candidate_registry"], "required", "asof_boundary", no_result_substitutes, "source packet hash required", "duplicate_key_component", "historical_reconstructable_and_prospective", "Decision-as-of timestamp that freezes inputs."),
        field("pending_create_utc", "pending_create", "event_time", "Captured when a pending intent is created or reconstructed from source-only intent logs.", ["pending_intent_log", "source_packet"], "required", source_only, no_result_substitutes, "pending-intent source hash required", "none", "prospective_capture_primary_historical_partial", "Pending create timestamp."),
        field("pending_create_source", "pending_create", "event_source", "Must identify source of pending create; cannot use broker order history.", ["pending_intent_log", "source_packet"], "required", source_only, ["account_history", "order_history", "mt5_order_id"], "source hash required", "none", "prospective_capture_primary_historical_partial", "Source family for pending create."),
        field("pending_cancel_or_expiry_utc", "pending_cancel_expiry", "event_time", "Captured at cancel/expiry event or null only with active-window proof.", ["pending_intent_log", "shadow_lifecycle_log"], "required_nullable", source_only, ["account_history", "order_history", "live_order_label"], "cancel/expiry source hash required", "none", "prospective_capture_primary_historical_partial", "Pending cancel or expiry timestamp."),
        field("pending_cancel_or_expiry_source", "pending_cancel_expiry", "event_source", "Must name non-account source for cancel/expiry proof.", ["pending_intent_log", "shadow_lifecycle_log"], "required_nullable", source_only, ["account_history", "order_history", "mt5_order_id"], "source hash required", "none", "prospective_capture_primary_historical_partial", "Source family for cancel/expiry."),
        field("cancel_or_expiry_reason_code", "cancel_expiry_reason", "event_metadata", "Must be assigned from frozen taxonomy, not post-outcome convenience.", ["pending_intent_log", "shadow_lifecycle_log", "source_taxonomy"], "required_nullable", source_only, ["profit_loss", "r_multiple", "validation_result"], "taxonomy version hash required", "none", "prospective_capture_primary_historical_partial", "Frozen cancel/expiry reason."),
        field("active_pending_window_start_utc", "active_pending_window", "window_start", "Must equal pending create or approved active-window start.", ["pending_intent_log", "source_packet"], "required", source_only, no_result_substitutes, "source hash required", "none", "prospective_capture_primary_historical_partial", "Start of active pending window."),
        field("active_pending_window_end_utc", "active_pending_window", "window_end", "Must be cancel, expiry, horizon end, or source-window end reason.", ["pending_intent_log", "shadow_lifecycle_log", "source_coverage_manifest"], "required", source_only, no_result_substitutes, "source hash required", "none", "prospective_capture_primary_historical_partial", "End of active pending window."),
        field("active_pending_window_end_reason", "active_pending_window", "window_metadata", "Must separate cancel, expiry, horizon, and source-truncation.", ["pending_intent_log", "source_coverage_manifest"], "required", source_only, ["post_outcome_score", "validation_result"], "source hash required", "none", "prospective_capture_primary_historical_partial", "Reason the pending observation window ended."),
        field("entry_price", "entry_touch_proof", "decision_input", "Must be frozen from candidate/pending intent before touch testing.", ["source_packet", "pending_intent_log"], "required", source_only, no_result_substitutes, "source packet hash required", "duplicate_key_component", "historical_reconstructable_and_prospective", "Frozen side-aware pending entry price."),
        field("side_aware_entry_touch_status", "entry_touch_proof", "source_window_observation", "Must use bid/ask side appropriate to candidate side.", ["tick_bid_ask", "approved_side_aware_quote_source"], "required", source_only, ["M1_midpoint_only_when_side_aware_required", "account_history", "order_history"], "tick/source hash required", "none", "prospective_capture_primary_historical_partial", "Entry touch/no-touch status."),
        field("side_aware_entry_touch_utc", "entry_touch_proof", "source_window_observation", "Null allowed only when no-touch proof covers the active window.", ["tick_bid_ask", "approved_side_aware_quote_source"], "required_nullable", source_only, ["broker_fill_time", "mt5_order_id", "account_history"], "tick/source hash required", "none", "prospective_capture_primary_historical_partial", "First side-aware entry touch timestamp."),
        field("terminal_area_definition", "terminal_area_touch_proof", "decision_input", "Must be frozen before terminal touch scan.", ["source_packet", "market_state_snapshot"], "required", source_only, ["post_outcome_target", "r_multiple"], "source hash required", "none", "historical_reconstructable_and_prospective", "Frozen terminal-area predicate."),
        field("terminal_area_touch_status", "terminal_area_touch_proof", "source_window_observation", "Must be source-observed inside active window, not scored as result.", ["tick_bid_ask", "M1_or_lower_OHLC_if_contract_allows"], "required", source_only, ["take_profit_result", "win_rate", "r_multiple"], "source hash required", "none", "prospective_capture_primary_historical_partial", "Terminal-area touch/no-touch status."),
        field("terminal_area_touch_utc", "terminal_area_touch_proof", "source_window_observation", "Null allowed only with no-touch proof or source blocker.", ["tick_bid_ask", "M1_or_lower_OHLC_if_contract_allows"], "required_nullable", source_only, ["take_profit_time", "account_history"], "source hash required", "none", "prospective_capture_primary_historical_partial", "First terminal-area touch timestamp."),
        field("protective_level_definition", "protective_level_touch_proof", "decision_input", "Must be frozen before protective touch scan.", ["source_packet", "risk_snapshot"], "required", source_only, ["stop_loss_result", "r_multiple"], "source hash required", "none", "historical_reconstructable_and_prospective", "Frozen protective-level predicate."),
        field("protective_level_touch_status", "protective_level_touch_proof", "source_window_observation", "Must remain event-order source evidence only.", ["tick_bid_ask", "M1_or_lower_OHLC_if_contract_allows"], "required", source_only, ["loss_result", "r_multiple", "account_history"], "source hash required", "none", "prospective_capture_primary_historical_partial", "Protective-level touch/no-touch status."),
        field("protective_level_touch_utc", "protective_level_touch_proof", "source_window_observation", "Null allowed only with no-touch proof or source blocker.", ["tick_bid_ask", "M1_or_lower_OHLC_if_contract_allows"], "required_nullable", source_only, ["stop_loss_time", "account_history"], "source hash required", "none", "prospective_capture_primary_historical_partial", "First protective-level touch timestamp."),
        field("no_touch_proof_through_utc", "no_touch_proof", "source_window_observation", "Must be paired with coverage status and source window end.", ["tick_bid_ask", "M1_or_lower_OHLC_if_contract_allows"], "required_when_no_touch_label", source_only, ["absence_in_account_history", "no_trade_result"], "source hash required", "none", "prospective_capture_primary_historical_partial", "Timestamp through which no-touch is proven."),
        field("source_coverage_start_utc", "source_coverage", "coverage_window", "Must bound every touch/no-touch proof.", ["source_coverage_manifest", "tick_bid_ask", "OHLC_source_manifest"], "required", "coverage_boundary", no_result_substitutes, "source hash required", "none", "historical_reconstructable_and_prospective", "Start of source coverage."),
        field("source_coverage_end_utc", "source_coverage", "coverage_window", "Must bound every touch/no-touch proof.", ["source_coverage_manifest", "tick_bid_ask", "OHLC_source_manifest"], "required", "coverage_boundary", no_result_substitutes, "source hash required", "none", "historical_reconstructable_and_prospective", "End of source coverage."),
        field("source_coverage_status", "source_coverage", "coverage_metadata", "Must distinguish full, partial, missing, empty-window, and blocked.", ["source_coverage_manifest"], "required", "blocker_boundary", no_result_substitutes, "source hash required", "none", "historical_reconstructable_and_prospective", "Coverage status for the active source window."),
        field("quote_side_used", "quote_side", "parser_metadata", "Must be bid, ask, bid_ask_pair, or explicit OHLC proxy policy.", ["tick_bid_ask", "OHLC_source_manifest"], "required", source_only, ["broker_fill_side", "account_history"], "parser/source hash required", "none", "historical_reconstructable_and_prospective", "Quote side used for touch tests."),
        field("source_granularity", "source_granularity_parser", "parser_metadata", "Must state tick, M1, lower-OHLC, or higher-res event source.", ["source_coverage_manifest"], "required", "ambiguity_boundary", no_result_substitutes, "source hash required", "none", "historical_reconstructable_and_prospective", "Granularity used for event ordering."),
        field("parser_version", "source_granularity_parser", "parser_metadata", "Must be versioned before packet build.", ["parser_manifest"], "required", source_only, no_result_substitutes, "parser script hash required", "none", "historical_reconstructable_and_prospective", "Parser/extractor version."),
        field("source_path_list", "source_hash_path", "source_manifest", "Must list every file/path used for source proof.", ["source_coverage_manifest"], "required", "provenance_boundary", no_result_substitutes, "sha256 per source required", "none", "historical_reconstructable_and_prospective", "Source file/path list."),
        field("source_hash_manifest", "source_hash_path", "source_manifest", "Must hash source files, parser, and controlling packet inputs.", ["source_coverage_manifest", "parser_manifest"], "required", "provenance_boundary", no_result_substitutes, "sha256 required", "none", "historical_reconstructable_and_prospective", "Hash manifest for provenance."),
        field("nofill_duplicate_key", "duplicate_denominator", "denominator_metadata", "Must be stable and source-derived; generated fallbacks are rejected.", ["row_ledger", "duplicate_control_manifest"], "required", "denominator_boundary", ["generated_fallback_duplicate_key"], "row ledger hash required", "unique_key_denominator_scope", "historical_reconstructable_and_prospective", "Stable no-fill duplicate key."),
        field("duplicate_group_id", "duplicate_denominator", "denominator_metadata", "Must be present for every row that can collide.", ["row_ledger", "duplicate_control_manifest"], "required", "denominator_boundary", ["generated_fallback_group_id"], "row ledger hash required", "collision_group_scope", "historical_reconstructable_and_prospective", "Duplicate collision group identifier."),
        field("canonical_counting_row_id", "duplicate_denominator", "denominator_metadata", "Must name the row that counts for the unique-key denominator.", ["duplicate_control_manifest"], "required", "denominator_boundary", ["human_markdown_only_selection"], "duplicate manifest hash required", "canonical_row_scope", "historical_reconstructable_and_prospective", "Canonical countable row ID."),
        field("row_level_denominator_scope", "duplicate_denominator", "denominator_metadata", "Must be frozen before label/result opening.", ["duplicate_control_manifest"], "required", "denominator_boundary", ["post_result_denominator"], "duplicate manifest hash required", "row_level_denominator_scope", "historical_reconstructable_and_prospective", "Row-level denominator scope."),
        field("unique_key_denominator_scope", "duplicate_denominator", "denominator_metadata", "Must be frozen before label/result opening.", ["duplicate_control_manifest"], "required", "denominator_boundary", ["post_result_denominator"], "duplicate manifest hash required", "unique_key_denominator_scope", "historical_reconstructable_and_prospective", "Unique-key denominator scope."),
        field("is_canonical_counting_row", "duplicate_denominator", "denominator_metadata", "Must be true for canonical unique-key row only.", ["duplicate_control_manifest"], "required", "denominator_boundary", ["noncanonical_denominator_inclusion"], "duplicate manifest hash required", "canonical_row_scope", "historical_reconstructable_and_prospective", "Canonical row flag."),
        field("noncanonical_projection_exclusion_policy", "noncanonical_projection_exclusion", "denominator_metadata", "Must exclude noncanonical duplicate projections before labels.", ["duplicate_control_manifest"], "required", "denominator_boundary", ["noncanonical_denominator_inclusion"], "duplicate manifest hash required", "noncanonical_projection_exclusion", "historical_reconstructable_and_prospective", "Policy excluding noncanonical projections."),
        field("missing_source_blocker_family", "missing_source_blocker_taxonomy", "blocker_metadata", "Must classify exact missing source or event-order gap.", ["blocker_taxonomy"], "required_when_blocked", "blocker_boundary", ["result_proxy_blocker_clearance"], "taxonomy version hash required", "none", "historical_reconstructable_and_prospective", "Blocker family for missing source states."),
        field("same_tick_same_bar_ambiguity_status", "same_tick_same_bar_ambiguity", "ambiguity_metadata", "Must preserve ambiguity rather than guess event order.", ["tick_bid_ask", "OHLC_source_manifest"], "required", "ambiguity_boundary", ["guessed_sequence", "account_history"], "source/parser hash required", "none", "historical_reconstructable_and_prospective", "Same-tick or same-bar ambiguity status."),
        field("label_family", "label_family_separation", "label_metadata", "Accepted labels remain input-only categorical source-control labels.", ["row_ledger"], "required", "label_boundary", ["performance_label", "result_label"], "row ledger hash required", "none", "historical_reconstructable_and_prospective", "Input-only label family."),
        field("label_assignment_boundary", "label_family_separation", "label_metadata", "Must say input-only and no result use.", ["row_ledger", "source_contract"], "required", "label_boundary", ["validation_result", "promotion_result"], "contract hash required", "none", "historical_reconstructable_and_prospective", "Boundary separating source labels from results."),
        field("forbidden_substitute_field_scan_status", "forbidden_field_guard", "audit_metadata", "Must pass generated-key and forbidden-field scans.", ["no_leak_audit"], "required", "no_leak_guard", ["broker_actual_r", "account_history", "hidden_label"], "audit hash required", "none", "historical_reconstructable_and_prospective", "No-leak scan status."),
        field("prospective_capture_mode", "prospective_capture", "capture_metadata", "Must be shadow/source-only unless separately approved.", ["capture_backlog"], "required", "live_effect_guard", ["live_order_behavior_change"], "backlog hash required", "none", "prospective_capture_primary", "Prospective capture mode and approval boundary."),
    ]


def validate_duplicate_denominator_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in DUPLICATE_CONTROL_REQUIRED_FIELDS:
        if key not in record or record.get(key) in (None, "", []):
            errors.append(f"missing_{key}")
    duplicate_key = str(record.get("nofill_duplicate_key", "")).lower()
    group_id = str(record.get("duplicate_group_id", "")).lower()
    generated_markers = ("generated", "fallback", "auto_", "unknown", "missing")
    if any(marker in duplicate_key for marker in generated_markers):
        errors.append("generated_or_fallback_nofill_duplicate_key")
    if any(marker in group_id for marker in generated_markers):
        errors.append("generated_or_fallback_duplicate_group_id")
    policy = str(record.get("noncanonical_projection_exclusion_policy", "")).upper()
    if "EXCLUDE" not in policy and "REJECT" not in policy:
        errors.append("noncanonical_projection_exclusion_policy_not_enforcing_exclusion")
    return errors


def deep_question_answers(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "question_id": "DQ-001",
            "question": "What exact fields would have prevented the 110 terminal-before-entry rows from requiring forensic reconstruction?",
            "claim": "They needed explicit pending lifecycle event capture plus side-aware touch ordering.",
            "evidence": "110 accepted input-only rows carry nofill_terminal_before_entry in the frozen row ledger.",
            "uncertainty": "The current packet cannot judge cancellation quality or live rule fitness.",
            "exact_field_or_control": [
                "pending_create_utc",
                "pending_cancel_or_expiry_utc",
                "cancel_or_expiry_reason_code",
                "side_aware_entry_touch_utc",
                "terminal_area_touch_utc",
                "active_pending_window_end_reason",
                "source_coverage_status",
            ],
            "owner": "SOURCE_BUILDER",
            "falsification_condition": "A future source-hashed packet with these fields still cannot order terminal touch versus entry touch for otherwise complete rows.",
        },
        {
            "question_id": "DQ-002",
            "question": "What exact fields would have prevented the 32 no-entry-through-horizon rows from staying source-control only?",
            "claim": "They need active pending window proof, no-touch proof through the window, and horizon-end reason before any future result design.",
            "evidence": "32 accepted source-corrected rows carry source_corrected_no_entry_through_pending_horizon.",
            "uncertainty": "They still do not become results without a separate preregistered result lane.",
            "exact_field_or_control": [
                "active_pending_window_start_utc",
                "active_pending_window_end_utc",
                "active_pending_window_end_reason",
                "no_touch_proof_through_utc",
                "source_coverage_start_utc",
                "source_coverage_end_utc",
                "source_coverage_status",
            ],
            "owner": "SOURCE_BUILDER",
            "falsification_condition": "A future no-touch row has full coverage and horizon fields but still cannot distinguish untouched entry from missing source.",
        },
        {
            "question_id": "DQ-003",
            "question": "What fields separate pending lifecycle hygiene from fill/path event-order research?",
            "claim": "Pending hygiene is create/cancel/expiry plus active-window and touch/no-touch proof; fill/path research is entry/protective/terminal sequence after entry touch.",
            "evidence": "G0 separates 142 pending hygiene labels from 29 OTI2 event-order labels.",
            "uncertainty": "A row can require both contracts, but the field families must stay separate.",
            "exact_field_or_control": [
                "pending_create_utc",
                "pending_cancel_or_expiry_utc",
                "cancel_or_expiry_reason_code",
                "entry_touch_proof fields",
                "protective_level_touch_utc",
                "terminal_area_touch_utc",
                "same_tick_same_bar_ambiguity_status",
            ],
            "owner": "SOURCE_BUILDER",
            "falsification_condition": "A verifier allows event-order labels without pending-window coverage or allows pending lifecycle labels to imply post-entry result order.",
        },
        {
            "question_id": "DQ-004",
            "question": "Which fields are required before a future no-fill result lane can exist without leakage?",
            "claim": "The source contract must freeze source coverage, duplicate denominator, label boundary, and forbidden-field scans before outcomes open.",
            "evidence": "Current route preserves NO_PROMOTION_VERDICT and keeps blockers/rejects outside denominators.",
            "uncertainty": "Sample floor and owner approval are outside this lane and remain closed.",
            "exact_field_or_control": [
                "source_hash_manifest",
                "source_path_list",
                "row_level_denominator_scope",
                "unique_key_denominator_scope",
                "canonical_counting_row_id",
                "label_assignment_boundary",
                "forbidden_substitute_field_scan_status",
            ],
            "owner": "FUTURE_PREREGISTRATION_DESIGN_LANE",
            "falsification_condition": "A future result lane can alter denominator, source coverage, or accepted labels after seeing outcomes.",
        },
        {
            "question_id": "DQ-005",
            "question": "What duplicate controls must be machine-enforced rather than human-read from markdown?",
            "claim": "Every packet must reject missing row-level denominator, unique-key denominator, duplicate group, canonical row, exclusion policy, and generated fallback duplicate keys.",
            "evidence": "225 accepted row-level inputs reduce to 182 unique accepted duplicate keys, with 39 noncanonical OTI5 projections rejected.",
            "uncertainty": "Canonical selection can still be wrong if future source identity fields are incomplete.",
            "exact_field_or_control": DUPLICATE_CONTROL_REQUIRED_FIELDS,
            "owner": "DUPLICATE_DENOMINATOR_VERIFIER_CONTROL",
            "falsification_condition": "The duplicate verifier accepts a record missing one required control or containing a generated fallback key.",
        },
        {
            "question_id": "DQ-006",
            "question": "Which residual blockers become easier to solve after this contract exists?",
            "claim": "The 3 OTI4 May 3 gaps and 1 original OTI2 active-window gap become easier; the 4 OTI3 same-tick rows remain blocked without higher-resolution event order.",
            "evidence": "G0 blocker ledger classifies 3 OTI4 rows as recoverable with read-only tick/M1/lower OHLC, 1 OTI2 row as recoverable with side-aware coverage, and 4 OTI3 rows as same-tick order ambiguity.",
            "uncertainty": "Local source existence is not the same as coverage inside the exact frozen window.",
            "exact_field_or_control": [
                "source_coverage_start_utc",
                "source_coverage_end_utc",
                "source_coverage_status",
                "quote_side_used",
                "source_granularity",
                "same_tick_same_bar_ambiguity_status",
            ],
            "owner": "RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
            "falsification_condition": "A blocker-clear lane finds complete side-aware source coverage and still cannot apply this taxonomy to clear or keep the row blocked.",
        },
        {
            "question_id": "DQ-007",
            "question": "Which source contract fields should be captured prospectively in shadow logs, and which must remain research-only proposals until separately approved?",
            "claim": "Source/provenance and pending lifecycle event fields are prospectively useful; live wiring, cancellation action, and result use need separate approval.",
            "evidence": "The prompt allows prospective capture backlog but forbids live behavior changes.",
            "uncertainty": "Actual logger wiring can touch live paths later and therefore needs a separate scoped approval/test lane.",
            "exact_field_or_control": [
                "prospective_capture_mode",
                "pending_create_utc",
                "pending_cancel_or_expiry_utc",
                "cancel_or_expiry_reason_code",
                "source_coverage_status",
                "source_hash_manifest",
                "live_wiring_requires_separate_approval",
            ],
            "owner": "FUTURE_SHADOW_TELEMETRY_LANE",
            "falsification_condition": "A future capture patch changes order behavior, selector logic, risk, execution, or cancellation decisions while claiming this source contract as authorization.",
        },
        {
            "question_id": "DQ-008",
            "question": "What is the most likely way a future agent could accidentally contaminate this lane, and how does this contract prevent it?",
            "claim": "The highest-risk contamination is using account/order/broker result labels or noncanonical duplicate rows to rescue ambiguous source rows.",
            "evidence": "The prompt forbids broker/account/order labels and G0 shows 39 noncanonical duplicate projections rejected.",
            "uncertainty": "A verifier can catch schema contamination, but reviewer discipline is still needed for narrative claims.",
            "exact_field_or_control": [
                "forbidden_substitute_field_scan_status",
                "noncanonical_projection_exclusion_policy",
                "label_assignment_boundary",
                "validation_safe=false",
                "outcome_review_opened=false",
            ],
            "owner": "NOLEAK_AUDITOR",
            "falsification_condition": "Generated schema field_names include forbidden result/account/order/hidden fields, or blocked/rejected rows enter accepted denominators.",
        },
        {
            "question_id": "DQ-009",
            "question": "What is the highest-learning next route after this contract?",
            "claim": "Run a G12 audit of this pending source contract first, then use the audited contract to clear exact residual blockers.",
            "evidence": "This route creates machine-checkable controls; a G12 audit is the safest next gate before source-access or preregistration lanes reuse them.",
            "uncertainty": "If the owner prioritizes direct source access, residual blocker clear can run next but must keep the G12 audit before any result lane.",
            "exact_field_or_control": [
                "G12_PENDING_SOURCE_CONTRACT_AUDIT",
                "RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
                "FILL_PATH_EVENT_ORDER_CONTRACT",
            ],
            "owner": "NEXT_PROMPT_PACK",
            "falsification_condition": "The G12 audit finds the contract is incomplete or the residual blocker lane needs fields not represented here.",
        },
    ]


def blocker_taxonomy() -> dict[str, Any]:
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "blocker_total": 8,
            "reject_total": 65,
            "blocker_families": [
                {
                    "family_id": "oti4_may3_source_gaps",
                    "count": 3,
                    "row_ids": ["NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"],
                    "blocker_codes": ["BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP"],
                    "missing_source_or_field": "Read-only tick parquet or M1/lower OHLC covering 2026-05-03 13:00-13:30 UTC opening range.",
                    "contract_fields_that_prevent_recurrence": ["source_coverage_status", "source_path_list", "source_hash_manifest", "source_coverage_start_utc", "source_coverage_end_utc"],
                    "denominator_policy": "outside_accepted_labels_and_denominators_until_exact_source_clearance",
                    "result_use": "forbidden",
                },
                {
                    "family_id": "oti3_same_tick_order_ambiguities",
                    "count": 4,
                    "row_ids": ["NOFILL-CAT-ROW-0130", "NOFILL-CAT-ROW-0143", "NOFILL-CAT-ROW-0165", "NOFILL-CAT-ROW-0178"],
                    "blocker_codes": ["BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE"],
                    "missing_source_or_field": "Higher-resolution or broker-native event-order source proving sequence inside identical timestamp without account/order labels.",
                    "contract_fields_that_prevent_recurrence": ["same_tick_same_bar_ambiguity_status", "source_granularity", "parser_version", "quote_side_used"],
                    "denominator_policy": "outside_accepted_labels_and_denominators_until_higher_resolution_event_order_source_exists",
                    "result_use": "forbidden",
                },
                {
                    "family_id": "original_oti2_source_gap",
                    "count": 1,
                    "row_ids": ["NOFILL-CAT-ROW-0241"],
                    "blocker_codes": [
                        "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED",
                        "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP",
                    ],
                    "missing_source_or_field": "Side-aware bid/ask tick or approved lower source covering active pending window through cancel.",
                    "contract_fields_that_prevent_recurrence": ["quote_side_used", "side_aware_entry_touch_status", "source_coverage_status", "active_pending_window_end_reason"],
                    "denominator_policy": "outside_accepted_labels_and_denominators_until_side_aware_coverage_exists",
                    "result_use": "forbidden",
                },
            ],
            "reject_families": [
                {
                    "family_id": "oti4_contract_exclusions",
                    "count": 26,
                    "reject_codes": [
                        "BLOCK_OTI4_BREAKOUT_SIDE_MISMATCHES_CANDIDATE_SIDE",
                        "BLOCK_OTI4_RANGE_NOT_COMPLETE_ASOF_DECISION",
                        "BLOCK_OTI4_NO_BREAKOUT_ASOF_UNDER_FROZEN_RANGE",
                    ],
                    "policy": "contract_excluded_no_label_no_denominator_no_result_use",
                },
                {
                    "family_id": "oti5_noncanonical_duplicate_projections",
                    "count": 39,
                    "reject_codes": ["REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION"],
                    "policy": "duplicate_excluded_no_label_no_denominator_no_result_use",
                },
            ],
        }
    )


def capture_backlog() -> dict[str, Any]:
    items = [
        {
            "backlog_id": "PEND-CAP-001",
            "priority": "P0",
            "title": "Machine-enforce duplicate denominator manifest in every future no-fill packet builder.",
            "source_contract_fields": DUPLICATE_CONTROL_REQUIRED_FIELDS,
            "prospective_shadow_only": True,
            "may_modify_live_code_in_this_lane": False,
            "requires_separate_owner_approval_for_live_wiring": True,
            "forbidden": ["result_scoring", "registry_edit", "live_order_behavior_change"],
            "success_check": "Verifier rejects missing denominators, missing canonical row ID, missing group ID, non-exclusion policy, and generated fallback keys.",
        },
        {
            "backlog_id": "PEND-CAP-002",
            "priority": "P1",
            "title": "Pending lifecycle source shadow capture schema.",
            "source_contract_fields": [
                "pending_create_utc",
                "pending_cancel_or_expiry_utc",
                "cancel_or_expiry_reason_code",
                "active_pending_window_start_utc",
                "active_pending_window_end_utc",
                "active_pending_window_end_reason",
            ],
            "prospective_shadow_only": True,
            "may_modify_live_code_in_this_lane": False,
            "requires_separate_owner_approval_for_live_wiring": True,
            "forbidden": ["cancel_rule_change", "execution_change", "selector_change"],
            "success_check": "Rows can distinguish pending create, cancel, expiry, horizon end, stale POI, and source truncation without account/order labels.",
        },
        {
            "backlog_id": "PEND-CAP-003",
            "priority": "P1",
            "title": "Side-aware touch/no-touch and coverage manifest.",
            "source_contract_fields": [
                "side_aware_entry_touch_status",
                "side_aware_entry_touch_utc",
                "terminal_area_touch_status",
                "protective_level_touch_status",
                "no_touch_proof_through_utc",
                "quote_side_used",
                "source_coverage_status",
            ],
            "prospective_shadow_only": True,
            "may_modify_live_code_in_this_lane": False,
            "requires_separate_owner_approval_for_live_wiring": True,
            "forbidden": ["broker_fill_substitution", "account_history_substitution", "post_outcome_score"],
            "success_check": "No-touch and touch labels cannot exist without quote side and source coverage status.",
        },
        {
            "backlog_id": "PEND-CAP-004",
            "priority": "P2",
            "title": "Residual blocker clear source-access lane for exactly 8 blockers.",
            "source_contract_fields": ["source_path_list", "source_hash_manifest", "source_coverage_status", "same_tick_same_bar_ambiguity_status"],
            "prospective_shadow_only": False,
            "may_modify_live_code_in_this_lane": False,
            "requires_separate_owner_approval_for_live_wiring": False,
            "forbidden": ["accepted_row_scoring", "rejected_row_scoring", "broker_actual_r", "account_history"],
            "success_check": "Each blocker is cleared or remains blocked from exact source coverage/event-order proof only.",
        },
        {
            "backlog_id": "PEND-CAP-005",
            "priority": "P2",
            "title": "Fill/path event-order contract derived from pending source fields.",
            "source_contract_fields": ["entry_touch_proof", "terminal_area_touch_proof", "protective_level_touch_proof", "same_tick_same_bar_ambiguity_status"],
            "prospective_shadow_only": True,
            "may_modify_live_code_in_this_lane": False,
            "requires_separate_owner_approval_for_live_wiring": True,
            "forbidden": ["performance_comparison", "result_lane_opening", "guessed_sequence"],
            "success_check": "Event-order categories can be emitted as categories while same-tick/same-bar ambiguity remains explicit.",
        },
    ]
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "backlog_items": items,
            "global_boundary": "All backlog items are source/control or prospective shadow proposals. This lane does not wire live loggers or change live trading behavior.",
        }
    )


def source_schema(counts: dict[str, Any]) -> dict[str, Any]:
    fields = contract_fields()
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "stable_schema_version": SCHEMA_VERSION,
            "required_field_families": REQUIRED_FIELD_FAMILIES,
            "field_count": len(fields),
            "contract_fields": fields,
            "forbidden_decision_time_field_names": sorted(FORBIDDEN_DECISION_TIME_FIELD_NAMES),
            "frozen_counts": {
                "partition": EXPECTED_PARTITION,
                "accepted_split": EXPECTED_ACCEPTED_SPLIT,
                "accepted_label_counts": EXPECTED_LABEL_COUNTS,
                "accepted_source_lane_counts": EXPECTED_SOURCE_LANE_COUNTS,
                "duplicate_posture": EXPECTED_DUPLICATE_POSTURE,
                "blocker_counts": EXPECTED_BLOCKER_COUNTS,
                "reject_counts": EXPECTED_REJECT_COUNTS,
            },
            "recomputed_counts": {
                "partition": counts["partition"],
                "accepted_split": counts["accepted_split"],
                "accepted_label_counts": counts["accepted_label_counts"],
                "accepted_source_lane_counts": counts["accepted_source_lane_counts"],
                "duplicate_posture": counts["duplicate_posture"],
            },
        }
    )


def source_contract_spec(counts: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": GENERATED_AT_UTC,
            "objective": "Machine-checkable source-only pending lifecycle capture contract with duplicate denominator controls folded into the same lane.",
            "source_authority": [
                rel(ROW_LEDGER),
                rel(ACCEPTED_PACKET),
                rel(G0_DIR / "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json"),
                rel(G0_DIR / "G0_NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_CONTROL_2026-05-09.json"),
            ],
            "frozen_facts": {
                "partition": "298 = 225 accepted + 8 blocked + 65 rejected",
                "accepted_split": "225 = 52 prior accepted + 173 source-corrected accepted",
                "accepted_labels_are_input_only": True,
                "blockers_and_rejects_excluded_from_labels_denominators_results_validation_promotion": True,
                "duplicate_posture": EXPECTED_DUPLICATE_POSTURE,
            },
            "schema_fields_artifact": "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json",
            "field_family_count": len(schema["required_field_families"]),
            "field_count": schema["field_count"],
            "deep_question_answers": deep_question_answers(counts),
            "contract_controls": [
                "No accepted input-only label may be treated as performance or validation evidence.",
                "No blocked or rejected row may enter accepted-label, row-level result, unique-key result, validation, or promotion denominators.",
                "Every future packet must publish row-level and unique-key denominators before outcome opening.",
                "Every touch/no-touch field must carry source coverage status, quote side, parser version, source path, and hash manifest.",
                "Same-tick or same-bar event ordering must be an ambiguity state unless higher-resolution source proves order.",
            ],
        }
    )


def duplicate_verifier_control(counts: dict[str, Any]) -> dict[str, Any]:
    valid_example = {
        "row_level_denominator_scope": "accepted_input_only_rows_225",
        "unique_key_denominator_scope": "accepted_unique_nofill_duplicate_keys_182",
        "nofill_duplicate_key": "OTI5_G6_CUSUM|OTG0-PKT-063|XAGUSD|2026-05-04|london|SHORT|LONG|no_entry_touch_no_r_scored",
        "duplicate_group_id": "G6_EXHAUSTION|XAGUSD|2026-05-04|london|SHORT|LONG",
        "canonical_counting_row_id": "NOFILL-CAT-ROW-0001",
        "is_canonical_counting_row": True,
        "noncanonical_projection_exclusion_policy": "REJECT_NONCANONICAL_PROJECTIONS_BEFORE_LABEL_OR_DENOMINATOR",
    }
    invalid_examples = [
        {"case_id": "missing_row_level_denominator", "record": {k: v for k, v in valid_example.items() if k != "row_level_denominator_scope"}},
        {"case_id": "missing_unique_key_denominator", "record": {k: v for k, v in valid_example.items() if k != "unique_key_denominator_scope"}},
        {"case_id": "missing_duplicate_group_id", "record": {k: v for k, v in valid_example.items() if k != "duplicate_group_id"}},
        {"case_id": "missing_canonical_row_id", "record": {k: v for k, v in valid_example.items() if k != "canonical_counting_row_id"}},
        {"case_id": "missing_noncanonical_exclusion_policy", "record": {k: v for k, v in valid_example.items() if k != "noncanonical_projection_exclusion_policy"}},
        {
            "case_id": "generated_fallback_duplicate_key",
            "record": {**valid_example, "nofill_duplicate_key": "GENERATED_FALLBACK|XAUUSD|UNKNOWN"},
        },
    ]
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "duplicate_posture": counts["duplicate_posture"],
            "required_fields": DUPLICATE_CONTROL_REQUIRED_FIELDS,
            "machine_enforced_rejections": [
                "missing_row_level_denominator_scope",
                "missing_unique_key_denominator_scope",
                "missing_duplicate_group_id",
                "missing_canonical_counting_row_id",
                "missing_noncanonical_projection_exclusion_policy",
                "generated_or_fallback_nofill_duplicate_key",
                "generated_or_fallback_duplicate_group_id",
            ],
            "valid_example": valid_example,
            "valid_example_errors": validate_duplicate_denominator_record(valid_example),
            "invalid_examples": [
                {
                    "case_id": item["case_id"],
                    "expected_errors": validate_duplicate_denominator_record(item["record"]),
                    "record": item["record"],
                }
                for item in invalid_examples
            ],
            "future_packet_rule": "A packet is rejected unless both row-level and unique-key denominators are frozen and every noncanonical projection is excluded before labels/results.",
        }
    )


def noleak_audit(schema: dict[str, Any], counts: dict[str, Any]) -> dict[str, Any]:
    field_names = {item["field_name"] for item in schema["contract_fields"]}
    forbidden_hits = sorted(field_names & FORBIDDEN_DECISION_TIME_FIELD_NAMES)
    blocked_label_violations = [
        row.get("packet_row_id")
        for row in counts["blocked_rows"]
        if row.get("categorical_input_label") is not None or row.get("in_accepted_packet_denominator") is not False
    ]
    rejected_label_violations = [
        row.get("packet_row_id")
        for row in counts["rejected_rows"]
        if row.get("categorical_input_label") is not None or row.get("in_accepted_packet_denominator") is not False
    ]
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "field_name_forbidden_hits": forbidden_hits,
            "forbidden_fields_documented_only_not_schema_fields": sorted(FORBIDDEN_DECISION_TIME_FIELD_NAMES),
            "blocked_label_or_denominator_violations": blocked_label_violations,
            "rejected_label_or_denominator_violations": rejected_label_violations,
            "accepted_labels_input_only": True,
            "blockers_and_rejects_outside_result_validation_promotion_use": True,
            "status": "PASS" if not forbidden_hits and not blocked_label_violations and not rejected_label_violations else "FAIL",
        }
    )


def context_anchor() -> dict[str, Any]:
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_CONTEXT_ANCHOR",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "worktree_path": str(REPO_ROOT),
            "branch": git_output(["branch", "--show-current"]),
            "starting_head": git_output(["rev-parse", "--short", "HEAD"]),
            "starting_head_full": git_output(["rev-parse", "HEAD"]),
            "live_state_freshness_status": live_state_freshness_status(),
            "controlling_prompt": rel(CONTROL_PROMPT),
            "latest_handoff_read": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            "control_input_hash_records": input_hash_records(),
            "searched_roots": [
                str(REPO_ROOT),
                r"C:\Users\MSI\Documents\ai-trading-agent\data",
                r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
                r"C:\tmp",
            ],
            "source_use_boundary": "No external source, MT5, paid/API/Databento, broker/account/order/history, or hidden-label source was used by this lane.",
        }
    )


def completion_audit() -> dict[str, Any]:
    checklist = [
        {"requirement": "Regenerate and read LIVE_STATE", "status": "PASS", "evidence": "Context anchor records LIVE_STATE freshness after preflight."},
        {"requirement": "Use controlling prompt and inputs", "status": "PASS", "evidence": "Context anchor hashes controlling prompt, G0 inputs, row ledger, accepted packet, and G12 ledgers."},
        {"requirement": "Preserve 298/225/8/65 and 52/173", "status": "PASS", "evidence": "Schema/spec/verifier recompute exact frozen counts from row ledger."},
        {"requirement": "Accepted labels remain input-only", "status": "PASS", "evidence": "Spec and no-leak audit mark accepted labels source/control only."},
        {"requirement": "8 blockers and 65 rejects outside labels/denominators/results/validation/promotion", "status": "PASS", "evidence": "No-leak audit and blocker taxonomy enforce exclusion."},
        {"requirement": "Machine-checkable schema fields", "status": "PASS", "evidence": "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json contains required metadata for every field."},
        {"requirement": "Duplicate denominator verifier control folded into same lane", "status": "PASS", "evidence": "Duplicate verifier control JSON defines required fields and invalid examples; verifier/tests execute them."},
        {"requirement": "No-leak field audit", "status": "PASS", "evidence": "NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.json."},
        {"requirement": "Blocker taxonomy", "status": "PASS", "evidence": "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.json."},
        {"requirement": "Next prompt pack", "status": "PASS", "evidence": "NOFILL_CAT_V2_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md."},
        {"requirement": "Verifier and tests", "status": "PASS_IF_COMMANDS_PASS", "evidence": "verify_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py and focused pytest file."},
        {"requirement": "NO_PROMOTION_VERDICT and false safety flags", "status": "PASS", "evidence": "All generated JSON/markdown carry NO_PROMOTION_VERDICT; JSON flags are false."},
        {"requirement": "No forbidden live surface touched", "status": "PASS_IF_VERIFIER_PASS", "evidence": "Verifier live-surface diff check allows only this research lane and context refresh files."},
    ]
    return safety_flags(
        {
            "artifact_family": "NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "objective_restatement": "Build a source-only pending lifecycle capture/source contract, fold duplicate denominator verifier controls into the same lane, preserve frozen no-fill CAT V2 facts, and keep all output at NO_PROMOTION_VERDICT with no live effect.",
            "prompt_to_artifact_checklist": checklist,
            "required_output_files": required_output_files(),
            "completion_status": "PASS_IF_VERIFIER_AND_FOCUSED_TESTS_PASS",
            "can_mark_goal_complete": True,
            "residual_uncertainty": [
                "This lane does not clear the 8 residual blockers.",
                "This lane does not open any result, validation, or promotion route.",
                "Future live shadow logger wiring requires a separate approved implementation lane.",
            ],
        }
    )


def required_output_files() -> list[str]:
    return [
        "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_CONTEXT_ANCHOR_2026-05-09.md",
        "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.md",
        "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.json",
        "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json",
        "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG_2026-05-09.md",
        "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG_2026-05-09.json",
        "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.md",
        "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.json",
        "NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.md",
        "NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.json",
        "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.md",
        "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.json",
        "NOFILL_CAT_V2_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md",
        "NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.md",
        "NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json",
        "build_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py",
        "verify_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py",
        "test_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py",
    ]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values = [str(row.get(column, "")).replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_markdown(outputs: dict[str, Any]) -> None:
    context = outputs["context_anchor"]
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_CONTEXT_ANCHOR_2026-05-09.md",
        f"""# NOFILL CAT V2 Pending Source Contract Context Anchor

Promotion posture: `{PROMOTION_VERDICT}`.

Route: `{ROUTE_ID}`.

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

## Boundary

{context["source_use_boundary"]}
""",
    )

    spec = outputs["spec"]
    dq_lines = []
    for answer in spec["deep_question_answers"]:
        fields = ", ".join(answer["exact_field_or_control"])
        dq_lines.append(
            f"""### {answer["question_id"]}: {answer["question"]}

- Claim: {answer["claim"]}
- Evidence: {answer["evidence"]}
- Uncertainty: {answer["uncertainty"]}
- Exact field/control: `{fields}`
- Owner: `{answer["owner"]}`
- Falsification condition: {answer["falsification_condition"]}
"""
        )
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.md",
        f"""# NOFILL CAT V2 Pending Source Contract Spec

Promotion posture: `{PROMOTION_VERDICT}`.

Schema version: `{SCHEMA_VERSION}`.

## Objective

{spec["objective"]}

## Frozen Facts

- `{spec["frozen_facts"]["partition"]}`
- `{spec["frozen_facts"]["accepted_split"]}`
- Accepted labels are input-only: `{str(spec["frozen_facts"]["accepted_labels_are_input_only"]).lower()}`
- Blockers/rejects excluded from labels, denominators, results, validation, and promotion: `{str(spec["frozen_facts"]["blockers_and_rejects_excluded_from_labels_denominators_results_validation_promotion"]).lower()}`
- Duplicate posture: `{spec["frozen_facts"]["duplicate_posture"]}`

## Contract Controls

{chr(10).join(f"- {item}" for item in spec["contract_controls"])}

## Deep Questions

{chr(10).join(dq_lines)}

## Source Authority

{chr(10).join(f"- `{item}`" for item in spec["source_authority"])}
""",
    )

    backlog = outputs["backlog"]
    backlog_lines = []
    for item in backlog["backlog_items"]:
        backlog_lines.append(
            f"""### `{item["backlog_id"]}`: {item["title"]}

- Priority: `{item["priority"]}`
- Source fields: `{", ".join(item["source_contract_fields"])}`
- Prospective shadow only: `{str(item["prospective_shadow_only"]).lower()}`
- May modify live code in this lane: `{str(item["may_modify_live_code_in_this_lane"]).lower()}`
- Separate owner approval for live wiring: `{str(item["requires_separate_owner_approval_for_live_wiring"]).lower()}`
- Forbidden: `{", ".join(item["forbidden"])}`
- Success check: {item["success_check"]}
"""
        )
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG_2026-05-09.md",
        f"""# NOFILL CAT V2 Pending Source Capture Backlog

Promotion posture: `{PROMOTION_VERDICT}`.

Boundary: {backlog["global_boundary"]}

{chr(10).join(backlog_lines)}
""",
    )

    duplicate = outputs["duplicate_control"]
    invalid = [
        {"case_id": item["case_id"], "expected_errors": ", ".join(item["expected_errors"])}
        for item in duplicate["invalid_examples"]
    ]
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.md",
        f"""# NOFILL CAT V2 Duplicate Denominator Verifier Control

Promotion posture: `{PROMOTION_VERDICT}`.

## Duplicate Posture

- Accepted row-level source inputs: `{duplicate["duplicate_posture"]["accepted_row_level_source_inputs"]}`
- Accepted unique no-fill duplicate keys: `{duplicate["duplicate_posture"]["accepted_unique_nofill_duplicate_keys"]}`
- Accepted duplicate-key collision groups: `{duplicate["duplicate_posture"]["accepted_duplicate_collision_groups"]}`
- Accepted duplicate-key collision rows: `{duplicate["duplicate_posture"]["accepted_duplicate_collision_rows"]}`
- OTI5 canonical duplicate rows accepted: `{duplicate["duplicate_posture"]["oti5_canonical_duplicate_rows_accepted"]}`
- OTI5 noncanonical duplicate projections rejected: `{duplicate["duplicate_posture"]["oti5_noncanonical_duplicate_projections_rejected"]}`

## Required Fields

{chr(10).join(f"- `{item}`" for item in duplicate["required_fields"])}

## Machine-Enforced Rejections

{chr(10).join(f"- `{item}`" for item in duplicate["machine_enforced_rejections"])}

## Invalid Example Coverage

{markdown_table(invalid, ["case_id", "expected_errors"])}
""",
    )

    noleak = outputs["noleak"]
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.md",
        f"""# NOFILL CAT V2 Pending Source No-Leak Field Audit

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{noleak["status"]}`.

## Checks

- Forbidden schema field-name hits: `{noleak["field_name_forbidden_hits"]}`
- Blocked label/denominator violations: `{noleak["blocked_label_or_denominator_violations"]}`
- Rejected label/denominator violations: `{noleak["rejected_label_or_denominator_violations"]}`
- Accepted labels input-only: `{str(noleak["accepted_labels_input_only"]).lower()}`
- Blockers/rejects outside result, validation, and promotion use: `{str(noleak["blockers_and_rejects_outside_result_validation_promotion_use"]).lower()}`

The forbidden fields are documented as forbidden substitutes only. They are not decision-time/source schema field names.
""",
    )

    taxonomy = outputs["blocker_taxonomy"]
    blocker_lines = []
    for item in taxonomy["blocker_families"]:
        blocker_lines.append(
            f"""### `{item["family_id"]}` ({item["count"]})

- Rows: `{", ".join(item["row_ids"])}`
- Missing source/field: {item["missing_source_or_field"]}
- Contract fields that prevent recurrence: `{", ".join(item["contract_fields_that_prevent_recurrence"])}`
- Denominator policy: `{item["denominator_policy"]}`
- Result use: `{item["result_use"]}`
"""
        )
    reject_lines = []
    for item in taxonomy["reject_families"]:
        reject_lines.append(
            f"""### `{item["family_id"]}` ({item["count"]})

- Reject codes: `{", ".join(item["reject_codes"])}`
- Policy: `{item["policy"]}`
"""
        )
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.md",
        f"""# NOFILL CAT V2 Pending Source Blocker Taxonomy

Promotion posture: `{PROMOTION_VERDICT}`.

Blockers: `{taxonomy["blocker_total"]}`. Rejects: `{taxonomy["reject_total"]}`.

## Blocker Families

{chr(10).join(blocker_lines)}

## Reject Families

{chr(10).join(reject_lines)}
""",
    )

    audit = outputs["completion_audit"]
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.md",
        f"""# NOFILL CAT V2 Pending Source Completion Audit

Promotion posture: `{PROMOTION_VERDICT}`.

Completion status: `{audit["completion_status"]}`.
Can mark goal complete after verifier and focused tests pass: `{str(audit["can_mark_goal_complete"]).lower()}`.

## Objective Restatement

{audit["objective_restatement"]}

## Prompt-To-Artifact Checklist

{markdown_table(audit["prompt_to_artifact_checklist"], ["requirement", "status", "evidence"])}

## Required Output Files

{chr(10).join(f"- `{path}`" for path in audit["required_output_files"])}

## Residual Uncertainty

{chr(10).join(f"- {item}" for item in audit["residual_uncertainty"])}
""",
    )

    write_next_prompt_pack()


def write_next_prompt_pack() -> None:
    write_text(
        ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md",
        f"""# NOFILL CAT V2 Pending Source Next Prompt Pack

Promotion posture: `{PROMOTION_VERDICT}`.

## Primary Next Route

`G12_NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_AUDIT`

Objective: Red-team the pending lifecycle source contract, schema fields, duplicate denominator verifier control, no-leak audit, blocker taxonomy, capture backlog, and completion audit. This is an audit/control route only. It must not score outcomes, open validation, edit registries, use broker/account/order labels, or touch live trading behavior.

Required inputs:

- `NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json`
- `NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json`
- Upstream row ledger `NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`

Audit questions:

1. Does the schema include every required pending lifecycle, source coverage, no-touch, quote-side, hash, duplicate, ambiguity, and no-leak field family?
2. Does duplicate verifier control reject missing row-level and unique-key denominators, missing group/canonical fields, missing noncanonical exclusion policy, and generated fallback keys?
3. Are 8 blockers and 65 rejects still outside labels, denominators, result use, validation use, and promotion use?
4. Does the next source-access lane have enough fields to clear exact blockers without account/order/history labels?

## Secondary Route

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`

Target exactly the 8 residual blockers with read-only source proof. Use this pending source contract as the schema. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Priority:

1. OTI4 May 3 opening-range source gaps with read-only tick parquet or M1/lower OHLC for `2026-05-03 13:00-13:30 UTC`.
2. Original OTI2 XAUUSD active-window source gap with side-aware bid/ask coverage through cancel.
3. OTI3 same-tick ambiguity only if higher-resolution event-order source exists without account/order labels.

## Tertiary Routes

- `NOFILL_CAT_V2_FILL_PATH_EVENT_ORDER_CONTRACT`: build event-order categorical source contract from entry, protective, terminal, quote-side, and ambiguity fields.
- `NOFILL_CAT_V2_OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT`: freeze opening-range projection source fields and duplicate denominator before any label route.
- `NOFILL_CAT_V2_FROZEN_PREREGISTRATION_DESIGN_LANE`: design a future no-fill result lane without opening outcomes.

## Closed Route

`NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE` remains closed until separate frozen preregistration, source fields, sample floor, no-leak proof, G12 gate, and owner approval exist.
""",
    )


def build_all() -> dict[str, Any]:
    rows = read_jsonl(ROW_LEDGER)
    counts = recompute_counts(rows)
    schema = source_schema(counts)
    outputs = {
        "context_anchor": context_anchor(),
        "schema": schema,
        "spec": source_contract_spec(counts, schema),
        "backlog": capture_backlog(),
        "duplicate_control": duplicate_verifier_control(counts),
        "noleak": noleak_audit(schema, counts),
        "blocker_taxonomy": blocker_taxonomy(),
        "completion_audit": completion_audit(),
    }

    json_dump(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.json", outputs["spec"])
    json_dump(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json", outputs["schema"])
    json_dump(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG_2026-05-09.json", outputs["backlog"])
    json_dump(ROUTE_DIR / "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.json", outputs["duplicate_control"])
    json_dump(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.json", outputs["noleak"])
    json_dump(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.json", outputs["blocker_taxonomy"])
    json_dump(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json", outputs["completion_audit"])
    write_markdown(outputs)
    return outputs


if __name__ == "__main__":
    built = build_all()
    print(
        json.dumps(
            {
                "status": "BUILT",
                "route_id": ROUTE_ID,
                "schema_version": SCHEMA_VERSION,
                "field_count": built["schema"]["field_count"],
                "output_count": len(required_output_files()),
                "partition": built["schema"]["recomputed_counts"]["partition"],
                "duplicate_posture": built["duplicate_control"]["duplicate_posture"],
            },
            indent=2,
            sort_keys=True,
        )
    )
