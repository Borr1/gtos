#!/usr/bin/env python3
"""Build a daily GTOS monitoring checklist from active runbooks.

The checklist is an operations artifact only. It does not call MT5, AI,
canaries, Databento, Sierra, or order/execution code.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_limitations_to_opportunities_queue_state as lto_queue

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DEFAULT_DATE = "2026-05-05"
DEFAULT_RUNBOOK = Path(".context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md")
DEFAULT_OBSERVER_RUNBOOK = Path(".context/05_operations/SHADOW_OBSERVER_RUNBOOK_2026-05-04.md")
DEFAULT_ACTIVE_GOAL = Path(".context/05_operations/GTOS_FULL_DAY_ACTIVE_MONITORING_GOAL_PROMPT_2026-05-04.md")
DEFAULT_PLAN = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_ENGINEERING_PLAN_2026-05-05.md")
DEFAULT_LTO_QUEUE_JSON = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.json")
DEFAULT_NEXT_IMPROVEMENTS_GOAL = Path(".context/05_operations/NEXT_IMPROVEMENTS_AND_LTO031_032_GOAL_PROMPT_2026-05-06.md")
DEFAULT_LTO031032_COMPLETION_AUDIT = Path("research/operations/NEXT_IMPROVEMENTS_LTO031_032_COMPLETION_AUDIT_2026-05-06.md")
DEFAULT_OUTPUT_JSON = Path("research/program_control/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path(".context/05_operations/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.md")

COMMAND_RE = re.compile(r"^\s*(python(?:\.exe)?\s+[^\n`]+?)\s*$", flags=re.MULTILINE)

BASELINE_COMMANDS = [
    "python scripts/generate_live_state.py",
    "python scripts/watchdog_e2e_verify.py --verbose",
    "python scripts/verify_forward_capture_readiness.py --output-json research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md",
    "python scripts/audit_live_shadow_followup_coverage.py --output-json research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json --output-md research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md",
]

LIVE_SHADOW_SEQUENCE = [
    "python scripts/run_live_monitoring_maintenance.py --max-hours 24 --step-timeout-seconds 900",
    "python scripts/_live_monitor_iter.py",
    "python scripts/follow_live_candidate_paths.py --max-hours 12",
    "python scripts/backfill_ai_narrowing_policy_shadow_evaluations.py",
    "python scripts/backfill_candidate_registry_audit.py",
    "python scripts/backfill_candidate_path_contract_audit.py",
    "python scripts/backfill_opportunity_lifecycle_audit.py",
    "python scripts/backfill_pending_limit_lifecycle_audit.py",
    "python scripts/backfill_v2b_forward_pair_resolution_audit.py",
    "python scripts/audit_v2_structural_selector_readiness.py",
    "python scripts/backfill_prefill_delivery_path_audit.py",
    "python scripts/backfill_fvg_ob_confluence_source_geometry.py",
    "python scripts/backfill_fvg_ob_confluence_audit.py",
    "python scripts/backfill_context_control_audit.py",
    "python scripts/backfill_broker_actual_r_audit.py",
    "python scripts/backfill_j46_j49_exit_comparator_audit.py",
    "python scripts/backfill_s79_side_aware_risk_context.py",
    "python scripts/backfill_regime_decay_outcome_join.py",
    "python scripts/backfill_decision_layer_diagnostics_join.py",
    "python scripts/audit_cross_instrument_correlation_decisions.py",
    "python scripts/backfill_mechanical_context_diagnostics_join.py",
    "python scripts/backfill_k55_ml_shadow_predictions.py",
    "python scripts/audit_lto_blocked_lane_readiness.py",
    "python scripts/audit_xauusd_same_market_extension.py",
    "python scripts/audit_es_mes_preregistration.py",
    "python scripts/audit_shadow_observer_hardening.py",
    "python scripts/backfill_account_pnl_truth_reconciliation.py",
    "python scripts/backfill_trade_index_lifecycle_audit.py",
    "python scripts/audit_sierra_proxy_registry.py",
    "python scripts/enrich_sierra_live_candidate_depth_features.py --max-hours 24 --max-file-size-mb 128 --max-per-symbol 2 --limit 6",
    "python scripts/audit_sierra_live_depth_confluence.py",
    "python scripts/audit_nas100_orderflow_adverse_selection.py",
    "python scripts/audit_gbpjpy_orderflow_proxy_gap.py",
    "python scripts/audit_sierra_6b_si_depth_policy.py",
    "python scripts/audit_orderflow_primitives.py",
    "python scripts/backfill_exit_management_no_event_status.py",
    "python scripts/audit_session_volatility_sweep_status.py",
    "python scripts/audit_notification_queue_dead_zone.py",
    "python scripts/audit_storage_retention.py --dry-run",
    "python scripts/summarize_live_shadow_opportunities.py",
    "python scripts/verify_shadow_log_integrity.py",
    "python scripts/audit_live_shadow_data_health.py",
]

RESEARCH_INTELLIGENCE_SEQUENCE = [
    "python scripts/backfill_m15_choch_diagnostics.py",
    "python scripts/backfill_continuation_no_retrace_shadow.py",
    "python scripts/backfill_xagusd_fresh_ob_late_ny.py",
]

SOURCE_GOVERNANCE_SEQUENCE = [
    "python scripts/build_lto031_lto032_source_contract_registry.py",
    "python scripts/build_lto031_lto032_free_public_source_manifests.py",
    "python scripts/build_lto031_lto032_databento_credit_replay_manifests.py",
    "python scripts/build_lto031_lto032_sierra_scid_footprint_profile_plan.py",
    "python scripts/build_lto032_options_gamma_vrp_source_manifests.py",
    "python scripts/build_k55_source_bundle_integration_plan.py",
]

SUPPLEMENTAL_RESEARCH_LANES = [
    {
        "lto_id": "NEXT-M15-CHOCH",
        "title": "M15 CHoCH Diagnostic Expansion",
        "status": "RESEARCH_SHADOW_ONLY",
        "follow_id": "NEXT-IMPROVEMENT-2B",
        "coverage_statuses": ["ROWS_PRESENT", "NO_PROMOTION_VERDICT"],
        "row_paths": [
            "shadow_logs/m15_choch_diagnostic_audit.jsonl",
            "research/program_control/M15_CHOCH_DIAGNOSTIC_AUDIT_2026-05-06.json",
        ],
    },
    {
        "lto_id": "NEXT-CONTINUATION-NO-RETRACE",
        "title": "Continuation / No-Retrace Shadow Lane",
        "status": "RESEARCH_SHADOW_ONLY",
        "follow_id": "NEXT-IMPROVEMENT-2A",
        "coverage_statuses": ["ROWS_PRESENT", "NO_PROMOTION_VERDICT"],
        "row_paths": [
            "shadow_logs/continuation_no_retrace_candidates.jsonl",
            "shadow_logs/continuation_no_retrace_resolutions.jsonl",
            "research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.json",
        ],
    },
    {
        "lto_id": "NEXT-XAGUSD-FRESH-OB",
        "title": "XAGUSD Fresh-OB Late-NY Tracking",
        "status": "RESEARCH_SHADOW_ONLY",
        "follow_id": "NEXT-IMPROVEMENT-2C",
        "coverage_statuses": ["ROWS_PRESENT", "NO_PROMOTION_VERDICT"],
        "row_paths": [
            "shadow_logs/xagusd_fresh_ob_late_ny.jsonl",
            "research/program_control/XAGUSD_FRESH_OB_LATE_NY_STATUS_2026-05-06.json",
        ],
    },
    {
        "lto_id": "LTO-031/LTO-032-P0-P4",
        "title": "LTO031/LTO032 Source Contracts And Manifests",
        "status": "SOURCE_GOVERNANCE_READY_SHADOW_ONLY",
        "follow_id": "SOURCE-GOVERNANCE-2026-05-06",
        "coverage_statuses": ["SOURCE_CONTRACTS_PRESENT", "NO_PROMOTION_VERDICT"],
        "row_paths": [
            "research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
            "research/program_control/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.json",
            "research/program_control/LTO031_LTO032_DATABENTO_CREDIT_REPLAY_MANIFESTS_2026-05-06.json",
            "research/program_control/LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.json",
            "research/program_control/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.json",
        ],
    },
    {
        "lto_id": "LTO-023/LTO-031/LTO-032-P5",
        "title": "K55 Source-Bundle Governance",
        "status": "K55_SOURCE_BUNDLE_GOVERNANCE_READY_SHADOW_ONLY",
        "follow_id": "K55-SOURCE-BUNDLE-2026-05-06",
        "coverage_statuses": ["SOURCE_BUNDLE_PLAN_PRESENT", "NUMERIC_FEATURES_DISABLED", "NO_PROMOTION_VERDICT"],
        "row_paths": [
            "research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.json",
            "research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md",
        ],
    },
]

RESTART_POLICY = [
    {
        "component": "production_orchestrators",
        "policy": "Restart only after additive capture code is changed and tests pass, or after a verified active-KZ failure. Use the existing durable Windows scheduled task when a full fleet reload is required.",
    },
    {
        "component": "shadow_observer",
        "policy": "Restart after observer schema/lifecycle changes or verified observer staleness; keep no-AI/no-order/no-Databento boundaries intact.",
    },
    {
        "component": "watchdog_notification",
        "policy": "Restart or wait for scheduled watchdog only after dead-zone policy changes; do not force notification workers during expected dead-zone cleanup.",
    },
    {
        "component": "sierra",
        "policy": "Do not restart Sierra unless file capture stalls or chartbook/source setup requires operator-side action.",
    },
    {
        "component": "databento",
        "policy": "Databento live collection is owner-approved for LTO010 value-max forward confluence. Start only through the registered collector when a trigger exists, collector env/API key are present, and cost/cooldown caps pass; every paid call must land in the confluence and budget ledgers with candidate/trigger join keys.",
    },
]


def read_text(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def extract_python_commands(*texts: str) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for match in COMMAND_RE.findall(text):
            command = " ".join(match.strip().split())
            normalized = command.replace("\\", "/")
            if normalized in seen:
                continue
            seen.add(normalized)
            commands.append(command)
    return commands


def load_lto_queue(path: str | Path = DEFAULT_LTO_QUEUE_JSON) -> dict[str, Any]:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return lto_queue.build_payload()


def lane_rows_from_queue(queue_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in queue_payload.get("items", []):
        if not item.get("follow_ids"):
            rows.append(
                {
                    "lto_id": item["id"],
                    "title": item["title"],
                    "status": item["status"],
                    "follow_id": "",
                    "coverage_statuses": item.get("coverage_statuses", []),
                    "row_paths": item.get("row_paths", []),
                }
            )
            continue
        for follow_id in item["follow_ids"]:
            rows.append(
                {
                    "lto_id": item["id"],
                    "title": item["title"],
                    "status": item["status"],
                    "follow_id": follow_id,
                    "coverage_statuses": item.get("coverage_statuses", []),
                    "row_paths": item.get("row_paths", []),
                }
            )
    return rows


def build_payload(
    checklist_date: str = DEFAULT_DATE,
    runbook_path: str | Path = DEFAULT_RUNBOOK,
    observer_runbook_path: str | Path = DEFAULT_OBSERVER_RUNBOOK,
    active_goal_path: str | Path = DEFAULT_ACTIVE_GOAL,
    plan_path: str | Path = DEFAULT_PLAN,
    lto_queue_json_path: str | Path = DEFAULT_LTO_QUEUE_JSON,
    next_improvements_goal_path: str | Path = DEFAULT_NEXT_IMPROVEMENTS_GOAL,
    lto031032_completion_audit_path: str | Path = DEFAULT_LTO031032_COMPLETION_AUDIT,
) -> dict[str, Any]:
    runbook_text = read_text(runbook_path)
    observer_text = read_text(observer_runbook_path)
    active_goal_text = read_text(active_goal_path)
    plan_text = read_text(plan_path)
    queue_payload = load_lto_queue(lto_queue_json_path)
    runbook_commands = extract_python_commands(runbook_text, observer_text, active_goal_text, plan_text)
    all_commands = []
    seen: set[str] = set()
    for command in [
        *BASELINE_COMMANDS,
        *LIVE_SHADOW_SEQUENCE,
        *RESEARCH_INTELLIGENCE_SEQUENCE,
        *SOURCE_GOVERNANCE_SEQUENCE,
        *runbook_commands,
    ]:
        normalized = command.replace("\\", "/")
        if normalized in seen:
            continue
        seen.add(normalized)
        all_commands.append(command)

    return {
        "schema_version": "gtos_daily_monitoring_checklist_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "checklist_date": checklist_date,
        "promotion_verdict": PROMOTION_VERDICT,
        "source_documents": [
            str(runbook_path),
            str(observer_runbook_path),
            str(active_goal_path),
            str(plan_path),
            str(lto_queue_json_path),
            str(next_improvements_goal_path),
            str(lto031032_completion_audit_path),
        ],
        "required_commands": {
            "baseline": BASELINE_COMMANDS,
            "live_shadow_sequence": LIVE_SHADOW_SEQUENCE,
            "research_intelligence_sequence": RESEARCH_INTELLIGENCE_SEQUENCE,
            "source_governance_sequence": SOURCE_GOVERNANCE_SEQUENCE,
            "runbook_commands": runbook_commands,
            "all_unique_commands": all_commands,
        },
        "expected_lanes": [*lane_rows_from_queue(queue_payload), *SUPPLEMENTAL_RESEARCH_LANES],
        "restart_policy": RESTART_POLICY,
        "safety_counters_required": {
            "ai_calls": 0,
            "order_calls": 0,
            "paid_data_calls": 0,
        },
        "paid_data_exception": {
            "component": "databento",
            "policy": "Allowed only for the LTO010 registered live collector; non-collector monitoring/backfill scripts must keep paid_data_calls=0.",
            "required_ledgers": [
                "shadow_logs/databento_live_confluence.jsonl",
                "shadow_logs/databento_live_budget_ledger.jsonl",
            ],
        },
        "cadence": {
            "active_kill_zone": "every 5 minutes",
            "between_kill_zones": "every 15 minutes",
            "owner_update": "every 30 minutes and immediately for verified URGENT/SERIOUS findings",
        },
        "blocked_lane_handling": {
            "SOURCE_NOT_CAPTURED": "preserve blocker unless exact point-in-time source evidence exists",
            "SOURCE_BLOCKED": "write/read blocker rows or reports; do not infer values",
            "APPROVAL_BLOCKED": "do not activate or call blocked service/model without owner approval",
            "EVENT_WAITING": "emit no-event/status proof where applicable",
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GTOS Daily Monitoring Checklist - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['created_at_utc']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Required Commands",
        "",
        "### Baseline",
        "",
    ]
    for command in payload["required_commands"]["baseline"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "### Live Shadow Sequence", ""])
    for command in payload["required_commands"]["live_shadow_sequence"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "### Research Intelligence Sequence", ""])
    for command in payload["required_commands"].get("research_intelligence_sequence", []):
        lines.append(f"- `{command}`")
    lines.extend(["", "### Source Governance Sequence", ""])
    for command in payload["required_commands"].get("source_governance_sequence", []):
        lines.append(f"- `{command}`")
    lines.extend(["", "### Additional Runbook Commands", ""])
    for command in payload["required_commands"]["runbook_commands"]:
        lines.append(f"- `{command}`")

    lines.extend(
        [
            "",
            "## Expected Lanes",
            "",
            "| Follow ID | LTO | Status | Row paths |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["expected_lanes"]:
        follow_id = f"`{row['follow_id']}`" if row["follow_id"] else "-"
        row_paths = ", ".join(f"`{path}`" for path in row.get("row_paths", [])) or "-"
        lines.append(f"| {follow_id} | `{row['lto_id']}` {row['title']} | `{row['status']}` | {row_paths} |")

    lines.extend(["", "## Restart Policy", ""])
    for item in payload["restart_policy"]:
        lines.append(f"- `{item['component']}`: {item['policy']}")

    lines.extend(
        [
            "",
            "## Safety Counters",
            "",
            "| Counter | Required value |",
            "|---|---:|",
        ]
    )
    for counter, value in payload["safety_counters_required"].items():
        lines.append(f"| `{counter}` | {value} |")

    lines.extend(
        [
            "",
            "## Cadence",
            "",
            f"- Active kill zone: {payload['cadence']['active_kill_zone']}",
            f"- Between kill zones: {payload['cadence']['between_kill_zones']}",
            f"- Owner update: {payload['cadence']['owner_update']}",
            "",
            "## Blocked Lane Handling",
            "",
        ]
    )
    for status, rule in payload["blocked_lane_handling"].items():
        lines.append(f"- `{status}`: {rule}")
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: str | Path, output_md: str | Path) -> None:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=DEFAULT_DATE)
    parser.add_argument("--runbook", default=str(DEFAULT_RUNBOOK))
    parser.add_argument("--observer-runbook", default=str(DEFAULT_OBSERVER_RUNBOOK))
    parser.add_argument("--active-goal", default=str(DEFAULT_ACTIVE_GOAL))
    parser.add_argument("--plan", default=str(DEFAULT_PLAN))
    parser.add_argument("--lto-queue-json", default=str(DEFAULT_LTO_QUEUE_JSON))
    parser.add_argument("--next-improvements-goal", default=str(DEFAULT_NEXT_IMPROVEMENTS_GOAL))
    parser.add_argument("--lto031032-completion-audit", default=str(DEFAULT_LTO031032_COMPLETION_AUDIT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    args = parser.parse_args()

    payload = build_payload(
        checklist_date=args.date,
        runbook_path=args.runbook,
        observer_runbook_path=args.observer_runbook,
        active_goal_path=args.active_goal,
        plan_path=args.plan,
        lto_queue_json_path=args.lto_queue_json,
        next_improvements_goal_path=args.next_improvements_goal,
        lto031032_completion_audit_path=args.lto031032_completion_audit,
    )
    write_outputs(payload, args.output_json, args.output_md)
    print(
        "wrote "
        f"{args.output_json} and {args.output_md}; "
        f"commands={len(payload['required_commands']['all_unique_commands'])} "
        f"lanes={len(payload['expected_lanes'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
