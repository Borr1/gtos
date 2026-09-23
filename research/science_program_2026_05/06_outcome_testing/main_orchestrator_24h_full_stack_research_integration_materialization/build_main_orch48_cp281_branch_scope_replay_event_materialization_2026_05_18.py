from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_BRANCH_SCOPE_REPLAY_EVENT_MATERIALIZATION"
SCHEMA_VERSION = "main_orch48_cp281_branch_scope_replay_event_materialization_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_frozen_universe_cp281_runtime_mapping import (  # noqa: E402
    CP281BranchDecisionRegistry,
    DEFAULT_BRANCH_DECISION_LEDGER,
    build_branch_scope_replay_event_rows,
    build_branch_scope_replay_match_rows,
    read_jsonl,
    summarize_branch_scope_replay_materialization,
)


HELPER = REPO / "src/research_infra/moonshot_frozen_universe_cp281_runtime_mapping.py"
TEST_FILE = REPO / "tests/research_infra/test_moonshot_frozen_universe_cp281_runtime_mapping.py"
OUTPUT_EVENT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_EVENT_LEDGER_{DATE}.jsonl"
OUTPUT_MATCH_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_MATCH_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = ["test_branch_scope_replay_materialization_preserves_duplicate_conflicts"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def source_surface(path: Path) -> dict[str, Any]:
    full = REPO / path
    return {
        "path": display_path(full),
        "exists": full.exists(),
        "bytes": full.stat().st_size if full.exists() else 0,
        "lines": count_lines(full) if full.exists() else 0,
        "sha256": sha256_path(full) if full.exists() else None,
    }


def test_coverage(test_text: str) -> dict[str, bool]:
    return {name: name in test_text for name in EXPECTED_TEST_NAMES}


def build() -> dict[str, Any]:
    generated_at = utc_now()
    branch_decision_rows = read_jsonl(REPO / DEFAULT_BRANCH_DECISION_LEDGER)
    registry = CP281BranchDecisionRegistry(branch_decision_rows)
    event_rows = build_branch_scope_replay_event_rows(branch_decision_rows)
    match_rows = build_branch_scope_replay_match_rows(event_rows, registry=registry)
    write_jsonl(OUTPUT_EVENT_LEDGER, event_rows)
    write_jsonl(OUTPUT_MATCH_LEDGER, match_rows)

    tests = test_coverage(TEST_FILE.read_text(encoding="utf-8"))
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at,
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "source_surfaces": [source_surface(DEFAULT_BRANCH_DECISION_LEDGER)],
        "code_surfaces": [
            code_surface(HELPER),
            code_surface(TEST_FILE),
            code_surface(Path(__file__)),
        ],
        **summarize_branch_scope_replay_materialization(event_rows=event_rows, match_rows=match_rows),
        "source_evidence_role": (
            "CP281_NATIVE_REPLAY_EVENT_MATERIALIZATION_FROM_CP280_CP281_HISTORICAL_READY_SLICE"
        ),
        "live_shadow_matching_role": "SECONDARY_EVENT_FIELD_INTEGRATION_EVIDENCE_ONLY_NOT_STRATEGY_EVIDENCE",
        "expected_test_name_coverage": tests,
        "expected_test_names_covered_rows": sum(tests.values()),
        "can_continue_to_historical_replay_execution": True,
    }
    summary["schema_version"] = SCHEMA_VERSION
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_EVENT_LEDGER, OUTPUT_MATCH_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at,
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "branch_scope_replay_event_rows": summary["branch_scope_replay_event_rows"],
        "branch_scope_replay_match_rows": summary["branch_scope_replay_match_rows"],
        "duplicate_scope_event_rows": summary["duplicate_scope_event_rows"],
        "action_conflict_match_rows": summary["action_conflict_match_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
