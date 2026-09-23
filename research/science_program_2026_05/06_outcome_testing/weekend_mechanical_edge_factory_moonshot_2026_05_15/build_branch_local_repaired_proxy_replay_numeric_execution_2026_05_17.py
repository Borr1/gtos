#!/usr/bin/env python3
"""Execute repaired-proxy replay contracts into numeric source/event rows."""

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

from src.research_infra.moonshot_repaired_proxy_replay_numeric_execution import (
    REPLAY_NUMERIC_SURFACE,
    bucket_rows,
    control_numeric_event_row,
    metric_lookup,
    replay_numeric_event_row,
    research_boundary,
    scope_row_lookup,
    source_numeric_metric_row,
    symbol_summary_rows,
)


CONTRACT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_CONTRACTS"
REGISTRY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_NUMERIC_EXECUTION"

CONTRACT_RESULT = ROUTE_DIR / f"{CONTRACT_PREFIX}_RESULT_2026-05-17.json"
REPLAY_SCOPE_CONTRACT_LEDGER = ROUTE_DIR / f"{CONTRACT_PREFIX}_REPLAY_SCOPE_CONTRACT_LEDGER_2026-05-17.jsonl"
CONTROL_POPULATION_CONTRACT_LEDGER = ROUTE_DIR / f"{CONTRACT_PREFIX}_CONTROL_POPULATION_CONTRACT_LEDGER_2026-05-17.jsonl"
REPAIR_SCOPE_LEDGER = ROUTE_DIR / f"{CONTRACT_PREFIX}_REPAIR_SCOPE_LEDGER_2026-05-17.jsonl"
DEFAULT_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{REGISTRY_PREFIX}_DEFAULT_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
AVOID_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{REGISTRY_PREFIX}_AVOID_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_replay_numeric_execution.py"
CONTRACT_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_replay_population.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_replay_numeric_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_NUMERIC_METRIC_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_NUMERIC_METRIC_LEDGER_2026-05-17.jsonl"
REPLAY_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
CONTROL_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
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


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_text(path: Path, text: str) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-NUM-SRC-{index:04d}",
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
    output.setdefault("replay_numeric_surface", REPLAY_NUMERIC_SURFACE)
    output.setdefault("research_boundary", research_boundary())
    return output


def source_rows_from_contracts(
    replay_contracts: list[dict[str, Any]],
    control_contracts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_path: dict[str, dict[str, Any]] = {}
    for row in replay_contracts:
        path = str(row.get("market_source_path") or "")
        if path and path not in rows_by_path:
            rows_by_path[path] = row
    for row in control_contracts:
        path = str(row.get("source_path") or "")
        if path and path not in rows_by_path:
            rows_by_path[path] = row
    return [rows_by_path[path] for path in sorted(rows_by_path)]


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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPLAY-NUM-SYSTEM-0001",
            "recommendation": (
                "Use replay numeric event rows as the immediate branch-local feature input, join control numeric rows "
                "as cross-market context, then rerun repaired-proxy registry scoring with these streamed source metrics."
            ),
            "next_branch_local_actions": [
                "rerun_default_off_registry_scores_with_replay_numeric_metrics",
                "rerun_avoid_comparators_with_replay_numeric_metrics",
                "join_control_numeric_rows_as_cross_market_context",
                "rebuild_exact_proxy_bridge_after_numeric_replay_score_rerun",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Replay Numeric Execution",
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
            (
                "Rerun default-off registry scores and avoid comparators with replay numeric metrics, join control "
                "numeric rows as cross-market context, and rebuild the exact/proxy bridge after the score rerun."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    text = f"""

## Checkpoint 174 - Replay Contracts Executed Into Numeric Source Rows

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 173. Replay scope contracts and control population contracts were executed against local CSV sources with bounded streaming source metrics.

Outputs:

- `{counts['source_numeric_metric_rows']}` source numeric metric rows, preserving the full unique source denominator from replay/control contracts.
- `{counts['replay_numeric_event_rows']}` replay numeric event rows, preserving the full `5,324` replay scope contract denominator.
- `{counts['control_numeric_event_rows']}` control numeric event rows, preserving the full `173` control population contract denominator.
- `{counts['symbol_summary_rows']}` symbol summary rows, `{counts['bucket_rows']}` bucket rows, and `1` system action row for the score-rerun pass.
- Source metric failures: `{counts['source_numeric_metric_failures']}`.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: rerun default-off registry scores and avoid comparators with replay numeric metrics, join control numeric rows as cross-market context, and rebuild the exact/proxy bridge after the score rerun.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    contract_result = read_json(CONTRACT_RESULT)
    replay_contracts = read_jsonl(REPLAY_SCOPE_CONTRACT_LEDGER)
    control_contracts = read_jsonl(CONTROL_POPULATION_CONTRACT_LEDGER)
    default_scopes = read_jsonl(DEFAULT_SCOPE_REGISTRY_LEDGER)
    avoid_scopes = read_jsonl(AVOID_SCOPE_REGISTRY_LEDGER)
    repair_scopes = read_jsonl(REPAIR_SCOPE_LEDGER)

    source_rows, manifest_hash = source_manifest_rows(
        [
            CONTRACT_RESULT,
            REPLAY_SCOPE_CONTRACT_LEDGER,
            CONTROL_POPULATION_CONTRACT_LEDGER,
            DEFAULT_SCOPE_REGISTRY_LEDGER,
            AVOID_SCOPE_REGISTRY_LEDGER,
            REPAIR_SCOPE_LEDGER,
            HELPER_MODULE,
            CONTRACT_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    metric_source_rows = source_rows_from_contracts(replay_contracts, control_contracts)
    source_metric_rows = [
        with_common(source_numeric_metric_row(row, REPO, index), generated_at, manifest_hash)
        for index, row in enumerate(metric_source_rows, 1)
    ]
    metrics_by_path = metric_lookup(source_metric_rows)
    scopes_by_id = scope_row_lookup(default_scopes, avoid_scopes, repair_scopes)
    replay_rows = [
        with_common(
            replay_numeric_event_row(
                row,
                metrics_by_path[str(row.get("market_source_path") or "")],
                scopes_by_id.get(str(row.get("input_registry_scope_row_id") or "")),
                index,
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(replay_contracts, 1)
    ]
    control_rows = [
        with_common(
            control_numeric_event_row(row, metrics_by_path[str(row.get("source_path") or "")], index),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(control_contracts, 1)
    ]
    symbol_rows = [
        with_common(row, generated_at, manifest_hash) for row in symbol_summary_rows(replay_rows, control_rows)
    ]
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in bucket_rows(source_metric_rows, replay_rows, control_rows)
    ]

    source_failures = sum(
        1 for row in source_metric_rows if row.get("numeric_metric_status") != "SOURCE_NUMERIC_METRICS_READY"
    )
    counts = {
        "input_replay_scope_contract_rows": len(replay_contracts),
        "input_control_population_contract_rows": len(control_contracts),
        "source_numeric_metric_rows": len(source_metric_rows),
        "source_numeric_metric_failures": source_failures,
        "replay_numeric_event_rows": len(replay_rows),
        "control_numeric_event_rows": len(control_rows),
        "symbol_summary_rows": len(symbol_rows),
        "system_action_rows": 1,
        "bucket_rows": len(bucket_output_rows),
        "source_manifest_rows": len(source_rows),
    }
    system_rows = [system_action_row(counts, generated_at, manifest_hash)]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "counts": counts,
        "upstream_counts": contract_result.get("counts", {}),
        "replay_contract_denominator_preserved": counts["replay_numeric_event_rows"]
        == contract_result.get("counts", {}).get("replay_scope_contract_rows"),
        "control_contract_denominator_preserved": counts["control_numeric_event_rows"]
        == contract_result.get("counts", {}).get("control_population_contract_rows"),
        "source_manifest_hash": manifest_hash,
        "system_recommendation": system_rows[0]["recommendation"],
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(SOURCE_NUMERIC_METRIC_LEDGER, source_metric_rows)
    write_jsonl(REPLAY_NUMERIC_EVENT_LEDGER, replay_rows)
    write_jsonl(CONTROL_NUMERIC_EVENT_LEDGER, control_rows)
    write_jsonl(SYMBOL_SUMMARY_LEDGER, symbol_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_replay_numeric_execution_result"),
            (SOURCE_NUMERIC_METRIC_LEDGER, "repaired_proxy_replay_numeric_source_metric_ledger"),
            (REPLAY_NUMERIC_EVENT_LEDGER, "repaired_proxy_replay_numeric_event_ledger"),
            (CONTROL_NUMERIC_EVENT_LEDGER, "repaired_proxy_replay_numeric_control_ledger"),
            (SYMBOL_SUMMARY_LEDGER, "repaired_proxy_replay_numeric_symbol_summary_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_replay_numeric_system_action_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_replay_numeric_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_replay_numeric_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_replay_numeric_summary"),
            (BUILDER_MODULE, "repaired_proxy_replay_numeric_builder"),
            (VERIFIER_MODULE, "repaired_proxy_replay_numeric_verifier"),
        ]
    )
    append_jsonl(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_replay_numeric_execution_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": (
                "Executed replay and control contracts into streamed source numeric metrics and branch-local numeric rows."
            ),
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
