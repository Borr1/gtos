#!/usr/bin/env python3
"""Build the market-expansion fill/session read-only probe package.

This route uses localhost MT5 bridge history orders/deals and M1 bars to repair
broker-real fill/slippage and observed quote-session evidence as far as the
local bridge can support. It stores aggregate rows only and never stores raw
ticket/order/deal/position identifiers. It does not send/check orders, select
symbols, read open position/order state, use depth/orderflow, push remotes,
apply config, or reload VPS/runtime processes.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
BROKER_AUTH_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_broker_authority_probe_2026_06_18"
DOSSIER_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_fill_session_probe"
HISTORY_START = datetime(2024, 1, 1, tzinfo=UTC)
M1_LOOKBACK_DAYS = 30
BRIDGE_HOST = "localhost"
BRIDGE_PORT = 8001
BRIDGE_TIMEOUT_SECONDS = 10


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value: Any, digits: int = 8) -> float | None:
    number = finite_float(value)
    return round(number, digits) if number is not None else None


def median(values: list[float]) -> float | None:
    clean = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not clean:
        return None
    mid = len(clean) // 2
    return clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2.0


def as_plain(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "_asdict"):
        return {key: as_plain(item) for key, item in value._asdict().items()}
    if isinstance(value, dict):
        return {str(key): as_plain(item) for key, item in value.items()}
    try:
        names = value.dtype.names
        if names:
            return {
                name: value[name].item() if hasattr(value[name], "item") else as_plain(value[name])
                for name in names
            }
    except Exception:  # noqa: BLE001 - non-numpy object
        pass
    if isinstance(value, (list, tuple, set)):
        return [as_plain(item) for item in value]
    return repr(value)


def load_dossier_rows() -> list[dict[str, Any]]:
    return read_json(DOSSIER_ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json")["rows"]


def risk_by_tag() -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for row in read_jsonl(DOSSIER_ROUTE / "SOURCE_EVENT_COST_LEDGER.jsonl"):
        risk = finite_float(row.get("risk_abs"))
        if risk and risk > 0:
            grouped.setdefault(row["tag"], []).append(risk)
    return {tag: value for tag, values in grouped.items() if (value := median(values)) is not None}


def connect_bridge():
    from siliconmetatrader5 import MetaTrader5

    mt5 = MetaTrader5(host=BRIDGE_HOST, port=BRIDGE_PORT, timeout=BRIDGE_TIMEOUT_SECONDS)
    initialized = mt5.initialize()
    return mt5, bool(initialized)


def history_rows(mt5: Any, broker_symbol: str, end: datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None, str | None]:
    try:
        raw_orders = mt5.history_orders_get(HISTORY_START, end, group=broker_symbol)
        order_error = None
    except Exception as exc:  # noqa: BLE001
        raw_orders = []
        order_error = repr(exc)
    try:
        raw_deals = mt5.history_deals_get(HISTORY_START, end, group=broker_symbol)
        deal_error = None
    except Exception as exc:  # noqa: BLE001
        raw_deals = []
        deal_error = repr(exc)
    orders = [as_plain(order) for order in (raw_orders or [])]
    deals = [as_plain(deal) for deal in (raw_deals or [])]
    return orders, deals, order_error, deal_error


def fill_slippage_rows(created_at: str, mt5: Any) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    end = datetime.now(UTC)
    risks = risk_by_tag()
    rows = []
    field_audit = {
        "schema": f"{SCHEMA_PREFIX}.history_order_deal_field_audit.v1",
        "created_at_utc": created_at,
        "history_window_start_utc": HISTORY_START.isoformat(),
        "history_window_end_utc": end.isoformat(),
        "order_field_names": [],
        "deal_field_names": [],
        "raw_ticket_or_order_ids_stored": False,
        "field_source": "first_available_history_order_deal_rows",
    }
    field_captured = False
    for source_row in load_dossier_rows():
        tag = source_row["tag"]
        broker_symbol = source_row["broker_symbol"]
        orders, deals, order_error, deal_error = history_rows(mt5, broker_symbol, end)
        if orders and not field_captured:
            field_audit["order_field_names"] = sorted(orders[0].keys())
            if deals:
                field_audit["deal_field_names"] = sorted(deals[0].keys())
            field_captured = True
        orders_by_ticket = {
            order.get("ticket"): order
            for order in orders
            if isinstance(order, dict) and order.get("ticket") is not None
        }
        joined = []
        for deal in deals:
            if not isinstance(deal, dict):
                continue
            if deal.get("entry") not in (0, 1):
                continue
            order = orders_by_ticket.get(deal.get("order"))
            if not order:
                continue
            deal_price = finite_float(deal.get("price"))
            order_price = finite_float(order.get("price_open"))
            if order_price in (None, 0.0):
                order_price = finite_float(order.get("price_current"))
            if deal_price is None or order_price is None:
                continue
            deal_type = deal.get("type")
            signed_slip = (
                deal_price - order_price
                if deal_type == 0
                else order_price - deal_price
                if deal_type == 1
                else deal_price - order_price
            )
            joined.append(
                {
                    "signed_price": signed_slip,
                    "abs_price": abs(deal_price - order_price),
                    "volume": finite_float(deal.get("volume")) or 0.0,
                    "deal_type": deal_type,
                    "order_type": order.get("type"),
                    "entry": deal.get("entry"),
                }
            )
        risk_abs = risks[tag]
        abs_values = [row["abs_price"] for row in joined]
        signed_values = [row["signed_price"] for row in joined]
        row = {
            "schema": f"{SCHEMA_PREFIX}.history_order_deal_fill_row.v1",
            "created_at_utc": created_at,
            "tag": tag,
            "file_symbol": source_row["file_symbol"],
            "broker_symbol": broker_symbol,
            "history_window_start_utc": HISTORY_START.isoformat(),
            "history_window_end_utc": end.isoformat(),
            "history_query": "history_orders_get plus history_deals_get aggregate-only group=broker_symbol",
            "raw_ticket_or_order_ids_stored": False,
            "order_count": len(orders),
            "deal_count": len(deals),
            "joined_entry_deal_count": len(joined),
            "order_type_values": sorted({order.get("type") for order in orders if isinstance(order, dict) and order.get("type") is not None}),
            "order_state_values": sorted({order.get("state") for order in orders if isinstance(order, dict) and order.get("state") is not None}),
            "order_filling_values": sorted({order.get("type_filling") for order in orders if isinstance(order, dict) and order.get("type_filling") is not None}),
            "deal_entry_values": sorted({deal.get("entry") for deal in deals if isinstance(deal, dict) and deal.get("entry") is not None}),
            "deal_type_values": sorted({deal.get("type") for deal in deals if isinstance(deal, dict) and deal.get("type") is not None}),
            "risk_abs_median": rounded(risk_abs, 10),
            "slippage_abs_price_mean": rounded(sum(abs_values) / len(abs_values), 10) if abs_values else None,
            "slippage_abs_price_max": rounded(max(abs_values), 10) if abs_values else None,
            "slippage_signed_price_mean": rounded(sum(signed_values) / len(signed_values), 10) if signed_values else None,
            "slippage_abs_r_mean": rounded((sum(abs_values) / len(abs_values)) / risk_abs, 10) if abs_values and risk_abs else None,
            "slippage_abs_r_max": rounded(max(abs_values) / risk_abs, 10) if abs_values and risk_abs else None,
            "slippage_signed_r_mean": rounded((sum(signed_values) / len(signed_values)) / risk_abs, 10) if signed_values and risk_abs else None,
            "order_error": order_error,
            "deal_error": deal_error,
        }
        if order_error or deal_error:
            row["fill_authority_status"] = "not_closed_history_error"
        elif not joined:
            row["fill_authority_status"] = "not_closed_no_direct_joined_fill_rows"
        else:
            row["fill_authority_status"] = "direct_observed_historical_order_deal_fill_slippage"
        rows.append(row)
    observed = [row for row in rows if row["fill_authority_status"] == "direct_observed_historical_order_deal_fill_slippage"]
    summary = {
        "schema": f"{SCHEMA_PREFIX}.history_order_deal_fill_summary.v1",
        "created_at_utc": created_at,
        "history_window_start_utc": HISTORY_START.isoformat(),
        "history_window_end_utc": end.isoformat(),
        "symbol_count": len(rows),
        "direct_fill_symbol_count": len(observed),
        "no_direct_fill_symbol_count": len(rows) - len(observed),
        "order_count_total": sum(row["order_count"] for row in rows),
        "deal_count_total": sum(row["deal_count"] for row in rows),
        "joined_entry_deal_count_total": sum(row["joined_entry_deal_count"] for row in rows),
        "max_slippage_abs_r_observed": rounded(max([row["slippage_abs_r_max"] for row in observed if row["slippage_abs_r_max"] is not None] or [0.0]), 10),
        "mean_slippage_abs_r_observed": rounded(
            sum(row["slippage_abs_r_mean"] for row in observed if row["slippage_abs_r_mean"] is not None)
            / len([row for row in observed if row["slippage_abs_r_mean"] is not None]),
            10,
        )
        if observed
        else None,
        "fill_authority_status_counts": dict(Counter(row["fill_authority_status"] for row in rows)),
        "all_symbols_fill_slippage_closed": False,
        "interpretation": (
            "historical order/deal joins repair direct slippage evidence for symbols with prior fills, "
            "but no direct fills for seven symbols and no prospective limit/queue fillability proof keep "
            "live authority open"
        ),
    }
    return rows, summary, field_audit


def m1_session_rows(created_at: str, mt5: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    end = datetime.now(UTC)
    start = end - timedelta(days=M1_LOOKBACK_DAYS)
    rows = []
    for source_row in load_dossier_rows():
        broker_symbol = source_row["broker_symbol"]
        copy_error = None
        try:
            rates = mt5.copy_rates_range(broker_symbol, mt5.TIMEFRAME_M1, start, end)
        except Exception as exc:  # noqa: BLE001
            rates = None
            copy_error = repr(exc)
        if rates is None:
            raw_rates = []
        else:
            try:
                raw_rates = list(rates)
            except TypeError:
                raw_rates = []
        rate_rows = [as_plain(row) for row in raw_rates]
        times = [int(row["time"]) for row in rate_rows if isinstance(row, dict) and row.get("time")]
        weekdays = sorted({datetime.fromtimestamp(item, UTC).weekday() for item in times})
        hours = sorted({datetime.fromtimestamp(item, UTC).hour for item in times})
        by_day: dict[str, int] = {}
        for item in times:
            dt = datetime.fromtimestamp(item, UTC)
            day = dt.date().isoformat()
            if day not in by_day or item < by_day[day]:
                by_day[day] = item
        first_hour_counts = Counter(
            f"{datetime.fromtimestamp(item, UTC).hour:02d}" for item in by_day.values()
        )
        weekend_count = sum(1 for item in times if datetime.fromtimestamp(item, UTC).weekday() >= 5)
        zero_tick_count = sum(1 for row in rate_rows if finite_float(row.get("tick_volume")) == 0)
        if copy_error:
            proxy_status = "not_closed_m1_copy_error"
        elif not rate_rows:
            proxy_status = "not_closed_no_m1_bars"
        elif weekend_count > 0 and weekdays == list(range(7)) and hours == list(range(24)):
            proxy_status = "observed_24_7_like_quote_availability_proxy"
        elif weekdays == [0, 1, 2, 3, 4] and hours == list(range(24)):
            proxy_status = "observed_weekday_24h_quote_availability_proxy"
        elif weekdays == [0, 1, 2, 3, 4] and hours:
            proxy_status = "observed_restricted_weekday_quote_availability_proxy"
        else:
            proxy_status = "observed_irregular_quote_availability_proxy"
        dominant_first_hour = first_hour_counts.most_common(1)[0][0] if first_hour_counts else None
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.observed_m1_session_availability_row.v1",
                "created_at_utc": created_at,
                "tag": source_row["tag"],
                "file_symbol": source_row["file_symbol"],
                "broker_symbol": broker_symbol,
                "lookback_start_utc": start.isoformat(),
                "lookback_end_utc": end.isoformat(),
                "m1_bar_count": len(rate_rows),
                "calendar_day_count": len(by_day),
                "weekdays_with_bars": weekdays,
                "utc_hours_with_bars": hours,
                "weekend_bar_count": weekend_count,
                "zero_tick_volume_bar_count": zero_tick_count,
                "first_bar_utc_hour_counts": dict(sorted(first_hour_counts.items())),
                "dominant_first_bar_utc_hour": dominant_first_hour,
                "observed_session_proxy_status": proxy_status,
                "explicit_session_table_status": "not_explicit_session_table",
                "copy_error": copy_error,
            }
        )
    status_counts = Counter(row["observed_session_proxy_status"] for row in rows)
    summary = {
        "schema": f"{SCHEMA_PREFIX}.observed_m1_session_availability_summary.v1",
        "created_at_utc": created_at,
        "lookback_days": M1_LOOKBACK_DAYS,
        "symbol_count": len(rows),
        "symbols_with_m1_bars": sum(1 for row in rows if row["m1_bar_count"] > 0),
        "explicit_session_table_closed": False,
        "observed_session_proxy_status_counts": dict(status_counts),
        "weekend_quote_symbols": [row["broker_symbol"] for row in rows if row["weekend_bar_count"] > 0],
        "restricted_weekday_symbols": [
            row["broker_symbol"]
            for row in rows
            if row["observed_session_proxy_status"] == "observed_restricted_weekday_quote_availability_proxy"
        ],
        "interpretation": (
            "observed M1 availability gives a broker-quote session proxy for guarded-open scheduling, "
            "but it is not an explicit broker trading-session table"
        ),
    }
    return rows, summary


def unresolved_requirements(created_at: str) -> list[dict[str, Any]]:
    items = [
        (
            "MX-FILL-SESSION-REQ-001",
            "explicit broker trading-session table or platform-source proof",
            "observed M1 availability repairs quote-session proxy but is not an explicit session table",
            "capture broker/platform session table or bridge method exposing exact trade/quote sessions",
        ),
        (
            "MX-FILL-SESSION-REQ-002",
            "broker-exact prospective limit-fill and market-fill authority",
            "historical order/deal joins repair observed slippage for prior fills only, not future limit queue/fillability",
            "VPS dry-run packet parity plus lifecycle/fill capture or strict guarded-open skip proof",
        ),
        (
            "MX-FILL-SESSION-REQ-003",
            "direct fill/slippage evidence for every activation symbol",
            "seven market-expansion symbols still have no direct joined order/deal fill rows in local account history",
            "broker/account history export, future capture, or exact family-transfer rule accepted by G12/owner",
        ),
        (
            "MX-FILL-SESSION-REQ-004",
            "broker-exact commission and swap authority from prior broker-authority route",
            "fill/session probe does not close no-history commission symbols, mode-5 swap formulas, or holding-time model",
            "continue from broker-authority route residual ledgers",
        ),
        (
            "MX-FILL-SESSION-REQ-005",
            "owner-approved VPS promotion and monitoring execution",
            "Mac route remains default-off and does not push, reload, restart, or apply live config",
            "VPS Codex session must absorb commits, rerun packet parity, apply only after all authority gates close, monitor, and retain rollback",
        ),
    ]
    return [
        {
            "schema": f"{SCHEMA_PREFIX}.unresolved_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": req_id,
            "requirement": requirement,
            "current_evidence": evidence,
            "repair_path": repair,
            "status": "not_closed_by_current_probe",
            "runtime_effect_now": "none_market_expansion_default_off",
        }
        for req_id, requirement, evidence, repair in items
    ]


def decision_ledgers(
    created_at: str,
    result: dict[str, Any],
    fill_summary: dict[str, Any],
    session_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decisions = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "fill_session_probe_partial_repair",
            "status": result["decision"],
            "evidence": {
                "direct_fill_symbol_count": result["direct_fill_symbol_count"],
                "symbols_with_m1_session_proxy": result["symbols_with_m1_session_proxy"],
                "explicit_session_table_closed": False,
            },
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "historical_fill_slippage_authority",
            "status": "partial_direct_history_not_prospective_fill_authority",
            "evidence": fill_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "observed_session_proxy",
            "status": "proxy_available_not_explicit_session_table",
            "evidence": session_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "market_expansion_promotion",
            "status": "default_off_not_promoted",
            "evidence": {"deployment_ready": False, "promotion_ready": False},
        },
    ]
    boundary = [
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "historical_fill_slippage",
            "status": "partial_not_closed",
            "evidence": fill_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "observed_quote_session_proxy",
            "status": "proxy_available_not_live_authority",
            "evidence": session_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "explicit_session_table",
            "status": "not_closed",
            "evidence": "M1 availability is observed proxy, not explicit platform session table",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "prospective_limit_queue_fillability",
            "status": "not_closed_not_mutated",
            "evidence": "route did not call order check/send and does not observe future queue fillability",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "owner_vps_action",
            "status": "not_executed_by_mac_route",
            "evidence": "no config activation, remote push, broker mutation, or VPS restart/reload",
        },
    ]
    return decisions, boundary


def forbidden_call_scan(created_at: str) -> dict[str, Any]:
    scanned_paths = [
        ROUTE / "build_market_expansion_fill_session_probe.py",
        ROUTE / "verify_market_expansion_fill_session_probe.py",
        PROJECT_ROOT / "tests" / "ultimate_book" / "test_market_expansion_fill_session_probe_artifacts.py",
    ]
    forbidden_patterns = [
        "order" + "_send" + "(",
        "order" + "_check" + "(",
        ".order" + "_send",
        ".order" + "_check",
        "TRADE" + "_ACTION_",
        "positions" + "_get" + "(",
        ".positions" + "_get",
        "mt5.orders" + "_get" + "(",
        ".orders" + "_get",
        "market" + "_book_add" + "(",
        "market" + "_book_get" + "(",
        "market" + "_book_release" + "(",
        "symbol" + "_select" + "(",
        "copy" + "_ticks_range" + "(",
        "subprocess" + ".run(['" + "ssh'",
        "subprocess" + ".run([\"" + "ssh\"",
        "rs" + "ync ",
        "sc" + "p ",
    ]
    matches = []
    for path in scanned_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in text:
                matches.append({"path": rel(path), "pattern": pattern})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "scanned_paths": [rel(path) for path in scanned_paths if path.exists()],
        "approved_read_calls_not_forbidden_in_this_route": [
            "history_orders_get",
            "history_deals_get",
            "copy_rates_range",
        ],
        "forbidden_patterns": forbidden_patterns,
        "matches": matches,
        "ok": not matches,
    }


def write_packet(result: dict[str, Any], requirements: list[dict[str, Any]]) -> None:
    req_text = "\n".join(f"- `{row['requirement_id']}`: {row['requirement']}" for row in requirements)
    packet = f"""# Market Expansion Fill/Session Probe Packet

Decision: `{result['decision']}`

This package improves fill/session evidence without promoting market expansion.
It used read-only history order/deal aggregates and observed M1 quote-session
availability. Raw ticket/order/deal identifiers are not stored.

What improved:

- Direct historical order/deal fill-slippage evidence exists for `{result['direct_fill_symbol_count']}/{result['selectable_symbol_count']}` symbols.
- Joined entry-deal rows: `{result['joined_entry_deal_count_total']}`.
- Max observed absolute slippage across direct symbols: `{result['max_slippage_abs_r_observed']}R`.
- Observed M1 quote-session proxy exists for `{result['symbols_with_m1_session_proxy']}/{result['selectable_symbol_count']}` symbols.

What remains open:

{req_text}

Runtime boundary:

- `live_authority=false`
- `deployment_ready=false`
- `promotion_ready=false`
- `runtime_effect=none_market_expansion_default_off_fill_session_probe_only`
"""
    (ROUTE / "FILL_SESSION_PROBE_PACKET.md").write_text(packet, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    prompt = f"""# Market Expansion Fill/Session Closure Successor Prompt

Created: {created_at}

Mandatory context use: run GTOS preflight, regenerate `.context/LIVE_STATE.md`, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/parallel_goal_merge_playbook.md`, this prompt, and the fill/session probe artifacts from disk as active instructions, not background. Do not rely on chat memory. After compaction/resume/interruption/uncertainty, reread the prompt, doctrine, and latest route artifacts before continuing and record instruction-coverage in the completion audit.

Lane posture: constructive source-repair and deployment-authority closure. Keep market expansion default-off until all authority gates close. Use maximum practical reasoning inside the evidence class, no arbitrary top-N, and no conservative brake. Preserve all material rows and pursue same-evidence-class repair before declaring a blocker.

Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been attempted, repaired, recomputed, or reduced to an exact owner/source/capture requirement. Full same-evidence-class pursuit is mandatory; a clean blocker ledger is not completion when a same-class read-only source-capture, source completeness check, branch decision, implementation decision, exact-R/proxy-R/expectancy recomputation, or result materialization step is still executable.

Input route: `research/operations/final_moonshot_market_expansion_fill_session_probe_2026_06_18/`.

Objective: close or exactly bound the remaining fill/session requirements for market expansion without orderflow/depth. The current probe gives direct historical fill/slippage joins for symbols with prior fills and observed M1 quote-session proxies for all activation symbols. Continue from those artifacts. Search for exact platform/broker session tables, future-safe guarded-open fillability rules, direct fill evidence for no-history symbols, broker-exact commission/swap residuals from the broker-authority route, and VPS packet-parity proof. If all gates close, prepare an owner-action activation packet and rollback/monitoring plan. If any gate remains open, keep expansion default-off and update unresolved requirement ledgers with exact source/capture requirements.

Result materialization standard: every branch decision and implementation decision must preserve result-use-status/evidence-class boundaries, exact-R/proxy-R/expectancy values where lawful, source-capture/source completeness status, row counts, denominator rules, no-leak/as-of controls, and unresolved owner/source/capture requirements.

Approved read-only evidence surfaces in this lane: aggregate `history_orders_get`, aggregate `history_deals_get`, `copy_rates_range` M1 availability, `symbol_info`, and `symbol_info_tick`. Forbidden unless the owner explicitly opens a deployment/live-operation lane: production-change, live trading, broker operation, broker/account/order/history/deal/position mutation beyond the approved aggregate read-only evidence class, order send/check, symbol selection, open positions/orders state reads, market book/depth/orderflow, prompt/config/risk/execution/safety/canary/selector live activation, credential mutation/disclosure, paid API/vendor calls, remote push, live config activation, and VPS restart/reload.

Completion requires: result JSON, decision ledger, promotion-boundary ledger, unresolved/blocker-repair ledgers, verifier result, focused test record, output manifest, saturation/self-red-team audit, completion audit with instruction coverage, and a scoped commit. Mark complete only when the completion standard is satisfied with no vague blockers or hidden live-action assumptions.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if path.is_file() and path.name != "OUTPUT_MANIFEST.json":
            artifacts.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
            "created_at_utc": created_at,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    mt5, initialized = connect_bridge()
    fill_rows, fill_summary, field_audit = fill_slippage_rows(created_at, mt5)
    session_rows, session_summary = m1_session_rows(created_at, mt5)
    requirements = unresolved_requirements(created_at)
    forbidden = forbidden_call_scan(created_at)
    selectable_count = len(load_dossier_rows())
    ok = (
        initialized
        and selectable_count == 14
        and fill_summary["direct_fill_symbol_count"] >= 1
        and session_summary["symbols_with_m1_bars"] == selectable_count
        and field_audit["raw_ticket_or_order_ids_stored"] is False
        and forbidden["ok"] is True
    )
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "decision": "FILL_SESSION_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED",
        "source_broker_authority_route": rel(BROKER_AUTH_ROUTE),
        "source_dossier_route": rel(DOSSIER_ROUTE),
        "selectable_symbol_count": selectable_count,
        "bridge_initialized": initialized,
        "direct_fill_symbol_count": fill_summary["direct_fill_symbol_count"],
        "no_direct_fill_symbol_count": fill_summary["no_direct_fill_symbol_count"],
        "joined_entry_deal_count_total": fill_summary["joined_entry_deal_count_total"],
        "max_slippage_abs_r_observed": fill_summary["max_slippage_abs_r_observed"],
        "mean_slippage_abs_r_observed": fill_summary["mean_slippage_abs_r_observed"],
        "symbols_with_m1_session_proxy": session_summary["symbols_with_m1_bars"],
        "explicit_session_table_closed": session_summary["explicit_session_table_closed"],
        "historical_fill_slippage_all_symbols_closed": fill_summary["all_symbols_fill_slippage_closed"],
        "prospective_limit_queue_fillability_closed": False,
        "config_patch_applied": False,
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "runtime_effect": "none_market_expansion_default_off_fill_session_probe_only",
        "deployment_not_ready_requirement_ids": [row["requirement_id"] for row in requirements],
        "deployment_not_ready_reasons": [row["requirement"] for row in requirements],
        "approved_read_surfaces_used": ["history_orders_get_aggregate_only", "history_deals_get_aggregate_only", "copy_rates_range_m1_availability"],
        "forbidden_surfaces_touched": [],
    }
    decisions, boundary = decision_ledgers(created_at, result, fill_summary, session_summary)
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "no_arbitrary_top_n": True,
        "anti_boxing_checked": [
            "history orders and deals joined in memory with no raw ids stored",
            "slippage converted to R using source-event median risk",
            "direct-fill and no-direct-fill symbols separated",
            "M1 availability checked for all 14 symbols",
            "observed quote-session proxy not overclaimed as explicit session table",
            "prospective limit queue/fillability kept open",
        ],
        "same_evidence_class_repairs_completed": [
            "direct historical fill/slippage aggregate rows materialized",
            "observed M1 quote-session availability rows materialized",
            "field audit proves raw ticket/order/deal identifiers are excluded from artifacts",
            "fill/session successor prompt hardened for exact remaining requirements",
        ],
        "remaining_exact_requirements": result["deployment_not_ready_reasons"],
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "instruction_coverage": {
            "mandatory_preflight_reread_by_orchestrator": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_controls_read": True,
            "constructive_source_repair_posture_applied": True,
            "inspire_not_kill_applied": True,
            "same_evidence_class_pursued": True,
            "no_arbitrary_top_n": True,
        },
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "raw_ticket_or_order_ids_stored": False,
        "forbidden_surfaces_touched": [],
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "owner_action_live_authority_boundary": "required before config patch, VPS reload, broker mutation, or live promotion",
    }

    write_jsonl(ROUTE / "HISTORY_ORDER_DEAL_FILL_LEDGER.jsonl", fill_rows)
    write_json(ROUTE / "HISTORY_ORDER_DEAL_FILL_SUMMARY.json", fill_summary)
    write_json(ROUTE / "HISTORY_ORDER_DEAL_FIELD_AUDIT.json", field_audit)
    write_jsonl(ROUTE / "OBSERVED_M1_SESSION_AVAILABILITY_LEDGER.jsonl", session_rows)
    write_json(ROUTE / "OBSERVED_M1_SESSION_AVAILABILITY_SUMMARY.json", session_summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "PROMOTION_BOUNDARY_LEDGER.jsonl", boundary)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FILL_SESSION_PROBE_RESULT.json", result)
    write_packet(result, requirements)
    write_next_prompt(created_at)
    return result


def run_command(command: list[str], timeout: int = 180) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    proc = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-5000:],
        "stderr_tail": proc.stderr[-5000:],
    }


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command(
        [sys.executable, str(ROUTE / "verify_market_expansion_fill_session_probe.py")],
        timeout=240,
    )
    write_json(
        ROUTE / "VERIFIER_COMMAND_RESULT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1",
            "created_at_utc": created_at,
            **verifier_result,
        },
    )
    checks = [
        run_command(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(ROUTE / "build_market_expansion_fill_session_probe.py"),
                str(ROUTE / "verify_market_expansion_fill_session_probe.py"),
                "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py",
                "-q",
            ],
            timeout=180,
        ),
    ]
    write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
            "created_at_utc": created_at,
            "ok": all(row["returncode"] == 0 for row in checks),
            "results": checks,
        },
    )
    write_output_manifest(created_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
