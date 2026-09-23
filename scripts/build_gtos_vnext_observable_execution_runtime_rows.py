#!/usr/bin/env python3
"""Build compact runtime rows for branch-local observable execution evidence."""

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
WAVE_ID = "WAVE_OBSERVABLE_EXECUTION_SCORER_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_OBSERVABLE_EXECUTION_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_OBSERVABLE_EXECUTION_RUNTIME_SUMMARY_{DATE}.json"

PRIMARY_SOURCE_NAMES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_UNIFIED_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE_UNIFIED_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_UNIFIED_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl",
)
SUPPORT_SOURCE_NAMES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_HORIZON_WORK_ORDER_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_OBSERVABLE_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_EXECUTION_DECISION_BUNDLE_SOURCE_POLICY_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE_COVERAGE_CARRYFORWARD_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_CONTROL_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_COVERAGE_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_HORIZON_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_SOURCE_EXECUTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE_SOURCE_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl",
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


def _first_numeric(*values: Any) -> float | None:
    for value in values:
        numeric = _to_float(value)
        if numeric is not None:
            return numeric
    return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    name = path.name
    if "OBSERVABLE_EXECUTION_DECISION_BUNDLE" in name:
        return "observable_execution_decision"
    if "OBSERVABLE_REPAIR_EXECUTION_BUNDLE" in name:
        return "observable_repair_execution"
    return "observable_scorer_execution"


def _symbol(row: dict[str, Any]) -> str:
    return _norm(row.get("symbol") or row.get("scope_symbol"))


def _session(row: dict[str, Any]) -> str:
    return _norm(row.get("route_session") or row.get("scope_session") or row.get("session_bucket"))


def _horizon(row: dict[str, Any]) -> str:
    return _norm(row.get("horizon_id") or row.get("scope_horizon"))


def _primitive(row: dict[str, Any]) -> str:
    return _norm(row.get("primitive_flag") or row.get("scope_primitive"))


def _text_blob(row: dict[str, Any]) -> str:
    keys = (
        "execution_decision",
        "execution_permission",
        "execution_status",
        "execution_stage",
        "input_implementation_status",
        "repair_execution_decision",
        "repair_execution_status",
        "repair_execution_result_class",
        "runtime_decision",
        "runtime_work_status",
        "scorer_execution_decision",
        "scorer_execution_status",
        "input_module_materialization_decision",
        "input_module_materialization_status",
    )
    return " ".join(_norm(row.get(key)).upper() for key in keys)


def _decision_shape(row: dict[str, Any], source_kind: str) -> tuple[str, str, str, str, str, str, str]:
    blob = _text_blob(row)
    source_repair = (
        _truthy(row.get("source_repair_required"))
        or _truthy(row.get("source_repair_requirement_open"))
        or _truthy(row.get("runtime_source_repair_required"))
        or "SOURCE_REPAIR" in blob
        or "EXACT_SOURCE" in blob
    )
    horizon_repair = "HORIZON_REBUILD" in blob or "HORIZON_REPAIR" in blob
    control_required = _truthy(row.get("control_required")) or "CONTROL_SCOPE" in blob
    denominator_guard = "DENOMINATOR" in blob
    negative = (
        _truthy(row.get("fail_if_negative_persists"))
        or "ZERO_OR_NEGATIVE" in blob
        or "KILL_IF_NEGATIVE" in blob
    )
    positive = (
        "CONTROLLED_POSITIVE_DELTA" in blob
        or "CONTROLLED_CHALLENGER_SCORE" in blob
        or "GUARDED_OBSERVABLE" in blob
        or "REGISTER_WITH_DENOMINATOR_GUARD" in blob
        or (
            "SOURCE_PROXY" in blob
            and not source_repair
            and not "AMBIGUOUS" in blob
        )
    )

    if negative:
        return (
            "AVOID",
            "observable_execution_avoid_filter",
            "observable_execution_avoid_filter",
            "OBSERVABLE_EXECUTION_NEGATIVE_PROXY_OR_KILL_GUARD",
            "observable_execution_avoid_guard",
            "observable_execution_avoid_guard",
            "observable_execution_avoid_filter",
        )
    if source_repair:
        return (
            "MIXED",
            "observable_execution_source_repair",
            "observable_execution_source_repair_guard",
            "SOURCE_REPAIR_FOR_EXACT_R",
            "source_repair_proof",
            "source_repair_execution_plan",
            "source_repair_proof",
        )
    if horizon_repair:
        return (
            "MIXED",
            "observable_execution_horizon_repair",
            "observable_execution_horizon_repair_guard",
            "OBSERVABLE_EXECUTION_HORIZON_REPAIR",
            "context_guard_input",
            "observable_execution_context_guard",
            "context_guard_input",
        )
    if positive:
        return (
            "FOLLOW",
            "observable_execution_follow_scorer",
            "observable_execution_follow_scorer",
            "OBSERVABLE_EXECUTION_POSITIVE_PROXY",
            "observable_execution_follow_scorer",
            "observable_execution_follow_scorer",
            "observable_execution_scorer_runtime",
        )
    if denominator_guard:
        component = "observable_execution_denominator_guard"
    elif control_required or "CONTROL" in blob:
        component = "observable_execution_control_guard"
    elif "SOURCE_POLICY" in blob or "AMBIGUOUS_PROXY" in blob:
        component = "observable_execution_source_policy_guard"
    else:
        component = f"{source_kind}_context_guard"
    return (
        "MIXED",
        component,
        "observable_execution_context_guard",
        "OBSERVABLE_EXECUTION_CONTEXT_GUARD",
        "context_guard_input",
        "observable_execution_context_guard",
        "context_guard_input",
    )


def _proxy_r_class(row: dict[str, Any], decision: str) -> str:
    if decision == "AVOID":
        return "STRONG_NEGATIVE_PROXY_R"
    score = _first_numeric(
        row.get("proxy_r_style_score_delta"),
        row.get("expectancy_style_proxy_delta"),
        row.get("scorer_proxy_score"),
        row.get("source_proxy_score"),
        row.get("horizon_proxy_score"),
        row.get("control_proxy_score_mean"),
    )
    if score is None:
        return ""
    if score >= 0.35:
        return "STRONG_POSITIVE_PROXY_R"
    if score > 0.0:
        return "POSITIVE_PROXY_R"
    if score < 0.0:
        return "STRONG_NEGATIVE_PROXY_R"
    return "NEGATIVE_PROXY_R"


def _effective_n(row: dict[str, Any]) -> float:
    values = [
        _to_float(row.get(field))
        for field in (
            "control_match_count",
            "denominator_guard_match_count",
            "exact_control_count",
            "selected_control_count",
            "same_symbol_control_count",
            "same_symbol_session_control_count",
            "duplicate_repair_scope_count",
        )
    ]
    values = [value for value in values if value is not None]
    return max(values) if values else 1.0


def _metrics(row: dict[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    proxy = _first_numeric(
        row.get("scorer_proxy_score"),
        row.get("source_proxy_score"),
        row.get("horizon_proxy_score"),
        row.get("control_proxy_score_mean"),
    )
    cost_adjusted = _first_numeric(
        row.get("proxy_r_style_score_delta"),
        row.get("expectancy_style_proxy_delta"),
        row.get("source_minus_horizon_proxy_delta"),
    )
    stress = _first_numeric(
        row.get("horizon_proxy_score"),
        row.get("control_scope_execution_score"),
        row.get("guard_strength_score"),
    )
    priority = _first_numeric(row.get("runtime_priority_score"), row.get("execution_priority_score"))
    if proxy is not None:
        metrics["proxy_score"] = proxy
    if cost_adjusted is not None:
        metrics["cost_adjusted_simulated_r"] = cost_adjusted
    if stress is not None:
        metrics["stress_simulated_r"] = stress
    if priority is not None:
        metrics["runtime_priority_score"] = priority
    metrics["effective_n"] = _effective_n(row)
    return metrics


def _runtime_row(
    row: dict[str, Any],
    *,
    line_no: int,
    path: Path,
    source_kind: str,
) -> dict[str, Any]:
    decision, component, action_class, evidence_class, group, role, surface = _decision_shape(row, source_kind)
    symbol = _symbol(row)
    session = _session(row)
    horizon = _horizon(row)
    primitive = _primitive(row)
    source_row_id = (
        _norm(row.get("execution_bundle_row_id"))
        or _norm(row.get("execution_row_id"))
        or _norm(row.get("repair_execution_row_id"))
        or f"{path.name}:{line_no}"
    )
    runtime_row_id = f"observable_execution:{source_kind}:{line_no}:{_sha256_text(source_row_id)[:16]}"
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
        "source_component": component,
    }
    event_scope = {key: value for key, value in event_scope.items() if value}
    payload = {
        "observable_execution_runtime_row_id": runtime_row_id,
        "row_key": runtime_row_id,
        "source_row_id": source_row_id,
        "input_source_row_id": source_row_id,
        "source_name": "gtos_vnext_observable_execution_wave",
        "evidence_family": "gtos_vnext_observable_execution",
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
        "source_bound": bool(symbol and session and horizon),
        "source_path": _path_text(path),
        "source_file_sha256": _sha256_file(path),
        "source_line_no": line_no,
        "source_kind": source_kind,
        "source_manifest_hash": _norm(row.get("source_manifest_hash")),
        "observable_scope_key": _norm(row.get("observable_scope_key")),
        "runtime_ready": _truthy(row.get("runtime_ready") or row.get("executable_now")),
        "runtime_source_repair_required": _truthy(
            row.get("runtime_source_repair_required")
            or row.get("source_repair_required")
            or row.get("source_repair_requirement_open")
        ),
        "control_required": _truthy(row.get("control_required") or row.get("runtime_control_required")),
        "denominator_guarded": _truthy(row.get("denominator_guarded")),
        "fail_if_negative_persists": _truthy(row.get("fail_if_negative_persists")),
        "input_execution_decision": _norm(row.get("execution_decision") or row.get("repair_execution_decision")),
        "input_runtime_decision": _norm(row.get("runtime_decision")),
        "input_runtime_work_status": _norm(row.get("runtime_work_status")),
        "input_execution_status": _norm(
            row.get("execution_status")
            or row.get("repair_execution_status")
            or row.get("scorer_execution_status")
        ),
        "proxy_r_class": _proxy_r_class(row, decision),
        "r_metrics": _metrics(row),
    }
    return {key: value for key, value in payload.items() if value not in ("", None)}


def build_runtime_rows() -> list[dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    for name in PRIMARY_SOURCE_NAMES:
        path = _source_path(name)
        source_kind = _source_kind(path)
        for line_no, row in enumerate(_read_jsonl(path), start=1):
            runtime_rows.append(
                _runtime_row(row, line_no=line_no, path=path, source_kind=source_kind)
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
        rows = _line_count(path) if path.exists() else 0
        wave_source_rows += rows
        source_artifacts.append(
            {
                "path": _path_text(path),
                "name": name,
                "sha256_or_git_blob": _sha256_file(path) if path.exists() else "",
                "rows": rows,
                "runtime_rows_read": rows if name in PRIMARY_SOURCE_NAMES else 0,
                "source_role": "primary_runtime_rows" if name in PRIMARY_SOURCE_NAMES else "supporting_sidecar_rows",
            }
        )
    coverage, blank_anchors = _coverage(runtime_rows)
    return {
        "schema_version": "gtos_vnext_observable_execution_runtime_summary_v1",
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
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in runtime_rows).items())),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in runtime_rows).items())),
        "system_surface_counts": dict(sorted(Counter(row["system_surface"] for row in runtime_rows).items())),
        "r_evidence_class_counts": dict(
            sorted(Counter(row["r_evidence_class"] for row in runtime_rows).items())
        ),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in runtime_rows).items())),
        "route_family_counts": dict(sorted(Counter(row["route_family"] for row in runtime_rows).items())),
        "proxy_r_class_counts": dict(
            sorted(Counter(_norm(row.get("proxy_r_class")) for row in runtime_rows if _norm(row.get("proxy_r_class"))).items())
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
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate generated outputs without rewriting.")
    args = parser.parse_args()
    runtime_rows = build_runtime_rows()
    summary = build_summary(runtime_rows)
    if args.check:
        existing_rows = OUTPUT_ROWS.read_text(encoding="utf-8") if OUTPUT_ROWS.exists() else ""
        expected_rows = "".join(json.dumps(row, sort_keys=True) + "\n" for row in runtime_rows)
        existing_summary = OUTPUT_SUMMARY.read_text(encoding="utf-8") if OUTPUT_SUMMARY.exists() else ""
        expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if existing_rows != expected_rows or existing_summary != expected_summary:
            print("Observable execution runtime rows are stale; rerun without --check.", file=sys.stderr)
            return 1
        return 0
    write_outputs(runtime_rows, summary)
    print(
        json.dumps(
            {
                "runtime_rows": len(runtime_rows),
                "wave_source_rows_counted": summary["wave_source_rows_counted"],
                "decision_counts": summary["decision_counts"],
                "blank_anchor_counts": summary["blank_anchor_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
