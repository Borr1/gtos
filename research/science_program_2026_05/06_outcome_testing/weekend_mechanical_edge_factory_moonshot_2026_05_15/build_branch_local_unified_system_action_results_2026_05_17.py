#!/usr/bin/env python3
"""Execute unified system work orders into branch-local action result rows."""

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

from src.research_infra.moonshot_branch_local_unified_system_action_results import (
    UNIFIED_SYSTEM_ACTION_RESULT_SURFACE,
    action_result_from_work_order,
    action_result_rollup,
)


PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_ACTION_RESULT_BUNDLE"
WORK_ORDER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE"

WORK_ORDER_RESULT_PATH = ROUTE_DIR / f"{WORK_ORDER_PREFIX}_RESULT_2026-05-17.json"
WORK_ORDER_LEDGER = ROUTE_DIR / f"{WORK_ORDER_PREFIX}_WORK_ORDER_LEDGER_2026-05-17.jsonl"
MARKET_EXPANSION_LEDGER = ROUTE_DIR / f"{WORK_ORDER_PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_ACTION_RESULT_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
ACTION_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_RESULT_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_RESULT_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_REPAIR_RESULT_LEDGER_2026-05-17.jsonl"
SCORE_WITH_CONTROL_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_WITH_CONTROL_RESULT_LEDGER_2026-05-17.jsonl"
REDESIGN_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_EXECUTION_RESULT_LEDGER_2026-05-17.jsonl"
GUARD_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_RESULT_LEDGER_2026-05-17.jsonl"
AUDIT_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_AUDIT_PRESERVATION_RESULT_LEDGER_2026-05-17.jsonl"
RECHECK_RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_RESULT_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
FAMILY_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local unified system action-result bundle. It consumes every unified work-order row into a concrete "
    "action result: default-off code/spec materialization, source/control repair action, score-with-control row, "
    "redesign variant action, guard registration, current-claim audit preservation, or recheck action. It does not "
    "change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
)

ACTION_FAMILY_OUTPUTS = {
    "IMPLEMENTATION_RESULT": IMPLEMENTATION_RESULT_LEDGER,
    "SOURCE_CONTROL_REPAIR_RESULT": SOURCE_CONTROL_RESULT_LEDGER,
    "SCORE_WITH_CONTROL_RESULT": SCORE_WITH_CONTROL_RESULT_LEDGER,
    "REDESIGN_EXECUTION_RESULT": REDESIGN_RESULT_LEDGER,
    "GUARD_RESULT": GUARD_RESULT_LEDGER,
    "AUDIT_PRESERVATION_RESULT": AUDIT_RESULT_LEDGER,
    "RECHECK_RESULT": RECHECK_RESULT_LEDGER,
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


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-ACTION-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
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
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def matrix_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("symbol") or "SYSTEM_LEVEL"),
        str(row.get("route_session") or "ALL_SESSIONS"),
        str(row.get("horizon_id") or "ALL_HORIZONS"),
        str(row.get("source_component") or "unknown_component"),
        str(row.get("primitive_flag") or "ALL_PRIMITIVES"),
    )


def build_market_lookup(market_rows: list[dict[str, Any]]) -> dict[tuple[str, str, str, str, str], dict[str, Any]]:
    lookup = {}
    for row in market_rows:
        if row.get("coverage_source") != "work_order_scope_consumed_from_unified_rows":
            continue
        lookup[matrix_key(row)] = row
    return lookup


def build_rollups(
    action_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in action_rows:
        by_scope[
            (
                row.get("symbol"),
                row.get("route_session"),
                row.get("horizon_id"),
                row.get("source_component"),
                row.get("action_result_family"),
            )
        ].append(row)
        by_family[
            (
                row.get("action_result_family"),
                row.get("action_execution_status"),
                row.get("next_concrete_builder"),
            )
        ].append(row)
    scope_rows = []
    for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1):
        scope_rows.append(with_common(action_result_rollup(key, by_scope[key], index, "scope_action"), generated_at, manifest_hash))
    family_rows = []
    for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1):
        family_rows.append(with_common(action_result_rollup(key, by_family[key], index, "family_status_builder"), generated_at, manifest_hash))
    return scope_rows, family_rows


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True}
            )
    manifest["latest_branch_local_unified_system_action_result_bundle"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "branch_local_unified_system_action_results_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed every work-order row into branch-local action result rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [WORK_ORDER_RESULT_PATH, WORK_ORDER_LEDGER, MARKET_EXPANSION_LEDGER, HELPER_MODULE, BUILDER_MODULE, VERIFIER_MODULE, TEST_MODULE],
        generated_at,
    )
    work_order_result = read_json(WORK_ORDER_RESULT_PATH)
    work_orders = read_jsonl(WORK_ORDER_LEDGER)
    market_rows = read_jsonl(MARKET_EXPANSION_LEDGER)
    market_lookup = build_market_lookup(market_rows)
    action_rows = [
        with_common(action_result_from_work_order(row, index, market_lookup.get(matrix_key(row))), generated_at, manifest_hash)
        for index, row in enumerate(work_orders, 1)
    ]
    by_family = {
        family: [row for row in action_rows if row.get("action_result_family") == family]
        for family in ACTION_FAMILY_OUTPUTS
    }
    scope_rollups, family_rollups = build_rollups(action_rows, generated_at, manifest_hash)
    distributions = {
        "action_result_family": string_counter(action_rows, "action_result_family"),
        "action_execution_status": string_counter(action_rows, "action_execution_status"),
        "proxy_r_style_result": string_counter(action_rows, "proxy_r_style_result"),
        "next_concrete_builder": string_counter(action_rows, "next_concrete_builder"),
        "source_component": string_counter(action_rows, "source_component"),
        "market_expansion_decision": string_counter(action_rows, "market_expansion_decision"),
    }
    component_action_counter = Counter(
        f"{row.get('source_component')}|{row.get('action_result_family')}|{row.get('action_execution_status')}"
        for row in action_rows
    )
    distributions["source_component_action_status"] = {
        key: int(component_action_counter[key]) for key in sorted(component_action_counter)
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-ACTION-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    questions = [
        "Did every work-order row become an action result row?",
        "Which implementation work orders are materialized as default-off code/spec candidates?",
        "Which source/control rows are exact-control builds, source repairs, or satisfied-source replay attachments?",
        "Which score-with-control rows are ready for computed deltas versus still control-required?",
        "Which no-fill redesign rows are avoid/inverse, retest, offset, market-entry, or family-split actions?",
        "Which guard rows are denominator guards versus source-confidence/context guards?",
        "Which current-claim rejection rows preserve mechanism opportunity instead of deleting it?",
        "Which action rows remain blocked by exact broker R versus computable proxy/control evidence?",
        "Which market/timeframe/session/horizon decisions are attached to action rows?",
        "What concrete scorer/source/redesign builder should consume this action-result packet next?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-ACTION-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by action-result, family, rollup, bucket, and market-expansion joined ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    counts = {
        "input_work_order_rows": len(work_orders),
        "input_market_expansion_rows": len(market_rows),
        "action_result_rows": len(action_rows),
        "implementation_result_rows": len(by_family["IMPLEMENTATION_RESULT"]),
        "source_control_repair_result_rows": len(by_family["SOURCE_CONTROL_REPAIR_RESULT"]),
        "score_with_control_result_rows": len(by_family["SCORE_WITH_CONTROL_RESULT"]),
        "redesign_execution_result_rows": len(by_family["REDESIGN_EXECUTION_RESULT"]),
        "guard_result_rows": len(by_family["GUARD_RESULT"]),
        "audit_preservation_result_rows": len(by_family["AUDIT_PRESERVATION_RESULT"]),
        "recheck_result_rows": len(by_family["RECHECK_RESULT"]),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    all_rows_consumed = len(action_rows) == len(work_orders) == work_order_result["counts"]["work_order_rows"]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_work_order_rows_consumed": all_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "action_result_family_counts": distributions["action_result_family"],
            "action_execution_status_counts": distributions["action_execution_status"],
            "proxy_r_style_result_counts": distributions["proxy_r_style_result"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_ACTION_RESULT_BUNDLE_RESULT: consume these action results into computed score deltas, exact-control/source repair rows, no-fill redesign scoring, guard registry specs, and branch-local default-off code candidates next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_action_result_surface": UNIFIED_SYSTEM_ACTION_RESULT_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_work_order_rows_consumed": all_rows_consumed,
        "action_result_family_counts": distributions["action_result_family"],
    }

    write_jsonl(ACTION_RESULT_LEDGER, action_rows)
    for family, path in ACTION_FAMILY_OUTPUTS.items():
        write_jsonl(path, by_family[family])
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollups)
    write_jsonl(FAMILY_ROLLUP_LEDGER, family_rollups)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Unified System Action Result Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Action result rows: `{counts['action_result_rows']}`.",
                f"- Implementation result rows: `{counts['implementation_result_rows']}`.",
                f"- Source/control repair result rows: `{counts['source_control_repair_result_rows']}`.",
                f"- Redesign execution result rows: `{counts['redesign_execution_result_rows']}`.",
                f"- Guard result rows: `{counts['guard_result_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        RUNTIME_SPEC_PATH,
        ACTION_RESULT_LEDGER,
        *ACTION_FAMILY_OUTPUTS.values(),
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
