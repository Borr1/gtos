"""Build source-bound weekend vNext counterfactual price-action ledgers.

This is an evidence builder only. It reads weekend live trade records and M1
captures, then writes route-owned forensic artifacts that classify:

- BTCUSD/ETHUSD candidates,
- prop-reset deferrals,
- placed vNext orders and lifecycle rows.

The path simulation is deliberately conservative. It uses M1 OHLC ordering
only, records same-bar ambiguity, and labels results as proxy evidence rather
than broker-realized truth.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_live_activation_active_repair_companion_2026_05_28"
)

OUT_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_COUNTERFACTUAL_PRICE_ACTION_LEDGER.jsonl"
OUT_SUMMARY = ROUTE_DIR / "LIVE_WEEKEND_COUNTERFACTUAL_PRICE_ACTION_SUMMARY.json"

WEEKEND_START = datetime(2026, 5, 28, tzinfo=timezone.utc)
WEEKEND_END = datetime(2026, 5, 31, tzinfo=timezone.utc)
DEFAULT_PENDING_HORIZON = timedelta(hours=48)


@dataclass(frozen=True)
class Bar:
    time_utc: datetime
    open: float
    high: float
    low: float
    close: float


def _parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _get(obj: Any, *keys: str, default: Any = None) -> Any:
    cur = obj
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def _first(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iter_trade_record_paths() -> list[Path]:
    base = ROOT / "knowledge_base" / "trade_records"
    paths: list[Path] = []
    for path in base.glob("*/*.json"):
        name = path.name
        if "2026-05-28" in name or "2026-05-29" in name or "2026-05-30" in name:
            paths.append(path)
    return sorted(paths)


def _load_m1(symbol: str) -> list[Bar]:
    bars: list[Bar] = []
    for day in ("2026-05-28", "2026-05-29", "2026-05-30"):
        path = ROOT / "data" / "m1" / symbol / f"{day}.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                t = _parse_time(row.get("time_utc"))
                o = _float(row.get("open"))
                h = _float(row.get("high"))
                l = _float(row.get("low"))
                c = _float(row.get("close"))
                if t is None or o is None or h is None or l is None or c is None:
                    continue
                bars.append(Bar(t, o, h, l, c))
    bars.sort(key=lambda b: b.time_utc)
    return bars


def _m1_coverage(bars: list[Bar]) -> dict[str, Any]:
    if not bars:
        return {"available": False, "rows": 0, "first_utc": None, "last_utc": None}
    return {
        "available": True,
        "rows": len(bars),
        "first_utc": bars[0].time_utc.isoformat(),
        "last_utc": bars[-1].time_utc.isoformat(),
    }


def _entry_touched(bar: Bar, side: str, entry: float) -> bool:
    if side.upper() == "LONG":
        return bar.low <= entry <= bar.high or bar.low <= entry
    if side.upper() == "SHORT":
        return bar.low <= entry <= bar.high or bar.high >= entry
    return False


def _level_hit(bar: Bar, side: str, level: float, event: str) -> bool:
    side = side.upper()
    if event in {"sl", "be"}:
        return bar.low <= level if side == "LONG" else bar.high >= level
    if event in {"trigger", "target", "raw_tp"}:
        return bar.high >= level if side == "LONG" else bar.low <= level
    return False


def _r_at_price(side: str, entry: float, stop: float, price: float) -> float | None:
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    if side.upper() == "LONG":
        return (price - entry) / risk
    if side.upper() == "SHORT":
        return (entry - price) / risk
    return None


def _simulate_path(
    *,
    bars: list[Bar],
    symbol: str,
    side: str | None,
    candle_time: datetime | None,
    entry: float | None,
    stop: float | None,
    raw_tp: float | None,
    trigger_price: float | None,
    final_target_price: float | None,
) -> dict[str, Any]:
    if candle_time is None or side not in {"LONG", "SHORT"} or entry is None or stop is None:
        return {
            "path_status": "not_simulated_missing_required_geometry",
            "m1_coverage": _m1_coverage(bars),
        }
    if not bars:
        return {"path_status": "not_simulated_no_m1_data", "m1_coverage": _m1_coverage(bars)}
    coverage = _m1_coverage(bars)
    m1_starts_after_candidate_seconds = max(
        0.0,
        (bars[0].time_utc - candle_time).total_seconds(),
    )
    path_evidence_completeness = (
        "complete_from_candidate_time"
        if m1_starts_after_candidate_seconds == 0.0
        else "m1_capture_starts_after_candidate_time"
    )

    horizon_end = candle_time + DEFAULT_PENDING_HORIZON
    path = [b for b in bars if candle_time <= b.time_utc <= horizon_end]
    if not path:
        return {
            "path_status": "not_simulated_no_m1_rows_after_candidate",
            "m1_coverage": coverage,
            "candidate_time_utc": candle_time.isoformat(),
            "path_evidence_completeness": path_evidence_completeness,
            "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
        }

    risk = abs(entry - stop)
    if risk <= 0:
        return {
            "path_status": "not_simulated_non_positive_risk_distance",
            "m1_coverage": coverage,
            "candidate_time_utc": candle_time.isoformat(),
            "path_evidence_completeness": path_evidence_completeness,
            "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
        }
    if trigger_price is None:
        trigger_price = entry + risk if side == "LONG" else entry - risk
    if final_target_price is None:
        final_target_price = entry + 3 * risk if side == "LONG" else entry - 3 * risk

    entry_idx = None
    entry_bar = None
    for idx, bar in enumerate(path):
        if _entry_touched(bar, side, entry):
            entry_idx = idx
            entry_bar = bar
            break
    if entry_idx is None or entry_bar is None:
        last = path[-1]
        favorable = max((_r_at_price(side, entry, stop, b.low if side == "SHORT" else b.high) for b in path), default=None)
        adverse = min((_r_at_price(side, entry, stop, b.high if side == "SHORT" else b.low) for b in path), default=None)
        return {
            "path_status": "no_entry_touch_before_last_available_m1",
            "candidate_time_utc": candle_time.isoformat(),
            "horizon_end_utc": horizon_end.isoformat(),
            "last_m1_utc": last.time_utc.isoformat(),
            "last_close": last.close,
            "max_favorable_r_before_entry": favorable,
            "max_adverse_r_before_entry": adverse,
            "m1_coverage": coverage,
            "path_evidence_completeness": path_evidence_completeness,
            "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
        }

    after = path[entry_idx:]
    first_stage = None
    first_stage_bar = None
    same_bar_ambiguous = False
    for bar in after:
        sl_hit = _level_hit(bar, side, stop, "sl")
        trigger_hit = _level_hit(bar, side, trigger_price, "trigger")
        if sl_hit and trigger_hit:
            first_stage = "same_bar_sl_and_1r_trigger_ambiguous"
            first_stage_bar = bar
            same_bar_ambiguous = True
            break
        if sl_hit:
            first_stage = "sl_before_1r_trigger"
            first_stage_bar = bar
            break
        if trigger_hit:
            first_stage = "one_r_trigger_first"
            first_stage_bar = bar
            break

    if first_stage_bar is None:
        last = path[-1]
        return {
            "path_status": "entry_filled_no_sl_or_1r_before_last_available_m1",
            "candidate_time_utc": candle_time.isoformat(),
            "entry_touch_utc": entry_bar.time_utc.isoformat(),
            "last_m1_utc": last.time_utc.isoformat(),
            "last_close": last.close,
            "unrealized_r_at_last_close": _r_at_price(side, entry, stop, last.close),
            "m1_coverage": coverage,
            "path_evidence_completeness": path_evidence_completeness,
            "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
        }

    if first_stage == "sl_before_1r_trigger":
        return {
            "path_status": "entry_filled_sl_before_1r_trigger",
            "proxy_gross_r": -1.0,
            "candidate_time_utc": candle_time.isoformat(),
            "entry_touch_utc": entry_bar.time_utc.isoformat(),
            "first_terminal_utc": first_stage_bar.time_utc.isoformat(),
            "m1_same_bar_ambiguity": False,
            "m1_coverage": coverage,
            "path_evidence_completeness": path_evidence_completeness,
            "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
        }
    if first_stage == "same_bar_sl_and_1r_trigger_ambiguous":
        return {
            "path_status": first_stage,
            "proxy_gross_r": None,
            "candidate_time_utc": candle_time.isoformat(),
            "entry_touch_utc": entry_bar.time_utc.isoformat(),
            "first_ambiguous_utc": first_stage_bar.time_utc.isoformat(),
            "m1_same_bar_ambiguity": True,
            "m1_coverage": coverage,
            "path_evidence_completeness": path_evidence_completeness,
            "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
        }

    second_stage = None
    second_stage_bar = None
    trigger_index = after.index(first_stage_bar)
    for bar in after[trigger_index:]:
        be_hit = _level_hit(bar, side, entry, "be")
        final_hit = _level_hit(bar, side, final_target_price, "target")
        if be_hit and final_hit:
            second_stage = "same_bar_be_and_3r_final_ambiguous_after_1r"
            second_stage_bar = bar
            same_bar_ambiguous = True
            break
        if final_hit:
            second_stage = "partial_1r_then_3r_final"
            second_stage_bar = bar
            break
        if be_hit:
            second_stage = "partial_1r_then_be"
            second_stage_bar = bar
            break

    if second_stage_bar is None:
        last = path[-1]
        residual_r = _r_at_price(side, entry, stop, last.close)
        proxy = None if residual_r is None else 0.5 + 0.5 * residual_r
        return {
            "path_status": "partial_1r_then_open_at_last_available_m1",
            "proxy_gross_r": proxy,
            "candidate_time_utc": candle_time.isoformat(),
            "entry_touch_utc": entry_bar.time_utc.isoformat(),
            "one_r_trigger_utc": first_stage_bar.time_utc.isoformat(),
            "last_m1_utc": last.time_utc.isoformat(),
            "last_close": last.close,
            "residual_unrealized_r_at_last_close": residual_r,
            "m1_same_bar_ambiguity": same_bar_ambiguous,
            "m1_coverage": coverage,
            "path_evidence_completeness": path_evidence_completeness,
            "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
        }

    proxy_by_stage = {
        "partial_1r_then_3r_final": 2.0,
        "partial_1r_then_be": 0.5,
    }
    return {
        "path_status": second_stage,
        "proxy_gross_r": proxy_by_stage.get(second_stage),
        "candidate_time_utc": candle_time.isoformat(),
        "entry_touch_utc": entry_bar.time_utc.isoformat(),
        "one_r_trigger_utc": first_stage_bar.time_utc.isoformat(),
        "second_terminal_utc": second_stage_bar.time_utc.isoformat(),
        "m1_same_bar_ambiguity": same_bar_ambiguous or second_stage.startswith("same_bar"),
        "m1_coverage": coverage,
        "path_evidence_completeness": path_evidence_completeness,
        "m1_starts_after_candidate_seconds": m1_starts_after_candidate_seconds,
    }


def _extract_candidate(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    pipeline = record.get("decision_pipeline") or {}
    meta = record.get("metadata") or {}
    candidate = record.get("moonshot_broader_origin_candidate") or {}
    trade_params = record.get("trade_parameters") or {}
    dyn = pipeline.get("gtos_vnext_moonshot_dynamic_execution") or {}
    router = dyn.get("router_record") or {}
    route_dims = router.get("route_dimensions") or {}
    source_event = dyn.get("source_event") or {}
    packet = pipeline.get("gtos_vnext_candidate_intelligence_packet") or {}
    identity = packet.get("candidate_identity") or {}
    risk_proof = packet.get("selected_cell_risk_proof") or {}
    geometry = packet.get("geometry") or {}
    raw_geometry = geometry.get("raw") or {}
    dynamic_policy = packet.get("dynamic_policy") or {}
    trigger_final = dynamic_policy.get("dynamic_trigger_final_pullback") or {}
    prop = (
        packet.get("prop_governor", {}).get("before_geometry_repair")
        or pipeline.get("gtos_vnext_prop_safe_selector")
        or {}
    )

    symbol = _first(meta.get("symbol"), identity.get("symbol"), candidate.get("symbol"))
    side = str(_first(candidate.get("side"), trade_params.get("direction"), identity.get("side"), route_dims.get("side")) or "").upper()
    candle_time = _parse_time(_first(meta.get("candle_close_utc"), meta.get("candle_time"), source_event.get("candle_time_utc")))
    entry = _float(_first(raw_geometry.get("entry_price"), trade_params.get("entry_price"), candidate.get("entry_price")))
    stop = _float(_first(raw_geometry.get("stop_loss"), trade_params.get("stop_loss"), candidate.get("stop_loss")))
    raw_tp = _float(_first(raw_geometry.get("take_profit_1"), trade_params.get("take_profit_1"), candidate.get("take_profit_1")))
    trigger_price = _float(
        _first(
            trigger_final.get("dynamic_be_trigger_price"),
            trigger_final.get("be_trigger_price"),
            trigger_final.get("trigger_price"),
            packet.get("dynamic_be_trigger_price"),
        )
    )
    final_target_price = _float(
        _first(
            trigger_final.get("dynamic_final_target_price"),
            trigger_final.get("final_target_price"),
            packet.get("dynamic_final_target_price"),
        )
    )
    if trigger_price is None and entry is not None and stop is not None:
        risk = abs(entry - stop)
        trigger_price = entry + risk if side == "LONG" else entry - risk
    if final_target_price is None and entry is not None and stop is not None:
        risk = abs(entry - stop)
        final_target_price = entry + 3 * risk if side == "LONG" else entry - 3 * risk

    refusal_reasons = _first(
        dyn.get("refusal_reasons"),
        pipeline.get("gtos_vnext_moonshot_dynamic_refusal_reasons"),
        packet.get("refusal_and_repair_reasons", {}).get("recorded_dynamic_refusal_reasons"),
        [],
    )
    if not isinstance(refusal_reasons, list):
        refusal_reasons = [str(refusal_reasons)]

    return {
        "source_path": str(path),
        "trade_id": meta.get("trade_id"),
        "symbol": symbol,
        "broker_symbol": _first(identity.get("broker_symbol"), source_event.get("broker_symbol"), symbol),
        "candidate_id": _first(candidate.get("candidate_id"), identity.get("candidate_id"), source_event.get("candidate_id"), _get(pipeline, "gtos_vnext_runtime", "evidence", "broader_origin_candidate_id")),
        "candle_time_utc": candle_time.isoformat() if candle_time else None,
        "session": _first(meta.get("kill_zone"), identity.get("session"), source_event.get("route_session"), route_dims.get("route_session")),
        "route_session": _first(identity.get("route_session"), source_event.get("route_session"), route_dims.get("route_session"), meta.get("kill_zone")),
        "utc_hour_bucket": _first(identity.get("utc_hour_bucket"), source_event.get("utc_hour_bucket"), route_dims.get("utc_hour_bucket")),
        "side": side or None,
        "framework": _first(candidate.get("framework"), identity.get("framework"), source_event.get("framework"), route_dims.get("framework")),
        "origin_family": _first(candidate.get("origin_family"), identity.get("origin_family"), route_dims.get("origin_family")),
        "candidate_origin_family": _first(candidate.get("candidate_origin_family"), identity.get("candidate_origin_family"), source_event.get("candidate_origin_family"), route_dims.get("candidate_origin_family")),
        "final_outcome": pipeline.get("final_outcome"),
        "entry_price": entry,
        "stop_loss": stop,
        "raw_take_profit_1_1_5r": raw_tp,
        "dynamic_trigger_price_1r_proxy": trigger_price,
        "dynamic_final_target_price_3r_proxy": final_target_price,
        "selected_policy": _first(dynamic_policy.get("selected_policy"), dyn.get("selected_policy"), route_dims.get("raw_asof_selected_policy")),
        "execution_policy_id": _first(dynamic_policy.get("execution_policy_id"), dyn.get("execution_policy_id"), route_dims.get("selected_cell_risk_execution_policy_id")),
        "dynamic_refusal_reasons": refusal_reasons,
        "broader_origin_allowed": _first(source_event.get("broader_origin_allowed"), route_dims.get("broader_origin_allowed")),
        "broader_origin_match_reason": _first(source_event.get("broader_origin_match_reason"), route_dims.get("broader_origin_match_reason")),
        "broader_origin_allowlist_rows": _first(source_event.get("broader_origin_allowlist_rows"), route_dims.get("broader_origin_allowlist_rows")),
        "selected_cell_risk_allowed": _first(risk_proof.get("allowed"), source_event.get("selected_cell_risk_allowed"), route_dims.get("selected_cell_risk_allowed")),
        "selected_cell_risk_pct": _first(risk_proof.get("risk_pct"), source_event.get("selected_cell_risk_pct"), route_dims.get("selected_cell_risk_pct")),
        "selected_cell_risk_cell_id": _first(risk_proof.get("cell_id"), source_event.get("selected_cell_risk_cell_id"), route_dims.get("selected_cell_risk_cell_id")),
        "selected_cell_risk_match_reason": _first(risk_proof.get("match_reason"), source_event.get("selected_cell_risk_match_reason"), route_dims.get("selected_cell_risk_match_reason")),
        "selected_cell_risk_unresolved_reasons": _first(source_event.get("selected_cell_risk_unresolved_reasons"), []),
        "source_mode": _first(source_event.get("source_mode"), route_dims.get("source_mode")),
        "source_path_feature_status": _first(source_event.get("source_path_feature_status"), route_dims.get("source_path_feature_status"), "raw_data_m15_asof_complete" if record.get("mso") else None),
        "source_window_complete": _first(source_event.get("source_window_complete"), route_dims.get("source_window_complete")),
        "gate1_passed": _get(pipeline, "gate1_result", "passed"),
        "gate1_reason": _first(_get(pipeline, "gate1_result", "details", "reason"), _get(pipeline, "gate1_result", "details", "denial_details", "reason"), _get(pipeline, "permission_reason")),
        "gate3_passed": _get(pipeline, "gate3_result", "passed"),
        "gate3_reason": _get(pipeline, "gate3_result", "details", "reason"),
        "gate3_spread_cents": _get(pipeline, "gate3_result", "details", "spread_cents"),
        "prop_action": _first(prop.get("action"), prop.get("would_action"), _get(pipeline, "gtos_vnext_prop_safe_selector", "action")),
        "prop_reason": _first(prop.get("reason"), _get(pipeline, "gtos_vnext_prop_safe_selector", "reason")),
        "prop_before_risk_pct": _first(prop.get("before_risk_pct"), _get(pipeline, "gtos_vnext_prop_safe_selector", "before_risk_pct")),
        "prop_after_risk_pct": _first(prop.get("after_risk_pct"), _get(pipeline, "gtos_vnext_prop_safe_selector", "after_risk_pct")),
        "prop_max_allowed_new_trade_risk_pct": _first(prop.get("max_allowed_new_trade_risk_pct"), _get(pipeline, "gtos_vnext_prop_safe_selector", "max_allowed_new_trade_risk_pct")),
    }


def _classify_block(row: dict[str, Any]) -> dict[str, Any]:
    outcome = row.get("final_outcome")
    reasons = set(row.get("dynamic_refusal_reasons") or [])
    classification: list[str] = []
    valid = "unresolved"

    if outcome == "DEFERRED_GTOS_VNEXT_PROP_RESET":
        classification.append("stale_pre_dynamic_prop_budget_deferral_not_vnext_proven")
        if row.get("selected_cell_risk_pct") in (None, ""):
            classification.append("selected_cell_risk_missing_before_prop_terminal_action")
        if row.get("prop_before_risk_pct") in (1, 1.0, 2, 2.0):
            classification.append("used_static_config_risk_before_selected_cell_lot_proof")
        valid = "not_valid_as_vnext_terminal_block_without_post_selector_budget_recheck"
    elif outcome == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC":
        if "framework_not_activated_in_stage13_full_moonshot_selector" in reasons:
            classification.append("selector_bridge_or_allowlist_mismatch")
        if "selected_cell_risk_not_verified_or_zero" in reasons:
            classification.append("selected_cell_risk_zero_or_unresolved")
        if row.get("selected_cell_risk_unresolved_reasons"):
            classification.append("risk_cell_unresolved_fields:" + ",".join(map(str, row["selected_cell_risk_unresolved_reasons"])))
        valid = "not_valid_as_market_rejection; vnext_contract_repair_or_exact_exclusion_required"
    elif outcome == "REJECTED_GATE1_SAFETY":
        classification.append("pre_repair_gate1_terminal_geometry_reject")
        valid = "not_valid_as_vnext_terminal_reject_without_executable_geometry_repair"
    elif outcome == "REJECTED_GATE3_CIRCUIT_BREAKER":
        classification.append("spread_gate_reject")
        valid = "valid_if_spread_units_and_market_session_verified"
    elif outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN":
        classification.append("broker_order_path_reached")
        valid = "placed_order_actual_lifecycle_required"

    if not classification:
        classification.append("unclassified")
    return {
        "block_classification": classification,
        "vnext_validity": valid,
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _mt5_readonly_snapshot(target_tickets: set[int]) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": False, "error": f"import_failed:{exc!r}"}
    if not mt5.initialize():  # pragma: no cover - environment dependent
        return {"available": False, "error": f"initialize_failed:{mt5.last_error()!r}"}
    try:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=5)
        account = mt5.account_info()
        positions = [p._asdict() for p in (mt5.positions_get() or [])]
        orders = [o._asdict() for o in (mt5.orders_get() or [])]
        deals: list[dict[str, Any]] = []
        for deal in mt5.history_deals_get(start, now) or []:
            row = deal._asdict()
            if (
                row.get("position_id") in target_tickets
                or row.get("order") in target_tickets
                or row.get("ticket") in target_tickets
            ):
                if row.get("time"):
                    row["time_utc"] = datetime.fromtimestamp(row["time"], tz=timezone.utc).isoformat()
                if row.get("time_msc"):
                    row["time_msc_utc"] = datetime.fromtimestamp(row["time_msc"] / 1000, tz=timezone.utc).isoformat()
                deals.append(row)
        return {
            "available": True,
            "checked_at_utc": now.isoformat(),
            "account": account._asdict() if account else None,
            "positions": positions,
            "orders": orders,
            "target_deals": deals,
        }
    finally:
        mt5.shutdown()


def _placed_order_rows(
    m1_cache: dict[str, list[Bar]],
    mt5_snapshot: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    lifecycle_rows = [
        row
        for row in _load_jsonl(ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl")
        if row.get("gtos_vnext_dynamic_policy_selected") or row.get("gtos_vnext_execution_policy_id")
    ]
    slippage_rows = _load_jsonl(ROOT / "shadow_logs" / "slippage.jsonl")
    slips_by_ticket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in slippage_rows:
        ticket = row.get("ticket") or row.get("order_ticket")
        if ticket is not None:
            slips_by_ticket[str(ticket)].append(row)

    mt5_deals_by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    mt5_positions_by_ticket: dict[str, dict[str, Any]] = {}
    if mt5_snapshot and mt5_snapshot.get("available"):
        for deal in mt5_snapshot.get("target_deals") or []:
            mt5_deals_by_position[str(deal.get("position_id"))].append(deal)
        for pos in mt5_snapshot.get("positions") or []:
            mt5_positions_by_ticket[str(pos.get("ticket"))] = pos

    out: list[dict[str, Any]] = []
    for row in lifecycle_rows:
        symbol = row.get("symbol")
        ticket = row.get("mt5_position_ticket") or row.get("trade_state_ticket") or row.get("mt5_entry_order_ticket")
        if not symbol or ticket is None:
            continue
        side = str(row.get("side") or "").upper()
        fill_time = _parse_time(row.get("fill_time_utc") or row.get("timestamp_utc"))
        entry = _float(row.get("executed_entry_price") or row.get("entry_price"))
        stop = _float(row.get("stop_loss"))
        final_target = _float(row.get("gtos_vnext_dynamic_final_target_price"))
        trigger = _float(row.get("gtos_vnext_dynamic_be_trigger_price"))
        bars = m1_cache.setdefault(symbol, _load_m1(symbol))
        actual_slips = slips_by_ticket.get(str(ticket), [])
        close_rows = [s for s in actual_slips if s.get("broker_profit") is not None or s.get("remaining_volume") == 0.0]
        partial_rows = [s for s in actual_slips if s.get("remaining_volume") not in (None, 0, 0.0)]
        entry_slip = next((s for s in actual_slips if s.get("slippage_event_type") == "entry"), None)
        if entry_slip:
            entry = _float(entry_slip.get("executed_entry_price") or entry_slip.get("fill_price") or entry)
            stop = _float(entry_slip.get("executed_stop_price") or stop)
            timeline = entry_slip.get("dynamic_exit_action_timeline") or {}
            trigger = _float(timeline.get("be_trigger_price") or trigger)
            final_target = _float(timeline.get("final_target_price") or final_target)
        mt5_deals = mt5_deals_by_position.get(str(ticket), [])
        mt5_entry_deals = [d for d in mt5_deals if d.get("entry") == 0]
        mt5_close_deals = [d for d in mt5_deals if d.get("entry") == 1]
        mt5_manual_close_deals = [
            d
            for d in mt5_close_deals
            if d.get("magic") not in (None, 0, 20260401) or d.get("reason") == 1 or d.get("magic") == 0
        ]
        mt5_open_position = mt5_positions_by_ticket.get(str(ticket))
        mt5_realized = sum(float(d.get("profit") or 0.0) for d in mt5_close_deals)
        mt5_commission = sum(float(d.get("commission") or 0.0) for d in mt5_deals)
        mt5_swap = sum(float(d.get("swap") or 0.0) for d in mt5_deals)
        if mt5_open_position and mt5_close_deals:
            broker_truth_status = "partial_closed_with_open_residual_reconciled_from_mt5"
        elif mt5_open_position:
            broker_truth_status = "open_position_reconciled_from_mt5"
        elif mt5_manual_close_deals:
            broker_truth_status = "closed_with_manual_intervention_reconciled_from_mt5"
        elif mt5_close_deals:
            broker_truth_status = "closed_reconciled_from_mt5"
        elif mt5_snapshot and mt5_snapshot.get("available"):
            broker_truth_status = "entry_only_no_close_deal_found_in_mt5_window"
        else:
            broker_truth_status = "mt5_readonly_snapshot_not_included"
        sim = _simulate_path(
            bars=bars,
            symbol=symbol,
            side=side,
            candle_time=fill_time,
            entry=entry,
            stop=stop,
            raw_tp=None,
            trigger_price=trigger,
            final_target_price=final_target,
        )
        out.append(
            {
                "ledger_scope": "placed_order_lifecycle_counterfactual",
                "symbol": symbol,
                "broker_symbol": row.get("broker_symbol"),
                "candidate_id": row.get("candidate_id"),
                "trade_id": row.get("trade_id"),
                "ticket": ticket,
                "side": side,
                "fill_time_utc": fill_time.isoformat() if fill_time else None,
                "executed_entry_price": entry,
                "stop_loss": stop,
                "dynamic_trigger_price": trigger,
                "dynamic_final_target_price": final_target,
                "actual_slippage_row_count": len(actual_slips),
                "actual_close_row_count": len(close_rows),
                "actual_partial_row_count": len(partial_rows),
                "broker_realized_profit_sum": sum(float(s.get("broker_profit") or 0.0) for s in close_rows),
                "entry_commission_sum": sum(float(s.get("commission") or 0.0) for s in actual_slips if s.get("commission") is not None),
                "swap_sum": sum(float(s.get("swap") or 0.0) for s in actual_slips if s.get("swap") is not None),
                "actual_close_times": [s.get("close_time") for s in close_rows if s.get("close_time")],
                "partial_close_times": [s.get("close_time") for s in partial_rows if s.get("close_time")],
                "residual_remaining_volumes": [s.get("remaining_volume") for s in partial_rows],
                "mt5_readonly_broker_truth_status": broker_truth_status,
                "mt5_readonly_deal_count": len(mt5_deals),
                "mt5_readonly_entry_deal_count": len(mt5_entry_deals),
                "mt5_readonly_close_deal_count": len(mt5_close_deals),
                "mt5_readonly_manual_close_deal_count": len(mt5_manual_close_deals),
                "mt5_readonly_realized_profit_sum": mt5_realized,
                "mt5_readonly_commission_sum": mt5_commission,
                "mt5_readonly_swap_sum": mt5_swap,
                "mt5_readonly_open_position": mt5_open_position,
                "mt5_readonly_close_deals": [
                    {
                        "ticket": d.get("ticket"),
                        "order": d.get("order"),
                        "time_utc": d.get("time_utc"),
                        "type": d.get("type"),
                        "entry": d.get("entry"),
                        "magic": d.get("magic"),
                        "reason": d.get("reason"),
                        "volume": d.get("volume"),
                        "price": d.get("price"),
                        "commission": d.get("commission"),
                        "swap": d.get("swap"),
                        "profit": d.get("profit"),
                        "comment": d.get("comment"),
                    }
                    for d in mt5_close_deals
                ],
                "counterfactual_fixed_ticket_binding_path_proxy": sim,
                "counterfactual_note": (
                    "Proxy uses M1 OHLC and assumes the current ticket-bound partial/BE/TP management "
                    "would apply to this ticket. Broker-realized PnL remains actual-only."
                ),
            }
        )
    return out


def build(*, include_mt5_readonly: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    m1_cache: dict[str, list[Bar]] = {}
    ledger: list[dict[str, Any]] = []

    for path in _iter_trade_record_paths():
        record = _json(path)
        if not record:
            continue
        row = _extract_candidate(path, record)
        symbol = row.get("symbol")
        outcome = row.get("final_outcome")
        in_scope = (
            symbol in {"BTCUSD", "ETHUSD"}
            or outcome == "DEFERRED_GTOS_VNEXT_PROP_RESET"
            or outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
        )
        if not in_scope:
            continue
        bars = m1_cache.setdefault(str(symbol), _load_m1(str(symbol))) if symbol else []
        candle_time = _parse_time(row.get("candle_time_utc"))
        sim = _simulate_path(
            bars=bars,
            symbol=str(symbol),
            side=row.get("side"),
            candle_time=candle_time,
            entry=row.get("entry_price"),
            stop=row.get("stop_loss"),
            raw_tp=row.get("raw_take_profit_1_1_5r"),
            trigger_price=row.get("dynamic_trigger_price_1r_proxy"),
            final_target_price=row.get("dynamic_final_target_price_3r_proxy"),
        )
        scope = "prop_deferral_counterfactual" if outcome == "DEFERRED_GTOS_VNEXT_PROP_RESET" else "candidate_counterfactual"
        if symbol in {"BTCUSD", "ETHUSD"}:
            scope = "btcusd_ethusd_candidate_counterfactual"
        if outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN":
            scope = "placed_trade_record_price_proxy"
        ledger.append(
            {
                "ledger_scope": scope,
                **row,
                **_classify_block(row),
                "price_action_proxy": sim,
            }
        )

    target_tickets: set[int] = set()
    for row in _load_jsonl(ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl"):
        if row.get("gtos_vnext_dynamic_policy_selected") or row.get("gtos_vnext_execution_policy_id"):
            for key in ("mt5_position_ticket", "trade_state_ticket", "mt5_entry_order_ticket"):
                value = row.get(key)
                if isinstance(value, int):
                    target_tickets.add(value)
    mt5_snapshot = _mt5_readonly_snapshot(target_tickets) if include_mt5_readonly else None
    ledger.extend(_placed_order_rows(m1_cache, mt5_snapshot=mt5_snapshot))
    ledger.sort(
        key=lambda r: (
            str(r.get("ledger_scope")),
            str(r.get("symbol")),
            str(r.get("candle_time_utc") or r.get("fill_time_utc") or ""),
            str(r.get("candidate_id") or ""),
        )
    )

    summary: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": "vnext_weekend_counterfactual_price_action_v1",
        "evidence_window_start_utc": WEEKEND_START.isoformat(),
        "evidence_window_end_utc": WEEKEND_END.isoformat(),
        "ledger_rows": len(ledger),
        "scope_counts": dict(Counter(r.get("ledger_scope") for r in ledger)),
        "symbol_counts": dict(Counter(r.get("symbol") for r in ledger if r.get("symbol"))),
        "outcome_counts": dict(Counter(r.get("final_outcome") for r in ledger if r.get("final_outcome"))),
        "vnext_validity_counts": dict(Counter(r.get("vnext_validity") for r in ledger if r.get("vnext_validity"))),
        "path_status_counts": dict(
            Counter(
                _get(r, "price_action_proxy", "path_status")
                or _get(r, "counterfactual_fixed_ticket_binding_path_proxy", "path_status")
                for r in ledger
            )
        ),
        "path_evidence_completeness_counts": dict(
            Counter(
                _get(r, "price_action_proxy", "path_evidence_completeness")
                or _get(r, "counterfactual_fixed_ticket_binding_path_proxy", "path_evidence_completeness")
                or "not_applicable_or_missing"
                for r in ledger
            )
        ),
        "btc_eth": {
            "rows": sum(1 for r in ledger if r.get("symbol") in {"BTCUSD", "ETHUSD"} and r.get("ledger_scope") == "btcusd_ethusd_candidate_counterfactual"),
            "by_symbol": {
                sym: {
                    "rows": sum(1 for r in ledger if r.get("symbol") == sym and r.get("ledger_scope") == "btcusd_ethusd_candidate_counterfactual"),
                    "outcomes": dict(Counter(r.get("final_outcome") for r in ledger if r.get("symbol") == sym and r.get("ledger_scope") == "btcusd_ethusd_candidate_counterfactual")),
                    "path_statuses": dict(Counter(_get(r, "price_action_proxy", "path_status") for r in ledger if r.get("symbol") == sym and r.get("ledger_scope") == "btcusd_ethusd_candidate_counterfactual")),
                    "path_evidence_completeness": dict(Counter(_get(r, "price_action_proxy", "path_evidence_completeness") for r in ledger if r.get("symbol") == sym and r.get("ledger_scope") == "btcusd_ethusd_candidate_counterfactual")),
                }
                for sym in ("BTCUSD", "ETHUSD")
            },
        },
        "prop_deferrals": {
            "rows": sum(1 for r in ledger if r.get("ledger_scope") == "prop_deferral_counterfactual"),
            "by_symbol": dict(Counter(r.get("symbol") for r in ledger if r.get("ledger_scope") == "prop_deferral_counterfactual")),
            "path_statuses": dict(Counter(_get(r, "price_action_proxy", "path_status") for r in ledger if r.get("ledger_scope") == "prop_deferral_counterfactual")),
            "path_evidence_completeness": dict(Counter(_get(r, "price_action_proxy", "path_evidence_completeness") for r in ledger if r.get("ledger_scope") == "prop_deferral_counterfactual")),
            "proxy_gross_r_sum_known": sum(
                float(_get(r, "price_action_proxy", "proxy_gross_r") or 0.0)
                for r in ledger
                if r.get("ledger_scope") == "prop_deferral_counterfactual"
                and _get(r, "price_action_proxy", "proxy_gross_r") is not None
            ),
            "known_proxy_r_rows": sum(
                1
                for r in ledger
                if r.get("ledger_scope") == "prop_deferral_counterfactual"
                and _get(r, "price_action_proxy", "proxy_gross_r") is not None
            ),
        },
        "placed_lifecycle": {
            "rows": sum(1 for r in ledger if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"),
            "broker_realized_profit_sum_known_rows": sum(
                float(r.get("broker_realized_profit_sum") or 0.0)
                for r in ledger
                if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"
            ),
            "actual_close_rows_total": sum(
                int(r.get("actual_close_row_count") or 0)
                for r in ledger
                if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"
            ),
            "actual_partial_rows_total": sum(
                int(r.get("actual_partial_row_count") or 0)
                for r in ledger
                if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"
            ),
            "mt5_readonly_included": bool(mt5_snapshot and mt5_snapshot.get("available")),
            "mt5_readonly_status": (
                "included"
                if mt5_snapshot and mt5_snapshot.get("available")
                else (mt5_snapshot or {}).get("error", "not_requested")
            ),
            "mt5_readonly_broker_truth_status_counts": dict(
                Counter(
                    r.get("mt5_readonly_broker_truth_status")
                    for r in ledger
                    if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"
                )
            ),
            "mt5_readonly_realized_profit_sum": sum(
                float(r.get("mt5_readonly_realized_profit_sum") or 0.0)
                for r in ledger
                if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"
            ),
            "mt5_readonly_commission_sum": sum(
                float(r.get("mt5_readonly_commission_sum") or 0.0)
                for r in ledger
                if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"
            ),
            "mt5_readonly_swap_sum": sum(
                float(r.get("mt5_readonly_swap_sum") or 0.0)
                for r in ledger
                if r.get("ledger_scope") == "placed_order_lifecycle_counterfactual"
            ),
        },
        "limitations": [
            "Counterfactual path uses M1 OHLC only; same-minute hit ordering is marked ambiguous.",
            "Dynamic momentum pullback close cannot be reconstructed where live records do not carry pullback thresholds.",
            "Broker-realized PnL is used only from slippage/account-history rows, not inferred from price path.",
            "Weekend no-trade/no-management after Friday broker close limits path evidence to the last captured M1 rows.",
        ],
    }
    return ledger, summary


def write_outputs(ledger: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_LEDGER.open("w", encoding="utf-8", newline="\n") as fh:
        for row in ledger:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Build and verify outputs are internally consistent.")
    parser.add_argument(
        "--include-mt5-readonly",
        action="store_true",
        help="Include a read-only MT5 account/history snapshot for placed order reconciliation.",
    )
    args = parser.parse_args()
    ledger, summary = build(include_mt5_readonly=args.include_mt5_readonly)
    write_outputs(ledger, summary)
    if args.check:
        if summary["btc_eth"]["rows"] == 0:
            raise SystemExit("no BTCUSD/ETHUSD candidate rows found")
        if summary["prop_deferrals"]["rows"] != 45:
            raise SystemExit(f"expected 45 prop deferrals, found {summary['prop_deferrals']['rows']}")
        if summary["placed_lifecycle"]["rows"] != 8:
            raise SystemExit(f"expected 8 placed lifecycle rows, found {summary['placed_lifecycle']['rows']}")
    print(f"wrote {OUT_LEDGER}")
    print(f"wrote {OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
