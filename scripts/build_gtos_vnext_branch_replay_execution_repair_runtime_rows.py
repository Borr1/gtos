#!/usr/bin/env python3
"""Build runtime rows for branch replay execution repair evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
MOONSHOT_ROUTE = Path(
    r"research/science_program_2026_05/"
    r"06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME_SUMMARY_{DATE}.json"
)

BLOCKER_REPAIR_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BLOCKER_REPAIR_LEDGER_2026-05-16.jsonl"
)
BRANCH_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BRANCH_LEDGER_2026-05-16.jsonl"
)
POSITIVE_CHALLENGER_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_POSITIVE_CHALLENGER_LEDGER_2026-05-16.jsonl"
)
SOURCE_ORDERING_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SOURCE_ORDERING_LEDGER_2026-05-16.jsonl"
)
WORK_UNIT_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_WORK_UNIT_LEDGER_2026-05-16.jsonl"
)
PRIMARY_SOURCE_NAMES = (
    BLOCKER_REPAIR_SOURCE,
    BRANCH_SOURCE,
    POSITIVE_CHALLENGER_SOURCE,
    SOURCE_ORDERING_SOURCE,
    WORK_UNIT_SOURCE,
)
SUPPORT_SOURCE_NAMES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BUCKET_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_QUESTION_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl",
)
ALL_SOURCE_NAMES = PRIMARY_SOURCE_NAMES + SUPPORT_SOURCE_NAMES
ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "entry_variant",
    "target_stop_order_class",
    "source_component",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=None)
def _sha256_file_cached(path_text: str) -> str:
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_file_cached(str(path))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _source_path(name: str) -> Path:
    return MOONSHOT_ROUTE / name


def _source_kind(path: Path) -> str:
    upper = path.name.upper()
    if "BLOCKER_REPAIR" in upper:
        return "blocker_repair"
    if "POSITIVE_CHALLENGER" in upper:
        return "positive_challenger"
    if "SOURCE_ORDERING" in upper:
        return "source_ordering"
    if "WORK_UNIT" in upper:
        return "work_unit"
    return "branch_replay"


def _route_parts(row: dict[str, Any]) -> tuple[str, str, str, str]:
    raw = _norm(row.get("route_candidate_id"))
    parts = raw.split("|") if raw else []
    symbol = _norm(row.get("symbol")) or (parts[0] if len(parts) > 0 else "")
    session = _norm(row.get("route_session")) or (parts[1] if len(parts) > 1 else "")
    primitive = parts[2] if len(parts) > 2 else ""
    horizon = parts[3] if len(parts) > 3 else ""
    return symbol, session, primitive, horizon


def _target_stop_order_class(row: dict[str, Any]) -> str:
    target = _norm(row.get("target_multiple"))
    stop = _norm(row.get("stop_multiple"))
    if target and stop:
        return f"target_{target}_stop_{stop}"
    return _norm(row.get("target_stop_contract_id"))


def _text_blob(row: dict[str, Any]) -> str:
    keys = (
        "action_family",
        "ambiguity_status",
        "blocker_repair_class",
        "branch_execution_class",
        "branch_result_class",
        "exact_failure_cause",
        "exact_missing_geometry_or_source_reason",
        "ordering_deep_action_class",
        "ordering_execution_class",
        "positive_deep_action_class",
        "positive_execution_class",
        "positive_replay_status",
        "replay_readiness_class",
        "source_deep_action_class",
        "source_execution_class",
        "source_repair_route_class",
        "target_stop_result",
        "work_unit_execution_status",
        "work_unit_execution_note",
    )
    return " ".join(_norm(row.get(key)).upper() for key in keys)


def _score_field(row: dict[str, Any]) -> tuple[str, float] | None:
    for key in (
        "rstyle_midpoint_mean",
        "interval_rstyle_midpoint_mean",
        "rstyle_lower_mean",
        "interval_rstyle_lower_mean",
        "rstyle_upper_mean",
        "interval_rstyle_upper_mean",
    ):
        value = _to_float(row.get(key))
        if value is not None:
            return key, value
    return None


def _decision_shape(
    row: dict[str, Any],
    *,
    source_kind: str,
) -> tuple[str, str, str, str, str, str, str]:
    blob = _text_blob(row)
    score_item = _score_field(row)
    score = score_item[1] if score_item else None
    action_family = _norm(row.get("action_family")).lower()

    source_or_ordering_repair = any(
        token in blob
        for token in (
            "SOURCE_EXACT_UNAVAILABLE",
            "ACQUIRE_OR_STRESS",
            "SOURCE_ACQUISITION",
            "SOURCE_REPAIR",
            "REPAIR_REQUIRED",
            "M15_INTERVAL",
            "M1_FILL_BAR_INTERVAL",
            "INTERVAL_BOUND",
            "INTERVAL_STRADDLES_ZERO",
            "BINDING_ONLY",
            "NO_SCALAR",
            "REVIEW_AND_ROUTE",
            "RUN_M15_INTERVAL",
            "RUN_M1_FILL_BAR",
            "RUN_SOURCE_STRESS",
        )
    )
    if source_kind == "blocker_repair":
        return (
            "MIXED",
            "branch_replay_execution_blocker_repair_guard",
            "branch_replay_execution_blocker_repair_guard",
            "BRANCH_REPLAY_EXECUTION_SOURCE_OR_ORDERING_REPAIR",
            "source_repair_proof",
            "branch_replay_execution_blocker_repair_context",
            "execution_adjacent_source_repair_guard",
        )
    if source_kind == "source_ordering" and source_or_ordering_repair:
        return (
            "MIXED",
            "branch_replay_execution_source_ordering_guard",
            "branch_replay_execution_source_ordering_guard",
            "BRANCH_REPLAY_EXECUTION_SOURCE_OR_ORDERING_REPAIR",
            "source_repair_proof",
            "branch_replay_execution_source_ordering_context",
            "execution_adjacent_source_repair_guard",
        )
    if source_kind == "work_unit":
        if action_family == "positive" and not source_or_ordering_repair:
            return (
                "FOLLOW",
                "branch_replay_execution_positive_work_unit",
                "branch_replay_execution_positive_work_unit_follow",
                "BRANCH_REPLAY_EXECUTION_POSITIVE_WORK_UNIT",
                "branch_replay_execution_work_unit",
                "branch_replay_execution_positive_work_unit",
                "execution_adjacent_branch_replay_work_order",
            )
        if action_family in {"adverse", "entry"} and "AVOID" in blob:
            return (
                "AVOID",
                "branch_replay_execution_work_unit_avoid",
                "branch_replay_execution_work_unit_avoid_filter",
                "BRANCH_REPLAY_EXECUTION_WORK_UNIT_AVOID",
                "execution_adjacent_avoid_filter",
                "branch_replay_execution_work_unit_avoid",
                "execution_adjacent_branch_replay_work_order",
            )
        return (
            "MIXED",
            "branch_replay_execution_work_unit_context",
            "branch_replay_execution_work_unit_context_guard",
            "BRANCH_REPLAY_EXECUTION_WORK_UNIT_CONTEXT",
            "context_guard_input",
            "branch_replay_execution_work_unit_context",
            "execution_adjacent_branch_replay_work_order",
        )
    if source_kind == "positive_challenger":
        if "POSITIVE_REPLAYABLE_NOW" in blob and score is not None and score > 0:
            return (
                "FOLLOW",
                "branch_replay_execution_positive_challenger",
                "branch_replay_execution_positive_challenger_follow",
                "BRANCH_REPLAY_EXECUTION_POSITIVE_CHALLENGER",
                "branch_replay_execution_positive_proxy",
                "branch_replay_execution_positive_challenger",
                "execution_adjacent_positive_proxy_scorer",
            )
        return (
            "MIXED",
            "branch_replay_execution_positive_source_repair",
            "branch_replay_execution_positive_source_repair_guard",
            "BRANCH_REPLAY_EXECUTION_POSITIVE_SOURCE_REPAIR",
            "source_repair_proof",
            "branch_replay_execution_positive_repair_context",
            "execution_adjacent_source_repair_guard",
        )
    if score is not None and score < 0:
        return (
            "AVOID",
            "branch_replay_execution_negative_or_redesign",
            "branch_replay_execution_negative_avoid_filter",
            "BRANCH_REPLAY_EXECUTION_NEGATIVE_OR_REDESIGN",
            "execution_adjacent_avoid_filter",
            "branch_replay_execution_negative_proxy",
            "execution_adjacent_branch_replay_filter",
        )
    if score is not None and score > 0 and not source_or_ordering_repair:
        return (
            "FOLLOW",
            "branch_replay_execution_positive_proxy",
            "branch_replay_execution_positive_proxy_follow",
            "BRANCH_REPLAY_EXECUTION_POSITIVE_PROXY",
            "branch_replay_execution_positive_proxy",
            "branch_replay_execution_positive_proxy",
            "execution_adjacent_positive_proxy_scorer",
        )
    if score is not None and score > 0:
        return (
            "FOLLOW",
            "branch_replay_execution_positive_repair_bounded_proxy",
            "branch_replay_execution_positive_bounded_follow",
            "BRANCH_REPLAY_EXECUTION_BOUNDED_POSITIVE_PROXY",
            "branch_replay_execution_bounded_proxy",
            "branch_replay_execution_positive_bounded_proxy",
            "execution_adjacent_positive_proxy_scorer",
        )
    return (
        "MIXED",
        "branch_replay_execution_context_guard",
        "branch_replay_execution_context_guard",
        "BRANCH_REPLAY_EXECUTION_CONTEXT",
        "context_guard_input",
        "branch_replay_execution_context_guard",
        "execution_adjacent_branch_replay_context",
    )


def _proxy_r_class(row: dict[str, Any], decision: str) -> str:
    score_item = _score_field(row)
    score = score_item[1] if score_item else None
    if decision == "AVOID":
        return "NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        if score is not None and score >= 0.35:
            return "STRONG_POSITIVE_PROXY_R"
        return "POSITIVE_PROXY_R"
    return ""


def _metric_from_scalar(value: float, source_field: str) -> dict[str, Any]:
    return {
        "sum": value,
        "mean": value,
        "count": 1,
        "match_rows_with_metric": 1,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _metrics(row: dict[str, Any], decision: str) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {
        "effective_n": _metric_from_scalar(1.0, "runtime_row")
    }
    score_item = _score_field(row)
    if score_item is None:
        if decision == "AVOID":
            metrics["proxy_score"] = _metric_from_scalar(-0.1, "avoid_filter_proxy")
            metrics["stress_simulated_r"] = _metric_from_scalar(-0.1, "avoid_filter_proxy")
        return metrics
    field, score = score_item
    if decision == "AVOID" and score > 0:
        score = -abs(score)
    if decision == "MIXED":
        return metrics
    metrics["proxy_score"] = _metric_from_scalar(score, field)
    metrics["cost_adjusted_simulated_r"] = _metric_from_scalar(score, field)
    metrics["stress_simulated_r"] = _metric_from_scalar(score, field)
    return metrics


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    for key in (
        "branch_replay_execution_id",
        "blocker_repair_id",
        "positive_replay_execution_id",
        "source_ordering_execution_id",
        "replay_execution_work_unit_id",
        "branch_queue_id",
        "target_stop_contract_id",
        "route_candidate_id",
        "source_row_id",
    ):
        value = _norm(row.get(key))
        if value:
            return value
    return f"{path.name}:{line_no}"


def _runtime_row(
    row: dict[str, Any],
    *,
    line_no: int,
    path: Path,
    source_kind: str,
) -> dict[str, Any]:
    decision, component, action_class, evidence_class, group, role, surface = (
        _decision_shape(row, source_kind=source_kind)
    )
    symbol, session, primitive, horizon = _route_parts(row)
    side = _norm(row.get("side"))
    entry_variant = _norm(row.get("entry_variant"))
    target_stop = _target_stop_order_class(row)
    source_row_id = _source_row_id(row, path, line_no)
    runtime_row_id = (
        f"branch_replay_execution_repair:{source_kind}:{line_no}:"
        f"{_sha256_text(source_row_id)[:16]}"
    )
    event_scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market": symbol,
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": session,
        "horizon_id": horizon,
        "primitive": primitive,
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop,
        "route_family": "numeric_router",
        "source_component": component,
    }
    event_scope = {key: value for key, value in event_scope.items() if value}
    payload = {
        "branch_replay_execution_repair_runtime_row_id": runtime_row_id,
        "row_key": runtime_row_id,
        "source_row_id": source_row_id,
        "source_name": "gtos_vnext_branch_replay_execution_repair_wave",
        "evidence_family": "gtos_vnext_branch_replay_execution_repair",
        "route_family": "numeric_router",
        "source_component": component,
        "action_class": action_class,
        "review_action": decision,
        "r_evidence_class": evidence_class,
        "source_group": group,
        "source_role": role,
        "system_surface": surface,
        "event_scope": event_scope,
        "symbol": symbol,
        "source_symbol": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market": symbol,
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": session,
        "horizon_id": horizon,
        "primitive": primitive,
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop,
        "source_bound": bool(symbol and session and side and component),
        "source_path": _path_text(path),
        "source_file_sha256": _sha256_file(path),
        "source_line_no": line_no,
        "source_kind": source_kind,
        "source_manifest_hash": _norm(row.get("source_manifest_hash")),
        "route_candidate_id": _norm(row.get("route_candidate_id")),
        "branch_queue_id": _norm(row.get("branch_queue_id")),
        "target_stop_contract_id": _norm(row.get("target_stop_contract_id")),
        "target_stop_result": _norm(row.get("target_stop_result")),
        "target_multiple": _norm(row.get("target_multiple")),
        "stop_multiple": _norm(row.get("stop_multiple")),
        "branch_execution_class": _norm(row.get("branch_execution_class")),
        "branch_result_class": _norm(row.get("branch_result_class")),
        "blocker_repair_class": _norm(row.get("blocker_repair_class")),
        "ordering_execution_class": _norm(row.get("ordering_execution_class")),
        "source_execution_class": _norm(row.get("source_execution_class")),
        "positive_execution_class": _norm(row.get("positive_execution_class")),
        "positive_replay_status": _norm(row.get("positive_replay_status")),
        "work_unit_execution_status": _norm(row.get("work_unit_execution_status")),
        "replay_readiness_class": _norm(row.get("replay_readiness_class")),
        "action_family": _norm(row.get("action_family")),
        "exact_missing_geometry_or_source_reason": _norm(
            row.get("exact_missing_geometry_or_source_reason")
        ),
        "exact_failure_cause": _norm(row.get("exact_failure_cause")),
        "exact_success_cause": _norm(row.get("exact_success_cause")),
        "proxy_r_class": _proxy_r_class(row, decision),
        "r_metrics": _metrics(row, decision),
    }
    return {key: value for key, value in payload.items() if value not in ("", None)}


def build_runtime_rows() -> list[dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    for name in PRIMARY_SOURCE_NAMES:
        path = _source_path(name)
        source_kind = _source_kind(path)
        for line_no, row in enumerate(_read_jsonl(path), start=1):
            runtime_rows.append(
                _runtime_row(
                    row,
                    line_no=line_no,
                    path=path,
                    source_kind=source_kind,
                )
            )
    return runtime_rows


def _coverage(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    coverage_fields = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "horizons": "horizon_id",
        "primitives": "primitive",
        "sides": "side",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
        "source_components": "source_component",
        "action_classes": "action_class",
    }
    coverage: dict[str, dict[str, int]] = {}
    blanks: Counter[str] = Counter()
    for label, field in coverage_fields.items():
        counter: Counter[str] = Counter()
        for row in rows:
            value = _norm(row.get(field) or row.get("event_scope", {}).get(field))
            if value:
                counter[value] += 1
            else:
                blanks[field] += 1
        coverage[label] = dict(sorted(counter.items()))
    for field in ANCHOR_FIELDS:
        blanks.setdefault(field, 0)
    return coverage, dict(sorted(blanks.items()))


def build_summary(runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts: list[dict[str, Any]] = []
    wave_source_rows = 0
    for name in ALL_SOURCE_NAMES:
        path = _source_path(name)
        exists = path.exists()
        rows = _line_count(path) if exists else 0
        wave_source_rows += rows
        runtime_rows_read = rows if name in PRIMARY_SOURCE_NAMES else 0
        source_artifacts.append(
            {
                "path": _path_text(path),
                "name": name,
                "sha256_or_git_blob": _sha256_file(path) if exists else "",
                "rows": rows,
                "runtime_rows_read": runtime_rows_read,
                "source_role": (
                    "primary_runtime_rows"
                    if name in PRIMARY_SOURCE_NAMES
                    else "supporting_sidecar_rows"
                ),
                "missing_or_broken": not exists,
            }
        )
    coverage, blank_anchors = _coverage(runtime_rows)
    return {
        "schema_version": "gtos_vnext_branch_replay_execution_repair_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": sum(
            int(item["runtime_rows_read"]) for item in source_artifacts
        ),
        "wave_source_rows_counted": wave_source_rows,
        "source_artifacts": source_artifacts,
        "decision_counts": dict(sorted(Counter(row["review_action"] for row in runtime_rows).items())),
        "source_component_counts": dict(
            sorted(Counter(row["source_component"] for row in runtime_rows).items())
        ),
        "source_role_counts": dict(
            sorted(Counter(row["source_role"] for row in runtime_rows).items())
        ),
        "source_group_counts": dict(
            sorted(Counter(row["source_group"] for row in runtime_rows).items())
        ),
        "system_surface_counts": dict(
            sorted(Counter(row["system_surface"] for row in runtime_rows).items())
        ),
        "r_evidence_class_counts": dict(
            sorted(Counter(row["r_evidence_class"] for row in runtime_rows).items())
        ),
        "action_class_counts": dict(
            sorted(Counter(row["action_class"] for row in runtime_rows).items())
        ),
        "route_family_counts": dict(
            sorted(Counter(row["route_family"] for row in runtime_rows).items())
        ),
        "coverage_counts": coverage,
        "blank_anchor_counts": blank_anchors,
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("event_scope")),
    }


def write_outputs(runtime_rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in runtime_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    runtime_rows = build_runtime_rows()
    summary = build_summary(runtime_rows)
    expected = int(summary["runtime_source_rows_represented"])
    if len(runtime_rows) != expected:
        raise SystemExit(
            f"runtime row count {len(runtime_rows)} != represented source rows {expected}"
        )
    if args.check:
        existing_rows = OUTPUT_ROWS.read_text(encoding="utf-8") if OUTPUT_ROWS.exists() else ""
        rendered_rows = "".join(json.dumps(row, sort_keys=True) + "\n" for row in runtime_rows)
        existing_summary = (
            OUTPUT_SUMMARY.read_text(encoding="utf-8") if OUTPUT_SUMMARY.exists() else ""
        )
        rendered_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if existing_rows != rendered_rows or existing_summary != rendered_summary:
            raise SystemExit("generated branch replay execution repair outputs are stale")
        return 0

    write_outputs(runtime_rows, summary)
    print(f"Wrote {OUTPUT_ROWS} ({len(runtime_rows)} rows)")
    print(f"Wrote {OUTPUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
