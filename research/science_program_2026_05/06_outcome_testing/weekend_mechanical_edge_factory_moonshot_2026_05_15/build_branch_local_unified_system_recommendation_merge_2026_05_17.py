#!/usr/bin/env python3
"""Merge branch-local implementation, guard, market-gap, and no-fill recommendation rows."""

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

from src.research_infra.moonshot_branch_local_unified_system_recommendation_merge import (
    UNIFIED_SYSTEM_RECOMMENDATION_SURFACE,
    rollup_row,
    unified_system_candidate,
)


PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE"

INPUTS = {
    "registry_scorer_module": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_BUNDLE_MODULE_REGISTRATION_LEDGER_2026-05-17.jsonl",
    "registry_scorer_module_system": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_BUNDLE_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl",
    "default_off_application": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_APPLICATION_BUNDLE_APPLICATION_LEDGER_2026-05-17.jsonl",
    "default_off_scorer_application": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_APPLICATION_BUNDLE_SCORER_APPLICATION_LEDGER_2026-05-17.jsonl",
    "shadow_source_guard": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_SHADOW_SOURCE_GUARD_BUNDLE_UNIFIED_DECISION_LEDGER_2026-05-17.jsonl",
    "market_gap_code": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_REPLAY_CODE_CANDIDATE_MARKET_GAP_CODE_LEDGER_2026-05-17.jsonl",
    "nofill_far_miss_family": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_FAMILY_SYNTHESIS_LEDGER_2026-05-16.jsonl",
    "nofill_far_miss_avoid": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl",
    "nofill_far_miss_retest": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl",
    "nofill_far_miss_source_confidence": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_SOURCE_CONFIDENCE_BRANCH_LEDGER_2026-05-16.jsonl",
    "nofill_near_miss_offset": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl",
    "nofill_near_miss_market_entry": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl",
    "nofill_near_miss_source_requirement": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_SOURCE_REQUIREMENT_LEDGER_2026-05-16.jsonl",
}

HELPER_MODULE = REPO / UNIFIED_SYSTEM_RECOMMENDATION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
UNIFIED_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_CANDIDATE_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
FAMILY_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local unified system recommendation merge bundle. It consumes module, default-off scorer, source-guard, "
    "market-gap, and no-fill redesign/control rows into one keep/redesign/implement/source-repair table. It does not "
    "change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-SYSTEM-MERGE-SRC-{index:04d}",
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
    manifest["latest_branch_local_unified_system_recommendation_merge_bundle"] = {
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
        "event": "branch_local_unified_system_recommendation_merge_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Merged module, default-off scorer, source-guard, market-gap, and no-fill rows into one unified keep/redesign/implement/source-repair table.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def build_rollups(
    candidates: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_scope[(row.get("mechanical_scope_key"), row.get("source_component"))].append(row)
        by_family[(row.get("source_component"), row.get("unified_decision_group"))].append(row)
    scope_rows = []
    for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1):
        scope_rows.append(with_common(rollup_row(key, by_scope[key], index, "scope_component"), generated_at, manifest_hash))
    family_rows = []
    for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1):
        family_rows.append(with_common(rollup_row(key, by_family[key], index, "source_component_decision_group"), generated_at, manifest_hash))
    return scope_rows, family_rows


def main() -> int:
    generated_at = now_utc()
    input_paths = [ROUTE_DIR / filename for filename in INPUTS.values()]
    source_manifest, manifest_hash = source_manifest_rows(
        [*input_paths, HELPER_MODULE, BUILDER_MODULE, VERIFIER_MODULE, TEST_MODULE],
        generated_at,
    )

    source_counts: dict[str, int] = {}
    candidates: list[dict[str, Any]] = []
    row_index = 1
    for component, filename in INPUTS.items():
        rows = read_jsonl(ROUTE_DIR / filename)
        source_counts[component] = len(rows)
        for row in rows:
            candidate = unified_system_candidate(component, row, row_index)
            candidates.append(with_common(candidate, generated_at, manifest_hash))
            row_index += 1

    scope_rollups, family_rollups = build_rollups(candidates, generated_at, manifest_hash)
    distributions = {
        "source_component": string_counter(candidates, "source_component"),
        "unified_decision_group": string_counter(candidates, "unified_decision_group"),
        "unified_action_class": string_counter(candidates, "unified_action_class"),
        "source_component_decision_group": {
            f"{row.get('source_component')}|{row.get('unified_decision_group')}": count
            for (row, count) in []
        },
    }
    component_group_counter = Counter(
        f"{row.get('source_component')}|{row.get('unified_decision_group')}" for row in candidates
    )
    distributions["source_component_decision_group"] = {
        key: int(component_group_counter[key]) for key in sorted(component_group_counter)
    }

    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-SYSTEM-MERGE-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "unified_candidate_rows": len(candidates),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "bucket_rows": len(buckets),
        "question_rows": 5,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
        **{f"input_{key}_rows": value for key, value in sorted(source_counts.items())},
    }
    questions = [
        "Did every selected upstream row become a unified recommendation row?",
        "Which families are implementable default-off versus redesign/source-repair/control-scoring?",
        "Do current-claim rejection rows preserve the underlying opportunity instead of deleting it?",
        "Which scope/component pairs now carry multiple implementation or redesign actions?",
        "What should be consumed next into branch-local code/spec/default-off scorer work?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-SYSTEM-MERGE-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by unified candidate, scope rollup, family rollup, and bucket ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "bucket_distributions": distributions,
        "system_decision": {
            "decision_group_counts": distributions["unified_decision_group"],
            "source_component_counts": distributions["source_component"],
            "component_group_counts": distributions["source_component_decision_group"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_RESULT: consume unified candidate rows into exact branch-local code/spec/default-off scorer implementation, source repair, and redesign work orders next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_recommendation_surface": UNIFIED_SYSTEM_RECOMMENDATION_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "decision_group_counts": distributions["unified_decision_group"],
    }
    outputs = [
        UNIFIED_CANDIDATE_LEDGER,
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_CANDIDATE_LEDGER, candidates)
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollups)
    write_jsonl(FAMILY_ROLLUP_LEDGER, family_rollups)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Unified System Recommendation Merge Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Unified candidate rows: `{counts['unified_candidate_rows']}`.",
                f"- Scope rollup rows: `{counts['scope_rollup_rows']}`.",
                f"- Family rollup rows: `{counts['family_rollup_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *outputs], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
