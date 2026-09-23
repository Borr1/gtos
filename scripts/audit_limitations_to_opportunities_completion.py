#!/usr/bin/env python3
"""Audit completion of the 2026-05-05 limitations-to-opportunities goal.

This is a meta-audit. It inspects the active source-of-truth anchors, queue,
checklist, blockers, verifiers, and reports. It does not call live trading,
AI, canaries, Databento, MT5, Sierra, execution, or order code.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_limitations_to_opportunities_queue_state as queue_mod  # noqa: E402

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "limitations_to_opportunities_completion_audit_v1"
DEFAULT_GOAL_PROMPT = Path(".context/05_operations/LIMITATIONS_TO_OPPORTUNITIES_IMPLEMENTATION_GOAL_PROMPT_2026-05-05.md")
DEFAULT_PLAN = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_ENGINEERING_PLAN_2026-05-05.md")
DEFAULT_QUEUE_JSON = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.json")
DEFAULT_CHECKLIST_JSON = Path("research/program_control/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.json")
DEFAULT_INTEGRITY_JSON = Path("research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO_COMPLETION_2026-05-05.json")
DEFAULT_HEALTH_JSON = Path("research/operations/LIVE_SHADOW_DATA_HEALTH_AUDIT_LTO_COMPLETION_2026-05-05.json")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_COMPLETION_AUDIT_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_COMPLETION_AUDIT_2026-05-05.md")

REPORT_PATHS_BY_LTO: dict[str, list[str]] = {
    "LTO-001": ["research/program_control/LTO001_MSO_SNAPSHOT_JOIN_AUDIT_2026-05-05.md"],
    "LTO-002": ["research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.md"],
    "LTO-003": ["research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md"],
    "LTO-004": ["research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md"],
    "LTO-005": ["research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.md"],
    "LTO-006": ["research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md"],
    "LTO-007": ["research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md"],
    "LTO-008": ["research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.md"],
    "LTO-009": ["research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.md"],
    "LTO-010": ["research/program_control/LTO010_DATABENTO_LIVE_CONFLUENCE_POLICY_2026-05-05.md"],
    "LTO-011": ["research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md"],
    "LTO-012": ["research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md"],
    "LTO-013": ["research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md"],
    "LTO-014": ["research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md"],
    "LTO-015": ["research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md"],
    "LTO-016": ["research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md"],
    "LTO-017": ["research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.md"],
    "LTO-018": ["research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md"],
    "LTO-019": ["research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.md"],
    "LTO-020": ["research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.md"],
    "LTO-021": ["research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md"],
    "LTO-022": ["research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md"],
    "LTO-023": [
        "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md",
        "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md",
    ],
    "LTO-024": ["research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md"],
    "LTO-025": ["research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.md"],
    "LTO-026": ["research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md"],
    "LTO-027": ["research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md"],
    "LTO-028": ["research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md"],
    "LTO-029": [
        "research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.md",
        "research/program_control/ES_MES_STRATEGY_COHORT_REGISTRY_2026-05-05.md",
    ],
    "LTO-030": ["research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.md"],
    "LTO-031": ["research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md"],
    "LTO-032": ["research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md"],
    "LTO-033": [
        "research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.md",
        "research/program_control/ORDERFLOW_SHADOW_DATA_ACCELERATION_PLAN_2026-05-05.md",
    ],
    "LTO-034": ["research/program_control/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.json"],
    "LTO-035": [
        "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md",
        "research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.md",
    ],
    "LTO-036": ["research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.md"],
    "LTO-037": ["research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md"],
    "LTO-038": ["research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md"],
    "LTO-039": ["research/program_control/LTO039_SHADOW_LOG_SEMANTIC_VERIFIER_EXPANSION_2026-05-05.md"],
    "LTO-040": ["research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.md"],
}

REQUIRED_COMMANDS = [
    "python scripts/generate_live_state.py",
    "python scripts/verify_shadow_log_integrity.py",
    "python scripts/audit_live_shadow_data_health.py",
    "python scripts/audit_lto_blocked_lane_readiness.py",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _check(status: bool, requirement: str, evidence: str, severity: str = "BLOCKER") -> dict[str, Any]:
    return {
        "requirement": requirement,
        "status": "PASS" if status else "FAIL",
        "severity": severity,
        "evidence": evidence,
    }


def _no_issues(value: Any) -> bool:
    return value in ({}, [], None)


def artifact_status(root: Path, rel_path: str) -> dict[str, Any]:
    path = root / rel_path
    exists = path.exists()
    text = read_text(path)
    verdict_ok = PROMOTION_VERDICT in text if text else True
    if path.suffix.lower() == ".json":
        payload = read_json(path)
        verdict = payload.get("promotion_verdict") or payload.get("reports", {}).get("lto024", {}).get("promotion_verdict")
        verdict_ok = (verdict in {None, PROMOTION_VERDICT}) or (PROMOTION_VERDICT in text)
    return {
        "path": rel_path,
        "exists": exists,
        "promotion_verdict_ok": verdict_ok,
        "size_bytes": path.stat().st_size if exists and path.is_file() else 0,
    }


def build_payload(
    *,
    root: Path,
    goal_prompt: Path = DEFAULT_GOAL_PROMPT,
    plan_path: Path = DEFAULT_PLAN,
    queue_json_path: Path = DEFAULT_QUEUE_JSON,
    checklist_json_path: Path = DEFAULT_CHECKLIST_JSON,
    integrity_json_path: Path = DEFAULT_INTEGRITY_JSON,
    health_json_path: Path = DEFAULT_HEALTH_JSON,
) -> dict[str, Any]:
    generated_at = utc_now_iso()
    plan_sections = queue_mod.parse_lto_sections(plan_path)
    follow_to_lto, lto_to_follow = queue_mod.parse_followup_mapping(plan_path)
    queue_payload = read_json(root / queue_json_path)
    if not queue_payload:
        queue_payload = queue_mod.build_payload(plan_path, root=root)
    checklist = read_json(root / checklist_json_path)
    integrity = read_json(root / integrity_json_path)
    health = read_json(root / health_json_path)
    queue_items = queue_payload.get("items", [])
    by_id = {item.get("id"): item for item in queue_items}
    status_counts = queue_payload.get("summary", {}).get("status_counts", {})
    allowed_blocked = {"LTO-024", "LTO-031", "LTO-032"}
    failed = []

    artifact_rows = []
    for lto_id in sorted(plan_sections):
        paths = REPORT_PATHS_BY_LTO.get(lto_id, [])
        artifacts = [artifact_status(root, rel_path) for rel_path in paths]
        artifact_rows.append(
            {
                "lto_id": lto_id,
                "status": by_id.get(lto_id, {}).get("status"),
                "artifacts": artifacts,
                "all_required_artifacts_exist": bool(artifacts) and all(item["exists"] for item in artifacts),
                "promotion_verdict_ok": all(item["promotion_verdict_ok"] for item in artifacts),
            }
        )

    blocked_rows = [row for row in artifact_rows if row["lto_id"] in allowed_blocked]
    done_rows = [row for row in artifact_rows if by_id.get(row["lto_id"], {}).get("status") == "DONE"]
    active_or_ready = [
        item.get("id")
        for item in queue_items
        if item.get("status") in {"ACTIVE", "READY_TO_IMPLEMENT", "EVENT_WAITING"}
    ]
    unexpected_blocked = [
        item.get("id")
        for item in queue_items
        if item.get("status") in {"APPROVAL_BLOCKED", "SOURCE_BLOCKED"} and item.get("id") not in allowed_blocked
    ]

    all_required_commands = checklist.get("required_commands", {}).get("all_unique_commands", [])
    checklist_requirements = [
        _check(
            any(required in command for command in all_required_commands),
            f"Checklist includes `{required}`",
            f"commands={len(all_required_commands)}",
        )
        for required in REQUIRED_COMMANDS
    ]

    lto_blocker_status = []
    blocker_log_path = root / "shadow_logs/lto_blocked_lane_status.jsonl"
    if blocker_log_path.exists():
        for line in blocker_log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("lto_id") in allowed_blocked:
                lto_blocker_status.append(row)

    checks = [
        _check((root / goal_prompt).exists(), "Goal prompt anchor exists", str(goal_prompt)),
        _check((root / plan_path).exists(), "Engineering plan anchor exists", str(plan_path)),
        _check(len(plan_sections) == 40, "Plan has exactly 40 LTO sections", f"count={len(plan_sections)}"),
        _check(len(follow_to_lto) == 34, "Plan maps all 34 LIVE-FOLLOW rows", f"count={len(follow_to_lto)}"),
        _check(
            queue_payload.get("promotion_verdict") == PROMOTION_VERDICT,
            "Queue preserves NO_PROMOTION_VERDICT",
            str(queue_json_path),
        ),
        _check(
            queue_payload.get("summary", {}).get("unmapped_live_follow_ids") == [],
            "Queue has zero unmapped LIVE-FOLLOW rows",
            json.dumps(queue_payload.get("summary", {}).get("unmapped_live_follow_ids")),
        ),
        _check(
            active_or_ready == [],
            "No active, ready, or event-waiting LTO work remains",
            json.dumps(active_or_ready),
        ),
        _check(unexpected_blocked == [], "Only approved external blockers remain", json.dumps(unexpected_blocked)),
        _check(
            all(row["all_required_artifacts_exist"] for row in done_rows),
            "Every DONE LTO has required report/control artifacts",
            json.dumps([row["lto_id"] for row in done_rows if not row["all_required_artifacts_exist"]]),
        ),
        _check(
            all(row["all_required_artifacts_exist"] for row in blocked_rows),
            "Every blocked LTO has a blocker/readiness artifact",
            json.dumps([row["lto_id"] for row in blocked_rows if not row["all_required_artifacts_exist"]]),
        ),
        _check(
            all(row["promotion_verdict_ok"] for row in artifact_rows),
            "Required artifacts preserve NO_PROMOTION_VERDICT where applicable",
            json.dumps([row["lto_id"] for row in artifact_rows if not row["promotion_verdict_ok"]]),
        ),
        _check(
            len({row.get("lto_id") for row in lto_blocker_status}) == 3,
            "Blocked lane status log covers LTO-024, LTO-031, and LTO-032",
            json.dumps(sorted({row.get("lto_id") for row in lto_blocker_status})),
        ),
        _check(
            all(row.get("ai_calls") == 0 and row.get("order_calls") == 0 and row.get("paid_data_calls") == 0 for row in lto_blocker_status),
            "Blocked lane rows carry zero AI/order/paid-data counters",
            "shadow_logs/lto_blocked_lane_status.jsonl",
        ),
        _check(
            _no_issues(integrity.get("issues")),
            "Shadow-log integrity verifier has no issues",
            str(integrity_json_path),
        ),
        _check(
            _no_issues(health.get("issues")),
            "Live shadow data-health audit has no issues",
            str(health_json_path),
        ),
        _check(
            "audit_lto_blocked_lane_readiness.py" in json.dumps(checklist),
            "Daily checklist includes blocked-lane readiness audit",
            str(checklist_json_path),
        ),
        *checklist_requirements,
    ]

    for check in checks:
        if check["status"] != "PASS" and check["severity"] == "BLOCKER":
            failed.append(check)

    completion_status = "ACHIEVED_WITH_DOCUMENTED_EXTERNAL_BLOCKERS" if not failed else "INCOMPLETE"
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "objective_restatement": {
            "deliverable": "Convert every LTO/LIVE-FOLLOW limitation into tested infrastructure or an explicit blocker artifact while preserving NO_PROMOTION_VERDICT and no live behavior change.",
            "success_criteria": [
                "40 LTO items parsed and mapped to the 34 LIVE-FOLLOW lanes.",
                "No READY_TO_IMPLEMENT or ACTIVE rows remain.",
                "Every DONE item has a report/control artifact and relevant tests/verifiers.",
                "Every source/approval blocked item has an explicit blocker/readiness artifact.",
                "Integrity and data-health verifiers pass with documented waiting/source lanes only.",
                "Daily monitoring checklist carries the commands needed to keep rows fresh.",
            ],
        },
        "completion_status": completion_status,
        "can_mark_goal_complete": completion_status == "ACHIEVED_WITH_DOCUMENTED_EXTERNAL_BLOCKERS",
        "queue_status_counts": status_counts,
        "remaining_external_blockers": {
            "approval_blocked": ["LTO-024"],
            "source_blocked": ["LTO-031", "LTO-032"],
            "interpretation": "These are not unfinished implementation lanes in the approved scope; they are explicit external/source/approval blockers with readiness artifacts.",
        },
        "checks": checks,
        "artifact_rows": artifact_rows,
        "lto_to_follow_ids": {key: sorted(value) for key, value in sorted(lto_to_follow.items())},
        "verifier_evidence": {
            "integrity_overall_status": integrity.get("overall_status"),
            "integrity_issues": integrity.get("issues"),
            "data_health_status": health.get("status"),
            "data_health_issues": health.get("issues"),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Limitations To Opportunities Completion Audit - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['created_at_utc']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        f"**Completion status:** `{payload['completion_status']}`",
        f"**Can mark goal complete:** `{payload['can_mark_goal_complete']}`",
        "",
        "## Objective",
        "",
        payload["objective_restatement"]["deliverable"],
        "",
        "## Queue Status",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(payload["queue_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Prompt-To-Artifact Checks", "", "| Status | Requirement | Evidence |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['status']}` | {check['requirement']} | {check['evidence']} |")
    lines.extend(
        [
            "",
            "## Remaining External Blockers",
            "",
            "- `LTO-024`: approval-blocked; not approved for implementation/activation.",
            "- `LTO-031`: source-blocked; external feed sources require legal access path, schema, publication-time convention, and no-lookahead tests.",
            "- `LTO-032`: source-blocked/partial; FlashAlpha Basic is forward context only, while historical/aggregate GEX, VIX1D/VIX9D, and VRP remain source-blocked.",
            "",
            "## Artifact Coverage",
            "",
            "| LTO | Status | Artifacts present | Promotion verdict ok |",
            "|---|---|---:|---|",
        ]
    )
    for row in payload["artifact_rows"]:
        lines.append(
            f"| `{row['lto_id']}` | `{row['status']}` | `{row['all_required_artifacts_exist']}` | `{row['promotion_verdict_ok']}` |"
        )
    lines.extend(
        [
            "",
            "## NO_PROMOTION_VERDICT",
            "",
            "This audit is a completion/control artifact. It does not validate, promote, or alter live trading behavior.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    payload = build_payload(root=args.root)
    write_outputs(payload, args.output_json, args.output_md)
    print(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "completion_status": payload["completion_status"],
                "can_mark_goal_complete": payload["can_mark_goal_complete"],
                "failed_checks": [check["requirement"] for check in payload["checks"] if check["status"] != "PASS"],
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            sort_keys=True,
        )
    )
    return 0 if payload["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
