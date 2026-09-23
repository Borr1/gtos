#!/usr/bin/env python3
"""Execute unified implementation-candidate scoring for branch/system transfer.

This builder scores all 386 branch-local candidates and all 400 market-gap
primitive candidates created by the unified execution decision packet. It is a
research-only execution layer: the output changes branch-local implementation
priority/action decisions, not live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_unified_execution_scorer import (
    score_branch_candidate,
    score_market_gap_candidate,
)


PREFIX_INPUT = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION"
UNIFIED_RESULT = ROUTE_DIR / f"{PREFIX_INPUT}_RESULT_2026-05-16.json"
BRANCH_EXECUTION = ROUTE_DIR / f"{PREFIX_INPUT}_BRANCH_EXECUTION_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_CANDIDATE = ROUTE_DIR / f"{PREFIX_INPUT}_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
MARKET_GAP_IMPLEMENTATION = ROUTE_DIR / f"{PREFIX_INPUT}_MARKET_GAP_IMPLEMENTATION_LEDGER_2026-05-16.jsonl"
CONCENTRATION_TRANSFER_TEST = ROUTE_DIR / f"{PREFIX_INPUT}_CONCENTRATION_TRANSFER_TEST_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_SCORE_LEDGER_2026-05-16.jsonl"
MARKET_GAP_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_SCORE_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_SCORE_LEDGER_2026-05-16.jsonl"
SYMBOL_SESSION_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_DECISION_LEDGER_2026-05-16.jsonl"
SOURCE_EXPANSION_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_EXPANSION_EXECUTION_LEDGER_2026-05-16.jsonl"
ENTRY_GEOMETRY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_GEOMETRY_EXECUTION_LEDGER_2026-05-16.jsonl"
AVOID_INVERSE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INVERSE_EXECUTION_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Unified implementation-candidate scoring packet only. It scores all 386 branch-local candidates and "
    "all 400 market-gap primitive candidates from the unified execution decision layer, producing concrete "
    "branch-local scorer, source-expansion, entry-geometry, and avoid/inverse execution actions. It does not "
    "change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, "
    "or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        file_hash = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-SCORING-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": file_hash,
                "status": "HASHED" if file_hash else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 9) if values else None


def score_band(score: float | None) -> str:
    if score is None:
        return "NO_SCORE_AVAILABLE"
    if score >= 0.55:
        return "SCORE_BAND_HIGH"
    if score >= 0.25:
        return "SCORE_BAND_MODERATE"
    if score >= 0.0:
        return "SCORE_BAND_REPAIRABLE"
    if score >= -0.25:
        return "SCORE_BAND_WEAK"
    return "SCORE_BAND_NEGATIVE"


def build_branch_score_rows(branch_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(branch_rows, 1):
        score = score_branch_candidate(row)
        output_rows.append(
            with_common(
                {
                    "branch_candidate_score_id": f"OHLC-GTOS-UNIFIED-SCORING-BRANCH-{index:05d}",
                    "candidate_scope": "BRANCH_LOCAL",
                    "branch_queue_id": row.get("branch_queue_id"),
                    "route_candidate_id": row.get("route_candidate_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "primary_export_family": row.get("primary_export_family"),
                    "side": row.get("side"),
                    "target_stop_contract_id": row.get("target_stop_contract_id"),
                    "entry_variant": row.get("entry_variant"),
                    "unified_execution_decision": row.get("unified_execution_decision"),
                    "implementation_candidate_type": row.get("implementation_candidate_type"),
                    "rstyle_midpoint_mean": row.get("rstyle_midpoint_mean"),
                    "rstyle_proxy_signal_class": row.get("rstyle_proxy_signal_class"),
                    "source_repair_pressure_class": row.get("source_repair_pressure_class"),
                    "execution_pressure_class": row.get("execution_pressure_class"),
                    "target_stop_result": row.get("target_stop_result"),
                    "candidate_score_proxy": score["candidate_score_proxy"],
                    "candidate_score_band": score_band(score["candidate_score_proxy"]),
                    "candidate_score_class": score["candidate_score_class"],
                    "candidate_score_formula": score["candidate_score_formula"],
                    "candidate_next_action": score["candidate_next_action"],
                    "implementation_decision_changed_by_scoring": score["candidate_score_class"]
                    not in {
                        "BRANCH_PROVENANCE_EXCLUDE_FROM_SCALAR_SCORER",
                        "BRANCH_AVOID_OR_KILL_PRESSURE",
                    },
                    "exact_failure_cause": row.get("exact_failure_cause"),
                    "exact_success_cause": row.get("exact_success_cause"),
                    "exact_missing_geometry_or_source_reason": row.get("exact_missing_geometry_or_source_reason"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output_rows


def build_market_gap_score_rows(
    market_gap_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(market_gap_rows, 1):
        score = score_market_gap_candidate(row)
        output_rows.append(
            with_common(
                {
                    "market_gap_candidate_score_id": f"OHLC-GTOS-UNIFIED-SCORING-MARKET-GAP-{index:05d}",
                    "candidate_scope": "MARKET_GAP_PRIMITIVE",
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "market_gap_action_id": row.get("market_gap_action_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("mapped_route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "action_class": row.get("action_class"),
                    "movement_status": row.get("movement_status"),
                    "unified_execution_decision": row.get("unified_execution_decision"),
                    "implementation_candidate_type": row.get("implementation_candidate_type"),
                    "flagged_n": row.get("flagged_n"),
                    "control_n": row.get("control_n"),
                    "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                    "delta_alignment_rate": row.get("delta_alignment_rate"),
                    "nofill_sidecar_status": row.get("nofill_sidecar_status"),
                    "residual_transfer_class": row.get("residual_transfer_class"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    "candidate_score_proxy": score["candidate_score_proxy"],
                    "candidate_score_band": score_band(score["candidate_score_proxy"]),
                    "candidate_score_class": score["candidate_score_class"],
                    "candidate_score_formula": score["candidate_score_formula"],
                    "candidate_next_action": score["candidate_next_action"],
                    "additional_flagged_rows_needed_for_n20": score["additional_flagged_rows_needed_for_n20"],
                    "flagged_to_control_ratio": score["flagged_to_control_ratio"],
                },
                generated_at,
                manifest_hash,
            )
        )
    return output_rows


def build_implementation_score_rows(
    implementation_rows: list[dict[str, Any]],
    branch_scores: list[dict[str, Any]],
    market_gap_scores: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    branch_by_id = {row.get("branch_queue_id"): row for row in branch_scores}
    market_gap_by_id = {row.get("market_gap_combo_id"): row for row in market_gap_scores}
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(implementation_rows, 1):
        if row.get("candidate_scope") == "BRANCH_LOCAL":
            score_row = branch_by_id.get(row.get("branch_queue_id"), {})
        else:
            score_row = market_gap_by_id.get(row.get("market_gap_combo_id"), {})
        output_rows.append(
            with_common(
                {
                    "implementation_score_id": f"OHLC-GTOS-UNIFIED-SCORING-IMPL-{index:05d}",
                    "implementation_candidate_id": row.get("implementation_candidate_id"),
                    "candidate_scope": row.get("candidate_scope"),
                    "branch_queue_id": row.get("branch_queue_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "primary_export_family": row.get("primary_export_family"),
                    "primitive_flag": row.get("primitive_flag"),
                    "implementation_candidate_type": row.get("implementation_candidate_type"),
                    "unified_execution_decision": row.get("unified_execution_decision"),
                    "candidate_score_proxy": score_row.get("candidate_score_proxy"),
                    "candidate_score_band": score_row.get("candidate_score_band"),
                    "candidate_score_class": score_row.get("candidate_score_class"),
                    "candidate_next_action": score_row.get("candidate_next_action") or row.get("same_resource_next_action"),
                    "code_surface": row.get("code_surface"),
                    "builder_surface": row.get("builder_surface"),
                    "scorer_function": row.get("scorer_function"),
                    "exact_failure_cause": row.get("exact_failure_cause"),
                    "exact_success_cause": row.get("exact_success_cause"),
                    "exact_missing_geometry_or_source_reason": row.get("exact_missing_geometry_or_source_reason"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output_rows


def build_symbol_session_rows(
    branch_scores: list[dict[str, Any]],
    market_gap_scores: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"branch": [], "market_gap": []})
    for row in branch_scores:
        grouped[(str(row.get("symbol")), str(row.get("route_session")))]["branch"].append(row)
    for row in market_gap_scores:
        grouped[(str(row.get("symbol")), str(row.get("route_session")))]["market_gap"].append(row)

    output_rows: list[dict[str, Any]] = []
    for index, ((symbol, route_session), groups) in enumerate(sorted(grouped.items()), 1):
        branch_group = groups["branch"]
        market_group = groups["market_gap"]
        score_values = [
            float(row["candidate_score_proxy"])
            for row in branch_group + market_group
            if row.get("candidate_score_proxy") is not None
        ]
        output_rows.append(
            with_common(
                {
                    "symbol_session_decision_id": f"OHLC-GTOS-UNIFIED-SCORING-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "branch_score_rows": len(branch_group),
                    "market_gap_score_rows": len(market_group),
                    "all_candidate_rows": len(branch_group) + len(market_group),
                    "candidate_score_proxy_mean": mean_or_none(score_values),
                    "candidate_score_class_counts": compact_counter(Counter(row.get("candidate_score_class") for row in branch_group + market_group)),
                    "unified_execution_decision_counts": compact_counter(Counter(row.get("unified_execution_decision") for row in branch_group + market_group)),
                    "implementation_candidate_type_counts": compact_counter(Counter(row.get("implementation_candidate_type") for row in branch_group + market_group)),
                    "concentration_decision": (
                        "CURRENT_BRANCH_AND_MARKET_GAP_BOTH_PRESENT"
                        if branch_group and market_group
                        else "MARKET_GAP_ONLY_SOURCE_EXPANSION_OR_TRANSFER_TEST"
                        if market_group
                        else "CURRENT_BRANCH_ONLY"
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output_rows


def bucket_rows_from_sources(
    branch_scores: list[dict[str, Any]],
    market_gap_scores: list[dict[str, Any]],
    implementation_scores: list[dict[str, Any]],
    symbol_session_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    sources = {
        "branch_candidate_score_class": Counter(row.get("candidate_score_class") for row in branch_scores),
        "branch_candidate_score_band": Counter(row.get("candidate_score_band") for row in branch_scores),
        "branch_unified_execution_decision": Counter(row.get("unified_execution_decision") for row in branch_scores),
        "market_gap_candidate_score_class": Counter(row.get("candidate_score_class") for row in market_gap_scores),
        "market_gap_candidate_score_band": Counter(row.get("candidate_score_band") for row in market_gap_scores),
        "market_gap_action_class": Counter(row.get("action_class") for row in market_gap_scores),
        "implementation_candidate_scope": Counter(row.get("candidate_scope") for row in implementation_scores),
        "implementation_candidate_score_class": Counter(row.get("candidate_score_class") for row in implementation_scores),
        "symbol_session_concentration_decision": Counter(row.get("concentration_decision") for row in symbol_session_rows),
    }
    distributions = {name: compact_counter(counter) for name, counter in sources.items()}
    rows: list[dict[str, Any]] = []
    for category, counter in distributions.items():
        for value, count in counter.items():
            rows.append(
                with_common(
                    {
                        "candidate_scoring_bucket_id": f"OHLC-GTOS-UNIFIED-SCORING-BUCKET-{len(rows) + 1:05d}",
                        "bucket_category": category,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return rows, distributions


def append_manifest(generated_files: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    manifest.setdefault("files", [])
    existing = {entry.get("path") for entry in manifest["files"]}
    for path in generated_files:
        rel = path.relative_to(REPO).as_posix()
        if rel in existing:
            continue
        manifest["files"].append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "route": PREFIX,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest.setdefault("routes", {})[PREFIX] = {
        "result_path": RESULT_PATH.relative_to(REPO).as_posix(),
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "unified_candidate_scoring_executed",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": (
            "Scored all 386 branch-local and 400 market-gap implementation candidates into direct branch, "
            "source-expansion, entry-geometry, and avoid/inverse execution actions."
        ),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        UNIFIED_RESULT,
        BRANCH_EXECUTION,
        IMPLEMENTATION_CANDIDATE,
        MARKET_GAP_IMPLEMENTATION,
        CONCENTRATION_TRANSFER_TEST,
        REPO / "src/research_infra/moonshot_unified_execution_scorer.py",
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    unified_result = read_json(UNIFIED_RESULT)
    branch_rows = read_jsonl(BRANCH_EXECUTION)
    implementation_rows = read_jsonl(IMPLEMENTATION_CANDIDATE)
    market_gap_rows = read_jsonl(MARKET_GAP_IMPLEMENTATION)

    branch_score_rows = build_branch_score_rows(branch_rows, generated_at, manifest_hash)
    market_gap_score_rows = build_market_gap_score_rows(market_gap_rows, generated_at, manifest_hash)
    implementation_score_rows = build_implementation_score_rows(
        implementation_rows, branch_score_rows, market_gap_score_rows, generated_at, manifest_hash
    )
    symbol_session_rows = build_symbol_session_rows(branch_score_rows, market_gap_score_rows, generated_at, manifest_hash)
    source_expansion_rows = [
        row for row in market_gap_score_rows if row.get("candidate_score_class", "").startswith("MARKET_GAP_SOURCE_EXPANSION")
    ]
    entry_geometry_rows = [
        row for row in market_gap_score_rows if row.get("candidate_score_class", "").startswith("MARKET_GAP_ENTRY_GEOMETRY")
    ]
    avoid_inverse_rows = [
        row for row in market_gap_score_rows if row.get("candidate_score_class") == "MARKET_GAP_AVOID_INVERSE_SCORE_NOW"
    ]
    bucket_rows, distributions = bucket_rows_from_sources(
        branch_score_rows, market_gap_score_rows, implementation_score_rows, symbol_session_rows, generated_at, manifest_hash
    )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-UNIFIED-SCORING-Q-001",
            "question": "Which branch-local candidates should be scored as market-entry challengers before any retest-limit revival?",
            "answer_route": "Use BRANCH_MARKET_ENTRY_CHALLENGER_SCORE_NOW rows and compare against retest/no-fill controls.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-SCORING-Q-002",
            "question": "Which market-gap rows need source expansion before branch scoring?",
            "answer_route": "Use MARKET_GAP_SOURCE_EXPANSION_* rows with additional_flagged_rows_needed_for_n20.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-SCORING-Q-003",
            "question": "Which non-current markets deserve immediate entry-geometry challenger scoring?",
            "answer_route": "Use MARKET_GAP_ENTRY_GEOMETRY_* rows, preserving mixed alignment controls.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-SCORING-Q-004",
            "question": "Which weak market-gap primitives should become avoid or inverse controls?",
            "answer_route": "Use MARKET_GAP_AVOID_INVERSE_SCORE_NOW rows.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-SCORING-Q-005",
            "question": "Does GBPJPY/XAUUSD concentration remain a branch-only boundary after scoring?",
            "answer_route": "No. Symbol/session scoring preserves 28 rows including market-gap-only sessions outside current concentration.",
        },
    ]
    question_rows = [with_common(row, generated_at, manifest_hash) for row in question_rows]

    generated_files = [
        BRANCH_SCORE_LEDGER,
        MARKET_GAP_SCORE_LEDGER,
        IMPLEMENTATION_SCORE_LEDGER,
        SYMBOL_SESSION_DECISION_LEDGER,
        SOURCE_EXPANSION_EXECUTION_LEDGER,
        ENTRY_GEOMETRY_EXECUTION_LEDGER,
        AVOID_INVERSE_EXECUTION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    counts = {
        "input_unified_branch_rows": len(branch_rows),
        "input_implementation_candidate_rows": len(implementation_rows),
        "input_market_gap_rows": len(market_gap_rows),
        "branch_score_rows": len(branch_score_rows),
        "market_gap_score_rows": len(market_gap_score_rows),
        "implementation_score_rows": len(implementation_score_rows),
        "symbol_session_decision_rows": len(symbol_session_rows),
        "source_expansion_execution_rows": len(source_expansion_rows),
        "entry_geometry_execution_rows": len(entry_geometry_rows),
        "avoid_inverse_execution_rows": len(avoid_inverse_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
    }
    system_decision = {
        "branch_score_class_counts": distributions["branch_candidate_score_class"],
        "market_gap_score_class_counts": distributions["market_gap_candidate_score_class"],
        "implementation_scope_counts": distributions["implementation_candidate_scope"],
        "system_recommendation": (
            "UNIFIED_CANDIDATE_SCORING_RESULT: execute branch market-entry challenger scoring, market-gap "
            "source expansion, market-gap entry-geometry scoring, and market-gap avoid/inverse controls from "
            "the full 786-row implementation-candidate denominator."
        ),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {"unified_execution": unified_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }

    write_jsonl(BRANCH_SCORE_LEDGER, branch_score_rows)
    write_jsonl(MARKET_GAP_SCORE_LEDGER, market_gap_score_rows)
    write_jsonl(IMPLEMENTATION_SCORE_LEDGER, implementation_score_rows)
    write_jsonl(SYMBOL_SESSION_DECISION_LEDGER, symbol_session_rows)
    write_jsonl(SOURCE_EXPANSION_EXECUTION_LEDGER, source_expansion_rows)
    write_jsonl(ENTRY_GEOMETRY_EXECUTION_LEDGER, entry_geometry_rows)
    write_jsonl(AVOID_INVERSE_EXECUTION_LEDGER, avoid_inverse_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Candidate Scoring",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch score rows: `{counts['branch_score_rows']}`",
                f"- Market-gap score rows: `{counts['market_gap_score_rows']}`",
                f"- Implementation score rows: `{counts['implementation_score_rows']}`",
                f"- Source-expansion execution rows: `{counts['source_expansion_execution_rows']}`",
                f"- Entry-geometry execution rows: `{counts['entry_geometry_execution_rows']}`",
                f"- Avoid/inverse execution rows: `{counts['avoid_inverse_execution_rows']}`",
                "",
                "Core result: every unified implementation candidate now has a deterministic score class and next action.",
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
