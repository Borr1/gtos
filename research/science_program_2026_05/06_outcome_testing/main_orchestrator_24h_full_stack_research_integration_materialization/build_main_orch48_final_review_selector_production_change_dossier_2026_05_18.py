from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    final_review_selector_production_change_dossier_row,
    summarize_final_review_selector_production_change_dossier,
)


SELECTOR_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SELECTOR_RECO_LEDGER_{DATE}.jsonl"
SELECTOR_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SELECTOR_RECO_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_expanded_market_reduced_surface_execution.py"),
    Path("tests/research_infra/test_moonshot_expanded_market_reduced_surface_execution.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_final_review_selector_production_change_dossier_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_final_review_selector_production_change_dossier_2026_05_18.py"
    ),
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


def read_jsonl_with_line_no(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                rows.append((line_no, json.loads(line)))
    return rows


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


def code_surface_summary() -> list[dict[str, Any]]:
    return [
        {
            "path": str(path).replace("\\", "/"),
            "bytes": (REPO / path).stat().st_size,
            "lines": count_lines(REPO / path),
            "sha256": sha256_path(REPO / path),
        }
        for path in CODE_SURFACES
    ]


def build() -> dict[str, Any]:
    selector_sha = sha256_path(SELECTOR_LEDGER)
    selector_summary_sha = sha256_path(SELECTOR_SUMMARY)
    selector_summary = read_json(SELECTOR_SUMMARY)
    selector_rows = read_jsonl_with_line_no(SELECTOR_LEDGER)

    dossier_rows: list[dict[str, Any]] = []
    for source_line_no, recommendation in selector_rows:
        dossier_rows.append(
            final_review_selector_production_change_dossier_row(
                recommendation,
                dossier_row_id=f"MAIN-ORCH48-FINAL-REVIEW-SELECTOR-PROD-CHANGE-DOSSIER-{len(dossier_rows) + 1:08d}",
                source_artifact=display_path(SELECTOR_LEDGER),
                source_line_no=source_line_no,
                source_sha256=selector_sha,
            )
        )
    write_jsonl(OUTPUT_LEDGER, dossier_rows)

    dossier_summary = summarize_final_review_selector_production_change_dossier(dossier_rows)
    summary = {
        "route_id": "MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PRODUCTION_CHANGE_DOSSIER",
        "schema_version": "main_orch48_final_review_selector_production_change_dossier_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_final_review_selector_recommendation_ledger": {
            "path": display_path(SELECTOR_LEDGER),
            "rows": count_lines(SELECTOR_LEDGER),
            "sha256": selector_sha,
        },
        "input_final_review_selector_recommendation_summary": {
            "path": display_path(SELECTOR_SUMMARY),
            "sha256": selector_summary_sha,
            "selector_recommendation_rows": selector_summary.get("selector_recommendation_rows"),
            "selector_recommendation_status_counts": selector_summary.get("selector_recommendation_status_counts"),
        },
        "code_surfaces": code_surface_summary(),
        **dossier_summary,
        "implementation_effect": {
            "production_change_dossier_draft_available": True,
            "default_off_mechanical_selector_scope_rows_for_review": dossier_summary[
                "mechanical_selector_scope_draft_ready_for_separate_review_rows"
            ],
            "production_change_opened_now": False,
            "live_selector_change_now": False,
            "runtime_trading_or_live_broker_effect": False,
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
        "route_id": summary["route_id"],
        "dossier_rows": summary["rows"],
        "production_change_dossier_status_counts": summary["production_change_dossier_status_counts"],
        "production_change_opened_now_rows": summary["production_change_opened_now_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
