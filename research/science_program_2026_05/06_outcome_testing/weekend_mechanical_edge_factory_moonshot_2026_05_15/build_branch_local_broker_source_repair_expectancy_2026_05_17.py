#!/usr/bin/env python3
"""Run broker/source repair and expectancy computation over numeric rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_broker_source_repair import (
    BROKER_SOURCE_REPAIR_SURFACE,
    build_source_index,
    expectation_summary_row,
    implementation_decision_row,
    repair_result_row,
    source_observation,
    stable_hash,
)


SHADOW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_SHADOW_SCORER_COMPUTE"
NUMERIC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES"
BRANCH_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS"
ACCEPTED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_BROKER_SOURCE_REPAIR_EXPECTANCY"

NUMERIC_RESULT = ROUTE_DIR / f"{NUMERIC_PREFIX}_RESULT_2026-05-17.json"
NUMERIC_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl"
EVENT_SCORE_LEDGER = ROUTE_DIR / f"{SHADOW_PREFIX}_NUMERIC_EVENT_SCORE_LEDGER_2026-05-17.jsonl"
REPAIR_QUEUE_LEDGER = ROUTE_DIR / f"{SHADOW_PREFIX}_SOURCE_REPAIR_QUEUE_LEDGER_2026-05-17.jsonl"
SCOPE_SCORE_LEDGER = ROUTE_DIR / f"{SHADOW_PREFIX}_SCOPE_SCORE_DECISION_LEDGER_2026-05-17.jsonl"
SHADOW_RESULT = ROUTE_DIR / f"{SHADOW_PREFIX}_RESULT_2026-05-17.json"
BRANCH_QUEUE_LEDGER = ROUTE_DIR / f"{BRANCH_PREFIX}_BRANCH_QUEUE_2026-05-16.jsonl"
ACCEPTED_BRANCH_LEDGER = ROUTE_DIR / f"{ACCEPTED_PREFIX}_BRANCH_LEDGER_2026-05-16.jsonl"

BROKER_LOG_PATHS = [
    REPO / "shadow_logs/broker_actual_r_audit.jsonl",
    REPO / "shadow_logs/account_pnl_truth_reconciliation.jsonl",
    REPO / "shadow_logs/pending_limit_lifecycle.jsonl",
    REPO / "shadow_logs/trade_index_lifecycle_audit.jsonl",
]
TRADE_RECORD_ROOT = REPO / "knowledge_base/trade_records"

HELPER_MODULE = REPO / "src/research_infra/moonshot_broker_source_repair.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTABLE_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_EXECUTABLE_SPEC_2026-05-17.json"
SOURCE_OBSERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_LOCAL_SOURCE_OBSERVATION_LEDGER_2026-05-17.jsonl"
REPAIR_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_RESULT_LEDGER_2026-05-17.jsonl"
EXACT_R_JOIN_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_R_JOIN_LEDGER_2026-05-17.jsonl"
EXPECTANCY_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_EXPECTANCY_SUMMARY_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_DECISION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local broker/source repair and expectancy computation. This artifact consumes the numeric shadow scorer "
    "repair queue, rejoins numeric and matched-branch source rows, inventories local broker/account/lifecycle/trade "
    "sources, attempts direct exact-R joins, computes repaired proxy/expectancy summaries, and emits hard research-only "
    "implementation decisions. It does not place orders or change live behavior."
)
IDENTIFIER_FIELD_ALIASES = {
    "trade_id": "source_identifier_a",
    "trade_record_trade_id": "source_identifier_b",
    "candidate_id": "source_identifier_c",
    "fill_id": "source_identifier_d",
    "ticket": "source_identifier_e",
    "pending_ticket": "source_identifier_f",
    "trade_state_ticket": "source_identifier_g",
    "mt5_deal_id": "source_identifier_h",
    "mt5_order_id": "source_identifier_i",
    "limit_intent_trade_id": "source_identifier_j",
    "source_links.mt5_export_deal_id": "source_identifier_k",
    "source_links.mt5_export_order_id": "source_identifier_l",
    "source_links.broker_actual_r_audit_row_key": "source_identifier_m",
}
FORBIDDEN_OUTPUT_IDENTIFIER_KEYS = {
    "ticket",
    "pending_ticket",
    "trade_state_ticket",
    "mt5_deal_id",
    "mt5_order_id",
    "direct_identifiers",
    "direct_repair_identifiers",
}


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


def alias_identifier_field(field: str) -> str:
    return IDENTIFIER_FIELD_ALIASES.get(field, f"source_identifier_x_{stable_hash(field)[:10]}")


def hashed_identifier_map(raw: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    fields: list[str] = []
    hashes: dict[str, str] = {}
    for field, value in sorted(raw.items()):
        alias = alias_identifier_field(str(field))
        fields.append(alias)
        hashes[alias] = stable_hash(str(value))
    return fields, hashes


def public_output_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    if isinstance(output.get("direct_identifiers"), dict):
        fields, hashes = hashed_identifier_map(output["direct_identifiers"])
        output["direct_identifier_field_aliases"] = fields
        output["direct_identifier_hashes"] = hashes
    if isinstance(output.get("direct_repair_identifiers"), dict):
        fields, hashes = hashed_identifier_map(output["direct_repair_identifiers"])
        output["direct_repair_identifier_field_aliases"] = fields
        output["direct_repair_identifier_hashes"] = hashes
    for key in FORBIDDEN_OUTPUT_IDENTIFIER_KEYS:
        output.pop(key, None)
    return output


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        rel = path.relative_to(REPO).as_posix() if path.is_absolute() and path.exists() else str(path)
        if rel in seen:
            continue
        seen.add(rel)
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-BROKER-SOURCE-REPAIR-SRC-{len(rows) + 1:04d}",
                "path": rel,
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "generated_utc": generated_at,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def find_first(obj: Any, keys: set[str]) -> Any:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and value not in (None, "", [], {}):
                return value
        for value in obj.values():
            found = find_first(value, keys)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first(item, keys)
            if found not in (None, "", [], {}):
                return found
    return None


def trade_record_flat_row(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": path.parent.name,
        "trade_record_trade_id": find_first(row, {"trade_id"}) or f"{path.parent.name}_{path.stem}",
        "candidate_id": find_first(row, {"candidate_id"}),
        "decision_time_utc": find_first(row, {"decision_time_utc", "timestamp_utc", "timestamp"}),
        "session": find_first(row, {"session", "kill_zone"}),
        "entry_price": find_first(row, {"entry_price"}),
        "stop_loss": find_first(row, {"stop_loss", "sl"}),
        "take_profit_1": find_first(row, {"take_profit_1", "tp1", "take_profit"}),
        "actual_r": find_first(row, {"actual_r", "result_r"}),
        "final_outcome": find_first(row, {"final_outcome", "outcome"}),
        "schema_version": "knowledge_base_trade_record_json",
        "source_path": path.relative_to(REPO).as_posix(),
        "source_raw_hash": stable_hash(row),
    }


def load_local_source_observations() -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for source_path in BROKER_LOG_PATHS:
        if not source_path.exists():
            continue
        for row in read_jsonl(source_path):
            observations.append(
                source_observation(
                    source_path.name,
                    row,
                    len(observations) + 1,
                    source_path.relative_to(REPO).as_posix(),
                )
            )
    for path in sorted(TRADE_RECORD_ROOT.rglob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            raw = read_json(path)
        except json.JSONDecodeError:
            continue
        flat = trade_record_flat_row(path, raw)
        observations.append(
            source_observation(
                "knowledge_base_trade_record",
                flat,
                len(observations) + 1,
                path.relative_to(REPO).as_posix(),
            )
        )
    return observations


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {value: int(counter[value]) for value in sorted(counter)}


def exact_join_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "broker_source_exact_r_join_row_id": f"OHLC-GTOS-BROKER-SOURCE-EXACT-R-JOIN-{index:06d}",
        "input_source_repair_queue_row_id": row.get("input_source_repair_queue_row_id"),
        "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "matched_branch_queue_id": row.get("matched_branch_queue_id"),
        "exact_broker_join_status": row.get("exact_broker_join_status"),
        "exact_broker_r_value": row.get("exact_broker_r_value"),
        "exact_broker_join_source_row_id": row.get("exact_broker_join_source_row_id"),
        "direct_repair_identifier_count": row.get("direct_repair_identifier_count"),
        "direct_identifier_match_count": row.get("direct_identifier_match_count"),
        "direct_exact_r_match_count": row.get("direct_exact_r_match_count"),
        "exact_missing_field_proof": row.get("exact_missing_field_proof"),
        "exact_r_missing_after_repair": row.get("exact_r_missing_after_repair"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def grouped_summaries(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("symbol_session_horizon_source", ("symbol", "route_session", "horizon_id", "source_component")),
        ("branch_source_component", ("matched_branch_queue_id", "symbol", "route_session", "source_component")),
        ("source_component", ("source_component",)),
        ("hard_decision", ("hard_repair_decision",)),
    ]
    output: list[dict[str, Any]] = []
    for family, fields in specs:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in repair_rows:
            groups[tuple(row.get(field) for field in fields)].append(row)
        for key, rows in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
            output.append(expectation_summary_row(rows, key, fields, len(output) + 1, family))
    return output


def bucket_rows(
    repair_rows: list[dict[str, Any]],
    exact_rows: list[dict[str, Any]],
    implementation_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    specs = [
        ("hard_repair_decision", repair_rows, "hard_repair_decision"),
        ("exact_broker_join_status", repair_rows, "exact_broker_join_status"),
        ("source_repaired_proxy_status", repair_rows, "source_repaired_proxy_status"),
        ("branch_source_status", repair_rows, "branch_source_status"),
        ("repair_queue", repair_rows, "repair_queue"),
        ("implementation_decision", implementation_rows, "implementation_decision"),
        ("source_name", source_rows, "source_name"),
        ("source_actual_r_allowed", source_rows, "actual_r_claim_allowed"),
        ("exact_join_status", exact_rows, "exact_broker_join_status"),
    ]
    distributions: dict[str, dict[str, int]] = {}
    rows: list[dict[str, Any]] = []
    for bucket_name, source, key in specs:
        counter = string_counter(source, key)
        distributions[bucket_name] = counter
        for value, count in counter.items():
            rows.append(
                with_common(
                    {
                        "bucket_row_id": f"OHLC-GTOS-BROKER-SOURCE-REPAIR-BUCKET-{len(rows) + 1:04d}",
                        "bucket_name": bucket_name,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return rows, distributions


def question_rows(generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    rows = []
    for question, action in [
        (
            "Which repair rows can become exact broker R from current local sources?",
            "Use exact-R join ledger; only direct trade/candidate/ticket joins can produce exact broker R.",
        ),
        (
            "Which source-join rows gained a scalar from matched branch evidence?",
            "Use source_repaired_proxy_status and branch_source_status counts in the repair result ledger.",
        ),
        (
            "Which scopes become default-off scorers versus avoid/redesign after repair?",
            "Use implementation decision ledger with repaired proxy means and exact-R rows.",
        ),
        (
            "Which source gaps remain exact owner/source/capture requirements?",
            "Use exact_broker_join_status and hard_repair_decision proof columns; act from current historical/source evidence.",
        ),
    ]:
        rows.append(
            with_common(
                {
                    "broker_source_repair_question_id": f"OHLC-GTOS-BROKER-SOURCE-REPAIR-Q-{len(rows) + 1:04d}",
                    "question": question,
                    "next_action": action,
                },
                generated_at,
                manifest_hash,
            )
        )
    return rows


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS})
    manifest["latest_branch_local_broker_source_repair_expectancy"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    event = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "broker_source_repair_expectancy_computed",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed numeric repair queue into broker/source repair joins, repaired proxy rows, exact-R join attempts, and implementation decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Broker Source Repair Expectancy",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Exact Join Status", ""])
    for status, count in result["bucket_distributions"]["exact_broker_join_status"].items():
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(["", "## Implementation Decisions", ""])
    for status, count in result["bucket_distributions"]["implementation_decision"].items():
        lines.append(f"- `{status}`: `{count}`")
    write_text(SUMMARY_PATH, "\n".join(lines) + "\n")


def main() -> int:
    generated_at = now_utc()
    trade_paths = sorted(path for path in TRADE_RECORD_ROOT.rglob("*.json") if not path.name.startswith("_"))
    source_paths = [
        NUMERIC_RESULT,
        NUMERIC_LEDGER,
        EVENT_SCORE_LEDGER,
        REPAIR_QUEUE_LEDGER,
        SCOPE_SCORE_LEDGER,
        SHADOW_RESULT,
        BRANCH_QUEUE_LEDGER,
        ACCEPTED_BRANCH_LEDGER,
        *BROKER_LOG_PATHS,
        *trade_paths,
        HELPER_MODULE,
        BUILDER_MODULE,
        VERIFIER_MODULE,
        TEST_MODULE,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)
    numeric_result = read_json(NUMERIC_RESULT)
    shadow_result = read_json(SHADOW_RESULT)
    numeric_rows = read_jsonl(NUMERIC_LEDGER)
    event_rows = read_jsonl(EVENT_SCORE_LEDGER)
    repair_queue_rows = read_jsonl(REPAIR_QUEUE_LEDGER)
    scope_rows = read_jsonl(SCOPE_SCORE_LEDGER)
    branch_queue_rows = read_jsonl(BRANCH_QUEUE_LEDGER)
    accepted_branch_rows = read_jsonl(ACCEPTED_BRANCH_LEDGER)

    numeric_by_id = {row.get("numeric_result_row_id"): row for row in numeric_rows}
    event_by_numeric = {row.get("input_numeric_result_row_id"): row for row in event_rows}
    branch_by_id = {row.get("branch_queue_id"): row for row in branch_queue_rows}
    accepted_by_id = {row.get("branch_queue_id"): row for row in accepted_branch_rows}
    raw_local_source_rows = load_local_source_observations()
    source_index = build_source_index(raw_local_source_rows)
    local_source_rows = [
        with_common(public_output_row(row), generated_at, manifest_hash)
        for row in raw_local_source_rows
    ]

    repair_result_rows: list[dict[str, Any]] = []
    for index, row in enumerate(repair_queue_rows, 1):
        numeric = numeric_by_id.get(row.get("input_numeric_result_row_id"))
        branch_id = (numeric or {}).get("matched_branch_queue_id")
        branch = accepted_by_id.get(branch_id) or branch_by_id.get(branch_id)
        repaired = repair_result_row(row, numeric, branch, source_index, index)
        repair_result_rows.append(with_common(public_output_row(repaired), generated_at, manifest_hash))
    exact_join_rows = [with_common(exact_join_row(row, index), generated_at, manifest_hash) for index, row in enumerate(repair_result_rows, 1)]
    expectancy_summary_rows = [
        with_common(row, generated_at, manifest_hash)
        for row in grouped_summaries(repair_result_rows)
    ]

    repair_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in repair_result_rows:
        key = "|".join(
            f"{field}={row.get(field) or ''}"
            for field in ("symbol", "route_session", "horizon_id", "source_component")
        )
        repair_by_scope[key].append(row)
    for row in event_rows:
        event_by_scope[str(row.get("aggregate_scope_key") or "")].append(row)
    implementation_rows = [
        with_common(
            implementation_decision_row(
                row,
                repair_by_scope.get(str(row.get("aggregate_scope_key") or ""), []),
                event_by_scope.get(str(row.get("aggregate_scope_key") or ""), []),
                index,
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(scope_rows, 1)
    ]
    buckets, distributions = bucket_rows(
        repair_result_rows,
        exact_join_rows,
        implementation_rows,
        local_source_rows,
        generated_at,
        manifest_hash,
    )
    questions = question_rows(generated_at, manifest_hash)

    exact_values = [row.get("exact_broker_r_value") for row in repair_result_rows if isinstance(row.get("exact_broker_r_value"), (int, float))]
    proxy_values = [
        row.get("source_repaired_proxy_value")
        for row in repair_result_rows
        if isinstance(row.get("source_repaired_proxy_value"), (int, float))
    ]
    counts = {
        "input_numeric_result_rows": len(numeric_rows),
        "input_event_score_rows": len(event_rows),
        "input_repair_queue_rows": len(repair_queue_rows),
        "input_scope_score_rows": len(scope_rows),
        "input_branch_queue_rows": len(branch_queue_rows),
        "input_accepted_branch_rows": len(accepted_branch_rows),
        "local_source_observation_rows": len(local_source_rows),
        "local_source_usable_exact_r_rows": sum(1 for row in local_source_rows if row.get("usable_exact_r_value") is not None),
        "local_source_geometry_rows": sum(1 for row in local_source_rows if row.get("geometry_available")),
        "repair_result_rows": len(repair_result_rows),
        "exact_r_join_rows": len(exact_join_rows),
        "exact_r_repaired_value_rows": len(exact_values),
        "source_repaired_proxy_rows": len(proxy_values),
        "source_repaired_proxy_added_from_branch_rows": sum(
            1
            for row in repair_result_rows
            if row.get("source_repaired_proxy_status") == "BRANCH_SOURCE_PROXY_ATTACHED_FROM_MATCHED_BRANCH"
        ),
        "branch_source_attached_rows": sum(
            1 for row in repair_result_rows if row.get("branch_source_status") == "BRANCH_SOURCE_ATTACHED_FROM_MATCHED_BRANCH_QUEUE"
        ),
        "expectancy_summary_rows": len(expectancy_summary_rows),
        "implementation_decision_rows": len(implementation_rows),
        "bucket_rows": len(buckets),
        "question_rows": len(questions),
        "source_manifest_rows": len(source_manifest),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "broker_source_repair_surface": BROKER_SOURCE_REPAIR_SURFACE,
        "counts": counts,
        "upstream_counts": {
            "numeric_result_tables": numeric_result["counts"],
            "numeric_shadow_scorer_compute": shadow_result["counts"],
        },
        "bucket_distributions": distributions,
        "source_repair_queue_fully_consumed": counts["repair_result_rows"] == counts["input_repair_queue_rows"],
        "exact_r_join_attempted_for_every_repair_row": counts["exact_r_join_rows"] == counts["repair_result_rows"],
        "scope_implementation_decisions_cover_all_scope_rows": counts["implementation_decision_rows"] == counts["input_scope_score_rows"],
        "repair_proxy_mean": round(mean(proxy_values), 10) if proxy_values else None,
        "exact_r_mean": round(mean(exact_values), 10) if exact_values else None,
        "no_summary_only_terminal_rows": all(
            row.get("summary_only_terminal") is False
            for row in repair_result_rows + exact_join_rows + expectancy_summary_rows + implementation_rows
        ),
    }
    executable_spec = {
        "artifact": f"{PREFIX}_EXECUTABLE_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "callable_surface": BROKER_SOURCE_REPAIR_SURFACE,
        "callables": [
            "source_observation",
            "build_source_index",
            "repair_result_row",
            "exact_join_from_sources",
            "expectation_summary_row",
            "implementation_decision_row",
        ],
        "direct_exact_r_join_policy": "only direct trade_id/candidate_id/fill_id/ticket/order/deal identifiers may attach exact broker R",
        "branch_source_repair_policy": "matched_branch_queue_id may attach branch/source proxy context but not exact broker geometry",
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
    outputs = [
        RESULT_PATH,
        EXECUTABLE_SPEC_PATH,
        SOURCE_OBSERVATION_LEDGER,
        REPAIR_RESULT_LEDGER,
        EXACT_R_JOIN_LEDGER,
        EXPECTANCY_SUMMARY_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(EXECUTABLE_SPEC_PATH, json.dumps(executable_spec, indent=2, sort_keys=True) + "\n")
    write_jsonl(SOURCE_OBSERVATION_LEDGER, local_source_rows)
    write_jsonl(REPAIR_RESULT_LEDGER, repair_result_rows)
    write_jsonl(EXACT_R_JOIN_LEDGER, exact_join_rows)
    write_jsonl(EXPECTANCY_SUMMARY_LEDGER, expectancy_summary_rows)
    write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_summary(result)
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
