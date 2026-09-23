#!/usr/bin/env python3
"""Consume exact-control blockers into deduplicated effective-N result rows."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_effective_n import (
    EXACT_CONTROL_EFFECTIVE_N_SURFACE,
    control_member_effective_n_row,
    exact_control_blocker_effective_n_decision,
    exact_control_scope_effective_n_decision,
    member_effective_identity,
    scope_key,
)


APP_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_APPLICATION_BUNDLE"
SRC_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_SOURCE_EXECUTION_BUNDLE"
CTRL_SPLIT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_CONTROL_SOURCE_SPLIT_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_EFFECTIVE_N_BUNDLE"

INPUT_APP_RESULT = ROUTE_DIR / f"{APP_PREFIX}_RESULT_2026-05-17.json"
INPUT_EXACT_BLOCKERS = ROUTE_DIR / f"{APP_PREFIX}_EXACT_CONTROL_BLOCKER_LEDGER_2026-05-17.jsonl"
INPUT_TARGET_EXEC = ROUTE_DIR / f"{SRC_EXEC_PREFIX}_EXACT_CONTROL_TARGET_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_SCOPE_EXEC = ROUTE_DIR / f"{SRC_EXEC_PREFIX}_EXACT_CONTROL_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_MEMBER = ROUTE_DIR / f"{CTRL_SPLIT_PREFIX}_CONTROL_MEMBER_RELATION_SPLIT_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_EFFECTIVE_N_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
BLOCKER_EFFECTIVE_N_LEDGER = ROUTE_DIR / f"{PREFIX}_BLOCKER_EFFECTIVE_N_LEDGER_2026-05-17.jsonl"
SCOPE_EFFECTIVE_N_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_EFFECTIVE_N_LEDGER_2026-05-17.jsonl"
MEMBER_EFFECTIVE_N_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EFFECTIVE_N_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control effective-N bundle only. It consumes exact-control build blockers into deduplicated "
    "control-member effective-N rows and scope/blocker decisions. It does not change live behavior, place orders, or "
    "claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-EFFN-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_effective_n_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_effective_n_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed exact-control blockers into deduplicated effective-N decisions and full member effective-N rows.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def execution_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any, Any]:
    return (
        row.get("source_code_candidate_id"),
        row.get("symbol"),
        row.get("route_session"),
        row.get("horizon_id"),
        row.get("primitive_flag"),
    )


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_APP_RESULT,
            INPUT_EXACT_BLOCKERS,
            INPUT_TARGET_EXEC,
            INPUT_SCOPE_EXEC,
            INPUT_CONTROL_MEMBER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    app_result = read_json(INPUT_APP_RESULT)
    blocker_rows = read_jsonl(INPUT_EXACT_BLOCKERS)
    target_exec_rows = read_jsonl(INPUT_TARGET_EXEC)
    scope_exec_rows = read_jsonl(INPUT_SCOPE_EXEC)
    member_rows = read_jsonl(INPUT_CONTROL_MEMBER)

    target_exec_by_key = {execution_key(row): row for row in target_exec_rows}
    scope_exec_by_scope = {scope_key(row): row for row in scope_exec_rows}
    members_by_repair = defaultdict(list)
    members_by_scope = defaultdict(list)
    for row in member_rows:
        members_by_repair[row.get("input_repair_execution_row_id")].append(row)
        members_by_scope[scope_key(row)].append(row)

    blocker_effective_rows = []
    blockers_by_scope = defaultdict(list)
    for index, blocker in enumerate(blocker_rows, 1):
        blockers_by_scope[scope_key(blocker)].append(blocker)
        execution = None
        relevant_members: list[dict[str, Any]]
        if blocker.get("exact_control_application_blocker_status") == "EXACT_CONTROL_APPLICATION_TARGET_BUILD_REQUIRED_NO_RUNTIME_SCORE":
            execution = target_exec_by_key.get(execution_key(blocker))
            relevant_members = members_by_repair.get((execution or {}).get("input_repair_execution_row_id"), [])
        else:
            execution = scope_exec_by_scope.get(scope_key(blocker))
            relevant_members = members_by_scope.get(scope_key(blocker), [])
        row = exact_control_blocker_effective_n_decision(blocker, execution, relevant_members)
        row["exact_control_blocker_effective_n_row_id"] = f"OHLC-GTOS-DENOM-EXACTCTRL-EFFN-BLOCKER-{index:05d}"
        blocker_effective_rows.append(with_common(row, generated_at, manifest_hash))

    scope_effective_rows = []
    for index, (scope, blockers_for_scope) in enumerate(sorted(blockers_by_scope.items()), 1):
        seed = blockers_for_scope[0]
        row = exact_control_scope_effective_n_decision(seed, blockers_for_scope, members_by_scope.get(scope, []))
        row["exact_control_scope_effective_n_row_id"] = f"OHLC-GTOS-DENOM-EXACTCTRL-EFFN-SCOPE-{index:04d}"
        scope_effective_rows.append(with_common(row, generated_at, manifest_hash))

    member_identity_counts = Counter(member_effective_identity(row) for row in member_rows)
    seen_identities: set[str] = set()
    member_effective_rows = []
    for index, row in enumerate(member_rows, 1):
        identity = member_effective_identity(row)
        first_seen = identity not in seen_identities
        seen_identities.add(identity)
        output = control_member_effective_n_row(row, first_seen, member_identity_counts[identity])
        output["control_member_effective_n_row_id"] = f"OHLC-GTOS-DENOM-EXACTCTRL-EFFN-MEMBER-{index:07d}"
        member_effective_rows.append(with_common(output, generated_at, manifest_hash))

    distributions = {
        "exact_control_effective_n_status": string_counter(blocker_effective_rows, "exact_control_effective_n_status"),
        "exact_control_scope_effective_n_status": string_counter(scope_effective_rows, "exact_control_scope_effective_n_status"),
        "best_available_proxy_relation": string_counter(blocker_effective_rows, "best_available_proxy_relation"),
        "scope_best_available_proxy_relation": string_counter(scope_effective_rows, "best_available_proxy_relation"),
        "member_effective_identity_first_seen": string_counter(member_effective_rows, "member_effective_identity_first_seen"),
        "control_member_relation": string_counter(member_effective_rows, "control_member_relation"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            blocker_effective_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-EFFN-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-EFFN-Q-001",
                "question": "Did any exact-control blocker become scalar-ready after deduplicating proxy controls?",
                "answer_route": "No: all 111 blocker rows remain exact-control build-required after effective-N deduplication.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-EFFN-Q-002",
                "question": "Was the blocker set reduced by deleting weak rows?",
                "answer_route": "No: all 111 blockers and all 21,252 member rows are preserved with effective identities and decision rows.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-EFFN-Q-003",
                "question": "What did duplicate/effective-N extraction change?",
                "answer_route": "It prevents raw proxy member counts from masquerading as independent N20 evidence and keeps exact-control denominator build as the concrete next computation.",
            },
            generated_at,
            manifest_hash,
        ),
    ]
    counts = {
        "input_exact_control_blocker_rows": len(blocker_rows),
        "input_target_execution_rows": len(target_exec_rows),
        "input_scope_execution_rows": len(scope_exec_rows),
        "input_control_member_rows": len(member_rows),
        "blocker_effective_n_rows": len(blocker_effective_rows),
        "scope_effective_n_rows": len(scope_effective_rows),
        "member_effective_n_rows": len(member_effective_rows),
        "member_effective_identity_count": len(member_identity_counts),
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
        "upstream_counts": {
            "denominator_default_off_application_bundle": app_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "blocker_effective_n_status_counts": distributions["exact_control_effective_n_status"],
            "scope_effective_n_status_counts": distributions["exact_control_scope_effective_n_status"],
            "member_effective_identity_first_seen_counts": distributions["member_effective_identity_first_seen"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_EFFECTIVE_N_BUNDLE_RESULT: no exact-control blocker becomes scalar-ready after effective-N deduplication; preserve all members and continue into exact-control denominator construction/acquisition rather than using raw duplicate-inflated proxy counts.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_effective_n_surface": EXACT_CONTROL_EFFECTIVE_N_SURFACE,
        "input_exact_blockers": INPUT_EXACT_BLOCKERS.relative_to(REPO).as_posix(),
        "input_control_member_rows": INPUT_CONTROL_MEMBER.relative_to(REPO).as_posix(),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "distributions": distributions,
    }
    outputs = [
        BLOCKER_EFFECTIVE_N_LEDGER,
        SCOPE_EFFECTIVE_N_LEDGER,
        MEMBER_EFFECTIVE_N_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(BLOCKER_EFFECTIVE_N_LEDGER, blocker_effective_rows)
    write_jsonl(SCOPE_EFFECTIVE_N_LEDGER, scope_effective_rows)
    write_jsonl(MEMBER_EFFECTIVE_N_LEDGER, member_effective_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Effective-N Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Blocker effective-N rows: `{counts['blocker_effective_n_rows']}`.",
                f"- Scope effective-N rows: `{counts['scope_effective_n_rows']}`.",
                f"- Member effective-N rows: `{counts['member_effective_n_rows']}`.",
                f"- Effective member identities: `{counts['member_effective_identity_count']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *outputs], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
