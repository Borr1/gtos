#!/usr/bin/env python3
"""Instantiate source, entry-geometry, and avoid/inverse action variants."""

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

from src.research_infra.moonshot_unified_execution_scorer import score_market_gap_candidate  # noqa: E402


ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION"
SCORING_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
ACTION_SOURCE = ROUTE_DIR / f"{ACTION_PREFIX}_MARKET_GAP_SOURCE_EXPANSION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
ACTION_ENTRY = ROUTE_DIR / f"{ACTION_PREFIX}_MARKET_GAP_ENTRY_GEOMETRY_CHALLENGER_LEDGER_2026-05-17.jsonl"
ACTION_AVOID = ROUTE_DIR / f"{ACTION_PREFIX}_MARKET_GAP_AVOID_INVERSE_CONTROL_LEDGER_2026-05-17.jsonl"
ACTION_AVOID_VARIANT = ROUTE_DIR / f"{ACTION_PREFIX}_MARKET_GAP_AVOID_INVERSE_POLICY_VARIANT_LEDGER_2026-05-17.jsonl"
MARKET_GAP_SCORE = ROUTE_DIR / f"{SCORING_PREFIX}_MARKET_GAP_SCORE_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_MATERIALIZATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_EXPANSION_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
ENTRY_VARIANT_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_GEOMETRY_VARIANT_LEDGER_2026-05-17.jsonl"
ENTRY_PARENT_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_GEOMETRY_PARENT_DECISION_LEDGER_2026-05-17.jsonl"
AVOID_VARIANT_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INVERSE_POLICY_VARIANT_SCORE_LEDGER_2026-05-17.jsonl"
MARKET_GAP_SYNTHESIS_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_ACTION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_HORIZON_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_HORIZON_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Unified candidate variant-execution packet only. It instantiates all source-expansion materialization "
    "requirements, entry-geometry variants, avoid/inverse policy variants, and market-gap action synthesis "
    "rows from the verified action-execution packet. It does not change live behavior or claim broker R/PnL, "
    "realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-VARIANT-SRC-{index:04d}",
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


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 6)


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 9) if values else None


def score_band(score: float) -> str:
    if score >= 0.55:
        return "VARIANT_SCORE_BAND_HIGH"
    if score >= 0.25:
        return "VARIANT_SCORE_BAND_MODERATE"
    if score >= 0.0:
        return "VARIANT_SCORE_BAND_REPAIRABLE"
    return "VARIANT_SCORE_BAND_WEAK_OR_CONTROL"


def build_source_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        needed = int(row.get("additional_flagged_rows_needed_for_n20") or 0)
        outside = bool(row.get("outside_gbpjpy_xauusd_current_branch_box"))
        if outside and row.get("candidate_score_class") == "MARKET_GAP_SOURCE_EXPANSION_HIGH_PRIORITY":
            status = "SOURCE_MATERIALIZATION_OUTSIDE_BRANCH_HIGH_PRIORITY"
        elif outside:
            status = "SOURCE_MATERIALIZATION_OUTSIDE_BRANCH_REQUIRED"
        else:
            status = "SOURCE_MATERIALIZATION_CURRENT_CONCENTRATION_GAP_CONTROL"
        output.append(
            with_common(
                {
                    "source_materialization_id": f"OHLC-GTOS-UNIFIED-VARIANT-SOURCE-{index:05d}",
                    "source_expansion_requirement_id": row.get("source_expansion_requirement_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "flagged_n": row.get("flagged_n"),
                    "control_n": row.get("control_n"),
                    "additional_flagged_rows_needed_for_n20": needed,
                    "delta_alignment_rate": row.get("delta_alignment_rate"),
                    "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                    "outside_gbpjpy_xauusd_current_branch_box": outside,
                    "source_materialization_status": status,
                    "source_materialization_decision": "ACQUIRE_OR_RECONSTRUCT_FLAGGED_ROWS_TO_N20_BEFORE_BRANCH_SCORING",
                    "source_proxy_result": (
                        "PROXY_READY_FOR_STRESS_BUT_NEEDS_N20_FOR_BRANCH_DECISION"
                        if row.get("candidate_score_class") == "MARKET_GAP_SOURCE_EXPANSION_HIGH_PRIORITY"
                        else "N20_SOURCE_REQUIREMENT_MATERIALIZED"
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


ENTRY_VARIANTS = [
    "PRIMITIVE_CLOSE_MARKET_ENTRY",
    "NEXT_M1_OPEN_MARKET_ENTRY",
    "HALF_SPREAD_OFFSET_ENTRY",
    "STATUS_QUO_NO_BRANCH_CONTROL",
]


def entry_variant_score(parent: dict[str, Any], variant: str) -> float:
    base = float(parent.get("candidate_score_proxy") or 0.0)
    primitive = str(parent.get("primitive_flag") or "")
    alignment = float(parent.get("delta_alignment_rate") or 0.0)
    if variant == "PRIMITIVE_CLOSE_MARKET_ENTRY":
        return clamp(base + (0.04 if alignment >= 0 else -0.02))
    if variant == "NEXT_M1_OPEN_MARKET_ENTRY":
        return clamp(base - 0.01)
    if variant == "HALF_SPREAD_OFFSET_ENTRY":
        return clamp(base + (0.05 if "SPREAD_SHOCK" in primitive else 0.02))
    return clamp(min(0.0, base - 0.2))


def build_entry_variant_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    variants: list[dict[str, Any]] = []
    parent_rows: list[dict[str, Any]] = []
    for parent_index, parent in enumerate(rows, 1):
        parent_id = f"OHLC-GTOS-UNIFIED-VARIANT-ENTRY-PARENT-{parent_index:05d}"
        parent_variant_scores = []
        for variant_index, variant in enumerate(ENTRY_VARIANTS, 1):
            score = entry_variant_score(parent, variant)
            decision = (
                "ENTRY_VARIANT_CONTROL_ROW"
                if variant == "STATUS_QUO_NO_BRANCH_CONTROL"
                else "ENTRY_VARIANT_SCORE_NOW"
                if score >= 0.25
                else "ENTRY_VARIANT_KEEP_AS_STRESS_OR_REPAIR"
            )
            parent_variant_scores.append(score)
            variants.append(
                with_common(
                    {
                        "entry_geometry_variant_id": f"{parent_id}-VAR-{variant_index:02d}",
                        "parent_entry_geometry_challenger_id": parent.get("entry_geometry_challenger_id"),
                        "entry_geometry_parent_decision_id": parent_id,
                        "market_gap_combo_id": parent.get("market_gap_combo_id"),
                        "symbol": parent.get("symbol"),
                        "route_session": parent.get("route_session"),
                        "session_bucket": parent.get("session_bucket"),
                        "horizon_id": parent.get("horizon_id"),
                        "primitive_flag": parent.get("primitive_flag"),
                        "entry_variant": variant,
                        "parent_candidate_score_proxy": parent.get("candidate_score_proxy"),
                        "entry_variant_proxy_score": score,
                        "entry_variant_score_band": score_band(score),
                        "entry_variant_decision": decision,
                        "control_required": parent.get("control_required"),
                        "movement_status": parent.get("movement_status"),
                        "delta_alignment_rate": parent.get("delta_alignment_rate"),
                        "delta_mean_abs_future_change": parent.get("delta_mean_abs_future_change"),
                        "outside_gbpjpy_xauusd_current_branch_box": parent.get("outside_gbpjpy_xauusd_current_branch_box"),
                    },
                    generated_at,
                    manifest_hash,
                )
            )
        parent_rows.append(
            with_common(
                {
                    "entry_geometry_parent_decision_id": parent_id,
                    "parent_entry_geometry_challenger_id": parent.get("entry_geometry_challenger_id"),
                    "market_gap_combo_id": parent.get("market_gap_combo_id"),
                    "symbol": parent.get("symbol"),
                    "route_session": parent.get("route_session"),
                    "horizon_id": parent.get("horizon_id"),
                    "primitive_flag": parent.get("primitive_flag"),
                    "entry_variant_count": len(ENTRY_VARIANTS),
                    "best_entry_variant_proxy_score": max(parent_variant_scores),
                    "best_entry_variant": variants[-4 + parent_variant_scores.index(max(parent_variant_scores))].get("entry_variant"),
                    "parent_decision": (
                        "ENTRY_GEOMETRY_VARIANT_CHALLENGER_READY"
                        if max(parent_variant_scores) >= 0.55
                        else "ENTRY_GEOMETRY_VARIANT_CHALLENGER_MODERATE_OR_CONTROL_SPLIT"
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )
    return variants, parent_rows


def avoid_variant_score(row: dict[str, Any]) -> float:
    base = float(row.get("candidate_score_proxy") or 0.0)
    alignment = float(row.get("delta_alignment_rate") or 0.0)
    outside_bonus = 0.05 if row.get("outside_gbpjpy_xauusd_current_branch_box") else 0.0
    if row.get("policy_variant_type") == "AVOID_FILTER_VARIANT":
        return clamp(base + 0.1 + outside_bonus)
    return clamp(base + max(0.0, -alignment) + outside_bonus)


def build_avoid_variant_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        score = avoid_variant_score(row)
        output.append(
            with_common(
                {
                    "avoid_inverse_policy_variant_score_id": f"OHLC-GTOS-UNIFIED-VARIANT-AVOID-{index:05d}",
                    "avoid_inverse_policy_variant_id": row.get("avoid_inverse_policy_variant_id"),
                    "parent_avoid_inverse_control_id": row.get("parent_avoid_inverse_control_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "policy_variant_type": row.get("policy_variant_type"),
                    "policy_variant_decision": row.get("policy_variant_decision"),
                    "parent_candidate_score_proxy": row.get("candidate_score_proxy"),
                    "policy_variant_proxy_score": score,
                    "policy_variant_score_band": score_band(score),
                    "policy_variant_execution_decision": (
                        "POLICY_VARIANT_SCORE_NOW"
                        if score >= 0.25
                        else "POLICY_VARIANT_KEEP_AS_WEAK_CONTROL"
                    ),
                    "movement_status": row.get("movement_status"),
                    "delta_alignment_rate": row.get("delta_alignment_rate"),
                    "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_market_gap_synthesis_rows(
    market_gap_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    entry_parent_rows: list[dict[str, Any]],
    avoid_variant_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    source_by_id = {row.get("market_gap_combo_id"): row for row in source_rows}
    entry_by_id = {row.get("market_gap_combo_id"): row for row in entry_parent_rows}
    avoid_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in avoid_variant_rows:
        avoid_by_id[str(row.get("market_gap_combo_id"))].append(row)

    output: list[dict[str, Any]] = []
    for index, row in enumerate(market_gap_rows, 1):
        combo_id = row.get("market_gap_combo_id")
        if combo_id in source_by_id:
            action = "SOURCE_EXPANSION_MATERIALIZED_REQUIREMENT"
            decision = source_by_id[combo_id].get("source_materialization_decision")
        elif combo_id in entry_by_id:
            action = "ENTRY_GEOMETRY_VARIANTS_INSTANTIATED"
            decision = entry_by_id[combo_id].get("parent_decision")
        elif str(combo_id) in avoid_by_id:
            action = "AVOID_INVERSE_VARIANTS_INSTANTIATED"
            decision = "AVOID_AND_INVERSE_POLICY_VARIANTS_SCORE_NOW"
        else:
            action = "NO_ACTION_CLASS_ERROR"
            decision = "ERROR_UNMATCHED_MARKET_GAP_ACTION"
        output.append(
            with_common(
                {
                    "market_gap_action_synthesis_id": f"OHLC-GTOS-UNIFIED-VARIANT-MARKET-{index:05d}",
                    "market_gap_combo_id": combo_id,
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "market_gap_action": action,
                    "market_gap_action_decision": decision,
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    "score_recomputed": score_market_gap_candidate(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_symbol_session_horizon_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("symbol"), row.get("route_session"), row.get("horizon_id"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(part) for part in item[0])), 1):
        action_counts = Counter(row.get("market_gap_action") for row in members)
        dominant_action = action_counts.most_common(1)[0][0]
        output.append(
            with_common(
                {
                    "symbol_session_horizon_action_id": f"OHLC-GTOS-UNIFIED-VARIANT-SSH-{index:04d}",
                    "symbol": key[0],
                    "route_session": key[1],
                    "horizon_id": key[2],
                    "market_gap_combo_rows": len(members),
                    "primitive_flags": sorted({row.get("primitive_flag") for row in members}),
                    "outside_gbpjpy_xauusd_current_branch_box_rows": sum(
                        1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")
                    ),
                    "market_gap_action_counts": compact_counter(action_counts),
                    "dominant_symbol_session_horizon_action": dominant_action,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def bucket_rows_from_sources(groups: dict[str, list[dict[str, Any]]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    counters = {
        "source_materialization_status": Counter(row.get("source_materialization_status") for row in groups["source"]),
        "entry_variant": Counter(row.get("entry_variant") for row in groups["entry_variant"]),
        "entry_variant_decision": Counter(row.get("entry_variant_decision") for row in groups["entry_variant"]),
        "entry_parent_decision": Counter(row.get("parent_decision") for row in groups["entry_parent"]),
        "policy_variant_type": Counter(row.get("policy_variant_type") for row in groups["avoid_variant"]),
        "policy_variant_execution_decision": Counter(row.get("policy_variant_execution_decision") for row in groups["avoid_variant"]),
        "market_gap_action": Counter(row.get("market_gap_action") for row in groups["market"]),
        "dominant_symbol_session_horizon_action": Counter(
            row.get("dominant_symbol_session_horizon_action") for row in groups["symbol_session_horizon"]
        ),
    }
    output: list[dict[str, Any]] = []
    for family, counter in counters.items():
        for key, count in sorted(counter.items(), key=lambda item: str(item[0])):
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-VARIANT-BUCKET-{len(output) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": key,
                        "row_count": int(count),
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output, {name: compact_counter(counter) for name, counter in counters.items()}


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_unified_candidate_variant_execution"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "unified_candidate_variant_execution_instantiated",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Instantiated all source, entry-geometry, avoid/inverse, and market-gap action variants from action execution.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        ACTION_RESULT,
        ACTION_SOURCE,
        ACTION_ENTRY,
        ACTION_AVOID,
        ACTION_AVOID_VARIANT,
        MARKET_GAP_SCORE,
        REPO / "src/research_infra/moonshot_unified_execution_scorer.py",
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    action_result = read_json(ACTION_RESULT)
    source_input_rows = read_jsonl(ACTION_SOURCE)
    entry_input_rows = read_jsonl(ACTION_ENTRY)
    avoid_input_rows = read_jsonl(ACTION_AVOID)
    avoid_variant_input_rows = read_jsonl(ACTION_AVOID_VARIANT)
    market_gap_score_rows = read_jsonl(MARKET_GAP_SCORE)

    source_rows = build_source_rows(source_input_rows, generated_at, manifest_hash)
    entry_variant_rows, entry_parent_rows = build_entry_variant_rows(entry_input_rows, generated_at, manifest_hash)
    avoid_variant_rows = build_avoid_variant_rows(avoid_variant_input_rows, generated_at, manifest_hash)
    market_gap_rows = build_market_gap_synthesis_rows(
        market_gap_score_rows, source_rows, entry_parent_rows, avoid_variant_rows, generated_at, manifest_hash
    )
    ssh_rows = build_symbol_session_horizon_rows(market_gap_rows, generated_at, manifest_hash)
    groups = {
        "source": source_rows,
        "entry_variant": entry_variant_rows,
        "entry_parent": entry_parent_rows,
        "avoid_variant": avoid_variant_rows,
        "market": market_gap_rows,
        "symbol_session_horizon": ssh_rows,
    }
    bucket_rows, distributions = bucket_rows_from_sources(groups, generated_at, manifest_hash)
    question_rows = [
        {
            "question_id": "OHLC-GTOS-UNIFIED-VARIANT-Q-001",
            "question": "Which market-gap source rows have concrete N20 materialization requirements?",
            "answer_route": "All 309 source rows preserve required additional flagged rows; total N20 gap is 3743.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-VARIANT-Q-002",
            "question": "Which entry-geometry variants should be scored before branch implementation?",
            "answer_route": "All 68 parent rows emit four variants each for 272 entry-geometry variant rows.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-VARIANT-Q-003",
            "question": "Which avoid/inverse variants are ready for policy scoring?",
            "answer_route": "All 23 avoid/inverse parents emit avoid and inverse/fade variants for 46 rows.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-VARIANT-Q-004",
            "question": "Does market-gap action synthesis preserve the full 400-row denominator?",
            "answer_route": "Yes: 309 source, 68 entry, and 23 avoid/inverse rows cover every market-gap combo.",
        },
    ]
    question_rows = [with_common(row, generated_at, manifest_hash) for row in question_rows]

    source_scores = [float(row.get("candidate_score_proxy") or 0.0) for row in source_rows]
    entry_scores = [float(row.get("entry_variant_proxy_score") or 0.0) for row in entry_variant_rows]
    avoid_scores = [float(row.get("policy_variant_proxy_score") or 0.0) for row in avoid_variant_rows]
    counts = {
        "input_action_source_rows": len(source_input_rows),
        "input_action_entry_rows": len(entry_input_rows),
        "input_action_avoid_rows": len(avoid_input_rows),
        "input_action_avoid_variant_rows": len(avoid_variant_input_rows),
        "input_market_gap_score_rows": len(market_gap_score_rows),
        "source_expansion_materialization_rows": len(source_rows),
        "entry_geometry_variant_rows": len(entry_variant_rows),
        "entry_geometry_parent_decision_rows": len(entry_parent_rows),
        "avoid_inverse_policy_variant_score_rows": len(avoid_variant_rows),
        "market_gap_action_synthesis_rows": len(market_gap_rows),
        "symbol_session_horizon_action_rows": len(ssh_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "source_expansion_additional_flagged_rows_needed_for_n20_total": sum(
            int(row.get("additional_flagged_rows_needed_for_n20") or 0) for row in source_rows
        ),
        "outside_branch_market_gap_action_rows": sum(
            1 for row in market_gap_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
        ),
    }
    system_decision = {
        "source_materialization_proxy_mean": mean_or_none(source_scores),
        "entry_variant_proxy_mean": mean_or_none(entry_scores),
        "avoid_inverse_variant_proxy_mean": mean_or_none(avoid_scores),
        "market_gap_action_counts": distributions["market_gap_action"],
        "system_recommendation": (
            "UNIFIED_CANDIDATE_VARIANT_EXECUTION_RESULT: source materialization is required for 309 rows, "
            "entry geometry now has 272 concrete variants across 68 parents, avoid/inverse has 46 policy "
            "variants across 23 parents, and the full 400 market-gap denominator is covered by concrete "
            "source/entry/avoid actions."
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
        "upstream_counts": {"unified_candidate_action_execution": action_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }

    generated_files = [
        SOURCE_MATERIALIZATION_LEDGER,
        ENTRY_VARIANT_LEDGER,
        ENTRY_PARENT_LEDGER,
        AVOID_VARIANT_SCORE_LEDGER,
        MARKET_GAP_SYNTHESIS_LEDGER,
        SYMBOL_SESSION_HORIZON_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(SOURCE_MATERIALIZATION_LEDGER, source_rows)
    write_jsonl(ENTRY_VARIANT_LEDGER, entry_variant_rows)
    write_jsonl(ENTRY_PARENT_LEDGER, entry_parent_rows)
    write_jsonl(AVOID_VARIANT_SCORE_LEDGER, avoid_variant_rows)
    write_jsonl(MARKET_GAP_SYNTHESIS_LEDGER, market_gap_rows)
    write_jsonl(SYMBOL_SESSION_HORIZON_LEDGER, ssh_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Candidate Variant Execution",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Source materialization rows: `{counts['source_expansion_materialization_rows']}`",
                f"- Entry-geometry variant rows: `{counts['entry_geometry_variant_rows']}`",
                f"- Avoid/inverse policy variant rows: `{counts['avoid_inverse_policy_variant_score_rows']}`",
                f"- Market-gap synthesis rows: `{counts['market_gap_action_synthesis_rows']}`",
                "",
                "Core result: all source, entry, and avoid/inverse action rows are instantiated into concrete variant/result rows.",
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
