#!/usr/bin/env python3
"""Resolve denominator/source acquisition-execution rows into concrete decisions."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_branch_local_denominator_source_resolution import (
    acquisition_requirement_resolution,
    exact_control_scope_resolution,
    exact_control_target_resolution,
    horizon_resolution,
    implementation_resolution,
    next_compute_action,
    source_resolution,
)


CLAIM_BOUNDARY = (
    "Branch-local denominator/source resolution bundle only. It converts acquisition-execution rows into "
    "implementation/build/kill/repair/redesign decisions and next same-resource compute actions. It does "
    "not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, "
    "validation, live-readiness, or promotion."
)
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
ACQ_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_BUNDLE"
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACTION_CANDIDATE_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_RESOLUTION_BUNDLE"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_UTC = utc_now()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(io_path(path).read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not io_path(path).exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in io_path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    io_path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    io_path(path).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with io_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def io_path(path: Path) -> Path:
    absolute = path.resolve()
    text = str(absolute)
    if sys.platform.startswith("win") and not text.startswith("\\\\?\\"):
        return Path("\\\\?\\" + text)
    return absolute


def split_scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        Path("src/research_infra/moonshot_branch_local_denominator_source_resolution.py"),
        Path(
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/"
            "build_branch_local_denominator_source_resolution_2026_05_17.py"
        ),
        Path(
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/"
            "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
        ),
        Path("tests/research_infra/test_moonshot_unified_execution_scorer.py"),
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_RESULT_2026-05-17.json",
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_RUNTIME_SPEC_2026-05-17.json",
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_UNIFIED_ACQUISITION_EXECUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_EXACT_CONTROL_TARGET_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_EXACT_CONTROL_SCOPE_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_SOURCE_EXACT_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_HORIZON_REPAIR_RESCORE_EXECUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{ACQ_PREFIX}_ACQUISITION_REQUIREMENT_EXECUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{ACTION_PREFIX}_RESULT_2026-05-17.json",
        ROUTE_DIR.relative_to(REPO) / f"{ACTION_PREFIX}_RUNTIME_SPEC_2026-05-17.json",
        ROUTE_DIR.relative_to(REPO) / f"{ACTION_PREFIX}_UNIFIED_ACTION_CANDIDATE_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{ACTION_PREFIX}_EXACT_CONTROL_SCOPE_ACTION_LEDGER_2026-05-17.jsonl",
    ]
    manifest_rows: list[dict[str, Any]] = []
    for index, rel_path in enumerate(paths, 1):
        abs_path = REPO / rel_path
        manifest_rows.append(
            {
                "source_manifest_row_id": f"OHLC-GTOS-DENOM-SRC-RES-MANIFEST-{index:04d}",
                "path": str(rel_path).replace("\\", "/"),
                "sha256": sha256_file(abs_path) if io_path(abs_path).exists() else None,
                "status": "HASHED" if io_path(abs_path).exists() else "MISSING",
                "generated_utc": GENERATED_UTC,
                "safe_flags": SAFE_FLAGS,
                "not_completion": True,
                "live_effect": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


SOURCE_MANIFEST_ROWS, SOURCE_MANIFEST_HASH = source_manifest()


def finalize(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "generated_utc": GENERATED_UTC,
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "live_effect": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_manifest_hash": SOURCE_MANIFEST_HASH,
    }


def add_ids(rows: list[dict[str, Any]], prefix: str, id_field: str) -> list[dict[str, Any]]:
    return [finalize({id_field: f"{prefix}-{idx:05d}", **row}) for idx, row in enumerate(rows, 1)]


def string_counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field)) for row in rows).items()))


def bucket_rows(distributions: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for family in sorted(distributions):
        for value, count in sorted(distributions[family].items()):
            rows.append(
                finalize(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-SRC-RES-BUCKET-{index:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": int(count),
                    }
                )
            )
            index += 1
    return rows


def main() -> None:
    acq_result = read_json(ROUTE_DIR / f"{ACQ_PREFIX}_RESULT_2026-05-17.json")
    action_result = read_json(ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json")
    acq_unified = read_jsonl(ROUTE_DIR / f"{ACQ_PREFIX}_UNIFIED_ACQUISITION_EXECUTION_LEDGER_2026-05-17.jsonl")
    acq_targets = read_jsonl(
        ROUTE_DIR / f"{ACQ_PREFIX}_EXACT_CONTROL_TARGET_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
    )
    acq_scopes = read_jsonl(
        ROUTE_DIR / f"{ACQ_PREFIX}_EXACT_CONTROL_SCOPE_BUILD_EXECUTION_LEDGER_2026-05-17.jsonl"
    )
    acq_sources = read_jsonl(ROUTE_DIR / f"{ACQ_PREFIX}_SOURCE_EXACT_REBUILD_EXECUTION_LEDGER_2026-05-17.jsonl")
    acq_horizons = read_jsonl(ROUTE_DIR / f"{ACQ_PREFIX}_HORIZON_REPAIR_RESCORE_EXECUTION_LEDGER_2026-05-17.jsonl")
    acq_requirements = read_jsonl(
        ROUTE_DIR / f"{ACQ_PREFIX}_ACQUISITION_REQUIREMENT_EXECUTION_LEDGER_2026-05-17.jsonl"
    )

    target_resolutions_raw = [exact_control_target_resolution(row) for row in acq_targets]
    target_resolutions = add_ids(
        target_resolutions_raw,
        "OHLC-GTOS-DENOM-SRC-RES-TARGET",
        "denominator_source_resolution_row_id",
    )
    targets_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = {}
    for row in target_resolutions:
        targets_by_scope.setdefault(split_scope_key(row), []).append(row)

    scope_resolutions = add_ids(
        [exact_control_scope_resolution(row, targets_by_scope.get(split_scope_key(row), [])) for row in acq_scopes],
        "OHLC-GTOS-DENOM-SRC-RES-SCOPE",
        "denominator_source_resolution_row_id",
    )
    source_resolutions = add_ids(
        [source_resolution(row) for row in acq_sources],
        "OHLC-GTOS-DENOM-SRC-RES-SOURCE",
        "denominator_source_resolution_row_id",
    )
    horizon_resolutions = add_ids(
        [horizon_resolution(row) for row in acq_horizons],
        "OHLC-GTOS-DENOM-SRC-RES-HORIZON",
        "denominator_source_resolution_row_id",
    )
    primary_resolutions = [*target_resolutions, *source_resolutions, *horizon_resolutions]
    implementation_decisions = add_ids(
        [implementation_resolution(row) for row in [*primary_resolutions, *scope_resolutions]],
        "OHLC-GTOS-DENOM-SRC-RES-IMPL",
        "implementation_resolution_row_id",
    )
    next_actions_raw = [
        action
        for action in (next_compute_action(row) for row in [*primary_resolutions, *scope_resolutions])
        if action is not None
    ]
    next_actions = add_ids(
        next_actions_raw,
        "OHLC-GTOS-DENOM-SRC-RES-NEXT",
        "next_compute_action_row_id",
    )
    resolved_by_action = {
        row.get("input_action_candidate_row_id"): row
        for row in [*target_resolutions, *source_resolutions, *horizon_resolutions]
    }
    acquisition_requirement_resolutions = add_ids(
        [
            acquisition_requirement_resolution(row, resolved_by_action.get(row.get("input_action_candidate_row_id")))
            for row in acq_requirements
        ],
        "OHLC-GTOS-DENOM-SRC-RES-REQ",
        "acquisition_requirement_resolution_row_id",
    )
    terminal_kills = add_ids(
        [
            row
            for row in [*source_resolutions, *horizon_resolutions]
            if row.get("candidate_implementation_state") in {"SOURCE_PROXY_KILLED", "HORIZON_KILLED"}
        ],
        "OHLC-GTOS-DENOM-SRC-RES-KILL",
        "terminal_kill_row_id",
    )
    guarded_candidates = add_ids(
        [
            row
            for row in scope_resolutions
            if row.get("candidate_implementation_state") == "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE"
        ],
        "OHLC-GTOS-DENOM-SRC-RES-GUARD",
        "guarded_candidate_row_id",
    )

    symbol_session_rows: list[dict[str, Any]] = []
    for index, ((symbol, session), rows) in enumerate(
        sorted(
            {
                key: [row for row in primary_resolutions if (row.get("symbol"), row.get("route_session")) == key]
                for key in {(row.get("symbol"), row.get("route_session")) for row in primary_resolutions}
            }.items()
        ),
        1,
    ):
        symbol_session_rows.append(
            finalize(
                {
                    "symbol_session_resolution_row_id": f"OHLC-GTOS-DENOM-SRC-RES-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": session,
                    "row_count": len(rows),
                    "terminal_kill_rows": sum(1 for row in rows if row.get("terminal_decision")),
                    "next_action_rows": sum(
                        1 for row in rows if row.get("candidate_implementation_state") != "HORIZON_KILLED"
                    ),
                    "outside_gbpjpy_xauusd_current_branch_box_rows": sum(
                        1 for row in rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
                    ),
                }
            )
        )

    distributions = {
        "denominator_source_resolution_lane": string_counter(primary_resolutions, "denominator_source_resolution_lane"),
        "denominator_source_resolution_status": string_counter(
            primary_resolutions, "denominator_source_resolution_status"
        ),
        "scope_resolution_status": string_counter(scope_resolutions, "denominator_source_resolution_status"),
        "candidate_implementation_state": string_counter(
            [*primary_resolutions, *scope_resolutions], "candidate_implementation_state"
        ),
        "implementation_resolution_status": string_counter(
            implementation_decisions, "implementation_resolution_status"
        ),
        "acquisition_requirement_resolution_status": string_counter(
            acquisition_requirement_resolutions, "denominator_source_resolution_status"
        ),
        "keep_kill_redesign_decision": string_counter(
            [*primary_resolutions, *scope_resolutions], "keep_kill_redesign_decision"
        ),
        "next_same_resource_action": string_counter(next_actions, "next_same_resource_action"),
        "terminal_kill_state": string_counter(terminal_kills, "candidate_implementation_state"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            primary_resolutions, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    buckets = bucket_rows(distributions)
    questions = [
        finalize(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-RES-Q-0001",
                "question": "Which rows are usable immediately after acquisition execution?",
                "answer_from_current_rows": "Only the 4 guarded exact-control scope proxies are implementation candidates now; all scalar target/source/horizon rows are build, repair, redesign, kill, or kill-check states.",
                "next_action": "materialize guarded proxy scorer specs and continue exact-control build actions",
            }
        ),
        finalize(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-RES-Q-0002",
                "question": "Which rows are terminal under current evidence?",
                "answer_from_current_rows": "61 source proxy candidates are killed pending exact-source contradiction routes, and 6 horizon rows are killed by negative repaired upper-bound evidence.",
                "next_action": "preserve killed rows as avoid/source-failure intelligence and continue source contradiction acquisition where available",
            }
        ),
        finalize(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-RES-Q-0003",
                "question": "Which rows need immediate computation instead of transfer-only bookkeeping?",
                "answer_from_current_rows": "207 next-action rows remain: exact-control target/scope builds, source contradiction checks, and horizon repair/redesign/kill-check rows.",
                "next_action": "execute guarded scorer materialization, exact-control build expansion, source contradiction acquisition, and horizon repair/redesign details",
            }
        ),
    ]

    counts = {
        "input_acquisition_unified_rows": len(acq_unified),
        "input_exact_control_target_build_rows": len(acq_targets),
        "input_exact_control_scope_build_rows": len(acq_scopes),
        "input_source_exact_rebuild_rows": len(acq_sources),
        "input_horizon_repair_rescore_rows": len(acq_horizons),
        "input_acquisition_requirement_execution_rows": len(acq_requirements),
        "primary_resolution_rows": len(primary_resolutions),
        "exact_control_target_resolution_rows": len(target_resolutions),
        "exact_control_scope_resolution_rows": len(scope_resolutions),
        "source_resolution_rows": len(source_resolutions),
        "horizon_resolution_rows": len(horizon_resolutions),
        "implementation_resolution_rows": len(implementation_decisions),
        "acquisition_requirement_resolution_rows": len(acquisition_requirement_resolutions),
        "next_compute_action_rows": len(next_actions),
        "terminal_kill_rows": len(terminal_kills),
        "guarded_implementation_candidate_rows": len(guarded_candidates),
        "symbol_session_resolution_rows": len(symbol_session_rows),
        "bucket_rows": len(buckets),
        "question_rows": len(questions),
        "source_manifest_rows": len(SOURCE_MANIFEST_ROWS),
        "runtime_spec_rows": 1,
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": GENERATED_UTC,
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "counts": counts,
        "upstream_counts": {
            "denominator_source_acquisition_execution_bundle": acq_result.get("counts", {}),
            "denominator_source_action_candidate_bundle": action_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "source_manifest_hash": SOURCE_MANIFEST_HASH,
        "system_decision": {
            "candidate_implementation_state_counts": distributions["candidate_implementation_state"],
            "implementation_resolution_status_counts": distributions["implementation_resolution_status"],
            "acquisition_requirement_resolution_status_counts": distributions[
                "acquisition_requirement_resolution_status"
            ],
            "next_same_resource_action_counts": distributions["next_same_resource_action"],
            "system_recommendation": (
                "BRANCH_LOCAL_DENOMINATOR_SOURCE_RESOLUTION_BUNDLE_RESULT: implement only guarded exact-control "
                "scope candidates now; keep source proxy kills out of implementation, execute source contradiction "
                "acquisition, exact-control denominator builds, and horizon repair/redesign/kill-check details."
            ),
        },
    }
    outputs = {
        f"{PREFIX}_PRIMARY_RESOLUTION_LEDGER_2026-05-17.jsonl": primary_resolutions,
        f"{PREFIX}_EXACT_CONTROL_TARGET_RESOLUTION_LEDGER_2026-05-17.jsonl": target_resolutions,
        f"{PREFIX}_EXACT_CONTROL_SCOPE_RESOLUTION_LEDGER_2026-05-17.jsonl": scope_resolutions,
        f"{PREFIX}_SOURCE_RESOLUTION_LEDGER_2026-05-17.jsonl": source_resolutions,
        f"{PREFIX}_HORIZON_RESOLUTION_LEDGER_2026-05-17.jsonl": horizon_resolutions,
        f"{PREFIX}_IMPLEMENTATION_RESOLUTION_LEDGER_2026-05-17.jsonl": implementation_decisions,
        f"{PREFIX}_ACQUISITION_REQUIREMENT_RESOLUTION_LEDGER_2026-05-17.jsonl": acquisition_requirement_resolutions,
        f"{PREFIX}_NEXT_COMPUTE_ACTION_LEDGER_2026-05-17.jsonl": next_actions,
        f"{PREFIX}_TERMINAL_KILL_LEDGER_2026-05-17.jsonl": terminal_kills,
        f"{PREFIX}_GUARDED_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl": guarded_candidates,
        f"{PREFIX}_SYMBOL_SESSION_RESOLUTION_LEDGER_2026-05-17.jsonl": symbol_session_rows,
        f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl": buckets,
        f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl": questions,
        f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl": [finalize(row) for row in SOURCE_MANIFEST_ROWS],
    }
    for filename, rows in outputs.items():
        write_jsonl(ROUTE_DIR / filename, rows)
    write_json(ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json", result)
    write_json(
        ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json",
        {
            "artifact": PREFIX,
            "generated_utc": GENERATED_UTC,
            "not_completion": True,
            "claim_boundary": CLAIM_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "input_artifacts": [ACQ_PREFIX, ACTION_PREFIX],
            "output_files": sorted([*outputs, f"{PREFIX}_RESULT_2026-05-17.json"]),
        },
    )
    (ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md").write_text(
        "\n".join(
            [
                "# Branch-Local Denominator Source Resolution Bundle",
                "",
                f"Generated UTC: `{GENERATED_UTC}`",
                "",
                f"- Primary resolution rows: `{len(primary_resolutions)}`.",
                f"- Implementation resolution rows: `{len(implementation_decisions)}`.",
                f"- Acquisition requirement resolution rows: `{len(acquisition_requirement_resolutions)}`.",
                f"- Guarded implementation candidates: `{len(guarded_candidates)}`.",
                f"- Terminal kill rows: `{len(terminal_kills)}`.",
                f"- Next compute action rows: `{len(next_actions)}`.",
                "- No live behavior, validation, promotion, broker R/PnL, win-rate, or expectancy claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_path = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
    manifest = read_json(manifest_path)
    manifest.setdefault("outputs", []).extend(
        {
            "path": str((ROUTE_DIR / filename).relative_to(REPO)).replace("\\", "/"),
            "artifact": PREFIX,
            "generated_utc": GENERATED_UTC,
            "sha256": sha256_file(ROUTE_DIR / filename),
        }
        for filename in [*outputs, f"{PREFIX}_RESULT_2026-05-17.json", f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json", f"{PREFIX}_SUMMARY_2026-05-17.md"]
    )
    write_json(manifest_path, manifest)
    with (ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "generated_utc": GENERATED_UTC,
                    "artifact": PREFIX,
                    "event": "denominator_source_resolution_built",
                    "counts": counts,
                    "not_completion": True,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                },
                sort_keys=True,
            )
            + "\n"
        )
    print(json.dumps({"artifact": PREFIX, "counts": counts, "ok": True}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
