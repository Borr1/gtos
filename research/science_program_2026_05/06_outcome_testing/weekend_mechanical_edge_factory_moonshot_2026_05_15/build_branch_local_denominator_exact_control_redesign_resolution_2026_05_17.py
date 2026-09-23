#!/usr/bin/env python3
"""Resolve exact-control split/redesign runtime rows into concrete decisions."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_resolution import (
    EXACT_CONTROL_REDESIGN_RESOLUTION_SURFACE,
    redesign_blocker_resolution,
    redesign_event_signal_resolution,
    redesign_scope_resolution,
    scope_key,
)


RUNTIME_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_RUNTIME_ROUTER_BUNDLE"
IMPL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_IMPLEMENTATION_CANDIDATE_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_RESOLUTION_BUNDLE"

INPUT_RUNTIME_RESULT = ROUTE_DIR / f"{RUNTIME_PREFIX}_RESULT_2026-05-17.json"
INPUT_EFFECTIVE_SCOPE = ROUTE_DIR / f"{RUNTIME_PREFIX}_EFFECTIVE_SCOPE_REGISTRATION_LEDGER_2026-05-17.jsonl"
INPUT_EVENT_ROUTING = ROUTE_DIR / f"{RUNTIME_PREFIX}_EVENT_RUNTIME_ROUTING_LEDGER_2026-05-17.jsonl"
INPUT_BLOCKER_IMPL = ROUTE_DIR / f"{IMPL_PREFIX}_BLOCKER_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_REDESIGN_RESOLUTION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCOPE_RESOLUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_RESOLUTION_LEDGER_2026-05-17.jsonl"
BLOCKER_RESOLUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_BLOCKER_RESOLUTION_LEDGER_2026-05-17.jsonl"
EVENT_SIGNAL_RESOLUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_SIGNAL_RESOLUTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control redesign-resolution bundle. It resolves split/redesign runtime rows into same-resource "
    "directional-context, horizon-transfer, target-tightening, or entry/avoid redesign decisions. It does not change live "
    "behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_redesign_resolution_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_redesign_resolution_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Resolved exact-control split/redesign runtime rows into concrete redesign decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RUNTIME_RESULT,
            INPUT_EFFECTIVE_SCOPE,
            INPUT_EVENT_ROUTING,
            INPUT_BLOCKER_IMPL,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    runtime_result = read_json(INPUT_RUNTIME_RESULT)
    effective_scope_rows = read_jsonl(INPUT_EFFECTIVE_SCOPE)
    event_rows = read_jsonl(INPUT_EVENT_ROUTING)
    blocker_rows = read_jsonl(INPUT_BLOCKER_IMPL)

    events_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in event_rows:
        events_by_scope[scope_key(row)].append(row)

    split_effective_rows = [row for row in effective_scope_rows if row.get("effective_runtime_family") == "SPLIT_REDESIGN_ROUTER"]
    scope_resolution_rows = []
    for index, scope_row in enumerate(split_effective_rows, 1):
        row = redesign_scope_resolution(scope_row, events_by_scope.get(scope_key(scope_row), []), effective_scope_rows)
        row["exact_control_redesign_scope_resolution_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-SCOPE-{index:04d}"
        )
        scope_resolution_rows.append(with_common(row, generated_at, manifest_hash))

    resolution_by_scope = {scope_key(row): row for row in scope_resolution_rows}
    split_blocker_rows = [
        row
        for row in blocker_rows
        if row.get("exact_control_blocker_implementation_status")
        == "EXACT_CONTROL_BLOCKER_IMPLEMENT_SPLIT_REDESIGN_CANDIDATE"
    ]
    blocker_resolution_rows = []
    for index, blocker in enumerate(split_blocker_rows, 1):
        row = redesign_blocker_resolution(blocker, resolution_by_scope.get(scope_key(blocker), {}))
        row["exact_control_redesign_blocker_resolution_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-BLOCKER-{index:05d}"
        )
        blocker_resolution_rows.append(with_common(row, generated_at, manifest_hash))

    signal_event_rows = [
        row
        for row in event_rows
        if row.get("runtime_event_routing_status") == "EXACT_CONTROL_RUNTIME_EVENT_REDESIGN_SIGNAL_ROUTED"
    ]
    event_signal_resolution_rows = []
    for index, event in enumerate(signal_event_rows, 1):
        row = redesign_event_signal_resolution(event, resolution_by_scope.get(scope_key(event), {}))
        row["exact_control_redesign_event_signal_resolution_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-EVENT-{index:06d}"
        )
        event_signal_resolution_rows.append(with_common(row, generated_at, manifest_hash))

    distributions = {
        "redesign_resolution_decision": string_counter(scope_resolution_rows, "redesign_resolution_decision"),
        "blocker_redesign_resolution_decision": string_counter(
            blocker_resolution_rows, "redesign_resolution_decision"
        ),
        "redesign_event_resolution_status": string_counter(
            event_signal_resolution_rows, "redesign_event_resolution_status"
        ),
        "redesign_family": string_counter(scope_resolution_rows, "redesign_family"),
        "horizon_transfer_status": string_counter(scope_resolution_rows, "horizon_transfer_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    counts = {
        "input_effective_scope_rows": len(effective_scope_rows),
        "input_runtime_event_rows": len(event_rows),
        "input_blocker_implementation_rows": len(blocker_rows),
        "split_effective_scope_rows": len(split_effective_rows),
        "split_blocker_input_rows": len(split_blocker_rows),
        "runtime_redesign_signal_event_rows": len(signal_event_rows),
        "scope_resolution_rows": len(scope_resolution_rows),
        "blocker_resolution_rows": len(blocker_resolution_rows),
        "event_signal_resolution_rows": len(event_signal_resolution_rows),
        "horizon_transfer_available_scope_rows": sum(
            1
            for row in scope_resolution_rows
            if row.get("horizon_transfer_status")
            == "REDESIGN_RESOLUTION_HORIZON_TRANSFER_DEFAULT_OFF_SCORER_AVAILABLE"
        ),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-Q-001",
                "question": "Were split/redesign rows consumed into concrete decisions?",
                "answer_route": f"Yes: {counts['scope_resolution_rows']} scope rows, {counts['blocker_resolution_rows']} blocker rows, and {counts['event_signal_resolution_rows']} event-signal rows were resolved.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-Q-002",
                "question": "Did any split row become a cleanup kill?",
                "answer_route": "No: every split row remains mechanism-preserved as a redesign, directional-context, horizon-transfer, or avoid/inverse route.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-Q-003",
                "question": "Were shorter-horizon transfers checked from same-resource exact-control scopes?",
                "answer_route": f"Yes: {counts['horizon_transfer_available_scope_rows']} split scopes found a shorter positive default-off horizon transfer.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-RESOLVE-Q-004",
                "question": "What remains next?",
                "answer_route": "Consume these redesign decisions into branch-local module integration or use them to prioritize the next source/horizon computation route.",
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
            "denominator_exact_control_runtime_router_bundle": runtime_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "scope_resolution_decision_counts": distributions["redesign_resolution_decision"],
            "blocker_resolution_decision_counts": distributions["blocker_redesign_resolution_decision"],
            "event_signal_resolution_counts": distributions["redesign_event_resolution_status"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_RESOLUTION_BUNDLE_RESULT: consume split/redesign runtime signals into concrete redesign decisions while preserving mechanism intelligence.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_redesign_resolution_surface": EXACT_CONTROL_REDESIGN_RESOLUTION_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "distributions": distributions,
    }
    outputs = [
        SCOPE_RESOLUTION_LEDGER,
        BLOCKER_RESOLUTION_LEDGER,
        EVENT_SIGNAL_RESOLUTION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(SCOPE_RESOLUTION_LEDGER, scope_resolution_rows)
    write_jsonl(BLOCKER_RESOLUTION_LEDGER, blocker_resolution_rows)
    write_jsonl(EVENT_SIGNAL_RESOLUTION_LEDGER, event_signal_resolution_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Redesign Resolution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Scope resolution rows: `{counts['scope_resolution_rows']}`.",
                f"- Blocker resolution rows: `{counts['blocker_resolution_rows']}`.",
                f"- Event signal resolution rows: `{counts['event_signal_resolution_rows']}`.",
                f"- Horizon transfer available scope rows: `{counts['horizon_transfer_available_scope_rows']}`.",
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
