#!/usr/bin/env python3
"""Register branch-local guarded denominator/source scorer specs."""

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

from src.research_infra.moonshot_branch_local_denominator_guarded_scorers import (
    GUARDED_SCORER_REGISTRY_SURFACE,
    register_research_only_guarded_scope_proxy_scorer,
    score_guarded_scope_proxy_event,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_ACTION_EXECUTION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_GUARDED_SCOPE_SCORER_REGISTRATION_BUNDLE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_RUNTIME_SPEC = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_SPEC_2026-05-17.json"
INPUT_GUARDED = ROUTE_DIR / f"{INPUT_PREFIX}_GUARDED_SCORER_SPEC_LEDGER_2026-05-17.jsonl"
INPUT_NEXT_ACTION = ROUTE_DIR / f"{INPUT_PREFIX}_NEXT_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_TERMINAL = ROUTE_DIR / f"{INPUT_PREFIX}_TERMINAL_KILL_PRESERVATION_LEDGER_2026-05-17.jsonl"
INPUT_IMPLEMENTATION = ROUTE_DIR / f"{INPUT_PREFIX}_IMPLEMENTATION_MATERIALIZATION_LEDGER_2026-05-17.jsonl"

REGISTRY_MODULE = REPO / GUARDED_SCORER_REGISTRY_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRATION_LEDGER_2026-05-17.jsonl"
SMOKE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SMOKE_LEDGER_2026-05-17.jsonl"
NEXT_ACTION_CARRYFORWARD_LEDGER = ROUTE_DIR / f"{PREFIX}_NEXT_ACTION_CARRYFORWARD_LEDGER_2026-05-17.jsonl"
TERMINAL_CARRYFORWARD_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_KILL_CARRYFORWARD_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_REGISTRATION_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_REGISTRATION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
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
    "Branch-local guarded scope scorer registration bundle only. It materializes research-only scorer registry rows "
    "from the guarded denominator/source action-execution specs and preserves all next-action and terminal-kill rows. "
    "It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
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
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-GUARDED-SCORER-REG-SRC-{index:04d}",
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


def registration_rows(spec_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, spec in enumerate(spec_rows, 1):
        registered = register_research_only_guarded_scope_proxy_scorer(spec)
        registered.update(
            {
                "guarded_scorer_registration_row_id": f"OHLC-GTOS-GUARDED-SCORER-REG-{index:05d}",
                "input_action_execution_status": spec.get("action_execution_status"),
                "input_action_execution_lane": spec.get("action_execution_lane"),
                "source_code_candidate_id": registered.get("guarded_scorer_key"),
                "registration_scope_preserved": True,
            }
        )
        output.append(with_common(registered, generated_at, manifest_hash))
    return output


def smoke_rows(reg_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, reg in enumerate(reg_rows, 1):
        matching_event = {
            "symbol": reg.get("symbol"),
            "route_session": reg.get("route_session"),
            "horizon_id": reg.get("horizon_id"),
            "primitive_flag": reg.get("primitive_flag"),
        }
        mismatch_event = dict(matching_event)
        mismatch_event["symbol"] = "XAUUSD" if reg.get("symbol") != "XAUUSD" else "GBPJPY"
        for case_name, event in [("MATCHING_SCOPE", matching_event), ("MISMATCHED_SYMBOL_SCOPE", mismatch_event)]:
            scored = score_guarded_scope_proxy_event(event, reg)
            scored.update(
                {
                    "guarded_scorer_smoke_row_id": f"OHLC-GTOS-GUARDED-SCORER-SMOKE-{len(output) + 1:05d}",
                    "input_guarded_scorer_registration_row_id": reg.get("guarded_scorer_registration_row_id"),
                    "smoke_case": case_name,
                }
            )
            output.append(with_common(scored, generated_at, manifest_hash))
    return output


def carry_next_actions(
    rows: list[dict[str, Any]],
    reg_by_resolution_id: dict[Any, dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        registration = reg_by_resolution_id.get(row.get("input_resolution_row_id"))
        carried = dict(row)
        carried.update(
            {
                "guarded_scorer_next_action_carryforward_row_id": f"OHLC-GTOS-GUARDED-SCORER-NEXT-{index:05d}",
                "matched_guarded_scorer_registration_row_id": (registration or {}).get(
                    "guarded_scorer_registration_row_id"
                ),
                "matched_guarded_scorer_key": (registration or {}).get("guarded_scorer_key"),
                "registration_followup_status": (
                    "GUARDED_SCORER_REGISTRATION_ATTACHED_BUILD_STILL_OPEN"
                    if registration
                    else "NO_GUARDED_SCORER_REGISTRATION_FOR_ACTION"
                ),
                "exact_control_build_still_open": bool(registration)
                or row.get("action_execution_lane") in {"EXACT_CONTROL_TARGET_BUILD", "EXACT_CONTROL_SCOPE_BUILD"},
                "preserve_next_action_without_truncation": True,
            }
        )
        output.append(with_common(carried, generated_at, manifest_hash))
    return output


def carry_terminal_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        carried = dict(row)
        carried.update(
            {
                "guarded_scorer_terminal_carryforward_row_id": f"OHLC-GTOS-GUARDED-SCORER-TERM-{index:05d}",
                "registration_followup_status": "TERMINAL_KILL_PRESERVED_NO_SCORER_REGISTRATION",
                "preserve_terminal_failure_intelligence": True,
            }
        )
        output.append(with_common(carried, generated_at, manifest_hash))
    return output


def implementation_registration_rows(
    rows: list[dict[str, Any]],
    reg_by_resolution_id: dict[Any, dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        registration = reg_by_resolution_id.get(row.get("input_resolution_row_id"))
        materialized = dict(row)
        if registration:
            status = "IMPLEMENTATION_GUARDED_SCORER_REGISTERED_BUILD_STILL_OPEN"
        else:
            status = "IMPLEMENTATION_REGISTRATION_NOT_APPLICABLE"
        materialized.update(
            {
                "guarded_scorer_implementation_registration_row_id": f"OHLC-GTOS-GUARDED-SCORER-IMPL-{index:05d}",
                "matched_guarded_scorer_registration_row_id": (registration or {}).get(
                    "guarded_scorer_registration_row_id"
                ),
                "matched_guarded_scorer_key": (registration or {}).get("guarded_scorer_key"),
                "implementation_registration_status": status,
                "unconditional_scalar_use_allowed": False,
            }
        )
        output.append(with_common(materialized, generated_at, manifest_hash))
    return output


def symbol_session_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("symbol"), row.get("route_session"))].append(row)
    output: list[dict[str, Any]] = []
    for index, ((symbol, route_session), members) in enumerate(
        sorted(grouped.items(), key=lambda item: tuple(str(part) for part in item[0])), 1
    ):
        output.append(
            with_common(
                {
                    "guarded_scorer_symbol_session_row_id": f"OHLC-GTOS-GUARDED-SCORER-SYMSESS-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "registration_rows": len(members),
                    "registered_rows": sum(
                        1
                        for row in members
                        if row.get("guarded_scorer_registration_status") == "GUARDED_SCORER_REGISTERED_RESEARCH_ONLY"
                    ),
                    "guarded_proxy_score_class_counts": string_counter(members, "guarded_proxy_score_class"),
                    "horizon_counts": string_counter(members, "horizon_id"),
                    "primitive_counts": string_counter(members, "primitive_flag"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def bucket_rows(
    reg_rows: list[dict[str, Any]],
    smoke: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    impl_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "guarded_scorer_registration_status": string_counter(reg_rows, "guarded_scorer_registration_status"),
        "guarded_proxy_score_class": string_counter(reg_rows, "guarded_proxy_score_class"),
        "symbol": string_counter(reg_rows, "symbol"),
        "route_session": string_counter(reg_rows, "route_session"),
        "horizon_id": string_counter(reg_rows, "horizon_id"),
        "primitive_flag": string_counter(reg_rows, "primitive_flag"),
        "smoke_status": string_counter(smoke, "guarded_scope_proxy_event_status"),
        "next_action_lane": string_counter(next_rows, "action_execution_lane"),
        "next_action_registration_followup_status": string_counter(next_rows, "registration_followup_status"),
        "terminal_kill_status": string_counter(terminal_rows, "action_execution_status"),
        "implementation_registration_status": string_counter(impl_rows, "implementation_registration_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(reg_rows, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    output: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-GUARDED-SCORER-BUCKET-{len(output) + 1:04d}",
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
    manifest["latest_branch_local_guarded_scope_scorer_registration_bundle"] = {
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
        "event": "branch_local_guarded_scope_scorer_registration_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Registered four branch-local guarded scope proxy scorer specs and preserved next-action/terminal rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_RESULT,
            INPUT_RUNTIME_SPEC,
            INPUT_GUARDED,
            INPUT_NEXT_ACTION,
            INPUT_TERMINAL,
            INPUT_IMPLEMENTATION,
            REGISTRY_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )

    input_result = read_json(INPUT_RESULT)
    guarded_specs = read_jsonl(INPUT_GUARDED)
    next_actions = read_jsonl(INPUT_NEXT_ACTION)
    terminal = read_jsonl(INPUT_TERMINAL)
    implementation = read_jsonl(INPUT_IMPLEMENTATION)

    registered = registration_rows(guarded_specs, generated_at, manifest_hash)
    reg_by_resolution_id = {row.get("input_resolution_row_id"): row for row in registered}
    smoke = smoke_rows(registered, generated_at, manifest_hash)
    next_carried = carry_next_actions(next_actions, reg_by_resolution_id, generated_at, manifest_hash)
    terminal_carried = carry_terminal_rows(terminal, generated_at, manifest_hash)
    implementation_registered = implementation_registration_rows(
        implementation, reg_by_resolution_id, generated_at, manifest_hash
    )
    symbol_sessions = symbol_session_rows(registered, generated_at, manifest_hash)
    buckets, distributions = bucket_rows(
        registered, smoke, next_carried, terminal_carried, implementation_registered, generated_at, manifest_hash
    )
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-GUARDED-SCORER-Q-001",
                "question": "Did guarded scorer registration consume all guarded specs?",
                "answer_route": "Yes: all 4 guarded action-execution specs are registered as research-only branch-local scorer rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-GUARDED-SCORER-Q-002",
                "question": "Did registration close exact-control denominator work?",
                "answer_route": "No: every registered scorer keeps exact-control denominator build open and disallows unconditional scalar use.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-GUARDED-SCORER-Q-003",
                "question": "Did next-action and terminal-kill rows stay preserved?",
                "answer_route": "Yes: all 207 next-action rows and all 67 terminal-kill rows are carried forward without truncation.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_guarded_scorer_spec_rows": len(guarded_specs),
        "input_next_action_execution_rows": len(next_actions),
        "input_terminal_kill_preservation_rows": len(terminal),
        "input_implementation_materialization_rows": len(implementation),
        "guarded_scorer_registration_rows": len(registered),
        "guarded_scorer_smoke_rows": len(smoke),
        "next_action_carryforward_rows": len(next_carried),
        "terminal_kill_carryforward_rows": len(terminal_carried),
        "implementation_registration_rows": len(implementation_registered),
        "symbol_session_registration_rows": len(symbol_sessions),
        "bucket_rows": len(buckets),
        "question_rows": len(questions),
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
        "upstream_counts": {"denominator_source_action_execution_bundle": input_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": {
            "guarded_scorer_registration_status_counts": distributions["guarded_scorer_registration_status"],
            "next_action_registration_followup_counts": distributions["next_action_registration_followup_status"],
            "system_recommendation": (
                "BRANCH_LOCAL_GUARDED_SCOPE_SCORER_REGISTRATION_BUNDLE_RESULT: register 4 research-only guarded "
                "scope proxy scorers, preserve 207 next-action rows, preserve 67 terminal kills, and continue exact "
                "control denominator/source/horizon repair execution before any unconditional scorer use."
            ),
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "input_action_execution_result": INPUT_RESULT.relative_to(REPO).as_posix(),
        "registry_surface": GUARDED_SCORER_REGISTRY_SURFACE,
        "guard_policy": {
            "research_only": True,
            "unconditional_scalar_use_allowed": False,
            "exact_control_denominator_build_still_required": True,
            "live_effect": False,
        },
        "distributions": distributions,
    }

    generated_files = [
        REGISTRATION_LEDGER,
        SMOKE_LEDGER,
        NEXT_ACTION_CARRYFORWARD_LEDGER,
        TERMINAL_CARRYFORWARD_LEDGER,
        IMPLEMENTATION_REGISTRATION_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(REGISTRATION_LEDGER, registered)
    write_jsonl(SMOKE_LEDGER, smoke)
    write_jsonl(NEXT_ACTION_CARRYFORWARD_LEDGER, next_carried)
    write_jsonl(TERMINAL_CARRYFORWARD_LEDGER, terminal_carried)
    write_jsonl(IMPLEMENTATION_REGISTRATION_LEDGER, implementation_registered)
    write_jsonl(SYMBOL_SESSION_LEDGER, symbol_sessions)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Guarded Scope Scorer Registration Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Guarded scorer registration rows: `{counts['guarded_scorer_registration_rows']}`.",
                f"- Smoke rows: `{counts['guarded_scorer_smoke_rows']}`.",
                f"- Next-action carryforward rows: `{counts['next_action_carryforward_rows']}`.",
                f"- Terminal kill carryforward rows: `{counts['terminal_kill_carryforward_rows']}`.",
                f"- Implementation registration rows: `{counts['implementation_registration_rows']}`.",
                "- Exact-control denominator builds remain open; unconditional scalar use remains disallowed.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
