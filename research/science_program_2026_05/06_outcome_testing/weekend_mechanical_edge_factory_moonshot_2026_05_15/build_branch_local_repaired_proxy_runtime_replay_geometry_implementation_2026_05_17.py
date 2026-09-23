#!/usr/bin/env python3
"""Build branch-local implementation candidates from geometry repair decisions."""

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

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_implementation import (
    RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION_SURFACE,
    aggregate_implementation_rows,
    geometry_implementation_rows,
    implementation_self_test_rows,
    research_boundary,
    system_implementation_rows,
)


GEOM_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_REPAIR"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION"

GEOMETRY_RESULT = ROUTE_DIR / f"{GEOM_PREFIX}_RESULT_2026-05-17.json"
GEOMETRY_ROW_LEDGER = ROUTE_DIR / f"{GEOM_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
GEOMETRY_AGGREGATE_LEDGER = ROUTE_DIR / f"{GEOM_PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
GEOMETRY_MISSING_FIELD_LEDGER = ROUTE_DIR / f"{GEOM_PREFIX}_MISSING_GEOMETRY_FIELD_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_implementation.py"
INPUT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_repair.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_runtime_replay_geometry_implementation_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_by(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "runtime_replay_geometry_implementation_result"),
        (ROW_LEDGER, "runtime_replay_geometry_implementation_row_ledger"),
        (AGGREGATE_LEDGER, "runtime_replay_geometry_implementation_aggregate_ledger"),
        (SELF_TEST_LEDGER, "runtime_replay_geometry_implementation_self_test_ledger"),
        (SYSTEM_LEDGER, "runtime_replay_geometry_implementation_system_ledger"),
        (SUMMARY_PATH, "runtime_replay_geometry_implementation_summary"),
        (BUILDER_MODULE, "runtime_replay_geometry_implementation_builder"),
        (VERIFIER_MODULE, "runtime_replay_geometry_implementation_verifier"),
        (HELPER_MODULE, "runtime_replay_geometry_implementation_helper"),
    ]
    return [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "status": "created",
            "type": kind,
        }
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_branch_local_repaired_proxy_runtime_replay_geometry_implementation"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 205,
        "event": "runtime_replay_geometry_implementation",
        "generated_utc": generated_at,
        "geometry_implementation_rows": counts["geometry_implementation_rows"],
        "aggregate_implementation_rows": counts["aggregate_implementation_rows"],
        "implementation_self_test_rows": counts["implementation_self_test_rows"],
        "self_test_pass_rows": counts["self_test_pass_rows"],
        "continuation": "apply branch-local implementation candidates to concrete scorer/comparator tables and source-repair tasks without a new routing layer.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 205 - Runtime Replay Geometry Implementation

Generated: {generated_at}

Trigger: continuation after Checkpoint 204. Deterministic geometry repair decisions were materialized into branch-local implementation candidates with executable self-tests.

Rows:
- geometry implementation rows: {counts['geometry_implementation_rows']}
- aggregate implementation rows: {counts['aggregate_implementation_rows']}
- self-test rows: {counts['implementation_self_test_rows']}
- self-test pass rows: {counts['self_test_pass_rows']}
- implementation kinds: {counts['implementation_kind_counts']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: apply branch-local implementation candidates to concrete scorer/comparator tables and source-repair tasks without a new routing layer.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    lines = [
        "# Runtime Replay Geometry Implementation",
        "",
        "Checkpoint 205 materializes deterministic geometry repair decisions into branch-local implementation candidates and self-tests.",
        "",
        "## Counts",
        "",
        f"- Geometry implementation rows: `{counts['geometry_implementation_rows']}`",
        f"- Aggregate implementation rows: `{counts['aggregate_implementation_rows']}`",
        f"- Self-test rows: `{counts['implementation_self_test_rows']}`",
        f"- Self-test pass rows: `{counts['self_test_pass_rows']}`",
        "",
        "## Implementation Kinds",
        "",
    ]
    for kind, count in counts["implementation_kind_counts"].items():
        lines.append(f"- `{kind}`: `{count}`")
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            "Apply the branch-local implementation candidates into concrete scorer/comparator tables and source-repair tasks without adding a routing layer.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    generated_at = now_utc()
    geometry_result = read_json(GEOMETRY_RESULT)
    geometry_rows = read_jsonl(GEOMETRY_ROW_LEDGER)
    aggregate_geometry = read_jsonl(GEOMETRY_AGGREGATE_LEDGER)
    missing_geometry = read_jsonl(GEOMETRY_MISSING_FIELD_LEDGER)

    implementation_rows = geometry_implementation_rows(geometry_rows)
    aggregate_rows = aggregate_implementation_rows(aggregate_geometry, implementation_rows)
    self_tests = implementation_self_test_rows(implementation_rows)
    system_rows = system_implementation_rows(implementation_rows, aggregate_rows, self_tests)

    counts = {
        "input_geometry_result_ok": 1 if geometry_result.get("ok") else 0,
        "input_geometry_repair_rows": len(geometry_rows),
        "input_aggregate_geometry_rows": len(aggregate_geometry),
        "input_missing_geometry_field_rows": len(missing_geometry),
        "geometry_implementation_rows": len(implementation_rows),
        "aggregate_implementation_rows": len(aggregate_rows),
        "implementation_self_test_rows": len(self_tests),
        "system_implementation_rows": len(system_rows),
        "self_test_pass_rows": sum(
            row.get("implementation_self_test_status") == "GEOMETRY_IMPLEMENTATION_SELF_TEST_PASS"
            for row in self_tests
        ),
        "self_test_repair_rows": sum(
            row.get("implementation_self_test_status") != "GEOMETRY_IMPLEMENTATION_SELF_TEST_PASS"
            for row in self_tests
        ),
        "implementation_kind_counts": count_by(implementation_rows, "implementation_kind"),
        "implementation_action_counts": count_by(implementation_rows, "implementation_action"),
        "aggregate_implementation_action_counts": count_by(aggregate_rows, "aggregate_implementation_action"),
    }

    result = {
        "artifact": PREFIX,
        "ok": True,
        "generated_utc": generated_at,
        "runtime_replay_geometry_implementation_surface": RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION_SURFACE,
        "research_boundary": research_boundary(),
        "counts": counts,
        "inputs": {
            "geometry_result": str(GEOMETRY_RESULT.relative_to(REPO)).replace("\\", "/"),
            "geometry_row_ledger": str(GEOMETRY_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "geometry_aggregate_ledger": str(GEOMETRY_AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "geometry_missing_field_ledger": str(GEOMETRY_MISSING_FIELD_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
    }

    write_jsonl(ROW_LEDGER, implementation_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_json(RESULT_PATH, result)
    write_text(SUMMARY_PATH, build_summary(counts))
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)

    result["output_sha256"] = {
        "row_ledger_sha256": sha256_file(ROW_LEDGER),
        "aggregate_ledger_sha256": sha256_file(AGGREGATE_LEDGER),
        "self_test_ledger_sha256": sha256_file(SELF_TEST_LEDGER),
        "system_ledger_sha256": sha256_file(SYSTEM_LEDGER),
    }
    write_json(RESULT_PATH, result)
    print(json.dumps({"artifact": PREFIX, "counts": counts, "generated_utc": generated_at, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
