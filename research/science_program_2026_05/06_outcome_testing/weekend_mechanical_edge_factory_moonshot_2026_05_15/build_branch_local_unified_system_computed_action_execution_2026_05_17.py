#!/usr/bin/env python3
"""Consume unified action results into computed score/source/redesign/code rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_branch_local_unified_system_computed_actions import (
    UNIFIED_SYSTEM_COMPUTED_ACTION_SURFACE,
    computed_action_result,
    computed_action_rollup,
    computed_market_timeframe_expansion_row,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_ACTION_RESULT_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_IMPLEMENTATION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_CONTROL_REPAIR_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_WITH_CONTROL_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_REDESIGN_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REDESIGN_EXECUTION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_AUDIT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_AUDIT_PRESERVATION_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_RESULT_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_EXPANSION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"

SIDE_DEFAULT_APP = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_APPLICATION_BUNDLE_APPLICATION_LEDGER_2026-05-17.jsonl"
SIDE_DEFAULT_SCORE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_APPLICATION_BUNDLE_SCORER_APPLICATION_LEDGER_2026-05-17.jsonl"
SIDE_MARKET_GAP_CODE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_REPLAY_CODE_CANDIDATE_MARKET_GAP_CODE_LEDGER_2026-05-17.jsonl"
SIDE_MARKET_GAP_SCORE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING_MARKET_GAP_SCORE_LEDGER_2026-05-16.jsonl"
SIDE_SHADOW_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE_SOURCE_GUARD_BUNDLE_LEDGER_2026-05-17.jsonl"
SIDE_SHADOW_SCORE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE_SCORE_CONTROL_BUNDLE_LEDGER_2026-05-17.jsonl"
SIDE_SHADOW_GUARD = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE_DENOMINATOR_GUARD_BUNDLE_LEDGER_2026-05-17.jsonl"
SIDE_SHADOW_ENABLE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE_IMPLEMENT_ENABLE_BUNDLE_LEDGER_2026-05-17.jsonl"
SIDE_SHADOW_HORIZON = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE_HORIZON_REPAIR_ACTION_LEDGER_2026-05-17.jsonl"
SIDE_NOFILL_FAMILY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_FAMILY_SYNTHESIS_LEDGER_2026-05-16.jsonl"
SIDE_NOFILL_AVOID = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl"
SIDE_NOFILL_RETEST = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl"
SIDE_NOFILL_SOURCE_CONF = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_SOURCE_CONFIDENCE_BRANCH_LEDGER_2026-05-16.jsonl"
SIDE_NEAR_OFFSET = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl"
SIDE_NEAR_MARKET = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl"
SIDE_NEAR_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_SOURCE_REQUIREMENT_LEDGER_2026-05-16.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_COMPUTED_ACTION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
COMPUTED_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPUTED_ACTION_LEDGER_2026-05-17.jsonl"
COMPUTED_SCORE_DELTA_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPUTED_SCORE_DELTA_LEDGER_2026-05-17.jsonl"
SCORE_WITH_CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_WITH_CONTROL_RESULT_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_SOURCE_REPAIR_LEDGER_2026-05-17.jsonl"
NOFILL_REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_REDESIGN_SCORING_LEDGER_2026-05-17.jsonl"
GUARD_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_REGISTRY_SPEC_LEDGER_2026-05-17.jsonl"
CODE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
AUDIT_ROUTE_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_AUDIT_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
FAMILY_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
MARKET_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TIMEFRAME_DECISION_ROLLUP_LEDGER_2026-05-17.jsonl"
MARKET_EXPANSION_MATRIX_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local unified system computed-action execution bundle. It consumes every unified action-result row into "
    "computed proxy deltas, exact-control/source repair result rows, no-fill redesign scoring rows, guard registry "
    "spec rows, default-off code candidate rows, or current-claim opportunity audit rows. It preserves exact/proxy "
    "source limits and market/timeframe/session/horizon expansion decisions. It does not change live behavior, "
    "place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
)

FAMILY_OUTPUTS = {
    "DEFAULT_OFF_CODE_CANDIDATE": CODE_CANDIDATE_LEDGER,
    "SOURCE_CONTROL_REPAIR": SOURCE_REPAIR_LEDGER,
    "SCORE_WITH_CONTROL": SCORE_WITH_CONTROL_LEDGER,
    "NOFILL_REDESIGN_SCORING": NOFILL_REDESIGN_LEDGER,
    "GUARD_REGISTRY_SPEC": GUARD_SPEC_LEDGER,
    "CURRENT_CLAIM_OPPORTUNITY_AUDIT": AUDIT_ROUTE_LEDGER,
}

SIDECAR_PATHS = [
    SIDE_DEFAULT_APP,
    SIDE_DEFAULT_SCORE,
    SIDE_MARKET_GAP_CODE,
    SIDE_MARKET_GAP_SCORE,
    SIDE_SHADOW_SOURCE,
    SIDE_SHADOW_SCORE,
    SIDE_SHADOW_GUARD,
    SIDE_SHADOW_ENABLE,
    SIDE_SHADOW_HORIZON,
    SIDE_NOFILL_FAMILY,
    SIDE_NOFILL_AVOID,
    SIDE_NOFILL_RETEST,
    SIDE_NOFILL_SOURCE_CONF,
    SIDE_NEAR_OFFSET,
    SIDE_NEAR_MARKET,
    SIDE_NEAR_SOURCE,
]

SIDECAR_ID_FIELDS = (
    "default_off_application_row_id",
    "scorer_application_row_id",
    "market_gap_code_id",
    "bundle_row_id",
    "family_synthesis_id",
    "avoid_filter_branch_id",
    "retest_redesign_branch_id",
    "source_confidence_branch_id",
    "near_miss_entry_control_offset_branch_id",
    "near_miss_entry_control_market_branch_id",
    "near_miss_entry_control_source_requirement_id",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


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
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-COMPUTED-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
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
            "live_effect": False,
        }
    )
    return row


def sidecar_key(row: dict[str, Any]) -> Any:
    for field in SIDECAR_ID_FIELDS:
        if row.get(field):
            return row.get(field)
    return row.get("input_row_id") or row.get("source_row_id")


def build_sidecar_lookup() -> tuple[dict[Any, dict[str, Any]], dict[str, int]]:
    lookup: dict[Any, dict[str, Any]] = {}
    counts: dict[str, int] = {}
    for path in SIDECAR_PATHS:
        rows = read_jsonl(path) if path.exists() else []
        counts[path.name] = len(rows)
        for row in rows:
            key = sidecar_key(row)
            if key and key not in lookup:
                lookup[key] = row
            combo = row.get("market_gap_combo_id")
            if combo and combo not in lookup:
                lookup[combo] = row
    return lookup, counts


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def numeric_present(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row.get(key) is not None)


def build_rollups(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("computed_action_family"),
            )
        ].append(row)
        by_family[
            (
                row.get("computed_action_family"),
                row.get("computed_action_status"),
                row.get("computed_next_action"),
            )
        ].append(row)
        by_market[
            (
                row.get("symbol"),
                row.get("route_session"),
                tuple(row.get("available_timeframes") or []),
                row.get("market_expansion_decision"),
                row.get("tradability_status"),
                row.get("fillability_no_fill_status"),
            )
        ].append(row)
    scope_rollups = [
        with_common(computed_action_rollup(key, by_scope[key], index, "scope_computed_action"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(computed_action_rollup(key, by_family[key], index, "family_status_next_action"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(computed_action_rollup(key, by_market[key], index, "market_timeframe_session_horizon_decision"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_market, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    return scope_rollups, family_rollups, market_rollups


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_branch_local_unified_system_computed_action_execution_bundle"] = {
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
        "event": "branch_local_unified_system_computed_action_execution_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed every unified action-result row into computed score/source/redesign/guard/code-candidate result rows and preserved the full market/timeframe/session/horizon expansion matrix.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_ACTION_LEDGER,
            INPUT_IMPLEMENTATION_LEDGER,
            INPUT_SOURCE_CONTROL_LEDGER,
            INPUT_SCORE_LEDGER,
            INPUT_REDESIGN_LEDGER,
            INPUT_GUARD_LEDGER,
            INPUT_AUDIT_LEDGER,
            INPUT_RECHECK_LEDGER,
            INPUT_MARKET_EXPANSION_LEDGER,
            *SIDECAR_PATHS,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    market_expansion_input_rows = read_jsonl(INPUT_MARKET_EXPANSION_LEDGER)
    sidecars, sidecar_counts = build_sidecar_lookup()
    computed_rows = [
        with_common(computed_action_result(row, index, sidecars.get(row.get("source_row_id"))), generated_at, manifest_hash)
        for index, row in enumerate(action_rows, 1)
    ]
    by_family = {
        family: [row for row in computed_rows if row.get("computed_action_family") == family]
        for family in FAMILY_OUTPUTS
    }
    score_delta_rows = [row for row in computed_rows if row.get("computed_proxy_delta") is not None]
    scope_rollups, family_rollups, market_rollups = build_rollups(computed_rows, generated_at, manifest_hash)
    computed_by_market_expansion: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in computed_rows:
        computed_by_market_expansion[row.get("market_expansion_row_id")].append(row)
    market_expansion_rows = [
        with_common(
            computed_market_timeframe_expansion_row(
                row,
                computed_by_market_expansion.get(row.get("market_timeframe_session_horizon_expansion_row_id"), []),
                index,
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(market_expansion_input_rows, 1)
    ]
    distributions = {
        "computed_action_family": string_counter(computed_rows, "computed_action_family"),
        "computed_action_status": string_counter(computed_rows, "computed_action_status"),
        "computed_proxy_delta_class": string_counter(computed_rows, "computed_proxy_delta_class"),
        "source_component": string_counter(computed_rows, "source_component"),
        "market_expansion_decision": string_counter(computed_rows, "market_expansion_decision"),
        "tradability_status": string_counter(computed_rows, "tradability_status"),
        "fillability_no_fill_status": string_counter(computed_rows, "fillability_no_fill_status"),
        "source_sidecar_joined": string_counter(computed_rows, "source_sidecar_joined"),
        "market_expansion_matrix_decision": string_counter(market_expansion_rows, "decision"),
        "market_expansion_matrix_tradability_status": string_counter(market_expansion_rows, "tradability_status"),
        "market_expansion_matrix_symbol": string_counter(market_expansion_rows, "symbol"),
        "market_expansion_matrix_coverage_source": string_counter(market_expansion_rows, "coverage_source"),
    }
    component_status = Counter(
        f"{row.get('source_component')}|{row.get('computed_action_family')}|{row.get('computed_action_status')}"
        for row in computed_rows
    )
    distributions["source_component_computed_status"] = {key: int(component_status[key]) for key in sorted(component_status)}
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-COMPUTED-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        "Did every action-result row become a computed action row?",
        "Which default-off implementation rows now have computed proxy deltas or code-candidate specs?",
        "Which score-with-control rows joined sidecar scores and which still need exact controls?",
        "Which source/control repair rows are exact-control denominator builds versus source repair or satisfied-source replay attachments?",
        "Which no-fill redesign variants produce target/stop, avoid/inverse, retest, offset, or market-entry proxy rows?",
        "Which guard rows register denominator guards versus no-fill source-confidence guards?",
        "Which current-claim rejection audit rows preserve opportunity paths without deleting the mechanism?",
        "Which market/timeframe/session/horizon rows remain outside current production concentration?",
        "Which rows have exact R unavailable but an honest lower-level proxy delta?",
        "Did the computed layer preserve every work-order market/timeframe/session/horizon expansion matrix row, including data-only and outside-market rows?",
        "What code/spec/source/redesign execution should consume this computed layer next?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-COMPUTED-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by computed action, score/source/redesign/guard/code, rollup, and bucket ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    counts = {
        "input_action_result_rows": len(action_rows),
        "computed_action_rows": len(computed_rows),
        "computed_score_delta_rows": len(score_delta_rows),
        "default_off_code_candidate_rows": len(by_family["DEFAULT_OFF_CODE_CANDIDATE"]),
        "source_repair_rows": len(by_family["SOURCE_CONTROL_REPAIR"]),
        "nofill_redesign_scoring_rows": len(by_family["NOFILL_REDESIGN_SCORING"]),
        "guard_registry_spec_rows": len(by_family["GUARD_REGISTRY_SPEC"]),
        "current_claim_opportunity_audit_rows": len(by_family["CURRENT_CLAIM_OPPORTUNITY_AUDIT"]),
        "score_with_control_rows": len(by_family["SCORE_WITH_CONTROL"]),
        "source_sidecar_joined_rows": sum(1 for row in computed_rows if row.get("source_sidecar_joined")),
        "computed_delta_available_rows": numeric_present(computed_rows, "computed_proxy_delta"),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "market_timeframe_session_horizon_expansion_rows": len(market_expansion_rows),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_rows_consumed = len(computed_rows) == len(action_rows) == input_result["counts"]["action_result_rows"]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "sidecar_input_counts": sidecar_counts,
        "all_action_result_rows_consumed": all_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "computed_action_family_counts": distributions["computed_action_family"],
            "computed_action_status_counts": distributions["computed_action_status"],
            "computed_proxy_delta_class_counts": distributions["computed_proxy_delta_class"],
            "market_expansion_decision_counts": distributions["market_expansion_decision"],
            "market_timeframe_session_horizon_expansion_decision_counts": distributions[
                "market_expansion_matrix_decision"
            ],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE_RESULT: consume computed rows into branch-local scorer/spec modules, exact denominator builders, no-fill variant comparators, source guards, and market/timeframe transfer decisions next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_computed_action_surface": UNIFIED_SYSTEM_COMPUTED_ACTION_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_action_result_rows_consumed": all_rows_consumed,
        "computed_action_family_counts": distributions["computed_action_family"],
    }

    write_jsonl(COMPUTED_ACTION_LEDGER, computed_rows)
    write_jsonl(COMPUTED_SCORE_DELTA_LEDGER, score_delta_rows)
    for family, path in FAMILY_OUTPUTS.items():
        write_jsonl(path, by_family[family])
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollups)
    write_jsonl(FAMILY_ROLLUP_LEDGER, family_rollups)
    write_jsonl(MARKET_ROLLUP_LEDGER, market_rollups)
    write_jsonl(MARKET_EXPANSION_MATRIX_LEDGER, market_expansion_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Unified System Computed Action Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Computed action rows: `{counts['computed_action_rows']}`.",
                f"- Computed score-delta rows: `{counts['computed_score_delta_rows']}`.",
                f"- Source repair rows: `{counts['source_repair_rows']}`.",
                f"- No-fill redesign scoring rows: `{counts['nofill_redesign_scoring_rows']}`.",
                f"- Guard registry spec rows: `{counts['guard_registry_spec_rows']}`.",
                f"- Market/timeframe/session/horizon expansion matrix rows: `{counts['market_timeframe_session_horizon_expansion_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        RUNTIME_SPEC_PATH,
        COMPUTED_ACTION_LEDGER,
        COMPUTED_SCORE_DELTA_LEDGER,
        *FAMILY_OUTPUTS.values(),
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        MARKET_ROLLUP_LEDGER,
        MARKET_EXPANSION_MATRIX_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
