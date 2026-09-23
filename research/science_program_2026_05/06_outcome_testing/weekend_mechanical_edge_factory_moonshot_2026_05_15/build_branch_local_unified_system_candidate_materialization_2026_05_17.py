#!/usr/bin/env python3
"""Consume candidate dispatch artifacts into executable materialized action surfaces."""

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

from src.research_infra.moonshot_branch_local_unified_system_candidate_materialization import (
    UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
    candidate_materialization_decision,
    candidate_materialization_rollup,
    guard_enforcement_materialization,
    market_action_materialization,
    nofill_comparator_materialization,
    opportunity_materialization,
    recheck_materialization,
    score_control_comparator_materialization,
    scorer_code_surface_materialization,
    source_control_builder_materialization,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_DISPATCH_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_DISPATCH_SELF_TEST_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_DISPATCH_SELF_TEST_LEDGER_2026-05-17.jsonl"
INPUT_SCORER_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_CONTROL_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_CONTROL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
INPUT_SCORE_CONTROL_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORE_CONTROL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
INPUT_NOFILL_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NOFILL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
INPUT_GUARD_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
INPUT_OPPORTUNITY_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CURRENT_CLAIM_OPPORTUNITY_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
INPUT_RECHECK_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RECHECK_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_TRANSFER_DISPATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_TRANSFER_DISPATCH_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
CANDIDATE_MATERIALIZATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_MATERIALIZATION_DECISION_LEDGER_2026-05-17.jsonl"
SCORER_CODE_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_CODE_SURFACE_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_BUILDER_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_BUILDER_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_COMPARATOR_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_COMPARATOR_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
NOFILL_COMPARATOR_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_COMPARATOR_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
GUARD_ENFORCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_ENFORCEMENT_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
OPPORTUNITY_MATERIALIZATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_OPPORTUNITY_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
RECHECK_MATERIALIZATION_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
MARKET_ACTION_MATERIALIZATION_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_ACTION_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
FAMILY_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
MARKET_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local unified system candidate-materialization bundle. It consumes every candidate dispatch row into "
    "materialized scorer/code, source/control builder, score-control comparator, no-fill comparator, guard enforcement, "
    "opportunity-preservation, recheck, and market-action rows. It does not change live behavior, place orders, or claim "
    "broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MATERIALIZATION-SRC-{index:04d}",
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


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def build_rollups(
    materialization_rows: list[dict[str, Any]],
    component_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in materialization_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("candidate_materialization_family"),
            )
        ].append(row)
        by_family[(row.get("candidate_materialization_family"), row.get("candidate_materialization_status"))].append(row)
    for row in component_rows:
        family = (
            row.get("scorer_materialization_status")
            or row.get("source_control_materialization_status")
            or row.get("score_control_materialization_status")
            or row.get("nofill_materialization_status")
            or row.get("guard_enforcement_status")
            or row.get("opportunity_materialization_status")
            or row.get("recheck_materialization_status")
        )
        by_family[(row.get("unified_system_candidate_materialization"), family)].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("market_action_materialization_status"))].append(row)
    scope_rollups = [
        with_common(candidate_materialization_rollup(key, by_scope[key], index, "scope_candidate_materialization"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(candidate_materialization_rollup(key, by_family[key], index, "family_candidate_materialization"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(candidate_materialization_rollup(key, by_market[key], index, "market_action_materialization"), generated_at, manifest_hash)
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
            generated.append(
                {"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True}
            )
    manifest["latest_branch_local_unified_system_candidate_materialization_bundle"] = {
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
        "event": "branch_local_unified_system_candidate_materialization_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed candidate dispatch rows into concrete scorer/source/control/no-fill/guard/opportunity/recheck/market materializations.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME,
            INPUT_DISPATCH_LEDGER,
            INPUT_DISPATCH_SELF_TEST_LEDGER,
            INPUT_SCORER_DISPATCH_LEDGER,
            INPUT_SOURCE_CONTROL_DISPATCH_LEDGER,
            INPUT_SCORE_CONTROL_DISPATCH_LEDGER,
            INPUT_NOFILL_DISPATCH_LEDGER,
            INPUT_GUARD_DISPATCH_LEDGER,
            INPUT_OPPORTUNITY_DISPATCH_LEDGER,
            INPUT_RECHECK_DISPATCH_LEDGER,
            INPUT_MARKET_TRANSFER_DISPATCH_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    dispatch_input = read_jsonl(INPUT_DISPATCH_LEDGER)
    scorer_input = read_jsonl(INPUT_SCORER_DISPATCH_LEDGER)
    source_input = read_jsonl(INPUT_SOURCE_CONTROL_DISPATCH_LEDGER)
    score_control_input = read_jsonl(INPUT_SCORE_CONTROL_DISPATCH_LEDGER)
    nofill_input = read_jsonl(INPUT_NOFILL_DISPATCH_LEDGER)
    guard_input = read_jsonl(INPUT_GUARD_DISPATCH_LEDGER)
    opportunity_input = read_jsonl(INPUT_OPPORTUNITY_DISPATCH_LEDGER)
    recheck_input = read_jsonl(INPUT_RECHECK_DISPATCH_LEDGER)
    market_input = read_jsonl(INPUT_MARKET_TRANSFER_DISPATCH_LEDGER)

    materialization_rows = [
        with_common(candidate_materialization_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(dispatch_input, 1)
    ]
    scorer_rows = [
        with_common(scorer_code_surface_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(scorer_input, 1)
    ]
    source_rows = [
        with_common(source_control_builder_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(source_input, 1)
    ]
    score_control_rows = [
        with_common(score_control_comparator_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(score_control_input, 1)
    ]
    nofill_rows = [
        with_common(nofill_comparator_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(nofill_input, 1)
    ]
    guard_rows = [
        with_common(guard_enforcement_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(guard_input, 1)
    ]
    opportunity_rows = [
        with_common(opportunity_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(opportunity_input, 1)
    ]
    recheck_rows = [
        with_common(recheck_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(recheck_input, 1)
    ]
    market_rows = [
        with_common(market_action_materialization(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_input, 1)
    ]
    all_component_rows = scorer_rows + source_rows + score_control_rows + nofill_rows + guard_rows + opportunity_rows + recheck_rows
    scope_rollups, family_rollups, market_rollups = build_rollups(
        materialization_rows, all_component_rows, market_rows, generated_at, manifest_hash
    )
    distributions = {
        "candidate_materialization_family": string_counter(materialization_rows, "candidate_materialization_family"),
        "candidate_materialization_status": string_counter(materialization_rows, "candidate_materialization_status"),
        "scorer_materialization_status": string_counter(scorer_rows, "scorer_materialization_status"),
        "source_control_materialization_status": string_counter(source_rows, "source_control_materialization_status"),
        "score_control_materialization_status": string_counter(score_control_rows, "score_control_materialization_status"),
        "nofill_materialization_status": string_counter(nofill_rows, "nofill_materialization_status"),
        "guard_enforcement_status": string_counter(guard_rows, "guard_enforcement_status"),
        "opportunity_materialization_status": string_counter(opportunity_rows, "opportunity_materialization_status"),
        "recheck_materialization_status": string_counter(recheck_rows, "recheck_materialization_status"),
        "market_action_materialization_status": string_counter(market_rows, "market_action_materialization_status"),
        "market_action_materialization_symbol": string_counter(market_rows, "symbol"),
        "market_action_materialization_tradability_status": string_counter(market_rows, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MATERIALIZATION-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MATERIALIZATION-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by materialization, component, market-action, rollup, bucket, and source-manifest ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(
            [
                "Did every candidate dispatch row become a concrete materialized action row?",
                "Which scorer rows are ready as default-off code surfaces with guard contracts?",
                "Which source/control rows can execute from same-resource evidence and which require proxy repair?",
                "Which no-fill rows become positive comparators, avoid/inverse filters, stress controls, or source repairs?",
                "Which guard rows enforce fail-closed behavior before any score use?",
                "Which current-claim rejection rows preserve opportunity as avoid/context/redesign/source/system input?",
                "Which market/timeframe/session/horizon rows become source repair, shadow, proxy/control, replay, system-input, or opportunity actions?",
                "What is the next same-resource implementation/system recommendation layer after materialization?",
            ],
            1,
        )
    ]
    counts = {
        "input_candidate_dispatch_rows": len(dispatch_input),
        "input_market_transfer_dispatch_rows": len(market_input),
        "candidate_materialization_decision_rows": len(materialization_rows),
        "scorer_code_surface_materialization_rows": len(scorer_rows),
        "source_control_builder_materialization_rows": len(source_rows),
        "score_control_comparator_materialization_rows": len(score_control_rows),
        "nofill_comparator_materialization_rows": len(nofill_rows),
        "guard_enforcement_materialization_rows": len(guard_rows),
        "current_claim_opportunity_materialization_rows": len(opportunity_rows),
        "recheck_materialization_rows": len(recheck_rows),
        "market_action_materialization_rows": len(market_rows),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    split_total = len(all_component_rows)
    all_candidate_dispatch_rows_consumed = (
        len(materialization_rows) == len(dispatch_input) == input_result["counts"]["candidate_dispatch_decision_rows"]
    )
    all_component_dispatch_rows_consumed = split_total == input_result["counts"]["candidate_dispatch_decision_rows"]
    all_market_dispatch_rows_consumed = (
        len(market_rows) == len(market_input) == input_result["counts"]["market_transfer_dispatch_rows"]
    )
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_candidate_dispatch_rows_consumed": all_candidate_dispatch_rows_consumed,
        "all_component_dispatch_rows_consumed": all_component_dispatch_rows_consumed,
        "all_market_dispatch_rows_consumed": all_market_dispatch_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "candidate_materialization_family_counts": distributions["candidate_materialization_family"],
            "candidate_materialization_status_counts": distributions["candidate_materialization_status"],
            "market_action_materialization_status_counts": distributions["market_action_materialization_status"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION_BUNDLE_RESULT: consume dispatch into concrete scorer/source/control/no-fill/guard/opportunity/recheck/market materializations and continue to implementation/system recommendation execution.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_candidate_dispatch_rows_consumed": all_candidate_dispatch_rows_consumed,
        "all_component_dispatch_rows_consumed": all_component_dispatch_rows_consumed,
        "all_market_dispatch_rows_consumed": all_market_dispatch_rows_consumed,
    }
    write_jsonl(CANDIDATE_MATERIALIZATION_LEDGER, materialization_rows)
    write_jsonl(SCORER_CODE_SURFACE_LEDGER, scorer_rows)
    write_jsonl(SOURCE_CONTROL_BUILDER_LEDGER, source_rows)
    write_jsonl(SCORE_CONTROL_COMPARATOR_LEDGER, score_control_rows)
    write_jsonl(NOFILL_COMPARATOR_LEDGER, nofill_rows)
    write_jsonl(GUARD_ENFORCEMENT_LEDGER, guard_rows)
    write_jsonl(OPPORTUNITY_MATERIALIZATION_LEDGER, opportunity_rows)
    write_jsonl(RECHECK_MATERIALIZATION_LEDGER, recheck_rows)
    write_jsonl(MARKET_ACTION_MATERIALIZATION_LEDGER, market_rows)
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollups)
    write_jsonl(FAMILY_ROLLUP_LEDGER, family_rollups)
    write_jsonl(MARKET_ROLLUP_LEDGER, market_rollups)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Unified System Candidate Materialization Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Candidate materialization decision rows: `{counts['candidate_materialization_decision_rows']}`.",
                f"- No-fill comparator materialization rows: `{counts['nofill_comparator_materialization_rows']}`.",
                f"- Guard enforcement materialization rows: `{counts['guard_enforcement_materialization_rows']}`.",
                f"- Market action materialization rows: `{counts['market_action_materialization_rows']}`.",
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
        CANDIDATE_MATERIALIZATION_LEDGER,
        SCORER_CODE_SURFACE_LEDGER,
        SOURCE_CONTROL_BUILDER_LEDGER,
        SCORE_CONTROL_COMPARATOR_LEDGER,
        NOFILL_COMPARATOR_LEDGER,
        GUARD_ENFORCEMENT_LEDGER,
        OPPORTUNITY_MATERIALIZATION_LEDGER,
        RECHECK_MATERIALIZATION_LEDGER,
        MARKET_ACTION_MATERIALIZATION_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        MARKET_ROLLUP_LEDGER,
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
