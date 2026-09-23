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

from src.research_infra.moonshot_numeric_router_system_recommendations import (
    compact_numeric_router_action_queue_row,
    summarize_numeric_router_action_queue,
)


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
FAMILY_LEDGER_BY_NAME = {
    "scorer_registry_surface": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_SURFACE_LEDGER_{DATE}.jsonl",
    "avoid_comparator_score": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_SCORE_LEDGER_{DATE}.jsonl",
    "context_guard_input": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_LEDGER_{DATE}.jsonl",
    "source_repair_proof": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_PROOF_LEDGER_{DATE}.jsonl",
}
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE_MANIFEST_{DATE}.json"


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
    action_rows: list[dict[str, Any]] = []
    input_ledger_summaries: list[dict[str, Any]] = []
    for family, path in FAMILY_LEDGER_BY_NAME.items():
        source_sha = sha256_path(path)
        rows = read_jsonl(path)
        input_ledger_summaries.append(
            {
                "family": family,
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "rows": len(rows),
                "sha256": source_sha,
            }
        )
        for index, row in enumerate(rows, start=1):
            action_rows.append(
                compact_numeric_router_action_queue_row(
                    row,
                    action_row_id=f"MAIN-ORCH48-NUMERIC-ROUTER-ACTION-{len(action_rows) + 1:08d}",
                    source_artifact=str(path.relative_to(REPO)).replace("\\", "/"),
                    source_line_no=index,
                    source_sha256=source_sha,
                )
            )
    write_jsonl(OUTPUT_LEDGER, action_rows)

    action_summary = summarize_numeric_router_action_queue(action_rows)
    summary = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE",
        "schema_version": "main_orch48_numeric_router_action_queue_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_ledger_summaries": input_ledger_summaries,
        "action_rows": action_summary["rows"],
        "output_family_counts": action_summary["output_family_counts"],
        "numeric_router_action_counts": action_summary["numeric_router_action_counts"],
        "symbol_counts": action_summary["symbol_counts"],
        "source_component_counts": action_summary["source_component_counts"],
        "summary_only_terminal_rows": action_summary["summary_only_terminal_rows"],
        "live_effect_rows": action_summary["live_effect_rows"],
        "runtime_score_allowed_rows": action_summary["runtime_score_allowed_rows"],
        "runtime_candidate_use_permitted_rows": action_summary["runtime_candidate_use_permitted_rows"],
        "candidate_use_allowed_now_rows": action_summary["candidate_use_allowed_now_rows"],
        "unconditional_scalar_use_allowed_rows": action_summary["unconditional_scalar_use_allowed_rows"],
        "replay_r_reference_counted_as_new_main_result_rows": action_summary[
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
        "action_rows": summary["action_rows"],
        "output_family_counts": summary["output_family_counts"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
