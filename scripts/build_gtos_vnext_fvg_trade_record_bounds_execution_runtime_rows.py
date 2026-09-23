#!/usr/bin/env python3
"""Build vNext runtime rows for FVG trade-record bounds execution evidence."""

from __future__ import annotations

import os
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


DATE = "2026-05-18"
SOURCE_DATE = "2026-05-17"
WAVE_ID = "WAVE_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_fvg_trade_record_bounds_execution_runtime"
SOURCE_NAME = "gtos_vnext_fvg_trade_record_bounds_execution_wave"
RUNTIME_SURFACE = "fvg_trade_record_bounds_execution_runtime"

BUILDER_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
MAIN_ORCH24_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)

OUTPUT_ROWS = (
    BUILDER_DIR
    / f"GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    BUILDER_DIR
    / f"GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_LEDGER = (
    MAIN_ORCH24_DIR
    / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_LEDGER_{SOURCE_DATE}.jsonl"
)

SOURCE_PATHS = (
    MAIN_ORCH24_DIR / "build_main_orch48_numeric_router_execution_identity_capture_contract_2026_05_18.py",
    MAIN_ORCH24_DIR / "build_main_orch48_numeric_router_future_slippage_lifecycle_emitter_2026_05_18.py",
    MAIN_ORCH24_DIR / "build_main_orch48_numeric_router_slippage_lifecycle_join_audit_2026_05_18.py",
    MAIN_ORCH24_DIR / "build_main_orchestrator_action_after_fvg_trade_record_bounds_repair_2026_05_17.py",
    MAIN_ORCH24_DIR / "build_main_orchestrator_fvg_ob_trade_record_bounds_default_source_materialization_2026_05_17.py",
    SOURCE_LEDGER,
    MAIN_ORCH24_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_OUTPUT_MANIFEST_{SOURCE_DATE}.json",
    MAIN_ORCH24_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_SUMMARY_{SOURCE_DATE}.json",
    MAIN_ORCH24_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_VERIFICATION_RESULT_{SOURCE_DATE}.json",
    MAIN_ORCH24_DIR / "verify_main_orch48_numeric_router_execution_identity_capture_contract_2026_05_18.py",
    MAIN_ORCH24_DIR / "verify_main_orch48_numeric_router_future_slippage_lifecycle_emitter_2026_05_18.py",
    MAIN_ORCH24_DIR / "verify_main_orch48_numeric_router_slippage_lifecycle_join_audit_2026_05_18.py",
    MAIN_ORCH24_DIR / "verify_main_orchestrator_action_after_fvg_trade_record_bounds_repair_2026_05_17.py",
    MAIN_ORCH24_DIR / "verify_main_orchestrator_fvg_ob_trade_record_bounds_default_source_materialization_2026_05_17.py",
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "side",
    "primitive",
    "entry_variant",
    "source_component",
    "action_class",
)

SYMBOL_ALIASES = {
    "US30_cash": "US30",
    "GBPUSD_6B": "GBPUSD",
    "NAS100_NQ": "NAS100",
    "US30_YM": "US30",
    "USDJPY_6J": "USDJPY",
    "XAUUSD_GC": "XAUUSD",
    "XAGUSD_SI": "XAGUSD",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _long_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


@lru_cache(maxsize=None)
def _sha256_file_cached(path_text: str) -> str:
    digest = hashlib.sha256()
    with open(_long_path(Path(path_text)), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_file_cached(str(path))


def _path_text(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(_long_path(path), encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _source_rows_count(path: Path) -> tuple[int | None, bool]:
    if path.suffix.casefold() == ".jsonl":
        return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()), True
    if path.suffix.casefold() == ".json":
        payload = _read_json(path)
        if isinstance(payload, list):
            return len(payload), True
        return 1, True
    return None, False


def _canonical_symbol(symbol: str) -> str:
    return SYMBOL_ALIASES.get(symbol, symbol)


def _canonical_session(row: dict[str, Any]) -> str:
    session = _norm(row.get("route_session"))
    if session:
        return session
    candidate_id = _norm(row.get("candidate_id"))
    if "T00:" in candidate_id or "T01:" in candidate_id or "T02:" in candidate_id:
        return "tokyo_kz"
    if "T07:" in candidate_id or "T08:" in candidate_id or "T09:" in candidate_id:
        return "london_core"
    if "T13:" in candidate_id or "T14:" in candidate_id or "T15:" in candidate_id:
        return "ny_core"
    return "ALL_SESSIONS"


def _row_runtime_class(row: dict[str, Any]) -> tuple[str, str, str, str, str, bool]:
    source_action = _norm(row.get("action_class"))
    proxy_r = _safe_float(row.get("after_proxy_r"))
    status_text = " ".join(
        _norm(row.get(field))
        for field in (
            "coverage_status",
            "branch_decision",
            "current_action",
            "implementation_decision",
        )
    ).casefold()

    if source_action == "KILL":
        return (
            "AVOID",
            "fvg_trade_record_bounds_avoid_filter",
            "fvg_trade_record_bounds_kill_guard",
            "avoid_filter",
            "FVG_TRADE_RECORD_BOUNDS_KILL_OR_NEGATIVE_PROXY",
            True,
        )
    if source_action == "IMPLEMENT_DEFAULT_OFF" and proxy_r is not None and proxy_r > 0:
        return (
            "FOLLOW",
            "fvg_trade_record_bounds_default_off_follow_pressure",
            "fvg_trade_record_bounds_default_off_positive_pressure",
            "follow_pressure",
            "FVG_TRADE_RECORD_BOUNDS_POSITIVE_PROXY",
            True,
        )
    if source_action == "IMPLEMENT_DEFAULT_OFF" and proxy_r is not None and proxy_r < 0:
        return (
            "AVOID",
            "fvg_trade_record_bounds_avoid_filter",
            "fvg_trade_record_bounds_negative_proxy_guard",
            "avoid_filter",
            "FVG_TRADE_RECORD_BOUNDS_NEGATIVE_PROXY",
            True,
        )
    if source_action == "KEEP":
        return (
            "MIXED",
            "fvg_trade_record_bounds_context",
            "fvg_trade_record_bounds_keep_context",
            "context_guard_input",
            "FVG_TRADE_RECORD_BOUNDS_KEEP_CONTEXT",
            True,
        )
    if source_action == "REDESIGN" and any(
        token in status_text for token in ("adverse", "negative")
    ):
        return (
            "AVOID",
            "fvg_trade_record_bounds_avoid_filter",
            "fvg_trade_record_bounds_redesign_negative_guard",
            "avoid_filter",
            "FVG_TRADE_RECORD_BOUNDS_RED_NEEDED_NEGATIVE_PROXY",
            True,
        )
    if source_action in {"REDESIGN", "PRESERVE_REQUIREMENT"}:
        return (
            "MIXED",
            "source_repair_guard",
            "fvg_trade_record_bounds_source_repair_guard",
            "source_repair_proof",
            "SOURCE_REPAIR_FOR_EXACT_R",
            False,
        )
    return (
        "MIXED",
        "fvg_trade_record_bounds_context",
        "fvg_trade_record_bounds_unclassified_context",
        "context_guard_input",
        "FVG_TRADE_RECORD_BOUNDS_CONTEXT",
        True,
    )


def _blank_anchor_fields(row: dict[str, Any]) -> list[str]:
    scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
    return [
        field
        for field in ANCHOR_FIELDS
        if field in scope and _norm(scope.get(field)) == ""
    ]


def _effective_n(proxy_r: float | None) -> dict[str, Any]:
    payload = {
        "source_field": "after_proxy_r",
        "source_shape": "scalar_or_null",
        "count": 1,
        "match_rows_with_metric": 1 if proxy_r is not None else 0,
        "positive_rows": 1 if proxy_r is not None and proxy_r > 0 else 0,
        "negative_rows": 1 if proxy_r is not None and proxy_r < 0 else 0,
        "zero_rows": 1 if proxy_r == 0 else 0,
        "sum": proxy_r if proxy_r is not None else None,
        "mean": proxy_r if proxy_r is not None else None,
    }
    return payload


def build_runtime_rows() -> list[dict[str, Any]]:
    source_sha = _sha256_file(SOURCE_LEDGER)
    rows: list[dict[str, Any]] = []
    for line_no, source in enumerate(_read_jsonl(SOURCE_LEDGER), start=1):
        source_symbol = _norm(source.get("symbol")) or "ALL_MARKETS"
        symbol = _canonical_symbol(source_symbol)
        side = _norm(source.get("side")) or "ALL_SIDES"
        route_session = _canonical_session(source)
        source_component = (
            _norm(source.get("primitive_family"))
            or _norm(source.get("source_capture_surface"))
            or _norm(source.get("strategy_id")).casefold()
            or "fvg_trade_record_bounds"
        )
        proxy_r = _safe_float(source.get("after_proxy_r"))
        before_proxy_r = _safe_float(source.get("before_proxy_r"))
        decision, runtime_action, source_role, source_group, r_class, source_complete = (
            _row_runtime_class(source)
        )
        target_stop_class = (
            "SOURCE_REPAIR_REQUIRED"
            if source_group == "source_repair_proof"
            else "NEGATIVE_PROXY"
            if decision == "AVOID"
            else "POSITIVE_PROXY"
            if decision == "FOLLOW"
            else "CONTEXT_OR_KEEP"
        )
        source_row_id = _norm(source.get("row_id")) or f"line_{line_no}"
        runtime_row_id = f"fvg_trade_record_bounds_execution:{source_row_id}"
        event_scope = {
            "symbol": symbol,
            "source_symbol": source_symbol,
            "market": symbol,
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": route_session,
            "side": side,
            "primitive": "fvg",
            "entry_variant": "fvg_trade_record_bounds",
            "route_family": _norm(source.get("strategy_id")) or source_component,
            "source_component": source_component,
            "action_class": runtime_action,
            "target_stop_order_class": target_stop_class,
        }
        row = {
            "schema_version": "gtos_vnext_fvg_trade_record_bounds_execution_runtime_v1",
            "batch_wave_id": WAVE_ID,
            "fvg_trade_record_bounds_execution_runtime_row_id": runtime_row_id,
            "source_name": SOURCE_NAME,
            "evidence_family": EVIDENCE_FAMILY,
            "system_surface": RUNTIME_SURFACE,
            "source_artifact_path": _path_text(SOURCE_LEDGER),
            "source_artifact_sha256": source_sha,
            "source_line_no": line_no,
            "source_row_id": source_row_id,
            "source_row_key": hashlib.sha256(
                f"{source_row_id}|{source.get('candidate_id')}|{line_no}".encode("utf-8")
            ).hexdigest(),
            "decision": decision,
            "runtime_effect_now": (
                "fvg_trade_record_bounds_avoid_risk_guard"
                if decision == "AVOID"
                else "fvg_trade_record_bounds_follow_pressure"
                if decision == "FOLLOW"
                else "fvg_trade_record_bounds_source_repair_risk_guard"
                if source_group == "source_repair_proof"
                else "fvg_trade_record_bounds_context"
            ),
            "runtime_decision_effect": decision in {"FOLLOW", "AVOID"} or source_group == "source_repair_proof",
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "live_effect": False,
            "production_change_opened_now": False,
            "gate_config_change_now": False,
            "symbol": symbol,
            "source_symbol": source_symbol,
            "symbol_family": resolve_vnext_symbol_family(symbol),
            "market": symbol,
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": route_session,
            "side": side,
            "primitive": "fvg",
            "entry_variant": "fvg_trade_record_bounds",
            "framework": "fvg_fill",
            "route_family": _norm(source.get("strategy_id")) or source_component,
            "source_component": source_component,
            "source_group": source_group,
            "source_role": source_role,
            "action_class": runtime_action,
            "source_action_class": _norm(source.get("action_class")),
            "source_coverage_status": _norm(source.get("coverage_status")),
            "source_current_action": _norm(source.get("current_action")),
            "source_branch_decision": _norm(source.get("branch_decision")),
            "source_capture_surface": _norm(source.get("source_capture_surface")),
            "source_bound": source_complete,
            "source_complete": source_complete,
            "r_evidence_class": r_class,
            "proxy_r_class": (
                "POSITIVE_PROXY"
                if proxy_r is not None and proxy_r > 0
                else "NEGATIVE_PROXY"
                if proxy_r is not None and proxy_r < 0
                else "ZERO_PROXY"
                if proxy_r == 0
                else "SOURCE_REPAIR_REQUIRED"
                if source_group == "source_repair_proof"
                else "NO_PROXY_R"
            ),
            "target_stop_order_class": target_stop_class,
            "before_proxy_r": before_proxy_r,
            "after_proxy_r": proxy_r,
            "proxy_r_delta": _safe_float(source.get("proxy_r_delta")),
            "effective_n": _effective_n(proxy_r),
            "candidate_id": _norm(source.get("candidate_id")),
            "implementation_decision": _norm(source.get("implementation_decision")),
            "implementation_candidate": _norm(source.get("implementation_candidate")),
            "decision_evidence": _norm(source.get("decision_evidence")),
            "scoring_boundary": _norm(source.get("scoring_boundary")),
            "data_requirement_state": _norm(source.get("data_requirement_state")),
            "event_scope": event_scope,
            "anchor_blank_fields": [],
            "replay_r_reference_counted_as_new_main_result": False,
        }
        row["anchor_blank_fields"] = _blank_anchor_fields(row)
        rows.append(row)
    return rows


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = []
    runtime_rows_by_path = Counter(row["source_artifact_path"] for row in rows)
    for path in SOURCE_PATHS:
        if not path.exists():
            source_artifacts.append(
                {
                    "path": _path_text(path),
                    "exists": False,
                    "sha256_or_git_blob": "",
                    "row_count_known": False,
                    "rows": None,
                    "rows_represented": 0,
                    "runtime_rows_read": 0,
                    "source_components": [],
                    "decision_counts": {},
                }
            )
            continue
        count, count_known = _source_rows_count(path)
        artifact_rows = [row for row in rows if row["source_artifact_path"] == _path_text(path)]
        source_artifacts.append(
            {
                "path": _path_text(path),
                "exists": True,
                "sha256_or_git_blob": _sha256_file(path),
                "row_count_known": count_known,
                "rows": count,
                "rows_represented": count if count is not None else 0,
                "runtime_rows_read": runtime_rows_by_path[_path_text(path)],
                "source_components": sorted({row["source_component"] for row in artifact_rows}),
                "decision_counts": dict(Counter(row["decision"] for row in artifact_rows)),
            }
        )

    coverage: dict[str, Counter[str]] = {
        "symbols": Counter(),
        "source_symbols": Counter(),
        "markets": Counter(),
        "timeframes": Counter(),
        "sessions": Counter(),
        "sides": Counter(),
        "source_components": Counter(),
        "action_classes": Counter(),
        "source_action_classes": Counter(),
        "target_stop_order_classes": Counter(),
        "frameworks": Counter(),
    }
    blank = Counter()
    for row in rows:
        coverage["symbols"][row["symbol"]] += 1
        coverage["source_symbols"][row["source_symbol"]] += 1
        coverage["markets"][row["market"]] += 1
        coverage["timeframes"][row["timeframe"]] += 1
        coverage["sessions"][row["route_session"]] += 1
        coverage["sides"][row["side"]] += 1
        coverage["source_components"][row["source_component"]] += 1
        coverage["action_classes"][row["action_class"]] += 1
        coverage["source_action_classes"][row["source_action_class"]] += 1
        coverage["target_stop_order_classes"][row["target_stop_order_class"]] += 1
        coverage["frameworks"][row["framework"]] += 1
        for field in row["anchor_blank_fields"]:
            blank[field] += 1

    source_rows_counted = sum(
        item["rows_represented"] for item in source_artifacts if item["path"] == _path_text(SOURCE_LEDGER)
    )
    return {
        "schema_version": "gtos_vnext_fvg_trade_record_bounds_execution_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_surface": RUNTIME_SURFACE,
        "generated_utc": "2026-05-18T00:00:00Z",
        "runtime_behavior_target": (
            "FVG trade-record-bounds action rows become source-bound runtime "
            "execution evidence: killed rows and negative proxy rows can veto "
            "risk, positive default-off rows exert follow pressure, redesign "
            "and preserved-requirement rows zero risk through source repair, "
            "and keep rows remain scoped context."
        ),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": source_rows_counted,
        "selected_source_unit_count": len(SOURCE_PATHS),
        "wave_source_artifact_count": len(SOURCE_PATHS),
        "wave_source_rows_counted": source_rows_counted,
        "row_count_unknown_unit_count": sum(
            1 for item in source_artifacts if not item["row_count_known"]
        ),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(
            sorted(Counter(row["source_component"] for row in rows).items())
        ),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "source_action_class_counts": dict(
            sorted(Counter(row["source_action_class"] for row in rows).items())
        ),
        "r_evidence_class_counts": dict(
            sorted(Counter(row["r_evidence_class"] for row in rows).items())
        ),
        "proxy_r_class_counts": dict(sorted(Counter(row["proxy_r_class"] for row in rows).items())),
        "coverage_counts": {key: dict(sorted(value.items())) for key, value in coverage.items()},
        "blank_anchor_counts": dict(sorted(blank.items())),
        "source_repair_required_rows": sum(
            row["source_group"] == "source_repair_proof" for row in rows
        ),
        "avoid_veto_rows": sum(row["decision"] == "AVOID" for row in rows),
        "follow_pressure_rows": sum(row["decision"] == "FOLLOW" for row in rows),
        "context_rows": sum(row["source_group"] == "context_guard_input" for row in rows),
        "candidate_use_allowed_now_rows": 0,
        "live_effect_rows": 0,
        "broker_operation_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "runtime_trading_or_live_broker_effect_rows": 0,
        "runtime_candidate_use_permitted_rows": 0,
        "source_artifacts": source_artifacts,
        "output_rows": _path_text(OUTPUT_ROWS),
    }


def write_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = build_runtime_rows()
    summary = build_summary(rows)
    BUILDER_DIR.mkdir(parents=True, exist_ok=True)
    with open(_long_path(OUTPUT_ROWS), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, summary


def check_outputs() -> bool:
    expected_rows = build_runtime_rows()
    expected_summary = build_summary(expected_rows)
    if not OUTPUT_ROWS.exists() or not OUTPUT_SUMMARY.exists():
        print("missing generated output", file=sys.stderr)
        return False
    actual_rows = _read_jsonl(OUTPUT_ROWS)
    actual_summary = _read_json(OUTPUT_SUMMARY)
    if actual_rows != expected_rows:
        print("runtime rows differ from regenerated rows", file=sys.stderr)
        return False
    if actual_summary != expected_summary:
        print("runtime summary differs from regenerated summary", file=sys.stderr)
        return False
    print(json.dumps(expected_summary, sort_keys=True))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return 0 if check_outputs() else 1
    _, summary = write_outputs()
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
