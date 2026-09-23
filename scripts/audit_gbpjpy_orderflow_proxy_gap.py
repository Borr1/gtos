#!/usr/bin/env python3
"""Audit the LTO-014 GBPJPY orderflow proxy gap.

This is shadow/research tooling only. It pre-registers the GBPJPY proxy design
problem, checks source availability for the 6B/6J two-leg idea, appends blocker
status rows for existing GBPJPY candidates, and writes a durable report. It
does not infer GBPJPY confluence, call Databento, call AI, call canaries, or
touch order/execution code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import PROMOTION_VERDICT, append_jsonl  # noqa: E402
from src.research_infra.sierra_proxy_registry import NO_REGISTERED_PROXY, registry_entry  # noqa: E402

SCHEMA_VERSION = "gbpjpy_orderflow_proxy_gap_status_v1"
REPORT_SCHEMA_VERSION = "lto014_gbpjpy_orderflow_proxy_gap_v1"
PROXY_DESIGN_VERSION = "gbpjpy_two_leg_proxy_design_v1"

DEFAULT_CANDIDATE_LOG = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_REGISTRY_STATUS_LOG = Path("shadow_logs/sierra_proxy_registry_status.jsonl")
DEFAULT_STATUS_LOG = Path("shadow_logs/gbpjpy_proxy_gap_status.jsonl")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md")

DEFAULT_6B_M15 = Path("data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/GBPUSD_6B_M15.csv")
DEFAULT_6J_M15 = Path("data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/USDJPY_6J_M15.csv")
DEFAULT_GBPJPY_M15 = Path("data/historical/GBPJPY_M15.csv")

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def latest_by_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        current = latest.get(candidate_id)
        if current is None or str(row.get("created_at_utc") or "") >= str(current.get("created_at_utc") or ""):
            latest[candidate_id] = row
    return latest


def _file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_signature(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.exists()).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(_file_hash(path)).encode("ascii"))
        digest.update(b"\0")
    entry = registry_entry("GBPJPY", "GBPJPY")
    digest.update(json.dumps(entry.as_dict(), sort_keys=True).encode("utf-8"))
    return digest.hexdigest()[:32]


def parse_dt(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_ohlcv_series(path: Path | str) -> dict[datetime, dict[str, float]]:
    p = Path(path)
    if not p.exists():
        return {}
    rows: dict[datetime, dict[str, float]] = {}
    with p.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            ts = parse_dt(str(row.get("time") or ""))
            if ts is None:
                continue
            try:
                close = float(row.get("close") or "")
            except (TypeError, ValueError):
                continue
            if not math.isfinite(close) or close <= 0:
                continue
            volume = _safe_float(row.get("volume")) or 0.0
            trades = _safe_float(row.get("num_trades"))
            rows[ts] = {"close": close, "volume": volume, "num_trades": trades if trades is not None else volume}
    return rows


def _safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def session_bucket(ts: datetime) -> str:
    t = ts.time()
    if time(0, 0) <= t < time(3, 0):
        return "tokyo"
    if time(7, 0) <= t < time(9, 30):
        return "london_gbpjpy"
    if time(13, 0) <= t < time(15, 30):
        return "ny_gbpjpy"
    return "other"


def build_price_transfer_diagnostic(
    *,
    leg_6b_m15: Path,
    leg_6j_m15: Path,
    gbpjpy_m15: Path,
    min_common_bars: int = 200,
) -> dict[str, Any]:
    series_6b = load_ohlcv_series(leg_6b_m15)
    series_6j = load_ohlcv_series(leg_6j_m15)
    series_gbpjpy = load_ohlcv_series(gbpjpy_m15)
    common_times = sorted(set(series_6b) & set(series_6j) & set(series_gbpjpy))
    source_rows = {
        "6b_m15_rows": len(series_6b),
        "6j_m15_rows": len(series_6j),
        "gbpjpy_m15_rows": len(series_gbpjpy),
        "common_m15_bars": len(common_times),
    }
    if len(common_times) < 3:
        return {
            "diagnostic_status": "SOURCE_FILES_MISSING_OR_INSUFFICIENT_OVERLAP",
            "source_paths": {
                "leg_6b_m15": str(leg_6b_m15),
                "leg_6j_m15": str(leg_6j_m15),
                "gbpjpy_m15": str(gbpjpy_m15),
            },
            "source_rows": source_rows,
            "thresholds": {
                "min_common_m15_bars_for_stability_gate": min_common_bars,
                "zero_lag_corr_floor_for_future_registration": 0.75,
                "max_abs_best_lag_bars_for_future_registration": 1,
            },
            "no_outcomes_opened": True,
        }

    synthetic_returns: list[float] = []
    gbpjpy_returns: list[float] = []
    return_times: list[datetime] = []
    for previous, current in zip(common_times, common_times[1:]):
        try:
            synth = math.log(series_6b[current]["close"] / series_6b[previous]["close"]) - math.log(
                series_6j[current]["close"] / series_6j[previous]["close"]
            )
            actual = math.log(series_gbpjpy[current]["close"] / series_gbpjpy[previous]["close"])
        except (KeyError, ValueError, ZeroDivisionError):
            continue
        if math.isfinite(synth) and math.isfinite(actual):
            synthetic_returns.append(synth)
            gbpjpy_returns.append(actual)
            return_times.append(current)

    lag_readout: dict[str, dict[str, Any]] = {}
    for lag in range(-2, 3):
        xs: list[float] = []
        ys: list[float] = []
        for index, synth in enumerate(synthetic_returns):
            actual_index = index + lag
            if 0 <= actual_index < len(gbpjpy_returns):
                xs.append(synth)
                ys.append(gbpjpy_returns[actual_index])
        corr = pearson(xs, ys)
        lag_readout[str(lag)] = {
            "lag_bars": lag,
            "meaning": "positive lag means synthetic 6B-6J return leads GBPJPY by that many M15 bars",
            "paired_returns": len(xs),
            "corr": corr,
        }

    non_null_lags = [row for row in lag_readout.values() if row["corr"] is not None]
    best_lag = max(non_null_lags, key=lambda row: abs(float(row["corr"]))) if non_null_lags else None
    session_counts = Counter(session_bucket(ts) for ts in return_times)
    by_date: dict[str, tuple[list[float], list[float]]] = {}
    for ts, synth, actual in zip(return_times, synthetic_returns, gbpjpy_returns):
        xs, ys = by_date.setdefault(ts.date().isoformat(), ([], []))
        xs.append(synth)
        ys.append(actual)

    daily_corr = {
        day: {
            "paired_returns": len(xs),
            "zero_lag_corr": pearson(xs, ys),
        }
        for day, (xs, ys) in sorted(by_date.items())
    }
    common_volume_6b = sum(series_6b[ts]["volume"] for ts in common_times)
    common_volume_6j = sum(series_6j[ts]["volume"] for ts in common_times)
    common_trades_6b = sum(series_6b[ts]["num_trades"] for ts in common_times)
    common_trades_6j = sum(series_6j[ts]["num_trades"] for ts in common_times)
    zero_corr = lag_readout["0"]["corr"]

    return {
        "diagnostic_status": "PRELIMINARY_PRICE_TRANSFER_DIAGNOSTIC_ONLY",
        "source_paths": {
            "leg_6b_m15": str(leg_6b_m15),
            "leg_6j_m15": str(leg_6j_m15),
            "gbpjpy_m15": str(gbpjpy_m15),
        },
        "source_rows": source_rows,
        "thresholds": {
            "min_common_m15_bars_for_stability_gate": min_common_bars,
            "zero_lag_corr_floor_for_future_registration": 0.75,
            "max_abs_best_lag_bars_for_future_registration": 1,
        },
        "current_gate_readout": {
            "common_bars_gate_met": len(common_times) >= min_common_bars,
            "zero_lag_corr": zero_corr,
            "zero_lag_corr_gate_met": zero_corr is not None and abs(zero_corr) >= 0.75,
            "best_lag_bars": None if best_lag is None else best_lag["lag_bars"],
            "best_lag_corr": None if best_lag is None else best_lag["corr"],
            "best_lag_gate_met": best_lag is not None and abs(int(best_lag["lag_bars"])) <= 1,
        },
        "lead_lag_readout": lag_readout,
        "daily_correlation_stability": daily_corr,
        "session_overlap_bars": dict(sorted(session_counts.items())),
        "contract_liquidity": {
            "common_volume_6b": common_volume_6b,
            "common_volume_6j": common_volume_6j,
            "common_num_trades_6b": common_trades_6b,
            "common_num_trades_6j": common_trades_6j,
            "both_legs_have_nonzero_common_volume": common_volume_6b > 0 and common_volume_6j > 0,
        },
        "no_outcomes_opened": True,
        "activation_policy": "diagnostic_only_no_proxy_activation_no_confluence_backfill",
    }


def proxy_designs() -> list[dict[str, Any]]:
    return [
        {
            "design_id": "NO_DIRECT_PROXY_CURRENT",
            "status": "CURRENT_BLOCKER",
            "source_legs": [],
            "can_claim": ["GBPJPY has no registered direct Sierra/Databento orderflow source in the current registry."],
            "cannot_claim": ["Any external orderflow confluence for GBPJPY candidates."],
            "allowed_use_now": "blocker/status rows only",
            "direct_confluence_allowed": False,
        },
        {
            "design_id": "6J_YEN_LEG_CONTEXT_ONLY",
            "status": "PRE_REGISTERED_CONTEXT_ONLY",
            "source_legs": ["6J.v.0"],
            "can_claim": ["Yen-leg futures context after USDJPY/6J transfer validation passes."],
            "cannot_claim": ["GBPJPY direct book liquidity or GBP-leg pressure."],
            "allowed_use_now": "design/readiness only",
            "direct_confluence_allowed": False,
        },
        {
            "design_id": "6B_GBP_LEG_CONTEXT_ONLY",
            "status": "PRE_REGISTERED_CONTEXT_ONLY",
            "source_legs": ["6B.v.0"],
            "can_claim": ["GBP-leg futures context after 6B common-second sampling alignment passes."],
            "cannot_claim": ["JPY-leg pressure or GBPJPY direct depth."],
            "allowed_use_now": "design/readiness only",
            "direct_confluence_allowed": False,
        },
        {
            "design_id": "TWO_BOOK_SYNTHETIC_6B_6J",
            "status": "PRE_REGISTERED_NOT_ACTIVE",
            "source_legs": ["6B.v.0", "6J.v.0"],
            "registered_return_formula": "log_return(GBPJPY) ~= log_return(6B) - log_return(6J)",
            "can_claim": [
                "A tested two-leg price-transfer context if correlation, lead/lag, session overlap, and liquidity gates pass.",
                "Separate GBP-leg and JPY-leg pressure diagnostics, never one synthetic ladder.",
            ],
            "cannot_claim": [
                "A single GBPJPY order book.",
                "Direct resting-liquidity walls for the broker's GBPJPY CFD.",
                "A live veto, entry-timing rule, stop rule, or target-expansion rule without a separate promotion dossier.",
            ],
            "allowed_use_now": "pre-registered shadow design only",
            "direct_confluence_allowed": False,
        },
        {
            "design_id": "BROKER_CROSS_OHLC_CONTROL",
            "status": "CONTROL_ONLY",
            "source_legs": ["GBPUSD broker OHLC", "USDJPY broker OHLC", "GBPJPY broker OHLC"],
            "can_claim": ["Price-transfer control diagnostics from as-of OHLC data."],
            "cannot_claim": ["External orderflow, depth, footprint, or volume-profile confluence."],
            "allowed_use_now": "control diagnostics only",
            "direct_confluence_allowed": False,
        },
    ]


def pre_registered_tests(validation: dict[str, Any]) -> list[dict[str, Any]]:
    readout = validation.get("current_gate_readout") or {}
    liquidity = validation.get("contract_liquidity") or {}
    session_counts = validation.get("session_overlap_bars") or {}
    return [
        {
            "test_id": "GBPJPY-PROXY-T1-CORRELATION-STABILITY",
            "purpose": "Check whether the synthetic 6B-6J return path tracks MT5 GBPJPY before any outcome join.",
            "pass_condition_for_future_registration": "common M15 bars >= 200 and abs(zero_lag_corr) >= 0.75 across the frozen source window",
            "current_status": "PASS" if readout.get("common_bars_gate_met") and readout.get("zero_lag_corr_gate_met") else "NOT_PASSED_OR_NOT_RUN",
            "outcomes_opened": False,
        },
        {
            "test_id": "GBPJPY-PROXY-T2-LEAD-LAG",
            "purpose": "Detect whether 6B/6J leads or lags GBPJPY enough to create timestamp/no-leak risk.",
            "pass_condition_for_future_registration": "best absolute correlation occurs at lag -1, 0, or +1 M15 bar; lag meaning must be frozen",
            "current_status": "PASS" if readout.get("best_lag_gate_met") else "NOT_PASSED_OR_NOT_RUN",
            "outcomes_opened": False,
        },
        {
            "test_id": "GBPJPY-PROXY-T3-SESSION-OVERLAP",
            "purpose": "Confirm the source legs have overlap in GBPJPY Tokyo/London/NY decision sessions.",
            "pass_condition_for_future_registration": "at least 12 common M15 return bars in each intended session before outcome analysis",
            "current_status": "PASS"
            if all(int(session_counts.get(bucket, 0)) >= 12 for bucket in ("tokyo", "london_gbpjpy", "ny_gbpjpy"))
            else "NOT_PASSED_OR_NOT_RUN",
            "outcomes_opened": False,
        },
        {
            "test_id": "GBPJPY-PROXY-T4-CONTRACT-LIQUIDITY",
            "purpose": "Confirm both futures legs are liquid enough in the exact common window.",
            "pass_condition_for_future_registration": "both 6B and 6J common-window volume and trade counts are nonzero",
            "current_status": "PASS"
            if liquidity.get("both_legs_have_nonzero_common_volume")
            and float(liquidity.get("common_num_trades_6b") or 0) > 0
            and float(liquidity.get("common_num_trades_6j") or 0) > 0
            else "NOT_PASSED_OR_NOT_RUN",
            "outcomes_opened": False,
        },
        {
            "test_id": "GBPJPY-PROXY-T5-OUTCOME-TRANSFER-CAVEAT",
            "purpose": "Prevent future reports from treating two-leg context as direct broker outcome validation.",
            "pass_condition_for_future_registration": "status rows keep existing GBPJPY candidate confluence blocked until a separate frozen outcome-transfer protocol exists",
            "current_status": "PASS",
            "outcomes_opened": False,
        },
    ]


def build_status_row(
    candidate: dict[str, Any],
    *,
    generated_at_utc: str,
    source_dependency_signature: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "")
    symbol = str(candidate.get("symbol") or "GBPJPY")
    broker_symbol = str(candidate.get("broker_symbol") or symbol)
    entry = registry_entry(symbol, broker_symbol)
    row_key = hashlib.sha256(f"{SCHEMA_VERSION}|{candidate_id}|{PROXY_DESIGN_VERSION}".encode("utf-8")).hexdigest()[:32]
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "lto_id": "LTO-014",
        "follow_id": "LIVE-FOLLOW-022",
        "status": "BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN",
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "candidate_id": candidate_id,
        "decision_time_utc": candidate.get("decision_time_utc"),
        "registry_proxy_class": entry.proxy_class,
        "registry_source_status": entry.source_status,
        "registry_parity_status": entry.parity_status,
        "current_proxy_status": "NO_REGISTERED_DIRECT_PROXY",
        "direct_proxy_registered": False,
        "direct_confluence_allowed": False,
        "existing_confluence_inferred": False,
        "blocker_policy": "KEEP_BLOCKER_ROWS_NO_BACKFILL_CONFLUENCE",
        "proxy_design_version": PROXY_DESIGN_VERSION,
        "proxy_design_status": "PRE_REGISTERED_NOT_ACTIVE",
        "registered_proxy_designs": [row["design_id"] for row in proxy_designs()],
        "pre_registered_tests": [row["test_id"] for row in pre_registered_tests(validation)],
        "validation_summary": {
            "diagnostic_status": validation.get("diagnostic_status"),
            "current_gate_readout": validation.get("current_gate_readout"),
            "session_overlap_bars": validation.get("session_overlap_bars"),
            "contract_liquidity": validation.get("contract_liquidity"),
            "no_outcomes_opened": validation.get("no_outcomes_opened", True),
        },
        "outcome_transfer_caveat_status": "NOT_OPENED_EXISTING_CANDIDATE_ROWS_REMAIN_BLOCKED",
        "no_leak_status": "PRE_REGISTERED_SOURCE_TESTS_ONLY_NO_OUTCOME_FIELDS",
        "promotion_verdict": PROMOTION_VERDICT,
        **NO_DECISION_COUNTERS,
    }


def build_report(
    *,
    root: Path,
    generated_at_utc: str | None = None,
    candidate_log: Path = DEFAULT_CANDIDATE_LOG,
    registry_status_log: Path = DEFAULT_REGISTRY_STATUS_LOG,
    status_log: Path = DEFAULT_STATUS_LOG,
    leg_6b_m15: Path = DEFAULT_6B_M15,
    leg_6j_m15: Path = DEFAULT_6J_M15,
    gbpjpy_m15: Path = DEFAULT_GBPJPY_M15,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    candidates = [
        row
        for row in latest_by_candidate(read_jsonl(root / candidate_log)).values()
        if str(row.get("symbol") or "") == "GBPJPY"
    ]
    registry_status_rows = [
        row for row in read_jsonl(root / registry_status_log) if str(row.get("symbol") or "") == "GBPJPY"
    ]
    sources = [
        root / candidate_log,
        root / leg_6b_m15,
        root / leg_6j_m15,
        root / gbpjpy_m15,
        root / "src/research_infra/sierra_proxy_registry.py",
    ]
    signature = source_signature(sources)
    validation = build_price_transfer_diagnostic(
        leg_6b_m15=root / leg_6b_m15,
        leg_6j_m15=root / leg_6j_m15,
        gbpjpy_m15=root / gbpjpy_m15,
    )
    status_rows = [
        build_status_row(
            candidate,
            generated_at_utc=generated,
            source_dependency_signature=signature,
            validation=validation,
        )
        for candidate in sorted(candidates, key=lambda row: str(row.get("candidate_id") or ""))
    ]
    entry = registry_entry("GBPJPY", "GBPJPY")
    direct_proxy_registered = entry.proxy_class != NO_REGISTERED_PROXY
    if direct_proxy_registered:
        status = "ACTION_REQUIRED_REGISTRY_CHANGED_REVIEW_GBPJPY_PROXY"
    elif not status_rows:
        status = "NO_GBPJPY_CANDIDATES_DESIGN_REGISTERED"
    else:
        status = "BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN"

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "lto_id": "LTO-014",
        "follow_id": "LIVE-FOLLOW-022",
        "status": status,
        "promotion_verdict": PROMOTION_VERDICT,
        "source_dependency_signature": signature,
        "source_paths": {
            "candidate_log": str(candidate_log),
            "registry_status_log": str(registry_status_log),
            "status_log": str(status_log),
            "leg_6b_m15": str(leg_6b_m15),
            "leg_6j_m15": str(leg_6j_m15),
            "gbpjpy_m15": str(gbpjpy_m15),
        },
        "completion_evidence": {
            "candidate_status_rows_built": len(status_rows),
            "gbpjpy_candidates_seen": len(candidates),
            "gbpjpy_registry_status_rows_seen": len(registry_status_rows),
            "direct_proxy_registered": direct_proxy_registered,
            "existing_gbpjpy_confluence_inferred": False,
            "live_trading_behavior_changed": False,
            "ai_calls": 0,
            "canary_calls": 0,
            "order_calls": 0,
            "paid_data_calls": 0,
        },
        "current_registry_entry": entry.as_dict(),
        "current_candidate_ids": [row.get("candidate_id") for row in status_rows],
        "proxy_designs": proxy_designs(),
        "price_transfer_validation": validation,
        "pre_registered_tests": pre_registered_tests(validation),
        "candidate_status_rows": status_rows,
        "synthesis": {
            "summary": (
                "GBPJPY remains blocked for external orderflow confluence because no direct Sierra/Databento proxy "
                "exists. The viable research path is a pre-registered two-book 6B/6J design that first proves "
                "price-transfer stability and then keeps leg-specific orderflow semantics separate."
            ),
            "non_claims": [
                "No GBPJPY confluence was inferred for existing rows.",
                "No two-book orderflow signal is active.",
                "6B and 6J are not treated as one synthetic GBPJPY ladder.",
                "No broker actual-R or candidate outcome rows were opened by this audit.",
                "No paid Databento, AI, canary, MT5 order, or execution call was made.",
            ],
            "next_steps": [
                "Keep current GBPJPY candidate rows marked no-proxy/source-blocked.",
                "Before any outcome join, freeze the 6B/6J price-transfer source window, lead/lag convention, and pass/fail gates.",
                "After 6B common-second and USDJPY/6J transfer gates pass, collect leg-specific footprint/depth features as context only.",
                "Only later test entry timing, veto, stop/invalidation, or target/RR expansion roles against broker actual-R and lifecycle truth.",
            ],
        },
    }


def append_status_rows_if_missing(rows: list[dict[str, Any]], path: Path) -> int:
    existing = {str(row.get("row_key") or "") for row in read_jsonl(path)}
    appended = 0
    for row in rows:
        key = str(row.get("row_key") or "")
        if not key or key in existing:
            continue
        append_jsonl(path, row)
        existing.add(key)
        appended += 1
    return appended


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    validation = payload["price_transfer_validation"]
    readout = validation.get("current_gate_readout") or {}
    liquidity = validation.get("contract_liquidity") or {}
    lines = [
        "# LTO-014 GBPJPY Orderflow Proxy Gap",
        "",
        "Date: 2026-05-05",
        "Scope: research/tooling only; existing local artifacts only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Synthesis",
        "",
        payload["synthesis"]["summary"],
        "",
        "## Completion Evidence",
        "",
        *table(
            ["field", "value"],
            [[key, value] for key, value in payload["completion_evidence"].items()],
        ),
        "",
        "## Proxy Designs",
        "",
        *table(
            ["design", "status", "source legs", "allowed now", "direct confluence"],
            [
                [
                    row["design_id"],
                    row["status"],
                    row["source_legs"],
                    row["allowed_use_now"],
                    row["direct_confluence_allowed"],
                ]
                for row in payload["proxy_designs"]
            ],
        ),
        "",
        "## Pre-Registered Tests",
        "",
        *table(
            ["test", "purpose", "current status", "outcomes opened"],
            [
                [row["test_id"], row["purpose"], row["current_status"], row["outcomes_opened"]]
                for row in payload["pre_registered_tests"]
            ],
        ),
        "",
        "## Price-Transfer Diagnostic",
        "",
        *table(
            ["field", "value"],
            [
                ["diagnostic_status", validation.get("diagnostic_status")],
                ["common_m15_bars", (validation.get("source_rows") or {}).get("common_m15_bars")],
                ["zero_lag_corr", readout.get("zero_lag_corr")],
                ["best_lag_bars", readout.get("best_lag_bars")],
                ["best_lag_corr", readout.get("best_lag_corr")],
                ["session_overlap_bars", validation.get("session_overlap_bars")],
                ["common_volume_6b", liquidity.get("common_volume_6b")],
                ["common_volume_6j", liquidity.get("common_volume_6j")],
                ["no_outcomes_opened", validation.get("no_outcomes_opened")],
            ],
        ),
        "",
        "## Current GBPJPY Rows",
        "",
        *table(
            ["candidate_id", "status", "direct confluence", "confluence inferred", "proxy design"],
            [
                [
                    row["candidate_id"],
                    row["status"],
                    row["direct_confluence_allowed"],
                    row["existing_confluence_inferred"],
                    row["proxy_design_version"],
                ]
                for row in payload["candidate_status_rows"]
            ],
        ),
        "",
        "## Non-Claims",
        "",
        *[f"- {item}" for item in payload["synthesis"]["non_claims"]],
        "",
        "## Next Steps",
        "",
        *[f"{idx}. {item}" for idx, item in enumerate(payload["synthesis"]["next_steps"], start=1)],
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-log", default=str(DEFAULT_CANDIDATE_LOG))
    parser.add_argument("--registry-status-log", default=str(DEFAULT_REGISTRY_STATUS_LOG))
    parser.add_argument("--status-log", default=str(DEFAULT_STATUS_LOG))
    parser.add_argument("--leg-6b-m15", default=str(DEFAULT_6B_M15))
    parser.add_argument("--leg-6j-m15", default=str(DEFAULT_6J_M15))
    parser.add_argument("--gbpjpy-m15", default=str(DEFAULT_GBPJPY_M15))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--no-append", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_report(
        root=ROOT,
        candidate_log=Path(args.candidate_log),
        registry_status_log=Path(args.registry_status_log),
        status_log=Path(args.status_log),
        leg_6b_m15=Path(args.leg_6b_m15),
        leg_6j_m15=Path(args.leg_6j_m15),
        gbpjpy_m15=Path(args.gbpjpy_m15),
    )
    appended = 0
    if not args.no_append:
        appended = append_status_rows_if_missing(payload["candidate_status_rows"], ROOT / args.status_log)
    payload["completion_evidence"]["status_rows_appended"] = appended
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "gbpjpy_candidates": payload["completion_evidence"]["gbpjpy_candidates_seen"],
                "status_rows_appended": appended,
                "output_json": args.output_json,
                "output_md": args.output_md,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
