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
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR_OUTPUT_MANIFEST_{DATE}.json"


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
        expected_candidate_id = expected_candidate.get("candidate_row_id") if expected_candidate else None
        registry_matches = registry.evaluate_event(match)
        matched_ids = [str(row.get("candidate_row_id") or "") for row in registry_matches]
        expected_found = bool(expected_candidate_id and expected_candidate_id in matched_ids)
        rows.append(
            {
                "replay_validator_row_id": f"MAIN-ORCH48-MOONSHOT-REDUCED-SURFACE-REPLAY-VALIDATOR-{len(rows) + 1:08d}",
                "match_source_line_no": line_no,
                "match_source_artifact": match_source_artifact,
                "match_source_sha256": match_ledger_sha,
                "source_match_row_id": match.get("reduced_surface_execution_match_row_id"),
                "source_execution_row_id": execution_id,
                "expected_candidate_row_id": expected_candidate_id,
                "expected_candidate_found": expected_found,
                "registry_matched_candidate_rows": len(registry_matches),
                "registry_matched_candidate_row_ids": matched_ids,
                "matched_decision_family": match.get("matched_decision_family"),
                "match_status": match.get("match_status"),
                "symbol": match.get("symbol"),
                "source_symbol": match.get("source_symbol"),
                "market_timeframe": match.get("market_timeframe"),
                "route_session": match.get("route_session"),
                "horizon_id": match.get("horizon_id"),
                "source_component": match.get("source_component"),
                "selected_side": match.get("selected_side"),
                "selected_intrabar_cost_adjusted_simulated_r": match.get(
                    "selected_intrabar_cost_adjusted_simulated_r"
                ),
                "replay_validator_status": "MAIN_REGISTRY_REPLAYS_HELD_MATCH"
                if expected_found
                else "MAIN_REGISTRY_REPLAY_REPAIR_REQUIRED",
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        )
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts = Counter(row["replay_validator_status"] for row in rows)
    decision_counts = Counter(row["matched_decision_family"] for row in rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR",
        "schema_version": "main_orch48_moonshot_reduced_surface_replay_validator_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "candidate_ledger_sha256": sha256_path(CANDIDATE_LEDGER),
        "match_ledger": match_source_artifact,
        "match_ledger_sha256": match_ledger_sha,
        "candidate_rows": len(candidates),
        "held_match_rows": len(rows),
        "expected_candidate_found_rows": sum(bool(row["expected_candidate_found"]) for row in rows),
        "replay_repair_rows": int(status_counts.get("MAIN_REGISTRY_REPLAY_REPAIR_REQUIRED", 0)),
        "total_registry_matched_candidate_rows": sum(int(row.get("registry_matched_candidate_rows") or 0) for row in rows),
        "replay_validator_status_counts": dict(sorted(status_counts.items())),
        "matched_decision_family_counts": dict(sorted(decision_counts.items())),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
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
        "expected_candidate_found_rows": summary["expected_candidate_found_rows"],
        "replay_repair_rows": summary["replay_repair_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
