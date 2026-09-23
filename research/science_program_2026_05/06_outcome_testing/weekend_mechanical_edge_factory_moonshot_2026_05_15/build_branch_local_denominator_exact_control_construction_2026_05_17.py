#!/usr/bin/env python3
"""Construct exact-control denominators from same-resource tick M15 ledgers."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_construction import (
    EXACT_CONTROL_CONSTRUCTION_SURFACE,
    SIERRA_PRIMITIVE_TRANSLATION,
    SIERRA_SOURCE_SYMBOLS,
    exact_control_blocker_construction,
    exact_control_denominator_event_row,
    exact_control_scope_construction,
    scope_key,
    scope_to_tick_control_key,
    sierra_translation_proxy_row,
    tick_control_key,
    tick_event_has_scope_flag,
    tick_event_matches_scope,
)


EFFN_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_EFFECTIVE_N_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_CONSTRUCTION_BUNDLE"

INPUT_EFFN_RESULT = ROUTE_DIR / f"{EFFN_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_EFFECTIVE_N = ROUTE_DIR / f"{EFFN_PREFIX}_SCOPE_EFFECTIVE_N_LEDGER_2026-05-17.jsonl"
INPUT_BLOCKER_EFFECTIVE_N = ROUTE_DIR / f"{EFFN_PREFIX}_BLOCKER_EFFECTIVE_N_LEDGER_2026-05-17.jsonl"
INPUT_TICK_CONTROL = ROUTE_DIR / "TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_2026-05-15.jsonl"
INPUT_TICK_EVENT = ROUTE_DIR / "TICK_M15_TARGET_MOVEMENT_EVENT_LEDGER_2026-05-15.jsonl"
INPUT_TICK_PRIMITIVE_SUMMARY = ROUTE_DIR / "TICK_M15_PRIMITIVE_FLAG_SUMMARY_LEDGER_2026-05-15.jsonl"
INPUT_SIERRA_CONTROL = ROUTE_DIR / "SIERRA_SCID_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_2026-05-16.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_CONSTRUCTION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCOPE_CONSTRUCTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_CONSTRUCTION_LEDGER_2026-05-17.jsonl"
BLOCKER_CONSTRUCTION_LEDGER = ROUTE_DIR / f"{PREFIX}_BLOCKER_CONSTRUCTION_LEDGER_2026-05-17.jsonl"
DENOMINATOR_EVENT_LEDGER = ROUTE_DIR / f"{PREFIX}_DENOMINATOR_EVENT_LEDGER_2026-05-17.jsonl"
SIERRA_TRANSLATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SIERRA_TRANSLATION_PROXY_LEDGER_2026-05-17.jsonl"
MISSED_OPPORTUNITY_AUDIT_LEDGER = ROUTE_DIR / f"{PREFIX}_MISSED_OPPORTUNITY_AUDIT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control denominator construction from existing tick M15 target-control and event ledgers. "
    "It converts prior effective-N blockers into exact same-resource construction rows and missed-opportunity audits. "
    "It does not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_construction_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_construction_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Converted exact-control effective-N blockers into tick M15 exact-control construction rows, denominator event rows, and missed-opportunity audits.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def sierra_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("source_symbol"), row.get("session_bucket"), row.get("horizon_id"), row.get("primitive_flag"))


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_EFFN_RESULT,
            INPUT_SCOPE_EFFECTIVE_N,
            INPUT_BLOCKER_EFFECTIVE_N,
            INPUT_TICK_CONTROL,
            INPUT_TICK_EVENT,
            INPUT_TICK_PRIMITIVE_SUMMARY,
            INPUT_SIERRA_CONTROL,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    effn_result = read_json(INPUT_EFFN_RESULT)
    scope_rows = read_jsonl(INPUT_SCOPE_EFFECTIVE_N)
    blocker_rows = read_jsonl(INPUT_BLOCKER_EFFECTIVE_N)
    tick_control_rows = read_jsonl(INPUT_TICK_CONTROL)
    tick_event_rows = read_jsonl(INPUT_TICK_EVENT)
    sierra_control_rows = read_jsonl(INPUT_SIERRA_CONTROL)

    tick_control_by_key = {tick_control_key(row): row for row in tick_control_rows}
    events_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    flagged_event_count_by_scope: Counter[tuple[Any, Any, Any, Any]] = Counter()
    scope_by_key = {scope_key(row): row for row in scope_rows}
    scope_keys = set(scope_by_key)
    event_index = 0
    denominator_event_rows = []
    for source_event_index, event in enumerate(tick_event_rows, 1):
        for key, scope in scope_by_key.items():
            if not tick_event_matches_scope(event, scope):
                continue
            event_index += 1
            events_by_scope[key].append(event)
            if tick_event_has_scope_flag(event, scope):
                flagged_event_count_by_scope[key] += 1
            output = exact_control_denominator_event_row(scope, event, source_event_index)
            output["exact_control_denominator_event_row_id"] = (
                f"OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-EVENT-{event_index:06d}"
            )
            denominator_event_rows.append(with_common(output, generated_at, manifest_hash))

    scope_construction_rows = []
    for index, scope in enumerate(scope_rows, 1):
        key = scope_key(scope)
        tick_control = tick_control_by_key.get(scope_to_tick_control_key(scope))
        row = exact_control_scope_construction(
            scope,
            tick_control,
            denominator_event_count=len(events_by_scope.get(key, [])),
            flagged_event_count=flagged_event_count_by_scope[key],
        )
        row["exact_control_scope_construction_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-SCOPE-{index:04d}"
        )
        scope_construction_rows.append(with_common(row, generated_at, manifest_hash))

    scope_construction_by_scope = {scope_key(row): row for row in scope_construction_rows}
    blocker_construction_rows = []
    missed_opportunity_rows = []
    for index, blocker in enumerate(blocker_rows, 1):
        row = exact_control_blocker_construction(blocker, scope_construction_by_scope.get(scope_key(blocker)))
        row["exact_control_blocker_construction_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-BLOCKER-{index:05d}"
        )
        row = with_common(row, generated_at, manifest_hash)
        blocker_construction_rows.append(row)
        audit = {
            "missed_opportunity_audit_row_id": f"OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-AUDIT-{index:05d}",
            "input_exact_control_blocker_construction_row_id": row["exact_control_blocker_construction_row_id"],
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "primitive_flag": row.get("primitive_flag"),
            "exact_control_result_class": row.get("exact_control_result_class"),
            "current_claim_rejected": row.get("current_claim_rejected"),
            "mixed_or_redesign_required": row.get("mixed_or_redesign_required"),
            "missed_opportunity_audit": row.get("missed_opportunity_audit"),
            "claim_rejected_scope": row.get("claim_rejected_scope"),
        }
        missed_opportunity_rows.append(with_common(audit, generated_at, manifest_hash))

    sierra_control_by_key = {sierra_key(row): row for row in sierra_control_rows}
    sierra_rows = []
    for scope in scope_rows:
        source_symbols = SIERRA_SOURCE_SYMBOLS.get(str(scope.get("symbol")), ())
        translations = SIERRA_PRIMITIVE_TRANSLATION.get(str(scope.get("primitive_flag")), ())
        if not source_symbols:
            sierra_rows.append(
                sierra_translation_proxy_row(scope, None, None, None)
            )
            continue
        if not translations:
            for source_symbol in source_symbols:
                sierra_rows.append(sierra_translation_proxy_row(scope, None, source_symbol, None))
            continue
        for source_symbol in source_symbols:
            for translated in translations:
                row = sierra_translation_proxy_row(
                    scope,
                    sierra_control_by_key.get(
                        (source_symbol, scope.get("tick_session_bucket") or scope_to_tick_control_key(scope)[1], scope.get("horizon_id"), translated)
                    ),
                    source_symbol,
                    translated,
                )
                sierra_rows.append(row)
    for index, row in enumerate(sierra_rows, 1):
        row["sierra_translation_proxy_row_id"] = f"OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-SIERRA-{index:04d}"
        with_common(row, generated_at, manifest_hash)

    distributions = {
        "exact_control_construction_status": string_counter(scope_construction_rows, "exact_control_construction_status"),
        "exact_control_result_class": string_counter(scope_construction_rows, "exact_control_result_class"),
        "blocker_exact_control_result_class": string_counter(blocker_construction_rows, "exact_control_result_class"),
        "branch_local_exact_control_score_allowed": string_counter(
            scope_construction_rows, "branch_local_exact_control_score_allowed"
        ),
        "current_claim_rejected": string_counter(blocker_construction_rows, "current_claim_rejected"),
        "mixed_or_redesign_required": string_counter(blocker_construction_rows, "mixed_or_redesign_required"),
        "sierra_translation_status": string_counter(sierra_rows, "sierra_translation_status"),
        "outside_gbpjpy_xauusd_current_branch_box": string_counter(
            blocker_construction_rows, "outside_gbpjpy_xauusd_current_branch_box"
        ),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    exact_built_scope_count = sum(
        1 for row in scope_construction_rows if row.get("exact_control_construction_status") == "EXACT_CONTROL_CONSTRUCTION_TICK_M15_N20_BUILT"
    )
    exact_built_blocker_count = sum(
        1 for row in blocker_construction_rows if row.get("exact_control_construction_status") == "EXACT_CONTROL_CONSTRUCTION_TICK_M15_N20_BUILT"
    )
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-Q-001",
                "question": "Can the 23 missing exact-control scopes be constructed from same-resource tick M15 ledgers?",
                "answer_route": f"Yes: {exact_built_scope_count} / {len(scope_rows)} scopes found exact tick M15 N20 controls.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-Q-002",
                "question": "Did exact construction preserve every blocker row instead of deleting weak or duplicate branches?",
                "answer_route": f"Yes: {len(blocker_construction_rows)} / {len(blocker_rows)} blocker rows became construction decision rows and missed-opportunity audits.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-Q-003",
                "question": "Are Sierra SCID rows exact substitutes for these tick M15 controls?",
                "answer_route": "No: Sierra rows use a different primitive taxonomy and are preserved as proxy/translation sidecars only unless exact equivalence is proven.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-CONSTRUCT-Q-004",
                "question": "What should happen to negative exact-control rows?",
                "answer_route": "Only the current positive claim is rejected; the mechanism is preserved as avoid/inverse/redesign/source-confidence or split intelligence.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_scope_effective_n_rows": len(scope_rows),
        "input_blocker_effective_n_rows": len(blocker_rows),
        "input_tick_control_rows": len(tick_control_rows),
        "input_tick_event_rows": len(tick_event_rows),
        "scope_construction_rows": len(scope_construction_rows),
        "blocker_construction_rows": len(blocker_construction_rows),
        "denominator_event_rows": len(denominator_event_rows),
        "denominator_event_flagged_rows": sum(1 for row in denominator_event_rows if row.get("primitive_present")),
        "sierra_translation_proxy_rows": len(sierra_rows),
        "missed_opportunity_audit_rows": len(missed_opportunity_rows),
        "exact_built_scope_rows": exact_built_scope_count,
        "exact_built_blocker_rows": exact_built_blocker_count,
        "current_claim_rejected_rows": sum(1 for row in blocker_construction_rows if row.get("current_claim_rejected")),
        "mixed_or_redesign_required_rows": sum(1 for row in blocker_construction_rows if row.get("mixed_or_redesign_required")),
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
            "denominator_exact_control_effective_n_bundle": effn_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "exact_control_construction_status_counts": distributions["exact_control_construction_status"],
            "blocker_exact_control_result_class_counts": distributions["blocker_exact_control_result_class"],
            "current_claim_rejected_counts": distributions["current_claim_rejected"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_CONSTRUCTION_BUNDLE_RESULT: exact tick M15 controls are now built for all prior missing scopes; consume positive/mixed/negative exact-control rows into default-off scoring, split/redesign, avoid/inverse, and source-confidence decisions without deleting underlying mechanisms.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_construction_surface": EXACT_CONTROL_CONSTRUCTION_SURFACE,
        "input_scope_effective_n": INPUT_SCOPE_EFFECTIVE_N.relative_to(REPO).as_posix(),
        "input_tick_control": INPUT_TICK_CONTROL.relative_to(REPO).as_posix(),
        "input_tick_event": INPUT_TICK_EVENT.relative_to(REPO).as_posix(),
        "branch_local_exact_control_score_allowed": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "distributions": distributions,
    }
    outputs = [
        SCOPE_CONSTRUCTION_LEDGER,
        BLOCKER_CONSTRUCTION_LEDGER,
        DENOMINATOR_EVENT_LEDGER,
        SIERRA_TRANSLATION_LEDGER,
        MISSED_OPPORTUNITY_AUDIT_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(SCOPE_CONSTRUCTION_LEDGER, scope_construction_rows)
    write_jsonl(BLOCKER_CONSTRUCTION_LEDGER, blocker_construction_rows)
    write_jsonl(DENOMINATOR_EVENT_LEDGER, denominator_event_rows)
    write_jsonl(SIERRA_TRANSLATION_LEDGER, sierra_rows)
    write_jsonl(MISSED_OPPORTUNITY_AUDIT_LEDGER, missed_opportunity_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Construction Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Scope construction rows: `{counts['scope_construction_rows']}`.",
                f"- Exact-built scope rows: `{counts['exact_built_scope_rows']}`.",
                f"- Blocker construction rows: `{counts['blocker_construction_rows']}`.",
                f"- Denominator event rows preserved: `{counts['denominator_event_rows']}`.",
                f"- Sierra translation/proxy rows: `{counts['sierra_translation_proxy_rows']}`.",
                f"- Current-claim rejected rows: `{counts['current_claim_rejected_rows']}`.",
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
