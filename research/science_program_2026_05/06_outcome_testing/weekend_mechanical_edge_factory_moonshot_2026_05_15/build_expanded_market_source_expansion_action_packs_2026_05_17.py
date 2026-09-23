#!/usr/bin/env python3
"""Build branch-local action packs from expanded-market action applications."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_source_expansion_action_packs import (
    EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS,
    action_pack_row,
    action_pack_self_test_row,
    aggregate_action_pack_rows,
    boundary_row,
    is_applied_action,
    replay_work_row,
    research_boundary,
)


APPLICATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS"

APPLICATION_RESULT = ROUTE_DIR / f"{APPLICATION_PREFIX}_RESULT_2026-05-17.json"
APPLICATION_ROW_LEDGER = ROUTE_DIR / f"{APPLICATION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
APPLICATION_RULE_LEDGER = ROUTE_DIR / f"{APPLICATION_PREFIX}_RULE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_packs.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_action_packs_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PACK_LEDGER = ROUTE_DIR / f"{PREFIX}_PACK_LEDGER_2026-05-17.jsonl"
WORK_LEDGER = ROUTE_DIR / f"{PREFIX}_WORK_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"


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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_source_expansion_action_packs_result"),
        (PACK_LEDGER, "expanded_market_source_expansion_action_packs"),
        (WORK_LEDGER, "expanded_market_source_expansion_action_pack_replay_work"),
        (SELF_TEST_LEDGER, "expanded_market_source_expansion_action_pack_self_tests"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_action_pack_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_action_pack_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_action_pack_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_action_pack_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_action_pack_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_action_pack_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_action_pack_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_action_pack_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    types = {entry["type"] for entry in entries}
    existing = manifest.setdefault("artifacts", [])
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + entries
    manifest["latest_expanded_market_source_expansion_action_packs"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept_lines: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    kept_lines.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept_lines.append(json.dumps(row, sort_keys=True))
    kept_lines.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 270 - Expanded-Market Source Expansion Action Packs"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 269. Applied action rows were materialized into executable branch-local research action packs with self-tests. Every non-pack row was preserved as concrete replay/source work with missing fields.

Rows:
- input action-application rows: {counts["input_application_rows"]}
- action packs: {counts["action_pack_rows"]}
- pack self-tests: {counts["self_test_rows"]}
- replay/source work rows: {counts["replay_work_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute action packs against branch-local candidate surfaces and use work rows as row-level replay/source tasks.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Action Packs",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint materializes applied CP269 action rows into branch-local research action packs and preserves every non-pack row as concrete replay/source work.",
            "",
            "## Counts",
            "",
            f"- Input action-application rows: `{counts['input_application_rows']}`",
            f"- Action packs: `{counts['action_pack_rows']}`",
            f"- Pack self-tests: `{counts['self_test_rows']}`",
            f"- Replay/source work rows: `{counts['replay_work_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
            "## Pack Kinds",
            "",
            f"`{json.dumps(counts['pack_kind_counts'], sort_keys=True)}`",
            "",
            "## Work Status",
            "",
            f"`{json.dumps(counts['work_status_counts'], sort_keys=True)}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    application_result = read_json(APPLICATION_RESULT)
    input_rows = 0
    pack_rows: list[dict[str, Any]] = []
    work_rows: list[dict[str, Any]] = []
    self_tests: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for row in iter_jsonl(APPLICATION_ROW_LEDGER):
        input_rows += 1
        if is_applied_action(row):
            pack = action_pack_row(row, len(pack_rows) + 1)
            pack_rows.append(pack)
            self_test = action_pack_self_test_row(pack, row, len(self_tests) + 1)
            self_tests.append(self_test)
            if self_test.get("self_test_status") != "ACTION_PACK_SELF_TEST_PASS":
                issues.append(
                    boundary_row(
                        {
                            "expanded_market_source_expansion_action_pack_issue_row_id": (
                                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-ISSUE-{len(issues) + 1:07d}"
                            ),
                            "issue_type": "ACTION_PACK_SELF_TEST_FAILURE",
                            "input_action_pack_row_id": pack.get(
                                "expanded_market_source_expansion_action_pack_row_id"
                            ),
                        }
                    )
                )
        else:
            work_rows.append(replay_work_row(row, len(work_rows) + 1))

    aggregates = aggregate_action_pack_rows(pack_rows, work_rows)
    pack_kinds = Counter(row.get("action_pack_kind") for row in pack_rows)
    work_status = Counter(row.get("work_status") for row in work_rows)
    decisions = Counter(
        [row.get("keep_kill_redesign_implement_decision") for row in pack_rows]
        + [row.get("keep_kill_redesign_implement_decision") for row in work_rows]
    )
    counts = {
        "input_application_result_ok": application_result.get("ok"),
        "input_application_rows": input_rows,
        "input_action_rule_rows": sum(1 for _ in iter_jsonl(APPLICATION_RULE_LEDGER)),
        "action_pack_rows": len(pack_rows),
        "replay_work_rows": len(work_rows),
        "self_test_rows": len(self_tests),
        "self_test_pass_rows": sum(
            row.get("self_test_status") == "ACTION_PACK_SELF_TEST_PASS" for row in self_tests
        ),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issues),
        "system_rows": 1,
        "pack_rows_with_simulated_r": sum(
            row.get("cost_adjusted_simulated_r") is not None for row in pack_rows
        ),
        "work_rows_with_simulated_r": sum(
            row.get("cost_adjusted_simulated_r") is not None for row in work_rows
        ),
        "symbol_count": len({row.get("symbol") for row in pack_rows + work_rows}),
        "source_path_count": len({row.get("source_path") for row in pack_rows + work_rows}),
        "pack_kind_counts": dict(sorted(pack_kinds.items())),
        "work_status_counts": dict(sorted(work_status.items())),
        "decision_counts": dict(sorted(decisions.items())),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_action_pack_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "application_row_ledger": str(APPLICATION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "application_rule_ledger": str(APPLICATION_RULE_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        PACK_LEDGER,
        WORK_LEDGER,
        SELF_TEST_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(PACK_LEDGER, pack_rows)
    write_jsonl(WORK_LEDGER, work_rows)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts))
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "inputs": {
            "application_result": str(APPLICATION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "application_row_ledger": str(APPLICATION_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "application_rule_ledger": str(APPLICATION_RULE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "pack_ledger": str(PACK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "work_ledger": str(WORK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_action_pack_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 270,
            "event": "checkpoint_270_expanded_market_source_expansion_action_packs",
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
