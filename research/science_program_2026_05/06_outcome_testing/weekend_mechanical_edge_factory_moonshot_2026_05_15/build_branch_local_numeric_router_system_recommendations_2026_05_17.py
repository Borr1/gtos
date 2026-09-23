#!/usr/bin/env python3
"""Convert numeric router outputs into concrete branch-system recommendations."""

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


ROUTER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_MODULE_ROUTER_APPLICATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_ROUTER_SYSTEM_RECOMMENDATIONS"

ROUTER_RESULT = ROUTE_DIR / f"{ROUTER_PREFIX}_RESULT_2026-05-17.json"
ROUTER_APPLICATION_LEDGER = ROUTE_DIR / f"{ROUTER_PREFIX}_EVENT_APPLICATION_LEDGER_2026-05-17.jsonl"
ROUTER_SCORER_LEDGER = ROUTE_DIR / f"{ROUTER_PREFIX}_SCORER_OUTPUT_LEDGER_2026-05-17.jsonl"
ROUTER_AVOID_LEDGER = ROUTE_DIR / f"{ROUTER_PREFIX}_AVOID_FILTER_OUTPUT_LEDGER_2026-05-17.jsonl"
ROUTER_REPAIR_OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTER_PREFIX}_SOURCE_REPAIR_OUTPUT_LEDGER_2026-05-17.jsonl"
ROUTER_CONTEXT_LEDGER = ROUTE_DIR / f"{ROUTER_PREFIX}_CONTEXT_STRESS_OUTPUT_LEDGER_2026-05-17.jsonl"
ROUTER_SOURCE_REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{ROUTER_PREFIX}_SOURCE_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
ROUTER_SCOPE_DECISION_LEDGER = ROUTE_DIR / f"{ROUTER_PREFIX}_SCOPE_DECISION_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_numeric_module_registry_router.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTABLE_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_EXECUTABLE_SPEC_2026-05-17.json"
SCORER_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_REGISTRY_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_COMPARATOR_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_COMPARATOR_SCORE_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_PROOF_LEDGER_2026-05-17.jsonl"
CONTEXT_GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTEXT_GUARD_INPUT_LEDGER_2026-05-17.jsonl"
SCOPE_SYSTEM_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_SYSTEM_DECISION_LEDGER_2026-05-17.jsonl"
SYMBOL_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SYSTEM_DECISION_ROLLUP_LEDGER_2026-05-17.jsonl"
SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local numeric router system recommendations. This packet consumes router outputs into concrete scorer registry "
    "surfaces, avoid comparator score rows, source-repair proof rows, context guard inputs, scope decisions, symbol rollups, "
    "and a system recommendation. It does not place orders or change live behavior."
)


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


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-NUMERIC-ROUTER-SYSTEM-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "generated_utc": generated_at,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


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


def number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {value: int(counter[value]) for value in sorted(counter)}


def scorer_registry_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    score = number(row.get("numeric_module_event_score"))
    return {
        "scorer_registry_surface_row_id": f"OHLC-GTOS-NUMERIC-ROUTER-SCORER-SURFACE-{index:06d}",
        "input_router_application_row_id": row.get("numeric_module_router_application_row_id"),
        "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "registry_surface_status": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
        "registry_surface_score": score,
        "proxy_r_class": row.get("proxy_r_class"),
        "target_stop_order_class": row.get("target_stop_order_class"),
        "event_callable": "route_numeric_event",
        "registry_source_surface": "src/research_infra/moonshot_numeric_module_registry_router.py",
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def avoid_comparator_score(row: dict[str, Any], index: int) -> dict[str, Any]:
    proxy = number(row.get("decision_proxy_value")) or number(row.get("proxy_r_value")) or 0.0
    target_stop = str(row.get("target_stop_order_class") or "")
    if target_stop == "STOP_FIRST_PROXY_DOMINANT":
        action = "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY"
    elif target_stop == "TARGET_STOP_AMBIGUOUS_OR_MIXED":
        action = "FAIL_CLOSED_OR_DOWNWEIGHT_AMBIGUOUS_NEGATIVE_PROXY"
    else:
        action = "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE"
    return {
        "avoid_comparator_score_row_id": f"OHLC-GTOS-NUMERIC-ROUTER-AVOID-COMPARATOR-{index:06d}",
        "input_router_application_row_id": row.get("numeric_module_router_application_row_id"),
        "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "avoid_comparator_action": action,
        "avoid_comparator_score": -abs(proxy),
        "proxy_r_class": row.get("proxy_r_class"),
        "target_stop_order_class": target_stop,
        "underlying_mechanism_preserved": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def source_repair_proof(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("source_repair_execution_status") or "")
    if status == "SOURCE_REPAIR_EXECUTION_SOURCE_JOIN_NOT_PRESENT_IN_CURRENT_NUMERIC_PACKET":
        decision = "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF"
    elif status == "SOURCE_REPAIR_EXECUTION_BROKER_GEOMETRY_ATTACHMENT_REQUIRED":
        decision = "BROKER_GEOMETRY_ATTACHMENT_REQUIRED_FOR_EXACT_SPREAD_PROXY"
    elif status == "SOURCE_REPAIR_EXECUTION_BROKER_EXECUTION_GEOMETRY_FIELDS_REQUIRED":
        decision = "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R"
    else:
        decision = "REPLAY_PROXY_REPAIR_REQUIRED"
    return {
        "source_repair_proof_row_id": f"OHLC-GTOS-NUMERIC-ROUTER-SOURCE-REPAIR-PROOF-{index:06d}",
        "input_source_repair_execution_row_id": row.get("source_repair_execution_row_id"),
        "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "repair_action": row.get("repair_action"),
        "source_repair_execution_status": status,
        "source_repair_system_decision": decision,
        "exact_repair_possible_from_current_packet": row.get("exact_repair_possible_from_current_packet"),
        "missing_field_count": row.get("missing_field_count"),
        "exact_missing_field_proof": row.get("exact_missing_field_proof"),
        "opportunity_preserved": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def context_guard_input(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "context_guard_input_row_id": f"OHLC-GTOS-NUMERIC-ROUTER-CONTEXT-GUARD-{index:06d}",
        "input_router_application_row_id": row.get("numeric_module_router_application_row_id"),
        "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "context_guard_decision": "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT",
        "proxy_r_class": row.get("proxy_r_class"),
        "target_stop_order_class": row.get("target_stop_order_class"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def scope_system_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    decision = str(row.get("router_scope_decision") or "")
    candidate_type = {
        "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS": "DEFAULT_OFF_SCORER_REGISTRY_SCOPE",
        "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE": "AVOID_INVERSE_COMPARATOR_SCOPE",
        "EXECUTE_SOURCE_GEOMETRY_REPAIR_SCOPE": "SOURCE_GEOMETRY_REPAIR_SCOPE",
        "MERGE_CONTEXT_STRESS_SCOPE_AS_GUARD_INPUT": "CONTEXT_STRESS_GUARD_SCOPE",
    }.get(decision, "RECHECK_SCOPE")
    return {
        "scope_system_decision_row_id": f"OHLC-GTOS-NUMERIC-ROUTER-SCOPE-SYSTEM-{index:05d}",
        "input_scope_router_decision_row_id": row.get("scope_router_decision_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "row_count": row.get("row_count"),
        "scorer_event_count": row.get("scorer_event_count"),
        "avoid_inverse_event_count": row.get("avoid_inverse_event_count"),
        "source_repair_event_count": row.get("source_repair_event_count"),
        "context_stress_event_count": row.get("context_stress_event_count"),
        "score_count": row.get("score_count"),
        "score_mean": row.get("score_mean"),
        "score_min": row.get("score_min"),
        "score_max": row.get("score_max"),
        "router_scope_decision": decision,
        "implementation_candidate_type": candidate_type,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def symbol_rollups(scope_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scope_rows:
        groups[str(row.get("symbol"))].append(row)
    output = []
    for index, symbol in enumerate(sorted(groups), 1):
        rows = groups[symbol]
        scores = [number(row.get("score_mean")) for row in rows if number(row.get("score_mean")) is not None]
        output.append(
            with_common(
                {
                    "symbol_system_decision_rollup_row_id": f"OHLC-GTOS-NUMERIC-ROUTER-SYMBOL-ROLLUP-{index:04d}",
                    "symbol": symbol,
                    "scope_count": len(rows),
                    "scope_decision_counts": string_counter(rows, "router_scope_decision"),
                    "implementation_candidate_counts": string_counter(rows, "implementation_candidate_type"),
                    "score_scope_count": len(scores),
                    "score_mean_of_scope_means": round(mean(scores), 10) if scores else None,
                    "runtime_score_allowed": False,
                    "unconditional_scalar_use_allowed": False,
                    "candidate_use_allowed_now": False,
                    "live_effect": False,
                    "summary_only_terminal": False,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def bucket_rows(rows_by_name: dict[str, list[dict[str, Any]]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    specs = [
        ("registry_surface_status", "scorer", "registry_surface_status"),
        ("avoid_comparator_action", "avoid", "avoid_comparator_action"),
        ("source_repair_system_decision", "repair", "source_repair_system_decision"),
        ("context_guard_decision", "context", "context_guard_decision"),
        ("router_scope_decision", "scope", "router_scope_decision"),
        ("implementation_candidate_type", "scope", "implementation_candidate_type"),
        ("scope_symbol", "scope", "symbol"),
    ]
    output = []
    for bucket_name, group_name, key in specs:
        for value, count in string_counter(rows_by_name[group_name], key).items():
            output.append(
                with_common(
                    {
                        "bucket_row_id": f"OHLC-GTOS-NUMERIC-ROUTER-SYSTEM-BUCKET-{len(output) + 1:04d}",
                        "bucket_name": bucket_name,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS})
    manifest["latest_branch_local_numeric_router_system_recommendations"] = {
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
        "event": "branch_local_numeric_router_system_recommendations_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed numeric router outputs into scorer registry surfaces, avoid comparator rows, source-repair proof rows, context guard inputs, and scope/system decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Branch-Local Numeric Router System Recommendations",
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
    lines.extend(["", "## Scope Decisions", ""])
    for decision, count in result["bucket_distributions"]["router_scope_decision"].items():
        lines.append(f"- `{decision}`: `{count}`")
    lines.append("")
    write_text(SUMMARY_PATH, "\n".join(lines))


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows(
        [
            ROUTER_RESULT,
            ROUTER_APPLICATION_LEDGER,
            ROUTER_SCORER_LEDGER,
            ROUTER_AVOID_LEDGER,
            ROUTER_REPAIR_OUTPUT_LEDGER,
            ROUTER_CONTEXT_LEDGER,
            ROUTER_SOURCE_REPAIR_EXECUTION_LEDGER,
            ROUTER_SCOPE_DECISION_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    router_result = read_json(ROUTER_RESULT)
    scorer_input = read_jsonl(ROUTER_SCORER_LEDGER)
    avoid_input = read_jsonl(ROUTER_AVOID_LEDGER)
    repair_input = read_jsonl(ROUTER_SOURCE_REPAIR_EXECUTION_LEDGER)
    context_input = read_jsonl(ROUTER_CONTEXT_LEDGER)
    scope_input = read_jsonl(ROUTER_SCOPE_DECISION_LEDGER)

    scorer_rows = [with_common(scorer_registry_surface(row, index), generated_at, manifest_hash) for index, row in enumerate(scorer_input, 1)]
    avoid_rows = [with_common(avoid_comparator_score(row, index), generated_at, manifest_hash) for index, row in enumerate(avoid_input, 1)]
    repair_rows = [with_common(source_repair_proof(row, index), generated_at, manifest_hash) for index, row in enumerate(repair_input, 1)]
    context_rows = [with_common(context_guard_input(row, index), generated_at, manifest_hash) for index, row in enumerate(context_input, 1)]
    scope_rows = [with_common(scope_system_decision(row, index), generated_at, manifest_hash) for index, row in enumerate(scope_input, 1)]
    rollup_rows = symbol_rollups(scope_rows, generated_at, manifest_hash)
    rows_by_name = {"scorer": scorer_rows, "avoid": avoid_rows, "repair": repair_rows, "context": context_rows, "scope": scope_rows}
    buckets = bucket_rows(rows_by_name, generated_at, manifest_hash)
    counts = {
        "input_scorer_output_rows": len(scorer_input),
        "input_avoid_filter_output_rows": len(avoid_input),
        "input_source_repair_execution_rows": len(repair_input),
        "input_context_stress_output_rows": len(context_input),
        "input_scope_decision_rows": len(scope_input),
        "scorer_registry_surface_rows": len(scorer_rows),
        "avoid_comparator_score_rows": len(avoid_rows),
        "source_repair_proof_rows": len(repair_rows),
        "context_guard_input_rows": len(context_rows),
        "scope_system_decision_rows": len(scope_rows),
        "symbol_rollup_rows": len(rollup_rows),
        "system_recommendation_rows": 1,
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_rows),
    }
    distributions = {
        "registry_surface_status": string_counter(scorer_rows, "registry_surface_status"),
        "avoid_comparator_action": string_counter(avoid_rows, "avoid_comparator_action"),
        "source_repair_system_decision": string_counter(repair_rows, "source_repair_system_decision"),
        "context_guard_decision": string_counter(context_rows, "context_guard_decision"),
        "router_scope_decision": string_counter(scope_rows, "router_scope_decision"),
        "implementation_candidate_type": string_counter(scope_rows, "implementation_candidate_type"),
        "scope_symbol": string_counter(scope_rows, "symbol"),
    }
    system_recommendation_rows = [
        with_common(
            {
                "system_recommendation_row_id": "OHLC-GTOS-NUMERIC-ROUTER-SYSTEM-RECOMMENDATION-0001",
                "system_recommendation": (
                    "Register the 5,341 scorer surfaces default-off with source/control guards; convert the 4,115 avoid "
                    "rows into avoid/inverse comparator scoring; preserve the 17,753 source-repair proofs as exact "
                    "broker/source geometry requirements; bind the 1,513 context rows as guard inputs; and use the 290 "
                    "scope decisions as the current branch-local implementation map."
                ),
                "scorer_registry_surface_rows": len(scorer_rows),
                "avoid_comparator_score_rows": len(avoid_rows),
                "source_repair_proof_rows": len(repair_rows),
                "context_guard_input_rows": len(context_rows),
                "scope_system_decision_rows": len(scope_rows),
                "scope_decision_counts": distributions["router_scope_decision"],
                "not_terminal": True,
                "next_same_resource_layer": "branch-local source surface code registration, avoid comparator scoring, and source/broker geometry proof repair queue consumption",
            },
            generated_at,
            manifest_hash,
        )
    ]
    questions = [
        with_common(
            {
                "numeric_router_system_question_id": f"OHLC-GTOS-NUMERIC-ROUTER-SYSTEM-Q-{index:04d}",
                "question": question,
                "next_action": next_action,
                "current_counts": counts,
            },
            generated_at,
            manifest_hash,
        )
        for index, (question, next_action) in enumerate(
            [
                ("Which default-off scorer surfaces should be codified as importable registry entries?", "consume scorer registry surfaces into branch-local source code registry rows"),
                ("Which avoid comparator rows change branch-system decisions by symbol/session/horizon?", "score avoid comparator rows by scope and merge with scorer surfaces"),
                ("Which exact-R repair proofs require broker geometry versus source joins?", "split source repair proof ledger into broker-geometry and source-join repair work"),
                ("Which scope decisions dominate the branch-system map?", "consume full scope decision ledger into next recommendation comparator without top-N truncation"),
            ],
            1,
        )
    ]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "bucket_distributions": distributions,
        "router_output_counts_consumed": {
            "scorer": counts["input_scorer_output_rows"] == router_result["counts"]["scorer_output_rows"],
            "avoid": counts["input_avoid_filter_output_rows"] == router_result["counts"]["avoid_filter_output_rows"],
            "repair": counts["input_source_repair_execution_rows"] == router_result["counts"]["source_repair_execution_rows"],
            "context": counts["input_context_stress_output_rows"] == router_result["counts"]["context_stress_output_rows"],
            "scope": counts["input_scope_decision_rows"] == router_result["counts"]["scope_decision_rows"],
        },
        "split_outputs_preserved": len(scorer_rows) + len(avoid_rows) + len(context_rows) == (
            router_result["counts"]["scorer_output_rows"]
            + router_result["counts"]["avoid_filter_output_rows"]
            + router_result["counts"]["context_stress_output_rows"]
        ),
        "source_repair_proofs_preserved": len(repair_rows) == router_result["counts"]["source_repair_execution_rows"],
        "all_scope_rows_have_system_decision": len(scope_rows) == router_result["counts"]["scope_decision_rows"],
        "no_summary_only_terminal_rows": all(
            row.get("summary_only_terminal") is False
            for row in scorer_rows + avoid_rows + repair_rows + context_rows + scope_rows + rollup_rows
        ),
    }
    executable_spec = {
        "artifact": f"{PREFIX}_EXECUTABLE_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_manifest_hash": manifest_hash,
        "not_completion": True,
        "input_router_result": ROUTER_RESULT.relative_to(REPO).as_posix(),
        "output_ledgers": {
            "scorer_registry_surface": SCORER_REGISTRY_LEDGER.relative_to(REPO).as_posix(),
            "avoid_comparator_score": AVOID_COMPARATOR_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_proof": SOURCE_REPAIR_PROOF_LEDGER.relative_to(REPO).as_posix(),
            "context_guard_input": CONTEXT_GUARD_LEDGER.relative_to(REPO).as_posix(),
            "scope_system_decision": SCOPE_SYSTEM_DECISION_LEDGER.relative_to(REPO).as_posix(),
        },
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
    outputs = [
        RESULT_PATH,
        EXECUTABLE_SPEC_PATH,
        SCORER_REGISTRY_LEDGER,
        AVOID_COMPARATOR_LEDGER,
        SOURCE_REPAIR_PROOF_LEDGER,
        CONTEXT_GUARD_LEDGER,
        SCOPE_SYSTEM_DECISION_LEDGER,
        SYMBOL_ROLLUP_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(EXECUTABLE_SPEC_PATH, json.dumps(executable_spec, indent=2, sort_keys=True) + "\n")
    write_jsonl(SCORER_REGISTRY_LEDGER, scorer_rows)
    write_jsonl(AVOID_COMPARATOR_LEDGER, avoid_rows)
    write_jsonl(SOURCE_REPAIR_PROOF_LEDGER, repair_rows)
    write_jsonl(CONTEXT_GUARD_LEDGER, context_rows)
    write_jsonl(SCOPE_SYSTEM_DECISION_LEDGER, scope_rows)
    write_jsonl(SYMBOL_ROLLUP_LEDGER, rollup_rows)
    write_jsonl(SYSTEM_RECOMMENDATION_LEDGER, system_recommendation_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(result)
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
