"""Expired-POI watch registry and revalidation logger.

Pending limit intents are executable state. A structural POI can outlive that
intent. This module keeps those lifecycles separate by archiving eligible
no-fill limit cancellations into a watch registry, then evaluating those
watches against fresh candles/ticks in shadow mode.

No function in this module sends orders or mutates execution state.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "expired_poi_watch_v1"
WATCH_REGISTRY_DIR = Path("knowledge_base/meta/expired_poi_watches")
REVALIDATION_LOG_PATH = Path("shadow_logs/expired_poi_revalidation.jsonl")

DEFAULT_ARCHIVE_REASONS = {"new_day", "48h clock expiry", "expired_48h"}
DEFAULT_MAX_WATCH_HOURS = 72.0
DEFAULT_APPROACH_THRESHOLD_R = 0.25
DEFAULT_MIN_REARM_RR = 1.5

INTERESTING_REVALIDATION_STATUSES = {
    "APPROACHING_ENTRY",
    "INSIDE_POI_REVALIDATION_ELIGIBLE_SHADOW",
    "INSIDE_POI_SL_DISTANCE_TOO_TIGHT_NO_REARM",
    "TOUCHED_REVALIDATION_ELIGIBLE_SHADOW",
    "TOUCHED_RR_DECAYED_NO_REARM",
    "TOUCHED_SL_DISTANCE_TOO_TIGHT_NO_REARM",
    "INVALIDATED_BY_SL",
    "EXPIRED_WATCH_MAX_AGE",
}

TERMINAL_WATCH_STATUSES = {
    "INVALIDATED_BY_SL",
    "EXPIRED_WATCH_MAX_AGE",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(_json_safe(row), sort_keys=True) + "\n")


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _get_nested(root: Any, *path: str) -> Any:
    cur = root
    for key in path:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            cur = getattr(cur, key, None)
    return cur


def _intent_get(intent: Any, name: str, default: Any = None) -> Any:
    if intent is None:
        return default
    if isinstance(intent, dict):
        return intent.get(name, default)
    return getattr(intent, name, default)


def _normalise_side(value: Any) -> str | None:
    side = str(value or "").strip().upper()
    if side in {"LONG", "BUY"}:
        return "LONG"
    if side in {"SHORT", "SELL"}:
        return "SHORT"
    return None


def _parse_zone(value: Any) -> tuple[float | None, float | None, str]:
    if isinstance(value, dict):
        low = _safe_float(value.get("low") or value.get("zone_low") or value.get("bottom"))
        high = _safe_float(value.get("high") or value.get("zone_high") or value.get("top"))
        if low is not None and high is not None:
            return min(low, high), max(low, high), "dict"
    if isinstance(value, str) and "-" in value:
        left, right = value.split("-", 1)
        low = _safe_float(left.strip())
        high = _safe_float(right.strip())
        if low is not None and high is not None:
            return min(low, high), max(low, high), "string"
    return None, None, "missing"


def _extract_poi_zone(record: dict[str, Any] | None) -> tuple[float | None, float | None, str]:
    if not isinstance(record, dict):
        return None, None, "record_missing"

    inst_zone = _get_nested(record, "instrumentation", "target_ob_zone")
    low, high, source = _parse_zone(inst_zone)
    if low is not None and high is not None:
        return low, high, f"instrumentation.{source}"

    shadow_zone = _get_nested(record, "shadow_data", "h1_zone")
    low, high, source = _parse_zone(shadow_zone)
    if low is not None and high is not None:
        return low, high, f"shadow_data.h1_zone.{source}"

    checks = _get_nested(record, "decision_pipeline", "level2_verification", "checks")
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            if check.get("name") not in {"h1_poi_exists", "entry_in_ob", "entry_in_breaker"}:
                continue
            mso_value = check.get("mso_value")
            low, high, source = _parse_zone(
                _get_nested(mso_value, "zone") if isinstance(mso_value, dict) else mso_value
            )
            if low is not None and high is not None:
                return low, high, f"level2.{check.get('name')}.{source}"

    ai_zone = _get_nested(record, "ai_response", "reasoning", "h1_setup", "zone")
    low, high, source = _parse_zone(ai_zone)
    if low is not None and high is not None:
        return low, high, f"ai_response.h1_setup.zone.{source}"

    return None, None, "not_found"


def _risk_reward(side: str, entry: float, stop_loss: float, take_profit: float) -> float | None:
    if side == "LONG":
        risk = entry - stop_loss
        reward = take_profit - entry
    elif side == "SHORT":
        risk = stop_loss - entry
        reward = entry - take_profit
    else:
        return None
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk


def _watch_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    cfg = config.get("expired_poi_watch") or {}
    return cfg if isinstance(cfg, dict) else {}


def _min_rearm_rr(config: dict[str, Any] | None) -> float:
    cfg = _watch_config(config)
    configured = _safe_float(cfg.get("min_rearm_rr"))
    if configured is not None:
        return configured
    return _safe_float(_get_nested(config, "risk", "min_rr")) or DEFAULT_MIN_REARM_RR


def _stable_watch_id(*parts: Any) -> str:
    raw = "|".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def should_archive_cancel_reason(reason: str, config: dict[str, Any] | None = None) -> bool:
    cfg = _watch_config(config)
    allowed = cfg.get("archive_cancel_reasons")
    reasons = set(allowed) if isinstance(allowed, list) and allowed else DEFAULT_ARCHIVE_REASONS
    return str(reason or "") in reasons


def build_expired_poi_watch(
    *,
    record: dict[str, Any] | None,
    intent: Any,
    cancel_reason: str,
    config: dict[str, Any] | None = None,
    record_path: str | None = None,
    archived_at_utc: str | None = None,
) -> dict[str, Any] | None:
    """Build a schema-stable expired-POI watch row from a cancelled limit.

    Returns None when the cancellation reason is not watch-eligible or when the
    source does not contain enough executable geometry to evaluate later.
    """
    if not should_archive_cancel_reason(cancel_reason, config):
        return None

    final_outcome = _get_nested(record, "decision_pipeline", "final_outcome")
    if isinstance(record, dict) and final_outcome not in {None, "LIMIT_PLACED", "PENDING_LIMIT", "ORDER_PLACED"}:
        return None

    limit_info = _get_nested(record, "limit_intent") or {}
    trade_params = _get_nested(record, "trade_parameters") or {}

    symbol = (
        _intent_get(intent, "source_symbol")
        or _get_nested(record, "metadata", "symbol")
        or _watch_config(config).get("symbol")
        or _get_nested(config, "market", "symbol")
    )
    symbol = str(symbol or "").replace(".", "_")
    if not symbol:
        return None

    side = _normalise_side(
        _intent_get(intent, "direction")
        or trade_params.get("direction")
        or _get_nested(record, "decision_pipeline", "ai_direction")
    )
    entry = _safe_float(
        _intent_get(intent, "limit_price")
        or limit_info.get("limit_price")
        or trade_params.get("entry_price")
    )
    stop_loss = _safe_float(
        _intent_get(intent, "stop_loss")
        or limit_info.get("stop_loss")
        or trade_params.get("stop_loss")
    )
    take_profit = _safe_float(
        _intent_get(intent, "take_profit_1")
        or limit_info.get("take_profit_1")
        or trade_params.get("take_profit_1")
    )
    if side is None or entry is None or stop_loss is None or take_profit is None:
        return None

    rr_at_entry = _risk_reward(side, entry, stop_loss, take_profit)
    if rr_at_entry is None:
        return None

    poi_low, poi_high, poi_source = _extract_poi_zone(record)
    trade_id = (
        _intent_get(intent, "trade_id")
        or limit_info.get("trade_id")
        or _get_nested(record, "metadata", "trade_id")
    )
    candidate_id = (
        _intent_get(intent, "candidate_id")
        or _get_nested(record, "candidate_id")
        or _get_nested(record, "metadata", "candidate_id")
        or _get_nested(record, "ai_response", "candidate_id")
    )
    decision_time = (
        _intent_get(intent, "decision_time_utc")
        or _get_nested(record, "metadata", "candle_close_utc")
        or _get_nested(record, "metadata", "candle_time")
    )
    archived_at = archived_at_utc or utc_now_iso()
    cfg = _watch_config(config)

    watch_id = _stable_watch_id(
        SCHEMA_VERSION,
        symbol,
        trade_id,
        candidate_id,
        side,
        entry,
        stop_loss,
        take_profit,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "event_type": "WATCH_CREATED",
        "watch_id": watch_id,
        "status": "ACTIVE_WATCH",
        "symbol": symbol,
        "source_symbol": _intent_get(intent, "source_symbol") or symbol,
        "broker_symbol": _get_nested(config, "market", "mt5_symbol") or symbol,
        "candidate_id": candidate_id,
        "original_trade_id": trade_id,
        "source_trade_record_path": record_path,
        "source_final_outcome": final_outcome,
        "source_ai_grade": _get_nested(record, "decision_pipeline", "ai_grade"),
        "source_ai_framework": _get_nested(record, "decision_pipeline", "ai_framework"),
        "source_l2_passed": _get_nested(record, "decision_pipeline", "level2_verification", "passed"),
        "side": side,
        "entry_price": entry,
        "stop_loss": stop_loss,
        "take_profit_1": take_profit,
        "risk_distance_at_entry": abs(entry - stop_loss),
        "reward_distance_at_entry": abs(take_profit - entry),
        "risk_reward_at_entry": rr_at_entry,
        "poi_low": poi_low,
        "poi_high": poi_high,
        "poi_source": poi_source,
        "decision_time_utc": decision_time,
        "pending_created_time_utc": _intent_get(intent, "placed_time"),
        "archived_at_utc": archived_at,
        "cancel_reason": cancel_reason,
        "original_kill_zone": _intent_get(intent, "kill_zone") or _get_nested(record, "metadata", "kill_zone"),
        "original_session": _intent_get(intent, "session"),
        "watch_reason": "pending_intent_expired_but_structural_poi_may_remain_valid",
        "mode": cfg.get("mode", "shadow"),
        "execution_override_enabled": bool(cfg.get("execution_override_enabled", False)),
        "min_rearm_rr": _min_rearm_rr(config),
        "max_watch_hours": _safe_float(cfg.get("max_watch_hours")) or DEFAULT_MAX_WATCH_HOURS,
        "approach_threshold_r": (
            _safe_float(cfg.get("approach_threshold_r")) or DEFAULT_APPROACH_THRESHOLD_R
        ),
        "require_kill_zone_for_rearm": bool(cfg.get("require_kill_zone_for_rearm", True)),
        "created_at_utc": archived_at,
    }


def watch_registry_path(symbol: str, registry_dir: str | Path | None = None) -> Path:
    safe_symbol = str(symbol or "").replace(".", "_")
    return Path(registry_dir or WATCH_REGISTRY_DIR) / f"expired_poi_watches_{safe_symbol}.jsonl"


def append_expired_poi_watch(
    watch: dict[str, Any],
    *,
    registry_dir: str | Path | None = None,
    dedupe: bool = True,
) -> bool:
    """Append a watch-created row. Returns True when a row was written."""
    symbol = str(watch.get("symbol") or "").replace(".", "_")
    if not symbol or not watch.get("watch_id"):
        return False
    path = watch_registry_path(symbol, registry_dir)
    if dedupe and path.exists():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("watch_id") == watch.get("watch_id") and row.get("event_type") == "WATCH_CREATED":
                    return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("expired_poi_watch dedupe read failed: %s", exc)
    _append_jsonl(path, watch)
    return True


def archive_expired_pending_intent(
    *,
    record: dict[str, Any] | None,
    intent: Any,
    cancel_reason: str,
    config: dict[str, Any] | None = None,
    record_path: str | None = None,
    registry_dir: str | Path | None = None,
) -> dict[str, Any] | None:
    """Archive an eligible expired pending intent as a structural POI watch."""
    watch = build_expired_poi_watch(
        record=record,
        intent=intent,
        cancel_reason=cancel_reason,
        config=config,
        record_path=record_path,
    )
    if not watch:
        return None
    append_expired_poi_watch(watch, registry_dir=registry_dir)
    return watch


def load_active_watches(
    symbol: str,
    *,
    registry_dir: str | Path | None = None,
    now: datetime | None = None,
    max_watch_hours: float | None = None,
) -> list[dict[str, Any]]:
    """Load latest active registry rows for a symbol."""
    path = watch_registry_path(symbol, registry_dir)
    if not path.exists():
        return []
    latest: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        watch_id = row.get("watch_id")
        if watch_id:
            latest[str(watch_id)] = row

    ref = now or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    else:
        ref = ref.astimezone(timezone.utc)

    active: list[dict[str, Any]] = []
    for watch in latest.values():
        if watch.get("status") != "ACTIVE_WATCH":
            continue
        created = _parse_dt(watch.get("archived_at_utc") or watch.get("created_at_utc"))
        hours = max_watch_hours
        if hours is None:
            hours = _safe_float(watch.get("max_watch_hours")) or DEFAULT_MAX_WATCH_HOURS
        if created is not None and (ref - created).total_seconds() / 3600.0 > hours:
            active.append(watch)
            continue
        active.append(watch)
    return sorted(active, key=lambda item: str(item.get("archived_at_utc") or ""))


def _is_inside_kill_zone(kill_zone: str | None) -> bool:
    return bool(kill_zone and str(kill_zone).lower() not in {"none", "unknown", ""})


def evaluate_expired_poi_watch(
    watch: dict[str, Any],
    *,
    candle: dict[str, Any] | None = None,
    bid: float | None = None,
    ask: float | None = None,
    now: datetime | None = None,
    config: dict[str, Any] | None = None,
    kill_zone: str | None = None,
    confirmation_state: str = "not_evaluated",
) -> dict[str, Any]:
    """Evaluate one expired-POI watch against fresh price evidence.

    The result is deliberately advisory/shadow-only. It says whether the old
    geometry is still coherent; it does not authorize execution.
    """
    ref = now or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    else:
        ref = ref.astimezone(timezone.utc)

    side = _normalise_side(watch.get("side"))
    entry = _safe_float(watch.get("entry_price"))
    stop_loss = _safe_float(watch.get("stop_loss"))
    take_profit = _safe_float(watch.get("take_profit_1"))
    risk_distance = _safe_float(watch.get("risk_distance_at_entry"))
    min_rr = _safe_float(watch.get("min_rearm_rr")) or _min_rearm_rr(config)
    sl_absolute_min = _safe_float(_get_nested(config, "risk", "sl_absolute_min")) or 0.0
    max_hours = _safe_float(watch.get("max_watch_hours")) or DEFAULT_MAX_WATCH_HOURS
    approach_r = _safe_float(watch.get("approach_threshold_r")) or DEFAULT_APPROACH_THRESHOLD_R
    require_kz = bool(watch.get("require_kill_zone_for_rearm", True))
    execution_override = bool(watch.get("execution_override_enabled", False))
    current_price = bid if side == "SHORT" else ask
    if current_price is None and isinstance(candle, dict):
        current_price = _safe_float(candle.get("close"))

    created = _parse_dt(watch.get("archived_at_utc") or watch.get("created_at_utc"))
    age_hours = None
    if created is not None:
        age_hours = (ref - created).total_seconds() / 3600.0

    high = _safe_float(candle.get("high")) if isinstance(candle, dict) else None
    low = _safe_float(candle.get("low")) if isinstance(candle, dict) else None
    close = _safe_float(candle.get("close")) if isinstance(candle, dict) else None
    candle_time = candle.get("time") if isinstance(candle, dict) else None

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_type": "WATCH_REVALIDATED",
        "created_at_utc": ref.isoformat(),
        "watch_id": watch.get("watch_id"),
        "symbol": watch.get("symbol"),
        "candidate_id": watch.get("candidate_id"),
        "original_trade_id": watch.get("original_trade_id"),
        "side": side,
        "entry_price": entry,
        "stop_loss": stop_loss,
        "take_profit_1": take_profit,
        "risk_reward_at_entry": watch.get("risk_reward_at_entry"),
        "current_price": current_price,
        "tick_bid": bid,
        "tick_ask": ask,
        "checked_candle_time_utc": candle_time,
        "checked_candle_high": high,
        "checked_candle_low": low,
        "checked_candle_close": close,
        "kill_zone": kill_zone,
        "inside_kill_zone": _is_inside_kill_zone(kill_zone),
        "watch_age_hours": age_hours,
        "confirmation_state": confirmation_state,
        "execution_allowed": False,
        "execution_override_enabled": execution_override,
        "requires_fresh_approval": True,
    }

    if side is None or entry is None or stop_loss is None or take_profit is None or current_price is None:
        result.update({"status": "DATA_MISSING", "reason": "missing_side_or_price_geometry"})
        return result

    if risk_distance is None or risk_distance <= 0:
        risk_distance = abs(entry - stop_loss)
    if risk_distance <= 0:
        result.update({"status": "DATA_MISSING", "reason": "invalid_risk_distance"})
        return result

    touched = False
    invalidated = False
    if side == "SHORT":
        touched = (high is not None and high >= entry) or current_price >= entry
        invalidated = (high is not None and high >= stop_loss) or current_price >= stop_loss
    elif side == "LONG":
        touched = (low is not None and low <= entry) or current_price <= entry
        invalidated = (low is not None and low <= stop_loss) or current_price <= stop_loss

    poi_low = _safe_float(watch.get("poi_low"))
    poi_high = _safe_float(watch.get("poi_high"))
    inside_poi = (
        poi_low is not None
        and poi_high is not None
        and poi_low <= current_price <= poi_high
    )
    distance_to_entry_r = abs(current_price - entry) / risk_distance
    rr_at_current = _risk_reward(side, current_price, stop_loss, take_profit)
    rr_ok_current = rr_at_current is not None and rr_at_current >= min_rr
    current_sl_distance = abs(current_price - stop_loss)
    sl_distance_ok = sl_absolute_min <= 0 or current_sl_distance >= sl_absolute_min
    in_kz = _is_inside_kill_zone(kill_zone)
    kz_ok = in_kz or not require_kz

    result.update({
        "entry_touched": touched,
        "inside_poi": inside_poi,
        "invalidated_by_sl": invalidated,
        "distance_to_entry": abs(current_price - entry),
        "distance_to_entry_r": distance_to_entry_r,
        "risk_reward_at_current": rr_at_current,
        "min_rearm_rr": min_rr,
        "rr_ok_current": rr_ok_current,
        "current_sl_distance": current_sl_distance,
        "sl_absolute_min": sl_absolute_min,
        "sl_distance_ok": sl_distance_ok,
        "kz_ok": kz_ok,
    })

    if age_hours is not None and age_hours > max_hours:
        result.update({"status": "EXPIRED_WATCH_MAX_AGE", "reason": "watch_age_exceeded"})
    elif invalidated:
        result.update({"status": "INVALIDATED_BY_SL", "reason": "price_reached_or_crossed_original_sl"})
    elif touched and rr_ok_current and not sl_distance_ok:
        result.update({
            "status": "TOUCHED_SL_DISTANCE_TOO_TIGHT_NO_REARM",
            "reason": "entry_touched_but_current_sl_distance_below_minimum",
        })
    elif touched and rr_ok_current and kz_ok:
        result.update({
            "status": "TOUCHED_REVALIDATION_ELIGIBLE_SHADOW",
            "reason": "entry_touched_current_rr_and_kz_ok_but_execution_disabled",
        })
    elif touched and not rr_ok_current:
        result.update({
            "status": "TOUCHED_RR_DECAYED_NO_REARM",
            "reason": "entry_touched_but_market_reentry_rr_below_minimum",
        })
    elif inside_poi and rr_ok_current and not sl_distance_ok:
        result.update({
            "status": "INSIDE_POI_SL_DISTANCE_TOO_TIGHT_NO_REARM",
            "reason": "price_inside_original_poi_but_current_sl_distance_below_minimum",
        })
    elif inside_poi and rr_ok_current and kz_ok:
        result.update({
            "status": "INSIDE_POI_REVALIDATION_ELIGIBLE_SHADOW",
            "reason": "price_inside_original_poi_geometry_ok_but_execution_disabled",
        })
    elif distance_to_entry_r <= approach_r:
        result.update({"status": "APPROACHING_ENTRY", "reason": "within_configured_entry_distance"})
    else:
        result.update({"status": "WAITING_FAR", "reason": "price_not_near_original_entry"})

    return result


def record_expired_poi_revalidation(
    result: dict[str, Any],
    *,
    log_path: str | Path | None = None,
) -> None:
    """Append one expired-POI revalidation row. Never raises."""
    try:
        _append_jsonl(Path(log_path or REVALIDATION_LOG_PATH), result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("expired_poi_watch revalidation log failed: %s", exc)


def close_expired_poi_watch(
    result: dict[str, Any],
    *,
    registry_dir: str | Path | None = None,
) -> None:
    """Append a terminal registry row so closed watches stop re-evaluating."""
    status = str(result.get("status") or "")
    symbol = str(result.get("symbol") or "").replace(".", "_")
    watch_id = result.get("watch_id")
    if status not in TERMINAL_WATCH_STATUSES or not symbol or not watch_id:
        return

    close_row = dict(result)
    close_row["event_type"] = "WATCH_CLOSED"
    close_row["closed_at_utc"] = utc_now_iso()
    close_row["close_status"] = status
    close_row["close_reason"] = result.get("reason")
    try:
        _append_jsonl(watch_registry_path(symbol, registry_dir), close_row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("expired_poi_watch close registry update failed: %s", exc)


def evaluate_and_log_active_watches(
    *,
    symbol: str,
    candle: dict[str, Any] | None,
    bid: float | None,
    ask: float | None,
    config: dict[str, Any] | None = None,
    kill_zone: str | None = None,
    registry_dir: str | Path | None = None,
    log_path: str | Path | None = None,
    log_all: bool = True,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Evaluate all active watches for a symbol and append shadow rows."""
    cfg = _watch_config(config)
    if not cfg.get("enabled", False) or str(cfg.get("mode", "shadow")).lower() == "off":
        return []

    max_watch_hours = _safe_float(cfg.get("max_watch_hours"))
    watches = load_active_watches(
        symbol,
        registry_dir=registry_dir,
        now=now,
        max_watch_hours=max_watch_hours,
    )
    rows: list[dict[str, Any]] = []
    for watch in watches:
        row = evaluate_expired_poi_watch(
            watch,
            candle=candle,
            bid=bid,
            ask=ask,
            now=now,
            config=config,
            kill_zone=kill_zone,
        )
        if log_all or row.get("status") in INTERESTING_REVALIDATION_STATUSES:
            record_expired_poi_revalidation(row, log_path=log_path)
        close_expired_poi_watch(row, registry_dir=registry_dir)
        rows.append(row)
    return rows
