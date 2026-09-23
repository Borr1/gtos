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
    final_review_adjusted_event_registry_scores,
    summarize_final_review_adjusted_event_registry_scores,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CANDIDATE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
EVENT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_ADAPTER_LEDGER_{DATE}.jsonl"
ADJUSTED_ROLLUP_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_OUTPUT_MANIFEST_{DATE}.json"


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
    candidates = read_jsonl(CANDIDATE_LEDGER)
    events = read_jsonl(EVENT_LEDGER)
    adjusted_rollups = read_jsonl(ADJUSTED_ROLLUP_LEDGER)
    scores = final_review_adjusted_event_registry_scores(events, candidates, adjusted_rollups)
    write_jsonl(OUTPUT_LEDGER, scores)

    score_summary = summarize_final_review_adjusted_event_registry_scores(scores)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_REGISTRY_SCORES",
        "schema_version": "main_orch48_moonshot_final_review_adjusted_registry_scores_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "candidate_ledger_sha256": sha256_path(CANDIDATE_LEDGER),
        "event_ledger": str(EVENT_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "event_ledger_sha256": sha256_path(EVENT_LEDGER),
        "adjusted_rollup_ledger": str(ADJUSTED_ROLLUP_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "adjusted_rollup_ledger_sha256": sha256_path(ADJUSTED_ROLLUP_LEDGER),
        "candidate_rows": len(candidates),
        "event_rows": len(events),
        "adjusted_rollup_rows": len(adjusted_rollups),
        "score_rows": len(scores),
        "registry_match_rows": score_summary["registry_match_rows"],
        "implementation_ready_registry_match_rows": score_summary["implementation_ready_registry_match_rows"],
        "capacity_blocked_registry_match_rows": score_summary["capacity_blocked_registry_match_rows"],
        "binding_repair_registry_match_rows": score_summary["binding_repair_registry_match_rows"],
        "expected_candidate_found_in_registry_rows": score_summary["expected_candidate_found_in_registry_rows"],
        "expected_candidate_implementation_ready_rows": score_summary["expected_candidate_implementation_ready_rows"],
        "expected_candidate_capacity_blocked_rows": score_summary["expected_candidate_capacity_blocked_rows"],
        "final_review_registry_score_status_counts": score_summary["final_review_registry_score_status_counts"],
        "final_review_registry_match_status_counts": score_summary["final_review_registry_match_status_counts"],
        "main_compiler_final_review_action_counts": score_summary["main_compiler_final_review_action_counts"],
        "symbol_counts": score_summary["symbol_counts"],
        "market_timeframe_counts": score_summary["market_timeframe_counts"],
        "source_component_counts": score_summary["source_component_counts"],
        "runtime_candidate_use_permitted_rows": score_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": score_summary["candidate_use_allowed_now_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": score_summary[
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
        "score_rows": summary["score_rows"],
        "registry_match_rows": summary["registry_match_rows"],
        "implementation_ready_registry_match_rows": summary["implementation_ready_registry_match_rows"],
        "capacity_blocked_registry_match_rows": summary["capacity_blocked_registry_match_rows"],
        "status_counts": summary["final_review_registry_score_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
