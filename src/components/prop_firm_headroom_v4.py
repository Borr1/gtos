"""Prop-firm account headroom snapshot contract for risk-bearing V4 paths.

The validator is local and read-only. It does not query MT5, mutate broker
state, place orders, or infer broker-real headroom from replay/proxy labels.
Callers must supply a fresh broker-real snapshot captured by their account
authority before a governed production row can become risk-bearing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_VERSION = "prop_firm_headroom_snapshot_v4"
DEFAULT_MAX_AGE_SECONDS = 900

SNAPSHOT_KEYS = (
    "gtos_vnext_prop_firm_headroom_snapshot_v4",
    "prop_firm_headroom_snapshot_v4",
    "prop_firm_headroom_snapshot",
)
ACCOUNT_STATE_KEYS = (
    "gtos_vnext_prop_firm_headroom_account_state_v4",
    "prop_firm_headroom_account_state_v4",
    "prop_firm_headroom_account_state",
)

BROKER_REAL_SOURCE_STATUSES = {
    "source_bound_broker_real_account_headroom",
    "broker_real_account_headroom_snapshot_captured",
    "broker_real_account_snapshot_captured",
}

REPLAY_OR_PROXY_TOKENS = (
    "replay",
    "proxy",
    "simulated",
    "simulation",
    "backtest",
    "frozen",
)


def _stable_sha256(payload: Any) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PropFirmHeadroomEvaluationV4:
    """Result of validating a supplied prop-firm headroom snapshot."""

    allowed: bool
    reason: str
    requested_risk_pct: float | None
    max_allowed_new_trade_risk_pct: float | None
    missing_fields: tuple[str, ...] = ()
    stale_by_seconds: float | None = None
    snapshot_age_seconds: float | None = None
    source_status: str | None = None
    evidence_class: str | None = None
    captured_at_utc: str | None = None
    snapshot: Mapping[str, Any] | None = None

    def to_packet(self) -> dict[str, Any]:
        return {
            "schema_version": "prop_firm_headroom_evaluation_v4",
            "component": "prop_firm_headroom_v4",
            "allowed": self.allowed,
            "reason": self.reason,
            "requested_risk_pct": self.requested_risk_pct,
            "max_allowed_new_trade_risk_pct": self.max_allowed_new_trade_risk_pct,
            "missing_fields": list(self.missing_fields),
            "stale_by_seconds": self.stale_by_seconds,
            "snapshot_age_seconds": self.snapshot_age_seconds,
            "source_status": self.source_status,
            "evidence_class": self.evidence_class,
            "captured_at_utc": self.captured_at_utc,
            "snapshot_present": self.snapshot is not None,
            "source_boundary": (
                "broker_real_account_headroom_required_no_replay_proxy_or_simulated_equity"
            ),
            "broker_runtime_change_status": False,
            "forbidden_surface_status": {
                "broker_account_order_history_deal_position_mutation": False,
                "order_send": False,
                "credential_disclosure_or_mutation": False,
                "paid_api_vendor_call": False,
                "active_vps_process_change": False,
            },
            "snapshot": dict(self.snapshot or {}),
        }


def _get_value(source: Any, key: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(key)
    return getattr(source, key, None)


def _clean_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _parse_utc(value: Any) -> datetime | None:
    text = _clean_str(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _contains_replay_or_proxy(*values: Any) -> bool:
    joined = " ".join(str(value or "").lower() for value in values)
    return any(token in joined for token in REPLAY_OR_PROXY_TOKENS)


def _first_mapping_value(source: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _runtime_config(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    cfg = config.get("gtos_vnext_runtime", {}) if isinstance(config, Mapping) else {}
    return cfg if isinstance(cfg, Mapping) else {}


def _is_sha256(value: Any) -> bool:
    text = _clean_str(value)
    if text is None or len(text) != 64:
        return False
    return all(char in "009abcdef" for char in text.lower())


def find_prop_firm_headroom_snapshot_v4(*sources: Any) -> Mapping[str, Any] | None:
    """Find the first nested PropFirmHeadroomSnapshotV4-like mapping."""
    for source in sources:
        if source is None:
            continue
        for key in SNAPSHOT_KEYS:
            value = _get_value(source, key)
            if isinstance(value, Mapping):
                return value
        if isinstance(source, Mapping):
            direct_schema = _clean_str(source.get("schema_version"))
            if direct_schema == SCHEMA_VERSION:
                return source
    return None


def _configured_max_age_seconds(config: Mapping[str, Any] | None) -> int:
    cfg = _runtime_config(config)
    raw = cfg.get(
        "prop_firm_headroom_snapshot_max_age_seconds",
        DEFAULT_MAX_AGE_SECONDS,
    )
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        return DEFAULT_MAX_AGE_SECONDS
    return max(1, value)


def _configured_required_account_namespace(
    config: Mapping[str, Any] | None,
) -> str | None:
    cfg = _runtime_config(config)
    return _clean_str(cfg.get("prop_firm_headroom_required_account_namespace"))


def build_prop_firm_headroom_snapshot_v4(
    *,
    account_info: Any,
    account_namespace: str,
    day_start_equity_or_balance_baseline: Any,
    daily_reset_window_id: str,
    config: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
    initial_equity_or_balance_baseline: Any = None,
    daily_loss_limit_pct: Any = None,
    overall_loss_limit_pct: Any = None,
    new_trade_buffer_pct: Any = None,
    account_login_salt: Any = None,
) -> dict[str, Any]:
    """Build a read-only broker-real PropFirmHeadroomSnapshotV4 from account facts.

    The adapter accepts an already-supplied account-info object or mapping. It
    does not query MT5, mutate account state, place orders, or retain raw login
    identifiers in the resulting snapshot.
    """

    cfg = _runtime_config(config)
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    captured_at = now.isoformat()
    namespace = str(account_namespace or "").strip()
    login = _get_value(account_info, "login")
    if login in (None, ""):
        login = _get_value(account_info, "account")
    equity = _float_or_none(_get_value(account_info, "equity"))
    balance = _float_or_none(_get_value(account_info, "balance"))
    current_equity = equity if equity is not None else balance
    day_start = _float_or_none(day_start_equity_or_balance_baseline)
    initial_baseline = _float_or_none(initial_equity_or_balance_baseline)
    if initial_baseline is None:
        initial_baseline = _float_or_none(cfg.get("prop_safe_selector_initial_balance"))
    daily_limit = _float_or_none(daily_loss_limit_pct)
    if daily_limit is None:
        daily_limit = _float_or_none(
            cfg.get("prop_safe_selector_external_daily_loss_limit_pct")
        )
    overall_limit = _float_or_none(overall_loss_limit_pct)
    if overall_limit is None:
        overall_limit = _float_or_none(
            cfg.get("prop_safe_selector_external_overall_max_loss_pct")
        )
    buffer_pct = _float_or_none(new_trade_buffer_pct)
    if buffer_pct is None:
        buffer_pct = _float_or_none(cfg.get("prop_firm_headroom_new_trade_buffer_pct"))
    buffer_pct = 0.0 if buffer_pct is None else max(0.0, buffer_pct)

    daily_drawdown_pct = None
    if current_equity is not None and day_start is not None and day_start > 0:
        daily_drawdown_pct = max(0.0, (day_start - current_equity) / day_start * 100.0)
    overall_drawdown_pct = None
    if (
        current_equity is not None
        and initial_baseline is not None
        and initial_baseline > 0
    ):
        overall_drawdown_pct = max(
            0.0,
            (initial_baseline - current_equity) / initial_baseline * 100.0,
        )
    daily_headroom = (
        max(0.0, daily_limit - daily_drawdown_pct)
        if daily_limit is not None and daily_drawdown_pct is not None
        else None
    )
    overall_headroom = (
        max(0.0, overall_limit - overall_drawdown_pct)
        if overall_limit is not None and overall_drawdown_pct is not None
        else None
    )
    headroom_candidates = [
        value for value in (daily_headroom, overall_headroom) if value is not None
    ]
    max_allowed = (
        max(0.0, min(headroom_candidates) - buffer_pct)
        if headroom_candidates
        else None
    )
    account_login_hash = _stable_sha256(
        {
            "account_namespace": namespace,
            "account_login": str(login or ""),
            "salt": str(account_login_salt if account_login_salt is not None else cfg.get("account_hash_salt") or ""),
        }
    )
    source_material = {
        "account_namespace": namespace,
        "account_login_hash": account_login_hash,
        "captured_at_utc": captured_at,
        "current_equity": current_equity,
        "balance": balance,
        "day_start_equity_or_balance_baseline": day_start,
        "initial_equity_or_balance_baseline": initial_baseline,
        "daily_reset_window_id": daily_reset_window_id,
        "available_daily_loss_headroom_pct": daily_headroom,
        "available_overall_loss_headroom_pct": overall_headroom,
        "max_allowed_new_trade_risk_pct": max_allowed,
    }
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "source_status": "source_bound_broker_real_account_headroom",
        "evidence_class": "broker_real_account_headroom_snapshot_v4",
        "captured_at_utc": captured_at,
        "account_namespace": namespace,
        "account_login_hash": account_login_hash,
        "daily_reset_window_id": daily_reset_window_id,
        "current_equity": current_equity,
        "balance": balance,
        "day_start_equity_or_balance_baseline": day_start,
        "initial_equity_or_balance_baseline": initial_baseline,
        "daily_drawdown_pct": daily_drawdown_pct,
        "overall_drawdown_pct": overall_drawdown_pct,
        "available_daily_loss_headroom_pct": daily_headroom,
        "available_overall_loss_headroom_pct": overall_headroom,
        "max_allowed_new_trade_risk_pct": max_allowed,
        "headroom_buffer_pct": buffer_pct,
        "source_event_hash_sha256": _stable_sha256(source_material),
        "broker_runtime_change_status": False,
        "broker_order_mutation": False,
    }
    snapshot["snapshot_hash_sha256"] = _stable_sha256(snapshot)
    return snapshot


def find_prop_firm_headroom_account_state_v4(*sources: Any) -> Mapping[str, Any] | None:
    """Find account-state facts that can build PropFirmHeadroomSnapshotV4."""
    for source in sources:
        if source is None:
            continue
        for key in ACCOUNT_STATE_KEYS:
            value = _get_value(source, key)
            if isinstance(value, Mapping):
                return value
        if isinstance(source, Mapping):
            direct_schema = _clean_str(source.get("schema_version"))
            if direct_schema == "prop_firm_headroom_account_state_v4":
                return source
    return None


def build_prop_firm_headroom_snapshot_v4_from_account_state(
    account_state: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Build PropFirmHeadroomSnapshotV4 from supplied runtime account facts.

    This adapter is intentionally read-only. It accepts facts already captured
    by the runtime or tests and never calls MT5 or broker APIs itself.
    """

    cfg = _runtime_config(config)
    embedded_account = account_state.get("account_info")
    if isinstance(embedded_account, Mapping):
        account_info: Mapping[str, Any] = embedded_account
    else:
        account_info = {
            "login": _first_mapping_value(
                account_state,
                ("account_login", "login", "account", "account_id"),
            ),
            "balance": _first_mapping_value(
                account_state,
                ("current_balance", "balance", "account_balance"),
            ),
            "equity": _first_mapping_value(
                account_state,
                ("current_equity", "equity", "account_equity"),
            ),
        }
    account_namespace = (
        _clean_str(
            _first_mapping_value(
                account_state,
                (
                    "account_namespace",
                    "broker_account_namespace",
                    "prop_account_namespace",
                ),
            )
        )
        or _clean_str(cfg.get("prop_firm_headroom_required_account_namespace"))
        or "unknown_account_namespace"
    )
    daily_reset_window_id = _clean_str(
        _first_mapping_value(
            account_state,
            ("daily_reset_window_id", "day_reset_window_id", "reset_window_id"),
        )
    )
    if not daily_reset_window_id:
        captured_at = now_utc or datetime.now(timezone.utc)
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)
        daily_reset_window_id = (
            f"{captured_at.astimezone(timezone.utc).date().isoformat()}/"
            f"{account_namespace}"
        )
    return build_prop_firm_headroom_snapshot_v4(
        account_info=account_info,
        account_namespace=account_namespace,
        day_start_equity_or_balance_baseline=_first_mapping_value(
            account_state,
            (
                "day_start_equity_or_balance_baseline",
                "day_start_equity",
                "day_start_balance",
                "day_start_baseline",
            ),
        ),
        daily_reset_window_id=daily_reset_window_id,
        config=config,
        now_utc=now_utc,
        initial_equity_or_balance_baseline=_first_mapping_value(
            account_state,
            (
                "initial_equity_or_balance_baseline",
                "initial_balance",
                "initial_equity",
            ),
        ),
        daily_loss_limit_pct=_first_mapping_value(
            account_state,
            (
                "daily_loss_limit_pct",
                "external_daily_loss_limit_pct",
                "max_daily_loss_pct",
            ),
        ),
        overall_loss_limit_pct=_first_mapping_value(
            account_state,
            (
                "overall_loss_limit_pct",
                "external_overall_loss_limit_pct",
                "external_total_loss_limit_pct",
                "max_overall_loss_pct",
            ),
        ),
        new_trade_buffer_pct=_first_mapping_value(
            account_state,
            ("new_trade_buffer_pct", "headroom_buffer_pct"),
        ),
        account_login_salt=_first_mapping_value(
            account_state,
            ("account_login_salt", "account_hash_salt"),
        ),
    )


def evaluate_prop_firm_headroom_snapshot_v4(
    *,
    snapshot: Mapping[str, Any] | None,
    requested_risk_pct: Any,
    config: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> PropFirmHeadroomEvaluationV4:
    """Validate a broker-real, fresh, sufficient headroom snapshot."""
    requested = _float_or_none(requested_risk_pct)
    if snapshot is None:
        return PropFirmHeadroomEvaluationV4(
            allowed=False,
            reason="snapshot_missing",
            requested_risk_pct=requested,
            max_allowed_new_trade_risk_pct=None,
            missing_fields=("gtos_vnext_prop_firm_headroom_snapshot_v4",),
        )

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    max_age_seconds = _configured_max_age_seconds(config)

    schema_version = _clean_str(snapshot.get("schema_version"))
    source_status = _clean_str(snapshot.get("source_status"))
    evidence_class = _clean_str(snapshot.get("evidence_class"))
    captured_at_raw = _first_mapping_value(
        snapshot,
        ("captured_at_utc", "generated_at_utc", "source_timestamp_utc"),
    )
    captured_at = _parse_utc(captured_at_raw)
    account_namespace = _first_mapping_value(
        snapshot,
        ("account_namespace", "broker_account_namespace", "target_namespace"),
    )
    account_hash = _first_mapping_value(
        snapshot,
        ("account_login_hash", "account_id_hash", "account_hash"),
    )
    daily_reset_window_id = _first_mapping_value(
        snapshot,
        ("daily_reset_window_id", "reset_window_id", "trading_day_utc"),
    )
    current_equity = _float_or_none(
        _first_mapping_value(snapshot, ("current_equity", "equity"))
    )
    day_start = _float_or_none(
        _first_mapping_value(
            snapshot,
            (
                "day_start_equity_or_balance_baseline",
                "day_start_equity",
                "day_start_balance",
            ),
        )
    )
    daily_headroom = _float_or_none(
        _first_mapping_value(
            snapshot,
            (
                "available_daily_loss_headroom_pct",
                "remaining_daily_headroom_pct",
                "daily_headroom_pct",
            ),
        )
    )
    overall_headroom = _float_or_none(
        _first_mapping_value(
            snapshot,
            (
                "available_overall_loss_headroom_pct",
                "remaining_overall_headroom_pct",
                "overall_headroom_pct",
            ),
        )
    )
    max_allowed = _float_or_none(
        _first_mapping_value(
            snapshot,
            (
                "max_allowed_new_trade_risk_pct",
                "available_new_trade_risk_pct",
                "approved_new_trade_risk_pct",
            ),
        )
    )
    if max_allowed is None:
        candidates = [
            value for value in (daily_headroom, overall_headroom) if value is not None
        ]
        max_allowed = min(candidates) if candidates else None

    broker_runtime_change = _bool_value(snapshot.get("broker_runtime_change_status"))
    order_mutation = _bool_value(snapshot.get("broker_order_mutation"))
    source_event_hash = _clean_str(snapshot.get("source_event_hash_sha256"))
    snapshot_hash = _clean_str(snapshot.get("snapshot_hash_sha256"))
    required_namespace = _configured_required_account_namespace(config)

    missing: list[str] = []
    if schema_version != SCHEMA_VERSION:
        missing.append("schema_version:prop_firm_headroom_snapshot_v4")
    if source_status not in BROKER_REAL_SOURCE_STATUSES:
        missing.append("source_status:broker_real_account_headroom")
    if not evidence_class:
        missing.append("evidence_class")
    if captured_at is None:
        missing.append("captured_at_utc")
    if not account_namespace:
        missing.append("account_namespace")
    if not account_hash:
        missing.append("account_login_hash_or_account_id_hash")
    elif not _is_sha256(account_hash):
        missing.append("account_login_hash_or_account_id_hash:sha256")
    if not daily_reset_window_id:
        missing.append("daily_reset_window_id")
    if required_namespace and account_namespace != required_namespace:
        missing.append("account_namespace:configured_account_mismatch")
    if current_equity is None or current_equity <= 0:
        missing.append("current_equity")
    if day_start is None or day_start <= 0:
        missing.append("day_start_equity_or_balance_baseline")
    if daily_headroom is None:
        missing.append("available_daily_loss_headroom_pct")
    if overall_headroom is None:
        missing.append("available_overall_loss_headroom_pct")
    if max_allowed is None:
        missing.append("max_allowed_new_trade_risk_pct")
    if requested is None or requested <= 0:
        missing.append("requested_risk_pct")
    if not _is_sha256(source_event_hash):
        missing.append("source_event_hash_sha256")
    if not _is_sha256(snapshot_hash):
        missing.append("snapshot_hash_sha256")
    if broker_runtime_change is not False:
        missing.append("broker_runtime_change_status:false")
    if order_mutation is not False:
        missing.append("broker_order_mutation:false")

    if _contains_replay_or_proxy(
        evidence_class,
        source_status,
        snapshot.get("result_scope"),
        snapshot.get("risk_packet_source_status"),
        snapshot.get("prop_firm_risk_block_evidence_status"),
    ):
        return PropFirmHeadroomEvaluationV4(
            allowed=False,
            reason="snapshot_not_broker_real",
            requested_risk_pct=requested,
            max_allowed_new_trade_risk_pct=max_allowed,
            missing_fields=tuple(dict.fromkeys(missing)),
            source_status=source_status,
            evidence_class=evidence_class,
            captured_at_utc=_clean_str(captured_at_raw),
            snapshot=snapshot,
        )

    if missing:
        return PropFirmHeadroomEvaluationV4(
            allowed=False,
            reason="snapshot_incomplete",
            requested_risk_pct=requested,
            max_allowed_new_trade_risk_pct=max_allowed,
            missing_fields=tuple(dict.fromkeys(missing)),
            source_status=source_status,
            evidence_class=evidence_class,
            captured_at_utc=_clean_str(captured_at_raw),
            snapshot=snapshot,
        )

    age_seconds = (now - captured_at).total_seconds() if captured_at else None
    if age_seconds is not None and age_seconds < -60.0:
        return PropFirmHeadroomEvaluationV4(
            allowed=False,
            reason="snapshot_from_future",
            requested_risk_pct=requested,
            max_allowed_new_trade_risk_pct=max_allowed,
            snapshot_age_seconds=age_seconds,
            source_status=source_status,
            evidence_class=evidence_class,
            captured_at_utc=_clean_str(captured_at_raw),
            snapshot=snapshot,
        )
    if age_seconds is None or age_seconds > max_age_seconds:
        stale_by = None if age_seconds is None else age_seconds - max_age_seconds
        return PropFirmHeadroomEvaluationV4(
            allowed=False,
            reason="snapshot_stale",
            requested_risk_pct=requested,
            max_allowed_new_trade_risk_pct=max_allowed,
            stale_by_seconds=stale_by,
            snapshot_age_seconds=age_seconds,
            source_status=source_status,
            evidence_class=evidence_class,
            captured_at_utc=_clean_str(captured_at_raw),
            snapshot=snapshot,
        )

    if max_allowed is None or requested is None or requested - max_allowed > 1e-9:
        return PropFirmHeadroomEvaluationV4(
            allowed=False,
            reason="snapshot_insufficient_headroom",
            requested_risk_pct=requested,
            max_allowed_new_trade_risk_pct=max_allowed,
            snapshot_age_seconds=age_seconds,
            source_status=source_status,
            evidence_class=evidence_class,
            captured_at_utc=_clean_str(captured_at_raw),
            snapshot=snapshot,
        )

    return PropFirmHeadroomEvaluationV4(
        allowed=True,
        reason="source_bound_broker_real_headroom_sufficient",
        requested_risk_pct=requested,
        max_allowed_new_trade_risk_pct=max_allowed,
        snapshot_age_seconds=age_seconds,
        source_status=source_status,
        evidence_class=evidence_class,
        captured_at_utc=_clean_str(captured_at_raw),
        snapshot=snapshot,
    )


__all__ = [
    "ACCOUNT_STATE_KEYS",
    "DEFAULT_MAX_AGE_SECONDS",
    "SCHEMA_VERSION",
    "PropFirmHeadroomEvaluationV4",
    "build_prop_firm_headroom_snapshot_v4",
    "build_prop_firm_headroom_snapshot_v4_from_account_state",
    "evaluate_prop_firm_headroom_snapshot_v4",
    "find_prop_firm_headroom_account_state_v4",
    "find_prop_firm_headroom_snapshot_v4",
]
