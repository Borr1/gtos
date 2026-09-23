"""Route-local no-leak time and as-of contract helpers for vNext Lane02.

This module is research-only. It does not read MT5 directly, place orders, or
change runtime configuration. The helpers are intentionally plain Python so
future feature-store, label-store, and replay builders can import the contract
before any production wiring is proposed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


AVAILABILITY_CLASSES = (
    "pre_candidate",
    "candidate_time",
    "pre_order",
    "post_order",
    "post_fill",
    "post_close",
    "replay_only",
    "label_only",
    "broker_realized",
    "future_outcome",
    "stale_historical",
    "source_metadata",
)

FEATURE_ALLOWED_CLASSES = {
    "pre_candidate",
    "candidate_time",
    "pre_order",
}

LABEL_ALLOWED_CLASSES = {
    "pre_candidate",
    "candidate_time",
    "label_only",
    "broker_realized",
    "future_outcome",
    "post_order",
    "post_fill",
    "post_close",
    "replay_only",
    "source_metadata",
}

REPLAY_DECISION_ALLOWED_CLASSES = {
    "pre_candidate",
    "candidate_time",
    "pre_order",
    "source_metadata",
}

BROKER_TRUTH_ALLOWED_CLASSES = {
    "post_order",
    "post_fill",
    "post_close",
    "broker_realized",
    "source_metadata",
}

UTC = timezone.utc
LONDON_TZ = ZoneInfo("Europe/London")
NEW_YORK_TZ = ZoneInfo("America/New_York")
MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def parse_utc_datetime(value: Any) -> datetime | None:
    """Parse common repo timestamp values into timezone-aware UTC datetimes."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        number = float(value)
        if number <= 0:
            return None
        if number > 10_000_000_000:
            number = number / 1000.0
        try:
            return datetime.fromtimestamp(number, tz=UTC)
        except (OSError, OverflowError, ValueError):
            return None
    else:
        text = str(value).strip()
        if not text or text in {"0", "0.0"}:
            return None
        if text.isdigit():
            return parse_utc_datetime(int(text))
        text = text.replace("Z", "+00:00")
        if " " in text and "T" not in text:
            text = text.replace(" ", "T")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def iso_utc(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value else None


def _time_to_minutes(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def _minutes_to_time(value: int) -> time:
    value = value % (24 * 60)
    return time(hour=value // 60, minute=value % 60)


def _within_minutes(now_minutes: int, start_minutes: int, end_minutes: int) -> bool:
    if start_minutes <= end_minutes:
        return start_minutes <= now_minutes <= end_minutes
    return now_minutes >= start_minutes or now_minutes <= end_minutes


def normalize_symbol(symbol: Any) -> str:
    return str(symbol or "").strip()


def broker_symbol_for(symbol: str, config: dict[str, Any]) -> str:
    instruments = config.get("instruments") if isinstance(config, dict) else {}
    if isinstance(instruments, dict):
        market = ((instruments.get(symbol) or {}).get("market") or {})
        broker = market.get("mt5_symbol") or market.get("symbol")
        if broker:
            return str(broker)
    market = config.get("market") if isinstance(config, dict) else {}
    if isinstance(market, dict) and market.get("mt5_symbol") and market.get("symbol") == symbol:
        return str(market["mt5_symbol"])
    return symbol


def kill_zone_windows_for_symbol(symbol: str, config: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Return UTC kill-zone windows after per-instrument override."""
    base_market = dict(config.get("market") or {})
    instruments = config.get("instruments") or {}
    instrument = instruments.get(symbol) or {}
    market = dict(base_market)
    market.update(instrument.get("market") or {})
    windows = market.get("kill_zones") or base_market.get("kill_zones") or {}
    return {str(name): dict(spec or {}) for name, spec in windows.items()}


def session_for_utc(value: Any, symbol: str, config: dict[str, Any]) -> dict[str, Any]:
    """Classify a UTC timestamp into repo kill-zone and local time views."""
    dt = parse_utc_datetime(value)
    if dt is None:
        return {
            "session": "unknown_session",
            "session_status": "timestamp_unparseable",
            "symbol": normalize_symbol(symbol),
        }
    symbol_key = normalize_symbol(symbol)
    windows = kill_zone_windows_for_symbol(symbol_key, config)
    now_minutes = dt.hour * 60 + dt.minute
    matches: list[dict[str, Any]] = []
    for name, spec in sorted(windows.items()):
        start = str(spec.get("start_utc") or "")
        end = str(spec.get("end_utc") or "")
        if not start or not end:
            continue
        start_minutes = _time_to_minutes(start)
        end_minutes = _time_to_minutes(end)
        if _within_minutes(now_minutes, start_minutes, end_minutes):
            core_end = str(spec.get("core_end_utc") or end)
            core_minutes = _time_to_minutes(core_end)
            in_core = _within_minutes(now_minutes, start_minutes, core_minutes)
            matches.append(
                {
                    "session": name,
                    "start_utc": start,
                    "end_utc": end,
                    "core_end_utc": core_end,
                    "core_status": "core" if in_core else "extended",
                }
            )
    if matches:
        primary = matches[0]
        session = primary["session"]
        status = "inside_configured_session"
    else:
        primary = {}
        session = "off_configured_session"
        status = "outside_configured_session"
    return {
        "broker_symbol": broker_symbol_for(symbol_key, config),
        "date_utc": dt.date().isoformat(),
        "is_crypto_symbol": symbol_key in {"BTCUSD", "ETHUSD"},
        "is_friday": dt.weekday() == 4,
        "london_local": dt.astimezone(LONDON_TZ).isoformat(),
        "malaysia_local": dt.astimezone(MALAYSIA_TZ).isoformat(),
        "matched_windows": matches,
        "new_york_local": dt.astimezone(NEW_YORK_TZ).isoformat(),
        "repo_session_authority": "UTC_CONFIG_KILL_ZONE_WINDOWS",
        "session": session,
        "session_core_status": primary.get("core_status"),
        "session_status": status,
        "symbol": symbol_key,
        "time_utc": dt.time().replace(microsecond=0).isoformat(),
        "timestamp_utc": dt.isoformat(),
    }


def candle_close_for(value: Any, timeframe_minutes: int) -> str | None:
    """Return the close timestamp for the candle containing value."""
    dt = parse_utc_datetime(value)
    if dt is None or timeframe_minutes <= 0:
        return None
    bucket = (dt.minute // timeframe_minutes) * timeframe_minutes
    open_dt = dt.replace(minute=bucket, second=0, microsecond=0)
    if timeframe_minutes >= 60:
        hour_bucket = (dt.hour // (timeframe_minutes // 60)) * (timeframe_minutes // 60)
        open_dt = dt.replace(hour=hour_bucket, minute=0, second=0, microsecond=0)
    close_dt = open_dt + timedelta(minutes=timeframe_minutes)
    return close_dt.astimezone(UTC).isoformat()


def is_friday_close_risk(value: Any, symbol: str) -> bool:
    dt = parse_utc_datetime(value)
    if dt is None:
        return False
    if normalize_symbol(symbol) in {"BTCUSD", "ETHUSD"}:
        return False
    return dt.weekday() == 4 and dt.time() >= time(20, 45)


def _field_text(field_path: str) -> str:
    return field_path.replace(".", "_").replace("[", "_").replace("]", "").lower()


def classify_field(field_path: str, *, source_path: str = "") -> dict[str, Any]:
    """Classify a field by decision-time availability and downstream use."""
    text = _field_text(field_path)
    source = source_path.replace("\\", "/").lower()
    reason = "default_candidate_time_or_non_time_context"
    availability = "candidate_time"

    if any(token in text for token in ("final_r", "net_r", "r_multiple", "expectancy", "win_rate", "profit_factor")):
        availability = "label_only"
        reason = "outcome_or_result_metric"
    if any(token in text for token in ("outcome", "result", "winner", "loser", "mfe", "mae", "adverse", "favorable")):
        availability = "future_outcome"
        reason = "path_or_outcome_label"
    if any(token in text for token in ("exit_time", "close_time", "closed_at", "timestamp_closed", "time_closed", "close_deal")):
        availability = "post_close"
        reason = "close_or_exit_timestamp"
    if any(token in text for token in ("fill_time", "filled_at", "entry_deal", "deal_ticket", "time_msc_utc")):
        availability = "post_fill"
        reason = "fill_or_deal_timestamp"
    if any(token in text for token in ("order_ticket", "order_result", "time_setup", "time_done", "pending_order", "position_id")):
        availability = "post_order"
        reason = "order_or_position_lifecycle_field"
    if any(token in text for token in ("commission", "swap", "fee", "slippage", "broker_profit", "broker_net", "broker_realized")):
        availability = "broker_realized"
        reason = "broker_realized_cost_or_pnl"
    if any(token in text for token in ("generated_at", "captured_at", "updated_at", "source_hash", "sha256", "mtime", "file_size", "line_count")):
        availability = "source_metadata"
        reason = "source_capture_or_file_metadata"
    if any(token in text for token in ("created_at", "logged_at", "recorded_at", "utc")) and availability == "candidate_time":
        availability = "source_metadata"
        reason = "log_write_or_generic_utc_timestamp_requires_asof_check"
    if any(token in text for token in ("decision_time", "candidate_time", "source_time", "candle_time", "candle_close", "entry_signal_time")):
        availability = "candidate_time"
        reason = "decision_or_candidate_clock"
    if any(token in text for token in ("pre_ai", "gate0", "gate1", "m15", "h1", "h4", "d1", "spread_at_decision", "bid_at_decision", "ask_at_decision")):
        availability = "pre_order"
        reason = "pre_order_decision_context"
    if any(token in text for token in ("session", "kill_zone", "symbol", "framework", "origin", "side", "route_id")) and availability == "candidate_time":
        availability = "pre_candidate"
        reason = "identity_or_session_key_available_before_scoring"
    if "replay" in text and availability in {"candidate_time", "source_metadata"}:
        availability = "replay_only"
        reason = "replay_artifact_or_counterfactual_field"
    if "historical" in text or "stage04" in source or "archive" in source:
        if availability in {"candidate_time", "source_metadata"}:
            availability = "stale_historical"
            reason = "historical_artifact_requires_source_asof_recheck_before_feature_use"
    if "broker" in source and availability in {"candidate_time", "source_metadata"}:
        availability = "broker_realized"
        reason = "broker_history_source_field"

    return {
        "availability_class": availability,
        "classification_reason": reason,
        "feature_store_allowed": availability in FEATURE_ALLOWED_CLASSES,
        "label_store_allowed": availability in LABEL_ALLOWED_CLASSES,
        "replay_decision_allowed": availability in REPLAY_DECISION_ALLOWED_CLASSES,
        "broker_truth_allowed": availability in BROKER_TRUTH_ALLOWED_CLASSES,
    }


def flatten_mapping(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten_mapping(child, child_prefix)
    elif isinstance(value, list):
        if not value:
            yield prefix, []
        else:
            for child in value:
                yield from flatten_mapping(child, f"{prefix}[]")
    else:
        yield prefix, value


def canonical_key(row: dict[str, Any], *, route_id: str | None = None, source_path: str | None = None) -> dict[str, Any]:
    """Build the canonical cross-store key policy for a candidate/order row."""
    symbol = normalize_symbol(row.get("symbol") or row.get("source_symbol") or row.get("candidate_symbol"))
    broker_symbol = normalize_symbol(row.get("broker_symbol")) or symbol
    candidate_time = (
        row.get("candidate_time_utc")
        or row.get("decision_time_utc")
        or row.get("source_time_utc")
        or row.get("candle_time_utc")
        or row.get("time_utc")
    )
    candle_time = row.get("candle_time_utc") or row.get("source_time_utc") or candidate_time
    return {
        "broker_symbol": broker_symbol,
        "candidate_time_utc": iso_utc(parse_utc_datetime(candidate_time)),
        "candle_time_utc": iso_utc(parse_utc_datetime(candle_time)),
        "deal_id": row.get("deal_ticket") or row.get("mt5_entry_deal_ticket") or row.get("ticket"),
        "framework": row.get("framework") or row.get("origin_family") or row.get("source_component"),
        "order_id": row.get("order_ticket") or row.get("mt5_entry_order_ticket") or row.get("order"),
        "origin": row.get("origin") or row.get("origin_family") or row.get("source_component"),
        "position_id": row.get("position_id") or row.get("mt5_position_ticket"),
        "route_id": route_id or row.get("route_id"),
        "side": str(row.get("side") or row.get("direction") or row.get("selected_side") or "").upper(),
        "source_path": source_path or row.get("source_path") or row.get("source_file"),
        "source_row_id": row.get("source_row_id") or row.get("selected_row_id") or row.get("candidate_id") or row.get("trade_id"),
        "symbol": symbol,
        "ticket_id": row.get("ticket") or row.get("order_ticket") or row.get("position_id"),
    }


@dataclass(frozen=True)
class LeakIssue:
    field_path: str
    availability_class: str
    reason: str
    value: Any = None


def validate_no_leak_row(
    row: dict[str, Any],
    *,
    context: str,
    decision_time_utc: Any | None = None,
    source_path: str = "",
) -> dict[str, Any]:
    """Validate a row against feature/label/replay/broker truth boundaries."""
    context_key = context.lower()
    if context_key == "feature_store":
        allowed = FEATURE_ALLOWED_CLASSES
    elif context_key == "label_store":
        allowed = LABEL_ALLOWED_CLASSES
    elif context_key == "replay_decision":
        allowed = REPLAY_DECISION_ALLOWED_CLASSES
    elif context_key == "broker_truth":
        allowed = BROKER_TRUTH_ALLOWED_CLASSES
    else:
        return {
            "context": context,
            "issue_count": 1,
            "issues": [
                {
                    "availability_class": "unknown",
                    "field_path": "<context>",
                    "reason": "unknown_validation_context",
                    "value": context,
                }
            ],
            "ok": False,
        }

    decision_dt = parse_utc_datetime(decision_time_utc)
    issues: list[LeakIssue] = []
    for field_path, value in flatten_mapping(row):
        if not field_path:
            continue
        classification = classify_field(field_path, source_path=source_path)
        availability = classification["availability_class"]
        if availability not in allowed:
            issues.append(
                LeakIssue(
                    field_path=field_path,
                    availability_class=availability,
                    reason=f"{availability}_not_allowed_in_{context_key}",
                    value=value,
                )
            )
            continue
        if context_key == "feature_store" and decision_dt is not None:
            parsed_value = parse_utc_datetime(value)
            if parsed_value is not None and parsed_value > decision_dt:
                issues.append(
                    LeakIssue(
                        field_path=field_path,
                        availability_class=availability,
                        reason="timestamp_after_decision_time_not_feature_usable",
                        value=value,
                    )
                )

    return {
        "context": context,
        "issue_count": len(issues),
        "issues": [
            {
                "availability_class": issue.availability_class,
                "field_path": issue.field_path,
                "reason": issue.reason,
                "value": issue.value,
            }
            for issue in issues
        ],
        "ok": not issues,
    }


def forbidden_runtime_effect_boundary() -> dict[str, bool | str]:
    return {
        "credential_or_remote_change": False,
        "live_broker_order_operation": False,
        "paid_api_vendor_call": False,
        "production_config_prompt_risk_execution_selector_change": False,
        "runtime_effect_boundary": "route_local_research_contract_only_no_live_behavior_change",
    }


__all__ = [
    "AVAILABILITY_CLASSES",
    "BROKER_TRUTH_ALLOWED_CLASSES",
    "FEATURE_ALLOWED_CLASSES",
    "LABEL_ALLOWED_CLASSES",
    "REPLAY_DECISION_ALLOWED_CLASSES",
    "broker_symbol_for",
    "candle_close_for",
    "canonical_key",
    "classify_field",
    "flatten_mapping",
    "forbidden_runtime_effect_boundary",
    "is_friday_close_risk",
    "kill_zone_windows_for_symbol",
    "parse_utc_datetime",
    "session_for_utc",
    "validate_no_leak_row",
]
