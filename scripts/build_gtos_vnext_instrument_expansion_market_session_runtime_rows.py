#!/usr/bin/env python3
"""Build runtime rows for legacy instrument-expansion market/session evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_instrument_expansion_market_session_runtime"
SOURCE_NAME = "gtos_vnext_instrument_expansion_market_session_wave"
RUNTIME_SURFACE = "instrument_expansion_market_session_runtime"

SOURCE_DIR = REPO_ROOT / "research" / "instrument_expansion_2026-04-25"
OUTPUT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
OUTPUT_ROWS = (
    OUTPUT_DIR
    / f"GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    OUTPUT_DIR
    / f"GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_UNITS: tuple[tuple[str, str, int | None], ...] = (
    ("UNIT_004112", "research/instrument_expansion_2026-04-25/01_edge_fit_estimates.csv", None),
    ("UNIT_004113", "research/instrument_expansion_2026-04-25/01_per_instrument_scorecard.csv", None),
    ("UNIT_004114", "research/instrument_expansion_2026-04-25/01_ranked_candidates.csv", None),
    ("UNIT_004115", "research/instrument_expansion_2026-04-25/01_scorecards_raw.json", None),
    ("UNIT_004117", "research/instrument_expansion_2026-04-25/02_DECAY_ANALYSIS.md", None),
    ("UNIT_004118", "research/instrument_expansion_2026-04-25/02_decay_analysis.py", None),
    ("UNIT_004119", "research/instrument_expansion_2026-04-25/02_decay_clusters.csv", None),
    ("UNIT_004120", "research/instrument_expansion_2026-04-25/02_h1_h2_split.csv", None),
    ("UNIT_004121", "research/instrument_expansion_2026-04-25/02_monthly_metrics.csv", None),
    ("UNIT_004122", "research/instrument_expansion_2026-04-25/02_per_instrument_decay_scorecard.csv", None),
    ("UNIT_004123", "research/instrument_expansion_2026-04-25/02_pooled_h1h2.csv", None),
    ("UNIT_004124", "research/instrument_expansion_2026-04-25/02_results.json", None),
    ("UNIT_004125", "research/instrument_expansion_2026-04-25/03_hourly_buckets.json", None),
    ("UNIT_004126", "research/instrument_expansion_2026-04-25/03_hourly_inspect.py", None),
    ("UNIT_004128", "research/instrument_expansion_2026-04-25/03_microstructure_analyzer.py", None),
    ("UNIT_004129", "research/instrument_expansion_2026-04-25/03_natural_kz_windows.csv", None),
    ("UNIT_004130", "research/instrument_expansion_2026-04-25/03_per_instrument_microstructure.csv", None),
    ("UNIT_004133", "research/instrument_expansion_2026-04-25/_compute_fingerprints.py", None),
    ("UNIT_004134", "research/instrument_expansion_2026-04-25/_gbpusd_kpi.py", None),
    ("UNIT_004135", "research/instrument_expansion_2026-04-25/_gbpusd_mechanical_backtest.py", None),
    ("UNIT_004136", "research/instrument_expansion_2026-04-25/_gbpusd_observer_resolved.jsonl", None),
    ("UNIT_004137", "research/instrument_expansion_2026-04-25/_gbpusd_pre_post_fa2.py", None),
    ("UNIT_004138", "research/instrument_expansion_2026-04-25/_pooled_analysis.py", None),
    ("UNIT_004139", "research/instrument_expansion_2026-04-25/_render_charts.py", None),
    ("UNIT_004140", "research/instrument_expansion_2026-04-25/_run_parallel.py", None),
    ("UNIT_004141", "research/instrument_expansion_2026-04-25/_run_subset.py", None),
    ("UNIT_004171", "research/instrument_expansion_2026-04-25/tier2_ger40/analyze.py", None),
    ("UNIT_004172", "research/instrument_expansion_2026-04-25/tier2_ger40/run_ger40_slice.py", None),
    ("UNIT_004195", "research/instrument_expansion_2026-04-25/tier2_nas100/_run_parallel.py", None),
    ("UNIT_004217", "research/instrument_expansion_2026-04-25/tier2_orchestrator_summary.json", None),
    ("UNIT_004218", "research/instrument_expansion_2026-04-25/tier2_per_slice.csv", None),
)

ROUTE_FRAMEWORKS = {
    "ob_retest": "ob_retest",
    "fvg_fill": "fvg_fill",
    "breaker_re_entry": "breaker_re_entry",
    "sweep_reversal": "sweep_reversal",
    "h1_bos_retest_wr": "ob_retest",
    "sweep_reversal_wr": "sweep_reversal",
}

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "symbol_family",
    "market_timeframe",
    "timeframe",
    "horizon_id",
    "route_session",
    "route_family",
    "side",
    "source_component",
    "source_role",
    "entry_variant",
    "target_stop_order_class",
    "r_evidence_class",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _to_float(value: Any) -> float | None:
    text = _norm(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    number = _to_float(value)
    if number is None:
        return None
    return int(number)


def _repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_payload(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _market_for_symbol(symbol: Any) -> str:
    text = _norm(symbol).upper()
    if text in {"XAUUSD", "XAGUSD"}:
        return "metals"
    if text.endswith("USD") or text.endswith("JPY") or text.endswith("CHF") or text.endswith("CAD") or text.endswith("GBP"):
        return "fx"
    if text in {"NAS100", "US30", "US30_CASH", "GER40", "UK100", "JP225", "SPX500"}:
        return "index"
    if text in {"BTCUSD", "ETHUSD"}:
        return "crypto"
    if "OIL" in text:
        return "energy"
    return text.lower() or "unknown_market"


def _symbol_family(symbol: Any) -> str:
    text = _norm(symbol).upper()
    return resolve_vnext_symbol_family(text) or f"{text}_FAMILY"


def _session_from_hour(hour: int | None) -> str:
    if hour is None:
        return "ALL_SESSIONS"
    if 0 <= hour < 3:
        return "tokyo_kz"
    if 7 <= hour < 12:
        return "london_core"
    if 13 <= hour < 19:
        return "ny_core"
    return "off_core_session"


def _session_from_window(start: Any) -> str:
    text = _norm(start)
    if not text:
        return "ALL_SESSIONS"
    try:
        hour = int(text.split(":", 1)[0])
    except ValueError:
        return "ALL_SESSIONS"
    return _session_from_hour(hour)


def _session_from_kz(value: Any) -> str:
    text = _norm(value).casefold()
    if text in {"london", "london_core"}:
        return "london_core"
    if text in {"ny", "new_york", "ny_core"}:
        return "ny_core"
    if text in {"tokyo", "asia", "asian", "tokyo_kz"}:
        return "tokyo_kz"
    return "off_core_session"


def _timeframe_from_metric(metric: Any) -> str:
    text = _norm(metric).casefold()
    if "m15" in text:
        return "M15"
    if "h1" in text:
        return "H1"
    if "h4" in text:
        return "H4"
    if "d1" in text or "daily" in text:
        return "D1"
    return "M15"


def _route_from_metric(metric: Any) -> str:
    return ROUTE_FRAMEWORKS.get(_norm(metric).casefold(), "instrument_expansion_context")


def _framework_for_route(route: str) -> str:
    return route if route in {"ob_retest", "fvg_fill", "breaker_re_entry"} else ""


def _decision_for_expectancy(expectancy: float | None, candidates: int | None = None) -> str:
    if expectancy is None:
        return "MIXED"
    if candidates is not None and candidates < 20:
        return "MIXED"
    if expectancy > 0.10:
        return "FOLLOW"
    if expectancy < 0.0:
        return "AVOID"
    return "MIXED"


def _route_expectancy(row: dict[str, Any]) -> float | None:
    candidates = _to_float(row.get("candidates"))
    wins = _to_float(row.get("wins"))
    losses = _to_float(row.get("losses"))
    if candidates is None or not candidates or wins is None or losses is None:
        return None
    return (wins * 1.5 - losses) / candidates


def _scope(
    *,
    symbol: str,
    timeframe: str = "M15",
    session: str = "ALL_SESSIONS",
    route_family: str = "",
    side: str = "",
    framework: str = "",
) -> dict[str, str]:
    known_family = resolve_vnext_symbol_family(symbol)
    scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "market_timeframe": timeframe,
        "timeframe": timeframe,
        "horizon_id": "h4",
        "route_session": session,
    }
    if known_family:
        scope["symbol_family"] = known_family
    if route_family:
        scope["route_family"] = route_family
    if framework:
        scope["framework"] = framework
    if side in {"LONG", "SHORT"}:
        scope["side"] = side
    return scope


def _base_row(
    *,
    source_path: Path,
    source_rows_by_path: Counter[str],
    payload: dict[str, Any],
    row_type: str,
    symbol: str,
    decision: str,
    source_component: str,
    source_role: str,
    r_evidence_class: str,
    source_line_no: int | None,
    timeframe: str = "M15",
    session: str = "ALL_SESSIONS",
    route_family: str = "",
    side: str = "ALL_SIDES",
    framework: str = "",
    action_class: str = "",
    entry_variant: str = "instrument_expansion",
    target_stop_order_class: str = "instrument_expansion_context",
    effective_n: float | None = None,
    proxy_score: float | None = None,
    cost_adjusted_simulated_r: float | None = None,
    stress_simulated_r: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_artifact = _repo_path(source_path)
    source_rows_by_path[source_artifact] += 1
    row_index = source_rows_by_path[source_artifact]
    market = _market_for_symbol(symbol)
    scope = _scope(
        symbol=symbol,
        timeframe=timeframe,
        session=session,
        route_family=route_family,
        side=side,
        framework=framework,
    )
    row_key = f"{row_type}:{source_artifact}:{row_index}:{_sha256_payload(payload)[:16]}"
    resolved_action_class = action_class or f"{source_component}_{decision.lower()}"
    row: dict[str, Any] = {
        "instrument_expansion_market_session_runtime_row_id": row_key,
        "row_key": row_key,
        "row_type": row_type,
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "source_artifact": source_artifact,
        "source_artifact_sha256": _sha256_file(source_path),
        "source_line_no": source_line_no,
        "source_row_id": f"{source_artifact}:{row_index}",
        "source_payload_sha256": _sha256_payload(payload),
        "decision": decision,
        "review_action": decision,
        "action_class": resolved_action_class,
        "source_component": source_component,
        "source_role": source_role,
        "r_evidence_class": r_evidence_class,
        "system_surface": RUNTIME_SURFACE,
        "runtime_surface": RUNTIME_SURFACE,
        "symbol": symbol,
        "source_symbol": symbol,
        "market": market,
        "symbol_family": _symbol_family(symbol),
        "market_timeframe": timeframe,
        "timeframe": timeframe,
        "horizon_id": "h4",
        "route_session": session,
        "route_family": route_family or "instrument_expansion_context",
        "framework": framework,
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop_order_class,
        "event_scope": scope,
        "source_bound": True,
        "runtime_evidence_executable": True,
        "runtime_candidate_use_permitted": True,
        "candidate_use_allowed_now": False,
        "broker_operation_permitted": False,
        "legacy_source_freshness_tier": "legacy_2026_04_25",
        "fresh_moonshot_cp_evidence_override_policy": (
            "Legacy instrument-expansion rows are source-role scoped market/session/cost "
            "pressure and cannot override fresher moonshot/CP280/CP281/CP282 evidence "
            "for the same symbol/session/route unless the fresher row is absent."
        ),
    }
    if effective_n is not None:
        row["effective_n"] = round(float(effective_n), 12)
    if proxy_score is not None:
        row["proxy_score"] = round(float(proxy_score), 12)
    if cost_adjusted_simulated_r is not None:
        row["cost_adjusted_simulated_r"] = round(float(cost_adjusted_simulated_r), 12)
    if stress_simulated_r is not None:
        row["stress_simulated_r"] = round(float(stress_simulated_r), 12)
    if extra:
        row.update(extra)
    return row


def _row_from_edge_fit(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    symbol = _norm(row.get("symbol")).upper()
    route_family = _norm(row.get("edge")).casefold()
    candidates = _to_int(row.get("candidates"))
    expectancy = _route_expectancy(row)
    wr = _to_float(row.get("wr"))
    decision = _decision_for_expectancy(expectancy, candidates)
    component = {
        "FOLLOW": "instrument_expansion_route_follow",
        "AVOID": "instrument_expansion_route_avoid",
    }.get(decision, "instrument_expansion_route_context")
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type="instrument_expansion_edge_fit_route_result",
        symbol=symbol,
        decision=decision,
        source_component=component,
        source_role="instrument_expansion_route_edge_fit",
        r_evidence_class="INSTRUMENT_EXPANSION_ROUTE_EXPECTANCY",
        source_line_no=line_no,
        route_family=route_family,
        framework=_framework_for_route(route_family),
        effective_n=candidates,
        proxy_score=None if wr is None else wr - 0.5,
        cost_adjusted_simulated_r=expectancy,
        stress_simulated_r=None if expectancy is None else expectancy * 0.5,
        target_stop_order_class="legacy_route_expectancy_proxy",
        extra={
            "observed_wr": wr,
            "wins": _to_int(row.get("wins")),
            "losses": _to_int(row.get("losses")),
            "timeouts": _to_int(row.get("timeouts")),
            "implied_n_per_month": _to_float(row.get("implied_n_per_month")),
        },
    )


def _row_from_market_score(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
    row_type: str,
) -> dict[str, Any]:
    symbol = _norm(row.get("symbol")).upper()
    recommendation = _norm(row.get("recommendation")).upper()
    composite = _to_float(row.get("composite_score"))
    if recommendation == "REJECT" or (composite is not None and composite < 56.3):
        decision = "AVOID"
        component = "instrument_expansion_market_candidate_avoid"
    elif recommendation == "STRONG-CANDIDATE" or (composite is not None and composite >= 61.2):
        decision = "FOLLOW"
        component = "instrument_expansion_market_candidate_follow"
    else:
        decision = "MIXED"
        component = "instrument_expansion_market_candidate_context"
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type=row_type,
        symbol=symbol,
        decision=decision,
        source_component=component,
        source_role="instrument_expansion_market_candidate_score",
        r_evidence_class="INSTRUMENT_EXPANSION_MARKET_ELIGIBILITY",
        source_line_no=line_no,
        effective_n=_to_float(row.get("ob_retest_candidates")),
        proxy_score=None if composite is None else (composite - 58.3) / 100.0,
        cost_adjusted_simulated_r=None if composite is None else (composite - 58.3) / 100.0,
        target_stop_order_class="market_candidate_score",
        extra={
            "recommendation": recommendation,
            "composite_score": composite,
            "is_live_symbol": str(row.get("is_live")).casefold() == "true",
            "reasoning": _norm(row.get("reasoning")),
        },
    )


def _rows_from_scorecard_raw(
    source_path: Path,
    source_rows_by_path: Counter[str],
) -> list[dict[str, Any]]:
    payload = _read_json(source_path)
    rows: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return rows
    for line_no, (symbol, data) in enumerate(sorted(payload.items()), start=1):
        if not isinstance(data, dict):
            continue
        data = dict(data)
        data.setdefault("symbol", symbol)
        rows.append(
            _row_from_market_score(
                source_path,
                source_rows_by_path,
                data,
                line_no,
                "instrument_expansion_raw_scorecard_market_context",
            )
        )
    return rows


def _row_from_decay_metric(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    symbol = _norm(row.get("instrument")).upper()
    metric = _norm(row.get("metric"))
    delta = _to_float(row.get("delta"))
    route_family = _route_from_metric(metric)
    framework = _framework_for_route(route_family)
    if route_family in {"ob_retest", "sweep_reversal"} and delta is not None:
        decision = "AVOID" if delta <= -0.10 else "FOLLOW" if delta >= 0.10 else "MIXED"
    else:
        decision = "MIXED"
    component = (
        "instrument_expansion_h1_h2_decay_guard"
        if decision == "AVOID"
        else "instrument_expansion_h1_h2_decay_context"
    )
    timeframe = _timeframe_from_metric(metric)
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type="instrument_expansion_h1_h2_decay_metric",
        symbol=symbol,
        decision=decision,
        source_component=component,
        source_role="instrument_expansion_decay_split",
        r_evidence_class="INSTRUMENT_EXPANSION_H1_H2_DECAY",
        source_line_no=line_no,
        timeframe=timeframe,
        route_family=route_family,
        framework=framework,
        effective_n=(_to_float(row.get("h1_n")) or 0.0) + (_to_float(row.get("h2_n")) or 0.0),
        proxy_score=delta,
        cost_adjusted_simulated_r=delta,
        target_stop_order_class="legacy_decay_split",
        extra={
            "metric": metric,
            "h1_mean": _to_float(row.get("h1_mean")),
            "h2_mean": _to_float(row.get("h2_mean")),
            "p_value": _to_float(row.get("p_value")),
        },
    )


def _row_from_monthly_metric(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    symbol = _norm(row.get("instrument")).upper()
    metric = _norm(row.get("metric"))
    value = _to_float(row.get("value"))
    route_family = _route_from_metric(metric)
    framework = _framework_for_route(route_family)
    score: float | None = None
    decision = "MIXED"
    if metric in {"h1_bos_retest_wr", "sweep_reversal_wr"} and value is not None:
        score = value - 0.5
        decision = "FOLLOW" if score >= 0.10 else "AVOID" if score <= -0.10 else "MIXED"
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type="instrument_expansion_monthly_market_metric",
        symbol=symbol,
        decision=decision,
        source_component="instrument_expansion_monthly_context",
        source_role="instrument_expansion_monthly_market_state",
        r_evidence_class="INSTRUMENT_EXPANSION_MONTHLY_CONTEXT",
        source_line_no=line_no,
        timeframe=_timeframe_from_metric(metric),
        route_family=route_family,
        framework=framework,
        proxy_score=score,
        cost_adjusted_simulated_r=score,
        target_stop_order_class="monthly_context",
        extra={"month": _norm(row.get("month")), "metric": metric, "metric_value": value},
    )


def _row_from_decay_scorecard(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
    row_type: str,
) -> dict[str, Any]:
    symbol = _norm(row.get("instrument") or row.get("symbol")).upper()
    direction = _norm(row.get("composite_direction")).upper()
    score = _to_float(row.get("decay_score"))
    delta = _to_float(row.get("h1_bos_wr_delta") or row.get("delta"))
    if "DECAYING" in direction and (score is None or score >= 60.0):
        decision = "AVOID"
        component = "instrument_expansion_h1_h2_decay_guard"
    elif "IMPROVING" in direction:
        decision = "FOLLOW"
        component = "instrument_expansion_h1_h2_decay_context"
    else:
        decision = "MIXED"
        component = "instrument_expansion_h1_h2_decay_context"
    proxy = delta if delta is not None else (None if score is None else (50.0 - score) / 100.0)
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type=row_type,
        symbol=symbol,
        decision=decision,
        source_component=component,
        source_role="instrument_expansion_decay_scorecard",
        r_evidence_class="INSTRUMENT_EXPANSION_DECAY_SCORECARD",
        source_line_no=line_no,
        route_family="ob_retest",
        framework="ob_retest",
        effective_n=(_to_float(row.get("h1_bos_wr_h1_n")) or 0.0)
        + (_to_float(row.get("h1_bos_wr_h2_n")) or 0.0),
        proxy_score=proxy,
        cost_adjusted_simulated_r=proxy,
        target_stop_order_class="legacy_decay_scorecard",
        extra={"composite_direction": direction, "decay_score": score},
    )


def _row_from_natural_window(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    symbol = _norm(row.get("symbol")).upper()
    peak = _to_float(row.get("peak_ratio_vs_uniform"))
    decision = "FOLLOW" if peak is not None and peak >= 1.5 else "MIXED"
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type="instrument_expansion_natural_kz_session_window",
        symbol=symbol,
        decision=decision,
        source_component="instrument_expansion_natural_kz_window",
        source_role="instrument_expansion_session_window",
        r_evidence_class="INSTRUMENT_EXPANSION_SESSION_ACTIVITY",
        source_line_no=line_no,
        session=_session_from_window(row.get("start_utc")),
        proxy_score=None if peak is None else peak - 1.0,
        cost_adjusted_simulated_r=None if peak is None else (peak - 1.0) / 2.0,
        target_stop_order_class="natural_kill_zone_window",
        extra={
            "rank": _to_int(row.get("rank")),
            "start_utc": _norm(row.get("start_utc")),
            "end_utc": _norm(row.get("end_utc")),
            "share_pct": _to_float(row.get("share_pct")),
            "peak_ratio_vs_uniform": peak,
            "asset_class": _norm(row.get("asset_class")),
        },
    )


def _row_from_microstructure(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    symbol = _norm(row.get("symbol")).upper()
    r_cost_typ = _to_float(row.get("r_cost_typ_pct"))
    r_cost_p99 = _to_float(row.get("r_cost_p99_pct"))
    lot_feasible = str(row.get("lot_feasible")).casefold() == "true"
    avoid = (not lot_feasible) or (r_cost_typ is not None and r_cost_typ >= 25.0) or (
        r_cost_p99 is not None and r_cost_p99 >= 100.0
    )
    decision = "AVOID" if avoid else "MIXED"
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type="instrument_expansion_microstructure_cost_feasibility",
        symbol=symbol,
        decision=decision,
        source_component=(
            "instrument_expansion_microstructure_cost_guard"
            if avoid
            else "instrument_expansion_microstructure_context"
        ),
        source_role="instrument_expansion_microstructure_cost",
        r_evidence_class="INSTRUMENT_EXPANSION_COST_FRICTION",
        source_line_no=line_no,
        effective_n=_to_float(row.get("n_m15_candles")),
        proxy_score=None if r_cost_typ is None else -r_cost_typ / 100.0,
        cost_adjusted_simulated_r=None if r_cost_typ is None else -r_cost_typ / 100.0,
        target_stop_order_class="spread_cost_feasibility",
        extra={
            "ftmo_yes": str(row.get("ftmo_yes")).casefold() == "true",
            "lot_feasible": lot_feasible,
            "r_cost_typ_pct": r_cost_typ,
            "r_cost_p99_pct": r_cost_p99,
            "spread_typ": _to_float(row.get("spread_typ")),
            "spread_p99": _to_float(row.get("spread_p99")),
            "deadzone_hours": _norm(row.get("deadzone_hours")),
        },
    )


def _row_from_hourly_bucket(
    source_path: Path,
    source_rows_by_path: Counter[str],
    symbol: str,
    hour: int,
    data: dict[str, Any],
) -> dict[str, Any]:
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload={"symbol": symbol, "hour": hour, **data},
        row_type="instrument_expansion_hourly_activity_bucket",
        symbol=symbol,
        decision="MIXED",
        source_component="instrument_expansion_hourly_session_context",
        source_role="instrument_expansion_hourly_activity",
        r_evidence_class="INSTRUMENT_EXPANSION_HOURLY_ACTIVITY_CONTEXT",
        source_line_no=hour + 1,
        session=_session_from_hour(hour),
        proxy_score=None,
        target_stop_order_class="hourly_session_activity",
        extra={
            "hour_utc": hour,
            "mean_range": _to_float(data.get("mean_range")),
            "mean_tick_vol": _to_float(data.get("mean_tick_vol")),
            "bucket_n": _to_int(data.get("n")),
        },
    )


def _rows_from_hourly_buckets(
    source_path: Path,
    source_rows_by_path: Counter[str],
) -> list[dict[str, Any]]:
    payload = _read_json(source_path)
    rows: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return rows
    for symbol, buckets in sorted(payload.items()):
        if not isinstance(buckets, dict):
            continue
        for hour_text, data in sorted(buckets.items(), key=lambda item: int(item[0])):
            if not isinstance(data, dict):
                continue
            rows.append(
                _row_from_hourly_bucket(source_path, source_rows_by_path, symbol.upper(), int(hour_text), data)
            )
    return rows


def _rows_from_results_json(
    source_path: Path,
    source_rows_by_path: Counter[str],
) -> list[dict[str, Any]]:
    payload = _read_json(source_path)
    rows: list[dict[str, Any]] = []
    if not isinstance(payload, list):
        return rows
    for line_no, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        symbol = _norm(item.get("symbol")).upper()
        monthly = item.get("monthly")
        rows.append(
            _base_row(
                source_path=source_path,
                source_rows_by_path=source_rows_by_path,
                payload=item,
                row_type="instrument_expansion_decay_results_symbol_summary",
                symbol=symbol,
                decision="MIXED",
                source_component="instrument_expansion_decay_results_context",
                source_role="instrument_expansion_decay_results_summary",
                r_evidence_class="INSTRUMENT_EXPANSION_DECAY_RESULTS_CONTEXT",
                source_line_no=line_no,
                effective_n=len(monthly) if isinstance(monthly, dict) else None,
                target_stop_order_class="decay_results_summary",
            )
        )
    return rows


def _row_from_tier2_slice(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    symbol = _norm(row.get("symbol")).upper()
    n_filled = _to_int(row.get("n_filled"))
    exp_r = _to_float(row.get("exp_r"))
    if n_filled is not None and n_filled >= 3 and exp_r is not None and exp_r > 0:
        decision = "FOLLOW"
        component = "instrument_expansion_tier2_slice_follow"
    elif n_filled is not None and n_filled >= 3 and exp_r is not None and exp_r < 0:
        decision = "AVOID"
        component = "instrument_expansion_tier2_slice_avoid"
    else:
        decision = "MIXED"
        component = "instrument_expansion_tier2_slice_context"
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type="instrument_expansion_tier2_slice_replay",
        symbol=symbol,
        decision=decision,
        source_component=component,
        source_role="instrument_expansion_tier2_replay_slice",
        r_evidence_class="INSTRUMENT_EXPANSION_TIER2_REPLAY_RESULT",
        source_line_no=line_no,
        route_family="ob_retest",
        framework="ob_retest",
        effective_n=n_filled,
        proxy_score=exp_r,
        cost_adjusted_simulated_r=exp_r,
        target_stop_order_class="tier2_slice_replay_r",
        extra={
            "slice": _norm(row.get("slice")),
            "start": _norm(row.get("start")),
            "end": _norm(row.get("end")),
            "wr": _to_float(row.get("wr")),
            "total_r": _to_float(row.get("total_r")),
            "cost": _to_float(row.get("cost")),
            "budget_capped": str(row.get("budget_capped")).casefold() == "true",
        },
    )


def _rows_from_tier2_orchestrator_summary(
    source_path: Path,
    source_rows_by_path: Counter[str],
) -> list[dict[str, Any]]:
    payload = _read_json(source_path)
    rows: list[dict[str, Any]] = []
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return rows
    for line_no, item in enumerate(results, start=1):
        if not isinstance(item, dict):
            continue
        symbol = _norm(item.get("symbol")).upper()
        ok = _to_int(item.get("returncode")) == 0
        rows.append(
            _base_row(
                source_path=source_path,
                source_rows_by_path=source_rows_by_path,
                payload=item,
                row_type="instrument_expansion_tier2_orchestrator_job_status",
                symbol=symbol,
                decision="MIXED" if ok else "AVOID",
                source_component=(
                    "instrument_expansion_tier2_job_context"
                    if ok
                    else "instrument_expansion_tier2_source_repair_guard"
                ),
                source_role="instrument_expansion_tier2_job_status",
                r_evidence_class="INSTRUMENT_EXPANSION_TIER2_SOURCE_STATUS",
                source_line_no=line_no,
                route_family="ob_retest",
                framework="ob_retest",
                proxy_score=0.0 if ok else -1.0,
                cost_adjusted_simulated_r=0.0 if ok else -1.0,
                target_stop_order_class="tier2_source_status",
                extra={
                    "slice": _norm(item.get("slice")),
                    "returncode": _to_int(item.get("returncode")),
                    "wall_seconds": _to_float(item.get("wall_seconds")),
                    "log": _norm(item.get("log")),
                },
            )
        )
    return rows


def _row_from_gbpusd_observer(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    symbol = "GBPUSD"
    side = _norm(row.get("direction")).upper()
    outcome = _norm(row.get("outcome")).upper()
    r_value = _to_float(row.get("r"))
    if outcome == "TP" or (r_value is not None and r_value > 0):
        decision = "FOLLOW"
        component = "instrument_expansion_gbpusd_observer_follow"
    elif outcome == "SL" or (r_value is not None and r_value < 0):
        decision = "AVOID"
        component = "instrument_expansion_gbpusd_observer_avoid"
    else:
        decision = "MIXED"
        component = "instrument_expansion_gbpusd_nofill_context"
    return _base_row(
        source_path=source_path,
        source_rows_by_path=source_rows_by_path,
        payload=row,
        row_type="instrument_expansion_gbpusd_observer_resolved_candidate",
        symbol=symbol,
        decision=decision,
        source_component=component,
        source_role="instrument_expansion_gbpusd_observer_candidate",
        r_evidence_class="INSTRUMENT_EXPANSION_GBPUSD_OBSERVER_OUTCOME",
        source_line_no=line_no,
        session=_session_from_kz(row.get("kz")),
        route_family="ob_retest",
        framework="ob_retest",
        side=side if side in {"LONG", "SHORT"} else "ALL_SIDES",
        effective_n=1.0,
        proxy_score=r_value,
        cost_adjusted_simulated_r=r_value,
        target_stop_order_class="gbpusd_observer_outcome",
        extra={
            "candidate_file": _norm(row.get("file")),
            "candle_time": _norm(row.get("candle_time")),
            "l2_passed": bool(row.get("l2_passed")),
            "l2_fails": row.get("l2_fails") if isinstance(row.get("l2_fails"), list) else [],
            "outcome": outcome,
            "r": r_value,
            "bars": _to_int(row.get("bars")),
        },
    )


def _simple_context_rows_from_csv(
    source_path: Path,
    source_rows_by_path: Counter[str],
    row_type: str,
    source_component: str,
    source_role: str,
    r_evidence_class: str,
) -> list[dict[str, Any]]:
    rows = []
    for line_no, row in enumerate(_read_csv(source_path), start=2):
        symbol = _norm(row.get("instrument") or row.get("symbol")).upper()
        if not symbol:
            continue
        rows.append(
            _base_row(
                source_path=source_path,
                source_rows_by_path=source_rows_by_path,
                payload=row,
                row_type=row_type,
                symbol=symbol,
                decision="MIXED",
                source_component=source_component,
                source_role=source_role,
                r_evidence_class=r_evidence_class,
                source_line_no=line_no,
                target_stop_order_class="instrument_expansion_context",
            )
        )
    return rows


def build_rows() -> list[dict[str, Any]]:
    source_rows_by_path: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []

    for line_no, row in enumerate(_read_csv(SOURCE_DIR / "01_edge_fit_estimates.csv"), start=2):
        rows.append(_row_from_edge_fit(SOURCE_DIR / "01_edge_fit_estimates.csv", source_rows_by_path, row, line_no))

    for file_name, row_type in (
        ("01_per_instrument_scorecard.csv", "instrument_expansion_per_instrument_scorecard_market_context"),
        ("01_ranked_candidates.csv", "instrument_expansion_ranked_candidate_market_context"),
    ):
        source_path = SOURCE_DIR / file_name
        for line_no, row in enumerate(_read_csv(source_path), start=2):
            rows.append(_row_from_market_score(source_path, source_rows_by_path, row, line_no, row_type))

    rows.extend(_rows_from_scorecard_raw(SOURCE_DIR / "01_scorecards_raw.json", source_rows_by_path))

    rows.extend(
        _simple_context_rows_from_csv(
            SOURCE_DIR / "02_decay_clusters.csv",
            source_rows_by_path,
            "instrument_expansion_decay_cluster_context",
            "instrument_expansion_decay_cluster_context",
            "instrument_expansion_decay_cluster",
            "INSTRUMENT_EXPANSION_DECAY_CLUSTER_CONTEXT",
        )
    )

    for line_no, row in enumerate(_read_csv(SOURCE_DIR / "02_h1_h2_split.csv"), start=2):
        rows.append(_row_from_decay_metric(SOURCE_DIR / "02_h1_h2_split.csv", source_rows_by_path, row, line_no))

    for line_no, row in enumerate(_read_csv(SOURCE_DIR / "02_monthly_metrics.csv"), start=2):
        rows.append(_row_from_monthly_metric(SOURCE_DIR / "02_monthly_metrics.csv", source_rows_by_path, row, line_no))

    for file_name, row_type in (
        ("02_per_instrument_decay_scorecard.csv", "instrument_expansion_per_instrument_decay_scorecard"),
        ("02_pooled_h1h2.csv", "instrument_expansion_pooled_h1h2_decay_context"),
    ):
        source_path = SOURCE_DIR / file_name
        for line_no, row in enumerate(_read_csv(source_path), start=2):
            rows.append(_row_from_decay_scorecard(source_path, source_rows_by_path, row, line_no, row_type))

    rows.extend(_rows_from_results_json(SOURCE_DIR / "02_results.json", source_rows_by_path))
    rows.extend(_rows_from_hourly_buckets(SOURCE_DIR / "03_hourly_buckets.json", source_rows_by_path))

    for line_no, row in enumerate(_read_csv(SOURCE_DIR / "03_natural_kz_windows.csv"), start=2):
        rows.append(_row_from_natural_window(SOURCE_DIR / "03_natural_kz_windows.csv", source_rows_by_path, row, line_no))

    for line_no, row in enumerate(_read_csv(SOURCE_DIR / "03_per_instrument_microstructure.csv"), start=2):
        rows.append(_row_from_microstructure(SOURCE_DIR / "03_per_instrument_microstructure.csv", source_rows_by_path, row, line_no))

    for line_no, row in enumerate(_read_jsonl(SOURCE_DIR / "_gbpusd_observer_resolved.jsonl"), start=1):
        rows.append(_row_from_gbpusd_observer(SOURCE_DIR / "_gbpusd_observer_resolved.jsonl", source_rows_by_path, row, line_no))

    rows.extend(_rows_from_tier2_orchestrator_summary(SOURCE_DIR / "tier2_orchestrator_summary.json", source_rows_by_path))

    for line_no, row in enumerate(_read_csv(SOURCE_DIR / "tier2_per_slice.csv"), start=2):
        rows.append(_row_from_tier2_slice(SOURCE_DIR / "tier2_per_slice.csv", source_rows_by_path, row, line_no))

    return rows


def _coverage_counts(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counters: dict[str, Counter[str]] = {field: Counter() for field in ANCHOR_FIELDS}
    for row in rows:
        for field in counters:
            value = _norm(row.get(field))
            if value:
                counters[field][value] += 1
    return {field: dict(sorted(counter.items())) for field, counter in counters.items()}


def _blank_anchor_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for field in ANCHOR_FIELDS:
            if not _norm(row.get(field)):
                counts[field] += 1
    return dict(sorted(counts.items()))


def _source_artifacts(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for row in rows:
        path = row["source_artifact"]
        counts[path] += 1
        by_path.setdefault(path, {
            "path": path,
            "sha256": row["source_artifact_sha256"],
        })
    return [
        {**payload, "runtime_rows": counts[path]}
        for path, payload in sorted(by_path.items())
    ]


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        return sum(1 for _ in handle)


def _source_unit_rows_represented(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_counts = Counter(row["source_artifact"] for row in rows)
    represented = []
    for unit_id, path, row_count in SOURCE_UNITS:
        source_path = REPO_ROOT / path
        runtime_rows = runtime_counts.get(path, 0)
        represented.append(
            {
                "unit_id": unit_id,
                "path": path,
                "row_count": row_count if row_count is not None else (runtime_rows or None),
                "runtime_rows": runtime_rows,
                "support_line_count": _line_count(source_path)
                if path.endswith((".py", ".md"))
                else None,
                "sha256": _sha256_file(source_path) if source_path.exists() else "",
            }
        )
    return represented


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = Counter(row["decision"] for row in rows)
    r_evidence_class_counts = Counter(row["r_evidence_class"] for row in rows)
    source_component_counts = Counter(row["source_component"] for row in rows)
    source_role_counts = Counter(row["source_role"] for row in rows)
    selected_units = _source_unit_rows_represented(rows)
    runtime_rows_by_source = {
        item["path"]: item["runtime_rows"]
        for item in selected_units
        if item["runtime_rows"]
    }
    return {
        "schema_version": "gtos_vnext_instrument_expansion_market_session_runtime_summary_v1",
        "generated_at": f"{DATE}T00:00:00Z",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(runtime_rows_by_source.values()),
        "selected_open_unit_count": len(SOURCE_UNITS),
        "selected_source_units_with_runtime_rows": sum(1 for item in selected_units if item["runtime_rows"]),
        "row_count_unknown_unit_count": sum(1 for item in selected_units if item["row_count"] is None),
        "support_script_or_markdown_units": sum(
            1 for _, path, _ in SOURCE_UNITS if path.endswith((".py", ".md"))
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now")
        ),
        "broker_operation_permitted_rows": sum(
            1 for row in rows if row.get("broker_operation_permitted")
        ),
        "route_follow_rows": source_component_counts.get("instrument_expansion_route_follow", 0),
        "route_avoid_rows": source_component_counts.get("instrument_expansion_route_avoid", 0),
        "market_follow_rows": source_component_counts.get("instrument_expansion_market_candidate_follow", 0),
        "market_avoid_rows": source_component_counts.get("instrument_expansion_market_candidate_avoid", 0),
        "microstructure_cost_guard_rows": source_component_counts.get("instrument_expansion_microstructure_cost_guard", 0),
        "tier2_slice_follow_rows": source_component_counts.get("instrument_expansion_tier2_slice_follow", 0),
        "tier2_slice_avoid_rows": source_component_counts.get("instrument_expansion_tier2_slice_avoid", 0),
        "gbpusd_observer_follow_rows": source_component_counts.get("instrument_expansion_gbpusd_observer_follow", 0),
        "gbpusd_observer_avoid_rows": source_component_counts.get("instrument_expansion_gbpusd_observer_avoid", 0),
        "decision_counts": dict(sorted(decision_counts.items())),
        "r_evidence_class_counts": dict(sorted(r_evidence_class_counts.items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "source_role_counts": dict(sorted(source_role_counts.items())),
        "coverage_counts": _coverage_counts(rows),
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": _source_artifacts(rows),
        "selected_source_units": selected_units,
        "runtime_rows_by_source_artifact": dict(sorted(runtime_rows_by_source.items())),
        "freshness_override_policy": (
            "These 2026-04-25 legacy expansion rows are scoped route/session/cost pressure. "
            "Fresher moonshot/CP280/CP281/CP282 rows remain dominant for the same "
            "symbol/session/side/route because the runtime resolver weights direct "
            "current source-bound evidence and these rows carry legacy source roles."
        ),
        "expected_runtime_effect": (
            "Expanded-market candidate scores and edge-fit rows add scoped FOLLOW/AVOID "
            "route pressure; natural KZ windows add session pressure; microstructure "
            "rows add cost/friction guards; GBPUSD observer and tier2 slices add "
            "realized replay/observer pressure. All rows are shadow/runtime evidence "
            "with broker operations still disabled."
        ),
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    summary = build_summary(rows)
    if args.check:
        existing_rows = _read_jsonl(OUTPUT_ROWS)
        existing_summary = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
        if existing_rows != rows or existing_summary != summary:
            raise SystemExit("generated instrument-expansion runtime rows are stale")
    else:
        write_outputs(rows, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
