from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROUTE_ID = "NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT"
SCHEMA_VERSION = "nofill_cat_v3_forward_lifecycle_capture_contract_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]

PROMPT_PATH = ROUTE_DIR / "NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_GOAL_PROMPT_2026-05-09.md"
OUTCOME_ROOT = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
G0_DIR = OUTCOME_ROOT / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review"
G12_COUNT_DIR = OUTCOME_ROOT / "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit"
RESULT_CONTRACT_DIR = OUTCOME_ROOT / "nofill_cat_v3_result_contract_update"
G12_RESULT_DIR = OUTCOME_ROOT / "g12_nofill_cat_v3_result_contract_audit"
G12_SOURCE_CONTROL_DIR = OUTCOME_ROOT / "g12_nofill_cat_v3_source_control_audit"
V2_PENDING_DIR = OUTCOME_ROOT / "nofill_cat_v2_pending_lifecycle_source_contract_builder"
G12_V2_PENDING_DIR = OUTCOME_ROOT / "g12_nofill_cat_v2_pending_source_contract_audit"

CONTROL_INPUTS = [
    PROMPT_PATH,
    REPO_ROOT / ".context/LIVE_STATE.md",
    REPO_ROOT / ".context/00_core/quick_reference_card.md",
    REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
    REPO_ROOT / ".context/00_core/research_current_state.md",
    REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md",
    REPO_ROOT / ".context/00_READING_ORDER.md",
    REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    G0_DIR / "G0_NOFILL_CAT_V3_SYNTHESIS_DECISION_LEDGER_2026-05-09.md",
    G0_DIR / "G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_2026-05-09.json",
    G0_DIR / "G0_NOFILL_CAT_V3_CATEGORICAL_LEARNING_SYNTHESIS_2026-05-09.md",
    G0_DIR / "G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md",
    G0_DIR / "G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_2026-05-09.json",
    G12_COUNT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_DECISION_LEDGER_2026-05-09.md",
    G12_COUNT_DIR / "NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_2026-05-09.json",
    RESULT_CONTRACT_DIR / "NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-09.json",
    G12_RESULT_DIR / "G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_2026-05-09.json",
    G12_SOURCE_CONTROL_DIR / "G12_NOFILL_REMAINING_DECISION_LEDGER_2026-05-09.json",
    G12_SOURCE_CONTROL_DIR / "G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.json",
    V2_PENDING_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.json",
    V2_PENDING_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json",
    V2_PENDING_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG_2026-05-09.json",
    G12_V2_PENDING_DIR / "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json",
]

STALE_PROMPT_PATH = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_cat_v3_result_contract_audit/"
    "G12_NOFILL_CAT_V3_COMPLETION_AUDIT_2026-05-09.json"
)
ACTUAL_G12_RESULT_AUDIT_PATH = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_cat_v3_result_contract_audit/"
    "G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_2026-05-09.json"
)

EXPECTED_PARTITION = {
    "universe_rows": 298,
    "accepted_row_level_inputs": 225,
    "source_control_rows": 4,
    "source_impossible_rows": 4,
    "rejected_rows": 65,
    "accepted_unique_nofill_duplicate_keys": 182,
    "accepted_secondary_duplicate_group_ids": 139,
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
PRIMARY_LABEL_COUNTS = {
    "nofill_terminal_before_entry": 110,
    "source_corrected_no_entry_through_pending_horizon": 32,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
}
OPENING_DRIVE_ROW_LEVEL_COUNT = 51
REJECT_OVERLAPS_NEUTRALIZED = 47

REQUIRED_FIELD_NAMES = [
    "forward_capture_row_id",
    "source_route",
    "source_row_id",
    "symbol",
    "broker_symbol",
    "source_symbol",
    "session",
    "side",
    "decision_timeframe",
    "candidate_id",
    "trade_id_source_safe",
    "source_packet_id",
    "source_inventory_id",
    "source_artifact_hash",
    "parser_version",
    "parser_code_hash",
    "builder_version",
    "controlling_head",
    "decision_asof_utc",
    "pending_intent_created_utc",
    "intended_entry_price",
    "side_aware_quote_reference",
    "intended_stop_or_protective_area",
    "intended_terminal_or_target_area",
    "pending_horizon_start_utc",
    "pending_horizon_end_utc",
    "cancel_expiry_utc",
    "cancel_expiry_reason_code",
    "tick_coverage_window_start_utc",
    "tick_coverage_window_end_utc",
    "lower_tf_coverage_window_start_utc",
    "lower_tf_coverage_window_end_utc",
    "missing_coverage_intervals",
    "quote_side",
    "spread_state",
    "timezone_normalization",
    "broker_server_timestamp_policy",
    "source_granularity",
    "first_quote_utc",
    "last_quote_utc",
    "source_file_hashes",
    "source_manifest_id",
    "source_manifest_created_utc",
    "side_aware_entry_touch_status",
    "entry_touch_first_utc",
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
    "no_entry_through_source_window_proof",
    "no_entry_through_pending_horizon_proof",
    "terminal_before_entry_categorical_proof",
    "event_order_resolution_method",
    "event_sequence",
    "same_tick_same_bar_ambiguity_status",
    "tie_policy",
    "impossible_from_source_code",
    "exact_next_source_if_unresolved",
    "nofill_duplicate_key",
    "duplicate_group_id",
    "canonical_row_id",
    "is_canonical_row",
    "noncanonical_projection_rule",
    "accepted_first_filtering_status",
    "reject_overlap_exclusion_status",
    "source_control_source_impossible_exclusion_status",
    "concentration_bucket",
    "source_control_state",
    "capture_backlog_item_id",
    "capture_backlog_status",
    "input_only_categorical_label",
    "future_result_label_status",
    "broker_actual_r_status",
    "hidden_path_label_status",
    "live_account_order_label_status",
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "promotion_verdict",
    "forbidden_field_scan_status",
]

FIELD_FAMILIES = {
    "row_identity_provenance": [
        "forward_capture_row_id",
        "source_route",
        "source_row_id",
        "symbol",
        "broker_symbol",
        "source_symbol",
        "session",
        "side",
        "decision_timeframe",
        "candidate_id",
        "trade_id_source_safe",
        "source_packet_id",
        "source_inventory_id",
        "source_artifact_hash",
        "parser_version",
        "parser_code_hash",
        "builder_version",
        "controlling_head",
    ],
    "decision_asof": ["decision_asof_utc"],
    "pending_intent_creation": [
        "pending_intent_created_utc",
        "intended_entry_price",
        "side_aware_quote_reference",
        "intended_stop_or_protective_area",
        "intended_terminal_or_target_area",
    ],
    "pending_horizon_cancel_expiry": [
        "pending_horizon_start_utc",
        "pending_horizon_end_utc",
        "cancel_expiry_utc",
        "cancel_expiry_reason_code",
    ],
    "source_coverage_quote": [
        "tick_coverage_window_start_utc",
        "tick_coverage_window_end_utc",
        "lower_tf_coverage_window_start_utc",
        "lower_tf_coverage_window_end_utc",
        "missing_coverage_intervals",
        "quote_side",
        "spread_state",
        "timezone_normalization",
        "broker_server_timestamp_policy",
        "source_granularity",
        "first_quote_utc",
        "last_quote_utc",
        "source_file_hashes",
    ],
    "tick_or_ltf_source_manifest": [
        "source_manifest_id",
        "source_manifest_created_utc",
    ],
    "touch_no_touch_proof": [
        "side_aware_entry_touch_status",
        "entry_touch_first_utc",
        "terminal_area_touch_status",
        "terminal_area_first_touch_utc",
        "protective_area_touch_status",
        "protective_area_first_touch_utc",
        "no_entry_through_source_window_proof",
        "no_entry_through_pending_horizon_proof",
        "terminal_before_entry_categorical_proof",
    ],
    "event_order_resolution": [
        "event_order_resolution_method",
        "event_sequence",
        "same_tick_same_bar_ambiguity_status",
        "tie_policy",
        "impossible_from_source_code",
        "exact_next_source_if_unresolved",
    ],
    "duplicate_denominator": [
        "nofill_duplicate_key",
        "duplicate_group_id",
        "canonical_row_id",
        "is_canonical_row",
        "noncanonical_projection_rule",
        "accepted_first_filtering_status",
        "reject_overlap_exclusion_status",
        "source_control_source_impossible_exclusion_status",
        "concentration_bucket",
    ],
    "label_family_separation": [
        "source_control_state",
        "input_only_categorical_label",
        "future_result_label_status",
        "broker_actual_r_status",
        "hidden_path_label_status",
        "live_account_order_label_status",
    ],
    "no_leak_audit": [
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "promotion_verdict",
        "forbidden_field_scan_status",
    ],
    "capture_backlog_control": [
        "capture_backlog_item_id",
        "capture_backlog_status",
        "exact_next_source_if_unresolved",
        "impossible_from_source_code",
        "source_control_state",
    ],
}

FORBIDDEN_SOURCE_FIELD_NAMES = {
    "actual_r",
    "synthetic_path_r",
    "r_value",
    "r_multiple",
    "win_rate",
    "expectancy",
    "broker_actual_r",
    "account_history",
    "mt5_order_ticket",
    "mt5_deal_id",
    "order_send_success",
    "order_send_attempted",
    "broker_fill_state",
    "live_order_state",
    "paid_api_result",
    "databento_payload",
}

ALLOWED_SOURCE_TYPES = [
    "decision_time_candidate_safe_projection",
    "pending_limit_lifecycle_source_safe_projection",
    "candidate_path_follow_source_projection",
    "candidate_ltf_path_order_source_projection",
    "tick_parquet_readonly_manifest",
    "lower_tf_ohlc_readonly_manifest",
    "source_control_rebuild_artifact",
    "source_contract_artifact",
    "parser_hash_manifest",
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


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - defensive context capture
        return f"UNAVAILABLE: {exc}"


def safety_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "opens_selector_logic": False,
        "opens_registry_edit": False,
        "opens_paid_api_or_databento_route": False,
        "changes_live_trading_behavior": False,
    }


def input_records() -> list[dict[str, Any]]:
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


def source_inventory() -> dict[str, Any]:
    worktree_tick_root = REPO_ROOT / "data/ticks"
    external_tick_root = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")
    sierra_root = Path(r"C:\SierraChart\Data")
    prior_worktree_route = (
        Path(r"C:\tmp\gtos_otb\NOFILLUSDJPYSEQ")
        / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access"
    )

    def dir_count(root: Path, pattern: str = "*") -> dict[str, Any]:
        if not root.exists():
            return {"path": str(root), "exists": False, "count": 0, "sample": []}
        items = sorted(root.glob(pattern))
        return {
            "path": str(root),
            "exists": True,
            "count": len(items),
            "sample": [item.name for item in items[:12]],
        }

    external_symbol_counts = {}
    if external_tick_root.exists():
        for symbol_dir in sorted(path for path in external_tick_root.iterdir() if path.is_dir()):
            external_symbol_counts[symbol_dir.name] = len(list(symbol_dir.glob("*.parquet")))

    return {
        "worktree_data_ticks": dir_count(worktree_tick_root),
        "external_ai_trading_agent_tick_root": {
            **dir_count(external_tick_root),
            "parquet_counts_by_symbol": external_symbol_counts,
            "contract_status": "available_as_readonly_source_inventory_not_validation_safe",
        },
        "sierra_chart_data_root": {
            **dir_count(sierra_root, "*.scid"),
            "market_depth_dir_exists": (sierra_root / "MarketDepthData").exists(),
            "contract_status": "available_source_inventory_requires_symbol_mapping_and_parser_hashing",
        },
        "prior_worktree_usdjpy_quote_sequence_route": {
            "path": str(prior_worktree_route),
            "exists": prior_worktree_route.exists(),
            "current_worktree_route_exists": (
                OUTCOME_ROOT / "nofill_cat_v3_usdjpy_quote_event_sequence_source_access"
            ).exists(),
            "contract_status": "prior_worktree_evidence_only_not_consumed_by_this_packet",
        },
    }


def field_family_for(name: str) -> str:
    for family, names in FIELD_FAMILIES.items():
        if name in names:
            return family
    raise KeyError(name)


def field_requiredness(name: str) -> str:
    optional = {
        "trade_id_source_safe",
        "missing_coverage_intervals",
        "spread_state",
        "entry_touch_first_utc",
        "terminal_area_first_touch_utc",
        "protective_area_first_touch_utc",
        "event_sequence",
        "exact_next_source_if_unresolved",
        "concentration_bucket",
        "input_only_categorical_label",
    }
    return "optional_with_explicit_null_reason" if name in optional else "required"


def asof_rule_for(name: str) -> str:
    if name in {
        "source_artifact_hash",
        "parser_version",
        "parser_code_hash",
        "builder_version",
        "controlling_head",
        "source_file_hashes",
        "forbidden_field_scan_status",
    }:
        return "record_at_capture_or_parser_build_time; never substitute later outcome data"
    if name in {
        "side_aware_entry_touch_status",
        "entry_touch_first_utc",
        "terminal_area_touch_status",
        "terminal_area_first_touch_utc",
        "protective_area_touch_status",
        "protective_area_first_touch_utc",
        "no_entry_through_source_window_proof",
        "no_entry_through_pending_horizon_proof",
        "terminal_before_entry_categorical_proof",
        "event_order_resolution_method",
        "event_sequence",
        "same_tick_same_bar_ambiguity_status",
        "tie_policy",
        "impossible_from_source_code",
    }:
        return "may use only source ticks/ltf bars inside the declared pending horizon and source coverage window"
    if name in {"future_result_label_status", "broker_actual_r_status", "hidden_path_label_status", "live_account_order_label_status"}:
        return "must remain NOT_OPENED_OR_FORBIDDEN in this route"
    return "must be known at decision_asof_utc or derived from a declared source manifest without account/order-history outcomes"


def no_leak_role_for(name: str) -> str:
    if name in {"validation_safe", "outcome_review_opened", "live_effect", "promotion_verdict"}:
        return "safety_flag"
    if name in {"future_result_label_status", "broker_actual_r_status", "hidden_path_label_status", "live_account_order_label_status"}:
        return "closed_result_label_guard"
    if name in {"nofill_duplicate_key", "duplicate_group_id", "canonical_row_id", "is_canonical_row"}:
        return "denominator_control_only"
    if "touch" in name or "event_order" in name or name.endswith("_proof"):
        return "source_event_order_control_only"
    return "source_identity_or_capture_metadata"


def contract_fields() -> list[dict[str, Any]]:
    fields = []
    for name in REQUIRED_FIELD_NAMES:
        fields.append(
            {
                "field_name": name,
                "field_family": field_family_for(name),
                "required_or_optional": field_requiredness(name),
                "allowed_source_types": ALLOWED_SOURCE_TYPES,
                "as_of_rule": asof_rule_for(name),
                "hash_requirement": "source_file_or_artifact_sha256_required_before row is contract-complete",
                "no_leak_role": no_leak_role_for(name),
                "forbidden_substitute_fields": sorted(FORBIDDEN_SOURCE_FIELD_NAMES),
                "capture_mode": "forward_source_capture_only",
                "verification_rule": (
                    "row fails contract if populated from account history, MT5 order/deal history, "
                    "actual R, synthetic R, win rate, expectancy, paid API, Databento, or post-outcome labels"
                ),
            }
        )
    return fields


def source_audit_records() -> list[dict[str, Any]]:
    return [
        {
            "surface": "src/components/pending_limit_lifecycle_logger.py",
            "status": "usable_only_after_safe_projection_allowlist",
            "source_value": "captures pending intent, candle/tick snapshots, checked-candle context, and asof cutoff",
            "contamination_risk": [
                "actual_r",
                "synthetic_path_r",
                "mt5_order_ticket",
                "pending_ticket",
                "order_send_attempted",
                "order_send_success",
                "broker_fill_state",
            ],
            "contract_rule": "never consume raw rows directly; build a source-safe projection and drop every order/account/result-shaped field",
        },
        {
            "surface": "src/research_infra/pending_limit_lifecycle_audit.py",
            "status": "useful_for_audit_context_not_decision_features",
            "source_value": "joins lifecycle, candidates, paths, ltf, trade records, account truth, and persisted intents",
            "contamination_risk": ["account truth", "trade record execution fields", "actual R context"],
            "contract_rule": "use only to audit source coverage and missing-source blockers; do not feed result labels",
        },
        {
            "surface": "scripts/follow_live_candidate_paths.py",
            "status": "source_projection_candidate_with_m15_limitations",
            "source_value": "forward observation labels for candidate path evolution from OHLC",
            "contamination_risk": ["M15 cannot claim same-bar tick order", "MT5 route must not be run by this contract lane"],
            "contract_rule": "future implementation may read existing artifacts, but this lane opens no MT5 route",
        },
        {
            "surface": "shadow_logs/candidate_ltf_path_order.jsonl",
            "status": "event-order_source_candidate_with_result_field_quarantine",
            "source_value": "M1 first-touch timestamps and ambiguity states",
            "contamination_risk": ["terminal_event_r and result-shaped fields must be excluded"],
            "contract_rule": "consume first-touch and ambiguity fields only, never terminal R fields",
        },
        {
            "surface": "shadow_logs/strategy_follow_candidates.jsonl",
            "status": "decision_context_source_candidate_after_allowlist",
            "source_value": "decision-time setup geometry, MSO summary, trade parameters, and no-post-outcome guard",
            "contamination_risk": ["final_outcome_at_log and mt5_order_ticket fields may exist downstream"],
            "contract_rule": "use an explicit field allowlist for geometry and decision asof fields",
        },
    ]


def contract_json() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": GENERATED_AT_UTC,
        **safety_flags(),
        "evidence_class": "source_capture_contract",
        "contract_status": "SOURCE_CAPTURE_CONTRACT_BUILT_NO_LIVE_WIRING",
        "controlling_decision": "G0_ACCEPT_AS_DURABLE_CATEGORICAL_CONTROL_SYNTHESIS_NO_RESULT_SCORING",
        "controlling_counts": {
            **EXPECTED_PARTITION,
            "source_control_rows": SOURCE_CONTROL_ROWS,
            "source_impossible_rows": SOURCE_IMPOSSIBLE_ROWS,
            "primary_label_counts": PRIMARY_LABEL_COUNTS,
            "opening_drive_row_level_count": OPENING_DRIVE_ROW_LEVEL_COUNT,
            "reject_overlaps_neutralized": REJECT_OVERLAPS_NEUTRALIZED,
        },
        "field_families": sorted(FIELD_FAMILIES),
        "required_field_names": REQUIRED_FIELD_NAMES,
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "forbidden_source_field_names": sorted(FORBIDDEN_SOURCE_FIELD_NAMES),
        "duplicate_denominator_policy": {
            "primary_key": "nofill_duplicate_key",
            "secondary_group": "duplicate_group_id",
            "row_level_denominator": 225,
            "unique_primary_denominator": 182,
            "secondary_group_denominator": 139,
            "accepted_first_filtering": "required_before_reject_overlap_scan",
            "reject_overlap_rule": "47 reject-overlap rows stay neutralized and cannot re-enter denominators",
            "source_control_source_impossible_rule": "the 4 source-control and 4 source-impossible rows remain outside result labels and performance denominators",
            "canonical_rule": "canonical_row_id must be stable before any duplicate group contributes a counting row",
        },
        "asof_policy": {
            "decision_context": "fields derived from candidate or pending intent must be known at decision_asof_utc",
            "forward_capture": "future tick/ltf observations must be bounded to pending_horizon_start_utc through pending_horizon_end_utc",
            "event_order": "same-tick, same-M1, same-M15, or missing-sequence cases must be marked ambiguous or impossible, never resolved by account outcomes",
            "hashing": "every source file and parser artifact must have SHA256 before a row is contract-complete",
        },
    }


def schema_json() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **safety_flags(),
        "contract_fields": contract_fields(),
        "required_field_families": sorted(FIELD_FAMILIES),
        "required_field_names": REQUIRED_FIELD_NAMES,
    }


def no_leak_policy_json() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **safety_flags(),
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "forbidden_source_field_names": sorted(FORBIDDEN_SOURCE_FIELD_NAMES),
        "closed_states": {
            "future_result_label_status": "NOT_OPENED",
            "broker_actual_r_status": "FORBIDDEN",
            "hidden_path_label_status": "FORBIDDEN",
            "live_account_order_label_status": "FORBIDDEN",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "required_scans": [
            "field allowlist scan",
            "forbidden key scan",
            "forbidden true-flag scan",
            "changed-path live-surface scan",
            "source hash completeness scan",
        ],
    }


def duplicate_policy_json() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **safety_flags(),
        "denominators": {
            "row_level_accepted_inputs": 225,
            "unique_nofill_duplicate_key": 182,
            "secondary_duplicate_group_id": 139,
        },
        "rules": [
            "apply accepted-first filtering to accepted_input_only rows before any duplicate count",
            "exclude reject-overlap rows before label or denominator assignment",
            "exclude source-control and source-impossible rows from result labels and performance denominators",
            "require canonical_row_id and is_canonical_row before counting duplicate groups",
            "fail rows with generated, fallback, missing, or non-stable duplicate keys",
        ],
        "required_fields": [
            "nofill_duplicate_key",
            "duplicate_group_id",
            "canonical_row_id",
            "is_canonical_row",
            "noncanonical_projection_rule",
            "accepted_first_filtering_status",
            "reject_overlap_exclusion_status",
            "source_control_source_impossible_exclusion_status",
        ],
    }


def backlog_json() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **safety_flags(),
        "implementation_status": "contract_only_no_live_wiring",
        "backlog": [
            {
                "rank": 1,
                "item": "source_safe_projection_builder",
                "priority": "P0",
                "scope": "offline research builder over already captured artifacts",
                "done_definition": "emits only the contract schema fields and fails closed on forbidden fields or missing hashes",
                "approval_needed": False,
            },
            {
                "rank": 2,
                "item": "tick_and_ltf_coverage_hasher",
                "priority": "P0",
                "scope": "read-only manifest over existing tick parquet, M1/LTF sources, and parser code hashes",
                "done_definition": "source_file_hashes, coverage windows, missing intervals, and parser_code_hash populated",
                "approval_needed": False,
            },
            {
                "rank": 3,
                "item": "event_order_resolution_verifier",
                "priority": "P1",
                "scope": "source-only event ordering with explicit ambiguity or impossibility codes",
                "done_definition": "same-tick/same-bar cases marked unresolved unless source sequence proves order",
                "approval_needed": False,
            },
            {
                "rank": 4,
                "item": "future_live_shadow_logger_projection",
                "priority": "P1",
                "scope": "proposal only; any live logger edit touches src and needs CEO approval before implementation",
                "done_definition": "approval gate documented; no live code changed by this route",
                "approval_needed": True,
            },
            {
                "rank": 5,
                "item": "usdjpy_broker_native_quote_event_sequence_source_access",
                "priority": "P1",
                "scope": "source access route for NOFILL-CAT-ROW-0130/0143/0165/0178",
                "done_definition": "bid/ask event sequence with sequence ID or sub-row timestamp, no account/order labels",
                "approval_needed": False,
            },
            {
                "rank": 6,
                "item": "may3_opening_drive_source_projection_contract",
                "priority": "P2",
                "scope": "market-session empty/tick-gap source projection for May 3 opening-drive rows",
                "done_definition": "source-control rows remain input-only and unscored",
                "approval_needed": False,
            },
            {
                "rank": 7,
                "item": "fill_path_vocabulary_contract_alignment",
                "priority": "P2",
                "scope": "align future categorical vocabulary to source proofs, not result scoring",
                "done_definition": "no entry/terminal/protective-area labels mapped to source-only proofs",
                "approval_needed": False,
            },
        ],
        "stop_conditions": [
            "missing source hash",
            "forbidden field present after projection",
            "same-tick/same-bar ambiguity without sequence source",
            "duplicate key generated or missing",
            "attempt to open validation_safe, outcome_review_opened, live_effect, or result scoring",
        ],
    }


def source_audit_json() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **safety_flags(),
        "source_inventory": source_inventory(),
        "code_surface_audit": source_audit_records(),
        "prompt_path_reconciliation": {
            "stale_prompt_path": STALE_PROMPT_PATH,
            "stale_prompt_path_exists": (REPO_ROOT / STALE_PROMPT_PATH).exists(),
            "actual_path_used": ACTUAL_G12_RESULT_AUDIT_PATH,
            "actual_path_exists": (REPO_ROOT / ACTUAL_G12_RESULT_AUDIT_PATH).exists(),
            "resolution": "actual committed result-contract audit path used; stale prompt path recorded as input defect",
        },
        "forbidden_routes_not_used": [
            "MT5 order/account/history routes",
            "paid API",
            "Databento",
            "credentials",
            "remote push",
            "registry edits",
            "live trading prompts or src behavior changes",
        ],
    }


def completion_audit_json() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": GENERATED_AT_UTC,
        **safety_flags(),
        "objective": "Build the forward no-fill lifecycle capture contract, source-safe schema, no-leak/duplicate/as-of rules, source/capture backlog, verifier plan, and next prompt pack.",
        "git_context": {
            "head_before_commit": git_output(["rev-parse", "--short", "HEAD"]),
            "branch": git_output(["branch", "--show-current"]),
            "status_short_at_build_time": git_output(["status", "--short"]),
        },
        "control_inputs": input_records(),
        "deliverables": required_output_files(),
        "searched_source_surfaces": [
            "src/components/pending_limit_lifecycle_logger.py",
            "src/research_infra/pending_limit_lifecycle_audit.py",
            "src/research_infra/opportunity_lifecycle_audit.py",
            "src/research_infra/candidate_path_contract.py",
            "scripts/follow_live_candidate_paths.py",
            "scripts/backfill_pending_limit_lifecycle_audit.py",
            "shadow_logs/pending_limit_lifecycle.jsonl",
            "shadow_logs/pending_limit_lifecycle_audit.jsonl",
            "shadow_logs/candidate_path_follow.jsonl",
            "shadow_logs/candidate_ltf_path_order.jsonl",
            "shadow_logs/strategy_follow_candidates.jsonl",
            "data/ticks",
            r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
            r"C:\SierraChart\Data",
            r"C:\tmp\gtos_otb\NOFILLUSDJPYSEQ",
        ],
        "verification_results": {
            "status": "PENDING_VERIFIER",
            "commands": [
                "python -m py_compile build_nofill_forward_lifecycle_capture_contract_2026_05_09.py verify_nofill_forward_lifecycle_capture_contract_2026_05_09.py",
                "python -B -m pytest test_nofill_forward_lifecycle_capture_contract_2026_05_09.py -q -p no:cacheprovider",
                "python verify_nofill_forward_lifecycle_capture_contract_2026_05_09.py",
            ],
        },
        "can_mark_goal_complete": False,
    }


def required_output_files() -> list[str]:
    return [
        "NOFILL_FORWARD_CONTEXT_ANCHOR_2026-05-09.md",
        "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.md",
        "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.json",
        "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json",
        "NOFILL_FORWARD_NO_LEAK_FIELD_POLICY_2026-05-09.md",
        "NOFILL_FORWARD_NO_LEAK_FIELD_POLICY_2026-05-09.json",
        "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_2026-05-09.md",
        "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_2026-05-09.json",
        "NOFILL_FORWARD_EXISTING_SOURCE_AND_CODE_AUDIT_2026-05-09.md",
        "NOFILL_FORWARD_EXISTING_SOURCE_AND_CODE_AUDIT_2026-05-09.json",
        "NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_2026-05-09.md",
        "NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_2026-05-09.json",
        "NOFILL_FORWARD_HOSTILE_EDGE_REVIEW_AND_SATURATION_2026-05-09.md",
        "NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md",
        "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md",
        "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.json",
    ]


def artifact_header(title: str) -> str:
    return (
        f"# {title}\n\n"
        f"- route_id: `{ROUTE_ID}`\n"
        f"- schema_version: `{SCHEMA_VERSION}`\n"
        f"- promotion_verdict: `{PROMOTION_VERDICT}`\n"
        "- validation_safe: `false`\n"
        "- outcome_review_opened: `false`\n"
        "- live_effect: `false`\n"
        "- opens_result_scoring: `false`\n"
        "- changes_live_trading_behavior: `false`\n"
    )


def build_context_anchor_md() -> str:
    inv = source_inventory()
    inputs = input_records()
    missing = [record["path"] for record in inputs if not record["exists"]]
    return artifact_header("NOFILL Forward Context Anchor 2026-05-09") + f"""
## Controlling State

This lane accepts the G0 no-fill CAT V3 synthesis as durable source/control context only. The frozen equation is:

`298 = 225 accepted input-only rows + 4 source-control rows + 4 source-impossible rows + 65 rejected rows`.

Primary denominators remain `225` row-level accepted inputs, `182` unique `nofill_duplicate_key` values, and `139` secondary `duplicate_group_id` values. The source-control rows are `{", ".join(SOURCE_CONTROL_ROWS)}`. The source-impossible rows are `{", ".join(SOURCE_IMPOSSIBLE_ROWS)}`.

## Prompt Path Reconciliation

The prompt listed `{STALE_PROMPT_PATH}`, but that path is absent in this worktree. The committed artifact used here is `{ACTUAL_G12_RESULT_AUDIT_PATH}`. This is a source-anchor correction, not a content rewrite.

## Source Inventory Snapshot

- Worktree `data/ticks`: exists={inv["worktree_data_ticks"]["exists"]}, count={inv["worktree_data_ticks"]["count"]}.
- External AI trading tick root: exists={inv["external_ai_trading_agent_tick_root"]["exists"]}, parquet_counts_by_symbol={inv["external_ai_trading_agent_tick_root"]["parquet_counts_by_symbol"]}.
- Sierra Chart `.scid`: exists={inv["sierra_chart_data_root"]["exists"]}, count={inv["sierra_chart_data_root"]["count"]}, market_depth_dir_exists={inv["sierra_chart_data_root"]["market_depth_dir_exists"]}.
- Prior USDJPY quote-sequence route in sibling worktree: exists={inv["prior_worktree_usdjpy_quote_sequence_route"]["exists"]}; current worktree route exists={inv["prior_worktree_usdjpy_quote_sequence_route"]["current_worktree_route_exists"]}.

## Missing Control Inputs

`{missing}`
"""


def build_contract_md() -> str:
    counts = "\n".join(f"- `{key}`: `{value}`" for key, value in EXPECTED_PARTITION.items())
    labels = "\n".join(f"- `{key}`: `{value}`" for key, value in PRIMARY_LABEL_COUNTS.items())
    families = "\n".join(f"- `{family}`: {', '.join(names)}" for family, names in sorted(FIELD_FAMILIES.items()))
    return artifact_header("NOFILL Forward Lifecycle Capture Contract 2026-05-09") + f"""
## Contract Boundary

This is a forward source-capture contract. It defines what must be captured before later no-fill review can be considered. It does not score outcomes, does not promote a signal, does not validate an edge, does not change live trading behavior, and does not open account/order-history routes.

## Frozen Counts

{counts}

Primary label counts carried as input/control vocabulary only:

{labels}

Opening-drive source projection remains `51` row-level inputs, of which `8` are primary accepted labels under the frozen G0 presentation. The `47` reject-overlap rows are neutralized by accepted-first filtering.

## Required Field Families

{families}

## Row Completion Rule

A row is contract-complete only when identity, pending intent, source coverage, touch/no-touch proof, event-order resolution, duplicate denominator controls, and no-leak guards are present. Missing source is not a failure to classify; it is a first-class blocker with `exact_next_source_if_unresolved`.
"""


def build_no_leak_md() -> str:
    forbidden = "\n".join(f"- `{name}`" for name in sorted(FORBIDDEN_SOURCE_FIELD_NAMES))
    allowed = "\n".join(f"- `{name}`" for name in ALLOWED_SOURCE_TYPES)
    return artifact_header("NOFILL Forward No-Leak Field Policy 2026-05-09") + f"""
## Allowed Source Classes

{allowed}

## Forbidden Substitutes

These names may appear in this document only as forbidden terms. They must not appear as accepted schema field names or source values:

{forbidden}

## Closed Labels

`future_result_label_status` must stay `NOT_OPENED`. `broker_actual_r_status`, `hidden_path_label_status`, and `live_account_order_label_status` must stay `FORBIDDEN`. The route fails if any artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.

## Raw Log Handling

Existing logs can contain useful source evidence and forbidden execution-shaped fields in the same row. Any future builder must use an allowlist projection. Raw `pending_limit_lifecycle`, `candidate_ltf_path_order`, or `strategy_follow_candidates` rows are not contract-safe inputs by themselves.
"""


def build_duplicate_md() -> str:
    rules = "\n".join(f"- {rule}" for rule in duplicate_policy_json()["rules"])
    return artifact_header("NOFILL Forward Duplicate Denominator Policy 2026-05-09") + f"""
## Denominators

- row-level accepted input denominator: `225`
- primary unique denominator: `182` `nofill_duplicate_key` values
- secondary denominator: `139` `duplicate_group_id` values

## Rules

{rules}

## Blocking Examples

Rows with generated/fallback duplicate keys, noncanonical projections, source-control state, source-impossible state, or reject-overlap state cannot enter any performance denominator. That is true even if the row has useful market-structure evidence.
"""


def build_source_audit_md() -> str:
    audit = source_audit_json()
    rows = []
    for record in audit["code_surface_audit"]:
        rows.append(
            f"### {record['surface']}\n\n"
            f"- status: `{record['status']}`\n"
            f"- source_value: {record['source_value']}\n"
            f"- contamination_risk: `{record['contamination_risk']}`\n"
            f"- contract_rule: {record['contract_rule']}\n"
        )
    return artifact_header("NOFILL Forward Existing Source And Code Audit 2026-05-09") + "\n" + "\n".join(rows)


def build_backlog_md() -> str:
    items = []
    for item in backlog_json()["backlog"]:
        items.append(
            f"{item['rank']}. `{item['item']}` ({item['priority']}) - {item['scope']}. "
            f"Done when: {item['done_definition']}. Approval needed: `{str(item['approval_needed']).lower()}`."
        )
    return artifact_header("NOFILL Forward Capture Backlog And Implementation Route 2026-05-09") + "\n## Backlog\n\n" + "\n".join(items) + """

## Forbidden Implementation Routes

No live trading prompts, no `src` trading behavior change, no risk/execution/permissions/safety gate edits, no canary edits, no MT5 account/order-history pull, no paid/API/Databento use, no credentials, no registry edits, no remote push, and no order behavior change are opened by this contract.
"""


def build_hostile_review_md() -> str:
    return artifact_header("NOFILL Forward Hostile Edge Review And Saturation 2026-05-09") + f"""
## Hostile Questions Answered

1. Could this be mistaken for result validation? No. The artifact carries `{PROMOTION_VERDICT}`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, and `opens_result_scoring=false` in JSON and markdown.
2. Could accepted counts leak rejected rows? The policy requires accepted-first filtering, neutralizes `{REJECT_OVERLAPS_NEUTRALIZED}` reject-overlap rows, and excludes source-control/source-impossible rows from result labels.
3. Could raw log fields leak account truth? Yes if consumed raw, so raw logs are explicitly unsafe. Only source-safe allowlist projections are allowed.
4. Could same-tick USDJPY rows be resolved by this contract? No. They stay source-impossible until a quote-event sequence source with sequence ID, exchange/broker event order, sub-ms timestamp, or sub-row ordering is obtained.
5. Could May 3 opening-drive rows be turned into performance evidence? No. They remain source-control/input-only unless a later source route proves coverage, and even then this contract opens no result scoring.
6. Is local heavy data enough for validation? No. Tick parquet and Sierra roots are source inventory only. They can populate coverage and event-order fields after hashing and parser verification.
7. Does this answer all same-evidence-class questions available locally? Yes for contract design, schema, no-leak rules, duplicate/as-of controls, source/code audit, backlog, and next prompts. It deliberately does not implement live logging or result scoring.
"""


def build_next_prompt_pack_md() -> str:
    return artifact_header("NOFILL Forward Next Prompt Pack 2026-05-09") + f"""
## Prompt 1 - G12 Audit

Run `G12_NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_AUDIT` against this folder. Audit the contract, schema, no-leak policy, duplicate/as-of controls, source/code audit, backlog, hostile review, tests, verifier, and completion audit. Preserve `{PROMOTION_VERDICT}`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, and do not open result scoring or live trading behavior.

## Prompt 2 - Source-Safe Projection Builder Plan

After G12 acceptance only, design an offline source-safe projection builder for already captured artifacts. It may read existing files and produce a manifest, but it must not edit live trading prompts/src logic, must not use MT5 account/order-history routes, and must fail closed on forbidden fields, missing hashes, unresolved event order, or generated duplicate keys.

## Prompt 3 - USDJPY Quote Event Sequence Source Access

Design a source-access route for `NOFILL-CAT-ROW-0130`, `NOFILL-CAT-ROW-0143`, `NOFILL-CAT-ROW-0165`, and `NOFILL-CAT-ROW-0178`. Required proof is bid/ask event ordering with sequence ID, sub-ms timestamp, or broker-native event sequence. Account/order labels and result scoring remain forbidden.
"""


def build_completion_md() -> str:
    return artifact_header("NOFILL Forward Completion Audit 2026-05-09") + """
## Status

`PENDING_VERIFIER` at build time. The verifier updates the JSON audit after py_compile, pytest, and contract verification pass.

## Delivered Files

""" + "\n".join(f"- `{name}`" for name in required_output_files())


def build_all() -> list[Path]:
    outputs: dict[str, str | dict[str, Any]] = {
        "NOFILL_FORWARD_CONTEXT_ANCHOR_2026-05-09.md": build_context_anchor_md(),
        "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.md": build_contract_md(),
        "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.json": contract_json(),
        "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json": schema_json(),
        "NOFILL_FORWARD_NO_LEAK_FIELD_POLICY_2026-05-09.md": build_no_leak_md(),
        "NOFILL_FORWARD_NO_LEAK_FIELD_POLICY_2026-05-09.json": no_leak_policy_json(),
        "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_2026-05-09.md": build_duplicate_md(),
        "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_2026-05-09.json": duplicate_policy_json(),
        "NOFILL_FORWARD_EXISTING_SOURCE_AND_CODE_AUDIT_2026-05-09.md": build_source_audit_md(),
        "NOFILL_FORWARD_EXISTING_SOURCE_AND_CODE_AUDIT_2026-05-09.json": source_audit_json(),
        "NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_2026-05-09.md": build_backlog_md(),
        "NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_2026-05-09.json": backlog_json(),
        "NOFILL_FORWARD_HOSTILE_EDGE_REVIEW_AND_SATURATION_2026-05-09.md": build_hostile_review_md(),
        "NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md": build_next_prompt_pack_md(),
        "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md": build_completion_md(),
        "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.json": completion_audit_json(),
    }
    written = []
    for name, content in outputs.items():
        path = ROUTE_DIR / name
        if isinstance(content, str):
            write_text(path, content)
        else:
            write_json(path, content)
        written.append(path)
    return written


def main() -> int:
    written = build_all()
    for path in written:
        print(rel(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
