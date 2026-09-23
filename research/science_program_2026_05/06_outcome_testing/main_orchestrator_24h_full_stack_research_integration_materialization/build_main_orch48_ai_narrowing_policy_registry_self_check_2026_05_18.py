from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_POLICY_REGISTRY_SELF_CHECK"
SCHEMA_VERSION = "main_orch48_ai_narrowing_policy_registry_self_check_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    AINarrowingPolicyRegistry,
    ai_narrowing_policy_scope_event,
    summarize_ai_narrowing_policy_registry_evaluations,
)


POLICY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_NARROWING_POLICY_LEDGER_{DATE}.jsonl"
POLICY_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_NARROWING_POLICY_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

CODE_SURFACES = [
    Path("src/research_infra/moonshot_expanded_market_reduced_surface_execution.py"),
    Path("tests/research_infra/test_moonshot_expanded_market_reduced_surface_execution.py"),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "build_main_orch48_ai_narrowing_policy_registry_self_check_2026_05_18.py"
    ),
    Path(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "verify_main_orch48_ai_narrowing_policy_registry_self_check_2026_05_18.py"
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
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
    policy_rows = read_jsonl(POLICY_LEDGER)
    policy_summary = read_json(POLICY_SUMMARY)
    policy_sha = sha256_path(POLICY_LEDGER)
    policy_summary_sha = sha256_path(POLICY_SUMMARY)

    registry = AINarrowingPolicyRegistry(policy_rows)
    eval_rows: list[dict[str, Any]] = []
    for idx, policy_row in enumerate(policy_rows, start=1):
        event = ai_narrowing_policy_scope_event(policy_row, event_row_id=f"MAIN-ORCH48-AI-NARROWING-EVENT-{idx:08d}")
        evaluation = registry.evaluate_event(event, evaluation_row_id=f"MAIN-ORCH48-AI-NARROWING-EVAL-{idx:08d}")
        evaluation["source_artifact"] = display_path(POLICY_LEDGER)
        evaluation["source_line_no"] = idx
        evaluation["source_sha256"] = policy_sha
        evaluation["policy_self_check_expected_row_id"] = policy_row.get("ai_narrowing_policy_row_id")
        evaluation["policy_self_check_expected_status"] = policy_row.get("ai_narrowing_policy_status")
        evaluation["policy_self_check_pass"] = (
            evaluation.get("matched_policy_rows") == 1
            and evaluation.get("matched_policy_row_ids") == [policy_row.get("ai_narrowing_policy_row_id")]
        )
        eval_rows.append(evaluation)
    write_jsonl(OUTPUT_LEDGER, eval_rows)

    registry_summary = summarize_ai_narrowing_policy_registry_evaluations(eval_rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_ai_narrowing_policy_ledger": {
            "path": display_path(POLICY_LEDGER),
            "rows": count_lines(POLICY_LEDGER),
            "sha256": policy_sha,
        },
        "input_ai_narrowing_policy_summary": {
            "path": display_path(POLICY_SUMMARY),
            "sha256": policy_summary_sha,
            "policy_rows": policy_summary.get("rows"),
            "ai_narrowing_review_ready_rows": policy_summary.get("ai_narrowing_review_ready_rows"),
            "policy_status_counts": policy_summary.get("ai_narrowing_policy_status_counts"),
        },
        "code_surfaces": code_surface_summary(),
        **registry_summary,
        "policy_self_check_pass_rows": sum(bool(row.get("policy_self_check_pass")) for row in eval_rows),
        "policy_self_check_fail_rows": sum(not bool(row.get("policy_self_check_pass")) for row in eval_rows),
        "implementation_effect": {
            "default_off_ai_narrowing_registry_available": True,
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "runtime_trading_or_live_broker_effect": False,
            "runtime_candidate_use_permitted": False,
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
        "rows": summary["rows"],
        "matched_policy_rows": summary["matched_policy_rows"],
        "policy_self_check_fail_rows": summary["policy_self_check_fail_rows"],
        "ai_call_skip_allowed_now_rows": summary["ai_call_skip_allowed_now_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
