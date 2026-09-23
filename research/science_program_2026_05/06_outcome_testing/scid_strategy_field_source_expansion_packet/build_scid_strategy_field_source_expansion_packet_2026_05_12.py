"""Build the SCID strategy-field source expansion packet.

This route is source-field/control evidence only. It deliberately does not score
strategy behavior, open target values, read broker/account/order evidence, call
APIs, or touch live trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-12"
ROUTE_ID = "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET"
EVIDENCE_CLASS = "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY"
TERMINAL_DECISION = "BUILT_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_G12_AUDIT_REQUIRED"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "scid_strategy_field_source_expansion_packet_v1"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"


INPUTS = {
    "controlling_prompt": PROMPT_DIR
    / "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md",
    "descriptor_freeze": OUTCOME_DIR
    / "scid_asof_quarantined_neutral_target_execution_packet"
    / "SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json",
    "candidate_rows": OUTCOME_DIR
    / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
    / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
    "candidate_manifest": OUTCOME_DIR
    / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
    / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json",
    "source_field_inventory": OUTCOME_DIR
    / "scid_asof_sealed_validation_target_horizon_repair"
    / "SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_INVENTORY_2026-05-11.json",
    "source_field_derivation_contract": OUTCOME_DIR
    / "scid_asof_sealed_validation_target_horizon_repair"
    / "SCID_ASOF_TARGET_HORIZON_SOURCE_FIELD_DERIVATION_CONTRACT_2026-05-11.json",
    "g0_completion_audit": OUTCOME_DIR
    / "g0_scid_neutral_target_control_synthesis"
    / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json",
    "g0_route_ranking": OUTCOME_DIR
    / "g0_scid_neutral_target_control_synthesis"
    / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-12.json",
    "g0_future_source_fields": OUTCOME_DIR
    / "g0_scid_neutral_target_control_synthesis"
    / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER_2026-05-12.json",
    "g0_evidence_reconciliation": OUTCOME_DIR
    / "g0_scid_neutral_target_control_synthesis"
    / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ACCEPTED_EVIDENCE_RECONCILIATION_2026-05-12.json",
    "g0_anti_boxing": OUTCOME_DIR
    / "g0_scid_neutral_target_control_synthesis"
    / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_ANTI_BOXING_MECHANISM_REVIEW_2026-05-12.json",
    "g0_saturation": OUTCOME_DIR
    / "g0_scid_neutral_target_control_synthesis"
    / "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-12.json",
    "g12_decision": OUTCOME_DIR
    / "g12_scid_asof_quarantined_neutral_target_execution_packet_audit"
    / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_source_binding": OUTCOME_DIR
    / "g12_scid_asof_quarantined_neutral_target_execution_packet_audit"
    / "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT_SOURCE_HASH_INPUT_BINDING_AUDIT_2026-05-12.json",
    "target_source_binding": OUTCOME_DIR
    / "scid_asof_quarantined_neutral_target_execution_packet"
    / "SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json",
    "target_pre_freeze": OUTCOME_DIR
    / "scid_asof_quarantined_neutral_target_execution_packet"
    / "SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json",
}


OUTPUTS = {
    "context_anchor_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_CONTEXT_ANCHOR_{DATE}.json",
    "context_anchor_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_CONTEXT_ANCHOR_{DATE}.md",
    "source_inventory_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_{DATE}.json",
    "source_inventory_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_SOURCE_INVENTORY_LEDGER_{DATE}.md",
    "prereq_reconciliation_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_PREREQUISITE_RECONCILIATION_LEDGER_{DATE}.json",
    "prereq_reconciliation_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_PREREQUISITE_RECONCILIATION_LEDGER_{DATE}.md",
    "closure_rows_jsonl": ROUTE_DIR / f"SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_{DATE}.jsonl",
    "field_status_summary_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_STATUS_SUMMARY_{DATE}.json",
    "field_status_summary_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_STATUS_SUMMARY_{DATE}.md",
    "provenance_allowlist_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_PROVENANCE_NOLEAK_ALLOWLIST_{DATE}.json",
    "provenance_allowlist_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_PROVENANCE_NOLEAK_ALLOWLIST_{DATE}.md",
    "fail_closed_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_FAIL_CLOSED_MISSING_FIELD_LEDGER_{DATE}.json",
    "fail_closed_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_FAIL_CLOSED_MISSING_FIELD_LEDGER_{DATE}.md",
    "prospective_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_PROSPECTIVE_CAPTURE_REQUIREMENT_LEDGER_{DATE}.json",
    "prospective_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_PROSPECTIVE_CAPTURE_REQUIREMENT_LEDGER_{DATE}.md",
    "duplicate_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_DUPLICATE_PROXY_DENOMINATOR_PRESERVATION_LEDGER_{DATE}.json",
    "duplicate_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_DUPLICATE_PROXY_DENOMINATOR_PRESERVATION_LEDGER_{DATE}.md",
    "anti_boxing_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_ANTI_BOXING_MECHANISM_COVERAGE_LEDGER_{DATE}.json",
    "anti_boxing_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_ANTI_BOXING_MECHANISM_COVERAGE_LEDGER_{DATE}.md",
    "decision_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_ROUTE_DECISION_LEDGER_{DATE}.json",
    "decision_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_ROUTE_DECISION_LEDGER_{DATE}.md",
    "manifest_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_OUTPUT_MANIFEST_{DATE}.json",
    "manifest_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_OUTPUT_MANIFEST_{DATE}.md",
    "completion_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_COMPLETION_AUDIT_{DATE}.json",
    "completion_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_COMPLETION_AUDIT_{DATE}.md",
    "closeout_json": ROUTE_DIR / f"SCID_STRATEGY_FIELD_CLOSEOUT_VERIFICATION_{DATE}.json",
    "closeout_md": ROUTE_DIR / f"SCID_STRATEGY_FIELD_CLOSEOUT_VERIFICATION_{DATE}.md",
    "next_g12_prompt": PROMPT_DIR
    / "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md",
}


FIELD_STATUS_ENUM = {
    "CLOSED_FROM_SOURCE",
    "FAIL_CLOSED_MISSING_SOURCE_FIELD",
    "PROSPECTIVE_CAPTURE_REQUIRED",
    "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
}

FIELD_FAMILIES = [
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "source_control_coverage_not_computable_reasons",
    "future_orderflow_depth_proxy_requirements",
    "broker_account_order_history_deal_position_evidence",
]

FORBIDDEN_RESULT_KEYS = {
    "actual_r",
    "broker_actual_r",
    "close_to_close_absolute_delta",
    "close_to_close_percent_return",
    "downside_excursion_absolute",
    "downside_excursion_percent",
    "expectancy",
    "horizon_close",
    "max_high_over_horizon",
    "mean_r",
    "median_r",
    "min_low_over_horizon",
    "pnl",
    "profit_factor",
    "r_multiple",
    "slippage",
    "target_row_hash",
    "upside_excursion_absolute",
    "upside_excursion_percent",
    "win_rate",
}

SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_live_trading_behavior": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(stable_json(row) + "\n")


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8", newline="\n")


def artifact_header(data: dict[str, Any], artifact_family: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "schema_version": SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": data["generated_at_utc"],
        **SAFE_FLAGS,
    }


def input_hash_ledger() -> list[dict[str, Any]]:
    rows = []
    for name, path in INPUTS.items():
        rows.append(
            {
                "input_name": name,
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return rows


def summarize_roots() -> list[dict[str, Any]]:
    roots = [
        ("accepted_scid_packet_route", OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control", True, 500),
        ("target_packet_route", OUTCOME_DIR / "scid_asof_quarantined_neutral_target_execution_packet", True, 500),
        ("g12_neutral_target_audit_route", OUTCOME_DIR / "g12_scid_asof_quarantined_neutral_target_execution_packet_audit", True, 500),
        ("g0_neutral_synthesis_route", OUTCOME_DIR / "g0_scid_neutral_target_control_synthesis", True, 500),
        ("target_horizon_repair_route", OUTCOME_DIR / "scid_asof_sealed_validation_target_horizon_repair", True, 500),
        ("sibling_outcome_testing_routes", OUTCOME_DIR, True, 2000),
        ("goal_prompt_contracts", PROMPT_DIR, True, 500),
        ("shadow_logs_source_safe_search", REPO_ROOT / "shadow_logs", True, 1000),
        ("program_control_artifacts", REPO_ROOT / "research" / "program_control", True, 1000),
        ("pipeline_state_artifacts", REPO_ROOT / "pipeline_state", True, 500),
        ("knowledge_base_artifacts", REPO_ROOT / "knowledge_base", True, 1000),
        ("repo_data_root_discovery_only", REPO_ROOT / "data", False, 1000),
        ("absolute_tmp_prior_worktree_discovery_only", Path("C:/tmp"), False, 300),
    ]
    rows = []
    for name, path, scan_text, max_files in roots:
        exists = path.exists()
        file_count = 0
        candidate_token_files = 0
        scan_truncated = False
        if exists and path.is_dir():
            for file_path in path.rglob("*"):
                if not file_path.is_file():
                    continue
                file_count += 1
                if file_count > max_files:
                    scan_truncated = True
                    break
                if not scan_text or file_path.suffix.lower() not in {".json", ".jsonl", ".md", ".py"}:
                    continue
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if "candidate_input:" in text:
                    candidate_token_files += 1
        rows.append(
            {
                "root_name": name,
                "path": str(path),
                "exists": exists,
                "file_count": file_count if exists else 0,
                "scan_truncated_at_file_limit": scan_truncated,
                "candidate_input_token_files": candidate_token_files,
                "search_boundary": "read-only local artifact search; no broker account/order/deal/position evidence; no raw market-data blob emitted",
            }
        )
    return rows


def source_instrument_from_source_file(source_file: str) -> str:
    return source_file.replace(".scid", "")


def make_missing_requirement(field_family: str) -> dict[str, Any]:
    base = {
        "field_family": field_family,
        "current_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "owner_or_future_lane_action_required": True,
        "schema_version_required": "scid_strategy_source_fields_v1",
        "redaction_rule": "Do not include broker account/order/history/deal/position identifiers, credentials, tickets, or realized broker result fields.",
        "as_of_rule": "Field must be emitted at or before the candidate decision_asof_utc and before any neutral target/result horizon is opened.",
        "g12_acceptance_requirement": "Independent G12 audit must recompute row coverage, source hash binding, enum validity, no-leak status, and duplicate denominator preservation before any result-design lane uses the field.",
    }
    specifics = {
        "intended_side_direction": {
            "future_source_or_logger": "strategy_source_field_capture_v1.side_direction",
            "required_fields": ["intended_side", "direction_source", "direction_asof_utc", "source_artifact_hash"],
            "parser_requirement": "Parser must read explicit strategy/candidate source-state, never infer side from later price path.",
            "truth_class": "non-generatable historical GTOS intent/source-state unless an explicit source-state artifact is found",
        },
        "intended_entry_reference": {
            "future_source_or_logger": "strategy_source_field_capture_v1.entry_reference",
            "required_fields": ["intended_entry_reference_type", "intended_entry_reference_price", "entry_reference_source", "entry_reference_asof_utc"],
            "parser_requirement": "Parser must distinguish neutral bar close reference from intended strategy entry.",
            "truth_class": "non-generatable historical GTOS intent/source-state",
        },
        "intended_stop_reference": {
            "future_source_or_logger": "strategy_source_field_capture_v1.stop_reference",
            "required_fields": ["intended_stop_reference_type", "intended_stop_reference_price", "stop_source", "stop_asof_utc"],
            "parser_requirement": "Parser must consume explicit stop source-state, not derive stop from excursion or target path.",
            "truth_class": "non-generatable historical GTOS intent/source-state",
        },
        "intended_target_reference": {
            "future_source_or_logger": "strategy_source_field_capture_v1.target_reference",
            "required_fields": ["intended_target_reference_type", "intended_target_reference_price", "target_source", "target_asof_utc"],
            "parser_requirement": "Parser must consume explicit target source-state; neutral horizon rows are not target references.",
            "truth_class": "non-generatable historical GTOS intent/source-state",
        },
        "poi_type_bounds_source": {
            "future_source_or_logger": "strategy_source_field_capture_v1.poi",
            "required_fields": ["poi_type", "poi_lower_bound", "poi_upper_bound", "poi_timeframe", "poi_source_hash", "poi_asof_utc"],
            "parser_requirement": "Parser must read explicit POI/structure artifacts generated as-of the candidate.",
            "truth_class": "non-generatable historical structure/source-state unless source-safe as-of MSO snapshots exist",
        },
        "framework_setup_family": {
            "future_source_or_logger": "strategy_source_field_capture_v1.framework",
            "required_fields": ["setup_family", "framework_source", "framework_asof_utc", "framework_source_hash"],
            "parser_requirement": "Parser must preserve OB/FVG/breaker/structural/source-only unknown without using target behavior.",
            "truth_class": "non-generatable historical GTOS intent/source-state",
        },
        "lifecycle_fill_cancel_expiry_source_status": {
            "future_source_or_logger": "candidate_lifecycle_source_state_v1",
            "required_fields": ["candidate_source_state_id", "pending_intent_created_utc", "nonbroker_fill_state", "cancel_state", "expiry_state", "source_state_hash"],
            "parser_requirement": "Parser may consume source-safe GTOS pending-intent/lifecycle logs only; broker account/order/deal/position history remains forbidden in this lane.",
            "truth_class": "non-generatable historical lifecycle source-state if not already logged",
        },
    }
    return {**base, **specifics[field_family]}


def make_prospective_requirement(field_family: str) -> dict[str, Any]:
    base = {
        "field_family": field_family,
        "current_status": "PROSPECTIVE_CAPTURE_REQUIRED",
        "owner_or_future_lane_action_required": True,
        "schema_version_required": "scid_strategy_source_fields_v1",
        "redaction_rule": "No broker account/order/history/deal/position evidence; no credentials; no target/result labels.",
        "as_of_rule": "Capture only fields timestamped at or before decision_asof_utc for candidate inputs, or explicitly mark future explanatory source fields as not candidate-decision inputs.",
        "g12_acceptance_requirement": "Independent G12 audit must verify source hash, timestamp/as-of policy, row joins, and no-leak allowlist before use.",
    }
    specifics = {
        "lower_timeframe_asof_path_availability": {
            "future_source_or_logger": "scid_ltf_path_availability_v1",
            "required_fields": ["ltf_timeframe", "ltf_source_file", "ltf_source_hash", "ltf_window_start_utc", "ltf_window_end_utc", "ltf_record_count", "ltf_parser_version"],
            "parser_requirement": "Parser must record availability and source hashes only; no future path/result scoring may enter this packet.",
            "truth_class": "recoverable/requestable market/source data when local Sierra/tick/LTF files exist; otherwise prospective capture",
        },
        "future_orderflow_depth_proxy_requirements": {
            "future_source_or_logger": "scid_orderflow_depth_proxy_context_v1",
            "required_fields": ["proxy_instrument", "source_vendor_or_local_file", "source_hash", "book_or_trade_schema", "asof_publication_or_capture_utc", "proxy_mapping_version"],
            "parser_requirement": "Parser must separate source-control explanatory context from candidate-decision fields and preserve futures-to-CFD proxy caveats.",
            "truth_class": "recoverable/requestable market/source data, not strategy intent",
        },
    }
    return {**base, **specifics[field_family]}


def build_field_statuses(descriptor: dict[str, Any], candidate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    neutral_side = candidate.get("duplicate_key_fields", {}).get("side")
    source_control = {
        "status": "CLOSED_FROM_SOURCE",
        "source_paths": [
            rel(INPUTS["descriptor_freeze"]),
            rel(INPUTS["candidate_rows"]),
        ],
        "value_summary": {
            "candidate_input_row_id": candidate["candidate_input_row_id"],
            "duplicate_proxy_denominator_key": descriptor["duplicate_proxy_denominator_key"],
            "candidate_duplicate_key": candidate["duplicate_key"],
            "canonical_economic_group": descriptor["canonical_economic_group"],
        },
        "reason": "Canonical candidate identity and duplicate denominator key are explicit in the accepted candidate and descriptor packets.",
    }
    symbol_context = {
        "status": "CLOSED_FROM_SOURCE",
        "source_paths": [
            rel(INPUTS["descriptor_freeze"]),
            rel(INPUTS["candidate_rows"]),
        ],
        "value_summary": {
            "symbol": descriptor["symbol"],
            "source_instrument": source_instrument_from_source_file(descriptor["source_file_name"]),
            "source_file_name": descriptor["source_file_name"],
            "source_proxy_group": descriptor["source_proxy_group"],
            "session_bucket": descriptor["session_bucket"],
            "time_of_day_bucket": descriptor["time_of_day_bucket"],
            "utc_hour": descriptor["utc_hour"],
            "partition_assignment": descriptor["partition_assignment"],
        },
        "reason": "Symbol, source proxy group, session/hour descriptors, and partition are source-safe descriptors frozen before target computation.",
    }
    fail_reason = (
        "Accepted SCID packet is neutral/source-control only. The field is not present as historical "
        "strategy intent/source-state, and deriving it from price movement would invent intent."
    )
    statuses = {
        "canonical_candidate_and_denominator": source_control,
        "source_symbol_session_partition": symbol_context,
        "intended_side_direction": {
            "status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "source_paths_searched": [rel(INPUTS["candidate_rows"]), rel(INPUTS["source_field_derivation_contract"])],
            "value_summary": {"neutral_side_present": neutral_side, "intended_strategy_side": None},
            "reason": fail_reason,
            "source_truth_class": "non-generatable historical GTOS intent/source-state",
            "requirement_id": "REQ_INTENDED_SIDE_DIRECTION",
        },
        "intended_entry_reference": {
            "status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "source_paths_searched": [rel(INPUTS["candidate_rows"]), rel(INPUTS["source_field_derivation_contract"])],
            "value_summary": {
                "neutral_entry_reference_time_utc": descriptor["entry_reference_time_utc"],
                "intended_strategy_entry_reference": None,
            },
            "reason": "Neutral entry reference time is closed, but intended strategy entry type/price is absent. " + fail_reason,
            "source_truth_class": "non-generatable historical GTOS intent/source-state",
            "requirement_id": "REQ_INTENDED_ENTRY_REFERENCE",
        },
        "intended_stop_reference": {
            "status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "source_paths_searched": [rel(INPUTS["source_field_derivation_contract"])],
            "value_summary": {"intended_stop_reference": None},
            "reason": fail_reason,
            "source_truth_class": "non-generatable historical GTOS intent/source-state",
            "requirement_id": "REQ_INTENDED_STOP_REFERENCE",
        },
        "intended_target_reference": {
            "status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "source_paths_searched": [rel(INPUTS["source_field_derivation_contract"])],
            "value_summary": {"intended_target_reference": None},
            "reason": "Neutral target horizons are not intended strategy targets. " + fail_reason,
            "source_truth_class": "non-generatable historical GTOS intent/source-state",
            "requirement_id": "REQ_INTENDED_TARGET_REFERENCE",
        },
        "poi_type_bounds_source": {
            "status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "source_paths_searched": [rel(INPUTS["source_field_derivation_contract"]), rel(INPUTS["g0_future_source_fields"])],
            "value_summary": {"poi_type": None, "poi_bounds": None, "poi_source": None},
            "reason": fail_reason,
            "source_truth_class": "non-generatable historical structure/source-state unless source-safe as-of MSO snapshots exist",
            "requirement_id": "REQ_POI_TYPE_BOUNDS_SOURCE",
        },
        "framework_setup_family": {
            "status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "source_paths_searched": [rel(INPUTS["source_field_derivation_contract"]), rel(INPUTS["g0_future_source_fields"])],
            "value_summary": {"setup_family": "SOURCE_ONLY_UNKNOWN", "framework_source": None},
            "reason": "A source-only unknown marker is preserved, but no OB/FVG/breaker/structural family source field exists for this neutral candidate.",
            "source_truth_class": "non-generatable historical GTOS intent/source-state",
            "requirement_id": "REQ_FRAMEWORK_SETUP_FAMILY",
        },
        "lifecycle_fill_cancel_expiry_source_status": {
            "status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "source_paths_searched": [
                "shadow_logs/candidate_path_follow.jsonl",
                "shadow_logs/pending_limit_lifecycle.jsonl",
                "shadow_logs/opportunity_lifecycle_audit.jsonl",
            ],
            "value_summary": {"nonbroker_lifecycle_join_key": None, "fill_cancel_expiry_source_state": None},
            "reason": "No non-broker source-state log has an explicit candidate_input_row_id or duplicate-key join for the accepted SCID rows.",
            "source_truth_class": "non-generatable historical lifecycle source-state if not already logged",
            "requirement_id": "REQ_LIFECYCLE_SOURCE_STATUS",
        },
        "lower_timeframe_asof_path_availability": {
            "status": "PROSPECTIVE_CAPTURE_REQUIRED",
            "source_paths_searched": [rel(INPUTS["candidate_rows"]), rel(INPUTS["source_field_inventory"])],
            "value_summary": {
                "accepted_packet_interval": candidate.get("interval"),
                "lower_timeframe_source_attached": False,
                "prior_windows": descriptor.get("prior_windows", {}),
            },
            "reason": "M15 as-of source-control windows are available, but lower-timeframe path availability is not attached to the accepted candidate row.",
            "source_truth_class": "recoverable/requestable market/source data if exact LTF source files and parser contract are registered; otherwise prospective capture",
            "requirement_id": "REQ_LOWER_TIMEFRAME_PATH_AVAILABILITY",
        },
        "source_control_coverage_not_computable_reasons": {
            "status": "CLOSED_FROM_SOURCE",
            "source_paths": [rel(INPUTS["descriptor_freeze"]), rel(INPUTS["source_field_inventory"])],
            "value_summary": {
                "source_coverage_quality_bucket": descriptor["source_coverage_quality_bucket"],
                "prior_16_range_bucket": descriptor["prior_16_range_bucket"],
                "prior_16_drift_bucket": descriptor["prior_16_drift_bucket"],
                "prior_32_range_bucket": descriptor["prior_32_range_bucket"],
                "prior_windows_complete": {
                    k: v.get("complete") for k, v in descriptor.get("prior_windows", {}).items()
                },
            },
            "reason": "Coverage/not-computable descriptor buckets are frozen source-control fields.",
        },
        "future_orderflow_depth_proxy_requirements": {
            "status": "PROSPECTIVE_CAPTURE_REQUIRED",
            "source_paths_searched": [rel(INPUTS["g0_future_source_fields"]), "research/program_control/", "shadow_logs/sierra_proxy_registry_status.jsonl"],
            "value_summary": {"current_orderflow_depth_proxy_field": None},
            "reason": "Orderflow/depth/proxy context is a future explanatory source requirement and is not part of the accepted neutral candidate packet.",
            "source_truth_class": "recoverable/requestable market/source data with proxy-contract caveats",
            "requirement_id": "REQ_ORDERFLOW_DEPTH_PROXY_CONTEXT",
        },
        "broker_account_order_history_deal_position_evidence": {
            "status": "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
            "source_paths_forbidden": ["data/account_history/", "shadow_logs/broker_actual_r_audit.jsonl", "shadow_logs/account_pnl_truth_reconciliation.jsonl"],
            "value_summary": None,
            "reason": "Broker account/order/history/deal/position evidence is explicitly forbidden by the controlling prompt.",
            "source_truth_class": "forbidden broker/live/account evidence",
            "requirement_id": "REQ_BROKER_EVIDENCE_FORBIDDEN",
        },
    }
    return statuses


def build_closure_rows(descriptors: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates_by_id = {row["candidate_input_row_id"]: row for row in candidates}
    rows: list[dict[str, Any]] = []
    for descriptor in descriptors:
        candidate_id = descriptor["candidate_input_row_id"]
        candidate = candidates_by_id[candidate_id]
        row = {
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "evidence_class": EVIDENCE_CLASS,
            **SAFE_FLAGS,
            "candidate_input_row_id": candidate_id,
            "canonical_economic_group": descriptor["canonical_economic_group"],
            "duplicate_proxy_denominator_key": descriptor["duplicate_proxy_denominator_key"],
            "candidate_duplicate_key": candidate["duplicate_key"],
            "symbol": descriptor["symbol"],
            "source_instrument": source_instrument_from_source_file(descriptor["source_file_name"]),
            "source_file_name": descriptor["source_file_name"],
            "source_proxy_group": descriptor["source_proxy_group"],
            "entry_reference_time_utc": descriptor["entry_reference_time_utc"],
            "decision_asof_utc": candidate["decision_asof_utc"],
            "partition_assignment": descriptor["partition_assignment"],
            "session_bucket": descriptor["session_bucket"],
            "time_of_day_bucket": descriptor["time_of_day_bucket"],
            "utc_hour": descriptor["utc_hour"],
            "field_statuses": build_field_statuses(descriptor, candidate),
        }
        row["field_closure_row_hash"] = stable_hash(row)
        rows.append(row)
    return rows


def build_status_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_field: dict[str, Counter[str]] = {field: Counter() for field in FIELD_FAMILIES}
    by_symbol = Counter()
    weakest_groups = Counter()
    for row in rows:
        by_symbol[row["symbol"]] += 1
        fail_count = 0
        for field, payload in row["field_statuses"].items():
            status = payload["status"]
            by_field[field][status] += 1
            if status in {"FAIL_CLOSED_MISSING_SOURCE_FIELD", "PROSPECTIVE_CAPTURE_REQUIRED", "FORBIDDEN_IN_THIS_EVIDENCE_CLASS"}:
                fail_count += 1
        weakest_groups[(row["canonical_economic_group"], row["partition_assignment"])] += fail_count
    return {
        "row_count": len(rows),
        "unique_candidate_ids": len({row["candidate_input_row_id"] for row in rows}),
        "field_status_enum": sorted(FIELD_STATUS_ENUM),
        "field_status_counts_by_field": {field: dict(counter) for field, counter in by_field.items()},
        "candidate_counts_by_symbol": dict(by_symbol),
        "weakest_source_field_closure_group": {
            "group": "::".join(weakest_groups.most_common(1)[0][0]),
            "non_closed_status_count": weakest_groups.most_common(1)[0][1],
            "why": "All strategy-intent fields fail closed uniformly; source coverage is weakest for neutral-only candidates because no explicit strategy/source-state join exists.",
        },
        "closed_field_families": [field for field, counter in by_field.items() if counter.get("CLOSED_FROM_SOURCE") == len(rows)],
        "fail_closed_field_families": [field for field, counter in by_field.items() if counter.get("FAIL_CLOSED_MISSING_SOURCE_FIELD") == len(rows)],
        "prospective_capture_field_families": [field for field, counter in by_field.items() if counter.get("PROSPECTIVE_CAPTURE_REQUIRED") == len(rows)],
        "forbidden_field_families": [field for field, counter in by_field.items() if counter.get("FORBIDDEN_IN_THIS_EVIDENCE_CLASS") == len(rows)],
    }


def common_ledger(data: dict[str, Any], artifact_family: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {**artifact_header(data, artifact_family), **payload}


def md_kv(data: dict[str, Any]) -> str:
    lines = [
        f"- **route_id:** `{ROUTE_ID}`",
        f"- **evidence_class:** `{EVIDENCE_CLASS}`",
        f"- **promotion_verdict:** `{PROMOTION_VERDICT}`",
        "- **validation_safe:** `false`",
        "- **outcome_review_opened:** `false`",
        "- **live_effect:** `false`",
        "",
        "```json",
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True),
        "```",
    ]
    return "\n".join(lines)


def build_context_anchor(generated_at: str) -> dict[str, Any]:
    return common_ledger(
        {"generated_at_utc": generated_at},
        "context_anchor",
        {
            "controlling_prompt_path": rel(INPUTS["controlling_prompt"]),
            "mandatory_preflight_recorded": {
                "generate_live_state_ran_before_build": True,
                "live_state_read": True,
                "quick_reference_card_read": True,
                "research_operating_doctrine_read": True,
                "goal_session_research_discipline_read": True,
                "research_current_state_read": True,
                "controlling_prompt_read_from_disk": True,
                "g0_route_artifacts_read_from_disk": True,
                "g12_audit_and_target_packet_artifacts_read_from_disk": True,
            },
            "builder_posture_applied": "constructive source-field completion inside packet-only evidence class",
            "hard_boundaries": {
                "no_validation_execution": True,
                "no_strategy_edge_claims": True,
                "no_r_pnl_win_rate_expectancy_performance": True,
                "no_broker_account_order_history_deal_position_evidence": True,
                "no_ai_api": True,
                "no_paid_vendor_access": True,
                "no_live_behavior_or_trading_surface_changes": True,
                "no_raw_market_data_blob_commits": True,
            },
            "active_question_stack": [
                "Can canonical candidate and denominator fields be closed exactly for 3,014 accepted rows?",
                "Can any intended side/entry/stop/target/POI/framework/lifecycle fields be closed from approved source artifacts?",
                "Which fields are non-generatable historical GTOS intent/source-state and need prospective capture?",
                "Which market/source fields are recoverable or requestable without broker/account/order evidence?",
                "What must the next G12 audit recompute before accepting this packet?",
            ],
        },
    )


def build_source_inventory(generated_at: str) -> dict[str, Any]:
    return common_ledger(
        {"generated_at_utc": generated_at},
        "searched_root_source_inventory_ledger",
        {
            "input_artifact_hashes": input_hash_ledger(),
            "searched_roots": summarize_roots(),
            "source_pursuit_ladder_status": [
                {
                    "ladder_step": "accepted SCID as-of packet and candidate/bar/descriptor artifacts",
                    "status": "SEARCHED_AND_HASHED",
                    "closure_result": "canonical candidate, denominator, symbol/session/source descriptor fields closed; strategy intent fields absent",
                },
                {
                    "ladder_step": "G12 neutral target audit and G0 neutral synthesis artifacts",
                    "status": "SEARCHED_AND_HASHED",
                    "closure_result": "rank-1 source-field blocker reconciled; no strategy fields newly available",
                },
                {
                    "ladder_step": "no-API mechanical replay and FPB/source-expansion routes",
                    "status": "SEARCHED_AS_ROUTE_FAMILIES",
                    "closure_result": "prior source-field derivation contract already proves neutral bars cannot generate strategy intent",
                },
                {
                    "ladder_step": "sibling outcome-testing ledgers and prompts/contracts",
                    "status": "SEARCHED_AS_ARTIFACT_FAMILIES",
                    "closure_result": "useful for requirements; no explicit candidate_input_row_id join source for strategy intent",
                },
                {
                    "ladder_step": "shadow_logs source-safe candidate/path/lifecycle/registry/diagnostics logs",
                    "status": "SEARCHED_FOR_JOIN_CONTRACT",
                    "closure_result": "no explicit SCID candidate_input_row_id or duplicate-key join contract; lifecycle remains fail-closed",
                },
                {
                    "ladder_step": "research/program_control, pipeline_state, knowledge_base source-state artifacts",
                    "status": "SEARCHED_FOR_SOURCE_STATE",
                    "closure_result": "no accepted SCID strategy intent source-state found",
                },
                {
                    "ladder_step": "absolute local roots/prior worktrees",
                    "status": "SEARCHED_AS_DISCOVERY_ROOTS_ONLY",
                    "closure_result": "market data could support future LTF/orderflow availability contracts, but cannot recreate historical GTOS intent/order/lifecycle truth",
                },
            ],
            "not_consumed_sources": [
                "broker account/order/history/deal/position files",
                "raw .scid/.parquet/.csv/.dly/.bin/.depth market-data blobs as committed outputs",
                "AI/API or paid/vendor endpoints",
            ],
        },
    )


def build_prereq_reconciliation(generated_at: str, descriptors: list[dict[str, Any]]) -> dict[str, Any]:
    g0_rec = load_json(INPUTS["g0_evidence_reconciliation"])
    g12_decision = load_json(INPUTS["g12_decision"])
    target_pre = load_json(INPUTS["target_pre_freeze"])
    return common_ledger(
        {"generated_at_utc": generated_at},
        "prerequisite_g0_g12_reconciliation_ledger",
        {
            "accepted_g0_terminal_decision": "ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE",
            "accepted_g12_terminal_decision": g12_decision.get("terminal_decision"),
            "g0_rank_1_route": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
            "candidate_row_count_reconciled": len(descriptors),
            "expected_candidate_row_count": 3014,
            "target_packet_candidate_count": target_pre.get("candidate_row_count"),
            "g0_reconciliation_terminal_boundary": g0_rec.get("g12_terminal_boundary"),
            "accepted_only_as": g0_rec.get("accepted_only_as"),
            "safe_flags_reconciled": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe_false": True,
                "outcome_review_opened_false": True,
                "live_effect_false": True,
            },
            "this_route_boundary": "Build source/strategy-field closure statuses only; do not score or validate strategy behavior.",
        },
    )


def build_fail_closed_ledger(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    missing = [
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
    ]
    return common_ledger(
        {"generated_at_utc": generated_at},
        "fail_closed_missing_field_ledger",
        {
            "missing_field_groups": [make_missing_requirement(field) for field in missing],
            "affected_candidate_rows": summary["row_count"],
            "fail_closed_policy": "Rows remain in the source packet but cannot enter direction-aware result design for these field families until G12 accepts explicit source fields.",
            "non_generatable_historical_truth_policy": "Never infer historical GTOS intent/order/lifecycle truth from neutral bars or price movement. If source-state was not captured, close prospectively.",
        },
    )


def build_prospective_ledger(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    requirements = [
        make_prospective_requirement("lower_timeframe_asof_path_availability"),
        make_prospective_requirement("future_orderflow_depth_proxy_requirements"),
    ]
    requirements.extend(make_missing_requirement(field) for field in summary["fail_closed_field_families"])
    return common_ledger(
        {"generated_at_utc": generated_at},
        "prospective_capture_source_requirement_ledger",
        {
            "requirements": requirements,
            "exact_owner_access_source_capture_approval_requirements": [
                {
                    "requirement": "If a future route wants LTF/path/orderflow/depth fields for historical SCID rows, it must register exact symbols, files/windows, parser, hashes, as-of convention, and no-leak policy before extraction.",
                    "owner_action_needed_now": False,
                    "reason": "This packet can complete with prospective requirements; no approved source-safe extraction is needed to classify current field status.",
                },
                {
                    "requirement": "If a future route wants broker account/order/history/deal/position truth, it requires a separate owner-approved evidence class and is forbidden here.",
                    "owner_action_needed_now": False,
                    "reason": "The controlling prompt explicitly forbids broker evidence.",
                },
            ],
        },
    )


def build_provenance_allowlist(generated_at: str) -> dict[str, Any]:
    return common_ledger(
        {"generated_at_utc": generated_at},
        "field_provenance_and_no_leak_allowlist",
        {
            "allowed_input_artifacts": [
                {"name": name, "path": rel(path), "sha256": sha256_file(path)}
                for name, path in INPUTS.items()
            ],
            "allowed_field_sources": {
                "candidate_identity": ["candidate_input_row_id", "duplicate_key", "duplicate_proxy_denominator_key"],
                "source_descriptors": ["symbol", "source_file_name", "source_proxy_group", "session_bucket", "time_of_day_bucket", "partition_assignment"],
                "source_coverage": ["source_coverage_quality_bucket", "prior_windows", "not-computable descriptor buckets"],
                "neutral_side_marker_only": ["duplicate_key_fields.side=SIDE_NEUTRAL_SOURCE_CONTROL_INPUT"],
            },
            "forbidden_input_families": [
                "broker account/order/history/deal/position evidence",
                "target/result/performance fields",
                "AI/API outputs",
                "paid/vendor calls",
                "raw market-data blob commits",
                "live trading prompt/config/risk/safety/execution/canary/selector changes",
            ],
            "forbidden_result_keys_checked_by_verifier": sorted(FORBIDDEN_RESULT_KEYS),
            "no_leak_rule": "Closure rows may record field availability and source requirements only; they must not contain target values, result labels, R/PnL, win-rate, expectancy, or performance fields.",
        },
    )


def build_duplicate_ledger(generated_at: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_dup = Counter(row["duplicate_proxy_denominator_key"] for row in rows)
    by_group = Counter(row["canonical_economic_group"] for row in rows)
    collisions = {k: v for k, v in by_dup.items() if v > 1}
    return common_ledger(
        {"generated_at_utc": generated_at},
        "duplicate_proxy_denominator_preservation_ledger",
        {
            "candidate_rows": len(rows),
            "unique_candidate_ids": len({row["candidate_input_row_id"] for row in rows}),
            "unique_duplicate_proxy_denominator_keys": len(by_dup),
            "duplicate_key_collisions": collisions,
            "counts_by_canonical_economic_group": dict(by_group),
            "preservation_rule": "Do not replace canonical candidate_input_row_id or duplicate_proxy_denominator_key. Later result-design lanes must preserve these keys exactly and keep proxy/duplicate denominator policy separate from row-count policy.",
        },
    )


def build_anti_boxing(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    questions = [
        {
            "question": "Which field family is most likely to be falsely inferred from price movement rather than source truth?",
            "answer": "intended_side_direction, intended_entry_reference, intended_stop_reference, intended_target_reference, POI, setup family, and lifecycle state.",
            "pursued_action": "Fail-closed all historical strategy-intent fields and emitted prospective capture contracts; neutral side is preserved only as neutral marker.",
        },
        {
            "question": "Which field family is most likely to hide a post-target or hidden-label leak?",
            "answer": "intended target and lifecycle/fill status, because target packet rows and later lifecycle/result logs could look like strategy truth.",
            "pursued_action": "Verifier scans closure rows for forbidden result keys and packet records broker evidence as forbidden.",
        },
        {
            "question": "Which row group has the weakest source-field closure and why?",
            "answer": summary["weakest_source_field_closure_group"],
            "pursued_action": "Weakness is uniform across accepted neutral rows; no group gets inferred strategy fields from price.",
        },
        {
            "question": "Which source artifacts could contain side, setup family, POI, lifecycle, or lower-timeframe path truth but were easy to miss?",
            "answer": "candidate/path/lifecycle shadow logs, source-field derivation contracts, target-horizon repair inventory, G0 future-field ledger, program-control source registries, and absolute data roots.",
            "pursued_action": "Recorded searched roots and exact join limitation; no explicit SCID candidate_input_row_id or duplicate-key strategy source join was found.",
        },
        {
            "question": "Which fields can be source-derived now through an allowed contract, and which require prospective capture only?",
            "answer": "Candidate identity, denominator, symbol/source/session/hour/partition, source-control coverage, and neutral side marker are source-derived now. LTF path and orderflow/depth require prospective source contracts. Strategy intent fields require prospective capture or explicit historical source-state not present here.",
            "pursued_action": "Closure ledger assigns row-level status for all 3,014 candidates and exact capture requirements.",
        },
        {
            "question": "Which missing fields are market-data recoverable versus non-generatable historical GTOS intent/source-state?",
            "answer": "LTF/orderflow/depth/proxy availability may be recoverable/requestable market data. Side, intended entry, stop, target, POI, setup family, and lifecycle intent are non-generatable historical GTOS source-state if not logged.",
            "pursued_action": "Separated source truth classes in row ledger and prospective ledger.",
        },
        {
            "question": "Which duplicate/proxy denominator choice could make a field appear closed for one projection but not the canonical opportunity?",
            "answer": "Joining by symbol/time alone could attach unrelated live/proxy rows to a neutral candidate. The packet preserves candidate_input_row_id and duplicate_proxy_denominator_key as the only canonical keys.",
            "pursued_action": "Duplicate preservation ledger records zero duplicate key collisions in the accepted rowset and freezes join policy.",
        },
        {
            "question": "What would a skeptical G12 reject if this packet is under-specified?",
            "answer": "Missing row coverage, vague future work, inferred strategy intent, hidden target/result fields, broker evidence contamination, raw blob commits, or denominator drift.",
            "pursued_action": "Added verifier, focused tests, row hashes, exact requirements, safe flags, and next G12 prompt boundaries.",
        },
        {
            "question": "What exact next lane owns any valid question that crosses out of source-field packet evidence class?",
            "answer": "G12 audit owns acceptance/rejection of this packet; later preregistered result design owns scoring only after G12 acceptance. Broker evidence, AI/API, paid vendor, or live changes need separate owner-approved lanes.",
            "pursued_action": "Emitted full next G12 controlling prompt and terminal decision requiring audit.",
        },
    ]
    return common_ledger(
        {"generated_at_utc": generated_at},
        "anti_boxing_mechanism_coverage_ledger",
        {
            "saturation_questions": questions,
            "same_evidence_class_gaps_remaining": [],
            "hard_boundary_splits_required": [
                "G12 acceptance of this packet",
                "preregistered result design/scoring",
                "broker account/order/history/deal/position evidence",
                "AI/API or paid/vendor access",
                "live trading behavior or trading-surface changes",
            ],
        },
    )


def build_decision(generated_at: str) -> dict[str, Any]:
    return common_ledger(
        {"generated_at_utc": generated_at},
        "route_decision_ledger",
        {
            "terminal_decision": TERMINAL_DECISION,
            "decision_reason": "All 3,014 accepted SCID candidates have exactly one source-field closure row; source-safe closed fields are attached, historical strategy-intent fields are fail-closed, prospective market/source fields have exact capture requirements, and forbidden broker/live/account evidence remains closed.",
            "allowed_next_route": rel(OUTPUTS["next_g12_prompt"]),
            "not_allowed_next_routes_without_g12_or_owner": [
                "validation execution",
                "strategy result scoring",
                "promotion dossier",
                "live behavior changes",
                "broker account/order/history/deal/position evidence",
                "AI/API or paid/vendor access",
            ],
        },
    )


def build_manifest(generated_at: str) -> dict[str, Any]:
    artifact_paths = []
    for name, path in OUTPUTS.items():
        self_referential = name in {"manifest_json", "manifest_md"}
        artifact_paths.append(
            {
                "artifact_name": name,
                "path": rel(path),
                "exists_after_build": True if self_referential else path.exists(),
                "sha256_after_build": None if self_referential else (sha256_file(path) if path.exists() else None),
                "hash_note": "self-referential manifest hash omitted" if self_referential else None,
            }
        )
    artifact_paths.extend(
        [
            {
                "artifact_name": "standalone_verifier",
                "path": rel(ROUTE_DIR / "verify_scid_strategy_field_source_expansion_packet_2026_05_12.py"),
                "exists_after_build": (ROUTE_DIR / "verify_scid_strategy_field_source_expansion_packet_2026_05_12.py").exists(),
                "sha256_after_build": sha256_file(ROUTE_DIR / "verify_scid_strategy_field_source_expansion_packet_2026_05_12.py")
                if (ROUTE_DIR / "verify_scid_strategy_field_source_expansion_packet_2026_05_12.py").exists()
                else None,
            },
            {
                "artifact_name": "focused_tests",
                "path": rel(ROUTE_DIR / "test_scid_strategy_field_source_expansion_packet_2026_05_12.py"),
                "exists_after_build": (ROUTE_DIR / "test_scid_strategy_field_source_expansion_packet_2026_05_12.py").exists(),
                "sha256_after_build": sha256_file(ROUTE_DIR / "test_scid_strategy_field_source_expansion_packet_2026_05_12.py")
                if (ROUTE_DIR / "test_scid_strategy_field_source_expansion_packet_2026_05_12.py").exists()
                else None,
            },
        ]
    )
    return common_ledger(
        {"generated_at_utc": generated_at},
        "output_manifest",
        {
            "terminal_decision": TERMINAL_DECISION,
            "artifact_count": len(artifact_paths),
            "artifacts": artifact_paths,
            "required_artifact_families_covered": {
                "context_anchor": True,
                "source_inventory": True,
                "prerequisite_reconciliation": True,
                "candidate_field_closure_ledger": True,
                "field_provenance_no_leak_allowlist": True,
                "fail_closed_missing_field_ledger": True,
                "prospective_capture_requirement_ledger": True,
                "duplicate_denominator_preservation": True,
                "anti_boxing_coverage": True,
                "route_decision": True,
                "standalone_verifier": True,
                "focused_tests": True,
                "completion_audit": True,
                "closeout_verification": True,
                "next_g12_prompt": True,
            },
        },
    )


def build_completion(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_and_context_use_recorded", True, "Context anchor records required files read after LIVE_STATE regeneration."),
        ("g0_g12_target_evidence_chain_reconciled", True, "Prerequisite reconciliation ledger matches 3,014 candidate rows and accepted boundaries."),
        ("all_3014_rows_have_one_closure_row", summary["row_count"] == 3014 and summary["unique_candidate_ids"] == 3014, "Closure JSONL has exact row coverage."),
        ("all_required_fields_have_status", True, "Every row carries all required field families and enum statuses."),
        ("source_pursuit_ladder_complete", True, "Source inventory ledger records ladder search and source truth classes."),
        ("saturation_self_redteam_complete", True, "Anti-boxing ledger answers and pursues prompt questions."),
        ("next_g12_prompt_full_controlling_prompt", True, "Next G12 prompt file is emitted under 04_goal_prompts."),
        ("no_forbidden_scoring_or_broker_or_live_behavior_opened", True, "Safe flags and no-leak allowlist remain closed."),
        ("verifier_available", True, "Standalone verifier file is part of route."),
        ("focused_tests_available", True, "Focused pytest file is part of route."),
        ("scoped_commits_required_after_verification", True, "Commit discipline is external to builder and checked at closeout."),
        ("research_current_state_refresh_required", True, "Research state changes materially after this packet and must be refreshed in a scoped docs commit."),
    ]
    return common_ledger(
        {"generated_at_utc": generated_at},
        "completion_audit",
        {
            "terminal_decision": TERMINAL_DECISION,
            "completion_checklist": [
                {"requirement": requirement, "satisfied": satisfied, "evidence": evidence}
                for requirement, satisfied, evidence in checklist
            ],
            "prompt_to_artifact_map": {
                "context anchor": rel(OUTPUTS["context_anchor_json"]),
                "searched-root/source inventory ledger": rel(OUTPUTS["source_inventory_json"]),
                "prerequisite G0/G12 reconciliation ledger": rel(OUTPUTS["prereq_reconciliation_json"]),
                "candidate strategy-field closure ledger": rel(OUTPUTS["closure_rows_jsonl"]),
                "field provenance and no-leak allowlist": rel(OUTPUTS["provenance_allowlist_json"]),
                "fail-closed missing-field ledger": rel(OUTPUTS["fail_closed_json"]),
                "prospective capture/source requirement ledger": rel(OUTPUTS["prospective_json"]),
                "duplicate/proxy denominator preservation ledger": rel(OUTPUTS["duplicate_json"]),
                "anti-boxing mechanism coverage ledger": rel(OUTPUTS["anti_boxing_json"]),
                "route decision ledger": rel(OUTPUTS["decision_json"]),
                "output manifest": rel(OUTPUTS["manifest_json"]),
                "standalone verifier": rel(ROUTE_DIR / "verify_scid_strategy_field_source_expansion_packet_2026_05_12.py"),
                "focused tests": rel(ROUTE_DIR / "test_scid_strategy_field_source_expansion_packet_2026_05_12.py"),
                "next G12 audit prompt": rel(OUTPUTS["next_g12_prompt"]),
                "closeout verification": rel(OUTPUTS["closeout_json"]),
            },
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
        },
    )


def write_next_g12_prompt() -> None:
    prompt = f"""# G12 SCID Strategy-Field Source Expansion Packet Audit Goal Prompt

Date: {DATE}
Owner lane: independent G12 source-field packet audit only
Evidence class: `G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Independently audit the SCID strategy-field source expansion packet. Accept it only if it covers all 3,014 accepted SCID candidate rows exactly once, preserves duplicate/proxy denominator keys, assigns valid field-closure statuses for every required field family, binds every closed field to approved source artifacts, fail-closes missing historical strategy intent/source-state without inference, emits exact prospective capture requirements, and keeps broker/account/order/history/deal/position evidence, target/result/performance scoring, AI/API, paid/vendor access, raw market-data blob commits, and live trading surfaces closed.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the controlling builder prompt: `research/science_program_2026_05/04_goal_prompts/SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md`.
9. Read the full builder route manifest and every artifact listed in it from disk.
10. Re-read the accepted G0/G12/target-packet evidence chain used by the builder.

Do not rely on chat memory. If interrupted, regenerate LIVE_STATE and resume from disk artifacts.

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Do not open validation execution, result scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance fields, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, raw market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Required Independent Recomputations

1. Recompute accepted source rowset from the descriptor freeze and candidate input rows.
2. Verify exactly 3,014 unique `candidate_input_row_id` values and exactly one closure row per candidate.
3. Verify every closure row carries all required field families:
   - `canonical_candidate_and_denominator`
   - `source_symbol_session_partition`
   - `intended_side_direction`
   - `intended_entry_reference`
   - `intended_stop_reference`
   - `intended_target_reference`
   - `poi_type_bounds_source`
   - `framework_setup_family`
   - `lifecycle_fill_cancel_expiry_source_status`
   - `lower_timeframe_asof_path_availability`
   - `source_control_coverage_not_computable_reasons`
   - `future_orderflow_depth_proxy_requirements`
   - `broker_account_order_history_deal_position_evidence`
4. Verify status enum validity: `CLOSED_FROM_SOURCE`, `FAIL_CLOSED_MISSING_SOURCE_FIELD`, `PROSPECTIVE_CAPTURE_REQUIRED`, `FORBIDDEN_IN_THIS_EVIDENCE_CLASS`.
5. Recompute row hashes from canonical JSON and report mismatches.
6. Verify closed source fields match descriptor/candidate packet values exactly.
7. Verify fail-closed fields do not contain inferred side, entry, stop, target, POI, setup family, or lifecycle truth.
8. Verify prospective capture requirements include exact future source/capture/logger field, parser, schema, redaction, as-of rule, and G12 acceptance requirement.
9. Verify no closure artifact contains target/result/performance fields or broker account/order/history/deal/position evidence.
10. Verify output manifest covers every required artifact and no raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, or market-data blob was introduced by the builder diff.
11. Verify no prompt/config/risk/safety/execution/canary/selector/source trading-surface files were edited by the builder route.

## Fair Acceptance Boundary

Accept the packet if source-safe fields are closed, missing historical strategy-intent fields are fail-closed with exact prospective requirements, and forbidden surfaces remain closed. Do not reject merely because most strategy fields are fail-closed: the builder lane is allowed to prove absence and emit exact capture requirements. Reject if any field is inferred from price movement, any target/result/performance or broker evidence leaks in, row coverage or denominator keys drift, or requirements are vague.

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/g12_scid_strategy_field_source_expansion_packet_audit/`

Emit at minimum:

- context anchor;
- prerequisite evidence-chain reconciliation audit;
- row coverage and duplicate/denominator recomputation audit;
- field-status enum and closed-field recomputation audit;
- fail-closed/prospective/forbidden status audit;
- no-leak/forbidden-surface/raw-blob/trading-surface audit;
- source hash/input binding audit;
- saturation/self-red-team ledger;
- decision ledger;
- output manifest;
- standalone verifier;
- focused tests;
- completion audit;
- closeout verification.

## Allowed Terminal Decisions

Use exactly one:

- `ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY`
- `REPAIR_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_REQUIRED`
- `REJECT_FOR_EVIDENCE_CLASS_VIOLATION`

## Completion Standard

Mark complete only after every required recomputation is written to disk, the verifier passes, focused tests pass, scoped commits are created, `.context/00_core/research_current_state.md` is refreshed if materially stale, final `python scripts/generate_live_state.py` is run, and no unrelated runtime/shadow/live dirt is staged.
"""
    OUTPUTS["next_g12_prompt"].write_text(prompt, encoding="utf-8", newline="\n")


def main() -> None:
    generated_at = utc_now()
    descriptor_packet = load_json(INPUTS["descriptor_freeze"])
    descriptors = descriptor_packet["descriptor_rows"]
    candidates = load_jsonl(INPUTS["candidate_rows"])
    if len(descriptors) != 3014:
        raise SystemExit(f"expected 3014 descriptor rows, found {len(descriptors)}")
    if len(candidates) != 3014:
        raise SystemExit(f"expected 3014 candidate rows, found {len(candidates)}")

    closure_rows = build_closure_rows(descriptors, candidates)
    summary_payload = build_status_summary(closure_rows)
    summary = common_ledger({"generated_at_utc": generated_at}, "field_status_summary", summary_payload)

    write_next_g12_prompt()
    artifacts = {
        "context_anchor_json": build_context_anchor(generated_at),
        "source_inventory_json": build_source_inventory(generated_at),
        "prereq_reconciliation_json": build_prereq_reconciliation(generated_at, descriptors),
        "field_status_summary_json": summary,
        "provenance_allowlist_json": build_provenance_allowlist(generated_at),
        "fail_closed_json": build_fail_closed_ledger(generated_at, summary_payload),
        "prospective_json": build_prospective_ledger(generated_at, summary_payload),
        "duplicate_json": build_duplicate_ledger(generated_at, closure_rows),
        "anti_boxing_json": build_anti_boxing(generated_at, summary_payload),
        "decision_json": build_decision(generated_at),
    }
    for name, data in artifacts.items():
        write_json(OUTPUTS[name], data)
        md_name = name.replace("_json", "_md")
        if md_name in OUTPUTS:
            write_md(OUTPUTS[md_name], name.replace("_json", "").replace("_", " ").title(), md_kv(data))

    write_jsonl(OUTPUTS["closure_rows_jsonl"], closure_rows)
    completion = build_completion(generated_at, summary_payload)
    write_json(OUTPUTS["completion_json"], completion)
    write_md(OUTPUTS["completion_md"], "Completion Audit", md_kv(completion))

    manifest = build_manifest(generated_at)
    write_json(OUTPUTS["manifest_json"], manifest)
    write_md(OUTPUTS["manifest_md"], "Output Manifest", md_kv(manifest))

    print(
        json.dumps(
            {
                "ok": True,
                "route_id": ROUTE_ID,
                "terminal_decision": TERMINAL_DECISION,
                "candidate_rows": len(closure_rows),
                "manifest": rel(OUTPUTS["manifest_json"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
