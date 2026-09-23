#!/usr/bin/env python3
"""Build tick-recomputed path metrics for Wave2 filled trades.

This repair is source-bound to local redacted_account tick parquet evidence and
trade-record/broker-truth timestamps. It does not infer missing runtime intent.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

PROFIT_LEDGER = ROUTE_DIR / "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl"
HARD_HALT = REPO_ROOT / "research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03"
BROKER_GROUPS = HARD_HALT / "BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json"
BROKER_ORDERS = HARD_HALT / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json"

TICK_ROOTS = [
    Path("/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04/emergency_hard_halt_evidence/data/ticks/redacted_account_live_bee34003"),
    Path("/Users/borr/Documents/gtos/repo/ai-trading-agent/data/ticks/redacted_account_live_bee34003"),
    REPO_ROOT / "data/ticks/redacted_account_live_bee34003",
]

FIRST_PASSAGE_THRESHOLDS = [-1.0, 0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
GIVEBACK_DROPS = [0.25, 0.5, 1.0]


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def parse_iso(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(value: datetime | pd.Timestamp | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: Any, digits: int = 6) -> float | None:
    numeric = safe_float(value)
    if numeric is None:
        return None
    return round(numeric, digits)


def minutes_between(start: datetime, end: datetime | pd.Timestamp | None) -> float | None:
    if end is None or pd.isna(end):
        return None
    if isinstance(end, pd.Timestamp):
        end = end.to_pydatetime()
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return round((end.astimezone(timezone.utc) - start).total_seconds() / 60.0, 6)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> int:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return len(rows)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_broker_groups() -> dict[str, dict[str, Any]]:
    payload = json.loads(BROKER_GROUPS.read_text(encoding="utf-8"))
    trades = payload.get("trades") if isinstance(payload, dict) else []
    return {str(row.get("position_id")): row for row in trades if isinstance(row, dict) and row.get("position_id") not in (None, "")}


def load_orders_by_position() -> dict[str, list[dict[str, Any]]]:
    payload = json.loads(BROKER_ORDERS.read_text(encoding="utf-8"))
    orders: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in payload if isinstance(payload, list) else []:
        if not isinstance(order, dict):
            continue
        position_id = order.get("position_id")
        if position_id in (None, ""):
            continue
        orders[str(position_id)].append(order)
    for position_orders in orders.values():
        position_orders.sort(key=lambda item: item.get("time_setup_msc") or item.get("time_done_msc") or 0)
    return orders


def source_tick_symbol(source_path: str, symbol: str | None) -> str:
    parts = Path(source_path).parts
    if "trade_records" in parts:
        index = parts.index("trade_records") + 1
        if index < len(parts):
            return parts[index]
    alias = {
        "NDX100": "NAS100",
        "US30": "US30_cash",
        "UKOIL": "UKOIL_cash",
        "USOIL": "USOIL_cash",
    }
    return alias.get(str(symbol or ""), str(symbol or ""))


def trade_record_payload(source_path: str) -> tuple[dict[str, Any], str]:
    path = REPO_ROOT / source_path
    if not path.exists():
        return {}, "source_path_missing_on_disk"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - artifact records exact read failure.
        return {}, f"json_read_error:{exc}"
    if not isinstance(payload, dict):
        return {}, "source_payload_not_object"
    return payload, "source_payload_loaded"


def date_range(start: datetime, end: datetime) -> list[str]:
    day = start.date()
    out: list[str] = []
    while day <= end.date():
        out.append(day.isoformat())
        day += timedelta(days=1)
    return out


def first_directional_stop(
    side: str,
    entry_price: float,
    payload: dict[str, Any],
    broker_orders: list[dict[str, Any]],
) -> tuple[float | None, str, float | None]:
    side = side.upper()
    execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
    limit_intent = payload.get("limit_intent") if isinstance(payload.get("limit_intent"), dict) else {}
    trade_params = payload.get("trade_parameters") if isinstance(payload.get("trade_parameters"), dict) else {}

    candidates: list[tuple[str, Any]] = [
        ("execution.stop_loss_directionally_valid", execution.get("stop_loss")),
        ("limit_intent.stop_loss_directionally_valid", limit_intent.get("stop_loss")),
        ("trade_parameters.stop_loss_directionally_valid", trade_params.get("stop_loss")),
    ]
    for order in broker_orders:
        sl = safe_float(order.get("sl"))
        if sl is not None and sl != 0:
            candidates.append(("broker_initial_order.sl_directionally_valid", sl))
            break

    for source, raw_stop in candidates:
        stop = safe_float(raw_stop)
        if stop is None or stop == 0:
            continue
        distance = abs(entry_price - stop)
        if distance <= 0:
            continue
        if side in {"LONG", "BUY"} and stop < entry_price:
            return stop, source, distance
        if side in {"SHORT", "SELL"} and stop > entry_price:
            return stop, source, distance

    sl_distance = safe_float(execution.get("sl_distance"))
    if sl_distance is not None and sl_distance > 0:
        return None, "execution.sl_distance_only_stop_not_directionally_repairable", abs(sl_distance)
    return None, "risk_distance_missing_or_zero", None


TICK_CACHE: dict[Path, tuple[pd.DataFrame | None, str | None]] = {}


def read_tick_file(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    cached = TICK_CACHE.get(path)
    if cached is not None:
        return cached
    try:
        table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
        frame = table.to_pandas()
        frame = frame.dropna(subset=["ts_utc", "bid", "ask"]).sort_values("ts_utc")
        TICK_CACHE[path] = (frame, None)
        return frame, None
    except Exception as exc:  # noqa: BLE001 - source coverage records parse failure.
        TICK_CACHE[path] = (None, str(exc))
        return None, str(exc)


def resolve_tick_files(symbol: str, dates: list[str]) -> tuple[list[Path], list[str], list[dict[str, str]]]:
    files: list[Path] = []
    missing: list[str] = []
    selected: list[dict[str, str]] = []
    for date in dates:
        found = None
        for root in TICK_ROOTS:
            candidate = root / symbol / f"{date}.parquet"
            if candidate.exists():
                found = candidate
                break
        if found is None:
            missing.append(date)
            continue
        files.append(found)
        selected.append({"date": date, "path": found.as_posix(), "source_root": found.parent.parent.as_posix()})
    return files, missing, selected


def concat_tick_window(files: list[Path], start: datetime, end: datetime) -> tuple[pd.DataFrame, list[str]]:
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    for path in files:
        frame, error = read_tick_file(path)
        if error:
            errors.append(f"{path.as_posix()}:{error}")
            continue
        if frame is None:
            continue
        filtered = frame[(frame["ts_utc"] >= pd.Timestamp(start)) & (frame["ts_utc"] <= pd.Timestamp(end))]
        if not filtered.empty:
            frames.append(filtered)
    if not frames:
        return pd.DataFrame(columns=["ts_utc", "bid", "ask"]), errors
    return pd.concat(frames, ignore_index=True).sort_values("ts_utc"), errors


def first_passage(series: pd.DataFrame, entry_time: datetime, threshold: float) -> dict[str, Any]:
    if series.empty:
        return {"threshold_r": threshold, "hit": False, "time_utc": None, "minutes_from_entry": None, "r_at_hit": None}
    if threshold >= 0:
        hit_rows = series[series["path_r"] >= threshold]
    else:
        hit_rows = series[series["path_r"] <= threshold]
    if hit_rows.empty:
        return {"threshold_r": threshold, "hit": False, "time_utc": None, "minutes_from_entry": None, "r_at_hit": None}
    first = hit_rows.iloc[0]
    return {
        "threshold_r": threshold,
        "hit": True,
        "time_utc": iso(first["ts_utc"]),
        "minutes_from_entry": minutes_between(entry_time, first["ts_utc"]),
        "r_at_hit": round_or_none(first["path_r"]),
    }


def adverse_before_threshold(series: pd.DataFrame, threshold_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label in ("0.25", "0.5", "1.0"):
        threshold = float(label)
        passage = threshold_rows[label]
        if passage.get("hit") is True and passage.get("time_utc"):
            cutoff = pd.Timestamp(parse_iso(passage["time_utc"]))
            scoped = series[series["ts_utc"] <= cutoff]
        else:
            scoped = series
        out[f"min_r_before_plus_{label.replace('.', '_')}r"] = round_or_none(scoped["path_r"].min()) if not scoped.empty else None
    return out


def giveback_after_mfe(series: pd.DataFrame, entry_time: datetime, mfe_index: int | None, mfe_r: float | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if mfe_index is None or mfe_r is None or series.empty:
        for drop in GIVEBACK_DROPS:
            key = str(drop).replace(".", "_")
            out[f"first_giveback_{key}r_after_mfe_time_utc"] = None
            out[f"first_giveback_{key}r_after_mfe_minutes_from_entry"] = None
            out[f"first_giveback_{key}r_minutes_after_mfe"] = None
        return out
    after_mfe = series.iloc[mfe_index:]
    mfe_time = after_mfe.iloc[0]["ts_utc"]
    for drop in GIVEBACK_DROPS:
        key = str(drop).replace(".", "_")
        hit = after_mfe[after_mfe["path_r"] <= (mfe_r - drop)]
        if hit.empty:
            out[f"first_giveback_{key}r_after_mfe_time_utc"] = None
            out[f"first_giveback_{key}r_after_mfe_minutes_from_entry"] = None
            out[f"first_giveback_{key}r_minutes_after_mfe"] = None
            continue
        first = hit.iloc[0]
        out[f"first_giveback_{key}r_after_mfe_time_utc"] = iso(first["ts_utc"])
        out[f"first_giveback_{key}r_after_mfe_minutes_from_entry"] = minutes_between(entry_time, first["ts_utc"])
        out[f"first_giveback_{key}r_minutes_after_mfe"] = round(
            (first["ts_utc"].to_pydatetime() - mfe_time.to_pydatetime()).total_seconds() / 60.0,
            6,
        )
    return out


def path_metrics(series: pd.DataFrame, entry_time: datetime) -> dict[str, Any]:
    if series.empty:
        return {
            "tick_count": 0,
            "tick_window_first_time_utc": None,
            "tick_window_last_time_utc": None,
            "tick_mfe_r": None,
            "tick_mfe_time_utc": None,
            "tick_mfe_time_minutes": None,
            "tick_mae_r": None,
            "tick_mae_time_utc": None,
            "tick_mae_time_minutes": None,
            "terminal_tick_r": None,
            "first_passage": {},
            "near_mfe_within_0_10r_first_time_utc": None,
            "near_mfe_within_0_10r_last_time_utc": None,
            "near_mfe_within_0_10r_min_r": None,
            "near_mfe_within_0_10r_max_r": None,
            "near_mfe_within_0_10r_range_r": None,
        }

    mfe_index = int(series["path_r"].idxmax())
    mae_index = int(series["path_r"].idxmin())
    mfe_row = series.loc[mfe_index]
    mae_row = series.loc[mae_index]
    terminal_row = series.iloc[-1]
    threshold_map = {str(threshold): first_passage(series, entry_time, threshold) for threshold in FIRST_PASSAGE_THRESHOLDS}
    metrics = {
        "tick_count": int(len(series)),
        "tick_window_first_time_utc": iso(series.iloc[0]["ts_utc"]),
        "tick_window_last_time_utc": iso(series.iloc[-1]["ts_utc"]),
        "tick_mfe_r": round_or_none(mfe_row["path_r"]),
        "tick_mfe_time_utc": iso(mfe_row["ts_utc"]),
        "tick_mfe_time_minutes": minutes_between(entry_time, mfe_row["ts_utc"]),
        "tick_mae_r": round_or_none(mae_row["path_r"]),
        "tick_mae_time_utc": iso(mae_row["ts_utc"]),
        "tick_mae_time_minutes": minutes_between(entry_time, mae_row["ts_utc"]),
        "terminal_tick_r": round_or_none(terminal_row["path_r"]),
        "terminal_tick_time_utc": iso(terminal_row["ts_utc"]),
        "first_passage": threshold_map,
    }
    metrics.update(adverse_before_threshold(series, threshold_map))
    metrics.update(giveback_after_mfe(series, entry_time, mfe_index, safe_float(metrics["tick_mfe_r"])))

    near_mfe = series[series["path_r"] >= (safe_float(metrics["tick_mfe_r"]) - 0.10)]
    metrics["near_mfe_within_0_10r_tick_count"] = int(len(near_mfe))
    metrics["near_mfe_within_0_10r_tick_fraction"] = round(len(near_mfe) / len(series), 6)
    metrics["near_mfe_within_0_10r_span_minutes"] = (
        round((near_mfe.iloc[-1]["ts_utc"].to_pydatetime() - near_mfe.iloc[0]["ts_utc"].to_pydatetime()).total_seconds() / 60.0, 6)
        if len(near_mfe) > 1
        else 0.0 if len(near_mfe) == 1 else None
    )
    metrics["near_mfe_within_0_10r_first_time_utc"] = iso(near_mfe.iloc[0]["ts_utc"]) if len(near_mfe) else None
    metrics["near_mfe_within_0_10r_last_time_utc"] = iso(near_mfe.iloc[-1]["ts_utc"]) if len(near_mfe) else None
    metrics["near_mfe_within_0_10r_min_r"] = round_or_none(near_mfe["path_r"].min()) if len(near_mfe) else None
    metrics["near_mfe_within_0_10r_max_r"] = round_or_none(near_mfe["path_r"].max()) if len(near_mfe) else None
    metrics["near_mfe_within_0_10r_range_r"] = round_or_none(
        safe_float(metrics["near_mfe_within_0_10r_max_r"]) - safe_float(metrics["near_mfe_within_0_10r_min_r"])
    )
    metrics["mfe_to_terminal_giveback_r"] = round_or_none(safe_float(metrics["tick_mfe_r"]) - safe_float(metrics["terminal_tick_r"]))
    metrics["time_from_mfe_to_terminal_minutes"] = (
        round(
            (terminal_row["ts_utc"].to_pydatetime() - mfe_row["ts_utc"].to_pydatetime()).total_seconds() / 60.0,
            6,
        )
        if pd.notna(terminal_row["ts_utc"]) and pd.notna(mfe_row["ts_utc"])
        else None
    )
    after_mfe = series.loc[mfe_index:]
    metrics["worst_r_after_mfe"] = round_or_none(after_mfe["path_r"].min()) if not after_mfe.empty else None
    metrics["mfe_to_worst_after_mfe_reversal_r"] = round_or_none(safe_float(metrics["tick_mfe_r"]) - safe_float(metrics["worst_r_after_mfe"]))
    return metrics


def discrepancy_flags(row: dict[str, Any], metrics: dict[str, Any], actual_r: float | None) -> list[str]:
    flags: list[str] = []
    ledger_mfe = safe_float(row.get("mfe_r"))
    ledger_mae = safe_float(row.get("mae_r"))
    ledger_mfe_time = safe_float(row.get("mfe_time_minutes"))
    ledger_mae_time = safe_float(row.get("mae_time_minutes"))
    tick_mfe = safe_float(metrics.get("tick_mfe_r"))
    tick_mae = safe_float(metrics.get("tick_mae_r"))
    terminal = safe_float(metrics.get("terminal_tick_r"))
    if ledger_mfe is None or ledger_mae is None:
        flags.append("ledger_mfe_or_mae_missing")
    if ledger_mfe_time is not None and ledger_mfe_time < 0:
        flags.append("ledger_mfe_time_negative")
    if ledger_mae_time is not None and ledger_mae_time < 0:
        flags.append("ledger_mae_time_negative")
    if ledger_mfe is not None and tick_mfe is not None:
        delta = tick_mfe - ledger_mfe
        if abs(delta) >= 1.0:
            flags.append("mfe_delta_ge_1r")
        elif abs(delta) >= 0.25:
            flags.append("mfe_delta_ge_0_25r")
    if ledger_mae is not None and tick_mae is not None:
        delta = tick_mae - ledger_mae
        if abs(delta) >= 1.0:
            flags.append("mae_delta_ge_1r")
        elif abs(delta) >= 0.25:
            flags.append("mae_delta_ge_0_25r")
    if actual_r is not None and terminal is not None and abs(terminal - actual_r) >= 0.25:
        flags.append("terminal_tick_r_differs_from_broker_real_cash_r")
    if tick_mfe is not None and tick_mfe >= 1.0 and not row.get("partial_close_events"):
        flags.append("tick_mfe_ge_1r_no_recorded_partial_close")
    if actual_r is not None and actual_r < 0 and tick_mfe is not None and tick_mfe > 0:
        flags.append("loser_positive_tick_mfe_before_loss")
    return flags


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    profit_rows = read_jsonl(PROFIT_LEDGER)
    broker_groups = load_broker_groups()
    broker_orders = load_orders_by_position()
    output_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    close_source_counts: Counter[str] = Counter()
    tick_root_counts: Counter[str] = Counter()
    missing_tick_dates: Counter[str] = Counter()
    parse_error_count = 0
    loser_rows = 0
    loser_full_repaired = 0
    broker_time_repairs = 0
    full_repaired_rows = 0

    for ordinal, row in enumerate(profit_rows, start=1):
        source_path = str(row.get("source_path") or "")
        payload, source_status = trade_record_payload(source_path)
        execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        lifecycle = payload.get("lifecycle") if isinstance(payload.get("lifecycle"), dict) else {}
        position_id = str(row.get("broker_position_id") or "")
        group = broker_groups.get(position_id, {})
        position_orders = broker_orders.get(position_id, [])

        entry_time = parse_iso(execution.get("fill_time_utc"))
        close_time = parse_iso(execution.get("terminal_exit_time_utc") or lifecycle.get("terminal_exit_time_utc"))
        close_time_source = "trade_record_terminal_exit_time_utc"
        if close_time is None and group.get("last_time_utc"):
            broker_last = parse_iso(group.get("last_time_utc"))
            if broker_last is not None:
                close_time = broker_last - timedelta(hours=3)
                close_time_source = "broker_truth_last_time_utc_minus_3h_server_time_repair"
                broker_time_repairs += 1
        close_source_counts[close_time_source] += 1

        side = str(execution.get("direction") or row.get("side") or group.get("side") or "").upper()
        entry_price = safe_float(execution.get("executed_entry_price") or execution.get("entry_price") or group.get("entry_price"))
        stop_loss = None
        risk_basis = "not_evaluated"
        risk_distance = None
        if entry_price is not None:
            stop_loss, risk_basis, risk_distance = first_directional_stop(side, entry_price, payload, position_orders)

        actual_r = safe_float(row.get("actual_r"))
        if actual_r is not None and actual_r < 0:
            loser_rows += 1

        tick_symbol = source_tick_symbol(source_path, row.get("symbol"))
        dates = date_range(entry_time, close_time) if entry_time and close_time else []
        tick_files, missing_dates, selected_files = resolve_tick_files(tick_symbol, dates)
        for missing_date in missing_dates:
            missing_tick_dates[f"{tick_symbol}/{missing_date}"] += 1
        for selected in selected_files:
            tick_root_counts[selected["source_root"]] += 1

        base_output: dict[str, Any] = {
            "generated_at_utc": GENERATED_AT,
            "row_ordinal": ordinal,
            "row_id": f"tick_path_repair:{ordinal}:{row.get('broker_position_id')}:{row.get('trade_id')}",
            "profit_harvest_row_id": row.get("row_id"),
            "trade_id": row.get("trade_id"),
            "candidate_id": row.get("candidate_id"),
            "broker_position_id": row.get("broker_position_id"),
            "symbol": row.get("symbol"),
            "tick_symbol": tick_symbol,
            "side": side,
            "source_path": source_path,
            "source_read_status": source_status,
            "entry_time_utc": iso(entry_time),
            "close_time_utc": iso(close_time),
            "close_time_source": close_time_source,
            "entry_price": round_or_none(entry_price),
            "stop_loss_for_r": round_or_none(stop_loss),
            "risk_distance_for_r": round_or_none(risk_distance),
            "risk_basis": risk_basis,
            "tick_date_window": dates,
            "tick_source_files": selected_files,
            "missing_tick_dates": missing_dates,
            "ledger_actual_r": round_or_none(actual_r),
            "ledger_mfe_r": row.get("mfe_r"),
            "ledger_mae_r": row.get("mae_r"),
            "ledger_mfe_time_minutes": row.get("mfe_time_minutes"),
            "ledger_mae_time_minutes": row.get("mae_time_minutes"),
            "ledger_hold_minutes": row.get("hold_minutes"),
            "partial_close_count": row.get("partial_close_count"),
            "selected_policy": row.get("selected_policy"),
            "execution_policy_id": row.get("execution_policy_id"),
            "evidence_class": "tick_parquet_recompute_with_trade_record_and_broker_truth_timestamp_repair",
            "result_use_status": "source_bound_path_repair_not_runtime_intent",
        }

        if not entry_time or not close_time or entry_price is None or risk_distance is None or risk_distance <= 0:
            status = "blocked_missing_entry_close_or_risk_basis"
            status_counts[status] += 1
            base_output.update(
                {
                    "tick_repair_status": status,
                    "full_tick_window_covered": False,
                    "usable_for_full_first_passage": False,
                    "tick_count": 0,
                    "tick_parse_errors": [],
                    "ledger_basis_discrepancy_flags": ["missing_entry_close_or_risk_basis"],
                }
            )
            output_rows.append(base_output)
            continue

        tick_window, parse_errors = concat_tick_window(tick_files, entry_time, close_time)
        parse_error_count += len(parse_errors)
        if not tick_window.empty:
            if side in {"LONG", "BUY"}:
                tick_window = tick_window.assign(path_r=(tick_window["bid"] - entry_price) / risk_distance)
                price_basis = "long_uses_bid"
            elif side in {"SHORT", "SELL"}:
                tick_window = tick_window.assign(path_r=(entry_price - tick_window["ask"]) / risk_distance)
                price_basis = "short_uses_ask"
            else:
                tick_window = tick_window.assign(path_r=pd.NA)
                price_basis = "unknown_side"
        else:
            price_basis = "no_tick_rows"

        full_window_covered = not missing_dates and not parse_errors
        if tick_window.empty:
            status = "tick_window_no_rows_in_entry_exit_interval"
        elif full_window_covered:
            status = "full_tick_window_recomputed"
            full_repaired_rows += 1
            if actual_r is not None and actual_r < 0:
                loser_full_repaired += 1
        else:
            status = "partial_tick_window_missing_source_dates_or_parse_errors"
        status_counts[status] += 1

        metrics = path_metrics(tick_window, entry_time)
        flags = discrepancy_flags(row, metrics, actual_r)
        base_output.update(metrics)
        base_output.update(
            {
                "tick_repair_status": status,
                "full_tick_window_covered": full_window_covered and not tick_window.empty,
                "usable_for_full_first_passage": status == "full_tick_window_recomputed",
                "executable_price_basis": price_basis,
                "tick_parse_errors": parse_errors,
                "tick_minus_ledger_mfe_r": round_or_none(safe_float(metrics.get("tick_mfe_r")) - safe_float(row.get("mfe_r")) if safe_float(metrics.get("tick_mfe_r")) is not None and safe_float(row.get("mfe_r")) is not None else None),
                "tick_minus_ledger_mae_r": round_or_none(safe_float(metrics.get("tick_mae_r")) - safe_float(row.get("mae_r")) if safe_float(metrics.get("tick_mae_r")) is not None and safe_float(row.get("mae_r")) is not None else None),
                "terminal_tick_minus_broker_actual_r": round_or_none(safe_float(metrics.get("terminal_tick_r")) - actual_r if safe_float(metrics.get("terminal_tick_r")) is not None and actual_r is not None else None),
                "ledger_basis_discrepancy_flags": flags,
                "loser_positive_mfe_before_loss_tick_repaired": bool(actual_r is not None and actual_r < 0 and safe_float(metrics.get("tick_mfe_r")) is not None and safe_float(metrics.get("tick_mfe_r")) > 0),
                "mfe_reversal_bucket": (
                    "giveback_ge_1r"
                    if safe_float(metrics.get("mfe_to_terminal_giveback_r")) is not None and safe_float(metrics.get("mfe_to_terminal_giveback_r")) >= 1.0
                    else "giveback_ge_0_5r"
                    if safe_float(metrics.get("mfe_to_terminal_giveback_r")) is not None and safe_float(metrics.get("mfe_to_terminal_giveback_r")) >= 0.5
                    else "giveback_lt_0_5r"
                    if safe_float(metrics.get("mfe_to_terminal_giveback_r")) is not None
                    else "missing"
                ),
            }
        )
        output_rows.append(base_output)

    audit = {
        "generated_at_utc": GENERATED_AT,
        "route": rel(ROUTE_DIR),
        "source_artifacts": {
            "profit_harvest_ledger": rel(PROFIT_LEDGER),
            "broker_trade_groups": rel(BROKER_GROUPS),
            "broker_orders": rel(BROKER_ORDERS),
            "tick_roots_considered": [path.as_posix() for path in TICK_ROOTS],
        },
        "filled_rows": len(profit_rows),
        "tick_repaired_full_rows": full_repaired_rows,
        "tick_partial_rows": status_counts["partial_tick_window_missing_source_dates_or_parse_errors"],
        "tick_no_window_rows": status_counts["tick_window_no_rows_in_entry_exit_interval"],
        "tick_blocked_rows": status_counts["blocked_missing_entry_close_or_risk_basis"],
        "loser_rows": loser_rows,
        "loser_full_tick_repaired_rows": loser_full_repaired,
        "broker_truth_minus_3h_close_time_repairs": broker_time_repairs,
        "status_counts": dict(status_counts),
        "close_time_source_counts": dict(close_source_counts),
        "tick_source_root_counts": dict(tick_root_counts),
        "missing_tick_date_counts": dict(missing_tick_dates),
        "parquet_parse_error_count": parse_error_count,
        "thresholds_r": FIRST_PASSAGE_THRESHOLDS,
        "executable_path_basis": {
            "long": "bid",
            "short": "ask",
            "r_denominator": "risk_distance_for_r",
        },
        "claim_boundary": {
            "full_tick_window_recomputed": "suitable for source-bound first-passage, MFE, MAE, giveback, and reversal diagnostics",
            "partial_tick_window_missing_source_dates_or_parse_errors": "diagnostic only; early path may be absent",
            "tick_window_no_rows_in_entry_exit_interval": "not repaired from current local tick evidence",
            "runtime_intent": "not reconstructed by this artifact",
        },
    }
    return output_rows, audit


def passage(row: dict[str, Any], threshold: str) -> dict[str, Any]:
    first_passage = row.get("first_passage") if isinstance(row.get("first_passage"), dict) else {}
    value = first_passage.get(threshold)
    return value if isinstance(value, dict) else {}


def passage_minutes(row: dict[str, Any], threshold: str) -> float | None:
    return round_or_none(passage(row, threshold).get("minutes_from_entry"))


def passage_hit(row: dict[str, Any], threshold: str) -> bool:
    return passage(row, threshold).get("hit") is True


def hold_minutes(row: dict[str, Any]) -> float | None:
    entry = parse_iso(row.get("entry_time_utc"))
    close = parse_iso(row.get("close_time_utc"))
    if entry is None or close is None:
        return round_or_none(row.get("ledger_hold_minutes"))
    return round((close - entry).total_seconds() / 60.0, 6)


def crossed_date(row: dict[str, Any]) -> bool | None:
    entry = parse_iso(row.get("entry_time_utc"))
    close = parse_iso(row.get("close_time_utc"))
    if entry is None or close is None:
        return None
    return entry.date() != close.date()


def path_source_status(row: dict[str, Any]) -> str:
    if row.get("tick_repair_status") == "full_tick_window_recomputed":
        return "tick_full_window_source_bound"
    if row.get("tick_repair_status") == "partial_tick_window_missing_source_dates_or_parse_errors":
        return "tick_partial_window_diagnostic_only"
    if row.get("tick_repair_status") == "tick_window_no_rows_in_entry_exit_interval":
        return "tick_file_present_but_no_rows_in_trade_window"
    return "path_source_gap"


def adverse_excursion_disposition(row: dict[str, Any]) -> str:
    mae = safe_float(row.get("tick_mae_r"))
    min_before_025 = safe_float(row.get("min_r_before_plus_0_25r"))
    if mae is None:
        return "source_gap_no_tick_mae"
    if not passage_hit(row, "0.25"):
        return "adverse_or_stalled_without_plus_0_25r" if mae < 0 else "no_plus_0_25r_no_adverse_tick_mae"
    if min_before_025 is not None and min_before_025 <= -0.5:
        return "deep_adverse_before_first_useful_profit"
    if min_before_025 is not None and min_before_025 <= -0.25:
        return "adverse_before_first_useful_profit"
    if min_before_025 is not None and min_before_025 < 0:
        return "minor_adverse_before_first_useful_profit"
    return "no_material_adverse_before_first_useful_profit"


def destination_efficiency(row: dict[str, Any]) -> str:
    if row.get("tick_repair_status") != "full_tick_window_recomputed":
        return "source_gap_or_partial_window"
    if passage_hit(row, "1.0"):
        minutes = passage_minutes(row, "1.0")
        if minutes is not None and minutes <= 60:
            return "reached_1r_within_1h"
        if minutes is not None and minutes <= 360:
            return "reached_1r_within_6h"
        return "reached_1r_slow_or_stale"
    if passage_hit(row, "0.5"):
        return "reached_0_5r_not_1r"
    if passage_hit(row, "0.25"):
        return "reached_0_25r_not_0_5r"
    return "never_reached_plus_0_25r"


def stale_thesis_status(row: dict[str, Any]) -> str:
    hold = hold_minutes(row)
    next_day = crossed_date(row)
    if hold is None:
        return "hold_time_source_gap"
    if hold >= 1440:
        return "stale_hold_ge_24h"
    if hold >= 720:
        return "stale_hold_ge_12h"
    if hold >= 360:
        return "stale_hold_ge_6h"
    if next_day:
        return "next_day_resolution_lt_6h"
    return "intraday_or_short_hold"


def harvest_failure_status(row: dict[str, Any]) -> str:
    actual_r = safe_float(row.get("ledger_actual_r"))
    mfe = safe_float(row.get("tick_mfe_r"))
    terminal = safe_float(row.get("terminal_tick_r"))
    if mfe is None:
        return "source_gap_no_tick_mfe"
    if actual_r is not None and actual_r < 0 and mfe > 0:
        if mfe >= 1.0:
            return "loser_reached_1r_or_more_before_loss"
        if mfe >= 0.5:
            return "loser_reached_0_5r_before_loss"
        if mfe >= 0.25:
            return "loser_reached_0_25r_before_loss"
        return "loser_positive_mfe_below_0_25r"
    if actual_r is not None and actual_r < 0:
        return "loser_no_positive_tick_mfe_to_harvest"
    if terminal is not None and mfe - terminal >= 1.0:
        return "winner_or_breakeven_large_mfe_giveback"
    if terminal is not None and mfe - terminal >= 0.5:
        return "winner_or_breakeven_moderate_mfe_giveback"
    return "no_material_harvest_failure_on_tick_path"


def base_path_identity(row: dict[str, Any], prefix: str) -> dict[str, Any]:
    return {
        "generated_at_utc": GENERATED_AT,
        "row_id": f"{prefix}:{row.get('row_ordinal')}:{row.get('broker_position_id')}:{row.get('trade_id')}",
        "source_tick_repair_row_id": row.get("row_id"),
        "broker_position_id": row.get("broker_position_id"),
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "symbol": row.get("symbol"),
        "tick_symbol": row.get("tick_symbol"),
        "side": row.get("side"),
        "entry_time_utc": row.get("entry_time_utc"),
        "close_time_utc": row.get("close_time_utc"),
        "close_time_source": row.get("close_time_source"),
        "source_path": row.get("source_path"),
        "source_paths": [row.get("source_path"), "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl"],
        "evidence_class": row.get("evidence_class"),
        "result_use_status": row.get("result_use_status"),
        "path_source_status": path_source_status(row),
        "tick_repair_status": row.get("tick_repair_status"),
        "full_tick_window_covered": row.get("full_tick_window_covered"),
        "usable_for_full_first_passage": row.get("usable_for_full_first_passage"),
        "missing_tick_dates": row.get("missing_tick_dates"),
    }


def build_first_passage_rows(tick_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in tick_rows:
        out = base_path_identity(row, "first_passage_ttd")
        out.update(
            {
                "entry_price": row.get("entry_price"),
                "stop_loss_for_r": row.get("stop_loss_for_r"),
                "risk_distance_for_r": row.get("risk_distance_for_r"),
                "actual_r": row.get("ledger_actual_r"),
                "terminal_tick_r": row.get("terminal_tick_r"),
                "tick_mfe_r": row.get("tick_mfe_r"),
                "tick_mae_r": row.get("tick_mae_r"),
                "time_to_green_minutes": passage_minutes(row, "0.0"),
                "time_to_plus_0_25r_minutes": passage_minutes(row, "0.25"),
                "time_to_plus_0_5r_minutes": passage_minutes(row, "0.5"),
                "time_to_plus_1r_minutes": passage_minutes(row, "1.0"),
                "time_to_plus_1_5r_minutes": passage_minutes(row, "1.5"),
                "time_to_plus_2r_minutes": passage_minutes(row, "2.0"),
                "time_to_plus_3r_minutes": passage_minutes(row, "3.0"),
                "time_to_minus_1r_minutes": passage_minutes(row, "-1.0"),
                "first_passage": row.get("first_passage"),
                "destination_efficiency": destination_efficiency(row),
                "same_evidence_class_repairs_attempted": [
                    "joined_trade_record_fill_and_close_times",
                    "repaired_missing_close_time_from_broker_truth_minus_3h_when_needed",
                    "read_local_tick_parquet_window",
                    "computed_executable_bid_ask_r_path",
                ],
                "status": "source_bound_first_passage_computed" if row.get("usable_for_full_first_passage") else "partial_or_missing_tick_window_source_gap",
                "v4_requirement_id": "EXECUTION_MANAGER_V4_FIRST_PASSAGE_AND_TTD",
                "owning_wave3_lane": "historical_replay_digital_twin_v4",
            }
        )
        rows.append(out)
    return rows


def build_entry_path_rows(tick_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in tick_rows:
        out = base_path_identity(row, "entry_path_mae_mfe_ttd")
        out.update(
            {
                "entry_price": row.get("entry_price"),
                "stop_loss_for_r": row.get("stop_loss_for_r"),
                "risk_distance_for_r": row.get("risk_distance_for_r"),
                "ledger_mfe_r": row.get("ledger_mfe_r"),
                "ledger_mae_r": row.get("ledger_mae_r"),
                "ledger_mfe_time_minutes": row.get("ledger_mfe_time_minutes"),
                "ledger_mae_time_minutes": row.get("ledger_mae_time_minutes"),
                "tick_mfe_r": row.get("tick_mfe_r"),
                "tick_mfe_time_utc": row.get("tick_mfe_time_utc"),
                "tick_mfe_time_minutes": row.get("tick_mfe_time_minutes"),
                "tick_mae_r": row.get("tick_mae_r"),
                "tick_mae_time_utc": row.get("tick_mae_time_utc"),
                "tick_mae_time_minutes": row.get("tick_mae_time_minutes"),
                "tick_minus_ledger_mfe_r": row.get("tick_minus_ledger_mfe_r"),
                "tick_minus_ledger_mae_r": row.get("tick_minus_ledger_mae_r"),
                "adverse_excursion_disposition": adverse_excursion_disposition(row),
                "min_r_before_plus_0_25r": row.get("min_r_before_plus_0_25r"),
                "min_r_before_plus_0_5r": row.get("min_r_before_plus_0_5r"),
                "min_r_before_plus_1_0r": row.get("min_r_before_plus_1_0r"),
                "time_to_plus_0_25r_minutes": passage_minutes(row, "0.25"),
                "time_to_plus_0_5r_minutes": passage_minutes(row, "0.5"),
                "time_to_plus_1r_minutes": passage_minutes(row, "1.0"),
                "ledger_basis_discrepancy_flags": row.get("ledger_basis_discrepancy_flags"),
                "finding": f"{row.get('symbol')} {row.get('side')} tick path {adverse_excursion_disposition(row)}; {destination_efficiency(row)}",
                "question_id": ["W2Q_ENTRY_PATH_MFE_MAE", "W2Q_LOSER_MFE_HARVEST"],
                "status": "source_bound_tick_path_computed" if row.get("tick_count", 0) else "source_gap_no_tick_rows",
                "v4_requirement_id": "EXECUTION_MANAGER_V4_ENTRY_PATH_AND_ADVERSE_EXCURSION",
                "owning_wave3_lane": "execution_manager_v4",
            }
        )
        rows.append(out)
    return rows


def build_poor_entry_rows(tick_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in tick_rows:
        out = base_path_identity(row, "poor_entry_adverse_excursion")
        out.update(
            {
                "entry_quality_status": adverse_excursion_disposition(row),
                "tick_mae_r": row.get("tick_mae_r"),
                "tick_mae_time_minutes": row.get("tick_mae_time_minutes"),
                "tick_mfe_r": row.get("tick_mfe_r"),
                "time_to_plus_0_25r_minutes": passage_minutes(row, "0.25"),
                "time_to_plus_0_5r_minutes": passage_minutes(row, "0.5"),
                "time_to_plus_1r_minutes": passage_minutes(row, "1.0"),
                "min_r_before_plus_0_25r": row.get("min_r_before_plus_0_25r"),
                "min_r_before_plus_0_5r": row.get("min_r_before_plus_0_5r"),
                "min_r_before_plus_1_0r": row.get("min_r_before_plus_1_0r"),
                "implementation_decision": "selector_or_execution_manager_must_penalize_entries_with_deep_adverse_before_useful_profit",
                "status": "source_bound_entry_adverse_excursion_computed" if row.get("tick_count", 0) else "source_gap_no_tick_rows",
            }
        )
        rows.append(out)
    return rows


def build_stale_rows(tick_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in tick_rows:
        out = base_path_identity(row, "stale_thesis_ttd")
        out.update(
            {
                "hold_minutes_repaired": hold_minutes(row),
                "crossed_utc_date": crossed_date(row),
                "stale_thesis_status": stale_thesis_status(row),
                "destination_efficiency": destination_efficiency(row),
                "time_to_plus_0_25r_minutes": passage_minutes(row, "0.25"),
                "time_to_plus_0_5r_minutes": passage_minutes(row, "0.5"),
                "time_to_plus_1r_minutes": passage_minutes(row, "1.0"),
                "tick_mfe_r": row.get("tick_mfe_r"),
                "mfe_to_terminal_giveback_r": row.get("mfe_to_terminal_giveback_r"),
                "terminal_tick_r": row.get("terminal_tick_r"),
                "implementation_decision": "execution_manager_v4_requires_thesis_horizon_and_stale_position_opportunity_cost_gate",
                "status": "source_bound_stale_thesis_ttd_computed" if row.get("tick_count", 0) else "source_gap_no_tick_rows",
            }
        )
        rows.append(out)
    return rows


def build_loser_harvest_rows(tick_rows: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    rows = []
    for row in tick_rows:
        actual_r = safe_float(row.get("ledger_actual_r"))
        if actual_r is None or actual_r >= 0:
            continue
        out = base_path_identity(row, prefix)
        out.update(
            {
                "actual_r": row.get("ledger_actual_r"),
                "tick_mfe_r": row.get("tick_mfe_r"),
                "tick_mfe_time_utc": row.get("tick_mfe_time_utc"),
                "tick_mfe_time_minutes": row.get("tick_mfe_time_minutes"),
                "tick_mae_r": row.get("tick_mae_r"),
                "tick_mae_time_utc": row.get("tick_mae_time_utc"),
                "tick_mae_time_minutes": row.get("tick_mae_time_minutes"),
                "terminal_tick_r": row.get("terminal_tick_r"),
                "mfe_to_terminal_giveback_r": row.get("mfe_to_terminal_giveback_r"),
                "mfe_to_worst_after_mfe_reversal_r": row.get("mfe_to_worst_after_mfe_reversal_r"),
                "worst_r_after_mfe": row.get("worst_r_after_mfe"),
                "near_mfe_within_0_10r_span_minutes": row.get("near_mfe_within_0_10r_span_minutes"),
                "near_mfe_within_0_10r_tick_count": row.get("near_mfe_within_0_10r_tick_count"),
                "near_mfe_within_0_10r_tick_fraction": row.get("near_mfe_within_0_10r_tick_fraction"),
                "near_mfe_within_0_10r_first_time_utc": row.get("near_mfe_within_0_10r_first_time_utc"),
                "near_mfe_within_0_10r_last_time_utc": row.get("near_mfe_within_0_10r_last_time_utc"),
                "near_mfe_within_0_10r_min_r": row.get("near_mfe_within_0_10r_min_r"),
                "near_mfe_within_0_10r_max_r": row.get("near_mfe_within_0_10r_max_r"),
                "near_mfe_within_0_10r_range_r": row.get("near_mfe_within_0_10r_range_r"),
                "first_giveback_0_25r_after_mfe_minutes_from_entry": row.get("first_giveback_0_25r_after_mfe_minutes_from_entry"),
                "first_giveback_0_5r_after_mfe_minutes_from_entry": row.get("first_giveback_0_5r_after_mfe_minutes_from_entry"),
                "first_giveback_1_0r_after_mfe_minutes_from_entry": row.get("first_giveback_1_0r_after_mfe_minutes_from_entry"),
                "first_giveback_0_25r_minutes_after_mfe": row.get("first_giveback_0_25r_minutes_after_mfe"),
                "first_giveback_0_5r_minutes_after_mfe": row.get("first_giveback_0_5r_minutes_after_mfe"),
                "first_giveback_1_0r_minutes_after_mfe": row.get("first_giveback_1_0r_minutes_after_mfe"),
                "harvest_failure_status": harvest_failure_status(row),
                "reversal_timestamp_0_25r_giveback_utc": row.get("first_giveback_0_25r_after_mfe_time_utc"),
                "consolidation_proxy_status": "near_mfe_band_0_10r_tick_dwell_proxy",
                "source_gap": None if row.get("tick_count", 0) else "tick_window_not_available_for_consolidation_reversal",
                "same_evidence_class_repairs_attempted": [
                    "tick_recomputed_loser_mfe_mae",
                    "tick_recomputed_mfe_giveback_timing",
                    "near_mfe_dwell_proxy_from_tick_path",
                    "terminal_tick_r_comparison",
                ],
                "status": "source_bound_loser_harvest_path_computed" if row.get("tick_count", 0) else "source_gap_no_tick_rows",
                "v4_requirement_id": "PROFIT_HARVEST_V4_MFE_CAPTURE_AND_REVERSAL",
                "owning_wave3_lane": "profit_harvest_mfe_capture_v4",
                "implementation_decision": "profit_harvest_v4_requires_mfe_capture_be_trailing_or_time_stop_when_tick_path_reaches_useful_profit_before_loss",
            }
        )
        rows.append(out)
    return rows


def write_derived_path_ledgers(tick_rows: list[dict[str, Any]]) -> dict[str, int]:
    first_passage_rows = build_first_passage_rows(tick_rows)
    entry_path_rows = build_entry_path_rows(tick_rows)
    poor_entry_rows = build_poor_entry_rows(tick_rows)
    stale_rows = build_stale_rows(tick_rows)
    loser_rows = build_loser_harvest_rows(tick_rows, "loser_mfe_harvest")
    profit_reversal_rows = build_loser_harvest_rows(tick_rows, "profit_path_consolidation_reversal")

    counts = {
        "WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl", first_passage_rows),
        "WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl", entry_path_rows),
        "WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl", entry_path_rows),
        "WAVE2_POOR_ENTRY_ADVERSE_EXCURSION_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_POOR_ENTRY_ADVERSE_EXCURSION_LEDGER.jsonl", poor_entry_rows),
        "WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl", stale_rows),
        "WAVE2_OVERNIGHT_NEXT_DAY_STALE_THESIS_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_OVERNIGHT_NEXT_DAY_STALE_THESIS_LEDGER.jsonl", stale_rows),
        "WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl", loser_rows),
        "WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl", loser_rows),
        "WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl": write_jsonl(ROUTE_DIR / "WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl", profit_reversal_rows),
    }
    return counts


def build_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        rows = None
        if path.suffix == ".jsonl":
            with path.open(encoding="utf-8") as handle:
                rows = sum(1 for line in handle if line.strip())
        files.append(
            {
                "path": rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "jsonl_rows": rows,
            }
        )
    return {
        "generated_at_utc": GENERATED_AT,
        "route": rel(ROUTE_DIR),
        "completion_status": "initial_spine_materialized_not_complete_allocator_window_and_tick_path_repair_added",
        "files": files,
    }


def main() -> int:
    rows, audit = build_rows()
    write_jsonl(ROUTE_DIR / "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl", rows)
    write_json(ROUTE_DIR / "WAVE2_TICK_REPAIR_SOURCE_COVERAGE_AUDIT.json", audit)
    derived_counts = write_derived_path_ledgers(rows)
    write_json(ROUTE_DIR / "WAVE2_OUTPUT_MANIFEST.json", build_manifest())
    print(
        json.dumps(
            {
                "ok": True,
                "generated_at_utc": GENERATED_AT,
                "route": rel(ROUTE_DIR),
                "output_rows": len(rows),
                "tick_repaired_full_rows": audit["tick_repaired_full_rows"],
                "tick_partial_rows": audit["tick_partial_rows"],
                "tick_no_window_rows": audit["tick_no_window_rows"],
                "tick_blocked_rows": audit["tick_blocked_rows"],
                "derived_path_ledgers": derived_counts,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
