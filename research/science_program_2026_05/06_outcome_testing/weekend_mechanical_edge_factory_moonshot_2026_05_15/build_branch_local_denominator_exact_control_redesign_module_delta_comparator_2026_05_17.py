#!/usr/bin/env python3
"""Compare executed redesign modules to exact-control default-off scopes."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_module_delta_comparator import (
    EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_SURFACE,
    redesign_event_module_delta_comparison,
    redesign_registry_candidate_from_comparison,
    redesign_scope_module_delta_comparison,
    scope_key,
)


EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_BUNDLE"
RUNTIME_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_RUNTIME_ROUTER_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_BUNDLE"

INPUT_EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_EXECUTION = ROUTE_DIR / f"{EXECUTION_PREFIX}_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EVENT_EXECUTION = ROUTE_DIR / f"{EXECUTION_PREFIX}_EVENT_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EFFECTIVE_SCOPE = ROUTE_DIR / f"{RUNTIME_PREFIX}_EFFECTIVE_SCOPE_REGISTRATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCOPE_COMPARATOR_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_COMPARATOR_LEDGER_2026-05-17.jsonl"
EVENT_COMPARATOR_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_COMPARATOR_LEDGER_2026-05-17.jsonl"
REGISTRY_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRY_CANDIDATE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control redesign module-delta comparator bundle. It compares executed redesign modules "
    "against already-registered default-off exact-control scorer scopes and materializes final default-off registry "
    "candidates. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_redesign_module_delta_comparator_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_redesign_module_delta_comparator_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Compared executed redesign module slots against default-off exact-control scopes and materialized final default-off registry candidates.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_EXECUTION_RESULT,
            INPUT_SCOPE_EXECUTION,
            INPUT_EVENT_EXECUTION,
            INPUT_EFFECTIVE_SCOPE,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    execution_result = read_json(INPUT_EXECUTION_RESULT)
    scope_execution_rows = read_jsonl(INPUT_SCOPE_EXECUTION)
    event_execution_rows = read_jsonl(INPUT_EVENT_EXECUTION)
    effective_scope_rows = read_jsonl(INPUT_EFFECTIVE_SCOPE)

    scope_comparator_rows = []
    for index, scope_execution in enumerate(scope_execution_rows, 1):
        row = redesign_scope_module_delta_comparison(scope_execution, effective_scope_rows)
        row["exact_control_redesign_scope_module_delta_comparison_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-SCOPE-{index:04d}"
        )
        scope_comparator_rows.append(with_common(row, generated_at, manifest_hash))
    comparator_by_scope = {scope_key(row): row for row in scope_comparator_rows}

    event_comparator_rows = []
    for index, event_execution in enumerate(event_execution_rows, 1):
        row = redesign_event_module_delta_comparison(event_execution, comparator_by_scope.get(scope_key(event_execution)))
        row["exact_control_redesign_event_module_delta_comparison_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-EVENT-{index:06d}"
        )
        event_comparator_rows.append(with_common(row, generated_at, manifest_hash))

    registry_candidate_rows = []
    for index, scope_comparator in enumerate(scope_comparator_rows, 1):
        registry_candidate_rows.append(
            with_common(redesign_registry_candidate_from_comparison(scope_comparator, index), generated_at, manifest_hash)
        )

    distributions = {
        "module_delta_comparator_decision": string_counter(scope_comparator_rows, "module_delta_comparator_decision"),
        "registry_candidate_class": string_counter(scope_comparator_rows, "registry_candidate_class"),
        "target_delta_use": string_counter(scope_comparator_rows, "target_delta_use"),
        "event_delta_comparison_status": string_counter(event_comparator_rows, "event_delta_comparison_status"),
        "registry_candidate_status": string_counter(registry_candidate_rows, "registry_candidate_status"),
        "module_slot": string_counter(scope_comparator_rows, "module_slot"),
        "same_mechanism_default_off_candidate_count": string_counter(
            scope_comparator_rows, "same_mechanism_default_off_candidate_count"
        ),
        "same_mechanism_shorter_default_off_candidate_count": string_counter(
            scope_comparator_rows, "same_mechanism_shorter_default_off_candidate_count"
        ),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "input_scope_execution_rows": len(scope_execution_rows),
        "input_event_execution_rows": len(event_execution_rows),
        "input_effective_scope_rows": len(effective_scope_rows),
        "scope_comparator_rows": len(scope_comparator_rows),
        "event_comparator_rows": len(event_comparator_rows),
        "registry_candidate_rows": len(registry_candidate_rows),
        "target_delta_negative_rows": distributions["target_delta_use"].get("TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR", 0),
        "shorter_horizon_transfer_registry_rows": distributions["registry_candidate_class"].get(
            "FINAL_REGISTRY_CANDIDATE_SHORTER_HORIZON_TRANSFER", 0
        ),
        "directional_context_registry_rows": distributions["registry_candidate_class"].get(
            "FINAL_REGISTRY_CANDIDATE_DIRECTIONAL_CONTEXT_FEATURE", 0
        ),
        "tighter_target_registry_rows": distributions["registry_candidate_class"].get(
            "FINAL_REGISTRY_CANDIDATE_TIGHTER_TARGET_STRESS", 0
        ),
        "entry_avoid_inverse_registry_rows": distributions["registry_candidate_class"].get(
            "FINAL_REGISTRY_CANDIDATE_ENTRY_AVOID_INVERSE_SPLIT", 0
        ),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-Q-001",
                "question": "Did executed module scopes become concrete final default-off registry candidates?",
                "answer_route": f"Yes: {counts['scope_comparator_rows']} executed scopes became {counts['registry_candidate_rows']} registry candidates.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-Q-002",
                "question": "Did negative target deltas become unconditional scalar scores?",
                "answer_route": f"No: {counts['target_delta_negative_rows']} rows carry TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR while preserving redesign intelligence.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-Q-003",
                "question": "Did the comparator preserve the full event denominator?",
                "answer_route": f"Yes: all {counts['event_comparator_rows']} module-execution event rows are preserved as comparator event rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-DELTA-Q-004",
                "question": "What is the next executable layer?",
                "answer_route": "Materialize the final branch-local default-off redesign registry or consume candidates into code/scorer specs with exact scope guards.",
            },
            generated_at,
            manifest_hash,
        ),
    ]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {
            "denominator_exact_control_redesign_module_execution_bundle": execution_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "module_delta_comparator_decision_counts": distributions["module_delta_comparator_decision"],
            "registry_candidate_class_counts": distributions["registry_candidate_class"],
            "target_delta_use_counts": distributions["target_delta_use"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_BUNDLE_RESULT: materialize final default-off redesign registry or exact-scope scorer/code specs next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_redesign_module_delta_comparator_surface": EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "registry_candidate_class_counts": distributions["registry_candidate_class"],
        "target_delta_use_counts": distributions["target_delta_use"],
    }
    outputs = [
        SCOPE_COMPARATOR_LEDGER,
        EVENT_COMPARATOR_LEDGER,
        REGISTRY_CANDIDATE_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(SCOPE_COMPARATOR_LEDGER, scope_comparator_rows)
    write_jsonl(EVENT_COMPARATOR_LEDGER, event_comparator_rows)
    write_jsonl(REGISTRY_CANDIDATE_LEDGER, registry_candidate_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Redesign Module Delta Comparator Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Scope comparator rows: `{counts['scope_comparator_rows']}`.",
                f"- Event comparator rows: `{counts['event_comparator_rows']}`.",
                f"- Registry candidate rows: `{counts['registry_candidate_rows']}`.",
                f"- Negative target-delta rows kept out of scalar use: `{counts['target_delta_negative_rows']}`.",
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
