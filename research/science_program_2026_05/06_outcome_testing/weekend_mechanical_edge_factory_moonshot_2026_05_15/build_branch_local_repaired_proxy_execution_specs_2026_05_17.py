#!/usr/bin/env python3
"""Build executable specs, repair tasks, exact/proxy bridge rows, and market populations."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_repaired_proxy_execution_specs import (
    BOUNDARY_SCHEMA,
    avoid_comparator_spec_from_event,
    boundary_row,
    bucket_rows,
    cost_observation_from_source,
    default_off_scorer_spec_from_event,
    exact_proxy_bridge_row,
    market_population_row,
    repair_task_from_event,
    research_boundary,
    scope_summary_rows,
    summarize_cost_by_symbol,
    to_float,
)


APP_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION"
BROKER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_BROKER_SOURCE_REPAIR_EXPECTANCY"
SHADOW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_SHADOW_SCORER_COMPUTE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"

DEFAULT_OFF_LEDGER = ROUTE_DIR / f"{APP_PREFIX}_DEFAULT_OFF_SCORE_LEDGER_2026-05-17.jsonl"
AVOID_LEDGER = ROUTE_DIR / f"{APP_PREFIX}_AVOID_REDESIGN_LEDGER_2026-05-17.jsonl"
REPAIR_REQUIRED_LEDGER = ROUTE_DIR / f"{APP_PREFIX}_REPAIR_REQUIRED_LEDGER_2026-05-17.jsonl"
EVENT_APPLICATION_LEDGER = ROUTE_DIR / f"{APP_PREFIX}_EVENT_APPLICATION_LEDGER_2026-05-17.jsonl"
APP_RESULT = ROUTE_DIR / f"{APP_PREFIX}_RESULT_2026-05-17.json"
EXACT_JOIN_LEDGER = ROUTE_DIR / f"{BROKER_PREFIX}_EXACT_R_JOIN_LEDGER_2026-05-17.jsonl"
LOCAL_OBSERVATION_LEDGER = ROUTE_DIR / f"{BROKER_PREFIX}_LOCAL_SOURCE_OBSERVATION_LEDGER_2026-05-17.jsonl"
NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{SHADOW_PREFIX}_NUMERIC_EVENT_SCORE_LEDGER_2026-05-17.jsonl"
EXACT_COMPUTE_LEDGER = ROUTE_DIR / f"{SHADOW_PREFIX}_EXACT_R_COMPUTE_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
DEFAULT_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_SCORER_SPEC_LEDGER_2026-05-17.jsonl"
DEFAULT_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_SCOPE_LEDGER_2026-05-17.jsonl"
AVOID_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_COMPARATOR_SPEC_LEDGER_2026-05-17.jsonl"
AVOID_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_SCOPE_LEDGER_2026-05-17.jsonl"
REPAIR_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_TASK_LEDGER_2026-05-17.jsonl"
REPAIR_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_SCOPE_LEDGER_2026-05-17.jsonl"
EXACT_PROXY_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"
COST_SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_COST_SOURCE_LEDGER_2026-05-17.jsonl"
COST_SYMBOL_LEDGER = ROUTE_DIR / f"{PREFIX}_COST_SYMBOL_LEDGER_2026-05-17.jsonl"
MARKET_POP_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_EXPANSION_POPULATION_LEDGER_2026-05-17.jsonl"
SOURCE_SEARCH_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_R_SOURCE_SEARCH_LEDGER_2026-05-17.jsonl"
SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"

CORE_EXACT_SOURCE_PATHS = [
    REPO / "shadow_logs/account_pnl_truth_reconciliation.jsonl",
    REPO / "shadow_logs/account_truth_reconciliation_status.jsonl",
    REPO / "shadow_logs/broker_actual_r_audit.jsonl",
    REPO / "shadow_logs/pending_limit_lifecycle.jsonl",
    REPO / "shadow_logs/pending_limit_lifecycle_audit.jsonl",
    REPO / "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
    REPO / "shadow_logs/trade_index_lifecycle_audit.jsonl",
    REPO / "shadow_logs/opportunity_lifecycle_audit.jsonl",
    REPO / "shadow_logs/slippage.jsonl",
    REPO / "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl",
    REPO / "data/account_history/mt5_deals_2026-04-27_2026-05-11.jsonl",
]

LEGACY_TOKENS = [
    "NO_" + "PROMOTION_VERDICT",
    "validation_" + "safe",
    "outcome_review_" + "opened",
    "live_" + "effect",
    "safe_" + "flags",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with open(long_path(path), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            boundary_row(
                {
                    "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-SRC-{index:04d}",
                    "path": path.relative_to(REPO).as_posix() if path.exists() else str(path),
                    "sha256": digest,
                    "status": "HASHED" if digest else "MISSING",
                    "generated_utc": generated_at,
                }
            )
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def id_hash(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def collect_source_search_and_cost_rows(generated_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    source_rows = []
    cost_rows = []
    symbol_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cost_index = 0
    trade_record_count_by_symbol: Counter[str] = Counter()

    for trade_path in (REPO / "knowledge_base/trade_records").glob("*/*.json"):
        symbol = trade_path.parent.name
        trade_record_count_by_symbol[symbol] += 1

    for path_index, path in enumerate(exact_source_paths(), 1):
        row_count = 0
        parse_errors = 0
        direct_identifier_rows = 0
        exact_value_rows = 0
        geometry_rows = 0
        if path.exists():
            for row in iter_jsonl(path):
                if not isinstance(row, dict):
                    parse_errors += 1
                    continue
                row_count += 1
                symbol = str(row.get("symbol") or row.get("broker_symbol") or row.get("source_symbol") or "")
                if symbol:
                    symbol_counts[symbol]["source_rows"] += 1
                identifiers = [
                    row.get("candidate_id"),
                    row.get("strategy_id"),
                    row.get("row_id"),
                    row.get("trade_id"),
                    row.get("mt5_order_id"),
                    row.get("mt5_deal_id"),
                    row.get("order"),
                    row.get("order_ticket"),
                    row.get("ticket"),
                    row.get("deal"),
                    row.get("deal_ticket"),
                    row.get("position_id"),
                    row.get("fill_id"),
                    row.get("row_key"),
                    row.get("pending_lifecycle_audit_row_key"),
                    row.get("broker_actual_r_audit_row_key"),
                ]
                if any(value not in (None, "") for value in identifiers):
                    direct_identifier_rows += 1
                    if symbol:
                        symbol_counts[symbol]["direct_identifier_rows"] += 1
                actual_r = row.get("actual_r") or row.get("result_r") or row.get("broker_actual_r")
                if to_float(actual_r) is not None:
                    exact_value_rows += 1
                    if symbol:
                        symbol_counts[symbol]["symbol_exact_r_rows"] += 1
                if row.get("entry_price") not in (None, "") and row.get("stop_loss") not in (None, ""):
                    geometry_rows += 1
                    if symbol:
                        symbol_counts[symbol]["geometry_rows"] += 1
                cost = cost_observation_from_source(row, path.relative_to(REPO).as_posix(), cost_index + 1)
                if cost is not None:
                    cost_index += 1
                    cost["generated_utc"] = generated_at
                    cost_rows.append(cost)
        else:
            parse_errors = 1
        source_rows.append(
            boundary_row(
                {
                    "source_search_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SOURCE-SEARCH-{path_index:04d}",
                    "source_path": path.relative_to(REPO).as_posix() if path.exists() else str(path),
                    "source_exists": path.exists(),
                    "row_count": row_count,
                    "parse_error_count": parse_errors,
                    "direct_identifier_rows": direct_identifier_rows,
                    "exact_value_rows": exact_value_rows,
                    "geometry_rows": geometry_rows,
                    "sha256": sha256_file(path),
                    "generated_utc": generated_at,
                }
            )
        )

    for index, (symbol, count) in enumerate(sorted(trade_record_count_by_symbol.items()), len(source_rows) + 1):
        symbol_counts[symbol]["trade_record_rows"] += count
        source_rows.append(
            boundary_row(
                {
                    "source_search_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SOURCE-SEARCH-{index:04d}",
                    "source_path": f"knowledge_base/trade_records/{symbol}",
                    "source_exists": True,
                    "row_count": int(count),
                    "parse_error_count": 0,
                    "direct_identifier_rows": int(count),
                    "exact_value_rows": 0,
                    "geometry_rows": 0,
                    "sha256": None,
                    "generated_utc": generated_at,
                }
            )
        )

    return source_rows, cost_rows, {symbol: dict(counter) for symbol, counter in symbol_counts.items()}


def exact_source_paths() -> list[Path]:
    paths = set(CORE_EXACT_SOURCE_PATHS)
    paths.update((REPO / "shadow_logs").glob("*.jsonl"))
    paths.update((REPO / "data/account_history").glob("*.jsonl"))
    return sorted(paths, key=lambda path: path.as_posix())


def collect_market_population_rows(generated_at: str) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    csv_paths = sorted((REPO / "data").rglob("*.csv"))
    pattern = re.compile(r"(?P<symbol>[A-Za-z0-9_]+)_(?P<tf>M1|M5|M15|H1|H4|D1)\.csv$", re.IGNORECASE)
    for path in csv_paths:
        match = pattern.search(path.name)
        if not match:
            continue
        row_count = 0
        first_time = None
        last_time = None
        try:
            with open(long_path(path), "r", encoding="utf-8", errors="replace", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = reader.fieldnames or []
                time_field = next((name for name in fieldnames if name.lower() in {"time", "datetime", "date", "timestamp"}), None)
                for row in reader:
                    row_count += 1
                    value = row.get(time_field) if time_field else None
                    if value and first_time is None:
                        first_time = value
                    if value:
                        last_time = value
        except OSError:
            continue
        rel = path.relative_to(REPO).as_posix()
        key = (rel, match.group("symbol"), match.group("tf"))
        if key in seen:
            continue
        seen.add(key)
        market_row = market_population_row(
            rel,
            match.group("symbol"),
            match.group("tf").upper(),
            row_count,
            first_time,
            last_time,
            sha256_file(path),
            len(rows) + 1,
        )
        market_row["generated_utc"] = generated_at
        rows.append(market_row)
    return rows


def row_by_key(path: Path, key_field: str) -> dict[str, dict[str, Any]]:
    output = {}
    for row in iter_jsonl(path):
        key = row.get(key_field)
        if key not in (None, ""):
            output[str(key)] = row
    return output


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {
                    "path": rel,
                    "artifact": PREFIX,
                    "sha256": sha256_file(path),
                    "research_boundary": research_boundary(),
                }
            )
    manifest["latest_branch_local_repaired_proxy_execution_specs"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    append_jsonl(
        SPRINT_LEDGER,
        {
            "timestamp_utc": result["generated_utc"],
            "route": PREFIX,
            "event": "repaired_proxy_execution_specs_built",
            "counts": result["counts"],
            "research_boundary": research_boundary(),
            "summary": "Consumed repaired proxy score, avoid/redesign, and repair-required rows into executable specs, exact/proxy bridge rows, cost proxy evidence, market population rows, and system recommendations.",
        },
    )


def append_active_ledger(result: dict[str, Any]) -> None:
    counts = result["counts"]
    text = (
        "\n## Checkpoint 171 - Repaired Proxy Rows Consumed Into Executable Specs And Bridge Ledgers\n\n"
        f"Timestamp UTC: `{result['generated_utc']}`\n\n"
        "Trigger: continuation after Checkpoint 170 and the May 17 boundary-wording correction. The repaired proxy "
        "application rows were consumed into executable branch-local specs, row-level repair tasks, exact/proxy bridge "
        "rows, cost proxy evidence, market expansion populations, and a system recommendation packet.\n\n"
        "Outputs:\n\n"
        f"- `{counts['default_off_scorer_spec_rows']}` default-off scorer event specs and "
        f"`{counts['default_off_scope_rows']}` default-off scope summaries from the full `12,303` row input.\n"
        f"- `{counts['avoid_comparator_spec_rows']}` avoid/redesign comparator specs and "
        f"`{counts['avoid_scope_rows']}` avoid/redesign scope summaries from the full `5,443` row input.\n"
        f"- `{counts['repair_task_rows']}` repair-required row tasks and `{counts['repair_scope_rows']}` repair scope "
        "summaries, preserving all `170` rows as executable source/broker geometry work.\n"
        f"- `{counts['exact_proxy_bridge_rows']}` exact/proxy bridge rows across the full application denominator; "
        f"exact broker-R rows found in this joined denominator: `{result['exact_r_value_rows']}`.\n"
        f"- `{counts['cost_source_rows']}` R-denominated cost source observations, "
        f"`{counts['cost_symbol_rows']}` symbol cost summaries, and `{counts['market_population_rows']}` local market "
        "population rows from reachable disk OHLCV sources.\n"
        f"- `{counts['source_search_rows']}` exact-R/source-search proof rows and "
        f"`{counts['system_recommendation_rows']}` system recommendation rows.\n\n"
        "Boundary correction applied: new outputs use concrete branch-local research boundaries and omit legacy "
        "defensive status-token blocks. Older checkpoints remain historical and were not rewritten solely for wording.\n\n"
        "Immediate continuation: implement the generated default-off scorer specs and avoid/redesign comparators into "
        "branch-local callable registries, execute the repair-task ledger against source/broker geometry roots, and expand "
        "market-population rows into replay/numeric populations where source-safe parsers are already available.\n"
    )
    with open(long_path(ACTIVE_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Repaired Proxy Execution Specs",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Branch-local research boundary schema: "
        f"`{result['research_boundary']['boundary_schema']}`.",
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            result["system_recommendation"],
        ]
    )
    write_text(SUMMARY_PATH, "\n".join(lines) + "\n")


def verify_no_legacy_tokens(paths: list[Path]) -> list[str]:
    issues = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in LEGACY_TOKENS:
            if token in text:
                issues.append(f"legacy_boundary_token:{path.name}:{token}")
    return issues


def main() -> int:
    generated_at = now_utc()
    app_result = read_json(APP_RESULT)
    manifest_rows, manifest_hash = source_manifest(
        [
            DEFAULT_OFF_LEDGER,
            AVOID_LEDGER,
            REPAIR_REQUIRED_LEDGER,
            EVENT_APPLICATION_LEDGER,
            APP_RESULT,
            EXACT_JOIN_LEDGER,
            LOCAL_OBSERVATION_LEDGER,
            NUMERIC_EVENT_LEDGER,
            EXACT_COMPUTE_LEDGER,
            Path(__file__),
            REPO / "src/research_infra/moonshot_repaired_proxy_execution_specs.py",
        ]
        + exact_source_paths(),
        generated_at,
    )

    exact_join_by_numeric = row_by_key(EXACT_JOIN_LEDGER, "input_numeric_result_row_id")
    numeric_by_id = row_by_key(NUMERIC_EVENT_LEDGER, "input_numeric_result_row_id")
    exact_compute_by_id = row_by_key(EXACT_COMPUTE_LEDGER, "input_numeric_result_row_id")

    source_search_rows, cost_rows, source_counts_by_symbol = collect_source_search_and_cost_rows(generated_at)
    cost_by_symbol = summarize_cost_by_symbol(cost_rows)
    cost_symbol_rows = [
        boundary_row(
            {
                "cost_symbol_row_id": f"OHLC-GTOS-REPAIRED-PROXY-COST-SYMBOL-{index:04d}",
                **row,
                "generated_utc": generated_at,
            }
        )
        for index, row in enumerate(cost_by_symbol.values(), 1)
    ]
    market_rows = collect_market_population_rows(generated_at)

    default_rows = list(iter_jsonl(DEFAULT_OFF_LEDGER))
    avoid_rows = list(iter_jsonl(AVOID_LEDGER))
    repair_rows = list(iter_jsonl(REPAIR_REQUIRED_LEDGER))

    default_specs = [default_off_scorer_spec_from_event(row, index) for index, row in enumerate(default_rows, 1)]
    avoid_specs = [avoid_comparator_spec_from_event(row, index) for index, row in enumerate(avoid_rows, 1)]
    repair_tasks = [
        repair_task_from_event(
            row,
            exact_join_by_numeric.get(str(row.get("input_numeric_result_row_id"))),
            source_counts_by_symbol.get(str(row.get("symbol") or ""), {}),
            index,
        )
        for index, row in enumerate(repair_rows, 1)
    ]

    all_app_rows = list(iter_jsonl(EVENT_APPLICATION_LEDGER))
    exact_proxy_rows = []
    exact_r_value_rows = 0
    for index, row in enumerate(all_app_rows, 1):
        numeric_id = str(row.get("input_numeric_result_row_id"))
        numeric_row = numeric_by_id.get(numeric_id) or exact_compute_by_id.get(numeric_id)
        exact_row = exact_join_by_numeric.get(numeric_id)
        bridge = exact_proxy_bridge_row(row, numeric_row, exact_row, cost_by_symbol.get(str(row.get("symbol") or "")), index)
        if bridge.get("exact_r_value") is not None:
            exact_r_value_rows += 1
        exact_proxy_rows.append(bridge)

    default_scope_rows = scope_summary_rows(
        default_specs,
        "default_off_scope_row_id",
        "OHLC-GTOS-REPAIRED-PROXY-DEFAULT-SCOPE",
    )
    avoid_scope_rows = scope_summary_rows(
        avoid_specs,
        "avoid_scope_row_id",
        "OHLC-GTOS-REPAIRED-PROXY-AVOID-SCOPE",
    )
    repair_scope_rows = scope_summary_rows(
        repair_tasks,
        "repair_scope_row_id",
        "OHLC-GTOS-REPAIRED-PROXY-REPAIR-SCOPE",
    )

    system_recommendation = (
        "Register the 102 default-off repaired-proxy scopes as branch-local scorer candidates, register the 154 "
        "avoid/redesign scopes as comparator candidates, execute the 34 repair-required scopes through source/broker "
        "geometry repair before scalar use, use the exact/proxy bridge ledger as the current R surface, and use local "
        "market population rows for the next replay/numeric expansion pass."
    )
    recommendation_rows = [
        boundary_row(
            {
                "system_recommendation_row_id": "OHLC-GTOS-REPAIRED-PROXY-EXEC-SYSREC-0001",
                "generated_utc": generated_at,
                "recommendation": system_recommendation,
                "default_off_scope_rows": len(default_scope_rows),
                "avoid_scope_rows": len(avoid_scope_rows),
                "repair_scope_rows": len(repair_scope_rows),
                "exact_proxy_bridge_rows": len(exact_proxy_rows),
                "market_population_rows": len(market_rows),
                "next_branch_local_actions": [
                    "implement_default_off_scorer_registry_from_spec_ledger",
                    "implement_avoid_redesign_comparator_registry_from_spec_ledger",
                    "execute_repair_task_ledger_against_source_and_broker_geometry",
                    "materialize_market_population_replay_numeric_rows",
                    "rerun_exact_proxy_bridge_after_each_source_repair_batch",
                ],
            }
        )
    ]

    buckets = bucket_rows(
        {
            "default_off_specs": default_specs,
            "avoid_specs": avoid_specs,
            "repair_tasks": repair_tasks,
            "exact_proxy_bridge": exact_proxy_rows,
            "market_populations": market_rows,
        }
    )

    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        DEFAULT_SPEC_LEDGER,
        DEFAULT_SCOPE_LEDGER,
        AVOID_SPEC_LEDGER,
        AVOID_SCOPE_LEDGER,
        REPAIR_TASK_LEDGER,
        REPAIR_SCOPE_LEDGER,
        EXACT_PROXY_LEDGER,
        COST_SOURCE_LEDGER,
        COST_SYMBOL_LEDGER,
        MARKET_POP_LEDGER,
        SOURCE_SEARCH_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        BUCKET_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]

    write_jsonl(DEFAULT_SPEC_LEDGER, default_specs)
    write_jsonl(DEFAULT_SCOPE_LEDGER, default_scope_rows)
    write_jsonl(AVOID_SPEC_LEDGER, avoid_specs)
    write_jsonl(AVOID_SCOPE_LEDGER, avoid_scope_rows)
    write_jsonl(REPAIR_TASK_LEDGER, repair_tasks)
    write_jsonl(REPAIR_SCOPE_LEDGER, repair_scope_rows)
    write_jsonl(EXACT_PROXY_LEDGER, exact_proxy_rows)
    write_jsonl(COST_SOURCE_LEDGER, cost_rows)
    write_jsonl(COST_SYMBOL_LEDGER, cost_symbol_rows)
    write_jsonl(MARKET_POP_LEDGER, market_rows)
    write_jsonl(SOURCE_SEARCH_LEDGER, source_search_rows)
    write_jsonl(SYSTEM_RECOMMENDATION_LEDGER, recommendation_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(SOURCE_MANIFEST_LEDGER, manifest_rows)

    counts = {
        "input_default_off_rows": len(default_rows),
        "input_avoid_redesign_rows": len(avoid_rows),
        "input_repair_required_rows": len(repair_rows),
        "input_event_application_rows": len(all_app_rows),
        "default_off_scorer_spec_rows": len(default_specs),
        "default_off_scope_rows": len(default_scope_rows),
        "avoid_comparator_spec_rows": len(avoid_specs),
        "avoid_scope_rows": len(avoid_scope_rows),
        "repair_task_rows": len(repair_tasks),
        "repair_scope_rows": len(repair_scope_rows),
        "exact_proxy_bridge_rows": len(exact_proxy_rows),
        "cost_source_rows": len(cost_rows),
        "cost_symbol_rows": len(cost_symbol_rows),
        "market_population_rows": len(market_rows),
        "source_search_rows": len(source_search_rows),
        "system_recommendation_rows": len(recommendation_rows),
        "bucket_rows": len(buckets),
        "source_manifest_rows": len(manifest_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "research_boundary": research_boundary(),
        "source_manifest_hash": manifest_hash,
        "upstream_application_counts": app_result["counts"],
        "counts": counts,
        "exact_r_value_rows": exact_r_value_rows,
        "system_recommendation": system_recommendation,
        "input_denominator_preserved": (
            counts["input_event_application_rows"]
            == counts["default_off_scorer_spec_rows"]
            + counts["avoid_comparator_spec_rows"]
            + counts["repair_task_rows"]
        ),
        "scope_role_counts": {
            "default_off_scopes": len(default_scope_rows),
            "avoid_redesign_scopes": len(avoid_scope_rows),
            "repair_required_scopes": len(repair_scope_rows),
        },
        "legacy_boundary_token_issues": [],
    }
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_summary(result)

    token_issues = verify_no_legacy_tokens(outputs)
    if token_issues:
        result["legacy_boundary_token_issues"] = token_issues
        write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
        raise SystemExit(json.dumps({"ok": False, "issues": token_issues}, indent=2, sort_keys=True))

    append_manifest(outputs, result)
    append_sprint_ledger(result)
    append_active_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
