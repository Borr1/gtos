#!/usr/bin/env python3
"""Build expanded-market proxy-R performance from market-population and expansion rows."""

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

from src.research_infra.moonshot_expanded_market_proxy_r_performance import (
    EXPANDED_MARKET_PROXY_R_PERFORMANCE_SURFACE,
    aggregate_performance_rows,
    boundary_row,
    cost_proxy_for_symbol,
    discover_ohlc_csv_sources,
    load_ohlc_rows,
    noncomputable_row,
    numeric_horizons,
    numeric_sessions,
    performance_row_from_score,
    research_boundary,
    score_source_session_horizon,
    sha256_file,
    source_aliases,
    symbol_key,
    system_row,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"
COMPUTED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE"
WORK_ORDER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"

MARKET_POPULATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_EXPANSION_POPULATION_LEDGER_2026-05-17.jsonl"
COST_SYMBOL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COST_SYMBOL_LEDGER_2026-05-17.jsonl"
COMPUTED_EXPANSION_MATRIX = (
    ROUTE_DIR / f"{COMPUTED_PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"
)
WORK_ORDER_EXPANSION_MATRIX = (
    ROUTE_DIR / f"{WORK_ORDER_PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"
)

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_proxy_r_performance.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_proxy_r_performance_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
NONCOMPUTABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACCESS_PROOF_LEDGER_2026-05-17.jsonl"
SEED_CONSUMPTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SEED_CONSUMPTION_LEDGER_2026-05-17.jsonl"
DISCOVERED_SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_DISCOVERED_OHLC_SOURCE_LEDGER_2026-05-17.jsonl"
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


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def index_market_population(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_path")): row for row in rows}


def source_index_by_symbol(sources: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        for alias in source_aliases(source.get("source_symbol")):
            index[alias].append(source)
    return index


def market_row_id_for_source(source: dict[str, Any], market_by_path: dict[str, dict[str, Any]]) -> str | None:
    market = market_by_path.get(str(source.get("source_path")))
    return str(market.get("market_population_row_id")) if market else None


def candidate_sources_for_seed(
    seed_row: dict[str, Any],
    source_by_path: dict[str, dict[str, Any]],
    source_by_symbol: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[str]]:
    candidates: list[dict[str, Any]] = []
    observed_paths: list[str] = []
    for path in seed_row.get("source_files") or []:
        observed_paths.append(str(path))
        source = source_by_path.get(str(path))
        if source and source.get("source_access_status") == "OHLC_CSV_REACHABLE":
            candidates.append(source)
    if not candidates:
        for alias in source_aliases(seed_row.get("symbol")):
            candidates.extend(source_by_symbol.get(alias, []))
    unique: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        unique[str(candidate.get("source_path"))] = candidate
    return list(unique.values()), observed_paths


def score_cache_key(source: dict[str, Any], session: str, horizon_id: str, side: str) -> tuple[str, str, str, str]:
    return (str(source.get("source_path")), session, horizon_id, side)


def source_proof_hash(path_text: str | None) -> str | None:
    if not path_text:
        return None
    path = REPO / path_text
    return sha256_file(path) if path.exists() else None


def build_seed_consumption_rows(
    market_rows: list[dict[str, Any]],
    expansion_rows: list[dict[str, Any]],
    performance_rows: list[dict[str, Any]],
    noncomputable_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    perf_by_market = Counter(row.get("input_market_population_row_id") for row in performance_rows)
    perf_by_expansion = Counter(row.get("input_expansion_matrix_row_id") for row in performance_rows)
    proof_by_expansion = Counter(row.get("input_expansion_matrix_row_id") for row in noncomputable_rows)
    rows: list[dict[str, Any]] = []
    for market in market_rows:
        market_id = market.get("market_population_row_id")
        rows.append(
            boundary_row(
                {
                    "seed_consumption_row_id": f"OHLC-GTOS-EXPANDED-MARKET-SEED-CONSUME-{len(rows) + 1:06d}",
                    "seed_kind": "market_population",
                    "input_market_population_row_id": market_id,
                    "symbol": market.get("symbol"),
                    "market_timeframe": market.get("timeframe"),
                    "source_path": market.get("source_path"),
                    "source_file_sha256": market.get("sha256"),
                    "performance_rows_generated": perf_by_market.get(market_id, 0),
                    "source_access_status": "CONSUMED_IN_PERFORMANCE_ROWS"
                    if perf_by_market.get(market_id, 0)
                    else "SOURCE_REACHABLE_BUT_NOT_REFERENCED_BY_EXPANSION_SEED",
                }
            )
        )
    for expansion in expansion_rows:
        expansion_id = expansion.get("market_timeframe_session_horizon_expansion_row_id")
        rows.append(
            boundary_row(
                {
                    "seed_consumption_row_id": f"OHLC-GTOS-EXPANDED-MARKET-SEED-CONSUME-{len(rows) + 1:06d}",
                    "seed_kind": "expansion_matrix",
                    "input_expansion_matrix_row_id": expansion_id,
                    "symbol": expansion.get("symbol"),
                    "route_session": expansion.get("route_session"),
                    "horizon_id": expansion.get("horizon_id"),
                    "source_component": expansion.get("source_component"),
                    "seed_decision": expansion.get("decision"),
                    "performance_rows_generated": perf_by_expansion.get(expansion_id, 0),
                    "source_access_proof_rows_generated": proof_by_expansion.get(expansion_id, 0),
                    "source_access_status": "CONSUMED_IN_PERFORMANCE_ROWS"
                    if perf_by_expansion.get(expansion_id, 0)
                    else "CONSUMED_AS_SOURCE_ACCESS_PROOF",
                }
            )
        )
    return rows


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_proxy_r_performance_result"),
        (PERFORMANCE_LEDGER, "expanded_market_proxy_r_performance_rows"),
        (AGGREGATE_LEDGER, "expanded_market_proxy_r_performance_aggregates"),
        (NONCOMPUTABLE_LEDGER, "expanded_market_proxy_r_source_access_proofs"),
        (SEED_CONSUMPTION_LEDGER, "expanded_market_proxy_r_seed_consumption"),
        (DISCOVERED_SOURCE_LEDGER, "expanded_market_proxy_r_discovered_sources"),
        (SYSTEM_LEDGER, "expanded_market_proxy_r_system"),
        (SUMMARY_PATH, "expanded_market_proxy_r_summary"),
        (BUILDER_MODULE, "expanded_market_proxy_r_builder"),
        (VERIFIER_MODULE, "expanded_market_proxy_r_verifier"),
        (HELPER_MODULE, "expanded_market_proxy_r_helper"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    manifest.setdefault("artifacts", []).extend(entries)
    manifest["latest_expanded_market_proxy_r_performance"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def append_sprint_event(generated_at: str, counts: dict[str, Any]) -> None:
    event = {
        "checkpoint": 216,
        "event": "expanded_market_proxy_r_performance",
        "generated_utc": generated_at,
        "input_market_population_rows": counts["input_market_population_rows"],
        "input_expansion_matrix_rows": counts["input_expansion_matrix_rows"],
        "performance_rows": counts["performance_rows"],
        "aggregate_rows": counts["aggregate_rows"],
        "source_access_proof_rows": counts["source_access_proof_rows"],
        "discovered_ohlc_source_rows": counts["discovered_ohlc_source_rows"],
        "additional_reachable_ohlc_source_rows": counts["additional_reachable_ohlc_source_rows"],
        "continuation": "continue to the next highest-value numeric plate after expanded-market performance commit.",
        "boundary": research_boundary(),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    text = f"""
## Checkpoint 216 - Expanded-Market Proxy-R Performance

Generated: {generated_at}

Trigger: owner correction after Checkpoint 215. The completed 1057-row scorer/avoid plate was closed, and the next checkpoint pivoted to broad-market numeric execution from the 301 market-population rows and the 1145-row expansion matrix.

Rows:
- market-population seed rows consumed: {counts['input_market_population_rows']}
- expansion-matrix seed rows consumed: {counts['input_expansion_matrix_rows']}
- discovered OHLC source rows: {counts['discovered_ohlc_source_rows']}
- additional reachable OHLC source rows: {counts['additional_reachable_ohlc_source_rows']}
- expanded-market performance rows: {counts['performance_rows']}
- aggregate performance rows: {counts['aggregate_rows']}
- source/access proof rows: {counts['source_access_proof_rows']}
- rows with simulated R: {counts['rows_with_simulated_r']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: continue to the next highest-value numeric plate; do not treat the 301/1145 seed universe as a stopping boundary.
"""
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Proxy-R Performance",
            "",
            "This checkpoint consumes the market-population and expansion-matrix seed rows into numeric proxy-R performance tables from reachable OHLC sources, with row-level source/access proof where geometry cannot be scored.",
            "",
            "## Counts",
            "",
            f"- Market-population seed rows: `{counts['input_market_population_rows']}`",
            f"- Expansion-matrix seed rows: `{counts['input_expansion_matrix_rows']}`",
            f"- Work-order expansion rows cross-checked: `{counts['input_work_order_expansion_matrix_rows']}`",
            f"- Discovered OHLC source rows: `{counts['discovered_ohlc_source_rows']}`",
            f"- Additional reachable OHLC source rows: `{counts['additional_reachable_ohlc_source_rows']}`",
            f"- Performance rows: `{counts['performance_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Source/access proof rows: `{counts['source_access_proof_rows']}`",
            f"- Rows with simulated R: `{counts['rows_with_simulated_r']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Continue to the next highest-value numeric plate after this checkpoint is committed.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    market_rows = read_jsonl(MARKET_POPULATION_LEDGER)
    computed_expansion_rows = read_jsonl(COMPUTED_EXPANSION_MATRIX)
    work_order_expansion_rows = read_jsonl(WORK_ORDER_EXPANSION_MATRIX)
    cost_rows = read_jsonl(COST_SYMBOL_LEDGER)

    discovered_sources = discover_ohlc_csv_sources(REPO)
    source_by_path = {str(row.get("source_path")): row for row in discovered_sources}
    market_by_path = index_market_population(market_rows)
    source_by_symbol = source_index_by_symbol(discovered_sources)
    market_source_paths = {str(row.get("source_path")) for row in market_rows}
    additional_sources = [row for row in discovered_sources if str(row.get("source_path")) not in market_source_paths]
    cost_by_symbol = {symbol_key(row.get("symbol")): row for row in cost_rows}

    ohlc_cache: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    score_cache: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    performance_rows: list[dict[str, Any]] = []
    noncomputable_rows: list[dict[str, Any]] = []

    def loaded_source(source: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        source_path = str(source.get("source_path"))
        if source_path not in ohlc_cache:
            rows, meta = load_ohlc_rows(REPO, source_path)
            source.update(meta)
            ohlc_cache[source_path] = (rows, meta)
        return ohlc_cache[source_path]

    for seed in computed_expansion_rows:
        sessions = numeric_sessions(seed.get("route_session"))
        horizons = numeric_horizons(seed.get("horizon_id"))
        candidates, observed_paths = candidate_sources_for_seed(seed, source_by_path, source_by_symbol)
        if not sessions:
            noncomputable_rows.append(
                noncomputable_row(
                    seed,
                    "EXPANSION_ROW_HAS_NO_NUMERIC_SESSION_ROUTE",
                    len(noncomputable_rows) + 1,
                    missing_fields=["numeric_route_session"],
                )
            )
            continue
        if not horizons:
            noncomputable_rows.append(
                noncomputable_row(
                    seed,
                    "EXPANSION_ROW_HAS_NO_NUMERIC_HORIZON_ROUTE",
                    len(noncomputable_rows) + 1,
                    missing_fields=["numeric_horizon_id"],
                )
            )
            continue
        if not candidates:
            proof_path = observed_paths[0] if observed_paths else None
            noncomputable_rows.append(
                noncomputable_row(
                    seed,
                    "NO_REACHABLE_OHLC_SOURCE_FOR_EXPANSION_ROW",
                    len(noncomputable_rows) + 1,
                    source_path=proof_path,
                    source_file_sha256=source_proof_hash(proof_path),
                    missing_fields=["reachable_ohlc_csv_source_path"],
                )
            )
            continue
        for source in candidates:
            rows, meta = loaded_source(source)
            source.update(meta)
            market_population_row_id = market_row_id_for_source(source, market_by_path)
            cost_proxy = cost_proxy_for_symbol(str(source.get("source_symbol") or seed.get("symbol")), cost_by_symbol)
            for session in sessions:
                for horizon_id in horizons:
                    for side in ("LONG", "SHORT"):
                        cache_key = score_cache_key(source, session, horizon_id, side)
                        if cache_key not in score_cache:
                            score_cache[cache_key] = score_source_session_horizon(
                                source,
                                rows,
                                session,
                                horizon_id,
                                side,
                                cost_proxy,
                            )
                        score = score_cache[cache_key]
                        if score.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED":
                            performance_rows.append(
                                performance_row_from_score(
                                    seed,
                                    source,
                                    session,
                                    horizon_id,
                                    side,
                                    score,
                                    len(performance_rows) + 1,
                                    market_population_row_id,
                                )
                            )
                        else:
                            noncomputable_rows.append(
                                noncomputable_row(
                                    seed,
                                    str(score.get("score_status") or "SOURCE_SESSION_HORIZON_NOT_SCOREABLE"),
                                    len(noncomputable_rows) + 1,
                                    source_path=str(source.get("source_path")),
                                    source_file_sha256=str(source.get("source_file_sha256") or ""),
                                    market_population_row_id=market_population_row_id,
                                    missing_fields=["eligible_forward_path_rows"],
                                )
                            )

    for source in additional_sources:
        rows, meta = loaded_source(source)
        source.update(meta)
        seed = {
            "market_timeframe_session_horizon_expansion_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-DISCOVERED-SOURCE-{len(performance_rows) + 1:06d}"
            ),
            "symbol": source.get("source_symbol"),
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "source_component": "discovered_ohlc_source",
            "decision": "score-discovered-source",
        }
        cost_proxy = cost_proxy_for_symbol(str(source.get("source_symbol")), cost_by_symbol)
        for side in ("LONG", "SHORT"):
            cache_key = score_cache_key(source, "ALL_SESSIONS", "h16", side)
            if cache_key not in score_cache:
                score_cache[cache_key] = score_source_session_horizon(
                    source,
                    rows,
                    "ALL_SESSIONS",
                    "h16",
                    side,
                    cost_proxy,
                )
            score = score_cache[cache_key]
            if score.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED":
                performance_rows.append(
                    performance_row_from_score(
                        seed,
                        source,
                        "ALL_SESSIONS",
                        "h16",
                        side,
                        score,
                        len(performance_rows) + 1,
                        None,
                    )
                )

    scored_source_paths = {str(row.get("source_path")) for row in performance_rows}
    market_population_fallback_sources = [
        source
        for source in discovered_sources
        if str(source.get("source_path")) in market_source_paths and str(source.get("source_path")) not in scored_source_paths
    ]
    for source in market_population_fallback_sources:
        rows, meta = loaded_source(source)
        source.update(meta)
        market_population_row_id = market_row_id_for_source(source, market_by_path)
        seed = {
            "market_timeframe_session_horizon_expansion_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-MARKET-POP-FALLBACK-{len(performance_rows) + 1:06d}"
            ),
            "symbol": source.get("source_symbol"),
            "route_session": "ALL_SESSIONS",
            "horizon_id": "h16",
            "source_component": "market_population_fallback",
            "decision": "score-market-population-source",
        }
        cost_proxy = cost_proxy_for_symbol(str(source.get("source_symbol")), cost_by_symbol)
        for side in ("LONG", "SHORT"):
            cache_key = score_cache_key(source, "ALL_SESSIONS", "h16", side)
            if cache_key not in score_cache:
                score_cache[cache_key] = score_source_session_horizon(
                    source,
                    rows,
                    "ALL_SESSIONS",
                    "h16",
                    side,
                    cost_proxy,
                )
            score = score_cache[cache_key]
            if score.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED":
                performance_rows.append(
                    performance_row_from_score(
                        seed,
                        source,
                        "ALL_SESSIONS",
                        "h16",
                        side,
                        score,
                        len(performance_rows) + 1,
                        market_population_row_id,
                    )
                )
            else:
                noncomputable_rows.append(
                    noncomputable_row(
                        seed,
                        str(score.get("score_status") or "MARKET_POPULATION_FALLBACK_NOT_SCOREABLE"),
                        len(noncomputable_rows) + 1,
                        source_path=str(source.get("source_path")),
                        source_file_sha256=str(source.get("source_file_sha256") or ""),
                        market_population_row_id=market_population_row_id,
                        missing_fields=["eligible_market_population_forward_path_rows"],
                    )
                )

    aggregate_rows = aggregate_performance_rows(performance_rows)
    seed_consumption_rows = build_seed_consumption_rows(
        market_rows,
        computed_expansion_rows,
        performance_rows,
        noncomputable_rows,
    )
    discovered_source_rows = [
        boundary_row(
            {
                "discovered_ohlc_source_row_id": f"OHLC-GTOS-EXPANDED-MARKET-OHLC-SOURCE-{index:05d}",
                **source,
                "input_market_population_row_id": market_row_id_for_source(source, market_by_path),
                "discovery_scope": "data_csv_ohlc_discovery",
            }
        )
        for index, source in enumerate(discovered_sources, start=1)
    ]
    system_rows = [
        system_row(
            performance_rows,
            aggregate_rows,
            noncomputable_rows,
            seed_consumption_rows,
            discovered_source_rows,
        )
    ]

    output_files = [
        PERFORMANCE_LEDGER,
        AGGREGATE_LEDGER,
        NONCOMPUTABLE_LEDGER,
        SEED_CONSUMPTION_LEDGER,
        DISCOVERED_SOURCE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    counts = {
        "input_market_population_rows": len(market_rows),
        "input_expansion_matrix_rows": len(computed_expansion_rows),
        "input_work_order_expansion_matrix_rows": len(work_order_expansion_rows),
        "discovered_ohlc_source_rows": len(discovered_sources),
        "additional_reachable_ohlc_source_rows": len(additional_sources),
        "market_population_fallback_source_rows": len(market_population_fallback_sources),
        "performance_rows": len(performance_rows),
        "aggregate_rows": len(aggregate_rows),
        "source_access_proof_rows": len(noncomputable_rows),
        "seed_consumption_rows": len(seed_consumption_rows),
        "system_rows": len(system_rows),
        "rows_with_simulated_r": sum(row.get("cost_adjusted_simulated_r") is not None for row in performance_rows),
        "rows_without_simulated_r": sum(row.get("cost_adjusted_simulated_r") is None for row in performance_rows),
        "source_path_count": len({row.get("source_path") for row in performance_rows}),
        "symbol_count": len({row.get("symbol") for row in performance_rows}),
        "expansion_rows_consumed_in_performance": len(
            {row.get("input_expansion_matrix_row_id") for row in performance_rows}
        ),
        "expansion_rows_consumed_as_source_access_proof": len(
            {row.get("input_expansion_matrix_row_id") for row in noncomputable_rows}
        ),
        "decision_counts": dict(
            sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in performance_rows).items())
        ),
    }

    write_jsonl(PERFORMANCE_LEDGER, performance_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(NONCOMPUTABLE_LEDGER, noncomputable_rows)
    write_jsonl(SEED_CONSUMPTION_LEDGER, seed_consumption_rows)
    write_jsonl(DISCOVERED_SOURCE_LEDGER, discovered_source_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "market_population_ledger": str(MARKET_POPULATION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "computed_expansion_matrix": str(COMPUTED_EXPANSION_MATRIX.relative_to(REPO)).replace("\\", "/"),
            "work_order_expansion_matrix": str(WORK_ORDER_EXPANSION_MATRIX.relative_to(REPO)).replace("\\", "/"),
            "cost_symbol_ledger": str(COST_SYMBOL_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "performance_ledger": str(PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_access_proof_ledger": str(NONCOMPUTABLE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "seed_consumption_ledger": str(SEED_CONSUMPTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "discovered_source_ledger": str(DISCOVERED_SOURCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_proxy_r_performance_surface": EXPANDED_MARKET_PROXY_R_PERFORMANCE_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    append_sprint_event(generated_at, counts)
    append_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
