#!/usr/bin/env python3
"""Build source-expansion execution rows from CP265 acquisition-proof evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_proxy_r_performance import (
    cost_proxy_for_symbol,
    discover_ohlc_csv_sources,
    load_ohlc_rows,
    score_source_session_horizon,
    source_aliases,
    symbol_key,
)
from src.research_infra.moonshot_expanded_market_source_expansion_execution import (
    EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION,
    aggregate_key,
    aggregate_rows_from_buckets,
    alternate_sources_for_row,
    boundary_row,
    empty_bucket,
    research_boundary,
    source_expansion_execution_row,
    source_expansion_gap_row,
    source_index_by_alias_timeframe,
    stable_text_sha256,
    update_bucket,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_EXECUTION"
COST_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
COST_SYMBOL_LEDGER = ROUTE_DIR / f"{COST_PREFIX}_COST_SYMBOL_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_GAP_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GAP_PROOF_LEDGER_2026-05-17.jsonl"
INPUT_CONSUMPTION_LEDGER = ROUTE_DIR / f"{PREFIX}_INPUT_CONSUMPTION_LEDGER_2026-05-17.jsonl"
DISCOVERED_SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_DISCOVERED_OHLC_SOURCE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return list(iter_jsonl(path))


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


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def searched_aliases(row: dict[str, Any]) -> list[str]:
    aliases: set[str] = set()
    for field in (row.get("symbol"), row.get("source_symbol"), row.get("symbol_family")):
        aliases.update(source_aliases(field))
    return sorted(alias for alias in aliases if alias)


def source_roots(sources: list[dict[str, Any]]) -> list[str]:
    roots = {str(Path(str(source.get("source_path") or "")).parts[0]) for source in sources}
    return sorted(root for root in roots if root and root != ".")


def score_cache_key(
    source: dict[str, Any],
    row: dict[str, Any],
    cost_proxy: dict[str, Any],
) -> tuple[str, str, str, str, str, str]:
    return (
        str(source.get("source_path")),
        str(row.get("route_session")),
        str(row.get("horizon_id")),
        str(row.get("side")),
        str(cost_proxy.get("cost_adjustment_r")),
        str(cost_proxy.get("stress_cost_adjustment_r")),
    )


def target_source_expansion_row(row: dict[str, Any]) -> bool:
    return (
        row.get("evidence_preservation_class") == "source-expansion-acquisition-proof"
        and row.get("source_repair_reachability_class") == "source-expansion-new-source-required"
    )


def input_consumption_row(
    evidence: dict[str, Any],
    sequence: int,
    candidate_count: int,
    execution_count: int,
    scored_count: int,
    gap_count: int,
    aliases: list[str],
) -> dict[str, Any]:
    if scored_count:
        status = "SOURCE_EXPANSION_INPUT_CONSUMED_IN_SIMULATED_R_EXECUTION"
    elif execution_count:
        status = "SOURCE_EXPANSION_INPUT_CONSUMED_IN_NONCOMPUTABLE_ALTERNATE_EXECUTION"
    else:
        status = "SOURCE_EXPANSION_INPUT_CONSUMED_IN_SOURCE_GAP_PROOF"
    return boundary_row(
        {
            "expanded_market_source_expansion_input_consumption_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-CONSUME-{sequence:07d}"
            ),
            "input_acceptance_execution_evidence_row_id": evidence.get(
                "expanded_market_repair_implementation_acceptance_evidence_execution_row_id"
            ),
            "input_source_repair_reachability_row_id": evidence.get(
                "input_source_repair_reachability_row_id"
            ),
            "input_action_class_performance_row_id": evidence.get(
                "input_action_class_performance_row_id"
            ),
            "source_expansion_input_consumption_status": status,
            "symbol_family": evidence.get("symbol_family"),
            "symbol": evidence.get("symbol"),
            "source_symbol": evidence.get("source_symbol"),
            "market_timeframe": evidence.get("market_timeframe"),
            "route_session": evidence.get("route_session"),
            "horizon_id": evidence.get("horizon_id"),
            "side": evidence.get("side"),
            "source_path": evidence.get("source_path"),
            "source_path_sha256": stable_text_sha256(evidence.get("source_path")),
            "source_file_sha256": evidence.get("source_file_sha256"),
            "searched_symbol_aliases": aliases,
            "candidate_alternate_source_count": candidate_count,
            "execution_rows_generated": execution_count,
            "execution_rows_with_simulated_r": scored_count,
            "source_gap_rows_generated": gap_count,
            "missing_simulated_fields": []
            if scored_count
            else ["additional_replay_source_path_hash_for_scope"],
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_INPUT_CONSUMED"
                if scored_count
                else "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_INPUT_CONSUMED_WITH_PROOF"
            ),
        }
    )


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_source_expansion_execution_result"),
        (EXECUTION_LEDGER, "expanded_market_source_expansion_execution_rows"),
        (SOURCE_GAP_PROOF_LEDGER, "expanded_market_source_expansion_gap_proof_rows"),
        (INPUT_CONSUMPTION_LEDGER, "expanded_market_source_expansion_input_consumption"),
        (DISCOVERED_SOURCE_LEDGER, "expanded_market_source_expansion_discovered_sources"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    types = {entry["type"] for entry in entries}
    existing = manifest.setdefault("artifacts", [])
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + entries
    manifest["latest_expanded_market_source_expansion_execution"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept_lines: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    kept_lines.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept_lines.append(json.dumps(row, sort_keys=True))
    kept_lines.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 266 - Expanded-Market Source Expansion Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: owner correction after Checkpoint 265. The next plate pivoted away from another repair-acceptance wrapper and consumed the preserved source-expansion acquisition-proof rows into alternate local OHLC source execution rows or exact local source-gap proof.

Rows:
- input source-expansion proof rows consumed: {counts["input_source_expansion_rows"]}
- discovered local OHLC CSV source rows: {counts["discovered_ohlc_source_rows"]}
- source-expansion execution rows: {counts["source_expansion_execution_rows"]}
- execution rows with simulated R: {counts["execution_rows_with_simulated_r"]}
- source gap proof rows: {counts["source_gap_proof_rows"]}
- input consumption rows: {counts["input_consumption_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: continue to the next highest-value numeric source/replay plate; do not return to same-bundle, registry, recommendation, relay, or wrapper-only work.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Execution",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint consumes the CP265 source-expansion acquisition-proof rows and scores every reachable same-symbol/timeframe alternate OHLC source discovered locally. Rows without an alternate local source are preserved as row-level source-gap proof.",
            "",
            "## Counts",
            "",
            f"- Input source-expansion proof rows: `{counts['input_source_expansion_rows']}`",
            f"- Discovered local OHLC CSV sources: `{counts['discovered_ohlc_source_rows']}`",
            f"- Source-expansion execution rows: `{counts['source_expansion_execution_rows']}`",
            f"- Execution rows with simulated R: `{counts['execution_rows_with_simulated_r']}`",
            f"- Source-gap proof rows: `{counts['source_gap_proof_rows']}`",
            f"- Input consumption rows: `{counts['input_consumption_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Continue to the next highest-value numeric source/replay plate after this checkpoint is committed.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    cost_rows = read_jsonl(COST_SYMBOL_LEDGER)
    cost_by_symbol = {symbol_key(row.get("symbol")): row for row in cost_rows}
    discovered_sources = discover_ohlc_csv_sources(REPO)
    source_index = source_index_by_alias_timeframe(discovered_sources)
    roots = source_roots(discovered_sources)

    ohlc_cache: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    score_cache: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    decisions: Counter[str] = Counter()
    candidate_count_distribution: Counter[int] = Counter()
    issues: list[dict[str, Any]] = []

    input_rows = 0
    execution_rows = 0
    scored_execution_rows = 0
    noncomputable_execution_rows = 0
    gap_rows = 0
    input_consumption_rows = 0
    source_path_count: set[str] = set()
    symbol_count: set[str] = set()

    def loaded_rows(source: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        source_path = str(source.get("source_path") or "")
        if source_path not in ohlc_cache:
            rows, meta = load_ohlc_rows(REPO, source_path)
            source.update(meta)
            ohlc_cache[source_path] = (rows, meta)
        return ohlc_cache[source_path]

    with (
        open(long_path(EXECUTION_LEDGER), "w", encoding="utf-8", newline="\n") as execution_handle,
        open(long_path(SOURCE_GAP_PROOF_LEDGER), "w", encoding="utf-8", newline="\n") as gap_handle,
        open(long_path(INPUT_CONSUMPTION_LEDGER), "w", encoding="utf-8", newline="\n") as consume_handle,
    ):
        for evidence in iter_jsonl(INPUT_EVIDENCE_LEDGER):
            if not target_source_expansion_row(evidence):
                continue
            input_rows += 1
            aliases = searched_aliases(evidence)
            candidates = alternate_sources_for_row(evidence, source_index)
            candidate_count_distribution[len(candidates)] += 1
            per_input_executions = 0
            per_input_scored = 0
            per_input_gaps = 0
            symbol_count.add(str(evidence.get("symbol") or ""))

            if not candidates:
                gap_rows += 1
                per_input_gaps = 1
                gap = source_expansion_gap_row(evidence, gap_rows, len(discovered_sources), aliases, roots)
                gap_handle.write(json.dumps(gap, sort_keys=True) + "\n")
                decisions[gap.get("keep_kill_redesign_implement_decision")] += 1
                update_bucket(buckets[aggregate_key(gap, "gap")], gap, "gap")
            else:
                for source in candidates:
                    rows, meta = loaded_rows(source)
                    source.update(meta)
                    cost_proxy = cost_proxy_for_symbol(str(evidence.get("symbol") or ""), cost_by_symbol)
                    cache_key = score_cache_key(source, evidence, cost_proxy)
                    if cache_key not in score_cache:
                        score_cache[cache_key] = score_source_session_horizon(
                            source,
                            rows,
                            str(evidence.get("route_session") or ""),
                            str(evidence.get("horizon_id") or ""),
                            str(evidence.get("side") or ""),
                            cost_proxy,
                        )
                    score = score_cache[cache_key]
                    execution_rows += 1
                    per_input_executions += 1
                    execution = source_expansion_execution_row(evidence, source, score, execution_rows)
                    execution_handle.write(json.dumps(execution, sort_keys=True) + "\n")
                    if execution.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED":
                        scored_execution_rows += 1
                        per_input_scored += 1
                    else:
                        noncomputable_execution_rows += 1
                    decisions[execution.get("keep_kill_redesign_implement_decision")] += 1
                    source_path_count.add(str(execution.get("source_expansion_candidate_source_path") or ""))
                    update_bucket(buckets[aggregate_key(execution, "execution")], execution, "execution")

            input_consumption_rows += 1
            consumption = input_consumption_row(
                evidence,
                input_consumption_rows,
                len(candidates),
                per_input_executions,
                per_input_scored,
                per_input_gaps,
                aliases,
            )
            consume_handle.write(json.dumps(consumption, sort_keys=True) + "\n")

    discovered_source_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_discovered_source_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-DISCOVERED-{index:05d}"
                ),
                **source,
                "source_path_sha256": stable_text_sha256(source.get("source_path")),
                "discovery_scope": "data_csv_ohlc_discovery",
            }
        )
        for index, source in enumerate(discovered_sources, 1)
    ]
    aggregate_rows = aggregate_rows_from_buckets(buckets)

    if input_rows != 3348:
        issues.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_issue_row_id": (
                        "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ISSUE-0000001"
                    ),
                    "issue_status": "INPUT_SOURCE_EXPANSION_ROW_COUNT_MISMATCH",
                    "observed_input_rows": input_rows,
                    "expected_input_rows": 3348,
                    "keep_kill_redesign_implement_decision": (
                        "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION_INPUT_SCOPE"
                    ),
                }
            )
        )

    counts = {
        "input_source_expansion_rows": input_rows,
        "discovered_ohlc_source_rows": len(discovered_source_rows),
        "source_expansion_execution_rows": execution_rows,
        "execution_rows_with_simulated_r": scored_execution_rows,
        "noncomputable_execution_rows": noncomputable_execution_rows,
        "source_gap_proof_rows": gap_rows,
        "input_consumption_rows": input_consumption_rows,
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "source_path_count": len(source_path_count),
        "symbol_count": len(symbol_count),
        "candidate_count_distribution": {
            str(key): value for key, value in sorted(candidate_count_distribution.items())
        },
        "decision_counts": dict(sorted(decisions.items())),
        "input_acceptance_execution_result_ok": input_result.get("ok"),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "input_evidence_ledger": str(INPUT_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "cost_symbol_ledger": str(COST_SYMBOL_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                    "searched_source_roots": roots,
                },
            }
        )
    ]

    output_files = [
        EXECUTION_LEDGER,
        SOURCE_GAP_PROOF_LEDGER,
        INPUT_CONSUMPTION_LEDGER,
        DISCOVERED_SOURCE_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(DISCOVERED_SOURCE_LEDGER, discovered_source_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts))
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "inputs": {
            "acceptance_execution_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "acceptance_execution_evidence_ledger": str(INPUT_EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "cost_symbol_ledger": str(COST_SYMBOL_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_gap_proof_ledger": str(SOURCE_GAP_PROOF_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "input_consumption_ledger": str(INPUT_CONSUMPTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "discovered_source_ledger": str(DISCOVERED_SOURCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_execution_surface": EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION,
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 266,
            "event": "checkpoint_266_expanded_market_source_expansion_execution",
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
