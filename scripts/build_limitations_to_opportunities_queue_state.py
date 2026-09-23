#!/usr/bin/env python3
"""Build the linked limitations-to-opportunities queue state.

This is a research/operations control artifact. It parses the active
limitations-to-opportunities plan and the live follow-up coverage audit, then
emits a durable queue state that keeps every LTO item mapped, statused, and
non-promotable.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
QUEUE_DATE = "2026-05-05"

DEFAULT_PLAN = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_ENGINEERING_PLAN_2026-05-05.md")
DEFAULT_COVERAGE_JSON = Path("research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json")
DEFAULT_OUTPUT_JSON = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.md")
LTO039_REPORT = Path("research/program_control/LTO039_SHADOW_LOG_SEMANTIC_VERIFIER_EXPANSION_2026-05-05.md")
LTO001_REPORT = Path("research/program_control/LTO001_MSO_SNAPSHOT_JOIN_AUDIT_2026-05-05.md")
LTO002_REPORT = Path("research/program_control/LTO002_CANDIDATE_REGISTRY_AUDIT_2026-05-05.md")
LTO003_REPORT = Path("research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md")
LTO004_REPORT = Path("research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md")
LTO005_REPORT = Path("research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.md")
LTO006_REPORT = Path("research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md")
LTO007_REPORT = Path("research/program_control/LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md")
LTO008_REPORT = Path("research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.md")
LTO009_REPORT = Path("research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.md")
LTO015_REPORT = Path("research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md")
LTO016_REPORT = Path("research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md")
LTO017_REPORT = Path("research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.md")
LTO018_REPORT = Path("research/program_control/LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md")
LTO019_REPORT = Path("research/program_control/LTO019_DECISION_LAYER_DIAGNOSTICS_JOIN_2026-05-05.md")
LTO020_REPORT = Path("research/program_control/LTO020_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_2026-05-05.md")
LTO023_REPORT = Path("research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md")
LTO024_REPORT = Path("research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md")
LTO027_REPORT = Path("research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md")
LTO028_REPORT = Path("research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md")
LTO029_REPORT = Path("research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.md")
LTO035_REPORT = Path("research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md")
LTO025_REPORT = Path("research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.md")
LTO026_REPORT = Path("research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md")
LTO010_REPORT = Path("research/program_control/LTO010_DATABENTO_LIVE_CONFLUENCE_POLICY_2026-05-05.md")
LTO011_REPORT = Path("research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md")
LTO012_REPORT = Path("research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.md")
LTO013_REPORT = Path("research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md")
LTO014_REPORT = Path("research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md")
LTO030_REPORT = Path("research/program_control/LTO030_6B_SI_DEPTH_POLICY_2026-05-05.md")
LTO031_REPORT = Path("research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md")
LTO032_REPORT = Path("research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md")
LTO033_REPORT = Path("research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.md")
LTO021_REPORT = Path("research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md")
LTO022_REPORT = Path("research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md")
LTO036_REPORT = Path("research/program_control/LTO036_CANARY_RESTART_GOVERNANCE_2026-05-05.md")
LTO037_REPORT = Path("research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md")
LTO038_REPORT = Path("research/program_control/LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md")

ALLOWED_STATUSES = {
    "ACTIVE",
    "READY_TO_IMPLEMENT",
    "APPROVAL_BLOCKED",
    "SOURCE_BLOCKED",
    "EVENT_WAITING",
    "DONE",
}

IMPLEMENTATION_ORDER = [
    "LTO-040",
    "LTO-034",
    "LTO-039",
    "LTO-001",
    "LTO-002",
    "LTO-003",
    "LTO-004",
    "LTO-005",
    "LTO-006",
    "LTO-007",
    "LTO-008",
    "LTO-009",
    "LTO-015",
    "LTO-025",
    "LTO-026",
    "LTO-010",
    "LTO-011",
    "LTO-012",
    "LTO-013",
    "LTO-014",
    "LTO-030",
    "LTO-031",
    "LTO-032",
    "LTO-033",
    "LTO-021",
    "LTO-022",
    "LTO-036",
    "LTO-037",
    "LTO-038",
    "LTO-016",
    "LTO-017",
    "LTO-018",
    "LTO-019",
    "LTO-020",
    "LTO-023",
    "LTO-024",
    "LTO-027",
    "LTO-028",
    "LTO-029",
    "LTO-035",
]

STATUS_OVERRIDES = {
    "LTO-024": "APPROVAL_BLOCKED",
    "LTO-031": "SOURCE_BLOCKED",
    "LTO-032": "SOURCE_BLOCKED",
}

BLOCKER_NOTES = {
    "LTO-010": "Owner-approved value-max trigger policy, cost cap, cooldown, env/API gate, and dry-run tooling are implemented; live Databento is no longer owner-approval-blocked but still requires enabled collector env/API key and a registered trigger.",
    "LTO-023": "Owner-approved read-only ML shadow path is implemented after target refresh/preregistration; prediction remains disabled until a matching registered model artifact exists, and no decision impact or promotion is allowed without a separate dossier.",
    "LTO-024": "Component 3B/tool-grounding/Reflexion must not wire or call AI without explicit owner approval.",
    "LTO-027": "Promotion-readiness audit is implemented and remains shadow-only: MT5 account history is used for filled broker outcomes where available, while unresolved shadow alternatives, exact V2 lock metadata, concentration, lifecycle, and preregistered dossier gates still block promotion.",
    "LTO-028": "XAUUSD same-market structural/path extension is preregistered as source-status only with outcomes closed at registration and live rows separated from replay evidence.",
    "LTO-029": "ES/MES strategy cohort is preregistered as context/control and future separate-cohort source status only, with source mapping, session windows, evidence classes, no-lookahead rules, and closed outcomes documented.",
    "LTO-035": "No-AI/no-execution observer hardening is implemented with a source/proxy/evidence-class registry, stale detection, restart policy, and GER40 final-closeout evidence; it does not enable new instruments or open outcomes.",
    "LTO-031": "Named external sources require legal access path, cache schema, and publication-time/no-lookahead convention before validation.",
    "LTO-032": "Options/gamma/VRP/GEX work requires legal timestamped source evidence before historical or forward collection.",
}

BLOCKER_ARTIFACTS = {
    "LTO-024": [LTO024_REPORT, Path("shadow_logs/lto_blocked_lane_status.jsonl")],
    "LTO-031": [LTO031_REPORT, Path("shadow_logs/lto_blocked_lane_status.jsonl")],
    "LTO-032": [LTO032_REPORT, Path("shadow_logs/lto_blocked_lane_status.jsonl")],
}

STATUS_REASON = {
    "ACTIVE": "currently selected for implementation",
    "READY_TO_IMPLEMENT": "safe additive research/tooling work remains",
    "APPROVAL_BLOCKED": "implementation or activation requires explicit owner approval",
    "SOURCE_BLOCKED": "source/access/legal/timestamp prerequisite is missing",
    "EVENT_WAITING": "correctly waiting for a future qualifying event",
    "DONE": "artifact-backed queue/checklist control work exists",
}

PRIOR_GAP_RE = re.compile(
    r"\b(?:FCI-ACTION-\d+|LIVE-FOLLOW-\d+B?|C-\d+|O-?\d+|P1-C-[A-Z0-9-]+|"
    r"H-PM\d+|ADR-\d+|OF-[A-Z0-9-]+|S79|K55)\b"
)


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip().replace(r"\|", "|") for cell in stripped.strip("|").split("|")]


def clean_cell(value: str) -> str:
    return value.replace("`", "").strip()


def extract_block(section: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.*)$", section, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    first_line = match.group(1).strip()
    tail = section[start:]
    next_match = re.search(
        r"^\s*(?:##\s+|Current state|Opportunity|Engineering action|Backfill|Validation|Prerequisite):?\s*",
        tail,
        flags=re.MULTILINE,
    )
    block = tail[: next_match.start()] if next_match else tail
    text = "\n".join(part for part in (first_line, block.strip()) if part).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def parse_lto_sections(plan_path: str | Path = DEFAULT_PLAN) -> dict[str, dict[str, Any]]:
    text = Path(plan_path).read_text(encoding="utf-8", errors="replace")
    matches = list(re.finditer(r"^### (LTO-\d{3}) - (.+)$", text, flags=re.MULTILINE))
    sections: dict[str, dict[str, Any]] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        item_id = match.group(1)
        sections[item_id] = {
            "id": item_id,
            "title": match.group(2).strip(),
            "current_state": extract_block(section, "Current state"),
            "opportunity": extract_block(section, "Opportunity"),
            "engineering_action": extract_block(section, "Engineering action"),
            "backfill": extract_block(section, "Backfill"),
            "validation": extract_block(section, "Validation"),
            "prerequisite": extract_block(section, "Prerequisite"),
        }
    return sections


def parse_followup_mapping(plan_path: str | Path = DEFAULT_PLAN) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    text = Path(plan_path).read_text(encoding="utf-8", errors="replace")
    follow_to_lto: dict[str, list[str]] = {}
    lto_to_follow: dict[str, list[str]] = {}
    for line in text.splitlines():
        cells = split_markdown_row(line)
        if len(cells) < 3:
            continue
        follow_id = clean_cell(cells[0])
        if not follow_id.startswith("LIVE-FOLLOW-"):
            continue
        lto_ids = re.findall(r"LTO-\d{3}", cells[2])
        follow_to_lto[follow_id] = lto_ids
        for lto_id in lto_ids:
            lto_to_follow.setdefault(lto_id, []).append(follow_id)
    return follow_to_lto, lto_to_follow


def load_coverage(path: str | Path = DEFAULT_COVERAGE_JSON) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"rows": [], "missing_coverage_path": str(p)}
    return json.loads(p.read_text(encoding="utf-8"))


def extract_prior_gap_ids(*texts: str) -> list[str]:
    found: set[str] = set()
    for text in texts:
        found.update(PRIOR_GAP_RE.findall(text or ""))
    return sorted(found)


def dynamic_status(item_id: str, unmapped_live_follow_ids: list[str], root: Path) -> str:
    if item_id == "LTO-040":
        script_exists = (root / "scripts/build_limitations_to_opportunities_queue_state.py").exists()
        return "DONE" if script_exists and not unmapped_live_follow_ids else "ACTIVE"
    if item_id == "LTO-034":
        script_exists = (root / "scripts/build_daily_monitoring_checklist.py").exists()
        return "DONE" if script_exists else "READY_TO_IMPLEMENT"
    if item_id == "LTO-039":
        report_exists = (root / LTO039_REPORT).exists()
        audit_exists = (root / "scripts/audit_live_shadow_data_health.py").exists()
        tests_exist = (root / "tests/test_live_shadow_data_health_audit.py").exists()
        return "DONE" if report_exists and audit_exists and tests_exist else "READY_TO_IMPLEMENT"
    if item_id == "LTO-001":
        report_exists = (root / LTO001_REPORT).exists()
        join_log_exists = (root / "shadow_logs/candidate_mso_snapshot_joins.jsonl").exists()
        helper_exists = (root / "src/research_infra/mso_snapshot_join.py").exists()
        backfill_exists = (root / "scripts/backfill_candidate_mso_snapshot_joins.py").exists()
        tests_exist = (root / "tests/test_mso_snapshot_join.py").exists()
        return "DONE" if all((report_exists, join_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-002":
        report_exists = (root / LTO002_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/candidate_registry_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/candidate_registry_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_candidate_registry_audit.py").exists()
        tests_exist = (root / "tests/test_candidate_registry_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-003":
        report_exists = (root / LTO003_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/candidate_path_contract_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/candidate_path_contract.py").exists()
        backfill_exists = (root / "scripts/backfill_candidate_path_contract_audit.py").exists()
        tests_exist = (root / "tests/test_candidate_path_contract.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-004":
        report_exists = (root / LTO004_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/opportunity_lifecycle_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/opportunity_lifecycle_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_opportunity_lifecycle_audit.py").exists()
        tests_exist = (root / "tests/test_opportunity_lifecycle_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-005":
        report_exists = (root / LTO005_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/pending_limit_lifecycle_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/pending_limit_lifecycle_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_pending_limit_lifecycle_audit.py").exists()
        tests_exist = (root / "tests/test_pending_limit_lifecycle_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-006":
        report_exists = (root / LTO006_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/v2b_forward_pair_resolution_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/v2b_forward_pair_resolution_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_v2b_forward_pair_resolution_audit.py").exists()
        tests_exist = (root / "tests/test_v2b_forward_pair_resolution_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-007":
        report_exists = (root / LTO007_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/prefill_delivery_path_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/prefill_delivery_path_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_prefill_delivery_path_audit.py").exists()
        tests_exist = (root / "tests/test_prefill_delivery_path_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-008":
        report_exists = (root / LTO008_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/fvg_ob_confluence_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/fvg_ob_confluence_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_fvg_ob_confluence_audit.py").exists()
        tests_exist = (root / "tests/test_fvg_ob_confluence_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-009":
        report_exists = (root / LTO009_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/context_control_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/context_control_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_context_control_audit.py").exists()
        tests_exist = (root / "tests/test_context_control_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-015":
        report_exists = (root / LTO015_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/broker_actual_r_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/broker_actual_r_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_broker_actual_r_audit.py").exists()
        exporter_exists = (root / "scripts/export_mt5_account_history_readonly.py").exists()
        tests_exist = (root / "tests/test_broker_actual_r_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, exporter_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-016":
        report_exists = (root / LTO016_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/j46_j49_exit_comparator_audit.jsonl").exists()
        helper_exists = (root / "src/research_infra/j46_j49_exit_comparator_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_j46_j49_exit_comparator_audit.py").exists()
        tests_exist = (root / "tests/test_j46_j49_exit_comparator_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-017":
        report_exists = (root / LTO017_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/s79_side_aware_risk_context.jsonl").exists()
        helper_exists = (root / "src/research_infra/s79_side_aware_risk_context.py").exists()
        backfill_exists = (root / "scripts/backfill_s79_side_aware_risk_context.py").exists()
        tests_exist = (root / "tests/test_s79_side_aware_risk_context.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-018":
        report_exists = (root / LTO018_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/regime_decay_outcome_join.jsonl").exists()
        helper_exists = (root / "src/research_infra/regime_decay_outcome_join.py").exists()
        backfill_exists = (root / "scripts/backfill_regime_decay_outcome_join.py").exists()
        tests_exist = (root / "tests/test_regime_decay_outcome_join.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-019":
        report_exists = (root / LTO019_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/decision_layer_diagnostics_join.jsonl").exists()
        helper_exists = (root / "src/research_infra/decision_layer_diagnostics_join.py").exists()
        backfill_exists = (root / "scripts/backfill_decision_layer_diagnostics_join.py").exists()
        tests_exist = (root / "tests/test_decision_layer_diagnostics_join.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-020":
        report_exists = (root / LTO020_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/mechanical_context_diagnostics_join.jsonl").exists()
        helper_exists = (root / "src/research_infra/mechanical_context_diagnostics_join.py").exists()
        backfill_exists = (root / "scripts/backfill_mechanical_context_diagnostics_join.py").exists()
        tests_exist = (root / "tests/test_mechanical_context_diagnostics_join.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-023":
        report_exists = (root / LTO023_REPORT).exists()
        status_log_exists = (root / "shadow_logs/ml_shadow_predictions.jsonl").exists()
        helper_exists = (root / "src/research_infra/k55_ml_shadow.py").exists()
        backfill_exists = (root / "scripts/backfill_k55_ml_shadow_predictions.py").exists()
        tests_exist = (root / "tests/test_k55_ml_shadow.py").exists()
        registry_exists = (root / "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, backfill_exists, tests_exist, registry_exists)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-027":
        report_exists = (root / LTO027_REPORT).exists()
        status_log_exists = (root / "shadow_logs/v2_structural_selector_readiness.jsonl").exists()
        helper_exists = (root / "src/research_infra/v2_structural_selector_readiness.py").exists()
        audit_exists = (root / "scripts/audit_v2_structural_selector_readiness.py").exists()
        tests_exist = (root / "tests/test_v2_structural_selector_readiness.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-028":
        report_exists = (root / LTO028_REPORT).exists()
        status_log_exists = (root / "shadow_logs/xauusd_same_market_extension_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/xauusd_same_market_extension.py").exists()
        audit_exists = (root / "scripts/audit_xauusd_same_market_extension.py").exists()
        tests_exist = (root / "tests/test_xauusd_same_market_extension.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-029":
        report_exists = (root / LTO029_REPORT).exists()
        registry_exists = (root / "research/program_control/ES_MES_STRATEGY_COHORT_REGISTRY_2026-05-05.md").exists()
        status_log_exists = (root / "shadow_logs/es_mes_preregistration_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/es_mes_preregistration.py").exists()
        audit_exists = (root / "scripts/audit_es_mes_preregistration.py").exists()
        tests_exist = (root / "tests/test_es_mes_preregistration.py").exists()
        return "DONE" if all((report_exists, registry_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-035":
        report_exists = (root / LTO035_REPORT).exists()
        registry_exists = (root / "research/program_control/LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.md").exists()
        status_log_exists = (root / "shadow_logs/shadow_observer_hardening_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/shadow_observer_hardening.py").exists()
        audit_exists = (root / "scripts/audit_shadow_observer_hardening.py").exists()
        tests_exist = (root / "tests/test_shadow_observer_hardening.py").exists()
        return "DONE" if all((report_exists, registry_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-025":
        report_exists = (root / LTO025_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/account_pnl_truth_reconciliation.jsonl").exists()
        helper_exists = (root / "src/research_infra/account_pnl_truth_reconciler.py").exists()
        backfill_exists = (root / "scripts/backfill_account_pnl_truth_reconciliation.py").exists()
        tests_exist = (root / "tests/test_account_pnl_truth_reconciler.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-026":
        report_exists = (root / LTO026_REPORT).exists()
        audit_log_exists = (root / "shadow_logs/trade_index_lifecycle_audit.jsonl").exists()
        inventory_index_exists = (root / "knowledge_base/index/trade_record_inventory_index_2026-05-05.json").exists()
        helper_exists = (root / "src/research_infra/trade_index_lifecycle_audit.py").exists()
        backfill_exists = (root / "scripts/backfill_trade_index_lifecycle_audit.py").exists()
        tests_exist = (root / "tests/test_trade_index_lifecycle_audit.py").exists()
        return "DONE" if all((report_exists, audit_log_exists, inventory_index_exists, helper_exists, backfill_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-010":
        report_exists = (root / LTO010_REPORT).exists()
        helper_exists = (root / "src/research_infra/databento_live_shadow.py").exists()
        collector_exists = (root / "scripts/databento_live_shadow_collector.py").exists()
        audit_exists = (root / "scripts/audit_databento_live_trigger_policy.py").exists()
        tests_exist = (root / "tests/test_databento_live_shadow.py").exists()
        return "DONE" if all((report_exists, helper_exists, collector_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-011":
        report_exists = (root / LTO011_REPORT).exists()
        status_log_exists = (root / "shadow_logs/nas100_orderflow_adverse_selection_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/nas100_orderflow_adverse_selection.py").exists()
        audit_exists = (root / "scripts/audit_nas100_orderflow_adverse_selection.py").exists()
        tests_exist = (root / "tests/test_nas100_orderflow_adverse_selection.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-012":
        report_exists = (root / LTO012_REPORT).exists()
        status_log_exists = (root / "shadow_logs/sierra_depth_enrichment_status.jsonl").exists()
        feature_log_exists = (root / "shadow_logs/sierra_depth_feature_snapshots.jsonl").exists()
        extractor_exists = (root / "scripts/enrich_sierra_live_candidate_depth_features.py").exists()
        audit_exists = (root / "scripts/audit_sierra_live_depth_confluence.py").exists()
        tests_exist = all(
            (
                (root / "tests/test_enrich_sierra_live_candidate_depth_features.py").exists(),
                (root / "tests/test_sierra_live_depth_confluence_audit.py").exists(),
            )
        )
        return "DONE" if all((report_exists, status_log_exists, feature_log_exists, extractor_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-013":
        report_exists = (root / LTO013_REPORT).exists()
        status_log_exists = (root / "shadow_logs/sierra_proxy_registry_status.jsonl").exists()
        registry_exists = (root / "src/research_infra/sierra_proxy_registry.py").exists()
        audit_exists = (root / "scripts/audit_sierra_proxy_registry.py").exists()
        tests_exist = all(
            (
                (root / "tests/test_sierra_proxy_registry.py").exists(),
                (root / "tests/test_sierra_proxy_registry_audit.py").exists(),
            )
        )
        return "DONE" if all((report_exists, status_log_exists, registry_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-014":
        report_exists = (root / LTO014_REPORT).exists()
        status_log_exists = (root / "shadow_logs/gbpjpy_proxy_gap_status.jsonl").exists()
        audit_exists = (root / "scripts/audit_gbpjpy_orderflow_proxy_gap.py").exists()
        tests_exist = (root / "tests/test_gbpjpy_orderflow_proxy_gap.py").exists()
        return "DONE" if all((report_exists, status_log_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-030":
        report_exists = (root / LTO030_REPORT).exists()
        status_log_exists = (root / "shadow_logs/sierra_6b_si_depth_policy_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/sierra_6b_si_depth_policy.py").exists()
        audit_exists = (root / "scripts/audit_sierra_6b_si_depth_policy.py").exists()
        tests_exist = (root / "tests/test_sierra_6b_si_depth_policy.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-033":
        report_exists = (root / LTO033_REPORT).exists()
        status_log_exists = (root / "shadow_logs/orderflow_primitives_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/orderflow_primitives.py").exists()
        audit_exists = (root / "scripts/audit_orderflow_primitives.py").exists()
        tests_exist = (root / "tests/test_orderflow_primitives.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-021":
        report_exists = (root / LTO021_REPORT).exists()
        status_log_exists = (root / "shadow_logs/exit_management_shadow_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/exit_management_no_event_audit.py").exists()
        audit_exists = (root / "scripts/backfill_exit_management_no_event_status.py").exists()
        tests_exist = (root / "tests/test_exit_management_no_event_audit.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-022":
        report_exists = (root / LTO022_REPORT).exists()
        status_log_exists = (root / "shadow_logs/session_volatility_sweep_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/session_volatility_sweep_status.py").exists()
        audit_exists = (root / "scripts/audit_session_volatility_sweep_status.py").exists()
        tests_exist = (root / "tests/test_session_volatility_sweep_status.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-036":
        report_exists = (root / LTO036_REPORT).exists()
        status_log_exists = (root / "shadow_logs/canary_restart_governance_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/canary_restart_governance.py").exists()
        audit_exists = (root / "scripts/audit_canary_restart_governance.py").exists()
        tests_exist = (root / "tests/test_canary_restart_governance.py").exists()
        watchdog_tests_exist = (root / "tests/test_watchdog_e2e_verify.py").exists()
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist, watchdog_tests_exist)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-037":
        report_exists = (root / LTO037_REPORT).exists()
        status_log_exists = (root / "shadow_logs/notification_queue_dead_zone_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/notification_queue_dead_zone_status.py").exists()
        audit_exists = (root / "scripts/audit_notification_queue_dead_zone.py").exists()
        tests_exist = (root / "tests/test_notification_queue_dead_zone_status.py").exists()
        watchdog_path = root / "scripts/watchdog.ps1"
        watchdog_hook_exists = watchdog_path.exists() and "audit_notification_queue_dead_zone.py" in watchdog_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist, watchdog_hook_exists)) else "READY_TO_IMPLEMENT"
    if item_id == "LTO-038":
        report_exists = (root / LTO038_REPORT).exists()
        status_log_exists = (root / "shadow_logs/storage_retention_status.jsonl").exists()
        helper_exists = (root / "src/research_infra/storage_retention_policy.py").exists()
        audit_exists = (root / "scripts/audit_storage_retention.py").exists()
        tests_exist = (root / "tests/test_storage_retention_policy.py").exists()
        checklist_path = root / "research/program_control/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.json"
        checklist_hook_exists = checklist_path.exists() and "audit_storage_retention.py" in checklist_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        return "DONE" if all((report_exists, status_log_exists, helper_exists, audit_exists, tests_exist, checklist_hook_exists)) else "READY_TO_IMPLEMENT"
    return STATUS_OVERRIDES.get(item_id, "READY_TO_IMPLEMENT")


def build_payload(
    plan_path: str | Path = DEFAULT_PLAN,
    coverage_json_path: str | Path = DEFAULT_COVERAGE_JSON,
    root: str | Path = ".",
) -> dict[str, Any]:
    root_path = Path(root)
    sections = parse_lto_sections(plan_path)
    follow_to_lto, lto_to_follow = parse_followup_mapping(plan_path)
    coverage = load_coverage(coverage_json_path)
    coverage_rows = {row["id"]: row for row in coverage.get("rows", [])}

    coverage_ids = sorted(coverage_rows)
    mapped_follow_ids = sorted(follow_to_lto)
    unmapped_live_follow_ids = [follow_id for follow_id in coverage_ids if follow_id not in follow_to_lto]
    missing_coverage_ids = [follow_id for follow_id in mapped_follow_ids if follow_id not in coverage_rows]

    items: list[dict[str, Any]] = []
    order_index = {item_id: index for index, item_id in enumerate(IMPLEMENTATION_ORDER, start=1)}
    for item_id in sorted(sections, key=lambda value: order_index.get(value, 999)):
        section = sections[item_id]
        follow_ids = sorted(lto_to_follow.get(item_id, []))
        row_statuses = sorted(
            {
                coverage_rows[follow_id].get("coverage_status", "MISSING_COVERAGE_ROW")
                for follow_id in follow_ids
                if follow_id in coverage_rows
            }
        )
        row_paths = sorted(
            {
                path
                for follow_id in follow_ids
                for path in coverage_rows.get(follow_id, {}).get("row_paths", [])
            }
        )
        source_texts = [
            coverage_rows.get(follow_id, {}).get("source", "")
            for follow_id in follow_ids
        ]
        prior_gap_ids = extract_prior_gap_ids(*source_texts, section.get("current_state", ""))
        status = dynamic_status(item_id, unmapped_live_follow_ids, root_path)
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Unsupported status for {item_id}: {status}")
        blocked_by = BLOCKER_NOTES.get(item_id, "")
        blocker_artifact_paths = [
            str(path)
            for path in BLOCKER_ARTIFACTS.get(item_id, [])
            if (root_path / path).exists()
        ]
        items.append(
            {
                "id": item_id,
                "title": section["title"],
                "status": status,
                "status_reason": STATUS_REASON[status],
                "blocked_by": blocked_by,
                "blocker_artifact_paths": blocker_artifact_paths,
                "implementation_order": order_index.get(item_id),
                "follow_ids": follow_ids,
                "coverage_statuses": row_statuses,
                "row_paths": row_paths,
                "prior_gap_ids": prior_gap_ids,
                "current_state": section.get("current_state", ""),
                "opportunity": section.get("opportunity", ""),
                "engineering_action": section.get("engineering_action", ""),
                "backfill": section.get("backfill", ""),
                "validation": section.get("validation", ""),
                "prerequisite": section.get("prerequisite", ""),
                "promotion_allowed": False,
                "promotion_verdict": PROMOTION_VERDICT,
            }
        )

    status_counts = Counter(item["status"] for item in items)
    lto_ids_in_plan = sorted(sections)
    mapped_lto_ids = sorted(lto_to_follow)
    payload = {
        "schema_version": "limitations_to_opportunities_queue_state_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_date": QUEUE_DATE,
        "promotion_verdict": PROMOTION_VERDICT,
        "source_plan": str(plan_path),
        "source_coverage_audit": str(coverage_json_path),
        "items": items,
        "summary": {
            "lto_item_count": len(items),
            "live_follow_row_count": len(coverage_ids),
            "mapped_live_follow_row_count": len(mapped_follow_ids),
            "unmapped_live_follow_ids": unmapped_live_follow_ids,
            "missing_coverage_ids_from_plan": missing_coverage_ids,
            "lto_ids_without_follow_ids": [item_id for item_id in lto_ids_in_plan if item_id not in lto_to_follow],
            "mapped_lto_ids_without_plan_section": [item_id for item_id in mapped_lto_ids if item_id not in sections],
            "status_counts": dict(sorted(status_counts.items())),
            "promotion_allowed_items": [item["id"] for item in items if item["promotion_allowed"]],
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Limitations To Opportunities Queue State - 2026-05-05",
        "",
        f"**Schema:** `{payload['schema_version']}`",
        f"**Generated:** `{payload['created_at_utc']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        f"**Source plan:** `{payload['source_plan']}`",
        f"**Source coverage audit:** `{payload['source_coverage_audit']}`",
        "",
        "## Summary",
        "",
        f"- LTO items: `{summary['lto_item_count']}`",
        f"- LIVE-FOLLOW rows mapped: `{summary['mapped_live_follow_row_count']}` / `{summary['live_follow_row_count']}`",
        f"- Unmapped LIVE-FOLLOW rows: `{', '.join(summary['unmapped_live_follow_ids']) or 'none'}`",
        f"- Missing coverage IDs from plan: `{', '.join(summary['missing_coverage_ids_from_plan']) or 'none'}`",
        f"- Promotion-allowed items: `{', '.join(summary['promotion_allowed_items']) or 'none'}`",
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in summary["status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Queue",
            "",
            "| LTO | Status | Follow IDs | Coverage statuses | Blocker / note |",
            "|---|---|---|---|---|",
        ]
    )
    for item in payload["items"]:
        follow_ids = ", ".join(f"`{value}`" for value in item["follow_ids"]) or "-"
        coverage_statuses = ", ".join(f"`{value}`" for value in item["coverage_statuses"]) or "-"
        note = item["blocked_by"] or item["status_reason"]
        if item.get("blocker_artifact_paths"):
            note = f"{note} Artifacts: {', '.join(f'`{path}`' for path in item['blocker_artifact_paths'])}."
        lines.append(
            f"| `{item['id']}` {item['title']} | `{item['status']}` | {follow_ids} | {coverage_statuses} | {note} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This queue is research/tooling only.",
            "- It does not validate, promote, or modify live trading behavior.",
            "- Every item remains `NO_PROMOTION_VERDICT` until a separate promotion dossier exists.",
            "- Rows marked source-, approval-, or event-blocked must not be fabricated from later data.",
        ]
    )
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
    parser.add_argument("--plan", default=str(DEFAULT_PLAN))
    parser.add_argument("--coverage-json", default=str(DEFAULT_COVERAGE_JSON))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    args = parser.parse_args()

    payload = build_payload(args.plan, args.coverage_json)
    write_outputs(payload, args.output_json, args.output_md)
    unmapped = payload["summary"]["unmapped_live_follow_ids"]
    print(
        "wrote "
        f"{args.output_json} and {args.output_md}; "
        f"lto_items={payload['summary']['lto_item_count']} "
        f"unmapped_live_follow={len(unmapped)}"
    )
    return 1 if unmapped else 0


if __name__ == "__main__":
    raise SystemExit(main())
