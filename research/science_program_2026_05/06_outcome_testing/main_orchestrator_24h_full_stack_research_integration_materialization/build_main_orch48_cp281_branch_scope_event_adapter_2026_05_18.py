from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_BRANCH_SCOPE_EVENT_ADAPTER"
SCHEMA_VERSION = "main_orch48_cp281_branch_scope_event_adapter_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_frozen_universe_cp281_runtime_mapping import (  # noqa: E402
    CP281BranchDecisionRegistry,
    DEFAULT_BRANCH_DECISION_LEDGER,
    read_jsonl,
    summarize_branch_scope_source_rows,
)


HELPER = REPO / "src/research_infra/moonshot_frozen_universe_cp281_runtime_mapping.py"
TEST_FILE = REPO / "tests/research_infra/test_moonshot_frozen_universe_cp281_runtime_mapping.py"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_SOURCE_ROLLUP_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EVENT_SOURCE_PATHS = [
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/strategy_follow_evaluations.jsonl"),
    Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    Path("shadow_logs/live_candidate_strategy_rollups.jsonl"),
    Path("shadow_logs/live_structural_strategy_metadata.jsonl"),
    Path("shadow_logs/candidate_features_log.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/fvg_ob_confluence_audit.jsonl"),
    Path("shadow_logs/scid_forward_source_capture.jsonl"),
    Path("shadow_logs/nofill_forward_source_capture.jsonl"),
]

EXPECTED_TEST_NAMES = ["test_branch_scope_source_adapter_fans_out_horizons_and_scores_matches"]


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


def test_coverage(test_text: str) -> dict[str, bool]:
    return {name: name in test_text for name in EXPECTED_TEST_NAMES}


def read_source(path: Path) -> tuple[list[dict[str, Any]], int]:
    absolute = REPO / path
    rows: list[dict[str, Any]] = []
    parse_errors = 0
    if absolute.exists():
        with absolute.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    parse_errors += 1
    return rows, parse_errors


def build() -> dict[str, Any]:
    generated_at = utc_now()
    branch_decisions = read_jsonl(REPO / DEFAULT_BRANCH_DECISION_LEDGER)
    registry = CP281BranchDecisionRegistry(branch_decisions)
    rows: list[dict[str, Any]] = []
    for index, source_path in enumerate(EVENT_SOURCE_PATHS, start=1):
        source_rows, parse_errors = read_source(source_path)
        rollup = summarize_branch_scope_source_rows(source_rows, registry=registry)
        absolute = REPO / source_path
        rows.append(
            {
                "branch_scope_event_adapter_row_id": f"MAIN-ORCH48-CP281-BRANCH-SCOPE-ADAPTER-{index:04d}",
                "event_source_path": str(source_path).replace("\\", "/"),
                "event_source_exists": absolute.exists(),
                "event_source_sha256": sha256_path(absolute) if absolute.exists() else None,
                "event_source_bytes": absolute.stat().st_size if absolute.exists() else None,
                "parse_error_rows": parse_errors,
                **rollup,
                "adapter_status": (
                    "CP281_BRANCH_SCOPE_EVENTS_DERIVED_AND_MATCHED"
                    if rollup["registry_match_rows"]
                    else "CP281_BRANCH_SCOPE_EVENTS_DERIVED_WITHOUT_REGISTRY_MATCHES"
                    if rollup["derived_cp281_branch_scope_event_rows"]
                    else "CP281_BRANCH_SCOPE_EVENTS_NOT_DERIVABLE_FROM_SOURCE"
                ),
                "production_change_approved": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
            }
        )
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts = Counter(row["adapter_status"] for row in rows)
    tests = test_coverage(TEST_FILE.read_text(encoding="utf-8"))
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_at,
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "branch_decision_ledger": display_path(REPO / DEFAULT_BRANCH_DECISION_LEDGER),
        "branch_decision_ledger_sha256": sha256_path(REPO / DEFAULT_BRANCH_DECISION_LEDGER),
        "branch_decision_rows": len(branch_decisions),
        "event_source_count": len(rows),
        "event_source_rows_total": sum(int(row.get("source_rows") or 0) for row in rows),
        "parse_error_rows_total": sum(int(row.get("parse_error_rows") or 0) for row in rows),
        "source_rows_with_cp281_branch_scope_events_total": sum(
            int(row.get("source_rows_with_cp281_branch_scope_events") or 0) for row in rows
        ),
        "derived_cp281_branch_scope_event_rows_total": sum(
            int(row.get("derived_cp281_branch_scope_event_rows") or 0) for row in rows
        ),
        "registry_matched_event_rows_total": sum(int(row.get("registry_matched_event_rows") or 0) for row in rows),
        "registry_match_rows_total": sum(int(row.get("registry_match_rows") or 0) for row in rows),
        "adapter_status_counts": dict(sorted(status_counts.items())),
        "source_paths": [row["event_source_path"] for row in rows],
        "code_surfaces": [
            code_surface(HELPER),
            code_surface(TEST_FILE),
            code_surface(Path(__file__)),
        ],
        "expected_test_name_coverage": tests,
        "expected_test_names_covered_rows": sum(tests.values()),
        "implementation_effect": {
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_import_path": False,
            "mutates_order_risk_prompt_safety_or_mt5": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
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
        "event_source_count": len(rows),
        "derived_cp281_branch_scope_event_rows_total": summary["derived_cp281_branch_scope_event_rows_total"],
        "registry_match_rows_total": summary["registry_match_rows_total"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
