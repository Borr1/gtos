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
    reduced_surface_event_emitter_contract_for_priority_group,
    summarize_reduced_surface_event_emitter_contracts,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
PRIORITY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_EMITTER_CONTRACT_OUTPUT_MANIFEST_{DATE}.json"


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
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
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
    priorities = read_jsonl(PRIORITY_LEDGER)
    priority_sha = sha256_path(PRIORITY_LEDGER)
    priority_artifact = str(PRIORITY_LEDGER.relative_to(REPO)).replace("\\", "/")
    contracts = [
        reduced_surface_event_emitter_contract_for_priority_group(
            priority,
            contract_row_id=f"MAIN-ORCH48-MOONSHOT-FINAL-REVIEW-ADJUSTED-EVENT-EMITTER-CONTRACT-{index:08d}",
            source_artifact=priority_artifact,
            source_line_no=int(priority.get("_source_line_no") or index),
            source_sha256=priority_sha,
        )
        for index, priority in enumerate(priorities, start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, contracts)

    contract_summary = summarize_reduced_surface_event_emitter_contracts(contracts)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_EVENT_EMITTER_CONTRACTS",
        "schema_version": "main_orch48_moonshot_final_review_adjusted_event_emitter_contracts_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "priority_ledger": priority_artifact,
        "priority_ledger_sha256": priority_sha,
        "priority_groups": len(priorities),
        "emitter_contract_rows": len(contracts),
        "candidate_rows": contract_summary["candidate_rows"],
        "final_review_overlay_bound_rows": contract_summary["final_review_overlay_bound_rows"],
        "implementation_ready_candidate_rows": contract_summary["implementation_ready_candidate_rows"],
        "capacity_blocked_candidate_rows": contract_summary["capacity_blocked_candidate_rows"],
        "event_registry_match_rows": contract_summary["event_registry_match_rows"],
        "expected_candidate_event_rows": contract_summary["expected_candidate_event_rows"],
        "duplicate_scope_event_match_rows": contract_summary["duplicate_scope_event_match_rows"],
        "emitter_contract_status_counts": contract_summary["emitter_contract_status_counts"],
        "source_capture_priority_class_counts": contract_summary["source_capture_priority_class_counts"],
        "final_review_source_capture_class_counts": contract_summary["final_review_source_capture_class_counts"],
        "final_review_adjusted_rollup_status_counts": contract_summary["final_review_adjusted_rollup_status_counts"],
        "main_compiler_final_review_action_counts": contract_summary["main_compiler_final_review_action_counts"],
        "required_event_field_counts": contract_summary["required_event_field_counts"],
        "required_numeric_threshold_field_counts": contract_summary["required_numeric_threshold_field_counts"],
        "required_source_identity_field_counts": contract_summary["required_source_identity_field_counts"],
        "symbol_counts": contract_summary["symbol_counts"],
        "market_timeframe_counts": contract_summary["market_timeframe_counts"],
        "source_component_counts": contract_summary["source_component_counts"],
        "runtime_candidate_use_permitted_rows": contract_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": contract_summary["candidate_use_allowed_now_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": contract_summary[
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
        "emitter_contract_rows": summary["emitter_contract_rows"],
        "implementation_ready_candidate_rows": summary["implementation_ready_candidate_rows"],
        "capacity_blocked_candidate_rows": summary["capacity_blocked_candidate_rows"],
        "status_counts": summary["emitter_contract_status_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
