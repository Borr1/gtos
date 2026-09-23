from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CONFIDENCE_FILTER_QUARANTINE"
SCHEMA_VERSION = "main_orch48_confidence_filter_quarantine_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.ai_decision_architecture_audit import (  # noqa: E402
    ai_architecture_confidence_filter_quarantine_row,
    summarize_ai_architecture_audit_rows,
)


CONFIG_PATH = REPO / "config/agent_config.yaml"
B12_AUTOPSY = REPO / "research/ai_behavior/B12_confidence/autopsy.json"
ORCHESTRATOR_SOURCE = REPO / "src/components/orchestrator.py"
CONFIDENCE_SCORER_SOURCE = REPO / "src/components/confidence_scorer.py"
AUDIT_MODULE = REPO / "src/research_infra/ai_decision_architecture_audit.py"
TEST_SOURCE = REPO / "tests/research_infra/test_ai_decision_architecture_audit.py"
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    surfaces = [
        AUDIT_MODULE,
        TEST_SOURCE,
        CONFIG_PATH,
        B12_AUTOPSY,
        ORCHESTRATOR_SOURCE,
        CONFIDENCE_SCORER_SOURCE,
        Path(__file__).resolve(),
        ROUTE_DIR / "verify_main_orch48_confidence_filter_quarantine_2026_05_18.py",
    ]
    return [
        {
            "path": display_path(path),
            "bytes": path.stat().st_size,
            "lines": count_lines(path),
            "sha256": sha256_path(path),
        }
        for path in surfaces
    ]


def build() -> dict[str, Any]:
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    b12_autopsy = read_json(B12_AUTOPSY)
    orchestrator_text = ORCHESTRATOR_SOURCE.read_text(encoding="utf-8", errors="replace")
    confidence_scorer_text = CONFIDENCE_SCORER_SOURCE.read_text(encoding="utf-8", errors="replace")

    rows = [
        ai_architecture_confidence_filter_quarantine_row(
            config_text,
            b12_autopsy,
            orchestrator_text=orchestrator_text,
            confidence_scorer_text=confidence_scorer_text,
            audit_row_id="MAIN-ORCH48-CONFIDENCE-FILTER-QUARANTINE-0001",
            source_artifact=display_path(CONFIG_PATH),
            source_sha256=sha256_path(CONFIG_PATH),
            b12_source_artifact=display_path(B12_AUTOPSY),
            b12_source_sha256=sha256_path(B12_AUTOPSY),
        ),
        {
            "ai_architecture_audit_row_id": "MAIN-ORCH48-CONFIDENCE-FILTER-QUARANTINE-0002",
            "audit_surface": "confidence_filter_runtime_halt_boundary",
            "schema_version": SCHEMA_VERSION,
            "source_artifact": display_path(RUNTIME_HALT_FLAG),
            "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
            "live_runtime_restart_now": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_change_opened_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "ai_architecture_action": "NO_RUNTIME_CONFIDENCE_FILTER_EXPERIMENT_DURING_SESSION_57_HALT",
        },
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    audit_summary = summarize_ai_architecture_audit_rows(rows)
    confidence_row = rows[0]
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            {"path": display_path(CONFIG_PATH), "lines": count_lines(CONFIG_PATH), "sha256": sha256_path(CONFIG_PATH)},
            {"path": display_path(B12_AUTOPSY), "lines": count_lines(B12_AUTOPSY), "sha256": sha256_path(B12_AUTOPSY)},
        ],
        "code_surfaces": code_surface_summary(),
        **audit_summary,
        "confidence_filter_mode": confidence_row["confidence_filter_mode"],
        "b12_confidence_trades_evaluated": confidence_row["b12_confidence_trades_evaluated"],
        "b12_confidence_family_size": confidence_row["b12_confidence_family_size"],
        "b12_confidence_predictive_strata": confidence_row["b12_confidence_predictive_strata"],
        "confidence_filter_active_branch_present": confidence_row["confidence_filter_active_branch_present"],
        "confidence_scorer_gold_price_config_present": confidence_row["confidence_scorer_gold_price_config_present"],
        "runtime_halt_active": rows[1]["runtime_halt_active"],
        "implementation_effect": {
            "confidence_filter_quarantine_materialized": True,
            "confidence_filter_mode_changed": False,
            "live_ai_runtime_change_now": False,
            "runtime_decision_effect": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "production_change_opened_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
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
        "route_id": ROUTE_ID,
        "rows": len(rows),
        "confidence_filter_mode": summary["confidence_filter_mode"],
        "b12_confidence_predictive_strata": summary["b12_confidence_predictive_strata"],
        "runtime_halt_active": summary["runtime_halt_active"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
