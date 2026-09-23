#!/usr/bin/env python3
"""Build compact runtime rows for unified action/work-order execution evidence."""

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
WAVE_ID = "WAVE_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME_SUMMARY_{DATE}.json"
)

ACTION_REDESIGN_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_ACTION_RESULT_BUNDLE_"
    "REDESIGN_EXECUTION_RESULT_LEDGER_2026-05-17.jsonl"
)
WORK_ORDER_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_"
    "WORK_ORDER_LEDGER_2026-05-17.jsonl"
)
PRIMARY_SOURCE_NAMES = (ACTION_REDESIGN_SOURCE, WORK_ORDER_SOURCE)
SUPPORT_SOURCE_NAMES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_GUARD_WORK_ORDER_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_RECHECK_WORK_ORDER_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
)
COMPUTED_ACTION_SUPPORT_NAMES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl",
)
ALL_SOURCE_NAMES = (
    PRIMARY_SOURCE_NAMES + SUPPORT_SOURCE_NAMES + COMPUTED_ACTION_SUPPORT_NAMES
)
ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "primitive",
    "side",
    "entry_variant",
    "target_stop_order_class",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    return str(value).strip().casefold() in {"1", "true", "yes", "y", "on"}


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=None)
def _sha256_file_cached(path_text: str) -> str:
    path = Path(path_text)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
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


def _text_blob(row: dict[str, Any]) -> str:
    keys = (
        "source_component",
        "source_status",
        "success_or_failure_cause",
        "implementation_decision",
        "implementation_implication",
        "executable_next_action",
        "unified_action_class",
        "unified_decision_group",
        "unified_system_decision",
        "work_order_family",
        "work_order_ready_state",
        "proxy_r_style_result",
        "action_execution_status",
    )
    return " ".join(_norm(row.get(key)).upper() for key in keys)


def _route_family_for_component(component: str) -> str:
    if component.startswith("nofill_"):
        return "nofill_mechanical"
    return "numeric_router"


def _decision_shape(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    component = _norm(row.get("source_component"))
    blob = _text_blob(row)
    score = _to_float(row.get("proxy_or_module_score") or row.get("proxy_numeric_score"))

    source_repair = any(
        token in blob
        for token in (
            "SOURCE_OR_CONTROL_REPAIR",
            "SOURCE_MATERIALIZATION_REQUIRED",
            "BUILD_EXACT_CONTROL_DENOMINATOR",
            "EXACT_CONTROL_DENOMINATOR",
            "SOURCE_GUARD_OR_REPAIR_REQUIRED",
            "REPAIR_NOFILL",
            "SOURCE_REQUIREMENT",
            "NO_RUNTIME_SCORE",
        )
    )
    if component == "nofill_near_miss_source_requirement":
        source_repair = True

    if (
        component == "nofill_far_miss_avoid"
        or component == "nofill_near_miss_offset"
        or "AVOID_FILTER" in blob
        or "FAILURE_AVOID" in blob
        or "AVOID_INVERSE" in blob
    ) and not source_repair:
        return (
            "AVOID",
            component or "unified_execution_avoid_filter",
            "unified_execution_action_work_order_avoid_filter",
            "UNIFIED_EXECUTION_ACTION_WORK_ORDER_AVOID_FILTER",
            "unified_execution_avoid_guard",
            "unified_execution_avoid_guard",
            "unified_execution_action_work_order_runtime",
        )

    if source_repair:
        return (
            "MIXED",
            component or "unified_execution_source_repair",
            "unified_execution_action_work_order_source_repair_guard",
            "SOURCE_REPAIR_FOR_EXACT_R",
            "source_repair_proof",
            "source_repair_execution_plan",
            "source_repair_proof",
        )

    if component == "nofill_near_miss_market_entry":
        return (
            "FOLLOW",
            component,
            "unified_execution_action_work_order_follow_scorer",
            "UNIFIED_EXECUTION_ACTION_WORK_ORDER_MARKET_ENTRY",
            "unified_execution_market_entry",
            "unified_execution_market_entry_follow",
            "nofill_pending_policy_runtime",
        )

    if (
        "IMPLEMENT" in blob
        or "ENTRY_GEOMETRY" in blob
        or "SCORER_MODULE" in blob
        or "SCORER_CANDIDATE" in blob
        or (score is not None and score > 0)
    ):
        return (
            "FOLLOW",
            component or "unified_execution_follow_scorer",
            "unified_execution_action_work_order_follow_scorer",
            "UNIFIED_EXECUTION_ACTION_WORK_ORDER_POSITIVE_PROXY",
            "scorer_registry_surface",
            "scorer_registry_surface",
            "default_off_research_scorer_registry_catalog",
        )

    return (
        "MIXED",
        component or "unified_execution_context_guard",
        "unified_execution_action_work_order_context_guard",
        "UNIFIED_EXECUTION_ACTION_WORK_ORDER_CONTEXT_GUARD",
        "context_guard_input",
        "unified_execution_context_guard",
        "context_guard_input",
    )


def _proxy_r_class(row: dict[str, Any], decision: str) -> str:
    if decision == "AVOID":
        return "STRONG_NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        score = _to_float(row.get("proxy_or_module_score") or row.get("proxy_numeric_score"))
        if score is None:
            return "POSITIVE_PROXY_R"
        if score >= 0.35:
            return "STRONG_POSITIVE_PROXY_R"
        if score > 0:
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
    score = _to_float(row.get("proxy_or_module_score") or row.get("proxy_numeric_score"))
    if score is not None:
        metrics["proxy_score"] = _metric_from_scalar(score, "proxy_or_module_score")
        metrics["cost_adjusted_simulated_r"] = _metric_from_scalar(
            score,
            "proxy_or_module_score",
        )
        metrics["stress_simulated_r"] = _metric_from_scalar(
            score,
            "proxy_or_module_score",
        )
    elif decision == "AVOID":
        metrics["proxy_score"] = _metric_from_scalar(-0.1, "avoid_filter_proxy")
        metrics["stress_simulated_r"] = _metric_from_scalar(
            -0.1,
            "avoid_filter_proxy",
        )
    return metrics


def _source_kind(path: Path) -> str:
    if "ACTION_RESULT_BUNDLE" in path.name:
        return "action_result_redesign_execution"
    return "work_order_execution"


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    return (
        _norm(row.get("unified_system_action_result_row_id"))
        or _norm(row.get("unified_system_work_order_row_id"))
        or _norm(row.get("source_row_id"))
        or f"{path.name}:{line_no}"
    )


def _runtime_row(
    row: dict[str, Any],
    *,
    line_no: int,
    path: Path,
    source_kind: str,
) -> dict[str, Any]:
    decision, component, action_class, evidence_class, group, role, surface = _decision_shape(row)
    symbol = _norm(row.get("symbol"))
    session = _norm(row.get("route_session"))
    horizon = _norm(row.get("horizon_id"))
    primitive = _norm(row.get("primitive_flag"))
    source_row_id = _source_row_id(row, path, line_no)
    runtime_row_id = (
        f"unified_execution_action_work_order:{source_kind}:{line_no}:"
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
        "route_family": _route_family_for_component(component),
        "source_component": component,
    }
    event_scope = {key: value for key, value in event_scope.items() if value}
    payload = {
        "unified_execution_action_work_order_runtime_row_id": runtime_row_id,
        "row_key": runtime_row_id,
        "source_row_id": source_row_id,
        "input_source_row_id": _norm(row.get("source_row_id")),
        "source_name": "gtos_vnext_unified_execution_action_work_order_wave",
        "evidence_family": "gtos_vnext_unified_execution_action_work_order",
        "route_family": _route_family_for_component(component),
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
        "source_bound": bool(symbol and session and component),
        "source_path": _path_text(path),
        "source_file_sha256": _sha256_file(path),
        "source_line_no": line_no,
        "source_kind": source_kind,
        "source_manifest_hash": _norm(row.get("source_manifest_hash")),
        "mechanical_scope_key": _norm(row.get("mechanical_scope_key")),
        "work_order_family": _norm(row.get("work_order_family")),
        "action_result_family": _norm(row.get("action_result_family")),
        "implementation_decision": _norm(row.get("implementation_decision")),
        "implementation_implication": _norm(row.get("implementation_implication")),
        "executable_next_action": _norm(row.get("executable_next_action")),
        "unified_decision_group": _norm(row.get("unified_decision_group")),
        "unified_system_decision": _norm(row.get("unified_system_decision")),
        "unified_action_class": _norm(row.get("unified_action_class")),
        "work_order_ready_state": _norm(row.get("work_order_ready_state")),
        "source_status": _norm(row.get("source_status")),
        "success_or_failure_cause": _norm(row.get("success_or_failure_cause")),
        "fillability_no_fill_status": _norm(row.get("fillability_no_fill_status")),
        "runtime_score_allowed": _truthy(row.get("runtime_score_allowed")),
        "candidate_use_allowed_now": _truthy(row.get("candidate_use_allowed_now")),
        "not_completion": _truthy(row.get("not_completion")),
        "proxy_r_class": _proxy_r_class(row, decision),
        "r_metrics": _metrics(row, decision),
    }
    return {key: value for key, value in payload.items() if value not in ("", None)}


def build_runtime_rows() -> list[dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    redesign_path = _source_path(ACTION_REDESIGN_SOURCE)
    for line_no, row in enumerate(_read_jsonl(redesign_path), start=1):
        runtime_rows.append(
            _runtime_row(
                row,
                line_no=line_no,
                path=redesign_path,
                source_kind=_source_kind(redesign_path),
            )
        )
    work_order_path = _source_path(WORK_ORDER_SOURCE)
    for line_no, row in enumerate(_read_jsonl(work_order_path), start=1):
        if _norm(row.get("work_order_family")) == "REDESIGN_EXECUTION":
            continue
        runtime_rows.append(
            _runtime_row(
                row,
                line_no=line_no,
                path=work_order_path,
                source_kind=_source_kind(work_order_path),
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
        runtime_rows_read = 0
        if name == ACTION_REDESIGN_SOURCE:
            runtime_rows_read = rows
        elif name == WORK_ORDER_SOURCE:
            runtime_rows_read = sum(
                1
                for row in _read_jsonl(path)
                if _norm(row.get("work_order_family")) != "REDESIGN_EXECUTION"
            )
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
        "schema_version": "gtos_vnext_unified_execution_action_work_order_runtime_summary_v1",
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
        "work_order_family_counts": dict(
            sorted(Counter(row.get("work_order_family", "") for row in runtime_rows).items())
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
            raise SystemExit("generated unified execution runtime outputs are stale")
        return 0

    write_outputs(runtime_rows, summary)
    print(f"Wrote {OUTPUT_ROWS} ({len(runtime_rows)} rows)")
    print(f"Wrote {OUTPUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
