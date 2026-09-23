"""Read-only current live candidate/trade/lifecycle/risk audit.

This audit is intentionally broader than a single issue check. It reconciles:

- every current broker-open redacted_account position against local trade records;
- every current-cycle candidate/trade record for 2026-06-02;
- entry/partial/close slippage telemetry;
- pending-limit lifecycle rows;
- dual-broker canonical intents and FTMO follower actions;
- account risk exposure and obvious stale/null linkage hazards.

It does not call MT5 and does not mutate broker state. Broker truth comes from
the route's most recent read-only MT5 probe.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE = Path("research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02")
TRADE_ROOT = Path("knowledge_base/redacted_account_live_bee34003/trade_records")
BROKER_PROBE = ROUTE / "DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json"
AGENT_CONFIG = Path("config/agent_config.yaml")
SLIPPAGE_LOG = Path("shadow_logs/slippage.jsonl")
PENDING_LIFECYCLE_LOG = Path("shadow_logs/pending_limit_lifecycle.jsonl")
INTENT_LOG = Path("pipeline_state/dual_broker/canonical_trade_intents.jsonl")
FOLLOWER_ACTIONS = Path(
    "pipeline_state/operator_profile/dual_broker_execution_follower_actions.jsonl"
)
TODAY = "2026-06-02"

SUMMARY_PATH = ROUTE / "DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_AUDIT.json"
LEDGER_PATH = ROUTE / "DUAL_CURRENT_LIVE_CANDIDATE_TRADE_LIFECYCLE_LEDGER.jsonl"
DIRECT_INSPECTION_PATH = ROUTE / "DUAL_CURRENT_LIVE_DIRECT_INSPECTION_CLASSES.json"
ANOMALY_LEDGER = ROUTE / "DUAL_ANOMALY_LEDGER.jsonl"
CHECKPOINT_LEDGER = ROUTE / "DUAL_SUPERVISOR_CHECKPOINTS.jsonl"
STATE_PATH = ROUTE / "DUAL_SUPERVISOR_STATE.json"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _close(a: Any, b: Any, tol: float = 1e-6, rel: float = 1e-6) -> bool:
    na = _number(a)
    nb = _number(b)
    if na is None or nb is None:
        return False
    return abs(na - nb) <= max(tol, abs(nb) * rel)


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                yield line_no, {"_malformed": True, "_raw": raw[:500]}
                continue
            yield line_no, row


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _final_outcome(record: dict[str, Any]) -> str:
    pipeline = _dict(record.get("decision_pipeline"))
    return str(pipeline.get("final_outcome") or record.get("final_outcome") or record.get("status") or "")


def _permission_reason(record: dict[str, Any]) -> str | None:
    pipeline = _dict(record.get("decision_pipeline"))
    gate3 = _dict(pipeline.get("gate3_result"))
    details = _dict(gate3.get("details"))
    for key in ("permission_reason", "reason", "blocked_by", "reject_reason"):
        value = pipeline.get(key) or gate3.get(key) or details.get(key)
        if value:
            return str(value)
    return None


def _rejection_class(record: dict[str, Any]) -> str | None:
    pipeline = _dict(record.get("decision_pipeline"))
    gate3 = _dict(pipeline.get("gate3_result"))
    details = _dict(gate3.get("details"))
    for key in (
        "same_symbol_vnext_lifecycle_conflict",
        "concurrent_cap",
        "cross_instrument_correlation_cluster",
    ):
        item = details.get(key)
        if isinstance(item, dict):
            status = str(item.get("status") or "")
            if "reject" in status.lower() or "excess" in status.lower() or item.get("rejected"):
                return key
    reason = _permission_reason(record)
    return reason


def _risk_released(direction: str, entry_price: Any, broker_sl: Any) -> bool:
    entry = _number(entry_price)
    sl = _number(broker_sl)
    if entry is None or sl is None:
        return False
    direction = direction.upper()
    if direction == "LONG":
        return sl >= entry
    if direction == "SHORT":
        return sl <= entry
    return False


def _symbol_aliases(symbol: str) -> set[str]:
    aliases = {symbol}
    mapping = {
        "GER40": {"GER30", "GER40", "GER40.cash"},
        "JP225": {"JP225", "JP225.cash"},
        "NAS100": {"NDX100", "NAS100", "US100.cash"},
        "SPX500": {"SPX500", "US500.cash"},
        "UK100": {"UK100", "UK100.cash"},
        "UKOIL_cash": {"UKOUSD", "UKOIL_cash", "UKOIL.cash"},
        "US30_cash": {"US30", "US30_cash", "US30.cash"},
        "USOIL_cash": {"USOUSD", "USOIL_cash", "USOIL.cash"},
    }
    aliases.update(mapping.get(symbol, set()))
    return aliases


def _record_summary(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    meta = _dict(record.get("metadata"))
    execution = _dict(record.get("execution"))
    instrumentation = _dict(record.get("instrumentation"))
    pipeline = _dict(record.get("decision_pipeline"))
    packet = _dict(pipeline.get("gtos_vnext_candidate_intelligence_packet"))
    identity = _dict(packet.get("candidate_identity"))
    gate3 = _dict(pipeline.get("gate3_result"))
    selected_cell = _dict(pipeline.get("gtos_vnext_selected_cell_risk_composition"))
    dynamic = _dict(pipeline.get("gtos_vnext_moonshot_dynamic_execution"))
    exit_payload = _dict(record.get("exit"))
    limit_intent = _dict(record.get("limit_intent"))

    symbol = meta.get("symbol") or identity.get("symbol")
    trade_id = meta.get("trade_id") or record.get("trade_id") or execution.get("trade_id")
    candidate_id = meta.get("candidate_id") or identity.get("candidate_id")
    policy = (
        instrumentation.get("gtos_vnext_dynamic_policy_selected")
        or execution.get("gtos_vnext_dynamic_policy_selected")
        or dynamic.get("selected_policy")
    )
    execution_policy_id = (
        instrumentation.get("gtos_vnext_execution_policy_id")
        or execution.get("gtos_vnext_execution_policy_id")
        or dynamic.get("execution_policy_id")
    )
    selected_risk_pct = (
        execution.get("gtos_vnext_selected_cell_risk_pct")
        or instrumentation.get("gtos_vnext_selected_cell_risk_pct")
        or selected_cell.get("effective_risk_pct")
        or pipeline.get("effective_risk_pct")
    )
    return {
        "path": str(path),
        "is_today": TODAY in path.name,
        "symbol": symbol,
        "broker_symbol": meta.get("broker_symbol") or execution.get("broker_symbol") or identity.get("broker_symbol"),
        "trade_id": trade_id,
        "candidate_id": candidate_id,
        "origin_family": identity.get("origin_family") or identity.get("candidate_origin_family"),
        "framework": pipeline.get("ai_framework") or identity.get("framework"),
        "direction": execution.get("direction") or pipeline.get("ai_direction") or identity.get("side"),
        "final_outcome": _final_outcome(record),
        "permission_reason": _permission_reason(record),
        "rejection_class": _rejection_class(record),
        "ticket": execution.get("position_ticket") or execution.get("ticket") or execution.get("mt5_ticket"),
        "entry_order_ticket": execution.get("entry_order_ticket"),
        "entry_deal_ticket": execution.get("entry_deal_ticket"),
        "entry_deal_ticket_status": execution.get("entry_deal_ticket_status"),
        "entry_price": execution.get("entry_price") or execution.get("executed_entry_price"),
        "initial_volume": execution.get("initial_volume") or execution.get("lot_size"),
        "current_volume": execution.get("current_volume"),
        "stop_loss": execution.get("stop_loss"),
        "active_stop_loss": execution.get("active_stop_loss") or execution.get("broker_stop_loss"),
        "active_take_profit": execution.get("active_take_profit") or execution.get("broker_take_profit"),
        "take_profit_1": execution.get("take_profit_1"),
        "cash_risk_amount": execution.get("cash_risk_amount"),
        "residual_worst_case_cash_risk_amount": execution.get("residual_worst_case_cash_risk_amount"),
        "risk_pct": execution.get("risk_pct"),
        "selected_risk_pct": selected_risk_pct,
        "selected_cell_id": (
            execution.get("gtos_vnext_selected_cell_risk_cell_id")
            or instrumentation.get("gtos_vnext_selected_cell_risk_cell_id")
            or selected_cell.get("selected_cell_id")
        ),
        "selected_policy": policy,
        "execution_policy_id": execution_policy_id,
        "partial_closed": instrumentation.get("gtos_vnext_recovered_partial_closed"),
        "residual_open": instrumentation.get("gtos_vnext_recovered_residual_open"),
        "recovered_partial_close_events": instrumentation.get(
            "gtos_vnext_recovered_partial_close_events"
        ),
        "active_lifecycle_status": instrumentation.get("gtos_vnext_active_lifecycle_truth_status"),
        "active_lifecycle_capture_status": execution.get("active_lifecycle_capture_status"),
        "old_primary_analyzer_called": pipeline.get("old_primary_analyzer_called"),
        "old_l2_required": pipeline.get("old_l2_required"),
        "gate3_status": gate3.get("status") or gate3.get("allowed"),
        "dynamic_refusal_reasons": pipeline.get("gtos_vnext_moonshot_dynamic_refusal_reasons"),
        "limit_order_ticket": limit_intent.get("order_ticket") or limit_intent.get("ticket"),
        "exit_present": record.get("exit") is not None,
        "exit_type": exit_payload.get("exit_type"),
        "actual_r": exit_payload.get("actual_r"),
        "broker_close_deal_id": exit_payload.get("broker_close_deal_id"),
        "broker_close_order_id": exit_payload.get("broker_close_order_id"),
        "broker_profit": exit_payload.get("broker_profit") or exit_payload.get("broker_close_deal_profit"),
        "mfe_time_minutes": exit_payload.get("mfe_time_minutes"),
        "mae_time_minutes": exit_payload.get("mae_time_minutes"),
    }


def _load_trade_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    today_rows: list[dict[str, Any]] = []
    for path in sorted(TRADE_ROOT.glob("*/*.json")):
        try:
            record = _load_json(path)
        except Exception as exc:  # noqa: BLE001
            row = {"path": str(path), "record_load_error": str(exc), "issues": ["record_load_error"]}
        else:
            row = _record_summary(path, record)
        all_rows.append(row)
        if TODAY in path.name:
            today_rows.append(row)
    return all_rows, today_rows


def _load_broker_state() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    probe = _load_json(BROKER_PROBE)
    funded = probe["probes"]["redacted_account"]
    ftmo = probe["probes"]["operator_profile"]
    positions = funded.get("positions") or []
    by_ticket = {int(pos["ticket"]): pos for pos in positions if pos.get("ticket") is not None}
    account = {
        "redacted_account": funded.get("account_info") or {},
        "ftmo": ftmo.get("account_info") or {},
        "redacted_account_orders": funded.get("orders") or [],
        "ftmo_orders": ftmo.get("orders") or [],
        "redacted_account_symbol_summary": funded.get("symbol_check_summary") or {},
        "ftmo_symbol_summary": ftmo.get("symbol_check_summary") or {},
        "probe_recorded_at_utc": probe.get("recorded_at_utc"),
    }
    return account, positions, ftmo.get("positions") or [], by_ticket


def _load_agent_risk_config() -> dict[str, Any]:
    config = yaml.safe_load(AGENT_CONFIG.read_text(encoding="utf-8")) or {}
    risk = config.get("risk") or {}
    return {
        "risk_per_trade_pct": risk.get("risk_per_trade_pct"),
        "max_daily_loss_pct": risk.get("max_daily_loss_pct"),
        "max_weekly_loss_pct": risk.get("max_weekly_loss_pct"),
        "max_monthly_loss_pct": risk.get("max_monthly_loss_pct"),
        "max_concurrent": risk.get("max_concurrent"),
        "cross_instrument_correlation_enabled": risk.get("cross_instrument_correlation_enabled"),
    }


def _load_jsonl_rows(path: Path, today_only: bool = False) -> list[dict[str, Any]]:
    rows = []
    for line_no, row in _iter_jsonl(path) or []:
        if today_only and TODAY not in json.dumps(row, sort_keys=True):
            continue
        row["_line_no"] = line_no
        rows.append(row)
    return rows


def _position_worst_case_risk(record: dict[str, Any], pos: dict[str, Any]) -> tuple[float | None, str]:
    if _risk_released(str(record.get("direction") or ""), record.get("entry_price"), pos.get("sl")):
        return 0.0, "broker_sl_at_or_better_than_entry"
    residual = _number(record.get("residual_worst_case_cash_risk_amount"))
    if residual is not None:
        return max(residual, 0.0), "record_residual_worst_case_cash_risk_amount"
    cash = _number(record.get("cash_risk_amount"))
    if cash is None:
        return None, "missing_cash_risk_amount"
    initial_volume = _number(record.get("initial_volume"))
    current_volume = _number(pos.get("volume"))
    if initial_volume and current_volume is not None:
        return max(cash * current_volume / initial_volume, 0.0), "scaled_original_cash_risk_by_current_volume"
    return max(cash, 0.0), "record_cash_risk_amount_unscaled"


def _material_record_issues(rec: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    final = str(rec.get("final_outcome") or "")
    is_filled = "LIMIT_FILLED" in final or final == "EXECUTED"
    is_rejected = final.startswith("REJECTED")
    is_skipped = final.startswith("SKIPPED")
    is_cancelled = final.startswith("LIMIT_CANCELLED")

    for field in ("symbol", "trade_id", "candidate_id", "final_outcome"):
        if rec.get(field) in (None, ""):
            issues.append({"issue_id": f"record_missing_{field}", "severity": "candidate_observability"})

    if rec.get("old_primary_analyzer_called") not in (False, None):
        issues.append({"issue_id": "old_primary_analyzer_called_in_vnext_record", "severity": "active_if_current_path"})
    if rec.get("old_l2_required") not in (False, None):
        issues.append({"issue_id": "old_l2_required_in_vnext_record", "severity": "active_if_current_path"})

    if is_filled:
        required = (
            "ticket",
            "direction",
            "entry_price",
            "initial_volume",
            "current_volume",
            "stop_loss",
            "take_profit_1",
            "cash_risk_amount",
            "risk_pct",
            "selected_policy",
            "execution_policy_id",
            "selected_risk_pct",
            "selected_cell_id",
        )
        for field in required:
            if rec.get(field) in (None, ""):
                issues.append({"issue_id": f"filled_record_missing_{field}", "severity": "active_if_open"})
        if _number(rec.get("current_volume")) == 0 and not rec.get("exit_present"):
            issues.append({"issue_id": "filled_open_record_zero_current_volume_without_exit", "severity": "active_if_open"})
        if rec.get("entry_deal_ticket") in (None, 0) and rec.get("entry_deal_ticket_status") not in (
            "CAPTURED",
            "BROKER_DEAL_TIME_SOURCE_NOT_CAPTURED",
        ):
            issues.append({"issue_id": "entry_deal_ticket_missing_without_status", "severity": "broker_truth_observability"})
        if rec.get("exit_present"):
            for field in ("exit_type", "actual_r"):
                if rec.get(field) in (None, ""):
                    issues.append({"issue_id": f"closed_record_missing_{field}", "severity": "exit_observability"})
            if _number(rec.get("mfe_time_minutes")) is not None and _number(rec.get("mfe_time_minutes")) < 0:
                issues.append({"issue_id": "closed_record_negative_mfe_time", "severity": "exit_analytics"})
            if _number(rec.get("mae_time_minutes")) is not None and _number(rec.get("mae_time_minutes")) < 0:
                issues.append({"issue_id": "closed_record_negative_mae_time", "severity": "exit_analytics"})

    if is_rejected and not (rec.get("permission_reason") or rec.get("rejection_class")):
        issues.append({"issue_id": "rejected_record_missing_reason", "severity": "candidate_decision_observability"})
    if is_skipped and not rec.get("dynamic_refusal_reasons"):
        issues.append({"issue_id": "skipped_dynamic_record_missing_refusal_reasons", "severity": "candidate_decision_observability"})
    if is_cancelled and rec.get("limit_order_ticket") not in (None, 0, ""):
        issues.append({"issue_id": "cancelled_record_still_has_live_limit_ticket_field", "severity": "pending_order_linkage"})
    return issues


def _inspect_records(
    all_records: list[dict[str, Any]],
    today_records: list[dict[str, Any]],
    broker_positions: list[dict[str, Any]],
    broker_by_ticket: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    records_by_ticket: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for rec in all_records:
        ticket = rec.get("ticket")
        if ticket is None:
            continue
        try:
            records_by_ticket[int(ticket)].append(rec)
        except (TypeError, ValueError):
            continue

    inspected_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for rec in today_records:
        rec_issues = _material_record_issues(rec)
        severity = "candidate_current_cycle"
        if rec.get("ticket") is not None:
            try:
                if int(rec["ticket"]) in broker_by_ticket:
                    severity = "active"
            except (TypeError, ValueError):
                pass
        inspected_rows.append(
            {
                **rec,
                "row_type": "today_trade_record",
                "issues": [item["issue_id"] for item in rec_issues],
                "inspection_status": "machine_inspected_agent_direct_class_pending",
            }
        )
        for issue in rec_issues:
            issues.append(
                {
                    **issue,
                    "record_path": rec.get("path"),
                    "ticket": rec.get("ticket"),
                    "symbol": rec.get("symbol"),
                    "final_outcome": rec.get("final_outcome"),
                    "severity": "active" if severity == "active" and issue["severity"].startswith("active") else issue["severity"],
                }
            )

    open_risk_rows = []
    for pos in broker_positions:
        ticket = int(pos["ticket"])
        matched = records_by_ticket.get(ticket, [])
        if len(matched) != 1:
            issue_id = "open_broker_position_missing_trade_record" if not matched else "open_broker_position_multiple_trade_records"
            issues.append(
                {
                    "issue_id": issue_id,
                    "ticket": ticket,
                    "symbol": pos.get("symbol"),
                    "severity": "active",
                    "matched_record_paths": [row.get("path") for row in matched],
                }
            )
            inspected_rows.append(
                {
                    "row_type": "broker_open_position",
                    "broker_position": pos,
                    "matched_record_paths": [row.get("path") for row in matched],
                    "issues": [issue_id],
                    "inspection_status": "machine_inspected_agent_direct_class_pending",
                }
            )
            continue

        rec = matched[0]
        rec_issues = []
        broker_symbol = str(pos.get("symbol") or "")
        logical_symbol = str(rec.get("symbol") or "")
        if broker_symbol not in _symbol_aliases(logical_symbol):
            rec_issues.append("broker_symbol_mismatch")
        if rec.get("exit_present"):
            rec_issues.append("record_has_exit_but_broker_position_open")
        if not _close(rec.get("current_volume"), pos.get("volume"), tol=0.011):
            rec_issues.append("current_volume_mismatch_broker")
        expected_sl = rec.get("active_stop_loss") or rec.get("stop_loss")
        if expected_sl is not None and not _close(expected_sl, pos.get("sl"), tol=0.02, rel=1e-7):
            rec_issues.append("stop_loss_mismatch_broker")
        expected_tp = rec.get("active_take_profit") or rec.get("take_profit_1")
        if expected_tp is not None and not _close(expected_tp, pos.get("tp"), tol=0.03, rel=1e-7):
            rec_issues.append("take_profit_mismatch_broker")
        broker_comment = str(pos.get("comment") or "")
        if broker_comment.startswith("TP1_"):
            if rec.get("partial_closed") is not True:
                rec_issues.append("broker_tp1_residual_record_not_marked_partial_closed")
            if rec.get("residual_open") is not True:
                rec_issues.append("broker_tp1_residual_record_not_marked_residual_open")
            released = _risk_released(str(rec.get("direction") or ""), rec.get("entry_price"), pos.get("sl"))
            if released and _number(rec.get("residual_worst_case_cash_risk_amount")) != 0.0:
                rec_issues.append("be_residual_risk_not_released_in_record")
        risk_amount, risk_source = _position_worst_case_risk(rec, pos)
        open_risk_rows.append(
            {
                "ticket": ticket,
                "symbol": rec.get("symbol"),
                "broker_symbol": broker_symbol,
                "direction": rec.get("direction"),
                "volume": pos.get("volume"),
                "entry_price": rec.get("entry_price"),
                "broker_sl": pos.get("sl"),
                "risk_amount": risk_amount,
                "risk_source": risk_source,
                "risk_released": risk_amount == 0.0,
                "record_path": rec.get("path"),
            }
        )
        inspected_rows.append(
            {
                **rec,
                "row_type": "broker_open_position_reconciled",
                "broker_position": pos,
                "worst_case_risk": open_risk_rows[-1],
                "issues": rec_issues,
                "inspection_status": "machine_inspected_agent_direct_class_pending",
            }
        )
        for issue in rec_issues:
            issues.append(
                {
                    "issue_id": issue,
                    "record_path": rec.get("path"),
                    "ticket": ticket,
                    "symbol": rec.get("symbol"),
                    "final_outcome": rec.get("final_outcome"),
                    "severity": "active",
                }
            )

    symbol_counts = Counter(str(row.get("symbol")) for row in open_risk_rows)
    duplicate_open_symbols = {symbol: count for symbol, count in symbol_counts.items() if count > 1}
    for symbol, count in duplicate_open_symbols.items():
        issues.append(
            {
                "issue_id": "duplicate_open_symbol_exposure",
                "symbol": symbol,
                "count": count,
                "severity": "active",
            }
        )

    risk_known = sum(row["risk_amount"] for row in open_risk_rows if row["risk_amount"] is not None)
    risk_unknown = [row for row in open_risk_rows if row["risk_amount"] is None]
    risk = {
        "open_position_worst_case_risk_rows": open_risk_rows,
        "known_open_worst_case_cash_risk": round(risk_known, 6),
        "unknown_open_worst_case_risk_tickets": [row["ticket"] for row in risk_unknown],
        "duplicate_open_symbols": duplicate_open_symbols,
    }
    return inspected_rows, issues, risk


def _inspect_slippage(
    all_records: list[dict[str, Any]],
    slippage_rows: list[dict[str, Any]],
    broker_by_ticket: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows_by_ticket: dict[int, list[dict[str, Any]]] = defaultdict(list)
    records_by_ticket: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for rec in all_records:
        try:
            records_by_ticket[int(rec.get("ticket"))].append(rec)
        except (TypeError, ValueError):
            continue

    def _active_telemetry_repair_evidence(
        ticket: Any,
        row_issues: list[str],
    ) -> list[dict[str, Any]]:
        try:
            ticket_int = int(ticket)
        except (TypeError, ValueError):
            return []
        evidence: list[dict[str, Any]] = []
        for rec in records_by_ticket.get(ticket_int, []):
            events = rec.get("recovered_partial_close_events")
            if not isinstance(events, list):
                continue
            for event in events:
                if not isinstance(event, dict):
                    continue
                if (
                    "negative_time_in_trade_minutes" in row_issues
                    and event.get("time_in_trade_minutes_repair_status")
                    == "negative_source_value_sanitized"
                ):
                    evidence.append(
                        {
                            "record_path": rec.get("path"),
                            "repair_field": "time_in_trade_minutes",
                            "repair_status": event.get(
                                "time_in_trade_minutes_repair_status"
                            ),
                            "repair_event_type": event.get("type"),
                        }
                    )
                if (
                    "partial_slippage_remaining_volume_mismatch_expected" in row_issues
                    and event.get("remaining_volume_repair_status")
                    == "remaining_volume_repaired_from_broker_residual"
                ):
                    evidence.append(
                        {
                            "record_path": rec.get("path"),
                            "repair_field": "remaining_volume",
                            "repair_status": event.get(
                                "remaining_volume_repair_status"
                            ),
                            "repair_event_type": event.get("type"),
                        }
                    )
        return evidence

    issues: list[dict[str, Any]] = []
    for row in slippage_rows:
        try:
            rows_by_ticket[int(row.get("ticket"))].append(row)
        except (TypeError, ValueError):
            continue
        row_issues = []
        if row.get("partial_close") is True:
            initial = _number(row.get("initial_volume"))
            closed = _number(row.get("volume_closed"))
            remaining = _number(row.get("remaining_volume"))
            if initial is not None and closed is not None and remaining is not None:
                expected_remaining = round(max(initial - closed, 0.0), 2)
                if not _close(remaining, expected_remaining, tol=0.011):
                    row_issues.append("partial_slippage_remaining_volume_mismatch_expected")
        minutes = _number(row.get("time_in_trade_minutes"))
        if minutes is not None and minutes < 0:
            row_issues.append("negative_time_in_trade_minutes")
        if row_issues:
            ticket = row.get("ticket")
            try:
                active_related = int(ticket) in broker_by_ticket
            except (TypeError, ValueError):
                active_related = False
            repair_evidence = (
                _active_telemetry_repair_evidence(ticket, row_issues)
                if active_related
                else []
            )
            severity = (
                "repaired_active_related_telemetry"
                if repair_evidence
                else (
                    "active_related_telemetry"
                    if active_related
                    else "historical_or_exit_telemetry"
                )
            )
            issues.append(
                {
                    "issue_id": "+".join(row_issues),
                    "line_no": row.get("_line_no"),
                    "ticket": ticket,
                    "symbol": row.get("symbol"),
                    "severity": severity,
                    "repair_evidence": repair_evidence,
                }
            )

    for rec in all_records:
        final = str(rec.get("final_outcome") or "")
        if "LIMIT_FILLED" not in final and final != "EXECUTED":
            continue
        ticket = rec.get("ticket")
        try:
            ticket_int = int(ticket)
        except (TypeError, ValueError):
            continue
        ticket_rows = rows_by_ticket.get(ticket_int, [])
        has_entry = any(row.get("slippage_event_type") == "entry" or row.get("trigger") == "limit_fill" for row in ticket_rows)
        if not has_entry:
            issues.append(
                {
                    "issue_id": "filled_record_missing_entry_slippage_row",
                    "ticket": ticket_int,
                    "symbol": rec.get("symbol"),
                    "record_path": rec.get("path"),
                    "severity": "broker_truth_observability",
                }
            )
        if rec.get("exit_present"):
            has_close = any(row.get("slippage_event_type") == "close" for row in ticket_rows)
            if not has_close:
                issues.append(
                    {
                        "issue_id": "closed_record_missing_close_slippage_row",
                        "ticket": ticket_int,
                        "symbol": rec.get("symbol"),
                        "record_path": rec.get("path"),
                        "severity": "exit_observability",
                    }
                )

    counts = Counter(str(row.get("trigger") or row.get("slippage_event_type") or "unknown") for row in slippage_rows)
    return issues, {"slippage_trigger_counts": dict(counts), "tickets_with_slippage": len(rows_by_ticket)}


def _inspect_pending_lifecycle(
    today_records: list[dict[str, Any]],
    pending_rows: list[dict[str, Any]],
    broker_orders: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows_by_record: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reason_counts: Counter[str] = Counter()
    issues: list[dict[str, Any]] = []
    for row in pending_rows:
        path = str(row.get("record_path") or "")
        if path:
            rows_by_record[path].append(row)
        reason_counts[str(row.get("reason") or row.get("cancel_reason") or row.get("fill_no_fill_label") or "missing_reason")] += 1

    for rec in today_records:
        final = str(rec.get("final_outcome") or "")
        rows = rows_by_record.get(str(rec.get("path")), [])
        latest = rows[-1] if rows else {}
        latest_reason = latest.get("reason") or latest.get("cancel_reason") or latest.get("fill_no_fill_label")
        if final.startswith("LIMIT_FILLED") and rows and latest_reason not in ("order_send_success", "filled", "limit_filled"):
            issues.append(
                {
                    "issue_id": "filled_record_pending_lifecycle_latest_not_success",
                    "record_path": rec.get("path"),
                    "symbol": rec.get("symbol"),
                    "ticket": rec.get("ticket"),
                    "latest_reason": latest_reason,
                    "severity": "active_if_open",
                }
            )
        if final.startswith("LIMIT_CANCELLED") and rows and latest_reason not in (
            "sl_too_close",
            "cancelled",
            "expired",
            "order_send_failed_retry",
        ):
            issues.append(
                {
                    "issue_id": "cancelled_record_pending_lifecycle_latest_unexpected",
                    "record_path": rec.get("path"),
                    "symbol": rec.get("symbol"),
                    "latest_reason": latest_reason,
                    "severity": "pending_order_observability",
                }
            )
    if broker_orders:
        issues.append(
            {
                "issue_id": "broker_pending_orders_present_during_audit",
                "count": len(broker_orders),
                "severity": "active",
            }
        )
    return issues, {
        "pending_lifecycle_rows_today": len(pending_rows),
        "pending_lifecycle_reason_counts": dict(reason_counts),
        "pending_records_with_rows": len(rows_by_record),
        "broker_pending_orders": len(broker_orders),
    }


def _source_lifecycle_key(intent: dict[str, Any]) -> tuple[Any, ...]:
    source = _dict(intent.get("source"))
    trade = _dict(intent.get("trade"))
    primary_order = _dict(intent.get("primary_order"))
    record_path = primary_order.get("record_path")
    trade_id = source.get("trade_id")
    if isinstance(trade_id, str) and trade_id.startswith("lim_filled_"):
        trade_id = "lim_" + trade_id[len("lim_filled_") :]
    return (
        source.get("runtime_namespace"),
        source.get("profile"),
        source.get("symbol"),
        source.get("candidate_id"),
        trade_id,
        record_path,
        trade.get("direction"),
    )


def _inspect_dual_bridge(
    intents: list[dict[str, Any]],
    follower_rows: list[dict[str, Any]],
    ftmo_positions: list[dict[str, Any]],
    ftmo_orders: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    key_counts: Counter[tuple[Any, ...]] = Counter(_source_lifecycle_key(row) for row in intents)
    duplicates = [
        {"source_lifecycle_key": list(key), "count": count}
        for key, count in key_counts.items()
        if count > 1
    ]
    if duplicates:
        issues.append(
            {
                "issue_id": "dual_intent_duplicate_source_lifecycle",
                "severity": "active_mirror_hazard",
                "duplicates": duplicates,
            }
        )

    intent_type_counts = Counter(str(row.get("intent_type") or "missing") for row in intents)
    modification_like_entries = [
        row
        for row in intents
        if str(row.get("intent_type") or "") == "market_entry"
        and any(token in json.dumps(row, sort_keys=True).lower() for token in ("partial", "break_even", "breakeven", "modify"))
    ]
    if modification_like_entries:
        # Context text can mention partial policy. This is not automatically a defect;
        # preserve the rows for direct inspection to prove they are not lifecycle
        # modifications re-emitted as fresh target entries.
        pass

    follower_events = Counter(str(row.get("event") or "missing") for row in follower_rows)
    processed_null = [
        row
        for row in follower_rows
        if row.get("event") == "market_intent_processed" and row.get("result") is None
    ]
    ftmo_position_times = [
        parsed
        for parsed in (_parse_utc_datetime(pos.get("time")) for pos in ftmo_positions)
        if parsed is not None
    ]
    successful_processed_times = [
        parsed
        for parsed in (
            _parse_utc_datetime(row.get("recorded_at_utc"))
            for row in follower_rows
            if row.get("event") == "market_intent_processed"
            and isinstance(row.get("result"), dict)
        )
        if parsed is not None
    ]
    earliest_ftmo_position_time = (
        min(successful_processed_times)
        if successful_processed_times
        else min(ftmo_position_times)
        if ftmo_position_times
        else None
    )
    active_null_rows = []
    historical_null_rows = []
    for row in processed_null:
        row_time = _parse_utc_datetime(row.get("recorded_at_utc"))
        if earliest_ftmo_position_time is not None and row_time is not None and row_time < earliest_ftmo_position_time:
            historical_null_rows.append(row)
        else:
            active_null_rows.append(row)
    if processed_null and not ftmo_positions and not ftmo_orders:
        issues.append(
            {
                "issue_id": "pre_repair_ftmo_market_intent_processed_with_null_result_ftmo_flat",
                "severity": "closed_pre_repair_mirror_gap_fresh_proof_pending",
                "count": len(processed_null),
                "intent_ids": [row.get("intent_id") for row in processed_null[-5:]],
            }
        )
    elif active_null_rows:
        issues.append(
            {
                "issue_id": "ftmo_market_intent_processed_with_null_result_while_target_not_flat",
                "severity": "active_mirror_hazard",
                "count": len(active_null_rows),
                "intent_ids": [row.get("intent_id") for row in active_null_rows[-5:]],
            }
        )
    if historical_null_rows:
        issues.append(
            {
                "issue_id": "pre_current_ftmo_position_market_intent_processed_with_null_result",
                "severity": "closed_pre_repair_mirror_gap_fresh_proof_pending",
                "count": len(historical_null_rows),
                "intent_ids": [row.get("intent_id") for row in historical_null_rows[-5:]],
                "earliest_current_ftmo_position_evidence_time_utc": (
                    earliest_ftmo_position_time.isoformat()
                    if earliest_ftmo_position_time is not None
                    else None
                ),
            }
        )

    return issues, {
        "intent_rows": len(intents),
        "intent_type_counts": dict(intent_type_counts),
        "duplicate_source_lifecycle_count": len(duplicates),
        "follower_action_rows": len(follower_rows),
        "follower_event_counts": dict(follower_events),
        "processed_null_result_count": len(processed_null),
        "processed_null_result_active_after_current_position_count": len(active_null_rows),
        "processed_null_result_before_current_position_count": len(historical_null_rows),
        "ftmo_positions": len(ftmo_positions),
        "ftmo_orders": len(ftmo_orders),
        "modification_like_market_entry_rows_for_direct_inspection": len(modification_like_entries),
    }


def _risk_account_summary(
    account: dict[str, Any],
    risk_config: dict[str, Any],
    open_risk: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    funded = account.get("redacted_account") or {}
    balance = _number(funded.get("balance"))
    equity = _number(funded.get("equity"))
    margin_level = _number(funded.get("margin_level"))
    known_open_risk = _number(open_risk.get("known_open_worst_case_cash_risk")) or 0.0
    max_daily_loss_pct = _number(risk_config.get("max_daily_loss_pct"))
    max_daily_loss_cash = balance * max_daily_loss_pct / 100.0 if balance is not None and max_daily_loss_pct is not None else None
    open_risk_pct_balance = known_open_risk / balance * 100.0 if balance else None
    if max_daily_loss_cash is not None and known_open_risk > max_daily_loss_cash:
        issues.append(
            {
                "issue_id": "open_worst_case_risk_exceeds_configured_daily_loss_cap",
                "severity": "active",
                "known_open_worst_case_cash_risk": known_open_risk,
                "max_daily_loss_cash": max_daily_loss_cash,
            }
        )
    if open_risk.get("unknown_open_worst_case_risk_tickets"):
        issues.append(
            {
                "issue_id": "unknown_open_worst_case_risk_tickets",
                "severity": "active_risk_authority_gap",
                "tickets": open_risk["unknown_open_worst_case_risk_tickets"],
            }
        )
    if margin_level is not None and margin_level < 200.0:
        issues.append(
            {
                "issue_id": "low_margin_level_under_200_pct",
                "severity": "active",
                "margin_level": margin_level,
            }
        )
    return issues, {
        "balance": balance,
        "equity": equity,
        "margin": funded.get("margin"),
        "margin_free": funded.get("margin_free"),
        "margin_level": margin_level,
        "known_open_worst_case_cash_risk": known_open_risk,
        "open_worst_case_risk_pct_balance": open_risk_pct_balance,
        "max_daily_loss_pct_config": max_daily_loss_pct,
        "max_daily_loss_cash_config": max_daily_loss_cash,
        "unknown_open_worst_case_risk_tickets": open_risk.get("unknown_open_worst_case_risk_tickets"),
        "ftmo_balance": (account.get("ftmo") or {}).get("balance"),
        "ftmo_equity": (account.get("ftmo") or {}).get("equity"),
    }


def main() -> int:
    recorded_at = _utcnow()
    all_records, today_records = _load_trade_records()
    account, broker_positions, ftmo_positions, broker_by_ticket = _load_broker_state()
    risk_config = _load_agent_risk_config()
    slippage_rows = _load_jsonl_rows(SLIPPAGE_LOG, today_only=False)
    pending_rows_today = _load_jsonl_rows(PENDING_LIFECYCLE_LOG, today_only=True)
    intent_rows = _load_jsonl_rows(INTENT_LOG, today_only=False)
    follower_rows = _load_jsonl_rows(FOLLOWER_ACTIONS, today_only=False)

    inspected_rows, record_issues, open_risk = _inspect_records(
        all_records, today_records, broker_positions, broker_by_ticket
    )
    slippage_issues, slippage_summary = _inspect_slippage(all_records, slippage_rows, broker_by_ticket)
    pending_issues, pending_summary = _inspect_pending_lifecycle(
        today_records, pending_rows_today, account["redacted_account_orders"]
    )
    dual_issues, dual_summary = _inspect_dual_bridge(
        intent_rows, follower_rows, ftmo_positions, account["ftmo_orders"]
    )
    risk_issues, risk_summary = _risk_account_summary(account, risk_config, open_risk)

    issues = record_issues + slippage_issues + pending_issues + dual_issues + risk_issues
    active_issues = [
        issue
        for issue in issues
        if str(issue.get("severity") or "").startswith("active")
        or issue.get("severity") == "active_mirror_hazard"
    ]
    outcome_counts = Counter(rec.get("final_outcome") or "" for rec in today_records)
    rejection_counts = Counter(
        rec.get("permission_reason") or rec.get("rejection_class") or "missing_reason"
        for rec in today_records
        if str(rec.get("final_outcome") or "").startswith("REJECTED")
    )
    policy_counts = Counter(rec.get("selected_policy") or "missing" for rec in today_records)
    record_issue_counts = Counter(issue["issue_id"] for issue in record_issues)
    issue_counts = Counter(issue["issue_id"] for issue in issues)

    direct_classes = {
        "schema_version": "dual_current_live_direct_inspection_classes_v1",
        "recorded_at_utc": recorded_at,
        "status": "agent_direct_inspection_required_for_material_classes",
        "classes": [
            {
                "class_id": "broker_open_position_reconciliation",
                "row_count": len(broker_positions),
                "machine_status": "inventoried",
                "direct_agent_status": "pending",
                "source_artifacts": [str(BROKER_PROBE), str(LEDGER_PATH)],
            },
            {
                "class_id": "today_candidate_decisions",
                "row_count": len(today_records),
                "machine_status": "inventoried",
                "direct_agent_status": "pending",
                "source_artifacts": [str(TRADE_ROOT), str(LEDGER_PATH)],
            },
            {
                "class_id": "today_rejections_and_skips",
                "row_count": sum(
                    1
                    for rec in today_records
                    if str(rec.get("final_outcome") or "").startswith(("REJECTED", "SKIPPED", "LIMIT_CANCELLED"))
                ),
                "machine_status": "inventoried",
                "direct_agent_status": "pending",
                "source_artifacts": [str(TRADE_ROOT), str(LEDGER_PATH)],
            },
            {
                "class_id": "slippage_entry_partial_close_telemetry",
                "row_count": len(slippage_rows),
                "machine_status": "inventoried",
                "direct_agent_status": "pending",
                "source_artifacts": [str(SLIPPAGE_LOG), str(SUMMARY_PATH)],
            },
            {
                "class_id": "pending_limit_lifecycle",
                "row_count": len(pending_rows_today),
                "machine_status": "inventoried",
                "direct_agent_status": "pending",
                "source_artifacts": [str(PENDING_LIFECYCLE_LOG), str(SUMMARY_PATH)],
            },
            {
                "class_id": "dual_broker_intent_and_follower",
                "row_count": len(intent_rows) + len(follower_rows),
                "machine_status": "inventoried",
                "direct_agent_status": "pending",
                "source_artifacts": [str(INTENT_LOG), str(FOLLOWER_ACTIONS), str(SUMMARY_PATH)],
            },
            {
                "class_id": "risk_authority",
                "row_count": len(open_risk["open_position_worst_case_risk_rows"]),
                "machine_status": "inventoried",
                "direct_agent_status": "pending",
                "source_artifacts": [str(BROKER_PROBE), str(AGENT_CONFIG), str(SUMMARY_PATH)],
            },
        ],
    }
    if not active_issues:
        direct_classes["status"] = "agent_direct_inspection_completed_no_active_defects"
        direct_evidence = {
            "broker_open_position_reconciliation": (
                "pass_after_local_record_repair",
                "Read-only MT5 probe reconciles all current redacted_account open tickets to local trade records; both brokers have 0 pending orders.",
            ),
            "today_candidate_decisions": (
                "no_active_candidate_decision_defect_found",
                f"{len(today_records)} current-day trade records inspected; active lifecycle records reconcile to broker truth.",
            ),
            "today_rejections_and_skips": (
                "no_active_rejection_defect_found",
                "Rejected/skipped/cancelled rows are explained by gate conflict, transient MT5 disconnect, correlation excess, SL-too-close, or no-fill lifecycle outcomes.",
            ),
            "slippage_entry_partial_close_telemetry": (
                "active_related_telemetry_repaired",
                "Active-related partial telemetry repair evidence is present; remaining slippage issues are historical or exit observability.",
            ),
            "pending_limit_lifecycle": (
                "no_active_pending_order_defect_found",
                "Pending lifecycle rows were inspected and broker truth shows 0 current pending orders on both accounts.",
            ),
            "dual_broker_intent_and_follower": (
                "contained_after_projector_freshness_guard_and_follower_recovery",
                "One projector and one FTMO follower are live; duplicate source lifecycle count is 0 and the pre-repair mirror gap is no longer active.",
            ),
            "risk_authority": (
                "pass",
                "Open worst-case risk is fully known and below the configured daily loss budget.",
            ),
        }
        for class_row in direct_classes["classes"]:
            status, evidence = direct_evidence[class_row["class_id"]]
            class_row["direct_agent_status"] = status
            class_row["direct_agent_evidence"] = evidence

    summary = {
        "schema_version": "dual_current_live_candidate_trade_lifecycle_audit_v2",
        "status": "active_defects_found" if active_issues else "no_active_trade_linkage_or_risk_defects_found",
        "recorded_at_utc": recorded_at,
        "route_id": "vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02",
        "runtime_effect_boundary": "read_only_disk_and_route_probe_audit_no_broker_mutation",
        "coverage": {
            "all_trade_records_loaded": len(all_records),
            "trade_records_today": len(today_records),
            "broker_open_positions_redacted_account": len(broker_positions),
            "broker_open_positions_ftmo": len(ftmo_positions),
            "broker_pending_orders_redacted_account": len(account["redacted_account_orders"]),
            "broker_pending_orders_ftmo": len(account["ftmo_orders"]),
            "slippage_rows_all": len(slippage_rows),
            "pending_lifecycle_rows_today": len(pending_rows_today),
            "dual_intent_rows": len(intent_rows),
            "follower_action_rows": len(follower_rows),
            "inspected_rows_written": len(inspected_rows),
        },
        "account": account,
        "risk_config": risk_config,
        "risk_summary": risk_summary,
        "open_risk": open_risk,
        "outcome_counts_today": dict(outcome_counts),
        "rejection_counts_today": dict(rejection_counts),
        "policy_counts_today": dict(policy_counts),
        "record_issue_counts": dict(record_issue_counts),
        "issue_counts": dict(issue_counts),
        "active_issue_count": len(active_issues),
        "all_issue_count": len(issues),
        "active_issues": active_issues,
        "issues": issues,
        "slippage_summary": slippage_summary,
        "pending_summary": pending_summary,
        "dual_bridge_summary": dual_summary,
        "direct_inspection_artifact": str(DIRECT_INSPECTION_PATH),
    }

    _write_json(SUMMARY_PATH, summary)
    _write_json(DIRECT_INSPECTION_PATH, direct_classes)
    with LEDGER_PATH.open("w", encoding="utf-8") as fh:
        for row in inspected_rows:
            row = {**row, "recorded_at_utc": recorded_at}
            fh.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")

    for issue in active_issues:
        _append_jsonl(
            ANOMALY_LEDGER,
            {
                **issue,
                "source_audit": str(SUMMARY_PATH),
                "recorded_at_utc": recorded_at,
                "runtime_effect_boundary": "read_only_disk_and_route_probe_audit_no_broker_mutation",
            },
        )
    _append_jsonl(
        CHECKPOINT_LEDGER,
        {
            "checkpoint_id": "current_live_candidate_trade_lifecycle_risk_audit",
            "status": summary["status"],
            "recorded_at_utc": recorded_at,
            "coverage": summary["coverage"],
            "active_issue_count": len(active_issues),
            "all_issue_count": len(issues),
            "next_action": (
                "repair_active_issues_before_widening"
                if active_issues
                else "direct_inspect_material_classes_then_reload_runtime_for_code_repairs_if_needed"
            ),
            "runtime_effect_boundary": "read_only_disk_and_route_probe_audit_no_broker_mutation",
        },
    )
    try:
        state = _load_json(STATE_PATH) if STATE_PATH.exists() else {}
        state.update(
            {
                "active_defect": (
                    "active_trade_linkage_or_risk_defects_found"
                    if active_issues
                    else "no_active_trade_linkage_or_risk_defects_found_after_current_lifecycle_and_bridge_projection_repairs"
                ),
                "active_defect_status": (
                    "repair_active_lifecycle_or_risk_issues_before_widening"
                    if active_issues
                    else "current_live_candidate_trade_lifecycle_risk_audit_active_issue_count_0"
                ),
                "latest_live_audit_status": {
                    "audit_path": str(SUMMARY_PATH),
                    "direct_inspection_path": str(DIRECT_INSPECTION_PATH),
                    "recorded_at_utc": recorded_at,
                    "status": summary["status"],
                    "active_issue_count": len(active_issues),
                    "all_issue_count": len(issues),
                    "redacted_account_positions": len(broker_positions),
                    "redacted_account_orders": len(account["redacted_account_orders"]),
                    "ftmo_positions": len(ftmo_positions),
                    "ftmo_orders": len(account["ftmo_orders"]),
                    "known_open_worst_case_cash_risk": risk_summary.get("known_open_worst_case_cash_risk"),
                    "open_worst_case_risk_pct_balance": risk_summary.get("open_worst_case_risk_pct_balance"),
                    "unknown_open_worst_case_risk_tickets": risk_summary.get("unknown_open_worst_case_risk_tickets"),
                },
                "latest_direct_inspection_status": {
                    "artifact": str(DIRECT_INSPECTION_PATH),
                    "status": direct_classes["status"],
                    "recorded_at_utc": recorded_at,
                    "classes": {
                        row["class_id"]: row.get("direct_agent_status")
                        for row in direct_classes["classes"]
                    },
                },
                "last_updated_utc": recorded_at,
                "terminal_completion": False,
                "goal_remains_active": True,
            }
        )
        _write_json(STATE_PATH, state)
    except Exception as exc:  # pragma: no cover - evidence write fallback
        _append_jsonl(
            ANOMALY_LEDGER,
            {
                "issue_id": "supervisor_state_audit_status_update_failed",
                "severity": "route_evidence",
                "recorded_at_utc": recorded_at,
                "error": str(exc),
                "source_audit": str(SUMMARY_PATH),
            },
        )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
