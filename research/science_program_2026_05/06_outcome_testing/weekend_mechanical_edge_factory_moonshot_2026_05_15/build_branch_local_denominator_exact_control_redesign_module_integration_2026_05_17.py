#!/usr/bin/env python3
"""Materialize exact-control redesign decisions into branch-local module slots."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_module_integration import (
    EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_SURFACE,
    redesign_blocker_module_integration,
    redesign_code_surface_registration,
    redesign_event_module_observation,
    redesign_scope_module_integration,
    scope_key,
)


REDESIGN_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_RESOLUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_BUNDLE"

INPUT_REDESIGN_RESULT = ROUTE_DIR / f"{REDESIGN_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_RESOLUTION = ROUTE_DIR / f"{REDESIGN_PREFIX}_SCOPE_RESOLUTION_LEDGER_2026-05-17.jsonl"
INPUT_BLOCKER_RESOLUTION = ROUTE_DIR / f"{REDESIGN_PREFIX}_BLOCKER_RESOLUTION_LEDGER_2026-05-17.jsonl"
INPUT_EVENT_RESOLUTION = ROUTE_DIR / f"{REDESIGN_PREFIX}_EVENT_SIGNAL_RESOLUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCOPE_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_MODULE_LEDGER_2026-05-17.jsonl"
BLOCKER_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_BLOCKER_MODULE_LEDGER_2026-05-17.jsonl"
EVENT_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_MODULE_LEDGER_2026-05-17.jsonl"
CODE_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_CODE_SURFACE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control redesign module-integration bundle. It consumes redesign-resolution rows into "
    "default-off module slots, event observations, and code-surface registrations. It does not change live behavior, "
    "place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_redesign_module_integration_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_redesign_module_integration_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed exact-control redesign-resolution decisions into default-off branch-local module slots.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_REDESIGN_RESULT,
            INPUT_SCOPE_RESOLUTION,
            INPUT_BLOCKER_RESOLUTION,
            INPUT_EVENT_RESOLUTION,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    redesign_result = read_json(INPUT_REDESIGN_RESULT)
    scope_resolution_rows = read_jsonl(INPUT_SCOPE_RESOLUTION)
    blocker_resolution_rows = read_jsonl(INPUT_BLOCKER_RESOLUTION)
    event_resolution_rows = read_jsonl(INPUT_EVENT_RESOLUTION)

    scope_module_rows = []
    for index, scope_row in enumerate(scope_resolution_rows, 1):
        row = redesign_scope_module_integration(scope_row)
        row["exact_control_redesign_scope_module_integration_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-SCOPE-{index:04d}"
        )
        scope_module_rows.append(with_common(row, generated_at, manifest_hash))
    module_by_scope = {scope_key(row): row for row in scope_module_rows}

    blocker_module_rows = []
    for index, blocker_row in enumerate(blocker_resolution_rows, 1):
        row = redesign_blocker_module_integration(blocker_row, module_by_scope.get(scope_key(blocker_row), {}))
        row["exact_control_redesign_blocker_module_integration_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-BLOCKER-{index:05d}"
        )
        blocker_module_rows.append(with_common(row, generated_at, manifest_hash))

    event_module_rows = []
    for index, event_row in enumerate(event_resolution_rows, 1):
        row = redesign_event_module_observation(event_row, module_by_scope.get(scope_key(event_row), {}))
        row["exact_control_redesign_event_module_observation_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EVENT-{index:06d}"
        )
        event_module_rows.append(with_common(row, generated_at, manifest_hash))

    code_surface_rows = []
    for index, scope_module_row in enumerate(scope_module_rows, 1):
        code_surface_rows.append(
            with_common(redesign_code_surface_registration(scope_module_row, index), generated_at, manifest_hash)
        )

    distributions = {
        "redesign_module_integration_status": string_counter(
            scope_module_rows, "redesign_module_integration_status"
        ),
        "blocker_redesign_module_integration_status": string_counter(
            blocker_module_rows, "redesign_module_integration_status"
        ),
        "event_module_observation_status": string_counter(event_module_rows, "event_module_observation_status"),
        "module_slot": string_counter(scope_module_rows, "module_slot"),
        "code_surface_status": string_counter(code_surface_rows, "code_surface_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "input_scope_resolution_rows": len(scope_resolution_rows),
        "input_blocker_resolution_rows": len(blocker_resolution_rows),
        "input_event_signal_resolution_rows": len(event_resolution_rows),
        "scope_module_rows": len(scope_module_rows),
        "blocker_module_rows": len(blocker_module_rows),
        "event_module_rows": len(event_module_rows),
        "code_surface_rows": len(code_surface_rows),
        "directional_context_scope_rows": distributions["module_slot"].get(
            "branch_local_exact_control_directional_context_feature", 0
        ),
        "shorter_horizon_transfer_scope_rows": distributions["module_slot"].get(
            "branch_local_exact_control_shorter_horizon_transfer_router", 0
        ),
        "tighter_target_stress_scope_rows": distributions["module_slot"].get(
            "branch_local_exact_control_tighter_target_stress_tester", 0
        ),
        "entry_avoid_inverse_scope_rows": distributions["module_slot"].get(
            "branch_local_exact_control_entry_avoid_inverse_splitter", 0
        ),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-Q-001",
                "question": "Were all redesign-resolution rows consumed into module integration rows?",
                "answer_route": f"Yes: {counts['scope_module_rows']} scopes, {counts['blocker_module_rows']} blockers, and {counts['event_module_rows']} events were consumed.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-Q-002",
                "question": "Did the integration convert any opportunity into cleanup kill?",
                "answer_route": "No: module slots preserve directional context, horizon transfer, tighter-target stress, entry split, and avoid/inverse routes.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-Q-003",
                "question": "Are code surfaces ready for the next execution layer?",
                "answer_route": f"Yes: {counts['code_surface_rows']} default-off code-surface registrations were created with exact-scope guards.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-Q-004",
                "question": "What remains next?",
                "answer_route": "Execute the module slots against event/control denominators or implement the default-off branch-local scorer/redesign registry.",
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
            "denominator_exact_control_redesign_resolution_bundle": redesign_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "module_slot_counts": distributions["module_slot"],
            "scope_module_status_counts": distributions["redesign_module_integration_status"],
            "blocker_module_status_counts": distributions["blocker_redesign_module_integration_status"],
            "event_module_status_counts": distributions["event_module_observation_status"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_BUNDLE_RESULT: execute default-off module slots or materialize the branch-local scorer/redesign registry next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_redesign_module_integration_surface": EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "module_slot_counts": distributions["module_slot"],
    }
    outputs = [
        SCOPE_MODULE_LEDGER,
        BLOCKER_MODULE_LEDGER,
        EVENT_MODULE_LEDGER,
        CODE_SURFACE_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(SCOPE_MODULE_LEDGER, scope_module_rows)
    write_jsonl(BLOCKER_MODULE_LEDGER, blocker_module_rows)
    write_jsonl(EVENT_MODULE_LEDGER, event_module_rows)
    write_jsonl(CODE_SURFACE_LEDGER, code_surface_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Redesign Module Integration Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Scope module rows: `{counts['scope_module_rows']}`.",
                f"- Blocker module rows: `{counts['blocker_module_rows']}`.",
                f"- Event module rows: `{counts['event_module_rows']}`.",
                f"- Code-surface rows: `{counts['code_surface_rows']}`.",
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
