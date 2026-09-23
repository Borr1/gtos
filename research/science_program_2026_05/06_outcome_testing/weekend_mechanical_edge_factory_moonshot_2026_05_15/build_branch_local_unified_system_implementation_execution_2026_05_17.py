#!/usr/bin/env python3
"""Consume computed action rows into branch-local implementation execution decisions."""

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

from src.research_infra.moonshot_branch_local_unified_system_implementation_execution import (
    UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
    current_claim_audit_route,
    default_off_module_spec,
    guard_binding_spec,
    implementation_execution_decision,
    implementation_execution_rollup,
    market_transfer_decision,
    nofill_variant_comparator,
    score_control_execution,
    source_builder_spec,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_COMPUTED_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPUTED_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_MARKET_EXPANSION = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
EXECUTION_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_DECISION_LEDGER_2026-05-17.jsonl"
DEFAULT_OFF_MODULE_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_MODULE_SPEC_LEDGER_2026-05-17.jsonl"
SOURCE_BUILDER_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_BUILDER_LEDGER_2026-05-17.jsonl"
NOFILL_COMPARATOR_LEDGER = ROUTE_DIR / f"{PREFIX}_NOFILL_VARIANT_COMPARATOR_LEDGER_2026-05-17.jsonl"
GUARD_BINDING_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_BINDING_LEDGER_2026-05-17.jsonl"
SCORE_CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
AUDIT_ROUTE_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_AUDIT_ROUTE_LEDGER_2026-05-17.jsonl"
MARKET_TRANSFER_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TIMEFRAME_TRANSFER_DECISION_LEDGER_2026-05-17.jsonl"
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
    "Branch-local unified system implementation-execution bundle. It consumes every computed action row into a "
    "concrete default-off module spec, source builder, score-control action, no-fill comparator, guard binding, "
    "current-claim audit route, or recheck decision, and consumes every market/timeframe expansion row into a "
    "market-transfer decision. It does not change live behavior, place orders, or claim broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-IMPLEMENTATION-SRC-{index:04d}",
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


def split_family(rows: list[dict[str, Any]], family: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("computed_action_family") == family]


def build_rollups(
    execution_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_market: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("execution_decision_class"),
            )
        ].append(row)
        by_family[(row.get("computed_action_family"), row.get("execution_action_class"))].append(row)
    for row in market_rows:
        by_market[(row.get("symbol"), row.get("tradability_status"), row.get("decision"), row.get("market_transfer_status"))].append(row)
    scope_rollups = [
        with_common(implementation_execution_rollup(key, by_scope[key], index, "scope_execution_decision"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    family_rollups = [
        with_common(implementation_execution_rollup(key, by_family[key], index, "family_execution_decision"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    market_rollups = [
        with_common(implementation_execution_rollup(key, by_market[key], index, "market_transfer_decision"), generated_at, manifest_hash)
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
    manifest["latest_branch_local_unified_system_implementation_execution_bundle"] = {
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
        "event": "branch_local_unified_system_implementation_execution_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed computed rows into concrete implementation, source, no-fill, guard, audit, score-control, and market-transfer execution decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [INPUT_RESULT, INPUT_COMPUTED_LEDGER, INPUT_MARKET_EXPANSION, HELPER_MODULE, BUILDER_MODULE, VERIFIER_MODULE, TEST_MODULE],
        generated_at,
    )
    input_result = read_json(INPUT_RESULT)
    computed_rows = read_jsonl(INPUT_COMPUTED_LEDGER)
    market_expansion_rows = read_jsonl(INPUT_MARKET_EXPANSION)
    execution_rows = [
        with_common(implementation_execution_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(computed_rows, 1)
    ]
    implementation_rows = split_family(computed_rows, "DEFAULT_OFF_CODE_CANDIDATE")
    source_rows = split_family(computed_rows, "SOURCE_CONTROL_REPAIR")
    score_rows = split_family(computed_rows, "SCORE_WITH_CONTROL")
    nofill_rows = split_family(computed_rows, "NOFILL_REDESIGN_SCORING")
    guard_rows = split_family(computed_rows, "GUARD_REGISTRY_SPEC")
    audit_rows = split_family(computed_rows, "CURRENT_CLAIM_OPPORTUNITY_AUDIT")
    module_specs = [with_common(default_off_module_spec(row, index), generated_at, manifest_hash) for index, row in enumerate(implementation_rows, 1)]
    source_builders = [with_common(source_builder_spec(row, index), generated_at, manifest_hash) for index, row in enumerate(source_rows, 1)]
    score_controls = [with_common(score_control_execution(row, index), generated_at, manifest_hash) for index, row in enumerate(score_rows, 1)]
    nofill_comparators = [with_common(nofill_variant_comparator(row, index), generated_at, manifest_hash) for index, row in enumerate(nofill_rows, 1)]
    guard_bindings = [with_common(guard_binding_spec(row, index), generated_at, manifest_hash) for index, row in enumerate(guard_rows, 1)]
    audit_routes = [with_common(current_claim_audit_route(row, index), generated_at, manifest_hash) for index, row in enumerate(audit_rows, 1)]
    market_transfers = [
        with_common(market_transfer_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(market_expansion_rows, 1)
    ]
    scope_rollups, family_rollups, market_rollups = build_rollups(execution_rows, market_transfers, generated_at, manifest_hash)
    distributions = {
        "execution_action_class": string_counter(execution_rows, "execution_action_class"),
        "execution_decision_class": string_counter(execution_rows, "execution_decision_class"),
        "execution_priority_tier": string_counter(execution_rows, "execution_priority_tier"),
        "computed_action_family": string_counter(execution_rows, "computed_action_family"),
        "source_component": string_counter(execution_rows, "source_component"),
        "market_transfer_status": string_counter(market_transfers, "market_transfer_status"),
        "market_transfer_decision": string_counter(market_transfers, "decision"),
        "market_transfer_symbol": string_counter(market_transfers, "symbol"),
        "market_transfer_tradability_status": string_counter(market_transfers, "tradability_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-IMPLEMENTATION-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        "Did every computed row become a concrete branch-local execution decision?",
        "Which default-off code candidates are now module specs with guard/control requirements?",
        "Which source/control rows are exact denominator builds, satisfied-source replay attachments, or repair/proxy builders?",
        "Which no-fill variants compare as positive, negative avoid/inverse, weak stress, or source/replay-required?",
        "Which guard rows bind denominator or no-fill source-confidence requirements before any score use?",
        "Which score-with-control rows can compare now and which require source/control repair first?",
        "Which current-claim rejection rows preserve opportunity routes rather than deleting mechanisms?",
        "Which market/timeframe/session/horizon rows transfer to shadow, replay, source-repair, proxy/control feature, system input, or preserved rejection?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-IMPLEMENTATION-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by implementation execution, module, source, no-fill, guard, score, audit, market-transfer, rollup, and bucket ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    counts = {
        "input_computed_action_rows": len(computed_rows),
        "input_market_expansion_rows": len(market_expansion_rows),
        "execution_decision_rows": len(execution_rows),
        "default_off_module_spec_rows": len(module_specs),
        "source_builder_rows": len(source_builders),
        "score_control_execution_rows": len(score_controls),
        "nofill_variant_comparator_rows": len(nofill_comparators),
        "guard_binding_rows": len(guard_bindings),
        "current_claim_audit_route_rows": len(audit_routes),
        "market_transfer_decision_rows": len(market_transfers),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "market_rollup_rows": len(market_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_rows_consumed = len(execution_rows) == len(computed_rows) == input_result["counts"]["computed_action_rows"]
    all_market_rows_consumed = len(market_transfers) == len(market_expansion_rows) == input_result["counts"]["market_timeframe_session_horizon_expansion_rows"]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_computed_rows_consumed": all_rows_consumed,
        "all_market_expansion_rows_consumed": all_market_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "execution_action_class_counts": distributions["execution_action_class"],
            "market_transfer_status_counts": distributions["market_transfer_status"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_BUNDLE_RESULT: execute module specs, source builders, no-fill comparators, guard bindings, score-control rows, audit routes, and market-transfer decisions into the next concrete code/source/replay layer.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_computed_rows_consumed": all_rows_consumed,
        "all_market_expansion_rows_consumed": all_market_rows_consumed,
    }
    write_jsonl(EXECUTION_DECISION_LEDGER, execution_rows)
    write_jsonl(DEFAULT_OFF_MODULE_SPEC_LEDGER, module_specs)
    write_jsonl(SOURCE_BUILDER_LEDGER, source_builders)
    write_jsonl(SCORE_CONTROL_LEDGER, score_controls)
    write_jsonl(NOFILL_COMPARATOR_LEDGER, nofill_comparators)
    write_jsonl(GUARD_BINDING_LEDGER, guard_bindings)
    write_jsonl(AUDIT_ROUTE_LEDGER, audit_routes)
    write_jsonl(MARKET_TRANSFER_LEDGER, market_transfers)
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
                "# Branch-Local Unified System Implementation Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Execution decision rows: `{counts['execution_decision_rows']}`.",
                f"- Default-off module spec rows: `{counts['default_off_module_spec_rows']}`.",
                f"- Source builder rows: `{counts['source_builder_rows']}`.",
                f"- No-fill variant comparator rows: `{counts['nofill_variant_comparator_rows']}`.",
                f"- Guard binding rows: `{counts['guard_binding_rows']}`.",
                f"- Market transfer decision rows: `{counts['market_transfer_decision_rows']}`.",
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
        EXECUTION_DECISION_LEDGER,
        DEFAULT_OFF_MODULE_SPEC_LEDGER,
        SOURCE_BUILDER_LEDGER,
        SCORE_CONTROL_LEDGER,
        NOFILL_COMPARATOR_LEDGER,
        GUARD_BINDING_LEDGER,
        AUDIT_ROUTE_LEDGER,
        MARKET_TRANSFER_LEDGER,
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
