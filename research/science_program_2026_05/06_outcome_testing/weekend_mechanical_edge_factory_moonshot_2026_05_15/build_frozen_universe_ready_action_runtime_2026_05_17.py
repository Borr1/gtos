#!/usr/bin/env python3
"""Materialize frozen implementation-ready actions into branch-local runtime rules."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_frozen_universe_ready_action_runtime import (
    FROZEN_UNIVERSE_READY_ACTION_RUNTIME_SURFACE,
    aggregate_rules,
    boundary_row,
    ready_action_runtime_rule,
    research_boundary,
    self_test_row,
    status_counts,
)


CLOSURE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME"
DATE = "2026-05-17"

INPUT_RESULT = ROUTE_DIR / f"{CLOSURE_PREFIX}_RESULT_{DATE}.json"
INPUT_READY_LEDGER = ROUTE_DIR / f"{CLOSURE_PREFIX}_IMPLEMENTATION_READY_BUNDLE_LEDGER_{DATE}.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
RULE_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_LEDGER_{DATE}.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_{DATE}.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_{DATE}.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"
HELPER_MODULE = REPO / "src/research_infra/moonshot_frozen_universe_ready_action_runtime.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_frozen_universe_ready_action_runtime_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line.lstrip("\ufeff"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digests[path.name] = hasher.hexdigest()
    return digests


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "frozen_universe_ready_action_runtime_result"),
        (RULE_LEDGER, "frozen_universe_ready_action_runtime_rules"),
        (SELF_TEST_LEDGER, "frozen_universe_ready_action_runtime_self_tests"),
        (AGGREGATE_LEDGER, "frozen_universe_ready_action_runtime_aggregates"),
        (ISSUE_LEDGER, "frozen_universe_ready_action_runtime_issues"),
        (SYSTEM_LEDGER, "frozen_universe_ready_action_runtime_system"),
        (SUMMARY_PATH, "frozen_universe_ready_action_runtime_summary"),
        (BUILDER_MODULE, "frozen_universe_ready_action_runtime_builder"),
        (VERIFIER_MODULE, "frozen_universe_ready_action_runtime_verifier"),
        (HELPER_MODULE, "frozen_universe_ready_action_runtime_helper"),
        (TEST_MODULE, "frozen_universe_ready_action_runtime_tests"),
    ]
    return [
        {"path": rel(path), "status": "created", "type": artifact_type}
        for path, artifact_type in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    types = {entry["type"] for entry in entries}
    existing = manifest.setdefault("artifacts", [])
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + entries
    manifest["latest_frozen_universe_ready_action_runtime"] = {
        "generated_utc": generated_at,
        "result": rel(RESULT_PATH),
        "files": entries,
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line.lstrip("\ufeff"))
                except json.JSONDecodeError:
                    kept.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept.append(json.dumps(row, sort_keys=True))
    kept.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 281 - Frozen-Universe Ready Action Runtime Rules"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after CP280 closure. The frozen implementation-ready bundle was consumed into branch-local executable follow/avoid rule rows with self-tests and aggregate scopes that main can directly consume.

Rows:
- input implementation-ready bundle rows: {counts["input_ready_rows"]}
- runtime rule rows: {counts["rule_rows"]}
- self-test rows: {counts["self_test_rows"]}
- self-test pass rows: {counts["self_test_pass_rows"]}
- aggregate scope rows: {counts["aggregate_rows"]}
- source rows represented: {counts["source_rows_represented"]}
- issue rows: {counts["issue_rows"]}

Output packet:
- `{rel(RESULT_PATH)}`
- `{rel(RULE_LEDGER)}`
- `{rel(SELF_TEST_LEDGER)}`
- `{rel(AGGREGATE_LEDGER)}`
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    ready_rows = list(iter_jsonl(INPUT_READY_LEDGER))
    rules = [ready_action_runtime_rule(row, index) for index, row in enumerate(ready_rows, start=1)]
    self_tests = [self_test_row(row, index) for index, row in enumerate(rules, start=1)]
    aggregates = aggregate_rules(rules)
    issues: list[dict[str, Any]] = []
    for row in rules:
        if row.get("missing_match_fields"):
            issues.append(
                boundary_row(
                    {
                        "frozen_ready_action_runtime_issue_row_id": (
                            f"FROZEN-MOONSHOT-READY-ACTION-RUNTIME-ISSUE-{len(issues)+1:07d}"
                        ),
                        "input_runtime_rule_row_id": row.get(
                            "frozen_ready_action_runtime_rule_row_id"
                        ),
                        "issue": "missing_match_fields",
                        "missing_match_fields": row.get("missing_match_fields"),
                    }
                )
            )
    for row in self_tests:
        if row.get("self_test_status") != "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS":
            issues.append(
                boundary_row(
                    {
                        "frozen_ready_action_runtime_issue_row_id": (
                            f"FROZEN-MOONSHOT-READY-ACTION-RUNTIME-ISSUE-{len(issues)+1:07d}"
                        ),
                        "input_runtime_rule_row_id": row.get("input_runtime_rule_row_id"),
                        "issue": "self_test_failed",
                        "self_test_status": row.get("self_test_status"),
                    }
                )
            )

    counts = {
        "input_closure_result_ok": input_result.get("ok") is True,
        "input_ready_rows": len(ready_rows),
        "rule_rows": len(rules),
        "self_test_rows": len(self_tests),
        "self_test_pass_rows": sum(
            1
            for row in self_tests
            if row.get("self_test_status") == "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS"
        ),
        "aggregate_rows": len(aggregates),
        "source_rows_represented": sum(int(row.get("source_action_closure_row_count") or 0) for row in rules),
        "action_class_counts": status_counts(rules, "action_class"),
        "self_test_status_counts": status_counts(self_tests, "self_test_status"),
        "issue_rows": len(issues),
    }
    system = boundary_row(
        {
            "system_row_id": "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-SYSTEM-0000001",
            "generated_utc": generated_at,
            "input_ready_ledger": rel(INPUT_READY_LEDGER),
            "builder": rel(BUILDER_MODULE),
            "helper": FROZEN_UNIVERSE_READY_ACTION_RUNTIME_SURFACE,
            "boundary": research_boundary(),
            "counts": counts,
        }
    )
    outputs = [RULE_LEDGER, SELF_TEST_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER]
    write_jsonl(RULE_LEDGER, rules)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, [system])

    result = boundary_row(
        {
            "ok": not issues and input_result.get("ok") is True,
            "generated_utc": generated_at,
            "input_result": rel(INPUT_RESULT),
            "input_ready_ledger": rel(INPUT_READY_LEDGER),
            "counts": counts,
            "output_sha256": output_sha256(outputs),
        }
    )
    write_json(RESULT_PATH, result)
    write_text(
        SUMMARY_PATH,
        f"""# Frozen Universe Ready Action Runtime

Generated: {generated_at}

Consumed all {counts["input_ready_rows"]} CP280 implementation-ready bundle rows into branch-local executable runtime rule rows that main can directly consume.

## Counts
- Runtime rule rows: {counts["rule_rows"]}
- Self-test rows: {counts["self_test_rows"]}
- Self-test pass rows: {counts["self_test_pass_rows"]}
- Aggregate scope rows: {counts["aggregate_rows"]}
- Source rows represented: {counts["source_rows_represented"]}
- Action classes: {counts["action_class_counts"]}
- Issue rows: {counts["issue_rows"]}
""",
    )

    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_281_frozen_universe_ready_action_runtime",
            "checkpoint": 281,
            "generated_utc": generated_at,
            "result": rel(RESULT_PATH),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()
