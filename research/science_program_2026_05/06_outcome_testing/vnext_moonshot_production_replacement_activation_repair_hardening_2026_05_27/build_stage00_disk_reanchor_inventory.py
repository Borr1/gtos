from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
PRIOR_ROUTE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_production_replacement_activation_2026_05_26"
)

CONTROL_PROMPT = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    / "VNEXT_MOONSHOT_PRODUCTION_REPLACEMENT_ACTIVATION_REPAIR_HARDENING_GOAL_PROMPT_2026-05-27.md"
)

STAGE00 = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE00_DISK_REANCHOR_{DATE}.json"
READ_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_REQUIRED_FILE_READ_LEDGER_{DATE}.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"
REPAIR_INVENTORY = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_INVENTORY_{DATE}.json"
NUMBER_FREEZE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_ACTIVATION_NUMBER_FREEZE_{DATE}.json"
DIRTY_CLASSIFICATION = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_DIRTY_FILE_CLASSIFICATION_{DATE}.json"
STAGE_SPINE = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"


REQUIRED_FILES = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_63_VNEXT_EXACT_R_SOURCE_REPAIR_GUARD_HANDOFF_2026-05-19.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_READING_ORDER.md",
    ".context/00_core/goal_session_research_discipline.md",
    "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_PRODUCTION_REPLACEMENT_ACTIVATION_REPAIR_HARDENING_GOAL_PROMPT_2026-05-27.md",
    "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_PRODUCTION_REPLACEMENT_ACTIVATION_GOAL_PROMPT_2026-05-26.md",
    "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_PRODUCTION_REPLACEMENT_ACTIVATION_STARTER_2026-05-26.txt",
    "config/agent_config.yaml",
    "config/profiles/redacted_account.yaml",
    "src/components/orchestrator.py",
    "src/components/execution.py",
    "src/components/gtos_vnext_runtime.py",
    "src/components/broader_origin_generators.py",
    "src/research/moonshot_default_off_policy_router.py",
    "scripts/_live_monitor_iter.py",
]


NAMED_REPAIR_GATES = [
    ("stage12_selected_count_truth", "repair stale 287390 selected-row assertion; derive current selector truth"),
    ("stage12_semantic_exit_code", "return nonzero on failed activation gates and missing proofs"),
    ("stage13_completion_audit_result_ingestion", "replace hardcoded pass strings with fresh machine-readable evidence"),
    ("manifest_hash_truth", "verify every manifest entry hash against current route artifacts"),
    ("rollback_executable_proof", "prove rollback overlay through runnable temp config/tests without repo mutation"),
    ("vnext_native_prescreen_news_parity", "apply valid prescreen/news controls in the vNext path without legacy fallback"),
    ("dynamic_pending_fill_persistence", "persist placement-time dynamic execution fields through limit fill/open_trade"),
    ("execution_policy_support_matrix", "fail execution-active unsupported dynamic policies"),
    ("broker_resolved_monitor_tick_parity", "remove old 5/7-symbol ceilings from monitor/tick surfaces"),
    ("broker_alias_repair_ger_oil", "non-mutating MT5 verification for GER30, UKOUSD, and USOUSD"),
    ("pending_notification_parity", "notify/log broader-origin pending placement with dynamic policy and selector proof"),
    ("redacted_account_risk_broker_geometry_current_specs", "rederive broker/risk geometry from current symbol evidence"),
    ("cost_slippage_commission_fill_capture", "capture decision/send/fill cost and lifecycle truth prospectively"),
    ("route_state_head_integrity", "repair stale current_head and prove route metadata matches git HEAD"),
    ("non_mutating_check_mode", "split write/check modes and prove check mode does not rewrite artifacts"),
    ("fake_completion_dead_selector_gates", "fail safe-but-dead selector collapse and completion self-certification"),
    ("canonical_frequency_executable_trade_ledger", "row-level membership/frequency/R ledger reconciling selector/risk/runtime paths"),
    ("prior_question_anatomy_consumption", "dereference prior question/anatomy closure rows into runtime/config/tests/exclusions"),
]


def _git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _status_paths(status_output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        rows.append({"status": status, "path": path.replace("\\", "/")})
    return rows


def _classify_dirty(path: str) -> str:
    if path.startswith(_rel(ROUTE_DIR) + "/"):
        return "current_route_owned"
    if path == ".context/LIVE_STATE.md":
        return "mandatory_preflight_regeneration"
    if path.startswith(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    ):
        return "pre_existing_full_replay_artifact_drift_not_owned_by_this_route"
    if path.startswith(
        "research/science_program_2026_05/04_goal_prompts/"
        "VNEXT_MOONSHOT_PRODUCTION_REPLACEMENT_ACTIVATION_REPAIR_HARDENING"
    ):
        return "current_route_controlling_prompt_untracked_input"
    if path.startswith("research/science_program_2026_05/04_goal_prompts/VNEXT_"):
        return "pre_existing_untracked_prompt_input_not_owned_by_stage00"
    if path.startswith(
        "research/science_program_2026_05/06_outcome_testing/"
        "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/"
    ):
        return "pre_existing_prior_route_artifact_input_not_owned_by_stage00"
    return "unclassified_pre_existing_or_external_dirty_path"


def _file_record(path_text: str, generated_at: str) -> dict[str, Any]:
    path = REPO_ROOT / path_text
    return {
        "exists": path.exists(),
        "generated_at_utc": generated_at,
        "path": path_text,
        "route_id": ROUTE_ID,
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "status": "read_required_preflight_input",
    }


def _activation_number_freeze(generated_at: str) -> dict[str, Any]:
    selector_summary = _read_json(
        PRIOR_ROUTE_DIR
        / "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json"
    )
    outside_summary = _read_json(
        PRIOR_ROUTE_DIR
        / "VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_SUMMARY_2026-05-26.json"
    )
    outside_verifier = _read_json(
        PRIOR_ROUTE_DIR
        / "VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_VERIFIER_2026-05-26.json"
    )
    redacted_account_summary = _read_json(
        PRIOR_ROUTE_DIR
        / "VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_2026-05-26.json"
    )
    metrics = selector_summary.get("combined_production_selector_metrics", {})
    return {
        "broader_origin_selected_rows": selector_summary.get("broader_origin_selected_rows"),
        "combined_selected_rows": selector_summary.get("combined_selected_rows"),
        "expected_selector_anchor": {
            "broader_origin_selected_rows": 213398,
            "combined_selected_rows": 274146,
            "expectancy_r": 0.44786181532328045,
            "old_three_selected_rows": 60748,
            "profit_factor": 2.4382409880020854,
            "total_r": 122779.52522361604,
            "win_rate_percent": 50.69743859111568,
        },
        "generated_at_utc": generated_at,
        "metrics": {
            "expectancy_r": metrics.get("expectancy_r"),
            "profit_factor": metrics.get("profit_factor"),
            "total_r": metrics.get("total_r"),
            "win_rate": metrics.get("win_rate"),
            "win_rate_percent": (
                metrics.get("win_rate") * 100 if isinstance(metrics.get("win_rate"), (int, float)) else None
            ),
        },
        "old_three_selected_rows": selector_summary.get("old_three_selected_rows"),
        "outside_session_risk_reconciliation": {
            "risk_disposition_row_counts": outside_summary.get("risk_disposition_row_counts"),
            "row_counts": outside_verifier.get("row_counts"),
            "status": outside_summary.get("status"),
            "verifier_status": outside_verifier.get("status"),
        },
        "redacted_account_broker_risk_geometry": {
            "row_counts": redacted_account_summary.get("row_counts"),
            "risk_unresolved_reason_counts": redacted_account_summary.get("risk_unresolved_reason_counts"),
            "status": redacted_account_summary.get("status"),
        },
        "input_paths": {
            "selector_summary": _rel(
                PRIOR_ROUTE_DIR
                / "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json"
            ),
            "outside_session_risk_summary": _rel(
                PRIOR_ROUTE_DIR
                / "VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_RISK_RECONCILIATION_SUMMARY_2026-05-26.json"
            ),
            "redacted_account_summary": _rel(
                PRIOR_ROUTE_DIR
                / "VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_2026-05-26.json"
            ),
        },
        "route_id": ROUTE_ID,
        "status": "frozen_from_current_disk_evidence_pending_recompute_verifier",
    }


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    head = _git(["log", "-1", "--oneline"])
    head_sha = _git(["rev-parse", "--short=9", "HEAD"])
    status_output = _git(["status", "--short"])
    dirty_rows = _status_paths(status_output)

    read_rows = [_file_record(path, generated_at) for path in REQUIRED_FILES]
    missing_required = [row["path"] for row in read_rows if not row["exists"]]
    _write_jsonl(READ_LEDGER, read_rows)

    repair_rows = [
        {
            "gate_id": gate_id,
            "description": description,
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_owner": "stage_01_to_stage_04",
            "status": "open_repair_gate",
        }
        for gate_id, description in NAMED_REPAIR_GATES
    ]
    _write_json(REPAIR_INVENTORY, {"generated_at_utc": generated_at, "repair_gates": repair_rows, "route_id": ROUTE_ID})

    number_freeze = _activation_number_freeze(generated_at)
    _write_json(NUMBER_FREEZE, number_freeze)

    classified_dirty = [
        {**row, "classification": _classify_dirty(row["path"])} for row in dirty_rows
    ]
    _write_json(
        DIRTY_CLASSIFICATION,
        {
            "dirty_paths": classified_dirty,
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "status": "dirty_paths_classified_before_stage00_generation",
        },
    )

    stage00 = {
        "control_prompt": _rel(CONTROL_PROMPT),
        "control_prompt_sha256": _sha256(CONTROL_PROMPT),
        "current_head": head,
        "current_head_sha": head_sha,
        "generated_at_utc": generated_at,
        "missing_required_files": missing_required,
        "prior_activation_route": _rel(PRIOR_ROUTE_DIR),
        "route_id": ROUTE_ID,
        "stage": "stage_00_disk_reanchor_and_repair_inventory",
        "status": "failed_missing_required_file" if missing_required else "completed_stage00_reanchor_inventory",
    }
    _write_json(STAGE00, stage00)

    control_rows = [
        {
            "current_head": head,
            "event": "stage00_disk_reanchor_inventory_written",
            "generated_at_utc": generated_at,
            "missing_required_files": missing_required,
            "route_id": ROUTE_ID,
            "status": stage00["status"],
        }
    ]
    _write_jsonl(CONTROL_LEDGER, control_rows)

    spine = {
        "active_files": [_rel(path) for path in [STAGE00, READ_LEDGER, CONTROL_LEDGER, REPAIR_INVENTORY, NUMBER_FREEZE, DIRTY_CLASSIFICATION]],
        "completed_gates": ["mandatory_preflight_regenerated_live_state", "stage00_repair_inventory_written"],
        "current_head": head,
        "current_stage": "stage_01_acceptance_and_evidence_hardening",
        "generated_at_utc": generated_at,
        "latest_numbers": number_freeze,
        "latest_test_commands": [],
        "next_exact_action": "Repair Stage12 selected-count test and semantic verifier fail exit, then add manifest/check-mode verifiers.",
        "open_gates": [row["gate_id"] for row in repair_rows],
        "route_id": ROUTE_ID,
        "stage_status": {
            "stage_00_disk_reanchor_and_repair_inventory": stage00["status"],
            "stage_01_acceptance_and_evidence_hardening": "in_progress",
            "stage_02_runtime_path_hardening": "pending",
            "stage_03_broker_risk_monitoring_alias_cost_capture": "pending",
            "stage_04_frequency_distribution_intelligence_consumption": "pending",
            "stage_05_full_verification_matrix": "pending",
            "stage_06_commit_and_final_route_state": "pending",
        },
    }
    _write_json(STAGE_SPINE, spine)

    manifest_outputs = []
    for path in [STAGE00, READ_LEDGER, CONTROL_LEDGER, REPAIR_INVENTORY, NUMBER_FREEZE, DIRTY_CLASSIFICATION, STAGE_SPINE]:
        manifest_outputs.append(
            {
                "path": _rel(path),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
                "stage": "stage_00",
                "status": "created",
            }
        )
    _write_json(
        OUTPUT_MANIFEST,
        {
            "generated_at_utc": generated_at,
            "outputs": manifest_outputs,
            "route_id": ROUTE_ID,
            "schema_version": "vnext_activation_repair_manifest_v1",
            "status": stage00["status"],
        },
    )

    print(json.dumps({"route_id": ROUTE_ID, "status": stage00["status"], "open_gates": len(repair_rows)}, sort_keys=True))
    return 0 if not missing_required else 1


if __name__ == "__main__":
    raise SystemExit(main())
