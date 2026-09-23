#!/usr/bin/env python3
"""Materialize local market-data proxy repairs for bounded Wave2 tick gaps.

This pass is intentionally read-only. It searches local package/worktree data,
uses M1 and quarantined tick rows only inside their evidence class, and refuses
to promote proxy coverage into exact redacted_account tick truth or runtime intent.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pyarrow.parquet as pq


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

PACKAGE_ROOT = Path("/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04")
INTEGRATION_ROOT = Path("/Users/borr/Documents/gtos/repo/ai-trading-agent")
MT5_BASE = Path(
    "/Users/borr/Library/Application Support/net.metaquotes.wine.metatrader5/"
    "drive_c/Program Files/MetaTrader 5/Bases"
)

TICK_ROOTS = [
    PACKAGE_ROOT / "emergency_hard_halt_evidence/data/ticks/redacted_account_live_bee34003",
    INTEGRATION_ROOT / "data/ticks/redacted_account_live_bee34003",
    REPO_ROOT / "data/ticks/redacted_account_live_bee34003",
]
M1_ROOTS = [
    PACKAGE_ROOT / "emergency_hard_halt_evidence/data/m1/redacted_account_live_bee34003",
    INTEGRATION_ROOT / "data/m1/redacted_account_live_bee34003",
    REPO_ROOT / "data/m1/redacted_account_live_bee34003",
]

THRESHOLDS = [-1.0, 0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0]


def route_path(name: str) -> Path:
    return ROUTE_DIR / name


def route_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int | None:
    if path.suffix != ".jsonl":
        return None
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def parse_dt(value: Any) -> datetime | None:
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


def date_range(start: datetime, end: datetime) -> list[str]:
    day = start.date()
    out: list[str] = []
    while day <= end.date():
        out.append(day.isoformat())
        day += timedelta(days=1)
    return out


def symbol_aliases(row: dict[str, Any]) -> list[str]:
    tick_symbol = row.get("tick_symbol") or row.get("symbol")
    symbol = row.get("symbol")
    aliases = [str(tick_symbol)]
    if symbol and symbol not in aliases:
        aliases.append(str(symbol))
    if symbol == "US30" and "US30_cash" not in aliases:
        aliases.insert(0, "US30_cash")
    return [alias for alias in aliases if alias and alias != "None"]


def file_meta(path: Path) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
    }


def load_tick(path: Path) -> tuple[pd.DataFrame | None, str]:
    try:
        table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
        frame = table.to_pandas()
        frame = frame.dropna(subset=["ts_utc", "bid", "ask"]).sort_values("ts_utc")
        return frame, "loaded"
    except Exception as exc:  # noqa: BLE001 - artifact records exact parse failure.
        return None, f"parse_error:{exc}"


def load_m1(path: Path) -> tuple[pd.DataFrame | None, str]:
    try:
        frame = pd.read_csv(path)
        frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
        frame = frame.dropna(subset=["time_utc", "open", "high", "low", "close"]).sort_values("time_utc")
        return frame, "loaded"
    except Exception as exc:  # noqa: BLE001 - artifact records exact parse failure.
        return None, f"parse_error:{exc}"


def direction(side: str) -> str:
    side = side.upper()
    if side in {"LONG", "BUY"}:
        return "long"
    if side in {"SHORT", "SELL"}:
        return "short"
    return "unknown"


def r_value(price: float, entry: float, risk: float, side: str) -> float:
    if direction(side) == "short":
        return (entry - price) / risk
    return (price - entry) / risk


def tick_segment_metrics(
    frame: pd.DataFrame,
    start: datetime,
    end: datetime,
    side: str,
    entry: float,
    risk: float,
    source_label: str,
) -> dict[str, Any]:
    mask = (frame["ts_utc"] >= pd.Timestamp(start)) & (frame["ts_utc"] <= pd.Timestamp(end))
    subset = frame.loc[mask].copy()
    if subset.empty:
        return {"source_label": source_label, "interval_rows": 0, "parse_status": "loaded_no_rows_in_interval"}
    price_col = "ask" if direction(side) == "short" else "bid"
    prices = subset[price_col]
    times = subset["ts_utc"]
    if direction(side) == "short":
        mfe_price = float(prices.min())
        mae_price = float(prices.max())
        mfe_time = times.loc[prices.idxmin()]
        mae_time = times.loc[prices.idxmax()]
    else:
        mfe_price = float(prices.max())
        mae_price = float(prices.min())
        mfe_time = times.loc[prices.idxmax()]
        mae_time = times.loc[prices.idxmin()]
    terminal_price = float(prices.iloc[-1])
    first_passage: dict[str, str | None] = {}
    for threshold in THRESHOLDS:
        if direction(side) == "short":
            target_price = entry - threshold * risk
            condition = prices <= target_price if threshold >= 0 else prices >= target_price
        else:
            target_price = entry + threshold * risk
            condition = prices >= target_price if threshold >= 0 else prices <= target_price
        hit = subset.loc[condition]
        first_passage[str(threshold)] = iso(hit["ts_utc"].iloc[0]) if not hit.empty else None
    return {
        "source_label": source_label,
        "interval_rows": int(len(subset)),
        "interval_first_time_utc": iso(subset["ts_utc"].iloc[0]),
        "interval_last_time_utc": iso(subset["ts_utc"].iloc[-1]),
        "price_basis": price_col,
        "mfe_price": mfe_price,
        "mae_price": mae_price,
        "mfe_r": round(r_value(mfe_price, entry, risk, side), 6),
        "mae_r": round(r_value(mae_price, entry, risk, side), 6),
        "mfe_time_utc": iso(mfe_time),
        "mae_time_utc": iso(mae_time),
        "terminal_price": terminal_price,
        "terminal_r": round(r_value(terminal_price, entry, risk, side), 6),
        "first_passage_r_threshold_time_utc": first_passage,
        "parse_status": "loaded",
    }


def m1_segment_metrics(
    frame: pd.DataFrame,
    start: datetime,
    end: datetime,
    side: str,
    entry: float,
    risk: float,
    source_label: str,
    exclude_until: datetime | None = None,
) -> dict[str, Any]:
    mask = (frame["time_utc"] >= pd.Timestamp(start)) & (frame["time_utc"] <= pd.Timestamp(end))
    if exclude_until is not None:
        mask &= frame["time_utc"] > pd.Timestamp(exclude_until)
    subset = frame.loc[mask].copy()
    if subset.empty:
        return {"source_label": source_label, "interval_rows": 0, "parse_status": "loaded_no_rows_in_interval"}
    if direction(side) == "short":
        mfe_idx = subset["low"].idxmin()
        mae_idx = subset["high"].idxmax()
        mfe_price = float(subset.loc[mfe_idx, "low"])
        mae_price = float(subset.loc[mae_idx, "high"])
    else:
        mfe_idx = subset["high"].idxmax()
        mae_idx = subset["low"].idxmin()
        mfe_price = float(subset.loc[mfe_idx, "high"])
        mae_price = float(subset.loc[mae_idx, "low"])
    terminal_price = float(subset["close"].iloc[-1])
    first_passage: dict[str, str | None] = {}
    for threshold in THRESHOLDS:
        if direction(side) == "short":
            target_price = entry - threshold * risk
            condition = subset["low"] <= target_price if threshold >= 0 else subset["high"] >= target_price
        else:
            target_price = entry + threshold * risk
            condition = subset["high"] >= target_price if threshold >= 0 else subset["low"] <= target_price
        hit = subset.loc[condition]
        first_passage[str(threshold)] = iso(hit["time_utc"].iloc[0]) if not hit.empty else None
    return {
        "source_label": source_label,
        "interval_rows": int(len(subset)),
        "interval_first_time_utc": iso(subset["time_utc"].iloc[0]),
        "interval_last_time_utc": iso(subset["time_utc"].iloc[-1]),
        "price_basis": "m1_ohlc_bar_proxy_no_bid_ask_ordering",
        "mfe_price": mfe_price,
        "mae_price": mae_price,
        "mfe_r": round(r_value(mfe_price, entry, risk, side), 6),
        "mae_r": round(r_value(mae_price, entry, risk, side), 6),
        "mfe_time_utc": iso(subset.loc[mfe_idx, "time_utc"]),
        "mae_time_utc": iso(subset.loc[mae_idx, "time_utc"]),
        "terminal_price": terminal_price,
        "terminal_r": round(r_value(terminal_price, entry, risk, side), 6),
        "first_passage_r_threshold_time_utc": first_passage,
        "parse_status": "loaded",
    }


def find_first_file(roots: list[Path], aliases: list[str], date: str, suffix: str) -> Path | None:
    for root in roots:
        for alias in aliases:
            path = root / alias / f"{date}{suffix}"
            if path.exists():
                return path
    return None


def find_quarantine_files(aliases: list[str], date: str) -> list[Path]:
    out: list[Path] = []
    for root in TICK_ROOTS:
        for alias in aliases:
            qdir = root / alias / "_corrupt_quarantine"
            if qdir.exists():
                out.extend(sorted(qdir.glob(f"{date}.*.corrupt.parquet")))
    return out


def summarize_segments(segments: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [seg for seg in segments if seg.get("interval_rows", 0)]
    if not usable:
        return {
            "proxy_path_status": "no_local_proxy_rows_in_entry_exit_interval",
            "mfe_r": None,
            "mae_r": None,
            "terminal_r": None,
            "first_segment_time_utc": None,
            "last_segment_time_utc": None,
        }
    mfe_seg = max(usable, key=lambda seg: seg.get("mfe_r") if seg.get("mfe_r") is not None else -10**9)
    mae_seg = min(usable, key=lambda seg: seg.get("mae_r") if seg.get("mae_r") is not None else 10**9)
    last_seg = max(usable, key=lambda seg: seg.get("interval_last_time_utc") or "")
    first_seg = min(usable, key=lambda seg: seg.get("interval_first_time_utc") or "9999")
    return {
        "proxy_path_status": "local_proxy_rows_materialized",
        "mfe_r": mfe_seg.get("mfe_r"),
        "mfe_time_utc": mfe_seg.get("mfe_time_utc"),
        "mfe_source_label": mfe_seg.get("source_label"),
        "mae_r": mae_seg.get("mae_r"),
        "mae_time_utc": mae_seg.get("mae_time_utc"),
        "mae_source_label": mae_seg.get("source_label"),
        "terminal_r": last_seg.get("terminal_r"),
        "terminal_time_utc": last_seg.get("interval_last_time_utc"),
        "terminal_source_label": last_seg.get("source_label"),
        "first_segment_time_utc": first_seg.get("interval_first_time_utc"),
        "last_segment_time_utc": last_seg.get("interval_last_time_utc"),
        "segment_labels_used": [seg.get("source_label") for seg in usable],
        "segment_count_used": len(usable),
    }


def coverage_status(start: datetime, end: datetime, summary: dict[str, Any], has_exact_full_tick: bool) -> tuple[str, list[str]]:
    first = parse_dt(summary.get("first_segment_time_utc"))
    last = parse_dt(summary.get("last_segment_time_utc"))
    gaps: list[str] = []
    if first is None:
        gaps.append("no_proxy_start")
    elif first > start + timedelta(minutes=1):
        gaps.append(f"entry_to_first_proxy_gap_minutes={round((first - start).total_seconds() / 60.0, 3)}")
    if last is None:
        gaps.append("no_proxy_end")
    elif last < end - timedelta(minutes=1):
        gaps.append(f"last_proxy_to_exit_gap_minutes={round((end - last).total_seconds() / 60.0, 3)}")
    if has_exact_full_tick:
        return "exact_full_tick_window_already_available", gaps
    if not gaps:
        return "full_entry_exit_proxy_coverage_not_exact_tick", [
            "exact_full_redacted_account_tick_export_still_required_for_full_tick_claims"
        ]
    return "partial_proxy_or_tick_coverage_remaining_source_gap", gaps + [
        "exact_full_redacted_account_tick_export_still_required_for_full_tick_claims"
    ]


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    recovery_rows = read_jsonl(route_path("WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl"))
    tick_repair_rows = read_jsonl(route_path("WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl"))
    tick_by_key = {
        (str(row.get("broker_position_id")), str(row.get("trade_id"))): row
        for row in tick_repair_rows
    }

    rows: list[dict[str, Any]] = []
    source_inventory: list[dict[str, Any]] = []
    for recovery in recovery_rows:
        key = (str(recovery.get("broker_position_id")), str(recovery.get("trade_id")))
        base = tick_by_key.get(key, {})
        start = parse_dt(recovery.get("entry_time_utc"))
        end = parse_dt(recovery.get("close_time_utc"))
        entry = safe_float(base.get("entry_price"))
        risk = safe_float(base.get("risk_distance_for_r"))
        side = str(base.get("side") or "")
        aliases = symbol_aliases(recovery)
        if start is None or end is None or entry is None or risk is None or risk <= 0 or direction(side) == "unknown":
            rows.append(
                {
                    "row_id": f"market_data_gap_proxy_repair:{recovery.get('broker_position_id')}:{recovery.get('trade_id')}",
                    "broker_position_id": recovery.get("broker_position_id"),
                    "trade_id": recovery.get("trade_id"),
                    "symbol": recovery.get("symbol"),
                    "repair_status": "input_geometry_or_time_missing_no_proxy_computed",
                    "source_paths": [],
                    "result_use_status": "market_data_recovery_proxy_audit_not_runtime_intent",
                }
            )
            continue

        segments: list[dict[str, Any]] = []
        source_files: list[dict[str, Any]] = []
        tick_segment_latest: datetime | None = None

        for date in date_range(start, end):
            tick_path = find_first_file(TICK_ROOTS, aliases, date, ".parquet")
            if tick_path is not None:
                frame, status = load_tick(tick_path)
                meta = file_meta(tick_path)
                meta.update({"source_type": "redacted_account_tick_parquet", "parse_status": status})
                source_files.append(meta)
                source_inventory.append(meta)
                if frame is not None:
                    metric = tick_segment_metrics(
                        frame, start, end, side, entry, risk, "redacted_account_tick_parquet"
                    )
                    metric["source_path"] = tick_path.as_posix()
                    segments.append(metric)
                    if metric.get("interval_last_time_utc"):
                        latest = parse_dt(metric["interval_last_time_utc"])
                        if latest and (tick_segment_latest is None or latest > tick_segment_latest):
                            tick_segment_latest = latest

            for qpath in find_quarantine_files(aliases, date):
                frame, status = load_tick(qpath)
                meta = file_meta(qpath)
                meta.update({"source_type": "readable_quarantined_tick_parquet", "parse_status": status})
                source_files.append(meta)
                source_inventory.append(meta)
                if frame is not None:
                    metric = tick_segment_metrics(
                        frame, start, end, side, entry, risk, "readable_quarantined_tick_parquet"
                    )
                    metric["source_path"] = qpath.as_posix()
                    segments.append(metric)
                    if metric.get("interval_last_time_utc"):
                        latest = parse_dt(metric["interval_last_time_utc"])
                        if latest and (tick_segment_latest is None or latest > tick_segment_latest):
                            tick_segment_latest = latest

            m1_path = find_first_file(M1_ROOTS, aliases, date, ".csv")
            if m1_path is not None:
                frame, status = load_m1(m1_path)
                meta = file_meta(m1_path)
                meta.update({"source_type": "redacted_account_m1_bar_proxy_csv", "parse_status": status})
                source_files.append(meta)
                source_inventory.append(meta)
                if frame is not None:
                    metric = m1_segment_metrics(
                        frame,
                        start,
                        end,
                        side,
                        entry,
                        risk,
                        "redacted_account_m1_bar_proxy",
                        exclude_until=tick_segment_latest,
                    )
                    metric["source_path"] = m1_path.as_posix()
                    segments.append(metric)

        summary = summarize_segments(segments)
        exact_full_tick = bool(base.get("full_tick_window_covered") is True)
        repair_status, remaining_gaps = coverage_status(start, end, summary, exact_full_tick)
        if recovery.get("recovery_status") == "mt5_ftmo_tick_cache_present_requires_parser_or_export":
            remaining_gaps.append("ftmo_mt5_ticks_dat_present_but_unparsed_readonly_export_or_parser_required")
        rows.append(
            {
                "row_id": f"market_data_gap_proxy_repair:{recovery.get('broker_position_id')}:{recovery.get('trade_id')}",
                "broker_position_id": recovery.get("broker_position_id"),
                "trade_id": recovery.get("trade_id"),
                "candidate_id": base.get("candidate_id"),
                "symbol": recovery.get("symbol"),
                "tick_symbol": recovery.get("tick_symbol"),
                "side": side,
                "entry_time_utc": recovery.get("entry_time_utc"),
                "close_time_utc": recovery.get("close_time_utc"),
                "entry_price": entry,
                "stop_loss_for_r": base.get("stop_loss_for_r"),
                "risk_distance_for_r": risk,
                "previous_tick_repair_status": recovery.get("previous_tick_repair_status"),
                "previous_mt5_recovery_status": recovery.get("recovery_status"),
                "repair_status": repair_status,
                "evidence_class": "proxy_market_data_repair_not_exact_tick_not_runtime_intent",
                "source_operation": "read_only_local_package_m1_tick_quarantine_and_mt5_inventory",
                "source_paths": [item["path"] for item in source_files],
                "source_files": source_files,
                "segment_metrics": segments,
                "best_available_proxy_metrics": summary,
                "previous_tick_repair_metrics": {
                    "tick_mfe_r": base.get("tick_mfe_r"),
                    "tick_mae_r": base.get("tick_mae_r"),
                    "terminal_tick_r": base.get("terminal_tick_r"),
                    "tick_count": base.get("tick_count"),
                    "tick_window_first_time_utc": base.get("tick_window_first_time_utc"),
                    "tick_window_last_time_utc": base.get("tick_window_last_time_utc"),
                    "full_tick_window_covered": base.get("full_tick_window_covered"),
                    "usable_for_full_first_passage": base.get("usable_for_full_first_passage"),
                },
                "remaining_gaps": sorted(set(remaining_gaps)),
                "result_use_status": "market_data_recovery_proxy_audit_not_broker_real_path_not_runtime_intent",
                "same_evidence_class_repairs_attempted": [
                    "searched_package_redacted_account_tick_parquet",
                    "searched_readable_corrupt_quarantine_tick_parquet",
                    "searched_package_and_integration_redacted_account_m1_csv",
                    "preserved_mt5_ticks_dat_parser_or_export_requirement_where_present",
                ],
                "v4_requirement_id": "market_data_source_recovery_and_proxy_label_contract",
                "owning_wave3_lane": "historical_replay_digital_twin_v4",
                "implementation_decision": (
                    "allow proxy-labeled replay diagnostics only; require exact full tick export/parser "
                    "before full first-passage or broker-real path claims"
                ),
            }
        )

    summary_payload = {
        "generated_at_utc": GENERATED_AT,
        "row_count": len(rows),
        "repair_status_counts": dict(Counter(row.get("repair_status") for row in rows)),
        "source_file_count": len({src["path"] for src in source_inventory}),
        "exact_full_tick_claims_created": 0,
        "claim_boundary": {
            "redacted_account_tick_parquet": "source-bound tick only for covered interval; not runtime intent",
            "readable_quarantined_tick_parquet": "quarantined tick proxy; usable only with explicit quarantine label",
            "redacted_account_m1_bar_proxy": "M1 OHLC proxy with no bid/ask and no intra-bar order",
            "mt5_ticks_dat": "read-only FTMO cache inventory only until parser/export materializes exact ticks",
        },
    }
    return rows, summary_payload, source_inventory


def append_unique_by_key(rows: list[dict[str, Any]], new_rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen = {row.get(key) for row in new_rows}
    return [row for row in rows if row.get(key) not in seen] + new_rows


def update_questions(proxy_count: int) -> None:
    question_ids = {"W2Q_CAPTURE_GAPS", "W2Q_ENTRY_PATH_MFE_MAE", "W2Q_VALIDATION_REPLAY"}
    for name in [
        "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl",
        "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
        "WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl",
        "WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl",
    ]:
        path = route_path(name)
        rows = []
        for row in read_jsonl(path):
            if row.get("question_id") in question_ids:
                actions = list(row.get("pursuit_actions") or [])
                if "wave2_market_data_gap_proxy_repair_pass" not in actions:
                    actions.append("wave2_market_data_gap_proxy_repair_pass")
                row["pursuit_actions"] = actions
                artifacts = str(row.get("result_artifact") or "")
                if "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl" not in artifacts:
                    row["result_artifact"] = (
                        artifacts + ";WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl"
                        if artifacts
                        else "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl"
                    )
                row["same_evidence_class_repairs_attempted"] = list(
                    dict.fromkeys(
                        list(row.get("same_evidence_class_repairs_attempted") or [])
                        + ["local_package_tick_m1_quarantine_proxy_repair"]
                    )
                )
                row["proxy_repair_rows_materialized"] = proxy_count
            rows.append(row)
        write_jsonl(path, rows)


def update_blockers(proxy_count: int) -> None:
    rows = [
        row
        for row in read_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"))
        if row.get("blocker_id") != "wave2_mt5_readonly_tick_gap_recovery"
    ]
    rows.append(
        {
            "blocker_id": "wave2_mt5_readonly_tick_gap_recovery",
            "source_path": (
                "WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl;"
                "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl"
            ),
            "evidence_class": "recoverable_market_data_or_proxy_source_gap_not_runtime_intent",
            "missing_file_path_field_source": (
                "exact full redacted_account tick windows for bounded partial rows; proxy local tick/M1/quarantine "
                "coverage is materialized but cannot become exact tick truth"
            ),
            "searched_roots_or_repairs": [
                "/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04/emergency_hard_halt_evidence/data/ticks/redacted_account_live_bee34003",
                "/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04/emergency_hard_halt_evidence/data/m1/redacted_account_live_bee34003",
                "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/ticks/redacted_account_live_bee34003",
                "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/m1/redacted_account_live_bee34003",
                MT5_BASE.as_posix(),
            ],
            "reason_repair_not_complete_in_initial_spine": (
                "local package/M1/quarantine data now supplies proxy repair rows, including full-window proxy "
                "coverage for EURJPY 242383463; exact full tick truth still requires read-only export/parser/source pull"
            ),
            "owner_access_source_capture_requirement": (
                "read-only exact tick export or parser for listed windows before promoting path claims to exact; "
                "do not mutate broker account/orders/history/deals/positions"
            ),
            "downstream_lane": "historical_replay_digital_twin_v4",
            "status": "proxy_repair_materialized_exact_tick_export_still_required",
            "row_count": proxy_count,
        }
    )
    write_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"), rows)


def update_source_ledgers(source_inventory: list[dict[str, Any]]) -> None:
    searched_rows = read_jsonl(route_path("WAVE2_SEARCHED_ROOT_LEDGER.jsonl"))
    new_roots = []
    for root in TICK_ROOTS + M1_ROOTS + [MT5_BASE]:
        file_count = 0
        if root.exists():
            file_count = sum(1 for item in root.rglob("*") if item.is_file())
        new_roots.append(
            {
                "generated_at_utc": GENERATED_AT,
                "root": root.as_posix(),
                "exists": root.exists(),
                "file_count": file_count,
                "search_method": "wave2_market_data_gap_proxy_repair_targeted_local_root_scan",
                "search_status": "searched_for_bounded_tick_gap_proxy_repair",
                "evidence_class": "read_only_local_market_data_source_search",
            }
        )
    write_jsonl(route_path("WAVE2_SEARCHED_ROOT_LEDGER.jsonl"), append_unique_by_key(searched_rows, new_roots, "root"))

    inv_rows = read_jsonl(route_path("WAVE2_SOURCE_INVENTORY.jsonl"))
    new_inv: list[dict[str, Any]] = []
    for src in source_inventory:
        new_inv.append(
            {
                "path": src["path"],
                "kind": "file",
                "exists": src["exists"],
                "size_bytes": src["size_bytes"],
                "sha256": src["sha256"],
                "jsonl_rows": None,
                "inventory_scope": "wave2_market_data_gap_proxy_repair",
                "evidence_class": src.get("source_type"),
                "source_capture_status": src.get("parse_status"),
                "consume_status": "consumed_for_proxy_repair_or_source_gap_boundary",
            }
        )
    write_jsonl(route_path("WAVE2_SOURCE_INVENTORY.jsonl"), append_unique_by_key(inv_rows, new_inv, "path"))


def update_intelligence(proxy_count: int, summary: dict[str, Any]) -> None:
    rows = read_jsonl(route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl"))
    new_rows = [
        {
            "intelligence_id": "W2INTEL-CONT-MKT-DATA-PROXY-001",
            "origin": "wave2_market_data_gap_proxy_repair",
            "finding": (
                f"Local package tick, readable quarantine tick, and M1 roots were searched for {proxy_count} "
                "bounded market-data gaps; proxy path rows are now materialized without promoting them to exact tick truth."
            ),
            "source_paths": [
                "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl",
                "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_SUMMARY.json",
            ],
            "evidence_class": "proxy_market_data_repair_not_exact_tick_not_runtime_intent",
            "downstream_question_ids": ["W2Q_CAPTURE_GAPS", "W2Q_ENTRY_PATH_MFE_MAE", "W2Q_VALIDATION_REPLAY"],
            "status": "accepted_proxy_repair_boundary_materialized",
            "v4_requirement_id": "market_data_source_recovery_and_proxy_label_contract",
            "repair_status_counts": summary.get("repair_status_counts"),
        }
    ]
    write_jsonl(route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl"), append_unique_by_key(rows, new_rows, "intelligence_id"))


def update_summary_artifacts(proxy_count: int, summary: dict[str, Any]) -> None:
    coverage = read_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"))
    materialization = dict(coverage.get("continuation_materialization") or {})
    materialization.update(
        {
            "generated_at_utc": GENERATED_AT,
            "market_data_gap_proxy_repair_rows": proxy_count,
            "market_data_gap_proxy_repair_status_counts": summary.get("repair_status_counts"),
            "status": "same_evidence_class_continuation_materialized_not_wave2_complete",
        }
    )
    coverage["continuation_materialization"] = materialization
    coverage["coverage_gap"] = (
        "Wave2 now includes row-level market/system, selector repair, allocator replay, zero-trade rank, "
        "final-say join, MT5 read-only source recovery, and local proxy market-data repair ledgers; remaining "
        "completion still requires full prompt pack, sealed validation, exact tick export/parser where needed, "
        "original runtime packet capture/prospective implementation, and non-generatable lifecycle fields."
    )
    write_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"), coverage)

    final_state = read_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json"))
    counts = dict(final_state.get("continuation_materialization_counts") or {})
    counts["market_data_gap_proxy"] = proxy_count
    final_state["continuation_materialization_counts"] = counts
    final_state["generated_at_utc"] = GENERATED_AT
    truths = list(final_state.get("truths") or [])
    truth = (
        "bounded missing market-data rows now have proxy repair materialized from package tick/M1/quarantine sources; "
        "exact full tick truth is still separately required before full path claims"
    )
    if truth not in truths:
        truths.append(truth)
    final_state["truths"] = truths
    gaps = [
        gap
        for gap in list(final_state.get("blocking_gaps") or [])
        if gap != "exact missing market tick windows require read-only source export or proxy-labeled replay before full path claims"
    ]
    new_gap = "exact full tick export/parser remains required for bounded market-data gaps before full first-passage claims"
    if new_gap not in gaps:
        gaps.append(new_gap)
    final_state["blocking_gaps"] = gaps
    final_state["wave3_prompt_pack_allowed"] = False
    final_state["status"] = "not_final_incomplete_master_state_continuation_materialized"
    write_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json"), final_state)


def update_markdown(proxy_count: int, summary: dict[str, Any]) -> None:
    completion_path = route_path("WAVE2_COMPLETION_AUDIT.md")
    completion = completion_path.read_text(encoding="utf-8")
    bullet = (
        f"- `WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl` materializes {proxy_count} local proxy repair rows "
        "from package tick, readable quarantined tick, package/integration M1, and MT5 cache inventory. It improves "
        "the no-data state without promoting proxy/M1/quarantined data into exact full tick truth.\n"
    )
    if "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl" not in completion:
        completion = completion.replace(
            "Still not complete:\n\n",
            bullet + "\nStill not complete:\n\n",
        )
    completion = completion.replace(
        "- Sealed validation/digital-twin execution is not complete.\n",
        "- Sealed validation/digital-twin execution is not complete.\n"
        "- Exact full tick export/parser remains required for bounded market-data gaps before full first-passage claims.\n",
    )
    completion_path.write_text(completion, encoding="utf-8")

    saturation_path = route_path("WAVE2_SATURATION_SELF_RED_TEAM.md")
    saturation = saturation_path.read_text(encoding="utf-8")
    bullet2 = (
        f"- Missing market-data rows were pushed beyond MT5 inventory: {proxy_count} proxy repair rows now preserve "
        "package tick, readable quarantine tick, M1 proxy, and remaining exact-export/parser requirements.\n"
    )
    if "Missing market-data rows were pushed beyond MT5 inventory" not in saturation:
        saturation = saturation.replace("Remaining skeptical rejection points:\n\n", bullet2 + "\nRemaining skeptical rejection points:\n\n")
    saturation = saturation.replace(
        "- MT5 cache discovery is read-only source inventory, not broker-real redacted_account tick truth unless exact exported ticks are produced and hashed.\n",
        "- MT5 cache discovery and local proxy repair are read-only source inventory/proxy diagnostics, not broker-real full tick truth unless exact exported ticks are produced and hashed.\n",
    )
    saturation_path.write_text(saturation, encoding="utf-8")


def regenerate_manifest() -> None:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        files.append(
            {
                "path": route_rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "jsonl_rows": row_count(path),
            }
        )
    write_json(
        route_path("WAVE2_OUTPUT_MANIFEST.json"),
        {
            "generated_at_utc": GENERATED_AT,
            "completion_status": "continuation_materialized_not_complete",
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> int:
    rows, summary, source_inventory = build_rows()
    proxy_count = write_jsonl(route_path("WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl"), rows)
    write_json(route_path("WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_SUMMARY.json"), summary)
    update_questions(proxy_count)
    update_blockers(proxy_count)
    update_source_ledgers(source_inventory)
    update_intelligence(proxy_count, summary)
    update_summary_artifacts(proxy_count, summary)
    update_markdown(proxy_count, summary)
    regenerate_manifest()
    print(json.dumps({"ok": True, "rows": proxy_count, "summary": summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
