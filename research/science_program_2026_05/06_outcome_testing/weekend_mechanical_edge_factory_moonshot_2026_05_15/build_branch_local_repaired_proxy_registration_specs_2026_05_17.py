#!/usr/bin/env python3
"""Build branch-local registration specs from repaired-proxy symbol action packets."""

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

from src.research_infra.moonshot_repaired_proxy_registration_specs import (
    REGISTRATION_SPEC_SURFACE,
    nonregistration_context_rows,
    registration_bucket_rows,
    registration_spec_rows,
    research_boundary,
    runtime_guard_rows,
    symbol_registration_summary_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REGISTRATION_SPECS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
SYMBOL_ACTION_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_ACTION_PACKET_LEDGER_2026-05-17.jsonl"
COMPARATOR_REGISTRATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARATOR_REGISTRATION_LEDGER_2026-05-17.jsonl"
COMPARATOR_NONREGISTRATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARATOR_NONREGISTRATION_LEDGER_2026-05-17.jsonl"
SYMBOL_PROXY_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_PROXY_SURFACE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_registration_specs.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_symbol_action_packet.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_registration_specs_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REGISTRATION_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRATION_SPEC_LEDGER_2026-05-17.jsonl"
RUNTIME_GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_RUNTIME_GUARD_LEDGER_2026-05-17.jsonl"
SYMBOL_REGISTRATION_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_REGISTRATION_SUMMARY_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_CONTEXT_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-REGISTRATION-SRCMAN-{index:04d}",
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
    output.setdefault("registration_spec_surface", REGISTRATION_SPEC_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-REGISTRATION-SYSTEM-0001",
            "recommendation": (
                "Use branch-local registration specs as the executable comparator registration bundle; carry "
                "nonregistration context separately and keep all specs outside production import paths."
            ),
            "next_branch_local_actions": [
                "execute_registration_specs_into_runtime_candidate_bundle",
                "roll_up_registration_specs_by_symbol_session_horizon",
                "carry_nonregistration_context_into_hold_reject_review",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Registration Specs",
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
    lines.extend(["", "## Continuation", "", "Execute registration specs into runtime candidate bundle.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 185 - Registration Specs\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 185 - Registration Specs

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 184. Comparator registration candidates were materialized into explicit branch-local registration specs and runtime guard rows.

Outputs:

- `{counts['registration_spec_rows']}` registration spec rows from `{counts['input_comparator_registration_rows']}` comparator registration candidates.
- `{counts['runtime_guard_rows']}` runtime guard rows and `{counts['symbol_registration_summary_rows']}` symbol registration summaries.
- `{counts['nonregistration_context_rows']}` nonregistration context rows preserved separately.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: execute registration specs into a runtime candidate bundle, then roll up by symbol/session/horizon.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    symbol_packet_rows_in = read_jsonl(SYMBOL_ACTION_PACKET_LEDGER)
    registration_rows_in = read_jsonl(COMPARATOR_REGISTRATION_LEDGER)
    nonregistration_rows_in = read_jsonl(COMPARATOR_NONREGISTRATION_LEDGER)
    proxy_surface_rows_in = read_jsonl(SYMBOL_PROXY_SURFACE_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            SYMBOL_ACTION_PACKET_LEDGER,
            COMPARATOR_REGISTRATION_LEDGER,
            COMPARATOR_NONREGISTRATION_LEDGER,
            SYMBOL_PROXY_SURFACE_LEDGER,
            HELPER_MODULE,
            INPUT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    spec_rows = [with_common(row, generated_at, manifest_hash) for row in registration_spec_rows(registration_rows_in)]
    guard_rows = [with_common(row, generated_at, manifest_hash) for row in runtime_guard_rows(spec_rows)]
    summary_rows = [with_common(row, generated_at, manifest_hash) for row in symbol_registration_summary_rows(spec_rows)]
    nonreg_context_rows = [
        with_common(row, generated_at, manifest_hash) for row in nonregistration_context_rows(nonregistration_rows_in)
    ]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in registration_bucket_rows(spec_rows, guard_rows, summary_rows, nonreg_context_rows)
    ]
    default_specs = sum(
        1 for row in spec_rows if row.get("registration_spec_family") == "default_off_repaired_proxy_scorer_comparator"
    )
    avoid_specs = sum(
        1 for row in spec_rows if row.get("registration_spec_family") == "avoid_redesign_repaired_proxy_comparator"
    )
    counts = {
        "input_symbol_action_result_ok": int(bool(input_result.get("ok"))),
        "input_symbol_action_packet_rows": len(symbol_packet_rows_in),
        "input_comparator_registration_rows": len(registration_rows_in),
        "input_comparator_nonregistration_rows": len(nonregistration_rows_in),
        "input_symbol_proxy_surface_rows": len(proxy_surface_rows_in),
        "registration_spec_rows": len(spec_rows),
        "default_off_registration_spec_rows": default_specs,
        "avoid_redesign_registration_spec_rows": avoid_specs,
        "runtime_guard_rows": len(guard_rows),
        "symbol_registration_summary_rows": len(summary_rows),
        "nonregistration_context_rows": len(nonreg_context_rows),
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
    write_jsonl(REGISTRATION_SPEC_LEDGER, spec_rows)
    write_jsonl(RUNTIME_GUARD_LEDGER, guard_rows)
    write_jsonl(SYMBOL_REGISTRATION_SUMMARY_LEDGER, summary_rows)
    write_jsonl(NONREGISTRATION_CONTEXT_LEDGER, nonreg_context_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_registration_specs_result"),
            (REGISTRATION_SPEC_LEDGER, "repaired_proxy_registration_spec_ledger"),
            (RUNTIME_GUARD_LEDGER, "repaired_proxy_registration_runtime_guard_ledger"),
            (SYMBOL_REGISTRATION_SUMMARY_LEDGER, "repaired_proxy_registration_symbol_summary_ledger"),
            (NONREGISTRATION_CONTEXT_LEDGER, "repaired_proxy_registration_nonregistration_context_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_registration_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_registration_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_registration_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_registration_summary"),
            (BUILDER_MODULE, "repaired_proxy_registration_builder"),
            (VERIFIER_MODULE, "repaired_proxy_registration_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_registration_specs_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Materialized comparator registration candidates into branch-local registration specs.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
