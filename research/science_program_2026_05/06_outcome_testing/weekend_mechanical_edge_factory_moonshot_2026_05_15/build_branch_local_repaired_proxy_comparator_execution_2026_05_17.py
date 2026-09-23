#!/usr/bin/env python3
"""Build branch-local comparator execution rows for repaired-proxy comparator inputs."""

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

from src.research_infra.moonshot_repaired_proxy_comparator_execution import (
    COMPARATOR_EXECUTION_SURFACE,
    comparator_action_rows,
    comparator_bucket_rows,
    comparator_execution_rows,
    proxy_r_surface_rows,
    research_boundary,
    symbol_execution_summary_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_INPUT_REPAIR_WORK"
EXHAUST_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_SOURCE_EXHAUSTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_EXECUTION"

COMPARATOR_INPUT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARATOR_INPUT_LEDGER_2026-05-17.jsonl"
COMPARATOR_INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
SOURCE_EXHAUSTION_RESULT = ROUTE_DIR / f"{EXHAUST_PREFIX}_RESULT_2026-05-17.json"
SOURCE_EXHAUSTION_GATE_LEDGER = ROUTE_DIR / f"{EXHAUST_PREFIX}_EXHAUSTION_GATE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_comparator_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_comparator_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
PROXY_R_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_PROXY_R_SURFACE_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_EXECUTION_SUMMARY_LEDGER_2026-05-17.jsonl"
COMPARATOR_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_ACTION_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-EXEC-SRCMAN-{index:04d}",
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
    output.setdefault("comparator_execution_surface", COMPARATOR_EXECUTION_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-EXEC-SYSTEM-0001",
            "recommendation": (
                "Use comparator execution rows as the current branch-local comparator surface while repair rows remain "
                "source-exhausted and exact/proxy rerun is held."
            ),
            "next_branch_local_actions": [
                "materialize_default_off_scorer_candidates_from_execution_rows",
                "materialize_avoid_redesign_comparators_from_execution_rows",
                "carry_proxy_r_surface_into_symbol_action_packet",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Comparator Execution",
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
    lines.extend(["", "## Continuation", "", "Materialize comparator execution rows into symbol action packets.", ""])
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    marker = "\n## Checkpoint 183 - Comparator Execution\n"
    existing = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            existing = handle.read()
    if marker in existing:
        write_text(ACTIVE_LEDGER, existing.split(marker, 1)[0].rstrip() + "\n")
    text = f"""

## Checkpoint 183 - Comparator Execution

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 182. Repair rows are current-branch source-exhausted, so the branch-local comparator input rows were executed against the current proxy-R surface.

Outputs:

- `{counts['comparator_execution_rows']}` comparator execution rows from `{counts['input_comparator_rows']}` comparator inputs.
- `{counts['proxy_r_surface_rows']}` proxy-R surface rows, `{counts['symbol_summary_rows']}` symbol summary rows, and `{counts['comparator_action_rows']}` comparator action rows.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: materialize comparator execution rows into symbol action packets and carry proxy-R surfaces forward while exact/proxy rerun remains gated.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    comparator_result = read_json(COMPARATOR_INPUT_RESULT)
    source_exhaustion_result = read_json(SOURCE_EXHAUSTION_RESULT)
    comparator_rows_in = read_jsonl(COMPARATOR_INPUT_LEDGER)
    source_exhaustion_gate_rows = read_jsonl(SOURCE_EXHAUSTION_GATE_LEDGER)
    source_rows, manifest_hash = source_manifest_rows(
        [
            COMPARATOR_INPUT_RESULT,
            COMPARATOR_INPUT_LEDGER,
            SOURCE_EXHAUSTION_RESULT,
            SOURCE_EXHAUSTION_GATE_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    execution_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in comparator_execution_rows(comparator_rows_in, source_exhaustion_gate_rows)
    ]
    proxy_rows = [with_common(row, generated_at, manifest_hash) for row in proxy_r_surface_rows(execution_rows)]
    summary_rows = [
        with_common(row, generated_at, manifest_hash) for row in symbol_execution_summary_rows(execution_rows)
    ]
    action_rows = [with_common(row, generated_at, manifest_hash) for row in comparator_action_rows(execution_rows)]
    bucket_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in comparator_bucket_rows(execution_rows, proxy_rows, summary_rows, action_rows)
    ]
    action_counts = {row["comparator_execution_action"]: row["comparator_execution_rows"] for row in action_rows}
    counts = {
        "input_comparator_result_ok": int(bool(comparator_result.get("ok"))),
        "input_source_exhaustion_result_ok": int(bool(source_exhaustion_result.get("ok"))),
        "input_comparator_rows": len(comparator_rows_in),
        "comparator_execution_rows": len(execution_rows),
        "proxy_r_surface_rows": len(proxy_rows),
        "symbol_summary_rows": len(summary_rows),
        "comparator_action_rows": len(action_rows),
        "bucket_rows": len(bucket_rows),
        "system_action_rows": 1,
        "source_manifest_rows": len(source_rows),
        **{f"action_{key.lower()}": value for key, value in action_counts.items()},
    }
    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "source_manifest_hash": manifest_hash,
        "source_exhaustion_gate_status": source_exhaustion_gate_rows[0].get("source_exhaustion_gate_status"),
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(COMPARATOR_EXECUTION_LEDGER, execution_rows)
    write_jsonl(PROXY_R_SURFACE_LEDGER, proxy_rows)
    write_jsonl(SYMBOL_SUMMARY_LEDGER, summary_rows)
    write_jsonl(COMPARATOR_ACTION_LEDGER, action_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)
    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_comparator_execution_result"),
            (COMPARATOR_EXECUTION_LEDGER, "repaired_proxy_comparator_execution_ledger"),
            (PROXY_R_SURFACE_LEDGER, "repaired_proxy_comparator_proxy_r_surface_ledger"),
            (SYMBOL_SUMMARY_LEDGER, "repaired_proxy_comparator_symbol_summary_ledger"),
            (COMPARATOR_ACTION_LEDGER, "repaired_proxy_comparator_action_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_comparator_execution_bucket_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_comparator_execution_system_action_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_comparator_execution_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_comparator_execution_summary"),
            (BUILDER_MODULE, "repaired_proxy_comparator_execution_builder"),
            (VERIFIER_MODULE, "repaired_proxy_comparator_execution_verifier"),
        ]
    )
    replace_sprint_event(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_comparator_execution_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": "Executed branch-local comparator input rows with source exhaustion gate attached.",
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
