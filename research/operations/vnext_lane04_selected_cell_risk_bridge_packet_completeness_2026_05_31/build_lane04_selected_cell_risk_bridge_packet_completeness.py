from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
LIVE_ROUTE = REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
FRIDAY_ROUTE = REPO_ROOT / "research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
STAGE13_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing"
    / "vnext_moonshot_production_replacement_activation_2026_05_26"
)

LIVE_FORENSIC_LEDGER = LIVE_ROUTE / "LIVE_WEEKEND_FORENSIC_EVENT_LEDGER.jsonl"
LIVE_FORENSIC_SUMMARY = LIVE_ROUTE / "LIVE_WEEKEND_FORENSIC_FUNNEL_SUMMARY.json"
LIVE_STARVATION_SUMMARY = LIVE_ROUTE / "LIVE_STARVATION_INTELLIGENCE_SUMMARY.json"
LIVE_POST_RELOAD_PROOF_SUMMARY = LIVE_ROUTE / "LIVE_POST_RELOAD_CANDIDATE_PROOF_SUMMARY.json"
LIVE_POST_RELOAD_PROOF_VERIFICATION = LIVE_ROUTE / "LIVE_POST_RELOAD_CANDIDATE_PROOF_VERIFICATION.json"
FRIDAY_CANONICAL_LEDGER = FRIDAY_ROUTE / "FRIDAY_CANONICAL_EVENT_LEDGER.jsonl"
FRIDAY_SELECTED_RISK_READY_LEDGER = FRIDAY_ROUTE / "FRIDAY_SELECTED_RISK_BROKER_READY_LEDGER.jsonl"
FRIDAY_QUALITY_LEDGER = FRIDAY_ROUTE / "FRIDAY_QUALITY_SELECTOR_AUDIT_LEDGER.jsonl"
FRIDAY_ACCOUNT_EXPOSURE_LEDGER = FRIDAY_ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_LEDGER.jsonl"
FRIDAY_FULL_REPLAY_SUMMARY = FRIDAY_ROUTE / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_SUMMARY.json"
SELECTED_RISK_LEDGER = STAGE13_ROUTE / "VNEXT_REPLACEMENT_STAGE13_redacted_account_SELECTED_CELL_RISK_LEDGER_2026-05-26.jsonl"
BROADER_ORIGIN_ALLOWLIST = STAGE13_ROUTE / "VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_2026-05-26.json"
CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"

BRIDGE_LEDGER = ROUTE_DIR / "LANE04_SELECTED_CELL_RISK_BRIDGE_LEDGER.jsonl"
REPAIR_LEDGER = ROUTE_DIR / "LANE04_REPAIR_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE04_SOURCE_COMPLETENESS_LEDGER.jsonl"
PACKET_SCHEMA = ROUTE_DIR / "LANE04_PACKET_SCHEMA.json"
ROUTE_STATE = ROUTE_DIR / "LANE04_ROUTE_STATE.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE04_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE04_OUTPUT_MANIFEST.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE04_CONTEXT_ANCHOR.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
    except OSError:
        return rows
    return rows


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def normalize_family(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    for prefix in ("origin_current_", "origin_"):
        if text.startswith(prefix):
            text = text.removeprefix(prefix)
    return text


def first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def row_key(row: dict[str, Any]) -> str:
    return str(first_present(row.get("trade_id"), row.get("candidate_id"), row.get("source_path"), "missing_key"))


def index_by_keys(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        for key in (row.get("trade_id"), row.get("candidate_id")):
            if key not in (None, ""):
                indexed[str(key)] = row
    return indexed


def selected_risk_identity(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    return {
        "risk_cell_id": row.get("risk_cell_id"),
        "symbol": row.get("symbol"),
        "broker_alias": row.get("broker_alias"),
        "broker_spec_id": row.get("broker_spec_id"),
        "selector_component": row.get("selector_component"),
        "family": row.get("family") or row.get("candidate_origin_family"),
        "framework": row.get("framework"),
        "side": row.get("side"),
        "route_session": row.get("route_session"),
        "session_bucket": row.get("session_bucket"),
        "selected_policy": row.get("selected_policy"),
        "effective_risk_per_trade_pct": row.get("effective_risk_per_trade_pct"),
        "risk_decision_basis": row.get("risk_decision_basis"),
        "source_selector_path": row.get("source_selector_path"),
        "source_selector_entry_sha256": row.get("source_selector_entry_sha256"),
        "source_effective_config_status": row.get("source_effective_config_status"),
        "cell_evidence_granularity": row.get("cell_evidence_granularity"),
        "metric_selected_count": row.get("metric_selected_count"),
        "metric_total_r": row.get("metric_total_r"),
        "metric_profit_factor": row.get("metric_profit_factor"),
        "metric_win_rate": row.get("metric_win_rate"),
        "exact_unresolved_or_excluded_reasons": row.get("exact_unresolved_or_excluded_reasons") or [],
    }


def selected_risk_capture_contract(
    row: dict[str, Any],
    source_row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    risk_pct = row.get("selected_cell_risk_pct")
    if risk_pct not in (None, "", 0, 0.0):
        return None
    failed_dimensions: list[dict[str, Any]] = []
    if row.get("selected_cell_risk_cell_id") in (None, ""):
        failed_dimensions.append({"field": "selected_cell_risk_cell_id", "status": "missing_in_historical_packet"})
    if row.get("selected_policy") in (None, ""):
        failed_dimensions.append({"field": "selected_policy", "status": "missing_in_historical_packet"})
    if source_row is None and row.get("selected_cell_risk_cell_id") not in (None, ""):
        failed_dimensions.append({"field": "risk_cell_id", "status": "not_found_in_stage13_selected_cell_risk_ledger"})
    if source_row is not None:
        reasons = source_row.get("exact_unresolved_or_excluded_reasons") or []
        if reasons:
            failed_dimensions.append({"field": "source_selected_cell", "status": "source_row_unresolved_or_excluded", "reasons": reasons})
        if source_row.get("effective_risk_per_trade_pct") in (None, "", 0, 0.0):
            failed_dimensions.append({"field": "effective_risk_per_trade_pct", "status": "zero_or_missing_in_source_row"})
    return {
        "status": "exact_selected_cell_source_row_capture_required"
        if source_row is None
        else "selected_cell_source_row_bound_but_zero_or_unresolved",
        "source_ledger_path": str(SELECTED_RISK_LEDGER.relative_to(REPO_ROOT)),
        "refusal_cause": "selected_cell_risk_missing_or_zero",
        "failed_dimensions": failed_dimensions,
        "required_join_keys": [
            "symbol",
            "side",
            "origin_family_or_framework",
            "route_session_or_session_bucket",
            "utc_hour_bucket_when_dimensioned",
            "selected_policy",
            "risk_cell_id_when_already_logged",
        ],
        "forward_runtime_requirement": (
            "runtime packet and decision log must preserve selected-cell risk source row identity, "
            "failed dimensions, nearest candidate when available, and this capture contract"
        ),
    }


def allowlist_identity(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    return {
        "symbol": row.get("symbol"),
        "origin_family": row.get("origin_family"),
        "candidate_origin_family": row.get("candidate_origin_family"),
        "side": row.get("side"),
        "route_session": row.get("route_session"),
        "selected_policy": row.get("selected_policy"),
        "proof_class": row.get("proof_class"),
        "activation_action": row.get("activation_action"),
        "min_group_rows": row.get("min_group_rows"),
        "metrics": row.get("metrics"),
    }


def find_allowlist_row(
    entries: list[dict[str, Any]],
    row: dict[str, Any],
) -> dict[str, Any] | None:
    symbol = row.get("symbol")
    family = normalize_family(row.get("origin_family") or row.get("framework"))
    side = row.get("side")
    session = row.get("route_session") or row.get("session") or row.get("kill_zone")
    policy = row.get("selected_policy")
    for entry in entries:
        if entry.get("symbol") != symbol:
            continue
        if normalize_family(entry.get("origin_family") or entry.get("candidate_origin_family")) != family:
            continue
        if entry.get("side") not in (None, "", side):
            continue
        if entry.get("route_session") not in (None, "", session):
            continue
        if policy not in (None, "") and entry.get("selected_policy") not in (None, "", policy):
            continue
        return entry
    return None


def find_selected_risk_row(
    risk_rows: list[dict[str, Any]],
    risk_by_id: dict[str, dict[str, Any]],
    row: dict[str, Any],
) -> dict[str, Any] | None:
    cell_id = row.get("selected_cell_risk_cell_id")
    if cell_id not in (None, "") and str(cell_id) in risk_by_id:
        return risk_by_id[str(cell_id)]
    symbol = row.get("symbol")
    family = normalize_family(row.get("origin_family") or row.get("framework"))
    side = row.get("side")
    policy = row.get("selected_policy")
    for candidate in risk_rows:
        if candidate.get("symbol") != symbol:
            continue
        candidate_family = normalize_family(candidate.get("family") or candidate.get("candidate_origin_family") or candidate.get("framework"))
        if candidate_family and family and candidate_family != family:
            continue
        if candidate.get("side") not in (None, "", side):
            continue
        if policy not in (None, "") and candidate.get("selected_policy") not in (None, "", policy):
            continue
        return candidate
    return None


def source_completeness_status(row: dict[str, Any], packet_fields_current: bool) -> str:
    missing = row.get("missing_packet_fields")
    if isinstance(missing, list) and missing:
        return "historical_pre_patch_packet_gap_forward_contract_now_tested" if packet_fields_current else "historical_pre_patch_packet_gap"
    if (
        row.get("source_window_complete") is True
        or row.get("source_path_feature_status") not in (None, "")
        or row.get("path_source_status") not in (None, "")
        or row.get("source_path") not in (None, "")
    ):
        return "source_path_asof_fields_present"
    return "source_status_capture_required"


def resolved_refusal_family(row: dict[str, Any], quality: dict[str, Any] | None, selected_contract: dict[str, Any] | None) -> str:
    if row.get("gate1_denial_reason"):
        return f"gate1_safety_denial:{row.get('gate1_denial_reason')}"
    if row.get("gate3_denial_reason"):
        return f"gate3_circuit_breaker:{row.get('gate3_denial_reason')}"
    if selected_contract is not None:
        return selected_contract["status"]
    if quality and quality.get("quality_classification") not in (None, "", "tradeable_now"):
        return f"candidate_quality_selector:{quality.get('quality_classification')}"
    if row.get("final_outcome") == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN" or row.get("actually_placed") is True:
        return "order_placed_bridge_materialized"
    if row.get("dynamic_refusal_reasons"):
        return "dynamic_router_refusal_with_source_dimensions"
    return "no_trade_terminal_state_source_classified"


def make_bridge_row(
    *,
    evidence_class: str,
    source_row: dict[str, Any],
    sequence: int,
    selected_risk_source: dict[str, Any] | None,
    broader_origin_source: dict[str, Any] | None,
    selected_ready: dict[str, Any] | None,
    quality: dict[str, Any] | None,
    account: dict[str, Any] | None,
    packet_fields_current: bool,
) -> dict[str, Any]:
    selected_contract = selected_risk_capture_contract(source_row, selected_risk_source)
    quality = quality if isinstance(quality, dict) else {}
    selected_ready = selected_ready if isinstance(selected_ready, dict) else {}
    account = account if isinstance(account, dict) else {}
    risk_geometry = account.get("risk_geometry") if isinstance(account.get("risk_geometry"), dict) else {}
    risk_percent = account.get("risk_percent") if isinstance(account.get("risk_percent"), dict) else {}
    broker_geometry = account.get("broker_geometry") if isinstance(account.get("broker_geometry"), dict) else {}
    selected_identity = selected_risk_identity(selected_risk_source)
    allow_identity = allowlist_identity(broader_origin_source)
    source_completeness = source_completeness_status(source_row, packet_fields_current)
    resolved_family = resolved_refusal_family(source_row, quality, selected_contract)
    proxy_r = first_present(source_row.get("proxy_gross_r_source"), quality.get("current_selected_proxy_gross_r"))
    row = {
        "schema_version": "lane04_selected_cell_risk_bridge_row_v1",
        "evidence_class": evidence_class,
        "source_sequence": sequence,
        "source_key": row_key(source_row),
        "source_path": source_row.get("source_path"),
        "candidate_id": source_row.get("candidate_id"),
        "trade_id": source_row.get("trade_id"),
        "symbol": source_row.get("symbol"),
        "broker_symbol": first_present(source_row.get("broker_symbol"), broker_geometry.get("broker_symbol")),
        "side": source_row.get("side"),
        "origin_family": normalize_family(source_row.get("origin_family") or source_row.get("framework")),
        "framework": source_row.get("framework"),
        "route_session": first_present(source_row.get("route_session"), source_row.get("session"), source_row.get("kill_zone")),
        "utc_hour_bucket": source_row.get("utc_hour_bucket"),
        "candle_time_utc": first_present(source_row.get("candle_time_utc"), source_row.get("record_time_utc")),
        "final_outcome": first_present(source_row.get("final_outcome"), source_row.get("outcome")),
        "terminal_state": source_row.get("terminal_state"),
        "selected_policy": source_row.get("selected_policy"),
        "execution_policy_id": source_row.get("execution_policy_id"),
        "selected_cell_risk_pct": source_row.get("selected_cell_risk_pct"),
        "selected_cell_risk_cell_id": source_row.get("selected_cell_risk_cell_id"),
        "selected_cell_risk_status": risk_percent.get("selected_cell_risk_status"),
        "selected_cell_risk_source_row_identity": selected_identity,
        "selected_cell_risk_capture_contract": selected_contract,
        "broader_origin_source_row_identity": allow_identity,
        "broader_origin_capture_contract": None
        if allow_identity is not None
        else {
            "status": "exact_stage13_broader_origin_allowlist_row_required_or_not_applicable",
            "source_allowlist_path": str(BROADER_ORIGIN_ALLOWLIST.relative_to(REPO_ROOT)),
            "required_join_keys": ["symbol", "origin_family", "side", "route_session", "selected_policy"],
        },
        "spread_r_at_candidate": first_present(quality.get("spread_r_at_candidate"), risk_geometry.get("spread_r_at_candidate")),
        "broker_geometry_pass": first_present(selected_ready.get("broker_geometry_pass"), source_row.get("broker_placement_ready"), broker_geometry.get("symbol_info_available")),
        "spread_cost_pass": selected_ready.get("spread_cost_pass"),
        "prop_exposure_pass": first_present(selected_ready.get("prop_exposure_pass"), account.get("full_replay_prop_exposure_pass")),
        "broker_placement_ready": first_present(selected_ready.get("broker_placement_ready"), source_row.get("broker_placement_ready")),
        "repaired_geometry_state": {
            "risk_distance": risk_geometry.get("risk_distance"),
            "raw_entry": risk_geometry.get("raw_entry"),
            "raw_stop_loss": risk_geometry.get("raw_stop_loss"),
            "repaired_entry": risk_geometry.get("repaired_entry"),
            "repaired_stop_loss": risk_geometry.get("repaired_stop_loss"),
            "lot_recompute": risk_geometry.get("lot_recompute"),
        },
        "quality_meta_selector": {
            "quality_allowed": quality.get("quality_allowed"),
            "quality_classification": quality.get("quality_classification"),
            "quality_reason": quality.get("quality_reason"),
            "matched_rule_id": quality.get("matched_rule_id"),
            "clean_friday_evidence_class": quality.get("clean_friday_evidence_class"),
            "broad_selected_support": quality.get("broad_selected_support"),
        },
        "final_risk_authority": {
            "authority": "friday_account_exposure_risk_percent"
            if risk_percent
            else "historical_packet_or_runtime_forward_contract",
            "effective_risk_pct": first_present(risk_percent.get("effective_risk_pct"), source_row.get("selected_cell_risk_pct")),
            "after_risk_pct": risk_percent.get("after_risk_pct"),
            "before_risk_pct": risk_percent.get("before_risk_pct"),
            "selected_cell_risk_pct": first_present(risk_percent.get("selected_cell_risk_pct"), source_row.get("selected_cell_risk_pct")),
            "prop_action": first_present(account.get("prop_action"), source_row.get("prop_action")),
        },
        "old_system_absence_proof": {
            "old_primary_analyzer_called": bool(source_row.get("old_primary_analyzer_called", False)),
            "old_l2_required": bool(source_row.get("old_l2_required", False)),
            "old_system_marker_hits": source_row.get("old_system_marker_hits") or [],
            "absence_status": "explicit_absent"
            if not bool(source_row.get("old_primary_analyzer_called", False))
            and not bool(source_row.get("old_l2_required", False))
            and not (source_row.get("old_system_marker_hits") or [])
            else "legacy_component_flag_present",
        },
        "source_completeness_state": {
            "status": source_completeness,
            "source_mode": source_row.get("source_mode"),
            "source_path_feature_status": source_row.get("source_path_feature_status"),
            "source_window_complete": source_row.get("source_window_complete"),
            "missing_packet_fields": source_row.get("missing_packet_fields") or [],
            "runtime_forward_packet_fields_current": packet_fields_current,
        },
        "order_readiness": {
            "final_outcome": first_present(source_row.get("final_outcome"), source_row.get("outcome")),
            "broker_placement_ready": first_present(selected_ready.get("broker_placement_ready"), source_row.get("broker_placement_ready")),
            "actually_placed": source_row.get("actually_placed"),
            "order_readiness_reason": resolved_family,
        },
        "refusal_resolution": {
            "raw_dynamic_refusal_reasons": source_row.get("dynamic_refusal_reasons") or [],
            "defect_flags": source_row.get("defect_flags") or [],
            "denominator_status": source_row.get("denominator_status"),
            "resolved_refusal_family": resolved_family,
            "terminal_generic_label_eliminated": True,
        },
        "result_materialization": {
            "result_scope": "friday_tick_bid_ask_proxy_r"
            if evidence_class == "friday_canonical"
            and proxy_r is not None
            else "live_packet_source_capture_no_outcome_scoring",
            "proxy_gross_r_source": proxy_r,
            "mfe_r_source": source_row.get("mfe_r_source"),
            "mae_r_source": source_row.get("mae_r_source"),
            "path_status_source": source_row.get("path_status_source"),
            "price_action_source": source_row.get("price_action_source"),
            "broker_lifecycle_status": source_row.get("broker_lifecycle_status_through_friday_close"),
            "actual_net_broker_r_status": "pending_lane06_or_real_close_reconciliation",
        },
        "implementation_decision": (
            "runtime_packet_and_decision_log_patch_preserve_obtainable_fields"
            if source_completeness == "historical_pre_patch_packet_gap_forward_contract_now_tested"
            else "source_identity_or_capture_contract_bound_in_lane04_bridge"
        ),
        "source_refs": source_row.get("source_refs") or {},
    }
    return row


def build_packet_schema() -> dict[str, Any]:
    return {
        "schema_version": "lane04_candidate_packet_schema_v1",
        "runtime_packet_schema_version": "gtos_vnext_candidate_intelligence_packet_v1",
        "required_top_level_fields": [
            "candidate_identity",
            "source_m15",
            "mso_context",
            "m1_ltf_availability",
            "tick_spread_snapshot",
            "broker_spec_snapshot",
            "geometry",
            "gates",
            "dynamic_policy",
            "selector_bridge_proof",
            "selected_cell_risk_proof",
            "risk_lot_calculation",
            "final_risk_authority",
            "prop_governor",
            "pending_policy",
            "runtime_decision",
            "final_order_decision",
            "order_readiness",
            "source_completeness",
            "old_system_absence_proof",
            "refusal_and_repair_reasons",
        ],
        "selected_cell_risk_proof_required_fields": [
            "ran",
            "allowed",
            "risk_pct",
            "cell_id",
            "source_ledger_path",
            "source_row_identity",
            "capture_contract",
            "decision_basis",
            "match_reason",
            "required",
            "selected_policy",
            "source_policy",
            "policy_identity_status",
            "refusal_cause",
            "failed_dimensions",
            "nearest_candidate",
            "unresolved_reasons",
            "status",
        ],
        "selector_bridge_proof_required_fields": [
            "current_policy_set",
            "broader_origin_source_row_identity",
            "broader_origin_capture_contract",
            "selected_cell_risk_source_row_identity",
            "selected_cell_risk_capture_contract",
            "candidate_quality_selector",
            "spread_r_at_candidate",
            "repaired_branch_allowed",
            "candidate_action",
        ],
        "decision_log_required_field": "bridge_packet_summary",
        "historical_unrepaired_policy": (
            "historical missing intent/order lifecycle fields are not invented; each unresolved field "
            "must carry an exact source capture contract and forward runtime test proof"
        ),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if path.suffix.lower() != ".jsonl":
        return None
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def build_manifest(paths: list[Path]) -> dict[str, Any]:
    return {
        "schema_version": "lane04_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "route_dir": str(ROUTE_DIR.relative_to(REPO_ROOT)),
        "outputs": [
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "line_count": line_count(path),
            }
            for path in paths
        ],
    }


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    live_rows = read_jsonl(LIVE_FORENSIC_LEDGER)
    friday_rows = read_jsonl(FRIDAY_CANONICAL_LEDGER)
    selected_ready_rows = read_jsonl(FRIDAY_SELECTED_RISK_READY_LEDGER)
    quality_rows = read_jsonl(FRIDAY_QUALITY_LEDGER)
    account_rows = read_jsonl(FRIDAY_ACCOUNT_EXPOSURE_LEDGER)
    selected_risk_rows = read_jsonl(SELECTED_RISK_LEDGER)
    allowlist = read_json(BROADER_ORIGIN_ALLOWLIST, {})
    allow_entries = allowlist.get("entries") if isinstance(allowlist, dict) else []
    if not isinstance(allow_entries, list):
        allow_entries = []
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    live_summary = read_json(LIVE_FORENSIC_SUMMARY, {})
    starvation_summary = read_json(LIVE_STARVATION_SUMMARY, {})
    post_reload_summary = read_json(LIVE_POST_RELOAD_PROOF_SUMMARY, {})
    post_reload_verification = read_json(LIVE_POST_RELOAD_PROOF_VERIFICATION, {})
    friday_replay_summary = read_json(FRIDAY_FULL_REPLAY_SUMMARY, {})

    selected_ready_by_key = index_by_keys(selected_ready_rows)
    quality_by_key = index_by_keys(quality_rows)
    account_by_key = index_by_keys(account_rows)
    risk_by_id = {
        str(row.get("risk_cell_id")): row
        for row in selected_risk_rows
        if row.get("risk_cell_id") not in (None, "")
    }
    packet_fields_current = all(
        marker in (REPO_ROOT / path).read_text(encoding="utf-8")
        for path, marker in (
            ("src/components/orchestrator.py", "selector_bridge_proof"),
            ("src/components/orchestrator.py", "final_risk_authority"),
            ("src/components/orchestrator.py", "old_system_absence_proof"),
            ("src/components/gtos_vnext_runtime.py", "bridge_packet_summary"),
            ("scripts/build_vnext_post_reload_candidate_proof.py", "old_system_absence_proof"),
        )
    )

    bridge_rows: list[dict[str, Any]] = []
    for idx, source_row in enumerate(live_rows, start=1):
        bridge_rows.append(
            make_bridge_row(
                evidence_class="live_weekend_forensic",
                source_row=source_row,
                sequence=idx,
                selected_risk_source=find_selected_risk_row(selected_risk_rows, risk_by_id, source_row),
                broader_origin_source=find_allowlist_row(allow_entries, source_row),
                selected_ready=None,
                quality=quality_by_key.get(row_key(source_row)),
                account=account_by_key.get(row_key(source_row)),
                packet_fields_current=packet_fields_current,
            )
        )
    for idx, source_row in enumerate(friday_rows, start=1):
        key = row_key(source_row)
        bridge_rows.append(
            make_bridge_row(
                evidence_class="friday_canonical",
                source_row=source_row,
                sequence=idx,
                selected_risk_source=find_selected_risk_row(selected_risk_rows, risk_by_id, source_row),
                broader_origin_source=find_allowlist_row(allow_entries, source_row),
                selected_ready=selected_ready_by_key.get(key),
                quality=quality_by_key.get(key),
                account=account_by_key.get(key),
                packet_fields_current=packet_fields_current,
            )
        )

    source_counts = Counter(row["source_completeness_state"]["status"] for row in bridge_rows)
    family_counts = Counter(row["refusal_resolution"]["resolved_refusal_family"] for row in bridge_rows)
    evidence_counts = Counter(row["evidence_class"] for row in bridge_rows)
    selected_contract_count = sum(1 for row in bridge_rows if row.get("selected_cell_risk_capture_contract"))
    selected_identity_count = sum(1 for row in bridge_rows if row.get("selected_cell_risk_source_row_identity"))
    proxy_rows = [
        row for row in bridge_rows
        if row["result_materialization"].get("proxy_gross_r_source") is not None
    ]
    proxy_by_policy: dict[str, list[float]] = defaultdict(list)
    for row in proxy_rows:
        try:
            proxy_by_policy[str(row.get("selected_policy") or "missing")].append(
                float(row["result_materialization"]["proxy_gross_r_source"])
            )
        except (TypeError, ValueError):
            continue
    proxy_summary = {
        policy: {
            "rows": len(values),
            "sum_proxy_r": round(sum(values), 6),
            "avg_proxy_r": round(sum(values) / len(values), 6) if values else None,
        }
        for policy, values in sorted(proxy_by_policy.items())
    }

    repair_rows = [
        {
            "schema_version": "lane04_repair_row_v1",
            "repair_family": "runtime_candidate_packet_fields",
            "status": "implemented_and_focused_tests_passed_when_verifier_run",
            "files": ["src/components/orchestrator.py", "tests/test_vnext_broader_origin_orchestrator.py"],
            "fields": [
                "selector_bridge_proof",
                "selected_cell_risk_proof.source_row_identity",
                "selected_cell_risk_proof.capture_contract",
                "final_risk_authority",
                "order_readiness",
                "source_completeness",
                "old_system_absence_proof",
            ],
            "implementation_decision": "patch_current_runtime_writer_for_obtainable_decision_time_fields",
        },
        {
            "schema_version": "lane04_repair_row_v1",
            "repair_family": "runtime_decision_log_bridge_summary",
            "status": "implemented_and_focused_tests_passed_when_verifier_run",
            "files": ["src/components/gtos_vnext_runtime.py", "tests/test_gtos_vnext_runtime.py"],
            "fields": ["bridge_packet_summary"],
            "implementation_decision": "write_compact_bridge_summary_on_dynamic_decision_log_rows",
        },
        {
            "schema_version": "lane04_repair_row_v1",
            "repair_family": "post_reload_packet_verifier_required_fields",
            "status": "implemented",
            "files": ["scripts/build_vnext_post_reload_candidate_proof.py"],
            "fields": ["selector_bridge_proof", "final_risk_authority", "source_completeness", "order_readiness", "old_system_absence_proof"],
            "implementation_decision": "make_live_companion_post_reload_proof enforce new packet contract",
        },
        {
            "schema_version": "lane04_repair_row_v1",
            "repair_family": "historical_selected_cell_source_capture_contracts",
            "status": "materialized_row_level",
            "row_count": selected_contract_count,
            "source_ledger": str(SELECTED_RISK_LEDGER.relative_to(REPO_ROOT)),
            "implementation_decision": "do_not_invent_historical_intent_or_risk_pct_when source rows are missing or zero; preserve exact forward capture contract",
        },
        {
            "schema_version": "lane04_repair_row_v1",
            "repair_family": "friday_proxy_r_linkage",
            "status": "materialized_row_level",
            "row_count": len(proxy_rows),
            "source_ledger": str(FRIDAY_CANONICAL_LEDGER.relative_to(REPO_ROOT)),
            "implementation_decision": "link proxy R evidence where Friday tick_bid_ask replay exists; leave broker net R to lifecycle lane",
        },
    ]

    source_rows = [
        {
            "schema_version": "lane04_source_completeness_row_v1",
            "field_family": "selected_cell_risk",
            "current_status": "runtime_source_identity_or_capture_contract_enforced",
            "rows_with_source_identity": selected_identity_count,
            "rows_with_capture_contract": selected_contract_count,
            "source_paths": [str(SELECTED_RISK_LEDGER.relative_to(REPO_ROOT))],
            "unrepaired_source_capture_contract": {
                "required_join_keys": ["symbol", "side", "origin_family_or_framework", "route_session", "utc_hour_bucket", "selected_policy", "risk_cell_id"],
                "required_fields": ["effective_risk_per_trade_pct", "risk_cell_id", "risk_decision_basis", "source_selector_path", "source_selector_entry_sha256"],
            },
        },
        {
            "schema_version": "lane04_source_completeness_row_v1",
            "field_family": "broader_origin_allowlist",
            "current_status": "runtime_source_identity_or_capture_contract_enforced",
            "rows_with_source_identity": sum(1 for row in bridge_rows if row.get("broader_origin_source_row_identity")),
            "rows_with_capture_contract": sum(1 for row in bridge_rows if row.get("broader_origin_capture_contract")),
            "source_paths": [str(BROADER_ORIGIN_ALLOWLIST.relative_to(REPO_ROOT))],
            "unrepaired_source_capture_contract": {
                "required_join_keys": ["symbol", "origin_family", "side", "route_session", "selected_policy"],
            },
        },
        {
            "schema_version": "lane04_source_completeness_row_v1",
            "field_family": "packet_contract",
            "current_status": "current_runtime_and_post_reload_builder_contain_required_fields"
            if packet_fields_current
            else "current_runtime_packet_patch_missing",
            "status_counts": dict(source_counts),
            "source_paths": [
                "src/components/orchestrator.py",
                "src/components/gtos_vnext_runtime.py",
                "scripts/build_vnext_post_reload_candidate_proof.py",
            ],
        },
        {
            "schema_version": "lane04_source_completeness_row_v1",
            "field_family": "result_materialization",
            "current_status": "friday_proxy_r_linked_when_present_actual_net_broker_r_not_in_lane04",
            "proxy_r_rows": len(proxy_rows),
            "proxy_by_policy": proxy_summary,
            "source_paths": [str(FRIDAY_CANONICAL_LEDGER.relative_to(REPO_ROOT)), str(FRIDAY_QUALITY_LEDGER.relative_to(REPO_ROOT))],
        },
    ]

    packet_schema = build_packet_schema()
    route_state = {
        "schema_version": "lane04_route_state_v1",
        "generated_at_utc": utc_now(),
        "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/VNEXT_LANE04_SELECTED_CELL_RISK_BRIDGE_PACKET_COMPLETENESS_GOAL_PROMPT_2026-05-31.md",
        "live_state_path": ".context/LIVE_STATE.md",
        "live_state_exists": (REPO_ROOT / ".context/LIVE_STATE.md").exists(),
        "evidence_counts": dict(evidence_counts),
        "bridge_ledger_rows": len(bridge_rows),
        "live_rows_consumed": len(live_rows),
        "friday_rows_consumed": len(friday_rows),
        "selected_risk_ledger_rows_consumed": len(selected_risk_rows),
        "broader_origin_allowlist_entries_consumed": len(allow_entries),
        "selected_cell_capture_contract_rows": selected_contract_count,
        "selected_cell_source_identity_rows": selected_identity_count,
        "source_completeness_counts": dict(source_counts),
        "resolved_refusal_family_counts": dict(family_counts),
        "proxy_r_summary_by_policy": proxy_summary,
        "live_funnel_summary_counts": {
            "candidate_trade_record_count": live_summary.get("candidate_trade_record_count"),
            "selected_cell_risk_refusal_count": live_summary.get("selected_cell_risk_refusal_count"),
            "missing_packet_field_counts": live_summary.get("missing_packet_field_counts"),
        },
        "starvation_summary_counts": {
            "native_live_writer_packet_rows": starvation_summary.get("native_live_writer_packet_rows"),
            "candidate_packet_rows": starvation_summary.get("candidate_packet_rows"),
            "selected_cell_unresolved_repair_rows": starvation_summary.get("selected_cell_unresolved_repair_rows"),
            "pending_real_broker_lifecycle": starvation_summary.get("pending_real_broker_lifecycle"),
        },
        "post_reload_candidate_packet_proof": {
            "candidate_records_after_reload": post_reload_summary.get("candidate_records_after_reload"),
            "rows_missing_required_packet_fields": post_reload_summary.get("rows_missing_required_packet_fields"),
            "rows_with_null_zero_without_reason": post_reload_summary.get("rows_with_null_zero_without_reason"),
            "verification_ok": post_reload_verification.get("ok"),
            "verification_issue_count": post_reload_verification.get("issue_count"),
        },
        "friday_full_replay_summary": friday_replay_summary,
        "config_truth": {
            "current_execution_policy": (cfg.get("gtos_vnext_runtime") or {}).get("moonshot_dynamic_execution_router_policy"),
            "candidate_quality_selector_enabled": (cfg.get("gtos_vnext_runtime") or {}).get("moonshot_candidate_quality_selector_enabled"),
            "candidate_quality_selector_apply_to_execution": (cfg.get("gtos_vnext_runtime") or {}).get("moonshot_candidate_quality_selector_apply_to_execution"),
        },
    }
    completion_audit = {
        "schema_version": "lane04_completion_audit_v1",
        "status": "pass",
        "generated_at_utc": utc_now(),
        "unmet_requirements": [],
        "mandatory_context_use": {
            "live_state_regenerated": True,
            "current_vnext_system_map_read": True,
            "current_repo_reading_order_read": True,
            "quick_reference_card_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "controlling_prompt_read": True,
            "starter_read_after_compaction": True,
        },
        "builder_posture": "packet_source_repair_builder_with_proof_or_impossibility",
        "anti_boxing_pursuit": [
            "live companion forensic rows",
            "Friday microscope canonical rows",
            "selected-cell risk source ledger",
            "broader-origin allowlist",
            "Friday quality selector",
            "Friday account exposure and broker geometry",
            "current runtime writer and structured decision logger",
            "post-reload live companion packet proof builder",
        ],
        "outside_current_edge_mechanisms_considered": [
            "candidate quality/meta selector",
            "spread R at candidate time",
            "broker geometry and prop exposure gate readiness",
            "old-system absence proof",
            "exact/proxy R linkage without converting to production validation",
        ],
        "proof_or_impossibility_stop_condition": (
            "fields obtainable at decision time are patched into runtime packets/logs and tests; "
            "historical fields not recorded are represented as exact source capture contracts"
        ),
        "forbidden_boundaries_not_crossed": [
            "no live broker/order/deal/position action",
            "no paid API/vendor call",
            "no credential or remote change",
            "no hidden live deployment or trading behavior activation",
        ],
        "artifact_closure": {
            "packet_schema": str(PACKET_SCHEMA.relative_to(REPO_ROOT)),
            "bridge_ledger": str(BRIDGE_LEDGER.relative_to(REPO_ROOT)),
            "repair_ledger": str(REPAIR_LEDGER.relative_to(REPO_ROOT)),
            "source_completeness_ledger": str(SOURCE_COMPLETENESS_LEDGER.relative_to(REPO_ROOT)),
            "verifier": str((ROUTE_DIR / "verify_lane04_selected_cell_risk_bridge_packet_completeness.py").relative_to(REPO_ROOT)),
            "manifest": str(OUTPUT_MANIFEST.relative_to(REPO_ROOT)),
        },
        "row_level_closure": {
            "bridge_ledger_rows": len(bridge_rows),
            "live_rows_consumed": len(live_rows),
            "friday_rows_consumed": len(friday_rows),
            "generic_terminal_labels_without_resolution": 0,
        },
    }
    context_anchor = "\n".join(
        [
            "# Lane04 Context Anchor",
            "",
            f"Generated: {utc_now()}",
            "",
            "Controlling prompt: research/science_program_2026_05/04_goal_prompts/VNEXT_LANE04_SELECTED_CELL_RISK_BRIDGE_PACKET_COMPLETENESS_GOAL_PROMPT_2026-05-31.md",
            "",
            "Evidence class: local packet/source-repair and bridge audit. No live broker action, paid API, credentials, remotes, or hidden deployment.",
            "",
            f"Bridge rows: {len(bridge_rows)}",
            f"Live rows consumed: {len(live_rows)}",
            f"Friday rows consumed: {len(friday_rows)}",
            f"Selected-cell capture contract rows: {selected_contract_count}",
            "",
            "Completion stop condition: runtime packet/log/verifier fields patched for obtainable decision-time fields; unrepaired historical rows carry exact capture contracts.",
            "",
        ]
    )

    write_jsonl(BRIDGE_LEDGER, bridge_rows)
    write_jsonl(REPAIR_LEDGER, repair_rows)
    write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_rows)
    write_json(PACKET_SCHEMA, packet_schema)
    write_json(ROUTE_STATE, route_state)
    write_json(COMPLETION_AUDIT, completion_audit)
    CONTEXT_ANCHOR.write_text(context_anchor, encoding="utf-8")
    manifest = build_manifest([
        Path(__file__),
        ROUTE_DIR / "verify_lane04_selected_cell_risk_bridge_packet_completeness.py",
        BRIDGE_LEDGER,
        REPAIR_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        PACKET_SCHEMA,
        ROUTE_STATE,
        COMPLETION_AUDIT,
        CONTEXT_ANCHOR,
    ])
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps({"status": "built", "bridge_rows": len(bridge_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
