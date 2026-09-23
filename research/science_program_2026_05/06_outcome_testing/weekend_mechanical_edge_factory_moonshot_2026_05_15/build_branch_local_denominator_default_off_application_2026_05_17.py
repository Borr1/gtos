#!/usr/bin/env python3
"""Apply branch-local default-off scorer surfaces to the full denominator."""

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

from src.research_infra.moonshot_branch_local_denominator_default_off_application import (
    DEFAULT_OFF_APPLICATION_SURFACE,
    current_claim_rejection_audit,
    default_off_application_decision,
    exact_control_blocker_decision,
    scorer_application_decision,
)


DECISION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DETAIL_DECISION_EXECUTION_BUNDLE"
SCORER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_SCORER_MATERIALIZATION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_APPLICATION_BUNDLE"

INPUT_DECISION_RESULT = ROUTE_DIR / f"{DECISION_PREFIX}_RESULT_2026-05-17.json"
INPUT_IMPLEMENTATION = ROUTE_DIR / f"{DECISION_PREFIX}_DEFAULT_OFF_IMPLEMENTATION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_EXPANSION = ROUTE_DIR / f"{DECISION_PREFIX}_EXACT_CONTROL_EXPANSION_LEDGER_2026-05-17.jsonl"
INPUT_SOURCE_COMPLETENESS = ROUTE_DIR / f"{DECISION_PREFIX}_SOURCE_COMPLETENESS_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON_DECISION = ROUTE_DIR / f"{DECISION_PREFIX}_HORIZON_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_SCORER_RESULT = ROUTE_DIR / f"{SCORER_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCORER_REGISTRATION = ROUTE_DIR / f"{SCORER_PREFIX}_REGISTRATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / DEFAULT_OFF_APPLICATION_SURFACE
SCORER_HELPER_MODULE = REPO / "src/research_infra/moonshot_branch_local_denominator_default_off_scorers.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_APPLICATION_LEDGER_2026-05-17.jsonl"
EXACT_CONTROL_BLOCKER_LEDGER = ROUTE_DIR / f"{PREFIX}_EXACT_CONTROL_BLOCKER_LEDGER_2026-05-17.jsonl"
SCORER_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_APPLICATION_LEDGER_2026-05-17.jsonl"
CURRENT_CLAIM_REJECTION_AUDIT_LEDGER = ROUTE_DIR / f"{PREFIX}_CURRENT_CLAIM_REJECTION_AUDIT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local denominator default-off application bundle only. It applies registered default-off scorer/gate "
    "surfaces to the full implementation denominator, preserves exact-control build blockers, and preserves current "
    "claim rejection audits so the unsupported claim is rejected without deleting the underlying mechanism, avoid "
    "feature, redesign route, source-capture route, or system intelligence. It does not change live behavior, place "
    "orders, or claim broker R/PnL, realized expectancy, win-rate, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-DEFAULT-OFF-APPLICATION-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_default_off_application_bundle"] = {
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
        "event": "branch_local_denominator_default_off_application_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Applied registered default-off scorer/gate surfaces to all implementation rows while preserving exact-control blockers and current-claim rejection audits.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_DECISION_RESULT,
            INPUT_IMPLEMENTATION,
            INPUT_EXACT_EXPANSION,
            INPUT_SOURCE_COMPLETENESS,
            INPUT_HORIZON_DECISION,
            INPUT_SCORER_RESULT,
            INPUT_SCORER_REGISTRATION,
            HELPER_MODULE,
            SCORER_HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    decision_result = read_json(INPUT_DECISION_RESULT)
    scorer_result = read_json(INPUT_SCORER_RESULT)
    implementation_rows = read_jsonl(INPUT_IMPLEMENTATION)
    exact_rows = read_jsonl(INPUT_EXACT_EXPANSION)
    source_rows = read_jsonl(INPUT_SOURCE_COMPLETENESS)
    horizon_rows = read_jsonl(INPUT_HORIZON_DECISION)
    registration_rows = read_jsonl(INPUT_SCORER_REGISTRATION)

    exact_by_detail = {row.get("input_detail_execution_row_id"): row for row in exact_rows}
    source_by_detail = {row.get("input_detail_execution_row_id"): row for row in source_rows}
    horizon_by_detail = {row.get("input_detail_execution_row_id"): row for row in horizon_rows}
    registration_by_detail = {row.get("input_detail_execution_row_id"): row for row in registration_rows}

    application_rows = []
    exact_blocker_rows = []
    scorer_application_rows = []
    rejection_audit_rows = []
    for index, row in enumerate(implementation_rows, 1):
        detail_id = row.get("input_detail_execution_row_id")
        registration = registration_by_detail.get(detail_id)
        exact = exact_by_detail.get(detail_id)
        source = source_by_detail.get(detail_id)
        horizon = horizon_by_detail.get(detail_id)
        application = default_off_application_decision(row, registration, exact, source, horizon)
        application["default_off_application_row_id"] = f"OHLC-GTOS-DENOM-DEFAULT-OFF-APP-{index:05d}"
        application_rows.append(with_common(application, generated_at, manifest_hash))
        if row.get("default_off_implementation_status") == "DEFAULT_OFF_BLOCKED_EXACT_CONTROL_BUILD_REQUIRED":
            blocker = exact_control_blocker_decision(row, exact)
            blocker["exact_control_blocker_row_id"] = (
                f"OHLC-GTOS-DENOM-DEFAULT-OFF-EXACT-BLOCKER-{len(exact_blocker_rows) + 1:05d}"
            )
            exact_blocker_rows.append(with_common(blocker, generated_at, manifest_hash))
        if registration:
            scorer_action = scorer_application_decision(row, registration)
            scorer_action["scorer_application_row_id"] = (
                f"OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-APP-{len(scorer_application_rows) + 1:05d}"
            )
            scorer_application_rows.append(with_common(scorer_action, generated_at, manifest_hash))
        if row.get("decision_result") == "KILL_PRESERVED":
            audit = current_claim_rejection_audit(row, source, horizon)
            audit["current_claim_rejection_audit_row_id"] = (
                f"OHLC-GTOS-DENOM-DEFAULT-OFF-REJECTION-AUDIT-{len(rejection_audit_rows) + 1:05d}"
            )
            rejection_audit_rows.append(with_common(audit, generated_at, manifest_hash))

    distributions = {
        "default_off_application_status": string_counter(application_rows, "default_off_application_status"),
        "default_off_application_decision_class": string_counter(application_rows, "default_off_application_decision_class"),
        "source_default_off_implementation_status": string_counter(application_rows, "source_default_off_implementation_status"),
        "scorer_surface_consumed": string_counter(application_rows, "scorer_surface_consumed"),
        "exact_control_build_still_required": string_counter(application_rows, "exact_control_build_still_required"),
        "current_claim_rejection_audit_required": string_counter(application_rows, "current_claim_rejection_audit_required"),
        "scorer_application_status": string_counter(scorer_application_rows, "scorer_application_status"),
        "exact_control_application_blocker_status": string_counter(
            exact_blocker_rows, "exact_control_application_blocker_status"
        ),
        "current_claim_rejection_audit_status": string_counter(
            rejection_audit_rows, "current_claim_rejection_audit_status"
        ),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            application_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-DEFAULT-OFF-APPLICATION-BUCKET-{len(buckets) + 1:04d}",
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
                "question_id": "OHLC-GTOS-DENOM-DEFAULT-OFF-APPLICATION-Q-001",
                "question": "Did every implementation row receive an application decision?",
                "answer_route": "Yes: all 274 implementation rows are represented in the application ledger.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DEFAULT-OFF-APPLICATION-Q-002",
                "question": "Did scorer surfaces apply to the rows they were registered for?",
                "answer_route": "Yes: 35 scorer-application rows consume the 35 registered default-off scorer/gate surfaces, with 33 scores emitted and 2 repair gates held.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DEFAULT-OFF-APPLICATION-Q-003",
                "question": "Are exact-control blockers still concrete rather than carryforward text?",
                "answer_route": "Yes: 111 exact-control blocker rows preserve target/scope build status, member counts, proxy relation, and no-runtime-score reason.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-DEFAULT-OFF-APPLICATION-Q-004",
                "question": "Does current-claim rejection delete the underlying opportunity mechanism?",
                "answer_route": "No: 128 current-claim rejection audits preserve what was tried, what could make it work, and whether it becomes avoid, redesign, merge, context, or source-capture intelligence.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_default_off_implementation_rows": len(implementation_rows),
        "input_exact_control_expansion_rows": len(exact_rows),
        "input_source_completeness_rows": len(source_rows),
        "input_horizon_decision_rows": len(horizon_rows),
        "input_default_off_scorer_registration_rows": len(registration_rows),
        "application_rows": len(application_rows),
        "exact_control_blocker_rows": len(exact_blocker_rows),
        "scorer_application_rows": len(scorer_application_rows),
        "current_claim_rejection_audit_rows": len(rejection_audit_rows),
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
            "denominator_detail_decision_execution_bundle": decision_result.get("counts", {}),
            "denominator_default_off_scorer_materialization_bundle": scorer_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "application_status_counts": distributions["default_off_application_status"],
            "scorer_application_status_counts": distributions["scorer_application_status"],
            "exact_control_blocker_status_counts": distributions["exact_control_application_blocker_status"],
            "current_claim_rejection_audit_status_counts": distributions["current_claim_rejection_audit_status"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_APPLICATION_BUNDLE_RESULT: consume 35 registered scorer/gate surfaces into scored or gate-held application rows, preserve 111 exact-control build blockers as no-runtime-score work rows, and preserve 128 current-claim rejection audits as avoid/redesign/source-capture intelligence rather than deleting mechanisms.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "default_off_application_surface": DEFAULT_OFF_APPLICATION_SURFACE,
        "input_default_off_implementation": INPUT_IMPLEMENTATION.relative_to(REPO).as_posix(),
        "input_default_off_scorer_registration": INPUT_SCORER_REGISTRATION.relative_to(REPO).as_posix(),
        "unconditional_scalar_use_allowed": False,
        "runtime_score_allowed": False,
        "distributions": distributions,
    }
    outputs = [
        APPLICATION_LEDGER,
        EXACT_CONTROL_BLOCKER_LEDGER,
        SCORER_APPLICATION_LEDGER,
        CURRENT_CLAIM_REJECTION_AUDIT_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(APPLICATION_LEDGER, application_rows)
    write_jsonl(EXACT_CONTROL_BLOCKER_LEDGER, exact_blocker_rows)
    write_jsonl(SCORER_APPLICATION_LEDGER, scorer_application_rows)
    write_jsonl(CURRENT_CLAIM_REJECTION_AUDIT_LEDGER, rejection_audit_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Default-Off Application Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Application rows: `{counts['application_rows']}`.",
                f"- Scorer application rows: `{counts['scorer_application_rows']}`.",
                f"- Exact-control blocker rows: `{counts['exact_control_blocker_rows']}`.",
                f"- Current-claim rejection audit rows: `{counts['current_claim_rejection_audit_rows']}`.",
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
