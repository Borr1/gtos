#!/usr/bin/env python3
"""Materialize final default-off redesign registry from module delta candidates."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_final_registry import (
    EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_SURFACE,
    final_registry_code_spec,
    final_registry_event_application,
    final_registry_row,
    scope_key,
)


DELTA_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_BUNDLE"

INPUT_DELTA_RESULT = ROUTE_DIR / f"{DELTA_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_COMPARATOR = ROUTE_DIR / f"{DELTA_PREFIX}_SCOPE_COMPARATOR_LEDGER_2026-05-17.jsonl"
INPUT_EVENT_COMPARATOR = ROUTE_DIR / f"{DELTA_PREFIX}_EVENT_COMPARATOR_LEDGER_2026-05-17.jsonl"
INPUT_REGISTRY_CANDIDATE = ROUTE_DIR / f"{DELTA_PREFIX}_REGISTRY_CANDIDATE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
FINAL_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_FINAL_REGISTRY_LEDGER_2026-05-17.jsonl"
CODE_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_CODE_SPEC_LEDGER_2026-05-17.jsonl"
EVENT_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_APPLICATION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control redesign final-registry bundle. It materializes exact-scope default-off redesign "
    "registry rows, code specs, and full-denominator event application rows from the comparator candidates. It does "
    "not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, "
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-REGISTRY-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_redesign_final_registry_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_redesign_final_registry_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Materialized final exact-scope default-off redesign registry rows and applied them across the full comparator event denominator.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_DELTA_RESULT,
            INPUT_SCOPE_COMPARATOR,
            INPUT_EVENT_COMPARATOR,
            INPUT_REGISTRY_CANDIDATE,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    delta_result = read_json(INPUT_DELTA_RESULT)
    scope_comparator_rows = read_jsonl(INPUT_SCOPE_COMPARATOR)
    event_comparator_rows = read_jsonl(INPUT_EVENT_COMPARATOR)
    registry_candidate_rows = read_jsonl(INPUT_REGISTRY_CANDIDATE)
    scope_comparator_by_id = {
        row.get("exact_control_redesign_scope_module_delta_comparison_row_id"): row for row in scope_comparator_rows
    }

    final_registry_rows = []
    for index, candidate in enumerate(registry_candidate_rows, 1):
        row = final_registry_row(
            candidate,
            scope_comparator_by_id.get(candidate.get("input_scope_module_delta_comparison_row_id"), {}),
            index,
        )
        final_registry_rows.append(with_common(row, generated_at, manifest_hash))
    final_registry_by_scope = {scope_key(row): row for row in final_registry_rows}

    code_spec_rows = []
    for index, registry in enumerate(final_registry_rows, 1):
        code_spec_rows.append(with_common(final_registry_code_spec(registry, index), generated_at, manifest_hash))

    event_application_rows = []
    for index, event in enumerate(event_comparator_rows, 1):
        row = final_registry_event_application(event, final_registry_by_scope.get(scope_key(event)))
        row["exact_control_redesign_final_registry_event_application_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-EVENT-{index:06d}"
        )
        event_application_rows.append(with_common(row, generated_at, manifest_hash))

    distributions = {
        "final_registry_status": string_counter(final_registry_rows, "final_registry_status"),
        "registry_candidate_class": string_counter(final_registry_rows, "registry_candidate_class"),
        "implementation_family": string_counter(final_registry_rows, "implementation_family"),
        "target_delta_use": string_counter(final_registry_rows, "target_delta_use"),
        "code_spec_status": string_counter(code_spec_rows, "code_spec_status"),
        "event_final_registry_application_status": string_counter(
            event_application_rows, "event_final_registry_application_status"
        ),
        "final_registry_event_join_state": string_counter(event_application_rows, "final_registry_event_join_state"),
        "event_target_delta_use": string_counter(event_application_rows, "target_delta_use"),
        "module_scope_relation": string_counter(event_application_rows, "module_scope_relation"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "input_scope_comparator_rows": len(scope_comparator_rows),
        "input_event_comparator_rows": len(event_comparator_rows),
        "input_registry_candidate_rows": len(registry_candidate_rows),
        "final_registry_rows": len(final_registry_rows),
        "code_spec_rows": len(code_spec_rows),
        "event_application_rows": len(event_application_rows),
        "signal_event_application_rows": sum(
            1
            for row in event_application_rows
            if str(row.get("event_final_registry_application_status", "")).endswith("_SIGNAL")
        ),
        "same_scope_control_event_application_rows": distributions["event_final_registry_application_status"].get(
            "FINAL_RED_REGISTRY_EVENT_SAME_SCOPE_CONTROL_CONTEXT", 0
        ),
        "non_scope_context_event_application_rows": distributions["event_final_registry_application_status"].get(
            "FINAL_RED_REGISTRY_EVENT_NON_SCOPE_CONTEXT", 0
        ),
        "exact_scope_joined_event_application_rows": distributions["final_registry_event_join_state"].get(
            "FINAL_RED_REGISTRY_EVENT_JOINED_EXACT_SCOPE", 0
        ),
        "exact_scope_unjoined_context_event_application_rows": distributions["final_registry_event_join_state"].get(
            "FINAL_RED_REGISTRY_EVENT_NO_EXACT_SCOPE_CONTEXT", 0
        ),
        "target_delta_negative_registry_rows": distributions["target_delta_use"].get(
            "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR", 0
        ),
        "target_delta_negative_event_application_rows": distributions["event_target_delta_use"].get(
            "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR", 0
        ),
        "target_delta_null_context_event_application_rows": distributions["event_target_delta_use"].get("None", 0),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-Q-001",
                "question": "Did every comparator registry candidate become a final default-off registry row?",
                "answer_route": f"Yes: {counts['input_registry_candidate_rows']} candidates became {counts['final_registry_rows']} final registry rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-Q-002",
                "question": "Did final registry materialization preserve the full event denominator?",
                "answer_route": f"Yes: {counts['event_application_rows']} comparator event rows were consumed into final registry event application rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-Q-003",
                "question": "Were negative target deltas converted into live scalar scoring?",
                "answer_route": f"No: {counts['target_delta_negative_registry_rows']} final registry rows retain target-delta scalar use disabled while preserving redesign opportunity.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-Q-004",
                "question": "What is the next executable layer?",
                "answer_route": "Consume final registry code specs into branch-local exact-scope observable scorer modules or run a cross-family system recommendation merge.",
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
            "denominator_exact_control_redesign_module_delta_comparator_bundle": delta_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "final_registry_status_counts": distributions["final_registry_status"],
            "event_application_status_counts": distributions["event_final_registry_application_status"],
            "event_join_state_counts": distributions["final_registry_event_join_state"],
            "implementation_family_counts": distributions["implementation_family"],
            "target_delta_use_counts": distributions["target_delta_use"],
            "event_target_delta_use_counts": distributions["event_target_delta_use"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_BUNDLE_RESULT: consume final exact-scope default-off code specs into scorer modules or cross-family system recommendation merge next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_redesign_final_registry_surface": EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "final_registry_status_counts": distributions["final_registry_status"],
        "event_application_status_counts": distributions["event_final_registry_application_status"],
        "event_join_state_counts": distributions["final_registry_event_join_state"],
        "event_target_delta_use_counts": distributions["event_target_delta_use"],
    }
    outputs = [
        FINAL_REGISTRY_LEDGER,
        CODE_SPEC_LEDGER,
        EVENT_APPLICATION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(FINAL_REGISTRY_LEDGER, final_registry_rows)
    write_jsonl(CODE_SPEC_LEDGER, code_spec_rows)
    write_jsonl(EVENT_APPLICATION_LEDGER, event_application_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Redesign Final Registry Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Final registry rows: `{counts['final_registry_rows']}`.",
                f"- Code spec rows: `{counts['code_spec_rows']}`.",
                f"- Event application rows: `{counts['event_application_rows']}`.",
                f"- Signal/control/context event rows: `{counts['signal_event_application_rows']}` / `{counts['same_scope_control_event_application_rows']}` / `{counts['non_scope_context_event_application_rows']}`.",
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
