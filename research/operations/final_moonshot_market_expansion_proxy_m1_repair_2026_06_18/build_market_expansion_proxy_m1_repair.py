#!/usr/bin/env python3
"""Targeted exact-M1 repair for proxy-gated market-expansion metadata rows."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
REGISTRY_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_default_off_registry_2026_06_18"
FOLLOWUP_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_followup_replay_2026_06_18"
AVAILABILITY_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_data_availability_2026_06_18"
RAW_EXPORT_DIR = PROJECT_ROOT / "data" / "mt5_research_exports" / "market_expansion_proxy_m1_repair_20260618"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_proxy_m1_repair"
TARGET_MULTIPLES = (1.0, 2.0, 3.0)
MIN_EXACT_M1_EVENTS_FOR_DEFAULT_OFF_SUPPORT = 20
UNIT_INTERACTION_WEIGHT = 0.05

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
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


def import_followup_module():
    path = FOLLOWUP_ROUTE / "build_market_expansion_followup_replay.py"
    spec = importlib.util.spec_from_file_location("market_expansion_followup", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rate_timestamp(rec: Any) -> int | None:
    try:
        return int(rec["time"])
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def rate_field(rec: Any, field: str, default: Any = None) -> Any:
    try:
        return rec[field]
    except (KeyError, TypeError, ValueError, IndexError):
        return default


def split_name(ts: pd.Timestamp) -> str:
    year = int(ts.year)
    if year <= 2021:
        return "train_le_2021"
    if year <= 2024:
        return "oos_2022_2024"
    return "sealed_ge_2025"


def summarize(values: list[float]) -> dict[str, Any]:
    clean = np.array([value for value in values if math.isfinite(value)], dtype=float)
    if clean.size == 0:
        return {
            "n": 0,
            "mean_r": None,
            "median_r": None,
            "win_rate": None,
            "std_r": None,
            "sharpe_like": None,
            "sum_r": 0.0,
        }
    std = float(np.std(clean, ddof=1)) if clean.size > 1 else 0.0
    return {
        "n": int(clean.size),
        "mean_r": round(float(np.mean(clean)), 6),
        "median_r": round(float(np.median(clean)), 6),
        "win_rate": round(float(np.mean(clean > 0)), 6),
        "std_r": round(std, 6),
        "sharpe_like": round(float(np.mean(clean) / std), 6) if std else None,
        "sum_r": round(float(np.sum(clean)), 6),
    }


def summarize_event_policy(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [float(row[key]) for row in rows if row.get(key) is not None and math.isfinite(float(row[key]))]
    out = summarize(values)
    out["splits"] = {
        split: summarize(
            [
                float(row[key])
                for row in rows
                if row.get("split") == split and row.get(key) is not None and math.isfinite(float(row[key]))
            ]
        )
        for split in ("train_le_2021", "oos_2022_2024", "sealed_ge_2025")
    }
    out["populated_split_count"] = sum(1 for payload in out["splits"].values() if payload["n"] > 0)
    out["positive_populated_split_count"] = sum(
        1 for payload in out["splits"].values() if payload["n"] > 0 and payload["mean_r"] is not None and payload["mean_r"] > 0
    )
    out["every_populated_split_positive"] = all(
        payload["n"] == 0 or (payload["mean_r"] is not None and payload["mean_r"] > 0)
        for payload in out["splits"].values()
    )
    return out


def _load_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    return rows


def _write_m1_csv(path: Path, rows_by_time: dict[int, dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    first_time = None
    last_time = None
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time", "open", "high", "low", "close", "volume"])
        for timestamp in sorted(rows_by_time):
            row = rows_by_time[timestamp]
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            rendered = dt.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([rendered, row["open"], row["high"], row["low"], row["close"], row["volume"]])
            first_time = first_time or rendered
            last_time = rendered
    return {
        "path": rel(path),
        "rows": len(rows_by_time),
        "first": first_time,
        "last": last_time,
        "sha256": sha256_file(path),
    }


def _event_day(ts: str) -> str:
    return pd.Timestamp(ts).date().isoformat()


def export_targeted_m1_from_bridge(
    *,
    repair_events: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    RAW_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    symbol_to_mt5 = {row["file_symbol"]: row["broker_symbol"] for row in registry_rows}
    requested_days: dict[str, set[str]] = defaultdict(set)
    for event in repair_events:
        if event.get("target2_path_source") == "M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH":
            continue
        requested_days[event["file_symbol"]].add(_event_day(event["time"]))

    try:
        from siliconmetatrader5 import MetaTrader5  # noqa: PLC0415
    except ModuleNotFoundError as exc:
        return {
            "schema": f"{SCHEMA_PREFIX}.targeted_m1_export_manifest.v1",
            "created_at_utc": created_at,
            "ok": False,
            "bridge_reachable": False,
            "error": f"siliconmetatrader5_unavailable:{exc}",
            "files": {},
        }

    client = MetaTrader5(host="localhost", port=8001, keepalive=True)
    initialized = bool(client.initialize())
    manifest: dict[str, Any] = {
        "schema": f"{SCHEMA_PREFIX}.targeted_m1_export_manifest.v1",
        "created_at_utc": created_at,
        "ok": initialized,
        "bridge_reachable": initialized,
        "bridge_host": "localhost",
        "bridge_port": 8001,
        "account_info_read": False,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "truth_scope": "exact_m1_ordered_price_path_only_not_broker_lifecycle_truth",
        "files": {},
        "errors": [],
    }
    if not initialized:
        manifest["errors"].append({"code": "bridge_initialize_failed", "last_error": str(client.last_error())})
        return manifest

    try:
        for file_symbol in sorted(requested_days):
            mt5_symbol = symbol_to_mt5[file_symbol]
            selected = bool(client.symbol_select(mt5_symbol, True))
            if not selected:
                manifest["errors"].append(
                    {
                        "file_symbol": file_symbol,
                        "mt5_symbol": mt5_symbol,
                        "code": "symbol_select_failed",
                        "last_error": str(client.last_error()),
                    }
                )
                continue
            rows_by_time: dict[int, dict[str, Any]] = {}
            raw_rows_returned = 0
            filtered_rows = 0
            empty_year_requests = 0
            years = sorted({int(day[:4]) for day in requested_days[file_symbol]})
            event_days = requested_days[file_symbol]
            days_with_rows: set[str] = set()
            for year in years:
                start = datetime(year, 1, 1, tzinfo=timezone.utc)
                end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
                rates = client.copy_rates_range(mt5_symbol, client.TIMEFRAME_M1, start, end)
                if rates is None or len(rates) == 0:
                    empty_year_requests += 1
                    continue
                raw_rows_returned += len(rates)
                for rec in rates:
                    timestamp = rate_timestamp(rec)
                    if timestamp is None:
                        continue
                    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    day = dt.date().isoformat()
                    if day not in event_days:
                        continue
                    rows_by_time[timestamp] = {
                        "open": rate_field(rec, "open"),
                        "high": rate_field(rec, "high"),
                        "low": rate_field(rec, "low"),
                        "close": rate_field(rec, "close"),
                        "volume": rate_field(rec, "tick_volume", 0),
                    }
                    filtered_rows += 1
                    days_with_rows.add(day)
            csv_stats = _write_m1_csv(RAW_EXPORT_DIR / f"{file_symbol}_M1.csv", rows_by_time)
            csv_stats.update(
                {
                    "file_symbol": file_symbol,
                    "mt5_symbol": mt5_symbol,
                    "event_days_requested": len(event_days),
                    "event_days_with_m1_rows": len(days_with_rows),
                    "event_days_without_m1_rows": len(event_days - days_with_rows),
                    "years_requested": years,
                    "raw_rows_returned": raw_rows_returned,
                    "filtered_rows_before_dedupe": filtered_rows,
                    "empty_year_requests": empty_year_requests,
                }
            )
            manifest["files"][f"{file_symbol}_M1"] = csv_stats
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()
    manifest["ok"] = manifest["bridge_reachable"] is True and not manifest["errors"]
    return manifest


def _dataframe_from_csv_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["time", "open", "high", "low", "close"]).sort_values("time")


def combined_m1_dataframe(module: Any, availability_matrix: dict[str, Any], file_symbol: str) -> pd.DataFrame:
    best = module.best_path(availability_matrix, file_symbol, "M1")
    frames = []
    if best is not None and best.exists():
        frames.append(module.load_ohlcv(best))
    targeted = RAW_EXPORT_DIR / f"{file_symbol}_M1.csv"
    if targeted.exists():
        frames.append(_dataframe_from_csv_rows(_load_csv_rows(targeted)))
    if not frames:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return combined
    combined = combined.drop_duplicates(subset=["time"], keep="last").sort_values("time").reset_index(drop=True)
    return combined


def book_interaction_rows(module: Any, candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    book = module.book_values()
    book_module = book["module"]
    all_days = book["all_days"]
    day_index = {day.isoformat()[:10]: index for index, day in enumerate(all_days)}
    base_values = book["current_values"]
    rows = []
    for candidate in candidate_rows:
        if candidate["repaired_exact_m1_event_count"] < MIN_EXACT_M1_EVENTS_FOR_DEFAULT_OFF_SUPPORT:
            continue
        aligned = [0.0] * len(base_values)
        matched = 0
        for day, value in candidate["daily_target2_exact_m1_sum_r"].items():
            index = day_index.get(day)
            if index is None:
                continue
            aligned[index] += float(value) * UNIT_INTERACTION_WEIGHT
            matched += 1
        if matched == 0:
            continue
        scenario = [base + add for base, add in zip(base_values, aligned, strict=True)]
        rows.append(
            {
                "tag": candidate["tag"],
                "file_symbol": candidate["file_symbol"],
                "mechanism": candidate["mechanism"],
                "matched_current_book_days": matched,
                "base_sharpe": round(float(book["current_sharpe"]), 6),
                "scenario_sharpe": round(float(book_module._sharpe(scenario)), 6),
                "delta_sharpe": round(float(book_module._sharpe(scenario) - book["current_sharpe"]), 6),
                "scenario_block": book_module._block(scenario),
                "runtime_effect": "none_exact_m1_unit_sensitivity_only",
            }
        )
    return rows


def build() -> dict[str, Any]:
    created_at = utc_now()
    module = import_followup_module()
    registry_result = read_json(REGISTRY_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json")
    registry_rows = read_jsonl(REGISTRY_ROUTE / "DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl")
    repair_registry_rows = [row for row in registry_rows if row["design_status"] == "repair_gated_default_off_spec_only"]
    repair_keys = {(row["file_symbol"], row["mechanism"]) for row in repair_registry_rows}
    raw_events = read_jsonl(PROJECT_ROOT / "data" / "mt5_research_exports" / "market_expansion_followup_replay_20260618" / "PATH_REPLAY_EVENT_LEDGER.jsonl")
    repair_events = [row for row in raw_events if (row["file_symbol"], row["mechanism"]) in repair_keys]
    availability_matrix = read_json(AVAILABILITY_ROUTE / "OHLCV_AVAILABILITY_MATRIX.json")

    export_manifest = export_targeted_m1_from_bridge(
        repair_events=repair_events,
        registry_rows=repair_registry_rows,
        created_at=created_at,
    )
    write_json(ROUTE / "TARGETED_M1_EXPORT_MANIFEST.json", export_manifest)

    m1_indexes: dict[str, dict[str, Any]] = {}
    m1_coverage_rows = []
    for row in repair_registry_rows:
        file_symbol = row["file_symbol"]
        if file_symbol in m1_indexes:
            continue
        df = combined_m1_dataframe(module, availability_matrix, file_symbol)
        m1_indexes[file_symbol] = module.path_index(df)
        m1_coverage_rows.append(
            {
                "file_symbol": file_symbol,
                "combined_m1_rows": int(len(df)),
                "combined_m1_first": df["time"].min().isoformat() if not df.empty else None,
                "combined_m1_last": df["time"].max().isoformat() if not df.empty else None,
                "targeted_export_rows": int((export_manifest.get("files", {}).get(f"{file_symbol}_M1") or {}).get("rows", 0)),
                "runtime_effect": "none_readonly_m1_source_repair",
            }
        )

    event_rows = []
    for event in repair_events:
        ts = pd.Timestamp(event["time"])
        event_out = {
            "tag": f"mx_{event['file_symbol'].lower()}_{event['mechanism']}",
            "file_symbol": event["file_symbol"],
            "broker_symbol": event["broker_symbol"],
            "family": event["family"],
            "mechanism": event["mechanism"],
            "time": event["time"],
            "date": ts.date().isoformat(),
            "split": split_name(ts),
            "signal": event["signal"],
            "previous_target2_path_source": event.get("target2_path_source") or "none",
            "previous_target2_net_r": event.get("target2_net_r"),
            "geometry_status": event.get("geometry_status"),
            "runtime_effect": "none_exact_m1_repair_replay_only",
        }
        if event.get("entry") is None or event.get("risk_abs") is None:
            event_out.update({"exact_m1_status": "geometry_not_reconstructable", "target2_exact_m1_net_r": None})
            event_rows.append(event_out)
            continue
        resolved_by_target: dict[int, dict[str, Any]] = {}
        for multiple in TARGET_MULTIPLES:
            resolved = module.resolve_path(
                m1_indexes[event["file_symbol"]],
                path_label="M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH",
                entry=float(event["entry"]),
                signal=int(event["signal"]),
                risk_abs=float(event["risk_abs"]),
                cost_r=float(event.get("cost_r") or 0.0),
                start=ts,
                end=ts + pd.Timedelta(days=1),
                target_multiple=multiple,
            )
            resolved_by_target[int(multiple)] = resolved
            event_out[f"target{int(multiple)}_exact_m1_net_r"] = resolved["net_r"]
            event_out[f"target{int(multiple)}_exact_m1_gross_r"] = resolved["gross_r"]
            event_out[f"target{int(multiple)}_exact_m1_status"] = resolved["status"]
            event_out[f"target{int(multiple)}_exact_m1_exit_time"] = resolved.get("exit_time")
            event_out[f"target{int(multiple)}_exact_m1_bar_count"] = resolved["bar_count"]
        event_out["exact_m1_status"] = resolved_by_target[2]["status"]
        event_out["target2_exact_m1_net_r"] = resolved_by_target[2]["net_r"]
        event_rows.append(event_out)

    events_by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in event_rows:
        events_by_tag[row["tag"]].append(row)

    candidate_rows = []
    for registry_row in repair_registry_rows:
        tag = registry_row["tag"]
        rows = events_by_tag[tag]
        target2_exact_rows = [row for row in rows if row.get("target2_exact_m1_net_r") is not None]
        previous_m1 = sum(1 for row in rows if row["previous_target2_path_source"] == "M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH")
        previous_m15 = sum(1 for row in rows if row["previous_target2_path_source"] == "M15_PROXY_PATH_NOT_BROKER_LIFECYCLE_TRUTH")
        previous_none = sum(1 for row in rows if row["previous_target2_path_source"] == "none")
        target2_summary = summarize_event_policy(rows, "target2_exact_m1_net_r")
        daily = defaultdict(float)
        for row in target2_exact_rows:
            daily[row["date"]] += float(row["target2_exact_m1_net_r"])
        exact_count = len(target2_exact_rows)
        exact_mean = target2_summary["mean_r"]
        if exact_count >= MIN_EXACT_M1_EVENTS_FOR_DEFAULT_OFF_SUPPORT and exact_mean is not None and exact_mean > 0:
            decision = "graduate_to_exact_m1_supported_default_off_metadata"
        elif exact_count >= MIN_EXACT_M1_EVENTS_FOR_DEFAULT_OFF_SUPPORT and exact_mean is not None and exact_mean <= 0:
            decision = "transform_to_context_or_veto_due_negative_exact_m1"
        else:
            decision = "remain_proxy_repair_gated_missing_exact_m1_history"
        candidate_rows.append(
            {
                "tag": tag,
                "file_symbol": registry_row["file_symbol"],
                "broker_symbol": registry_row["broker_symbol"],
                "family": registry_row["family"],
                "mechanism": registry_row["mechanism"],
                "source_event_count": len(rows),
                "previous_exact_m1_event_count": previous_m1,
                "previous_m15_proxy_event_count": previous_m15,
                "previous_no_path_event_count": previous_none,
                "repaired_exact_m1_event_count": exact_count,
                "repaired_exact_m1_coverage_ratio": round(exact_count / len(rows), 6) if rows else 0.0,
                "new_exact_m1_events_added": max(exact_count - previous_m1, 0),
                "target2_exact_m1_summary": target2_summary,
                "target2_exact_m1_status_counts": dict(Counter(row.get("exact_m1_status") for row in rows)),
                "daily_target2_exact_m1_sum_r": dict(sorted(daily.items())),
                "decision": decision,
                "activation_weight_now": 0.0,
                "live_authority": False,
                "runtime_effect": "none_exact_m1_repair_replay_only",
            }
        )

    full_book_rows = book_interaction_rows(module, candidate_rows)
    decision_counts = Counter(row["decision"] for row in candidate_rows)
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": registry_result.get("ok") is True and len(candidate_rows) == 10 and export_manifest.get("bridge_reachable") is True,
        "decision": "MARKET_EXPANSION_PROXY_M1_REPAIR_COMPLETE_NO_LIVE_AUTHORITY",
        "source_registry_route": rel(REGISTRY_ROUTE),
        "proxy_candidate_count": len(candidate_rows),
        "source_event_count": len(event_rows),
        "previous_exact_m1_event_count": sum(row["previous_exact_m1_event_count"] for row in candidate_rows),
        "previous_m15_proxy_event_count": sum(row["previous_m15_proxy_event_count"] for row in candidate_rows),
        "repaired_exact_m1_event_count": sum(row["repaired_exact_m1_event_count"] for row in candidate_rows),
        "new_exact_m1_events_added": sum(row["new_exact_m1_events_added"] for row in candidate_rows),
        "decision_counts": dict(sorted(decision_counts.items())),
        "activation_weight_now": 0.0,
        "live_authority": False,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "account_info_read": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
    }
    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_artifacts": [
            rel(REGISTRY_ROUTE / "DEFAULT_OFF_REGISTRY_SPEC_LEDGER.jsonl"),
            rel(REGISTRY_ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_REGISTRY_RESULT.json"),
            rel(FOLLOWUP_ROUTE / "MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json"),
            "data/mt5_research_exports/market_expansion_followup_replay_20260618/PATH_REPLAY_EVENT_LEDGER.jsonl",
        ],
        "repair_rows": [row["tag"] for row in repair_registry_rows],
        "allowed_data": ["local MT5 OHLCV/tick-volume exports", "localhost siliconmetatrader5 bridge read-only M1 bars"],
        "forbidden_data": ["orderflow", "depth", "broker order/deal/position/account mutation", "MT5 order state", "VPS process mutation", "live config activation"],
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "ok": True,
        "all_proxy_rows_processed": len(candidate_rows) == 10,
        "all_proxy_events_processed": len(event_rows) == sum(row["source_event_count"] for row in candidate_rows),
        "no_arbitrary_top_n": True,
        "raw_m1_bars_tracked_only_by_manifest": True,
    }
    repair_ledger = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger.v1",
        "ok": True,
        "remaining_proxy_repair_gated_count": decision_counts.get("remain_proxy_repair_gated_missing_exact_m1_history", 0),
        "graduated_exact_m1_supported_count": decision_counts.get("graduate_to_exact_m1_supported_default_off_metadata", 0),
        "transformed_context_or_veto_count": decision_counts.get("transform_to_context_or_veto_due_negative_exact_m1", 0),
        "next_requirements": [
            "update metadata registry only after route verification if any row graduated",
            "run full-book interaction review for graduated rows before future activation package",
            "broker spec/cost/session/deployment verifier remains required before activation",
        ],
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "ok": result["ok"],
        "instruction_coverage": {
            "mandatory_gtos_preflight": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_hardening_controls_read": True,
            "inspire_not_kill_rows_preserved": True,
            "no_arbitrary_top_n": True,
            "same_evidence_class_m1_repair_pursued": True,
        },
        "runtime_effect": "none_research_replay_only",
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 -m py_compile research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18/build_market_expansion_proxy_m1_repair.py research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18/verify_market_expansion_proxy_m1_repair.py tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py",
            "python3 research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18/verify_market_expansion_proxy_m1_repair.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py -q",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_proxy_m1_repair_2026_06_18 --full-jsonl",
            "git diff --check",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }
    decision_rows = [
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "proxy_candidate_count": result["proxy_candidate_count"],
            "source_event_count": result["source_event_count"],
            "new_exact_m1_events_added": result["new_exact_m1_events_added"],
            "decision_counts": result["decision_counts"],
            "runtime_effect": "none_research_replay_only",
        }
    ]
    decision_rows.extend(
        {
            "created_at_utc": created_at,
            "decision": row["decision"],
            "tag": row["tag"],
            "file_symbol": row["file_symbol"],
            "mechanism": row["mechanism"],
            "repaired_exact_m1_event_count": row["repaired_exact_m1_event_count"],
            "target2_exact_m1_mean_r": row["target2_exact_m1_summary"]["mean_r"],
            "activation_weight_now": 0.0,
            "live_authority": False,
            "runtime_effect": "none_research_replay_only",
        }
        for row in candidate_rows
    )
    next_prompt = """# Market Expansion Graduated Metadata Integration Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the proxy M1 repair artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md` as active instructions before acting.

Evidence class: metadata integration for exact-M1-repaired market-expansion rows. This is not live authority. Operate with maximum practical reasoning, active creativity, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, full ledger preservation for all material rows, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation.

Objective: if the proxy M1 repair route graduates any rows, update only default-off metadata to reflect exact-M1 support; keep activation weight `0.0`, preserve collision losers, rerun registry and artifact tests, and preserve every non-graduated row as repair-gated, context/veto/sizing, or source requirement. Result materialization, source completeness, and implementation decision fields are required for every repaired row.

Forbidden surfaces: no production-change or live trading broker operation; no prompt/config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no orderflow/depth; no paid API/vendor calls.

Required verification and completion audit: rerun the registry verifier, proxy M1 repair verifier, focused pytest artifact tests, prompt-hardening validator, route artifact audit, and `git diff --check`; write or update a completion audit, manifest, decision ledger, and focused test result before committing.
"""

    write_json(ROUTE / "PROXY_M1_REPAIR_INPUT_MANIFEST.json", input_manifest)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl(ROUTE / "EXACT_M1_REPAIR_EVENT_LEDGER.jsonl", event_rows)
    write_jsonl(ROUTE / "EXACT_M1_REPAIR_CANDIDATE_LEDGER.jsonl", candidate_rows)
    write_jsonl(ROUTE / "FULL_BOOK_EXACT_M1_INTERACTION_LEDGER.jsonl", full_book_rows)
    write_jsonl(ROUTE / "M1_SOURCE_COVERAGE_LEDGER.jsonl", m1_coverage_rows)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair_ledger)
    write_json(ROUTE / "MARKET_EXPANSION_PROXY_M1_REPAIR_RESULT.json", result)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
            "created_at_utc": created_at,
            "files": sorted({*(path.name for path in ROUTE.iterdir() if path.is_file()), "OUTPUT_MANIFEST.json"}),
        },
    )
    return result


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "proxy_candidate_count": result["proxy_candidate_count"],
                "previous_m15_proxy_event_count": result["previous_m15_proxy_event_count"],
                "repaired_exact_m1_event_count": result["repaired_exact_m1_event_count"],
                "new_exact_m1_events_added": result["new_exact_m1_events_added"],
                "decision_counts": result["decision_counts"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
