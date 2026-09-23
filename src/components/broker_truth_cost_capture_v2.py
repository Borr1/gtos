"""Default-off broker truth and cost capture helpers.

The functions here build append-only lifecycle rows from caller-supplied MT5
snapshots. They do not call MT5, place/modify/close orders, mutate live
configuration, or make network calls.
"""

from __future__ import annotations

import hashlib
import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.utils.broker_profile import broker_account_namespace, sanitize_namespace


SCHEMA_VERSION = "broker_truth_cost_capture_v2_lifecycle_row_v1"
READONLY_EXPORT_SCHEMA_VERSION = "broker_truth_cost_capture_v2_readonly_export_manifest_v1"
DEFAULT_LOG_PATH = Path("shadow_logs/broker_truth_cost_capture_v2.jsonl")

BROKER_REAL_STATES = {
    "BROKER_REAL",
    "BROKER_READONLY_SNAPSHOT",
    "PROSPECTIVE_CAPTURE",
    "SOURCE_GAP",
    "PROXY_ONLY",
}

TICKET_BOUND_EVENTS = {
    "order_request",
    "order_result",
    "entry_fill",
    "deal",
    "position_snapshot",
    "partial_close",
    "residual_position",
    "modify_request",
    "modify_result",
    "rejection",
    "close",
    "cost",
    "manual_client_intervention",
    "false_local_close",
    "telegram_parity",
}

PROJECTION_FIELD_NAMES = {
    "projected_pnl",
    "projected_profit",
    "projected_r",
    "local_projected_r",
    "local_risk_dollar_projection",
    "synthetic_r",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _object_snapshot(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return dict(value)
    fields = getattr(value, "_fields", None)
    if fields:
        return {field: getattr(value, field, None) for field in fields}
    if hasattr(value, "_asdict"):
        try:
            return dict(value._asdict())
        except Exception:  # noqa: BLE001 - snapshotting must stay best-effort
            return None
    if hasattr(value, "__dict__"):
        return {
            key: item
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return None


def order_result_snapshot(result: Any) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "success": bool(getattr(result, "success", False)),
        "retcode": getattr(result, "retcode", None),
        "retcode_external": getattr(result, "retcode_external", None),
        "request_id": getattr(result, "request_id", None),
        "comment": getattr(result, "comment", None),
        "order": getattr(result, "order", None),
        "deal": getattr(result, "deal", None),
        "volume": getattr(result, "volume", None),
        "price": getattr(result, "price", None),
    }


def spread_context_from_tick(tick: Any) -> dict[str, Any]:
    snapshot = _object_snapshot(tick) or {}
    bid = _as_float(snapshot.get("bid"))
    ask = _as_float(snapshot.get("ask"))
    spread = None
    if bid is not None and ask is not None:
        spread = abs(ask - bid)
    return {
        "bid": bid,
        "ask": ask,
        "spread_price": spread,
        "spread_cents": _as_float(snapshot.get("spread_cents")),
        "time_utc": (
            snapshot.get("time").isoformat()
            if hasattr(snapshot.get("time"), "isoformat")
            else snapshot.get("time")
        ),
        "source_state": "CAPTURED" if spread is not None else "SOURCE_GAP",
    }


def stop_freeze_context_from_symbol_info(symbol_info: Any) -> dict[str, Any]:
    snapshot = _object_snapshot(symbol_info) or {}
    keys = [
        "name",
        "trade_stops_level",
        "trade_freeze_level",
        "point",
        "trade_tick_size",
        "trade_tick_value",
        "trade_contract_size",
        "volume_min",
        "volume_max",
        "volume_step",
        "filling_mode",
        "spread",
    ]
    context = {key: snapshot.get(key) for key in keys}
    captured = context.get("trade_stops_level") is not None or context.get("trade_freeze_level") is not None
    context["source_state"] = "CAPTURED" if captured else "SOURCE_GAP"
    return context


def capture_enabled(config: dict[str, Any] | None) -> bool:
    section = (config or {}).get("broker_truth_cost_capture_v2") or {}
    return bool(section.get("enabled") is True)


def capture_log_path(config: dict[str, Any] | None) -> Path:
    section = (config or {}).get("broker_truth_cost_capture_v2") or {}
    configured = section.get("log_path")
    if configured:
        return Path(configured)
    namespace = sanitize_namespace(broker_account_namespace(config))
    if namespace:
        return DEFAULT_LOG_PATH.parent / namespace / DEFAULT_LOG_PATH.name
    return DEFAULT_LOG_PATH


def _ticket_identity_status(row: dict[str, Any]) -> str:
    identifiers = [
        row.get("ticket"),
        row.get("order_id"),
        row.get("deal_id"),
        row.get("position_id"),
    ]
    return "TICKET_BOUND" if any(value not in (None, "", 0) for value in identifiers) else "TICKET_IDENTITY_SOURCE_GAP"


def build_lifecycle_row(
    *,
    lifecycle_event_type: str,
    symbol: str | None,
    broker_symbol: str | None = None,
    source_family: str,
    source_path: str | None = None,
    source_line: int | None = None,
    source_capture_utc: str | None = None,
    broker_real_or_proxy_state: str = "PROSPECTIVE_CAPTURE",
    ticket: int | str | None = None,
    order_id: int | str | None = None,
    deal_id: int | str | None = None,
    position_id: int | str | None = None,
    request: dict[str, Any] | None = None,
    result: Any = None,
    event_time_utc: str | None = None,
    volume: float | None = None,
    fill_price: float | None = None,
    close_price: float | None = None,
    commission: float | None = None,
    swap: float | None = None,
    broker_profit: float | None = None,
    spread_at_action: dict[str, Any] | None = None,
    stop_freeze_context: dict[str, Any] | None = None,
    account_snapshot: dict[str, Any] | None = None,
    false_local_close_classification: str | None = None,
    telegram_parity_status: str | None = None,
    cost_source_reason: str | None = None,
    source_refs: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    capture_time = source_capture_utc or utc_now_iso()
    result_snapshot = order_result_snapshot(result)
    if result_snapshot:
        order_id = order_id if order_id is not None else result_snapshot.get("order")
        deal_id = deal_id if deal_id is not None else result_snapshot.get("deal")
        fill_price = fill_price if fill_price is not None else result_snapshot.get("price")
        volume = volume if volume is not None else result_snapshot.get("volume")
    row = {
        "schema_version": SCHEMA_VERSION,
        "row_id": _stable_hash(
            SCHEMA_VERSION,
            source_family,
            source_path,
            source_line,
            lifecycle_event_type,
            symbol,
            ticket,
            order_id,
            deal_id,
            position_id,
            event_time_utc,
            capture_time,
        ),
        "source_family": source_family,
        "source_path": source_path,
        "source_line": source_line,
        "source_capture_utc": capture_time,
        "event_time_utc": event_time_utc,
        "lifecycle_event_type": lifecycle_event_type,
        "symbol": symbol,
        "broker_symbol": broker_symbol or symbol,
        "ticket": ticket,
        "order_id": order_id,
        "deal_id": deal_id,
        "position_id": position_id,
        "ticket_identity_status": None,
        "broker_real_or_proxy_state": broker_real_or_proxy_state,
        "request": dict(request) if request else None,
        "result": result_snapshot,
        "retcode": (result_snapshot or {}).get("retcode"),
        "retcode_external": (result_snapshot or {}).get("retcode_external"),
        "request_id": (result_snapshot or {}).get("request_id"),
        "volume": volume,
        "fill_price": fill_price,
        "close_price": close_price,
        "commission": commission,
        "swap": swap,
        "broker_profit": broker_profit,
        "spread_at_action": spread_at_action,
        "stop_freeze_context": stop_freeze_context,
        "account_snapshot": account_snapshot,
        "false_local_close_classification": false_local_close_classification,
        "telegram_parity_status": telegram_parity_status,
        "cost_source_reason": cost_source_reason,
        "source_refs": list(source_refs or []),
        "no_leak_status": "POST_DECISION_BROKER_TRUTH_NOT_DECISION_FEATURE",
        "runtime_effect_boundary": "default_off_append_only_capture_no_order_effect",
        "no_execution_effect": True,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }
    if extra:
        row["extra"] = dict(extra)
    row["ticket_identity_status"] = _ticket_identity_status(row)
    row["validation_issues"] = validate_lifecycle_row(row)
    return row


def validate_lifecycle_row(row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    event_type = str(row.get("lifecycle_event_type") or "")
    source_family = str(row.get("source_family") or "")
    broker_state = str(row.get("broker_real_or_proxy_state") or "")
    cost_reason = str(row.get("cost_source_reason") or "")

    if not source_family:
        issues.append("missing_source_family")
    if not (row.get("source_path") or row.get("source_refs")):
        issues.append("missing_source_identity")
    if broker_state not in BROKER_REAL_STATES:
        issues.append(f"invalid_broker_real_or_proxy_state:{broker_state}")
    if event_type in TICKET_BOUND_EVENTS and row.get("ticket_identity_status") != "TICKET_BOUND":
        issues.append("ticket_bound_lifecycle_missing_ticket_order_deal_position_identity")

    lower_source = source_family.lower()
    lower_reason = cost_reason.lower()
    if broker_state in {"BROKER_REAL", "BROKER_READONLY_SNAPSHOT"}:
        if any(name in row for name in PROJECTION_FIELD_NAMES):
            issues.append("projected_pnl_field_present_on_broker_truth_row")
        if "proxy" in lower_source or "projection" in lower_source:
            issues.append("broker_real_row_uses_proxy_or_projection_source_family")
        if "proxy" in lower_reason or "projection" in lower_reason:
            issues.append("broker_real_cost_source_reason_uses_proxy_or_projection")

    has_cost_value = any(
        row.get(field) is not None
        for field in ("commission", "swap", "broker_profit")
    )
    if (event_type == "cost" or has_cost_value) and not cost_reason:
        issues.append("missing_cost_source_reason")

    if event_type == "false_local_close" and not row.get("false_local_close_classification"):
        issues.append("false_local_close_missing_broker_contradiction_classification")

    return issues


def append_lifecycle_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def readonly_export_source_manifest(
    path: Path,
    *,
    source_family: str = "readonly_broker_history_export",
    captured_asof_utc: str | None = None,
) -> dict[str, Any]:
    rows = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for line in handle:
            if line.strip():
                rows += 1
    return {
        "schema_version": READONLY_EXPORT_SCHEMA_VERSION,
        "source_family": source_family,
        "source_path": str(path),
        "source_sha256": sha256_file(path),
        "source_size_bytes": path.stat().st_size,
        "nonempty_line_count": rows,
        "captured_asof_utc": captured_asof_utc or utc_now_iso(),
        "no_broker_access": True,
        "order_calls": 0,
        "paid_data_calls": 0,
        "runtime_effect_boundary": "read_only_export_parse_only_no_broker_mutation",
    }


def _first_present(row: dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return None


def build_lifecycle_row_from_readonly_export(
    raw_row: dict[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_family: str = "readonly_broker_history_export",
    source_capture_utc: str | None = None,
    source_sha256: str | None = None,
) -> dict[str, Any]:
    """Normalize one already-exported broker history row.

    This helper never calls MT5. It converts caller-supplied JSONL/CSV rows into
    the same append-only lifecycle contract used by the default-off live helper.
    """
    deal_id = _first_present(raw_row, ("deal", "deal_id", "history_deal"))
    order_id = _first_present(raw_row, ("order", "order_id", "history_order"))
    position_id = _first_present(raw_row, ("position_id", "position", "position_ticket"))
    ticket = _first_present(raw_row, ("ticket", "order_ticket", "mt5_order_ticket"))
    event_type = _first_present(raw_row, ("lifecycle_event_type", "event_type", "type"))
    if not event_type:
        event_type = "deal" if deal_id else "position_snapshot" if position_id else "order_result"
    commission = _as_float(_first_present(raw_row, ("commission", "commission_fee")))
    swap = _as_float(_first_present(raw_row, ("swap", "swap_fee")))
    profit = _as_float(_first_present(raw_row, ("profit", "broker_profit", "pnl")))
    cost_reason = None
    if any(value is not None for value in (commission, swap, profit)):
        cost_reason = "read_only_broker_history_export"

    return build_lifecycle_row(
        lifecycle_event_type=str(event_type),
        symbol=_first_present(raw_row, ("symbol", "broker_symbol")),
        broker_symbol=_first_present(raw_row, ("broker_symbol", "symbol")),
        source_family=source_family,
        source_path=source_path,
        source_line=source_line,
        source_capture_utc=source_capture_utc,
        broker_real_or_proxy_state="BROKER_READONLY_SNAPSHOT",
        ticket=ticket,
        order_id=order_id,
        deal_id=deal_id,
        position_id=position_id,
        event_time_utc=_first_present(raw_row, ("time_utc", "time", "event_time_utc", "close_time")),
        volume=_as_float(_first_present(raw_row, ("volume", "lots"))),
        fill_price=_as_float(_first_present(raw_row, ("price", "fill_price", "entry_price"))),
        close_price=_as_float(_first_present(raw_row, ("close_price", "exit_price"))),
        commission=commission,
        swap=swap,
        broker_profit=profit,
        cost_source_reason=cost_reason,
        source_refs=[f"{source_path}:{source_line}"],
        extra={
            "readonly_export_source_sha256": source_sha256,
            "raw_field_names": sorted(str(key) for key in raw_row),
        },
    )


def iter_lifecycle_rows_from_readonly_export(
    path: Path,
    *,
    source_family: str = "readonly_broker_history_export",
    source_capture_utc: str | None = None,
) -> Iterable[dict[str, Any]]:
    """Yield normalized lifecycle rows from a local JSONL or CSV export."""
    source_sha = sha256_file(path)
    suffixes = {suffix.lower() for suffix in path.suffixes}
    if ".csv" in suffixes:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for line_no, row in enumerate(reader, 2):
                yield build_lifecycle_row_from_readonly_export(
                    dict(row),
                    source_path=str(path),
                    source_line=line_no,
                    source_family=source_family,
                    source_capture_utc=source_capture_utc,
                    source_sha256=source_sha,
                )
        return

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            yield build_lifecycle_row_from_readonly_export(
                row,
                source_path=str(path),
                source_line=line_no,
                source_family=source_family,
                source_capture_utc=source_capture_utc,
                source_sha256=source_sha,
            )


def record_lifecycle_event_if_enabled(
    config: dict[str, Any] | None,
    **kwargs: Any,
) -> dict[str, Any] | None:
    if not capture_enabled(config):
        return None
    row = build_lifecycle_row(**kwargs)
    append_lifecycle_row(capture_log_path(config), row)
    return row
