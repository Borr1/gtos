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

from src.research_infra.ai_decision_architecture_audit import (
    ai_architecture_canary_audit_row,
    ai_architecture_config_audit_row,
    ai_architecture_malformed_response_audit_row,
    ai_architecture_selector_dossier_audit_row,
    parse_jsonl,
    summarize_ai_architecture_audit_rows,
)


CONFIG_PATH = REPO / "config/agent_config.yaml"
MALFORMED_LOG = REPO / "shadow_logs/malformed_responses.jsonl"
CANARY_MANIFEST = REPO / "scripts/canary_fixtures/manifest.json"
SELECTOR_DOSSIER_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_SELECTOR_PROD_CHANGE_DOSSIER_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/ai_decision_architecture_audit.py"),
    Path("tests/research_infra/test_ai_decision_architecture_audit.py"),
    Path("src/components/primary_analyzer.py"),
    Path("src/components/confidence_scorer.py"),
    Path("scripts/api_refusal_monitor.py"),
    Path("scripts/canary_test.py"),
    Path("config/agent_config.yaml"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_ai_decision_architecture_audit_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_ai_decision_architecture_audit_2026_05_18.py"
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
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    malformed_text = MALFORMED_LOG.read_text(encoding="utf-8") if MALFORMED_LOG.exists() else ""
    malformed_rows = parse_jsonl(malformed_text)
    canary_manifest = read_json(CANARY_MANIFEST)
    selector_summary = read_json(SELECTOR_DOSSIER_SUMMARY)

    rows = [
        ai_architecture_config_audit_row(
            config_text,
            audit_row_id="MAIN-ORCH48-AI-DECISION-ARCHITECTURE-AUDIT-00000001",
            source_artifact=display_path(CONFIG_PATH),
            source_sha256=sha256_path(CONFIG_PATH),
        ),
        ai_architecture_malformed_response_audit_row(
            malformed_rows,
            audit_row_id="MAIN-ORCH48-AI-DECISION-ARCHITECTURE-AUDIT-00000002",
            source_artifact=display_path(MALFORMED_LOG),
            source_sha256=sha256_path(MALFORMED_LOG),
        ),
        ai_architecture_canary_audit_row(
            canary_manifest,
            audit_row_id="MAIN-ORCH48-AI-DECISION-ARCHITECTURE-AUDIT-00000003",
            source_artifact=display_path(CANARY_MANIFEST),
            source_sha256=sha256_path(CANARY_MANIFEST),
        ),
        ai_architecture_selector_dossier_audit_row(
            selector_summary,
            audit_row_id="MAIN-ORCH48-AI-DECISION-ARCHITECTURE-AUDIT-00000004",
            source_artifact=display_path(SELECTOR_DOSSIER_SUMMARY),
            source_sha256=sha256_path(SELECTOR_DOSSIER_SUMMARY),
        ),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    audit_summary = summarize_ai_architecture_audit_rows(rows)
    summary = {
        "route_id": "MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT",
        "schema_version": "main_orch48_ai_decision_architecture_audit_v1",
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            {"path": display_path(CONFIG_PATH), "rows": count_lines(CONFIG_PATH), "sha256": sha256_path(CONFIG_PATH)},
            {
                "path": display_path(MALFORMED_LOG),
                "rows": count_lines(MALFORMED_LOG),
                "sha256": sha256_path(MALFORMED_LOG),
            },
            {
                "path": display_path(CANARY_MANIFEST),
                "rows": count_lines(CANARY_MANIFEST),
                "sha256": sha256_path(CANARY_MANIFEST),
            },
            {
                "path": display_path(SELECTOR_DOSSIER_SUMMARY),
                "rows": count_lines(SELECTOR_DOSSIER_SUMMARY),
                "sha256": sha256_path(SELECTOR_DOSSIER_SUMMARY),
            },
        ],
        "code_surfaces": code_surface_summary(),
        **audit_summary,
        "implementation_effect": {
            "ai_architecture_audit_available": True,
            "paid_api_or_vendor_call": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
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
        "audit_rows": summary["rows"],
        "malformed_response_rows": summary["malformed_response_rows"],
        "manual_canary_fixture_rows": summary["manual_canary_fixture_rows"],
        "mechanical_selector_scope_draft_ready_for_separate_review_rows": summary[
            "mechanical_selector_scope_draft_ready_for_separate_review_rows"
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
