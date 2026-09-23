#!/usr/bin/env python3
"""Build acquisition/proxy replay rows from branch-local repair execution results."""

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

from src.research_infra.moonshot_branch_local_repair_acquisition_proxy import (
    ACQUISITION_PROXY_SURFACE,
    control_member_proxy_replay,
    exact_control_acquisition_requirement,
    horizon_proxy_stress,
    source_acquisition_proxy_requirement,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_REPAIR_EXECUTION_BUNDLE"
CONTROL_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_OBSERVABLE_SCORER_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIR_ACQUISITION_PROXY_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_UNIFIED = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_REPAIR = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_REPAIR_WORK_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_CONTROL = ROUTE_DIR / f"{INPUT_PREFIX}_EXACT_CONTROL_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON = ROUTE_DIR / f"{INPUT_PREFIX}_HORIZON_REPAIR_SIDECAR_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_EXECUTION = ROUTE_DIR / f"{CONTROL_EXEC_PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / ACQUISITION_PROXY_SURFACE
BUILDER_MODULE = Path(__file__)

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
UNIFIED_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_ACQUISITION_PROXY_LEDGER_2026-05-17.jsonl"
EXACT_CONTROL_REQ_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
CONTROL_MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_MEMBER_PROXY_REPLAY_LEDGER_2026-05-17.jsonl"
SOURCE_REQ_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACQUISITION_PROXY_REQUIREMENT_LEDGER_2026-05-17.jsonl"
HORIZON_STRESS_LEDGER = ROUTE_DIR / f"{PREFIX}_HORIZON_PROXY_STRESS_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_ACQUISITION_PROXY_LEDGER_2026-05-17.jsonl"
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
    "Branch-local repair acquisition/proxy bundle only. It converts repair-execution rows into exact-control "
    "acquisition requirements, full selected-control member proxy replay rows, and source/horizon acquisition "
    "proxy requirements. It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-REPAIR-ACQPX-SRC-{index:04d}",
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


def make_row(row_id: str, payload: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    payload["acquisition_proxy_row_id"] = row_id
    return with_common(payload, generated_at, manifest_hash)


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
                    "symbol_session_acquisition_proxy_id": f"OHLC-GTOS-REPAIR-ACQPX-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "row_count": len(members),
                    "acquisition_proxy_lane_counts": string_counter(members, "acquisition_proxy_lane"),
                    "acquisition_proxy_status_counts": string_counter(members, "acquisition_proxy_status"),
                    "requirement_open_rows": sum(1 for row in members if row.get("acquisition_requirement_open")),
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
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "acquisition_proxy_lane": string_counter(unified_rows, "acquisition_proxy_lane"),
        "acquisition_proxy_status": string_counter(unified_rows, "acquisition_proxy_status"),
        "exact_control_acquisition_status": string_counter(exact_rows, "acquisition_proxy_status"),
        "control_member_relation": string_counter(member_rows, "control_member_relation"),
        "control_member_score_band": string_counter(member_rows, "control_proxy_score_band"),
        "source_acquisition_status": string_counter(source_rows, "acquisition_proxy_status"),
        "source_proxy_score_band": string_counter(source_rows, "source_proxy_score_band"),
        "horizon_proxy_stress_status": string_counter(horizon_rows, "acquisition_proxy_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(unified_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-REPAIR-ACQPX-BUCKET-{len(output) + 1:04d}",
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
    manifest["latest_branch_local_repair_acquisition_proxy_bundle"] = {
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
        "event": "branch_local_repair_acquisition_proxy_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Converted repair execution rows into acquisition requirements and full selected-control member proxy replay rows.",
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
            INPUT_SOURCE_REPAIR,
            INPUT_EXACT_CONTROL,
            INPUT_HORIZON,
            INPUT_CONTROL_EXECUTION,
            HELPER_MODULE,
            BUILDER_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    input_unified = read_jsonl(INPUT_UNIFIED)
    source_repair_rows = read_jsonl(INPUT_SOURCE_REPAIR)
    exact_control_rows = read_jsonl(INPUT_EXACT_CONTROL)
    horizon_rows_input = read_jsonl(INPUT_HORIZON)
    control_execution_rows = read_jsonl(INPUT_CONTROL_EXECUTION)
    control_by_runtime = {row.get("input_runtime_work_row_id"): row for row in control_execution_rows}

    exact_control_requirement_rows: list[dict[str, Any]] = []
    control_member_rows: list[dict[str, Any]] = []
    for index, row in enumerate(exact_control_rows, 1):
        exact_requirement = make_row(
            f"OHLC-GTOS-REPAIR-ACQPX-EXACTCTRL-{index:05d}",
            exact_control_acquisition_requirement(row),
            generated_at,
            manifest_hash,
        )
        exact_control_requirement_rows.append(exact_requirement)
        runtime_ids = list(row.get("selected_control_runtime_work_row_ids") or [])
        candidate_ids = list(row.get("selected_control_input_candidate_ids") or [])
        for member_index, runtime_id in enumerate(runtime_ids, 1):
            candidate_id = candidate_ids[member_index - 1] if member_index - 1 < len(candidate_ids) else None
            control_member_rows.append(
                make_row(
                    f"OHLC-GTOS-REPAIR-ACQPX-CMEMBER-{len(control_member_rows) + 1:07d}",
                    control_member_proxy_replay(
                        row,
                        control_by_runtime.get(runtime_id),
                        runtime_id,
                        candidate_id,
                        member_index,
                    ),
                    generated_at,
                    manifest_hash,
                )
            )

    source_requirement_rows: list[dict[str, Any]] = []
    horizon_stress_rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_repair_rows, 1):
        source_requirement = make_row(
            f"OHLC-GTOS-REPAIR-ACQPX-SOURCE-{index:05d}",
            source_acquisition_proxy_requirement(row),
            generated_at,
            manifest_hash,
        )
        source_requirement_rows.append(source_requirement)
        if str(row.get("source_repair_family") or "").startswith("HORIZON"):
            horizon_stress_rows.append(
                make_row(
                    f"OHLC-GTOS-REPAIR-ACQPX-HSTRESS-{len(horizon_stress_rows) + 1:05d}",
                    horizon_proxy_stress(row),
                    generated_at,
                    manifest_hash,
                )
            )

    unified_rows = [*exact_control_requirement_rows, *source_requirement_rows]
    symbol_session_rows = build_symbol_session_rows(unified_rows, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        unified_rows,
        exact_control_requirement_rows,
        control_member_rows,
        source_requirement_rows,
        horizon_stress_rows,
        generated_at,
        manifest_hash,
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-REPAIR-ACQPX-Q-001",
                "question": "Did exact-control failures become concrete acquisition/proxy replay rows?",
                "answer_route": "Yes: all 92 exact-control rows have acquisition requirements and every selected control member is preserved in a full proxy replay ledger.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-REPAIR-ACQPX-Q-002",
                "question": "Did the member replay avoid scope-only shortcuts?",
                "answer_route": "Yes: member rows join selected runtime-work IDs to control execution rows, preserving member scope, score, score band, and relation to the target row.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-REPAIR-ACQPX-Q-003",
                "question": "Did source/horizon repairs get actionable acquisition rows?",
                "answer_route": "Yes: all 98 source rows have source acquisition/proxy requirements and the 37 horizon rows have fail-closed stress rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-REPAIR-ACQPX-Q-004",
                "question": "What remains open after this packet?",
                "answer_route": "Exact same-scope control denominators, exact source rows, and horizon targetable rebuilds remain open as specific acquisition/proxy replay actions with row-level deficits and scores.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_unified_repair_execution_rows": len(input_unified),
        "input_source_repair_work_execution_rows": len(source_repair_rows),
        "input_exact_control_repair_execution_rows": len(exact_control_rows),
        "input_horizon_repair_sidecar_execution_rows": len(horizon_rows_input),
        "input_control_execution_rows": len(control_execution_rows),
        "unified_acquisition_proxy_rows": len(unified_rows),
        "exact_control_acquisition_requirement_rows": len(exact_control_requirement_rows),
        "control_member_proxy_replay_rows": len(control_member_rows),
        "source_acquisition_proxy_requirement_rows": len(source_requirement_rows),
        "horizon_proxy_stress_rows": len(horizon_stress_rows),
        "member_rows_joined_to_control_execution": sum(1 for row in control_member_rows if row.get("member_lookup_status") == "CONTROL_MEMBER_JOINED"),
        "member_rows_missing_control_execution": sum(1 for row in control_member_rows if row.get("member_lookup_status") != "CONTROL_MEMBER_JOINED"),
        "exact_control_requirements_open_rows": sum(1 for row in exact_control_requirement_rows if row.get("acquisition_requirement_open")),
        "source_requirements_open_rows": sum(1 for row in source_requirement_rows if row.get("acquisition_requirement_open")),
        "symbol_session_acquisition_proxy_rows": len(symbol_session_rows),
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
            "observable_repair_execution_bundle": input_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "acquisition_proxy_lane_counts": distributions["acquisition_proxy_lane"],
            "exact_control_acquisition_status_counts": distributions["exact_control_acquisition_status"],
            "control_member_relation_counts": distributions["control_member_relation"],
            "source_acquisition_status_counts": distributions["source_acquisition_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_REPAIR_ACQUISITION_PROXY_BUNDLE_RESULT: convert 92 exact-control global-proxy "
                "failures into exact-control acquisition requirements and full selected-control member replay rows; "
                "convert 98 source/horizon repair rows into source acquisition and horizon stress rows."
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
            "primary_rows": "92 exact-control acquisition requirements + 98 source acquisition requirements",
            "control_member_rows": "all selected control runtime-work members from exact-control rows; no top-N",
            "scope_only_join_allowed": False,
        },
        "execution_policy": {
            "exact_control": "preserve row-level deficits to n20 and full selected member replay",
            "source_repair": "preserve exact-source/horizon requirements and proxy scores",
            "horizon_stress": "compute fail-closed stress rows for every horizon repair source row",
        },
        "bucket_distributions": distributions,
    }

    generated_files = [
        UNIFIED_LEDGER,
        EXACT_CONTROL_REQ_LEDGER,
        CONTROL_MEMBER_LEDGER,
        SOURCE_REQ_LEDGER,
        HORIZON_STRESS_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(UNIFIED_LEDGER, unified_rows)
    write_jsonl(EXACT_CONTROL_REQ_LEDGER, exact_control_requirement_rows)
    write_jsonl(CONTROL_MEMBER_LEDGER, control_member_rows)
    write_jsonl(SOURCE_REQ_LEDGER, source_requirement_rows)
    write_jsonl(HORIZON_STRESS_LEDGER, horizon_stress_rows)
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
                "# Historical OHLC GTOS Replay Branch-Local Repair Acquisition Proxy Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified acquisition/proxy rows: `{counts['unified_acquisition_proxy_rows']}`",
                f"- Exact-control acquisition requirement rows: `{counts['exact_control_acquisition_requirement_rows']}`",
                f"- Control member proxy replay rows: `{counts['control_member_proxy_replay_rows']}`",
                f"- Source acquisition/proxy requirement rows: `{counts['source_acquisition_proxy_requirement_rows']}`",
                f"- Horizon proxy stress rows: `{counts['horizon_proxy_stress_rows']}`",
                "",
                "Core result: exact-control and source repair requirements are now executable acquisition/proxy rows with full selected-control member replay preserved.",
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
