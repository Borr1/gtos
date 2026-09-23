from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_CAPACITY_BLOCKLIST"
SCHEMA_VERSION = "main_orch48_ai_narrowing_capacity_blocklist_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (  # noqa: E402
    AINarrowingCapacityBlocklist,
    final_review_ai_narrowing_capacity_blocklist_row,
    summarize_ai_narrowing_capacity_blocklist,
)


DOSSIER_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_LEDGER_{DATE}.jsonl"
CONFIG_PATH = REPO / "config/agent_config.yaml"
RUNTIME_HALT_FLAG = REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append((line_no, row))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def build() -> dict[str, Any]:
    generated = utc_now()
    dossier_sha = sha256_path(DOSSIER_LEDGER)
    config_sha = sha256_path(CONFIG_PATH)
    dossier_rows = read_jsonl(DOSSIER_LEDGER)
    source_rows = [
        (line_no, row)
        for line_no, row in dossier_rows
        if row.get("capacity_blocked_candidate_row_ids")
    ]
    blocklist_rows = [
        final_review_ai_narrowing_capacity_blocklist_row(
            row,
            blocklist_row_id=f"MAIN-ORCH48-AI-NARROWING-CAPACITY-BLOCKLIST-{index:08d}",
            source_artifact=display_path(DOSSIER_LEDGER),
            source_line_no=line_no,
            source_sha256=dossier_sha,
        )
        for index, (line_no, row) in enumerate(source_rows, start=1)
    ]
    blocklist = AINarrowingCapacityBlocklist(blocklist_rows)
    candidate_ids = sorted(
        {
            candidate_id
            for row in blocklist_rows
            for candidate_id in (row.get("capacity_blocked_candidate_row_ids") or [])
        }
    )
    self_check_rows = [
        blocklist.evaluate_candidate(
            candidate_id,
            evaluation_row_id=f"MAIN-ORCH48-AI-NARROWING-CAPACITY-BLOCKLIST-EVAL-{index:08d}",
        )
        for index, candidate_id in enumerate(candidate_ids, start=1)
    ]
    write_jsonl(OUTPUT_LEDGER, blocklist_rows)
    blocklist_summary = summarize_ai_narrowing_capacity_blocklist(blocklist_rows)
    eval_status_counts: dict[str, int] = {}
    for row in self_check_rows:
        status = str(row.get("ai_narrowing_capacity_blocklist_eval_status"))
        eval_status_counts[status] = eval_status_counts.get(status, 0) + 1
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "status": "OK_DEFAULT_OFF_AI_NARROWING_CAPACITY_BLOCKLIST_MATERIALIZED",
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_final_review_selector_production_change_dossier": {
            "path": display_path(DOSSIER_LEDGER),
            "sha256": dossier_sha,
            "rows": len(dossier_rows),
        },
        "config_source": {
            "path": display_path(CONFIG_PATH),
            "sha256": config_sha,
        },
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "blocklist_summary": blocklist_summary,
        "blocklist_registry_summary": blocklist.summarize(),
        "self_check_candidate_rows": len(self_check_rows),
        "self_check_eval_status_counts": dict(sorted(eval_status_counts.items())),
        "implementation_effect": {
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "capacity_blocklist_active_now": False,
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "claim_boundary": (
            "Rows are a default-off capacity blocklist extracted from final-review selector evidence. "
            "They do not activate ai_narrowing.capacity_blocklist_active, skip AI calls, or change live selectors."
        ),
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
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
        "blocklist_rows": len(blocklist_rows),
        "unique_candidate_ids": blocklist_summary["unique_capacity_blocked_candidate_ids"],
        "pre_ai_selector_blocked_candidate_ids": blocklist_summary["unique_pre_ai_selector_blocked_candidate_ids"],
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "manifest_output_count": len(outputs),
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, sort_keys=True))
