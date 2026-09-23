from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_RUNTIME_CONFIG_GUARD"
SCHEMA_VERSION = "main_orch48_ai_narrowing_runtime_config_guard_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (  # noqa: E402
    AINarrowingPolicyRegistry,
    ai_narrowing_policy_scope_event,
    ai_narrowing_runtime_config_guard_decision,
    normalize_ai_narrowing_runtime_config,
    summarize_ai_narrowing_policy_registry_evaluations,
    summarize_ai_narrowing_runtime_config_guard_decisions,
)


POLICY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_NARROWING_POLICY_LEDGER_{DATE}.jsonl"
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
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
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    guard_config = normalize_ai_narrowing_runtime_config(config)
    policy_rows = read_jsonl(POLICY_LEDGER)
    policy_sha = sha256_path(POLICY_LEDGER)
    config_sha = sha256_path(CONFIG_PATH)
    registry = AINarrowingPolicyRegistry(policy_rows)
    runtime_halt_active = RUNTIME_HALT_FLAG.exists()

    eval_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    for index, policy_row in enumerate(policy_rows, start=1):
        event = ai_narrowing_policy_scope_event(
            policy_row,
            event_row_id=f"MAIN-ORCH48-AI-NARROWING-RUNTIME-CONFIG-EVENT-{index:08d}",
        )
        evaluation = registry.evaluate_event(
            event,
            evaluation_row_id=f"MAIN-ORCH48-AI-NARROWING-RUNTIME-CONFIG-EVAL-{index:08d}",
        )
        decision = ai_narrowing_runtime_config_guard_decision(
            evaluation,
            config=config,
            runtime_halt_active=runtime_halt_active,
            decision_row_id=f"MAIN-ORCH48-AI-NARROWING-RUNTIME-CONFIG-DECISION-{index:08d}",
        )
        decision.update(
            {
                "route_id": ROUTE_ID,
                "route_schema_version": SCHEMA_VERSION,
                "input_policy_row_id": policy_row.get("ai_narrowing_policy_row_id"),
                "policy_ledger_path": display_path(POLICY_LEDGER),
                "policy_ledger_sha256": policy_sha,
                "config_path": display_path(CONFIG_PATH),
                "config_sha256": config_sha,
                "runtime_halt_flag_path": display_path(RUNTIME_HALT_FLAG),
                "broker_operation": False,
            }
        )
        eval_rows.append(evaluation)
        decision_rows.append(decision)

    write_jsonl(OUTPUT_LEDGER, decision_rows)
    decision_summary = summarize_ai_narrowing_runtime_config_guard_decisions(decision_rows)
    eval_summary = summarize_ai_narrowing_policy_registry_evaluations(eval_rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated,
        "status": "OK_DEFAULT_OFF_AI_NARROWING_RUNTIME_CONFIG_GUARD_DOCUMENTED",
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "policy_ledger": {
            "path": display_path(POLICY_LEDGER),
            "sha256": policy_sha,
            "rows": len(policy_rows),
        },
        "config_source": {
            "path": display_path(CONFIG_PATH),
            "sha256": config_sha,
            "ai_narrowing": guard_config,
        },
        "runtime_halt_active": runtime_halt_active,
        "decision_summary": decision_summary,
        "registry_eval_summary": eval_summary,
        "implementation_effect": {
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
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
            "This plate adds the explicit default-off config guard and evaluates policy rows against it. "
            "It does not wire a selector into PrimaryAnalyzer, skip AI calls, restart runtime, or touch broker state."
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
        "decision_rows": len(decision_rows),
        "status": summary["status"],
        "runtime_halt_active": runtime_halt_active,
        "ai_call_skip_allowed_now_rows": decision_summary["ai_call_skip_allowed_now_rows"],
        "runtime_eligible_after_all_gates_rows": decision_summary["runtime_eligible_after_all_gates_rows"],
        "manifest_output_count": len(outputs),
    }


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, sort_keys=True))
