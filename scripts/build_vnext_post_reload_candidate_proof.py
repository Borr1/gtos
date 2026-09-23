from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_ROUTE_DIR = REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
LEDGER_PATH = LIVE_ROUTE_DIR / "LIVE_POST_RELOAD_CANDIDATE_PROOF_LEDGER.jsonl"
SUMMARY_PATH = LIVE_ROUTE_DIR / "LIVE_POST_RELOAD_CANDIDATE_PROOF_SUMMARY.json"
CHECKPOINT_PATH = LIVE_ROUTE_DIR / "LIVE_COMPANION_CURRENT_CHECKPOINT.json"
DEFAULT_RELOAD_TS = "2026-05-28T17:17:05+00:00"
POST_RELOAD_EVENT_TIME_GRACE = timedelta(minutes=30)

REQUIRED_PACKET_PATHS = (
    ("candidate_identity", "candidate_id"),
    ("candidate_identity", "symbol"),
    ("candidate_identity", "broker_symbol"),
    ("candidate_identity", "origin_family"),
    ("candidate_identity", "side"),
    ("candidate_identity", "session"),
    ("candidate_identity", "kill_zone"),
    ("source_m15", "source_fields"),
    ("mso_context", "D1"),
    ("mso_context", "H4"),
    ("mso_context", "H1"),
    ("mso_context", "M15"),
    ("m1_ltf_availability",),
    ("tick_spread_snapshot",),
    ("broker_spec_snapshot",),
    ("geometry", "raw"),
    ("geometry", "repaired"),
    ("gates", "gate0_deployment_profile_trading"),
    ("gates", "gate1_pre_geometry"),
    ("gates", "gate1_final_after_repair"),
    ("gates", "gate3"),
    ("dynamic_policy", "selected_policy"),
    ("dynamic_policy", "execution_policy_id"),
    ("selector_bridge_proof",),
    ("selected_cell_risk_proof",),
    ("risk_lot_calculation",),
    ("final_risk_authority",),
    ("prop_governor", "before_geometry_repair"),
    ("prop_governor", "after_geometry_repair"),
    ("final_order_decision",),
    ("order_readiness",),
    ("source_completeness",),
    ("old_system_absence_proof",),
    ("refusal_and_repair_reasons",),
)


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _config() -> dict[str, Any]:
    return yaml.safe_load((REPO_ROOT / "config/agent_config.yaml").read_text(encoding="utf-8"))


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _get(data: Any, path: tuple[str, ...]) -> Any:
    value = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _mtime_utc(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except (TypeError, ValueError):
        return None


def _record_event_utc(record: dict[str, Any]) -> datetime | None:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    candidate = (
        record.get("moonshot_broader_origin_candidate")
        if isinstance(record.get("moonshot_broader_origin_candidate"), dict)
        else {}
    )
    pipeline = record.get("decision_pipeline") if isinstance(record.get("decision_pipeline"), dict) else {}
    packet = (
        pipeline.get("gtos_vnext_candidate_intelligence_packet")
        if isinstance(pipeline.get("gtos_vnext_candidate_intelligence_packet"), dict)
        else {}
    )
    identity = packet.get("candidate_identity") if isinstance(packet.get("candidate_identity"), dict) else {}
    for value in (
        identity.get("candle_close_utc"),
        candidate.get("candle_close_utc"),
        metadata.get("candle_close_utc"),
        metadata.get("candle_time"),
        candidate.get("candle_time_utc"),
        record.get("timestamp_utc"),
    ):
        parsed = _parse_utc(value)
        if parsed is not None:
            return parsed
    return None


def _checkpoint_reload_ts() -> str | None:
    checkpoint = _read_json(CHECKPOINT_PATH, {})
    if not isinstance(checkpoint, dict):
        return None
    flow = checkpoint.get("post_reload_candidate_flow")
    if isinstance(flow, dict) and flow.get("reload_timestamp_utc"):
        return str(flow["reload_timestamp_utc"])
    process = checkpoint.get("process")
    if isinstance(process, dict) and process.get("oldest_orchestrator_start_utc"):
        return str(process["oldest_orchestrator_start_utc"])
    return None


def _effective_reload_ts(reload_ts_text: str | None) -> str:
    return reload_ts_text or _checkpoint_reload_ts() or DEFAULT_RELOAD_TS


def _checkpoint_snapshot_upper_bound() -> str | None:
    checkpoint = _read_json(CHECKPOINT_PATH, {})
    if not isinstance(checkpoint, dict):
        return None
    value = checkpoint.get("generated_at_utc")
    return str(value) if value else None


def _candidate_records_after(
    reload_ts: datetime,
    *,
    snapshot_upper_bound: datetime | None = None,
) -> list[tuple[Path, datetime, dict[str, Any]]]:
    records: list[tuple[Path, datetime, dict[str, Any]]] = []
    for path in sorted((REPO_ROOT / "knowledge_base/trade_records").glob("*/*.json")):
        if path.name.startswith("_"):
            continue
        mtime = _mtime_utc(path)
        if mtime <= reload_ts:
            continue
        if snapshot_upper_bound and mtime > snapshot_upper_bound:
            continue
        record = _read_json(path, {})
        if isinstance(record, dict) and record.get("moonshot_broader_origin_candidate"):
            event_ts = _record_event_utc(record)
            if event_ts is None or event_ts < reload_ts - POST_RELOAD_EVENT_TIME_GRACE:
                continue
            records.append((path, mtime, record))
    return records


def _mso_packet(record: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    mso = record.get("mso")
    timeframes = mso.get("timeframes") if isinstance(mso, dict) else None
    available_hint = set()
    source_fields = candidate.get("source_fields") if isinstance(candidate.get("source_fields"), dict) else {}
    if isinstance(source_fields.get("mso_timeframes_available"), list):
        available_hint = {str(item) for item in source_fields.get("mso_timeframes_available")}
    packet: dict[str, Any] = {}
    for timeframe in ("D1", "H4", "H1", "M15"):
        if isinstance(timeframes, dict) and isinstance(timeframes.get(timeframe), dict):
            packet[timeframe] = {"available": True, "context": timeframes[timeframe]}
        elif timeframe in available_hint:
            packet[timeframe] = {
                "available": True,
                "context_status": "available_in_candidate_source_fields",
                "missing_reason": "saved_record_mso_context_omitted_or_non_dict",
            }
        else:
            packet[timeframe] = {
                "available": False,
                "missing_reason": "not_present_in_saved_record",
            }
    if isinstance(mso, dict):
        packet["_mso_timestamp_utc"] = mso.get("timestamp_utc")
        packet["_data_quality"] = mso.get("data_quality")
    return packet


def _policy_intent(candidate: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    runtime_cfg = cfg.get("gtos_vnext_runtime") or {}
    primary_policy = runtime_cfg.get("moonshot_dynamic_execution_router_policy") or "momentum_exhaustion"
    partial_policy = runtime_cfg.get(
        "moonshot_dynamic_execution_router_momentum_exception_policy",
        "partial_be_runner",
    )
    partial_families = runtime_cfg.get(
        "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
    ) or []
    family = str(candidate.get("origin_family") or candidate.get("candidate_origin_family") or "")
    family = family.removeprefix("origin_current_").removeprefix("origin_")
    selected_policy = partial_policy if family in set(partial_families) else primary_policy
    execution_ids = {
        "be_after_trigger": "vnext_exec_be_after_trigger_1r_to_15r",
        "partial_be_runner": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
        "momentum_exhaustion": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
    }
    return {
        "primary_policy": primary_policy,
        "selected_policy": selected_policy,
        "execution_policy_id": execution_ids.get(selected_policy),
        "partial_exception_policy": partial_policy,
        "partial_exception_origin_families": partial_families,
        "selected_policy_source": "pre_dynamic_current_production_policy_intent",
    }


def _selected_cell_packet(dynamic_record: dict[str, Any]) -> dict[str, Any]:
    router_record = dynamic_record.get("router_record") if isinstance(dynamic_record, dict) else {}
    if not isinstance(router_record, dict):
        router_record = {}
    route_dimensions = router_record.get("route_dimensions")
    if not isinstance(route_dimensions, dict):
        route_dimensions = {}
    source_event = dynamic_record.get("source_event") if isinstance(dynamic_record, dict) else {}
    if not isinstance(source_event, dict):
        source_event = {}
    def source_get(key: str, default: Any = None) -> Any:
        marker = object()
        value = route_dimensions.get(key, marker)
        if value is not marker and value not in (None, "", [], {}):
            return value
        fallback = source_event.get(key, marker)
        if fallback is not marker:
            return fallback
        if value is not marker:
            return value
        return default

    if not dynamic_record:
        return {"ran": False, "not_run_reason": "dynamic_router_not_reached"}
    allowed = source_get("selected_cell_risk_allowed")
    risk_pct = source_get("selected_cell_risk_pct")
    selected_policy = (
        source_get("selected_cell_risk_selected_policy")
        or dynamic_record.get("selected_policy")
    )
    source_policy = source_get("selected_cell_risk_source_policy")
    policy_identity_status = source_get("selected_cell_risk_policy_identity_status")
    if selected_policy and not policy_identity_status:
        policy_identity_status = "selected_policy_inherited_from_dynamic_router_record"
    return {
        "ran": True,
        "allowed": allowed,
        "risk_pct": risk_pct,
        "cell_id": source_get("selected_cell_risk_cell_id"),
        "source_ledger_path": source_get("selected_cell_risk_source_ledger_path"),
        "source_row_identity": source_get("selected_cell_risk_source_row_identity"),
        "capture_contract": source_get("selected_cell_risk_capture_contract"),
        "decision_basis": source_get("selected_cell_risk_decision_basis"),
        "match_reason": source_get("selected_cell_risk_match_reason"),
        "required": source_get("selected_cell_risk_required"),
        "selected_policy": selected_policy,
        "source_policy": source_policy,
        "source_policy_missing_reason": None
        if source_policy
        else "selected_cell_risk_source_policy_not_reported",
        "execution_policy_id": source_get("selected_cell_risk_execution_policy_id")
        or dynamic_record.get("execution_policy_id"),
        "policy_identity_status": policy_identity_status,
        "proof_reference": source_get("selected_cell_risk_cell_id") or source_event.get("row_id"),
        "refusal_cause": source_get("selected_cell_risk_refusal_cause"),
        "failed_dimensions": source_get("selected_cell_risk_failed_dimensions") or [],
        "nearest_candidate": source_get("selected_cell_risk_nearest_candidate"),
        "unresolved_reasons": source_get("selected_cell_risk_unresolved_reasons")
        or source_get("selected_cell_risk_execution_critical_unresolved_reasons")
        or [],
        "status": "verified_positive"
        if allowed is True and risk_pct not in (None, "", 0, 0.0)
        else "not_verified_or_zero",
    }


def _packet_from_saved_record(
    record: dict[str, Any],
    path: Path,
    mtime: datetime,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    candidate = record.get("moonshot_broader_origin_candidate") or {}
    metadata = record.get("metadata") or {}
    pipeline = record.get("decision_pipeline") or {}
    dynamic_record = pipeline.get("gtos_vnext_moonshot_dynamic_execution") or {}
    ltf_path = pipeline.get("gtos_vnext_ltf_path_execution") or {}
    gate1 = pipeline.get("gate1_result")
    gate3 = pipeline.get("gate3_result")
    repair = pipeline.get("gtos_vnext_executable_geometry_repair") or {}
    prop_before = pipeline.get("gtos_vnext_prop_safe_selector") or {}
    prop_after = pipeline.get("gtos_vnext_prop_safe_selector_after_geometry_repair")
    raw_trade_params = candidate.get("trade_parameters") if isinstance(candidate.get("trade_parameters"), dict) else {}
    runtime_cfg = cfg.get("gtos_vnext_runtime") or {}
    router_record = dynamic_record.get("router_record") if isinstance(dynamic_record, dict) else {}
    if not isinstance(router_record, dict):
        router_record = {}
    route_dimensions = router_record.get("route_dimensions")
    if not isinstance(route_dimensions, dict):
        route_dimensions = {}
    source_event = dynamic_record.get("source_event") if isinstance(dynamic_record, dict) else {}
    if not isinstance(source_event, dict):
        source_event = {}

    def dynamic_source_get(key: str, default: Any = None) -> Any:
        marker = object()
        value = route_dimensions.get(key, marker)
        if value is not marker and value not in (None, "", [], {}):
            return value
        fallback = source_event.get(key, marker)
        if fallback is not marker:
            return fallback
        if value is not marker:
            return value
        return default

    if repair:
        repair_path = {
            "entered": True,
            "status": repair.get("status"),
            "actions": repair.get("actions") or [],
        }
        repaired = {"status": repair.get("status"), "geometry": repair.get("repaired")}
        lot_recompute = repair.get("lot_recompute") or {
            "status": "missing",
            "missing_reason": "repair_present_without_lot_recompute",
        }
    else:
        reason = "dynamic_execution_not_applied_before_geometry_repair"
        if not dynamic_record:
            reason = "dynamic_router_not_reached_before_geometry_repair"
        repair_path = {"entered": False, "status": "not_entered", "not_entered_reason": reason}
        repaired = {"status": "not_run", "not_run_reason": reason, "geometry": None}
        lot_recompute = {"status": "not_run", "not_run_reason": reason}

    spread_cents = _get(gate3, ("details", "spread_cents")) if isinstance(gate3, dict) else None
    tick_snapshot = {
        "available": spread_cents is not None,
        "source": "gate3_result.details.spread_cents" if spread_cents is not None else None,
        "spread_cents": spread_cents,
    }
    if spread_cents is None:
        tick_snapshot["missing_reason"] = "tick_spread_not_captured_in_saved_record"

    broker_spec = repair.get("broker_spec_check") if repair else None
    if not isinstance(broker_spec, dict):
        broker_spec = {
            "available": False,
            "missing_reason": "not_captured_before_candidate_packet_patch_unless_geometry_repair_entered",
        }

    final_outcome = pipeline.get("final_outcome") or record.get("final_outcome")
    order_path = "not_reached"
    if record.get("limit_intent"):
        order_path = "pending_limit"
    elif record.get("execution"):
        order_path = "market_order"
    elif final_outcome == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC":
        order_path = "dynamic_execution_refused_before_geometry_repair"

    intent = _policy_intent(candidate, cfg)
    selected_cell = _selected_cell_packet(dynamic_record if isinstance(dynamic_record, dict) else {})
    selected_policy = (
        dynamic_record.get("selected_policy") if isinstance(dynamic_record, dict) else None
    ) or intent.get("selected_policy")
    execution_policy_id = (
        dynamic_record.get("execution_policy_id") if isinstance(dynamic_record, dict) else None
    ) or intent.get("execution_policy_id")
    effective_risk_pct = (
        pipeline.get("effective_risk_pct")
        or (prop_before.get("after_risk_pct") if isinstance(prop_before, dict) else None)
        or (prop_before.get("before_risk_pct") if isinstance(prop_before, dict) else None)
    )
    candidate_quality_selector = dynamic_source_get("candidate_quality_selector")
    if not isinstance(candidate_quality_selector, dict):
        candidate_quality_selector = {
            "enabled": bool(runtime_cfg.get("moonshot_candidate_quality_selector_enabled")),
            "apply_to_execution": bool(
                runtime_cfg.get("moonshot_candidate_quality_selector_apply_to_execution")
            ),
            "classification": (
                "not_run_before_dynamic_router"
                if not dynamic_record
                else "not_reported_by_dynamic_router"
            ),
            "refusal_reason": "dynamic_router_not_reached" if not dynamic_record else None,
            "evidence_path": runtime_cfg.get("moonshot_candidate_quality_selector_evidence_path"),
        }
    final_risk_authority = {
        "authority": (
            "post_geometry_prop_safe_selector"
            if isinstance(prop_after, dict) and prop_after.get("after_risk_pct") is not None
            else "pre_geometry_prop_safe_selector"
            if isinstance(prop_before, dict)
            and (
                prop_before.get("after_risk_pct") is not None
                or prop_before.get("before_risk_pct") is not None
            )
            else "pipeline_effective_risk_pct"
            if pipeline.get("effective_risk_pct") is not None
            else "risk_not_reached_or_not_recorded"
        ),
        "effective_risk_pct": effective_risk_pct,
        "selected_cell_risk_pct": selected_cell.get("risk_pct"),
        "selected_cell_risk_cell_id": selected_cell.get("cell_id"),
        "selected_cell_risk_status": selected_cell.get("status"),
        "selected_policy": selected_policy,
        "execution_policy_id": execution_policy_id,
        "prop_safe_before_geometry": prop_before or None,
        "prop_safe_after_geometry": prop_after if isinstance(prop_after, dict) else None,
    }
    selector_bridge_proof = {
        "schema_version": "gtos_vnext_selector_bridge_proof_v1",
        "dynamic_router_ran": bool(dynamic_record),
        "dynamic_not_run_reason": None if dynamic_record else "dynamic_router_not_reached",
        "current_policy_set": {
            "primary_policy": runtime_cfg.get("moonshot_dynamic_execution_router_policy")
            or "momentum_exhaustion",
            "selected_policy": selected_policy,
            "execution_policy_id": execution_policy_id,
            "partial_exception_policy": runtime_cfg.get(
                "moonshot_dynamic_execution_router_momentum_exception_policy"
            ),
            "partial_exception_origin_families": runtime_cfg.get(
                "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
            ),
        },
        "policy_intent": intent,
        "broader_origin_allowed": dynamic_source_get("broader_origin_allowed"),
        "broader_origin_match_reason": dynamic_source_get("broader_origin_match_reason"),
        "broader_origin_source_row_identity": dynamic_source_get(
            "broader_origin_source_row_identity"
        ),
        "broader_origin_capture_contract": dynamic_source_get(
            "broader_origin_capture_contract"
        ),
        "selected_cell_risk_source_row_identity": selected_cell.get("source_row_identity"),
        "selected_cell_risk_capture_contract": selected_cell.get("capture_contract"),
        "candidate_quality_selector": candidate_quality_selector,
        "spread_r_at_candidate": dynamic_source_get("spread_r_at_candidate"),
        "repaired_branch_allowed": (
            dynamic_record.get("candidate_use_allowed_now")
            if isinstance(dynamic_record, dict)
            else None
        ),
        "candidate_action": (
            dynamic_record.get("candidate_action") if isinstance(dynamic_record, dict) else None
        ),
    }
    final_order_decision = {
        "final_outcome": final_outcome,
        "reached_order_path": bool(record.get("limit_intent") or record.get("execution")),
        "order_path": order_path,
    }

    packet = {
        "schema_version": "gtos_vnext_candidate_intelligence_packet_v1",
        "capture_mode": "historical_saved_record_backfill",
        "capture_reason": "post_reload_record_preceded_live_packet_writer_patch",
        "record_path": str(path.relative_to(REPO_ROOT)),
        "record_mtime_utc": mtime.isoformat(),
        "candidate_identity": {
            "candidate_id": candidate.get("candidate_id"),
            "trade_id": metadata.get("trade_id"),
            "symbol": metadata.get("symbol") or candidate.get("symbol"),
            "broker_symbol": candidate.get("source_symbol") or metadata.get("broker_symbol") or candidate.get("symbol"),
            "origin_family": candidate.get("origin_family"),
            "candidate_origin_family": candidate.get("candidate_origin_family"),
            "framework": candidate.get("framework"),
            "side": candidate.get("side") or candidate.get("direction"),
            "session": candidate.get("session") or metadata.get("kill_zone"),
            "kill_zone": metadata.get("kill_zone") or candidate.get("kill_zone"),
            "route_session": candidate.get("route_session"),
            "utc_hour_bucket": candidate.get("utc_hour_bucket"),
            "candle_close_utc": candidate.get("candle_close_utc") or metadata.get("candle_close_utc"),
        },
        "source_m15": {
            "candle_open_utc": candidate.get("candle_open_utc"),
            "candle_close_utc": candidate.get("candle_close_utc") or metadata.get("candle_close_utc"),
            "timeframe": candidate.get("timeframe") or "M15",
            "market_timeframe": candidate.get("market_timeframe") or "M15",
            "source_path_feature_status": candidate.get("source_path_feature_status"),
            "source_window_complete": candidate.get("source_window_complete"),
            "source_fields": candidate.get("source_fields") or {},
        },
        "mso_context": _mso_packet(record, candidate),
        "m1_ltf_availability": {
            "ran": bool(ltf_path),
            "not_run_reason": None if ltf_path else "ltf_path_execution_not_reached",
            "source_complete": _get(ltf_path, ("path_state", "source_complete")),
            "source_timeframe": _get(ltf_path, ("path_state", "source_timeframe")),
            "path_source_status": _get(ltf_path, ("path_state", "path_source_status")),
            "path_state": ltf_path.get("path_state") if isinstance(ltf_path, dict) else None,
        },
        "tick_spread_snapshot": tick_snapshot,
        "broker_spec_snapshot": broker_spec,
        "geometry": {
            "raw": {
                "direction": raw_trade_params.get("direction") or candidate.get("direction"),
                "entry_price": _float_or_none(raw_trade_params.get("entry_price", candidate.get("entry_price"))),
                "stop_loss": _float_or_none(raw_trade_params.get("stop_loss", candidate.get("stop_loss"))),
                "take_profit_1": _float_or_none(raw_trade_params.get("take_profit_1", candidate.get("take_profit_1"))),
                "risk_reward_ratio": _float_or_none(raw_trade_params.get("risk_reward_ratio", candidate.get("risk_reward_ratio"))),
            },
            "repair_path": repair_path,
            "repaired": repaired,
            "repair_thresholds": repair.get("thresholds") if repair else None,
            "dynamic_target": repair.get("dynamic_target") if repair else None,
        },
        "gates": {
            "gate0_deployment_profile_trading": {
                "ran": True,
                "phase": (cfg.get("deployment") or {}).get("phase"),
                "trading_enabled": bool(cfg.get("trading_enabled", True)),
                "profile": cfg.get("profile") or cfg.get("active_profile"),
            },
            "gate1_pre_geometry": {
                "ran": isinstance(gate1, dict),
                "deferred_for_repair": isinstance(gate1, dict)
                and "deferred_until_vnext_executable_geometry_repair" in set(gate1.get("checks_run") or []),
                "output": gate1,
            },
            "gate1_final_after_repair": {
                "ran_after_repair": bool(repair)
                and isinstance(gate1, dict)
                and "deferred_until_vnext_executable_geometry_repair" not in set(gate1.get("checks_run") or []),
                "not_run_reason": None if repair else repair_path["not_entered_reason"],
                "output": gate1,
            },
            "gate3": {"ran": isinstance(gate3, dict), "output": gate3},
        },
        "dynamic_policy": {
            "ran": bool(dynamic_record),
            "not_run_reason": None if dynamic_record else "dynamic_router_not_reached",
            "policy_intent": intent,
            "selected_policy_source": "dynamic_router_result"
            if dynamic_record
            else "pre_dynamic_current_production_policy_intent",
            "applied": dynamic_record.get("applied") if isinstance(dynamic_record, dict) else None,
            "selected_policy": selected_policy,
            "execution_policy_id": execution_policy_id,
            "decision_status": dynamic_record.get("decision_status") if isinstance(dynamic_record, dict) else None,
            "candidate_action": dynamic_record.get("candidate_action") if isinstance(dynamic_record, dict) else None,
            "source_quality_action": dynamic_record.get("source_quality_action") if isinstance(dynamic_record, dict) else None,
            "prop_action": dynamic_record.get("prop_action") if isinstance(dynamic_record, dict) else None,
            "refusal_reasons": dynamic_record.get("refusal_reasons") if isinstance(dynamic_record, dict) else [],
        },
        "selector_bridge_proof": selector_bridge_proof,
        "selected_cell_risk_proof": selected_cell,
        "risk_lot_calculation": {
            "autocorrelation_risk_sizing": pipeline.get("autocorrelation_risk_sizing"),
            "vnext_risk_adjustment": pipeline.get("gtos_vnext_risk_adjustment"),
            "prop_safe_selector_before_geometry": prop_before or None,
            "effective_risk_pct": effective_risk_pct,
            "lot_recompute": lot_recompute,
        },
        "final_risk_authority": final_risk_authority,
        "prop_governor": {
            "before_geometry_repair": prop_before or {
                "ran": False,
                "not_run_reason": "prop_safe_selector_not_reached",
            },
            "after_geometry_repair": prop_after or {
                "ran": False,
                "not_run_reason": "geometry_repair_not_entered" if not repair else "prop_recheck_missing",
            },
        },
        "pending_policy": {
            "ran": bool(pipeline.get("gtos_vnext_pending_policy")),
            "record": pipeline.get("gtos_vnext_pending_policy"),
        },
        "runtime_decision": pipeline.get("gtos_vnext_runtime"),
        "final_order_decision": final_order_decision,
        "order_readiness": {
            "reached_order_path": bool(final_order_decision.get("reached_order_path")),
            "order_path": final_order_decision.get("order_path"),
            "final_outcome": final_order_decision.get("final_outcome"),
            "not_ready_reason": (
                None
                if final_order_decision.get("reached_order_path")
                else final_order_decision.get("order_path") or "order_path_not_reached"
            ),
            "geometry_repair_status": repaired.get("status"),
            "selected_cell_risk_status": selected_cell.get("status"),
            "dynamic_policy_selected": selected_policy,
            "execution_policy_id": execution_policy_id,
        },
        "source_completeness": {
            "source_mode": dynamic_source_get("source_mode", candidate.get("source_mode")),
            "source_path_feature_status": dynamic_source_get(
                "source_path_feature_status",
                candidate.get("source_path_feature_status"),
            ),
            "source_window_complete": dynamic_source_get(
                "source_window_complete",
                candidate.get("source_window_complete"),
            ),
            "live_generation": "historical_saved_record_backfill",
            "m1_ltf_available": bool(ltf_path),
            "tick_spread_available": bool(tick_snapshot.get("available")),
            "broker_spec_available": bool(
                broker_spec.get("available")
                if "available" in broker_spec
                else broker_spec.get("symbol_info_available")
            ),
            "selected_policy_ordered_path_status": dynamic_source_get(
                "selected_policy_ordered_path_status"
            ),
            "ordered_path_status": dynamic_source_get("ordered_path_status"),
            "selected_cell_capture_contract": selected_cell.get("capture_contract"),
            "broader_origin_capture_contract": selector_bridge_proof.get(
                "broader_origin_capture_contract"
            ),
        },
        "old_system_absence_proof": {
            "old_primary_analyzer_called": bool(
                pipeline.get("old_primary_analyzer_called", False)
            ),
            "old_l2_required": bool(pipeline.get("old_l2_required", False)),
            "absence_status": (
                "explicit_absent"
                if not bool(pipeline.get("old_primary_analyzer_called", False))
                and not bool(pipeline.get("old_l2_required", False))
                else "legacy_component_flag_present"
            ),
            "current_system": "gtos_vnext_moonshot_production_replacement",
        },
        "refusal_and_repair_reasons": {
            "dynamic_refusal_reasons": dynamic_record.get("refusal_reasons") if isinstance(dynamic_record, dict) else [],
            "recorded_dynamic_refusal_reasons": pipeline.get("gtos_vnext_moonshot_dynamic_refusal_reasons", []),
            "permission_reason": pipeline.get("permission_reason"),
            "permission_gate": pipeline.get("permission_gate"),
            "repair_actions": repair.get("actions") if repair else [],
            "repair_not_entered_reason": None if repair else repair_path["not_entered_reason"],
        },
    }
    return packet


def _packet_missing_fields(packet: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for path in REQUIRED_PACKET_PATHS:
        value = _get(packet, path)
        if value in (None, ""):
            missing.append(".".join(path))
    return missing


def _null_zero_without_reason(packet: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    selected = packet.get("selected_cell_risk_proof") or {}
    selected_status = selected.get("status")
    selected_match_reason = selected.get("match_reason")
    if (
        selected.get("risk_pct") in (None, 0, 0.0, "")
        and selected_status != "not_verified_or_zero"
        and not (
            selected.get("ran") is False
            and (
                selected.get("not_run_reason")
                or selected.get("risk_pct_missing_reason")
                or selected_status == "not_applicable_dynamic_router_not_reached"
            )
        )
    ):
        issues.append("selected_cell_risk_proof.risk_pct")
    if selected_status == "not_verified_or_zero":
        if not (
            selected.get("decision_basis")
            or selected_match_reason
            or selected.get("risk_pct_missing_reason")
            or selected.get("refusal_cause")
            or selected.get("unresolved_reasons")
            or selected.get("capture_contract")
        ):
            issues.append("selected_cell_risk_proof.reason")
        if selected_match_reason == "no_exact_selected_cell_risk_match" and not (
            selected.get("refusal_cause")
            or selected.get("failed_dimensions")
            or selected.get("nearest_candidate")
            or selected.get("capture_contract")
        ):
            issues.append("selected_cell_risk_proof.no_exact_match_classification")
    broker = packet.get("broker_spec_snapshot") or {}
    if broker.get("available") is False and not broker.get("missing_reason"):
        issues.append("broker_spec_snapshot.missing_reason")
    tick = packet.get("tick_spread_snapshot") or {}
    if tick.get("available") is False and not tick.get("missing_reason"):
        issues.append("tick_spread_snapshot.missing_reason")
    repaired = _get(packet, ("geometry", "repaired")) or {}
    if repaired.get("geometry") is None and not repaired.get("not_run_reason") and not repaired.get("missing_reason"):
        issues.append("geometry.repaired")
    prop_after = _get(packet, ("prop_governor", "after_geometry_repair")) or {}
    if prop_after.get("ran") is False and not prop_after.get("not_run_reason"):
        issues.append("prop_governor.after_geometry_repair.not_run_reason")
    return issues


def _row_from_record(path: Path, mtime: datetime, record: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    pipeline = record.get("decision_pipeline") or {}
    packet = pipeline.get("gtos_vnext_candidate_intelligence_packet")
    packet_present_before = isinstance(packet, dict)
    packet_contract_projection_applied = False
    if not packet_present_before:
        packet = _packet_from_saved_record(record, path, mtime, cfg)
    elif _packet_missing_fields(packet):
        packet = _packet_from_saved_record(record, path, mtime, cfg)
        packet_contract_projection_applied = True
    assert isinstance(packet, dict)
    repair_path = _get(packet, ("geometry", "repair_path")) or {}
    final_gate = _get(packet, ("gates", "gate1_final_after_repair")) or {}
    selected = packet.get("selected_cell_risk_proof") or {}
    lot = _get(packet, ("risk_lot_calculation", "lot_recompute")) or {}
    prop_after = _get(packet, ("prop_governor", "after_geometry_repair")) or {}
    final_order = packet.get("final_order_decision") or {}
    dynamic_policy = packet.get("dynamic_policy") or {}
    identity = packet.get("candidate_identity") or {}
    selector_bridge = packet.get("selector_bridge_proof") or {}
    source_completeness = packet.get("source_completeness") or {}
    order_readiness = packet.get("order_readiness") or {}
    final_risk = packet.get("final_risk_authority") or {}
    old_system_absence = packet.get("old_system_absence_proof") or {}
    return {
        "schema_version": "vnext_post_reload_candidate_proof_row_v1",
        "record_path": str(path.relative_to(REPO_ROOT)),
        "record_mtime_utc": mtime.isoformat(),
        "system_version": (record.get("metadata") or {}).get("system_version"),
        "candidate_id": identity.get("candidate_id"),
        "symbol": identity.get("symbol"),
        "broker_symbol": identity.get("broker_symbol"),
        "origin_family": identity.get("origin_family"),
        "candidate_origin_family": identity.get("candidate_origin_family"),
        "side": identity.get("side"),
        "session": identity.get("session"),
        "kill_zone": identity.get("kill_zone"),
        "final_outcome": final_order.get("final_outcome") or pipeline.get("final_outcome"),
        "packet_present_before_build": packet_present_before,
        "packet_contract_projection_applied": packet_contract_projection_applied,
        "packet_capture_mode": packet.get("capture_mode", "live_writer"),
        "packet_missing_required_fields": _packet_missing_fields(packet),
        "null_zero_without_reason": _null_zero_without_reason(packet),
        "entered_executable_geometry_repair": bool(repair_path.get("entered")),
        "repair_status": repair_path.get("status"),
        "repair_actions": repair_path.get("actions") or [],
        "repair_not_entered_reason": repair_path.get("not_entered_reason"),
        "final_gate1_ran_after_repair": bool(final_gate.get("ran_after_repair")),
        "final_gate1_not_run_reason": final_gate.get("not_run_reason"),
        "selected_cell_risk_proof_ran": bool(selected.get("ran")),
        "selected_cell_risk_status": selected.get("status"),
        "selected_cell_risk_pct": selected.get("risk_pct"),
        "selected_cell_risk_cell_id": selected.get("cell_id"),
        "selected_cell_risk_capture_contract": selected.get("capture_contract"),
        "selector_bridge_candidate_quality_classification": _get(
            selector_bridge,
            ("candidate_quality_selector", "classification"),
        ),
        "selector_bridge_spread_r_at_candidate": selector_bridge.get("spread_r_at_candidate"),
        "source_completeness_state": source_completeness,
        "final_risk_authority": final_risk.get("authority"),
        "final_risk_effective_risk_pct": final_risk.get("effective_risk_pct"),
        "risk_lot_recompute_status": lot.get("status"),
        "prop_before_geometry_action": _get(packet, ("prop_governor", "before_geometry_repair", "action")),
        "prop_after_geometry_ran": prop_after.get("ran") if "ran" in prop_after else bool(prop_after),
        "prop_after_geometry_action": prop_after.get("action"),
        "prop_after_geometry_not_run_reason": prop_after.get("not_run_reason"),
        "dynamic_policy_selected": dynamic_policy.get("selected_policy"),
        "execution_policy_id": dynamic_policy.get("execution_policy_id"),
        "dynamic_policy_applied": dynamic_policy.get("applied"),
        "dynamic_refusal_reasons": dynamic_policy.get("refusal_reasons") or [],
        "reached_order_path": bool(order_readiness.get("reached_order_path")),
        "order_path": order_readiness.get("order_path") or final_order.get("order_path"),
        "old_primary_analyzer_called": old_system_absence.get("old_primary_analyzer_called"),
        "old_l2_required": old_system_absence.get("old_l2_required"),
        "old_system_absence_status": old_system_absence.get("absence_status"),
        "packet": packet,
    }


def build(
    *,
    reload_ts_text: str | None = None,
    backfill_records: bool = False,
    snapshot_upper_bound_text: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    effective_reload_ts = _effective_reload_ts(reload_ts_text)
    reload_ts = datetime.fromisoformat(effective_reload_ts.replace("Z", "+00:00"))
    effective_snapshot_upper_bound = (
        snapshot_upper_bound_text or _checkpoint_snapshot_upper_bound()
    )
    snapshot_upper_bound = (
        _parse_utc(effective_snapshot_upper_bound)
        if effective_snapshot_upper_bound
        else None
    )
    cfg = _config()
    rows: list[dict[str, Any]] = []
    backfilled_paths: list[str] = []
    for path, mtime, record in _candidate_records_after(
        reload_ts,
        snapshot_upper_bound=snapshot_upper_bound,
    ):
        pipeline = record.setdefault("decision_pipeline", {})
        if backfill_records and not isinstance(pipeline.get("gtos_vnext_candidate_intelligence_packet"), dict):
            packet = _packet_from_saved_record(record, path, mtime, cfg)
            pipeline["gtos_vnext_candidate_intelligence_packet"] = packet
            record.setdefault("instrumentation", {})[
                "gtos_vnext_candidate_intelligence_packet_backfill"
            ] = {
                "backfilled_at_utc": datetime.now(timezone.utc).isoformat(),
                "reason": "post_reload_candidate_preceded_live_packet_writer_patch",
                "script": "scripts/build_vnext_post_reload_candidate_proof.py",
            }
            path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            backfilled_paths.append(str(path.relative_to(REPO_ROOT)))
            mtime = _mtime_utc(path)
        rows.append(_row_from_record(path, mtime, record, cfg))

    final_counts = Counter(str(row.get("final_outcome") or "missing") for row in rows)
    packet_modes = Counter(str(row.get("packet_capture_mode") or "missing") for row in rows)
    repair_counts = Counter(
        "entered" if row.get("entered_executable_geometry_repair") else "not_entered"
        for row in rows
    )
    summary = {
        "schema_version": "vnext_post_reload_candidate_proof_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reload_timestamp_utc": reload_ts.isoformat(),
        "snapshot_upper_bound_utc": (
            snapshot_upper_bound.isoformat() if snapshot_upper_bound else None
        ),
        "candidate_records_after_reload": len(rows),
        "final_outcome_counts": dict(final_counts),
        "packet_capture_mode_counts": dict(packet_modes),
        "packet_missing_before_build": sum(1 for row in rows if not row["packet_present_before_build"]),
        "records_backfilled": backfilled_paths,
        "repair_entry_counts": dict(repair_counts),
        "rows_missing_required_packet_fields": sum(1 for row in rows if row["packet_missing_required_fields"]),
        "rows_with_null_zero_without_reason": sum(1 for row in rows if row["null_zero_without_reason"]),
        "dynamic_refusal_rows": sum(
            1 for row in rows if row.get("final_outcome") == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC"
        ),
        "order_path_rows": sum(1 for row in rows if row.get("reached_order_path")),
        "ledger_path": str(LEDGER_PATH.relative_to(REPO_ROOT)),
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reload-ts",
        default=None,
        help=(
            "Override the current checkpoint reload timestamp. By default the "
            "builder uses LIVE_COMPANION_CURRENT_CHECKPOINT.json so current-live "
            "proof does not include historical pre-repair packet rows."
        ),
    )
    parser.add_argument("--backfill-records", action="store_true")
    parser.add_argument(
        "--snapshot-upper-bound-utc",
        default=None,
        help=(
            "Ignore trade records with mtime after this UTC timestamp. By default "
            "the current live checkpoint generated_at_utc is used when available."
        ),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows, summary = build(
        reload_ts_text=args.reload_ts,
        backfill_records=args.backfill_records,
        snapshot_upper_bound_text=args.snapshot_upper_bound_utc,
    )
    comparable_summary = dict(summary)
    comparable_summary.pop("generated_at_utc", None)
    if args.check:
        current_rows = []
        if LEDGER_PATH.exists():
            for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    current_rows.append(json.loads(line))
        current_summary = _read_json(SUMMARY_PATH, {})
        current_comparable = dict(current_summary or {})
        current_comparable.pop("generated_at_utc", None)
        if current_rows != rows or current_comparable != comparable_summary:
            print(json.dumps({"status": "failed", "reason": "outputs_not_current"}, sort_keys=True))
            return 1
        print(json.dumps({"status": "passed", "rows": len(rows)}, sort_keys=True))
        return 0
    _write_jsonl(LEDGER_PATH, rows)
    out_summary = dict(summary)
    SUMMARY_PATH.write_text(json.dumps(out_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "built", "rows": len(rows), "backfilled": len(summary["records_backfilled"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
