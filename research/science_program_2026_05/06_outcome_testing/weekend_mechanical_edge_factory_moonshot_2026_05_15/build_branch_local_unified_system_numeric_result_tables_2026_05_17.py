#!/usr/bin/env python3
"""Compute numeric result tables from integrated execution rows.

This builder consumes the committed 17,916-row integrated-result execution
packet and joins it to computed action rows, no-fill source sidecars, and the
386-row branch R-style replay table. It writes numeric exact/proxy-R,
expectancy, target/stop, cost/stress, and keep/redesign/implement decision
tables rather than another routing/materialization layer.
"""

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

from src.research_infra.moonshot_integrated_result_numeric_scorer import (
    NUMERIC_SCORER_SURFACE,
    numeric_result_row,
    numeric_rollup,
)


EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION_BUNDLE"
COMPUTED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES"

EXEC_RESULT = ROUTE_DIR / f"{EXEC_PREFIX}_RESULT_2026-05-17.json"
EXEC_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_INTEGRATED_RESULT_EXECUTION_LEDGER_2026-05-17.jsonl"
COMPUTED_LEDGER = ROUTE_DIR / f"{COMPUTED_PREFIX}_COMPUTED_ACTION_LEDGER_2026-05-17.jsonl"
BRANCH_RSTYLE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
EXACT_REPAIR_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_EXACT_REPAIR_BRANCH_LEDGER_2026-05-16.jsonl"

SIDE_SOURCE_FILES = [
    ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl",
    ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl",
    ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_SOURCE_CONFIDENCE_BRANCH_LEDGER_2026-05-16.jsonl",
    ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_FAMILY_SYNTHESIS_LEDGER_2026-05-16.jsonl",
    ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl",
    ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl",
    ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_SOURCE_REQUIREMENT_LEDGER_2026-05-16.jsonl",
]

HELPER_MODULE = REPO / NUMERIC_SCORER_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
NUMERIC_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl"
PROXY_EXPECTANCY_LEDGER = ROUTE_DIR / f"{PREFIX}_PROXY_R_EXPECTANCY_RESULT_LEDGER_2026-05-17.jsonl"
EXACT_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_R_OR_MISSING_PROOF_LEDGER_2026-05-17.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_KEEP_KILL_REDESIGN_IMPLEMENT_DECISION_LEDGER_2026-05-17.jsonl"
SOURCE_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GEOMETRY_REPAIR_LEDGER_2026-05-17.jsonl"
FAMILY_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_EXPECTANCY_SUMMARY_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_HORIZON_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_HORIZON_EXPECTANCY_SUMMARY_LEDGER_2026-05-17.jsonl"
SOURCE_COMPONENT_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_COMPONENT_SUMMARY_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local numeric result tables for integrated execution rows. This packet consumes the latest 17,916-row "
    "integrated-result execution ledger into exact/proxy-R, expectancy-style proxy, target/stop, cost/stress, "
    "source/geometry proof, and keep/redesign/implement decisions. It is research-only, does not place orders, and "
    "does not change live behavior."
)

SIDE_ID_KEYS = (
    "avoid_filter_branch_id",
    "retest_redesign_branch_id",
    "source_confidence_branch_id",
    "family_synthesis_id",
    "near_miss_entry_control_offset_branch_id",
    "near_miss_entry_control_market_branch_id",
    "near_miss_entry_control_source_requirement_id",
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
    if not path.exists() and not Path(long_path(path)).exists():
        return None
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-NUMERIC-RESULT-SRC-{index:04d}",
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


def sidecar_id(row: dict[str, Any]) -> str | None:
    for key in SIDE_ID_KEYS:
        value = row.get(key)
        if value:
            return str(value)
    return None


def branch_scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any] | None:
    route_candidate_id = row.get("route_candidate_id")
    target_stop_contract_id = row.get("target_stop_contract_id")
    entry_variant = row.get("entry_variant") or row.get("source_entry_variant")
    if route_candidate_id and target_stop_contract_id and entry_variant:
        return (route_candidate_id, target_stop_contract_id, entry_variant)
    return None


def build_sidecar_map(paths: list[Path]) -> dict[str, dict[str, Any]]:
    sidecars: dict[str, dict[str, Any]] = {}
    for path in paths:
        for row in read_jsonl(path):
            row_id = sidecar_id(row)
            if row_id:
                sidecars[row_id] = row
    return sidecars


def build_branch_maps(branch_rows: list[dict[str, Any]], exact_repair_rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[tuple[Any, Any, Any], list[dict[str, Any]]]]:
    by_id = {str(row.get("branch_queue_id")): row for row in branch_rows if row.get("branch_queue_id")}
    for row in exact_repair_rows:
        branch_id = row.get("branch_queue_id")
        if branch_id and branch_id in by_id:
            merged = dict(by_id[str(branch_id)])
            merged.update({f"exact_repair_{key}": value for key, value in row.items() if key not in merged})
            merged["repair_feasibility_class"] = row.get("repair_feasibility_class")
            by_id[str(branch_id)] = merged
    by_scope: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in by_id.values():
        key = branch_scope_key(row)
        if key:
            by_scope[key].append(row)
    return by_id, by_scope


def match_branch(
    execution_row: dict[str, Any],
    sidecar_row: dict[str, Any] | None,
    branch_by_id: dict[str, dict[str, Any]],
    branch_by_scope: dict[tuple[Any, Any, Any], list[dict[str, Any]]],
) -> tuple[dict[str, Any] | None, int, str]:
    source_row_id = str(execution_row.get("source_row_id") or "")
    if source_row_id in branch_by_id:
        return branch_by_id[source_row_id], 1, "DIRECT_BRANCH_QUEUE_ID_MATCH"
    if sidecar_row:
        key = branch_scope_key(sidecar_row)
        matches = branch_by_scope.get(key, []) if key else []
        if len(matches) == 1:
            return matches[0], 1, "SIDECAR_SCOPE_UNIQUE_BRANCH_MATCH"
        if matches:
            return None, len(matches), "SIDECAR_SCOPE_MULTIPLE_BRANCH_MATCHES_PRESERVED"
    return None, 0, "NO_BRANCH_SCOPE_MATCH"


def proxy_expectancy_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "numeric_result_row_id",
        "input_integrated_result_execution_row_id",
        "input_unified_system_computed_action_row_id",
        "source_component",
        "source_row_id",
        "symbol",
        "route_session",
        "horizon_id",
        "primitive_flag",
        "integrated_result_execution_family",
        "computed_action_family",
        "proxy_r_status",
        "proxy_r_class",
        "proxy_r_value",
        "proxy_r_lower",
        "proxy_r_upper",
        "proxy_r_method",
        "expectancy_proxy_value",
        "expectancy_proxy_method",
        "pass_control_delta_proxy",
        "target_stop_order_class",
        "cost_stress_status",
        "keep_kill_redesign_implement_decision",
    ]
    return {key: row.get(key) for key in keys}


def exact_proof_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "numeric_result_row_id",
        "input_integrated_result_execution_row_id",
        "source_component",
        "source_row_id",
        "symbol",
        "route_session",
        "horizon_id",
        "exact_r_status",
        "exact_r_value",
        "exact_r_source_key",
        "exact_missing_field_proof",
        "branch_match_status",
        "matched_branch_queue_id",
        "sidecar_source_row_joined",
        "source_hashes",
    ]
    return {key: row.get(key) for key in keys}


def decision_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "numeric_result_row_id",
        "source_component",
        "source_row_id",
        "symbol",
        "route_session",
        "horizon_id",
        "primitive_flag",
        "integrated_result_execution_family",
        "computed_action_family",
        "proxy_r_class",
        "target_stop_order_class",
        "exact_r_status",
        "cost_stress_status",
        "keep_kill_redesign_implement_decision",
        "negative_or_failure_intelligence_role",
        "missing_geometry_source_decision",
    ]
    return {key: row.get(key) for key in keys}


def source_repair_required(row: dict[str, Any]) -> bool:
    if str(row.get("exact_r_status") or "").startswith("EXACT_R_NOT_COMPUTABLE"):
        return True
    if row.get("proxy_r_value") is None:
        return True
    if row.get("cost_stress_status") == "COST_STRESS_NOT_COMPUTABLE_NO_SPREAD_OR_SLIPPAGE_FIELD":
        return True
    if row.get("target_stop_order_class") == "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return True
    return False


def source_repair_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_geometry_repair_row_id": row["numeric_result_row_id"].replace("NUMERIC-RESULT", "SOURCE-REPAIR"),
        "input_numeric_result_row_id": row["numeric_result_row_id"],
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "missing_source_or_geometry_proof": {
            "exact_missing_field_proof": row.get("exact_missing_field_proof"),
            "cost_stress_status": row.get("cost_stress_status"),
            "target_stop_order_class": row.get("target_stop_order_class"),
            "branch_match_status": row.get("branch_match_status"),
        },
        "repair_implementation_action": (
            "join_or_reconstruct_broker_execution_geometry"
            if row.get("proxy_r_value") is not None
            else "repair_source_sidecar_or_branch_replay_before_numeric_score"
        ),
        "opportunity_preserved": True,
    }


def build_rollups(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_ssh: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_component: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[
            (
                row.get("integrated_result_execution_family"),
                row.get("computed_action_family"),
                row.get("source_component"),
            )
        ].append(row)
        by_ssh[(row.get("symbol"), row.get("route_session"), row.get("horizon_id"))].append(row)
        by_component[(row.get("source_component"),)].append(row)
    family_rows = [
        with_common(numeric_rollup(key, by_family[key], index, "family_expectancy"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    ssh_rows = [
        with_common(numeric_rollup(key, by_ssh[key], index, "symbol_session_horizon_expectancy"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_ssh, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    component_rows = [
        with_common(numeric_rollup(key, by_component[key], index, "source_component_expectancy"), generated_at, manifest_hash)
        for index, key in enumerate(sorted(by_component, key=lambda item: tuple(str(part) for part in item)), 1)
    ]
    return family_rows, ssh_rows, component_rows


def bucket_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    specs = [
        ("exact_r_status", "exact_r_status"),
        ("proxy_r_class", "proxy_r_class"),
        ("target_stop_order_class", "target_stop_order_class"),
        ("cost_stress_status", "cost_stress_status"),
        ("decision", "keep_kill_redesign_implement_decision"),
        ("source_component", "source_component"),
        ("execution_family", "integrated_result_execution_family"),
        ("branch_match_status", "branch_match_status"),
    ]
    output = []
    seq = 1
    for bucket_name, key in specs:
        counter = Counter(str(row.get(key)) for row in rows)
        for value in sorted(counter):
            output.append(
                with_common(
                    {
                        "bucket_row_id": f"OHLC-GTOS-NUMERIC-RESULT-BUCKET-{seq:04d}",
                        "bucket_name": bucket_name,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    },
                    generated_at,
                    manifest_hash,
                )
            )
            seq += 1
    return output


def question_rows(result_counts: dict[str, Any], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    questions = [
        (
            "exact_r_geometry_repair",
            "Which source rows can be upgraded from proxy R to exact broker R by joining order/deal/fill lifecycle fields?",
            "execute_source_geometry_repair_rows_before_any_exact_R_claim",
        ),
        (
            "cost_stress_expansion",
            "Which proxy-positive rows lose edge after spread/slippage evidence is joined?",
            "run spread/slippage source builders for rows with COST_STRESS_NOT_COMPUTABLE",
        ),
        (
            "negative_proxy_conversion",
            "Which negative rows should become avoid/inverse filters, source guards, or failure features?",
            "consume strong-negative and negative decision rows into avoid/inverse modules",
        ),
        (
            "market_transfer_numeric_followup",
            "Do outside-market rows keep positive proxy R after symbol/session/horizon rollup controls?",
            "run transfer rollup controls without collapsing outside-market evidence",
        ),
    ]
    return [
        with_common(
            {
                "numeric_question_id": f"OHLC-GTOS-NUMERIC-RESULT-QUESTION-{index:04d}",
                "question_key": key,
                "question": question,
                "next_action": action,
                "current_result_counts": result_counts,
            },
            generated_at,
            manifest_hash,
        )
        for index, (key, question, action) in enumerate(questions, 1)
    ]


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Branch-Local Unified System Numeric Result Tables",
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
    lines.extend(["", "## Numeric Distributions", ""])
    for key, value in result["bucket_distributions"].items():
        lines.append(f"### {key}")
        for bucket, count in value.items():
            lines.append(f"- `{bucket}`: `{count}`")
        lines.append("")
    lines.extend(
        [
            "## Continuation",
            "",
            "This checkpoint is numeric scoring work. The next same-resource step is to consume the decision ledger into runnable default-off scorer modules, source-geometry repair code, and avoid/inverse filters for negative proxy rows.",
            "",
        ]
    )
    write_text(SUMMARY_PATH, "\n".join(lines))


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS})
    manifest["latest_branch_local_unified_system_numeric_result_tables"] = {
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
        "event": "branch_local_unified_system_numeric_result_tables_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Computed numeric exact/proxy-R, expectancy, target/stop, cost/stress, and keep/redesign/implement result tables from 17,916 integrated execution rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        EXEC_RESULT,
        EXEC_LEDGER,
        COMPUTED_LEDGER,
        BRANCH_RSTYLE_LEDGER,
        EXACT_REPAIR_LEDGER,
        *SIDE_SOURCE_FILES,
        HELPER_MODULE,
        BUILDER_MODULE,
        VERIFIER_MODULE,
        TEST_MODULE,
    ]
    source_rows, manifest_hash = source_manifest_rows(source_paths, generated_at)

    execution_rows = read_jsonl(EXEC_LEDGER)
    computed_rows = read_jsonl(COMPUTED_LEDGER)
    computed_by_id = {
        str(row.get("unified_system_computed_action_row_id")): row
        for row in computed_rows
        if row.get("unified_system_computed_action_row_id")
    }
    branch_by_id, branch_by_scope = build_branch_maps(read_jsonl(BRANCH_RSTYLE_LEDGER), read_jsonl(EXACT_REPAIR_LEDGER))
    sidecars = build_sidecar_map(SIDE_SOURCE_FILES)

    numeric_rows: list[dict[str, Any]] = []
    for index, execution_row in enumerate(execution_rows, 1):
        computed = computed_by_id.get(str(execution_row.get("input_unified_system_computed_action_row_id")))
        source_row_id = str(execution_row.get("source_row_id") or "")
        sidecar = sidecars.get(source_row_id)
        if sidecar is None and computed:
            sidecar = sidecars.get(str(computed.get("source_sidecar_row_id") or ""))
        branch, match_count, match_status = match_branch(execution_row, sidecar, branch_by_id, branch_by_scope)
        numeric_rows.append(
            with_common(
                numeric_result_row(
                    execution_row,
                    computed,
                    branch,
                    sidecar,
                    index,
                    branch_match_count=match_count,
                    branch_match_status=match_status,
                ),
                generated_at,
                manifest_hash,
            )
        )

    proxy_rows = [with_common(proxy_expectancy_row(row), generated_at, manifest_hash) for row in numeric_rows]
    exact_rows = [with_common(exact_proof_row(row), generated_at, manifest_hash) for row in numeric_rows]
    decision_rows = [with_common(decision_row(row), generated_at, manifest_hash) for row in numeric_rows]
    source_repair_rows = [with_common(source_repair_row(row), generated_at, manifest_hash) for row in numeric_rows if source_repair_required(row)]
    family_rows, ssh_rows, component_rows = build_rollups(numeric_rows, generated_at, manifest_hash)
    buckets = bucket_rows(numeric_rows, generated_at, manifest_hash)

    counts = {
        "input_integrated_execution_rows": len(execution_rows),
        "input_computed_action_rows": len(computed_rows),
        "numeric_result_rows": len(numeric_rows),
        "proxy_expectancy_rows": len(proxy_rows),
        "exact_r_or_missing_proof_rows": len(exact_rows),
        "decision_rows": len(decision_rows),
        "source_geometry_repair_rows": len(source_repair_rows),
        "family_summary_rows": len(family_rows),
        "symbol_session_horizon_summary_rows": len(ssh_rows),
        "source_component_summary_rows": len(component_rows),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_rows),
        "computed_row_joined_rows": sum(1 for row in numeric_rows if row["computed_action_row_joined"]),
        "branch_rstyle_joined_rows": sum(1 for row in numeric_rows if row["branch_rstyle_row_joined"]),
        "sidecar_joined_rows": sum(1 for row in numeric_rows if row["sidecar_source_row_joined"]),
        "numeric_proxy_r_rows": sum(1 for row in numeric_rows if row["proxy_r_value"] is not None),
        "exact_r_value_rows": sum(1 for row in numeric_rows if row["exact_r_value"] is not None),
    }
    bucket_distributions = {
        "exact_r_status": dict(Counter(str(row["exact_r_status"]) for row in numeric_rows)),
        "proxy_r_class": dict(Counter(str(row["proxy_r_class"]) for row in numeric_rows)),
        "target_stop_order_class": dict(Counter(str(row["target_stop_order_class"]) for row in numeric_rows)),
        "cost_stress_status": dict(Counter(str(row["cost_stress_status"]) for row in numeric_rows)),
        "decision": dict(Counter(str(row["keep_kill_redesign_implement_decision"]) for row in numeric_rows)),
        "source_component": dict(Counter(str(row["source_component"]) for row in numeric_rows)),
        "execution_family": dict(Counter(str(row["integrated_result_execution_family"]) for row in numeric_rows)),
        "branch_match_status": dict(Counter(str(row["branch_match_status"]) for row in numeric_rows)),
    }

    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_manifest_hash": manifest_hash,
        "numeric_scorer_surface": NUMERIC_SCORER_SURFACE,
        "counts": counts,
        "bucket_distributions": bucket_distributions,
        "all_integrated_execution_rows_consumed": counts["numeric_result_rows"] == counts["input_integrated_execution_rows"],
        "all_numeric_rows_have_decision": counts["decision_rows"] == counts["numeric_result_rows"],
        "no_summary_only_terminal_rows": all(row.get("summary_only_terminal") is False for row in numeric_rows),
        "output_files": {
            "numeric_result_ledger": NUMERIC_RESULT_LEDGER.relative_to(REPO).as_posix(),
            "proxy_expectancy_ledger": PROXY_EXPECTANCY_LEDGER.relative_to(REPO).as_posix(),
            "exact_proof_ledger": EXACT_PROOF_LEDGER.relative_to(REPO).as_posix(),
            "decision_ledger": DECISION_LEDGER.relative_to(REPO).as_posix(),
            "source_repair_ledger": SOURCE_REPAIR_LEDGER.relative_to(REPO).as_posix(),
        },
    }
    questions = question_rows(counts, generated_at, manifest_hash)

    runtime_spec = {
        "artifact": PREFIX,
        "numeric_scorer_surface": NUMERIC_SCORER_SURFACE,
        "input": {
            "integrated_execution_ledger": EXEC_LEDGER.relative_to(REPO).as_posix(),
            "computed_action_ledger": COMPUTED_LEDGER.relative_to(REPO).as_posix(),
            "branch_rstyle_ledger": BRANCH_RSTYLE_LEDGER.relative_to(REPO).as_posix(),
            "side_source_files": [path.relative_to(REPO).as_posix() for path in SIDE_SOURCE_FILES],
        },
        "output": result["output_files"],
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }

    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime_spec, indent=2, sort_keys=True) + "\n")
    write_jsonl(NUMERIC_RESULT_LEDGER, numeric_rows)
    write_jsonl(PROXY_EXPECTANCY_LEDGER, proxy_rows)
    write_jsonl(EXACT_PROOF_LEDGER, exact_rows)
    write_jsonl(DECISION_LEDGER, decision_rows)
    write_jsonl(SOURCE_REPAIR_LEDGER, source_repair_rows)
    write_jsonl(FAMILY_SUMMARY_LEDGER, family_rows)
    write_jsonl(SYMBOL_SESSION_HORIZON_SUMMARY_LEDGER, ssh_rows)
    write_jsonl(SOURCE_COMPONENT_SUMMARY_LEDGER, component_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(result)

    outputs = [
        RESULT_PATH,
        RUNTIME_SPEC_PATH,
        NUMERIC_RESULT_LEDGER,
        PROXY_EXPECTANCY_LEDGER,
        EXACT_PROOF_LEDGER,
        DECISION_LEDGER,
        SOURCE_REPAIR_LEDGER,
        FAMILY_SUMMARY_LEDGER,
        SYMBOL_SESSION_HORIZON_SUMMARY_LEDGER,
        SOURCE_COMPONENT_SUMMARY_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
