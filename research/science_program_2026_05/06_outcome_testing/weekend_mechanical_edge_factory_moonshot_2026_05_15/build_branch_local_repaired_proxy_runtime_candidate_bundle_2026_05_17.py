#!/usr/bin/env python3
"""Build branch-local runtime-candidate bundles from repaired-proxy registration specs."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_repaired_proxy_runtime_candidate_bundle import (
    RUNTIME_CANDIDATE_BUNDLE_SURFACE,
    guard_check_rows,
    nonregistration_review_rows,
    research_boundary,
    runtime_candidate_bucket_rows,
    runtime_candidate_rows,
    symbol_candidate_bundle_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REGISTRATION_SPECS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
REGISTRATION_SPEC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REGISTRATION_SPEC_LEDGER_2026-05-17.jsonl"
RUNTIME_GUARD_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_GUARD_LEDGER_2026-05-17.jsonl"
SYMBOL_REGISTRATION_SUMMARY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_REGISTRATION_SUMMARY_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_CONTEXT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONREGISTRATION_CONTEXT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_candidate_bundle.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_registration_specs.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_candidate_bundle_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_RUNTIME_CANDIDATE_LEDGER_2026-05-17.jsonl"
GUARD_CHECK_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_CHECK_LEDGER_2026-05-17.jsonl"
SYMBOL_CANDIDATE_BUNDLE_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_CANDIDATE_BUNDLE_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REVIEW_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_REVIEW_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_text(path: Path, text: str) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def replace_sprint_event(path: Path, row: dict[str, Any]) -> None:
    event = row.get("event")
    route = row.get("route")
    retained: list[str] = []
    if path.exists():
        with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    retained.append(line.rstrip("\r\n"))
                    continue
                if existing.get("event") == event and existing.get("route") == route:
                    continue
                retained.append(line.rstrip("\r\n"))
    retained.append(json.dumps(row, sort_keys=True))
    write_text(path, "\n".join(retained) + "\n")


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
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SRCMAN-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "generated_utc": generated_at,
                "research_boundary": research_boundary(),
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    output = dict(row)
    output["generated_utc"] = generated_at
    output["source_manifest_hash"] = manifest_hash
    output.setdefault("runtime_candidate_bundle_surface", RUNTIME_CANDIDATE_BUNDLE_SURFACE)
    output.setdefault("research_boundary", research_boundary())
    return output


def update_output_manifest(entries: list[tuple[Path, str]]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    artifacts = manifest.setdefault("artifacts", [])
    existing = {str(item.get("path")) for item in artifacts}
    for path, artifact_type in entries:
        rel = path.relative_to(REPO).as_posix()
        if rel in existing:
            continue
        artifacts.append({"path": rel, "status": "created", "type": artifact_type})
        existing.add(rel)
    write_json(OUTPUT_MANIFEST, manifest)


def system_action_row(counts: dict[str, int], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    return with_common(
        {
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SYSTEM-0001",
            "recommendation": (
                "Carry the 223 guarded branch-local runtime candidates into the next symbol/session/horizon "
                "rollup and keep nonregistration review rows outside the candidate bundle."
            ),
            "next_branch_local_actions": [
                "roll_up_runtime_candidates_by_symbol_session_horizon",
                "register_branch_local_candidate_bundle_module",
                "keep_nonregistration_review_rows_separate",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Runtime Candidate Bundle",
        "",
        f"Generated UTC: `{generated_at}`",
        "",
        "Branch-local research boundary schema: `concrete_branch_local_research_boundary_v1`.",
        "",
        "## Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: `{counts[key]}`")
    lines.extend(
        [
            "",
            "## Continuation",
            "",
            "Roll runtime candidates up by symbol, session, and horizon, then register a branch-local module surface.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 186 - Runtime Candidate Bundle\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 186 - Runtime Candidate Bundle

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 185. Registration specs were converted into branch-local runtime candidate rows with explicit guard checks and symbol bundle rollups.

Outputs:

- `{counts['runtime_candidate_rows']}` runtime candidate rows from `{counts['input_registration_spec_rows']}` registration specs.
- `{counts['guard_check_rows']}` guard-check rows, with `{counts['guard_check_passed_rows']}` passed and `{counts['guard_check_blocked_rows']}` blocked.
- `{counts['symbol_candidate_bundle_rows']}` symbol/session/horizon candidate bundle rows.
- `{counts['nonregistration_review_rows']}` nonregistration review rows kept outside the candidate bundle.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: roll the candidate bundle into a branch-local module/registry surface and keep source-exhaustion proof attached.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    spec_rows_in = read_jsonl(REGISTRATION_SPEC_LEDGER)
    runtime_guard_rows_in = read_jsonl(RUNTIME_GUARD_LEDGER)
    symbol_summary_rows_in = read_jsonl(SYMBOL_REGISTRATION_SUMMARY_LEDGER)
    nonregistration_rows_in = read_jsonl(NONREGISTRATION_CONTEXT_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            REGISTRATION_SPEC_LEDGER,
            RUNTIME_GUARD_LEDGER,
            SYMBOL_REGISTRATION_SUMMARY_LEDGER,
            NONREGISTRATION_CONTEXT_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    candidate_rows = [with_common(row, generated_at, manifest_hash) for row in runtime_candidate_rows(spec_rows_in)]
    guard_rows = [
        with_common(row, generated_at, manifest_hash) for row in guard_check_rows(candidate_rows, runtime_guard_rows_in)
    ]
    bundle_rows = [
        with_common(row, generated_at, manifest_hash) for row in symbol_candidate_bundle_rows(candidate_rows, guard_rows)
    ]
    nonregistration_review = [
        with_common(row, generated_at, manifest_hash) for row in nonregistration_review_rows(nonregistration_rows_in)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in runtime_candidate_bucket_rows(candidate_rows, guard_rows, bundle_rows, nonregistration_review)
    ]
    default_candidates = sum(
        1
        for row in candidate_rows
        if row.get("runtime_candidate_family") == "branch_local_default_off_repaired_proxy_scorer_candidate"
    )
    avoid_candidates = sum(
        1
        for row in candidate_rows
        if row.get("runtime_candidate_family") == "branch_local_avoid_redesign_repaired_proxy_comparator_candidate"
    )
    guard_passed = sum(1 for row in guard_rows if row.get("guard_check_passed") is True)
    counts = {
        "input_registration_result_ok": int(bool(input_result.get("ok"))),
        "input_registration_spec_rows": len(spec_rows_in),
        "input_runtime_guard_rows": len(runtime_guard_rows_in),
        "input_symbol_registration_summary_rows": len(symbol_summary_rows_in),
        "input_nonregistration_context_rows": len(nonregistration_rows_in),
        "runtime_candidate_rows": len(candidate_rows),
        "default_off_runtime_candidate_rows": default_candidates,
        "avoid_redesign_runtime_candidate_rows": avoid_candidates,
        "guard_check_rows": len(guard_rows),
        "guard_check_passed_rows": guard_passed,
        "guard_check_blocked_rows": len(guard_rows) - guard_passed,
        "symbol_candidate_bundle_rows": len(bundle_rows),
        "nonregistration_review_rows": len(nonregistration_review),
        "bucket_rows": len(bucket_rows),
        "system_action_rows": 1,
        "source_manifest_rows": len(source_rows),
    }
    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(RUNTIME_CANDIDATE_LEDGER, candidate_rows)
    write_jsonl(GUARD_CHECK_LEDGER, guard_rows)
    write_jsonl(SYMBOL_CANDIDATE_BUNDLE_LEDGER, bundle_rows)
    write_jsonl(NONREGISTRATION_REVIEW_LEDGER, nonregistration_review)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_runtime_candidate_bundle_result"),
            (RUNTIME_CANDIDATE_LEDGER, "repaired_proxy_runtime_candidate_ledger"),
            (GUARD_CHECK_LEDGER, "repaired_proxy_runtime_candidate_guard_check_ledger"),
            (SYMBOL_CANDIDATE_BUNDLE_LEDGER, "repaired_proxy_runtime_symbol_candidate_bundle_ledger"),
            (NONREGISTRATION_REVIEW_LEDGER, "repaired_proxy_runtime_nonregistration_review_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_runtime_candidate_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_runtime_candidate_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_runtime_candidate_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_runtime_candidate_summary"),
            (BUILDER_MODULE, "repaired_proxy_runtime_candidate_builder"),
            (VERIFIER_MODULE, "repaired_proxy_runtime_candidate_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_runtime_candidate_bundle_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Materialized repaired-proxy registration specs into branch-local runtime candidates.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
