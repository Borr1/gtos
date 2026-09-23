#!/usr/bin/env python3
"""Build survivor-failure proxy runtime rows for GTOS vNext."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
OUTPUT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)

DATE = "2026-05-18"
IMPLEMENTATION_DECISION_PATH = (
    SOURCE_DIR / "MAIN_ORCH24_SURVIVOR_FAILURE_IMPLEMENTATION_DECISION_LEDGER_2026-05-16.jsonl"
)
IMPLICATION_QUEUE_PATH = (
    SOURCE_DIR / "MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_LEDGER_2026-05-16.jsonl"
)
SUPPORT_PATHS = (
    SOURCE_DIR / "build_main_orchestrator_survivor_failure_implication_queue_2026_05_16.py",
    IMPLEMENTATION_DECISION_PATH,
    IMPLICATION_QUEUE_PATH,
    SOURCE_DIR / "MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_OUTPUT_MANIFEST_2026-05-16.json",
    SOURCE_DIR / "MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_SUMMARY_2026-05-16.json",
    SOURCE_DIR / "MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_VERIFICATION_RESULT_2026-05-16.json",
    SOURCE_DIR / "verify_main_orchestrator_survivor_failure_implication_queue_2026_05_16.py",
)
OUTPUT_ROWS_PATH = (
    OUTPUT_DIR / f"GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY_PATH = (
    OUTPUT_DIR / f"GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_SUMMARY_{DATE}.json"
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _normalized(value: Any) -> str:
    if value in (None, "None"):
        return ""
    return str(value).strip()


def _snake(value: Any) -> str:
    text = _normalized(value).lower()
    cleaned = []
    last_sep = False
    for char in text:
        if char.isalnum():
            cleaned.append(char)
            last_sep = False
        elif not last_sep:
            cleaned.append("_")
            last_sep = True
    return "".join(cleaned).strip("_")


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any]:
    if isinstance(value, (int, float)):
        return {
            "count": 1,
            "max": float(value),
            "mean": float(value),
            "min": float(value),
            "negative_rows": 1 if value < 0 else 0,
            "positive_rows": 1 if value > 0 else 0,
            "source_field": source_field,
            "source_shape": "survivor_failure_proxy_r",
            "sum": float(value),
            "zero_rows": 1 if value == 0 else 0,
        }
    return {
        "count": 0,
        "max": None,
        "mean": None,
        "min": None,
        "negative_rows": 0,
        "positive_rows": 0,
        "source_field": source_field,
        "source_shape": "missing",
        "sum": None,
        "zero_rows": 0,
    }


def _decision(row: dict[str, Any]) -> str:
    bucket = _normalized(row.get("bucket")).upper()
    decision = _normalized(row.get("decision")).upper()
    if bucket == "IMPLEMENTATION_CANDIDATE_WITH_EXISTING_NUMERIC_SUPPORT":
        return "FOLLOW"
    if decision == "PRESERVE_OR_REPLAY_WITH_CONTROLS":
        return "FOLLOW"
    if bucket == "KILL_OR_AVOID_WITH_EVIDENCE":
        return "AVOID"
    if decision == "KILL_OR_AVOID_WITH_EVIDENCE":
        return "AVOID"
    return "MIXED"


def _action_class(decision: str) -> str:
    if decision == "FOLLOW":
        return "survivor_failure_follow_scorer"
    if decision == "AVOID":
        return "survivor_failure_avoid_filter"
    return "survivor_failure_context_guard"


def _source_rows_represented(row: dict[str, Any]) -> int:
    evidence = row.get("source_evidence") or row.get("evidence") or {}
    counts = evidence.get("proxy_outcome_counts") if isinstance(evidence, dict) else {}
    if isinstance(counts, dict):
        value = counts.get("evidence_weight_rows")
        if isinstance(value, int) and value > 0:
            return value
    return 1


def _runtime_rows() -> list[dict[str, Any]]:
    implication_rows = _read_jsonl(IMPLICATION_QUEUE_PATH)
    implication_sha = _sha256(IMPLICATION_QUEUE_PATH)
    impl_sha = _sha256(IMPLEMENTATION_DECISION_PATH)
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(implication_rows, start=1):
        row_id = f"GTOS-VNEXT-SURVIVOR-FAILURE-{idx:06d}"
        source_row_id = row.get("row_id") or row.get("decision_id") or row.get("source_decision_id") or row_id
        decision = _decision(row)
        symbol = _normalized(row.get("symbol"))
        session = _normalized(row.get("session"))
        if symbol and not session:
            session = "ALL_SESSIONS"
        family = _normalized(row.get("family"))
        source_rows = _source_rows_represented(row)
        source_evidence = row.get("source_evidence") or row.get("evidence") or {}
        proxy_counts = (
            source_evidence.get("proxy_outcome_counts")
            if isinstance(source_evidence, dict)
            else {}
        )
        runtime_row = {
            "survivor_failure_runtime_row_id": row_id,
            "row_key": row_id,
            "source_row_id": source_row_id,
            "schema_version": "gtos_vnext_survivor_failure_runtime_v1",
            "evidence_family": "gtos_vnext_survivor_failure_runtime",
            "source_name": "main_orch24_survivor_failure",
            "source_group": "survivor_failure_implication_queue",
            "source_role": "survivor_failure_proxy_decision",
            "source_component": "survivor_failure_proxy",
            "source_path": _repo_path(IMPLICATION_QUEUE_PATH),
            "source_artifact": _repo_path(IMPLICATION_QUEUE_PATH),
            "source_file_sha256": "",
            "source_artifact_sha256": implication_sha,
            "declared_origin_artifact": _repo_path(IMPLEMENTATION_DECISION_PATH),
            "declared_origin_sha256": impl_sha,
            "declared_origin_line_no": row.get("source_line_no"),
            "source_line_no": idx,
            "source_symbol": symbol,
            "symbol": symbol,
            "market": symbol,
            "route_session": session,
            "session": session,
            "side": "",
            "timeframe": "",
            "market_timeframe": "",
            "horizon_id": "",
            "entry_variant": _snake(family),
            "primitive": "",
            "route_family": "survivor_failure_proxy",
            "target_stop_order_class": "",
            "decision": decision,
            "review_action": decision,
            "action_class": _action_class(decision),
            "implementation_action": row.get("decision") or row.get("bucket"),
            "runtime_effect_now": (
                "survivor_failure_avoid_pressure"
                if decision == "AVOID"
                else "survivor_failure_follow_pressure"
                if decision == "FOLLOW"
                else "survivor_failure_context_pressure"
            ),
            "runtime_score_allowed": decision == "FOLLOW",
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "live_effect": False,
            "validation_safe": False,
            "bucket": row.get("bucket"),
            "source_decision": row.get("decision"),
            "source_result_id": row.get("source_result_id"),
            "proxy_r_conservative": row.get("proxy_r_conservative"),
            "proxy_r_midpoint": row.get("proxy_r_midpoint"),
            "proxy_r_optimistic": row.get("proxy_r_optimistic"),
            "r_evidence_class": (
                "SURVIVOR_FAILURE_POSITIVE_PROXY_R"
                if decision == "FOLLOW"
                else "SURVIVOR_FAILURE_NEGATIVE_PROXY_R"
                if decision == "AVOID"
                else "SURVIVOR_FAILURE_CONTEXT_PROXY_R"
            ),
            "r_metrics": {
                "effective_n": _metric(source_rows, source_field="proxy_outcome_counts.evidence_weight_rows"),
                "proxy_score": _metric(row.get("proxy_r_midpoint"), source_field="proxy_r_midpoint"),
                "stress_simulated_r": _metric(row.get("proxy_r_conservative"), source_field="proxy_r_conservative"),
                "cost_adjusted_simulated_r": _metric(row.get("proxy_r_optimistic"), source_field="proxy_r_optimistic"),
            },
            "source_rows_represented": source_rows,
            "source_event_rows": source_rows,
            "proxy_outcome_counts": proxy_counts if isinstance(proxy_counts, dict) else {},
            "system_implication_tags": row.get("system_implication_tags") or [],
            "queue_classes": row.get("queue_classes") or [],
            "row_type": row.get("row_type") or "SOURCE_DECISION_ROW",
        }
        rows.append(runtime_row)
    return rows


def _counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_normalized(row.get(field)) for row in rows)
    counts.pop("", None)
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    anchors = (
        "symbol",
        "source_symbol",
        "market",
        "route_session",
        "side",
        "timeframe",
        "market_timeframe",
        "horizon_id",
        "entry_variant",
        "primitive",
        "target_stop_order_class",
    )
    return {
        field: sum(1 for row in rows if _normalized(row.get(field)) == "")
        for field in anchors
        if sum(1 for row in rows if _normalized(row.get(field)) == "")
    }


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_by_path = Counter(row["source_path"] for row in rows)
    artifacts = []
    for path in SUPPORT_PATHS:
        artifacts.append(
            {
                "path": _repo_path(path),
                "rows": _line_count(path),
                "runtime_rows_read": runtime_by_path.get(_repo_path(path), 0),
                "sha256_or_git_blob": _sha256(path) if path.exists() else "",
                "suffix": path.suffix,
            }
        )
    return artifacts


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifacts(rows)
    return {
        "schema_version": "gtos_vnext_survivor_failure_runtime_summary_v1",
        "wave_id": "WAVE_MAIN_ORCH24_SURVIVOR_FAILURE_RUNTIME",
        "output_rows": _repo_path(OUTPUT_ROWS_PATH),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(int(row.get("source_rows_represented") or 0) for row in rows),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": sum(item["rows"] for item in source_artifacts),
        "decision_counts": _counts(rows, "decision"),
        "bucket_counts": _counts(rows, "bucket"),
        "source_decision_counts": _counts(rows, "source_decision"),
        "action_class_counts": _counts(rows, "action_class"),
        "r_evidence_class_counts": _counts(rows, "r_evidence_class"),
        "coverage_counts": {
            "symbols": _counts(rows, "symbol"),
            "markets": _counts(rows, "market"),
            "source_symbols": _counts(rows, "source_symbol"),
            "sessions": _counts(rows, "route_session"),
            "sides": _counts(rows, "side"),
            "timeframes": _counts(rows, "timeframe"),
            "entry_variants": _counts(rows, "entry_variant"),
            "target_stop_order_classes": _counts(rows, "target_stop_order_class"),
        },
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
    }


def build(*, check: bool = False) -> dict[str, Any]:
    rows = _runtime_rows()
    summary = _summary(rows)
    row_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if check:
        if not OUTPUT_ROWS_PATH.exists():
            raise SystemExit(f"missing output rows: {OUTPUT_ROWS_PATH}")
        if not OUTPUT_SUMMARY_PATH.exists():
            raise SystemExit(f"missing output summary: {OUTPUT_SUMMARY_PATH}")
        if OUTPUT_ROWS_PATH.read_text(encoding="utf-8") != row_text:
            raise SystemExit(f"stale output rows: {OUTPUT_ROWS_PATH}")
        if OUTPUT_SUMMARY_PATH.read_text(encoding="utf-8") != summary_text:
            raise SystemExit(f"stale output summary: {OUTPUT_SUMMARY_PATH}")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_ROWS_PATH.write_text(row_text, encoding="utf-8")
        OUTPUT_SUMMARY_PATH.write_text(summary_text, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))


if __name__ == "__main__":
    main()
