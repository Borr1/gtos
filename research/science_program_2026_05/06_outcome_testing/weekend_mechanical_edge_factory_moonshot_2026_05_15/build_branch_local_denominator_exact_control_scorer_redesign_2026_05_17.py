#!/usr/bin/env python3
"""Consume exact-control construction rows into scorer and redesign execution rows."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_scorer_redesign import (
    EXACT_CONTROL_SCORER_REDESIGN_SURFACE,
    exact_control_blocker_runtime_decision,
    exact_control_event_score,
    exact_control_scope_runtime_spec,
    scope_key,
)


CONSTRUCT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_CONSTRUCTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_SCORER_REDESIGN_BUNDLE"

INPUT_CONSTRUCTION_RESULT = ROUTE_DIR / f"{CONSTRUCT_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_CONSTRUCTION = ROUTE_DIR / f"{CONSTRUCT_PREFIX}_SCOPE_CONSTRUCTION_LEDGER_2026-05-17.jsonl"
INPUT_BLOCKER_CONSTRUCTION = ROUTE_DIR / f"{CONSTRUCT_PREFIX}_BLOCKER_CONSTRUCTION_LEDGER_2026-05-17.jsonl"
INPUT_DENOMINATOR_EVENT = ROUTE_DIR / f"{CONSTRUCT_PREFIX}_DENOMINATOR_EVENT_LEDGER_2026-05-17.jsonl"
INPUT_MISSED_AUDIT = ROUTE_DIR / f"{CONSTRUCT_PREFIX}_MISSED_OPPORTUNITY_AUDIT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_SCORER_REDESIGN_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCOPE_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_RUNTIME_SPEC_LEDGER_2026-05-17.jsonl"
BLOCKER_RUNTIME_LEDGER = ROUTE_DIR / f"{PREFIX}_BLOCKER_RUNTIME_DECISION_LEDGER_2026-05-17.jsonl"
EVENT_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_SCORE_LEDGER_2026-05-17.jsonl"
SCOPE_SCORER_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_DEFAULT_OFF_SCORER_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control scorer/redesign bundle. It consumes exact-control construction rows into default-off "
    "scope scorers, event-level scorer behavior, and split/redesign execution rows. It does not change live behavior, "
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-SCORER-REDESIGN-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_scorer_redesign_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_scorer_redesign_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed exact-control construction rows into default-off scorer and split/redesign execution rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_CONSTRUCTION_RESULT,
            INPUT_SCOPE_CONSTRUCTION,
            INPUT_BLOCKER_CONSTRUCTION,
            INPUT_DENOMINATOR_EVENT,
            INPUT_MISSED_AUDIT,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    construction_result = read_json(INPUT_CONSTRUCTION_RESULT)
    scope_rows = read_jsonl(INPUT_SCOPE_CONSTRUCTION)
    blocker_rows = read_jsonl(INPUT_BLOCKER_CONSTRUCTION)
    event_rows = read_jsonl(INPUT_DENOMINATOR_EVENT)
    missed_audit_rows = read_jsonl(INPUT_MISSED_AUDIT)

    scope_runtime_rows = []
    for index, scope in enumerate(scope_rows, 1):
        row = exact_control_scope_runtime_spec(scope)
        row["exact_control_scope_runtime_spec_row_id"] = f"OHLC-GTOS-DENOM-EXACTCTRL-SCORER-SCOPE-{index:04d}"
        scope_runtime_rows.append(with_common(row, generated_at, manifest_hash))

    scope_runtime_by_scope = {scope_key(row): row for row in scope_runtime_rows}
    blocker_runtime_rows = []
    scorer_rows = []
    redesign_rows = []
    for index, blocker in enumerate(blocker_rows, 1):
        runtime = exact_control_blocker_runtime_decision(blocker, scope_runtime_by_scope.get(scope_key(blocker)))
        runtime["exact_control_blocker_runtime_decision_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-SCORER-BLOCKER-{index:05d}"
        )
        runtime = with_common(runtime, generated_at, manifest_hash)
        blocker_runtime_rows.append(runtime)
        if runtime.get("branch_local_score_allowed"):
            scorer_rows.append(
                with_common(
                    {
                        "exact_control_scope_default_off_scorer_row_id": (
                            f"OHLC-GTOS-DENOM-EXACTCTRL-SCORER-DEFAULT-{len(scorer_rows) + 1:05d}"
                        ),
                        "input_blocker_runtime_decision_row_id": runtime["exact_control_blocker_runtime_decision_row_id"],
                        "symbol": runtime.get("symbol"),
                        "route_session": runtime.get("route_session"),
                        "horizon_id": runtime.get("horizon_id"),
                        "primitive_flag": runtime.get("primitive_flag"),
                        "default_off_exact_control_score": runtime.get("default_off_exact_control_score"),
                        "scorer_status": "DEFAULT_OFF_EXACT_CONTROL_SCORER_REGISTERED_FROM_EXACT_N20",
                        "unconditional_scalar_use_allowed": False,
                        "runtime_score_allowed": False,
                        "live_effect": False,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
        if runtime.get("branch_local_redesign_required"):
            audit = missed_audit_rows[index - 1] if index <= len(missed_audit_rows) else {}
            redesign_rows.append(
                with_common(
                    {
                        "exact_control_redesign_execution_row_id": (
                            f"OHLC-GTOS-DENOM-EXACTCTRL-SCORER-REDESIGN-{len(redesign_rows) + 1:05d}"
                        ),
                        "input_blocker_runtime_decision_row_id": runtime["exact_control_blocker_runtime_decision_row_id"],
                        "symbol": runtime.get("symbol"),
                        "route_session": runtime.get("route_session"),
                        "horizon_id": runtime.get("horizon_id"),
                        "primitive_flag": runtime.get("primitive_flag"),
                        "redesign_family": runtime.get("redesign_family"),
                        "exact_control_proxy_r_style_delta": runtime.get("exact_control_proxy_r_style_delta"),
                        "exact_control_alignment_delta": runtime.get("exact_control_alignment_delta"),
                        "redesign_status": "EXACT_CONTROL_SPLIT_REDESIGN_EXECUTED_DEFAULT_OFF",
                        "missed_opportunity_audit": audit.get("missed_opportunity_audit"),
                        "unconditional_scalar_use_allowed": False,
                        "runtime_score_allowed": False,
                        "live_effect": False,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    event_score_rows = []
    for index, event in enumerate(event_rows, 1):
        event_with_scope_id = {**event}
        scope_runtime = scope_runtime_by_scope.get(scope_key(event))
        if scope_runtime:
            event_with_scope_id["input_scope_construction_row_id"] = scope_runtime.get("input_scope_construction_row_id")
        row = exact_control_event_score(event_with_scope_id, scope_runtime)
        row["exact_control_event_score_row_id"] = f"OHLC-GTOS-DENOM-EXACTCTRL-SCORER-EVENT-{index:06d}"
        event_score_rows.append(with_common(row, generated_at, manifest_hash))

    distributions = {
        "exact_control_scope_runtime_status": string_counter(scope_runtime_rows, "exact_control_scope_runtime_status"),
        "exact_control_blocker_runtime_status": string_counter(blocker_runtime_rows, "exact_control_blocker_runtime_status"),
        "exact_control_event_runtime_status": string_counter(event_score_rows, "exact_control_event_runtime_status"),
        "redesign_family": string_counter(redesign_rows, "redesign_family"),
        "scorer_status": string_counter(scorer_rows, "scorer_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            blocker_runtime_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-SCORER-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-SCORER-Q-001",
                "question": "Did exact-control construction produce executable branch-local scorer behavior?",
                "answer_route": f"Yes: {len(scorer_rows)} default-off blocker scorer rows and {sum(1 for row in event_score_rows if row.get('exact_control_event_runtime_status') == 'EXACT_CONTROL_EVENT_DEFAULT_OFF_SCORE_EMITTED')} event-level emitted-score rows were built.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-SCORER-Q-002",
                "question": "Were split rows deleted because target delta was negative?",
                "answer_route": f"No: {len(redesign_rows)} split/redesign rows were executed and preserve alignment-positive intelligence.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-SCORER-Q-003",
                "question": "Does any emitted score become unconditional or live behavior?",
                "answer_route": "No: every scorer/redesign/event row remains branch-local, default-off, and unconditional scalar use remains false.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_scope_construction_rows": len(scope_rows),
        "input_blocker_construction_rows": len(blocker_rows),
        "input_denominator_event_rows": len(event_rows),
        "scope_runtime_spec_rows": len(scope_runtime_rows),
        "blocker_runtime_decision_rows": len(blocker_runtime_rows),
        "event_score_rows": len(event_score_rows),
        "scope_default_off_scorer_rows": len(scorer_rows),
        "redesign_execution_rows": len(redesign_rows),
        "default_off_event_score_emitted_rows": sum(
            1
            for row in event_score_rows
            if row.get("exact_control_event_runtime_status") == "EXACT_CONTROL_EVENT_DEFAULT_OFF_SCORE_EMITTED"
        ),
        "redesign_alignment_event_signal_rows": sum(
            1
            for row in event_score_rows
            if row.get("exact_control_event_runtime_status") == "EXACT_CONTROL_EVENT_REDESIGN_ALIGNMENT_SIGNAL_EMITTED"
        ),
        "bucket_rows": len(buckets),
        "question_rows": len(questions),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {
            "denominator_exact_control_construction_bundle": construction_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "scope_runtime_status_counts": distributions["exact_control_scope_runtime_status"],
            "blocker_runtime_status_counts": distributions["exact_control_blocker_runtime_status"],
            "event_runtime_status_counts": distributions["exact_control_event_runtime_status"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_SCORER_REDESIGN_BUNDLE_RESULT: consume exact positive controls as default-off scorer candidates and consume negative-target/positive-alignment controls as redesign/inverse-directional features without deleting mechanism intelligence.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_scorer_redesign_surface": EXACT_CONTROL_SCORER_REDESIGN_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "distributions": distributions,
    }
    outputs = [
        SCOPE_RUNTIME_LEDGER,
        BLOCKER_RUNTIME_LEDGER,
        EVENT_SCORE_LEDGER,
        SCOPE_SCORER_LEDGER,
        REDESIGN_EXECUTION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(SCOPE_RUNTIME_LEDGER, scope_runtime_rows)
    write_jsonl(BLOCKER_RUNTIME_LEDGER, blocker_runtime_rows)
    write_jsonl(EVENT_SCORE_LEDGER, event_score_rows)
    write_jsonl(SCOPE_SCORER_LEDGER, scorer_rows)
    write_jsonl(REDESIGN_EXECUTION_LEDGER, redesign_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Scorer Redesign Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Scope runtime specs: `{counts['scope_runtime_spec_rows']}`.",
                f"- Blocker runtime decisions: `{counts['blocker_runtime_decision_rows']}`.",
                f"- Event score rows: `{counts['event_score_rows']}`.",
                f"- Default-off blocker scorer rows: `{counts['scope_default_off_scorer_rows']}`.",
                f"- Redesign execution rows: `{counts['redesign_execution_rows']}`.",
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
