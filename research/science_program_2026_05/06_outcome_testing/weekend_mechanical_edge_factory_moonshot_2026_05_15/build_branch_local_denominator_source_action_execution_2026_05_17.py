#!/usr/bin/env python3
"""Execute denominator/source resolution actions into guarded specs and next-action rows."""

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

from src.research_infra.moonshot_branch_local_denominator_source_action_execution import (
    guarded_scorer_spec,
    next_action_execution,
    terminal_kill_preservation,
)


CLAIM_BOUNDARY = (
    "Branch-local denominator/source action-execution bundle only. It materializes guarded scorer specs, "
    "next same-resource compute actions, and terminal kill preservation rows from resolution decisions. It "
    "does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, "
    "validation, live-readiness, or promotion."
)
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
RES_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_RESOLUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACTION_EXECUTION_BUNDLE"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_UTC = utc_now()


def io_path(path: Path) -> Path:
    absolute = path.resolve()
    text = str(absolute)
    if sys.platform.startswith("win") and not text.startswith("\\\\?\\"):
        return Path("\\\\?\\" + text)
    return absolute


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


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        Path("src/research_infra/moonshot_branch_local_denominator_source_action_execution.py"),
        Path(
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/"
            "build_branch_local_denominator_source_action_execution_2026_05_17.py"
        ),
        Path(
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/"
            "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
        ),
        Path("tests/research_infra/test_moonshot_unified_execution_scorer.py"),
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_RESULT_2026-05-17.json",
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_RUNTIME_SPEC_2026-05-17.json",
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_PRIMARY_RESOLUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_EXACT_CONTROL_SCOPE_RESOLUTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_GUARDED_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_NEXT_COMPUTE_ACTION_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_TERMINAL_KILL_LEDGER_2026-05-17.jsonl",
        ROUTE_DIR.relative_to(REPO) / f"{RES_PREFIX}_IMPLEMENTATION_RESOLUTION_LEDGER_2026-05-17.jsonl",
    ]
    rows: list[dict[str, Any]] = []
    for index, rel_path in enumerate(paths, 1):
        abs_path = REPO / rel_path
        exists = io_path(abs_path).exists()
        rows.append(
            {
                "source_manifest_row_id": f"OHLC-GTOS-DENOM-SRC-ACTEXEC-MANIFEST-{index:04d}",
                "path": str(rel_path).replace("\\", "/"),
                "sha256": sha256_file(abs_path) if exists else None,
                "status": "HASHED" if exists else "MISSING",
                "generated_utc": GENERATED_UTC,
                "safe_flags": SAFE_FLAGS,
                "not_completion": True,
                "live_effect": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


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
                        "bucket_id": f"OHLC-GTOS-DENOM-SRC-ACTEXEC-BUCKET-{index:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": int(count),
                    }
                )
            )
            index += 1
    return rows


def split_symbol_session(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted({(row.get("symbol"), row.get("route_session")) for row in rows})
    output: list[dict[str, Any]] = []
    for index, key in enumerate(keys, 1):
        members = [row for row in rows if (row.get("symbol"), row.get("route_session")) == key]
        output.append(
            finalize(
                {
                    "symbol_session_action_execution_row_id": f"OHLC-GTOS-DENOM-SRC-ACTEXEC-SYMSESS-{index:04d}",
                    "symbol": key[0],
                    "route_session": key[1],
                    "row_count": len(members),
                    "candidate_use_allowed_now_rows": sum(1 for row in members if row.get("candidate_use_allowed_now")),
                    "terminal_decision_rows": sum(1 for row in members if row.get("terminal_decision")),
                    "outside_gbpjpy_xauusd_current_branch_box_rows": sum(
                        1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")
                    ),
                }
            )
        )
    return output


def main() -> None:
    resolution_result = read_json(ROUTE_DIR / f"{RES_PREFIX}_RESULT_2026-05-17.json")
    primary_rows = read_jsonl(ROUTE_DIR / f"{RES_PREFIX}_PRIMARY_RESOLUTION_LEDGER_2026-05-17.jsonl")
    scope_rows = read_jsonl(ROUTE_DIR / f"{RES_PREFIX}_EXACT_CONTROL_SCOPE_RESOLUTION_LEDGER_2026-05-17.jsonl")
    guarded_rows = read_jsonl(ROUTE_DIR / f"{RES_PREFIX}_GUARDED_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl")
    next_rows = read_jsonl(ROUTE_DIR / f"{RES_PREFIX}_NEXT_COMPUTE_ACTION_LEDGER_2026-05-17.jsonl")
    terminal_rows = read_jsonl(ROUTE_DIR / f"{RES_PREFIX}_TERMINAL_KILL_LEDGER_2026-05-17.jsonl")
    implementation_rows = read_jsonl(ROUTE_DIR / f"{RES_PREFIX}_IMPLEMENTATION_RESOLUTION_LEDGER_2026-05-17.jsonl")

    resolution_by_id = {row.get("denominator_source_resolution_row_id"): row for row in [*primary_rows, *scope_rows]}
    guarded_specs = add_ids(
        [guarded_scorer_spec(row) for row in guarded_rows],
        "OHLC-GTOS-DENOM-SRC-ACTEXEC-GUARD",
        "guarded_scorer_spec_row_id",
    )
    next_action_rows = add_ids(
        [
            next_action_execution(row, resolution_by_id.get(row.get("input_resolution_row_id"), {}))
            for row in next_rows
        ],
        "OHLC-GTOS-DENOM-SRC-ACTEXEC-NEXT",
        "action_execution_row_id",
    )
    terminal_kill_rows = add_ids(
        [terminal_kill_preservation(row) for row in terminal_rows],
        "OHLC-GTOS-DENOM-SRC-ACTEXEC-KILL",
        "terminal_kill_preservation_row_id",
    )
    implementation_materialization_rows = add_ids(
        [
            {
                "denominator_source_action_execution_surface": "src/research_infra/moonshot_branch_local_denominator_source_action_execution.py",
                "action_execution_lane": "IMPLEMENTATION_MATERIALIZATION",
                "action_execution_status": row.get("implementation_resolution_status"),
                "input_implementation_resolution_row_id": row.get("implementation_resolution_row_id"),
                "input_resolution_row_id": row.get("input_resolution_row_id"),
                "source_resolution_lane": row.get("source_resolution_lane"),
                "symbol": row.get("symbol"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "primitive_flag": row.get("primitive_flag"),
                "source_code_candidate_id": row.get("source_code_candidate_id"),
                "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                "candidate_implementation_state": row.get("candidate_implementation_state"),
                "candidate_use_allowed_now": row.get("candidate_use_allowed_now"),
                "terminal_decision": row.get("terminal_decision"),
                "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
                "next_same_resource_action": row.get("next_same_resource_action"),
                "resolution_action": row.get("resolution_action"),
                "implementation_implication": row.get("implementation_implication"),
                "live_effect": False,
            }
            for row in implementation_rows
        ],
        "OHLC-GTOS-DENOM-SRC-ACTEXEC-IMPL",
        "implementation_materialization_row_id",
    )
    symbol_session_rows = split_symbol_session(next_action_rows)
    distributions = {
        "action_execution_lane": string_counter(next_action_rows, "action_execution_lane"),
        "action_execution_status": string_counter(next_action_rows, "action_execution_status"),
        "candidate_implementation_state": string_counter(next_action_rows, "candidate_implementation_state"),
        "guarded_proxy_score_class": string_counter(guarded_specs, "guarded_proxy_score_class"),
        "implementation_materialization_status": string_counter(
            implementation_materialization_rows, "action_execution_status"
        ),
        "terminal_kill_status": string_counter(terminal_kill_rows, "action_execution_status"),
        "next_execution_step": string_counter(next_action_rows, "next_execution_step"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            next_action_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    buckets = bucket_rows(distributions)
    questions = [
        finalize(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACTEXEC-Q-0001",
                "question": "Which resolution rows produce usable guarded scorer specs now?",
                "answer_from_current_rows": "4 exact-control scope rows materialize as guarded research-only scorer specs while exact-control denominator build remains open.",
                "next_action": "wire guarded scorer specs into branch-local candidate registry and continue exact denominator expansion",
            }
        ),
        finalize(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACTEXEC-Q-0002",
                "question": "Which killed candidates stay preserved as system intelligence?",
                "answer_from_current_rows": "67 terminal kill rows are preserved: 61 source proxy kills and 6 horizon kills.",
                "next_action": "use killed rows as source/horizon failure intelligence and keep exact contradiction routes for source rows",
            }
        ),
        finalize(
            {
                "question_id": "OHLC-GTOS-DENOM-SRC-ACTEXEC-Q-0003",
                "question": "Which next same-resource computations remain open?",
                "answer_from_current_rows": "207 action-execution rows remain open across exact-control build, source contradiction, and horizon repair/redesign/kill-check routes.",
                "next_action": "execute denominator expansion, contradiction checks, and horizon detail materialization",
            }
        ),
    ]
    counts = {
        "input_primary_resolution_rows": len(primary_rows),
        "input_exact_scope_resolution_rows": len(scope_rows),
        "input_guarded_candidate_rows": len(guarded_rows),
        "input_next_compute_action_rows": len(next_rows),
        "input_terminal_kill_rows": len(terminal_rows),
        "input_implementation_resolution_rows": len(implementation_rows),
        "guarded_scorer_spec_rows": len(guarded_specs),
        "next_action_execution_rows": len(next_action_rows),
        "terminal_kill_preservation_rows": len(terminal_kill_rows),
        "implementation_materialization_rows": len(implementation_materialization_rows),
        "symbol_session_action_execution_rows": len(symbol_session_rows),
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
        "upstream_counts": {"denominator_source_resolution_bundle": resolution_result.get("counts", {})},
        "bucket_distributions": distributions,
        "source_manifest_hash": SOURCE_MANIFEST_HASH,
        "system_decision": {
            "action_execution_status_counts": distributions["action_execution_status"],
            "implementation_materialization_status_counts": distributions["implementation_materialization_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_DENOMINATOR_SOURCE_ACTION_EXECUTION_BUNDLE_RESULT: materialize 4 guarded "
                "research-only scorer specs now, preserve 67 killed rows, and execute 207 same-resource "
                "build/contradiction/repair/redesign rows before any broader implementation claim."
            ),
        },
    }
    outputs = {
        f"{PREFIX}_GUARDED_SCORER_SPEC_LEDGER_2026-05-17.jsonl": guarded_specs,
        f"{PREFIX}_NEXT_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl": next_action_rows,
        f"{PREFIX}_TERMINAL_KILL_PRESERVATION_LEDGER_2026-05-17.jsonl": terminal_kill_rows,
        f"{PREFIX}_IMPLEMENTATION_MATERIALIZATION_LEDGER_2026-05-17.jsonl": implementation_materialization_rows,
        f"{PREFIX}_SYMBOL_SESSION_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl": symbol_session_rows,
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
            "input_artifacts": [RES_PREFIX],
            "output_files": sorted([*outputs, f"{PREFIX}_RESULT_2026-05-17.json"]),
        },
    )
    (ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md").write_text(
        "\n".join(
            [
                "# Branch-Local Denominator Source Action Execution Bundle",
                "",
                f"Generated UTC: `{GENERATED_UTC}`",
                "",
                f"- Guarded scorer spec rows: `{len(guarded_specs)}`.",
                f"- Next action execution rows: `{len(next_action_rows)}`.",
                f"- Terminal kill preservation rows: `{len(terminal_kill_rows)}`.",
                f"- Implementation materialization rows: `{len(implementation_materialization_rows)}`.",
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
                    "event": "denominator_source_action_execution_built",
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
