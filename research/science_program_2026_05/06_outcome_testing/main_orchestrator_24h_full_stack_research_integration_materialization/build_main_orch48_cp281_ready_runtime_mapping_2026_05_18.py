from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING"
SCHEMA_VERSION = "main_orch48_cp281_ready_runtime_mapping_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
MOONSHOT_ROOT = Path("C:/tmp/")
MOONSHOT_ROUTE_RELATIVE = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
MOONSHOT_ROUTE_DIR = MOONSHOT_ROOT / MOONSHOT_ROUTE_RELATIVE

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_frozen_universe_cp281_runtime_mapping import (  # noqa: E402
    SCHEMA_VERSION as MAPPING_SCHEMA_VERSION,
    build_aggregate_mapping_rows,
    build_registry_self_check_rows,
    build_rule_mapping_rows,
    build_source_capture_contract_rows,
    read_jsonl,
    summarize_mapping,
)


CP281_RESULT = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME_RESULT_2026-05-17.json"
CP281_RULES = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME_RULE_LEDGER_2026-05-17.jsonl"
CP281_SELF_TESTS = (
    "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME_SELF_TEST_LEDGER_2026-05-17.jsonl"
)
CP281_AGGREGATES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME_AGGREGATE_LEDGER_2026-05-17.jsonl"
)

HELPER = REPO / "src/research_infra/moonshot_frozen_universe_cp281_runtime_mapping.py"
TEST_FILE = REPO / "tests/research_infra/test_moonshot_frozen_universe_cp281_runtime_mapping.py"
OUTPUT_RULE_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_RULE_LEDGER_{DATE}.jsonl"
OUTPUT_AGGREGATE_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_AGGREGATE_LEDGER_{DATE}.jsonl"
OUTPUT_SOURCE_CONTRACT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_SOURCE_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_SELF_CHECK_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_SELF_CHECK_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_rule_mapping_preserves_follow_and_avoid_rows_with_controls",
    "test_registry_evaluates_self_events_and_keeps_default_off_controls",
    "test_source_capture_contract_and_self_check_cover_each_rule",
    "test_aggregate_rows_and_summary_preserve_counts",
]


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


def moonshot_display(filename: str) -> str:
    return str(MOONSHOT_ROUTE_RELATIVE / filename).replace("\\", "/")


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


def run_git_in_moonshot(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "-c", "safe.directory=C:/tmp/", "-C", str(MOONSHOT_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "args": ["git", "-c", "safe.directory=C:/tmp/", "-C", str(MOONSHOT_ROOT), *args],
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


def source_inventory() -> dict[str, dict[str, Any]]:
    files = {
        "cp281_result": CP281_RESULT,
        "cp281_rules": CP281_RULES,
        "cp281_self_tests": CP281_SELF_TESTS,
        "cp281_aggregates": CP281_AGGREGATES,
    }
    inventory: dict[str, dict[str, Any]] = {}
    for key, filename in files.items():
        path = MOONSHOT_ROUTE_DIR / filename
        inventory[key] = {
            "path": moonshot_display(filename),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "lines": count_lines(path) if path.exists() else 0,
            "sha256": sha256_path(path) if path.exists() else None,
        }
    return inventory


def test_coverage(test_text: str) -> dict[str, bool]:
    return {name: name in test_text for name in EXPECTED_TEST_NAMES}


def build() -> dict[str, Any]:
    generated_at = utc_now()
    moonshot_head_result = run_git_in_moonshot("rev-parse", "HEAD")
    moonshot_status_result = run_git_in_moonshot("status", "--short")
    moonshot_head = moonshot_head_result["stdout"]
    moonshot_status_clean = moonshot_status_result["returncode"] == 0 and not moonshot_status_result["stdout"]
    inventory = source_inventory()
    cp281_result = json.loads((MOONSHOT_ROUTE_DIR / CP281_RESULT).read_text(encoding="utf-8"))
    rule_source_rows = read_jsonl(MOONSHOT_ROUTE_DIR / CP281_RULES)
    self_test_source_rows = read_jsonl(MOONSHOT_ROUTE_DIR / CP281_SELF_TESTS)
    aggregate_source_rows = read_jsonl(MOONSHOT_ROUTE_DIR / CP281_AGGREGATES)

    rule_mapping_rows = build_rule_mapping_rows(
        rule_source_rows,
        self_test_source_rows,
        source_rule_artifact=moonshot_display(CP281_RULES),
        source_rule_artifact_sha256=inventory["cp281_rules"]["sha256"],
        source_self_test_artifact=moonshot_display(CP281_SELF_TESTS),
        source_self_test_artifact_sha256=inventory["cp281_self_tests"]["sha256"],
        moonshot_head=moonshot_head,
        moonshot_status_clean=moonshot_status_clean,
    )
    aggregate_mapping_rows = build_aggregate_mapping_rows(
        aggregate_source_rows,
        source_aggregate_artifact=moonshot_display(CP281_AGGREGATES),
        source_aggregate_artifact_sha256=inventory["cp281_aggregates"]["sha256"],
        moonshot_head=moonshot_head,
        moonshot_status_clean=moonshot_status_clean,
    )
    source_contract_rows = build_source_capture_contract_rows(rule_mapping_rows)
    self_check_rows = build_registry_self_check_rows(rule_mapping_rows)

    write_jsonl(OUTPUT_RULE_LEDGER, rule_mapping_rows)
    write_jsonl(OUTPUT_AGGREGATE_LEDGER, aggregate_mapping_rows)
    write_jsonl(OUTPUT_SOURCE_CONTRACT_LEDGER, source_contract_rows)
    write_jsonl(OUTPUT_SELF_CHECK_LEDGER, self_check_rows)

    tests = test_coverage(TEST_FILE.read_text(encoding="utf-8"))
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at,
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "moonshot_git_head": moonshot_head_result,
        "moonshot_git_status": moonshot_status_result,
        "moonshot_head": moonshot_head,
        "moonshot_status_clean": moonshot_status_clean,
        "moonshot_root": str(MOONSHOT_ROOT),
        "moonshot_route_relative": str(MOONSHOT_ROUTE_RELATIVE).replace("\\", "/"),
        "source_inventory": inventory,
        "code_surfaces": [
            code_surface(HELPER),
            code_surface(TEST_FILE),
            code_surface(Path(__file__)),
        ],
        **summarize_mapping(
            rule_mapping_rows=rule_mapping_rows,
            aggregate_mapping_rows=aggregate_mapping_rows,
            source_capture_contract_rows=source_contract_rows,
            registry_self_check_rows=self_check_rows,
            cp281_result_counts=cp281_result.get("counts") or {},
            moonshot_head=moonshot_head,
            moonshot_status_clean=moonshot_status_clean,
        ),
        "mapping_schema_version": MAPPING_SCHEMA_VERSION,
        "expected_test_name_coverage": tests,
        "expected_test_names_covered_rows": sum(tests.values()),
        "stale_cp215_cp223_not_controlling": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [
        OUTPUT_RULE_LEDGER,
        OUTPUT_AGGREGATE_LEDGER,
        OUTPUT_SOURCE_CONTRACT_LEDGER,
        OUTPUT_SELF_CHECK_LEDGER,
        OUTPUT_SUMMARY,
    ]
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
        "rule_mapping_rows": len(rule_mapping_rows),
        "aggregate_mapping_rows": len(aggregate_mapping_rows),
        "source_contract_rows": len(source_contract_rows),
        "self_check_rows": len(self_check_rows),
        "moonshot_head": moonshot_head,
        "moonshot_status_clean": moonshot_status_clean,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
