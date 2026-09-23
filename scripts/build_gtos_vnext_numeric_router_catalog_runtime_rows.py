#!/usr/bin/env python3
"""Build runtime rows for MAIN_ORCH48 numeric-router catalog evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_SUMMARY_{DATE}.json"

CATALOG_SOURCE_NAMES = (
    "MAIN_ORCH48_NUMERIC_ROUTER_AVOID_FILTER_CATALOG_LEDGER_2026-05-18.jsonl",
    "MAIN_ORCH48_NUMERIC_ROUTER_SCORER_REGISTRY_CATALOG_LEDGER_2026-05-18.jsonl",
    "MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_CATALOG_LEDGER_2026-05-18.jsonl",
)
SCOPE_DECISION_SOURCE_NAME = "MAIN_ORCH48_NUMERIC_ROUTER_SCOPE_DECISION_LEDGER_2026-05-18.jsonl"
ACTION_QUEUE_SOURCE_NAME = "MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE_LEDGER_2026-05-18.jsonl"
SUPPORT_NAME_TOKENS = (
    "MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE",
    "MAIN_ORCH48_NUMERIC_ROUTER_AVOID_FILTER",
    "MAIN_ORCH48_NUMERIC_ROUTER_AVOID_SCORE",
    "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG",
    "MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD",
    "MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC",
    "MAIN_ORCH48_NUMERIC_ROUTER_IMPLEMENTATION_CATALOG",
    "MAIN_ORCH48_NUMERIC_ROUTER_SCOPE_DECISION",
    "MAIN_ORCH48_NUMERIC_ROUTER_SCORER",
    "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE",
    "MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO",
)
SUPPORT_SCRIPT_TOKENS = (
    "numeric_router_action_queue",
    "numeric_router_catalog",
    "numeric_router_family_action",
    "numeric_router_implementation_catalog",
    "numeric_router_source_component_bridge",
    "numeric_router_system_recommendation",
)
ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "symbol_family",
    "market_timeframe",
    "timeframe",
    "route_session",
    "horizon_id",
    "primitive",
    "side",
    "source_component",
    "entry_variant",
    "target_stop_order_class",
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


def _to_int(value: Any, default: int = 0) -> int:
    numeric = _to_float(value)
    if numeric is None:
        return default
    return int(numeric)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_text(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
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


def _line_count(path: Path) -> int | None:
    if path.suffix.lower() == ".json":
        return 1
    if path.suffix.lower() not in {".jsonl", ".json", ".md", ".txt", ".py"}:
        return None
    try:
        with path.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _catalog_wave_source_paths() -> list[Path]:
    paths: list[Path] = []
    for path in SOURCE_DIR.iterdir():
        if not path.is_file():
            continue
        name = path.name
        lower = name.casefold()
        if any(token in name for token in SUPPORT_NAME_TOKENS) or any(
            token in lower for token in SUPPORT_SCRIPT_TOKENS
        ):
            paths.append(path)
    return sorted(paths, key=lambda item: item.name.casefold())


def _metric_from_stats(stats: Any, *, source_field: str) -> dict[str, Any] | None:
    if not isinstance(stats, dict):
        return None
    count = _to_float(stats.get("count"))
    mean = _to_float(stats.get("mean"))
    if count is None or count <= 0 or mean is None:
        return None
    total = count * mean
    return {
        "sum": round(total, 12),
        "count": int(count) if count.is_integer() else count,
        "mean": round(mean, 12),
        "min": stats.get("min"),
        "max": stats.get("max"),
        "positive_rows": int(total > 0),
        "negative_rows": int(total < 0),
        "zero_rows": int(total == 0),
        "source_field": source_field,
        "source_shape": "numeric_router_catalog_stats",
    }


def _metric_from_count(value: int, *, source_field: str) -> dict[str, Any]:
    return {
        "sum": value,
        "count": 1,
        "mean": value,
        "positive_rows": int(value > 0),
        "negative_rows": 0,
        "zero_rows": int(value == 0),
        "source_field": source_field,
        "source_shape": "row_count",
    }


def _shape_for_action(action: str, catalog_type: str = "") -> tuple[str, str, str, str, str, str]:
    upper = action.upper()
    if "DEFAULT_OFF_SCORER" in upper or "IMPLEMENT_DEFAULT_OFF_SCORER" in upper:
        return (
            "FOLLOW",
            "numeric_router_default_off_follow_scorer",
            "default_off_scorer_registry",
            "default_off_scorer_surface",
            "numeric_router_default_off_scorer_catalog",
            "numeric_router_default_off_follow_pressure",
        )
    if (
        "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE" in upper
        or "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY" in upper
        or "FAIL_CLOSED_OR_DOWNWEIGHT_AMBIGUOUS_NEGATIVE_PROXY" in upper
        or "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE" in upper
        or "avoid_filter" in catalog_type.casefold()
    ):
        return (
            "AVOID",
            "numeric_router_default_off_avoid_filter",
            "avoid_filter_catalog",
            "default_off_avoid_filter",
            "numeric_router_default_off_avoid_filter_catalog",
            "numeric_router_default_off_avoid_pressure",
        )
    if "SOURCE_GEOMETRY_REPAIR" in upper or "SOURCE_REPAIR" in upper:
        return (
            "MIXED",
            "numeric_router_scope_source_repair_guard",
            "source_repair_proof",
            "source_repair_execution_plan",
            "numeric_router_scope_source_repair_map",
            "numeric_router_scope_source_repair_context",
        )
    return (
        "MIXED",
        "numeric_router_context_guard",
        "context_guard_input",
        "context_guard_input",
        "numeric_router_context_guard_catalog",
        "numeric_router_context_guard_pressure",
    )


def _source_rows_represented(row: dict[str, Any]) -> int:
    for key in ("input_action_rows", "row_count", "catalog_priority_weight"):
        value = _to_int(row.get(key))
        if value:
            return value
    return 1


def _base_runtime_row(
    row: dict[str, Any],
    *,
    row_id: str,
    source_path: Path,
    action: str,
    catalog_type: str = "",
    source_kind: str,
) -> dict[str, Any]:
    decision, action_class, source_group, source_role, system_surface, runtime_effect = (
        _shape_for_action(action, catalog_type)
    )
    symbol = _norm(row.get("symbol"))
    source_component = _norm(row.get("source_component")) or "numeric_router_catalog"
    route_session = _norm(row.get("route_session"))
    horizon_id = _norm(row.get("horizon_id"))
    proxy_r_class = _norm(row.get("proxy_r_class"))
    source_rows = _source_rows_represented(row)
    scope = {
        "route_family": "numeric_router",
        "source_component": source_component,
    }
    if symbol:
        scope["symbol"] = symbol
        scope["symbol_family"] = resolve_vnext_symbol_family(symbol)
    if route_session:
        scope["route_session"] = route_session
    if horizon_id:
        scope["horizon_id"] = horizon_id
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class
    if target_stop := _norm(row.get("target_stop_order_class")):
        scope["target_stop_order_class"] = target_stop

    metrics: dict[str, Any] = {"effective_n": _metric_from_count(source_rows, source_field="source_rows_represented")}
    proxy_metric = (
        _metric_from_stats(row.get("registry_surface_score_stats"), source_field="registry_surface_score_stats")
        or _metric_from_stats(row.get("avoid_comparator_score_stats"), source_field="avoid_comparator_score_stats")
    )
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    elif (score := _to_float(row.get("score_mean"))) is not None and (count := _to_float(row.get("score_count"))) is not None:
        metrics["proxy_score"] = {
            "sum": round(score * count, 12),
            "count": int(count) if count.is_integer() else count,
            "mean": round(score, 12),
            "min": row.get("score_min"),
            "max": row.get("score_max"),
            "positive_rows": int(score * count > 0),
            "negative_rows": int(score * count < 0),
            "zero_rows": int(score * count == 0),
            "source_field": "scope_decision_score_mean",
            "source_shape": "numeric_router_scope_decision_score",
        }

    path_hash = _sha256_file(source_path)
    result = {
        "numeric_router_catalog_runtime_row_id": row_id,
        "row_key": row_id,
        "source_row_id": (
            _norm(row.get("numeric_router_catalog_entry_id"))
            or _norm(row.get("scope_system_decision_row_id"))
            or row_id
        ),
        "source_name": "main_orch48_numeric_router_catalog",
        "evidence_family": "gtos_vnext_numeric_router_catalog_runtime",
        "route_family": "numeric_router",
        "source_component": source_component,
        "source_group": source_group,
        "source_role": source_role,
        "system_surface": system_surface,
        "decision": decision,
        "review_action": decision,
        "action_class": action_class,
        "implementation_action": action,
        "row_route_decision": action,
        "runtime_effect_now": runtime_effect,
        "r_evidence_class": proxy_r_class or (
            "SOURCE_REPAIR_FOR_EXACT_R" if source_group == "source_repair_proof" else "NUMERIC_ROUTER_CATALOG_CONTEXT"
        ),
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market_timeframe": "",
        "timeframe": "",
        "route_session": route_session,
        "horizon_id": horizon_id,
        "primitive": "",
        "side": "",
        "entry_variant": "",
        "target_stop_order_class": target_stop,
        "source_rows_represented": source_rows,
        "source_event_rows": source_rows,
        "unique_scope_registry_match_rows": 1,
        "source_bound": bool(symbol and route_session and source_component),
        "source_complete": True,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "runtime_score_allowed": False,
        "live_effect": False,
        "validation_safe": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "outcome_review_opened": False,
        "catalog_type": catalog_type,
        "catalog_priority_bucket": row.get("catalog_priority_bucket"),
        "catalog_priority_rank": row.get("catalog_priority_rank"),
        "catalog_entry_status": row.get("catalog_entry_status"),
        "implementation_target": row.get("implementation_target") or row.get("implementation_candidate_type"),
        "numeric_router_source_kind": source_kind,
        "source_path": _path_text(source_path),
        "drill_through_path": _path_text(source_path),
        "source_file_sha256": path_hash,
        "source_artifact_sha256": path_hash,
        "declared_origin_artifact": _path_text(source_path),
        "declared_origin_sha256": path_hash,
        "declared_origin_line_no": row.get("source_line_no"),
        "r_metrics": metrics,
        "event_scope": scope,
    }
    for key in (
        "primitive_flag",
        "output_family",
        "input_action_rows",
        "input_numeric_router_family_spec_id",
        "input_numeric_router_catalog_entry_id",
        "input_scope_router_decision_row_id",
        "scope_system_decision_row_id",
        "router_scope_decision",
        "score_count",
        "avoid_inverse_event_count",
        "context_stress_event_count",
        "scorer_event_count",
    ):
        if key in row:
            result[key] = row.get(key)
    return result


def _catalog_rows() -> list[dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    ordinal = 1
    for name in CATALOG_SOURCE_NAMES:
        path = SOURCE_DIR / name
        for row in _read_jsonl(path):
            runtime_rows.append(
                _base_runtime_row(
                    row,
                    row_id=f"GTOS-VNEXT-NUMERIC-ROUTER-CATALOG-{ordinal:06d}",
                    source_path=path,
                    action=_norm(row.get("numeric_router_action")),
                    catalog_type=_norm(row.get("catalog_type")),
                    source_kind="catalog_entry",
                )
            )
            ordinal += 1
    path = SOURCE_DIR / SCOPE_DECISION_SOURCE_NAME
    for row in _read_jsonl(path):
        runtime_rows.append(
            _base_runtime_row(
                row,
                row_id=f"GTOS-VNEXT-NUMERIC-ROUTER-CATALOG-{ordinal:06d}",
                source_path=path,
                action=_norm(row.get("router_scope_decision")),
                catalog_type="scope_decision_implementation_map",
                source_kind="scope_decision_map",
            )
        )
        ordinal += 1
    runtime_rows.sort(key=lambda item: item["numeric_router_catalog_runtime_row_id"])
    return runtime_rows


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _catalog_rows()
    runtime_rows_by_source_name = Counter(Path(row["source_path"]).name for row in rows)
    source_stats: list[dict[str, Any]] = []
    for path in _catalog_wave_source_paths():
        source_stats.append(
            {
                "path": _path_text(path),
                "rows": _line_count(path),
                "sha256_or_git_blob": _sha256_file(path),
                "suffix": path.suffix.lower(),
                "runtime_rows_read": runtime_rows_by_source_name.get(path.name, 0),
            }
        )

    action_queue_rows = _line_count(SOURCE_DIR / ACTION_QUEUE_SOURCE_NAME) or 0
    source_rows_represented = sum(int(row.get("source_rows_represented") or 0) for row in rows)
    counted_source_rows = sum(
        int(stat["rows"]) for stat in source_stats if isinstance(stat.get("rows"), int)
    )
    summary = {
        "schema_version": "gtos_vnext_numeric_router_catalog_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": source_rows_represented,
        "unique_action_queue_rows_represented": action_queue_rows,
        "catalog_runtime_rows_read": sum(
            _line_count(SOURCE_DIR / name) or 0 for name in CATALOG_SOURCE_NAMES
        ),
        "scope_decision_rows_read": _line_count(SOURCE_DIR / SCOPE_DECISION_SOURCE_NAME) or 0,
        "wave_source_rows_counted": counted_source_rows,
        "wave_source_artifact_count": len(source_stats),
        "row_count_unknown_source_artifact_count": sum(
            1 for stat in source_stats if stat.get("rows") is None
        ),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "implementation_action_counts": dict(
            sorted(Counter(row["implementation_action"] for row in rows).items())
        ),
        "catalog_type_counts": dict(sorted(Counter(row["catalog_type"] for row in rows).items())),
        "source_component_counts": dict(
            sorted(Counter(row["source_component"] for row in rows if row.get("source_component")).items())
        ),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "system_surface_counts": dict(sorted(Counter(row["system_surface"] for row in rows).items())),
        "r_evidence_class_counts": dict(
            sorted(Counter(row["r_evidence_class"] for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "market_counts": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
        "timeframe_counts": dict(
            sorted(Counter(row["market_timeframe"] for row in rows if row.get("market_timeframe")).items())
        ),
        "route_session_counts": dict(
            sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
        ),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
        "horizon_id_counts": dict(
            sorted(Counter(row["horizon_id"] for row in rows if row.get("horizon_id")).items())
        ),
        "coverage_counts": {
            "symbols": dict(sorted(Counter(row["symbol"] for row in rows if row.get("symbol")).items())),
            "markets": dict(sorted(Counter(row["market"] for row in rows if row.get("market")).items())),
            "source_symbols": dict(
                sorted(Counter(row["source_symbol"] for row in rows if row.get("source_symbol")).items())
            ),
            "timeframes": dict(
                sorted(Counter(row["market_timeframe"] for row in rows if row.get("market_timeframe")).items())
            ),
            "sessions": dict(
                sorted(Counter(row["route_session"] for row in rows if row.get("route_session")).items())
            ),
            "sides": dict(sorted(Counter(row["side"] for row in rows if row.get("side")).items())),
            "entry_variants": dict(
                sorted(Counter(row["entry_variant"] for row in rows if row.get("entry_variant")).items())
            ),
            "target_stop_order_classes": dict(
                sorted(
                    Counter(
                        row["target_stop_order_class"]
                        for row in rows
                        if row.get("target_stop_order_class")
                    ).items()
                )
            ),
            "source_components": dict(
                sorted(Counter(row["source_component"] for row in rows if row.get("source_component")).items())
            ),
            "horizons": dict(
                sorted(Counter(row["horizon_id"] for row in rows if row.get("horizon_id")).items())
            ),
        },
        "blank_anchor_counts": {
            field: count
            for field, count in {
                field: sum(1 for row in rows if not row.get(field))
                for field in ANCHOR_FIELDS
            }.items()
            if count
        },
        "source_artifacts": source_stats,
        "output_rows": _path_text(OUTPUT_ROWS),
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Build rows without writing outputs")
    args = parser.parse_args()
    rows, summary = build_rows()
    if not args.check:
        ROUTE_DIR.mkdir(parents=True, exist_ok=True)
        with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        OUTPUT_SUMMARY.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
