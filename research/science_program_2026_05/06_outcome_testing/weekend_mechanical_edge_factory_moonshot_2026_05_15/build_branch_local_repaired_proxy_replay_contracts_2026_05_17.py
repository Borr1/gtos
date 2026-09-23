#!/usr/bin/env python3
"""Build replay-population contracts for repaired-proxy registry scopes."""

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

from src.research_infra.moonshot_repaired_proxy_replay_population import (
    REPLAY_CONTRACT_SURFACE,
    bucket_rows,
    build_scope_rows_by_symbol,
    control_population_contract_row,
    replay_scope_contract_row,
    repair_scope_rows_from_executions,
    research_boundary,
    source_probe_row,
    symbol_summary_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_CONTRACTS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
DEFAULT_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DEFAULT_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
AVOID_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_AVOID_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
MARKET_REPLAY_NUMERIC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_REPLAY_NUMERIC_POPULATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_replay_population.py"
REGISTRY_HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_execution_registry.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_repaired_proxy_replay_contracts_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_PROBE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_PROBE_LEDGER_2026-05-17.jsonl"
REPAIR_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_SCOPE_LEDGER_2026-05-17.jsonl"
REPLAY_SCOPE_CONTRACT_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_SCOPE_CONTRACT_LEDGER_2026-05-17.jsonl"
CONTROL_POPULATION_CONTRACT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_POPULATION_CONTRACT_LEDGER_2026-05-17.jsonl"
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-CONTRACT-SRC-{index:04d}",
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
    output.setdefault("replay_contract_surface", REPLAY_CONTRACT_SURFACE)
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
            "system_action_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPLAY-CONTRACT-SYSTEM-0001",
            "recommendation": (
                "Use replay scope contracts as the immediate numeric replay work queue, use control population contracts "
                "for cross-market controls, and repair any source probes that lack OHLC columns before replay."
            ),
            "next_branch_local_actions": [
                "execute_replay_scope_contracts_into_numeric_event_rows",
                "join_control_population_contracts_as_cross_market_controls",
                "repair_source_probe_rows_without_ohlc_columns",
                "rerun_registered_scope_scores_after_replay_numeric_rows_exist",
            ],
            **counts,
        },
        generated_at,
        manifest_hash,
    )


def write_summary(path: Path, generated_at: str, counts: dict[str, int]) -> None:
    lines = [
        "# Repaired Proxy Replay Contracts",
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
                "Execute replay scope contracts into numeric event rows, join cross-market controls, and repair any "
                "source probes that fail source/header checks before replay."
            ),
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def append_checkpoint(generated_at: str, counts: dict[str, int]) -> None:
    text = f"""

## Checkpoint 173 - Registered Scopes Bound To Replay Populations

Timestamp UTC: `{generated_at}`

Trigger: continuation after Checkpoint 172. The registered repaired-proxy scopes were bound to concrete local market population files and source-header probes.

Outputs:

- `{counts['source_probe_rows']}` market source probe rows across the full `301` market population denominator.
- `{counts['repair_scope_rows']}` repair scope rows derived from the `170` repair execution rows.
- `{counts['replay_scope_contract_rows']}` replay scope contract rows binding default-off, avoid/redesign, and repair scopes to same-symbol market sources.
- `{counts['control_population_contract_rows']}` cross-market control population contract rows for market sources without registered same-symbol scopes.
- `{counts['symbol_summary_rows']}` symbol summary rows, `{counts['bucket_rows']}` bucket rows, and `1` system action row for the next numeric replay pass.

Boundary: new outputs use concrete branch-local research boundaries and do not add legacy defensive status-token blocks.

Immediate continuation: execute replay scope contracts into numeric event rows, join control population contracts as cross-market controls, repair source-probe failures, and rerun registered scope scores after replay numeric rows exist.
"""
    append_text(ACTIVE_LEDGER, text)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    default_scopes = read_jsonl(DEFAULT_SCOPE_REGISTRY_LEDGER)
    avoid_scopes = read_jsonl(AVOID_SCOPE_REGISTRY_LEDGER)
    repair_executions = read_jsonl(REPAIR_EXECUTION_LEDGER)
    market_rows = read_jsonl(MARKET_REPLAY_NUMERIC_LEDGER)

    source_rows, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            DEFAULT_SCOPE_REGISTRY_LEDGER,
            AVOID_SCOPE_REGISTRY_LEDGER,
            REPAIR_EXECUTION_LEDGER,
            MARKET_REPLAY_NUMERIC_LEDGER,
            HELPER_MODULE,
            REGISTRY_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    repair_scopes = repair_scope_rows_from_executions(repair_executions)
    scope_rows_by_symbol = build_scope_rows_by_symbol(default_scopes, avoid_scopes, repair_scopes)
    source_probes = [
        with_common(source_probe_row(row, REPO, index), generated_at, manifest_hash)
        for index, row in enumerate(market_rows, 1)
    ]
    probes_by_market = {
        str(row.get("input_market_replay_population_row_id") or ""): row for row in source_probes
    }

    replay_contracts: list[dict[str, Any]] = []
    control_contracts: list[dict[str, Any]] = []
    for market_row in market_rows:
        market_id = str(market_row.get("market_replay_population_row_id") or "")
        probe = probes_by_market[market_id]
        scope_rows = scope_rows_by_symbol.get(str(market_row.get("symbol") or ""), [])
        if scope_rows:
            for scope_row in scope_rows:
                replay_contracts.append(
                    with_common(
                        replay_scope_contract_row(scope_row, market_row, probe, len(replay_contracts) + 1),
                        generated_at,
                        manifest_hash,
                    )
                )
        else:
            control_contracts.append(
                with_common(
                    control_population_contract_row(market_row, probe, len(control_contracts) + 1),
                    generated_at,
                    manifest_hash,
                )
            )

    symbol_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in symbol_summary_rows(replay_contracts, control_contracts)
    ]
    bucket_output_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in bucket_rows(source_probes, replay_contracts, control_contracts)
    ]

    counts = {
        "input_default_scope_rows": len(default_scopes),
        "input_avoid_scope_rows": len(avoid_scopes),
        "input_repair_execution_rows": len(repair_executions),
        "input_market_population_rows": len(market_rows),
        "source_probe_rows": len(source_probes),
        "repair_scope_rows": len(repair_scopes),
        "replay_scope_contract_rows": len(replay_contracts),
        "control_population_contract_rows": len(control_contracts),
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
        "upstream_counts": input_result.get("counts", {}),
        "market_population_denominator_preserved": counts["source_probe_rows"]
        == input_result.get("counts", {}).get("market_replay_numeric_population_rows"),
        "source_probe_failures": sum(
            1 for row in source_probes if not row.get("source_exists") or not row.get("has_ohlc_columns")
        ),
        "system_recommendation": system_rows[0]["recommendation"],
        "source_manifest_hash": manifest_hash,
        "ok": True,
    }

    write_json(RESULT_PATH, result)
    write_jsonl(SOURCE_PROBE_LEDGER, source_probes)
    write_jsonl(REPAIR_SCOPE_LEDGER, [with_common(row, generated_at, manifest_hash) for row in repair_scopes])
    write_jsonl(REPLAY_SCOPE_CONTRACT_LEDGER, replay_contracts)
    write_jsonl(CONTROL_POPULATION_CONTRACT_LEDGER, control_contracts)
    write_jsonl(SYMBOL_SUMMARY_LEDGER, symbol_rows)
    write_jsonl(SYSTEM_ACTION_LEDGER, system_rows)
    write_jsonl(BUCKET_LEDGER, bucket_output_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(SUMMARY_PATH, generated_at, counts)

    update_output_manifest(
        [
            (RESULT_PATH, "repaired_proxy_replay_contracts_result"),
            (SOURCE_PROBE_LEDGER, "repaired_proxy_replay_contracts_source_probe_ledger"),
            (REPAIR_SCOPE_LEDGER, "repaired_proxy_replay_contracts_repair_scope_ledger"),
            (REPLAY_SCOPE_CONTRACT_LEDGER, "repaired_proxy_replay_contracts_scope_contract_ledger"),
            (CONTROL_POPULATION_CONTRACT_LEDGER, "repaired_proxy_replay_contracts_control_population_ledger"),
            (SYMBOL_SUMMARY_LEDGER, "repaired_proxy_replay_contracts_symbol_summary_ledger"),
            (SYSTEM_ACTION_LEDGER, "repaired_proxy_replay_contracts_system_action_ledger"),
            (BUCKET_LEDGER, "repaired_proxy_replay_contracts_bucket_ledger"),
            (SOURCE_MANIFEST_LEDGER, "repaired_proxy_replay_contracts_source_manifest_ledger"),
            (SUMMARY_PATH, "repaired_proxy_replay_contracts_summary"),
            (BUILDER_MODULE, "repaired_proxy_replay_contracts_builder"),
            (VERIFIER_MODULE, "repaired_proxy_replay_contracts_verifier"),
        ]
    )
    append_jsonl(
        SPRINT_LEDGER,
        {
            "timestamp_utc": generated_at,
            "event": "repaired_proxy_replay_contracts_built",
            "route": PREFIX,
            "counts": counts,
            "research_boundary": research_boundary(),
            "summary": (
                "Bound registered repaired-proxy scopes to local market replay populations and source-header probes."
            ),
        },
    )
    append_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
