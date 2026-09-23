#!/usr/bin/env python3
"""Run the branch-local numeric shadow scorer over current moonshot rows."""

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

from src.research_infra.moonshot_branch_local_shadow_scorer_compute import (
    SHADOW_SCORER_COMPUTE_SURFACE,
    build_shadow_scorer_registry,
    repair_queue_row,
    score_scope_event,
    scored_numeric_event,
)


NUMERIC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES"
SYSTEM_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_ROUTER_SYSTEM_RECOMMENDATIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_SHADOW_SCORER_COMPUTE"

NUMERIC_RESULT = ROUTE_DIR / f"{NUMERIC_PREFIX}_RESULT_2026-05-17.json"
NUMERIC_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{SYSTEM_PREFIX}_SCORER_REGISTRY_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_COMPARATOR_LEDGER = ROUTE_DIR / f"{SYSTEM_PREFIX}_AVOID_COMPARATOR_SCORE_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"{SYSTEM_PREFIX}_SOURCE_REPAIR_PROOF_LEDGER_2026-05-17.jsonl"
CONTEXT_GUARD_LEDGER = ROUTE_DIR / f"{SYSTEM_PREFIX}_CONTEXT_GUARD_INPUT_LEDGER_2026-05-17.jsonl"
SCOPE_SYSTEM_LEDGER = ROUTE_DIR / f"{SYSTEM_PREFIX}_SCOPE_SYSTEM_DECISION_LEDGER_2026-05-17.jsonl"
SYSTEM_RESULT = ROUTE_DIR / f"{SYSTEM_PREFIX}_RESULT_2026-05-17.json"

HELPER_MODULE = REPO / "src/research_infra/moonshot_branch_local_shadow_scorer_compute.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTABLE_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_EXECUTABLE_SPEC_2026-05-17.json"
EVENT_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_NUMERIC_EVENT_SCORE_LEDGER_2026-05-17.jsonl"
EXACT_R_COMPUTE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_R_COMPUTE_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_QUEUE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_REPAIR_QUEUE_LEDGER_2026-05-17.jsonl"
SCOPE_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_SCORE_DECISION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_HORIZON_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_HORIZON_SUMMARY_LEDGER_2026-05-17.jsonl"
SOURCE_COMPONENT_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_COMPONENT_SUMMARY_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local numeric shadow scorer compute. This packet runs callable scorer/source-repair code over the current "
    "numeric result rows and router recommendation ledgers, producing exact-R compute attempts, proxy-R score rows, "
    "scope decisions, repair queues, and summaries. It is research-only and has no live behavior."
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
                "source_manifest_id": f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-SRC-{index:04d}",
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


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {value: int(counter[value]) for value in sorted(counter)}


def number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def exact_compute_row(score_row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "exact_r_compute_row_id": f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-EXACT-R-{index:06d}",
        "input_numeric_result_row_id": score_row.get("input_numeric_result_row_id"),
        "symbol": score_row.get("symbol"),
        "route_session": score_row.get("route_session"),
        "horizon_id": score_row.get("horizon_id"),
        "primitive_flag": score_row.get("primitive_flag"),
        "source_component": score_row.get("source_component"),
        "source_row_id": score_row.get("source_row_id"),
        "exact_r_compute_status": score_row.get("exact_r_compute_status"),
        "exact_r_value": score_row.get("exact_r_value"),
        "exact_r_missing_fields": score_row.get("exact_r_missing_fields"),
        "proxy_r_value": score_row.get("proxy_r_value"),
        "cost_stress_adjusted_proxy_r": score_row.get("cost_stress_adjusted_proxy_r"),
        "shadow_score_basis": score_row.get("shadow_score_basis"),
        "shadow_score": score_row.get("shadow_score"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def summarize_group(rows: list[dict[str, Any]], group_key: tuple[Any, ...], row_id: str) -> dict[str, Any]:
    scores = [row.get("shadow_score") for row in rows if isinstance(row.get("shadow_score"), (int, float))]
    exact_values = [row.get("exact_r_value") for row in rows if isinstance(row.get("exact_r_value"), (int, float))]
    proxy_values = [row.get("cost_stress_adjusted_proxy_r") for row in rows if isinstance(row.get("cost_stress_adjusted_proxy_r"), (int, float))]
    return {
        "summary_row_id": row_id,
        "symbol": group_key[0],
        "route_session": group_key[1],
        "horizon_id": group_key[2],
        "source_component": group_key[3],
        "row_count": len(rows),
        "score_count": len(scores),
        "shadow_score_mean": round(mean(scores), 10) if scores else None,
        "shadow_score_min": min(scores) if scores else None,
        "shadow_score_max": max(scores) if scores else None,
        "exact_r_value_rows": len(exact_values),
        "exact_r_mean": round(mean(exact_values), 10) if exact_values else None,
        "proxy_r_value_rows": len(proxy_values),
        "proxy_r_mean": round(mean(proxy_values), 10) if proxy_values else None,
        "shadow_decision_counts": string_counter(rows, "shadow_decision"),
        "target_stop_order_counts": string_counter(rows, "target_stop_order_class"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def summary_rows(event_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ssh_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    component_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in event_rows:
        ssh_groups[(row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("source_component"))].append(row)
        component_groups[(None, None, None, row.get("source_component"))].append(row)
    ssh_rows = [
        with_common(summarize_group(rows, key, f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-SSH-SUMMARY-{index:04d}"), generated_at, manifest_hash)
        for index, (key, rows) in enumerate(sorted(ssh_groups.items(), key=lambda item: tuple(str(part) for part in item[0])), 1)
    ]
    component_rows = [
        with_common(summarize_group(rows, key, f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-COMPONENT-SUMMARY-{index:04d}"), generated_at, manifest_hash)
        for index, (key, rows) in enumerate(sorted(component_groups.items(), key=lambda item: tuple(str(part) for part in item[0])), 1)
    ]
    return ssh_rows, component_rows


def bucket_rows(groups: dict[str, list[dict[str, Any]]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    specs = [
        ("shadow_decision", "event", "shadow_decision"),
        ("shadow_score_basis", "event", "shadow_score_basis"),
        ("exact_r_compute_status", "event", "exact_r_compute_status"),
        ("cost_adjustment_status", "event", "cost_adjustment_status"),
        ("repair_queue", "repair", "repair_queue"),
        ("source_repair_system_decision", "repair", "source_repair_system_decision"),
        ("scope_shadow_decision", "scope", "scope_shadow_decision"),
        ("symbol", "scope", "symbol"),
    ]
    output: list[dict[str, Any]] = []
    distributions: dict[str, dict[str, int]] = {}
    for bucket_name, group_name, key in specs:
        counter = string_counter(groups[group_name], key)
        distributions[bucket_name] = counter
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_row_id": f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-BUCKET-{len(output) + 1:04d}",
                        "bucket_name": bucket_name,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output, distributions


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS})
    manifest["latest_branch_local_numeric_shadow_scorer_compute"] = {
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
        "event": "branch_local_numeric_shadow_scorer_compute_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Ran callable branch-local shadow scorer and source-repair compute over all numeric rows and recommendation ledgers.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Branch-Local Numeric Shadow Scorer Compute",
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
    lines.extend(["", "## Decisions", ""])
    for decision, count in result["bucket_distributions"]["scope_shadow_decision"].items():
        lines.append(f"- `{decision}`: `{count}`")
    write_text(SUMMARY_PATH, "\n".join(lines) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows(
        [
            NUMERIC_RESULT,
            NUMERIC_LEDGER,
            SCORER_SURFACE_LEDGER,
            AVOID_COMPARATOR_LEDGER,
            SOURCE_REPAIR_PROOF_LEDGER,
            CONTEXT_GUARD_LEDGER,
            SCOPE_SYSTEM_LEDGER,
            SYSTEM_RESULT,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    numeric_result = read_json(NUMERIC_RESULT)
    system_result = read_json(SYSTEM_RESULT)
    numeric_rows = read_jsonl(NUMERIC_LEDGER)
    scorer_surface_rows = read_jsonl(SCORER_SURFACE_LEDGER)
    avoid_rows = read_jsonl(AVOID_COMPARATOR_LEDGER)
    source_repair_rows = read_jsonl(SOURCE_REPAIR_PROOF_LEDGER)
    context_rows = read_jsonl(CONTEXT_GUARD_LEDGER)
    scope_rows_input = read_jsonl(SCOPE_SYSTEM_LEDGER)

    event_score_rows = [
        with_common(scored_numeric_event(row, index), generated_at, manifest_hash)
        for index, row in enumerate(numeric_rows, 1)
    ]
    exact_rows = [
        with_common(exact_compute_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(event_score_rows, 1)
    ]
    repair_rows = [
        with_common(repair_queue_row(row, index), generated_at, manifest_hash)
        for index, row in enumerate(source_repair_rows, 1)
    ]
    registry = build_shadow_scorer_registry(event_score_rows, repair_rows)
    scope_score_rows = [
        with_common(score_scope_event(row, registry, index), generated_at, manifest_hash)
        for index, row in enumerate(scope_rows_input, 1)
    ]
    ssh_summary_rows, source_component_rows = summary_rows(event_score_rows, generated_at, manifest_hash)
    buckets, distributions = bucket_rows(
        {"event": event_score_rows, "repair": repair_rows, "scope": scope_score_rows},
        generated_at,
        manifest_hash,
    )
    questions = [
        with_common(
            {
                "numeric_shadow_scorer_question_id": f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-Q-{index:04d}",
                "question": question,
                "next_action": next_action,
            },
            generated_at,
            manifest_hash,
        )
        for index, (question, next_action) in enumerate(
            [
                ("Which default-off proxy scopes survive avoid penalties?", "use scope score ledger to bind default-off scorers with avoid/source guards"),
                ("Which exact-R rows can be computed from current broker geometry?", "consume exact-R compute ledger and repair missing geometry rows"),
                ("Which repair queue is broker-geometry versus source-join dominated?", "execute broker/source repair queues separately"),
                ("Which symbol/session/horizon/source components concentrate positive and negative scores?", "consume full summary ledgers before any branch-system recommendation"),
            ],
            1,
        )
    ]

    counts = {
        "input_numeric_result_rows": len(numeric_rows),
        "input_scorer_surface_rows": len(scorer_surface_rows),
        "input_avoid_comparator_rows": len(avoid_rows),
        "input_source_repair_proof_rows": len(source_repair_rows),
        "input_context_guard_rows": len(context_rows),
        "input_scope_system_rows": len(scope_rows_input),
        "numeric_event_score_rows": len(event_score_rows),
        "exact_r_compute_rows": len(exact_rows),
        "exact_r_value_rows": sum(1 for row in exact_rows if row.get("exact_r_value") is not None),
        "proxy_score_rows": sum(1 for row in event_score_rows if row.get("shadow_score_basis") == "proxy_r"),
        "source_repair_queue_rows": len(repair_rows),
        "scope_score_decision_rows": len(scope_score_rows),
        "symbol_session_horizon_summary_rows": len(ssh_summary_rows),
        "source_component_summary_rows": len(source_component_rows),
        "bucket_rows": len(buckets),
        "question_rows": len(questions),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "shadow_scorer_compute_surface": SHADOW_SCORER_COMPUTE_SURFACE,
        "counts": counts,
        "upstream_counts": {
            "numeric_result_tables": numeric_result["counts"],
            "numeric_router_system_recommendations": system_result["counts"],
        },
        "bucket_distributions": distributions,
        "all_numeric_rows_scored": counts["numeric_event_score_rows"] == numeric_result["counts"]["numeric_result_rows"],
        "all_exact_r_attempted": counts["exact_r_compute_rows"] == counts["numeric_event_score_rows"],
        "all_source_repair_proofs_queued": counts["source_repair_queue_rows"] == system_result["counts"]["source_repair_proof_rows"],
        "all_scope_rows_scored": counts["scope_score_decision_rows"] == system_result["counts"]["scope_system_decision_rows"],
        "no_summary_only_terminal_rows": all(
            row.get("summary_only_terminal") is False
            for row in event_score_rows + exact_rows + repair_rows + scope_score_rows + ssh_summary_rows + source_component_rows
        ),
    }
    executable_spec = {
        "artifact": f"{PREFIX}_EXECUTABLE_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "shadow_scorer_compute_surface": SHADOW_SCORER_COMPUTE_SURFACE,
        "callables": [
            "scored_numeric_event",
            "exact_r_from_geometry",
            "repair_queue_row",
            "build_shadow_scorer_registry",
            "score_scope_event",
        ],
        "input_numeric_rows": NUMERIC_LEDGER.relative_to(REPO).as_posix(),
        "output_event_score_ledger": EVENT_SCORE_LEDGER.relative_to(REPO).as_posix(),
        "output_exact_r_compute_ledger": EXACT_R_COMPUTE_LEDGER.relative_to(REPO).as_posix(),
        "output_source_repair_queue_ledger": SOURCE_REPAIR_QUEUE_LEDGER.relative_to(REPO).as_posix(),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
    outputs = [
        RESULT_PATH,
        EXECUTABLE_SPEC_PATH,
        EVENT_SCORE_LEDGER,
        EXACT_R_COMPUTE_LEDGER,
        SOURCE_REPAIR_QUEUE_LEDGER,
        SCOPE_SCORE_LEDGER,
        SYMBOL_SESSION_HORIZON_SUMMARY_LEDGER,
        SOURCE_COMPONENT_SUMMARY_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(EXECUTABLE_SPEC_PATH, json.dumps(executable_spec, indent=2, sort_keys=True) + "\n")
    write_jsonl(EVENT_SCORE_LEDGER, event_score_rows)
    write_jsonl(EXACT_R_COMPUTE_LEDGER, exact_rows)
    write_jsonl(SOURCE_REPAIR_QUEUE_LEDGER, repair_rows)
    write_jsonl(SCOPE_SCORE_LEDGER, scope_score_rows)
    write_jsonl(SYMBOL_SESSION_HORIZON_SUMMARY_LEDGER, ssh_summary_rows)
    write_jsonl(SOURCE_COMPONENT_SUMMARY_LEDGER, source_component_rows)
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
