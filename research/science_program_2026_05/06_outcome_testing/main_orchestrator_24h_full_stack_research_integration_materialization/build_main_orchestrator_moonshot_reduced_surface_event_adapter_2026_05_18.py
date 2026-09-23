from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    ReducedSurfaceCandidateRegistry,
    load_candidate_rows,
    reduced_surface_event_from_source_row,
    required_event_fields_for_candidate,
    summarize_reduced_surface_events,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_ROOT = Path("C:/tmp/")
MOONSHOT_ROUTE_REL = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
MATCH_LEDGER = (
    MOONSHOT_ROOT
    / MOONSHOT_ROUTE_REL
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION_MATCH_LEDGER_2026-05-17.jsonl"
)
CANDIDATE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_ADAPTER_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_ADAPTER_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_ADAPTER_OUTPUT_MANIFEST_{DATE}.json"


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


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                yield line_no, json.loads(line)


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
    candidate_by_execution_id = {
        str(row.get("source_reduced_surface_execution_row_id") or ""): row for row in candidates
    }
    registry = ReducedSurfaceCandidateRegistry(candidates)
    rows: list[dict[str, Any]] = []
    match_ledger_sha = sha256_path(MATCH_LEDGER)
    match_source_artifact = str(MATCH_LEDGER.relative_to(MOONSHOT_ROOT)).replace("\\", "/")

    for line_no, match in iter_jsonl(MATCH_LEDGER):
        execution_id = str(match.get("input_reduced_surface_execution_row_id") or "")
        expected_candidate = candidate_by_execution_id.get(execution_id)
        required_fields = required_event_fields_for_candidate(expected_candidate) if expected_candidate else None
        event = reduced_surface_event_from_source_row(
            match,
            event_row_id=f"MAIN-ORCH48-MOONSHOT-REDUCED-SURFACE-EVENT-{len(rows) + 1:08d}",
            source_kind="moonshot_held_replay_match_row",
            source_artifact=match_source_artifact,
            source_line_no=line_no,
            source_sha256=match_ledger_sha,
            required_event_fields=required_fields,
        )
        registry_matches = registry.evaluate_event(event)
        matched_ids = [str(row.get("candidate_row_id") or "") for row in registry_matches]
        expected_candidate_id = expected_candidate.get("candidate_row_id") if expected_candidate else None
        expected_found = bool(expected_candidate_id and expected_candidate_id in matched_ids)
        event_complete = event.get("event_adapter_status") == "REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE"
        event.update(
            {
                "source_match_row_id": match.get("reduced_surface_execution_match_row_id"),
                "source_execution_row_id": execution_id,
                "input_matched_implementation_selection_row_id": match.get(
                    "input_matched_implementation_selection_row_id"
                ),
                "expected_candidate_row_id": expected_candidate_id,
                "expected_candidate_found": expected_found,
                "registry_matched_candidate_rows": len(registry_matches),
                "registry_matched_candidate_row_ids": matched_ids,
                "matched_decision_family": match.get("matched_decision_family"),
                "match_status": match.get("match_status"),
                "event_production_status": "REDUCED_SURFACE_EVENT_PRODUCTION_PASS"
                if event_complete and expected_found
                else "REDUCED_SURFACE_EVENT_PRODUCTION_REPAIR_REQUIRED",
            }
        )
        rows.append(event)

    write_jsonl(OUTPUT_LEDGER, rows)

    event_summary = summarize_reduced_surface_events(rows)
    event_production_status_counts = Counter(row["event_production_status"] for row in rows)
    decision_counts = Counter(row.get("matched_decision_family") for row in rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_ADAPTER",
        "schema_version": "main_orch48_moonshot_reduced_surface_event_adapter_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "candidate_ledger_sha256": sha256_path(CANDIDATE_LEDGER),
        "match_ledger": match_source_artifact,
        "match_ledger_sha256": match_ledger_sha,
        "candidate_rows": len(candidates),
        "held_match_rows": len(rows),
        "contract_complete_event_rows": int(
            event_summary["event_adapter_status_counts"].get("REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE", 0)
        ),
        "contract_incomplete_event_rows": int(
            event_summary["event_adapter_status_counts"].get("REDUCED_SURFACE_EVENT_CONTRACT_INCOMPLETE", 0)
        ),
        "expected_candidate_found_rows": sum(bool(row["expected_candidate_found"]) for row in rows),
        "event_production_repair_rows": int(
            event_production_status_counts.get("REDUCED_SURFACE_EVENT_PRODUCTION_REPAIR_REQUIRED", 0)
        ),
        "total_registry_matched_candidate_rows": sum(int(row.get("registry_matched_candidate_rows") or 0) for row in rows),
        "event_adapter_status_counts": event_summary["event_adapter_status_counts"],
        "event_production_status_counts": dict(sorted(event_production_status_counts.items())),
        "matched_decision_family_counts": dict(sorted(decision_counts.items())),
        "missing_required_field_counts": event_summary["missing_required_field_counts"],
        "invalid_numeric_field_counts": event_summary["invalid_numeric_field_counts"],
        "runtime_candidate_use_permitted_rows": event_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": event_summary["candidate_use_allowed_now_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": event_summary[
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
        "held_match_rows": len(rows),
        "contract_complete_event_rows": summary["contract_complete_event_rows"],
        "expected_candidate_found_rows": summary["expected_candidate_found_rows"],
        "event_production_repair_rows": summary["event_production_repair_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
