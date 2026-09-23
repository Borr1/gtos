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
    compact_final_review_row,
    summarize_final_review_rows,
)
from src.research_infra.moonshot_expanded_market_reduced_surface_execution import load_candidate_rows


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_ROOT = Path("C:/tmp/")
MOONSHOT_ROUTE_REL = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
FINAL_REVIEW_LEDGER = (
    MOONSHOT_ROOT
    / MOONSHOT_ROUTE_REL
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_REVIEW_EXECUTION_ROW_LEDGER_2026-05-17.jsonl"
)
IMPLEMENTATION_CANDIDATE_LEDGER = (
    MOONSHOT_ROOT
    / MOONSHOT_ROUTE_REL
    / "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES_ROW_LEDGER_2026-05-17.jsonl"
)
CANDIDATE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_OUTPUT_MANIFEST_{DATE}.json"


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
    main_candidates = load_candidate_rows(CANDIDATE_LEDGER)
    main_candidate_by_execution_id = {
        str(row.get("source_reduced_surface_execution_row_id") or ""): row for row in main_candidates
    }

    implementation_candidate_source_artifact = str(IMPLEMENTATION_CANDIDATE_LEDGER.relative_to(MOONSHOT_ROOT)).replace(
        "\\", "/"
    )
    implementation_candidate_sha = sha256_path(IMPLEMENTATION_CANDIDATE_LEDGER)
    implementation_candidates: dict[str, dict[str, Any]] = {}
    for line_no, row in iter_jsonl(IMPLEMENTATION_CANDIDATE_LEDGER):
        row["_source_line_no"] = line_no
        implementation_candidates[str(row.get("implementation_candidate_row_id") or "")] = row

    final_review_source_artifact = str(FINAL_REVIEW_LEDGER.relative_to(MOONSHOT_ROOT)).replace("\\", "/")
    final_review_sha = sha256_path(FINAL_REVIEW_LEDGER)
    rows: list[dict[str, Any]] = []
    for line_no, final_review in iter_jsonl(FINAL_REVIEW_LEDGER):
        implementation_candidate_id = str(final_review.get("input_implementation_candidate_row_id") or "")
        implementation_candidate = implementation_candidates.get(implementation_candidate_id)
        execution_id = str((implementation_candidate or {}).get("input_reduced_surface_execution_row_id") or "")
        main_candidate = main_candidate_by_execution_id.get(execution_id)
        rows.append(
            compact_final_review_row(
                final_review,
                implementation_candidate,
                main_candidate,
                final_review_source_artifact=final_review_source_artifact,
                final_review_source_line_no=line_no,
                final_review_source_sha256=final_review_sha,
                implementation_candidate_source_artifact=implementation_candidate_source_artifact
                if implementation_candidate
                else None,
                implementation_candidate_source_line_no=(implementation_candidate or {}).get("_source_line_no"),
                implementation_candidate_source_sha256=implementation_candidate_sha if implementation_candidate else None,
                output_row_id=f"MAIN-ORCH48-MOONSHOT-FINAL-REVIEW-OVERLAY-{len(rows) + 1:08d}",
            )
        )
    write_jsonl(OUTPUT_LEDGER, rows)

    final_summary = summarize_final_review_rows(rows)
    summary = {
        "route_id": "MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE",
        "schema_version": "main_orch48_moonshot_expanded_market_final_review_intake_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        "candidate_ledger_sha256": sha256_path(CANDIDATE_LEDGER),
        "final_review_ledger": final_review_source_artifact,
        "final_review_ledger_sha256": final_review_sha,
        "implementation_candidate_ledger": implementation_candidate_source_artifact,
        "implementation_candidate_ledger_sha256": implementation_candidate_sha,
        "main_candidate_rows": len(main_candidates),
        "implementation_candidate_rows": len(implementation_candidates),
        "final_review_rows": len(rows),
        "main_candidate_bound_rows": final_summary["main_candidate_bound_rows"],
        "final_review_evidence_rows": final_summary["final_review_evidence_rows"],
        "evidence_execution_rows_claimed": final_summary["evidence_execution_rows_claimed"],
        "main_compiler_final_review_action_counts": final_summary["main_compiler_final_review_action_counts"],
        "final_review_integrity_status_counts": final_summary["final_review_integrity_status_counts"],
        "symbol_counts": final_summary["symbol_counts"],
        "market_timeframe_counts": final_summary["market_timeframe_counts"],
        "source_component_counts": final_summary["source_component_counts"],
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_rows": final_summary[
            "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_rows"
        ],
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_sum_reference": final_summary[
            "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_sum_reference"
        ],
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_mean_reference": final_summary[
            "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_mean_reference"
        ],
        "runtime_candidate_use_permitted_rows": final_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": final_summary["candidate_use_allowed_now_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": final_summary[
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
        "final_review_rows": len(rows),
        "main_candidate_bound_rows": summary["main_candidate_bound_rows"],
        "action_counts": summary["main_compiler_final_review_action_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
