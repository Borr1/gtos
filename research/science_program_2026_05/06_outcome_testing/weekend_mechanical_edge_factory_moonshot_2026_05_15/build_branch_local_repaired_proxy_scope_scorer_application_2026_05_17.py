#!/usr/bin/env python3
"""Apply repaired-proxy scope scorer registry to all numeric shadow events."""

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

from src.research_infra.moonshot_repaired_proxy_scope_scorer import (
    REPAIRED_PROXY_SCOPE_SCORER_SURFACE,
    application_summary_row,
    build_registry,
    event_application_row,
    registry_row_from_decision,
)


BROKER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_BROKER_SOURCE_REPAIR_EXPECTANCY"
SHADOW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_NUMERIC_SHADOW_SCORER_COMPUTE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION"

BROKER_RESULT = ROUTE_DIR / f"{BROKER_PREFIX}_RESULT_2026-05-17.json"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / f"{BROKER_PREFIX}_IMPLEMENTATION_DECISION_LEDGER_2026-05-17.jsonl"
REPAIR_RESULT_LEDGER = ROUTE_DIR / f"{BROKER_PREFIX}_REPAIR_RESULT_LEDGER_2026-05-17.jsonl"
EVENT_SCORE_LEDGER = ROUTE_DIR / f"{SHADOW_PREFIX}_NUMERIC_EVENT_SCORE_LEDGER_2026-05-17.jsonl"
SHADOW_RESULT = ROUTE_DIR / f"{SHADOW_PREFIX}_RESULT_2026-05-17.json"

HELPER_MODULE = REPO / "src/research_infra/moonshot_repaired_proxy_scope_scorer.py"
BUILDER_MODULE = Path(__file__)
BROKER_HELPER_MODULE = REPO / "src/research_infra/moonshot_broker_source_repair.py"
BROKER_BUILDER_MODULE = ROUTE_DIR / "build_branch_local_broker_source_repair_expectancy_2026_05_17.py"
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTABLE_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_EXECUTABLE_SPEC_2026-05-17.json"
REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRY_LEDGER_2026-05-17.jsonl"
EVENT_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_APPLICATION_LEDGER_2026-05-17.jsonl"
DEFAULT_OFF_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_SCORE_LEDGER_2026-05-17.jsonl"
AVOID_REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_REDESIGN_LEDGER_2026-05-17.jsonl"
REPAIR_REQUIRED_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_REQUIRED_LEDGER_2026-05-17.jsonl"
APPLICATION_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_APPLICATION_SUMMARY_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local repaired-proxy scope scorer application. This artifact consumes broker/source repair implementation "
    "decisions into a callable repaired-proxy scope registry and applies it to every numeric shadow event, producing "
    "default-off score rows, avoid/redesign comparator rows, repair-required rows, and full summaries. It is research-only "
    "and has no live behavior."
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
                "source_manifest_id": f"OHLC-GTOS-REPAIRED-PROXY-SCOPE-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "generated_utc": generated_at,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
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
    return {value: int(counter[value]) for value in sorted(counter)}


def grouped_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("symbol_session_horizon_source", ("symbol", "route_session", "horizon_id", "source_component")),
        ("registry_role", ("registry_role",)),
        ("event_status", ("repaired_proxy_event_status",)),
        ("source_component", ("source_component",)),
    ]
    output: list[dict[str, Any]] = []
    for family, fields in specs:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row.get(field) for field in fields)].append(row)
        for key, grouped in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
            output.append(application_summary_row(grouped, key, fields, len(output) + 1, family))
    return output


def bucket_rows(
    registry_rows: list[dict[str, Any]],
    application_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    specs = [
        ("registry_role", registry_rows, "registry_role"),
        ("implementation_decision", registry_rows, "implementation_decision"),
        ("event_status", application_rows, "repaired_proxy_event_status"),
        ("event_action", application_rows, "repaired_proxy_event_action"),
        ("score_source", application_rows, "repaired_proxy_event_score_source"),
        ("source_component", application_rows, "source_component"),
        ("symbol", application_rows, "symbol"),
    ]
    rows: list[dict[str, Any]] = []
    distributions: dict[str, dict[str, int]] = {}
    for bucket_name, source, key in specs:
        counter = string_counter(source, key)
        distributions[bucket_name] = counter
        for value, count in counter.items():
            rows.append(
                with_common(
                    {
                        "bucket_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCOPE-BUCKET-{len(rows) + 1:04d}",
                        "bucket_name": bucket_name,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return rows, distributions


def question_rows(generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    questions = [
        ("Which repaired scopes emit default-off scores now?", "consume default-off score ledger by symbol/session/horizon/source_component"),
        ("Which repaired scopes force avoid/redesign behavior now?", "consume avoid/redesign ledger and compare against default-off score ledger"),
        ("Which repaired scopes still fail closed for source or broker geometry?", "consume repair-required ledger and split direct-identifier versus source-rebuild requirements"),
        ("Which symbols/sessions concentrate repaired proxy scores?", "consume full application summary ledger with no row truncation"),
    ]
    return [
        with_common(
            {
                "repaired_proxy_scope_question_id": f"OHLC-GTOS-REPAIRED-PROXY-SCOPE-Q-{index:04d}",
                "question": question,
                "next_action": action,
            },
            generated_at,
            manifest_hash,
        )
        for index, (question, action) in enumerate(questions, 1)
    ]


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS})
    manifest["latest_branch_local_repaired_proxy_scope_scorer_application"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    event = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "repaired_proxy_scope_scorer_applied",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Registered repaired-proxy scope scorer behavior and applied it to every numeric shadow event.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Repaired Proxy Scope Scorer Application",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Event Status", ""])
    for status, count in result["bucket_distributions"]["event_status"].items():
        lines.append(f"- `{status}`: `{count}`")
    write_text(SUMMARY_PATH, "\n".join(lines) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows(
        [
            BROKER_RESULT,
            IMPLEMENTATION_DECISION_LEDGER,
            REPAIR_RESULT_LEDGER,
            EVENT_SCORE_LEDGER,
            SHADOW_RESULT,
            HELPER_MODULE,
            BUILDER_MODULE,
            BROKER_HELPER_MODULE,
            BROKER_BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    broker_result = read_json(BROKER_RESULT)
    shadow_result = read_json(SHADOW_RESULT)
    implementation_rows = read_jsonl(IMPLEMENTATION_DECISION_LEDGER)
    repair_rows = read_jsonl(REPAIR_RESULT_LEDGER)
    event_rows = read_jsonl(EVENT_SCORE_LEDGER)

    registry_rows = [
        with_common(registry_row_from_decision(row, index), generated_at, manifest_hash)
        for index, row in enumerate(implementation_rows, 1)
    ]
    registry = build_registry(registry_rows)
    repairs_by_numeric: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in repair_rows:
        repairs_by_numeric[str(row.get("input_numeric_result_row_id"))].append(row)

    application_rows = [
        with_common(
            event_application_row(
                row,
                registry["by_scope"].get(str(row.get("aggregate_scope_key") or "")),
                repairs_by_numeric.get(str(row.get("input_numeric_result_row_id")), []),
                index,
            ),
            generated_at,
            manifest_hash,
        )
        for index, row in enumerate(event_rows, 1)
    ]
    default_rows = [row for row in application_rows if row.get("emits_default_off_score")]
    avoid_rows = [row for row in application_rows if row.get("emits_avoid_or_redesign")]
    repair_required_rows = [row for row in application_rows if row.get("emits_source_repair_required")]
    summary_rows = [with_common(row, generated_at, manifest_hash) for row in grouped_summaries(application_rows)]
    buckets, distributions = bucket_rows(registry_rows, application_rows, generated_at, manifest_hash)
    questions = question_rows(generated_at, manifest_hash)

    outputs = [
        RESULT_PATH,
        EXECUTABLE_SPEC_PATH,
        REGISTRY_LEDGER,
        EVENT_APPLICATION_LEDGER,
        DEFAULT_OFF_LEDGER,
        AVOID_REDESIGN_LEDGER,
        REPAIR_REQUIRED_LEDGER,
        APPLICATION_SUMMARY_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    counts = {
        "input_implementation_decision_rows": len(implementation_rows),
        "input_repair_result_rows": len(repair_rows),
        "input_event_score_rows": len(event_rows),
        "registry_rows": len(registry_rows),
        "event_application_rows": len(application_rows),
        "default_off_score_rows": len(default_rows),
        "avoid_redesign_rows": len(avoid_rows),
        "repair_required_rows": len(repair_required_rows),
        "application_summary_rows": len(summary_rows),
        "bucket_rows": len(buckets),
        "question_rows": len(questions),
        "source_manifest_rows": len(source_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "repaired_proxy_scope_scorer_surface": REPAIRED_PROXY_SCOPE_SCORER_SURFACE,
        "counts": counts,
        "upstream_counts": {
            "broker_source_repair_expectancy": broker_result["counts"],
            "numeric_shadow_scorer_compute": shadow_result["counts"],
        },
        "bucket_distributions": distributions,
        "all_implementation_decisions_registered": counts["registry_rows"] == broker_result["counts"]["implementation_decision_rows"],
        "all_numeric_shadow_events_applied": counts["event_application_rows"] == shadow_result["counts"]["numeric_event_score_rows"],
        "event_outputs_partition_full_denominator": (
            counts["default_off_score_rows"] + counts["avoid_redesign_rows"] + counts["repair_required_rows"]
            == counts["event_application_rows"]
        ),
        "no_summary_only_terminal_rows": all(
            row.get("summary_only_terminal") is False
            for row in registry_rows + application_rows + summary_rows
        ),
    }
    executable_spec = {
        "artifact": f"{PREFIX}_EXECUTABLE_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "callable_surface": REPAIRED_PROXY_SCOPE_SCORER_SURFACE,
        "callables": [
            "registry_row_from_decision",
            "build_registry",
            "score_event_with_repaired_scope",
            "event_application_row",
            "application_summary_row",
        ],
        "input_implementation_decisions": IMPLEMENTATION_DECISION_LEDGER.relative_to(REPO).as_posix(),
        "input_event_rows": EVENT_SCORE_LEDGER.relative_to(REPO).as_posix(),
        "output_event_application_rows": EVENT_APPLICATION_LEDGER.relative_to(REPO).as_posix(),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(EXECUTABLE_SPEC_PATH, json.dumps(executable_spec, indent=2, sort_keys=True) + "\n")
    write_jsonl(REGISTRY_LEDGER, registry_rows)
    write_jsonl(EVENT_APPLICATION_LEDGER, application_rows)
    write_jsonl(DEFAULT_OFF_LEDGER, default_rows)
    write_jsonl(AVOID_REDESIGN_LEDGER, avoid_rows)
    write_jsonl(REPAIR_REQUIRED_LEDGER, repair_required_rows)
    write_jsonl(APPLICATION_SUMMARY_LEDGER, summary_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_rows)
    write_summary(result)
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
