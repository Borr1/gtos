from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_TOUCH_COUNT_GATE_OUTCOME_JOIN"
SCHEMA_VERSION = "main_orch48_touch_count_gate_outcome_join_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.gate_filter_selector_evidence import (  # noqa: E402
    build_touch_count_gate_outcome_join_rows,
    summarize_touch_count_gate_outcome_join,
)


TOUCH_COUNT_LOG = REPO / "shadow_logs/touch_count_gate_decisions.jsonl"
OUTCOME_LOG = REPO / "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"
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
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
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
    touch_sha = sha256_path(TOUCH_COUNT_LOG)
    outcome_sha = sha256_path(OUTCOME_LOG)
    touch_rows = read_jsonl(TOUCH_COUNT_LOG)
    outcome_rows = read_jsonl(OUTCOME_LOG)
    joined_rows = build_touch_count_gate_outcome_join_rows(
        touch_count_rows=touch_rows,
        outcome_rows=outcome_rows,
        touch_source_path=display_path(TOUCH_COUNT_LOG),
        touch_source_sha256=touch_sha,
        outcome_source_path=display_path(OUTCOME_LOG),
        outcome_source_sha256=outcome_sha,
    )
    write_jsonl(OUTPUT_LEDGER, joined_rows)
    join_summary = summarize_touch_count_gate_outcome_join(joined_rows)
    gate_action = (
        "KEEP_TOUCH_COUNT_THRESHOLD_2_AND_REVIEW_SOURCE_CAPTURE_GAP"
        if join_summary["joined_reject_positive_fillable_proxy_rows"] == 0
        else "REVIEW_TOUCH_COUNT_THRESHOLD_WITH_POSITIVE_FILLABLE_REJECTS"
    )
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "status": "OK_TOUCH_COUNT_GATE_OUTCOME_JOIN_MATERIALIZED",
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "touch_count_log": {
            "path": display_path(TOUCH_COUNT_LOG),
            "sha256": touch_sha,
            "rows": len(touch_rows),
        },
        "outcome_log": {
            "path": display_path(OUTCOME_LOG),
            "sha256": outcome_sha,
            "rows": len(outcome_rows),
        },
        "join_summary": join_summary,
        "gate_action": gate_action,
        "current_config_threshold": 2,
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "implementation_effect": {
            "touch_count_gate_outcome_join_materialized": True,
            "gate_config_change_now": False,
            "runtime_decision_effect": False,
            "production_change_opened_now": False,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "claim_boundary": (
            "Joined rows are forward-shadow gate evidence only. They do not count new replay R, "
            "change gate1.touch_count_reject_threshold, restart runtime, or touch broker state."
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
        "rows": len(joined_rows),
        "joined_rows": join_summary["joined_rows"],
        "joined_reject_rows": join_summary["joined_reject_rows"],
        "joined_reject_positive_fillable_proxy_rows": join_summary["joined_reject_positive_fillable_proxy_rows"],
        "gate_action": gate_action,
        "manifest_output_count": len(outputs),
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, sort_keys=True))
