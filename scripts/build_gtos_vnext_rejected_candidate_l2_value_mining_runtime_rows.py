#!/usr/bin/env python3
"""Build vNext runtime rows from rejected-candidate/L2 value mining artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
ROWS_PATH = ROUTE_DIR / f"GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_ROWS_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_SUMMARY_{DATE}.json"

L2_SUMMARY_JSON = Path("research/academic_pipeline/data/L2_rejection_summary.json")
L2_SUMMARY_MD = Path("research/academic_pipeline/results/L2_rejection_analysis_v1.md")
RCVM_DIR = Path("research/rejected_candidates_value_mining")

SOURCE_PATHS = (
    L2_SUMMARY_JSON,
    L2_SUMMARY_MD,
    RCVM_DIR / "02_taxonomy.py",
    RCVM_DIR / "03_forward_resolve.py",
    RCVM_DIR / "04_resolve_neutral.py",
    RCVM_DIR / "05_bucket_analysis.py",
    RCVM_DIR / "06_drilldown.py",
    RCVM_DIR / "07_baseline.py",
    RCVM_DIR / "08_live_data.py",
    RCVM_DIR / "09_live_l2_detail.py",
    RCVM_DIR / "10_live_l2_corrected.py",
    RCVM_DIR / "11_backtest_corrected.py",
    RCVM_DIR / "13_live_notrade.py",
    RCVM_DIR / "bt_corrected_l2.jsonl",
    RCVM_DIR / "bt_corrected_l2_summary.csv",
    RCVM_DIR / "bucket_metrics.json",
    RCVM_DIR / "bucket_per_instrument.csv",
    RCVM_DIR / "bucket_per_month.csv",
    RCVM_DIR / "forward_resolution.jsonl",
    RCVM_DIR / "forward_resolution_neutral.jsonl",
    RCVM_DIR / "live_l2_corrected.jsonl",
    RCVM_DIR / "live_l2_corrected_summary.csv",
    RCVM_DIR / "live_l2_detailed.jsonl",
    RCVM_DIR / "live_l2_resolved.jsonl",
    RCVM_DIR / "taxonomy.json",
)

SESSION_MAP = {
    "london": "london_core",
    "ny": "ny_core",
    "tokyo": "tokyo_kz",
}

SYMBOL_FAMILY = {
    "EURUSD": "EURUSD_6E_FAMILY",
    "GBPJPY": "GBPJPY_FAMILY",
    "GBPUSD": "GBPUSD_6B_FAMILY",
    "GER40": "GER40_DAX_FAMILY",
    "NAS100": "NAS100_NQ_FAMILY",
    "UK100": "UK100_FTSE_FAMILY",
    "US30": "US30_YM_FAMILY",
    "US30_cash": "US30_YM_FAMILY",
    "USDJPY": "USDJPY_6J_FAMILY",
    "XAGUSD": "XAGUSD_SILVER_FAMILY",
    "XAUUSD": "XAUUSD_GC_FAMILY",
}

L2_BUCKET_COMPONENTS = {
    "entry_in_ob": "l2_entry_in_ob_rejection_value",
    "h1_poi_exists": "l2_h1_poi_rejection_value",
    "m15_choch_exists": "l2_m15_choch_rejection_value",
    "sl_beyond_ob": "l2_sl_beyond_ob_rejection_value",
}

NO_TRADE_COMPONENTS = {
    "blocked_limit": "rejected_candidate_blocked_limit_value",
    "c1_failed": "rejected_candidate_c1_failed_value",
    "c2_m15_opposing": "rejected_candidate_c2_m15_opposing_value",
    "c3_direction_mismatch": "rejected_candidate_c3_direction_mismatch_value",
    "no_qualifying_h1_poi": "rejected_candidate_no_qualifying_h1_poi_value",
    "no_reason_logged": "rejected_candidate_no_reason_logged_value",
    "ob_proximity_no_unmitigated": "rejected_candidate_ob_proximity_value",
    "other_or_unknown": "rejected_candidate_other_unknown_value",
    "parse_error": "rejected_candidate_parse_error_value",
    "prescreen_no_direction": "rejected_candidate_prescreen_no_direction_value",
}


def _repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(_repo_path(path).read_bytes()).hexdigest()
    except OSError:
        return ""


def _line_count(path: Path) -> int | None:
    full = _repo_path(path)
    try:
        if path.suffix.lower() == ".py":
            return None
        if path.suffix.lower() == ".json":
            return 1
        with full.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with _repo_path(path).open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with _repo_path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _canonical_session(value: Any) -> str:
    raw = str(value or "").strip().casefold()
    return SESSION_MAP.get(raw, raw)


def _canonical_side(value: Any) -> str:
    raw = str(value or "").strip().upper()
    return raw if raw in {"LONG", "SHORT"} else ""


def _symbol(value: Any) -> str:
    return str(value or "").strip()


def _bucket_slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def _component_for_bucket(bucket: str) -> str:
    return L2_BUCKET_COMPONENTS.get(bucket) or NO_TRADE_COMPONENTS.get(bucket) or (
        f"rejected_candidate_{_bucket_slug(bucket) or 'unknown'}_value"
    )


def _source_role(decision: str) -> str:
    if decision == "AVOID":
        return "rejected_candidate_l2_value_avoid_filter"
    if decision == "FOLLOW":
        return "rejected_candidate_l2_value_follow_pressure"
    return "rejected_candidate_l2_value_context_guard"


def _action_class(component: str, decision: str) -> str:
    if decision == "AVOID":
        suffix = "avoid_filter"
    elif decision == "FOLLOW":
        suffix = "follow_scorer"
    else:
        suffix = "context_guard"
    return f"{component}_{suffix}"


def _decision(n: int, total_r: float) -> str:
    if n < 3:
        return "MIXED"
    exp_r = total_r / n if n else 0.0
    if exp_r <= -0.05:
        return "AVOID"
    if exp_r >= 0.05:
        return "FOLLOW"
    return "MIXED"


def _metric(sum_value: float, count: int) -> dict[str, Any]:
    mean = sum_value / count if count else None
    return {
        "sum": round(sum_value, 12),
        "count": count,
        "mean": round(mean, 12) if mean is not None else None,
        "positive_rows": 1 if sum_value > 0 else 0,
        "negative_rows": 1 if sum_value < 0 else 0,
        "zero_rows": 1 if sum_value == 0 else 0,
        "source_field": "fwd_r",
        "source_shape": "scope_total_r_over_source_rows",
    }


def _effective_n_metric(count: int) -> dict[str, Any]:
    return {
        "sum": count,
        "count": 1,
        "mean": count,
        "positive_rows": 1 if count > 0 else 0,
        "negative_rows": 0,
        "zero_rows": 1 if count == 0 else 0,
        "source_field": "source_rows_represented",
        "source_shape": "scope_row_count",
    }


def _row_id(payload: dict[str, Any]) -> str:
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(stable.encode("utf-8")).hexdigest()[:24]
    return f"rejected_candidate_l2_value:{digest}"


def _group_key(dataset: str, row: dict[str, Any], bucket: str, side: str) -> tuple[str, ...]:
    symbol = _symbol(row.get("_instrument") or row.get("symbol") or row.get("instrument"))
    return (
        dataset,
        bucket,
        symbol,
        _canonical_session(row.get("kill_zone")),
        side,
    )


def _accumulate(groups: dict[tuple[str, ...], dict[str, Any]], key: tuple[str, ...], row: dict[str, Any]) -> None:
    group = groups.setdefault(
        key,
        {
            "n": 0,
            "filled": 0,
            "not_filled": 0,
            "wins": 0,
            "losses": 0,
            "expiries": 0,
            "total_r": 0.0,
            "source_row_ids": [],
            "source_symbols": Counter(),
            "source_dates": Counter(),
            "entry_rows": 0,
            "exit_rows": 0,
        },
    )
    group["n"] += 1
    filled = bool(row.get("filled"))
    if filled:
        group["filled"] += 1
    if str(row.get("outcome") or row.get("fwd_outcome") or "").upper() == "NOT_FILLED":
        group["not_filled"] += 1
    outcome = str(row.get("outcome") or row.get("fwd_outcome") or "").upper()
    if outcome == "TP":
        group["wins"] += 1
    elif outcome in {"SL", "SL_AND_TP"}:
        group["losses"] += 1
    elif outcome == "EXPIRY":
        group["expiries"] += 1
    r_value = row.get("fwd_r")
    if r_value is None:
        r_value = row.get("fwd_long_r")
    try:
        group["total_r"] += float(r_value or 0.0)
    except (TypeError, ValueError):
        pass
    row_id = row.get("trade_id") or row.get("timestamp_utc") or row.get("candle_time")
    if row_id and len(group["source_row_ids"]) < 12:
        group["source_row_ids"].append(str(row_id))
    symbol = _symbol(row.get("_instrument") or row.get("symbol") or row.get("instrument"))
    if symbol:
        group["source_symbols"][symbol] += 1
    ts = str(row.get("timestamp_utc") or row.get("candle_time") or "")
    if len(ts) >= 7:
        group["source_dates"][ts[:7]] += 1
    if row.get("entry") or row.get("entry_price") or row.get("fwd_entry"):
        group["entry_rows"] += 1
    if row.get("sl") or row.get("stop_loss") or row.get("tp1") or row.get("take_profit_1") or row.get("outcome") or row.get("fwd_outcome"):
        group["exit_rows"] += 1


def _build_group_rows(
    groups: dict[tuple[str, ...], dict[str, Any]],
    *,
    source_path: Path,
    source_kind: str,
    framework: str = "",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, stats in sorted(groups.items()):
        dataset, bucket, symbol, session, side = key
        count = int(stats["n"])
        total_r = float(stats["total_r"])
        decision = _decision(count, total_r)
        component = _component_for_bucket(bucket)
        action_class = _action_class(component, decision)
        scope: dict[str, Any] = {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "symbol_family": SYMBOL_FAMILY.get(symbol, ""),
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": session,
            "side": side,
        }
        if framework:
            scope["framework"] = framework
            scope["route_family"] = framework
        base = {
            "dataset": dataset,
            "bucket": bucket,
            "symbol": symbol,
            "session": session,
            "side": side,
            "source_kind": source_kind,
        }
        runtime_id = _row_id(base)
        rows.append(
            {
                "schema_version": "gtos_vnext_rejected_candidate_l2_value_mining_runtime_row_v1",
                "rejected_candidate_l2_value_mining_runtime_row_id": runtime_id,
                "row_key": runtime_id,
                "evidence_family": "gtos_vnext_rejected_candidate_l2_value_mining",
                "source_name": "gtos_vnext_rejected_candidate_l2_value_mining_wave",
                "source_group": f"{dataset}:{bucket}",
                "source_role": _source_role(decision),
                "source_component": component,
                "system_surface": "pre_ai_post_l2_l2_rejection_value_mining",
                "runtime_effect_now": "pre_ai_post_l2_l2_rejection_value_mining",
                "review_action": decision,
                "decision": decision,
                "action_class": action_class,
                "r_evidence_class": f"REJECTED_CANDIDATE_L2_VALUE_MINING_{decision}",
                "implementation_action": (
                    "IMPLEMENT_L2_REJECTION_VALUE_AVOID_FILTER"
                    if decision == "AVOID"
                    else (
                        "IMPLEMENT_L2_REJECTION_VALUE_FOLLOW_PRESSURE"
                        if decision == "FOLLOW"
                        else "MERGE_L2_REJECTION_VALUE_AS_CONTEXT"
                    )
                ),
                "event_scope": {k: v for k, v in scope.items() if v},
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": SYMBOL_FAMILY.get(symbol, ""),
                "timeframe": "M15",
                "market_timeframe": "M15",
                "route_session": session,
                "side": side,
                "framework": framework,
                "route_family": framework,
                "source_path": _rel(source_path),
                "drill_through_path": _rel(source_path),
                "source_artifact": _rel(source_path),
                "source_artifact_sha256": _sha256(source_path),
                "source_bound": True,
                "source_complete": decision in {"FOLLOW", "AVOID"},
                "runtime_candidate_use_permitted": decision in {"FOLLOW", "AVOID"},
                "candidate_use_allowed_now": decision == "FOLLOW",
                "live_effect": False,
                "broker_operation": False,
                "paid_api_or_vendor_call": False,
                "runtime_trading_or_live_broker_effect": False,
                "source_rows_represented": count,
                "row_count": count,
                "source_row_ids_sample": stats["source_row_ids"],
                "source_symbol_counts": dict(stats["source_symbols"]),
                "source_month_counts": dict(stats["source_dates"]),
                "filled_rows": int(stats["filled"]),
                "not_filled_rows": int(stats["not_filled"]),
                "win_rows": int(stats["wins"]),
                "loss_rows": int(stats["losses"]),
                "expiry_rows": int(stats["expiries"]),
                "entry_reference_rows": int(stats["entry_rows"]),
                "exit_reference_rows": int(stats["exit_rows"]),
                "total_r": round(total_r, 12),
                "exp_r": round(total_r / count, 12) if count else None,
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(total_r, count),
                    "stress_simulated_r": _metric(total_r, count),
                    "proxy_score": _metric(total_r, count),
                    "effective_n": _effective_n_metric(count),
                },
            }
        )
    return rows


def _corrected_l2_rows(path: Path, dataset: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in _read_jsonl(path):
        bucket = str(row.get("l2_failed_check") or row.get("bucket_sub") or "").strip()
        side = _canonical_side(row.get("direction"))
        if not bucket or not side:
            continue
        _accumulate(groups, _group_key(dataset, row, bucket, side), row)
    return _build_group_rows(groups, source_path=path, source_kind="corrected_l2_limit_fill", framework="ob_retest")


def _directional_forward_rows(path: Path) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in _read_jsonl(path):
        bucket = str(row.get("bucket_sub") or "").strip()
        side = _canonical_side(row.get("fwd_direction") or row.get("direction") or row.get("ai_direction_evaluated"))
        if not bucket or not side:
            continue
        _accumulate(groups, _group_key("directional_forward_resolution", row, bucket, side), row)
    return _build_group_rows(groups, source_path=path, source_kind="directional_forward_resolution")


def _neutral_forward_rows(path: Path) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in _read_jsonl(path):
        bucket = str(row.get("bucket_sub") or "").strip()
        if not bucket:
            continue
        for side, r_key, outcome_key in (
            ("LONG", "fwd_long_r", "fwd_long_outcome"),
            ("SHORT", "fwd_short_r", "fwd_short_outcome"),
        ):
            projected = {
                **row,
                "fwd_r": row.get(r_key),
                "fwd_outcome": row.get(outcome_key),
                "filled": True,
            }
            _accumulate(groups, _group_key("neutral_side_forward_resolution", projected, bucket, side), projected)
    return _build_group_rows(groups, source_path=path, source_kind="neutral_side_forward_resolution")


def _source_artifacts() -> list[dict[str, Any]]:
    artifacts = []
    for path in SOURCE_PATHS:
        artifacts.append(
            {
                "path": _rel(path),
                "hash": _sha256(path),
                "hash_algorithm": "sha256",
                "row_count": _line_count(path),
            }
        )
    return artifacts


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(_directional_forward_rows(RCVM_DIR / "forward_resolution.jsonl"))
    rows.extend(_neutral_forward_rows(RCVM_DIR / "forward_resolution_neutral.jsonl"))
    rows.extend(_corrected_l2_rows(RCVM_DIR / "bt_corrected_l2.jsonl", "backtest_corrected_l2_limit_fill"))
    rows.extend(_corrected_l2_rows(RCVM_DIR / "live_l2_corrected.jsonl", "live_corrected_l2_limit_fill"))
    return rows


def _decision_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(row.get("decision") for row in rows)
    return {key: counts[key] for key in ("FOLLOW", "AVOID", "MIXED") if counts[key]}


def _dimension_counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(str(row.get(field) or "") for row in rows if row.get(field))
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    fields = (
        "symbol",
        "source_symbol",
        "market",
        "timeframe",
        "market_timeframe",
        "route_session",
        "side",
        "framework",
        "route_family",
        "source_component",
    )
    row_list = list(rows)
    return {
        field: sum(1 for row in row_list if not row.get(field))
        for field in fields
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    artifacts = _source_artifacts()
    source_rows_counted = sum(int(item.get("row_count") or 0) for item in artifacts)
    unknown = sum(1 for item in artifacts if item.get("row_count") is None)
    corrected_rows = [
        row for row in rows
        if row.get("source_path", "").endswith(("bt_corrected_l2.jsonl", "live_l2_corrected.jsonl"))
    ]
    return {
        "schema_version": "gtos_vnext_rejected_candidate_l2_value_mining_runtime_summary_v1",
        "runtime_rows_path": _rel(ROWS_PATH),
        "runtime_summary_path": _rel(SUMMARY_PATH),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(int(row.get("source_rows_represented") or 0) for row in rows),
        "wave_source_rows_counted": source_rows_counted,
        "wave_source_artifact_count": len(artifacts),
        "row_count_unknown_unit_count": unknown,
        "selected_open_unit_count": len(artifacts),
        "decision_counts": _decision_counts(rows),
        "source_component_counts": _dimension_counts(rows, "source_component"),
        "source_group_counts": _dimension_counts(rows, "source_group"),
        "source_role_counts": _dimension_counts(rows, "source_role"),
        "action_class_counts": _dimension_counts(rows, "action_class"),
        "r_evidence_class_counts": _dimension_counts(rows, "r_evidence_class"),
        "symbol_counts": _dimension_counts(rows, "symbol"),
        "source_symbol_counts": _dimension_counts(rows, "source_symbol"),
        "market_counts": _dimension_counts(rows, "market"),
        "timeframe_counts": _dimension_counts(rows, "timeframe"),
        "route_session_counts": _dimension_counts(rows, "route_session"),
        "side_counts": _dimension_counts(rows, "side"),
        "framework_counts": _dimension_counts(rows, "framework"),
        "route_family_counts": _dimension_counts(rows, "route_family"),
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "corrected_l2_runtime_rows": len(corrected_rows),
        "corrected_l2_source_rows_represented": sum(int(row.get("source_rows_represented") or 0) for row in corrected_rows),
        "entry_reference_rows": sum(int(row.get("entry_reference_rows") or 0) for row in rows),
        "exit_reference_rows": sum(int(row.get("exit_reference_rows") or 0) for row in rows),
        "candidate_use_allowed_now_rows": sum(1 for row in rows if row.get("candidate_use_allowed_now")),
        "runtime_candidate_use_permitted_rows": sum(1 for row in rows if row.get("runtime_candidate_use_permitted")),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect")),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(1 for row in rows if row.get("paid_api_or_vendor_call")),
        "runtime_trading_or_live_broker_effect_rows": sum(1 for row in rows if row.get("runtime_trading_or_live_broker_effect")),
        "source_artifacts": artifacts,
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROWS_PATH.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    summary = build_summary(rows)
    if args.check:
        existing_rows = ROWS_PATH.read_text(encoding="utf-8-sig") if ROWS_PATH.exists() else ""
        expected_rows = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
        existing_summary = SUMMARY_PATH.read_text(encoding="utf-8-sig") if SUMMARY_PATH.exists() else ""
        expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if existing_rows != expected_rows or existing_summary != expected_summary:
            print("rejected candidate L2 value mining runtime rows are stale")
            return 1
        print(json.dumps({
            "ok": True,
            "runtime_row_count": summary["runtime_row_count"],
            "runtime_source_rows_represented": summary["runtime_source_rows_represented"],
            "wave_source_rows_counted": summary["wave_source_rows_counted"],
            "decision_counts": summary["decision_counts"],
        }, sort_keys=True))
        return 0

    write_outputs(rows, summary)
    print(json.dumps({
        "wrote": _rel(ROWS_PATH),
        "summary": _rel(SUMMARY_PATH),
        "runtime_row_count": summary["runtime_row_count"],
        "runtime_source_rows_represented": summary["runtime_source_rows_represented"],
        "wave_source_rows_counted": summary["wave_source_rows_counted"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
