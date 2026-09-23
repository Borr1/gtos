#!/usr/bin/env python3
"""Build branch-local implementation candidates from implementation-priority rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_impl_candidates import (
    EXPANDED_MARKET_IMPL_CANDIDATES,
    aggregate_key,
    aggregate_rows_from_buckets,
    boundary_row,
    empty_bucket,
    evidence_preservation_row,
    implementation_candidate_input,
    implementation_candidate_row,
    issue_rows,
    research_boundary,
    self_test_row,
    update_bucket,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_PRIORITY"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_CANDIDATES"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_ROW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_impl_candidates.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_impl_candidates_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
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


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = [
        (RESULT_PATH, "expanded_market_impl_candidates_result"),
        (CANDIDATE_LEDGER, "expanded_market_impl_candidate_rows"),
        (EVIDENCE_LEDGER, "expanded_market_impl_candidate_evidence"),
        (SELF_TEST_LEDGER, "expanded_market_impl_candidate_self_tests"),
        (AGGREGATE_LEDGER, "expanded_market_impl_candidate_aggregates"),
        (ISSUE_LEDGER, "expanded_market_impl_candidate_issues"),
        (SYSTEM_LEDGER, "expanded_market_impl_candidate_system"),
        (SUMMARY_PATH, "expanded_market_impl_candidate_summary"),
        (BUILDER_MODULE, "expanded_market_impl_candidate_builder"),
        (VERIFIER_MODULE, "expanded_market_impl_candidate_verifier"),
        (HELPER_MODULE, "expanded_market_impl_candidate_helper"),
        (TEST_MODULE, "expanded_market_impl_candidate_tests"),
    ]
    rows = [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]
    existing = manifest.setdefault("artifacts", [])
    types = {row["type"] for row in rows}
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + rows
    manifest["latest_expanded_market_impl_candidates"] = {
        "generated_utc": generated_at,
        "files": rows,
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
    marker = "## Checkpoint 256 - Expanded-Market Implementation Candidates"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 255. Positive alternate-source repair priority rows were materialized as branch-local implementation candidates with scope self-tests; all other priority rows were preserved as row-addressable numeric evidence.

Rows:
- input implementation-priority rows: {counts["input_implementation_priority_rows"]}
- implementation candidate rows: {counts["implementation_candidate_rows"]}
- preserved evidence rows: {counts["preserved_evidence_rows"]}
- self-test rows: {counts["self_test_rows"]}
- self-test pass rows: {counts["self_test_pass_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: execute the branch-local implementation candidates against held implementation-priority rows and preserve all evidence and mismatch rows.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any], result: dict[str, Any]) -> str:
    return f"""# Expanded-Market Implementation Candidates

Generated: {generated_at}

## Inputs

- Implementation-priority rows: `{counts["input_implementation_priority_rows"]}`

## Outputs

- Implementation candidate rows: `{counts["implementation_candidate_rows"]}`
- Preserved evidence rows: `{counts["preserved_evidence_rows"]}`
- Self-test rows: `{counts["self_test_rows"]}`
- Self-test pass rows: `{counts["self_test_pass_rows"]}`
- Aggregate rows: `{counts["aggregate_rows"]}`
- Issue rows: `{counts["issue_rows"]}`

## Result

- ok: `{result["ok"]}`
- issues: `{result["issues"]}`
"""


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    candidate_class_counts: Counter[str] = Counter()
    evidence_class_counts: Counter[str] = Counter()
    priority_tier_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    source_paths: set[str] = set()
    symbol_families: set[str] = set()
    issues: list[dict[str, Any]] = []
    input_rows = 0
    candidate_rows = 0
    evidence_rows = 0
    self_test_rows = 0
    self_test_pass_rows = 0

    with (
        open(long_path(CANDIDATE_LEDGER), "w", encoding="utf-8", newline="\n") as candidate_handle,
        open(long_path(EVIDENCE_LEDGER), "w", encoding="utf-8", newline="\n") as evidence_handle,
        open(long_path(SELF_TEST_LEDGER), "w", encoding="utf-8", newline="\n") as self_test_handle,
    ):
        for input_rows, source_row in enumerate(iter_jsonl(INPUT_ROW_LEDGER), 1):
            source_paths.add(str(source_row.get("source_path") or ""))
            symbol_families.add(str(source_row.get("symbol_family") or ""))
            priority_tier_counts[source_row.get("implementation_priority_tier")] += 1
            if implementation_candidate_input(source_row):
                candidate_rows += 1
                candidate = implementation_candidate_row(source_row, candidate_rows)
                self_test_rows += 1
                test = self_test_row(candidate, source_row, self_test_rows)
                candidate_handle.write(json.dumps(candidate, sort_keys=True) + "\n")
                self_test_handle.write(json.dumps(test, sort_keys=True) + "\n")
                candidate_class_counts[candidate.get("implementation_priority_class")] += 1
                decision_counts[candidate.get("keep_kill_redesign_implement_decision")] += 1
                update_bucket(buckets[aggregate_key(candidate, "candidate")], candidate, "candidate")
                if test.get("self_test_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_PASS":
                    self_test_pass_rows += 1
                issues.extend(issue_rows([candidate], [test]))
            else:
                evidence_rows += 1
                evidence = evidence_preservation_row(source_row, evidence_rows)
                evidence_handle.write(json.dumps(evidence, sort_keys=True) + "\n")
                evidence_class_counts[evidence.get("evidence_preservation_class")] += 1
                decision_counts[evidence.get("keep_kill_redesign_implement_decision")] += 1
                update_bucket(buckets[aggregate_key(evidence, "evidence")], evidence, "evidence")

    aggregate_rows = aggregate_rows_from_buckets(buckets)
    system_rows = [
        boundary_row(
            {
                "expanded_market_impl_candidate_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-IMPL-SYSTEM-0001"
                ),
                "input_implementation_priority_rows": input_rows,
                "implementation_candidate_rows": candidate_rows,
                "preserved_evidence_rows": evidence_rows,
                "self_test_rows": self_test_rows,
                "self_test_pass_rows": self_test_pass_rows,
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issues),
                "candidate_class_counts": dict(sorted(candidate_class_counts.items())),
                "evidence_class_counts": dict(sorted(evidence_class_counts.items())),
                "priority_tier_counts": dict(sorted(priority_tier_counts.items())),
                "decision_counts": dict(sorted(decision_counts.items())),
                "source_path_count": len(source_paths),
                "symbol_family_count": len(symbol_families),
                "metadata": {
                    "input_implementation_priority_result_ok": input_result.get("ok"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    counts = {
        "input_implementation_priority_rows": input_rows,
        "implementation_candidate_rows": candidate_rows,
        "preserved_evidence_rows": evidence_rows,
        "self_test_rows": self_test_rows,
        "self_test_pass_rows": self_test_pass_rows,
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "candidate_class_counts": dict(sorted(candidate_class_counts.items())),
        "evidence_class_counts": dict(sorted(evidence_class_counts.items())),
        "priority_tier_counts": dict(sorted(priority_tier_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_path_count": len(source_paths),
        "symbol_family_count": len(symbol_families),
        "system_rows": len(system_rows),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "expanded_market_impl_candidates_surface": EXPANDED_MARKET_IMPL_CANDIDATES,
        "research_boundary": research_boundary(),
        "inputs": {
            "implementation_priority_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "implementation_priority_rows": str(INPUT_ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "evidence_ledger": str(EVIDENCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "counts": counts,
    }
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts, result))
    result["output_sha256"] = output_sha256(
        [
            CANDIDATE_LEDGER,
            EVIDENCE_LEDGER,
            SELF_TEST_LEDGER,
            AGGREGATE_LEDGER,
            ISSUE_LEDGER,
            SYSTEM_LEDGER,
            SUMMARY_PATH,
        ]
    )
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "event": "checkpoint_256_expanded_market_impl_candidates",
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
