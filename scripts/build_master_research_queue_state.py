#!/usr/bin/env python3
"""Build the GTOS master research queue state.

Research/tooling only. This script parses the ML master backlog mechanically,
then applies explicit artifact-backed reconciliation overlays from the weekend
research artifacts. It does not promote any trading logic and it keeps every
candidate at NO_PROMOTION_VERDICT unless a separate promotion dossier exists.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BACKLOG = "research/ml_program/MASTER_BACKLOG.md"
DEFAULT_RESEARCH_CURRENT_STATE = ".context/00_core/research_current_state.md"
DEFAULT_DEFERRED_LEDGER = (
    "research/phase_3_external_feed_validation/"
    "PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md"
)
DEFAULT_OUTPUT_JSON = "research/program_control/MASTER_RESEARCH_QUEUE_STATE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/program_control/MASTER_RESEARCH_QUEUE_STATE_2026-05-03.md"

QUEUE_DATE = "2026-05-03"

DONE_BACKLOG_STATUSES = {
    "DONE",
    "DONE_NULL",
    "COMPLETED",
    "DSR_VALIDATED",
    "ANSWERED_BY_NA8",
    "SHIPPED + EXT_DESIGN",
    "SHIPPED + EXT_PENDING",
}
FAILED_BACKLOG_STATUSES = {"FAILED", "DSR_FAILED", "DONE-FAIL"}
DEFERRED_BACKLOG_STATUSES = {"DEFERRED"}
FILED_BACKLOG_STATUSES = {"FILED", "DESIGN_DONE", "DESIGN_DONE_PENDING_INTEGRATION", "PARTIAL"}

LANE_NAMES = {
    "lane_0_control_tower": "Lane 0 - Backlog Reconciliation / Control Tower",
    "lane_1_methodology": "Lane 1 - Methodology Infrastructure",
    "lane_2_path_scaling": "Lane 2 - Path Scaling: V2 / V2b / V3 / V4",
    "lane_3_execution_telemetry": "Lane 3 - Execution / Telemetry / Label Truth",
    "lane_4_orderflow_proxy_sierra": "Lane 4 - Orderflow / Proxy / Sierra",
    "lane_5_data_ml_quality": "Lane 5 - Data / Backfill / ML Cohort Quality",
    "lane_6_asset_risk_edge": "Lane 6 - Asset / Risk / Vol / Edge Mechanism",
    "lane_7_recurring_open_questions": "Lane 7 - Recurring / Literature / Open Questions",
}

TIER_BASE_PRIORITY = {
    "T1": 10,
    "T2": 20,
    "T3": 30,
    "T4": 40,
    "DONE": 90,
}


def split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip().replace(r"\|", "|") for cell in stripped.strip("|").split("|")]


def parse_backlog(path: str | Path = DEFAULT_BACKLOG) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, Any]] = []
    current_section = "unknown"
    section_re = re.compile(r"^## Section ([A-Z][^-\n]*)")
    for line in text.splitlines():
        section_match = section_re.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            continue

        cells = split_markdown_row(line)
        if len(cells) < 4:
            continue
        if cells[0] in {"ID", "---"} or set(cells[0]) == {"-"}:
            continue
        if not re.match(r"^[A-Z]+-\d+$", cells[0]):
            continue
        rows.append(
            {
                "id": cells[0],
                "tier": cells[1],
                "backlog_status": cells[2],
                "item": cells[3],
                "section": current_section,
                "source": str(path),
            }
        )
    return rows


def normalize_status(backlog_status: str) -> str:
    status = backlog_status.strip()
    if status in DONE_BACKLOG_STATUSES:
        return "DONE"
    if status in FAILED_BACKLOG_STATUSES:
        return "REJECTED_FAILED"
    if status in DEFERRED_BACKLOG_STATUSES:
        return "DEFERRED_WITH_TRIGGER"
    if status in FILED_BACKLOG_STATUSES:
        return "FILED_FOR_APPROVAL"
    if status == "BLOCKED":
        return "BLOCKED_WITH_REASON"
    return "STILL_PENDING_RANKED"


def lane_for_item(item_id: str, text: str = "") -> str:
    if item_id in {"D-6", "D-11", "O-1", "O-2", "O-8", "U-11"}:
        return "lane_0_control_tower"
    prefix = item_id.split("-")[0]
    if prefix == "M" or item_id == "B-6":
        return "lane_1_methodology"
    if item_id in {"C-7", "C-9"}:
        return "lane_2_path_scaling"
    if prefix == "O" or item_id in {"L-6", "L-7"}:
        return "lane_3_execution_telemetry"
    if "orderflow" in text.lower() or "proxy" in text.lower() or "sierra" in text.lower():
        return "lane_4_orderflow_proxy_sierra"
    if prefix in {"D", "K", "P", "S", "Q"}:
        return "lane_5_data_ml_quality"
    if prefix in {"A", "R", "V", "E", "X", "C", "B"}:
        return "lane_6_asset_risk_edge"
    return "lane_7_recurring_open_questions"


def base_priority(lane: str, tier: str, status: str) -> int:
    lane_order = list(LANE_NAMES).index(lane) * 100
    tier_priority = TIER_BASE_PRIORITY.get(tier, 25)
    status_penalty = 500 if status == "DONE" else 400 if status in {"REJECTED_FAILED", "DEFERRED_WITH_TRIGGER"} else 0
    return lane_order + tier_priority + status_penalty


def default_item(row: dict[str, Any]) -> dict[str, Any]:
    status = normalize_status(row["backlog_status"])
    lane = lane_for_item(row["id"], row["item"])
    return {
        "id": row["id"],
        "lane": lane,
        "lane_name": LANE_NAMES[lane],
        "status": status,
        "backlog_status": row["backlog_status"],
        "blocked_by": "",
        "artifact_required": "",
        "tests_required": "",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable",
        "priority": base_priority(lane, row["tier"], status),
        "dependencies": [],
        "new_followups_opened": [],
        "tier": row["tier"],
        "section": row["section"],
        "item": row["item"],
        "latest_artifact_path": "",
        "reconciliation_note": "",
        "source": row["source"],
    }


LANE6_PRIORITY620_ARTIFACT = "research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md"
LANE6_PRIORITY620_TESTS = (
    "python -m pytest tests/test_lane6_priority620_triage.py "
    "tests/test_master_research_queue_state.py -q"
)
LANE6_TAIL_ARTIFACT = "research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md"
LANE6_TAIL_TESTS = (
    "python -m pytest tests/test_lane6_tail_triage.py "
    "tests/test_master_research_queue_state.py -q"
)
LANE7_ARTIFACT = "research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md"
LANE7_TESTS = (
    "python -m pytest tests/test_lane7_open_questions_triage.py "
    "tests/test_master_research_queue_state.py -q"
)


def lane6_priority620_overlay(
    status: str,
    *,
    blocked_by: str = "",
    artifact_required: str = "Lane 6 priority-620 triage artifact",
    candidate_strength_vs_j46_j49: str = "not_applicable",
    reconciliation_note: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "blocked_by": blocked_by,
        "artifact_required": artifact_required,
        "latest_artifact_path": LANE6_PRIORITY620_ARTIFACT,
        "tests_required": LANE6_PRIORITY620_TESTS,
        "candidate_strength_vs_j46_j49": candidate_strength_vs_j46_j49,
        "reconciliation_note": reconciliation_note,
    }


def lane6_tail_overlay(
    status: str,
    *,
    blocked_by: str = "",
    artifact_required: str = "Lane 6 tail triage artifact",
    candidate_strength_vs_j46_j49: str = "not_applicable",
    reconciliation_note: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "blocked_by": blocked_by,
        "artifact_required": artifact_required,
        "latest_artifact_path": LANE6_TAIL_ARTIFACT,
        "tests_required": LANE6_TAIL_TESTS,
        "candidate_strength_vs_j46_j49": candidate_strength_vs_j46_j49,
        "reconciliation_note": reconciliation_note,
    }


def lane7_overlay(
    status: str,
    *,
    blocked_by: str = "",
    artifact_required: str = "Lane 7 recurring/open-question triage artifact",
    candidate_strength_vs_j46_j49: str = "not_applicable",
    reconciliation_note: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "blocked_by": blocked_by,
        "artifact_required": artifact_required,
        "latest_artifact_path": LANE7_ARTIFACT,
        "tests_required": LANE7_TESTS,
        "candidate_strength_vs_j46_j49": candidate_strength_vs_j46_j49,
        "reconciliation_note": reconciliation_note,
    }


ARTIFACT_OVERLAYS: dict[str, dict[str, Any]] = {
    "D-6": {
        "status": "DONE",
        "latest_artifact_path": "research/operations/weekend_backlog_ops_triage_2026-05-03.md",
        "reconciliation_note": "Alias boundary documented: NAS100 canonical, NDX100 redacted_account broker alias, US100.cash historical demo context.",
        "tests_required": "documentation-only; read-only file/code grep evidence",
        "new_followups_opened": ["ALIAS-HYGIENE-CENTRALIZE-EXTRACTION-MAPPING"],
    },
    "D-11": {
        "status": "DONE",
        "latest_artifact_path": "research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md",
        "reconciliation_note": "Bias audit completed; old backfill usable with downsampling/source flags, not live-equivalent.",
        "tests_required": "python -m pytest tests/test_d11_2022_2023_backfill_bias.py -q",
        "new_followups_opened": ["D11-REGENERATE-GBPJPY-US30CASH-OLD-LABELS", "D11-SOURCE-PERIOD-FEATURE-FLAGS"],
    },
    "U-11": {
        "status": "DONE",
        "latest_artifact_path": "research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md",
        "reconciliation_note": "Open research question answered by D-11 audit; follow-ups are data generation/source-flag tasks.",
        "tests_required": "python -m pytest tests/test_d11_2022_2023_backfill_bias.py -q",
        "new_followups_opened": ["D11-REGENERATE-GBPJPY-US30CASH-OLD-LABELS", "D11-SOURCE-PERIOD-FEATURE-FLAGS"],
    },
    "O-1": {
        "status": "DONE",
        "latest_artifact_path": "research/operations/weekend_backlog_ops_triage_2026-05-03.md",
        "reconciliation_note": "_trade_index.json staleness refreshed; implementation/verifier split into generated Lane 3 follow-up.",
        "tests_required": "documentation-only; read-only counts",
        "new_followups_opened": ["O1-INDEX-REBUILD-OR-STALE-VERIFIER"],
    },
    "O-2": {
        "status": "DONE",
        "latest_artifact_path": "research/operations/weekend_backlog_ops_triage_2026-05-03.md",
        "reconciliation_note": "Alias triage filed and no live-code change needed.",
        "tests_required": "documentation-only; read-only file/code grep evidence",
    },
    "O-8": {
        "status": "DONE",
        "latest_artifact_path": "research/operations/weekend_backlog_ops_triage_2026-05-03.md",
        "reconciliation_note": "Gap audit completed; lifecycle-aware completeness verifier split into generated Lane 3 follow-up.",
        "tests_required": "documentation-only; read-only counts",
        "new_followups_opened": ["O8-LIFECYCLE-COMPLETENESS-VERIFIER"],
    },
    "O-3": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 310,
        "blocked_by": "Operator must enable the Windows scheduled-task 'Wake the computer to run this task' setting and verify the next active kill-zone wake cycle.",
        "artifact_required": "operator confirmation plus next active KZ wake verification",
        "latest_artifact_path": "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md",
        "tests_required": "operator/system verification; no repo-only test can flip the Task Scheduler setting",
        "candidate_strength_vs_j46_j49": "not_applicable_operator_action",
        "reconciliation_note": "Repo-side triage confirms O-3 is operator-only, not an unblocked research/coding task.",
    },
    "O-5": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 310,
        "blocked_by": "Disk cleanup and pagefile raise require OS/admin action outside repo research tooling.",
        "artifact_required": "operator/admin completion plus rerun of ops checks",
        "latest_artifact_path": "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md",
        "tests_required": "operator/system verification; no repo-only test can perform disk cleanup/pagefile changes",
        "candidate_strength_vs_j46_j49": "not_applicable_operator_action",
        "reconciliation_note": "Repo-side triage confirms O-5 is operator/admin maintenance, not an unblocked research/coding task.",
    },
    "B-6": {
        "status": "DONE",
        "latest_artifact_path": "research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md",
        "reconciliation_note": "Methodology-discipline bundle closed for current/future research claims: weighted SE, effective-N/trial counter, and PBO hardened-claim gate are now in research_infra.",
        "tests_required": "python -m pytest tests/test_methodology_gate.py -q",
    },
    "M-7": {
        "status": "DONE",
        "priority": 101,
        "artifact_required": "training-overlap-weighted SE replacement or implementation ticket scoped to research pipelines",
        "latest_artifact_path": "research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md",
        "tests_required": "targeted methodology tests",
        "reconciliation_note": "Implemented in src/research_infra/methodology_gate.py and audited across current primary methodology artifacts; historical Stouffer fields are archived and blocked from promotion use.",
    },
    "M-12": {
        "status": "DONE",
        "priority": 102,
        "artifact_required": "effective-N/trial counter for research lift claims",
        "latest_artifact_path": "research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md",
        "tests_required": "targeted methodology tests",
        "reconciliation_note": "Effective-N and cumulative trial-budget helpers implemented in research_infra methodology gate.",
    },
    "M-13": {
        "status": "DONE",
        "priority": 103,
        "artifact_required": "PBO guard baked into primary evaluation pipelines or approval-safe implementation ticket",
        "latest_artifact_path": "research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md",
        "tests_required": "targeted methodology tests",
        "reconciliation_note": "PBO hardened-claim gate implemented and current primary artifacts audited; promotion p-values allowed count remains zero.",
    },
    "M-16": {
        "status": "DONE",
        "priority": 110,
        "artifact_required": "bias-variance bookkeeping artifact for Q1.3 fixed-HP CPCV path diffs",
        "latest_artifact_path": "research/ml_program/audit/Q13_CPCV_BIAS_VARIANCE_BOOKKEEPING_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_q13_cpcv_bias_variance.py -q",
        "reconciliation_note": "Q1.3 +0.030896 lift classified variance-dominated: 13.1% signal share vs 86.9% path-variance share.",
    },
    "M-10": {
        "status": "DONE",
        "priority": 120,
        "artifact_required": "Hansen SPA-style test over current K54-class lift series",
        "latest_artifact_path": "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_methodology_alternatives.py -q",
        "reconciliation_note": "SPA-style stationary bootstrap applied to K54 v2/v3/v4 lift series with explicit CPCV-path-dependence caveat; diagnostic only, no promotion p-values.",
    },
    "M-11": {
        "status": "DONE",
        "priority": 121,
        "artifact_required": "Diebold-Mariano per-fold paired AUC diagnostic",
        "latest_artifact_path": "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_methodology_alternatives.py -q",
        "reconciliation_note": "Fold-aggregated paired AUC DM-style HAC diagnostics reconstructed for K54 v2/v3 where per-row CPCV predictions exist.",
    },
    "M-14": {
        "status": "DONE",
        "priority": 122,
        "artifact_required": "Christoffersen interval-coverage artifact for K54 v3 confidence-band feature",
        "latest_artifact_path": "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_methodology_alternatives.py -q",
        "reconciliation_note": "K54 v3 conformal calibration has Christoffersen proxy coverage p=0.00158; holdout remains deferred, no validation claim.",
    },
    "M-15": {
        "status": "DONE",
        "priority": 123,
        "artifact_required": "Bayesian backtesting alternative methodology track",
        "latest_artifact_path": "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_methodology_alternatives.py -q",
        "reconciliation_note": "Bayesian normal-normal posterior track applied to K54-class lifts under CPCV-weighted SE and skeptical prior; parallel evidence only.",
    },
    "M-5": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 124,
        "blocked_by": "Exact 7-symbol per-instrument resolution needs full 2022-2023 v2/v3 feature catalog and old mechanical labels for missing symbols; current evidence is v1-schema/effective-group only.",
        "artifact_required": "rerun after D11 missing labels and v2/v3 feature backfill exist",
        "latest_artifact_path": "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_methodology_alternatives.py -q",
        "reconciliation_note": "Current empirical read keeps AFML/CPCV-honest as promotion doctrine; exact per-symbol Inoue-Kilian/Diebold resolution is data-blocked.",
    },
    "M-6": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 125,
        "blocked_by": "No observations x 47 instrument-side-regime cell performance-differential matrix was found in current artifacts.",
        "artifact_required": "47-cell cell_id x observation/fold matrix with candidate and benchmark metrics",
        "latest_artifact_path": "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_methodology_alternatives.py -q",
        "reconciliation_note": "Romano-Wolf StepM harness exists and is smoke-tested, but the requested 47-cell empirical panel is absent.",
    },
    "C-7": {
        "status": "DONE",
        "priority": 210,
        "artifact_required": "Path-9 composition and replication diagnostic artifact",
        "latest_artifact_path": "research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane2_c7_c9_path_scaling_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_ml_diagnostic",
        "reconciliation_note": "Path-9 was Feb-heavy and cross-cohort, not single-symbol; replication scan shows temporal fragility rather than stable all-window lift.",
    },
    "C-9": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 210,
        "blocked_by": "Full C-9 needs deterministic L2 reconstruction, resolved V2b post-cutoff OB-boundary/J46 pairs, pending lifecycle + original POI/pre-fill fields for reentry, and measured cost/slippage.",
        "artifact_required": "L2 reconstruction plus resolved V2b rows plus lifecycle/pre-fill join before full ablation/reentry validation",
        "latest_artifact_path": "research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane2_c7_c9_path_scaling_triage.py -q",
        "candidate_strength_vs_j46_j49": "partial_chain_positive_discovery_only; V3 FVG-only rescue delta +0.270259R vs J46 on same-dataset replay, no promotion",
        "reconciliation_note": "Protocol/V0/V2/V2b/V3 subcomponents exist, but the exact L2 on/off and close-and-reenter comparison remains blocked rather than failed.",
    },
    "A-2": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 420,
        "blocked_by": "Local external-feed inventory has VIXCLS/GVZCLS but no VIX1D or VIX9D cache/source; the spread cannot be constructed without a confirmed legal/free source.",
        "artifact_required": "confirmed legal/free VIX1D and VIX9D source plus no-leak as-of fetch/cache",
        "latest_artifact_path": "research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane4_options_proxy_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        "reconciliation_note": "Lane 4 triage found VIX1D/VIX9D absent from local external-feed inventory; A-2 is data/source blocked, not executable.",
    },
    "A-3": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 420,
        "blocked_by": "No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists in data/external.",
        "artifact_required": "no-leak VRP construction spec with as-of implied-vol/variance source and realized-vol estimator",
        "latest_artifact_path": "research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane4_options_proxy_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        "reconciliation_note": "Lane 4 triage keeps A-3 blocked until VRP source, estimator, and publication-time convention are registered.",
    },
    "D-3": {
        "status": "DONE",
        "priority": 420,
        "blocked_by": "",
        "artifact_required": "FlashAlpha Basic proxy path integrated; official/historical CBOE GEX remains separate source work",
        "latest_artifact_path": "research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane4_options_proxy_triage.py tests/test_external_feeds.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_feed_integration_only",
        "reconciliation_note": "FlashAlpha Basic single-expiry GEX proxy integration is complete and locally cached for QQQ/DIA/SPY/GLD/SLV; no alpha or official-CBOE validation claim.",
    },
    "K-5": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "Raw W-unit pooling failed on the MT5 retail/CFD substrate; literal mechanism needs LOB/TAQ-style depth and trade volume.",
        "artifact_required": "approved LOB/trade-volume substrate or new preregistered pooling transform",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_substrate_failed",
        "reconciliation_note": "K54 v3 W-unit ablation shows ON AUC 0.510 vs OFF AUC 0.564; current substrate closes K-5.",
    },
    "K-6": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "Pooled K54 v3/v4 training ran and failed global decision gates; same-cohort iteration is closed.",
        "artifact_required": "n>=5000 cohort expansion with source-period flags and missing old labels resolved",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_global_k54_failed",
        "reconciliation_note": "K54 v3 DSR-p 0.321 and K54 v4 all-architecture fail close pooled multi-instrument K54 as an unblocked lane item.",
    },
    "K-7": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation.",
        "artifact_required": "n>=5000 or feature-specific preregistered cohort where stop clusters are directly measured",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_below_noise",
        "reconciliation_note": "Osler stop-cluster proxy was marginal/not top-50; K-7 does not remain unblocked on the current cohort.",
    },
    "K-8": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation.",
        "artifact_required": "larger cohort or standalone OB-age preregistration that clears methodology gate",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_below_noise",
        "reconciliation_note": "Power-law OB-age weighting is closed for the current cohort as part of the below-noise K-7..K-10 feature block.",
    },
    "K-9": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "K-9 was below noise in the K54 v3 global model and the global K54 family failed per-cohort floors.",
        "artifact_required": "larger cohort and per-cohort interaction preregistration",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_below_noise",
        "reconciliation_note": "Regime/round/side interaction does not remain an unblocked architecture task on the current cohort.",
    },
    "K-10": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "K-10 appeared marginally in some top-100 screens but did not produce decision-grade lift.",
        "artifact_required": "n>=5000 or standalone asset-specialist feature test",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_below_noise",
        "reconciliation_note": "Above-up/below-down round-aligned feature is closed for the current K54 cohort.",
    },
    "K-11": {
        "status": "DONE",
        "priority": 520,
        "blocked_by": "",
        "artifact_required": "research component complete; no live promotion implied",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_tooling_done",
        "reconciliation_note": "Per-fold top-100 screening ran in K54 v3/v4; empirical stability failed, but the component is not pending.",
    },
    "K-12": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 520,
        "blocked_by": "Meta-labeling ran, but n=528 with about 250 primary-positive rows was statistically weak and showed no measurable lift.",
        "artifact_required": "n>5000 or new label-rich K55 shadow cohort",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_sample_size",
        "reconciliation_note": "Component 3A meta-labeling head is deferred on sample size rather than unblocked.",
    },
    "K-13": {
        "status": "DONE",
        "priority": 520,
        "blocked_by": "",
        "artifact_required": "research label component complete",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_tooling_done",
        "reconciliation_note": "Triple-barrier labels fed the K54 v3 meta-label head; no K-13 tooling blocker remains.",
    },
    "K-14": {
        "status": "DONE",
        "priority": 520,
        "blocked_by": "",
        "artifact_required": "true holdout remains separate validation gate, not an implementation blocker",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_calibration_done",
        "reconciliation_note": "Adaptive conformal calibration CPCV proxy exists; coverage was 0.881 vs 0.900 target with Christoffersen p 0.00158.",
    },
    "K-15": {
        "status": "DONE",
        "priority": 520,
        "blocked_by": "",
        "artifact_required": "stability gate complete; current feature set failed the gate",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_stability_gate_done",
        "reconciliation_note": "TreeSHAP-style stability gate is reported; current K54 features have only 2 stable features and mean Jaccard 0.169.",
    },
    "K-18": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "K54 v3 master failed DSR and stability gates; K54 v4 fallback architectures also failed. No same-cohort K54 architecture iteration remains unblocked.",
        "artifact_required": "n>=5000 or alternate broker/provider pre-2024 GBPJPY+US30 coverage plus v2/v3 feature backfill",
        "latest_artifact_path": "research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_k54_architecture_triage.py -q",
        "candidate_strength_vs_j46_j49": "NAS_US30 specialist remains K55-shadow discovery only; not promotion comparable to J46-J49.",
        "reconciliation_note": "K54 v3/v4 global architecture work is closed for the current cohort; top-3%/NAS_US30 findings remain shadow/discovery paths only.",
    },
    "P-1": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 520,
        "blocked_by": "Portfolio-wide vol-conditioning failed H-PM01; live insertion between 3A and execution would change risk/trading behavior and needs CEO approval even for shadow.",
        "artifact_required": "CEO approval for NAS100-only shadow A/B or fresh portfolio-wide preregistration that clears gates",
        "latest_artifact_path": "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_architecture_system_flow_triage.py -q",
        "candidate_strength_vs_j46_j49": "NAS100-only subcandidate delta_R +0.0907 DSR-p 0.0152; portfolio-wide failed, not promotion comparable.",
        "reconciliation_note": "Component 3C portfolio-wide overlay is deferred; only a NAS100-only shadow/approval path remains.",
    },
    "P-2": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 520,
        "blocked_by": "Meta-labeling ran in K54 v3 but was statistically weak at the current cohort size.",
        "artifact_required": "n>5000 or new label-rich K55 shadow cohort plus CEO approval for live system-flow wiring",
        "latest_artifact_path": "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_architecture_system_flow_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_sample_size",
        "reconciliation_note": "Component 3D module inherits K-12 sample-size deferral.",
    },
    "P-3": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 520,
        "blocked_by": "K54 global candidates failed; conformal has only a CPCV proxy and no live/holdout system-flow candidate to calibrate.",
        "artifact_required": "approved K55/K54 shadow candidate plus preregistered holdout/calibration window",
        "latest_artifact_path": "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_architecture_system_flow_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_calibration_deferred",
        "reconciliation_note": "Adaptive conformal module is deferred as system-flow work even though the CPCV proxy exists.",
    },
    "P-5": {
        "status": "REJECTED_FAILED",
        "priority": 520,
        "blocked_by": "K-5 W-unit pooling failed and K-6 pooled K54 v3/v4 training failed global gates.",
        "artifact_required": "usable LOB/trade-volume substrate or n>=5000 source-flagged cohort",
        "latest_artifact_path": "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_architecture_system_flow_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_inherits_k5_k6_failure",
        "reconciliation_note": "Pooled multi-instrument training pipeline is closed for the current substrate/cohort.",
    },
    "P-6": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 520,
        "blocked_by": "K54 v4 T7-NAS routing add was negative and all K54 v4 architectures failed; any inference routing layer is shadow-only until a specialist survives forward evidence.",
        "artifact_required": "K55-shadow specialist evidence clearing sample, stability, and approval gates",
        "latest_artifact_path": "research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_architecture_system_flow_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_k55_shadow_specialist_only",
        "reconciliation_note": "Per-instrument-group inference routing remains deferred after K54 v4 routing ablation failed.",
    },
    "K-16": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "No same-cohort K54 architecture iteration remains unblocked after K54 v3/v4 primary failure; focal loss would be another current-cohort loss-function variant.",
        "artifact_required": "n>=5000 regime-balanced labels or new label-rich K55 shadow cohort plus preregistered focal-loss comparison",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_same_cohort_k54_closed",
        "reconciliation_note": "Remaining Lane 5 architecture triage defers K-16 until a larger/source-balanced cohort or shadow cohort exists.",
    },
    "K-17": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "Pooled K54 v3/v4 training failed global gates, and data-poor instruments still need source-period flags and missing old labels resolved before new pooling claims are meaningful.",
        "artifact_required": "source-period flags, missing old labels resolved, and n>=5000 or source-balanced expanded cohort",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_cohort_quality",
        "reconciliation_note": "Remaining Lane 5 architecture triage defers hierarchical pooling until cohort/data-quality blockers clear.",
    },
    "P-7": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "Heartbeat/drawdown thresholds are safety/risk behavior, current tick history is too short for Hawkes calibration, and live threshold changes require CEO approval.",
        "artifact_required": ">=30 trading days all-symbol ticks or approved depth/feed data plus research-only simulation before approval path",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_safety_threshold_research",
        "reconciliation_note": "Remaining Lane 5 architecture triage defers Hawkes threshold work until data and approval triggers exist.",
    },
    "P-8": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "The literature-prior is documented, but no local HDP-HMM/Kirby-null research harness has passed; replacing the regime classifier would touch live/shadow behavior.",
        "artifact_required": "standalone HDP-HMM research harness with Kirby fat-tailed-mixture null-test and OOS realized-R comparison",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_literature_prior_no_empirical_gate",
        "reconciliation_note": "Remaining Lane 5 architecture triage defers sticky HDP-HMM until the Kirby null-test and OOS harness exist.",
    },
    "P-9": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "This depends on D-1 tick-count-time substrate maturity and would alter Component 1/tick-daemon runtime behavior; current all-symbol tick history is below the 30-day trigger.",
        "artifact_required": ">=30 trading days all-symbol ticks or approved feed plus research-only trade-count resampling validation",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_depends_on_d1_tick_substrate",
        "reconciliation_note": "Remaining Lane 5 architecture triage defers trade-count-time triggers until D-1 substrate maturity and approval.",
    },
    "P-10": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "Feature family has a literature prior, but same-cohort K54 feature iteration is closed after v3/v4 failure; old-label/source-period blockers still constrain new pooled training.",
        "artifact_required": "preregistered feature-family ablation after source flags/missing old labels are fixed and n>=5000 or new label-rich shadow cohort exists",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_literature_feature_prior_not_empirical",
        "reconciliation_note": "Remaining Lane 5 architecture triage keeps signature/fractional/HAR-RV features as a future preregistered feature refresh, not current K54 iteration.",
    },
    "S-1": {
        "status": "FILED_FOR_APPROVAL",
        "priority": 530,
        "blocked_by": "Design ticket exists, but target assumptions are stale after K54 v4 failed and implementation would touch orchestrator/config live paths.",
        "artifact_required": "refresh target model to current K55-shadow evidence and obtain explicit approval before scaffold/logger/orchestrator hook implementation",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "filed_design_only_no_promotion",
        "reconciliation_note": "K55 shadow design is filed, but not an unblocked coding task in this research loop.",
    },
    "S-2": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "K54 v4 T7-NAS routing add was negative and P-6 is already deferred; routing needs forward K55 specialist evidence first.",
        "artifact_required": "K55-shadow specialist evidence clearing sample, stability, and approval gates",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_inherits_p6_routing_failure",
        "reconciliation_note": "S-2 inherits P-6 routing deferral after K54 v4 routing ablation failed.",
    },
    "S-3": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "No K55 shadow logger/output exists yet; 30-day evaluation requires implementation plus enough forward shadow events.",
        "artifact_required": "S-1 implementation/smoke test plus >=30 days or n>=50 K55-shadow events",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_no_shadow_rows",
        "reconciliation_note": "K55 30-day evaluation is deferred until shadow rows exist.",
    },
    "S-4": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 530,
        "blocked_by": "No paired live AI+ML shadow dataset exists; current K54 evidence is discovery/refinement only.",
        "artifact_required": "paired AI decision, K55 decision, and realized-R rows from S-3 at preregistered sample floors",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_no_paired_shadow_dataset",
        "reconciliation_note": "Hybrid ML+AI measurement is deferred until paired shadow data exists.",
    },
    "S-5": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 540,
        "blocked_by": "Production flip requires successful S-3/S-4 shadow evaluation, promotion dossier, and explicit CEO approval; no such evidence exists.",
        "artifact_required": "successful K55 shadow gate, separate promotion dossier, and explicit CEO approval",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_arch_ml_quality_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_requires_future_promotion_dossier",
        "reconciliation_note": "K55 production flip remains deferred and cannot be inferred from current discovery artifacts.",
    },
    "V-1": {
        "status": "DONE",
        "priority": 610,
        "blocked_by": "",
        "artifact_required": "feature/tooling complete; Component 3C integration remains separate P-1/V-9 work",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_feature_done; portfolio-wide H-PM01 failed",
        "reconciliation_note": "Lane 6 triage closes V-1 because realized-vol-rank tooling exists in H-PM01/H-PM03/NA8; sizing integration remains deferred elsewhere.",
    },
    "V-2": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 610,
        "blocked_by": "No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists; VIXCLS/GVZCLS alone do not define VRP.",
        "artifact_required": "no-leak VRP construction spec with as-of implied-vol/variance source and realized-vol estimator",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        "reconciliation_note": "Lane 6 triage keeps VRP blocked on source/construction, consistent with A-3.",
    },
    "V-3": {
        "status": "DONE",
        "priority": 610,
        "blocked_by": "",
        "artifact_required": "feature/tooling complete; live Component 3C overlay remains separate",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_feature_done",
        "reconciliation_note": "K54 regime feature family already includes run-length, flip-window, and score-dynamics persistence features.",
    },
    "A-8": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 610,
        "blocked_by": "Local feeds have XAUUSD nominal bars plus FRED real-rate/inflation-expectation proxies, but no CPI/PCE deflator or pre-registered real-gold-price percentile construction.",
        "artifact_required": "legal CPI/PCE deflator source with publication-time metadata and registered real-gold-price percentile lookback",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        "reconciliation_note": "Lane 6 triage blocks A-8 until the real-gold deflator/source and no-leak construction are registered.",
    },
    "C-2": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 610,
        "blocked_by": "GTOS does not observe counterparty stop placements, broker client positioning, or IG/OANDA-style client sentiment locally; production trade records contain our proposed levels only.",
        "artifact_required": "legal counterparty/retail-positioning proxy or order-book stop-density source",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_unobserved_counterparty_data",
        "reconciliation_note": "Disposition-effect feature work is blocked on unobserved counterparty stop-placement data.",
    },
    "E-1": {
        "status": "REJECTED_FAILED",
        "priority": 610,
        "blocked_by": "The K54 v3 Osler round-level stop-cluster proxy was implemented as K-7 and contributed only below-noise lift; production trade history records proposed GTOS levels, not counterparty stop clusters.",
        "artifact_required": "direct stop-cluster/counterparty data or feature-specific preregistered cohort clearing methodology gates",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "rejected_below_noise_proxy",
        "reconciliation_note": "Current Osler/K-7 proxy path is closed as failed; this does not disprove true counterparty stop clustering.",
    },
    "E-2": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 610,
        "blocked_by": "Current all-symbol MT5 tick coverage is short and quote-only; Toth-Bouchaud latent-liquidity shape needs mature tick/depth/order-flow evidence.",
        "artifact_required": ">=30 trading days all-symbol ticks or approved depth/order-flow feed plus preregistered V-shape estimator",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "deferred_substrate_maturity",
        "reconciliation_note": "Toth-Bouchaud V-shape work is deferred until the tick/depth substrate is mature enough for the mechanism.",
    },
    "E-4": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 610,
        "blocked_by": "F11/OB-decay artifacts exist, but no retail-flow-share proxy, broker client-sentiment cache, Google Trends cache, or social-flow dataset is available locally.",
        "artifact_required": "legal retail-flow-share proxy with time coverage aligned to F11 windows",
        "latest_artifact_path": "research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane6_asset_risk_edge_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_missing_retail_flow_proxy",
        "reconciliation_note": "F11-vs-retail-flow regression is blocked until a retail-flow-share proxy exists.",
    },
    "A-1": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Local FlashAlpha GEX proxy exists but only forward/current snapshots are cached; no legal historical gamma-sign series is available for NAS/US30 cross-period sign-flip validation.",
        artifact_required=">=30 trading days of FlashAlpha snapshots or legal historical CBOE/GEX data",
        candidate_strength_vs_j46_j49="deferred_proxy_feature_not_strategy_comparable",
        reconciliation_note="FlashAlpha GEX has 15 local proxy rows; gamma sign is forward-only until the history trigger is met.",
    ),
    "A-4": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="A-1 is forward-only and A-2/A-3 are blocked; same-cohort K54/K55 retraining is closed until cohort/source-quality triggers.",
        artifact_required="source-complete A-1/A-2/A-3 feature set plus approved retraining trigger",
        candidate_strength_vs_j46_j49="blocked_specialist_retrain_inputs_absent",
        reconciliation_note="NAS_US30 specialist retrain cannot verify the sign-flip cure from current local inputs.",
    ),
    "A-5": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="No local Japan/UK rate-differential, carry-unwind, or BIS/Aquilina source is cached for JPY-pair factor decomposition.",
        artifact_required="legal JPY carry/rate-differential source cache with publication-time metadata",
        candidate_strength_vs_j46_j49="blocked_missing_jpy_carry_sources",
        reconciliation_note="Local FRED/DXY/VIX partial macro cache is insufficient for JPY carry factor decomposition.",
    ),
    "A-6": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="No local BoE policy, GBP political-risk, or registered legal proxy feed exists.",
        artifact_required="legal BoE/GBP policy-risk source contract and cache",
        candidate_strength_vs_j46_j49="blocked_missing_gbp_policy_sources",
        reconciliation_note="GBP specialist feature construction is source-blocked, not an ML architecture task.",
    ),
    "A-7": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="FRED has partial USD macro series but no Treasury-basis/intermediary-capital source or Fed-funds feature contract is registered.",
        artifact_required="Treasury-basis/intermediary-capital/Fed-funds feature sources with as-of metadata",
        candidate_strength_vs_j46_j49="blocked_partial_macro_cache_only",
        reconciliation_note="FRED cache has yields, DXY, VIX/GVZ, and inflation proxies, but not the full dollar-specialist feature set.",
    ),
    "A-9": lane6_priority620_overlay(
        "DONE",
        artifact_required="feed-feasibility artifact; alpha validation separate",
        candidate_strength_vs_j46_j49="not_strategy_comparable_feed_feasibility_only",
        reconciliation_note="Gold COT feed feasibility is satisfied for XAUUSD via the normalized CFTC cache; no alpha validation is implied.",
    ),
    "A-11": lane6_priority620_overlay(
        "DONE",
        artifact_required="calendar-feature feasibility artifact; alpha validation separate",
        candidate_strength_vs_j46_j49="not_strategy_comparable_calendar_feature_only",
        reconciliation_note="LBMA fix-calendar feature feasibility is satisfied for metals via the normalized calendar cache.",
    ),
    "A-12": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="No Krohn-Mueller-Whelan FX-fix source/cache exists locally; D-5 remains blocked for FX-fix scope.",
        artifact_required="confirmed KMW FX-fix source/licensing path or registered legal proxy",
        candidate_strength_vs_j46_j49="blocked_missing_fx_fix_source",
        reconciliation_note="LBMA calendar readiness does not supply the KMW top-9-currency FX-fix dataset.",
    ),
    "A-13": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="VIXCLS and Treasury yields exist, but TED/funding-liquidity/intermediary-capital source contract is incomplete.",
        artifact_required="complete funding-liquidity factor sources with no-lookahead metadata",
        candidate_strength_vs_j46_j49="blocked_incomplete_funding_liquidity_sources",
        reconciliation_note="FRED cache is partial and does not complete the Brunnermeier-Nagel-Pedersen funding-liquidity feature.",
    ),
    "A-14": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="No BIS JPY carry-unwind table/cache/source spec exists locally.",
        artifact_required="BIS JPY carry-unwind table/cache/source spec",
        candidate_strength_vs_j46_j49="blocked_missing_bis_jpy_source",
        reconciliation_note="Aquilina-style JPY carry-unwind classifier is source-blocked until BIS data is registered.",
    ),
    "A-16": lane6_priority620_overlay(
        "FILED_FOR_APPROVAL",
        blocked_by="Replacing the live cross-instrument correlation gate would alter risk behavior and needs CEO approval; research-only prototype can be scoped separately.",
        artifact_required="CEO approval before any live risk-model replacement work",
        candidate_strength_vs_j46_j49="not_strategy_comparable_risk_model_approval",
        reconciliation_note="DCC/cDCC/Block-DECO is filed as an approval-gated risk-model replacement, not an unblocked live-code change.",
    ),
    "B-2": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Portfolio-wide vol conditioning failed; NAS100-only subcandidate needs shadow/approval trigger before Component 3C work.",
        artifact_required="NAS100-only shadow design/approval after H-PM01 portfolio failure",
        candidate_strength_vs_j46_j49="deferred_component_3c_nas100_only_shadow",
        reconciliation_note="H-PM01 portfolio delta mean R=-0.004960547358764833 with DSR-p=0.9999646857030353; NAS100-only remains a future shadow candidate.",
    ),
    "B-3": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Risk-policy replacement must be simulated over DSR-surviving J46-J49/S79 baselines and needs live-risk approval.",
        artifact_required="preregistered replacement-risk simulation plus CEO approval",
        candidate_strength_vs_j46_j49="deferred_risk_replacement_not_validated",
        reconciliation_note="Combined MC supports shipped full-stack risk; no replacement policy is validated.",
    ),
    "B-4": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Asset-specialist bundle depends on blocked/deferred A-1/A-2/A-3/A-4/A-5/A-6/A-7/A-8; A-9/A-11 are feed-feasibility only.",
        artifact_required="source-complete constituent asset-specialist feature set",
        candidate_strength_vs_j46_j49="blocked_bundle_constituents_unavailable",
        reconciliation_note="Most constituent specialist features lack source-complete as-of data.",
    ),
    "B-7": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Edge-mechanism bundle has E-1 failed, E-2 deferred, E-4 blocked, and E-3 blocked.",
        artifact_required="constituent edge-mechanism items unblocked or completed",
        candidate_strength_vs_j46_j49="blocked_bundle_constituents_unavailable",
        reconciliation_note="No bundle-level edge-mechanism validation can proceed from current local data.",
    ),
    "C-3": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Inverted-TP log has correction records but no symbol/outcome linkage, so Walasek lambda-context dependence cannot be measured from current data.",
        artifact_required="symbol/outcome/realized-R linkage for inverted-TP corrections",
        candidate_strength_vs_j46_j49="blocked_missing_outcome_linkage",
        reconciliation_note="knowledge_base/inverted_tp_log.jsonl has 66 rows, but current keys lack realized-R/outcome and symbol linkage.",
    ),
    "C-4": lane6_priority620_overlay(
        "DONE",
        artifact_required="H-PM03/combined-MC LONG-modifier simulation evidence",
        candidate_strength_vs_j46_j49="risk_modifier_live_stack_not_new_signal",
        reconciliation_note="Daniel-Moskowitz-style LONG modifier simulation is closed by H-PM03/combined MC: side_aware_everywhere H2 P(pass)=0.7806666666666666 and full P(bust HARD)=0.022.",
    ),
    "C-5": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="K54/K55 same-cohort training is closed after v3/v4 failures; reopen only with n>=5000 or source-quality/cohort-expansion trigger.",
        artifact_required="n>=5000 or source-quality/cohort-expansion trigger before Sharpe-objective training",
        candidate_strength_vs_j46_j49="deferred_loss_function_until_new_cohort",
        reconciliation_note="Sharpe-objective training is a future K-family loss-function study, not current-cohort work.",
    ),
    "C-6": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Continuous-sized entries require actual broker-R/fill truth, lifecycle telemetry, and live-risk approval before system-flow use.",
        artifact_required="actual-R/fill-truth/lifecycle telemetry and CEO approval",
        candidate_strength_vs_j46_j49="deferred_continuous_sizing_label_truth",
        reconciliation_note="Existing MC covers fixed policy overlays; continuous sizing remains future research after label-truth blockers clear.",
    ),
    "C-8": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Feature-stability artifacts exist, but there is no K54 production deployment performance series because K54 is not deployed.",
        artifact_required="K55 shadow/live performance series joined to feature-stability artifacts",
        candidate_strength_vs_j46_j49="blocked_no_production_ml_performance_series",
        reconciliation_note="K54 v3 mean Jaccard=0.1685447455309013 with 2 stable features; deployment-performance regression awaits K55 rows.",
    ),
    "E-3": lane6_priority620_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Lillo-Mike-Farmer-Sato meta-order long-memory needs signed order-flow/meta-order aggregates; local OHLCV/H1 bars and MT5 tick volume are not a parent-order flow substrate.",
        artifact_required="signed order-flow/meta-order aggregate source",
        candidate_strength_vs_j46_j49="blocked_missing_signed_orderflow",
        reconciliation_note="Do not substitute candle direction or retail tick volume for signed meta-order flow.",
    ),
    "E-5": lane6_priority620_overlay(
        "DONE",
        artifact_required="uncorrelated-edge inventory artifact",
        candidate_strength_vs_j46_j49="not_single_strategy_inventory_only",
        reconciliation_note="Uncorrelated-edge discovery inventory is current via NA-11 plus queue state; live candidates remain discovery/forward-shadow only.",
    ),
    "R-1": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Risk-constrained Kelly replacement needs a preregistered simulation over DSR-surviving J46-J49/S79 baselines and CEO approval before risk behavior changes.",
        artifact_required="preregistered RCK simulation plus CEO approval",
        candidate_strength_vs_j46_j49="deferred_risk_policy_replacement",
        reconciliation_note="Current evidence supports shipped S79/full-stack risk, not replacing it with RCK.",
    ),
    "R-2": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Lambda auto-calibration depends on R-1 and owner-approved risk replacement path.",
        artifact_required="R-1 approval path plus validated lambda calibration design",
        candidate_strength_vs_j46_j49="deferred_depends_on_r1",
        reconciliation_note="No lambda knob is approved or validated for FN constraint auto-calibration.",
    ),
    "R-5": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Per-instrument weights require the R-1 simulation path and source-flagged all-symbol cohort; do not override S79 uniform profile from current evidence.",
        artifact_required="R-1 simulation path plus source-flagged all-symbol cohort",
        candidate_strength_vs_j46_j49="deferred_weight_optimization_not_validated",
        reconciliation_note="Existing S79/full-stack evidence remains the active baseline.",
    ),
    "R-6": lane6_priority620_overlay(
        "DONE",
        artifact_required="H-PM03/combined-MC side-aware sizing evidence",
        candidate_strength_vs_j46_j49="risk_modifier_already_live_not_new_signal",
        reconciliation_note="Side-aware sizing is closed by H-PM03/combined MC and existing config flip: full P(bust HARD)=0.022.",
    ),
    "R-7": lane6_priority620_overlay(
        "REJECTED_FAILED",
        artifact_required="H-PM01 portfolio-wide vol-scaled sizing failure evidence",
        candidate_strength_vs_j46_j49="rejected_portfolio_wide_vol_scaled_sizing",
        reconciliation_note="All-7 vol-scaled sizing failed portfolio-wide in H-PM01: delta mean R=-0.004960547358764833, DSR-p=0.9999646857030353.",
    ),
    "R-8": lane6_priority620_overlay(
        "DONE",
        artifact_required="lambda-context control audit artifact",
        candidate_strength_vs_j46_j49="not_strategy_comparable_static_risk_audit",
        reconciliation_note="Lambda-context audit is resolved at control level; any lambda-knob replacement is deferred under R-1/R-2.",
    ),
    "R-9": lane6_priority620_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Bundle depends on deferred R-1/R-2/R-5 and rejected R-7; only R-6 is done.",
        artifact_required="constituent risk-policy replacement items validated and approved",
        candidate_strength_vs_j46_j49="deferred_bundle_constituents_not_ready",
        reconciliation_note="Risk-policy bundle cannot replace S79/full-stack from current evidence.",
    ),
    "V-4": lane6_tail_overlay(
        "DONE",
        artifact_required="sigma multiplier mapping evidence",
        candidate_strength_vs_j46_j49="not_strategy_comparable_sizing_function_done",
        reconciliation_note="Sigma multiplier mapping exists in H-PM01: bsc_sigma_mult = clip(median_vol / realized_vol_30d, 0.5, 2.0).",
    ),
    "V-5": lane6_tail_overlay(
        "REJECTED_FAILED",
        artifact_required="H-PM01 Barroso-Santa-Clara portfolio backtest",
        candidate_strength_vs_j46_j49="rejected_portfolio_wide_vol_managed_backtest",
        reconciliation_note="Barroso-Santa-Clara vol-managed backtest failed portfolio-wide: delta mean R=-0.004960547358764833, delta Sharpe=-2.5761764707408985%, DSR-p=0.9999646857030353.",
    ),
    "V-6": lane6_tail_overlay(
        "REJECTED_FAILED",
        artifact_required="H-PM01 vol-managed vs uniform 2% A/B",
        candidate_strength_vs_j46_j49="rejected_uniform_vs_vol_managed_ab",
        reconciliation_note="Vol-managed sizing vs uniform 2% A/B is H-PM01 and failed portfolio-wide.",
    ),
    "V-7": lane6_tail_overlay(
        "DONE",
        artifact_required="H-PM03/combined-MC side-aware evidence",
        candidate_strength_vs_j46_j49="risk_modifier_already_live_not_new_signal",
        reconciliation_note="Daniel-Moskowitz-style LONG/side-aware sizing is closed by H-PM03/combined MC.",
    ),
    "V-8": lane6_tail_overlay(
        "REJECTED_FAILED",
        artifact_required="H-PM01 broad vol-scaling policy failure evidence",
        candidate_strength_vs_j46_j49="rejected_broad_vol_scaling_policy",
        reconciliation_note="Moreira-Muir/Barroso broad vol-scaling fails as an all-symbol policy; NAS100-only remains shadow/deferred.",
    ),
    "V-9": lane6_tail_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Component 3C bundle depends on V-2 source completion and broad V-5/V-6 success; portfolio-wide vol sizing failed and live insertion requires approval.",
        artifact_required="NAS100-only shadow/approval route or new source-complete vol bundle",
        candidate_strength_vs_j46_j49="deferred_component_3c_bundle_not_validated",
        reconciliation_note="Keep only NAS100-only shadow/approval route open from current H-PM01 evidence.",
    ),
    "X-1": lane6_tail_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Volume-bar E24/E26 retest needs real trade volume or approved tick/depth feed; MT5 retail tick volume is not a volume-bar substrate.",
        artifact_required="approved real-volume/depth feed or volume-bar substrate",
        candidate_strength_vs_j46_j49="blocked_missing_real_volume_bars",
        reconciliation_note="Current tick cache is quote/retail-substrate limited.",
    ),
    "X-2": lane6_tail_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Dollar-bar E24/E26 retest needs price x real traded volume; current MT5 feed lacks true centralized trade volume.",
        artifact_required="approved real trade-volume feed",
        candidate_strength_vs_j46_j49="blocked_missing_dollar_bar_substrate",
        reconciliation_note="Use only after futures/venue trade-volume data exists.",
    ),
    "X-3": lane6_tail_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Imbalance-bar E24/E26 retest needs signed trades or aggressor-side proxy; current local data is OHLCV/quote-tick only.",
        artifact_required="approved signed-trade/aggressor-side feed",
        candidate_strength_vs_j46_j49="blocked_missing_imbalance_bar_substrate",
        reconciliation_note="Do not substitute candle direction for signed trade imbalance.",
    ),
    "X-5": lane6_tail_overlay(
        "DONE",
        artifact_required="seven-symbol rough-vol Hurst diagnostic",
        candidate_strength_vs_j46_j49="not_strategy_comparable_rough_vol_diagnostic",
        reconciliation_note="Rough-vol proxy H estimated on 7 symbols from local M15 data; median H=0.5050851741228051, range=[0.48422314477656087, 0.6033981383377698].",
    ),
    "X-6": lane6_tail_overlay(
        "DONE",
        artifact_required="canonical K54 v1 reconciliation evidence",
        candidate_strength_vs_j46_j49="not_applicable_baseline_reconciliation",
        reconciliation_note="K54 v1 0.571 was reconciled by canonical_v1_rerun/K1 follow-ups; promotion anchor is CPCV-honest 0.5286.",
    ),
    "A-10": lane6_tail_overlay(
        "DONE",
        artifact_required="WGC feed-feasibility artifact",
        candidate_strength_vs_j46_j49="not_strategy_comparable_feed_feasibility_only",
        reconciliation_note="WGC data plumbing exists with latest demand rows=9475 and central-bank-like rows=162; alpha validation remains separate.",
    ),
    "A-15": lane6_tail_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="No He-Kelly-Manela/intermediary-capital source, status file, normalized cache, or source spec exists locally.",
        artifact_required="legal H-K-M/intermediary-capital source and cache",
        candidate_strength_vs_j46_j49="blocked_missing_hkm_source",
        reconciliation_note="Same blocker as D-7; FRED/WGC/CFTC feeds do not supply H-K-M intermediary-capital SDF.",
    ),
    "A-17": lane6_tail_overlay(
        "DONE",
        artifact_required="tail-dependence diagnostic artifact",
        candidate_strength_vs_j46_j49="not_strategy_comparable_tail_diagnostic",
        reconciliation_note="Copula/tail-dependence diagnostic ran on 13064 aligned M15 returns and 21 pairs; feature feasibility only.",
    ),
    "A-18": lane6_tail_overlay(
        "DONE",
        artifact_required="Forbes-Rigobon correlation diagnostic artifact",
        candidate_strength_vs_j46_j49="not_strategy_comparable_correlation_diagnostic",
        reconciliation_note="Forbes-Rigobon adjusted high-vol correlations are included in the tail-correlation diagnostic; feature feasibility only.",
    ),
    "B-5": lane6_tail_overlay(
        "FILED_FOR_APPROVAL",
        blocked_by="AI-grounding bundle depends on L-1/L-2/L-8 and would alter Component 3A behavior if wired live; L-4 debate is owner-parked for now because it adds AI/API cost.",
        artifact_required="CEO approval plus refreshed shadow-only AI grounding design that excludes debate unless L-4 is explicitly reopened",
        candidate_strength_vs_j46_j49="filed_ai_behavior_bundle_approval",
        reconciliation_note="Tool scaffolding exists, but live AI behavior changes need explicit CEO approval; Component 3B debate remains dormant by owner decision.",
    ),
    "R-3": lane6_tail_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Strub EVT-CDaR sizing needs preregistered simulation over DSR-surviving baselines and CEO approval before risk behavior changes.",
        artifact_required="preregistered EVT-CDaR simulation plus CEO approval",
        candidate_strength_vs_j46_j49="deferred_risk_policy_replacement",
        reconciliation_note="Keep as future risk-policy replacement branch, not an unblocked live implementation.",
    ),
    "R-4": lane6_tail_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Smooth Grossman-Zhou drawdown control needs simulation and owner approval; current H29 drawdown reducer remains the live safety path.",
        artifact_required="preregistered drawdown-control simulation plus CEO approval",
        candidate_strength_vs_j46_j49="deferred_drawdown_policy_replacement",
        reconciliation_note="Do not alter live drawdown behavior from current evidence.",
    ),
    "X-4": lane6_tail_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Tick-level Hawkes fitting needs mature tick/depth/order-flow history; current tick capture is short and quote-only.",
        artifact_required=">=30 trading days all-symbol ticks or approved signed order-flow/depth feed",
        candidate_strength_vs_j46_j49="deferred_tick_substrate_maturity",
        reconciliation_note="Current tick cache has 30 parquet files across 7 symbols.",
    ),
    "X-7": lane6_tail_overlay(
        "FILED_FOR_APPROVAL",
        blocked_by="Cascade-prompt rebuild would touch prompts/trading evaluation behavior; V4/cascade remains shelved/lost and requires explicit CEO approval before rebuild.",
        artifact_required="CEO approval before prompt rebuild",
        candidate_strength_vs_j46_j49="filed_prompt_behavior_approval",
        reconciliation_note="Recovered template exists, but no prompt rebuild is an unblocked research-loop change.",
    ),
    "L-1": lane6_tail_overlay(
        "FILED_FOR_APPROVAL",
        blocked_by="QuantMCP-style grounding would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required.",
        artifact_required="CEO approval plus refreshed shadow-only tool-use design",
        candidate_strength_vs_j46_j49="filed_tool_use_grounding_approval",
        reconciliation_note="ai_tools scaffolding and design exist, but PrimaryAnalyzer does not import ai_tools.",
    ),
    "L-2": lane6_tail_overlay(
        "FILED_FOR_APPROVAL",
        blocked_by="FinAgent-style market-state tool inventory would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required.",
        artifact_required="CEO approval plus refreshed market-state tool inventory design",
        candidate_strength_vs_j46_j49="filed_tool_inventory_approval",
        reconciliation_note="Current ai_tools files include recent-outcome/session-vol registry scaffolding.",
    ),
    "L-4": lane6_tail_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Owner decision 2026-05-03: leave Component 3B debate dormant because it is down-road work and adds extra AI/API cost.",
        artifact_required="Reopen only with explicit CEO request plus a shadow-only, budget-capped debate design",
        candidate_strength_vs_j46_j49="deferred_owner_parked_extra_api_cost",
        reconciliation_note="Debate code/tests exist, but orchestrator does not import debate; keep it out of near-term approval queue.",
    ),
    "L-8": lane6_tail_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="LLM transfer test depends on L-1/L-2 shadow grounding implementation and approval path.",
        artifact_required="L-1/L-2 shadow grounding harness before Sonnet transfer test",
        candidate_strength_vs_j46_j49="deferred_depends_on_grounding_shadow",
        reconciliation_note="No Sonnet-class transfer test can be run before the grounding intervention exists in a shadow harness.",
    ),
    "RR-1": lane6_tail_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Quarterly last-6-months literature refresh across 22 domains requires a dedicated current-web literature sweep and source-citation pass outside this local evidence triage.",
        artifact_required="dedicated web-enabled quarterly literature-refresh pass",
        candidate_strength_vs_j46_j49="deferred_dedicated_literature_refresh",
        reconciliation_note="Existing local literature corpus remains usable, but RR-1 specifically asks for current last-6-month paper discovery.",
    ),
    "RR-2": lane7_overlay(
        "DONE",
        artifact_required="current DSR/effective-N tracker snapshot",
        candidate_strength_vs_j46_j49="not_applicable_methodology_tracker",
        reconciliation_note="Current DSR/effective-N tracker snapshot has 15 DSR rows and promotion-p-value allowed count 0.",
    ),
    "RR-3": lane7_overlay(
        "DONE",
        artifact_required="current decay-alarm snapshot",
        candidate_strength_vs_j46_j49="not_applicable_decay_monitor_snapshot",
        reconciliation_note="Current OB continuation snapshot has latest date 2026-05-01 with 0 alarms; monthly decay report exists.",
    ),
    "RR-4": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Requires the same dedicated current-web literature sweep deferred under RR-1.",
        artifact_required="dedicated current-web literature refresh after failed experiments",
        candidate_strength_vs_j46_j49="deferred_current_literature_refresh",
        reconciliation_note="Local killed-hypothesis and backlog artifacts are current, but new-literature refresh is not a local-evidence task.",
    ),
    "RR-5": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Capacity-decay band re-evaluation needs actual AUM/capacity growth or venue-volume participation data.",
        artifact_required="AUM/capacity trigger plus venue-volume or slippage/capacity data",
        candidate_strength_vs_j46_j49="deferred_capacity_trigger_absent",
        reconciliation_note="Current live prop-account scale does not trigger capacity analysis.",
    ),
    "RR-6": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Needs separately logged live edge return streams before an edge-correlation/diversification metric is meaningful.",
        artifact_required="edge-level live return streams for active alpha inventory",
        candidate_strength_vs_j46_j49="deferred_missing_edge_return_streams",
        reconciliation_note="Current alpha inventory is not enough to estimate a hypothesis-portfolio correlation matrix.",
    ),
    "RR-7": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Requires a current-web paper status/retraction watcher with source citations.",
        artifact_required="web-enabled paper status/retraction watcher",
        candidate_strength_vs_j46_j49="deferred_current_paper_status_watcher",
        reconciliation_note="No local source can prove that no domain paper expired or was retracted.",
    ),
    "U-1": lane7_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Same blocker as M-5: full 2022-2023 v2/v3 feature catalog plus source-flagged supplemental old-label integration.",
        artifact_required="full v2/v3 backfill and source-flagged old-label integration",
        candidate_strength_vs_j46_j49="blocked_same_as_m5",
        reconciliation_note="Current doctrine remains AFML/CPCV-honest; exact per-instrument Inoue-Kilian resolution is data-blocked.",
    ),
    "U-2": lane7_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="MT5 alone has no option dealer gamma sign, VIX1D/VIX9D, VRP, or official GEX source.",
        artifact_required="external options/gamma source or approved proxy contract",
        candidate_strength_vs_j46_j49="blocked_missing_gamma_source",
        reconciliation_note="FlashAlpha Basic proxy data exists, but gamma sign is not constructible from MT5 OHLC/tick data alone.",
    ),
    "U-4": lane7_overlay(
        "DONE",
        artifact_required="K54 v3/v4 per-instrument/group sweep evidence",
        candidate_strength_vs_j46_j49="NAS_US30 specialist discovery only; global K54 failed",
        reconciliation_note="Per-instrument/group sweep is answered by K54 v3/v4 triage: global K54 failed; strongest remaining group is NAS_US30 specialist discovery.",
    ),
    "U-6": lane7_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Broker substrate lacks true trade count/depth; current tick files are retail quote ticks, not centralized trade prints.",
        artifact_required="true trade-print/depth feed before trade-count-time bars",
        candidate_strength_vs_j46_j49="blocked_missing_trade_count_substrate",
        reconciliation_note="Same substrate blocker as X-1/X-2/X-3; do not relabel quote-tick count as trade-count time.",
    ),
    "U-8": lane7_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="No He-Kelly-Manela/intermediary-capital source, cache, or source contract exists locally.",
        artifact_required="legal H-K-M/intermediary-capital source and cache",
        candidate_strength_vs_j46_j49="blocked_missing_hkm_source",
        reconciliation_note="Lane 7 triage found no local H-K-M/intermediary-capital source.",
    ),
    "U-9": lane7_overlay(
        "DONE",
        artifact_required="lambda-context code/config scan",
        candidate_strength_vs_j46_j49="not_strategy_comparable_control_scan",
        reconciliation_note="Live config/code scan found 0 literal lambda=2 hits; relevant risk/ratio knobs are config-driven.",
    ),
    "U-10": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Depends on L-1/L-2 tool-use grounding shadow implementation and approval path.",
        artifact_required="approved L-1/L-2 shadow grounding harness",
        candidate_strength_vs_j46_j49="deferred_depends_on_grounding_shadow",
        reconciliation_note="Tool scaffolding exists but PrimaryAnalyzer does not import ai_tools.",
    ),
    "U-12": lane7_overlay(
        "BLOCKED_WITH_REASON",
        blocked_by="Same blocker as A-8: no local CPI/PCE-deflated real-gold-price percentile construction.",
        artifact_required="real-gold-price percentile source and construction",
        candidate_strength_vs_j46_j49="blocked_missing_real_gold_feature",
        reconciliation_note="Erb-Harvey remains a literature lens, not a locally validated decay attribution feature.",
    ),
    "U-13": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Needs AUM/capacity trigger plus venue-volume or slippage/capacity data by instrument.",
        artifact_required="AUM/capacity trigger plus per-instrument venue/slippage data",
        candidate_strength_vs_j46_j49="deferred_capacity_trigger_absent",
        reconciliation_note="Same practical trigger as RR-5.",
    ),
    "U-14": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Needs longer live history or a clean publication/crowding proxy panel; current OB-decay monitor is sample-limited.",
        artifact_required="longer live history or publication/crowding proxy panel",
        candidate_strength_vs_j46_j49="deferred_decay_sample_limited",
        reconciliation_note="Current monitor observes decay but does not validate McLean-Pontiff publication-decay rate on GTOS edge.",
    ),
    "U-15": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Requires dedicated literature/book synthesis and translation into substrate-immune candidate specs.",
        artifact_required="dedicated Renaissance/edge-aggregation synthesis",
        candidate_strength_vs_j46_j49="deferred_dedicated_literature_synthesis",
        reconciliation_note="Session-45 pivot references Renaissance-style candidates, but this item is not locally closed as a deep dive.",
    ),
    "U-16": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Depends on P-8: standalone sticky-HDP-HMM plus Kirby fat-tailed-mixture null-test harness.",
        artifact_required="HDP-HMM/Kirby-null research harness",
        candidate_strength_vs_j46_j49="deferred_depends_on_p8_harness",
        reconciliation_note="No local HDP-HMM/Kirby-null harness has passed.",
    ),
    "U-17": lane7_overlay(
        "DONE",
        artifact_required="Path-9 temporal-window and cached-FRED context artifact",
        candidate_strength_vs_j46_j49="not_applicable_path_diagnostic",
        reconciliation_note="Path-9 is Feb-heavy and cross-cohort, not single-symbol; fold 4 turns negative after the window and cached FRED shows elevated gold volatility.",
    ),
    "L-3": lane7_overlay(
        "FILED_FOR_APPROVAL",
        blocked_by="Reflexion/post-trade feedback loop would alter AI/adaptation behavior and needs CEO approval plus shadow-only design.",
        artifact_required="CEO approval plus shadow-only Reflexion design",
        candidate_strength_vs_j46_j49="filed_ai_adaptation_approval",
        reconciliation_note="AdaptiveReview exists, but this is not a live Reflexion loop.",
    ),
    "L-5": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="Hybrid LLM+ML architecture depends on a surviving K55/K54 shadow candidate and approval for system-flow changes.",
        artifact_required="surviving shadow candidate plus system-flow approval",
        candidate_strength_vs_j46_j49="deferred_architecture_path_no_surviving_candidate",
        reconciliation_note="Current K54 global architectures failed; L-5 is a future architecture path, not an unblocked implementation.",
    ),
    "Z-1": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="No current GTOS classical-pipeline blocker requires quantum finance work; revisit only on explicit CEO request or after classical methods saturate.",
        artifact_required="explicit CEO request or classical-method saturation trigger",
        candidate_strength_vs_j46_j49="deferred_low_priority_quantum_track",
        reconciliation_note="Local quantum-related research files found but no GTOS implementation path is unblocked.",
    ),
    "Z-2": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="No current GTOS derivatives-evaluation bottleneck or quantum runtime path exists.",
        artifact_required="explicit derivatives-evaluation bottleneck plus quantum runtime path",
        candidate_strength_vs_j46_j49="deferred_low_priority_quantum_track",
        reconciliation_note="Quantum Monte Carlo is not an unblocked GTOS trading-research task.",
    ),
    "Z-3": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="No current GTOS RL/quantum runtime path exists, and live-learning changes would require separate approval.",
        artifact_required="explicit CEO request plus approved RL/quantum research path",
        candidate_strength_vs_j46_j49="deferred_low_priority_quantum_track",
        reconciliation_note="Quantum RL review is not an unblocked GTOS trading-research task.",
    ),
    "Z-4": lane7_overlay(
        "DEFERRED_WITH_TRIGGER",
        blocked_by="No current GTOS classical-pipeline blocker requires quantum finance work; revisit only on explicit CEO request or after classical methods saturate.",
        artifact_required="explicit CEO request or classical-method saturation trigger",
        candidate_strength_vs_j46_j49="deferred_low_priority_quantum_track",
        reconciliation_note="IBM/Goldman quantum derivatives literature follow is not an unblocked GTOS trading-research task.",
    ),
    "D-1": {
        "status": "DEFERRED_WITH_TRIGGER",
        "priority": 520,
        "blocked_by": "Tick capture exists for 7/7 symbols, but local history is only 5 days at best and MT5 retail volume/last fields are not a real volume/dollar substrate.",
        "artifact_required": ">=30 trading days of all-symbol tick captures or approved paid LOB/trade feed",
        "latest_artifact_path": "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_data_source_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_data_substrate",
        "reconciliation_note": "Lane 5 data-source triage defers D-1 until tick history/substrate trigger is met; tick capture/helpers are present but not volume/dollar/imbalance bar infrastructure.",
    },
    "D-2": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 520,
        "blocked_by": "Local MT5 tick probes and tick-capture cache do not provide pre-2024 tick history; broker retention only covers recent windows.",
        "artifact_required": "alternate broker/provider/archive or paid historical tick/LOB source with pre-2024 coverage",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_data_feed_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_data_availability",
        "reconciliation_note": "Lane 5 remaining data/feed triage blocks D-2 on broker tick-history retention.",
    },
    "D-4": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 520,
        "blocked_by": "CFTC fetcher and XAUUSD gold cache exist, but no local FX COT contract mappings/rows are present.",
        "artifact_required": "official CFTC FX contract map plus fetched/cached FX COT rows with publication-time guards",
        "latest_artifact_path": "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_data_source_triage.py tests/test_external_feeds.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_data_source",
        "reconciliation_note": "Lane 5 data-source triage confirms the CFTC infrastructure/gold cache exists, but the full gold+FX backlog item remains blocked.",
    },
    "D-5": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 520,
        "blocked_by": "LBMA gold/silver fix calendar exists, but no local Krohn-Mueller-Whelan FX-fix source/cache is present.",
        "artifact_required": "confirmed KMW FX-fix source/licensing path or registered legal FX-fix proxy",
        "latest_artifact_path": "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_data_source_triage.py tests/test_external_feeds.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_data_source",
        "reconciliation_note": "Lane 5 data-source triage confirms LBMA calendar exists, but the full LBMA+KMW FX-fix backlog item remains blocked.",
    },
    "D-7": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 520,
        "blocked_by": "No local H-K-M/intermediary-capital SDF source, status file, normalized cache, or registered source spec was found.",
        "artifact_required": "legal H-K-M source/access path plus no-lookahead publication metadata",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_data_feed_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_data_source",
        "reconciliation_note": "Lane 5 remaining data/feed triage blocks D-7 until a legal H-K-M/intermediary-capital source is registered.",
    },
    "D-8": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 520,
        "blocked_by": "FRED macro cache exists, but no BIS source/cache/spec exists locally; full FRED/BIS item remains incomplete.",
        "artifact_required": "BIS macro source tables cached with publication-time metadata and joined to existing FRED cache",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_data_feed_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_data_source_partial_fred_ready",
        "reconciliation_note": "Lane 5 remaining data/feed triage confirms FRED is ready but BIS is absent.",
    },
    "D-9": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 520,
        "blocked_by": "No distinct Federal Reserve research-feed source contract, parser, status file, or normalized cache exists beyond the FRED macro feed.",
        "artifact_required": "defined Federal Reserve research source, fields, cadence, publication-time model, and parser/cache",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_data_feed_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_ambiguous_source",
        "reconciliation_note": "Lane 5 remaining data/feed triage blocks D-9 because the requested Fed research feed is not specified or cached beyond FRED.",
    },
    "D-10": {
        "status": "DONE",
        "priority": 520,
        "blocked_by": "",
        "artifact_required": "data-plumbing complete; alpha validation and scheduled/operator refresh remain separate work",
        "latest_artifact_path": "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_remaining_data_feed_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_strategy_comparable_feed_integration_only",
        "reconciliation_note": "Lane 5 remaining data/feed triage closes D-10 as WGC data plumbing; local GDT/ETF imports include central-bank/other-institution rows.",
    },
    "D-12": {
        "status": "BLOCKED_WITH_REASON",
        "priority": 520,
        "blocked_by": "Current MT5 history probes show no full 2021 all-symbol M15 coverage; only XAGUSD has a small late-2021 slice.",
        "artifact_required": "alternate broker/provider/archive for pre-2022 OHLCV coverage",
        "latest_artifact_path": "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md",
        "tests_required": "python -m pytest tests/test_lane5_data_source_triage.py -q",
        "candidate_strength_vs_j46_j49": "not_applicable_data_availability",
        "reconciliation_note": "Lane 5 data-source triage blocks D-12 on broker history availability; current redacted_account MT5 cannot supply full pre-2022 coverage.",
    },
}


SYNTHETIC_QUEUE_ITEMS: list[dict[str, Any]] = [
    {
        "id": "P0-SOURCE-MAP",
        "lane": "lane_0_control_tower",
        "status": "DONE",
        "blocked_by": "",
        "artifact_required": "source-map artifact",
        "tests_required": "documentation-only",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable",
        "priority": 5,
        "dependencies": [],
        "new_followups_opened": [],
        "tier": "P0",
        "section": "weekend_goal",
        "item": "No-forward-data source map and run plan.",
        "latest_artifact_path": "research/phase_3_external_feed_validation/WEEKEND_NO_FORWARD_DATA_SOURCE_MAP_2026-05-03.md",
        "reconciliation_note": "Weekend P0 artifact exists and preserves NO_PROMOTION_VERDICT.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P1-A-V2-CONFLUENCE-DEEPDIVE",
        "lane": "lane_2_path_scaling",
        "status": "ACCEPTED_CANDIDATE_DISCOVERY",
        "blocked_by": "Unseen/forward confluence rows required before validation.",
        "artifact_required": "forward-only confluence ledger after V2b resolved rows exist",
        "tests_required": "python -m pytest tests/test_raw_ohlc_path_scaling_v2_confluence_deepdive.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "positive_same_dataset_discovery_vs_j46; FVG delta full +0.033292R, 2026 +0.365975R; OB delta full +0.024061R, 2026 +0.233839R; no promotion",
        "priority": 205,
        "dependencies": [],
        "new_followups_opened": [
            "V2DD-H1-FVG-ONLY-RESCUE-POCKET",
            "V2DD-H2-FVG-THEN-OB-TAIL-PRESERVATION",
            "V2DD-H3-COMPOSITE-ARBITRATION-NOT-BLIND-COMPOSITE",
        ],
        "tier": "P1",
        "section": "weekend_goal",
        "item": "V2 confluence/disagreement deep dive.",
        "latest_artifact_path": "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.md",
        "reconciliation_note": "Discovery pockets accepted; Composite remains global overlock warning.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P1-B-PREFILL-DELIVERY-PATH-HARNESS",
        "lane": "lane_2_path_scaling",
        "status": "DONE",
        "blocked_by": "",
        "artifact_required": "coverage artifact plus sample rows",
        "tests_required": "python -m pytest tests/test_raw_ohlc_prefill_delivery_path.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable_tooling_only",
        "priority": 705,
        "dependencies": [],
        "new_followups_opened": ["PREFILL-FORWARD-LIFECYCLE-JOIN-AFTER-TELEMETRY"],
        "tier": "P1",
        "section": "weekend_goal",
        "item": "Pre-fill delivery-path capture harness.",
        "latest_artifact_path": "research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md",
        "reconciliation_note": "Tooling exists; scoring delivery/reversal strategy remains forbidden without lifecycle truth.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P1-C-V3-FVG-ONLY-RESCUE",
        "lane": "lane_2_path_scaling",
        "status": "STRONGER_THAN_BASELINE_CANDIDATE",
        "blocked_by": "Same-dataset exploratory replay only; needs V2b/forward resolved rows, lifecycle telemetry, and promotion dossier if CEO asks.",
        "artifact_required": "forward-shadow validation design and later unseen resolved rows",
        "tests_required": "python -m pytest tests/test_raw_ohlc_path_scaling_v3_risk_bank.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "V3_FVG_ONLY_RESCUE_RISK_BANK mean delta vs J46 +0.270259R on existing replay; discovery-only stronger candidate, not validation",
        "priority": 206,
        "dependencies": ["P1-A-V2-CONFLUENCE-DEEPDIVE", "P1-B-PREFILL-DELIVERY-PATH-HARNESS"],
        "new_followups_opened": ["V3-FVG-ONLY-FORWARD-SHADOW-PRIORITY", "V3-LIFECYCLE-AWARE-VARIANTS-AFTER-P2I"],
        "tier": "P1",
        "section": "weekend_goal",
        "item": "V3 full exploratory replay; strongest discovered V3 branch.",
        "latest_artifact_path": "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.md",
        "reconciliation_note": "Classified as stronger-than-baseline discovery per durable goal; still NO_PROMOTION_VERDICT.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P1-D-V2B-ROLLING-STATUS-TOOL",
        "lane": "lane_2_path_scaling",
        "status": "BLOCKED_WITH_REASON",
        "blocked_by": "0 resolved post-cutoff OB-boundary/J46 pairs; keep collection/replay running.",
        "artifact_required": "resolved prospective pair rows reaching registered sample floors",
        "tests_required": "python -m pytest tests/test_raw_ohlc_path_scaling_v2b_prospective.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "blocked_no_resolved_prospective_pairs",
        "priority": 210,
        "dependencies": [],
        "new_followups_opened": ["V2B-FORWARD-RESOLVED-PAIRS-COLLECTION"],
        "tier": "P1",
        "section": "weekend_goal",
        "item": "V2b rolling status/evaluator hardening.",
        "latest_artifact_path": "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_ROLLING_STATUS_TOOL_2026-05-03.md",
        "reconciliation_note": "Evaluator hardened, validation still blocked rather than failed.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P1-E-NAS100-CACHED-ORDERFLOW-FORENSICS",
        "lane": "lane_4_orderflow_proxy_sierra",
        "status": "ACCEPTED_CANDIDATE_DISCOVERY",
        "blocked_by": "Actual-R coverage 1 and synthetic winner side 1; leave-one-date flips depth sign.",
        "artifact_required": "forward NAS100 rows with actual-R and winner-side coverage",
        "tests_required": "python -m pytest tests/test_orderflow_mbo_nas100_features.py tests/test_orderflow_nas100_cached_feature_forensics.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_strategy_comparable; diagnostic depth/thinness branch only",
        "priority": 405,
        "dependencies": [],
        "new_followups_opened": ["OF-NAS100-DEPTH-ADVERSE-SELECTION-V1-FORWARD"],
        "tier": "P1",
        "section": "weekend_goal",
        "item": "Cached NAS100 orderflow feature forensics.",
        "latest_artifact_path": "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md",
        "reconciliation_note": "Depth/thinness remains forward diagnostic, not a filter.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P1-F-PROXY-MAPPING-WEEKEND-FORENSICS",
        "lane": "lane_4_orderflow_proxy_sierra",
        "status": "DEFERRED_WITH_TRIGGER",
        "blocked_by": "Needs approved/pre-registered USDJPY/6J price-transfer follow-up data; no broad paid pulls.",
        "artifact_required": "registered price-transfer follow-up before depth or alpha features",
        "tests_required": "python -m pytest tests/test_orderflow_proxy_mapping_priorities.py tests/test_orderflow_proxy_mapping_weekend_forensics.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_alpha_claim_proxy_transfer_only",
        "priority": 440,
        "dependencies": [],
        "new_followups_opened": ["USDJPY-6J-REGISTERED-PRICE-TRANSFER-FOLLOWUP"],
        "tier": "P1",
        "section": "weekend_goal",
        "item": "Proxy mapping weak-window forensics.",
        "latest_artifact_path": "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_PROXY_MAPPING_WEEKEND_FORENSICS_2026-05-03.md",
        "reconciliation_note": "USDJPY/6J remains review-open; GBPJPY two-book depth stays blocked.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P2-G-PHASE3-METHODOLOGY-DIAGNOSTICS",
        "lane": "lane_1_methodology",
        "status": "DONE",
        "blocked_by": "",
        "artifact_required": "diagnostics artifact",
        "tests_required": "python -m pytest tests/test_phase3_methodology_diagnostics.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable_methodology_guard",
        "priority": 610,
        "dependencies": [],
        "new_followups_opened": ["M-7", "M-12", "M-13"],
        "tier": "P2",
        "section": "weekend_goal",
        "item": "Phase 3 methodology diagnostics harness.",
        "latest_artifact_path": "research/phase_3_external_feed_validation/PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.md",
        "reconciliation_note": "Phase 3 claim diagnostics forbid promotion p-values; broader M-7/M-12/M-13 are closed by the methodology infrastructure gate.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "P2-I-PENDING-LIMIT-LIFECYCLE-TELEMETRY",
        "lane": "lane_3_execution_telemetry",
        "status": "FILED_FOR_APPROVAL",
        "blocked_by": "CEO/main-thread approval required before touching execution.py or orchestrator.py.",
        "artifact_required": "approval plus isolated logger implementation/tests",
        "tests_required": "future isolated logger tests listed in ticket",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable_label_truth_tooling",
        "priority": 330,
        "dependencies": [],
        "new_followups_opened": ["PENDING-LIMIT-LIFECYCLE-LOGGER-AFTER-APPROVAL"],
        "tier": "P2",
        "section": "weekend_goal",
        "item": "Pending-limit lifecycle telemetry integration ticket.",
        "latest_artifact_path": "research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md",
        "reconciliation_note": "Spec/ticket filed, no live hook implemented.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "O1-INDEX-REBUILD-OR-STALE-VERIFIER",
        "lane": "lane_3_execution_telemetry",
        "status": "DONE",
        "blocked_by": "",
        "artifact_required": "research-only _trade_index staleness verifier",
        "tests_required": "python -m pytest tests/test_execution_telemetry_verifier.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable_label_truth_tooling",
        "priority": 616,
        "dependencies": ["O-1"],
        "new_followups_opened": [],
        "tier": "T1",
        "section": "generated_followup",
        "item": "Build verifier or plan for replacing stale _trade_index.json consumers.",
        "latest_artifact_path": "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md",
        "reconciliation_note": "Verifier implemented and run; current verdict is STALE_REBUILD_OR_CONSUMER_MIGRATION_REQUIRED.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "O8-LIFECYCLE-COMPLETENESS-VERIFIER",
        "lane": "lane_3_execution_telemetry",
        "status": "DONE",
        "blocked_by": "",
        "artifact_required": "research-only verifier over live_evaluations/trade_records/index/shadow outcomes",
        "tests_required": "python -m pytest tests/test_execution_telemetry_verifier.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable_label_truth_tooling",
        "priority": 615,
        "dependencies": ["O-8"],
        "new_followups_opened": [],
        "tier": "T1",
        "section": "generated_followup",
        "item": "Build lifecycle-aware completeness verifier for trade_records/live_evaluations enrichment gap.",
        "latest_artifact_path": "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md",
        "reconciliation_note": "Verifier implemented and run; current verdict is INCOMPLETE_CURRENT_DATA because LIMIT_PLACED rows lack execution and pending_lifecycle fields.",
        "source": "WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
    },
    {
        "id": "D11-REGENERATE-GBPJPY-US30CASH-OLD-LABELS",
        "lane": "lane_5_data_ml_quality",
        "status": "DONE",
        "blocked_by": "",
        "artifact_required": "generation/locator report plus source-period flags",
        "tests_required": "python -m pytest tests/test_d11_missing_old_labels.py -q",
        "promotion_allowed": False,
        "candidate_strength_vs_j46_j49": "not_applicable_data_quality",
        "priority": 505,
        "dependencies": ["D-11"],
        "new_followups_opened": [],
        "tier": "T1",
        "section": "generated_followup",
        "item": "Regenerate or locate GBPJPY and US30_cash 2022-2023 mechanical labels.",
        "latest_artifact_path": "research/ml_program/audit/D11_MISSING_OLD_LABELS_REGENERATION_2026-05-03.md",
        "reconciliation_note": "Supplemental F11-style mechanical labels generated from local data/historical OHLCV: GBPJPY 238 filled rows, US30_cash 227 filled rows, versioned separately from the canonical five-symbol cohort.",
        "source": "D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md",
    },
]


def apply_overlay(item: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    for key, value in overlay.items():
        out[key] = value
    out["priority"] = min(out.get("priority", 999), base_priority(out["lane"], out["tier"], out["status"]))
    if out["status"] in {"DONE", "REJECTED_FAILED", "DEFERRED_WITH_TRIGGER"}:
        out["priority"] = max(out["priority"], 600)
    return out


def build_queue(backlog_path: str | Path = DEFAULT_BACKLOG) -> list[dict[str, Any]]:
    items = []
    for row in parse_backlog(backlog_path):
        item = default_item(row)
        overlay = ARTIFACT_OVERLAYS.get(item["id"])
        if overlay:
            item = apply_overlay(item, overlay)
        items.append(item)
    existing_ids = {item["id"] for item in items}
    for item in SYNTHETIC_QUEUE_ITEMS:
        if item["id"] not in existing_ids:
            row = dict(item)
            row["lane_name"] = LANE_NAMES[row["lane"]]
            row["backlog_status"] = "generated"
            items.append(row)
    return sorted(items, key=lambda row: (row["priority"], row["lane"], row["id"]))


def backlog_delta(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deltas = []
    for row in items:
        if row["backlog_status"] == "generated":
            continue
        normalized = normalize_status(row["backlog_status"])
        if row["status"] != normalized or row.get("latest_artifact_path") or row.get("new_followups_opened"):
            deltas.append(
                {
                    "id": row["id"],
                    "backlog_status": row["backlog_status"],
                    "queue_status": row["status"],
                    "latest_artifact_path": row.get("latest_artifact_path", ""),
                    "note": row.get("reconciliation_note", ""),
                    "new_followups_opened": row.get("new_followups_opened", []),
                }
            )
    return deltas


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_queue_items": len(items),
        "master_backlog_items": sum(1 for row in items if row["backlog_status"] != "generated"),
        "generated_followup_items": sum(1 for row in items if row["backlog_status"] == "generated"),
        "status_counts": dict(sorted(Counter(row["status"] for row in items).items())),
        "lane_counts": dict(sorted(Counter(row["lane"] for row in items).items())),
        "unblocked_ranked": [
            row["id"]
            for row in items
            if row["status"] == "STILL_PENDING_RANKED" and not row.get("blocked_by")
        ][:25],
        "stronger_than_baseline_candidates": [
            row["id"] for row in items if row["status"] == "STRONGER_THAN_BASELINE_CANDIDATE"
        ],
        "promotion_allowed_items": [row["id"] for row in items if row.get("promotion_allowed")],
    }


def build_payload(
    *,
    backlog_path: str | Path = DEFAULT_BACKLOG,
    research_current_state_path: str | Path = DEFAULT_RESEARCH_CURRENT_STATE,
    deferred_ledger_path: str | Path = DEFAULT_DEFERRED_LEDGER,
) -> dict[str, Any]:
    items = build_queue(backlog_path)
    return {
        "schema_version": "master_research_queue_state_v1",
        "queue_date": QUEUE_DATE,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "source_files": [
            str(backlog_path),
            str(research_current_state_path),
            str(deferred_ledger_path),
            ".context/05_operations/WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md",
        ],
        "summary": summarize(items),
        "backlog_delta": backlog_delta(items),
        "items": items,
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else ""
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    items = payload["items"]
    summary = payload["summary"]
    unblocked = [
        row
        for row in items
        if row["status"] == "STILL_PENDING_RANKED" and not row.get("blocked_by")
    ][:20]
    blocked = [row for row in items if row["status"] == "BLOCKED_WITH_REASON"][:20]
    deferred = [row for row in items if row["status"] == "DEFERRED_WITH_TRIGGER"][:20]
    lines = [
        "# Master Research Queue State",
        "",
        f"Date: {payload['queue_date']}",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Control Summary",
        "",
        f"- Total queue items: `{summary['total_queue_items']}`.",
        f"- Master-backlog items: `{summary['master_backlog_items']}`.",
        f"- Generated follow-up/control items: `{summary['generated_followup_items']}`.",
        f"- Stronger-than-baseline candidates: `{summary['stronger_than_baseline_candidates']}`.",
        f"- Promotion-allowed items: `{summary['promotion_allowed_items']}`.",
        "",
        "Status counts:",
        "",
        *table(["status", "count"], [[k, v] for k, v in summary["status_counts"].items()]),
        "",
        "Lane counts:",
        "",
        *table(["lane", "count"], [[k, v] for k, v in summary["lane_counts"].items()]),
        "",
        "## Backlog Delta Report",
        "",
        "Artifact-backed deltas and status clarifications found while reconciling the backlog:",
        "",
        *table(
            ["id", "backlog status", "queue status", "artifact", "note", "follow-ups"],
            [
                [
                    row["id"],
                    row["backlog_status"],
                    row["queue_status"],
                    row["latest_artifact_path"],
                    row["note"],
                    row["new_followups_opened"],
                ]
                for row in payload["backlog_delta"]
            ],
        ),
        "",
        "## Next Unblocked Ranked Items",
        "",
        *table(
            ["priority", "id", "lane", "artifact required", "tests required"],
            [
                [
                    row["priority"],
                    row["id"],
                    row["lane"],
                    row["artifact_required"],
                    row["tests_required"],
                ]
                for row in unblocked
            ],
        ),
        "",
        "## Blocked And Deferred Triggers",
        "",
        *table(
            ["id", "status", "blocked by", "trigger/artifact required"],
            [
                [row["id"], row["status"], row["blocked_by"], row["artifact_required"]]
                for row in blocked + deferred
            ],
        ),
        "",
        "## Full Queue Index",
        "",
        *table(
            ["priority", "id", "lane", "status", "blocked_by", "artifact", "candidate strength"],
            [
                [
                    row["priority"],
                    row["id"],
                    row["lane"],
                    row["status"],
                    row["blocked_by"],
                    row["latest_artifact_path"],
                    row["candidate_strength_vs_j46_j49"],
                ]
                for row in items
            ],
        ),
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This queue state is a control artifact. It does not validate, promote, or modify any live trading behavior.",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", default=DEFAULT_BACKLOG)
    parser.add_argument("--research-current-state", default=DEFAULT_RESEARCH_CURRENT_STATE)
    parser.add_argument("--deferred-ledger", default=DEFAULT_DEFERRED_LEDGER)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        backlog_path=args.backlog,
        research_current_state_path=args.research_current_state,
        deferred_ledger_path=args.deferred_ledger,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "queue_items={total} statuses={statuses} stronger={stronger}".format(
            total=payload["summary"]["total_queue_items"],
            statuses=payload["summary"]["status_counts"],
            stronger=payload["summary"]["stronger_than_baseline_candidates"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
