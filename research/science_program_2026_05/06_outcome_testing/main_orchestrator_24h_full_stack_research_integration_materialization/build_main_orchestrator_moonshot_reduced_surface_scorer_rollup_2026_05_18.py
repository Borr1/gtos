from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    load_candidate_rows,
    reduced_surface_candidate_event_rollups,
    summarize_reduced_surface_candidate_event_rollups,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CANDIDATE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
EVENT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_ADAPTER_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_OUTPUT_MANIFEST_{DATE}.json"


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build() -> dict[str, Any]:
    candidates = load_candidate_rows(CANDIDATE_LEDGER)
    events = read_jsonl(EVENT_LEDGER)
    rollups = reduced_surface_candidate_event_rollups(candidates, events)
    write_jsonl(OUTPUT_LEDGER, rollups)

    rollup_summary = summarize_reduced_surface_candidate_event_rollups(rollups)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP",
        "schema_version": "main_orch48_moonshot_reduced_surface_scorer_rollup_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "candidate_ledger_sha256": sha256_path(CANDIDATE_LEDGER),
        "event_ledger": str(EVENT_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "event_ledger_sha256": sha256_path(EVENT_LEDGER),
        "candidate_rows": len(candidates),
        "event_rows": len(events),
        "rollup_rows": len(rollups),
        "candidates_with_event_matches": rollup_summary["candidates_with_event_matches"],
        "candidates_without_event_matches": rollup_summary["candidates_without_event_matches"],
        "event_registry_match_rows": rollup_summary["event_registry_match_rows"],
        "expected_candidate_event_rows": rollup_summary["expected_candidate_event_rows"],
        "duplicate_scope_event_match_rows": rollup_summary["duplicate_scope_event_match_rows"],
        "candidate_event_rollup_status_counts": rollup_summary["candidate_event_rollup_status_counts"],
        "main_compiler_action_counts": rollup_summary["main_compiler_action_counts"],
        "symbol_counts": rollup_summary["symbol_counts"],
        "market_timeframe_counts": rollup_summary["market_timeframe_counts"],
        "source_component_counts": rollup_summary["source_component_counts"],
        "runtime_candidate_use_permitted_rows": rollup_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": rollup_summary["candidate_use_allowed_now_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": rollup_summary[
            "replay_r_reference_counted_as_new_main_result_rows"
        ],
        "implementation_effect": {
            "runtime_or_live_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": summary["route_id"],
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
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
        "route_id": summary["route_id"],
        "candidate_rows": len(candidates),
        "event_rows": len(events),
        "event_registry_match_rows": summary["event_registry_match_rows"],
        "candidates_without_event_matches": summary["candidates_without_event_matches"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
