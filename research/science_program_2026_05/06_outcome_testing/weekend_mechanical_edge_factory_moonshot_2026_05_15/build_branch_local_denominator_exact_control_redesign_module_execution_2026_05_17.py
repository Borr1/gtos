#!/usr/bin/env python3
"""Execute exact-control redesign module slots against runtime events."""

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

from src.research_infra.moonshot_branch_local_denominator_exact_control_redesign_module_execution import (
    EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_SURFACE,
    redesign_code_surface_execution,
    redesign_event_module_execution,
    redesign_scope_module_execution,
    scope_key,
)


MODULE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_BUNDLE"
RUNTIME_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_RUNTIME_ROUTER_BUNDLE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_BUNDLE"

INPUT_MODULE_RESULT = ROUTE_DIR / f"{MODULE_PREFIX}_RESULT_2026-05-17.json"
INPUT_SCOPE_MODULE = ROUTE_DIR / f"{MODULE_PREFIX}_SCOPE_MODULE_LEDGER_2026-05-17.jsonl"
INPUT_CODE_SURFACE = ROUTE_DIR / f"{MODULE_PREFIX}_CODE_SURFACE_LEDGER_2026-05-17.jsonl"
INPUT_RUNTIME_EVENTS = ROUTE_DIR / f"{RUNTIME_PREFIX}_EVENT_RUNTIME_ROUTING_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
SCOPE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_EXECUTION_LEDGER_2026-05-17.jsonl"
EVENT_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_EXECUTION_LEDGER_2026-05-17.jsonl"
CODE_SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_CODE_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local exact-control redesign module-execution bundle. It executes default-off module slots against "
    "runtime event/control denominators. It does not change live behavior, place orders, or claim broker R/PnL, "
    "realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-SRC-{index:04d}",
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
    manifest["latest_branch_local_denominator_exact_control_redesign_module_execution_bundle"] = {
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
        "event": "branch_local_denominator_exact_control_redesign_module_execution_bundle_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Executed exact-control redesign module slots against runtime event/control denominators.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            INPUT_MODULE_RESULT,
            INPUT_SCOPE_MODULE,
            INPUT_CODE_SURFACE,
            INPUT_RUNTIME_EVENTS,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
        ],
        generated_at,
    )
    module_result = read_json(INPUT_MODULE_RESULT)
    scope_module_rows = read_jsonl(INPUT_SCOPE_MODULE)
    code_surface_rows = read_jsonl(INPUT_CODE_SURFACE)
    runtime_event_rows = read_jsonl(INPUT_RUNTIME_EVENTS)

    events_by_scope: dict[tuple[Any, Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in runtime_event_rows:
        events_by_scope[scope_key(row)].append(row)

    scope_execution_rows = []
    for index, scope_module in enumerate(scope_module_rows, 1):
        row = redesign_scope_module_execution(scope_module, events_by_scope.get(scope_key(scope_module), []))
        row["exact_control_redesign_scope_module_execution_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-SCOPE-{index:04d}"
        )
        scope_execution_rows.append(with_common(row, generated_at, manifest_hash))
    execution_by_scope = {scope_key(row): row for row in scope_execution_rows}

    event_execution_rows = []
    for index, event in enumerate(runtime_event_rows, 1):
        row = redesign_event_module_execution(event, execution_by_scope.get(scope_key(event)))
        row["exact_control_redesign_event_module_execution_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-EVENT-{index:06d}"
        )
        event_execution_rows.append(with_common(row, generated_at, manifest_hash))

    code_surface_by_scope = {scope_key(row): row for row in code_surface_rows}
    code_surface_execution_rows = []
    for index, scope_execution in enumerate(scope_execution_rows, 1):
        code_surface = code_surface_by_scope.get(scope_key(scope_execution), {})
        row = redesign_code_surface_execution(code_surface, scope_execution)
        row["exact_control_redesign_code_surface_execution_row_id"] = (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-CODE-{index:04d}"
        )
        code_surface_execution_rows.append(with_common(row, generated_at, manifest_hash))

    distributions = {
        "module_execution_status": string_counter(scope_execution_rows, "module_execution_status"),
        "event_module_execution_status": string_counter(event_execution_rows, "event_module_execution_status"),
        "module_scope_relation": string_counter(event_execution_rows, "module_scope_relation"),
        "module_slot": string_counter(scope_execution_rows, "module_slot"),
        "code_surface_execution_status": string_counter(code_surface_execution_rows, "code_surface_execution_status"),
    }
    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    relation_counts = distributions["module_scope_relation"]
    counts = {
        "input_scope_module_rows": len(scope_module_rows),
        "input_code_surface_rows": len(code_surface_rows),
        "input_runtime_event_rows": len(runtime_event_rows),
        "scope_execution_rows": len(scope_execution_rows),
        "event_execution_rows": len(event_execution_rows),
        "code_surface_execution_rows": len(code_surface_execution_rows),
        "module_scope_event_rows": relation_counts.get("MODULE_SCOPE_SIGNAL_EVENT", 0)
        + relation_counts.get("MODULE_SCOPE_CONTROL_EVENT", 0),
        "module_scope_signal_event_rows": relation_counts.get("MODULE_SCOPE_SIGNAL_EVENT", 0),
        "module_scope_control_event_rows": relation_counts.get("MODULE_SCOPE_CONTROL_EVENT", 0),
        "non_module_scope_context_event_rows": relation_counts.get("NON_MODULE_SCOPE_CONTEXT_EVENT", 0),
        "bucket_rows": len(buckets),
        "question_rows": 4,
        "source_manifest_rows": len(source_manifest),
        "runtime_spec_rows": 1,
    }
    questions = [
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-Q-001",
                "question": "Were module slots executed against the full runtime event denominator?",
                "answer_route": f"Yes: {counts['event_execution_rows']} runtime events were preserved, including {counts['module_scope_event_rows']} module-scope events.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-Q-002",
                "question": "Were same-scope controls preserved for module execution deltas?",
                "answer_route": f"Yes: {counts['module_scope_control_event_rows']} same-scope control events were preserved alongside {counts['module_scope_signal_event_rows']} signal events.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-Q-003",
                "question": "Did code-surface execution inflate blocker lineage?",
                "answer_route": f"No: {counts['code_surface_execution_rows']} code-surface executions match the {counts['scope_execution_rows']} scope executions, not blocker count.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-EXEC-Q-004",
                "question": "What remains next?",
                "answer_route": "Consume executed module slots into final branch-local scorer/redesign registry or compare module deltas against existing default-off scorer scopes.",
            },
            generated_at,
            manifest_hash,
        ),
    ]
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {
            "denominator_exact_control_redesign_module_integration_bundle": module_result.get("counts", {}),
        },
        "bucket_distributions": distributions,
        "system_decision": {
            "module_execution_status_counts": distributions["module_execution_status"],
            "event_execution_status_counts": distributions["event_module_execution_status"],
            "module_scope_relation_counts": distributions["module_scope_relation"],
            "module_slot_counts": distributions["module_slot"],
            "system_recommendation": "BRANCH_LOCAL_DENOMINATOR_EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_BUNDLE_RESULT: consume executed module slots into final default-off registry or module-delta comparator next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "exact_control_redesign_module_execution_surface": EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "module_scope_relation_counts": distributions["module_scope_relation"],
        "event_execution_status_counts": distributions["event_module_execution_status"],
    }
    outputs = [
        SCOPE_EXECUTION_LEDGER,
        EVENT_EXECUTION_LEDGER,
        CODE_SURFACE_EXECUTION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        RUNTIME_SPEC_PATH,
    ]
    write_jsonl(SCOPE_EXECUTION_LEDGER, scope_execution_rows)
    write_jsonl(EVENT_EXECUTION_LEDGER, event_execution_rows)
    write_jsonl(CODE_SURFACE_EXECUTION_LEDGER, code_surface_execution_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Denominator Exact-Control Redesign Module Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Scope execution rows: `{counts['scope_execution_rows']}`.",
                f"- Event execution rows: `{counts['event_execution_rows']}`.",
                f"- Module-scope signal/control rows: `{counts['module_scope_signal_event_rows']}` / `{counts['module_scope_control_event_rows']}`.",
                f"- Non-module context event rows: `{counts['non_module_scope_context_event_rows']}`.",
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
