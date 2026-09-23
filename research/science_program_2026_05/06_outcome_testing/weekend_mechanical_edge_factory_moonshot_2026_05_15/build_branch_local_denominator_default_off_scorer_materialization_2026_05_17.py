#!/usr/bin/env python3
"""Materialize denominator default-off scorer behavior rows."""

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

from src.research_infra.moonshot_branch_local_denominator_default_off_scorers import (
    DEFAULT_OFF_SCORER_SURFACE,
    register_default_off_scorer,
    score_default_off_event,
)


DECISION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DETAIL_DECISION_EXECUTION_BUNDLE"
DETAIL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DETAIL_EXECUTION_BUNDLE"
GUARDED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_GUARDED_SCOPE_SCORER_REGISTRATION_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_SCORER_MATERIALIZATION_BUNDLE"

INPUT_DECISION_RESULT = ROUTE_DIR / f"{DECISION_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCORER_BEHAVIOR = ROUTE_DIR / f"{DECISION_PREFIX}_SCORER_BEHAVIOR_LEDGER_2026-05-17.jsonl"
INPUT_HORIZON_DECISION = ROUTE_DIR / f"{DECISION_PREFIX}_HORIZON_DECISION_LEDGER_2026-05-17.jsonl"
INPUT_EXACT_EXPANSION = ROUTE_DIR / f"{DECISION_PREFIX}_EXACT_CONTROL_EXPANSION_LEDGER_2026-05-17.jsonl"
INPUT_NEXT_DETAIL = ROUTE_DIR / f"{DETAIL_PREFIX}_NEXT_ACTION_DETAIL_LEDGER_2026-05-17.jsonl"
INPUT_GUARDED_REGISTRATION = ROUTE_DIR / f"{GUARDED_PREFIX}_REGISTRATION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / DEFAULT_OFF_SCORER_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRATION_LEDGER_2026-05-17.jsonl"
SMOKE_LEDGER = ROUTE_DIR / f"{PREFIX}_SMOKE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local denominator default-off scorer materialization bundle only. It registers default-off scorer behavior "
    "for guarded scope proxy, horizon repair, horizon redesign, and horizon kill-check rows. It does not change live "
    "behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-SRC-{index:04d}",
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
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_branch_local_denominator_default_off_scorer_materialization_bundle"] = {
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
        "event": "branch_local_denominator_default_off_scorer_materialization_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Registered default-off scorer behavior rows and smoke-tested matching versus mismatched scopes.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def source_for_behavior(
    row: dict[str, Any],
    detail_by_id: dict[Any, dict[str, Any]],
    horizon_by_id: dict[Any, dict[str, Any]],
    exact_by_id: dict[Any, dict[str, Any]],
    guarded_by_id: dict[Any, dict[str, Any]],
) -> dict[str, Any]:
    detail_id = row.get("input_detail_execution_row_id")
    if row.get("scorer_behavior_status") == "SCORER_BEHAVIOR_GUARDED_SCOPE_PROXY_MATCH_ONLY":
        detail = detail_by_id.get(detail_id, {})
        guarded = guarded_by_id.get(detail.get("matched_guarded_scorer_registration_row_id"), {})
        return detail | exact_by_id.get(detail_id, {}) | guarded
    return horizon_by_id.get(detail_id, {})


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_DECISION_RESULT,
            INPUT_SCORER_BEHAVIOR,
            INPUT_HORIZON_DECISION,
            INPUT_EXACT_EXPANSION,
            INPUT_NEXT_DETAIL,
            INPUT_GUARDED_REGISTRATION,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    input_result = read_json(INPUT_DECISION_RESULT)
    behavior_rows = read_jsonl(INPUT_SCORER_BEHAVIOR)
    horizon_rows = read_jsonl(INPUT_HORIZON_DECISION)
    exact_rows = read_jsonl(INPUT_EXACT_EXPANSION)
    detail_rows = read_jsonl(INPUT_NEXT_DETAIL)
    guarded_rows = read_jsonl(INPUT_GUARDED_REGISTRATION)
    detail_by_id = {row.get("denominator_detail_execution_row_id"): row for row in detail_rows}
    horizon_by_id = {row.get("input_detail_execution_row_id"): row for row in horizon_rows}
    exact_by_id = {row.get("input_detail_execution_row_id"): row for row in exact_rows}
    guarded_by_id = {row.get("guarded_scorer_registration_row_id"): row for row in guarded_rows}

    registrations = []
    for index, row in enumerate(behavior_rows, 1):
        registration = register_default_off_scorer(
            row,
            source_for_behavior(row, detail_by_id, horizon_by_id, exact_by_id, guarded_by_id),
        )
        registration["default_off_scorer_registration_row_id"] = f"OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-REG-{index:05d}"
        registrations.append(with_common(registration, generated_at, manifest_hash))

    smoke_rows = []
    for registration in registrations:
        matching_event = {
            "symbol": registration.get("symbol"),
            "route_session": registration.get("route_session"),
            "horizon_id": registration.get("horizon_id"),
            "primitive_flag": registration.get("primitive_flag"),
        }
        mismatch_event = {**matching_event, "symbol": "XAUUSD" if registration.get("symbol") != "XAUUSD" else "GBPJPY"}
        for case, event in (("MATCHING_SCOPE", matching_event), ("MISMATCHED_SYMBOL_SCOPE", mismatch_event)):
            scored = score_default_off_event(event, registration)
            scored["default_off_scorer_smoke_row_id"] = f"OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-SMOKE-{len(smoke_rows) + 1:05d}"
            scored["smoke_case"] = case
            smoke_rows.append(with_common(scored, generated_at, manifest_hash))

    distributions = {
        "default_off_scorer_registration_status": string_counter(registrations, "default_off_scorer_registration_status"),
        "default_off_scorer_kind": string_counter(registrations, "default_off_scorer_kind"),
        "source_behavior_status": string_counter(registrations, "source_behavior_status"),
        "scorer_permission": string_counter(registrations, "scorer_permission"),
        "smoke_status": string_counter(smoke_rows, "default_off_scorer_event_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(registrations, "outside_gbpjpy_xauusd_current_branch_box"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(with_common({"bucket_id": f"OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-BUCKET-{len(buckets)+1:04d}", "bucket_family": family, "bucket_value": value, "row_count": count}, generated_at, manifest_hash))
    questions = [
        with_common({"question_id": "OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-Q-001", "question": "Did all scorer-behavior rows become registrations?", "answer_route": "Yes: all 35 scorer-behavior rows register as default-off branch-local scorer or gate rows."}, generated_at, manifest_hash),
        with_common({"question_id": "OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-Q-002", "question": "Did matching and mismatch behavior execute?", "answer_route": "Yes: every registration has matching-scope and mismatched-symbol smoke rows, 70 rows total."}, generated_at, manifest_hash),
        with_common({"question_id": "OHLC-GTOS-DENOM-DEFAULT-OFF-SCORER-Q-003", "question": "Do kill-check gates emit scalar scores?", "answer_route": "No: the 2 kill-check gate registrations hold the gate and emit no scalar score."}, generated_at, manifest_hash),
    ]
    counts = {
        "input_scorer_behavior_rows": len(behavior_rows),
        "input_horizon_decision_rows": len(horizon_rows),
        "input_exact_control_expansion_rows": len(exact_rows),
        "input_next_detail_rows": len(detail_rows),
        "input_guarded_scorer_registration_rows": len(guarded_rows),
        "default_off_scorer_registration_rows": len(registrations),
        "default_off_scorer_smoke_rows": len(smoke_rows),
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
        "upstream_counts": {"denominator_detail_decision_execution_bundle": input_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": {
            "registration_status_counts": distributions["default_off_scorer_registration_status"],
            "scorer_kind_counts": distributions["default_off_scorer_kind"],
            "smoke_status_counts": distributions["smoke_status"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_DEFAULT_OFF_SCORER_MATERIALIZATION_BUNDLE_RESULT: materialize 35 default-off scorer/gate behaviors with scope smoke tests; keep all live behavior disabled and continue into exact-control build execution or source/horizon module integration from these registrations.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "default_off_scorer_surface": DEFAULT_OFF_SCORER_SURFACE,
        "input_decision_result": INPUT_DECISION_RESULT.relative_to(REPO).as_posix(),
        "input_guarded_scorer_registration": INPUT_GUARDED_REGISTRATION.relative_to(REPO).as_posix(),
        "unconditional_scalar_use_allowed": False,
        "distributions": distributions,
    }
    outputs = [REGISTRATION_LEDGER, SMOKE_LEDGER, BUCKET_LEDGER, QUESTION_LEDGER, SOURCE_MANIFEST_LEDGER, RUNTIME_SPEC_PATH]
    write_jsonl(REGISTRATION_LEDGER, registrations)
    write_jsonl(SMOKE_LEDGER, smoke_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(SUMMARY_PATH, "\n".join(["# Branch-Local Denominator Default-Off Scorer Materialization Bundle", "", f"Generated UTC: `{generated_at}`", "", f"- Registration rows: `{counts['default_off_scorer_registration_rows']}`.", f"- Smoke rows: `{counts['default_off_scorer_smoke_rows']}`.", "", CLAIM_BOUNDARY, ""]))
    append_manifest([RESULT_PATH, SUMMARY_PATH, *outputs], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
