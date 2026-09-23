from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL"
SCHEMA_VERSION = "main_orch48_ai_trace_trade_record_backfill_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.ai_decision_trace_backfill import (  # noqa: E402
    SCHEMA_VERSION as BACKFILL_SCHEMA_VERSION,
    build_trade_record_ai_trace_backfill_rows,
    iter_trade_record_paths,
    summarize_trade_record_ai_trace_backfill,
)


TRADE_RECORD_ROOT = REPO / "knowledge_base/trade_records"
BACKFILL_HELPER = REPO / "src/research_infra/ai_decision_trace_backfill.py"
BACKFILL_TEST = REPO / "tests/research_infra/test_ai_decision_trace_backfill.py"
TRACE_PROVENANCE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_TRACE_PROVENANCE_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_trade_record_backfill_row_is_hash_only",
    "test_trade_record_backfill_rows_and_summary",
    "test_iter_trade_record_paths_excludes_pending_index_files",
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def test_coverage(test_text: str) -> dict[str, bool]:
    return {name: name in test_text for name in EXPECTED_TEST_NAMES}


def build() -> dict[str, Any]:
    generated_at = utc_now()
    discovered_json_paths = sorted(path for path in TRADE_RECORD_ROOT.rglob("*.json") if path.is_file())
    trade_record_paths = iter_trade_record_paths(TRADE_RECORD_ROOT)
    rows = build_trade_record_ai_trace_backfill_rows(
        trade_record_paths,
        source_root=REPO,
        generated_at_utc=generated_at,
    )
    write_jsonl(OUTPUT_LEDGER, rows)
    backfill_summary = summarize_trade_record_ai_trace_backfill(rows)
    tests = test_coverage(BACKFILL_TEST.read_text(encoding="utf-8"))
    trace_summary = read_json(TRACE_PROVENANCE_SUMMARY)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at,
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            {
                "path": display_path(TRADE_RECORD_ROOT),
                "json_files_discovered": len(discovered_json_paths),
                "trade_record_json_files": len(trade_record_paths),
                "excluded_non_trade_record_json_files": len(discovered_json_paths) - len(trade_record_paths),
            },
            code_surface(TRACE_PROVENANCE_SUMMARY),
        ],
        "code_surfaces": [
            code_surface(BACKFILL_HELPER),
            code_surface(BACKFILL_TEST),
            code_surface(Path(__file__)),
        ],
        **backfill_summary,
        "backfill_schema_version": BACKFILL_SCHEMA_VERSION,
        "expected_test_name_coverage": tests,
        "expected_test_names_covered_rows": sum(tests.values()),
        "inherited_trace_logger_enabled": bool((trace_summary.get("implementation_effect") or {}).get("ai_decision_trace_logger_enabled")),
        "inherited_hash_only_prompt_response_provenance": bool(
            (trace_summary.get("implementation_effect") or {}).get("hash_only_prompt_response_provenance")
        ),
        "implementation_effect": {
            "trade_record_ai_trace_backfill_materialized": True,
            "hash_only_prompt_response_provenance": True,
            "runtime_trace_stream_write": False,
            "trading_decision_behavior_changed": False,
            "paid_api_or_vendor_call": False,
            "broker_operation": False,
            "runtime_candidate_use_permitted": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)
    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
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
        "rows": summary["rows"],
        "complete_rows": summary["complete_rows"],
        "stores_full_prompt_or_response_text_rows": summary["stores_full_prompt_or_response_text_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
