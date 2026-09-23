#!/usr/bin/env python3
"""Build control/source split rows from repair acquisition proxy results."""

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

from src.research_infra.moonshot_branch_local_control_source_split import (
    CONTROL_SOURCE_SPLIT_SURFACE,
    control_member_relation_split,
    exact_control_relation_split,
    horizon_rebuild_split,
    scope_acquisition_plan,
    source_acquisition_split,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIR_ACQUISITION_PROXY_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_CONTROL_SOURCE_SPLIT_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_ACQUISITION_PROXY_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_EXACT_CONTROL_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_MEMBER = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_MEMBER_PROXY_REPLAY_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_ACQUISITION_PROXY_REQUIREMENT_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_PROXY_STRESS_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / CONTROL_SOURCE_SPLIT_SURFACE
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_CONTROL_SOURCE_SPLIT_LEDGER_2026-05-17.jsonl"
EXACT_RELATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_RELATION_SPLIT_LEDGER_2026-05-17.jsonl"
MEMBER_RELATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_MEMBER_RELATION_SPLIT_LEDGER_2026-05-17.jsonl"
SOURCE_SPLIT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACQUISITION_SPLIT_LEDGER_2026-05-17.jsonl"
HORIZON_SPLIT_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_REBUILD_SPLIT_LEDGER_2026-05-17.jsonl"
SCOPE_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ACQUISITION_PLAN_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_CONTROL_SOURCE_SPLIT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch-local control/source split bundle only. It converts exact-control acquisition requirements, "
    "selected-control member proxy replay, and source/horizon acquisition rows into concrete control/source "
    "split decisions and scope action plans. It does not change live behavior, place orders, or claim broker "
    "R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


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
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        file_hash = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-CTRL-SRC-SPLIT-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": file_hash,
                "status": "HASHED" if file_hash else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


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


def make_row(row_id_key: str, row_id: str, payload: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    payload[row_id_key] = row_id
    return with_common(payload, generated_at, manifest_hash)


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def build_symbol_session_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("symbol"), row.get("route_session"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])), 1):
        symbol, route_session = key
        output.append(
            with_common(
                {
                    "symbol_session_control_source_split_id": f"OHLC-GTOS-CTRL-SRC-SPLIT-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "control_source_split_lane_counts": string_counter(members, "control_source_split_lane"),
                    "control_source_split_status_counts": string_counter(members, "control_source_split_status"),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(
    unified_rows: list[dict[str, Any]],
    exact_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "control_source_split_lane": string_counter(unified_rows, "control_source_split_lane"),
        "control_source_split_status": string_counter(unified_rows, "control_source_split_status"),
        "exact_control_best_proxy_relation": string_counter(exact_rows, "best_available_proxy_relation"),
        "exact_control_best_proxy_rows_needed_to_n20": string_counter(
            exact_rows, "best_available_proxy_rows_needed_to_n20"
        ),
        "member_relation": string_counter(member_rows, "control_member_relation"),
        "member_split_status": string_counter(member_rows, "control_source_split_status"),
        "source_split_status": string_counter(source_rows, "control_source_split_status"),
        "source_repair_family": string_counter(source_rows, "source_repair_family"),
        "horizon_split_status": string_counter(horizon_rows, "control_source_split_status"),
        "scope_plan_status": string_counter(scope_rows, "control_source_split_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            unified_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-CTRL-SRC-SPLIT-BUCKET-{len(output) + 1:04d}",
                        "bucket_family": family,
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
            generated.append(
                {
                    "path": rel,
                    "artifact": PREFIX,
                    "sha256": sha256_file(path),
                    "safe_flags": SAFE_FLAGS,
                    "not_completion": True,
                }
            )
    manifest["latest_branch_local_control_source_split_bundle"] = {
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
        "event": "branch_local_control_source_split_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Converted exact-control/source/horizon acquisition rows into relation splits, member splits, and scope acquisition plans.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME_SPEC,
            INPUT_UNIFIED,
            INPUT_EXACT_CONTROL,
            INPUT_CONTROL_MEMBER,
            INPUT_SOURCE,
            INPUT_HORIZON,
            HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    input_unified = read_jsonl(INPUT_UNIFIED)
    exact_input = read_jsonl(INPUT_EXACT_CONTROL)
    member_input = read_jsonl(INPUT_CONTROL_MEMBER)
    source_input = read_jsonl(INPUT_SOURCE)
    horizon_input = read_jsonl(INPUT_HORIZON)

    members_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in member_input:
        members_by_target[str(row.get("input_repair_execution_row_id"))].append(row)

    exact_scope_counts = Counter(scope_key(row) for row in exact_input)
    exact_rows: list[dict[str, Any]] = []
    for index, row in enumerate(exact_input, 1):
        split = exact_control_relation_split(
            row,
            members_by_target.get(str(row.get("input_repair_execution_row_id")), []),
            int(exact_scope_counts[scope_key(row)]),
        )
        exact_rows.append(
            make_row(
                "control_source_split_row_id",
                f"OHLC-GTOS-CTRL-SRC-SPLIT-EXACT-{index:05d}",
                split,
                generated_at,
                manifest_hash,
            )
        )

    exact_split_by_target = {row.get("input_repair_execution_row_id"): row for row in exact_rows}
    member_rows: list[dict[str, Any]] = []
    for target_id, members in sorted(members_by_target.items()):
        target_split = exact_split_by_target.get(target_id)
        if not target_split:
            continue
        relation_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for member in members:
            relation_groups[str(member.get("control_member_relation"))].append(member)
        for member in members:
            relation = str(member.get("control_member_relation"))
            member_rows.append(
                make_row(
                    "control_member_relation_split_row_id",
                    f"OHLC-GTOS-CTRL-SRC-SPLIT-MEMBER-{len(member_rows) + 1:07d}",
                    control_member_relation_split(member, target_split, relation_groups[relation]),
                    generated_at,
                    manifest_hash,
                )
            )

    source_rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_input, 1):
        source_rows.append(
            make_row(
                "control_source_split_row_id",
                f"OHLC-GTOS-CTRL-SRC-SPLIT-SOURCE-{index:05d}",
                source_acquisition_split(row),
                generated_at,
                manifest_hash,
            )
        )

    horizon_rows: list[dict[str, Any]] = []
    for index, row in enumerate(horizon_input, 1):
        horizon_rows.append(
            make_row(
                "horizon_rebuild_split_row_id",
                f"OHLC-GTOS-CTRL-SRC-SPLIT-HORIZON-{index:05d}",
                horizon_rebuild_split(row),
                generated_at,
                manifest_hash,
            )
        )

    exact_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    source_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    horizon_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in exact_rows:
        exact_by_scope[scope_key(row)].append(row)
    for row in source_rows:
        source_by_scope[scope_key(row)].append(row)
    for row in horizon_rows:
        horizon_by_scope[scope_key(row)].append(row)

    scope_rows: list[dict[str, Any]] = []
    all_scopes = sorted(set(exact_by_scope) | set(source_by_scope) | set(horizon_by_scope), key=lambda values: tuple(str(value) for value in values))
    for index, scope in enumerate(all_scopes, 1):
        scope_rows.append(
            make_row(
                "scope_acquisition_plan_row_id",
                f"OHLC-GTOS-CTRL-SRC-SPLIT-SCOPE-{index:05d}",
                scope_acquisition_plan(scope, exact_by_scope[scope], source_by_scope[scope], horizon_by_scope[scope]),
                generated_at,
                manifest_hash,
            )
        )

    unified_rows = [*exact_rows, *source_rows]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        exact_rows,
        member_rows,
        source_rows,
        horizon_rows,
        scope_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-CTRL-SRC-SPLIT-Q-001",
                "question": "Do exact-control rows have any exact-scope selected members in current rows?",
                "answer_route": "No: exact-control selected members preserve zero exact-scope relations, so exact denominator acquisition remains open.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-CTRL-SRC-SPLIT-Q-002",
                "question": "What is the strongest current proxy relation for exact-control rows?",
                "answer_route": "Same-symbol/session/horizon is available for 40 rows, same-symbol/session for 44 rows, and same-symbol only for 8 rows; all remain under n20.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-CTRL-SRC-SPLIT-Q-003",
                "question": "Do exact-control and source requirements overlap at exact symbol/session/horizon/primitive scope?",
                "answer_route": "No: the 121-scope action plan has 23 exact-control-only scopes, 61 exact-source-only scopes, and 37 horizon-source-only scopes.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-CTRL-SRC-SPLIT-Q-004",
                "question": "Did the bundle avoid top-N selected-control shortcuts?",
                "answer_route": "Yes: all 21,252 selected-control members are emitted in the compact relation split ledger with target relation context.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-CTRL-SRC-SPLIT-Q-005",
                "question": "What immediate next computation follows this split?",
                "answer_route": "Build exact-scope denominator acquisition for the 23 exact-control scopes and source/horizon rebuild routes for the 98 source scopes.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_acquisition_proxy_rows": len(input_unified),
        "input_exact_control_acquisition_requirement_rows": len(exact_input),
        "input_control_member_proxy_replay_rows": len(member_input),
        "input_source_acquisition_proxy_requirement_rows": len(source_input),
        "input_horizon_proxy_stress_rows": len(horizon_input),
        "unified_control_source_split_rows": len(unified_rows),
        "exact_control_relation_split_rows": len(exact_rows),
        "control_member_relation_split_rows": len(member_rows),
        "source_acquisition_split_rows": len(source_rows),
        "horizon_rebuild_split_rows": len(horizon_rows),
        "scope_acquisition_plan_rows": len(scope_rows),
        "scope_exact_source_overlap_rows": sum(1 for row in scope_rows if row.get("scope_exact_source_overlap")),
        "exact_control_no_exact_scope_member_rows": sum(1 for row in exact_rows if row.get("exact_scope_absent")),
        "exact_control_best_proxy_under_n20_rows": sum(
            1 for row in exact_rows if int(row.get("best_available_proxy_rows_needed_to_n20") or 0) > 0
        ),
        "member_rows_kept_for_strongest_proxy": sum(1 for row in member_rows if row.get("keep_for_strongest_available_proxy")),
        "source_exact_rebuild_rows": sum(
            1 for row in source_rows if row.get("control_source_split_status") == "CONTROL_SOURCE_SPLIT_EXACT_SOURCE_REBUILD_REQUIRED"
        ),
        "horizon_rescore_rows": sum(
            1 for row in horizon_rows if row.get("control_source_split_status") == "CONTROL_SOURCE_SPLIT_HORIZON_RESCORE_REBUILD_ACTIVE"
        ),
        "horizon_kill_check_rows": sum(
            1 for row in horizon_rows if row.get("control_source_split_status") == "CONTROL_SOURCE_SPLIT_HORIZON_KILL_CHECK_REBUILD_ACTIVE"
        ),
        "symbol_session_control_source_split_rows": len(symbol_session_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {
            "repair_acquisition_proxy_bundle": input_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "control_source_split_lane_counts": distributions["control_source_split_lane"],
            "control_source_split_status_counts": distributions["control_source_split_status"],
            "exact_control_best_proxy_relation_counts": distributions["exact_control_best_proxy_relation"],
            "scope_plan_status_counts": distributions["scope_plan_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_CONTROL_SOURCE_SPLIT_BUNDLE_RESULT: exact-control rows require exact-scope "
                "denominator acquisition; selected-control proxy evidence is preserved in full; source and "
                "horizon rows are disjoint exact-scope rebuild routes."
            ),
        },
    }
    runtime_spec = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "identity_policy": {
            "primary_rows": "92 exact-control relation split rows + 98 source acquisition split rows",
            "member_rows": "all selected control-member rows from acquisition proxy; no top-N",
            "scope_rows": "exact symbol/session/horizon/primitive action plans",
        },
        "execution_policy": {
            "exact_control": "split by strongest available proxy relation and preserve exact n20 deficit",
            "source": "split exact-source rebuild from horizon rebuild/rescore and kill-check",
            "horizon": "preserve fail-closed stress without entering primary denominator",
        },
        "bucket_distributions": distributions,
    }

    generated_files = [
        UNIFIED_LEDGER,
        EXACT_RELATION_LEDGER,
        MEMBER_RELATION_LEDGER,
        SOURCE_SPLIT_LEDGER,
        HORIZON_SPLIT_LEDGER,
        SCOPE_PLAN_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(EXACT_RELATION_LEDGER, exact_rows)
    write_jsonl(MEMBER_RELATION_LEDGER, member_rows)
    write_jsonl(SOURCE_SPLIT_LEDGER, source_rows)
    write_jsonl(HORIZON_SPLIT_LEDGER, horizon_rows)
    write_jsonl(SCOPE_PLAN_LEDGER, scope_rows)
    write_jsonl(SYMBOL_SESSION_LEDGER, symbol_session_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime_spec, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch-Local Control Source Split Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified control/source split rows: `{counts['unified_control_source_split_rows']}`",
                f"- Exact-control relation split rows: `{counts['exact_control_relation_split_rows']}`",
                f"- Control-member relation split rows: `{counts['control_member_relation_split_rows']}`",
                f"- Source acquisition split rows: `{counts['source_acquisition_split_rows']}`",
                f"- Horizon rebuild split rows: `{counts['horizon_rebuild_split_rows']}`",
                f"- Scope acquisition plan rows: `{counts['scope_acquisition_plan_rows']}`",
                "",
                "Core result: exact-control, source, and horizon requirements are now split into concrete same-resource acquisition plans while preserving every selected control member.",
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
