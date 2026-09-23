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

from src.research_infra.moonshot_expanded_market_final_review_execution import (
    apply_final_review_overlay_to_rollups,
    summarize_final_review_adjusted_rollups,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
ROLLUP_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_LEDGER_{DATE}.jsonl"
FINAL_REVIEW_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_OUTPUT_MANIFEST_{DATE}.json"


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
    rollups = read_jsonl(ROLLUP_LEDGER)
    final_review_rows = read_jsonl(FINAL_REVIEW_LEDGER)
    adjusted = apply_final_review_overlay_to_rollups(rollups, final_review_rows)
    write_jsonl(OUTPUT_LEDGER, adjusted)

    adjusted_summary = summarize_final_review_adjusted_rollups(adjusted)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP",
        "schema_version": "main_orch48_moonshot_final_review_adjusted_rollup_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "rollup_ledger": str(ROLLUP_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "rollup_ledger_sha256": sha256_path(ROLLUP_LEDGER),
        "final_review_ledger": str(FINAL_REVIEW_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "final_review_ledger_sha256": sha256_path(FINAL_REVIEW_LEDGER),
        "input_rollup_rows": len(rollups),
        "input_final_review_rows": len(final_review_rows),
        "adjusted_rollup_rows": len(adjusted),
        "final_review_overlay_bound_rows": adjusted_summary["final_review_overlay_bound_rows"],
        "final_review_adjusted_rollup_status_counts": adjusted_summary["final_review_adjusted_rollup_status_counts"],
        "main_compiler_final_review_action_counts": adjusted_summary["main_compiler_final_review_action_counts"],
        "event_registry_match_rows": adjusted_summary["event_registry_match_rows"],
        "expected_candidate_event_rows": adjusted_summary["expected_candidate_event_rows"],
        "duplicate_scope_event_match_rows": adjusted_summary["duplicate_scope_event_match_rows"],
        "final_review_evidence_rows": adjusted_summary["final_review_evidence_rows"],
        "symbol_counts": adjusted_summary["symbol_counts"],
        "market_timeframe_counts": adjusted_summary["market_timeframe_counts"],
        "source_component_counts": adjusted_summary["source_component_counts"],
        "runtime_candidate_use_permitted_rows": adjusted_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": adjusted_summary["candidate_use_allowed_now_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": adjusted_summary[
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
        "adjusted_rollup_rows": len(adjusted),
        "status_counts": summary["final_review_adjusted_rollup_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
