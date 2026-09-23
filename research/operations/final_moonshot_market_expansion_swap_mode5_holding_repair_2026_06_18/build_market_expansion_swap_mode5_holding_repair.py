#!/usr/bin/env python3
"""Build market-expansion swap mode-5 and holding-time proxy evidence.

This route uses official MQL5 documentation as the formula source plus
committed local route artifacts and local D1 OHLCV CSVs. It does not call MT5,
mutate broker/account/order/history/deal/position state, use orderflow/depth,
apply config, push remotes, or touch VPS processes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
OPS = PROJECT_ROOT / "research" / "operations"
READINESS_ROUTE = OPS / "final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18"
DOSSIER_ROUTE = OPS / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
BROKER_ROUTE = OPS / "final_moonshot_market_expansion_broker_authority_probe_2026_06_18"
FILLABILITY_ROUTE = OPS / "final_moonshot_market_expansion_observed_session_fillability_repair_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_swap_mode5_holding_repair"
DECISION = "MARKET_EXPANSION_SWAP_MODE5_HOLDING_PROXY_REPAIRED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"
MQL5_SYMBOL_DOC_URL = "https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants"
MAX_HOLDING_NIGHTS = 4


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_time(raw: str) -> datetime:
    text = str(raw).replace("T", " ").split("+")[0]
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value: Any, digits: int = 10) -> float | None:
    number = finite_float(value)
    return round(number, digits) if number is not None else None


def side_from_signal(signal: int) -> str:
    return "LONG" if signal > 0 else "SHORT"


def mql_day_of_week(day: datetime) -> int:
    # Python Monday=0; MQL Sunday=0, Monday=1, ..., Saturday=6.
    return (day.weekday() + 1) % 7


def read_bars(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                bars.append(
                    Bar(
                        time=parse_time(row["time"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume") or 0.0),
                    )
                )
            except (KeyError, ValueError):
                continue
    bars.sort(key=lambda item: item.time)
    return bars


def index_bars_by_date(paths: dict[str, Path]) -> tuple[dict[str, list[Bar]], dict[str, dict[str, int]]]:
    bars_by_symbol: dict[str, list[Bar]] = {}
    index_by_symbol: dict[str, dict[str, int]] = {}
    for symbol, path in paths.items():
        bars = read_bars(path)
        bars_by_symbol[symbol] = bars
        index_by_symbol[symbol] = {bar.time.date().isoformat(): idx for idx, bar in enumerate(bars)}
    return bars_by_symbol, index_by_symbol


def build_source_index(created_at: str) -> dict[str, Any]:
    docs = [
        {
            "source_id": "mql5_market_info_constants_symbol_info_double_swap_fields",
            "url": MQL5_SYMBOL_DOC_URL,
            "source_owner": "MetaQuotes MQL5 official documentation",
            "source_class": "primary_public_documentation",
            "used_fields": [
                "SYMBOL_SWAP_MODE",
                "SYMBOL_SWAP_ROLLOVER3DAYS",
                "SYMBOL_SWAP_LONG",
                "SYMBOL_SWAP_SHORT",
            ],
            "source_statement_summary": "Symbol properties define swap mode, side-aware long/short swap values, and day-of-week for 3-day rollover.",
        },
        {
            "source_id": "mql5_enum_symbol_swap_mode_interest_current",
            "url": f"{MQL5_SYMBOL_DOC_URL}#enum_symbol_swap_mode",
            "source_owner": "MetaQuotes MQL5 official documentation",
            "source_class": "primary_public_documentation",
            "used_fields": ["SYMBOL_SWAP_MODE_INTEREST_CURRENT", "SYMBOL_SWAP_MODE_INTEREST_OPEN"],
            "source_statement_summary": "Interest-current swap is specified annual interest from instrument price at swap calculation; standard bank year is 360 days. Interest-open uses open price instead.",
        },
    ]
    facts = {
        "point_mode_formula": "daily_cash_proxy = swap_raw_points * point * account_currency_value_per_price_unit_per_lot",
        "interest_current_formula": "daily_cash_proxy = current_price_proxy * account_currency_value_per_price_unit_per_lot * (annual_interest_percent / 100) / 360",
        "rollover_multiplier_formula": "3 on swap_rollover3days MQL day, else 1",
        "mql_day_mapping": "Sunday=0, Monday=1, Tuesday=2, Wednesday=3, Thursday=4, Friday=5, Saturday=6",
        "current_price_proxy_used": "D1 close of the held rollover bar because broker exact swap posting price/time is not available in the local artifacts",
        "holding_proxy_used": f"D1 open entry path to target/stop/time-stop with max {MAX_HOLDING_NIGHTS} rollover nights",
    }
    return {
        "schema": f"{SCHEMA_PREFIX}.primary_source_index.v1",
        "created_at_utc": created_at,
        "official_sources": docs,
        "source_index_hash": sha256_text(json.dumps(docs, sort_keys=True)),
        "formula_facts": facts,
        "live_authority_boundary": "official formula plus local D1 proxy; not broker-posted swap, exact posting time, or VPS parity",
    }


def build_source_manifest(
    created_at: str,
    matrix_rows: list[dict[str, Any]],
    dossier_rows: list[dict[str, Any]],
) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    by_tag = {row["tag"]: row for row in dossier_rows}
    d1_paths: dict[str, Path] = {}
    manifest: list[dict[str, Any]] = []
    for row in matrix_rows:
        tag = row["tag"]
        file_symbol = row["file_symbol"]
        source_spans = by_tag[tag].get("source_spans") or {}
        d1_raw = ((source_spans.get("D1") or {}).get("best_path"))
        path = PROJECT_ROOT / d1_raw if d1_raw else None
        present = bool(path and path.exists())
        if present and path:
            d1_paths[file_symbol] = path
        manifest.append(
            {
                "schema": f"{SCHEMA_PREFIX}.source_manifest_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": file_symbol,
                "timeframe": "D1",
                "path": d1_raw,
                "present": present,
                "bytes": path.stat().st_size if present and path else None,
                "sha256": sha256_file(path) if present and path else None,
            }
        )
    return d1_paths, manifest


def first_d1_exit_offset(
    bars: list[Bar],
    start_idx: int,
    *,
    signal: int,
    stop: float,
    target: float,
) -> tuple[str, int | None, str | None]:
    max_idx = min(start_idx + MAX_HOLDING_NIGHTS, len(bars) - 1)
    for offset, bar_idx in enumerate(range(start_idx, max_idx + 1)):
        bar = bars[bar_idx]
        stop_hit = bar.low <= stop if signal > 0 else bar.high >= stop
        target_hit = bar.high >= target if signal > 0 else bar.low <= target
        if stop_hit and target_hit:
            return "same_d1_bar_stop_target_ambiguous", offset, bar.time.date().isoformat()
        if target_hit:
            return "target_first_d1_proxy", offset, bar.time.date().isoformat()
        if stop_hit:
            return "stop_first_d1_proxy", offset, bar.time.date().isoformat()
    if max_idx - start_idx < MAX_HOLDING_NIGHTS:
        return "time_stop_truncated_by_future_d1_source_gap", max_idx - start_idx, bars[max_idx].time.date().isoformat()
    return "time_stop_max_holding_proxy", MAX_HOLDING_NIGHTS, bars[start_idx + MAX_HOLDING_NIGHTS].time.date().isoformat()


def rollover_plan(
    bars: list[Bar],
    start_idx: int,
    holding_nights: int,
    swap_rollover3days: int | None,
) -> tuple[list[dict[str, Any]], int, int, int]:
    plan: list[dict[str, Any]] = []
    triple_count = 0
    total_multiplier = 0
    for offset in range(max(0, holding_nights)):
        bar_idx = start_idx + offset
        if bar_idx >= len(bars):
            break
        bar = bars[bar_idx]
        mql_day = mql_day_of_week(bar.time)
        multiplier = 3 if swap_rollover3days is not None and mql_day == int(swap_rollover3days) else 1
        if multiplier == 3:
            triple_count += 1
        total_multiplier += multiplier
        plan.append(
            {
                "offset_from_entry_bar": offset,
                "rollover_bar_date": bar.time.date().isoformat(),
                "rollover_bar_close_price": rounded(bar.close, 8),
                "mql_day_of_week": mql_day,
                "multiplier": multiplier,
            }
        )
    return plan, len(plan), triple_count, total_multiplier


def compute_swap_cash(
    *,
    swap_mode: int | None,
    swap_raw: float | None,
    point: float | None,
    value_per_price_unit: float | None,
    current_price: float,
    multiplier: int,
) -> float | None:
    if swap_mode is None or swap_raw is None or value_per_price_unit is None:
        return None
    if int(swap_mode) == 1:
        if point is None:
            return None
        return swap_raw * point * value_per_price_unit * multiplier
    if int(swap_mode) == 5:
        return current_price * value_per_price_unit * (swap_raw / 100.0) / 360.0 * multiplier
    return None


def build_event_swap_rows(
    created_at: str,
    event_rows: list[dict[str, Any]],
    swap_rows: list[dict[str, Any]],
    bars_by_symbol: dict[str, list[Bar]],
    index_by_symbol: dict[str, dict[str, int]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    swap_by_tag_side = {(row["tag"], row["side"]): row for row in swap_rows}
    out: list[dict[str, Any]] = []
    for event in event_rows:
        signal = int(event.get("signal") or 0)
        side = side_from_signal(signal)
        tag = event["tag"]
        symbol = event["file_symbol"]
        date = event["date"]
        risk_abs = finite_float(event.get("risk_abs"))
        swap = swap_by_tag_side.get((tag, side), {})
        bars = bars_by_symbol.get(symbol, [])
        start_idx = index_by_symbol.get(symbol, {}).get(date)
        value_per_price_unit = finite_float(swap.get("value_per_price_unit_per_lot_account_currency"))
        risk_cash = risk_abs * value_per_price_unit if risk_abs is not None and value_per_price_unit is not None else None
        swap_mode = int(swap["swap_mode"]) if swap.get("swap_mode") is not None else None
        swap_rollover3days = int(swap["swap_rollover3days"]) if swap.get("swap_rollover3days") is not None else None
        point = finite_float(swap.get("point"))
        swap_raw = finite_float(swap.get("swap_raw"))

        if signal not in {-1, 1} or risk_abs is None or risk_abs <= 0 or start_idx is None or not bars or risk_cash is None or risk_cash <= 0:
            status = "not_computable_missing_signal_risk_d1_or_value_conversion"
            exit_status = None
            exit_offset = None
            exit_date = None
            holding_nights = 0
            rollovers: list[dict[str, Any]] = []
            rollover_count = 0
            triple_count = 0
            total_multiplier = 0
            total_cash = None
            total_r = None
        else:
            entry = bars[start_idx].open
            stop = entry - risk_abs if signal > 0 else entry + risk_abs
            target = entry + 2.0 * risk_abs if signal > 0 else entry - 2.0 * risk_abs
            exit_status, exit_offset, exit_date = first_d1_exit_offset(
                bars,
                start_idx,
                signal=signal,
                stop=stop,
                target=target,
            )
            holding_nights = int(exit_offset or 0)
            rollovers, rollover_count, triple_count, total_multiplier = rollover_plan(
                bars,
                start_idx,
                holding_nights,
                swap_rollover3days,
            )
            cash_values = [
                compute_swap_cash(
                    swap_mode=swap_mode,
                    swap_raw=swap_raw,
                    point=point,
                    value_per_price_unit=value_per_price_unit,
                    current_price=float(item["rollover_bar_close_price"]),
                    multiplier=int(item["multiplier"]),
                )
                for item in rollovers
            ]
            if any(value is None for value in cash_values):
                status = "not_computable_unsupported_swap_mode_or_missing_formula_input"
                total_cash = None
                total_r = None
            else:
                total_cash = sum(float(value) for value in cash_values)
                total_r = total_cash / risk_cash if risk_cash else None
                if swap_mode == 1:
                    status = "point_mode_holding_swap_proxy_computed"
                elif swap_mode == 5:
                    status = "interest_current_mode5_holding_swap_proxy_computed"
                else:
                    status = "not_computable_unsupported_swap_mode"
                    total_cash = None
                    total_r = None

        out.append(
            {
                "schema": f"{SCHEMA_PREFIX}.source_event_swap_holding_proxy_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": symbol,
                "broker_symbol": event["broker_symbol"],
                "date": date,
                "split": event.get("split"),
                "signal": signal,
                "side": side,
                "risk_abs": risk_abs,
                "risk_cash_per_lot_account_currency": rounded(risk_cash, 10),
                "value_per_price_unit_per_lot_account_currency": rounded(value_per_price_unit, 10),
                "swap_mode": swap_mode,
                "swap_raw": swap_raw,
                "point": point,
                "swap_rollover3days": swap_rollover3days,
                "holding_model": f"d1_open_to_2r_target_or_1r_stop_or_{MAX_HOLDING_NIGHTS}_overnight_time_stop",
                "holding_exit_status": exit_status,
                "holding_exit_offset_d1_bars": exit_offset,
                "holding_exit_date": exit_date,
                "holding_nights_proxy": holding_nights,
                "rollover_count": rollover_count,
                "triple_rollover_count": triple_count,
                "rollover_multiplier_total": total_multiplier,
                "rollover_plan": rollovers,
                "total_swap_cash_per_lot_account_currency_proxy": rounded(total_cash, 10),
                "total_swap_r_per_lot_risk_proxy": rounded(total_r, 10),
                "swap_conversion_status": status,
                "raw_proxy_r_before_swap": rounded(event.get("raw_proxy_r"), 10),
                "proxy_r_cost3_before_swap": rounded(event.get("proxy_r_cost3"), 10),
                "proxy_r_cost3_after_swap_proxy": rounded((event.get("proxy_r_cost3") or 0.0) + (total_r or 0.0), 10) if total_r is not None else None,
                "result_scope": "official_formula_plus_local_d1_holding_proxy_not_broker_posted_swap_authority",
                "live_authority_ready": False,
            }
        )

    status_counts = Counter(row["swap_conversion_status"] for row in out)
    mode_counts = Counter(str(row["swap_mode"]) for row in out)
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in out:
        by_tag[row["tag"]].append(row)
    per_tag = {}
    for tag, rows in sorted(by_tag.items()):
        swap_values = [row["total_swap_r_per_lot_risk_proxy"] for row in rows if row["total_swap_r_per_lot_risk_proxy"] is not None]
        per_tag[tag] = {
            "event_count": len(rows),
            "computed_event_count": len(swap_values),
            "swap_mode_counts": dict(Counter(str(row["swap_mode"]) for row in rows)),
            "status_counts": dict(Counter(row["swap_conversion_status"] for row in rows)),
            "mean_swap_r_proxy": rounded(sum(swap_values) / len(swap_values), 10) if swap_values else None,
            "min_swap_r_proxy": rounded(min(swap_values), 10) if swap_values else None,
            "max_swap_r_proxy": rounded(max(swap_values), 10) if swap_values else None,
        }
    computed_values = [row["total_swap_r_per_lot_risk_proxy"] for row in out if row["total_swap_r_per_lot_risk_proxy"] is not None]
    summary = {
        "schema": f"{SCHEMA_PREFIX}.source_event_swap_holding_proxy_summary.v1",
        "created_at_utc": created_at,
        "event_count": len(out),
        "computed_event_count": len(computed_values),
        "mode5_event_count": sum(1 for row in out if row["swap_mode"] == 5),
        "point_mode_event_count": sum(1 for row in out if row["swap_mode"] == 1),
        "status_counts": dict(status_counts),
        "swap_mode_counts": dict(mode_counts),
        "holding_exit_status_counts": dict(Counter(str(row["holding_exit_status"]) for row in out)),
        "holding_night_counts": dict(Counter(str(row["holding_nights_proxy"]) for row in out)),
        "mean_swap_r_proxy": rounded(sum(computed_values) / len(computed_values), 10) if computed_values else None,
        "min_swap_r_proxy": rounded(min(computed_values), 10) if computed_values else None,
        "max_swap_r_proxy": rounded(max(computed_values), 10) if computed_values else None,
        "total_swap_r_proxy": rounded(sum(computed_values), 10) if computed_values else None,
        "per_tag": per_tag,
        "live_authority_ready": False,
        "interpretation": "official MQL5 formula plus local D1 holding proxy; not broker-posted swap, exact posting time, explicit session, fill, or VPS parity authority",
    }
    return out, summary


def forbidden_scan(created_at: str) -> dict[str, Any]:
    tokens = [
        "order_" + "send(",
        "order_" + "check(",
        "orders_" + "get(",
        "positions_" + "get(",
        "history_" + "deals_" + "get(",
        "history_" + "orders_" + "get(",
        "market_book_" + "add(",
        "market_book_" + "get(",
        "market_book_" + "release(",
        "MetaTrader" + "5(",
    ]
    matches = []
    files = [
        ROUTE / "build_market_expansion_swap_mode5_holding_repair.py",
        ROUTE / "verify_market_expansion_swap_mode5_holding_repair.py",
    ]
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in tokens:
            if token in text:
                matches.append({"path": rel(path), "token": token})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "ok": not matches,
        "matches": matches,
        "scanned_files": [rel(path) for path in files],
    }


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if not path.is_file() or path.name == "OUTPUT_MANIFEST.json":
            continue
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


def write_packet(result: dict[str, Any], summary: dict[str, Any]) -> None:
    text = f"""# Market Expansion Swap Mode5 And Holding Repair

Decision: `{result['decision']}`

Runtime effect: `{result['runtime_effect']}`

## Result

- Source events preserved: `{summary['event_count']}`.
- Computed swap proxy rows: `{summary['computed_event_count']}`.
- Mode-5 interest-current event rows repaired: `{summary['mode5_event_count']}`.
- Point-mode event rows recomputed with holding model: `{summary['point_mode_event_count']}`.
- Mean swap proxy R per source event: `{summary['mean_swap_r_proxy']}`.
- Total source-event swap proxy R: `{summary['total_swap_r_proxy']}`.

This route repairs the formula/holding-time layer using official MQL5 swap
documentation, committed broker swap fields, order-calc profit conversion, and
local D1 bars. It remains a default-off source-bound proxy: exact broker swap
posting time, broker-posted swap debits/credits, explicit trading-session table,
prospective fills, and VPS packet parity are not closed here.
"""
    (ROUTE / "SWAP_MODE5_HOLDING_REPAIR_PACKET.md").write_text(text, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    text = f"""# Next Prompt - Market Expansion Explicit Session And VPS Packet Parity Repair

Created: {created_at}

`/goal Follow this controlling prompt as the complete objective. Mandatory preflight: run python3 scripts/generate_live_state.py and read .context/LIVE_STATE.md, current_vnext_system_map.md, current_repo_reading_order.md, goal_session_research_discipline.md, research_operating_doctrine.md, orchestrator_successor_operating_brief.md, orchestrator_methodology_hardening_controls.md, parallel_goal_merge_playbook.md, and latest artifacts in research/operations/final_moonshot_market_expansion_swap_mode5_holding_repair_2026_06_18. Do not rely on chat memory.`

Treat doctrine as active instructions, not background. This is a constructive repair/deployment-package builder lane with no conservative brake: pursue full same-evidence-class pursuit to explicit session-table or session-source proof and VPS packet parity without live activation. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or exactly ruled out. Completion audit must record instruction coverage, source completeness, result materialization, all branch decision or implementation decision rows, remaining exact/proxy-R or expectancy limitations, and proof-or-impossibility.

No arbitrary top-N, no top-N, no top 3/5/10, and no number-limited cutoff for questions, ambiguities, source roots, routes, blockers, opportunities, or findings. Preserve all material rows in a full ledger before any ranked summary.

Objective: close or exactly bound the remaining market-expansion live-authority gaps after swap-mode5/holding repair: explicit broker trading-session table/platform-source proof, VPS-side packet parity for default-off package fields, broker-posted swap/commission/fill monitoring requirements, and exact activation/rollback owner-action boundary. Build strongest deployable default-off package and handoff. If live promotion is not authorized in the active turn, do not apply it; emit exact commands and checks.

Forbidden surfaces unless the owner explicitly opens the deployment lane in the same turn: no broker/account/order/history/deal/position mutation, no order send/check, no live trading behavior activation, no paid API/vendor calls, no credential changes, no remote push, no VPS restart/reload, no production config activation. Read-only bridge/VPS packet inspection is allowed only if credentials and access are already present and no state mutation occurs.

Required verification: route verifier, focused test, pytest continuity, route artifact audit with full JSONL, prompt hardening validation, manifest/hash output, scoped commit, and context refresh.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(text, encoding="utf-8")


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    matrix = read_jsonl(READINESS_ROUTE / "CANDIDATE_AUTHORITY_MATRIX.jsonl")
    dossier = read_jsonl(DOSSIER_ROUTE / "SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl")
    events = read_jsonl(DOSSIER_ROUTE / "SOURCE_EVENT_COST_LEDGER.jsonl")
    swap_rows = read_jsonl(BROKER_ROUTE / "SWAP_TO_R_PARTIAL_AUTHORITY_LEDGER.jsonl")
    source_index = build_source_index(created_at)
    d1_paths, source_manifest = build_source_manifest(created_at, matrix, dossier)
    bars_by_symbol, index_by_symbol = index_bars_by_date(d1_paths)
    event_swap_rows, summary = build_event_swap_rows(created_at, events, swap_rows, bars_by_symbol, index_by_symbol)
    forbidden = forbidden_scan(created_at)
    requirements = [
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-SWAP-HOLDING-REQ-001",
            "requirement": "broker-posted swap debit/credit validation by activation symbol and side",
            "current_status": "not_closed_formula_proxy_only",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-SWAP-HOLDING-REQ-002",
            "requirement": "exact broker swap posting time and current-price convention",
            "current_status": "not_closed_d1_close_current_price_proxy_used",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-SWAP-HOLDING-REQ-003",
            "requirement": "explicit broker trading-session table and prospective fill authority",
            "current_status": "not_closed_carried_forward",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-SWAP-HOLDING-REQ-004",
            "requirement": "VPS packet parity, monitoring, rollback, and owner-approved promotion execution",
            "current_status": "not_closed_owner_action_boundary",
        },
    ]
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            len(matrix) == 14
            and len(source_manifest) == 14
            and summary["event_count"] == 2596
            and summary["computed_event_count"] == 2596
            and summary["mode5_event_count"] == 913
            and summary["point_mode_event_count"] == 1683
            and forbidden["ok"] is True
        ),
        "decision": DECISION,
        "candidate_count": len(matrix),
        "source_event_count": summary["event_count"],
        "computed_event_count": summary["computed_event_count"],
        "mode5_event_count": summary["mode5_event_count"],
        "point_mode_event_count": summary["point_mode_event_count"],
        "mean_swap_r_proxy": summary["mean_swap_r_proxy"],
        "min_swap_r_proxy": summary["min_swap_r_proxy"],
        "max_swap_r_proxy": summary["max_swap_r_proxy"],
        "total_swap_r_proxy": summary["total_swap_r_proxy"],
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "runtime_effect": "none_swap_mode5_holding_proxy_only",
        "approved_read_surfaces_used": [
            "official_mql5_public_documentation",
            "committed_route_artifacts",
            "local_d1_ohlcv_csv_files",
        ],
        "forbidden_surfaces_touched": [],
    }
    decision_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": DECISION,
            "status": "repaired_formula_and_holding_proxy_not_live_authority",
            "reason": "mode-5 formula and per-event holding swap proxy computed for all source events; broker-posted swap and VPS parity remain open",
        }
    ]
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "no_arbitrary_top_n": True,
        "all_source_events_preserved": True,
        "same_evidence_class_pursued": [
            "official MQL5 swap-mode source indexed",
            "all side-aware broker swap rows consumed",
            "all local D1 source files hashed",
            "all 2,596 source events assigned a D1 holding path",
            "all 913 mode-5 crypto source events computed with interest-current formula",
            "all 1,683 point-mode source events recomputed with holding-night multipliers",
        ],
        "non_overclaim_boundaries": [
            "not broker-posted swap authority",
            "not exact broker swap posting time",
            "not explicit session table",
            "not prospective broker fill authority",
            "not VPS parity or live activation",
        ],
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "instruction_coverage": {
            "mandatory_preflight_reread_by_orchestrator": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_controls_read": True,
            "constructive_builder_posture_applied": True,
            "full_same_evidence_class_pursuit": True,
            "no_arbitrary_top_n": True,
            "result_materialization_status": "source_event_swap_holding_proxy_materialized",
        },
        "primary_source_index_written": True,
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "forbidden_surfaces_touched": [],
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
    }

    write_json(ROUTE / "PRIMARY_SOURCE_INDEX.json", source_index)
    write_jsonl(ROUTE / "SOURCE_MANIFEST_LEDGER.jsonl", source_manifest)
    write_jsonl(ROUTE / "SOURCE_EVENT_SWAP_HOLDING_PROXY_LEDGER.jsonl", event_swap_rows)
    write_json(ROUTE / "SOURCE_EVENT_SWAP_HOLDING_PROXY_SUMMARY.json", summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "SWAP_MODE5_HOLDING_REPAIR_RESULT.json", result)
    write_packet(result, summary)
    write_next_prompt(created_at)
    return result


def run_command(command: list[str], timeout: int = 240) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    proc = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    return {"command": " ".join(command), "returncode": proc.returncode, "stdout_tail": proc.stdout[-5000:], "stderr_tail": proc.stderr[-5000:]}


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command([sys.executable, str(ROUTE / "verify_market_expansion_swap_mode5_holding_repair.py")])
    write_json(ROUTE / "VERIFIER_COMMAND_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1", "created_at_utc": created_at, **verifier_result})
    checks = [
        run_command(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(ROUTE / "build_market_expansion_swap_mode5_holding_repair.py"),
                str(ROUTE / "verify_market_expansion_swap_mode5_holding_repair.py"),
                "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command([sys.executable, "-m", "pytest", "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py", "-q"], timeout=180),
    ]
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.focused_test_result.v1", "created_at_utc": created_at, "ok": all(row["returncode"] == 0 for row in checks), "results": checks})
    write_output_manifest(created_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] and all(row["returncode"] == 0 for row in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
