"""Broker-net pretrade cost packet and gate helpers.

This module is local/read-only. It consumes caller-supplied tick, config, and
symbol metadata; it never calls MT5, sends orders, mutates broker state, or
opens paid data sources.
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from src.costs.model import commission_usd_per_lot_for_packet, rollover_nights
from src.utils.broker_clock import UnknownBrokerClockError
from src.utils.broker_profile import broker_account_namespace, sanitize_namespace


PRETRADE_COST_PACKET_SCHEMA_VERSION = "gtos_v4_pretrade_broker_net_cost_packet_v1"
BROKER_TRUE_COMMISSION_MODE = "broker_true_commission_default_v1"
LEGACY_ZERO_COMMISSION_COMPARATOR_MODE = (
    "legacy_status_only_zero_commission_comparator_v1"
)
COMMISSION_COST_MODEL_VERSION = "broker_true_commission_cash_to_r_v1"
TOTAL_COST_COMPONENTS = (
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
    "commission_r",
)
DEFAULT_ALLOWED_COMMISSION_STATUSES = {
    "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP",
    "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK",
}
SPEC_FIELD_CANDIDATES = {
    "point": ("point", "tick_size"),
    "trade_tick_size": ("trade_tick_size", "tick_size", "point"),
    "trade_tick_value": ("trade_tick_value", "trade_tick_value_profit"),
    "trade_contract_size": ("trade_contract_size", "contract_size"),
    "volume_min": ("volume_min",),
    "volume_max": ("volume_max",),
    "volume_step": ("volume_step",),
    "trade_stops_level": ("trade_stops_level",),
    "trade_freeze_level": ("trade_freeze_level",),
    "spread": ("spread",),
    "trade_mode": ("trade_mode",),
    "filling_mode": ("filling_mode",),
    "swap_long": ("swap_long",),
    "swap_short": ("swap_short",),
    "swap_mode": ("swap_mode",),
    "swap_rollover3days": ("swap_rollover3days",),
    "currency_base": ("currency_base",),
    "currency_profit": ("currency_profit",),
    "currency_margin": ("currency_margin",),
}
EXPLICIT_SESSION_TABLE_CANDIDATES = (
    "symbol_info_session_trade",
    "symbol_info_session_quote",
    "trade_sessions",
    "quote_sessions",
    "trading_sessions",
    "session_table",
    "broker_trading_sessions",
    "broker_quote_sessions",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _aware_utc(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _snapshot(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "_asdict"):
        try:
            return dict(value._asdict())
        except Exception:  # noqa: BLE001 - best-effort read-only snapshot
            return {}
    fields = getattr(value, "_fields", None)
    if fields:
        return {field: getattr(value, field, None) for field in fields}
    if hasattr(value, "__dict__"):
        return {
            key: item
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }
    return {}


def _trade_context(trade_params: Any) -> Any:
    if isinstance(trade_params, dict):
        return trade_params
    nested = getattr(trade_params, "trade_parameters", None)
    return nested if nested is not None else trade_params


def trade_value(trade_params: Any, key: str, default: Any = None) -> Any:
    source = _trade_context(trade_params)
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def set_trade_value(trade_params: Any, key: str, value: Any) -> None:
    source = _trade_context(trade_params)
    if isinstance(source, dict):
        source[key] = value
    else:
        setattr(source, key, value)
    if source is not trade_params and not isinstance(trade_params, dict):
        setattr(trade_params, key, value)


def is_vnext_broker_net_cost_required(
    config: dict[str, Any] | None,
    trade_params: Any,
) -> bool:
    cfg = _mapping((_mapping(config)).get("gtos_vnext_runtime"))
    if not _as_bool(cfg.get("enabled"), False):
        return False
    if not _as_bool(cfg.get("apply_to_execution"), False):
        return False
    if str(cfg.get("mode") or "").strip().lower() != "production_replacement_vnext_moonshot":
        return False
    return bool(
        trade_value(trade_params, "gtos_vnext_production_execution_path")
        or trade_value(trade_params, "gtos_vnext_selected_cell_risk_cell_id")
        or trade_value(trade_params, "gtos_vnext_selected_cell_risk_pct") is not None
    )


def _instrument_market_config(
    config: dict[str, Any] | None,
    *,
    symbol: str | None,
    broker_symbol: str | None,
) -> dict[str, Any]:
    cfg = _mapping(config)
    instruments = _mapping(cfg.get("instruments"))
    candidates = [
        symbol,
        broker_symbol,
        str(symbol or "").replace(".", "_"),
        str(broker_symbol or "").replace(".", "_"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        row = _mapping(instruments.get(str(candidate)))
        market = _mapping(row.get("market"))
        if market:
            return dict(market)
    return {}


def _first_present(*sources: dict[str, Any], names: tuple[str, ...]) -> Any:
    for source in sources:
        for name in names:
            value = source.get(name)
            if value not in (None, ""):
                return value
    return None


def _symbol_spec_packet(
    config: dict[str, Any] | None,
    *,
    symbol: str,
    broker_symbol: str,
    symbol_info: Any,
) -> dict[str, Any]:
    cfg = _mapping(config)
    info = _snapshot(symbol_info)
    instrument_market = _instrument_market_config(
        config, symbol=symbol, broker_symbol=broker_symbol
    )
    top_market = _mapping(cfg.get("market"))
    fields: dict[str, Any] = {}
    field_status: dict[str, str] = {}
    for output_field, names in SPEC_FIELD_CANDIDATES.items():
        value = _first_present(info, instrument_market, top_market, names=names)
        fields[output_field] = value
        field_status[output_field] = "captured" if value not in (None, "") else "missing"
    source_refs = []
    if info:
        source_refs.append("mt5_symbol_info_snapshot")
    if instrument_market:
        source_refs.append("config.instruments.<symbol>.market")
    if top_market:
        source_refs.append("config.market")
    required_missing = [
        key
        for key in (
            "point",
            "trade_tick_size",
            "trade_tick_value",
            "trade_contract_size",
            "volume_min",
            "volume_step",
            "trade_stops_level",
            "trade_freeze_level",
            "trade_mode",
        )
        if fields.get(key) in (None, "")
    ]
    return {
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "fields": fields,
        "field_status": field_status,
        "source_refs": source_refs,
        "source_status": "captured" if not required_missing else "source_gap",
        "required_missing_fields": required_missing,
    }


def _explicit_session_table_packet(
    config: dict[str, Any] | None,
    *,
    symbol: str,
    broker_symbol: str,
    symbol_info: Any,
) -> dict[str, Any]:
    cfg = _mapping(config)
    info = _snapshot(symbol_info)
    instrument_market = _instrument_market_config(
        config, symbol=symbol, broker_symbol=broker_symbol
    )
    top_market = _mapping(cfg.get("market"))
    captures = []
    for source_ref, source in (
        ("mt5_symbol_info_snapshot", info),
        ("config.instruments.<symbol>.market", instrument_market),
        ("config.market", top_market),
    ):
        for field in EXPLICIT_SESSION_TABLE_CANDIDATES:
            value = source.get(field)
            if value not in (None, "", [], {}):
                captures.append(
                    {
                        "source_ref": source_ref,
                        "field": field,
                        "value_type": type(value).__name__,
                    }
                )
    return {
        "source_status": "captured" if captures else "source_gap",
        "capture_count": len(captures),
        "captures": captures,
        "candidate_fields": list(EXPLICIT_SESSION_TABLE_CANDIDATES),
        "authority_note": (
            "trade_mode availability is not explicit trading-session table authority"
        ),
    }


def _profile_packet(config: dict[str, Any] | None) -> dict[str, Any]:
    cfg = _mapping(config)
    profile = _mapping(cfg.get("broker_profile"))
    runtime = _mapping(cfg.get("runtime"))
    namespace = broker_account_namespace(cfg)
    return {
        "profile_name": cfg.get("profile_name") or profile.get("broker"),
        "broker_account_namespace": namespace or None,
        "broker": profile.get("broker"),
        "company": profile.get("company"),
        "server": profile.get("server"),
        "dual_broker_role": _mapping(cfg.get("dual_broker")).get("role"),
        "runtime_profile_namespace": runtime.get("profile_namespace"),
        "source_status": "captured" if namespace else "source_gap",
    }


def _tick_packet(tick: Any, sl_distance: float | None) -> dict[str, Any]:
    tick_row = _snapshot(tick)
    bid = _as_float(tick_row.get("bid") if tick_row else getattr(tick, "bid", None))
    ask = _as_float(tick_row.get("ask") if tick_row else getattr(tick, "ask", None))
    spread_price = abs(ask - bid) if bid is not None and ask is not None else None
    spread_r = None
    if spread_price is not None and sl_distance and sl_distance > 0:
        spread_r = spread_price / sl_distance
    tick_time = tick_row.get("time") if tick_row else getattr(tick, "time", None)
    if hasattr(tick_time, "isoformat"):
        tick_time = tick_time.isoformat()
    return {
        "bid": bid,
        "ask": ask,
        "time_utc": tick_time,
        "spread_price": spread_price,
        "spread_cents": _as_float(
            tick_row.get("spread_cents") if tick_row else getattr(tick, "spread_cents", None)
        ),
        "spread_r": spread_r,
        "source_status": "captured" if spread_r is not None else "source_gap",
    }


def _side_from_trade(trade_params: Any) -> str | None:
    value = (
        trade_value(trade_params, "direction")
        or trade_value(trade_params, "side")
        or trade_value(trade_params, "order_side")
    )
    text = str(value or "").strip().upper()
    if text in {"LONG", "BUY"}:
        return "LONG"
    if text in {"SHORT", "SELL"}:
        return "SHORT"
    return None


_SCORE_CACHE: dict[str, dict[str, float | None]] = {}
_SCORE_LOCK = threading.Lock()


def _on_challenge() -> bool:
    try:
        from src.judgment.state_choices import on_challenge
    except Exception:
        return False
    try:
        return bool(on_challenge())
    except Exception:
        return False


def _finite_score(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _score_block(block: Any) -> float | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    parsed = None
    try:
        from src.judgment.jev_questions import returned_number

        parsed = _finite_score(returned_number(block))
    except Exception:
        parsed = None
    raw = None
    if block.get("score") is not None:
        raw = block.get("score")
    elif block.get("Score") is not None:
        raw = block.get("Score")
    elif block.get("value") is not None:
        raw = block.get("value")
    number = _finite_score(raw)
    if parsed is not None and number is not None and parsed != number:
        return None
    if parsed is not None:
        return parsed
    return number


def _challenge_scores(
    spot: str,
    facts: dict[str, Any],
    questions: dict[str, str],
) -> dict[str, float | None]:
    """One Score post for this state. Empty, error, or disagreement is None.

    Friends never call this. The cache key is the facts, so a new quote or
    config is a new ask. The socket wait is the stored dynamic timeout when
    one has already been returned; otherwise the ask has no timeout.
    """

    if not questions:
        return {}
    blob = json.dumps(
        {"spot": spot, "facts": facts, "questions": questions},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    key = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    with _SCORE_LOCK:
        cached = _SCORE_CACHE.get(key)
    if cached is not None:
        return dict(cached)
    empty = {name: None for name in questions}
    try:
        from src.judgment.jev_client import resolve_key
        from src.judgment.state_choices import MODEL, API_URL
    except Exception:
        return empty
    token, _source = resolve_key()
    if not token:
        return empty
    payload = {
        "model": MODEL,
        "state": {"spot": spot, "facts": facts},
        "questions": {
            name: {
                "type": "score",
                "instructions": text,
            }
            for name, text in questions.items()
        },
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-judgment/0.1",
        },
    )
    wait = None
    try:
        from src.judgment.jev_client import _stored_score

        stored = _stored_score("jev_call_timeout")
        if stored is not None and stored > 0:
            wait = stored
    except Exception:
        wait = None
    try:
        with urllib.request.urlopen(req, timeout=wait) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return empty
    except Exception:
        return empty
    answers = body.get("answers") if isinstance(body, dict) else None
    if not isinstance(answers, dict):
        return empty
    out = {name: _score_block(answers.get(name)) for name in questions}
    with _SCORE_LOCK:
        _SCORE_CACHE[key] = dict(out)
    return out


def _swap_clock_bounds(runtime_cfg: dict[str, Any]) -> tuple[float | None, float | None]:
    """Bar minutes and interest day-count. A missing config value is a hop.

    Off the Challenge writer the historical constants stay, so a friend book
    is unchanged. On the Challenge writer an empty score stays unset.
    """

    minutes = _as_float(runtime_cfg.get("selected_cell_swap_cost_minutes_per_bar"))
    days = _as_float(runtime_cfg.get("selected_cell_swap_interest_days_per_year"))
    if minutes is not None and days is not None:
        return minutes, days
    if not _on_challenge():
        return (
            15.0 if minutes is None else minutes,
            360.0 if days is None else days,
        )
    questions: dict[str, str] = {}
    if minutes is None:
        questions["minutes_per_bar"] = (
            "The score you return is how many minutes one bar of this state lasts. "
            "An empty score leaves the bar length unset. This question does not send."
        )
    if days is None:
        questions["interest_days_per_year"] = (
            "The score you return is the interest day-count for this swap state. "
            "An empty score leaves the day-count unset. This question does not send."
        )
    got = _challenge_scores(
        "broker_net_cost.swap_clock",
        {
            "minutes_configured": minutes is not None,
            "days_configured": days is not None,
        },
        questions,
    )
    if minutes is None:
        minutes = got.get("minutes_per_bar")
    if days is None:
        days = got.get("interest_days_per_year")
    return minutes, days


def _resolve_max_with_sleeve_override(
    runtime_cfg: dict[str, Any],
    base_key: str,
    by_sleeve_key: str,
    default: float | None,
    sleeve: str | None,
) -> float | None:
    """Effective cost-gate ceiling: the per-sleeve override (runtime_cfg[by_sleeve_key][sleeve]) when
    present, else the global runtime ceiling, else `default`. Lets a tiny-stop session sleeve (fx_jpy /
    fx_jpy_ny on M15, where a normal JPY-cross spread is a large fraction of the ~8-pip stop) run a looser
    spread/total-cost ceiling for an owner-approved live trial WITHOUT relaxing the gate for any other
    sleeve. Absent the override key, behaviour is byte-identical to before (global ceiling / default)."""
    base = _as_float(runtime_cfg.get(base_key))
    if base is None:
        base = default
    overrides = _mapping(runtime_cfg.get(by_sleeve_key))
    if sleeve and sleeve in overrides:
        override = _as_float(overrides.get(sleeve))
        if override is not None:
            return override
    return base


def _swap_cost_packet(
    *,
    runtime_cfg: dict[str, Any],
    trade_params: Any,
    spec: dict[str, Any],
    swap_value: Any,
    entry_price: float | None,
    sl_distance: float | None,
    entry_utc: Any = None,
    exit_utc: Any = None,
    server: Any = None,
) -> dict[str, Any]:
    """Convert adverse broker swap into pretrade R cost when the units are source-bound.

    MT5 swap mode 1 is points. In that mode the conversion is volume-independent:
    adverse_swap_points * point / stop_distance gives daily swap drag in R, then
    the configured/native time-stop horizon scales it to expected holding R.
    MT5 interest modes 5/6 use an annual percentage of current/open price; those
    are also volume-independent in R after dividing by the stop distance.
    Currency-denominated modes need post-sizing volume/cash-risk conversion and
    are left as source gaps here.
    """
    fields = _mapping(spec.get("fields"))
    swap = _as_float(swap_value)
    mode = _as_float(fields.get("swap_mode"))
    point = _as_float(fields.get("point"))
    rollover3days = _as_float(fields.get("swap_rollover3days"))
    raw_bars = (
        trade_value(trade_params, "gtos_vnext_dynamic_time_stop_bars")
        or runtime_cfg.get("selected_cell_swap_cost_time_stop_bars")
    )
    holding_bars = _as_float(raw_bars)
    minutes_per_bar, interest_days = _swap_clock_bounds(runtime_cfg)
    raw_holding_days = None
    if (
        holding_bars is not None
        and holding_bars > 0
        and minutes_per_bar is not None
        and minutes_per_bar > 0
    ):
        raw_holding_days = holding_bars * minutes_per_bar / 1440.0
    else:
        default_days = _as_float(runtime_cfg.get("selected_cell_swap_cost_default_hold_days"))
        if default_days is not None and default_days >= 0:
            raw_holding_days = default_days
    cap_days = _as_float(runtime_cfg.get("selected_cell_swap_cost_horizon_days_cap"))
    holding_days = raw_holding_days
    horizon_capped = False
    if (
        holding_days is not None
        and cap_days is not None
        and cap_days >= 0
        and holding_days > cap_days
    ):
        holding_days = cap_days
        horizon_capped = True

    entry_instant = _aware_utc(entry_utc)
    exit_instant = _aware_utc(exit_utc)
    server_name = str(server or "").strip()
    rollover_detail: dict[str, Any] = {}
    swap_charge_units = holding_days
    swap_charge_basis = "modelled_fractional_holding_days_no_entry_instant"

    # ---- B-COST-1: the horizon this packet charges against -----------------------------------
    # Swap is a financing charge levied AT the broker's rollover instant on positions that are
    # open across it. It is not a function of elapsed time: measured on 299 closed positions
    # across both live accounts (2026-07-25 export, `*_history_deals_get.jsonl`), 0 positions
    # carry a nonzero swap without crossing a broker-wall midnight -- including holds of 14.7 h
    # (FTMO) and 17.9 h (redacted_account). Crossing is the whole rule.
    #
    # `holding_days` above is a FORECAST -- the planned time stop, read from
    # `gtos_vnext_dynamic_time_stop_bars`. Charging rollover crossings against a forecast is
    # correct pretrade (nothing else is knowable) and WRONG afterwards, because the realized
    # hold is almost always shorter. Measured on the sealed five-month census
    # (F1_TRADE_EXCURSION_CENSUS_V1.parquet, 146,736 filled trades): the forecast was a flat
    # 8.00 h against a 1.98 h sealed lifecycle horizon and a 21-minute median realized hold, so
    # 29,338 trades were charged a full night, 87.9% of that charge landed on trades held under
    # an hour, and the true realized crossings were 0 -- every one of them.
    #
    # So: when the caller knows how the trade actually ended, the realized interval decides.
    # `exit_utc` absent keeps the pretrade estimate byte-for-byte what it was; this matters
    # because `total_cost_r` feeds the live pre-trade refusal at :990-994 on ARMED accounts.
    realized_basis = entry_instant is not None and exit_instant is not None
    horizon_hours = None if holding_days is None else float(holding_days) * 24.0
    horizon_source = "forecast_planned_time_stop"
    if realized_basis:
        elapsed = (exit_instant - entry_instant).total_seconds() / 3600.0
        if elapsed >= 0:
            horizon_hours = elapsed
            horizon_source = "realized_entry_to_exit_elapsed"
        else:
            realized_basis = False
            horizon_source = "source_gap_exit_before_entry"

    if entry_utc not in (None, ""):
        if entry_instant is None:
            swap_charge_units = None
            swap_charge_basis = "source_gap_invalid_or_naive_entry_utc"
        elif not server_name:
            swap_charge_units = None
            swap_charge_basis = "source_gap_broker_server_missing"
        elif horizon_hours is not None:
            try:
                swap_charge_units, rollover_detail = rollover_nights(
                    entry_instant,
                    horizon_hours,
                    server=server_name,
                    rollover3days_weekday=(
                        int(rollover3days) if rollover3days is not None else None
                    ),
                )
                swap_charge_basis = (
                    "broker_wall_midnight_crossings_realized"
                    if realized_basis
                    else "broker_wall_midnight_crossings"
                )
            except (UnknownBrokerClockError, TypeError, ValueError) as exc:
                swap_charge_units = None
                swap_charge_basis = "source_gap_broker_rollover_clock"
                rollover_detail = {"error": f"{type(exc).__name__}:{exc}"}

    # ---- B9: favourable carry -------------------------------------------------------------
    # `elif swap >= 0` below books a swap the broker PAYS as a cost of exactly 0.00, and it does
    # so by short-circuiting: on that branch no mode/point/clock validation runs at all, so the
    # packet reports `source_status: "captured"` with an empty `missing_fields` even when the
    # conversion is unavailable. Two consequences, and they have different remedies:
    #
    #   * RESEARCH -- 0 of 632,934 cached `swap_cost_r` values is negative
    #     (`B9_CLAMP_EVIDENCE_V1.json`); the estate's own numbers understate favourable-carry
    #     sleeves. `energy_agri` is ARMED and both its instruments carry positive `swap_long`.
    #   * LIVE -- `total_cost_r` (:768-773) feeds the hard pre-trade refusal at :990-994 against
    #     `selected_cell_pretrade_max_total_cost_r` (0.15), and `execution.py:3438-3444` returns
    #     None on a refusal. Overstating cost there is CONSERVATIVE: it refuses trades it should
    #     admit. That is a live-behaviour change on armed money, so it is owner-gated.
    #
    # The credit is therefore always MEASURED and reported, and only ever carries decision
    # authority behind `selected_cell_swap_credit_favourable_carry` (default False). With the key
    # absent every field this function already emitted is bit-identical to before.
    #
    # The credit is real money, not a spec artifact: 7 of 37 nonzero-swap FTMO deals in the
    # 2026-07-25 export were POSITIVE (`B9_REALIZED_SWAP_V1.json`), and realized sign agrees with
    # the spec-table sign on 17 of 18 FTMO symbol/sides -- the one exception (US500.cash SHORT)
    # is a table that moved between the deals and the snapshot, not a broken convention.
    credit_authority = _as_bool(runtime_cfg.get("selected_cell_swap_credit_favourable_carry"), False)
    favourable_swap_points = None
    daily_price_credit = None
    daily_cost_r_carry_credited = None
    cost_r_carry_credited = None
    credit_missing: list[str] = []

    missing: list[str] = []
    unsupported: list[str] = []
    cost_r = None
    daily_cost_r = None
    daily_price_drag = None
    adverse_swap_points = None
    if swap is None:
        missing.append("swap_value")
    elif swap >= 0:
        cost_r = 0.0
        daily_cost_r = 0.0
        adverse_swap_points = 0.0
        favourable_swap_points = float(swap)
        # Mirror of the adverse arithmetic below, sign-flipped. Validated the same way, so a
        # favourable side with a missing point or an unresolvable clock now reports a source gap
        # on the CREDIT instead of a silent zero -- while `cost_r` stays 0.0 by default.
        if mode is None:
            credit_missing.append("swap_mode")
        if sl_distance is None or sl_distance <= 0:
            credit_missing.append("sl_distance")
        if holding_days is None:
            credit_missing.append("holding_days")
        if swap_charge_units is None:
            credit_missing.append("swap_charge_units")
        if mode == 1.0:
            if point is None or point <= 0:
                credit_missing.append("point")
            if not credit_missing:
                daily_price_credit = -favourable_swap_points * float(point)
        elif mode in {5.0, 6.0}:
            credit_price = _as_float(
                entry_price if entry_price is not None else trade_value(trade_params, "entry_price")
            )
            credit_dpy = interest_days
            if credit_price is None or credit_price <= 0:
                credit_missing.append("entry_price")
            if credit_dpy is None or credit_dpy <= 0:
                credit_missing.append("swap_interest_days_per_year")
            if not credit_missing:
                daily_price_credit = -float(credit_price) * (favourable_swap_points / 100.0) / float(credit_dpy)
        elif mode is not None:
            credit_missing.append(f"swap_mode:{mode:g}")
        if daily_price_credit is not None:
            daily_cost_r_carry_credited = daily_price_credit / float(sl_distance)
            cost_r_carry_credited = daily_cost_r_carry_credited * float(swap_charge_units)
            if credit_authority:
                daily_cost_r = daily_cost_r_carry_credited
                daily_price_drag = daily_price_credit
                cost_r = cost_r_carry_credited
    else:
        adverse_swap_points = abs(swap)
        if mode is None:
            missing.append("swap_mode")
        if sl_distance is None or sl_distance <= 0:
            missing.append("sl_distance")
        if holding_days is None:
            missing.append("holding_days")
        if entry_utc not in (None, "") and entry_instant is None:
            missing.append("aware_entry_utc")
        if entry_instant is not None and not server_name:
            missing.append("broker_server")
        if swap_charge_units is None and not any(
            field in missing for field in ("aware_entry_utc", "broker_server")
        ):
            unsupported.append("broker_rollover_clock")
        if mode == 1.0:
            if point is None or point <= 0:
                missing.append("point")
            if not missing and not unsupported:
                daily_price_drag = adverse_swap_points * float(point)
                daily_cost_r = daily_price_drag / float(sl_distance)
                cost_r = daily_cost_r * float(swap_charge_units)
        elif mode in {5.0, 6.0}:
            price = _as_float(entry_price if entry_price is not None else trade_value(trade_params, "entry_price"))
            days_per_year = interest_days
            if price is None or price <= 0:
                missing.append("entry_price")
            if days_per_year is None or days_per_year <= 0:
                missing.append("swap_interest_days_per_year")
            if not missing and not unsupported:
                daily_price_drag = float(price) * (adverse_swap_points / 100.0) / float(days_per_year)
                daily_cost_r = daily_price_drag / float(sl_distance)
                cost_r = daily_cost_r * float(swap_charge_units)
        elif mode is not None:
            unsupported.append(f"swap_mode:{mode:g}")
        if cost_r is not None:
            cost_r = daily_cost_r * float(swap_charge_units)

    source_status = "captured" if cost_r is not None else "source_gap"
    return {
        "model_version": (
            "broker_rollover_crossing_swap_cost_r_v2"
            if swap_charge_basis == "broker_wall_midnight_crossings"
            else "points_mode_time_stop_swap_cost_r_v1"
        ),
        "source_status": source_status,
        "cost_r": cost_r,
        "daily_cost_r": daily_cost_r,
        "daily_price_drag": daily_price_drag,
        "swap_value": swap,
        "swap_mode": int(mode) if mode is not None and float(mode).is_integer() else mode,
        "swap_mode_interpretation": (
            "points"
            if mode == 1.0
            else "annual_interest_current_or_open_price"
            if mode in {5.0, 6.0}
            else "unsupported_or_missing"
        ),
        "point": point,
        "adverse_swap_points": adverse_swap_points,
        "entry_price": _as_float(entry_price if entry_price is not None else trade_value(trade_params, "entry_price")),
        "interest_days_per_year": interest_days,
        "holding_bars": holding_bars,
        "minutes_per_bar": minutes_per_bar,
        "uncapped_estimated_holding_days": raw_holding_days,
        "horizon_days_cap": cap_days,
        "horizon_capped": horizon_capped,
        "estimated_holding_days": holding_days,
        "entry_utc": entry_instant.isoformat() if entry_instant is not None else None,
        "exit_utc": exit_instant.isoformat() if exit_instant is not None else None,
        "broker_server": server_name or None,
        "swap_charge_basis": swap_charge_basis,
        "swap_charge_units": swap_charge_units,
        # B-COST-1: publish the horizon this charge was computed against, and where it came
        # from, so a forecast/lifecycle disagreement is visible instead of silent. The sealed
        # census carried a 4x disagreement (8.00 h forecast vs a 1.98 h lifecycle horizon) that
        # nothing could see, because only the resulting cost was ever written down.
        "swap_horizon_hours_used": horizon_hours,
        "swap_horizon_source": horizon_source,
        "swap_charge_is_realized": realized_basis,
        "rollover_nights_charged": rollover_detail.get("nights_charged"),
        "rollover_crossings": list(rollover_detail.get("crossings") or ()),
        "rollover_clock_error": rollover_detail.get("error"),
        "swap_rollover3days": int(rollover3days) if rollover3days is not None else None,
        "missing_fields": missing,
        "unsupported_fields": unsupported,
        # B9. The hook was already here, hardcoded False since the 2026-07-25 foundation
        # snapshot, read by nothing. It now reports the truth.
        "favorable_swap_credit_applied": bool(credit_authority and cost_r_carry_credited is not None),
        "carry_credit_authority": credit_authority,
        "favourable_swap_points": favourable_swap_points,
        "daily_price_credit": daily_price_credit,
        "daily_cost_r_carry_credited": daily_cost_r_carry_credited,
        # Signed R the broker pays over the charged nights. NEGATIVE = a credit. Always measured;
        # only reaches `cost_r` when `selected_cell_swap_credit_favourable_carry` is true.
        "cost_r_carry_credited": cost_r_carry_credited,
        # The R the default (clamped) path discards. >= 0 by construction; 0.0 on adverse sides.
        "credit_r_foregone": (
            None if cost_r_carry_credited is None else max(0.0, -cost_r_carry_credited)
        ),
        "credit_source_status": (
            "not_applicable_adverse_or_absent_swap"
            if favourable_swap_points is None
            else ("captured" if cost_r_carry_credited is not None else "source_gap")
        ),
        "credit_missing_fields": credit_missing,
    }


def _commission_cost_packet(
    *,
    mode: str,
    profile: dict[str, Any],
    broker_symbol: str,
    entry_price: float | None,
    sl_distance: float | None,
    spec: dict[str, Any],
) -> dict[str, Any]:
    """Resolve round-turn broker commission and convert it into candidate R.

    The default path deliberately has no config switch.  The only zero-commission behavior is
    the explicitly named comparator mode used by offline A/B tooling.  A missing account,
    instrument, notional price, stop, or cash-to-price conversion remains missing and therefore
    fails the live packet closed; it is never coerced to zero.
    """
    if mode not in {BROKER_TRUE_COMMISSION_MODE, LEGACY_ZERO_COMMISSION_COMPARATOR_MODE}:
        raise ValueError(f"unsupported commission_mode:{mode}")

    provenance = (
        "src.costs.model.commission_usd_per_lot_for_packet:"
        "BROKER_TRUE_COSTS_V1.json + current symbol_spec trade_tick_value/trade_tick_size "
        "+ candidate sl_distance"
    )
    if mode == LEGACY_ZERO_COMMISSION_COMPARATOR_MODE:
        return {
            "model_version": COMMISSION_COST_MODEL_VERSION,
            "mode": mode,
            "source_status": "explicit_comparator",
            "cost_r": None,
            "usd_per_lot_round_turn": None,
            "usd_per_price_unit_per_lot": None,
            "entry_price": entry_price,
            "sl_distance": sl_distance,
            "broker_symbol": broker_symbol,
            "account_namespace": profile.get("broker_account_namespace"),
            "server": profile.get("server"),
            "artifact": "BROKER_TRUE_COSTS_V1.json",
            "provenance": provenance,
            "included_in_total_cost_r": False,
            "missing_fields": [],
            "comparator_only": True,
            "comparator_note": (
                "reproduces the pre-CN status-only zero-commission decision surface; "
                "never selected by config or a live caller"
            ),
        }

    fields = _mapping(spec.get("fields"))
    tick_value = _as_float(fields.get("trade_tick_value"))
    tick_size = _as_float(fields.get("trade_tick_size"))
    usd_per_price_unit_per_lot = None
    missing: list[str] = []
    if sl_distance is None or sl_distance <= 0:
        missing.append("sl_distance")
    if tick_value is None or tick_value <= 0:
        missing.append("trade_tick_value")
    if tick_size is None or tick_size <= 0:
        missing.append("trade_tick_size")
    if tick_value is not None and tick_value > 0 and tick_size is not None and tick_size > 0:
        usd_per_price_unit_per_lot = tick_value / tick_size

    usd_per_lot = commission_usd_per_lot_for_packet(
        broker_symbol,
        server=profile.get("server"),
        namespace=profile.get("broker_account_namespace"),
        entry_price=entry_price,
    )
    if usd_per_lot is None:
        missing.append("broker_true_commission_schedule_or_required_entry_price")

    cost_r = None
    if not missing and usd_per_price_unit_per_lot is not None:
        cost_r = float(usd_per_lot) / (
            float(sl_distance) * float(usd_per_price_unit_per_lot)
        )
    return {
        "model_version": COMMISSION_COST_MODEL_VERSION,
        "mode": mode,
        "source_status": "captured" if cost_r is not None else "source_gap",
        "cost_r": cost_r,
        "usd_per_lot_round_turn": usd_per_lot,
        "usd_per_price_unit_per_lot": usd_per_price_unit_per_lot,
        "entry_price": entry_price,
        "sl_distance": sl_distance,
        "broker_symbol": broker_symbol,
        "account_namespace": profile.get("broker_account_namespace"),
        "server": profile.get("server"),
        "artifact": "BROKER_TRUE_COSTS_V1.json",
        "provenance": provenance,
        "included_in_total_cost_r": cost_r is not None,
        "missing_fields": sorted(set(missing)),
        "comparator_only": False,
    }


def build_pretrade_cost_packet(
    *,
    config: dict[str, Any] | None,
    trade_params: Any,
    tick: Any,
    symbol: str | None = None,
    broker_symbol: str | None = None,
    entry_price: float | None = None,
    stop_loss: float | None = None,
    sl_distance: float | None = None,
    risk_pct: float | None = None,
    symbol_info: Any = None,
    asof_utc: str | None = None,
    commission_mode: str = BROKER_TRUE_COMMISSION_MODE,
) -> dict[str, Any]:
    cfg = _mapping(config)
    runtime_cfg = _mapping(cfg.get("gtos_vnext_runtime"))
    clean_symbol = str(
        symbol
        or _mapping(cfg.get("market")).get("symbol")
        or trade_value(trade_params, "source_symbol")
        or "UNKNOWN"
    )
    clean_broker_symbol = str(
        broker_symbol
        or _mapping(cfg.get("market")).get("mt5_symbol")
        or clean_symbol
    )
    required = is_vnext_broker_net_cost_required(cfg, trade_params)
    stop_loss = _as_float(stop_loss if stop_loss is not None else trade_value(trade_params, "stop_loss"))
    entry_price = _as_float(entry_price if entry_price is not None else trade_value(trade_params, "entry_price"))
    if sl_distance is None and entry_price is not None and stop_loss is not None:
        sl_distance = abs(entry_price - stop_loss)
    sl_distance = _as_float(sl_distance)
    side = _side_from_trade(trade_params)
    tick_cost = _tick_packet(tick, sl_distance)
    spec = _symbol_spec_packet(
        cfg,
        symbol=clean_symbol,
        broker_symbol=clean_broker_symbol,
        symbol_info=symbol_info,
    )
    explicit_session_table = _explicit_session_table_packet(
        cfg,
        symbol=clean_symbol,
        broker_symbol=clean_broker_symbol,
        symbol_info=symbol_info,
    )
    profile = _profile_packet(cfg)

    allowed_commission_statuses = set(
        runtime_cfg.get("selected_cell_allowed_commission_model_statuses")
        or DEFAULT_ALLOWED_COMMISSION_STATUSES
    )
    commission_status = str(
        trade_value(trade_params, "gtos_vnext_commission_model_status") or ""
    ).strip()
    swap_field = "swap_long" if side == "LONG" else "swap_short" if side == "SHORT" else None
    swap_value = (
        _first_present(
            spec["fields"],
            _instrument_market_config(cfg, symbol=clean_symbol, broker_symbol=clean_broker_symbol),
            _mapping(cfg.get("market")),
            names=(swap_field,),
        )
        if swap_field
        else None
    )
    expected_slippage_r = _as_float(
        trade_value(trade_params, "gtos_vnext_expected_slippage_r")
        or trade_value(trade_params, "gtos_vnext_slippage_r")
        or runtime_cfg.get("selected_cell_default_expected_slippage_r")
    )
    expected_slippage_source = (
        "trade_params"
        if trade_value(trade_params, "gtos_vnext_expected_slippage_r")
        or trade_value(trade_params, "gtos_vnext_slippage_r")
        else "config.selected_cell_default_expected_slippage_r"
        if expected_slippage_r is not None
        else None
    )
    swap_cost = _swap_cost_packet(
        runtime_cfg=runtime_cfg,
        trade_params=trade_params,
        spec=spec,
        swap_value=swap_value,
        entry_price=entry_price,
        sl_distance=sl_distance,
        entry_utc=asof_utc,
        # Pretrade there is no exit instant, so this resolves to None and the estimate is
        # unchanged. A post-lifecycle caller that knows how the trade ended passes
        # `gtos_vnext_exit_utc` and gets the realized crossing count instead of a forecast.
        exit_utc=trade_value(trade_params, "gtos_vnext_exit_utc"),
        server=profile.get("server"),
    )
    commission_cost = _commission_cost_packet(
        mode=commission_mode,
        profile=profile,
        broker_symbol=clean_broker_symbol,
        entry_price=entry_price,
        sl_distance=sl_distance,
        spec=spec,
    )

    cost_sleeve = _mapping(
        trade_value(trade_params, "gtos_vnext_source_event_details")
    ).get("sleeve")
    cost_sleeve = str(cost_sleeve) if cost_sleeve else None
    max_spread_r = _resolve_max_with_sleeve_override(
        runtime_cfg,
        "selected_cell_pretrade_max_spread_r",
        "selected_cell_pretrade_max_spread_r_by_sleeve",
        None,
        cost_sleeve,
    )
    max_spread_bound_unset = False
    if max_spread_r is None:
        if not _on_challenge():
            max_spread_r = 0.10
        else:
            asked_spread = _challenge_scores(
                "broker_net_cost.max_spread_r",
                {"sleeve": cost_sleeve, "symbol": clean_symbol},
                {
                    "max_spread_r": (
                        "The score you return is the spread ceiling in R for this state. "
                        "An empty score leaves the ceiling unset and does not send."
                    ),
                },
            )
            max_spread_r = asked_spread.get("max_spread_r")
            max_spread_bound_unset = max_spread_r is None
    total_cost_r = None
    commission_r = _as_float(commission_cost.get("cost_r"))
    commission_term_ready = (
        commission_mode == LEGACY_ZERO_COMMISSION_COMPARATOR_MODE
        or commission_r is not None
    )
    total_cost_r_carry_credited = None
    if tick_cost["spread_r"] is not None and commission_term_ready:
        total_cost_r = (
            float(tick_cost["spread_r"])
            + float(expected_slippage_r or 0.0)
            + float(swap_cost.get("cost_r") or 0.0)
            + float(commission_r or 0.0)
        )
        # B9. Same sum with the favourable-carry credit applied, ALWAYS computed so the number is
        # observable in every packet and every log. It is not the gate input unless
        # `selected_cell_swap_credit_favourable_carry` is true -- in which case `swap_cost["cost_r"]`
        # already carries the credit and the two totals coincide.
        swap_signed = swap_cost.get("cost_r_carry_credited")
        if swap_signed is None:
            swap_signed = swap_cost.get("cost_r")
        total_cost_r_carry_credited = (
            float(tick_cost["spread_r"])
            + float(expected_slippage_r or 0.0)
            + float(swap_signed or 0.0)
            + float(commission_r or 0.0)
        )
    max_total_cost_r = _resolve_max_with_sleeve_override(
        runtime_cfg,
        "selected_cell_pretrade_max_total_cost_r",
        "selected_cell_pretrade_max_total_cost_r_by_sleeve",
        None,
        cost_sleeve,
    )
    limit_tolerance_r = _as_float(runtime_cfg.get("selected_cell_pretrade_cost_limit_tolerance_r"))
    if limit_tolerance_r is None:
        limit_tolerance_r = 1e-6
    trade_mode = _as_float(spec["fields"].get("trade_mode"))

    packet = {
        "schema_version": PRETRADE_COST_PACKET_SCHEMA_VERSION,
        "model_version": "vnext_selected_cell_pretrade_cost_model_v3",
        "status": "NOT_APPLICABLE" if not required else "CHECKED",
        "authority": "broker_calibrated_replay_cost",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_gap_cost_fallback_blocked": False,
        "asof_utc": asof_utc or utc_now_iso(),
        "evidence_class": "pretrade_broker_profile_quote_symbol_spec_cost_packet",
        "result_use_status": "pretrade_gate_input_not_broker_realized_outcome",
        "symbol": clean_symbol,
        "broker_symbol": clean_broker_symbol,
        "side": side,
        "risk_pct": risk_pct,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "sl_distance": sl_distance,
        "selected_cell_risk_cell_id": trade_value(
            trade_params, "gtos_vnext_selected_cell_risk_cell_id"
        ),
        "selected_cell_risk_decision_basis": trade_value(
            trade_params, "gtos_vnext_selected_cell_risk_decision_basis"
        ),
        "profile": profile,
        "symbol_spec": spec,
        "tick_cost": tick_cost,
        "spread_price": tick_cost["spread_price"],
        "spread_r": tick_cost["spread_r"],
        "max_spread_r": max_spread_r,
        "max_spread_bound_unset": max_spread_bound_unset,
        "commission_model_status": commission_status or None,
        "commission_model_required": _as_bool(
            runtime_cfg.get("selected_cell_commission_model_required"),
            True,
        ),
        "allowed_commission_model_statuses": sorted(allowed_commission_statuses),
        "commission_cost": commission_cost,
        "commission_r": commission_r,
        "commission_cost_model_required": (
            required and commission_mode == BROKER_TRUE_COMMISSION_MODE
        ),
        "commission_cost_authority": "broker_true_costs_v1",
        "commission_cost_provenance": commission_cost.get("provenance"),
        "commission_mode": commission_mode,
        "swap": {
            "side_field": swap_field,
            "value": _as_float(swap_value),
            "source_status": "captured" if swap_value not in (None, "") else "source_gap",
            "cost_r": swap_cost.get("cost_r"),
            "cost_r_source_status": swap_cost.get("source_status"),
        },
        "swap_cost": swap_cost,
        "expected_slippage_r": expected_slippage_r,
        "expected_slippage_source": expected_slippage_source,
        "total_cost_r": total_cost_r,
        # B9. Observable-only unless the credit has authority; never read by
        # `pretrade_cost_refusal_reasons`, which keeps gating on `total_cost_r`.
        "total_cost_r_carry_credited": total_cost_r_carry_credited,
        "carry_credit_r_foregone": swap_cost.get("credit_r_foregone"),
        "carry_credit_authority": swap_cost.get("carry_credit_authority"),
        "total_cost_components": {
            "spread_r": tick_cost["spread_r"],
            "expected_slippage_r": expected_slippage_r,
            "swap_cost_r": swap_cost.get("cost_r"),
            "commission_r": commission_r,
        },
        "total_cost_components_expected": list(TOTAL_COST_COMPONENTS),
        "cost_excludes": (
            ["commission"]
            if commission_mode == LEGACY_ZERO_COMMISSION_COMPARATOR_MODE
            else []
        ),
        "max_total_cost_r": max_total_cost_r,
        "cost_limit_tolerance_r": limit_tolerance_r,
        "broker_hours": {
            "trade_mode": int(trade_mode) if trade_mode is not None else None,
            "source_status": "captured" if trade_mode is not None else "source_gap",
            "trade_mode_allows_deal": trade_mode == 4.0 if trade_mode is not None else None,
        },
        "explicit_session_table": explicit_session_table,
        "config_requirements": {
            "packet_required": _as_bool(
                runtime_cfg.get("selected_cell_pretrade_cost_model_required"),
                True,
            ),
            "profile_namespace_required": _as_bool(
                runtime_cfg.get("selected_cell_profile_namespace_required"),
                False,
            ),
            "symbol_spec_required": _as_bool(
                runtime_cfg.get("selected_cell_symbol_spec_required"),
                False,
            ),
            "swap_model_required": _as_bool(
                runtime_cfg.get("selected_cell_swap_model_required"),
                False,
            ),
            "swap_cost_model_required": _as_bool(
                runtime_cfg.get("selected_cell_swap_cost_model_required"),
                False,
            ),
            "slippage_model_required": _as_bool(
                runtime_cfg.get("selected_cell_slippage_model_required"),
                False,
            ),
            "broker_hours_required": _as_bool(
                runtime_cfg.get("selected_cell_broker_hours_required"),
                False,
            ),
            "explicit_session_table_required": _as_bool(
                runtime_cfg.get("selected_cell_explicit_session_table_required"),
                False,
            ),
        },
        "forbidden_surface_status": {
            "broker_operation": False,
            "order_calls": 0,
            "account_history_calls": 0,
            "paid_api_or_vendor_call": False,
            "credential_access": False,
            "remote_push": False,
        },
        "runtime_effect_boundary": "pretrade_local_packet_and_gate_no_broker_mutation",
    }
    reasons = pretrade_cost_refusal_reasons(packet)
    packet["refusal_reasons"] = reasons
    if required:
        packet["status"] = "REFUSED" if reasons else "PASSED"
    return packet


def pretrade_cost_refusal_reasons(packet: dict[str, Any]) -> list[str]:
    if packet.get("status") == "NOT_APPLICABLE":
        return []
    requirements = _mapping(packet.get("config_requirements"))
    reasons: list[str] = []
    tick_cost = _mapping(packet.get("tick_cost"))
    if requirements.get("packet_required", True):
        if tick_cost.get("spread_r") is None:
            reasons.append("missing_current_quote_spread_or_sl_distance")
        else:
            max_spread = _as_float(packet.get("max_spread_r"))
            spread_r = _as_float(tick_cost.get("spread_r"))
            tolerance = _as_float(packet.get("cost_limit_tolerance_r")) or 0.0
            if packet.get("max_spread_bound_unset"):
                reasons.append("max_spread_bound_unset")
            elif (
                max_spread is not None
                and spread_r is not None
                and spread_r - max_spread > tolerance
            ):
                reasons.append(
                    f"spread_r_exceeds_selected_cell_limit:{spread_r:.6f}>{max_spread:.6f}"
                )
    if packet.get("commission_model_required"):
        status = str(packet.get("commission_model_status") or "")
        allowed = set(packet.get("allowed_commission_model_statuses") or [])
        if status not in allowed:
            reasons.append(
                "missing_or_unapproved_selected_cell_commission_model_status:"
                f"{status or 'blank'}"
            )
    if packet.get("commission_cost_model_required"):
        commission_cost = _mapping(packet.get("commission_cost"))
        if (
            commission_cost.get("source_status") != "captured"
            or _as_float(commission_cost.get("cost_r")) is None
        ):
            detail = ",".join(
                str(value) for value in (commission_cost.get("missing_fields") or [])
            )
            reasons.append(
                "missing_broker_true_commission_cost_r_conversion"
                + (f":{detail}" if detail else "")
            )
    if requirements.get("profile_namespace_required") and not _mapping(packet.get("profile")).get(
        "broker_account_namespace"
    ):
        reasons.append("missing_broker_account_profile_namespace")
    if requirements.get("symbol_spec_required"):
        spec = _mapping(packet.get("symbol_spec"))
        missing = spec.get("required_missing_fields") or []
        if missing:
            reasons.append("missing_broker_symbol_spec_fields:" + ",".join(sorted(missing)))
    if requirements.get("swap_model_required"):
        swap = _mapping(packet.get("swap"))
        if swap.get("source_status") != "captured":
            reasons.append("missing_side_aware_swap_schedule")
    if requirements.get("swap_cost_model_required"):
        swap_cost = _mapping(packet.get("swap_cost"))
        if swap_cost.get("source_status") != "captured":
            missing = ",".join(str(v) for v in (swap_cost.get("missing_fields") or []))
            unsupported = ",".join(str(v) for v in (swap_cost.get("unsupported_fields") or []))
            detail = ",".join(v for v in (missing, unsupported) if v)
            reasons.append(
                "missing_side_aware_swap_cost_r_conversion"
                + (f":{detail}" if detail else "")
            )
    if requirements.get("slippage_model_required") and packet.get("expected_slippage_r") is None:
        reasons.append("missing_expected_slippage_r")
    if requirements.get("broker_hours_required"):
        hours = _mapping(packet.get("broker_hours"))
        if hours.get("source_status") != "captured":
            reasons.append("missing_broker_trade_mode_or_hours_state")
        elif hours.get("trade_mode_allows_deal") is not True:
            reasons.append(f"broker_trade_mode_not_deal_enabled:{hours.get('trade_mode')}")
    if requirements.get("explicit_session_table_required"):
        session_table = _mapping(packet.get("explicit_session_table"))
        if session_table.get("source_status") != "captured":
            reasons.append("missing_explicit_broker_trading_session_table")
    max_total = _as_float(packet.get("max_total_cost_r"))
    total = _as_float(packet.get("total_cost_r"))
    tolerance = _as_float(packet.get("cost_limit_tolerance_r")) or 0.0
    if max_total is not None and total is not None and total - max_total > tolerance:
        reasons.append(f"total_cost_r_exceeds_limit:{total:.6f}>{max_total:.6f}")
    return reasons


def pretrade_cost_refusal_reason(packet: dict[str, Any]) -> str | None:
    reasons = packet.get("refusal_reasons")
    if isinstance(reasons, list) and reasons:
        return ";".join(str(reason) for reason in reasons)
    if packet.get("status") == "REFUSED":
        reason = packet.get("refusal_reason")
        return str(reason) if reason else "pretrade_cost_packet_refused"
    return None
